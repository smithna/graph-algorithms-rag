"""Question decomposition: name the entities, then look them up by name.

Section 5's semantic entity seeder matches a whole-question embedding against
entity *descriptions*. Measured, that seeder has cosine's disease — the exact
failure the section teaches:

- Every entity description shares the corpus boilerplate ("… documented in the
  Lewis and Clark Expedition journals"), which alone accounts for ~75% of a
  bad match's similarity (WISDOM RIVER: raw cosine 0.38 against a Sacagawea
  question, 0.29 of it from the bare template).
- The alias list embedded into the description *dilutes* the name it exists to
  strengthen: "Sacagawea" alone matches the question at raw cosine 0.66; the
  full templated description with eight alias spellings matches at 0.55.
- The candidate pool below the top handful is a monoculture of degree-1
  coreference nodes (INTERPRETERS WIFE, HIS NATION) — section 4's unresolved
  generic entities — so any filter that drops them back-fills with
  boilerplate-floor noise (WISDOM RIVER, at pooled rank 35 of 80).

This module is the alternative: ask an LLM to *name* the entities the question
is about — a typed manifest, not an answer — then resolve each name against the
graph the way the corps-of-discovery text2cypher agent resolves Cypher params:

  proper-noun labels (Person, NativeNation, Place, WaterBody, Supply)
      → per-label **full-text** index over canonicalName/name/aliases.
        Token matching never sees the boilerplate, and every alias is a
        separate field to hit rather than noise averaged into one vector.

  concept labels (AnimalSpecies, PlantSpecies, Taxon, Event)
      → per-label **vector** index. "Grizzly bear" must reach URSUS ARCTOS
        HORRIBILIS; full-text actually ranks it *below* short-named Supply
        junk, because Lucene's field-length norm punishes a 32-alias array.
        (Lucene also does not stem — "horse" does not match "horses".)

Unlike a Cypher parameter, a PPR seed set does not need an argmax: a mention
keeps every strong match, so the two SACAGAWEA duplicates both get seeded and
resolution stays optional rather than load-bearing (section 4's callback,
intact). What changes is *which* candidates exist at all — entities the
question names, instead of anything expedition-flavoured.

The LLM call is cached on disk keyed by (model, question), same contract as
the embedding cache: a benchmark re-run costs nothing and is byte-for-byte
repeatable. Like everything else in this repo, nothing here writes to the
database.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .config import read_query, settings

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache" / "decompose"

#: Same model the section-4 adjudicator settled on by measurement (perfect
#: precision and recall on 187 labelled pairs — see ``adjudicate.py``). Naming
#: the entities in one question is a far easier task than judging duplicate
#: pairs, and the cache makes the choice cheap either way.
DEFAULT_DECOMPOSE_MODEL = "gpt-5.6-luna"

MENTION_LABELS = (
    "Person", "NativeNation", "Place", "WaterBody",
    "AnimalSpecies", "PlantSpecies", "Taxon", "Event", "Supply",
    "Unknown",
)

#: Proper-noun labels resolve by token match. Place and WaterBody share
#: ``location_search`` deliberately — the corps agent found the LLM cannot
#: reliably tell a river from a fort, and the shared index makes that mistake
#: free. ``Unknown`` gets the cross-label index.
FULLTEXT_ROUTES = {
    "Person":       "person_search",
    "NativeNation": "native_nation_search",
    "Place":        "location_search",
    "WaterBody":    "location_search",
    "Supply":       "supply_search",
    "Unknown":      "entity_search",
}

#: Concept labels resolve semantically, against the per-label vector indexes
#: built by the corps repo's ``embed_entities.py``.
VECTOR_ROUTES = {
    "AnimalSpecies": "animalspecies_embeddings",
    "PlantSpecies":  "plantspecies_embeddings",
    "Taxon":         "taxon_embeddings",
    "Event":         "event_embeddings",
}

#: A full-text candidate is kept while it scores at least this fraction of the
#: mention's best hit. Generous on purpose: exact-name duplicates (the two
#: SACAGAWEA nodes) land within a few percent of each other, while the junk
#: tail falls off fast. Untuned beyond that — see the measurement script.
FULLTEXT_KEEP_RATIO = 0.5

#: A vector candidate is kept while it sits within this margin of the mention's
#: best hit, on the index's (1+cosine)/2 scale. Wide enough to keep sibling
#: species ("a cottonwood" should seed every POPULUS), narrow enough to drop
#: the boilerplate floor, which sits ~0.1 below a real name match. Untuned.
VECTOR_KEEP_MARGIN = 0.03

#: Hard cap on nodes one mention may seed, after the thresholds above.
MAX_NODES_PER_MENTION = 4


@dataclass(frozen=True)
class Mention:
    """One entity the question explicitly names, as the LLM typed it."""

    phrase: str
    label: str


@dataclass
class ResolvedMention:
    """A mention plus the graph nodes its name resolved to (possibly none)."""

    mention: Mention
    #: ``[{nodeId, name, label, score}, ...]`` sorted by score, capped.
    candidates: list[dict]
    #: "fulltext" | "vector" | "fulltext→vector" | "none"
    via: str


#: The examples are paraphrases, deliberately NOT questions from the benchmark
#: bank — few-shotting the bank's own questions would contaminate the
#: seed-coverage measurement in scripts/measure_seeds.py.
DECOMPOSE_PROMPT = """\
You extract the entities that a question explicitly names, so a retrieval
system can look each one up by name in a knowledge graph built from the Lewis
and Clark expedition journals (1804-1806).

What counts as an entity the question names:
- People and nations: "Clark", "the Shoshone", "Sergeant Ordway".
- Geography, including destinations: "the Rocky Mountains", "the Pacific",
  "the Missouri", "Fort Mandan".
- Concrete kinds of animal, plant, goods, or vessel the question asks about,
  even without a proper name: "horses", "grizzly bears", "canoes", "camas".
- Named events: "the court martial", "the death of Sergeant Floyd".

What does not count:
- The expedition itself ("the expedition", "the party", "the corps",
  "the Corps of Discovery") — the entire corpus is about it.
- Open categories the question is asking to have filled in: "Native nations"
  in "which Native nations…", "illnesses" in "what illnesses…".
- Anything you think a correct ANSWER would involve. Only what the question
  itself says.

phrase: the entity as the question puts it, minus articles — the graph knows
historical spellings and aliases. label: who or what kind of thing it is
(Unknown when unsure).

Examples:
Q: What did Clark write when the party first saw the Rocky Mountains?
→ Clark (Person), Rocky Mountains (Place)
Q: How did the corps acquire canoes from the Clatsop?
→ canoes (Supply), Clatsop (NativeNation)
Q: What hardships did the men face during the winter?
→ (no entities)
"""


@lru_cache(maxsize=1)
def _schema():
    """Structured-output schema, pydantic imported lazily like adjudicate.py."""
    from pydantic import BaseModel

    from typing import Literal

    class MentionModel(BaseModel):
        phrase: str
        label: Literal[  # type: ignore[valid-type]
            "Person", "NativeNation", "Place", "WaterBody", "AnimalSpecies",
            "PlantSpecies", "Taxon", "Event", "Supply", "Unknown",
        ]

    class Decomposition(BaseModel):
        mentions: list[MentionModel]

    return Decomposition


@lru_cache(maxsize=1)
def _client():
    from openai import OpenAI

    return OpenAI(api_key=settings().openai_api_key)


def _cache_path(model: str, question: str) -> Path:
    # The prompt is part of the key: editing the rules must invalidate every
    # cached parse, or a prompt fix silently serves answers from the old rules.
    key = hashlib.sha256(
        f"{model}::{DECOMPOSE_PROMPT}::{question}".encode()
    ).hexdigest()[:32]
    return CACHE_DIR / f"{key}.json"


def decompose(
    question: str,
    *,
    model: str = DEFAULT_DECOMPOSE_MODEL,
    use_cache: bool = True,
) -> list[Mention]:
    """Ask the LLM which entities the question names. Cached on disk."""
    path = _cache_path(model, question)
    if use_cache and path.exists():
        return [Mention(**m) for m in json.loads(path.read_text())]

    kwargs = dict(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": DECOMPOSE_PROMPT},
            {"role": "user", "content": question},
        ],
        response_format=_schema(),
    )
    client = _client()
    endpoint = getattr(client.chat.completions, "parse", None)
    if endpoint is None:  # pragma: no cover - older openai client
        endpoint = client.beta.chat.completions.parse

    try:
        parsed = endpoint(**kwargs).choices[0].message.parsed
    except Exception as exc:
        # GPT-5-generation models reject explicit temperature; drop and retry.
        # Same tolerance as adjudicate.py, for the same reason.
        if "temperature" not in str(exc):
            raise
        kwargs.pop("temperature", None)
        parsed = endpoint(**kwargs).choices[0].message.parsed

    mentions = [Mention(phrase=m.phrase.strip(), label=m.label) for m in parsed.mentions]
    mentions = [m for m in mentions if m.phrase]

    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([m.__dict__ for m in mentions]))
    return mentions


# Lucene special characters, escaped so "O'Fallon" or "who?" cannot break the
# query. Same list the corps agent uses.
_LUCENE_SPECIALS = re.compile(r'[+\-&|!(){}\[\]^"~*?:\\/]')


def _singularize(phrase: str) -> list[str]:
    """Naive singulars for plural tokens — Lucene's standard analyzer does not
    stem, so "horses" matches BIG HORSES MEADEAL (df 1) but not HORSE (df 37).
    Appending de-pluralised tokens to the OR-query lets the exact name win.
    """
    extras = []
    for token in phrase.split():
        low = token.lower()
        if len(low) > 3 and low.endswith("ies"):
            extras.append(token[:-3] + "y")
        elif len(low) > 3 and low.endswith("s") and not low.endswith("ss"):
            extras.append(token[:-1])
    return extras


def _fulltext_query(index: str, lucene: str) -> list[dict]:
    return read_query(
        """
        CALL db.index.fulltext.queryNodes($index, $lucene)
        YIELD node, score
        WHERE NOT node:GenericLocation AND NOT node:Chunk
        RETURN id(node)                                  AS nodeId,
               coalesce(node.canonicalName, node.name)   AS name,
               head(labels(node))                        AS label,
               score
        LIMIT 10
        """,
        index=index,
        lucene=lucene,
    )


def _fulltext_candidates(index: str, phrase: str) -> list[dict]:
    """All-tokens-AND first, OR fallback.

    A single OR query at the keep-ratio admits any node matching *one* token —
    FORT MANDAN for "Fort Clatsop", SERGEANT for "Sergeant Floyd". The AND
    query (`+(fort) +(clatsop)`, each group holding the token plus its naive
    singular) returns only nodes matching every token: precise when the graph
    has the name. When it returns nothing — which is exactly the
    extraction-gap case, where no node carries the full name — fall back to
    the generous OR query and let the keep-ratio nominate nearest names.
    """
    groups = []
    for token in phrase.split():
        variants = " ".join(
            _LUCENE_SPECIALS.sub(r"\\\g<0>", v) for v in [token, *_singularize(token)]
        )
        groups.append(f"+({variants})")
    rows = _fulltext_query(index, " ".join(groups))
    if rows:
        return rows

    loose = " ".join([phrase, *_singularize(phrase)])
    return _fulltext_query(index, _LUCENE_SPECIALS.sub(r"\\\g<0>", loose))


def _vector_candidates(index: str, phrase: str) -> list[dict]:
    from .embedding import embed

    return read_query(
        """
        CALL db.index.vector.queryNodes($index, 5, $embedding)
        YIELD node, score
        WHERE NOT node:GenericLocation AND NOT node:Chunk
        RETURN id(node)                                  AS nodeId,
               coalesce(node.canonicalName, node.name)   AS name,
               head(labels(node))                        AS label,
               score
        """,
        index=index,
        embedding=embed(phrase),
    )


def _keep_strong(candidates: list[dict], *, ratio: float | None, margin: float | None) -> list[dict]:
    """Keep candidates near the top hit — all the duplicates, none of the tail."""
    if not candidates:
        return []
    candidates = sorted(candidates, key=lambda c: -c["score"])
    top = candidates[0]["score"]
    if ratio is not None:
        kept = [c for c in candidates if c["score"] >= top * ratio]
    else:
        kept = [c for c in candidates if c["score"] >= top - (margin or 0.0)]
    return kept[:MAX_NODES_PER_MENTION]


def _degrees(node_ids: list[int]) -> dict[int, int]:
    """Chunk degree (df) per node — the seed weighting needs it for twins."""
    if not node_ids:
        return {}
    rows = read_query(
        """
        UNWIND $ids AS nid
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE id(e) = nid
        RETURN nid AS nodeId, count(DISTINCT c) AS df
        """,
        ids=node_ids,
    )
    return {r["nodeId"]: r["df"] for r in rows}


def _same_name_duplicates(names: list[str], *, in_graph: frozenset[int]) -> list[dict]:
    """Nodes under *any* label whose exact name matches a resolved candidate.

    Per-label routing is precise, but section 4's unresolved duplicates do not
    respect labels — the second SACAGAWEA node is a mislabelled NativeNation,
    invisible to a Person-routed lookup. Same name string, same named entity:
    pulling exact-name twins back in keeps "you do not have to fix your
    entities before this works" true for this seeder, without readmitting any
    fuzzy cross-label noise.
    """
    if not names:
        return []
    rows = read_query(
        """
        UNWIND $names AS name
        MATCH (n)
        WHERE coalesce(n.canonicalName, n.name) = name
          AND NOT n:Chunk AND NOT n:GenericLocation
        RETURN DISTINCT id(n)                          AS nodeId,
               coalesce(n.canonicalName, n.name)       AS name,
               head(labels(n))                         AS label
        """,
        names=names,
    )
    return [r for r in rows if r["nodeId"] in in_graph]


def resolve_mention(mention: Mention, *, in_graph: frozenset[int]) -> ResolvedMention:
    """Resolve one mention to graph nodes, routed by label.

    Full-text on the label's own index first for proper nouns; the cross-label
    ``entity_search`` when that finds nothing (the LLM's label can be wrong,
    and so can the extractor's); a vector fallback when the label has an
    embedding index (misspellings the alias list does not know). Exact-name
    twins under other labels are then unioned in — see
    :func:`_same_name_duplicates`. Candidates outside the mentions projection
    are dropped throughout: a node with no MENTIONED_IN edge cannot seed a
    walk (hard GDS error).
    """
    via = "none"
    kept: list[dict] = []

    ft_index = FULLTEXT_ROUTES.get(mention.label)
    if ft_index:
        rows = [r for r in _fulltext_candidates(ft_index, mention.phrase) if r["nodeId"] in in_graph]
        kept = _keep_strong(rows, ratio=FULLTEXT_KEEP_RATIO, margin=None)
        via = "fulltext"
        if not kept and ft_index != "entity_search":
            rows = [
                r for r in _fulltext_candidates("entity_search", mention.phrase)
                if r["nodeId"] in in_graph
            ]
            kept = _keep_strong(rows, ratio=FULLTEXT_KEEP_RATIO, margin=None)
            via = "fulltext(cross-label)"

    if not kept:
        vec_index = VECTOR_ROUTES.get(mention.label)
        if vec_index:
            rows = [r for r in _vector_candidates(vec_index, mention.phrase) if r["nodeId"] in in_graph]
            kept = _keep_strong(rows, ratio=None, margin=VECTOR_KEEP_MARGIN)
            via = "vector" if via == "none" else "fulltext→vector"

    if kept:
        have = {c["nodeId"] for c in kept}
        floor = min(c["score"] for c in kept)
        for twin in _same_name_duplicates([c["name"] for c in kept], in_graph=in_graph):
            if twin["nodeId"] not in have and len(kept) < MAX_NODES_PER_MENTION:
                # A twin inherits the weakest kept score: it matched by
                # identity of name, not by its own retrieval evidence. (Seed
                # weighting groups by name anyway — see pagerank.py.)
                kept.append({**twin, "score": floor})
                have.add(twin["nodeId"])
        degrees = _degrees([c["nodeId"] for c in kept])
        for c in kept:
            c["df"] = degrees.get(c["nodeId"], 1)
    else:
        via = "none"
    return ResolvedMention(mention=mention, candidates=kept, via=via)


def decompose_and_resolve(
    question: str,
    *,
    model: str = DEFAULT_DECOMPOSE_MODEL,
    in_graph: frozenset[int],
    use_cache: bool = True,
) -> list[ResolvedMention]:
    """The full pipeline: manifest from the LLM, then one lookup per mention."""
    return [
        resolve_mention(m, in_graph=in_graph)
        for m in decompose(question, model=model, use_cache=use_cache)
    ]

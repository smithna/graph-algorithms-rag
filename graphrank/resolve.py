"""Resolve natural-language mentions to nodes in the graph.

Proper nouns go through the full-text indexes (token matching beats cosine
similarity on names like "Columbia River"); concepts go through the per-label
vector indexes. Both index families are created by the corps-of-discovery
pipeline — this repo only reads them.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import query
from .embedding import embed

#: Per-label vector indexes created by embed_entities.py
LABEL_VECTOR_INDEX: dict[str, str] = {
    "Person": "person_embeddings",
    "Place": "place_embeddings",
    "WaterBody": "waterbody_embeddings",
    "AnimalSpecies": "animalspecies_embeddings",
    "PlantSpecies": "plantspecies_embeddings",
    "NativeNation": "nativenation_embeddings",
    "Event": "event_embeddings",
    "Taxon": "taxon_embeddings",
}

#: Per-label full-text indexes created by setup_fulltext_indexes.py
LABEL_FULLTEXT_INDEX: dict[str, str] = {
    "Person": "person_search",
    "Place": "location_search",  # covers Place + WaterBody
    "WaterBody": "location_search",
    "NativeNation": "native_nation_search",
}

_LUCENE_SPECIAL = set('+-&|!(){}[]^"~*?:\\/')


#: How close a weaker text match has to be before corpus prominence decides.
#:
#: Lucene scores a name match against how rare the term is *in that index*, not
#: against how much the corpus actually talks about the node. In this graph that
#: backfires: a stray ``:Person {canonicalName: "SHOSHONE"}`` with one mention
#: scores 7.32 on ``person_search``, while the real ``:NativeNation`` Shoshone
#: with 205 mentions scores 6.66 on ``native_nation_search``. Taking the higher
#: score picks a node with no extracted relationships, and every path query
#: through it returns nothing — silently.
#:
#: So: when two hits match the name about equally well, prefer the one the
#: corpus is actually about. Within this ratio of the best score, mention count
#: breaks the tie.
NEAR_TIE_RATIO = 0.75


@dataclass
class ResolvedEntity:
    label: str
    name: str
    node_id: int
    score: float
    resolved_via: str  # "fulltext" | "vector"
    #: How many chunks mention this node — the tie-breaker, kept for display
    mentions: int = 0


def _best_of(hits: list[ResolvedEntity]) -> ResolvedEntity | None:
    """Pick the strongest hit, breaking near-ties on corpus prominence."""
    live = [h for h in hits if h is not None]
    if not live:
        return None
    best_score = max(h.score for h in live)
    contenders = [h for h in live if h.score >= best_score * NEAR_TIE_RATIO]
    return max(contenders, key=lambda h: (h.mentions, h.score))


def _escape_lucene(text: str) -> str:
    return "".join(f"\\{c}" if c in _LUCENE_SPECIAL else c for c in text)


def resolve_entity(text: str, label: str | None = None) -> ResolvedEntity | None:
    """Find the single best node for a phrase, optionally constrained to a label."""
    if label:
        hit = _resolve_in_label(text, label)
        return hit

    # No label given: try every full-text index, then pick across all of them at
    # once. Comparing index-by-index would let whichever index happened to be
    # consulted first keep a lead it did not earn.
    fulltext_hits = [
        _fulltext_lookup(text, candidate_label)
        for candidate_label in ("Person", "Place", "NativeNation")
    ]
    best = _best_of([h for h in fulltext_hits if h])
    if best:
        return best

    # Fall back to semantic labels.
    vector_hits = [
        _vector_lookup(text, candidate_label)
        for candidate_label in ("Event", "AnimalSpecies", "PlantSpecies", "Taxon")
    ]
    return _best_of([h for h in vector_hits if h])


def _resolve_in_label(text: str, label: str) -> ResolvedEntity | None:
    if label in LABEL_FULLTEXT_INDEX:
        hit = _fulltext_lookup(text, label)
        if hit:
            return hit
    return _vector_lookup(text, label)


def _fulltext_lookup(text: str, label: str) -> ResolvedEntity | None:
    index = LABEL_FULLTEXT_INDEX.get(label)
    if not index:
        return None
    # Take several hits, not one: the top-scoring node in an index can be a
    # near-duplicate the corpus barely mentions. _best_of sorts that out.
    rows = query(
        f"""
        CALL db.index.fulltext.queryNodes('{index}', $q)
        YIELD node, score
        WHERE NOT node:GenericLocation
        RETURN coalesce(node.canonicalName, node.name) AS name,
               head(labels(node))                      AS label,
               id(node)                                AS nodeId,
               score,
               count {{ (node)-[:MENTIONED_IN]->(:Chunk) }} AS mentions
        ORDER BY score DESC
        LIMIT 5
        """,
        q=_escape_lucene(text),
    )
    return _best_of(
        [
            ResolvedEntity(
                label=row["label"],
                name=row["name"],
                node_id=row["nodeId"],
                score=row["score"],
                resolved_via="fulltext",
                mentions=row["mentions"],
            )
            for row in rows
            if row["name"]
        ]
    )


def _vector_lookup(text: str, label: str) -> ResolvedEntity | None:
    index = LABEL_VECTOR_INDEX.get(label)
    if not index:
        return None
    rows = query(
        f"""
        CALL db.index.vector.queryNodes('{index}', 5, $embedding)
        YIELD node, score
        WHERE NOT node:GenericLocation
        RETURN coalesce(node.canonicalName, node.name) AS name,
               head(labels(node))                      AS label,
               id(node)                                AS nodeId,
               score,
               count {{ (node)-[:MENTIONED_IN]->(:Chunk) }} AS mentions
        ORDER BY score DESC
        """,
        embedding=embed(text),
    )
    return _best_of(
        [
            ResolvedEntity(
                label=row["label"],
                name=row["name"],
                node_id=row["nodeId"],
                score=row["score"],
                resolved_via="vector",
                mentions=row["mentions"],
            )
            for row in rows
            if row["name"]
        ]
    )

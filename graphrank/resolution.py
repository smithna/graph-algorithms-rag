"""Entity resolution, read-only — candidate generation and transitive closure.

This is a port of `disambiguate.py` from the corps-of-discovery-graph-rag repo,
with the writes taken out. The original is a build-time pipeline: it finds
duplicate entity nodes, asks an LLM to confirm them, writes
`IS_SAME_ENTITY_AS` relationships, runs WCC over those relationships, and
merges each component with `apoc.refactor.mergeNodes`.

None of that happens here. This module **never writes to the database**, and
the guarantee is enforced rather than promised: every query goes through
:func:`~graphrank.config.read_query`, which opens a read transaction, so the
server rejects a write with `Neo.ClientError.Statement.AccessMode` before it
can touch anything. See :func:`write_audit` for the before/after proof.

Why a read-only port is possible at all
───────────────────────────────────────
The original had to write `IS_SAME_ENTITY_AS` because that is what WCC ran on.
GDS needs a *graph* to compute connected components over, and the only graph the
original knew how to build was one made of real relationships in the database.

The change that removes the writes is small and worth stating plainly, because
it is the section's engineering punchline: **carry candidate pairs as node-id
tuples instead of name tuples.** Once a pair is `(3828, 4830)` rather than
`("SHOSHONE", "SHOSHONE")`, the pairs can be projected straight into GDS with
`gds.graph.cypher.project` over an `UNWIND $pairs`, and real `gds.wcc.stream`
runs against that in-memory graph. No relationship is ever created. The
transitive closure — A≈B, B≈C, so one entity — is identical to what the
original computed, because it *is* the same algorithm on the same edges.

The `graphdatascience` client runs Cypher projections with `QueryMode.READ`, so
even the projection step is inside a read transaction. That makes this a
stronger zero-write guarantee than the source ever had.

What WCC is actually for
────────────────────────
WCC is usually taught as a clustering algorithm and that is misleading. It
answers "are these connected at all", not "are these a topic". Run it on a raw
corpus graph and you get one giant component plus dust — a useless answer, and
the reason people conclude WCC is not good for much.

Here it is doing the one thing it is exactly right for: transitive closure over
a sparse, high-precision graph of "these two are probably the same". The edges
are candidate identities, not co-occurrences, so components stay small and mean
something.

The three signals
─────────────────
``cooccurrence``  cosine similarity over chunk co-occurrence vectors, via
                  `gds.nodeSimilarity.filtered`
``string``        Jaro-Winkler with title-token stripping, plus token
                  containment, plus double-metaphone on the surname. Catches
                  archaic spellings — the journals write Charbonneau as
                  "Chabonah", whose metaphone codes (XPN vs XRPN) sit at ~0.925
                  similarity even though the raw strings do not.
``alias``         shared alias arrays, or one node's alias matching the other's
                  canonical name. Receipts from resolution passes already run.

What the co-occurrence signal actually does here
────────────────────────────────────────────────
Measured on this corpus, for Person, against the identity gold set in
`questions/corps_members.yaml` (run `demo_resolution.py --compare-signals` to
reproduce):

    signals              pairs    TP    FP   precision   recall   largest WCC
    string + alias         901    64    19        0.77     0.25            54
    co-occurrence only     252     2   136        0.01     0.01            78
    all three            1,147    64   154        0.29     0.25           249

Co-occurrence proposed 246 pairs the string ladder did not. **Zero** of them
were real duplicates. Adding the signal left recall exactly where it was and
cut precision from 0.77 to 0.29. No support floor or similarity cutoff rescues
it — sweeping both to their useful limits never produces a unique true positive.

The reason is structural, and it is more interesting than the result:

    Two spellings of one person almost never occur in the same chunk.

A scribe writing an entry picks one spelling and uses it throughout, so
"DREWYER" and "GEORGE DROUILLARD" have nearly disjoint chunk sets. Their
co-occurrence *neighbourhoods* are therefore built from different evidence —
and worse, every member of the corps co-occurs with every other member, so the
neighbourhoods that do overlap overlap for everyone. The signal cannot separate
"same person" from "same expedition". `MERIWETHER LEWIS` and `WILLIAM CLARK`
have nearly parallel co-occurrence vectors, and only the string signal's
disagreement keeps them apart.

So the honest claim for this corpus is narrower than "co-occurrence finds
duplicates strings miss": co-occurrence is a **recall instrument for corpora
where the same entity is named differently in the same context** — cross-document
entity resolution, say, where two source systems describe the same customer in
the same transaction. This corpus is not that shape, and the demo says so.

The algorithm is not wrong and node similarity is not useless. It is answering
the question it was asked, on data where that question does not discriminate.
The same algorithm pointed at a different question — "which chunks share
entities with this chunk" — does real work at query time; that is
`graphrank/cooccurrence.py`.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

from .config import gds, read_query, settings

# ── Tuning ────────────────────────────────────────────────────────────────────
# Carried over from disambiguate.py so the demo reproduces the pipeline's own
# behaviour rather than a re-tuned version of it.

LABELS = [
    "Person",
    "NativeNation",
    "Place",
    "WaterBody",
    "PlantSpecies",
    "AnimalSpecies",
    "Supply",
    "Event",
]

COSINE_CUTOFF = 0.5

#: Jaro-Winkler **similarity** cutoffs — 1.0 is identical.
#:
#: Read this before touching the Cypher below, because there is a trap in it.
#: `apoc.text.jaroWinklerDistance` returns a *distance*, not a similarity:
#:
#:     apoc.text.jaroWinklerDistance('SHIELDS', 'SHIELDS')  =  0.0
#:     apoc.text.jaroWinklerDistance('ABC',     'XYZ')      =  1.0
#:     apoc.text.jaroWinklerDistance('MARTHA',  'MARHTA')   =  0.0389
#:
#: and 1 - 0.0389 = 0.961, which is the textbook Jaro-Winkler similarity for
#: that canonical example. The name says "Distance" and the function means it.
#:
#: The pipeline this module is ported from tests `jw >= 0.92` against that
#: distance directly, which asks for strings that are maximally *unlike* each
#: other. That is why its string signal never fired on the pairs it was written
#: to catch: BRATTON/BRATTEN scores 0.057, SHIELDS/SHEILDS 0.038, and identical
#: metaphone codes score 0.000 — all far below a 0.92 threshold, all rejected.
#: It is a large part of why so many duplicates survived two resolution passes.
#:
#: So the queries below convert explicitly, `1 - jaroWinklerDistance(...)`, and
#: these cutoffs are similarities in the ordinary sense.
JARO_CUTOFF = 0.92
METAPHONE_CUTOFF = 0.85
MIN_CHUNK_COUNT = 2  # minimum chunk co-occurrences before an edge is projected
TOP_K = 10

COOCCURRENCE_GRAPH = "entity-cooccurrence"
PAIR_GRAPH = "resolution-candidates"

#: Single-word Person names unambiguous throughout the corpus, and so safe to
#: merge with their multi-word equivalents. Anything not on this list is left
#: alone: "Shannon" or "Collins" could be different men in different chunks.
UNAMBIGUOUS_SINGLE_NAMES: frozenset[str] = frozenset(
    {"LEWIS", "CLARK", "SACAGAWEA", "CHARBONNEAU", "ORDWAY", "GASS", "PRYOR", "FLOYD"}
)

#: Rank and honorific tokens stripped from the front of Person names before
#: string comparison. Jaro-Winkler weights shared *prefixes* especially heavily,
#: so "Sergt. Gass" and "Sergt. Pryor" score as near-identical on the strength of
#: a token that says nothing about identity.
TITLE_TOKENS: frozenset[str] = frozenset(
    {
        "sergt", "serjt", "sgt", "sarjt", "sjt", "seri",
        "serjeant", "sergeant", "sergiant",
        "capt", "captain",
        "lt", "lts", "lieut", "lieuts", "lieutenant", "lieutenants",
        "corp", "cpl", "corporal",
        "pvt", "private",
        "major", "maj",
        "col", "colonel",
        "gen", "general",
        "chief",
        "dr", "doctor",
        "mr", "mrs",
    }
)


# ── Types ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EntityRef:
    """One entity node, keyed by the internal id GDS streams back."""

    node_id: int
    label: str
    name: str
    mentions: int = 0

    def __str__(self) -> str:
        return self.name


@dataclass
class CandidatePair:
    """A proposed duplicate, carried as node ids rather than names.

    The node ids are the whole trick. They survive the round trip into GDS and
    back, which is what lets WCC run over these pairs without them first
    existing as relationships in the database.
    """

    left: EntityRef
    right: EntityRef
    #: Which of "cooccurrence" / "string" / "alias" proposed this pair
    signals: set[str] = field(default_factory=set)
    #: Cosine similarity, when the co-occurrence signal fired
    similarity: float | None = None

    @property
    def key(self) -> tuple[int, int]:
        return (min(self.left.node_id, self.right.node_id),
                max(self.left.node_id, self.right.node_id))

    @property
    def names(self) -> tuple[str, str]:
        return (self.left.name, self.right.name)

    def describe(self) -> str:
        return f"{self.left.name}  ~  {self.right.name}"


@dataclass
class Component:
    """A set of entities WCC found to be transitively connected."""

    component_id: int
    members: list[EntityRef]

    @property
    def size(self) -> int:
        return len(self.members)

    def describe(self) -> str:
        return " + ".join(sorted(m.name for m in self.members))


# ── Entity inventory ──────────────────────────────────────────────────────────


def entities(label: str | None = None) -> dict[int, EntityRef]:
    """Every resolvable entity node, keyed by internal node id."""
    filter_clause = f"AND n:{label}" if label else ""
    rows = read_query(
        f"""
        MATCH (n)
        WHERE NOT n:Chunk
          AND NOT n:GenericLocation
          AND n.canonicalName IS NOT NULL
          {filter_clause}
        RETURN id(n)             AS nodeId,
               head(labels(n))   AS label,
               n.canonicalName   AS name,
               count {{ (n)-[:MENTIONED_IN]->(:Chunk) }} AS mentions
        """
    )
    return {
        row["nodeId"]: EntityRef(
            node_id=row["nodeId"],
            label=row["label"],
            name=row["name"],
            mentions=row["mentions"],
        )
        for row in rows
        if row["name"]
    }


# ── Signal 1: co-occurrence similarity ────────────────────────────────────────

COOCCURRENCE_PROJECTION = """
MATCH (e1)-[:MENTIONED_IN]->(c:Chunk)<-[:MENTIONED_IN]-(e2)
WHERE id(e1) < id(e2)
  AND NOT e1:Chunk AND NOT e2:Chunk
  AND NOT e1:GenericLocation AND NOT e2:GenericLocation
  AND e1.canonicalName IS NOT NULL
  AND e2.canonicalName IS NOT NULL
WITH e1, e2, count(DISTINCT c) AS chunkCount
WHERE chunkCount >= $minCount
RETURN gds.graph.project(
    $graphName, e1, e2,
    {
        sourceNodeLabels: labels(e1),
        targetNodeLabels: labels(e2),
        relationshipType: 'MENTIONED_WITH',
        relationshipProperties: {chunkCount: chunkCount}
    },
    {undirectedRelationshipTypes: ['MENTIONED_WITH']}
)
"""


def drop_graph(name: str) -> None:
    """Drop a projected graph if it exists. Catalog-only — touches no data."""
    client = gds()
    try:
        if client.graph.exists(name)["exists"]:
            client.graph.get(name).drop()
    except Exception:  # pragma: no cover - best effort
        pass


def build_cooccurrence_graph():
    """Project entity↔entity co-occurrence, weighted by shared chunk count.

    All labels go in together so cross-label edges enrich the vectors — that a
    person co-occurs with the same rivers and nations as another person is
    exactly the evidence we want. Filtered node similarity then restricts the
    *pairs* to same-label ones.

    Runs inside a read transaction: `gds.graph.cypher.project` is issued by the
    client with `QueryMode.READ`.
    """
    drop_graph(COOCCURRENCE_GRAPH)
    graph, _ = gds().graph.cypher.project(
        COOCCURRENCE_PROJECTION,
        graphName=COOCCURRENCE_GRAPH,
        minCount=MIN_CHUNK_COUNT,
    )
    return graph


def cooccurrence_candidates(
    graph, inventory: dict[int, EntityRef], label: str
) -> list[CandidatePair]:
    """Filtered cosine similarity over co-occurrence vectors, same-label only."""
    frame = gds().nodeSimilarity.filtered.stream(
        graph,
        sourceNodeFilter=label,
        targetNodeFilter=label,
        topK=TOP_K,
        similarityCutoff=COSINE_CUTOFF,
        similarityMetric="COSINE",
        relationshipWeightProperty="chunkCount",
    )

    pairs: list[CandidatePair] = []
    for row in frame.itertuples():
        left = inventory.get(row.node1)
        right = inventory.get(row.node2)
        if left is None or right is None or left.node_id == right.node_id:
            continue
        pairs.append(
            CandidatePair(
                left=left,
                right=right,
                signals={"cooccurrence"},
                similarity=float(row.similarity),
            )
        )
    return pairs


# ── Signal 2: string similarity ───────────────────────────────────────────────

STRING_CANDIDATES = """
MATCH (a:{label}), (b:{label})
WHERE a.canonicalName < b.canonicalName
  AND NOT a:GenericLocation AND NOT b:GenericLocation
WITH a, b,
     [t IN split(toLower(a.canonicalName), ' ') | trim(replace(t, '.', ''))] AS tokA_raw,
     [t IN split(toLower(b.canonicalName), ' ') | trim(replace(t, '.', ''))] AS tokB_raw
WITH a, b,
     CASE WHEN size(tokA_raw) > 1 AND head(tokA_raw) IN $titles
          THEN tail(tokA_raw) ELSE tokA_raw END AS tokA,
     CASE WHEN size(tokB_raw) > 1 AND head(tokB_raw) IN $titles
          THEN tail(tokB_raw) ELSE tokB_raw END AS tokB
WITH a, b, tokA, tokB,
     apoc.text.join(tokA, ' ') AS strippedA,
     apoc.text.join(tokB, ' ') AS strippedB
WITH a, b, tokA, tokB, strippedA, strippedB,
     1 - apoc.text.jaroWinklerDistance(strippedA, strippedB) AS jw,
     apoc.text.doubleMetaphone(last(tokA)) AS metLastA,
     apoc.text.doubleMetaphone(last(tokB)) AS metLastB
WHERE strippedA <> '' AND strippedB <> ''
  AND (
    // 1. Jaro-Winkler, blocked on first character
    (left(strippedA, 1) = left(strippedB, 1) AND jw >= $jaroCutoff)
    // 2. Token containment — every token of the shorter name is in the longer
    OR (size(tokA) <= size(tokB) AND size(tokA) > 1
        AND all(t IN tokA WHERE size(t) >= 3) AND all(t IN tokA WHERE t IN tokB))
    OR (size(tokB) <  size(tokA) AND size(tokB) > 1
        AND all(t IN tokB WHERE size(t) >= 3) AND all(t IN tokB WHERE t IN tokA))
    // 3. Double metaphone on the last token — the "Chabonah" case
    OR (metLastA <> '' AND metLastB <> ''
        AND size(metLastA) >= 3 AND size(metLastB) >= 3
        AND left(metLastA, 1) = left(metLastB, 1)
        AND 1 - apoc.text.jaroWinklerDistance(metLastA, metLastB) >= $metaphoneCutoff)
  )
RETURN id(a) AS leftId, id(b) AS rightId
"""


def string_candidates(
    inventory: dict[int, EntityRef], label: str
) -> list[CandidatePair]:
    """The string-signal ladder: Jaro-Winkler, token containment, metaphone."""
    rows = read_query(
        STRING_CANDIDATES.format(label=label),
        titles=list(TITLE_TOKENS) if label == "Person" else [],
        jaroCutoff=JARO_CUTOFF,
        metaphoneCutoff=METAPHONE_CUTOFF,
    )
    return _pairs_from_rows(rows, inventory, "string")


# ── Signal 3: aliases ─────────────────────────────────────────────────────────

ALIAS_CANDIDATES = """
MATCH (a:{label}), (b:{label})
WHERE a.canonicalName < b.canonicalName
  AND NOT a:GenericLocation AND NOT b:GenericLocation
  AND (
    any(aa IN coalesce(a.aliases, []) WHERE
          toUpper(aa) = b.canonicalName
          OR any(ba IN coalesce(b.aliases, []) WHERE toLower(aa) = toLower(ba)))
    OR any(ba IN coalesce(b.aliases, []) WHERE toUpper(ba) = a.canonicalName)
  )
RETURN id(a) AS leftId, id(b) AS rightId
"""


def alias_candidates(
    inventory: dict[int, EntityRef], label: str
) -> list[CandidatePair]:
    """Pairs sharing an alias, or where one node's alias is the other's name."""
    rows = read_query(ALIAS_CANDIDATES.format(label=label))
    return _pairs_from_rows(rows, inventory, "alias")


def _pairs_from_rows(
    rows: list[dict], inventory: dict[int, EntityRef], signal: str
) -> list[CandidatePair]:
    pairs: list[CandidatePair] = []
    for row in rows:
        left = inventory.get(row["leftId"])
        right = inventory.get(row["rightId"])
        if left is None or right is None:
            continue
        pairs.append(CandidatePair(left=left, right=right, signals={signal}))
    return pairs


# ── Union of signals ──────────────────────────────────────────────────────────


def _person_pair_allowed(left: EntityRef, right: EntityRef) -> bool:
    """Person-specific gate carried over from the original pipeline.

    Only merge multi-word names with multi-word names, unless one side is a
    known-unambiguous single name. This is why `HOWARD` and `THOMAS HOWARD`
    survive as separate nodes — the gate is deliberately conservative, and the
    demo surfaces exactly what it leaves behind.
    """
    both_multi = " " in left.name and " " in right.name
    one_famous = (
        left.name in UNAMBIGUOUS_SINGLE_NAMES or right.name in UNAMBIGUOUS_SINGLE_NAMES
    )
    return both_multi or one_famous


def candidates(
    label: str,
    *,
    graph=None,
    inventory: dict[int, EntityRef] | None = None,
    use_cooccurrence: bool = True,
    apply_person_gate: bool = True,
) -> list[CandidatePair]:
    """All candidate duplicate pairs for one label, unioned across signals.

    Pairs proposed by more than one signal are merged into a single
    `CandidatePair` whose `signals` set records everything that fired — which is
    the most useful column in the demo output, because agreement between an
    independent string signal and an independent graph signal is far stronger
    evidence than either alone.
    """
    inventory = inventory if inventory is not None else entities()

    proposed: list[CandidatePair] = []
    if use_cooccurrence and graph is not None:
        proposed += cooccurrence_candidates(graph, inventory, label)
    proposed += string_candidates(inventory, label)
    proposed += alias_candidates(inventory, label)

    merged: dict[tuple[int, int], CandidatePair] = {}
    for pair in proposed:
        existing = merged.get(pair.key)
        if existing is None:
            merged[pair.key] = pair
            continue
        existing.signals |= pair.signals
        if pair.similarity is not None:
            existing.similarity = pair.similarity

    result = list(merged.values())
    if label == "Person" and apply_person_gate:
        result = [p for p in result if _person_pair_allowed(p.left, p.right)]

    result.sort(key=lambda p: (-len(p.signals), -(p.similarity or 0.0), p.names))
    return result


def filter_pairs(
    pairs: list[CandidatePair], *, signals: set[str] | None = None
) -> list[CandidatePair]:
    """Keep only pairs proposed by at least one of ``signals``.

    Exists because the three signals have wildly different precision, and the
    demo needs to show that rather than assert it. On this corpus the
    co-occurrence signal alone proposes 1,192 Person pairs; string and alias
    together propose 78. Feed all of them into transitive closure and WCC
    returns one 93-node component containing both captains, Sacagawea, York and
    most of the sergeants — because the corps genuinely did travel together, so
    their co-occurrence vectors genuinely are near-parallel.

    That is not a bug in node similarity. It is node similarity answering the
    question it was asked. The lesson for the slide is that co-occurrence is a
    **recall** instrument: it is how you find candidates worth paying to
    adjudicate, and it is not by itself evidence of identity.
    """
    if signals is None:
        return list(pairs)
    return [p for p in pairs if p.signals & signals]


def signal_breakdown(pairs: list[CandidatePair]) -> dict[str, int]:
    """How many pairs each signal contributed, for the demo's summary line."""
    counts: dict[str, int] = defaultdict(int)
    for pair in pairs:
        for signal in pair.signals:
            counts[signal] += 1
        if len(pair.signals) > 1:
            counts["multi-signal"] += 1
    counts["total"] = len(pairs)
    return dict(counts)


# ── Transitive closure: real WCC, zero writes ─────────────────────────────────

PAIR_PROJECTION = """
UNWIND $pairs AS pair
MATCH (a) WHERE id(a) = pair[0]
MATCH (b) WHERE id(b) = pair[1]
RETURN gds.graph.project(
    $graphName, a, b,
    {
        sourceNodeLabels: labels(a),
        targetNodeLabels: labels(b),
        relationshipType: 'CANDIDATE_SAME_AS'
    },
    {undirectedRelationshipTypes: ['CANDIDATE_SAME_AS']}
)
"""


def components(
    pairs: list[CandidatePair], inventory: dict[int, EntityRef]
) -> list[Component]:
    """Run real `gds.wcc.stream` over the candidate pairs. Writes nothing.

    This is the step the original pipeline could only reach by first writing
    `IS_SAME_ENTITY_AS` relationships into the database. Because the pairs are
    node-id tuples, they project directly:

        UNWIND $pairs AS pair
        MATCH (a) WHERE id(a) = pair[0]
        MATCH (b) WHERE id(b) = pair[1]
        RETURN gds.graph.project(...)

    The result is the same components over the same edges — the graph just lives
    in GDS memory for the duration of the call instead of in the store forever.

    Components of size 2 are single confirmed pairs. Components larger than that
    are where transitive closure did work no pairwise comparison could: A≈B and
    B≈C were found by different signals, and only WCC concludes A≈C.
    """
    if not pairs:
        return []

    drop_graph(PAIR_GRAPH)
    graph, _ = gds().graph.cypher.project(
        PAIR_PROJECTION,
        graphName=PAIR_GRAPH,
        pairs=[list(pair.key) for pair in pairs],
    )
    try:
        frame = gds().wcc.stream(graph)
    finally:
        graph.drop()

    grouped: dict[int, list[EntityRef]] = defaultdict(list)
    for row in frame.itertuples():
        ref = inventory.get(row.nodeId)
        if ref is not None:
            grouped[int(row.componentId)].append(ref)

    result = [
        Component(component_id=cid, members=members)
        for cid, members in grouped.items()
        if len(members) > 1
    ]
    result.sort(key=lambda c: (-c.size, c.describe()))
    return result


# ── Gold set ──────────────────────────────────────────────────────────────────

GOLD_PATH = Path(__file__).resolve().parent.parent / "questions" / "corps_members.yaml"


@dataclass
class GoldSet:
    """Identity-based gold set.

    The unit is an *identity* — one person, listed under every surface form that
    exists in the graph as its own node. That is what makes both precision and
    recall computable: a pair within an identity is correct, a pair spanning two
    identities is wrong, and the set of all within-identity pairs is the
    denominator recall needs.
    """

    roster: set[str]
    #: person -> the surface forms in the graph that denote them
    identities: dict[str, set[str]]
    #: extraction artifacts (two names concatenated); excluded from scoring
    malformed: set[str]
    #: probably-a-misreading, but not asserted; excluded from scoring
    uncertain: dict[str, str]
    #: pairs that are different people despite looking similar
    never_merge: list[dict]

    @property
    def name_to_identity(self) -> dict[str, str]:
        return {
            name: person
            for person, names in self.identities.items()
            for name in names
        }

    @property
    def never_merge_keys(self) -> set[frozenset[str]]:
        return {frozenset(entry["names"]) for entry in self.never_merge}

    def excluded(self) -> set[str]:
        return self.malformed | set(self.uncertain)


def load_gold(path: Path | None = None) -> GoldSet:
    data = yaml.safe_load((path or GOLD_PATH).read_text())

    identities: dict[str, set[str]] = {}
    for entry in data.get("identities", []) or []:
        person = entry["person"].strip().upper()
        identities[person] = {n.strip().upper() for n in entry.get("names", [])}

    return GoldSet(
        roster={name.strip().upper() for name in data.get("roster", [])},
        identities=identities,
        malformed={n.strip().upper() for n in data.get("malformed", []) or []},
        uncertain={
            e["name"].strip().upper(): e.get("probably", "").strip().upper()
            for e in data.get("uncertain", []) or []
        },
        never_merge=data.get("never_merge", []) or [],
    )


def present_names(names: set[str], label: str = "Person") -> set[str]:
    """Which of ``names`` exist as nodes. One round trip."""
    if not names:
        return set()
    rows = read_query(
        f"""
        UNWIND $names AS name
        MATCH (p:{label} {{canonicalName: name}})
        RETURN DISTINCT name
        """,
        names=sorted(names),
    )
    return {row["name"] for row in rows}


def roster_presence(gold: GoldSet) -> tuple[set[str], set[str]]:
    """Split the reference roster into names present and absent in the graph."""
    present = present_names(gold.roster)
    return present, gold.roster - present


@dataclass
class Scores:
    """Precision and recall over the identity gold set."""

    evaluable: int
    true_positives: list[CandidatePair]
    false_positives: list[CandidatePair]
    #: Within-identity pairs that exist in the graph but were never proposed
    missed: list[tuple[str, str, str]]
    recall_denominator: int
    hard_negatives_caught: list[CandidatePair]
    hard_negatives_total: int
    #: Identities with more than one node still in the graph
    split_identities: dict[str, set[str]]

    @property
    def precision(self) -> float | None:
        if self.evaluable == 0:
            return None
        return len(self.true_positives) / self.evaluable

    @property
    def recall(self) -> float | None:
        if self.recall_denominator == 0:
            return None
        return len(self.true_positives) / self.recall_denominator


def score(pairs: list[CandidatePair], gold: GoldSet, present: set[str]) -> Scores:
    """Score candidate pairs against the identity gold set.

    A pair is **evaluable** when both endpoints are surface forms of a known
    identity and neither is excluded. Within one identity it is a true positive;
    spanning two it is a false positive. Everything else is unlabelled — the
    corpus holds thousands of people this gold set says nothing about, and
    counting them either way would be inventing a number.

    Recall's denominator is every within-identity pair whose endpoints both
    exist in the graph. That is a real denominator: it is exactly the set of
    duplicate pairs the pipeline *should* have found and did not merge.
    """
    lookup = gold.name_to_identity
    excluded = gold.excluded()
    never_merge = gold.never_merge_keys

    evaluable: list[CandidatePair] = []
    true_positives: list[CandidatePair] = []
    false_positives: list[CandidatePair] = []
    caught: list[CandidatePair] = []
    proposed: set[frozenset[str]] = set()

    for pair in pairs:
        names = frozenset(pair.names)
        if names in never_merge:
            caught.append(pair)

        left, right = pair.names
        if left in excluded or right in excluded:
            continue
        left_identity = lookup.get(left)
        right_identity = lookup.get(right)
        if left_identity is None or right_identity is None:
            continue

        evaluable.append(pair)
        proposed.add(names)
        if left_identity == right_identity:
            true_positives.append(pair)
        else:
            false_positives.append(pair)

    # Recall denominator: every within-identity pair still split in the graph.
    split: dict[str, set[str]] = {}
    denominator = 0
    missed: list[tuple[str, str, str]] = []
    for person, names in gold.identities.items():
        live = sorted(n for n in names if n in present and n not in excluded)
        if len(live) < 2:
            continue
        split[person] = set(live)
        for i, left in enumerate(live):
            for right in live[i + 1 :]:
                denominator += 1
                if frozenset((left, right)) not in proposed:
                    missed.append((person, left, right))

    return Scores(
        evaluable=len(evaluable),
        true_positives=true_positives,
        false_positives=false_positives,
        missed=missed,
        recall_denominator=denominator,
        hard_negatives_caught=caught,
        hard_negatives_total=len(never_merge),
        split_identities=split,
    )


# ── Recall, replayed from alias arrays ────────────────────────────────────────

ALIAS_REPLAY = """
UNWIND $probes AS probe
WITH probe[0] AS canonical, probe[1] AS alias
WITH canonical, alias,
     [t IN split(toLower(canonical), ' ') | trim(replace(t, '.', ''))] AS tokC_raw,
     [t IN split(toLower(alias),     ' ') | trim(replace(t, '.', ''))] AS tokA_raw
WITH canonical, alias,
     CASE WHEN size(tokC_raw) > 1 AND head(tokC_raw) IN $titles
          THEN tail(tokC_raw) ELSE tokC_raw END AS tokC,
     CASE WHEN size(tokA_raw) > 1 AND head(tokA_raw) IN $titles
          THEN tail(tokA_raw) ELSE tokA_raw END AS tokA
WITH canonical, alias, tokC, tokA,
     apoc.text.join(tokC, ' ') AS strippedC,
     apoc.text.join(tokA, ' ') AS strippedA
WITH canonical, alias, tokC, tokA, strippedC, strippedA,
     1 - apoc.text.jaroWinklerDistance(strippedC, strippedA) AS jw,
     apoc.text.doubleMetaphone(last(tokC)) AS metC,
     apoc.text.doubleMetaphone(last(tokA)) AS metA
RETURN canonical,
       alias,
       strippedC <> '' AND strippedA <> ''
         AND left(strippedC, 1) = left(strippedA, 1)
         AND jw >= $jaroCutoff                                        AS byJaro,
       (size(tokA) <= size(tokC) AND size(tokA) > 1
         AND all(t IN tokA WHERE size(t) >= 3)
         AND all(t IN tokA WHERE t IN tokC))
       OR (size(tokC) < size(tokA) AND size(tokC) > 1
         AND all(t IN tokC WHERE size(t) >= 3)
         AND all(t IN tokC WHERE t IN tokA))                          AS byContainment,
       metC <> '' AND metA <> '' AND size(metC) >= 3 AND size(metA) >= 3
         AND left(metC, 1) = left(metA, 1)
         AND 1 - apoc.text.jaroWinklerDistance(metC, metA) >= $metaphoneCutoff AS byMetaphone
"""


@dataclass
class AliasRecall:
    """How much of what past resolution merged the string ladder would re-find.

    Honest limitation, and worth saying out loud from the stage: this replays
    the **string signals only**. The co-occurrence signal cannot be replayed,
    because the alias no longer exists as a node — it has no co-occurrence
    vector of its own to compare. So this number is a floor on the full
    pipeline's recall, not an estimate of it. The graph signal's contribution
    shows up in candidate generation on live nodes, not here.
    """

    total: int
    by_jaro: int
    by_containment: int
    by_metaphone: int
    caught: int
    missed: list[tuple[str, str]]

    @property
    def recall(self) -> float | None:
        return self.caught / self.total if self.total else None


def alias_recall(label: str = "Person", *, limit_to: set[str] | None = None) -> AliasRecall:
    """Replay the string ladder against alias/canonical pairs already merged.

    The `aliases` array on a resolved node is a receipt: every string in it was
    once a separate node that some pass decided was the same entity. Testing the
    ladder against those pairs measures what it would catch if it saw them fresh.
    """
    rows = read_query(
        f"""
        MATCH (n:{label})
        WHERE n.canonicalName IS NOT NULL AND n.aliases IS NOT NULL
        UNWIND n.aliases AS alias
        WITH n.canonicalName AS canonical, toUpper(alias) AS alias
        WHERE alias <> canonical AND trim(alias) <> ''
        RETURN DISTINCT canonical, alias
        """
    )
    if limit_to is not None:
        rows = [r for r in rows if r["canonical"] in limit_to]
    if not rows:
        return AliasRecall(0, 0, 0, 0, 0, [])

    results = read_query(
        ALIAS_REPLAY,
        probes=[[r["canonical"], r["alias"]] for r in rows],
        titles=list(TITLE_TOKENS) if label == "Person" else [],
        jaroCutoff=JARO_CUTOFF,
        metaphoneCutoff=METAPHONE_CUTOFF,
    )

    by_jaro = by_containment = by_metaphone = caught = 0
    missed: list[tuple[str, str]] = []
    for row in results:
        hit_jaro = bool(row["byJaro"])
        hit_containment = bool(row["byContainment"])
        hit_metaphone = bool(row["byMetaphone"])
        by_jaro += hit_jaro
        by_containment += hit_containment
        by_metaphone += hit_metaphone
        if hit_jaro or hit_containment or hit_metaphone:
            caught += 1
        else:
            missed.append((row["canonical"], row["alias"]))

    return AliasRecall(
        total=len(results),
        by_jaro=by_jaro,
        by_containment=by_containment,
        by_metaphone=by_metaphone,
        caught=caught,
        missed=missed,
    )


# ── Write audit ───────────────────────────────────────────────────────────────


@dataclass
class Snapshot:
    """Counts and alias samples, taken before and after a run."""

    nodes: int
    relationships: int
    entities: int
    labels: dict[str, int]
    rel_types: dict[str, int]
    alias_sample: dict[str, list[str]]

    def diff(self, other: "Snapshot") -> list[str]:
        """Every difference between two snapshots. Empty means zero writes."""
        changes: list[str] = []
        for field_name in ("nodes", "relationships", "entities"):
            before, after = getattr(self, field_name), getattr(other, field_name)
            if before != after:
                changes.append(f"{field_name}: {before:,} → {after:,}")

        for name, mapping in (("label", "labels"), ("relationship type", "rel_types")):
            before_map = getattr(self, mapping)
            after_map = getattr(other, mapping)
            for key in sorted(set(before_map) | set(after_map)):
                before = before_map.get(key, 0)
                after = after_map.get(key, 0)
                if before != after:
                    changes.append(f"{name} {key}: {before:,} → {after:,}")

        for key in sorted(set(self.alias_sample) | set(other.alias_sample)):
            before = self.alias_sample.get(key)
            after = other.alias_sample.get(key)
            if before != after:
                changes.append(f"aliases[{key}]: {before} → {after}")

        return changes


#: Nodes whose alias arrays are sampled in the audit. These are the ones a
#: merge would rewrite first, so they are the most sensitive tripwire available.
ALIAS_SAMPLE_NAMES = [
    "SACAGAWEA",
    "MERIWETHER LEWIS",
    "WILLIAM CLARK",
    "TOUSSAINT CHARBONNEAU",
    "SHOSHONE",
    "HIDATSA",
]


def snapshot() -> Snapshot:
    """Capture the database's shape, for before/after comparison."""
    counts = read_query(
        """
        CALL { MATCH (n) RETURN count(n) AS nodes }
        CALL { MATCH ()-[r]->() RETURN count(r) AS relationships }
        CALL { MATCH (e) WHERE NOT e:Chunk AND e.canonicalName IS NOT NULL
               RETURN count(e) AS entities }
        RETURN nodes, relationships, entities
        """
    )[0]

    labels = {
        row["label"]: row["count"]
        for row in read_query(
            """
            CALL db.labels() YIELD label
            CALL (label) {
                MATCH (n) WHERE label IN labels(n) RETURN count(n) AS count
            }
            RETURN label, count
            """
        )
    }
    rel_types = {
        row["relType"]: row["count"]
        for row in read_query(
            """
            CALL db.relationshipTypes() YIELD relationshipType AS relType
            CALL (relType) {
                MATCH ()-[r]->() WHERE type(r) = relType RETURN count(r) AS count
            }
            RETURN relType, count
            """
        )
    }

    alias_rows = read_query(
        """
        UNWIND $names AS name
        MATCH (n {canonicalName: name})
        RETURN name, coalesce(n.aliases, []) AS aliases
        """,
        names=ALIAS_SAMPLE_NAMES,
    )

    return Snapshot(
        nodes=counts["nodes"],
        relationships=counts["relationships"],
        entities=counts["entities"],
        labels=labels,
        rel_types=rel_types,
        alias_sample={row["name"]: sorted(row["aliases"]) for row in alias_rows},
    )

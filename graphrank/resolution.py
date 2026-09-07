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

What each signal is actually worth
─────────────────────────────────
Measured on `rawluna`, the canonical pre-disambiguation baseline (see "Which
database to measure on" below), Person label, against the identity gold set in
`questions/corps_members.yaml`:

    signals              pairs    TP    FP   precision   recall
    string + alias         802    29     8        0.78     0.16
    co-occurrence only   1,028     7   446        0.02     0.04
    all three            1,814    32   450        0.07     0.18

Taken at face value the co-occurrence row is damning: 7 right, 446 wrong. As a
*decision* procedure it is useless.

But it is not a decision procedure. Run the adjudicator over those 453 scoreable
pairs and it rejects 445, keeping 7 of the 7 true positives and one false one —
precision 0.015 -> 0.875. And three of the survivors are pairs no string signal
can reach:

    INDIAN WOMAN  ~  THE SQUAR     1.000
    SACAGAWEA     ~  THE SQUAR     1.000
    INDIAN WOMAN  ~  SACAGAWEA     0.725

That is the complete Sacagawea identity — three surface forms with nothing in
common as strings — handed to WCC, which closes them into one entity. It is the
single best demonstration in the section, and only the graph signal produces it.

So the shape of the thing is:

    recall is what the algorithm is for
    precision is what the adjudicator is for

811 Person nodes make 328,455 possible pairs. The three signals propose 1,814 of
them — a 181x cut — and the adjudicator cleans up what is left for fractions of
a cent. A signal with 1.5% precision is not a broken signal when something
downstream can afford to filter it. That is why this module returns candidates
and verdicts as *values* and decides nothing itself.

Which database to measure on
────────────────────────────
Not the shipped release dump. That is the *post*-pipeline graph —
`build_graph.py` runs `disambiguate.py` twice before cutting it — so the
duplicates left in it are the ones that run failed to find. And its signals were
not equally alive: because of the inverted comparison documented at
`JARO_CUTOFF` above, its Jaro-Winkler and metaphone branches never fired, while
co-occurrence worked and swept the corpus. What remains is close to the
complement of what co-occurrence can find, handed to a string ladder that never
got to run. Measured there, co-occurrence looks worthless *by construction* —
and the numbers above are meaningfully different from the ones that graph gives.

`demo_resolution.py --compare-signals` detects this and says so. Measure on
`rawluna` instead: `NEO4J_DATABASE=rawluna python scripts/demo_resolution.py`.

Note also that there is no fully unresolved state in this pipeline: `extract.py`
resolves as it extracts, assigning a canonical name per mention and filing the
raw surface form as an alias, so freshly extracted nodes already carry
"Capt. Lewis" and "Chabonah". The right baseline is *post-extraction,
pre-disambiguation* — which is exactly the state `disambiguate.py` operates on,
and therefore the right place to judge its signals.

None of this touches the query-time use of the same algorithm. "Which chunks
share entities with this chunk" is a different question and does real work —
that is `graphrank/cooccurrence.py`.
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

#: Similarity metric and its cutoff, chosen together — changing one without
#: re-tuning the other measures the pair, not the change.
#:
#: The source pipeline used COSINE at 0.5. Swept against the gold set on
#: `rawluna` (Person, best operating point per metric):
#:
#:     metric    weight        thr   pairs  TP   FP   precision  recall
#:     COSINE    chunkCount   0.35     363   4  359      0.011    0.022
#:     COSINE    idfWeighted  0.30     371   4  367      0.011    0.022
#:     JACCARD   chunkCount   0.10     253   1  252      0.004    0.006
#:     JACCARD   idfWeighted  0.05     313   2  311      0.006    0.011
#:     OVERLAP   chunkCount   0.95     202   6  196      0.030    0.033
#:     OVERLAP   idfWeighted  0.95     148   6  142      0.041    0.033
#:
#: OVERLAP wins, and the reason is structural rather than empirical. Duplicate
#: surface forms are *asymmetric*: `SACAGAWEA` occurs in 8 chunks and has 5
#: co-occurrence neighbours, `INDIAN WOMAN` occurs in 24 and has 38. JACCARD
#: divides by the union and so punishes that mismatch — it is the worst metric
#: here, and it loses the pair entirely. COSINE tolerates it. OVERLAP, which
#: divides by min(|A|,|B|), asks the question duplicate detection actually wants:
#: *is the rare name's context contained in the common name's?*
SIMILARITY_METRIC = "OVERLAP"
COSINE_CUTOFF = 0.70

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
#: Minimum shared chunks before an entity-entity edge is projected.
#:
#: The source pipeline used 2. That looks like sensible noise control and is
#: actively harmful here, because it is the *rare* surface forms that need
#: resolving and they are exactly the ones a floor removes. Thirteen of the
#: nineteen nodes that refer to Sacagawea appear in a single chunk, so at a
#: floor of 2 they have no edges at all and are invisible to node similarity —
#: unreachable, not merely low-scoring.
#:
#: Dropping it to 1 improves every measure at once, which is rare enough to be
#: worth stating plainly (Person, `rawluna`, OVERLAP/idfWeighted):
#:
#:     minCount   pairs   TP    FP   precision   recall   unique TPs
#:            2   1,028    8   467       0.017    0.024            4
#:            1   1,359   10   242       0.040    0.030           10
#:
#: More candidates, *half* the false positives, 2.4x the precision, and 2.5x the
#: true positives that no string signal can reach. The denser graph is also
#: better conditioned: with more neighbours per node, fewer pairs achieve the
#: trivial OVERLAP score of 1.0 that comes from one tiny neighbourhood sitting
#: inside a larger one.
#:
#: Costs a bigger projection — 5,123 nodes / 156,062 relationships versus
#: 1,441 / 26,908 — which still projects in seconds.
MIN_CHUNK_COUNT = 1

#: Neighbours per source node kept by nodeSimilarity.
#:
#: Not a cosmetic knob. At the source pipeline's TOP_K=10 — and at 25 — the
#: `SACAGAWEA ~ INDIAN WOMAN` pair does not appear in OVERLAP output *at all*,
#: because 138 other labelled pairs score a perfect 1.0 and saturate the list.
#: Those perfect scores are trivial containment: any 2-neighbour node sits
#: entirely inside a 38-neighbour node. Raising TOP_K to 100 restores the pair
#: at 0.725. Anything above 100 changes nothing.
TOP_K = 100

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
WITH e1, e2, chunkCount,
     count { (e1)-[:MENTIONED_IN]->(:Chunk) } AS df1,
     count { (e2)-[:MENTIONED_IN]->(:Chunk) } AS df2
RETURN gds.graph.project(
    $graphName, e1, e2,
    {
        sourceNodeLabels: labels(e1),
        targetNodeLabels: labels(e2),
        relationshipType: 'MENTIONED_WITH',
        relationshipProperties: {
            chunkCount: toFloat(chunkCount),
            idfWeighted: CASE WHEN df1 = 0 OR df2 = 0 THEN 0.0 ELSE
                toFloat(chunkCount)
                * log(1.0 + toFloat($totalChunks) / df1)
                * log(1.0 + toFloat($totalChunks) / df2)
            END
        }
    },
    {undirectedRelationshipTypes: ['MENTIONED_WITH']}
)
"""

#: Which relationship property `cooccurrence_candidates` scores on.
#:
#: ``chunkCount``   raw shared-chunk count, as the source pipeline used
#: ``idfWeighted``  the same count discounted by both endpoints' inverse chunk
#:                  frequency
#:
#: The IDF variant exists because of what the one true positive on this corpus
#: turned out to be made of. `SACAGAWEA` and `INDIAN WOMAN` never share a chunk;
#: they match through four shared neighbours, and **79% of the resulting cosine
#: comes from MERIWETHER LEWIS and WILLIAM CLARK** — who co-occur with nearly
#: everyone and therefore say almost nothing about identity. Only 22% comes from
#: TOUSSAINT CHARBONNEAU (her husband) and HIDATSA (her nation), which are the
#: neighbours that actually identify her.
#:
#: That is the same hub trap the retrieval projection already defuses, one stage
#: earlier: `projection.py` IDF-weights its MENTIONS edges precisely so a shared
#: mention of Beaverhead Rock outweighs a shared mention of Lewis.
#:
#: **Measured, it does not help — and that is the interesting part.** Under IDF
#: the composition flips as intended: Charbonneau goes from 16.5% of the cosine
#: to 48.4% and the two captains fall from 78.7% to 43.6%, so the match is made
#: for the right reason. But precision is unchanged (0.006 -> 0.007 on
#: `rawluna`), a third fewer candidates buys nothing, on `rawgraph` it costs a
#: true positive, and it drags this very match from 0.647 down to 0.501 against
#: a 0.5 cutoff.
#:
#: The reason is that the two algorithms fail differently. PageRank's problem is
#: hubs — a ubiquitous node creates shortcuts, and down-weighting it fixes that.
#: Node similarity's problem here is *sparsity*: SACAGAWEA has five neighbours,
#: and cosine over five dimensions is high whenever three or four coincide, no
#: matter how they are weighted. Reweighting redistributes evidence; it does not
#: create any.
#:
#: So `chunkCount` stays the default. Both remain available because the negative
#: result is worth being able to reproduce.
#:
#: Note the arithmetic works out cleanly for cosine. Weighting an edge by
#: ``idf(e1) * idf(e2)`` scales each node's whole vector by its own IDF, and
#: cosine is scale-invariant — so a node's own IDF cancels, and what survives is
#: exactly a discount on each *shared neighbour*. One symmetric edge weight gets
#: the asymmetric effect we want.
COOCCURRENCE_WEIGHTS = ("chunkCount", "idfWeighted")


def drop_graph(name: str) -> None:
    """Drop a projected graph if it exists. Catalog-only — touches no data."""
    client = gds()
    try:
        if client.graph.exists(name)["exists"]:
            client.graph.get(name).drop()
    except Exception:  # pragma: no cover - best effort
        pass


def build_cooccurrence_graph(min_count: int | None = None):
    """Project entity↔entity co-occurrence, weighted by shared chunk count.

    All labels go in together so cross-label edges enrich the vectors — that a
    person co-occurs with the same rivers and nations as another person is
    exactly the evidence we want. Filtered node similarity then restricts the
    *pairs* to same-label ones.

    Runs inside a read transaction: `gds.graph.cypher.project` is issued by the
    client with `QueryMode.READ`.
    """
    drop_graph(COOCCURRENCE_GRAPH)
    total = read_query("MATCH (c:Chunk) RETURN count(c) AS n")[0]["n"]
    graph, _ = gds().graph.cypher.project(
        COOCCURRENCE_PROJECTION,
        graphName=COOCCURRENCE_GRAPH,
        minCount=MIN_CHUNK_COUNT if min_count is None else min_count,
        totalChunks=total,
    )
    return graph


def cooccurrence_candidates(
    graph,
    inventory: dict[int, EntityRef],
    label: str,
    *,
    weight: str = "idfWeighted",
    metric: str = SIMILARITY_METRIC,
    cutoff: float = COSINE_CUTOFF,
    top_k: int = TOP_K,
) -> list[CandidatePair]:
    """Filtered similarity over co-occurrence vectors, same-label only.

    ``weight`` selects the edge property (:data:`COOCCURRENCE_WEIGHTS`);
    ``metric`` is one of COSINE / JACCARD / OVERLAP — see
    :data:`SIMILARITY_METRIC` for why the default is OVERLAP.
    """
    if weight not in COOCCURRENCE_WEIGHTS:
        raise ValueError(f"weight must be one of {COOCCURRENCE_WEIGHTS}")
    frame = gds().nodeSimilarity.filtered.stream(
        graph,
        sourceNodeFilter=label,
        targetNodeFilter=label,
        topK=top_k,
        similarityCutoff=cutoff,
        similarityMetric=metric,
        relationshipWeightProperty=weight,
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
    weight: str = "idfWeighted",
    metric: str = SIMILARITY_METRIC,
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
        proposed += cooccurrence_candidates(
            graph, inventory, label, weight=weight, metric=metric
        )
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


# ── Layer 1: evidence sufficiency ─────────────────────────────────────────────

#: Minimum chunks one endpoint of a confirmed pair must have.
#:
#: The failure this prevents is specific and was measured, not guessed. A
#: one-chunk node paired with another one-chunk node gives the judge nothing to
#: discriminate with, so it falls back on whatever identity it recognises. On
#: this corpus that produced 27 confirmations of `SQUAR INTERPRETRESS` against
#: one-chunk Native leaders from three different nations — TIN NACH-E-MOO-TOOLT
#: (Nez Perce), MAN-NES-SUR REE (Hidatsa), CONIA COMAWOOL (Clatsop) — every one
#: resolved to "Sacagawea".
#:
#: Requiring one well-evidenced endpoint removed 21 of the 25 contaminants from
#: her cluster and cost **nothing**: all 14 of her surface forms survived,
#: because the sparse ones still reach the cluster through `INDIAN WOMAN` (24
#: chunks) and `SACAGAWEA` (8). The 18 dropped edges were redundant.
#:
#: **This is deliberately not a "generic reference" filter.** The obvious
#: framing — flag vague-sounding names, an analogue of
#: `flag_generic_locations.py` — fails on this corpus and would do real harm.
#: "The Indian woman" is culturally generic and referentially unique: there was
#: one. "The interpreter" is equally generic and genuinely ambiguous: there were
#: four. No string test and no LLM prompt separates those without the corpus,
#: and a plausible prompt deletes Sacagawea's references, which are phrased the
#: way women were referred to in 1804.
#:
#: Evidence sufficiency sidesteps the whole question. It never reads the words.
MIN_EVIDENCE_CHUNKS = 2


def filter_by_evidence(
    pairs: list[CandidatePair], *, min_chunks: int = MIN_EVIDENCE_CHUNKS
) -> list[CandidatePair]:
    """Drop confirmed pairs where neither side has enough support to judge."""
    return [
        p for p in pairs
        if max(p.left.mentions, p.right.mentions) >= min_chunks
    ]


# ── Layer 2: transitivity verification — catching bridge nodes before closure ─


@dataclass
class Bridge:
    """A node whose confirmed neighbours are *not* the same as each other."""

    node: EntityRef
    left: EntityRef
    right: EntityRef
    #: True when the contradiction came from the cache rather than a fresh call
    from_cache: bool

    def describe(self) -> str:
        return (
            f"{self.node.name}  bridges  {self.left.name}  ~/~  {self.right.name}"
        )


@dataclass
class TransitivityReport:
    bridges: list[Bridge]
    checks_needed: int
    cache_hits: int
    llm_calls: int

    @property
    def bridge_nodes(self) -> set[int]:
        return {b.node.node_id for b in self.bridges}


def verify_transitivity(
    pairs: list[CandidatePair],
    *,
    judge=None,
    max_calls: int = 200,
) -> TransitivityReport:
    """Find bridge nodes among confirmed pairs, before WCC closes over them.

    **The assumption nobody checks.** WCC closure is exactly the claim that
    "same entity" is transitive: A~X and B~X therefore A~B. Adjudication never
    tests that, because it only ever sees pairs. Bridge nodes are precisely
    where the assumption fails — `THE INTERPRETER` is legitimately confirmed
    against both Charbonneau and Drouillard, and closure then fuses two men who
    share nothing but a job.

    So: verify it, but only where it can bite. For each node with two or more
    confirmed neighbours, ask whether those neighbours are the same as each
    other. A "no" means the node is a bridge and is dropped from the merge
    graph — left unmerged, which is the safe default.

    **Most of these questions have already been answered.** Candidate
    adjudication rejects far more pairs than it confirms and the pipeline throws
    those rejections away, but a rejection is exactly the evidence needed here.
    Two people who co-occur constantly — Sacagawea and Charbonneau, say — are
    almost certainly proposed as a candidate and rejected long before anything
    asks whether `HIS WIFE` bridges them. ``judge`` is consulted only for pairs
    with no recorded verdict, and the report says how many were free.

    ``judge(left_name, right_name, label) -> bool | None`` returns None when it
    declines to answer; such pairs are treated as consistent, because refusing
    to merge on an unanswered question is the conservative choice.
    """
    neighbours: dict[int, set[int]] = defaultdict(set)
    refs: dict[int, EntityRef] = {}
    confirmed: set[tuple[int, int]] = set()
    for pair in pairs:
        a, b = pair.left, pair.right
        refs[a.node_id], refs[b.node_id] = a, b
        neighbours[a.node_id].add(b.node_id)
        neighbours[b.node_id].add(a.node_id)
        confirmed.add(pair.key)

    bridges: list[Bridge] = []
    checks = cache_hits = llm_calls = 0

    for node_id, nbrs in sorted(neighbours.items()):
        if len(nbrs) < 2:
            continue
        ordered = sorted(nbrs)
        for i, left_id in enumerate(ordered):
            for right_id in ordered[i + 1 :]:
                key = (min(left_id, right_id), max(left_id, right_id))
                # already confirmed same -> transitivity holds here by definition
                if key in confirmed:
                    continue
                left, right = refs[left_id], refs[right_id]
                checks += 1
                verdict = None
                if judge is not None:
                    verdict, was_cached = judge(left.name, right.name, left.label)
                    if was_cached:
                        cache_hits += 1
                    else:
                        llm_calls += 1
                        if llm_calls >= max_calls:
                            judge = None  # stop spending; remaining treated as consistent
                if verdict is False:
                    bridges.append(
                        Bridge(
                            node=refs[node_id],
                            left=left,
                            right=right,
                            from_cache=bool(verdict is not None and was_cached),
                        )
                    )
                    break
            else:
                continue
            break

    return TransitivityReport(
        bridges=bridges,
        checks_needed=checks,
        cache_hits=cache_hits,
        llm_calls=llm_calls,
    )


def components_verified(
    pairs: list[CandidatePair],
    inventory: dict[int, EntityRef],
    report: TransitivityReport,
    *,
    max_component: int | None = 25,
) -> tuple[list[Component], list[Component]]:
    """Close over confirmed pairs with bridge nodes removed.

    Returns ``(accepted, refused)``. A component larger than ``max_component``
    is refused rather than merged — a backstop for whatever the bridge check
    did not catch. Refusing to merge is always recoverable; merging is not.
    """
    bridge_ids = report.bridge_nodes
    kept = [
        p for p in pairs
        if p.left.node_id not in bridge_ids and p.right.node_id not in bridge_ids
    ]
    closed = components(kept, inventory)
    if max_component is None:
        return closed, []
    accepted = [c for c in closed if c.size <= max_component]
    refused = [c for c in closed if c.size > max_component]
    return accepted, refused


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

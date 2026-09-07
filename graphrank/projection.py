"""Project the retrieval graph into GDS once, then reuse it for every query.

Projection is a one-time cost and it is amortised: 289 ms for ``lc-retrieval``,
94 ms for ``lc-mentions``, once per session.

Be careful with the follow-on claim, though. A PPR call against a projected
graph costs about 55 ms almost regardless of how many seeds it restarts from,
because the cost is per-call overhead rather than source count. Section 5's
retrieval makes two such calls — one per structural signal — so a fresh
question is ~196 ms end to end, against 4 ms for plain cosine. The honest
performance argument is not that the graph work is free, it is that ~200 ms is
invisible beside the generation call that follows.

Three relationship types go into the projection:

``MENTIONS``     entity <-> chunk, weighted by inverse chunk frequency
``NEXT_CHUNK``   chunk <-> chunk, the journal's own reading order
``RELATED``      entity <-> entity, the extracted semantic relationships

The IDF weight on ``MENTIONS`` is doing real work. Without it, every chunk in
the corpus is two hops from every other chunk through MERIWETHER LEWIS, who is
mentioned nearly everywhere. PageRank on that graph returns the same handful of
Lewis-adjacent passages no matter what you ask. Weighting each mention edge by
``log(1 + totalChunks / df)`` makes a shared mention of "Sacagawea" or
"Beaverhead Rock" count for far more than a shared mention of "Lewis".
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .config import gds, query, read_query, settings

# All three types are projected undirected: random walks need to flow
# chunk -> entity -> chunk, and "what preceded this" is as useful as "what
# followed it".
PROJECTION_QUERY = """
CALL {
    // ── entity -> chunk, weighted by inverse chunk frequency ──────────────
    // df = how many distinct chunks mention this entity. Rare entities make
    // strong edges; ubiquitous ones (LEWIS, CLARK) make nearly weightless ones.
    MATCH (e)-[:MENTIONED_IN]->(seen:Chunk)
    WHERE NOT e:Chunk AND NOT e:GenericLocation
    WITH e, count(DISTINCT seen) AS df
    MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
    WITH DISTINCT e, c, df
    RETURN e   AS source,
           c   AS target,
           'MENTIONS' AS relType,
           log(1.0 + toFloat($totalChunks) / df) AS weight

    UNION ALL

    // ── chunk -> chunk, the journals' own sequence ────────────────────────
    MATCH (c1:Chunk)-[:NEXT_CHUNK]->(c2:Chunk)
    RETURN c1 AS source,
           c2 AS target,
           'NEXT_CHUNK' AS relType,
           $nextChunkWeight AS weight

    UNION ALL

    // ── entity -> entity, the extracted semantic relationships ────────────
    MATCH (a)-[r]->(b)
    WHERE NOT a:Chunk AND NOT b:Chunk
      AND NOT a:GenericLocation AND NOT b:GenericLocation
      AND type(r) <> 'MENTIONED_IN'
    RETURN a AS source,
           b AS target,
           'RELATED' AS relType,
           $relatedWeight AS weight
}
RETURN gds.graph.project(
    $graphName,
    source,
    target,
    {
        sourceNodeLabels: labels(source),
        targetNodeLabels: labels(target),
        relationshipType:  relType,
        relationshipProperties: {weight: weight}
    },
    {undirectedRelationshipTypes: ['MENTIONS', 'NEXT_CHUNK', 'RELATED']}
)
"""


# ── The second projection, and why there are two ─────────────────────────────
#
# A projection is not neutral infrastructure: it encodes what you are
# optimising for. ``lc-retrieval`` above is built for reranking, and its IDF
# weights deliberately *suppress* ubiquitous entities.
#
# Multi-seed PPR wants a different graph, for two measured reasons:
#
# 1. ``MENTIONED_IN`` is the only relationship here whose direction is honestly
#    symmetric — "entity appears in passage" is co-membership. Extracted
#    entity-entity edges are not: ``MET`` and ``MARRIED_TO`` are symmetric,
#    ``MEMBER_OF`` and ``TRIBUTARY_OF`` flow importance toward the container,
#    and ``SHOT`` carries no importance semantics at all. PageRank's model
#    needs one consistent meaning for an outbound edge; that graph has none.
# 2. ``NEXT_CHUNK`` is a chain, so it leaks walk mass into passages that are
#    merely adjacent in time rather than related in substance.
#
# The IDF weight is kept as a *property* so it can be switched on and off.
# It matters far more than it looks: naive, the walk decides every question is
# about Lewis, Clark, Drouillard and deer (entity top-8 overlap across
# questions 4.53/8); IDF-weighted, that falls to 0.60/8.
#: Selectable weight expressions for the mentions projection. ``df`` is the
#: entity's chunk frequency; ``ec`` is how many entities the chunk holds.
#:
#: ── Why the choice matters, and why one obvious idea does nothing ──────────
#:
#: A weight that is a function of the **entity alone** cancels out of that
#: entity's own mass distribution: all of SHOSHONE's 192 edges carry the same
#: number, so its outflow divides 192 ways regardless. Measured — mean PPR mass
#: on SHOSHONE's chunks under three schemes:
#:
#:     uniform 1.0              0.001439
#:     1 / df   (inverse degree) 0.001497
#:     IDF                       0.001449
#:
#: So ``idf`` does **not** equalise what a seed contributes per chunk. What it
#: does do is act on the *chunk's* outflow, steering mass toward rare entities —
#: which is why it collapses entity-level hub dominance (cross-question top-8
#: overlap 4.47/8 -> 0.60/8) while leaving seed mass-per-chunk alone.
#:
#: To change a seed's mass split, the weight has to vary **across that seed's
#: edges**. Term frequency would, but there is none to use: of 14,799
#: (entity, chunk) pairs only 131 have more than one edge, max 3, mean 1.009.
#: ``idf_over_entities`` uses entity density as the TF substitute instead — the
#: seed's share of the chunk's entities. A 305-character passage holding three
#: entities gives each a third; a 2,000-character entry holding twenty gives
#: each a twentieth.
#:
#: Measured against the hand-read passages of finding 5d (n=4, so promising
#: rather than settled):
#:
#:     weighting               charbonneau ranks   sacagawea Nov-4 rank
#:     idf (default)                    7, 3, 5                      8
#:     idf_over_entities                5, 6, 3                      3
#:
#: It does not help conjunction — SHOSHONE+EQUUS both/onlyHorse goes 4/8 to
#: 10/6 — so it is a retrieval change, not a fix for the degree imbalance
#: described in the outline's finding 5d.
MENTION_WEIGHTS = {
    "idf": "log(1.0 + toFloat($totalChunks) / df)",
    "idf_over_entities": "log(1.0 + toFloat($totalChunks) / df) / ec",
    "inverse_degree": "1.0 / df",
    "inverse_entities": "1.0 / ec",
    "uniform": "1.0",
}

MENTIONS_PROJECTION_QUERY = """
MATCH (e)-[:MENTIONED_IN]->(seen:Chunk)
WHERE NOT e:Chunk AND NOT e:GenericLocation
WITH e, count(DISTINCT seen) AS df
MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
WITH DISTINCT e, c, df
CALL (c) {
    MATCH (x)-[:MENTIONED_IN]->(c)
    WHERE NOT x:Chunk AND NOT x:GenericLocation
    RETURN count(DISTINCT x) AS ec
}
RETURN gds.graph.project(
    $graphName,
    e,
    c,
    {
        sourceNodeLabels: labels(e),
        targetNodeLabels: labels(c),
        relationshipType:  'MENTIONS',
        relationshipProperties: {weight: __WEIGHT__}
    },
    {undirectedRelationshipTypes: ['MENTIONS']}
)
"""



@dataclass
class ProjectionStats:
    name: str
    node_count: int
    relationship_count: int
    projection_ms: float


def total_chunks() -> int:
    return query("MATCH (c:Chunk) RETURN count(c) AS n")[0]["n"]


def graph_exists(name: str | None = None) -> bool:
    name = name or settings().graph_name
    return bool(gds().graph.exists(name)["exists"])


def get_graph(name: str | None = None):
    """Return the projected graph, raising a useful error if it is missing."""
    name = name or settings().graph_name
    if not graph_exists(name):
        raise RuntimeError(
            f"GDS graph '{name}' is not projected. "
            f"Run `python scripts/project_graph.py` first."
        )
    return gds().graph.get(name)


def drop_graph(name: str | None = None) -> None:
    name = name or settings().graph_name
    if graph_exists(name):
        gds().graph.get(name).drop()


def project(name: str | None = None, *, force: bool = False) -> ProjectionStats:
    """Project the retrieval graph into the GDS catalog.

    Idempotent: an existing projection is reused unless ``force`` is set.
    """
    cfg = settings()
    name = name or cfg.graph_name

    if graph_exists(name):
        if not force:
            graph = gds().graph.get(name)
            return ProjectionStats(
                name=name,
                node_count=graph.node_count(),
                relationship_count=graph.relationship_count(),
                projection_ms=0.0,
            )
        drop_graph(name)

    graph, result = gds().graph.cypher.project(
        PROJECTION_QUERY,
        graphName=name,
        totalChunks=total_chunks(),
        nextChunkWeight=cfg.next_chunk_weight,
        relatedWeight=cfg.related_weight,
    )

    return ProjectionStats(
        name=name,
        node_count=graph.node_count(),
        relationship_count=graph.relationship_count(),
        projection_ms=float(result.get("projectMillis", 0.0)),
    )


# ── Internal id <-> business key mapping ──────────────────────────────────────
#
# GDS streams results keyed by Neo4j's internal node id. These two helpers
# translate in bulk — one round trip, not one per node.


def chunk_ids_to_node_ids(chunk_ids: list[str]) -> dict[str, int]:
    rows = query(
        """
        MATCH (c:Chunk)
        WHERE c.chunkId IN $chunkIds
        RETURN c.chunkId AS chunkId, id(c) AS nodeId
        """,
        chunkIds=chunk_ids,
    )
    return {row["chunkId"]: row["nodeId"] for row in rows}


def node_ids_to_chunks(node_ids: list[int]) -> dict[int, dict]:
    rows = query(
        """
        MATCH (c:Chunk)
        WHERE id(c) IN $nodeIds
        RETURN id(c)      AS nodeId,
               c.chunkId  AS chunkId,
               c.text     AS text,
               toString(c.date) AS date,
               c.author   AS author
        """,
        nodeIds=node_ids,
    )
    return {row["nodeId"]: row for row in rows}


def project_mentions(name: str | None = None, *, force: bool = False) -> ProjectionStats:
    """Project the ``MENTIONED_IN``-only undirected graph that PPR seeds walk.

    Separate from :func:`project` on purpose — see the note above
    ``MENTIONS_PROJECTION_QUERY``. Idempotent unless ``force``.
    """
    cfg = settings()
    name = name or cfg.mentions_graph_name

    if graph_exists(name):
        if not force:
            graph = gds().graph.get(name)
            return ProjectionStats(
                name=name,
                node_count=graph.node_count(),
                relationship_count=graph.relationship_count(),
                projection_ms=0.0,
            )
        drop_graph(name)

    scheme = settings().mention_weight
    if scheme not in MENTION_WEIGHTS:
        raise ValueError(
            f"MENTION_WEIGHT={scheme!r} is not one of {sorted(MENTION_WEIGHTS)}"
        )
    graph, result = gds().graph.cypher.project(
        MENTIONS_PROJECTION_QUERY.replace("__WEIGHT__", MENTION_WEIGHTS[scheme]),
        graphName=name,
        totalChunks=total_chunks(),
    )
    return ProjectionStats(
        name=name,
        node_count=graph.node_count(),
        relationship_count=graph.relationship_count(),
        projection_ms=float(result.get("projectMillis", 0.0)),
    )


def get_mentions_graph(name: str | None = None):
    """Return the mentions-only projection, with a useful error if it is absent."""
    name = name or settings().mentions_graph_name
    if not graph_exists(name):
        raise RuntimeError(
            f"GDS graph '{name}' is not projected. "
            f"Run `python scripts/project_graph.py` first."
        )
    return gds().graph.get(name)


@lru_cache(maxsize=1)
def mentions_membership() -> frozenset[int]:
    """Node ids present in the mentions projection.

    Only nodes touching a ``MENTIONED_IN`` edge are in that graph, so an entity
    with an embedding but no mentions — and a chunk the extractor found nothing
    in — are both absent. Seeding PPR at a missing node is a hard GDS error, and
    179 chunks (6.1% of the corpus, 3.4% of its text) have zero entities and are
    unreachable by any walk over this graph at any damping. That is a real recall
    floor, and the reason this pipeline blends with cosine rather than replacing
    it.
    """
    rows = read_query(
        """
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        WHERE NOT e:Chunk AND NOT e:GenericLocation
        RETURN id(e) AS nodeId
        UNION
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        WHERE NOT e:Chunk AND NOT e:GenericLocation
        RETURN id(c) AS nodeId
        """
    )
    return frozenset(row["nodeId"] for row in rows)


def all_chunk_node_ids() -> list[int]:
    """Every chunk node id, in a stable order — the corpus-wide scoring index."""
    return [
        row["nodeId"]
        for row in read_query("MATCH (c:Chunk) RETURN id(c) AS nodeId ORDER BY id(c)")
    ]


def hub_table(limit: int = 12) -> list[dict]:
    """Top entities by chunk degree, with the IDF weight each one earns.

    The hub trap, made showable rather than assertable. It does two jobs at
    once: the corpus is a daily record of what the party shot and ate, so the
    deer outranks both captains — and ``DREWYER`` appears here while
    ``GEORGE DROUILLARD`` is a separate node, which puts section 4's unresolved
    entities on screen for free.
    """
    return read_query(
        """
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        WHERE NOT e:Chunk AND NOT e:GenericLocation
        WITH e, count(DISTINCT c) AS df
        RETURN head(labels(e))                    AS label,
               coalesce(e.canonicalName, e.name)  AS name,
               df                                 AS chunks,
               log(1.0 + toFloat($totalChunks) / df) AS idfWeight
        ORDER BY df DESC
        LIMIT $limit
        """,
        totalChunks=total_chunks(),
        limit=limit,
    )

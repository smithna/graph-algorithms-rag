"""Project the retrieval graph into GDS once, then reuse it for every query.

This is the single most important performance fact in the talk: projection is
the expensive step, and it is amortised. A personalized PageRank run against an
already-projected graph is milliseconds.

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

from .config import gds, query, settings

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

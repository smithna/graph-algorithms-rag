"""Pure vector search — the control condition.

Everything else in this repo is measured against this. It is deliberately the
same query the corps-of-discovery demo app runs, so the comparison is honest:
the only thing that changes downstream is what the graph does with the results.
"""

from __future__ import annotations

import time

from .config import query
from .embedding import embed
from .models import Entity, Relationship, RetrievalResult, RetrievedChunk

VECTOR_QUERY = """
CALL db.index.vector.queryNodes('chunk_embeddings', $k, $embedding)
YIELD node AS chunk, score
RETURN chunk.chunkId        AS chunkId,
       chunk.text           AS text,
       toString(chunk.date) AS date,
       chunk.author         AS author,
       score
ORDER BY score DESC
"""


def vector_search(embedding: list[float], k: int = 8) -> list[RetrievedChunk]:
    """Top-k chunks by cosine similarity. No graph involved."""
    rows = query(VECTOR_QUERY, k=k, embedding=embedding)
    return [
        RetrievedChunk(
            chunk_id=row["chunkId"],
            text=row["text"],
            date=row["date"],
            author=row["author"],
            vector_score=row["score"],
            final_score=row["score"],
            source="vector",
        )
        for row in rows
    ]


def fetch_entities(chunk_ids: list[str]) -> dict[str, list[Entity]]:
    """Named entities mentioned in each chunk."""
    if not chunk_ids:
        return {}
    rows = query(
        """
        MATCH (c:Chunk) WHERE c.chunkId IN $chunkIds
        OPTIONAL MATCH (e)-[:MENTIONED_IN]->(c)
        WHERE NOT e:GenericLocation AND NOT e:Chunk
        WITH c.chunkId AS chunkId,
             collect(DISTINCT {
                 label: head(labels(e)),
                 name:  coalesce(e.canonicalName, e.name, '')
             }) AS entities
        RETURN chunkId, entities
        """,
        chunkIds=chunk_ids,
    )
    return {
        row["chunkId"]: [
            Entity(label=e["label"], name=e["name"])
            for e in row["entities"]
            if e.get("name")
        ]
        for row in rows
    }


def fetch_relationships(chunk_ids: list[str], limit: int = 40) -> list[Relationship]:
    """Extracted relationships whose endpoints both appear in the retrieved set."""
    if not chunk_ids:
        return []
    rows = query(
        """
        MATCH (a)-[:MENTIONED_IN]->(c:Chunk)
        WHERE c.chunkId IN $chunkIds AND NOT a:GenericLocation AND NOT a:Chunk
        MATCH (a)-[r]->(b)
        WHERE type(r) <> 'MENTIONED_IN'
          AND NOT b:Chunk AND NOT b:GenericLocation
          AND EXISTS {
              MATCH (b)-[:MENTIONED_IN]->(c2:Chunk)
              WHERE c2.chunkId IN $chunkIds
          }
        RETURN DISTINCT
               head(labels(a))                       AS fromType,
               coalesce(a.canonicalName, a.name, '') AS fromName,
               type(r)                               AS relType,
               head(labels(b))                       AS toType,
               coalesce(b.canonicalName, b.name, '') AS toName,
               r.chunkId                             AS chunkId,
               toString(r.date)                      AS date
        LIMIT $limit
        """,
        chunkIds=chunk_ids,
        limit=limit,
    )
    return [
        Relationship(
            from_name=row["fromName"],
            from_type=row["fromType"],
            rel_type=row["relType"],
            to_name=row["toName"],
            to_type=row["toType"],
            chunk_id=row.get("chunkId"),
            date=row.get("date"),
        )
        for row in rows
    ]


def attach_graph_context(result: RetrievalResult) -> RetrievalResult:
    """Populate per-chunk entities plus the shared relationship list."""
    chunk_ids = result.chunk_ids()
    entities_by_chunk = fetch_entities(chunk_ids)

    seen: dict[str, Entity] = {}
    for chunk in result.chunks:
        chunk.entities = entities_by_chunk.get(chunk.chunk_id, [])
        for entity in chunk.entities:
            seen[entity.key()] = entity

    result.entities = list(seen.values())
    result.relationships = fetch_relationships(chunk_ids)
    return result


def retrieve(question: str, k: int = 8, *, with_graph_context: bool = False) -> RetrievalResult:
    """Baseline strategy: embed the question, take the top-k nearest chunks."""
    started = time.perf_counter()
    chunks = vector_search(embed(question), k=k)
    result = RetrievalResult(
        question=question,
        strategy="vector",
        chunks=chunks,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        debug={"k": k},
    )
    if with_graph_context:
        attach_graph_context(result)
    return result

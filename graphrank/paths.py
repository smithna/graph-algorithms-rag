"""Path exploration with Yen's k-shortest paths.

Vector search can tell you that two concepts are both relevant. It cannot tell
you *how they are related* — and "how" is usually the actual question.

Yen's algorithm returns the k shortest distinct routes between two anchor
entities. Each route is an explanation, and because the extracted relationships
carry ``chunkId`` and ``date`` properties, every hop hands back the journal
passage that evidences it. The retrieved context is therefore not "eight
passages that mention Sacagawea" but "the specific passages that establish the
chain connecting Sacagawea to the Shoshone horses."

Multiple paths matter more than the single shortest one. The shortest path is
often a trivial co-occurrence; the second and third are where the interesting
mechanism usually lives.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from .baseline import vector_search
from .config import gds, query
from .embedding import embed
from .models import Entity, Path, Relationship, RetrievalResult, RetrievedChunk
from .projection import get_graph
from .resolve import LABEL_VECTOR_INDEX, ResolvedEntity, resolve_entity


@dataclass
class PathConfig:
    #: How many distinct routes Yen's should return per anchor pair
    k_paths: int = 5
    #: Longest route worth reporting — beyond this, "related" stops meaning much
    max_hops: int = 5
    #: Cap on evidence passages handed back as context
    k: int = 8
    #: Follow only extracted entity-entity relationships, not the chunk layer
    relationship_types: tuple[str, ...] = ("RELATED",)
    #: Uniform edge cost makes totalCost equal hop count, which is what you want
    #: for explanation. Set True to let IDF weights bend the routes instead.
    weighted: bool = False


def infer_anchors(question: str, n: int = 2) -> list[ResolvedEntity]:
    """Best-effort anchor extraction with no LLM in the loop.

    Searches every per-label entity vector index with the question embedding and
    keeps the strongest distinct hits. Good enough for a demo; the question bank
    lets you pin anchors explicitly when you want determinism.
    """
    embedding = embed(question)
    hits: list[ResolvedEntity] = []

    for label, index in LABEL_VECTOR_INDEX.items():
        rows = query(
            f"""
            CALL db.index.vector.queryNodes('{index}', 2, $embedding)
            YIELD node, score
            WHERE NOT node:GenericLocation
            RETURN coalesce(node.canonicalName, node.name) AS name,
                   head(labels(node)) AS label,
                   id(node) AS nodeId,
                   score
            """,
            embedding=embedding,
        )
        for row in rows:
            if row["name"]:
                hits.append(
                    ResolvedEntity(
                        label=row["label"],
                        name=row["name"],
                        node_id=row["nodeId"],
                        score=row["score"],
                        resolved_via="vector",
                    )
                )

    hits.sort(key=lambda h: h.score, reverse=True)
    seen: set[int] = set()
    anchors: list[ResolvedEntity] = []
    for hit in hits:
        if hit.node_id not in seen:
            seen.add(hit.node_id)
            anchors.append(hit)
        if len(anchors) >= n:
            break
    return anchors


def k_shortest_paths(
    source: ResolvedEntity,
    target: ResolvedEntity,
    *,
    config: PathConfig | None = None,
    graph=None,
) -> list[Path]:
    """Yen's k-shortest paths between two entities, hydrated with relationships."""
    config = config or PathConfig()
    graph = graph if graph is not None else get_graph()

    params: dict = {
        "sourceNode": source.node_id,
        "targetNode": target.node_id,
        "k": config.k_paths,
        "relationshipTypes": list(config.relationship_types),
    }
    if config.weighted:
        params["relationshipWeightProperty"] = "weight"

    try:
        frame = gds().shortestPath.yens.stream(graph, **params)
    except Exception:
        # No route at all, or the anchors are not in the projected subgraph.
        return []

    paths: list[Path] = []
    seen_routes: set[tuple[int, ...]] = set()
    for row in frame.itertuples():
        node_ids = list(row.nodeIds)
        if len(node_ids) - 1 > config.max_hops:
            continue
        # Yen's treats parallel relationships as distinct paths; a route here is
        # a node sequence, and _hydrate shows one relationship per hop anyway.
        if tuple(node_ids) in seen_routes:
            continue
        seen_routes.add(tuple(node_ids))
        hydrated = _hydrate(node_ids, total_cost=float(row.totalCost))
        if hydrated:
            paths.append(hydrated)
    return paths


def _hydrate(node_ids: list[int], *, total_cost: float) -> Path | None:
    """Turn a list of internal node ids into named nodes and typed relationships."""
    if len(node_ids) < 2:
        return None

    node_rows = query(
        """
        MATCH (n) WHERE id(n) IN $nodeIds
        RETURN id(n) AS nodeId,
               head(labels(n)) AS label,
               coalesce(n.canonicalName, n.name, '') AS name
        """,
        nodeIds=node_ids,
    )
    by_id = {row["nodeId"]: row for row in node_rows}
    nodes = [
        Entity(
            label=by_id.get(nid, {}).get("label", "Unknown"),
            name=by_id.get(nid, {}).get("name", str(nid)),
        )
        for nid in node_ids
    ]

    # One relationship per hop. Yen's works on the undirected projection, so the
    # stored relationship may point either way — match undirected and record the
    # direction we actually traversed.
    hop_rows = query(
        """
        UNWIND range(0, size($nodeIds) - 2) AS i
        WITH i, $nodeIds[i] AS aId, $nodeIds[i + 1] AS bId
        MATCH (a) WHERE id(a) = aId
        MATCH (b) WHERE id(b) = bId
        MATCH (a)-[r]-(b)
        WHERE type(r) <> 'MENTIONED_IN'
        // Entity merges combine parallel relationships, leaving list-valued
        // date/chunkId on ~400 relationships; take the first element of each.
        WITH i, a, b, r,
             CASE WHEN valueType(r.date) STARTS WITH 'LIST'
                  THEN r.date[0] ELSE r.date END       AS relDate,
             CASE WHEN valueType(r.chunkId) STARTS WITH 'LIST'
                  THEN r.chunkId[0] ELSE r.chunkId END AS relChunkId
        ORDER BY i, relDate
        RETURN i,
               head(labels(a))                       AS fromType,
               coalesce(a.canonicalName, a.name, '') AS fromName,
               type(r)                               AS relType,
               head(labels(b))                       AS toType,
               coalesce(b.canonicalName, b.name, '') AS toName,
               relChunkId                            AS chunkId,
               toString(relDate)                     AS date
        """,
        nodeIds=node_ids,
    )

    first_per_hop: dict[int, dict] = {}
    for row in hop_rows:
        first_per_hop.setdefault(row["i"], row)

    relationships: list[Relationship] = []
    for i in range(len(node_ids) - 1):
        row = first_per_hop.get(i)
        if row is None:
            return None
        relationships.append(
            Relationship(
                from_name=row["fromName"],
                from_type=row["fromType"],
                rel_type=row["relType"],
                to_name=row["toName"],
                to_type=row["toType"],
                chunk_id=row.get("chunkId"),
                date=row.get("date"),
            )
        )

    return Path(nodes=nodes, relationships=relationships, total_cost=total_cost)


def evidence_chunks(paths: list[Path], limit: int = 8) -> list[RetrievedChunk]:
    """The journal passages that justify each hop.

    Prefers the ``chunkId`` recorded on the relationship at extraction time.
    Structural relationships such as ``BELONGS_TO`` carry no chunkId, so those
    hops fall back to a passage where both endpoints are mentioned together.
    """
    direct_ids: list[str] = []
    fallback_pairs: list[tuple[str, str]] = []

    for path in paths:
        for rel in path.relationships:
            if rel.chunk_id:
                direct_ids.append(rel.chunk_id)
            else:
                fallback_pairs.append((rel.from_name, rel.to_name))

    chunks: dict[str, RetrievedChunk] = {}

    if direct_ids:
        rows = query(
            """
            MATCH (c:Chunk) WHERE c.chunkId IN $chunkIds
            RETURN c.chunkId AS chunkId, c.text AS text,
                   toString(c.date) AS date, c.author AS author
            """,
            chunkIds=list(dict.fromkeys(direct_ids)),
        )
        for row in rows:
            chunks[row["chunkId"]] = RetrievedChunk(
                chunk_id=row["chunkId"],
                text=row["text"],
                date=row["date"],
                author=row["author"],
                source="path-evidence",
                final_score=1.0,
            )

    for from_name, to_name in fallback_pairs:
        if len(chunks) >= limit:
            break
        rows = query(
            """
            MATCH (a)-[:MENTIONED_IN]->(c:Chunk)<-[:MENTIONED_IN]-(b)
            WHERE coalesce(a.canonicalName, a.name) = $fromName
              AND coalesce(b.canonicalName, b.name) = $toName
            RETURN c.chunkId AS chunkId, c.text AS text,
                   toString(c.date) AS date, c.author AS author
            LIMIT 2
            """,
            fromName=from_name,
            toName=to_name,
        )
        for row in rows:
            chunks.setdefault(
                row["chunkId"],
                RetrievedChunk(
                    chunk_id=row["chunkId"],
                    text=row["text"],
                    date=row["date"],
                    author=row["author"],
                    source="path-cooccurrence",
                    final_score=0.5,
                ),
            )

    ordered = sorted(chunks.values(), key=lambda c: (c.date or "", c.chunk_id))
    return ordered[:limit]


def retrieve(
    question: str,
    *,
    anchors: list[str] | None = None,
    config: PathConfig | None = None,
) -> RetrievalResult:
    """Path-explanation retrieval between two anchor concepts."""
    config = config or PathConfig()
    started = time.perf_counter()

    if anchors and len(anchors) >= 2:
        resolved = [resolve_entity(a) for a in anchors[:2]]
        resolved = [r for r in resolved if r is not None]
    else:
        resolved = infer_anchors(question, n=2)

    if len(resolved) < 2:
        # Nothing to connect — degrade to plain vector search rather than fail.
        chunks = vector_search(embed(question), k=config.k)
        return RetrievalResult(
            question=question,
            strategy="paths",
            chunks=chunks,
            elapsed_ms=(time.perf_counter() - started) * 1000,
            debug={"anchors": [r.name for r in resolved], "fell_back": True},
        )

    source, target = resolved[0], resolved[1]
    found = k_shortest_paths(source, target, config=config)
    chunks = evidence_chunks(found, limit=config.k)

    if not chunks:
        chunks = vector_search(embed(question), k=config.k)

    entity_map: dict[str, Entity] = {}
    relationships: list[Relationship] = []
    for path in found:
        for node in path.nodes:
            entity_map[node.key()] = node
        relationships.extend(path.relationships)

    return RetrievalResult(
        question=question,
        strategy="paths",
        chunks=chunks,
        entities=list(entity_map.values()),
        relationships=relationships,
        paths=found,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        debug={
            "anchors": [source.name, target.name],
            "anchor_labels": [source.label, target.label],
            "path_count": len(found),
            "hop_counts": [p.hops for p in found],
            "fell_back": not found,
        },
    )

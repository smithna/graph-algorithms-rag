"""Path exploration with Yen's k-shortest paths.

Vector search can tell you that two concepts are both relevant. It cannot tell
you *how they are related* — and "how" is usually the actual question.

Yen's algorithm returns the k shortest distinct routes between two anchor
entities. Each route is an explanation, and because the extracted relationships
carry ``chunkId`` and ``date`` properties, every hop hands back the journal
passage that evidences it. The retrieved context is therefore not "eight
passages that mention Sacagawea" but "the specific passages that establish the
chain connecting Sacagawea to the Shoshone horses."

Multiple paths matter, but not for the reason usually given. On a graph of
*typed extracted relationships* the single shortest path is a strong claim, not
a trivial co-occurrence (hand-read on `lewisclark`: Sacagawea MEMBER_OF Shoshone
at k=1 is the load-bearing fact for the horse question). Where k earns its keep
is hub-mediated pairs: Sacagawea and Cameahwait are siblings, but the graph has
no sibling edge, so k=1 and k=2 route through "both knew Lewis" and the shared
nation — the recognition scene only surfaces at k=3, through the Event node both
PARTICIPATED_IN. And higher k exposes graph defects a single path hides: an
unmerged duplicate makes a route through the anchor's own alias look like an
explanation. Ask for several routes and read the receipts.
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

    # Two GDS behaviours make the naive call unusable on stage, both measured:
    # Yen's treats parallel relationships as distinct paths, so asking for k=25
    # returned 7 distinct node sequences (one route came back 12 times) — hence
    # the over-request below. And its ordering among equal-cost routes is
    # nondeterministic: three consecutive identical calls returned the three
    # tied 2-hop routes in three different orders. Routes are therefore deduped,
    # then tie-sorted by hop count and route text.
    #
    # What that buys, exactly: any cost class the over-request enumerates
    # COMPLETELY (the 1- and 2-hop classes on the demo pairs) comes back stable,
    # every run. A cost class larger than the remaining raw budget (3-hop ties
    # number in the dozens) is sampled, and WHICH ties fill the tail can differ
    # between invocations — the sort stabilises order, not membership. Talk over
    # the head of the list; treat the tail as "more routes exist at this cost".
    params: dict = {
        "sourceNode": source.node_id,
        "targetNode": target.node_id,
        "k": min(config.k_paths * 5, 50),
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
        if tuple(node_ids) in seen_routes:
            continue
        seen_routes.add(tuple(node_ids))
        hydrated = _hydrate(node_ids, total_cost=float(row.totalCost))
        if hydrated:
            paths.append(hydrated)

    paths.sort(key=lambda p: (p.total_cost, p.hops, p.describe()))
    return paths[: config.k_paths]


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

    # One relationship per hop, reported in its STORED direction. Yen's works on
    # the undirected projection, so a hop may traverse an edge backwards; the
    # extractor asserted a direction and the display must keep it, or
    # "CAMEAHWAIT MEMBER_OF SHOSHONE" renders as "SHOSHONE MEMBER_OF CAMEAHWAIT".
    #
    # Receipts: entity merges combine parallel relationships, leaving ~400 with
    # list-valued chunkId — and the merged date array is RAGGED (measured: 11
    # chunkIds against 8 dates on one edge), so r.date[i] can belong to a
    # different receipt than r.chunkId[i]. Every receipt is kept, ordered by the
    # receipt chunk's own date, and the hop's date comes from its first chunk.
    hop_rows = query(
        """
        UNWIND range(0, size($nodeIds) - 2) AS i
        WITH i, $nodeIds[i] AS aId, $nodeIds[i + 1] AS bId
        MATCH (a) WHERE id(a) = aId
        MATCH (b) WHERE id(b) = bId
        MATCH (a)-[r]-(b)
        WHERE type(r) <> 'MENTIONED_IN'
        WITH i, r,
             head(labels(startNode(r)))                                   AS fromType,
             coalesce(startNode(r).canonicalName, startNode(r).name, '')  AS fromName,
             head(labels(endNode(r)))                                     AS toType,
             coalesce(endNode(r).canonicalName, endNode(r).name, '')      AS toName,
             CASE WHEN r.chunkId IS NULL THEN []
                  WHEN valueType(r.chunkId) STARTS WITH 'LIST' THEN r.chunkId
                  ELSE [r.chunkId] END                                    AS rawIds
        CALL (rawIds) {
            OPTIONAL MATCH (c:Chunk) WHERE c.chunkId IN rawIds
            WITH c ORDER BY c.date
            RETURN collect(c.chunkId) AS chunkIds, toString(head(collect(c.date))) AS date
        }
        RETURN i, fromType, fromName, type(r) AS relType, toType, toName,
               chunkIds, date
        ORDER BY i, date
        """,
        nodeIds=node_ids,
    )

    per_hop: dict[int, list[dict]] = {}
    for row in hop_rows:
        per_hop.setdefault(row["i"], []).append(row)

    relationships: list[Relationship] = []
    for i in range(len(node_ids) - 1):
        rows = per_hop.get(i)
        if not rows:
            return None
        row, rest = rows[0], rows[1:]
        chunk_ids = row["chunkIds"] or []
        relationships.append(
            Relationship(
                from_name=row["fromName"],
                from_type=row["fromType"],
                rel_type=row["relType"],
                to_name=row["toName"],
                to_type=row["toType"],
                chunk_id=chunk_ids[0] if chunk_ids else None,
                date=row.get("date"),
                chunk_ids=chunk_ids,
                parallel_types=sorted({r["relType"] for r in rest} - {row["relType"]}),
            )
        )

    return Path(nodes=nodes, relationships=relationships, total_cost=total_cost)


def evidence_chunks(paths: list[Path], limit: int = 8) -> list[RetrievedChunk]:
    """The journal passages that justify each hop.

    Prefers the ``chunkId`` receipts recorded on the relationship at extraction
    time — all of them, since merged relationships carry several. Structural
    relationships such as ``BELONGS_TO`` carry no chunkId, so those hops fall
    back to a passage where both endpoints are mentioned together. Know the
    fallback's limits before putting it on a slide: Taxon nodes have no
    MENTIONED_IN edges, so a taxonomy hop yields ZERO passages, silently — and
    the fallback matches endpoints by name, so a duplicate name (two SHOSHONE
    COVE nodes exist) can cite a passage about the other node.
    """
    # Receipt selection is round-robin over hops in route order: the first
    # receipt of every hop of route 1, then route 2, ... then every hop's second
    # receipt, and so on until the cap. Two simpler schemes both failed a hand
    # read: taking only receipt [0] hid the explicit membership passage sitting
    # at [1], and taking every receipt in date order filled the cap with a merged
    # hop's eleven council passages and pushed the recognition scene out
    # entirely. Selection follows route priority; display order is chronological.
    per_hop_ids: list[list[str]] = []
    fallback_pairs: list[tuple[str, str]] = []

    for path in paths:
        for rel in path.relationships:
            if rel.chunk_ids:
                per_hop_ids.append(rel.chunk_ids)
            elif rel.chunk_id:
                per_hop_ids.append([rel.chunk_id])
            else:
                fallback_pairs.append((rel.from_name, rel.to_name))

    direct_ids: list[str] = []
    depth = 0
    while len(direct_ids) < limit and any(depth < len(ids) for ids in per_hop_ids):
        for ids in per_hop_ids:
            if depth < len(ids) and ids[depth] not in direct_ids:
                direct_ids.append(ids[depth])
                if len(direct_ids) >= limit:
                    break
        depth += 1

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

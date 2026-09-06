"""Louvain community detection over the retrieval graph.

Communities are the thematic structure that pure similarity cannot see. Two
passages about "trading for horses in the mountains" are similar in embedding
space *and* land in the same community. Two passages that both use the word
"river" are similar in embedding space and land nowhere near each other.

That difference buys two distinct things:

**Diversification.** Vector top-k routinely returns eight near-duplicates of the
same moment. Capping how many chunks any single community may contribute forces
the context window to span the question instead of restating one answer.

**Expansion.** Once the seed hits reveal which communities the question lives
in, high-authority members of those communities can be pulled in even when
their wording never matched the query.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass

import pandas as pd

from .baseline import attach_graph_context, vector_search
from .config import gds, query, settings
from .embedding import embed
from .models import Entity, RetrievalResult, RetrievedChunk
from .projection import chunk_ids_to_node_ids, get_graph, node_ids_to_chunks

_COMMUNITY_CACHE: dict[str, pd.Series] = {}


@dataclass
class CommunityConfig:
    candidate_k: int = 50
    k: int = 8
    #: Max chunks any one community may contribute to the context window
    max_per_community: int = 2
    #: Louvain resolution — higher yields more, smaller communities
    resolution: float = 1.0
    max_levels: int = 10
    weighted: bool = True


def detect(
    *,
    config: CommunityConfig | None = None,
    graph=None,
    refresh: bool = False,
) -> pd.Series:
    """Run Louvain and return a Series mapping node id -> community id."""
    config = config or CommunityConfig()
    graph = graph if graph is not None else get_graph()

    key = f"{graph.name()}::{config.resolution}::{config.weighted}"
    if not refresh and key in _COMMUNITY_CACHE:
        return _COMMUNITY_CACHE[key]

    params: dict = {
        "maxLevels": config.max_levels,
        "relationshipTypes": ["MENTIONS", "NEXT_CHUNK", "RELATED"],
    }
    if config.weighted:
        params["relationshipWeightProperty"] = "weight"

    frame = gds().louvain.stream(graph, **params)
    series = frame.set_index("nodeId")["communityId"]
    _COMMUNITY_CACHE[key] = series
    return series


def write_back(
    *,
    config: CommunityConfig | None = None,
    graph=None,
    write_property: str = "communityId",
) -> dict:
    """Persist community ids onto the Neo4j nodes.

    This *writes to your database*. It is opt-in behind a flag on
    ``scripts/detect_communities.py`` for exactly that reason — but once the
    property exists you can explore communities in Browser and Bloom, which is
    worth a lot on stage.
    """
    config = config or CommunityConfig()
    graph = graph if graph is not None else get_graph()

    params: dict = {
        "writeProperty": write_property,
        "maxLevels": config.max_levels,
        "relationshipTypes": ["MENTIONS", "NEXT_CHUNK", "RELATED"],
    }
    if config.weighted:
        params["relationshipWeightProperty"] = "weight"

    return dict(gds().louvain.write(graph, **params))


def summarize(
    community_ids: list[int] | None = None,
    *,
    config: CommunityConfig | None = None,
    top_entities: int = 8,
    limit: int = 15,
) -> list[dict]:
    """Describe communities by their most-connected entities and their span.

    This is the "what is actually *in* this corpus" view — a table of contents
    nobody wrote, derived entirely from structure.
    """
    membership = detect(config=config)
    node_ids = membership.index.tolist()

    rows = query(
        """
        MATCH (n) WHERE id(n) IN $nodeIds
        RETURN id(n) AS nodeId,
               head(labels(n)) AS label,
               coalesce(n.canonicalName, n.name, '') AS name,
               n:Chunk AS isChunk,
               toString(n.date) AS date,
               size([(n)-[:MENTIONED_IN]->(:Chunk) | 1]) AS mentionCount
        """,
        nodeIds=node_ids,
    )

    grouped: dict[int, dict] = defaultdict(
        lambda: {"entities": [], "chunk_count": 0, "dates": []}
    )
    for row in rows:
        community_id = int(membership.loc[row["nodeId"]])
        bucket = grouped[community_id]
        if row["isChunk"]:
            bucket["chunk_count"] += 1
            if row["date"]:
                bucket["dates"].append(row["date"])
        elif row["name"]:
            bucket["entities"].append(
                (row["mentionCount"] or 0, row["label"], row["name"])
            )

    summaries = []
    for community_id, bucket in grouped.items():
        if community_ids is not None and community_id not in community_ids:
            continue
        entities = sorted(bucket["entities"], reverse=True)[:top_entities]
        dates = sorted(bucket["dates"])
        summaries.append(
            {
                "community_id": community_id,
                "chunk_count": bucket["chunk_count"],
                "entity_count": len(bucket["entities"]),
                "date_range": (dates[0], dates[-1]) if dates else None,
                "top_entities": [
                    Entity(label=label, name=name, community_id=community_id)
                    for _, label, name in entities
                ],
            }
        )

    summaries.sort(key=lambda s: s["chunk_count"], reverse=True)
    return summaries[:limit] if community_ids is None else summaries


def retrieve(
    question: str,
    *,
    config: CommunityConfig | None = None,
    with_graph_context: bool = False,
) -> RetrievalResult:
    """Community-diversified retrieval.

    Take a wide vector slate, label each candidate with its community, then walk
    the slate in similarity order admitting at most ``max_per_community`` chunks
    from any one theme. Leftover slots, if any, are backfilled in similarity
    order so the strategy never returns fewer than ``k``.
    """
    config = config or CommunityConfig()
    started = time.perf_counter()

    candidates = vector_search(embed(question), k=config.candidate_k)
    if not candidates:
        return RetrievalResult(question=question, strategy="vector+community")

    membership = detect(config=config)
    id_map = chunk_ids_to_node_ids([c.chunk_id for c in candidates])

    for chunk in candidates:
        node_id = id_map.get(chunk.chunk_id)
        if node_id is not None and node_id in membership.index:
            chunk.community_id = int(membership.loc[node_id])

    selected: list[RetrievedChunk] = []
    used: dict[int | None, int] = defaultdict(int)
    overflow: list[RetrievedChunk] = []

    for chunk in candidates:
        if len(selected) >= config.k:
            break
        if used[chunk.community_id] < config.max_per_community:
            used[chunk.community_id] += 1
            chunk.source = "community"
            selected.append(chunk)
        else:
            overflow.append(chunk)

    for chunk in overflow:
        if len(selected) >= config.k:
            break
        chunk.source = "community-backfill"
        selected.append(chunk)

    result = RetrievalResult(
        question=question,
        strategy="vector+community",
        chunks=selected,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        debug={
            "candidate_k": config.candidate_k,
            "max_per_community": config.max_per_community,
            "communities_represented": sorted(
                {c.community_id for c in selected if c.community_id is not None}
            ),
            "communities_in_vector_topk": sorted(
                {
                    c.community_id
                    for c in candidates[: config.k]
                    if c.community_id is not None
                }
            ),
        },
    )
    if with_graph_context:
        attach_graph_context(result)
    return result

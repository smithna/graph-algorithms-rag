"""Leiden community detection over the retrieval graph.

Communities are the thematic structure that pure similarity cannot see. Two
passages about "trading for horses in the mountains" are similar in embedding
space *and* land in the same community. Two passages that both use the word
"river" are similar in embedding space and land nowhere near each other.

That difference buys two distinct things:

**Diversification.** Vector top-k routinely returns eight near-duplicates of the
same moment. Capping how many chunks any single community may contribute forces
the context window to span the question instead of restating one answer. On
this corpus the strategy that most needs the cap is not vector search — it is
section 5's expansion walk, whose conjunction-seeking collapsed the
illness-and-injury window onto one week at Long Camp (finding 5l). Hence
:func:`diversify`, which caps *any* strategy's ranked slate.

**Expansion.** Once the seed hits reveal which communities the question lives
in, high-authority members of those communities can be pulled in even when
their wording never matched the query.

On the mechanics: :func:`detect` runs the algorithm in **mutate** mode — the
membership lands as a node property on the in-memory projection (never the
database) and is streamed back from there. That way :func:`conductance` and
every window cap in one process read the *same run*, which matters because
community detection is only reproducible when the seed and the run are pinned
together.
"""

from __future__ import annotations

import re
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
#: Stats of the run behind each cached membership (modularity, counts).
_DETECT_STATS: dict[str, dict] = {}
#: The relationship types communities are detected over — the full retrieval
#: graph, including the NEXT_CHUNK chain. That is deliberate: an "episode" is
#: exactly a stretch of consecutive entries plus the entities they share, and
#: the chain is what lets the algorithm see it.
COMMUNITY_REL_TYPES = ["MENTIONS", "NEXT_CHUNK", "RELATED"]


@dataclass
class CommunityConfig:
    candidate_k: int = 50
    k: int = 8
    #: Max chunks any one community may contribute to the context window
    max_per_community: int = 2
    #: "leiden" (the default, and the only algorithm the talk uses) or
    #: "louvain". Leiden is the default because Louvain can emit internally
    #: disconnected communities, and because Louvain has no seed parameter —
    #: it redraws its partition on every run. `louvain` stays selectable only
    #: so the difference can be demonstrated on request.
    algorithm: str = "leiden"
    #: Resolution (GDS calls it gamma) — higher yields more, smaller
    #: communities
    resolution: float = 1.0
    max_levels: int = 10
    weighted: bool = True
    #: Leiden only. A fixed seed needs concurrency=1, which is what makes a
    #: measurement re-runnable; Louvain has no seed parameter in GDS.
    random_seed: int = 42

    def cache_key(self, graph_name: str) -> str:
        return (
            f"{graph_name}::{self.algorithm}::{self.resolution}::{self.weighted}"
        )

    def mutate_property(self) -> str:
        """Projection property holding this config's membership."""
        raw = f"communityId_{self.algorithm}_{self.resolution}_{self.weighted}"
        return re.sub(r"[^0-9A-Za-z_]", "_", raw)


def _algo(config: CommunityConfig):
    client = gds()
    if config.algorithm == "louvain":
        return client.louvain
    if config.algorithm == "leiden":
        return client.leiden
    raise ValueError(
        f"algorithm={config.algorithm!r} is not 'louvain' or 'leiden'"
    )


def _algo_params(config: CommunityConfig) -> dict:
    params: dict = {
        "maxLevels": config.max_levels,
        "relationshipTypes": COMMUNITY_REL_TYPES,
    }
    if config.algorithm == "louvain":
        # GDS spells Louvain's resolution parameter `gamma` only for Leiden.
        if config.resolution != 1.0:
            params["gamma"] = config.resolution
    else:
        params["gamma"] = config.resolution
        params["randomSeed"] = config.random_seed
        params["concurrency"] = 1  # required for randomSeed to bite
    if config.weighted:
        params["relationshipWeightProperty"] = "weight"
    return params


def detect(
    *,
    config: CommunityConfig | None = None,
    graph=None,
    refresh: bool = False,
) -> pd.Series:
    """Detect communities; return a Series mapping node id -> community id.

    Runs in mutate mode so the same membership is queryable by
    :func:`conductance` — see the module docstring.
    """
    config = config or CommunityConfig()
    graph = graph if graph is not None else get_graph()

    key = config.cache_key(graph.name())
    if not refresh and key in _COMMUNITY_CACHE:
        return _COMMUNITY_CACHE[key]

    prop = config.mutate_property()
    client = gds()
    try:
        stats = _algo(config).mutate(graph, mutateProperty=prop, **_algo_params(config))
    except Exception:
        # A previous process already mutated this property onto the resident
        # projection. Drop and re-run rather than trusting a run this process
        # never saw — an unseeded community run is not reproducible.
        client.graph.nodeProperties.drop(graph, [prop])
        stats = _algo(config).mutate(graph, mutateProperty=prop, **_algo_params(config))

    frame = client.graph.nodeProperty.stream(graph, prop)
    series = frame.set_index("nodeId")["propertyValue"].astype(int)
    series.name = "communityId"
    _COMMUNITY_CACHE[key] = series
    _DETECT_STATS[key] = dict(stats)
    return series


def detect_stats(*, config: CommunityConfig | None = None, graph=None) -> dict:
    """Stats (modularity, communityCount, ranLevels) of the cached run."""
    config = config or CommunityConfig()
    graph = graph if graph is not None else get_graph()
    key = config.cache_key(graph.name())
    if key not in _DETECT_STATS:
        detect(config=config, graph=graph)
    return _DETECT_STATS[key]


def conductance(
    *,
    config: CommunityConfig | None = None,
    graph=None,
) -> pd.Series:
    """Per-community conductance for the membership :func:`detect` produced.

    Conductance is the share of a community's edge weight that leaves it —
    a cohesion check that costs one call. The working thresholds (from the
    ki-post rule of thumb): ≤0.35 reads as a tight theme you can build on,
    ≥0.60 as a loose one you should not.

    Returns a Series mapping community id -> conductance.
    """
    config = config or CommunityConfig()
    graph = graph if graph is not None else get_graph()

    detect(config=config, graph=graph)  # ensure the mutate happened here
    params: dict = {
        "communityProperty": config.mutate_property(),
        "relationshipTypes": COMMUNITY_REL_TYPES,
    }
    if config.weighted:
        params["relationshipWeightProperty"] = "weight"
    frame = gds().conductance.stream(graph, **params)
    return frame.set_index("community")["conductance"]


def write_back(
    *,
    config: CommunityConfig | None = None,
    graph=None,
    write_property: str = "communityId",
) -> dict:
    """Persist community ids onto the Neo4j nodes.

    This *writes to your database*. It is opt-in behind a flag on
    ``scripts/demo_communities.py`` for exactly that reason — but once the
    property exists you can explore communities in Browser and Bloom, which is
    worth a lot on stage.
    """
    config = config or CommunityConfig()
    graph = graph if graph is not None else get_graph()

    return dict(
        _algo(config).write(
            graph, writeProperty=write_property, **_algo_params(config)
        )
    )


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


def label_communities(
    chunks: list[RetrievedChunk], *, config: CommunityConfig | None = None
) -> None:
    """Stamp each chunk with the community id of :func:`detect`'s membership."""
    membership = detect(config=config)
    id_map = chunk_ids_to_node_ids([c.chunk_id for c in chunks])
    for chunk in chunks:
        node_id = id_map.get(chunk.chunk_id)
        if node_id is not None and node_id in membership.index:
            chunk.community_id = int(membership.loc[node_id])


def _cap(
    candidates: list[RetrievedChunk], config: CommunityConfig
) -> list[RetrievedChunk]:
    """Walk a ranked slate admitting at most ``max_per_community`` per theme.

    Leftover slots, if any, are backfilled in slate order so the window never
    holds fewer than ``k``.
    """
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

    return selected


def diversify(
    base: RetrievalResult,
    *,
    config: CommunityConfig | None = None,
    with_graph_context: bool = False,
) -> RetrievalResult:
    """Community-cap **any** strategy's ranked slate.

    ``base`` should carry a slate wider than ``config.k`` (run the strategy
    with a large k); the cap then walks it in the strategy's own rank order.
    This is deliberately strategy-agnostic: on this corpus the window that
    collapses onto one episode is section 5's expansion walk, so the cap has to
    apply to *its* ranking, not only to cosine's.
    """
    config = config or CommunityConfig()
    started = time.perf_counter()

    candidates = list(base.chunks)
    label_communities(candidates, config=config)
    selected = _cap(candidates, config)

    debug: dict = {
        "base_strategy": base.strategy,
        "candidates": len(candidates),
        "max_per_community": config.max_per_community,
        "algorithm": config.algorithm,
        "communities_represented": sorted(
            {c.community_id for c in selected if c.community_id is not None}
        ),
        "communities_in_base_topk": sorted(
            {
                c.community_id
                for c in candidates[: config.k]
                if c.community_id is not None
            }
        ),
        "backfilled": [c.chunk_id for c in selected if c.source == "community-backfill"],
    }
    # Keep the base strategy's corpus-wide cosine ranks where it recorded them,
    # so promotions stay attributable after the cap re-orders the window.
    base_cosine_rank = base.debug.get("cosine_rank")
    if base_cosine_rank is not None:
        debug["cosine_rank"] = {
            c.chunk_id: base_cosine_rank.get(c.chunk_id) for c in selected
        }
        debug["promoted"] = [
            c.chunk_id
            for c in selected
            if (base_cosine_rank.get(c.chunk_id) or 10**9) > config.k
        ]

    result = RetrievalResult(
        question=base.question,
        strategy=f"{base.strategy}+community",
        chunks=selected,
        elapsed_ms=base.elapsed_ms + (time.perf_counter() - started) * 1000,
        debug=debug,
    )
    if with_graph_context:
        attach_graph_context(result)
    return result


def retrieve(
    question: str,
    *,
    config: CommunityConfig | None = None,
    with_graph_context: bool = False,
) -> RetrievalResult:
    """Community-diversified vector retrieval.

    Take a wide vector slate, label each candidate with its community, then walk
    the slate in similarity order admitting at most ``max_per_community`` chunks
    from any one theme.
    """
    config = config or CommunityConfig()
    started = time.perf_counter()

    candidates = vector_search(embed(question), k=config.candidate_k)
    if not candidates:
        return RetrievalResult(question=question, strategy="vector+community")

    label_communities(candidates, config=config)
    selected = _cap(candidates, config)

    result = RetrievalResult(
        question=question,
        strategy="vector+community",
        chunks=selected,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        debug={
            "candidate_k": config.candidate_k,
            "max_per_community": config.max_per_community,
            "algorithm": config.algorithm,
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

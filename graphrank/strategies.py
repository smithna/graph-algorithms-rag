"""The strategy registry the benchmark harness runs against.

Every strategy has the same signature — ``(question, k, **options) ->
RetrievalResult`` — so adding a new idea means adding one function here and
nothing else anywhere.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

import pandas as pd

from . import baseline, communities, cooccurrence, pagerank, paths
from .baseline import attach_graph_context, vector_search
from .communities import CommunityConfig
from .cooccurrence import CooccurrenceConfig
from .embedding import embed
from .models import RetrievalResult, RetrievedChunk
from .pagerank import RerankConfig
from .paths import PathConfig
from .projection import chunk_ids_to_node_ids


def vector_strategy(question: str, k: int = 8, **options) -> RetrievalResult:
    return baseline.retrieve(question, k=k, **options)


def ppr_strategy(question: str, k: int = 8, **options) -> RetrievalResult:
    with_graph_context = options.pop("with_graph_context", False)
    config = RerankConfig(k=k, **options)
    return pagerank.rerank(question, config=config, with_graph_context=with_graph_context)


def community_strategy(question: str, k: int = 8, **options) -> RetrievalResult:
    with_graph_context = options.pop("with_graph_context", False)
    config = CommunityConfig(k=k, **options)
    return communities.retrieve(
        question, config=config, with_graph_context=with_graph_context
    )


def cooccurrence_strategy(question: str, k: int = 8, **options) -> RetrievalResult:
    """Rank by shared entities rather than shared vocabulary.

    The build-time algorithm from section 4, pointed at query time. Two chunks
    about the same episode can share almost no words while sharing the rare
    entities that make them the same episode.
    """
    with_graph_context = options.pop("with_graph_context", False)
    config = CooccurrenceConfig(k=k, **options)
    return cooccurrence.retrieve(
        question, config=config, with_graph_context=with_graph_context
    )


def path_strategy(question: str, k: int = 8, **options) -> RetrievalResult:
    anchors = options.pop("anchors", None)
    config = PathConfig(k=k, **options)
    return paths.retrieve(question, anchors=anchors, config=config)


def hybrid_strategy(
    question: str,
    k: int = 8,
    *,
    candidate_k: int = 50,
    seed_k: int = 5,
    alpha: float = 0.5,
    normalize: str = "lift",
    max_per_community: int = 2,
    with_graph_context: bool = False,
    **_,
) -> RetrievalResult:
    """Rank with personalized PageRank, then diversify across communities.

    This is the configuration to reach for in production: PageRank decides what
    is *relevant to this question*, Louvain stops the window filling up with
    eight restatements of the same relevant thing.
    """
    started = time.perf_counter()
    rerank_config = RerankConfig(
        candidate_k=candidate_k,
        seed_k=seed_k,
        k=candidate_k,  # rank the whole slate; the community cap does the cutting
        alpha=alpha,
        normalize=normalize,
    )

    ranked = pagerank.rerank(question, config=rerank_config)
    if not ranked.chunks:
        return RetrievalResult(question=question, strategy="hybrid")

    membership = communities.detect(
        config=CommunityConfig(max_per_community=max_per_community)
    )
    id_map = chunk_ids_to_node_ids([c.chunk_id for c in ranked.chunks])
    for chunk in ranked.chunks:
        node_id = id_map.get(chunk.chunk_id)
        if node_id is not None and node_id in membership.index:
            chunk.community_id = int(membership.loc[node_id])

    selected: list[RetrievedChunk] = []
    used: dict[int | None, int] = defaultdict(int)
    overflow: list[RetrievedChunk] = []

    for chunk in ranked.chunks:
        if len(selected) >= k:
            break
        if used[chunk.community_id] < max_per_community:
            used[chunk.community_id] += 1
            selected.append(chunk)
        else:
            overflow.append(chunk)

    for chunk in overflow:
        if len(selected) >= k:
            break
        selected.append(chunk)

    result = RetrievalResult(
        question=question,
        strategy="hybrid",
        chunks=selected,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        debug={
            **ranked.debug,
            "max_per_community": max_per_community,
            "communities_represented": sorted(
                {c.community_id for c in selected if c.community_id is not None}
            ),
        },
    )
    if with_graph_context:
        attach_graph_context(result)
    return result


StrategyFn = Callable[..., RetrievalResult]

REGISTRY: dict[str, StrategyFn] = {
    "vector": vector_strategy,
    "ppr": ppr_strategy,
    "community": community_strategy,
    "cooccurrence": cooccurrence_strategy,
    "paths": path_strategy,
    "hybrid": hybrid_strategy,
}

#: Sensible order for reports — baseline first, then one idea at a time.
DEFAULT_ORDER = ["vector", "ppr", "community", "cooccurrence", "hybrid"]


def get(name: str) -> StrategyFn:
    try:
        return REGISTRY[name]
    except KeyError:
        raise KeyError(
            f"Unknown strategy '{name}'. Available: {', '.join(sorted(REGISTRY))}"
        ) from None

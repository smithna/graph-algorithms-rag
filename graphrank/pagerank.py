"""Personalized PageRank reranking.

The idea in one sentence: let the vector index nominate a wide slate of
candidates, then let the graph decide which of them actually belong in the
context window.

Plain PageRank asks "which nodes are important in this graph?" — a global,
query-independent answer. *Personalized* PageRank restarts the random walk at a
chosen set of source nodes, so it asks the far more useful question: "which
nodes are important **relative to what this question is about?**"

The source nodes are the top vector hits. A candidate chunk that shares rare
entities with those hits, or sits one hop away through an extracted
relationship, accumulates score. A chunk that merely uses similar vocabulary but
is structurally marooned does not.

Two knobs matter and both are exposed:

``alpha``      how much of the final score is cosine similarity vs. PPR
``normalize``  ``"lift"`` divides personalized score by global PageRank, which
               suppresses chunks that are central to *everything* and rewards
               chunks that are central to *this question*
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import pandas as pd

from .baseline import attach_graph_context, vector_search
from .config import gds
from .embedding import embed
from .models import RetrievalResult, RetrievedChunk
from .projection import chunk_ids_to_node_ids, get_graph

_GLOBAL_PAGERANK_CACHE: dict[str, pd.Series] = {}


@dataclass
class RerankConfig:
    #: How many chunks the vector index nominates before reranking
    candidate_k: int = 50
    #: How many of those seed the random walk restart set
    seed_k: int = 5
    #: How many survive into the context window
    k: int = 8
    #: 1.0 = pure cosine, 0.0 = pure PageRank
    alpha: float = 0.5
    #: "none" | "lift"
    normalize: str = "lift"
    damping_factor: float = 0.85
    max_iterations: int = 20
    tolerance: float = 1e-7
    #: Use the IDF weights baked into the projection
    weighted: bool = True


def personalized_pagerank(
    seed_node_ids: list[int],
    *,
    config: RerankConfig | None = None,
    graph=None,
) -> pd.Series:
    """Run PPR from ``seed_node_ids``. Returns a Series indexed by node id."""
    config = config or RerankConfig()
    graph = graph if graph is not None else get_graph()

    params: dict = {
        "sourceNodes": seed_node_ids,
        "dampingFactor": config.damping_factor,
        "maxIterations": config.max_iterations,
        "tolerance": config.tolerance,
    }
    if config.weighted:
        params["relationshipWeightProperty"] = "weight"

    frame = gds().pageRank.stream(graph, **params)
    return frame.set_index("nodeId")["score"]


def global_pagerank(*, config: RerankConfig | None = None, graph=None) -> pd.Series:
    """Query-independent PageRank, computed once and cached for the session.

    Used as the denominator of the ``lift`` normalization: a chunk that scores
    high for *every* question is not telling us anything about *this* one.
    """
    config = config or RerankConfig()
    graph = graph if graph is not None else get_graph()

    key = f"{graph.name()}::{config.weighted}::{config.damping_factor}"
    if key in _GLOBAL_PAGERANK_CACHE:
        return _GLOBAL_PAGERANK_CACHE[key]

    params: dict = {
        "dampingFactor": config.damping_factor,
        "maxIterations": config.max_iterations,
        "tolerance": config.tolerance,
    }
    if config.weighted:
        params["relationshipWeightProperty"] = "weight"

    frame = gds().pageRank.stream(graph, **params)
    series = frame.set_index("nodeId")["score"]
    _GLOBAL_PAGERANK_CACHE[key] = series
    return series


def _min_max(values: pd.Series) -> pd.Series:
    low, high = values.min(), values.max()
    if high - low < 1e-12:
        return pd.Series(0.5, index=values.index)
    return (values - low) / (high - low)


def rerank(
    question: str,
    *,
    config: RerankConfig | None = None,
    with_graph_context: bool = False,
) -> RetrievalResult:
    """Vector search for candidates, personalized PageRank for the ranking."""
    config = config or RerankConfig()
    started = time.perf_counter()

    # ── 1. Wide vector recall ────────────────────────────────────────────────
    candidates = vector_search(embed(question), k=config.candidate_k)
    if not candidates:
        return RetrievalResult(question=question, strategy="vector+ppr")

    id_map = chunk_ids_to_node_ids([c.chunk_id for c in candidates])
    seeds = [c for c in candidates[: config.seed_k] if c.chunk_id in id_map]
    seed_node_ids = [id_map[c.chunk_id] for c in seeds]
    if not seed_node_ids:
        return RetrievalResult(question=question, strategy="vector+ppr")

    # ── 2. Personalized PageRank from the strongest vector hits ──────────────
    ppr_scores = personalized_pagerank(seed_node_ids, config=config)

    if config.normalize == "lift":
        baseline_scores = global_pagerank(config=config)
        graph_scores = ppr_scores / (baseline_scores.reindex(ppr_scores.index) + 1e-12)
    else:
        graph_scores = ppr_scores

    # ── 3. Blend cosine similarity with graph centrality ─────────────────────
    candidate_node_ids = [id_map[c.chunk_id] for c in candidates if c.chunk_id in id_map]
    graph_component = graph_scores.reindex(candidate_node_ids).fillna(0.0)
    vector_component = pd.Series(
        {id_map[c.chunk_id]: (c.vector_score or 0.0) for c in candidates if c.chunk_id in id_map}
    )

    norm_graph = _min_max(graph_component)
    norm_vector = _min_max(vector_component.reindex(candidate_node_ids))
    blended = config.alpha * norm_vector + (1 - config.alpha) * norm_graph

    # ── 4. Rerank and cut to the context window ──────────────────────────────
    by_node_id = {id_map[c.chunk_id]: c for c in candidates if c.chunk_id in id_map}
    vector_rank = {c.chunk_id: i + 1 for i, c in enumerate(candidates)}
    seed_ids = {c.chunk_id for c in seeds}

    reranked: list[RetrievedChunk] = []
    for node_id, score in blended.sort_values(ascending=False).items():
        chunk = by_node_id[node_id]
        chunk.graph_score = float(graph_component.get(node_id, 0.0))
        chunk.final_score = float(score)
        chunk.source = "seed" if chunk.chunk_id in seed_ids else "ppr"
        reranked.append(chunk)

    selected = reranked[: config.k]

    result = RetrievalResult(
        question=question,
        strategy="vector+ppr",
        chunks=selected,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        debug={
            "candidate_k": config.candidate_k,
            "seed_k": config.seed_k,
            "alpha": config.alpha,
            "normalize": config.normalize,
            "seed_chunk_ids": [c.chunk_id for c in seeds],
            "vector_rank": {c.chunk_id: vector_rank[c.chunk_id] for c in selected},
            # Chunks the graph pulled into the window that plain vector top-k missed
            "promoted": [
                c.chunk_id for c in selected if vector_rank[c.chunk_id] > config.k
            ],
        },
    )
    if with_graph_context:
        attach_graph_context(result)
    return result

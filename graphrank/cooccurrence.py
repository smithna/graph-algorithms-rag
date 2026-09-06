"""Node similarity as a *retrieval* strategy, not just a resolution one.

Section 4 spends most of its time using node similarity at build time, to find
entities that are secretly the same. The same algorithm answers a different and
genuinely useful question at query time:

    "Find chunks that share entities with this chunk"

which is not the same question as

    "Find chunks that sound like this chunk"

and catches things embeddings miss. A passage describing the Shoshone horse
trade and a passage describing Cameahwait's kinship claim may share almost no
vocabulary — different verbs, different subjects, one about animals and one
about people — while sharing the rare entities that make them the same episode.
Cosine similarity over text sees two unrelated passages. Cosine similarity over
*entity membership* sees one story.

How it works
────────────
The retrieval projection already contains everything needed. ``MENTIONS`` edges
connect entities to chunks and carry the IDF weight

    log(1 + totalChunks / df)

so running ``gds.nodeSimilarity.filtered`` over that relationship type alone,
weighted, computes cosine similarity between chunks over their weighted entity
sets. Sharing *Beaverhead Rock* counts heavily; sharing *Lewis* counts for
almost nothing. That weighting is the difference between this strategy working
and it returning the same Lewis-adjacent passages for every question — the same
hub trap section 5 breaks for PageRank, defused the same way.

No new projection is needed, which is the point worth making on the slide:
projection is the expensive step and it is amortised across every strategy in
this repo.

The blend
─────────
Like the PageRank strategy, this one nominates with vectors and ranks with
structure. ``alpha`` controls the mix, and ``alpha=1.0`` reproduces the vector
baseline exactly — which is the honest way to show a strategy is doing something
rather than merely reordering noise.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import pandas as pd

from .baseline import attach_graph_context, vector_search
from .config import gds
from .embedding import embed
from .models import RetrievalResult, RetrievedChunk
from .projection import chunk_ids_to_node_ids, get_graph, node_ids_to_chunks


@dataclass
class CooccurrenceConfig:
    #: How many chunks the vector index nominates
    candidate_k: int = 50
    #: How many of those are used as similarity sources
    seed_k: int = 5
    #: How many survive into the context window
    k: int = 8
    #: 1.0 = pure cosine, 0.0 = pure entity-overlap
    alpha: float = 0.5
    #: Neighbours per source considered by node similarity
    top_k: int = 25
    #: Ignore pairs below this cosine similarity over entity sets
    similarity_cutoff: float = 0.05
    #: Use the projection's IDF weights rather than raw entity counts
    weighted: bool = True


def _min_max(values: pd.Series) -> pd.Series:
    low, high = values.min(), values.max()
    if high - low < 1e-12:
        return pd.Series(0.5, index=values.index)
    return (values - low) / (high - low)


def similar_chunks(
    seed_node_ids: list[int],
    *,
    config: CooccurrenceConfig | None = None,
    graph=None,
) -> pd.Series:
    """Chunks sharing entities with the seeds, scored by weighted cosine.

    Returns a Series indexed by chunk node id. Restricting ``relationshipTypes``
    to ``MENTIONS`` is what makes this entity overlap rather than a blend of
    entity overlap and reading order — ``NEXT_CHUNK`` would otherwise make every
    chunk similar to its neighbours for reasons that have nothing to do with
    what they are about.
    """
    config = config or CooccurrenceConfig()
    graph = graph if graph is not None else get_graph()

    params: dict = {
        "sourceNodeFilter": seed_node_ids,
        "targetNodeFilter": "Chunk",
        "relationshipTypes": ["MENTIONS"],
        "topK": config.top_k,
        "similarityCutoff": config.similarity_cutoff,
        "similarityMetric": "COSINE",
    }
    if config.weighted:
        params["relationshipWeightProperty"] = "weight"

    frame = gds().nodeSimilarity.filtered.stream(graph, **params)
    if frame.empty:
        return pd.Series(dtype=float)

    # A chunk reachable from several seeds is better evidence than one reachable
    # from a single seed, so accumulate rather than take the max.
    return frame.groupby("node2")["similarity"].sum()


def retrieve(
    question: str,
    *,
    config: CooccurrenceConfig | None = None,
    with_graph_context: bool = False,
) -> RetrievalResult:
    """Vector search for seeds, entity overlap for the ranking."""
    config = config or CooccurrenceConfig()
    started = time.perf_counter()

    candidates = vector_search(embed(question), k=config.candidate_k)
    if not candidates:
        return RetrievalResult(question=question, strategy="cooccurrence")

    id_map = chunk_ids_to_node_ids([c.chunk_id for c in candidates])
    seeds = [c for c in candidates[: config.seed_k] if c.chunk_id in id_map]
    seed_node_ids = [id_map[c.chunk_id] for c in seeds]
    if not seed_node_ids:
        return RetrievalResult(question=question, strategy="cooccurrence")

    overlap = similar_chunks(seed_node_ids, config=config)

    # The candidate slate is the union of what vectors nominated and what entity
    # overlap discovered. The second half is the whole point: those chunks were
    # never in the vector top-k, and several of them are the answer.
    by_node_id: dict[int, RetrievedChunk] = {
        id_map[c.chunk_id]: c for c in candidates if c.chunk_id in id_map
    }
    discovered = [int(n) for n in overlap.index if int(n) not in by_node_id]
    for node_id, row in node_ids_to_chunks(discovered).items():
        by_node_id[node_id] = RetrievedChunk(
            chunk_id=row["chunkId"],
            text=row["text"],
            date=row["date"],
            author=row["author"],
            vector_score=None,
            source="cooccurrence",
        )

    node_ids = list(by_node_id)
    graph_component = overlap.reindex(node_ids).fillna(0.0)
    vector_component = pd.Series(
        {nid: (chunk.vector_score or 0.0) for nid, chunk in by_node_id.items()}
    ).reindex(node_ids)

    blended = config.alpha * _min_max(vector_component) + (1 - config.alpha) * _min_max(
        graph_component
    )

    vector_rank = {c.chunk_id: i + 1 for i, c in enumerate(candidates)}
    seed_ids = {c.chunk_id for c in seeds}

    ranked: list[RetrievedChunk] = []
    for node_id, score in blended.sort_values(ascending=False).items():
        chunk = by_node_id[node_id]
        chunk.graph_score = float(graph_component.get(node_id, 0.0))
        chunk.final_score = float(score)
        if chunk.chunk_id in seed_ids:
            chunk.source = "seed"
        elif chunk.vector_score is None:
            chunk.source = "cooccurrence"
        else:
            chunk.source = "vector+cooccurrence"
        ranked.append(chunk)

    selected = ranked[: config.k]

    result = RetrievalResult(
        question=question,
        strategy="cooccurrence",
        chunks=selected,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        debug={
            "candidate_k": config.candidate_k,
            "seed_k": config.seed_k,
            "alpha": config.alpha,
            "seed_chunk_ids": [c.chunk_id for c in seeds],
            "discovered_beyond_vector": len(discovered),
            # Chunks entity overlap pulled in that the vector index never
            # nominated at all — the ones a pure embedding pipeline cannot reach
            "off_vector": [
                c.chunk_id for c in selected if c.chunk_id not in vector_rank
            ],
        },
    )
    if with_graph_context:
        attach_graph_context(result)
    return result

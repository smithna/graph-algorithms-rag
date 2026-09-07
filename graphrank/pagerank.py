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

import math
import time
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from .baseline import attach_graph_context, vector_search
from .config import gds
from .embedding import embed
from .models import RetrievalResult, RetrievedChunk
from .projection import chunk_ids_to_node_ids, get_graph, node_ids_to_chunks

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


# ═════════════════════════════════════════════════════════════════════════════
#  Section 5: multi-seed PPR over the mentions graph
# ═════════════════════════════════════════════════════════════════════════════
#
# Everything above reranks the vector top-k. That is the safe use of PPR and it
# is nearly a no-op on this corpus — the upside is bounded by "what sits in
# positions 9-50 that belongs in 1-8", which measured as one slot in eight. The
# thing PPR is actually good at, surfacing passages nobody nominated, is
# forbidden by the candidate gate.
#
# What the corpus needs instead is *conjunction*. Cosine scores every passage
# against the question independently, on vocabulary, and has no representation
# for "this passage connects two things the question is about". Measured:
# passages carrying two or more of a question's gold entities sit at a median
# cosine rank of 524 of 2,913, and 5 of 13 benchmark questions have none at all
# in the vector top-8. One passage names both Charles Floyd and the Missouri
# River; cosine ranks it 415 of 2,913. Blended retrieval brings it to 68 at the
# default 0.6/0.4 weighting, and to 16 at pure structure — the passage that most
# needs the graph is the one cosine's weight costs the most.
#
# Multi-seed PPR is conjunction-aware for free, because PPR is **linear in the
# restart distribution**:
#
#     PPR(w1*v1 + w2*v2)  ==  w1*PPR(v1) + w2*PPR(v2)
#
# exactly, not approximately — verified on this graph to 7e-07. GDS exposes that
# directly: ``sourceNodes`` takes node-bias pairs, and the bias *is* the linear
# weight. So an arbitrarily weighted multi-seed walk is **one** call, and the
# whole retrieval is two (one per structural signal), not one per seed.

from .config import read_query
from .projection import (
    all_chunk_node_ids,
    get_mentions_graph,
    mentions_membership,
)

#: PPR result per (graph, seed, damping, weighted). Linearity means this cache
#: is reusable across questions *and* across every seed weighting.
_SEED_PPR_CACHE: dict[tuple, pd.Series] = {}

# ── MEASURED: seed weighting does not matter on this corpus ─────────────────
#
# The intuition is strong — weight each seed by how well it matches the
# question, so a better match pulls harder. It does nothing here, and the
# negative result is worth keeping because the knob looks so plausible.
#
# Entity cosine scores cluster tightly (0.203/0.202/0.201/0.198 after
# normalising), so ``proportional`` is arithmetically almost ``uniform``.
# ``softmax`` and ``margin`` exist to *force* a spread — softmax reaches
# 0.40/0.03, a 13x ratio — and the retrieval outcome still does not move:
#
#     weighting       top-8   median rank      cosine off: top-8   median
#     uniform            22           318                     10      502
#     proportional       22           318                     10      500
#     softmax            22           326                     10      506
#     margin             23           326                     10      502
#
# The mechanism: every seed for a question is semantically close to the
# question, so the seeds sit in overlapping neighbourhoods and their PPR
# distributions are highly correlated. Reweighting a set of nearly-parallel
# vectors barely rotates the sum. Weighting would matter if the seeds were
# *far apart* — genuinely ambiguous candidates in different parts of the graph
# — which is worth saying, because that is exactly when you reach for it.
#
# All four are kept selectable so the demo can show the non-effect rather than
# assert it. ``proportional`` stays the default: principled, free, harmless.
#
# ── But the seed *count* matters a great deal ───────────────────────────────
#
# Same measurement, varying how many entities are seeded (shipped path,
# cosine 0.6 / structure 0.4):
#
#     entity_seed_k    top-8   median rank
#     1                   14           380
#     2                   23           308      <- the whole win is here
#     3                   22           314
#     5                   22           318
#     8                   23           335
#
# Going from one seed to two lifts conjunction passages in the top-8 by 64%;
# everything after that is flat. Which is the design claim, earned: you do not
# need to *pick* the right entity, and you do not need to weight the
# candidates cleverly — you need to stop choosing exactly one. At pure
# structure the tail degrades further (8 seeds drops to 4 in the top-8, because
# weak semantic matches start seeding unrelated neighbourhoods); cosine's share
# masks that in the blend.
SEED_WEIGHTINGS = ("uniform", "proportional", "softmax", "margin")


@dataclass
class ExpandConfig:
    """Config for corpus-wide multi-seed PPR retrieval."""

    #: How many survive into the context window
    k: int = 8
    #: Discard entity seeds mentioned in fewer than this many chunks. 0 = keep all.
    #:
    #: ── Why this knob exists ────────────────────────────────────────────────
    #:
    #: PPR normalises each single-seed run to sum ~1, so **every seed gets the
    #: same total mass regardless of degree** — and therefore mass *per chunk*
    #: goes as 1/degree. A degree-1 seed puts essentially all of its mass on its
    #: single chunk: ~62x what a degree-62 seed gives each of its own.
    #:
    #: This is not hypothetical. Measured seed degrees:
    #:
    #:     charbonneau-role        62,  1,  1
    #:     sacagawea-interpreting  64,  1
    #:     shoshone-horses          2,  1,  1     <- the whole signal is 4 chunks
    #:
    #: and the top of the entity ranking is then mechanical rather than
    #: retrieved — 1806-05-10 took 99.9% of its score from one degree-1 seed.
    #: Semantic match cannot police this: match scores span ~2% across seeds
    #: while degree spans 62x, so `seed_weighting` is three orders of magnitude
    #: too weak to compensate. It is the same reason weighting measured as a
    #: no-op.
    #:
    #: **But a degree-1 seed is a confident bet, not automatically a bad one.**
    #: `BIRTH OF JEAN BAPTISTE CHARBONNEAU` (degree 1) spikes 1805-02-11, which
    #: is the birth passage and genuinely relevant. `JEAN BAPTISTE CHARBONNEAU`
    #: (degree 1) spikes 1806-05-27, which is not. High variance either way.
    #:
    #: Measured against the hand-read passages of finding 5d (n=4, so a
    #: direction rather than a verdict) — filtering and degree-proportional bias
    #: come out equivalent, and both are marginal:
    #:
    #:     variant             charbonneau (cos .6 / .3)   sacagawea (.6 / .3)
    #:     keep all (default)  3/3 [7,3,5]  2/3 [13,2,4]   [8]  [6]
    #:     bias by degree      3/3 [8,3,4]  2/3 [11,2,3]   [7]  [6]
    #:     drop degree < 5     3/3 [8,3,4]  2/3 [11,2,3]   [7]  [6]
    #:
    #: **Default is 0 (off)** because the evidence is four passages, and because
    #: a filter can empty the seed set outright: at 5, all three
    #: `shoshone-horses` seeds are discarded and the entity signal disappears
    #: silently. If you raise this, check for that.
    min_seed_degree: int = 0
    #: Entity seeds drawn from question-to-entity semantic match.
    #: 1 -> 2 is the single biggest structural win in this pipeline (+64%
    #: conjunction passages in the top-8); 2-8 is a plateau in the blend. Three
    #: is chosen because it also sits near the peak at *pure* structure, where
    #: the tail degrades past 5 — so it is the robust choice across both
    #: regimes rather than the best in either.
    entity_seed_k: int = 3
    #: Passage seeds drawn from the cosine top-N
    passage_seed_k: int = 5
    #: Weight on cosine; the remainder is split across the two PPR signals.
    #: Measured plateau is broad — every value from 0.9 to 0.1 beats cosine
    #: alone (13 conjunction passages in the top-8 at 1.0, 20-23 everywhere
    #: else), and 0.7-0.3 are indistinguishable. The knob is forgiving; do not
    #: read a precise optimum into it on thirteen questions.
    cosine_weight: float = 0.6
    #: How the entity PPR and passage PPR halves divide the structural weight
    entity_share: float = 0.5
    #: One of :data:`SEED_WEIGHTINGS`. Measured a no-op for retrieval quality,
    #: and free either way — GDS takes per-seed bias in the same single call —
    #: so this is kept at the principled default rather than the cheap one.
    seed_weighting: str = "proportional"
    #: Temperature for ``softmax`` weighting. Smaller is sharper.
    softmax_temperature: float = 0.01
    #: Walk horizon. Mass within k steps is ``1 - d**(k+1)``, so 0.45 keeps 96%
    #: of the walk inside three steps. Measured: shorter is monotonically
    #: better here, and 0.85 was the worst of six values tested.
    #:
    #: Deliberately *not* ported into :class:`RerankConfig`, which runs a
    #: different architecture over a different projection. Section 4's finding
    #: 3c is the standing lesson: an operating point measured on one machine is
    #: not automatically right for another one.
    damping_factor: float = 0.45
    max_iterations: int = 30
    tolerance: float = 1e-8
    #: Use the IDF weights baked into the mentions projection
    weighted: bool = True


@lru_cache(maxsize=1)
def entity_index_names() -> tuple[str, ...]:
    """Vector indexes over entities — every one except the chunk index.

    Read from the database rather than hardcoded, so a new entity label with an
    index is picked up automatically. Note ``Supply`` (634 nodes) has no
    embedding and no index, so it can never be seeded semantically.
    """
    rows = read_query("SHOW VECTOR INDEXES YIELD name, labelsOrTypes")
    return tuple(
        row["name"]
        for row in rows
        if "Chunk" not in (row["labelsOrTypes"] or [])
    )


@dataclass
class Seed:
    node_id: int
    name: str
    label: str
    match_score: float
    weight: float = 0.0


def _apply_weighting(
    scores: list[float], weighting: str, *, temperature: float, baseline: float | None
) -> list[float]:
    """Turn semantic match scores into restart weights that sum to 1."""
    n = len(scores)
    if n == 0:
        return []
    if weighting == "uniform":
        return [1.0 / n] * n
    if weighting == "proportional":
        total = sum(scores) or 1.0
        return [s / total for s in scores]
    if weighting == "softmax":
        top = max(scores)
        exps = [math.exp((s - top) / max(temperature, 1e-9)) for s in scores]
        total = sum(exps) or 1.0
        return [e / total for e in exps]
    if weighting == "margin":
        # Zero the scale at the first *rejected* entity, so the kept seeds are
        # weighted by how much better than the cutoff they were. This is what
        # gives a tightly-clustered score set any usable spread.
        floor = baseline if baseline is not None else min(scores) * 0.999
        gaps = [max(s - floor, 0.0) for s in scores]
        total = sum(gaps)
        if total <= 0:
            return [1.0 / n] * n
        return [g / total for g in gaps]
    raise ValueError(f"Unknown seed_weighting {weighting!r}; expected one of {SEED_WEIGHTINGS}")


def entity_seeds(
    question_embedding: list[float], *, config: ExpandConfig | None = None
) -> list[Seed]:
    """Semantic-match the question against entity names; seed *all* the best ones.

    This is the step that makes entity resolution optional rather than
    load-bearing. You never have to decide which of two ``SACAGAWEA`` nodes is
    the real one, or which of four tree species was meant — seed both, or all
    four, weighted by match, and let the structure sort it out. An argmax
    linking step fails hard when it picks wrong; proportional seeding degrades
    gracefully.
    """
    config = config or ExpandConfig()
    in_graph = mentions_membership()

    rows: list[dict] = []
    for index in entity_index_names():
        rows += read_query(
            """
            CALL db.index.vector.queryNodes($index, 5, $embedding)
            YIELD node AS n, score
            WHERE NOT n:Chunk
            RETURN id(n)                            AS nodeId,
                   coalesce(n.canonicalName, n.name) AS name,
                   head(labels(n))                  AS label,
                   score
            """,
            index=index,
            embedding=question_embedding,
        )

    rows = [r for r in rows if r["nodeId"] in in_graph]
    if config.min_seed_degree > 0:
        keep = {
            r["nodeId"]
            for r in read_query(
                """
                UNWIND $ids AS nid
                MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE id(e) = nid
                WITH nid, count(DISTINCT c) AS df
                WHERE df >= $minDf
                RETURN nid AS nodeId
                """,
                ids=list({r["nodeId"] for r in rows}),
                minDf=config.min_seed_degree,
            )
        }
        filtered = [r for r in rows if r["nodeId"] in keep]
        # Never hand back an empty seed set silently — see the note on
        # min_seed_degree; shoshone-horses loses every seed at a threshold of 5.
        rows = filtered or rows
    rows.sort(key=lambda r: -r["score"])

    seen: set[int] = set()
    unique: list[dict] = []
    for row in rows:
        if row["nodeId"] in seen:
            continue
        seen.add(row["nodeId"])
        unique.append(row)

    kept = unique[: config.entity_seed_k]
    # The first rejected match is the natural zero point for `margin` weighting.
    baseline = (
        unique[config.entity_seed_k]["score"]
        if len(unique) > config.entity_seed_k
        else None
    )
    weights = _apply_weighting(
        [r["score"] for r in kept],
        config.seed_weighting,
        temperature=config.softmax_temperature,
        baseline=baseline,
    )
    return [
        Seed(
            node_id=r["nodeId"],
            name=r["name"],
            label=r["label"],
            match_score=float(r["score"]),
            weight=float(w),
        )
        for r, w in zip(kept, weights)
    ]


def seed_pagerank(node_id: int, *, config: ExpandConfig | None = None) -> pd.Series:
    """PPR from a single restart node, cached for the session.

    Single-seed rather than multi-seed on purpose: linearity means any weighted
    combination of seeds is a weighted sum of these, so caching per seed makes
    reweighting free and lets seeds shared between questions be reused.
    """
    config = config or ExpandConfig()
    graph = get_mentions_graph()
    key = (graph.name(), node_id, config.damping_factor, config.weighted)
    if key in _SEED_PPR_CACHE:
        return _SEED_PPR_CACHE[key]

    params: dict = {
        "sourceNodes": [node_id],
        "dampingFactor": config.damping_factor,
        "maxIterations": config.max_iterations,
        "tolerance": config.tolerance,
    }
    if config.weighted:
        params["relationshipWeightProperty"] = "weight"

    frame = gds().pageRank.stream(graph, **params)
    series = frame.set_index("nodeId")["score"]
    _SEED_PPR_CACHE[key] = series
    return series


def combine_seeds(
    weighted_seeds: list[tuple[int, float]], *, config: ExpandConfig | None = None
) -> pd.Series:
    """Weighted sum of single-seed PPR runs — exact, by linearity.

    **Prefer :func:`batched_pagerank`.** This existed to get weighted seeds,
    which turned out to be unnecessary: GDS ``sourceNodes`` accepts node-bias
    pairs, so a weighted multi-seed walk is one call rather than N. What is left
    here is a per-seed cache, useful only when the same seed recurs across many
    questions, and a direct demonstration that linearity holds.

    Kept because it makes the linearity claim checkable rather than asserted —
    the equality against a single biased call is a two-line test.
    """
    config = config or ExpandConfig()
    total: pd.Series | None = None
    for node_id, weight in weighted_seeds:
        contribution = seed_pagerank(node_id, config=config) * weight
        total = contribution if total is None else total.add(contribution, fill_value=0.0)
    return total if total is not None else pd.Series(dtype=float)


def batched_pagerank(
    seeds: list[int] | list[tuple[int, float]], *, config: ExpandConfig | None = None
) -> pd.Series:
    """PPR from a whole seed set in **one** GDS call, with optional per-seed bias.

    ``seeds`` is either a flat list of node ids (uniform restart) or a list of
    ``(node_id, bias)`` pairs. GDS ``sourceNodes`` accepts both — the biased
    form is the documented ``[[nodeId1, bias1], [nodeId2, bias2], ...]`` syntax:

        https://neo4j.com/docs/graph-data-science/current/algorithms/page-rank/

    Two things measured against GDS 2026.7.0, because the docs do not say:

    1. **Bias is the unnormalised linear weight.** ``sourceNodes=[[n, w], ...]``
       equals ``sum(w * PPR(n))`` to 7e-07. Biases are *not* rescaled to sum to
       one — doubling every bias doubles every output score exactly. A flat list
       is identical to every bias being 1.0 (diff 1.7e-18), which means GDS
       gives each source node its own unit of restart mass, so a flat batched
       run is the **sum** of the single-seed runs, not their mean.
    2. **One call is near-free in the seed count**, because the cost is per-call
       fixed overhead — graph setup plus streaming 6,270 rows — not the number
       of sources:

           seeds     1 call, N sources     N calls, 1 source     ratio
           1                    52.4 ms               53.4 ms   1.02x
           2                    54.9 ms              107.8 ms   1.96x
           3                    53.8 ms              165.0 ms   3.07x
           5                    54.8 ms              273.5 ms   4.99x
           8                    56.2 ms              440.6 ms   7.84x

    Together those mean weighted multi-seed PPR costs exactly one call. There is
    no speed/expressiveness trade-off to make here, which is worth knowing:
    :func:`combine_seeds` looks like it buys expressiveness and does not.
    """
    config = config or ExpandConfig()
    if not seeds:
        return pd.Series(dtype=float)

    if isinstance(seeds[0], tuple):
        source_nodes = [[int(node), float(bias)] for node, bias in seeds]  # type: ignore[misc]
    else:
        source_nodes = [int(node) for node in seeds]  # type: ignore[arg-type]

    params: dict = {
        "sourceNodes": source_nodes,
        "dampingFactor": config.damping_factor,
        "maxIterations": config.max_iterations,
        "tolerance": config.tolerance,
    }
    if config.weighted:
        params["relationshipWeightProperty"] = "weight"

    frame = gds().pageRank.stream(get_mentions_graph(), **params)
    return frame.set_index("nodeId")["score"]


def _percentile(values: pd.Series) -> pd.Series:
    """Rank-normalise to [0, 1].

    Min-max is wrong for PPR and it is worth knowing why: PPR scores are
    power-law distributed, so the restart nodes take almost all the mass and
    min-max maps everything else to ~0. Blending that against cosine hands the
    entire decision to cosine. Percentile ranks are scale-free and survive the
    skew.
    """
    return values.rank(pct=True)


def expand(
    question: str,
    *,
    config: ExpandConfig | None = None,
    with_graph_context: bool = False,
) -> RetrievalResult:
    """Retrieve over the **whole corpus** by blending cosine with multi-seed PPR.

    Two structural signals, both over the mentions-only graph:

    ``entity``   seeds are entities the question semantically matches, so the
                 walk fans out from what the question is *about*
    ``passage``  seeds are the top cosine hits, so the walk reinforces the
                 entities the best semantic matches have in common

    Unlike :func:`rerank`, nothing gates the candidate set — every chunk in the
    corpus is scored. That is the point: the passage naming both Floyd and the
    Missouri sits at cosine rank 415, so no candidate window short enough to be
    worth having would ever have contained it.
    """
    config = config or ExpandConfig()
    started = time.perf_counter()

    embedding = embed(question)
    chunk_index = pd.Index(all_chunk_node_ids())
    in_graph = mentions_membership()

    # ── 1. Cosine over the entire corpus ─────────────────────────────────────
    t0 = time.perf_counter()
    rows = read_query(
        """
        CALL db.index.vector.queryNodes('chunk_embeddings', $k, $embedding)
        YIELD node AS c, score
        RETURN id(c) AS nodeId, c.chunkId AS chunkId, score
        """,
        k=len(chunk_index),
        embedding=embedding,
    )
    cosine = pd.Series({r["nodeId"]: r["score"] for r in rows}).reindex(chunk_index).fillna(0.0)
    cosine_rank = {r["nodeId"]: i + 1 for i, r in enumerate(rows)}
    cosine_ms = (time.perf_counter() - t0) * 1000

    # ── 2. Entity-seeded PPR ─────────────────────────────────────────────────
    t0 = time.perf_counter()
    seeds = entity_seeds(embedding, config=config)
    # One call, biased by seed weight. GDS bias == the linear weight exactly, so
    # any weighting is free; see batched_pagerank.
    entity_scores = (
        batched_pagerank([(s.node_id, s.weight) for s in seeds], config=config)
        .reindex(chunk_index)
        .fillna(0.0)
    )
    entity_ms = (time.perf_counter() - t0) * 1000

    # ── 3. Passage-seeded PPR ────────────────────────────────────────────────
    t0 = time.perf_counter()
    passage_seed_ids = [
        r["nodeId"] for r in rows if r["nodeId"] in in_graph
    ][: config.passage_seed_k]
    # Always uniform — the top cosine hits are not ranked against each other.
    passage_scores = (
        batched_pagerank(passage_seed_ids, config=config)
        .reindex(chunk_index)
        .fillna(0.0)
    )
    passage_ms = (time.perf_counter() - t0) * 1000

    # ── 4. Blend on percentile ranks ─────────────────────────────────────────
    structural = 1.0 - config.cosine_weight
    blended = (
        config.cosine_weight * _percentile(cosine)
        + structural * config.entity_share * _percentile(entity_scores)
        + structural * (1.0 - config.entity_share) * _percentile(passage_scores)
    )

    ordered = list(blended.sort_values(ascending=False).head(config.k).index)
    texts = node_ids_to_chunks(ordered)

    chunks: list[RetrievedChunk] = []
    for node_id in ordered:
        row = texts.get(node_id)
        if row is None:
            continue
        chunks.append(
            RetrievedChunk(
                chunk_id=row["chunkId"],
                text=row["text"],
                date=row["date"],
                author=row["author"],
                vector_score=float(cosine.get(node_id, 0.0)),
                graph_score=float(entity_scores.get(node_id, 0.0)),
                final_score=float(blended.get(node_id, 0.0)),
                source="seed" if node_id in set(passage_seed_ids) else "ppr",
            )
        )

    result = RetrievalResult(
        question=question,
        strategy="expand",
        chunks=chunks,
        elapsed_ms=(time.perf_counter() - started) * 1000,
        debug={
            "cosine_weight": config.cosine_weight,
            "entity_share": config.entity_share,
            "seed_weighting": config.seed_weighting,
            "damping_factor": config.damping_factor,
            "corpus_scored": len(chunk_index),
            "entity_seeds": [
                {
                    "name": s.name,
                    "label": s.label,
                    "match": round(s.match_score, 4),
                    "weight": round(s.weight, 4),
                }
                for s in seeds
            ],
            "cosine_rank": {
                row["chunkId"]: cosine_rank.get(node_id)
                for node_id, row in ((n, texts[n]) for n in ordered if n in texts)
            },
            # Passages the structure pulled in from outside the cosine top-k
            "promoted": [
                texts[n]["chunkId"]
                for n in ordered
                if n in texts and (cosine_rank.get(n) or 10**9) > config.k
            ],
            "timings_ms": {
                "cosine": round(cosine_ms, 1),
                "entity_ppr": round(entity_ms, 1),
                "passage_ppr": round(passage_ms, 1),
            },
        },
    )
    if with_graph_context:
        attach_graph_context(result)
    return result

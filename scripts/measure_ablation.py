#!/usr/bin/env python3
"""The extraction-grade ablation: degrade the graph to NER grade, measure who pays.

    python scripts/measure_ablation.py                       # all three questions
    python scripts/measure_ablation.py --only charbonneau-role
    python scripts/measure_ablation.py --generous            # sensitivity: audited gazetteer
    python scripts/measure_ablation.py --keep-graphs         # leave projections up

Finding 5h-1's experiment, behind 5h-5's approved framing. Section 4's graph
resolved pronouns at build time ("one of his wives" -> SACAGAWEA), so the tag
filter owns the corpus's best passages and 5g measured filter+cosine at parity
with PPR. Most graphs are not built that well. This script simulates the graph
most people have — plain NER with a name gazetteer, no coreference pass, no
resolution — by keeping only the ``MENTIONED_IN`` edges that
``measure_extraction_grade.py`` classifies as **name-backed** (surface-only and
inference edges both drop: a descriptive alias like "the squaw" was linked by
build-time coreference, and an inference edge never had a surface form at all).
The classification is imported from that script, not reimplemented.

Three arms, all read-only against the store (projections are in-memory, under
this script's own names — ``lc-mentions`` and ``lc-retrieval`` are not touched):

1. **filter+cosine on ablated tags** — 5g's champion, on the graph it actually
   gets. Membership only: an endpoint whose seed edge dropped is lost *by
   construction*; the arm exists to show that, not to rank.
2. **entity-seeded PPR (decomposed seeder) on the ablated graph** — the
   measurement is each judged passage's RANK under pure entity-PPR score,
   corpus-wide, next to the same walk's rank on the full graph. Ranks, not
   top-k membership: n is small and thresholds manufacture findings
   (5d-quinquies).
3. **arm 2 + NEXT_CHUNK edges** — the query-time coreference patch. Pronoun
   antecedents live in the preceding chunk, so the sequence edge gets the one
   mechanistic job 5c never gave it: bridging a chunk whose only route in was
   a resolved pronoun.

Endpoints are the passages already judged by reading (5d, 5f) plus the two 5h-1
receipts — no new relevance judgements are made here. Each endpoint is
classified first: if its seed-entity edge is name-backed it *survives* ablation
and serves as a sanity control, not a test case. The test cases are the three
SACAGAWEA coref-only passages.

Results and their reading live in ``docs/talk-outline.md``, finding 5i.

Known boundary case, found during hand verification and kept deliberately:
SHOSHONE -> Nov-4 is classed surface-only ("Snake Indians" is a filed alias but
an *exonym* — no string kinship with SHOSHONE — so ``name_like`` calls it
descriptive) and therefore drops. Arguably a real NER+gazetteer would keep it;
dropping it makes the walk's job strictly harder, so a recovery here is the
conservative reading. Nov-4's surviving route is through TOUSSAINT CHARBONNEAU
(name-backed in that chunk).
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict

import _bootstrap  # noqa: F401
import pandas as pd
import yaml
from rich.console import Console
from rich.table import Table

from measure_extraction_grade import name_like, normalize
from graphrank.config import gds, read_query, settings
from graphrank.embedding import embed
from graphrank.pagerank import ExpandConfig, decomposed_entity_seeds
from graphrank.projection import (
    all_chunk_node_ids,
    drop_graph,
    graph_exists,
    project_mentions,
    total_chunks,
)

console = Console()
QUESTION_BANK = _bootstrap.ROOT / "questions" / "questions.yaml"

#: Projection names owned by this script. Never the configured ones.
ABLATED = "lc-mentions-ablated"
ABLATED_NEXT = "lc-mentions-ablated-next"

# ── Endpoints: every passage already judged by reading ────────────────────────
#
# 5d hand-read charbonneau-role (3 clear the bar) and sacagawea-interpreting
# (Nov-4, the best single instance); 5f's question audition added
# ordway-responsibilities (2 clear the bar). The two ``receipt`` chunks are
# 5h-1's: SACAGAWEA inference edges whose passages the hand reads crowned —
# Jun-16 was read in 5h-1, Aug-14 was judged the corpus's best in 5f's
# cameahwait-horses audition. Receipts measure *reachability from the
# SACAGAWEA seed*, not relevance to sacagawea-interpreting.
ENDPOINTS: dict[str, dict] = {
    "charbonneau-role": {
        "judged": {
            "c93c273845523b67": "1805-03-18 the hiring",
            "75f8e33804b7e5b1": "1804-12-18 which language",
            "a050481481fa6407": "1805-08-25 his judgement",
        },
        "receipts": {},
    },
    "sacagawea-interpreting": {
        "judged": {
            "13c2e69bf03a0342": "1804-11-04 'one of his wives'",
        },
        "receipts": {
            "9cd3f68af86f0822": "1805-06-16 her fever",
            "d78f95d2f2546361": "1805-08-14 Cameahwait",
        },
    },
    "ordway-responsibilities": {
        "judged": {
            "deeba7bd9825481c": "1804-05-17 court martial",
            "481d7edc8df88019": "1804-05-26 detachment order",
        },
        "receipts": {},
    },
}

#: The entity whose tag/seed carries each question — the edge whose class
#: decides control vs. test case. (The decomposed seeder may add twins.)
SEED_ENTITY = {
    "charbonneau-role": "TOUSSAINT CHARBONNEAU",
    "sacagawea-interpreting": "SACAGAWEA",
    "ordway-responsibilities": "JOHN ORDWAY",
}

# ── Hand-audited gazetteer gaps (2026-09-07) ──────────────────────────────────
#
# The classifier's known contamination, quantified for the one entity the
# result turns on. A regex sweep for every plausible spelling of Sacagawea's
# name (sah/sar + cah/kah + gar/gah…, sacaja…, janey) over all 2,913 chunk
# texts finds 12 chunks that *name* her. Six are the classifier's name-backed
# set. Five more carry a SACAGAWEA edge the classifier drops — either the text
# spelling is not filed as an alias ("Sah-kah-gar-wea", 1805-04-07) or the
# filed alias is a real name ``name_like`` calls descriptive ("Sah-cah-gah",
# "Janey"). The last two have no SACAGAWEA edge at all (extraction recall).
#
# ``--generous`` restores these five edges as name-backed — the "NER with the
# gazetteer a careful team would actually build" grade. None of the three test
# chunks is among them, so the test cases stay tests; the mode exists to show
# whether the conclusion survives the classifier's measured contamination.
GAZETTEER_AUDIT: dict[str, set[str]] = {
    "SACAGAWEA": {
        "3d03443918eb7706",  # 1805-04-07 "Sah-kah-gar-wea" — spelling not filed
        "66f0fbdde19d8a0d",  # 1805-05-20 "Sah-ca-gar me-ah or bird woman's River"
        "0434149b949d81cd",  # 1805-06-10 "Sah-cah-gah" — filed alias, misclassed
        "7afea42d00985598",  # 1805-11-24 "Janey" — filed alias, misclassed
        "3299119fad01e925",  # 1806-04-28 "Sah-cah gah" — filed alias, misclassed
    },
}


def classify_edges(*, generous: bool = False) -> tuple[list[tuple[int, int]], dict]:
    """Every MENTIONED_IN edge -> its support class; returns the name-backed
    survivors and bookkeeping for the mass report.

    Same classification as ``measure_extraction_grade.main`` — containment of
    the entity's known surface forms in the chunk text, with ``name_like``
    splitting names from descriptions — reused rather than reimplemented.
    """
    chunk_text = {
        row["id"]: normalize(row["text"])
        for row in read_query("MATCH (c:Chunk) RETURN id(c) AS id, c.text AS text")
    }
    entities = read_query(
        """
        MATCH (e)-[:MENTIONED_IN]->(:Chunk)
        WHERE NOT e:Chunk AND NOT e:GenericLocation
        WITH DISTINCT e
        RETURN id(e) AS id,
               coalesce(e.canonicalName, e.name) AS canonical,
               coalesce(e.aliases, []) AS aliases
        """
    )
    name_forms: dict[int, list[str]] = {}
    all_forms: dict[int, list[str]] = {}
    for e in entities:
        canonical = e["canonical"] or ""
        names = {normalize(canonical)} if canonical else set()
        everything = set(names)
        for alias in e["aliases"]:
            form = normalize(alias)
            everything.add(form)
            if name_like(alias, canonical):
                names.add(form)
        name_forms[e["id"]] = sorted(names)
        all_forms[e["id"]] = sorted(everything)

    edges = read_query(
        """
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        WHERE NOT e:Chunk AND NOT e:GenericLocation
        RETURN DISTINCT id(e) AS eid, id(c) AS cid, c.chunkId AS chunkId
        """
    )
    audit_edges: set[tuple[int, int]] = set()
    if generous:
        canonical_of = {e["id"]: e["canonical"] for e in entities}
        audit_edges = {
            (edge["eid"], edge["cid"])
            for edge in edges
            if edge["chunkId"] in GAZETTEER_AUDIT.get(canonical_of[edge["eid"]], ())
        }

    survivors: list[tuple[int, int]] = []
    edge_class: dict[tuple[int, int], str] = {}
    for edge in edges:
        text = chunk_text[edge["cid"]]
        key = (edge["eid"], edge["cid"])
        if any(f in text for f in name_forms[edge["eid"]]) or key in audit_edges:
            edge_class[key] = "name-backed"
            survivors.append(key)
        elif any(f in text for f in all_forms[edge["eid"]]):
            edge_class[key] = "surface-only"
        else:
            edge_class[key] = "inference"

    info = {
        "total_edges": len(edges),
        "edge_class": edge_class,
        "chunks_with_edges_full": {e["cid"] for e in edges},
        "chunks_with_edges_ablated": {c for _, c in survivors},
    }
    return survivors, info


def project_ablated(survivors: list[tuple[int, int]], *, with_next: bool) -> str:
    """Project the ablated mentions graph, IDF reweighted on the *ablated*
    degrees — an ordinary extraction would compute IDF from its own edges."""
    name = ABLATED_NEXT if with_next else ABLATED
    if graph_exists(name):
        drop_graph(name)

    df: dict[int, int] = defaultdict(int)
    for eid, _ in survivors:
        df[eid] += 1
    n_chunks = total_chunks()
    rows = [
        [eid, cid, math.log(1.0 + n_chunks / df[eid])] for eid, cid in survivors
    ]

    mention_part = """
        UNWIND $rows AS row
        MATCH (e) WHERE id(e) = row[0]
        MATCH (c) WHERE id(c) = row[1]
        RETURN e AS source, c AS target, 'MENTIONS' AS relType, row[2] AS weight
    """
    next_part = """
        UNION ALL
        MATCH (c1:Chunk)-[:NEXT_CHUNK]->(c2:Chunk)
        RETURN c1 AS source, c2 AS target,
               'NEXT_CHUNK' AS relType, $nextWeight AS weight
    """
    rel_types = ["MENTIONS", "NEXT_CHUNK"] if with_next else ["MENTIONS"]
    cypher = f"""
    CALL {{
        {mention_part}
        {next_part if with_next else ""}
    }}
    RETURN gds.graph.project(
        $graphName, source, target,
        {{
            sourceNodeLabels: labels(source),
            targetNodeLabels: labels(target),
            relationshipType: relType,
            relationshipProperties: {{weight: weight}}
        }},
        {{undirectedRelationshipTypes: {rel_types!r}}}
    )
    """
    params: dict = {"graphName": name, "rows": rows}
    if with_next:
        params["nextWeight"] = settings().next_chunk_weight
    graph, _ = gds().graph.cypher.project(cypher, **params)
    console.print(
        f"  projected [bold]{name}[/]: {graph.node_count()} nodes, "
        f"{graph.relationship_count()} relationships"
    )
    return name


def ppr_chunk_scores(
    graph_name: str, weighted_seeds: list[tuple[int, float]], config: ExpandConfig
) -> pd.Series:
    """Pure entity-seeded PPR over one projection, reindexed to every chunk.

    Chunks absent from the projection score 0.0 — on the ablated graph that is
    the point, not an artifact: a chunk with no surviving tag is unreachable.
    """
    frame = gds().pageRank.stream(
        gds().graph.get(graph_name),
        sourceNodes=[[int(n), float(w)] for n, w in weighted_seeds],
        dampingFactor=config.damping_factor,
        maxIterations=config.max_iterations,
        tolerance=config.tolerance,
        relationshipWeightProperty="weight",
    )
    scores = frame.set_index("nodeId")["score"]
    return scores.reindex(pd.Index(all_chunk_node_ids())).fillna(0.0)


def rank_of(scores: pd.Series, node_id: int) -> str:
    """Corpus-wide rank (1 = best); '—' when the walk never reaches it."""
    s = float(scores.get(node_id, 0.0))
    if s <= 0.0:
        return "—"
    return str(1 + int((scores > s).sum()))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--only", help="run a single question id")
    parser.add_argument(
        "--keep-graphs",
        action="store_true",
        help="leave the ablated projections in the GDS catalog",
    )
    parser.add_argument(
        "--generous",
        action="store_true",
        help="also keep the hand-audited GAZETTEER_AUDIT edges (sensitivity run)",
    )
    args = parser.parse_args()

    bank = {e["id"]: e["question"] for e in yaml.safe_load(QUESTION_BANK.read_text())}
    questions = [q for q in ENDPOINTS if not args.only or q == args.only]
    if not questions:
        console.print(f"[red]no question with id {args.only!r}[/]")
        return 1

    config = ExpandConfig(entity_seeder="decomposed")

    # ── Classify and project ──────────────────────────────────────────────────
    console.print("[bold]Classifying MENTIONED_IN edges[/] (reusing "
                  "measure_extraction_grade's classifier"
                  + (", plus the hand-audited gazetteer gaps" if args.generous else "")
                  + ")…")
    survivors, info = classify_edges(generous=args.generous)
    n_total = info["total_edges"]
    n_kept = len(survivors)
    full_cov = info["chunks_with_edges_full"]
    abl_cov = info["chunks_with_edges_ablated"]
    n_chunks = total_chunks()
    console.print(
        f"  kept {n_kept}/{n_total} edges ({100 * n_kept / n_total:.1f}%) — "
        f"chunks with no entity edge: {n_chunks - len(full_cov)} full "
        f"({100 * (n_chunks - len(full_cov)) / n_chunks:.1f}%) → "
        f"{n_chunks - len(abl_cov)} ablated "
        f"({100 * (n_chunks - len(abl_cov)) / n_chunks:.1f}%)"
    )

    project_mentions()  # the full-graph baseline, idempotent
    project_ablated(survivors, with_next=False)
    project_ablated(survivors, with_next=True)

    ablated_entity_nodes = {e for e, _ in survivors}
    ablated_edges_by_entity: dict[int, set[int]] = defaultdict(set)
    for eid, cid in survivors:
        ablated_edges_by_entity[eid].add(cid)

    chunk_node_id = {
        r["chunkId"]: r["nodeId"]
        for r in read_query(
            "MATCH (c:Chunk) RETURN c.chunkId AS chunkId, id(c) AS nodeId"
        )
    }

    try:
        for qid in questions:
            question = bank[qid]
            spec = ENDPOINTS[qid]
            endpoints = {**spec["judged"], **spec["receipts"]}
            console.print(f"\n[bold]{qid}[/] — {question}")

            # ── Seeds: the decomposed seeder, guarded against ablated absence ─
            seeds, _debug = decomposed_entity_seeds(question, config=config)
            kept_seeds, dropped_seeds = [], []
            for s in seeds:
                (kept_seeds if s.node_id in ablated_entity_nodes else dropped_seeds).append(s)
            for s in seeds:
                df_full = len(
                    read_query(
                        "MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE id(e)=$n "
                        "RETURN DISTINCT id(c) AS cid",
                        n=s.node_id,
                    )
                )
                df_abl = len(ablated_edges_by_entity.get(s.node_id, ()))
                gone = " [red](absent from ablated graph — not seeded there)[/]" \
                    if s.node_id not in ablated_entity_nodes else ""
                console.print(
                    f"  seed {s.name} ({s.label}, weight {s.weight:.3f}) "
                    f"df {df_full} → {df_abl} ablated{gone}"
                )

            # ── Arm 1: filter+cosine membership on ablated tags ───────────────
            filter_chunks: set[int] = set()
            for s in kept_seeds:
                filter_chunks |= ablated_edges_by_entity.get(s.node_id, set())
            cosine_rows = read_query(
                """
                CALL db.index.vector.queryNodes('chunk_embeddings', $k, $embedding)
                YIELD node AS c, score
                RETURN id(c) AS nodeId, score
                """,
                k=n_chunks,
                embedding=embed(question),
            )
            filtered_order = [
                r["nodeId"] for r in cosine_rows if r["nodeId"] in filter_chunks
            ]
            filter_rank = {n: i + 1 for i, n in enumerate(filtered_order)}

            # ── Arms 2 & 3 (+ full-graph reference walk) ─────────────────────
            weighted = [(s.node_id, s.weight) for s in seeds]
            weighted_abl = [(s.node_id, s.weight) for s in kept_seeds]
            scores_full = ppr_chunk_scores(settings().mentions_graph_name, weighted, config)
            scores_abl = ppr_chunk_scores(ABLATED, weighted_abl, config)
            scores_next = ppr_chunk_scores(ABLATED_NEXT, weighted_abl, config)

            table = Table(header_style="bold", show_lines=False)
            table.add_column("endpoint")
            table.add_column("seed edge")
            table.add_column("role")
            table.add_column("filter+cosine (ablated)")
            table.add_column("PPR full", justify="right")
            table.add_column("PPR ablated", justify="right")
            table.add_column("PPR ablated+NEXT", justify="right")

            seed_eids = [s.node_id for s in seeds]
            for cid, desc in endpoints.items():
                node = chunk_node_id[cid]
                cls = next(
                    (
                        info["edge_class"][(e, node)]
                        for e in seed_eids
                        if (e, node) in info["edge_class"]
                    ),
                    "no edge",
                )
                role = "control" if cls == "name-backed" else "TEST"
                if cid in spec["receipts"]:
                    role += " (receipt)"
                membership = (
                    f"in filter, rank {filter_rank[node]}/{len(filtered_order)}"
                    if node in filter_chunks
                    else "[red]LOST by construction[/]"
                )
                table.add_row(
                    desc,
                    cls,
                    role,
                    membership,
                    rank_of(scores_full, node),
                    rank_of(scores_abl, node),
                    rank_of(scores_next, node),
                )
            console.print(table)
    finally:
        if not args.keep_graphs:
            drop_graph(ABLATED)
            drop_graph(ABLATED_NEXT)

    console.print(
        "\n[dim]Ranks are corpus-wide (2,913 chunks) under pure entity-seeded PPR "
        "score — no cosine blend, no top-k threshold. 'PPR full' is the same seed "
        "set walking the unablated lc-mentions graph. The bound stands either "
        "way: the walk cannot recover a passage whose entities were never tagged "
        "(limit #3), nor the zero-entity chunks (6.1% full, more ablated).[/]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

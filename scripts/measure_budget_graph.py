#!/usr/bin/env python3
"""Measure the budget graph as it stands: filter+cosine vs. entity-seeded PPR.

    NEO4J_DATABASE=budgetluna python scripts/measure_budget_graph.py
    NEO4J_DATABASE=neo4j      python scripts/measure_budget_graph.py   # gold reference
    python scripts/measure_budget_graph.py --only sacagawea-interpreting
    python scripts/measure_budget_graph.py --oracle-shards      # seed every audited shard
    python scripts/measure_budget_graph.py --vector-margin 0.10 # automatic shard discovery

Finding 5i simulated NER-grade extraction by ablating the gold graph's edges.
Nathan's correction: the graph most teams have is not NER output — it is what
``budgetluna`` is. That database is a copy of ``rawluna`` (the gpt-5.6-luna
extraction, frozen for section 4's measurements) with entity full-text and
vector indexes added and **the resolution pass skipped**: a modern LLM
extraction, shipped as-is. No edges are deleted here; the graph is measured as
it stands, on whatever database ``NEO4J_DATABASE`` selects. Run it against
``neo4j`` and it reproduces 5i's full-graph reference column — same seeds,
same walk, same rank arithmetic.

What "no resolution pass" actually looks like (recon that motivated the runs):
the LLM resolved pronouns *within* its context window, but where the journals
never name the person it minted **vague nodes** — Nov-4's coreference is a
Person literally named ``ONE OF HIS WIVES``; Aug-14 has ``HIS WOMAN`` and
``OUR INTERPRETER``; her fever passage tags no person at all. The identity is
shattered across SACAGAWEA (df 8), INDIAN WOMAN (df 24), THE INDIAN WOMAN,
spelling twins (SAHKAHGAR WE, SAH CAH GAH WE, SAHCAH GAHWEAH, JANEY)… — and
because those shards have *different name strings*, the decomposed seeder's
exact-name twin union (5f's duplicate rescue) cannot fire. Named men are fine:
TOUSSAINT CHARBONNEAU df 55, JOHN ORDWAY df 79.

Same arms and discipline as ``measure_ablation.py`` (endpoints are the 5d/5f
hand-read passages plus the 5h-1 receipts; ranks, never top-k, per
5d-quinquies): filter+cosine membership, pure entity-seeded PPR rank
corpus-wide, and the same walk with NEXT_CHUNK added. Projections are
in-memory, in this database's own GDS catalog; ``--keep-graphs`` retains them.

This script's own output is the write-up -- run it to see the numbers.
"""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
import yaml
from rich.console import Console
from rich.table import Table

from measure_ablation import ENDPOINTS, ppr_chunk_scores, rank_of
from graphrank.config import gds, read_query, settings
from graphrank.embedding import embed
from graphrank.pagerank import ExpandConfig, decomposed_entity_seeds
from graphrank.projection import (
    drop_graph,
    graph_exists,
    project_mentions,
    total_chunks,
)

console = Console()
QUESTION_BANK = _bootstrap.ROOT / "questions" / "questions.yaml"

# ── Oracle shards (hand-audited 2026-09-07) ───────────────────────────────────
#
# The single-node seeding above measures what the *seeder* can find. These
# lists measure what the *walk* could do if query-time entity resolution were
# solved: every budgetluna Person shard of the entity, audited by purity —
# the share of the shard's chunks that are gold-graph chunks of the resolved
# entity (cross-database join on chunkId; kept at purity >= 0.5). This is an
# oracle by construction: purity is computed against the gold graph, which a
# real budget-path system does not have.
#
# Two shards fail the cut and are worth knowing about: INDIAN WOMAN (df 24,
# purity 0.42) and SQUAR (df 7, purity 0.43) — the corpus's biggest shards of
# her are themselves contaminated, because the journals use those phrases for
# other women too. The bridge-node problem (section 4, 3d) at the extraction
# layer.
ORACLE_SHARDS: dict[str, list[str]] = {
    "sacagawea-interpreting": [
        "SACAGAWEA",                        # df 8, purity 1.00
        "INTERPRETER",                      # df 3, purity 0.67
        "THE INDIAN WOMAN",                 # df 3, purity 0.67
        "THE SQUAR",                        # df 3, purity 0.67
        "OUR INTERPRETER",                  # df 2, purity 1.00
        "THE INTERPRETER",                  # df 2, purity 0.50
        "HIS WIFE",                         # df 2, purity 1.00
        "INTERPRETERS WIFE",                # df 2, purity 1.00
        "ONE OF HIS WIVES",                 # df 1 — Nov-4's tag
        "SAHKAHGAR WE",                     # df 1
        "OUR INTERPRETER THE SNAKE WOMAN",  # df 1
        "HIS WOMAN",                        # df 1 — Aug-14's tag
        "THE WIFE OF SHABONO",              # df 1
        "SQUARWIFE",                        # df 1
        "JANEY",                            # df 1
        "SAHCAH GAHWEAH",                   # df 1
        "SNAKE INDIAN WIFE",                # df 1
    ],
}

#: Owned by this script — the configured mentions projection plus NEXT_CHUNK,
#: mirroring projection.py's IDF weighting. Never the configured names.
PLUS_NEXT = "lc-mentions-plus-next"

PLUS_NEXT_QUERY = """
CALL {
    MATCH (e)-[:MENTIONED_IN]->(seen:Chunk)
    WHERE NOT e:Chunk AND NOT e:GenericLocation
    WITH e, count(DISTINCT seen) AS df
    MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
    WITH DISTINCT e, c, df
    RETURN e AS source, c AS target, 'MENTIONS' AS relType,
           log(1.0 + toFloat($totalChunks) / df) AS weight
    UNION ALL
    MATCH (c1:Chunk)-[:NEXT_CHUNK]->(c2:Chunk)
    RETURN c1 AS source, c2 AS target,
           'NEXT_CHUNK' AS relType, $nextWeight AS weight
}
RETURN gds.graph.project(
    $graphName, source, target,
    {
        sourceNodeLabels: labels(source),
        targetNodeLabels: labels(target),
        relationshipType: relType,
        relationshipProperties: {weight: weight}
    },
    {undirectedRelationshipTypes: ['MENTIONS', 'NEXT_CHUNK']}
)
"""


def shard_seeds(names: list[str]) -> list:
    """Seeds for an audited shard list, df-proportional — 5f's identity: this
    mixture walks exactly as the one merged node would, to first hop."""
    from graphrank.pagerank import Seed

    rows = read_query(
        """
        UNWIND $names AS name
        MATCH (e) WHERE coalesce(e.canonicalName, e.name) = name
          AND NOT e:Chunk AND NOT e:GenericLocation
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        RETURN id(e) AS nodeId, coalesce(e.canonicalName, e.name) AS name,
               head(labels(e)) AS label, count(DISTINCT c) AS df
        """,
        names=names,
    )
    total = sum(r["df"] for r in rows) or 1
    return [
        Seed(node_id=r["nodeId"], name=r["name"], label=r["label"],
             match_score=1.0, weight=r["df"] / total)
        for r in rows
    ]


def widen_with_vector(seeds: list, mentions: list[dict], margin: float) -> list:
    """Automatic shard discovery: union each mention's vector candidates within
    ``margin`` of its top hit into the seed set, df-proportional over the union.

    The honest version of "just widen the net": whatever the margin admits is
    seeded, wrong-person shards included — no oracle filters them.
    """
    from graphrank.pagerank import Seed

    existing = {row["name"] for row in read_query("SHOW VECTOR INDEXES YIELD name RETURN name")}
    union: dict[int, dict] = {
        s.node_id: {"name": s.name, "label": s.label} for s in seeds
    }
    for m in mentions:
        index = f"{m['label'].lower().replace(' ', '')}_embeddings"
        if index not in existing:
            continue
        rows = read_query(
            """
            CALL db.index.vector.queryNodes($index, 15, $embedding)
            YIELD node, score
            WHERE NOT node:Chunk AND NOT node:GenericLocation
            RETURN id(node) AS nodeId, coalesce(node.canonicalName, node.name) AS name,
                   head(labels(node)) AS label, score
            """,
            index=index,
            embedding=embed(m["phrase"]),
        )
        if not rows:
            continue
        top = max(r["score"] for r in rows)
        for r in rows:
            if r["score"] >= top - margin:
                union.setdefault(r["nodeId"], {"name": r["name"], "label": r["label"]})

    df = {
        r["nodeId"]: r["df"]
        for r in read_query(
            """
            UNWIND $ids AS nid
            MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE id(e) = nid
            RETURN nid AS nodeId, count(DISTINCT c) AS df
            """,
            ids=list(union),
        )
    }
    total = sum(df.get(n, 0) for n in union) or 1
    return [
        Seed(node_id=n, name=meta["name"], label=meta["label"],
             match_score=1.0, weight=df.get(n, 0) / total)
        for n, meta in union.items()
        if df.get(n, 0) > 0
    ]


def project_plus_next() -> None:
    if graph_exists(PLUS_NEXT):
        drop_graph(PLUS_NEXT)
    graph, _ = gds().graph.cypher.project(
        PLUS_NEXT_QUERY,
        graphName=PLUS_NEXT,
        totalChunks=total_chunks(),
        nextWeight=settings().next_chunk_weight,
    )
    console.print(
        f"  projected [bold]{PLUS_NEXT}[/]: {graph.node_count()} nodes, "
        f"{graph.relationship_count()} relationships"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--only", help="run a single question id")
    parser.add_argument(
        "--keep-graphs",
        action="store_true",
        help="leave the plus-NEXT projection in the GDS catalog",
    )
    parser.add_argument(
        "--oracle-shards",
        action="store_true",
        help="seed every audited identity shard (ORACLE_SHARDS) instead of the "
             "seeder's resolution — the upper bound on query-time seeding",
    )
    parser.add_argument(
        "--vector-margin",
        type=float,
        default=0.0,
        help="automatic shard discovery: union each mention's vector candidates "
             "within this margin of its top hit into the seed set (try 0.10)",
    )
    args = parser.parse_args()

    cfg = settings()
    console.print(
        f"[bold]Measuring database {cfg.neo4j_database!r} as it stands[/] "
        f"(no ablation — this graph IS the condition)"
    )

    bank = {e["id"]: e["question"] for e in yaml.safe_load(QUESTION_BANK.read_text())}
    questions = [q for q in ENDPOINTS if not args.only or q == args.only]
    if not questions:
        console.print(f"[red]no question with id {args.only!r}[/]")
        return 1

    config = ExpandConfig(entity_seeder="decomposed")
    n_chunks = total_chunks()

    stats = project_mentions()
    console.print(
        f"  projected [bold]{stats.name}[/]: {stats.node_count} nodes, "
        f"{stats.relationship_count} relationships"
    )
    project_plus_next()

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

            seeds, debug = decomposed_entity_seeds(question, config=config)
            if args.oracle_shards and qid in ORACLE_SHARDS:
                seeds = shard_seeds(ORACLE_SHARDS[qid])
                console.print(
                    f"  [yellow]oracle-shard seeding[/] — {len(seeds)} audited shards"
                )
            elif args.vector_margin > 0:
                seeds = widen_with_vector(seeds, debug["mentions"], args.vector_margin)
                console.print(
                    f"  [yellow]vector-margin {args.vector_margin} widening[/] — "
                    f"{len(seeds)} seeds after union"
                )
            for m in debug["mentions"]:
                resolved = ", ".join(m["resolved_to"]) or "∅"
                console.print(
                    f"  mention {m['phrase']!r} → {resolved} ({m['via']})"
                )
            seed_ids = [s.node_id for s in seeds]
            df = {
                r["nodeId"]: r["df"]
                for r in read_query(
                    """
                    UNWIND $ids AS nid
                    MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE id(e) = nid
                    RETURN nid AS nodeId, count(DISTINCT c) AS df
                    """,
                    ids=seed_ids,
                )
            }
            for s in seeds:
                console.print(
                    f"  seed {s.name} ({s.label}, weight {s.weight:.3f}) "
                    f"df {df.get(s.node_id, 0)}"
                )

            # The tag filter: every chunk carrying a mention edge from a seed.
            filter_chunks = {
                r["nodeId"]
                for r in read_query(
                    """
                    UNWIND $ids AS nid
                    MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE id(e) = nid
                    RETURN DISTINCT id(c) AS nodeId
                    """,
                    ids=seed_ids,
                )
            }
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

            weighted = [(s.node_id, s.weight) for s in seeds]
            scores = ppr_chunk_scores(cfg.mentions_graph_name, weighted, config)
            scores_next = ppr_chunk_scores(PLUS_NEXT, weighted, config)

            table = Table(header_style="bold", show_lines=False)
            table.add_column("endpoint")
            table.add_column("seed tag")
            table.add_column("filter+cosine")
            table.add_column("PPR", justify="right")
            table.add_column("PPR +NEXT", justify="right")

            for cid, desc in endpoints.items():
                node = chunk_node_id[cid]
                tagged = node in filter_chunks
                membership = (
                    f"in filter, rank {filter_rank[node]}/{len(filtered_order)}"
                    if tagged
                    else "[red]LOST — no tag[/]"
                )
                label = "tagged" if tagged else "[red]untagged[/]"
                if cid in spec["receipts"]:
                    label += " (receipt)"
                table.add_row(
                    desc, label, membership,
                    rank_of(scores, node), rank_of(scores_next, node),
                )
            console.print(table)
    finally:
        if not args.keep_graphs:
            drop_graph(PLUS_NEXT)

    console.print(
        f"\n[dim]Ranks are corpus-wide ({n_chunks} chunks) under pure entity-seeded "
        "PPR score — no cosine blend, no top-k threshold. Endpoints and the walk "
        "machinery are identical to measure_ablation.py; only the graph differs.[/]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

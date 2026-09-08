#!/usr/bin/env python3
"""Neighborhood questions: the answer entity's name is the thing the asker lacks.

    NEO4J_DATABASE=lewisclark python scripts/measure_neighborhood.py
    NEO4J_DATABASE=lewisclark python scripts/measure_neighborhood.py --delete-test

Class 1 of the post-5g screen (5h-4's candidate, finally measured): questions
like "what do we know about Sacagawea's brother?" where the entity whose
chunks hold the answer — CAMEAHWAIT — is precisely what the asker doesn't
know. The resolvable mention (SACAGAWEA) supports a filter, but the filter
excludes the answer population *by construction*: only 2 of Cameahwait's 16
chunks co-mention his sister. The walk's claim is that those 2 bridge chunks
carry restart mass from the anchor across to the satellite's exclusive chunks.

Second case, `wallawalla-chief`: "which chief hosted the expedition among the
Walla Walla on the return?" — Yelleppit, whose 8 chunks are split across two
spelling shards (Clark writes Yelleppit, Lewis writes Yellept). The resolvable
mention is the *nation*, and the nation is itself shattered into a dozen
df-1..3 spelling shards, 4 of the 8 answer chunks carrying no nation tag at
all — so even an oracle OR-filter over every shard is blind to half the
answer. 5k's spelling-shard finding and Class 1 meet in one question.

Measurements are population-level, the 5e/5k form: the target population is
tag-defined (every chunk the satellite nodes are MENTIONED_IN — all of them
read and confirmed substantive for the flagship cases before this script was
written), and we report each target chunk's corpus rank plus subset medians
under: cosine; filter+cosine on the resolved mention (with the coverage
receipt); pure entity-seeded PPR from the resolved nodes (df-proportional —
5f's merged-node identity); and the 0.6/0.4 blend. Resolution uses the
decomposed seeder's deterministic full-text path (`resolve_mention`) — the
LLM step would only emit the phrase, so it is bypassed, same as 5k.

``--delete-test`` reruns the flagship walk on a projection with the 2 bridge
chunks removed: if the satellite chunks' ranks crater, the bridge — not some
diffuse similarity — is the mechanism.

Results and their reading live in ``docs/talk-outline.md``, finding 5m.
"""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
import pandas as pd
from rich.console import Console
from rich.table import Table

from graphrank.config import gds, read_query, settings
from graphrank.decompose import Mention, resolve_mention
from graphrank.embedding import embed
from graphrank.pagerank import ExpandConfig, batched_pagerank, _percentile
from graphrank.projection import (
    MENTIONS_PROJECTION_QUERY,
    MENTION_WEIGHTS,
    all_chunk_node_ids,
    graph_exists,
    mentions_membership,
    project_mentions,
    total_chunks,
)

console = Console()

CASES = {
    "sacagawea-brother": {
        "question": "What do we know about Sacagawea's brother?",
        #: What the decomposed seeder can resolve from the question. The
        #: satellite's name is deliberately NOT here — not knowing it is the case.
        "mention": Mention(phrase="Sacagawea", label="Person"),
        "satellites": ["Cameahwait"],
        #: The reunion passage — the one chunk that states the relation.
        "key_chunk": "dd08cca00b6da427",
    },
    "wallawalla-chief": {
        "question": "Which chief hosted the expedition among the Walla Walla on their return journey, and what did he do for them?",
        "mention": Mention(phrase="Walla Walla", label="NativeNation"),
        "satellites": ["Yelleppit", "Yellept"],
        #: The white-horse gift, Lewis's entry.
        "key_chunk": "e81755a8a87a8443",
    },
}

ABLATION_GRAPH = "lc-mentions-nobridge"


def corpus_ranks(scores: pd.Series) -> pd.Series:
    """Rank 1 = best; zero-score chunks share the worst ranks (method='min')."""
    return scores.rank(ascending=False, method="min")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--delete-test", action="store_true",
                        help="rerun the flagship walk with the bridge chunks removed")
    args = parser.parse_args()

    console.print(f"[bold]Neighborhood measurement on '{settings().neo4j_database}'[/bold]")
    project_mentions()
    config = ExpandConfig()
    chunk_index = pd.Index(all_chunk_node_ids())
    in_graph = mentions_membership()

    for qid, case in CASES.items():
        console.rule(f"[bold]{qid}[/bold]")
        console.print(f"[italic]{case['question']}[/italic]")

        # ── target population: every chunk the satellite is mentioned in ─────
        targets = read_query(
            """
            UNWIND $names AS name
            MATCH (s {name: name})-[:MENTIONED_IN]->(c:Chunk)
            RETURN DISTINCT id(c) AS nodeId, c.chunkId AS chunkId,
                   toString(c.date) AS date
            ORDER BY date
            """,
            names=case["satellites"],
        )

        # ── what the question can actually resolve (deterministic path) ──────
        resolved = resolve_mention(case["mention"], in_graph=in_graph)
        seeds = [
            (c["nodeId"], float(max(c.get("df", 1), 1))) for c in resolved.candidates
        ]
        console.print(
            f"'{case['mention'].phrase}' resolves via {resolved.via} to: "
            + " · ".join(f"{c['name']} (df {c.get('df', '?')})" for c in resolved.candidates)
        )

        # ── the filter's reach: chunks tagged by ANY resolved node ────────────
        filter_rows = read_query(
            """
            UNWIND $ids AS nid
            MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE id(e) = nid
            RETURN DISTINCT id(c) AS nodeId
            """,
            ids=[n for n, _ in seeds],
        )
        filter_set = {r["nodeId"] for r in filter_rows}
        target_ids = [t["nodeId"] for t in targets]
        covered = [t for t in targets if t["nodeId"] in filter_set]
        console.print(
            f"targets: {len(targets)} chunks · filter (all resolved tags, "
            f"{len(filter_set)} chunks) covers [bold]{len(covered)}/{len(targets)}[/bold]"
            f" — the rest are excluded by construction"
        )

        # ── signals ───────────────────────────────────────────────────────────
        rows = read_query(
            """
            CALL db.index.vector.queryNodes('chunk_embeddings', $k, $embedding)
            YIELD node AS c, score
            RETURN id(c) AS nodeId, score
            """,
            k=len(chunk_index), embedding=embed(case["question"]),
        )
        cosine = pd.Series({r["nodeId"]: r["score"] for r in rows}).reindex(chunk_index).fillna(0.0)
        walk = batched_pagerank(seeds, config=config).reindex(chunk_index).fillna(0.0)
        blend = 0.6 * _percentile(cosine) + 0.4 * _percentile(walk)

        r_cos, r_walk, r_blend = map(corpus_ranks, (cosine, walk, blend))
        # filtered cosine: rank targets within the filter's chunk set only
        f_cos = cosine[cosine.index.isin(filter_set)]
        r_fcos = corpus_ranks(f_cos)

        table = Table(title=f"{qid} — corpus rank of every target chunk (of {len(chunk_index)})")
        for col in ("chunk", "date", "in filter?", "filter+cos", "cosine", "walk", "blend"):
            table.add_column(col, justify="right" if col not in ("chunk", "date") else "left")
        for t in targets:
            n = t["nodeId"]
            key = " ◀ key" if t["chunkId"] == case["key_chunk"] else ""
            table.add_row(
                t["chunkId"][:8] + key,
                t["date"] or "?",
                "yes" if n in filter_set else "[red]NO[/red]",
                str(int(r_fcos[n])) if n in filter_set else "—",
                str(int(r_cos[n])),
                str(int(r_walk[n])),
                str(int(r_blend[n])),
            )
        console.print(table)

        blind = [t["nodeId"] for t in targets if t["nodeId"] not in filter_set]
        for name, ranks in (
            ("all targets", [r_cos, r_walk, r_blend]),
            ("filter-blind targets", None),
        ):
            ids = target_ids if name == "all targets" else blind
            med = lambda r: int(r[ids].median())  # noqa: E731
            console.print(
                f"  median rank, {name} (n={len(ids)}): "
                f"cosine {med(r_cos)} · walk {med(r_walk)} · blend {med(r_blend)}"
            )
        top8 = {
            "cosine": set(r_cos[r_cos <= 8].index),
            "blend": set(r_blend[r_blend <= 8].index),
        }
        for sname, ids in top8.items():
            hits = [t["chunkId"][:8] for t in targets if t["nodeId"] in ids]
            console.print(f"  {sname} top-8 holds {len(hits)} target(s): {hits}")

        # ── delete-test: sever the bridge, rerun the walk ─────────────────────
        if args.delete_test and qid == "sacagawea-brother":
            bridge_ids = [t["chunkId"] for t in covered]
            console.print(f"\n[bold]delete-test[/bold]: removing bridge chunks {bridge_ids}")
            if graph_exists(ABLATION_GRAPH):
                gds().graph.get(ABLATION_GRAPH).drop()
            q = MENTIONS_PROJECTION_QUERY.replace(
                "MATCH (e)-[:MENTIONED_IN]->(c:Chunk)\nWITH DISTINCT e, c, df",
                "MATCH (e)-[:MENTIONED_IN]->(c:Chunk)\n"
                "WHERE NOT c.chunkId IN $excluded\nWITH DISTINCT e, c, df",
            ).replace("__WEIGHT__", MENTION_WEIGHTS[settings().mention_weight])
            graph, _ = gds().graph.cypher.project(
                q, graphName=ABLATION_GRAPH, totalChunks=total_chunks(),
                excluded=bridge_ids,
            )
            frame = gds().pageRank.stream(
                graph,
                sourceNodes=[[int(n), float(w)] for n, w in seeds],
                dampingFactor=config.damping_factor,
                maxIterations=config.max_iterations,
                tolerance=config.tolerance,
                relationshipWeightProperty="weight",
            )
            walk_ablated = (
                frame.set_index("nodeId")["score"].reindex(chunk_index).fillna(0.0)
            )
            r_abl = corpus_ranks(walk_ablated)
            console.print("  walk rank, bridge intact → bridge removed (filter-blind targets):")
            for t in targets:
                if t["nodeId"] in blind:
                    console.print(
                        f"    {t['chunkId'][:8]} {t['date']}: "
                        f"{int(r_walk[t['nodeId']])} → {int(r_abl[t['nodeId']])}"
                    )
            console.print(
                f"  median: {int(r_walk[blind].median())} → {int(r_abl[blind].median())}"
            )
            gds().graph.get(ABLATION_GRAPH).drop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

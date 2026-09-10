#!/usr/bin/env python3
"""Bridge decay: how the walk's reach into a neighbor falls with anchor degree.

    NEO4J_DATABASE=lewisclark python scripts/measure_bridge_decay.py
    NEO4J_DATABASE=lewisclark python scripts/measure_bridge_decay.py --per-bin 60

Finding 5m ended on a two-point contrast: seeded at a df-3 anchor the walk
crossed to a satellite's exclusive chunks and won (median rank 16); seeded at
a df-85 anchor the bridge carried ~2% of first-hop mass and nothing reached a
top-8. Nathan's proposed agent rule generalizes it: **resolve the question's
mentions, count their chunk degree, and route — low-df seeds justify
expansion, high-df seeds say filter and stop.** Degree is one COUNT after
resolution, observable before any retrieval runs; the *bridge* fraction is
not observable (the satellite is the unknown), so df is the whole signal an
agent gets a priori.

This script turns the two points into a curve, with no relevance judgements:
for every (anchor, satellite) co-mention pair in the graph — satellite df
4..30 with at least 3 chunks the anchor does not share — run single-seed PPR
from the anchor and record the **median corpus rank of the satellite's
exclusive chunks** (tag-defined populations, the 5e/5k mass form). Pairs are
grouped by anchor degree; anchors are stratum-sampled deterministically.

What the curve does and does not claim: it measures the walk's *crossing
capacity* — how discoverable a neighbor's unshared chunks are from an anchor
seed — as a function of anchor degree. It says nothing about beating cosine
on any particular question (that needs questions and reads; 5m did two).

This script's own output is the write-up -- run it to see the numbers.
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import defaultdict
from pathlib import Path

import _bootstrap  # noqa: F401
import pandas as pd
from rich.console import Console
from rich.table import Table

from graphrank.config import read_query, settings
from graphrank.pagerank import ExpandConfig, batched_pagerank
from graphrank.projection import all_chunk_node_ids, project_mentions

console = Console()

BINS = [(2, 5), (6, 15), (16, 40), (41, 100), (101, 300), (301, 10**9)]


def bin_label(df: int) -> str:
    for lo, hi in BINS:
        if lo <= df <= hi:
            return f"{lo}-{hi}" if hi < 10**9 else f"{lo}+"
    return "<2"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--per-bin", type=int, default=100,
                        help="max anchors sampled per degree bin (default 100)")
    parser.add_argument("--seed", type=int, default=1805, help="sampling seed")
    args = parser.parse_args()

    console.print(f"[bold]Bridge decay on '{settings().neo4j_database}'[/bold]")
    project_mentions()
    config = ExpandConfig()
    chunk_index = pd.Index(all_chunk_node_ids())

    pairs = read_query(
        """
        MATCH (a)-[:MENTIONED_IN]->(ch:Chunk)
        WHERE NOT a:Chunk AND NOT a:GenericLocation
        WITH a, count(DISTINCT ch) AS df_a
        WHERE df_a >= 2
        MATCH (a)-[:MENTIONED_IN]->(shared:Chunk)<-[:MENTIONED_IN]-(s)
        WHERE s <> a AND NOT s:Chunk AND NOT s:GenericLocation
        WITH a, df_a, s, count(DISTINCT shared) AS shared
        MATCH (s)-[:MENTIONED_IN]->(sc:Chunk)
        WITH a, df_a, s, shared, count(DISTINCT sc) AS df_s
        WHERE df_s >= 4 AND df_s <= 30 AND df_s - shared >= 3
        RETURN id(a) AS anchor_id,
               coalesce(a.canonicalName, a.name) AS anchor,
               head(labels(a)) AS anchor_label,
               df_a, shared,
               id(s) AS satellite_id,
               coalesce(s.canonicalName, s.name) AS satellite,
               df_s
        """,
    )
    console.print(f"[dim]{len(pairs)} pairs, {len({p['anchor_id'] for p in pairs})} anchors[/dim]")

    by_anchor: dict[int, list[dict]] = defaultdict(list)
    for p in pairs:
        by_anchor[p["anchor_id"]].append(p)

    # deterministic stratum sample of anchors per degree bin
    strata: dict[str, list[int]] = defaultdict(list)
    for aid, plist in sorted(by_anchor.items()):
        strata[bin_label(plist[0]["df_a"])].append(aid)
    rng = random.Random(args.seed)
    keep: set[int] = set()
    for label, aids in strata.items():
        keep.update(rng.sample(aids, min(args.per_bin, len(aids))))

    rows_out: list[dict] = []
    for i, aid in enumerate(sorted(keep)):
        anchor_chunks = {
            r["nodeId"]
            for r in read_query(
                "MATCH (a)-[:MENTIONED_IN]->(c:Chunk) WHERE id(a) = $aid "
                "RETURN DISTINCT id(c) AS nodeId", aid=aid,
            )
        }
        sat_chunks = {
            r["sid"]: r["chunks"]
            for r in read_query(
                """
                UNWIND $sids AS sid
                MATCH (s)-[:MENTIONED_IN]->(c:Chunk) WHERE id(s) = sid
                RETURN sid, collect(DISTINCT id(c)) AS chunks
                """,
                sids=[p["satellite_id"] for p in by_anchor[aid]],
            )
        }
        walk = batched_pagerank([aid], config=config).reindex(chunk_index).fillna(0.0)
        ranks = walk.rank(ascending=False, method="min")
        for p in by_anchor[aid]:
            ex = [c for c in sat_chunks.get(p["satellite_id"], [])
                  if c not in anchor_chunks and c in ranks.index]
            if len(ex) < 3:
                continue
            rows_out.append({
                "anchor": p["anchor"], "anchor_label": p["anchor_label"],
                "df_a": p["df_a"], "satellite": p["satellite"], "df_s": p["df_s"],
                "shared": p["shared"],
                "bridge_frac": round(p["shared"] / p["df_a"], 4),
                "median_rank": int(ranks[ex].median()),
            })
        if (i + 1) % 100 == 0:
            console.print(f"[dim]  {i + 1}/{len(keep)} anchors[/dim]")

    frame = pd.DataFrame(rows_out)
    out = Path(__file__).resolve().parent.parent / "results" / f"bridge-decay-{settings().neo4j_database}.csv"
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)

    table = Table(title="median walk-rank of the satellite's exclusive chunks, by anchor degree")
    for col in ("anchor df", "pairs", "median of medians", "% pairs ≤50", "% pairs ≤100", "median bridge frac"):
        table.add_column(col, justify="right")
    frame["bin"] = frame["df_a"].map(bin_label)
    order = [f"{lo}-{hi}" if hi < 10**9 else f"{lo}+" for lo, hi in BINS]
    for label in order:
        sub = frame[frame["bin"] == label]
        if sub.empty:
            continue
        table.add_row(
            label, str(len(sub)),
            str(int(sub["median_rank"].median())),
            f"{(sub['median_rank'] <= 50).mean():.0%}",
            f"{(sub['median_rank'] <= 100).mean():.0%}",
            f"{sub['bridge_frac'].median():.3f}",
        )
    console.print(table)

    # the mechanism view: bridge fraction, not raw degree
    table2 = Table(title="same pairs, by bridge fraction (shared/df_a) — NOT observable a priori")
    for col in ("bridge frac", "pairs", "median of medians", "% pairs ≤50"):
        table2.add_column(col, justify="right")
    edges = [0, 0.02, 0.05, 0.1, 0.2, 0.5, 1.01]
    for lo, hi in zip(edges, edges[1:]):
        sub = frame[(frame["bridge_frac"] >= lo) & (frame["bridge_frac"] < hi)]
        if sub.empty:
            continue
        table2.add_row(
            f"{lo:.2f}–{hi:.2f}", str(len(sub)),
            str(int(sub["median_rank"].median())),
            f"{(sub['median_rank'] <= 50).mean():.0%}",
        )
    console.print(table2)
    console.print(f"[bold]per-pair data written to {out}[/bold]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

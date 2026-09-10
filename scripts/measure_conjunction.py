#!/usr/bin/env python3
"""Multi-seed conjunction: what the walk can and cannot lift into the window.

    NEO4J_DATABASE=lewisclark python scripts/measure_conjunction.py
    NEO4J_DATABASE=lewisclark python scripts/measure_conjunction.py --neither-sweep
    NEO4J_DATABASE=lewisclark python scripts/measure_conjunction.py --seed-bias

Three measurements behind outline finding 5p (2026-09-09), testing the
intuition "seed the parts of the graph the question is about and the passages
central to that mix should rank well — even ones that never mention a seed."

Default mode — per seed pair, PPR from A, B, and A+B over `lc-mentions`
(idf, d=0.45): the combined top-20 with mention flags and per-seed mass
split. Result: both-mention chunks jump from single-seed ranks 9–122 to
combined ranks 1–9; chunks mentioning NEITHER seed never appear.

--neither-sweep — where does the first neither-chunk rank, across
damping {0.45, 0.85} x projection {mentions-only, mentions+RELATED}? Result:
rank 76–368, never top-50. On a bipartite mentions graph a neither-chunk is
>=3 hops out and mass-capped; extracted entity-entity edges (weight 1.0,
undirected) barely move it. Entity-seeded walks do conjunction, not depth —
indirect elevation is real only from *passage* seeds (distance parity: a
passage seed's nearest non-seed chunks are the 2-hop co-mention chunks,
which is slide 5.12's buttons mechanism).

--seed-bias — limit 1 of 5.10 ("it combines evidence — but you don't choose
the weights"): per-chunk contribution goes as bias/df, so a hub seed is
nearly free to ignore. Restart bias by sqrt(df) is the measured compromise:
both-mention chunks fill the top-8 (5->8 of 8 for LEWIS 825 + CYNOMYS 42)
while the rare seed's solo chunks hold their ranks (median 29 both schemes).
Full df-proportional bias buys the arithmetic 2x bonus (1.04x -> 1.89x) but
demotes the rare seed's own chunks to hub-level noise (median 29 -> 441) —
the conjunction is bought by destroying the rare entity's solo signal.
"""

from __future__ import annotations

import argparse
import math

import _bootstrap  # noqa: F401
import pandas as pd

from graphrank.config import gds, read_query, settings
from graphrank.pagerank import ExpandConfig
from graphrank.projection import all_chunk_node_ids, total_chunks

PAIRS = [
    ("TOUSSAINT CHARBONNEAU", "SHOSHONE"),   # bridge: SACAGAWEA
    ("SACAGAWEA", "HIDATSA"),                # bridge: CHARBONNEAU
    ("SACAGAWEA", "SHOSHONE"),               # benchmark shoshone-horses
    ("FORT MANDAN", "SHOSHONE"),             # the hiring neighbourhood
    ("CHARLES FLOYD", "MISSOURI RIVER"),     # the known direct-conjunction pair
]

BIAS_PAIRS = [
    ("MERIWETHER LEWIS", "CYNOMYS LUDOVICIANUS"),  # 5.10 limit 1's own example
    ("WILLIAM CLARK", "CAMEAHWAIT"),               # second hub+rare pair
]

TOP_N = 20

#: mentions + extracted entity-entity edges, undirected, RELATED weight 1.0 —
#: used only by --neither-sweep, projected fresh and dropped afterwards.
EXP_GRAPH = "exp-mentions-rel"
EXP_PROJECTION = """
CALL {
    MATCH (e)-[:MENTIONED_IN]->(seen:Chunk)
    WHERE NOT e:Chunk AND NOT e:GenericLocation
    WITH e, count(DISTINCT seen) AS df
    MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
    WITH DISTINCT e, c, df
    RETURN e AS source, c AS target, 'MENTIONS' AS relType,
           log(1.0 + toFloat($totalChunks) / df) AS weight
    UNION ALL
    MATCH (a)-[r]->(b)
    WHERE NOT a:Chunk AND NOT b:Chunk
      AND NOT a:GenericLocation AND NOT b:GenericLocation
      AND type(r) <> 'MENTIONED_IN'
    RETURN a AS source, b AS target, 'RELATED' AS relType, 1.0 AS weight
}
RETURN gds.graph.project(
    $graphName, source, target,
    {sourceNodeLabels: labels(source), targetNodeLabels: labels(target),
     relationshipType: relType, relationshipProperties: {weight: weight}},
    {undirectedRelationshipTypes: ['MENTIONS', 'RELATED']}
)
"""


def resolve(name: str) -> dict:
    rows = read_query(
        """
        MATCH (e) WHERE NOT e:Chunk AND NOT e:GenericLocation
          AND coalesce(e.canonicalName, e.name) = $name
        OPTIONAL MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        RETURN id(e) AS nodeId, coalesce(e.canonicalName, e.name) AS name,
               head(labels(e)) AS label, count(DISTINCT c) AS df
        ORDER BY df DESC
        """,
        name=name,
    )
    if not rows:
        raise SystemExit(f"no entity named {name!r}")
    if len(rows) > 1:
        print(f"  ! {name} resolves to {len(rows)} nodes, using df-max")
    return rows[0]


def mentioning(entity_ids: list[int]) -> set[int]:
    rows = read_query(
        "MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE id(e) IN $ids "
        "RETURN DISTINCT id(c) AS cid",
        ids=entity_ids,
    )
    return {r["cid"] for r in rows}


def ppr(graph, seeds, damping: float, chunk_index) -> pd.Series:
    """`seeds` is a flat id list or [[id, bias], ...] — GDS takes both."""
    frame = gds().pageRank.stream(
        graph,
        sourceNodes=seeds,
        dampingFactor=damping,
        maxIterations=40,
        tolerance=1e-8,
        relationshipWeightProperty="weight",
    )
    return frame.set_index("nodeId")["score"].reindex(chunk_index).fillna(0.0)


def chunk_meta(chunk_node_ids: list[int]) -> dict[int, dict]:
    rows = read_query(
        """
        MATCH (c:Chunk) WHERE id(c) IN $ids
        RETURN id(c) AS nodeId, c.chunkId AS chunkId, toString(c.date) AS date,
               left(c.text, 260) AS text
        """,
        ids=chunk_node_ids,
    )
    return {r["nodeId"]: r for r in rows}


def mentions_graph():
    return gds().graph.get(settings().mentions_graph_name)


# ── default mode: combined top-20 with mention flags ─────────────────────────


def conjunction_tables() -> None:
    cfg = ExpandConfig()  # documents the shipped operating point: d=0.45, idf
    chunk_index = pd.Index(all_chunk_node_ids())
    graph = mentions_graph()

    for name_a, name_b in PAIRS:
        a, b = resolve(name_a), resolve(name_b)
        print(f"\n{'=' * 96}\nPAIR: {a['name']} (df={a['df']})  +  {b['name']} (df={b['df']})")

        ppr_a = ppr(graph, [a["nodeId"]], cfg.damping_factor, chunk_index)
        ppr_b = ppr(graph, [b["nodeId"]], cfg.damping_factor, chunk_index)
        combined = ppr_a + ppr_b  # linearity: identical to one biased call

        rank_a = ppr_a.rank(ascending=False, method="min")
        rank_b = ppr_b.rank(ascending=False, method="min")
        rank_c = combined.rank(ascending=False, method="min")

        chunks_a, chunks_b = mentioning([a["nodeId"]]), mentioning([b["nodeId"]])
        top = list(combined.sort_values(ascending=False).head(TOP_N).index)
        meta = chunk_meta(top)

        n_neither = 0
        for pos, nid in enumerate(top, 1):
            in_a, in_b = nid in chunks_a, nid in chunks_b
            flag = "A+B" if in_a and in_b else "A" if in_a else "B" if in_b else "NEITHER"
            share_a = float(ppr_a[nid]) / (float(ppr_a[nid]) + float(ppr_b[nid]) + 1e-18)
            row = meta[nid]
            print(
                f"{pos:3d}. [{flag:>7}] {row['date']}  rank A-only={int(rank_a[nid]):>4} "
                f"B-only={int(rank_b[nid]):>4} A+B={int(rank_c[nid]):>4}  massA={share_a:.2f}"
            )
            if flag == "NEITHER":
                n_neither += 1
                print(f"        text: {row['text']!r}")
        print(f"  -> {n_neither}/{TOP_N} of the combined top-{TOP_N} mention neither seed")


# ── --neither-sweep: damping x projection grid ───────────────────────────────


def neither_sweep() -> None:
    chunk_index = pd.Index(all_chunk_node_ids())
    g = gds()

    if g.graph.exists(EXP_GRAPH)["exists"]:
        g.graph.get(EXP_GRAPH).drop()
    graph_rel, _ = g.graph.cypher.project(
        EXP_PROJECTION, graphName=EXP_GRAPH, totalChunks=total_chunks()
    )
    print(f"projected {EXP_GRAPH}: {graph_rel.node_count()} nodes, "
          f"{graph_rel.relationship_count()} rels")

    try:
        grid = ((mentions_graph(), "mentions"), (graph_rel, "ment+rel"))
        for name_a, name_b in PAIRS:
            a, b = resolve(name_a), resolve(name_b)
            direct = mentioning([a["nodeId"], b["nodeId"]])
            for graph, gname in grid:
                for d in (0.45, 0.85):
                    scores = ppr(graph, [a["nodeId"], b["nodeId"]], d, chunk_index)
                    ordered = scores.sort_values(ascending=False)
                    first, in_top50 = None, 0
                    for pos, nid in enumerate(ordered.index, 1):
                        if nid in direct:
                            continue
                        first = first or pos
                        if pos <= 50:
                            in_top50 += 1
                        if pos > 50 and first:
                            break
                    print(f"{a['name'][:12]}+{b['name'][:12]:<14} {gname:9s} d={d}  "
                          f"first NEITHER at rank {first:>4} | {in_top50:>2} of top-50")
    finally:
        g.graph.get(EXP_GRAPH).drop()
        print(f"dropped {EXP_GRAPH}")


# ── --seed-bias: restart bias vs the 1/df contribution imbalance ─────────────


def seed_bias() -> None:
    chunk_index = pd.Index(all_chunk_node_ids())
    graph = mentions_graph()

    for name_hub, name_rare in BIAS_PAIRS:
        hub, rare = resolve(name_hub), resolve(name_rare)
        c_hub, c_rare = mentioning([hub["nodeId"]]), mentioning([rare["nodeId"]])
        both, only_rare, only_hub = c_hub & c_rare, c_rare - c_hub, c_hub - c_rare
        print(f"\n{'=' * 96}\n{hub['name']} (df={hub['df']}) + {rare['name']} (df={rare['df']})"
              f"   both={len(both)} onlyRare={len(only_rare)} onlyHub={len(only_hub)}")

        schemes = {
            "uniform": (1.0, 1.0),
            "sqrt-df": (math.sqrt(hub["df"]), math.sqrt(rare["df"])),
            "df-prop": (float(hub["df"]), float(rare["df"])),
        }
        for scheme, (w_hub, w_rare) in schemes.items():
            total = w_hub + w_rare
            seeds = [[hub["nodeId"], w_hub / total], [rare["nodeId"], w_rare / total]]
            scores = ppr(graph, seeds, 0.45, chunk_index)
            ranks = scores.rank(ascending=False, method="min")

            def stats(ids: set[int]) -> tuple[float, float]:
                return (scores[scores.index.isin(ids)].mean(),
                        ranks[ranks.index.isin(ids)].median())

            m_both, r_both = stats(both)
            m_rare, r_rare = stats(only_rare)
            _, r_hub = stats(only_hub)
            top20 = list(scores.sort_values(ascending=False).head(20).index)

            def comp(ids: list[int]) -> str:
                b = sum(1 for i in ids if i in both)
                r = sum(1 for i in ids if i in only_rare)
                h = sum(1 for i in ids if i in only_hub)
                return f"both={b} rare={r} hub={h} none={len(ids) - b - r - h}"

            print(f"  {scheme:8s} bonus={m_both / m_rare:5.2f}x | median rank "
                  f"both={int(r_both):>4} onlyRare={int(r_rare):>4} onlyHub={int(r_hub):>4}"
                  f" | top8 [{comp(top20[:8])}] | top20 [{comp(top20)}]")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--neither-sweep", action="store_true")
    parser.add_argument("--seed-bias", action="store_true")
    args = parser.parse_args()

    if args.neither_sweep:
        neither_sweep()
    elif args.seed_bias:
        seed_bias()
    else:
        conjunction_tables()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""The corpus table of contents: Leiden themes on the homogeneous co-mention graph.

    NEO4J_DATABASE=lewisclark python scripts/measure_theme_map.py
    NEO4J_DATABASE=lewisclark python scripts/measure_theme_map.py --gamma 2.0
    NEO4J_DATABASE=lewisclark python scripts/measure_theme_map.py --sweep

Finding 6d (2026-09-09): §6 rebuilt around the theme map. Nathan's homogeneous
projection — chunk–chunk SHARES_ENTITIES edges weighted by shared-entity
count, entities above a rarity cutoff excluded (default df < 50; sparsifying
by rarity beat a min-weight cut on every measured axis, and the original
df<400 form on modularity/conductance at a coverage cost — see the finding).

Gamma chosen by sweep elbow, not to match a slide count: on the df<50 graph
the largest-community share flattens at gamma 1.5 with p50 still ~100.
Defaults: --max-df 50, --gamma 1.5. Seeded and single-threaded so the
partition is reproducible.

Writes results/themes-lewisclark-comention.md: the sweep, the per-community
table (size, date span, conductance, defining entities), connectivity check,
and the Blumenfeld conductance thresholds (<=0.35 tight, >=0.60 loose).
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict

import _bootstrap  # noqa: F401

from graphrank.config import gds, read_query

RESULTS = _bootstrap.ROOT / "results" / "themes-lewisclark-comention.md"

#: Entities at or above this chunk-degree do not create edges. Sparsifying by
#: rarity (Nathan, 2026-09-09) beat a min-weight cut on every axis measured:
#: at df<50 modularity 0.38 vs 0.15 (df<400) and 0.24 (weight>=2), conductance
#: median 0.54 vs 0.74/0.60, coverage 83%. The elbow moves to gamma 1.5.
MAX_DF = 50

PROJECT = """
MATCH (c1:Chunk)<-[:MENTIONED_IN]-(b)-[:MENTIONED_IN]->(c2:Chunk)
WHERE c1 < c2
AND COUNT{ (b)-[:MENTIONED_IN]->() } < $maxdf
WITH c1, c2, count(*) AS weight
RETURN gds.graph.project($name, c1, c2,
  {relationshipType: "SHARES_ENTITIES", relationshipProperties: {weight: weight}},
  {undirectedRelationshipTypes: ["SHARES_ENTITIES"]})
"""

def graph_name(maxdf: int) -> str:
    return f"relatedChunksDf{maxdf}"

GAMMAS = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0)


def ensure_graph(maxdf: int):
    g = gds()
    name = graph_name(maxdf)
    if not g.graph.exists(name)["exists"]:
        read_query(PROJECT, maxdf=maxdf, name=name)
    return g.graph.get(name)


def leiden_kwargs(gamma: float) -> dict:
    return dict(relationshipWeightProperty="weight", gamma=float(gamma),
                randomSeed=42, concurrency=1)


def sweep(maxdf: int) -> list[str]:
    g, G = gds(), ensure_graph(maxdf)
    n = G.node_count()
    lines = ["| gamma | communities | modularity | max size | max % | p50 |",
             "|---|---|---|---|---|---|"]
    for gamma in GAMMAS:
        s = g.leiden.stats(G, **leiden_kwargs(gamma))
        d = s["communityDistribution"]
        lines.append(f"| {gamma} | {s['communityCount']} | {s['modularity']:.4f} "
                     f"| {d['max']} | {100 * d['max'] / n:.1f}% | {d['p50']} |")
    return lines


def report(gamma: float, maxdf: int) -> None:
    g, G = gds(), ensure_graph(maxdf)

    frame = g.leiden.stream(G, **leiden_kwargs(gamma))
    comm = dict(zip(frame["nodeId"], frame["communityId"]))
    sizes = Counter(comm.values())

    # connectivity per community (union-find over projection edges)
    parent: dict = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    edges = g.graph.relationships.stream(G)
    for s_, t_ in zip(edges["sourceNodeId"], edges["targetNodeId"]):
        if comm.get(s_) == comm.get(t_):
            ra, rb = find(s_), find(t_)
            if ra != rb:
                parent[ra] = rb
    pieces = defaultdict(set)
    for node, c in comm.items():
        pieces[c].add(find(node))
    disconnected = [c for c, p in pieces.items() if len(p) > 1]

    # conductance needs the community id mutated onto the projection
    prop = f"tocCommunity_{str(gamma).replace('.', '_')}"
    try:
        g.graph.nodeProperties.drop(G, [prop])
    except Exception:
        pass
    g.leiden.mutate(G, mutateProperty=prop, **leiden_kwargs(gamma))
    cond_frame = g.conductance.stream(G, communityProperty=prop,
                                      relationshipWeightProperty="weight")
    conductance = dict(zip(cond_frame["community"], cond_frame["conductance"]))

    # per-community span + defining entities (hubs excluded, like the edges)
    node_rows = read_query(
        "MATCH (c:Chunk) RETURN id(c) AS nid, c.chunkId AS cid, toString(c.date) AS date")
    by_comm: dict = defaultdict(list)
    for r in node_rows:
        if r["nid"] in comm:
            by_comm[comm[r["nid"]]].append(r)

    ent_rows = read_query(
        """
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        WHERE NOT e:Chunk AND NOT e:GenericLocation
        WITH e, count(DISTINCT c) AS df WHERE df < $maxdf
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        RETURN id(c) AS nid, coalesce(e.canonicalName, e.name) AS name
        """,
        maxdf=maxdf,
    )
    ents: dict = defaultdict(Counter)
    for r in ent_rows:
        if r["nid"] in comm:
            ents[comm[r["nid"]]][r["name"]] += 1

    n_chunks = read_query("MATCH (c:Chunk) RETURN count(c) AS n")[0]["n"]
    med = sorted(conductance.values())[len(conductance) // 2]
    tight = sum(1 for v in conductance.values() if v <= 0.35)
    loose = sum(1 for v in conductance.values() if v >= 0.60)

    lines = [
        "# The corpus table of contents — Leiden themes on the co-mention graph",
        "",
        f"`lewisclark` · projection `{graph_name(maxdf)}` (chunk–chunk SHARES_ENTITIES, "
        f"hubs df≥{maxdf} excluded) · {G.node_count()} of {n_chunks} chunks "
        f"({n_chunks - G.node_count()} isolated, no non-hub co-mention) · "
        f"{G.relationship_count() // 2} undirected pairs",
        f"Leiden gamma={gamma}, randomSeed=42, concurrency=1 (reproducible)",
        "",
        f"**{len(sizes)} communities · internally disconnected: {len(disconnected)}"
        f"{' ' + str(disconnected) if disconnected else ''} · conductance median "
        f"{med:.2f} · {tight} of {len(sizes)} tight (≤0.35) · {loose} loose (≥0.60)**",
        "",
        "## Gamma sweep (stats mode) — why this gamma",
        "",
        *sweep(maxdf),
        "",
        f"Gamma {gamma} sits at this projection's elbow: the point where the "
        f"largest-community share stops falling steeply, before median size "
        f"collapses into fragments.",
        "",
        "## The themes",
        "",
        "| id | chunks | span | conductance | defining entities |",
        "|---|---|---|---|---|",
    ]
    for c, size in sizes.most_common():
        rows = by_comm[c]
        dates = sorted(r["date"] for r in rows if r["date"])
        span = f"{dates[0][:7]} → {dates[-1][:7]}" if dates else "—"
        top = ", ".join(name for name, _ in ents[c].most_common(5))
        lines.append(f"| {c} | {size} | {span} | {conductance.get(c, float('nan')):.2f} | {top} |")

    out = RESULTS
    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[:14]))
    print(f"...\nwrote {out} ({len(sizes)} communities)")
    for line in lines[13:13 + 13]:
        print(line)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--gamma", type=float, default=1.5)
    ap.add_argument("--max-df", type=int, default=MAX_DF)
    ap.add_argument("--sweep", action="store_true")
    args = ap.parse_args()
    if args.sweep:
        print("\n".join(sweep(args.max_df)))
    else:
        report(args.gamma, args.max_df)


if __name__ == "__main__":
    main()

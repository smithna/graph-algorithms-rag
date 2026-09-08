#!/usr/bin/env python3
"""Community diversification on the thematic questions — section 6's measurement.

    NEO4J_DATABASE=lewisclark python scripts/measure_communities.py
    NEO4J_DATABASE=lewisclark python scripts/measure_communities.py --only illness-and-injury

Finding 5l ended on a measured hand-off: the expansion walk wins trade-goods
and food-sources but collapses illness-and-injury onto one episode — 7 of 8
window chunks from one week at Long Camp, month coverage 4 -> 1 — because when
a theme's rare entities all co-occur in one episode, conjunction-seeking *is*
episode-seeking. The proposed fix was "cap the window per community". This
script measures that fix on the same three questions, same database, same
window form as 5l, so the read-pack judgements transfer.

Four windows per question, top-8 each:

1. ``vector``            cosine alone — 5l's baseline, unchanged
2. ``expand``            the shipped walk (cosine 0.6 / entity 0.2 / passage
                         0.2) — 5l's windows, reproduced not re-measured
3. ``expand+community``  the same blended ranking, capped at
                         ``max_per_community`` chunks per Louvain community
4. ``vector+community``  the classic diversification baseline: cosine capped
                         the same way, so the walk's contribution under the
                         cap is separable from the cap itself

The capped windows are measured on **Leiden with a fixed random seed**
(concurrency=1), because that is byte-identical across processes — verified —
while Louvain's partition, and therefore its capped window, drifts from run to
run. Louvain is reported as the robustness check instead of the measurement.

Per the measurement discipline this script emits **no verdict**: membership
tables with community ids, community fact-sheets (size, span, top entities,
conductance) for every community a window touches, descriptive window stats
(months, near-duplicate pairs, distinct entities), a Louvain robustness
check, and an internal-connectivity audit of both partitions (the textbook
reason Leiden exists — checked here rather than asserted). The verdict comes
from reading the read-pack it writes to ``results/communities-<database>.md``
— chunks already judged in 5l's read-pack (``results/thematic-<database>.md``)
are flagged as such.

Results and their reading live in ``docs/talk-outline.md``, section 6 findings.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from rich.console import Console
from rich.table import Table

from graphrank import communities
from graphrank.communities import CommunityConfig
from graphrank.config import read_query, settings
from graphrank.models import RetrievalResult
from graphrank.pagerank import ExpandConfig, expand
from graphrank.projection import project, project_mentions
from graphrank.strategies import vector_strategy
from measure_thematic import K, THEMATIC, window_stats

console = Console()

#: How deep a slate the cap may draw from. 50 matches the candidate window
#: every other strategy in this repo uses.
CANDIDATE_K = 50


def internally_disconnected(membership) -> tuple[int, int]:
    """How many communities are not internally connected.

    The textbook motivation for Leiden is that Louvain can emit communities
    whose members are not mutually reachable *within* the community. This
    checks the claim on this graph instead of asserting it: rebuild the
    projection's edge list from the database (same predicates), keep only
    intra-community edges, and count components per community with union-find.

    Returns (disconnected_communities, total_communities).
    """
    edges = read_query(
        """
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        WHERE NOT e:Chunk AND NOT e:GenericLocation
        RETURN DISTINCT id(e) AS s, id(c) AS t
        UNION
        MATCH (c1:Chunk)-[:NEXT_CHUNK]->(c2:Chunk)
        RETURN id(c1) AS s, id(c2) AS t
        UNION
        MATCH (a)-[r]->(b)
        WHERE NOT a:Chunk AND NOT b:Chunk
          AND NOT a:GenericLocation AND NOT b:GenericLocation
          AND type(r) <> 'MENTIONED_IN'
        RETURN id(a) AS s, id(b) AS t
        """
    )
    community = membership.to_dict()
    parent: dict[int, int] = {n: n for n in community}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for edge in edges:
        s, t = edge["s"], edge["t"]
        if s in community and community[s] == community.get(t):
            parent[find(s)] = find(t)

    components: dict[int, set[int]] = {}
    for node, cid in community.items():
        components.setdefault(cid, set()).add(find(node))
    disconnected = sum(1 for roots in components.values() if len(roots) > 1)
    return disconnected, len(components)


def build_windows(
    question: str, config: CommunityConfig
) -> tuple[dict[str, RetrievalResult], RetrievalResult]:
    """The four windows, plus the wide expand slate for the robustness check.

    The top-8 of a ranked slate is the same whether you ask for 8 or 50, so
    ``vector`` and ``expand`` are trims of the wide runs — one scoring pass
    per strategy, and the capped window provably shares its base ranking.
    """
    wide_vector = vector_strategy(question, k=CANDIDATE_K)
    wide_expand = expand(
        question,
        config=ExpandConfig(k=CANDIDATE_K, cosine_weight=0.6, entity_share=0.5),
    )

    def trim(wide: RetrievalResult, strategy: str) -> RetrievalResult:
        return RetrievalResult(
            question=wide.question,
            strategy=strategy,
            chunks=list(wide.chunks[: config.k]),
            elapsed_ms=wide.elapsed_ms,
            debug=dict(wide.debug),
        )

    windows = {
        "vector": trim(wide_vector, "vector"),
        "expand": trim(wide_expand, "expand"),
        "expand+community": communities.diversify(wide_expand, config=config),
        "vector+community": communities.diversify(wide_vector, config=config),
    }
    communities.label_communities(
        [c for w in windows.values() for c in w.chunks], config=config
    )
    return windows, wide_expand


def community_fact_sheet(community_ids: list[int], config: CommunityConfig) -> Table:
    """Size, span, top entities and conductance for the communities in play."""
    summaries = {
        s["community_id"]: s
        for s in communities.summarize(community_ids, config=config, limit=10**6)
    }
    cond = communities.conductance(config=config)

    table = Table(title="communities touched by any window", header_style="bold")
    table.add_column("id", justify="right")
    table.add_column("chunks", justify="right")
    table.add_column("span")
    table.add_column("conductance", justify="right")
    table.add_column("top entities")
    for cid in community_ids:
        s = summaries.get(cid)
        if s is None:
            table.add_row(str(cid), "?", "?", "?", "?")
            continue
        span = (
            f"{s['date_range'][0][:7]} → {s['date_range'][1][:7]}"
            if s["date_range"]
            else "—"
        )
        table.add_row(
            str(cid),
            str(s["chunk_count"]),
            span,
            f"{cond.get(cid, float('nan')):.2f}",
            ", ".join(e.name for e in s["top_entities"][:5]),
        )
    return table


def louvain_check(qid: str, wide_expand: RetrievalResult, config: CommunityConfig) -> str:
    """Same cap under Louvain — window agreement as a robustness note, no verdict.

    Louvain's partition varies across runs, so this is one draw from that
    distribution, not a number to quote.
    """
    import copy

    # Work on a copy: label_communities stamps community_id onto the chunk
    # objects, and the caller's windows must keep their Leiden labels.
    wide_expand = copy.deepcopy(wide_expand)
    louvain_cfg = CommunityConfig(
        k=config.k,
        max_per_community=config.max_per_community,
        algorithm="louvain",
        resolution=config.resolution,
    )
    leiden = communities.diversify(wide_expand, config=config)
    louvain = communities.diversify(wide_expand, config=louvain_cfg)
    shared = len(set(louvain.chunk_ids()) & set(leiden.chunk_ids()))
    return (
        f"{qid}: expand+community windows share {shared}/{config.k} chunks "
        f"across Leiden/Louvain (Louvain redraws each run)"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--only", choices=sorted(THEMATIC), help="run one question")
    parser.add_argument("--max-per-community", type=int, default=2)
    args = parser.parse_args()

    db = settings().neo4j_database
    console.print(f"[bold]Community measurement on database '{db}'[/bold]")
    for stats in (project(), project_mentions()):
        console.print(
            f"[dim]{stats.name}: {stats.node_count} nodes / "
            f"{stats.relationship_count} rels[/dim]"
        )

    config = CommunityConfig(
        k=K, max_per_community=args.max_per_community, algorithm="leiden"
    )
    for algo in ("leiden", "louvain"):
        acfg = CommunityConfig(algorithm=algo)
        m = communities.detect(config=acfg)
        stats = communities.detect_stats(config=acfg)
        cond = communities.conductance(config=acfg)
        disconnected, total = internally_disconnected(m)
        console.print(
            f"[dim]{algo}: {m.nunique()} communities, modularity "
            f"{stats.get('modularity', float('nan')):.4f}, conductance median "
            f"{cond.median():.2f} ({int((cond <= 0.35).sum())} tight ≤0.35, "
            f"{int((cond >= 0.60).sum())} loose ≥0.60), "
            f"{disconnected}/{total} internally disconnected[/dim]"
        )
    console.print()

    # 5l's read-pack: chunks already hand-judged there need no second read.
    judged_path = Path(__file__).resolve().parent.parent / "results" / f"thematic-{db}.md"
    already_judged = (
        {
            line.split()[1]
            for line in judged_path.read_text().splitlines()
            if line.startswith("### ")
        }
        if judged_path.exists()
        else set()
    )

    questions = {args.only: THEMATIC[args.only]} if args.only else THEMATIC

    read_pack: list[str] = [
        f"# Community read-pack — database `{db}`\n",
        "Every distinct chunk across all four windows, grouped by question.",
        "Membership flags say which strategy's top-8 holds it and at what",
        "position; `cosine` is the corpus-wide cosine rank; `community` is the",
        "chunk's Leiden community (seed 42). Chunks marked *judged in 5l* carry",
        "a hand read in `thematic-" + db + ".md`. Judge the rest by reading.\n",
    ]
    robustness: list[str] = []

    for qid, question in questions.items():
        console.rule(f"[bold]{qid}[/bold]")
        console.print(f"[italic]{question}[/italic]")

        windows, wide_expand = build_windows(question, config)

        # ── membership table with community ids ─────────────────────────────
        table = Table(title=f"{qid} — top-{K} windows (chunk · community)")
        table.add_column("pos")
        for name in windows:
            table.add_column(name)
        for i, row in enumerate(zip(*(w.chunks for w in windows.values())), 1):
            table.add_row(
                str(i), *(f"{c.chunk_id[:10]} · {c.community_id}" for c in row)
            )
        console.print(table)

        # ── descriptive stats ───────────────────────────────────────────────
        vector_window = set(windows["vector"].chunk_ids())
        stats_table = Table(title=f"{qid} — window stats (descriptive, no judgement)")
        for col in ("strategy", "vs vector", "entities", "near-dup pairs", "months", "communities"):
            stats_table.add_column(col)
        for name, result in windows.items():
            ids = result.chunk_ids()
            ws = window_stats(ids)
            n_communities = len(
                {c.community_id for c in result.chunks if c.community_id is not None}
            )
            stats_table.add_row(
                name,
                f"{len(set(ids) & vector_window)}/{K}" if name != "vector" else "—",
                str(ws["distinct_entities"]),
                str(ws["near_dup_pairs"]),
                str(ws["distinct_months"]),
                str(n_communities),
            )
        console.print(stats_table)

        # ── the communities in play ─────────────────────────────────────────
        touched = sorted(
            {
                c.community_id
                for w in windows.values()
                for c in w.chunks
                if c.community_id is not None
            }
        )
        console.print(community_fact_sheet(touched, config))

        robustness.append(louvain_check(qid, wide_expand, config))

        # ── read-pack: union of all windows, full text ──────────────────────
        union: dict[str, dict] = {}
        for name, result in windows.items():
            for pos, c in enumerate(result.chunks, 1):
                entry = union.setdefault(c.chunk_id, {"chunk": c, "member": {}})
                entry["member"][name] = pos
        cosine_ranks = wide_expand.debug.get("cosine_rank", {})

        read_pack.append(f"\n## {qid}\n\n> {question}\n")
        for chunk_id, entry in sorted(union.items()):
            c = entry["chunk"]
            flags = " · ".join(
                f"{name} #{pos}" for name, pos in sorted(entry["member"].items())
            )
            cr = cosine_ranks.get(chunk_id, "≤8" if "vector" in entry["member"] else "?")
            judged = " · **judged in 5l**" if chunk_id in already_judged else ""
            read_pack.append(
                f"### {chunk_id} — {c.date or 'no date'} — {c.author or 'unknown'}\n"
                f"*{flags} · cosine rank {cr} · community {c.community_id}{judged}*\n\n"
                f"{c.text}\n"
            )

    console.print()
    for line in robustness:
        console.print(f"[dim]{line}[/dim]")

    out = Path(__file__).resolve().parent.parent / "results" / f"communities-{db}.md"
    out.write_text("\n".join(read_pack))
    console.print(f"\n[bold]read-pack written to {out}[/bold] — the verdict lives there")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

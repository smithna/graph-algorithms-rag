#!/usr/bin/env python3
"""Communities: the corpus's table of contents, derived from structure.

    python scripts/demo_communities.py                    # list the themes
    python scripts/demo_communities.py --write            # persist communityId
    python scripts/demo_communities.py -q "What illnesses and injuries did the corps deal with?" --base expand

The default algorithm is Leiden with a fixed random seed, because that is
deterministic across runs — the same themes and the same windows every time,
which is what a live demo needs. ``--algorithm louvain`` shows the classic
algorithm instead (and redraws its partition every run).
"""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from rich.console import Console
from rich.table import Table

from graphrank import baseline, communities
from graphrank.communities import CommunityConfig
from graphrank.pagerank import ExpandConfig, expand

console = Console()


def show_themes(config: CommunityConfig, limit: int) -> None:
    summaries = communities.summarize(config=config, limit=limit)
    cond = communities.conductance(config=config)

    table = Table(title=f"Top {len(summaries)} communities", header_style="bold")
    table.add_column("id", width=5, justify="right")
    table.add_column("chunks", width=7, justify="right")
    table.add_column("entities", width=8, justify="right")
    table.add_column("span", width=23)
    table.add_column("cond.", width=5, justify="right")
    table.add_column("Defining entities")

    for summary in summaries:
        span = (
            f"{summary['date_range'][0]} → {summary['date_range'][1]}"
            if summary["date_range"]
            else "—"
        )
        table.add_row(
            str(summary["community_id"]),
            f"{summary['chunk_count']:,}",
            f"{summary['entity_count']:,}",
            span,
            f"{cond.get(summary['community_id'], float('nan')):.2f}",
            ", ".join(e.name for e in summary["top_entities"]),
        )
    console.print(table)
    console.print(
        "[dim]cond. is conductance — the share of a community's edge weight "
        "that leaves it. ≤0.35 reads as a tight theme, ≥0.60 as a loose one.[/]"
    )


def window_months(result) -> int:
    return len({(c.date or "?")[:7] for c in result.chunks})


def show_diversification(question: str, config: CommunityConfig, base: str) -> None:
    console.rule(f"[bold]{question}")

    if base == "expand":
        wide = expand(
            question,
            config=ExpandConfig(
                k=config.candidate_k, cosine_weight=0.6, entity_share=0.5
            ),
        )
    else:
        wide = baseline.retrieve(question, k=config.candidate_k)
    plain = type(wide)(
        question=wide.question,
        strategy=wide.strategy,
        chunks=list(wide.chunks[: config.k]),
        elapsed_ms=wide.elapsed_ms,
        debug=dict(wide.debug),
    )
    diverse = communities.diversify(wide, config=config, with_graph_context=True)
    baseline.attach_graph_context(plain)
    communities.label_communities(plain.chunks, config=config)

    from graphrank.metrics import redundancy

    table = Table(header_style="bold")
    table.add_column("Strategy")
    table.add_column("Communities", justify="right")
    table.add_column("Months", justify="right")
    table.add_column("Redundancy", justify="right")

    table.add_row(
        f"{base} top-{config.k}",
        str(len({c.community_id for c in plain.chunks if c.community_id is not None})),
        str(window_months(plain)),
        f"{redundancy(plain):.3f}",
    )
    table.add_row(
        f"community-capped (max {config.max_per_community}/theme)",
        str(len(diverse.debug.get("communities_represented", []))),
        str(window_months(diverse)),
        f"{redundancy(diverse):.3f}",
    )
    console.print(table)
    console.print(
        "[dim]Redundancy is mean pairwise entity overlap between retrieved "
        "passages. Lower means the context window covers more ground.[/]"
    )

    detail = Table(header_style="bold")
    detail.add_column("pos", justify="right")
    detail.add_column(f"{base} top-{config.k}")
    detail.add_column("community-capped")
    for i, (a, b) in enumerate(zip(plain.chunks, diverse.chunks), 1):
        detail.add_row(
            str(i),
            f"{(a.date or '?')[:10]} · c{a.community_id}",
            f"{(b.date or '?')[:10]} · c{b.community_id}",
        )
    console.print(detail)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-q", "--question", help="also show diversification on a question")
    parser.add_argument("--base", choices=("vector", "expand"), default="expand",
                        help="which strategy's ranking the cap applies to")
    parser.add_argument("-k", type=int, default=8)
    parser.add_argument("--max-per-community", type=int, default=2)
    parser.add_argument("--algorithm", choices=("leiden", "louvain"), default="leiden",
                        help="leiden (seeded, deterministic) or louvain (redraws each run)")
    parser.add_argument("--resolution", type=float, default=1.0,
                        help="higher yields more, smaller communities")
    parser.add_argument("--limit", type=int, default=12, help="communities to list")
    parser.add_argument("--write", action="store_true",
                        help="WRITES communityId onto your Neo4j nodes")
    args = parser.parse_args()

    config = CommunityConfig(
        k=args.k,
        max_per_community=args.max_per_community,
        algorithm=args.algorithm,
        resolution=args.resolution,
    )

    if args.write:
        console.print("[yellow]Writing communityId back to Neo4j …[/]")
        stats = communities.write_back(config=config)
        console.print(
            f"[green]✓[/] wrote {stats.get('nodePropertiesWritten', 0):,} properties, "
            f"{stats.get('communityCount', 0):,} communities, "
            f"modularity {stats.get('modularity', float('nan')):.4f}"
        )

    show_themes(config, args.limit)

    if args.question:
        show_diversification(args.question, config, args.base)

    return 0


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

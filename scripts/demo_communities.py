#!/usr/bin/env python3
"""Louvain communities: the corpus's table of contents, derived from structure.

    python scripts/demo_communities.py                    # list the themes
    python scripts/demo_communities.py --write            # persist communityId
    python scripts/demo_communities.py -q "What did they eat on the Columbia?"
"""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from rich.console import Console
from rich.table import Table

from graphrank import baseline, communities
from graphrank.communities import CommunityConfig

console = Console()


def show_themes(config: CommunityConfig, limit: int) -> None:
    summaries = communities.summarize(config=config, limit=limit)

    table = Table(title=f"Top {len(summaries)} communities", header_style="bold")
    table.add_column("id", width=5, justify="right")
    table.add_column("chunks", width=7, justify="right")
    table.add_column("entities", width=8, justify="right")
    table.add_column("span", width=23)
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
            ", ".join(e.name for e in summary["top_entities"]),
        )
    console.print(table)


def show_diversification(question: str, config: CommunityConfig) -> None:
    console.rule(f"[bold]{question}")

    plain = baseline.retrieve(question, k=config.k, with_graph_context=True)
    diverse = communities.retrieve(question, config=config, with_graph_context=True)

    from graphrank.metrics import redundancy

    table = Table(header_style="bold")
    table.add_column("Strategy")
    table.add_column("Communities", justify="right")
    table.add_column("Redundancy", justify="right")
    table.add_column("ms", justify="right")

    table.add_row(
        "vector only",
        str(len(diverse.debug.get("communities_in_vector_topk", []))),
        f"{redundancy(plain):.3f}",
        f"{plain.elapsed_ms:.0f}",
    )
    table.add_row(
        f"community-capped (max {config.max_per_community}/theme)",
        str(len(diverse.debug.get("communities_represented", []))),
        f"{redundancy(diverse):.3f}",
        f"{diverse.elapsed_ms:.0f}",
    )
    console.print(table)
    console.print(
        "[dim]Redundancy is mean pairwise entity overlap between retrieved "
        "passages. Lower means the context window covers more ground.[/]"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-q", "--question", help="also show diversification on a question")
    parser.add_argument("-k", type=int, default=8)
    parser.add_argument("--max-per-community", type=int, default=2)
    parser.add_argument("--resolution", type=float, default=1.0,
                        help="higher yields more, smaller communities")
    parser.add_argument("--limit", type=int, default=12, help="communities to list")
    parser.add_argument("--write", action="store_true",
                        help="WRITES communityId onto your Neo4j nodes")
    args = parser.parse_args()

    config = CommunityConfig(
        k=args.k,
        max_per_community=args.max_per_community,
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
        show_diversification(args.question, config)

    return 0


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

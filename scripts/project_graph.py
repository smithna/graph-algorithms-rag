#!/usr/bin/env python3
"""Project the retrieval graph into the GDS catalog.

Run this once per session. Every algorithm script reuses the projection, which
is the whole performance argument: you pay for the projection once and then
personalized PageRank costs milliseconds per query.
"""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from rich.console import Console
from rich.table import Table

from graphrank.config import settings
from graphrank.projection import drop_graph, graph_exists, project, total_chunks

console = Console()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="re-project even if it exists")
    parser.add_argument("--drop", action="store_true", help="drop the projection and exit")
    args = parser.parse_args()

    cfg = settings()

    if args.drop:
        drop_graph()
        console.print(f"[green]✓[/] dropped '{cfg.graph_name}'")
        return 0

    if graph_exists() and not args.force:
        console.print(
            f"[yellow]![/] '{cfg.graph_name}' already projected — "
            "reusing it. Pass --force to rebuild."
        )

    console.print(f"Projecting [bold]{cfg.graph_name}[/] …")
    stats = project(force=args.force)

    table = Table(show_header=False, box=None)
    table.add_row("Graph", stats.name)
    table.add_row("Nodes", f"{stats.node_count:,}")
    table.add_row("Relationships", f"{stats.relationship_count:,}")
    table.add_row("Corpus chunks", f"{total_chunks():,}")
    if stats.projection_ms:
        table.add_row("Projection time", f"{stats.projection_ms:,.0f} ms")
    table.add_row("MENTIONS weight", "log(1 + totalChunks / df)  [IDF]")
    table.add_row("NEXT_CHUNK weight", f"{cfg.next_chunk_weight}")
    table.add_row("RELATED weight", f"{cfg.related_weight}")
    console.print(table)

    console.print("\n[bold green]Ready.[/] Try: python scripts/demo_pagerank.py")
    return 0


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

#!/usr/bin/env python3
"""Project the retrieval graphs into the GDS catalog.

Run this once per session. Every algorithm script reuses the projections, so
the projection cost is amortised — 289 ms and 94 ms respectively.

That is not the same as queries being free: section 5's retrieval runs two PPR
calls at ~55 ms each, so a fresh question is ~196 ms. See the note in
``graphrank/projection.py``.

**Two projections, on purpose.** A projection is not neutral infrastructure —
it encodes what you are optimising for.

``lc-retrieval``  all three relationship types. Reranking (sections 5-7).
``lc-mentions``   ``MENTIONED_IN`` only, undirected. Multi-seed PPR (section 5).

Section 5's walk wants the second one because ``MENTIONED_IN`` is the only
relationship here whose direction is honestly symmetric, and because
``NEXT_CHUNK`` leaks walk mass into passages that are merely adjacent in time.
"""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from rich.console import Console
from rich.table import Table

from graphrank.config import settings
from graphrank.projection import (
    drop_graph,
    graph_exists,
    project,
    project_mentions,
    total_chunks,
)

console = Console()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="re-project even if it exists")
    parser.add_argument("--drop", action="store_true", help="drop both projections and exit")
    args = parser.parse_args()

    cfg = settings()

    if args.drop:
        for name in (cfg.graph_name, cfg.mentions_graph_name):
            drop_graph(name)
            console.print(f"[green]✓[/] dropped '{name}'")
        return 0

    for name in (cfg.graph_name, cfg.mentions_graph_name):
        if graph_exists(name) and not args.force:
            console.print(
                f"[yellow]![/] '{name}' already projected — reusing it. "
                "Pass --force to rebuild."
            )

    console.print(f"Projecting [bold]{cfg.graph_name}[/] …")
    retrieval = project(force=args.force)
    console.print(f"Projecting [bold]{cfg.mentions_graph_name}[/] …")
    mentions = project_mentions(force=args.force)

    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("")
    table.add_column(cfg.graph_name, justify="right")
    table.add_column(cfg.mentions_graph_name, justify="right")
    table.add_row("Nodes", f"{retrieval.node_count:,}", f"{mentions.node_count:,}")
    table.add_row(
        "Relationships",
        f"{retrieval.relationship_count:,}",
        f"{mentions.relationship_count:,}",
    )
    table.add_row(
        "Projection time",
        f"{retrieval.projection_ms:,.0f} ms" if retrieval.projection_ms else "reused",
        f"{mentions.projection_ms:,.0f} ms" if mentions.projection_ms else "reused",
    )
    table.add_row("Relationship types", "MENTIONS, NEXT_CHUNK, RELATED", "MENTIONS")
    table.add_row("MENTIONS weight", "log(1 + totalChunks / df)", "log(1 + totalChunks / df)")
    table.add_row("NEXT_CHUNK weight", f"{cfg.next_chunk_weight}", "—")
    table.add_row("RELATED weight", f"{cfg.related_weight}", "—")
    console.print(table)
    console.print(f"\nCorpus chunks: [bold]{total_chunks():,}[/]")

    console.print("\n[bold green]Ready.[/] Try: python scripts/demo_pagerank.py")
    return 0


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

#!/usr/bin/env python3
"""Yen's k-shortest paths: why two concepts are related, with receipts.

    python scripts/demo_paths.py --from Sacagawea --to Shoshone
    python scripts/demo_paths.py --from "Grizzly Bear" --to "Great Falls" -k 5

Every hop reports the journal passage it was extracted from, so the path is not
just a claim about a connection — it is a citation trail.
"""

from __future__ import annotations

import argparse
import textwrap

import _bootstrap  # noqa: F401
from rich.console import Console
from rich.table import Table

from graphrank import paths
from graphrank.paths import PathConfig
from graphrank.resolve import resolve_entity

console = Console()


def _preview(text: str, width: int = 92) -> str:
    return textwrap.shorten(" ".join(text.split()), width=width, placeholder=" …")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--from", dest="source", required=True, help="first anchor concept")
    parser.add_argument("--to", dest="target", required=True, help="second anchor concept")
    parser.add_argument("-k", "--k-paths", type=int, default=5, help="how many routes")
    parser.add_argument("--max-hops", type=int, default=5)
    parser.add_argument("--weighted", action="store_true",
                        help="let IDF weights bend the routes instead of counting hops")
    parser.add_argument("--evidence", type=int, default=6, help="evidence passages to show")
    args = parser.parse_args()

    source = resolve_entity(args.source)
    target = resolve_entity(args.target)

    if source is None or target is None:
        missing = args.source if source is None else args.target
        console.print(f"[red]✗[/] could not resolve '{missing}' to a node in the graph")
        return 1

    console.rule(
        f"[bold]{source.name}[/] ({source.label})  ⇄  [bold]{target.name}[/] ({target.label})"
    )
    console.print(
        f"[dim]resolved via {source.resolved_via} / {target.resolved_via}[/]\n"
    )

    config = PathConfig(
        k_paths=args.k_paths,
        max_hops=args.max_hops,
        weighted=args.weighted,
        k=args.evidence,
    )
    found = paths.k_shortest_paths(source, target, config=config)

    if not found:
        console.print(
            "[yellow]No route within the hop limit.[/] "
            "Try --max-hops, or check that both anchors have extracted relationships."
        )
        return 0

    table = Table(title=f"{len(found)} shortest routes", header_style="bold")
    table.add_column("#", width=3, justify="right")
    table.add_column("hops", width=5, justify="right")
    table.add_column("Route")
    for i, path in enumerate(found, 1):
        table.add_row(str(i), str(path.hops), path.describe())
    console.print(table)

    console.print("\n[bold]Hop-by-hop evidence[/]")
    for i, path in enumerate(found, 1):
        console.print(f"\n[bold cyan]Route {i}[/]")
        for rel in path.relationships:
            citation = f"  [dim]{rel.date or 'undated'} · {rel.chunk_id or 'structural'}[/]"
            console.print(f"  {rel.describe()}{citation}")

    evidence = paths.evidence_chunks(found, limit=args.evidence)
    if evidence:
        console.print(f"\n[bold]Context assembled from those hops[/] ({len(evidence)} passages)")
        for chunk in evidence:
            header = " · ".join(x for x in (chunk.author, chunk.date) if x)
            console.print(f"\n[dim]{header or chunk.chunk_id} ({chunk.source})[/]")
            console.print(f"  {_preview(chunk.text)}")

    return 0


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

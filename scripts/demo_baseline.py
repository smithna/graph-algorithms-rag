#!/usr/bin/env python3
"""Section 0: the cold open — pure vector search, nothing else.

    NEO4J_DATABASE=lewisclark python scripts/demo_baseline.py
    python scripts/demo_baseline.py "your question here" -k 8

This is the control condition (`graphrank.baseline.vector_search`) run on the
talk's opening question, and it is deliberately the ONLY retrieval this script
can do — no walk, no filter, no graph — so putting its output on slide 0.1
spoils nothing that §5 demonstrates. The point of the cold open is that this
window *looks* shippable; §0.2 counts what's actually in it.
"""

from __future__ import annotations

import argparse
import textwrap

import _bootstrap  # noqa: F401
from rich.console import Console
from rich.table import Table

from graphrank.baseline import vector_search
from graphrank.config import settings
from graphrank.embedding import embed

console = Console()

DEFAULT_QUESTION = "What was Toussaint Charbonneau's role on the expedition?"


def _preview(text: str, width: int = 66) -> str:
    return textwrap.shorten(" ".join(text.split()), width=width, placeholder=" …")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("-k", type=int, default=8, help="window size (default 8)")
    args = parser.parse_args()

    console.print(f"[bold]Vector baseline on '{settings().neo4j_database}'[/bold]")
    console.print(f"[dim]{args.question}[/dim]\n")

    chunks = vector_search(embed(args.question), k=args.k)

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", justify="right")
    table.add_column("date")
    table.add_column("author")
    table.add_column("cosine", justify="right")
    table.add_column("passage")
    for i, c in enumerate(chunks, 1):
        table.add_row(str(i), c.date or "—", c.author or "—",
                      f"{c.vector_score:.3f}", _preview(c.text))
    console.print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

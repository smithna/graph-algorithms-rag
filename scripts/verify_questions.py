#!/usr/bin/env python3
"""Check every gold label in the question bank against the live graph.

Gold entity names must match `canonicalName` exactly or recall is meaningless.
This reports each name that does not resolve and suggests the closest match the
graph actually contains.

    python scripts/verify_questions.py
    python scripts/verify_questions.py --fix    # rewrite questions.yaml in place
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
import yaml
from rich.console import Console
from rich.table import Table

from graphrank.config import query
from graphrank.resolve import resolve_entity

console = Console()
ROOT = Path(__file__).resolve().parent.parent
QUESTION_BANK = ROOT / "questions" / "questions.yaml"


def exact_match(name: str) -> str | None:
    rows = query(
        """
        MATCH (n) WHERE coalesce(n.canonicalName, n.name) = $name
          AND NOT n:Chunk
        RETURN head(labels(n)) AS label LIMIT 1
        """,
        name=name,
    )
    return rows[0]["label"] if rows else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--questions", type=Path, default=QUESTION_BANK)
    parser.add_argument("--fix", action="store_true",
                        help="replace unresolved names with the suggested match")
    args = parser.parse_args()

    entries = yaml.safe_load(args.questions.read_text()) or []

    table = Table(header_style="bold")
    table.add_column("Question")
    table.add_column("Gold name")
    table.add_column("Status")
    table.add_column("Suggestion")

    problems = 0
    replacements: dict[str, str] = {}

    for entry in entries:
        for name in entry.get("gold", []) or []:
            label = exact_match(name)
            if label:
                table.add_row(entry["id"], name, f"[green]✓ {label}[/]", "")
                continue

            problems += 1
            suggestion = resolve_entity(name)
            if suggestion:
                table.add_row(
                    entry["id"],
                    name,
                    "[red]✗ no exact match[/]",
                    f"{suggestion.name} ({suggestion.label}, via {suggestion.resolved_via})",
                )
                replacements[name] = suggestion.name
            else:
                table.add_row(entry["id"], name, "[red]✗ no exact match[/]",
                              "[dim]nothing close[/]")

        for anchor in entry.get("anchors", []) or []:
            resolved = resolve_entity(anchor)
            if resolved is None:
                problems += 1
                table.add_row(entry["id"], f"anchor: {anchor}",
                              "[red]✗ unresolvable[/]", "")

    console.print(table)

    if problems == 0:
        console.print("\n[bold green]All gold labels resolve.[/] Benchmark numbers are trustworthy.")
        return 0

    console.print(f"\n[yellow]{problems} label(s) need attention.[/]")

    if args.fix and replacements:
        text = args.questions.read_text()
        for old, new in replacements.items():
            text = text.replace(f"- {old}\n", f"- {new}\n")
        args.questions.write_text(text)
        console.print(f"[green]✓[/] rewrote {len(replacements)} name(s) in {args.questions}")
    elif replacements:
        console.print("[dim]Re-run with --fix to apply the suggestions.[/]")

    return 1


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

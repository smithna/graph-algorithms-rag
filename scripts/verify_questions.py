#!/usr/bin/env python3
"""Check every gold target in the question bank against the live graph.

Each gold entry in `questions.yaml` is a display name pinned by that question's
`targets:` map to a [canonicalName, label] pair. A benchmark number is only as
good as those pins, and the old version of this script was fooled by decoys:
its ✓ meant "a node with this name exists", not "the right node" — it passed
ELK on a near-empty stray while 439 mentions of the actual elk sat on CERVUS
CANADENSIS (outline finding #10).

So verification now applies the mention-count prominence prior that
`resolve.py` uses to break its near-ties. A pin passes only if:

  1. the (canonicalName, label) node exists,
  2. exactly one node carries that (name, label) — no silent coin-flip,
  3. no other node bearing the same name has MORE mentions — the pinned node
     must be the one the corpus is actually about.

It also warns (without failing) when a pinned node is textually thin (< 10
mentions): a thin target bounds every strategy equally and is a finding to
report, not a label to patch around.

    NEO4J_DATABASE=lewisclark python scripts/verify_questions.py

There is no --fix any more: targets are curated pairs, and suggestions are
printed for a human to adopt deliberately.
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

#: Below this many mentions a target is flagged as thin. Thin ≠ wrong: the
#: node can still be the most prominent bearer of its name (PACIFIC OCEAN has
#: 19 mentions and no better candidate). The flag exists so nobody quotes a
#: recall number without knowing the gold entity barely exists in the corpus.
THIN_MENTIONS = 10


def candidates(name: str) -> list[dict]:
    """Every non-Chunk node whose canonical name matches, most-mentioned first."""
    return query(
        """
        MATCH (n) WHERE coalesce(n.canonicalName, n.name) = $name
          AND NOT n:Chunk
        RETURN head(labels(n)) AS label,
               count { (n)-[:MENTIONED_IN]->(:Chunk) } AS mentions
        ORDER BY mentions DESC
        """,
        name=name,
    )


def display_bearers(display: str) -> list[dict]:
    """Every non-Chunk node carrying the display name as name OR alias.

    This is what catches a decoy whose true node goes by a different canonical
    name: the graph's own alias lists say who really answers to "ELK".
    """
    return query(
        """
        MATCH (n) WHERE NOT n:Chunk AND (
            toUpper(coalesce(n.canonicalName, n.name)) = toUpper($name)
            OR any(a IN coalesce(n.aliases, []) WHERE toUpper(a) = toUpper($name))
        )
        RETURN coalesce(n.canonicalName, n.name) AS name,
               head(labels(n)) AS label,
               count { (n)-[:MENTIONED_IN]->(:Chunk) } AS mentions,
               CASE WHEN toUpper(coalesce(n.canonicalName, n.name)) = toUpper($name)
                    THEN 'its name' ELSE 'an alias' END AS via
        ORDER BY mentions DESC
        """,
        name=display,
    )


def check_target(display: str, name: str, label: str) -> tuple[str, str, bool]:
    """Return (status_markup, detail_markup, ok) for one pinned target."""
    rows = candidates(name)
    pinned = [r for r in rows if r["label"] == label]

    if not pinned:
        suggestion = resolve_entity(display) or resolve_entity(name)
        hint = (
            f"try {suggestion.name} ({suggestion.label}, "
            f"{suggestion.mentions} mentions, via {suggestion.resolved_via})"
            if suggestion
            else "[dim]nothing close[/]"
        )
        return "[red]✗ pin not found[/]", hint, False

    if len(pinned) > 1:
        return (
            f"[red]✗ ambiguous pin[/]",
            f"{len(pinned)} nodes share ({name}, {label}) — a name alone "
            f"cannot address the right one",
            False,
        )

    mine = pinned[0]["mentions"]
    rivals = [r for r in rows if r["label"] != label]
    outranked = [r for r in rivals if r["mentions"] > mine]
    if outranked:
        top = outranked[0]
        return (
            "[red]✗ decoy suspected[/]",
            f"pinned {label} has {mine} mentions but {top['label']} "
            f"'{name}' has {top['mentions']} — prominence prior says the "
            f"corpus is about the other node",
            False,
        )

    # Same-name prominence alone cannot catch the historical failure: a decoy
    # NAMED ELK while the real node is CERVUS CANADENSIS with "Elk" among its
    # aliases. So also rank every node that bears the DISPLAY name — as
    # canonical name or as alias — and demand the pin (or a node the pin
    # dominates) is where the corpus mass actually sits.
    bearers = display_bearers(display)
    stronger = [
        b for b in bearers
        if (b["name"], b["label"]) != (name, label) and b["mentions"] > mine
    ]
    if stronger and mine < THIN_MENTIONS and stronger[0]["mentions"] >= 10 * max(mine, 1):
        top = stronger[0]
        return (
            "[red]✗ decoy suspected[/]",
            f"pin has {mine} mentions but '{display}' is carried by "
            f"{top['name']} ({top['label']}, {top['mentions']} — as "
            f"{top['via']})",
            False,
        )

    detail = f"{mine} mentions"
    if rivals:
        detail += f" (beats {len(rivals)} same-name rival(s))"
    if stronger:
        top = stronger[0]
        detail += (
            f" [yellow]⚠ '{display}' is also carried by {top['name']} "
            f"({top['label']}, {top['mentions']}) — confirm the pin[/]"
        )
    if mine < THIN_MENTIONS:
        return f"[yellow]✓ thin[/]", f"[yellow]{detail} — bounds every strategy[/]", True
    return f"[green]✓ {label}[/]", detail, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--questions", type=Path, default=QUESTION_BANK)
    args = parser.parse_args()

    entries = yaml.safe_load(args.questions.read_text()) or []

    table = Table(header_style="bold")
    table.add_column("Question")
    table.add_column("Gold name")
    table.add_column("Pinned target")
    table.add_column("Status")
    table.add_column("Detail")

    problems = 0
    checked: dict[tuple[str, str, str], tuple[str, str, bool]] = {}

    for entry in entries:
        gold = entry.get("gold", []) or []
        targets = entry.get("targets", {}) or {}

        for display in gold:
            pin = targets.get(display)
            if not pin or len(pin) != 2:
                problems += 1
                table.add_row(entry["id"], display, "—",
                              "[red]✗ no target pin[/]",
                              "add a [canonicalName, label] pair under targets:")
                continue

            name, label = pin
            key = (display, name, label)
            if key not in checked:
                checked[key] = check_target(display, name, label)
            status, detail, ok = checked[key]
            if not ok:
                problems += 1
            table.add_row(entry["id"], display, f"{name} · {label}", status, detail)

        stray = set(targets) - set(gold)
        if stray:
            problems += 1
            table.add_row(entry["id"], ", ".join(sorted(stray)), "—",
                          "[red]✗ target without gold entry[/]", "")

        for anchor in entry.get("anchors", []) or []:
            resolved = resolve_entity(anchor)
            if resolved is None:
                problems += 1
                table.add_row(entry["id"], f"anchor: {anchor}", "—",
                              "[red]✗ unresolvable[/]", "")

    console.print(table)

    if problems == 0:
        console.print(
            "\n[bold green]All gold targets verify.[/] Every pin exists, is "
            "unique, and is the most-mentioned bearer of its name."
        )
        return 0

    console.print(f"\n[yellow]{problems} target(s) need attention[/] — "
                  "no benchmark number is quotable until this runs clean.")
    return 1


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

#!/usr/bin/env python3
"""Run the question bank through every strategy and score the results.

    python scripts/benchmark.py
    python scripts/benchmark.py --strategies vector ppr hybrid --k 8
    python scripts/benchmark.py --out results/run1

Reports answer-entity recall, redundancy, context size, and latency per
strategy. Per-question detail goes to CSV and JSON so the numbers can be
inspected rather than taken on faith.
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict
from pathlib import Path

import _bootstrap  # noqa: F401
import yaml
from rich.console import Console
from rich.table import Table

from graphrank import strategies
from graphrank.baseline import attach_graph_context
from graphrank.metrics import Scorecard, alias_map, score
from graphrank.projection import graph_exists

console = Console()

ROOT = Path(__file__).resolve().parent.parent
QUESTION_BANK = ROOT / "questions" / "questions.yaml"


def load_questions(path: Path, only: list[str] | None = None) -> list[dict]:
    entries = yaml.safe_load(path.read_text()) or []
    if only:
        entries = [e for e in entries if e.get("id") in only]
    return entries


def run_one(name: str, entry: dict, k: int) -> Scorecard:
    fn = strategies.get(name)
    options: dict = {"with_graph_context": True}
    if name == "paths" and entry.get("anchors"):
        options = {"anchors": entry["anchors"]}

    result = fn(entry["question"], k=k, **options)

    # Path retrieval skips graph-context hydration above; add it so redundancy
    # and recall see the same fields for every strategy.
    if not result.entities:
        attach_graph_context(result)

    gold = entry.get("gold", []) or []
    return score(result, gold, alias_map(gold))


def summarize(rows: list[Scorecard]) -> dict:
    return {
        "recall": statistics.mean(r.recall for r in rows) if rows else 0.0,
        "redundancy": statistics.mean(r.redundancy for r in rows) if rows else 0.0,
        "tokens": statistics.mean(r.context_tokens for r in rows) if rows else 0.0,
        "p50_ms": statistics.median(r.elapsed_ms for r in rows) if rows else 0.0,
        "p95_ms": (
            sorted(r.elapsed_ms for r in rows)[max(0, int(len(rows) * 0.95) - 1)]
            if rows
            else 0.0
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--questions", type=Path, default=QUESTION_BANK)
    parser.add_argument("--strategies", nargs="+", default=strategies.DEFAULT_ORDER)
    parser.add_argument("--only", nargs="+", help="run just these question ids")
    parser.add_argument("-k", type=int, default=8, help="context window size")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "benchmark")
    args = parser.parse_args()

    if not graph_exists():
        console.print("[red]✗[/] no GDS projection — run scripts/project_graph.py first")
        return 1

    entries = load_questions(args.questions, args.only)
    if not entries:
        console.print(f"[red]✗[/] no questions loaded from {args.questions}")
        return 1

    unlabeled = [e["id"] for e in entries if not e.get("gold")]
    if unlabeled:
        console.print(
            f"[yellow]![/] {len(unlabeled)} question(s) have no gold labels and will "
            f"score 0 recall: {', '.join(unlabeled)}"
        )

    console.print(
        f"Running [bold]{len(entries)}[/] questions × "
        f"[bold]{len(args.strategies)}[/] strategies (k={args.k}) …\n"
    )

    all_rows: list[Scorecard] = []
    by_strategy: dict[str, list[Scorecard]] = {name: [] for name in args.strategies}

    for entry in entries:
        console.print(f"[dim]{entry['id']}[/]  {entry['question']}")
        for name in args.strategies:
            try:
                card = run_one(name, entry, args.k)
            except Exception as exc:
                console.print(f"  [red]{name} failed: {exc}[/]")
                continue
            card.strategy = name
            by_strategy[name].append(card)
            all_rows.append(card)
            console.print(
                f"  {name:<10} recall {card.recall:5.1%}  "
                f"redundancy {card.redundancy:.2f}  {card.elapsed_ms:6.0f} ms"
            )

    # ── Summary ──────────────────────────────────────────────────────────────
    console.print()
    table = Table(title=f"Summary over {len(entries)} questions (k={args.k})",
                  header_style="bold")
    table.add_column("Strategy")
    table.add_column("Recall", justify="right")
    table.add_column("Δ vs vector", justify="right")
    table.add_column("Redundancy", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("p50 ms", justify="right")
    table.add_column("p95 ms", justify="right")

    stats = {name: summarize(rows) for name, rows in by_strategy.items() if rows}
    reference = stats.get("vector", {}).get("recall")

    for name in args.strategies:
        if name not in stats:
            continue
        s = stats[name]
        if reference is None or name == "vector":
            delta = "—"
        else:
            points = (s["recall"] - reference) * 100
            colour = "green" if points > 0 else ("red" if points < 0 else "white")
            delta = f"[{colour}]{points:+.1f} pts[/]"
        table.add_row(
            name,
            f"{s['recall']:.1%}",
            delta,
            f"{s['redundancy']:.3f}",
            f"{s['tokens']:,.0f}",
            f"{s['p50_ms']:,.0f}",
            f"{s['p95_ms']:,.0f}",
        )
    console.print(table)

    # ── Persist ──────────────────────────────────────────────────────────────
    args.out.parent.mkdir(parents=True, exist_ok=True)
    json_path = args.out.with_suffix(".json")
    csv_path = args.out.with_suffix(".csv")

    json_path.write_text(
        json.dumps(
            {
                "k": args.k,
                "question_count": len(entries),
                "summary": stats,
                "detail": [asdict(row) for row in all_rows],
            },
            indent=2,
        )
    )

    import csv as _csv

    with csv_path.open("w", newline="") as handle:
        writer = _csv.writer(handle)
        writer.writerow(
            ["strategy", "question", "recall", "redundancy", "tokens", "ms", "missed"]
        )
        for row in all_rows:
            writer.writerow(
                [
                    row.strategy,
                    row.question,
                    f"{row.recall:.4f}",
                    f"{row.redundancy:.4f}",
                    row.context_tokens,
                    f"{row.elapsed_ms:.1f}",
                    "; ".join(row.missed),
                ]
            )

    console.print(f"\n[green]✓[/] wrote {json_path} and {csv_path}")
    return 0


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

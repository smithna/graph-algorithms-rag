#!/usr/bin/env python3
"""Run the question bank through every strategy and score the results.

    NEO4J_DATABASE=lewisclark python scripts/benchmark.py
    python scripts/benchmark.py --strategies vector ppr hybrid --k 8
    python scripts/benchmark.py --out results/run1

Reports answer-entity recall, redundancy, context size, and latency per
strategy, overall and per question kind. The `kind: control` questions are the
honesty check: plain vector should win them, and the summary says so out loud
either way. Per-question detail goes to CSV, JSON, and a markdown report so
the numbers can be inspected rather than taken on faith.

Gold entities are (canonicalName, label) pins from questions.yaml — run
scripts/verify_questions.py first; a benchmark over unverified pins can score
decoy nodes without noticing.
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
from graphrank.metrics import Scorecard, gold_targets, score, surface_forms
from graphrank.projection import graph_exists

console = Console()

ROOT = Path(__file__).resolve().parent.parent
QUESTION_BANK = ROOT / "questions" / "questions.yaml"

#: The registry's report order, plus `paths` — it lives outside DEFAULT_ORDER
#: because it needs anchors to shine, but section 8 benchmarks every strategy.
BENCH_ORDER = [*strategies.DEFAULT_ORDER[:-1], "paths", "hybrid"]

KIND_ORDER = ["control", "connection", "authority", "thematic", "sequence"]


def load_questions(path: Path, only: list[str] | None = None) -> list[dict]:
    entries = yaml.safe_load(path.read_text()) or []
    if only:
        entries = [e for e in entries if e.get("id") in only]
    return entries


def run_one(name: str, entry: dict, k: int, targets, forms) -> Scorecard:
    fn = strategies.get(name)
    # path_strategy takes anchors, not with_graph_context — the old harness
    # leaked the latter into PathConfig whenever a question had no anchors.
    if name == "paths":
        options: dict = {"anchors": entry.get("anchors")}
    else:
        options = {"with_graph_context": True}

    result = fn(entry["question"], k=k, **options)

    # Path retrieval skips graph-context hydration above; add it so redundancy
    # and recall see the same fields for every strategy.
    if not result.entities:
        attach_graph_context(result)

    card = score(result, targets, forms)
    card.question_id = entry.get("id", "")
    card.kind = entry.get("kind", "")
    return card


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


def delta_vs_vector(
    name: str, rows: list[Scorecard], by_strategy: dict[str, list[Scorecard]]
) -> float | None:
    """Recall delta against vector over the SAME questions this strategy ran.

    A strategy that runs a subset (paths needs anchors) must not be compared
    against vector's mean over the full bank — that difference would measure
    which questions were skipped, not retrieval quality.
    """
    if name == "vector":
        return None
    vec = {r.question_id: r.recall for r in by_strategy.get("vector", [])}
    shared = [(r.recall, vec[r.question_id]) for r in rows if r.question_id in vec]
    if not shared:
        return None
    mine = statistics.mean(s for s, _ in shared)
    theirs = statistics.mean(v for _, v in shared)
    return (mine - theirs) * 100


def kinds_present(rows: list[Scorecard]) -> list[str]:
    seen = {r.kind for r in rows if r.kind}
    return [k for k in KIND_ORDER if k in seen] + sorted(seen - set(KIND_ORDER))


def kind_recall(rows: list[Scorecard]) -> dict[str, float]:
    by_kind: dict[str, list[float]] = {}
    for r in rows:
        by_kind.setdefault(r.kind, []).append(r.recall)
    return {k: statistics.mean(v) for k, v in by_kind.items()}


def control_verdict(by_strategy: dict[str, list[Scorecard]]) -> list[str]:
    """Plain-language check: does vector still win the control questions?"""
    vector_rows = [r for r in by_strategy.get("vector", []) if r.kind == "control"]
    if not vector_rows:
        return ["no control questions were run — the honesty check is missing."]
    v = statistics.mean(r.recall for r in vector_rows)
    lines = [f"vector's mean recall on control questions: {v:.1%}"]
    for name, rows in by_strategy.items():
        if name == "vector":
            continue
        controls = [r for r in rows if r.kind == "control"]
        if not controls:
            continue
        s = statistics.mean(r.recall for r in controls)
        if s < v:
            lines.append(
                f"⚠ {name} loses a control question to vector "
                f"({s:.1%} vs {v:.1%}) — if this strategy also wins hard "
                f"questions, that trade must be reported, not tuned away."
            )
    if len(lines) == 1:
        lines.append(
            "every strategy matches or beats vector on the controls — "
            "no strategy pays for hard questions with easy ones."
        )
    return lines


def write_markdown(
    path: Path,
    entries: list[dict],
    k: int,
    args_strategies: list[str],
    stats: dict[str, dict],
    by_strategy: dict[str, list[Scorecard]],
    all_rows: list[Scorecard],
) -> None:
    lines: list[str] = []
    add = lines.append

    add(f"# Benchmark — {len(entries)} questions × "
        f"{len([s for s in args_strategies if s in stats])} strategies (k={k})")
    add("")
    add("Answer-entity recall over (canonicalName, label) pins verified by "
        "`verify_questions.py`. A gold entity counts as found if its node has "
        "a MENTIONED_IN edge into a retrieved passage or any of its surface "
        "forms appears in the passage text. Entity recall says the context "
        "*contains the facts* — it never says the answer is right.")
    add("")

    add("## Summary")
    add("")
    add("| strategy | n | recall | Δ vs vector¹ | redundancy | tokens | p50 ms | p95 ms |")
    add("|---|---|---|---|---|---|---|---|")
    for name in args_strategies:
        if name not in stats:
            continue
        s = stats[name]
        points = delta_vs_vector(name, by_strategy[name], by_strategy)
        delta = "—" if points is None else f"{points:+.1f} pts"
        add(f"| {name} | {len(by_strategy[name])} | {s['recall']:.1%} | {delta} "
            f"| {s['redundancy']:.3f} | {s['tokens']:,.0f} | {s['p50_ms']:,.0f} "
            f"| {s['p95_ms']:,.0f} |")
    add("")
    add("¹ Δ is computed over the questions that strategy actually ran "
        "(`paths` runs only where the question pins two anchors — section 7's "
        "own trigger condition).")
    add("")

    kinds = kinds_present(all_rows)
    counts = {kind: len({r.question_id for r in all_rows if r.kind == kind})
              for kind in kinds}
    add("## Recall by question kind")
    add("")
    add("| strategy | " + " | ".join(f"{k} ({counts[k]})" for k in kinds) + " |")
    add("|---|" + "---|" * len(kinds))
    for name in args_strategies:
        if name not in stats:
            continue
        per_kind = kind_recall(by_strategy[name])
        add(f"| {name} | " + " | ".join(
            f"{per_kind[k]:.1%}" if k in per_kind else "—" for k in kinds
        ) + " |")
    add("")
    add("Small samples per kind — treat single-question flips as noise; "
        "the per-question grid below is the ground truth.")
    add("")

    add("## The control check")
    add("")
    for line in control_verdict(by_strategy):
        add(f"- {line}")
    add("")

    add("## Per-question recall")
    add("")
    ordered = [e["id"] for e in entries]
    ran = [s for s in args_strategies if s in stats]
    add("| question | kind | gold | " + " | ".join(ran) + " |")
    add("|---|---|---|" + "---|" * len(ran))
    cards = {(r.question_id, r.strategy): r for r in all_rows}
    for entry in entries:
        qid = entry["id"]
        cells = []
        for name in ran:
            card = cards.get((qid, name))
            cells.append(f"{card.recall:.0%}" if card else "·")
        add(f"| {qid} | {entry.get('kind','')} | {len(entry.get('gold') or [])} | "
            + " | ".join(cells) + " |")
    add("")

    add("## Misses")
    add("")
    missed_any = False
    for entry in entries:
        qid = entry["id"]
        rows = [r for r in all_rows if r.question_id == qid and r.missed]
        if not rows:
            continue
        missed_any = True
        per = ", ".join(f"{r.strategy}: {'/'.join(r.missed)}" for r in rows)
        add(f"- **{qid}** — {per}")
    if not missed_any:
        add("- none — every strategy found every gold entity (suspicious; "
            "check the gold set is not too easy).")
    add("")

    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--questions", type=Path, default=QUESTION_BANK)
    parser.add_argument("--strategies", nargs="+", default=BENCH_ORDER)
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
        targets = gold_targets(entry)
        forms = surface_forms(targets)
        for name in args.strategies:
            # Path retrieval triggers off question shape — two pinned anchors
            # (section 7's own architecture). On this database the anchor
            # inference fallback cannot run at all: Person/Place/WaterBody/
            # NativeNation nodes carry no embeddings, so there is nothing to
            # infer from. Scoring paths on anchor-less questions would measure
            # that gap, not the strategy.
            if name == "paths" and not entry.get("anchors"):
                console.print(f"  {'paths':<12} [dim]skipped — no anchors[/]")
                continue
            try:
                card = run_one(name, entry, args.k, targets, forms)
            except Exception as exc:
                console.print(f"  [red]{name} failed: {exc}[/]")
                continue
            card.strategy = name
            by_strategy[name].append(card)
            all_rows.append(card)
            console.print(
                f"  {name:<12} recall {card.recall:5.1%}  "
                f"redundancy {card.redundancy:.2f}  {card.elapsed_ms:6.0f} ms"
            )

    # ── Summary ──────────────────────────────────────────────────────────────
    console.print()
    table = Table(title=f"Summary over {len(entries)} questions (k={args.k})",
                  header_style="bold")
    table.add_column("Strategy")
    table.add_column("n", justify="right")
    table.add_column("Recall", justify="right")
    table.add_column("Δ vs vector", justify="right")
    table.add_column("Redundancy", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("p50 ms", justify="right")
    table.add_column("p95 ms", justify="right")

    stats = {name: summarize(rows) for name, rows in by_strategy.items() if rows}

    for name in args.strategies:
        if name not in stats:
            continue
        s = stats[name]
        points = delta_vs_vector(name, by_strategy[name], by_strategy)
        if points is None:
            delta = "—"
        else:
            colour = "green" if points > 0 else ("red" if points < 0 else "white")
            delta = f"[{colour}]{points:+.1f} pts[/]"
        table.add_row(
            name,
            str(len(by_strategy[name])),
            f"{s['recall']:.1%}",
            delta,
            f"{s['redundancy']:.3f}",
            f"{s['tokens']:,.0f}",
            f"{s['p50_ms']:,.0f}",
            f"{s['p95_ms']:,.0f}",
        )
    console.print(table)
    console.print("[dim]Δ is computed over the questions each strategy "
                  "actually ran; paths runs only where anchors are pinned.[/]")

    console.print("\n[bold]Control check[/]")
    for line in control_verdict(by_strategy):
        console.print(f"  {line}")

    # ── Persist ──────────────────────────────────────────────────────────────
    args.out.parent.mkdir(parents=True, exist_ok=True)
    json_path = args.out.with_suffix(".json")
    csv_path = args.out.with_suffix(".csv")
    md_path = args.out.with_suffix(".md")

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
            ["strategy", "question_id", "kind", "recall", "redundancy",
             "tokens", "ms", "missed"]
        )
        for row in all_rows:
            writer.writerow(
                [
                    row.strategy,
                    row.question_id,
                    row.kind,
                    f"{row.recall:.4f}",
                    f"{row.redundancy:.4f}",
                    row.context_tokens,
                    f"{row.elapsed_ms:.1f}",
                    "; ".join(row.missed),
                ]
            )

    write_markdown(md_path, entries, args.k, args.strategies, stats,
                   by_strategy, all_rows)

    console.print(f"\n[green]✓[/] wrote {json_path}, {csv_path}, and {md_path}")
    return 0


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

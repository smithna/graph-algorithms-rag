#!/usr/bin/env python3
"""Entity resolution, read-only: node similarity + WCC, with zero writes.

    python scripts/demo_resolution.py
    python scripts/demo_resolution.py --label NativeNation
    python scripts/demo_resolution.py --signals string alias --limit 20
    python scripts/demo_resolution.py --adjudicate --max-calls 25
    python scripts/demo_resolution.py --check-roster

The talk's claim is that graph structure finds duplicates that string matching
cannot, and that WCC turns pairwise guesses into whole identities. This script
demonstrates both against the live database and **writes nothing** — proved at
the end by diffing a before/after snapshot rather than by asserting it.

The run has five movements:

  1. Receipts        the `aliases` arrays past resolution already produced
  2. Candidates      three signals proposing duplicate pairs, live
  3. Closure         real gds.wcc.stream over pairs that were never written
  4. Scoring         precision against the corps roster, recall replayed
                     from alias arrays
  5. Audit           node/relationship counts and alias samples, diffed
"""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
from rich.console import Console
from rich.table import Table

from graphrank import adjudicate as adj
from graphrank import resolution as res

console = Console()

SIGNAL_STYLE = {
    "cooccurrence": "cyan",
    "string": "yellow",
    "alias": "magenta",
}


def _signals(pair: res.CandidatePair) -> str:
    return " ".join(
        f"[{SIGNAL_STYLE.get(s, 'white')}]{s}[/]" for s in sorted(pair.signals)
    )


# ── 1. Receipts ───────────────────────────────────────────────────────────────


def show_receipts(label: str, limit: int = 6) -> None:
    """The alias arrays are what past resolution already merged."""
    rows = res.read_query(
        f"""
        MATCH (n:{label})
        WHERE n.aliases IS NOT NULL AND size(n.aliases) > 1
        RETURN n.canonicalName AS name,
               n.aliases       AS aliases,
               count {{ (n)-[:MENTIONED_IN]->(:Chunk) }} AS mentions
        ORDER BY size(n.aliases) DESC, mentions DESC
        LIMIT $limit
        """,
        limit=limit,
    )
    if not rows:
        return

    table = Table(
        title=f"Already merged — {label} nodes and the surface forms they absorbed",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Canonical", style="bold")
    table.add_column("n", justify="right")
    table.add_column("Aliases")
    for row in rows:
        aliases = row["aliases"]
        shown = ", ".join(aliases[:7])
        if len(aliases) > 7:
            shown += f"  (+{len(aliases) - 7} more)"
        table.add_row(row["name"], str(len(aliases)), shown)
    console.print(table)
    console.print(
        "[dim]Each alias was once a separate node. Retrieval for any one of them "
        "used to miss everything filed under the others.[/]\n"
    )


# ── 2. Candidates ─────────────────────────────────────────────────────────────


def show_candidates(pairs: list[res.CandidatePair], limit: int) -> None:
    breakdown = res.signal_breakdown(pairs)
    table = Table(
        title=f"Candidate duplicate pairs that survived resolution  ({breakdown['total']} total)",
        show_header=True,
        header_style="bold",
    )
    table.add_column("#", justify="right", style="dim")
    table.add_column("Pair")
    table.add_column("Signals")
    table.add_column("cosine", justify="right")
    table.add_column("mentions", justify="right", style="dim")

    for i, pair in enumerate(pairs[:limit], 1):
        similarity = f"{pair.similarity:.3f}" if pair.similarity is not None else "—"
        table.add_row(
            str(i),
            pair.describe(),
            _signals(pair),
            similarity,
            f"{pair.left.mentions}/{pair.right.mentions}",
        )
    console.print(table)

    parts = [
        f"[{SIGNAL_STYLE.get(k, 'white')}]{k}[/] {v}"
        for k, v in sorted(breakdown.items())
        if k not in ("total", "multi-signal")
    ]
    console.print(
        "  " + " · ".join(parts)
        + f" · [bold]multi-signal[/] {breakdown.get('multi-signal', 0)}"
    )
    console.print(
        "[dim]A pair two independent signals agree on is far stronger evidence "
        "than either alone.[/]\n"
    )


# ── 3. Transitive closure ─────────────────────────────────────────────────────


def show_components(
    components: list[res.Component], title: str, note: str, limit: int = 12
) -> None:
    if not components:
        console.print(f"[dim]{title}: no components.[/]\n")
        return

    table = Table(title=title, show_header=True, header_style="bold")
    table.add_column("size", justify="right")
    table.add_column("Members merged by transitive closure")
    for component in components[:limit]:
        members = component.describe()
        if len(members) > 150:
            members = members[:147] + " …"
        table.add_row(str(component.size), members)
    console.print(table)
    if len(components) > limit:
        console.print(f"[dim]  … and {len(components) - limit} more[/]")
    console.print(f"[dim]{note}[/]\n")


# ── 4. Scoring ────────────────────────────────────────────────────────────────


def show_scores(
    pairs: list[res.CandidatePair], gold: res.GoldSet, present: set[str], limit: int
) -> res.Scores:
    scores = res.score(pairs, gold, present)

    table = Table(
        title="Scored against the corps-member identity gold set",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Measure")
    table.add_column("Value", justify="right")
    table.add_column("Meaning", style="dim")

    table.add_row(
        "split identities",
        str(len(scores.split_identities)),
        "corps members still spread across >1 node",
    )
    table.add_row(
        "duplicate pairs to find",
        str(scores.recall_denominator),
        "recall denominator: within-identity pairs in the graph",
    )
    table.add_row("", "", "")
    table.add_row(
        "evaluable pairs",
        str(scores.evaluable),
        "both endpoints are known surface forms",
    )
    table.add_row(
        "true positives",
        f"[green]{len(scores.true_positives)}[/]",
        "same person, correctly proposed",
    )
    table.add_row(
        "false positives",
        f"[red]{len(scores.false_positives)}[/]",
        "different people, wrongly proposed",
    )
    precision = scores.precision
    recall = scores.recall
    table.add_row(
        "[bold]precision[/]",
        f"[bold]{precision:.2f}[/]" if precision is not None else "n/a",
        "on the labelled slice only",
    )
    table.add_row(
        "[bold]recall[/]",
        f"[bold]{recall:.2f}[/]" if recall is not None else "n/a",
        "of duplicate pairs that exist in the graph",
    )
    table.add_row(
        "hard negatives proposed",
        f"{len(scores.hard_negatives_caught)}/{scores.hard_negatives_total}",
        "known-different pairs the signals proposed anyway",
    )
    console.print(table)

    if scores.true_positives:
        console.print(
            "  [green]Found[/] — duplicates that survived both resolution passes:"
        )
        for pair in scores.true_positives[:limit]:
            console.print(f"    [green]✓[/] {pair.describe():52} {_signals(pair)}")
        if len(scores.true_positives) > limit:
            console.print(f"    [dim]… and {len(scores.true_positives) - limit} more[/]")

    if scores.false_positives:
        console.print("\n  [red]Wrong[/] — different people proposed as one:")
        for pair in scores.false_positives[:limit]:
            console.print(f"    [red]✗[/] {pair.describe():52} {_signals(pair)}")
        if len(scores.false_positives) > limit:
            console.print(f"    [dim]… and {len(scores.false_positives) - limit} more[/]")

    if scores.missed:
        console.print("\n  [yellow]Missed[/] — real duplicates no signal proposed:")
        for person, left, right in scores.missed[:limit]:
            console.print(f"    [yellow]·[/] {left}  /  {right}   [dim]({person})[/]")
        if len(scores.missed) > limit:
            console.print(f"    [dim]… and {len(scores.missed) - limit} more[/]")

    console.print()
    return scores


def show_recall(label: str) -> None:
    recall = res.alias_recall(label)
    if not recall.total:
        console.print("[dim]No alias pairs to replay.[/]\n")
        return

    table = Table(
        title="Recall, replayed from alias arrays",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Signal")
    table.add_column("Caught", justify="right")
    table.add_column("of", justify="right", style="dim")
    table.add_row("Jaro-Winkler", str(recall.by_jaro), str(recall.total))
    table.add_row("token containment", str(recall.by_containment), str(recall.total))
    table.add_row("double metaphone", str(recall.by_metaphone), str(recall.total))
    table.add_row(
        "[bold]any string signal[/]",
        f"[bold]{recall.caught}[/]",
        str(recall.total),
    )
    console.print(table)
    if recall.recall is not None:
        console.print(f"  string-ladder recall: [bold]{recall.recall:.2f}[/]")
    console.print(
        "[dim]String signals only. A merged alias has no co-occurrence vector of "
        "its own, so the graph signal cannot be replayed — this is a floor on the "
        "pipeline's recall, not an estimate of it.[/]"
    )
    if recall.missed:
        console.print(f"  [yellow]missed {len(recall.missed)}[/], e.g.:")
        for canonical, alias in recall.missed[:6]:
            console.print(f"    [yellow]·[/] {canonical}  ✗  {alias}")
        console.print(
            "[dim]    These are what the graph signal is for: no string ladder "
            "reaches them.[/]"
        )
    console.print()


# ── 5. Write audit ────────────────────────────────────────────────────────────


def show_audit(before: res.Snapshot, after: res.Snapshot) -> bool:
    changes = before.diff(after)

    table = Table(title="Write audit", show_header=True, header_style="bold")
    table.add_column("Measure")
    table.add_column("Before", justify="right")
    table.add_column("After", justify="right")
    table.add_column("", justify="center")
    for name, b, a in (
        ("nodes", before.nodes, after.nodes),
        ("relationships", before.relationships, after.relationships),
        ("entities", before.entities, after.entities),
        ("distinct labels", len(before.labels), len(after.labels)),
        ("distinct rel types", len(before.rel_types), len(after.rel_types)),
        ("alias arrays sampled", len(before.alias_sample), len(after.alias_sample)),
    ):
        table.add_row(
            name,
            f"{b:,}",
            f"{a:,}",
            "[green]=[/]" if b == a else "[red]≠[/]",
        )
    console.print(table)

    if changes:
        console.print("[bold red]✗ The database changed:[/]")
        for change in changes:
            console.print(f"    [red]{change}[/]")
        return False

    console.print(
        "[bold green]✓ Zero writes.[/] Counts, per-label and per-type totals, and "
        "every sampled alias array are byte-identical."
    )
    console.print(
        "[dim]  Not merely unchanged — unchangeable: every query above ran in a "
        "read transaction, so the server rejects a write with "
        "Neo.ClientError.Statement.AccessMode before it reaches the store.[/]"
    )
    return True


# ── Signal comparison ─────────────────────────────────────────────────────────


def compare_signals(
    pairs: list[res.CandidatePair],
    inventory: dict[int, res.EntityRef],
    gold: res.GoldSet,
    present: set[str],
) -> None:
    """Score each signal mix side by side.

    Read the warning this prints before quoting any of these numbers. On a graph
    that has already been through `disambiguate.py` the comparison is biased in a
    known direction — see the module docstring of `graphrank/resolution.py`.
    """
    table = Table(
        title="What each signal actually contributes",
        show_header=True,
        header_style="bold",
    )
    table.add_column("Signals")
    table.add_column("pairs", justify="right")
    table.add_column("TP", justify="right")
    table.add_column("FP", justify="right")
    table.add_column("precision", justify="right")
    table.add_column("recall", justify="right")
    table.add_column("largest WCC", justify="right")

    mixes = [
        ("string + alias", {"string", "alias"}),
        ("co-occurrence only", {"cooccurrence"}),
        ("all three", None),
    ]
    for name, signals in mixes:
        subset = res.filter_pairs(pairs, signals=signals)
        if not subset:
            continue
        scores = res.score(subset, gold, present)
        components = res.components(subset, inventory)
        largest = max((c.size for c in components), default=0)
        precision = scores.precision
        recall = scores.recall
        table.add_row(
            name,
            str(len(subset)),
            f"[green]{len(scores.true_positives)}[/]",
            f"[red]{len(scores.false_positives)}[/]",
            f"{precision:.2f}" if precision is not None else "n/a",
            f"{recall:.2f}" if recall is not None else "n/a",
            str(largest),
        )
    console.print(table)

    if _already_disambiguated():
        console.print(
            "  [bold yellow]![/] This graph has already been through "
            "[bold]disambiguate.py[/], so the duplicates left are the ones that "
            "run missed.\n    Its Jaro-Winkler and metaphone branches were "
            "inverted and never fired, while its co-occurrence\n    branch worked "
            "and swept the corpus — so these numbers flatter the string ladder "
            "and\n    penalise co-occurrence, by construction.\n"
            "    Build a pre-disambiguation graph to measure this honestly; see "
            "docs/talk-outline.md.\n"
        )

    # The comparison that matters: does the graph signal reach anything the
    # string ladder cannot?
    string_alias = {p.key for p in res.filter_pairs(pairs, signals={"string", "alias"})}
    cooccurrence_only = [
        p
        for p in res.filter_pairs(pairs, signals={"cooccurrence"})
        if p.key not in string_alias
    ]
    lookup = gold.name_to_identity
    excluded = gold.excluded()
    unique_hits = [
        p
        for p in cooccurrence_only
        if p.names[0] not in excluded
        and p.names[1] not in excluded
        and lookup.get(p.names[0]) is not None
        and lookup.get(p.names[0]) == lookup.get(p.names[1])
    ]
    console.print(
        f"  Co-occurrence proposed [bold]{len(cooccurrence_only)}[/] pairs the string "
        f"ladder did not. Of those, [bold]{len(unique_hits)}[/] are real duplicates."
    )
    for pair in unique_hits[:8]:
        console.print(f"    [green]✓[/] {pair.describe()}")
    console.print()


def _already_disambiguated() -> bool:
    """Has `disambiguate.py` run on this graph?

    The obvious test — "do entity nodes carry `aliases`?" — does not work, and
    the reason is worth knowing: `extract.py` populates `aliases` itself. The
    extractor assigns a canonical name per mention and files the raw surface
    form alongside it, so even a freshly extracted graph has `Capt. Lewis` and
    `Chabonah` sitting in alias arrays. There is no state in this pipeline where
    entities are wholly unresolved.

    What does discriminate is `corpsMember`, which `tag_corps_members.py` sets
    in step 14 — after both disambiguation passes. Its presence means the whole
    build ran; its absence means the graph stopped short of it.
    """
    row = res.read_query(
        """
        CALL { MATCH (p:Person) WHERE p.corpsMember IS NOT NULL
               RETURN count(p) AS tagged }
        CALL { MATCH ()-[r:IS_SAME_ENTITY_AS]->() RETURN count(r) AS pending }
        RETURN tagged, pending
        """
    )[0]
    return row["tagged"] > 0 and row["pending"] == 0


# ── Roster check ──────────────────────────────────────────────────────────────


def check_roster() -> int:
    gold = res.load_gold()
    present, absent = res.roster_presence(gold)
    console.rule("[bold]Corps roster vs the graph")
    console.print(f"  roster entries : {len(gold.roster)}")
    console.print(f"  present        : [green]{len(present)}[/]")
    console.print(f"  absent         : [yellow]{len(absent)}[/]")
    if absent:
        console.print("\n  Not found in the graph (excluded from scoring):")
        for name in sorted(absent):
            console.print(f"    [yellow]·[/] {name}")
        console.print(
            "\n[dim]  A corps member the journals never name is not a resolution "
            "failure, so these are excluded rather than counted as misses.[/]"
        )
    return 0


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--label", default="Person", choices=res.LABELS)
    parser.add_argument(
        "--signals",
        nargs="+",
        choices=["cooccurrence", "string", "alias"],
        default=None,
        help="restrict candidate generation to these signals (default: all)",
    )
    parser.add_argument("--limit", type=int, default=15, help="rows per table")
    parser.add_argument(
        "--adjudicate",
        action="store_true",
        help="ask an LLM to confirm each pair (costs money; off by default)",
    )
    parser.add_argument("--model", default=adj.DEFAULT_MODEL)
    parser.add_argument(
        "--max-calls",
        type=int,
        default=adj.DEFAULT_MAX_CALLS,
        help="hard cap on LLM calls; cached verdicts do not count",
    )
    parser.add_argument(
        "--check-roster",
        action="store_true",
        help="report which roster names exist in the graph, then exit",
    )
    parser.add_argument("--no-receipts", action="store_true")
    parser.add_argument(
        "--compare-signals",
        action="store_true",
        help="score each signal mix side by side (Person only)",
    )
    args = parser.parse_args()

    if args.check_roster:
        return check_roster()

    label = args.label

    # ── Snapshot before anything runs ────────────────────────────────────────
    before = res.snapshot()

    console.rule(f"[bold]Entity resolution — {label}, read-only")
    console.print(
        f"[dim]{before.nodes:,} nodes · {before.relationships:,} relationships · "
        f"{before.entities:,} resolvable entities[/]\n"
    )

    if not args.no_receipts:
        show_receipts(label)

    # ── Candidate generation ─────────────────────────────────────────────────
    inventory = res.entities()
    graph = None
    wanted = set(args.signals) if args.signals else None
    needs_cooccurrence = wanted is None or "cooccurrence" in wanted

    try:
        if needs_cooccurrence:
            graph = res.build_cooccurrence_graph()
            console.print(
                f"[dim]co-occurrence projection: {graph.node_count():,} entities, "
                f"{graph.relationship_count():,} weighted edges[/]\n"
            )

        pairs = res.candidates(label, graph=graph, inventory=inventory)
        pairs = res.filter_pairs(pairs, signals=wanted)
        if not pairs:
            console.print("[yellow]No candidate pairs.[/]")
            return 0

        show_candidates(pairs, args.limit)

        # ── Transitive closure ───────────────────────────────────────────────
        raw_components = res.components(pairs, inventory)
        largest = max((c.size for c in raw_components), default=0)
        show_components(
            raw_components,
            f"WCC over all {len(pairs)} candidate pairs",
            f"Largest component: {largest} nodes. WCC answers 'are these connected "
            "at all' — run it over unadjudicated candidates and one wrong edge "
            "welds two identities together for good.",
        )

        # ── Adjudication ─────────────────────────────────────────────────────
        if args.adjudicate:
            console.print(
                f"[bold]Adjudicating[/] up to {args.max_calls} pairs with "
                f"{args.model} …"
            )
            verdicts = adj.adjudicate(
                pairs,
                enabled=True,
                model=args.model,
                max_calls=args.max_calls,
            )
            summary = adj.summarize(verdicts)
            console.print(
                "  "
                + " · ".join(f"{k} {v}" for k, v in sorted(summary.items()))
                + "\n"
            )
            confirmed = adj.confirmed_pairs(verdicts)
            if confirmed:
                show_components(
                    res.components(confirmed, inventory),
                    f"WCC over {len(confirmed)} adjudicated pairs",
                    "This is the ordering the build pipeline uses: candidates for "
                    "recall, adjudication for precision, closure last.",
                )
        else:
            console.print(
                "[dim]Adjudication is off. Re-run with --adjudicate to confirm "
                "pairs with an LLM before closure (costs money).[/]\n"
            )

        # ── Scoring ──────────────────────────────────────────────────────────
        if label == "Person":
            gold = res.load_gold()
            present, absent = res.roster_presence(gold)
            all_gold_names = {n for names in gold.identities.values() for n in names}
            present = res.present_names(all_gold_names)
            if absent:
                console.print(
                    f"[dim]{len(absent)} of {len(gold.roster)} roster names are absent "
                    f"from the graph and excluded from scoring "
                    f"(--check-roster to list them).[/]\n"
                )
            if args.compare_signals:
                compare_signals(pairs, inventory, gold, present)
            show_scores(pairs, gold, present, args.limit)
            show_recall(label)

    finally:
        if graph is not None:
            res.drop_graph(res.COOCCURRENCE_GRAPH)

    # ── Audit ────────────────────────────────────────────────────────────────
    after = res.snapshot()
    console.rule()
    clean = show_audit(before, after)
    return 0 if clean else 1


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

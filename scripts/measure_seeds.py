#!/usr/bin/env python3
"""Seed-selection quality: does the seeder pick the entities the question names?

    python scripts/measure_seeds.py                # the full bank, both seeders
    python scripts/measure_seeds.py --only sacagawea-interpreting
    python scripts/measure_seeds.py --show-seeds   # every seed, per question

Why this measurement exists, and why it is *allowed* to exist
─────────────────────────────────────────────────────────────
Every attempt to tune section 5's retrieval died in finding 5d-quinquies: four
hand-judged passages, pinned at the ceiling of the entity percentile, behind a
binary top-8 threshold — the metric measured noise. Seed *selection* is
different. "The question names Sacagawea; is a Sacagawea node in the seed set?"
is exact set membership against ground truth you can check by reading one line.
No relevance proxy, no ranking, no threshold. It is the one part of this
pipeline where quality is measurable today.

Ground truth: for each bank question, the entities its *text explicitly names*
(not what a correct answer would involve — that is the gold set's job, and gold
is measured separately as a secondary view). Each named entity is an accept-set
of canonical names, because extraction sometimes stored the real thing under a
sibling node (there is no FORT CLATSOP; the graph has CLATSOP VILLAGE), and
because duplicates are still unresolved (either SACAGAWEA node counts — that is
section 4's point). Phrases the graph has NO node for (the keelboat) are listed
as ``absent`` and reported separately: a seeder cannot be dinged for the
extraction's gaps, but the audience should see them — they are limit #3.

Read the seeds, not just the counts: --show-seeds prints every seed with its
degree so the WISDOM-RIVER class of failure is visible as a name, not a number.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import _bootstrap  # noqa: F401
import yaml
from rich.console import Console
from rich.table import Table

from graphrank import pagerank
from graphrank.config import read_query
from graphrank.embedding import embed
from graphrank.pagerank import ExpandConfig
from graphrank.projection import project_mentions

console = Console()
ROOT = Path(__file__).resolve().parent.parent
QUESTION_BANK = ROOT / "questions" / "questions.yaml"

# ── Ground truth: what each question's text names ─────────────────────────────
#
# Checkable by reading the question string. `named` maps each phrase the
# question uses to the canonical names that count as resolving it (verified
# against the live graph — every listed name exists). `absent` records phrases
# the graph has no node for at all, verified by full-text search over every
# label; they demonstrate the extraction bound rather than seeder failure.
#
# Questions that name nothing (`named: {}`) are the fallback path by design:
# thematic questions ask about a *kind* of thing, and there is no name to look
# up. The decomposed seeder must return nothing rather than hallucinate.
QUESTION_NAMED: dict[str, dict] = {
    "shoshone-horses": {
        "named": {
            "Shoshone": {"SHOSHONE"},
            # The question says "horses". The animal node is EQUUS CABALLUS;
            # extraction also filed horses-as-goods under Supply HORSE. Either
            # is the thing the question names.
            "horses": {"EQUUS CABALLUS", "HORSE"},
        },
        "absent": [],
    },
    "sacagawea-interpreting": {
        # "Native nations" is a category, not a name.
        "named": {"Sacagawea": {"SACAGAWEA"}},
        "absent": [],
    },
    "charbonneau-role": {
        "named": {"Toussaint Charbonneau": {"TOUSSAINT CHARBONNEAU"}},
        "absent": [],
    },
    "grizzly-encounters": {
        "named": {"grizzly bears": {"URSUS ARCTOS HORRIBILIS"}},
        "absent": [],
    },
    "ordway-responsibilities": {
        "named": {"Sergeant Ordway": {"JOHN ORDWAY"}},
        "absent": [],
    },
    "great-falls-portage": {
        # No GREAT FALLS place exists. The falls are FALLS OF MISSOURI (df 3);
        # a GREAT FALLS Event (df 2) also exists. Both are thin — the corpus's
        # biggest episode is barely an entity, which is its own finding.
        "named": {"Great Falls": {"FALLS OF MISSOURI", "GREAT FALLS"}},
        "absent": [],
    },
    "fort-clatsop-winter": {
        # No FORT CLATSOP node; the place extraction built is CLATSOP VILLAGE.
        "named": {"Fort Clatsop": {"CLATSOP VILLAGE"}},
        "absent": [],
    },
    "trade-goods": {"named": {}, "absent": []},
    "food-sources": {"named": {}, "absent": []},
    "illness-and-injury": {"named": {}, "absent": []},
    "before-floyd-death": {
        "named": {"Sergeant Floyd": {"CHARLES FLOYD"}},
        "absent": [],
    },
    "pacific-arrival": {
        "named": {"the Pacific": {"PACIFIC OCEAN"}},
        "absent": [],
    },
    "keelboat-return": {
        "named": {"the Missouri": {"MISSOURI RIVER", "MISSOURI"}},
        # Verified: no node matches "keelboat" (or "barge") in any full-text
        # index. The question's central object was never extracted.
        "absent": ["the keelboat"],
    },
    "prairie-dog": {
        "named": {"prairie dog": {"CYNOMYS LUDOVICIANUS"}},
        "absent": [],
    },
}


def seed_degrees(node_ids: list[int]) -> dict[int, int]:
    if not node_ids:
        return {}
    rows = read_query(
        """
        UNWIND $ids AS nid
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE id(e) = nid
        RETURN nid AS nodeId, count(DISTINCT c) AS df
        """,
        ids=node_ids,
    )
    return {r["nodeId"]: r["df"] for r in rows}


def run_seeder(name: str, question: str, config: ExpandConfig):
    """Return (seeds, elapsed_ms, fallback_used, mentions_debug)."""
    t0 = time.perf_counter()
    if name == "semantic":
        seeds = pagerank.entity_seeds(embed(question), config=config)
        fallback, mentions = False, None
    else:
        seeds, debug = pagerank.decomposed_entity_seeds(question, config=config)
        mentions = debug["mentions"]
        fallback = not seeds
        if fallback:
            seeds = pagerank.entity_seeds(embed(question), config=config)
    return seeds, (time.perf_counter() - t0) * 1000, fallback, mentions


def coverage(seeds, named: dict[str, set[str]]):
    """Which named phrases have a seed in their accept-set, and which seeds are extra."""
    seed_names = {s.name for s in seeds}
    hit = {phrase for phrase, accept in named.items() if accept & seed_names}
    accepted_names = set().union(*named.values()) if named else set()
    extra = [s for s in seeds if s.name not in accepted_names]
    return hit, extra


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--only", help="run a single question id")
    parser.add_argument("--show-seeds", action="store_true",
                        help="print every seed with label, degree, and weight")
    parser.add_argument("--model", default="", help="decomposition model override")
    args = parser.parse_args()

    project_mentions()
    entries = yaml.safe_load(QUESTION_BANK.read_text()) or []
    if args.only:
        entries = [e for e in entries if e["id"] == args.only]
        if not entries:
            console.print(f"[red]no question with id {args.only!r}[/]")
            return 1

    config = ExpandConfig(decompose_model=args.model)

    table = Table(title="Seed selection vs. what the question names",
                  header_style="bold", show_lines=False)
    table.add_column("question")
    table.add_column("seeder")
    table.add_column("named hit", justify="right")
    table.add_column("extra seeds", justify="right")
    table.add_column("gold hit", justify="right")
    table.add_column("ms", justify="right")
    table.add_column("notes")

    totals = {  # per seeder: [named hit, named total, extra, gold hit, gold total]
        "semantic": [0, 0, 0, 0, 0],
        "decomposed": [0, 0, 0, 0, 0],
    }

    for entry in entries:
        qid, question = entry["id"], entry["question"]
        truth = QUESTION_NAMED.get(qid)
        if truth is None:
            console.print(f"[yellow]{qid} has no ground truth entry — skipped[/]")
            continue
        named: dict[str, set[str]] = truth["named"]
        gold = set(entry.get("gold", []))

        for seeder in ("semantic", "decomposed"):
            seeds, ms, fallback, mentions = run_seeder(seeder, question, config)
            hit, extra = coverage(seeds, named)
            seed_names = {s.name for s in seeds}
            gold_hit = gold & seed_names

            notes = []
            if fallback:
                notes.append("fell back to semantic (question names nothing)")
            if truth["absent"]:
                notes.append(f"not in graph: {', '.join(truth['absent'])}")
            if seeder == "decomposed" and mentions and args.show_seeds:
                for m in mentions:
                    notes.append(
                        f"[dim]{m['phrase']} ({m['label']}, {m['via']}) → "
                        f"{', '.join(m['resolved_to']) or '∅'}[/]"
                    )

            t = totals[seeder]
            t[0] += len(hit); t[1] += len(named)
            t[2] += len(extra)
            t[3] += len(gold_hit); t[4] += len(gold)

            table.add_row(
                qid if seeder == "semantic" else "",
                seeder,
                f"{len(hit)}/{len(named)}" if named else "—",
                str(len(extra)),
                f"{len(gold_hit)}/{len(gold)}",
                f"{ms:.0f}",
                "; ".join(notes),
            )

            if args.show_seeds:
                degrees = seed_degrees([s.node_id for s in seeds])
                for s in seeds:
                    ok = "[green]✓[/]" if s.name in set().union(*named.values(), gold) else "[red]·[/]"
                    console.print(
                        f"    {ok} {seeder:<10} {s.weight:.3f}  df={degrees.get(s.node_id, 0):<4} "
                        f"{s.label:<14} {s.name}"
                    )

    console.print(table)

    console.print("\n[bold]Totals over the bank[/] (named-entity coverage is the primary "
                  "metric; gold is a secondary view — gold lists answer-entities, which a "
                  "seeder is not supposed to guess):")
    for seeder, (nh, nt, extra, gh, gt) in totals.items():
        console.print(
            f"  {seeder:<10}  named {nh}/{nt}   extra seeds {extra}   gold {gh}/{gt}"
        )
    console.print(
        "\n[dim]'extra seeds' counts seeds outside named∪gold. For the semantic seeder "
        "those are the WISDOM-RIVER class; for the decomposed seeder they are usually "
        "duplicates of a named entity riding along, which is intended — read them with "
        "--show-seeds before treating the count as damning.[/]"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Measure section 5's knobs against the question bank.

Three sweeps, all read-only, all scored the same way:

    --weighting   does seed weighting matter? uniform / proportional /
                  softmax / margin
    --seeds       does the number of seeds matter?
    --blend       where does the useful middle sit between cosine and structure?
    --damping     how long should the walk be?

    python scripts/sweep_pagerank.py --weighting
    python scripts/sweep_pagerank.py --all

── What is being scored, and what it is not ─────────────────────────────────

A passage counts as **conjunction-bearing** for a question if it mentions two
or more of that question's gold entities. That is a *proxy for relevance, not
ground truth*: a passage can name Floyd and the Missouri without being about
his death. So these numbers support "cosine does not retrieve conjunction" —
they do NOT establish that the retrieved passages are correct answers. Any
accuracy claim still belongs to section 8 and its gold set.

Gold targets come from `questions/gold_overrides.yaml`, because several labels
in `questions.yaml` resolve to the wrong node. See that file's header.
"""

from __future__ import annotations

import argparse
import statistics
from pathlib import Path

import _bootstrap  # noqa: F401
import pandas as pd
import yaml
from rich.console import Console
from rich.table import Table

from graphrank.config import read_query
from graphrank.embedding import embed
from graphrank.pagerank import (
    SEED_WEIGHTINGS,
    ExpandConfig,
    _percentile,
    batched_pagerank,
    entity_seeds,
)
from graphrank.projection import all_chunk_node_ids, mentions_membership, project_mentions

console = Console()
ROOT = Path(__file__).resolve().parent.parent


def load_questions() -> list[dict]:
    return yaml.safe_load((ROOT / "questions" / "questions.yaml").read_text())


def load_gold_targets() -> dict[str, list[list[str]]]:
    return yaml.safe_load((ROOT / "questions" / "gold_overrides.yaml").read_text())


def conjunction_passages(gold_pairs: list[list[str]]) -> set[int]:
    """Chunk node ids mentioning >=2 distinct gold entities for this question."""
    if len(gold_pairs) < 2:
        return set()
    rows = read_query(
        """
        UNWIND $pairs AS pair
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        WHERE coalesce(e.canonicalName, e.name) = pair[0]
          AND head(labels(e)) = pair[1]
        WITH c, count(DISTINCT coalesce(e.canonicalName, e.name)) AS matched
        WHERE matched >= 2
        RETURN id(c) AS nodeId
        """,
        pairs=gold_pairs,
    )
    return {row["nodeId"] for row in rows}


class Fixture:
    """Everything that does not depend on the knobs, computed once."""

    def __init__(self) -> None:
        self.chunk_index = pd.Index(all_chunk_node_ids())
        in_graph = mentions_membership()
        targets = load_gold_targets()
        self.questions = []

        for question in load_questions():
            pairs = [p for name in question["gold"] for p in targets.get(name, [])]
            embedding = embed(question["question"])
            rows = read_query(
                """
                CALL db.index.vector.queryNodes('chunk_embeddings', $k, $embedding)
                YIELD node AS c, score
                RETURN id(c) AS nodeId, score
                """,
                k=len(self.chunk_index),
                embedding=embedding,
            )
            cosine = (
                pd.Series({r["nodeId"]: r["score"] for r in rows})
                .reindex(self.chunk_index)
                .fillna(0.0)
            )
            self.questions.append(
                {
                    "id": question["id"],
                    "kind": question["kind"],
                    "embedding": embedding,
                    "cosine_pct": _percentile(cosine),
                    "gold": conjunction_passages(pairs),
                    "passage_seeds": [r["nodeId"] for r in rows if r["nodeId"] in in_graph][:5],
                }
            )

    def structural(self, config: ExpandConfig) -> dict[str, tuple[pd.Series, pd.Series, list]]:
        out = {}
        for q in self.questions:
            seeds = entity_seeds(q["embedding"], config=config)
            # Same code path expand() uses: one biased GDS call per signal.
            entity = (
                batched_pagerank([(s.node_id, s.weight) for s in seeds], config=config)
                .reindex(self.chunk_index)
                .fillna(0.0)
            )
            passage = (
                batched_pagerank(q["passage_seeds"], config=config)
                .reindex(self.chunk_index)
                .fillna(0.0)
            )
            out[q["id"]] = (_percentile(entity), _percentile(passage), seeds)
        return out

    def score(self, structural, *, cosine_weight: float, entity_share: float = 0.5) -> dict:
        """Total conjunction passages reaching top-8, and their median rank."""
        remainder = 1.0 - cosine_weight
        in_top8, ranks = 0, []
        for q in self.questions:
            if not q["gold"]:
                continue
            entity_pct, passage_pct, _ = structural[q["id"]]
            blended = (
                cosine_weight * q["cosine_pct"]
                + remainder * entity_share * entity_pct
                + remainder * (1.0 - entity_share) * passage_pct
            )
            order = list(blended.sort_values(ascending=False).index)
            rank = {node: i + 1 for i, node in enumerate(order)}
            found = [rank[n] for n in q["gold"] if n in rank]
            in_top8 += sum(1 for r in found if r <= 8)
            ranks += found
        return {"top8": in_top8, "median": statistics.median(ranks) if ranks else 0}


def sweep_weighting(fx: Fixture) -> None:
    console.rule("[bold]Does seed weighting matter?")
    table = Table(show_header=True, header_style="bold")
    for col in ("weighting", "weight spread (max→min)", "top-8", "median rank"):
        table.add_column(col, justify="right" if col != "weighting" else "left")

    for weighting in SEED_WEIGHTINGS:
        config = ExpandConfig(seed_weighting=weighting)
        structural = fx.structural(config)
        result = fx.score(structural, cosine_weight=config.cosine_weight)
        spreads = []
        for _, (_, _, seeds) in structural.items():
            if seeds:
                spreads.append(f"{max(s.weight for s in seeds):.2f}/{min(s.weight for s in seeds):.2f}")
        table.add_row(weighting, spreads[0] if spreads else "—",
                      str(result["top8"]), f"{result['median']:.0f}")
    console.print(table)
    console.print(
        "[dim]Weight spread is from the first question, as an illustration; "
        "top-8 and median rank are pooled over the whole bank.[/]"
    )
    # Structure-only, so cosine cannot mask a weighting difference
    console.print("\n[bold]Same comparison with cosine switched off[/] (cosine_weight=0):")
    for weighting in SEED_WEIGHTINGS:
        config = ExpandConfig(seed_weighting=weighting)
        result = fx.score(fx.structural(config), cosine_weight=0.0, entity_share=1.0)
        console.print(f"  {weighting:14s} top-8 {result['top8']:>3d}   median rank {result['median']:.0f}")


def sweep_seeds(fx: Fixture) -> None:
    console.rule("[bold]How many entity seeds?")
    table = Table(show_header=True, header_style="bold")
    for col in ("seeds", "top-8", "median rank", "top-8 (structure only)", "median (structure only)"):
        table.add_column(col, justify="right")
    for count in (1, 2, 3, 4, 5, 8, 12):
        config = ExpandConfig(entity_seed_k=count)
        structural = fx.structural(config)
        blended = fx.score(structural, cosine_weight=config.cosine_weight)
        pure = fx.score(structural, cosine_weight=0.0, entity_share=1.0)
        table.add_row(
            str(count),
            str(blended["top8"]),
            f"{blended['median']:.0f}",
            str(pure["top8"]),
            f"{pure['median']:.0f}",
        )
    console.print(table)
    console.print(
        "[dim]1 -> 2 is the single biggest structural win in this pipeline. The blend's\n"
        "cosine share masks the degradation past 5 seeds that shows up under pure\n"
        "structure, where weak semantic matches start seeding unrelated neighbourhoods.[/]"
    )


def sweep_blend(fx: Fixture) -> None:
    console.rule("[bold]Where does the useful middle sit?")
    structural = fx.structural(ExpandConfig())
    table = Table(show_header=True, header_style="bold")
    for col in ("cosine", "structure", "top-8", "median rank"):
        table.add_column(col, justify="right")
    for weight in [round(1.0 - 0.1 * i, 1) for i in range(11)]:
        result = fx.score(structural, cosine_weight=weight)
        label = f"{weight:.1f}"
        table.add_row(label, f"{1 - weight:.1f}", str(result["top8"]), f"{result['median']:.0f}")
    console.print(table)


def sweep_damping(fx: Fixture) -> None:
    console.rule("[bold]How long should the walk be?")
    table = Table(show_header=True, header_style="bold")
    for col in ("damping", "mass ≤3 steps", "top-8", "median rank"):
        table.add_column(col, justify="right")
    for damping in [0.35, 0.45, 0.55, 0.65, 0.75, 0.85]:
        config = ExpandConfig(damping_factor=damping)
        result = fx.score(fx.structural(config), cosine_weight=config.cosine_weight)
        table.add_row(f"{damping:.2f}", f"{100 * (1 - damping**4):.0f}%",
                      str(result["top8"]), f"{result['median']:.0f}")
    console.print(table)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--weighting", action="store_true")
    parser.add_argument("--seeds", action="store_true")
    parser.add_argument("--blend", action="store_true")
    parser.add_argument("--damping", action="store_true")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    if not any([args.weighting, args.seeds, args.blend, args.damping, args.all]):
        args.all = True

    stats = project_mentions()
    console.print(
        f"[dim]{stats.name}: {stats.node_count:,} nodes, "
        f"{stats.relationship_count:,} rels"
        + (f", projected in {stats.projection_ms:.0f} ms" if stats.projection_ms else " (reused)")
        + "[/]"
    )
    console.print("[dim]Embedding questions and scoring the corpus …[/]")
    fx = Fixture()
    scored = sum(1 for q in fx.questions if q["gold"])
    console.print(
        f"[dim]{scored} of {len(fx.questions)} questions have conjunction passages "
        f"(a question needs >=2 gold entities to be scoreable).[/]\n"
    )

    if args.weighting or args.all:
        sweep_weighting(fx)
    if args.seeds or args.all:
        sweep_seeds(fx)
    if args.blend or args.all:
        sweep_blend(fx)
    if args.damping or args.all:
        sweep_damping(fx)
    return 0


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

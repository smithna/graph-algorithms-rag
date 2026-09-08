#!/usr/bin/env python3
"""Section 5: what multi-seed personalized PageRank does to a ranking.

    python scripts/demo_pagerank.py                     # the Floyd case
    python scripts/demo_pagerank.py --hubs              # the hub trap, visible
    python scripts/demo_pagerank.py --conjunction       # cosine's blind spot
    python scripts/demo_pagerank.py --weighting-check   # a knob that does nothing
    python scripts/demo_pagerank.py "your question here" --blend 0.4

The default question is the section's demo case. On ``lewisclark`` two
passages name both Charles Floyd and the Missouri River; cosine ranks the
buried one 412 of 2,913, because a passage that answers by *combining*
entities does not read like the question. Blended retrieval reaches it: rank
95 at the default --blend 0.6, and rank 8 at --blend 0.0. Worth showing both —
the passage that most needs the graph is the one cosine's weight costs the
most. (On the retired ``neo4j`` graph: one passage, 415 -> 68 -> 16.)
"""

from __future__ import annotations

import argparse
import statistics
import textwrap
from pathlib import Path

import _bootstrap  # noqa: F401
import yaml
from rich.console import Console
from rich.table import Table

from graphrank import baseline, pagerank
from graphrank.config import read_query
from graphrank.embedding import embed
from graphrank.pagerank import SEED_WEIGHTINGS, ExpandConfig
from graphrank.projection import hub_table, project_mentions, total_chunks

console = Console()
ROOT = Path(__file__).resolve().parent.parent

DEFAULT_QUESTION = "What was happening in the days before Sergeant Floyd died?"


def _preview(text: str, width: int = 62) -> str:
    return textwrap.shorten(" ".join(text.split()), width=width, placeholder=" …")


# ── the hub trap, made visible ───────────────────────────────────────────────
def show_hubs() -> None:
    console.rule("[bold]The hub trap: who the walk keeps bumping into")
    rows = hub_table(12)
    table = Table(show_header=True, header_style="bold")
    table.add_column("chunks", justify="right")
    table.add_column("share", justify="right")
    table.add_column("IDF weight", justify="right")
    table.add_column("label")
    table.add_column("entity")
    corpus = total_chunks()
    for row in rows:
        table.add_row(
            f"{row['chunks']:,}",
            f"{100 * row['chunks'] / corpus:.1f}%",
            f"{row['idfWeight']:.2f}",
            row["label"],
            row["name"],
        )
    console.print(table)
    console.print(
        "\nTwo things worth saying out loud about this table:\n"
        "  • Lewis sits in [bold]28% of the corpus[/] — and the [bold]elk outranks Captain Clark[/].\n"
        "    A daily record of what the party shot and ate. The hub is rarely who\n"
        "    you assume: on the previous extraction the white-tailed deer outranked\n"
        "    both captains. A better extractor moved the hub; it did not remove it.\n"
        "  • [bold]DREWYER[/] is here with 297 chunks while [bold]GEORGE DROUILLARD[/] is a\n"
        "    separate node. Section 4's unresolved entities, on screen, for free.\n"
    )
    console.print(
        "The IDF weight is the one-line fix: a shared mention of the top hub is worth\n"
        f"{rows[0]['idfWeight']:.2f}, a rare entity's is worth far more. Measured effect on\n"
        "cross-question entity overlap: [bold]2.84/8 naive → 0.47/8[/] with mentions-only +\n"
        "short walk + IDF (each choice helps; it takes all three — outline finding 5o).\n"
        "Hubs concentrate at the entity level and dissipate at the passage level —\n"
        "so IDF matters most when the entity set is what you consume."
    )


# ── cosine's blind spot, measured ────────────────────────────────────────────
def show_conjunction(config: ExpandConfig) -> None:
    console.rule("[bold]What cosine cannot represent: conjunction")
    questions = yaml.safe_load((ROOT / "questions" / "questions.yaml").read_text())
    targets = yaml.safe_load((ROOT / "questions" / "gold_overrides.yaml").read_text())

    table = Table(show_header=True, header_style="bold")
    table.add_column("question")
    table.add_column("kind")
    table.add_column("passages", justify="right")
    table.add_column("cosine\nbest", justify="right")
    table.add_column("cosine\nmedian", justify="right")
    table.add_column("blended\nbest", justify="right")
    table.add_column("blended\nmedian", justify="right")

    for question in questions:
        pairs = [p for name in question["gold"] for p in targets.get(name, [])]
        if len(pairs) < 2:
            continue
        rows = read_query(
            """
            UNWIND $pairs AS pair
            MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
            WHERE coalesce(e.canonicalName, e.name) = pair[0]
              AND head(labels(e)) = pair[1]
            WITH c, count(DISTINCT coalesce(e.canonicalName, e.name)) AS matched
            WHERE matched >= 2
            RETURN c.chunkId AS chunkId
            """,
            pairs=pairs,
        )
        gold = {r["chunkId"] for r in rows}
        if not gold:
            continue

        cosine = read_query(
            """
            CALL db.index.vector.queryNodes('chunk_embeddings', $k, $embedding)
            YIELD node AS c, score
            RETURN c.chunkId AS chunkId
            """,
            k=total_chunks(),
            embedding=embed(question["question"]),
        )
        cos_rank = {r["chunkId"]: i + 1 for i, r in enumerate(cosine)}
        wide = ExpandConfig(**{**config.__dict__, "k": total_chunks()})
        blended = pagerank.expand(question["question"], config=wide)
        blend_rank = {c.chunk_id: i + 1 for i, c in enumerate(blended.chunks)}

        cos = sorted(cos_rank.get(g, 10**9) for g in gold)
        ppr = sorted(blend_rank.get(g, 10**9) for g in gold)
        table.add_row(
            question["id"],
            question["kind"],
            str(len(gold)),
            str(cos[0]),
            f"{statistics.median(cos):.0f}",
            str(ppr[0]),
            f"{statistics.median(ppr):.0f}",
        )
    console.print(table)
    console.print(
        "\n[dim]A passage counts here if it mentions two or more of the question's gold\n"
        "entities. That is a proxy for relevance, not ground truth — it shows cosine\n"
        "does not retrieve conjunction, not that these passages are correct answers.\n"
        "Gold targets come from questions/gold_overrides.yaml; see its header for why.[/]"
    )


# ── the weighting non-result ─────────────────────────────────────────────────
def show_weighting_check(question: str, config: ExpandConfig) -> None:
    console.rule("[bold]Seed weighting: a knob that looks useful and is not")
    table = Table(show_header=True, header_style="bold")
    table.add_column("weighting")
    table.add_column("weights assigned to the seeds")
    table.add_column("top-8 changed?", justify="right")

    reference: list[str] | None = None
    for weighting in SEED_WEIGHTINGS:
        variant = ExpandConfig(**{**config.__dict__, "seed_weighting": weighting})
        result = pagerank.expand(question, config=variant)
        weights = " ".join(f"{s['weight']:.2f}" for s in result.debug["entity_seeds"])
        ids = result.chunk_ids()
        if reference is None:
            reference, changed = ids, "— (reference)"
        else:
            changed = "no" if ids == reference else f"yes, {sum(1 for a, b in zip(ids, reference) if a != b)} slots"
        table.add_row(weighting, weights, changed)
    console.print(table)
    console.print(
        "\nSharpening the weights 13x changes nothing measurable — note that [bold]softmax[/]\n"
        "collapses to a single effective seed and the window still does not move. Every\n"
        "seed for a question is semantically close to the question, so the seeds sit in\n"
        "overlapping neighbourhoods and their PPR distributions are nearly parallel;\n"
        "reweighting parallel vectors barely rotates the sum. Over the whole question\n"
        "bank: [bold]uniform 22, proportional 22, softmax 22, margin 23[/] passages in the top-8.\n"
    )
    console.print(
        "[bold]What does matter is how many seeds you use[/] — measured over the bank:\n"
        "\n    seeds     top-8   median rank\n"
        "    1            14           380\n"
        "    2            23           308   <- the entire win is here\n"
        "    3            22           314\n"
        "    5            22           318\n"
        "    8            23           335\n"
        "\nSo the design claim survives in a sharper form: you do not need to [italic]pick[/] the\n"
        "right entity, and you do not need to weight the candidates cleverly. You need\n"
        "to stop choosing exactly one. Weighting would matter if the seeds were genuinely\n"
        "[italic]far apart[/] in the graph — worth saying, because that is when people reach for it."
    )


# ── the main event ───────────────────────────────────────────────────────────
def show_comparison(question: str, config: ExpandConfig, *, compare_rerank: bool) -> None:
    console.rule(f"[bold]{question}")

    plain = baseline.retrieve(question, k=config.k)
    blended = pagerank.expand(question, config=config)

    for mention in blended.debug.get("mentions", []):
        console.print(
            f"[dim]named in the question:[/] {mention['phrase']} "
            f"({mention['label']}, via {mention['via']}) → "
            f"{', '.join(mention['resolved_to']) or '[red]nothing[/]'}"
        )
    if blended.debug.get("seeder_fallback"):
        console.print("[yellow]question names no entities — fell back to the semantic seeder[/]")

    seeds = Table(title="Entity seeds — chosen from the question, not from an answer key",
                  show_header=True, header_style="bold")
    seeds.add_column("weight", justify="right")
    seeds.add_column("match", justify="right")
    seeds.add_column("label")
    seeds.add_column("entity")
    for seed in blended.debug["entity_seeds"]:
        seeds.add_row(f"{seed['weight']:.3f}", f"{seed['match']:.3f}", seed["label"], seed["name"])
    console.print(seeds)

    left = Table(title=f"Cosine only  ({plain.elapsed_ms:.0f} ms)",
                 show_header=True, header_style="bold")
    left.add_column("#", width=3, justify="right")
    left.add_column("cos", width=6, justify="right")
    left.add_column("Passage")
    for i, chunk in enumerate(plain.chunks, 1):
        left.add_row(str(i), f"{chunk.vector_score:.3f}", _preview(chunk.text))

    cos_rank = blended.debug.get("cosine_rank", {})
    promoted = set(blended.debug.get("promoted", []))
    right = Table(
        title=f"Cosine + multi-seed PPR  ({blended.elapsed_ms:.0f} ms, "
              f"{blended.debug['corpus_scored']:,} passages scored)",
        show_header=True, header_style="bold",
    )
    right.add_column("#", width=3, justify="right")
    right.add_column("cos #", width=6, justify="right")
    right.add_column("score", width=6, justify="right")
    right.add_column("Passage")
    for i, chunk in enumerate(blended.chunks, 1):
        was = cos_rank.get(chunk.chunk_id)
        marker = f"[green]{was}[/]" if chunk.chunk_id in promoted else str(was or "–")
        right.add_row(str(i), marker, f"{chunk.final_score:.3f}", _preview(chunk.text))

    console.print(left)
    console.print(right)

    if compare_rerank:
        from graphrank.pagerank import RerankConfig

        gated = pagerank.rerank(question, config=RerankConfig(k=config.k))
        overlap = len(set(plain.chunk_ids()) & set(gated.chunk_ids()))
        gate = gated.debug["candidate_k"]
        beyond = sum(
            1 for c in blended.chunks if (cos_rank.get(c.chunk_id) or 0) > gate
        )
        console.print(
            f"\n[bold]For contrast — the candidate-gated reranker[/] "
            f"({gated.elapsed_ms:.0f} ms): {overlap}/{config.k} passages unchanged "
            f"from cosine.\nIt only ranks the vector top-{gate}, so its ceiling is "
            f"'what sits in positions {config.k + 1}-{gate}'.\n"
            f"{beyond} of this window's passages came from beyond cosine rank {gate}, "
            "and were unreachable that way."
        )

    green = [c for c in blended.chunks if c.chunk_id in promoted]
    deepest = max((cos_rank.get(c.chunk_id) or 0) for c in blended.chunks) if blended.chunks else 0
    console.print(
        f"\n[bold]{len(green)}[/] of {config.k} slots went to passages outside the cosine "
        f"top-{config.k}; the deepest was at cosine rank [bold]{deepest}[/] of "
        f"{blended.debug['corpus_scored']:,}."
    )
    console.print(
        f"cosine {config.cosine_weight:.1f} / structure {1 - config.cosine_weight:.1f} · "
        f"damping {config.damping_factor} ({100 * (1 - config.damping_factor**4):.0f}% of walk "
        f"mass within 3 steps) · weighting {config.seed_weighting}"
    )
    timings = blended.debug["timings_ms"]
    console.print(
        f"[dim]cosine {timings['cosine']:.0f} ms · entity PPR {timings['entity_ppr']:.0f} ms · "
        f"passage PPR {timings['passage_ppr']:.0f} ms — PPR is cached per seed, so a repeat "
        f"question is nearly free.[/]"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("-k", type=int, default=8, help="context window size")
    parser.add_argument("--blend", type=float, default=0.6,
                        help="weight on cosine; 1.0 = pure cosine, 0.0 = pure structure")
    parser.add_argument("--damping", type=float, default=0.45, help="walk horizon")
    parser.add_argument("--weighting", choices=SEED_WEIGHTINGS, default="proportional")
    parser.add_argument("--entity-seeds", type=int, default=3)
    parser.add_argument("--seeder", choices=("semantic", "decomposed"), default="semantic",
                        help="semantic = whole-question embedding vs entity descriptions; "
                             "decomposed = LLM names the entities, resolved by name "
                             "(cached; needs OPENAI_API_KEY on first run per question)")
    parser.add_argument("--hubs", action="store_true", help="show the hub table and exit")
    parser.add_argument("--conjunction", action="store_true",
                        help="show cosine's conjunction blind spot across the question bank")
    parser.add_argument("--weighting-check", action="store_true",
                        help="show that seed weighting does not change the result")
    parser.add_argument("--compare-rerank", action="store_true",
                        help="also run the candidate-gated reranker, for contrast")
    args = parser.parse_args()

    project_mentions()
    config = ExpandConfig(
        k=args.k,
        cosine_weight=args.blend,
        damping_factor=args.damping,
        seed_weighting=args.weighting,
        entity_seed_k=args.entity_seeds,
        entity_seeder=args.seeder,
    )

    if args.hubs:
        show_hubs()
        return 0
    if args.conjunction:
        show_conjunction(config)
        return 0
    if args.weighting_check:
        show_weighting_check(args.question, config)
        return 0

    show_comparison(args.question, config, compare_rerank=args.compare_rerank)
    return 0


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

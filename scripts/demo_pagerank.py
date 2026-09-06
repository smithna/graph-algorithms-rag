#!/usr/bin/env python3
"""Show what personalized PageRank does to a vector ranking.

Prints the plain vector top-k beside the reranked top-k, with the rank each
chunk held before reranking. Chunks marked [+] were outside the vector top-k
entirely — the graph pulled them in.

    python scripts/demo_pagerank.py "How did the corps get horses from the Shoshone?"
"""

from __future__ import annotations

import argparse
import textwrap

import _bootstrap  # noqa: F401
from rich.console import Console
from rich.table import Table

from graphrank import baseline, pagerank
from graphrank.pagerank import RerankConfig

console = Console()

DEFAULT_QUESTION = "How did the corps acquire horses from the Shoshone?"


def _preview(text: str, width: int = 68) -> str:
    return textwrap.shorten(" ".join(text.split()), width=width, placeholder=" …")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument("-k", type=int, default=8, help="context window size")
    parser.add_argument("--candidate-k", type=int, default=50, help="vector recall depth")
    parser.add_argument("--seed-k", type=int, default=5, help="PageRank restart set size")
    parser.add_argument("--alpha", type=float, default=0.5,
                        help="1.0 = pure cosine, 0.0 = pure PageRank")
    parser.add_argument("--normalize", choices=["none", "lift"], default="lift")
    args = parser.parse_args()

    console.rule(f"[bold]{args.question}")

    config = RerankConfig(
        candidate_k=args.candidate_k,
        seed_k=args.seed_k,
        k=args.k,
        alpha=args.alpha,
        normalize=args.normalize,
    )

    plain = baseline.retrieve(args.question, k=args.k)
    reranked = pagerank.rerank(args.question, config=config)

    left = Table(title=f"Vector only  ({plain.elapsed_ms:.0f} ms)",
                 show_header=True, header_style="bold")
    left.add_column("#", width=3, justify="right")
    left.add_column("cos", width=6, justify="right")
    left.add_column("Passage")
    for i, chunk in enumerate(plain.chunks, 1):
        left.add_row(str(i), f"{chunk.vector_score:.3f}", _preview(chunk.text))

    vector_rank = reranked.debug.get("vector_rank", {})
    promoted = set(reranked.debug.get("promoted", []))

    right = Table(
        title=f"Vector + personalized PageRank  ({reranked.elapsed_ms:.0f} ms)",
        show_header=True,
        header_style="bold",
    )
    right.add_column("#", width=3, justify="right")
    right.add_column("was", width=5, justify="right")
    right.add_column("score", width=6, justify="right")
    right.add_column("Passage")
    for i, chunk in enumerate(reranked.chunks, 1):
        was = vector_rank.get(chunk.chunk_id)
        marker = "[green]+[/]" if chunk.chunk_id in promoted else str(was or "–")
        right.add_row(str(i), marker, f"{chunk.final_score:.3f}", _preview(chunk.text))

    console.print(left)
    console.print(right)

    overlap = len(set(plain.chunk_ids()) & set(reranked.chunk_ids()))
    console.print(
        f"\n[bold]{len(promoted)}[/] of {args.k} slots went to passages outside the "
        f"vector top-{args.k}.  Overlap with baseline: {overlap}/{args.k}."
    )
    console.print(
        f"Seeds: {len(reranked.debug.get('seed_chunk_ids', []))} restart nodes · "
        f"alpha={args.alpha} · normalize={args.normalize}"
    )
    return 0


if __name__ == "__main__":
    from graphrank.cli import run

    raise SystemExit(run(main))

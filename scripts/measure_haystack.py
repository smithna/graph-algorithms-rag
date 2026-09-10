#!/usr/bin/env python3
"""The haystack question, answered on the theme map vs plain cosine.

    NEO4J_DATABASE=lewisclark python scripts/measure_haystack.py

Finding 6e (2026-09-09): does slide 6.3's claim — "the map turns one
impossible question into 25 answerable ones" — survive being run?

Method (no LLM, one cached question embedding): cosine-score every chunk;
group scores by theme (relatedChunksDf50, Leiden gamma 1.5, seed 42); rank
themes by their best-matching chunk; the MAP WINDOW takes the single best
chunk from each of the top-8 themes. Contrast with plain cosine top-8 on:
months covered, distinct themes, and the passages themselves (read them).

Writes results/haystack-lewisclark.md with both windows in full plus the
best-hardship-passage-per-theme for all 25 themes.
"""

from __future__ import annotations

from collections import defaultdict

import _bootstrap  # noqa: F401

from graphrank.config import gds, read_query
from graphrank.embedding import embed
from measure_theme_map import ensure_graph, leiden_kwargs

RESULTS = _bootstrap.ROOT / "results" / "haystack-lewisclark.md"

Q = "What were the greatest hardships the expedition faced?"
K = 8


def main() -> None:
    g, G = gds(), ensure_graph(50)
    frame = g.leiden.stream(G, **leiden_kwargs(1.5))
    comm = dict(zip(frame["nodeId"], frame["communityId"]))

    emb = embed(Q)
    rows = read_query(
        """
        CALL db.index.vector.queryNodes('chunk_embeddings', 2913, $e)
        YIELD node AS c, score
        RETURN id(c) AS nid, c.chunkId AS cid, toString(c.date) AS date,
               c.author AS author, left(c.text, 420) AS text, score
        """,
        e=emb,
    )
    for i, r in enumerate(rows):
        r["cosRank"] = i + 1
        r["theme"] = comm.get(r["nid"])  # None = unmapped (489 chunks)

    best_per_theme: dict = {}
    for r in rows:  # rows are cosine-ordered, so first hit per theme is its best
        t = r["theme"]
        if t is not None and t not in best_per_theme:
            best_per_theme[t] = r
    theme_order = sorted(best_per_theme, key=lambda t: best_per_theme[t]["cosRank"])

    cosine_win = rows[:K]
    map_win = [best_per_theme[t] for t in theme_order[:K]]

    def month_set(win):
        return sorted({r["date"][:7] for r in win if r["date"]})

    def fmt(win, show_theme=True):
        out = []
        for i, r in enumerate(win, 1):
            th = f"theme {r['theme']}" if r["theme"] is not None else "UNMAPPED"
            out.append(f"{i}. {r['date']} · cos#{r['cosRank']}"
                       + (f" · {th}" if show_theme else "")
                       + f" · {r['author']}\n   " + " ".join(r["text"].split()))
        return out

    lines = [
        "# The haystack question on the theme map vs plain cosine",
        "",
        f"> {Q}",
        "",
        f"Map: relatedChunksDf50 · Leiden gamma 1.5 seed 42 · 25 themes "
        f"(489 chunks unmapped). Window rule: rank themes by their best cosine "
        f"chunk; take that one chunk from each of the top-{K} themes.",
        "",
        f"## Plain cosine top-{K} — months: {month_set(cosine_win)}",
        f"",
        f"Fair 25-slot baseline: cosine top-25 covers {len(month_set(rows[:25]))} "
        f"months {month_set(rows[:25])} — nothing from 1804; five days appear "
        f"more than once (1806-06-17 three times).",
        "",
        *fmt(cosine_win),
        "",
        f"## Map window (best chunk of each top-{K} theme) — months: {month_set(map_win)}",
        "",
        *fmt(map_win),
        "",
        "## All 25 themes' best hardship passage (rank = theme relevance order)",
        "",
    ]
    for t in theme_order:
        r = best_per_theme[t]
        lines.append(f"- theme {t}: cos#{r['cosRank']} · {r['date']} · "
                     + " ".join(r["text"].split())[:140])
    unmapped_top = [r for r in rows[:50] if r["theme"] is None]
    lines += ["", f"Unmapped chunks inside cosine's top-50: {len(unmapped_top)} "
              f"({[r['cosRank'] for r in unmapped_top]})"]

    RESULTS.write_text("\n".join(lines) + "\n")
    print(f"cosine months: {month_set(cosine_win)}")
    print(f"map    months: {month_set(map_win)}")
    print(f"map window themes: {[r['theme'] for r in map_win]}")
    print(f"map window cosine ranks: {[r['cosRank'] for r in map_win]}")
    print(f"wrote {RESULTS}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Grounded LLM summaries for the haystack question: cosine-25 vs the map's 25.

    NEO4J_DATABASE=lewisclark python scripts/measure_haystack_summaries.py

Finding 6e addendum (2026-09-09): the raw chunk lists are retrieval plumbing;
what a person gets is the summary. Same prompt, same model
(gpt-5.6-luna; the model only supports default temperature), grounded-only
instructions, dates cited:
  A) context = plain cosine top-25
  B) context = the map's 25 (best chunk per theme, relatedChunksDf50 / gamma 1.5)
Responses cached on disk by prompt hash — the cache is what makes the quoted
text stable across re-runs. Appends both summaries to results/haystack-lewisclark.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import _bootstrap  # noqa: F401

from graphrank.config import gds, read_query, settings
from graphrank.embedding import embed
from measure_theme_map import ensure_graph, leiden_kwargs

RESULTS = _bootstrap.ROOT / "results" / "haystack-lewisclark.md"
CACHE = _bootstrap.ROOT / ".cache" / "summaries"
MODEL = "gpt-5.6-luna"
Q = "What were the greatest hardships the expedition faced?"

PROMPT = """You are answering a question about the Lewis and Clark expedition
using ONLY the journal passages provided below. Do not use any outside
knowledge; if the passages do not support a claim, do not make it.

Question: {q}

Write a concise summary answer (150-200 words). Name each distinct hardship
you find, citing dates like (1805-12-16). Order by severity as the passages
present it.

Passages:
{passages}"""


def llm(prompt: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"{MODEL}::{prompt}".encode()).hexdigest()[:24]
    path = CACHE / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())["text"]
    from openai import OpenAI
    client = OpenAI(api_key=settings().openai_api_key)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.choices[0].message.content.strip()
    path.write_text(json.dumps({"model": MODEL, "text": text}))
    return text


def main() -> None:
    g, G = gds(), ensure_graph(50)
    frame = g.leiden.stream(G, **leiden_kwargs(1.5))
    comm = dict(zip(frame["nodeId"], frame["communityId"]))

    rows = read_query(
        """
        CALL db.index.vector.queryNodes('chunk_embeddings', 2913, $e)
        YIELD node AS c, score
        RETURN id(c) AS nid, toString(c.date) AS date, c.text AS text
        """,
        e=embed(Q),
    )
    best_per_theme: dict = {}
    for i, r in enumerate(rows):
        r["cosRank"] = i + 1
        t = comm.get(r["nid"])
        if t is not None and t not in best_per_theme:
            best_per_theme[t] = r

    cosine25 = rows[:25]
    map25 = sorted(best_per_theme.values(), key=lambda r: r["cosRank"])
    assert len(map25) == 25, len(map25)

    def render(chunks):
        return "\n\n".join(f"[{r['date']}] " + " ".join(r["text"].split())
                           for r in chunks)

    summaries = {}
    for label, chunks in (("cosine top-25", cosine25), ("map: one per theme", map25)):
        summaries[label] = llm(PROMPT.format(q=Q, passages=render(chunks)))

    block = ["", "## Grounded summaries (gpt-5.6-luna, cached)", ""]
    for label, text in summaries.items():
        block += [f"### {label}", "", text, ""]
    with open(RESULTS, "a") as fh:
        fh.write("\n".join(block))
    for label, text in summaries.items():
        print(f"===== {label}\n{text}\n")


if __name__ == "__main__":
    main()

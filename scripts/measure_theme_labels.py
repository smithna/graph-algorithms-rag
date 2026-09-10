#!/usr/bin/env python3
"""LLM theme labels for the 25 communities, grounded in central chunks.

    NEO4J_DATABASE=lewisclark python scripts/measure_theme_labels.py

Finding 6d addendum (2026-09-09, Nathan's design):
1. Write the Leiden community id (relatedChunksDf50, gamma 1.5, seed 42) onto
   the Chunk nodes as `tocCommunity`, so in-community degree is a Cypher query.
2. Per community: top-3 chunks by IN-COMMUNITY degree centrality (distinct
   co-mention neighbors through rare entities, same community).
3. Label each theme with gpt-5.6-luna from the defining entities + those
   central chunks (cached on disk — stable text across runs).
Rewrites the themes table in results/themes-lewisclark-comention.md with a
`theme` column and saves labels to results/theme-labels.json.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict

import _bootstrap  # noqa: F401

from graphrank.config import gds, query, read_query, settings
from measure_theme_map import ensure_graph, leiden_kwargs

LABELS = _bootstrap.ROOT / "results" / "theme-labels.json"
RESULTS = _bootstrap.ROOT / "results" / "themes-lewisclark-comention.md"
CACHE = _bootstrap.ROOT / ".cache" / "summaries"
MODEL = "gpt-5.6-luna"

PROMPT = """These are journal passages from the Lewis and Clark expedition that a
clustering algorithm grouped together, plus the names that define the group.
Name the group's theme in 2-4 words, title case. Reply with the theme only.

Defining names: {entities}

Representative passages (most-connected in the group):
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
        model=MODEL, messages=[{"role": "user", "content": prompt}])
    text = resp.choices[0].message.content.strip().strip('"')
    path.write_text(json.dumps({"model": MODEL, "text": text}))
    return text


def main() -> None:
    g, G = gds(), ensure_graph(50)
    frame = g.leiden.stream(G, **leiden_kwargs(1.5))
    comm = dict(zip(frame["nodeId"], frame["communityId"]))

    # 1. write community ids onto the chunk nodes
    query("MATCH (c:Chunk) REMOVE c.tocCommunity")
    query(
        """
        UNWIND $pairs AS p
        MATCH (c:Chunk) WHERE id(c) = p[0]
        SET c.tocCommunity = p[1]
        """,
        pairs=[[int(n), int(c)] for n, c in comm.items()],
    )
    print(f"wrote tocCommunity onto {len(comm)} chunks")

    # 2. in-community degree, straight Cypher (Nathan's design)
    central = read_query(
        """
        MATCH (c1:Chunk)<-[:MENTIONED_IN]-(b)-[:MENTIONED_IN]->(c2:Chunk)
        WHERE c1 <> c2 AND c1.tocCommunity IS NOT NULL
          AND c1.tocCommunity = c2.tocCommunity
          AND COUNT{ (b)-[:MENTIONED_IN]->() } < 50
        WITH c1, count(DISTINCT c2) AS inDeg
        ORDER BY c1.tocCommunity, inDeg DESC
        WITH c1.tocCommunity AS community,
             collect({cid: c1.chunkId, deg: inDeg, text: left(c1.text, 650)})[..3] AS top
        RETURN community, top
        """
    )
    print(f"central chunks computed for {len(central)} communities")

    # defining entities per community (rare, in-community mention counts)
    ents: dict = defaultdict(Counter)
    for r in read_query(
        """
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        WHERE NOT e:Chunk AND NOT e:GenericLocation AND c.tocCommunity IS NOT NULL
        WITH e, count(DISTINCT c) AS df WHERE df < 50
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE c.tocCommunity IS NOT NULL
        RETURN c.tocCommunity AS community, coalesce(e.canonicalName, e.name) AS name
        """
    ):
        ents[r["community"]][r["name"]] += 1

    # 3. label each community
    labels = {}
    for row in central:
        c = row["community"]
        entities = ", ".join(n for n, _ in ents[c].most_common(8))
        passages = "\n\n".join(
            f"[{t['cid'][:8]} · in-community degree {t['deg']}] "
            + " ".join(t["text"].split()) for t in row["top"])
        labels[c] = llm(PROMPT.format(entities=entities, passages=passages))
        print(f"c{c:>3}: {labels[c]}")
    LABELS.write_text(json.dumps(labels, indent=1, sort_keys=True))

    # 4. rewrite the themes table with the label column
    lines = RESULTS.read_text().splitlines()
    out = []
    for line in lines:
        if line.startswith("| id | chunks |"):
            out.append("| id | chunks | span | conductance | theme (LLM, grounded) | defining entities |")
        elif line.startswith("|---|---|---|---|---|"):
            out.append("|---|---|---|---|---|---|")
        elif line.startswith("| ") and line.count("|") == 6:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            cid = int(parts[0])
            out.append("| " + " | ".join(parts[:4] + [labels.get(cid, "?")] + parts[4:]) + " |")
        else:
            out.append(line)
    RESULTS.write_text("\n".join(out) + "\n")
    print(f"labels merged into {RESULTS}")


if __name__ == "__main__":
    main()

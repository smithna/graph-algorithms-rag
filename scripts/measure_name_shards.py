#!/usr/bin/env python3
"""Name-shard identities: many spellings of one person, and who can find them.

    NEO4J_DATABASE=neo4j      python scripts/measure_name_shards.py   # the demo graph
    NEO4J_DATABASE=budgetluna python scripts/measure_name_shards.py   # the budget graph

Sacagawea (5j/5j-bis) is the *role-shard* case: rarely named, identity spread
over descriptive nodes. George Drouillard is the other cell of the matrix —
the *spelling-shard* case: named constantly, but the corpus spells him
Drewyer, Drouillard, Drewyear, Drewnyer…, and extraction split him into
disjoint nodes whose name strings never match. Notably this is NOT a
budget-graph pathology: the gold demo graph never merged DREWYER (df 265)
into GEORGE DROUILLARD (df 63) either — it is the unresolved duplicate the
hub table shows on stage. So 5g's "filter+cosine parity" carries an unstated
precondition measured here: parity holds for entities the resolution pass
actually merged; ask about Drouillard by his historical name and the tag
filter sees a fifth of him, on the demo graph itself.

Three membership/mass measurements per case, no relevance judgements:

1. **Resolution** — what each way of asking resolves to (deterministic
   full-text path of the decomposed seeder; the LLM step would only emit the
   phrase). The seeder is spelling-hostage: each phrase catches the shard
   spelled its way and nothing else.
2. **Vector discoverability of the missed shard** — where the other big
   shard ranks among vector candidates for the canonical ask. This is where
   the co-typed substitution of 5e reappears one layer down: similar names of
   *different people* (the Dorion cluster — a different interpreter) embed
   closer than different spellings of *the same person*.
3. **Walk reach, population-level** — median corpus rank of the missed
   shard's chunks under PPR seeded from what resolution caught, vs. seeded
   from both shards df-proportionally (5f's identity: arithmetically the
   merged node's walk), vs. plain cosine on a question about the person.
   Medians of a tag-defined population, the 5e form — no relevance proxy,
   no top-k threshold.

This script's own output is the write-up -- run it to see the numbers.
"""

from __future__ import annotations

import argparse

import _bootstrap  # noqa: F401
import pandas as pd
from rich.console import Console
from rich.table import Table

from measure_ablation import ppr_chunk_scores
from graphrank.config import read_query, settings
from graphrank.decompose import Mention, resolve_mention
from graphrank.embedding import embed
from graphrank.pagerank import ExpandConfig
from graphrank.projection import mentions_membership, project_mentions, total_chunks

console = Console()

CASES = {
    "drouillard": {
        #: Big shards of the identity, by canonical name. Verified present on
        #: both `neo4j` and `budgetluna`; smaller df-1..6 shards (DREWYERS,
        #: DREWNYER, SHANNON DREWYER — a conflation node) exist but carry no
        #: mass worth modelling.
        "shards": ["GEORGE DROUILLARD", "DREWYER"],
        #: Ways a user might ask. The first is the canonical ask used for the
        #: vector-discoverability and walk measurements.
        "asks": ["George Drouillard", "Drouillard", "Drewyer"],
        "question": "What did George Drouillard contribute to the expedition?",
        #: For the shard-landscape table.
        "pattern": r"(?i).*(dr[ueo]+[wil]+[a-z]*(yer|ard|yar|iard)|drewyer|drouil).*",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--case", default="drouillard", choices=sorted(CASES))
    args = parser.parse_args()
    case = CASES[args.case]

    cfg = settings()
    console.print(f"[bold]Name shards on {cfg.neo4j_database!r}[/] — {args.case}")

    # ── Shard landscape ───────────────────────────────────────────────────────
    rows = read_query(
        """
        MATCH (e) WHERE NOT e:Chunk AND NOT e:GenericLocation
          AND coalesce(e.canonicalName, e.name) =~ $pat
        OPTIONAL MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        RETURN head(labels(e)) AS label, coalesce(e.canonicalName, e.name) AS name,
               count(DISTINCT c) AS df
        ORDER BY df DESC
        """,
        pat=case["pattern"],
    )
    for r in rows:
        console.print(f"  df={r['df']:4d} {r['label']:10s} {r['name']}")

    shard_ids = {}
    shard_chunks = {}
    for name in case["shards"]:
        nid = read_query(
            "MATCH (e:Person) WHERE coalesce(e.canonicalName, e.name) = $n "
            "RETURN id(e) AS nid",
            n=name,
        )[0]["nid"]
        shard_ids[name] = nid
        shard_chunks[name] = {
            r["c"]
            for r in read_query(
                "MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE id(e) = $n "
                "RETURN DISTINCT id(c) AS c",
                n=nid,
            )
        }
    a, b = case["shards"]
    overlap = shard_chunks[a] & shard_chunks[b]
    console.print(
        f"\n  {a} df {len(shard_chunks[a])} · {b} df {len(shard_chunks[b])} · "
        f"co-occur in {len(overlap)} chunks — the shards are "
        f"{'disjoint' if not overlap else 'overlapping'}"
    )

    # ── 1. Resolution per ask ─────────────────────────────────────────────────
    in_graph = mentions_membership()
    caught: list[dict] = []
    for i, phrase in enumerate(case["asks"]):
        rm = resolve_mention(Mention(phrase=phrase, label="Person"), in_graph=in_graph)
        names = [c["name"] for c in rm.candidates]
        console.print(f"  ask {phrase!r} ({rm.via}) → {', '.join(names) or '∅'}")
        if i == 0:
            caught = rm.candidates

    caught_chunks: set[int] = set()
    for c in caught:
        caught_chunks |= {
            r["c"]
            for r in read_query(
                "MATCH (e)-[:MENTIONED_IN]->(c:Chunk) WHERE id(e) = $n "
                "RETURN DISTINCT id(c) AS c",
                n=c["nodeId"],
            )
        }
    union = shard_chunks[a] | shard_chunks[b]
    missed = union - caught_chunks
    console.print(
        f"\n  the canonical ask catches {len(caught_chunks)} of {len(union)} chunks "
        f"({100 * len(caught_chunks) / len(union):.0f}%) — a tag filter on what it "
        f"caught loses [bold]{len(missed)}[/] passages"
    )

    # ── 2. Vector discoverability of the missed shard ─────────────────────────
    vec = read_query(
        """
        CALL db.index.vector.queryNodes('person_embeddings', 50, $e)
        YIELD node, score
        RETURN coalesce(node.canonicalName, node.name) AS name, score
        """,
        e=embed(case["asks"][0]),
    )
    caught_names = {c["name"] for c in caught}
    console.print(f"\n  vector candidates for {case['asks'][0]!r} (position of each shard):")
    for i, r in enumerate(vec, 1):
        if r["name"] in case["shards"] or i <= 5:
            mark = " ← shard" if r["name"] in case["shards"] else ""
            found = " (caught)" if r["name"] in caught_names else ""
            console.print(f"    #{i:2d} {r['score']:.4f}  {r['name']}{mark}{found}")

    # ── 3. Walk reach over the missed population ──────────────────────────────
    project_mentions()
    config = ExpandConfig()

    def median_rank(weighted_seeds) -> float:
        scores = ppr_chunk_scores(cfg.mentions_graph_name, weighted_seeds, config)
        ranks = scores.rank(ascending=False, method="min")
        return float(ranks.loc[list(missed)].median())

    df_a, df_b = len(shard_chunks[a]), len(shard_chunks[b])
    merged = [
        (shard_ids[a], df_a / (df_a + df_b)),
        (shard_ids[b], df_b / (df_a + df_b)),
    ]
    emb = embed(case["question"])
    cos = read_query(
        """
        CALL db.index.vector.queryNodes('chunk_embeddings', $k, $e)
        YIELD node, score RETURN id(node) AS nid
        """,
        k=total_chunks(),
        e=emb,
    )
    cos_rank = {r["nid"]: i + 1 for i, r in enumerate(cos)}
    cos_med = pd.Series([cos_rank.get(c, total_chunks()) for c in missed]).median()

    table = Table(header_style="bold")
    table.add_column(f"median corpus rank of the {len(missed)} missed chunks")
    table.add_column("rank", justify="right")
    table.add_row(
        "walk seeded from what resolution caught",
        f"{median_rank([(c['nodeId'], 1.0 / len(caught)) for c in caught]):.0f}",
    )
    table.add_row("walk seeded from both shards, df-proportional (= merged walk)",
                  f"{median_rank(merged):.0f}")
    table.add_row("cosine, question embedding", f"{cos_med:.0f}")
    table.add_row("tag filter on both shards", "all in filter (membership)")
    console.print(table)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

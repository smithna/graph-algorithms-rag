#!/usr/bin/env python3
"""Thematic questions on the resolved graph: the one class where no filter can run.

    NEO4J_DATABASE=lewisclark python scripts/measure_thematic.py
    NEO4J_DATABASE=lewisclark python scripts/measure_thematic.py --only trade-goods

Finding 5g reduced section 5's bar to "beat the entity filter, not cosine" —
and 5h-2(b) named the one question class where that bar collapses back to
cosine: thematic questions. All three in the bank (`trade-goods`,
`food-sources`, `illness-and-injury`) decompose to **zero entity mentions**
(verified against the cached gpt-5.6-luna parses before this script ran), so
there is no tag to filter on and filter+cosine cannot be constructed. The
comparison is passage-seeded PPR — entity-based query expansion, hop from
cosine's top chunks to their rare entities to the passages sharing them —
against cosine alone, on `lewisclark`, where any win cannot be blamed on
extraction gaps.

Three strategies per question, top-8 each:

1. ``vector``        cosine alone — the only baseline that exists here
2. ``passage-blend`` cosine 0.6 + passage-seeded PPR 0.4 (entity_share=0)
3. ``expand``        the shipped default: cosine 0.6 + entity PPR 0.2 +
                     passage PPR 0.2, semantic entity seeder (on lewisclark
                     that draws from the species/event/taxon vector indexes)

Per the measurement discipline this script emits **no verdict**: membership
tables, promotion receipts (which shared entities carried each promoted
passage, at what IDF), and descriptive window stats (distinct entities,
near-duplicate pairs). The verdict comes from reading the read-pack it writes
to ``results/thematic-<database>.md`` — every distinct chunk across all
windows, grouped by question, with per-strategy membership flags. Fresh hand
reads are the cost 5h-2 priced in; the old finding-4/5 numbers used the
proxy-contaminated gold and are not comparable.

Results and their reading live in ``docs/talk-outline.md``, finding 5l.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
import numpy as np
from rich.console import Console
from rich.table import Table

from graphrank.config import read_query, settings
from graphrank.decompose import decompose
from graphrank.embedding import embed
from graphrank.models import RetrievalResult
from graphrank.pagerank import ExpandConfig, expand
from graphrank.projection import project_mentions
from graphrank.strategies import vector_strategy

console = Console()

THEMATIC = {
    "trade-goods": "What goods did the expedition trade with Native nations along the route?",
    "food-sources": "How did the expedition feed itself across different stretches of the journey?",
    "illness-and-injury": "What illnesses and injuries did the corps deal with?",
}

K = 8


def strategies(question: str) -> dict[str, RetrievalResult]:
    """The three windows under comparison. Every expand call scores the corpus."""
    return {
        "vector": vector_strategy(question, k=K),
        "passage-blend": expand(
            question,
            config=ExpandConfig(k=K, cosine_weight=0.6, entity_share=0.0),
        ),
        "expand": expand(
            question,
            config=ExpandConfig(k=K, cosine_weight=0.6, entity_share=0.5),
        ),
    }


def confirm_no_filter(qid: str, question: str) -> None:
    """The premise, checked live: zero decomposed mentions -> no tag filter exists."""
    mentions = decompose(question)
    if mentions:
        console.print(
            f"[red]{qid}: decomposed to {[(m.phrase, m.label) for m in mentions]} — "
            "a filter CAN run; this question no longer belongs in this measurement[/red]"
        )
    else:
        console.print(f"[dim]{qid}: zero decomposed mentions — no filter can run[/dim]")


def shared_entity_receipt(seed_chunk_ids: list[str], chunk_id: str) -> list[dict]:
    """Which entities connect a promoted chunk back to the passage seeds.

    The mechanism made visible: a promotion is legitimate exactly when rare
    entities carried it, and suspicious when the bridge is a hub.
    """
    return read_query(
        """
        MATCH (seed:Chunk) WHERE seed.chunkId IN $seedIds
        MATCH (e)-[:MENTIONED_IN]->(seed)
        WHERE NOT e:Chunk AND NOT e:GenericLocation
        WITH DISTINCT e
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk {chunkId: $chunkId})
        MATCH (e)-[:MENTIONED_IN]->(any:Chunk)
        WITH e, count(DISTINCT any) AS df
        RETURN head(labels(e))                   AS label,
               coalesce(e.canonicalName, e.name) AS name,
               df
        ORDER BY df ASC
        LIMIT 6
        """,
        seedIds=seed_chunk_ids,
        chunkId=chunk_id,
    )


def window_stats(chunk_ids: list[str]) -> dict:
    """Descriptive stats for one top-8 window. No relevance content.

    ``near_dup_pairs`` counts window pairs with embedding cosine > 0.85 — the
    "eight near-duplicate passages about one trading session" failure mode,
    counted rather than asserted.
    """
    rows = read_query(
        """
        MATCH (c:Chunk) WHERE c.chunkId IN $ids
        OPTIONAL MATCH (e)-[:MENTIONED_IN]->(c)
        WHERE NOT e:Chunk AND NOT e:GenericLocation
        RETURN c.chunkId AS chunkId, toString(c.date) AS date, c.embedding AS embedding,
               collect(DISTINCT coalesce(e.canonicalName, e.name)) AS entities
        """,
        ids=chunk_ids,
    )
    entities = {e for r in rows for e in r["entities"]}
    vectors = np.array([r["embedding"] for r in rows if r["embedding"]])
    near_dups = 0
    if len(vectors) > 1:
        normed = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
        sims = normed @ normed.T
        near_dups = int((np.triu(sims, k=1) > 0.85).sum())
    months = sorted({(r["date"] or "?")[:7] for r in rows})
    return {
        "distinct_entities": len(entities),
        "near_dup_pairs": near_dups,
        "distinct_months": len(months),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--only", choices=sorted(THEMATIC), help="run one question")
    args = parser.parse_args()

    db = settings().neo4j_database
    console.print(f"[bold]Thematic measurement on database '{db}'[/bold]")
    stats = project_mentions()
    console.print(
        f"[dim]{stats.name}: {stats.node_count} nodes / "
        f"{stats.relationship_count} rels[/dim]\n"
    )

    questions = (
        {args.only: THEMATIC[args.only]} if args.only else THEMATIC
    )

    read_pack: list[str] = [
        f"# Thematic read-pack — database `{db}`\n",
        "Every distinct chunk across all windows, grouped by question.",
        "Membership flags say which strategy's top-8 holds it and at what",
        "position; `cosine` is the corpus-wide cosine rank. Judge by reading.\n",
    ]

    for qid, question in questions.items():
        console.rule(f"[bold]{qid}[/bold]")
        console.print(f"[italic]{question}[/italic]")
        confirm_no_filter(qid, question)

        results = strategies(question)

        # ── membership table ────────────────────────────────────────────────
        table = Table(title=f"{qid} — top-{K} windows")
        table.add_column("pos")
        for name in results:
            table.add_column(name)
        rows = zip(*(r.chunks for r in results.values()))
        for i, row in enumerate(rows, 1):
            table.add_row(str(i), *(c.chunk_id for c in row))
        console.print(table)

        # ── overlap + descriptive stats ─────────────────────────────────────
        windows = {name: [c.chunk_id for c in r.chunks] for name, r in results.items()}
        vector_window = set(windows["vector"])
        stats_table = Table(title=f"{qid} — window stats (descriptive, no judgement)")
        stats_table.add_column("strategy")
        stats_table.add_column("vs vector")
        stats_table.add_column("entities")
        stats_table.add_column("near-dup pairs")
        stats_table.add_column("months")
        for name, ids in windows.items():
            ws = window_stats(ids)
            overlap = len(set(ids) & vector_window)
            stats_table.add_row(
                name,
                f"{overlap}/{K}" if name != "vector" else "—",
                str(ws["distinct_entities"]),
                str(ws["near_dup_pairs"]),
                str(ws["distinct_months"]),
            )
        console.print(stats_table)

        # ── entity seeds the expand run chose (lewisclark: species/event/taxon)
        seeds = results["expand"].debug.get("entity_seeds", [])
        if seeds:
            console.print(
                "entity seeds: "
                + " · ".join(f"{s['name']} ({s['label']}, {s['match']})" for s in seeds)
            )

        # ── promotion receipts ──────────────────────────────────────────────
        seed_ids = results["passage-blend"].debug.get("promoted", [])
        for name in ("passage-blend", "expand"):
            result = results[name]
            promoted = result.debug.get("promoted", [])
            passage_seeds = [
                c.chunk_id for c in results["vector"].chunks[:5]
            ]  # cosine top-5 == the walk's passage seeds
            if promoted:
                console.print(f"\n[bold]{name}[/bold] promoted {len(promoted)}:")
            for chunk_id in promoted:
                bridge = shared_entity_receipt(passage_seeds, chunk_id)
                rank = result.debug.get("cosine_rank", {}).get(chunk_id)
                carried = ", ".join(
                    f"{b['name']} ({b['label']} df {b['df']})" for b in bridge
                )
                console.print(
                    f"  {chunk_id} (cosine rank {rank}) ← {carried or 'NO shared entity'}"
                )

        # ── read-pack: union of all windows, full text ──────────────────────
        union: dict[str, dict] = {}
        for name, r in results.items():
            for pos, c in enumerate(r.chunks, 1):
                entry = union.setdefault(
                    c.chunk_id,
                    {"chunk": c, "member": {}},
                )
                entry["member"][name] = pos
        cosine_ranks = {
            **results["passage-blend"].debug.get("cosine_rank", {}),
            **results["expand"].debug.get("cosine_rank", {}),
        }
        read_pack.append(f"\n## {qid}\n\n> {question}\n")
        for chunk_id, entry in sorted(union.items()):
            c = entry["chunk"]
            flags = " · ".join(
                f"{name} #{pos}" for name, pos in sorted(entry["member"].items())
            )
            cr = cosine_ranks.get(chunk_id, "≤8" if "vector" in entry["member"] else "?")
            read_pack.append(
                f"### {chunk_id} — {c.date or 'no date'} — {c.author or 'unknown'}\n"
                f"*{flags} · cosine rank {cr}*\n\n{c.text}\n"
            )

    out = Path(__file__).resolve().parent.parent / "results" / f"thematic-{db}.md"
    out.write_text("\n".join(read_pack))
    console.print(f"\n[bold]read-pack written to {out}[/bold] — the verdict lives there")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

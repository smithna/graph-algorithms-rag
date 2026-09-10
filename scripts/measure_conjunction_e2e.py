#!/usr/bin/env python3
"""Conjunction questions end-to-end: decomposed seeder + expand, windows read.

    NEO4J_DATABASE=lewisclark python scripts/measure_conjunction_e2e.py

Finding 5q (2026-09-09): the end-to-end companion to 5p. One devised question
per 5p seed pair, run exactly as §5.9 runs (shipped ExpandConfig,
entity_seeder='decomposed'), against the cosine top-8 baseline. Costs one
decompose call + one embedding call per question on first run (cached after).

Per-question outcome is in the finding; headline: the conjunction reordering
survives end-to-end (dual-mention chunks move to the top of 5 of 7 windows),
SACAGAWEA+HIDATSA / CLARK+CAMEAHWAIT / LEWIS+PRAIRIE DOG are the clean
windows, FORT MANDAN+SHOSHONE is the honest miss (the answer passage predates
the fort's naming, so the conjunction never exists in the tag layer), and the
prairie-dog question surfaced a query-time resolution miss (seeder resolved
'prairie dog' to a grouse — CYNOMYS carries only 'burrowing squirrels' as an
alias, vector rank 5) that the passage-seeded half of the blend absorbed:
2/8 -> 8/8 dual-mention chunks anyway.
"""

import _bootstrap  # noqa: F401

from graphrank.baseline import vector_search
from graphrank.config import read_query
from graphrank.embedding import embed
from graphrank.pagerank import ExpandConfig, expand

QUESTIONS = [
    ("CHARBONNEAU+SHOSHONE", "TOUSSAINT CHARBONNEAU", "SHOSHONE",
     "How did Toussaint Charbonneau help the expedition communicate with the Shoshone?"),
    ("SACAGAWEA+HIDATSA", "SACAGAWEA", "HIDATSA",
     "How did Sacagawea come to be living among the Hidatsa when the expedition met her?"),
    ("SACAGAWEA+SHOSHONE", "SACAGAWEA", "SHOSHONE",
     "What part did Sacagawea play in the expedition's negotiations with the Shoshone?"),
    ("FORT MANDAN+SHOSHONE", "FORT MANDAN", "SHOSHONE",
     "What arrangements did the captains make at Fort Mandan for interpreting the Shoshone language?"),
    ("FLOYD+MISSOURI", "CHARLES FLOYD", "MISSOURI RIVER",
     "Where along the Missouri River was Sergeant Charles Floyd buried?"),
    ("LEWIS+PRAIRIE DOG", "MERIWETHER LEWIS", "CYNOMYS LUDOVICIANUS",
     "How did Captain Lewis's party capture a prairie dog, and how did he describe it?"),
    ("CLARK+CAMEAHWAIT", "WILLIAM CLARK", "CAMEAHWAIT",
     "What did William Clark record about his dealings with the Shoshone chief Cameahwait?"),
]

#: Receipts whose blend/cosine position is worth tracking per question.
PROBES = {
    "nov4-hiring": "13c2e69bf03a0342",
}


def entity_chunks(name: str) -> set[str]:
    rows = read_query(
        """
        MATCH (e)-[:MENTIONED_IN]->(c:Chunk)
        WHERE NOT e:Chunk AND coalesce(e.canonicalName, e.name) = $name
        RETURN DISTINCT c.chunkId AS cid
        """,
        name=name,
    )
    return {r["cid"] for r in rows}


def flag(cid: str, in_a: set[str], in_b: set[str]) -> str:
    a, b = cid in in_a, cid in in_b
    return "A+B" if a and b else "A  " if a else "B  " if b else "-- "


def main() -> None:
    cfg = ExpandConfig(entity_seeder="decomposed")
    for label, name_a, name_b, question in QUESTIONS:
        in_a, in_b = entity_chunks(name_a), entity_chunks(name_b)
        print(f"\n{'=' * 100}\n[{label}] {question}")

        cosine = vector_search(embed(question), k=8)
        result = expand(question, config=cfg)
        dbg = result.debug

        print(f"  seeder: {dbg.get('seeder')}"
              + (f"  (FELL BACK: {dbg['seeder_fallback']})" if "seeder_fallback" in dbg else ""))
        for m in dbg.get("mentions", []):
            print(f"    mention {m['phrase']!r} ({m['label']}, via {m['via']}) -> {m['resolved_to']}")
        for s in dbg.get("entity_seeds", []):
            print(f"    seed {s['name']} ({s['label']})  weight={s['weight']}")

        print("  cosine top-8:")
        for i, c in enumerate(cosine, 1):
            print(f"    {i}. [{flag(c.chunk_id, in_a, in_b)}] {c.date}  {c.text[:150]!r}")

        print(f"  expand top-8 (promoted from beyond cosine top-8: {len(dbg['promoted'])}):")
        for i, c in enumerate(result.chunks, 1):
            crank = dbg["cosine_rank"].get(c.chunk_id)
            print(f"    {i}. [{flag(c.chunk_id, in_a, in_b)}] {c.date}  cosine#{crank:>4}  {c.text[:150]!r}")

        n_both_cos = sum(1 for c in cosine if c.chunk_id in in_a and c.chunk_id in in_b)
        n_both_exp = sum(1 for c in result.chunks if c.chunk_id in in_a and c.chunk_id in in_b)
        print(f"  A+B chunks in window: cosine {n_both_cos}/8 -> expand {n_both_exp}/8"
              f"   | corpus has {len(in_a & in_b)} A+B chunks total")


if __name__ == "__main__":
    main()

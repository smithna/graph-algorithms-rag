"""Layered disambiguation: candidates -> adjudicate -> evidence -> transitivity -> merge.

Reads candidates and applies both safety layers using graphrank.resolution,
which never writes. The merge at the end is the ONLY write, and it is gated.
"""
import os, sys, argparse
sys.path.insert(0, "/Users/nathansmith/Documents/kcdc-2026/graph-algorithms-rag")

ap = argparse.ArgumentParser()
ap.add_argument("--database", default="lewisclark")
ap.add_argument("--label", default="Person")
ap.add_argument("--max-calls", type=int, default=1500)
ap.add_argument("--max-component", type=int, default=25)
ap.add_argument("--apply", action="store_true", help="actually merge (default: dry run)")
a = ap.parse_args()
os.environ["NEO4J_DATABASE"] = a.database

from graphrank import resolution as R, adjudicate as A
from graphrank.config import query

inv = R.entities()
byname = {e.name: e for e in inv.values()}
g = R.build_cooccurrence_graph()
try:
    pairs = R.candidates(a.label, graph=g, inventory=inv)
    print(f"[1] candidates: {len(pairs)}", flush=True)

    verdicts = A.adjudicate(pairs, enabled=True, max_calls=a.max_calls)
    conf = A.confirmed_pairs(verdicts); s = A.summarize(verdicts)
    print(f"[2] adjudicated: confirmed={s.get('confirmed',0)} rejected={s.get('rejected',0)} "
          f"cache={s.get('cache',0)} fresh={s.get('llm',0)} capped={s.get('skipped-cap',0)}", flush=True)

    ev = R.filter_by_evidence(conf)
    print(f"[3] evidence filter: {len(conf)} -> {len(ev)} pairs", flush=True)

    def judge(l, r, lbl):
        c = A.cached_verdict(l, r, lbl)
        if c is not None: return c, True
        v = A.adjudicate([R.CandidatePair(left=byname[l], right=byname[r])], enabled=True, max_calls=1)
        return (v[0].same_entity if v[0].decided else None), False

    rep = R.verify_transitivity(ev, judge=judge, max_calls=400)
    print(f"[4] transitivity: {rep.checks_needed} checks, {rep.cache_hits} cached, "
          f"{rep.llm_calls} fresh, {len(rep.bridges)} bridges", flush=True)
    for b in rep.bridges[:15]: print(f"      {b.describe()}", flush=True)

    ok, refused = R.components_verified(ev, inv, rep, max_component=a.max_component)
    print(f"[5] components: {len(ok)} accepted, {len(refused)} refused (>{a.max_component})", flush=True)
    for c in refused: print(f"      REFUSED [{c.size}] {c.describe()[:120]}", flush=True)
    for c in sorted(ok, key=lambda c: -c.size)[:15]:
        print(f"      [{c.size}] {c.describe()[:130]}", flush=True)

    if not a.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to merge.", flush=True)
        sys.exit(0)

    print(f"\n[6] MERGING {len(ok)} components ...", flush=True)
    merged = 0
    for c in ok:
        ids = [m.node_id for m in c.members]
        canon = max((m.name for m in c.members), key=len)
        query(f"""
            MATCH (n:{a.label}) WHERE id(n) IN $ids
            WITH collect(n) AS nodes, reduce(acc=[], x IN collect(n) |
                 acc + coalesce(x.aliases,[]) + [x.name]) AS raw
            CALL apoc.refactor.mergeNodes(nodes, {{mergeRels:true, produceSelfRel:false}})
            YIELD node
            SET node.canonicalName = $canon, node.name = $display,
                node.aliases = [x IN coll.distinct(raw) WHERE x <> $display]
        """, ids=ids, canon=canon, display=canon.title())
        merged += 1
    print(f"[6] merged {merged} components", flush=True)
finally:
    R.drop_graph(R.COOCCURRENCE_GRAPH)

"""Layered disambiguation: candidates -> adjudicate -> evidence -> transitivity
-> consistency -> merge.

Reads candidates and applies the safety layers using graphrank.resolution,
which never writes. The merge at the end is the ONLY write, and it is gated.

Under --apply, layer 3 runs with require_complete: a cluster merges only when
every internal member pair carries a decided verdict and none is negative.
Dry runs tolerate unverified pairs and report them instead.
"""
import os, sys, argparse
sys.path.insert(0, "/Users/nathansmith/Documents/kcdc-2026/graph-algorithms-rag")

ap = argparse.ArgumentParser()
ap.add_argument("--database", default="lewisclark")
ap.add_argument("--label", default="Person")
ap.add_argument("--max-calls", type=int, default=1500)
ap.add_argument("--max-component", type=int, default=25)
ap.add_argument("--consistency-max-calls", type=int, default=600)
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

    vmap = {v.pair.key: v.same_entity for v in verdicts if v.decided}
    ok, refused = R.components_verified(ev, inv, rep, max_component=a.max_component,
                                        verdict_map=vmap)
    print(f"[5] components: {len(ok)} accepted, {len(refused)} refused (>{a.max_component})", flush=True)
    for c in refused: print(f"      REFUSED [{c.size}] {c.describe()[:120]}", flush=True)
    for c in sorted(ok, key=lambda c: -c.size)[:15]:
        print(f"      [{c.size}] {c.describe()[:130]}", flush=True)

    kept = R.bridge_cut(ev, rep, vmap)
    mergeable, crep = R.verify_components(
        ok, kept,
        adjudicator=lambda ps, mc: A.adjudicate(ps, enabled=True, max_calls=mc),
        max_calls=a.consistency_max_calls,
        require_complete=a.apply,
        verdict_map=vmap,
    )
    n_clean = sum(1 for o in crep.outcomes if o.status == "clean")
    n_split = sum(1 for o in crep.outcomes if o.status == "split")
    n_ref = sum(1 for o in crep.outcomes if o.status == "refused")
    print(f"[6] consistency: {crep.checks} closure-asserted pairs checked "
          f"({crep.cache_hits} cached, {crep.llm_calls} fresh, {crep.unverified} unanswered) — "
          f"{n_clean} clean, {n_split} split, {n_ref} refused -> {len(mergeable)} mergeable clusters",
          flush=True)
    for o in crep.outcomes:
        if o.status == "clean" and not o.unverified:
            continue
        print(f"      {o.describe()}", flush=True)
        for l, r in o.violations[:8]:
            print(f"          {l.name}  ~/~  {r.name}", flush=True)
        if len(o.violations) > 8:
            print(f"          ... and {len(o.violations) - 8} more rejections", flush=True)
        if o.status == "split":
            for sc in o.subclusters:
                print(f"          -> [{sc.size}] {sc.describe()}", flush=True)
            dropped = o.component.size - sum(c.size for c in o.subclusters + o.withheld)
            if dropped:
                merged_ids = {m.node_id for c in o.subclusters + o.withheld for m in c.members}
                names = sorted(m.name for m in o.component.members if m.node_id not in merged_ids)
                print(f"          -> unmerged: {', '.join(names)}", flush=True)
        for w in o.withheld:
            print(f"          WITHHELD [{w.size}] {w.describe()[:110]} (unverified pairs)", flush=True)
        for d in o.disputed_edges:
            print(f"          DISPUTED  {d.describe()}  (excluded from merge)", flush=True)
        if o.unverified and o.status != "refused":
            print(f"          {o.unverified} pairs unverified", flush=True)

    if not a.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to merge.", flush=True)
        sys.exit(0)

    from collections import Counter

    def canonical_for(cluster):
        """Majority of the judge's canonical choices across the cluster's
        cached confirmations; longest-name only as a last resort."""
        tally = Counter()
        names = sorted(m.name for m in cluster.members)
        for i, l in enumerate(names):
            for r in names[i + 1:]:
                cn = A.cached_canonical(l, r, a.label)
                if cn:
                    tally[cn] += 1
        if tally:
            return max(tally.items(), key=lambda kv: (kv[1], len(kv[0]), kv[0]))[0]
        return max(names, key=len)

    from graphrank.config import read_query

    print(f"\n[7] MERGING {len(mergeable)} clusters ...", flush=True)
    merged = 0
    for c in mergeable:
        ids = [m.node_id for m in c.members]
        canon = canonical_for(c)
        # canonicalName is unique per label. The judge's canonical can name a
        # node outside the cluster (its 'YORK' for the servant forms collides
        # with the existing single-word YORK node the person gate excluded).
        # Merging into that node is unverified, so fall back to a member name,
        # whose holder is being absorbed and therefore cannot collide.
        taken = read_query(
            f"MATCH (p:{a.label}) WHERE p.canonicalName = $c AND NOT id(p) IN $ids "
            "RETURN count(p) AS n", c=canon, ids=ids)[0]["n"]
        if taken:
            fallback = max(sorted(m.name for m in c.members), key=len)
            print(f"      canonical '{canon}' taken by an outside node; "
                  f"using '{fallback}'", flush=True)
            canon = fallback
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
        print(f"      [{c.size}] -> {canon}", flush=True)
    print(f"[7] merged {merged} clusters", flush=True)
finally:
    R.drop_graph(R.COOCCURRENCE_GRAPH)

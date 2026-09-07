"""Read-only audit of the lewisclark taxonomy — finds misfiled species.

What it catches, and why each check exists (diagnosed 2026-09-07):

`add_taxonomy.py` left some species unresolved — nodes whose canonicalName is
still an English common name (SWAN, SEAL, BEAR, CARR) — and then genus-matched
them by string. Real genera exist with those spellings (*Swan* is a rove-beetle
genus, *Beara* a moth genus), so the swans were filed under Coleoptera with an
internally consistent chain above them. No graph-local check can catch this:
the chain is right, the attachment is wrong, and the tell is that the species
name is not a taxon name at all.

Checks, cheapest first:

1. **name-shape** (local): a resolved species name is `GENUS EPITHET` or
   `GENUS SP.` — two alphabetic tokens. Anything else (single words, English
   phrases) is an unresolved common name; its BELONGS_TO edge is a guess.
2. **kingdom** (local): AnimalSpecies chains must reach Animalia, PlantSpecies
   must reach Plantae.
3. **gbif** (--gbif, network): strict-match each binomial-shaped name against
   GBIF's species/match API and compare kingdom / order / family / genus with
   the graph's chain. Distinguishes *synonym reassignments* (GBIF resolves the
   name into a different accepted genus — the graph is arguably ahead or behind
   nomenclature, not wrong) from *contradictions* (different order or class —
   misfiled). Responses are cached to disk so re-runs are free and polite.

Writes nothing. Fixes are a separate decision.

Usage:
  python tools/audit_taxonomy.py                    # checks 1-2
  python tools/audit_taxonomy.py --gbif             # + authority verification
  python tools/audit_taxonomy.py --database lewisclark
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, "/Users/nathansmith/Documents/kcdc-2026/graph-algorithms-rag")

ap = argparse.ArgumentParser()
ap.add_argument("--database", default="lewisclark")
ap.add_argument("--gbif", action="store_true", help="verify against GBIF (network)")
ap.add_argument("--limit", type=int, default=0, help="cap GBIF lookups (0 = all)")
a = ap.parse_args()
os.environ["NEO4J_DATABASE"] = a.database

from graphrank.config import read_query

CACHE = Path(__file__).resolve().parent.parent / ".cache" / "gbif"
# Two tokens (binomial), three tokens (subspecific trinomial like URSUS ARCTOS
# HORRIBILIS), or a genus-level placeholder "GENUS SP."
BINOMIAL = re.compile(
    r"^[A-Z][A-Za-z-]+ ([a-z][a-z-]+|[A-Z][a-z-]+)( [A-Za-z-]+)?$|^[A-Z][A-Za-z-]+ SP\.?$",
    re.IGNORECASE,
)


def fetch_species():
    return read_query("""
        MATCH (s:AnimalSpecies|PlantSpecies)
        OPTIONAL MATCH path = (s)-[:BELONGS_TO*]->(k:Taxon {rank:'kingdom'})
        WITH s, path ORDER BY length(path) DESC
        WITH s, collect(path)[0] AS path
        RETURN elementId(s) AS eid, s.canonicalName AS name,
               [x IN labels(s) WHERE x IN ['AnimalSpecies','PlantSpecies']][0] AS label,
               coalesce(s.aliases, []) AS aliases,
               [n IN coalesce(nodes(path), [])[1..] | [n.name, n.rank]] AS chain
        ORDER BY label, name
    """)


def check_name_shape(rows):
    bad = [r for r in rows if not BINOMIAL.match(r["name"] or "")]
    print(f"\n[1] name-shape: {len(bad)} of {len(rows)} species are not "
          f"binomial-shaped (folk-named nodes)")
    # A folk-named node linked at GENUS rank is the string-match bug's
    # signature (its fuzzy lookups always landed on genera: SWAN -> the
    # rove-beetle genus *Swan*). tools/resolve_species_names.py links folk
    # category names only at family rank or higher, GBIF-verified, so those
    # are deliberate — reported separately, not as suspects.
    suspicious = [r for r in bad if r["chain"] and r["chain"][0][1] == "genus"]
    category = [r for r in bad if r["chain"] and r["chain"][0][1] != "genus"]
    print(f"    {len(suspicious)} linked at genus rank — string-match guesses, fix these:")
    for r in suspicious:
        chain = " > ".join(n for n, _ in r["chain"][:3])
        print(f"      {r['name']:<28} [{r['label']}]  -> {chain}")
    print(f"    {len(category)} linked at family+ rank (deliberate category links), "
          f"{len(bad) - len(suspicious) - len(category)} unlinked")
    return bad


def check_kingdom(rows):
    expected = {"AnimalSpecies": "Animalia", "PlantSpecies": "Plantae"}
    wrong = []
    for r in rows:
        kingdoms = [n for n, rank in r["chain"] if rank == "kingdom"]
        if kingdoms and kingdoms[0] != expected[r["label"]]:
            wrong.append((r, kingdoms[0]))
    print(f"\n[2] kingdom: {len(wrong)} species reach the wrong kingdom")
    for r, k in wrong:
        print(f"      {r['name']:<28} [{r['label']}] -> {k}")
    return wrong


def gbif_match(name: str) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^A-Za-z0-9]+", "_", name.lower())
    path = CACHE / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    url = ("https://api.gbif.org/v1/species/match?strict=true&name="
           + urllib.parse.quote(name))
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read())
    path.write_text(json.dumps(data, indent=2))
    time.sleep(0.15)  # polite pacing; cache makes re-runs free
    return data


def check_gbif(rows):
    binomials = [r for r in rows if BINOMIAL.match(r["name"] or "")
                 and not (r["name"] or "").upper().endswith(("SP.", "SP"))]
    if a.limit:
        binomials = binomials[:a.limit]
    print(f"\n[3] GBIF verification of {len(binomials)} binomial species ...")

    tallies = Counter()
    contradictions, synonyms, unknown = [], [], []
    for i, r in enumerate(binomials, 1):
        try:
            g = gbif_match(r["name"].capitalize())
        except Exception as exc:
            tallies["error"] += 1
            unknown.append((r, f"lookup failed: {exc}"))
            continue
        if g.get("matchType") in (None, "NONE"):
            tallies["no-match"] += 1
            unknown.append((r, "GBIF strict match found nothing"))
            continue

        graph = {rank: n for n, rank in r["chain"]}
        # Kingdom disagreement is a hard contradiction regardless of synonymy.
        exp_kingdom = {"AnimalSpecies": "Animalia", "PlantSpecies": "Plantae"}[r["label"]]
        if g.get("kingdom") and g["kingdom"] != exp_kingdom:
            tallies["wrong-kingdom"] += 1
            contradictions.append((r, f"GBIF kingdom {g['kingdom']}, label says {exp_kingdom}"))
            continue

        disagree = [
            (rank, graph.get(rank), g.get(rank))
            for rank in ("order", "family")
            if graph.get(rank) and g.get(rank) and graph[rank] != g[rank]
        ]
        if disagree:
            if g.get("synonym") or (g.get("genus") and graph.get("genus")
                                    and g["genus"] != graph["genus"]):
                tallies["synonym-or-moved"] += 1
                synonyms.append((r, disagree))
            else:
                tallies["contradiction"] += 1
                contradictions.append((r, disagree))
        else:
            tallies["ok"] += 1
        if i % 100 == 0:
            print(f"    {i}/{len(binomials)} checked", flush=True)

    print(f"    tallies: {dict(tallies)}")
    if contradictions:
        print(f"\n    CONTRADICTIONS ({len(contradictions)}) — graph chain disagrees with GBIF:")
        for r, why in contradictions:
            print(f"      {r['name']:<32} {why}")
    if synonyms:
        print(f"\n    reassignments/synonyms ({len(synonyms)}) — likely fine, listed for the record:")
        for r, why in synonyms[:15]:
            print(f"      {r['name']:<32} {why}")
    if unknown:
        print(f"\n    no GBIF strict match ({len(unknown)}) — name may not be a real taxon:")
        for r, why in unknown[:15]:
            print(f"      {r['name']:<32} {why}")


def main():
    rows = fetch_species()
    print(f"Auditing {len(rows)} species on {a.database} (read-only)")
    check_name_shape(rows)
    check_kingdom(rows)
    if a.gbif:
        check_gbif(rows)
    else:
        print("\n(skipped GBIF verification — pass --gbif to run it)")


if __name__ == "__main__":
    main()

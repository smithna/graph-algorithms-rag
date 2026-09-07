"""Resolve the unresolved common-name species nodes to verified taxa.

The audit (tools/audit_taxonomy.py, 2026-09-07) found 101 species whose
canonicalName is still a journal common name (SWAN, BRARO, SEA OTTER), 72 of
them carrying BELONGS_TO edges that were string-match guesses — EAGLES under
the moth genus *Eacles*, MOSQUITOES under Cephalopoda. This pass fixes the
population the honest way:

  1. **Judge**: `gpt-5.6-luna` reads the name, its alias spellings, and up to
     two journal passages, and answers at the most specific rank the evidence
     supports — binomial, genus, higher taxon, or "generic". Verdicts are
     cached on disk (`.cache/species_resolution/`), so re-runs are free and
     deterministic, same pattern as adjudication.
  2. **Authority**: every proposed name is strict-matched against GBIF
     (cache shared with the audit). No GBIF confirmation, no write. The judge
     proposes; the authority disposes.
  3. **Write** (--apply, dry run by default): drop the node's guessed
     BELONGS_TO edges; MERGE the GBIF classification chain as Taxon nodes;
     link the species at its resolved rank; rename to the binomial (or
     'GENUS SP.'), keeping the old name as an alias. A rename that collides
     with an existing node's canonicalName (uniqueness constraint on both
     species labels) merges into that node instead — apoc.refactor.mergeNodes,
     aliases unioned, mentions preserved.

Nodes the judge calls 'generic' or GBIF refuses keep their names and simply
lose their guessed edges: unlinked is honest, linked-by-string-luck is not.

Usage:
  python tools/resolve_species_names.py             # dry run: table only
  python tools/resolve_species_names.py --apply
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, "/Users/nathansmith/Documents/kcdc-2026/graph-algorithms-rag")

ap = argparse.ArgumentParser()
ap.add_argument("--database", default="lewisclark")
ap.add_argument("--model", default="gpt-5.6-luna")
ap.add_argument("--apply", action="store_true", help="write (default: dry run)")
a = ap.parse_args()
os.environ["NEO4J_DATABASE"] = a.database

from graphrank.config import query, read_query, settings

LLM_CACHE = Path(__file__).resolve().parent.parent / ".cache" / "species_resolution"
GBIF_CACHE = Path(__file__).resolve().parent.parent / ".cache" / "gbif"
BINOMIAL = re.compile(
    r"^[A-Z][A-Za-z-]+ ([a-z][a-z-]+|[A-Z][a-z-]+)( [A-Za-z-]+)?$|^[A-Z][A-Za-z-]+ SP\.?$",
    re.IGNORECASE,
)
CHAIN_RANKS = ["kingdom", "phylum", "class", "order", "family", "genus"]

#: Hand-reviewed overrides (2026-09-07), each grounded in the node's passages:
#: EAGLES — the node's mentions are the garter-snake description ("narrow
#:   stripe of light yellow along the center of the back"); the name and the
#:   evidence contradict, and filing either way propagates the upstream
#:   mention-attribution error. Refuse.
#: GRAINS — one mention, a bird list ("Curloos, some Grains, ducks"); the
#:   judge's phonetic-cranes reading is plausible but brant is equally so.
#:   One ambiguous passage is not evidence; the species-level claim was
#:   over-confident. Refuse.
#: NEOGALE VISON — the correct modern name for American mink (2021
#:   reclassification); the GBIF backbone still files it under Neovison, so
#:   the no-match selector would wrongly sweep it in. Leave it alone.
OVERRIDES: dict[tuple[str, str], str] = {
    ("AnimalSpecies", "EAGLES"): "drop-edges",
    ("AnimalSpecies", "GRAINS"): "drop-edges",
    ("AnimalSpecies", "NEOGALE VISON"): "skip",
}

RESOLUTION_PROMPT = """
You are a naturalist-historian of the Lewis and Clark Expedition (1804-1806)
and a taxonomist. You are given a name the journals use for an animal or
plant, its recorded alias spellings, and journal passages where it appears.
Identify the taxon it refers to.

The journals use archaic, phonetic, and French-derived vocabulary: 'braro' is
blaireau (the American badger), 'moonax' is the woodchuck, spellings are
chaotic. The expedition's route — Missouri River, northern Rockies, Columbia,
Pacific coast, 1804-1806 — constrains the candidates. Use the passages.

Answer at the MOST SPECIFIC rank the evidence supports:
- resolution="species": scientific_name is the binomial, when name + context
  determine one species (e.g. "sea otter" on the Pacific coast -> Enhydra lutris).
- resolution="genus": scientific_name is the genus alone, when the species is
  uncertain but the genus is determinate ("swan" could be trumpeter or tundra
  -> Cygnus). rank="genus".
- resolution="higher": scientific_name is a family/order/class, with rank set,
  for genuinely broad terms ("water fowls" -> Anseriformes, rank "order").
- resolution="generic": the term is too vague or heterogeneous to place at any
  useful rank ("bugs"). scientific_name="".

Be conservative: a wrong specific answer is worse than a correct broad one.
Use currently accepted scientific names.
""".strip()


def _schema():
    from pydantic import BaseModel

    class NameResolution(BaseModel):
        resolution: str      # species | genus | higher | generic
        scientific_name: str
        rank: str            # for higher: family/order/class; else may be ""
        note: str            # one short sentence of reasoning

    return NameResolution


def resolve_name(client, label: str, name: str, aliases: list[str],
                 passages: list[str]) -> dict:
    LLM_CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(f"{a.model}::{label}::{name}".encode()).hexdigest()[:32]
    path = LLM_CACHE / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())

    kind = "animal" if label == "AnimalSpecies" else "plant"
    user = f"Journal name for a {kind}: {name}\n"
    if aliases:
        user += f"Alias spellings: {', '.join(aliases[:10])}\n"
    for i, p in enumerate(passages, 1):
        user += f"\nPassage {i}: {p}\n"

    kwargs = dict(
        model=a.model,
        temperature=0,
        messages=[{"role": "system", "content": RESOLUTION_PROMPT},
                  {"role": "user", "content": user}],
        response_format=_schema(),
    )
    endpoint = getattr(client.chat.completions, "parse", None) \
        or client.beta.chat.completions.parse
    try:
        parsed = endpoint(**kwargs).choices[0].message.parsed
    except Exception as exc:
        # GPT-5 generation rejects explicit temperature; drop and retry.
        if "temperature" not in str(exc):
            raise
        kwargs.pop("temperature", None)
        parsed = endpoint(**kwargs).choices[0].message.parsed
    out = {"resolution": parsed.resolution, "scientific_name": parsed.scientific_name,
           "rank": parsed.rank, "note": parsed.note, "name": name, "label": label}
    path.write_text(json.dumps(out, indent=2))
    return out


def gbif_match(name: str, rank: str = "", kingdom: str = "") -> dict:
    """Strict GBIF match, with rank/kingdom hints.

    The hints matter: genus and higher-taxon names are frequently homonyms
    across kingdoms (Cygnus, Pinus, Angelica all collide), and on ambiguity a
    strict match punts to a kingdom-level HIGHERRANK result. Scoping the query
    resolves the homonym instead of refusing the name.
    """
    GBIF_CACHE.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^A-Za-z0-9]+", "_", f"{name}|{rank}|{kingdom}".lower())
    path = GBIF_CACHE / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    url = ("https://api.gbif.org/v1/species/match?strict=true&name="
           + urllib.parse.quote(name))
    if rank:
        url += "&rank=" + urllib.parse.quote(rank)
    if kingdom:
        url += "&kingdom=" + urllib.parse.quote(kingdom)
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.loads(resp.read())
    path.write_text(json.dumps(data, indent=2))
    time.sleep(0.15)
    return data


def normalise(sci: str) -> str:
    toks = sci.strip().split()
    if not toks:
        return ""
    return " ".join([toks[0].capitalize()] + [t.lower() for t in toks[1:]])


def _res_type(res: dict) -> str:
    """Normalise the judge's resolution field — it sometimes answers with a
    rank word ('family') instead of the 'higher' bucket."""
    r = (res.get("resolution") or "").lower()
    if r in ("species", "genus", "generic"):
        return r
    if r in ("higher", "family", "order", "class", "phylum", "subfamily", "tribe"):
        return "higher"
    return "unknown"


def verify(res: dict, label: str) -> tuple[dict | None, str]:
    """GBIF-verify a judge resolution. Returns (gbif_response, reason-if-refused)."""
    kind = _res_type(res)
    if kind == "generic" or not res["scientific_name"]:
        return None, "generic"
    if kind == "unknown":
        return None, f"unrecognised resolution '{res.get('resolution')}'"
    sci = normalise(res["scientific_name"])
    kingdom_hint = {"AnimalSpecies": "Animalia", "PlantSpecies": "Plantae"}[label]
    rank_hint = {"species": "SPECIES", "genus": "GENUS"}.get(kind) \
        or (res.get("rank") or "").upper()
    try:
        g = gbif_match(sci, rank=rank_hint, kingdom=kingdom_hint)
    except Exception as exc:
        return None, f"gbif lookup failed: {exc}"
    if g.get("matchType") in (None, "NONE"):
        return None, "no strict GBIF match"
    ok_kingdoms = {"AnimalSpecies": {"Animalia"},
                   "PlantSpecies": {"Plantae", "Chromista"}}[label]
    if g.get("kingdom") not in ok_kingdoms:
        return None, f"GBIF kingdom {g.get('kingdom')} vs label {label}"
    want = {"species": {"SPECIES", "SUBSPECIES"},
            "genus": {"GENUS"},
            "higher": {"FAMILY", "ORDER", "CLASS", "PHYLUM"}}[kind]
    if g.get("rank") not in want:
        return None, f"GBIF rank {g.get('rank')} vs claimed {res['resolution']}"
    return g, ""


def plan_action(row, res, g) -> dict:
    """What --apply will do for one node. Pure planning, no writes."""
    if g is None:
        return {"action": "drop-edges", "why": res}
    if _res_type(res) == "species":
        canon = g["canonicalName"].upper()
    elif _res_type(res) == "genus":
        canon = f"{g['canonicalName'].upper()} SP."
    else:
        canon = row["name"]  # higher: keep the folk name, just link it right
    chain = [(g[r].strip(), r) for r in CHAIN_RANKS if g.get(r)]
    lowest = chain[-1]
    existing = read_query(
        """
        MATCH (x:AnimalSpecies|PlantSpecies)
        WHERE toUpper(x.canonicalName) = $canon AND elementId(x) <> $eid
        RETURN elementId(x) AS eid, x.canonicalName AS name LIMIT 1
        """, canon=canon, eid=row["eid"])
    return {
        "action": ("merge" if existing and canon != row["name"] else
                   "link" if canon == row["name"] else "rename"),
        "canon": canon, "chain": chain, "lowest": lowest,
        "target": existing[0] if existing else None,
    }


def apply_action(row, plan) -> None:
    query("MATCH (s) WHERE elementId(s) = $eid "
          "OPTIONAL MATCH (s)-[r:BELONGS_TO]->() DELETE r", eid=row["eid"])
    if plan["action"] == "drop-edges":
        return
    # Taxon chain, top-down, honouring the (rank, name) uniqueness constraint.
    chain = plan["chain"]
    for (name, rank) in chain:
        query("MERGE (:Taxon {name: $name, rank: $rank})", name=name, rank=rank)
    for (child, parent) in zip(chain[1:], chain[:-1]):
        query("""
            MATCH (c:Taxon {name: $cn, rank: $cr}), (p:Taxon {name: $pn, rank: $pr})
            MERGE (c)-[:BELONGS_TO]->(p)
        """, cn=child[0], cr=child[1], pn=parent[0], pr=parent[1])

    if plan["action"] == "merge":
        # apoc's default property strategy lets the absorbed node's properties
        # OVERWRITE the target's — the first apply of this script turned
        # BISON BISON into BISON that way. Re-assert the identity explicitly,
        # exactly as the Person merge in disambiguate_layered.py does.
        query("""
            MATCH (target) WHERE elementId(target) = $tid
            MATCH (s) WHERE elementId(s) = $eid
            WITH target, s,
                 coalesce(target.aliases, []) + coalesce(s.aliases, [])
                 + [target.name, target.canonicalName, s.name, s.canonicalName] AS raw
            CALL apoc.refactor.mergeNodes([target, s],
                 {mergeRels: true, produceSelfRel: false}) YIELD node
            SET node.canonicalName = $canon, node.name = $display,
                node.aliases = [x IN coll.distinct(raw)
                                WHERE x <> $display AND x <> $canon]
        """, tid=plan["target"]["eid"], eid=row["eid"],
              canon=plan["canon"], display=plan["canon"].title())
        node_ref = ("MATCH (s) WHERE elementId(s) = $eid",
                    {"eid": plan["target"]["eid"]})
    else:
        if plan["action"] == "rename":
            query("""
                MATCH (s) WHERE elementId(s) = $eid
                WITH s, coalesce(s.aliases, []) + [s.name, s.canonicalName] AS raw
                SET s.canonicalName = $canon, s.name = $display,
                    s.aliases = [x IN coll.distinct(raw)
                                 WHERE x <> $display AND x <> $canon]
            """, eid=row["eid"], canon=plan["canon"],
                  display=plan["canon"].title())
        node_ref = ("MATCH (s) WHERE elementId(s) = $eid", {"eid": row["eid"]})

    match, params = node_ref
    query(f"""
        {match}
        MATCH (t:Taxon {{name: $tn, rank: $tr}})
        MERGE (s)-[:BELONGS_TO]->(t)
    """, **params, tn=plan["lowest"][0], tr=plan["lowest"][1])


def main() -> None:
    all_rows = read_query("""
        MATCH (s:AnimalSpecies|PlantSpecies)
        OPTIONAL MATCH (s)-[:MENTIONED_IN]->(c:Chunk)
        WITH s, collect(c.text)[0..2] AS passages
        RETURN elementId(s) AS eid, s.canonicalName AS name,
               [x IN labels(s) WHERE x IN ['AnimalSpecies','PlantSpecies']][0] AS label,
               coalesce(s.aliases, []) AS aliases,
               [p IN passages | left(p, 400)] AS passages
        ORDER BY label, name
    """)

    # "Unresolved" = not the shape of a scientific name, OR shaped like one but
    # unknown to the authority — "SWAN GEESE" is two tokens and fools any
    # regex; GBIF strict match is the selector that cannot be fooled. The
    # existence probes share the audit's cache, so they are free after the
    # first audit run.
    def unresolved(row) -> bool:
        if OVERRIDES.get((row["label"], row["name"])) == "skip":
            return False
        name = row["name"] or ""
        if not BINOMIAL.match(name):
            return True
        if name.upper().endswith(("SP.", "SP")):
            return False
        try:
            return gbif_match(normalise(name)).get("matchType") in (None, "NONE")
        except Exception:
            return False  # network trouble: leave the node alone this run

    rows = [r for r in all_rows if unresolved(r)]
    print(f"{len(rows)} unresolved species on {a.database} "
          f"(of {len(all_rows)} total)", flush=True)

    from openai import OpenAI
    client = OpenAI(api_key=settings().openai_api_key)

    plans, counts = [], {}
    for i, row in enumerate(rows, 1):
        res = resolve_name(client, row["label"], row["name"],
                           row["aliases"], row["passages"])
        if OVERRIDES.get((row["label"], row["name"])) == "drop-edges":
            g, refused = None, "hand-reviewed override (see OVERRIDES)"
        else:
            g, refused = verify(res, row["label"])
        plan = plan_action(row, res if g else refused, g)
        plans.append((row, res, g, plan))
        counts[plan["action"]] = counts.get(plan["action"], 0) + 1
        if i % 20 == 0:
            print(f"  {i}/{len(rows)} judged", flush=True)

    print(f"\nplan: {counts}\n", flush=True)
    for row, res, _g, plan in plans:
        sci = res.get("scientific_name") or "-"
        if plan["action"] == "drop-edges":
            print(f"  DROP-EDGES  {row['name']:<28} ({res.get('resolution','?')}: "
                  f"{sci}; {plan['why'] if isinstance(plan['why'], str) else ''})",
                  flush=True)
        else:
            chain = " > ".join(n for n, _ in plan["chain"][::-1][:4])
            tgt = f" -> MERGE INTO {plan['target']['name']}" if plan["action"] == "merge" else ""
            print(f"  {plan['action'].upper():<11} {row['name']:<28} -> "
                  f"{plan['canon']:<34} [{chain}]{tgt}", flush=True)

    if not a.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply.", flush=True)
        return

    print("\nApplying ...", flush=True)
    for row, res, g, plan in plans:
        # Re-plan against the live database: an earlier apply in this loop may
        # have renamed a sibling onto the same canonical (SWAN and SWANS both
        # resolve to CYGNUS SP.), turning this row's rename into a merge — the
        # uniqueness constraint on canonicalName makes the stale plan a crash.
        live = plan_action(row, res, g) if g is not None else plan
        if live["action"] != plan["action"]:
            print(f"  re-planned {row['name']}: {plan['action']} -> {live['action']}",
                  flush=True)
        apply_action(row, live)
    print(f"Applied {len(plans)} resolutions.", flush=True)


if __name__ == "__main__":
    main()

# Prompt: validate the section 4 demos end-to-end

Copy everything below the line into a fresh session.

---

Run and validate the **section 4 (entity resolution) demos** for the KCDC talk,
now that the `lewisclark` pipeline is complete. The goal is a demo path that
works end-to-end, measured results written into `talk-outline.md`, and a
recommendation on what each demo runs against. Code and measurements first;
no slides.

## Read first

1. `docs/talk-outline.md` — section 4 and findings **3 through 3g** (3g is the
   consistency-gated merge that finished the work; finding 3's "Measured at
   last" holds the enrichment split).
2. `docs/picking-up-entity-resolution.md` — the banner at the top is the
   current state; the operational traps section further down still applies.

## State you can rely on (verified 2026-09-07, do not re-derive)

- `lewisclark` is fully built: 675 Person nodes (consistency-gated
  disambiguation, finding 3g), Sacagawea at 85 chunks / 32 aliases with
  provenance-tagged enrichment links (`r.source`, `r.externalOnly`,
  `r.alsoExternal`), taxonomy repaired (0 string-guess edges;
  `tools/audit_taxonomy.py` is the regression check), 41 `corpsMember=true`
  tags, 10 fulltext indexes (incl. `person_search`, `entity_search`), and
  vector embeddings on **AnimalSpecies / PlantSpecies / Event / Taxon only**
  (1,506 nodes, per-label indexes). Person/Place/WaterBody/NativeNation are
  fulltext-only **by design** — see "Design notes" in the outline before
  "fixing" that.
- `rawluna` is the frozen pre-disambiguation measurement baseline; `neo4j` is
  the current demo graph for sections 5–8. Both must stay untouched.
- Checkpoints under `corps-of-discovery-graph-rag/data/checkpoints/`:
  `lewisclark-pre-disambiguation`, `-post-disambiguation`,
  `-post-enrichment`, `-post-species-resolution` (latest). Restore procedure
  is in the handoff doc.
- Caches make everything re-runnable for free: `.cache/adjudication/` (~3k
  verdicts incl. rejections), `.cache/species_resolution/`, `.cache/gbif/`.
  `tools/disambiguate_layered.py` (dry run) reproduces the full layered
  pipeline from cache, byte-identical — 2,144 candidates in, 40 clusters out,
  zero API calls.

## What to do

1. **Run the section 4 demo scripts against their intended databases** and fix
   what breaks. `scripts/demo_resolution.py` measures on `rawluna` (read-only;
   it warns if pointed at `neo4j`). Locate `demo_paths.py` and run it against
   `lewisclark` — its dependencies (`person_search`, embeddings) are satisfied
   for the first time, and it has never actually run there.
2. **Decide and verify the demo arc.** The intended shape: candidates at
   recall settings on `rawluna` (read-only, the 2c/3 story) → the layered
   dry run showing adjudication/evidence/transitivity/consistency (3e/3g)
   → `lewisclark` as the applied "after" graph (Sacagawea 8 → 47 chunks from
   corpus evidence, 85 with tagged enrichment; Brattons split; Ordway intact).
   Time each step — the dry run is cache-only and should be demo-fast, but
   verify, and note anything that projects poorly (long output, slow steps).
3. **Spot-check retrieval on `lewisclark`** with the queries the demos will
   issue: fuzzy fulltext (`Crusatte~` → PETER CRUZATTE), alias resolution
   (`Minnetarees` → HIDATSA), vector lanes (`elk` → CERVUS CANADENSIS,
   `salmon` → Salmonidae, `birth of a child` → the Charbonneau birth).
4. **Write results into the outline** (section 4 working notes / the demo
   checklist), per the measurement discipline memory: real numbers, stated
   conditions, no round-trip claims from memory.

## Known issues to expect (don't rediscover them)

- Fulltext ranking favors unmerged shards: `"interpreters wife"` puts
  SACAGAWEA at rank ~6 behind sparse leftovers (`HIS WIFE`,
  `WIFE OF SHABONO`). Real, disclosed, possibly a talk beat — decide whether
  the demo needs mention-count boosting or just different example queries.
- Vector lane: generic nodes are embedded (`ROOTS` outranks `CAMASSIA SP.`
  for "camas root"); Floyd ranks 3rd for "death of a corps member". Both are
  candidates for either a fix or a disclosed caveat.
- The DBMS heap is still **1 GiB** — Desktop discarded a manual
  `neo4j.conf` edit (it regenerates the file; use Desktop's Settings UI).
  GDS projections OOM'd once at this size. If demos need GDS, check
  `gds.debug.sysInfo` first and get the heap raised before measuring.
- Corps scripts follow the **home database** — never run one unpatched;
  patches live in `tools/corps-patches/`. Home stays `neo4j`; pass
  `NEO4J_DATABASE=` explicitly.
- A parallel workstream uses `budgetluna` (section 5) — leave it alone, and
  stage explicit git paths, never `git add -A`.
- Do not modify the `corps-of-discovery-graph-rag` repo.

## Open questions to answer with measurements

- Does `lewisclark` fully replace `neo4j` for section 4's live demo, or is it
  the "after" exhibit while the walkthrough runs read-only on `rawluna`?
- Is the layered dry run demoable live (wall time, output volume on a
  projector), or does it need a `--demo` trimmed output mode?
- The person-embeddings fallback idea (outline "Design notes") — does any
  demo query actually need it, or does it stay noted-for-later?

# Picking up the entity resolution work

Handoff for the unfinished part of section 4: **disambiguating `lewisclark`**.
Nothing in the talk depends on this. Section 4 demos against `neo4j` and
`rawluna`, both of which work today. This is an improvement that stalled on a
real problem, and it is worth resuming only when there is time to do it properly.

Read [`talk-outline.md`](talk-outline.md) findings **3c–3f** first — they hold
the reasoning. This file holds the operational detail that does not belong in
the outline.

---

## Current state

| database | what it is | status |
|---|---|---|
| `neo4j` | v1.0 dump, fully built, all indexes | **the demo graph** — do not disturb |
| `rawluna` | pre-disambiguation, `gpt-5.6-luna` extraction, frozen | section 4 measurement baseline |
| `lewisclark` | clone of `rawluna` + mention resolution + taxonomy | **parked at 794 Person nodes** |
| `rawgraph` | old `gpt-4o-mini` extraction | retired |

`lewisclark` has had:

- `ingest.py` (2,913 chunks) and `extract.py` with `gpt-5.6-luna`
- `resolve_mentions.py` (17 single-word Person nodes absorbed)
- `fix_waterbody_labels.py`, `flag_generic_locations.py`, `cleanup_relationships.py`
- `add_taxonomy.py` (833 species resolved, species merged 952 → 578)
- `enrich_sacagawea.py`, **then its contributions deliberately removed** — see below

It has **not** had: `disambiguate.py`, `tag_corps_members.py`,
`setup_fulltext_indexes.py`, `embed_entities.py`. Without the last two,
`demo_paths.py` fails on it (no `person_search` index).

### Restore points

```
corps-of-discovery-graph-rag/data/checkpoints/
    lewisclark-post-taxonomy/lewisclark.dump      # before scraper links were removed
    lewisclark-pre-disambiguation/lewisclark.dump # ← current state, use this one
```

```bash
neo4j-admin database load lewisclark \
  --from-path=<checkpoint dir> --overwrite-destination=true
```

The database must be **stopped** first (`STOP DATABASE lewisclark`), but the
DBMS can stay up — stopping the whole DBMS would disturb other work.
`neo4j-admin` is not on `PATH`; use the copy under Neo4j Desktop's application
support directory and set `JAVA_HOME` to Desktop's bundled JRE.

### The Sacagawea provenance experiment

`enrich_sacagawea.py` scrapes 13 surface forms from lewis-clark.org. The patched
copy tags everything it creates:

```
(:Person {canonicalName:'SACAGAWEA'})-[r:MENTIONED_IN]->(:Chunk)
    r.source = 'lewis-clark.org'   r.externalOnly = true   r.alsoExternal = true
```

Those 56 `externalOnly` links **and** the 13 aliases were then removed, so
disambiguation runs on honest data and the section 4 claim ("the algorithm found
her, not a website") holds on the demo graph itself. `p.externalAliases` still
holds the 13 forms, so re-adding them afterwards is trivial — and the
before/after split is the measurement section 4 actually wants: how much the
scraper adds *beyond* what the graph found.

Sacagawea is currently back to un-enriched geometry: **8 chunks, 8 aliases, 52
co-occurrence neighbours** — matching `rawluna` (51) apart from one mention that
`resolve_mentions` re-routed.

---

## Why it is parked

Two dry runs, both on Person, 2,144 candidates, **nothing written**:

| | node removal | edge removal |
|---|---|---|
| components | 31 | 42 |
| Sacagawea | fragmented into 2, her node in neither | whole but contaminated |
| bad merges | some | five Brattons as one man; Drouillard with Mandan chiefs |

**Root cause: the layered script drove candidate generation from
`resolution.py`'s defaults** — OVERLAP, `minCount=1`, `topK=100` — which exist
for read-only analysis where nothing merges. Finding 3c says exactly this is
unsafe under WCC closure. `tools/corps-patches/disambiguate.patch` already
carries conservative settings; the layered script bypassed them.

**First thing to try on resuming:** re-run `tools/disambiguate_layered.py` with
conservative candidate generation (COSINE, cutoff 0.5, `minCount` 2, `topK` 10)
instead of `resolution.py`'s defaults. That single change may be most of the fix,
and it was never tested.

**The real problem underneath** is correlation clustering with must-not-link
constraints: closure must respect negative verdicts, not only positive ones.
Greedy approximations are order-dependent. Practical options:

1. deterministic edge order (descending evidence) and accept an approximation
2. refuse to merge wherever constraints conflict — recoverable, probably right here
3. cap component size and refuse the rest (already implemented as a backstop)

---

## What is in `tools/`

Patched copies of the corps scripts live as **diffs**, not forks, so the
originals stay authoritative:

| file | what it changes |
|---|---|
| `corps-patches/disambiguate.patch` | Jaro-Winkler inversion fix; `gpt-5.6-luna`; GPT-5 temperature guard; explicit `NEO4J_DATABASE` + `gds.set_database` |
| `corps-patches/resolve_mentions.patch` | model + temperature guard + explicit database |
| `corps-patches/add_taxonomy.patch` | same |
| `corps-patches/enrich_sacagawea.patch` | provenance tagging on `MENTIONED_IN` |
| `disambiguate_layered.py` | candidates → adjudicate → evidence → transitivity → merge, `--apply` gated, dry run by default |
| `gate.py` | aborts on mega-clusters, collapsed Person count, or Drouillard appearing in Sacagawea's aliases |

Apply a patch with `patch -o out.py original.py the.patch`, or read it as
documentation of what needed fixing.

---

## Operational traps, all of which have already bitten

1. **The corps scripts follow the HOME DATABASE.** They call `driver.session()`
   with no database. The patches fix this, but any *unpatched* script silently
   targets whatever home is set to. Leave home on `neo4j`; pass
   `NEO4J_DATABASE=` explicitly.
2. **GDS graph names are per-database but shared within one.** Two processes
   disambiguating the same database collide on `entity-cooccurrence` — one drops
   the graph under the other, and `disambiguate.py` swallows the error and
   silently returns no candidates. Never run two resolution jobs on one database.
3. **Checkpoint before LLM-driven merging, not after.** That boundary is where
   recovery costs one minute instead of two hours. Taxonomy alone is ~100 minutes.
4. **`add_taxonomy.py` is not additive** — it merges species (952 → 578 here)
   while resolving common names to binomials.
5. **Two conversations, one repo.** `git add -A` from another session will sweep
   in-flight work into unrelated commits. Stage explicit paths.
6. **`adjudicate()` is now parallel** (`max_workers=8`); serial was 5 verdicts/min
   versus ~150. `verify_transitivity()` is still serial and would benefit.

---

## The cache is an asset — do not delete it

`.cache/adjudication/` holds ~2,900 verdicts (~5 MB, gitignored), **including
rejections**. On the second dry run **444 of 444 transitivity checks were
answered from cache with zero API calls.** It makes re-runs nearly free and
byte-for-byte reproducible. If you need a clean measurement, point
`CACHE_DIR` elsewhere rather than deleting this.

---

## What already works and should not be re-litigated

- adjudication rejects ~76% of candidates — the recall/precision division of labour
- the evidence filter (≥2 chunks on one endpoint) removes one-chunk-to-one-chunk
  confirmations, which is where the Nez Perce/Hidatsa/Clatsop false merges came from
- transitivity verification correctly finds bridge nodes
- several components are unambiguously correct: **16 spellings of Cruzatte**,
  7 of Frazer, 5 of Weiser, 4 of Goodrich, 3 of Howard

The layers are sound. The input they were fed was not.

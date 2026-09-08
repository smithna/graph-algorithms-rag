# KCDC 2026 — Graph Algorithms for RAG: talk outline + build plan

> **This file is the source of truth for the talk.** It holds the section
> outline, the timings, and the build progress. Work happens one talk section
> per conversation — start any new session by reading this file, then the
> Progress table below to see where things stand.

## Progress

Talk sections are built one at a time. `Code` is what has to exist in this repo
before the section's slides can be written honestly.

| # | Section | Code | Status |
|---|---|---|---|
| — | **Step 0: verify repo against a live DBMS** | all existing scripts | ✅ **Done** — dump restored, every script runs clean |
| 0 | Cold open — the failure | `baseline.py` | ✅ verified live |
| 1 | What is a graph? | none | not started |
| 2 | What is Graph RAG / evidence | none (sources gathered) | not started |
| 3 | Roadmap | none | not started |
| 4 | Entities are a mess → node similarity + WCC | `resolution.py`, `adjudicate.py`, `demo_resolution.py`, `cooccurrence.py` | ✅ **built, verified, and the section's story settled** — Sacagawea cluster is the spine; see *Section 4 findings* |
| 5 | Ranking can't tell people apart → entity-seeded PPR | `pagerank.py`, `projection.py`, `decompose.py`, `demo_pagerank.py`, `sweep_pagerank.py`, `measure_seeds.py`, `measure_extraction_grade.py`, `measure_ablation.py`, `measure_budget_graph.py`, `measure_name_shards.py` | ✅ **built, verified live, slides drafted** — thesis settled on the third attempt (co-typed entity substitution); `charbonneau-role` is the spine. **Start at *Section 5 in one page*.** New: decomposed seeder (5d-ter's fix), built + measured — named-entity coverage 10/11 vs semantic 8/11, finding 5f. Open: title, demo-graph choice, whether 5f gets stage time. New: 5h screens PPR's remaining case after 5g's filter parity; **framing approved** (5h-5: gold-plated §4 path vs budget cheap-extraction path, walk compensates at query time). **Ablation built and measured (5i, `measure_ablation.py`): the filter goes blind to the coref-only passages and the walk does NOT buy them back — ranks 114–1108 ablated vs 11–62 full; SACAGAWEA keeps 6/64 edges; NEXT_CHUNK is no coref patch. Replicated on a REAL budget graph (5j, `measure_budget_graph.py` on new `budgetluna` = rawluna + indexes, no resolution): harsher — identity shattered across 19 shards + 25 untagged chunks, fever/Aug-14 at rank 1709/1475, and the edge-support metric scores the worse graph better. Multi-shard seeding measured (5j-bis): oracle shards restore even the FILTER on 2 of 3 — query-time compensation is query-time entity resolution; the sole adjacency win needs the impure shard the correct merge excludes. "About as good, less work up front" refuted; surviving beat: the walk covers duplicates and hubs; shards need resolving — at build time once or at query time forever. Spelling-shard case measured (5k, `measure_name_shards.py`): DREWYER 265 / GEORGE DROUILLARD 63 unmerged ON THE DEMO GRAPH — 5g's parity requires *resolved* tags; vector discovery ranks the other spelling #22 behind the Dorions; the walk trails cosine at bridging it; the df-prop merged walk (median 168) or a two-tag filter fixes it — the easy §3-machinery merge the pipeline never ran. New: 5l (`measure_thematic.py`, on `lewisclark`): thematic questions are the no-filter class — all three decompose to zero mentions, bar drops to cosine alone; hand-read verdict: expand **wins trade-goods** (buttons-off-coats promoted from cosine 77, Twisted Hair gun payment from 112, month coverage 3→7, carried by df-4..16 Supply nodes) **and food-sources** (5→7 months, ration passage from rank 34), **collapses illness-and-injury onto one episode** (4→1 months, 7/8 chunks from Long Camp May 1806) — the measured hand-off to §6 diversification. Passage half discriminative; junk Event entity seeds mattered by demotion, not promotion. New: 5m (`measure_neighborhood.py`, `lewisclark`): neighborhood questions ("Sacagawea's brother") — filter covers 2/16 and 1/8 by construction; hub-anchor flagship fails ALL strategies in the top-8 (bridge = 2 of the anchor's 85 edges; delete-test 338→601 median confirms the bridge is the mechanism) but pure walk surfaces the *name* at rank 4 → two-step retrieval; low-df-anchor replication (Walla Walla chief, anchor df 3) wins one-shot: blend median 10 vs cosine 43, walk crosses 1-of-12 nation shards to the chief's untagged chunks. New: 5n (`measure_bridge_decay.py`): Nathan's agent rule measured as a curve — 38k anchor/satellite pairs, median walk-rank of exclusive chunks monotonic in anchor df (39 at df 2-5 → 1058 at df 300+, no exceptions); routing table: df≲15 expand, df≳40 filter (5g) or two-step (5m), zero mentions passage-expand (5l); §9 material — the graph-tool decision is one COUNT query. **Stage close redrafted (2026-09-07): 5.12–5.14 in `section-05-slides.md` now tell the 5l/5m/5n story (buttons → the brother's name → the routing table), decay curve parked for §9; section runs 14:00 raw, cut plan to 10:00 drafted; sign-offs pending: trims inside protected beats, or 5.12→§6.** **MIGRATED to `lewisclark` (2026-09-07, finding 5o): every 5.1–5.11 number re-measured — failure table 69/300/2; Lewis is now the TOP hub (825 chunks, 28.3%: the deer punchline is dead, elk-outranks-Clark replaces it); ladder 2.84→0.47/8; damping direction holds; alpha=1.0 verifies 14/14; fresh question ~215 ms; hand read redone on the new windows, 3/11 clear (Nathan's read pending); receipts adapted — duplicate seeding now PACIFIC OCEAN/OCIAN df-proportional (one SACAGAWEA remains, §4 merged it), degree imbalance now LEWIS+CYNOMYS (6.1% bonus), extraction bound now the missing keelboat (the horse receipt got FIXED by luna: Aug-18 passage carries HORSES and ranks #1). Slides updated; `neo4j` history kept in findings 1–5k** |
| 6 | Context is redundant → communities | `communities.py`, `demo_communities.py`, `measure_communities.py` | ✅ **built, measured on `lewisclark`, slides drafted** — Leiden + conductance added; seeded Leiden is the measured partition (Louvain redraws every run, 6a); Louvain's disconnected-community flaw caught live (1,089-node case) and GDS Leiden's guarantee has a measured asterisk (6b); `diversify()` caps *any* strategy's slate — capping the walk repairs 5l's illness collapse (1→4 months, recovers Lewis's gunshot + Fort Clatsop sick-list, hand-read) and is byte-identical on the two questions the walk already wins (6c). Read-pack: `results/communities-lewisclark.md`; slides [`docs/section-06-slides.md`](section-06-slides.md). **Stage scope decided 2026-09-07: Leiden only — Louvain findings are Q&A backup, no slide time** |
| 7 | Can't explain → path finding | `paths.py`, `demo_paths.py` | ✅ **built, measured on `lewisclark`, slides drafted** — both section claims audited by hand-reading 22 routes / 85 receipt passages (read-pack: `results/paths-lewisclark-readpack.md`, local only). The k claim was BACKWARDS on a typed graph (7a): mechanism at k=1 when the edge exists; the brother pair has NO sibling edge anywhere, so the recognition scene arrives at k=3 via the Event node, both hops citing the same chunk — 5m's two-step completes (7g). Receipts hold, and the five wrong edges they expose are the demo (7b: wrong-captain GUIDED, Cameahwait-as-Hidatsa). `[0]` receipt pick replaced — merged arrays are ragged, 11 chunkIds vs 8 dates (7c); BELONGS_TO fallback returns zero passages silently, taxonomy route needs raw k=40 (7d); Yen's dedup + deterministic tie-sort shipped (7e: k=25 raw → 7 unique, tie order unstable across runs); Step-0 resolver incident reproduces with SHOSHONE BOY as the decoy, fix verified; HIS WIFE tautology route is §4-refusal-meets-§7 (7f). Slides [`docs/section-07-slides.md`](section-07-slides.md) |
| 8 | Does this help? | `benchmark.py`, `metrics.py` | runs; **gold set is broken worse than reported** — 4 labels missing *and* at least 4 more silently resolving to near-empty decoy nodes. See *Section 5 findings* #10 |
| 9 | How to implement | docs only | not started |
| 10 | Takeaways | none | not started |
| — | **Step 6: the deck** | reveal.js, vendored offline | scaffold not started; **section 4 slide content drafted** — [`docs/section-04-slides.md`](section-04-slides.md) |

### Step 0 results (2026-09-06)

The `.env` credentials were real but the database was **empty** — the corps
dump had never been restored. Restored `lewis-clark-graphrag.dump` from the
v1.0 release into the Desktop-managed Enterprise 2026.07.1 DBMS via
`neo4j-admin database load` (the `neo4j` database stopped, the DBMS left
running). Live shape:

| | |
|---|---|
| Chunk nodes | 2,913 |
| Entity nodes | 3,992 |
| MENTIONED_IN | 16,518 |
| GDS projection | 6,959 nodes / 49,040 rels in **267 ms** |
| GDS / APOC | 2026.7.0, all required procedures present |

Every outline compatibility risk resolved: `gds.nodeSimilarity.filtered` is GA
(no `beta.` fallback needed), `gds.leiden` and `gds.conductance` both exist,
`client.chat.completions.parse` exists in openai 3.8.0, `pydantic` and a
`graphdatascience<2` pin are now in `requirements.txt`.

**Two real breakages found and fixed:**

1. **`demo_paths.py` returned nothing for Sacagawea → Shoshone.** There are two
   `SHOSHONE` nodes: the real `:NativeNation` with 205 mentions, and a stray
   `:Person` with 1. Lucene scored the stray *higher* (7.32 vs 6.66), because
   full-text scoring rewards rarity within an index and knows nothing about how
   much the corpus talks about a node. Resolution picked the stray, which has no
   extracted relationships, so every path query through it returned empty —
   silently. `resolve.py` now breaks near-ties on mention count. This is the
   entity-resolution failure of section 4 breaking section 7's demo, live, and
   it is worth one sentence from the stage.
2. **Notification and progress-bar noise.** `id()` deprecation warnings fired
   six times per query as multi-line blocks, and the GDS client's tqdm bars
   redraw into a smear when captured. Both silenced in `config.py`; `id()` is
   used deliberately, since GDS streams internal node ids and `elementId()` will
   not join to them.

Still outstanding: `verify_questions.py` reports **4 unresolved gold labels**
(`CAMAS` → `CAMASSIA QUAMASH`, `PRAIRIE DOG`, and two others). That is Step 5,
not section 4, and no benchmark number should be quoted until it runs clean.

### Section 4 findings — working notes, not slide material

> ⚠️ **Numbers below are for our own decision-making.** Nathan's call: no
> precision or recall claims go on a slide, because the gold set is a hand-built
> reference rather than ground truth — see *3b. What the gold set is, and what
> it is not*. The section is carried by the Sacagawea example instead. Keep
> these tables; they are how we chose the metric, the model and the thresholds.

Section 4's code is built, runs read-only, and has been measured against three
independently built graphs:

| database | what it is | status |
|---|---|---|
| `rawluna` | pre-disambiguation, `gpt-5.6-luna` extraction | **keep, frozen** — the section-4 measurement baseline, and where the live walkthrough runs (read-only) |
| `lewisclark` | clone of `rawluna` + mentions + taxonomy + **consistency-gated disambiguation** | **pipeline complete 2026-09-07** (675 Persons, 41 corps tags, 10 fulltext indexes, embeddings on 4 labels) — section 4's "after" graph; demo path validated, see *3h* |
| `neo4j` | the v1.0 dump — `gpt-4o-mini` extraction throughout | **keep** — the demo graph for sections 5–8; section 4's "after" exhibit moved to `lewisclark` (see 3h) |
| `rawgraph` | pre-disambiguation, `gpt-4o-mini` extraction | retired |

**Why `neo4j` is being replaced rather than kept as the "after" graph.** It is
not a better graph, only an older one — its entities and relationships come from
a `gpt-4o-mini` extraction that we measured as producing 39% fewer mention edges
and roughly four times as many malformed concatenated-name nodes. Finishing
`rawluna` gives a demo graph on the better extraction; `rawluna` itself stays
frozen so the pre-disambiguation baseline survives.

**The resolution steps were run on corrected copies**, not the shipped scripts —
`disambiguate.py` with the Jaro-Winkler inversion fixed, `gpt-5.6-luna` as the
judge, and OVERLAP/idfWeighted/topK=100/minCount=1 from finding 2c. Running it
as shipped would have baked both known defects straight into the demo graph.

**Sacagawea provenance is now recorded in the graph.** `enrich_sacagawea.py`
still runs — the demo graph should retrieve her as well as possible — but the
patched copy tags every relationship it creates:

```
(:Person {canonicalName:'SACAGAWEA'})-[r:MENTIONED_IN]->(:Chunk)
    r.source       = 'lewis-clark.org'   -- the scraped list supplied it
    r.externalOnly = true                -- only the website found it
    r.alsoExternal = true                -- corpus AND website found it
```

plus `p.externalAliases` holding the 13 scraped surface forms. Before
resolution the split is **56 external-only / 4 both / 4 corpus-only**, so the
website is doing nearly all the work at that point. The number that matters is
the same split *after* resolution has merged her other eighteen nodes — that is
the honest measure of how much of a hand-curated external source the algorithm
actually replaces, and it can be queried live on stage.

All findings below are settled. Finding #2 went through a retraction on the way
— the first version of that experiment was biased — and the history is kept,
because it is the most useful thing in this section.

#### 1. The string ladder in `disambiguate.py` is inverted

`apoc.text.jaroWinklerDistance` returns a **distance**, not a similarity:

```
apoc.text.jaroWinklerDistance('SHIELDS', 'SHIELDS')  =  0.0
apoc.text.jaroWinklerDistance('MARTHA',  'MARHTA')   =  0.0389   → 1 − x = 0.961
```

The source pipeline tests `jw >= 0.92` against that distance directly, which
asks for strings that are maximally *unlike* each other. So its Jaro-Winkler
and metaphone signals never fired on the pairs they were written to catch:
`BRATTON`/`BRATTEN` scores 0.057, `SHIELDS`/`SHEILDS` 0.038, identical
metaphone codes 0.000 — all rejected by a 0.92 floor.

This is a large part of why so many duplicates survived two resolution passes,
and it is a genuinely good five seconds of stage time: the bug is invisible,
the function name is the trap, and the fix is `1 - x`. Corrected in
`graphrank/resolution.py`; the string signal went from 10 Person pairs to 895.

*(The corps repo still has the inverted version. Worth a PR, separately.)*

#### 2. Co-occurrence earns its place — but only behind adjudication

*(This finding was reported, retracted, and then re-established on a clean
graph. The retraction was right to make and the history is kept below, because
"my first measurement was rigged" is a better story than the result alone.)*

**The false start.** The first measurement ran against the release dump, which
is the *post*-pipeline graph — `build_graph.py` runs `disambiguate.py` twice
before cutting it. Worse, the two signals had not competed on equal terms during
that build: because of finding #1, the Jaro-Winkler and metaphone branches were
inverted and never fired, while co-occurrence (cosine, correctly thresholded)
worked and swept the corpus. What survives into the dump is close to *the
complement of what co-occurrence can find*, handed to a string ladder that never
got to run. Measuring there made co-occurrence look worthless by construction.

**The clean test.** Rebuilt the corpus from Project Gutenberg into a separate
`rawgraph` database — 2,913 chunks, identical count to the dump — ran
`extract.py`, then only the label-cleanup steps, skipping every step that is
itself entity resolution. Details in the box below.

Result on `rawluna`, the canonical pre-disambiguation baseline, scored against
the hand-built identity gold set:

| signals | pairs | TP | FP | precision | recall | largest WCC |
|---|---|---|---|---|---|---|
| string + alias | 802 | 29 | 8 | **0.78** | 0.16 | 37 |
| co-occurrence only | 1,028 | 7 | 446 | 0.02 | 0.04 | 96 |
| all three | 1,814 | 32 | 450 | 0.07 | **0.18** | 265 |

⚠️ These are the **final** numbers, after the metric and threshold corrections
in 2c below. The first pass used COSINE at 0.5 and `topK=10`, which gave
co-occurrence 1 true positive instead of 7 — read 2c before quoting anything
from this table.

**The conclusion held.** Co-occurrence is hopeless on its own: 7 true positives
against 446 false ones.

**And then adjudication changes the verdict completely.** Running the LLM over
the 453 scoreable co-occurrence pairs:

| | pairs kept | TP | FP | precision |
|---|---|---|---|---|
| co-occurrence, raw | 453 | 7 | 446 | **0.015** |
| after adjudication | 8 | 7 | 1 | **0.875** |

**Adjudication rejected 445 of 453, keeping every true positive.** And the pairs
only co-occurrence can find are the ones that matter:

> `INDIAN WOMAN  ~  SACAGAWEA`

No string signal reaches that, ever. Jaro-Winkler, token containment and
metaphone are all hopeless on it. It is the exact case the section's intuition
was about, and it is real.

**So the original framing was right, and the section survives — with a sharper
point than it started with.** Co-occurrence is not a *decision* procedure and it
is terrible when used as one. It is a **recall instrument**, and its output is
only usable behind a precision stage. That is precisely the architecture
`disambiguate.py` already has, and it is why the honest note in the section
below is the load-bearing sentence, not a caveat:

> The algorithm's job isn't to decide — it's to shrink the candidate set from
> O(n²) to something adjudication can afford.

Now with numbers behind it:

| | |
|---|---|
| Person nodes | 811 |
| All possible pairs | **328,455** |
| Proposed by all three signals | **1,814** — 0.55% |
| Reduction | **181×** |
| Adjudicated at gpt-4o-mini | fractions of a cent |

That is the section. Not "graph structure beats string matching" — it doesn't,
on its own, on this corpus — but **"the algorithm makes an unaffordable problem
affordable, and buys you the cases nothing else can reach."**

> ##### How `rawgraph` was built, and why it is the right baseline
>
> ```
> CREATE DATABASE rawgraph                     -- nothing deleted; neo4j untouched
> ALTER USER neo4j SET HOME DATABASE rawgraph  -- corps scripts call session()
>                                              -- with no database. Restored after.
> python ingest.py                             -- Gutenberg -> 2,913 chunks
> EXTRACTION_CONCURRENCY=10 python extract.py   -- ~45 min, a few dollars
> python fix_waterbody_labels.py
> python flag_generic_locations.py
> python cleanup_relationships.py
> ```
>
> **Skipped deliberately, because each is itself entity resolution:**
>
> | skipped | why |
> |---|---|
> | `resolve_mentions.py` | LLM re-routes single-word Person mentions onto full-name nodes and deletes the emptied ones — it absorbs exactly the `SHIELDS`/`JOHN SHIELDS` pairs under test |
> | `enrich_sacagawea.py` | hand-written alias linking; writes `aliases` directly, pre-solving the hardest semantic case |
> | `disambiguate.py` | the thing being measured |
> | `add_taxonomy.py` | time only — Taxon nodes have no `MENTIONED_IN` edges, so they cannot enter the co-occurrence projection |
>
> **One caveat that matters, and is worth a sentence on stage.** There is no
> such thing as a fully unresolved graph from this pipeline. `extract.py`
> resolves *as it extracts*: the LLM assigns a canonical name to each mention
> and files the raw surface form as an alias, so a freshly extracted node
> already carries `Capt. Lewis`, `Chabonah`, `Sergt. Pryor`. 217 Person nodes in
> `rawgraph` have populated alias arrays before any resolution step runs.
>
> So `rawgraph` is *post-extraction, pre-disambiguation* — which is exactly the
> state `disambiguate.py` is designed to operate on, and therefore the correct
> place to evaluate its signals. It is not "raw entities" in an absolute sense,
> and the slide should not claim it is.
>
> Both databases are kept, so before/after resolution can be shown side by side
> without a reload: `NEO4J_DATABASE=rawgraph python scripts/demo_resolution.py`.

#### 2b. Replicated on a better extraction — and the model default was wrong

`extract.py` defaulted to `gpt-4o-mini`, and finding #4 below shows that is now
the *worst* of six current models on this pipeline's adjudication task. So the
whole corpus was re-extracted with `gpt-5.6-luna` into a third database,
`rawluna`, and everything above was re-run against it.

**What better extraction fixed, and what it did not:**

| | `rawgraph` (gpt-4o-mini) | `rawluna` (gpt-5.6-luna) |
|---|---|---|
| entity nodes | 4,460 | 5,264 |
| Person nodes | 795 | 811 |
| `MENTIONED_IN` edges | 16,355 | **22,754** (+39%) |
| **malformed nodes present** | **22 of 29** | **5 of 29** (−77%) |
| identities still split | 24 | 22 |
| duplicate pairs to find | 221 | 180 |

The split is exactly the one to put on a slide, because the two halves behave
completely differently:

- **Extraction artifacts collapse.** The concatenated-name junk — `SHANNON
  HOWARD`, `LABEECH SHANNON`, `SHANNON COLLINS SHIELDS`, two names from a party
  list fused into one entity — drops by 77%. Those were never a resolution
  problem; they were an extraction problem wearing a resolution problem's
  clothes.
- **Real duplicates do not.** 22 corps members are still split across 180
  pairs. `DREWYER` (329 mentions) and `GEORGE DROUILLARD` (51) are still two
  nodes, and the split is *starker* than before. No extractor fixes this,
  because the variation is in the journals: Clark spelled it differently on
  different days.

*(Not a pure win: luna also invents `JOHN BRATTON` (7 mentions) alongside
William Bratton, and prefers modern forms like `PIERRE CRUZATTE` that the
journals never use. Better, not perfect.)*

**And the co-occurrence result replicates.** On `rawluna` — with a
co-occurrence graph 39% denser in mention edges, which is the best case the
signal could ask for:

| signals | pairs | TP | FP | precision | recall |
|---|---|---|---|---|---|
| string + alias | 802 | 29 | 8 | 0.78 | 0.16 |
| co-occurrence only | 323 | 1 | 175 | 0.01 | 0.01 |
| all three | 1,116 | 30 | 180 | 0.14 | 0.17 |

Co-occurrence proposed 314 pairs the string ladder did not. Exactly **one** was
real, and it is the same one as before:

> `SACAGAWEA ~ INDIAN WOMAN`

Adjudication then rejected 175 of 176 and kept precisely that pair —
precision 0.006 → 1.000.

**So the finding is robust across three independently built graphs:** the
post-disambiguation dump, a gpt-4o-mini extraction, and a gpt-5.6-luna
extraction with 39% more mention edges. Co-occurrence contributes one semantic
match nothing else can reach, buried in 175 false positives, and adjudication
recovers it cleanly every time. That is a replication, not an anecdote, and it
is worth saying so from the stage.

⚠️ **Caveat on the recall column.** The gold set's surface forms were harvested
from the `neo4j` graph, which descends from a gpt-4o-mini extraction. `rawluna`
names entities differently (99 of the gold forms present, versus 110 in
`rawgraph`), so absolute recall is not comparable across the two databases. The
*unique contribution* comparison is unaffected, because both signals are scored
on the same forms within each graph.

#### 2c. Metric and threshold matter more than weighting — OVERLAP wins

Three corrections came out of reviewing the IDF experiment, and together they
roughly **sevenfold** the co-occurrence signal's true positives.

**Correction 1 — the IDF test was confounded.** It changed the weighting while
holding the cutoff at 0.5, so it measured weighting *and* threshold jointly and
blamed the weighting. Re-swept, COSINE's best operating point is 0.35 raw /
0.30 IDF, not 0.5 — and at their own optima the two weightings are identical
(precision 0.011 both). The original conclusion survived, but for the wrong
reason.

**Correction 2 — COSINE was the wrong metric.** Duplicate surface forms are
*asymmetric*: `SACAGAWEA` has 5 co-occurrence neighbours, `INDIAN WOMAN` has 38.
Swept against the gold set on `rawluna`:

| metric | weight | thr | pairs | TP | FP | precision | recall |
|---|---|---|---|---|---|---|---|
| COSINE | chunkCount | 0.35 | 363 | 4 | 359 | 0.011 | 0.022 |
| COSINE | idfWeighted | 0.30 | 371 | 4 | 367 | 0.011 | 0.022 |
| JACCARD | chunkCount | 0.10 | 253 | 1 | 252 | 0.004 | 0.006 |
| JACCARD | idfWeighted | 0.05 | 313 | 2 | 311 | 0.006 | 0.011 |
| OVERLAP | chunkCount | 0.95 | 202 | 6 | 196 | 0.030 | 0.033 |
| **OVERLAP** | **idfWeighted** | 0.95 | 148 | 6 | 142 | **0.041** | 0.033 |

The ordering is not luck, it is the metric definitions:

> **JACCARD** divides by the union, so it *punishes* the size mismatch that is
> the signature of a duplicate. Worst metric here; loses the pair outright.
> **COSINE** tolerates it. **OVERLAP** divides by `min(|A|,|B|)` and therefore
> asks the question duplicate detection actually wants: *is the rare name's
> context contained in the common name's?*

**Correction 3 — `topK` was silently truncating.** At the pipeline's `topK=10`,
and at 25, `SACAGAWEA ~ INDIAN WOMAN` does not appear in OVERLAP output **at
all** — because 138 other labelled pairs score a perfect 1.0 and saturate the
list. Those perfect scores are trivial containment: any 2-neighbour node sits
entirely inside a 38-neighbour node. At `topK=100` the pair returns at 0.725.

**Result of all three, on `rawluna`:**

| signals | pairs | TP | FP | precision | recall |
|---|---|---|---|---|---|
| string + alias | 802 | 29 | 8 | 0.78 | 0.16 |
| co-occurrence only | 1,028 | **7** | 446 | 0.02 | 0.04 |
| all three | 1,814 | 32 | 450 | 0.07 | 0.18 |

Co-occurrence goes from 1 unique true positive to **3** — and the three are the
whole Sacagawea identity:

```
INDIAN WOMAN  ~  THE SQUAR    1.000
SACAGAWEA     ~  THE SQUAR    1.000
INDIAN WOMAN  ~  SACAGAWEA    0.725
```

Three surface forms with nothing in common as strings, handed to WCC, which
closes them into one entity. **That is the demo.** Adjudication over the 453
scoreable pairs rejects 445 and keeps 7 of 7 true positives plus one false one —
precision 0.015 → 0.875.

#### 2d. Why the signal is weak — stated correctly this time

An earlier draft claimed the problem was that two spellings of one person rarely
share a chunk. That is true and **irrelevant** — node similarity compares
neighbourhoods, not chunks, so a direct edge was never needed. Duplicates coming
from different authors and different entries is the normal case, and
second-order similarity is precisely the right instrument for it.

The real limitation is **sparsity, and it is self-inflicted by the problem
shape.** A rare spelling variant appears in few chunks, so it has few
neighbours — `SACAGAWEA` has five. Similarity over five elements is unstable
whichever metric computes it.

And the obvious remedy makes things worse, which is the finding worth showing:

| min neighbours | 0 | 3 | 4 | 5 | 8 |
|---|---|---|---|---|---|
| true positives | **7** | 3 | 2 | 1 | **0** |
| false positives | 446 | 338 | 316 | 294 | 228 |

Requiring a minimum neighbourhood size strips true positives faster than false
ones, **because the duplicates are themselves the sparse nodes**. The signal is
structurally weakest exactly where it is needed.

That is the honest case for an adjudicator, and a far better line than the hub
story it replaces. It also draws the distinction the audience needs:

> PageRank's failure mode is **hubs** — down-weight the hub and it is fixed.
> Node similarity's failure mode here is **sparsity** — reweighting
> redistributes evidence, it cannot create any. Same-looking problem, same-
> looking fix, different disease.

*(The IDF weighting is kept as the default anyway: at OVERLAP's operating point
it gives the best precision in the sweep, and it makes the Sacagawea match rest
on Charbonneau at 48% rather than on the two captains at 79%. Right answer for
the right reason.)*

#### 3. The headline result: replacing an external data source with corpus evidence

The corps pipeline resolves Sacagawea with `enrich_sacagawea.py` — a script that
**scrapes a curated list of 13 surface forms from lewis-clark.org**. A
third-party website someone had to find, trust, and maintain, hard-coded into
the build. It is the least reproducible thing in the pipeline.

`rawluna` was built *without* that script. And node similarity plus WCC recover
the identity from evidence inside the corpus alone.

**What the extractor leaves behind.** Sacagawea is named directly in 8 chunks
and referred to indirectly far more often, across **19 separate nodes** — almost
none sharing a token with "SACAGAWEA":

```
SACAGAWEA · INDIAN WOMAN · THE INDIAN WOMAN · OUR INDIAN WOMAN
THE INDIAN WOMAN WITH US · SQUAR · THE SQUAR · THE SQUAW · HIS SQUAR
SQUARWIFE · SQUAR INTERPRETRESS · SQUAR WIFE TO SHABONO · JANEY
THE WIFE OF SHABONO · WIFE OF SHABONO · SHABONOS WIFE · SNAKE INDIAN WIFE
INTERPRETERS WIFE · OUR INTERPRETER THE SNAKE WOMAN
```

**What co-occurrence + adjudication + WCC recover, unaided:**

| stage | result |
|---|---|
| co-occurrence candidates | 252 scoreable pairs, 10 true, 242 false — precision **0.040** |
| after adjudication | 10 kept, **10 true, 0 false** — precision **1.000** |
| after WCC | **one 10-node component** |

```
INDIAN WOMAN + INTERPRETERS WIFE + SACAGAWEA + SQUAR INTERPRETRESS
+ SQUAR WIFE TO SHABONO + THE INDIAN WOMAN + THE INDIAN WOMAN WITH US
+ THE SQUAR + THE SQUAW + THE WIFE OF SHABONO
```

Ten surface forms, one entity, **zero false positives**, no external list. The
hub of the cluster is `SQUAR INTERPRETRESS` — a one-chunk node that links to
eight of the others at similarity 1.000, because a single passage puts it in
company nothing else shares.

**This is the section's strongest claim, and it is a different claim than the
one the outline started with.** Not "graph structure beats string matching" — it
loses that contest badly. It is:

> Graph structure reaches identities that **no string method and no amount of
> hand-curation from the open web** will give you, because the evidence is in
> how the corpus uses the names, not in the names themselves.

**Say the caveat too.** Nine of the nineteen forms are still missed — `JANEY`,
`SNAKE INDIAN WIFE`, `OUR INDIAN WOMAN`, `HIS SQUAR` among them — mostly
one-chunk nodes whose single passage shares too little with the rest. The
external list still beats the algorithm on raw coverage. What the algorithm
gives you is coverage that is *derived*, reproducible, and works on a corpus
nobody has written a website about.

**Measured at last (2026-09-07, on the disambiguated `lewisclark` — see 3g).**
The provenance-tagged `enrich_sacagawea.py` ran *after* the consistency-gated
merge, so every link it creates says whether the graph already had it
(`alsoExternal`) or not (`externalOnly`). The chunk-level split:

| source | chunks | of the 85 total |
|---|---|---|
| graph only — the curated site never lists them | **25** | 29% |
| both — graph found it, the site agrees | 22 | 26% |
| scraper only — beyond what the graph found | **38** | 45% |

Neither source contains the other, and that is the finding. The graph derived
47 of her 85 known passages (55%) from corpus evidence alone — including **25
the hand-curated site does not list**, so "the website is the superset" is
false. The scraper's 38 unique chunks are concentrated exactly where alias
matching is structurally blind: passages that reference her only by pronoun and
context. Her near-death at the Marias — *"I found that her pulse were scarcely
perceptible"* — contains no surface form of any name; the curated list reaches
it because a historian read the journals and wrote the date down. No extraction
pipeline hits that from text.

On the aliases the same shape: of the site's 13 curated forms, the graph had
independently recovered 5–6 (strict string match 3; ignoring leading articles,
`Squar Interpretress`, `Interpreters Wife`, `The Squaw`, `The Squar`, `Indian
Woman`). What only the site knows: `Janey` (Clark's private nickname), the
Snake-woman family, `our interpretress` — names whose evidence lives outside
the corpus.

So the section's claim gets its final, honest form: **the graph does not
replace the external source; it demotes it.** The identity no longer *depends*
on lewis-clark.org — 55% of her mention coverage, and the identity itself, are
derived and reproducible — and what the site adds is now tagged provenance
(`r.source`, `r.externalOnly`), auditable and removable in one query, instead
of scraper output fused invisibly into the graph. External data as enrichment
you can point to, not a dependency you have to trust.

Post-enrichment state: 85 chunks, 32 aliases (the corps script's case-sensitive
dedup keeps `the squaw` alongside `The Squaw` — cosmetic, noted). The 13 forms
also remain stored on `p.externalAliases`.

#### 3b. What the gold set is, and what it is not

**It is not ground truth, and no slide should treat it as one.** Nathan's call,
and it is the right one. The limits are worth writing down so nobody — us
included — quotes these numbers later without them.

**Where the labels come from.** `questions/corps_members.yaml` was assembled by
reading surface forms off the live graph and grouping them using the historical
roster. That is deliberately *independent of the pipeline* — it is not derived
from what `disambiguate.py` chose to merge, which is what makes it usable for
judging the pipeline at all. But independent is not the same as correct. That
`SQUAR WIFE TO SHABONO` denotes Sacagawea is a judgement, a good one, not a fact
established by anything.

**And the pipeline's own history is shakier still.** The merges recorded in the
shipped graph's `aliases` arrays were confirmed by an LLM judge running on
`gpt-4o-mini`, which finding #4 below shows misses a third of real duplicates.
Its false *negatives* are documented; its false *positives* are not, and at
least one is visible — `GEORGE SHANNON` sits in `GEORGE DROUILLARD`'s alias
array in the shipped dump. So the corpus's own resolution history contains
mistakes, which is precisely why the gold set was not built from it.

**Coverage is thin and lopsided.** On `rawluna`:

| | |
|---|---|
| Person nodes | 811 |
| labelled by the gold set | **114 (14%)** |
| string+alias pairs that are scoreable | **56 of 802 (7%)** |
| co-occurrence pairs that are scoreable | 252 of 1,359 (19%) |

A precision figure computed on 7% of a signal's output is not a precision
figure, and the 7% is biased: labelled forms are the ones recognisable as corps
members, so the unscored remainder is disproportionately junk-vs-junk. True
precision across the whole output is likely *worse* than what the tables say.

Recall is lopsided in the other direction — Sacagawea is now **46%** of the
recall denominator (153 of 330 pairs), because she is the only identity
enumerated exhaustively. Any aggregate recall number is mostly hers.

**So what survives, and can go on a slide:**

- ✅ The Sacagawea cluster — ten named nodes, shown on screen, checkable by eye
- ✅ *How* OVERLAP works — one diagram of the two neighbourhoods, plus a
  throwaway line that other metrics may suit other corpora. **Not** the
  comparison table; there is no stage time for it and it is not the point
- ✅ Counts of what a given run proposed, kept and closed — those are exact
- ❌ Any precision or recall percentage
- ❌ "co-occurrence finds N% of duplicates"

**If we ever do want a defensible precision number**, the cheap route is a
random sample: take ~100 proposed pairs regardless of labelling, judge them, and
estimate from that. It is unbiased and far cheaper than labelling 811 nodes.
Not needed for the talk as scoped.

#### 3c. Tuning for recall is unsafe once WCC merges the result — learned the hard way

Worth a slide, because it was an actual failure on this project rather than a
hypothetical, and it sharpens the WCC danger point from an anecdote into a rule.

**What happened.** The OVERLAP/`idfWeighted`/`topK=100`/`MIN_CHUNK_COUNT=1`
settings from finding 2c were measured on **Person**, against a Person gold set,
in a **read-only** setting where every candidate pair was adjudicated
independently and nothing was merged. On that basis they were a clear
improvement — 1 unique true positive became 10.

Those settings were then ported into `disambiguate.py`, which is a very
different machine: it runs over **all eight labels** and it **merges** using
**WCC transitive closure**. The result on a full pipeline run:

| | |
|---|---|
| `SACAGAWEA` | 168 aliases, 417 chunks — absorbed `George Drouillard`, `George Drewyer`, `Windsor` |
| one `NativeNation` node | **498 aliases** — Kickapoo, Sioux and most other nations welded together |
| clusters over 20 aliases | 15 |

**Why.** `MIN_CHUNK_COUNT=1` admits every one-chunk node. OVERLAP divides by
`min(|A|,|B|)`, so two one-chunk nodes that share a couple of incidental
neighbours score near 1.0. `Place` is full of one-off island names, so it
produced pairs like `GOOD HOPE ISLAND ~ ROCK ISLAND` — **zero shared chunks**.
The judge confirmed some of them (an 1804 island name is genuinely ambiguous
without a map), and then WCC chained every confirmed false positive into a
mega-cluster.

**The rule, and it is the slide:**

> A precision error costs you **one bad pair** if a human or an LLM reviews each
> pair independently. Under transitive closure it costs you **an entire merged
> identity, permanently** — and one bad edge is enough. So the operating point
> that is right for generating candidates is not automatically right for
> generating *merges*. Tune recall where a judge sees each pair alone; tune
> precision where a closure algorithm will chain them.

This is also the concrete answer to "why does adjudication run *before* WCC and
not after". It is not an implementation detail. Closure amplifies whatever
precision you hand it.

**What the pipeline runs now:** the original conservative candidate generation
(COSINE, cutoff 0.5, `minCount` 2, `topK` 10), keeping only the two changes that
are correct regardless of context — the Jaro-Winkler inversion fix and the
`gpt-5.6-luna` judge. The aggressive settings stay in `graphrank/resolution.py`,
which is read-only and never merges, where they are safe and measurably better.

**And a process lesson worth one line:** the run now has an automated gate after
each pass that aborts if any cluster exceeds 120 aliases, if the Person count
collapses, or if Drouillard turns up in Sacagawea's aliases. A pipeline that can
silently weld two identities together should refuse to continue when it starts
doing so.

#### 3d. Bridge nodes — and a correction to what this section first claimed

⚠️ **This finding was reported once in a form that flattered the model, and is
corrected here.** The first version said "the judge was never wrong — WCC
manufactured the error from clean inputs." That is true of the pairs originally
tested and false in general. Keeping the correction visible, because the
corrected version is the more useful one.

**What is still true.** Asked about *well-known, named individuals*, the judge
is reliable. With `disambiguate.py`'s own prompt, `gpt-5.6-luna` answers:

```
SACAGAWEA    ~ GEORGE DROUILLARD    different   ✓
SACAGAWEA    ~ WINDSOR              different   ✓
INDIAN WOMAN ~ GEORGE DROUILLARD    different   ✓
SACAGAWEA    ~ INDIAN WOMAN         SAME        ✓
DREWYER      ~ GEORGE DROUILLARD    SAME        ✓
```

It never said Sacagawea was Drouillard. And bridge nodes are real: vague
references get confirmed against two different people —

```
THE INTERPRETER  →  confirmed same as GEORGE DROUILLARD *and* TOUSSAINT CHARBONNEAU
HIS WIFE         →  confirmed same as SACAGAWEA         *and* TOUSSAINT CHARBONNEAU
```

giving the chain that actually fired:

```
SACAGAWEA ──[HIS WIFE]── TOUSSAINT CHARBONNEAU ──[THE INTERPRETER]── GEORGE DROUILLARD
```

**What was wrong.** The claim that the *inputs* to closure were sound. Reading
the adjudication cache for one hub node, `SQUAR INTERPRETRESS`, shows 35
confirmed edges — 33 of them resolving to "Sacagawea", including:

| confirmed same as | chunks | what the graph says it is |
|---|---|---|
| TIN NACH-E-MOO-TOOLT | 1 | `MEMBER_OF → NEZ PERCE` |
| MAN-NES-SUR REE | 1 | `MEMBER_OF → HIDATSA` |
| CONIA COMAWOOL | 1 | `MEMBER_OF → CLATSOP` |
| WE ARK KOOMT | 1 | `TRADED_WITH → MERIWETHER LEWIS` |

Those are distinct Native leaders from three different nations. **The judge
confirmed all of them as Sacagawea.** So the 33:1 "consensus" is not evidence of
anything — it is thirty-three errors in a row.

**The pattern is specific and predictable:** a one-chunk vague descriptor paired
with a one-chunk unfamiliar name. Both sides are sparse, the judge has nothing
to discriminate with, and it reaches for the identity it recognises.

> **Corrected claim:** closure did not invent the error, and neither did the
> model alone. **Sparse ambiguous nodes produce bad pairwise judgements, and
> closure then compounds them into merged identities.** Two failures, and the
> second is only dangerous because of the first.

**Why this kills the obvious repairs.** Majority-voting a node's canonical names
sounds principled and is not:

| node | tally | order-dependent? |
|---|---|---|
| `SQUAR INTERPRETRESS` (hub) | 33 : 1 : 1 | no — but the 33 are wrong |
| `THE INTERPRETER` (bridge) | **1 : 1** | **yes — an exact tie** |
| `HIS WIFE` (bridge) | single edge | no majority exists |

Majority is robust exactly where it does not matter and undefined or tied
exactly where it does. Removing the *node* instead is no better — it was tried,
and dropping `SQUAR INTERPRETRESS` fragmented Sacagawea's cluster and lost her
node entirely, because the same node is both a genuine member and a bridge.

**So the fix belongs upstream, at candidate generation.** These nodes are toxic
twice: they attract false confirmations *and* they bridge. `flag_generic_locations.py`
already exists because "the river" is useless as a place; there is no equivalent
for people, so `THE INTERPRETER`, `HIS WIFE`, `SQUAR INTERPRETRESS` and `OUR
GUIDE` all sit in the graph as first-class Person nodes.

It also explains cleanly why `MIN_CHUNK_COUNT=1` was catastrophic in 3c: it
admits precisely this population.

**For the stage.** The corrected story is better than the original, because "the
model was perfect and the algorithm ruined it" is a comfortable story and this
one is not:

> Sparse entities get bad answers from *both* halves. The model cannot
> distinguish two people it has never heard of who appear once each. Closure
> then turns those individual mistakes into a single wrong identity that no
> amount of per-pair accuracy would have prevented. Fix what enters the
> candidate set, not what comes out of it.

#### 3e. The disambiguation design — two layers, measured

Settled after 3c and 3d. Neither layer reads the words in a name; both are
structural, deterministic and order-independent. Measured on `lewisclark`
against Sacagawea's cluster:

| stage | her forms kept | contaminants |
|---|---|---|
| confirmed pairs, no rules | 14 | **25** |
| + layer 1 (evidence) | 14 | 4 |
| + layer 2 (transitivity) | **11** | **0** |

**Layer 1 — evidence sufficiency.** A confirmed pair needs at least one
endpoint with ≥2 chunks. Two one-chunk nodes confirming each other is not
evidence: neither side has anything to discriminate with, so the judge reaches
for the identity it recognises. This alone removed 21 of 25 contaminants and
cost nothing — the sparse forms still reach the cluster through `INDIAN WOMAN`
(24 chunks) and `SACAGAWEA` (8), so the 18 dropped edges were redundant.

**Layer 2 — transitivity verification.** WCC closure *is* the claim that "same
entity" is transitive, and nothing ever tests it. For each node with two or more
confirmed neighbours, ask whether those neighbours are the same as each other; a
"no" means the node is a bridge and is dropped from the merge graph. It caught
the interpreter family and two more cross-identity welds worth naming on a
slide:

```
P. CRUSAT     bridges  GEORGE DROUILLARD ~/~ PIERRE CRUZATTE
JOHN BRATTEN  bridges  JOHN ORDWAY       ~/~ WILLIAM BRATTON
```

**It is cheaper than it sounds: 33 of 81 checks (41%) were answered free** from
verdicts already in the cache. Candidate adjudication rejects far more than it
confirms and the pipeline throws those rejections away — but a rejection is
exactly the evidence transitivity needs. Two people who co-occur constantly are
almost certainly proposed and rejected long before anything asks whether a vague
node bridges them. *(Nathan's suggestion; the pipeline could persist these as an
`IS_NOT_SAME_ENTITY_AS` relationship, since it has no cache of its own.)*

**Layer 3 — component size cap**, as a backstop for whatever the first two miss.
Not needed on this data (0 components refused), but cheap insurance: refusing to
merge is recoverable, merging is not.

**Why not a `flag_generic_persons` step.** It was the obvious idea and it is
wrong for this corpus. "The Indian woman" is culturally generic and
referentially unique — there was one. "The interpreter" is equally generic and
genuinely ambiguous — there were four. No string rule separates them, and an
LLM asked "is this a generic reference?" says yes to both, which deletes
Sacagawea's references. Her forms are phrased the way women were referred to in
1804; a filter that penalises that phrasing erases her from the graph while
leaving the actually-ambiguous nodes untouched.

> **The slide, if it earns a place:** the fix was not to teach the system what a
> vague name looks like. It was to stop treating a single passage as evidence.

**The cost, stated plainly.** Layer 2 drops 3 of her 14 forms —
`SQUAR INTERPRETRESS` and the two interpreter-worded ones — because they are
genuinely ambiguous, not because they are sparse. An 11-node cluster with zero
contaminants is a stronger claim on stage than a 14-node one with
`THE INTERPRETER` in it.

**Status: implemented read-only in `graphrank/resolution.py`, not wired into
`disambiguate.py`.** Running it on `lewisclark` is a separate decision.

#### 3f. Applying the design failed — and the root cause was reusing read-only defaults

The two-layer design in 3e verifies cleanly on a scoped test and **does not hold
at full scale**. Two dry runs on `lewisclark` (Person, 2,144 candidates,
nothing written), differing only in how a bridge is removed:

| | node removal | edge removal |
|---|---|---|
| components accepted | 31 | 42 |
| Sacagawea | **fragmented into 2, her own node in neither** | whole again, but **contaminated** |
| obvious bad merges | some | more |

**Node removal** deleted 48 nodes including `MERIWETHER LEWIS`, tearing apart
the clusters the exercise exists to build. **Edge removal** kept them together
but left paths open, producing merges that are plainly wrong:

```
[9]  HUGH BRATTON + ISAAC BRATTON + JOHN BRATTON + RICHARD BRATTON + W BRATTEN…
[8]  BLACK CAT + CHIEF OF THE MAH HAR + GEORGE DROUILLARD + KA KAW ISSASSA…
[11] AD HAKO HO PIN NEE + AR-RAT-TA NA-MOCK-SHE + BEL-LAR SA RA + …
```

Five Brattons as one man. Drouillard merged with Mandan chiefs. Eleven
unrelated Native names in one blob.

**The root cause was not the layers.** The script drove candidate generation
from `graphrank/resolution.py`'s defaults — OVERLAP, `minCount=1`, `topK=100` —
which exist for **read-only analysis where nothing merges**. That is exactly the
configuration finding 3c identifies as unsafe under WCC closure, and it was
reused anyway. `disambiguate_fixed.py` already carries the conservative
settings; the layered script bypassed them.

So 3c's lesson has now been learned twice, the second time by ignoring it:

> The operating point that is right for **generating candidates** is not
> automatically right for **generating merges**.

**What did work, and is worth keeping:**

- adjudication rejected **1,638 of 2,144** candidates — the recall/precision
  division of labour behaving exactly as section 4 claims
- the evidence filter cut the survivors **506 → 297**, removing the
  one-chunk-to-one-chunk confirmations
- transitivity found **48 bridges**, and **444 of 444 checks came free from
  cache** on the second run — the negative-cache idea fully vindicated
- several components are unambiguously correct and would be real wins:
  `P CRUSAT + PETER CROUSAT + PETER CROUZATT + …` (16 spellings of Cruzatte),
  Frazer (7), Weiser (5), Goodrich (4), Howard (3)

**Status: resolved — see 3g (2026-09-07).** Kept as written at the time:
handoff in [`picking-up-entity-resolution.md`](picking-up-entity-resolution.md)
— restore points, the patched scripts, the operational traps, and the first
thing to try on resuming. `lewisclark` remained pre-disambiguation at 794
Person nodes, checkpointed at
`data/checkpoints/lewisclark-pre-disambiguation/`. `neo4j` and `rawluna` were
never touched, and section 4 demos against them.

**What finishing this actually needs** — a future session, not a pre-deadline
patch. The real problem is correlation clustering with must-not-link
constraints: closure has to respect the negative verdicts, not just the positive
ones. Greedy approximations are order-dependent, which is the question Nathan
raised about majority voting and which applies here too. Doing it properly means
choosing a deterministic edge order (descending evidence, say) and accepting
that the result is an approximation — or refusing to merge wherever constraints
conflict, which is recoverable and probably right for a demo corpus.

#### 3g. Finished: consistency-gated merging — closure made to prove its claim (2026-09-07)

3f's diagnosis said the fix was correlation clustering with must-not-link
constraints. That is what got built, applied to `lewisclark`, and verified.
**794 → 675 Person nodes, 40 clusters merged, and the headline number: Sacagawea
went from 8 chunks / 8 aliases to 47 chunks / 19 aliases — 12 surface forms,
zero contaminants — with candidate generation still at the recall settings.**
The answer to 3c/3f turned out not to be tuning candidates down; it was gating
merges on verdict consistency. Recall stays where a judge reviews pairs;
precision now lives where closure merges them.

**Layer 3, component consistency** (`resolution.verify_components`, wired into
`tools/disambiguate_layered.py`). A component is the claim that every member
pair is the same entity, but adjudication only ever saw the edges that built
it — the far pairs of a chain are asserted by closure and asked of nobody, which
is how five Brattons became one man. So before anything merges:

1. **Every closure-asserted member pair gets a verdict** — the confirmed edges
   by construction, the rest from the adjudication cache or fresh calls (442
   pairs on this corpus; the final run answered 442/442 from cache, zero API
   calls, byte-identical output).
2. **A rejection is a cannot-link constraint, enforced absolutely.** Layer 2
   verified transitivity locally (two hops) and enforced it weakly (cut one
   edge, which alternate paths route around — 3f's "whole but contaminated").
   Layer 3 re-clusters each component greedily under its constraints: edges
   union strongest-first, any union that would co-cluster a rejected pair is
   skipped, and the constraint propagates to the merged set. Kruskal with a
   veto — greedy correlation clustering, made order-independent by a
   deterministic edge order.
3. **The edge order is (contradictions, signal agreement, min-mentions,
   similarity, names)** — contradictions first, because the failure it fixes
   was measured, not imagined: the judge confirmed `SACAGAWEA ~
   HOHAST-ILL-PILP` (a Nez Perce chief) while rejecting him against every
   woman-form. Both endpoints well-attested, so pure evidence ranking let the
   lie claim her node first and the vetoes dragged her out of her own cluster.
   Third-party verdicts dispute a wrong positive far more than a right one;
   counting them picks the honest edge. Evidence measures what the judge had to
   work with — the other verdicts measure whether it agreed with itself.
4. **An edge more disputed than corroborated cannot support a merge at all.**
   Found the hard way, live: the first `--apply` merged `JOHN BRATTEN` into
   **John Ordway** — a judge confirmation with no negative *between* the pair,
   sitting in a two-member component where no veto can fire. Post-merge
   verification caught it, the checkpoint restore cost the promised minute, and
   the fix generalises: for each edge, every third entity with decided verdicts
   against both endpoints is a witness — opposite verdicts dispute the edge
   (if A matches C and B does not, A and B are not the same person), matching
   confirmations corroborate it. `BRATTEN ~ ORDWAY` had one disputing witness
   (William Bratton) and zero corroborating ones. Merges now require the
   witnesses to net out in favour. A confirmed pair nobody corroborates is a
   verdict, not evidence.
5. **Merged nodes take the judge's canonical name**, by majority over the
   cluster's confirmed verdicts, not the longest surface form — the earlier
   rule named her merged node "Our Interpreter The Snake Woman" and Jefferson's
   "President Of The States Of America". One trap: the judge canonicalises the
   servant forms to `YORK`, which collides with the uniqueness constraint on
   the existing single-word `YORK` node the person gate had excluded; on
   collision the merge falls back to a member name rather than absorbing a node
   no layer verified.

**What it caught, end to end** (all from the dry-run reports, reproducible from
cache): the Bratton chain split with William's six spellings intact and Hugh,
Isaac, Richard, and John-the-other refused; Drouillard separated from the
Mandan and Hidatsa chiefs (`LE BORGNE` and `POCAPSAHE (BLACK CAT)` emerged as
their own correctly-named nodes); Dorion Sr. and Jr. kept apart; `MAN-NES-SUR
REE` expelled from the La Rocque cluster; `THOMAS JEFFERSON ~ MY OLD GUIDE`
refused; William Clark expelled from a chiefs' component; the 11-name Native
component refused entirely rather than blended.

**The costs, stated plainly, because refusing is the mechanism working:**
`WILLIAM WARNER ~ WILLIAM WERNER` is a real pair and was refused — Warner's own
false confirmations against Sacagawea's forms are disputing witnesses against
his one true edge. `SAR CAR GAH WE` (clearly her) stayed unmerged. The
plausible `AR-RAT-TA NA-MOCK-SHE` spelling pair went down with its disputed
component. All recoverable: nothing wrong was written, and an unmerged
duplicate is a recall miss, not a corrupted identity.

**Still judge's-word-only, disclosed for review:** `GEORGE DROUILLARD + MR.
DURIAUR` (accepted by Nathan; "Durion" usually means Dorion), `RICARRE CHIEF`
merged with the Black Cat forms, `PAR NAR NE AR PAR BE + WHITE CRAIN`. Each
survived because no witness disputes it — the rule's honest residual.

**For the stage.** The arc is now one sentence per act: nodeSimilarity at
recall settings finds candidates no string signal can (that is 2c); the judge
turns candidates into verdicts (3e); and closure is not allowed to assume
transitivity — it must prove every pair it asserts, against verdicts that are
free because rejections were cached (3g). WCC is still in the loop; it just
stopped being trusted on faith.

**Status: applied.** `lewisclark` is at 675 Person nodes, gate passed
(no mega-clusters, Sacagawea's cluster verified), and the merged state is
checkpointed at `data/checkpoints/lewisclark-post-disambiguation/`. `rawluna`
and `neo4j` untouched. Before `demo_paths.py` runs against it, `lewisclark`
still needs `tag_corps_members.py`, `setup_fulltext_indexes.py`, and
`embed_entities.py`. The Sacagawea re-enrichment measurement ran on top of the
merge — results in finding 3 ("Measured at last").

#### 3h. Demo validation — the section 4 demo path, run end to end (2026-09-07)

Conditions for every number below: local Desktop DBMS (heap still 1 GiB max),
wall-clock timings on this machine, no resident GDS projections at start,
`NEO4J_DATABASE=` passed explicitly, home database untouched on `neo4j`.

**The demo arc, decided and measured.** Three acts, two databases:

1. **Walkthrough on `rawluna`, read-only** — `demo_resolution.py`: **3.8 s**.
   2,135 candidates (co-occurrence 1,359 / string 798 / alias 66, multi-signal
   86) from a 5,123-entity / 156,062-edge projection; naive WCC largest
   component 399; write audit zero writes. With `--adjudicate --max-calls 0`:
   **2.6 s**, 2,063 of 2,135 verdicts from cache (499 confirmed / 1,564
   rejected / 72 undecided).
   **New measurement, and it is the beat that motivates 3g:** WCC over just
   the 499 *confirmed* pairs still welds Sacagawea into a **91-node
   mega-component** (her forms + the Labiche cluster + Windsor + Warner/Werner
   + a dozen chiefs, bridged by `HIS WIFE` / `THE INTERPRETER` / `OUR GUIDE`).
   Adjudication before closure is not enough — closure asserts pairs nobody
   judged. Display note: the components table caps at 12 rows regardless of
   `--limit`, so this weld is what the audience sees there; the clean
   Sacagawea cluster is act 2's job.
2. **Layered dry run on `rawluna`** — `tools/disambiguate_layered.py
   --database rawluna --max-calls 0 --consistency-max-calls 0`: **2.2 s, 151
   lines**. 2,135 candidates → 499 confirmed → 248 past the evidence filter →
   415 transitivity checks (all cached, 38 bridges) → 37 components →
   consistency layer checks 395 closure-asserted pairs → 13 split, 24 clean →
   **34 mergeable clusters**. The Sacagawea payoff prints as `SPLIT [17 → 12]`:
   her 12-form cluster emerges with `HIS WIFE`, `THE INTERPRETER`, `ONE OF HIS
   WIVES`, `SAR CAR GAH WE` excluded and the disputed edges named. Bratton vs
   Ordway, Jefferson vs `MY OLD GUIDE`, and Warner/Werner refusals all visible.
   **Demoable live as-is — no `--demo` trim mode needed.** Output volume is
   fine on a projector; the longest block (the 11-name Native component's
   rejection list) is ~20 lines.
   *One prerequisite:* 98 verdicts (72 candidate + 26 consistency) are not in
   cache, because `rawluna`'s candidate set differs slightly from the
   `lewisclark` pre-disambiguation state the cache was built on
   (`resolve_mentions` absorbed 17 nodes there). One run without the caps
   (~98 judge calls, pennies) fills them; this session's permission gate
   blocked paid API calls, so **run it once before rehearsal** — after that
   the demo is zero-API and deterministic.
3. **`lewisclark` as the "after" graph** — validated live: 675 Persons;
   SACAGAWEA 85 chunks / 32 aliases with provenance tags reconciling exactly
   (38 `externalOnly` + 22 `alsoExternal` + 25 untagged graph-only = the
   finding-3 split); 41 `corpsMember`; WILLIAM BRATTON intact (11 aliases, 40
   mentions) with Hugh/Isaac/Richard/John-the-other separate; JOHN ORDWAY (20
   aliases, 79 mentions) with no Bratten absorbed. `demo_resolution.py`
   pointed here opens with the receipts table — SACAGAWEA's 32 absorbed forms
   next to REUBIN FIELD's 38 — which *is* the after exhibit in one screen.
   The dry run re-pointed at post-merge `lewisclark` finds only 879 leftover
   candidates → 4 mergeable clusters (2.2 s): the walkthrough has no story
   here, which is why acts 1–2 stay on `rawluna`.

**`demo_paths.py` ran on `lewisclark` for the first time — two breaks, both
fixed in `graphrank/` (corps repo untouched):**

- `paths._hydrate` crashed on `toString(r.date)`: the 3g merge combined
  parallel relationships, leaving **403 relationships with list-valued
  `date`/`chunkId`** (364 with both as lists, 39 chunkId-only). Fix: normalise
  to the first element of each in the hop query.
- Yen's treats parallel relationships as distinct paths, so identical routes
  printed twice. Fix: dedupe by node sequence in `k_shortest_paths`.

After the fixes: `--from Sacagawea --to Shoshone` **0.7 s**, 4 distinct routes
with dated chunk citations; `--from Cameahwait --to Sacagawea` 0.7 s, 3
routes. Prerequisite: `NEO4J_DATABASE=lewisclark python scripts/project_graph.py`
first (~1 s, builds `lc-retrieval` + `lc-mentions`). Caveats: route 4 of the
Shoshone query walks through `DREWYER` — an unmerged Drouillard shard, visible
on stage (disclose it or use `-k 3`); and the docstring's `--from "Grizzly
Bear"` example never worked on *either* graph — fulltext beats the vector lane
whenever any name index returns a hit, so it resolves to `BEAR CREEK` here and
`WHITE BEAR ISLANDS` on `neo4j`. Use person/place/nation anchors. (`lewisclark`
actually resolves `Great Falls` correctly, 32 mentions, where `neo4j` picks a
junk one-mention `GREAT` Person node.)

**Retrieval spot checks on `lewisclark`** — the queries the demos will issue,
all rank 1:

| query | lane | result |
|---|---|---|
| `Crusatte~` | fulltext fuzzy | PETER CRUZATTE 10.67 (61 mentions); unmerged `CRUSATT`/`CRUZATTE`/`CRUSAT` shards trail at 4.7–6.0 — the recall-miss residue, visible |
| `Minnetarees` | fulltext alias | HIDATSA (147 mentions) |
| `elk` | vector, AnimalSpecies | CERVUS CANADENSIS 0.707 (587 mentions) |
| `salmon` | vector, Taxon | Salmonidae 0.801 |
| `birth of a child` | vector, Event | BIRTH OF NEWBORN BABE 0.806, then BIRTH OF JEAN BAPTISTE CHARBONNEAU 0.721 |

The birth ranking is **not** an error: the top hit is a different real birth
(chunk `4c77b279`, 1805-08-26); the Charbonneau birth is its own event/chunk
(`c4e6e907`, 1805-02-11). Both retrieve; say "the top two hits are the
expedition's two recorded births" and it becomes a feature.

The known `"interpreters wife"` failure reproduces: SACAGAWEA rank 6 at score
2.34 behind `HIS WIFE` 4.58 (2 mentions) and three one-mention shards, and
`resolve_entity`'s near-tie prominence rule cannot reach her (she is below
0.75 × best). **Decision: no mention-count boosting.** Either keep it as the
disclosed "unmerged shards outrank the merged identity" beat, or keep it off
stage — the spot-check table above is the safe query set.

**Answers to the open questions:**

- **`lewisclark` does not replace `rawluna`; it replaces `neo4j` — for section
  4 only.** Walkthrough (candidates, naive closure, layered dry run) runs
  read-only on `rawluna`; `lewisclark` is the applied after graph and hosts
  the retrieval + paths demos. `neo4j` stays the sections 5–8 graph.
- **The layered dry run is live-demoable**: 2.2 s, 151 lines, no trim mode
  needed — after the one cache-filling run above.
- **Person-embeddings fallback stays noted-for-later.** Every person/nation
  demo query resolves via fulltext; the one mis-resolution observed (`Grizzly
  Bear`) is a fulltext-vs-vector *lane-ordering* issue that person embeddings
  would not touch.

Heap note: the whole section-4 workload ran at the 1 GiB heap — co-occurrence
projection plus `lc-retrieval`/`lc-mentions` all built — but finished with
~135 MiB free and everything else idle. The pre-demo raise to 2 GiB (Desktop
Settings UI, not `neo4j.conf`) stands. Projections created today were dropped
afterwards; they rebuild in ~1 s.

#### 4. The default model is three generations stale

Benchmarked over 187 labelled Person pairs, `gpt-4o-mini` — the default in both
`extract.py` and `disambiguate.py` — is the worst of six current models:

| model | TP | FP | FN | precision | recall | F1 | wall |
|---|---|---|---|---|---|---|---|
| gpt-4o-mini | 31 | 0 | 17 | 1.000 | **0.646** | 0.785 | 16s |
| gpt-4.1-nano | 39 | 0 | 9 | 1.000 | 0.812 | 0.897 | 13s |
| gpt-5-nano | 39 | 0 | 9 | 1.000 | 0.812 | 0.897 | 105s |
| gpt-5-mini | 47 | 0 | 1 | 1.000 | 0.979 | 0.989 | 89s |
| gpt-5.4-nano | 47 | 0 | 1 | 1.000 | 0.979 | 0.989 | 18s |
| **gpt-5.6-luna** | 48 | 0 | 0 | 1.000 | **1.000** | **1.000** | 30s |

**Every model has perfect precision.** On a task this constrained none of them
invent a merge, so the entire spread is recall — how many real duplicates a
model is willing to recognise. `gpt-4o-mini` balks at `GEORGE DREWYER` /
`GEORGE DROUILLARD` and `SILAS GOODRICH` / `SILAS GUTRICH`.

Adjudicating every Person candidate pair costs ~9¢ on `gpt-4o-mini` and ~12¢ on
`gpt-5.6-luna`. **Three cents buys 35 points of recall.** At this corpus size
price is not a real axis; choose on quality.

Reproduce with `demo_resolution.py --compare-models`. The top three are within
one pair of each other on 187 samples and are statistically indistinguishable;
the gap down to `gpt-4o-mini` is not.

*Operational note:* the entire GPT-5 generation rejects an explicit
`temperature`, which both `adjudicate.py` and the corps `extract.py` hardcode to
0. `adjudicate.py` retries without it.

#### 5. Transitive closure is the sharpest demo material

WCC over unadjudicated candidates produces one 54-node component containing
both captains, Sacagawea, York and most of the sergeants. Over string+alias
only it is legible and the failure is visible in miniature:

```
GEORGE DREWYER + GEORGE DROUILLARD + GEORGE SHANNON
JOHN B. THOMPSON + JOHN SHEILDS + JOHN SHIELDS
```

Two correct edges plus one wrong edge on a shared given name, and Shannon is
permanently Drouillard. That is the argument for adjudication, shown rather
than asserted — and `--adjudicate` then produces clean components live.

Real duplicates still in the graph after two resolution passes, for the slides:
`DREWYER`/`GEORGE DROUILLARD` (328 mentions split), `CRUZATTE` in 11 forms,
`LABICHE` in 11, `BRATTEN`(24)/`BRATTON`(23) split almost evenly.

### Section 5 findings — working notes, not slide material

> **⚠️ This block is ~1,100 lines and went a long way into the weeds. Read this
> one-page summary and stop, unless you need a specific mechanism. The reading
> guide at the end says which sub-findings are load-bearing and which are
> superseded.**

#### Section 5 in one page

**The settled thesis** (third version; the first two were measured and
retracted):

> **Cosine retrieves the topic. Entity-seeded PPR retrieves the entity.** When a
> question turns on a specific thing and cosine's vocabulary match drags in the
> wrong ones of the same type, seeding the entity fixes it — *provided
> extraction attached that entity to the passage.*
>
> It earns its place in proportion to how many **same-type entities** your
> corpus holds. Forty engineers and you asked what Chen owns: worth it. One CEO,
> one product: don't bother.

**The four pieces of evidence that hold.** Each is measured on mass, on hundreds
of items, or by reading — never on a small-sample threshold:

| | |
|---|---|
| **The failure is real and exact** | 69 passages mention Charbonneau; median cosine rank **300**; **2** in the top-8. Four of eight slots go to *other* interpreters — Dorion, Gravelin, Duriaur (5e; `lewisclark` numbers, 5o — `neo4j` was 62/296/2) |
| **The entity signal is load-bearing** | delete it and the hand-judged passages fall `[3,6] → [26,14]` and `[6] → [15]` (5o; on `neo4j` it was ~7 rank positions, 5d-quinquies) |
| **The hand read** | redone on `lewisclark` windows: 11 promoted passages read in full across 3 questions; **3 clear the bar** (5o, Nathan's read pending). Demo case is `charbonneau-role` (`neo4j` history: 4 of 16, 5d) |
| **The best single instance** | a 305-char passage at cosine rank 20 that **never names Sacagawea**, reachable only because extraction resolved *"one of his wives"* → `SACAGAWEA` — retagging confirmed on `lewisclark` (5d, 5o) |

**Three limits, all measured, all stated on stage** — this is what makes the
multi-tool argument structural rather than a hedge:

1. **Combines evidence with weights you didn't choose.** Additivity *is* a
   conjunction bonus — comparable-degree seeds put all 17 dual-mention chunks
   in the top-20 at median rank 9 (SAC+CHAR, 5o). But each seed's share goes
   as `1/degree`, so a hub is nearly free to ignore — LEWIS(825)+CYNOMYS(42):
   a 6.1% bonus (5o; 5d-quater's mechanism, and the corrected linearity note).
2. **Cannot enumerate or order.** 18 passages in the week before Floyd died;
   cosine's top-8 holds 3, and so does *every* graph variant including
   `NEXT_CHUNK` at long damping — replicated exactly on `lewisclark` (5c, 5o).
   A date filter returns 18 in one hop.
3. **Bounded by extraction.** No keelboat entity exists anywhere in the graph,
   so the question that names one can seed nothing (5o; the `neo4j` receipt —
   the horse missing from the horse-trading passage — was *fixed* by the luna
   extraction, which is the measured "better extraction moves the boundary,
   it does not remove it" coda).

**What was retracted, and why it matters more than the wins:**

| retracted | why |
|---|---|
| The hub trap as the section's centrepiece | Lewis is the *third* hub (deer 589, elk 439); nothing is 2 hops from everything (15.4%); naive PPR does **not** return the same passages (0/8 overlap) — finding 1 |
| The long-passage blur hypothesis | sign reversed — longer passages rank **better** (Spearman −0.252) — finding 3 |
| The conjunction thesis | the co-mention proxy was hub-contaminated (100% for grizzly, 87% food-sources); the Floyd demo case was a **false positive** — the passage is from ten weeks before he died — findings 4, 10, 5d |
| Four tuning conclusions (5d-bis…quater) | the judged passages saturate the entity percentile at 0.97–0.999, and a binary top-8 threshold on n=4 turned one-position drift into "findings" — **5d-quinquies** |

**Open decisions — a fresh conversation should start here:**

1. **Title sign-off.** *"Your ranking can't tell people apart."*
2. **`neo4j` vs `lewisclark` — DECIDED and DONE (2026-09-07): `lewisclark`
   for everything; the 5.1–5.11 migration landed.** Full record in
   **finding 5o**; slides updated; `neo4j` tables kept in findings 1–5k as
   history. How the checklist resolved, item by item:
   - **Re-measured, shifts as predicted and one bigger**: failure table
     69/300/2 (Charbonneau df 69, as predicted); hub table — the *unpredicted*
     shift: **Lewis is now the top hub** (825 chunks, 28.3%), so the
     deer-outranks-the-captains punchline died and 5.6 now runs on
     elk-outranks-Clark + "a better extractor moved the hub"; Drewyer
     297/Drouillard 84 row survives on screen; ladder 2.84 → 0.47/8 (Lewis
     3.2 → 18.1; decomposed-seed methodology note in 5o); damping direction
     holds (0.85 worst); `alpha=1.0` 14/14; latency ~215 ms fresh; Nov-4 at
     cosine rank 20, SACAGAWEA/SHOSHONE tags confirmed.
   - **Mechanism change executed**: demo path is `--seeder decomposed`
     everywhere; `charbonneau-role` seeds one node at weight 1.0. The
     duplicate-seeding receipt pivoted to **PACIFIC OCEAN / PACIFIC OCIAN**
     (df 19/5, weights 0.605/0.395) rather than Drewyer/Drouillard — measured:
     cross-token spelling shards do NOT get hedged (GEORGE DROUILLARD scores
     2.99 vs DREWYER 10.15 on `'Drewyer'`, below the 0.5 keep-ratio), which
     is 5k's boundary and is now an honesty line on slide 5.4.
   - **Hand reads redone, not ported**: 11 promotions read, 3 clear (5o) —
     **Nathan's read pending**.
   - **Projection**: `lc-retrieval` projected on `lewisclark`
     (8,139 / 63,836, 78 ms).
   - **Heap**: found already at **8 GiB** — no restart needed.
3. **Gold-set design fix** — gold should name what makes an answer *correct*,
   not every entity present. Drop hub entities; fold `gold_overrides.yaml` into
   `questions.yaml`; teach `verify_questions.py` to rank by mention count.
   Unblocks Step 5 (finding 10).
4. **How much of the retraction to tell** in slide 5.9 (~20 seconds).
5. **The section's frame (5h-5) — now measured, and the third leg failed
   (5i).** The ablation ran: on an NER-grade graph the filter goes blind to
   the coref-only passages *and the walk does not buy them back* (ranks
   114–1108 vs 11–62 on the full graph; SACAGAWEA keeps 6 of 64 edges).
   NEXT_CHUNK is no coreference patch (nearest naming chunk is 169 hops from
   the fever passage). Then re-run on a REAL budget graph (5j, `budgetluna` =
   `rawluna` + indexes, no resolution): harsher still — the luna extraction
   shatters her identity across 19 shard nodes + 25 untagged chunks, the
   walk leaves the fever/Aug-14 passages at rank 1709/1475, and the
   edge-support metric scores the worse graph *better* (75.1% name-backed vs
   gold's 64.5%). Seeding every shard (5j-bis) closes the loop: with oracle
   shards even the *filter* recovers 2 of 3 (query-time compensation =
   query-time entity resolution), automatic shard discovery is a knife-edge,
   and the one adjacency win (shards × NEXT_CHUNK, fever 1844→47) runs
   through a shard the "correct" merge would exclude. "About as good, less
   work up front" is off slides permanently in that form. The landing is
   Nathan's (end of 5j-bis): *resolve the shards at query time and you might
   as well be filtering on tags again* — every query-time trick measured is
   the tag filter or entity resolution in disguise; the value lives in the
   entity layer. How to stage that is the open decision.
6. **The thematic beat (5l) — the walk's one clean win on a good graph, now
   measured on `lewisclark`.** Zero-mention questions have no filter to run;
   hand reads give expand trade-goods (buttons-off-coats from cosine 77) and
   food-sources (month coverage 5→7) and take illness-and-injury (window
   collapses onto one episode, 4→1 months — the measured entrance to §6).
   Open: how much stage time, and whether the 5.12 decision table gains the
   row *"questions name nothing → passage-seeded expansion + community cap."*
7. **The neighborhood beat (5m) — Class 1 measured, and it splits on anchor
   degree.** "Sacagawea's brother": filter sees 2/16 by construction, but no
   strategy top-8s a single target (bridge = 2 of her 85 edges — reachable,
   not ranked, with a denominator); the walk's contribution is surfacing the
   *name* Cameahwait at pure-walk rank 4 → two-step retrieval, hand-off to
   §7. The low-df replication (Walla Walla chief, anchor df 3) wins one-shot:
   blend median 10 vs cosine 43, crossing 1-of-12 nation shards to the
   chief's untagged chunks. The delete-test (median 338→601 with the two
   bridge chunks removed) is the section's cleanest mechanism demo. Open:
   stage time, and the decision-table row *"the answer's entity is the
   unknown → low-df anchor: walk and done; hub anchor: walk for the name,
   then query it."*
8. **The agent routing rule (5n) — Nathan's, measured.** Seed degree predicts
   whether expansion pays, monotonically across 38k anchor/satellite pairs
   (median exclusive-chunk walk-rank 39 at df 2–5 → 1,058 at df 300+). The
   routing table (zero mentions → passage-expand; df≲15 → expand; df≳40 →
   filter or two-step) is one COUNT query to implement. Open: whether it
   lives in §5's close or §9's implementation beat — it is the talk's
   sharpest "when do I actually need the graph" answer. **Drafted
   (2026-09-07): §5 close redrafted as 5.12–5.14 around this story
   (`section-05-slides.md`), routing table on stage in 5.14, decay curve
   parked for §9. Pending Nathan: the cut plan to 10:00 (trims inside
   previously-protected beats, or 5.12 moves to open §6), and the fact that
   5.1–5.11 quote `neo4j` while 5.12–5.14 quote `lewisclark` — open decision
   #2's re-measurement question is now forced.**

**Highest-leverage untested change**: **question decomposition for seed
selection.** The entity seeder is itself a cosine step with cosine's disease —
it returns `WISDOM RIVER` and `SAGITTARIA LATIFOLIA` for a Sacagawea question.
Naming the entities from the question (NER, parse, or an agent choosing
explicitly) is where the leverage is; edge weights, seed weights and degree
filters all measured no-op or unmeasurable (5d-ter, 5d-quinquies). **Now built
and measured — see finding 5f.**

**Reading guide:**

| load-bearing | 1, 2, 3, 4, 5b, 5c, 5d, 5e, 5g, 5h, 5i, 5j, 5k, 5l, 5m, 5n, **5o (the migrated numbers — quote these)**, 8, 9, 10, 11, 12 |
|---|---|
| **mechanisms hold, conclusions do not** | 5d-bis, 5d-ter, 5d-quater — see the warning on each |
| **read before any of those three** | **5d-quinquies** |
| superseded numbers | finding 5's blend/damping/seed sweeps were scored against the contaminated proxy; keep for history, do not quote |


> ⚠️ **Two of this section's own claims did not reproduce and are retracted
> below.** The history is kept, exactly as in section 4: "the mechanism I
> assumed was wrong, and here is what the data said instead" is the most useful
> thing in the section. Measured 2026-09-07 against the **`neo4j`** demo graph,
> read-only. Every number below is `neo4j`-specific — see finding #12.
>
> **Migration note (2026-09-07, later):** the demo graph is now `lewisclark`
> and every number slides 5.1–5.11 quote was re-measured there — see
> **finding 5o** for the old-vs-new record. The `neo4j` tables in findings
> 1–5k stay as written, as history; quote 5o, not them.

#### 1. RETRACTED: the hub trap as the outline stated it

The outline claimed *"every chunk in the corpus is two hops from every other
chunk through MERIWETHER LEWIS... run it naively and every question returns
roughly the same passages."* All three parts are false here.

| claim | measured |
|---|---|
| Lewis is the dominant hub | **He is third.** `ODOCOILEUS VIRGINIANUS` 589 chunks, `CERVUS CANADENSIS` 439, Lewis 377 |
| every chunk is 2 hops from every other | mean 2-hop reach is **448 of 2,912** — 15.4% of the corpus (median 424, max 1,154, min 0) |
| every question returns the same passages | cross-question overlap of unrestricted PPR top-8 is **0.00/8 — every pair, every mode.** 48 distinct passages in 48 slots |

The corpus is a daily record of what the party shot and ate, and
`add_taxonomy.py` renamed the animals to Latin binomials, so the deer outranks
both captains. Lewis alone accounts for 1.67% of chunk pairs; the deer 4.08%.

#### 2. What survives: the trap is real at the *entity* level

| | naive (unweighted) | + IDF | + IDF & lift |
|---|---|---|---|
| entity top-8 cross-question overlap | **4.53/8** | **0.60/8** | **0.00/8** |
| PPR mass on the 10 biggest hubs | 12.60% | 6.95% | — |
| mean rank of Lewis among entities | **2.5** | 9.0 | — |
| median mention-count of top entities | — | 23 | **2** |

Naive, the walk believes every question is about Lewis, Clark, Drouillard and
deer — Lewis is the *single top entity* for the prairie-dog, Floyd and Great
Falls questions. IDF-weighted, the top entities become `EQUUS CABALLUS` for the
horse question, `CYNOMYS LUDOVICIANUS` for the prairie dog, `EXAMINATION OF
PORTAGE` for the portage.

**And the mechanism explains why the passage level was spared.** A hub
*receives* mass from every passage mentioning it, so it concentrates; when it
re-emits, it sprays that mass across 589 passages, so each gets almost nothing.
**Hubs concentrate at the entity level and dissipate at the passage level.**
Consequence worth a slide: IDF weighting is essential when the output you
consume is the entity set (graph expansion, subgraph extraction, community
seeding) and much less important when you only read passages off the end.

**Lift is not free.** It drives overlap to zero by pushing the median
mention-count of top entities from 23 to **2** — you trade hubs for one-off
noise. Two fixes where one overcorrects is a better ten minutes than two that
both simply work.

#### 3. RETRACTED: the long-passage blur hypothesis

The hypothesis — a long, topically mixed passage has a blurry centroid
embedding, so a specific detail inside it ranks poorly — is **disconfirmed, with
the sign reversed.**

| gold-bearing passages | n | median cosine rank |
|---|---|---|
| short (<250 words) | 77 | **946** |
| long (≥400 words) | 213 | **389** |

`Spearman(words, cosine rank) = −0.252`; entity count is flat at −0.025.
**Longer passages rank better.** Averaging dilutes specificity but also broadens
coverage — more text means more surface area to overlap the query's vocabulary
— and on this corpus coverage wins. The long mixed passages are the ones cosine
*likes*.

#### 4. The real failure: cosine has no representation for conjunction

Passages mentioning **two or more** of a question's gold entities, and how many
reach the vector top-8:

| question | kind | bearing | best rank | median | in top-8 |
|---|---|---|---|---|---|
| shoshone-horses | connection | 86 | 5 | 578 | 2 |
| sacagawea-interpreting | connection | 26 | 1 | 108 | 4 |
| charbonneau-role | connection | 13 | 5 | 121 | 1 |
| grizzly-encounters | authority | 24 | 17 | 445 | **0** |
| great-falls-portage | authority | 46 | 9 | 638 | **0** |
| fort-clatsop-winter | authority | 9 | 1 | 15 | 3 |
| trade-goods | thematic | 8 | **166** | 724 | **0** |
| food-sources | thematic | 162 | 4 | 743 | 1 |
| illness-and-injury | thematic | 16 | 19 | 468 | **0** |
| before-floyd-death | sequence | 1 | **415** | 415 | **0** |
| pacific-arrival | sequence | 16 | 3 | 277 | 1 |
| keelboat-return | control | 13 | 5 | 165 | 1 |
| prairie-dog | control | 0 | — | — | — |

**Five of thirteen questions have zero conjunction-bearing passages in the
vector top-8.** A passage that answers by *combining* entities does not read
like the question — an entry naming Floyd and the Missouri reads like a day's
log. Multi-seed PPR is natively conjunction-aware: seed at both and passages
touching both accumulate mass from two independent sources.

Note the `kind` column — `connection` questions retrieve tolerably, `authority`
and `thematic` do not. That is the same line section 8 draws, arriving here
independently.

*(`prairie-dog` shows 0 because it has a single gold entity and the test needs
two. An artifact, not a result.)*

#### 5. Multi-seed PPR + blend: the measured result

Setup: `MENTIONED_IN`-only undirected projection, entity seeds from
question-to-entity semantic match across the eight entity vector indexes (**no
gold used to pick seeds**), passage seeds from the cosine top-5, blended on
percentile ranks over the whole corpus.

| strategy | conjunction passages in top-8 | median rank |
|---|---|---|
| cosine only | 14 | 524 |
| entity-seeded PPR only | 9 | 488 |
| passage-seeded PPR only | 12 | 353 |
| blend 0.6 / 0.4 | 22 | 323 |
| blend 0.2 / 0.8 | **24** | **276** |
| entity + passage PPR, no cosine | 19 | 309 |

**Cosine alone is the worst row.** Any blend lifts top-8 hits ~60%. There is a
broad plateau from cosine weight 0.9 down to 0.1 — the knob is forgiving, and
Nathan's 60/40 instinct sits comfortably inside it. **Do not quote a single
optimum**: the top-8 column bounces 21→23→22→22→21→24→21 and that is noise on
thirteen questions. Median rank *is* monotonic in structure weight.

**The demo case.** `before-floyd-death` — one passage in the corpus names both
Charles Floyd and the Missouri River. Cosine ranks it **415 of 2,913**. Blended
retrieval reaches it at **68** with the shipped 0.6/0.4 weighting and at **16**
at pure structure. *(An earlier draft of this section quoted "413 → 16" — the
413 was a transcription error for 415, and the 16 silently assumed pure
structure. Both corrected.)* The blend-dependence is worth showing rather than
hiding: this is the one passage where cosine's weight is pure cost.

**The entity seeds are a demo screen in their own right:**

```
shoshone-horses      PURCHASE OF HORSES · EXCHANGE OF HORSES · TRADE FOR HORSES
grizzly-encounters   URSUS ARCTOS HORRIBILIS · WHITE BEAR CLIFT · WHITEBEAR ISLANDS
great-falls-portage  PORTAGE DIFFICULTY · GREAT FALLS · PORTAGE OF 940 YARDS
sacagawea-interp.    SACAGAWEA(NativeNation) · SACAGAWEA(Person) · INTERPRETERS WIFE
```

The last row seeds **both** Sacagawea nodes — the real `Person` and a mislabeled
`NativeNation` duplicate — and the result is fine. That is the "you do not have
to resolve it first" claim demonstrated live, and a better section 10 callback
than running a second database.

**Resolved: seed weighting does nothing. Seed *count* does everything.**

Four weighting schemes, measured over the bank. ``softmax`` at temperature 0.01
collapses to a single effective seed (1.00/0.00/0.00) and ``margin`` reaches a
13× ratio, so the spread is real, not cosmetic:

| weighting | top-8 | median rank | structure only: top-8 | median |
|---|---|---|---|---|
| uniform | 22 | 318 | 10 | 502 |
| proportional | 22 | 318 | 10 | 500 |
| softmax | 22 | 326 | 10 | 506 |
| margin | 23 | 326 | 10 | 502 |

**Nothing moves.** The mechanism: every seed for a question is semantically
close to the question, so the seeds sit in overlapping neighbourhoods and their
PPR distributions are nearly parallel — reweighting nearly-parallel vectors
barely rotates the sum. Weighting *would* matter if the seeds were genuinely far
apart in the graph, which is worth saying from the stage, because that is
exactly the situation people reach for it in.

Then vary the *number* of seeds instead:

| seeds | top-8 | median rank | structure only: top-8 | median |
|---|---|---|---|---|
| 1 | 14 | 380 | 8 | 876 |
| **2** | **23** | **308** | **13** | 593 |
| 3 | 22 | 314 | 11 | 484 |
| 4 | 22 | 310 | 12 | **438** |
| 5 | 22 | 318 | 10 | 500 |
| 8 | 23 | 335 | **4** | 592 |
| 12 | 19 | 346 | **3** | 572 |

**One seed to two is a 64% lift in conjunction passages reaching the top-8**,
and everything after that is a plateau in the blend. Under pure structure the
tail degrades hard — 8 seeds drops to 4 in the top-8 — because weak semantic
matches start seeding unrelated neighbourhoods, and cosine's share masks that in
the blend.

So the design claim survives in a sharper and more useful form:

> You do not need to *pick* the right entity, and you do not need to weight the
> candidates cleverly. You need to stop choosing exactly **one**.

All four weightings stay selectable so the demo can *show* the non-effect rather
than assert it — `demo_pagerank.py --weighting-check` prints both tables.
Shipped defaults: `seed_weighting="proportional"` (principled, free, harmless),
`entity_seed_k=3` (inside the blended plateau and near the pure-structure peak,
so robust across both regimes rather than best in either).

#### 5b. Latency — and a retracted measurement of my own

The outline used to claim "per-query PPR against a projected graph is
milliseconds." True of *one* PPR call, and the first implementation here made
eight of them — one per seed — for no reason, as it turns out.

**First attempt, and it was wrong.** I measured five separate single-seed runs
at 58 ms total against one five-source call at 53 ms, and concluded batching
does not help. The seed list came from
`MATCH (e)-[:MENTIONED_IN]->(c:Chunk) RETURN id(c) LIMIT 5`, which returns **the
same chunk five times** — so four of the five "runs" were cache hits. A second
measurement in the same session said 53 ms per seed and contradicted it; the
contradiction is what exposed the bug.

**Measured properly**, with distinct real seeds:

| seeds | 1 call, N sources | N calls, 1 source | ratio |
|---|---|---|---|
| 1 | 52.4 ms | 53.4 ms | 1.02× |
| 2 | 54.9 ms | 107.8 ms | 1.96× |
| 3 | 53.8 ms | 165.0 ms | 3.07× |
| 5 | 54.8 ms | 273.5 ms | 4.99× |
| 8 | 56.2 ms | 440.6 ms | 7.84× |

Near-linear in the number of seeds, because the cost is per-call fixed overhead
— graph setup plus streaming 6,270 rows — not the source count. The pandas
weighted sum was never the cost either: 0.3 ms.

**End-to-end effect:**

| | one call per seed | one call per signal |
|---|---|---|
| `expand`, fresh question | ~580 ms | **196 ms** |
| entity PPR (3 seeds) | 187 ms | 72 ms |
| passage PPR (5 seeds) | 273 ms | 53 ms |
| cosine over 2,913 chunks | 39 ms | 39 ms |

The whole retrieval is now **two** PPR calls, one per structural signal,
regardless of how many seeds each restarts from.

Retrieval quality is unchanged — every conjunction median stayed within noise,
and several bests improved.

**Why batching is safe — and I got the reason wrong first.** My initial fix
assumed `sourceNodes` only took a flat list, so I reasoned that batching
required a *uniform* restart distribution, which was acceptable only because
seed weighting had measured as a no-op. Nathan pointed at the
[GDS PageRank syntax](https://neo4j.com/docs/graph-data-science/current/algorithms/page-rank/),
which documents node-bias pairs:

> To use different bias for different source nodes, use the syntax:
> `[[nodeId1, bias1], [nodeId2, bias2], …]`

So there was never a trade-off. Measured against GDS 2026.7.0, since the docs
do not say:

| question | answer |
|---|---|
| Is the pair syntax accepted? | yes |
| Is bias the linear weight? | **yes** — `sourceNodes=[[n,w],…]` equals `Σ w·PPR(n)` to 7e-07 |
| Are biases normalised? | **no** — doubling every bias doubles every score exactly |
| Is a flat list equivalent to bias 1.0? | yes, to 1.7e-18 |

That last one is why a flat batched run is the **sum** of the single-seed runs
and not their mean: GDS gives each source node its own unit of restart mass. A
mean-normalised comparison differs by a factor of `|S|` — 0.385 on a 3-seed
question — which is what first made me think linearity had failed. It had not;
Spearman between the two is 0.999992 and the top-5 are identical.

`seed_weighting` therefore stays at `proportional`, the principled default,
rather than being pushed to `uniform` to buy speed that was never at stake.
`combine_seeds()` is kept only to make the linearity claim checkable, and its
docstring now says so.

**The transferable lesson**, and it is better than the fix: I designed around a
limitation the parameter list does not have, and then measured a trade-off that
does not exist. Read the signature first.


Projection really is amortised, so that half of the original claim stands.

Also from the benchmark harness, and **directional only** — the gold set still
has the defects in finding #10, so these are not quotable:

Also from the benchmark harness, and **directional only** — the gold set still
has the defects in finding #10, so these are not quotable:

| strategy | recall | Δ vs vector | redundancy | p50 |
|---|---|---|---|---|
| vector | 74.4% | — | 0.054 | 4 ms |
| ppr | 74.4% | **+0.0 pts** | 0.057 | 79 ms |
| expand | 78.2% | +3.8 pts | **0.096** | 522 ms |

Two things fall out even so. `ppr` scoring **exactly zero** improvement is the
candidate-gate ceiling showing up on an independent metric. And `expand`'s
redundancy nearly doubling (0.054 → 0.096) is a real cost that hands section 6
its setup: more structure pulls in more passages about the same episode, which
is precisely what community diversification is for.

#### 5c. Coverage questions are not section 5's business — measured

Nathan's point, and it holds: cosine does badly when the answer spans **more
than one chunk**, and the arbitrary top-k cutoff is the mechanism. The surprise
is that the graph does not help either.

`before-floyd-death` — Floyd died 1804-08-20, and 18 passages exist for
08-13..08-20:

| retrieval mode | in top-8 | in top-20 |
|---|---|---|
| cosine only | **3 / 18** | 3 / 18 |
| blend + `lc-mentions` (shipped) | 3 / 18 | 3 / 18 |
| blend + `lc-retrieval` (has `NEXT_CHUNK`) | 3 / 18 | 3 / 18 |
| blend + `lc-retrieval`, damping 0.85 | 3 / 18 | 3 / 18 |
| **date-filtered Cypher** | **18 / 18** in one hop | — |

Fifteen of the eighteen are ordinary daily entries about weather and hunting.
Neither their vocabulary nor their entity structure marks them as "the days
before Floyd died" — **only the date does**, and only a filter can express that.

Two consequences:

1. **`questions.yaml`'s note on this question was false and is corrected.** It
   claimed `NEXT_CHUNK` in the projection lets PageRank flow along the journal's
   reading order. It does not. `kind: sequence` questions must not be used to
   evaluate PageRank.
2. **This is the measured basis for a multi-tool framing.** Three retrieval
   modes with three distinct failure profiles:

   | mode | good at | blind to |
   |---|---|---|
   | cosine | topical resemblance | enumeration; anything needing an arbitrary cutoff |
   | multi-seed PPR | connection, corroboration | ordering, completeness, dates |
   | text2cypher / filters | exact enumeration when the constraint is expressible | anything not expressible as a constraint |

   Neither of the first two dominates. Section 5's honest job is to teach what
   structure adds *and* name what it does not — the choice is per question.

*(Constraint from Nathan, 2026-09-07: **do not modify the community-days demo
repo** unless specifically instructed. Any agent/tool work stays a proposal.)*

#### 5d. The hand read — 16 promotions, judged by reading them

The conjunction proxy was broken, so the only honest test left was to read
every passage the blend promotes into the top-8 from outside cosine's, for the
three `kind: connection` questions, and ask one thing of each: **does it contain
something a correct answer needs that no cosine top-8 passage contains?**

| question | cosine top-8 | promotions | clear the bar |
|---|---|---|---|
| `charbonneau-role` | **2 of 8 relevant** | 6 | **3** |
| `sacagawea-interpreting` | 3 strong, 1 partial | 3 | **1 (decisive)** |
| `shoshone-horses` | 1 strong, 2 context | 7 | **0** |

**4 of 16.** Not a rout, not nothing. What matters is that the wins and the
losses have different causes, and both are teachable.

##### Where it works: cosine retrieves the *topic*, PPR retrieves the *entity*

`charbonneau-role` is the case to demo. Cosine's top-8 has only two relevant
passages; the other six are about **different interpreters** — Dorion with the
Sioux, Gravelin with the Ricara, Jusseaume — plus the arrival at St. Charles
and a list of Sioux bands. Charbonneau is not named in any of them. Cosine
matched the *word* "interpreter". The three promotions that clear the bar carry
what the question actually asks:

```
1805-03-18  "Mr. Tousent Chabono, Enlisted as an Interpreter this evening"   <- the hiring
1804-12-18  "Chabonoe our big belly interpeter"                              <- WHICH language
1805-08-25  "out of patience with the folly of Charbono who had not
             sufficient sagacity to see the consequencies"                   <- his judgement
```

And the single best instance in the whole read, from
`sacagawea-interpreting` — cosine rank **22**, 305 characters, and it **never
uses her name**:

> `1804-11-04` *"a french man by Name Chabonah, who Speaks the Big Belley
> language visit us, he wished to hire & informed us his 2 Squars were Snake
> Indians, we engau him to go on with us and take one of his wives to interpet
> the Snake language"*

That is the hiring *and* the arrangement the question asks about. It is
reachable because extraction resolved **"one of his wives" → `SACAGAWEA`** and
**"Snake Indians" → `SHOSHONE`**. The entity layer carries a coreference the
text never states, so cosine cannot reach it and the graph can. **That is
section 4 paying off in section 5, on one readable passage** — a far better
callback than a second database.

##### Where it fails: `shoshone-horses`, and it fails three times over

All seven promotions are April–May 1806, about the **Nez Perce, Skillutes,
Eneshur and Walla Walla** — the return journey. Not one concerns the Shoshone.
The question names the nation; every promotion is a different nation a year
later. Three separate causes, each worth knowing:

1. **The seeder matched the verb, not the constraint.** It chose
   `PURCHASE OF HORSES`, `EXCHANGE OF HORSES`, `TRADE FOR HORSES` — generic
   Event nodes — over `SHOSHONE`. Same error class as cosine's, committed one
   layer up.
2. **Seeding the discriminating entities barely helps.** Forcing
   `SHOSHONE + SACAGAWEA` moves August-1805 passages in the top-8 from 1 to 2.
3. **And no combiner rescues it.** `SUM` (what linearity gives) and `MIN` (a
   deliberately conjunctive combiner) both return **0 of 8** August-1805
   passages.

##### Why (3) happens, and it is the section's real lesson

Read the entities the extractor attached to the Aug 18 1805 passage — the one
that *is* the answer, *"I soon obtained three very good horses for which I gave
an uniform coat, a pair of legings, a few handkerchiefs, three knives"*:

```
SHOSHONE (NativeNation) · SHOSHONE COVE · DREWYER · WILLIAM CLARK · JEFFERSON RIVER
UNIFORM COAT · PAIR OF LEGINGS · THREE KNIVES · HANDKERCHIEFS · OLD CHECKED SHIRT  (all Supply)
CHIEFS COAT · WIFE · INTERPRETER  (all mislabelled Person)
```

**There is no horse.** A passage about buying three horses has no horse entity
attached. The traded goods are all there — as `Supply`, which has **no embedding
and no vector index**, so the seeder can never select them. The horse-trading
`Event` nodes exist but sit on 1805-08-28, 1806-04-19, 1806-04-25 and
1806-05-10.

So the structure that would answer this question was never built. **No retrieval
algorithm over this graph can find it by structure**, and that bound is set by
extraction, not by ranking.

##### Combining evidence — stated correctly on the third attempt

*(Two earlier versions of this were wrong. The first said "PPR can never do
conjunction." The second corrected that to "additive scoring cannot represent
AND." Nathan then pointed out that my worked example presupposed its own
conclusion, and he was right. Full history kept, because the final answer is
more useful than any of the drafts.)*

**Where I went wrong.** I argued a weighted sum has no interaction term, so
`(1.0, 0.0)` and `(0.5, 0.5)` both score 1.0 and the sum cannot tell "near one
seed" from "near both". But if chunk X mentions entity A only and chunk Y
mentions A **and** B, then both sit one hop from A and receive *the same* mass
from it — and Y receives B's contribution **on top**. For my numbers to hold, Y
would have to be more weakly attached to A than X is, which is a different
scenario I had quietly assumed. **The sum does give a bonus for being connected
to both.**

**Measured, on comparable-degree seeds:**

| seeds | group | n | median rank | median score |
|---|---|---|---|---|
| `SACAGAWEA` (64) + `TOUSSAINT CHARBONNEAU` (62) | **both** | 9 | **5** | 0.004425 |
| | only A | 55 | 71 | 0.002166 |
| | only B | 53 | 51 | 0.002244 |

The "both" score is exactly the sum of the two singles (0.00217 + 0.00224 =
0.00441), and that additivity puts **all nine** dual-mention chunks in the
top-20 — median rank 5 against 51 and 71. That is a large, reliable conjunction
bonus, and it is the answer to "can PPR combine evidence": **yes, and well.**

**Where it actually degrades — degree, not additivity:**

| seeds | group | n | median rank | median score |
|---|---|---|---|---|
| `SHOSHONE` (192) + `EQUUS CABALLUS` (14) | both | 2 | 4 | 0.010669 |
| | only A | 190 | 110 | 0.000733 |
| | **only B** | 12 | **8** | **0.010007** |

Mass-per-chunk from a seed is roughly `1/degree`. The rare entity's 14 chunks
each take a big share; the hub's 192 each take a sliver. So a chunk mentioning
*only* `EQUUS CABALLUS` scores 0.0100 against 0.0107 for one mentioning both —
a **6.6%** bonus for also containing the Shoshone, and the top-20 holds 12
"only B" against 2 "both".

> **PPR does conjoin — but with weights you did not choose.** Each seed's
> contribution is set by its degree in the graph, not by what the question
> needs. Pair a rare entity with a hub and the hub is nearly free to ignore.

**And you cannot normalise that away.** Percentile-ranking each seed's vector
*before* summing equalises them and gives a clean conjunction signal —
dual-mention chunks separate from single-mention by 30-60× in rank:

| seeds | combination | both | only A | only B |
|---|---|---|---|---|
| SHOSHONE + EQUUS CABALLUS | raw sum (ships) | 4 | 110 | **8** |
| | per-seed percentile | 6 | **307** | **329** |
| MERIWETHER LEWIS (377) + CYNOMYS (23) | raw sum (ships) | 6 | 208 | **16** |
| | per-seed percentile | 10 | **401** | **387** |

**But it wrecks retrieval on the only ground truth available** — the hand-read
passages from finding 5d:

| | hand-judged passages in the top-8 |
|---|---|
| normalise **after** the sum (what ships) | `charbonneau-role` **3/3**, `sacagawea-interpreting` **1/1** |
| normalise **per seed** | **0/3**, **0/1** (best ranks 22, 11, 14 and 22) |

**Why**, and this is the load-bearing mechanic. Percentile-ranking a sparse PPR
vector inflates its near-zero tail into the whole score range:

```
seed                                 deg   chunks >1e-6   % near-zero
TOUSSAINT CHARBONNEAU                 62           2339         19.7%
JEAN BAPTISTE CHARBONNEAU              1           1637         43.8%
BIRTH OF JEAN BAPTISTE CHARBONNEAU     1            990         66.0%

BIRTH OF JEAN BAPTISTE CHARBONNEAU: 1,923 chunks sit at PPR <= 1e-6, and
percentile-ranking spreads them across 0.044 .. 0.660 — noise is handed
66% of the available score range.
```

Two of the three seeds have **degree 1**. Normalising per seed gives those two
noise fields equal footing with the one real signal.

**So the shipped design is right, for a reason worth saying out loud:**

> Normalising *after* the sum lets absolute PPR magnitude act as an **implicit
> confidence weight** on each seed. A degree-1 seed with nothing to say
> contributes almost nothing. The algorithm weights your seeds by how much they
> actually know.

**And that unifies this with finding #5.** Explicit seed weighting measured as a
no-op because the seeds are *already* self-weighted, by orders of magnitude in
PPR mass, while my explicit weights varied by about 2%. Weighting was never
going to matter — the sum had already done it better.

**What survives of the linearity point.** Not an expressive limit. Linearity is
why the whole seed set goes into one `sourceNodes` call *and* why the seeds
self-weight by informativeness. One property, two benefits.

##### 5d-bis. Edge weighting: what cancels, and the one variant that helps

> ⚠️ **The ranking comparisons in this finding measure noise** — the judged
> passages saturate the entity percentile, and the top-8 threshold amplifies
> one-position drift. See **5d-quinquies**. The *mechanisms* here hold; the
> conclusions about which setting is better do not.

Nathan's suggestion — weight the relationships by inverse entity degree before
running PPR, to fix the degree imbalance above. Tested, and it produced a real
improvement, though not the one intended.

**Inverse entity degree does nothing, and the reason is worth knowing.** A
weight that is a function of the **entity alone** cancels out of that entity's
own mass distribution: all 192 of `SHOSHONE`'s edges carry the same number, so
its outflow divides 192 ways regardless. Mean PPR mass on SHOSHONE's chunks:

| weight | mean mass per chunk |
|---|---|
| uniform 1.0 | 0.001439 |
| **1 / df** (inverse degree) | 0.001497 |
| IDF (ships) | 0.001449 |

Four percent apart. Which also explains what the shipped IDF *is* doing: it acts
on the **chunk's** outflow, steering mass toward rare entities. That is why it
collapses entity-level hub dominance (4.47/8 → 0.60/8) while leaving seed
mass-per-chunk untouched. Two different effects that look like one knob.

**So the weight has to vary across the seed's own edges.** Term frequency would
qualify — but there is none to use: of 14,799 (entity, chunk) pairs only **131**
have more than one edge, max 3, mean 1.009. The extractor emits one mention edge
per pair.

**Entity density is the available substitute** — the seed's share of the chunk's
entities. Measured against the hand-read passages of finding 5d:

| weighting | `charbonneau-role` ranks | `sacagawea-interpreting` Nov-4 rank |
|---|---|---|
| `idf` (default) | 7, 3, 5 | **8** |
| **`idf_over_entities`** | 5, 6, 3 | **3** |
| `inverse_entities` | 5, 6, 4 | 3 |

The decisive Nov-4 passage moves from rank **8 — one slot from falling out of
the window — to rank 3.** It is 305 characters holding three entities, so
Sacagawea is a third of it; a 2,000-character entry holding twenty gives each a
twentieth. Note `1/ec` alone ≈ `idf/ec`, so the chunk normalisation is doing the
work, not the IDF term.

**It does not fix conjunction.** `SHOSHONE`+`EQUUS CABALLUS` both/onlyHorse goes
4/8 → 10/6, slightly worse. This is a retrieval improvement, not an answer to
the degree imbalance.

**Not shipped as the default**, on n=4 hand-judged passages. Added as
`MENTION_WEIGHT` (`idf` | `idf_over_entities` | `inverse_entities` | `uniform`)
with the reasoning in `projection.py`, so the next person can settle it against
a wider read or a repaired gold set instead of re-deriving it.

**The remaining honest option for the degree imbalance** is degree-proportional
seed *bias* — `sourceNodes: [[id, degree], ...]` — which equalises what each
seed contributes per chunk. Untested, and it carries an obvious cost: it
elevates all 192 of a hub's chunks to the level of a rare entity's 14, which is
the hub trap arriving through a different door. Worth measuring before believing.

##### 5d-ter. Rare seeds dominate — and the seeder has cosine's disease

> ⚠️ **The ranking comparisons in this finding measure noise** — the judged
> passages saturate the entity percentile, and the top-8 threshold amplifies
> one-position drift. See **5d-quinquies**. The *mechanisms* here hold; the
> conclusions about which setting is better do not.

Nathan's concern: pick four or five seeds matching the question, one of them
rare and a weaker match, and the rare one dominates PageRank. **Confirmed as a
mechanism, and it explains more than it was aimed at.**

PPR normalises each single-seed run to sum ≈ 1, so **every seed receives the
same total mass regardless of degree** — and mass *per chunk* therefore goes as
`1/degree`. A degree-1 seed puts essentially all its mass on its single chunk:
about 62× what a degree-62 seed gives each of its own. Actual seed degrees:

| question | seed degrees |
|---|---|
| `charbonneau-role` | 62, **1**, **1** |
| `sacagawea-interpreting` | 64, **1** |
| `shoshone-horses` | **2, 1, 1** — the entire entity signal is four chunks |

And the top of the entity ranking is then mechanical rather than retrieved:
`1806-05-10` took **99.9%** of its score from one degree-1 seed; `1806-04-25`
likewise. That is the deeper reason `shoshone-horses` failed — not just that the
seeder chose topical Events, but that those Events are degree-1 nodes each
spiking one arbitrary passage.

**Semantic match cannot police this.** Match scores span ~2% across the seeds;
degree spans 62×. `seed_weighting` is three orders of magnitude too weak to
compensate — the same reason weighting measured as a no-op in finding #5.

**A degree-1 seed is a confident bet, not automatically a bad one.**
`BIRTH OF JEAN BAPTISTE CHARBONNEAU` (degree 1) spikes `1805-02-11`, the birth
passage, genuinely relevant. `JEAN BAPTISTE CHARBONNEAU` (degree 1) spikes
`1806-05-27`, which is not. All of the mass on one passage, no hedging: precise
when extraction put the entity in the right place, a confident error when it
did not.

**Why this has not hurt more, and it is not reassuring.** Cosine's 60% is
masking the spikes. Push the blend to cosine 0.3 and `charbonneau-role` goes
**3/3 → 2/3**. So the blend weight is doing double duty — combining signals
*and* suppressing seed-degree artifacts. "Tune the blend" is partly "tune how
much seed noise you tolerate," which is not a clean design.

**Two remedies tested, neither a fix:**

| min_seed_degree | `charbonneau` | `sacagawea` | `shoshone` Aug-1805 | seeds selected |
|---|---|---|---|---|
| **0** (ships) | **3/3** | 1/1 [8] | 1/8 | the degree-1 ones |
| 3 | 2/3 | 1/1 [7] | 2/8 | + `ST. CHARLES` |
| 5 | 2/3 | 1/1 [6] | 2/8 | + `WISDOM RIVER`, `SAGITTARIA LATIFOLIA` |
| 10 | **3/3** | 1/1 [6] | 2/8 | `TOUSSAINT CHARBONNEAU` alone |

Degree-proportional seed bias measured equivalent to filtering, and both are
marginal. Filtering at 3 and 5 makes `charbonneau-role` **worse**, and only
recovers at 10 — where the threshold is strict enough that one clean seed
survives. **What helps is fewer, better seeds; not the degree filter.**

##### And the finding underneath all of it

Look at what the filter admits in place of the degree-1 seeds: `WISDOM RIVER`
and `SAGITTARIA LATIFOLIA`, for a question about Sacagawea interpreting.
`ST. CHARLES`, for a question about Charbonneau.

> **The entity seeder is itself a cosine retrieval step, and it has cosine's
> disease.** It matches a whole-question embedding against entity names and
> returns things that are vaguely expedition-flavoured. The remedy for co-typed
> substitution is being delivered by a mechanism that suffers from co-typed
> substitution.

So the leverage in this pipeline is not in edge weights, seed weights, or degree
filters — all three measured as no-ops or marginal. It is in **seed selection**,
and doing that properly means *naming* the entities the question is about rather
than embedding-matching the question as a whole. That is question decomposition
— an NER or parse step, or the agent Nathan described choosing entities
explicitly — and it is the single highest-leverage untested change to this
section's pipeline. *(Since built and measured: finding 5f, `decompose.py`.)*

`min_seed_degree` is added and documented, **default 0**, with the measurement
and the caveat that it can empty the seed set (all three `shoshone-horses` seeds
are discarded at a threshold of 5; the code falls back rather than returning
nothing). n=4 hand-judged passages throughout, so these are directions, not
verdicts.

##### 5d-quater. Sharpened bias helps — and it argues for ONE seed, not several

> ⚠️ **The ranking comparisons in this finding measure noise** — the judged
> passages saturate the entity percentile, and the top-8 threshold amplifies
> one-position drift. See **5d-quinquies**. The *mechanisms* here hold; the
> conclusions about which setting is better do not.

Nathan's proposal: inverse entity degree in the projection, plus sharpened
biases prioritising stronger cosine similarity. Tested as a cross-product. The
sharpening helps; the projection change does not.

The reason it was worth trying, which neither of us had said: **the degree-1
seeds are also the weaker cosine matches.**

```
charbonneau:  TOUSSAINT CHARBONNEAU  0.862  (deg 62)
              JEAN BAPTISTE          0.808  (deg 1)
              BIRTH OF JEAN BAPTISTE 0.800  (deg 1)
```

So sharpening on match score suppresses exactly the seeds that spike.

| projection | bias | `charbonneau` | `sacagawea` Nov-4 |
|---|---|---|---|
| **IDF** | proportional *(ships)* | 3/3 [7,3,5] | [8] |
| IDF | power:20 → 0.67/0.18/0.15 | 3/3 [8,3,4] | [7] |
| IDF | softmax:0.03 | 3/3 [8,3,4] | [7] |
| **IDF** | **softmax:0.01 → 0.99/0.00/0.00** | 3/3 [8,3,4] | **[5]** |
| `inverse_degree` | proportional | 3/3 [7,3,4] | [7] |
| `inverse_degree` | *every* sharpening scheme | 3/3 [7,3,4] | [7] |

**Best result measured on this pipeline so far**: IDF + aggressive sharpening.
The Nov-4 passage moves 8 → 5, out of precarious and into comfortable.
Charbonneau is a wash (same rank sum).

**Unexplained**: under `inverse_degree`, five different bias schemes produce
*identical* output — sharpening is completely inert. `1/df` spans 3000× against
IDF's 11×, so the walk is plausibly dominated by rare-entity funnelling in a way
that swamps the restart distribution, but that is a guess. Flagged, not claimed.

##### The uncomfortable implication, and it retires a claim of mine

`softmax:0.01` produces weights `0.99 / 0.00 / 0.00`. **That is a single seed.**
Which is the third independent route to the same destination:

| route | effective seeds | `charbonneau` |
|---|---|---|
| `min_seed_degree=10` | 1 | 3/3 [8,3,4] |
| `softmax:0.01` | ~1 | 3/3 [8,3,4] |
| ships, equal weights | 3 | 3/3 [7,3,5] |

> **On the hand-read evidence, one well-chosen seed is as good as or better than
> several.** The "seed all the candidates, don't argmax" story that slide 5.4 was
> built on is **not supported**. It rested on the seed-count table (1 → 2 seeds
> = +64%), which was scored against the co-mention proxy later found
> hub-contaminated.

**The resolution-robustness claim survives in a weaker, more honest form.**
`softmax:0.01` on the Sacagawea question selects the **mislabelled
`NativeNation` duplicate** as its single seed and still returns the best result
— because both `SACAGAWEA` nodes lead to the same neighbourhood. So argmax is
safe here not because we hedged across candidates, but because the duplicates
are *structurally equivalent*. That is still a real point about tolerating
imperfect resolution, and it is still a section 4 callback. It is not "seed all
four and let structure sort it out."

**Consequences for the section:**

- Slide **5.4** must be rewritten. "Seed all four" becomes something like
  "pick the best-matching entity, and note that picking the *wrong duplicate*
  costs you nothing because it lands in the same neighbourhood."
- The Sacagawea two-node screen still works, for the weaker claim.
- `min_seed_degree` and the bias-sharpening knob are both routes to the same
  end; **sharpening is the better one** because it does not risk emptying the
  seed set and it needs no threshold tuned per corpus.

**Caveat, unchanged and load-bearing: n = 4 hand-judged passages.** Every number
in 5d-bis, 5d-ter and 5d-quater is a direction, not a verdict. What would settle
them is a wider hand read over the `kind: connection` questions, which is also
what would let the earlier sweeps be re-scored honestly.

##### 5d-quinquies. ⚠️ THE TUNING FINDINGS ABOVE MEASURE NOISE — read this first

Nathan pushed on "five different bias schemes giving identical output can't be
right." He was right, and running it down invalidated my own last three
conclusions. **Read this before believing 5d-bis, 5d-ter or 5d-quater.**

**First, the small correction.** Bias *is* applied under `inverse_degree` —
`[1,0,0]` vs `[0,0,1]` differ by 6.17e-01, and 4 of the top-20 slots change
across bias schemes. "Sharpening is inert under `inverse_degree`" is
**withdrawn**; it was never inert.

**Then the real problem.** The four hand-judged passages sit at entity
percentile **0.97–0.999 under every configuration tested**:

```
1805-03-18   cosine rank 21   entity pct 0.9832..0.9842   final ranks [7, 8, 8]
1804-12-18   cosine rank 15   entity pct 0.9969..0.9990   final ranks [3, 3, 3]
1805-08-25   cosine rank 22   entity pct 0.9952..0.9983   final ranks [5, 4, 4]
1804-11-04   cosine rank 22   entity pct 0.9715..0.9787   final ranks [8, 7, 5]
```

They are **pinned at the ceiling of the entity ranking.** Varying the seed
weighting moves a percentile from 0.983 to 0.984, which shifts the blended score
by `0.2 × 0.001`. Their final position is then decided by cosine, which does not
change. The metric cannot see entity-side tuning.

**And the metric was binary.** "In top-8", on four passages whose ranks cluster
around 8. A one-position drift flips the count:

| finding | what I claimed | what it rests on |
|---|---|---|
| 5d-bis | `idf_over_entities` helps (Nov-4: 8 → 3) | a 5-position move on a saturated metric — the largest seen, still not distinguishable from noise at n=4 |
| 5d-ter | filtering at 3–5 makes `charbonneau-role` **worse**, 3/3 → 2/3 | **one passage moving rank 8 → 9**, crossing an arbitrary threshold |
| 5d-quater | one seed as good as or better than several | [7,3,5] vs [8,3,4] — *identical rank sum* |

**So `5d-ter`'s headline is a threshold artifact**, and slide 5.4 does **not**
need rewriting on that basis. The "seed all the candidates" claim is
*unsupported*, not *refuted* — there is no evidence either way.

##### What survives, and it is the part that matters

**The entity signal is load-bearing, and that is measured on a sensitive
comparison** — deleting it entirely, rather than perturbing it:

| question | with entity signal | entity signal removed |
|---|---|---|
| `charbonneau-role` | [7, 3, 5] | **[14, 10, 11]** |
| `sacagawea-interpreting` | [8] | **[11]** |

Roughly **seven rank positions** on the charbonneau passages. That is a large,
robust effect, and it is the whole basis of the section's claim. It is not in
doubt.

Also surviving, because none of it depends on the blended-rank metric:

- **The hand read itself** (finding 5d) — 4 of 16 promotions clear the bar. A
  judgement about passage content, not a ranking measurement.
- **Degree-1 seeds concentrate their mass** (5d-ter's mechanism) — measured
  directly on mass shares, exact: `1806-05-10` took 99.9% of its score from one
  degree-1 seed.
- **A weight that is a function of the entity alone cancels in that entity's
  outflow** (5d-bis's mechanism) — measured on mass, not rank.
- **Additivity is a conjunction bonus** — measured over 9 to 190 chunks per
  group, not four.
- **The seeder returns `WISDOM RIVER` and `SAGITTARIA LATIFOLIA` for a Sacagawea
  question** — an observation, and the most useful thing in this whole thread.

##### The methodological rule, and it is a slide

> **A binary threshold on a handful of items amplifies noise into findings.** I
> made this error four times in one sitting, having already retracted a *different*
> metric for a *different* reason on the same section. The mechanisms I measured
> on mass and on hundreds of chunks all held; every conclusion I drew from
> "how many of four passages are in the top-8" was noise.

**What would make tuning measurable**: many more hand-judged passages, *and*
mean rank rather than a top-k threshold, *and* — because the judged passages
saturate the entity percentile — a target measured on the entity component
directly rather than through a blend that cosine dominates.

**Until then**: `MENTION_WEIGHT`, `min_seed_degree` and bias sharpening are all
implemented, documented, and **not tuned**. Defaults stay where they are.
Nobody should read the tables in 5d-bis through 5d-quater as showing one setting
beats another.

##### What section 5 can honestly claim, after all this

Not conjunction. Not "better chunks". This:

> **Cosine retrieves the topic. Entity-seeded PPR retrieves the entity.** When a
> question is about a specific thing and cosine's vocabulary match drags in the
> wrong ones, seeding the entity fixes it — *provided extraction attached that
> entity to the passage.*

With three measured limits stated on stage, not hidden:

| limit | evidence |
|---|---|
| no conjunction | linearity; SUM and MIN both 0/8 (this finding) |
| no enumeration or ordering | 3/18 for every graph variant (finding 5c) |
| bounded by extraction | the Aug 18 passage has no horse (this finding) |

Which is what makes the multi-tool argument **structural** rather than
empirical: three retrieval modes, three different things they cannot do.

#### 5e. Co-typed entity substitution — the mechanism, and the analogy that carries it

This is the section's claim stated as a mechanism, and it is the part an
audience can take home to a corpus that has nothing to do with Lewis and Clark.

**The measurement.** For *"What was Toussaint Charbonneau's role on the
expedition?"*:

| | passages | median cosine rank | in top-8 |
|---|---|---|---|
| mention **Charbonneau** (the entity) | 62 | **296** | **2** |
| interpreter vocabulary, **not** him | 108 | 578 | 2 |
| neither | 2,743 | 1,524 | 4 |

Cosine's top-8, tagged:

```
1. CHARBONNEAU        Chabono
2. neither            Duriaur          <- a Sioux go-between
3. neither            -                <- arrival at St. Charles
4. interpreter vocab  Dourion          <- the Sioux interpreter
5. CHARBONNEAU        Charbono
6. interpreter vocab  Durion, Gravelin <- Sioux + Ricara interpreters
7. neither            -                <- a Minetarree chief's visit
8. neither            Gravline         <- the barge pilot
```

**Four of eight slots go to other French-speaking go-betweens on the same
expedition.** Two more are diplomatic encounters naming no interpreter at all.
Sixty of his sixty-two passages sit outside the window.

*(Note for anyone re-running this: a naive `CONTAINS 'interpret'` filter is
wrong on this corpus. The journals spell it `interpeter`, `enterpreter`,
`inturpeter`, `interpter`, `interptr`, `interpetr`. Nineteenth-century
orthography defeated my first version of this table.)*

**The mechanism.** A whole-passage embedding is an **average over ~300 words**.
The question encodes roughly `{interpreter, role, expedition, a French
surname}`. In a passage about Dorion negotiating with the Sioux, the
role-and-diplomacy vocabulary — *interpreter, chief, speech, presents, nation* —
recurs and dominates that average, while a name appearing once contributes a
sliver. So the passage that *is* about Charbonneau, whose name shows up once
between a weather note and a hunting tally, sits **further** from the query
centroid than a passage about a different interpreter doing interpreter things.

Cosine cannot make identity a **hard** constraint. In a continuous similarity
space "Dorion the Sioux interpreter" is genuinely near "Charbonneau the
interpreter" — they differ by one low-mass token and agree on everything else.
That is not a defect in the embedding; it is what averaging does.

> **Name it: co-typed entity substitution.** Cosine answers *"an interpreter"*
> when you asked about *"this interpreter."*

**Why the entity layer fixes it.** `MENTIONED_IN` is a **discrete** edge —
either extraction attached the entity or it did not. No averaging, so identity
is binary: the hard constraint cosine can only express softly. Same thing the
granularity measurement pointed at (median 60 words per entity in a 325-word
passage): **the entity is a pointer, the embedding is an average.**

**What it predicts — this is what makes the claim useful rather than anecdotal:**

| | |
|---|---|
| **helps** | the question turns on a specific entity, and the corpus holds several of the same type |
| **does not help** | no discriminating entity to seed — `illness-and-injury` is a category, not a thing |
| **does not help** | only one entity of that type exists, so cosine has nothing to substitute — which is exactly why `prairie-dog` is a `control` question |

> **The technique earns its place in proportion to how many same-type entities
> your corpus contains.**

##### The analogy for the stage — and get the mapping right

Nathan's, adjusted. The first version — *"forty engineers, five of them named
Chen"* — is **section 4's** problem, not section 5's. There is no name collision
in the Charbonneau case; cosine returned Dorion and Gravelin, different names,
same job. So:

> **Section 5.** Your corpus has forty engineers. You ask what **Chen** owns.
> Cosine hands you three passages about **Rodriguez** owning a similar service —
> because *"engineer owns service"* is most of the sentence and *"Chen"* is one
> word of it.

> **Section 4** (callback, same imagined corpus). And five of those forty
> engineers are named Chen.

One company, two different failures, one per section. That pairing is stronger
than either analogy alone, and it gives section 10 its spine for free.

#### 5f. The decomposed seeder — 5d-ter's conclusion, built and measured (2026-09-07)

5d-ter ended with "the leverage is in seed selection, and doing that properly
means *naming* the entities the question is about." Built, in
`graphrank/decompose.py`: an LLM extracts a typed manifest of the entities the
question explicitly names (cached on disk per model+prompt+question), and each
mention resolves by name — per-label **full-text** index for proper nouns,
per-label **vector** index for species/events, exact-name twins under other
labels unioned back in. It is the corps repo's text2cypher param-resolution
pattern minus the argmax: every strong match seeds. Select with
`ExpandConfig(entity_seeder="decomposed")` or `demo_pagerank.py --seeder
decomposed`; default remains `semantic` (no LLM in the retrieval path).

**The diagnosis that motivated it, measured on the live graph.** Why does the
semantic seeder return WISDOM RIVER for a Sacagawea question? Three effects:

1. **Boilerplate floor.** Every `embeddingDescription` shares the template
   suffix ("… documented in the Lewis and Clark Expedition journals"). The bare
   template alone matches the sacagawea-interpreting question at raw cosine
   0.288; WISDOM RIVER's full description at 0.383 — the shared boilerplate is
   ~75% of the match. Any entity clears ~0.65 on the index scale against any
   expedition-flavoured question.
2. **Alias dilution.** "Sacagawea" alone matches the question at raw cosine
   0.664; the full description with eight alias spellings averaged in matches
   at 0.553. The alias list *lowers* the canonical-name match — and it is why
   the mislabelled NativeNation duplicate (one alias) outranks the real Person
   node (eight): 0.7998 vs 0.7764. That is the mechanism behind 5.4's demo
   picking the duplicate first.
3. **Scale optics.** Neo4j vector indexes report `(1+cosine)/2`, so raw
   0.38-vs-0.55 reads as 0.69-vs-0.78. Relatedly, `proportional` seed
   weighting operates on the compressed scale — flatter even than finding #5
   measured.

Full-text lookup bypasses 1 and 3 and inverts 2 (each alias is a separate
field to hit). Lucene brings its own quirks, both handled: no stemming
("horses" ≠ HORSE — de-pluralised tokens are appended to the query), and
field-length norms bury a 32-alias species under short-named Supply junk
(species route to vector indexes instead, same routing the corps agent chose).

**The measurement — `scripts/measure_seeds.py`, and why it is exempt from
5d-quinquies.** Seed selection is exact set membership against what the
question's *text names* (an accept-set per phrase, hand-resolved against the
live graph; checkable by reading one line). No relevance proxy, no rank
threshold. Over the 13-question bank:

| seeder | named-entity coverage | seeds outside named∪gold |
|---|---|---|
| semantic | 8/11 | 29 |
| **decomposed** | **10/11** | 22 |

Highlights, worth more than the totals:

- `shoshone-horses`: semantic 0/2 (it seeds PURCHASE OF HORSES, df 2, and two
  df-1 Events); decomposed 2/2 — SHOSHONE (df 192) + Supply HORSE (df 37).
- `charbonneau-role`: one seed, TOUSSAINT CHARBONNEAU, weight 1.0. The two
  degree-1 spike seeds from 5d-ter are simply gone.
- Both SACAGAWEA duplicates still seed (0.5 each) via the exact-name twin
  union — section 4's "you don't have to fix your entities first" survives
  by identity evidence rather than by accident.
- `keelboat-return`: MISSOURI RIVER (df 307) finally seeds; "the keelboat"
  resolves to nothing because **no keelboat entity exists** — limit #3
  surfacing at the seeder, correctly reported rather than papered over.
- Thematic questions (`trade-goods`, `food-sources`, `illness-and-injury`)
  parse to zero mentions and **fall back to the semantic seeder** by design —
  a category question has no name to look up.
- The one decomposed miss, `great-falls-portage`, is a corpus truth: there is
  no GREAT FALLS place node. The biggest episode of the expedition exists as a
  df-3 WaterBody (FALLS OF MISSOURI) and a df-2 Event. The semantic seeder's
  "hit" there is the df-2 Event decoy — hollow either way. Finding #10's
  gold-set audit applies to places too.

**Retrieval effect: none measurable, as expected.** The four hand-read
passages stay in the top-8 under both seeders (charbonneau [7,3,5] semantic vs
[8,3,4] decomposed — the same rank-sum wash 5d-quater measured for
single-seed; Nov-4 moves 8 → 7). Observation, not verdict — n=4, saturated
metric, per 5d-quinquies. The measurable claim is "the seeds are now the
question's entities," not "the answers got better."

**Costs, stated plainly.** An LLM parse enters the retrieval path: ~0.8-2s
uncached, ~0 cached (the cache also pins the parse, so demo behaviour is
frozen after first run — parse variance was observed across prompt revisions
before caching). Known rough edges, all visible in `--show-seeds` and all
untuned by policy: PRAIRIE BIRD rides along with CYNOMYS at a 0.001 vector
near-tie no constant margin can exclude; FORT MANDAN token-matches "Fort
Clatsop" at the 0.5 full-text keep-ratio; Person SERGEANT (df 1) rides with
CHARLES FLOYD. Legible failures — a name you can read on screen — where the
semantic seeder's were not.

**Two refinements after review (same day).** Measured effect: named coverage
unchanged at 10/11, extras 22 → 19, hand-read ranks unchanged.

1. **Name-twins split their mention's share by degree, not evenly** — and this
   is arithmetic, not a heuristic: duplicates with degrees d1, d2 weighted
   ∝ d1, d2 put ``share/(d1+d2)`` on each of their chunks, exactly what one
   *merged* node of degree d1+d2 would do. Seeding unresolved duplicates
   df-proportionally **behaves as if you had resolved them**, to first hop.
   That upgrades section 4's callback from "seeding the duplicate happens to
   be fine" to an identity. (The even split had handed the df-1 mislabelled
   SHOSHONE twin half the unit — a 5d-ter spike by construction; it now gets
   0.5%.) Distinct-name candidates still split by match score: different
   names are different guesses, and degree is not evidence there.
2. **Full-text resolves all-tokens-AND first, OR fallback.** ``+(sergeant)
   +(floyd)`` returns CHARLES FLOYD alone (an alias carries the rank);
   ``+(fort) +(clatsop)`` returns exactly CLATSOP VILLAGE — extraction stored
   "Fort Clatsop" as its alias, so the AND query finds the right node
   *precisely because* aliases are separate token fields. The OR fallback
   fires only when no node carries the full name — the extraction-gap case,
   where nearest-name nomination is the correct behaviour.

**The question audition (same day) — one added, one retracted, two mechanisms.**

Four new questions were engineered to be PPR-wins-over-both (identity
constraint + no role-bearing edges + passage count ≫ k), screened by exact
membership counts, then **judged by reading both windows in full** — and the
reading overturned half of what the counts said, again.

- **`ordway-responsibilities` — added to the bank.** 74 passages, median
  cosine rank 95; vector top-8 holds him in 5 slots (rest: no-name sergeant
  duty orders, a Cameahwait scene); PPR fills 8/8. Two promotions clear the
  5d bar with content no cosine passage had: the 1804-05-17 order where
  Ordway convenes a court martial in the captains' behalf, and the 1804-05-26
  detachment order giving his squad the batteaux crew. Cypher side: 102 edges
  of diary noise, 74 unrankable passages.
- **`cameahwait-horses` — rejected, after I had proposed it for the demo.**
  The counts looked favourable (vector 3/8, median 127, wrong slots all Nez
  Perce horse-trading — a perfect co-typed substitution setup). Reading the
  windows showed PPR **drops the corpus's best passage** (Aug-14, Lewis asks
  Cameahwait to mobilise his village and 30 spare horses — cosine's #1,
  absent from PPR's top-14) and imports the rival April-1806 cluster.
- **Mechanism worth keeping, maybe worth stage time: the passage-seed half of
  the structural signal is cosine wearing a graph costume.** `expand` seeds
  one PPR run from the cosine top-5; on this question 3 of those 5 are the
  wrong nation, so the structural signal *amplifies* the substitution instead
  of correcting it. The entity signal can't outvote it: the "horses" mention
  resolved to the Supply HORSE group, which attaches to every nation's horse
  trading. When cosine is wrong, half the graph signal is wrong with it, by
  construction.
- **Recipe boundary, from the two that failed the audition** (York: vector
  already 5/8; Twisted Hair: 6/8): a named entity is not enough. It takes
  shared same-type vocabulary AND buried passages (median ≫ k). A
  distinctive name atop a dominant cluster is the `prairie-dog` control
  lesson at the Person label.

**For the talk:** this is the "where the leverage actually is" beat (5.10/5.12
or the bridge to the agent ending), one line: *the entity seeder is itself a
retrieval step with cosine's disease, and the cure is the one you already know
— name the entity, then look it up by name.* Same pattern as last year's
text2cypher param resolution, which makes it a cross-talk callback for anyone
who saw the community-days demo. The df-proportional twin split is a candidate
one-liner for 5.4: *seeding both SACAGAWEA nodes, weighted by degree, is
mathematically the same walk as having merged them.*

#### 5g. Filter+cosine parity — the cheapest baseline matches PPR on every hand-read case (2026-09-07)

Nathan's question: is PPR better than *prefilter passages to those mentioning a
seeded entity, then rank by cosine*? Measured against the hand-read passages
(membership checks only — no new relevance judgements):

| question | judged passages in filter+cosine top-8 | in PPR top-8 | window overlap |
|---|---|---|---|
| `charbonneau-role` | **3/3** | 3/3 | 7/8 |
| `sacagawea-interpreting` | **1/1** (Nov-4) | 1/1 | 6/8 |
| `ordway-responsibilities` | **2/2** | 2/2 | 7/8 |

**Equivalent on every single-entity case**, and the filter needs no GDS, no
projection, no damping — one Cypher predicate plus the vector index.
Conjunction, PPR's best structural claim, measured as a one-passage edge:
"What did Sacagawea and Charbonneau do together?" puts 4 of the 9 dual-mention
chunks in PPR's top-8 vs 3 for filter+cosine — and a count-matched-entities
tiebreak would trivially close that.

**So the entity *signal* ≈ the entity *filter*.** The 7-rank-positions
delete-test (5d-quinquies) was measuring the value of the identity constraint,
not of the walk. The load-bearing ingredients are build-time extraction with
coreference, and naming the question's entities — PPR was the vehicle.

**One candidate counter-receipt checked and killed.** The hope: the walk
recovers passages the seeder's lookup missed (the CAMEAHWAT misspelling).
Verified false — the promoted Aug-14 passage is tagged under canonical
CAMEAHWAIT too, so the filter would also have included it. No case on this
corpus shows the walk reaching a judged passage the filter excludes.

**Where PPR still earns the extra machinery — with confidence labels:**

1. *Entity-ranking consumers* (real, measured today). Filter+cosine emits no
   entity ranking. Graph expansion, community seeding, subgraph extraction —
   and all of finding #1/5.6's hub work — exist only in walk-land.
2. *Ordinary-extraction corpora* (mechanism solid, not demonstrable here —
   precisely because this extraction is unusually good). Nov-4 is inside the
   filter only because `extract.py` resolved "one of his wives" → SACAGAWEA at
   build time. On an NER-grade graph without coreference, the filter loses
   Nov-4-class passages *categorically*; the walk still reaches them in ≤3
   steps through co-mentions (CHARBONNEAU and SHOSHONE are tagged). Filter
   parity is rented from build-time coreference.
3. *Graded membership* (mechanism real, harm of the binary alternative
   unmeasured). A filter includes a dubious match's passages at full strength
   or not at all; the walk includes the df-1 SHOSHONE twin at 0.5%.
4. *One mechanism instead of accumulating patches* (judgement). Union, dedup,
   conjunction tiebreak, per-entity weights, a hop of reach — each patch on
   filter+sort is a special case of walk parameters.

**Where it loses money, already measured:** the passage-seed half amplifies
cosine's substitution when cosine is wrong (5f, Cameahwait), a failure mode
filter+cosine cannot have.

**Nathan's sharpening, and it is the version that matters: the filter does not
need a graph at all.** Entity tags in any store — a Postgres array column, an
Elasticsearch keyword field, a vector-DB metadata filter — run filter+cosine.
The audience-facing point is *when moving to a graph adds value and when it is
just a headache*. The taxonomy, mapped to the talk's own sections:

| capability | needs |
|---|---|
| single-entity identity questions (this section's headline failure) | **tags in the store you already run** |
| conjunction, most of it | tags + a count-of-matched-tags tiebreak |
| the entity layer itself — extraction, aliases, coreference, resolution | build-time work, storage-agnostic — **this is where the value lives**, and section 4's problem (five Chens) poisons a tag filter exactly as it poisons a seed set |
| reach beyond the tags when extraction is ordinary | the bipartite graph (the walk) |
| communities (§6), path explanations (§7), text2cypher enumeration | **graph only — no tag-store equivalent exists** |
| entity-level outputs (expansion, agent routing) | the graph — a filter consumes entities, it cannot produce them |

Decision rule for the stage: *questions name one entity at a time and your
chunks are well tagged → add a keyword filter and go home early. The graph
starts paying when entities relate to each other in ways your questions
exploit — corroboration, communities, paths, structured queries — or when
extraction can't be trusted to tag everything.* Extends 5.12's existing "one
CEO, one product? save yourself the projection" to "forty engineers but
single-entity questions? save yourself the database."

**Editorial consequence — DECIDED (2026-09-07).** Nathan: 5.12 becomes the
tags-vs.-graph decision rule (drafted in `section-05-slides.md`, take-home
line upgraded to "cosine retrieves the topic, the **entity layer** retrieves
the entity"); **filter parity itself gets no stage time** — it is the Q&A
pocket behind 5.12, with this finding as the receipts. Title still open.
Still to do: thread the same frame through sections 9 and 10 when those
sections are built.

#### 5h. Before giving up on PPR — three candidate mechanisms screened (2026-09-07)

Nathan's framing: 5g's parity plus the editorial decision leaves PPR with less
stage time than the session description promises. Before conceding that, screen
the remaining ways the walk could genuinely win — harder questions, chunk
seeding, richer projections. Screened read-only against `neo4j`, membership
checks only, no new relevance judgements.

**The reframe that governs all of it: after 5g, the bar is not "cosine fails,"
it is "the *filter* fails."** A PPR win now requires a judged-relevant passage
the filter cannot have, or a question the filter cannot run on.

##### 5h-1. The extraction-grade ablation — 5g's claim #2 is demonstrable here after all, and it is the strong candidate

> **Status (2026-09-07, later the same day): built and measured — finding 5i.**
> The screen below stands; the experiment's *hypothesis* (the walk buys the
> passages back at query time) did not hold. Read 5i before quoting anything
> from this subsection's "stage shape" paragraph.

5g called the ordinary-extraction argument "mechanism solid, not demonstrable
here — precisely because this extraction is unusually good." Wrong on the
second half: the corpus records *how good*, edge by edge. New
`scripts/measure_extraction_grade.py` classifies every `MENTIONED_IN` edge by
its textual support in the chunk (whitespace-normalized containment against
the entity's recorded surface forms):

| support class | edges | share |
|---|---|---|
| name-backed (canonical or name-like alias in text) | 9,541 | 64.5% |
| surface-only (only a descriptive alias — "the squaw", "This River") | 3,465 | 23.4% |
| **no surface form at all — pure build-time inference** | **1,793** | **12.1%** |

Per label, pure inference: Person **7.8%**, Event 66.5%, species 22–25%
(inflated by the Latin renaming — strict NER tags no common nouns, so
arguably honest, but quote the proper-noun labels), NativeNation 0.8%.
Contamination runs both ways: gazetteer gaps inflate it (a chunk says
"shabono" but only "Toust. Shabono" is filed, so containment misses — a
recording gap, not coreference), and surface-only deflates it (linking "the
squaw" *was* build-time coreference). ~12% is a size class, not a constant.

**The receipt that makes it a demo:** SACAGAWEA has **21 chunks with no
surface form of any of her 21 recorded forms** — and they include exactly the
passages the hand reads crowned: **Nov-4** (5d's best single instance),
**Jun-16** ("her pulse were scarcely perceptible" — her fever, never names
her), and **Aug-14** (the Cameahwait mobilisation passage 5f judged the
corpus's best). The filter owns these passages only because `extract.py`
resolved pronouns at build time. Charbonneau has 10 such chunks, Ordway 2.

**The experiment (not yet built):** project an ablated mentions graph keeping
only name-backed edges — a simulation of ordinary NER-grade extraction — and
run filter+cosine vs entity-seeded PPR on it, endpoints = the existing
hand-read passages. The filter loses the coref-only judged passages *by
construction*; the measurement is whether the walk still reaches them (Nov-4
names Chabonah and the Snake nation, so `SACAGAWEA → her named chunks →
CHARBONNEAU/SHOSHONE → Nov-4` survives ablation — the question is its rank).
Second arm: add `NEXT_CHUNK` to the *ablated* graph only. Pronoun antecedents
live in the preceding chunk, so the sequence edge becomes a **query-time
coreference patch** — a mechanistic job NEXT_CHUNK never had in 5c, and 5c's
verdict on sequence questions stands regardless.

**Stage shape if it holds:** *"your graph is probably not this good — degrade
it to what standard extraction gives you, and the filter goes blind to the
best passages in the corpus; the walk buys them back at query time."* PPR
becomes insurance against extraction quality. That inverts 5g without
contradicting it: on a great graph, tags suffice; on the graph you actually
have, the walk earns rent. It also completes the section's arc — 5.12's "the
entity layer retrieves the entity" keeps its headline, and PPR is what you
run when the entity layer is ordinary.

##### 5h-2. Chunk seeding — exists already; two variants untested

The passage half of `expand` *is* chunk seeding, and 5f measured it as a
liability when cosine is wrong (Cameahwait: 3 of 5 seeds were the wrong
nation). Untested variants: **(a)** identity-constrained passage seeds — seed
the walk from filter+cosine's top instead of raw cosine's, killing the
amplification by construction; **(b)** thematic questions (`trade-goods`,
`food-sources`, `illness-and-injury`) — the decomposed seeder parses zero
mentions, so **no filter can run at all**, and finding 4 measured cosine's
failure (trade-goods: best conjunction rank 166, median 724, 0 in top-8).
Passage-seeded PPR is entity-based query expansion — hop from cosine's top
chunks to their rare entities (the awls and the blue beads) to the passages
sharing them, vocabulary-free. The one tool that even applies. Cost: judging
it means fresh hand reads; every old blend number is proxy-contaminated.

##### 5h-3. Richer projections — screened weak, except inside 5h-1

Entity–entity `RELATED` edges: the extracted types are event-ish (OBSERVED
2,911, ACQUIRED_PROVISION 962, MET_WITH 953…), and the relationship a
neighborhood question would ride does not exist — **no SACAGAWEA–CAMEAHWAIT
edge of any type**. The projection docstring's semantics objection stands.
`NEXT_CHUNK`: 5c's no-effect verdict on sequence questions stands; its one
live prospect is the ablated-graph coreference patch above.

##### 5h-4. Harder questions, under the new bar

Two classes clear "the filter fails": **(i)** identity questions on
ordinary-extraction graphs — 5h-1 covers this with the existing question bank,
no new questions needed; **(ii)** neighborhood questions ("what do we know
about Sacagawea's brother?") where the nameable seed is X but answers live in
passages mentioning only the related Y — CAMEAHWAIT has 10 chunks without
SACAGAWEA. Candidate only: those 10 are unread, and connection-explanation is
partly §7's business.

**Recommendation:** build 5h-1 first. It reuses every hand-read endpoint, it
is a delete-test on mass (the discipline that has held all week), and it is
the one mechanism that restores PPR to the stage time the session description
promises — as the query-time complement to §4's build-time entity layer,
which is the talk's own thesis anyway.

##### 5h-5. The framing — Nathan's, APPROVED as the section's story (2026-09-07)

Nathan, on when PPR actually paid off for him: *a huge, diverse corpus, no
time to develop an ontology, and an extraction prompt that just said "find me
interesting stuff."* That experience is the frame the section has been
missing, and it inverts the ablation from a degradation exercise into the
audience's reality: **the ablated graph isn't a worst case, it's the graph
most people have.**

The two paths, as the section should draw them:

| | the §4 path (gold-plated) | the §5 path (budget) |
|---|---|---|
| build time | careful extraction, coreference, resolution, taxonomy, governance | cheap prompt, no resolution pass, ship it |
| query time | tag filter + cosine — go home early | entity-seeded PPR compensates |
| duplicates | merged at build time | seed all twins df-proportionally — **measured identical to the merged walk** (5f refinement, an identity) |
| coreference gaps | resolved at build time ("one of his wives" → SACAGAWEA) | the walk bridges via co-mentions / adjacency — **measured in 5i: reachability survives, rank does not; this leg FAILED** |
| hubs, no ontology | curated / renamed at build time | IDF weight damps them automatically — **measured, finding 2** (4.53/8 → 0.60/8) |

Three legs; two already measured, one pending. **"About as good and less work
up front" is the hypothesis 5h-1 tests, not yet a slide line** — per the
measurement discipline, the phrase stays off slides until the ablated-graph
ranks exist. *(The ranks now exist — finding 5i — and they refuse the phrase:
the third leg failed for coreference-heavy entities. The stage shape below is
kept for history but is superseded by 5i's closing paragraph.)* And the bound gets stated on stage: the walk only buys back
edges that exist *somewhere in the neighborhood*. It cannot recover what
cheap extraction never tagged at all (limit #3's horse passage), and the
6.1% of chunks with zero entities stay unreachable at any damping. Build-time
work is the only fix for those — that is what keeps the two paths a real
trade instead of a sales pitch.

Stage shape, revised from 5h-1's: *"Section 4 showed you the gold-plated
entity layer. Here is the confession: you usually don't have time for that. I
didn't — my best PPR results came from a corpus where the extraction prompt
was 'find me interesting stuff.' So skip the governance, take the cheap
graph, and let the walk pay the rent at query time: duplicates seed as if you
had merged them, missing coreference gets bridged through co-mentions, and
the IDF weight does the hub curation you never did."* The personal anecdote
opens the beat — it is the "problem the audience has felt" this section's
opening has needed.

#### 5i. The extraction-grade ablation, run — the walk keeps the passages *reachable*, not *ranked* (2026-09-07)

5h-1's experiment, built (`scripts/measure_ablation.py`) and measured. Design
as specified there: keep only the **name-backed** `MENTIONED_IN` edges
(classification imported from `measure_extraction_grade.py`, not
reimplemented), project `lc-mentions-ablated` (IDF reweighted on the ablated
degrees — an ordinary extraction would compute IDF from its own edges) plus a
`+NEXT_CHUNK` variant, seed with the decomposed seeder, and measure the
**corpus-wide rank** of every already-hand-read endpoint under pure
entity-seeded PPR — ranks, never top-k membership, per 5d-quinquies. Read-only
throughout; `lc-mentions` and `lc-retrieval` untouched.

**Hand verification before measurement, one surprise kept.** The three
SACAGAWEA receipts (Nov-4, Jun-16 fever, Aug-14) classify `inference` and drop,
and CHARBONNEAU→Nov-4 is name-backed and survives — as 5h-1 predicted. But
**SHOSHONE→Nov-4 is `surface-only` and drops**: "Snake Indians"/"Snake" are
filed aliases and present in the text, yet they are *exonyms* — no string
kinship with SHOSHONE (JW 0.58) — so `name_like` classes them descriptive.
5h-1's "Nov-4 names Chabonah and the Snake nation" was right about the text
and wrong about the classifier. Kept as-is deliberately: a real NER+gazetteer
might well link the exonym, so dropping it makes the walk's job strictly
harder, and any recovery is the conservative reading. Nov-4's surviving route
is through CHARBONNEAU alone.

**The result that reframes the experiment: ablation is not uniform.** Corpus
mass first: 9,541 of 14,799 edges kept (64.5%, matching 5h-1's classifier
run); chunks with zero entity edges grow 179 → 387 (6.1% → 13.3%). But
per seed entity:

| seed | edges kept | share |
|---|---|---|
| JOHN ORDWAY | 72 / 74 | 97% |
| TOUSSAINT CHARBONNEAU | 52 / 62 | 84% |
| **SACAGAWEA** | **6 / 64** | **9%** |

The journals almost never name her. A regex sweep over all 2,913 chunk texts
for every plausible spelling (sah/sar + cah/kah + gar/gah…, sacaja…, janey)
finds **12 chunks in the whole corpus that name Sacagawea at all** — 6 are the
classifier's name-backed set, 5 more carry edges the classifier drops on
gazetteer/`name_like` gaps (audit table in the script), 2 have no edge at all.
Cheap extraction does not degrade this graph evenly: it specifically deletes
the person who exists in the text as "the squaw", "the Indian woman", "one of
his wives". **The entity the demo question is about is the entity NER-grade
extraction can barely see** — 64 chunks of build-time identity resting on ~12
namings.

**The measurement.** Controls = endpoints whose seed edge is name-backed (they
survive ablation; they exist to show the instrument sees what was varied).
Tests = the three SACAGAWEA coref-only passages. Ranks are corpus-wide
(2,913) under pure entity-seeded PPR:

| endpoint (controls) | filter+cosine, ablated | PPR full | ablated | +NEXT |
|---|---|---|---|---|
| charbonneau 1805-03-18 hiring | in filter, rank 5/52 | 47 | 40 | 37 |
| charbonneau 1804-12-18 language | in filter, 3/52 | 4 | 1 | 4 |
| charbonneau 1805-08-25 judgement | in filter, 6/52 | 6 | 6 | 8 |
| ordway 1804-05-17 court martial | in filter, 52/72 | 19 | 18 | 17 |
| ordway 1804-05-26 detachment | in filter, 7/72 | 21 | 25 | 26 |

| endpoint (tests) | filter+cosine, ablated | PPR full | ablated | +NEXT | ablated, generous |
|---|---|---|---|---|---|
| Nov-4 "one of his wives" | **LOST by construction** | 58 | 114 | 118 | 165 |
| Jun-16 her fever | **LOST** | 11 | 480 | 566 | 706 |
| Aug-14 Cameahwait | **LOST** | 62 | 1108 | 779 | 844 |

Controls barely move — ±7 rank positions across both graphs, the delete-test
seeing exactly what was deleted. Tests fall off a cliff.

**Verdict, one per arm:**

1. **Filter+cosine goes blind, categorically.** As constructed — this arm is
   the control for 5h-5's claim, and the claim's first half holds: no tag, no
   passage, at any k.
2. **The walk does NOT buy them back.** It keeps all three *reachable* — the
   predicted route is real (SACAGAWEA → her named Aug-17/19 chunks →
   CHARBONNEAU → Nov-4, verified edge by edge) — but at ranks 114–1108, not
   in any context window anyone ships. The mechanism is the non-uniformity
   above: ablation didn't just delete the filter's view of these passages, it
   deleted 58 of the seed's own 64 edges, so the walk starts nearly blind
   too. **"About as good and less work up front" is unsupported by these
   numbers and stays off slides** — not as a hedge but as a measured result:
   for a coreference-heavy entity, the walk degrades from rank ~11–62 to rank
   ~114–1108 exactly where the filter degrades to nothing.
3. **NEXT_CHUNK is not a coreference patch on this corpus, and the premise is
   why.** The antecedent is *not* in the preceding chunk: the nearest chunk
   naming Sacagawea sits **169 NEXT_CHUNK hops** from the Jun-16 fever
   passage, 14 from Aug-14, and beyond 500 from Nov-4. The journals' persistent
   referent ("the squaw") spans months — coreference here is corpus-scale, not
   sentence-scale — so at damping 0.45 the sequence edge carries nothing, and
   adding it *hurts* two of three tests (114→118, 480→566: pure mass
   dilution). 5c's no-effect verdict on NEXT_CHUNK now extends to the one
   mechanistic job 5h-1 had reserved for it. *(Corrected in 5j-bis: on the
   real budget graph the adjacent chunks DO carry the antecedent — as
   role-phrase shard tags the gold graph had merged away, so this ablation
   could never see them. Adjacency pays only when those shards are seeded,
   and only to ~rank 50.)*

**Sensitivity (the classifier's contamination, quantified rather than
waved at).** `--generous` restores the 5 hand-audited gazetteer-gap edges
(SACAGAWEA df 6 → 11, the honest ceiling for what any NER gazetteer could
tag): test ranks 165 / 706 / 844. Individual endpoints wiggle in both
directions — more surviving Sacagawea chunks spread the seed mass wider, so
Nov-4 actually *drops* — but the conclusion is identical at both gazetteer
grades. Not a classifier artifact.

**What this does to 5h-5's frame.** Two legs stand measured (duplicates seed
as if merged — 5f's identity; IDF damps hubs — finding 2). The third leg is
now measured and **the budget path does not cover coreference.** What survives
for the walk, stated honestly:

- *Graceful vs. categorical failure.* The filter loses coref-only passages
  absolutely; the walk keeps them at nonzero score, findable by a consumer
  that looks past top-8 (agentic retrieval, entity expansion, §7 paths). Real,
  but a different claim than "compensates at query time".
- *Everything name-backed keeps working.* Controls held within a few
  positions; on the 84–97% of edges ordinary extraction does produce, the
  machinery is fine.
- The bound, which now has teeth: the walk cannot recover never-tagged
  passages (limit #3's horse), and the zero-entity floor doubles under
  ablation (6.1% → 13.3% of chunks unreachable at any damping).

For the person the corpus names ~12 times and refers to hundreds of times by
role, **build-time coreference is the only thing that pays — section 4's
thesis landing in section 5 with numbers.** Stage consequence is Nathan's
call, but the honest beat now reads: *the walk covers your duplicates and
your hubs; it does not cover your pronouns.* The Sacagawea coverage number —
6 name-backed chunks out of 64 — is itself the most quotable artifact this
experiment produced: the demo corpus's most important person is nearly
invisible to the extraction grade most teams run.

*(Observation parked, not concluded: the ordway court-martial control sits at
filter+cosine rank 52/72 — legal-orders vocabulary, cosine's known blind spot
— while the ablated walk ranks it 18. One instance, n=1, noted here so nobody
re-derives it as a finding.)*

*(Same day: Nathan pointed out the simulation undersells the real thing —
see 5j, which reruns the measurement on an actual budget extraction and
confirms this finding harder.)*

#### 5j. The budget graph for real — `rawluna` replaces the simulation, and it is harsher (2026-09-07)

Nathan's correction to 5i's design: the graph most teams have is not NER
output — it is a modern-LLM extraction with no resolution pass, and the
project already owns one. `rawluna` is the gpt-5.6-luna extraction, frozen
for section 4's measurements. New database **`budgetluna`** = a copy of it
(dump/load; `rawluna` untouched and now checkpointed at
`../rawluna-2026-09-07T17-12-30.dump`) plus the query-side indexes the
machinery needs and nothing else: the corps repo's full-text index statements
verbatim, and `embed_entities.py` run from a patched copy that targets the
database explicitly (the home-database gotcha) — 3,669 entities embedded,
per-label vector indexes created, **resolution pass skipped**. Chunk ids and
chunk embeddings are identical to the demo corpus, so every hand-read
endpoint carries over unchanged.

`scripts/measure_budget_graph.py` measures whatever database is configured,
as it stands — no ablation, the graph *is* the condition. Validation: run
against `neo4j` it reproduces 5i's full-graph reference column exactly
(47/4/6, 58/11/62, 19/21).

**What "no resolution pass" actually looks like — and it is not missing
edges.** The luna extractor resolves pronouns within its context window, but
where the journals never name the person it mints **vague nodes**: Nov-4's
coreference is a Person literally named `ONE OF HIS WIVES`; Aug-14 carries
`HIS WOMAN` and `OUR INTERPRETER`; the fever passage tags no person at all
except Clark. Identity shatter, measured over gold-SACAGAWEA's 64 chunks
(cross-database join on chunkId, keyword-generous so every count favors the
budget graph):

| where the 64 chunks went in `budgetluna` | chunks |
|---|---|
| SACAGAWEA (the node the seeder can find) | 8 |
| INDIAN WOMAN | 10 |
| 17 further shards — THE INDIAN WOMAN, SQUAR, HIS WIFE, ONE OF HIS WIVES, JANEY, SAHKAHGAR WE, … | 1–3 each |
| **no plausible her-referent Person at all** | **25** |

The named men are fine — CHARBONNEAU df 55 (gold 62), ORDWAY df 79 (gold 74).
Budget extraction is only cheap for people the text names.

**The extraction-grade classifier cannot see this failure — it scores the
budget graph as *better*.** `measure_extraction_grade.py` on `budgetluna`:
**75.1% name-backed, 3.6% inference** (gold graph: 64.5% / 12.1%). Of course
it does: instead of resolving "the Indian woman" to SACAGAWEA (an edge with no
name support), the budget extractor minted a node *named* THE INDIAN WOMAN,
whose edge is trivially name-backed. Fragmentation moves the defect from
edges to nodes, and edge-support classification is blind to nodes. 5h-1's
"~12% is a size class" caveat gets a sharper sibling: **an edge-support
quality metric can improve as the extraction gets worse.**

**The seeder finds one shard.** "Sacagawea" resolves by full-text to
SACAGAWEA (df 8) alone. 5f's exact-name twin union — the mechanism that made
duplicates seed as if merged — cannot fire here, because a real budget
graph's duplicates are *spelling variants and descriptions*, not exact-name
twins. That leg of 5h-5's table quietly assumed the duplicates section 4's
pipeline produces; the duplicates a cheap pipeline produces are a harder
class.

**Results** (same endpoints, same machinery as 5i; ranks corpus-wide under
pure entity-seeded PPR):

| endpoint (controls) | filter+cosine | PPR | +NEXT |
|---|---|---|---|
| charbonneau 1805-03-18 hiring | in filter, 6/55 | 2 | 1 |
| charbonneau 1804-12-18 language | in filter, 4/55 | 6 | 8 |
| charbonneau 1805-08-25 judgement | in filter, 5/55 | 47 | 48 |
| ordway 1804-05-17 court martial | in filter, 54/79 | 23 | 18 |
| ordway 1804-05-26 detachment | in filter, 7/79 | 6 | 8 |

| endpoint (tests) | filter+cosine | gold PPR | budget PPR | +NEXT | 5i ablated |
|---|---|---|---|---|---|
| Nov-4 "one of his wives" | **LOST — no tag** | 58 | 75 | 90 | 114 |
| Jun-16 her fever | **LOST** | 11 | **1709** | 1769 | 480 |
| Aug-14 Cameahwait | **LOST** | 62 | **1475** | 1154 | 1108 |

Nov-4 is the exception that proves the mechanism: CHARBONNEAU is tagged on it
*and* on two of her eight chunks (Aug-17/19), so the three-step bridge exists
and delivers rank 75 — the walk's honest best case, reachable but not
shippable. The fever and Aug-14 passages land **worse than the simulation**
(1709/1475 vs 480/1108), because 5i's ablation still walked the gold node
set with edges removed, while the real budget graph's identity shards do not
connect to the seed at all. NEXT_CHUNK: still no coreference patch — worse on
two of three, same as 5i.

**Verdict.** The real budget graph confirms 5i and hardens it: the filter is
blind *and* the walk is starved, now measured on the kind of graph the
audience actually has rather than a degradation of a gold one. What is
genuinely new beyond 5i:

1. **The shatter table.** A person can be ~90% invisible to every name-keyed
   mechanism — filter, seeder, walk — while the extraction looks healthy on
   every edge-level metric.
2. **The metric inversion.** Textual-support classification scores the worse
   graph higher. Anyone auditing extraction quality by edge support alone
   will certify exactly the graph that fails this way.
3. **The twin-union boundary.** Duplicate-tolerance by exact-name union is
   real but only covers the duplicates a *good* pipeline leaves behind;
   cheap pipelines produce shards no name lookup groups.

The beat stands as 5i left it — *the walk covers your duplicates and your
hubs; it does not cover your pronouns* — and "your pronouns" is now measured
on a real gpt-5.6-luna extraction. Section 4's build-time
coreference+resolution is what turns 25 invisible chunks and 19 shards into
one node with 64 edges; nothing at query time did.

*(Caveats that travel with this: one corpus, and an unusually pronoun-heavy
one — first-person journals where the most-mentioned woman is referred to
almost entirely by role; the fever passage is arguably extraction recall
rather than coreference (no person tagged at all); and the charbonneau
hiring control at budget PPR rank 2 vs gold 47 is a different extraction's
different neighborhood, an observation, not a finding.)*

##### 5j-bis. Seeding every shard — Nathan's question, and it changes the mechanism story (2026-09-07)

Nathan asked whether the walk above was seeded from multiple possible
matches. It was not — "Sacagawea" resolves to the SACAGAWEA node alone,
because all three rescue mechanisms miss by construction: the full-text AND
query cannot token-match SAHKAHGAR WE or JANEY, the exact-name twin union
needs identical strings, and the seeder's vector fallback only fires when
full-text returns nothing. So 5j's verdict conflated *the walk cannot
compensate* with *the seeder cannot find the shards*. Separated, with two new
arms (`--vector-margin`, `--oracle-shards` in `measure_budget_graph.py`):

**Arm setup.** *Automatic:* union each mention's vector candidates within
0.10 of its top hit — no oracle, whatever the margin admits gets seeded;
here that is SACAGAWEA (8) + SNAKE INDIAN WIFE (1) + THE SQUAW (1) + the
**impure** INDIAN WOMAN (df 24, purity 0.42 — 58% of its chunks are other
women), which takes 0.706 of the df-proportional mass. *Oracle:* all 17
audited shards with purity ≥ 0.5 against gold (table in the script) — an
upper bound no real budget system has, and note the purity cut **excludes**
INDIAN WOMAN and SQUAR. Cells below are `filter · PPR · PPR+NEXT`:

| seeds | Nov-4 | Jun-16 fever | Aug-14 |
|---|---|---|---|
| what the seeder finds (5j above) | LOST · 75 · 90 | LOST · 1709 · 1769 | LOST · 1475 · 1154 |
| + vector margin 0.10, automatic | LOST · 131 · 184 | LOST · 1844 · **47** | LOST · 1031 · **69** |
| oracle: 17 audited shards | **IN, rank 3/31** · 17 · 22 | LOST · 2184 · 2208 | **IN, rank 26/31** · 2 · 2 |

Four findings, each mechanistic:

1. **Query-time compensation on a budget graph = query-time entity
   resolution.** Under oracle shards the *filter* recovers Nov-4 and Aug-14
   too (their tags are ONE OF HIS WIVES and HIS WOMAN — shards). 5g's parity
   returns the moment identity is resolved, at either build time or query
   time; the walk never separately compensates. "Skip the resolution pass"
   does not delete the work, it moves it into every query.
2. **Shard discovery is the wall.** The shipped vector margin (0.03) finds
   nothing new — SACAGAWEA sits 0.09 above the shard band. 0.10 catches
   three pure shards plus the impure hub; a hair wider (0.122+) admits
   KA KAWISSASSA and Charbonneau's own shards (SHABONOE, 0.7398). The
   seeder's-disease theme (5d-ter), now at the shard layer.
3. **The 5h-1 adjacency patch finally fires — as shards × NEXT_CHUNK, and
   only that far.** With the impure INDIAN WOMAN seeded, NEXT_CHUNK pulls the
   fever passage 1844 → **47** and Aug-14 1031 → **69**. Verified mechanism:
   INDIAN WOMAN tags chunks **one NEXT hop** from both test passages (the
   same-day chunks that say "the Indian woman" where the test chunk says
   "her"). This *corrects 5i's mechanism note*: the antecedent's role-phrase
   IS in the adjacent chunk — but on the gold graph those role-phrase
   mentions were merged into SACAGAWEA, so the name-support ablation deleted
   them, while the budget graph keeps them as taggable shards. Bound stated:
   rank ~47–69 is top 2%, not a context window, and it took the walk's every
   trick at once.
4. **The purity trap.** The oracle — purity ≥ 0.5, the "correct" merge —
   *loses* the fever passage (2184/2208) that the noisy automatic arm
   reaches (47), because the excluded INDIAN WOMAN shard is the one carrying
   the fever-week adjacency. Coverage and contamination have the same
   source: the phrase everyone used for her is the phrase used for others.
   Section 3d's bridge nodes at the extraction layer, now with a measured
   cost in *both* directions — merge it and import wrong-person chunks,
   drop it and lose the neighborhood.

The beat survives unchanged and gains its sharpest line: **the budget path's
query-time bill is an entity-resolution bill.** Duplicates and hubs the walk
covers; shards need resolving — at build time once, or at query time forever,
and the fever passage is only ever reachable through the contaminated shard
either way.

**Nathan's closing sharpening, and it is the section's landing:** *if we
resolve all the shards at query time, we might as well be filtering on tags
again.* The measurements make that an identity chain, not an analogy:
df-proportional shard seeding IS the merged node's walk (5f's arithmetic),
and the merged walk IS filter parity (5g) — so query-time resolution + walk
= build-time resolution + tag filter, paid per query instead of once, with
the bridge-node problem live and no consistency gate behind it (the
0.10-margin knife edge is §3's candidate generation rebuilt inside the
seeder, minus 3g's adjudication). The oracle row says it plainly: shards
known, the *filter* holds Nov-4 at rank 3/31. What survives the collapse,
stated small because it is small: (i) fever-class passages — no tag at any
resolution quality, walk+adjacency only, rank 47, an agent's path not a
context window; (ii) graded membership on impure shards — a filter takes
INDIAN WOMAN's 24 chunks all-or-nothing at 58% wrong-person, the walk takes
them down-weighted (mechanism only, those chunks unjudged — 5g claim #3
stays a footnote); (iii) build-time resolution is once, cached, and
judge-gated; query-time is every query, in the latency path, ungated. Every
query-time trick measured in 5i–5j-bis is the tag filter in disguise or
entity resolution in disguise — the value lives in the entity layer, which
is the talk's own thesis arriving from the opposite direction.

#### 5k. The other shard class — George Drouillard, one man in many spellings (2026-09-07)

Nathan's question after 5j-bis: Sacagawea is a tough nut — what about people
like Drouillard, named constantly but under wild spellings? Measured,
`scripts/measure_name_shards.py`, on both graphs. This completes a 2×2 the
section now owns: *role shards* (rarely named, identity in descriptions —
5j) vs. *spelling shards* (always named, identity split by orthography).

**Finding zero, and it relocates the problem: this one is live on the DEMO
graph.** The gold pipeline never merged DREWYER (df **265**) into GEORGE
DROUILLARD (df **63**) — disjoint, zero co-occurring chunks, 328 chunks
between them (11% of the corpus). Ask about him by his historical name and
the tag filter sees **19%** of him (`budgetluna`: 13%, 51/380). So 5g's
filter parity carries a precondition that was invisible until now: **parity
holds for *resolved* tags.** Every 5g case happened to ask about entities the
resolution pass had merged; Drouillard is the man it missed — the hub table's
on-stage duplicate, now with a measured retrieval bill.

The measurements, per graph (gold / budget):

1. **The seeder is spelling-hostage.** "George Drouillard" and "Drouillard"
   resolve to GEORGE DROUILLARD alone; "Drewyer" resolves to DREWYER (plus,
   on gold, the conflation shards DREWYER JOS and DREWYER FRASURE). Whichever
   spelling the user types, they get that shard and nothing else — full-text
   cannot cross an orthography gap, and the exact-name twin union (5f)
   requires identical strings.

   *Nathan asked whether full-text shouldn't return several candidates. It
   does — top-10, keep everything within 50% of the best hit, then twins;
   that is how "Drewyer" keeps five candidates and how both SACAGAWEA nodes
   seeded in 5f. But candidacy requires sharing a token, and every route was
   checked: the AND query matches exactly one node; the OR fallback (never
   fired — AND succeeded) scores GEORGE DREWYER at 3.76 on the shared
   "george" vs. 11.38 for the top hit, far below the keep-ratio floor; even
   Lucene's maximum fuzziness (`drouillard~2`) returns only GEORGE DROUILLARD
   — "drewyer" is ~5 edits away. And it is symmetric: asking as "drewyer"
   keeps the five DREWYER-cluster candidates and* cuts *GEORGE DROUILLARD
   (1.56, below the floor). Multi-candidate resolution returns a few
   candidates* per spelling cluster, *never across clusters.*
2. **Vector discovery fails *worse* here than for role shards.** DREWYER —
   81% of the man — ranks **#22** among vector candidates for "George
   Drouillard" on both graphs, behind five Dorion variants (Pierre Dorion:
   a *different* interpreter — 5e's co-typed substitution, now one layer
   down, inside shard discovery), DREYER, DURIOUE, DURRIEN. A margin deep
   enough to reach #22 admits ~21 nodes, mostly other people. Embedding
   space clusters French-surname-shaped strings: similar names of different
   people sit closer than different spellings of the same person. Sacagawea's
   role shards had a usable-if-impure margin at 0.10; Drouillard has none.
3. **The walk from the caught shard trails plain cosine.** Median corpus rank
   of the 265 missed DREWYER chunks, seeded from what resolution caught:
   **681** (budget: 862) — vs. cosine on a Drouillard question at **499**
   (533). The shards never co-occur, so the bridge is three steps through
   shared co-mentions, and those co-mentions are the expedition's hubs, which
   the IDF weight exists to damp. The weighting that saves the walk from
   Lewis kills the only route between a man's two spellings.
4. **Resolution fixes it, cheaply, and then either tool works.** Both shards
   df-proportional (arithmetically the merged node, 5f): median **168**
   (196). Tag filter on both shards: every passage, by membership. And unlike
   Sacagawea this is the *easy* merge — two pure, disjoint shards, exactly
   the string-similarity-plus-judge case §3's machinery handles, no
   bridge-node ambiguity. The pipeline simply never ran it on him.

**The 2×2, candidate stage material:**

| shard class | query-time discoverable? | build-time fix |
|---|---|---|
| spelling shards (Drouillard, 265/63 on the demo graph) | no — vector nominates similar names of *other people* first (#22, behind the Dorions) | string + judge merge — cheap, §3's machinery |
| role shards (Sacagawea, 19 shards + 25 untagged) | partial and impure; shards×NEXT reaches ~rank 50 | coreference — the expensive pass |

Both rows end at the entity layer, which is 5j-bis's landing generalized: the
choice is never filter vs. walk, it is when the resolution bill gets paid —
and Drouillard shows the bill exists even on the graph you thought was gold.

*(Discipline notes: all medians are over tag-defined populations — no chunk
was judged for relevance, and no claim is made about which DREWYER passages
answer anything; the Drouillard question used for the cosine reference is not
in the bank; the conflation shards — SHANNON DREWYER df 6, "Shannon &
Drewyer" sentences fused into one node — are noted but unmodelled.)*

#### 5l. Thematic questions on `lewisclark` — the class with no filter, and the walk's first clean win on a good graph (2026-09-07)

After 5g, a PPR win needs a question the filter cannot run on. 5h-2(b) named
the class: the bank's three thematic questions (`trade-goods`, `food-sources`,
`illness-and-injury`) decompose to **zero entity mentions** — re-verified live
against the cached `gpt-5.6-luna` parses before this run — so no tag filter
can be constructed and the bar honestly drops back to cosine alone. Run on
**`lewisclark`** (chunk embeddings + `chunk_embeddings` index restored with
the clone; `lc-mentions` projects at 7,354 nodes / 44,900 rels / 220 ms), so
a win cannot be credited to extraction gaps the way 5i's inverse was. New
`scripts/measure_thematic.py`; fresh hand reads of every window
(`results/thematic-lewisclark.md`, 48 distinct chunks); the old finding-4/5
thematic numbers used the contaminated proxy and are not comparable.

Three windows per question: `vector` (cosine top-8), `passage-blend` (cosine
0.6 + passage-PPR 0.4 — pure 5h-2(b)), `expand` (shipped 0.6/0.2/0.2, semantic
entity seeder — on `lewisclark` that means the species/event/taxon indexes).

**The hand read, trade-goods — cosine's thematic failure is co-typed
substitution writ large.** The question asks what *the expedition* traded;
cosine's top-8 answers with *other people's* trade — the coastal
maritime-trade cluster (two near-duplicate Lewis/Clark journal pairs among
them) and the Skillute middleman economy. Read honestly, only 2 of 8 vector
slots show the expedition trading anything. `expand` promoted, from cosine
ranks 28–112, the passages that *are* the answer:

| promotion | cosine rank | carried by |
|---|---|---|
| the captains cut the **buttons off their coats** (+ eye-water, basilicon) to buy roots and bread, 1806-06-02 | **77** | BUTTONS df 5 |
| **gun + 100 balls + 2 lbs powder** paid to Twisted Hair for horse-keeping; the gun itself bought "of the indians below for 2 Elkskins", 1806-05-12 | **112** | KNIVES df 16, POWDER df 64 |
| Ordway ferries **elk skins, two coats, 4 robes** downriver "to add to the Stores… for the purchase of horses"; 3 dogs bought as food, 1806-04-18 | 28 | COATS df 4, PACK SADDLES df 4 |
| Blackfeet parley — flag, medal, handkerchief given; their Saskatchewan trade described, 1806-08-12 | 108 | GUNS df 35, BLANKETS df 19 |

Window month-coverage goes **3 → 7**; distinct entities 93 → 125; the
near-duplicate pair count drops 2 → 1. The mechanism is exactly 5h-2(b)'s
prediction: **the question says "goods", cosine retrieves the passages that
*describe* goods (trader inventories), and the walk crosses the low-df Supply
nodes — BUTTONS, COATS, ELKSKINS, BEADS — from the descriptions to the
passages where the expedition actually spent them.** Vocabulary-free query
expansion, receipts printed per promotion by the script.

**food-sources reads the same way.** Promotions from ranks 34–90 include the
corpus's best quantified ration passage ("it requires 4 deer, an Elk and a
deer, or one buffaloe, to supply us plentifully 24 hours", rank 34), horse
beef for supper on the Kooskooske (57), dogs purchased to eat (60), the
meat-exhausted buffalo hunt of the return (90), and the subsistence-planning
council ("we now view the horses as our only Certain resource for food", rank
9). Month coverage **5 → 7**, entities 41 → 83. The question literally asks
"across different stretches", and the stretch coverage is the win. One
promotion is a clean miss: the Cameahwait village-arrival scene (rank 13) has
no food content and rode in on the CAMEAHWAIT bridge — the graded-membership
cost, visible and priced.

**illness-and-injury is the anti-case, and it is the section's honest bound.**
Per-slot relevance actually *improves* — vector's #1 is Clark doctoring forty
Nez Perce with eye-water, topic-match-wrong-subject again — but `expand`
collapses the window onto **one episode**: 7 of 8 chunks from the May 1806
Long Camp medical drama (the child's imposthume, Bratton's back, the paralyzed
chief), month coverage **4 → 1**, near-duplicate pairs 0 → 2. Gone: the
Sept-1805 mass sickness, the dysentery-and-skin-eruptions passage, the Fort
Clatsop sick-list. The mechanism is the same one that wins above: when a
theme's rare entities all co-occur in one episode (JEAN BAPTISTE CHARBONNEAU
df 9, WILLIAM BRATTON df 40, JOHN SHIELDS df 118, in the same chunks), the
walk's conjunction-seeking *is* episode-seeking, and it anti-diversifies.
Which theme breaks it is a fact about the corpus's entity co-occurrence
structure, not about the question's wording — nothing in the two question
texts predicts trade-goods wins and illness loses. **This is §6's entrance,
measured**: the bank note always said community diversification should shine
on a thematic question; it turns out the walk is what *creates* the need on
this one.

**Attribution, so the entity half doesn't get oversold.** The semantic entity
seeds are junk-on-paper for these questions — `DEPARTURE OF JOHN COLTER` seeds
two *different* questions (cosine's disease at the entity level, 5d-ter as
predicted). A percentile diagnostic on the star promotions shows both halves
agreeing (passage-PPR 0.87–0.99, entity-PPR 0.89–1.0 — the latter inflated by
sparsity, where "reachable at all" is a high percentile), so the promotions
are jointly supported with the passage half discriminative. The entity half's
real, measurable act was **demotion**: it pushed the native-trade-network
passages (entity percentile 0.16–0.77) out of the trade window, which is why
`expand` diverges from `passage-blend` far more than its 0.2 weight suggests.
`passage-blend` alone is conservative — 5–6 of 8 slots unchanged, promotions
only from ranks 9–30.

*(Discipline notes: three questions, windows of 8, judged by reading — no
gold, no rank metrics, and the near-dup/month/entity counts are descriptive
corroboration, not verdicts. The blend weights are the shipped defaults,
deliberately untuned — after 5d-quinquies, no knob sweeps against hand-read
outcomes. Single corpus; the illness collapse in particular should be
replicated on any second corpus before it becomes a general claim.)*

**What section 5 gets to say, and it completes the arc:** on a good graph,
single-entity questions belong to the tag filter (5g); questions that name
nothing belong to the walk, because there is no tag to filter and cosine
retrieves the *description* of the theme rather than its instances. The
buttons passage is the stage demo — one sentence of setup, one promotion, one
receipt (BUTTONS, df 5, shared with a trader-inventory passage the vector
already had). Illness is the stated bound and the hand-off to §6. Candidate
extension to the 5.12 decision table: *"questions name nothing at all →
passage-seeded expansion, and cap the window per community."*

#### 5m. Neighborhood questions — the filter can't be built, and the walk finds the name rather than the answer (2026-09-07)

Class 1 of the post-5g screen (5h-4's candidate): questions where the entity
holding the answer is *the thing the asker doesn't know*. Two cases built on
`lewisclark` in `scripts/measure_neighborhood.py`, both with tag-defined
target populations that were **read in full before the questions were
engineered** (16 Cameahwait chunks, 8 Yelleppit/Yellept chunks — all
substantive). Resolution uses the decomposed seeder's deterministic full-text
path, as in 5k. Strategies: cosine; filter+cosine on the resolvable mention;
pure entity-seeded PPR from the resolved nodes (df-proportional); 0.6/0.4
blend. Population medians, the 5e/5k form.

**The filter receipts are total.** "What do we know about Sacagawea's
brother?" resolves only SACAGAWEA (df 85), whose filter covers **2 of 16**
Cameahwait chunks. "Which chief hosted the expedition among the Walla Walla
on the return?" resolves ONE of the nation's **twelve** spelling shards
(WALLA WALLA, df 3 — resolution is spelling-hostage, 5k one layer up), whose
filter covers **1 of 8** Yelleppit chunks; 4 of the 8 carry no nation tag of
any spelling, so even an oracle OR-filter over all twelve shards is blind to
half the answer.

**The flagship fails everyone — and the failure is arithmetic.** Median
corpus rank of the 16 target chunks: cosine **319**, pure walk **314**, blend
**172**. The reunion passage that states the relation ("the Indian woman, who
proved to be a sister of the Chif Cameahwait"): cosine 149, blend **26**,
filter+cosine 15-of-85. **No strategy puts a single target in its top-8**,
and both top-8 windows were read: cosine's is tomahawk-recovery and
horse-butchering junk, the blend's is Sacagawea-biography junk. The reason is
5i's lesson with a denominator: the bridge is 2 chunks out of the anchor's 85
first-hop edges, ~2% of the walk's first-hop mass, and no damping value
turns 2% into a top-8. Reachable, not ranked.

**The delete-test confirms the bridge is the mechanism.** Reproject without
the 2 bridge chunks and rerun the walk: every one of the 14 satellite-only
chunks worsens, median **338 → 601** (worst cases 666→1733, 829→1782). The
mass really does cross those two chunks; there is just not enough of it.

**The replication wins, and the contrast isolates the variable: anchor
degree.** wallawalla-chief medians: cosine 43, walk **16**, blend **10**;
blend's top-8 holds 3 targets to cosine's 2. Seeded at one df-3 shard, the
walk put a third of its first-hop mass on a chunk co-mentioning Yelleppit and
crossed to the chief's other chunks — including the four no filter of any
kind can reach — doing **query-time shard resolution through the satellite
himself as the bridge**. Same mechanism as the flagship, opposite outcome,
because the bridge was 1 edge of 3 instead of 2 of 85. The walk crosses a
bridge in proportion to how little else the anchor touches; ask for the
brother of the corpus's most-storied woman and the bridge drowns in her own
biography.

**What the walk actually contributes on the hub-anchored case: the name.**
Pure walk ranks the second bridge chunk (Charbonneau, the Indian woman, and
*Cameahwait* arriving together) at **4** — cosine has it at 1187. One-shot
retrieval cannot answer the brother question, but the walk's top-8 hands the
asker the missing name, after which the question collapses (his 16 chunks
*are* his tag population). Class 1's honest landing: **on a hub anchor it is
a two-step retrieval — the walk performs the name-discovery step, and the
follow-up is a tag lookup**; agentic retrieval, or §7's path business, not a
better ranker. On a low-df anchor, one shot suffices and the blend simply
wins.

*(Discipline notes: two cases; populations tag-defined and read; medians over
16 and 8 chunks; window verdicts by reading both top-8s; no gold, no
proxy. The Le Borgne case was screened out — his passages hinge on "swivel,"
which cosine finds unaided. The wallawalla blend's remaining top-8 slots were
not judged; the claim there is target coverage, not window purity.)*

**Stage candidates:** the delete-test is the cleanest mechanism demo the
section owns (one projection, one rerun, every rank moves the same
direction); the brother question is honest theatre — every retrieval mode
whiffs, then the walk quietly surfaces the name — and it hands off to §7's
"explain the connection" beat. The anchor-degree contrast (85 vs 3) extends
5.12's decision table: *"the answer's entity is the unknown → low-df anchor:
walk and done; hub anchor: walk to discover the name, then query it."*

#### 5n. Bridge decay — Nathan's agent rule, measured as a curve (2026-09-07)

5m ended on a two-point contrast (anchor df 3 wins, df 85 loses), and Nathan
generalized it into an **agent routing rule: resolve the question's mentions,
count their chunk degree, and route — low-df seeds justify expansion, high-df
seeds say filter and stop.** Degree is one COUNT query after resolution,
observable before any retrieval runs. The bridge fraction — how much of the
anchor's edge mass crosses toward the satellite — is the true mechanism but
is *not* observable a priori (the satellite is the unknown), so df is the
entire signal an agent gets.

`scripts/measure_bridge_decay.py` turns the two points into a curve with no
relevance judgements: every (anchor, satellite) co-mention pair on
`lewisclark` (satellite df 4–30, ≥3 exclusive chunks; 38,098 pairs, anchors
stratum-sampled 385 of 1,575), single-seed PPR per anchor, median corpus rank
of the satellite's **exclusive** chunks per pair — tag-defined populations,
the 5e/5k mass form. By anchor degree:

| anchor df | pairs | median of pair-medians | % pairs ≤50 | % ≤100 |
|---|---|---|---|---|
| 2–5 | 840 | **39** | 59% | 82% |
| 6–15 | 2,589 | 112 | 23% | 46% |
| 16–40 | 5,885 | 223 | 5% | 19% |
| 41–100 | 5,606 | 388 | 0% | 5% |
| 101–300 | 6,377 | 624 | 0% | 0% |
| 301+ | 2,332 | 1,058 | 0% | 0% |

Monotonic top to bottom, no exceptions. Binned instead by bridge fraction
(shared/df_a) the same pairs run 700 → 29 median across six bins — the
fraction is the mechanism, degree its observable proxy (the two are coupled
by construction: a df-3 anchor sharing one chunk has bridge fraction 0.33; a
df-300 anchor sharing one has 0.003). 5m's cases sit on the curve: Walla
Walla (df 3) measured walk-median 16 against the bin's 39; Sacagawea (df 85)
measured 338 against the bin's 388.

**The routing table an agent can execute** (thresholds are this corpus's —
2,913 chunks — the shape is the claim, the numbers are not portable):

| resolution outcome | route |
|---|---|
| zero mentions (thematic) | passage-seeded expansion, community cap (5l) |
| seeds with df ≲ 15 | **expand** — the filter can't fill a window anyway, and the walk crosses bridges at useful rank |
| seeds with df ~16–40 | marginal: blend, expect partial coverage |
| seeds with df ≳ 40 | **filter+cosine and stop** (5g); if the question is relational ("X's brother"), go two-step — walk or read for the missing name, then query it (5m) |

*(Discipline notes: this measures the walk's crossing capacity — how
discoverable a neighbor's unshared chunks are from an anchor seed — not
victory over cosine on any question; that comparison needs questions and
reads, and 5m did two. Populations are tag-defined; medians over ≥3 chunks
per pair; per-pair data in `results/bridge-decay-lewisclark.csv`. Single
corpus, single damping (0.45), IDF weights; the monotonicity is robust to
binning, the absolute medians are not.)*

**Where it lands in the talk:** this is §9 material as much as §5 — "when
does your agent reach for the graph tool" now has a measured answer and a
one-query implementation. It also closes section 5's arc cleanly: 5g said
tags beat the walk when extraction is good; 5l said the walk owns questions
with no tags; 5m/5n say that in between, *the seed's degree tells you which
regime you are in before you spend anything*.

#### 5o. The `lewisclark` migration — 5.1–5.11 re-measured (2026-09-07)

Decision #2 executed: **`lewisclark` is the demo graph for everything**, and
every number slides 5.1–5.11 quote has been re-measured there. The `neo4j`
tables in findings 1–5k above are kept unchanged as history, per this
section's retraction precedent — do not quote them for the stage; quote this
finding and the updated `section-05-slides.md`.

Conditions: local Desktop DBMS (heap found already raised to **8 GiB** — the
2 GiB pre-condition is more than met), `NEO4J_DATABASE=lewisclark` passed
explicitly everywhere, home database untouched on `neo4j`, all work
read-only. `lc-retrieval` projected on `lewisclark` for the first time
(8,139 nodes / 63,836 rels, 78 ms); `lc-mentions` re-used (7,354 / 44,900,
67 ms fresh). Question decompositions came from the 5f disk cache — zero new
API calls for the bank; three probe questions (Drouillard phrasings, Pacific,
prairie-dog) cost one parse each.

##### The headline numbers, old vs new

| measurement | `neo4j` (history) | **`lewisclark` (quote these)** |
|---|---|---|
| 5.1 failure table: mention Charbonneau | 62 · median 296 · 2 in top-8 | **69 · median 300 · 2 in top-8** |
| 5.1: interpreter vocabulary, not him | 108 · 578 · 2 | **101 · 576 · 2** |
| 5.1: neither | 2,743 · 1,524 · 4 | **2,743 · 1,523 · 4** |
| 5.6 hub table top rows | deer 589 · elk 439 · Lewis 377 | **Lewis 825 (28.3%) · elk 587 · Clark 506 · mule deer 458 · bison 396 · Missouri 348 · DREWYER 297** |
| 5.6 unresolved-duplicate row | DREWYER 265 vs GEORGE DROUILLARD | **DREWYER 297 vs GEORGE DROUILLARD 84 — survives** |
| 5.6 overlap ladder (naive → IDF → short → mentions+short+IDF) | 4.47 → 0.60 → 1.07 → 0.07 | **2.84 → 2.04 → 1.27 → 0.47** |
| 5.6 Lewis mean rank, naive → final | 2.5 → 21.5 | **3.2 → 18.1** (median 3 → 10) |
| 5.7/finding 6 damping | 0.85 worst of six (16 top-8 / 442) | **holds: 0.85 worst on both columns (19 / 542 vs 27 / 482 at 0.45)** |
| 5.8/finding 7 `alpha=1.0` | 6/6 identical orderings | **14/14 identical** (0.9: 7/14; 0.5: 0/14, overlap 7.64; 0.0: 5.21) |
| 5.4 Nov-4 passage | cosine rank 22 | **cosine rank 20**, promoted to blend #6; `SACAGAWEA` and `SHOSHONE` both tagged on `13c2e69bf03a0342` — the extraction-resolved coreference survives (a stray `ONE OF HIS WIVES` Person is also tagged, harmless) |
| 5.4 granularity | median 60 words/entity in a 325-word chunk | **median 40 words/entity in a 333-word chunk** |
| 5.10 conjunction, comparable degree | SAC(64)+CHAR(62): 9 dual chunks, median 5 vs 71/51, all in top-20 | **SAC(85)+CHAR(69): 17 dual chunks, median 9 vs 104/44, all 17 in top-20** (median score 0.00712 ≈ 0.00324+0.00402 — additivity holds) |
| 5.10 degree imbalance | SHOSHONE(192)+EQUUS(14): 6.6% bonus | **pair replaced — see below. LEWIS(825)+CYNOMYS(42): only-B 0.00633 vs both 0.00672, a 6.1% bonus** |
| 5.10 Floyd week | 18 passages; 3/18 in top-8, cosine and every variant | **identical: 18; 3/18 for cosine, shipped blend, `lc-retrieval` blend, and d=0.85** |
| 5.10 bounded-by-extraction receipt | Aug-18 horse passage has no horse | **receipt replaced — see below. New: no keelboat/barge entity exists at all** |
| entity-signal delete test | judged ranks [7,3,5]→[14,10,11], [8]→[11] | **[3,6]→[26,14] (charbonneau), [6]→[15] (Nov-4) — larger, still the section's basis** |
| zero-entity recall floor | 179 chunks · 6.1% · 3.4% of text | **129 chunks · 4.4% · 2.2% of text** |
| 5.11 latency | project 94 ms · cosine 4 ms · fresh ~196 ms · 8 seeds batched 56 vs 441 ms | **project 67 ms (mentions) / 78 ms (retrieval) · cosine 6 ms · fresh ~215 ms (cosine 45 + entity PPR 70 + passage PPR 70) · 8 seeds 66 vs 494 ms (7.5×)** |
| finding 5's Floyd–Missouri demo case | 1 chunk names both; cosine 415 → blend 68 → pure structure 16 | **2 chunks name both; the buried one: cosine 412 → blend 95 → pure structure 8** |

Ladder methodology note: the `lewisclark` ladder was run with the
**decomposed** seeds each question actually uses on this graph (semantic
fallback for the three thematic questions), over the current 14-question
bank. Decomposed seeds are sharper — many questions carry a single seed — so
the naive row starts lower than `neo4j`'s 4.47 partly for that reason. The
story the slide tells survives intact: naive, Lewis sits in the top handful
of entities for *every* question (mean rank 3.2); each fix helps alone and
the three together take overlap to 0.47/8 and Lewis to 18.

##### What changed in kind, not just in number

1. **Lewis is now the top hub — the deer punchline is dead.** The luna
   extraction tags people far more aggressively (Lewis 377 → 825, in 28.3% of
   the corpus), so "the deer outranks both captains" is false on
   `lewisclark`. What survives is better: **the elk still outranks Captain
   Clark**, and the hub *moved* when the extractor changed — "whatever you
   assumed your hub was, check" now has a measured demonstration across two
   extractions of the same corpus. Slide 5.6 rewritten accordingly.
2. **The seeder is the decomposed one, by necessity and by preference.**
   `lewisclark` has no Person vector indexes by design, so the semantic
   seeder cannot seed people at all; the decomposed seeder (5f) is the demo
   path. Consequence for 5.9: `charbonneau-role` seeds **one** node,
   `TOUSSAINT CHARBONNEAU` at weight 1.0 — the two degree-1 spike seeds are
   gone, and the slide now shows the mention-resolution line instead of a
   three-seed table.
3. **The "seeds both duplicates" receipt pivots to `PACIFIC OCIAN`.**
   Post-disambiguation there is one SACAGAWEA Person, so the old receipt is
   impossible — which is itself the new slide's §4 callback ("the duplicate
   that used to sit on this slide got merged; the pipeline left you PACIFIC
   OCIAN instead"). Measured receipt: `pacific-arrival`'s mention `'Pacific'`
   resolves to **PACIFIC OCEAN (df 19, weight 0.605) and PACIFIC OCIAN (df 5,
   weight 0.395)** — a real spelling-shard duplicate, hedged automatically,
   df-proportional split on screen. Bonus receipt in the same run:
   `keelboat-return`'s `'Missouri'` seeds the exact-name twins MISSOURI
   (WaterBody, df 7, 0.268) and MISSOURI (Place, df 1, 0.038).
   **The honest limit, measured:** the hedge only covers shards sharing a
   token. For `'Drewyer'`, fulltext returns DREWYER 10.15 and GEORGE
   DROUILLARD 2.99 — below the 0.5 keep-ratio, so only the asked-for spelling
   seeds; `'George Drouillard'` and `'Drouillard'` return GEORGE DROUILLARD
   alone. Exactly finding 5k's boundary: a cross-token spelling shard is
   build-time work. Stated on the slide as a parenthetical.
4. **The horse receipt got fixed by the better extraction — and the
   extraction-bound receipt moves to the keelboat.** On `lewisclark` the
   Aug-18-1805 passage carries `Supply HORSES` (plus SHOSHONE, SHOSHONE COVE,
   LEWIS, CLARK, JEFFERSON'S RIVER, ODOCOILEUS HEMIONUS), the decomposed
   seeder resolves `'horses'` to the Supply shards (HORSE 61 / HORSES 110)
   via the supply fulltext index, and the blend puts the Aug-18 answer at
   **#1** for `shoshone-horses` (it sits at cosine rank 5 there too — the
   re-embedded corpus is kinder to it). The replacement receipt is cleaner:
   **no keelboat or barge entity exists anywhere in the graph** — the
   decomposer reports `'keelboat' → nothing` (already noted in 5f), the
   April-7 answer passages cannot be seeded by the question's word, and the
   coda "better extraction moves the boundary, it does not remove it" is now
   measured rather than asserted (horse fixed, keelboat still missing,
   129 zero-entity chunks).
5. **The degree-imbalance receipt pivots to LEWIS + CYNOMYS.** Luna's
   EQUUS CABALLUS is df 65 against SHOSHONE 150 — only a 2.3× gap, and the
   old pair no longer shows the effect cleanly (only-horse median rank 38,
   both 6). MERIWETHER LEWIS (825) + CYNOMYS LUDOVICIANUS (42) is the same
   mechanism at a 20× gap and lands within a hair of the old number: a
   **6.1%** bonus for also mentioning Lewis (0.00633 only-B vs 0.00672 both).

##### The hand read, redone on the `lewisclark` windows (5d-class)

Same rule as 5d — *does the promotion contain something a correct answer
needs that no cosine top-8 passage contains?* — applied to every passage the
shipped blend (decomposed seeds) promotes into the top-8 from outside
cosine's, across the three `kind: connection` questions. Judged by the
migrating session by reading each window in full; **awaiting Nathan's read**
before anything here is treated as settled.

| question | cosine top-8 (lewisclark) | promotions | clear the bar |
|---|---|---|---|
| `charbonneau-role` | 2 of 8 carry him (the 1806 pay settlement at #1 — new, and strong — and the Lewis departure roster) | 6 | **2** |
| `sacagawea-interpreting` | 4 strong + 2 partial — better than `neo4j`'s window | 4 | **1 (Nov-4, decisive)** |
| `shoshone-horses` | 3 of 8 are Aug-1805, **including the Aug-18 answer at cosine rank 5** | 1 | **0** |

**3 of 11.** The same shape as `neo4j`'s 4 of 16: real wins, not a rout, and
the failures teach.

Promotion-by-promotion, `charbonneau-role` (blend window: 6 of 8 tagged with
him, vs cosine's 2 — that membership count is exact and slide-safe):

- ✅ `1805-03-18` (cosine 22) — *"Mr. Tousent Chabono, Enlisted as an
  Interpreter this evening"*. The hiring; the same passage that won on
  `neo4j`. No cosine passage has the start of the role.
- ✅ `1805-04-07`, Clark's departure roster (cosine 27) — *"Shabonah and his
  Indian Squar to act as an Interpreter & interpretress for the snake
  Indians"*. The assignment — WHICH language and why her. Cosine's window has
  Lewis's roster, which lists him as interpreter but not the Snake
  assignment; this is the which-language content that `1804-12-18` carried in
  the old read. Judged as clearing on that basis; the closest call of the
  three.
- ❌ `1806-07-01` (cosine 35) — the return-split plan; Charbonneau listed
  among Clark's ten. Mentions him, adds no role content.
- ❌ `1806-08-11` (cosine 33) — Dixon/Hancock trappers; he is not in it
  (promoted by blend mechanics, not by his tag).
- ❌ `1806-06-01` (cosine 40) — the failed trading errand with LaPage. Real
  color (he was used as a trader), not *needed* by a correct answer.
- ❌ `1806-08-15` (cosine 59) — Colter's discharge + Charbonneau relaying
  Minetarree war news. Color again.

`sacagawea-interpreting` (cosine window now holds the 1805-08-17 council
*"through the medium of Labuish, Charbono and Sah-cah-gar-weah"*, both copies
of the 1806-05-11 Chopunnish chain council, and 1805-11-03 — her failing to
converse with a coastal captive, which is a which-nations receipt in itself):

- ✅ `1804-11-04` (cosine 20) — the hiring and the arrangement; never names
  her. Still the best single passage, still reachable only through the
  extraction-resolved coreference. Decisive, as before.
- ❌ `1806-08-17` (cosine 15) — the family's discharge, "in the Capacity of
  interpreter and interpretes[s]". Explicit, but the capacity is already
  evidenced live by the Aug-17-1805 council in cosine's window.
- ❌ `1805-08-17` continuation (cosine 19) — Clark to take "Carbono and the
  indian woman" to hasten the horses. Logistics.
- ❌ `1806-06-04` (cosine 30) — Chopunnish diplomacy, Shoshone messaging
  plans; she is not in it.

`shoshone-horses`: one promotion (`1806-02-15` horse-abundance/mules, cosine
18) — Columbia-plains horse ethnography, not the Shoshone acquisition; does
not clear. But the question's complexion changed: the Aug-18 answer passage
is *inside* cosine's top-8 here (rank 5) and the blend ranks it #1, with
Aug-14 and Aug-24 also in the window. The old triple failure (seeder matched
the verb / forcing seeds barely helps / no combiner rescues) is `neo4j`
history — on `lewisclark` the decomposed seeder resolves `'horses'` +
`'Shoshone'` (df 150) and the window is respectable. The question is no
longer a clean failure exhibit; it is also not a promotion win.

##### Rough edges found in passing, for the 5f ledger

- **`prairie-dog` decomposes to the wrong species on `lewisclark`.** The
  mention `'prairie dog'` routes to the AnimalSpecies vector index and
  resolves to `TYMPANUCHUS PHASIANELLUS` (sharp-tailed grouse — the journals'
  "prairie fowl"), not `CYNOMYS LUDOVICIANUS` (df 42, present). The word
  *prairie* carries the match — cosine's disease at the seeder, one more
  time, in a legible form. The control question still functions (its point is
  that cosine already wins it), but `--show-seeds` on stage would show a
  grouse; worth knowing before Q&A.
- **5.1's #2 slot (`Mr. Duriaur`, 1804-06-12) is tagged `GEORGE DROUILLARD`**
  on `lewisclark` — the judge's-word-only merge 3g disclosed (`GEORGE
  DROUILLARD + MR. DURIAUR`, accepted by Nathan; historically that man is
  almost certainly Dorion Sr.). The slide's names column reads the text, not
  the tags, so it is unaffected — but a hub-table or filter demo that touches
  GEORGE DROUILLARD inherits that merge's chunks.

##### Not re-measured, and why

- **Finding 4's conjunction-bearing table and finding 5's blend/weighting/
  seed-count sweeps** — scored against the co-mention proxy already retracted
  for relevance; off slides by standing rule. The damping sweep (direction
  only) was re-run because slide 5.7 quotes the direction.
- **5f's coverage numbers (10/11 vs 8/11)** — the accept-sets in
  `measure_seeds.py` were hand-resolved against `neo4j` names; re-scoring
  them against `lewisclark` without re-resolving each accept-set would be the
  gold-decoy mistake again. The seeds themselves were spot-verified above
  (charbonneau 1 seed, shoshone-horses resolves both mentions, thematic
  fall back). Re-resolving the accept-sets is Step-5-adjacent work.
- **5i/5j/5j-bis (ablation and budget graph)** — they run on their own
  databases (`budgetluna`, synthetic ablation) by construction; nothing to
  migrate.
- **5b's linearity checks** (bias = linear weight, flat = sum) — GDS-version
  properties, not corpus properties; the batching ratio table was re-measured
  (66 vs 494 ms) and the linearity claims were not re-tested.
- **`keelboat-return` control re-confirmation at the shipped blend** (caveat
  #12's last bullet) — superseded in spirit: the question's seeds and window
  were inspected during the receipt work; a formal re-confirmation belongs
  with Step 5's gold repair.

#### 6. Damping: shorter walks win monotonically

Share of walk mass within `k` steps is `1 − d^(k+1)`.

| damping | mass ≤3 steps | top-8 | median rank |
|---|---|---|---|
| **0.35** | 98% | 19 | **274** |
| 0.45 | 96% | 19 | 286 |
| 0.55 | 91% | 19 | 309 |
| 0.65 | 82% | 19 | 322 |
| 0.75 | 68% | 17 | 350 |
| **0.85** ← `RerankConfig` default | 48% | **16** | **442** |

The three-step horizon is not a heuristic on this corpus, it is the optimum, and
the shipped default is the worst of six values tested. On a bipartite walk the
parity matters too: from an **entity** seed, step 1 = passages mentioning it,
step 2 = co-mentioned entities, step 3 = passages of those entities.

*Re-measured on `lewisclark` (5o): direction holds — 0.85 is the worst of the
six on both columns (top-8 19, median 542) against 27/482 at 0.45.*

#### 7. `alpha=1.0` verifies exactly — and the current architecture caps the gain

| alpha | identical ordering to baseline | overlap |
|---|---|---|
| **1.0** | **6/6** | 8.00/8 |
| 0.9 | 3/6 | 8.00/8 |
| 0.5 | 0/6 | 7.67/8 |
| 0.0 | 0/6 | 5.33/8 |

`alpha=1.0` reproduces the vector baseline byte-for-byte, which is the
credibility move: it proves the knob is real and the baseline was not swapped.

*Re-measured on `lewisclark` (5o): 14/14 identical orderings at `alpha=1.0`
(0.9: 7/14 identical, overlap 8.00; 0.5: 0/14, 7.64; 0.0: 0/14, 5.21).*

**But it also exposes why the shipped design underdelivers.** `rerank()` seeds
from the vector top-5 and then ranks *only the vector top-50*, so the upside is
bounded by "what sits in positions 9–50 that belongs in 1–8." Live, that is
**one slot in eight**. The thing PPR is good at — surfacing passages nobody
nominated — is forbidden by the candidate gate. Section 5's new design blends
over the whole corpus instead, which is what lets a passage at rank 415 be
reached at all.

*Terminology hazard for the slides:* `RerankConfig.alpha` is the cosine/graph
score blend and `damping_factor` is the walk horizon. They are unrelated knobs
and need distinct names on screen.

#### 8. Global PageRank on this graph is a degree count — and `lift` is degree normalisation

Two independent reasons plain PageRank has no defensible job here, both of which
killed an earlier suggestion to use it as an entity-linking prominence prior:

- **Undirected collapses to degree.** For a connected undirected graph the walk's
  stationary distribution is *exactly* `deg(v)/2|E|`; PageRank adds teleport,
  which shrinks it toward uniform. So it is a smoothed degree count and carries
  no new information.
- **Directed is semantically incoherent.** PageRank's model requires an outbound
  edge to mean one consistent thing. Here `MET` and `MARRIED_TO` are symmetric,
  `MEMBER_OF` and `TRIBUTARY_OF` flow importance toward the container, and `SHOT`
  carries none. For the symmetric types the direction is partly an artifact of
  which entity the extractor named first — not a property of the world.

Consequence for shipping code: `pagerank.py` uses global PageRank as the `lift`
denominator on the undirected projection, so **`lift` is currently
`PPR / weighted-degree` under a grander name.** That does not invalidate it —
dividing by the walk's base visit rate is well motivated — but the explanation
has to change from "divide by global importance" to "divide by how often the
walk lands here regardless of the question," and `global_pagerank()` plus its
session cache may reduce to a degree lookup. **Unmeasured:** Spearman of global
PageRank against weighted degree on `lc-retrieval`. Worth one query before the
simplification.

The structurally-inert signal that suggestion was reaching for — the stray
`SHOSHONE` `:Person` with no extracted relationships — is just **degree**, and
`resolve.py`'s mention-count tie-break already captures it. Good thirty seconds
from the stage: *we reached for PageRank and a `count()` was better.*

#### 9. Corpus shape — and the decision not to re-chunk

Chunks are long enough for the mechanism to matter: **median 325 words, p90 486,
median 60 words per entity** — roughly 5× finer granularity than the
whole-passage embedding. 698 chunks (24%) carry four or more distinct entity
types.

*On `lewisclark` (5o): median 333 words, median **40** words per entity (the
luna extraction is denser — 22,699 mention edges), and the zero-entity recall
floor shrinks to 129 chunks (4.4%, 2.2% of text). The shape argument below is
unchanged.*

```
workable      (>=250 words, >=4 entities)   1,405   48.2%
long but thin (>=250 words,  <4 entities)     447   15.3%
short enough  (embedding already sharp)     1,061   36.4%
invisible     (zero entities)                 179    6.1%
```

**Extraction saturates before length does.** Entity count climbs to the 400–499
word band (6.4 avg) then *reverses* (5.3 at 500–599), while chars-per-entity
rises monotonically 145 → 339. The longest passages are the least densely
annotated — the granularity gain erodes exactly where blur is worst.
*(Evidence past 500 words is thin: n=142, and one chunk above 600.)*

**A hard recall floor.** 179 chunks — 6.1% of chunks, 3.4% of corpus text — have
zero entities and are unreachable by any `MENTIONED_IN` walk from any seed at any
damping. Mean length 707 chars, max 2,210, so these are not only junk fragments.
Honest slide material: *the graph cannot see 6% of this corpus and vector search
can*, which is the argument for union rather than replacement.

**Decision: do not re-chunk to one chunk per diary entry.** Entry boundaries are
*already* in the graph — every chunk carries non-null `date` and `author`, 1,275
(date, author) entries over 2,913 chunks, 436 already single-chunk — so
entry-level grouping is a `GROUP BY`, not a rebuild. And entry-level chunks would
be far too long for this extractor: mean 699 words, p50 561, p90 1,390, max
4,664. It fails either way you build it:

- **re-extract at entry level** → ~6 entities regardless of length, so
  words-per-entity goes from 60 to 200+ and the 5× advantage drops under 2×
- **re-attach existing mentions** → same entity count, blurrier embedding
  (p90 486 → 1,390 words), no gain

More blur without more pointers is the one combination the design cannot use.
Re-chunking would also **invalidate section 4 completely** — co-occurrence *is*
chunk co-membership — collide with `lewisclark`, and force a re-embed.

**Better idea, and it is a slide: separate the retrieval unit from the context
unit.** Retrieve at chunk granularity where the embedding is sharp and entities
are dense, then expand the winners to their sibling chunks in the same entry
before handing context to the LLM. Strictly more than entry chunking, no rebuild,
nothing invalidated.

**One cleanup worth doing:** 400 chunks are under 100 words and some are clearly
chunking damage — `'===='`, `'side are lowest and more distant from the
river.'`. Fix it the way `flag_generic_locations.py` does: add a flag, filter at
query time. Additive, changes no existing co-membership measurement, and keeps
`'===='` out of a live candidate list.

#### 10. The gold set is broken worse than the Progress table said — this blocks section 8

`verify_questions.py` reports 4 unresolved labels. It **passes with ✓** on labels
that resolve to near-empty decoy nodes:

| gold label | resolves to | should be |
|---|---|---|
| `ELK` | Supply, **11** mentions | `CERVUS CANADENSIS` (439) |
| `BISON` | AnimalSpecies, **3** | `BISON BISON` (330) |
| `SALMON` | Supply, **13** | `ONCORHYNCHUS CLARKII` (45) + `TSHAWYTSCHA` (30) |
| `GREAT FALLS` | Event, **2** | `GREAT FALLS OF THE MISSOURI` (26) |

Fixing `food-sources` alone took it from 3 conjunction-bearing passages to
**162**. And **9 of 22 gold labels are ambiguous** — several nodes share the
name — including `SHOSHONE` (NativeNation:192 vs Person:1), which is the section
7 bug verbatim, and `SACAGAWEA` (Person:64 vs NativeNation:1).

**The defect is that `✓` means "a node with this name exists", not "the right
node".** It cannot catch a decoy. The fix is the mention-count prominence prior
that `resolve.py` already got and this script never did — see finding #8.

Two labels are genuinely thin rather than mis-resolved: `NEZ PERCE` has 2
mentions (the journals say *Chopunnish*, split across `Person` nodes) and
`PACIFIC OCEAN` has 4. Those are real extraction gaps that bound every strategy,
and `Supply` (634 nodes) has **no embeddings and no vector index** at all.

`questions/questions.yaml` was **not edited** — the corrected mapping was local
to the experiment, since that file feeds section 8's benchmark and Step 5 is not
section 5's scope.

#### 11. Two decisions taken

**No resolved-vs-unresolved second database in section 5.** The comparison would
be `neo4j` vs `rawluna`, which differ in *extraction model* too (39% fewer
mention edges) — confounded, and section 4 already retracted one measurement for
exactly that. The free version is better: the hub table shows `DREWYER` at #7
with 265 mentions while `GEORGE DROUILLARD` is a separate node, and the entity
seeds visibly include both `SACAGAWEA` nodes. One sentence, no second database.

**Numbers *do* go on section 5's slides**, which does not contradict section 4.
Section 4's numbers needed the gold set to mean anything; these are measurements
of the algorithm's own behaviour — cross-question overlap, hub mass, damping
sweep, blend sweep, `alpha=1.0` identity, projection and query latency — exact,
reproducible on stage, and carrying no judgement about whether a retrieved
passage is correct. Every *accuracy* claim still waits for section 8.

#### 12. Caveats that must travel with every number above

- **The relevance signal is a proxy.** "Mentions ≥2 gold entities" is not
  "answers the question." These numbers support *cosine does not retrieve
  conjunction*; they do **not** establish that those passages are the right
  answers. Same discipline as section 4's gold-set note.
- **Thirteen questions is a small sample**, and one contributes nothing. Treat
  blend-weight differences of 1–3 top-8 hits as noise.
- **Findings 1–5k are `neo4j`; the slides are `lewisclark`.** The predicted
  re-measurement happened (2026-09-07): finding 5o holds the migrated numbers
  and the shifts were real — the hub table changed its headline (Lewis top at
  28.3%), the ladder shallowed (2.84 → 0.47 vs 4.47 → 0.07), two receipts had
  to be replaced outright. The `neo4j` tables above stay as history; quote 5o
  and `section-05-slides.md`.
- The `control` question `keelboat-return` is *not* harmed by the blend (cosine
  1 in top-8 at median 164; blend 0.8/0.2 gives 2 at median 153), but this must
  be re-confirmed at whatever weight ships — it is the outline's own honesty
  check.

### Section 6 findings — working notes, not slide material

Conditions for every number below: local Desktop DBMS (heap raised to 8 GiB
max after the 2026-09-07 OOM — projections rebuilt in <300 ms), database
`lewisclark`, `NEO4J_DATABASE=` passed explicitly, home database untouched.
`lc-retrieval` projects at 8,139 nodes / 63,836 rels; communities are detected
over all three relationship types — including `NEXT_CHUNK`, deliberately: an
"episode" is exactly a stretch of consecutive entries plus the entities they
share, and the chain is what lets the algorithm see it.

#### 6a. Validated on `lewisclark` — and seeded Leiden replaces Louvain as the *measured* partition (2026-09-07)

`communities.py` and `demo_communities.py` had never run against `lewisclark`.
They now do, live: ~47 communities covering all 2,913 chunks, modularity 0.56,
and the themes table reads as a table of contents someone could have written —
a Mandan-winter community, a Columbia-descent fishing community, a
trade-goods community (`GUNS, AXES, MERCHANDIZE, FLOUR`), a Shoshone-horses
community. Topic extraction at zero *additional* token cost — the community
step itself is token-free; unlike Blumenfeld's natively-linked wiki corpus,
ours rides on mention edges the extraction pass already paid for.

**But Louvain redraws its partition every run.** Three observed runs gave 46,
48 and 37 communities (modularity moved only 0.560 → 0.562), and the
community-capped illness window kept only 5–6 of its 8 chunks across two
process restarts. Nothing in the pipeline seeds it; GDS Louvain accepts no
seed. **GDS Leiden does** (`randomSeed`, which requires `concurrency=1`), and
with a fixed seed the *entire measurement* — every window of finding 6c — is
byte-identical across processes, verified by diffing two full runs. So:

> **Leiden is the measured partition and the demo default; Louvain is the
> robustness check.** Their capped windows agree 8/8 on trade-goods and
> food-sources in every observed Louvain draw, and 6–7/8 on illness across
> three draws (it redraws). This repo's discipline is
> that measurements re-run byte-for-byte; an unseeded partition cannot deliver
> that, and a live demo whose "themes" differ every run reads as hand-waving
> from the stage.

`CommunityConfig` gained `algorithm` ("louvain"/"leiden"), and `detect()` now
runs in **mutate** mode — membership lands as a property on the in-memory
projection (never the database) and is streamed back, so `conductance()` and
every window cap in a process read the *same run* rather than a fresh draw.

#### 6b. Louvain's textbook flaw, caught live — and Leiden's guarantee has an asterisk (2026-09-07)

> **Off-stage as of 2026-09-07 — Nathan's call: the talk covers Leiden alone.**
> The Louvain half of this finding is Q&A backup and the reason the demo runs
> Leiden; only the Leiden asterisk (one 24-node community split 13/11 — verify
> with per-community WCC) and the conductance numbers get slide time.

The outline's Leiden pitch ("Louvain can emit internally disconnected
communities") was a claim waiting for a measurement. Measured, per community:
filter the projection to the community's nodes and run WCC (also
cross-checked against a pure-Python union-find over the same edge predicates —
both methods agree):

| partition | internally disconnected | worst case |
|---|---|---|
| Louvain (one draw) | **2 of 48** | a **1,089-node** "community" whose members are not mutually reachable |
| Louvain (another draw) | 1 of 37 | — |
| Leiden (seeded) | **1 of 47** | 24 nodes, split 13 / 11 |

The Louvain number is the slide: a third of the projection's nodes sitting in
one community that is not actually connected inside. But the honest surprise
is the third row — **GDS's Leiden implementation also emitted one disconnected
community** on this graph (not a `maxLevels` truncation; it converged at 6 of
10 levels, and 30 levels reproduces it). The guarantee as implemented is not
absolute. The takeaway stays what the section preaches: *verify, don't trust
the algorithm's name* — connectivity per community is one WCC call.

**Conductance behaves as the ki-post thresholds predict.** Median 0.27 across
the partition; 35 of 47 communities ≤0.35 ("tight theme"), zero ≥0.60. The
communities the thematic windows touch run 0.25–0.46 — cohesive enough to cap
on, and the check costs one `gds.conductance.stream` call against the same
mutated property.

*(Also fixed in passing: `baseline.py`'s graph-context query did
`toString(r.date)`, and on `lewisclark` 364 relationships carry date*
**arrays** *— section 4's merge combined parallel relationships' conflicting
dates. Section 4's footprints keep turning up in later sections' plumbing,
which is worth one aside from the stage.)*

#### 6c. The measured cold open: capping the walk repairs 5l's illness collapse — and is a provable no-op where the walk already wins (2026-09-07)

5l ended with the walk collapsing `illness-and-injury` onto one week at Long
Camp and named the fix: *cap the window per community*. The critical design
point, easy to get wrong: the cap must apply to **the expansion walk's
ranking**, not to cosine's — `communities.retrieve` capped only a vector
slate, so `diversify()` now caps *any* strategy's wide slate (the walk runs at
k=50, the cap walks that ranking admitting ≤2 chunks per community).
`scripts/measure_communities.py` measures it in 5l's exact form — same three
thematic questions, same window stats, fresh read-pack
(`results/communities-lewisclark.md`) with 5l-judged chunks flagged — so the
hand reads transfer. `expand` reproduces 5l's windows byte-for-byte first.

| illness-and-injury | vs vector | entities | near-dup pairs | months | communities |
|---|---|---|---|---|---|
| vector | — | 64 | 0 | 4 | 3 |
| expand (5l's window) | 2/8 | 68 | 2 | **1** | **1** |
| **expand+community** | 3/8 | 86 | **0** | **4** | **5** |
| vector+community | 5/8 | 60 | 0 | 5 | 5 |

**All eight of the walk's chunks sit in one community.** The collapse 5l
diagnosed by reading dates is visible as a single community id — the failure
is *structural, and the structure the fix needs is already computed*. Capped,
the window keeps Long Camp's two strongest chunks (the child + Bratton's
sweat-hole, the chief + imposthume) and refills the freed slots from the same
blended ranking.

**The hand read of what came in** (new chunks judged by reading; the rest
carry 5l's judgements):

- **Lewis shot through the thigh by Cruzatte, 1806-08-12** (cosine 21) — the
  expedition's most famous injury, absent from *every* 5l window; the walk had
  it reachable and the collapse had buried it. The window's best promotion.
- **The Fort Clatsop sick-list, 1806-02-22** (cosine 44) — "Gibson, Bratton,
  Sergt. Ordway, Willard and McNeal are all on the recovery… something I
  beleive of the influenza." One of the three passages 5l explicitly listed as
  *gone* under the collapse, back in the window.
- The June 8 recovery report (cosine 104): Bratton "no longer an invalid",
  the chief bearing his own weight — legitimate closure of the medical arc,
  though it extends the Long Camp storyline from a different community.
- The costs: two May-1806 native-doctoring passages (cosine 79 and vector's
  #1) — treating Nez Perce patients, 5l's "topic-match-wrong-subject" class —
  now hold two slots. Diversity of *episode* is not diversity of *subject*.

**Where the cap is a no-op, it is provably a no-op.** On `trade-goods` and
`food-sources` — the walk's two clean 5l wins — the capped window is
**byte-identical** to the uncapped one, because those windows already span 6
communities. The cap only bites where the failure is. That is the argument
for leaving it on: it is not a trade-off knob, it is a guard rail.

**The honest bound, and it is mechanical.** The community grain is coarser
than the episode grain. Community 23 is "the corps members" — 286 chunks
spanning the whole expedition — and it contains Long Camp *and* the Sept-1805
Lolo starvation-sickness passages. The cap's two slots for community 23 go to
Long Camp (blend ranks 1–2), so the Sept-1805 dysentery chunk that sits at
cosine rank 2 — in vector's window! — is **locked out** of the capped expand
window. Capping fixes the collapse exactly insofar as the collapsed episode's
competitors live in *other* communities. Second bound: the cap can only
choose from the slate it is given — `vector+community` backfilled one
plainly irrelevant chunk (damaged powder canisters) from cosine's deep slate.
A cap diversifies a ranking; it cannot make the ranking deeper than it is.

*(Discipline notes: three questions, windows of 8, judged by reading against
5l's read-pack; month/near-dup/entity/community counts are descriptive
corroboration, not verdicts. Cap settings are the shipped defaults —
`max_per_community=2`, `k=8`, resolution 1.0, deliberately untuned; after
5d-quinquies, no knob sweeps against hand-read outcomes. Leiden seed 42
throughout; single corpus. `vector+community`'s month gain (4→5) rides partly
on wrong-subject and one irrelevant chunk — the stat without the read would
oversell it, same lesson as ever.)*

**What section 6 gets to say:** the walk's conjunction-seeking is
episode-seeking (5l), the episode is *visible in the graph* as a community,
and a two-line cap over the algorithm's own output repairs the failure without
touching the two questions the walk already wins. Retrieval diversity is not a
reranker heuristic here; it falls out of the same structure that ranked the
chunks. And the section's honesty beats — Louvain redrawing, Leiden's
asterisk, the corps-members community being coarser than an episode — are all
one-query demonstrations, which is the talk's whole thesis in miniature.

### Design notes not yet folded into the sections

- **Entity retrieval split, decided 2026-09-07 (not yet built):** fulltext-only
  for Person / Place / WaterBody / NativeNation (queries are name-shaped, and
  disambiguation folded the descriptive Person forms into aliases); vector
  embeddings only for AnimalSpecies / PlantSpecies / Taxon / Event (taxonomy
  replaced the user's vocabulary with binomials, and Event queries are
  paraphrases). **Idea for later:** keep `person_embeddings` as a fallback
  index the agent consults only when fulltext returns empty, for pure-paraphrase
  person queries with no alias token overlap ("the enslaved man on the
  expedition" → York). None of the current 14 demo questions needs it.
- ~~**Section 4 has a full implementation design**~~ — **built.** Candidate
  pairs are carried as node-id tuples, projected via `gds.graph.cypher.project`
  over `UNWIND $pairs`, and real `gds.wcc.stream` runs against them. Confirmed
  in the client source that Cypher projections run with `QueryMode.READ`, and
  every other query goes through a new `config.read_query()` that opens a read
  transaction — so a write is rejected by the *server*
  (`Neo.ClientError.Statement.AccessMode`), not merely avoided by the code. The
  write audit at the end of every run diffs node/relationship counts, per-label
  and per-type totals, and six sampled `aliases` arrays. It reports zero changes.
- ~~**Gold set for section 4**: the ~40-name roster~~ — **replaced, and the
  reason is itself a slide.** The roster uses modern canonical spellings; the
  graph uses the journals'. Ten of the 41 roster names do not exist as nodes at
  all — there is no `PIERRE CRUZATTE` node, there are eleven differently-spelled
  ones. `questions/corps_members.yaml` now carries 35 **identities** (a person
  plus every surface form of them actually observed in the graph), 29 malformed
  nodes and 4 uncertain ones excluded from scoring, and 9 hard negatives. That
  makes precision *and* recall computable against a real denominator: 24 corps
  members are still split across multiple nodes, giving 252 duplicate pairs the
  pipeline should have merged and did not.
- ~~**Known compatibility risks**~~ — **all resolved.** See Step 0 results above.


### Section 7 findings — working notes, not slide material

All measured on `lewisclark` (2026-09-07). Method: `results/make_paths_readpack.py`
ran Yen's at k=8 for four anchor pairs and dumped **every hop of every route with
every receipt's full passage text** — 22 unique routes, 85 distinct passages, all
hand-read. `results/` is gitignored; the read-pack lives only on this machine and
regenerates in ~10 s. A fresh path query answers in ~220–470 ms end to end.

#### 7a. The k claim was backwards — on a typed graph, co-occurrence lives at HIGH k

The outline asserted "the single shortest path is usually trivial co-occurrence;
the 2nd/3rd carry the mechanism." Hand-reading every route says otherwise, and
the reason is structural: Yen's here walks the **extracted typed relationships**
(`RELATED` projection), not a co-occurrence graph, so a 1-hop path is a strong
semantic claim, not an incidental one.

- **Pairs with a direct extracted edge get the mechanism at k=1.**
  Sacagawea→Shoshone: k=1 is `MEMBER_OF`, and its receipt array contains both
  the kinship-dependence passage ("our only dependence for a friendly
  negociation with the Snake Indians on whom we depend for horses") and the
  explicit membership statement ("they were not of her nation, the Snake
  Indians"). Charbonneau→Hidatsa: k=1 is `INTERPRETED_FOR`, receipt = the
  actual hiring scene at Fort Mandan (1804-11-04). For the questions the bank
  pins to these anchors, k=1 *is* the answer.
- **The mechanism moves to k>1 exactly when the graph lacks the edge.**
  Sacagawea→Cameahwait are brother and sister; the graph has **no sibling
  relationship of any type** (checked: zero SIBLING/BROTHER/SISTER/FAMILY rel
  types corpus-wide) — the extraction bound, §5o's keelboat pattern again. The
  recognition scene survives only as an Event node: k=1 routes through "both
  knew Lewis", k=2 through the shared nation, and **k=3 is both anchors
  `PARTICIPATED_IN` → MEETING OF THOSE PEOPLE — both hops citing the SAME
  chunk, `dd08cca`, the passage that says "the Indian woman, who proved to be
  a sister of the Chif Cameahwait."** One passage is the entire explanation.
- **Higher k drifts INTO co-occurrence, not out of it.** The 3-hop tie class is
  shared-hub and shared-commodity routes: both acquired a FLAG / SHIRT /
  TOBACCO / HORSE / CORN (Supply hubs), both observed the white apple or
  quawmash (plant hubs), both met Lewis. The claimed direction is inverted.

**The honest re-statement, and it is better on stage:** k does not buy you a
*better* path at position k — all three 2-hop Cameahwait routes are exact cost
ties, and Yen's has no notion of which one explains. **k buys the set**; the
reader (or the LLM the context is handed to) picks the mechanism. That is also
the honest reason the k=3 position can't be sold as a ranking — see 7e.

#### 7b. Receipts hold — and where they don't, that's the demo

"Every hop hands back the journal passage that evidences it" survives the audit:
most hops' receipts genuinely evidence the relationship. The exceptions are
extraction errors that **only reading the receipt catches**, which turns the
fidelity hazard into the section's strongest material:

| hop on a live route | what the receipt actually says |
|---|---|
| `SACAGAWEA -[GUIDED]-> MERIWETHER LEWIS` (her only GUIDED edge) | Clark's journal, 1806-07-06 — she guided **Clark** on the Yellowstone leg; Lewis was elsewhere. Wrong captain. |
| `CAMEAHWAIT -[MEMBER_OF]-> HIDATSA` | the receipt says the Hidatsa **attacked** his people ("killed or taken prisoners"); he is Shoshone. The edge asserts the opposite of its own evidence. |
| `NEESH-NE-PAR-KE-YOU-OOK -[MEMBER_OF]-> SHOSHONE` | Cut Nose is Nez Perce; the passage has "The Shoshone man" *traveling with* him. |
| `LEWIS -[MET_WITH]-> HIDATSA`, receipts [4] and [5] | both are the 1806 Two Medicine **Blackfeet** encounter — the journals call both nations "Minnetares", and the extractor filed the fight under the wrong one. |
| `SHABONO -[INTERPRETED_FOR]-> SHOSHONE`, receipt [1] | the passage says his **wife** was the interpretess for the Shoshoni; he was for the Crow. |

The audit verdict is not "the receipts are unreliable" — it is that **a path
without receipts would have asserted all five of those falsehoods with nothing
to check them against.** The receipt is the audit mechanism. (And the LLM that
gets the context sees the passage, not the edge label, so the wrong edges are
survivable at generation time.)

#### 7c. Hazard (a) measured: the `[0]` receipt pick was not honest, and the arrays can't even be zipped

403 relationships carry list-valued `chunkId` from §4's merges (OBSERVED alone:
260, mean 7.7 receipts, max **113** on one edge). Two measured facts killed the
old `[0]`-element display:

1. **`[0]` hid the best receipt.** On the demo's own k=1 hop
   (`SACAGAWEA MEMBER_OF SHOSHONE`, 6 receipts), element [0] was the *implied*
   receipt (the sulphur-spring passage) while the **explicit** one ("not of her
   nation, the Snake Indians") sat at [1].
2. **The arrays are ragged, so `date[i]` does not belong to `chunkId[i]`.**
   `LEWIS MET_WITH CAMEAHWAIT` carries **11 chunkIds against 8 dates**; checked
   element-wise, alignment holds at [0]–[1] and is garbage beyond. Any display
   that zips the two arrays cites real passages under wrong dates.

Shipped fix in `paths.py`: every hop keeps **all** receipts, ordered by the
receipt chunk's own date; the hop's displayed date comes from the chunk, never
from the edge array; the demo prints `chunkId (+N more)`. Evidence assembly
selects round-robin across hops in route order (first receipt of every hop of
route 1, then route 2, …) — because the two simpler schemes both failed a hand
read: `[0]`-only hid receipts (above), and all-receipts-in-date-order filled
the 8-slot cap with one merged hop's eleven council passages and **pushed the
recognition scene out of the context entirely**. Selection is route-priority;
display stays chronological.

#### 7d. Hazard (b) measured: the structural fallback returns nothing, silently

`BELONGS_TO` is the only relationship type with no chunkId — 1,172 edges, all
taxonomy. The fallback ("a passage where both endpoints are mentioned
together") returns **zero passages for every taxonomy hop**, because Taxon
nodes have no `MENTIONED_IN` edges at all — verified: URSUS AMERICANUS ~ Ursus
co-mention count is 0. So a route through the taxonomy arrives with no receipts
and contributes nothing to context, and nothing warns you. The demo now prints
`structural — no receipt` instead of a blank.

The taxonomy route is also nearly unreachable: between the two bear species,
`URSUS AMERICANUS → Ursus → URSUS ARCTOS HORRIBILIS` — the one route that
actually says "these are both bears" — first appears at **raw k=40**, behind 39
paths of the form "someone once saw both animals." Second fallback gotcha, noted
for Q&A: the co-mention query matches endpoints **by name**, and duplicate names
exist (two SHOSHONE COVE nodes), so a fallback receipt can cite the other node.

#### 7e. Yen's on-stage mechanics: duplicates eat k, and tie order is not stable

Both measured, both now handled in `paths.py`:

- **Parallel relationships are distinct paths to Yen's.** Raw k=25 between the
  bear species returned **7 distinct node sequences** — one sequence came back
  12 times (its hops have that many parallel extracted edges). Ask for 8
  routes, get 5–6. Fix: over-request 5×, dedup on node sequence.
- **Ordering among equal-cost routes is nondeterministic.** Three consecutive
  identical calls returned the three tied 2-hop Cameahwait routes in three
  different orders — and at fixed k the *membership* of the 3-hop tail differed
  between invocations minutes apart. Fix: deterministic tie-sort
  (cost, hops, route text). What that buys, precisely: any cost class the raw
  request enumerates completely (the 1- and 2-hop classes on every demo pair)
  is stable every run; a class bigger than the leftover budget (3-hop ties
  number in the dozens) is a *sample* — order stable, membership not. The demo
  script talks over the head of the list and treats the tail as "more routes
  exist at this cost." The k=3 recognition-scene position is stable because the
  cost-2 class has exactly three members; it is an artifact of the shipped
  tie-sort, not a relevance ranking, and the slide must not claim otherwise.

#### 7f. §4 breaks §7, three ways — all live on `lewisclark`

1. **The Step-0 resolver incident reproduces with a new decoy.** The stray
   1-mention `SHOSHONE :Person` that emptied every path query on `neo4j` does
   not exist here — but `SHOSHONE BOY :Person` (1 mention) outscores the real
   `:NativeNation` (150 mentions) on fulltext, **8.19 vs 6.48**, for exactly
   the Step-0 reason (Lucene rarity ≠ corpus prominence). The mention-count
   near-tie break holds — resolution lands on the nation — verified, not
   assumed. Same disease, different patient, fix generalizes: that is the
   one-sentence §4 callback.
2. **Unmerged duplicates fabricate explanation routes through the anchor's own
   alias.** A live k=8 route: `SACAGAWEA -[OBSERVED]-> PEDIOMELUM SP. (the
   white apple) <-[OBSERVED]- HIS WIFE -[INTERPRETED_FOR]-> SHOSHONE` — every
   hop receipt-faithful (both "women" gather white apples on the trail; the
   1806-07-03 passage really does say the interpretess served the Shoshoni),
   and the route is still a tautology: **HIS WIFE is Sacagawea**, the §4
   bridge node the consistency gate deliberately refused to merge (3d/3g).
   Same pattern doubled elsewhere: SHABONO vs TOUSSAINT CHARBONNEAU spawn
   parallel route families, and DREWYER (297 chunks) vs GEORGE DROUILLARD (84)
   put the §5k unmerged pair on the route table. The graph explains Sacagawea's
   Shoshone tie *via Sacagawea under another name*, with receipts.
3. **Fulltext-first resolution misroutes species anchors.** "Grizzly Bear"
   resolves to `BEAR CREEK` (WaterBody, 2 mentions) — token overlap in the
   Place index short-circuits before the semantic labels are tried — and every
   path query from it returns empty. The docstring's own example failed live.
   Demo fix: `--from-label/--to-label` pin the resolver
   (`--from-label AnimalSpecies` → BEAR, 121 mentions, routes return).
   `resolve.py` itself left untouched — §5's measurements run through it.

#### 7g. The two-step landing: 5m's flagship completes here

5m measured: "What do we know about Sacagawea's brother?" defeats every one-shot
retriever (no strategy puts a target in the top-8), and the pure walk's rank-4
chunk hands the asker one thing — the **name** Cameahwait. §7 is the second
step, and it is not a better ranker, it is a different query: pin both anchors,
ask for routes. The k=3 route lands both feet on `dd08cca` — the recognition
scene, the single passage in 2,913 that states the sibling relationship — in
~220 ms, deterministically, and the round-robin evidence assembly keeps it in
the 6-passage context. The walk performs name discovery; the path query performs
explanation; neither can do the other's job (the walk ranked `dd08cca` nowhere
near the window, and the path query cannot start until something names the
second anchor). That is the §5→§7 arc in one sentence, with §6's hand-off ("the
system can hand you eight diverse, relevant passages and still not tell you how
two things are connected") as the bridge between the steps.


## Context

Nathan is giving a 60-minute KCDC session on using graph algorithms to improve
RAG context retrieval and ranking. The submitted abstract promised
query-time work (personalized PageRank reranking, hybrid similarity+structure,
path exploration, performance comparisons). The outline he actually wants also
covers **node similarity and community detection for entity resolution**, which
is build-time work.

The reframe that reconciles them, and which this outline is built on:

> Graph algorithms serve RAG at two stages. At build time they make the graph
> good enough to retrieve from. At query time they decide what comes back.
> Skip the first and the second produces garbage.

Audience skews new (some returners from last year's *RAG Has a Relationship
Problem*), so foundational material gets a fast pass with a pointer to the
[community days repo](https://github.com/smithna/corps-of-discovery-graph-rag)
rather than a rebuild.

Framing principle Nathan set: **lead with a problem, solve it with an
algorithm.** Attendees don't know they want graph algorithms, and some of them
genuinely don't need them. Every section opens with a failure they've felt.

Two sources to weave in: the NICD paper (`nicd-reducing-hallucinations-graphrag.pdf`)
and the Neo4j blog on [scaling Karpathy's LLM wiki](https://neo4j.com/blog/agentic-ai/scaling-karpathy-llm-wiki-graph/).
The blog cites the paper, so they're one thread.

A third source, **not evidence but good framing**: Arijit Ghoshal's
[*When Does Graph RAG Actually Add Value?*](https://medium.com/@arijitghoshal222/when-does-graph-rag-actually-add-value-a-hands-on-experiment-2f61a0c31736).
Four retrieval setups — plain vector RAG, graph-only, graph RAG, and a frontier
model handed the whole corpus — over the same questions. Its useful contribution
is a vocabulary: graph RAG helps with **reasoning problems** and does close to
nothing for **coverage problems** ("retrieve all the relevant text"). That is the
same line section 8 already draws with its control questions, said more crisply.

**Do not put its numbers on a slide.** Two documents, LLM-as-judge scoring on a
1–10 scale, one run. It is an honest blog post about a weekend experiment and
says so itself. It belongs in the further-reading slide and as a phrase Nathan
borrows — not in the evidence table next to a 510-question study.

**This plan delivers the outline.** Code gets implemented section by section
afterward, in the order given at the bottom.

---

## The outline

Budget: **53 minutes of content + ~7 for Q&A.**

### 0. Cold open — the failure (3 min) · 0:00

No title slide theory. Open with the pipeline breaking.

Run a Lewis & Clark question through plain vector RAG and show it returning
confident, fluent, *incomplete* context. The passages all look relevant. The
answer is still wrong, because what was needed sat one hop away and never
scored high enough to make the window.

> "Nothing here is a bad embedding. The retrieval did exactly what it was
> designed to do. That's the problem."

### 1. What is a graph? (3 min) · 0:03

Deliberately fast. Nodes are things, relationships are how they connect, and
the one distinction that matters: **relationships are stored explicitly, not
computed at query time by matching IDs.**

One diagram. Point at the community days repo for the longer version and move
on — the algorithms are what was sold.

### 2. What is Graph RAG — and does it actually work? (7 min) · 0:06

The architecture in one slide: vector index and knowledge graph in the same
database, both available to the same retrieval step.

Then the evidence, handled honestly:

**From the Karpathy wiki post** — the framing line is *"give the agent a
structure it can navigate, not just a box it can search."* Graph navigation
supplies verbs a vector store doesn't have: traversal, paths, centrality. Also
worth one beat: **community detection over link structure costs zero tokens** —
on his wiki corpus the links are native, so no LLM touches that build step. On
ours, say **zero *additional* tokens**: the community step itself is
token-free, but the mention edges it reads came from the extraction pass
earlier sections already paid for. That's the thesis for section 3.

**From the NICD paper** (510 MoNaCo questions, 28k Wikipedia docs):

| | Vector RAG | Vector+graph | Zero-shot |
|---|---|---|---|
| Factual correctness (precision) | 0.15 | **0.36** | 0.43 |
| Factual correctness (recall) | 0.13 | **0.33** | 0.39 |
| Fine-grained truthfulness | 35 | **63** | 40.5 |
| Total tokens (median) | 41,694 | 45,695 | 1,108 |

Vector+graph roughly **doubles** precision and recall over vector-only, and
wins fine-grained truthfulness outright, for ~9% more tokens.

Say the awkward parts out loud, because they're more interesting than the
headline and someone will look it up:

- **Zero-shot beats both** on factual correctness and answer relevancy — MoNaCo
  is built on public Wikipedia the model already memorized. The authors say so.
- **Coarse truthfulness actually favors plain vector RAG** (−31 vs −49),
  because vector RAG refuses to answer more often. Refusing isn't winning.
- **The paper was funded by Neo4j**, disclosed in their conflict-of-interest
  statement. One sentence, from the stage, costs nothing. If it comes up in
  Q&A, the honest follow-up is that independent write-ups reach compatible
  conclusions on the reasoning-vs-coverage split — Ghoshal's is on the further
  reading slide — they're just far smaller. Thin but independent, next to
  thorough but funded.

**Then the gift.** The agent in that study had a shortest-path tool available.
It was **never called, not once.** LLMs are biased toward tools resembling what
they saw in training, so it fell back to vector search even when the system
prompt pushed it toward graph tools.

> "So the lesson isn't 'give your agent graph tools.' It's: put the graph
> algorithms in the retrieval path, deterministically, where the model doesn't
> get a vote."

That line is the hinge of the whole talk. Everything after it is *what to put
in that path.*

### 3. Roadmap (1 min) · 0:13

Four failures, four algorithms, two stages.

| Stage | Failure | Algorithm |
|---|---|---|
| Build | Your entities are a mess | Node similarity + WCC |
| Query | Your ranking is wrong | Personalized PageRank |
| Query | Your context is redundant | Louvain / Leiden |
| Query | You can't explain the answer | Yen's k-shortest paths |

### 4. "Your entities are a mess" → node similarity + WCC (9 min) · 0:14

> **Editorial decision (Nathan): no precision/recall numbers on these slides.**
> The gold set is a reasonable hand-built reference, not ground truth — see
> "What the gold set is and isn't" below. The section is built on the Sacagawea
> example instead, which is concrete, checkable on screen, and matters to this
> corpus. Aggregate metrics stay in the working notes for our own use.

**The failure.** In the journals, William Clark is `CLARK`, `CAPT. CLARK`,
`WILLIAM CLARK`, `Capt Clark`, `Wm. Clark`. Every one is a separate node.
Retrieval for Clark silently misses most of Clark. No error, no warning — just
quietly incomplete context, which is the worst failure mode RAG has.

**Then make it personal to the corpus.** Sacagawea is named directly in **8
chunks**. She is referred to in far more. Ask the graph for Sacagawea and you
get 8 chunks' worth of a woman who is present through the entire expedition.

**The naive fix and why it breaks.** String matching gets you a long way and
then falls off a cliff. The journals spell Charbonneau as *Chabonah* —
double-metaphone catches that (XPN vs XRPN). Show the ladder working. Then show
what it is up against here:

```
SACAGAWEA · INDIAN WOMAN · THE INDIAN WOMAN · OUR INDIAN WOMAN
THE INDIAN WOMAN WITH US · SQUAR · THE SQUAR · THE SQUAW · HIS SQUAR
SQUARWIFE · SQUAR INTERPRETRESS · SQUAR WIFE TO SHABONO · JANEY
THE WIFE OF SHABONO · WIFE OF SHABONO · SNAKE INDIAN WIFE
INTERPRETERS WIFE · OUR INTERPRETER THE SNAKE WOMAN
```

Nineteen nodes, one woman. **No string algorithm will ever connect `SACAGAWEA`
to `THE SQUAR`**, because there is nothing there to connect. The letters have
run out.

**How the corps repo solved it — and why that should bother you.** With
`enrich_sacagawea.py`: a script that scrapes a curated list of her surface forms
from **lewis-clark.org**. It works. It is also a third-party website hard-coded
into a build pipeline, and it exists only because someone had already done this
by hand for this specific expedition. There is no lewis-clark.org for your
corpus.

**You have more information than you think.** Two names appearing alongside the
same people, places and dates are probably the same entity — and that signal is
already in the graph, at zero token cost.

- Project entity↔entity co-occurrence weighted by shared chunk count
- `gds.nodeSimilarity.filtered` with **OVERLAP** — one diagram, below
- Union it with the string and alias signals

**One visual, then move on.** No metric comparison table — there isn't time, and
it isn't the point. Draw the two neighbourhoods as overlapping circles, with the
real numbers from this corpus:

```
   SACAGAWEA                        INDIAN WOMAN
   appears alongside                appears alongside
   51 other entities                174 other entities

            ╭──────────╮
            │  33      │╭────────────────────────╮
            │   SACA   ││  18 shared  │   156    │
            │          │╯  CAMEAHWAIT ╰──────────╯
            ╰──────────╯  HIDATSA · DREWYER · HORSES
                          CAMASSIA QUAMASH · CANOES …

   OVERLAP  = 18 / 51  = 0.35   ← divide by the SMALLER circle
   JACCARD  = 18 / 207 = 0.09   ← divide by EVERYTHING
```

The whole idea in one line: **a rare name and a common name for the same person
have lopsided neighbourhoods, so divide by the smaller one.** Jaccard divides by
the union and punishes her for being rare; overlap asks the question we actually
mean — *is the rare name's world contained in the common name's?*

Then one throwaway sentence and move on: *"Overlap fits this corpus because the
duplicates are lopsided. If yours aren't, try the others — GDS gives you cosine
and Jaccard on the same call."* That is the whole treatment. No table, no
benchmark.

*(Footnote for us, not the slide: the implementation also weights each shared
neighbour by inverse chunk frequency, so a shared mention of Charbonneau counts
far more than one of Lewis. The real score is therefore not the raw set ratio
above — the diagram teaches the shape of the formula, not the arithmetic GDS
runs.)*

**The payoff, live.** Running that on a graph built *without* the scraper, the
algorithm proposes candidates, the LLM adjudicates them, and WCC closes them:

```
INDIAN WOMAN + INTERPRETERS WIFE + SACAGAWEA + SQUAR INTERPRETRESS
+ SQUAR WIFE TO SHABONO + THE INDIAN WOMAN + THE INDIAN WOMAN WITH US
+ THE SQUAR + THE SQUAW + THE WIFE OF SHABONO
```

Ten surface forms, one entity, **derived entirely from how the corpus uses the
names.** No website. Point out that the hub of the cluster is `SQUAR
INTERPRETRESS`, a node appearing in a *single chunk* — one passage puts it in
company nothing else shares, and that is enough.

> **The line:** the graph found her the way a reader does — not by how the name
> is spelled, but by who she is always standing next to.

**Say what it costs.** The graph signal on its own is *bad* — it proposes
hundreds of wrong pairs for every right one, and anyone who ships it unfiltered
gets nonsense. That is not a defect, it is a division of labour:

> **Recall is what the algorithm is for. Precision is what the adjudicator is
> for.** The algorithm's job is to shrink an O(n²) problem — 811 people is
> 328,455 possible pairs — down to something an LLM can afford to read. It does
> not decide anything.

**WCC, and what it is actually for.** Sharpen this, because it's usually taught
wrong: WCC answers *"are these connected at all"*, not *"are these a topic."*
Its job here is **transitive closure** — A≈B, B≈C, therefore one entity. The
Sacagawea cluster is built from ten pairwise judgements; no single one of them
sees the whole identity. WCC is what turns them into one node.

And show the danger in the same breath: one wrong edge welds two identities
together permanently. `GEORGE DREWYER + GEORGE DROUILLARD + GEORGE SHANNON` —
two correct merges and one shared given name, and Shannon is Drouillard forever.
That is why adjudication runs *before* closure, not after.

**Same algorithm, query time.** One slide: node similarity also retrieves.
"Find chunks that share entities with this chunk" is a different question from
"find chunks that sound like this chunk," and it catches things embeddings
miss. Carried into the benchmark in section 8 as the `cooccurrence` strategy.

**Demo** — validated end to end 2026-09-07, timings and conditions in finding
3h. Three acts, two databases:
- `demo_resolution.py --adjudicate --max-calls 0` on **`rawluna`** (read-only,
  2.6 s): the nineteen surface forms, live candidates, and the write audit —
  and the trap: WCC over the *confirmed* pairs still welds Sacagawea into a
  91-node component
- `tools/disambiguate_layered.py --database rawluna --max-calls 0
  --consistency-max-calls 0` (dry run, 2.2 s, 151 lines): the consistency
  layer prints `SPLIT [17 → 12]` — her clean cluster, the impostors expelled
  by name (prerequisite: one cache-filling run before rehearsal, see 3h)
- **`lewisclark`**, the applied after graph: receipts table (SACAGAWEA, 32
  absorbed forms), `Crusatte~` → PETER CRUZATTE, and `demo_paths.py` with
  dated chunk citations (project `lc-retrieval` there first)

**Take-home for this section.** Fix entity resolution before you tune retrieval,
and note that build-time work is what makes query-time work possible — the
callback section 10 lands.

### 5. "Your ranking can't combine evidence" → multi-seed PPR (10 min) · 0:23

*(Title changed and thesis rebuilt — the previous version's hub-trap centrepiece
did not reproduce against live data. Retraction and replacement in
*Section 5 findings*. **Nathan to sign off on the new title.**)*

**The failure.** Vector top-8 returns eight passages that each mention *part* of
the answer. None of them connects the parts. Cosine scores every passage against
the question independently, on vocabulary — it has **no representation for
conjunction**, and conjunction is what most real questions need.

Shown, not asserted: passages carrying two or more of a question's gold entities
*together* sit at a median cosine rank of **524 of 2,913**. Five of thirteen
questions have **none** in the vector top-8. `before-floyd-death` has exactly one
passage naming both Charles Floyd and the Missouri River, and cosine ranks it
**415**.

**PageRank in 60 seconds** — and say the honest thing while you are there. Plain
PageRank asks "what is important in this graph?", but on an undirected graph the
stationary distribution is *exactly* proportional to degree, so plain PageRank
here is **a fancy degree count**. It is not the interesting half. What is
interesting is **changing where the walk starts**: personalized PageRank
restarts at chosen source nodes and measures structural proximity to *that set*,
aggregated over every path rather than the shortest one.

**Two seed sets, over a graph with one relationship type.**

- **Entity-seeded.** Semantic-match the question against the entity embeddings,
  take the top few, weight them by match score, seed all of them. You never have
  to decide *which* tree species was meant — or which of two `SACAGAWEA` nodes is
  the real one. Seed both and let structure sort it out. **This is the section 10
  callback made visible**: argmax entity linking fails hard when resolution is
  wrong; proportional seeding degrades gracefully.
- **Passage-seeded.** Seed at the top cosine passages, which reinforces the
  entities the best semantic matches have in common.
- **Project `MENTIONED_IN` only, undirected.** It is the one relationship here
  whose direction is honestly symmetric — "entity appears in passage" is
  co-membership. Dropping `RELATED` drops the edges whose direction has no
  consistent meaning across types (`MET` is symmetric, `MEMBER_OF` is not,
  `SHOT` carries no importance semantics at all). Dropping `NEXT_CHUNK` stops
  mass leaking to passages that are merely adjacent in time.

**PPR is linear in the restart distribution**, and GDS hands you that directly.
`PPR(w₁v₁ + w₂v₂)` is *exactly* `w₁·PPR(v₁) + w₂·PPR(v₂)`, and
[`sourceNodes`](https://neo4j.com/docs/graph-data-science/current/algorithms/page-rank/)
takes **node-bias pairs** — `[[nodeId1, bias1], [nodeId2, bias2], …]` — where
the bias *is* the linear weight (verified to 7e-07). So an arbitrarily weighted
multi-seed walk is **one** call, and the whole retrieval is two: one per
structural signal.

Two measured details the docs do not state, both worth a moment on screen
because they will bite someone:

- **Biases are not normalised.** Double every bias and every score doubles. A
  flat list is identical to every bias being 1.0, so GDS gives each source node
  its own unit of restart mass — meaning a flat batched run is the **sum** of
  the single-seed runs, not their mean. Compare a batched score against an
  averaged one and you see a factor of `|S|` and conclude, wrongly, that
  linearity failed. *(I did exactly that.)*
- **Seed count is nearly free.** One call with eight sources costs 56 ms; eight
  separate calls cost 441 ms. The cost is per-call overhead, not source count.


**Keep the walk short.** Damping is the horizon: the share of walk mass within
`k` steps is `1 − d^(k+1)`. Measured, shorter is strictly better, and the value
the repo currently ships is the worst of six tested:

| damping | mass ≤ 3 steps | median rank of conjunction passages |
|---|---|---|
| 0.35 | 98% | **274** |
| 0.55 | 91% | 309 |
| 0.85 ← shipped default | 48% | **442** |

**Hybrid retrieval** — abstract takeaway #2, and the good news is that the knob
is forgiving:

| cosine / PPR | conjunction passages reaching top-8 | median rank |
|---|---|---|
| **1.0 / 0.0** | **14** | **524** |
| 0.6 / 0.4 | 22 | 323 |
| 0.2 / 0.8 | 24 | 276 |

Cosine alone is the worst row. *Any* blend lifts top-8 hits by roughly 60%, and
there is a broad plateau from about 0.9 down to 0.1 — so the honest advice is
"pick something in the middle, it is not delicate." Do **not** quote a single
optimum; the top-8 column is noisy on thirteen questions.

Also worth ten seconds: there are **two places** to combine cosine and
structure — in the *seed weights* or in the *final score* — and seeding is the
better one, because structure then operates on a semantically-informed prior
instead of fighting it after the fact.

**The hub trap** — demoted from centrepiece to a supporting finding, because
the measured version is narrower than the outline claimed but more useful. Hubs
do **not** make every question return the same passages (cross-question passage
overlap is 0/8). They dominate the *entity* side of the walk: naive entity
top-8 overlap across questions is **4.53/8**, and Meriwether Lewis is the single
top-ranked entity for the prairie-dog, Floyd and Great Falls questions. The
mechanism is worth a sentence — a hub *receives* mass from every passage that
mentions it, then sprays it across 589 passages, so **hubs concentrate at the
entity level and dissipate at the passage level.** IDF-weighting the mention
edges takes that 4.53 to **0.60**. The rule: IDF matters when the output you
consume is the entity set; much less when you only read passages off the end.

And show the top-hub table itself, because it does two jobs at once:

```
589  ODOCOILEUS VIRGINIANUS      330  BISON BISON        265  DREWYER
439  CERVUS CANADENSIS           307  MISSOURI RIVER     224  JOSEPH FIELD
377  MERIWETHER LEWIS            291  WILLIAM CLARK      192  SHOSHONE
```

The corpus is a daily record of what they shot and ate, so the deer outranks
both captains — and `DREWYER` sits at #7 with 265 mentions while
`GEORGE DROUILLARD` is a *separate node*. The hub table displays section 4's
unresolved-entity problem for free, with no second database.

**Demo** — `demo_pagerank.py`, rebuilt: the entity seeds chosen from the
question (a good screen on its own — `PURCHASE OF HORSES`, `PORTAGE DIFFICULTY`,
both `SACAGAWEA` nodes), then the `before-floyd-death` passage moving from
cosine rank **415** to **68** at the shipped 0.6/0.4 blend — and to **16** with
the slider pushed to pure structure. Show both: the passage that most needs the
graph is the one cosine's weight costs the most, which is the honest way to
introduce the blend rather than claiming a free lunch.

**Cost, and the one-line fix that mattered.** Pass the whole seed set to
`sourceNodes` in a single call — with biases if you want them. It is almost free
in the number of seeds, because the cost is per-call fixed overhead:

| seeds | 1 call, N sources | N calls, 1 source | ratio |
|---|---|---|---|
| 1 | 52.4 ms | 53.4 ms | 1.02× |
| 3 | 53.8 ms | 165.0 ms | **3.07×** |
| 5 | 54.8 ms | 273.5 ms | **4.99×** |
| 8 | 56.2 ms | 440.6 ms | **7.84×** |

| | measured |
|---|---|
| `lc-mentions` projection | **94 ms**, once per session, amortised |
| plain cosine top-8 | **4 ms** |
| candidate-gated rerank (`ppr`) | **79 ms** p50 |
| `expand`, fresh question | **~196 ms** — cosine 39, entity PPR 72, passage PPR 53 |
| *(first implementation, one call per seed)* | *~580 ms* |

**~50× plain vector, and it still does not matter**, because the generation call
that follows dwarfs 200 ms. That is the honest framing for a latency slide: not
"it's free", but "it's invisible next to the LLM you are about to call."

And because bias is supported, there is **no trade-off between weighting the
seeds and batching them.** That is the useful shape of the lesson, and it is
worth saying out loud: I designed around a limitation the signature does not
have. Read the parameter list first.


### 6. "Your context is redundant" → community detection (6 min) · 0:33

**The failure — measured, and inherited from section 5 (5l).** Eight retrieved
passages, all describing the same week at Long Camp. Recall metrics look fine;
month coverage went 4 → 1; most of the context window is restatement. And it
was the *expansion walk* that did it — the smartest retriever in the talk so
far is the one that collapses, because conjunction-seeking is episode-seeking.
On screen: the eight dates, then the eight community ids — **all the same
number**. The failure is structural and the structure is already computed.

**Leiden — alone. DECIDED 2026-09-07 (Nathan): six minutes doesn't fit two
algorithms, so Louvain gets no stage time** — at most a name-drop in a speaker
note. The stage beat: densely connected relative to chance, not merely
connected — the contrast with WCC from section 4. Seeded (`randomSeed`,
`concurrency=1`) it returns the same partition every run, which is what a
measured claim and a live demo both require (finding 6a). Honest asterisk,
kept: Leiden's paper guarantees internally connected communities, and GDS's
run on this graph still left one 24-node community split 13/11 — verify with
per-community WCC rather than trusting the name (finding 6b). The Louvain
material (the 1,089-node disconnected community, the redrawing partition)
stays in findings 6a/6b as Q&A backup only.

**Conductance as a cohesion check** — from the ki post: ≤0.35 reads as a tight
theme, ≥0.60 as a loose one. Measured here: median 0.27, 35 of 47 tight, none
loose. A cheap way to know whether a community means anything before you build
on it — one stream call against the same in-memory membership.

**Two payoffs:**
- *Diversification* — cap how many passages any one community contributes **to
  the walk's own ranking** (not just cosine's), and the window covers the
  question instead of restating one answer: illness goes 1 month / 1 community
  / 2 near-dup pairs → 4 months / 5 communities / 0, and the recovered
  passages are Lewis's gunshot wound and the Fort Clatsop influenza sick-list
  (finding 6c, judged by reading). On trade-goods and food-sources — the
  walk's 5l wins — the capped window is *byte-identical*: the cap only bites
  where the failure is. Say the bound too: community 23 is 286 chunks of
  "corps members", coarser than an episode, and it locks the Sept-1805
  sickness out of the capped window. A cap is a guard rail, not a ranker.
- *Topic extraction* — a table of contents for the corpus that nobody wrote,
  derived entirely from structure, at zero *additional* token cost (callback
  to section 2: the community step is token-free; the mention edges it rides
  on were already paid for): the Mandan winter, the Columbia fishery, the
  trade-goods economy, each with its date span on screen.

**Demo** — `demo_communities.py`: the themes table (with conductance), then
`-q illness --base expand`: expand top-8 all `c23`, capped window spanning
five communities and four months, redundancy 0.128 → 0.050.

### 7. "You can't explain the answer" → path finding (5 min) · 0:39

*(Measured 2026-09-07 — see Section 7 findings. Slides drafted:
[`docs/section-07-slides.md`](section-07-slides.md).)*

**The failure.** The system tells you two things are related. It cannot tell
you *how* — and "how" is usually the actual question. Entrance is §5m's
flagship: every retriever missed the brother question, the walk surfaced the
*name* at rank 4 — now explain the connection, with receipts.

**Yen's k-shortest paths**, and why **k** matters — the measured version, which
inverts the outline's original claim (finding 7a): on a typed extracted graph
the shortest path is a strong claim when the edge exists, and *higher* k drifts
into shared-commodity co-occurrence. k earns its keep where the graph lacks the
edge: no sibling relationship exists anywhere in the graph, so the recognition
scene arrives at k=3, through the Event node both anchors PARTICIPATED_IN — both
hops citing the same passage. k buys the *set*; Yen's cannot rank explanations
(the 2-hop routes are exact cost ties).

**Paths carry receipts.** Every extracted relationship stores the `chunkId` it
came from, so each hop hands back the journal passage that evidences it — all
of them now, not element `[0]` of a merged array (finding 7c). And the receipts
are the audit: five wrong edges on live demo routes are catchable only by
reading their own citations (finding 7b — the wrong-captain GUIDED edge,
Cameahwait filed as Hidatsa).

**Demo** — `demo_paths.py`, Sacagawea → Cameahwait (the §5/§6/§7 storyline
pair; Sacagawea → Shoshone as backup). Deterministic route order, ~220 ms.

**Callback.** This is the tool the NICD agent never called once. Deterministic
retrieval path, not an agent tool.

### 8. Does this actually help? (4 min) · 0:44

Abstract takeaway #4, with real numbers from the benchmark harness — recall,
redundancy, context tokens, p50/p95 latency across every strategy.

Say what the metric is and why: **answer-entity recall**, alias-aware,
deterministic, no LLM judge. It measures the one thing RAG lives or dies on —
did the context actually contain the facts — without adding variance to a
measurement whose job is to be boring.

**Show where plain vector wins.** The bank has control questions for exactly
this, and vector *should* take them. A strategy tuned until it wins the hard
questions and quietly breaks the easy ones is not an improvement.

> "Maybe you don't need this."

Then: the signals that say you do. The cleanest way to split it, borrowed from
Ghoshal's post (see Context):

> "Graph algorithms fix **reasoning** problems. They do very little for
> **coverage** problems. If your retrieval is failing because the right chunk
> never came back, none of this helps — go fix your chunking and your
> embeddings first."

Concretely, you want this when: answers require traversal rather than lookup,
the same entity is named differently across documents, or the question is about
how things connect rather than what they say.

**And the caveat that costs nothing to say:** if the whole corpus fits in the
context window, stuff it in the context window. Ghoshal's frontier-model
baseline beat every retrieval setup he tested, and the NICD paper's zero-shot
column says something similar. Retrieval architecture is a response to a corpus
that doesn't fit — not a virtue on its own.

### 9. How to implement this (3 min) · 0:48

Deliberately brief and vendor-plural. The honest axis is not "who has a better
PageRank" — it's **where does your graph live, and how often does it change.**

- **Neo4j GDS** — what the demos ran on; algorithms where the data already lives
- **NetworkX** — the standard entry point in Python. In-memory, single-machine.
  *(Nathan doesn't use it enough to demo it fairly, so: name it, don't benchmark it.)*
- **Others exist** — igraph, cuGraph, Spark GraphX, and most graph databases
  ship some algorithm library

The point to land: **these are algorithms, not products.** PageRank is
PageRank. If your corpus is small enough to fit in memory you may not need a
graph database at all — and knowing that makes the case for one honest when you
do.

**New (2026-09-07): this section's strongest candidate beat is the measured
routing rule from finding 5n** — "when does your agent reach for the graph
tool" answered with the bridge-decay curve and a one-COUNT-query router. A
stage draft is parked at the bottom of `section-05-slides.md` (banner: PARKED
FOR §9). It coexists with §10's take-home #2: the router is retrieval-path
code, not a model-side tool choice.

### 10. Three things to take home (2 min) · 0:51

1. **Build time gates query time.** Personalized PageRank over a graph where
   `CAPT. LEWIS` and `MERIWETHER LEWIS` are separate nodes will confidently
   rank the wrong passages. Fix entity resolution first.
2. **Put the algorithms in the retrieval path, not in the agent's toolbox.**
   The model won't reach for them.
3. **Measure on your own corpus.** The harness is in the repo. Include control
   questions where plain vector should win, and check that it still does.

Repo link, plus a **further reading** list on the same slide (no time spent on
it out loud — it exists for the PDF):

- NICD, *Reducing hallucinations with GraphRAG* — the 510-question study
- Blumenfeld (Neo4j), [*Scaling Karpathy's LLM wiki*](https://neo4j.com/blog/agentic-ai/scaling-karpathy-llm-wiki-graph/) — source of §6's seeded-Leiden practice and the conductance thresholds
- Ghoshal, [*When Does Graph RAG Actually Add Value?*](https://medium.com/@arijitghoshal222/when-does-graph-rag-actually-add-value-a-hands-on-experiment-2f61a0c31736) — small experiment, useful framing
- [Last year's talk repo](https://github.com/smithna/corps-of-discovery-graph-rag) — the pipeline that built this graph

Q&A from 0:53.

---

## Risks in this outline

- **Four live demos is too many.** Recommend two live (PageRank hub trap,
  paths) and two pre-recorded or screenshotted (resolution, communities).
  Decide before rehearsal, not during.
- **Section 2 is the most compressible** if rehearsal runs long — the evidence
  table can drop to the two rows that matter.
- **Section 4 is the most likely to overrun.** It has the most new vocabulary
  (co-occurrence, filtered node similarity, WCC, transitive closure).
- **Nothing in the repo has been run against a live database yet.** Timings for
  every demo section are estimates until it has.

---

## Implementation sequence

Section by section, as agreed. **Step 0 is not optional** — the repo was
written without a database to test against.

**Step 0 — Verify the existing repo end-to-end.** Fill in `.env`, then
`check_setup.py` → `project_graph.py` → each demo. Fix whatever breaks. Confirm
`graphdatascience` 1.22 works with `neo4j` driver 6.3.0 against real queries;
pin down if not. *This gates every timing estimate above.*

**Step 1 — Section 4 code (new).** `graphrank/resolution.py` +
`scripts/demo_resolution.py`, read-only port of `disambiguate.py`'s candidate
generation: co-occurrence projection, `nodeSimilarity.filtered`, string/alias
signals, and real `gds.wcc.stream` over in-memory candidate pairs. Plus the
corps-member gold-set precision/recall, and the `cooccurrence` query-time
strategy registered in `strategies.py`.

**Step 2 — Section 5 code.** ✅ **Done.** *Scope grew well past "add hub
visibility": the outline's hub story did not reproduce and the section's thesis
was rebuilt on measurement — see Section 5 findings.* What shipped:

1. `lc-mentions`, a second projection — `MENTIONED_IN` only, undirected,
   IDF weight kept as a switchable property. `project_graph.py` builds both and
   prints them side by side. Two jobs, two projections: the IDF weighting that
   is right for retrieval is wrong for prominence, and `RELATED`'s direction has
   no consistent meaning across types.
2. `pagerank.expand()` — corpus-wide retrieval blending cosine with two
   structural signals (entity-seeded and passage-seeded PPR) on **percentile
   ranks**. Min-max is wrong for PPR and the code says why: PPR is power-law
   distributed, so min-max hands the whole decision back to cosine.
3. Entity seeding by question-to-entity semantic match across the eight entity
   vector indexes (read from the database, not hardcoded), with four selectable
   weighting schemes — kept so the demo can *show* that weighting does nothing.
4. `seed_pagerank()` caches per seed node and `combine_seeds()` blends, which is
   exact by linearity. Reweighting after the first pass is free, and seeds
   shared between questions are reused.
5. `demo_pagerank.py` rebuilt with four views: the Floyd comparison (default),
   `--hubs`, `--conjunction`, `--weighting-check`, plus `--compare-rerank` to
   make the candidate-gate point against the old path.
6. `sweep_pagerank.py` — the measurement harness: `--weighting`, `--seeds`,
   `--blend`, `--damping`.
7. `questions/gold_overrides.yaml` — corrected gold targets as `(name, label)`
   pairs chosen by mention count. **A stopgap**, with the reasoning in its
   header; `questions.yaml` was deliberately left untouched. Folding these in
   and teaching `verify_questions.py` to rank by mention count is Step 5.
8. `expand` registered in `strategies.py`, so section 8 can benchmark it.

**Deliberately not changed:** `RerankConfig.damping_factor` stays at `0.85`
even though `0.85` measured worst on the mentions graph. That measurement was
taken on a different architecture over a different projection, and section 4's
finding 3c is the standing lesson — an operating point measured on one machine
is not automatically right for another. `ExpandConfig` uses `0.45`.

**Step 3 — Section 6 code.** Leiden alongside Louvain in `communities.py`;
`gds.conductance` for the cohesion check. Verify GDS tier for `gds.leiden`.

**Step 4 — Section 7.** Already built; verify against live data only.

**Step 5 — Section 8 numbers.** Run `verify_questions.py` and fix the gold
labels (they are currently unverified). Add markdown table output to
`benchmark.py`. Run it for real numbers.

**Step 6 — The deck.** Only after the demos have run and the numbers exist.

**Format: reveal.js, vendored for offline use.** Decided deliberately over
PPTX:

- Speaker view carries the notes *and* a running timer, which is what makes the
  per-section minute budgets above usable in rehearsal
- Real syntax highlighting for the Cypher and GDS calls, which are most of
  sections 4–7
- Diagrams as inline SVG — editable as markup rather than redrawn
- Prints to PDF if KCDC wants slides afterward

**Vendor reveal.js into the repo. Do not load it from a CDN.** The deck has to
open from a local file with no network, because conference wifi is not a
dependency worth taking. Publish an Artifact copy alongside it for reviewing
between sessions, but the local file is what gets presented from.

Match last year's dark theme so it reads as a sequel: background `#0D1B2A`,
panel `#152235`, accent `#018BFF`, highlight `#00CC76`, body text `#E8EDF2`,
muted `#7A8FA6`, Calibri, 16:9.

Nathan does not plan to hand-edit the deck, so optimise for quality over
round-trip editability.

## Verification

- Every demo script runs clean against the live DBMS and produces the output
  the outline claims it does
- `demo_resolution.py` performs **zero writes** — confirm by running it against
  the DB and diffing node/relationship counts and a sample of `aliases` arrays
  before and after
- `verify_questions.py` returns no unresolved gold labels before any benchmark
  number is quoted or put on a slide
- `benchmark.py` shows plain `vector` winning the `kind: control` questions; if
  it doesn't, the blend is over-weighted toward structure
- Each section's demo is timed during rehearsal and the outline's minute
  budgets are corrected to match reality

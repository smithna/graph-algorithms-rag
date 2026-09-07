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
| 5 | Ranking can't tell people apart → entity-seeded PPR | `pagerank.py`, `projection.py`, `decompose.py`, `demo_pagerank.py`, `sweep_pagerank.py`, `measure_seeds.py` | ✅ **built, verified live, slides drafted** — thesis settled on the third attempt (co-typed entity substitution); `charbonneau-role` is the spine. **Start at *Section 5 in one page*.** New: decomposed seeder (5d-ter's fix), built + measured — named-entity coverage 10/11 vs semantic 8/11, finding 5f. Open: title, demo-graph choice, whether 5f gets stage time |
| 6 | Context is redundant → communities | `communities.py`, `demo_communities.py` | ✅ runs live; still needs Leiden + conductance |
| 7 | Can't explain → path finding | `paths.py`, `demo_paths.py` | ✅ runs live (needed a resolution fix — see below) |
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
| `rawluna` | pre-disambiguation, `gpt-5.6-luna` extraction | **keep, frozen** — the section-4 measurement baseline |
| `lewisclark` | clone of `rawluna` + mentions + taxonomy, **pre-disambiguation** | parked — disambiguation unresolved, see 3f |
| `neo4j` | the v1.0 dump — `gpt-4o-mini` extraction throughout | **keep** — still the demo graph; `lewisclark` did not supersede it |
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

**Status: not applied.** Handoff written up in
[`picking-up-entity-resolution.md`](picking-up-entity-resolution.md) — restore
points, the patched scripts, the operational traps, and the first thing to try
on resuming. `lewisclark` remains pre-disambiguation at 794 Person nodes,
checkpointed at
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
| **The failure is real and exact** | 62 passages mention Charbonneau; median cosine rank **296**; **2** in the top-8. Four of eight slots go to *other* interpreters — Dorion, Gravelin, Duriaur (5e) |
| **The entity signal is load-bearing** | delete it and the hand-judged passages fall `[7,3,5] → [14,10,11]` and `[8] → [11]` — about **7 rank positions** (5d-quinquies) |
| **The hand read** | 16 promoted passages read in full across 3 questions; **4 clear the bar.** Demo case is `charbonneau-role` (5d) |
| **The best single instance** | a 305-char passage at cosine rank 22 that **never names Sacagawea**, reachable only because extraction resolved *"one of his wives"* → `SACAGAWEA` (5d) |

**Three limits, all measured, all stated on stage** — this is what makes the
multi-tool argument structural rather than a hedge:

1. **Combines evidence with weights you didn't choose.** Additivity *is* a
   conjunction bonus — comparable-degree seeds put all 9 dual-mention chunks in
   the top-20 at median rank 5. But each seed's share goes as `1/degree`, so a
   hub is nearly free to ignore (5d-quater's mechanism, and the corrected
   linearity note).
2. **Cannot enumerate or order.** 18 passages in the week before Floyd died;
   cosine's top-8 holds 3, and so does *every* graph variant including
   `NEXT_CHUNK` at long damping. A date filter returns 18 in one hop (5c).
3. **Bounded by extraction.** The passage that answers "how did they get horses
   from the Shoshone" has **no horse entity attached** (5d).

**What was retracted, and why it matters more than the wins:**

| retracted | why |
|---|---|
| The hub trap as the section's centrepiece | Lewis is the *third* hub (deer 589, elk 439); nothing is 2 hops from everything (15.4%); naive PPR does **not** return the same passages (0/8 overlap) — finding 1 |
| The long-passage blur hypothesis | sign reversed — longer passages rank **better** (Spearman −0.252) — finding 3 |
| The conjunction thesis | the co-mention proxy was hub-contaminated (100% for grizzly, 87% food-sources); the Floyd demo case was a **false positive** — the passage is from ten weeks before he died — findings 4, 10, 5d |
| Four tuning conclusions (5d-bis…quater) | the judged passages saturate the entity percentile at 0.97–0.999, and a binary top-8 threshold on n=4 turned one-position drift into "findings" — **5d-quinquies** |

**Open decisions — a fresh conversation should start here:**

1. **Title sign-off.** *"Your ranking can't tell people apart."*
2. **`neo4j` vs `lewisclark`.** Every number above is `neo4j`. `lewisclark`
   descends from a different extraction (+39% mention edges). **If the demo
   graph changes, all of it is re-measured.** This gates the slides.
3. **Gold-set design fix** — gold should name what makes an answer *correct*,
   not every entity present. Drop hub entities; fold `gold_overrides.yaml` into
   `questions.yaml`; teach `verify_questions.py` to rank by mention count.
   Unblocks Step 5 (finding 10).
4. **How much of the retraction to tell** in slide 5.9 (~20 seconds).

**Highest-leverage untested change**: **question decomposition for seed
selection.** The entity seeder is itself a cosine step with cosine's disease —
it returns `WISDOM RIVER` and `SAGITTARIA LATIFOLIA` for a Sacagawea question.
Naming the entities from the question (NER, parse, or an agent choosing
explicitly) is where the leverage is; edge weights, seed weights and degree
filters all measured no-op or unmeasurable (5d-ter, 5d-quinquies). **Now built
and measured — see finding 5f.**

**Reading guide:**

| load-bearing | 1, 2, 3, 4, 5b, 5c, 5d, 5e, 8, 9, 10, 11, 12 |
|---|---|
| **mechanisms hold, conclusions do not** | 5d-bis, 5d-ter, 5d-quater — see the warning on each |
| **read before any of those three** | **5d-quinquies** |
| superseded numbers | finding 5's blend/damping/seed sweeps were scored against the contaminated proxy; keep for history, do not quote |


> ⚠️ **Two of this section's own claims did not reproduce and are retracted
> below.** The history is kept, exactly as in section 4: "the mechanism I
> assumed was wrong, and here is what the data said instead" is the most useful
> thing in the section. Measured 2026-09-07 against the **`neo4j`** demo graph,
> read-only. Every number below is `neo4j`-specific — see finding #12.

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

#### 7. `alpha=1.0` verifies exactly — and the current architecture caps the gain

| alpha | identical ordering to baseline | overlap |
|---|---|---|
| **1.0** | **6/6** | 8.00/8 |
| 0.9 | 3/6 | 8.00/8 |
| 0.5 | 0/6 | 7.67/8 |
| 0.0 | 0/6 | 5.33/8 |

`alpha=1.0` reproduces the vector baseline byte-for-byte, which is the
credibility move: it proves the knob is real and the baseline was not swapped.

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
- **All of it is `neo4j`.** The section 4 findings above record `lewisclark` as
  the intended replacement demo graph. `lewisclark` descends from `rawluna`,
  which has 39% more mention edges and names entities differently, so the hub
  table, the overlap figures and the blend sweep will all shift. **If the demo
  graph changes, section 5's numbers must be re-measured from scratch.** The
  code is database-agnostic; the slide figures are not.
- The `control` question `keelboat-return` is *not* harmed by the blend (cosine
  1 in top-8 at median 164; blend 0.8/0.2 gives 2 at median 153), but this must
  be re-confirmed at whatever weight ships — it is the outline's own honesty
  check.

### Design notes not yet folded into the sections

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
no LLM extraction pass at build time. That's the thesis for section 3.

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

**Demo** — `demo_resolution.py`, read-only, runs in ~2 s:
- Sacagawea's nineteen surface forms, as the problem statement
- live candidate generation, then `--adjudicate`, then the closed component
- the write audit proving zero writes

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

**The failure.** Eight retrieved passages, all describing the same afternoon.
Recall metrics look fine. Most of the context window is restatement.

**Louvain and Leiden.** Densely connected relative to chance, not merely
connected — the contrast with WCC from section 4. Leiden exists because Louvain
can emit internally disconnected communities. *(Verify GDS tier for
`gds.leiden` before this goes on a slide.)*

**Conductance as a cohesion check** — from the ki post: ≤0.35 reads as a tight
theme, ≥0.60 as a loose one. A cheap way to know whether a community means
anything before you build on it.

**Two payoffs:**
- *Diversification* — cap how many passages any one community contributes, and
  the window covers the question instead of restating one answer
- *Topic extraction* — a table of contents for the corpus that nobody wrote,
  derived entirely from structure, at zero token cost (callback to section 2)

**Demo** — `demo_communities.py`: the themes, then the redundancy delta between
plain top-k and community-capped retrieval.

### 7. "You can't explain the answer" → path finding (5 min) · 0:39

**The failure.** The system tells you two things are related. It cannot tell
you *how* — and "how" is usually the actual question.

**Yen's k-shortest paths**, and specifically why **k** matters: the single
shortest path is very often a trivial co-occurrence. The second and third are
where the mechanism lives.

**Paths carry receipts.** Every extracted relationship stores the `chunkId` it
came from, so each hop hands back the journal passage that evidences it. The
context isn't "eight passages mentioning Sacagawea" — it's the specific chain
establishing how the Shoshone horses were obtained.

**Demo** — `demo_paths.py`, Sacagawea → Shoshone.

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
- Neo4j, [*Scaling Karpathy's LLM wiki*](https://neo4j.com/blog/agentic-ai/scaling-karpathy-llm-wiki-graph/)
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

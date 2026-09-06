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
| 5 | Ranking is wrong → personalized PageRank | `pagerank.py`, `demo_pagerank.py` | ✅ runs live; still needs hub visibility |
| 6 | Context is redundant → communities | `communities.py`, `demo_communities.py` | ✅ runs live; still needs Leiden + conductance |
| 7 | Can't explain → path finding | `paths.py`, `demo_paths.py` | ✅ runs live (needed a resolution fix — see below) |
| 8 | Does this help? | `benchmark.py`, `metrics.py` | runs; **4 gold labels still unresolved** |
| 9 | How to implement | docs only | not started |
| 10 | Takeaways | none | not started |
| — | **Step 6: the deck** | reveal.js, vendored offline | not started — section 4's narrative settled: built on the Sacagawea example, no metric claims |

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
| `neo4j` | the demo graph — restored dump, fully disambiguated | **keep** — what the demos run against |
| `rawluna` | pre-disambiguation, `gpt-5.6-luna` extraction | **keep** — the canonical measurement baseline |
| `rawgraph` | pre-disambiguation, `gpt-4o-mini` extraction | retired — superseded by `rawluna` |

**`rawluna` is the baseline for all measurement from here on.** `rawgraph` was
an earlier build on the stale extraction model; its numbers are retained below
only where they establish that a result *replicates* across independent builds,
which is evidence worth keeping. Nothing new should be measured on it.

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

### 5. "Your ranking is wrong" → personalized PageRank (10 min) · 0:23

**The failure.** Vector top-8 returns eight passages that *sound* like the
question. Sounding like the question and answering it are different things.

**PageRank in 60 seconds**, then the pivot: plain PageRank asks "what's
important in this graph?" — a global, query-independent answer, the same for
every question you ever ask. **Personalized** PageRank restarts the walk at
chosen source nodes, so it asks the useful question: *what's important
relative to what this question is about?* The source nodes are your top vector
hits. Vector search nominates; the graph ranks.

**The hub trap — break it live.** This is the section's centerpiece and it is
the thing that will actually save someone in the audience a wasted afternoon.
Run it naively: every question returns roughly the same passages. Why? Every
chunk in the corpus is two hops from every other chunk through `MERIWETHER
LEWIS`, who is mentioned nearly everywhere. The random walk drowns.

Two fixes, both one line:
- **IDF-weight the mention edges**: `log(1 + totalChunks / df)`, so a shared
  mention of *Beaverhead Rock* counts for far more than a shared mention of
  *Lewis*
- **Normalize by global PageRank** ("lift"): a passage that ranks high for
  *every* question is not evidence about *this* one

**Hybrid retrieval** — abstract takeaway #2. The `alpha` blend between cosine
and structure. Show `alpha=1.0` reproducing the baseline exactly, `alpha=0.0`
going pure-structure, and where the useful middle sits.

**Demo** — `demo_pagerank.py`: vector top-k beside reranked top-k, with the
pre-rerank position of each passage and the promoted ones flagged.

**Cost.** Projection is the expensive step and it's amortized. Per-query PPR
against a projected graph is milliseconds.

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

**Step 2 — Section 5 code.** Add hub visibility to `demo_pagerank.py` (top
entities by degree) so the hub trap is showable rather than assertable.

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

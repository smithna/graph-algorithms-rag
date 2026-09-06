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
| 4 | Entities are a mess → node similarity + WCC | `resolution.py`, `adjudicate.py`, `demo_resolution.py`, `cooccurrence.py` | ✅ **built, verified, and measured on a clean pre-disambiguation graph** — see *Section 4 findings* |
| 5 | Ranking is wrong → personalized PageRank | `pagerank.py`, `demo_pagerank.py` | ✅ runs live; still needs hub visibility |
| 6 | Context is redundant → communities | `communities.py`, `demo_communities.py` | ✅ runs live; still needs Leiden + conductance |
| 7 | Can't explain → path finding | `paths.py`, `demo_paths.py` | ✅ runs live (needed a resolution fix — see below) |
| 8 | Does this help? | `benchmark.py`, `metrics.py` | runs; **4 gold labels still unresolved** |
| 9 | How to implement | docs only | not started |
| 10 | Takeaways | none | not started |
| — | **Step 6: the deck** | reveal.js, vendored offline | not started — section 4's numbers now exist |

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

### Section 4 findings — read before writing these slides

Section 4's code is built, runs read-only, and has now been measured against a
purpose-built pre-disambiguation graph (`rawgraph`) as well as the demo graph.
Both findings below are settled. Finding #2 went through a retraction on the way
— the first version of that experiment was biased — and the history is kept
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

Result on the clean graph, scored against the hand-built identity gold set:

| signals | pairs | TP | FP | precision | recall | largest WCC |
|---|---|---|---|---|---|---|
| string + alias | 915 | 47 | 13 | **0.78** | 0.21 | 37 |
| co-occurrence only | 207 | 2 | 129 | 0.02 | 0.01 | 73 |
| all three | 1,112 | 48 | 139 | 0.26 | **0.22** | 242 |

**The conclusion held.** Co-occurrence still contributes almost nothing on its
own: 1 true positive the string ladder could not reach, against 129 false
positives. Raw precision 0.015.

**And then adjudication changes the verdict completely.** Running the LLM over
those 131 scoreable co-occurrence pairs:

| | pairs kept | TP | FP | precision |
|---|---|---|---|---|
| co-occurrence, raw | 131 | 2 | 129 | **0.015** |
| after adjudication | 2 | 2 | 0 | **1.000** |

**Adjudication rejected 129 of 131 — every false positive, no true ones.** And
the pair only co-occurrence could find is the one that matters:

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
| Person nodes | 795 |
| All possible pairs | **315,615** |
| Proposed by all three signals | **1,112** — 0.35% |
| Reduction | **284×** |
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

#### 3. Transitive closure is the sharpest demo material

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
  statement. One sentence, from the stage, costs nothing.

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

**The failure.** In the journals, William Clark is `CLARK`, `CAPT. CLARK`,
`WILLIAM CLARK`, `Capt Clark`, `Wm. Clark`. Every one is a separate node.
Retrieval for Clark silently misses most of Clark. No error, no warning — just
quietly incomplete context, which is the worst failure mode RAG has.

**The naive fix and why it breaks.** String matching gets you a long way and
then falls off a cliff. The journals spell Charbonneau as *Chabonah*. Raw
Jaro-Winkler scores that below threshold. Double-metaphone on the surname
catches it (XPN vs XRPN, JW ≈ 0.925). Show the ladder of string signals — but
frame it as a losing battle, because it is.

**You have more information than you think — and then you measure it.**
✅ *Settled on a clean pre-disambiguation graph; see "Section 4 findings" above
for the numbers and for the retraction this went through first.*

The intuition is reasonable: two names appearing alongside the same people,
places and dates are probably the same entity, and that signal is already in
the graph at zero token cost.

- Project entity↔entity co-occurrence weighted by shared chunk count
- `gds.nodeSimilarity.filtered` — cosine over co-occurrence vectors, same-label
- Union the graph signal with the string and alias signals

Then show the measurement, live, and let it complicate the story — because it
does. On its own the graph signal is *bad*: 2 true positives against 129 false
ones, precision 0.015. Someone in the room is about to conclude it is useless.

Then run adjudication over exactly those pairs and show 129 of 131 rejected,
both true positives kept, precision 1.00 — including `INDIAN WOMAN ~ SACAGAWEA`,
which no string signal on earth reaches.

That is the beat the section is built around: **a signal with 1.5% precision is
not a broken signal if something downstream can afford to filter it.** 315,615
possible pairs become 1,112 — a 284× cut — and the LLM cleans up what is left
for fractions of a cent. Recall is what the algorithm is for; precision is what
the adjudicator is for.

**WCC, and what it is actually for.** Sharpen this, because it's usually taught
wrong: WCC answers *"are these connected at all"*, not *"are these a topic."*
Its job here is **transitive closure** — A≈B, B≈C, therefore one entity. That
is a precise and correct use. Run WCC on a raw corpus graph and you get one
giant component and some dust.

**Same algorithm, query time.** One slide: node similarity also retrieves.
"Find chunks that share entities with this chunk" is a different question from
"find chunks that sound like this chunk," and it catches things embeddings
miss. Carried into the benchmark in section 8 as the `cooccurrence` strategy.

**Demo** — `demo_resolution.py`, read-only, runs in ~2 s:
- the `aliases` arrays as receipts of what past resolution already merged
  (`JOSEPH FIELD` absorbed 44 surface forms; `SACAGAWEA` 21)
- live candidate generation finding duplicates that **survived both passes** —
  `DREWYER`/`GEORGE DROUILLARD`, 328 mentions split down the middle
- `--compare-signals`: precision and recall per signal mix, the table that
  refutes the intuition above
- transitive closure contaminating an identity in three names:
  `GEORGE DREWYER + GEORGE DROUILLARD + GEORGE SHANNON`
- `--adjudicate` to clean it up, and the write audit proving zero writes

**Honest note.** An LLM adjudicates the candidate pairs. The algorithm's job
isn't to decide — it's to shrink the candidate set from O(n²) to something
adjudication can afford. Adjudication is off by default, disk-cached, and hard-
capped, so the demo is free and byte-for-byte repeatable after the first run.

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

Then: the signals that say you do. Answers requiring traversal rather than
lookup. The same entity named differently across documents. Questions about how
things connect rather than what they say.

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

Repo link. Q&A from 0:53.

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

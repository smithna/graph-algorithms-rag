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
| — | **Step 0: verify repo against a live DBMS** | all existing scripts | ⛔ **Blocked** — `.env` still has placeholder `NEO4J_PASSWORD` / `OPENAI_API_KEY` |
| 0 | Cold open — the failure | `baseline.py` | written, unverified |
| 1 | What is a graph? | none | not started |
| 2 | What is Graph RAG / evidence | none (sources gathered) | not started |
| 3 | Roadmap | none | not started |
| 4 | Entities are a mess → node similarity + WCC | `resolution.py`, `adjudicate.py`, `demo_resolution.py`, `cooccurrence.py` | **next up** — designed, not written |
| 5 | Ranking is wrong → personalized PageRank | `pagerank.py`, `demo_pagerank.py` | written, unverified; needs hub visibility |
| 6 | Context is redundant → communities | `communities.py`, `demo_communities.py` | written, unverified; needs Leiden + conductance |
| 7 | Can't explain → path finding | `paths.py`, `demo_paths.py` | written, unverified |
| 8 | Does this help? | `benchmark.py`, `metrics.py` | written, unverified; gold labels unchecked |
| 9 | How to implement | docs only | not started |
| 10 | Takeaways | none | not started |

**Nothing in this repo has been executed against a live database yet.** Every
timing estimate below is provisional, and the gold labels in
`questions/questions.yaml` are unverified guesses until `verify_questions.py`
runs clean.

### Design notes not yet folded into the sections

- **Section 4 has a full implementation design** (read-only port of
  `disambiguate.py`): carry candidate pairs as node-id tuples rather than name
  tuples, which is what lets real `gds.wcc.stream` run with zero database
  writes. Project candidate pairs via `gds.graph.cypher.project` with
  `UNWIND $pairs` — the client runs Cypher projections in a **read**
  transaction, so it is a stronger zero-write guarantee than the source had.
- **Gold set for section 4**: the ~40-name `CORPS_MEMBERS` roster in
  `corps-of-discovery-graph-rag/tag_corps_members.py`. Precision from pairs
  where both endpoints are on the roster; recall replayed from the `aliases`
  arrays of already-merged nodes.
- **Known compatibility risks**: `openai` 3.8.0 moved
  `client.beta.chat.completions.parse` → `client.chat.completions.parse`;
  `pydantic` is used but missing from `requirements.txt`; `graphdatascience`
  should be pinned `<2`; `gds.nodeSimilarity.filtered` needs a `beta.` fallback
  below GDS 2.5.


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

**You have more information than you think.** This is the section's real point.
Two names that keep appearing alongside the same people, places, and dates are
probably the same entity — *even when the strings disagree entirely.* That
signal is already sitting in the graph as co-occurrence, and it costs no LLM
tokens to read.

- Project entity↔entity co-occurrence weighted by shared chunk count
- `gds.nodeSimilarity.filtered` — cosine over co-occurrence vectors, same-label
- Union the graph signal with the string and alias signals

**WCC, and what it is actually for.** Sharpen this, because it's usually taught
wrong: WCC answers *"are these connected at all"*, not *"are these a topic."*
Its job here is **transitive closure** — A≈B, B≈C, therefore one entity. That
is a precise and correct use. Run WCC on a raw corpus graph and you get one
giant component and some dust.

**Same algorithm, query time.** One slide: node similarity also retrieves.
"Find chunks that share entities with this chunk" is a different question from
"find chunks that sound like this chunk," and it catches things embeddings
miss. Carried into the benchmark in section 8 as the `cooccurrence` strategy.

**Demo** — `demo_resolution.py`, read-only:
- the `aliases` arrays as receipts of what past resolution already merged
- live candidate generation finding duplicates that **survived both passes**
- precision/recall against the 40-name corps-member gold set

**Honest note.** An LLM adjudicates the candidate pairs. The algorithm's job
isn't to decide — it's to shrink the candidate set from O(n²) to something
adjudication can afford.

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
Match the existing dark theme (`#0D1B2A` / `#018BFF` / Calibri / 10×5.625in) so
it reads as a sequel.

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

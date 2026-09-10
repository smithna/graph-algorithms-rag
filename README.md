# Graph Algorithms for RAG Retrieval

> Vector similarity gets you candidates. Graph algorithms get you the right answer.

Companion code for a talk on using graph algorithms — node similarity,
personalized PageRank, Leiden community detection, and Yen's k-shortest
paths — to improve context retrieval and ranking in a RAG pipeline.

It runs against the Lewis & Clark knowledge graph built by
[corps-of-discovery-graph-rag](https://github.com/smithna/corps-of-discovery-graph-rag).
This repo adds the algorithm and retrieval layer on top of that graph — it
doesn't re-ingest or re-chunk the source text, and the original chunk
embeddings are untouched. It does, however, rerun parts of that repo's
entity-resolution and taxonomy-extraction pipeline against a newer model
(`gpt-5.6-luna`, via the patches in `tools/corps-patches/`) where measurement
surfaced problems the original pipeline didn't catch, and adds a handful of
entity embeddings the original build didn't have. See
[`tools/README.md`](tools/README.md) for exactly what changed and why.

---

## The talk

**The deck is the source of truth for the session this code backs** —
[`deck/index.html`](deck/index.html), a self-contained reveal.js
presentation with full speaker notes and per-slide timing baked in (see
[`deck/README.md`](deck/README.md) for how to present it, and how to read the
notes). There's no separate outline or script in this repo; the deck **is**
the final form of the talk.

The paper the talk's numbers are checked against —
NICD's *Reducing hallucinations with GraphRAG* — is in
[`docs/nicd-reducing-hallucinations-graphrag.pdf`](docs/nicd-reducing-hallucinations-graphrag.pdf)
(reproduced here under its CC BY-NC-SA 4.0 license; see the file for
attribution).

---

## What's here

| Technique | Module | What it fixes |
|---|---|---|
| Entity resolution, read-only | [`graphrank/resolution.py`](graphrank/resolution.py) | `CAPT. CLARK` and `WILLIAM CLARK` are separate nodes, so retrieval for Clark misses most of Clark. Node similarity + WCC find the duplicates — without writing anything. |
| Node similarity retrieval | [`graphrank/cooccurrence.py`](graphrank/cooccurrence.py) | "Chunks that share entities with this chunk" is a different question from "chunks that sound like it", and catches passages embeddings miss. |
| Personalized PageRank rerank | [`graphrank/pagerank.py`](graphrank/pagerank.py) | Vector top-k ranks by wording. PPR ranks by how central a passage is *to this question's* neighbourhood. |
| Leiden community detection | [`graphrank/communities.py`](graphrank/communities.py) | Vector top-k returns eight restatements of one thing, and can't answer whole-corpus questions at all. A theme map — communities as a table of contents — fixes both. |
| Yen's k-shortest paths | [`graphrank/paths.py`](graphrank/paths.py) | Similarity says two concepts are both relevant. Paths say *how they are connected*, with the passage evidencing each hop. |
| Hybrid | [`graphrank/strategies.py`](graphrank/strategies.py) | PageRank decides relevance, community structure stops redundancy. This is the production configuration. |
| Benchmark harness | [`scripts/benchmark.py`](scripts/benchmark.py) | Recall, redundancy, context size, and latency per strategy. |

---

## The two design decisions that matter

**Mention edges are IDF-weighted.** Without this the whole approach collapses.
Every chunk in the corpus is two hops from every other chunk through
`MERIWETHER LEWIS`, who is mentioned nearly everywhere — so unweighted PageRank
returns the same Lewis-adjacent passages regardless of the question. Each
`(entity)-[:MENTIONS]->(chunk)` edge is weighted `log(1 + totalChunks / df)`, so
a shared mention of "Beaverhead Rock" counts for far more than a shared mention
of "Lewis". See [`graphrank/projection.py`](graphrank/projection.py).

**Scores are normalized by global PageRank.** The `lift` normalization divides
each personalized score by the node's query-independent PageRank. A passage
that ranks highly for *every* question is not evidence about *this* one.
Set `--normalize none` to see what happens without it — the difference is the
most instructive thing in the demo.

---

## Prerequisites

- **Python 3.10+**
- **Neo4j 5.x with the GDS plugin.** PageRank, Leiden, and Yen's all run in
  GDS. Aura Free does not include it — you would need
  [Aura Graph Analytics](https://neo4j.com/docs/graph-data-science/current/aura-graph-analytics/)
  instead, which changes the client code.
- **The Lewis & Clark graph**, restored from the
  [corps-of-discovery release dump](https://github.com/smithna/corps-of-discovery-graph-rag/releases/latest).
- **An OpenAI API key** — used *only* to embed the question. Chunk and entity
  embeddings already live in the graph.

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in NEO4J_URI, NEO4J_PASSWORD, OPENAI_API_KEY
```

Then confirm the graph is where you think it is:

```bash
python scripts/check_setup.py
```

This verifies the connection, the GDS plugin, the node and relationship counts,
and every vector and full-text index the retrieval layer depends on. Fix
anything it flags before going further.

---

## Run it

### 1. Project the graph (once per session)

```bash
python scripts/project_graph.py
```

Projection is the expensive step and it is amortised — this is the performance
argument in the talk. Once the graph is in the GDS catalog, a personalized
PageRank run is milliseconds. Add `--force` to rebuild after changing weights.

### 2. Entity resolution (read-only)

```bash
python scripts/demo_resolution.py                      # the whole pipeline
python scripts/demo_resolution.py --compare-signals    # what each signal is worth
python scripts/demo_resolution.py --signals string alias
python scripts/demo_resolution.py --check-roster       # gold names vs the graph
python scripts/demo_resolution.py --adjudicate --max-calls 25   # costs money
```

Finds duplicate entity nodes with three signals — chunk co-occurrence similarity,
a string ladder (Jaro-Winkler, token containment, double metaphone), and shared
aliases — then runs real `gds.wcc.stream` over the candidate pairs to get
transitive closure. `DREWYER` and `GEORGE DROUILLARD` are the same man with 328
mentions split between them.

**It writes nothing, and proves it.** Candidate pairs are carried as node-id
tuples rather than name tuples, which is what lets WCC run over a graph
projected from `UNWIND $pairs` instead of over `IS_SAME_ENTITY_AS`
relationships that would have to be created first. Every query runs in a read
transaction, so the server rejects a write outright. The run ends by diffing
node and relationship counts, per-label and per-type totals, and a sample of
`aliases` arrays against a snapshot taken before it started.

**Measure on `rawluna`, not the demo graph.** The shipped dump has already been
through `disambiguate.py`, so the duplicates left in it are the ones that run
missed — measuring resolution signals there is biased, and the script warns you.
`rawluna` is a pre-disambiguation build kept for exactly this purpose:

```bash
NEO4J_DATABASE=rawluna python scripts/demo_resolution.py --compare-signals
```

`--compare-signals` is the one to run first. On this corpus the co-occurrence
signal contributes zero unique true positives and costs 48 points of precision
— a result worth reproducing before trusting the intuition behind it.

Adjudication is off by default. When enabled it is capped, disk-cached, and
still writes nothing to the database.

### 3. Personalized PageRank reranking

```bash
python scripts/demo_pagerank.py "How did the corps acquire horses from the Shoshone?"
```

Prints the vector top-k beside the reranked top-k. The `was` column shows each
passage's pre-rerank position; a green `+` means the graph pulled in a passage
that vector search had ranked outside the window entirely.

Knobs worth turning on stage:

```bash
--alpha 0.0        # pure PageRank, no cosine contribution
--alpha 1.0        # pure cosine — reproduces the baseline exactly
--normalize none   # drop the global-PageRank correction and watch hubs take over
--candidate-k 100  # deeper recall for the graph to rerank
```

### 4. Community detection

```bash
python scripts/demo_communities.py                        # the corpus's themes
python scripts/demo_communities.py -q "How did they feed themselves?"
python scripts/demo_communities.py --write                # persist communityId
```

Without a question it lists the communities: a table of contents for the
journals that nobody wrote, derived entirely from structure. With `-q` it
compares redundancy between plain vector top-k and community-capped retrieval.

`--write` writes a `communityId` property onto your Neo4j nodes. It is behind a
flag because it modifies your database — but once it is there you can explore
communities in Browser and Bloom, which demos well.

### 5. Path exploration

```bash
python scripts/demo_paths.py --from Sacagawea --to Shoshone
python scripts/demo_paths.py --from "Grizzly Bear" --to "Great Falls" -k 5
```

Yen's returns the k shortest distinct routes between two anchors. Each hop
reports the journal entry it was extracted from, so the path is a citation
trail rather than an assertion. The shortest route is often a trivial
co-occurrence — the second and third are usually where the mechanism lives.

### 6. Benchmark

```bash
python scripts/verify_questions.py   # do this first — see the warning below
python scripts/benchmark.py
```

Runs the question bank through every strategy and reports:

- **recall** — fraction of gold answer entities present in the assembled
  context, alias-aware (the journals call Sacagawea "Janey")
- **redundancy** — mean pairwise entity overlap between retrieved passages;
  high redundancy means the window is full of restatements
- **tokens** — so a strategy cannot buy recall by shipping more text
- **p50 / p95 ms** — latency against an already-projected graph

Per-question detail lands in `results/benchmark.json` and `.csv`.

> ⚠️ **The gold labels in [`questions/questions.yaml`](questions/questions.yaml)
> have not been checked against a live database.** They were written against the
> documented schema. Run `python scripts/verify_questions.py` first — it reports
> every gold name that does not resolve to a node and suggests the closest match
> the graph actually contains. Benchmark numbers are meaningless until it comes
> back clean.

---

## Why entity recall, and not an LLM judge

The harness deliberately scores retrieval, not generation. Answer-entity recall
asks the one question RAG lives or dies on — *did the context actually contain
the facts needed?* — and it is deterministic, free, and indifferent to which
strategy produced the context. An LLM judge would add variance and cost to a
measurement whose whole job is to be boring and repeatable.

The question bank includes **control questions** (`kind: control`) that plain
vector search should already answer well. They are there to catch the failure
mode where a graph strategy is tuned until it wins on connection questions and
quietly breaks the easy ones. If `vector` does not win those, the blend is
over-weighted toward structure.

---

## Repository layout

```
deck/                 # the talk itself — reveal.js, vendored, presents offline
├── index.html         # every slide, every speaker note, every timing budget
├── README.md          # how to present it, keyboard shortcuts, structure notes
└── assets/            # diagrams (mostly inline SVG) and the two supplied images

graphrank/             # the retrieval/algorithms library
├── config.py           # env, driver, GDS client
├── embedding.py        # question embedding with an on-disk cache
├── models.py            # shared result types
├── resolve.py           # phrase -> node, via full-text or vector index
├── projection.py        # the GDS projection and its IDF weighting
├── baseline.py           # pure vector search — the control
├── resolution.py         # read-only entity resolution: signals, WCC, scoring, audit
├── adjudicate.py         # LLM pair adjudication — opt-in, capped, disk-cached
├── cooccurrence.py       # node similarity as a query-time retrieval strategy
├── pagerank.py           # personalized PageRank reranking
├── communities.py        # Leiden detection, summarization, the theme-map
├── paths.py              # Yen's k-shortest paths + evidence assembly
├── strategies.py         # the registry the benchmark runs against
└── metrics.py            # recall, redundancy, context size

scripts/               # everything runnable
├── check_setup.py       # verify the environment first
├── project_graph.py     # project once, reuse everywhere
├── demo_resolution.py   # duplicate entities, zero writes
├── demo_pagerank.py     # before/after reranking
├── demo_communities.py  # themes + diversification
├── demo_paths.py        # explanatory routes with citations
├── make_paths_readpack.py # human-readable dump of every path + receipt
├── verify_questions.py  # validate gold labels against the graph
├── benchmark.py         # the comparison table
└── measure_*.py         # one-off measurement scripts behind specific deck
                          # claims — each names its own output in results/

questions/             # the benchmark's question bank and gold answer labels
results/               # generated by scripts/ above; gitignored, reproducible
tools/                 # one-time corpus-prep utilities — see tools/README.md
docs/                  # the NICD paper the talk's numbers are checked against
```

---

## Adding a strategy

Write a function with the signature `(question, k, **options) -> RetrievalResult`
and register it:

```python
# graphrank/strategies.py
REGISTRY["my_idea"] = my_idea_strategy
```

The benchmark picks it up immediately: `python scripts/benchmark.py --strategies vector my_idea`.

---

## License

MIT

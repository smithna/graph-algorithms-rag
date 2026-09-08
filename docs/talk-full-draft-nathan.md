# Graph Algorithms for RAG — full talk draft

**Nathan Smith · KCDC 2026 · 53 minutes of content + ~7 for Q&A**

> **What this is.** All eleven section files compiled into one document for
> review and editing. Content is **verbatim** from the section files — nothing
> has been rewritten, resolved, or reconciled. Headings are demoted one level
> and the repeated "draft slide content" preamble is lifted here; that is the
> whole of the mechanical editing.
>
> **Cross-section problems are NOT fixed here.** They are listed in
> [`talk-full-draft-review.md`](talk-full-draft-review.md), which is the
> companion to this file and the thing to read first.
>
> **Speaker notes are blockquotes.** Text inside a blockquote that is styled as
> a heading is *on-slide typography*, not document structure.
>
> **Source of truth remains [`talk-outline.md`](talk-outline.md).** This
> document is a review artifact; edits made here need to land back in the
> per-section files (or the section files need to be retired in favour of this
> one — an open question for Nathan).

---

## Timing ledger

| § | section | budget | drafted | Δ | starts (budget) |
|---|---|---|---|---|---|
| 0 | Cold open: the failure | 3:00 | 3:00 | — | 0:00 |
| 1 | What is a graph? | 3:00 | 3:00 | — | 0:03 |
| 2 | What is Graph RAG, and does it work? | 7:00 | 7:00 | — | 0:06 |
| 3 | Roadmap | 1:00 | 1:00 | — | 0:13 |
| 4 | Your entities are a mess | 9:00 | **10:30** | **+1:30** | 0:14 |
| 5 | Your ranking can't tell people apart | 10:00 | **14:00** | **+4:00** | 0:23 |
| 6 | Your context is redundant | 6:00 | 6:00 | — | 0:33 |
| 7 | You can't explain the answer | 5:00 | 5:00 | — | 0:39 |
| 8 | Does this actually help? | 4:00 | 4:00 | — | 0:44 |
| 9 | How to implement this | 3:00 | 3:00 | — | 0:48 |
| 10 | Three things to take home | 2:00 | 2:00 | — | 0:51 |
| | **total** | **53:00** | **58:30** | **+5:30** | Q&A 0:53 |

**The overage is entirely §4 and §5.** Both carry drafted cut plans (§4 has
three ranked cuts to 8:55; §5 has eleven trims to exactly 10:00, several inside
beats the draft had previously marked untouchable). Neither has been applied.

**Every start time in the section headers assumes the cuts land.** As drafted,
§6 starts at 0:38:30, not 0:33, and Q&A starts at 0:58:30 — past the hour.

---

## Structural spine

Four failures, four algorithms, two stages — the §3 roadmap, restated so the
arc is visible in one place:

| § | stage | the failure | the algorithm | live demo? |
|---|---|---|---|---|
| 0 | — | *(the cold open — the failure, undiagnosed)* | none | **yes** — `demo_baseline.py` |
| 4 | build | Your entities are a mess | node similarity + WCC | recording |
| 5 | query | Your ranking can't tell people apart | personalized PageRank | **yes** — `demo_pagerank.py` |
| 6 | query | Your context is redundant | Leiden | slide output |
| 7 | query | You can't explain the answer | Yen's k-shortest paths | **yes** ×2 — `demo_paths.py` |
| 8 | — | *(does any of it help — the benchmark)* | — | no |
| 9 | — | *(the router: one COUNT query)* | — | no |

Every section opens with a problem the audience has felt, then solves it — and
says when not to reach for the algorithm.

---

Insert a bio slide like the one from the corps-discovery repo. They also shared a sponsor slide that they would like us to show. It's KCDC_2026_Sponsors_Slide.jpg. It can go after the bio slide.

## Section 0 — Cold open: the failure

*live demo, no title slide first · 3 minutes · starts 0:00* · source: [`section-00-slides.md`](section-00-slides.md)

> **Editorial constraints for this section:**
> - **The demo is live and it is `baseline.py` only.** No blend, no graph, no
>   comparison — the fix must not appear before the failure has landed.
> - **Question choice: `charbonneau-role`, deliberately the same question 5.1
>   diagnoses.** The cold open shows the crash; section 5 comes back and does
>   the autopsy. The callback is the structure, not an accident. ⚠️ Needs
>   Nathan's sign-off — the alternative is a different question here, which
>   means a new verified live run before anything goes on a slide.
> - **No diagnosis here.** The words "co-typed entity substitution," the
>   annotated names-per-passage build, and the median-rank table all belong to
>   5.1. The cold open ends on the problem, named only as far as "incomplete."
> - Numbers on screen are the verified `lewisclark` ones (outline finding 5o):
>   69 / 67 / 2-of-8. Nothing else.
> - ⚠️ **One small code gate remains:** the live run needs a vector-only view.
>   `demo_pagerank.py` prints the comparison, which spoils section 5. Either a
>   `--vector-only` flag or a five-line `scripts/demo_baseline.py`. Listed
>   under Assets.

---

### 0.1 — The question, run live (1:15)

**Screen:** a terminal, not a slide. The question typed in front of them.

> ### "What was Toussaint Charbonneau's role on the expedition?"

```
NEO4J_DATABASE=lewisclark python scripts/demo_baseline.py \
    "What was Toussaint Charbonneau's role on the expedition?"
```

**The top-8 comes back. It looks great.**

> No hello, no title slide. Type the question, hit enter, and read the results
> with them for a moment.
>
> Read rank 1 aloud — it is genuinely him, paid off "for his Services as an
> enterpreter." Skim two more: interpreters, negotiations with the Sioux,
> expedition logistics. Every passage is on-topic, fluent, plausibly what you
> would hand an LLM. If this were your pipeline you would ship it.

---

### 0.2 — The reveal (1:00)

**Slide:** one fraction, large.

> # 2 of 8
> ### passages in that window are about the man you asked about

**Slide (build):**

> ### 69 passages in this corpus mention Charbonneau.
> ### 67 of them are outside the window.

> The rest of the window went to *other* interpreters — Dorion, Gravelines —
> and to diplomatic scenes with no interpreter in them at all. The context is
> confident, fluent, and **incomplete**. An LLM reading it will give you a
> well-written answer about the wrong Frenchman, and nothing anywhere will
> throw an error.
>
> And the passages that were needed are not hiding. They are in the database,
> tagged to the man, one hop from where retrieval was standing. They just
> never scored high enough to make the window.

---

### 0.3 — The line, then the title (0:45)

**Slide:** the line, alone on black.

> ## "Nothing here is a bad embedding.
> ## The retrieval did exactly what it was designed to do.
> ## **That's the problem.**"

**Slide:** title slide, only now.

> **Graph Algorithms for RAG** · Nathan Smith · KCDC 2026
> *(sequel line: last year — why a knowledge graph; this year — what the
> algorithms do with it)*

> Cosine similarity is doing its job perfectly. The job is the wrong job —
> and no amount of embedding-model upgrades changes what the job *is*.
>
> This hour is about what to do instead: four failures like this one, four
> graph algorithms, and the measured receipts for when each one helps — and
> when it doesn't. You might remember this Lewis and Clark dataset if you came to my talk at community days. In that session I demonstrated some benefits of GraphRAG in a side by side comparison with vanilla vector retrieval. Today's focus is on the value that graph algorithms add to our RAG stack, and we'll
> back to this exact question with a fix in section 5. 
>
> *(House-keeping in one breath: repo link is on the last slide, questions at
> the end.)*

Add a table of contents showing what we're going to cover during the session.

---

### Timing

| slide | min |
|---|---|
| 0.1 the question, live | 1:15 |
| 0.2 the reveal | 1:00 |
| 0.3 the line + title | 0:45 |
| **total** | **3:00** |

---

### Assets still needed

- [ ] **Vector-only demo entry point** — `demo_pagerank.py --vector-only` or a
      tiny `scripts/demo_baseline.py` that prints the top-8 with text
      previews and nothing else. The one code gate on this section.
- [ ] Terminal styled for the projector: font size, and the top-8 previews
      short enough that rank 1's "for his Services as an enterpreter" is
      legible from the back
- [ ] The 2-of-8 slide and the 69/67 build — text only, huge
- [ ] Title slide with the sequel line and last year's repo URL
- [ ] Rehearsal fallback: a screenshot of the live run, in case the DBMS
      isn't up at minute zero (the one demo with no warm-up time before it)


---

## Section 1 — What is a graph?

*deliberately fast · 3 minutes · starts 0:03* · source: [`section-01-slides.md`](section-01-slides.md)

> **Editorial constraints for this section:**
> - **Fast pass, one diagram.** The audience skews new but the algorithms are
>   what was sold; foundations get three minutes and a pointer to the
>   community days repo for the longer build.
> - **The diagram is this corpus**, not `(:Person)-[:KNOWS]->(:Person)`. Every
>   label and relationship type shown here reappears in sections 4–7, so this
>   section is secretly vocabulary pre-loading.
> - **One distinction gets the time: relationships are stored, not computed.**
>   Everything else is a definition said once.
> - Plant **degree** here. Section 5's close and section 9's routing rule turn
>   on "count the node's edges," and it costs five seconds to define now.

---

### 1.1 — Nodes and relationships (1:00)

**Slide:** the diagram — inline SVG, drawn from the live graph's actual shape.

```
                        MEMBER_OF
   (SACAGAWEA:Person) ────────────▶ (SHOSHONE:NativeNation)
          │
          │ MENTIONED_IN
          ▼
   (Chunk: 1805-08-17, Lewis)──NEXT_CHUNK──▶(Chunk: 1805-08-17, Clark)
```

> Nodes are things: a person, a nation, a passage of journal text. Labels say
> what kind of thing. Properties hang key-value data off them — a name, a
> date, and later, an embedding.
>
> Relationships connect two nodes, they have a type and a direction, and —
> the part that matters — **they are data**. `SACAGAWEA MEMBER_OF SHOSHONE`
> is a fact sitting in the database, written once at build time.
>
> This is the actual shape of tonight's graph: the Lewis & Clark journals,
> chunked, with the people, places, and nations mentioned in each chunk
> extracted and linked. Same corpus as last year's talk — that talk was about
> *building* this; the repo link at the end has the whole pipeline. Tonight is
> about what the algorithms do with it.

---

### 1.2 — The one distinction that matters (1:00)

**Slide:** side by side.

> | relational | graph |
> |---|---|
> | the connection is **computed** at query time — match IDs across tables | the connection is **stored** — follow the pointer |
> | cost grows with the tables you join | cost grows with the edges you touch |

> If you have only one takeaway from these three minutes: a JOIN *derives* the
> relationship every time you ask, by matching keys. A graph wrote it down.
> Traversing a million-node graph two hops out from one node touches a few
> hundred edges and never looks at the rest.
>
> That is the property every algorithm in this talk leans on. PageRank,
> community detection, path finding — they are all "follow edges, many times,
> fast," and they are only practical because following an edge is a pointer
> lookup, not a join.

They are also practical because many of the algorithms decompose to matrix multiplication. For example, we're not actually doing random walks when we calculate PageRank.

---

### 1.3 — The four words you need (1:00)

**Slide:** glossary, one line each.

> **Label** — what kind of node. `Person`, `Chunk`, `NativeNation`.
> **Relationship type** — what kind of edge. `MENTIONED_IN`, `MEMBER_OF`.
> **Property** — data on either. `canonicalName`, `date`, `embedding`.
> **Degree** — how many edges a node has. **Remember this one.**

> Four definitions and we're done with theory for the day.
>
> Degree gets a beat of its own: it is just a count of a node's edges, it
> costs one query, and by the end of the hour a single degree count will be
> deciding which retrieval strategy your pipeline runs. Cheap number, does a
> lot of work.
>
> Everything deeper — how the chunks were cut, how the entities were
> extracted, how the embeddings got there — is last year's talk, and the repo
> is on the final slide. Onward: what happens when you put a vector index and
> this graph in the same database.

---

### Timing

| slide | min |
|---|---|
| 1.1 nodes and relationships | 1:00 |
| 1.2 stored, not computed | 1:00 |
| 1.3 glossary + degree plant | 1:00 |
| **total** | **3:00** |

---

### Assets still needed

- [ ] The 1.1 diagram as inline SVG — real labels, real relationship types,
      readable node captions; reuse the visual language in sections 4–7 so
      the graph "looks the same" all hour

I can make these in arrows.app and export as SVG. No need for you to write the SVG code.

- [ ] The join-vs-pointer table styled as a slide (or a two-panel sketch:
      key-matching arrows vs a single fat edge)
- [ ] Glossary slide with **degree** visually set apart from the other three


---

## Section 2 — What is Graph RAG, and does it actually work?

*the architecture, the evidence, and the gift · 7 minutes · starts 0:06* · source: [`section-02-slides.md`](section-02-slides.md)

> **Editorial constraints for this section:**
> - **Handle the evidence honestly, out loud.** The NICD caveats — zero-shot
>   wins, refusal-flattered truthfulness, Neo4j funding — get stage time,
>   because they are more interesting than the headline and someone in the
>   room will look the paper up.
> - **Ghoshal stays off the evidence slides.** Two documents, LLM-judged, one
>   run — further-reading list only, plus his *reasoning vs coverage*
>   vocabulary, which Nathan borrows with attribution.
> - **The "zero tokens" beat is stated precisely** (corrected 2026-09-07): on
>   a natively-linked corpus it is zero, full stop; on an extracted corpus
>   like ours it is zero **additional** tokens — the community step is
>   token-free, but the mention edges it reads were paid for at extraction.
>   Section 6.3 repeats this precision; the two must match.
> - **The never-called tool is the hinge of the whole talk.** Land it slowly.
>   Everything from section 4 on is "what to put in the retrieval path," and
>   this is the beat that justifies that framing.
> - This section is the designated **compression victim** if rehearsal runs
>   long: the NICD table can drop to its two load-bearing rows (precision,
>   truthfulness). Marked inline.

---

### 2.1 — The architecture in one slide (1:00)

**Slide:** one diagram, no bullets.

```
                 ┌───────────────  one database  ───────────────┐
                 │                                              │
   question ──▶  │   vector index          knowledge graph      │
                 │   (chunk embeddings)    (entities, edges)    │
                 │          \                  /                │
                 │           ▼   one retrieval step  ▼          │
                 └──────────────────────┬───────────────────────┘
                                        ▼
                               context window → LLM
```

> Graph RAG is not "replace your vector search." Same chunks, same
> embeddings, same top-k entry point you already run. The difference is that
> the chunks sit inside a knowledge graph — the entities mentioned in each
> passage, and how those entities connect — and both are available to the
> **same retrieval step**, in the same query language, in the same
> transaction.
>
> One retrieval step. Not a vector call and then a graph service and then a
> reranker service. That locality is what makes everything in sections 4–7
> one query instead of an architecture diagram.

---

### 2.2 — Structure you can navigate (1:30)

**Slide:** the framing, attributed.

> ### "give the agent a structure it can navigate, not just a box it can search"
> — Zach Blumenfeld, *Scaling Karpathy's LLM wiki* (Neo4j blog)

**Slide (build):** the verbs.

> A vector store answers one question: *what's near this?*
> A graph adds verbs: **traverse · path · rank · cluster**

**Slide:** the token bill for that structure.

> On his wiki corpus, the community structure cost **zero tokens** — the links
> are native.
> On an extracted corpus like ours: zero **additional** tokens — the
> algorithms are token-free, the mention edges they read were paid for at
> extraction.

> Blumenfeld's post scales community detection over Karpathy's LLM-generated
> wiki, and the framing line is the best one-sentence pitch for Graph RAG I
> know. Similarity search gives you one verb. The graph gives you traversal —
> and that is where the algorithms live.
>
> The token beat, said precisely because section 6 collects on it: graph
> *algorithms* don't call a model. On a corpus with native links — a wiki, a
> codebase, a citation network — the whole structural layer is free. On our
> corpus the links came out of an LLM extraction pass, so the honest claim is
> zero *additional* tokens: once you've paid for extraction, every algorithm
> in this talk reruns on it for free, forever. That's the thesis of the
> roadmap coming in section 3: pay at build time, retrieve cheap at query
> time.

---

### 2.3 — Does it work? The evidence (2:30)

**Slide:** the study, sized before the numbers.

> **NICD, *Reducing hallucinations with GraphRAG*** — 510 multi-source
> questions (MoNaCo), 28,000 Wikipedia docs, three pipelines.

**Slide:** the table.

| | Vector RAG | Vector+graph | Zero-shot |
|---|---|---|---|
| Factual correctness (precision) | 0.15 | **0.36** | 0.43 |
| Factual correctness (recall) | 0.13 | **0.33** | 0.39 |
| Fine-grained truthfulness | 35 | **63** | 40.5 |
| Total tokens (median) | 41,694 | 45,695 | 1,108 |

*(Compression cut, if rehearsal needs it: keep the precision and truthfulness
rows only.)*

> The headline: adding the graph to vector RAG roughly **doubles** factual
> precision and recall, and wins fine-grained truthfulness outright, for about
> nine percent more tokens. That is the strongest published number I can hand
> you, and it's a real study — 510 questions, not a weekend demo.

**Slide (build):** the awkward parts, on screen in the same font size.

> - **Zero-shot beats both** on correctness — MoNaCo is public Wikipedia; the
>   model has memorized the corpus. The authors say so themselves.
> - **Coarse truthfulness favors plain vector RAG** (−31 vs −49) — because it
>   *refuses to answer* more often. Refusing isn't winning.
> - **The study was funded by Neo4j.** Disclosed in the paper. Now disclosed
>   here.

> Say all three before anyone asks. The zero-shot column is why "just use a
> bigger model" works on Wikipedia and not on your incident reports — your
> corpus isn't in the training set; that column vanishes on private data, and
> the other two don't.
>
> The refusal point cuts the other way: it's the same failure the cold open
> showed. Vector RAG hands the model *less* of the right context, the model
> balks more often, and a coarse metric scores the balk as honesty.
>
> And the funding: one sentence, costs nothing, buys the whole section its
> credibility. *(If it comes up in Q&A: independent write-ups — Ghoshal's
> weekend experiment is on the further-reading slide — reach compatible
> conclusions on the reasoning-vs-coverage split, at a fraction of the scale.
> Thin but independent, next to thorough but funded.)*

---

### 2.4 — The gift (1:30)

**Slide:** one fact, no chart.

> ## The agent in that study had a shortest-path tool.
> ## It was called **zero** times.
> ### Not once, in 510 questions.

> This is my favorite finding in the paper and it's in nobody's abstract. The
> agent had graph tools *available*. The system prompt encouraged them. And it
> never touched the path tool — it fell back to vector search, every time,
> because models reach for tools that look like what they saw in training.
>
> *(Beat.)*

**Slide:** the hinge.

> ### The lesson isn't "give your agent graph tools."
> ### **Put the graph algorithms in the retrieval path, deterministically —
> ### where the model doesn't get a vote.**

> This line is the spine of the rest of the hour. Every section from here on
> is about what belongs *in that path*: resolution before indexing, PageRank
> inside retrieval, community caps on the window, paths in the answer. Code
> that runs whether or not the model feels like it.

---

### 2.5 — Hand-off (0:30)

**Slide:** none — the roadmap is next.

> So: the graph gives retrieval verbs it doesn't have, the best available
> evidence says the combination roughly doubles factual quality on multi-source
> questions, and the model won't drive the graph by itself. Which leaves
> exactly one question — *what specifically do you put in the path?* Four
> failures, four algorithms.

---

### Timing

| slide | min |
|---|---|
| 2.1 architecture | 1:00 |
| 2.2 structure + zero-additional-tokens | 1:30 |
| 2.3 evidence + awkward parts | 2:30 |
| 2.4 the gift + the hinge | 1:30 |
| 2.5 hand-off | 0:30 |
| **total** | **7:00** |

---

### Assets still needed

- [ ] Architecture diagram as inline SVG — one database boundary drawn as one
      box; the "one retrieval step" caption is the point
- [ ] NICD table styled with the vector+graph column highlighted and the
      zero-shot column *not* grayed out (we argue against hiding it)
- [ ] "Called zero times" slide — text only, huge
- [ ] The hinge slide — this is the most-photographed slide in the talk after
      5.14's routing table; set it like one
- [ ] Verify the exact coarse-truthfulness values (−31 / −49) against the PDF
      (`nicd-reducing-hallucinations-graphrag.pdf`) before the scaffold —
      transcribed here from the outline


---

## Section 3 — Roadmap

*four failures, four algorithms, two stages · 1 minute · starts 0:13* · source: [`section-03-slides.md`](section-03-slides.md)

> **Editorial constraints for this section:**
> - One slide, one minute. The reframe gets said out loud; the table is left
>   on screen while it's said.
> - **Section titles here must track the section files** — §5's row currently
>   reads *"can't tell people apart"* to match `section-05-slides.md`'s
>   draft title, which still needs Nathan's sign-off. If that title moves,
>   this row moves with it.
> - §6's row says **Leiden**, not "Louvain / Leiden" — stage scope decided
>   2026-09-07 (Louvain is Q&A backup only).

---

### 3.1 — The map (1:00)

**Slide:** the table. This stays up for the full minute.

> | stage | the failure you've felt | the algorithm |
> |---|---|---|
> | **Build** | Your entities are a mess | node similarity + WCC |
> | **Query** | Your ranking can't tell people apart | personalized PageRank |
> | **Query** | Your context is redundant | Leiden |
> | **Query** | You can't explain the answer | Yen's k-shortest paths |

**Slide element (footer line, stays as the table is discussed):**

> *Build time makes the graph worth retrieving from. Query time decides what
> comes back. Skip the first and the second returns garbage.*

> Graph algorithms serve RAG at **two stages**, and the talk is honest about
> both. One section on build time — unglamorous, and it gates everything.
> Three on query time — where your retrieval actually improves.
>
> Each section opens the same way this talk did: with a failure you have
> already hit, whether or not you knew its name. If a row is a failure you
> genuinely don't have — some corpora don't — that section will also tell you
> so; part of the pitch is knowing when *not* to reach for the algorithm.
>
> *(Timekeeping anchor: this slide is minute 13-to-14. Section 4 starts on
> schedule or the cuts list comes out.)*

---

### Timing

| slide | min |
|---|---|
| 3.1 the map | 1:00 |
| **total** | **1:00** |

---

### Assets still needed

- [ ] The table as the talk's recurring visual — sections 4–7 each re-show it
      with their row highlighted (cheap in reveal.js: same slide, one class),
      so build it once, parameterized


---

## Section 4 — "Your entities are a mess"

*node similarity + WCC · 9 minutes · starts 0:14* · source: [`section-04-slides.md`](section-04-slides.md)

> **Editorial constraints agreed for this section:**
> - **No precision or recall percentages.** The gold set is a hand-built
>   reference, not ground truth. Claims on screen are things the audience can
>   check by eye: named nodes, a drawn chain, counts from a live run.
> - **The Sacagawea example is the spine.** Everything else hangs off it.
> - **No metric comparison table.** One diagram for OVERLAP, one throwaway line
>   about other corpora.

---

### 4.1 — The failure (0:45)

We should explain that these entities were extracted by LLM from unstructured text. You could have dupes like this in structured data too though.
**Slide:** the same man, five ways.

```
CLARK · CAPT. CLARK · WILLIAM CLARK · Capt Clark · Wm. Clark
```

**Every one of those is a separate node.**

> Retrieval for Clark silently misses most of Clark. No error, no warning, no
> stack trace — just quietly incomplete context, which is the worst failure mode
> RAG has. A wrong answer you can catch. A *thin* answer looks exactly like a
> good one.

---

### 4.2 — Now make it personal (1:00)

**Slide:** one number, large.

> # 8
> ### chunks in which Sacagawea is named

**Slide (build):** and the forms she is *actually* referred to by —

```
SACAGAWEA          INDIAN WOMAN        THE INDIAN WOMAN
OUR INDIAN WOMAN   THE INDIAN WOMAN WITH US
SQUAR              THE SQUAR           THE SQUAW
HIS SQUAR          SQUARWIFE           SQUAR INTERPRETRESS
SQUAR WIFE TO SHABONO                  JANEY
THE WIFE OF SHABONO    WIFE OF SHABONO    SNAKE INDIAN WIFE
INTERPRETERS WIFE      OUR INTERPRETER THE SNAKE WOMAN
```

**Nineteen nodes. One woman.**

> She is present for the entire expedition and named eight times. Ask this graph
> for Sacagawea and you get eight chunks' worth of someone who is everywhere.
>
> This is the section in one slide. Hold on it.

---

### 4.3 — The naive fix, and where it dies (1:15)

**Slide:** the string ladder, working.

| signal | catches |
|---|---|
| Jaro-Winkler | `BRATTEN` / `BRATTON` |
| token containment | `JOHN SHIELDS` / `SHIELDS` |
| double metaphone | `Chabonah` / `Charbonneau` — XPN vs XRPN |

> The journals spell Charbonneau at least six ways. Metaphone catches it: the
> letters diverge, the *sounds* do not. This ladder is good engineering and it
> gets you a long way.

**Slide:** then the wall.
squaw was part of the language at Lewis & Clark's time, but can be considered offensive today
> # SACAGAWEA → THE INDIAN WOMAN
> ### no string algorithm will ever connect these

> There is nothing to connect. Not a shared prefix, not a shared token, not a
> shared phoneme. The letters have run out. And this is not an edge case — it is
> *most* of the nineteen.

**Optional 5-second aside if the room is technical:**

```
apoc.text.jaroWinklerDistance('SHIELDS','SHIELDS')  =  0.0
```

> It returns a *distance*. The pipeline I ported this from compares it as a
> similarity — `jw >= 0.92` — so its string signal only ever fired on strings
> that were maximally *un*alike. Invisible bug, name of the function is the
> trap, fix is `1 - x`. Worth five seconds because everyone in this room has
> shipped one of these.

---

### 4.4 — How the original solved it (1:00)

**Slide:** a screenshot of `enrich_sacagawea.py`, the `SOURCE_URL` line highlighted.

```python
SOURCE_URL = "https://lewis-clark.org/people/sacagawea/sacagawea-in-the-journals/"
```

**It scrapes a curated list of her surface forms off a website.**

> And it works! Thirteen forms, hand-curated by historians, and the problem is
> solved for Sacagawea.
>
> It is also a third-party website hard-coded into a build pipeline. It exists
> because someone already did this by hand, for this specific expedition.
>
> **There is no lewis-clark.org for your corpus.**

> *(Beat. This is the turn — from "here is a fix" to "here is why we need an
> algorithm.")*

---

### 4.5 — You have more information than you think (1:15)

**Slide:** the idea.

> ## Two names that keep appearing alongside the same people, places and dates
> ## are probably the same entity

Include a diagram showing Sacagawea relationship to Indian Woman. It coulde be like the output of this Cypher query.

MATCH t1= (:Person {canonicalName:"SACAGAWEA"})-[:MENTIONED_IN]->()<-[:MENTIONED_IN]-(n:Person)
MATCH t2=(:Person {canonicalName:"INDIAN WOMAN"})-[:MENTIONED_IN]->()<-[:MENTIONED_IN]-(n)
WHERE n.canonicalName IN ['CAMEAHWAIT', 'TOUSSAINT CHARBONNEAU']
RETURN t1, t2

I saved it in docs as "sacagawea appears with indian woman.svg"

**Slide:** where the signal already is.

- entity ↔ entity co-occurrence, weighted by shared chunk count
- `gds.nodeSimilarity.filtered`, same-label
- union it with the string and alias signals
- **costs zero LLM tokens** — it is reading structure that extraction already built

**Slide — the one diagram.** Two overlapping circles, small one mostly inside the large one.

```
   SACAGAWEA                          INDIAN WOMAN
   appears alongside 51               appears alongside 174

              ╭─────────╮
              │   33    │╭──────────────────────────╮
              │         ││   18 shared  │   156     │
              ╰─────────╯╯ CAMEAHWAIT · HIDATSA ·   │
                          DREWYER · HORSES · CANOES │
                          ╰──────────────────────────╯

   OVERLAP  =  18 / 51   =  0.35    ← divide by the SMALLER circle
   JACCARD  =  18 / 207  =  0.09    ← divide by EVERYTHING
```

> A rare name and a common name for the same person have **lopsided**
> neighbourhoods. Jaccard divides by the union and punishes her for being rare.
> Overlap divides by the smaller set and asks the question we actually mean:
> *is the rare name's world contained in the common name's?*

**Throwaway line, then move on:**

> "Overlap fits this corpus because the duplicates are lopsided. If yours
> aren't, try the others — GDS gives you cosine and Jaccard on the same call."

*(No comparison table. No benchmark. Next slide.)*

---

### 4.6 — The payoff (1:30) · LIVE DEMO or recording

**Run:** `demo_resolution.py` against the graph built **without** the scraper.

**Slide:** the closed component.

```
INDIAN WOMAN  +  INTERPRETERS WIFE  +  SACAGAWEA  +  SQUAR INTERPRETRESS
+  SQUAR WIFE TO SHABONO  +  THE INDIAN WOMAN  +  THE INDIAN WOMAN WITH US
+  THE SQUAR  +  THE SQUAW  +  THE WIFE OF SHABONO
```

**Ten surface forms. One entity. No website.**

> Point at `SQUAR INTERPRETRESS`. That node appears in **one chunk**. One
> passage puts it in company nothing else shares, and that is enough — it ends
> up the hub that ties eight of the others together.

> **The line:** the graph found her the way a reader does — not by how the name
> is spelled, but by who she is always standing next to.

**Honest caveat, say it:**

> Nine of the nineteen are still missed. The scraped list still beats the
> algorithm on raw coverage. What the algorithm gives you is coverage that is
> *derived* — reproducible, and it works on a corpus nobody has written a
> website about.

---

### 4.7 — What it costs (1:00)

**Slide:** the uncomfortable part.

> ## On its own, the graph signal is bad.
> ### Hundreds of wrong pairs for every right one.

> Anyone who ships this unfiltered gets nonsense. I want to be straight about
> that, because the next slide is why it doesn't matter.

**Slide:** the division of labour.

> # Recall is what the algorithm is for.
> # Precision is what the adjudicator is for.

| | |
|---|---|
| 811 people in the graph | |
| every possible pair | **328,455** |
| what the signals propose | **~1,100** |
| what that costs to adjudicate | *fractions of a cent* |

> The algorithm's job is not to decide. It is to turn an O(n²) problem into a
> list short enough that something slower and better can read all of it.
>
> A signal with 1% precision is not a broken signal when something downstream
> can afford to filter it.

---

### 4.8 — WCC, and what it is actually for (1:30)

We need to explain what WCC is before we talk about what it's for. What problem does it solve?
**Slide:** the correction.

> ## WCC answers "are these connected at all"
> ## not "are these a topic"

> It gets taught as clustering and that is misleading. Run it on a raw corpus
> graph and you get one giant component and some dust. Here it does the one
> thing it is exactly right for: **transitive closure.** A≈B, B≈C, therefore one
> entity.
>
> The Sacagawea cluster is built from ten pairwise judgements. **No single one
> of them sees the whole identity.** WCC is what turns them into one node.

**Slide — the danger, in the same breath.** This is the strongest content in the section.

```
SACAGAWEA ──[HIS WIFE]── TOUSSAINT CHARBONNEAU ──[THE INTERPRETER]── GEORGE DROUILLARD
```

> I did this to my own graph. Sacagawea absorbed Drouillard.
>
> Ask the model directly and it gets the hard ones right: *is Sacagawea the same
> entity as George Drouillard?* No. *As Windsor?* No.
>
> But "his wife", beside Charbonneau, **is** Sacagawea. "The interpreter" **is**
> Charbonneau. And Drouillard **was** the sign-language interpreter. Each link
> defensible on its own — and closure turns them into one wrong entity.

**Slide:** and it gets worse — check what the model said about the *sparse* nodes.

```
SQUAR INTERPRETRESS  confirmed same as  TIN NACH-E-MOO-TOOLT  (Nez Perce)
                                        MAN-NES-SUR REE       (Hidatsa)
                                        CONIA COMAWOOL        (Clatsop)
```

> Three different Native leaders, from three different nations, all confirmed as
> Sacagawea. Each appears in exactly **one chunk**, and so does "squar
> interpretress". The model has nothing to tell them apart, so it reaches for the
> identity it recognises.
>
> So it is not that the model was perfect and the algorithm ruined it. That
> would be a comfortable story. **Sparse entities get bad answers from both
> halves** — and closure turns individual mistakes into one merged identity.

**Slide:** the rule.

> ## Fix what enters the candidate set, not what comes out of it.

> No amount of per-pair accuracy saves you here, because the pairs that fail are
> the ones nobody can judge. This pipeline has a `flag_generic_locations` step
> because "the river" is useless as a place. It has nothing equivalent for
> people — so "the interpreter", "his wife" and "squar interpretress" sit in the
> graph as first-class Person nodes, attracting bad matches and bridging
> identities.
>
> And adjudicate *before* you close, never after.

---

Take 4.9 out. I would just run a cypher query for this, not use a GDS algorithm. The GDS algorithm shows global common neighbors, which is what we want at build time.
### 4.9 — Same algorithm, query time (0:45)

**Slide:**

> ### "Find chunks that share entities with this chunk"
> ### is a different question from
> ### "find chunks that sound like this chunk"

> Node similarity is not only a build-time tool. Pointed at chunks instead of
> entities it retrieves — and it catches passages embeddings miss, because two
> chunks about the same episode can share almost no vocabulary while sharing the
> rare entities that make them the same episode.
>
> It comes back in section 8 as the `cooccurrence` strategy.

---

### 4.10 — Take home (0:30)

> ## Fix entity resolution before you tune retrieval.

> Personalized PageRank over a graph where Sacagawea is nineteen nodes will
> confidently rank the wrong passages — and it will look like it is working.
>
> Build time gates query time. That is the whole reason this section comes
> before the next one.

*(Hands directly to section 5.)*

---

### Timing

| slide | min |
|---|---|
| 4.1 the failure | 0:45 |
| 4.2 make it personal | 1:00 |
| 4.3 string ladder + wall | 1:15 |
| 4.4 the scraped website | 1:00 |
| 4.5 co-occurrence + OVERLAP diagram | 1:15 |
| 4.6 the payoff (demo) | 1:30 |
| 4.7 what it costs | 1:00 |
| 4.8 WCC + the bridge | 1:30 |
| 4.9 query time | 0:45 |
| 4.10 take home | 0:30 |
| **total** | **10:30** |

⚠️ **Over budget by 1:30.** The section is allotted 9:00. Cut candidates, in
order of preference:

1. **4.9 query time (−0:45)** — it is a trailer for section 8, not load-bearing her
2. **4.3's Jaro-Winkler aside (−0:20)** — delightful, entirely optional
3. **4.7 (−0:30)** — compress to the two-line "recall/precision" slide, drop the table

Cutting 1 and 2 lands at 9:25. Cutting all three lands at 8:55.

Cut 4.9. Keep 4.3 and 4.7

**Do not cut 4.2, 4.6 or 4.8.** Those are the section.

---

### Assets still needed

- [ ] OVERLAP two-circle diagram as inline SVG (spec above, real numbers)
- [ ] Bridge-node chain diagram as inline SVG
- [ ] Screenshot of `enrich_sacagawea.py` with `SOURCE_URL` highlighted
- [ ] Recording of `demo_resolution.py` (outline recommends resolution be
      pre-recorded rather than live — only two demos should be live)
- [ ] Decide which database 4.6 demos against — see note below

### Open decision

4.6 says "the graph built **without** the scraper". Today that is `rawluna`,
which is pre-disambiguation, so the *closed cluster* has to come from
`demo_resolution.py --adjudicate` rather than from merged nodes in the graph.
That is fine and arguably better — the audience watches it happen rather than
seeing a result. Confirm before recording.


---

## Section 5 — "Your ranking can't tell people apart"

*entity-seeded personalized PageRank · 10 minutes · starts 0:23* · source: [`section-05-slides.md`](section-05-slides.md)

> **⚠️ Title needs Nathan's sign-off.** The original was *"Your ranking is
> wrong"*, which promises an improvement this corpus does not deliver at the
> passage level. A second draft used *"can't combine evidence"*, written for a
> conjunction thesis that was measured and retracted. The current title matches
> what is actually demonstrable.
>
> **Editorial constraints agreed for this section:**
>
> - **Numbers are allowed on screen — but only ones that need no relevance
>   judgement.** Where a passage ranks, how often two questions return the same
>   entities, latency, whether `alpha=1.0` reproduces the baseline: all exact.
>   **The blend, damping and seed-count sweeps stay off the slides**, because
>   they were scored against a co-mention proxy that turned out to be
>   hub-contaminated (findings #4, #10). They are working notes, not evidence.
> - **No accuracy claims.** "Cosine returns the wrong interpreter" is checkable
>   on screen. "The blended results are better answers" needs a gold set and
>   belongs to section 8.
> - **Relevance judgements on this section's demo are hand-made**, by reading
>   sixteen passages in full (finding 5d). Say that from the stage. It is a
>   feature, not an apology.
> - **`charbonneau-role` is the spine.** Everything hangs off it.
> - **The three limits get stage time, not a footnote.** They are what makes the
>   multi-tool argument structural rather than a hedge.
> - **Every number in this section is `lewisclark`** (migrated 2026-09-07,
>   outline finding 5o; the old `neo4j` values are kept there as history). The
>   demo runs with `NEO4J_DATABASE=lewisclark` and `--seeder decomposed` —
>   `lewisclark` has no Person vector indexes by design, so the semantic seeder
>   cannot seed people there.

---

### 5.1 — The failure (1:15)

**Slide:** the question.

> ### "What was Toussaint Charbonneau's role on the expedition?"

**Slide (build):** what vector search returns, with the names in each passage.

```
1.  Chabono                         <- him: paid off "for his Services as an enterpreter"
2.  Duriaur                         <- a Sioux go-between
3.  (nobody)                        <- the return to St. Charles
4.  Dourion                         <- the Sioux interpreter
5.  Durion, Gravelin                <- Sioux and Ricara interpreters
6.  Drewyer, Charbono               <- him, in the departure roster
7.  (nobody)                        <- a Minetarree chief pays a visit
8.  Gravline                        <- the barge pilot
```

**Two of eight are about the man you asked about.**

> Four slots went to *other* French-speaking go-betweens on the same expedition.
> Two went to diplomatic scenes with no interpreter in them at all.
>
> And this is not a near miss. Sixty-nine passages in this corpus mention
> Charbonneau. **Sixty-seven of them are outside this window.**

**Slide:** the number.

| | passages | median rank | in top-8 |
|---|---|---|---|
| mention **Charbonneau** | 69 | **300** | **2** |
| interpreter vocabulary, not him | 101 | 576 | 2 |

> Nothing here is a bad embedding. Every passage it returned is about
> interpreting on the Lewis and Clark expedition. It answered the question I
> asked. It just answered it about the wrong person.

---

### 5.2 — Name it (1:00)

**Slide:**

> ## Co-typed entity substitution
> ### It answers *"an interpreter."* You asked about *"this interpreter."*
We didn't really ask about an interpreter. We asked about Charbanneau's role without saying interpreter.

**Slide:** why, in one line of arithmetic.

> ### A passage embedding is an average over ~330 words.

> The question encodes *interpreter, role, expedition* — and a French surname.
>
> In a passage about Dorion negotiating with the Sioux, the words *interpreter,
> chief, speech, presents, nation* recur throughout. They dominate that average.
> A name that appears **once**, between a weather note and a hunting tally,
> contributes a sliver.
>
> So the passage that is *actually* about Charbonneau sits **further** from the
> question than a passage about a different interpreter doing interpreter
> things. Cosine has no way to make identity a **hard** constraint — in a
> continuous space, "Dorion the Sioux interpreter" is genuinely near
> "Charbonneau the interpreter". They differ by one low-mass token and agree on
> everything else.

**Slide — take it home. This is the slide people will remember.**

> ## Your corpus has forty engineers.
> ## You ask what **Chen** owns.
> ## You get three passages about **Rodriguez** owning a similar service.

> Because *"engineer owns service"* is most of the sentence, and *"Chen"* is one
> word of it.
>
> *(Beat.)* Hold onto the forty engineers. We come back to them at the end.

---

### 5.3 — PageRank in 60 seconds (1:00)

**Slide:** the two questions.

> **PageRank:** what is important in this graph?
> **Personalized PageRank:** what is important *relative to these nodes?*

**Slide:** the honest aside. Fifteen seconds, and it buys the room.
Drop the plain PageRank side note and the pviot. We need to explain how personalized PageRank works. Make an annimation that shows mass iteratively being distributed from a source node to its neighborhood. Also explain how the damping factor works at this point.
> ### On an undirected graph, plain PageRank is a fancy degree count.

> The stationary distribution of an undirected random walk is *exactly*
> proportional to degree. PageRank adds teleport, which shrinks it toward
> uniform. If your graph is undirected, you have computed `count()` the
> expensive way.
>
> I reached for it on this project as a prominence prior for entity linking. A
> mention count beat it. Say so — it costs nothing and everything after it is
> trusted more.

**Slide:** the pivot.

> ## The interesting knob is not the algorithm.
> ## It's **where the walk starts.**

---

### 5.4 — Seed the entity. Seed all of them. (1:30)
The point this needs to emphasize is that our entity resolution is never going to be perfect, so we don't need to pick just one seed.


**Slide:** the fix, in one sentence.

> ### `MENTIONED_IN` is a **discrete** edge.
> ### Either extraction attached the entity, or it didn't.

> No averaging. Identity is binary. That is the hard constraint cosine can only
> express softly — and it is the whole trick.
>
> Median 40 words per entity in a 333-word passage. **The entity is a pointer.
> The embedding is an average.**

**Slide:** but don't pick one.

> Question mentions a tree. Your graph has four `POPULUS` species.
> **Which do you seed?**
>
> ## You may not have to choose.

> *(Speaker honesty note: I cannot show you that seeding all four beats picking
> the best one. I tried to measure it and my metric wasn't sensitive enough to
> tell — see the outline's finding 5d-quinquies. What I **can** show you is the
> next slide, which is the weaker and more interesting claim: picking the
> **wrong duplicate** costs you nothing.)*

**Slide — the live receipt.** Seeds chosen for the Pacific question, from the
question alone (`'Pacific' → fulltext`):

```
PACIFIC OCEAN   (WaterBody · 19 passages)   weight 0.605
PACIFIC OCIAN   (WaterBody ·  5 passages)   weight 0.395   <- Clark's spelling, unmerged
```

> It seeds **both** Pacific nodes. It does not know which is "real" and does not
> need to. Take an argmax over entity candidates and you have built a single
> point of failure into retrieval that fails *silently* when it picks wrong.
>
> And the weights are not a heuristic — they split by **passage count**, which
> makes seeding the two shards *arithmetically identical* to seeding the one
> node a resolution pass would have made, to first hop. You do not have to fix
> your entities before this works. You just do better when you have.
>
> **This is section 4's callback, twice over.** The duplicate that used to sit
> on this slide — a mislabelled second `SACAGAWEA` — is not in the graph any
> more, because section 4's machinery merged it. The pipeline left `PACIFIC
> OCIAN` behind instead. There is always another duplicate.
>
> *(Honesty line, worth five seconds: this insurance only covers duplicates
> that share a token. `DREWYER` and `GEORGE DROUILLARD` — one man, no shared
> token — do NOT get hedged: ask with either spelling and you seed only that
> shard. A spelling shard is build-time work, which is the Q&A pocket behind
> 5.14 — outline finding 5k.)*

**Slide — and the passage that proves the mechanism.** Cosine rank **20**,
305 characters, and it **never says her name**:

> `1804-11-04` *"a french man by Name Chabonah, who Speaks the Big Belley
> language visit us, he wished to hire & informed us his 2 Squars were Snake
> Indians, we engau him to go on with us and **take one of his wives to interpet
> the Snake language**"*

> That is the hiring *and* the arrangement — he speaks Hidatsa, she interprets
> Shoshone. It is the best single passage in the corpus for "which nations did
> Sacagawea interpret for, and how did that work."
>
> Cosine buried it because it is short and never names her. **The graph reaches
> it because extraction resolved "one of his wives" → `SACAGAWEA` and "Snake
> Indians" → `SHOSHONE`.**
>
> The entity layer is carrying a coreference the text never states. That is
> build-time work paying off at query time, on one passage you can read from
> the back of the room.

---
I don't think we have time to go into this. Just say we're walking on the MENTIONS graph.
### 5.5 — The graph you walk on is a decision (0:45)

**Slide:** two projections.

| | `lc-retrieval` | `lc-mentions` |
|---|---|---|
| relationships | MENTIONS, NEXT_CHUNK, RELATED | **MENTIONS only** |

**Slide:** why throw two thirds away.

> `MENTIONED_IN` is the only relationship here whose direction is *honestly*
> symmetric — "entity appears in passage" is co-membership.
>
> The extracted entity-to-entity edges are not. `MET` and `MARRIED_TO` are
> symmetric. `MEMBER_OF` and `TRIBUTARY_OF` flow importance toward the
> container. `SHOT` carries none at all. PageRank needs an outbound edge to mean
> **one consistent thing** — and for the symmetric types, the direction is
> partly an artifact of which entity the extractor happened to name first.
>
> `NEXT_CHUNK` is a chain, so it leaks walk mass into passages that are merely
> *adjacent in time.*

> ## A projection is not neutral infrastructure.
> ## It encodes what you're optimising for.

---

### 5.6 — The hub trap (1:15)

**Slide:** top entities by how many passages mention them.

```
825  MERIWETHER LEWIS         <- 28% of the corpus
587  CERVUS CANADENSIS        (elk)
506  WILLIAM CLARK
458  ODOCOILEUS HEMIONUS      (mule deer)
396  BISON BISON
348  MISSOURI RIVER
297  DREWYER
```

> **Lewis is in 28% of the corpus — and the elk outranks Captain Clark.** A
> daily record of what the party shot and ate. Whatever you assumed your hub
> was — check: on the previous extraction of this same corpus, the
> *white-tailed deer* outranked both captains. A better extractor moved the
> hub. It did not remove it.
>
> And row seven: `DREWYER`, 297 passages. `GEORGE DROUILLARD` is a **separate
> node**. Section 4's unresolved entities, on screen, for free.

**Slide:** what hubs do to a naive walk — and what three choices do about it.

| graph | walk | edge weights | same top-8 entities across questions |
|---|---|---|---|
| all three types | long (d=0.85) | none | **2.84 / 8** · Lewis ranks **3.2** |
| all three types | long | IDF | 2.04 / 8 |
| all three types | short (d=0.45) | none | 1.27 / 8 |
| **mentions only** | **short** | **IDF** | **0.47 / 8** · Lewis ranks **18.1** |

> Top row is the configuration everyone writes first: all your edges, damping
> 0.85 because that is the number in every tutorial, no weighting because why
> would you weight. Fourteen different questions and the walk returns **nearly
> three of the same eight entities** every time — and Lewis is in the top
> handful for *every* question, whatever you ask.
>
> **Three choices, and each one helps on its own — it takes all three to
> finish the job.** Drop the edges whose direction is meaningless. Shorten the
> walk. IDF-weight the mentions:

```cypher
log(1.0 + toFloat($totalChunks) / df)   AS weight
```

**Slide — the mechanism, because this is the part that transfers.**

> ## Hubs **concentrate** at the entity level and **dissipate** at the passage level.

> A hub receives mass from all 825 passages that mention it — then sprays it
> back across all 825, so each gets almost nothing.
>
> Which is why my passage ranking never looked broken while the entity ranking
> was garbage. **If you consume the entity set** — graph expansion, subgraph
> extraction, community seeding — this bites hard. If you only read passages off
> the end, you may never notice it happening.

---

### 5.7 — Keep the walk short (0:30)

**Slide:** damping is a horizon, not a magic number.

> ### share of walk mass within *k* steps = `1 − d^(k+1)`

| damping | mass within 3 steps |
|---|---|
| 0.45 | **96%** |
| 0.85 | **48%** |

> Three steps is what you want on a bipartite graph. From an entity seed: step 1
> is the passages that mention it, step 3 is the passages of its co-mentioned
> entities. That is the neighbourhood.
>
> `0.85` — the tutorial default, including in tutorials I have written — puts
> less than half the walk mass inside it. Measured on this corpus, shorter was
> better at every value we tried.

---

### 5.8 — The blend, and one honest knob (0:45) · abstract takeaway #2

**Slide:** the credibility move.

> # alpha = 1.0
> ### reproduces the vector baseline byte for byte
> ### 14 questions, 14 identical orderings

> Before I show you a knob, I want you to trust it is a real knob and that I
> have not quietly swapped the baseline underneath it.

**Slide:** where to combine.

> ### Two places to blend similarity and structure:
> ### in the **seed weights**, or in the **final score**.

> Weight the restart distribution by semantic match and structure operates *on*
> a semantically-informed prior. A post-hoc linear blend has the two signals
> fighting after the fact. Seeding is the better one.
>
> The mixing weight itself turned out to be forgiving over a wide range on this
> corpus — which is the useful news. It is not a delicate parameter. I am not
> going to put a sweep on screen, because the only relevance measure I had for
> it was a proxy I later found broken, and I would rather show you passages.

---

### 5.9 — The payoff (1:30) · LIVE DEMO

**Run:**
`NEO4J_DATABASE=lewisclark python scripts/demo_pagerank.py "What was Toussaint Charbonneau's role on the expedition?" --seeder decomposed`

**Slide:** the seed it chose from the question alone.

```
named in the question:  'Toussaint Charbonneau'  (Person, via fulltext)

TOUSSAINT CHARBONNEAU   (Person)   weight 1.000
```

> One seed — because the question names one entity, and the seeder now *names*
> entities instead of embedding the whole question. The old semantic seeder
> added two degree-1 relatives that each spiked one arbitrary passage; they are
> simply gone (outline finding 5f).

**Slide:** what the window looks like now.

> ### Cosine top-8: **2 of 8** passages carry him.
> ### Blended top-8: **6 of 8.**

**Slide:** the two promotions worth reading, and what each one adds.

```
1805-03-18   "Mr. Tousent Chabono, Enlisted as an Interpreter this evening"
             -> the hiring itself            (cosine rank 22)

1805-04-07   "Shabonah and his Indian Squar to act as an Interpreter &
              interpretress for the snake Indians"
             -> the assignment: WHICH language, and why her   (cosine rank 27)
```

> Cosine's own #1 was the *end* of the story — the 1806 settlement, "Settled
> with Touisant Chabono for his Services as an enterpreter … 500$ 33⅓ cents."
> The graph adds how the job **began** and what it actually **was**. Beginning,
> job description, and payoff — cosine had one of the three.

**Say this plainly — it is the section's integrity:**

> I judged these by reading them. Eleven promoted passages across three
> questions, read in full, one question each: *does this contain something a
> correct answer needs that no cosine passage has?*
>
> **Three of eleven cleared that bar.** Not a rout. I had a metric that said it
> was much better than that, and the metric was measuring the wrong thing — so I
> read the passages instead. If you take one methodological thing from this talk,
> take that.

---

### 5.10 — Three things it cannot do (1:15)

**Slide:** all three, measured.

> ### 1. It combines evidence — but you don't choose the weights.

> Good news first: additivity **is** a conjunction bonus. Seed `SACAGAWEA` and
> `CHARBONNEAU` — comparable degree, 85 and 69 passages — and every one of the
> seventeen passages mentioning **both** lands in the top-20, median rank **9**,
> against 104 and 44 for passages mentioning either alone.
>
> Now seed `MERIWETHER LEWIS` (825 passages) with `CYNOMYS LUDOVICIANUS` (42).
> A passage mentioning **only the prairie dog** scores 0.00633. One mentioning
> **both** scores 0.00672. A 6% bonus for also being about Lewis.
>
> Because each seed's contribution is roughly `1 / its degree`. **Pair a rare
> entity with a hub and the hub is nearly free to ignore** — and you did not
> pick that weighting, your graph did.
>
> *(And no, you can't just normalise the seeds to equal footing. I tried. It
> gives you a beautiful conjunction signal and it drops every passage I'd
> hand-verified out of the top-8 — because normalising a sparse walk hands its
> noise floor 66% of the score range. The un-normalised sum is quietly weighting
> each seed by how much it actually knows.)*

> ### 2. It cannot enumerate or order.

> *"What was happening in the days before Sergeant Floyd died?"* — 18 passages
> exist in that week. Cosine's top-8 contains **3**. So does every graph variant
> I tried, including one with the journal's own `NEXT_CHUNK` sequence and a long
> walk: **3 of 18**.
>
> A date filter returns all eighteen in one hop. Nothing in those passages'
> vocabulary *or* entity structure says "the days before Floyd died". Only the
> date does.

> ### 3. It is bounded by extraction.

> *"When was the keelboat sent back down the Missouri?"* — the boat the entire
> first year of the expedition happened on. Here is every keelboat entity in
> the graph:

```
'keelboat'  ->  (nothing)
```

> **There is no keelboat.** The journals call it "the barge" or "the boat," the
> extractor never promoted it to an entity, and the seeder honestly reports the
> miss. The April 7th 1805 passage that answers the question exists — and
> nothing can seed a node that was never built.
>
> The structure that would answer this question was never built. **No ranking
> algorithm fixes that.**
>
> *(And say the coda — it is the honest version of hope: on the previous
> extraction, the receipt on this slide was a horse missing from a
> horse-trading passage. The better extractor fixed that one — that passage now
> carries a `HORSES` tag and the walk ranks it #1 for the horse question. It
> still built no keelboat, and 129 passages — 4.4% of the corpus — carry zero
> entities and are invisible to any walk. Better extraction moves the boundary.
> It does not remove it.)*

**Slide:** so —

> ## Three retrieval modes. Three different things they can't do.
> | | good at | blind to |
> |---|---|---|
> | cosine | topical resemblance | telling same-type entities apart |
> | entity-seeded PPR | identity, corroboration | ordering, completeness, choosing its own weights |
> | Cypher / filters | exact enumeration and constraints | anything you can't write down |

> This is why the answer is not one retriever. It is knowing which question
> you have.

---

### 5.11 — What it costs (0:45)

**Slide:**

| | |
|---|---|
| project the graph | **67 ms**, once |
| plain cosine top-8 | **6 ms** |
| this, on a fresh question | **~215 ms** |

**Slide:** and the one-line fix that got it there.

```
sourceNodes: [[nodeId1, bias1], [nodeId2, bias2], …]
```

> `sourceNodes` takes the whole seed set in one call — **with per-seed bias.**
> One call with eight sources: 66 ms. Eight separate calls: 494 ms. The cost is
> per-call overhead, not source count.
>
> I built it one call per seed, because I assumed weighted seeds required it.
> They don't.

> ## Read the signature before you design around it.

**Slide:**

> ### ~35× plain vector — and it doesn't matter.
> The generation call you're about to make dwarfs 200 ms.

---

### 5.12 — The question that names nothing (1:00) · `lewisclark`

> The section so far said: name the entity, make identity the hard
> constraint. Fine. Now take that away.

**Slide:** the question.

> ### "What goods did the expedition trade with Native nations along the route?"
>
> ### Entities named: **none.**

> The decomposer parses this and comes back empty — correctly. There is no
> tag to filter on. Every trick in this section so far is off the table, and
> cosine is the only baseline that even runs.

**Slide (build):** what cosine returns.

```
1.  a trader inventory: guns, kettles, beads...     (Lewis's copy)
2.  the same inventory                              (Clark's copy)
3.  who the coastal traders might be
4.  Clark trading for horses                        <- the expedition, at last
5.  Skillute middlemen moving pounded fish
6.  the beads-as-currency passage                   (again, twice)
...
```

> Two of eight show **the expedition** trading anything. The question says
> *goods*, and cosine faithfully retrieves the passages that **describe**
> goods — inventories, other people's commerce — including the same journal
> entry twice, once per captain.

**Slide — the promotion.** Cosine rank **77**. Carried by `BUTTONS` — a
`Supply` node in **5** passages:

> `1806-06-02` *"having exhausted all our merchandize we are obliged to have
> recourse to every subterfuge... our traders McNeal and York were furnished
> with **the buttons which Capt. C. and myself cut off our coats**, some eye
> water and Basilicon which we made for that purpose... in the evening they
> returned with about 3 bushels of roots and some bread"*

> The captains cutting the buttons off their coats to buy food. The best
> trade-goods passage in the corpus, and cosine had it at 77 — because it
> doesn't *describe* trade goods, it *spends* them.
>
> Blend in a short walk from cosine's own top passages and it crosses the
> goods themselves — BUTTONS, COATS, ELKSKINS, five-passage Supply nodes —
> from the inventories to the transactions. The gun paid to Twisted Hair for
> horse-keeping comes in from rank **112** the same way. Window coverage goes
> from 3 months of the journey to 7.
>
> **Cosine retrieves the description of the theme. The walk retrieves its
> instances.** When the question names nothing, that walk is the only
> identity signal you have.

---

### 5.13 — The answer is a name you don't have (1:00) · `lewisclark`

**Slide:** the question.

> ### "What do we know about Sacagawea's brother?"

> Sixteen passages in this corpus are about her brother. Here is everything
> failing to find them, and I want to show you the failure because the
> *reason* is one number.

**Slide (build):** the whiff, all three modes.

| mode | its top-8 contains |
|---|---|
| cosine | tomahawk recovery, horse butchering — **0 of 16** |
| filter on SACAGAWEA | can only ever see **2 of 16** — he's mostly in passages she isn't |
| blend with the walk | her biography — **0 of 16** |

> The filter isn't blind by accident — you can't filter on a name you don't
> know; **not knowing it is the question.** And the walk from SACAGAWEA
> genuinely reaches him: exactly **2** of her **85** passages also mention
> her brother. Two edges of eighty-five. About 2% of the walk's mass crosses
> that bridge, and no damping value turns 2% into a top-8.

**Slide — prove the bridge is real.** Delete those 2 passages from the
projection and rerun:

> ### median rank of his passages: **338 → 601.** All fourteen fall.

> The mass crosses exactly where the mechanism says. There just isn't enough
> of it — the anchor is too famous.

**Slide — what the walk actually did.**

> ### Pure walk, rank **4**: *"Charbono, the Indian Woman, **Cameahwait** and about 50 men... arrived"*
> ### Cosine had this passage at **1187**.

> One-shot retrieval can't answer this question. But the walk's top-8 hands
> you the thing you were missing — **the name**. Query CAMEAHWAIT and all
> sixteen passages are simply his tag set. On a famous anchor, this is a
> **two-step retrieval**: the walk performs the name-discovery step.
>
> And when the anchor is *obscure*, one shot works: same question shape for
> the Walla Walla chief who hosted them — an anchor in **3** passages, not 85
> — and the blend puts his chunks at median rank **10**, including four that
> no filter can reach because no spelling of the nation is tagged on them.

---

### 5.14 — Take home: one number decides (0:30)

> ## Cosine retrieves the topic. The **entity layer** retrieves the entity.
> ## And the seed's **degree** tells you which tool to spend.

**Slide:** the decision rule. This is the slide people photograph.

> ### Resolve the question's mentions. Count their passages. Then:
>
> | the question... | do this |
> |---|---|
> | names a well-tagged entity in **many** passages | **filter on the tag and stop** — the walk just dilutes |
> | names an entity in **few** passages | **walk** — the filter can't fill a window, and the bridges are strong |
> | names someone *related to* the answer | walk for the **name**, then query the name |
> | names **nothing** | walk from cosine's top passages — nothing else runs |

> That count is one Cypher query, before you retrieve anything. Forty
> engineers and you asked what Chen owns? Chen is tagged everywhere he
> matters — filter and go home early. Asked about Chen's *predecessor*,
> whoever that was? That's the walk finding you a name. Asked "who owns
> something like this" with no name at all? That's the walk or nothing.
>
> Section 9 shows this as the routing rule your agent actually executes, with
> the measured curve behind it.
>
> One CEO, one product, one customer? Save yourself the projection — and
> probably the tags too.

*(Q&A pockets, not stage time: filter parity on single-entity questions is
finding 5g; the thematic hand reads and the illness counter-case are 5l; the
brother case, delete-test and Walla Walla replication are 5m; the 38k-pair
decay curve is 5n.)*

*(Hands to section 6 — and this is now a measured fact, not a segue: the same
walk that won trade-goods collapsed the illness question into one week at
Long Camp, 7 of 8 passages about the same sick child. "And now every passage
in that window is about the same afternoon." Section 6 is the fix.)*

---

### PARKED FOR §9 — the routing rule as the implementation beat

> **Not §5 stage time — and now transcribed: the canonical copy is slide 9.1
> in [`section-09-slides.md`](section-09-slides.md) (moved 2026-09-07).** Kept
> here as the block's origin since the numbers are §5's (finding 5n); edits
> belong in the §9 file. It coexists with §10's take-home #2 ("in the
> retrieval path, not the agent's toolbox") — the router IS retrieval-path
> code.

**Slide:** the curve. 38,098 anchor–satellite pairs, median walk-rank of the
satellite's unshared passages, by anchor degree:

| seed's passage count | median rank of the neighbor's passages | reaches top-50 |
|---|---|---|
| 2–5 | **39** | 59% of pairs |
| 6–15 | 112 | 23% |
| 16–40 | 223 | 5% |
| 41–100 | 388 | 0% |
| 300+ | 1,058 | 0% |

> Monotonic, no exceptions. The two cases you saw in section 5 sit on it:
> the Walla Walla chief (anchor df 3) came back at 16; Sacagawea's brother
> (anchor df 85) at 338. The mechanism is the bridge fraction — how much of
> the seed's edge mass points toward the answer — but you can't observe that
> before retrieving. Degree you can. It's `MATCH (e)-[:MENTIONED_IN]->(c)
> RETURN count(c)`, and it routes the query before you spend anything.
>
> Thresholds are this corpus's; the shape is what transfers. Measure your own
> — the harness is in the repo (`measure_bridge_decay.py`, no relevance
> judgements required).

---

### Timing

| slide | min |
|---|---|
| 5.1 the failure | 1:15 |
| 5.2 name it + forty engineers | 1:00 |
| 5.3 PageRank in 60s | 1:00 |
| 5.4 seed the entity, seed all of them | 1:30 |
| 5.5 the projection is a decision | 0:45 |
| 5.6 the hub trap | 1:15 |
| 5.7 keep the walk short | 0:30 |
| 5.8 the blend | 0:45 |
| 5.9 the payoff (demo) | 1:30 |
| 5.10 three things it cannot do | 1:15 |
| 5.11 what it costs | 0:45 |
| 5.12 the question that names nothing | 1:00 |
| 5.13 the answer is a name you don't have | 1:00 |
| 5.14 take home: one number decides | 0:30 |
| **total** | **14:00** |

⚠️ **Over budget by 4:00.** Allotted 10:00. The close grew from 0:30 to 2:30
when 5l/5m/5n landed (2026-09-07); the decay curve is already parked for §9
rather than told here. Getting to 10:00 takes the original five cuts plus
trims *inside* beats previously marked untouchable — **flagged for Nathan's
rehearsal call, not applied silently:**

| cut | saves | running |
|---|---|---|
| drop **5.5**, keeping only the "a projection is not neutral infrastructure" line inside 5.4 | 0:45 | 13:15 |
| fold **5.7** into 5.6 as one sentence | 0:30 | 12:45 |
| drop **5.3's** degree-count aside | 0:15 | 12:30 |
| drop **5.11's** `sourceNodes` retraction, keep the cost table | 0:20 | 12:10 |
| compress **5.8** to the `alpha=1.0` slide alone | 0:25 | 11:45 |
| **5.6**: show only the first and last rows of the four-row hub table | 0:30 | 11:15 |
| **5.9**: one promoted passage instead of two (keep the enlistment; drop the Snake-assignment roster) | 0:15 | 11:00 |
| **5.10**: drop the normalisation parenthetical in limit #1 | 0:15 | 10:45 |
| **5.4**: drop the speaker-honesty parenthetical (the 5d-quinquies caveat moves to the outline pocket) | 0:15 | 10:30 |
| **5.2**: tighten the passage-average mechanism to two sentences | 0:15 | 10:15 |
| **5.13**: compress the Walla Walla contrast to its one-line landing (the full case is a Q&A pocket) | 0:15 | **10:00** |

I support all these cuts.

**Do not cut 5.1, 5.2's forty-engineers slide, 5.4's Nov-4 passage, 5.9, the
three limits of 5.10, or any of 5.12–5.14.** The old close (tags-vs-graph
rule) is not lost — it *is* 5.14's first and last table rows, now with
measured receipts behind every row.

**If Nathan prefers not to trim inside 5.2/5.4/5.9/5.10:** the alternative
that fits is moving **5.12** (the thematic beat) to §6's opening — the
illness collapse is literally §6's motivating failure, and trade-goods can
open §6 as "here's the walk winning, and here's the same walk needing the
community cap". That saves 1:00 here and costs §6 the same, so it is a
section-budget trade, not a cut.

---

### Assets still needed

- [ ] 5.1's tagged top-8 as a slide where the "wrong name" column reads at a
      glance — the names are the punchline, set them large
- [ ] The forty-engineers slide. Text only, big. No diagram.
- [ ] Hub table styled so Lewis-at-28%-of-the-corpus and elk-above-Clark land
      without explanation (source: `NEO4J_DATABASE=lewisclark
      demo_pagerank.py --hubs`)
- [ ] "Concentrate at the entity level, dissipate at the passage level" as
      inline SVG — one hub, many arrows in, the same many arrows out, thin
- [ ] Bipartite 3-step diagram for 5.7: entity → passages → co-mentioned
      entities → their passages
- [ ] 5.10's keelboat receipt: `'keelboat' → (nothing)` set large — possibly a
      ghosted, struck-through `KEELBOAT` node beside the April-7 passage
- [ ] `demo_pagerank.py` recording as backup; **this should be one of the two
      live demos** — it is the payoff and it runs in ~215 ms
      (`NEO4J_DATABASE=lewisclark`, `--seeder decomposed`)
- [ ] 5.12: the buttons passage set large, with the carrier line
      (`BUTTONS · Supply · 5 passages · cosine rank 77`) as a caption
- [ ] 5.12: cosine's trade-goods top-8 as a labeled list where "the same
      inventory, twice" reads at a glance
- [ ] 5.13: the three-mode whiff table; then the delete-test as a single
      before→after arrow (338 → 601, "all fourteen fall")
- [ ] 5.13: the rank-4 passage with **Cameahwait** highlighted — the name
      appearing is the slide
- [ ] 5.14: the routing table styled as the photograph slide (peer of 5.2's
      forty engineers)
- [ ] §9 (parked): decay curve as a simple bar or line from
      `results/bridge-decay-lewisclark.csv` — six bins, one falling line

### Open decisions

1. **The title.** *"Your ranking can't tell people apart"* — needs sign-off.
2. **Which database — DECIDED and MIGRATED (2026-09-07): `lewisclark` for
   everything.** 5.1–5.11 re-measured on `lewisclark` in the migration
   conversation; 5.12–5.14 were already `lewisclark`. The full old-vs-new
   record, methodology notes, and the redone hand read live in the outline's
   finding 5o; the `neo4j` numbers are kept there as history. The hand-read
   judgments in 5o are the migrating session's and await Nathan's read.
3. **How much of the retraction to tell.** 5.9 currently spends ~20 seconds on
   "my metric was measuring the wrong thing, so I read the passages." I think it
   is the most valuable twenty seconds in the section. It is also the easiest
   thing to cut if a rehearsal runs long, and Nathan may prefer to keep the
   methodology out of a 10-minute slot.

1. Title is fine
2. Don't use neo4j database for anything
3. Don't tell the retraction story

**Decided (2026-09-07):** 5.12 is the tags-vs.-graph decision rule;
the filter-parity finding (outline 5g) gets **no stage time** — it is the Q&A
pocket behind 5.12. Title remains open (decision #1).

**Redrafted (2026-09-07, later):** the close is now the 5l/5m/5n story —
5.12 the thematic win (buttons), 5.13 the brother question (whiff → the name
→ two-step), 5.14 the routing rule, with the decay curve parked for §9. The
old tags-vs-graph rule survives as 5.14's table rows. Consequences needing
Nathan's sign-off: (a) the 10:00 fit now requires trims inside beats the
draft previously protected — see the cut table; (b) alternatively 5.12 moves
to open §6 (a budget trade, argued under the cut table). The former (c) — the
`neo4j`/`lewisclark` split across the section — is resolved: the migration
landed 2026-09-07 and every beat now quotes `lewisclark` (outline finding 5o).


---

## Section 6 — "Your context is redundant"

*community detection: Louvain, Leiden, conductance · 6 minutes · starts 0:33* · source: [`section-06-slides.md`](section-06-slides.md)

> **Editorial constraints for this section:**
>
> - **Every number on screen is either exact or a hand read, and says which.**
>   Community counts, months, community ids, cosine ranks, conductance: exact.
>   "The recovered passages are the right ones": judged by reading, said so
>   from the stage — same posture as section 5.
> - **The cold open is inherited, not invented.** Section 5 *measured* the
>   illness collapse (finding 5l) and handed it here. Play it as continuity:
>   the best retriever so far caused the worst window.
> - **Leiden only on stage — Nathan's call, 2026-09-07.** Six minutes doesn't
>   fit two algorithms. Louvain gets at most a name-drop in a speaker note; the
>   measured Louvain material (the 1,089-node disconnected community, the
>   partition redrawing every run — findings 6a/6b) stays in the outline as
>   Q&A backup, not slides.
> - **The honesty beats get stage time**: Leiden's connectivity asterisk and
>   the community-vs-episode grain mismatch. Each is a one-query demonstration
>   — they *are* the talk's thesis, not hedges on it.
> - Every window below is from the seeded-Leiden run
>   (`measure_communities.py`, byte-identical across re-runs). If asked about
>   Louvain: agreement with these windows was 8/8 on trade/food every draw,
>   6–7/8 on illness — and it redraws, which is why it isn't the demo.

---

### 6.1 — The failure (1:00)

**Slide:** section 5's parting shot, replayed.

> ### "What illnesses and injuries did the corps deal with?"

**Slide (build):** the expansion walk's top-8 — just the dates.

```
1806-05-24 · 1806-05-27 · 1806-05-22 · 1806-05-24
1806-05-22 · 1806-05-26 · 1806-05-24 · 1806-05-28
```

**One week. Twenty-eight months of journals, and every slot is the same
medical drama at Long Camp.**

**Slide (build):** the same eight chunks — just their community ids.

```
c23 · c23 · c23 · c23 · c23 · c23 · c23 · c23
```

> Section 5's walk earned its place: it won trade-goods and food-sources by
> reading. And on this question it produced the worst window in the talk —
> because the rare entities that make a theme retrievable all co-occur in one
> episode, so conjunction-seeking *is* episode-seeking. Recall metrics would
> never show you this; every one of these passages is genuinely about illness.
>
> The second build is the whole section: the failure is *structural*, and the
> structure that names it — "these are all one cluster" — is computable from
> the graph we already have. No LLM, no labels, no gold set.

---

### 6.2 — Leiden (1:00)

**Slide:** the one-line definition, against section 4's.

> **WCC** (section 4): *connected at all* — one path suffices.
> **Leiden**: *densely connected relative to chance* — neighborhoods,
> not reachability.

Include a diagram that shows nodes colored by Leiden community. All are one WCC, but they represent several Leiden communities.

**Slide (build):** one call, and it's repeatable.

Don't show Neo4j syntax in the deck if we can help it. Try to make this vendor neutral. We for sure don't need this cypher here.
```cypher
CALL gds.leiden.mutate('lc-retrieval', {
  mutateProperty: 'communityId',
  relationshipWeightProperty: 'weight',
  randomSeed: 42, concurrency: 1      // same partition, every run
})
// 47 communities · all 2,913 chunks covered · ~100 ms
```

**Slide:** the honesty beat.

> Leiden *guarantees* internally connected communities.
> Ours had **one 24-node community split 13 / 11**. Verify — it's one WCC
> call per community, and you already know WCC from section 4.

> Same family of algorithms as section 4's WCC, opposite question: not "can
> you get there at all" but "is this neighborhood denser than chance predicts."
> Leiden is the current standard for that (the successor to Louvain, if you've
> met it), and it takes a random seed — which matters here, because this talk's
> discipline is re-run-and-diff, and an algorithm that redraws its themes every
> run can't be measured or demoed.
>
> The asterisk is the section in miniature: the algorithm's *paper* guarantees
> connectivity; the implementation on your graph is a claim to check, and the
> check costs one query. Verify; don't trust the name.

---

### 6.3 — The table of contents nobody wrote (0:45)

We need to explain the projection that Leiden used.

**Slide:** the themes table, live output (`demo_communities.py`).

```
 id  chunks  span                 cond.  defining entities
 5      691  1804-05 → 1806-09    0.37   MERIWETHER LEWIS, CERVUS CANADENSIS, WILLIAM CLARK
 23     286  1804-05 → 1806-09    0.39   PRYOR, SHIELDS, SHANNON, GASS, SACAGAWEA
 8      275  1804-05 → 1806-09    0.25   MANDAN, HIDATSA, SIOUX, ARIKARA, CORN, FORT MANDAN
 44     212  1804-07 → 1806-08    0.34   CLATSOP, SAGITTARIA LATIFOLIA, NETUL, SALT
 24     160  1804-10 → 1806-08    0.38   SHOSHONE, HORSES, NEZ PERCE
 …
```

> The corpus's own structure, summarized: the daily hunting economy, the corps
> roster (note Sacagawea and Drouillard in c23 — section 6 rides on section 4's
> merge), the Mandan winter, the Clatsop salt camp, the Shoshone horse
> negotiations. Nobody wrote this index, and deriving it cost **zero
> additional tokens** — Leiden reads the mention edges earlier sections
> already built; no LLM is in the loop. (Say "additional" precisely: on a
> natively-linked corpus like a wiki it's zero, full stop — section 2's beat.)
>
> The `cond.` column is **conductance**: the share of a community's edge weight
> that leaves it. Rule of thumb, from Zach Blumenfeld's Karpathy-wiki post
> (the further-reading slide): ≤0.35 is a tight theme you can build on, ≥0.60
> is a loose one you shouldn't. This partition: median 0.27, 35 of 47 tight,
> none loose. One stream call, and you know whether "community" means anything
> on your graph before you bet retrieval on it.

---

### 6.4 — The fix: cap the window per community (1:45)

**Slide:** the whole fix.

```python
wide = expand(question, k=50)          # section 5's walk, deeper slate
window = diversify(wide, max_per_community=2)   # ≤2 chunks per community
```

**Slide (build):** the illness window, before → after (exact counts).

| | months | communities | near-dup pairs |
|---|---|---|---|
| walk top-8 | 1 | 1 | 2 |
| **walk, capped** | **4** | **5** | **0** |

**Slide (build):** what the freed slots filled with (hand-read).

```
1806-08-12  Lewis shot through the thigh by Cruzatte     (cosine rank 21)
1806-02-22  Fort Clatsop sick-list: "…something of the influenza"  (rank 44)
1806-06-08  Bratton "no longer an invalid" — the recovery          (rank 104)
```

**Slide:** and on the two questions the walk already won:

> **The capped window is byte-identical to the uncapped one.**
> (trade-goods and food-sources already spanned 6 communities.)

> The cap applies to the *walk's own ranking* — that matters. Capping cosine is
> the textbook demo; our collapse came from the walk, so the cap has to ride
> its slate. Keep the two best Long Camp passages, then keep walking down the
> ranking, skipping any community that already gave two.
>
> What came back — judged by reading, like everything in this talk: the most
> famous injury of the whole expedition, Lewis shot by his own hunter, which
> *no* strategy's window had. The Fort Clatsop influenza sick-list section 5
> explicitly listed as a casualty of the collapse. And the closure of
> Bratton's story.
>
> And where the window was already diverse, the cap did nothing at all — it
> only bites where the failure is. That's why it's on by default: it is a
> guard rail, not a trade-off knob.

---

### 6.5 — What the cap cannot do (1:00)

**Slide:** the bound, stated mechanically.

> Community **23**: 286 chunks, 1804-05 → 1806-08 — "the corps members."
> It contains Long Camp *and* the Sept-1805 starvation sickness.
> Two slots for c23 → Long Camp takes both → **Sept-1805 stays locked out**
> (it sits at cosine rank 2 — plain vector search has it).

**Slide:**

> A cap **diversifies a ranking**. It cannot make the ranking deeper,
> and its grain is the community's, not the episode's.

> Two honest limits. First: communities are coarser than episodes. The
> passages this window still misses aren't missing because the cap failed —
> they live in the *same* community as Long Camp, and the cap's budget for
> that community went to higher-ranked chunks. Second: a cap only reorders the
> slate it is given — cap a shallow or noisy ranking and you diversify into
> noise; the vector-side cap pulled in one flatly irrelevant passage.
>
> So the routing rule from section 5 gets its final row: *questions that name
> nothing → passage-seeded expansion, capped per community* — with the cap
> understood as insurance against episode collapse, not as a relevance signal.

---

### 6.6 — Hand-off (0:30)

**Slide:** the decision table, one row longer (callback to 5.12 / forward to §9).

| resolution outcome | route |
|---|---|
| zero mentions (thematic) | passage-seeded expansion **+ community cap** |
| seeds df ≲ 15 | expand |
| seeds df ≳ 40 | filter + cosine, stop |

> The window now covers the question instead of restating one afternoon. The
> next failure is different in kind: the system can hand you eight diverse,
> relevant passages and still not tell you *how* two things are connected —
> and "how" is usually the actual question. That's path finding.

---

### Timing

| slide | time | cumulative |
|---|---|---|
| 6.1 the failure | 1:00 | 1:00 |
| 6.2 Leiden | 1:00 | 2:00 |
| 6.3 table of contents + conductance | 0:45 | 2:45 |
| 6.4 the fix, measured | 1:45 | 4:30 |
| 6.5 the bound | 1:00 | 5:30 |
| 6.6 hand-off | 0:30 | 6:00 |


---

## Section 7 — "You can't explain the answer"

*path finding: Yen's k-shortest paths, with receipts · 5 minutes · starts 0:39* · source: [`section-07-slides.md`](section-07-slides.md)

> **Editorial constraints for this section:**
>
> - **Every route and receipt on screen ran live on `lewisclark` and was
>   hand-read** (finding 7a–7g; read-pack `results/paths-lewisclark-readpack.md`,
>   local only). Route order is deterministic — the shipped tie-sort — and
>   ~220 ms per query, so the demo is safe to run live.
> - **Do not claim the k-th path is the k-th best explanation.** The 2-hop
>   routes are exact cost ties; Yen's cannot rank explanations. The honest line
>   is "k buys the set" (7a/7e), and it is on a slide because it is true, not as
>   a hedge.
> - **The entrance is inherited from §5m and bridged by 6.6** — the brother
>   question, every retriever whiffing, the walk handing back one name. Play it
>   as the second step of a two-step retrieval, not a new topic.
> - **The wrong edges get stage time.** Cameahwait-as-Hidatsa is not an
>   embarrassment to skip; a receipt refuting its own edge is the strongest
>   pro-receipt argument the corpus offers (7b).

---

### 7.1 — The failure (0:45)

**Slide:** the §6 hand-off, cashed in.

> ### "What do we know about Sacagawea's brother?"
>
> §5: every one-shot retriever missed. The walk's rank-4 passage gave us
> one thing — a name: **Cameahwait**.

**Slide (build):**

> Eight diverse, relevant passages still can't tell you **how** two things
> are connected — and "how" is usually the actual question.

> Section 5 measured this question failing every retrieval mode, and the walk
> quietly handing back the missing name. Ranking is out of moves: the answer
> isn't a pile of passages about either person, it's the *connection between
> them*. Different question shape, different tool — and now that we hold both
> names, we can ask it directly.

---

### 7.2 — Ask the graph HOW (live demo, 1:30)

**Demo:** `demo_paths.py --from Sacagawea --to Cameahwait`

**Slide (the route table, as the demo prints it):**

```
1   SACAGAWEA -[GUIDED]->          MERIWETHER LEWIS -[MET_WITH]->        CAMEAHWAIT
2   SACAGAWEA -[MEMBER_OF]->       SHOSHONE         <-[MEMBER_OF]-       CAMEAHWAIT
3   SACAGAWEA -[PARTICIPATED_IN]-> MEETING OF THOSE PEOPLE  <-[PARTICIPATED_IN]- CAMEAHWAIT
```

**Slide (build) — route 3's receipt, both hops, the same passage:**

> *"Capt. Clark arrived with the Interpreter Charbono, and the Indian woman,
> **who proved to be a sister of the Chif Cameahwait**. the meeting of those
> people was really affecting…"* — Lewis, August 17, 1805

> Yen's k-shortest paths over the extracted relationships. Route 1: they both
> knew Lewis — true and useless. Route 2: same nation — warmer. Route 3: both
> participated in one event, and both hops cite the **same journal entry** —
> the recognition scene, the one passage in 2,913 that states the sibling
> relationship. One passage is the entire explanation, and it arrived as a
> *citation*, not a similarity score. ~220 milliseconds.
>
> That's the two-step landing: the walk discovered the name, the path query
> explained the connection. Neither can do the other's job.

---

### 7.3 — Why k matters (the honest version, 1:00)

**Slide:**

> The graph has **no sibling edge**. Not for them — not for anyone.
> The extractor made an *event node* instead. The mechanism lives at k=3
> only because k=1 and k=2 route through what the graph *does* have.

**Slide (build):**

> - Edge exists → **k=1 is the answer** (Sacagawea—Shoshone: `MEMBER_OF`, and
>   its receipt is the kinship-dependence passage)
> - Edge missing → the mechanism hides **somewhere in the k-set**
> - Higher k drifts into "both acquired a shirt" — co-occurrence lives at
>   *high* k here, not low
> - The three 2-hop routes are exact cost ties: **Yen's enumerates, it cannot
>   rank explanations. k buys the set; the reader picks.**

> I'll retract our own outline from the stage: we wrote "the shortest path is
> usually trivial co-occurrence, the 2nd/3rd carry the mechanism." Hand-reading
> every hop of every route says that's backwards on a graph of *typed extracted
> relationships* — a 1-hop MEMBER_OF is a strong claim. What k really insures
> against is the extraction bound: when the edge you need was never extracted,
> the explanation survives only in structure, and you need several routes to
> find which structure. Ask for five, read five.

---

### 7.4 — Receipts catch the graph lying (1:00)

**Demo:** `demo_paths.py --from Cameahwait --to Hidatsa` — one more query, same
tool. *(The 1-hop route is in the stable cost class; safe live.)*

**Slide:**

```
1   CAMEAHWAIT -[MEMBER_OF]-> HIDATSA        1805-08-13 · d067c3d2…
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
```

**Slide (build) — that edge's own receipt:**

> *"these people **had been attacked by** the Minetares of Fort de prarie this
> spring and about 20 of them killed and taken prisoners"* — Lewis, Aug 13, 1805
>
> The edge says Cameahwait is Hidatsa. Its own citation says the Hidatsa
> attacked his people.

> Every relationship stores the chunk it was extracted from, so every hop is
> auditable — and audited, this graph confesses: an edge filing Cameahwait
> under the nation that raided his camp, a GUIDED edge naming the wrong
> captain. The receipt is what catches all of it. And the model you hand the
> context to reads the *passage*, not the edge label — so a wrong edge with a
> right receipt is survivable. A wrong edge without one is just a confident
> lie. If you keep one thing from this section: paths give you explanations
> you can check, and checking them is not optional.

---

### 7.5 — Put it in the pipeline, not the toolbox (0:45)

**Slide:** the NICD callback.

> In the 510-question NICD study, the agent had a path-finding tool.
> **It never called it. Not once.**

**Slide (build):**

> Path retrieval here is deterministic: resolve two anchors → Yen's → receipts
> → context. ~220 ms. **The model doesn't get a vote.**

> Same lesson as the routing table in section 5: if an algorithm materially
> improves retrieval, wire it into the retrieval path. Ours triggers off the
> question shape — two resolved anchors and a "how" — not off a model's whim.
> Next question: all these wins are anecdotes I hand-read to you. Does any of
> it survive a benchmark? That's section 8.

---

### Timing

| slide | time | cumulative |
|---|---|---|
| 7.1 the failure | 0:45 | 0:45 |
| 7.2 live demo — ask HOW | 1:30 | 2:15 |
| 7.3 why k matters, honestly | 1:00 | 3:15 |
| 7.4 receipts catch lies | 1:00 | 4:15 |
| 7.5 NICD close → §8 | 0:45 | 5:00 |


---

## Section 8 — "Does this actually help?"

*the benchmark: answer-entity recall over 14 questions · 4 minutes · starts 0:44* · source: [`section-08-slides.md`](section-08-slides.md)

> **Editorial constraints for this section:**
>
> - **Audience calibration (Nathan, 2026-09-07): developers who want practical
>   guidelines and how-to — not statisticians.** Slides carry things they can
>   *do*; measurement methodology lives in speaker notes and Q&A. No
>   macro/micro, variance, or confidence vocabulary on screen. Every slide
>   should answer "what would I do with this on Monday."
> - **Every number ran on `lewisclark`, four full runs compared** (finding
>   8a–8g; read-pack `results/section-08-readpack.md`, local only).
>   `vector`/`ppr`/`expand`/`cooccurrence` are identical across runs — quote
>   them exactly. `community`/`hybrid` (Louvain redraw) and `paths` (Yen's tie
>   order, n=3) move by one entity between runs — the table shows them as
>   ranges and the notes say why in one plain sentence.
> - **Recall means "the context contains the facts." It never means the answer
>   is right** — the hand-read showed even a legitimate credit can be the
>   right entity in the wrong episode (8d). Do not let a slide imply more.
> - **The boring result IS the result.** The section's job is to earn trust by
>   reporting +1 gold entity as +1 gold entity, right before §9 tells them
>   when that one entity is the one they need.
> - **The gold-set repair story (8a–8b) is Q&A backup, not stage time** — one
>   line at most ("the benchmark's own gold set had the section-4 disease;
>   fixing it was half the work"). If asked: decoy nodes, prominence prior,
>   the great-falls-of-the-Columbia false credit.
> - **The close hands §9 the Ghoshal split** — slide 9.1's router is the
>   answer to the question this section ends on. Do not resolve it here.

---

### 8.1 — Measure it yourself, in an afternoon (0:45)

**Slide:**

> ### How do you know if any of this helped *your* corpus?
>
> One metric you can build in an afternoon — no LLM judge, no eval bill:
>
> **Did the retrieved context contain the entities a correct answer needs?**
>
> - string + edge matching against your own graph — deterministic, free
> - aliases come along for free: "Janey" counts for Sacagawea,
>   "quawmash" counts for camas
> - the harness is in the repo — point `benchmark.py` at your graph

**Slide (build):**

> **And write control questions** — ones plain vector search *should* win.
> A strategy that wins hard questions by losing easy ones is not an
> improvement.

> This is the part I most want you to steal. You don't need an eval framework
> or a judge model to know whether graph retrieval is earning its keep — your
> graph already knows every entity's aliases, so "are the answer's entities in
> the window" is a lookup. Fourteen questions, five kinds, and two of them are
> controls. One confession, because it's the same lesson as section 4: my
> benchmark's own gold set pointed at decoy nodes — "a node named ELK exists"
> is not "the elk" — and fixing that was half the work of this section. Verify
> your gold labels against the graph before you trust a number; that script's
> in the repo too.

---

### 8.2 — The table (1:15)

**Slide (the benchmark table, as `benchmark.py` prints it):**

| strategy | recall | Δ vs vector | p50 | p95 |
|---|---|---|---|---|
| **vector** | **86.3%** | — | 5 ms | 5 ms |
| ppr (rerank) | 86.3% | +0.0 | 88 ms | 103 ms |
| **expand (§5)** | **88.1%** | **+1.8** | 198 ms | 218 ms |
| community (§6) | 86–88% | ±0–1.8 | 7 ms | 8 ms |
| cooccurrence (§4) | 82.1% | −4.2 | 16 ms | 17 ms |
| paths (§7) | n=3 only | — | 23 ms | 23 ms |
| hybrid | 86–88% | ±0–1.8 | 89 ms | 95 ms |

**Slide (build):**

> ✓ **Controls: every strategy scored 100%, every run.**
> Nothing paid for the hard questions with the easy ones.

> Read it top to bottom. Plain vector, on a graph where section 4 already did
> its job, gets 86%. The best graph strategy adds 1.8 points — in raw counts,
> **one more answer entity in the window**. The controls are the row I care
> most about: vector should win them, and everything held. Three practical
> footnotes, all things you'd hit in production: community and hybrid show a
> range because Louvain deals a fresh partition every run — pin your seeds if
> you need repeatable output, section 6 showed how. Paths only ran on three
> questions, because path retrieval isn't a general retriever — it fires when
> the question names two things, which is exactly how section 7 said to wire
> it. And the whole right-hand side of this table is milliseconds: the graph
> is not your latency problem.

---

### 8.3 — "Maybe you don't need this." (1:00)

**Slide:**

> ### Maybe you don't need this.
>
> - one net answer entity, for ~200 ms of graph work
> - this corpus is **~942k tokens** — it fits in one context window.
>   **If your corpus fits, stuff it in and skip retrieval.**
> - the whole-corpus baseline beat every retrieval setup in Ghoshal's
>   experiment; the NICD zero-shot numbers rhyme

> Nobody selling you a graph database will say this from a stage, so I will:
> on this corpus, at this window size, with the entities resolved, the boring
> baseline is very good — and this corpus literally fits in a context window,
> so the strongest baseline isn't even retrieval. Retrieval architecture is a
> response to a corpus that doesn't fit. And when the benchmark fails, it
> fails for **every** strategy the same way: the expedition's only death sits
> at cosine rank 64 for the illness question, and no walk, no community, no
> path pulls it into the window. The right chunk never came back — no
> reranker fixes that. That's a chunking-and-embeddings problem, and you fix
> it there.

---

### 8.4 — The three signals that say you do (1:00)

**Slide (the Ghoshal split):**

> **Graph algorithms fix *reasoning* problems.**
> **They do very little for *coverage* problems.**
>
> If retrieval fails because the right chunk never came back — fix your
> chunking and your embeddings first.

**Slide (build) — reach for the graph when:**

> 1. the answer requires **traversal**, not lookup — *"how did she get the
>    horses?"*
> 2. the same entity is **named differently** across documents — Drewyer /
>    Drouillard / "the inidian woman"
> 3. the question is about **how things connect**, not what they say

> Look back at where the graph earned its keep tonight — every win was one of
> these three shapes. Ordway's duty orders that cosine ranked at 95:
> traversal. Drewyer and Drouillard: naming. The brother question — the name
> at rank 4, then the one passage in 2,913 that states the relationship:
> connection. And our two benchmark failures, trade goods and illness, are
> neither — they're coverage, and the graph rightly did nothing for them. So
> the practical question isn't "is graph RAG better." It's "which of these
> shapes is my question" — and it turns out your pipeline can answer that
> automatically, with one COUNT query, before spending anything. That's
> section 9.

---

### Timing

| slide | time | cumulative |
|---|---|---|
| 8.1 measure it yourself | 0:45 | 0:45 |
| 8.2 the table + controls | 1:15 | 2:00 |
| 8.3 maybe you don't need this | 1:00 | 3:00 |
| 8.4 the three signals → §9 | 1:00 | 4:00 |


---

## Section 9 — How to implement this

*the router, the tools, and what not to tune · 3 minutes · starts 0:48* · source: [`section-09-slides.md`](section-09-slides.md)

> **Editorial constraints for this section:**
> - **Deliberately brief and vendor-plural.** The honest axis is not "who has
>   a better PageRank" — it's *where does your graph live, and how often does
>   it change.*
> - **NetworkX is named, never benchmarked.** Nathan doesn't use it enough to
>   represent it fairly; saying that out loud is the credibility move.
> - **9.1 is the canonical home of the bridge-decay curve** (finding 5n),
>   moved here from the parked draft at the bottom of `section-05-slides.md`.
>   The numbers are the measured 38k-pair sweep; §5.14's decision table is the
>   qualitative version and this is its receipt.
> - **The routing rule coexists with §10's take-home #2**, deliberately: the
>   router is retrieval-path code, not a model-side tool choice. 9.1's notes
>   say so in one line so nobody hears a contradiction.
> - ⚠️ **9.3's Leiden-resolution line ("a corpus decision, not a tunable") is
>   from the 2026-09-07 session and needs its backing example confirmed with
>   Nathan before the scaffold.** Drafted number-free; it rides on §5/§6's
>   already-measured lesson that operating points don't transfer.

---

### 9.1 — When to reach for the graph: one number decides (1:15)

**Slide:** the measured curve behind 5.14's routing table. 38,098
anchor–satellite pairs; median walk-rank of the satellite's unshared passages,
by anchor degree.

| seed's passage count | median rank of the neighbor's passages | reaches top-50 |
|---|---|---|
| 2–5 | **39** | 59% of pairs |
| 6–15 | 112 | 23% |
| 16–40 | 223 | 5% |
| 41–100 | 388 | 0% |
| 300+ | 1,058 | 0% |

**Slide (build):** the router is one query.

```cypher
MATCH (e {canonicalName: $seed})-[:MENTIONED_IN]->(c)
RETURN count(c)   // ≲15 → walk · ≳40 → filter + cosine · 0 → passage-expand
```

> Section 5 ended with a decision table; here is the curve underneath it.
> Monotonic, no exceptions, and the two cases you watched sit right on it —
> the Walla Walla chief, anchor in 3 passages, came back at rank 16; the walk
> from Sacagawea's 85 passages put her brother's at 338.
>
> The mechanism is the bridge fraction — how much of the seed's edge mass
> points toward the answer — but you can't observe that before retrieving.
> **Degree you can.** It's one COUNT query, it runs before you spend anything,
> and it routes the question: sparse seed → walk; hub seed → filter on the tag
> and stop; no seed at all → expand from cosine's top passages, capped per
> community (section 6).
>
> Note what this router is: retrieval-path code. It is not the agent choosing
> a graph tool — section 2 showed how that ends. The *pipeline* counts, the
> pipeline routes, the model never gets a vote.
>
> The thresholds are this corpus's. The **shape** is what transfers — measure
> your own; the harness is in the repo (`measure_bridge_decay.py`, no
> relevance judgements required).

---

### 9.2 — Where to run it (1:00)

**Slide:** vendor-plural, one axis.

> The question isn't *whose PageRank* —
> it's **where does your graph live, and how often does it change?**

> | | |
> |---|---|
> | **Neo4j GDS** | what tonight ran on — the algorithms live where the data lives |
> | **NetworkX** | the standard Python entry point; in-memory, single-machine |
> | **others** | igraph, cuGraph, Spark GraphX — and most graph databases ship an algorithm library |

> Everything you watched tonight ran on Neo4j GDS, because that's where this
> graph lives and I wasn't moving 22,000 mention edges into pandas between
> demos. If your corpus fits in memory and rebuilds nightly, NetworkX is a
> `pip install` and every algorithm in this talk is in it. I don't use it
> enough to demo it fairly, so I won't — but that's a statement about me, not
> about it.
>
> The point to land: **these are algorithms, not products.** PageRank is
> PageRank; Leiden is Leiden; the papers are public and the implementations
> are everywhere. If your corpus is small enough to fit in memory you may not
> need a graph database at all — and knowing that is exactly what makes the
> case for one honest when you do.

---

### 9.3 — What to tune, and what to decide (0:45)

**Slide:** the rule.

> ### Operating points don't transfer.
> ### Some knobs aren't knobs: **resolution (γ) is a corpus decision, not a tunable.**

> Twice in building this talk, a setting measured as *best* on one machine was
> ported to another and did damage — candidate-generation thresholds that were
> right for read-only analysis welded identities together the moment a merge
> step ran downstream. The setting wasn't wrong; the *transfer* was.
>
> And some parameters shouldn't be swept at all. Leiden's resolution — gamma,
> the knob that decides how big a "community" is — looks like a hyperparameter
> and isn't one: it encodes what a *theme* means at your corpus's granularity.
> Sweep it against a retrieval metric and the metric can't see what you traded
> away; look at the partition it produces — do these clusters match what an
> episode, a service, a ticket *is* in your domain? — and decide it once.
> Then hold it still, because the discipline that kept this talk honest is
> **re-run and diff**: seed the randomness, rerun the pipeline, and treat any
> change you didn't make as a bug.
>
> Which is most of take-home #3, so let's do those.

---

### Timing

| slide | min |
|---|---|
| 9.1 the router + curve | 1:15 |
| 9.2 where to run it | 1:00 |
| 9.3 tune vs decide | 0:45 |
| **total** | **3:00** |

---

### Assets still needed

- [ ] The decay curve as a chart, not (only) a table — five bars or a single
      falling line, anchor-degree buckets on the x-axis; the table stays in
      the appendix/PDF
- [ ] The one-query router slide with the three routes as annotations on the
      Cypher, not a second slide
- [ ] Tool table styled to read in five seconds — logos optional, no feature
      matrix
- [ ] 9.3's rule slide — two lines, large; γ typeset as the Greek letter with
      "resolution" beside it
- [ ] Confirm with Nathan the backing example for the γ line (which sweep or
      partition-read it came from) and add one receipt to the notes if it
      exists


---

## Section 10 — Three things to take home

*2 minutes · starts 0:51 · Q&A from 0:53* · source: [`section-10-slides.md`](section-10-slides.md)

> **Editorial constraints for this section:**
> - Two slides. The three take-homes get the spoken time; the further-reading
>   slide gets **zero seconds out loud** — it exists for the PDF and the
>   phones.
> - Each take-home is a callback, not new material. If a sentence here needs
>   explaining, it belongs in an earlier section instead.
> - The Lewis example in #1 is stated as a hypothetical ("a graph where…"),
>   which stays true regardless of which database the demos ran on.

---

### 10.1 — Three things (1:30)

**Slide:** all three, together, then a beat on each.

> ### 1 · Build time gates query time.
> Personalized PageRank over a graph where `CAPT. LEWIS` and
> `MERIWETHER LEWIS` are separate nodes will confidently rank the wrong
> passages. Fix entity resolution first.
>
> ### 2 · Put the algorithms in the retrieval path, not the agent's toolbox.
> The model won't reach for them. The study in section 2 gave an agent a
> path tool; it was called zero times. The router in section 9 is code.
>
> ### 3 · Measure on your own corpus.
> The harness is in the repo. Include control questions plain vector should
> win — and check that it still does.

> One each, ten seconds apiece, all callbacks:
>
> Number one is section 4 — and you watched it bite sections 5 through 7:
> every query-time algorithm inherited the merge, and the one demo that broke
> in rehearsal broke on an unresolved entity.
>
> Number two is the hinge from section 2, and it's the difference between
> "my agent has graph tools" and "my retrieval uses graph algorithms." One is
> a hope; the other is a code path.
>
> Number three is how this talk was built. Half the findings in the repo are
> measurements that *refused* to say what I wanted — the control questions
> are what kept the other half honest. Your corpus will disagree with mine
> somewhere. Find where.

---

### 10.2 — The repo, and further reading (0:30)

**Slide:** links, QR code, no talking.

> **github.com/smithna/graph-algorithms-rag** — tonight's code, the measurement
> harness, and every number in this deck with the script that produced it.
>
> - NICD, *Reducing hallucinations with GraphRAG* — the 510-question study
> - Blumenfeld (Neo4j), *Scaling Karpathy's LLM wiki* — seeded Leiden and the
>   conductance thresholds §6 used
> - Ghoshal, *When Does Graph RAG Actually Add Value?* — small experiment,
>   useful reasoning-vs-coverage framing
> - Last year: *RAG Has a Relationship Problem* —
>   github.com/smithna/corps-of-discovery-graph-rag — the pipeline that built
>   this graph
>
> **Thank you. Questions?**

> Leave the slide up through Q&A; it's the one people photograph on the way
> out. Nothing on it needs narration — the thirty seconds are "thank you,"
> the repo name said once, and open for questions at 0:53.

They gave me a SessionFeedbackQrCode.png that can go at the end of the session. Maybe could share a slide with the repo QR code.

---

### Timing

| slide | min |
|---|---|
| 10.1 three things | 1:30 |
| 10.2 repo + reading + thanks | 0:30 |
| **total** | **2:00** |

---

### Assets still needed

- [ ] QR code for the talk repo (and verify the repo URL once it's public —
      `smithna/graph-algorithms-rag` assumed here to match last year's
      account; **not yet confirmed**)
- [ ] The three take-homes styled as the closing photograph-slide pair with
      10.2 — consistent with 5.14 and 2.4's hinge, the talk's other two
      photo slides
- [ ] Q&A backup pocket list (one hidden slide of pointers): Louvain findings
      (6a/6b), filter parity (5g), the budget-graph replication (5j),
      Ghoshal caveats — so answers can land on a visual if needed

---

## Appendix A — consolidated assets checklist

Gathered from the per-section "Assets still needed" lists. **§6, §7 and §8 have
no assets list of their own** — see review note R14.

### Code gates (block a demo)

- [ ] **§0** — vector-only demo entry point: `demo_pagerank.py --vector-only`
      or a small `scripts/demo_baseline.py` that prints the top-8 with text
      previews and nothing else. *The one code gate in the talk.*

### Diagrams (inline SVG)

- [ ] **§1.1** — the corpus diagram: real labels, real relationship types.
      Establishes the visual language reused in §4–§7.
- [ ] **§2.1** — architecture: one database boundary as one box; "one
      retrieval step" is the caption that matters
- [ ] **§4.5** — OVERLAP two-circle diagram, real numbers
- [ ] **§4.8** — bridge-node chain (Sacagawea → Charbonneau → Drouillard)
- [ ] **§5.6** — "concentrate at the entity level, dissipate at the passage
      level": one hub, many arrows in, the same many arrows out, thin
- [ ] **§5.7** — bipartite 3-step diagram: entity → passages → co-mentioned
      entities → their passages
- [ ] **§9.1** — decay curve as a chart, not only a table (five bars or one
      falling line; the table stays in the appendix/PDF)

### Photograph slides (the four the room will shoot)

- [ ] **§2.4** — the hinge: "in the retrieval path, deterministically"
- [ ] **§5.2** — the forty engineers. Text only, big, no diagram.
- [ ] **§5.14** — the routing table
- [ ] **§10.1 + §10.2** — the three take-homes and the repo/reading pair

### Styled tables and text slides

- [ ] **§1.2** — join-vs-pointer table (or a two-panel sketch)
- [ ] **§1.3** — glossary with **degree** visually set apart
- [ ] **§2.3** — NICD table, vector+graph column highlighted, zero-shot column
      *not* grayed out
- [ ] **§3.1** — the roadmap table, built once and parameterized so §4–§7 can
      each re-show it with their row highlighted
- [ ] **§0.2** — the 2-of-8 slide and the 69/67 build, text only, huge
- [ ] **§2.4** — "called zero times", text only, huge
- [ ] **§4.4** — screenshot of `enrich_sacagawea.py`, `SOURCE_URL` highlighted
- [ ] **§5.1** — the tagged top-8 where the wrong-name column reads at a glance
- [ ] **§5.6** — hub table: Lewis-at-28% and elk-above-Clark land without
      explanation (`NEO4J_DATABASE=lewisclark demo_pagerank.py --hubs`)
- [ ] **§5.10** — the keelboat receipt set large; possibly a ghosted,
      struck-through `KEELBOAT` node beside the April-7 passage
- [ ] **§5.12** — the buttons passage set large, carrier line as caption; and
      cosine's trade-goods top-8 where "the same inventory, twice" reads
- [ ] **§5.13** — the three-mode whiff table; the delete test as one
      before→after arrow; the rank-4 passage with **Cameahwait** highlighted
- [ ] **§9.1** — the one-query router, three routes annotated on the Cypher
- [ ] **§9.2** — tool table that reads in five seconds, no feature matrix
- [ ] **§9.3** — the rule slide, two lines, γ typeset as the Greek letter
- [ ] **§0.3** — title slide with the sequel line and last year's repo URL
- [ ] **§10.2** — QR code for the talk repo

### Recordings and fallbacks

- [ ] **§4.6** — recording of `demo_resolution.py` (the outline recommends
      resolution be pre-recorded)
- [ ] **§5.9** — `demo_pagerank.py` recording as backup; this should be one of
      the live demos (`lewisclark`, `--seeder decomposed`, ~215 ms)
- [ ] **§0** — screenshot fallback of the live run, in case the DBMS isn't up
      at minute zero. *The only demo with no warm-up time before it.*
- [ ] **§10** — Q&A backup pocket: one hidden slide of pointers (Louvain
      findings 6a/6b, filter parity 5g, the budget-graph replication 5j,
      Ghoshal caveats)

### Projector / legibility

- [ ] **§0.1** — terminal styled for the projector: font size, and previews
      short enough that rank 1's *"for his Services as an enterpreter"* is
      legible from the back

---

## Appendix B — consolidated open decisions

Every decision the section files still flag as needing Nathan. Ordered by what
blocks the most downstream work.

| # | § | decision | blocks |
|---|---|---|---|
| 1 | 5 | **The section title.** *"Your ranking can't tell people apart."* Two earlier drafts were retracted (*"is wrong"* over-promised; *"can't combine evidence"* was written for a measured-and-retracted thesis). | §3's roadmap row, the outline's own §5 header, the deck scaffold |
| 2 | 4, 5 | **The cut plans.** §4 is +1:30 with three ranked cuts drafted; §5 is +4:00 with eleven trims drafted, several inside beats previously protected. Alternative for §5: move 5.12 to open §6 (a section-budget trade, not a cut). | the whole timing ledger; rehearsal |
| 3 | 0 | **Cold-open question choice.** Defaults to `charbonneau-role`, the same question §5.1 diagnoses — deliberate callback. Changing it means a new verified live run before anything goes on a slide. | §0 slides, §5.1's callback |
| 4 | 4 | **Which database 4.6 demos against.** Today that's `rawluna` (pre-disambiguation), so the closed cluster comes from `demo_resolution.py --adjudicate` rather than merged nodes — arguably better, the audience watches it happen. Confirm before recording. | the §4 recording |
| 5 | 5 | **How much of the retraction to tell.** 5.9 spends ~20s on "my metric measured the wrong thing, so I read the passages." The draft argues it's the most valuable 20 seconds in the section and the easiest thing to cut. | §5's cut plan |
| 6 | 5 | **The hand-read judgments in outline finding 5o** are the migrating session's and await Nathan's read. | §5.9's "3 of 11" claim |
| 7 | 9 | **9.3's γ line** — "resolution is a corpus decision, not a tunable" — needs its backing example confirmed. Drafted number-free. | §9.3 |
| 8 | 2 | **Verify NICD coarse-truthfulness values (−31 / −49)** against `nicd-reducing-hallucinations-graphrag.pdf`. Transcribed from the outline, never checked against the source. | §2.3 |
| 9 | 10 | **Repo URL** — `smithna/graph-algorithms-rag` assumed to match last year's account. Not yet confirmed, and it's on the QR code. | §10.2, the QR asset |
| 10 | 5 | **Whether finding 5f gets stage time** (the decomposed seeder's 10/11 vs 8/11 coverage). Currently a speaker note in 5.9. | §5 budget |

### Already decided — recorded so they don't get relitigated

- **§5 runs entirely on `lewisclark`** (migrated 2026-09-07, finding 5o).
  `neo4j` numbers are kept in the outline as history only.
- **§6 is Leiden only on stage** (2026-09-07). Louvain findings 6a/6b are Q&A
  backup with no slide time. *(But see review note R2 — the §6 subtitle and
  §8's speaker note haven't caught up with this.)*
- **§5.12 is the tags-vs-graph decision rule**; filter parity (5g) gets no
  stage time and is the Q&A pocket behind it.
- **The bridge-decay curve is §9.1's**, not §5's. §5's copy is marked parked
  and points here. *(See R9 — the parked copy is still in the file verbatim.)*
- **NetworkX is named, never benchmarked** — and saying so out loud is the
  credibility move, not an omission to apologize for.

---

## Appendix C — the four questions the talk runs on

The demos and measurements come back to a small set of questions. Collected
here because they recur across sections and the callbacks depend on them.

| question | first seen | comes back at |
|---|---|---|
| *"What was Toussaint Charbonneau's role on the expedition?"* | §0.1 (undiagnosed) | §5.1 (the autopsy), §5.9 (the fix) |
| *"What illnesses and injuries did the corps deal with?"* | §5's close (measured, finding 5l) | §6.1 (the failure), §6.4 (the cap), §8.3 (still fails the benchmark) |
| *"What goods did the expedition trade with Native nations?"* | §5.12 | §8.4 (listed as a benchmark failure) |
| *"What do we know about Sacagawea's brother?"* | §5.13 | §7.1–7.2 (the two-step landing), §8.4 |

The last two rows are where §8 and §5/§6 disagree — see review notes R1 and R3.

---

## Appendix D — the numbers on screen

Every figure the audience sees, with its section, so a single re-measurement
can be traced to every slide it touches. All `lewisclark` unless noted.

| number | meaning | § |
|---|---|---|
| 69 / 67 / 2-of-8 | Charbonneau passages, outside the window, in the window | 0.2, 5.1 |
| median rank 300 | where Charbonneau's passages sit under cosine | 5.1 |
| 19 nodes / 13 forms / 10 recovered / 9 missed | Sacagawea's surface forms | 4.2, 4.4, 4.6 |
| 811 people · 328,455 pairs · ~1,100 proposed | the recall/precision division of labour | 4.7 |
| 0.15→0.36, 0.13→0.33, 35→63, 41,694→45,695 | NICD: precision, recall, truthfulness, tokens | 2.3 |
| −31 / −49 | NICD coarse truthfulness ⚠️ **unverified** | 2.3 |
| zero | times the agent called the path tool, in 510 questions | 2.4, 7.5, 10.1 |
| 825 (28.3%) · 587 · 506 · 458 · 396 · 348 · 297 | the hub table | 5.6 |
| 2.84 → 0.47 / 8 · Lewis 3.2 → 18.1 | the three-choice hub ladder | 5.6 |
| 96% vs 48% | walk mass within 3 steps at d=0.45 vs d=0.85 | 5.7 |
| 14 / 14 | identical orderings at alpha=1.0 | 5.8 |
| 2 of 8 → 6 of 8 | Charbonneau window, cosine vs blended | 5.9 |
| 3 of 11 | promoted passages clearing the hand-read bar | 5.9 |
| median 9 vs 104 / 44 · 0.00633 vs 0.00672 (6%) | conjunction bonus, and the hub imbalance | 5.10 |
| 3 of 18 | the Floyd enumeration failure, every variant | 5.10 |
| 129 passages (4.4%) | chunks carrying zero entities | 5.10 |
| 67 ms · 6 ms · ~215 ms · 66 vs 494 ms | projection, cosine, blend, batched vs looped seeds | 5.11 |
| rank 77 → in-window · 112 · 3→7 months | the buttons passage and trade-goods coverage | 5.12 |
| 16 passages · 2 of 85 edges · 338 → 601 · rank 4 · cosine 1187 | the brother question | 5.13 |
| median 10 (blend) vs 43 (cosine) | Walla Walla chief, anchor df 3 | 5.13 |
| 39 / 112 / 223 / 388 / 1,058 · 38,098 pairs | the bridge-decay curve | 9.1 |
| 47 communities · 2,913 chunks · ~100 ms · one 24-node split 13/11 | Leiden | 6.2 |
| median conductance 0.27 · 35 of 47 tight · none loose | the partition ⚠️ **see R7** | 6.3 |
| 1→4 months · 1→5 communities · 2→0 near-dups | the cap, on the illness window | 6.4 |
| ranks 21 / 44 / 104 | what the freed slots filled with | 6.4 |
| ~220 ms | path query latency ⚠️ **conflicts with §8's 23 ms — see R5** | 7.2, 7.5 |
| 86.3% · +1.8 (32/38 vs 31/38) · 82.1% · 100% controls | the benchmark | 8.2 |
| ~942k tokens | the corpus, which fits in one context window | 8.3 |
| rank 64 | Floyd's death, for the illness question, every strategy | 8.3 |


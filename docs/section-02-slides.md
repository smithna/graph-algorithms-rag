# Section 2 — What is Graph RAG, and does it actually work?
### the architecture, the evidence, and the gift · 7 minutes · starts 0:06

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
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

## 2.1 — The architecture in one slide (1:00)

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

## 2.2 — Structure you can navigate (1:30)

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

## 2.3 — Does it work? The evidence (2:30)

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

## 2.4 — The gift (1:30)

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

## 2.5 — Hand-off (0:30)

**Slide:** none — the roadmap is next.

> So: the graph gives retrieval verbs it doesn't have, the best available
> evidence says the combination roughly doubles factual quality on multi-source
> questions, and the model won't drive the graph by itself. Which leaves
> exactly one question — *what specifically do you put in the path?* Four
> failures, four algorithms.

---

## Timing

| slide | min |
|---|---|
| 2.1 architecture | 1:00 |
| 2.2 structure + zero-additional-tokens | 1:30 |
| 2.3 evidence + awkward parts | 2:30 |
| 2.4 the gift + the hinge | 1:30 |
| 2.5 hand-off | 0:30 |
| **total** | **7:00** |

---

## Assets still needed

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

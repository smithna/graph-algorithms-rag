# Section 8 — "Does this actually help?"
### the benchmark: answer-entity recall over 14 questions · 4 minutes · starts 0:44

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
> **Editorial constraints for this section:**
>
> - **Every number ran on `lewisclark`, four full runs compared** (finding
>   8a–8g; read-pack `results/section-08-readpack.md`, local only).
>   `vector`/`ppr`/`expand`/`cooccurrence` are byte-stable across runs — quote
>   them exactly. `community`/`hybrid` (Louvain redraw) and `paths` (Yen's tie
>   order, n=3) move by one entity between runs — quote ranges or leave them
>   in the table without headline claims.
> - **Recall means "the context contains the facts." It never means the answer
>   is right** — and the hand-read showed even a legitimate credit can be the
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

## 8.1 — The metric, and why it's deliberately boring (0:45)

**Slide:**

> ### Answer-entity recall
>
> Did the retrieved context actually contain the entities a correct answer
> needs?
>
> - alias-aware — "Janey" counts for Sacagawea, "quawmash" for camas
> - deterministic — no LLM judge, no variance in the measurement
> - honest about its limit: it says the facts are **in the window**, not that
>   the answer is right

> Fourteen questions, five kinds — connection, authority, thematic, sequence,
> and two **controls**: questions plain vector search should win. If a graph
> strategy loses the easy questions while winning the hard ones, that's not an
> improvement, that's a trade someone should have to defend. The measurement's
> job is to be boring: every number tonight is reproducible on this laptop.
> One line of confession — the benchmark's own gold set had the section-4
> disease: half its labels pointed at decoy nodes ("a node named ELK exists"
> is not "the elk"). Fixing the gold set was half the work of this section,
> and the tooling that fixes it is the same prominence prior from section 4.

---

## 8.2 — The table (1:15)

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
> its job, gets 86%. The best graph strategy adds 1.8 points. In raw counts
> that is **one gold entity** — 32 of 38 instead of 31. The controls are the
> row I care most about: vector should win them, and it does — so should
> everyone, and everyone does. Two honest footnotes: community and hybrid
> wobble by one entity between runs because Louvain redraws its partition —
> section 6 told you that would happen. And paths only runs on three
> questions, because path retrieval isn't a general retriever — it triggers
> off question shape, which is exactly how section 7 said to deploy it.
> Latency: the graph costs milliseconds, not seconds.

---

## 8.3 — "Maybe you don't need this." (1:00)

**Slide:**

> ### Maybe you don't need this.
>
> - one net gold entity, for ~200 ms of graph work
> - this corpus is **~942k tokens** — it fits in one context window
> - Ghoshal's whole-corpus frontier baseline beat every retrieval setup he
>   tested; the NICD zero-shot column says the same thing

> I want to say this from the stage because nobody selling you a graph
> database will: on this corpus, at this window size, with the entities
> resolved, the boring baseline is very good — and this corpus *fits in a
> context window*, so the strongest baseline isn't even retrieval. Retrieval
> architecture is a response to a corpus that doesn't fit — not a virtue.
> And where the benchmark fails, it fails for **every** strategy identically:
> the expedition's only death sits at cosine rank 64 for the illness question,
> and no walk, no community, no path promotes it into the window. The right
> chunks never came back — no reranker fixes that.

---

## 8.4 — The signals that say you do (1:00)

**Slide (the Ghoshal split):**

> **Graph algorithms fix *reasoning* problems.**
> **They do very little for *coverage* problems.**
>
> If retrieval fails because the right chunk never came back — fix your
> chunking and your embeddings first.

**Slide (build):**

> You want this when:
>
> - the answer requires **traversal**, not lookup — *"how did she get the
>   horses?"*
> - the same entity is **named differently** across documents — Drewyer /
>   Drouillard / "the squaw"
> - the question is about **how things connect**, not what they say

> Look back at where the graph earned its keep tonight: Ordway's duty orders
> that cosine ranked at 95. The brother's name at rank 4 when every retriever
> whiffed. The recognition scene no ranker could surface but a two-anchor path
> query returned in 220 milliseconds. Every one of those is a *reasoning*
> shape — traversal, aliasing, connection. And our two benchmark failures —
> trade goods, illness — are *coverage* shapes: the right passages exist and
> never came back in eight. So the honest question isn't "is graph RAG
> better." It's "which problem do you have" — and it turns out you can route
> that question with one COUNT query. That's section 9.

---

## Timing

| slide | time | cumulative |
|---|---|---|
| 8.1 the metric | 0:45 | 0:45 |
| 8.2 the table + controls | 1:15 | 2:00 |
| 8.3 maybe you don't need this | 1:00 | 3:00 |
| 8.4 the Ghoshal split → §9 | 1:00 | 4:00 |

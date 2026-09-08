# Section 8 — "Does this actually help?"
### the benchmark: answer-entity recall over 14 questions · 4 minutes · starts 0:44

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
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

## 8.1 — Measure it yourself, in an afternoon (0:45)

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

## 8.3 — "Maybe you don't need this." (1:00)

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

## 8.4 — The three signals that say you do (1:00)

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
>    Drouillard / "the squaw"
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

## Timing

| slide | time | cumulative |
|---|---|---|
| 8.1 measure it yourself | 0:45 | 0:45 |
| 8.2 the table + controls | 1:15 | 2:00 |
| 8.3 maybe you don't need this | 1:00 | 3:00 |
| 8.4 the three signals → §9 | 1:00 | 4:00 |

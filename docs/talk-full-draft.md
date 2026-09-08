# Graph Algorithms for RAG — full talk draft

**Nathan Smith · KCDC 2026 · 53 minutes of content + ~7 for Q&A**

> **What this is.** All eleven section files compiled into one document, with
> **Nathan's draft edits applied and the nineteen cross-section review findings
> resolved** (2026-09-08). The per-section `section-NN-slides.md` files are now
> **behind this document** — this is the copy the deck gets built from.
>
> **Cross-section problems are fixed here**, not just listed. Every finding
> from [`talk-full-draft-review.md`](talk-full-draft-review.md) is closed out in
> **Appendix E**, with the measurement behind it where one was needed.
>
> **Speaker notes are blockquotes.** Text inside a blockquote that is styled as
> a heading is *on-slide typography*, not document structure.
>
> **Source of truth remains [`talk-outline.md`](talk-outline.md)** for findings
> and history; this document is the source of truth for what gets said on
> stage.

---

## Timing ledger

| § | section | budget | now | Δ | starts |
|---|---|---|---|---|---|
| 0 | Cold open: the failure | 3:00 | **3:30** | **+0:30** | 0:00 |
| 1 | What is a graph? | 3:00 | 3:00 | — | 0:03:30 |
| 2 | What is Graph RAG, and does it work? | 7:00 | **7:15** | **+0:15** | 0:06:30 |
| 3 | Roadmap | 1:00 | 1:00 | — | 0:13:45 |
| 4 | Your entities are a mess | 9:00 | **10:00** | **+1:00** | 0:14:45 |
| 5 | Your ranking can't tell people apart | 10:00 | **10:25** | **+0:25** | 0:24:45 |
| 6 | Your context is redundant | 6:00 | 6:00 | — | 0:35:10 |
| 7 | You can't explain the answer | 5:00 | 5:00 | — | 0:41:10 |
| 8 | Does this actually help? | 4:00 | 4:00 | — | 0:46:10 |
| 9 | How to implement this | 3:00 | 3:00 | — | 0:50:10 |
| 10 | Three things to take home | 2:00 | 2:00 | — | 0:53:10 |
| | **total** | **53:00** | **55:10** | **+2:10** | Q&A 0:55:10 |

**Down from +5:30.** §5's eleven cuts are **applied** (Nathan: *"I support all
these cuts"*), 4.9 is **cut**, and the §5 retraction beat is **out** (open
decision #3). What the applied cuts did not pay for is the new material Nathan
asked for, and it is only fair to say where the remaining +1:55 went:

| added | § | cost |
|---|---|---|
| bio slide + KCDC sponsor slide + table of contents | 0.3 | +0:30 |
| how personalized PageRank actually works, and damping | 5.3 | +0:45 |
| what WCC *is*, before what it's for | 4.8 | +0:15 |
| the NICD refusal numbers and zero-shot's −127 (from verifying the paper) | 2.3 | +0:15 |

The rest is §4 landing at 9:45 after 4.9 came out rather than at 8:55, because
4.3 and 4.7 stayed in (Nathan: *"Cut 4.9. Keep 4.3 and 4.7"*).

### ⚠️ Slot: last session, last day (Nathan, 2026-09-08)

**This changes what "over budget" costs.** In a mid-morning slot, running two
minutes long is untidy. In the final slot of the final day it means finishing
to a room that is already standing up, and it eats the Q&A that a tired
audience was never going to fill anyway. **Getting under 53:00 is now the
highest-value change left in the talk** — higher than any remaining polish.

It also re-ranks the cut list. The rule for a tired room is: **cut arithmetic,
protect the beats that wake people up.** Measured across the deck there are
**363 numbers on screen**, and they cluster where the fade is worst — §6
carries 126 of them and §8 another 42, i.e. minutes 35–50. Meanwhile the
things that pull a flat room back — the Jaro-Winkler bug, the elk outranking
Captain Clark, the captains cutting buttons off their coats, §8.4 admitting
two of its own wins don't survive measurement — cost seconds and were mostly
sitting near the *top* of the cut lists. That was backwards and is now fixed
in each section's list.

**Recommended cut set for a tired last slot (−2:10, lands at 53:00):**

| cut | saves | why it's the right one here |
|---|---|---|
| **§4.7's 328,455-pair table** | 0:30 | Four numbers in service of a point the two-line slide already makes. Highest density-per-second in §4 |
| **§0.3's table of contents** | 0:20 | §3.1 does the same job better, ninety seconds later |
| **§5.11's cost table** | 0:25 | Keep the spoken landing — *"~35× plain vector, and the generation call dwarfs it"* — drop the three-row table |
| **§9.3 (tune vs decide)** | 0:45 | ⚠️ **the painful one.** It's one of the most transferable lessons in the talk, and it is also pure abstraction arriving at minute 50 to a room that is done. It survives as a Q&A pocket and in the repo |
| **§6.3's projection table** | 0:10 | §5.4 already says the one-line version |

**If §9.3 stays** — defensible; it's genuinely good — the alternative 0:45 is
§2's NICD table down to two rows (−0:30) plus §6.5's second limit (−0:15). I'd
rather lose §9.3 than the NICD table now that every number in it is verified,
but that is a taste call and it is yours.

**Two further candidates**, both already argued in-place and neither applied —
rehearsal calls, not merge fixes:

1. **Move 5.12 (trade-goods) to open §6** — the illness collapse is §6's
   motivating failure and trade-goods sets it up. Saves §5 1:00, costs §6 1:00:
   a section-budget trade that nets nothing on the total but puts §5 under
   budget. Detail under §5's cut table.
2. **§4.7 down to its two-line recall/precision slide**, dropping the
   328,455-pair table (−0:30), and **§2 to its two load-bearing NICD rows**
   (−0:30). §2 is already designated the compression victim — though the NICD
   table got *more* worth showing whole once it was verified, so I would spend
   the §4.7 cut first.

**Timekeeping anchors, now two** (review R19): §3.1's speaker note is the first
(minute 13-to-14 or the cuts come out); **§6.1 is the second** — if §6 has not
started by **0:35**, §6.5 and §7.3 are the drop-ins.

---

## Structural spine

Four failures, four algorithms, two stages — the §3 roadmap, restated so the
arc is visible in one place:

| § | stage | the failure | the algorithm | live demo? |
|---|---|---|---|---|
| 0 | — | *(the cold open — the failure, undiagnosed)* | none | **screenshot** — `demo_baseline.py` (R11) |
| 4 | build | Your entities are a mess | node similarity + WCC | recording |
| 5 | query | Your ranking can't tell people apart | personalized PageRank | **yes** — `demo_pagerank.py` |
| 6 | query | Your context is redundant | Leiden | slide output |
| 7 | query | You can't explain the answer | Yen's k-shortest paths | **yes** ×2 — `demo_paths.py` |
| 8 | — | *(does any of it help — the benchmark)* | — | no |
| 9 | — | *(the router: one COUNT query)* | — | no |

Every section opens with a problem the audience has felt, then solves it — and
says when not to reach for the algorithm.

---

## Section 0 — Cold open: the failure

*screenshot, no title slide first · 3:30 · starts 0:00* · source: [`section-00-slides.md`](section-00-slides.md)

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
> - **The cold open is a screenshot, not a live run — Nathan's call (R11):**
>   *"I think demo-baseline could be a screenshot."* That takes the talk from
>   four live demos to two (5.9 and §7's single terminal session), which is what
>   §4's and §5's asset notes always said the budget was. It also retires the
>   riskiest demo in the deck — the one that ran at minute zero with no warm-up.
>   The code gate below still applies: the screenshot has to be *of* a
>   vector-only run, or it spoils section 5.
> - ⚠️ **One small code gate remains:** the screenshot needs a vector-only view.
>   `demo_pagerank.py` prints the comparison, which spoils section 5. Either a
>   `--vector-only` flag or a five-line `scripts/demo_baseline.py`. Listed
>   under Assets.
> - **Hello happens at 0.3, not here.** The bio and sponsor slides Nathan asked
>   for go *after* the title slide, because this section's whole design is that
>   there is no greeting before the failure lands. See 0.3.

---

### 0.1 — The question (1:15) · **screenshot**

**Screen:** a terminal, not a slide — a **screenshot** of the run (R11), sized
so the top-8 reads from the back.

> ### "What was Toussaint Charbonneau's role on the expedition?"

```
NEO4J_DATABASE=lewisclark python scripts/demo_baseline.py \
    "What was Toussaint Charbonneau's role on the expedition?"
```

**The top-8 comes back. It looks great.**

> No hello, no title slide. Put the question up and read the results with them
> for a moment — the screenshot is doing the work a live run used to, and it
> reads identically from row 20.
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

### 0.3 — The line, the title, and hello (1:15)

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
> when it doesn't.
>
> You might recognise this Lewis & Clark dataset if you came to my talk at
> Community Days. That session put GraphRAG side by side with vanilla vector
> retrieval and showed what the graph adds. **Today is the next question: what
> the graph *algorithms* add on top of it.** Same corpus, a year further in.
>
> And we come back to this exact question, with a fix, in section 5.
>
> *(House-keeping in one breath: repo link is on the last slide, questions at
> the end.)*

#### 0.3b — hello, sponsors, and the map (0:30)

**Slide:** the bio, as a graph. Ported from last year's deck (slide 2 of
`rag_relationship_problem.pptx`) — the joke is that the bio *is* a graph, which
also pre-loads section 1's vocabulary for free.

```
                     ┌──────────────── AT_COMPANY ────────────────┐
   (Person: Nathan Smith)                                          ▼
        │  WORKS_AT ──▶ (Position · 6 years) ────────────────▶ (Neo4j)
        │                     │ PREVIOUS_JOB
        │                     ▼
        │               (Position · 1 year)  ─── AT_COMPANY ──▶ (Lovevery)
        │                     │ PREVIOUS_JOB
        │                     ▼
        │               (Position · 5 years) ─── AT_COMPANY ──▶ (PRA Health Sciences)
        │
        ├─ PLAYS  {level: advanced} ────────▶ (Piano)
        ├─ PLAYS  {level: intermediate} ────▶ (Organ)
        ├─ SPEAKS {level: débutant} ────────▶ (French)
        ├─ SPEAKS {level: nybörjare} ──────▶ (Swedish)
        └─ ORGANIZES ──────────────────────▶ (Data Science KC)
```

> Ten seconds, and don't read it out — the room reads a graph faster than you
> can narrate one. The only line worth saying: *"that's my bio, and it's also
> the last slide tonight where I get to draw the graph by hand."*
>
> ⚠️ **Two things to fix when porting it** (see Assets): the Neo4j tenure was
> "5 years" on last year's slide and needs to read **6**; and the original has
> a typo — one edge is `PREIVIOUS_JOB`.

**Slide:** the KCDC sponsors. Supplied by the organisers:
[`KCDC_2026_Sponsors_Slide.jpg`](KCDC_2026_Sponsors_Slide.jpg).

> Full-bleed, five seconds, one sentence — *"KCDC runs on these folks, thank
> you"* — and move. It goes here because it is the only place in the talk where
> a house-keeping slide doesn't interrupt an argument.

**Slide:** where we're going. The table of contents Nathan asked for.

> | | | |
> |---|---|---|
> | **0** the failure | **4** entities are a mess | **8** does it help? |
> | **1** what's a graph | **5** ranking can't tell people apart | **9** how to implement |
> | **2** what's Graph RAG | **6** context is redundant | **10** take-homes |
> | **3** the roadmap | **7** can't explain the answer | |

> Fifteen seconds. Put a hand on the middle column — sections 4 through 7 —
> *"those four are the talk; the rest is scaffolding"* — and go.
>
> This is deliberately **not** section 3's roadmap. This one is "here are
> eleven signposts, here's how long you're in the room." Section 3 is the
> argument: four failures, four algorithms, two stages. If rehearsal wants the
> 0:20 back, this is the slide to drop — §3 does the load-bearing version.

---

### Timing

| slide | min |
|---|---|
| 0.1 the question (screenshot) | 1:15 |
| 0.2 the reveal | 1:00 |
| 0.3 the line + title | 0:45 |
| 0.3b bio + sponsors + contents | 0:30 |
| **total** | **3:30** |

---

### Assets still needed

- [ ] **Vector-only demo entry point** — `demo_pagerank.py --vector-only` or a
      tiny `scripts/demo_baseline.py` that prints the top-8 with text
      previews and nothing else. The one code gate on this section. *(Still
      needed even though 0.1 is now a screenshot — the screenshot has to be of
      a vector-only run or it spoils §5.)*
- [ ] **The 0.1 screenshot itself** (R11): captured from a real
      `NEO4J_DATABASE=lewisclark` run, terminal styled for the projector, and
      the top-8 previews short enough that rank 1's *"for his Services as an
      enterpreter"* is legible from the back
- [ ] The 2-of-8 slide and the 69/67 build — text only, huge
- [ ] Title slide with the sequel line and last year's repo URL
- [ ] **Bio-as-graph slide**, ported from `rag_relationship_problem.pptx`
      slide 2 — Nathan re-draws in arrows.app and exports SVG. **Update Neo4j
      tenure 5 → 6 years; fix the `PREIVIOUS_JOB` typo.**
- [ ] **Sponsor slide** — `KCDC_2026_Sponsors_Slide.jpg`, full-bleed, as
      supplied
- [ ] **Table-of-contents slide** — eleven signposts, three columns; the four
      algorithm sections visually weighted


---

## Section 1 — What is a graph?

*deliberately fast · 3 minutes · starts 0:03:30* · source: [`section-01-slides.md`](section-01-slides.md)

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
>
> One honest footnote, because the mental picture misleads people later: for
> several of these, **nobody is actually walking**. A graph is an adjacency
> matrix, and "spread mass to my neighbours, repeatedly" is a
> **matrix-vector multiply, iterated to convergence** — decades of linear
> algebra optimisation apply. We are *not* simulating random walks when we
> compute PageRank; the walk is the proof, not the implementation. Say it
> once, here, and section 5's mass-distribution picture stays a picture
> instead of becoming a performance claim.

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

- [ ] The 1.1 diagram — **Nathan draws it in arrows.app and exports SVG**
      (his call: *"No need for you to write the SVG code"*). Real labels, real
      relationship types, readable node captions; this export sets the visual
      language reused in sections 4–7 so the graph "looks the same" all hour.
      **Export checklist, learned from the §4.5 export:** set a `viewBox` (the
      arrows.app export ships bare `width`/`height`, so it will not scale in
      reveal.js), widen nodes until captions stop wrapping mid-word, and check
      the grey edge labels (`#959aa1`) against the dark deck background
- [ ] The join-vs-pointer table styled as a slide (or a two-panel sketch:
      key-matching arrows vs a single fat edge)
- [ ] Glossary slide with **degree** visually set apart from the other three


---

## Section 2 — What is Graph RAG, and does it actually work?

*the architecture, the evidence, and the gift · 7:15 (budget 7:00) · starts 0:06:30* · source: [`section-02-slides.md`](section-02-slides.md)

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
> - **✅ Every NICD number verified against the paper, 2026-09-08** (open
>   decision #8, closed). Source PDF now **in the repo** at
>   [`nicd-reducing-hallucinations-graphrag.pdf`](nicd-reducing-hallucinations-graphrag.pdf)
>   — *Wedge, Stutter, Dixon & Cała, National Innovation Centre for Data,
>   Newcastle University*, long version, 25pp. Table 2 confirms all of it
>   exactly: precision
>   0.15/0.36/0.43, recall 0.13/0.33/0.39, coarse truthfulness **−31/−49**/−127,
>   fine-grained **35/63**/40.5, total tokens **41,694/45,695/1,108**. Also
>   confirmed: 510 questions, **28,240** source articles (the "28,000" on the
>   slide is a fair round), and the conflict-of-interest statement naming Neo4j
>   as the funder. Nothing needed correcting.
> - **Licence note, because the repo URL goes on a slide.** The paper is
>   **CC BY-NC-SA 4.0**, copyright held by the authors. Verbatim
>   redistribution is *permitted* under that licence with attribution, and
>   ShareAlike attaches to **adaptations**, not to bundling the unmodified PDF
>   — so shipping it in the repo does not put any obligation on the repo's own
>   licence. Two things it does require: **name the authors and the licence**
>   next to the file (a line in the README or a sibling
>   `nicd-paper-LICENSE.txt`), and keep the repo non-commercial in character,
>   which a conference-talk repo is. The paper's own note — *"for any use
>   beyond those covered by this license, obtain permission by emailing the
>   authors"* — is worth knowing about but does not apply here.
> - **The authors' code is public too:** `github.com/NICD-UK/graph-based-rag-qa`
>   — added to the further-reading slide, since §8.1's whole pitch is "steal
>   this harness" and theirs is the one behind these numbers.
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
| Coarse truthfulness | −31 | −49 | **−127** |
| Total tokens (median) | 41,694 | 45,695 | 1,108 |

*(Verified against Table 2 of the paper, 2026-09-08. The coarse-truthfulness
row is **new to this slide** — it was in the speaker notes as a caveat, and it
belongs on screen, because it is the row where zero-shot's apparent win
collapses. See the note below.)*

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
>   *refuses to answer* far more often. Refusing isn't winning.
> - **The study was funded by Neo4j.** Disclosed in the paper. Now disclosed
>   here.

> Say all three before anyone asks. The zero-shot column is why "just use a
> bigger model" works on Wikipedia and not on your incident reports — your
> corpus isn't in the training set; that column vanishes on private data, and
> the other two don't.
>
> The refusal point cuts the other way, and the paper hands you the numbers to
> say it hard: **the coarse metric gives 0 for a refusal and −1 for a
> hallucination, so a system that answers almost nothing can't lose much.**
> Vector RAG answered about **27%** of the 510 questions. Vector+graph answered
> **65%** — the authors' own summary line is that the graph *"more than halved
> the proportion of complex questions that the agent refused to answer."* So
> vector RAG's better-looking −31 is bought with silence. It's the same failure
> the cold open showed: hand the model less of the right context and it balks,
> and a coarse metric scores the balk as honesty.
>
> And the row that ends the argument is the one I've now put on screen:
> **zero-shot's coarse truthfulness is −127.** It answers nearly everything and
> hallucinates in 59% of cases. So the honest reading of this table is not
> "zero-shot wins" — it's *"zero-shot is confident, vector RAG is quiet, and
> the graph is the only one of the three doing both jobs at once."*
>
> *(**Q&A pocket, not stage time** — if pressed on whether the −31/−49 gap is
> real: the confidence intervals don't overlap, [−31, −18] against [−61, −44].)*
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
> never touched the path tool — it fell back to vector search, every time.
>
> **And that last clause is the authors', not mine** — verified in the paper,
> 2026-09-08. Their explanation: graph tools for complex QA are *"likely
> under-represented in LLM training,"* and *"LLMs are conservative in their
> tool selection, and are biased towards tools that align with their
> training."* So this isn't a quirk of one agent; it's a prediction about
> yours.
>
> *(**Q&A pocket** — two more tools went unused, backlinks and a calculator.
> The shortest-path one is worth naming from the stage because it's the one
> this talk spends five minutes on in section 7.)*
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
| 2.3 evidence + awkward parts | **2:45** |
| 2.4 the gift + the hinge | 1:30 |
| 2.5 hand-off | 0:30 |
| **total** | **7:15** |

⚠️ **+0:15**, and it is the NICD verification's fault: 2.3 gained the refusal
numbers (27% vs 65% of questions answered) and zero-shot's −127. The
coarse-truthfulness table row itself is free — it is on-slide — and the
confidence-interval and unused-tools asides are marked as Q&A pockets rather
than stage time.

**This section is the designated compression victim and the cut is already
drafted** — NICD table down to precision and truthfulness only, −0:30, which
more than covers it. I have not applied it, because the table is now *more*
worth showing whole than it was: the four-row version is what makes the
"zero-shot is confident, vector RAG is quiet, the graph does both jobs"
reading possible.

---

### Assets still needed

- [ ] Architecture diagram as inline SVG — one database boundary drawn as one
      box; the "one retrieval step" caption is the point
- [ ] NICD table styled with the vector+graph column highlighted and the
      zero-shot column *not* grayed out (we argue against hiding it)
- [ ] "Called zero times" slide — text only, huge
- [ ] The hinge slide — this is the most-photographed slide in the talk after
      5.14's routing table; set it like one
- [x] **Verified 2026-09-08** — all NICD numbers checked against the paper;
      every one exact
- [x] **PDF in the repo** — `docs/nicd-reducing-hallucinations-graphrag.pdf`
- [ ] **Attribution line for the NICD PDF** (CC BY-NC-SA 4.0): authors,
      title, institution and licence URL in the README or a sibling
      `nicd-paper-LICENSE.txt`. Redistribution is permitted; naming the
      authors and the licence is the condition
- [ ] **§2.3** — restyle the NICD table with the new coarse-truthfulness row;
      zero-shot's **−127** is the number that has to land


---

## Section 3 — Roadmap

*four failures, four algorithms, two stages · 1 minute · starts 0:13:45* · source: [`section-03-slides.md`](section-03-slides.md)

> **Editorial constraints for this section:**
> - One slide, one minute. The reframe gets said out loud; the table is left
>   on screen while it's said.
> - **Section titles here must track the section files** — §5's row reads
>   *"can't tell people apart"*, ✅ **signed off 2026-09-08**. The outline's §5
>   header now matches it too (review finding R15).
> - §6's row says **Leiden**, and that is now the only word for it anywhere —
>   slides, speaker notes and code (2026-09-08, review finding R2).

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
> *(Timekeeping anchor #1 of 2: this slide is minute 13-to-14. Section 4 starts
> on schedule or the cuts list comes out. **Anchor #2 is §6.1 at 0:35** — §4
> and §5 are the two sections that have ever run long, and they are both behind
> you by then. Review finding R19.)*

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

*node similarity + WCC · 10:00 (budget 9:00) · starts 0:14:45* · source: [`section-04-slides.md`](section-04-slides.md)

> **Editorial constraints agreed for this section:**
> - **No precision or recall percentages.** The gold set is a hand-built
>   reference, not ground truth. Claims on screen are things the audience can
>   check by eye: named nodes, a drawn chain, counts from a live run.
> - **The Sacagawea example is the spine.** Everything else hangs off it.
> - **No metric comparison table.** One diagram for OVERLAP, one throwaway line
>   about other corpora.

---

### 4.1 — The failure (0:45)

**Slide:** the same man, five ways.

```
CLARK · CAPT. CLARK · WILLIAM CLARK · Capt Clark · Wm. Clark
```

**Every one of those is a separate node.**

> Where these came from, in one sentence, because it changes who thinks this
> slide is about them: **an LLM extracted these entities out of unstructured
> journal text**, one chunk at a time, and it faithfully reported the name each
> passage actually used. Nothing malfunctioned. Five spellings in the source
> become five nodes in the graph.
>
> And if you are sitting there thinking *my data is structured, this isn't my
> problem* — you have these too. Every CRM has `ACME Corp`, `Acme
> Corporation`, and `acme-corp-1`. Extraction makes the duplicates *plentiful*;
> it does not make them exotic.
>
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
>
> **Handle the language once, here, plainly, and then never again:** *"'Squaw'
> was ordinary usage in the captains' 1805 English. It is offensive now. These
> are the journals' words, not mine, and they are on the slide because they are
> the data the pipeline has to cope with."* One sentence, no apology tour — and
> because it lands here, on first appearance, 4.3's slide doesn't have to stop
> for it.

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

> # SACAGAWEA → THE INDIAN WOMAN
> ### no string algorithm will ever connect these

> There is nothing to connect. Not a shared prefix, not a shared token, not a
> shared phoneme. The letters have run out. And this is not an edge case — it is
> *most* of the nineteen.

**The Jaro-Winkler aside — 5 seconds, and keep it.** *(Marked "optional" in
the first draft and ranked #2 for cutting; both were wrong once the slot was
known. This is minute 18 of the final session of the conference and this is
the talk's only real shipped-bug laugh. It earns its twenty seconds precisely
when the room is flat.)*

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

**Slide — the signal, drawn.** Nathan's arrows.app export:
[`sacagawea appears with indian woman.svg`](sacagawea%20appears%20with%20indian%20woman.svg).

```
   (SACAGAWEA) ──MENTIONED_IN──▶ ┌─ 1805-04-07 ─┐ ◀──MENTIONED_IN── (INDIAN WOMAN)
                                 │  1805-08-14  │
                                 │  1805-08-17  │
                                 │  1805-08-19  │
                                 │  1805-08-22  │
                                 │  1805-08-25  │
                                 │  1806-01-06  │
                                 └─ 1806-04-22 ─┘
                                    ▲        ▲
                       MENTIONED_IN │        │ MENTIONED_IN
                        (CAMEAHWAIT)         (TOUSSAINT CHARBONNEAU)
```

**Two names. The same passages. The same brother, the same husband.**

> This is the slide the section turns on, and it needs no numbers. Two nodes
> the string ladder cannot touch, standing in the same eight journal entries,
> beside the same two people. *That* is the signal — and a human reader would
> have called it in a second.

**Slide:** where the signal already is.

- entity ↔ entity co-occurrence, weighted by shared chunk count
- a **filtered node-similarity** call, restricted to same-label pairs
- union it with the string and alias signals
- **costs zero LLM tokens** — it is reading structure that extraction already built

> *(Speaker note — the diagram's provenance, if anyone asks: it is the
> **unresolved** graph, which is the only place both nodes still exist. The
> query behind it is*
>
> ```
> MATCH t1 = (:Person {canonicalName:"SACAGAWEA"})-[:MENTIONED_IN]->()
>              <-[:MENTIONED_IN]-(n:Person)
> MATCH t2 = (:Person {canonicalName:"INDIAN WOMAN"})-[:MENTIONED_IN]->()
>              <-[:MENTIONED_IN]-(n)
> WHERE n.canonicalName IN ['CAMEAHWAIT', 'TOUSSAINT CHARBONNEAU']
> RETURN t1, t2
> ```
>
> *— run on `rawluna`/`budgetluna`. On the merged graph it returns nothing,
> because there is no `INDIAN WOMAN` any more. The algorithm's own success is
> what deletes its evidence, which is worth five seconds if the question comes.
> Keep the query off the slide — see §6.2 on vendor-neutral syntax.)*

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

### 4.6 — The payoff (1:30) · **recording** (`rawluna`)

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

**Slide — and now the number, because this is what it bought.** Same corpus,
same extraction, before and after the merge:

> | | passages you get for "Sacagawea" |
> |---|---|
> | unresolved — the node *named* `SACAGAWEA` | **8** |
> | her other 13 names, standing separately | 40 more, spread over 13 nodes |
> | **after resolution — one node** | **47** |

> **Eight to forty-seven.** That is the section, quantified, and it is the
> number I did not put on a slide until now.
>
> One detail worth five seconds because it is the mechanism in miniature: those
> 48 passages **do not overlap at all**. Every journal entry names her exactly
> one way. So this is not a merge that consolidated redundant coverage — the
> duplicates were each other's *only* coverage.
>
> *(And to be exact about a number that shows up again in section 5: she has
> **85** passages on the live graph. 47 came from the journals, which is what
> resolution earned. The other 38 came from the scraped reference page on the
> next slide. Resolution gets credit for 8→47, not 8→85 — and I would rather
> hand you the smaller honest number than the bigger one.)*

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

### 4.8 — WCC, and what it is actually for (1:45)

**Slide:** what it is, before what it's for.

> ## Weakly Connected Components
> ### Follow the edges, ignoring direction. Everything you can reach is one component.
> ### That's the entire algorithm.

**Slide (build):** the problem it solves.

```
   SACAGAWEA ≈ THE SQUAR          three separate pairwise judgements
   THE SQUAR ≈ INDIAN WOMAN       nothing has seen all three
   INDIAN WOMAN ≈ JANEY
                                  ── WCC ──▶  one entity, four names
```

> Say what it *is* first, because "component" sounds like jargon and isn't:
> start anywhere, follow every edge you can, ignore which way the arrows point,
> and stop when you can't reach anything new. That set is a component. One
> pass, linear in the edges, no parameters — there is nothing to tune and
> nothing to seed.
>
> And the problem it solves is the one I actually have: **my matcher only ever
> produces pairs.** It said Sacagawea ≈ the squar, and separately the squar ≈
> Indian woman. Nothing in the pipeline ever looked at an *identity*. WCC is
> the step that turns a bag of pairs into "these ten names are one person" —
> transitive closure, computed for free.

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
>
> *(Section 6 comes back to this contrast with a receipt: on the retrieval
> graph, WCC returns **one** component containing all 8,139 nodes. Leiden
> returns **47** communities inside it. Same family, different question.)*

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

### 4.9 — Take home (0:30)

*(Numbered 4.9 now. The old 4.9 — "same algorithm, query time" — is **cut**,
per Nathan: "Take 4.9 out. I would just run a cypher query for this, not use a
GDS algorithm. The GDS algorithm shows global common neighbors, which is what
we want at build time." He is right on both counts, and cutting it also
retires review finding R13: the beat promised that node similarity at query
time "catches passages embeddings miss", and §8 measures that same strategy at
**82.1%, −4.2** — the only strategy in the benchmark that loses to plain
vector. The section was setting up a payoff that §8 refutes. It was also the
#1 cut candidate on its own merits.)*

> ## Fix entity resolution before you tune retrieval.

> Personalized PageRank over a graph where Sacagawea is nineteen nodes will
> confidently rank the wrong passages — and it will look like it is working.
>
> You just watched it be worth **8 passages against 47**. That is not a
> hygiene argument, it is a retrieval argument: everything in the next three
> sections walks on these edges, and a walk from the wrong node is confidently
> wrong.
>
> Build time gates query time. That is the whole reason this section comes
> before the next one.

*(Hands directly to section 5.)*

---

### Timing

| slide | min |
|---|---|
| 4.1 the failure (+ LLM extraction) | 0:45 |
| 4.2 make it personal | 1:00 |
| 4.3 string ladder + wall | 1:15 |
| 4.4 the scraped website | 1:00 |
| 4.5 co-occurrence diagram + OVERLAP | 1:15 |
| 4.6 the payoff (recording) + 8→47 | 1:30 |
| 4.7 what it costs | 1:00 |
| 4.8 what WCC is, what it's for, the bridge | 1:45 |
| 4.9 take home | 0:30 |
| **total** | **10:00** |

⚠️ **Over budget by 1:00**, down from +1:30. Applied: **4.9 is cut** (−0:45).
Kept, per Nathan: **4.3 and 4.7**. Added, per Nathan: the WCC definition in
4.8 (+0:15).

Remaining candidates, re-ranked for the last slot:

1. **4.7 down to its two-line recall/precision slide (−0:30)** — drop the
   328,455-pair table. **Take this one.** Four numbers serving a point the two
   lines already make, and §4's densest few seconds.
2. **4.6's 8→47 table (−0:20)** — reluctantly next. It is the section's only
   hard number and the whole point of adding it, but three rows is three rows.
3. **4.3's Jaro-Winkler aside (−0:20)** — ⚠️ **protect this, don't cut it.**
   It was candidate #2 before the slot was known; that was backwards. It is
   the only place the talk shows a real shipped bug, it gets a laugh, and a
   laugh at minute 18 of the last session of the conference is worth more than
   twenty seconds of budget. If the room is flat, this beat is *why* you keep
   it.

Cutting 1 lands at 9:30. Cutting 1 and 2 lands at 9:10.

**Do not cut 4.2, 4.5's diagram, 4.6 or 4.8.** Those are the section.

---

### Assets still needed

- [ ] **DONE — the 4.5 co-occurrence diagram**: Nathan's arrows.app export,
      `sacagawea appears with indian woman.svg`. **Three fixes before it goes
      in the deck:** (a) add `viewBox="0 0 1776.88 1045.58"` and drop the fixed
      `width`/`height`, or it will not scale in reveal.js; (b) node captions
      wrap mid-word in the export (`Sacagawe|a`, `Cameahw|ait`) — widen the
      nodes in arrows.app and re-export; (c) the background is already
      transparent and the node fills (`#00bff3`, `#ffb9f8`) suit the dark
      palette, but the `#959aa1` edge labels want a contrast check on the
      projector
- [ ] OVERLAP two-circle diagram — **arrows.app export** (real numbers)
- [ ] Bridge-node chain diagram — **arrows.app export**
- [ ] WCC "three pairs → one entity" diagram for 4.8 — **arrows.app export**
- [ ] The 8→47 before/after table styled as the section's payoff number
- [ ] Screenshot of `enrich_sacagawea.py` with `SOURCE_URL` highlighted
- [ ] Recording of `demo_resolution.py` — resolution stays pre-recorded, and
      with §0 now a screenshot the live count is **two** (5.9, and §7's single
      terminal session)

### Open decision — resolved

4.6 says "the graph built **without** the scraper", and Nathan has settled
which database that is: **`rawluna`** (open decision #2 — *"Don't use neo4j
database for anything"*). It is pre-disambiguation, so the *closed cluster*
comes from `demo_resolution.py --adjudicate` rather than from merged nodes in
the graph — the audience watches it happen rather than seeing a result, which
is the better recording anyway. The 8→47 table pairs `rawluna` (8) with
`lewisclark` (47): same corpus, same extraction, before and after the merge.


---

## Section 5 — "Your ranking can't tell people apart"

*entity-seeded personalized PageRank · 10:25 (budget 10:00) · starts 0:24:45* · source: [`section-05-slides.md`](section-05-slides.md)

> **✅ Title signed off (Nathan, 2026-09-08): *"Your ranking can't tell people
> apart."*** The original *"Your ranking is wrong"* over-promised at the passage
> level; the second draft *"can't combine evidence"* was written for a
> conjunction thesis that was measured and retracted. This one matches what is
> demonstrable. §3's roadmap row and the outline's §5 header now both track it.
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
>   sixteen passages in full (finding 5d). Say **that** from the stage, in one
>   sentence. **Do not tell the retraction story** — Nathan's call, 2026-09-08,
>   open decision #3. The disclosure stays ("I judged these by reading them");
>   the twenty-second narrative about the metric that measured the wrong thing
>   comes out. It survives in the outline and as a Q&A pocket.
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

### 5.2 — Name it (0:45)

**Slide:**

> ## Co-typed entity substitution
> ### You asked what **this man** did.
> ### It told you what **an interpreter** does.

> Note what the question did *not* say: it never used the word "interpreter."
> It named a man and asked for his role. Retrieval worked out that his role was
> interpreting — which is genuinely impressive — and then handed back the job
> description instead of the man.

**Slide:** why, in one line of arithmetic.

> ### A passage embedding is an average over ~330 words.

> In a passage about Dorion negotiating with the Sioux, *interpreter, chief,
> speech, presents, nation* recur throughout and dominate that average; a
> surname that appears **once**, between a weather note and a hunting tally,
> contributes a sliver.
>
> So the passage actually about Charbonneau sits **further** from the question
> than a passage about a different interpreter doing interpreter things. Cosine
> cannot make identity a **hard** constraint — they differ by one low-mass
> token and agree on everything else.

**Slide — take it home. This is the slide people will remember.**

> ## Your corpus has forty engineers.
> ## You ask what **Chen** owns.
> ## You get three passages about **Rodriguez** owning a similar service.

> Because *"engineer owns service"* is most of the sentence, and *"Chen"* is one
> word of it.
>
> *(Beat.)* Hold onto the forty engineers. We come back to them at the end.

---

### 5.3 — How personalized PageRank actually works (1:30)

*(Reworked on Nathan's note: the plain-PageRank aside and the pivot slide are
**out** — the aside was also cut #3 on the §5 cut list. What replaces them is
the mechanism, because every later beat in this section is an argument about
where mass goes, and the room cannot follow those arguments without this one.
**5.7's damping material is folded in here** rather than into 5.6 — damping is
part of the mechanism, and explaining it twice was the reason 5.7 existed.)*

**Slide:** the two questions.

> **PageRank:** what is important in this graph?
> **Personalized PageRank:** what is important *relative to these nodes?*

**Slide — the animation.** One seed, mass spreading, four steps. This is the
one build in the talk that has to move.

```
 step 0     ●1.00  on the seed          everything else 0
                │
 step 1     split it along the seed's mention edges
            ● .125  ● .125  ● .125 …    (8 passages, schematic)
                │
 step 2     each passage splits ITS mass over the entities it names
            the people and places in those passages light up
                │
 step 3     and back out to THEIR passages
            passages that never mention the seed now hold mass
                │
 step 4     …iterate until the numbers stop moving
```

*(Eight edges because eight is drawable. The real `SACAGAWEA` has **85**
mention edges, so her first step hands each passage about 1.2% — which is worth
saying out loud, because it is exactly the arithmetic behind 5.6's hub trap and
5.13's "2 of 85" bridge.)*

> Say it as one sentence and let the animation carry it: **put a unit of mass
> on the node you care about, let every node hand its mass to its neighbours,
> repeat until the numbers stop changing.** Whatever ends up holding a lot of
> mass is well connected *to your seed* — not well connected in general.
>
> That's the whole algorithm. The "walk" language — a random surfer clicking
> links — is how the proof goes, not how the code runs; as section 1 said, this
> is a matrix multiply iterated to convergence.
>
> The one thing to watch in the animation: **step 3 is where it stops being a
> lookup.** Mass reaches passages that never mention your seed at all, because
> they mention people your seed is mentioned *with*. Steps 0 and 1 are just a
> tag filter with extra arithmetic; step 3 is the part a filter cannot do. That
> is the entire value proposition of this section, and it happens on step
> three.

**Slide — and the one parameter, which is not a magic number.**

> ### Damping `d` is a **horizon**, not a tuning knob.
> ### share of mass within *k* steps = `1 − d^(k+1)`

> | damping | mass within 3 steps |
> |---|---|
> | **0.45** | **96%** |
> | 0.85 | 48% |

> At every step, a fraction of the mass **teleports back to the seed** instead
> of spreading onward. That fraction is what stops the mass diffusing into the
> whole graph until it is just a popularity contest — it is exactly what makes
> this *personalized*. Set it to 1.0 and there is no teleport: you get plain
> PageRank, and your seed stops mattering.
>
> So read `d` as "how far from the seed am I willing to look." Three steps is
> what you want on a bipartite graph like this one — step 1 is her passages,
> step 3 is her co-mentioned entities' passages. That is the neighbourhood.
>
> `0.85` is the number in every tutorial, including tutorials I have written,
> and it puts **less than half** the mass inside that horizon. Measured on this
> corpus, shorter was better at every value we tried.

---

### 5.4 — Seed the entity. Seed all of them. (1:15)

**Slide:** the fix, in one sentence.

> ### `MENTIONED_IN` is a **discrete** edge.
> ### Either extraction attached the entity, or it didn't.

> No averaging. Identity is binary. That is the hard constraint cosine can only
> express softly — and it is the whole trick.
>
> Median 40 words per entity in a 333-word passage. **The entity is a pointer.
> The embedding is an average.**

**Slide:** but don't pick one.

> ### Your entity resolution will never be perfect.
> ### **So stop building retrieval that needs it to be.**
>
> Question mentions a tree. Your graph has four `POPULUS` species — and you
> genuinely do not know which one is "real."
>
> ## You don't have to choose.

> This is the slide that earns section 4 its place *and* forgives it. You just
> watched resolution take Sacagawea from 8 passages to 47 — and leave nine
> forms behind, and leave `DREWYER` and `GEORGE DROUILLARD` as two nodes. That
> is the permanent state of every corpus. **Nobody ships a resolved graph; they
> ship a less-broken one.**
>
> So the design question is not "how do I get resolution right." It is "what
> does retrieval do when resolution is wrong" — and the answer is: seed every
> candidate, weight them, and let the arithmetic sort it out.

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
>
> *(One sentence of housekeeping, and then we move — Nathan's note: "Just say
> we're walking on the MENTIONS graph." So: **everything in this section walks
> on the mention edges only** — entity-in-passage, nothing else. The extracted
> entity-to-entity edges are out, and so is the chunk-to-chunk chain. Why is a
> good question and it is section 6's, where the projection changes and it
> matters.)*

---

*(**5.5 — "The graph you walk on is a decision" — is cut.** Nathan: "I don't
think we have time to go into this. Just say we're walking on the MENTIONS
graph." Cut #1 on the §5 list, −0:45. The material is not lost: the one line
worth keeping — *a projection is not neutral infrastructure* — is now a clause
in 5.4 above, and the full contrast gets a better home in **§6.3**, where
Leiden runs on a **different** projection and the difference is the point.)*

---

### 5.6 — The hub trap (0:45)

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
| **mentions only** | **short** | **IDF** | **0.47 / 8** · Lewis ranks **18.1** |

*(Cut #6 applied: first and last rows only. The two middle rows — IDF alone at
2.04, short walk alone at 1.27 — move to the speaker note, where they still
make the "each one helps, it takes all three" point without four rows of
table.)*

> Top row is the configuration everyone writes first: all your edges, damping
> 0.85 because that is the number in every tutorial, no weighting because why
> would you weight. Fourteen different questions and the walk returns **nearly
> three of the same eight entities** every time — and Lewis is in the top
> handful for *every* question, whatever you ask.
>
> **Three choices, and each one helps on its own — it takes all three to
> finish the job.** Drop the edges whose direction is meaningless. Shorten the
> walk. IDF-weight the mentions. *(The middle rows, if you want them out loud:
> IDF alone gets 2.84 → 2.04; the short walk alone gets it to 1.27. Together
> with the projection: 0.47.)*
>
> The weight is the standard one — a mention of a rare entity counts for more
> than a mention of Lewis:

```
weight  =  log( 1 + total_chunks / chunks_mentioning_this_entity )
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

*(**5.7 — "Keep the walk short" — is cut as a separate beat** (cut #2, −0:30).
Its content is not gone: the `1 − d^(k+1)` horizon, the 96%-vs-48% table and
the "shorter was better at every value" line are all **in 5.3 now**, where
damping is introduced as part of the mechanism. The cut list folded it into
5.6; folding it into 5.3 costs the same and means damping gets explained once
instead of half-explained twice.)*

---

### 5.8 — The blend, and one honest knob (0:20) · abstract takeaway #2

**Slide:** the credibility move.

> # alpha = 1.0
> ### reproduces the vector baseline byte for byte
> ### 14 questions, 14 identical orderings

> Before I show you a knob, I want you to trust it is a real knob and that I
> have not quietly swapped the baseline underneath it.

> Before I show you a knob, I want you to trust it is a real knob and that I
> have not quietly swapped the baseline underneath it. Turn the blend all the
> way to cosine and you get cosine back, exactly, on all fourteen questions.
>
> *(Cut #5 applied: the "two places to combine" slide is gone. If it comes up —
> blend in the **seed weights**, not in the final score, so structure operates
> on a semantically-informed prior instead of two signals fighting after the
> fact. And the mixing weight is forgiving over a wide range here, which is the
> useful news: not a delicate parameter.)*

---

### 5.9 — The payoff (0:55) · **LIVE DEMO**

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

**Slide:** the promotion worth reading, and what it adds.

```
1805-03-18   "Mr. Tousent Chabono, Enlisted as an Interpreter this evening"
             -> the hiring itself            (cosine rank 22)
```

> Cosine's own #1 was the *end* of the story — the 1806 settlement, "Settled
> with Touisant Chabono for his Services as an enterpreter … 500$ 33⅓ cents."
> The graph adds how the job **began**. Cosine had the payoff; it did not have
> the hiring.
>
> *(Cut #7 applied: the 1805-04-07 Snake-assignment roster comes out. It is not
> a loss — the *better* version of that passage, the Nov-4 hiring-and-arrangement
> entry, is already on stage in 5.4 and is protected from cutting.)*

**Say this plainly, in one sentence — it is the section's integrity:**

> **I judged these by reading them.** Eleven promoted passages across three
> questions, read in full: *does this contain something a correct answer needs
> that no cosine passage has?* **Three of eleven cleared that bar.** Not a rout,
> and I would rather hand you three read passages than a percentage.
>
> *(Open decision #3, settled by Nathan 2026-09-08: **don't tell the retraction
> story.** The twenty seconds on "I had a metric that said it was much better,
> and it was measuring the wrong thing" comes out. The disclosure above stays —
> it is a constraint on this section, not the same thing as the narrative. The
> full retraction lives in the outline and is a Q&A pocket; if someone asks how
> the three-of-eleven number was arrived at, that is the moment for it, and it
> lands better as an answer than as a confession nobody requested.)*

---

### 5.10 — Three things it cannot do (1:00)

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
*(Cut #8 applied: the normalisation parenthetical is out. Q&A pocket —
normalising the seeds to equal footing gives a beautiful conjunction signal and
drops every hand-verified passage out of the top-8, because normalising a
sparse walk hands its noise floor 66% of the score range.)*

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

### 5.11 — What it costs (0:25)

**Slide:**

| | |
|---|---|
| project the graph | **67 ms**, once |
| plain cosine top-8 | **6 ms** |
| this, on a fresh question | **~215 ms** |

**Slide:**

> ### ~35× plain vector — and it doesn't matter.
> The generation call you're about to make dwarfs 200 ms.

> *(Cut #4 applied: the `sourceNodes` retraction is out — keep the cost table,
> drop the story. Q&A pocket: the API takes the whole weighted seed set in one
> call; I built it one call per seed because I assumed weighted seeds required
> it, and paid 494 ms instead of 66. "Read the signature before you design
> around it.")*

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

### 5.13 — The answer is a name you don't have (0:45) · `lewisclark`

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
> **And when the anchor is obscure, one shot works.** Same question shape, the
> Walla Walla chief who hosted them — anchor in **3** passages, not 85 — and
> the blend puts his chunks at median rank **10**. One line, and move.
>
> *(Cut #11 applied. Q&A pocket: four of those passages are ones no filter can
> reach, because no spelling of the nation is tagged on them. And note for
> §9.1 — that pair also appears in the 38k-pair decay sweep at rank **16**;
> two different measurements of the same pair, and §9.1 now says which is
> which. Review finding R6.)*

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

### PARKED FOR §9 — now a pointer, not a copy

**The bridge-decay curve lives in [§9.1](#91--when-to-reach-for-the-graph-one-number-decides).**
The numbers are §5's (finding 5n) and this is where the block was drafted, but
the canonical copy — table, speaker note, router query — is §9.1's, and it was
duplicated here verbatim through the compile. **Deduplicated 2026-09-08**
(review finding R9): edits belong in §9.1.

---

### Timing

**All eleven cuts applied** (Nathan, 2026-09-08: *"I support all these cuts"*),
plus open decision #3 (drop the retraction story, −0:20).

| slide | was | now | what changed |
|---|---|---|---|
| 5.1 the failure | 1:15 | 1:15 | — |
| 5.2 name it + forty engineers | 1:00 | 0:45 | mechanism tightened (cut 10); *"an interpreter"* framing fixed |
| 5.3 **how personalized PageRank works** | 1:00 | **1:30** | aside + pivot out (cut 3); mechanism, animation and damping in; **5.7 folded in** |
| 5.4 seed the entity, seed all of them | 1:30 | 1:15 | honesty parenthetical out (cut 9); reframed on imperfect resolution |
| ~~5.5 the projection is a decision~~ | 0:45 | — | **cut** (cut 1); one clause kept in 5.4, the contrast moves to §6.3 |
| 5.6 the hub trap | 1:15 | 0:45 | hub table down to two rows (cut 6) |
| ~~5.7 keep the walk short~~ | 0:30 | — | **cut** (cut 2); damping now lives in 5.3 |
| 5.8 the blend | 0:45 | 0:20 | `alpha=1.0` slide only (cut 5) |
| 5.9 the payoff (**live demo**) | 1:30 | 0:55 | one promoted passage (cut 7); retraction story out (decision #3) |
| 5.10 three things it cannot do | 1:15 | 1:00 | normalisation parenthetical out (cut 8) |
| 5.11 what it costs | 0:45 | 0:25 | `sourceNodes` retraction out (cut 4) |
| 5.12 the question that names nothing | 1:00 | 1:00 | — |
| 5.13 the answer is a name you don't have | 1:00 | 0:45 | Walla Walla to one line (cut 11) |
| 5.14 take home: one number decides | 0:30 | 0:30 | — |
| | **14:00** | **10:25** | **−3:35** |

⚠️ **+0:25, down from +4:00.** The cut plan promised exactly 10:00, and it
would have hit it — the extra 25 seconds are **5.3**, where Nathan asked for
the mechanism to be explained properly (mass distribution, the animation, and
damping). That is a fair trade and I would not take it back: every argument in
5.4, 5.6, 5.10 and 5.13 is an argument about where mass goes, and the room
cannot follow them from "PageRank in 60 seconds."

**Two ways to close the last 0:25, neither applied:**

1. **Move 5.12 (trade-goods) to open §6** — still the best option, and now
   *more* attractive than when it was drafted: §6's motivating failure is the
   illness collapse, trade-goods is the same walk winning, and §8 scores both
   as coverage failures (finding R1), so telling them together is the honest
   framing. Saves 1:00 here, costs §6 1:00 — a section-budget trade that puts
   §5 at 9:25 and §6 at 7:00.
2. **Drop the §0.3 table of contents (−0:20)** and let §3's roadmap do it.
   Costs §5 nothing, and §3 is the load-bearing version anyway.

**Do not cut 5.1, 5.2's forty-engineers slide, 5.3's animation, 5.4's Nov-4
passage, 5.9, the three limits of 5.10, or any of 5.12–5.14.** The old close
(tags-vs-graph rule) is not lost — it *is* 5.14's first and last table rows,
now with measured receipts behind every row.

---

### Assets still needed

- [ ] 5.1's tagged top-8 as a slide where the "wrong name" column reads at a
      glance — the names are the punchline, set them large
- [ ] The forty-engineers slide. Text only, big. No diagram.
- [ ] Hub table styled so Lewis-at-28%-of-the-corpus and elk-above-Clark land
      without explanation (source: `NEO4J_DATABASE=lewisclark
      demo_pagerank.py --hubs`)
- [ ] "Concentrate at the entity level, dissipate at the passage level" —
      **arrows.app export**: one hub, many arrows in, the same many arrows
      out, thin
- [ ] **5.3's mass-distribution animation** — the one build in the talk that
      has to move. Four steps from a single `SACAGAWEA` seed: mass 1.0 → split
      across her 9 mention edges → into the entities those passages name →
      back out to *their* passages. **Step 3 is the beat**: passages light up
      that never mention her. Reveal.js fragments over one arrows.app export
      (five states of the same diagram, opacity/colour per fragment) is
      cheaper and more reliable than a video, and it stays legible if the
      projector eats the animation
- [ ] **5.3's damping slide** — `1 − d^(k+1)` with the 96%/48% table; the
      teleport-back-to-seed arrow is the part that makes it click
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

### Open decisions — all three closed by Nathan, 2026-09-08

1. **The title** — ✅ *"Your ranking can't tell people apart."* Nathan: *"Title
   is fine."* §3's roadmap row and the outline's §5 header now match it
   (review finding R15).
2. **Which database** — ✅ *"Don't use neo4j database for anything."* §5 was
   already fully migrated to `lewisclark` (finding 5o). What this decision
   changes is **§4**: 4.6's "before" graph is `rawluna`, and the 8→47 receipt
   pairs `rawluna` with `lewisclark`. `neo4j` is now history in the outline
   only, and nothing on stage runs against it. *(Two spoken asides still refer
   to the previous **extraction** — 5.6's white-tailed-deer hub and 5.10's
   horse-passage coda. Those are claims about an earlier extraction, not
   measurements taken on `neo4j` at showtime, and they are the strongest
   "better extraction moves the boundary" material in the talk, so they stay.
   Flagging them so the decision is not later read as broken.)*
3. **How much of the retraction to tell** — ✅ *"Don't tell the retraction
   story."* Applied in 5.9: the disclosure ("I judged these by reading them",
   three of eleven) stays, because it is a standing constraint on this section;
   the twenty-second narrative comes out. It is a Q&A pocket, and it answers
   better than it confesses.

**Decided (2026-09-07):** 5.12 is the tags-vs.-graph decision rule;
the filter-parity finding (outline 5g) gets **no stage time** — it is the Q&A
pocket behind 5.12. Title remains open (decision #1).

**Redrafted (2026-09-07, later):** the close is now the 5l/5m/5n story —
5.12 the thematic win (buttons), 5.13 the brother question (whiff → the name
→ two-step), 5.14 the routing rule, with the decay curve parked for §9. The
old tags-vs-graph rule survives as 5.14's table rows.

**Settled (2026-09-08):** (a) the eleven trims are **applied** — Nathan
supports all of them; (b) moving 5.12 to open §6 stays available and is now
the recommended way to close the last 0:25, argued under the cut table; (c)
the database split was already resolved and is now decided in the stronger
form — *nothing* runs on `neo4j`.


---

## Section 6 — "Your context is redundant"

*community detection: Leiden and conductance · 6 minutes · starts 0:35:10* · source: [`section-06-slides.md`](section-06-slides.md)

> **Editorial constraints for this section:**
>
> - **⚠️ This is the most number-dense section in the talk** — 126 figures on
>   screen across six minutes, at minutes 35–41 of the final slot. Two of those
>   clusters are fine and should not be "fixed": 6.1's eight repeated dates are
>   meant to read as a *pattern*, not as data ("every slot is the same week"),
>   and 6.3's themes table is meant to be skimmed as structure, the way you
>   skim a book's contents page. Say both of those out loud as shapes rather
>   than reading the numbers. The genuinely optional density is 6.3's
>   projection table (§5.4 already gives the one-line version) — that is the
>   drop-in if the room is flat.
> - **Every number on screen is either exact or a hand read, and says which.**
>   Community counts, months, community ids, cosine ranks, conductance: exact.
>   "The recovered passages are the right ones": judged by reading, said so
>   from the stage — same posture as section 5.
> - **The cold open is inherited, not invented.** Section 5 *measured* the
>   illness collapse (finding 5l) and handed it here. Play it as continuity:
>   the best retriever so far caused the worst window.
> - **Leiden only — and Louvain is now gone from the code too.** Nathan,
>   2026-09-08: *"I don't want to use or teach Louvain."* That closed review
>   finding R2, which had found three places still saying Louvain, including one
>   that mattered: `CommunityConfig.algorithm` **defaulted to `louvain`**, so
>   §8's `community` and `hybrid` rows had been benchmarked with the algorithm
>   this section tells people to avoid. The default is now `leiden`, the
>   benchmark has been **re-run**, and §8.2's table and note are updated.
>   Louvain survives only as a selectable flag for demonstrating the
>   difference; it gets no stage time and no Q&A pocket.
> - **No vendor *procedure signatures* on the slides.** Nathan, 2026-09-08:
>   *"Don't show Neo4j syntax in the deck if we can help it. Try to make this
>   vendor neutral."* 6.2's `gds.leiden.mutate` call is **off the slide** — the
>   parameters that matter (weighted, seeded, concurrency 1) are said out loud
>   instead. §9.2's whole argument is that these are algorithms, not products;
>   showing one vendor's procedure signature undercuts it four sections early.
>   **The line is procedures, not the query language:** §9.1's router query
>   stays as written, because openCypher and the GQL standard are implemented by
>   more vendors than Neo4j (Nathan's call, same day) — a `MATCH … RETURN
>   count()` reads as a graph query, not as a product. A `gds.*` call does not.
> - **The honesty beats get stage time**: Leiden's connectivity asterisk and
>   the community-vs-episode grain mismatch. Each is a one-query demonstration
>   — they *are* the talk's thesis, not hedges on it.
> - Every window below is from the seeded-Leiden run
>   (`measure_communities.py`, byte-identical across re-runs — **re-verified
>   2026-09-08**: three consecutive benchmark runs returned 88.1% recall and
>   0.049 redundancy to the digit).

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
>
> *(**Timekeeping anchor #2 of 2** — review finding R19. This slide should be
> up by **0:35**. §4 and §5 are the only sections that have ever run long and
> they are both behind you now, so if the clock is fine here it is fine for the
> rest of the hour. If it isn't: **6.5** and **7.3** are the drop-ins, in that
> order — 6.5 is a limit the audience will accept unstated, 7.3 is
> methodology. Do **not** buy time out of 6.4; it is the fix this whole section
> exists to show.)*

---

### 6.2 — Leiden (1:00)

**Slide:** the one-line definition, against section 4's.

> **WCC** (section 4): *connected at all* — one path suffices.
> **Leiden**: *densely connected relative to chance* — neighborhoods,
> not reachability.

**Slide (build) — the same graph, both algorithms, measured.** This is the
diagram Nathan asked for: one component, many communities.

```
        ┌──────────────── one WCC component: all 8,139 nodes ─────────────────┐
        │                                                                     │
        │    ╭───────╮   ╭───────╮   ╭───────╮   ╭───────╮   ╭───────╮        │
        │    │  c5   │   │  c23  │   │  c8   │   │  c44  │   │  c24  │  …     │
        │    │ 691   │   │ 286   │   │ 275   │   │ 212   │   │ 160   │        │
        │    ╰───────╯   ╰───────╯   ╰───────╯   ╰───────╯   ╰───────╯        │
        │                                                                     │
        └─────────────────────────────────────────────────────────────────────┘

              WCC says:     1 component
              Leiden says:  47 communities
```

> Run both on the same projection and this is what you get: **WCC returns one
> component containing every node in the graph. Leiden returns forty-seven
> communities inside it.**
>
> That is not a disagreement — they answered different questions. WCC was asked
> "is any of this reachable from any of the rest," and on a real corpus the
> answer is always yes, because everything is two hops from Lewis. Leiden was
> asked "which of these neighborhoods are denser than chance," and there the
> answer has structure in it.
>
> Which is exactly why section 4 used WCC for identity and this section does
> not: transitive closure wants "connected at all." Themes need "denser than
> chance."

**Slide (build):** one call, and it's repeatable.

> ### 47 communities · all 2,913 chunks covered · ~100 ms
> ### **weighted · seeded · single-threaded**

> One call — and deliberately **not** shown as one vendor's procedure
> signature; §9.2 argues these are algorithms rather than products and I would
> rather not undercut that here. Every library spells this differently and they
> all take the same three things that matter:
>
> - **weighted**, on the same IDF mention weight section 5 used
> - **a random seed**, which is why this partition is the same one every time
> - **single-threaded** — because on most implementations the seed only bites
>   at concurrency 1, which is a footgun worth naming out loud
>
> That third one is the practical tip: people set the seed, leave concurrency
> at default, and conclude the algorithm is nondeterministic.

**Slide:** the honesty beat.

> Leiden *guarantees* internally connected communities.
> Ours had **one 24-node community split 13 / 11**. Verify — it's one WCC
> call per community, and you already know WCC from section 4.

> Same family of algorithms as section 4's WCC, opposite question: not "can
> you get there at all" but "is this neighborhood denser than chance predicts."
> Leiden is the current standard for that, and it takes a random seed — which
> matters here, because this talk's discipline is re-run-and-diff, and an
> algorithm that redraws its themes every run can't be measured or demoed.
>
> *(If someone names Louvain in Q&A: it is the predecessor, it can emit
> internally disconnected communities, and it has no seed parameter — so it
> deals a fresh partition every run. That last property is not academic; it was
> silently in this talk's own benchmark until 2026-09-08. One sentence, then
> move on — Nathan does not want it taught.)*
>
> The asterisk is the section in miniature: the algorithm's *paper* guarantees
> connectivity; the implementation on your graph is a claim to check, and the
> check costs one query. Verify; don't trust the name.

---

### 6.3 — The table of contents nobody wrote (0:45)

**Slide — first, what it ran on.** The projection Nathan asked to have
explained, and it is a different one from section 5's:

> | | §5's walk | §6's Leiden |
> |---|---|---|
> | entity → passage | ✅ weighted by IDF | ✅ weighted by IDF |
> | passage → next passage | ❌ | ✅ |
> | entity → entity | ❌ | ✅ |
> | | 7,354 nodes · 44,900 edges | 8,139 nodes · 63,836 edges |

> Ten seconds, and it pays for itself. Section 5 threw away two thirds of the
> graph on purpose — a walk needs every outbound edge to mean one consistent
> thing, and `MEMBER_OF` and `SHOT` do not. **Community detection wants them
> back.**
>
> Because look at what a theme actually *is* in a journal: a stretch of
> consecutive entries, plus the people and places they share. The
> passage-to-passage chain is the "consecutive" half. Section 5 dropped it
> because adjacency in time is not evidence of relevance; section 6 needs it
> because adjacency in time is most of what an *episode* means.
>
> **Same graph, two projections, opposite decisions — and both are right.**
> That is the whole content of the beat section 5 cut for time.

**Slide:** the themes table, output from `demo_communities.py`.

```
 id  chunks  span                 cond.  defining entities
 5      691  1804-05 → 1806-09    0.37   MERIWETHER LEWIS, CERVUS CANADENSIS, WILLIAM CLARK, DREWYER
 23     286  1804-05 → 1806-09    0.39   PRYOR, SHIELDS, SHANNON, GASS, SACAGAWEA, GEORGE DROUILLARD
 8      275  1804-05 → 1806-09    0.25   MANDAN, HIDATSA, SIOUX, ARIKARA, CORN, FORT MANDAN
 44     212  1804-07 → 1806-08    0.34   CLATSOP, SAGITTARIA LATIFOLIA, NETUL, SALT
 24     160  1804-10 → 1806-08    0.38   SHOSHONE, HORSES, NEZ PERCE
 …
```

> The corpus's own structure, summarized: the daily hunting economy, the corps
> roster, the Mandan winter, the Clatsop salt camp, the Shoshone horse
> negotiations. Nobody wrote this index, and deriving it cost **zero
> additional tokens** — Leiden reads the mention edges earlier sections
> already built; no LLM is in the loop. (Say "additional" precisely: on a
> natively-linked corpus like a wiki it's zero, full stop — section 2's beat.)
>
> **And read the two Drouillards out loud, because they are the best
> unplanned receipt in the section** (review finding R4): `GEORGE DROUILLARD`
> is in c23 with the corps roster. `DREWYER` — the same man, 297 passages — is
> in **c5**, with the hunting economy. Section 4 told you an unresolved entity
> costs you recall. Here it costs you something else: the man is filed under
> two different *themes*, and no amount of community detection can merge them,
> because as far as this graph is concerned they are two people who did two
> different jobs. **Build time gates query time, and this is what it looks like
> three sections later.**
>
> The `cond.` column is **conductance**: the share of a community's edge weight
> that leaves it. Rule of thumb, from Zach Blumenfeld's Karpathy-wiki post
> (the further-reading slide): ≤0.35 is a tight theme you can build on, ≥0.60
> is a loose one you shouldn't.
>
> **Now say the awkward thing out loud, because the room is already doing the
> arithmetic** (review finding R7, Nathan's call — *"Say out loud that the big
> ones are loose"*): three of the five numbers on this slide fail the threshold
> I just handed you. That is not a problem with the partition, it is **what
> this slide is a sample of** — these are the five *largest* communities, and
> size and looseness go together. Across all 47: median conductance **0.27**,
> 35 of 47 tight, none loose. The five on screen: median **0.37**. The other
> 42: median **0.25**.
>
> So the honest version is *"the big ones are the loose ones, and that is the
> normal shape of a partition"* — which is more useful than a clean slide,
> because it is the thing they will find on their own corpus in ten minutes.

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

> Community **23**: 286 chunks, 1804-05 → 1806-09 — "the corps members."
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
| 6.2 Leiden (+ WCC-vs-Leiden diagram) | 1:00 | 2:00 |
| 6.3 projection + table of contents + conductance | 0:45 | 2:45 |
| 6.4 the fix, measured | 1:45 | 4:30 |
| 6.5 the bound | 1:00 | 5:30 |
| 6.6 hand-off | 0:30 | 6:00 |
| **total** | | **6:00** |

**On budget.** 6.2 and 6.3 both gained material (the diagram, the projection
table, the conductance honesty) without gaining time — what paid for it was
removing the Cypher block from 6.2 and the "rides on section 4's merge" note
from 6.3, both of which needed narration. If 6.3 runs long in rehearsal, the
projection table is the drop-in: it is the cheapest 10 seconds to lose and
§5.4 already says the one-line version.

⚠️ **If §5.12 moves here** (§5's recommended way to close its last 0:25), this
section becomes 7:00 and the ledger's total does not change.

---

### Assets still needed

*(This section had no assets list — review finding R14.)*

- [ ] **The WCC-vs-Leiden diagram for 6.2** — Nathan's ask, and the numbers are
      verified: one WCC component of 8,139 nodes, 47 Leiden communities inside
      it. **arrows.app export**, communities as coloured clusters inside one
      outlined boundary; the five largest labelled with their chunk counts, the
      rest as unlabelled dots
- [ ] **The projection comparison table for 6.3** — §5's walk vs §6's Leiden,
      with the two edge types §6 adds back visually emphasised
- [ ] The themes table styled as a table of contents — it should *look* like a
      book's front matter; the `cond.` column set quieter than the rest
- [ ] The conductance honesty line as a slide element, not just narration:
      **five largest median 0.37 · other 42 median 0.25**
- [ ] The illness before/after window table (months / communities / near-dups)
- [ ] The three recovered passages with their cosine ranks as a caption
- [ ] Decide whether `demo_communities.py` runs live or ships as captured
      output. **Recommend captured** — with §0 now a screenshot the live budget
      is two demos (5.9 and §7), and this table is 47 rows of terminal output
      that gains nothing from being live


---

## Section 7 — "You can't explain the answer"

*path finding: Yen's k-shortest paths, with receipts · 5 minutes · starts 0:41:10* · source: [`section-07-slides.md`](section-07-slides.md)

> **Editorial constraints for this section:**
>
> - **Every route and receipt on screen ran live on `lewisclark` and was
>   hand-read** (finding 7a–7g; read-pack `results/paths-lewisclark-readpack.md`,
>   local only). Route order is deterministic — the shipped tie-sort.
> - **⚠️ Warm the projection before this section.** Review finding R5 flagged
>   §7's *~220 ms* against §8's *23 ms* as an order-of-magnitude contradiction.
>   Measured 2026-09-08, and they are both right: the **first** path query in a
>   fresh process costs **~212 ms**, every one after it costs **~23 ms**
>   (reproduced across two fresh processes: 211.9 / 22.9 / 21.5 / 23.7 and
>   211.1 / 26.8 / 43.8 / 24.4). §7 was quoting a cold start and §8 the warm
>   steady state. Both numbers are now labelled as such on the slides — and the
>   practical consequence is a rehearsal instruction: **run one throwaway path
>   query before you walk on stage**, or 7.2 pays the cold start in front of the
>   room.
> - **Anchors must be pinned on this graph.** `lewisclark` has no Person vector
>   index by design, so the anchor-inference path raises rather than degrades.
>   Both demos pass `--from`/`--to`, so this never fires — but do not
>   improvise an un-anchored path query on stage.
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
> *citation*, not a similarity score. **About 20 milliseconds** — this is the
> second query of the session, and the first one warmed the projection.
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

**Demo:** `demo_paths.py --from Cameahwait --to Hidatsa` — one more query in
**the same terminal session** as 7.2, which is why the talk's live-demo count is
two and not three (review finding R11). *(The 1-hop route is in the stable cost
class; safe live.)*

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

**Slide:** the NICD callback, in a clause.

> The agent in that study had this exact tool. **Zero calls.**

**Slide (build):**

> Path retrieval here is deterministic: resolve two anchors → Yen's → receipts
> → context. ~20 ms warm. **The model doesn't get a vote.**

> *(Review finding R18: this is the third telling of "called zero times" — §2.4
> is the hinge, §10.1 is take-home #2, and this one is compressed to a clause
> on purpose. Do not re-inflate it; the room already knows the number, and the
> callback works better as a nod than as a retelling.)*
>
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
| **total** | | **5:00** |

**On budget.** 7.3 is the drop-in if §6 overran — it is the most interesting
beat to lose and the only one that is purely methodological.

---

### Assets still needed

*(This section had no assets list — review finding R14.)*

- [ ] **The route table as the demo prints it**, three routes, the relationship
      types legible from the back — this is the slide that carries 7.2
- [ ] The recognition-scene receipt set large, with *"who proved to be a sister
      of the Chif Cameahwait"* emphasised — the phrase is the payoff
- [ ] The Cameahwait→Hidatsa route with the strike-through styling, and its
      receipt beside it. **The contradiction has to be readable in one look**:
      edge says "member of", citation says "attacked by"
- [ ] The k-set slide (edge exists → k=1; edge missing → somewhere in the set;
      Yen's enumerates, it cannot rank)
- [ ] **Rehearsal note, not an asset:** the warm-up path query, in the
      pre-flight checklist (see the constraint above — ~212 ms cold, ~23 ms
      warm)


---

## Section 8 — "Does this actually help?"

*the benchmark: answer-entity recall over 14 questions · 4 minutes · starts 0:46:10* · source: [`section-08-slides.md`](section-08-slides.md)

> **Editorial constraints for this section:**
>
> - **Audience calibration (Nathan, 2026-09-07): developers who want practical
>   guidelines and how-to — not statisticians.** Slides carry things they can
>   *do*; measurement methodology lives in speaker notes and Q&A. No
>   macro/micro, variance, or confidence vocabulary on screen. Every slide
>   should answer "what would I do with this on Monday."
> - **And the slot sharpens that (2026-09-08): this section lands at minute 46
>   of the last session of the last day.** §8 and §9 are the two most
>   number-dense sections in the talk, arriving exactly when the room is most
>   tired. 8.2's table has already been cut from five columns to three — the
>   p50 column went, and latency is now one line under the table ("7–200 ms,
>   all of it") rather than seven numbers. Read the table *for* them; assume
>   nobody is doing arithmetic. The rule for the rest of the section: **say the
>   one number that matters before you say anything about columns.**
> - **Every number re-measured 2026-09-08 on `lewisclark`** after the
>   Louvain→Leiden fix (review finding R2). `vector`/`ppr`/`expand`/
>   `cooccurrence` are unchanged and identical across runs — quote them
>   exactly. **`community` and `hybrid` are now reproducible too**: three
>   consecutive runs returned 88.1% / 0.049 / 0.050 to the digit, because
>   seeded Leiden replaced the Louvain redraw. The ±1-entity range that used to
>   be in this table was an artifact of an algorithm §6 tells people not to use,
>   and it is gone.
> - **⚠️ `paths` is the one row that is not reproducible, and the slide says
>   so.** Ten consecutive runs: 69.4 ×4, 77.8 ×3, 80.6 ×2, 88.9 ×1 — mean
>   **76.1%**, range 69.4–88.9. The cause is documented in the code: the
>   3-hop cost class has dozens of tied routes, more than the over-request
>   budget, so *which* ties fill the tail differs per invocation. The previous
>   draft quoted **69.4%** — a single draw, and the low one — as if it were the
>   value. Report the mean and the range, and say why in one sentence.
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

| strategy | what you watched | recall | Δ vs vector | p50 |
|---|---|---|---|---|
| **vector** | the cold open's baseline | **86.3%** | — | 7 ms |
| ppr *(rerank)* | §5's contrast variant — reranks the top-50 only | 86.3% | +0.0 | 87 ms |
| **expand** | **§5.9's live demo** | **88.1%** | **+1.8** | 202 ms |
| community | §6's capped window | 88.1% | +1.8 | 8 ms |
| cooccurrence | the §4 beat that got cut | 82.1% | −4.2 | 16 ms |
| paths | §7, and only 3 questions have anchors | 76.1% * | — | 23 ms |
| **hybrid** | §5 + §6 together — the production one | **88.1%** | **+1.8** | 90 ms |

> *\* `paths` is a mean over 10 runs (range 69.4–88.9). It is the only row
> here that moves. Everything else is identical run to run.*

**Slide (build) — which row was which demo** (review finding R3):

> ### `expand` is the demo you watched at minute 25. It is the **+1.8** row.
> ### `ppr` is the variant I showed you for contrast. It is the **+0.0** row.

**Slide (build):**

> ✓ **Controls: every strategy scored 100%, every run.**
> Nothing paid for the hard questions with the easy ones.

> Read it top to bottom. Plain vector, on a graph where section 4 already did
> its job, gets 86%. The best graph strategy adds 1.8 points — in raw counts,
> **one more answer entity in the window**. The controls are the row I care
> most about: vector should win them, and everything held.
>
> **Say the `expand`/`ppr` distinction out loud, because the audience cannot
> read it off the table** (review finding R3): the demo at minute 25 is
> `expand` — it scores every chunk in the corpus, which is the only way a
> passage at cosine rank 413 can be retrieved at all. `ppr` reranks the vector
> top-50, so its ceiling is "whatever is already in positions 9 through 50,"
> and unsurprisingly it moves nothing. **Same algorithm, and the one that
> reranks a shortlist is the one that scores zero.** That is a genuinely useful
> result and it would have been invisible if I had shown one row.
>
> Then three practical footnotes:
>
> **One — `community` and `hybrid` used to show a range here, and don't any
> more.** The old benchmark ran Louvain, which redraws its partition every
> run; §6 teaches Leiden with a pinned seed. Those disagreed until two days
> ago, and the range in this table was the smell. Pin the seed and the row goes
> still — three runs, same digits.
>
> **Two — `paths` still moves, and I'm leaving it visible.** Yen's enumerates
> tied routes and there are more three-hop ties than the query asks for, so the
> tail is effectively sampled. Ten runs spread 69 to 89. The mean is the honest
> number and the range is the honest error bar. Also: it only ran on three
> questions, because path retrieval isn't a general retriever — it fires when
> the question names two things, exactly as §7 said to wire it.
>
> **Three — the whole right-hand column is milliseconds.** The graph is not
> your latency problem.

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

> 1. the answer requires **traversal**, not lookup — *"what was Charbonneau's
>    role?"*, answered from the hiring entry cosine had at rank 22
> 2. the same entity is **named differently** across documents — Drewyer /
>    Drouillard / "the Indian woman"
> 3. the question is about **how things connect**, not what they say — *"what
>    about her brother?"*

> Look back at where the graph earned its keep tonight, and every win was one
> of these three shapes — **all three of these you watched happen**:
>
> **Traversal** is the cold open, closed. Charbonneau's role: 2 of 8 became 6
> of 8, and the passage that made it work was the enlistment entry sitting at
> cosine rank 22. **Naming** is Drewyer and Drouillard — and note it cost you
> twice: section 4 showed the recall loss, and section 6 showed the same man
> filed under two different *themes*, c5 and c23. **Connection** is the brother
> question: the walk hands back a name at rank 4, and then one passage out of
> 2,913 states the relationship, with a citation.
>
> **Now the uncomfortable part, and I want it on the record rather than
> smoothed over.** Two questions in this benchmark score badly: trade goods and
> illness. Those are the same two questions I stood here and called wins in
> sections 5 and 6 — the buttons cut off the captains' coats, promoted from
> rank 77; the illness window going from one week to four months.
>
> **Both things are true, and the disagreement is the finding.** I judged those
> two by reading the passages. The benchmark judges them by counting answer
> entities in the window. On these two questions those two methods reach
> opposite conclusions — and the metric is not obviously the one that's right:
> its complaint about the illness window is partly that the window stopped
> being eight copies of the same afternoon.
>
> What I can say without hedging is what *both* methods agree on: these two are
> **coverage** problems, not reasoning problems. The right chunks are thin on
> the ground and no amount of ranking manufactures them. If your retrieval
> fails that way, the graph is not your fix — your chunking is.
>
> So the practical question isn't "is graph RAG better." It's "which of these
> shapes is my question" — and your pipeline can answer that automatically,
> with one COUNT query, before spending anything. That's section 9.

---

### Timing

| slide | time | cumulative |
|---|---|---|
| 8.1 measure it yourself | 0:45 | 0:45 |
| 8.2 the table + controls | 1:15 | 2:00 |
| 8.3 maybe you don't need this | 1:00 | 3:00 |
| 8.4 the three signals → §9 | 1:00 | 4:00 |
| **total** | | **4:00** |

**On budget, but 8.4 is now dense** — it carries the three shapes *and* the
metric-vs-reading disagreement. If it runs over in rehearsal, the thing to cut
is the *elaboration* of the disagreement, never its first two sentences: the
audience heard trade-goods and illness called wins twenty minutes ago, and
this section calls them failures. Leaving that unsaid is the one thing here
that would cost real credibility.

---

### Assets still needed

*(This section had no assets list — review finding R14.)*

- [ ] **The benchmark table styled**, with the new "what you watched" column —
      it is what makes the table readable without narration, and it is the fix
      for review finding R3. Highlight `expand` (the demo) and `hybrid` (the
      production config); set the `paths` asterisk small but legible
- [ ] **The `expand` vs `ppr` slide** — two lines, large: the demo is the +1.8
      row, the shortlist reranker is the +0.0 row
- [ ] The controls line as a check-mark slide element, not a table row
- [ ] The 942k-token "your corpus might fit" slide — one number, huge
- [ ] **8.4's three shapes**, each with the receipt beside it (rank 22 /
      c5-vs-c23 / rank 4 → the one passage), and the coverage caveat as a
      visually distinct block so the disagreement reads as deliberate
- [ ] Re-generate `results/benchmark.md` into the appendix/PDF from the
      2026-09-08 Leiden run — the numbers in the repo are current, the deck
      appendix should match


---

## Section 9 — How to implement this

*the router, the tools, and what not to tune · 3 minutes · starts 0:50:10* · source: [`section-09-slides.md`](section-09-slides.md)

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

**Slide (build):** the router is one query. *(Kept as Cypher deliberately —
see §6's no-vendor-syntax constraint: the line is drawn at procedure
signatures, and this is standard pattern-matching that GQL implementers share.
Worth one clause out loud if §9.2's "algorithms, not products" argument is
going to land: **the query is as portable as the algorithm is.**)*

```cypher
MATCH (e {canonicalName: $seed})-[:MENTIONED_IN]->(c)
RETURN count(c)   // ≲15 → walk · ≳40 → filter + cosine · 0 → passage-expand
```

> Section 5 ended with a decision table; here is the curve underneath it.
> Monotonic, no exceptions, and the two cases you watched sit right on it —
> **in this sweep**, the Walla Walla pair lands at rank **16** and the
> Sacagawea–brother pair at **338**.
>
> *(Say "in this sweep" and mean it — review finding R6. §5.13 quoted the Walla
> Walla chief at median rank **10**; that was the blend's median for that
> question. This 16 is the same pair's position in the 38,098-pair decay sweep,
> which measures the pure walk and averages differently. Two measurements, two
> numbers, and the audience heard the first one nine minutes ago — so name the
> measurement, or it reads as a number that drifted.)*
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

*2 minutes · starts 0:53:10 · Q&A from 0:55:10* · source: [`section-10-slides.md`](section-10-slides.md)

> **Editorial constraints for this section:**
> - Two slides. The three take-homes get the spoken time; the further-reading
>   slide gets **zero seconds out loud** — it exists for the PDF and the
>   phones.
> - Each take-home is a callback, not new material. If a sentence here needs
>   explaining, it belongs in an earlier section instead.
> - **Take-home #1 is now the measured 8→47, not the Lewis hypothetical**
>   (review findings R10 and R17). The hypothetical was chosen because it stayed
>   true regardless of which database the demos ran on — but that concern is
>   gone now that §4.6 carries the before/after receipt on stage, and the
>   audience spent nine minutes on Sacagawea's nineteen names and zero on
>   Lewis's. Pay the callback in the currency they were paid in.

---

### 10.1 — Three things (1:30)

**Slide:** all three, together, then a beat on each.

> ### 1 · Build time gates query time.
> Sacagawea was **8 passages** in the raw graph and **47** after resolution.
> Every algorithm tonight walked on those edges. Fix entity resolution first.
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
> Number one is section 4 — and you watched it bite every section after it:
> the walk in §5 seeds on those edges, §6 filed the same man under two
> different themes because he is still two nodes, and §8 measured what it was
> all worth.
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

**Slide:** links, **two QR codes**, no talking.

> | | |
> |---|---|
> | **the repo** ▓▒░ | **rate this session** ▓▒░ |
> | tonight's code and every number in it | `SessionFeedbackQrCode.png` |

> **github.com/smithna/graph-algorithms-rag** — tonight's code, the measurement
> harness, and every number in this deck with the script that produced it.
>
> - NICD, *Reducing hallucinations with GraphRAG* — the 510-question study
>   (paper in this repo; their code: `github.com/NICD-UK/graph-based-rag-qa`)
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
> the repo name said once, and open for questions.
>
> **Two QR codes, side by side, equal weight** — the repo and KCDC's session
> feedback code (`SessionFeedbackQrCode.png`, supplied by the organisers).
> Sharing the slide is the right call: it is up for the whole of Q&A, which is
> exactly when people fill the feedback form, and a separate feedback slide
> would either replace the repo slide or steal seconds from the close. Say
> **one** sentence for it — *"left is the code, right is the feedback form,
> and I'd genuinely like to know what missed"* — then stop talking.

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
- [ ] **QR code pair for 10.2** — repo and `SessionFeedbackQrCode.png`, side
      by side, equal weight, both tested from the back of a room
- [ ] Q&A backup pocket list (one hidden slide of pointers): filter parity
      (5g), the budget-graph replication (5j), the §5.9 metric retraction
      (open decision #3 — off-stage, but the most likely question), the
      `paths` run-to-run spread, Ghoshal caveats — so answers can land on a
      visual if needed. **No Louvain pocket** (Nathan: don't use or teach it)

---

## Appendix A — consolidated assets checklist

Gathered from the per-section "Assets still needed" lists. **§6, §7 and §8 now
have their own lists** (review finding R14 closed), so this appendix is
complete for all eleven sections.

**Standing instruction on diagrams (Nathan, 2026-09-08):** *"I can make these
in arrows.app and export as SVG. No need for you to write the SVG code."* So
every "inline SVG" item below is an **arrows.app export**. Three things bit the
one export already in hand (§4.5), and they will bite every one — fold them
into the export routine:

1. **Add a `viewBox`.** The export ships bare `width`/`height` and will not
   scale in reveal.js.
2. **Widen nodes until captions stop wrapping mid-word** (`Sacagawe|a`,
   `Cameahw|ait` in the §4.5 export).
3. **Check edge-label contrast** — the default `#959aa1` grey against the dark
   deck, on the actual projector.

### Code gates (block a demo)

- [ ] **§0** — vector-only entry point: `demo_pagerank.py --vector-only` or a
      small `scripts/demo_baseline.py` that prints the top-8 with text previews
      and nothing else. *The one code gate in the talk* — still needed even
      though §0.1 is now a screenshot, because the screenshot has to be **of** a
      vector-only run or it spoils §5.
- [x] **§6/§8** — `CommunityConfig.algorithm` defaulted to `louvain`, so §8's
      `community` and `hybrid` rows were benchmarked with the algorithm §6
      tells people to avoid. **Fixed 2026-09-08**: default is `leiden`, and
      `results/benchmark.{md,csv,json}` re-generated. Review finding R2.

### Live demos — two, confirmed

| § | demo | status |
|---|---|---|
| 0.1 | `demo_baseline.py` | **screenshot** (Nathan, R11) |
| 4.6 | `demo_resolution.py` | pre-recorded, on `rawluna` |
| **5.9** | **`demo_pagerank.py`** | **live** — `lewisclark`, `--seeder decomposed` |
| **7.2 + 7.4** | **`demo_paths.py`** | **live**, one terminal session, two queries |
| 6.3 | `demo_communities.py` | captured output (recommended) |

⚠️ **Pre-flight:** run one throwaway path query before walking on stage. First
call ~212 ms, every call after ~23 ms (review finding R5).

### Diagrams (arrows.app exports)

- [ ] **§0.3** — the bio-as-graph, ported from last year's deck. **Neo4j
      tenure 5 → 6 years; fix the `PREIVIOUS_JOB` typo.**
- [ ] **§1.1** — the corpus diagram: real labels, real relationship types.
      Establishes the visual language reused in §4–§7.
- [ ] **§2.1** — architecture: one database boundary as one box; "one
      retrieval step" is the caption that matters
- [x] **§4.5** — **done**: `sacagawea appears with indian woman.svg`, Nathan's
      export. Needs the three export fixes above.
- [ ] **§4.5** — OVERLAP two-circle diagram, real numbers
- [ ] **§4.8** — WCC "three pairs → one entity" diagram
- [ ] **§4.8** — bridge-node chain (Sacagawea → Charbonneau → Drouillard)
- [ ] **§5.3** — **the mass-distribution animation**, five fragment states of
      one export. The only diagram in the talk that has to move, and step 3
      (passages lighting up that never mention the seed) is the beat.
- [ ] **§5.6** — "concentrate at the entity level, dissipate at the passage
      level": one hub, many arrows in, the same many arrows out, thin
- [ ] **§6.2** — **one WCC component, 47 Leiden communities** — Nathan's ask;
      numbers verified (8,139 nodes in one component)
- [ ] **§9.1** — decay curve as a chart, not only a table (five bars or one
      falling line; the table stays in the appendix/PDF)

*(§5.7's bipartite 3-step diagram is dropped — 5.7 is cut, and 5.3's animation
covers the same ground better.)*

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
- [ ] **§0.3** — sponsor slide (`KCDC_2026_Sponsors_Slide.jpg`, full-bleed)
      and the table-of-contents slide
- [ ] **§4.6** — the 8→47 before/after table, the section's payoff number
- [ ] **§6.3** — the §5-vs-§6 projection comparison, and the conductance
      honesty line (five largest 0.37 · other 42 0.25)
- [ ] **§8.2** — the benchmark table with its "what you watched" column, and
      the `expand`-vs-`ppr` two-liner
- [ ] **§5.12** — the buttons passage set large, carrier line as caption; and
      cosine's trade-goods top-8 where "the same inventory, twice" reads
- [ ] **§5.13** — the three-mode whiff table; the delete test as one
      before→after arrow; the rank-4 passage with **Cameahwait** highlighted
- [ ] **§9.1** — the one-query router, three routes annotated on the Cypher
- [ ] **§9.2** — tool table that reads in five seconds, no feature matrix
- [ ] **§9.3** — the rule slide, two lines, γ typeset as the Greek letter
- [ ] **§0.3** — title slide with the sequel line and last year's repo URL
- [ ] **§10.2** — QR codes for the talk repo **and** KCDC session feedback
      (`SessionFeedbackQrCode.png`), side by side

### Recordings and fallbacks

- [ ] **§4.6** — recording of `demo_resolution.py` on `rawluna`
- [ ] **§5.9** — `demo_pagerank.py` recording as backup for the live run
      (`lewisclark`, `--seeder decomposed`, ~215 ms)
- [ ] **§0.1** — **the screenshot itself**, now the primary artifact rather
      than a fallback (R11)
- [ ] **§7** — captured route tables as backup for the live session
- [ ] **§10** — Q&A backup pocket: one hidden slide of pointers (filter parity
      5g, the budget-graph replication 5j, the §5.9 metric retraction, the
      `paths` run-to-run spread, Ghoshal caveats). **No Louvain pocket.**

### Projector / legibility

- [ ] **§0.1** — terminal styled for the projector: font size, and previews
      short enough that rank 1's *"for his Services as an enterpreter"* is
      legible from the back

---

## Appendix B — consolidated open decisions

Every decision the section files still flag as needing Nathan. Ordered by what
blocks the most downstream work.

### Closed 2026-09-08

| # | § | decision | how it landed |
|---|---|---|---|
| 1 | 5 | The section title | ✅ *"Your ranking can't tell people apart"* — *"Title is fine."* §3's row and the outline header now match |
| 2 | 4, 5 | The cut plans | ✅ **applied** — §5's eleven trims (*"I support all these cuts"*) and §4's 4.9 (*"Cut 4.9. Keep 4.3 and 4.7"*). Ledger now +1:55, with two named candidates for the rest |
| 4 | 4 | Which database 4.6 demos against | ✅ `rawluna` — follows from *"Don't use neo4j database for anything"*. The 8→47 receipt pairs `rawluna` with `lewisclark` |
| 5 | 5 | How much of the retraction to tell | ✅ **none of it** — *"Don't tell the retraction story."* Disclosure stays, narrative out, Q&A pocket |
| — | 6, 8 | Louvain vs Leiden | ✅ *"I don't want to use or teach Louvain."* Code default changed, benchmark re-run, three places corrected (R2) |
| — | 6 | Vendor syntax on slides | ✅ *"Don't show Neo4j syntax in the deck if we can help it."* 6.2's Cypher removed; §9.1's COUNT query kept — see the note below |
| — | 0 | Cold open live or captured | ✅ **screenshot** — *"I think demo-baseline could be a screenshot"* (R11), which lands the two-demo budget |
| 8 | 2 | Verify NICD's −31 / −49 | ✅ **verified 2026-09-08 against the PDF** — and every other NICD number with it. All exact; nothing needed correcting. Three additions came out of the check: the coarse-truthfulness row now goes **on screen** (zero-shot is −127, which is where its apparent win collapses), the refusal caveat gains the paper's own numbers (27% vs 65% of questions answered), and §2.4's "models reach for tools that look like their training" is confirmed as the **authors' own** explanation |
| — | 9 | Whether §9.1's router query stays as Cypher | ✅ **stays.** Nathan, 2026-09-08: openCypher and the GQL standard are used by more vendors than Neo4j, so it does not read as vendor syntax. The rule stands for **procedure signatures** — §6.2's `gds.leiden.mutate` is still off the slides |

### Still open

| # | § | decision | blocks |
|---|---|---|---|
| 3 | 0 | **Cold-open question choice.** Defaults to `charbonneau-role`, the same question §5.1 diagnoses — deliberate callback. Changing it now means a new verified run **and** a new screenshot. | §0 slides, §5.1's callback |
| 6 | 5 | **The hand-read judgments in outline finding 5o** are the migrating session's and await Nathan's read. | §5.9's "3 of 11" claim |
| 7 | 9 | **9.3's γ line** — "resolution is a corpus decision, not a tunable" — needs its backing example confirmed. Drafted number-free. | §9.3 |
| 9 | 10 | **Repo URL — and the repo does not exist yet.** Checked 2026-09-08: `graph-algorithms-rag` has **no git remote**; it is a local repo on `main` with no upstream, 6 commits, and the whole talk draft still untracked. The `smithna` account is confirmed (last year's repo is at `github.com/smithna/corps-of-discovery-graph-rag`), so the *assumed* URL is the right shape — but the QR code cannot be generated, and §8.1's "the harness is in the repo" and §10.2's "every number with the script that produced it" are not yet true statements. **Sequence: create the repo under `smithna`, commit (the talk draft, the assets and the NICD PDF are all untracked), push, then generate the QR.** | §10.2, the QR assets, §8.1's claim |
| 10 | 5 | **Whether finding 5f gets stage time** (the decomposed seeder's 10/11 vs 8/11 coverage). Currently a speaker note in 5.9. | §5 budget |
| 11 | 5, 6 | **Whether 5.12 moves to open §6** — the recommended way to close §5's last 0:25. A section-budget trade: §5 → 9:25, §6 → 7:00, total unchanged. | §5 and §6 running order |

**On the "how much room is left" question:** the ledger is at 54:55 against a
53:00 budget, and Q&A is budgeted from 0:53. Decisions 11 and the §0.3
table-of-contents drop are the two cheapest ways back under.

### Already decided — recorded so they don't get relitigated

- **§5 runs entirely on `lewisclark`** (migrated 2026-09-07, finding 5o).
  `neo4j` numbers are kept in the outline as history only.
- **§6 is Leiden only — and now Louvain is out of the code as well**
  (2026-09-08). The subtitle, §8.2's note and `CommunityConfig`'s default all
  corrected; the benchmark re-ran. Louvain gets no slide time and no Q&A
  pocket. *(R2 closed.)*
- **§5.12 is the tags-vs-graph decision rule**; filter parity (5g) gets no
  stage time and is the Q&A pocket behind it.
- **The bridge-decay curve is §9.1's**, not §5's. §5's copy is now a
  **one-line pointer**, not a verbatim duplicate. *(R9 closed.)*
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
| *"What goods did the expedition trade with Native nations?"* | §5.12 | §8.4 (named as a coverage failure, deliberately) |
| *"What do we know about Sacagawea's brother?"* | §5.13 | §7.1–7.2 (the two-step landing), §8.4 (the "connection" shape) |

**The trade-goods and illness rows are where the hand-read and the benchmark
disagree, and §8.4 now says so from the stage** rather than letting the
audience notice it — a win at minute 25, a win at minute 36, and both named as
coverage failures at minute 47. *(R1 closed; the wording is in §8.4.)*

---

## Appendix D — the numbers on screen

Every figure the audience sees, with its section, so a single re-measurement
can be traced to every slide it touches. All `lewisclark` unless noted.

| number | meaning | § |
|---|---|---|
| 69 / 67 / 2-of-8 | Charbonneau passages, outside the window, in the window | 0.2, 5.1 |
| median rank 300 | where Charbonneau's passages sit under cosine | 5.1 |
| 19 nodes / 13 forms / 10 recovered / 9 missed | Sacagawea's surface forms | 4.2, 4.4, 4.6 |
| **8 → 47** (and 85 with the scraper) | resolution's payoff, verified 2026-09-08 | 4.6, 4.9, 10.1 |
| 811 people · 328,455 pairs · ~1,100 proposed | the recall/precision division of labour | 4.7 |
| 0.15→0.36, 0.13→0.33, 35→63, 41,694→45,695 | NICD: precision, recall, truthfulness, tokens — ✅ all verified 2026-09-08 | 2.3 |
| −31 / −49 / **−127** | NICD coarse truthfulness — ✅ verified against the PDF 2026-09-08 | 2.3 |
| 27% vs 65% answered | NICD refusal rates — why vector RAG's −31 looks better | 2.3 |
| zero | times the agent called the path tool, in 510 questions | 2.4, 7.5, 10.1 |
| 825 (28.3%) · 587 · 506 · 458 · 396 · 348 · 297 | the hub table | 5.6 |
| 2.84 → 0.47 / 8 · Lewis 3.2 → 18.1 | the three-choice hub ladder | 5.6 |
| 96% vs 48% | walk mass within 3 steps at d=0.45 vs d=0.85 | **5.3** *(was 5.7, now cut)* |
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
| median conductance 0.27 · 35 of 47 tight · none loose | the whole partition | 6.3 |
| **0.37 (five largest) vs 0.25 (other 42)** | why the slide's five numbers look loose — verified 2026-09-08 | 6.3 |
| **1 WCC component / 47 Leiden communities** | same projection, both algorithms — verified 2026-09-08 | 6.2 |
| 8,139 nodes / 63,836 edges · 7,354 / 44,900 | §6's projection vs §5's | 6.3 |
| 1→4 months · 1→5 communities · 2→0 near-dups | the cap, on the illness window | 6.4 |
| ranks 21 / 44 / 104 | what the freed slots filled with | 6.4 |
| **~212 ms cold / ~23 ms warm** | path query latency — R5 resolved by measurement, 2026-09-08 | 7.2, 7.5, 8.2 |
| 86.3% · +1.8 (32/38 vs 31/38) · 82.1% · 100% controls | the benchmark, re-run on Leiden 2026-09-08 | 8.2 |
| **76.1%, range 69.4–88.9 (n=10 runs)** | `paths` — the one row that is not reproducible | 8.2 |
| 88.1% · 0.049 · 0.050 | `community` / `hybrid` under seeded Leiden — identical across 3 runs | 8.2 |
| 1804-05-17 → **1806-09**-11 · 286 chunks | community 23's span — R12 fixed | 6.3, 6.5 |
| ~942k tokens | the corpus, which fits in one context window | 8.3 |
| rank 64 | Floyd's death, for the illness question, every strategy | 8.3 |
| median 10 *(the blend, that question)* vs 16 *(the 38k sweep)* | Walla Walla chief — two measurements, both labelled (R6) | 5.13, 9.1 |

**Re-measured 2026-09-08, and what moved.** The Louvain→Leiden fix left the
headline recall numbers alone (`community` and `hybrid` are still 88.1%,
+1.8) but changed the per-kind breakdown: connection questions **93.8% →
100%**, thematic **63.9% → 55.6%**, and trade-goods went from 1 of 4 gold
entities to 0 of 4 for both strategies. That last one is the §8.4 disagreement
in raw form — the algorithm this talk teaches scores *worse* on the question
§5.12 celebrates than the algorithm it tells you to avoid did. It is on the
record here because it is exactly the kind of thing that should not be
discovered by someone in the audience re-running the harness.

---

## Appendix E — the nineteen review findings, closed

Every finding from [`talk-full-draft-review.md`](talk-full-draft-review.md).
Nathan annotated four of them directly; the rest were judgment calls, and where
a call needed a fact I measured it rather than picking.

| # | finding | resolution |
|---|---|---|
| **R1** | §8 lists as failures the two questions §5/§6 claim as wins | **Nathan: "Let's think of new examples for 8.4."** New examples — all three now things the audience actually watched — plus §8.4 **names the disagreement out loud** instead of letting the room find it. §5/§6 judged by reading, §8 by counting entities; both stated, neither called the winner. |
| **R2** | §6 says Leiden-only; subtitle and §8's notes still say Louvain | **Nathan: "I don't want to use or teach Louvain."** All three places fixed — *and* the one that mattered: `CommunityConfig.algorithm` **defaulted to `louvain`**, so §8 had benchmarked the wrong algorithm. Default → `leiden`, benchmark **re-run**, table and note rewritten. |
| **R3** | §8's strategy names never mapped to §5/§6's demos | Verified in code: `demo_pagerank.py` calls `pagerank.expand`, so **§5.9's demo is the +1.8 row**, not the +0.0 one. §8.2 gains a "what you watched" column and a slide making the `expand`/`ppr` distinction explicit — the shortlist reranker being the zero is a genuinely useful finding. |
| **R4** | §6.3 credits §4 with a merge §5.6 says never happened | Measured: c23 holds `GEORGE DROUILLARD` (84 passages), c5 holds `DREWYER` (297). The note was backwards — it is not evidence the merge worked, it is evidence the split **costs you twice**. Rewritten as that, and the table row now shows both. |
| **R5** | Path latency ~220 ms (§7) vs 23 ms (§8.2) | Measured: **~212 ms cold, ~23 ms warm**, reproduced across fresh processes. §7 quoted a cold start, §8 the steady state. Both labelled, and it produced a rehearsal instruction: warm the projection first. |
| **R6** | Walla Walla chief at rank 10 and rank 16 | Two different measurements. §9.1 now says "in this sweep"; §5.13 keeps its median-10 for that question. |
| **R7** | §6.3's conductance slide argues against itself | **Nathan: "Say out loud that the big ones are loose."** Done, with the receipt: five largest median **0.37**, other 42 median **0.25**, all 47 median 0.27. |
| **R8** | §8.4's Ordway example appears nowhere in the talk | Removed with R1's rewrite. (Ordway *is* real — a defining entity of c23 — but he is never on stage, and a callback to something unseen is worse than no callback.) |
| **R9** | §5's parked routing block duplicates §9.1 verbatim | Replaced with a one-line pointer. |
| **R10** | Sacagawea is 8 chunks in §4 and 85 in §5 | Measured, and the review's suggested framing was **wrong**: 8 → **47** is resolution's work; the other 38 come from the scraped page. Added to §4.6 as 8→47 with the 85 explained, and it is now take-home #1. Also found: the 48 shard passages **do not overlap at all**. |
| **R11** | Four live demos against a stated budget of two | **Nathan: "I think demo-baseline could be a screenshot."** Applied. With §7's two queries counted as one terminal session, the live count is **two** — and the riskiest demo in the deck is retired. |
| **R12** | Community 23's span ends 1806-09 in §6.3, 1806-08 in §6.5 | Measured: **1804-05-17 → 1806-09-11**. §6.5 was wrong; fixed. |
| **R13** | §4.9 trails `cooccurrence` as a win; §8.2 shows it as the worst | Dissolved — **4.9 is cut** (Nathan). Noted in §4.9's cut rationale so the reason survives. |
| **R14** | §6, §7, §8 have no "Assets still needed" lists | Written, and folded into Appendix A. All eleven sections now have one. |
| **R15** | The outline's own §5 header is stale | Fixed in `talk-outline.md` — title decided, so the header follows. |
| **R16** | DREWYER is 297 in §5.6 and 265 in outline finding 5k | Measured on `lewisclark`: **297**. The slide was right; finding 5k's 265 was a pre-migration number. Corrected in the outline, since it is Q&A material Nathan may say out loud. |
| **R17** | §10's take-home #1 swaps §4's example | Folded into R10 — take-home #1 is now the measured 8→47, which is both a stronger callback and in the currency the audience was paid in. |
| **R18** | "Called zero times" is told three times | §7.5's telling compressed to a clause, with a note not to re-inflate it. §2.4 and §10.1 keep theirs. |
| **R19** | Start times hold only if the cuts land | The cuts landed. Ledger recomputed (**54:55**, +1:55), start times updated throughout, and a **second timekeeping checkpoint** added at §6.1. |

**One thing the review did not catch**, found while re-running its numbers:
**§8's `paths` row is not reproducible.** Ten runs spread 69.4–88.9% (mean
76.1%). The old table quoted 69.4% — one draw, and the lowest — as the value.
The cause is in the code's own comment: there are more tied 3-hop routes than
the query over-requests, so the tail is sampled. §8.2 now reports mean and
range and says why.


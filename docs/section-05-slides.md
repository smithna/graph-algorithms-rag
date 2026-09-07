# Section 5 — "Your ranking can't combine evidence"
### multi-seed personalized PageRank · 10 minutes · starts 0:23

> # ⛔ DO NOT BUILD SLIDES FROM THIS YET
>
> **Three faults found after drafting, on verification against live data.**
> The structure and the arc are worth keeping; several load-bearing numbers and
> the demo case are not. Nothing here should reach reveal.js until 1 and 2 are
> settled.
>
> **1. The demo case (5.1, 5.10) is a false positive.** The single passage
> naming both `CHARLES FLOYD` and `MISSOURI RIVER` — the one cosine ranks 415
> and structure promotes to 16 — is from **1804-06-08**, ten weeks *before*
> Floyd died on 1804-08-20. It is a routine log about passing the Mine River in
> which Clark takes "Sjt. Floyd" on a four-mile walk. It has nothing to do with
> his death. Meanwhile cosine's top three are 1804-08-20 *"Sergeant Floyd much
> weaker and no better"*, 1804-08-20, and 1804-08-19. **Cosine answers this
> question correctly and the structural promotion is noise.** I built the demo
> narrative on a co-mention count without reading the passage — the exact error
> the outline's own caveat warns about.
>
> **2. The conjunction metric is hub-contaminated in half the bank.** "Mentions
> ≥2 gold entities" collapses to "mentions both captains" whenever the gold set
> contains `MERIWETHER LEWIS` (377 chunks) or `WILLIAM CLARK` (291):
>
> | question | conjunction passages | qualify via hubs only |
> |---|---|---|
> | grizzly-encounters | 24 | **24 (100%)** |
> | pacific-arrival | 16 | 14 (88%) |
> | food-sources | 162 | **141 (87%)** |
> | great-falls-portage | 46 | 37 (80%) |
> | illness-and-injury | 16 | 12 (75%) |
> | shoshone-horses | 86 | 56 (65%) |
> | sacagawea-interpreting | 26 | 0 |
> | charbonneau-role | 13 | 0 |
> | fort-clatsop-winter | 9 | 0 |
> | trade-goods | 8 | 0 |
> | keelboat-return | 13 | 0 |
> | before-floyd-death | 1 | 0 |
>
> Every pooled figure in this draft (median 527 → 232, top-8 13 → 22) mixes
> both halves, so it is substantially measuring "does this passage name Lewis
> and Clark". Visible in the promoted passages: `illness-and-injury` promotes a
> passage about **guard-duty exemptions**. The fix is to require at least one
> low-df gold entity and re-run every sweep; six questions survive that filter.
>
> **3. The hub-trap numbers (5.7) describe a graph this section does not use.**
> `4.53/8 → 0.60/8` was measured on `lc-retrieval` at damping 0.85. On the
> shipped configuration the trap is far milder. Measured matrix:
>
> | graph | damping | edges | entity top-8 overlap | Lewis mean rank |
> |---|---|---|---|---|
> | lc-retrieval | 0.85 | unweighted | **4.47/8** | **2.5** |
> | lc-retrieval | 0.85 | IDF | 0.60/8 | 8.3 |
> | lc-retrieval | 0.45 | unweighted | 1.07/8 | 9.8 |
> | lc-retrieval | 0.45 | IDF | 0.13/8 | 17.2 |
> | lc-mentions | 0.85 | unweighted | 1.67/8 | 7.8 |
> | lc-mentions | 0.85 | IDF | 0.13/8 | 18.2 |
> | lc-mentions | 0.45 | unweighted | 0.47/8 | 14.7 |
> | **lc-mentions (shipped)** | **0.45** | **IDF** | **0.07/8** | **21.5** |
>
> This is *better* material than the draft has — all three design choices
> independently defuse the trap, and the naive configuration is the one
> everybody writes first. But 5.7 must be rewritten to say so, and its
> "Lewis is the top entity for the prairie-dog, Floyd and Great Falls
> questions" example is wrong on the shipped config (and wrong for Floyd on any
> config — `CHARLES FLOYD` outranks him there).
>
> **Also wrong, minor:** 5.5's seed list shows `INTERPRETERS WIFE`; at
> `entity_seed_k=3` the third seed is `CAPTURE OF SACAGAWEA`. And 5.1's date
> list was written from memory, not from the run.

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
> **Editorial constraints agreed for this section:**
> - **Numbers *are* allowed on screen here** — and that does not contradict
>   section 4. Section 4's numbers needed the gold set to mean anything. These
>   are measurements of the algorithm's own *behaviour*: cross-question overlap,
>   hub mass, a damping sweep, a blend sweep, latency. Exact, reproducible on
>   stage, and carrying no claim about whether a retrieved passage is correct.
> - **No accuracy claims.** "Cosine does not retrieve conjunction" is
>   demonstrable. "The blended results are better answers" is not — that waits
>   for section 8 and its gold set. Never say recall in this section.
> - **The Floyd passage is the spine.** Everything else hangs off it.
> - **Two of this section's earlier claims were retracted on measurement.** The
>   slides state what is true now; the history lives in the outline's *Section 5
>   findings*. Only one retraction earns stage time, as an optional aside (5.11).

---

## 5.1 — The failure (1:00)

**Slide:** the question, and what came back.

> ### "What was happening in the days before Sergeant Floyd died?"

**Slide (build):** the vector top-8, as a list of dates.

```
Aug 20 1804 · Aug 20 1804 · Aug 26 1804 · Aug 26 1804
Jul 27 1806 · May 27 1806 · Apr 20 1805 · Jun 30 1805
```

**Every passage is about a day. None of them is about the question.**

> Two of these are the right days and they came back for the wrong reason —
> they contain the word "Floyd". The rest are days that *sound* like a journal
> entry about a sick man. 1806 is two years too late.
>
> Nothing here is a bad embedding. This is what cosine similarity is for and it
> did it correctly.

---

## 5.2 — Name the actual defect (1:00)

**Slide:** one sentence.

> ## Cosine scores each passage against the question, alone.
> ## It has no way to represent **conjunction.**

> The answer to that question lives in a passage that mentions Floyd **and** the
> Missouri River **and** a date in August 1804. But a passage that answers by
> *combining* things does not read like the question. It reads like a day's log.
>
> There is exactly one passage in this corpus that names both Charles Floyd and
> the Missouri River.

**Slide:** the number, large.

> # 415
> ### of 2,913 — where cosine ranks it

> No candidate window short enough to be worth having contains rank 415.
>
> And it is not one unlucky question. Across the benchmark bank, passages
> carrying two or more of a question's entities sit at a **median cosine rank of
> 527**, and **five of twelve** questions have *none* of them in the top-8.

**Say the caveat, once, and mean it:**

> I am counting passages that mention two or more of the question's entities.
> That is a proxy for relevance, not a ground truth. It shows what cosine
> *doesn't rank* — it does not prove those passages are the right answers. That
> claim needs a gold set and it comes in section 8.

---

## 5.3 — PageRank in 60 seconds (1:00)

**Slide:** the two questions.

> **PageRank:** what is important in this graph?
> **Personalized PageRank:** what is important *relative to these nodes?*

> Plain PageRank is the random surfer — restart anywhere, see where you end up.
> One number per node, the same for every question you will ever ask.

**Slide:** the honest aside. Worth 15 seconds and it buys the room.

> ### On an undirected graph, plain PageRank is a fancy degree count.

> The stationary distribution of an undirected random walk is *exactly*
> proportional to degree. PageRank adds teleport, which shrinks it toward
> uniform. So if your graph is undirected, you have computed `count()` the
> expensive way.
>
> I reached for it in this project as a prominence prior for entity linking, and
> a mention count was better. Say so; it costs nothing and the room trusts the
> next claim more.

**Slide:** the pivot.

> ## The interesting knob is not the algorithm.
> ## It's **where the walk starts.**

---

## 5.4 — Personalized PageRank, as a similarity (0:45)

**Slide:**

> ### PPR measures structural proximity to a **set** of nodes —
> ### aggregated over *every* path, not the shortest one.

Two consequences worth naming:

- **corroboration beats a single strong match** — many mediocre paths outrank
  one good one, which cosine cannot express because it never sees the set
- **it decays smoothly** — damping is a tunable horizon, where "one hop away"
  is just the cutoff that was easy to write in Cypher

> This is the complement to vector search, and that is the whole architectural
> point: cosine asks *what sounds like the question*, PPR asks *what connects to
> what I already found.*

---

## 5.5 — Seed everything. Don't pick one. (1:15)

**Slide:** the ambiguity problem, as everyone actually meets it.

> Question mentions a tree. Your graph has four `POPULUS` species.
> **Which node do you seed?**

**Slide:** the answer.

> ## Wrong question. Seed all four.

> The moment you take an argmax over entity candidates you have built a
> single point of failure into retrieval, and when it picks wrong it fails
> silently. Seed all the plausible candidates instead and let the structure
> decide which neighbourhood is coherent.

**Slide — the live receipt.** The entity seeds this pipeline picks for a
Sacagawea question, chosen from the question alone:

```
SACAGAWEA        (NativeNation)      <- a mislabelled duplicate
SACAGAWEA        (Person)            <- the real one
INTERPRETERS WIFE (Person)
```

> It seeds **both** Sacagawea nodes. It does not know or care which is real, and
> the result is fine.
>
> **This is section 4's callback, made visible.** Argmax linking fails hard when
> resolution is wrong. Proportional seeding degrades gracefully. You do not have
> to fix your entities before this works — you just do better when you have.

**Slide:** and the measured part, because the obvious refinement is a trap.

| seeds | conjunction passages in top-8 |
|---|---|
| 1 | 14 |
| **2** | **23** |
| 3 | 22 |
| 8 | 23 |

> One seed to two is **+64%**. After that it is flat.
>
> Now the part I got wrong. I assumed the win was in *weighting* the seeds by
> how well each matched the question. I built four weighting schemes, including
> one that collapses to a single effective seed and one with a 13× spread.
>
> **All four score the same.** Every seed for a question is semantically close
> to the question, so they sit in overlapping neighbourhoods and their PPR
> vectors are nearly parallel — reweighting parallel vectors barely rotates the
> sum.
>
> **You don't need to pick the right entity, and you don't need to weight them
> cleverly. You need to stop choosing exactly one.**

---

## 5.6 — The graph you walk on is a decision (0:45)

**Slide:** two projections, side by side.

| | `lc-retrieval` | `lc-mentions` |
|---|---|---|
| relationships | MENTIONS, NEXT_CHUNK, RELATED | **MENTIONS only** |
| direction | undirected | undirected |

**Slide:** why the second one drops two thirds of the graph.

> `MENTIONED_IN` is the only relationship here whose direction is *honestly*
> symmetric — "entity appears in passage" is co-membership.
>
> The extracted entity-to-entity edges are not. `MET` and `MARRIED_TO` are
> symmetric. `MEMBER_OF` and `TRIBUTARY_OF` flow importance toward the
> container. `SHOT` carries no importance semantics at all. PageRank's model
> needs an outbound edge to mean **one consistent thing**, and that graph has no
> such thing — for the symmetric types the direction is partly an artifact of
> which entity the extractor happened to name first.
>
> And `NEXT_CHUNK` is a chain, so it leaks walk mass into passages that are
> merely *adjacent in time.*

**The line:**

> ## A projection is not neutral infrastructure.
> ## It encodes what you're optimising for.

---

## 5.7 — The hub trap (1:30)

**Slide:** top entities by how many passages mention them.

```
589  ODOCOILEUS VIRGINIANUS   (white-tailed deer)
439  CERVUS CANADENSIS        (elk)
377  MERIWETHER LEWIS
330  BISON BISON
307  MISSOURI RIVER
291  WILLIAM CLARK
265  DREWYER
```

> **The deer outranks both captains.** This corpus is a daily record of what
> they shot and ate. Whatever you assumed your hub was, check.
>
> And look at row seven — `DREWYER`, 265 passages. `GEORGE DROUILLARD` is a
> **different node** in this graph. Section 4's unresolved entities, on screen,
> for free.

**Slide:** what the hubs do to the walk. Same six questions, unweighted edges.

```
prairie dog question   ->  top entity: MERIWETHER LEWIS
Floyd question         ->  top entity: MERIWETHER LEWIS
Great Falls question   ->  top entity: MERIWETHER LEWIS
```

> The walk decides every question is about Lewis, Clark, Drouillard and deer.
> Across six different questions the top-8 entities overlap **4.53 of 8**.

**Slide:** the one-line fix.

```cypher
log(1.0 + toFloat($totalChunks) / df)   AS weight
```

| | naive | IDF-weighted |
|---|---|---|
| entity top-8 overlap across questions | **4.53 / 8** | **0.60 / 8** |
| PPR mass on the ten biggest hubs | 12.6% | 6.9% |

> IDF-weighted, the top entities become `EQUUS CABALLUS` for the horse question
> and `CYNOMYS LUDOVICIANUS` for the prairie dog. The walk starts answering the
> question it was asked.

**Slide — the mechanism, and it is the part that transfers.**

> ## Hubs **concentrate** at the entity level and **dissipate** at the passage level.

> A hub receives mass from all 589 passages that mention it — then sprays it
> back across all 589, so each gets almost nothing.
>
> Which is why my passage ranking never looked broken while the entity ranking
> was garbage. If you consume the **entity set** — graph expansion, subgraph
> extraction, community seeding — this bites you hard. If you only read passages
> off the end, you may never notice.

**Optional, 10 seconds, if time allows:** the second fix over-corrects.

> Normalising by global PageRank ("lift") drives cross-question overlap to
> *zero* — by dragging the median mention-count of top entities from 23 down to
> **2**. You have traded hubs for one-off noise. Two fixes, one of which goes
> too far, is more useful than two that both just work.

---

## 5.8 — Keep the walk short (0:45)

**Slide:** damping is a horizon, not a magic number.

> ### share of walk mass within *k* steps = `1 − d^(k+1)`

| damping | mass within 3 steps | median rank of conjunction passages |
|---|---|---|
| **0.35** | 98% | **314** |
| 0.55 | 91% | 328 |
| 0.75 | 68% | 350 |
| **0.85** | 48% | **380** |

> `0.85` is the default in every PageRank tutorial including the one I wrote,
> and it is the **worst** of six values here. It puts less than half the walk
> mass within three steps.
>
> Three steps is what you want on a bipartite graph: from an entity seed, step 1
> is the passages that mention it, step 3 is the passages of its co-mentioned
> entities. That is the neighbourhood. Past that you are reading the whole
> corpus at low volume.

---

## 5.9 — The blend (1:15) · abstract takeaway #2

**Slide:** the credibility move, first.

> # alpha = 1.0
> ### reproduces the vector baseline, byte for byte. 6 questions, 6 identical orderings.

> Before I show you a knob, I want you to trust that it is a real knob and that
> I haven't swapped the baseline out underneath it.

**Slide:** the sweep.

| cosine / structure | conjunction passages in top-8 | median rank |
|---|---|---|
| **1.0 / 0.0** | **13** | **527** |
| 0.8 / 0.2 | 19 | 386 |
| 0.6 / 0.4 | 22 | 314 |
| 0.4 / 0.6 | 22 | 264 |
| 0.2 / 0.8 | 22 | 232 |
| 0.0 / 1.0 | 20 | 250 |

> **Cosine alone is the worst row in the table.** And then a broad plateau —
> anything from 0.9 to 0.1 beats it, and everything in the middle is within
> noise of everything else in the middle.
>
> That is the useful finding, so resist quoting an optimum: **the knob is
> forgiving.** Pick something in the middle. On thirteen questions, the
> difference between 22 and 23 is not a difference.

**Slide:** and where to combine them, which matters more than the ratio.

> ### Two places to blend cosine and structure:
> ### in the **seed weights**, or in the **final score**.

> Seeding is the better one. Weight the restart distribution by semantic match
> and structure operates *on* a semantically-informed prior. A post-hoc linear
> blend has the two signals fighting after the fact.

---

## 5.10 — The payoff (1:15) · LIVE DEMO

**Run:** `demo_pagerank.py` — the default question is the Floyd case.

**Slide:** the seeds it chose, from the question alone.

```
DEATH OF CHARLES FLOYD      (Event)
CHARLES FLOYD               (Person)
BAD COLD OF CHARLES FLOYD   (Event)
```

> Note that two of the three are `Event` nodes. Nobody designed that; the
> extractor made event entities and the semantic match found them.

**Slide:** the passage, moving.

```
                             cosine rank
cosine only                      415
+ structure  (0.6 / 0.4)          68
+ structure  (pure)               16
```

> **Show both numbers, and say why.** At the shipped blend it goes to 68 — good,
> not spectacular. Push the slider to pure structure and it lands at 16.
>
> This is the one passage in the corpus where cosine's opinion is pure cost, so
> cosine's weight is what holds it down. That is the honest way to introduce a
> blend: not a free lunch, a trade you are choosing.

**Slide:** and the contrast that makes the architecture point.

> ### The obvious design — rerank the vector top-50 — cannot do this.
> ### Its ceiling is "what sits in positions 9 through 50."

> I built that first. It moves one passage in eight, and on the benchmark's own
> recall metric it scores **exactly zero** improvement over plain cosine.
> Rank 415 was never reachable. **Score the whole corpus.**

---

## 5.11 — What it costs (1:00)

**Slide:**

| | |
|---|---|
| project the graph | **94 ms**, once |
| plain cosine top-8 | **4 ms** |
| this, on a fresh question | **~196 ms** |

> Two PPR calls, one per structural signal, whatever the seed count. Projection
> is the amortised part and that is the standard claim — but the per-query claim
> everyone makes, *"PPR against a projected graph is milliseconds"*, is only true
> of **one** call.

**Slide:** the API detail that made it 3× faster.

```
sourceNodes: [[nodeId1, bias1], [nodeId2, bias2], …]
```

> `sourceNodes` takes the whole seed set in one call — **with per-node bias.**
> One call with eight sources is 56 ms; eight separate calls are 441 ms, because
> the cost is per-call overhead, not source count.
>
> I built it one call per seed, because I assumed weighted seeds needed it. They
> don't. I designed around a limitation the parameter list doesn't have, then
> measured a trade-off that doesn't exist.

**The line, and it is the transferable one:**

> ## Read the signature before you design around it.

**Slide:** the framing that matters.

> ### ~50× plain vector — and it doesn't matter.
> The generation call you're about to make dwarfs 200 ms.

---

## 5.12 — Take home (0:30)

> ## Vector search nominates. The graph decides.
> ### And it can only decide about passages you let it see.

> Three things to take away:
>
> **One.** Cosine ranks what sounds like the question. Graph structure ranks
> what connects to what you found. Different questions, and you need both.
>
> **Two.** Don't argmax your entities. Seed all the candidates.
>
> **Three.** Whatever you weight your edges by is a claim about what matters.
> Make it on purpose.

*(Hands to section 6: "and now every one of those eight passages is about the
same afternoon.")*

---

## Timing

| slide | min |
|---|---|
| 5.1 the failure | 1:00 |
| 5.2 name the defect | 1:00 |
| 5.3 PageRank in 60s | 1:00 |
| 5.4 PPR as a similarity | 0:45 |
| 5.5 seed everything | 1:15 |
| 5.6 the projection is a decision | 0:45 |
| 5.7 the hub trap | 1:30 |
| 5.8 keep the walk short | 0:45 |
| 5.9 the blend | 1:15 |
| 5.10 the payoff (demo) | 1:15 |
| 5.11 what it costs | 1:00 |
| 5.12 take home | 0:30 |
| **total** | **11:55** |

⚠️ **Over budget by 1:55.** The section is allotted 10:00. Cut candidates, in
order of preference:

1. **5.4 entirely (−0:45)** — it is theory the demo demonstrates anyway; fold
   its one useful line ("cosine asks what sounds like it, PPR asks what connects
   to it") into 5.3's pivot slide
2. **5.7's lift aside (−0:10)** and **5.3's degree-count aside (−0:15)** —
   both delightful, both optional
3. **5.6 (−0:45)** — compress to the single "a projection is not neutral
   infrastructure" slide, drop the relationship-semantics detail
4. **5.11's sourceNodes story (−0:25)** — keep the cost table, drop the
   retraction

Cutting 1 and 2 lands at 10:45. Cutting 1, 2 and 3 lands at 10:00 exactly.

**Do not cut 5.1, 5.2, 5.5, 5.7's hub table, or 5.10.** Those are the section.

---

## Assets still needed

- [ ] Hub table as a styled slide with the deer/captains contrast visible at a
      glance (source: `demo_pagerank.py --hubs`)
- [ ] The "hubs concentrate at the entity level, dissipate at the passage level"
      diagram as inline SVG — one hub, 589 arrows in, 589 arrows out, thin
- [ ] Bipartite 3-step diagram for 5.8: entity → passages → co-mentioned
      entities → their passages
- [ ] Screen recording of `demo_pagerank.py` for 5.10 — outline says only two
      demos should be live; **this should be one of them** (it is the section's
      payoff and it is fast)
- [ ] `--conjunction` table as a slide if 5.2 needs more than the single 415

## Open decisions

1. **The section title.** `"Your ranking can't combine evidence"` replaces
   `"Your ranking is wrong"`. The old title promises an improvement this corpus
   does not deliver at the passage level — the reranker moves one slot in eight.
   Needs Nathan's sign-off.
2. **Which database.** Every number in this draft is measured on `neo4j`. The
   outline's section 4 findings still record `lewisclark` as the intended
   replacement demo graph, and it descends from a different extraction with 39%
   more mention edges. **If the demo graph changes, every table here is
   re-measured.** Settle before building slides in reveal.js.
3. **5.10's blend value.** The demo shows 415 → 68 → 16 across the slider. If
   that is one number too many for the stage, show 415 → 16 at pure structure
   and mention the shipped default verbally.

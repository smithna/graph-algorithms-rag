# Section 5 — "Your ranking can't tell people apart"
### entity-seeded personalized PageRank · 10 minutes · starts 0:23

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
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

---

## 5.1 — The failure (1:15)

**Slide:** the question.

> ### "What was Toussaint Charbonneau's role on the expedition?"

**Slide (build):** what vector search returns, with the names in each passage.

```
1.  Chabono                         <- him
2.  Duriaur                         <- a Sioux go-between
3.  (nobody)                        <- the party reaches St. Charles
4.  Dourion                         <- the Sioux interpreter
5.  Charbono                        <- him
6.  Durion, Gravelin                <- Sioux and Ricara interpreters
7.  (nobody)                        <- a Minetarree chief pays a visit
8.  Gravline                        <- the barge pilot
```

**Two of eight are about the man you asked about.**

> Four slots went to *other* French-speaking go-betweens on the same expedition.
> Two went to diplomatic scenes with no interpreter in them at all.
>
> And this is not a near miss. Sixty-two passages in this corpus mention
> Charbonneau. **Sixty of them are outside this window.**

**Slide:** the number.

| | passages | median rank | in top-8 |
|---|---|---|---|
| mention **Charbonneau** | 62 | **296** | **2** |
| interpreter vocabulary, not him | 108 | 578 | 2 |

> Nothing here is a bad embedding. Every passage it returned is about
> interpreting on the Lewis and Clark expedition. It answered the question I
> asked. It just answered it about the wrong person.

---

## 5.2 — Name it (1:00)

**Slide:**

> ## Co-typed entity substitution
> ### It answers *"an interpreter."* You asked about *"this interpreter."*

**Slide:** why, in one line of arithmetic.

> ### A passage embedding is an average over ~300 words.

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

## 5.3 — PageRank in 60 seconds (1:00)

**Slide:** the two questions.

> **PageRank:** what is important in this graph?
> **Personalized PageRank:** what is important *relative to these nodes?*

**Slide:** the honest aside. Fifteen seconds, and it buys the room.

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

## 5.4 — Seed the entity. Seed all of them. (1:30)

**Slide:** the fix, in one sentence.

> ### `MENTIONED_IN` is a **discrete** edge.
> ### Either extraction attached the entity, or it didn't.

> No averaging. Identity is binary. That is the hard constraint cosine can only
> express softly — and it is the whole trick.
>
> Median 60 words per entity in a 325-word passage. **The entity is a pointer.
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

**Slide — the live receipt.** Seeds chosen for a Sacagawea question, from the
question alone:

```
SACAGAWEA   (NativeNation)   <- a mislabelled duplicate
SACAGAWEA   (Person)         <- the real one
CAPTURE OF SACAGAWEA (Event)
```

> It seeds **both** Sacagawea nodes. It does not know which is real and does not
> need to. Take an argmax over entity candidates and you have built a single
> point of failure into retrieval that fails *silently* when it picks wrong.
>
> **This is section 4's callback.** It seeds both Sacagawea nodes and the result
> is fine — and even if you sharpen down to *one* seed, it picks the mislabelled
> duplicate and still works, because both nodes land in the same neighbourhood.
> You do not have to fix your entities before this works. You just do better
> when you have.

**Slide — and the passage that proves the mechanism.** Cosine rank **22**,
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

## 5.5 — The graph you walk on is a decision (0:45)

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

## 5.6 — The hub trap (1:15)

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

> **The deer outranks both captains.** A daily record of what they shot and ate.
> Whatever you assumed your hub was — check.
>
> And row seven: `DREWYER`, 265 passages. `GEORGE DROUILLARD` is a **separate
> node**. Section 4's unresolved entities, on screen, for free.

**Slide:** what hubs do to a naive walk — and what three choices do about it.

| graph | walk | edge weights | same top-8 entities across questions |
|---|---|---|---|
| all three types | long (d=0.85) | none | **4.47 / 8** · Lewis ranks **2.5** |
| all three types | long | IDF | 0.60 / 8 |
| all three types | short (d=0.45) | none | 1.07 / 8 |
| **mentions only** | **short** | **IDF** | **0.07 / 8** · Lewis ranks **21.5** |

> Top row is the configuration everyone writes first: all your edges, damping
> 0.85 because that is the number in every tutorial, no weighting because why
> would you weight. Six different questions and the walk returns **four and a
> half of the same eight entities** every time. It has decided every question is
> about Lewis, Clark, Drouillard and deer.
>
> **Three choices, each of which independently defuses it.** Drop the edges
> whose direction is meaningless. Shorten the walk. IDF-weight the mentions:

```cypher
log(1.0 + toFloat($totalChunks) / df)   AS weight
```

**Slide — the mechanism, because this is the part that transfers.**

> ## Hubs **concentrate** at the entity level and **dissipate** at the passage level.

> A hub receives mass from all 589 passages that mention it — then sprays it
> back across all 589, so each gets almost nothing.
>
> Which is why my passage ranking never looked broken while the entity ranking
> was garbage. **If you consume the entity set** — graph expansion, subgraph
> extraction, community seeding — this bites hard. If you only read passages off
> the end, you may never notice it happening.

---

## 5.7 — Keep the walk short (0:30)

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

## 5.8 — The blend, and one honest knob (0:45) · abstract takeaway #2

**Slide:** the credibility move.

> # alpha = 1.0
> ### reproduces the vector baseline byte for byte
> ### 6 questions, 6 identical orderings

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

## 5.9 — The payoff (1:30) · LIVE DEMO

**Run:** `demo_pagerank.py` — default question is `charbonneau-role`.

**Slide:** the seeds it chose from the question alone.

```
TOUSSAINT CHARBONNEAU               (Person)
JEAN BAPTISTE CHARBONNEAU           (Person)
BIRTH OF JEAN BAPTISTE CHARBONNEAU  (Event)
```

**Slide:** the three passages it pulled in, and what each one adds.

```
1805-03-18   "Mr. Tousent Chabono, Enlisted as an Interpreter this evening"
             -> the hiring itself

1804-12-18   "Chabonoe our big belly interpeter"
             -> WHICH language: Hidatsa

1805-08-25   "out of patience with the folly of Charbono who had not
              sufficient sagacity to see the consequencies"
             -> his judgement in the job
```

> The hiring. The language. And the day he sat on the news that the Shoshone
> were leaving with the horses and did not think to mention it.
>
> **None of those three is in the cosine top-8.** Cosine gave me Dorion,
> Gravelin, and the party arriving at St. Charles.

**Say this plainly — it is the section's integrity:**

> I judged these by reading them. Sixteen promoted passages across three
> questions, read in full, one question each: *does this contain something a
> correct answer needs that no cosine passage has?*
>
> **Four of sixteen cleared that bar.** Not a rout. I had a metric that said it
> was much better than that, and the metric was measuring the wrong thing — so I
> read the passages instead. If you take one methodological thing from this talk,
> take that.

---

## 5.10 — Three things it cannot do (1:15)

**Slide:** all three, measured.

> ### 1. It combines evidence — but you don't choose the weights.

> Good news first: additivity **is** a conjunction bonus. Seed `SACAGAWEA` and
> `CHARBONNEAU` — comparable degree — and every one of the nine passages
> mentioning **both** lands in the top-20, median rank **5**, against 51 and 71
> for passages mentioning either alone.
>
> Now seed `SHOSHONE` (192 passages) with `EQUUS CABALLUS` (14). A passage
> mentioning **only the horse** scores 0.0100. One mentioning **both** scores
> 0.0107. A 6.6% bonus for also being about the Shoshone.
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

> *"How did the corps obtain horses from the Shoshone?"* — the passage that
> answers it is Aug 18 1805: *"I soon obtained three very good horses for which I
> gave an uniform coat, a pair of legings, a few handkerchiefs, three knives."*
>
> Here is what the extractor attached to it:

```
SHOSHONE · SHOSHONE COVE · DREWYER · WILLIAM CLARK · JEFFERSON RIVER
UNIFORM COAT · PAIR OF LEGINGS · THREE KNIVES · HANDKERCHIEFS   (all Supply)
```

> **There is no horse.** A passage about buying three horses has no horse in the
> graph. Every traded good is there, and `Supply` nodes have no embedding, so
> nothing can seed them.
>
> The structure that would answer this question was never built. **No ranking
> algorithm fixes that.**

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

## 5.11 — What it costs (0:45)

**Slide:**

| | |
|---|---|
| project the graph | **94 ms**, once |
| plain cosine top-8 | **4 ms** |
| this, on a fresh question | **~196 ms** |

**Slide:** and the one-line fix that got it there.

```
sourceNodes: [[nodeId1, bias1], [nodeId2, bias2], …]
```

> `sourceNodes` takes the whole seed set in one call — **with per-seed bias.**
> One call with eight sources: 56 ms. Eight separate calls: 441 ms. The cost is
> per-call overhead, not source count.
>
> I built it one call per seed, because I assumed weighted seeds required it.
> They don't.

> ## Read the signature before you design around it.

**Slide:**

> ### ~50× plain vector — and it doesn't matter.
> The generation call you're about to make dwarfs 200 ms.

---

## 5.12 — Take home (0:30)

> ## Cosine retrieves the topic. The graph retrieves the entity.

**Slide:** and when to bother.

> ### It earns its place in proportion to how many **same-type entities** your corpus has.

> Forty engineers, and you asked what Chen owns? This is for you.
>
> One CEO, one product, one customer? Save yourself the projection.
>
> *(And five of those forty engineers are named Chen — which is the problem we
> solved in the last section. One company, two different failures.)*

*(Hands to section 6: "and now every passage in that window is about the same
afternoon.")*

---

## Timing

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
| 5.12 take home | 0:30 |
| **total** | **12:00** |

⚠️ **Over budget by 2:00.** Allotted 10:00. Cut candidates, in order, with the
running total — the first four are not enough on their own:

| cut | saves | running |
|---|---|---|
| drop **5.5**, keeping only the "a projection is not neutral infrastructure" line inside 5.4 | 0:45 | 11:15 |
| fold **5.7** into 5.6 as one sentence | 0:30 | 10:45 |
| drop **5.3's** degree-count aside | 0:15 | 10:30 |
| drop **5.11's** `sourceNodes` retraction, keep the cost table | 0:20 | 10:10 |
| compress **5.8** to the `alpha=1.0` slide alone | 0:25 | **9:45** |

All five lands at 9:45 with slack for the live demo overrunning. Four of five
still leaves it 10 seconds over, so **plan on all five** and treat 5.3's aside
and 5.11's retraction as restorable if a rehearsal comes in fast.

**Do not cut 5.1, 5.2, 5.4's Nov-4 passage, 5.9, or 5.10.** Those are the
section. 5.10 especially — it is what makes the whole talk's multi-tool
argument honest, and it is the thing nobody else's PageRank talk will say.

---

## Assets still needed

- [ ] 5.1's tagged top-8 as a slide where the "wrong name" column reads at a
      glance — the names are the punchline, set them large
- [ ] The forty-engineers slide. Text only, big. No diagram.
- [ ] Hub table styled so deer-above-captains lands without explanation
      (source: `demo_pagerank.py --hubs`)
- [ ] "Concentrate at the entity level, dissipate at the passage level" as
      inline SVG — one hub, many arrows in, the same many arrows out, thin
- [ ] Bipartite 3-step diagram for 5.7: entity → passages → co-mentioned
      entities → their passages
- [ ] The Aug-18-1805 entity list for 5.10 with **no horse** visibly absent —
      possibly strike-through a ghosted `EQUUS CABALLUS`
- [ ] `demo_pagerank.py` recording as backup; **this should be one of the two
      live demos** — it is the payoff and it runs in 196 ms

## Open decisions

1. **The title.** *"Your ranking can't tell people apart"* — needs sign-off.
2. **Which database.** Every number here is `neo4j`. The section 4 findings still
   record `lewisclark` as the intended replacement demo graph, built from a
   different extraction with 39% more mention edges. **If the demo graph changes,
   every table here is re-measured** — including the hub table and the
   62/296/2 figures that open the section.
3. **How much of the retraction to tell.** 5.9 currently spends ~20 seconds on
   "my metric was measuring the wrong thing, so I read the passages." I think it
   is the most valuable twenty seconds in the section. It is also the easiest
   thing to cut if a rehearsal runs long, and Nathan may prefer to keep the
   methodology out of a 10-minute slot.

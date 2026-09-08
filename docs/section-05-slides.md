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
> - **Every number in this section is `lewisclark`** (migrated 2026-09-07,
>   outline finding 5o; the old `neo4j` values are kept there as history). The
>   demo runs with `NEO4J_DATABASE=lewisclark` and `--seeder decomposed` —
>   `lewisclark` has no Person vector indexes by design, so the semantic seeder
>   cannot seed people there.

---

## 5.1 — The failure (1:15)

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

## 5.2 — Name it (1:00)

**Slide:**

> ## Co-typed entity substitution
> ### It answers *"an interpreter."* You asked about *"this interpreter."*

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

## 5.9 — The payoff (1:30) · LIVE DEMO

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

## 5.10 — Three things it cannot do (1:15)

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

## 5.11 — What it costs (0:45)

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

## 5.12 — The question that names nothing (1:00) · `lewisclark`

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

## 5.13 — The answer is a name you don't have (1:00) · `lewisclark`

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

## 5.14 — Take home: one number decides (0:30)

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

## PARKED FOR §9 — the routing rule as the implementation beat

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

## Assets still needed

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

## Open decisions

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

# Compile review — cross-section findings

> ## ✅ ALL NINETEEN RESOLVED — 2026-09-08
>
> **This file is now the historical record of the review, not an open list.**
> The resolutions live in **Appendix E of
> [`talk-full-draft.md`](talk-full-draft.md)**, one row per finding, with the
> measurement behind it where one was needed.
>
> **Nathan annotated four findings directly in this file** and those
> annotations drove their resolutions — they are left exactly where he wrote
> them, in the R1, R2, R7 and R11 sections below:
>
> | | Nathan's note | what it drove |
> |---|---|---|
> | **R1** | *"Let's think of new examples for 8.4"* | §8.4's three examples all replaced with things the audience watched — and §8.4 now names the §5/§6-vs-§8 disagreement out loud |
> | **R2** | *"I don't want to use or teach Louvain"* | the three text fixes **plus a code fix**: `CommunityConfig.algorithm` defaulted to `louvain`, so §8 had benchmarked the wrong algorithm. Default → `leiden`, benchmark re-run |
> | **R7** | *"Say out loud that the big ones are loose"* | §6.3, with the receipt: five largest median conductance 0.37, other 42 median 0.25 |
> | **R11** | *"I think demo-baseline could be a screenshot"* | §0.1 is a screenshot; live-demo count is now two |
>
> The other fifteen were judgment calls. Where a call turned on a fact, the
> fact was measured rather than guessed — that is how R4, R5, R10, R12 and R16
> were settled, and **R10's resolution contradicts what this file proposed**:
> "8 → 85" would have credited resolution with 38 passages that came from the
> scraped reference page. The honest number is **8 → 47**.
>
> **One finding this review missed**, surfaced while re-running its numbers:
> §8's `paths` row is **not reproducible** — ten runs spread 69.4–88.9%
> (mean 76.1%), and the table quoted the lowest draw as the value.

---

Companion to [`talk-full-draft.md`](talk-full-draft.md). *(Original preamble,
kept as written: "Nothing listed here has been changed in the compiled
document; it is all reported, not resolved." That is no longer true — see
above.)*

These are the things that only surface when all eleven sections are read at
once — which, under the one-section-per-conversation working agreement, had not
happened before this pass. Ordered by what an attentive audience member is most
likely to catch.

---

## Contradictions on stage

### R1 · §8 lists as failures the two questions §5 and §6 claim as wins

The sharpest problem in the deck.

- **§5.12** — the walk **wins** trade-goods. Buttons-off-coats promoted from
  cosine rank 77, the Twisted Hair gun payment from 112, month coverage 3→7.
  Sold as the section's thematic payoff, hand-read.
- **§6.4** — the cap **repairs** illness-and-injury. 1→4 months, 1→5
  communities, recovers Lewis's gunshot and the Fort Clatsop sick-list. Sold
  as the section's whole reason to exist.
- **§8.4** — *"our two benchmark failures, trade goods and illness, are
  neither — they're coverage, and the graph rightly did nothing for them."*

So §8 names, as the talk's two coverage failures, exactly the two questions §5
and §6 spent four minutes claiming as wins.

Both are defensible — §5/§6 judged by hand-reading passages, §8 measures
answer-entity recall, and §5.9 explicitly warns that a metric said one thing
and reading said another. **But nothing on stage says that.** As drafted the
audience hears a win at minute 31, a win at minute 36, and both called failures
at minute 47. 

Needs one sentence in §8.4 naming the difference — something like *"and the two
the hand-read liked, the metric doesn't; that disagreement is the honest state
of it"* — or §8.4 needs different examples. This is a content decision, not a
merge fix. Let's think of new examples for 8.4

### R2 · §6 says Leiden-only; its own subtitle and §8's notes still say Louvain

The decision (2026-09-07, recorded in both the outline and §6's editorial
constraints) is **Leiden only on stage; Louvain is Q&A backup with no slide
time.** Three places didn't get the memo:

1. **§6's own subtitle** still reads *"community detection: Louvain, Leiden,
   conductance"* — contradicting the constraint four lines below it.
2. **§8.2's speaker note**: *"community and hybrid show a range because
   **Louvain** deals a fresh partition every run — pin your seeds if you need
   repeatable output, **section 6 showed how**."* §6 shows *Leiden* with
   `randomSeed: 42`. The callback describes a section that no longer exists.
3. Underneath both: **§8's `community` and `hybrid` strategies apparently run
   Louvain, while §6 teaches Leiden.** If that's true, the benchmark isn't
   measuring the algorithm the talk taught, and the ±1-entity range in the §8
   table is an artifact of an algorithm the audience was told to avoid. If it
   isn't true, §8's note is simply wrong. Either way it needs settling before
   the scaffold — §3's roadmap row already commits to "Leiden".

   I don't want to use or teach Louvain.

### R3 · §8's strategy names are never mapped to §5's and §6's demos

§8.2 reports seven strategies: `vector`, `ppr (rerank)`, `expand (§5)`,
`community (§6)`, `cooccurrence (§4)`, `paths (§7)`, `hybrid`.

Two of them carry a §5 lineage — `ppr` at **+0.0** and `expand` at **+1.8** —
and the table labels only `expand` as §5. But §5 demos *entity*-seeded PPR
(5.9, `--seeder decomposed`) and separately describes *passage*-seeded
expansion (5.12). Nothing on stage says which row is which.

If §5's flagship live demo is the `ppr` row, then **§8 silently reports the
talk's headline demo as a zero** four minutes after §7 sends the audience there
expecting a verdict. The audience can't tell, which is worse than either answer.
One clause per row in §8.2's notes fixes it.

### R4 · §6.3 credits §4 with a merge that §5.6 says never happened

- **§6.3 note**: *"the corps roster (note Sacagawea and **Drouillard** in c23
  — section 6 rides on section 4's merge)"*
- **§5.6**: *"row seven: `DREWYER`, 297 passages. `GEORGE DROUILLARD` is a
  **separate node**. Section 4's unresolved entities, on screen, for free."*

§5 uses the unmerged Drouillard as a live demonstration that resolution is
incomplete; §6 cites the same entity as proof the merge worked. Also: the c23
row in §6.3's table lists `PRYOR, SHIELDS, SHANNON, GASS, SACAGAWEA` — no
Drouillard visible, so the note points at something not on the slide.

### R5 · Path latency: ~220 ms (§7) vs 23 ms (§8.2)

§7.2 and §7.5 both quote **~220 ms** and use it to argue the demo is safe live
and the router is cheap. §8.2 measures `paths` at **p50 23 ms / p95 23 ms** —
an order of magnitude apart.

Probably different scopes (§7's number likely includes anchor resolution and
receipt fetching; §8's likely times the Yen's call alone). Fine — but they're
both stated flatly as what path retrieval costs, nine minutes apart, and the
listener has no way to reconcile them.

### R6 · The Walla Walla chief comes back at rank 10 and at rank 16

- **§5.13**: *"the blend puts his chunks at median rank **10**"*
- **§9.1** (and §5's parked block): *"the Walla Walla chief, anchor in 3
  passages, came back at rank **16**"*

Again two different measurements — 10 is the blend's median for that question,
16 is that pair's position in the 38k-pair decay sweep. Both use the phrasing
"came back at". Since §9.1 explicitly says *"the two cases you watched sit right
on it,"* it invites the comparison and then shows a different number.

### R7 · §6.3's conductance slide argues against itself

The displayed rows are `0.37 · 0.39 · 0.25 · 0.34 · 0.38`. The stated rule of
thumb is *"≤0.35 is a tight theme you can build on."* **Three of the five
numbers on screen fail it** — and the speaker note then says *"median 0.27, 35
of 47 tight, none loose."*

Both are almost certainly true (the largest communities are the loosest, and
the slide shows the five largest). But the audience sees five numbers, is
handed a threshold, does the arithmetic, and gets the opposite of the claim.
Either show a tight community in the table, or say out loud that the big ones
are the loose ones.

Say out loud that the big ones are loose

---

## Orphans and loose ends

### R8 · §8.4's Ordway example appears nowhere in the talk

§8.4: *"Look back at where the graph earned its keep tonight — **Ordway's duty
orders that cosine ranked at 95: traversal.**"*

Ordway is not in §4, §5, §6 or §7. The sentence asks the audience to recall
something they were never shown. The other two examples in that list
(Drewyer/Drouillard, the brother question) are real callbacks and land.

### R9 · §5's parked routing block duplicates §9.1 verbatim

§5's file ends with a `PARKED FOR §9` block containing the full decay table,
and says the canonical copy is 9.1. §9.1 has the same table and the same
speaker-note paragraph. In the compiled document both appear in full, ~40 lines
apart in reading order.

Left in deliberately — deleting it is an edit, not a merge. But it should
probably become a one-line pointer once §5's cut plan is settled.

### R10 · Sacagawea is 8 chunks in §4 and 85 passages in §5 — and that gap is §4's best unclaimed win

- **§4.2**: *"**8** chunks in which Sacagawea is named"* — the section's most
  quotable number, on a slide by itself.
- **§5.10 / §5.13**: `SACAGAWEA`, **85 passages**, used as a hub-scale anchor.

Both correct — §4.2 counts the unresolved graph, which is its entire point, and
§5 runs post-merge on `lewisclark`. But **nothing on stage connects 8 to 85**,
and a listener who remembers the big number from minute 15 will hear a
contradiction at minute 30.

More to the point: 8→85 *is* the payoff of §4, quantified, and the talk never
states it. §4.10 currently argues build-time-gates-query-time with a
hypothetical. This makes it a receipt. Worth a slide, not just a fix.

### R11 · Four live demos, against a stated budget of two

§4's assets say *"the outline recommends resolution be pre-recorded rather than
live — only two demos should be live."* §5's assets say `demo_pagerank.py`
*"should be one of the two live demos."* But as drafted:

| § | demo | marked |
|---|---|---|
| 0.1 | `demo_baseline.py` | *"a terminal, not a slide"*, live, minute zero |
| 5.9 | `demo_pagerank.py` | **LIVE DEMO** |
| 7.2 | `demo_paths.py --from Sacagawea --to Cameahwait` | **live demo** |
| 7.4 | `demo_paths.py --from Cameahwait --to Hidatsa` | *"safe live"* |


That's four, and §0's is the riskiest of them all — it runs at minute zero with
no warm-up, which §0's own assets list flags. §6.3 also shows
`demo_communities.py` output described as "live output" without saying whether
it runs.

Either the two-demo rule is stale or three sections need to change. It also
changes the rehearsal fallback list.

I think demo-baseline could be a screenshot

### R12 · Community 23's span ends 1806-09 in §6.3 and 1806-08 in §6.5

Chunk count agrees (286). One digit, two slides, four minutes apart.

### R13 · §4.9 trails `cooccurrence` as a win; §8.2 shows it as the worst strategy

§4.9 promises node similarity at query time *"catches passages embeddings
miss"* and *"comes back in section 8 as the `cooccurrence` strategy."* In
§8.2, `cooccurrence` scores **82.1%, −4.2** — the only strategy that loses to
plain vector, by the largest margin in the table. §8 never mentions the promise.

Not strictly a contradiction (it can catch passages embeddings miss *and* score
worse overall), but §4.9 sets up a payoff that §8 refutes without comment.
Convenient: §4.9 is already the #1 cut candidate in §4's own cut plan, and
cutting it removes this problem too.

---

## Structural gaps

### R14 · §6, §7 and §8 have no "Assets still needed" lists

The other eight sections have them. Those three account for two live demos, the
Leiden output table, the route tables, the receipt passages, and the benchmark
table — all of which need styling, and none of which are tracked anywhere.
Appendix A of the compiled doc is therefore complete only for §0–§5, §9, §10.

### R15 · The outline's own §5 header is stale

[`talk-outline.md`](talk-outline.md) line ~4490 still reads *"5. Your ranking
can't **combine evidence** → multi-seed PPR"*. The section file's title is
*"Your ranking can't tell people apart"* → *entity-seeded personalized
PageRank*, and the combine-evidence thesis was measured and retracted. §3's
roadmap row already tracks the new title.

Since the outline is the source of truth, this is the one place the stale title
actively misleads a future session.

### R16 · DREWYER is 297 passages in §5.6 and 265 in outline finding 5k

§5.4's honesty line points at 5k as a **Q&A pocket** — so this is a number
Nathan may say out loud, from a finding whose count disagrees with the slide
he'll be standing next to. Likely a pre-`lewisclark` measurement that survived
the migration. Worth reconciling precisely because it's Q&A material, where
there's no chance to caveat.

---

## Judgment calls, not errors

### R17 · §10's take-home #1 swaps §4's example

§4.10 states it as *"a graph where Sacagawea is nineteen nodes."* §10.1 states
it as *"a graph where `CAPT. LEWIS` and `MERIWETHER LEWIS` are separate
nodes."* §10's editorial note explains the choice — a hypothetical stays true
regardless of which database the demos ran on.

Defensible, but the audience spent nine minutes on Sacagawea's nineteen forms
and zero on Lewis's name variants. The callback would land harder in the
currency they were paid in. (And per R10, "nineteen nodes → 85 passages" is
available and stronger than either.)

### R18 · "Called zero times" is told three times

§2.4 (the hinge, 1:30), §7.5 (the NICD callback, 0:45), §10.1 (take-home #2).
All three are deliberate and each is labelled as a callback. Flagging only so
the repetition is a choice rather than an accident of three separate drafting
sessions — the §7.5 telling is the one that could compress to a clause.

### R19 · Start times hold only if the cuts land

Every section header states a start time from the outline's budget. As drafted,
§4 and §5 push everything after them 5:30 late — §6 would start at 0:38:30 and
Q&A at 0:58:30. §3.1's speaker note already builds in the checkpoint
(*"this slide is minute 13-to-14. Section 4 starts on schedule or the cuts list
comes out"*), which is the right instinct; it just needs a second checkpoint
after §5.

---

## What the compile did *not* touch

- No wording changed, in slides or speaker notes.
- No numbers changed, reconciled, or recomputed.
- No cuts applied — §4's and §5's cut plans are drafted, not executed.
- Duplicated content (R9) left in place.
- Section-level editorial constraints kept in full; they read as review
  material, not scaffold instructions.
- Only mechanical edits: headings demoted one level, the identical
  "draft slide content / speaker notes are blockquotes" preamble lifted to the
  front matter once instead of eleven times, and front matter + appendices
  added.

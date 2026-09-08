# Section 6 — "Your context is redundant"
### community detection: Louvain, Leiden, conductance · 6 minutes · starts 0:33

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
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

## 6.1 — The failure (1:00)

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

## 6.2 — Leiden (1:00)

**Slide:** the one-line definition, against section 4's.

> **WCC** (section 4): *connected at all* — one path suffices.
> **Leiden**: *densely connected relative to chance* — neighborhoods,
> not reachability.

**Slide (build):** one call, and it's repeatable.

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

## 6.3 — The table of contents nobody wrote (0:45)

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

## 6.4 — The fix: cap the window per community (1:45)

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

## 6.5 — What the cap cannot do (1:00)

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

## 6.6 — Hand-off (0:30)

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

## Timing

| slide | time | cumulative |
|---|---|---|
| 6.1 the failure | 1:00 | 1:00 |
| 6.2 Leiden | 1:00 | 2:00 |
| 6.3 table of contents + conductance | 0:45 | 2:45 |
| 6.4 the fix, measured | 1:45 | 4:30 |
| 6.5 the bound | 1:00 | 5:30 |
| 6.6 hand-off | 0:30 | 6:00 |

# Section 4 — "Your entities are a mess"
### node similarity + WCC · 9 minutes · starts 0:14

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
> **Editorial constraints agreed for this section:**
> - **No precision or recall percentages.** The gold set is a hand-built
>   reference, not ground truth. Claims on screen are things the audience can
>   check by eye: named nodes, a drawn chain, counts from a live run.
> - **The Sacagawea example is the spine.** Everything else hangs off it.
> - **No metric comparison table.** One diagram for OVERLAP, one throwaway line
>   about other corpora.

---

## 4.1 — The failure (0:45)

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

## 4.2 — Now make it personal (1:00)

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

## 4.3 — The naive fix, and where it dies (1:15)

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

> # SACAGAWEA → THE SQUAR
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

## 4.4 — How the original solved it (1:00)

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

## 4.5 — You have more information than you think (1:15)

**Slide:** the idea.

> ## Two names that keep appearing alongside the same people, places and dates
> ## are probably the same entity

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

## 4.6 — The payoff (1:30) · LIVE DEMO or recording

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

## 4.7 — What it costs (1:00)

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

## 4.8 — WCC, and what it is actually for (1:30)

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

> I did this to my own graph last night. Sacagawea absorbed Drouillard.
>
> And here is the thing — **the model was never wrong.** Ask it directly:
> *is Sacagawea the same entity as George Drouillard?* No. *As Windsor?* No.
> It gets every direct pair right.
>
> But "his wife", beside Charbonneau, **is** Sacagawea. "The interpreter" **is**
> Charbonneau. And Drouillard **was** the sign-language interpreter. Four
> defensible judgements, not a wrong one among them — and one merged entity that
> is flatly wrong.

**Slide:** the rule.

> ## Closure doesn't just propagate errors. It manufactures them.
> A genuinely ambiguous node is not a wrong answer waiting for a better model.
> It is a **bridge** — and WCC will cross it.

> Two consequences. **One:** adjudicate *before* you close, never after.
> **Two:** be careful what you let into the candidate set — this pipeline has a
> `flag_generic_locations` step because "the river" is useless as a place. It
> has nothing equivalent for people, so "the interpreter" and "his wife" sit in
> the graph as first-class Person nodes, waiting to be bridges.

---

## 4.9 — Same algorithm, query time (0:45)

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

## 4.10 — Take home (0:30)

> ## Fix entity resolution before you tune retrieval.

> Personalized PageRank over a graph where Sacagawea is nineteen nodes will
> confidently rank the wrong passages — and it will look like it is working.
>
> Build time gates query time. That is the whole reason this section comes
> before the next one.

*(Hands directly to section 5.)*

---

## Timing

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

1. **4.9 query time (−0:45)** — it is a trailer for section 8, not load-bearing here
2. **4.3's Jaro-Winkler aside (−0:20)** — delightful, entirely optional
3. **4.7 (−0:30)** — compress to the two-line "recall/precision" slide, drop the table

Cutting 1 and 2 lands at 9:25. Cutting all three lands at 8:55.

**Do not cut 4.2, 4.6 or 4.8.** Those are the section.

---

## Assets still needed

- [ ] OVERLAP two-circle diagram as inline SVG (spec above, real numbers)
- [ ] Bridge-node chain diagram as inline SVG
- [ ] Screenshot of `enrich_sacagawea.py` with `SOURCE_URL` highlighted
- [ ] Recording of `demo_resolution.py` (outline recommends resolution be
      pre-recorded rather than live — only two demos should be live)
- [ ] Decide which database 4.6 demos against — see note below

## Open decision

4.6 says "the graph built **without** the scraper". Today that is `rawluna`,
which is pre-disambiguation, so the *closed cluster* has to come from
`demo_resolution.py --adjudicate` rather than from merged nodes in the graph.
That is fine and arguably better — the audience watches it happen rather than
seeing a result. Confirm before recording.

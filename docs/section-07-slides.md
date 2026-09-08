# Section 7 — "You can't explain the answer"
### path finding: Yen's k-shortest paths, with receipts · 5 minutes · starts 0:39

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
> **Editorial constraints for this section:**
>
> - **Every route and receipt on screen ran live on `lewisclark` and was
>   hand-read** (finding 7a–7g; read-pack `results/paths-lewisclark-readpack.md`,
>   local only). Route order is deterministic — the shipped tie-sort — and
>   ~220 ms per query, so the demo is safe to run live.
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

## 7.1 — The failure (0:45)

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

## 7.2 — Ask the graph HOW (live demo, 1:30)

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
> *citation*, not a similarity score. ~220 milliseconds.
>
> That's the two-step landing: the walk discovered the name, the path query
> explained the connection. Neither can do the other's job.

---

## 7.3 — Why k matters (the honest version, 1:00)

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

## 7.4 — Receipts catch the graph lying (1:00)

**Demo:** `demo_paths.py --from Cameahwait --to Hidatsa` — one more query, same
tool. *(The 1-hop route is in the stable cost class; safe live.)*

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

## 7.5 — Put it in the pipeline, not the toolbox (0:45)

**Slide:** the NICD callback.

> In the 510-question NICD study, the agent had a path-finding tool.
> **It never called it. Not once.**

**Slide (build):**

> Path retrieval here is deterministic: resolve two anchors → Yen's → receipts
> → context. ~220 ms. **The model doesn't get a vote.**

> Same lesson as the routing table in section 5: if an algorithm materially
> improves retrieval, wire it into the retrieval path. Ours triggers off the
> question shape — two resolved anchors and a "how" — not off a model's whim.
> Next question: all these wins are anecdotes I hand-read to you. Does any of
> it survive a benchmark? That's section 8.

---

## Timing

| slide | time | cumulative |
|---|---|---|
| 7.1 the failure | 0:45 | 0:45 |
| 7.2 live demo — ask HOW | 1:30 | 2:15 |
| 7.3 why k matters, honestly | 1:00 | 3:15 |
| 7.4 receipts catch lies | 1:00 | 4:15 |
| 7.5 NICD close → §8 | 0:45 | 5:00 |

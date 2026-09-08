# Section 10 — Three things to take home
### 2 minutes · starts 0:51 · Q&A from 0:53

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
> **Editorial constraints for this section:**
> - Two slides. The three take-homes get the spoken time; the further-reading
>   slide gets **zero seconds out loud** — it exists for the PDF and the
>   phones.
> - Each take-home is a callback, not new material. If a sentence here needs
>   explaining, it belongs in an earlier section instead.
> - The Lewis example in #1 is stated as a hypothetical ("a graph where…"),
>   which stays true regardless of which database the demos ran on.

---

## 10.1 — Three things (1:30)

**Slide:** all three, together, then a beat on each.

> ### 1 · Build time gates query time.
> Personalized PageRank over a graph where `CAPT. LEWIS` and
> `MERIWETHER LEWIS` are separate nodes will confidently rank the wrong
> passages. Fix entity resolution first.
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
> Number one is section 4 — and you watched it bite sections 5 through 7:
> every query-time algorithm inherited the merge, and the one demo that broke
> in rehearsal broke on an unresolved entity.
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

## 10.2 — The repo, and further reading (0:30)

**Slide:** links, QR code, no talking.

> **github.com/smithna/graph-algorithms-rag** — tonight's code, the measurement
> harness, and every number in this deck with the script that produced it.
>
> - NICD, *Reducing hallucinations with GraphRAG* — the 510-question study
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
> the repo name said once, and open for questions at 0:53.

---

## Timing

| slide | min |
|---|---|
| 10.1 three things | 1:30 |
| 10.2 repo + reading + thanks | 0:30 |
| **total** | **2:00** |

---

## Assets still needed

- [ ] QR code for the talk repo (and verify the repo URL once it's public —
      `smithna/graph-algorithms-rag` assumed here to match last year's
      account; **not yet confirmed**)
- [ ] The three take-homes styled as the closing photograph-slide pair with
      10.2 — consistent with 5.14 and 2.4's hinge, the talk's other two
      photo slides
- [ ] Q&A backup pocket list (one hidden slide of pointers): Louvain findings
      (6a/6b), filter parity (5g), the budget-graph replication (5j),
      Ghoshal caveats — so answers can land on a visual if needed

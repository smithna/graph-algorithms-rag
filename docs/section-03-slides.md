# Section 3 — Roadmap
### four failures, four algorithms, two stages · 1 minute · starts 0:13

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
> **Editorial constraints for this section:**
> - One slide, one minute. The reframe gets said out loud; the table is left
>   on screen while it's said.
> - **Section titles here must track the section files** — §5's row currently
>   reads *"can't tell people apart"* to match `section-05-slides.md`'s
>   draft title, which still needs Nathan's sign-off. If that title moves,
>   this row moves with it.
> - §6's row says **Leiden**, not "Louvain / Leiden" — stage scope decided
>   2026-09-07 (Louvain is Q&A backup only).

---

## 3.1 — The map (1:00)

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
> *(Timekeeping anchor: this slide is minute 13-to-14. Section 4 starts on
> schedule or the cuts list comes out.)*

---

## Timing

| slide | min |
|---|---|
| 3.1 the map | 1:00 |
| **total** | **1:00** |

---

## Assets still needed

- [ ] The table as the talk's recurring visual — sections 4–7 each re-show it
      with their row highlighted (cheap in reveal.js: same slide, one class),
      so build it once, parameterized

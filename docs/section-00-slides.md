# Section 0 — Cold open: the failure
### live demo, no title slide first · 3 minutes · starts 0:00

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
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
> - ⚠️ **One small code gate remains:** the live run needs a vector-only view.
>   `demo_pagerank.py` prints the comparison, which spoils section 5. Either a
>   `--vector-only` flag or a five-line `scripts/demo_baseline.py`. Listed
>   under Assets.

---

## 0.1 — The question, run live (1:15)

**Screen:** a terminal, not a slide. The question typed in front of them.

> ### "What was Toussaint Charbonneau's role on the expedition?"

```
NEO4J_DATABASE=lewisclark python scripts/demo_baseline.py \
    "What was Toussaint Charbonneau's role on the expedition?"
```

**The top-8 comes back. It looks great.**

> No hello, no title slide. Type the question, hit enter, and read the results
> with them for a moment.
>
> Read rank 1 aloud — it is genuinely him, paid off "for his Services as an
> enterpreter." Skim two more: interpreters, negotiations with the Sioux,
> expedition logistics. Every passage is on-topic, fluent, plausibly what you
> would hand an LLM. If this were your pipeline you would ship it.

---

## 0.2 — The reveal (1:00)

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

## 0.3 — The line, then the title (0:45)

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
> when it doesn't. Everything runs on the Lewis & Clark journals, and we come
> back to this exact question with a fix in section 5.
>
> *(House-keeping in one breath: repo link is on the last slide, questions at
> the end.)*

---

## Timing

| slide | min |
|---|---|
| 0.1 the question, live | 1:15 |
| 0.2 the reveal | 1:00 |
| 0.3 the line + title | 0:45 |
| **total** | **3:00** |

---

## Assets still needed

- [ ] **Vector-only demo entry point** — `demo_pagerank.py --vector-only` or a
      tiny `scripts/demo_baseline.py` that prints the top-8 with text
      previews and nothing else. The one code gate on this section.
- [ ] Terminal styled for the projector: font size, and the top-8 previews
      short enough that rank 1's "for his Services as an enterpreter" is
      legible from the back
- [ ] The 2-of-8 slide and the 69/67 build — text only, huge
- [ ] Title slide with the sequel line and last year's repo URL
- [ ] Rehearsal fallback: a screenshot of the live run, in case the DBMS
      isn't up at minute zero (the one demo with no warm-up time before it)

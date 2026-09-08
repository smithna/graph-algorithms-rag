# Section 9 — How to implement this
### the router, the tools, and what not to tune · 3 minutes · starts 0:48

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
> **Editorial constraints for this section:**
> - **Deliberately brief and vendor-plural.** The honest axis is not "who has
>   a better PageRank" — it's *where does your graph live, and how often does
>   it change.*
> - **NetworkX is named, never benchmarked.** Nathan doesn't use it enough to
>   represent it fairly; saying that out loud is the credibility move.
> - **9.1 is the canonical home of the bridge-decay curve** (finding 5n),
>   moved here from the parked draft at the bottom of `section-05-slides.md`.
>   The numbers are the measured 38k-pair sweep; §5.14's decision table is the
>   qualitative version and this is its receipt.
> - **The routing rule coexists with §10's take-home #2**, deliberately: the
>   router is retrieval-path code, not a model-side tool choice. 9.1's notes
>   say so in one line so nobody hears a contradiction.
> - ⚠️ **9.3's Leiden-resolution line ("a corpus decision, not a tunable") is
>   from the 2026-09-07 session and needs its backing example confirmed with
>   Nathan before the scaffold.** Drafted number-free; it rides on §5/§6's
>   already-measured lesson that operating points don't transfer.

---

## 9.1 — When to reach for the graph: one number decides (1:15)

**Slide:** the measured curve behind 5.14's routing table. 38,098
anchor–satellite pairs; median walk-rank of the satellite's unshared passages,
by anchor degree.

| seed's passage count | median rank of the neighbor's passages | reaches top-50 |
|---|---|---|
| 2–5 | **39** | 59% of pairs |
| 6–15 | 112 | 23% |
| 16–40 | 223 | 5% |
| 41–100 | 388 | 0% |
| 300+ | 1,058 | 0% |

**Slide (build):** the router is one query.

```cypher
MATCH (e {canonicalName: $seed})-[:MENTIONED_IN]->(c)
RETURN count(c)   // ≲15 → walk · ≳40 → filter + cosine · 0 → passage-expand
```

> Section 5 ended with a decision table; here is the curve underneath it.
> Monotonic, no exceptions, and the two cases you watched sit right on it —
> the Walla Walla chief, anchor in 3 passages, came back at rank 16; the walk
> from Sacagawea's 85 passages put her brother's at 338.
>
> The mechanism is the bridge fraction — how much of the seed's edge mass
> points toward the answer — but you can't observe that before retrieving.
> **Degree you can.** It's one COUNT query, it runs before you spend anything,
> and it routes the question: sparse seed → walk; hub seed → filter on the tag
> and stop; no seed at all → expand from cosine's top passages, capped per
> community (section 6).
>
> Note what this router is: retrieval-path code. It is not the agent choosing
> a graph tool — section 2 showed how that ends. The *pipeline* counts, the
> pipeline routes, the model never gets a vote.
>
> The thresholds are this corpus's. The **shape** is what transfers — measure
> your own; the harness is in the repo (`measure_bridge_decay.py`, no
> relevance judgements required).

---

## 9.2 — Where to run it (1:00)

**Slide:** vendor-plural, one axis.

> The question isn't *whose PageRank* —
> it's **where does your graph live, and how often does it change?**

> | | |
> |---|---|
> | **Neo4j GDS** | what tonight ran on — the algorithms live where the data lives |
> | **NetworkX** | the standard Python entry point; in-memory, single-machine |
> | **others** | igraph, cuGraph, Spark GraphX — and most graph databases ship an algorithm library |

> Everything you watched tonight ran on Neo4j GDS, because that's where this
> graph lives and I wasn't moving 22,000 mention edges into pandas between
> demos. If your corpus fits in memory and rebuilds nightly, NetworkX is a
> `pip install` and every algorithm in this talk is in it. I don't use it
> enough to demo it fairly, so I won't — but that's a statement about me, not
> about it.
>
> The point to land: **these are algorithms, not products.** PageRank is
> PageRank; Leiden is Leiden; the papers are public and the implementations
> are everywhere. If your corpus is small enough to fit in memory you may not
> need a graph database at all — and knowing that is exactly what makes the
> case for one honest when you do.

---

## 9.3 — What to tune, and what to decide (0:45)

**Slide:** the rule.

> ### Operating points don't transfer.
> ### Some knobs aren't knobs: **resolution (γ) is a corpus decision, not a tunable.**

> Twice in building this talk, a setting measured as *best* on one machine was
> ported to another and did damage — candidate-generation thresholds that were
> right for read-only analysis welded identities together the moment a merge
> step ran downstream. The setting wasn't wrong; the *transfer* was.
>
> And some parameters shouldn't be swept at all. Leiden's resolution — gamma,
> the knob that decides how big a "community" is — looks like a hyperparameter
> and isn't one: it encodes what a *theme* means at your corpus's granularity.
> Sweep it against a retrieval metric and the metric can't see what you traded
> away; look at the partition it produces — do these clusters match what an
> episode, a service, a ticket *is* in your domain? — and decide it once.
> Then hold it still, because the discipline that kept this talk honest is
> **re-run and diff**: seed the randomness, rerun the pipeline, and treat any
> change you didn't make as a bug.
>
> Which is most of take-home #3, so let's do those.

---

## Timing

| slide | min |
|---|---|
| 9.1 the router + curve | 1:15 |
| 9.2 where to run it | 1:00 |
| 9.3 tune vs decide | 0:45 |
| **total** | **3:00** |

---

## Assets still needed

- [ ] The decay curve as a chart, not (only) a table — five bars or a single
      falling line, anchor-degree buckets on the x-axis; the table stays in
      the appendix/PDF
- [ ] The one-query router slide with the three routes as annotations on the
      Cypher, not a second slide
- [ ] Tool table styled to read in five seconds — logos optional, no feature
      matrix
- [ ] 9.3's rule slide — two lines, large; γ typeset as the Greek letter with
      "resolution" beside it
- [ ] Confirm with Nathan the backing example for the γ line (which sweep or
      partition-read it came from) and add one receipt to the notes if it
      exists

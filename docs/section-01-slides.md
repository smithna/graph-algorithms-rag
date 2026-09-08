# Section 1 — What is a graph?
### deliberately fast · 3 minutes · starts 0:03

> **Draft slide content.** Markdown for review; the reveal.js scaffold comes
> later and is mechanical. Speaker notes are in blockquotes.
>
> **Editorial constraints for this section:**
> - **Fast pass, one diagram.** The audience skews new but the algorithms are
>   what was sold; foundations get three minutes and a pointer to the
>   community days repo for the longer build.
> - **The diagram is this corpus**, not `(:Person)-[:KNOWS]->(:Person)`. Every
>   label and relationship type shown here reappears in sections 4–7, so this
>   section is secretly vocabulary pre-loading.
> - **One distinction gets the time: relationships are stored, not computed.**
>   Everything else is a definition said once.
> - Plant **degree** here. Section 5's close and section 9's routing rule turn
>   on "count the node's edges," and it costs five seconds to define now.

---

## 1.1 — Nodes and relationships (1:00)

**Slide:** the diagram — inline SVG, drawn from the live graph's actual shape.

```
                        MEMBER_OF
   (SACAGAWEA:Person) ────────────▶ (SHOSHONE:NativeNation)
          │
          │ MENTIONED_IN
          ▼
   (Chunk: 1805-08-17, Lewis)──NEXT_CHUNK──▶(Chunk: 1805-08-17, Clark)
```

> Nodes are things: a person, a nation, a passage of journal text. Labels say
> what kind of thing. Properties hang key-value data off them — a name, a
> date, and later, an embedding.
>
> Relationships connect two nodes, they have a type and a direction, and —
> the part that matters — **they are data**. `SACAGAWEA MEMBER_OF SHOSHONE`
> is a fact sitting in the database, written once at build time.
>
> This is the actual shape of tonight's graph: the Lewis & Clark journals,
> chunked, with the people, places, and nations mentioned in each chunk
> extracted and linked. Same corpus as last year's talk — that talk was about
> *building* this; the repo link at the end has the whole pipeline. Tonight is
> about what the algorithms do with it.

---

## 1.2 — The one distinction that matters (1:00)

**Slide:** side by side.

> | relational | graph |
> |---|---|
> | the connection is **computed** at query time — match IDs across tables | the connection is **stored** — follow the pointer |
> | cost grows with the tables you join | cost grows with the edges you touch |

> If you have only one takeaway from these three minutes: a JOIN *derives* the
> relationship every time you ask, by matching keys. A graph wrote it down.
> Traversing a million-node graph two hops out from one node touches a few
> hundred edges and never looks at the rest.
>
> That is the property every algorithm in this talk leans on. PageRank,
> community detection, path finding — they are all "follow edges, many times,
> fast," and they are only practical because following an edge is a pointer
> lookup, not a join.

---

## 1.3 — The four words you need (1:00)

**Slide:** glossary, one line each.

> **Label** — what kind of node. `Person`, `Chunk`, `NativeNation`.
> **Relationship type** — what kind of edge. `MENTIONED_IN`, `MEMBER_OF`.
> **Property** — data on either. `canonicalName`, `date`, `embedding`.
> **Degree** — how many edges a node has. **Remember this one.**

> Four definitions and we're done with theory for the day.
>
> Degree gets a beat of its own: it is just a count of a node's edges, it
> costs one query, and by the end of the hour a single degree count will be
> deciding which retrieval strategy your pipeline runs. Cheap number, does a
> lot of work.
>
> Everything deeper — how the chunks were cut, how the entities were
> extracted, how the embeddings got there — is last year's talk, and the repo
> is on the final slide. Onward: what happens when you put a vector index and
> this graph in the same database.

---

## Timing

| slide | min |
|---|---|
| 1.1 nodes and relationships | 1:00 |
| 1.2 stored, not computed | 1:00 |
| 1.3 glossary + degree plant | 1:00 |
| **total** | **3:00** |

---

## Assets still needed

- [ ] The 1.1 diagram as inline SVG — real labels, real relationship types,
      readable node captions; reuse the visual language in sections 4–7 so
      the graph "looks the same" all hour
- [ ] The join-vs-pointer table styled as a slide (or a two-panel sketch:
      key-matching arrows vs a single fat edge)
- [ ] Glossary slide with **degree** visually set apart from the other three

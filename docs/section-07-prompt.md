# Kickoff prompt — section 7 session

> Paste the block below into a fresh conversation to build section 7, per the
> working agreement (one section per conversation, code before slides).

---

Build section 7 of the talk (path finding — "You can't explain the answer" →
Yen's k-shortest paths), code before slides, per the working agreement.

Start by reading graph-algorithms-rag/docs/talk-outline.md: the Progress
table, the §7 outline body, and the two hand-offs pointed at this section —
finding 5m's two-step landing and slide 6.6's close. All work runs on
`lewisclark` — that decision is made; pass NEO4J_DATABASE=lewisclark
explicitly (never repoint the home database). Sanity-check the heap first
(should read 8 GiB via SHOW SETTINGS); if the GDS catalog is empty, rebuild
with `project_graph.py` — `demo_paths.py` needs `lc-retrieval`.

Section 7 has a measured entrance waiting: 5m's flagship, "What do we know
about Sacagawea's brother?" — every one-shot retriever misses the top-8, but
the pure walk surfaces Cameahwait's *name* at rank 4. §7 is the second step:
explain the connection, with receipts. The outline's planned demo is
Sacagawea → Shoshone via `demo_paths.py`; Sacagawea → Cameahwait is the
candidate that ties §5/§6/§7 into one storyline. Both code paths run live but
neither of the section's claims has ever been measured — they are asserted in
the outline body only:

1. **"k matters — the single shortest path is usually trivial co-occurrence;
   the 2nd/3rd carry the mechanism."** Run Yen's at k=1..N for the demo
   anchor pairs (and other pairs the question bank implies) and hand-read
   every hop of every path. Which k first yields a path whose hops *explain*
   rather than merely co-occur? Judged by reading, not by cost or length.
2. **"Paths carry receipts — every hop hands back the journal passage that
   evidences it."** Verify receipt fidelity on `lewisclark` by reading: does
   each hop's chunkId actually evidence that relationship? Two known hazards:
   (a) §4's merge left ~400 relationships with ARRAY date/chunkId properties;
   `paths.py` takes element [0], which silently picks one receipt of several —
   decide whether that is honest enough for the stage or whether hops should
   surface all receipts. (b) Structural relationships (BELONGS_TO etc.) carry
   no chunkId, and `evidence_chunks()` falls back — know what the fallback
   returns before it is on a slide.

Known `lewisclark` facts that will touch this section: DREWYER (297 chunks)
and GEORGE DROUILLARD (84) are still unmerged, so anchors resolving to either
change the story; Persons are fulltext-only (no Person vector index), so
`resolve.py`'s fulltext path is the resolver; and the Step-0 incident — the
stray 1-mention SHOSHONE :Person outscoring the 205-mention :NativeNation on
fulltext, silently emptying every path query, fixed by breaking near-ties on
mention count — is §4-breaks-§7 stage material. Verify the fix holds on
`lewisclark` rather than assuming it.

Measurement discipline: judgments by reading every hop and its cited passage;
no small-sample top-k thresholds; mass or population metrics wherever a count
is claimed; keep retractions in the outline with their history. Don't tune
Yen's weighting against hand-read outcomes — measure what ships.

You own §7 findings, docs/section-07-slides.md (5:00, starts 0:39), and
Progress row 7 only — do not edit §4/§5/§6 files. The NICD callback closes
the section ("the agent never called its path-finding tool once — so put the
algorithm in the deterministic retrieval path, where the model doesn't get a
vote"); the paper is at ~/Downloads/nicd-reducing-hallucinations-graphrag.pdf
if needed. Commit when done. `results/` is gitignored — if you write a
read-pack there, say so in your summary, since hand-read evidence lives only
on this machine.

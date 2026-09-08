# Kickoff prompt — section 8 session

> Paste the block below into a fresh conversation to build section 8, per the
> working agreement (one section per conversation, code before slides). This is
> the last unbuilt section of the talk.

---

Build section 8 of the talk ("Does this actually help?" → the benchmark), code
before slides, per the working agreement. This is the talk's last unbuilt
section, and every other section has an IOU pointing at it: §5's slides say
"every accuracy claim waits for section 8," and §7 closes on "all these wins
are anecdotes I hand-read to you — does any of it survive a benchmark?"

Start by reading graph-algorithms-rag/docs/talk-outline.md: the Progress table,
the §8 outline body (answer-entity recall, where vector should win, the Ghoshal
reasoning-vs-coverage split, the corpus-fits-in-context caveat), Section 5
finding #10 (the gold-set breakage that blocks this section), the Verification
checklist at the bottom, and Implementation-sequence Step 5 — which is this
session's code gate. All work runs on `lewisclark` — pass
NEO4J_DATABASE=lewisclark explicitly (never repoint the home database).
Sanity-check the heap first (should read 8 GiB via SHOW SETTINGS); if the GDS
catalog is empty, rebuild with `project_graph.py` — the strategies need both
`lc-retrieval` and `lc-mentions`.

**The gold set is broken, and no benchmark number is quotable until it is
fixed.** Finding #10: `verify_questions.py` passes ✓ on labels that resolve to
near-empty decoy nodes (its ✓ means "a node with this name exists," not "the
right node") — ELK→Supply(11) instead of CERVUS CANADENSIS, BISON→(3) instead
of BISON BISON, SALMON and GREAT FALLS likewise, and 9 of 22 labels are
ambiguous across nodes. Step 5's prescription: teach `verify_questions.py` the
mention-count prominence prior `resolve.py` already has, fold
`questions/gold_overrides.yaml` (a deliberate stopgap — read its header) into
`questions/questions.yaml` as (name, label) pairs, add markdown table output to
`benchmark.py`, then run for real numbers. Two cautions on the fold: finding
#10's decoy table was measured before the lewisclark migration and the species
re-resolution — re-verify every mapping ON `lewisclark` rather than copying the
table; and two labels are thin rather than mis-resolved (NEZ PERCE — journals
say Chopunnish, split across Person nodes — and PACIFIC OCEAN at 4 mentions):
those are extraction gaps that bound every strategy, which is a finding to
report, not a label to patch around.

The bank is 14 questions across five kinds (3 authority, 4 connection,
2 control, 2 sequence, 3 thematic); `strategies.py` registers vector, ppr,
expand, community, cooccurrence, paths, and hybrid. Two things the numbers must
survive before a slide:

1. **The controls are the honesty check.** `benchmark.py` must show plain
   `vector` winning the `kind: control` questions (Verification section's own
   criterion; §5's caveats note keelboat-return must be re-confirmed at
   whatever blend weight ships). A strategy that wins hard questions and loses
   easy ones is the outline's stated failure mode — if that happens, report
   it, don't tune it away.
2. **Recall is alias-aware, and §4's residuals cut both ways.** `metrics.py`
   builds an alias map from the graph; DREWYER (297 chunks) and GEORGE
   DROUILLARD (84) are still unmerged on `lewisclark`, SHABONO and TOUSSAINT
   CHARBONNEAU likewise, and HIS WIFE is a deliberately-unmerged bridge node.
   Know what the alias map does with those before quoting a recall number —
   a gold entity whose mentions live on an unmerged twin is §4 breaking §8,
   which is stage material, not noise.

Known traps from prior sections that will touch this one: §7's session changed
`paths.py` evidence assembly (all receipts, route-priority round-robin), so
`path_strategy`'s numbers measure the NEW code — that is correct ("measure what
ships"), just don't compare against any pre-§7 paths run; Supply nodes (634)
have no embeddings and no vector index; 179 chunks have zero entities and are
unreachable by any walk (the measured recall floor and the reason blends exist);
and the 3-hop tail of a Yen's route set is sampled, not stable, so per-question
paths results can vary slightly between runs — check whether it moves the
scorecard before claiming determinism.

Measurement discipline, non-negotiable here of all sections: 14 questions is a
small sample — mean/median rank over top-k membership, no findings manufactured
from 1–2 question flips; population metrics wherever a count is claimed; read
the passages behind any headline win before it goes on a slide (finding #10's
proxy caveat stands: entity recall supports "the context contains the facts,"
never "the answer is right"); keep retractions in the outline with their
history. The section's stated posture is that boring numbers are the point —
"maybe you don't need this" gets said from the stage, with the Ghoshal
reasoning/coverage split and the NICD zero-shot column as the caveat that costs
nothing.

You own §8 findings, docs/section-08-slides.md (4:00, starts 0:44), Progress
row 8, and Step 5's code (`verify_questions.py`, `benchmark.py`,
`questions/questions.yaml` + folding away `gold_overrides.yaml`,
`metrics.py` if scoring needs it) — do not edit §0–§7 slide files or their
demo scripts, and `resolve.py` is shared measured surface: port its prominence
prior into `verify_questions.py` rather than changing it. The section hands off
to §9's routing-table beat ("when do you need this") — slide 9.1 already
exists and quotes 5n; land §8's close on the Ghoshal split so 9.1 picks it up.
Commit when done. `results/` is gitignored — if you write benchmark output or
a read-pack there, say so in your summary, since that evidence lives only on
this machine.

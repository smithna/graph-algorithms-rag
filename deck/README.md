# The deck

`index.html` — *Graph Algorithms for RAG*, KCDC 2026. reveal.js 5.2.1, vendored
under `vendor/reveal/` and **never loaded from a CDN**: the deck presents from
this machine with conference wifi assumed dead.

`index.html` is the source of truth for what gets said on stage — every
slide carries its own speaker notes and minute budget (see `M` below). The
working drafts this deck was built from aren't part of this repo; the deck
itself is the final form.

## Presenting

**Use the local server, not `file://`:**

```bash
python -m http.server 8412 --directory deck
```

Then open `http://localhost:8412`. Still zero network — it's localhost — and
it's the only way the speaker view is reliable.

Opening `index.html` directly by double-clicking **does** render the slides
(every path is relative and every script is a UMD build, so there are no ES
module CORS problems). What is not dependable from `file://` is the **speaker
view popup**: it opens a second window that loads the deck in an iframe and
talks to it via `postMessage`, and browsers treat each `file://` document as an
opaque origin, so Chrome in particular blocks it. Since the speaker view is the
reason for reveal.js over PowerPoint — notes *and* a running timer, against
per-section minute budgets — run the server.

There is a launch config at `../../.claude/launch.json` (name: `deck`) if you're
driving this from Claude Code.

## Keys

| key | does |
|---|---|
| `→` / `←` | next / previous. Navigation is **linear** — no vertical stacks to get lost in mid-demo |
| `S` | **speaker view** — notes, next slide, elapsed timer, per-slide timing |
| `M` | toggle the section/timing markers in the bottom-left. On for rehearsal, off for the room |
| `F` | fullscreen |
| `O` / `Esc` | slide overview |
| `B` / `.` | blank the screen — useful when cutting to a terminal for a live demo |
| `?` | reveal's own shortcut list |

The deck is 1600×900 (16:9), matching last year's 10 × 5.625in deck.

## Asset history

All slide assets are in — `grep -n 'class="todo"' deck/index.html` returns
nothing. For the record, in case a future diagram needs the same treatment:

**Diagrams — arrows.app exports.** Nathan draws these; no hand-written SVG,
with two exceptions (§2.1's architecture box and §10.2's QR code, below).
Three fixes bit the one export already in hand and will bite every one: add a
`viewBox` (the export ships bare `width`/`height` and won't scale), widen
nodes until captions stop wrapping mid-word, and check the default `#959aa1`
edge-label grey against the dark background on the actual projector. Landed
2026-09-08: **§1.1**, both **§4.8** diagrams, **§5.6**, **§6.2** (its export
shipped without a `viewBox`; the copy here has one added). Landed 2026-09-09:
**§4.5's** co-occurrence export (fixed in place), **§4.5's** OVERLAP circles
(hand-drawn, area-accurate), **§5.3's** mass-distribution build (five
click-through overlay frames — `assets/images/5_3_ppr_generator.py`
regenerates them), and **§2.1's** architecture diagram (hand-authored SVG,
no arrows.app export — `assets/images/2_1_architecture.svg`).

**The repo QR code** on §10.2 — the repo exists now
(`github.com/smithna/graph-algorithms-rag`, public, pushed) and the code is
generated from it (`assets/RepoQrCode.png`, verified to decode back to that
URL). §8.1's "the harness is in the repo" and §10.2's "every number with the
script that produced it" are both true sentences now.

*(The two supplied images are already in — `assets/KCDC_2026_Sponsors_Slide.jpg`
as a `contain` background on §0.3b, and `assets/SessionFeedbackQrCode.png` on
§10.2.)*

## Fonts

The palette matches last year's deck exactly. The **font does not, yet.**

The theme asks for Calibri first, but **Calibri is not installed on this
machine** — no Office — so it currently falls back to Avenir Next. That means
the deck may look different here than on whatever machine presents it, which is
the one kind of variation a vendored deck is supposed to eliminate.

The fix is in `css/theme-kcdc.css`: drop `Carlito-Regular.woff2` and
`Carlito-Bold.woff2` into `assets/fonts/` and uncomment the two `@font-face`
blocks. Carlito is metric-compatible with Calibri and SIL Open Font Licensed,
so last year's metrics survive and the deck stops depending on what's installed.

## Structure

**63 slides** (as of the 2026-09-09 §5/§6 rebuild — re-check with
`Reveal.getTotalSlides()`, this number drifts every time slides are merged or
cut), all 11 sections, every slide carrying speaker notes and its minute
budget — about 51 seconds a slide against the current 53:40 draft total, summed
directly from each slide's own marker (toggle with `M`); §5 and §6 are
un-rehearsed estimates, not measured.

It was 103 at first draft, which was ~32 seconds a slide and too many. The
reduction was **consolidation, not cutting**: wherever the draft says
"Slide (build):", that is a **reveal fragment on one slide**, not a second
slide, and the first pass had split them. 26 beats were merged back into single
slides that build, and the §1/§2/§8/§9 dividers came out (their speaker notes
moved to each section's first slide). Every word of content and every speaker
note survived — verified by word-frequency diff; the only text that went is the
four dividers' own titles.

**If you merge or add anything, re-check that slides still fit when fully
built.** Two merges overflowed 900px and needed fixing (§8.2 got a compact
`.callout` instead of two headings; §5.10's three limits got `class="tight"`).
The check, with the deck open:

```js
for (let i = 0; i < Reveal.getTotalSlides(); i++) {
  Reveal.slide(i); const s = Reveal.getCurrentSlide();
  s.querySelectorAll('.fragment').forEach(f => f.classList.add('visible'));
  Reveal.layout();
  if (s.scrollHeight > 900) console.log(i + 1, s.dataset.menuTitle, s.scrollHeight);
}
```

Note that browsers cache `theme-kcdc.css` aggressively during editing — a hash
change won't reload it. Hard-reload, or bust it with a query string.

Some speaker notes cite an internal research log by shorthand — `"finding
5q"`, `"the outline"` — from working documents used while building the talk
that aren't part of this repo. Treat those as flavor, not links: the actual
receipts are in `results/` and the `scripts/` that produced them.

Two timekeeping anchors are called out in the notes — **§3.1** (minute
13-to-14) and **§6.1** (0:35) — because §4 and §5 are the only sections that
have ever run long.

**This draft is demo-free (since 2026-09-09).** §5.9's live demo was cut in
the §5 restructure; §7.2 and §7.4 now show `demo_paths.py`'s captured output
as results on glass rather than running it live, so there is no pre-flight
step left. §0.1 is a screenshot and §4.6 is a recording. If live demos come
back, restore the old pre-flight (below) and §7's divider notes.

**Pre-flight (parked, not currently needed):** run one throwaway path query
before walking on stage. The first path query in a fresh process costs
~212 ms; every one after costs ~23 ms.

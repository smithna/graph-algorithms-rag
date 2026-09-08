# The deck

`index.html` — *Graph Algorithms for RAG*, KCDC 2026. reveal.js 5.2.1, vendored
under `vendor/reveal/` and **never loaded from a CDN**: the deck presents from
this machine with conference wifi assumed dead.

Content comes from [`../docs/talk-full-draft.md`](../docs/talk-full-draft.md),
which is the source of truth for what gets said on stage. **Edit the draft
first, then this.** The per-section `docs/section-NN-slides.md` files are behind
both.

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

## What's still needed

**15 asset placeholders**, each rendered as a loud dashed box naming exactly
what's missing. Find them with:

```bash
grep -n 'class="todo"' deck/index.html
```

They fall into three groups:

1. **Diagrams — arrows.app exports.** Nathan draws these; no hand-written SVG.
   Three fixes bit the one export already in hand and will bite every one:
   add a `viewBox` (the export ships bare `width`/`height` and won't scale),
   widen nodes until captions stop wrapping mid-word, and check the default
   `#959aa1` edge-label grey against the dark background on the actual
   projector.
   The one that matters most is **§1.1** — it sets the visual language reused
   in §4–§7 — and the one with the most work in it is **§5.3's
   mass-distribution animation**, five reveal fragments over one export.
2. **Supplied images.** `docs/KCDC_2026_Sponsors_Slide.jpg` and
   `docs/SessionFeedbackQrCode.png` need copying into `deck/assets/`.
3. **The two QR codes** on §10.2 — blocked on the repo actually existing. It
   has no git remote yet; create it under `smithna`, push, *then* generate the
   codes. Until then §8.1's "the harness is in the repo" and §10.2's "every
   number with the script that produced it" are not yet true sentences.

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

103 slides, all 11 sections, every slide carrying speaker notes and its minute
budget. Two timekeeping anchors are called out in the notes — **§3.1** (minute
13-to-14) and **§6.1** (0:35) — because §4 and §5 are the only sections that
have ever run long.

Live demos are **two**: §5.9 (`demo_pagerank.py`) and §7.2 + §7.4
(`demo_paths.py`, one terminal session, two queries). §0.1 is a screenshot and
§4.6 is a recording.

**Pre-flight:** run one throwaway path query before walking on stage. The first
path query in a fresh process costs ~212 ms; every one after costs ~23 ms.

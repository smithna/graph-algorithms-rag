#!/usr/bin/env python3
"""Generate 0_3b_bio.svg — the "whoami, as a graph" slide.

Port of slide 2 of last year's deck
(corps-of-discovery-graph-rag/docs/rag_relationship_problem.pptx, media/image1.png),
redrawn for the dark theme. Two fixes on port (deck todo, 2026-09-09):
  - Neo4j tenure 5 -> 6 years
  - the original's PREIVIOUS_JOB typo -> PREVIOUS_JOB
Node palette follows the original (Neo4j-browser-style category colors).

    python 0_3b_bio_generator.py   # writes 0_3b_bio.svg next to itself
"""

from __future__ import annotations

import math
from pathlib import Path

W, H = 1760, 1100
R = 80  # default node radius

BLUE, LIME, AMBER = "#4C8EDA", "#A4CF30", "#F5B942"
TEAL, PURPLE, RED = "#00857C", "#6E3FA3", "#D8391E"
EDGE, LABEL, CAPTION = "#7A8FA6", "#E8EDF2", "#7A8FA6"
BG_HALO = "#0D1B2A"

# name -> (x, y, r, fill, lines-inside)
NODES = {
    "piano":   (322, 300, R, LIME, ["Piano"]),
    "organ":   (158, 468, R, LIME, ["Organ"]),
    "french":  (105, 778, R, AMBER, ["French"]),
    "swedish": (229, 989, R, AMBER, ["Swedish"]),
    "person":  (593, 719, 85, BLUE, ["Person"]),
    "pos1":    (835, 460, R, TEAL, ["Position"]),
    "pos2":    (1179, 460, R, TEAL, ["Position"]),
    "pos3":    (1527, 460, R, TEAL, ["Position"]),
    "neo4j":   (835, 130, R, PURPLE, ["Neo4j"]),
    "lovevery": (1179, 130, R, PURPLE, ["Lovevery"]),
    "pra":     (1527, 130, R, PURPLE, ["PRA Health", "Sciences"]),
    "dskc":    (1078, 889, 108, RED, ["Data", "Science KC"]),
    "p2":      (1563, 719, R, BLUE, ["Person"]),
    "p3":      (1561, 989, R, BLUE, ["Person"]),
}

# (src, dst, label lines)
EDGES = [
    ("person", "piano", ["PLAYS · level: advanced"]),
    ("person", "organ", ["PLAYS · level: intermediate"]),
    ("person", "french", ["SPEAKS · level: débutant"]),
    ("person", "swedish", ["SPEAKS · level: nybörjare"]),
    ("person", "pos1", ["WORKS_AT"]),
    ("pos1", "pos2", ["PREVIOUS_JOB"]),
    ("pos2", "pos3", ["PREVIOUS_JOB"]),
    ("pos1", "neo4j", ["AT_COMPANY"]),
    ("pos2", "lovevery", ["AT_COMPANY"]),
    ("pos3", "pra", ["AT_COMPANY"]),
    ("person", "dskc", ["ORGANIZES"]),
    ("p2", "dskc", ["ORGANIZES"]),
    ("p3", "dskc", ["ORGANIZES"]),
]

# free-floating property captions: (x, y, anchor, text)
CAPTIONS = [
    (735, 322, "end", "duration: 6 years"),
    (1179, 585, "middle", "duration: 1 year"),
    (1630, 585, "start", "duration: 5 years"),
]


def trim(x1, y1, x2, y2, r1, r2):
    """Endpoints of the segment between two circles' rims."""
    dx, dy = x2 - x1, y2 - y1
    d = math.hypot(dx, dy)
    ux, uy = dx / d, dy / d
    pad = 10  # gap so the arrowhead clears the rim
    return (x1 + ux * (r1 + 4), y1 + uy * (r1 + 4),
            x2 - ux * (r2 + pad), y2 - uy * (r2 + pad))


def main() -> None:
    parts = [
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'font-family="inherit" '
        f'aria-label="Nathan as a property graph: a Person node who PLAYS piano and '
        f'organ, SPEAKS French and Swedish, WORKS_AT a Position (6 years) at Neo4j '
        f'with PREVIOUS_JOB positions at Lovevery and PRA Health Sciences, and '
        f'ORGANIZES Data Science KC along with two other people.">',
        '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{EDGE}"/></marker></defs>',
    ]

    for src, dst, label in EDGES:
        x1, y1, r1 = NODES[src][:3]
        x2, y2, r2 = NODES[dst][:3]
        ax, ay, bx, by = trim(x1, y1, x2, y2, r1, r2)
        parts.append(
            f'<line x1="{ax:.0f}" y1="{ay:.0f}" x2="{bx:.0f}" y2="{by:.0f}" '
            f'stroke="{EDGE}" stroke-width="3" marker-end="url(#arr)"/>'
        )
        mx, my = (ax + bx) / 2, (ay + by) / 2
        angle = math.degrees(math.atan2(by - ay, bx - ax))
        if angle > 90:
            angle -= 180
        elif angle < -90:
            angle += 180
        parts.append(
            f'<text x="{mx:.0f}" y="{my - 10:.0f}" font-size="26" fill="{LABEL}" '
            f'text-anchor="middle" transform="rotate({angle:.0f} {mx:.0f} {my:.0f})" '
            f'paint-order="stroke" stroke="{BG_HALO}" stroke-width="8">'
            f"{label[0]}</text>"
        )

    for x, y, r, fill, lines in NODES.values():
        parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>')
        n = len(lines)
        for i, line in enumerate(lines):
            dy = y + 9 + (i - (n - 1) / 2) * 30
            parts.append(
                f'<text x="{x}" y="{dy:.0f}" font-size="27" fill="#FFFFFF" '
                f'text-anchor="middle">{line}</text>'
            )

    for x, y, anchor, text in CAPTIONS:
        parts.append(
            f'<text x="{x}" y="{y}" font-size="24" fill="{CAPTION}" '
            f'text-anchor="{anchor}" font-style="italic">{text}</text>'
        )

    parts.append("</svg>")
    out = Path(__file__).with_name("0_3b_bio.svg")
    out.write_text("\n".join(parts))
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

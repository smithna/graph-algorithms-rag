# §5.4d "The bridge": how the grouse seed reaches the prairie-dog file.
# Same visual language as 5_3_ppr_generator.py (palette, ring colors, heat
# fills, warn-colored hot path). Static single frame: GROUSE -> its six
# passages (one highlighted: the 1804-09-12 campsite) -> CYNOMYS -> its file.
import math, os

BG, TEXT, MUTED, WARN, EDGE = "#0D1B2A", "#E8EDF2", "#7A8FA6", "#FFB454", "#5c6f85"
ENTITY_RING, CHUNK_RING, DARK = "#00bff3", "#ffb9f8", "#1a1b1d"
RAMP = [(0.0, "#23344b"), (0.35, "#6b2d5c"), (0.7, "#c9502e"), (1.0, "#FFB454")]
W, H = 1500, 700


def lerp_hex(c1, c2, t):
    a = [int(c1[i:i+2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i+2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x+(y-x)*t):02x}" for x, y in zip(a, b))


def ramp_color(t):
    for (t0, c0), (t1, c1) in zip(RAMP, RAMP[1:]):
        if t <= t1:
            return lerp_hex(c0, c1, (t - t0) / (t1 - t0))
    return RAMP[-1][1]


def heat(v):
    if v <= 0:
        return RAMP[0][1]
    t = 1 + math.log10(max(v, 0.01)) / 2
    return ramp_color(max(0.0, min(1.0, t)))


def line(a, b, hot, w_hot=4.5, w_cold=1.8):
    return (f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" '
            f'stroke="{WARN if hot else EDGE}" stroke-width="{w_hot if hot else w_cold}"/>')


def node(x, y, r, ring, v, lines=(), fs=15, ring_w=3):
    fill = heat(v)
    tcol = DARK if math.sqrt(v) > 0.45 else TEXT
    s = f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{ring}" stroke-width="{ring_w}"/>'
    n = len(lines)
    for i, txt in enumerate(lines):
        dy = y + (i - (n - 1) / 2) * (fs + 3) + fs * 0.35
        s += (f'<text x="{x}" y="{dy}" text-anchor="middle" font-size="{fs}" '
              f'font-weight="bold" fill="{tcol}">{txt}</text>')
    return s


grouse = (200, 300, 95)
campsite = (610, 300, 44)
others = [(610, 75, 28), (610, 165, 28), (610, 430, 28), (610, 520, 28), (610, 605, 28)]
cyno = (985, 300, 90)
fan = [(1345, 120, 30), (1345, 210, 30), (1345, 300, 30), (1345, 390, 30), (1345, 480, 30)]

o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">',
     f'<rect width="100%" height="100%" fill="{BG}"/>']

# edges (cold first, hot path on top)
for c in others:
    o.append(line(grouse[:2], c[:2], False))
o.append(line(grouse[:2], campsite[:2], True))
o.append(line(campsite[:2], cyno[:2], True))
for p_ in fan:
    o.append(line(cyno[:2], p_[:2], True, w_hot=2.8))

# nodes
for c in others:
    o.append(node(*c, CHUNK_RING, 0.02))
o.append(node(*grouse, ENTITY_RING, 1.0, ("TYMPANUCHUS", "PHASIANELLUS"), fs=19))
o.append(node(*campsite, CHUNK_RING, 0.35, ring_w=4))
o.append(node(*cyno, ENTITY_RING, 0.5, ("CYNOMYS", "LUDOVICIANUS"), fs=19))
for p_ in fan:
    o.append(node(*p_, CHUNK_RING, 0.15))

# annotations
o.append(f'<text x="200" y="435" text-anchor="middle" font-size="24" fill="{MUTED}">the wrong seed &#183; a grouse</text>')
o.append(f'<text x="400" y="42" text-anchor="middle" font-size="24" fill="{MUTED}">6 passages &#8212; each edge carries 1/6 of the walk</text>')
o.append(f'<text x="610" y="240" text-anchor="middle" font-family="Menlo, Consolas, monospace" font-size="24" fill="{WARN}">1804-09-12</text>')
o.append(f'<text x="610" y="378" text-anchor="middle" font-size="22" fill="{MUTED}">the shared campsite</text>')
o.append(f'<text x="985" y="424" text-anchor="middle" font-size="24" fill="{MUTED}">the prairie dog &#183; 42 passages</text>')
o.append(f'<text x="1345" y="548" text-anchor="middle" font-size="22" fill="{MUTED}">&#8230;and its whole file</text>')
o.append(f'<text x="1345" y="576" text-anchor="middle" font-size="22" fill="{MUTED}">rides across</text>')

# the quote, bottom center
o.append(f'<text x="{W/2}" y="678" text-anchor="middle" font-size="29" font-style="italic" fill="{TEXT}">'
         f'&#8220;Camped &#8230; opsd. a Village of <tspan fill="{WARN}">Barking Prarie Squriels</tspan>'
         f' &#8230; also a great number of <tspan fill="{WARN}">Grous</tspan> &amp; 3 foxes&#8221;</text>')

o.append('</svg>')
outdir = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(outdir, "5_4_bridge.svg"), "w").write("\n".join(o))
print("wrote 5_4_bridge.svg")

# §5.3 mass-distribution overlays: five identical-geometry SVG frames.
# Step numbers are exact power iterations of PPR on this schematic graph
# (d=0.85, restart to the seed); step 4 is the converged vector. Recompute:
# iterate y = .15*e_seed + .85 * sum(x[u]/deg(u) over neighbours).
# Node fill is a heat gradient driven by that frame's mass (sqrt-scaled so
# small masses stay visible); entity vs chunk identity lives in the ring color.
import math, os

BG, TEXT, MUTED, WARN, EDGE = "#0D1B2A", "#E8EDF2", "#7A8FA6", "#FFB454", "#5c6f85"
ENTITY_RING, CHUNK_RING, DARK = "#00bff3", "#ffb9f8", "#1a1b1d"
COLD, HOT = "#23344b", "#FFB454"
W, H = 1500, 800

def lerp_hex(c1, c2, t):
    a = [int(c1[i:i+2],16) for i in (1,3,5)]
    b = [int(c2[i:i+2],16) for i in (1,3,5)]
    return "#" + "".join(f"{round(x+(y-x)*t):02x}" for x, y in zip(a, b))

# Inferno-style ramp (navy -> plum -> ember -> warn orange): midpoints stay
# saturated instead of passing through brown. t is log-scaled over two decades
# (0.01 -> 1.0) so real mass values spread across the ramp.
RAMP = [(0.0, "#23344b"), (0.35, "#6b2d5c"), (0.7, "#c9502e"), (1.0, "#FFB454")]

def ramp_color(t):
    for (t0, c0), (t1, c1) in zip(RAMP, RAMP[1:]):
        if t <= t1:
            return lerp_hex(c0, c1, (t - t0) / (t1 - t0))
    return RAMP[-1][1]

def heat(v):
    if v <= 0: return RAMP[0][1]
    t = 1 + math.log10(max(v, 0.01)) / 2   # .01 -> 0, .1 -> .5, 1.0 -> 1
    return ramp_color(max(0.0, min(1.0, t)))

seed = (170, 390, 62)
passages = [(540, 80+i*88, 30) for i in range(8)]
entities = {"CHARBONNEAU": (920, 200, 52), "CAMEAHWAIT": (920, 400, 52), "HIDATSA": (920, 580, 52)}
rpass = [(1310, 250, 30), (1310, 430, 30), (1310, 610, 30)]

p2e = {0:"CHARBONNEAU",1:"CHARBONNEAU",2:"CHARBONNEAU",3:"CHARBONNEAU",
       4:"CAMEAHWAIT",5:"CAMEAHWAIT",6:"HIDATSA",7:"HIDATSA"}
e2r = {"CHARBONNEAU":[0], "CAMEAHWAIT":[1], "HIDATSA":[2]}

def line(a, b, hot):
    return f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{WARN if hot else EDGE}" stroke-width="{3.5 if hot else 1.8}"/>'

def node(x, y, r, ring, v, label=None, fs=17):
    fill = heat(v)
    s = f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{ring}" stroke-width="3"/>'
    if label:
        tcol = DARK if math.sqrt(v) > 0.45 else TEXT
        s += f'<text x="{x}" y="{y+fs*0.35}" text-anchor="middle" font-size="{fs}" font-weight="bold" fill="{tcol}">{label}</text>'
    return s

def mass(x, y, v, hot, fs=19):
    color = WARN if hot else (MUTED if v == 0 else TEXT)
    txt = "1.00" if v == 1 else (f"{v:.3f}".rstrip("0").lstrip("0") if v else "0")
    return f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Menlo, Consolas, monospace" font-size="{fs}" font-weight="bold" fill="{color}">{txt}</text>'

def legend():
    stops = "".join(f'<stop offset="{p}%" stop-color="{heat(0.01 * 100**(p/100))}"/>' for p in range(0, 101, 5))
    return (f'<defs><linearGradient id="heat" x1="0" y1="0" x2="1" y2="0">{stops}</linearGradient></defs>'
            f'<rect x="30" y="742" width="180" height="14" rx="7" fill="url(#heat)"/>'
            f'<text x="30" y="732" font-size="15" fill="{MUTED}">mass  .01</text>'
            f'<text x="210" y="732" text-anchor="end" font-size="15" fill="{MUTED}">1</text>')

def frame(step, caption, seed_m, p_m, e_m, r_m, hot):
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">',
         f'<rect width="100%" height="100%" fill="{BG}"/>', legend()]
    for p in passages: o.append(line(seed[:2], p[:2], hot == "sp"))
    for i, p in enumerate(passages): o.append(line(p[:2], entities[p2e[i]][:2], hot == "pe"))
    for name, e in entities.items():
        for ri in e2r[name]: o.append(line(e[:2], rpass[ri][:2], hot == "er"))
    o.append(node(*seed, ENTITY_RING, seed_m, "SACAGAWEA", 19))
    for i, p in enumerate(passages): o.append(node(*p, CHUNK_RING, p_m[i]))
    for j, (name, e) in enumerate(entities.items()): o.append(node(*e, ENTITY_RING, e_m[j], name, 15))
    for k, p in enumerate(rpass): o.append(node(*p, CHUNK_RING, r_m[k]))
    o.append(mass(seed[0], seed[1]+seed[2]+30, seed_m, step == 0, 27))
    for i, p in enumerate(passages): o.append(mass(p[0]-58, p[1]+6, p_m[i], step == 1))
    for j, (name, e) in enumerate(entities.items()): o.append(mass(e[0], e[1]+e[2]+28, e_m[j], step == 2, 21))
    for k, p in enumerate(rpass): o.append(mass(p[0]+62, p[1]+6, r_m[k], step == 3))
    if step >= 3:
        o.append(f'<text x="1310" y="700" text-anchor="middle" font-size="19" '
                 f'fill="{WARN if step==3 else MUTED}">these passages never<tspan x="1310" dy="24">mention the seed</tspan></text>')
    o.append(f'<text x="{W/2}" y="770" text-anchor="middle" font-family="Menlo, Consolas, monospace" font-size="21" fill="{TEXT}">'
             f'<tspan fill="{WARN}">step {step}</tspan> — {caption}</text>')
    o.append(f'<text x="{W-16}" y="26" text-anchor="end" font-size="16" fill="{MUTED}">schematic — the real seed has 85 mention edges</text>')
    o.append('</svg>')
    return "\n".join(o)

Z8 = [0]*8
frames = [
    (0, "all the mass starts on the seed", 1.00, Z8, [0,0,0], [0,0,0], "none"),
    (1, "the seed keeps .15 — the damping factor — and splits .85 along its mention edges", .15, [.106]*8, [0,0,0], [0,0,0], "sp"),
    (2, "each passage splits its mass over every entity it names — damping tops the seed back up", .51, [.016]*8, [.18,.09,.09], [0,0,0], "pe"),
    (3, "and back out to THEIR passages — mass reaches passages that never mention the seed", .20, [.085]*4+[.08]*4, [.03,.014,.014], [.031,.026,.026], "er"),
    (4, "iterate until the numbers stop moving", .32, [.052]*4+[.05]*4, [.10,.056,.056], [.018,.016,.016], "none"),
]
outdir = "/Users/nathansmith/Documents/kcdc-2026/graph-algorithms-rag/deck/assets/images"
for step, cap, sm, pm, em, rm, hot in frames:
    open(os.path.join(outdir, f"5_3_ppr_step{step}.svg"), "w").write(frame(step, cap, sm, pm, em, rm, hot))
    print("wrote step", step)

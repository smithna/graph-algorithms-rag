# §6.2 Leiden intro: a SCHEMATIC of community detection on a chunk-only graph.
# One connected graph (every node reachable), three visibly denser
# neighborhoods, colored by community; sparse bridge edges keep it one
# component. Deliberately a schematic, labeled as such — the real partition
# (relatedChunksDf50, 25 communities) is the table-of-contents slide's job.
# Same palette as the other generators. Deterministic (seeded).
import math
import os
import random

BG, TEXT, MUTED, EDGE = "#0D1B2A", "#E8EDF2", "#7A8FA6", "#5c6f85"
CLUSTER_COLORS = ["#00bff3", "#FFB454", "#ffb9f8"]
FILL = "#16263a"
W, H = 1500, 640

rng = random.Random(42)

CENTERS = [(330, 300, 190), (900, 220, 170), (1150, 470, 150)]
N_PER = 14

nodes = []  # (x, y, cluster)
for ci, (cx, cy, cr) in enumerate(CENTERS):
    for _ in range(N_PER):
        a = rng.uniform(0, 2 * math.pi)
        r = cr * math.sqrt(rng.uniform(0.05, 0.85))
        # keep clear of the bottom captions (y >= ~600)
        nodes.append((cx + r * math.cos(a), min(cy + r * math.sin(a), 575), ci))

def dist(i, j):
    return math.hypot(nodes[i][0] - nodes[j][0], nodes[i][1] - nodes[j][1])

edges_in, edges_out = [], []
for ci in range(len(CENTERS)):
    idx = [i for i, n in enumerate(nodes) if n[2] == ci]
    # connect each node to its 4 nearest cluster-mates: dense inside
    for i in idx:
        near = sorted((j for j in idx if j != i), key=lambda j: dist(i, j))[:4]
        for j in near:
            if (j, i) not in edges_in:
                edges_in.append((i, j))
# stitch each cluster internally: k-nearest graphs can strand clumps
def components(idx, edge_list):
    parent = {i: i for i in idx}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b in edge_list:
        if a in parent and b in parent:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    groups = {}
    for i in idx:
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())

for ci in range(len(CENTERS)):
    idx = [i for i, n in enumerate(nodes) if n[2] == ci]
    comps = components(idx, edges_in)
    while len(comps) > 1:
        # connect the two closest components
        best = min(((i, j) for i in comps[0] for c in comps[1:] for j in c),
                   key=lambda ij: dist(*ij))
        edges_in.append(best)
        comps = components(idx, edges_in)

# a few bridges: one connected component, sparse between
BRIDGES = [(0, 1), (1, 2), (0, 2)]
for a, b in BRIDGES:
    ia = min((i for i, n in enumerate(nodes) if n[2] == a),
             key=lambda i: dist(i, [j for j, n in enumerate(nodes) if n[2] == b][0]))
    ib = min((j for j, n in enumerate(nodes) if n[2] == b), key=lambda j: dist(ia, j))
    edges_out.append((ia, ib))

# verify the caption's claim before drawing: exactly one component overall
_all = list(range(len(nodes)))
_final = components(_all, edges_in + edges_out)
assert len(_final) == 1, f"graph not connected: {len(_final)} components"

o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">',
     f'<rect width="100%" height="100%" fill="{BG}"/>']
for i, j in edges_in:
    x1, y1, _ = nodes[i]; x2, y2, _ = nodes[j]
    o.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{EDGE}" stroke-width="1.6"/>')
for i, j in edges_out:
    x1, y1, _ = nodes[i]; x2, y2, _ = nodes[j]
    o.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{MUTED}" stroke-width="1.6" stroke-dasharray="7,7"/>')
for x, y, ci in nodes:
    o.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="13" fill="{FILL}" stroke="{CLUSTER_COLORS[ci]}" stroke-width="3.5"/>')

o.append(f'<text x="330" y="560" text-anchor="middle" font-size="26" fill="{CLUSTER_COLORS[0]}">a community: dense inside…</text>')
o.append(f'<text x="1010" y="620" text-anchor="middle" font-size="26" fill="{MUTED}">…sparse between — yet still one connected graph</text>')
o.append(f'<text x="{W-16}" y="30" text-anchor="end" font-size="18" fill="{MUTED}">schematic — the real graph: 2,424 passages, 25 communities</text>')
o.append('</svg>')

outdir = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(outdir, "6_2_leiden_schematic.svg"), "w").write("\n".join(o))
print("wrote 6_2_leiden_schematic.svg")

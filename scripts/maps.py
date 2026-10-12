"""Render schematic SVG route maps from OSM water polygons + stop coordinates."""
import json, math

def load_water(path):
    d = json.load(open(path))
    rings = []
    for e in d["elements"]:
        if e["type"] == "way" and "geometry" in e:
            g = [(p["lat"], p["lon"]) for p in e["geometry"]]
            if len(g) > 3 and g[0] == g[-1]:
                rings.append(g)
        elif e["type"] == "relation":
            segs = [[(p["lat"], p["lon"]) for p in m["geometry"]] for m in e.get("members", [])
                    if m.get("type") == "way" and m.get("geometry")]
            rings.extend(assemble(segs))
    return rings

def assemble(segs):
    segs = [s for s in segs if len(s) > 1]
    out = []
    while segs:
        ring = segs.pop(0)
        changed = True
        while ring[0] != ring[-1] and changed:
            changed = False
            for i, s in enumerate(segs):
                if s[0] == ring[-1]: ring = ring + s[1:]
                elif s[-1] == ring[-1]: ring = ring + s[::-1][1:]
                elif s[-1] == ring[0]: ring = s + ring[1:]
                elif s[0] == ring[0]: ring = s[::-1] + ring[1:]
                else: continue
                segs.pop(i); changed = True; break
        if len(ring) > 3:
            out.append(ring)
    return out

def clip(poly, xmin, ymin, xmax, ymax):
    def inside(p, edge):
        x, y = p
        return {"l": x >= xmin, "r": x <= xmax, "t": y >= ymin, "b": y <= ymax}[edge]
    def inter(a, b, edge):
        (x1, y1), (x2, y2) = a, b
        if edge in "lr":
            X = xmin if edge == "l" else xmax
            t = (X - x1) / (x2 - x1) if x2 != x1 else 0
            return (X, y1 + t * (y2 - y1))
        Y = ymin if edge == "t" else ymax
        t = (Y - y1) / (y2 - y1) if y2 != y1 else 0
        return (x1 + t * (x2 - x1), Y)
    for edge in "lrtb":
        if not poly: break
        res = []
        prev = poly[-1]
        for cur in poly:
            if inside(cur, edge):
                if not inside(prev, edge): res.append(inter(prev, cur, edge))
                res.append(cur)
            elif inside(prev, edge):
                res.append(inter(prev, cur, edge))
            prev = cur
        poly = res
    return poly

def simplify(pts, tol):
    if len(pts) < 4: return pts
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        (x1, y1), (x2, y2) = pts[a], pts[b]
        dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1e-9
        best, idx = -1, None
        for i in range(a + 1, b):
            x, y = pts[i]
            dd = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L
            if dd > best: best, idx = dd, i
        if idx is not None and best > tol:
            keep[idx] = True; stack += [(a, idx), (idx, b)]
    return [p for p, k in zip(pts, keep) if k]

def simplify_ring(pts, tol):
    if len(pts) < 5: return pts
    x0, y0 = pts[0]
    k = max(range(len(pts)), key=lambda i: (pts[i][0] - x0) ** 2 + (pts[i][1] - y0) ** 2)
    if k == 0: return pts
    return simplify(pts[:k + 1], tol)[:-1] + simplify(pts[k:], tol)

def load_lines(path):
    d = json.load(open(path))
    return [[(p["lat"], p["lon"]) for p in e["geometry"]] for e in d["elements"]
            if e["type"] == "way" and "geometry" in e and "service" not in e.get("tags", {})]

def polys_svg(rings, P, W, H, tol=0.7, min_area=12):
    m = 6; paths = []
    for ring in rings:
        pts = [P(a, b) for a, b in ring]
        bx = [p[0] for p in pts]; by = [p[1] for p in pts]
        if max(bx) < -m or min(bx) > W + m or max(by) < -m or min(by) > H + m: continue
        pts = clip(pts, -m, -m, W + m, H + m)
        if len(pts) < 3: continue
        pts = simplify_ring(pts + [pts[0]], tol)
        if len(pts) < 4: continue
        area = abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1] for i in range(len(pts) - 1))) / 2
        if area < min_area: continue
        paths.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts[:-1]) + "Z")
    return "".join(paths)

def lines_svg(lines, P, W, H, tol=0.8):
    m = 20; out = []
    for ln in lines:
        pts = [P(a, b) for a, b in ln]
        runs, cur = [], []
        for i, (x, y) in enumerate(pts):
            ins = -m <= x <= W + m and -m <= y <= H + m
            if ins: cur.append((x, y))
            elif cur: cur.append((x, y)); runs.append(cur); cur = []
        if cur: runs.append(cur)
        for r in runs:
            r = simplify(r, tol)
            if len(r) > 1: out.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in r))
    return "".join(out)

def render(rings, stops, extra=(), W=600, parks=(), metro=(), pad=0.18, min_aspect=0.62, max_aspect=1.05,
           route=True, title="", colors=None, badge_mode=False):
    """stops: list of dict(lat, lon, label, n) — n is the number shown in the pin.
    extra: list of dict(lat, lon, label, kind='hotel')."""
    allp = list(stops) + list(extra)
    lats = [p["lat"] for p in allp]; lons = [p["lon"] for p in allp]
    lat0 = (max(lats) + min(lats)) / 2
    kx = math.cos(math.radians(lat0))
    xs = [(p["lon"]) * kx for p in allp]; ys = [-p["lat"] for p in allp]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = max(x1 - x0, 0.004), max(y1 - y0, 0.004)
    x0 -= w * pad; x1 += w * pad * 1.6; y0 -= h * pad; y1 += h * pad
    w, h = x1 - x0, y1 - y0
    asp = h / w
    if asp < min_aspect:
        nh = w * min_aspect; y0 -= (nh - h) / 2; y1 += (nh - h) / 2; h = nh
    elif asp > max_aspect:
        nw = h / max_aspect; x0 -= (nw - w) / 2; x1 += (nw - w) / 2; w = nw
    s = W / w; H = round(h * s)
    P = lambda lat, lon: ((lon * kx - x0) * s, (-lat - y0) * s)
    water = polys_svg(rings, P, W, H)
    green = polys_svg(parks, P, W, H, tol=0.9, min_area=40)
    rail = lines_svg(metro, P, W, H)
    svg = [f'<svg class="map" viewBox="0 0 {W} {H}" role="img" aria-label="{title}" xmlns="http://www.w3.org/2000/svg">',
           f'<rect class="m-land" x="0" y="0" width="{W}" height="{H}"/>']
    # faint grid
    g = []
    for gx in range(0, W, 60): g.append(f"M{gx} 0V{H}")
    for gy in range(0, H, 60): g.append(f"M0 {gy}H{W}")
    svg.append(f'<path class="m-grid" d="{"".join(g)}"/>')
    if green: svg.append(f'<path class="m-park" d="{green}"/>')
    if water: svg.append(f'<path class="m-water" fill-rule="evenodd" d="{water}"/>')
    if rail: svg.append(f'<path class="m-metro" d="{rail}"/>')
    pts = [P(p["lat"], p["lon"]) for p in stops]
    if route and len(pts) > 1:
        svg.append('<path class="m-route" d="M' + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + '"/>')
    # labels with simple collision avoidance
    placed = []
    def fits(r):
        if r[0] < 2 or r[2] > W - 2 or r[1] < 2 or r[3] > H - 2: return False
        for q in placed:
            if not (r[2] < q[0] or r[0] > q[2] or r[3] < q[1] or r[1] > q[3]): return False
        return True
    marks = []
    for p, (x, y) in zip(list(extra), [P(e["lat"], e["lon"]) for e in extra]):
        marks.append(("hotel", x, y, p))
    for p, (x, y) in zip(stops, pts):
        marks.append(("stop", x, y, p))
    for kind, x, y, p in marks:
        placed.append((x - 15, y - 15, x + 15, y + 15))
    labels = []
    for kind, x, y, p in marks:
        lab = p.get("label")
        if not lab: continue
        tw = len(lab) * 9.4 + 6; th = 19
        cands = [(x + 19, y - th / 2, "start"), (x - 19 - tw, y - th / 2, "end"),
                 (x - tw / 2, y - 20 - th, "middle"), (x - tw / 2, y + 20, "middle"),
                 (x + 16, y - 26, "start"), (x + 16, y + 8, "start"), (x - 16 - tw, y - 26, "end"), (x - 16 - tw, y + 8, "end")]
        chosen = None
        for cx, cy, anc in cands:
            r = (cx, cy, cx + tw, cy + th)
            if fits(r): chosen = (cx, cy, anc, r); break
        if not chosen:
            cx, cy, anc = cands[0]; chosen = (cx, cy, anc, (cx, cy, cx + tw, cy + th))
        cx, cy, anc, r = chosen; placed.append(r)
        tx = {"start": r[0], "end": r[2], "middle": (r[0] + r[2]) / 2}[anc]
        labels.append(f'<text class="m-label{" m-hl" if kind == "hotel" else ""}" x="{tx:.1f}" y="{cy + 15:.1f}" text-anchor="{anc}">{lab}</text>')
    for kind, x, y, p in marks:
        if kind == "hotel":
            svg.append(f'<g class="m-hotel"><rect x="{x - 12:.1f}" y="{y - 12:.1f}" width="24" height="24" rx="5"/>'
                       f'<path d="M{x - 5:.1f} {y + 5:.1f}V{y - 5:.1f}M{x + 5:.1f} {y + 5:.1f}V{y - 5:.1f}M{x - 5:.1f} {y:.1f}H{x + 5:.1f}"/></g>')
        else:
            cls = "m-pin" + (" m-alt" if p.get("alt") else "")
            svg.append(f'<g class="{cls}"><circle cx="{x:.1f}" cy="{y:.1f}" r="14"/>'
                       f'<text x="{x:.1f}" y="{y + 5.5:.1f}" text-anchor="middle">{p["n"]}</text></g>')
    svg += labels
    # scale bar
    km_px = s * (1 / 111.32) * 1  # 1 km in px (latitude degrees)
    for km in (0.5, 1, 2, 5, 10, 20):
        if km * km_px > 70: break
    L = km * km_px
    svg.append(f'<g class="m-scale"><path d="M16 {H - 18}h{L:.1f}M16 {H - 23}v10M{16 + L:.1f} {H - 23}v10"/>'
               f'<text x="{16 + L + 8:.1f}" y="{H - 13}">{("%g" % km).replace(".", ",")} км</text></g>')
    svg.append(f'<g class="m-north"><path d="M{W - 24} {H - 46}l8 20-8-5-8 5z"/><text x="{W - 24}" y="{H - 8}" text-anchor="middle">С</text></g>')
    svg.append("</svg>")
    return "".join(svg)

"""Relief plates: pixel-art drawings turned into solid, bevelled 3D slabs.

Every pixel of a pixart.Art drawing becomes a column whose half-thickness comes from the shape that
owns it (material keys: d = half-thickness in texels, d0 = half-thickness at the shape's rim, bev = bevel
width in pixels, raise / inset = relative to whatever lies underneath). Front and back faces are greedy
merged rectangles; side walls between columns of different height sample the pixel's own colour, the
way vanilla extrudes item sprites. Pixels whose glow is strong become emissive (full-bright) quads.
"""
import numpy as np
from scipy import ndimage

def depth_map(art):
    """Half-thickness per pixel, following the shapes in draw order."""
    H, W = art.f.h, art.f.w
    order = sorted(art.shapes, key=lambda s: (s[2], s[3]))
    D = np.zeros((H, W), np.float32)
    for mk, m, z, i in order:
        if 'up' in m and 'raise' not in m:
            m = dict(m, **{'raise': m['up']})
        if m.get('flat') and 'd' not in m and 'raise' not in m and 'inset' not in m:
            own = np.maximum(D, 0.5)          # dots and sparkles ride on the surface below
        elif 'raise' in m:
            base = np.where(D > 0, D, m.get('d', 0.5))
            own = base + m['raise']
        elif 'inset' in m:
            base = np.where(D > 0, D, 1.0)
            own = np.maximum(0.25, base - m['inset'])
        else:
            d1 = float(m.get('d', 1.0))
            d0 = float(m.get('d0', d1))
            if d0 < d1:
                bev = max(1.0, float(m.get('bev', 2)))
                dist = ndimage.distance_transform_edt(np.pad(mk, 1))[1:-1, 1:-1]
                own = np.clip(d0 + (dist - 1) * (d1 - d0) / bev, d0, d1)
            else:
                own = np.full((H, W), d1, np.float32)
        D[mk] = own[mk]
    return np.round(D * 4) / 4

def emissive_map(rgba, glow, ratio=0.45):
    if glow is None:
        return np.zeros(rgba.shape[:2], bool)
    g = glow[..., :3].max(-1)
    b = rgba[..., :3].max(-1).astype(np.float32)
    return (glow[..., 3] > 0) & (g >= ratio * np.maximum(b, 1)) & (rgba[..., 3] > 0)

def greedy(key, valid):
    """Maximal rectangles of equal key. Returns list of (x0, y0, x1, y1, key)."""
    H, W = valid.shape
    used = np.zeros((H, W), bool)
    out = []
    for y in range(H):
        x = 0
        while x < W:
            if not valid[y, x] or used[y, x]:
                x += 1
                continue
            k = key[y, x]
            x1 = x
            while x1 + 1 < W and valid[y, x1 + 1] and not used[y, x1 + 1] and key[y, x1 + 1] == k:
                x1 += 1
            y1 = y
            while y1 + 1 < H:
                row_ok = valid[y1 + 1, x:x1 + 1] & ~used[y1 + 1, x:x1 + 1] & (key[y1 + 1, x:x1 + 1] == k)
                if row_ok.all():
                    y1 += 1
                else:
                    break
            used[y:y1 + 1, x:x1 + 1] = True
            out.append((x, y, x1 + 1, y1 + 1, k))
            x = x1 + 1
    return out

def orient(verts, uvs, normal):
    """Order the quad so that (v1-v0) x (v2-v0) points along the outward normal."""
    v = np.asarray(verts, float)
    n = np.cross(v[1] - v[0], v[2] - v[0])
    if np.dot(n, normal) < 0:
        return list(reversed(verts)), list(reversed(uvs))
    return verts, uvs

def mesh(rgba, depth, emis):
    """Quads in plate pixel space: x right, y down, z = Rv x Dv (pointing away from the drawing's viewer).
    Returns list of (verts[4] (x, y, z), uvs[4] (pixel coords), normal, emissive)."""
    H, W = depth.shape
    solid = (rgba[..., 3] > 0) & (depth > 0)
    D = np.where(solid, depth, 0.0)
    quads = []
    # ---- front (-z, the drawing as seen) and back (+z, mirrored)
    key = np.round(D * 4).astype(int) * 2 + emis.astype(int)
    for x0, y0, x1, y1, k in greedy(key, solid):
        d = (k // 2) / 4.0
        e = bool(k % 2)
        uv = [(x0, y0), (x0, y1), (x1, y1), (x1, y0)]
        for zs in (-1, 1):
            vs = [(x0, y0, zs * d), (x0, y1, zs * d), (x1, y1, zs * d), (x1, y0, zs * d)]
            vv, uu = orient(vs, uv, (0, 0, zs))
            quads.append((vv, uu, (0, 0, zs), e))
    # ---- walls. For each pixel and each side, the uncovered height span on the front and back halves.
    def walls(axis):
        # axis 0: walls perpendicular to x (between columns), runs along y; axis 1: perpendicular to y, runs along x
        out = []
        for side in (-1, 1):
            if axis == 0:
                nb = np.zeros_like(D)
                if side > 0:
                    nb[:, :-1] = D[:, 1:]
                else:
                    nb[:, 1:] = D[:, :-1]
            else:
                nb = np.zeros_like(D)
                if side > 0:
                    nb[:-1, :] = D[1:, :]
                else:
                    nb[1:, :] = D[:-1, :]
            exposed = solid & (D > nb + 1e-6)
            # span on each half: from nb to D (if neighbour solid) or from 0 to D (empty neighbour: one full wall)
            lo = np.where(nb > 0, nb, -D)        # empty neighbour -> wall spans -D..D in one piece
            k2 = (np.round(D * 4).astype(int) * 1000 + np.round((lo + 8) * 4).astype(int)) * 2 + emis.astype(int)
            if axis == 0:
                # runs along y for every x
                for x in range(W):
                    col = exposed[:, x]
                    if not col.any():
                        continue
                    y = 0
                    while y < H:
                        if not col[y]:
                            y += 1
                            continue
                        k = k2[y, x]
                        y1 = y
                        while y1 + 1 < H and col[y1 + 1] and k2[y1 + 1, x] == k:
                            y1 += 1
                        out.append((x, y, y1 + 1, D[y, x], lo[y, x], bool(emis[y, x])))
                        y = y1 + 1
            else:
                for y in range(H):
                    row = exposed[y]
                    if not row.any():
                        continue
                    x = 0
                    while x < W:
                        if not row[x]:
                            x += 1
                            continue
                        k = k2[y, x]
                        x1 = x
                        while x1 + 1 < W and row[x1 + 1] and k2[y, x1 + 1] == k:
                            x1 += 1
                        out.append((y, x, x1 + 1, D[y, x], lo[y, x], bool(emis[y, x])))
                        x = x1 + 1
            for rec in out:
                yield axis, side, rec
            out = []
    for axis in (0, 1):
        for ax, side, (fixed, a0, a1, d, lo, e) in walls(axis):
            spans = [(-d, d)] if lo < 0 else [(-d, -lo), (lo, d)]
            for za, zb in spans:
                if axis == 0:
                    x = fixed + (1 if side > 0 else 0)
                    vs = [(x, a0, za), (x, a1, za), (x, a1, zb), (x, a0, zb)]
                    uc0, uc1 = fixed + 0.3, fixed + 0.7
                    uv = [(uc0, a0), (uc0, a1), (uc1, a1), (uc1, a0)]
                    n = (side, 0, 0)
                else:
                    y = fixed + (1 if side > 0 else 0)
                    vs = [(a0, y, za), (a1, y, za), (a1, y, zb), (a0, y, zb)]
                    vc0, vc1 = fixed + 0.3, fixed + 0.7
                    uv = [(a0, vc0), (a1, vc0), (a1, vc1), (a0, vc1)]
                    n = (0, side, 0)
                vv, uu = orient(vs, uv, n)
                quads.append((vv, uu, n, e))
    return quads

# ------------------------------------------------------------------------------------------- smooth relief
LENS = 0.48        # bevels run this far into a shape (fraction of its half-width): lens / diamond sections

def depth_map_smooth(art):
    """Continuous half-thickness per pixel plus the owning shape of every pixel. Bevelled shapes get a
    full lens cross-section; inset / raised / flat shapes keep crisp steps against their surroundings."""
    H, W = art.f.h, art.f.w
    order = sorted(art.shapes, key=lambda s: (s[2], s[3]))
    D = np.zeros((H, W), np.float32)
    owner = -np.ones((H, W), int)
    for k, (mk, m, z, i) in enumerate(order):
        if 'up' in m and 'raise' not in m:
            m = dict(m, **{'raise': m['up']})
        if m.get('flat') and 'd' not in m and 'raise' not in m and 'inset' not in m:
            own = np.maximum(D, 0.5)
        elif 'raise' in m:
            base = np.where(D > 0, D, m.get('d', 0.5))
            own = base + m['raise']
        elif 'inset' in m:
            base = np.where(D > 0, D, 1.0)
            own = np.maximum(0.25, base - m['inset'])
        else:
            d1 = float(m.get('d', 1.0))
            d0 = float(m.get('d0', d1))
            if d0 < d1:
                dist = ndimage.distance_transform_edt(np.pad(mk, 1))[1:-1, 1:-1]
                bev = max(1.0, float(m.get('bev', 2)), LENS * float(dist[mk].max()))
                own = d0 + (d1 - d0) * np.clip((dist - 0.5) / bev, 0, 1)
            else:
                own = np.full((H, W), d1, np.float32)
        D[mk] = own[mk]
        owner[mk] = k
    return np.round(D * 16) / 16, owner

CORNERS = ((0, 0), (1, 0), (1, 1), (0, 1))      # corner offsets of a pixel, in drawing order

def corner_heights(D, owner, solid):
    """h[y, x, c]: height of corner c of pixel (x, y), averaged over the solid pixels of the same shape
    that touch that corner, so each shape is one continuous surface."""
    H, W = D.shape
    Dp = np.pad(D, 1)
    Op = np.pad(owner, 1, constant_values=-2)
    Sp = np.pad(solid, 1)
    hs = np.zeros((H, W, 4), np.float32)
    ys, xs = np.mgrid[0:H, 0:W]
    own = owner
    for c, (cx, cy) in enumerate(CORNERS):
        tot = np.zeros((H, W), np.float32)
        cnt = np.zeros((H, W), np.float32)
        for dy in (-1, 0):
            for dx in (-1, 0):
                qy, qx = ys + cy + dy + 1, xs + cx + dx + 1
                ok = Sp[qy, qx] & (Op[qy, qx] == own)
                tot += np.where(ok, Dp[qy, qx], 0)
                cnt += ok
        hs[..., c] = np.where(cnt > 0, tot / np.maximum(cnt, 1), D)
    return hs

def _tri_normal(a, b, c):
    n = np.cross(np.subtract(b, a), np.subtract(c, a))
    l = np.linalg.norm(n)
    return n / l if l > 1e-9 else n

def mesh_smooth(rgba, D, owner, emis):
    """Sloped relief: coplanar pixels merge into rectangles, curved bevels become triangle pairs, walls
    only where the surface breaks (silhouette or a step between shapes)."""
    H, W = D.shape
    solid = (rgba[..., 3] > 0) & (D > 0)
    hs = corner_heights(D, owner, solid)
    quads = []
    # ---- surfaces
    h0, h1, h2, h3 = hs[..., 0], hs[..., 1], hs[..., 2], hs[..., 3]
    planar = solid & (np.abs(h0 + h2 - h1 - h3) < 1e-4)
    ys, xs = np.mgrid[0:H, 0:W]
    a = h1 - h0
    b = h3 - h0
    c = h0 - a * xs - b * ys
    keymap = {}
    key = np.full((H, W), -1, int)
    for y, x in zip(*np.nonzero(planar)):
        k = (int(round(a[y, x] * 256)), int(round(b[y, x] * 256)), int(round(c[y, x] * 256)), bool(emis[y, x]))
        key[y, x] = keymap.setdefault(k, len(keymap))
    inv = {v: k for k, v in keymap.items()}
    for x0, y0, x1, y1, k in greedy(key, planar):
        ka, kb, kc, e = inv[k]
        pa, pb, pc = ka / 256, kb / 256, kc / 256
        hgt = lambda X, Y: pa * X + pb * Y + pc
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        for zs in (-1, 1):
            vs = [(X, Y, zs * hgt(X, Y)) for X, Y in corners]
            uv = list(corners)
            n = _tri_normal(vs[0], vs[1], vs[2])
            if n[2] * zs < 0:
                n = -n
            vv, uu = orient(vs, uv, n)
            quads.append((vv, uu, tuple(n), e))
    for y, x in zip(*np.nonzero(solid & ~planar)):
        hh = hs[y, x]
        pts = [(x + cx, y + cy) for cx, cy in CORNERS]
        diag = (0, 2) if abs(hh[0] - hh[2]) <= abs(hh[1] - hh[3]) else (1, 3)
        tris = [(0, 1, 2), (0, 2, 3)] if diag == (0, 2) else [(0, 1, 3), (1, 2, 3)]
        e = bool(emis[y, x])
        for zs in (-1, 1):
            for t in tris:
                vs = [(pts[i][0], pts[i][1], zs * hh[i]) for i in t]
                uv = [pts[i] for i in t]
                n = _tri_normal(*vs)
                if n[2] * zs < 0:
                    n = -n
                vv, uu = orient(vs, uv, n)
                quads.append((vv, uu, tuple(n), e))
    # ---- walls: silhouette, and steps between shapes (only the higher side builds the wall)
    sides = (((1, 0), (1, 2), (0, 3)), ((-1, 0), (3, 0), (2, 1)), ((0, 1), (2, 3), (1, 0)), ((0, -1), (0, 1), (3, 2)))
    for y, x in zip(*np.nonzero(solid)):
        hh = hs[y, x]
        e = bool(emis[y, x])
        for (dx, dy), (ca, cb), (qa, qb) in sides:
            qx, qy = x + dx, y + dy
            inside = 0 <= qx < W and 0 <= qy < H and solid[qy, qx]
            A = (x + CORNERS[ca][0], y + CORNERS[ca][1])
            Bp = (x + CORNERS[cb][0], y + CORNERS[cb][1])
            ha, hb = float(hh[ca]), float(hh[cb])
            if dx:
                uvs = lambda: [(x + 0.3, A[1]), (x + 0.3, Bp[1]), (x + 0.7, Bp[1]), (x + 0.7, A[1])]
            else:
                uvs = lambda: [(A[0], y + 0.3), (Bp[0], y + 0.3), (Bp[0], y + 0.7), (A[0], y + 0.7)]
            nrm = (dx, dy, 0)
            if not inside:
                vs = [(A[0], A[1], -ha), (Bp[0], Bp[1], -hb), (Bp[0], Bp[1], hb), (A[0], A[1], ha)]
                vv, uu = orient(vs, uvs(), nrm)
                quads.append((vv, uu, nrm, e))
                continue
            qh = hs[qy, qx]
            ga, gb = float(qh[qa]), float(qh[qb])
            if ha <= ga + 1e-4 and hb <= gb + 1e-4:
                continue
            la, lb = min(ga, ha), min(gb, hb)
            for zs in (-1, 1):
                vs = [(A[0], A[1], zs * la), (Bp[0], Bp[1], zs * lb), (Bp[0], Bp[1], zs * hb), (A[0], A[1], zs * ha)]
                vv, uu = orient(vs, uvs(), nrm)
                quads.append((vv, uu, nrm, e))
    return quads

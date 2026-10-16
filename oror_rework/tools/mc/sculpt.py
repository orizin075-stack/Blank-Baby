"""Sculpted character meshes for RigModel (meshes/<key>.bin).

Geometry is attached to the bones of a rig.Rig and written in the same frame as Bone.box: absolute model
coordinates (y down, feet at 24, front = -Z) of the bone's *unrotated* rest frame; the bone's rest
rotation and every animation turn it about its pivot. All surfaces carry per-vertex normals, so the
entity shader shades them smoothly.

Primitives
  sweep()  generalised loft: cross-sections (superellipse + modulation) swept along a path with
           rotation-minimising frames, optional round / pointed / flat caps. Limbs, torso, hair strands,
           horns, tails, capes (very flat sections), skirts (open lathe), halos (closed path)...
  rbox()   rounded box with box-UV faces, painted by paint.py's box painters (heads, armour, gadgets).
  relief() pixel-art plate extruded into a bevelled slab (relief.py): wings, fins, ornaments.

Each surface owns a texture region (TD texels per model pixel). Painters receive per-texel world
position, normal and ambient occlusion, so shading, hems and patterns follow the 3D shape."""
import math, struct, zlib
import numpy as np
from PIL import Image
from rig import bone_matrices, rot_zyx

TD = 2                                  # texels per model pixel

# ============================================================================== helpers
def _fn(v, n, t):
    """scalar | sequence | callable(t) -> array (n,)"""
    if callable(v):
        return np.array([float(v(x)) for x in t])
    a = np.asarray(v, float)
    if a.ndim == 0:
        return np.full(n, float(a))
    if len(a) == n:
        return a
    return np.interp(t, np.linspace(0, 1, len(a)), a)

def _unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)

def frames(P, up):
    """Rotation-minimising frames along a polyline: tangent T, 'front' axis F (starts as the part of `up`
    orthogonal to T) and side axis S = T x F."""
    P = np.asarray(P, float)
    n = len(P)
    T = np.zeros_like(P)
    T[1:-1] = P[2:] - P[:-2]
    T[0] = P[1] - P[0]
    T[-1] = P[-1] - P[-2]
    T = _unit(T)
    up = np.asarray(up, float)
    F = np.zeros_like(P)
    f = up - (up @ T[0]) * T[0]
    if np.linalg.norm(f) < 1e-6:
        f = np.cross(T[0], [1.0, 0, 0])
        if np.linalg.norm(f) < 1e-6:
            f = np.cross(T[0], [0, 0, 1.0])
    F[0] = _unit(f)
    for i in range(1, n):
        # double reflection (Wang et al.)
        v1 = P[i] - P[i - 1]
        c1 = v1 @ v1
        if c1 < 1e-12:
            F[i] = F[i - 1]
            continue
        rL = F[i - 1] - (2 / c1) * (v1 @ F[i - 1]) * v1
        tL = T[i - 1] - (2 / c1) * (v1 @ T[i - 1]) * v1
        v2 = T[i] - tL
        c2 = v2 @ v2
        F[i] = rL - (2 / c2) * (v2 @ rL) * v2 if c2 > 1e-12 else rL
        F[i] = _unit(F[i] - (F[i] @ T[i]) * T[i])
    S = np.cross(T, F)
    return T, F, S

def bezier(*pts, n=12):
    """Polyline through a Bezier curve given by its control points."""
    pts = np.asarray(pts, float)
    t = np.linspace(0, 1, n)[:, None]
    k = len(pts) - 1
    out = np.zeros((n, 3))
    for i, p in enumerate(pts):
        out += math.comb(k, i) * (1 - t) ** (k - i) * t ** i * p
    return out

def arc(center, radius, a0, a1, axis='y', n=16):
    cx, cy, cz = center
    a = np.linspace(a0, a1, n)
    if axis == 'y':
        return np.stack([cx + radius * np.cos(a), np.full(n, cy), cz + radius * np.sin(a)], 1)
    if axis == 'x':
        return np.stack([np.full(n, cx), cy + radius * np.cos(a), cz + radius * np.sin(a)], 1)
    return np.stack([cx + radius * np.cos(a), cy + radius * np.sin(a), np.full(n, cz)], 1)

def resample(P, step=1.0, min_n=3):
    P = np.asarray(P, float)
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    n = max(min_n, int(math.ceil(d[-1] / step)) + 1)
    s = np.linspace(0, d[-1], n)
    return np.stack([np.interp(s, d, P[:, i]) for i in range(3)], 1)

# ============================================================================== surfaces
class Surf:
    """Mesh patch on a bone. V/N in the bone's box frame, UV in region texels, Q quads (index quadruples)."""
    def __init__(self, bone, V, N, UV, Q, size, mat, kind, info=None, name='surf'):
        self.bone, self.V, self.N, self.UV, self.Q = bone, np.asarray(V, float), _unit(N), np.asarray(UV, float), np.asarray(Q, int)
        self.size = (max(1, int(size[0])), max(1, int(size[1])))
        self.mat, self.kind, self.info, self.name = mat, kind, info or {}, name
        self.rgba = self.glow = None
        self.pos = None                       # atlas offset

def rest_matrix(bone):
    """4x4 rest transform of a bone (box coords relative to its pivot -> model coords), as bone_matrices."""
    chain = []
    b = bone
    while b is not None:
        chain.append(b)
        b = b.parent
    M = np.eye(4)
    for b in reversed(chain):
        pp = b.parent.pivot if b.parent else (0, 0, 0)
        L = np.eye(4)
        L[:3, 3] = [b.pivot[i] - pp[i] for i in range(3)]
        R = np.eye(4)
        R[:3, :3] = rot_zyx(*b.rot)
        Sm = np.diag([*b.scale, 1.0])
        M = M @ L @ R @ Sm
    return M

class Sculpt:
    """Collects surfaces for a rig; rig.sculpt points here."""
    def __init__(self, rig, td=TD):
        self.rig, self.td, self.surfs = rig, td, []
        rig.sculpt = self

    def add(self, s):
        if s.info.get('world'):
            # geometry given in rest-pose model coordinates: bring it into the bone's box frame
            M = rest_matrix(s.bone)
            Mi = np.linalg.inv(M)
            piv = np.array(s.bone.pivot, float)
            s.V = (Mi[:3, :3] @ s.V.T).T + Mi[:3, 3] + piv
            s.N = _unit((Mi[:3, :3] @ s.N.T).T)
        self.surfs.append(s)
        return s

def S(rig):
    return getattr(rig, 'sculpt', None) or Sculpt(rig)

# ------------------------------------------------------------------------------ sweep
def sweep(bone, path, a, b=None, mat=None, e=2.0, k=16, up=(0, 0, -1), mod=None, off=None, caps=('round', 'round'),
          cap_len=None, closed=False, theta0=0.0, arc_range=None, name='sweep', td=None, info=None, step=None):
    """Loft a cross-section along `path` (n,3).
    a: half size along the side axis S, b: half size along the front axis F (default a); scalars, sequences
    (resampled over t) or callables of t in [0, 1]. e: superellipse exponent (2 = ellipse, 4 = rounded square).
    mod(theta, t) -> radius multiplier; off(theta, t) -> (dS, dF) section offsets. theta = 0 points along F
    (the 'front'), increasing towards S. caps: 'round' | 'point' | 'flat' | None for each end.
    closed: the path is a loop (torus). arc_range=(t0, t1) sweeps only part of the section (open sheet)."""
    rig = bone.rig
    td = td or getattr(getattr(rig, 'sculpt', None), 'td', TD)
    P = np.asarray(path, float)
    if step:
        P = resample(P, step)
    if closed:
        P = np.vstack([P, P[:1]])
    n = len(P)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    dist = np.r_[0, np.cumsum(seg)]
    t = dist / max(dist[-1], 1e-9)
    A = _fn(a, n, t)
    B = _fn(a if b is None else b, n, t)
    E = _fn(e, n, t)
    if closed:
        T = np.zeros_like(P)
        T[1:-1] = P[2:] - P[:-2]
        T[0] = T[-1] = P[1] - P[-2]
        T = _unit(T)
        F = _unit(np.asarray(up, float) - (T @ np.asarray(up, float))[:, None] * T)
        Sd = np.cross(T, F)
    else:
        T, F, Sd = frames(P, up)
    # ring parameters (path rings + cap rings)
    rings = []                     # (center, T, F, S, scaleA, scaleB, E, t, tipflag)
    def cap(end, kind):
        if kind not in ('round', 'point', 'flat'):
            return []
        i = 0 if end == 0 else n - 1
        sgn = -1.0 if end == 0 else 1.0
        r = max(A[i], B[i])
        L = cap_len if cap_len is not None else (r if kind == 'round' else r * 1.6)
        out = []
        if kind == 'round':
            steps = max(2, min(5, int(round(r * 1.2)) + 1))
            for j in range(1, steps + 1):
                phi = (math.pi / 2) * j / steps
                out.append((P[i] + sgn * T[i] * L * math.sin(phi), math.cos(phi), j == steps))
        elif kind == 'point':
            out.append((P[i] + sgn * T[i] * L * 0.55, 0.55, False))
            out.append((P[i] + sgn * T[i] * L, 0.0, True))
        else:
            out.append((P[i], 0.0, True))
        if end == 0:
            out = out[::-1]
        return [(c, T[i], F[i], Sd[i], A[i] * f, B[i] * f, E[i], 0.0 if end == 0 else 1.0, tip) for c, f, tip in out]
    if not closed:
        rings += cap(0, caps[0] if caps else None)
    for i in range(n):
        rings.append((P[i], T[i], F[i], Sd[i], A[i], B[i], E[i], t[i], False))
    if not closed:
        rings += cap(1, caps[1] if caps else None)
    R = len(rings)
    if arc_range is None:
        th = theta0 + np.linspace(-math.pi, math.pi, k + 1)
    else:
        th = theta0 + np.linspace(arc_range[0], arc_range[1], k + 1)
    cols = k + 1
    V = np.zeros((R, cols, 3))
    C = np.zeros((R, 3))
    tips = np.zeros(R, bool)
    for r_i, (c, Ti, Fi, Si, ai, bi, ei, ti, tip) in enumerate(rings):
        ct, st = np.cos(th), np.sin(th)
        pw = 2.0 / max(ei, 0.5)
        x = np.sign(st) * np.abs(st) ** pw          # side
        y = np.sign(ct) * np.abs(ct) ** pw          # front
        m = mod(th, ti) if mod is not None else 1.0
        sx, sy = ai * x * m, bi * y * m
        if off is not None:
            ds, dn = off(th, ti)
            sx, sy = sx + ds, sy + dn
        V[r_i] = c + np.outer(sx, Si) + np.outer(sy, Fi)
        C[r_i] = c
        tips[r_i] = tip
    # normals: finite differences on the grid
    dU = np.zeros_like(V)
    if arc_range is None:
        dU[:, 1:-1] = V[:, 2:] - V[:, :-2]
        dU[:, 0] = dU[:, -1] = V[:, 1] - V[:, -2]
    else:
        dU[:, 1:-1] = V[:, 2:] - V[:, :-2]
        dU[:, 0] = V[:, 1] - V[:, 0]
        dU[:, -1] = V[:, -1] - V[:, -2]
    dV = np.zeros_like(V)
    if closed:
        dV[1:-1] = V[2:] - V[:-2]
        dV[0] = dV[-1] = V[1] - V[-2]
    else:
        dV[1:-1] = V[2:] - V[:-2]
        dV[0] = V[1] - V[0]
        dV[-1] = V[-1] - V[-2]
    Nn = np.cross(dU, dV)
    # orient outwards (away from the ring centre); for sheets use the front direction
    out = V - C[:, None, :]
    flip = (Nn * out).sum(-1)
    if np.nanmean(np.sign(flip[np.abs(flip) > 1e-9])) < 0 if (np.abs(flip) > 1e-9).any() else False:
        Nn = -Nn
    bad = np.linalg.norm(Nn, axis=-1) < 1e-9
    for r_i in range(R):
        if bad[r_i].any():
            Ti = rings[r_i][1]
            sgn = -1.0 if r_i < R / 2 else 1.0
            if tips[r_i]:
                Nn[r_i, bad[r_i]] = sgn * Ti
            else:
                Nn[r_i, bad[r_i]] = (out[r_i, bad[r_i]] if np.linalg.norm(out[r_i]) > 0 else sgn * Ti)
    Nn = _unit(Nn)
    # UVs: u around (arc length of the widest ring), v along (centre distance, caps by surface length)
    per = np.array([np.linalg.norm(np.diff(V[r], axis=0), axis=1).sum() for r in range(R)])
    W = max(1, int(math.ceil(per.max() * td)))
    along = np.zeros(R)
    for r_i in range(1, R):
        along[r_i] = along[r_i - 1] + np.linalg.norm(V[r_i] - V[r_i - 1], axis=1).mean()
    H = max(1, int(math.ceil(along[-1] * td)))
    U = np.linspace(0, W, cols)
    UV = np.zeros((R, cols, 2))
    UV[..., 0] = U[None, :]
    UV[..., 1] = (along / max(along[-1], 1e-9) * H)[:, None]
    idx = np.arange(R * cols).reshape(R, cols)
    Q = []
    for r_i in range(R - 1):
        for j in range(cols - 1):
            Q.append((idx[r_i, j], idx[r_i + 1, j], idx[r_i + 1, j + 1], idx[r_i, j + 1]))
    inf = dict(info or {})
    inf.update(rows=R, cols=cols, theta=th, ring_t=np.array([rg[7] for rg in rings]))
    s = Surf(bone, V.reshape(-1, 3), Nn.reshape(-1, 3), UV.reshape(-1, 2), Q, (W, H), mat, 'sweep', inf, name)
    return S(rig).add(s)

def tube(bone, pts, r0, r1=None, mat=None, **kw):
    """Round tube through pts, radius tapering r0 -> r1."""
    r1 = r0 if r1 is None else r1
    return sweep(bone, pts, lambda t: r0 + (r1 - r0) * t, mat=mat, **kw)

def lathe(bone, center, profile, mat=None, k=24, rz=None, **kw):
    """Surface of revolution about a vertical axis through `center` (x, z); profile = [(y, r), ...] top to
    bottom. rz scales the depth (ellipse). The path runs down the axis."""
    prof = np.asarray(profile, float)
    path = np.stack([np.full(len(prof), center[0]), prof[:, 0], np.full(len(prof), center[1])], 1)
    rad = prof[:, 1]
    rzk = 1.0 if rz is None else rz
    return sweep(bone, path, rad, rad * rzk, mat=mat, k=k, up=(0, 0, -1), **kw)

def torus(bone, center, R, r, mat=None, axis='y', k=10, n=40, **kw):
    path = arc(center, R, 0, 2 * math.pi, axis, n + 1)[:-1]
    up = {'y': (0, -1, 0), 'x': (1, 0, 0), 'z': (0, 0, -1)}[axis]
    return sweep(bone, path, r, mat=mat, k=k, closed=True, up=up, caps=None, **kw)

# ------------------------------------------------------------------------------ rounded box
FACES = {
    # face: (normal, origin corner selector, u axis, v axis)  -- box-UV orientation of paint.py / ModelPart
    'front':  ((0, 0, -1), ('x0', 'y0', 'z0'), (1, 0, 0), (0, 1, 0)),
    'back':   ((0, 0, 1), ('x1', 'y0', 'z1'), (-1, 0, 0), (0, 1, 0)),
    'right':  ((-1, 0, 0), ('x0', 'y0', 'z1'), (0, 0, -1), (0, 1, 0)),
    'left':   ((1, 0, 0), ('x1', 'y0', 'z0'), (0, 0, 1), (0, 1, 0)),
    'top':    ((0, -1, 0), ('x0', 'y0', 'z1'), (1, 0, 0), (0, 0, -1)),
    'bottom': ((0, 1, 0), ('x0', 'y1', 'z1'), (1, 0, 0), (0, 0, -1)),
}

class FakeCube:
    def __init__(self, bone, name, size, origin=(0, 0, 0)):
        self.bone, self.name, self.size, self.origin = bone, name, tuple(size), origin

def _samples(lo, hi, r, step=None):
    """Grid lines across a face: the flat middle needs none, the rounded margins three each."""
    L = hi - lo
    xs = {round(lo, 5), round(hi, 5)}
    if step:
        xs |= set(np.linspace(lo, hi, max(2, int(math.ceil(L / step)) + 1)).round(5))
    if r > 1e-6 and L > 0:
        rr = min(r, L / 2)
        for f in (0.3, 0.65, 1.0):
            xs.add(round(lo + rr * f, 5))
            xs.add(round(hi - rr * f, 5))
    return np.array(sorted(xs))

def rbox(bone, origin, size, mat, radius=None, name='box', faces=None, grow=0.0, td=None, skip=(), info=None):
    """Rounded box (min corner `origin`, `size`), every face its own box-UV region so paint.py painters apply.
    radius defaults to 30% of the smallest side (max 2 px). Zero-thickness boxes become double-sided plates."""
    rig = bone.rig
    td = td or getattr(getattr(rig, 'sculpt', None), 'td', TD)
    o = np.array(origin, float) - grow
    s = np.array(size, float) + 2 * grow
    hi = o + s
    if radius is None:
        positive = [v for v in s if v > 0.05]
        radius = min(2.0, 0.3 * min(positive)) if positive else 0.0
    r = float(radius)
    lo_in = o + np.minimum(r, s / 2)
    hi_in = hi - np.minimum(r, s / 2)
    flat_axis = [i for i in range(3) if s[i] < 0.05]
    cube = FakeCube(bone, name, tuple(float(v) for v in size))
    out = []
    for face, (nrm, corner, ua, va) in FACES.items():
        if face in skip:
            continue
        nrm, ua, va = np.array(nrm, float), np.array(ua, float), np.array(va, float)
        ax = int(np.argmax(np.abs(nrm)))
        if ax in flat_axis and nrm[ax] > 0 and False:
            continue
        fm = mat
        if faces and face in faces:
            fm = faces[face]
            if fm is None:
                continue
        iu, iv = int(np.argmax(np.abs(ua))), int(np.argmax(np.abs(va)))
        wpx, hpx = s[iu], s[iv]
        if wpx < 0.05 or hpx < 0.05:
            continue
        us = _samples(0, wpx, r)
        vs = _samples(0, hpx, r)
        cx = np.array([o[0] if corner[0] == 'x0' else hi[0], o[1] if corner[1] == 'y0' else hi[1], o[2] if corner[2] == 'z0' else hi[2]])
        P = cx[None, None, :] + us[None, :, None] * ua[None, None, :] + vs[:, None, None] * va[None, None, :]
        inner = np.clip(P, lo_in, hi_in)
        d = P - inner
        dl = np.linalg.norm(d, axis=-1, keepdims=True)
        Nf = np.where(dl > 1e-9, d / np.maximum(dl, 1e-12), nrm)
        if r > 0:
            Pr = np.where(dl > 1e-9, inner + r * Nf, P)
        else:
            Pr = P
        if ax in flat_axis:
            Nf = np.broadcast_to(nrm, Nf.shape).copy()
            Pr = P
        rows, cols = P.shape[:2]
        W, H = max(1, int(round(wpx * td))), max(1, int(round(hpx * td)))
        UV = np.stack(np.broadcast_arrays(us[None, :] / wpx * W, vs[:, None] / hpx * H), -1)
        idx = np.arange(rows * cols).reshape(rows, cols)
        Q = [(idx[i, j], idx[i + 1, j], idx[i + 1, j + 1], idx[i, j + 1]) for i in range(rows - 1) for j in range(cols - 1)]
        inf = dict(info or {})
        inf.update(face=face, cube=cube, px=(wpx, hpx))
        out.append(S(rig).add(Surf(bone, Pr.reshape(-1, 3), Nf.reshape(-1, 3), UV.reshape(-1, 2), Q, (W, H), fm, 'box', inf, name)))
    return out

def crbox(bone, center, size, mat, **kw):
    c, s = np.asarray(center, float), np.asarray(size, float)
    return rbox(bone, c - s / 2, s, mat, **kw)

# ------------------------------------------------------------------------------ relief plates
def relief(bone, art_fn, w, h, at, U, V, mat=None, name='relief', res=2, info=None):
    """Pixel-art plate: art_fn(Art) draws on a w x h pixel canvas (res pixels per model px); canvas pixel
    (0, 0) corner sits at `at`, U = direction of +x (columns), V = direction of +y (rows), in box coords.
    The drawing is extruded into a bevelled slab (relief.py), depth in canvas pixels scaled likewise."""
    import pixart as PA, relief as RL
    rig = bone.rig
    art = PA.Art(PA.Frame(int(w), int(h), (0, 0), (1, 0), 1.0))
    art_fn(art)
    rgba, gl = art.render()
    D, owner = RL.depth_map_smooth(art)
    em = RL.emissive_map(rgba, gl)
    rgba = rgba.copy()
    if em.any():
        bright = np.clip(rgba[..., :3].astype(np.float32) * 0.7 + gl[..., :3] * 0.6, 0, 255)
        rgba[..., :3] = np.where(em[..., None], bright, rgba[..., :3]).astype(np.uint8)
    U, Vv = _unit(U), _unit(V)
    Nn = np.cross(U, Vv)
    at = np.asarray(at, float)
    k = 1.0 / res
    verts, norms, uvs, quads = [], [], [], []
    for vs, uv, n, e in RL.mesh_smooth(rgba, D, owner, em):
        base = len(verts)
        nw = n[0] * U + n[1] * Vv + n[2] * Nn
        nw = nw / max(1e-9, np.linalg.norm(nw))
        pts = [at + (x * U + y * Vv + z * Nn) * k for x, y, z in vs]
        uv = list(uv)
        if len(pts) == 3:
            pts.append(pts[2])
            uv.append(uv[2])
        for p_, q in zip(pts, uv):
            verts.append(p_)
            norms.append(nw)
            uvs.append(q)
        quads.append((base, base + 1, base + 2, base + 3))
    inf = {'rgba': rgba, 'emis': em, 'glowsrc': gl}
    inf.update(info or {})
    surf = Surf(bone, verts, norms, uvs, quads, (rgba.shape[1], rgba.shape[0]), mat, 'relief', inf, name)
    return S(rig).add(surf)

# ============================================================================== baking
def world_of(rig):
    mats = bone_matrices(rig)
    return mats

def surf_world(s, mats):
    Mb = mats[s.bone.name]
    piv = np.array(s.bone.pivot, float)
    P = (Mb[:3, :3] @ (s.V - piv).T).T + Mb[:3, 3]
    N = (Mb[:3, :3] @ s.N.T).T
    return P, _unit(N)

def raster_attrs(s, Pw, Nw):
    """Per-texel world position/normal and coverage in the surface's region (UV-space rasterisation)."""
    W, H = s.size
    P = np.zeros((H, W, 3), np.float32)
    N = np.zeros((H, W, 3), np.float32)
    cov = np.zeros((H, W), bool)
    UV = s.UV
    for q in s.Q:
        for tri in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
            a, b, c = UV[tri[0]], UV[tri[1]], UV[tri[2]]
            den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(den) < 1e-12:
                continue
            x0, x1 = int(max(0, math.floor(min(a[0], b[0], c[0]) - 0.5))), int(min(W - 1, math.ceil(max(a[0], b[0], c[0]))))
            y0, y1 = int(max(0, math.floor(min(a[1], b[1], c[1]) - 0.5))), int(min(H - 1, math.ceil(max(a[1], b[1], c[1]))))
            if x1 < x0 or y1 < y0:
                continue
            ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
            px, py = xs + 0.5, ys + 0.5
            l1 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / den
            l2 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / den
            l3 = 1 - l1 - l2
            eps = -0.02
            m = (l1 >= eps) & (l2 >= eps) & (l3 >= eps)
            if not m.any():
                continue
            pw = l1[..., None] * Pw[tri[0]] + l2[..., None] * Pw[tri[1]] + l3[..., None] * Pw[tri[2]]
            nw = l1[..., None] * Nw[tri[0]] + l2[..., None] * Nw[tri[1]] + l3[..., None] * Nw[tri[2]]
            sub = (slice(y0, y1 + 1), slice(x0, x1 + 1))
            P[sub][m] = pw[m]
            N[sub][m] = nw[m]
            cov[sub][m] = True
    # fill uncovered texels from neighbours
    if not cov.all() and cov.any():
        from scipy import ndimage
        idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
        P = P[idx[0], idx[1]]
        N = N[idx[0], idx[1]]
    N = N / np.maximum(np.linalg.norm(N, axis=-1, keepdims=True), 1e-9)
    return P, N, cov

class Occlusion:
    """Volumetric ambient occlusion: the character is voxelised from its texel samples, filled, blurred;
    occlusion at a texel = density a little way out along its normal."""
    def __init__(self, samples, res=0.5):
        from scipy import ndimage
        pts = np.concatenate([p.reshape(-1, 3) for p in samples])
        self.lo = pts.min(0) - 4
        self.res = res
        dims = np.ceil((pts.max(0) + 4 - self.lo) / res).astype(int) + 1
        g = np.zeros(dims, bool)
        ii = np.floor((pts - self.lo) / res).astype(int)
        ii = np.clip(ii, 0, dims - 1)
        g[ii[:, 0], ii[:, 1], ii[:, 2]] = True
        g = ndimage.binary_closing(g, iterations=1)
        g = ndimage.binary_fill_holes(g)
        self.d1 = ndimage.gaussian_filter(g.astype(np.float32), 1.2 / res)
        self.d2 = ndimage.gaussian_filter(g.astype(np.float32), 3.0 / res)

    def sample(self, grid, P):
        from scipy import ndimage
        c = ((P.reshape(-1, 3) - self.lo) / self.res).T
        return ndimage.map_coordinates(grid, c, order=1, mode='constant').reshape(P.shape[:-1])

    def ao(self, P, N):
        near = self.sample(self.d1, P + N * 1.4)
        far = self.sample(self.d2, P + N * 3.5)
        occ = 1.4 * np.maximum(0, near - 0.10) + 1.1 * np.maximum(0, far - 0.16)
        return np.clip(1.0 - occ, 0.35, 1.0)

def bake(rig, painter, seed=11, ao=True):
    """Paint every surface: painter(surf, ctx) -> (rgb, alpha, glow)."""
    sc = rig.sculpt
    mats = world_of(rig)
    ctxs = []
    for s in sc.surfs:
        Pw, Nw = surf_world(s, mats)
        P, N, cov = raster_attrs(s, Pw, Nw)
        ctxs.append((P, N, cov))
    occ = Occlusion([c[0][c[2]] for c in ctxs if c[2].any()]) if ao else None
    for s, (P, N, cov) in zip(sc.surfs, ctxs):
        A = occ.ao(P, N) if occ is not None and s.info.get('ao', True) else np.ones(P.shape[:2], np.float32)
        rng = np.random.default_rng(zlib.crc32(f'{seed}/{s.bone.name}/{s.name}/{s.info.get("face", "")}'.encode()))
        rgb, alpha, glow = painter(s, dict(P=P, N=N, cov=cov, ao=A, rng=rng, td=sc.td))
        H, W = s.size[1], s.size[0]
        rgba = np.zeros((H, W, 4), np.float32)
        rgba[..., :3] = rgb
        rgba[..., 3] = 255 if alpha is None else np.clip(alpha, 0, 1) * 255
        s.rgba = rgba
        s.glow = glow

# ============================================================================== atlas + export
def pack(surfs, max_w=1024):
    order = sorted(range(len(surfs)), key=lambda i: (-surfs[i].size[1], -surfs[i].size[0]))
    best = None
    for Wt in (64, 128, 256, 512, 1024, 2048):
        if Wt > max_w:
            break
        pos, x, y, shelf, ok = {}, 0, 0, 0, True
        for i in order:
            w, h = surfs[i].size[0] + 2, surfs[i].size[1] + 2      # 1 texel gutter
            if w > Wt:
                ok = False
                break
            if x + w > Wt:
                x, y, shelf = 0, y + shelf, 0
            pos[i] = (x + 1, y + 1)
            x += w
            shelf = max(shelf, h)
        if not ok:
            continue
        Ht = max(16, int(math.ceil((y + shelf) / 16.0)) * 16)
        cand = (max(Wt, Ht), Wt * Ht, Wt, Ht, pos)
        if best is None or cand[:2] < best[:2]:
            best = cand
    _, _, Wt, Ht, pos = best
    for i, s in enumerate(surfs):
        s.pos = pos[i]
    return Wt, Ht

GLOW_K = 0.85

def atlas(rig):
    surfs = rig.sculpt.surfs
    Wt, Ht = pack(surfs)
    tex = np.zeros((Ht, Wt, 4), np.float32)
    glow = np.zeros((Ht, Wt, 4), np.float32)
    for s in surfs:
        x, y = s.pos
        w, h = s.size
        tex[y:y + h, x:x + w] = s.rgba
        # gutter: extend edge texels (no alpha bleeding at seams)
        tex[y - 1, x:x + w] = s.rgba[0]
        tex[y + h, x:x + w] = s.rgba[-1]
        tex[y - 1:y + h + 1, x - 1] = tex[y - 1:y + h + 1, x]
        tex[y - 1:y + h + 1, x + w] = tex[y - 1:y + h + 1, x + w - 1]
        if s.glow is not None:
            g = s.glow
            m = (g[..., 3] > 0) & (s.rgba[..., 3] > 0)
            reg = glow[y:y + h, x:x + w]
            reg[m] = g[m]
    k = glow[..., 3:4] / 255.0 * GLOW_K
    glow[..., :3] *= k
    glow[..., 3] = np.where(glow[..., 3] > 0, 255, 0)
    glow[glow[..., 3] == 0, :3] = 0
    return (Image.fromarray(np.clip(tex, 0, 255).astype(np.uint8), 'RGBA'),
            Image.fromarray(np.clip(glow, 0, 255).astype(np.uint8), 'RGBA'), (Wt, Ht))

def export_mesh(rig, path, size):
    """meshes/<key>.bin: per bone (rig order) vertices (1/32 px rel. pivot, uv/65535, normal*127) and quads."""
    Wt, Ht = size
    by_bone = {}
    for s in rig.sculpt.surfs:
        by_bone.setdefault(s.bone.name, []).append(s)
    out = [struct.pack('>ii', 0x4F524D33, len(rig.bones))]
    total = 0
    for b in rig.bones:
        ss = by_bone.get(b.name, [])
        V, UV, N, Q = [], [], [], []
        base = 0
        offs = []
        piv = np.array(b.pivot, float)
        for s in ss:
            offs.append(base)
            x, y = s.pos
            V.append(s.V - piv)
            UV.append(np.stack([(s.UV[:, 0] + x) / Wt, (s.UV[:, 1] + y) / Ht], 1))
            N.append(s.N)
            Q.append(np.asarray(s.Q, int) + base)
            base += len(s.V)
        if not ss:
            out.append(struct.pack('>i', 0))
            continue
        V = np.concatenate(V); UV = np.concatenate(UV); N = np.concatenate(N); Q = np.concatenate(Q)
        if len(V) > 65535:
            raise ValueError(f'{rig.key}/{b.name}: {len(V)} vertices')
        vi = np.clip(np.round(V * 32), -32768, 32767).astype('>i2')
        ui = np.clip(np.round(UV * 65535), 0, 65535).astype('>u2')
        ni = np.clip(np.round(N * 127), -127, 127).astype('i1')
        rec = np.zeros(len(V), dtype=[('p', '>i2', 3), ('u', '>u2', 2), ('n', 'i1', 3)])
        rec['p'], rec['u'], rec['n'] = vi, ui, ni
        out.append(struct.pack('>i', len(V)))
        out.append(rec.tobytes())
        out.append(struct.pack('>i', len(Q)))
        out.append(Q.astype('>u2').tobytes())
        G = np.concatenate([np.asarray(s.Q, int) + off for s, off in zip(ss, offs) if s.glow is not None and (s.glow[..., 3] > 0).any()]) \
            if any(s.glow is not None and (s.glow[..., 3] > 0).any() for s in ss) else np.zeros((0, 4), int)
        out.append(struct.pack('>i', len(G)))
        out.append(G.astype('>u2').tobytes())
        total += len(Q)
    with open(path, 'wb') as fh:
        fh.write(b''.join(out))
    return total

def model_top(rig):
    mats = world_of(rig)
    lo = 1e9
    for s in rig.sculpt.surfs:
        P, _ = surf_world(s, mats)
        lo = min(lo, P[:, 1].min())
    return lo

# ============================================================================== preview
L0 = _unit(np.array([0.2, 1.0, -0.7]))        # Minecraft entity lights (world, y up)
L1 = _unit(np.array([-0.2, 1.0, 0.7]))

def render(rig, tex, glow=None, yaw=25, pitch=8, size=(420, 560), pose=None, bg=(46, 48, 58), frame=None, scale=None):
    """Gouraud-shaded orthographic preview of the sculpted mesh with the entity lighting model."""
    W, H = size
    T = np.asarray(tex, np.float32) / 255.0
    G = np.asarray(glow, np.float32) / 255.0 if glow is not None else None
    th, tw = T.shape[:2]
    mats = bone_matrices(rig, pose)
    V = rot_zyx(math.radians(pitch), 0, 0) @ rot_zyx(0, math.radians(yaw), 0)
    img = np.zeros((H, W, 3), np.float32)
    img[:] = bg
    zb = np.full((H, W), -1e9, np.float32)
    tris = []
    allp = []
    for s in rig.sculpt.surfs:
        if s.info.get('lids'):
            continue                                  # eyelids only show while blinking
        Mb = mats[s.bone.name]
        piv = np.array(s.bone.pivot, float)
        P = (Mb[:3, :3] @ (s.V - piv).T).T + Mb[:3, 3]
        N = _unit((Mb[:3, :3] @ s.N.T).T)
        Pw = np.stack([P[:, 0], -P[:, 1], -P[:, 2]], 1)        # world: y up, front towards +z (camera)
        Nw = np.stack([N[:, 0], -N[:, 1], -N[:, 2]], 1)
        Pv = Pw @ V.T
        lit = np.clip(0.4 + 0.6 * (np.maximum(0, Nw @ L0) + np.maximum(0, Nw @ L1)), 0, 1)
        x, y = s.pos
        uv = (s.UV + (x, y))
        allp.append(Pv)
        for q in s.Q:
            for tri in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
                tris.append((Pv[list(tri)], uv[list(tri)], lit[list(tri)]))
    allp = np.concatenate(allp)
    lo, hi = allp.min(0), allp.max(0)
    if frame is None:
        span = max(hi[0] - lo[0], (hi[1] - lo[1]) * W / H) * 1.1
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    else:
        cx, cy, span = frame
    sc = W / span
    for P, uv, lit in tris:
        Sx = (P[:, 0] - cx) * sc + W / 2
        Sy = -(P[:, 1] - cy) * sc + H / 2
        x0, x1 = int(max(0, math.floor(Sx.min()))), int(min(W - 1, math.ceil(Sx.max())))
        y0, y1 = int(max(0, math.floor(Sy.min()))), int(min(H - 1, math.ceil(Sy.max())))
        if x1 < x0 or y1 < y0:
            continue
        den = (Sy[1] - Sy[2]) * (Sx[0] - Sx[2]) + (Sx[2] - Sx[1]) * (Sy[0] - Sy[2])
        if abs(den) < 1e-9:
            continue
        ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
        px, py = xs + 0.5, ys + 0.5
        l1 = ((Sy[1] - Sy[2]) * (px - Sx[2]) + (Sx[2] - Sx[1]) * (py - Sy[2])) / den
        l2 = ((Sy[2] - Sy[0]) * (px - Sx[2]) + (Sx[0] - Sx[2]) * (py - Sy[2])) / den
        l3 = 1 - l1 - l2
        m = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        if not m.any():
            continue
        z = l1 * P[0, 2] + l2 * P[1, 2] + l3 * P[2, 2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        m &= z > sub
        if not m.any():
            continue
        u = l1 * uv[0, 0] + l2 * uv[1, 0] + l3 * uv[2, 0]
        v = l1 * uv[0, 1] + l2 * uv[1, 1] + l3 * uv[2, 1]
        ui = np.clip(u.astype(int), 0, tw - 1)
        vi = np.clip(v.astype(int), 0, th - 1)
        texel = T[vi, ui]
        m &= texel[..., 3] > 0.1
        if not m.any():
            continue
        li = l1 * lit[0] + l2 * lit[1] + l3 * lit[2]
        col = texel[..., :3] * li[..., None] * 255
        if G is not None:
            col = col + G[vi, ui, :3] * 255
        sub[m] = z[m]
        img[y0:y1 + 1, x0:x1 + 1][m] = np.clip(col[m], 0, 255)
    return Image.fromarray(img.astype(np.uint8))

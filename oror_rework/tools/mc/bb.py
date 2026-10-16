"""Blockbench-style geometry for RigModel meshes (meshes/<key>.bin).

Every part is a cuboid with flat faces and crisp edges, optionally rotated about a pivot like a Blockbench
element, and every face owns its own pixel-art texture region (TD texels per model pixel). This is the look of
the models people call the best-looking in Minecraft (L_Ender's Cataclysm, Yes Steve Model, Touhou Little Maid,
Bosses of Mass Destruction): many small, deliberately placed and angled boxes, clean hand-painted textures.

cube()     one cuboid by min corner + size in the bone's box frame; rot (radians, applied Z*Y*X like bones)
           turns it about `pivot` (default: its centre)
obox()     cuboid by centre, size and explicit local axes
enable()   makes sculpt.sweep / torus / lathe / tube / rbox / relief build cuboids, so recipes written for the
           sculpt toolkit (creatures, trinkets, props) produce Blockbench-style geometry as well:
           a loft becomes a chain of boxes along its path, a ring becomes a ring of tangent boxes, an open sheet
           becomes angled plates, a relief becomes a stepped pixel extrusion (like vanilla item models)."""
import math
import numpy as np
import sculpt as SC
from rig import rot_zyx

TD = 2
FACES = SC.FACES
_orig = {}


def _unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-12)


def _td(bone, td):
    return td or getattr(getattr(bone.rig, 'sculpt', None), 'td', TD)


def obox(bone, center, size, axes, mat, name='cube', faces=None, td=None, info=None, skip=(), inflate=0.0, tex_size=None):
    """Cuboid: centre (3,), size along its local axes, axes = 3x3 whose columns are the local x, y, z directions
    in box coordinates. Plates (one size ~0) get their two big faces only, a hair apart, so both sides show
    their own texture. tex_size keeps the texture resolution of the un-inflated box (Blockbench inflate)."""
    rig = bone.rig
    td = _td(bone, td)
    c = np.asarray(center, float)
    s = np.abs(np.asarray(size, float))
    R = np.asarray(axes, float)
    ts = np.abs(np.asarray(tex_size if tex_size is not None else s, float))
    flat = [i for i in range(3) if s[i] < 0.05]
    g = s + 2 * inflate
    for i in flat:
        g[i] = 0.0
    lo, hi = -g / 2, g / 2
    cube = SC.FakeCube(bone, name, tuple(float(v) for v in s))
    out = []
    for face, (nrm, corner, ua, va) in FACES.items():
        if face in skip:
            continue
        fm = mat
        if faces and face in faces:
            fm = faces[face]
            if fm is None:
                continue
        nrm, ua, va = np.array(nrm, float), np.array(ua, float), np.array(va, float)
        ax = int(np.argmax(np.abs(nrm)))
        iu, iv = int(np.argmax(np.abs(ua))), int(np.argmax(np.abs(va)))
        if flat and ax not in flat:
            continue
        wpx, hpx = g[iu], g[iv]
        if wpx < 0.02 or hpx < 0.02:
            continue
        cx = np.array([lo[0] if corner[0] == 'x0' else hi[0], lo[1] if corner[1] == 'y0' else hi[1],
                       lo[2] if corner[2] == 'z0' else hi[2]])
        if ax in flat:
            cx = cx + nrm * 0.012
        P = np.array([cx, cx + wpx * ua, cx + wpx * ua + hpx * va, cx + hpx * va])
        Pw = c + P @ R.T
        n = _unit(R @ nrm)
        W = max(1, int(round(ts[iu] * td)))
        H = max(1, int(round(ts[iv] * td)))
        UV = np.array([[0, 0], [W, 0], [W, H], [0, H]], float)
        inf = dict(info or {})
        inf.update(face=face, cube=cube, px=(float(ts[iu]), float(ts[iv])), bb=True, dims=tuple(float(v) for v in ts))
        out.append(SC.S(rig).add(SC.Surf(bone, Pw, np.tile(n, (4, 1)), UV, [(0, 1, 2, 3)], (W, H), fm, 'bb', inf, name)))
    return out


def cube(bone, origin, size, mat, rot=None, pivot=None, name='cube', faces=None, td=None, info=None, skip=(), inflate=0.0):
    o = np.asarray(origin, float)
    s = np.asarray(size, float)
    c = o + s / 2
    R = np.eye(3)
    if rot is not None and any(abs(v) > 1e-9 for v in rot):
        R = rot_zyx(*rot)
        p = c if pivot is None else np.asarray(pivot, float)
        c = p + R @ (c - p)
    return obox(bone, c, s, R, mat, name=name, faces=faces, td=td, info=info, skip=skip, inflate=inflate)


def ccube(bone, center, size, mat, **kw):
    c, s = np.asarray(center, float), np.asarray(size, float)
    return cube(bone, c - s / 2, s, mat, **kw)


def beam(bone, p0, p1, w, d, mat, up=(0, 0, -1), name='beam', ext=0.0, **kw):
    """Box from p0 to p1 (length axis), w across (side), d along `up` (front)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    T = p1 - p0
    L = float(np.linalg.norm(T))
    if L < 1e-6:
        return []
    T = T / L
    F = np.asarray(up, float) - (np.asarray(up, float) @ T) * T
    if np.linalg.norm(F) < 1e-6:
        F = np.cross(T, [1.0, 0, 0]) if abs(T[0]) < 0.9 else np.cross(T, [0, 0, 1.0])
    F = _unit(F)
    Sd = np.cross(T, F)
    R = np.stack([Sd, T, F], 1)
    return obox(bone, (p0 + p1) / 2, (w, L + ext, d), R, mat, name=name, **kw)


# ============================================================================== sculpt -> cuboids
def sweep_boxes(bone, path, a, b=None, mat=None, e=2.0, k=16, up=(0, 0, -1), mod=None, off=None, caps=('round', 'round'),
                cap_len=None, closed=False, theta0=0.0, arc_range=None, name='sweep', td=None, info=None, step=None):
    P = np.asarray(path, float)
    if len(P) < 2:
        return []
    if closed:
        P = np.vstack([P, P[:1]])
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    keep = np.r_[True, seg > 1e-6]
    P = P[keep]
    if len(P) < 2:
        return []
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    d = np.r_[0, np.cumsum(seg)]
    L = d[-1]
    tt = d / L
    A0 = SC._fn(a, len(P), tt)
    B0 = SC._fn(a if b is None else b, len(P), tt)
    big = float(np.mean(np.maximum(A0, B0)))
    if arc_range is not None:
        stp = step or float(np.clip(L / 6, 1.0, 3.0))
    else:
        stp = step or float(np.clip(1.4 * big + 0.5, 0.8, 3.2))
    n = max(2, int(math.ceil(L / stp - 1e-6)) + 1)
    if closed:
        n = max(n, 8)
    s = np.linspace(0, L, n)
    Q = np.stack([np.interp(s, d, P[:, i]) for i in range(3)], 1)
    tq = s / L
    A = SC._fn(a, n, tq) if callable(a) else np.interp(tq, tt, A0)
    B = SC._fn(a if b is None else b, n, tq) if (callable(b) or (b is None and callable(a))) else np.interp(tq, tt, B0)
    if closed:
        T = np.zeros_like(Q)
        T[1:-1] = Q[2:] - Q[:-2]
        T[0] = T[-1] = Q[1] - Q[-2]
        T = _unit(T)
        upv = np.asarray(up, float)
        F = _unit(upv - (T @ upv)[:, None] * T)
        Sd = np.cross(T, F)
    else:
        T, F, Sd = SC.frames(Q, up)
    inf0 = dict(info or {})
    out = []
    if arc_range is not None:
        th0, th1 = theta0 + arc_range[0], theta0 + arc_range[1]
        per = max(1e-6, abs(th1 - th0) * float(np.mean(np.maximum(A, B))))
        m = max(1, int(math.ceil(per / 2.6)))
        ths = np.linspace(th0, th1, m + 1)
        def ring(i, th):
            ct, st = np.cos(th), np.sin(th)
            mm = mod(th, tq[i]) if mod is not None else 1.0
            sx, sy = A[i] * st * mm, B[i] * ct * mm
            if off is not None:
                ds, dn = off(th, tq[i])
                sx, sy = sx + ds, sy + dn
            return Q[i] + np.outer(np.atleast_1d(sx), Sd[i]).reshape(-1, 3) + np.outer(np.atleast_1d(sy), F[i]).reshape(-1, 3)
        rings = [ring(i, ths) for i in range(n)]
        thick = float(inf0.pop('thick', 0.5))
        for i in range(n - 1):
            for j in range(m):
                q00, q01 = rings[i][j], rings[i][j + 1]
                q10, q11 = rings[i + 1][j], rings[i + 1][j + 1]
                xa = _unit((q01 - q00) + (q11 - q10))
                ya = (q10 + q11) / 2 - (q00 + q01) / 2
                ln = float(np.linalg.norm(ya))
                if ln < 1e-6:
                    continue
                ya = _unit(ya - (ya @ xa) * xa)
                za = np.cross(xa, ya)
                ctr = (q00 + q01 + q10 + q11) / 4
                # keep the plate's outer face outward (away from the path)
                if (ctr - (Q[i] + Q[i + 1]) / 2) @ za < 0:
                    xa, za = -xa, -za
                wdt = (np.linalg.norm(q01 - q00) + np.linalg.norm(q11 - q10)) / 2 + 0.12
                ctr = ctr - za * thick / 2
                inf = dict(inf0, t=float((tq[i] + tq[i + 1]) / 2), t_lo=float(tq[i]), t_hi=float(tq[i + 1]), seg=i, col=j)
                out += obox(bone, ctr, (wdt, ln + 0.1, thick), np.stack([xa, ya, za], 1), mat, name=name, td=td, info=inf)
        return out
    for i in range(n - 1):
        p0, p1 = Q[i], Q[i + 1]
        Tm = _unit(p1 - p0)
        Fm = F[i] + F[i + 1]
        Fm = Fm - (Fm @ Tm) * Tm
        if np.linalg.norm(Fm) < 1e-6:
            Fm = F[i] - (F[i] @ Tm) * Tm
        Fm = _unit(Fm)
        Sm = np.cross(Tm, Fm)
        am = (A[i] + A[i + 1]) / 2
        bm = (B[i] + B[i + 1]) / 2
        if mod is not None:
            try:
                am *= float(np.mean(mod(np.array([math.pi / 2, -math.pi / 2]), (tq[i] + tq[i + 1]) / 2)))
                bm *= float(np.mean(mod(np.array([0.0, math.pi]), (tq[i] + tq[i + 1]) / 2)))
            except Exception:
                pass
        if am < 0.04 and bm < 0.04:
            continue
        w, dd = max(0.2, 2 * am), max(0.2, 2 * bm)
        ln = float(np.linalg.norm(p1 - p0))
        ov = min(0.45, 0.35 * min(w, dd)) if (i < n - 2 or closed) else 0.0
        if i > 0 or closed:
            ov += 0.0
        inf = dict(inf0, t=float((tq[i] + tq[i + 1]) / 2), t_lo=float(tq[i]), t_hi=float(tq[i + 1]), seg=i)
        ctr = (p0 + p1) / 2 + Tm * ov / 2
        out += obox(bone, ctr, (w, ln + ov, dd), np.stack([Sm, Tm, Fm], 1), mat, name=name, td=td, info=inf)
    if not closed and caps:
        for end in (0, 1):
            kind = caps[end] if len(caps) > end else None
            if kind not in ('round', 'point'):
                continue
            i = 0 if end == 0 else n - 1
            sgn = -1.0 if end == 0 else 1.0
            am, bm = A[i], B[i]
            r = max(am, bm)
            if r < 0.12:
                continue
            Ti = T[i]
            Fi = _unit(F[i] - (F[i] @ Ti) * Ti)
            Si = np.cross(Ti, Fi)
            R = np.stack([Si, Ti, Fi], 1)
            inf = dict(inf0, t=float(end), seg=-1, cap=kind)
            if kind == 'round':
                Lc = (cap_len if cap_len is not None else r) * 0.55
                if Lc < 0.15:
                    continue
                out += obox(bone, Q[i] + sgn * Ti * Lc / 2, (max(0.2, 2 * am * 0.7), Lc, max(0.2, 2 * bm * 0.7)), R, mat,
                            name=name, td=td, info=inf)
            else:
                Lc = (cap_len if cap_len is not None else r * 1.6)
                if Lc < 0.2:
                    continue
                out += obox(bone, Q[i] + sgn * Ti * Lc * 0.3, (max(0.2, 2 * am * 0.62), Lc * 0.6, max(0.2, 2 * bm * 0.62)), R, mat,
                            name=name, td=td, info=inf)
                out += obox(bone, Q[i] + sgn * Ti * Lc * 0.78, (max(0.15, 2 * am * 0.3), Lc * 0.4, max(0.15, 2 * bm * 0.3)), R, mat,
                            name=name, td=td, info=inf)
    return out


def rbox_bb(bone, origin, size, mat, radius=None, name='box', faces=None, grow=0.0, td=None, skip=(), info=None):
    o = np.asarray(origin, float) - grow
    s = np.asarray(size, float) + 2 * grow
    inf = dict(info or {})
    return obox(bone, o + s / 2, s, np.eye(3), mat, name=name, faces=faces, td=td, info=inf, skip=skip,
                tex_size=np.asarray(size, float))


def relief_bb(bone, art_fn, w, h, at, U, V, mat=None, name='relief', res=2, info=None):
    """Pixel-art plate extruded in steps (flat walls, like vanilla item models)."""
    import pixart as PA, relief as RL
    rig = bone.rig
    art = PA.Art(PA.Frame(int(w), int(h), (0, 0), (1, 0), 1.0))
    art_fn(art)
    rgba, gl = art.render()
    D = RL.depth_map(art)
    em = RL.emissive_map(rgba, gl)
    rgba = rgba.copy()
    if em.any():
        bright = np.clip(rgba[..., :3].astype(np.float32) * 0.7 + gl[..., :3] * 0.6, 0, 255)
        rgba[..., :3] = np.where(em[..., None], bright, rgba[..., :3]).astype(np.uint8)
    D = np.where(D > 0, np.maximum(0.5, np.round(D * 2) / 2), 0.0)
    U, Vv = _unit(U), _unit(V)
    Nn = np.cross(U, Vv)
    at = np.asarray(at, float)
    kk = 1.0 / res
    verts, norms, uvs, quads = [], [], [], []
    for vs, uv, n, e in RL.mesh(rgba, D, em):
        base = len(verts)
        nw = n[0] * U + n[1] * Vv + n[2] * Nn
        nw = nw / max(1e-9, np.linalg.norm(nw))
        for (x, y, z), q in zip(vs, uv):
            verts.append(at + (x * U + y * Vv + z * Nn) * kk)
            norms.append(nw)
            uvs.append(q)
        quads.append((base, base + 1, base + 2, base + 3))
    inf = {'rgba': rgba, 'emis': em, 'glowsrc': gl, 'bbrelief': True}
    inf.update(info or {})
    surf = SC.Surf(bone, verts, norms, uvs, quads, (rgba.shape[1], rgba.shape[0]), mat, 'relief', inf, name)
    return SC.S(rig).add(surf)


def enable():
    if _orig:
        return
    _orig.update(sweep=SC.sweep, rbox=SC.rbox, relief=SC.relief)
    SC.sweep = sweep_boxes
    SC.rbox = rbox_bb
    SC.relief = relief_bb


def disable():
    if not _orig:
        return
    SC.sweep, SC.rbox, SC.relief = _orig['sweep'], _orig['rbox'], _orig['relief']
    _orig.clear()

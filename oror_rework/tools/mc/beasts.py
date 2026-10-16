"""Sculpted creature parts: smooth lofted bodies, heads and jaws, tails that stay continuous across their
swaying bones, tapered legs with toes and claws, horns, teeth, eyes painted at 3D positions, and fins,
flukes and sails as bevelled relief plates (2x pixel art)."""
import math
import numpy as np
import pixart as PA
import sculpt as SC
from paint import M
from colors import hexc, mix, shade

def eye(p, r, color, glow=True, slit=True, pupil='#0a0c14'):
    return {'kind': 'eye', 'p': p, 'r': r, 'color': color, 'glow': glow, 'slit': slit, 'pupil': pupil}

def dot(p, r, color, glow=False, amount=1.0):
    return {'kind': 'dot', 'p': p, 'r': r, 'color': color, 'glow': glow, 'glow_amount': amount}

def line(p, p2, r, color, glow=False):
    return {'kind': 'line', 'p': p, 'p2': p2, 'r': r, 'color': color, 'glow': glow}

def loft(bone, pts, w, h, mat, e=2.2, k=20, caps=('round', 'round'), spots=None, name='body', mod=None, off=None, cap_len=None,
         td=None, up=(0, -1, 0), info=None):
    """Body along a path (any direction); w = half width (sideways), h = half height (vertical)."""
    inf = {'hem': False, 'spots': spots or []}
    inf.update(info or {})
    return SC.sweep(bone, np.asarray(pts, float), w, h, mat, e=e, k=k, up=up, caps=caps, mod=mod, off=off, cap_len=cap_len,
                    name=name, info=inf, td=td)

def tail(r, parent, start, mat, segs, name='tail', amp=0.14, speed=0.08, ax=1, droop=0.0, tip=None, e=2.2, k=14,
         end_cap='point', spots=None):
    """Continuous tapered tail along +Z: segs = [(half width, half height, length), ...]; each segment its own
    'tail' bone (chain animation), the section at a joint matches the next one so the tail reads as one body."""
    x, y, z = start
    prev = parent
    for i, (w, h, L) in enumerate(segs):
        b = r.bone(f'{name}{i}', prev, (x, y, z), rot=(droop, 0, 0), anim='tail', i=i, amp=amp, speed=speed, ax=ax)
        w2, h2 = (segs[i + 1][0], segs[i + 1][1]) if i + 1 < len(segs) else (w * 0.35, h * 0.35)
        last = i == len(segs) - 1
        m = tip if (tip and last) else mat
        loft(b, [(x, y, z - 0.4), (x, y, z + L * 0.5), (x, y, z + L + (0 if last else 0.3))], [w * 1.02, (w + w2) / 2, w2],
             [h * 1.02, (h + h2) / 2, h2], m, e=e, k=k, caps=('round', end_cap if last else 'round'), name=name)
        prev = b
        z += L
    return prev, (x, y, z)

def horn(bone, base, direction, length, r0, mat, curl=(0, 0, 0), k=10, name='horn', tines=0):
    """Tapered curved horn from base along direction, bending by curl (added to the far end)."""
    b0 = np.asarray(base, float)
    d = np.asarray(direction, float)
    d = d / np.linalg.norm(d)
    c = np.asarray(curl, float)
    pts = SC.bezier(b0 - d * 0.3, b0 + d * length * 0.5, b0 + d * length * 0.85 + c * 0.5, b0 + d * length + c, n=12)
    SC.sweep(bone, pts, lambda t: r0 * (1 - 0.85 * t ** 1.2), None, mat, k=k, caps=('round', 'point'), name=name,
             mod=lambda th, t: 1 + 0.06 * np.cos(3 * th) * (1 - t), info={'hem': False})
    for j in range(tines):
        q = pts[4 + j * 3]
        side = np.cross(d, [0, 1.0, 0])
        if np.linalg.norm(side) < 1e-6:
            side = np.array([1.0, 0, 0])
        side = side / np.linalg.norm(side)
        tip = q + (side * (0.4 + 0.2 * j) - np.array([0, 1.0, 0])) * length * 0.3
        SC.sweep(bone, [q, (q + tip) / 2, tip], lambda t: r0 * 0.5 * (1 - 0.8 * t), None, mat, k=6, caps=('round', 'point'),
                 name=name + '_tine', info={'hem': False})

def teeth(bone, a, b, n, size, mat=None, down=True, name='teeth'):
    """Row of conical teeth from point a to point b (pointing down, or up for a lower jaw)."""
    mat = mat or M('horn', '#f2efe6', tip='#d8d0c0')
    a, b = np.asarray(a, float), np.asarray(b, float)
    sgn = 1.0 if down else -1.0
    for i in range(n):
        p = a + (b - a) * (i + 0.5) / n
        L = size * (1.0 if i % 2 == 0 else 0.7)
        SC.sweep(bone, [p - (0, sgn * 0.2, 0), p + (0, sgn * L, 0)], lambda t: size * 0.35 * (1 - 0.9 * t), None, mat, k=5,
                 caps=('round', 'point'), name=name, info={'hem': False})

def limb(r, parent, name, anim, top, foot_y, x, z, rt, rf, mat, foot=None, claw=None, toes=3, bend=0.6, k=12):
    """Leg from the hip/shoulder (top) to the ground: thigh bulge, a backward bend at the hock, a paw with toes."""
    b = r.bone(name, parent, (x, top, z), anim=anim)
    yk = top + (foot_y - top) * 0.55
    pts = [(x, top - rt * 0.4, z), (x, top + (yk - top) * 0.5, z + bend * 0.4), (x, yk, z + bend), (x, foot_y - rf * 0.8, z)]
    loft(b, pts, [rt, rt * 0.9, rf * 1.1, rf], [rt * 1.1, rt, rf * 1.15, rf * 0.95], mat, k=k, caps=('round', None), name='leg')
    fm = foot or mat
    loft(b, [(x, foot_y - rf * 0.9, z + rf * 0.4), (x, foot_y - rf * 0.5, z - rf * 0.3), (x, foot_y - rf * 0.4, z - rf * 1.2)],
         [rf * 1.15, rf * 1.3, rf * 1.1], [rf * 0.75, rf * 0.6, rf * 0.45], fm, k=k, caps=('round', 'round'), name='paw')
    if claw:
        for i in range(toes):
            dx = (i - (toes - 1) / 2) * rf * 0.7
            p = np.array([x + dx, foot_y - rf * 0.35, z - rf * 1.55])
            SC.sweep(b, [p, p + (dx * 0.15, 0.25, -rf * 0.7)], lambda t: rf * 0.28 * (1 - 0.85 * t), None, claw, k=5,
                     caps=('round', 'point'), name='claw', info={'hem': False})
    return b

def fin(bone, at, U, V, outline, color, edge=None, rays=None, fork=False, glow=0.0, res=2, name='fin', d=0.45):
    """Relief fin: outline = polygon in model px in the (U, V) plane from `at` (U = along the root, V = outwards).
    rays: colour of the stiffening rays fanning from the root; edge: glowing rim colour."""
    pts = np.asarray(outline, float)
    lo = pts.min(0) - 1.5
    hi = pts.max(0) + 1.5
    W, H = int(math.ceil((hi[0] - lo[0]) * res)), int(math.ceil((hi[1] - lo[1]) * res))
    P = [((u - lo[0]) * res, (v - lo[1]) * res) for u, v in pts]
    def draw(art):
        art.poly(P, PA.mat('cloth', color, 0.0, d=d, d0=0.2, bev=2), 1)
        if rays:
            root = np.mean([P[0], P[-1]], 0)
            for q in P[1:-1]:
                art.stroke([tuple(root), tuple(q)], 0.9, PA.mat('cloth', rays, 0.0, up=0.12, outline=False), 2)
        if edge:
            for a, b in zip(P[1:-2], P[2:-1]):
                art.stroke([a, b], 1.0, PA.mat('energy', edge, glow or 0.6, up=0.1, outline=False), 3)
    U, V = np.asarray(U, float), np.asarray(V, float)
    U, V = U / np.linalg.norm(U), V / np.linalg.norm(V)
    origin = np.asarray(at, float) + U * lo[0] + V * lo[1]
    return SC.relief(bone, draw, W, H, origin, U, V, M('fin', color), name=name, res=res)

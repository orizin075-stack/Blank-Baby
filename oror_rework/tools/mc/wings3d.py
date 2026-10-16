"""Sculpted wings: layered feather fans and bat/dragon membranes as bevelled relief plates (2x pixel art),
in two jointed halves (arm + hand) so the wing beats and folds like the box wings did."""
import math
import numpy as np
import pixart as PA
import sculpt as SC
from colors import hexc, mix, shade

def _pm(style, color, glow=0.0, **kw):
    return PA.mat(style, color, glow=glow, **kw)

def feather(art, base, ang, L, w, col, tip, z, glow=0.0, shaft=None, d=0.7):
    du, dv = math.cos(ang), math.sin(ang)
    nu, nv = -dv, du
    bx, by = base
    pts = [(bx + nu * w * 0.45, by + nv * w * 0.45),
           (bx + du * L * 0.62 + nu * w * 0.55, by + dv * L * 0.62 + nv * w * 0.55),
           (bx + du * L * 0.9 + nu * w * 0.3, by + dv * L * 0.9 + nv * w * 0.3),
           (bx + du * L, by + dv * L),
           (bx + du * L * 0.9 - nu * w * 0.32, by + dv * L * 0.9 - nv * w * 0.32),
           (bx + du * L * 0.6 - nu * w * 0.5, by + dv * L * 0.6 - nv * w * 0.5),
           (bx - nu * w * 0.45, by - nv * w * 0.45)]
    art.poly(pts, _pm('cloth', col, 0.0, d=d), z)
    if tip:
        tpts = [(bx + du * L * 0.68 + nu * w * 0.52, by + dv * L * 0.68 + nv * w * 0.52), pts[2], pts[3], pts[4],
                (bx + du * L * 0.68 - nu * w * 0.48, by + dv * L * 0.68 - nv * w * 0.48)]
        art.poly(tpts, _pm('cloth', tip, glow, d=d), z)
    if shaft:
        art.stroke([(bx, by), (bx + du * L * 0.8, by + dv * L * 0.8)], 0.7, _pm('cloth', shaft, 0.0, up=0.1, outline=False), z + 0.5)

def feather_half(span, height, mat, outer, side):
    """Drawing callback for one half of a feather wing, canvas x outward from the joint."""
    col = mat['color']
    tip = mat.get('tip')
    glow = 0.55 if mat.get('glow') else 0.0
    light = mix(col, '#ffffff', 0.35)
    dark = shade(col, 0.78)
    W, H = int(span * 2) + 6, int(height * 2) + 8
    def draw(art):
        top = 5.0
        # leading edge (arm / hand bone with coverts)
        edge = [(0.0, top + 1.5), (W * 0.5, top - 0.5 if not outer else top), (W - 3.0, top + (1.5 if not outer else 3.5))]
        art.stroke(edge, 3.2, _pm('cloth', dark, 0.0, d=1.1, d0=0.5, bev=2), 6)
        n = 7 if not outer else 8
        for i in range(n):
            t = (i + 0.5) / n
            bx = 1.5 + t * (W - 6)
            by = top + 1.6 + (0.0 if not outer else 2.2 * t)
            if not outer:
                ang = math.radians(92 - 14 * t)
                L = height * 2 * (0.72 + 0.12 * math.sin(t * math.pi))
            else:
                ang = math.radians(82 - 52 * t)
                L = height * 2 * (0.86 + 0.24 * t)
            feather(art, (bx, by), ang, L, 4.6, dark if i % 2 else col, tip, 2 + (i % 2) * 0.2, glow, shaft=light, d=0.55)
        # middle layer: shorter feathers over the long ones
        for i in range(n):
            t = (i + 0.3) / n
            bx = 1.0 + t * (W - 6)
            by = top + 1.4 + (0.0 if not outer else 2.0 * t)
            ang = math.radians(88 - (10 if not outer else 40) * t)
            feather(art, (bx, by), ang, height * 2 * 0.42, 4.2, col, None, 4, glow, shaft=None, d=0.75)
        # coverts: two scalloped rows along the edge
        for row in range(2):
            m = int((W - 4) / 2.6)
            for i in range(m):
                bx = 1.5 + i * 2.6 + row * 1.3
                by = top + 1.0 + row * 2.2 + (0 if not outer else 2.0 * i / m)
                art.ell(bx, by + 1.6, 1.6, 2.2, _pm('cloth', light if row == 0 else col, 0.0, d=0.9), 7 + row * 0.1)
    return draw, W, H

def membrane_half(span, height, mat, bone_mat, outer, side):
    col = mat['color']
    acc = mat.get('accent')
    bcol = (bone_mat or mat)['color']
    glow = 0.0
    W, H = int(span * 2) + 6, int(height * 2) + 8
    def draw(art):
        top = 4.0
        if not outer:
            pts = [(0, top), (W - 2, top), (W - 2, H * 0.62), (W * 0.65, H * 0.48), (W * 0.32, H * 0.72), (0, H * 0.55)]
            art.poly(pts, _pm('cloth', col, 0.0, d=0.3), 1)
            art.stroke([(0, top + 1), (W - 1, top)], 2.8, _pm('cloth', bcol, 0.0, d=0.9, d0=0.4, bev=2), 5)
            if acc:
                for k in range(3):
                    art.curve((W * 0.2 * (k + 1), top + 2), (W * 0.22 * (k + 1), H * 0.35), (W * 0.2 * (k + 1) + 2, H * 0.55), 0.6,
                              _pm('energy', acc, 0.7, d=0.35, outline=False), 3)
        else:
            tips = []
            for k in range(4):
                a = math.radians(-6 + 28 * k)
                L = (W - 4) * (1.0 - 0.13 * k)
                tips.append((1 + math.cos(a) * L, top + math.sin(a) * L * 0.95 + 1))
            poly = [(0, top)]
            for k, tp in enumerate(tips):
                poly.append(tp)
                if k < len(tips) - 1:
                    nx = tips[k + 1]
                    poly.append(((tp[0] + nx[0]) / 2 * 0.72, (tp[1] + nx[1]) / 2 * 0.78 + 1))
            poly.append((0, H * 0.62))
            art.poly(poly, _pm('cloth', col, 0.0, d=0.3), 1)
            for tp in tips:
                art.stroke([(0.5, top + 0.5), tp], 2.0, _pm('cloth', bcol, 0.0, d=0.85, d0=0.35, bev=2), 5, taper=(2.6, 0.9))
                art.dot(tp[0], tp[1], _pm('cloth', mat.get('accent', shade(bcol, 0.6)), 0.0, d=0.9), 6, r=0.8)
    return draw, W, H

def wing(rig, parent, side, at, kind, mat, span=12.0, height=10.0, mat2=None, rest=0.45):
    x, y, z = at
    nm = 'wing_r' if side < 0 else 'wing_l'
    root = rig.bone(nm, parent, (x, y, z), rot=(0.12, side * -rest, side * -0.18), anim=nm, amp=0.18, speed=0.12)
    S = float(span)
    Hh = float(height)
    inner = S * 0.48
    outer = S - inner + 1.0
    U = np.array([side, 0.0, 0.0])
    V = np.array([0.0, 1.0, 0.0])
    if kind in ('feather', 'membrane'):
        if kind == 'feather':
            d1, W1, H1 = feather_half(inner, Hh * 0.8, mat, False, side)
            d2, W2, H2 = feather_half(outer, Hh, mat, True, side)
        else:
            d1, W1, H1 = membrane_half(inner, Hh * 0.85, mat, mat2, False, side)
            d2, W2, H2 = membrane_half(outer, Hh, mat, mat2, True, side)
        # canvas x runs outward; place the inner half at the root, slightly behind the body
        o1 = np.array([x, y - 2.5, z + 0.3])
        SC.relief(root, d1, W1, H1, o1, U, V, mat, name='wing_in')
        tip = rig.bone(nm + '_tip', root, (x + side * inner, y, z + 0.3), rot=(0, side * -0.32, side * -0.18), anim='sway', ax=1,
                       amp=0.06, speed=0.12)
        o2 = np.array([x + side * (inner - 0.8), y - 2.5 - 0.2, z + 0.15])
        SC.relief(tip, d2, W2, H2, o2, U, V, mat, name='wing_out')
    elif kind == 'mech':
        for k in range(4):
            px = x + side * (1.5 + k * 2.8)
            SC.crbox(root, (px, y + Hh * (0.35 - 0.05 * k), z + 0.3 * k), (2.2, Hh * (1 - 0.15 * k), 0.8),
                     mat if k % 2 == 0 else (mat2 or mat), radius=0.35, name='plate')
    elif kind == 'light':
        for k in range(5):
            px = x + side * S * (0.12 + 0.19 * k)
            L = Hh * (1 - 0.12 * k)
            SC.sweep(root, [(px, y - 2 + k, z + 0.25 * k), (px + side * 1.2, y - 2 + k + L * 0.6, z + 0.25 * k),
                            (px + side * 2.0, y - 2 + k + L, z + 0.25 * k)], lambda t: 0.7 * (1 - 0.8 * t ** 1.5), 0.18,
                     dict(mat, glow=True), k=8, up=(0, 0, 1), caps=('round', 'point'), name='blade', info={'hem': False})
    return root

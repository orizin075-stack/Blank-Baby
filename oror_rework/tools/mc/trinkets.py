"""Small sculpted objects: floating crystals, stars, cards, petals, gears, books, vials, toys and the
orbiting rings of them that many characters carry."""
import math
import numpy as np
import pixart as PA
import sculpt as SC
from colors import hexc, mix, shade

def crystal(bone, c, r, mat, long=1.6, sides=6, name='crystal'):
    c = np.asarray(c, float)
    SC.sweep(bone, [c + (0, -r * long, 0), c + (0, -r * 0.3, 0), c + (0, r * 0.5, 0), c + (0, r * long * 0.8, 0)],
             [0.02, r, r * 0.92, 0.02], None, dict(mat), e=2.0, k=sides, caps=(None, None), name=name, info={'hem': False})

def sphere(bone, c, r, mat, name='orb'):
    c = np.asarray(c, float)
    SC.sweep(bone, [c + (0, -r * 0.55, 0), c + (0, r * 0.55, 0)], r * 0.84, None, dict(mat), k=14, caps=('round', 'round'),
             cap_len=r * 0.45, name=name, info={'hem': False})

def star_plate(bone, c, r, mat, shape='star', normal=(0, 0, -1), name='star'):
    col = mat['color']
    glow = 0.9 if mat.get('glow') else 0.0
    res = 2
    W = H = int(round(r * 2 * res)) + 4
    cx = cy = W / 2
    def draw(art):
        R = r * res
        if shape == 'star':
            pts = []
            for k in range(10):
                a = -math.pi / 2 + math.pi * k / 5
                rr = R if k % 2 == 0 else R * 0.45
                pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
            art.poly(pts, PA.mat('energy' if glow else 'metal', col, glow, d=0.9, d0=0.3, bev=2), 2)
        elif shape == 'diamond':
            art.poly([(cx, cy - R), (cx + R * 0.62, cy), (cx, cy + R), (cx - R * 0.62, cy)], PA.mat('gem', col, glow or 0.6, d=0.9, d0=0.3, bev=2), 2)
        elif shape == 'leaf':
            art.poly([(cx - R * 0.9, cy + R * 0.5), (cx - R * 0.2, cy - R * 0.6), (cx + R * 0.9, cy - R * 0.5), (cx + R * 0.2, cy + R * 0.6)],
                     PA.mat('cloth', col, glow, d=0.6, d0=0.2, bev=2), 2)
            art.stroke([(cx - R * 0.8, cy + R * 0.45), (cx + R * 0.8, cy - R * 0.45)], 0.7, PA.mat('cloth', shade(col, 0.7), glow, up=0.1), 3)
        else:
            art.ell(cx, cy, R, R, PA.mat('energy', col, glow, d=0.8, d0=0.3, bev=2), 2)
    n = np.asarray(normal, float)
    U = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 0, 1.0])
    V = np.array([0, 1.0, 0])
    at = np.asarray(c, float) - U * (W / 2 / res) - V * (H / 2 / res) - n * 0.0
    return SC.relief(bone, draw, W, H, at, U, V, mat, name=name, res=res)

def card(bone, c, w, h, mat, name='card'):
    SC.crbox(bone, c, (w, h, 0.35), mat, radius=0.12, name=name)

def gear(bone, c, r, mat, teeth=8, name='gear'):
    c = np.asarray(c, float)
    def mod(th, t):
        return 1 + 0.14 * (np.cos(teeth * th) > 0.3)
    SC.sweep(bone, [c + (0, 0, -0.35), c + (0, 0, 0.35)], r, None, dict(mat), e=2.0, k=teeth * 6, up=(0, -1, 0), mod=mod,
             caps=('flat', 'flat'), name=name, info={'hem': False})

def book(bone, c, mat, page, w=3.0, h=4.0, d=1.2, name='book'):
    cx, cy, cz = c
    SC.crbox(bone, (cx, cy, cz), (w, h, d * 0.7), page, radius=0.15, name=name + '_pages')
    for sgn in (-1, 1):
        SC.crbox(bone, (cx + 0.15, cy, cz + sgn * d * 0.45), (w + 0.4, h + 0.4, 0.3), mat, radius=0.15, name=name + '_cover')
    SC.sweep(bone, [(cx - w / 2 - 0.1, cy - h / 2 - 0.2, cz), (cx - w / 2 - 0.1, cy + h / 2 + 0.2, cz)], 0.35, d * 0.6, mat, k=10,
             caps=('flat', 'flat'), name=name + '_spine', info={'hem': False})

def vial(bone, c, glass, liquid, r=0.55, L=2.0, name='vial'):
    cx, cy, cz = c
    SC.lathe(bone, (cx, cz), [(cy - L / 2 - 0.2, r * 0.45), (cy - L / 2 + 0.3, r * 0.5), (cy - L / 2 + 0.6, r), (cy + L / 2, r)],
             dict(liquid, glow=True), k=10, caps=(None, 'round'), name=name, info={'hem': False})
    SC.lathe(bone, (cx, cz), [(cy - L / 2 - 0.6, r * 0.42), (cy - L / 2 - 0.2, r * 0.42)], {'type': 'wood', 'color': '#8a6a4a'}, k=8,
             caps=('flat', None), name=name + '_cork', info={'hem': False})

def toy(bone, c, mat, kind, size):
    if kind == 'star':
        return star_plate(bone, c, size, mat)
    if kind == 'card':
        return card(bone, c, size * 0.8, size * 1.2, mat)
    return SC.crbox(bone, c, (size, size, size), mat, radius=size * 0.25, name='toy')

def orbiters(rig, parent, center, mat, count=4, radius=10.0, size=1.6, speed=0.035, name='orbit', bob=0.6, shapes=None):
    cx, cy, cz = center
    hub = rig.bone(name, parent, (cx, cy, cz), anim='spin', speed=speed)
    for i in range(count):
        a = 2 * math.pi * i / count
        px, pz = cx + math.cos(a) * radius, cz + math.sin(a) * radius
        b = rig.bone(f'{name}_{i}', hub, (px, cy, pz), anim='float', amp=bob, speed=0.08, phase=i * 1.7)
        s = shapes[i % len(shapes)] if shapes else (size, size, size)
        m = mat if not isinstance(mat, list) else mat[i % len(mat)]
        t = m.get('type')
        big = max(s[0], s[1])
        out = np.array([math.cos(a), 0, math.sin(a)])
        if t == 'plane':
            star_plate(b, (px, cy, pz), big * 0.6 + 0.3, m, shape=m.get('shape', 'star'), normal=tuple(out))
        elif t == 'gem':
            crystal(b, (px, cy, pz), max(0.55, big * 0.42), m, long=1.7 if s[1] > s[0] else 1.4)
        elif t in ('slime', 'energy'):
            sphere(b, (px, cy, pz), max(0.6, big * 0.5), m)
        elif s[2] == 0:
            card(b, (px, cy, pz), max(1.2, s[0]), max(1.6, s[1]), m)
        elif t == 'metal' and m.get('pattern') == 'rings':
            gear(b, (px, cy, pz), max(1.0, big * 0.5), m)
        else:
            SC.crbox(b, (px, cy, pz), tuple(max(0.8, v) for v in s), m, radius=0.3, name='orb')
    return hub


def wheel(bone, center, R, rim, runes=None, hub=None, spokes=8, teeth=12):
    """Great wheel worn on the back (ouroboros): rim with teeth, spokes, an inner rune ring and a hub gem,
    in the bone's XY plane facing +Z."""
    cx, cy, cz = center
    SC.torus(bone, center, R, 0.42, dict(rim), axis='z', k=8, n=48, name='wheel_rim')
    SC.torus(bone, center, R - 0.9, 0.22, dict(rim), axis='z', k=6, n=44, name='wheel_rim2')
    for i in range(teeth):
        a = 2 * math.pi * i / teeth
        d = np.array([math.cos(a), math.sin(a), 0.0])
        base = np.array(center) + d * (R + 0.3)
        SC.sweep(bone, [base, base + d * 1.1], lambda t: 0.45 * (1 - 0.85 * t), 0.3, dict(rim), k=6, up=(0, 0, 1),
                 caps=('round', 'point'), name='wheel_tooth', info={'hem': False})
    for i in range(spokes):
        a = 2 * math.pi * (i + 0.5) / spokes
        d = np.array([math.cos(a), math.sin(a), 0.0])
        SC.sweep(bone, [np.array(center) + d * 0.9, np.array(center) + d * (R - 0.9)], [0.22, 0.16], None, dict(rim), k=6,
                 caps=('round', 'round'), name='wheel_spoke', info={'hem': False})
    if runes:
        SC.torus(bone, (cx, cy, cz + 0.15), R * 0.62, 0.2, dict(runes, glow=True), axis='z', k=6, n=36, name='wheel_runes')
    if hub:
        crystal(bone, (cx, cy, cz - 0.1), 0.9, hub, long=1.2)

def poly_ring(bone, center, R, sides, thick, mat, axis='y'):
    """Polygonal halo (a heptagram-like geometric ring), closed path with crisp corners."""
    cx, cy, cz = center
    pts = []
    for i in range(sides):
        a0, a1 = 2 * math.pi * i / sides, 2 * math.pi * (i + 1) / sides
        for t in np.linspace(0, 1, 6)[:-1]:
            x = (1 - t) * math.cos(a0) + t * math.cos(a1)
            z = (1 - t) * math.sin(a0) + t * math.sin(a1)
            pts.append((cx + R * x, cy, cz + R * z) if axis == 'y' else (cx + R * x, cy + R * z, cz))
    up = (0, -1, 0) if axis == 'y' else (0, 0, 1)
    SC.sweep(bone, pts, thick, thick * 0.6, dict(mat), k=6, closed=True, up=up, caps=None, name='poly_ring', info={'hem': False})

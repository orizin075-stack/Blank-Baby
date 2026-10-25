"""OROR's non-human characters rebuilt as Ice and Fire style cube models (0.17.27).

The lofted sculpts (creatures_sc.py) became chains of thin slabs in the cube pipeline: striped bodies, pin-point
eyes and no mouths. These are modelled the way Ice and Fire's dragons and Minecraft's own mobs are: a few large,
deliberate boxes per body part, a head with a separate snout, brow and lower jaw, eyes as small plates standing
proud of the head (iapaint draws rim, iris, pupil and catchlight), a mouth interior with real teeth, wings as spars
over a membrane cut to shape, tails as chains of tapering boxes.

Model space as everywhere in this toolkit: pixels, y down (the ground is y = 24), the front is -z. Bone animation
names are the ones RigModel plays (root, breath, head, jaw, leg_r / leg_l, knee, tail with i, sway, float, spin,
pulse, liquid, blink).
"""
import math
import numpy as np
import bb
import sculpt as SC
from paint import M
from rig import Rig

RECIPES = {}


def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn


# ====================================================================================================== the kit

def rig(key, td=2):
    r = Rig(key)
    SC.Sculpt(r, td=td)
    return r


def box(bone, lo, hi, mat, **kw):
    lo, hi = np.asarray(lo, float), np.asarray(hi, float)
    return bb.cube(bone, np.minimum(lo, hi), np.abs(hi - lo), mat, **kw)


def cbox(bone, c, size, mat, **kw):
    return bb.ccube(bone, c, size, mat, **kw)


def rbox(bone, lo, hi, mat, bevel=1.0, **kw):
    """A box with chamfered edges: three crossing boxes, each full along one axis and cut back by `bevel` on the
    other two (how Blockbench modellers round off a whale's head or a beast's chest)."""
    lo, hi = np.minimum(lo, hi).astype(float), np.maximum(lo, hi).astype(float)
    b = np.minimum(bevel, (hi - lo) * 0.3)
    for i in range(3):
        l, h = lo + b, hi - b
        l[i], h[i] = lo[i], hi[i]
        box(bone, l, h, mat, **kw)


def mirror(fn, *pts):
    """Calls fn(sx, ...) for sx = -1 (the right side, x < 0) and +1."""
    return [fn(sx) for sx in (-1, 1)]


def seg(bone, p0, p1, w, d, mat, up=(0, -1, 0), **kw):
    return bb.beam(bone, p0, p1, w, d, mat, up=up, **kw)


def chain_boxes(bone, pts, w0, w1, mat, d0=None, d1=None, up=(0, -1, 0)):
    """Tapering boxes through pts (horns, spars, claws)."""
    n = len(pts) - 1
    d0 = w0 if d0 is None else d0
    d1 = w1 if d1 is None else d1
    for i in range(n):
        t = i / max(1, n)
        t2 = (i + 1) / max(1, n)
        w = w0 + (w1 - w0) * (t + t2) / 2
        d = d0 + (d1 - d0) * (t + t2) / 2
        seg(bone, pts[i], pts[i + 1], w, d, mat, up=up, ext=min(w, d) * 0.5)


def eye(bone, c, w, h, side, mat, depth=0.3):
    """An eye plate centred on c, standing depth/2 proud of the surface it sits on."""
    m = dict(mat, out=side)
    if side in ('right', 'left'):
        size = (depth, h, w)
    elif side == 'front':
        size = (w, h, depth)
    else:
        size = (w, depth, h)
    return cbox(bone, c, size, m, td=4, info={'out': side})


def teeth(bone, x, y0, z0, z1, n, size, mat, down=True):
    """A row of teeth along z at side x: hanging from y0 (down) or standing on it."""
    for k in range(n):
        z = z0 + (z1 - z0) * (k + 0.5) / n
        h = size * (1.25 if k % 2 == 0 else 0.9)
        lo = (x - size / 2, y0, z - size / 2)
        hi = (x + size / 2, y0 + (h if down else -h), z + size / 2)
        box(bone, lo, hi, mat)


def teeth_x(bone, z, y0, x0, x1, n, size, mat, down=True):
    """A row of teeth across x at depth z (a front-facing maw)."""
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n
        h = size * (1.3 if k % 2 == 0 else 0.85)
        box(bone, (x - size / 2, y0, z - size / 2), (x + size / 2, y0 + (h if down else -h), z + size / 2), mat)


def claws(bone, foot_front_z, y, x, n, size, mat, spread=1.1):
    for k in range(n):
        cx = x + (k - (n - 1) / 2) * spread
        seg(bone, (cx, y - size * 0.5, foot_front_z + 0.2), (cx, y + 0.05, foot_front_z - size * 1.2), size * 0.55, size * 0.6, mat,
            up=(0, 0, -1))


def leg(r, parent, name, anim, hip, knee, ankle, w_upper, w_lower, mat, foot=(2.6, 1.2, 3.2), claw=None, toes=3, knee_amp=None):
    """A two-bone leg: thigh from hip to knee (bone `name`, anim leg_r / leg_l), shin from knee to ankle (bone
    name+'_low', anim knee), a foot box under the ankle with claws at its front."""
    up = r.bone(name, parent, hip, anim=anim)
    seg(up, hip, knee, w_upper, w_upper * 1.1, mat, up=(0, 0, -1), ext=w_upper * 0.4)
    low = r.bone(name + '_low', up, knee, anim='knee')
    seg(low, knee, ankle, w_lower, w_lower, mat, up=(0, 0, -1), ext=w_lower * 0.5)
    fw, fh, fl = foot
    ax, ay, az = ankle
    box(low, (ax - fw / 2, ay - fh / 2, az - fl * 0.7), (ax + fw / 2, ay + fh / 2, az + fl * 0.3), mat)
    if claw:
        claws(low, az - fl * 0.7, ay + fh / 2, ax, toes, min(1.0, fw / toes * 1.1), claw, spread=fw / toes)
    return up, low


def tail(r, parent, start, lengths, widths, mat, droop=0.12, lift=0.0, spikes=None, amp=0.12, speed=0.07, name='tail'):
    """Chain of tapering boxes going back (+z); each link its own bone (anim tail, i = index)."""
    p = np.asarray(start, float)
    bone = parent
    ends = []
    for i, (L, w) in enumerate(zip(lengths, widths)):
        bone = r.bone(f'{name}{i + 1}', bone, tuple(p), anim='tail', i=i, amp=amp, speed=speed)
        ang = droop * (1 - i / len(lengths)) - lift * (i / len(lengths))
        q = p + np.array([0.0, math.sin(ang) * L, math.cos(ang) * L])
        seg(bone, p, q, w, w * 0.9, mat, up=(0, -1, 0), ext=w * 0.3)
        if spikes and i < len(lengths) - 1:
            mid = (p + q) / 2
            seg(bone, mid + np.array([0, -w * 0.4, 0]), mid + np.array([0, -w * 0.4 - max(0.8, w * 0.45), L * 0.25]),
                max(0.35, w * 0.18), max(0.6, w * 0.3), spikes, up=(0, 0, 1))
        ends.append((bone, q))
        p = q
    return ends


def wing(r, parent, side, shoulder, arm, fingers, membrane, spar_mat, rot, amp=0.32, speed=0.11, accent=None, glow=False,
         name=None, td=None):
    """A bat / dragon wing laid flat (y = shoulder y) and raised by the bone's rest rotation `rot`.
    arm: [elbow, wrist] (x, z) offsets; fingers: tip (x, z) points. x is mirrored by side (-1 right, +1 left)."""
    sx = side
    nm = name or ('wing_r' if sx < 0 else 'wing_l')
    b = r.bone(nm, parent, shoulder, rot=(rot[0], rot[1] * sx, rot[2] * -sx), anim='sway', ax=2, amp=amp, speed=speed,
               phase=0.0)
    x0, y, z0 = shoulder
    P = lambda xz: (x0 + sx * xz[0], y, z0 + xz[1])
    elbow, wrist = P(arm[0]), P(arm[1])
    chain_boxes(b, [(x0, y, z0), elbow, wrist], 1.6, 1.0, spar_mat)
    tips = [P(t) for t in fingers]
    for t in tips:
        chain_boxes(b, [wrist, t], 0.7, 0.3, spar_mat)
    claws_at = (wrist[0] + sx * 0.4, y - 0.4, wrist[2] - 1.0)
    seg(b, wrist, claws_at, 0.5, 0.5, M('horn', '#d8cfb8'))
    # membrane: one plate under the spars, cut to the outline shoulder - elbow - wrist - tips - body
    body_end = P((1.2, fingers[-1][1] * 0.75))
    outline = [(x0, z0), (elbow[0], elbow[2]), (wrist[0], wrist[2])]
    for i, t in enumerate(tips):
        outline.append((t[0], t[2]))
        if i + 1 < len(tips):
            # scallop between fingers
            n = tips[i + 1]
            mid = ((t[0] + n[0]) / 2, (t[2] + n[2]) / 2)
            inward = ((mid[0] + wrist[0]) / 2, (mid[1] + wrist[2]) / 2)
            outline.append(((mid[0] * 0.72 + inward[0] * 0.28), (mid[1] * 0.72 + inward[1] * 0.28)))
    outline.append((body_end[0], body_end[2]))
    xs = [p[0] for p in outline]
    zs = [p[1] for p in outline]
    veins = [(wrist[0], wrist[2], t[0], t[2]) for t in tips] + [(elbow[0], elbow[2], body_end[0], body_end[2])]
    mat = M('wingskin', membrane, poly=outline, axes='xz', veins=veins, accent=accent, glow=glow)
    box(b, (min(xs), y + 0.25, min(zs)), (max(xs), y + 0.25, max(zs)), mat, td=td)
    return b


def spikes_row(bone, z0, z1, n, y, h0, h1, mat, w=0.9, lean=0.6):
    for k in range(n):
        t = k / max(1, n - 1)
        z = z0 + (z1 - z0) * t
        h = h0 + (h1 - h0) * t
        seg(bone, (0, y + 0.3, z), (0, y - h, z + h * lean), w, w * 1.6, mat, up=(0, 0, 1))


# ==================================================================================================== dragons

def dragon_head(r, neck_bone, at, scale, skin, belly_mat, eye_mat, horn_mat, mouth_mat, tooth_mat, brow=None, open_jaw=0.16,
                horns='swept', frill=None):
    """Ice and Fire dragon head: skull, snout, brow ridges, nostrils, two rows of teeth, a hinged lower jaw.
    at: the skull's back-centre top (x, y, z); scale: 1 = a 6-wide skull."""
    s = scale
    ax, ay, az = at
    head = r.bone('head', neck_bone, (ax, ay + 2.5 * s, az), anim='head')
    # skull and snout
    box(head, (-3 * s, ay, az - 6 * s), (3 * s, ay + 4.6 * s, az), skin)
    box(head, (-2.1 * s, ay + 1.0 * s, az - 13 * s), (2.1 * s, ay + 3.7 * s, az - 6 * s), skin,
        faces={'bottom': mouth_mat})
    box(head, (-1.6 * s, ay + 0.7 * s, az - 12.6 * s), (1.6 * s, ay + 1.0 * s, az - 8.5 * s), skin)       # snout ridge
    # nostrils
    for sx in (-1, 1):
        box(head, (sx * 1.0 * s - 0.35 * s, ay + 0.95 * s, az - 12.6 * s), (sx * 1.0 * s + 0.35 * s, ay + 1.05 * s, az - 11.8 * s),
            M('simple', '#120c10'))
    # brow ridges over the eyes, angled down to the front: the "frown" every Ice and Fire dragon has
    brow = brow or skin
    for sx in (-1, 1):
        box(head, (sx * 1.0 * s, ay - 0.5 * s, az - 6.4 * s), (sx * 3.4 * s, ay + 0.7 * s, az - 3.0 * s), brow,
            rot=(-0.18, sx * 0.12, 0), pivot=(sx * 2.2 * s, ay, az - 4.7 * s))
    # eyes on the sides of the skull under the brows
    for sx in (-1, 1):
        eye(head, (sx * 3.0 * s, ay + 1.6 * s, az - 4.8 * s), 2.8 * s, 1.5 * s, 'left' if sx > 0 else 'right', eye_mat)
    # upper teeth
    for sx in (-1, 1):
        teeth(head, sx * 1.75 * s, ay + 3.7 * s, az - 12.4 * s, az - 6.6 * s, 5, 0.55 * s, tooth_mat, down=True)
    # cheek plates and horns
    for sx in (-1, 1):
        box(head, (sx * 2.6 * s, ay + 2.4 * s, az - 2.8 * s), (sx * 3.5 * s, ay + 4.6 * s, az + 0.4 * s), belly_mat)
        if horns == 'swept':
            chain_boxes(head, [(sx * 2.0 * s, ay + 0.2 * s, az - 0.6 * s), (sx * 2.7 * s, ay - 1.6 * s, az + 2.6 * s),
                               (sx * 3.0 * s, ay - 2.6 * s, az + 5.6 * s), (sx * 2.7 * s, ay - 2.9 * s, az + 8.2 * s)],
                        1.5 * s, 0.45 * s, horn_mat)
            chain_boxes(head, [(sx * 3.1 * s, ay + 3.0 * s, az - 0.5 * s), (sx * 4.0 * s, ay + 3.2 * s, az + 2.4 * s),
                               (sx * 4.4 * s, ay + 2.8 * s, az + 4.4 * s)], 0.9 * s, 0.3 * s, horn_mat)
        elif horns == 'crown':
            for k, (dx, dz, L) in enumerate(((1.2, 0.0, 4.6), (2.4, -1.2, 3.6), (3.2, -2.8, 2.6))):
                chain_boxes(head, [(sx * dx * s, ay + 0.3 * s, az + dz * s), (sx * (dx + 0.5) * s, ay - L * 0.7 * s, az + (dz + L * 0.6) * s),
                                   (sx * (dx + 0.6) * s, ay - L * s, az + (dz + L * 1.1) * s)], 1.0 * s, 0.3 * s, horn_mat)
    if frill:
        for sx in (-1, 1):
            for k in range(3):
                seg(head, (sx * 3.2 * s, ay + (1.0 + k * 1.2) * s, az - 0.2 * s),
                    (sx * (5.0 + k * 0.4) * s, ay + (0.2 + k * 1.5) * s, az + (2.6 - k * 0.3) * s), 0.35 * s, 1.0 * s, frill, up=(sx, 0, 0))
    # lower jaw on its own hinge, left a little open so the teeth and mouth show
    jaw = r.bone('jaw', head, (0, ay + 4.0 * s, az - 2.5 * s), rot=(open_jaw, 0, 0), anim='jaw')
    box(jaw, (-1.95 * s, ay + 3.75 * s, az - 12.4 * s), (1.95 * s, ay + 5.1 * s, az - 2.5 * s), belly_mat,
        faces={'top': mouth_mat})
    box(jaw, (-0.6 * s, ay + 5.1 * s, az - 11.5 * s), (0.6 * s, ay + 5.6 * s, az - 8.0 * s), skin)            # chin
    for sx in (-1, 1):
        teeth(jaw, sx * 1.55 * s, ay + 3.75 * s, az - 12.0 * s, az - 6.6 * s, 4, 0.5 * s, tooth_mat, down=False)
    return head, jaw


def dragon(key, skin_c, belly_c, accent, eye_c, horn_c, membrane_c, gem=None, mood='fierce', mech=False, wing_glow=False,
           vane=None):
    r = rig(key)
    pat = dict(pattern='dragon', accent=accent, pattern_glow=True, glow_amount=0.5) if mech else {}
    skin = M('metal', skin_c, accent=accent) if mech else M('scale', skin_c, belly=belly_c)
    belly = M('metal', belly_c) if mech else M('scale', belly_c, belly=belly_c)
    horn = M('horn', horn_c, tip=accent, glow=True)
    eye_m = M('eye', eye_c, pupil='slit' if not mech else 'ring', mood=mood, lid=skin_c)
    mouth = M('mouth', '#4a1220')
    tooth = M('tooth', '#efe6d2')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 13, 2), anim='breath')
    # torso: chest, belly, hips
    box(body, (-4.6, 8.8, -9.5), (4.6, 17.2, -1.0), skin)
    box(body, (-4.2, 9.4, -1.0), (4.2, 17.6, 8.0), skin)
    box(body, (-3.8, 9.6, 8.0), (3.8, 16.2, 13.0), skin)
    box(body, (-3.6, 17.2, -8.6), (3.6, 17.9, 7.6), belly)                       # belly plates
    spikes_row(body, -8.0, 11.5, 7, 8.8, 2.4, 1.4, horn)
    if gem:
        for (x, y, z, sz) in ((-4.7, 11.0, -6.0, 1.4), (4.7, 11.0, -6.0, 1.4), (-4.3, 12.5, 3.0, 1.0), (4.3, 12.5, 3.0, 1.0),
                              (0, 8.6, -2.0, 1.2), (0, 9.2, 6.0, 1.0)):
            cbox(body, (x, y, z), (sz, sz, sz), M('gem', gem[int(abs(x * 3 + z)) % len(gem)], glow=True), rot=(0.3, 0.6, 0.2))
    if mech:
        for sx in (-1, 1):                                                   # light seams and thruster vents
            box(body, (sx * 4.62, 11.0, -8.0), (sx * 4.7, 11.4, 7.0), M('energy', accent, glow=True))
            box(body, (sx * 1.6 - 0.9, 8.3, 4.0), (sx * 1.6 + 0.9, 8.8, 9.0), M('metal', '#2a3038'))
            cbox(body, (sx * 1.6, 8.25, 6.5), (1.2, 0.2, 4.0), M('energy', accent, glow=True))
    # neck rising forward, then the head
    neck = r.bone('neck', body, (0, 11.5, -8.5), anim='sway', ax=1, amp=0.04, speed=0.05)
    seg(neck, (0, 12.0, -8.0), (0, 8.5, -12.5), 5.2, 5.0, skin, up=(0, 0, -1), ext=1.0)
    seg(neck, (0, 8.5, -12.5), (0, 5.0, -15.0), 4.4, 4.4, skin, up=(0, 0, -1), ext=1.0)
    spikes_row(neck, -12.0, -15.5, 2, 4.8, 1.8, 1.6, horn, lean=0.8)
    head, jaw = dragon_head(r, neck, (0, 1.2, -14.5), 1.0, skin, belly, eye_m, horn, mouth, tooth, mood != 'happy' and skin or None,
                            open_jaw=0.22 if mood == 'happy' else 0.15)
    # legs: diagonal pairs share a phase (front right with back left)
    claw = M('horn', '#d8cfb8')
    for sx in (-1, 1):
        leg(r, body, 'leg_f' + ('r' if sx < 0 else 'l'), 'leg_r' if sx < 0 else 'leg_l',
            (sx * 4.4, 13.5, -5.5), (sx * 5.0, 18.5, -7.0), (sx * 4.8, 22.6, -5.6), 2.8, 2.0, skin, foot=(2.6, 1.4, 3.2), claw=claw)
        leg(r, body, 'leg_b' + ('r' if sx < 0 else 'l'), 'leg_l' if sx < 0 else 'leg_r',
            (sx * 4.0, 13.0, 10.0), (sx * 4.8, 17.6, 7.6), (sx * 4.6, 22.6, 11.0), 3.6, 2.2, skin, foot=(2.8, 1.4, 3.4), claw=claw)
    # wings
    spar = M('horn', horn_c) if not mech else M('metal', skin_c, accent=accent)
    for sx in (-1, 1):
        wing(r, body, sx, (sx * 4.4, 9.6, -5.0), [(8.0, 1.0), (15.0, 3.5)],
             [(22.0, 9.0), (19.5, 15.0), (13.5, 17.5), (7.0, 15.5)], membrane_c, spar, rot=(0.0, 0.18, 0.55),
             accent=vane or accent, glow=wing_glow)
    # tail
    ends = tail(r, body, (0, 12.8, 12.6), [5.5, 5.5, 5.0, 4.5, 4.0, 3.6], [4.6, 3.8, 3.1, 2.5, 1.9, 1.4], skin, droop=0.18, spikes=horn)
    tip_bone, tip = ends[-1]
    tx, ty, tz = tip
    if gem:
        cbox(tip_bone, (tx, ty, tz + 1.2), (0.6, 3.6, 2.6), M('gem', gem[0], glow=True), rot=(0.0, 0.0, 0.0))
    elif mech:
        cbox(tip_bone, (tx, ty, tz + 1.2), (0.4, 3.2, 3.2), M('energy', accent, glow=True))
    return r


@recipe
def demiurgos():
    # 空創龍王 デミウルゴス: a small black dragon (about five metres) set with rainbow gems; mysterious more than
    # menacing. Amethyst eyes under heavy brows, gem-studded spine and tail spade.
    return dragon('demiurgos', '#2c2a3a', '#544a72', '#b48cff', '#c58cff', '#2a2638', '#2b2140',
                  gem=['#ff6ad5', '#6af0ff', '#ffe46a', '#7dff8a', '#a07dff'], mood='fierce', vane='#8f6ad8')


@recipe
def teia():
    # 光越天龍 テイア: a small dragon fused with machinery: a pale metal shell with cyan light seams, photon wings,
    # thrusters on the back. Cheerful big-brother: bright eyes and a grin.
    return dragon('teia', '#c9d2dc', '#8c99a8', '#6ff6ff', '#7ff6ff', '#e8eef4', '#bfe8ff', mood='happy', mech=True,
                  wing_glow=True, vane='#ff9af2')


# ================================================================================================= more parts

def fin(bone, poly, axes, at, colour, accent=None, glow=False, veins=None, td=None):
    """A flat fin or sail: a zero-thickness plate on the plane where the third axis = at, cut to `poly`
    (points in the two named axes, e.g. axes='zy' for an upright fin on the centre line)."""
    ia, ib = ['xyz'.index(c) for c in axes]
    ic = 3 - ia - ib
    P = np.asarray(poly, float)
    lo, hi = np.zeros(3), np.zeros(3)
    lo[ia], hi[ia] = P[:, 0].min(), P[:, 0].max()
    lo[ib], hi[ib] = P[:, 1].min(), P[:, 1].max()
    lo[ic] = hi[ic] = at
    mat = M('wingskin', colour, poly=[tuple(p) for p in P], axes=axes, veins=veins or [], accent=accent, glow=glow)
    return box(bone, lo, hi, mat, td=td)


def hoop(bone, c, radius, thick, mat, axis='y', n=28, depth=None):
    """A ring of tangent boxes round `axis` (rotors, halos, armillary bands)."""
    c = np.asarray(c, float)
    depth = thick if depth is None else depth
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        def at(a):
            u, v = math.cos(a) * radius, math.sin(a) * radius
            return c + {'y': np.array([u, 0, v]), 'z': np.array([u, v, 0]), 'x': np.array([0, u, v])}[axis]
        up = {'y': (0, -1, 0), 'z': (0, 0, -1), 'x': (-1, 0, 0)}[axis]
        seg(bone, at(a0), at(a1), thick, depth, mat, up=up, ext=0.15)


def ball(bone, c, r, mat, squash=(1.0, 1.0, 1.0), **kw):
    """A voxel ball: three crossing boxes, each full along one axis and cut back along the others."""
    sx, sy, sz = (2 * r * k for k in squash)
    cbox(bone, c, (sx, sy * 0.72, sz * 0.72), mat, **kw)
    cbox(bone, c, (sx * 0.72, sy, sz * 0.72), mat, **kw)
    cbox(bone, c, (sx * 0.72, sy * 0.72, sz), mat, **kw)


def feather_wing(r, parent, side, shoulder, span, feather, spar, rot, n=7, amp=0.3, speed=0.1):
    """A bird wing laid flat and raised by the rest rotation: the arm runs out along x, rows of feather plates run
    back from it, longest at the tip (primaries)."""
    sx = side
    b = r.bone('wing_r' if sx < 0 else 'wing_l', parent, shoulder, rot=(rot[0], rot[1] * sx, rot[2] * -sx), anim='sway', ax=2,
               amp=amp, speed=speed)
    x0, y, z0 = shoulder
    tip = (x0 + sx * span, y - 0.4, z0 + 2.0)
    chain_boxes(b, [(x0, y, z0), (x0 + sx * span * 0.45, y - 0.6, z0 - 0.8), tip], 1.8, 1.0, spar)
    for k in range(n):
        t = (k + 0.5) / n
        bx = x0 + sx * span * t
        bz = z0 + (-0.8 if t < 0.45 else -0.8 + 2.8 * (t - 0.45))
        L = 5.5 + 9.0 * t ** 1.4
        w = span / n * 1.25
        box(b, (bx - w / 2, y + 0.1, bz), (bx + w / 2, y + 0.45, bz + L), feather, rot=(0, sx * -0.12 * t, 0), pivot=(bx, y, bz))
        # coverts: a shorter row on top
        box(b, (bx - w / 2, y - 0.2, bz - 0.4), (bx + w / 2, y + 0.1, bz + L * 0.45), dict(feather, tip=None))
    return b


def sea_fin_bone(r, parent, name, pivot, poly, axes, at, colour, edge, rot=(0, 0, 0), ax=2, amp=0.12, speed=0.08, phase=0.0):
    b = r.bone(name, parent, pivot, rot=rot, anim='sway', ax=ax, amp=amp, speed=speed, phase=phase)
    fin(b, poly, axes, at, colour, accent=edge, veins=[(poly[0][0], poly[0][1], p[0], p[1]) for p in poly[2:-1:2]])
    return b


# ============================================================================================= sea beasts

@recipe
def enkou():
    # 災極海獣 淵煌: the edge of a shark, the speed of an orca, the dignity of a dragon. Obsidian scales with glowing
    # circuit-like marks, pale blue deep-sea eyes, an orca's white patches, a mouth full of teeth.
    r = rig('enkou')
    hide = M('scale', '#1a2232', belly='#dfe8ee', pattern='vine', accent='#7fdcff', pattern_glow=True, glow_amount=0.45)
    plain = M('scale', '#18202e', belly='#dfe8ee')
    white = M('scale', '#e6eef2', belly='#e6eef2')
    fin_c, edge = '#1e2a3c', '#7fdcff'
    horn = M('horn', '#20283a', tip='#8fe3ff', glow=True)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.5, speed=0.05)
    body = r.bone('body', root, (0, 13, 0), anim='sway', ax=1, amp=0.05, speed=0.06)
    rbox(body, (-5.6, 7.6, -10.0), (5.6, 18.6, 4.0), hide, bevel=1.4)
    rbox(body, (-4.8, 8.4, 3.0), (4.8, 17.6, 12.0), hide, bevel=1.2)
    rbox(body, (-3.6, 9.6, 11.0), (3.6, 16.4, 18.0), hide, bevel=1.0)
    box(body, (-4.8, 18.6, -9.0), (4.8, 19.2, 10.0), white)                                  # white belly
    for sx in (-1, 1):
        box(body, (sx * 5.6, 13.0, -6.0), (sx * 5.75, 18.0, 2.0), white)                        # orca flank patch
        for k in range(3):
            box(body, (sx * 5.6, 9.6, -8.6 + k * 1.3), (sx * 5.7, 13.4, -8.1 + k * 1.3), M('energy', edge, glow=True))
    fin(body, [(-5.0, 7.8), (-1.5, -2.5), (1.5, -5.5), (3.5, -4.8), (5.0, 1.0), (8.5, 7.8)], 'zy', 0.0, fin_c, accent=edge,
        veins=[(-3, 7.8, 1.5, -5.0), (1, 7.8, 3.5, -4.0)])
    for sx in (-1, 1):
        sea_fin_bone(r, body, 'fin_' + ('r' if sx < 0 else 'l'), (sx * 5.4, 17.0, -6.0),
                     [(sx * 5.4, -7.5), (sx * 11.0, -4.0), (sx * 15.5, 1.5), (sx * 13.0, 2.0), (sx * 5.4, -2.0)], 'xz', 17.2,
                     fin_c, edge, rot=(0.0, 0.0, sx * -0.35), amp=0.14, phase=sx)
    head = r.bone('head', body, (0, 13, -10), anim='head')
    rbox(head, (-5.2, 8.2, -19.0), (5.2, 17.6, -10.0), plain, bevel=1.2)
    box(head, (-4.4, 9.0, -25.0), (4.4, 15.4, -19.0), plain, faces={'bottom': M('mouth', '#3e1018')})
    box(head, (-3.0, 9.6, -28.0), (3.0, 14.6, -25.0), plain, faces={'bottom': M('mouth', '#3e1018')})
    for sx in (-1, 1):
        box(head, (sx * 1.0 - 0.4, 9.55, -27.6), (sx * 1.0 + 0.4, 9.65, -26.8), M('simple', '#06080c'))
        eye(head, (sx * 5.25, 11.6, -15.8), 3.2, 1.8, 'left' if sx > 0 else 'right',
            M('eye', '#bff4ff', pupil='round', mood='fierce', lid='#18202e'))
        box(head, (sx * 5.2, 9.4, -14.0), (sx * 5.35, 11.0, -10.6), white)                    # orca eye patch
        box(head, (sx * 1.5, 7.6, -19.5), (sx * 4.8, 8.4, -14.5), plain, rot=(-0.12, 0, 0))  # brow
        chain_boxes(head, [(sx * 3.4, 8.4, -12.0), (sx * 4.2, 6.6, -8.5), (sx * 4.5, 5.6, -4.5), (sx * 4.0, 5.4, -1.5)],
                    1.6, 0.4, horn)
        teeth(head, sx * 4.0, 15.4, -24.6, -19.6, 5, 0.75, M('tooth', '#f2ede2'), down=True)
        teeth(head, sx * 2.6, 14.6, -27.6, -25.2, 2, 0.7, M('tooth', '#f2ede2'), down=True)
    jaw = r.bone('jaw', head, (0, 16.0, -11.0), rot=(0.22, 0, 0), anim='jaw')
    box(jaw, (-4.6, 15.6, -26.8), (4.6, 18.4, -11.0), white, faces={'top': M('mouth', '#3e1018')})
    for sx in (-1, 1):
        teeth(jaw, sx * 3.8, 15.6, -26.0, -14.0, 6, 0.7, M('tooth', '#f2ede2'), down=False)
    ends = tail(r, body, (0, 13.0, 17.5), [5.5, 5.0, 4.5, 4.0], [6.0, 4.6, 3.4, 2.4], hide, droop=0.02, amp=0.18, speed=0.08)
    tb, (tx, ty, tz) = ends[-1]
    fin(tb, [(tz - 1.5, ty - 0.5), (tz + 4.0, ty - 9.5), (tz + 6.5, ty - 10.5), (tz + 3.0, ty - 2.0), (tz + 3.0, ty + 1.5),
             (tz + 6.0, ty + 7.0), (tz + 4.0, ty + 7.2), (tz - 1.5, ty + 1.0)], 'zy', 0.0, fin_c, accent=edge,
        veins=[(tz, ty, tz + 5.5, ty - 9.5), (tz, ty, tz + 4.8, ty + 6.5)])
    return r


@recipe
def bahamut():
    # 大海皇鯨 バハムート: a whale's smooth body with a dragon's scales and horns, a great sail-fin that raises the
    # tides, a coral reef and its life on the back. Gentle mediator of the sea: kind eyes, a slow smile.
    r = rig('bahamut')
    skin = M('scale', '#2e5b7c', belly='#d6ecf2', scale_size=2.2, contrast=0.55)
    pale = M('scale', '#d6ecf2', belly='#d6ecf2', pattern='stripes', accent='#b4d4e2', scale_size=2.2, contrast=0.5)
    horn = M('horn', '#f2ead8', tip='#ffd36a', glow=True)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.0, speed=0.04)
    body = r.bone('body', root, (0, 12, 0), anim='sway', ax=1, amp=0.03, speed=0.04)
    rbox(body, (-10.0, 2.6, -14.0), (10.0, 20.4, 14.0), skin, bevel=2.2)
    rbox(body, (-8.0, 19.0, -12.0), (8.0, 21.0, 12.0), pale, bevel=1.0)
    rbox(body, (-7.4, 5.2, 12.0), (7.4, 17.6, 22.0), skin, bevel=1.8)
    # the reef on the back: corals, kelp and anemones
    reef = [('#ff7aa8', -4.0, -6.0, 3.2), ('#ffb35c', 3.5, -3.0, 2.6), ('#b07aff', -1.0, 4.0, 3.6), ('#ff8a6a', 5.0, 7.5, 2.4),
            ('#7fe0c0', -5.5, 8.0, 2.8), ('#ffd36a', 1.5, -9.0, 2.0)]
    for col, x, z, h in reef:
        cm = M('simple', col)
        box(body, (x - 0.6, 2.6 - h, z - 0.6), (x + 0.6, 2.6, z + 0.6), cm)
        box(body, (x - 1.8, 2.6 - h * 0.7, z - 0.4), (x - 0.6, 2.6 - h * 0.55, z + 0.4), cm)
        box(body, (x + 0.6, 2.6 - h * 0.9, z - 0.4), (x + 1.6, 2.6 - h * 0.75, z + 0.4), cm)
    for x, z, h in ((-6.5, -1.0, 7.0), (6.5, 2.0, 6.0), (-2.5, 10.0, 5.0), (2.0, 11.5, 6.5)):
        box(body, (x - 0.4, 2.6 - h, z - 0.4), (x + 0.4, 2.6, z + 0.4), M('leaf', '#3fae5a'), rot=(0.12, 0, 0.1), pivot=(x, 2.6, z))
    for x, z in ((-2.5, -10.5), (6.0, -7.5), (-7.0, 3.5), (0.5, 0.0)):
        box(body, (x - 0.9, 1.6, z - 0.9), (x + 0.9, 2.6, z + 0.9), M('simple', '#cfc6b4'))     # barnacles
    # the great sail fin: raises the tides
    fin(body, [(-8.0, 2.6), (-5.0, -10.0), (0.0, -15.0), (5.0, -14.0), (9.0, -7.0), (12.0, 2.6)], 'zy', 0.0, '#3a8fb0',
        accent='#bff4ff', glow=True, veins=[(-6.0, 2.6, 0.0, -14.0), (0.0, 2.6, 5.0, -13.5), (5.0, 2.6, 9.0, -6.5)])
    for sx in (-1, 1):
        sea_fin_bone(r, body, 'fin_' + ('r' if sx < 0 else 'l'), (sx * 10.0, 16.0, -6.0),
                     [(sx * 10.0, -8.0), (sx * 17.0, -4.0), (sx * 24.0, 3.0), (sx * 20.0, 4.0), (sx * 10.0, -1.0)], 'xz', 16.2,
                     '#2e5b7c', '#bff4ff', rot=(0, 0, sx * -0.3), amp=0.1, speed=0.05, phase=sx)
    # the head: a whale's blunt brow and long smiling mouth
    head = r.bone('head', body, (0, 12, -14), anim='head')
    rbox(head, (-8.6, 3.6, -29.0), (8.6, 17.0, -13.0), skin, bevel=2.4, faces={'bottom': M('mouth', '#5a2030')})
    for sx in (-1, 1):
        eye(head, (sx * 8.65, 13.6, -19.0), 3.8, 2.6, 'left' if sx > 0 else 'right',
            M('eye', '#2a7ab8', sclera='#f2f8fb', pupil='round', mood='kind', lid='#22465f', glow_amount=0.45))
        box(head, (sx * 8.6, 11.6, -21.4), (sx * 8.75, 12.2, -16.6), M('simple', '#22465f'))    # a soft brow line
        box(head, (sx * 8.6, 16.2, -27.0), (sx * 8.75, 16.6, -16.0), M('simple', '#5a2030'))   # the smile line
        chain_boxes(head, [(sx * 4.0, 4.0, -20.0), (sx * 6.0, 0.5, -17.0), (sx * 7.0, -1.5, -12.0), (sx * 6.2, -2.0, -8.0)],
                    2.2, 0.6, horn)
        for k in range(9):                                                                   # baleen
            z = -27.5 + k * 1.4
            box(head, (sx * 7.4 - 0.25, 17.0, z), (sx * 7.4 + 0.25, 18.0, z + 0.9), M('tooth', '#e8dcc0'))
    jaw = r.bone('jaw', head, (0, 16.5, -15.0), rot=(0.06, 0, 0), anim='jaw')
    rbox(jaw, (-8.2, 17.0, -28.6), (8.2, 21.0, -13.5), pale, bevel=1.4, faces={'top': M('mouth', '#5a2030')})
    ends = tail(r, body, (0, 11.5, 21.0), [6.5, 6.0, 5.0], [11.0, 8.0, 5.5], skin, droop=0.0, amp=0.12, speed=0.04)
    tb, (tx, ty, tz) = ends[-1]
    fin(tb, [(-1.5, tz - 1.0), (-9.0, tz + 3.5), (-14.5, tz + 8.5), (-9.0, tz + 7.0), (0.0, tz + 4.0), (9.0, tz + 7.0),
             (14.5, tz + 8.5), (9.0, tz + 3.5), (1.5, tz - 1.0)], 'xz', ty, '#2e5b7c', accent='#bff4ff',
        veins=[(0, tz, -12.0, tz + 7.5), (0, tz, 12.0, tz + 7.5)])
    return r


# ========================================================================================== land and myth

@recipe
def kurma():
    # 嶺脈地龍 クールマ: an earth dragon carrying a mountain range: ridges for a back, valleys between the scales,
    # cliffs for horns and plates; forests, snow and springs on its back. Calm as an old sage: half-lidded amber eyes,
    # a mossy beard and long whiskers.
    r = rig('kurma')
    hide = M('scale', '#5e6b48', belly='#c8b88a', scale_size=1.4, contrast=0.8)
    rock = M('rock', '#7a7466')
    grass = M('leaf', '#5c9a3c')
    snow = M('simple', '#eef2f4')
    moss = M('fur', '#4f7a34', tip='#8fbf5a')
    horn = M('rock', '#8a8274')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 14, 0), anim='breath')
    rbox(body, (-12.0, 9.0, -14.0), (12.0, 19.5, 16.0), hide, bevel=2.0)
    rbox(body, (-14.0, 5.0, -16.0), (14.0, 11.0, 18.0), rock, bevel=2.2)          # the shell's rim of bedrock
    # the range: stepped peaks with grass shoulders and snow caps
    peaks = [(-6.0, -6.0, 9.0, 13.0), (5.0, -2.0, 8.0, 17.0), (-2.0, 8.0, 9.0, 12.0), (8.0, 10.0, 6.0, 9.0), (-9.0, 9.0, 5.0, 8.0)]
    for x, z, w, h in peaks:
        steps = 4
        for k in range(steps):
            t = k / steps
            hw = w * (1 - t * 0.78)
            y0 = 5.0 - h * t
            y1 = 5.0 - h * (t + 1 / steps)
            box(body, (x - hw, y1, z - hw), (x + hw, y0, z + hw), rock)
            if k == 1:
                box(body, (x - hw - 0.3, y0 - 0.6, z - hw - 0.3), (x + hw + 0.3, y0, z + hw + 0.3), grass)
        box(body, (x - w * 0.25, 5.0 - h - 1.2, z - w * 0.25), (x + w * 0.25, 5.0 - h + 0.9, z + w * 0.25), snow)
    for x, z in ((-11.0, -3.0), (10.5, 4.0), (-4.0, 14.0), (2.0, -12.0), (11.0, -9.0), (-12.0, 12.0)):     # trees
        box(body, (x - 0.5, 2.0, z - 0.5), (x + 0.5, 5.0, z + 0.5), M('wood', '#6a4a2a'))
        box(body, (x - 1.6, -1.6, z - 1.6), (x + 1.6, 2.2, z + 1.6), M('leaf', '#3f7f3a'))
        box(body, (x - 0.9, -3.0, z - 0.9), (x + 0.9, -1.6, z + 0.9), M('leaf', '#4f9a44'))
    box(body, (-0.4, -6.0, -1.0), (0.4, 5.0, -0.2), M('energy', '#7fd8ff', glow=True))           # a spring falling
    # neck and head
    neck = r.bone('neck', body, (0, 13, -14), anim='sway', ax=1, amp=0.03, speed=0.04)
    rbox(neck, (-4.6, 10.0, -21.0), (4.6, 18.0, -13.0), hide, bevel=1.2)
    head = r.bone('head', neck, (0, 13, -21), anim='head')
    rbox(head, (-5.4, 7.6, -30.0), (5.4, 15.6, -20.0), hide, bevel=1.4)
    box(head, (-4.4, 9.0, -34.0), (4.4, 14.4, -30.0), hide, faces={'bottom': M('mouth', '#4a2420')})       # blunt snout
    for sx in (-1, 1):
        box(head, (sx * 2.0 - 0.5, 8.95, -33.6), (sx * 2.0 + 0.5, 9.05, -32.4), M('simple', '#1a1410'))
        box(head, (sx * 1.6, 6.8, -29.5), (sx * 5.8, 8.0, -24.5), rock, rot=(-0.1, 0, 0))               # stony brow
        eye(head, (sx * 5.45, 9.9, -27.0), 3.2, 1.9, 'left' if sx > 0 else 'right',
            M('eye', '#ffb84a', pupil='round', mood='kind', lid='#4a5638', glow_amount=0.6))
        chain_boxes(head, [(sx * 4.0, 7.8, -22.0), (sx * 6.5, 4.6, -19.0), (sx * 8.4, 2.0, -15.0), (sx * 9.0, 0.8, -11.0)],
                    2.6, 0.8, horn)                                                                      # crag horns
        chain_boxes(head, [(sx * 6.5, 4.6, -19.0), (sx * 9.5, 4.4, -18.0)], 1.2, 0.5, horn)
        chain_boxes(head, [(sx * 3.4, 12.6, -33.5), (sx * 6.5, 13.0, -34.5), (sx * 9.0, 15.5, -33.0), (sx * 10.0, 19.0, -31.0)],
                    0.6, 0.3, M('horn', '#d8c89a'))                                                      # whiskers
        teeth(head, sx * 3.8, 14.4, -33.6, -30.6, 2, 0.8, M('tooth', '#e8e0c8'), down=True)
    jaw = r.bone('jaw', head, (0, 14.8, -22.0), rot=(0.1, 0, 0), anim='jaw')
    box(jaw, (-4.6, 14.4, -33.6), (4.6, 17.0, -22.0), M('scale', '#c8b88a', belly='#c8b88a'), faces={'top': M('mouth', '#4a2420')})
    for k, (x, l) in enumerate(((-2.4, 4.5), (-0.8, 6.0), (0.8, 6.0), (2.4, 4.5))):                    # the beard
        box(jaw, (x - 0.7, 17.0, -32.0 + k * 0.4), (x + 0.7, 17.0 + l, -30.6 + k * 0.4), moss)
    # four pillar legs with stone toes
    toes = M('rock', '#9a9282')
    for sx in (-1, 1):
        for name, z, anim in (('leg_f', -9.0, 'leg_r' if sx < 0 else 'leg_l'), ('leg_b', 11.0, 'leg_l' if sx < 0 else 'leg_r')):
            leg(r, body, name + ('r' if sx < 0 else 'l'), anim, (sx * 10.0, 16.5, z), (sx * 11.0, 20.0, z - 0.5),
                (sx * 10.8, 22.8, z), 5.6, 5.0, hide, foot=(6.0, 2.4, 6.0), claw=toes, toes=3)
    tail(r, body, (0, 15.0, 16.0), [5.0, 4.5, 3.5], [6.0, 4.4, 2.8], hide, droop=0.35, spikes=horn, amp=0.08, speed=0.04)
    return r


@recipe
def eomaia():
    # 始祖神獣 エオマイア: a lion's mane, a wolf's fangs, a serpent's scales, a bird's wings, a fish's fins, an
    # elephant's tusks, a stag's antlers and a beast's claws, in harmony: the primal whole. Haughty king and mother:
    # golden eyes under a heavy brow, a proud open jaw.
    r = rig('eomaia')
    fur = M('fur', '#c99a52', tip='#ecc87e')
    mane = M('fur', '#6a3f1e', tip='#a8682e')
    scales = M('scale', '#3e6a52', belly='#a8c89a')
    ivory = M('horn', '#f2e8d2', tip='#fff6dc')
    antler = M('horn', '#8a6a44', tip='#ffd36a', glow=True)
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 13, 2), anim='breath')
    rbox(body, (-5.0, 8.4, -9.5), (5.0, 18.0, 0.0), fur, bevel=1.4)
    rbox(body, (-4.4, 9.0, -0.5), (4.4, 17.2, 8.5), fur, bevel=1.2)
    rbox(body, (-4.6, 8.6, 8.0), (4.6, 16.4, 13.0), fur, bevel=1.2)
    box(body, (-3.6, 17.2, -4.0), (3.6, 17.8, 7.5), scales)                                   # serpent-scaled belly
    # the mane: a ruff of layered fur round the neck and over the shoulders
    for k, (w, y0, y1, z0, z1) in enumerate(((6.6, 3.0, 15.5, -14.0, -9.0), (6.0, 4.5, 14.0, -9.5, -5.5), (5.4, 6.5, 12.0, -6.0, -3.0))):
        rbox(body, (-w, y0, z0), (w, y1, z1), mane, bevel=1.4)
    neck = r.bone('neck', body, (0, 9.5, -10.0), anim='sway', ax=1, amp=0.03, speed=0.05)
    head = r.bone('head', neck, (0, 6.5, -13.0), anim='head')
    rbox(head, (-3.4, 3.4, -19.5), (3.4, 9.6, -13.0), fur, bevel=0.9)
    box(head, (-2.2, 6.2, -24.0), (2.2, 9.0, -19.5), fur, faces={'bottom': M('mouth', '#4a1420')})   # wolf muzzle
    box(head, (-0.9, 5.9, -24.3), (0.9, 7.0, -23.0), M('simple', '#1a1214'))                     # nose
    for sx in (-1, 1):
        box(head, (sx * 1.0, 2.8, -19.8), (sx * 3.7, 4.0, -15.8), mane, rot=(-0.2, 0, 0))         # heavy brow
        eye(head, (sx * 3.45, 5.3, -17.6), 2.6, 1.5, 'left' if sx > 0 else 'right',
            M('eye', '#ffc23a', pupil='slit', mood='fierce', lid='#6a3f1e', glow_amount=0.85))
        box(head, (sx * 2.4, 1.0, -15.0), (sx * 3.6, 3.6, -13.4), fur)                           # ears
        # stag antlers with tines
        chain_boxes(head, [(sx * 2.0, 3.4, -14.5), (sx * 3.6, -0.5, -13.0), (sx * 5.4, -4.2, -12.0), (sx * 6.2, -7.5, -10.5)], 1.2, 0.5, antler)
        chain_boxes(head, [(sx * 3.6, -0.5, -13.0), (sx * 4.2, -3.0, -16.0)], 0.7, 0.3, antler)
        chain_boxes(head, [(sx * 5.4, -4.2, -12.0), (sx * 7.8, -5.0, -14.0)], 0.6, 0.3, antler)
        chain_boxes(head, [(sx * 5.8, -6.0, -11.2), (sx * 4.6, -8.6, -10.0)], 0.5, 0.25, antler)
        # elephant tusks from the upper jaw, curving forward and up
        chain_boxes(head, [(sx * 2.0, 8.6, -21.0), (sx * 2.6, 10.6, -24.0), (sx * 2.8, 10.4, -27.0), (sx * 2.6, 8.6, -29.0)], 1.0, 0.45, ivory)
        teeth(head, sx * 1.8, 9.0, -23.6, -20.0, 2, 0.6, M('tooth', '#f2ede2'), down=True)
        box(head, (sx * 1.8 - 0.3, 9.0, -23.6), (sx * 1.8 + 0.3, 10.8, -23.0), M('tooth', '#f2ede2'))   # wolf fangs
    jaw = r.bone('jaw', head, (0, 8.8, -14.5), rot=(0.2, 0, 0), anim='jaw')
    box(jaw, (-2.0, 9.0, -23.6), (2.0, 10.6, -14.5), fur, faces={'top': M('mouth', '#4a1420')})
    for sx in (-1, 1):
        box(jaw, (sx * 1.6 - 0.3, 7.6, -23.0), (sx * 1.6 + 0.3, 9.0, -22.4), M('tooth', '#f2ede2'))
    # feathered wings
    feather = M('feather', '#f2e6cc', tip='#ffd36a', glow=True)
    for sx in (-1, 1):
        feather_wing(r, body, sx, (sx * 4.6, 9.4, -6.0), 17.0, feather, M('fur', '#e8d8b0'), rot=(0.0, 0.25, 0.6), n=7)
    # legs: lion legs with serpent-scale bands, fish fins at the elbows, big claws
    claw = M('horn', '#2a2420')
    for sx in (-1, 1):
        up, low = leg(r, body, 'leg_f' + ('r' if sx < 0 else 'l'), 'leg_r' if sx < 0 else 'leg_l',
                      (sx * 4.2, 14.0, -5.5), (sx * 4.6, 19.0, -6.5), (sx * 4.4, 22.6, -6.0), 3.2, 2.4, fur, foot=(3.2, 1.6, 3.6), claw=claw)
        box(low, (sx * 4.6 - 1.3, 19.4, -7.8), (sx * 4.6 + 1.3, 20.6, -5.2), scales)
        fin(up, [(-6.0, 16.0), (-3.0, 15.5), (0.0, 19.5), (-4.0, 18.5)], 'zy', sx * 5.9, '#3e8a9a', accent='#9ff0ff')
        leg(r, body, 'leg_b' + ('r' if sx < 0 else 'l'), 'leg_l' if sx < 0 else 'leg_r',
            (sx * 4.0, 13.0, 10.0), (sx * 4.6, 18.0, 8.0), (sx * 4.4, 22.6, 11.0), 3.8, 2.4, fur, foot=(3.2, 1.6, 3.6), claw=claw)
    ends = tail(r, body, (0, 11.0, 12.5), [5.0, 4.5, 4.0, 3.5], [2.4, 2.0, 1.6, 1.2], scales, droop=-0.3, amp=0.14)
    tb, (tx, ty, tz) = ends[-1]
    fin(tb, [(tz - 1.0, ty), (tz + 3.5, ty - 4.5), (tz + 5.0, ty - 1.0), (tz + 5.0, ty + 1.0), (tz + 3.5, ty + 4.5)], 'zy', 0.0,
        '#3e8a9a', accent='#9ff0ff')
    box(tb, (-1.2, ty - 1.2, tz - 1.0), (1.2, ty + 1.2, tz + 1.4), mane)                         # the tuft
    return r


# ========================================================================================== beings and things

@recipe
def chaos():
    # 万象混沌 カオス: a shape that changes each time it is seen; here the cloud of countless eyes: a violet-black
    # mass with a great eye and a grinning maw, eyeballs drifting round it, a rainbow core above, an upside-down
    # town and fish raining round it.
    r = rig('chaos')
    mass = M('void', '#3a1e52')
    flesh = M('scale', '#2c1640', belly='#4a2a62', pattern='vine', accent='#ff6ad5', pattern_glow=True, glow_amount=0.4, scale_size=1.6)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=2.0, speed=0.05)
    body = r.bone('body', root, (0, 11, 0), anim='liquid', amp=0.04)
    rbox(body, (-9.0, 1.0, -8.0), (9.0, 20.0, 8.0), flesh, bevel=3.0)
    for (x, y, z, w) in ((-8.0, 4.0, 2.0, 5.0), (8.5, 6.0, -1.0, 5.5), (0.0, -1.0, 3.0, 6.0), (-5.5, 16.0, -2.0, 5.0),
                         (6.0, 17.0, 3.0, 4.5), (0.0, 10.0, 7.5, 6.0)):
        rbox(body, (x - w, y - w * 0.8, z - w * 0.8), (x + w, y + w * 0.8, z + w * 0.8), mass, bevel=1.6)
    # the great eye and the maw under it
    rbox(body, (-4.2, 3.2, -8.6), (4.2, 8.8, -7.4), M('simple', '#f2ecf6'), bevel=0.8)
    eye(body, (0.0, 6.0, -8.7), 7.2, 4.4, 'front', M('eye', '#ff4fd2', sclera='#f6eef8', pupil='slit', mood='fierce', lid='#2c1640'))
    box(body, (-6.0, 11.0, -8.5), (6.0, 16.5, -7.6), M('mouth', '#240814'))
    box(body, (-6.6, 10.2, -8.9), (6.6, 11.0, -7.6), flesh)
    box(body, (-6.6, 16.5, -8.9), (6.6, 17.3, -7.6), flesh)
    tooth = M('tooth', '#efe8f2')
    teeth_x(body, -8.4, 11.0, -6.0, 6.0, 9, 0.9, tooth, down=True)
    teeth_x(body, -8.4, 16.5, -5.6, 5.6, 8, 0.8, tooth, down=False)
    # drifting eyeballs, each on its own bone
    irises = ['#7ff6ff', '#ffe46a', '#7dff8a', '#ff8a5a', '#b48cff', '#ff6ad5']
    spots = [(-10.5, 2.0, -5.0, 2.2), (10.5, 4.0, -4.5, 2.6), (-11.0, 13.0, -3.0, 2.0), (11.0, 14.0, -2.0, 2.2),
             (-4.0, -2.5, -6.0, 1.8), (5.0, -2.0, -6.0, 1.9)]
    for k, (x, y, z, rr) in enumerate(spots):
        b = r.bone(f'eye{k + 1}', body, (x, y, z), anim='chaos', phase=k * 1.1)
        rbox(b, (x - rr, y - rr, z - rr), (x + rr, y + rr, z + rr), M('simple', '#f2ecf6'), bevel=rr * 0.35)
        eye(b, (x, y, z - rr - 0.05), rr * 1.8, rr * 1.7, 'front',
            M('eye', irises[k % len(irises)], sclera='#f6eef8', pupil='round' if k % 2 else 'slit', mood='calm', lid='#d8cce0'))
    # the rainbow core above
    core = r.bone('core', root, (0, -6, 0), anim='pulse', amp=0.12, speed=0.09)
    cbox(core, (0, -6, 0), (4.0, 4.0, 4.0), M('oilslick', '#ff8ae0', glow=True), rot=(0.6, 0.78, 0.0))
    # the upside-down town and the fish round it
    orbit = r.bone('orbit', root, (0, 10, 0), anim='spin', speed=0.015, cast=0.0)
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        x, z = math.cos(a) * 16.0, math.sin(a) * 16.0
        box(orbit, (x - 1.6, -1.0, z - 1.6), (x + 1.6, 2.4, z + 1.6), M('simple', '#c8beb0'))      # walls, hanging
        box(orbit, (x - 2.0, 2.4, z - 2.0), (x + 2.0, 3.4, z + 2.0), M('simple', '#8a3a2a'))       # the roof below
        box(orbit, (x - 0.5, 0.0, z - 1.7), (x + 0.5, 1.2, z - 1.6), M('energy', '#ffd36a', glow=True))
    for k in range(5):
        a = k * 2 * math.pi / 5
        x, y, z = math.cos(a) * 13.0, 18.0 - k * 2.0, math.sin(a) * 13.0
        box(orbit, (x - 0.6, y - 0.8, z - 1.6), (x + 0.6, y + 0.8, z + 1.2), M('scale', '#ff9a4a', belly='#ffe0b0'))
        box(orbit, (x - 0.1, y - 1.2, z + 1.2), (x + 0.1, y + 1.2, z + 2.4), M('membrane', '#ff9a4a'))
    return r


@recipe
def hephaistos():
    # 典域工廠 ヘファイストス: a sphere of machinery round an SF cube of crystal or unknown metal, with a forge-lit
    # eye; machine spheres orbit it, each an arm, an eye, a furnace, a workshop and a weapon.
    r = rig('hephaistos')
    steel = M('metal', '#5f6f80', accent='#ff9a3a', pattern='rings')
    dark = M('metal', '#2f3842')
    glow = M('energy', '#ff9a3a', glow=True)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.5, speed=0.05)
    body = r.bone('body', root, (0, 11, 0), anim='breath')
    cbox(body, (0, 11, 0), (7.0, 7.0, 7.0), M('gem', '#9ff0ff', glow=True), rot=(0.62, 0.785, 0.0))
    # the armillary shell: two rings of plates
    for k in range(10):
        a = k * 2 * math.pi / 10
        x, y = math.cos(a) * 8.5, 11 + math.sin(a) * 8.5
        cbox(body, (x, y, 0), (2.4, 2.4, 9.0), steel, rot=(0, 0, a))
        z, x2 = math.cos(a) * 8.5, math.sin(a) * 8.5
        cbox(body, (x2, 11.0, z), (2.2, 9.0, 2.2), dark, rot=(0, a, 0))
    # the forge eye in front of the core
    rbox(body, (-4.6, 6.4, -9.6), (4.6, 15.6, -6.0), dark, bevel=1.0)
    eye(body, (0, 11, -9.7), 7.0, 7.0, 'front', M('eye', '#ffa040', sclera='#1a1e24', pupil='ring', mood='calm', lid='#2f3842'))
    for sx in (-1, 1):
        box(body, (sx * 4.6, 10.4, -9.4), (sx * 5.8, 11.6, -6.4), glow)
    # orbiting machine spheres
    kinds = ['eye', 'furnace', 'arm', 'cannon']
    for k, kind in enumerate(kinds):
        a = k * math.pi / 2 + 0.6
        x, y, z = math.cos(a) * 15.0, 8.0 + (k % 2) * 6.0, math.sin(a) * 15.0
        b = r.bone(f'orb{k + 1}', root, (0, 11, 0), anim='spin', speed=0.02 + 0.005 * k, cast=0.0)
        ball(b, (x, y, z), 2.6, steel)
        if kind == 'eye':
            eye(b, (x, y, z - 2.65), 2.6, 2.6, 'front', M('eye', '#7ff6ff', pupil='ring', lid='#2f3842'))
        elif kind == 'furnace':
            box(b, (x - 1.4, y - 0.8, z - 2.7), (x + 1.4, y + 1.6, z - 2.4), glow)
            box(b, (x - 0.6, y - 4.6, z - 0.6), (x + 0.6, y - 2.4, z + 0.6), dark)                 # chimney
        elif kind == 'arm':
            chain_boxes(b, [(x, y + 2.0, z), (x - 1.0, y + 5.0, z - 2.0), (x - 1.5, y + 6.0, z - 5.0)], 1.0, 0.7, dark)
            for sx in (-1, 1):
                seg(b, (x - 1.5, y + 6.0, z - 5.0), (x - 1.5 + sx * 1.0, y + 6.8, z - 6.6), 0.4, 0.4, steel)
        else:
            chain_boxes(b, [(x, y, z - 2.0), (x, y, z - 6.5)], 1.4, 1.2, dark)
            box(b, (x - 0.5, y - 0.5, z - 6.7), (x + 0.5, y + 0.5, z - 6.5), glow)
    halo = r.bone('halo', root, (0, 11, 0), anim='spin', speed=0.01, cast=0.0)
    hoop(halo, (0, 11, 0), 19.0, 0.6, M('energy', '#7ff6ff', glow=True), axis='y', n=40, depth=0.4)
    for k in range(8):
        a = k * math.pi / 4
        cbox(halo, (math.cos(a) * 19.0, 11, math.sin(a) * 19.0), (1.0, 1.8, 1.0), M('metal', '#8aa0b4'), rot=(0, -a, 0))
    return r


@recipe
def mels():
    # 至高武王 メルス: a clear sphere of living gel about fifty centimetres across with the world's hardest core
    # inside; it turns into blade, spear, hammer, shield and bow. Given a quiet face (two calm eyes and a small mouth on
    # the core) so it reads as a being, not a lump; a few weapon shards circle it.
    r = rig('mels')
    r.translucent = True
    root = r.bone('root', None, (0, 24, 0), anim='root')
    core = r.bone('core', root, (0, 20, 0), anim='pulse', amp=0.05, speed=0.07)
    rbox(core, (-1.8, 18.2, -1.8), (1.8, 21.8, 1.8), M('gem', '#d8f6ff', glow=True), bevel=0.5)
    body = r.bone('body', root, (0, 24, 0), anim='liquid', amp=0.07)
    rbox(body, (-4.2, 15.8, -4.2), (4.2, 24.0, 4.2), M('slime', '#a8e8ff', alpha=110), bevel=1.6)
    for sx in (-1, 1):
        eye(body, (sx * 1.5, 19.0, -4.25), 1.3, 1.8, 'front', M('eye', '#123048', pupil='none', mood='calm', lid='#7fc8e8', glow=False))
    box(body, (-0.7, 21.0, -4.26), (0.7, 21.4, -4.2), M('simple', '#3a7898'))
    ring = r.bone('shards', root, (0, 19, 0), anim='spin', speed=0.05, cast=0.0)
    for k, (w, h) in enumerate(((0.4, 3.0), (0.6, 2.2), (0.4, 2.6))):
        a = k * 2 * math.pi / 3
        x, z = math.cos(a) * 6.5, math.sin(a) * 6.5
        cbox(ring, (x, 19, z), (w, h, 0.9), M('gem', '#bff4ff', glow=True), rot=(0, a, 0.3))
    return r


@recipe
def yggdrasil():
    # 玖天神樹 イグドラシル: the tree that pierces heaven, holding nine worlds in its boughs; one flower raises the
    # land around it to a divine sanctum. A gentle old face in the bark: green-lit eyes under knotted brows, a
    # hollow mouth; nine world-fruits hang glowing under the crown.
    r = rig('yggdrasil')
    bark = M('wood', '#5a4030')
    pale = M('wood', '#7a5a40')
    leaf = M('leaf', '#4f9a44', flowers='#ffd6f0')
    leaf2 = M('leaf', '#3f8a3e')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    trunk = r.bone('body', root, (0, 10, 0), anim='sway', ax=2, amp=0.01, speed=0.02)
    rbox(trunk, (-6.5, -12.0, -6.5), (6.5, 24.0, 6.5), bark, bevel=1.6)
    rbox(trunk, (-8.5, 16.0, -8.5), (8.5, 24.0, 8.5), bark, bevel=2.0)
    for k in range(6):                                                                     # roots
        a = k * math.pi / 3 + 0.3
        chain_boxes(trunk, [(math.cos(a) * 6.0, 21.0, math.sin(a) * 6.0), (math.cos(a) * 11.0, 22.6, math.sin(a) * 11.0),
                            (math.cos(a) * 15.0, 23.6, math.sin(a) * 15.0)], 3.2, 1.4, bark)
    # the face
    for sx in (-1, 1):
        box(trunk, (sx * 0.8, 0.6, -7.4), (sx * 4.4, 2.2, -6.4), pale, rot=(0, 0, sx * -0.15))      # knotted brows
        eye(trunk, (sx * 2.6, 3.6, -6.65), 3.0, 1.9, 'front', M('eye', '#9fff7a', pupil='round', mood='kind', lid='#3e2a1e'))
    box(trunk, (-0.8, 3.6, -7.6), (0.8, 7.0, -6.4), pale)                                       # nose knot
    box(trunk, (-2.6, 8.6, -6.7), (2.6, 10.8, -6.45), M('mouth', '#1e140e'))                    # the hollow mouth
    box(trunk, (-3.0, 10.8, -7.2), (3.0, 11.6, -6.4), pale)
    box(trunk, (-2.4, 7.8, -7.0), (2.4, 8.6, -6.4), pale)
    # boughs to the crown
    crown = r.bone('crown', trunk, (0, -12, 0), anim='sway', ax=2, amp=0.015, speed=0.025)
    for k in range(5):
        a = k * 2 * math.pi / 5
        chain_boxes(crown, [(0, -10.0, 0), (math.cos(a) * 9.0, -18.0, math.sin(a) * 9.0), (math.cos(a) * 16.0, -24.0, math.sin(a) * 16.0)],
                    3.6, 1.6, bark)
    rbox(crown, (-17.0, -40.0, -17.0), (17.0, -24.0, 17.0), leaf, bevel=4.0)
    rbox(crown, (-11.0, -46.0, -11.0), (11.0, -38.0, 11.0), leaf2, bevel=3.0)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.6
        x, z = math.cos(a) * 17.0, math.sin(a) * 17.0
        rbox(crown, (x - 7.0, -30.0, z - 7.0), (x + 7.0, -20.0, z + 7.0), leaf if k % 2 else leaf2, bevel=2.4)
    # the nine world-fruits
    worlds = ['#ff6ad5', '#6af0ff', '#ffe46a', '#7dff8a', '#a07dff', '#ff8a5a', '#ffffff', '#5a8aff', '#ff5a6a']
    for k, col in enumerate(worlds):
        a = k * 2 * math.pi / 9
        x, z = math.cos(a) * 14.0, math.sin(a) * 14.0
        b = r.bone(f'fruit{k + 1}', crown, (x, -20.0, z), anim='float', amp=0.6, speed=0.05, phase=k)
        box(b, (x - 0.15, -21.5, z - 0.15), (x + 0.15, -20.0, z + 0.15), leaf2)
        cbox(b, (x, -19.4, z), (1.6, 1.6, 1.6), M('gem', col, glow=True), rot=(0.4, 0.6, 0))
    return r


# ================================================================================================ familiars

@recipe
def familiar_beast():
    # エオマイアの仔: Eomaia's cub, a little horned beast: big round eyes, antler nubs, a fluffy ruff, stubby wings.
    r = rig('familiar_beast')
    fur = M('fur', '#d8a85e', tip='#f2d494')
    ruff = M('fur', '#8a5a2e', tip='#c8884a')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 18, 0), anim='breath')
    rbox(body, (-2.8, 15.0, -3.5), (2.8, 20.4, 5.0), fur, bevel=1.0)
    rbox(body, (-3.4, 13.2, -4.6), (3.4, 19.6, -1.6), ruff, bevel=1.0)
    head = r.bone('head', body, (0, 14, -3.5), anim='head')
    rbox(head, (-3.4, 8.6, -9.6), (3.4, 14.8, -3.4), fur, bevel=1.0)
    box(head, (-1.6, 12.2, -11.4), (1.6, 14.4, -9.6), M('fur', '#f2dcb0'), faces={'bottom': M('mouth', '#6a2430')})
    box(head, (-0.6, 12.0, -11.5), (0.6, 12.8, -11.0), M('simple', '#2a1a1a'))
    for sx in (-1, 1):
        eye(head, (sx * 1.75, 11.0, -9.7), 1.9, 2.2, 'front', M('eye', '#f2b030', sclera='#ffffff', pupil='round', mood='happy',
                                                                    lid='#8a5a2e', look=0.0))
        box(head, (sx * 2.2, 7.0, -6.0), (sx * 3.4, 9.0, -4.4), fur)                                  # ears
        chain_boxes(head, [(sx * 1.2, 8.8, -6.0), (sx * 1.6, 7.0, -5.4), (sx * 2.2, 6.2, -5.0)], 0.7, 0.4,
                    M('horn', '#e8d8b0', tip='#ffd36a', glow=True))
        box(head, (sx * 1.0 - 0.2, 14.4, -11.2), (sx * 1.0 + 0.2, 15.0, -10.9), M('tooth', '#ffffff'))   # little fangs
    jaw = r.bone('jaw', head, (0, 14.2, -6.0), rot=(0.12, 0, 0), anim='jaw')
    box(jaw, (-1.4, 14.4, -11.0), (1.4, 15.4, -6.0), M('fur', '#f2dcb0'), faces={'top': M('mouth', '#6a2430')})
    for sx in (-1, 1):
        leg(r, body, 'leg_f' + ('r' if sx < 0 else 'l'), 'leg_r' if sx < 0 else 'leg_l', (sx * 1.8, 19.0, -2.0), (sx * 1.9, 21.5, -2.2),
            (sx * 1.8, 23.3, -2.0), 1.6, 1.4, fur, foot=(1.6, 1.0, 1.8), claw=None)
        leg(r, body, 'leg_b' + ('r' if sx < 0 else 'l'), 'leg_l' if sx < 0 else 'leg_r', (sx * 1.8, 19.0, 3.8), (sx * 1.9, 21.5, 3.4),
            (sx * 1.8, 23.3, 3.8), 1.8, 1.4, fur, foot=(1.6, 1.0, 1.8), claw=None)
        feather_wing(r, body, sx, (sx * 2.6, 15.6, -1.0), 4.0, M('feather', '#f2e6cc', tip='#ffd36a'), M('fur', '#e8d8b0'),
                     rot=(0.0, 0.2, 0.5), n=3, amp=0.4, speed=0.18)
    ends = tail(r, body, (0, 16.0, 4.8), [2.0, 2.0], [1.2, 1.0], fur, droop=-0.6, amp=0.2, speed=0.12)
    tb, (tx, ty, tz) = ends[-1]
    rbox(tb, (-1.0, ty - 1.4, tz - 0.6), (1.0, ty + 0.6, tz + 1.4), M('fur', '#fff0d0'), bevel=0.4)
    return r


@recipe
def familiar_sprite():
    # イグドラシル／マグナ・マーテルの若葉の精: a leaf sprite: a bud with a happy face, a flower on its head,
    # two leaf wings and a little root tail.
    r = rig('familiar_sprite')
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=2.0, speed=0.08)
    body = r.bone('body', root, (0, 16, 0), anim='float', amp=0.8, speed=0.07)
    rbox(body, (-2.6, 12.8, -2.4), (2.6, 18.6, 2.4), M('skin', '#e6f8c8'), bevel=0.9)
    for sx in (-1, 1):
        eye(body, (sx * 1.15, 15.0, -2.45), 1.3, 1.7, 'front', M('eye', '#3a9a4a', sclera='#ffffff', pupil='round', mood='happy',
                                                                     lid='#5aa04a', look=0.0))
        box(body, (sx * 1.9 - 0.3, 16.3, -2.42), (sx * 1.9 + 0.3, 16.7, -2.4), M('simple', '#ffb0c0'))     # blush
    box(body, (-0.6, 17.0, -2.44), (0.6, 17.4, -2.4), M('mouth', '#a0404a'))
    rbox(body, (-3.0, 11.6, -2.8), (3.0, 13.4, 2.8), M('leaf', '#5aa04a'), bevel=0.6)                  # leaf cap
    for k in range(5):
        a = k * 2 * math.pi / 5
        cbox(body, (math.cos(a) * 1.1, 10.8, math.sin(a) * 1.1), (1.2, 0.5, 1.2), M('simple', '#ffd6f0'))
    cbox(body, (0, 10.6, 0), (0.8, 0.8, 0.8), M('energy', '#ffe46a', glow=True))
    for sx in (-1, 1):
        b = r.bone('wing_' + ('r' if sx < 0 else 'l'), body, (sx * 2.4, 14.0, 0.5), anim='sway', ax=2, amp=0.35, speed=0.2,
                   rot=(0, 0, sx * -0.4))
        fin(b, [(sx * 2.4, 0.0), (sx * 6.0, -2.0), (sx * 9.0, 0.5), (sx * 6.5, 3.0)], 'xz', 14.0, '#7ac35a', accent='#d8f2b8')
    chain_boxes(body, [(0, 18.6, 0), (0.4, 20.4, 0.3), (-0.2, 22.0, 0.6)], 0.8, 0.3, M('wood', '#7a5a3a'))
    return r


@recipe
def familiar_curse():
    # 獄華の分御霊: a scrap of Gokuka's curse with a will of its own: a violet flame-blob with one glaring eye, a
    # jagged grin, little horns and a wisp for a tail.
    r = rig('familiar_curse')
    blob = M('scale', '#3a1a52', belly='#5a2a72', pattern='vine', accent='#ff4fd2', pattern_glow=True, glow_amount=0.5)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=2.0, speed=0.09)
    body = r.bone('body', root, (0, 19, 0), anim='liquid', amp=0.06)
    rbox(body, (-3.6, 15.0, -3.4), (3.6, 21.6, 3.4), blob, bevel=1.3)
    for (x, z, h) in ((-1.8, -0.5, 3.2), (1.2, 0.8, 4.0), (0.0, 1.8, 2.6)):                      # flame tongues
        chain_boxes(body, [(x, 15.4, z), (x * 1.2, 13.0, z + 0.6), (x * 1.3, 15.0 - h, z + 1.4)], 1.4, 0.4,
                    M('horn', '#3a1a52', tip='#ff4fd2', glow=True))
    eye(body, (0, 17.2, -3.45), 3.0, 2.2, 'front', M('eye', '#ff4fd2', sclera='#fff0fa', pupil='slit', mood='fierce', lid='#2a0e3a'))
    box(body, (-2.6, 19.4, -3.5), (2.6, 20.6, -3.38), M('mouth', '#14040c'))
    teeth_x(body, -3.5, 19.4, -2.4, 2.4, 5, 0.5, M('tooth', '#ffffff'), down=True)
    teeth_x(body, -3.5, 20.6, -2.2, 2.2, 4, 0.45, M('tooth', '#ffffff'), down=False)
    for sx in (-1, 1):
        chain_boxes(body, [(sx * 2.4, 15.4, -1.0), (sx * 3.2, 13.6, -0.6), (sx * 3.4, 12.6, 0.2)], 0.8, 0.3, M('horn', '#1a0a24', tip='#ff8ae0'))
    tail(r, body, (0, 19.0, 3.2), [2.0, 2.0, 1.6], [1.8, 1.2, 0.7], blob, droop=-0.3, amp=0.25, speed=0.12)
    return r


@recipe
def familiar_drone():
    # ヘファイストス／ヴァレリア系の工廠球体: a little forge drone: a steel ball with one big lens eye, side thrusters
    # and a rotor on top.
    r = rig('familiar_drone')
    steel = M('metal', '#5a7088', accent='#52e8d6', pattern='rings')
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=2.0, speed=0.1)
    body = r.bone('body', root, (0, 18, 0), anim='sway', ax=1, amp=0.25, speed=0.04)
    ball(body, (0, 18, 0), 3.0, steel)
    box(body, (-3.3, 17.6, -3.3), (3.3, 18.4, 3.3), M('metal', '#2f3842'))
    rbox(body, (-1.8, 16.2, -3.2), (1.8, 19.8, -2.4), M('metal', '#2f3842'), bevel=0.5)
    eye(body, (0, 18.0, -3.25), 2.8, 2.8, 'front', M('eye', '#52e8d6', pupil='ring', mood='calm', lid='#2f3842'))
    for sx in (-1, 1):
        box(body, (sx * 3.0, 17.2, -0.8), (sx * 4.2, 18.8, 1.6), M('metal', '#8aa0b4'))
        box(body, (sx * 3.2, 18.8, 1.0), (sx * 4.0, 19.2, 1.6), M('energy', '#52e8d6', glow=True))
    box(body, (-0.4, 13.0, -0.4), (0.4, 15.4, 0.4), M('metal', '#b0c0d0'))
    rotor = r.bone('rotor', root, (0, 13, 0), anim='spin', speed=0.4, cast=0.0)
    hoop(rotor, (0, 13, 0), 4.6, 0.4, M('energy', '#a5f3ff', glow=True), axis='y', n=20, depth=0.25)
    for a in (0.0, math.pi / 2):
        cbox(rotor, (0, 13, 0), (9.2 * abs(math.cos(a)) + 0.6, 0.25, 9.2 * abs(math.sin(a)) + 0.6), M('metal', '#b0c0d0'))
    return r

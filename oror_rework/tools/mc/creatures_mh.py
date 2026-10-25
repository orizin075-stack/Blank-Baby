"""OROR's non-human characters, redesigned to the level of L_Ender's Cataclysm, Alex's Caves, Legendary Monsters
and Monster Hunter style mod bosses (0.17.29), following each character's description.

Compared with the first cube pass (creatures_ia.py) every body part is built from several shaped pieces: crested
skulls with inset glowing eyes under brow plates, cheek plates and layered horns; necks and backs covered by
overlapping armour plates with spikes; digitigrade hind legs with armoured shins and claws; wings with jointed
fingers, a thumb claw and veined membranes; tails of plated segments ending in a weapon. Hides use the shingle,
carapace and hide painters (iapaint.py).

Model space: pixels, y down (ground y = 24), the front is -z.
"""
import math
import numpy as np
import bb
from paint import M
from creatures_ia import (rig as _rig, box, rbox, cbox, seg, chain_boxes, eye, teeth, teeth_x, fin, ball, hoop, sea_fin_bone,
                          recipe as _unused)


def rig(key, td=2):
    """Two texels per model pixel for fine detail on big bosses, every texel on its material's palette: the reference
    mods (Cataclysm, Alex's Caves, Legendary Monsters) paint a boss with 14-32 colours per texture; OROR's earlier
    painted gradients gave 250-960."""
    r = _rig(key, td=td)
    r.snap = True
    return r

RECIPES = {}


def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn


# ====================================================================================================== the kit

def fit_height(r, skip=('wing',)):
    """Sets the rig's height (what the renderer scales to the hitbox) from the body alone: parts on bones whose name
    starts with one of `skip` (raised wings, orbiting satellites, a hanging town) may rise above the hitbox, so they
    no longer shrink the body."""
    import sculpt as SC
    mats = SC.world_of(r)
    top = 1e9
    for s in r.sculpt.surfs:
        b, hidden = s.bone, False
        while b is not None:
            if any(b.name.startswith(k) for k in skip):
                hidden = True
                break
            b = b.parent
        if not hidden:
            top = min(top, float(SC.surf_world(s, mats)[0][:, 1].min()))
    r.height = round(24 - top, 3)
    return r


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(len(a)))


def _span(mat, t0, t1):
    """The material for one box of a multi-box horn or spike, so its tip colour follows the whole length."""
    return dict(mat, t0=t0, t1=t1) if mat.get('type') == 'horn' else mat


def horn(bone, pts, w0, w1, mat, rings=False):
    """A horn through pts, tapering from w0 to w1, coloured root to tip along its whole length."""
    n = len(pts) - 1
    for i in range(n):
        t, t2 = i / n, (i + 1) / n
        w = w0 + (w1 - w0) * (t + t2) / 2
        seg(bone, pts[i], pts[i + 1], w, w, _span(mat, t, t2), ext=w * 0.5)
    if rings:
        p0, p1 = np.asarray(pts[0], float), np.asarray(pts[1], float)
        c = p0 + (p1 - p0) * 0.15
        seg(bone, c - (p1 - p0) * 0.05, c + (p1 - p0) * 0.08, w0 * 1.3, w0 * 1.3, _span(mat, 0.0, 0.1))


def spike(bone, base, tip, w, mat):
    seg(bone, base, tip, w, w, _span(mat, 0.0, 0.75), up=(0, 0, 1), ext=w * 0.3)
    seg(bone, lerp(base, tip, 0.55), tip, w * 0.55, w * 0.55, _span(mat, 0.55, 1.0), up=(0, 0, 1))


def dorsal_plates(bone, z0, z1, y_of, n, w, h, plate, spike_mat=None, spike_h=None, lean=0.35):
    """Overlapping armour plates down the spine, each tilted back over the next, with a spike on top."""
    for k in range(n):
        t = k / max(1, n - 1)
        z = z0 + (z1 - z0) * t
        y = y_of(z)
        ww = w(t) if callable(w) else w
        hh = h(t) if callable(h) else h
        box(bone, (-ww / 2, y - hh * 0.35, z - 1.3), (ww / 2, y + hh * 0.25, z + 1.5), plate, rot=(lean, 0, 0), pivot=(0, y, z))
        if spike_mat is not None:
            sh = spike_h(t) if callable(spike_h) else spike_h
            spike(bone, (0, y - hh * 0.2, z), (0, y - hh * 0.2 - sh, z + sh * 0.55), max(0.6, ww * 0.18), spike_mat)


def drake_head(r, parent, at, s, sp):
    """Monster Hunter style dragon head. at = (x, y, z) of the skull's back top centre; s = scale (1: a 6.4-wide
    skull); sp: dict of materials and options (skin, plate, horn, eye, mouth, tooth, horns, crest, nose_horn,
    open)."""
    ax, ay, az = at
    S = lambda x, y, z: (ax + x * s, ay + y * s, az + z * s)
    skin, plate, hornm = sp['skin'], sp['plate'], sp['horn']
    head = r.bone('head', parent, S(0, 2.6, 0), anim='head')
    # cranium, forehead ridge, crest
    rbox(head, S(-3.2, 0.0, -6.6), S(3.2, 4.6, 0.2), skin, bevel=0.8 * s)
    box(head, S(-1.3, -0.6, -6.4), S(1.3, 0.3, -0.6), plate)
    for k in range(sp.get('crest', 3)):
        z = -4.2 + k * 2.0
        spike(head, S(0, -0.4, z), S(0, -1.3 - 0.4 * k, z + 1.6), 0.8 * s, hornm)
    if sp.get('gem'):
        cbox(head, S(0, -0.75, -6.2), (1.5 * s, 1.5 * s, 1.5 * s), sp['gem'], rot=(0.3, 0.785, 0))
    # brow plates angled down to the front: the frown
    for sx in (-1, 1):
        box(head, S(sx * 0.9, -0.7, -7.2), S(sx * 3.8, 0.7, -3.0), plate, rot=(-0.22, sx * 0.1, sx * 0.1),
            pivot=S(sx * 2.3, 0, -5.0))
    # snout: upper jaw with a ridge, a stepped tip, nostril bumps
    rbox(head, S(-2.3, 0.9, -13.4), S(2.3, 3.7, -6.0), skin, bevel=0.5 * s, faces={'bottom': sp['mouth']})
    box(head, S(-1.9, 1.2, -14.6), S(1.9, 3.5, -13.2), skin, faces={'bottom': sp['mouth']})
    box(head, S(-1.0, 0.5, -13.0), S(1.0, 0.95, -7.0), plate)
    for sx in (-1, 1):
        box(head, S(sx * 1.25 - 0.55, 0.75, -14.2), S(sx * 1.25 + 0.55, 1.3, -12.9), skin)
        box(head, S(sx * 1.25 - 0.3, 0.7, -14.25), S(sx * 1.25 + 0.3, 0.8, -13.6), M('simple', '#100a0c'))
    if sp.get('nose_horn'):
        horn(head, [S(0, 0.6, -12.0), S(0, -1.2, -12.6), S(0, -2.6, -12.0)], 1.1 * s, 0.35 * s, hornm, rings=False)
    # eyes in dark sockets under the brows
    for sx in (-1, 1):
        side = 'left' if sx > 0 else 'right'
        cbox(head, S(sx * 3.2, 1.7, -5.0), (0.25, 2.0 * s, 3.6 * s), M('simple', '#0c0a10'))
        eye(head, S(sx * 3.32, 1.75, -5.0), 3.2 * s, 1.7 * s, side, sp['eye'])
    # cheek plates with backward spikes, upper teeth
    for sx in (-1, 1):
        box(head, S(sx * 2.7, 2.0, -3.8), S(sx * 3.9, 4.9, 0.6), plate, rot=(0, sx * -0.12, 0), pivot=S(sx * 3.3, 3.4, -1.6))
        spike(head, S(sx * 3.6, 3.6, 0.2), S(sx * 4.6, 3.9, 2.8), 0.8 * s, hornm)
        teeth(head, sx * 1.95 * s + ax, ay + 3.7 * s, az - 13.8 * s, az - 6.4 * s, 6, 0.6 * s, sp['tooth'], down=True)
        teeth(head, sx * 1.5 * s + ax, ay + 3.5 * s, az - 14.4 * s, az - 13.4 * s, 1, 0.75 * s, sp['tooth'], down=True)
    # horns
    style = sp.get('horns', 'swept')
    for sx in (-1, 1):
        if style in ('swept', 'crown'):
            horn(head, [S(sx * 2.0, 0.0, -1.0), S(sx * 2.9, -1.8, 2.0), S(sx * 3.4, -3.0, 5.2), S(sx * 3.3, -3.4, 8.2),
                        S(sx * 2.8, -2.9, 10.4)], 1.7 * s, 0.4 * s, hornm)
            horn(head, [S(sx * 3.2, 1.6, -0.6), S(sx * 4.6, 1.2, 1.8), S(sx * 5.4, 0.2, 3.6)], 1.0 * s, 0.3 * s, hornm)
        if style == 'crown':
            horn(head, [S(sx * 1.2, -0.4, -3.6), S(sx * 1.7, -3.0, -3.0), S(sx * 2.0, -5.4, -1.6), S(sx * 1.9, -6.9, 0.4)],
                 1.3 * s, 0.35 * s, hornm)
        if style == 'blade':                          # flat swept fins (Teia)
            box(head, S(sx * 1.4, -1.2, -2.0), S(sx * 2.4, 0.2, 9.0), hornm, rot=(-0.25, sx * -0.18, 0), pivot=S(sx * 1.9, 0, -2.0))
            box(head, S(sx * 2.6, 0.2, -1.0), S(sx * 3.4, 1.4, 6.0), hornm, rot=(-0.15, sx * -0.3, 0), pivot=S(sx * 3.0, 0.8, -1.0))
    # lower jaw on its hinge, open a little: teeth and the mouth show
    jaw = r.bone('jaw', head, S(0, 4.2, -2.4), rot=(sp.get('open', 0.16), 0, 0), anim='jaw')
    rbox(jaw, S(-2.1, 3.8, -13.9), S(2.1, 5.4, -2.0), sp.get('jaw', skin), bevel=0.4 * s, faces={'top': sp['mouth']})
    spike(jaw, S(0, 5.3, -10.5), S(0, 6.6, -9.0), 0.8 * s, hornm)
    for sx in (-1, 1):
        teeth(jaw, sx * 1.65 * s + ax, ay + 3.8 * s, az - 13.4 * s, az - 6.6 * s, 5, 0.55 * s, sp['tooth'], down=False)
        spike(jaw, S(sx * 2.0, 4.6, -3.0), S(sx * 3.0, 5.6, -0.8), 0.6 * s, hornm)
    return head, jaw


def plated_neck(r, parent, pts, widths, skin, plate, hornm, belly, spikes=True):
    neck = r.bone('neck', parent, pts[0], anim='sway', ax=1, amp=0.04, speed=0.05)
    for i in range(len(pts) - 1):
        w = widths[i]
        seg(neck, pts[i], pts[i + 1], w, w * 0.95, skin, up=(0, 0, -1), ext=w * 0.35)
        mid = lerp(pts[i], pts[i + 1], 0.5)
        box(neck, (mid[0] - w * 0.38, mid[1] - w * 0.62, mid[2] - 1.4), (mid[0] + w * 0.38, mid[1] - w * 0.35, mid[2] + 1.4), plate,
            rot=(0.5, 0, 0), pivot=mid)
        if spikes and i % 2 == 0:
            spike(neck, (mid[0], mid[1] - w * 0.55, mid[2]), (mid[0], mid[1] - w * 0.55 - 1.8, mid[2] + 1.2), 0.8, hornm)
        box(neck, (mid[0] - w * 0.32, mid[1] + w * 0.38, mid[2] - 1.2), (mid[0] + w * 0.32, mid[1] + w * 0.5, mid[2] + 1.2), belly)
    return neck


def claw_foot(bone, ankle, w, l, skin, claw, toes=3, back_toe=True):
    ax, ay, az = ankle
    rbox(bone, (ax - w / 2, ay - 0.6, az - l * 0.75), (ax + w / 2, ay + 1.3, az + l * 0.25), skin, bevel=0.3)
    for k in range(toes):
        x = ax + (k - (toes - 1) / 2) * (w / toes)
        tz = az - l * 0.75
        seg(bone, (x, ay + 0.6, tz + 0.4), (x, ay + 1.2, tz - 1.4), w / toes * 0.75, 0.9, skin, up=(0, -1, 0))
        seg(bone, (x, ay + 0.5, tz - 1.2), (x, ay + 1.35, tz - 2.6), w / toes * 0.42, 0.5, claw, up=(0, 0, -1))
    if back_toe:
        seg(bone, (ax, ay + 0.6, az + l * 0.2), (ax, ay + 1.3, az + l * 0.2 + 1.4), 0.5, 0.5, claw, up=(0, 0, 1))


def fore_leg(r, parent, name, anim, sx, shoulder, elbow, wrist, w, skin, plate, claw):
    up = r.bone(name, parent, shoulder, anim=anim)
    rbox(up, (shoulder[0] - w * 0.75, shoulder[1] - w * 0.9, shoulder[2] - w * 0.9),
         (shoulder[0] + w * 0.75, shoulder[1] + w * 0.6, shoulder[2] + w * 0.8), skin, bevel=0.6)
    seg(up, shoulder, elbow, w, w * 1.05, skin, up=(0, 0, -1), ext=w * 0.4)
    box(up, (shoulder[0] + sx * w * 0.45, shoulder[1] - w * 0.9, shoulder[2] - w * 0.9),
        (shoulder[0] + sx * (w * 0.45 + 0.5), shoulder[1] + w * 0.4, shoulder[2] + w * 0.7), plate)
    low = r.bone(name + '_low', up, elbow, anim='knee')
    seg(low, elbow, wrist, w * 0.75, w * 0.8, skin, up=(0, 0, -1), ext=w * 0.3)
    box(low, (elbow[0] - w * 0.42, elbow[1] + 0.4, elbow[2] - w * 0.55), (elbow[0] + w * 0.42, wrist[1] - 1.0, elbow[2] - w * 0.3), plate)
    spike(low, (elbow[0], elbow[1], elbow[2] + w * 0.3), (elbow[0], elbow[1] - 0.4, elbow[2] + w * 0.3 + 1.6), 0.6, claw)
    claw_foot(low, wrist, w * 1.1, w * 1.4, skin, claw)
    return up, low


def hind_leg(r, parent, name, anim, sx, hip, knee, ankle, foot, w, skin, plate, claw):
    """Digitigrade: thigh forward to the knee, shin back to the raised ankle, a long foot to the toes."""
    up = r.bone(name, parent, hip, anim=anim)
    rbox(up, (hip[0] - w * 0.7, hip[1] - w * 0.9, hip[2] - w * 1.1), (hip[0] + w * 0.7, hip[1] + w * 0.9, hip[2] + w * 0.9), skin, bevel=0.8)
    seg(up, hip, knee, w * 1.05, w * 1.25, skin, up=(0, 0, -1), ext=w * 0.4)
    low = r.bone(name + '_low', up, knee, anim='knee')
    seg(low, knee, ankle, w * 0.7, w * 0.8, skin, up=(0, 0, 1), ext=w * 0.3)
    box(low, (knee[0] - w * 0.4, knee[1] + 0.6, knee[2] + w * 0.3), (knee[0] + w * 0.4, ankle[1] - 0.6, knee[2] + w * 0.55), plate,
        rot=(-0.35, 0, 0), pivot=knee)
    seg(low, ankle, foot, w * 0.6, w * 0.6, skin, up=(0, 0, -1), ext=w * 0.3)
    claw_foot(low, foot, w * 1.1, w * 1.2, skin, claw, back_toe=False)
    spike(low, ankle, (ankle[0], ankle[1] - 0.2, ankle[2] + 1.6), 0.55, claw)
    return up, low


def drake_wing(r, parent, side, shoulder, arm, fingers, membrane, spar, claw, rot, accent=None, glow=False, vanes=None,
               amp=0.3, speed=0.1, skin_kw=None):
    """Dragon wing laid flat and raised by the rest rotation; arm = [elbow, wrist] (x, z); fingers = tips (x, z)."""
    sx = side
    b = r.bone('wing_r' if sx < 0 else 'wing_l', parent, shoulder, rot=(rot[0], rot[1] * sx, rot[2] * -sx), anim='sway', ax=2,
               amp=amp, speed=speed)
    x0, y, z0 = shoulder
    P = lambda xz: (x0 + sx * xz[0], y, z0 + xz[1])
    elbow, wrist = P(arm[0]), P(arm[1])
    chain_boxes(b, [(x0, y, z0), elbow], 2.2, 1.7, spar)
    chain_boxes(b, [elbow, wrist], 1.7, 1.3, spar)
    for j in (elbow, wrist):
        cbox(b, j, (2.0, 2.0, 2.0), spar)
    seg(b, wrist, (wrist[0] + sx * 0.6, y - 0.6, wrist[2] - 2.4), 0.7, 0.7, claw, up=(0, -1, 0))      # thumb claw
    tips = [P(t) for t in fingers]
    for t in tips:
        knuckle = lerp(wrist, t, 0.45)
        chain_boxes(b, [wrist, knuckle, t], 1.0, 0.35, spar)
        cbox(b, knuckle, (1.1, 1.1, 1.1), spar)
    if vanes:
        # light vanes instead of skin: long glowing blades fanned from the wrist (Teia)
        for k, (t, col) in enumerate(zip(tips, vanes)):
            seg(b, lerp(wrist, t, 0.55), lerp(wrist, t, 1.3), 1.2, 0.3, M('energy', col, glow=True), up=(0, -1, 0))
        if skin_kw is None:
            return b
    body_end = P((1.2, fingers[-1][1] * 0.8))
    outline = [(x0, z0), (elbow[0], elbow[2]), (wrist[0], wrist[2])]
    for i, t in enumerate(tips):
        outline.append((t[0], t[2]))
        if i + 1 < len(tips):
            n = tips[i + 1]
            mid = ((t[0] + n[0]) / 2, (t[2] + n[2]) / 2)
            outline.append((mid[0] * 0.7 + wrist[0] * 0.3, mid[1] * 0.7 + wrist[2] * 0.3))
    outline.append((body_end[0], body_end[2]))
    xs = [p[0] for p in outline]
    zs = [p[1] for p in outline]
    veins = [(wrist[0], wrist[2], t[0], t[2]) for t in tips] + [(elbow[0], elbow[2], body_end[0], body_end[2])]
    for i in range(len(tips) - 1):
        a, c = tips[i], tips[i + 1]
        m = lerp(a, c, 0.5)
        veins.append((lerp(wrist, a, 0.6)[0], lerp(wrist, a, 0.6)[2], m[0], m[2]))
    mat = M('wingskin', membrane, poly=outline, axes='xz', veins=veins, accent=accent, glow=glow, **(skin_kw or {}))
    box(b, (min(xs), y + 0.3, min(zs)), (max(xs), y + 0.3, max(zs)), mat)
    return b


def plated_tail(r, parent, start, lengths, widths, skin, plate, spike_mat, droop=0.15, amp=0.12, speed=0.07, pairs=False,
                spikes=True):
    p = np.asarray(start, float)
    bone = parent
    ends = []
    n = len(lengths)
    for i, (L, w) in enumerate(zip(lengths, widths)):
        bone = r.bone(f'tail{i + 1}', bone, tuple(p), anim='tail', i=i, amp=amp, speed=speed)
        ang = droop * (1 - i / n)
        q = p + np.array([0.0, math.sin(ang) * L, math.cos(ang) * L])
        seg(bone, p, q, w, w * 0.92, skin, up=(0, -1, 0), ext=w * 0.3)
        mid = (p + q) / 2
        box(bone, (-w * 0.4, mid[1] - w * 0.62, mid[2] - L * 0.35), (w * 0.4, mid[1] - w * 0.4, mid[2] + L * 0.35), plate,
            rot=(0.25, 0, 0), pivot=tuple(mid))
        if spikes and i < n - 1:
            if pairs:
                for sx in (-1, 1):
                    spike(bone, (sx * w * 0.35, mid[1] - w * 0.45, mid[2]), (sx * (w * 0.35 + 1.0), mid[1] - w * 0.45 - max(0.9, w * 0.4), mid[2] + 1.0),
                          max(0.45, w * 0.16), spike_mat)
            else:
                spike(bone, (0, mid[1] - w * 0.5, mid[2]), (0, mid[1] - w * 0.5 - max(1.0, w * 0.55), mid[2] + 1.2), max(0.5, w * 0.2), spike_mat)
        ends.append((bone, tuple(q)))
        p = q
    return ends


def wyvern(key, spec):
    """A four-legged, two-winged dragon (Demiurgos, Teia) from a spec dict."""
    r = rig(key)
    skin, plate, hornm, belly = spec['skin'], spec['plate'], spec['horn'], spec['belly']
    claw = spec.get('claw', M('horn', '#d8cfb8'))
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 13, 2), anim='breath')
    rbox(body, (-4.8, 8.6, -9.8), (4.8, 17.4, -1.0), skin, bevel=1.3)                 # chest
    rbox(body, (-4.3, 9.2, -1.6), (4.3, 17.2, 8.0), skin, bevel=1.2)                  # belly
    rbox(body, (-4.0, 9.4, 7.4), (4.0, 16.2, 13.2), skin, bevel=1.1)                  # hips
    for z0, z1 in ((-8.8, -1.4), (-1.0, 7.4)):
        box(body, (-3.4, 17.2, z0), (3.4, 17.8, z1), belly)
    dorsal_plates(body, -8.5, 12.0, lambda z: 8.8 if z < 7 else 9.3, 8, lambda t: 4.0 - 1.2 * t, 1.6, plate, hornm,
                  lambda t: 2.6 - 1.0 * t)
    for sx in (-1, 1):                                                                # shoulder plates
        box(body, (sx * 4.2, 9.0, -9.0), (sx * 5.4, 13.6, -3.4), plate, rot=(0, 0, sx * 0.25), pivot=(sx * 4.8, 11.0, -6.0))
        spike(body, (sx * 5.0, 9.8, -4.0), (sx * 6.2, 8.6, -1.6), 0.7, hornm)
    neck = plated_neck(r, body, [(0, 12.2, -8.6), (0, 9.6, -12.2), (0, 6.6, -14.8), (0, 4.6, -16.2)], [5.4, 4.8, 4.2], skin, plate,
                       hornm, belly)
    drake_head(r, neck, (0, 1.6, -15.6), spec.get('head_scale', 1.0), dict(skin=skin, plate=plate, horn=hornm, eye=spec['eye'],
               mouth=M('mouth', '#43101c'), tooth=M('tooth', '#efe6d2'), horns=spec.get('horns', 'swept'), jaw=belly,
               crest=spec.get('crest', 2), nose_horn=spec.get('nose_horn', False), open=spec.get('open', 0.16), gem=spec.get('head_gem')))
    for sx in (-1, 1):
        fore_leg(r, body, 'leg_f' + ('r' if sx < 0 else 'l'), 'leg_r' if sx < 0 else 'leg_l', sx, (sx * 4.6, 13.6, -6.0),
                 (sx * 5.2, 18.4, -7.4), (sx * 5.0, 22.4, -6.4), 2.6, skin, plate, claw)
        hind_leg(r, body, 'leg_b' + ('r' if sx < 0 else 'l'), 'leg_l' if sx < 0 else 'leg_r', sx, (sx * 4.3, 13.4, 9.8),
                 (sx * 4.9, 17.6, 6.8), (sx * 4.8, 21.0, 11.4), (sx * 4.8, 22.6, 9.6), 3.0, skin, plate, claw)
    ws = spec.get('wing_scale', 1.0)
    sc2 = lambda pts: [(x * ws, z * ws) for x, z in pts]
    for sx in (-1, 1):
        drake_wing(r, body, sx, (sx * 4.4, 9.4, -5.6), sc2([(8.5, 0.5), (16.0, 3.0)]),
                   sc2([(24.0, 9.0), (21.5, 16.0), (15.0, 19.0), (8.0, 17.0)]), spec['membrane'], spec.get('spar', plate), claw,
                   rot=spec.get('wing_rot', (0.4, 0.25, 0.6)), accent=spec.get('vein'), glow=spec.get('vein_glow', False),
                   vanes=spec.get('vanes'), skin_kw=spec.get('wing_kw'))
    ends = plated_tail(r, body, (0, 12.6, 12.8), [5.0, 5.0, 4.6, 4.2, 3.8, 3.4, 3.0], [4.8, 4.0, 3.4, 2.8, 2.2, 1.7, 1.3], skin, plate,
                       hornm, droop=0.16)
    if spec.get('tail_tip'):
        spec['tail_tip'](r, ends[-1])
    if spec.get('extra'):
        spec['extra'](r, root, body)
    return fit_height(r, ('wing', 'shards'))


@recipe
def demiurgos():
    # 空創龍王 デミウルゴス: a small (five metre) dragon of black scales glinting as if set with rainbow gems; more
    # mystery than menace. A crown of horns for the king of dragons, amethyst eyes, star-veined wings, a gem-cluster
    # tail tip, and shards of things it has imagined into being drifting round it.
    gems = ['#ff6ad5', '#6af0ff', '#ffe46a', '#7dff8a', '#b48cff']
    def tip(r, end):
        b, (x, y, z) = end
        for k, (dx, dy, dz, sz) in enumerate(((0, 0, 1.6, 2.0), (0.9, -0.8, 0.8, 1.3), (-0.9, -0.6, 0.9, 1.2), (0, 0.9, 0.6, 1.1))):
            cbox(b, (x + dx, y + dy, z + dz), (sz, sz * 1.6, sz), M('gem', gems[k % len(gems)], glow=True), rot=(0.3, 0.7, 0.4 * k))
    def extra(r, root, body):
        orbit = r.bone('shards', root, (0, 8, 2), anim='spin', speed=0.02, cast=0.0)
        for k in range(6):
            a = k * math.pi / 3
            x, z = math.cos(a) * 17.0, 2 + math.sin(a) * 17.0
            cbox(orbit, (x, 4.0 + (k % 2) * 3.0, z), (1.2, 2.6, 1.2), M('gem', gems[k % len(gems)], glow=True), rot=(0.5, a, 0.6))
        for k, (x, y, z) in enumerate(((-4.9, 11.5, -5.5), (4.9, 11.5, -5.5), (-4.4, 12.6, 3.5), (4.4, 12.6, 3.5), (0, 8.4, -3.0))):
            cbox(body, (x, y, z), (1.2, 1.2, 1.2), M('gem', gems[k % len(gems)], glow=True), rot=(0.6, 0.8, 0.3))
    return wyvern('demiurgos', dict(
        skin=M('shingle', '#36324c', belly='#5a5078', glints=gems, glint_rate=0.05), plate=M('carapace', '#2a263c', accent='#b48cff'),
        horn=M('horn', '#3a3450', tip='#e6d2ff', glow=True), belly=M('carapace', '#5a5078'),
        eye=M('eye', '#d29cff', pupil='slit', mood='fierce', lid='#1c1a28', glow_amount=1.0), membrane='#221a3a', vein='#b48cff',
        vein_glow=True, wing_kw=dict(stars=0.035), wing_scale=1.3, horns='crown', head_gem=M('gem', '#ff6ad5', glow=True), tail_tip=tip,
        extra=extra))


@recipe
def teia():
    # 光越天龍 テイア: a small, slender sky dragon a few metres long. A shell of dense unknown metal, machine and life
    # fused: smooth armour plates in rows, a streamlined wedge head and limbs, photon-flow wings that spread rainbow
    # streaks with every beat, an organ in the chest that turns mana into light, thrusters on the back. More a flying
    # weapon than a beast to look at; a cheerful big brother in character (ring-pupil eyes, a grin).
    r = rig('teia')
    hull = M('carapace', '#d6dee8', accent='#7ff6ff')
    plate = M('carapace', '#eef2f6', accent='#7ff6ff')
    dark = M('carapace', '#56606e')
    trim = M('carapace', '#9aa6b6', accent='#ff9af2')
    claw = M('horn', '#e8eef4', tip='#7ff6ff', glow=True)
    light = lambda c: M('energy', c, glow=True)
    rainbow = ['#ff6a8a', '#ffb36a', '#ffe46a', '#7dff8a', '#6af0ff', '#8a9cff', '#d58aff']
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 12.5, 2), anim='breath')
    rbox(body, (-3.4, 9.8, -9.0), (3.4, 15.6, -1.6), hull, bevel=1.0)               # chest
    rbox(body, (-2.7, 10.4, -2.2), (2.7, 15.0, 6.2), hull, bevel=0.9)               # waist
    rbox(body, (-3.1, 10.2, 5.6), (3.1, 15.0, 10.8), hull, bevel=1.0)               # hips
    rbox(body, (-2.6, 15.2, -8.4), (2.6, 16.0, -2.0), dark, bevel=0.3)              # keel
    rbox(body, (-2.0, 14.8, -2.0), (2.0, 15.6, 6.0), dark, bevel=0.3)
    # the light organ: a cyan core behind a split chest plate
    cbox(body, (0, 12.6, -9.15), (2.2, 2.2, 0.6), light('#bffaff'), rot=(0, 0, 0.785))
    for sx in (-1, 1):
        box(body, (sx * 0.9, 10.2, -9.4), (sx * 3.2, 15.2, -8.8), plate, rot=(0, sx * 0.25, 0), pivot=(sx * 2, 12.6, -9.0))
        # flank armour: three overlapping plates with a glowing seam between them
        for k, (z0, z1) in enumerate(((-8.4, -2.8), (-3.2, 3.0), (2.6, 9.8))):
            box(body, (sx * 3.0, 10.6, z0), (sx * 3.6, 14.0, z1), plate, rot=(0, 0, sx * 0.12), pivot=(sx * 3.3, 12.3, 0))
        box(body, (sx * 3.05, 14.1, -8.0), (sx * 3.15, 14.4, 9.4), light('#7ff6ff'))
    dorsal_plates(body, -8.0, 9.6, lambda z: 9.9 if z < 5.4 else 10.1, 7, lambda t: 5.0 - 1.4 * t, 1.2, plate, lean=0.5)
    # back thrusters between the wings
    for sx in (-1, 1):
        rbox(body, (sx * 1.6 - 1.0, 7.6, -1.0), (sx * 1.6 + 1.0, 9.6, 6.4), trim, bevel=0.4)
        box(body, (sx * 1.6 - 1.2, 7.4, 5.4), (sx * 1.6 + 1.2, 9.8, 6.8), dark)
        cbox(body, (sx * 1.6, 8.6, 6.9), (1.6, 1.6, 0.3), light('#bffaff'))
        box(body, (sx * 1.6 - 0.15, 6.6, 0.0), (sx * 1.6 + 0.15, 7.6, 4.8), plate)      # a fin on each pod
    # neck: three slim plated segments, no spikes
    neck = plated_neck(r, body, [(0, 11.4, -8.4), (0, 9.0, -11.4), (0, 6.6, -13.6), (0, 5.0, -15.0)], [3.8, 3.4, 3.0], hull, plate,
                       claw, dark, spikes=False)
    # head: a long wedge with a visor ridge and swept blades, eyes set in the sides
    head = r.bone('head', neck, (0, 5.4, -15.2), anim='head')
    rbox(head, (-2.4, 2.4, -20.2), (2.4, 6.0, -14.2), hull, bevel=0.7)                   # cranium
    rbox(head, (-1.9, 3.0, -25.6), (1.9, 5.4, -19.6), hull, bevel=0.5, faces={'bottom': M('mouth', '#2a3a48')})   # snout
    box(head, (-1.2, 3.3, -27.0), (1.2, 5.1, -25.4), plate, faces={'bottom': M('mouth', '#2a3a48')})
    box(head, (-0.8, 1.7, -25.2), (0.8, 2.6, -14.0), plate, rot=(-0.06, 0, 0), pivot=(0, 2.4, -20))   # visor ridge
    box(head, (-0.2, 1.65, -25.0), (0.2, 1.75, -15.0), light('#7ff6ff'))
    for sx in (-1, 1):
        side = 'left' if sx > 0 else 'right'
        cbox(head, (sx * 2.4, 3.9, -19.0), (0.25, 1.9, 3.8), M('simple', '#0c1218'))
        eye(head, (sx * 2.52, 3.9, -19.0), 3.4, 1.5, side, M('eye', '#7ff6ff', pupil='ring', mood='happy', lid='#2a3038', glow_amount=1.0))
        # brow blades swept back past the skull, and a lower pair along the cheeks
        box(head, (sx * 1.2, 1.6, -21.0), (sx * 2.0, 2.4, -9.0), plate, rot=(-0.2, sx * -0.16, sx * 0.25), pivot=(sx * 1.6, 2.0, -20.0))
        box(head, (sx * 1.6, 1.9, -20.4), (sx * 1.7, 2.1, -9.6), light('#7ff6ff'), rot=(-0.2, sx * -0.16, sx * 0.25), pivot=(sx * 1.6, 2.0, -20.0))
        box(head, (sx * 2.2, 4.4, -17.6), (sx * 2.8, 5.2, -11.2), trim, rot=(-0.1, sx * -0.3, 0), pivot=(sx * 2.5, 4.8, -17.0))
        teeth(head, sx * 1.55, 5.4, -25.4, -20.2, 4, 0.5, M('tooth', '#f4f8ff'), down=True)
    jaw = r.bone('jaw', head, (0, 5.6, -15.6), rot=(0.2, 0, 0), anim='jaw')
    rbox(jaw, (-1.7, 5.4, -25.4), (1.7, 6.8, -15.6), dark, bevel=0.4, faces={'top': M('mouth', '#2a3a48')})
    for sx in (-1, 1):
        teeth(jaw, sx * 1.25, 5.5, -25.0, -20.6, 3, 0.45, M('tooth', '#f4f8ff'), down=False)
    # legs: slim, with blade fins on the forearms and shins
    for sx in (-1, 1):
        up, low = fore_leg(r, body, 'leg_f' + ('r' if sx < 0 else 'l'), 'leg_r' if sx < 0 else 'leg_l', sx, (sx * 3.4, 13.2, -5.6),
                           (sx * 3.9, 17.8, -6.8), (sx * 3.8, 22.4, -6.0), 1.9, hull, plate, claw)
        box(low, (sx * 3.9 - 0.12, 17.6, -6.4), (sx * 3.9 + 0.12, 21.0, -3.6), light('#7ff6ff'), rot=(-0.3, 0, 0), pivot=(sx * 3.9, 18, -6))
        up, low = hind_leg(r, body, 'leg_b' + ('r' if sx < 0 else 'l'), 'leg_l' if sx < 0 else 'leg_r', sx, (sx * 3.2, 13.0, 8.6),
                           (sx * 3.7, 17.2, 6.0), (sx * 3.6, 20.8, 10.2), (sx * 3.6, 22.6, 8.6), 2.2, hull, plate, claw)
    # wings: a metal frame of arm and four fingers, a membrane of streaming rainbow light, light blades past the tips
    for sx in (-1, 1):
        drake_wing(r, body, sx, (sx * 3.2, 9.6, -5.2), [(7.5, 1.0), (14.5, 3.4)],
                   [(23.0, 6.0), (21.0, 12.5), (15.5, 16.0), (8.5, 14.5)], '#cfefff', trim, claw, rot=(0.35, 0.3, 0.5),
                   accent='#ffffff', glow=True, vanes=['#ff6a8a', '#ffe46a', '#7dff8a', '#6af0ff'],
                   skin_kw=dict(bands=rainbow, edge='#7ff6ff'))
    # tail: slim plates, a cross of light at the end like a stabiliser
    ends = plated_tail(r, body, (0, 12.4, 10.4), [4.6, 4.6, 4.4, 4.0, 3.6, 3.2], [3.6, 3.0, 2.5, 2.0, 1.6, 1.2], hull, plate,
                       claw, droop=0.1, spikes=False)
    b, (x, y, z) = ends[-1]
    box(b, (-0.15, y - 3.0, z - 2.0), (0.15, y + 3.0, z + 1.6), light('#7ff6ff'), rot=(0.5, 0, 0), pivot=(0, y, z))
    box(b, (-3.0, y - 0.15, z - 2.0), (3.0, y + 0.15, z + 1.6), light('#ff9af2'))
    return fit_height(r, ('wing',))


# ------------------------------------------------------------------------------------------- lofted bodies

def stations(ctrl, step=1.6):
    """Control stations (z, top, bottom, width[, x]) refined to one every `step` pixels along z."""
    out = [tuple(ctrl[0])]
    for a, b in zip(ctrl, ctrl[1:]):
        n = max(1, int(round(abs(b[0] - a[0]) / step)))
        out += [lerp(a, b, k / n) for k in range(1, n + 1)]
    return out


def loft(bone, ctrl, mat, step=1.6, bevel=0.3, faces=None, caps=True):
    """A smooth body lofted through control stations (z, top, bottom, width[, x]): one slice per step, each an
    octagonal section (two crossing boxes) sized to the mean of its two stations, so the outline tapers in small
    visible steps like a hand-built Blockbench whale. Slice ends hidden by a larger neighbour are left out."""
    st = stations(ctrl, step)
    sl = []
    for a, b in zip(st, st[1:]):
        m = lerp(a, b, 0.5)
        x = m[4] if len(m) > 4 else 0.0
        sl.append((min(a[0], b[0]), max(a[0], b[0]), m[1], m[2], m[3], x))
    sl.sort()
    for i, (z0, z1, top, bot, w, x) in enumerate(sl):
        h = bot - top
        bv = min(bevel * min(w, h), w * 0.3, h * 0.3)
        skip = []
        for j, face in ((i - 1, 'front'), (i + 1, 'back')):
            if 0 <= j < len(sl):
                _, _, t2, b2, w2, x2 = sl[j]
                if t2 <= top + 1e-6 and b2 >= bot - 1e-6 and w2 >= w - 1e-6 and abs(x2 - x) < 1e-6:
                    skip.append(face)
            elif not caps:
                skip.append(face)
        kw = dict(skip=tuple(skip))
        if faces:
            kw['faces'] = faces
        box(bone, (x - w / 2, top + bv, z0), (x + w / 2, bot - bv, z1), mat, **kw)
        box(bone, (x - w / 2 + bv, top, z0), (x + w / 2 - bv, bot, z1), mat, **kw)
    return st


def section(ctrl, z):
    """(top, bottom, width) of a lofted body at z."""
    for a, b in zip(ctrl, ctrl[1:]):
        if min(a[0], b[0]) <= z <= max(a[0], b[0]):
            t = (z - a[0]) / ((b[0] - a[0]) or 1)
            m = lerp(a, b, t)
            return m[1], m[2], m[3]
    a = ctrl[0] if abs(z - ctrl[0][0]) < abs(z - ctrl[-1][0]) else ctrl[-1]
    return a[1], a[2], a[3]


def tail_loft(r, parent, ctrl, cuts, mat, amp=0.14, speed=0.07, name='tail', **kw):
    """A lofted tail split into bones at the z values in cuts (each its own 'tail' link)."""
    bones = []
    bone = parent
    zs = [ctrl[0][0]] + list(cuts) + [ctrl[-1][0]]
    for i in range(len(zs) - 1):
        z0, z1 = zs[i], zs[i + 1]
        t, b, w = section(ctrl, z0)
        bone = r.bone(f'{name}{i + 1}', bone, (0, (t + b) / 2, z0), anim='tail', i=i, amp=amp, speed=speed)
        part = [(z0,) + section(ctrl, z0)] + [c for c in ctrl if z0 < c[0] < z1] + [(z1,) + section(ctrl, z1)]
        loft(bone, part, mat, **kw)
        bones.append(bone)
    return bones


def fang_rows(bone, x_of, y, z0, z1, n, size, mat, down=True, rows=2):
    """Several rows of teeth, the outer row long and the inner rows shorter and set back (a shark's battery)."""
    for k in range(rows):
        sz = size * (1.0 - 0.28 * k)
        for sx in (-1, 1):
            teeth(bone, sx * (x_of - k * size * 0.9), y, z0 + k * size * 0.8, z1, max(2, n - k), sz, mat, down=down)


@recipe
def enkou():
    # 災極海獣 淵煌: a sea beast hundreds of metres long that sleeps in the lightless deep. A shark's edges, an orca's
    # streamlined body and an ancient dragon's dignity, covered in obsidian scales that melt into black water; a great
    # head with row upon row of sharp teeth; pale blue eyes like a deep-sea fish's light organs; a long tail whose
    # slightest stroke turns the current; glowing patterns like sea creatures across the hide.
    r = rig('enkou')
    glowc = '#8fe8ff'
    hide = M('shingle', '#141b28', belly='#d6e2ea', countershade=(15.6, 1.2), scale_size=1.25, mark=glowc,
             waves=[(10.8, 0.7, 14.0, 0.0)], dots=(14.2, 2.8, 0.3))
    head_hide = M('shingle', '#141b28', belly='#d6e2ea', countershade=(14.8, 0.6), scale_size=1.1, mark=glowc, dots=(13.8, 2.2, 0.3))
    plate = M('carapace', '#0e131c', accent=glowc)
    jawm = M('shingle', '#d6e2ea', belly='#d6e2ea', scale_size=0.9)
    hornm = M('horn', '#1a2232', tip=glowc, glow=True)
    tooth = M('tooth', '#f4efe4')
    mouth = M('mouth', '#3a0e18')
    fin_c, edge = '#121a28', glowc
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.2, speed=0.05)
    body = r.bone('body', root, (0, 13, 0), anim='sway', ax=1, amp=0.05, speed=0.06)
    trunk = [(-11, 7.4, 18.8, 10.8), (-6, 6.8, 19.4, 12.2), (0, 6.8, 19.4, 12.6), (6, 7.4, 18.8, 11.6), (11, 8.4, 17.8, 9.8),
             (16, 9.4, 16.6, 7.6)]
    loft(body, trunk, hide)
    # a dragon's ridge: low obsidian plates down the spine, the great dorsal fin standing among them
    for k in range(7):
        z = -10 + k * 3.6
        t, b, w = section(trunk, z)
        if -3 < z < 8:
            continue
        box(body, (-1.1, t - 1.0, z - 1.2), (1.1, t + 0.4, z + 1.6), plate, rot=(0.45, 0, 0), pivot=(0, t, z))
    fin(body, [(-4.0, 7.2), (-0.5, -1.5), (3.0, -7.5), (5.2, -8.4), (5.6, -6.6), (6.4, 0.5), (9.0, 7.4)], 'zy', 0.0, fin_c,
        accent=edge, glow=True, veins=[(-2, 7, 4.2, -7.6), (2, 7, 5.6, -4.0), (5, 7, 7.0, 2.0)])
    for sx in (-1, 1):
        # orca paddles low on the flanks, small pelvic fins behind
        sea_fin_bone(r, body, 'fin_' + ('r' if sx < 0 else 'l'), (sx * 5.6, 17.0, -5.0),
                     [(sx * 5.6, -8.0), (sx * 12.0, -4.5), (sx * 17.5, 1.5), (sx * 16.0, 3.2), (sx * 11.0, 1.8), (sx * 5.6, -1.5)],
                     'xz', 17.4, fin_c, edge, rot=(0.0, 0.0, sx * -0.4), amp=0.14, phase=sx)
        fin(body, [(sx * 4.2, 9.0), (sx * 8.4, 12.0), (sx * 7.6, 13.4), (sx * 4.2, 13.0)], 'xz', 17.0, fin_c, accent=edge)
        # gill slits behind the head
        for k in range(4):
            box(body, (sx * (5.5 + 0.02 * k), 10.6 + k * 0.2, -10.4 + k * 1.15), (sx * (5.72 + 0.02 * k), 15.6 - k * 0.2, -10.0 + k * 1.15),
                M('simple', '#05070a'))
    # head: a long, flat-topped skull with an overhanging snout, brow armour and swept dragon horns
    head = r.bone('head', body, (0, 13, -11), anim='head')
    skull = [(-31.5, 11.2, 13.4, 2.6), (-29.5, 9.8, 13.9, 5.0), (-25, 8.6, 14.3, 7.4), (-20, 7.8, 14.6, 9.2), (-15, 7.3, 14.9, 10.4),
             (-10.5, 7.2, 15.1, 10.8)]
    loft(head, skull, head_hide, faces={'bottom': mouth})
    for sx in (-1, 1):
        side = 'left' if sx > 0 else 'right'
        t, b, w = section(skull, -18.5)
        # a heavy armoured brow over each eye, a ridge of plates behind it
        box(head, (sx * 1.4, t - 0.5, -23.0), (sx * (w / 2 + 0.2), t + 0.7, -15.4), plate, rot=(-0.1, 0, sx * 0.22),
            pivot=(sx * (w / 2), t + 0.6, -19))
        cbox(head, (sx * (w / 2 - 0.05), 10.6, -18.6), (0.3, 2.2, 4.0), M('simple', '#05080c'))
        eye(head, (sx * (w / 2 + 0.08), 10.6, -18.6), 3.6, 1.6, side, M('eye', '#9fe8ff', pupil='slit', mood='fierce', lid='#0e131c',
            glow_amount=1.0))
        # photophores in a line under the eye
        for k in range(4):
            cbox(head, (sx * (section(skull, -24 + k * 2.6)[2] / 2 + 0.1), 12.6, -24 + k * 2.6), (0.3, 0.6, 0.6),
                 M('energy', glowc, glow=True))
        # swept horns: a long pair from the back of the skull, a short pair below
        horn(head, [(sx * 3.0, 7.8, -14.0), (sx * 4.2, 6.6, -10.0), (sx * 5.0, 6.0, -5.6), (sx * 5.2, 6.2, -1.4)], 1.8, 0.4, hornm)
        horn(head, [(sx * 4.8, 9.6, -12.5), (sx * 6.6, 9.0, -9.6), (sx * 7.6, 8.4, -6.8)], 1.2, 0.3, hornm)
    # teeth: two rows along the upper jaw, long fangs in front
    fang_rows(head, 4.0, 14.6, -27.5, -15.5, 8, 0.8, tooth, down=True)
    for sx in (-1, 1):
        teeth(head, sx * 1.8, 13.9, -29.8, -28.0, 2, 0.95, tooth, down=True)
    jaw = r.bone('jaw', head, (0, 15.2, -11.0), rot=(0.26, 0, 0), anim='jaw')
    lower = [(-30.0, 14.2, 15.4, 3.6), (-26, 14.4, 16.8, 6.6), (-20, 14.7, 18.0, 8.6), (-14, 15.0, 18.7, 10.0), (-10.5, 15.1, 18.9, 10.4)]
    loft(jaw, lower, jawm, faces={'top': mouth})
    fang_rows(jaw, 3.6, 14.8, -28.0, -15.0, 7, 0.75, tooth, down=False)
    for sx in (-1, 1):
        box(jaw, (sx * 2.2, 17.2, -24.0), (sx * 4.8, 18.4, -13.0), plate, rot=(0, 0, sx * -0.2), pivot=(sx * 3.5, 17.8, -18))
    # tail: a long lofted tail in four links, a low ridge, and a shark's crescent fluke
    tail_ctrl = [(16, 9.4, 16.6, 7.6), (22, 10.4, 15.6, 5.6), (28, 11.2, 14.8, 4.0), (34, 11.8, 14.2, 2.8), (40, 12.2, 13.8, 1.8)]
    tb = tail_loft(r, body, tail_ctrl, [22, 28, 34], hide, amp=0.16, speed=0.07)
    for i, b in enumerate(tb[:-1]):
        z = 19 + i * 6
        t, _, w = section(tail_ctrl, z)
        box(b, (-0.8, t - 0.9, z - 1.0), (0.8, t + 0.3, z + 1.4), plate, rot=(0.45, 0, 0), pivot=(0, t, z))
    fin(tb[1], [(23.0, 10.6), (26.5, 6.8), (28.0, 6.6), (28.2, 10.9)], 'zy', 0.0, fin_c, accent=edge)   # second dorsal
    tz, ty = 39.5, 13.0
    fin(tb[-1], [(tz - 2.5, ty - 0.6), (tz + 3.0, ty - 10.5), (tz + 6.5, ty - 12.0), (tz + 4.0, ty - 5.0), (tz + 3.2, ty - 0.2),
                 (tz + 4.6, ty + 5.5), (tz + 2.6, ty + 6.4), (tz - 2.5, ty + 0.8)], 'zy', 0.0, fin_c, accent=edge, glow=True,
        veins=[(tz - 1, ty, tz + 5.6, ty - 11.0), (tz - 1, ty, tz + 3.4, ty + 5.6), (tz, ty, tz + 3.6, ty - 4.0)])
    return r


def coral(bone, x, y, z, kind, colour, s=1.0):
    """A little piece of reef standing on the surface at (x, y, z): 'branch' (staghorn), 'fan', 'brain', 'weed'."""
    m = M('simple', colour)
    if kind == 'branch':
        seg(bone, (x, y, z), (x, y - 2.4 * s, z), 0.6 * s, 0.6 * s, m)
        for dx, dz, h in ((-0.9, 0.2, 1.6), (0.8, -0.3, 1.9), (0.1, 0.9, 1.3)):
            seg(bone, (x, y - 1.1 * s, z), (x + dx * s, y - (1.1 + h) * s, z + dz * s), 0.45 * s, 0.45 * s, m)
    elif kind == 'fan':
        fin(bone, [(x - 1.6 * s, y - 1.0 * s), (x - 1.2 * s, y - 3.0 * s), (x, y - 3.6 * s), (x + 1.3 * s, y - 2.9 * s),
                   (x + 1.6 * s, y - 1.0 * s), (x, y)], 'xy', z, colour, accent=None,
            veins=[(x, y, x - 1.2 * s, y - 2.8 * s), (x, y, x, y - 3.4 * s), (x, y, x + 1.2 * s, y - 2.7 * s)])
    elif kind == 'brain':
        rbox(bone, (x - 1.0 * s, y - 1.3 * s, z - 1.0 * s), (x + 1.0 * s, y + 0.1, z + 1.0 * s), M('rock', colour), bevel=0.4 * s)
    else:
        for k, (dx, h) in enumerate(((-0.3, 3.2), (0.3, 2.4), (0.0, 4.0))):
            seg(bone, (x + dx * s, y, z + dx * s), (x + dx * s * 2.4, y - h * s, z + 0.6 * s), 0.3 * s, 0.3 * s, m, up=(0, 0, -1))


def shrine(bone, x, y, z, s=1.0, stone='#e8e2d2', roof='#3f8a8c', gold='#e8c46a'):
    """A small white temple with columns and a green copper roof standing on the surface at (x, y, z)."""
    st, rf, gd = M('carapace', stone), M('carapace', roof), M('simple', gold)
    rbox(bone, (x - 2.6 * s, y - 0.8 * s, z - 3.4 * s), (x + 2.6 * s, y + 0.2, z + 3.4 * s), st, bevel=0.2 * s)       # podium
    for cx in (-1.9, 1.9):
        for cz in (-2.7, -0.9, 0.9, 2.7):
            seg(bone, (x + cx * s, y - 0.8 * s, z + cz * s), (x + cx * s, y - 3.8 * s, z + cz * s), 0.55 * s, 0.55 * s, st)
    box(bone, (x - 2.5 * s, y - 4.4 * s, z - 3.3 * s), (x + 2.5 * s, y - 3.8 * s, z + 3.3 * s), st)                   # lintel
    for k in range(4):                                                                                                  # stepped roof
        w = 2.8 - k * 0.75
        box(bone, (x - w * s, y - (4.4 + 0.55 * (k + 1)) * s, z - 3.6 * s), (x + w * s, y - (4.4 + 0.55 * k) * s, z + 3.6 * s), rf)
    cbox(bone, (x, y - 7.0 * s, z), (0.6 * s, 0.9 * s, 0.6 * s), gd)
    cbox(bone, (x, y - 2.3 * s, z), (1.2 * s, 1.6 * s, 1.2 * s), M('energy', '#9ff4ff', glow=True))                     # the sacred light


def hut(bone, x, y, z, s=1.0, wall='#d8c8a4', roof='#a2553a'):
    box(bone, (x - 1.0 * s, y - 1.6 * s, z - 1.2 * s), (x + 1.0 * s, y, z + 1.2 * s), M('carapace', wall))
    box(bone, (x - 1.25 * s, y - 2.1 * s, z - 1.4 * s), (x + 1.25 * s, y - 1.6 * s, z + 1.4 * s), M('carapace', roof))
    box(bone, (x - 0.7 * s, y - 2.6 * s, z - 1.4 * s), (x + 0.7 * s, y - 2.1 * s, z + 1.4 * s), M('carapace', roof))
    box(bone, (x - 0.3 * s, y - 1.0 * s, z - 1.25 * s), (x + 0.3 * s, y, z - 1.2 * s), M('simple', '#3a2a1c'))


@recipe
def bahamut():
    # 大海皇鯨 バハムート: a dragon-whale hundreds of kilometres long, emperor of the sea. A whale's smooth streamlined
    # body with a dragon's scales and horns, a fin on the back great enough to raise currents, a deep blue body that
    # looks like a moving island from afar; coral reefs and seaweed have taken root on the back, with a temple and a
    # settlement built there in old legends. Gentle and unhurried: kind eyes and a slow smile.
    r = rig('bahamut')
    hide = M('shingle', '#1f548c', belly='#d4e4ee', countershade=(17.2, 0.8), scale_size=1.7, mark='#bff0ff',
             dots=(13.2, 3.4, 0.34))
    head_hide = M('shingle', '#1f548c', belly='#d4e4ee', countershade=(16.0, 0.4), scale_size=1.4)
    jawm = M('shingle', '#d4e4ee', belly='#e4eef4', scale_size=1.0)
    plate = M('carapace', '#173f6c', accent='#8ff0ff')
    hornm = M('horn', '#efe2c0', tip='#f6d46e')
    mouth = M('mouth', '#4a1c2a')
    fin_c, edge = '#1a4a7c', '#8ff0ff'
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.0, speed=0.04)
    body = r.bone('body', root, (0, 12, 0), anim='sway', ax=1, amp=0.03, speed=0.04)
    trunk = [(-18, 6.6, 20.2, 14.8), (-12, 6.0, 20.6, 15.8), (-4, 5.6, 20.8, 16.2), (4, 5.8, 20.4, 15.4), (12, 7.2, 19.2, 12.8),
             (19, 9.0, 17.6, 9.2)]
    loft(body, trunk, hide, step=1.8)
    # head: a long whale head, a smiling mouth line, kind eyes low by the corners of the mouth
    head = r.bone('head', body, (0, 13, -18), anim='head')
    skull = [(-36, 10.8, 15.4, 6.8), (-34, 9.2, 15.8, 10.0), (-29, 7.8, 16.1, 12.8), (-23, 7.0, 16.3, 14.2), (-18, 6.6, 16.5, 14.8)]
    loft(head, skull, head_hide, faces={'bottom': mouth}, step=1.8)
    for sx in (-1, 1):
        side = 'left' if sx > 0 else 'right'
        t, b, w = section(skull, -22.5)
        cbox(head, (sx * (w / 2 - 0.05), 14.2, -22.5), (0.3, 2.2, 3.2), M('simple', '#0b1a2c'))
        eye(head, (sx * (w / 2 + 0.08), 14.2, -22.5), 2.8, 1.8, side, M('eye', '#5ab8ff', pupil='round', sclera='#eef4f8', mood='kind',
            lid='#163c66', look=0.4, glow_amount=0.5))
        # dragon horns sweeping back from the crown, frills behind them, long barbels trailing from the snout
        horn(head, [(sx * 3.6, 7.4, -25.0), (sx * 5.0, 5.4, -22.0), (sx * 6.2, 4.6, -18.4), (sx * 6.8, 5.0, -15.0)], 2.0, 0.45, hornm)
        horn(head, [(sx * 5.6, 9.0, -22.5), (sx * 7.4, 8.4, -20.0), (sx * 8.4, 8.6, -17.6)], 1.2, 0.3, hornm)
        fin(head, [(sx * 5.8, -21.0), (sx * 9.4, -18.0), (sx * 9.0, -15.0), (sx * 6.8, -17.4), (sx * 7.0, -14.0), (sx * 5.8, -16.0)], 'xz',
            9.4, fin_c, accent=edge)
        b1 = r.bone('barbel_' + ('r' if sx < 0 else 'l'), head, (sx * 3.6, 14.4, -33.0), anim='sway', ax=1, amp=0.18, speed=0.06,
                    phase=sx)
        chain_boxes(b1, [(sx * 3.6, 14.4, -33.0), (sx * 6.4, 15.2, -30.0), (sx * 8.0, 16.6, -25.0), (sx * 8.6, 18.2, -20.0)], 0.7, 0.3,
                    M('horn', '#d8e4ec', tip='#8ff0ff', glow=True))
        # baleen fringe along the upper jaw
        teeth(head, sx * (section(skull, -27)[2] / 2 - 0.5), 16.0, -34.0, -19.0, 16, 0.45, M('tooth', '#e8dcc0'), down=True)
        # a row of scutes along the brow
        for k in range(4):
            z = -31 + k * 3.0
            t2, _, w2 = section(skull, z)
            box(head, (sx * 1.0, t2 - 0.5, z - 1.0), (sx * 2.6, t2 + 0.3, z + 1.4), plate, rot=(0.3, 0, 0), pivot=(sx * 1.8, t2, z))
    jaw = r.bone('jaw', head, (0, 16.4, -18), rot=(0.08, 0, 0), anim='jaw')
    lower = [(-35.4, 15.4, 17.0, 6.4), (-33, 15.8, 18.6, 9.8), (-28, 16.1, 19.8, 12.6), (-22, 16.3, 20.4, 14.2), (-18, 16.5, 20.6, 14.8)]
    loft(jaw, lower, jawm, faces={'top': mouth}, step=1.8)
    # the back: a reef, a temple and a village; the great sail fin rising behind them
    t0 = section(trunk, -10)[0]
    shrine(body, 0, t0 + 0.2, -10.0, s=0.95)
    for k, (x, z, kind, col) in enumerate(((-4.6, -14.5, 'branch', '#ff7a8a'), (4.4, -14.0, 'fan', '#ff9a5a'), (-5.2, -7.0, 'brain', '#c86ad8'),
                                           (5.0, -6.5, 'branch', '#ffd36a'), (-5.6, 1.8, 'weed', '#3fae6a'), (5.6, 2.4, 'weed', '#58c27a'),
                                           (-4.8, 3.6, 'fan', '#ff6ab0'), (4.6, 4.6, 'brain', '#ff8a6a'), (0.0, -16.0, 'weed', '#3fae6a'),
                                           (-6.2, -11.0, 'weed', '#58c27a'), (6.4, -10.0, 'branch', '#7ad8ff'))):
        tt, _, w = section(trunk, z)
        y = tt + 0.25 + (abs(x) / (w / 2)) ** 2 * 1.2
        coral(body, x, y, z, kind, col)
    for x, z in ((-4.0, -3.0), (3.8, -1.5), (-1.2, 0.5)):
        hut(body, x, section(trunk, z)[0] + 0.3 + (abs(x) / 7.0) ** 2, z, s=0.8)
    fin(body, [(0.0, 6.2), (3.0, -4.0), (7.0, -11.5), (10.5, -13.0), (12.5, -10.0), (13.0, -2.0), (16.5, 7.4)], 'zy', 0.0, fin_c,
        accent=edge, glow=True, veins=[(2, 6, 8.5, -12), (5, 6, 11.5, -11.5), (9, 6, 12.8, -4), (12, 7, 14.8, 1)])
    for k in range(5):
        z = 17 + k * 2.2
        tt, _, w = section(trunk + [(26, 10.4, 16.2, 6.4)], z)
        box(body, (-0.9, tt - 0.7, z - 0.9), (0.9, tt + 0.3, z + 1.3), plate, rot=(0.4, 0, 0), pivot=(0, tt, z))
    for sx in (-1, 1):
        # long humpback flippers with knobbed leading edges
        fb = sea_fin_bone(r, body, 'fin_' + ('r' if sx < 0 else 'l'), (sx * 7.4, 18.0, -12.0),
                          [(sx * 7.2, -14.5), (sx * 13.0, -12.0), (sx * 20.0, -6.0), (sx * 23.0, -1.5), (sx * 21.6, -0.6), (sx * 13.0, -5.6),
                           (sx * 7.2, -9.0)], 'xz', 18.2, fin_c, edge, rot=(0.0, 0.0, sx * -0.3), amp=0.1, phase=sx)
        for k in range(5):
            t = k / 4
            cbox(fb, (sx * (8.5 + 12.5 * t), 18.2, -13.6 + 10.0 * t), (1.1, 0.6, 1.1), M('carapace', '#d4e4ee'))
    tail_ctrl = [(19, 9.0, 17.6, 9.2), (26, 10.4, 16.2, 6.4), (32, 11.2, 15.4, 4.4), (38, 11.8, 14.8, 3.2), (43, 12.0, 14.6, 2.6)]
    tb = tail_loft(r, body, tail_ctrl, [26, 32, 38], hide, amp=0.12, speed=0.05, step=1.8)
    ty = 13.4
    fin(tb[-1], [(-1.2, 38.5), (-6.0, 40.0), (-12.0, 43.5), (-12.5, 46.0), (-7.0, 45.0), (-2.0, 44.0), (0.0, 45.5), (2.0, 44.0), (7.0, 45.0),
                 (12.5, 46.0), (12.0, 43.5), (6.0, 40.0), (1.2, 38.5)], 'xz', ty, fin_c, accent=edge, glow=True,
        veins=[(0, 39, -11, 44.5), (0, 39, 11, 44.5), (0, 39, -5, 44.0), (0, 39, 5, 44.0)])
    return r


def peak(bone, x, z, base, w, h, rock, snow=None, grass=None, steps=5, seed=0, lean=(0.0, 0.0)):
    """A crag of stacked, shrinking, slightly offset blocks rising from y = base (a mountain on Kurma's back);
    grass ledges low down, a snow cap on top."""
    rng = np.random.default_rng(seed)
    cx, cz = x, z
    tops = []
    for k in range(steps):
        t = k / steps
        hw = w * (1 - 0.8 * t) * (0.9 + 0.2 * rng.random())
        hd = w * (1 - 0.8 * t) * (0.9 + 0.2 * rng.random())
        y0, y1 = base - h * t, base - h * (t + 1 / steps)
        top = snow if (snow is not None and k >= steps - 2 and h > 9) else rock
        rbox(bone, (cx - hw / 2, y1, cz - hd / 2), (cx + hw / 2, y0 + 0.3, cz + hd / 2), top, bevel=min(hw, hd) * 0.12)
        if grass is not None and k in (0, 1):
            box(bone, (cx - hw / 2 - 0.25, y0 - 0.5, cz - hd / 2 - 0.25), (cx + hw / 2 + 0.25, y0 + 0.2, cz + hd / 2 + 0.25), grass)
        tops.append((cx, y1, cz, hw, hd))
        cx += lean[0] * h / steps + (rng.random() - 0.5) * w * 0.12
        cz += lean[1] * h / steps + (rng.random() - 0.5) * w * 0.12
    return tops


def conifer(bone, x, y, z, s=1.0, leaf='#2f6a3a', trunk='#5a3e24'):
    box(bone, (x - 0.3 * s, y - 1.2 * s, z - 0.3 * s), (x + 0.3 * s, y, z + 0.3 * s), M('wood', trunk))
    for k, w in enumerate((1.6, 1.15, 0.7)):
        box(bone, (x - w * s / 2 - 0.3 * s, y - (1.2 + 1.1 * (k + 1)) * s, z - w * s / 2 - 0.3 * s),
            (x + w * s / 2 + 0.3 * s, y - (1.2 + 1.1 * k) * s + 0.1, z + w * s / 2 + 0.3 * s), M('leaf', leaf))


def pillar_leg(r, parent, name, anim, top, foot_y, w, skin, plate, claw, knee_dz=-0.6):
    """A heavy pillar leg (Kurma, Eomaia): a thick upper limb, an armoured knee, a wide foot with blunt claws."""
    x, y, z = top
    up = r.bone(name, parent, top, anim=anim)
    knee = (x, y + (foot_y - y) * 0.48, z + knee_dz)
    rbox(up, (x - w * 0.62, y - w * 0.4, z - w * 0.62), (x + w * 0.62, knee[1] + 0.6, z + w * 0.62), skin, bevel=w * 0.2)
    low = r.bone(name + '_low', up, knee, anim='knee')
    rbox(low, (x - w * 0.5, knee[1] - 0.4, knee[2] - w * 0.5), (x + w * 0.5, foot_y - 1.6, knee[2] + w * 0.5), skin, bevel=w * 0.16)
    box(low, (x - w * 0.56, knee[1] - 1.4, knee[2] - w * 0.66), (x + w * 0.56, knee[1] + 2.2, knee[2] - w * 0.36), plate,
        rot=(-0.12, 0, 0), pivot=knee)
    rbox(low, (x - w * 0.66, foot_y - 2.2, knee[2] - w * 0.78), (x + w * 0.66, foot_y, knee[2] + w * 0.6), skin, bevel=w * 0.14)
    for k in range(3):
        cx = x + (k - 1) * w * 0.42
        box(low, (cx - w * 0.17, foot_y - 1.3, knee[2] - w * 0.98), (cx + w * 0.17, foot_y, knee[2] - w * 0.7), claw)
    return up, low


@recipe
def kurma():
    # 嶺脈地龍 クールマ: an earth dragon over ten kilometres high carrying a mountain range: the ranges are its back, the
    # valleys the gaps between its scales, the cliffs and peaks its horns and carapace. Rock and mineral flesh layered
    # with strata, forests and grassland on its slopes, rivers in its gorges, caves and lakes here and there. An old
    # sage watching over the land: heavy-lidded amber eyes, a mossy beard, long whiskers.
    r = rig('kurma')
    strata = M('strata', '#7a7262', bands=['#8a8070', '#7a7262', '#6a6456', '#8e7a62', '#5e5a50', '#7e766a'], band=1.4, ore='#7ff0c8',
               top='#5f9a3e')
    shell = M('strata', '#7a7262', bands=['#8a8070', '#7a7262', '#6a6456', '#8e7a62', '#5e5a50', '#7e766a'], band=1.6, ore='#7ff0c8',
              top='#5f9a3e')
    cliff = M('strata', '#857c6c', bands=['#948a7a', '#857c6c', '#766e60', '#9a8a70'], band=1.2, top='#6aa246')
    snow = M('strata', '#e8eef2', bands=['#eef2f6', '#e2eaf0', '#d6e0e8'], band=0.8, top='#f6f8fa', cracks=False)
    crag = M('strata', '#857c6c', bands=['#948a7a', '#857c6c', '#766e60', '#9a8a70'], band=0.9)
    hide = M('shingle', '#5a6248', belly='#b8a888', scale_size=1.6)
    plate = M('rock', '#8a8274')
    grass = M('leaf', '#5c9a3c')
    water = M('energy', '#6ccaff', glow=True)
    claw = M('rock', '#a39a88')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 14, 0), anim='breath')
    trunk = [(-16, 9.5, 18.8, 18.0), (-12, 8.0, 19.6, 23.0), (-4, 7.4, 20.0, 25.0), (6, 7.4, 20.0, 25.0), (14, 8.0, 19.6, 22.0),
             (19, 9.5, 18.8, 16.0)]
    loft(body, trunk, hide, step=2.0)
    # the shell: a skirt of layered bedrock wider than the body, flat on top where the range stands
    dome = [(-17.5, 5.6, 12.6, 22.0), (-14, 3.4, 13.0, 29.0), (-6, 2.4, 13.4, 32.0), (8, 2.4, 13.4, 32.0), (16, 3.4, 13.0, 28.0),
            (20.5, 5.6, 12.6, 20.0)]
    loft(body, dome, shell, step=2.0)
    # the range
    peaks = [(1.5, -2.0, 10.0, 19.0, 3), (-8.0, -8.5, 7.5, 12.0, 5), (9.0, 6.0, 7.0, 12.5, 7), (-7.0, 9.5, 7.0, 10.0, 11),
             (10.5, -9.0, 5.5, 8.0, 13), (-12.0, 1.0, 5.0, 6.5, 17), (1.0, 14.0, 5.5, 7.0, 19), (12.5, -1.5, 4.0, 5.0, 23)]
    caves = []
    for x, z, w, h, seed in peaks:
        tops = peak(body, x, z, 2.6, w, h, cliff, snow=snow, grass=grass, steps=5 if h > 8 else 4, seed=seed)
        caves.append(tops[1])
    # caves: dark mouths on the faces of two crags
    for (cx, cy, cz, hw, hd), sx in ((caves[1], -1), (caves[2], 1)):
        box(body, (cx + sx * hw / 2 - sx * 0.05 - 0.1, cy + 0.6, cz - 1.0), (cx + sx * hw / 2 + 0.1, cy + 2.6, cz + 1.0),
            M('simple', '#0c0a08'))
    # forests on the shoulders of the range
    for k, (x, z) in enumerate(((-12.5, -9.0), (-13.5, -5.0), (-11.0, 6.5), (-13.0, 10.5), (12.0, 2.0), (13.5, 7.0), (6.0, -11.5),
                                (3.0, -13.0), (-3.0, -13.5), (6.0, 15.0), (-2.5, 16.5), (13.0, 11.5), (-14.0, -1.5), (14.5, -6.0))):
        conifer(body, x, 2.5, z, s=0.9 + 0.25 * ((k * 7) % 3) / 2, leaf=('#2f6a3a', '#3a7a40', '#2a5e36')[k % 3])
    # a river: from a spring between the peaks across the plateau, over the edge and down the shell as a waterfall
    path = [(-2.6, 4.6), (-4.8, 4.0), (-7.0, 3.2), (-9.6, 3.6), (-12.4, 3.0), (-15.2, 3.4)]
    for (x0, z0), (x1, z1) in zip(path, path[1:]):
        seg(body, (x0, 2.35, z0), (x1, 2.35, z1), 1.4, 0.15, water, up=(0, -1, 0))
    t, b, w = section(dome, 3.4)
    box(body, (-w / 2 - 0.2, 2.6, 2.6), (-w / 2 - 0.05, 12.4, 4.2), water)
    box(body, (-w / 2 - 0.6, 12.2, 1.8), (-w / 2 + 0.2, 12.7, 5.0), M('simple', '#e8f6ff'))     # foam
    # a lake in the valley behind the summit
    rbox(body, (1.5, 2.3, 7.8), (6.0, 2.45, 11.6), M('energy', '#4ab0e8', glow=True), bevel=0.8)
    # neck and head: a heavy horned skull, a stony brow over kind eyes, a mossy beard and whiskers
    neck = r.bone('neck', body, (0, 13, -15), anim='sway', ax=1, amp=0.03, speed=0.04)
    loft(neck, [(-23, 9.4, 17.4, 9.0), (-19, 9.2, 18.0, 10.4), (-15, 9.0, 18.6, 12.0)], hide, step=2.0)
    for k in range(3):
        z = -21.5 + k * 2.6
        box(neck, (-3.0, 8.0, z - 1.2), (3.0, 9.8, z + 1.4), plate, rot=(0.35, 0, 0), pivot=(0, 9, z))
    head = r.bone('head', neck, (0, 13, -22), anim='head')
    skull = [(-36.5, 10.4, 14.4, 7.6), (-34, 9.0, 14.8, 9.6), (-29, 8.0, 15.2, 11.2), (-24, 7.8, 15.4, 11.6), (-21, 8.4, 15.4, 11.0)]
    loft(head, skull, hide, faces={'bottom': M('mouth', '#4a2420')}, step=1.8)
    for sx in (-1, 1):
        side = 'left' if sx > 0 else 'right'
        t, b, w = section(skull, -28.5)
        box(head, (sx * 1.2, t - 1.4, -32.0), (sx * (w / 2 + 0.8), t + 0.4, -25.5), cliff, rot=(-0.1, 0, sx * 0.12),
            pivot=(sx * w / 2, t, -28))                                                                         # mossy brow
        cbox(head, (sx * (w / 2 - 0.05), 10.4, -28.4), (0.3, 2.0, 3.6), M('simple', '#1a1610'))
        eye(head, (sx * (w / 2 + 0.08), 10.5, -28.4), 3.2, 1.7, side, M('eye', '#ffb84a', pupil='round', mood='kind', lid='#4a5638',
            glow_amount=0.6))
        horn(head, [(sx * 3.6, 8.2, -24.0), (sx * 6.2, 5.0, -21.0), (sx * 8.4, 2.4, -17.0), (sx * 9.4, 0.6, -12.5)], 3.0, 0.9, crag)
        horn(head, [(sx * 6.0, 5.4, -21.0), (sx * 9.0, 5.0, -19.6), (sx * 10.6, 3.8, -18.4)], 1.6, 0.6, crag)
        horn(head, [(sx * 5.4, 11.6, -23.0), (sx * 8.0, 11.6, -21.0), (sx * 9.6, 10.8, -19.0)], 1.2, 0.4, crag)       # cheek crags
        chain_boxes(head, [(sx * 3.4, 13.0, -36.0), (sx * 6.4, 13.6, -37.0), (sx * 9.0, 15.8, -35.4), (sx * 10.2, 19.2, -33.0)],
                    0.6, 0.3, M('horn', '#d8c89a'))                                                              # whiskers
        box(head, (sx * 2.2 - 0.5, 9.95, -36.4), (sx * 2.2 + 0.5, 10.05, -35.2), M('simple', '#1a1410'))         # nostrils
        teeth(head, sx * 3.6, 14.4, -35.8, -31.0, 3, 0.8, M('tooth', '#e8e0c8'), down=True)
    for k in range(3):
        conifer(head, (k - 1) * 2.4, section(skull, -25 + k)[0] + 0.1, -25.0 + k * 1.5, s=0.55, leaf='#3a7a40')   # trees on the crown
    jaw = r.bone('jaw', head, (0, 15.0, -22.0), rot=(0.1, 0, 0), anim='jaw')
    loft(jaw, [(-36, 14.4, 16.0, 6.6), (-33, 14.8, 17.2, 9.0), (-27, 15.0, 17.8, 10.4), (-22, 15.0, 18.0, 10.6)],
         M('shingle', '#b8a888', belly='#b8a888', scale_size=1.0), faces={'top': M('mouth', '#4a2420')}, step=1.8)
    for k, (x, l) in enumerate(((-2.6, 4.0), (-0.9, 5.6), (0.9, 5.6), (2.6, 4.0))):                              # mossy beard
        box(jaw, (x - 0.8, 17.4, -33.6 + k * 0.3), (x + 0.8, 17.4 + l, -31.8 + k * 0.3), M('fur', '#4f7a34', tip='#8fbf5a'))
    # four pillar legs, the shell's rim resting over them
    for sx in (-1, 1):
        pillar_leg(r, body, 'leg_f' + ('r' if sx < 0 else 'l'), 'leg_r' if sx < 0 else 'leg_l', (sx * 10.0, 15.5, -9.0), 24.0, 6.4,
                   hide, cliff, claw)
        pillar_leg(r, body, 'leg_b' + ('r' if sx < 0 else 'l'), 'leg_l' if sx < 0 else 'leg_r', (sx * 10.0, 15.5, 11.0), 24.0, 6.4,
                   hide, cliff, claw)
    # a short, heavy tail with a ridge of little crags
    tail_ctrl = [(19, 10.5, 18.0, 12.0), (24, 12.0, 18.6, 8.0), (29, 14.0, 19.4, 5.2), (33, 16.0, 20.0, 3.2)]
    tb = tail_loft(r, body, tail_ctrl, [24, 29], hide, amp=0.06, speed=0.04, step=1.8)
    for i, b in enumerate(tb):
        z = 21.5 + i * 4.5
        t, _, w = section(tail_ctrl, z)
        peak(b, 0, z, t + 0.4, w * 0.5, 2.6 - i * 0.6, cliff, steps=3, seed=31 + i)
    return r


def bird_wing(r, parent, side, shoulder, span, feather, covert, spar, rot, n=9, amp=0.3, speed=0.1):
    """A great feathered wing laid flat and raised by its rest rotation: an arm of three joints, then three layers of
    feather plates fanned back from it (coverts, secondaries, long primaries spread like fingers at the tip)."""
    sx = side
    b = r.bone('wing_r' if sx < 0 else 'wing_l', parent, shoulder, rot=(rot[0], rot[1] * sx, rot[2] * -sx), anim='sway', ax=2,
               amp=amp, speed=speed)
    x0, y, z0 = shoulder
    elbow = (x0 + sx * span * 0.38, y - 0.3, z0 - 1.6)
    wrist = (x0 + sx * span * 0.72, y - 0.5, z0 - 0.6)
    tip = (x0 + sx * span, y - 0.6, z0 + 1.0)
    chain_boxes(b, [(x0, y, z0), elbow], 2.2, 1.8, spar)
    chain_boxes(b, [elbow, wrist], 1.8, 1.4, spar)
    chain_boxes(b, [wrist, tip], 1.4, 0.8, spar)
    for k in range(n):
        t = (k + 0.5) / n
        if t < 0.38:
            p = lerp((x0, y, z0), elbow, t / 0.38)
        elif t < 0.72:
            p = lerp(elbow, wrist, (t - 0.38) / 0.34)
        else:
            p = lerp(wrist, tip, (t - 0.72) / 0.28)
        bx, _, bz = p
        L = 6.0 + 11.0 * t ** 1.3 + (0.9 if k % 2 else -0.4)       # a ragged trailing edge
        w = span / n * 0.95
        dy = 0.06 * (k % 3)
        fan = sx * -(0.08 + 0.6 * max(0.0, t - 0.55))                # every feather angled back, primaries spread at the tip
        box(b, (bx - w / 2, y + 0.15 + dy, bz), (bx + w / 2, y + 0.45 + dy, bz + L), feather, rot=(0, fan, 0), pivot=(bx, y, bz))
        box(b, (bx - w * 0.55, y - 0.1, bz - 0.2), (bx + w * 0.55, y + 0.15, bz + L * 0.55), covert, rot=(0, fan * 0.6, 0),
            pivot=(bx, y, bz))
        box(b, (bx - w * 0.6, y - 0.35, bz - 0.4), (bx + w * 0.6, y - 0.1, bz + L * 0.25), covert)
    return b


def insect_leg(r, parent, name, side, hip, mat, claw, phase=0.0):
    """A slender jointed chitin leg folded at the flank like a mantis's (Eomaia's insect legs)."""
    sx = side
    x, y, z = hip
    b = r.bone(name, parent, hip, anim='sway', ax=0, amp=0.12, speed=0.09, phase=phase)
    knee = (x + sx * 3.6, y - 3.0, z - 1.0)
    foot = (x + sx * 5.0, y + 3.6, z - 3.4)
    tip = (x + sx * 4.6, y + 5.6, z - 2.0)
    chain_boxes(b, [hip, knee], 1.0, 0.8, mat)
    chain_boxes(b, [knee, foot], 0.8, 0.55, mat)
    chain_boxes(b, [foot, tip], 0.5, 0.25, claw)
    cbox(b, knee, (1.2, 1.2, 1.2), mat)
    for k in range(3):                                           # little spines along the shin
        p = lerp(knee, foot, 0.25 + k * 0.25)
        seg(b, p, (p[0] - sx * 0.1, p[1] - 0.2, p[2] - 0.9), 0.25, 0.25, claw)
    return b


@recipe
def eomaia():
    # 始祖神獣 エオマイア: origin of all beasts, mother of every animal; their blood, memory, instinct and potential in one
    # body. A lion's mane, a wolf's fangs, a serpent's scales, a bird's wings, a fish's fins, an insect's legs, an
    # elephant's tusks and a stag's antlers, all living together as one creature, wild yet solemnly beautiful. A
    # haughty king and a mother: golden eyes under a heavy brow, head held high.
    r = rig('eomaia')
    fur = M('fur', '#c99a52', tip='#ecc87e')
    mane = M('fur', '#6a3f1e', tip='#b8783a')
    mane2 = M('fur', '#8a5428', tip='#d8a050')
    scales = M('shingle', '#2f6e5a', belly='#a8c89a', scale_size=0.9, glints=['#9ff0c8'], glint_rate=0.03)
    ivory = M('horn', '#f6eacc', tip='#fffaf0')
    antler = M('horn', '#8a6a44', tip='#ffd36a', glow=True)
    chitin = M('carapace', '#2e2a3c', accent='#b48cff')
    claw = M('horn', '#2a2420', tip='#5a4a40')
    feather = M('feather', '#f4e6c8', tip='#e8a83a', glow=True)
    covert = M('feather', '#d8bc88', tip='#f4e6c8')
    finc, edge = '#3e8a9a', '#9ff0ff'
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 13, 2), anim='breath')
    trunk = [(-11, 8.6, 17.6, 9.4), (-7, 8.0, 18.4, 10.6), (-1, 8.6, 18.0, 9.8), (5, 9.2, 17.0, 9.0), (10, 8.8, 16.6, 9.6), (14, 9.6, 15.4, 8.0)]
    loft(body, trunk, fur, step=1.6)
    loft(body, [(-6, 17.4, 18.6, 7.0), (6, 16.4, 17.4, 6.4)], scales, step=2.0)          # a serpent-scaled belly
    # the mane: layered ruffs round the neck and over the shoulders
    for k, (w, y0, y1, z0, z1, m) in enumerate(((13.4, 2.6, 16.0, -15.0, -10.0, mane), (12.6, 3.8, 15.4, -11.0, -6.6, mane2),
                                                (11.4, 5.6, 14.0, -7.4, -3.6, mane), (9.8, 7.0, 12.0, -4.4, -1.0, mane2))):
        rbox(body, (-w / 2, y0, z0), (w / 2, y1, z1), m, bevel=1.8)
    for k in range(5):                                          # locks hanging below the ruff
        x = (k - 2) * 2.4
        box(body, (x - 1.0, 15.0, -14.0 + abs(k - 2) * 0.6), (x + 1.0, 18.2 - abs(k - 2) * 0.6, -11.6), mane, rot=(0.15, 0, 0))
    neck = r.bone('neck', body, (0, 9.5, -11.0), anim='sway', ax=1, amp=0.03, speed=0.05)
    head = r.bone('head', neck, (0, 6.0, -14.0), anim='head')
    skull = [(-25.0, 6.8, 9.0, 3.4), (-22.5, 5.8, 9.2, 4.6), (-19.5, 4.4, 9.4, 5.6), (-16.5, 3.0, 9.6, 7.0), (-13.5, 2.8, 9.8, 7.4)]
    loft(head, skull, fur, faces={'bottom': M('mouth', '#4a1420')})
    box(head, (-1.0, 5.6, -25.4), (1.0, 6.8, -24.2), M('simple', '#1a1214'))                    # nose
    rbox(head, (-3.9, 1.6, -16.4), (3.9, 5.0, -12.0), mane, bevel=1.0)                         # a crest of mane over the brow
    for sx in (-1, 1):
        side = 'left' if sx > 0 else 'right'
        box(head, (sx * 0.9, 2.6, -20.4), (sx * 3.6, 3.7, -16.4), mane, rot=(-0.22, 0, sx * 0.12), pivot=(sx * 2.4, 3.2, -18))
        cbox(head, (sx * 3.45, 5.0, -18.0), (0.3, 1.8, 2.8), M('simple', '#1a1214'))
        eye(head, (sx * 3.55, 5.0, -18.0), 2.8, 1.5, side, M('eye', '#ffc23a', pupil='slit', mood='fierce', lid='#6a3f1e', glow_amount=0.9))
        box(head, (sx * 2.4, 0.4, -15.4), (sx * 3.8, 3.2, -13.6), fur, rot=(0, 0, sx * 0.3), pivot=(sx * 3, 3, -14.5))   # ears
        # stag antlers: a beam with four tines each, gold-lit tips
        horn(head, [(sx * 2.0, 2.4, -15.0), (sx * 3.6, -1.4, -13.6), (sx * 5.4, -5.0, -12.4), (sx * 6.6, -8.4, -10.8), (sx * 6.8, -11.0, -9.0)],
             1.3, 0.5, antler)
        for (a, b) in (((sx * 3.6, -1.4, -13.6), (sx * 4.2, -3.6, -17.0)), ((sx * 5.4, -5.0, -12.4), (sx * 8.4, -6.0, -14.6)),
                       ((sx * 6.0, -6.8, -11.6), (sx * 5.2, -10.0, -12.4)), ((sx * 6.6, -8.4, -10.8), (sx * 9.0, -10.2, -11.6))):
            horn(head, [a, b], 0.7, 0.3, antler)
        # elephant tusks from the upper jaw, curving forward and up
        horn(head, [(sx * 2.2, 8.4, -21.0), (sx * 2.8, 10.6, -24.0), (sx * 3.0, 10.4, -27.6), (sx * 2.6, 8.2, -30.0)], 1.1, 0.45, ivory)
        box(head, (sx * 1.6 - 0.3, 9.0, -24.4), (sx * 1.6 + 0.3, 11.0, -23.8), M('tooth', '#f2ede2'))                   # wolf fangs
        teeth(head, sx * 1.9, 9.0, -23.4, -18.0, 3, 0.55, M('tooth', '#f2ede2'), down=True)
    jaw = r.bone('jaw', head, (0, 9.0, -14.5), rot=(0.18, 0, 0), anim='jaw')
    loft(jaw, [(-24.4, 9.0, 10.2, 3.0), (-20, 9.2, 11.0, 4.6), (-15, 9.4, 11.4, 5.6)], fur, faces={'top': M('mouth', '#4a1420')})
    for sx in (-1, 1):
        box(jaw, (sx * 1.4 - 0.3, 7.4, -23.6), (sx * 1.4 + 0.3, 9.2, -23.0), M('tooth', '#f2ede2'))
    rbox(jaw, (-2.4, 10.4, -18.0), (2.4, 13.0, -14.0), mane2, bevel=0.8)                    # a beard of mane
    # great feathered wings
    for sx in (-1, 1):
        bird_wing(r, body, sx, (sx * 4.4, 9.0, -6.0), 22.0, feather, covert, M('fur', '#e8d8b0', tip='#fff4dc'), rot=(0.35, 0.25, 0.55))
    # legs: lion legs with serpent-scaled forearms and fish fins at the elbows; a pair of insect legs folded at the flanks
    for sx in (-1, 1):
        up, low = fore_leg(r, body, 'leg_f' + ('r' if sx < 0 else 'l'), 'leg_r' if sx < 0 else 'leg_l', sx, (sx * 4.0, 13.6, -7.0),
                           (sx * 4.5, 18.6, -7.8), (sx * 4.4, 22.4, -7.0), 2.6, fur, scales, claw)
        fin(up, [(-8.8, 17.2), (-5.6, 16.2), (-3.6, 20.4), (-6.6, 19.6)], 'zy', sx * 5.9, finc, accent=edge)
        hind_leg(r, body, 'leg_b' + ('r' if sx < 0 else 'l'), 'leg_l' if sx < 0 else 'leg_r', sx, (sx * 4.0, 13.0, 10.0),
                 (sx * 4.6, 17.4, 7.2), (sx * 4.5, 20.8, 11.6), (sx * 4.5, 22.6, 10.0), 2.9, fur, scales, claw)
        insect_leg(r, body, 'bug_' + ('r' if sx < 0 else 'l'), sx, (sx * 4.4, 13.4, 1.0), chitin, claw, phase=sx)
    # a serpent's tail ending in a fish's fan fin
    tail_ctrl = [(13.0, 10.2, 13.4, 3.0), (18, 9.2, 12.0, 2.6), (23, 8.0, 10.6, 2.2), (28, 6.6, 9.0, 1.8), (32, 5.6, 7.8, 1.4)]
    tb = tail_loft(r, body, tail_ctrl, [18, 23, 28], scales, amp=0.16, speed=0.07)
    fin(tb[-1], [(31.0, 6.6), (34.6, 2.0), (36.4, 3.6), (35.2, 6.8), (36.4, 10.0), (34.6, 11.4), (31.0, 7.0)], 'zy', 0.0, finc, accent=edge,
        glow=True, veins=[(31.5, 6.7, 35.4, 2.6), (31.5, 6.7, 35.8, 6.8), (31.5, 6.7, 35.4, 10.8)])
    return fit_height(r, ('wing',))


def sphere(bone, c, rad, mat, n=None, octa=False, squash=(1.0, 1.0, 1.0)):
    """A ball of horizontal slices (a stepped circle from the side). octa: each slice an octagon of two crossing
    boxes (round from above too, for opaque balls); otherwise one box per slice, so a see-through ball has no faces
    inside it. Slice faces covered by a larger neighbour are left out."""
    cx, cy, cz = c
    n = n or max(5, int(round(rad * 2 / 1.1)))
    t = 2 * rad * squash[1] / n
    for i in range(n):
        y0 = cy - rad * squash[1] + i * t
        ym = y0 + t / 2
        e = (ym - cy) / (rad * squash[1])
        half = rad * math.sqrt(max(0.04, 1 - e * e))
        hx, hz = half * squash[0], half * squash[2]
        skip = ('bottom',) if ym < cy - t * 0.5 else (('top',) if ym > cy + t * 0.5 else ())
        if octa:
            b = min(hx, hz) * 0.29
            box(bone, (cx - hx, y0, cz - hz + b), (cx + hx, y0 + t, cz + hz - b), mat, skip=skip)
            box(bone, (cx - hx + b, y0, cz - hz), (cx + hx - b, y0 + t, cz + hz), mat, skip=skip)
        else:
            box(bone, (cx - hx, y0, cz - hz), (cx + hx, y0 + t, cz + hz), mat, skip=skip)


def shell_sphere(bone, c, rad, mat, n=11):
    """A hollow see-through ball: the side walls of square horizontal slices and the step rings between them, as
    plates, so nothing inside it but what is meant to be seen (Mels's nucleus)."""
    cx, cy, cz = c
    t = 2 * rad / n
    halves = []
    for i in range(n):
        ym = cy - rad + (i + 0.5) * t
        e = (ym - cy) / rad
        halves.append(rad * math.sqrt(max(0.05, 1 - e * e)))
    for i, h in enumerate(halves):
        y0 = cy - rad + i * t
        box(bone, (cx - h, y0, cz - h), (cx + h, y0 + t, cz + h), mat, skip=('top', 'bottom'))
    def ring(y, h_in, h_out):
        if h_out - h_in < 0.02:
            return
        box(bone, (cx - h_out, y, cz - h_out), (cx + h_out, y, cz - h_in), mat)
        box(bone, (cx - h_out, y, cz + h_in), (cx + h_out, y, cz + h_out), mat)
        box(bone, (cx - h_out, y, cz - h_in), (cx - h_in, y, cz + h_in), mat)
        box(bone, (cx + h_in, y, cz - h_in), (cx + h_out, y, cz + h_in), mat)
    box(bone, (cx - halves[0], cy - rad, cz - halves[0]), (cx + halves[0], cy - rad, cz + halves[0]), mat)
    box(bone, (cx - halves[-1], cy + rad, cz - halves[-1]), (cx + halves[-1], cy + rad, cz + halves[-1]), mat)
    for i in range(n - 1):
        y = cy - rad + (i + 1) * t
        a, b = halves[i], halves[i + 1]
        ring(y, min(a, b), max(a, b))


@recipe
def mels():
    # 至高武王 メルス: the world's greatest martial artist is a clear sphere about fifty centimetres across: no eyes,
    # no mouth, no limbs, nothing to read an expression from; inside, the intelligence of countless arts and an
    # enormous store of mana. An artificial all-purpose weapon made by an ageless sage, a slime whose gel is
    # controlled to the last drop: harder than steel and thinner than water at once. Here: the clear ball, its bright
    # nucleus and the currents of its control circling inside, and a few of the weapons it becomes held in gel round it.
    r = rig('mels')
    r.translucent = True
    c = (0.0, 19.8, 0.0)
    gel = M('gel', '#9fe6ff', c=c, r=4.2, alpha=95)
    root = r.bone('root', None, (0, 24, 0), anim='root')
    core = r.bone('core', root, c, anim='pulse', amp=0.06, speed=0.07)
    cbox(core, c, (2.0, 2.0, 2.0), M('gem', '#e8fbff', glow=True), rot=(0.615, 0.785, 0))
    cbox(core, c, (1.0, 1.0, 1.0), M('energy', '#ffffff', glow=True), rot=(0.615, 0.785, 0))
    flow = r.bone('flow', root, c, anim='spin', speed=0.06, cast=0.0)
    hoop(flow, c, 2.9, 0.22, M('energy', '#7fe8ff', glow=True, glow_amount=0.7), axis='y', n=16, depth=0.2)
    flow2 = r.bone('flow2', root, c, rot=(1.1, 0, 0.5), anim='spin', speed=-0.05, cast=0.0)
    hoop(flow2, c, 2.5, 0.2, M('energy', '#c8a8ff', glow=True, glow_amount=0.7), axis='y', n=14, depth=0.2)
    body = r.bone('body', root, (0, 24, 0), anim='liquid', amp=0.07)
    shell_sphere(body, c, 4.2, gel, n=11)
    box(body, (-3.4, 23.85, -3.4), (3.4, 24.0, 3.4), M('slime', '#9fe6ff', alpha=70))        # where it rests on the floor
    # weapons it becomes, held in clear gel and circling slowly
    ring = r.bone('shards', root, (0, 18.5, 0), anim='spin', speed=0.03, cast=0.0)
    shard = M('slime', '#bff4ff', alpha=150)
    edge = M('energy', '#bff4ff', glow=True, glow_amount=0.6)
    for k in range(5):
        a = k * 2 * math.pi / 5
        x, z = math.cos(a) * 7.0, math.sin(a) * 7.0
        y = 18.0 + (k % 2) * 1.4
        if k == 0:      # blade
            cbox(ring, (x, y, z), (0.35, 4.4, 1.0), shard, rot=(0, a, 0.25)); cbox(ring, (x, y + 2.3, z), (0.4, 0.4, 2.0), edge, rot=(0, a, 0.25))
        elif k == 1:    # spear head
            cbox(ring, (x, y, z), (0.9, 2.6, 0.9), shard, rot=(0.785, a, 0)); cbox(ring, (x, y + 2.2, z), (0.3, 2.2, 0.3), edge, rot=(0, a, 0))
        elif k == 2:    # hammer
            cbox(ring, (x, y - 1.0, z), (2.2, 1.4, 1.4), shard, rot=(0, a, 0)); cbox(ring, (x, y + 0.8, z), (0.4, 2.6, 0.4), edge, rot=(0, a, 0))
        elif k == 3:    # shield
            cbox(ring, (x, y, z), (2.8, 3.2, 0.35), shard, rot=(0, a + math.pi / 2, 0)); cbox(ring, (x, y, z), (0.8, 0.8, 0.5), edge, rot=(0, a + math.pi / 2, 0))
        else:           # bow
            for j in range(5):
                t = (j - 2) / 2
                cbox(ring, (x + math.cos(a) * (0.9 - 0.9 * t * t), y + t * 2.0, z + math.sin(a) * (0.9 - 0.9 * t * t)), (0.4, 1.1, 0.4),
                     shard, rot=(0, a, -t * 0.5))
            cbox(ring, (x, y, z), (0.12, 4.2, 0.12), edge, rot=(0, a, 0))
    return fit_height(r, ('shards',))


def machine_ball(bone, c, rad, hull, band, seam=None, n=None):
    """An opaque machine sphere: octagonal slices of hull, a raised band round the equator, glowing seams."""
    sphere(bone, c, rad, hull, n=n, octa=True)
    cx, cy, cz = c
    hoop(bone, c, rad * 1.02, max(0.5, rad * 0.16), band, axis='y', n=max(12, int(rad * 4)), depth=max(0.4, rad * 0.14))
    if seam is not None:
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            box(bone, (cx + math.cos(a) * rad * 0.74 - 0.12, cy - rad * 0.7, cz + math.sin(a) * rad * 0.74 - 0.12),
                (cx + math.cos(a) * rad * 0.74 + 0.12, cy + rad * 0.7, cz + math.sin(a) * rad * 0.74 + 0.12), seam)


@recipe
def hephaistos():
    # 典域工廠 ヘファイストス: a machine god born of transcendent technology that treats every substance and structure,
    # life, godhood and the universe itself as something to design and build. A spherical machine with a cubic core
    # neither crystal nor any known metal; round it float machine spheres of every size, each an observation device,
    # a machine tool, a furnace, a hangar or a weapon, parting, joining and changing shape, so the whole is never the
    # same twice. No face, no hands or feet: the machines that circle it are its eyes and arms.
    r = rig('hephaistos')
    hull = M('metal', '#4a5462')
    dark = M('metal', '#262c34')
    brass = M('metal', '#b48a3e')
    seam = M('energy', '#ff9a3a', glow=True, glow_amount=0.8)
    cyan = M('energy', '#8ff4ff', glow=True)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.5, speed=0.05)
    c = (0.0, 11.0, 0.0)
    # the core: a cube of crystal-metal, turning slowly, seen through the gap between the two hemispheres
    core = r.bone('core', root, c, anim='spin', speed=0.03, cast=0.0)
    cbox(core, c, (5.6, 5.6, 5.6), M('gem', '#bff6ff', glow=True), rot=(0.615, 0.785, 0))
    cbox(core, c, (6.2, 0.4, 6.2), cyan, rot=(0.615, 0.785, 0))
    cbox(core, c, (0.4, 6.2, 6.2), cyan, rot=(0.615, 0.785, 0))
    # the shell: an upper and a lower hemisphere of plated metal that breathe apart round the core
    top = r.bone('shell_top', root, c, anim='sway', ax=1, amp=0.0, speed=0.05)
    bot = r.bone('shell_bottom', root, c, anim='sway', ax=1, amp=0.0, speed=0.05)
    R = 8.0
    n = 12
    t = 2 * R / n
    for i in range(n):
        y0 = c[1] - R + i * t
        ym = y0 + t / 2
        if abs(ym - c[1]) < t * 1.1:
            continue                                    # the open equator: the core shows through
        e = (ym - c[1]) / R
        h = R * math.sqrt(max(0.05, 1 - e * e))
        b = h * 0.29
        bone = top if ym < c[1] else bot
        mat = hull if i % 3 else dark
        box(bone, (-h, y0, -h + b), (h, y0 + t, h - b), mat)
        box(bone, (-h + b, y0, -h), (h - b, y0 + t, h), mat)
    for bone, y in ((top, c[1] - t * 1.1), (bot, c[1] + t * 1.1)):
        hoop(bone, (0, y, 0), R * 0.98, 0.9, brass, axis='y', n=28, depth=0.7)     # brass rims at the gap
        for k in range(8):
            a = k * math.pi / 4
            cbox(bone, (math.cos(a) * R * 0.99, y, math.sin(a) * R * 0.99), (0.6, 0.5, 0.6), seam)
    # panel seams and vents
    for k in range(6):
        a = k * math.pi / 3
        for bone, y0, y1 in ((top, c[1] - R * 0.86, c[1] - t * 1.4), (bot, c[1] + t * 1.4, c[1] + R * 0.86)):
            box(bone, (math.cos(a) * R * 0.86 - 0.1, y0, math.sin(a) * R * 0.86 - 0.1),
                (math.cos(a) * R * 0.86 + 0.1, y1, math.sin(a) * R * 0.86 + 0.1), seam, rot=(0, -a, 0),
                pivot=(math.cos(a) * R * 0.86, (y0 + y1) / 2, math.sin(a) * R * 0.86))
    rbox(top, (-2.2, c[1] - R - 1.2, -2.2), (2.2, c[1] - R + 0.6, 2.2), brass, bevel=0.5)          # crown hatch
    cbox(top, (0, c[1] - R - 1.3, 0), (1.2, 0.3, 1.2), cyan)
    rbox(bot, (-2.6, c[1] + R - 0.6, -2.6), (2.6, c[1] + R + 1.0, 2.6), dark, bevel=0.5)          # forge outlet below
    cbox(bot, (0, c[1] + R + 1.05, 0), (3.4, 0.2, 3.4), seam)
    # orbits: rings of travel and the machines that ride them
    orbit_a = r.bone('orbit_a', root, c, anim='spin', speed=0.025, cast=0.0)
    orbit_b = r.bone('orbit_b', root, c, rot=(0.5, 0, 0.35), anim='spin', speed=-0.018, cast=0.0)
    orbit_c = r.bone('orbit_c', root, c, rot=(-0.4, 0, -0.5), anim='spin', speed=0.032, cast=0.0)
    hoop(orbit_a, c, 15.0, 0.25, M('energy', '#ffb060', glow=True, glow_amount=0.5), axis='y', n=40, depth=0.15)
    def at(a, rad):
        return (math.cos(a) * rad, c[1], math.sin(a) * rad)
    # 1 observation sphere: a great lens, its rings and a glowing iris (the god's eye is a machine)
    x, y, z = at(0.0, 15.0)
    machine_ball(orbit_a, (x, y, z), 3.0, hull, brass, n=6)
    for k, (rr, m) in enumerate(((2.4, dark), (1.8, brass), (1.2, M('gem', '#ff9a3a', glow=True)), (0.5, M('simple', '#1a0c04')))):
        cbox(orbit_a, (x - 3.0 - 0.15 * k, y, z), (0.3, rr * 2, rr * 2), m)
    # 2 machine-tool sphere with a jointed manipulator arm and a three-fingered claw
    x, y, z = at(math.pi * 2 / 3, 15.0)
    machine_ball(orbit_a, (x, y, z), 2.6, hull, brass, n=6)
    p0 = (x, y + 2.0, z)
    p1 = (x * 0.8, y + 6.0, z * 0.8)
    p2 = (x * 0.62, y + 4.0, z * 0.62)
    chain_boxes(orbit_a, [p0, p1], 1.2, 1.0, dark)
    chain_boxes(orbit_a, [p1, p2], 1.0, 0.8, dark)
    for j in (p0, p1):
        cbox(orbit_a, j, (1.6, 1.6, 1.6), brass)
    for k in range(3):
        a = k * 2 * math.pi / 3
        seg(orbit_a, p2, (p2[0] + math.cos(a) * 1.0, p2[1] + 1.8, p2[2] + math.sin(a) * 1.0), 0.45, 0.45, brass)
    # 3 furnace sphere: a glowing grate and a short stack
    x, y, z = at(math.pi * 4 / 3, 15.0)
    machine_ball(orbit_a, (x, y, z), 3.2, dark, brass, seam=seam, n=6)
    for k in range(4):
        box(orbit_a, (x - 3.3, y - 1.5 + k * 0.9, z - 1.6), (x - 3.0, y - 1.1 + k * 0.9, z + 1.6), seam)
    seg(orbit_a, (x, y - 3.0, z), (x, y - 6.0, z), 1.2, 1.2, dark)
    cbox(orbit_a, (x, y - 6.2, z), (1.4, 0.3, 1.4), seam)
    # 4 hangar sphere on the tilted orbit: a lit hatch, small drones beside it
    x, y, z = at(0.8, 12.0)
    machine_ball(orbit_b, (x, y, z), 3.4, hull, brass, n=6)
    box(orbit_b, (x - 2.0, y - 2.0, z - 3.5), (x + 2.0, y + 2.0, z - 3.3), dark)
    for k in range(3):
        box(orbit_b, (x - 1.6, y - 1.4 + k * 1.3, z - 3.55), (x + 1.6, y - 1.2 + k * 1.3, z - 3.5), cyan)
    for k in range(3):
        sphere(orbit_b, (x + 4.0 + k * 1.8, y - 2.0 + k * 1.4, z - 2.0), 0.7, hull, n=3, octa=True)
        cbox(orbit_b, (x + 4.0 + k * 1.8, y - 2.0 + k * 1.4, z - 2.75), (0.5, 0.5, 0.2), cyan)
    # 5 weapon sphere on the other tilted orbit: twin barrels and a charging muzzle
    x, y, z = at(3.6, 13.0)
    machine_ball(orbit_c, (x, y, z), 3.0, dark, brass, n=6)
    for dy in (-0.9, 0.9):
        seg(orbit_c, (x, y + dy, z - 2.0), (x, y + dy, z - 8.0), 1.0, 1.0, hull)
        cbox(orbit_c, (x, y + dy, z - 8.1), (1.3, 1.3, 0.4), brass)
        cbox(orbit_c, (x, y + dy, z - 8.35), (0.6, 0.6, 0.1), cyan)
    # small satellites
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.3
        sphere(orbit_c, (math.cos(a) * 18.0, c[1] + math.sin(a * 2) * 2.0, math.sin(a) * 18.0), 1.0, hull, n=4, octa=True)
    return fit_height(r, ('orbit',))


@recipe
def nun():
    # 天変万化 ヌン: a shapeshifter travelling to know everything in the world, taking any form and the nature of
    # whatever it becomes. Its usual shape is a black, writhing, viscous mass of magic matter with no clear skeleton,
    # no face and no limbs, between liquid and shadow; on need it becomes an emperor or a vagrant, an old man or a
    # child, a beast or a bird, a sword, a staff, an old book, a shadow in the wind. Here: the black mass with an oily
    # sheen, drips and a puddle, feelers that sway, and half-made shapes of things it has been rising out of it (a
    # hand, a bird's wing, a crown, a book). One feeler, arm_r, holds its jester's staff.
    r = rig('nun')
    ink = M('oilslick', '#100c16', hues=['#7a3ad0', '#2ab0c0'])
    ink2 = M('oilslick', '#1a1424', hues=['#c03a8a', '#3ad08a'])
    gloss = M('energy', '#c8b8ff', glow=True, glow_amount=0.35)
    gold = M('metal', '#8a7034')
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=0.0, speed=0.06)
    mass = r.bone('mass', root, (0, 24, 0), anim='liquid', amp=0.08)
    # the mass: overlapping lumps, heavier at the bottom, slumping forward
    for (x, y, z, rad, m) in ((0, 17.0, 0, 6.6, ink), (-3.4, 19.5, 1.6, 4.6, ink2), (3.6, 19.8, -1.2, 4.4, ink), (0.8, 12.4, -0.6, 4.4, ink2),
                              (-1.6, 9.4, 0.4, 3.0, ink), (2.4, 21.6, 3.2, 3.0, ink2), (-4.4, 22.0, -2.6, 2.4, ink)):
        sphere(mass, (x, y, z), rad, m, octa=True)
    # the puddle it stands in, and drops running down
    for (x, z, w, d) in ((0, 0, 17.0, 14.0), (-5.0, 4.0, 7.0, 6.0), (6.0, -3.0, 5.0, 6.0)):
        rbox(mass, (x - w / 2, 23.6, z - d / 2), (x + w / 2, 24.0, z + d / 2), ink, bevel=1.2)
    for k, (x, z, y0, l) in enumerate(((-6.0, -1.0, 17.0, 3.4), (5.8, 1.6, 18.0, 2.6), (2.0, -6.0, 15.0, 4.0), (-3.0, 5.6, 19.0, 2.2))):
        seg(mass, (x, y0, z), (x, y0 + l, z), 0.9, 0.9, ink2)
        cbox(mass, (x, y0 + l + 0.5, z), (1.3, 1.3, 1.3), ink2)
    # sheen: a few glints of light on the black
    for (x, y, z) in ((-2.0, 12.0, -4.6), (3.0, 15.0, -6.2), (-4.6, 17.5, -4.0), (1.0, 9.0, -2.6)):
        cbox(mass, (x, y, z), (0.6, 0.3, 0.2), gloss)
    # half-formed things surfacing: a hand reaching out of the left side, a crown sunk in the top, a book's corner
    hand = r.bone('hand', mass, (6.4, 15.0, -2.0), anim='sway', ax=2, amp=0.1, speed=0.05)
    seg(hand, (6.0, 15.0, -2.0), (9.0, 13.0, -3.0), 1.6, 1.2, ink)
    for k in range(4):
        seg(hand, (9.0, 13.0 - k * 0.1, -3.6 + k * 0.5), (10.6, 11.0 - k * 0.5, -4.2 + k * 0.6), 0.45, 0.45, ink2)
    seg(hand, (8.6, 13.4, -3.6), (9.6, 12.0, -5.2), 0.45, 0.45, ink2)
    hoop(mass, (0.4, 9.2, 0.0), 2.2, 0.6, gold, axis='y', n=12, depth=0.6)
    for k in range(5):
        a = k * 2 * math.pi / 5
        seg(mass, (0.4 + math.cos(a) * 2.2, 8.8, math.sin(a) * 2.2), (0.4 + math.cos(a) * 2.3, 7.2, math.sin(a) * 2.3), 0.5, 0.5, gold)
    box(mass, (-6.8, 19.0, -4.8), (-3.6, 19.9, -1.6), M('cloth', '#6a3a2a'), rot=(0.3, 0.4, 0.5), pivot=(-5.2, 19.4, -3.2))
    box(mass, (-6.6, 18.9, -4.6), (-3.8, 19.0, -1.8), M('simple', '#e8dcc0'), rot=(0.3, 0.4, 0.5), pivot=(-5.2, 19.4, -3.2))
    # a bird's wing rising from the back, its feathers dissolving into the mass
    wing = r.bone('wing_r', mass, (-2.0, 12.0, 4.0), rot=(0.4, 0.5, 0.3), anim='sway', ax=2, amp=0.15, speed=0.06)
    for k in range(6):
        t = k / 5
        seg(wing, (-2.0 - t * 1.0, 12.0 - t * 3.0, 4.0 + t * 1.2), (-2.0 - t * 1.0 - 6.0 + abs(t - 0.5) * 3.0, 12.0 - t * 3.0 - 6.5, 4.0 + t * 1.2 + 2.0),
            1.1, 0.3, ink2 if k % 2 else ink)
    # feelers: three swaying, and arm_r, which hangs at the right side with the staff in its tip
    for i, (x, y, z, ang) in enumerate(((-5.4, 13.0, 3.0, -0.9), (4.6, 11.0, 4.4, 0.7), (0.0, 10.0, 6.0, 0.0))):
        p = np.array([x, y, z])
        bone = mass
        for j in range(4):
            bone = r.bone(f'feeler{i}_{j}', bone, tuple(p), anim='tail', i=j, amp=0.22, speed=0.07, ax=1)
            q = p + np.array([math.sin(ang) * 2.2, -1.6 + j * 0.7, 2.0])
            seg(bone, p, q, 1.3 - j * 0.25, 1.3 - j * 0.25, ink if j % 2 else ink2)
            p = q
    arm = r.bone('arm_r', mass, (-6.6, 14.0, -2.0), anim='arm_r', reach=7.5)
    chain_boxes(arm, [(-6.6, 14.0, -2.0), (-7.4, 17.5, -2.4), (-7.0, 21.5, -2.0)], 2.0, 1.2, ink2)
    cbox(arm, (-7.0, 21.5, -2.0), (1.8, 1.4, 1.8), ink)
    return r


def eyeball(r, parent, name, c, rad, iris, phase=0.0, pupil='round', look=(0.0, 0.0, -1.0)):
    """A loose eyeball on its own bone: a white ball with veins, an iris disc and pupil turned toward `look`."""
    b = r.bone(name, parent, c, anim='chaos', phase=phase)
    sphere(b, c, rad, M('carapace', '#efe6ee'), n=max(3, int(rad * 1.6)), octa=True)
    lx, ly, lz = look
    n = math.sqrt(lx * lx + ly * ly + lz * lz) or 1.0
    lx, ly, lz = lx / n, ly / n, lz / n
    side = 'front' if abs(lz) >= max(abs(lx), abs(ly)) else ('left' if lx > 0 else 'right')
    p = (c[0] + lx * rad * 0.98, c[1] + ly * rad * 0.98, c[2] + lz * rad * 0.98)
    eye(b, p, rad * 1.25, rad * 1.25, side, M('eye', iris, pupil=pupil, mood='calm', lid='#d8c4d8', glow_amount=0.8), depth=0.3)
    return b


@recipe
def chaos():
    # 万象混沌 カオス: not a life, a monster, a god or a spirit: the chaos that spills when the world loses its
    # coherence, given form. No stable body; seen again it has changed: a rainbow foetus filling the sky, a purple-
    # black mass like a continent turned inside out, a cloud full of countless eyeballs, a beast wearing the sea, a
    # dragon of city ruins, countless human arms from a flower field. Its stuff is flesh, buildings, land and space
    # itself. At its heart sometimes a rainbow core appears, clear as a gem, cloudy as an oil film, holding a nebula's
    # colours. Round it the ground turns to sea, cities hang upside down in the sky, fish pour from their windows.
    r = rig('chaos')
    flesh = M('oilslick', '#2a1438', hues=['#ff6ad5', '#6af0ff'])
    flesh2 = M('oilslick', '#3a1e52', hues=['#ffe46a', '#7dff8a'])
    cloud = M('void', '#5a3a7a')
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=2.0, speed=0.05)
    body = r.bone('body', root, (0, 11, 0), anim='liquid', amp=0.04)
    # the mass: a ring of lumps round an open heart, so the core shows through
    for k in range(10):
        a = k * 2 * math.pi / 10
        x, y = math.cos(a) * 9.0, 10.0 + math.sin(a) * 8.0
        z = 1.0 + math.sin(a * 3.0) * 1.5
        sphere(body, (x, y, z), 4.2 + (k % 3) * 0.7, flesh if k % 2 else flesh2, octa=True)
    for (x, y, z, rad) in ((0, 10.0, 6.0, 6.0), (-7.0, 3.0, 4.0, 3.4), (7.5, 17.0, 3.0, 3.6), (-8.0, 18.0, 4.0, 3.0)):
        sphere(body, (x, y, z), rad, cloud, octa=True)
    # the rainbow core in the heart
    core = r.bone('core', root, (0, 10.0, -1.0), anim='pulse', amp=0.12, speed=0.09)
    cbox(core, (0, 10.0, -1.0), (5.0, 5.0, 5.0), M('rainbow', '#ffffff'), rot=(0.615, 0.785, 0))
    cbox(core, (0, 10.0, -1.0), (6.4, 0.6, 6.4), M('energy', '#ffe8ff', glow=True), rot=(0.615, 0.785, 0))
    cbox(core, (0, 10.0, -1.0), (3.0, 3.0, 3.0), M('energy', '#ffffff', glow=True), rot=(0.2, 0.3, 0.5))
    # countless eyeballs in the cloud, looking every way
    irises = ['#7ff6ff', '#ffe46a', '#7dff8a', '#ff8a5a', '#b48cff', '#ff6ad5', '#6a8aff']
    spots = [(-9.0, 5.0, -3.6, 2.4, (-0.3, 0, -1)), (8.4, 6.0, -3.8, 2.8, (0.3, 0.1, -1)), (-5.0, 16.4, -3.6, 2.0, (0, 0.4, -1)),
             (5.0, 16.0, -4.0, 1.7, (0.2, 0, -1)), (-13.0, 11.0, 0.0, 1.8, (-1, 0, -0.2)), (13.0, 10.0, 0.0, 2.2, (1, 0, -0.2)),
             (0.0, 1.0, -3.4, 2.4, (0, -0.3, -1)), (0.0, 19.6, -3.0, 1.6, (0, 0.6, -1)), (-4.0, 9.6, -4.6, 1.2, (0, 0, -1)),
             (10.0, 1.6, 2.6, 1.5, (1, 0, 0.2)), (-10.4, 2.0, 2.0, 1.4, (-1, 0, 0.1)), (8.0, 19.0, -1.0, 1.3, (0.4, 0.5, -1)),
             (4.4, 9.0, -5.0, 1.0, (0, 0, -1)), (-11.0, 17.0, 1.0, 1.2, (-1, 0.3, 0))]
    for k, (x, y, z, rad, look) in enumerate(spots):
        eyeball(r, body, f'eye{k + 1}', (x, y, z), rad, irises[k % len(irises)], phase=k * 0.9, pupil='slit' if k % 3 == 0 else 'round',
                look=look)
    # arms reaching out of a little flower field on the right flank
    for k in range(4):
        x0, y0, z0 = 10.4 + k * 0.4, 13.0 + k * 1.2, -2.0 + k * 1.6
        arm = r.bone(f'arm{k}', body, (x0, y0, z0), anim='sway', ax=2, amp=0.18, speed=0.06, phase=k)
        chain_boxes(arm, [(x0, y0, z0), (x0 + 3.4, y0 - 1.6 - k * 0.4, z0 - 0.6), (x0 + 6.0, y0 - 3.6 + k * 0.3, z0 - 1.2)], 1.3, 1.0,
                    M('skin', '#d8b8a8'))
        for f in range(4):
            seg(arm, (x0 + 6.0, y0 - 3.6 + k * 0.3, z0 - 1.2), (x0 + 7.4, y0 - 4.0 + f * 0.5, z0 - 1.6 + f * 0.4), 0.3, 0.3, M('skin', '#d8b8a8'))
    for k in range(10):
        x, z = 7.0 + (k % 4) * 1.4, -3.0 + (k // 4) * 2.2
        cbox(body, (x + 2.0, 8.4 - (k % 3) * 0.3, z), (0.9, 0.9, 0.9), M('simple', ['#ff7ab0', '#ffe46a', '#ffffff', '#9a7aff'][k % 4]))
    # an upside-down town hanging in the sky round it, fish falling from its windows
    orbit = r.bone('orbit', root, (0, 10, 0), anim='spin', speed=0.012, cast=0.0)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.4
        x, z = math.cos(a) * 17.0, math.sin(a) * 17.0
        h = 3.0 + (k % 3) * 1.2
        box(orbit, (x - 1.6, -4.0, z - 1.6), (x + 1.6, -4.0 + h, z + 1.6), M('carapace', '#d8cfc0'))           # walls, roof down
        for step in range(3):
            w = 2.0 - step * 0.6
            box(orbit, (x - w, -4.0 + h + step * 0.6, z - w), (x + w, -4.0 + h + (step + 1) * 0.6, z + w), M('carapace', '#9a3a2a'))
        for wy in range(int(h // 1.4)):
            box(orbit, (x - 0.5, -3.4 + wy * 1.4, z - 1.65), (x + 0.5, -2.6 + wy * 1.4, z - 1.6), M('energy', '#ffd36a', glow=True))
        cbox(orbit, (x, -5.0, z), (4.6, 1.6, 4.6), M('strata', '#7a6a5a', bands=['#7a6a5a', '#5a4a3a'], band=0.5))   # torn ground
        box(orbit, (x - 2.3, -4.2, z - 2.3), (x + 2.3, -4.2, z + 2.3), M('leaf', '#5f9a3e'))                            # its grass, facing down
        for f in range(2):
            fy = -4.0 + h + 2.0 + f * 3.0
            box(orbit, (x - 0.5 + f, fy - 0.6, z - 2.6), (x + 0.5 + f, fy + 0.6, z - 0.4), M('shingle', '#ff9a4a', belly='#ffe0b0', scale_size=0.5))
            box(orbit, (x + f - 0.1, fy - 1.0, z - 0.4), (x + f + 0.1, fy + 1.0, z + 0.8), M('energy', '#ffb36a', glow=True, glow_amount=0.3))
    return fit_height(r, ('orbit',))


def world_orb(bone, c, rad, kind):
    """One of the nine worlds hanging in Yggdrasil's boughs: a small round world with its own look."""
    looks = {'sea': ('#2f7ad0', '#e8f4ff'), 'fire': ('#e8541a', '#ffd36a'), 'ice': ('#bfe8ff', '#ffffff'), 'forest': ('#3f9a44', '#ffd6f0'),
             'dark': ('#2a2238', '#b48cff'), 'light': ('#fff2b0', '#ffffff'), 'stone': ('#8a8274', '#d8c8a0'),
             'sky': ('#8fd8ff', '#ffffff'), 'death': ('#4a5a5a', '#9ff0c8')}
    base, acc = looks[kind]
    sphere(bone, c, rad, M('gem', base, glow=kind in ('fire', 'light', 'dark')), n=4, octa=True)
    cx, cy, cz = c
    hoop(bone, c, rad * 1.25, 0.18, M('energy', acc, glow=True, glow_amount=0.6), axis='y', n=12, depth=0.12)
    seg(bone, (cx, cy - rad, cz), (cx, cy - rad - 5.0, cz), 0.3, 0.3, M('wood', '#5a4030'))          # its stem


@recipe
def yggdrasil():
    # 玖天神樹 イグドラシル: a tree so vast it pierces heaven and holds nine worlds within it, circulating and
    # amplifying the world's natural mana. The trunk rises through the sea of clouds, the boughs spread to wrap the
    # nine worlds, the roots reach the deep strata and bind themselves to the ley lines and spirit veins; every leaf
    # and flower holds immense mana. No face: here the trunk with mana running up it in glowing veins, a ring of
    # cloud round its middle, a crown of leaf with glowing blossoms, the nine worlds hanging in it, roots spread over
    # the ground with ley lines burning in them.
    r = rig('yggdrasil')
    bark = M('wood', '#5a4030')
    bark2 = M('wood', '#6e5038')
    vein = M('energy', '#9fffd8', glow=True, glow_amount=0.8)
    leaf = M('leaf', '#4f9a44', flowers='#ffd6f0')
    leaf2 = M('leaf', '#3f8a3e', flowers='#fff2b0')
    leaf3 = M('leaf', '#5aa84e')
    cloud = M('carapace', '#f4f8fc')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    trunk = r.bone('body', root, (0, 10, 0), anim='sway', ax=2, amp=0.01, speed=0.02)
    # trunk: slices of bark twisting as they rise, flaring at the foot
    n = 22
    for i in range(n):
        y1 = 24.0 - i * 2.8
        y0 = y1 - 2.8
        t = i / (n - 1)
        w = 13.0 - 7.0 * t ** 0.7 + (4.0 if i == 0 else (2.0 if i == 1 else 0.0))
        a = t * 1.2
        cx, cz = math.sin(t * 3.0) * 1.2, math.cos(t * 2.4) * 0.8
        box(trunk, (cx - w / 2, y0, cz - w / 2 + w * 0.15), (cx + w / 2, y1, cz + w / 2 - w * 0.15), bark if i % 2 else bark2, rot=(0, a, 0),
            pivot=(cx, (y0 + y1) / 2, cz))
        box(trunk, (cx - w / 2 + w * 0.15, y0, cz - w / 2), (cx + w / 2 - w * 0.15, y1, cz + w / 2), bark2 if i % 2 else bark, rot=(0, a, 0),
            pivot=(cx, (y0 + y1) / 2, cz))
        # mana veins climbing the bark on four sides
        for k in range(4):
            b = k * math.pi / 2 + a + t * 2.0
            r0 = w / 2 + 0.02
            box(trunk, (cx + math.cos(b) * r0 - 0.2, y0, cz + math.sin(b) * r0 - 0.2), (cx + math.cos(b) * r0 + 0.2, y1, cz + math.sin(b) * r0 + 0.2),
                vein)
    # roots: thick arms over the ground with ley lines burning in them
    for k in range(7):
        a = k * 2 * math.pi / 7 + 0.2
        p0 = (math.cos(a) * 5.0, 21.0, math.sin(a) * 5.0)
        p1 = (math.cos(a) * 11.0, 22.6, math.sin(a) * 11.0)
        p2 = (math.cos(a + 0.2) * 17.0, 23.4, math.sin(a + 0.2) * 17.0)
        chain_boxes(trunk, [p0, p1, p2], 4.2, 1.6, bark)
        seg(trunk, (p1[0], 21.6, p1[2]), (p2[0], 22.8, p2[2]), 0.35, 0.35, vein, up=(0, -1, 0))
    # the sea of clouds round the middle of the trunk
    for k in range(12):
        a = k * 2 * math.pi / 12
        rr = 10.0 + (k % 3) * 1.4
        sphere(trunk, (math.cos(a) * rr, -8.0 + (k % 2) * 1.2, math.sin(a) * rr), 2.6 + (k % 3) * 0.6, cloud, n=3, octa=True)
    # boughs and the crown
    top = 24.0 - n * 2.8
    crown = r.bone('crown', trunk, (0, top, 0), anim='sway', ax=2, amp=0.02, speed=0.03)
    boughs = []
    for k in range(8):
        a = k * 2 * math.pi / 8 + 0.3
        p0 = (0, top + 6.0 - (k % 2) * 3.0, 0)
        p1 = (math.cos(a) * 9.0, top - 2.0 - (k % 3), math.sin(a) * 9.0)
        p2 = (math.cos(a + 0.25) * 17.0, top - 1.0 + (k % 2) * 3.0, math.sin(a + 0.25) * 17.0)
        chain_boxes(crown, [p0, p1, p2], 3.0, 1.2, bark)
        boughs.append(p2)
    for k, (x, y, z) in enumerate(boughs + [(0, top - 9.0, 0), (6, top - 7.0, 5), (-6, top - 7.5, -4), (5, top - 6.0, -7), (-7, top - 6.5, 6)]):
        rad = 6.5 if k < 8 else 7.5
        sphere(crown, (x, y - 2.0, z), rad, (leaf, leaf2, leaf3)[k % 3], n=5, octa=True)
    # glowing blossoms dotted over the crown
    for k in range(26):
        a = k * 2.399
        rr = 6.0 + (k * 7 % 13)
        cbox(crown, (math.cos(a) * rr, top - 6.0 - (k % 5) * 2.4, math.sin(a) * rr), (1.0, 1.0, 1.0),
             M('energy', ('#ffd6f0', '#fff2b0', '#bff6ff')[k % 3], glow=True, glow_amount=0.9))
    # the nine worlds hanging in the boughs
    kinds = ['sea', 'fire', 'ice', 'forest', 'dark', 'light', 'stone', 'sky', 'death']
    for k, kind in enumerate(kinds):
        a = k * 2 * math.pi / 9 + 0.1
        rr = 15.0 + (k % 2) * 3.0
        world_orb(crown, (math.cos(a) * rr, top + 9.5 + (k % 3) * 1.4, math.sin(a) * rr), 2.2, kind)
    return r


# ============================================================================================ reference forms
# After the reference gallery (oror_rework/ref_mobs): the reference bosses are built from a few big, simple volumes
# with dramatic appendages: wings that are the forelimbs with thick finger spars and ragged membranes (Monster
# Expansion's Skrythe), tall rows of spikes (Leivekilth), a box head with a cavernous toothed mouth and ragged sail
# fins (Alex's Caves' Hullbreaker), long thin legs with big talons (Ignathos), slab armour plates (Rakoth).

def _unit3(v):
    v = np.asarray(v, float)
    return v / (np.linalg.norm(v) or 1.0)


def membrane(bone, pts, colour, veins3=(), accent=None, glow=False, **kw):
    """A membrane through 3D points (the first is its root): a plate in the plane of the first three points, cut to the
    polygon of all of them, painted by the wingskin painter in its own plane coordinates."""
    P = [np.asarray(p, float) for p in pts]
    o = P[0]
    u = _unit3(P[1] - o)
    n = _unit3(np.cross(u, P[2] - o))
    v = np.cross(n, u)
    uv = [((p - o) @ u, (p - o) @ v) for p in P]
    a = [q[0] for q in uv]
    b = [q[1] for q in uv]
    a0, a1, b0, b1 = min(a), max(a), min(b), max(b)
    veins = [(((np.asarray(p0) - o) @ u), ((np.asarray(p0) - o) @ v), ((np.asarray(p1) - o) @ u), ((np.asarray(p1) - o) @ v))
             for p0, p1 in veins3]
    mat = M('wingskin', colour, poly=uv, frame=(tuple(o), tuple(u), tuple(v)), veins=veins, accent=accent, glow=glow, **kw)
    c = o + u * (a0 + a1) / 2 + v * (b0 + b1) / 2
    R = np.stack([u, n, v], 1)
    return bb.obox(bone, c, (a1 - a0, 0.0, b1 - b0), R, mat)


def ragged(p0, p1, n, depth, side, jag=0.35, seed=0):
    """Points along an edge from p0 to p1 that scallop inward by `depth` (toward `side`, a direction) between the ends,
    with small jags: the trailing edge of a wyvern's membrane or a fish's fin."""
    rng = np.random.default_rng(seed)
    p0, p1, side = np.asarray(p0, float), np.asarray(p1, float), _unit3(side)
    out = []
    for k in range(1, n):
        t = k / n
        q = p0 + (p1 - p0) * t + side * depth * math.sin(math.pi * t)
        q = q + side * depth * jag * (rng.random() - 0.5) * (1 if k % 2 else -1)
        out.append(tuple(q))
    return out


def wing_arm(r, parent, side, shoulder, elbow, wrist, tips, membrane_c, spar, claw, body_pt, name=None, accent=None,
             glow=False, skin_kw=None, spar_w=1.6, amp=0.12, speed=0.06):
    """A wyvern's wing that is its forelimb: shoulder, elbow raised, wrist planted on the ground with a thumb claw,
    thick finger spars radiating up and back to `tips`, and a ragged membrane between each pair of fingers and from
    the last finger back to the flank (`body_pt`)."""
    sx = side
    b = r.bone(name or ('wing_r' if sx < 0 else 'wing_l'), parent, shoulder, anim='sway', ax=2, amp=amp, speed=speed, phase=sx)
    chain_boxes(b, [shoulder, elbow], spar_w * 1.5, spar_w * 1.25, spar)
    chain_boxes(b, [elbow, wrist], spar_w * 1.25, spar_w, spar)
    for j in (elbow, wrist):
        cbox(b, j, (spar_w * 1.6,) * 3, spar)
    # thumb claw and the knuckle it walks on
    seg(b, wrist, (wrist[0] + sx * 0.4, wrist[1] + 1.6, wrist[2] - 1.6), 0.9, 0.9, claw, up=(0, 0, -1))
    for k, t in enumerate(tips):
        mid = lerp(wrist, t, 0.42)
        chain_boxes(b, [wrist, mid, t], spar_w * 0.95, spar_w * 0.4, spar)
        cbox(b, mid, (spar_w * 1.05,) * 3, spar)
    kw = dict(skin_kw or {})
    for k in range(len(tips)):
        a = tips[k]
        nxt = tips[k + 1] if k + 1 < len(tips) else body_pt
        inward = _unit3(np.asarray(wrist, float) - (np.asarray(a, float) + np.asarray(nxt, float)) / 2)
        edge = ragged(a, nxt, 7, np.linalg.norm(np.asarray(nxt) - np.asarray(a)) * 0.22, inward, seed=k + 3)
        pts = [wrist, a] + edge + [nxt]
        veins = [(wrist, lerp(wrist, lerp(a, nxt, 0.5), 0.8))]
        membrane(b, pts, membrane_c, veins3=veins, accent=accent, glow=glow, **kw)
    return b


def crystal(bone, base, tip, w, mat, cap=None):
    """A tall thin prism (Leivekilth's ice spikes, Demiurgos's gems): a square shaft tapering to a point."""
    seg(bone, base, lerp(base, tip, 0.7), w, w, mat, up=(0, 0, 1), ext=w * 0.3)
    seg(bone, lerp(base, tip, 0.6), tip, w * 0.6, w * 0.6, cap or mat, up=(0, 0, 1))


def talon_foot(bone, ankle, toe_dir, w, skin, claw, n=3):
    """A big bird-of-prey foot: three long toes spread forward with hooked talons, one back toe."""
    ax, ay, az = ankle
    for k in range(n):
        spread = (k - (n - 1) / 2) * 0.55
        dx, dz = math.sin(spread) * 3.2, -math.cos(spread) * 3.2
        knuckle = (ax + dx * 0.55, ay + 0.6, az + dz * 0.55)
        toe = (ax + dx, ay + 1.2, az + dz)
        chain_boxes(bone, [(ax, ay, az), knuckle, toe], w * 0.55, w * 0.42, skin)
        chain_boxes(bone, [toe, (toe[0] + dx * 0.35, ay + 2.0, toe[2] + dz * 0.35)], w * 0.38, w * 0.15, claw)
    chain_boxes(bone, [(ax, ay, az), (ax, ay + 1.4, az + 2.0), (ax, ay + 2.0, az + 2.8)], w * 0.4, w * 0.15, claw)


def long_leg(r, parent, name, anim, hip, knee, ankle, foot, w, skin, plate, claw):
    """Monster Expansion's long, thin wyvern leg: a muscular thigh, a long shin back to a high ankle, a long foot."""
    up = r.bone(name, parent, hip, anim=anim)
    rbox(up, (hip[0] - w * 0.75, hip[1] - w, hip[2] - w * 1.1), (hip[0] + w * 0.75, hip[1] + w * 0.9, hip[2] + w * 1.0), skin, bevel=w * 0.3)
    seg(up, hip, knee, w * 1.15, w * 1.3, skin, up=(0, 0, -1), ext=w * 0.4)
    low = r.bone(name + '_low', up, knee, anim='knee')
    seg(low, knee, ankle, w * 0.6, w * 0.7, skin, up=(0, 0, 1), ext=w * 0.3)
    box(low, (knee[0] - w * 0.36, knee[1] + 0.4, knee[2] + w * 0.32), (knee[0] + w * 0.36, ankle[1] - 0.5, knee[2] + w * 0.6), plate,
        rot=(-0.4, 0, 0), pivot=knee)
    seg(low, ankle, foot, w * 0.5, w * 0.5, skin, up=(0, 0, -1), ext=w * 0.25)
    talon_foot(low, foot, (0, 0, -1), w * 1.3, skin, claw)
    return up, low


@recipe
def demiurgos():
    # 空創龍王 デミウルゴス, rebuilt on Monster Expansion's Skrythe: a wyvern whose wings are its forelimbs, walking on
    # its wrists, with enormous ragged membranes (the black-scaled small dragon of the lore: five metres, rainbow gem
    # glints in jet scales, mystery more than mass), a long neck, a long-snouted head under a crest of tall gems, long
    # thin hind legs with big talons, a long tail ending in a gem cluster. Rows of rainbow crystals along the spine
    # replace scattered glints; the membranes hold a night sky.
    r = rig('demiurgos')
    gems = ['#ff6ad5', '#6af0ff', '#ffe46a', '#7dff8a', '#b48cff']
    gem = lambda k: M('gem', gems[k % len(gems)], glow=True)
    skin = M('shingle', '#2a2636', belly='#4a4064', scale_size=1.3)
    plate = M('carapace', '#1c1a26', accent='#b48cff')
    spar = M('carapace', '#141018')
    claw = M('horn', '#2a2438', tip='#e6d2ff', glow=True)
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 12, 2), anim='breath')
    rbox(body, (-4.0, 7.6, -6.5), (4.0, 15.0, 1.0), skin, bevel=1.4)
    rbox(body, (-3.4, 8.6, 0.0), (3.4, 14.2, 8.0), skin, bevel=1.2)
    rbox(body, (-3.8, 8.2, 7.0), (3.8, 14.0, 12.0), skin, bevel=1.2)
    for z0, z1 in ((-6.0, 0.0), (0.4, 7.6)):
        box(body, (-2.8, 14.2, z0), (2.8, 15.2, z1), M('carapace', '#4a4064'))
    # a row of rainbow crystals along the spine, tallest over the shoulders (Leivekilth's spike row)
    for k, (z, h, lean) in enumerate(((-5.0, 6.5, -1), (-2.2, 5.0, 1), (0.8, 3.8, -1), (3.6, 2.8, 1), (6.4, 2.2, -1), (9.2, 1.8, 1))):
        y0 = 7.8 if z < 7 else 8.4
        crystal(body, (lean * 0.8, y0, z), (lean * 2.0, y0 - h, z + h * 0.5), 0.9 + h * 0.1, gem(k))
    neck = r.bone('neck', body, (0, 9.5, -5.5), anim='sway', ax=1, amp=0.04, speed=0.05)
    chain_boxes(neck, [(0, 10.5, -5.5), (0, 6.5, -9.5), (0, 3.0, -12.5), (0, 1.5, -14.5)], 4.2, 3.0, skin)
    for k in range(4):
        p = lerp((0, 8.5, -7.5), (0, 0.6, -14.0), k / 3)
        crystal(neck, p, (0, p[1] - 3.2 + k * 0.3, p[2] + 1.8), 0.8, gem(k + 2))
    head = r.bone('head', neck, (0, 1.6, -14.8), anim='head')
    rbox(head, (-2.3, -1.2, -20.0), (2.3, 2.8, -13.6), skin, bevel=0.6)                       # skull
    rbox(head, (-1.7, -0.2, -24.6), (1.7, 2.4, -19.6), skin, bevel=0.5, faces={'bottom': M('mouth', '#43101c')})   # long snout
    box(head, (-1.0, -0.6, -24.2), (1.0, -0.1, -15.0), plate)                                   # nose ridge
    for sx in (-1, 1):
        side = 'left' if sx > 0 else 'right'
        box(head, (sx * 1.0, -1.8, -20.5), (sx * 2.8, -0.8, -16.4), plate, rot=(-0.25, 0, sx * 0.15), pivot=(sx * 2, -1.2, -18.5))
        cbox(head, (sx * 2.25, 0.6, -18.2), (0.3, 1.4, 2.6), M('simple', '#0c0a10'))
        eye(head, (sx * 2.38, 0.6, -18.2), 2.6, 1.2, side, M('eye', '#d29cff', pupil='slit', mood='fierce', lid='#1c1a28', glow_amount=1.0))
        horn(head, [(sx * 1.6, -1.0, -15.0), (sx * 2.6, -3.6, -12.4), (sx * 3.2, -5.6, -9.0), (sx * 3.0, -6.4, -5.6)], 1.4, 0.35, claw)
        teeth(head, sx * 1.35, 2.4, -24.2, -19.8, 4, 0.5, M('tooth', '#efe6d2'), down=True)
    for k in range(3):                                                                         # the crown of gems
        crystal(head, (0, -1.1, -17.5 + k * 1.6), (0, -5.0 - k * 0.8, -15.0 + k * 1.8), 0.9, gem(k))
    jaw = r.bone('jaw', head, (0, 2.6, -14.4), rot=(0.14, 0, 0), anim='jaw')
    rbox(jaw, (-1.5, 2.4, -24.0), (1.5, 3.8, -14.4), M('carapace', '#4a4064'), bevel=0.4, faces={'top': M('mouth', '#43101c')})
    for sx in (-1, 1):
        teeth(jaw, sx * 1.15, 2.5, -23.6, -19.6, 3, 0.45, M('tooth', '#efe6d2'), down=False)
    # long thin hind legs with talons
    for sx in (-1, 1):
        long_leg(r, body, 'leg_b' + ('r' if sx < 0 else 'l'), 'leg_l' if sx < 0 else 'leg_r', (sx * 3.6, 12.0, 9.0),
                 (sx * 4.4, 16.0, 4.6), (sx * 4.4, 20.6, 11.0), (sx * 4.4, 22.4, 8.6), 2.2, skin, plate, claw)
    # the wings are the forelimbs: walking on the wrists, the fingers fanned up and back, a night sky in the membranes
    wing_kw = dict(stars=0.03, streaks='#ff9ae8')
    for sx in (-1, 1):
        wing_arm(r, body, sx, (sx * 3.8, 9.0, -3.5), (sx * 11.0, 3.0, 1.5), (sx * 10.5, 23.0, -8.0),
                 [(sx * 13.0, -15.0, -4.0), (sx * 24.0, -12.0, 6.0), (sx * 30.0, -2.0, 15.0), (sx * 24.0, 8.0, 24.0)],
                 '#261c48', spar, claw, (sx * 3.6, 12.0, 11.0), accent='#b48cff', glow=True, skin_kw=wing_kw, spar_w=1.5)
    # a long tail of tapering boxes, crystals along it, a gem cluster at the end
    ends = plated_tail(r, body, (0, 11.0, 11.5), [5.0, 5.0, 4.8, 4.6, 4.4, 4.0], [3.6, 3.0, 2.5, 2.0, 1.6, 1.2], skin, plate,
                       claw, droop=0.2, spikes=False)
    for i, (b, q) in enumerate(ends[:-1]):
        crystal(b, (0, q[1] - 1.2, q[2] - 1.5), (0, q[1] - 3.4 + i * 0.3, q[2] - 0.2), 0.7, gem(i))
    b, (x, y, z) = ends[-1]
    for k, (dx, dy, dz, sz) in enumerate(((0, 0, 1.8, 2.2), (1.0, -1.0, 0.9, 1.5), (-1.0, -0.8, 1.0, 1.4), (0, 1.1, 0.7, 1.2))):
        cbox(b, (x + dx, y + dy, z + dz), (sz, sz * 1.7, sz), gem(k), rot=(0.4, 0.7, 0.3 * k))
    return fit_height(r, ('wing',))


def ragged_fin(bone, root0, root1, tip, colour, depth=0.1, accent=None, glow=False, n=11, seed=0, rays=3, **kw):
    """A fin standing on the line root0-root1 and reaching `tip`: straight leading edge, ragged scalloped trailing edge,
    a few rays from the root (Hullbreaker's sail fins)."""
    r0, r1, t = (np.asarray(p, float) for p in (root0, root1, tip))
    inward = _unit3((r0 + r1) / 2 - (t + r1) / 2)
    edge = ragged(t, r1, n, np.linalg.norm(r1 - t) * min(depth, 0.12), inward, jag=1.4, seed=seed)
    veins = [(tuple(lerp(r0, r1, (k + 0.5) / (rays + 1))), tuple(lerp(t, r1, (k + 1) / (rays + 1)))) for k in range(rays)]
    return membrane(bone, [tuple(r0), tuple(t)] + edge + [tuple(r1)], colour, veins3=veins, accent=accent, glow=glow, **kw)


def sail_fin(bone, r0, r1, height, lean, colour, spine_mat=None, light_mat=None, n_rays=4, seed=0, **kw):
    """A broad sail fin on the base r0-r1 (Hullbreaker): it rises `height` (along -y, leaning back by `lean`), its top
    edge scalloped between ray tips that end in spines and lights."""
    r0, r1 = np.asarray(r0, float), np.asarray(r1, float)
    up = np.array([0.0, -height, lean])
    tops = []
    for k in range(n_rays + 1):
        t = k / n_rays
        h = 1.0 - 0.45 * t                                    # tallest at the front, falling away behind
        tops.append(lerp(r0, r1, t * 0.85 + 0.05) + up * h)
    pts = [tuple(r0)]
    for k in range(n_rays):
        a, b = np.asarray(tops[k]), np.asarray(tops[k + 1])
        pts.append(tuple(a))
        mid = (a + b) / 2 + np.array([0.0, height * 0.16, 0.0])
        pts.append(tuple(mid))
    pts.append(tuple(tops[-1]))
    pts.append(tuple(r1))
    veins = [(tuple(lerp(r0, r1, k / n_rays * 0.85 + 0.05)), tuple(tops[k])) for k in range(n_rays + 1)]
    membrane(bone, pts, colour, veins3=veins, **kw)
    for k, t in enumerate(tops):
        base = lerp(r0, r1, k / n_rays * 0.85 + 0.05)
        if spine_mat is not None:
            seg(bone, base, t, 0.5, 0.5, spine_mat)
            spike(bone, t, (t[0], t[1] - 1.6, t[2] + 1.0), 0.45, spine_mat)
        if light_mat is not None:
            cbox(bone, t, (0.55, 0.55, 0.55), light_mat)
    return tops


def dots(bone, pts, size, mat):
    for p in pts:
        cbox(bone, p, (size, size, size), mat)


@recipe
def enkou():
    # 災極海獣 淵煌, rebuilt on Alex's Caves' Hullbreaker and Cataclysm's Leviathan: a great box of a head that is
    # mostly mouth, three rows of teeth in it, pale blue light-organ eyes in armoured sockets; a body stepping down in
    # big boxes clad in rows of obsidian scale plates, to a long tail and a shark's crescent fluke; the lore's shark
    # edge in one huge ragged dorsal fin, an orca's white belly and paddle fins, an ancient dragon's horns, brow
    # spikes and whiskers; a lateral line of glowing dots and ragged sail fins down the back.
    r = rig('enkou')
    glowc = '#8fe8ff'
    hide = M('shingle', '#121824', belly='#d6e2ea', countershade=(16.6, 0.8), scale_size=1.1)
    dark = M('shingle', '#0c1018', belly='#d6e2ea', scale_size=0.9)
    white = M('carapace', '#d6e2ea')
    plate = M('carapace', '#1a2232', accent=glowc)
    scute = M('carapace', '#202a3a')
    hornm = M('horn', '#182030', tip=glowc, glow=True)
    spine = M('horn', '#0e1420', tip='#5a7a9a')
    tooth = M('tooth', '#f4efe4')
    mouth = M('mouth', '#2a0a12')
    light = M('energy', glowc, glow=True)
    fin_c = '#1c2a40'
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.2, speed=0.05)
    body = r.bone('body', root, (0, 13, 0), anim='sway', ax=1, amp=0.05, speed=0.06)
    # body: three big boxes stepping down toward the tail
    segs = [(-6.4, 6.0, 19.6, -10.0, 3.0), (-5.4, 7.0, 18.6, 2.4, 11.0), (-4.0, 8.4, 17.0, 10.4, 17.0)]
    for (x0, y0, y1, z0, z1) in segs:
        rbox(body, (x0, y0, z0), (-x0, y1, z1), hide, bevel=1.4)
    box(body, (-5.0, 19.4, -9.0), (5.0, 19.9, 10.0), white)                                     # white belly
    for k in range(9):                                                                          # belly grooves
        box(body, (-4.6, 19.85, -8.4 + k * 2.0), (4.6, 19.95, -7.8 + k * 2.0), M('carapace', '#a8b8c4'))
    # armour: overlapping obsidian scale plates in two rows down each side of the back, a ridge of spikes between
    for (x0, y0, y1, z0, z1) in segs:
        for row, yy in enumerate((y0 + 0.4, y0 + 2.6)):
            n = int((z1 - z0) / 2.2)
            for k in range(n):
                z = z0 + 1.0 + k * 2.2
                for sx in (-1, 1):
                    xx = sx * (-x0 - 0.6 - row * 0.6)
                    box(body, (xx - 1.2, yy - 0.7, z - 1.1), (xx + 1.2, yy + 0.6, z + 1.3), scute, rot=(0.35, 0, -sx * (0.5 + row * 0.35)),
                        pivot=(xx, yy, z))
    for z in np.arange(-9.0, 17.0, 1.6):
        if -6.5 < z < 3.5 or 4.0 < z < 10.8 or 11.0 < z < 16.8:
            continue
        y = 6.0 if z < 3 else (7.0 if z < 10.5 else 8.4)
        spike(body, (0, y, z), (0, y - 1.6, z + 0.9), 0.6, spine)
    for sx in (-1, 1):
        box(body, (sx * 6.38, 14.0, -8.0), (sx * 6.5, 18.6, -1.0), white)                            # orca flank patch
        for k in range(4):                                                                          # gill slits
            box(body, (sx * 6.36, 9.6, -9.2 + k * 1.3), (sx * 6.5, 14.6, -8.7 + k * 1.3), M('simple', '#04060a'))
        dots(body, [(sx * (6.45 if z < 3 else (5.45 if z < 10.5 else 4.05)), 11.6 + z * 0.05, z) for z in np.arange(-6.0, 17.0, 1.4)], 0.45, light)
        dots(body, [(sx * 6.45, 9.0, z) for z in np.arange(-4.0, 2.5, 1.8)], 0.4, light)
    # a shark's dorsal fin: tall, broad at the root, its trailing edge curved like a sickle; then two broad ragged
    # sail fins down the back (Hullbreaker)
    fk = dict(accent='#4a6a8e', edge='#5a86b0', streaks=True)
    tip = (0, -13.0, 4.0)
    falcate = ragged(tip, (0, 6.2, 4.6), 9, 3.0, (0, 0, -1), jag=0.5, seed=1)
    membrane(body, [(0, 6.2, -9.0), tip] + falcate + [(0, 6.2, 4.6)], fin_c,
             veins3=[((0, 6.2, z), lerp((0, 6.2, z), tip, 0.85)) for z in (-6.0, -3.0, 0.0)], **fk)
    for z in (-6.0, -3.0, 0.0):
        seg(body, (0, 6.2, z), lerp((0, 6.2, z), tip, 0.85), 0.45, 0.45, spine)
    spike(body, tip, (0, -15.2, 5.6), 0.55, spine)
    cbox(body, tip, (0.6, 0.6, 0.6), light)
    sail_fin(body, (0, 7.2, 5.0), (0, 7.2, 11.0), 8.5, 3.0, fin_c, spine, light, n_rays=4, seed=2, **fk)
    sail_fin(body, (0, 8.6, 11.4), (0, 8.6, 16.6), 6.5, 2.6, fin_c, spine, light, n_rays=3, seed=3, **fk)
    for sx in (-1, 1):
        fb = r.bone('fin_' + ('r' if sx < 0 else 'l'), body, (sx * 6.2, 17.6, -6.0), anim='sway', ax=2, amp=0.14, speed=0.08, phase=sx)
        ptip = (sx * 18.0, 23.0, 5.0)
        edge = ragged(ptip, (sx * 6.2, 17.6, 0.5), 8, 2.0, (0, 0, -1), jag=0.8, seed=5 + sx)
        membrane(fb, [(sx * 6.2, 17.6, -9.0), (sx * 12.0, 20.6, -5.0), ptip] + edge + [(sx * 6.2, 17.6, 0.5)], fin_c,
                 veins3=[((sx * 6.2, 17.6, z), lerp((sx * 6.2, 17.6, z), ptip, 0.8)) for z in (-7.0, -4.0, -1.0)], **fk)
        for z in (-7.0, -4.0, -1.0):
            seg(fb, (sx * 6.2, 17.6, z), lerp((sx * 6.2, 17.6, z), ptip, 0.8), 0.45, 0.45, spine)
        cbox(fb, ptip, (0.6, 0.6, 0.6), light)
        pb = r.bone('pelvic_' + ('r' if sx < 0 else 'l'), body, (sx * 5.0, 18.2, 9.0), anim='sway', ax=2, amp=0.1, speed=0.08, phase=-sx)
        membrane(pb, [(sx * 5.0, 18.2, 7.0), (sx * 9.5, 21.8, 12.0)] + ragged((sx * 9.5, 21.8, 12.0), (sx * 5.0, 18.2, 11.0), 5, 1.0,
                 (0, 0, -1), seed=8 + sx) + [(sx * 5.0, 18.2, 11.0)], fin_c, **fk)
    # head: a big box that is mostly mouth
    head = r.bone('head', body, (0, 13, -10), anim='head')
    rbox(head, (-6.0, 5.4, -24.0), (6.0, 13.0, -9.6), dark, bevel=1.4, faces={'bottom': mouth})        # upper skull
    rbox(head, (-5.2, 6.0, -27.4), (5.2, 12.0, -23.0), dark, bevel=1.2, faces={'bottom': mouth})       # overhanging snout
    box(head, (-5.6, 12.6, -25.6), (5.6, 13.2, -10.0), mouth)                                          # roof of the mouth
    box(head, (-1.2, 4.8, -27.0), (1.2, 5.6, -11.0), plate)                                            # skull ridge
    for k in range(5):
        spike(head, (0, 4.9, -24.0 + k * 3.0), (0, 3.4 - k * 0.2, -22.8 + k * 3.0), 0.7, spine)
    for sx in (-1, 1):
        side = 'left' if sx > 0 else 'right'
        # armoured eye socket: a heavy brow with spikes over a pale blue light organ
        box(head, (sx * 3.0, 4.8, -20.6), (sx * 6.6, 6.4, -14.0), plate, rot=(-0.1, 0, sx * 0.25), pivot=(sx * 5.0, 5.6, -17.0))
        for k in range(3):
            spike(head, (sx * (5.6 + k * 0.2), 5.0, -19.6 + k * 2.2), (sx * (7.4 + k * 0.3), 4.0, -18.4 + k * 2.2), 0.6, spine)
        cbox(head, (sx * 6.0, 8.4, -17.0), (0.3, 3.0, 4.2), M('simple', '#04060a'))
        eye(head, (sx * 6.12, 8.4, -17.0), 3.6, 2.4, side, M('eye', '#bff4ff', pupil='round', mood='fierce', lid='#0a0e16', glow_amount=1.0))
        box(head, (sx * 5.9, 10.6, -21.0), (sx * 6.5, 12.6, -11.0), plate, rot=(0, sx * 0.05, 0))        # cheek plate
        dots(head, [(sx * 6.55, 11.6, z) for z in (-20.0, -18.6, -17.2, -15.8, -14.4, -13.0)], 0.4, light)
        dots(head, [(sx * 5.25, 7.0, z) for z in (-26.4, -25.0)], 0.5, light)                          # snout lights
        box(head, (sx * 2.0 - 0.5, 5.95, -27.45), (sx * 2.0 + 0.5, 7.0, -27.35), M('simple', '#04060a'))  # nostrils
        horn(head, [(sx * 4.6, 5.8, -14.0), (sx * 6.2, 3.4, -10.0), (sx * 7.0, 2.4, -5.0), (sx * 6.6, 2.4, -0.5)], 2.2, 0.5, hornm)
        horn(head, [(sx * 5.8, 9.0, -12.0), (sx * 8.4, 8.2, -8.6), (sx * 9.6, 8.6, -5.2)], 1.4, 0.4, hornm)
        for row in range(3):
            teeth(head, sx * (5.0 - row * 1.1), 13.0, -26.0 + row * 1.4, -11.0, 11 - row * 2, 1.0 - row * 0.22, tooth, down=True)
    teeth_x(head, -26.8, 12.0, -4.4, 4.4, 7, 1.1, tooth, down=True)
    jaw = r.bone('jaw', head, (0, 13.4, -10.5), rot=(0.42, 0, 0), anim='jaw')
    rbox(jaw, (-5.6, 13.4, -26.0), (5.6, 17.6, -10.5), white, bevel=1.2, faces={'top': mouth})
    box(jaw, (-3.6, 17.4, -25.6), (3.6, 18.2, -16.0), plate)                                       # chin plate
    for sx in (-1, 1):
        for row in range(2):
            teeth(jaw, sx * (4.6 - row * 1.1), 13.4, -25.0 + row * 1.4, -12.0, 10 - row * 2, 0.95 - row * 0.22, tooth, down=False)
        box(jaw, (sx * 5.5, 14.0, -25.0), (sx * 5.8, 17.0, -12.0), plate)
        bb_ = r.bone('barbel_' + ('r' if sx < 0 else 'l'), jaw, (sx * 3.6, 17.4, -24.0), anim='sway', ax=0, amp=0.2, speed=0.07, phase=sx)
        chain_boxes(bb_, [(sx * 3.6, 17.4, -24.0), (sx * 4.4, 21.0, -23.0), (sx * 4.0, 25.0, -21.0), (sx * 3.0, 27.0, -18.0)], 0.9, 0.4,
                    M('horn', '#182030', tip=glowc, glow=True))
    teeth_x(jaw, -25.6, 13.4, -4.0, 4.0, 6, 1.0, tooth, down=False)
    # tail: tapering boxes with scale plates, glowing dots, a crescent fluke with rays
    ends = plated_tail(r, body, (0, 12.6, 16.6), [5.0, 4.6, 4.2, 3.8, 3.4], [6.6, 5.2, 4.0, 3.0, 2.2], hide, plate, spine, droop=0.02, spikes=True,
                       amp=0.16, speed=0.07)
    for i, (b, q) in enumerate(ends):
        x, y, z = q
        dots(b, [(sx * (3.3 - i * 0.55), y - 0.6, z - 2.0) for sx in (-1, 1)], 0.42, light)
    b, (x, y, z) = ends[-1]
    # the crescent fluke: a tall upper lobe and a shorter lower one, both broad at the root
    for lobe, (h, back) in ((-1, (14.0, 7.0)), (1, (9.0, 5.5))):
        tipl = (0, y + lobe * h, z + back)
        edge = ragged(tipl, (0, y, z + 2.4), 7, 1.6, (0, 0, -1), jag=0.8, seed=9 + lobe)
        membrane(b, [(0, y, z - 2.0), tipl] + edge + [(0, y, z + 2.4)], fin_c,
                 veins3=[((0, y, z - 1.0), lerp((0, y, z), tipl, 0.9)), ((0, y, z + 0.6), lerp((0, y, z + 1.0), tipl, 0.8))], **fk)
        seg(b, (0, y, z - 1.0), lerp((0, y, z), tipl, 0.95), 0.5, 0.5, spine)
        cbox(b, tipl, (0.6, 0.6, 0.6), light)
    return r

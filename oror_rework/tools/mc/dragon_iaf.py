"""059g: the dragons built as Ice and Fire builds its dragons (the user: "今作ってるドラゴンと画像を見て同じものに見えるか？
アッチが結構理想形 ... もっとあるだろいろいろ"): many parts, each a few deliberate boxes, at twice the size of creatures_ia's
(one texture pixel to a model pixel, so the scales are as fine as theirs).

  * the head: a skull, a snout as long again with a plated ridge, nostrils and a horn on the nose, brow plates that
    frown, small slit eyes under them, two great horns swept back in three links and a lesser pair under them, cheek
    spikes, teeth in both jaws, a red mouth, a tongue, the jaw hung open;
  * the neck: four links rising in an S, thick at the shoulders, plated underneath, spined along the top;
  * the body: a deep chest raised, humps where the wings root, a narrower waist, the hips; belly plates in bands; a
    ridge of plates and spines down the back;
  * the legs: three links each (thigh, shin, foot), a muscle over the hind thigh, toes and claws;
  * the wings: a thick arm, five finger bones running out past a membrane cut deep between them, a thumb claw;
  * the tail: fourteen links, as long as the rest, spined on top and finned down both sides, a spade or a gem at the end.
Model space: pixels, y down (the ground is y = 24), the front is -z.
"""
import math
import numpy as np
from paint import M
import creatures_ia as CI

RECIPES = {}


def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn


def leg(r, parent, name, anim, pts, widths, mat, claw, toes=3):
    """Hip, knee, ankle, foot: the thigh (anim), the shin and foot (knee), toes with claws."""
    up = r.bone(name, parent, pts[0], anim=anim)
    CI.seg(up, pts[0], pts[1], widths[0], widths[0] * 1.15, mat, up=(0, 0, -1), ext=widths[0] * 0.35)
    low = r.bone(name + '_low', up, pts[1], anim='knee')
    CI.seg(low, pts[1], pts[2], widths[1], widths[1], mat, up=(0, 0, -1), ext=widths[1] * 0.4)
    CI.seg(low, pts[2], pts[3], widths[2], widths[2], mat, up=(0, 0, -1), ext=widths[2] * 0.4)
    fx, fy, fz = pts[3]
    w = widths[2] * 1.5
    CI.box(low, (fx - w / 2, fy - 1.0, fz - 2.5), (fx + w / 2, 24.0, fz + 2.0), mat)
    for t in range(toes):
        x = fx + (t - (toes - 1) / 2) * w / toes * 1.05
        CI.seg(low, (x, 23.0, fz - 2.0), (x, 23.3, fz - 5.0), 1.3, 1.5, mat, up=(0, -1, 0))
        CI.seg(low, (x, 23.0, fz - 5.0), (x, 24.0, fz - 7.2), 0.7, 0.9, claw, up=(0, -1, 0))
    CI.seg(low, (fx, fy, fz + 1.5), (fx, 23.6, fz + 3.6), 0.6, 0.8, claw, up=(0, -1, 0))        # the dewclaw
    return up, low


def wing(r, parent, side, shoulder, arm, fingers, membrane, spar, claw, rot, accent=None, glow=False, ragged=False, shards=None):
    sx = side
    b = r.bone('wing_r' if sx < 0 else 'wing_l', parent, shoulder, rot=(rot[0], rot[1] * sx, rot[2] * -sx), anim='sway', ax=2,
               amp=0.22, speed=0.08)
    x0, y, z0 = shoulder
    Pt = lambda xz: (x0 + sx * xz[0], y, z0 + xz[1])
    elbow, wrist = Pt(arm[0]), Pt(arm[1])
    CI.chain_boxes(b, [(x0, y, z0), elbow, wrist], 5.0, 2.8, spar)
    tips = [Pt(t) for t in fingers]
    for t in tips:
        d = np.subtract(t, wrist)
        ext = tuple(np.add(t, d / np.linalg.norm(d) * 5.0))
        CI.chain_boxes(b, [wrist, t, ext], 2.2, 0.6, spar)
    CI.seg(b, wrist, (wrist[0] + sx * 1.0, y - 1.2, wrist[2] - 5.0), 1.6, 1.6, claw)
    body_end = Pt((3.0, fingers[-1][1] * 0.84))
    outline = [(x0, z0), (elbow[0], elbow[2]), (wrist[0], wrist[2])]
    scallops = []
    for i, t in enumerate(tips):
        outline.append((t[0], t[2]))
        n = tips[i + 1] if i + 1 < len(tips) else body_end
        mid = ((t[0] + n[0]) / 2, (t[2] + n[2]) / 2)
        sc = (mid[0] * 0.62 + wrist[0] * 0.38, mid[1] * 0.62 + wrist[2] * 0.38)
        if ragged:
            q1 = (t[0] * 0.72 + sc[0] * 0.28 + sx * 1.2, t[2] * 0.72 + sc[1] * 0.28 + 1.6)
            q2 = (n[0] * 0.72 + sc[0] * 0.28 - sx * 0.8, n[2] * 0.72 + sc[1] * 0.28 - 1.2)
            outline += [q1, (q1[0] * 0.5 + sc[0] * 0.5 - sx * 1.6, q1[1] * 0.5 + sc[1] * 0.5 + 0.6), sc, q2]
        else:
            outline.append(sc)
        scallops.append(sc)
    outline.append((body_end[0], body_end[2]))
    veins = [(wrist[0], wrist[2], t[0], t[2]) for t in tips] + [(elbow[0], elbow[2], body_end[0], body_end[2])]
    veins += [(elbow[0], elbow[2], sc[0], sc[1]) for sc in scallops[-3:]]
    xs, zs = [p[0] for p in outline], [p[1] for p in outline]
    CI.box(b, (min(xs), y + 0.6, min(zs)), (max(xs), y + 0.6, max(zs)),
           M('wingskin', membrane, poly=outline, axes='xz', veins=veins, accent=accent, glow=glow, streaks=True))
    if shards:
        for k, sc in enumerate(scallops):
            CI.cbox(b, (sc[0], y + 2.4, sc[1]), (1.2, 4.6, 1.2), M('gem', shards[k % len(shards)], glow=True), rot=(0.2, 0.4, 0.1))
    return b


def iaf_dragon(key, skin, belly, plate, horn, spike, claw, eye_m, membrane, spar, accent=None, wing_glow=False, crown=None,
               gems=None, chest_gem=None, ragged=False, shards=None, fins=None, tail_tip=None, seams=None):
    r = CI.rig(key, td=1)
    mouth = M('mouth', '#5a1420')
    tooth = M('tooth', '#f0e8d4')
    tongue = M('simple', '#a83048')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 2, 4), rot=(-0.12, 0, 0), anim='breath')
    # ------------------------------------------------------------------------------------------------ the body
    CI.rbox(body, (-10.0, -9.0, -21.0), (10.0, 12.5, -3.0), skin, bevel=3.2)        # the deep chest
    CI.rbox(body, (-8.0, -6.0, -4.0), (8.0, 11.0, 13.0), skin, bevel=2.5)           # the waist
    CI.rbox(body, (-7.0, -5.0, 12.0), (7.0, 9.0, 23.0), skin, bevel=2.2)            # the hips
    for sx in (-1, 1):
        CI.rbox(body, (sx * 5.5, -11.0, -17.0), (sx * 10.5, -3.0, -6.0), skin, bevel=1.6)   # the wings' roots
        CI.rbox(body, (sx * 5.0, -3.0, 12.0), (sx * 9.0, 7.0, 22.0), skin, bevel=1.6)       # the hind thighs' muscle
    for k in range(10):                                                              # belly plates in bands
        z = -18.0 + k * 3.9
        yb = 12.0 - max(0.0, (z + 3.0)) * 0.13
        CI.box(body, (-6.0 + k * 0.12, yb, z), (6.0 - k * 0.12, yb + 0.9, z + 3.3), belly)
    for k in range(9):                                                               # the back's plates and spines
        z = -18.0 + k * 5.0
        yt = -8.0 + (z + 18.0) * 0.07
        CI.box(body, (-1.8, yt - 1.3, z), (1.8, yt + 0.4, z + 3.8), plate)
        h = 6.0 - k * 0.42
        CI.seg(body, (0, yt - 0.9, z + 1.9), (0, yt - 0.9 - h, z + 1.9 + h * 0.75), 1.3, 2.6, spike, up=(0, 0, 1))
    if seams is not None:
        for sx in (-1, 1):
            CI.box(body, (sx * 9.05, 0.0, -18.0), (sx * 9.2, 0.8, -5.0), seams)
            CI.box(body, (sx * 8.05, 1.0, -3.0), (sx * 8.2, 1.8, 12.0), seams)
    if gems:
        for i, (x, y, z, sz) in enumerate(((-9.1, 2.0, -14.0, 2.6), (9.1, 2.0, -14.0, 2.6), (-8.1, 3.0, 4.0, 2.0), (8.1, 3.0, 4.0, 2.0),
                                            (-7.1, 1.0, 17.0, 1.6), (7.1, 1.0, 17.0, 1.6))):
            CI.cbox(body, (x, y, z), (sz, sz, sz), M('gem', gems[i % len(gems)], glow=True), rot=(0.3, 0.6, 0.2))
    if chest_gem is not None:
        CI.cbox(body, (0, 4.0, -20.6), (5.0, 6.0, 1.4), chest_gem, rot=(0, 0, 0.785))
        CI.cbox(body, (0, 4.0, -20.3), (7.0, 8.0, 0.8), M('metal', '#d8b060'), rot=(0, 0, 0.785))
    # ------------------------------------------------------------------------------------------------ the neck
    pts = [(0, -4.0, -17.0), (0, -11.0, -23.0), (0, -18.0, -27.0), (0, -24.0, -30.5), (0, -29.0, -35.0)]
    widths = [12.0, 10.6, 9.4, 8.4]
    bone = body
    for i in range(4):
        bone = r.bone(f'neck{i + 1}', bone, pts[i], anim='sway', ax=1, amp=0.03, speed=0.05, phase=0.6 * i)
        p, q = np.asarray(pts[i], float), np.asarray(pts[i + 1], float)
        CI.seg(bone, tuple(p), tuple(q), widths[i], widths[i] * 0.95, skin, up=(0, 0, -1), ext=widths[i] * 0.5)
        d = (q - p) / np.linalg.norm(q - p)
        fwd = np.array([0.0, d[2], -d[1]])                                        # the throat's side of the link
        fwd = fwd / np.linalg.norm(fwd)
        CI.seg(bone, tuple(p - fwd * widths[i] * 0.45 + d * 0.5), tuple(q - fwd * widths[i] * 0.42 - d * 0.5), widths[i] * 0.62,
               1.0, belly, up=tuple(-fwd))
        m = (p + q) / 2 + fwd * widths[i] * 0.48
        CI.seg(bone, tuple(m), tuple(m + fwd * (4.6 - i * 0.5) + d * -1.5), 1.1, 2.4, spike, up=tuple(d))
    # ------------------------------------------------------------------------------------------------ the head
    A = np.array([0.0, -29.0, -35.0])
    k_ = 1.3                                                                          # the head a third larger
    S = lambda o: tuple(A + np.asarray(o, float) * k_)
    head = r.bone('head', bone, tuple(A), anim='head')
    CI.rbox(head, S((-5.5, -6, -10)), S((5.5, 3, 2)), skin, bevel=1.4 * k_)              # the skull
    CI.rbox(head, S((-4.2, -4, -28)), S((4.2, 1.5, -9)), skin, bevel=1.0 * k_)           # the snout
    CI.box(head, S((-2.2, -5, -26)), S((2.2, -4, -10)), plate)                          # the nose's plated ridge
    CI.chain_boxes(head, [S((0, -4.5, -24.5)), S((0, -7, -22.5)), S((0, -8.2, -20))], 1.6 * k_, 0.4 * k_, horn)
    CI.box(head, S((-3.9, 1.4, -27.5)), S((3.9, 1.5, -9)), mouth)                       # the palate
    for sx in (-1, 1):
        CI.box(head, S((sx * 1.7 - 0.5, -4.1, -27.6)), S((sx * 1.7 + 0.5, -3.6, -26.4)), M('simple', '#120c10'))
        CI.box(head, S((sx * 1.3, -7.6, -13)), S((sx * 6.2, -5.2, -4)), plate, rot=(-0.16, sx * 0.12, 0), pivot=S((sx * 3.8, -6.4, -8.5)))
        CI.eye(head, S((sx * 5.55, -2.6, -8)), 2.4 * k_, 1.2 * k_, 'left' if sx > 0 else 'right', eye_m)
        CI.chain_boxes(head, [S((sx * 3.4, -6, -0.5)), S((sx * 5, -11, 6)), S((sx * 5.8, -14, 13)), S((sx * 5.2, -15, 19.5))],
                       3.4 * k_, 0.7 * k_, horn)                                     # the great horns
        CI.chain_boxes(head, [S((sx * 5.2, -2.5, 0.5)), S((sx * 8.6, -4.5, 6)), S((sx * 10.2, -5.5, 10.5))], 2.0 * k_, 0.5 * k_, horn)
        CI.chain_boxes(head, [S((sx * 5.4, 1, -2)), S((sx * 8.4, 2, 2.5)), S((sx * 10, 3, 6))], 1.6 * k_, 0.4 * k_, horn)
        for j in range(3):
            CI.seg(head, S((sx * 4.8, -4 + j * 2.4, 1.8)), S((sx * 6.8, -3 + j * 2.6, 6)), 0.8 * k_, 1.4 * k_, spike, up=(0, 0, 1))
        a0, a1 = S((sx * 3.7, 1.5, -27)), S((sx * 3.7, 1.5, -11))
        CI.teeth(head, a0[0], a0[1], a0[2], a1[2], 7, 1.0 * k_, tooth, down=True)
    t0 = S((-3.4, 1.5, -27.6))
    CI.teeth_x(head, t0[2], t0[1], -3.4 * k_, 3.4 * k_, 4, 1.0 * k_, tooth, down=True)
    if crown is not None:
        for (dx, h, back) in ((0.0, 13.0, 4.0), (2.2, 11.0, 4.6), (-2.2, 11.0, 4.6), (4.2, 8.0, 5.2), (-4.2, 8.0, 5.2)):
            CI.chain_boxes(head, [S((dx, -5.5, -1)), S((dx * 1.2, -5.5 - h * 0.55, -1 + back * 0.6)), S((dx * 1.4, -5.5 - h, -1 + back))],
                           2.2 * k_, 0.5 * k_, crown)
    jaw = r.bone('jaw', head, S((0, 1.5, -1)), rot=(0.4, 0, 0), anim='jaw')
    CI.rbox(jaw, S((-4.0, 1.5, -26.5)), S((4.0, 4.5, -1)), belly, bevel=0.8 * k_)
    CI.box(jaw, S((-3.6, 1.45, -25.5)), S((3.6, 1.55, -2)), mouth)
    CI.seg(jaw, S((0, 1.2, -5)), S((0, 1.1, -19)), 2.6 * k_, 0.6 * k_, tongue, up=(0, -1, 0))
    for sx in (-1, 1):
        j0, j1 = S((sx * 3.3, 1.5, -25.5)), S((sx * 3.3, 1.5, -11))
        CI.teeth(jaw, j0[0], j0[1], j0[2], j1[2], 6, 0.9 * k_, tooth, down=False)
        CI.seg(jaw, S((sx * 3.6, 4.4, -5)), S((sx * 5.6, 6, -1)), 0.8 * k_, 1.2 * k_, spike, up=(0, 0, 1))
    t1 = S((0, 1.5, -26))
    CI.teeth_x(jaw, t1[2], t1[1], -3.0 * k_, 3.0 * k_, 3, 0.9 * k_, tooth, down=False)
    # ------------------------------------------------------------------------------------------------ the legs
    for sx in (-1, 1):
        sd = 'r' if sx < 0 else 'l'
        leg(r, body, 'leg_f' + sd, 'leg_r' if sx < 0 else 'leg_l',
            [(sx * 8.0, 4.0, -12.0), (sx * 10.0, 12.0, -9.0), (sx * 9.6, 18.5, -14.0), (sx * 9.6, 22.4, -15.0)], [6.0, 4.4, 3.4],
            skin, claw)
        leg(r, body, 'leg_b' + sd, 'leg_l' if sx < 0 else 'leg_r',
            [(sx * 7.6, 3.0, 17.0), (sx * 10.0, 11.0, 10.0), (sx * 9.6, 17.5, 20.0), (sx * 9.6, 22.4, 18.0)], [7.4, 5.0, 3.8],
            skin, claw)
    # ------------------------------------------------------------------------------------------------ the wings
    for sx in (-1, 1):
        f = 0.74
        wing(r, body, sx, (sx * 8.5, -8.0, -11.0), [(24.0 * f, 3.0 * f), (48.0 * f, 6.0 * f)],
             [(84.0 * f, 1.0 * f), (80.0 * f, 24.0 * f), (68.0 * f, 44.0 * f), (50.0 * f, 56.0 * f), (30.0 * f, 54.0 * f)], membrane,
             spar, claw, rot=(0.0, 0.5, 0.6), accent=accent, glow=wing_glow, ragged=ragged, shards=shards)
    # ------------------------------------------------------------------------------------------------ the tail
    p = np.array([0.0, 1.0, 23.0])
    bone = body
    n = 14
    for i in range(n):
        L = 6.2 - i * 0.2
        w = 7.4 * (1 - i / n) + 1.0
        bone = r.bone(f'tail{i + 1}', bone, tuple(p), anim='tail', i=i, amp=0.08, speed=0.05)
        ang = 0.12 * (1 - i / n) - 0.05 * (i / n)
        q = p + np.array([0.0, math.sin(ang) * L, math.cos(ang) * L])
        CI.seg(bone, tuple(p), tuple(q), w, w * 0.9, skin, up=(0, -1, 0), ext=w * 0.25)
        m = (p + q) / 2
        if i < n - 1:
            CI.seg(bone, tuple(m + (0, -w * 0.42, 0)), tuple(m + (0, -w * 0.42 - max(1.4, w * 0.55), L * 0.3)), max(0.6, w * 0.16),
                   max(1.0, w * 0.32), spike, up=(0, 0, 1))
            if fins is not None and i % 2 == 0:
                for sx in (-1, 1):
                    CI.seg(bone, tuple(m + (sx * w * 0.4, 0, 0)), tuple(m + (sx * (w * 0.4 + max(1.6, w * 0.7)), -0.6, 1.8)),
                           0.6, max(1.2, w * 0.4), fins, up=(0, -1, 0))
        p = q
    if tail_tip is not None:
        CI.cbox(bone, tuple(p + (0, 0, 2.0)), (1.0, 6.0, 4.6), tail_tip)
    r.height = 62.0                          # the renderer fits it to the hitbox: the skull's top, not the wings' tips
    return r


@recipe
def demiurgos():
    # 空創龍王 デミウルゴス: Ice and Fire's build with the user's sheet 22: black scales, gold horns, gold claws and gold
    # caps on the wing bones, a crown of gold horns, starry violet wings hung with crystals and ragged at the edge,
    # rainbow crystals down the back and the tail, a jewel in a gold frame on the chest, violet eyes.
    gold = '#d8b060'
    return iaf_dragon('demiurgos', M('scale', '#1c1a26', belly='#7a7690', scale_size=1.0, contrast=0.9),
                      M('scale', '#8a86a0', belly='#9a96b0', scale_size=1.4, contrast=0.5), M('scale', '#2a2638', belly='#2a2638'),
                      M('horn', gold, tip='#fff0b8'), M('gem', '#c8a8ff', glow=True), M('horn', gold, tip='#fff0b8'),
                      M('eye', '#c060ff', pupil='slit', mood='fierce', lid='#1c1a26'), '#2a1e48', M('horn', '#1e1a28', tip=gold),
                      accent='#a070ff', crown=M('horn', gold, tip='#fff0b8'), gems=['#ff6ad5', '#6af0ff', '#ffe46a', '#7dff8a'],
                      chest_gem=M('gem', '#c08cff', glow=True), ragged=True, shards=['#b48cff', '#6af0ff', '#ff6ad5'],
                      fins=M('gem', '#d8b8ff', glow=True), tail_tip=M('gem', '#ff6ad5', glow=True))


@recipe
def teia():
    # 光越天龍 テイア: Ice and Fire's build with the user's sheet 17: white armour scales trimmed in gold over a dark frame,
    # cyan light in the seams, wings of light hung with prism crystals, crystal spines, crest, claws and fins.
    return iaf_dragon('teia', M('metal', '#e4e8ee', accent='#d8b060'), M('metal', '#6a707c'), M('metal', '#c8b070'),
                      M('gem', '#9ff4ff', glow=True), M('gem', '#bff6ff', glow=True), M('gem', '#7ff0ff', glow=True),
                      M('eye', '#5ff0ff', pupil='ring', mood='happy', lid='#e4e8ee'), '#bfe8ff', M('metal', '#e4e8ee', accent='#d8b060'),
                      accent='#ffb8f0', wing_glow=True, crown=M('gem', '#bff6ff', glow=True),
                      shards=['#9ff4ff', '#e0b0ff', '#fff0a0'], fins=M('gem', '#c8f0ff', glow=True),
                      tail_tip=M('gem', '#9ff4ff', glow=True), seams=M('energy', '#6ff6ff', glow=True))

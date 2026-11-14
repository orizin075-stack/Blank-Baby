"""059g: OROR's two dragons and its earth dragon remade after the user's references (Ice and Fire's dragons, a black
dragon with a crown of horns, and a hulking stone beast with a maw full of teeth: "ドラゴンの子はこういうの参考に",
"クールマはこの子を参考に").

What the references have and creatures_ia.dragon (0.17.27) had not:
  * a long neck rising in an S (three links that sway one after another), the head carried high and forward;
  * a long head: skull, a snout as long again, brows that frown, teeth in both jaws, the jaw open;
  * wings far wider than the body (a span about three times its length), five finger spars and a membrane cut
    in scallops between them, raised as the dragon stands;
  * a deep chest over a narrower waist, legs that stand on their toes behind, claws;
  * a tail as long as the rest of the dragon, in nine links, spined all the way, a spade or a gem at its end;
  * a row of spines from the neck to the tail (and, for Demiurgos, the black dragon's crown of tall horns).
Kurma (嶺脈地龍, an earth dragon carrying a mountain range) is the stone beast: a hulking, high-shouldered body of
reddish rock hide, a great low head that is mostly jaw, rows of big white teeth above and below, small amber eyes
deep under heavy brow plates, pillar forelegs with claws, and on its back a ridge of stone plates that is the
mountain range of its legend: crags, moss and snow on the highest.

Model space as creatures_ia: pixels, y down (the ground is y = 24), the front is -z.
"""
import math
import numpy as np
from paint import M
import creatures_ia as CI

RECIPES = {}


def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn


def neck_chain(r, parent, pts, widths, mat, spikes=None, spike_h=1.6):
    """Links from pts[0] to pts[-1], each its own bone (they sway one after another), spined along the top."""
    bone = parent
    for i in range(len(pts) - 1):
        bone = r.bone(f'neck{i + 1}', bone, pts[i], anim='sway', ax=1, amp=0.03, speed=0.05, phase=0.7 * i)
        CI.seg(bone, pts[i], pts[i + 1], widths[i], widths[i] * 0.95, mat, up=(0, 0, -1), ext=widths[i] * 0.3)
        if spikes is not None:
            p, q = np.asarray(pts[i], float), np.asarray(pts[i + 1], float)
            m = (p + q) / 2
            d = q - p
            up = np.array([0.0, -d[2], d[1]])
            up = up / (np.linalg.norm(up) or 1)
            base = m + up * (widths[i] * 0.45)
            CI.seg(bone, tuple(base), tuple(base + up * spike_h - d / np.linalg.norm(d) * 0.8), 0.6, 1.1, spikes, up=(0, 0, 1))
    return bone


def if_wing(r, parent, side, shoulder, arm, fingers, membrane, spar, claw, rot, amp=0.24, speed=0.09, accent=None, glow=False,
            ragged=False, shards=None):
    """Ice and Fire's wing: a thick arm to the wrist, finger bones that run out past the membrane, a thumb claw, and a
    membrane cut deep between the fingers (scallops reaching halfway back to the wrist), ragged at the edge for a
    wild dragon; veins from the wrist, brush streaks."""
    sx = side
    b = r.bone('wing_r' if sx < 0 else 'wing_l', parent, shoulder, rot=(rot[0], rot[1] * sx, rot[2] * -sx), anim='sway', ax=2,
               amp=amp, speed=speed)
    x0, y, z0 = shoulder
    Pt = lambda xz: (x0 + sx * xz[0], y, z0 + xz[1])
    elbow, wrist = Pt(arm[0]), Pt(arm[1])
    CI.chain_boxes(b, [(x0, y, z0), elbow, wrist], 2.6, 1.5, spar)
    tips = [Pt(t) for t in fingers]
    for t in tips:
        d = np.subtract(t, wrist)
        ext = tuple(np.add(t, d / np.linalg.norm(d) * 2.6))
        CI.chain_boxes(b, [wrist, t, ext], 1.2, 0.35, spar)
    CI.seg(b, wrist, (wrist[0] + sx * 0.5, y - 0.6, wrist[2] - 2.6), 0.8, 0.8, claw)                  # the thumb claw
    body_end = Pt((1.6, fingers[-1][1] * 0.82))
    outline = [(x0, z0), (elbow[0], elbow[2]), (wrist[0], wrist[2])]
    scallops = []
    for i, t in enumerate(tips):
        outline.append((t[0], t[2]))
        n = tips[i + 1] if i + 1 < len(tips) else body_end
        mid = ((t[0] + n[0]) / 2, (t[2] + n[2]) / 2)
        dip = 0.4
        sc = (mid[0] * (1 - dip) + wrist[0] * dip, mid[1] * (1 - dip) + wrist[2] * dip)
        if ragged:
            q1 = (t[0] * 0.7 + sc[0] * 0.3 + sx * 0.6, t[2] * 0.7 + sc[1] * 0.3 + 0.8)
            q2 = (n[0] * 0.7 + sc[0] * 0.3 - sx * 0.4, n[2] * 0.7 + sc[1] * 0.3 - 0.6)
            outline += [q1, (q1[0] * 0.5 + sc[0] * 0.5 - sx * 0.8, q1[1] * 0.5 + sc[1] * 0.5 + 0.3), sc, q2]
        else:
            outline.append(sc)
        scallops.append(sc)
    outline.append((body_end[0], body_end[2]))
    veins = [(wrist[0], wrist[2], t[0], t[2]) for t in tips] + [(elbow[0], elbow[2], body_end[0], body_end[2])]
    veins += [(elbow[0], elbow[2], sc[0], sc[1]) for sc in scallops[-2:]]
    xs, zs = [p[0] for p in outline], [p[1] for p in outline]
    CI.box(b, (min(xs), y + 0.3, min(zs)), (max(xs), y + 0.3, max(zs)),
           M('wingskin', membrane, poly=outline, axes='xz', veins=veins, accent=accent, glow=glow, streaks=True))
    if shards:
        for k, sc in enumerate(scallops):
            CI.cbox(b, (sc[0], y + 1.2, sc[1]), (0.7, 2.4, 0.7), M('gem', shards[k % len(shards)], glow=True), rot=(0.2, 0.4, 0.1))
    return b


def side_spines(ends, mat, every=1, scale=1.0):
    """Spines out to both sides of a tail's links (the fins down an Ice and Fire tail)."""
    prev = None
    for i, (bone, q) in enumerate(ends):
        if prev is not None and i % every == 0 and i < len(ends) - 1:
            m = (np.asarray(prev) + np.asarray(q)) / 2
            w = max(0.8, 2.6 * (1 - i / len(ends))) * scale
            for sx in (-1, 1):
                CI.seg(bone, tuple(m + (sx * 0.4, 0, 0)), tuple(m + (sx * w * 1.4, -0.6, 1.4)), 0.5, 1.0, mat, up=(0, -1, 0))
        prev = q


def crown(head, at, s, mat):
    """The black dragon's crown: five tall horns fanning up and back from the back of the skull."""
    ax, ay, az = at
    for k, (dx, h, back) in enumerate(((0.0, 7.5, 2.0), (1.4, 6.6, 2.4), (-1.4, 6.6, 2.4), (2.7, 5.0, 2.8), (-2.7, 5.0, 2.8))):
        base = (dx * s, ay + 0.6 * s, az - 0.8 * s)
        mid = (dx * 1.25 * s, ay - h * 0.55 * s, az + back * 0.6 * s)
        tip = (dx * 1.45 * s, ay - h * s, az + back * s)
        CI.chain_boxes(head, [base, mid, tip], 1.3 * s, 0.35 * s, mat)


def if_dragon(key, skin, belly, horn, spike, eye_m, membrane, spar, accent=None, wing_glow=False, crown_mat=None, gems=None,
              seams=None, tail_tip=None, claw=None, ragged=False, shards=None, chest_gem=None, fins=None):
    r = CI.rig(key)
    mouth = M('mouth', '#4a1220')
    tooth = M('tooth', '#efe6d2')
    claw = claw or M('horn', '#d8cfb8')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    # the chest raised, as Ice and Fire's dragons stand
    body = r.bone('body', root, (0, 12.5, 2), rot=(-0.14, 0, 0), anim='breath')
    # a deep chest, a narrower waist, the hips
    CI.rbox(body, (-5.2, 6.4, -11.5), (5.2, 17.0, -1.0), skin, bevel=1.3)
    CI.rbox(body, (-4.4, 7.6, -1.5), (4.4, 16.2, 9.0), skin, bevel=1.1)
    CI.rbox(body, (-4.0, 8.2, 8.5), (4.0, 15.4, 14.0), skin, bevel=1.0)
    CI.box(body, (-3.9, 17.0, -10.5), (3.9, 17.6, 8.5), belly)                          # belly plates
    CI.box(body, (-3.2, 16.2, 8.5), (3.2, 16.8, 13.5), belly)
    CI.spikes_row(body, -10.5, 13.0, 9, 6.4, 2.6, 1.3, spike, w=0.9, lean=0.7)
    if seams:
        for sx in (-1, 1):                                                              # the machine's light seams
            CI.box(body, (sx * 5.22, 10.0, -10.0), (sx * 5.3, 10.4, -1.5), seams)
            CI.box(body, (sx * 4.42, 10.6, -1.0), (sx * 4.5, 11.0, 8.5), seams)
            CI.cbox(body, (sx * 1.6, 7.3, 5.0), (1.2, 0.3, 4.0), seams)                 # thrusters on the back
    if gems:
        for i, (x, y, z, sz) in enumerate(((-5.25, 10.5, -7.0, 1.5), (5.25, 10.5, -7.0, 1.5), (-4.45, 12.0, 3.0, 1.1),
                                            (4.45, 12.0, 3.0, 1.1), (0, 6.2, -4.0, 1.3), (0, 7.4, 5.0, 1.1))):
            CI.cbox(body, (x, y, z), (sz, sz, sz), M('gem', gems[i % len(gems)], glow=True), rot=(0.3, 0.6, 0.2))
    # the neck in an S, up and forward, then the long head
    neck = neck_chain(r, body, [(0, 9.4, -10.5), (0, 5.2, -14.2), (0, 0.8, -16.6), (0, -2.6, -19.6)], [5.0, 4.3, 3.7], skin,
                      spikes=spike)
    head, jaw = CI.dragon_head(r, neck, (0, -5.2, -19.0), 1.05, skin, belly, eye_m, horn, mouth, tooth, brow=skin, open_jaw=0.3,
                               horns='swept')
    if crown_mat is not None:
        crown(head, (0, -5.2, -19.0), 1.05, crown_mat)
    # legs: the front ones under the chest, the hind ones on their toes
    for sx in (-1, 1):
        side = 'r' if sx < 0 else 'l'
        CI.leg(r, body, 'leg_f' + side, 'leg_r' if sx < 0 else 'leg_l', (sx * 4.8, 13.6, -6.8), (sx * 5.6, 18.6, -8.4),
               (sx * 5.2, 22.6, -6.6), 3.0, 2.2, skin, foot=(2.8, 1.4, 3.4), claw=claw)
        CI.leg(r, body, 'leg_b' + side, 'leg_l' if sx < 0 else 'leg_r', (sx * 4.4, 12.8, 10.2), (sx * 5.4, 17.2, 6.4),
               (sx * 5.0, 22.6, 11.8), 3.8, 2.4, skin, foot=(3.0, 1.4, 3.6), claw=claw)
    # the great wings: five fingers, a span three times the body
    for sx in (-1, 1):
        if_wing(r, body, sx, (sx * 4.8, 7.6, -6.4), [(12.0, 2.0), (24.0, 4.0)],
                [(41.0, 3.0), (39.0, 13.0), (33.0, 22.0), (24.0, 28.0), (13.5, 27.0)], membrane, spar, claw,
                rot=(0.0, 0.3, 0.86), amp=0.24, speed=0.09, accent=accent, glow=wing_glow, ragged=ragged, shards=shards)
    if chest_gem is not None:
        CI.cbox(body, (0, 12.0, -11.7), (2.6, 3.2, 0.8), chest_gem, rot=(0, 0, 0.785))
        CI.cbox(body, (0, 12.0, -11.5), (3.6, 4.2, 0.4), M('metal', '#d8b060'), rot=(0, 0, 0.785))
    # the tail: as long as the rest, spined to its end
    ends = CI.tail(r, body, (0, 11.8, 13.6), [5.6, 5.4, 5.2, 5.0, 4.8, 4.4, 4.0, 3.6, 3.2],
                   [4.4, 3.9, 3.4, 2.9, 2.5, 2.1, 1.7, 1.3, 1.0], skin, droop=0.1, lift=0.06, spikes=spike, amp=0.1, speed=0.06)
    if fins is not None:
        side_spines(ends, fins)
    tip_bone, (tx, ty, tz) = ends[-1]
    if tail_tip is not None:
        CI.cbox(tip_bone, (tx, ty, tz + 1.4), (0.6, 3.8, 3.0), tail_tip, rot=(0.0, 0.0, 0.0))
    # the renderer fits `height` to the mob's hitbox: the head's top, not the raised wings' tips
    r.height = 29.5
    return r


@recipe
def demiurgos():
    # 空創龍王 デミウルゴス (the user's sheet 22 and the Ice and Fire photos): a black dragon, gold horns, gold claws and
    # gold caps on the wing bones; wings like a starry night, violet to the edge, crystals hanging from it; rainbow
    # crystals down the back and the tail; a great jewel in a gold frame on the chest; violet eyes; a ragged edge.
    skin = M('scale', '#1c1a26', belly='#8e8aa0', scale_size=1.2, contrast=0.85)
    belly = M('scale', '#8e8aa0', belly='#a8a4b8', scale_size=1.6, contrast=0.5)
    gold = '#d8b060'
    horn = M('horn', gold, tip='#fff0b8', glow=False)
    spike = M('gem', '#c8a8ff', glow=True)
    eye_m = M('eye', '#c060ff', pupil='slit', mood='fierce', lid='#1c1a26')
    return if_dragon('demiurgos', skin, belly, horn, spike, eye_m, '#2a1e48', M('horn', '#1e1a28', tip=gold), accent='#a070ff',
                     crown_mat=M('horn', gold, tip='#fff0b8'), gems=['#ff6ad5', '#6af0ff', '#ffe46a', '#7dff8a', '#a07dff'],
                     tail_tip=M('gem', '#ff6ad5', glow=True), claw=M('horn', gold), ragged=True,
                     shards=['#b48cff', '#6af0ff', '#ff6ad5'], chest_gem=M('gem', '#c08cff', glow=True),
                     fins=M('gem', '#d8b8ff', glow=True))


@recipe
def teia():
    # 光越天龍 テイア (the user's sheet 17 and the Ice and Fire photos): a slender dragon of white armour plates trimmed in
    # gold over a dark frame, cyan light in the joints, wings of prism-crystal blades, a crest of crystals, cyan crystal
    # claws, a fan of crystal blades at the tail's end.
    skin = M('metal', '#e4e8ee', accent='#d8b060')
    belly = M('metal', '#6a707c')
    horn = M('gem', '#9ff4ff', glow=True)
    spike = M('gem', '#bff6ff', glow=True)
    eye_m = M('eye', '#5ff0ff', pupil='ring', mood='happy', lid='#e4e8ee')
    return if_dragon('teia', skin, belly, horn, spike, eye_m, '#bfe8ff', M('metal', '#e4e8ee', accent='#d8b060'),
                     accent='#ffb8f0', wing_glow=True, seams=M('energy', '#6ff6ff', glow=True),
                     tail_tip=M('gem', '#9ff4ff', glow=True), claw=M('gem', '#7ff0ff', glow=True),
                     shards=['#9ff4ff', '#e0b0ff', '#fff0a0'], crown_mat=M('gem', '#bff6ff', glow=True),
                     fins=M('gem', '#c8f0ff', glow=True))


@recipe
def kurma():
    # 嶺脈地龍 クールマ: an earth dragon carrying a mountain range. The user's reference: a hulking stone beast, high
    # shoulders, a low head that is mostly jaw, rows of big white teeth, small eyes under heavy brows, reddish rock
    # hide with darker plates. The range of its legend is the ridge of stone plates on its back (crags, moss, snow).
    r = CI.rig('kurma')
    # the lore's hide: obsidian and granite, worn by weather, moss and grass in its cracks; green light in the seams
    hide = M('scale', '#5c5a52', belly='#c8b89a', scale_size=1.8, contrast=0.75)
    plate = M('rock', '#7e786c')
    crag = M('rock', '#8a8478')
    moss = M('leaf', '#5a8a3a')
    snow = M('simple', '#eef2f4')
    tooth = M('tooth', '#f2ead8')
    mouth = M('mouth', '#5a1a1a')
    claw = M('rock', '#d8d0bc')
    vein = M('energy', '#5effa8', glow=True)
    water = M('energy', '#8fd8ff', glow=False)
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 12.0, 0), anim='breath')
    # a hulking body: the shoulders high and massive, the back sloping down to the hips
    CI.rbox(body, (-12.5, 1.5, -15.0), (12.5, 17.0, 1.5), hide, bevel=2.6)
    CI.rbox(body, (-10.5, 4.8, 0.5), (10.5, 16.2, 14.5), hide, bevel=2.2)
    CI.rbox(body, (-9.5, 16.0, -13.0), (9.5, 17.6, 12.0), M('scale', '#c8b89a', belly='#c8b89a', scale_size=2.0))
    for sx in (-1, 1):                                                                   # the green seams of its veins
        CI.box(body, (sx * 12.55, 8.0, -12.0), (sx * 12.65, 8.5, -2.0), vein)
        CI.box(body, (sx * 10.55, 9.5, 2.0), (sx * 10.65, 10.0, 12.0), vein)
    # the mountain range on its back: a shelf of earth and moss, peaks of grey stone with snow, a forest, a lake and
    # a waterfall over the flank
    CI.box(body, (-11.0, -0.2, -13.5), (11.0, 2.0, 13.0), M('leaf', '#4f7a34'))
    CI.box(body, (-10.5, 1.8, -13.0), (10.5, 3.0, 12.5), M('rock', '#6a5a44'))
    for (x, z, w, h) in ((-3.0, -6.0, 8.0, 15.0), (4.5, -1.0, 6.5, 11.0), (-5.5, 6.0, 5.5, 8.0), (5.0, 8.5, 4.5, 6.0)):
        for k in range(4):
            t = k / 4
            hw = w * (1 - t * 0.75)
            y0, y1 = -0.2 - h * t, -0.2 - h * (t + 0.25)
            CI.box(body, (x - hw, y1, z - hw), (x + hw, y0, z + hw), crag)
            if k == 0:
                CI.box(body, (x - hw - 0.3, y0 - 1.0, z - hw - 0.3), (x + hw + 0.3, y0, z + hw + 0.3), moss)
        CI.box(body, (x - w * 0.22, -0.2 - h - 1.0, z - w * 0.22), (x + w * 0.22, -0.2 - h * 0.78, z + w * 0.22), snow)
    for (x, z) in ((-9.0, -10.0), (9.0, -9.0), (-9.5, 2.0), (9.5, 4.0), (0.5, 11.0), (-8.5, 10.5), (8.5, 12.0), (1.0, 4.0)):
        CI.box(body, (x - 0.4, -2.2, z - 0.4), (x + 0.4, -0.2, z + 0.4), M('wood', '#5a3e24'))     # spruces
        CI.box(body, (x - 1.4, -4.2, z - 1.4), (x + 1.4, -2.2, z + 1.4), M('leaf', '#2f5a2e'))
        CI.box(body, (x - 0.8, -5.8, z - 0.8), (x + 0.8, -4.2, z + 0.8), M('leaf', '#356a34'))
    CI.box(body, (1.0, -0.4, 2.0), (6.0, -0.1, 6.5), water)                                       # the lake
    CI.box(body, (10.4, -0.1, 3.0), (10.9, 9.0, 5.5), water)                                      # its waterfall
    # the head: low and forward, a great maw
    neck = r.bone('neck', body, (0, 8.0, -14.0), anim='sway', ax=1, amp=0.03, speed=0.04)
    CI.rbox(neck, (-7.5, 3.5, -20.5), (7.5, 15.5, -12.5), hide, bevel=1.8)
    head = r.bone('head', neck, (0, 9.0, -20.0), anim='head')
    CI.rbox(head, (-8.5, 2.6, -35.0), (8.5, 11.6, -19.0), hide, bevel=1.8)
    CI.box(head, (-7.4, 11.5, -34.2), (7.4, 11.6, -20.0), mouth)                         # the palate
    for sx in (-1, 1):
        # heavy brow plates, frowning down to the front
        CI.box(head, (sx * 1.5, 1.6, -31.5), (sx * 8.9, 4.2, -23.0), plate, rot=(-0.16, 0, sx * 0.08), pivot=(sx * 5.0, 2.9, -27.0))
        CI.eye(head, (sx * 8.55, 6.4, -27.0), 2.4, 1.4, 'left' if sx > 0 else 'right',
               M('eye', '#ffb040', pupil='slit', mood='fierce', lid='#5a3a2a', glow_amount=0.7))
        CI.box(head, (sx * 2.6 - 0.6, 2.5, -34.4), (sx * 2.6 + 0.6, 2.7, -33.0), M('simple', '#1a1410'))   # nostrils
        CI.teeth(head, sx * 7.4, 11.6, -33.8, -21.0, 6, 1.4, tooth, down=True)
        # cheek plates behind the jaw's hinge
        CI.box(head, (sx * 8.4, 5.0, -22.5), (sx * 9.6, 12.0, -18.5), plate)
    CI.teeth_x(head, -34.2, 11.6, -6.8, 6.8, 7, 1.5, tooth, down=True)
    jaw = r.bone('jaw', head, (0, 11.6, -20.0), rot=(0.34, 0, 0), anim='jaw')
    CI.rbox(jaw, (-7.9, 11.6, -34.4), (7.9, 16.6, -19.6), M('scale', '#66625a', belly='#c8b89a', scale_size=1.8), bevel=1.3)
    CI.box(jaw, (-7.0, 11.55, -33.6), (7.0, 11.65, -20.4), mouth)                        # the tongue's bed
    for sx in (-1, 1):
        CI.teeth(jaw, sx * 7.0, 11.6, -33.4, -21.5, 6, 1.3, tooth, down=False)
        # two tusks up from the jaw's front corners
        CI.chain_boxes(jaw, [(sx * 6.2, 12.2, -33.6), (sx * 6.6, 9.2, -34.6), (sx * 6.3, 7.4, -34.2)], 1.6, 0.6, tooth)
    CI.teeth_x(jaw, -33.8, 11.6, -5.6, 5.6, 6, 1.4, tooth, down=False)
    CI.box(jaw, (-6.0, 16.6, -33.0), (6.0, 18.0, -24.0), plate)                          # the chin's plate
    # pillar forelegs with stone bracers, shorter hind legs
    for sx in (-1, 1):
        side = 'r' if sx < 0 else 'l'
        up, low = CI.leg(r, body, 'leg_f' + side, 'leg_r' if sx < 0 else 'leg_l', (sx * 11.2, 7.5, -8.5), (sx * 13.2, 15.4, -10.5),
                         (sx * 12.4, 22.2, -9.4), 7.2, 6.0, hide, foot=(7.6, 3.2, 7.2), claw=claw, toes=3)
        CI.box(low, (sx * 12.8 - 3.6, 16.0, -13.0), (sx * 12.8 + 3.6, 19.5, -6.5), plate)
        CI.leg(r, body, 'leg_b' + side, 'leg_l' if sx < 0 else 'leg_r', (sx * 9.4, 11.5, 9.5), (sx * 10.4, 17.2, 7.4),
               (sx * 9.8, 22.6, 10.0), 6.2, 4.8, hide, foot=(6.2, 2.6, 5.8), claw=claw, toes=3)
    CI.tail(r, body, (0, 10.5, 14.0), [5.0, 4.6, 4.2, 3.6], [6.2, 5.0, 3.8, 2.6], hide, droop=0.3, spikes=plate, amp=0.08,
            speed=0.04)
    r.height = 37.2                                  # as before: the range's peaks may rise over the hitbox
    return r

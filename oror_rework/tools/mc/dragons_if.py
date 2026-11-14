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


def crown(head, at, s, mat):
    """The black dragon's crown: five tall horns fanning up and back from the back of the skull."""
    ax, ay, az = at
    for k, (dx, h, back) in enumerate(((0.0, 7.5, 2.0), (1.4, 6.6, 2.4), (-1.4, 6.6, 2.4), (2.7, 5.0, 2.8), (-2.7, 5.0, 2.8))):
        base = (dx * s, ay + 0.6 * s, az - 0.8 * s)
        mid = (dx * 1.25 * s, ay - h * 0.55 * s, az + back * 0.6 * s)
        tip = (dx * 1.45 * s, ay - h * s, az + back * s)
        CI.chain_boxes(head, [base, mid, tip], 1.3 * s, 0.35 * s, mat)


def if_dragon(key, skin, belly, horn, spike, eye_m, membrane, spar, accent=None, wing_glow=False, crown_mat=None, gems=None,
              seams=None, tail_tip=None):
    r = CI.rig(key)
    mouth = M('mouth', '#4a1220')
    tooth = M('tooth', '#efe6d2')
    claw = M('horn', '#d8cfb8')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 12.5, 2), anim='breath')
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
        CI.wing(r, body, sx, (sx * 4.8, 7.8, -6.2), [(11.0, 1.5), (22.0, 5.0)],
                [(38.0, 6.0), (35.0, 15.5), (29.0, 23.5), (20.5, 27.5), (11.5, 25.0)], membrane, spar, rot=(0.0, 0.14, 0.72),
                amp=0.26, speed=0.09, accent=accent, glow=wing_glow)
    # the tail: as long as the rest, spined to its end
    ends = CI.tail(r, body, (0, 11.8, 13.6), [5.6, 5.4, 5.2, 5.0, 4.8, 4.4, 4.0, 3.6, 3.2],
                   [4.4, 3.9, 3.4, 2.9, 2.5, 2.1, 1.7, 1.3, 1.0], skin, droop=0.1, lift=0.06, spikes=spike, amp=0.1, speed=0.06)
    tip_bone, (tx, ty, tz) = ends[-1]
    if tail_tip is not None:
        CI.cbox(tip_bone, (tx, ty, tz + 1.4), (0.6, 3.8, 3.0), tail_tip, rot=(0.0, 0.0, 0.0))
    return r


@recipe
def demiurgos():
    # 空創龍王 デミウルゴス: a small black dragon (about five metres) set with rainbow gems; mysterious more than
    # menacing. The black dragon of the user's reference: a crown of tall horns, black scales, a red maw; here the
    # horns and spines are amethyst-tipped and the gems rainbow, the eyes amethyst under heavy brows.
    skin = M('scale', '#201e2b', belly='#3e3656', scale_size=1.2, contrast=0.8)
    belly = M('scale', '#3e3656', belly='#3e3656', scale_size=1.6, contrast=0.5)
    horn = M('horn', '#2a2638', tip='#b48cff', glow=True)
    spike = M('horn', '#2e2a3c', tip='#c8a8ff', glow=True)
    crown_mat = M('gem', '#d8c8ff', glow=True)
    eye_m = M('eye', '#c58cff', pupil='slit', mood='fierce', lid='#201e2b')
    return if_dragon('demiurgos', skin, belly, horn, spike, eye_m, '#2a2036', M('horn', '#2a2638'), accent='#8f6ad8',
                     crown_mat=crown_mat, gems=['#ff6ad5', '#6af0ff', '#ffe46a', '#7dff8a', '#a07dff'],
                     tail_tip=M('gem', '#ff6ad5', glow=True))


@recipe
def teia():
    # 光越天龍 テイア: a small dragon fused with machinery: a pale metal shell with cyan light seams, photon wings,
    # thrusters on the back; cheerful big brother: bright eyes. Its wings are the crystal dragon's of the references
    # (light through panes), its spines crystal.
    skin = M('metal', '#c9d2dc', accent='#6ff6ff')
    belly = M('metal', '#8c99a8')
    horn = M('horn', '#e8eef4', tip='#6ff6ff', glow=True)
    spike = M('gem', '#bff6ff', glow=True)
    eye_m = M('eye', '#7ff6ff', pupil='ring', mood='happy', lid='#c9d2dc')
    return if_dragon('teia', skin, belly, horn, spike, eye_m, '#bfe8ff', M('metal', '#c9d2dc', accent='#6ff6ff'),
                     accent='#ff9af2', wing_glow=True, seams=M('energy', '#6ff6ff', glow=True),
                     tail_tip=M('energy', '#6ff6ff', glow=True))


@recipe
def kurma():
    # 嶺脈地龍 クールマ: an earth dragon carrying a mountain range. The user's reference: a hulking stone beast, high
    # shoulders, a low head that is mostly jaw, rows of big white teeth, small eyes under heavy brows, reddish rock
    # hide with darker plates. The range of its legend is the ridge of stone plates on its back (crags, moss, snow).
    r = CI.rig('kurma')
    hide = M('scale', '#8a5c42', belly='#b98a62', scale_size=1.8, contrast=0.7)
    plate = M('rock', '#6a4836')
    crag = M('rock', '#7e766a')
    moss = M('leaf', '#5a8a3a')
    snow = M('simple', '#eef2f4')
    tooth = M('tooth', '#f2ead8')
    mouth = M('mouth', '#5a1a1a')
    claw = M('horn', '#e2d6bc')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 12.0, 0), anim='breath')
    # a hulking body: the shoulders high and massive, the back sloping down to the hips
    CI.rbox(body, (-12.5, 1.5, -15.0), (12.5, 17.0, 1.5), hide, bevel=2.6)
    CI.rbox(body, (-10.5, 4.8, 0.5), (10.5, 16.2, 14.5), hide, bevel=2.2)
    CI.rbox(body, (-9.5, 16.0, -13.0), (9.5, 17.6, 12.0), M('scale', '#b98a62', belly='#b98a62', scale_size=2.0))
    # the ridge of stone plates down the back: the mountain range
    ridge = [(-12.5, 1.5, 6.5, 6.0), (-7.0, 0.8, 7.5, 8.0), (-1.5, 1.2, 7.0, 7.0), (4.0, 3.0, 6.0, 5.5), (9.0, 4.6, 5.0, 4.0),
             (13.0, 5.6, 3.8, 3.0)]
    for i, (z, y, w, h) in enumerate(ridge):
        CI.box(body, (-w / 2, y - h, z - 2.2), (w / 2, y + 0.6, z + 2.2), plate, rot=(0.25, 0, 0), pivot=(0, y, z))
        if h >= 6.0:
            # a crag on the plate: grey stone stepping up, moss on its shoulder, snow on the peak
            CI.box(body, (-w / 3, y - h - 2.4, z - 1.4), (w / 3, y - h + 0.4, z + 1.4), crag)
            CI.box(body, (-w / 3 - 0.3, y - h - 0.2, z - 1.6), (w / 3 + 0.3, y - h + 0.4, z + 1.6), moss)
            CI.box(body, (-w / 6, y - h - 3.6, z - 0.8), (w / 6, y - h - 2.2, z + 0.8), snow)
    for sx in (-1, 1):
        for z, y, s in ((-10.0, 4.5, 4.5), (-3.0, 3.5, 4.0), (5.0, 6.5, 3.5)):          # side plates over the flanks
            CI.box(body, (sx * 10.5 - 1.0, y, z - s / 2), (sx * 12.9, y + s, z + s / 2), plate, rot=(0, 0, sx * 0.35),
                   pivot=(sx * 11.5, y, z))
    # trees in the moss of the lower plates
    for x, z in ((-3.5, 4.0), (3.0, 9.0)):
        CI.box(body, (x - 0.5, -0.8, z - 0.5), (x + 0.5, 2.4, z + 0.5), M('wood', '#6a4a2a'))
        CI.box(body, (x - 1.5, -3.8, z - 1.5), (x + 1.5, -0.6, z + 1.5), M('leaf', '#3f7f3a'))
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
    CI.rbox(jaw, (-7.9, 11.6, -34.4), (7.9, 16.6, -19.6), M('scale', '#9a6a4c', belly='#b98a62', scale_size=1.8), bevel=1.3)
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
    return r

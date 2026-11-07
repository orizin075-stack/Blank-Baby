"""(054) The villager king's three later forms as Blockbench-style rigs (build_bb recipes), drawn by RoyalRenderer's
KingFormRenderer through RigModel in place of the villager king's own small model.

  hero    英雄王 — back from his first death as the hero of a tale: a towering knight in white-silver plate edged with
          gold, a great helm with a crown fused to its brow, a glowing visor and a white plume, a sun on the breast,
          a royal-blue tabard and cape, a holy greatsword with a burning fuller and a tower shield bearing the sun.
  broken  崩壊王 — the hero's form coming apart like a model whose data has gone wrong: plates slid out of place,
          pieces gone to the missing texture, an arm of error blocks with too many joints, the greatsword in floating
          pieces, the shield shattered round him, pixels drifting off him, eyes red and cyan.
  divine  バアル＝ゼブル — the broken shell fallen away, a god: white and gold robes to the ground over a gold
          breastplate, a horned crown of the storm god, a sun-disc halo of rays behind his head and a second ring
          turning about it, an upper pair of great wings of light and a lower pair of glassy veined wings (the lord of
          the flies made holy), the two clubs Yagrush and Aymur in his hands, lightning glyphs circling him.

Built on the 'large' template (44 px tall); RoyalRenderer scales them to the king's hitbox, which grows with each
form (KingForms.strengthen: the scale attribute).
"""
import math
import numpy as np
from rig import Rig
from paint import M
from figure import Humanoid, wing, orbiters
import bb
import sculpt as SC
import trinkets as TK
import bbpaint as BP
import king_arms as KA
from figure_bb import box, cbox

RECIPES = {}


def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn


# ------------------------------------------------------------------------------------------------------- palette
SILVER = '#dfe5ef'
SILVER_D = '#a9b2c4'
STEEL = '#6f788c'
GOLD = '#e8b640'
GOLD_L = '#ffe9a6'
ROYAL = '#21409a'
ROYAL_D = '#152a66'
IVORY = '#f4f1e8'
SWORD_TILT = -1.15
SKY = '#9fe0ff'


def mats_hero():
    return dict(
        plate=M('metal', SILVER, accent=GOLD, pattern='filigree'),
        plate2=M('metal', SILVER),
        plate_d=M('metal', SILVER_D),
        steel=M('metal', STEEL),
        gold=M('metal', GOLD, accent=GOLD_L, pattern='gold_lines'),
        gold2=M('metal', GOLD),
        tabard=M('cloth', ROYAL, accent=GOLD, trim=2, pattern='cross'),
        cape=M('cloth', ROYAL, accent=GOLD, trim=2, pattern='embroidery'),
        lining=M('cloth', ROYAL_D),
        plume=M('cloth', '#ffffff', accent='#dfe6f2', pattern='stripes'),
        fur=M('fur', IVORY),
        glow=M('energy', SKY),
        sun=M('gem', '#ff3a1a', glow=True),
        gem=M('gem', '#6cb8ff', glow=True),
        blade=M('metal', '#c9d2e0'),
        edge=M('metal', '#f2f6fc'),
        fuller=M('metal', GOLD, accent='#fff6c8', pattern='runes', pattern_glow=True, glow_amount=0.55),
        leather=M('cloth', '#4a3426'),
    )


# ------------------------------------------------------------------------------------------------------- pieces
def sun_disc(bone, c, r, gold, core, rays=8, normal_z=-1.0, ray_len=None, depth=0.4):
    """A raised sun: a disc, a ring of rays, a glowing core; on a face looking along z."""
    x, y, z = c
    rl = ray_len or r * 0.9
    bb.ccube(bone, (x, y, z), (r * 1.6, r * 1.6, depth), gold, name='sun_disc')
    bb.ccube(bone, (x, y, z), (r * 1.1, r * 2.1, depth * 0.8), gold, name='sun_disc2')
    bb.ccube(bone, (x, y, z), (r * 2.1, r * 1.1, depth * 0.8), gold, name='sun_disc3')
    for i in range(rays):
        a = 2 * math.pi * i / rays + math.pi / rays
        L = rl * (1.0 if i % 2 == 0 else 0.7)
        cx, cy = x + math.cos(a) * (r + L / 2), y + math.sin(a) * (r + L / 2)
        bb.ccube(bone, (cx, cy, z + 0.05 * normal_z), (L, 0.45, depth * 0.7), gold, rot=(0, 0, a), name='sun_ray')
    bb.ccube(bone, (x, y, z + normal_z * depth * 0.6), (r * 0.8, r * 0.8, depth * 0.6), core, name='sun_core')


def pauldron(h, arm, sgn, P, tiers=3, spikes=3, big=1.0):
    """Layered plate over the shoulder: a dome with a gold rim and spikes, two lames below it, each tilted out."""
    aw, ad = h.T['arm']
    x = arm.pivot[0]
    y = h.top
    pb = h.rig.bone(arm.name + '_pauldron', arm, (x, y, 0), rot=(0, 0, sgn * -0.22))
    W, D = (aw + 3.6) * big, (ad + 3.4) * big
    cx = x + sgn * 0.6
    bb.ccube(pb, (cx, y - 0.6, 0), (W, 2.6, D), P['plate'], name='pauldron_dome')
    bb.ccube(pb, (cx, y - 1.95, 0), (W - 1.6, 0.8, D - 1.6), P['plate2'], name='pauldron_cap')
    for f in (-1, 1):
        bb.ccube(pb, (cx, y + 0.55, f * (D / 2 + 0.05)), (W + 0.2, 0.7, 0.3), P['gold2'], name='pauldron_rim')
    bb.ccube(pb, (cx + sgn * (W / 2 + 0.05), y + 0.55, 0), (0.3, 0.7, D + 0.2), P['gold2'], name='pauldron_rim')
    for k in range(1, tiers):
        yy = y + 0.9 + k * 1.35
        ww = W - k * 0.7
        bb.ccube(pb, (cx + sgn * k * 0.45, yy, 0), (ww, 1.4, D - k * 0.6), P['plate'] if k % 2 else P['plate_d'],
                 rot=(0, 0, sgn * -0.12 * k), pivot=(cx, yy, 0), name='pauldron_lame')
        bb.ccube(pb, (cx + sgn * k * 0.45, yy + 0.62, 0), (ww + 0.2, 0.3, D - k * 0.6 + 0.2), P['gold2'],
                 rot=(0, 0, sgn * -0.12 * k), pivot=(cx, yy, 0), name='pauldron_lame_rim')
    for i in range(spikes):
        zz = (i - (spikes - 1) / 2) * (D / (spikes + 0.5))
        L = 2.2 + (0.8 if i == spikes // 2 else 0)
        bb.ccube(pb, (cx + sgn * 0.8, y - 1.9 - L / 2, zz), (0.9, L, 0.9), P['gold2'], rot=(0, 0, sgn * 0.35),
                 pivot=(cx, y - 1.9, zz), name='pauldron_spike')
        bb.ccube(pb, (cx + sgn * 1.0, y - 2.0 - L, zz), (0.5, 0.9, 0.5), P['gold2'], rot=(0, 0, sgn * 0.5),
                 pivot=(cx, y - 1.9, zz), name='pauldron_spike_tip')
    bb.ccube(pb, (cx + sgn * (W / 2 + 0.25), y - 0.4, 0), (0.4, 1.4, 1.4), P['gem'], name='pauldron_gem')
    return pb


def limb_armour(h, P, broken=None):
    """Couters, vambraces, gauntlets; cuisses, poleyns, greaves, sabatons."""
    aw, ad = h.T['arm']
    parts = []
    for fore, sgn in ((h.fore_r, -1), (h.fore_l, 1)):
        x = fore.pivot[0]
        parts.append(bb.ccube(fore, (x, h.elbow_y + 0.3, 0), (aw + 1.2, 2.0, ad + 1.2), P['gold2'], name='couter'))
        parts.append(bb.ccube(fore, (x + sgn * (aw / 2 + 0.5), h.elbow_y + 0.3, 0.3), (0.5, 2.8, 2.8), P['plate'],
                              rot=(0.6, 0, 0), name='couter_fan'))
        parts.append(bb.ccube(fore, (x, h.elbow_y + 3.6, 0), (aw + 0.8, 4.4, ad + 0.8), P['plate'], name='vambrace'))
        parts.append(bb.ccube(fore, (x, h.wrist_y - 0.2, 0), (aw + 1.4, 0.9, ad + 1.4), P['gold2'], name='gauntlet_cuff'))
        parts.append(bb.ccube(fore, (x, h.wrist_y + 1.3, -0.1), (aw + 0.5, 2.6, ad + 0.6), P['steel'], name='gauntlet'))
        for k in range(3):
            parts.append(bb.ccube(fore, (x - 1.2 + k * 1.2, h.wrist_y + 2.4, -ad / 2 - 0.25), (0.9, 1.2, 0.5), P['plate_d'],
                                  name='knuckle'))
    for leg, shin, sgn in ((h.leg_r, h.shin_r, -1), (h.leg_l, h.shin_l, 1)):
        x = leg.pivot[0]
        parts.append(bb.ccube(leg, (x, (h.hip_y + h.knee_y) / 2 + 0.6, 0), (5.8, h.knee_y - h.hip_y - 1.0, 5.8), P['plate2'],
                              name='cuisse'))
        parts.append(bb.ccube(leg, (x, h.knee_y - 2.0, -3.0), (5.0, 1.0, 0.4), P['gold2'], name='cuisse_rim'))
        parts.append(bb.ccube(shin, (x, h.knee_y + 0.6, -2.9), (4.0, 3.4, 1.3), P['gold'], name='poleyn'))
        parts.append(bb.ccube(shin, (x + sgn * 2.4, h.knee_y + 0.6, -1.6), (0.5, 3.0, 3.0), P['plate'], rot=(0.5, 0, 0),
                              name='poleyn_wing'))
        parts.append(bb.ccube(shin, (x, h.knee_y - 0.6, -3.7), (0.7, 1.6, 0.7), P['gold2'], rot=(-0.6, 0, 0), name='poleyn_spike'))
        g0, g1 = h.knee_y + 2.4, h.ankle_y - 0.4
        parts.append(bb.ccube(shin, (x, (g0 + g1) / 2, 0), (5.4, g1 - g0, 5.4), P['plate2'], name='greave'))
        parts.append(bb.ccube(shin, (x, (g0 + g1) / 2, -2.75), (1.0, g1 - g0 - 1.0, 0.3), P['gold2'], name='greave_ridge'))
        parts.append(bb.ccube(shin, (x, g1 - 0.4, 0), (5.8, 0.8, 5.8), P['gold2'], name='greave_rim'))
        parts.append(bb.ccube(shin, (x, h.ankle_y + 0.3, -1.3), (5.4, 1.6, 7.4), P['plate_d'], name='sabaton'))
        parts.append(bb.ccube(shin, (x, h.ankle_y + 0.1, -4.9), (3.6, 1.2, 1.4), P['plate2'], rot=(0.25, 0, 0), name='sabaton_toe'))
    return parts


def great_helm(h, P, crown=True, plume=True, visor_mat=None, crown_spikes=7):
    head = h.head
    top = h.head_top
    cy = top + 4.0
    bb.ccube(head, (0, cy - 0.2, 0), (9.6, 9.6, 9.6), P['plate'], name='helm')
    bb.ccube(head, (0, cy + 1.2, -4.95), (8.6, 6.0, 0.7), P['plate2'], name='visor')
    bb.ccube(head, (0, cy + 3.9, -5.0), (6.4, 1.0, 0.7), P['plate_d'], name='visor_jaw', rot=(0.25, 0, 0))
    vm = visor_mat or P['glow']
    bb.ccube(head, (0, cy - 0.5, -5.35), (6.8, 0.75, 0.2), vm, name='visor_slit')
    bb.ccube(head, (0, cy + 1.6, -5.35), (0.75, 2.8, 0.2), vm, name='visor_breath')
    for s in (-1, 1):
        for k in range(3):
            bb.ccube(head, (s * 1.8, cy + 1.4 + k * 0.9, -5.33), (1.2, 0.35, 0.15), P['steel'], name='breath_hole')
    bb.ccube(head, (0, top - 0.7, 0), (1.3, 1.2, 10.2), P['gold2'], name='helm_ridge')
    bb.ccube(head, (0, cy - 0.2, -5.05), (0.9, 9.0, 0.5), P['gold2'], name='helm_nasal')
    for s in (-1, 1):
        # little wings on the helm's sides
        for k in range(3):
            L = 3.6 - k * 0.8
            bb.ccube(head, (s * (5.3 + L / 2 * 0.6), cy - 1.6 - k * 0.9, 1.0 + k * 0.9), (L, 0.7, 1.0), P['gold2'],
                     rot=(0, s * -0.35, s * (0.55 + k * 0.18)), pivot=(s * 5.0, cy - 1.0, 1.0), name='helm_wing')
    if crown:
        bb.ccube(head, (0, top + 0.2, 0), (10.6, 1.6, 10.6), P['gold'], name='crown_band', faces={'top': None, 'bottom': None})
        for i in range(crown_spikes):
            a = -math.pi / 2 + (i - (crown_spikes - 1) / 2) * (math.pi / (crown_spikes - 0.5))
            px, pz = math.cos(a) * 5.2, math.sin(a) * 5.2
            L = 3.4 if i == crown_spikes // 2 else (2.6 if i % 2 == 0 else 1.8)
            bb.ccube(head, (px, top - L / 2 - 0.4, pz), (1.1, L, 1.1), P['gold2'], name='crown_spike')
            bb.ccube(head, (px, top - L - 0.6, pz), (0.7, 0.7, 0.7), P['gem'] if i == crown_spikes // 2 else P['sun'], name='crown_jewel')
        for i in range(4):
            a = math.pi / 2 + (i - 1.5) * 0.7
            bb.ccube(head, (math.cos(a) * 5.2, top - 0.9, math.sin(a) * 5.2), (1.0, 1.4, 1.0), P['gold2'], name='crown_back')
    if plume:
        pl = h.rig.bone('plume', head, (0, top - 1.4, 0.5), anim='hair', amp=0.07, speed=0.07, drag=0.4)
        for k, (dx, w) in enumerate(((0.0, 2.4), (-1.1, 1.6), (1.1, 1.6))):
            SC.sweep(pl, [(dx, top - 1.2, 0.0), (dx, top - 5.0, 2.6), (dx * 1.4, top - 5.4, 7.0), (dx * 1.8, top - 2.2, 11.0),
                          (dx * 2.0, top + 4.0, 12.6)], lambda t, w=w: w * (1.0 - 0.75 * t ** 1.4), 0.9 - 0.25 * (k > 0), P['plume'],
                     k=10, up=(0, -1, 0), caps=('round', 'point'), name='plume', info={'hem': False})
    return head


def tower_shield(bone, c, P, emblem=True, w=13.0, hgt=19.0, out=1):
    """A tower shield standing on the forearm, its face looking out along x (out = +1 or -1)."""
    x, y, z = c
    bb.ccube(bone, (x, y, z), (0.9, hgt, w), P['plate2'], name='shield')
    bb.ccube(bone, (x + out * 0.55, y, z), (0.3, hgt - 1.6, w - 1.6), M('cloth', ROYAL, accent=GOLD, pattern='trim'), name='shield_field')
    for s in (-1, 1):
        bb.ccube(bone, (x + out * 0.45, y, z + s * (w / 2 - 0.3)), (0.6, hgt + 0.2, 0.7), P['gold2'], name='shield_rim')
        bb.ccube(bone, (x + out * 0.45, y + s * (hgt / 2 - 0.3), z), (0.6, 0.7, w + 0.2), P['gold2'], name='shield_rim')
    bb.ccube(bone, (x + out * 0.45, y + hgt / 2 + 1.0, z), (0.6, 2.0, w * 0.5), P['gold2'], name='shield_top')
    bb.ccube(bone, (x + out * 0.45, y - hgt / 2 - 1.2, z), (0.6, 2.4, w * 0.3), P['gold2'], name='shield_point')
    if emblem:
        # the sun on its face (the shield's face looks along -x when held on the left arm, out from the body)
        sb = bone
        sx = x + out * 0.8
        bb.ccube(sb, (sx, y - 1.0, z), (0.4, 3.6, 3.6), P['gold2'], name='shield_sun')
        bb.ccube(sb, (sx, y - 1.0, z), (0.4, 5.0, 1.4), P['gold2'], name='shield_sun')
        bb.ccube(sb, (sx, y - 1.0, z), (0.4, 1.4, 5.0), P['gold2'], name='shield_sun')
        for i in range(8):
            a = i * math.pi / 4 + math.pi / 8
            bb.ccube(sb, (sx, y - 1.0 + math.sin(a) * 3.4, z + math.cos(a) * 3.4), (0.35, 0.5, 1.8), P['gold2'], rot=(a, 0, 0),
                     name='shield_ray')
        bb.ccube(sb, (sx + out * 0.3, y - 1.0, z), (0.3, 1.6, 1.6), P['sun'], name='shield_core')


def glitch_px(seed, amount=1.0):
    """A post-pass for a relief's pixels (king_arms.place): runs of columns slid up or down, blocks gone to the
    missing texture, a few pixels torn out. The slab's walls follow the torn silhouette."""
    def post(rgba, gl):
        rng = np.random.default_rng(seed)
        rgba, gl = rgba.copy(), gl.copy()
        H, W = rgba.shape[:2]
        for _ in range(int(4 * amount) + 1):
            x0, w, sh = int(rng.integers(0, max(1, W - 8))), int(rng.integers(2, 7)), int(rng.integers(-3, 4))
            rgba[:, x0:x0 + w] = np.roll(rgba[:, x0:x0 + w], sh, axis=0)
            gl[:, x0:x0 + w] = np.roll(gl[:, x0:x0 + w], sh, axis=0)
        ys, xs = np.nonzero(rgba[..., 3] > 0)
        for _ in range(int(len(ys) * 0.012 * amount)):
            k = int(rng.integers(0, len(ys)))
            y0, x0 = ys[k], xs[k]
            sz = int(rng.integers(2, 5))
            blk = rgba[y0:y0 + sz, x0:x0 + sz]
            on = blk[..., 3] > 0
            cy, cx = np.indices(on.shape)
            mag = ((cy + cx) % 2 == 0)
            blk[on & mag, :3] = (255, 0, 255)
            blk[on & ~mag, :3] = (0, 0, 0)
            gl[y0:y0 + sz, x0:x0 + sz][on & mag] = (255, 0, 255, 255)
        holes = rng.random(rgba.shape[:2]) < 0.015 * amount
        rgba[holes, 3] = 0
        return rgba, gl
    return post


def holy_sword(bone, hand, broken=False):
    """聖剣《黎明》 (king_arms 'greatsword') in the fist: the grip through the hand along the bone's +y, the blade on
    below it, edge-on (its width along z, its flats to the sides) as a sword is held; the bone tilts it forward.
    Broken: the hilt whole in his hand, the blade in five floating, glitching pieces with gaps between them."""
    U, V = (0, 1, 0), (0, 0, 1)
    if not broken:
        KA.place(bone, 'greatsword', hand, U, V, nm='holy_sword')
        return
    KA.place(bone, 'greatsword', hand, U, V, clip=(-10, 31), post=glitch_px(5, 0.5), nm='holy_hilt')
    L = KA.DESIGNS['greatsword']['length']
    cuts = [31, 45, 59, 72, 85, 101]
    x, y, z = hand
    g = KA.DESIGNS['greatsword']['grip_u']
    for i in range(len(cuts) - 1):
        mid = y + ((cuts[i] + cuts[i + 1]) / 2 - g) * L / 100.0
        tb = bone.rig.bone(f'blade_bit_{i}', bone, (x, mid, z), anim='float', amp=0.35 + 0.1 * i, speed=0.11, phase=i * 1.3)
        gap = (i + 1) * 0.9
        KA.place(tb, 'greatsword', (x + (0.3 if i % 2 else -0.3), y + gap, z + (0.4 if i % 2 else -0.3)), U, V,
                 clip=(cuts[i], cuts[i + 1]), post=glitch_px(17 + i, 1.0), nm=f'holy_blade_{i}')


# ------------------------------------------------------------------------------------------------------- forms
def knight(r, P, broken=False):
    """The hero's whole body (the broken form builds the same, then corrupts it)."""
    h = Humanoid(r, 'large', skin='#e9c3a3', accent=GOLD)
    h.body(top_mat=P['plate'], bottom_mat=P['plate2'], waist_mat=P['steel'], legs_mat=P['plate2'], boots_mat=P['plate'],
           arms_mat=P['plate2'], hands_mat=P['steel'], neck=None, boots_h=6)
    h.head_cube({'iris': '#4a90ff', 'iris2': '#cfefff', 'style': 'calm', 'glow_eyes': True})
    great_helm(h, P, visor_mat=P.get('visor'))
    torso = h.torso
    cw, ch, cd = h.T['chest']
    bb.ccube(torso, (0, h.top - 0.2, 0), (8.4, 1.8, 7.6), P['gold'], name='gorget')
    bb.ccube(torso, (0, h.top + 4.2, -cd / 2 - 0.4), (cw - 0.6, 7.6, 0.8), P['plate'], name='breastplate')
    bb.ccube(torso, (0, h.top + 1.0, -cd / 2 - 0.7), (cw - 2.0, 1.2, 0.5), P['gold2'], name='breast_rim')
    sun_disc(torso, (0, h.top + 4.4, -cd / 2 - 1.0), 1.8, P['gold2'], P['sun'], rays=12, depth=0.5)
    for i in range(3):
        bb.ccube(torso, (0, h.chest_y1 + 0.2 + i * 1.15, -cd / 2 - 0.2 + i * 0.1), (cw - 1.8 - i * 0.6, 1.3, 0.6),
                 P['plate2'] if i % 2 == 0 else P['plate_d'], rot=(-0.08, 0, 0), name='lame')
    bb.ccube(torso, (0, h.top + 4.0, cd / 2 + 0.35), (cw - 0.6, 7.4, 0.7), P['plate2'], name='backplate')
    h.belt(P['gold'], buckle=P['gem'])
    for z, nm in ((-3.25, 'tabard_f'), (3.25, 'tabard_b')):
        tb = r.bone(nm, h.hips, (0, h.pelvis_top + 1.0, z), anim='sway', ax=0, amp=0.04, speed=0.05, phase=0.5 if z > 0 else 0.0)
        bb.ccube(tb, (0, h.pelvis_top + 7.5, z), (5.6, 13.0, 0.45), P['tabard'], name='tabard')
        bb.ccube(tb, (0, h.pelvis_top + 14.2, z), (5.6, 0.6, 0.6), P['gold2'], name='tabard_hem')
        sun_disc(tb, (0, h.pelvis_top + 6.0, z - 0.35 if z < 0 else z + 0.35), 0.9, P['gold2'], P['sun'], rays=8, depth=0.25,
                 normal_z=-1 if z < 0 else 1)
    for leg, sgn in ((h.leg_r, -1), (h.leg_l, 1)):
        x = leg.pivot[0]
        for k in range(3):
            bb.ccube(leg, (x + sgn * 0.6, h.hip_y + 0.6 + k * 1.5, -2.9 - k * 0.05), (5.6 - k * 0.3, 1.8, 0.7),
                     P['plate'] if k % 2 == 0 else P['plate_d'], rot=(-0.1, 0, sgn * 0.1), name='tasset')
    for arm, sgn in ((h.arm_r, -1), (h.arm_l, 1)):
        pauldron(h, arm, sgn, P)
    limb_armour(h, P)
    cape = h.cape(P['cape'], length=28, width=15)
    sun_disc(cape, (0, h.top + 7.0, cd / 2 + 1.0), 2.2, P['gold2'], P['sun'], rays=12, depth=0.35, normal_z=1)
    h.fur_collar(P['fur'], shoulders=False)
    sb = r.bone('sword', h.fore_r, (h.fore_r.pivot[0], h.hand_y, -0.2), rot=(SWORD_TILT, 0, 0))
    holy_sword(sb, (h.fore_r.pivot[0], h.hand_y, -0.2), broken=broken)
    return h


@recipe
def villager_king_hero():
    r = Rig('villager_king_hero', height=44.0)        # the plume stands above the hitbox
    P = mats_hero()
    h = knight(r, P)
    shb = r.bone('shield', h.fore_l, (h.fore_l.pivot[0], h.elbow_y + 4.0, 0))
    tower_shield(shb, (h.fore_l.pivot[0] + 3.4, h.elbow_y + 4.0, -0.5), P)
    return r


# ---------------------------------------------------------------------------------------- the broken form's paint
MAGENTA, CYAN = np.array([255, 0, 255], np.float32), np.array([0, 255, 255], np.float32)


def _checker(f, cell=2):
    return (((f.u // cell) + (f.v // cell)) % 2 == 0)


def m_missing(mat, f, s, ctx):
    """Minecraft's own missing texture: magenta and black squares, the magenta faintly alight."""
    on = _checker(f, int(mat.get('cell', 2)))
    rgb = np.zeros((f.H, f.W, 3), np.float32)
    rgb[on] = MAGENTA
    glow = np.zeros((f.H, f.W, 4), np.float32)
    glow[on, :3] = MAGENTA
    glow[on, 3] = 255 * float(mat.get('glow_amount', 0.55))
    return rgb, None, glow


def m_glitch(mat, f, s, ctx):
    """A material whose texture has gone wrong: the base painted, then patches of the missing texture, rows slid
    sideways, a red/cyan colour fringe and stuck pixels (magenta, cyan, white), the bright ones alight."""
    base = mat['base']
    fn = BP.PAINTERS.get(base.get('type'), BP.m_fallback)
    rgb, alpha, glow = fn(base, f, s, ctx)
    rgb = np.array(rgb, np.float32)
    glow = np.zeros((f.H, f.W, 4), np.float32) if glow is None else np.array(glow, np.float32)
    rng = np.random.default_rng(int(f.seed) & 0x7fffffff)
    H, W = f.H, f.W
    amt = float(mat.get('amount', 1.0))
    for _ in range(int(max(1, W * H / 110) * amt)):
        w, hh = int(rng.integers(1, 4)), int(rng.integers(1, 4))
        x0, y0 = int(rng.integers(0, W)), int(rng.integers(0, H))
        sl = (slice(y0, min(H, y0 + hh)), slice(x0, min(W, x0 + w)))
        on = _checker(f)[sl]
        patch = np.where(on[..., None], MAGENTA, 0.0)
        rgb[sl] = patch
        glow[sl][..., :3] = np.where(on[..., None], MAGENTA, 0.0)
        glow[sl][..., 3] = np.where(on, 150.0, 0.0)
    for y in range(H):
        if W > 2 and rng.random() < 0.18 * amt:
            k = int(rng.choice((-3, -2, -1, 1, 2, 3)))
            rgb[y] = np.roll(rgb[y], k, axis=0)
            glow[y] = np.roll(glow[y], k, axis=0)
    if W > 2 and rng.random() < 0.5:
        rgb[..., 0] = np.roll(rgb[..., 0], 1, axis=1)
        rgb[..., 2] = np.roll(rgb[..., 2], -1, axis=1)
    for _ in range(int(max(1, W * H / 140) * amt)):
        y, x = int(rng.integers(0, H)), int(rng.integers(0, W))
        c = [MAGENTA, CYAN, np.array([255, 255, 255], np.float32), np.array([255, 40, 40], np.float32)][int(rng.integers(0, 4))]
        rgb[y, x] = c
        glow[y, x, :3] = c
        glow[y, x, 3] = 220
    return rgb, alpha, glow


BP.PAINTERS['missing'] = m_missing
BP.PAINTERS['glitch'] = m_glitch


def glitched(m, amount=1.0):
    return M('glitch', m.get('color', '#888888'), base=dict(m), amount=amount)


# ---------------------------------------------------------------------------------------- the broken form's shape
CRACKED = dict(accent='#d01030', pattern='cracks', pattern_glow=True, glow_amount=0.5)


class Corrupt:
    """While it is in force, every ornament cube (bb.ccube) is corrupted as it is made: some left out, some gone to
    the missing texture, the rest painted wrong; a third knocked out of place and askew. With shatter > 0 the plates
    (flat metal pieces) break instead, that share of them: split into shards with gaps between them, some shards gone
    (holes), the rest lifted off and tilted, a dark core of nothing where the plate was, alight with red cracks.
    The body's own boxes stay."""

    def __init__(self, seed=7, shatter=0.0):
        self.rng = np.random.default_rng(seed)
        self.orig = bb.ccube
        self.shatter = shatter

    def _shards(self, bone, center, size, mat, kw):
        rng, orig = self.rng, self.orig
        from rig import rot_zyx
        s = np.asarray(size, float)
        C = np.asarray(center, float)
        rot = kw.get('rot')
        R = rot_zyx(*rot) if rot is not None and any(abs(v) > 1e-9 for v in rot) else np.eye(3)
        if rot is not None and kw.get('pivot') is not None:
            p = np.asarray(kw['pivot'], float)
            C = p + R @ (C - p)
        thin = int(np.argmin(s))
        a0, a1 = [a for a in range(3) if a != thin]
        nrm = R[:, thin]
        piv = np.asarray(getattr(bone, 'pivot', (0, 0, 0)), float)
        out_sign = 1.0 if float(nrm @ (C - piv)) >= 0 else -1.0
        nm = kw.get('name', 'plate')
        # the core of nothing under the plate
        core = s.copy()
        core[thin] *= 0.55
        core[a0] *= 0.82
        core[a1] *= 0.82
        bb.obox(bone, C - nrm * out_sign * s[thin] * 0.2, core, R, M('void', '#0a0010'), name=nm + '_void')
        n0 = 2 if s[a0] < 4.5 else 3
        n1 = 2 if s[a1] < 4.5 else 3
        base = mat if mat.get('type') != 'metal' else M('metal', mat.get('color', SILVER), **CRACKED)
        for i in range(n0):
            for j in range(n1):
                if rng.random() < 0.24:
                    continue                        # a hole: the shard is gone
                gap = 0.4 + rng.random() * 0.35
                cell = s.copy()
                cell[a0] = max(0.4, s[a0] / n0 - gap)
                cell[a1] = max(0.4, s[a1] / n1 - gap)
                off = np.zeros(3)
                off[a0] = (i + 0.5) * s[a0] / n0 - s[a0] / 2 + rng.uniform(-0.25, 0.25)
                off[a1] = (j + 0.5) * s[a1] / n1 - s[a1] / 2 + rng.uniform(-0.25, 0.25)
                off[thin] = out_sign * rng.uniform(0.3, 1.4)
                tilt = rot_zyx(*rng.uniform(-0.4, 0.4, 3))
                m = M('missing', '#ff00ff') if rng.random() < 0.04 else base
                # each shard on a bone of its own, so it can fall away as he breaks (KingRig: crumble_*)
                cb = bone.rig.bone('crumble', bone, tuple(C + R @ off))
                bb.obox(cb, C + R @ off, cell, R @ tilt, m, name=nm + '_shard')
        return []

    def __enter__(self):
        rng, orig = self.rng, self.orig

        def cc(bone, center, size, mat, **kw):
            t = mat.get('type')
            sz = sorted(float(v) for v in size)
            if self.shatter > 0 and t in ('metal', 'glitch') and sz[0] <= 1.4 and sz[1] >= 1.6 and sz[2] >= 2.4 \
                    and rng.random() < self.shatter:
                return self._shards(bone, center, size, mat, kw)
            roll = rng.random()
            if t not in ('energy', 'gem') and roll < 0.06:
                return []
            if t in ('energy', 'gem'):
                mat = M('energy', '#ff2a6a' if rng.random() < 0.5 else '#2affff')
            elif roll < 0.15:
                mat = M('missing', '#ff00ff')
            elif roll < 0.6:
                mat = glitched(mat, amount=0.35 + rng.random() * 0.5)
            c = np.asarray(center, float)
            if rng.random() < 0.3:
                c = c + rng.uniform(-1.4, 1.4, 3)
                r0 = kw.get('rot') or (0, 0, 0)
                kw['rot'] = tuple(float(v) + float(rng.uniform(-0.35, 0.35)) for v in r0)
                kw.pop('pivot', None)
            if self.shatter > 0 and rng.random() < 0.55:
                # the king's own pieces fall away too as he breaks
                bone = bone.rig.bone('crumble', bone, tuple(c))
            return orig(bone, tuple(c), size, mat, **kw)

        bb.ccube = cc
        return self

    def __exit__(self, *a):
        bb.ccube = self.orig


@recipe
def villager_king_broken():
    r = Rig('villager_king_broken', height=44.0)
    P = mats_hero()
    P['visor'] = M('energy', '#ff2a4a')
    # the plate cracked all over, red light in the cracks; the body boxes under it too
    P['plate'] = M('metal', SILVER, **CRACKED)
    P['plate_d'] = M('metal', SILVER_D, **CRACKED)
    P['plate2'] = glitched(P['plate2'], 0.3)
    P['steel'] = glitched(P['steel'], 0.3)
    with Corrupt(11, shatter=0.85):
        h = knight(r, P, broken=True)
    # one eye's glow gone cyan
    bb.ccube(h.head, (1.6, h.head_top + 3.5, -5.5), (2.6, 0.8, 0.2), M('energy', '#2affff'), name='visor_cyan')
    # the left arm run on into an arm of error blocks: too many joints, claws
    fore = h.fore_l
    x = fore.pivot[0]
    prev, y = fore, h.wrist_y + 2.0
    mats = [M('missing', '#ff00ff'), M('void', '#140014'), M('missing', '#ff00ff', cell=1)]
    for k in range(4):
        L = 4.2 - k * 0.5
        j = r.bone(f'error_arm_{k}', prev, (x, y, 0), rot=(-0.25, 0, 0.12 * (1 if k % 2 else -1)), anim='sway', ax=2, amp=0.12,
                   speed=0.17, phase=k * 0.9)
        bb.ccube(j, (x, y + L / 2, 0), (3.4 - k * 0.4, L, 3.4 - k * 0.4), mats[k % 3], name='error_arm')
        bb.ccube(j, (x + 0.6, y + L * 0.3, -1.8), (1.0, 1.0, 1.0), M('energy', '#ff00ff'), name='error_node')
        prev, y = j, y + L
    for c in range(4):
        a = (c - 1.5) * 0.45
        bb.ccube(prev, (x + math.sin(a) * 1.4, y + 1.6, math.cos(a) * 1.4 - 1.2), (0.7, 3.6, 0.7), M('void', '#1a001a'),
                 rot=(0.5, 0, a), name='error_claw')
        bb.ccube(prev, (x + math.sin(a) * 1.9, y + 3.6, math.cos(a) * 1.9 - 2.0), (0.5, 1.2, 0.5), M('energy', '#ff2aff'),
                 rot=(0.7, 0, a), name='error_claw_tip')
    # the shield in pieces round him, his skin's pixels drifting off him
    orbiters(r, h.torso, (0, h.top + 4, 0), [glitched(P['plate']), M('missing', '#ff00ff'), glitched(P['gold2']),
                                              M('cloth', ROYAL, accent=GOLD, pattern='trim')],
             count=6, radius=13, size=2.6, speed=0.045, name='shards', shapes=[(3.0, 3.8, 0.8), (2.2, 2.2, 0.8), (3.4, 2.0, 0.8)])
    orbiters(r, h.hips, (0, h.pelvis_top, 0), [M('energy', '#ff00ff'), M('energy', '#00ffff'), M('void', '#000000'),
                                                M('energy', '#ffffff')], count=10, radius=10, size=0.9, speed=-0.07, name='pixels')
    orbiters(r, h.head, (0, h.head_top - 3, 0), [M('missing', '#ff00ff'), M('energy', '#00ffff')], count=5, radius=7, size=1.0,
             speed=0.09, name='pixels_hi')
    rot_stages(r, h)
    return r


def leg_chain(r, parent, start, segs, mats, name, joint=None, anim_amp=0.1, phase=0.0):
    """A jointed limb of boxes along a list of points (a spider's leg, an enderman's arm, a tendril), each segment its
    own swaying bone."""
    prev = parent
    pts = [np.array(start, float)] + [np.array(p, float) for p in segs]
    for i in range(len(pts) - 1):
        b = r.bone(f'{name}_{i}', prev, tuple(pts[i]), anim='sway', ax=2 if i % 2 else 0, amp=anim_amp, speed=0.13, phase=phase + i * 0.7)
        w = mats[i % len(mats)]
        bb.beam(b, pts[i], pts[i + 1], max(0.5, 1.6 - i * 0.3), max(0.5, 1.6 - i * 0.3), w, name=name)
        if joint:
            bb.ccube(b, tuple(pts[i + 1]), (1.4 - i * 0.2, 1.4 - i * 0.2, 1.4 - i * 0.2), joint, name=name + '_joint')
        prev = b
    return prev


def rot_stages(r, h):
    """(054) The broken king worsens as he is hurt (RoyalRenderer scales each stage in by his health): the corruption
    takes from the monsters of the world and grows them on him.
      rot1 (below 3/4): a spider's legs out of his back, clusters of spider's eyes on his helm and his breast
      rot2 (below 1/2): his breast torn open on a rotten rib cage, an enderman's long black arm off his right shoulder,
                         slime dripping from him
      rot3 (below 1/4): the villager king's old head bursting out of his left shoulder, the warden's sculk tendrils
                         out of his back, silverfish segments crawling up the error arm, a phantom's torn wing"""
    cw, ch, cd = h.T['chest']
    chitin = M('scale', '#2a1c16', accent='#5a1a14')
    spider_eye = M('energy', '#ff1a1a')
    flesh = M('scale', '#5a6a3a', accent='#3a2a1a')
    bone_m = M('metal', '#d8d0b8')
    ender = M('void', '#120a18')
    ender_eye = M('energy', '#d070ff')
    slime = M('gem', '#6fd06a', glow=False, alpha=0.7)
    sculk = M('scale', '#0c2a34', accent='#30e0e0')
    sculk_glow = M('energy', '#3af0f0')
    silver = M('metal', '#8a8f9a')
    phantom = M('membrane', '#3a4a7a', accent='#a0ff60', alpha=0.8)
    # rot1: spider legs and eyes
    s1 = r.bone('rot1_body', h.torso, (0, h.top + 4, cd / 2), anim='')
    for sgn in (-1, 1):
        for k in range(3):
            y = h.top + 2.5 + k * 2.6
            x0 = sgn * 2.5
            leg_chain(r, s1, (x0, y, cd / 2 + 0.5),
                      [(x0 + sgn * 7, y - 6 + k, cd / 2 + 3 + k), (x0 + sgn * 13, y + 2, cd / 2 + 5 + k), (x0 + sgn * 15, y + 14 - k * 2, cd / 2 + 4)],
                      [chitin], f'rot1_leg_{"r" if sgn < 0 else "l"}{k}', joint=M('scale', '#3a2a1a'), anim_amp=0.12, phase=k + sgn)
    s1h = r.bone('rot1_eyes', h.head, (0, h.head_top + 2, -5), anim='')
    for (dx, dy, sz) in ((-3.2, 1.0, 1.1), (-2.0, 0.2, 0.8), (3.4, 1.6, 1.2), (2.4, 0.4, 0.7), (3.8, 3.0, 0.8), (-3.6, 2.6, 0.9)):
        bb.ccube(s1h, (dx, h.head_top + 2 + dy, -5.1), (sz, sz, 0.35), spider_eye, name='spider_eye')
    for (dx, dy, sz) in ((-2.2, 2.0, 0.9), (-1.0, 3.0, 0.7), (1.8, 2.4, 1.0), (0.4, 1.4, 0.6)):
        bb.ccube(s1, (dx, h.top + 2 + dy, -cd / 2 - 1.3), (sz, sz, 0.35), spider_eye, name='spider_eye')
    # rot2: the rib cage, the enderman's arm, slime
    s2 = r.bone('rot2_body', h.torso, (0, h.top + 4, -cd / 2), anim='breath')
    bb.ccube(s2, (0, h.top + 4.2, -cd / 2 - 1.0), (6.6, 7.0, 0.6), flesh, name='rot_flesh')
    for k in range(5):
        y = h.top + 1.6 + k * 1.35
        for sgn in (-1, 1):
            bb.ccube(s2, (sgn * 1.9, y, -cd / 2 - 1.5), (3.2, 0.6, 0.6), bone_m, rot=(0, 0, sgn * 0.25), name='rib')
    bb.ccube(s2, (0, h.top + 4.0, -cd / 2 - 1.4), (0.8, 7.0, 0.6), bone_m, name='sternum')
    bb.ccube(s2, (0.4, h.top + 5.0, -cd / 2 - 1.2), (2.0, 2.2, 1.2), M('energy', '#a0ff40'), name='rot_heart')
    sa = r.bone('rot2_arm', h.torso, (-h.shoulder_x - 1.0, h.top + 1.0, 1.5), anim='')
    hand = leg_chain(r, sa, (-h.shoulder_x - 1.0, h.top + 1.0, 1.5),
                     [(-h.shoulder_x - 4.0, h.top + 10, 3.0), (-h.shoulder_x - 5.0, h.top + 22, 1.0), (-h.shoulder_x - 4.5, h.top + 31, -1.5)],
                     [ender], 'rot2_ender', joint=ender, anim_amp=0.06)
    for k in range(3):
        bb.ccube(hand, (-h.shoulder_x - 4.5 + (k - 1) * 0.8, h.top + 32.6, -1.8), (0.5, 2.4, 0.5), ender, name='ender_finger')
    bb.ccube(sa, (-h.shoulder_x - 3.0, h.top + 6.0, 1.0), (0.6, 0.6, 0.2), ender_eye, name='ender_eye')
    for (x, y, z) in ((-5.5, h.wrist_y, -1.0), (5.0, h.chest_y1 + 1.0, -2.6), (-2.0, h.pelvis_y1 + 2.0, -3.4), (3.0, h.top + 7.5, 3.6)):
        db = r.bone('rot2_drip', h.torso, (x, y, z), anim='float', amp=0.6, speed=0.09)
        bb.ccube(db, (x, y + 1.0, z), (1.2, 2.4, 1.2), slime, name='slime')
        bb.ccube(db, (x, y + 2.8, z), (0.7, 1.4, 0.7), slime, name='slime')
    # rot3: the old head, sculk tendrils, silverfish, the phantom's wing
    s3 = r.bone('rot3_head', h.torso, (h.shoulder_x - 0.5, h.top - 1.0, 0.5), rot=(0.2, -0.5, 0.55), anim='sway', ax=2, amp=0.15, speed=0.21)
    hx, hy = h.shoulder_x - 0.5, h.top - 6.0
    bb.ccube(s3, (hx, hy, 0.5), (7.0, 8.4, 7.0), M('skin', '#bd8b6a'), name='old_head')
    bb.ccube(s3, (hx, hy + 1.6, -3.6), (1.8, 3.6, 1.6), M('skin', '#a8785a'), name='old_nose')
    bb.ccube(s3, (hx, hy - 1.4, -3.05), (5.4, 0.8, 0.2), M('cloth', '#3a281c'), name='old_brow')
    for sgn in (-1, 1):
        bb.ccube(s3, (hx + sgn * 1.7, hy - 0.4, -3.1), (1.4, 1.0, 0.2), M('energy', '#fffaf0'), name='old_eye')
        bb.ccube(s3, (hx + sgn * 1.7, hy - 0.4, -3.2), (0.6, 1.0, 0.1), M('energy', '#20c040' if sgn < 0 else '#ff2020'), name='old_iris')
    bb.ccube(s3, (hx, hy + 4.0, -2.6), (5.2, 3.0, 2.4), M('fur', '#e8e4dc'), name='old_beard')
    bb.ccube(s3, (hx, hy - 5.0, 0.5), (7.6, 1.6, 7.6), M('missing', '#ff00ff'), name='old_crown')
    for k in range(4):
        a = (k - 1.5) * 0.5
        leg_chain(r, s3, (math.sin(a) * 2.5, h.top + 2.0 + k * 1.5, cd / 2 + 0.6),
                  [(math.sin(a) * 6, h.top - 4 + k * 2, cd / 2 + 7), (math.sin(a) * 9, h.top - 9 + k * 3, cd / 2 + 12),
                   (math.sin(a) * 10, h.top - 15 + k * 4, cd / 2 + 14)], [sculk], f'rot3_sculk{k}', joint=sculk_glow, anim_amp=0.14, phase=k)
    for k in range(5):
        sb = r.bone(f'rot3_silverfish{k}', h.fore_l, (h.fore_l.pivot[0] + 1.6, h.elbow_y + k * 1.6, -1.9), anim='float', amp=0.25,
                    speed=0.3, phase=k)
        bb.ccube(sb, (h.fore_l.pivot[0] + 1.6, h.elbow_y + k * 1.6, -1.9), (1.6 - k * 0.15, 1.2, 1.4), silver, name='silverfish')
    pw = r.bone('rot3_phantom', h.torso, (-2.5, h.top + 2.0, cd / 2 + 1.0), rot=(0.1, 0.6, 0.3), anim='wing_r', amp=0.25, speed=0.15)
    for i in range(6):
        t = i / 5
        bb.ccube(pw, (-2.5 - 2.0 - i * 2.4, h.top + 2.0 + t * 3.0, cd / 2 + 1.0), (2.4, 6.0 - t * 3.0 + (1 if i % 2 else 0), 0.2), phantom,
                 name='phantom_wing')


# ------------------------------------------------------------------------------------------------- the god's form
WHITE = '#fbf8ef'
GOLD_D = '#f0c24a'
STORM = '#1d2a6e'
STORM_D = '#111840'
STORM_L = '#bfe3ff'


def _beam(bone, p0, p1, w, d, mat, name, up=(0, 0, -1)):
    return bb.beam(bone, p0, p1, w, d, mat, up=up, name=name)


def feather_wing(r, parent, sgn, at, span, feather, edge, covert, name, rest=(0.18, 0.55, 0.22), amp=0.16, lift=1.0, scale_len=1.0,
                 tip_mat=None, eyes=None):
    """A bird's (an angel's) wing built feather by feather, after the spectral wings of the reference bosses
    (Cataclysm's Maledictus): an armoured leading edge arching up from the shoulder through the elbow and the wrist
    to the tip; primaries fanning from the hand (out and up at the tip, down and out toward the wrist); secondaries
    hanging from the forearm, shorter toward the body; two rows of short coverts over their roots. Each feather is a
    long thin blade, a broad shaft and a narrower tip, set a hair behind the one before so they overlap like a fan.
    The wing lies in the plane x (out, sgn) by y (down), a little back along z; the bone sweeps it back and up."""
    ax, ay, az = at
    root = r.bone(name, parent, (ax, ay, az), rot=(rest[0], sgn * -rest[1], sgn * -rest[2]), anim=name.split('_')[0] + '_' + ('r' if sgn < 0 else 'l'),
                  amp=amp, speed=0.1)
    S = float(span)

    def P(u, v, dz=0.0):
        return np.array([ax + sgn * u * S, ay + v * S * lift, az + dz])
    sh, el, wr, tip = P(0.0, 0.0), P(0.30, -0.30), P(0.62, -0.44), P(0.86, -0.40)
    # the arm of the wing: gold, thick at the shoulder
    _beam(root, sh, el, 1.6, 1.2, edge, 'wing_arm')
    _beam(root, el, wr, 1.3, 1.0, edge, 'wing_fore')
    _beam(root, wr, tip, 1.0, 0.8, edge, 'wing_hand')
    for q, s_ in ((el, 1.9), (wr, 1.6)):
        bb.ccube(root, tuple(q), (s_, s_, s_), edge, name='wing_joint')

    def blade(base, ang, L, w, mat, z, nm, tmat=None):
        # ang: 0 = straight down (+y), positive turns outward (toward sgn x)
        d = np.array([sgn * math.sin(ang), math.cos(ang), 0.0])
        b0 = base + np.array([0, 0, z])
        b1 = b0 + d * L * 0.72
        b2 = b0 + d * L
        _beam(root, b0, b1, w, 0.32, mat, nm)
        _beam(root, b1 - d * 0.2, b2, w * 0.6, 0.3, tmat or tip_mat or mat, nm + '_tip')
        if eyes and nm != 'covert' and (int(abs(b0[0]) * 7 + abs(b0[1]) * 3) % 3 == 0):
            e = b0 + d * L * 0.55 + np.array([0, 0, -0.25])
            bb.ccube(root, tuple(e), (w * 0.62, w * 0.62, 0.2), eyes[0], name='wing_eye')
            bb.ccube(root, tuple(e + np.array([0, 0, -0.12])), (w * 0.3, w * 0.3, 0.12), eyes[1], name='wing_iris')

    L0 = S * scale_len
    # primaries: from the hand, fanning from out-and-up at the tip to down-and-out by the wrist
    n = 10
    for i in range(n):
        t = i / (n - 1)
        base = tip + (wr - tip) * t
        ang = math.radians(118 - 78 * t)          # 118 deg: out and up; 40 deg: down and out
        L = L0 * (0.52 - 0.18 * t)
        blade(base, ang, L, 2.6, feather, 0.55 + 0.11 * i, 'primary')
    # secondaries: hanging from the forearm and the arm
    m = 9
    for i in range(m):
        t = i / (m - 1)
        base = wr + (sh - wr) * t
        ang = math.radians(32 - 26 * t)
        L = L0 * (0.40 - 0.16 * t)
        blade(base, ang, L, 2.8, feather, 0.35 + 0.08 * i, 'secondary')
    # coverts: two rows of short feathers over the roots
    for row, (k, Lr, z0) in enumerate(((11, 0.15, 0.1), (9, 0.24, 0.22))):
        for i in range(k):
            t = i / (k - 1)
            base = (tip + (sh - tip) * t) + np.array([0, 0.6 + row * 0.9, 0])
            ang = math.radians(60 - 40 * t)
            blade(base, ang, L0 * Lr, 2.3, covert, z0 + 0.02 * i, 'covert')
    return root


def insect_wing(r, parent, sgn, at, length, width, glass, vein, name):
    """A long glassy wing (the lord of the flies, made holy): a pane of stepped plates edged in gold, gold veins."""
    ax, ay, az = at
    root = r.bone(name, parent, (ax, ay, az), rot=(0.25, sgn * -0.75, sgn * 0.35), anim='wing_' + ('r' if sgn < 0 else 'l'), amp=0.3,
                  speed=0.35)
    steps = 8
    for i in range(steps):
        t = (i + 0.5) / steps
        h = width * math.sin(math.pi * (0.08 + 0.92 * t)) ** 0.8
        x = ax + sgn * length * t
        bb.ccube(root, (x, ay + h * 0.15, az + 0.1), (length / steps + 0.05, h, 0.12), glass, name='pane')
        bb.ccube(root, (x, ay - h * 0.35, az + 0.05), (length / steps + 0.05, 0.3, 0.2), vein, name='pane_edge')
        bb.ccube(root, (x, ay + h * 0.65, az + 0.05), (length / steps + 0.05, 0.25, 0.2), vein, name='pane_edge')
    _beam(root, (ax, ay, az), (ax + sgn * length, ay - width * 0.25, az), 0.5, 0.3, vein, 'vein')
    _beam(root, (ax, ay + 0.6, az), (ax + sgn * length * 0.9, ay + width * 0.3, az), 0.35, 0.3, vein, 'vein')
    for k in range(5):
        x = ax + sgn * length * (0.18 + 0.16 * k)
        _beam(root, (x, ay - width * 0.2, az), (x + sgn * 1.2, ay + width * 0.45, az), 0.25, 0.3, vein, 'vein')
    return root


UP, FWD, SIDE = (0, -1, 0), (0, 0, -1), (0, 0, 1)


def open_sleeves(h, mat, drop=7.0):
    """Wide sleeves that end above the wrist, so the hands come out free to hold his arms (a sleeve hanging over the
    fist swallowed the hafts), their slack hanging in a deep pouch behind the forearm."""
    aw, ad = h.T['arm']
    for arm, fore in ((h.arm_r, h.fore_r), (h.arm_l, h.fore_l)):
        x = arm.pivot[0]
        box(arm, x - aw / 2 - 0.35, h.top - 0.2, -ad / 2 - 0.35, aw + 0.7, h.elbow_y - h.top + 0.4, ad + 0.7, dict(mat, trim=0),
            name='sleeve_up', faces={'bottom': None})
        L = h.wrist_y - h.elbow_y - 0.3
        box(fore, x - aw / 2 - 0.5, h.elbow_y - 0.5, -ad / 2 - 0.5, aw + 1.0, L, ad + 1.0, mat, name='sleeve', info={'hem': True},
            faces={'top': None})
        box(fore, x - aw / 2 - 0.4, h.elbow_y + 0.5, ad / 2 + 0.5, aw + 0.8, L - 1.0 + drop * 0.55, 1.2 + drop * 0.3, mat,
            name='sleeve_pouch', info={'hem': True})


# Each stance's holding pose (KingRig.HOLD applies it in game: upper arm and forearm x rotations, right then left).
# Every haft runs through the middle of the fist square to the forearm, never along it: the forearm is brought up
# level for the long arms so their shafts stand upright in the fist; a little for the clubs and the swords.
HOLD_POSES = {
    'clubs': (-0.2, -0.45, -0.2, -0.45),
    'scythe': (-0.3, -1.25, 0.0, 0.0),
    'twin': (-0.25, -0.6, -0.25, -0.6),
    'spear': (-0.3, -1.2, 0.0, 0.0),
    'bow': (0.0, 0.0, -0.3, -1.25),
}


def hold_pose(stance):
    """The holding pose as a preview pose (sculpt.render's pose)."""
    ar, fr, al, fl = HOLD_POSES[stance]
    return {'arm_r': (ar, 0, 0), 'fore_r': (fr, 0, 0), 'arm_l': (al, 0, 0), 'fore_l': (fl, 0, 0)}


def stance_arms(r, h, hand_y=None):
    """Baal Zebul's five arms (king_arms designs as slabs), each set on its own bones under the fists so KingRig can show
    one set at a time (KingDeeds.switchStance; KingRig picks the set by what is in his hands) and bring his arms into
    its holding pose (HOLD_POSES). Each grip is in the middle of the fist; each weapon's bone is turned so that, in the
    holding pose, it stands as it should:
      clubs   雷霆棍 Yagrush (right) and Aymur (left), fists forward, the heads forward and high
      scythe  蝿王の大鎌, the right forearm level, the haft upright in the fist, the crescent out forward over him
      twin    the twin swords, Seraph (right) and Beelzebub (left), fists a little raised, the points forward
      spear   雷槍, the right forearm level, the haft upright, held a third of the way up
      bow     虹の大弓, the left forearm level, the bow upright in the fist, its back to the foe"""
    hy = h.hand_y if hand_y is None else hand_y
    xr, xl = h.fore_r.pivot[0], h.fore_l.pivot[0]

    def lean(stance, side, world):
        """The weapon bone's x rotation under the forearm for a wanted lean in the world (0 upright, + forward)."""
        ar, fr, al, fl = HOLD_POSES[stance]
        return world - ((ar + fr) if side == 'r' else (al + fl))

    cb = r.bone('arms_clubs_r', h.fore_r, (xr, hy, -0.2), rot=(lean('clubs', 'r', 0.75), 0, 0))
    KA.place(cb, 'yagrush', (xr, hy, -0.2), UP, SIDE, cross=57, nm='yagrush')
    cb = r.bone('arms_clubs_l', h.fore_l, (xl, hy, -0.2), rot=(lean('clubs', 'l', 0.75), 0, 0))
    KA.place(cb, 'aymur', (xl, hy, -0.2), UP, SIDE, cross=60, nm='aymur')
    sc = r.bone('arms_scythe_r', h.fore_r, (xr, hy, -0.2), rot=(lean('scythe', 'r', 0.15), 0, 0))
    KA.place(sc, 'scythe', (xr, hy, -0.2), UP, SIDE, nm='scythe')
    tr = r.bone('arms_twin_r', h.fore_r, (xr, hy, -0.2), rot=(lean('twin', 'r', 1.85), 0, 0))
    KA.place(tr, 'seraph', (xr, hy, -0.2), UP, SIDE, nm='seraph')
    tl = r.bone('arms_twin_l', h.fore_l, (xl, hy, -0.2), rot=(lean('twin', 'l', 1.85), 0, 0))
    KA.place(tl, 'beelzebub', (xl, hy, -0.2), UP, SIDE, nm='beelzebub')
    sp = r.bone('arms_spear_r', h.fore_r, (xr, hy, -0.2), rot=(lean('spear', 'r', 0.1), 0, 0))
    KA.place(sp, 'spear', (xr, hy, -0.2), UP, SIDE, nm='spear')
    bw = r.bone('arms_bow_l', h.fore_l, (xl, hy, -0.2), rot=(lean('bow', 'l', 0.05), 0, 0))
    KA.place(bw, 'bow', (xl, hy, -0.2), UP, FWD, nm='bow')


@recipe
def _weapons_preview():
    """(not shipped) the hero's sword and Baal Zebul's arms side by side, as slabs."""
    r = Rig('_weapons_preview')
    root = r.bone('root', None, (0, 24, 0))
    spots = [('greatsword', -30, -8, (0, 1, 0), SIDE, None), ('yagrush', -20, 20, UP, SIDE, 57), ('aymur', -12, 20, UP, SIDE, 60),
             ('scythe', 0, 22, UP, SIDE, None), ('seraph', 10, -4, (0, 1, 0), SIDE, None), ('beelzebub', 16, -4, (0, 1, 0), SIDE, None),
             ('spear', 24, 12, UP, SIDE, None), ('bow', 32, 2, UP, FWD, None)]
    for i, (n, x, y, U, V, cr) in enumerate(spots):
        b = r.bone(f'w{i}', root, (x, y, 0), rot=(0, 1.5708, 0))
        KA.place(b, n, (x, y, 0), U, V, cross=cr, nm=n)
    return r


def god_face(h, P):
    """The storm god's face: a gold diadem across the brow with a sun jewel, gold marks under the eyes, gold ear
    rings, and the braided gold beard of the old gods."""
    head, top = h.head, h.head_top
    fz = -4.0
    bb.ccube(head, (0, top + 1.6, fz - 0.15), (8.4, 1.1, 0.35), P['gold2'], name='diadem')
    bb.ccube(head, (0, top + 1.6, 0), (8.6, 1.0, 8.6), P['gold2'], name='diadem_band', faces={'top': None, 'bottom': None})
    bb.ccube(head, (0, top + 1.4, fz - 0.45), (1.6, 1.8, 0.4), P['gold'], name='diadem_sun')
    bb.ccube(head, (0, top + 1.4, fz - 0.7), (0.8, 0.8, 0.3), P['sun'], name='diadem_jewel')
    for sgn in (-1, 1):
        bb.ccube(head, (sgn * 2.4, top + 1.2, fz - 0.3), (1.2, 0.5, 0.3), P['gem'], name='diadem_gem')
        bb.ccube(head, (sgn * 2.1, top + 5.0, fz - 0.06), (1.6, 0.25, 0.1), P['gold2'], name='eye_mark')
        bb.ccube(head, (sgn * 2.6, top + 5.4, fz - 0.06), (0.25, 0.9, 0.1), P['gold2'], name='eye_mark')
        bb.ccube(head, (sgn * 4.25, top + 5.4, 0), (0.4, 1.6, 0.6), P['gold2'], name='earring')
        bb.ccube(head, (sgn * 4.3, top + 6.6, 0), (0.6, 0.6, 0.6), P['gem'], name='earring_gem')
    # moustache and the braided beard
    bb.ccube(head, (0, top + 6.6, fz - 0.25), (4.6, 0.8, 0.5), P['beard'], name='moustache')
    for sgn in (-1, 1):
        bb.ccube(head, (sgn * 2.6, top + 7.2, fz - 0.25), (0.8, 1.6, 0.5), P['beard'], name='moustache_end')
    bb.ccube(head, (0, top + 7.6, fz - 0.6), (6.4, 1.2, 1.4), P['beard'], name='beard_root')
    for k, dx in enumerate((-2.0, 0.0, 2.0)):
        n = 4 if dx else 5
        for j in range(n):
            y0 = top + 8.6 + j * 1.25
            bb.ccube(head, (dx, y0, fz - 0.55 - j * 0.15), (1.5 - j * 0.12, 1.15, 1.2), P['beard'] if j % 2 == 0 else P['beard2'], name='braid')
        bb.ccube(head, (dx, top + 8.6 + n * 1.25 - 0.3, fz - 0.6 - n * 0.15), (1.1, 0.5, 1.1), P['gold2'], name='braid_ring')


def demon_face(h, P):
    """The lord of the flies' face: a gold mask over the brow and the eyes with six glowing eyes in two clusters (a
    fly's many eyes), its edges swept back like wings; a black beard braided and ringed with gold; gold ear rings."""
    head, top = h.head, h.head_top
    fz = -4.0
    bb.ccube(head, (0, top + 3.6, fz - 0.3), (8.6, 4.2, 0.5), P['gold'], name='mask')
    bb.ccube(head, (0, top + 1.2, fz - 0.45), (1.4, 3.0, 0.5), P['gold2'], name='mask_ridge')
    for sgn in (-1, 1):
        bb.ccube(head, (sgn * 4.9, top + 2.8, fz + 0.6), (2.4, 1.0, 0.4), P['gold2'], rot=(0, sgn * 0.5, sgn * -0.5), name='mask_wing')
        bb.ccube(head, (sgn * 5.4, top + 1.8, fz + 1.2), (2.0, 0.8, 0.4), P['gold2'], rot=(0, sgn * 0.6, sgn * -0.8), name='mask_wing')
        for (dx, dy, sz) in ((1.4, 3.4, 1.1), (2.7, 3.0, 0.9), (2.2, 4.4, 0.8)):
            bb.ccube(head, (sgn * dx, top + dy, fz - 0.62), (sz, sz, 0.3), P['eye'], name='eye')
            bb.ccube(head, (sgn * dx, top + dy, fz - 0.78), (sz * 0.45, sz * 0.45, 0.1), P['eye_core'], name='eye_core')
        bb.ccube(head, (sgn * 4.25, top + 5.4, 0), (0.4, 1.8, 0.6), P['gold2'], name='earring')
        bb.ccube(head, (sgn * 4.3, top + 6.8, 0), (0.7, 0.7, 0.7), P['ruby'], name='earring_gem')
    bb.ccube(head, (0, top + 6.6, fz - 0.25), (4.8, 0.8, 0.5), P['beard'], name='moustache')
    bb.ccube(head, (0, top + 7.6, fz - 0.6), (6.6, 1.3, 1.4), P['beard'], name='beard_root')
    for dx in (-2.1, 0.0, 2.1):
        n = 5 if dx else 6
        for j in range(n):
            bb.ccube(head, (dx, top + 8.7 + j * 1.25, fz - 0.55 - j * 0.15), (1.6 - j * 0.12, 1.15, 1.25), P['beard'], name='braid')
            if j % 2 == 1:
                bb.ccube(head, (dx, top + 8.7 + j * 1.25, fz - 0.55 - j * 0.15), (1.75 - j * 0.12, 0.4, 1.4), P['gold2'], name='braid_ring')
        bb.ccube(head, (dx, top + 8.7 + n * 1.25 - 0.3, fz - 0.6 - n * 0.15), (0.9, 0.9, 0.9), P['gold2'], name='braid_end')


def spiked_collar(h, P):
    """A towering collar behind the head: black blades edged in gold, fanned up and out like a dark sun's rays."""
    cw, ch, cd = h.T['chest']
    y0 = h.top - 0.5
    for i in range(9):
        a = (i - 4) * 0.28
        L = 9.5 - abs(i - 4) * 1.1
        c = (math.sin(a) * (L / 2 + 2.0), y0 - math.cos(a) * (L / 2) - 1.0, cd / 2 + 1.4)
        bb.ccube(h.torso, c, (1.6, L, 0.6), P['black_gold'], rot=(0.25, 0, -a), pivot=(0, y0, cd / 2 + 1.4), name='collar_blade')
        tip = (math.sin(a) * (L + 2.0), y0 - math.cos(a) * L - 1.0, cd / 2 + 1.0)
        bb.ccube(h.torso, tip, (0.9, 1.4, 0.7), P['gold2'], rot=(0.25, 0, -a), name='collar_tip')


def ophan(r, parent, center, R, rim, eye, iris, axis, speed, name, n=30, thick=1.8):
    """An ophan (Ezekiel 1): a wheel whose rim is full of eyes, turning. A ring of gold plates round the centre in the
    plane square to its axis ('x' or 'z'), every third plate bearing an eye that looks out."""
    cx, cy, cz = center
    b = r.bone(name, parent, (cx, cy, cz), anim='spin', ax=0 if axis == 'x' else 2, speed=speed)
    for i in range(n):
        a = 2 * math.pi * i / n
        if axis == 'z':        # the wheel stands in the x-y plane, facing the front
            p = (cx + math.cos(a) * R, cy + math.sin(a) * R, cz)
            rot = (0, 0, a)
            size = (thick, 2 * math.pi * R / n + 0.15, thick)
            out = np.array([0, 0, -1.0])
        else:                  # the wheel stands in the y-z plane, edge-on to the front
            p = (cx, cy + math.sin(a) * R, cz + math.cos(a) * R)
            rot = (-a, 0, 0)
            size = (thick, 2 * math.pi * R / n + 0.15, thick)
            out = np.array([-1.0, 0, 0])
        bb.ccube(b, p, size, rim, rot=rot, name='ophan_rim')
        if i % 2 == 0:
            q = np.array(p) + out * (thick / 2 + 0.05)
            bb.ccube(b, tuple(q), (0.25, 1.6, 1.6) if axis == 'x' else (1.6, 1.6, 0.25), eye, name='ophan_eye')
            bb.ccube(b, tuple(q + out * 0.15), (0.12, 0.8, 0.8) if axis == 'x' else (0.8, 0.8, 0.12), iris, name='ophan_iris')
    return b


def broken_halo(r, h, center, R):
    """The sun of his face broken: a ring of tarnished gold segments with three gone, those beside the gaps pushed out
    of true, a black inner ring edged in crimson, crimson dripping from the breaks; the whole knocked askew."""
    cx, cy, cz = center
    hb = r.bone('halo_broken', h.head, (cx, cy, cz), rot=(0, 0, 0.38))
    gold = M('metal', '#b98a2e', edge_glow='#ff3a1a')
    black = M('metal', '#140a10', edge_glow='#ff2a2a')
    n, gone = 20, {3, 4, 12}
    rng = np.random.default_rng(13)
    for i in range(n):
        if i in gone:
            continue
        a = 2 * math.pi * i / n
        near = (i + 1) % n in gone or (i - 1) % n in gone
        rr = R + (rng.uniform(0.4, 1.2) if near else 0.0)
        tw = rng.uniform(-0.35, 0.35) if near else 0.0
        bb.ccube(hb, (cx + math.cos(a) * rr, cy + math.sin(a) * rr, cz + (0.4 if near else 0)), (2.4, 0.9, 0.6), gold,
                 rot=(tw, tw * 0.5, a + math.pi / 2), name='halo_seg')
        if i % 2 == 0:
            bb.ccube(hb, (cx + math.cos(a) * (R - 1.5), cy + math.sin(a) * (R - 1.5), cz + 0.2), (1.8, 0.5, 0.4), black,
                     rot=(0, 0, a + math.pi / 2), name='halo_inner')
        if near and math.sin(a) > -0.3:
            for k in range(3):
                bb.ccube(hb, (cx + math.cos(a) * rr, cy + math.sin(a) * rr + 0.9 + k * 0.8, cz), (0.35, 0.7, 0.3),
                         M('energy', '#c0101a'), name='halo_drip')


def fallen(r, h, P):
    """The fallen god's marks: black tears running from the six eyes of his mask and a crack across it; a chain
    about him from shoulder to hip and shackles on his wrists with broken chains hanging from them; pale blue fire of
    souls on his shoulders and about his crown, and souls drifting round him."""
    head, top = h.head, h.head_top
    fz = -4.0
    tear = M('void', '#050208')
    for sgn in (-1, 1):
        for (dx, dy, L) in ((1.4, 3.4, 3.6), (2.7, 3.0, 2.6), (2.2, 4.4, 2.0)):
            bb.ccube(head, (sgn * dx, top + dy + 0.5 + L / 2, fz - 0.72), (0.32, L, 0.18), tear, name='tear')
            bb.ccube(head, (sgn * dx, top + dy + 0.6 + L, fz - 0.74), (0.42, 0.42, 0.2), M('energy', '#c0101a'), name='tear_drop')
    for k in range(5):
        bb.ccube(head, (-3.4 + k * 1.5, top + 2.3 + (k % 2) * 0.5, fz - 0.62), (1.6, 0.22, 0.12), tear, rot=(0, 0, 0.5 - (k % 2)), name='mask_crack')
    iron = M('metal', '#3e3a44', accent='#7a7480', pattern='cracks')
    cw, ch, cd = h.T['chest']
    # a chain from the right shoulder down across the breast to the left hip, links turned each to the next
    p0, p1 = np.array([-cw / 2 + 0.5, h.top + 0.8, -cd / 2 - 1.3]), np.array([cw / 2 + 0.6, h.top + 10.5, -cd / 2 - 1.1])
    for k in range(9):
        p = p0 + (p1 - p0) * k / 8
        bb.ccube(h.torso, tuple(p), (1.3, 0.6, 0.5) if k % 2 else (0.5, 0.6, 1.2), iron, rot=(0, 0, 0.75), name='chain')
    for fore, sgn in ((h.fore_r, -1), (h.fore_l, 1)):
        x = fore.pivot[0]
        bb.ccube(fore, (x, h.wrist_y + 0.2, 0), (5.2, 1.2, 5.2), iron, name='shackle')
        hang = r.bone('chain_hang_' + ('r' if sgn < 0 else 'l'), fore, (x + sgn * 2.4, h.wrist_y + 0.6, 0), anim='sway', ax=0, amp=0.18,
                      speed=0.07, phase=sgn)
        for k in range(6):
            bb.ccube(hang, (x + sgn * 2.4, h.wrist_y + 1.2 + k * 1.05, 0), (0.5, 1.1, 1.0) if k % 2 else (1.0, 1.1, 0.5), iron, name='chain_link')
        bb.ccube(hang, (x + sgn * 2.4, h.wrist_y + 7.6, 0), (0.9, 0.8, 0.9), M('metal', '#2a2630', edge_glow='#7fe8ff'), name='chain_end')
    soul = M('energy', '#8ff0ff', alpha=0.85)
    for arm, sgn in ((h.arm_r, -1), (h.arm_l, 1)):
        fl = r.bone('soulfire_' + ('r' if sgn < 0 else 'l'), arm, (arm.pivot[0] + sgn * 1.0, h.top - 3.0, 0), anim='float', amp=0.5, speed=0.2,
                    phase=sgn)
        for k in range(4):
            bb.ccube(fl, (arm.pivot[0] + sgn * (1.0 + k * 0.3), h.top - 3.0 - k * 1.3, 0.3 * k), (1.6 - k * 0.3, 1.6, 1.6 - k * 0.3), soul,
                     name='soulfire')
    for k in range(6):
        a = k * math.pi / 3
        fl = r.bone(f'crownfire_{k}', head, (math.cos(a) * 3.2, top - 4.5, math.sin(a) * 3.2), anim='float', amp=0.4, speed=0.25, phase=k)
        bb.ccube(fl, (math.cos(a) * 3.2, top - 4.5, math.sin(a) * 3.2), (0.8, 1.6, 0.8), soul, name='crownfire')
    orbiters(r, h.torso, (0, h.top + 4, 0), [M('energy', '#8ff0ff'), M('energy', '#c8ffff')], count=10, radius=9, size=0.9, speed=-0.05,
             name='souls', bob=1.2)


@recipe
def villager_king_divine():
    r = Rig('villager_king_divine', height=45.0)       # the horns, the wings and the wheels stand above and round it
    r.translucent = True                                # the fly wings and the burning wings
    P = dict(
        gold=M('metal', '#e8b640', accent='#fff0b8', pattern='filigree'),
        gold2=M('metal', '#f0c24a'),
        black=M('metal', '#1d1823', accent='#e8b640', pattern='gold_lines'),
        black_gold=M('metal', '#1a1520', edge_glow='#ffcf5a'),
        linen=M('cloth', '#e6dfcf', accent='#9a1020', trim=2, pattern='runes', pattern_glow=True, glow_amount=0.7),
        linen_top=M('cloth', '#f7f3ea', accent='#e8b640', seam=True),
        sleeve=M('cloth', '#1a1420', accent='#e8b640', trim=2),
        sun=M('gem', '#ffd75a', glow=True),
        ruby=M('gem', '#ff3a2a', glow=True),
        eye=M('energy', '#ff5a1a'),
        eye_core=M('energy', '#ffe08a'),
        bolt=M('energy', '#fff2b0'),
        bolt_core=M('energy', '#ffffff'),
        haft=M('metal', '#2a2230'),
        beard=M('metal', '#f2ede2'),
        burning=M('energy', '#efe2bf', alpha=0.9, glow_amount=0.8),
        burning_tip=M('energy', '#5a0a12', alpha=0.95),
        covert=M('energy', '#c9963a', alpha=0.92),
        dark=M('metal', '#140f18', edge_glow='#ff3a2a'),
        dark_tip=M('energy', '#a0101c', alpha=0.95),
        fly=M('membrane', '#4a4a30', accent='#c79cff', alpha=0.5),
        vein=M('metal', '#120e14'),
        horn=M('horn', '#16121a', tip='#ffcf5a', glow=True),
        sclera=M('energy', '#fffaf0'),
        pupil=M('energy', '#ff3a10'),
        chitin=M('metal', '#16121a', accent='#e8b640', pattern='gold_lines'),
        edge=M('energy', '#ff3a1a'),
        wing=M('membrane', '#3a1418', accent='#ff5a3a', alpha=0.7),
        red_eye=M('energy', '#ff2a10'),
        white_blade=M('metal', '#eef1f8'), gold_edge=M('metal', '#fff3c4'),
        black_blade=M('metal', '#1a1520', accent='#ff3a1a', pattern='gold_lines'), fuller=M('energy', '#ffd75a'),
        grip=M('cloth', '#3a1a20'), tassel=M('cloth', '#c41a2a'), rainbow=M('rainbow', '#ffffff'),
    )
    P['haft'] = M('metal', '#f4efe2')
    h = Humanoid(r, 'large', skin='#f1dccb', accent='#e8b640', hover=3.0)
    h.body(top_mat=P['linen_top'], bottom_mat=P['linen'], legs_mat=P['linen'], boots_mat=P['gold2'], arms_mat=P['sleeve'],
           hands_mat=P['black'], neck=None)
    h.robe(P['linen'], flare=4.2)                      # a garment down to the foot (Revelation 1:13)
    open_sleeves(h, P['sleeve'], drop=7)
    cw, ch, cd = h.T['chest']
    # girt about the breast with a golden girdle; black-and-gold armour over the linen
    bb.ccube(h.torso, (0, h.top + 6.2, 0), (cw + 1.0, 1.6, cd + 1.0), P['gold'], name='girdle')
    bb.ccube(h.torso, (0, h.top - 0.2, 0), (9.0, 2.0, 8.0), P['gold'], name='gorget')
    for sgn in (-1, 1):
        bb.ccube(h.torso, (sgn * 3.4, h.top + 2.8, -cd / 2 - 0.5), (3.0, 5.4, 0.7), P['black'], rot=(0, 0, sgn * 0.1), name='breast_plate')
    bb.ccube(h.torso, (0, h.top + 3.0, -cd / 2 - 0.9), (3.4, 3.4, 0.5), P['gold2'], name='sun_rim')
    bb.ccube(h.torso, (0, h.top + 3.0, -cd / 2 - 1.2), (2.2, 2.2, 0.4), P['sun'], name='sun_core')
    for i in range(12):
        a = i * math.pi / 6
        bb.ccube(h.torso, (math.cos(a) * 2.5, h.top + 3.0 + math.sin(a) * 2.5, -cd / 2 - 0.8), (1.5, 0.4, 0.35), P['gold2'],
                 rot=(0, 0, a), name='sun_ray')
    bb.ccube(h.torso, (0, h.top + 4.0, cd / 2 + 0.35), (cw, 7.4, 0.7), P['black'], name='backplate')
    for i in range(10):
        a = (i - 4.5) * 0.32
        bb.ccube(h.hips, (math.sin(a) * 6.2, h.pelvis_top + 4.0, -math.cos(a) * 3.8), (2.4, 6.0, 0.5), P['black'] if i % 2 else P['gold'],
                 rot=(-0.18, -a, 0), name='skirt_plate')
    for fore, sgn in ((h.fore_r, -1), (h.fore_l, 1)):
        x = fore.pivot[0]
        bb.ccube(fore, (x, h.wrist_y - 1.6, 0), (5.6, 3.6, 5.6), P['gold'], name='bracer')
        bb.ccube(fore, (x + sgn * 3.0, h.wrist_y - 2.4, 0), (0.6, 4.0, 2.2), P['gold2'], rot=(0, 0, sgn * -0.5), name='bracer_fin')
        for k in range(4):
            bb.ccube(fore, (x - 1.5 + k * 1.0, h.wrist_y + 3.6, -1.8), (0.55, 2.4, 0.55), P['gold2'], rot=(-0.5, 0, 0), name='claw')
    h.belt(P['gold2'], buckle=P['ruby'])
    for arm, sgn in ((h.arm_r, -1), (h.arm_l, 1)):
        pauldron(h, arm, sgn, dict(plate=P['black'], plate2=P['black_gold'], plate_d=P['black'], gold2=P['gold2'], gem=P['ruby']),
                 tiers=3, spikes=3, big=1.3)
    # the head: hair white like wool (Daniel 7:9), eyes as a flame of fire, the fly's many eyes on a gold mask, the
    # horns of the storm god, a crown
    h.head_cube({'iris': '#ff6a2a', 'iris2': '#ffe08a', 'style': 'man_sharp', 'glow_eyes': True})
    h.hair('#f7f3ea', style='long', length=18, tip='#ffe9b0', bangs='parted')
    demon_face(h, P)
    h.horns(P['horn'], kind='dragon', length=24, spread=1.0, base=3.4)
    h.crown(M('metal', '#1a1418', edge_glow='#ff3a1a'), gems=P['ruby'], spikes=9, tall=4.0)
    # his countenance as the sun: a sun disc behind the head with a corona of rays; seven stars over him
    # (the user: more ominous, a supreme god twisted and fallen) the sun of his face cracked and knocked askew, a
    # corona of crimson about it; black tears from his eyes; chains on him; pale blue fire of souls
    broken_halo(r, h, (0, h.head_top + 3.0, 7.5), 8.0)
    h.halo(M('ring', '#c8302a', width=0.12, spikes=30), radius=10.5, y=h.head_top + 3.0, z=7.8, tilt=1.5, speed=0.008, name='corona')
    fallen(r, h, P)
    orbiters(r, h.head, (0, h.head_top - 6, 0), M('plane', '#fff4c0', shape='star', glow=True), count=7, radius=6.5, size=1.8,
             speed=0.03, name='seven_stars', bob=0.4)
    # the wheels within a wheel at his feet, their rims full of eyes, going where he goes (Ezekiel 1:15-21)
    ophan(r, h.root, (0, 17.0, 0.5), 8.6, P['gold2'], P['sclera'], P['pupil'], 'z', 0.03, 'ophan_a')
    ophan(r, h.root, (0, 17.0, 0.5), 7.8, P['gold'], P['sclera'], P['pupil'], 'x', -0.04, 'ophan_b')
    # six wings (Isaiah 6:2): with twain he covered his face (black wings rising beside the head), with twain he did
    # fly (great burning wings, full of eyes), with twain he covered his feet (the fly's wings, folded down)
    for sgn in (-1, 1):
        side = 'r' if sgn < 0 else 'l'
        feather_wing(r, h.torso, sgn, (sgn * 2.6, h.top + 1.0, cd / 2 + 1.4), 36.0, P['burning'], P['gold2'], P['covert'],
                     'wing_' + side, tip_mat=P['burning_tip'], eyes=(P['sclera'], P['pupil']))
        feather_wing(r, h.torso, sgn, (sgn * 2.0, h.top - 1.0, cd / 2 + 0.8), 15.0, P['dark'], P['gold2'], P['dark'],
                     'veil_' + side, rest=(0.35, 0.25, 1.05), amp=0.05, tip_mat=P['dark_tip'])
        fw = insect_wing(r, h.hips, sgn, (sgn * 2.4, h.pelvis_top + 2.0, cd / 2 + 0.6), 19.0, 7.0, P['fly'], P['vein'], 'fly_' + side)
        fw.rot = (0.45, sgn * -0.35, sgn * -1.15)
    # his five arms, one set at a time (KingDeeds.switchStance; KingRig shows the set by what is in his main hand):
    # the thunder clubs Yagrush and Aymur, the fly lord's scythe, the twin swords Seraph and Beelzebub, the thunder
    # spear, the great bow of rainbow light
    stance_arms(r, h)
    # lightning about him (Revelation 4:5) and the flies at his feet
    orbiters(r, h.torso, (0, h.top + 2, 0), [M('plane', '#ff4a2a', shape='star', glow=True), M('plane', '#9ff0ff', shape='star', glow=True)],
             count=8, radius=21, size=2.4, speed=0.02, name='lightnings')
    orbiters(r, h.hips, (0, h.pelvis_y1 + 6, 0), [M('void', '#0c0a08'), M('void', '#1a1610'), M('energy', '#c79cff')], count=24, radius=11,
             size=0.6, speed=0.13, name='flies', bob=1.6)
    return r


# --------------------------------------------------------------------------------------------- the first form
@recipe
def villager_king_regal():
    """(054) The villager king as he is on his throne: still a villager (the long nose, the single brow, the green
    eyes, the great white beard), but a king: a tall imperial crown with arches over a crimson cap and an orb and
    cross on top, an ermine mantle, a crimson robe worked with gold to the floor, a gold chain of office with the
    kingdom's sun, a long crimson cape bearing the royal arms, rings, and the sceptre at his belt."""
    r = Rig('villager_king_regal', height=40.0)
    GOLDK, CRIMSON, CRIMSON_D = '#e8b640', '#9a1626', '#5e0c18'
    P = dict(
        gold=M('metal', GOLDK, accent='#fff0b8', pattern='filigree'),
        gold2=M('metal', GOLDK),
        robe=M('cloth', CRIMSON, accent=GOLDK, trim=2, pattern='embroidery'),
        robe2=M('cloth', CRIMSON, accent=GOLDK, trim=2),
        cape=M('cloth', CRIMSON_D, accent=GOLDK, trim=2, pattern='embroidery'),
        ermine=M('cloth', '#f4f1ea', accent='#16141a', pattern='dots'),
        skin=M('skin', '#bf8d6c'),
        skin_d=M('skin', '#a8785a'),
        brow=M('cloth', '#e8e2d6'),
        beard=M('fur', '#efebe2'),
        ruby=M('gem', '#e8243a', glow=True),
        sapphire=M('gem', '#3a7aff', glow=True),
        emerald=M('gem', '#2ad070', glow=True),
        pearl=M('gem', '#f4f0ff'),
        velvet=M('cloth', CRIMSON, accent=GOLDK),
    )
    h = Humanoid(r, 'man', skin='#bf8d6c', accent=GOLDK)
    h.body(top_mat=P['robe2'], bottom_mat=P['robe'], legs_mat=P['robe'], boots_mat=P['gold2'], arms_mat=P['robe2'], hands_mat=P['skin'],
           neck=None)
    h.robe(P['robe'], flare=3.0)
    h.kimono_sleeves(P['robe2'], drop=4)
    # the villager's head: tall, the long nose, the single brow, green eyes, a great white beard
    head, top = h.head, h.head_top
    HW = 9.0
    bb.ccube(head, (0, top + 4.6, 0), (HW, 10.4, HW), P['skin'], name='villager_head')
    bb.ccube(head, (0, top + 7.0, -HW / 2 - 1.0), (2.2, 4.6, 2.2), P['skin_d'], name='villager_nose')
    bb.ccube(head, (0, top + 3.6, -HW / 2 - 0.12), (7.0, 1.1, 0.25), P['brow'], name='brow')
    for sgn in (-1, 1):
        bb.ccube(head, (sgn * 2.0, top + 4.8, -HW / 2 - 0.1), (1.8, 1.1, 0.2), M('cloth', '#f6f4ee'), name='eye_white')
        bb.ccube(head, (sgn * 1.6, top + 4.8, -HW / 2 - 0.16), (0.9, 1.1, 0.12), M('gem', '#2a9a4a'), name='eye_green')
    bb.ccube(head, (0, top + 9.6, -HW / 2 - 0.6), (8.4, 4.0, 1.6), P['beard'], name='beard')
    bb.ccube(head, (0, top + 12.6, -HW / 2 - 0.9), (6.0, 3.0, 1.4), P['beard'], name='beard_low')
    bb.ccube(head, (0, top + 14.8, -HW / 2 - 1.0), (3.4, 2.2, 1.2), P['beard'], name='beard_tip')
    for sgn in (-1, 1):
        bb.ccube(head, (sgn * 4.2, top + 7.6, -1.0), (1.2, 6.0, 5.0), P['beard'], name='whisker')
    # the imperial crown: a jewelled band, a crimson cap, two arches, an orb and cross
    ct = top - 0.6
    bb.ccube(head, (0, ct, 0), (HW + 1.2, 2.4, HW + 1.2), P['gold'], name='crown_band', faces={'top': None, 'bottom': None})
    bb.ccube(head, (0, ct - 2.4, 0), (HW - 0.8, 3.6, HW - 0.8), P['velvet'], name='crown_cap')
    for i, gem in enumerate((P['ruby'], P['sapphire'], P['emerald'], P['sapphire'])):
        a = i * math.pi / 2
        bb.ccube(head, (math.sin(a) * (HW / 2 + 0.7), ct, -math.cos(a) * (HW / 2 + 0.7)), (1.6, 1.6, 1.6), gem, name='crown_gem')
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        bb.ccube(head, (math.sin(a) * (HW / 2 + 0.6), ct - 1.9, -math.cos(a) * (HW / 2 + 0.6)), (1.2, 2.0, 1.2), P['gold2'], name='crown_fleur')
        bb.ccube(head, (math.sin(a) * (HW / 2 + 0.6), ct - 3.2, -math.cos(a) * (HW / 2 + 0.6)), (0.7, 0.7, 0.7), P['pearl'], name='crown_pearl')
    for rot in (0.0, math.pi / 2):
        for k in range(7):
            t = k / 6
            ang = math.pi * t
            px, py = math.cos(ang) * (HW / 2 + 0.2), ct - 1.0 - math.sin(ang) * 5.0
            if rot == 0.0:
                bb.ccube(head, (px, py, 0), (1.3, 1.3, 1.1), P['gold2'], name='crown_arch')
            else:
                bb.ccube(head, (0, py, px), (1.1, 1.3, 1.3), P['gold2'], name='crown_arch')
    bb.ccube(head, (0, ct - 6.6, 0), (2.4, 2.4, 2.4), P['gold'], name='crown_orb')
    bb.ccube(head, (0, ct - 8.6, 0), (0.7, 2.2, 0.7), P['gold2'], name='crown_cross')
    bb.ccube(head, (0, ct - 8.9, 0), (2.0, 0.7, 0.7), P['gold2'], name='crown_cross')
    # ermine mantle, the chain of office, the cape with the arms, rings, the sceptre at the belt
    h.fur_collar(P['ermine'], shoulders=True)
    cw, ch, cd = h.T['chest']
    for k in range(9):
        a = (k - 4) * 0.32
        bb.ccube(h.torso, (math.sin(a) * 3.4, h.top + 1.0 + (1 - math.cos(a)) * -6.0 + 3.2, -cd / 2 - 1.0), (1.0, 0.7, 0.5), P['gold2'],
                 rot=(0, 0, a), name='chain_link')
    sun_disc(h.torso, (0, h.top + 5.4, -cd / 2 - 1.2), 1.4, P['gold2'], P['ruby'], rays=12, depth=0.5)
    cape = h.cape(P['cape'], length=24, width=13)
    bb.ccube(cape, (0, h.top + 6.0, cd / 2 + 0.95), (5.6, 6.4, 0.3), P['gold'], name='arms_shield')
    sun_disc(cape, (0, h.top + 6.0, cd / 2 + 1.25), 1.4, P['gold2'], P['ruby'], rays=8, depth=0.3, normal_z=1)
    h.belt(P['gold'], buckle=P['ruby'])
    sb = r.bone('sceptre', h.hips, (-4.4, h.pelvis_top, -1.0), rot=(0.1, 0, 0.3))
    bb.ccube(sb, (-4.4, h.pelvis_top + 3.0, -1.0), (0.8, 9.0, 0.8), P['gold2'], name='sceptre_rod')
    bb.ccube(sb, (-4.4, h.pelvis_top - 2.0, -1.0), (1.8, 1.8, 1.8), P['sapphire'], name='sceptre_head')
    bb.ccube(sb, (-4.4, h.pelvis_top - 1.0, -1.0), (2.2, 0.6, 2.2), P['gold2'], name='sceptre_collar')
    for fore in (h.fore_r, h.fore_l):
        x = fore.pivot[0]
        bb.ccube(fore, (x, h.wrist_y + 1.0, -1.25), (1.0, 0.5, 0.3), P['ruby'], name='ring')
    return r

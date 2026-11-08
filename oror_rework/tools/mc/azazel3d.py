"""(056) Azazel, the rebel against god (アザゼル［神に叛きし者］), lord of the illagers, as a rig in king3d's manner.

Who he is (the Book of Enoch, Leviticus 16): the chief of the Watchers who came down, taught men to forge swords,
shields and breastplates and taught the arts of the metals; for it he was bound hand and foot and cast into the
darkness of the wilderness of Dudael, rough and jagged stones heaped on him; and he is the one the scapegoat is sent
out to. In the mod he reigns over the illagers from their city, far weaker than the villager king but with a blade
against him.

So: an illager become a fallen angel. The illagers' grey face, long nose and one heavy brow, its eyes burning
violet; a goat's curled horns (the scapegoat) and a crown of black forge-iron spikes; four wings of charred feathers
with ember edges, one pair torn; a black evoker's robe worked with bronze and violet runes under a bronze breastplate
and pauldrons (the breastplates he taught); the shackles he broke at wrists and ankles, their chains hanging; a broken
halo of black iron glowing like a cooling forge; the jagged stones of Dudael turning about his back; the king-slayer
blade (king_arms 'rebel_blade') in his right fist, a violet flame in his open left hand.
"""
import math
import numpy as np
from rig import Rig
from paint import M
from figure import Humanoid, orbiters
import bb
import king3d
from king3d import recipe, pauldron, feather_wing, SWORD_TILT
import king_arms as KA


def illager_head(h, P):
    """The illager's head: a long grey face, the long nose, one heavy dark brow drawn down in a scowl, deep sockets
    with violet burning eyes, a cheek split by a crack of ember (burnt in the fall)."""
    head, top = h.head, h.head_top
    HW = 8.6
    bb.ccube(head, (0, top + 4.8, 0), (HW, 10.8, HW), P['skin'], name='illager_head')
    bb.ccube(head, (0, top + 7.2, -HW / 2 - 1.1), (2.0, 4.8, 2.2), P['skin_d'], name='illager_nose')
    bb.ccube(head, (0, top + 3.4, -HW / 2 - 0.15), (7.4, 1.5, 0.35), P['brow'], rot=(0, 0, 0), name='brow')
    for sgn in (-1, 1):
        bb.ccube(head, (sgn * 2.6, top + 3.1, -HW / 2 - 0.25), (2.4, 0.7, 0.3), P['brow'], rot=(0, 0, sgn * -0.35), name='brow_scowl')
        bb.ccube(head, (sgn * 2.0, top + 4.8, -HW / 2 - 0.08), (2.0, 1.4, 0.2), P['socket'], name='eye_socket')
        bb.ccube(head, (sgn * 1.8, top + 4.8, -HW / 2 - 0.16), (1.0, 1.0, 0.14), P['eye'], name='eye_violet')
    bb.ccube(head, (0, top + 9.6, -HW / 2 - 0.1), (4.4, 0.6, 0.2), P['socket'], name='mouth')
    for k in range(4):
        bb.ccube(head, (3.0 - k * 0.5, top + 6.2 + k * 1.1, -HW / 2 - 0.12), (0.4, 1.2, 0.12), P['ember'], rot=(0, 0, 0.3 * (k % 2) - 0.15),
                 name='cheek_crack')
    # hair: lank and black, falling behind
    bb.ccube(head, (0, top + 6.0, HW / 2 + 0.6), (HW + 0.4, 9.0, 1.2), P['hair'], name='hair_back')
    for sgn in (-1, 1):
        bb.ccube(head, (sgn * (HW / 2 + 0.4), top + 5.0, 1.2), (0.8, 7.0, 5.0), P['hair'], name='hair_side')
    return HW


def iron_crown(h, P, HW):
    """A crown of black forge-iron: a band, spikes of uneven height, each glowing at the tip like iron from the fire."""
    head, top = h.head, h.head_top
    ct = top - 0.4
    bb.ccube(head, (0, ct, 0), (HW + 1.2, 2.0, HW + 1.2), P['iron'], name='crown_band', faces={'top': None, 'bottom': None})
    for i in range(7):
        a = i * 2 * math.pi / 7
        tall = 1.6 + (0.9 if i == 0 else (i % 2) * 0.7)
        x, z = math.sin(a) * (HW / 2 + 0.7), -math.cos(a) * (HW / 2 + 0.7)
        bb.ccube(head, (x, ct - 1.0 - tall / 2, z), (1.0, tall, 1.0), P['iron'], rot=(0, -a, 0), name='crown_spike')
        bb.ccube(head, (x, ct - 1.2 - tall, z), (0.6, 0.8, 0.6), P['ember'], name='crown_ember')
    bb.ccube(head, (0, ct + 0.1, -HW / 2 - 0.8), (1.8, 1.8, 0.6), P['violet_gem'], name='crown_gem')


def broken_iron_halo(r, h, P):
    """Half a halo of black iron behind his head, tilted, glowing at its broken ends like a cooling forge."""
    hb = r.bone('halo_iron', h.head, (0, h.head_top - 2.0, 6.2), anim='spin', ax=2, speed=0.004)
    R = 7.0
    for k in range(14):
        a = math.pi * 0.15 + k * math.pi * 0.9 / 13
        bb.ccube(hb, (math.cos(a) * R, h.head_top - 2.0 - math.sin(a) * R, 6.2), (1.6, 0.9, 0.7), P['iron'] if k % 4 else P['iron_glow'],
                 rot=(0, 0, -a + math.pi / 2), name='halo_seg')
    for a in (math.pi * 0.15, math.pi * 1.05):
        bb.ccube(hb, (math.cos(a) * R, h.head_top - 2.0 - math.sin(a) * R, 6.2), (1.0, 1.0, 1.0), P['ember'], name='halo_end')


def shackles(r, h, P):
    """The shackles Raphael bound him with, broken: on both wrists and both ankles, a length of chain hanging from each."""
    for fore, sgn in ((h.fore_r, -1), (h.fore_l, 1)):
        x = fore.pivot[0]
        bb.ccube(fore, (x, h.wrist_y + 0.2, 0), (5.0, 1.4, 5.0), P['iron'], name='shackle')
        hang = r.bone('chain_hang_' + ('r' if sgn < 0 else 'l'), fore, (x + sgn * 2.3, h.wrist_y + 0.6, 0), anim='sway', ax=0, amp=0.2,
                      speed=0.07, phase=sgn)
        for k in range(7):
            bb.ccube(hang, (x + sgn * 2.3, h.wrist_y + 1.2 + k * 1.05, 0), (0.5, 1.1, 1.0) if k % 2 else (1.0, 1.1, 0.5), P['iron'],
                     name='chain_link')
        bb.ccube(hang, (x + sgn * 2.3, h.wrist_y + 8.6, 0), (1.0, 0.9, 1.0), P['iron_glow'], name='chain_broken_end')
    for shin, sgn in ((h.shin_r, -1), (h.shin_l, 1)):
        x = shin.pivot[0]
        y = h.ankle_y - 1.2
        bb.ccube(shin, (x, y, 0), (5.0, 1.4, 5.0), P['iron'], name='ankle_shackle')


def scapegoat_sigil(bone, c, P):
    """A goat's skull in bronze on his breast: the brow, the long face, the curling horns, a violet light in the eyes."""
    x, y, z = c
    bb.ccube(bone, (x, y, z), (3.2, 2.6, 0.5), P['bronze'], name='sigil_skull')
    bb.ccube(bone, (x, y + 2.4, z), (1.8, 2.4, 0.5), P['bronze'], name='sigil_snout')
    for sgn in (-1, 1):
        bb.ccube(bone, (x + sgn * 0.8, y - 0.1, z - 0.3), (0.7, 0.7, 0.2), P['violet_gem'], name='sigil_eye')
        for k in range(5):
            a = k * 0.55
            bb.ccube(bone, (x + sgn * (1.8 + math.sin(a) * 1.6), y - 1.0 - math.cos(a) * 1.6 + 1.2, z), (0.7, 0.7, 0.45), P['bronze_d'],
                     name='sigil_horn')


@recipe
def azazel():
    r = Rig('azazel', height=42.0)                  # the horns, the crown spikes and the wings stand above
    r.translucent = True                             # the torn feathers and the flame
    P = dict(
        skin=M('skin', '#8d9597'), skin_d=M('skin', '#7a8285'),
        brow=M('cloth', '#1c1a1e'), socket=M('void', '#120c16'), eye=M('energy', '#b45cff'),
        hair=M('fur', '#16141a'),
        ember=M('energy', '#ff7a1a'),
        iron=M('metal', '#26222a', accent='#4a4450', pattern='cracks'),
        iron_glow=M('metal', '#2a2226', edge_glow='#ff7a1a'),
        violet_gem=M('gem', '#9a3cff', glow=True),
        bronze=M('metal', '#b8752a', accent='#f0c070', pattern='filigree'),
        bronze_d=M('metal', '#8a521c'),
        robe=M('cloth', '#1b181e', accent='#b8752a', trim=2, pattern='runes', pattern_glow=True, glow_amount=0.5),
        robe2=M('cloth', '#211d25', accent='#b8752a', trim=2),
        sleeve=M('cloth', '#18151b', accent='#9a3cff', trim=2),
        leather=M('cloth', '#2a1e18', accent='#b8752a'),
        horn=M('horn', '#5a4c3e', tip='#e8dcc4'),
        feather=M('energy', '#3a3436', alpha=0.95, glow_amount=0.0),
        feather_edge=M('metal', '#4a2a1a', edge_glow='#ff7a1a'),
        covert=M('energy', '#262226', alpha=0.95, glow_amount=0.0),
        feather_tip=M('energy', '#ff6a1a', alpha=0.9),
        torn=M('energy', '#2c2629', alpha=0.85, glow_amount=0.0),
        flame=M('energy', '#b45cff', alpha=0.85),
        flame_core=M('energy', '#f2dcff'),
        stone=M('metal', '#3a332c', accent='#5a5048', pattern='cracks'),
    )
    h = Humanoid(r, 'man', skin='#8d9597', accent='#b8752a')
    h.body(top_mat=P['robe2'], bottom_mat=P['robe'], legs_mat=P['robe'], boots_mat=P['iron'], arms_mat=P['sleeve'], hands_mat=P['skin'],
           neck=None)
    h.robe(P['robe'], flare=3.2)
    king3d.open_sleeves(h, P['sleeve'], drop=6)
    HW = illager_head(h, P)
    h.horns(P['horn'], kind='ram', length=15, spread=0.9, base=2.8)
    iron_crown(h, P, HW)
    broken_iron_halo(r, h, P)
    # the breastplates he taught men to make: bronze breast and back, pauldrons, bracers, a smith's belt
    cw, ch, cd = h.T['chest']
    h.breastplate(P['bronze'])
    scapegoat_sigil(h.torso, (0, h.top + 4.2, -cd / 2 - 1.3), P)
    bb.ccube(h.torso, (0, h.top + 4.0, cd / 2 + 0.4), (cw, 7.0, 0.7), P['bronze_d'], name='backplate')
    for arm, sgn in ((h.arm_r, -1), (h.arm_l, 1)):
        pauldron(h, arm, sgn, dict(plate=P['bronze'], plate2=P['bronze_d'], plate_d=P['iron'], gold2=P['bronze'], gem=P['violet_gem']),
                 tiers=2, spikes=3, big=1.0)
    for fore in (h.fore_r, h.fore_l):
        bb.ccube(fore, (fore.pivot[0], h.wrist_y - 2.0, 0), (5.2, 3.0, 5.2), P['bronze_d'], name='bracer')
    h.belt(P['leather'], buckle=P['bronze'])
    for k, (dx, L) in enumerate(((-3.0, 4.0), (-1.0, 5.0), (1.2, 3.6), (3.2, 4.4))):
        bb.ccube(h.hips, (dx, h.pelvis_top + 1.4 + L / 2, -h.T['chest'][2] / 2 - 0.8), (1.6, L, 0.4), P['leather'], name='belt_tab')
    shackles(r, h, P)
    # four wings of charred feathers, their edges like embers: a great pair, and a lower pair torn
    for sgn in (-1, 1):
        side = 'r' if sgn < 0 else 'l'
        feather_wing(r, h.torso, sgn, (sgn * 2.4, h.top + 1.2, cd / 2 + 1.2), 30.0, P['feather'], P['feather_edge'], P['covert'],
                     'wing_' + side, tip_mat=P['feather_tip'])
        feather_wing(r, h.torso, sgn, (sgn * 2.0, h.top + 5.0, cd / 2 + 1.0), 17.0, P['torn'], P['feather_edge'], P['covert'],
                     'wing_low_' + side, rest=(0.55, 0.45, 0.6), amp=0.08, tip_mat=P['feather_tip'])
    # the king-slayer blade in the right fist; a violet flame over the open left hand
    sb = r.bone('sword', h.fore_r, (h.fore_r.pivot[0], h.hand_y, -0.2), rot=(SWORD_TILT, 0, 0))
    KA.place(sb, 'rebel_blade', (h.fore_r.pivot[0], h.hand_y, -0.2), (0, 1, 0), (0, 0, 1), nm='rebel_blade')
    xl = h.fore_l.pivot[0]
    fl = r.bone('hand_flame', h.fore_l, (xl, h.hand_y + 1.5, -1.0), anim='float', amp=0.3, speed=0.25)
    for k in range(4):
        bb.ccube(fl, (xl + (k % 2) * 0.3 - 0.15, h.hand_y + 1.5 + k * 1.2, -1.0 - k * 0.15), (2.2 - k * 0.45, 1.5, 2.2 - k * 0.45),
                 P['flame'] if k else P['flame_core'], name='flame')
    # the jagged stones of Dudael heaped on him once, turning about his back now
    orbiters(r, h.torso, (0, h.top + 6, 9.0), [P['stone'], M('metal', '#2a2520', accent='#4a4038', pattern='cracks')], count=7, radius=12,
             size=2.2, speed=0.012, name='dudael_stones', bob=0.8)
    orbiters(r, h.hips, (0, h.pelvis_y1 + 6, 0), [P['ember'], M('energy', '#ffb04a')], count=12, radius=9, size=0.45, speed=0.06,
             name='embers', bob=1.4)
    return r

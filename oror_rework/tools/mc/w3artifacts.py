"""3D focus and charm relics: archetypes chosen by the item's name, coloured with the character's palette.
Same toolkit and conventions as w3designs (u up, v across, w depth, texels; u = 0 where the hand holds).
hold: 'sword' (staffs, scabbards, feathers), 'fist' (hanging pendants / talismans, +u runs down the arm),
'palm' (objects carried upright in the hand)."""
import math
from forge3d import W3D
from paint import M
from w3parts import (Mt, octo, grip, collar, cone, gem, crystal, spikes, chain, halo, disc, side_plate, front_plate, star, sigil,
                     feather_wing, bat_wing, leaf, ring3d, orbit, coil)
from relic_icons import PAL

def mats(p, s, g):
    return Mt('metal', p), Mt('metal', s), Mt('energy', g)

# ------------------------------------------------------------------------------------------- archetypes
def a_orb(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    octo(w, -6, 8, 2.4, S, 'stem')
    cone(w, -12, 4, 4.0, 2.4, S, steps=2, name='base')
    for k in range(4):
        c = w.group(-1, 0, 0, rot=(90 * k + 45, 0, 0), name=f'claw{k}')
        c.box(3, 4.5, 0, 7, 2, 2, S.b(), rot=(0, 0, 25), name='c1')
        c.box(8.5, 5.5, 0, 4, 2, 2, P.b(), rot=(0, 0, -25), name='c2')
    w.box(6, 0, 0, 9, 9, 9, M('gem', g, glow=True), name='orb')
    w.box(6, 0, 0, 8, 8, 8, M('gem', p, glow=True), rot=(45, 45, 0), name='orb2')
    gem(w, 6, 0, 0, 3, '#ffffff', name='core')
    halo(w, 6, 8.5, 7.3, S, d=0.5, name='band', tilt=20)

def a_cube(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    w.box(4, 0, 0, 10, 10, 10, M('gem', g, glow=True), rot=(45, 35, 0), name='cube')
    ring3d(w, 4, 8, 6, (3, 3, 3), S, name='nodes')
    halo(w, 4, 10, 9, G, spokes=0, name='orbit', d=0.5, tilt=30)
    octo(w, -6, 6, 2.0, S, 'stem')

def a_book(w, p, s, g, kind=None, **o):
    P, S, G = mats(p, s, g)
    if kind == 'scroll':
        octo(w.group(0, 0, 0, rot=(0, 0, 90), name='rod'), 0, 16, 1.6, S, 'rod')
        sp = front_plate(w, -18, 2, -8, 8)
        sp.poly([(-17, -6.5), (0, -6.5), (0, 6.5), (-17, 6.5)], Mt('cloth', '#f2e4c0').p(d=0.5), 2)
        for k in range(4):
            sp.stroke([(-3 - k * 3.5, -4.5), (-3 - k * 3.5, 4.5)], 0.8, G.p(d=0.5), 3)
        gem(w, 0, 9, 0, 3, g, name='end')
        return
    if kind in ('page', 'bookmark'):
        sp = front_plate(w, -2, 22, -8, 8)
        if kind == 'page':
            sp.poly([(0, -7), (20, -6), (21, 6), (1, 7)], Mt('cloth', '#fbf5e6').p(d=0.4), 2)
            for k in range(5):
                sp.stroke([(4 + k * 3, -4.5), (4 + k * 3, 4.5)], 0.8, G.p(d=0.5), 3)
            halo(w, 10, 13, 11.8, G, spikes_n=8, name='halo', d=0.3)
        else:
            sp.poly([(0, -2.5), (19, -2.5), (21, 0), (19, 2.5), (0, 2.5)], S.p(d=0.5), 2)
            star(sp, 14, 0, 2.2, 1, 5, G.p(d=0.75), 3)
            w.box(-2, 0, 0, 3, 3, 3, M('gem', g, glow=True), rot=(45, 0, 45), name='charm')
        return
    w.box(4, 0, 0, 18, 14, 5, S.b(), name='cover')
    w.box(4, 0.5, 0, 16, 13, 4, M('cloth', '#f6eedc', pattern='stripes', accent='#e0d4b8'), name='pages')
    for du in (-8, 8):
        for dv in (-6.5, 6.5):
            w.box(4 + du, dv, 0, 3, 2, 6, P.b(), name='corner')
    em = front_plate(w, -6, 14, -8, 8, w=2.6)
    sigil(em, 4, 0, 5.5, P.p(d=0.5), G.p(d=0.75), 3, n=5)
    w.box(4, 7.6, 0, 4, 1, 6, P.b(), name='clasp')
    gem(w, 4, 7.8, 0, 2, g, name='clasp_gem')

def a_mirror(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    grip(w, -14, -2, 1.6, S, bands=(-12, -4), band_mt=P)
    p_ = front_plate(w, -4, 26, -15, 15)
    p_.ring(11, 0, 12, 9.5, P.p(d=1.5, d0=0.75, bev=2), 2)
    p_.ell(11, 0, 9.5, 9.5, Mt('metal', '#e8f0ff').p(d=0.5), 1)
    p_.ell(11, -2, 5, 3, G.p(d=0.75), 3)
    for k in range(8):
        a = 2 * math.pi * k / 8
        p_.poly([(11 + math.cos(a - 0.12) * 11.5, math.sin(a - 0.12) * 11.5), (11 + math.cos(a) * 14.5, math.sin(a) * 14.5),
                 (11 + math.cos(a + 0.12) * 11.5, math.sin(a + 0.12) * 11.5)], S.p(d=1.0), 1)
    gem(w, 23.5, 0, 0, 3, g, name='top_gem')

def a_crown(w, p, s, g, kind=None, **o):
    P, S, G = mats(p, s, g)
    halo(w, 0, 8, 6.2, P, d=1.5, name='band')
    halo(w, 2, 8.4, 6.6, S, d=0.75, name='band2')
    if kind == 'horn':
        for sgn in (-1, 1):
            h = w.group(2, sgn * 6, 0, rot=(0, 0, sgn * -30), name=f'horn{sgn}')
            h.box(4, 0, 0, 8, 3, 3, S.b(), name='h1')
            h2 = h.group(8, 0, 0, rot=(0, 0, sgn * 40), name=f'horn2{sgn}')
            h2.box(3, 0, 0, 6, 2, 2, P.b(), name='h2')
            h2.box(6.5, 0, 0, 2, 1, 1, G.b(), name='h3')
    elif kind == 'leaf':
        for k in range(8):
            g_ = w.group(2, 0, 0, rot=(45 * k, 0, 0), name=f'lf{k}')
            lp = g_.plate(-2, 10, -4, 4, v=7, U=(1, 0, 0), V=(0, 0, 1))
            leaf(lp, 0, 0, 0, 9, 2.6, Mt('cloth', '#8fe060').p(d=0.5), 2)
        ring3d(w, 3, 7.5, 4, (3, 3, 3), Mt('cloth', '#ffd0e8'), name='blossom')
    else:
        spikes(w, 2.5, 8, 7.2, 4, 2, S, tilt=68, name='crownpt')
        for k in range(8):
            a = math.radians(360 * k / 8)
            gem(w, 8.5, math.cos(a) * 8.6, math.sin(a) * 8.6, 2, g, name=f'tipgem{k}', facet=False)
        ring3d(w, 1, 8.2, 8, (2, 2, 2), M('gem', g, glow=True), phase=22.5, name='gems')
    gem(w, 2, 0, 8.6, 3, g, name='front_gem')

def a_ring(w, p, s, g, kind=None, **o):
    P, S, G = mats(p, s, g)
    p_ = front_plate(w, -10, 10, -10, 10)
    p_.ring(0, 0, 9, 6, P.p(d=1.75, d0=1.0, bev=1.5), 2)
    p_.ring(0, 0, 7.8, 7.0, G.p(inset=0.25), 3)
    if kind == 'calc':
        for k in range(6):
            a = 2 * math.pi * k / 6
            w.box(math.cos(a) * 12, math.sin(a) * 12, 0, 3, 3, 3, M('gem', g, glow=True), rot=(45, 45, 0), name=f'bit{k}')
    w.box(9.5, 0, 0, 4, 5, 5, S.b(), name='setting')
    gem(w, 12, 0, 0, 4, g, name='stone')

def a_bracelet(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    halo(w, 0, 9, 6, P, d=2.0, name='band')
    ring3d(w, 0, 9, 10, (3, 2, 3), S, name='studs')
    gem(w, 0, 0, 9.8, 4, g, name='stone')

def a_card(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    p_ = front_plate(w, -1, 25, -9, 9)
    p_.poly([(0, -8), (24, -8), (24, 8), (0, 8)], S.p(d=0.75), 1)
    p_.poly([(1.5, -6.5), (22.5, -6.5), (22.5, 6.5), (1.5, 6.5)], Mt('cloth', '#fbf6ea').p(d=1.0), 2)
    sigil(p_, 12, 0, 5.5, P.p(up=0.25), G.p(up=0.5), 3, n=8)
    star(p_, 12, 0, 2.6, 1.0, 4, G.p(up=0.75), 5)

def a_talisman(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    w.box(-1, 0, 0, 3, 3, 3, M('gem', g, glow=True), rot=(45, 0, 45), name='knot')
    p_ = front_plate(w, -1, 30, -6, 6)
    p_.poly([(1, -5), (29, -5), (29, 5), (1, 5)], Mt('cloth', '#f6efe0').p(d=0.4), 2)
    p_.stroke([(5, 0), (25, 0)], 1.2, Mt('cloth', '#c02a3a').p(up=0.2), 3)
    for u in (8, 14, 20):
        p_.stroke([(u, -3), (u + 2, 3)], 0.9, Mt('cloth', '#c02a3a').p(up=0.2), 3)
    sigil(p_, 24, 0, 3.5, S.p(up=0.25), G.p(up=0.5), 4, n=5)

def a_feather(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    p_ = front_plate(w, -4, 40, -10, 10)
    p_.stroke([(-3, 0), (38, 0)], 1.2, S.p(d=0.75), 3)
    p_.poly([(4, 0.2), (12, 7.5), (26, 8), (36, 3), (39, 0.2)], Mt('cloth', p).p(d=0.75, d0=0.4, bev=2), 2)
    p_.poly([(6, -0.2), (14, -6.5), (28, -6.5), (36, -2), (39, -0.2)], Mt('cloth', s).p(d=0.75, d0=0.4, bev=2), 2)
    for u in range(10, 36, 5):
        p_.stroke([(u, 0), (u + 4, 5)], 0.6, G.p(inset=0.25), 4)
    gem(w, -3, 0, 0, 3, g, name='quill_gem')

MOTIF = {}

def a_pendant(w, p, s, g, motif=None, **o):
    """Hangs from the hand: +u runs down."""
    P, S, G = mats(p, s, g)
    chain(w, [(1 + k * 2.2, 0, 0) for k in range(5)], S, size=1)
    p_ = front_plate(w, 8, 32, -11, 11)
    c = 21
    if motif == 'feather':
        p_.poly([(10, 0), (16, 5), (28, 4), (32, 0), (28, -4), (16, -5)], Mt('cloth', p).p(d=0.75), 2)
        p_.stroke([(10, 0), (31, 0)], 0.8, G.p(up=0.25), 3)
    elif motif == 'wing':
        bat_wing(p_, 11, 0, 0.0, 20, Mt('metal', p).p(d=0.75), 2, fingers=4)
    elif motif == 'horn':
        p_.poly([(10, -3), (14, -4), (24, -2), (32, 3), (24, 1.5), (14, 1)], Mt('metal', p).p(d=1.25, d0=0.5, bev=2), 2)
    elif motif == 'scale':
        for k in range(3):
            p_.ell(13 + k * 6, 0, 4, 5.5 - k, Mt('metal', p if k % 2 == 0 else s).p(d=1.0), 2 + k)
    elif motif == 'claw':
        for v in (-4, 0, 4):
            p_.poly([(10, v - 1.2), (22, v - 1.5), (30, v + 1.5), (22, v + 0.8), (10, v + 1.2)], Mt('metal', p).p(d=0.75), 2)
    elif motif == 'heart':
        p_.ell(18, -3.5, 5, 4.5, Mt('metal', p).p(d=1.25), 2)
        p_.ell(18, 3.5, 5, 4.5, Mt('metal', p).p(d=1.25), 2)
        p_.poly([(18, -8), (31, 0), (18, 8)], Mt('metal', p).p(d=1.25), 2)
        p_.ell(19, 0, 3.5, 3.5, G.p(d=1.75), 3)
    elif motif == 'flower':
        for k in range(6):
            a = 2 * math.pi * k / 6
            p_.ell(c + math.cos(a) * 5, math.sin(a) * 5, 3.6, 3.6, Mt('cloth', p).p(d=0.75), 2)
        p_.ell(c, 0, 3, 3, G.p(d=1.25), 3)
    else:
        p_.ell(c, 0, 9, 7.5, S.p(d=1.25, d0=0.75, bev=1.5), 2)
        p_.ell(c, 0, 6.5, 5, Mt('gem', g).p(d=1.75), 3)
    w.box(10, 0, 0, 3, 4, 4, P.b(), name='bail')

def a_badge(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    p_ = front_plate(w, -12, 12, -11, 11)
    p_.sym([(-11, 0.1), (-6, 6), (2, 9), (10, 9), (11, 0.1)], S.p(d=1.25, d0=0.75, bev=1.5), 2)
    p_.sym([(-9, 0.1), (-5, 4.6), (2, 7), (8.5, 7), (9.5, 0.1)], P.p(d=1.5), 3)
    star(p_, 2, 0, 5, 2, 5, G.p(up=0.5), 4, rot=math.pi / 2)
    for s_ in (-1, 1):
        r = w.group(-10, s_ * 4, -1, rot=(0, 0, s_ * 25), name=f'rib{s_}')
        r.box(-4, 0, 0, 8, 3, 1, Mt('cloth', '#c02a3a').b(), name='ribbon')

def a_staff(w, p, s, g, head=None, **o):
    P, S, G = mats(p, s, g)
    grip(w, -26, 34, 1.8, S, bands=(-20, 0, 20), band_mt=P)
    cone(w, -30, 4, 2.4, 1.6, P, steps=2, name='butt')
    cone(w, 34, 4, 2.0, 3.6, P, steps=2, name='cup')
    if head == 'coral':
        for k in range(5):
            c = w.group(38, 0, 0, rot=(72 * k, 0, 0), name=f'cor{k}')
            c.box(4, 2, 0, 8, 2, 2, Mt('metal', '#ff8f80').b(), rot=(0, 0, -30), name='c1')
            c.box(9, 5, 0, 5, 2, 2, Mt('metal', '#ffb0a0').b(), rot=(0, 0, 10), name='c2')
        gem(w, 44, 0, 0, 4, '#ffffff', name='pearl')
    elif head == 'flower' or head == 'seed':
        for k in range(6):
            c = w.group(40, 0, 0, rot=(60 * k, 0, 0), name=f'pet{k}')
            c.box(1, 4, 0, 4, 6, 2, Mt('cloth', '#ffd0e8').b(), rot=(0, 0, -35), name='petal')
        gem(w, 41, 0, 0, 4, g, name='seed')
    elif head == 'crystal':
        for k, r in enumerate(((0, 0, 0), (0, 0, 25), (0, 0, -25), (30, 0, 15))):
            crystal(w, 42, 0, 0, 10 - k * 2, 3, g, rot=r, name=f'cr{k}')
    elif head == 'cross':
        p_ = front_plate(w, 36, 62, -10, 10)
        p_.poly([(38, -2), (60, -2), (60, 2), (38, 2)], P.p(d=1.25), 2)
        p_.poly([(48, -8), (52, -8), (52, 8), (48, 8)], P.p(d=1.25), 2)
        p_.ring(50, 0, 6.5, 5.2, G.p(d=0.75), 3)
        gem(w, 50, 0, 0, 3, g, name='center')
    elif head == 'crown':
        ring3d(w, 40, 4, 6, (6, 2, 2), P, name='crownpts')
        gem(w, 44, 0, 0, 5, g, name='crown_gem')
        halo(w, 44, 8, 6.8, G, spikes_n=8, name='sun', d=0.5)
    else:
        gem(w, 42, 0, 0, 6, g, name='head_gem')
        halo(w, 42, 7, 5.8, P, d=0.75, name='head_ring')

def a_bottle(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    glass = M('gem', '#eef8ff', glow=False, alpha=0.45)
    w.box(2, 0, 0, 10, 10, 10, M('energy', g), name='liquid')
    w.box(4, 0, 0, 14, 12, 12, glass, name='glass')
    w.box(4, 0, 0, 12, 13, 13, glass, rot=(45, 0, 0), name='glass2')
    octo(w, 13, 4, 2.4, Mt('gem', '#eef8ff'), 'neck')
    w.box(16, 0, 0, 3, 5, 5, S.b(), name='cork')
    w.box(4, 0, 6.8, 6, 6, 1, M('cloth', '#f2e4c0'), name='label')

def a_chalice(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    cone(w, -12, 3, 5.0, 3.0, S, steps=1, name='foot')
    octo(w, -5, 12, 1.6, S, 'stem')
    gem(w, -4, 0, 0, 3, g, name='knop')
    cone(w, 1, 12, 3.0, 7.5, P, steps=4, name='cup')
    halo(w, 13, 7.6, 6.4, S, d=0.75, name='lip')
    disc(w, 12, 6.4, 6.4, Mt('energy', g), d=0.5)

def a_furnace(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    w.box(0, 0, 0, 14, 14, 12, S.b(), name='body')
    w.box(0, 0, 6.2, 8, 8, 1, M('energy', g), name='fire')
    for k in range(3):
        w.box(-2 + k * 2.6, 0, 6.8, 1, 9, 1, P.b(), name='grate')
    octo(w, 10, 8, 2.4, P, 'chimney')
    crystal(w, 16, 0, 0, 5, 2, g, name='flame')
    for s_ in (-1, 1):
        w.box(-6, s_ * 7.5, 0, 3, 2, 10, P.b(), name='foot')

def a_clock(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    p_ = front_plate(w, -12, 12, -12, 12)
    p_.ell(0, 0, 11, 11, P.p(d=1.5, d0=0.75, bev=1.5), 1)
    p_.ell(0, 0, 9, 9, Mt('cloth', '#fbf6ea').p(d=1.0), 2)
    for k in range(12):
        a = 2 * math.pi * k / 12
        p_.dot(math.cos(a) * 7.6, math.sin(a) * 7.6, S.p(up=0.25), 3)
    p_.stroke([(0, 0), (6, 1.5)], 0.9, S.p(up=0.5), 4)
    p_.stroke([(0, 0), (-1, -5)], 0.9, G.p(up=0.5), 4)
    gem(w, 12.5, 0, 0, 3, g, name='crown')
    for k in range(3):
        gear = w.group(-6 + k * 6, 10, -2, rot=(0, 0, 20 * k), name=f'gear{k}')
        halo(gear.group(0, 0, 0, rot=(0, 90, 0), name='g'), 0, 3.5, 1.5, S, spikes_n=8, name='gear', d=0.5)

def a_dice(w, p, s, g, **o):
    for k, (u, v, r) in enumerate(((2, -4, (20, 30, 10)), (5, 5, (-15, 50, 30)))):
        w.box(u, v, 0, 9, 9, 9, M('metal', p if k == 0 else s, pattern='dots', accent='#202020'), rot=r, name=f'die{k}')
    gem(w, 12, 0, 0, 3, g, name='spark')

def a_mask(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    p_ = front_plate(w, -12, 12, -11, 11)
    p_.ell(0, 0, 11, 9.5, P.p(d=1.75, d0=1.0, bev=2), 2)
    p_.poly([(-10, 0), (10, 0), (9, 8.5), (0, 9.5), (-8, 7)], S.p(d=2.0, d0=1.25, bev=2), 3)
    for s_ in (-1, 1):
        p_.poly([(2, s_ * 5), (4.5, s_ * 3.3), (2, s_ * 1.6), (-0.5, s_ * 3.3)], G.p(inset=0.5), 4)
    p_.stroke([(-5, -3), (-6.5, 0), (-5, 3)], 0.9, Mt('metal', '#7a1028').p(inset=0.25), 4)
    for s_ in (-1, 1):
        h = w.group(9, s_ * 7, 0, rot=(0, 0, s_ * -30), name=f'tip{s_}')
        h.box(3, 0, 0, 6, 2, 2, S.b(), name='t')

def a_box(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    w.box(0, 0, 0, 12, 14, 12, M('metal', p, pattern='stripes', accent=s), name='box')
    w.box(7, 0, 0, 3, 15, 13, S.b(), name='lid')
    w.box(0, 0, 0, 13, 3, 13, M('cloth', '#ff6fa0'), name='ribbon_v')
    w.box(0, 0, 0, 13, 15, 3, M('cloth', '#ff6fa0'), name='ribbon_w')
    sp = front_plate(w, 4, 22, -8, 8)
    star(sp, 14, 0, 7, 3, 5, G.p(d=0.75), 2, rot=-math.pi / 2)

def a_eye(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    w.box(2, 0, 0, 12, 12, 12, M('metal', '#f6f2f0'), name='eyeball')
    w.box(2, 0, 0, 11, 13, 11, M('metal', '#f6f2f0'), rot=(45, 0, 0), name='eyeball2')
    p_ = front_plate(w, -6, 10, -8, 8, w=6.8)
    p_.ell(2, 0, 4.2, 4.2, G.p(d=0.75), 2)
    p_.ell(2, 0, 2, 1, Mt('metal', '#100810').p(d=1.0), 3)
    halo(w, 2, 9, 7.6, P, spikes_n=8, name='frame', d=0.75, tilt=90)
    octo(w, -8, 6, 1.6, S, 'stem')

def a_stele(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    w.box(4, 0, 0, 22, 14, 5, M('rock', p), name='stone')
    w.box(16, 0, 0, 3, 10, 5, M('rock', p), name='cap')
    w.box(-8, 0, 0, 3, 18, 8, M('rock', s), name='plinth')
    p_ = front_plate(w, -6, 16, -7, 7, w=2.6)
    for k in range(4):
        p_.stroke([(12 - k * 4, -4), (12 - k * 4, 4)], 0.9, G.p(d=0.5), 2)
    sigil(p_, 2, 0, 3.4, S.p(d=0.5), G.p(d=0.5), 3, n=5)

def a_shell(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    gem(w, 2, 0, 0, 6, g, name='core')
    for k in range(6):
        c = w.group(2, 0, 0, rot=(60 * k, 0, 0), name=f'plate{k}')
        hp = c.plate(-6, 6, -5, 5, v=6.5, U=(1, 0, 0), V=(0, 0, 1))
        pts = [(math.cos(math.pi / 3 * j) * 5, math.sin(math.pi / 3 * j) * 4.5) for j in range(6)]
        hp.poly(pts, P.p(d=0.75), 2)
        hp.ell(0, 0, 1.5, 1.5, G.p(d=1.0), 3)
    halo(w, 2, 10, 9, S, d=0.5, name='rim')

def a_catalyst(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    for k, (r, c) in enumerate((((0, 0, 0), '#ff8fe0'), ((0, 0, 30), '#7fe0ff'), ((0, 0, -30), '#ffe07f'), ((40, 20, 10), '#9fff9f'))):
        crystal(w, 4, 0, 0, 12 - k * 2, 4, c, rot=r, name=f'shard{k}')
    ring3d(w, -2, 6, 6, (3, 2, 2), S, name='cage')
    octo(w, -6, 6, 2.0, P, 'base')

def a_tool(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    grip(w, -14, 8, 2.0, Mt('metal', '#5a3a22'), bands=(-12, 6), band_mt=P)
    w.box(14, 0, 0, 14, 4, 3, S.b(), name='shaft')
    for s_ in (-1, 1):
        j = w.group(22, s_ * 3, 0, rot=(0, 0, s_ * -20), name=f'jaw{s_}')
        j.box(3, 0, 0, 6, 3, 3, P.b(), name='jaw')
    halo(w.group(16, 0, 0, rot=(0, 90, 0), name='gearg'), 0, 4, 2, P, spikes_n=8, name='gear', d=0.5)
    gem(w, 10, 0, 2, 2, g, name='lens')

def a_scabbard(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    p_ = front_plate(w, -4, 64, -6, 6)
    p_.sym([(-2, 4.2), (50, 3.8), (60, 2.2), (62, 0.1)], S.p(d=1.75, d0=1.0, bev=2), 2)
    for u in (8, 30, 52):
        p_.poly([(u, -4.6), (u + 3, -4.6), (u + 3, 4.6), (u, 4.6)], P.p(up=0.25), 3)
    p_.stroke([(12, 0), (48, 0)], 0.9, G.p(inset=0.25), 4)
    w.box(-4, 0, 0, 3, 9, 6, P.b(), name='koiguchi')
    t = w.group(10, 4, 0, rot=(0, 0, 150), name='sageo')
    t.box(5, 0, 0, 10, 1, 1, Mt('cloth', g).b(), name='cord')

def a_armillary(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    octo(w, -8, 8, 1.6, S, 'stem')
    cone(w, -13, 3, 4.0, 2.0, S, steps=1, name='foot')
    gem(w, 6, 0, 0, 5, g, name='star')
    for k, rot in enumerate(((0, 0, 0), (0, 60, 0), (0, -60, 0), (90, 30, 0))):
        halo(w.group(6, 0, 0, rot=rot, name=f'arm{k}'), 0, 9 - k * 0.6, 8.2 - k * 0.6, P if k % 2 == 0 else S, d=0.5, name='ring')

def a_hourglass(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    glass = M('gem', '#eef8ff', glow=False, alpha=0.45)
    for s_ in (-1, 1):
        w.box(s_ * 9, 0, 0, 2, 14, 14, P.b(), name='plate')
    for s_ in (-1, 1):
        for t in (-1, 1):
            w.box(0, s_ * 6, t * 6, 18, 2, 2, S.b(), name='post')
    w.box(-4, 0, 0, 6, 9, 9, glass, rot=(45, 0, 0), name='bulb_lo')
    w.box(4, 0, 0, 6, 9, 9, glass, rot=(45, 0, 0), name='bulb_hi')
    w.box(-5, 0, 0, 3, 6, 6, M('energy', g), name='sand_lo')
    w.box(3, 0, 0, 2, 4, 4, M('energy', g), name='sand_hi')

def a_fruit(w, p, s, g, **o):
    w.box(-6, 0, 0, 8, 2, 2, M('wood', '#8a6a48'), rot=(0, 0, 10), name='twig')
    gem(w, 2, 0, 0, 9, g, name='fruit')
    w.box(2, 0, 0, 8, 8, 8, M('gem', '#ffffff', glow=True), rot=(45, 45, 0), name='fruit_core')
    for k, a in enumerate((40, -40, 150)):
        lp = front_plate(w.group(7, 0, 0, rot=(0, 0, a), name=f'leaf{k}'), -2, 12, -4, 4)
        leaf(lp, 0, 0, 0, 10, 3, Mt('cloth', '#7fd060').p(d=0.5), 2)

def a_horn(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    for i in range(6):
        t = i / 5
        g_ = w.group(-6 + 8 * i, 4 * t * t, 0, rot=(0, 0, -20 * t), name=f'seg{i}')
        octo(g_, 0, 8, 4.5 - 2.6 * t, P if i % 2 == 0 else S, f'seg{i}')
    halo(w, 38, 5.5, 3, G, name='bell', d=0.75)
    w.box(-12, 0, 0, 4, 4, 4, S.b(), name='mouthpiece')
    t = w.group(4, 4, 0, rot=(0, 0, 160), name='strap')
    t.box(6, 0, 0, 12, 1, 2, Mt('cloth', '#7a4a2a').b(), name='strap')

def a_gauntlet(w, p, s, g, **o):
    P, S, G = mats(p, s, g)
    cone(w, -16, 14, 6.0, 5.0, S, steps=2, name='bracer')
    w.box(3, 0, 0, 10, 13, 8, P.b(), name='hand')
    for k, v in enumerate((-4.5, -1.5, 1.5, 4.5)):
        f = w.group(8, v, 0, rot=(0, -30, 0), name=f'f{k}')
        f.box(3, 0, 0, 6, 2, 4, S.b(), name='finger')
    gem(w, 3, 0, 4.5, 4, g, name='stone')

ARCH = {k[2:]: v for k, v in globals().items() if k.startswith('a_')}

RULES = [('詠譜', 'book', 'palm', {'kind': 'page'}), ('鞘', 'scabbard', 'sword', {}), ('天球儀', 'armillary', 'palm', {}), ('砂時計', 'hourglass', 'palm', {}), ('神実', 'fruit', 'palm', {}),
         ('演算環', 'ring', 'palm', {'kind': 'calc'}), ('角冠', 'crown', 'palm', {'kind': 'horn'}), ('若葉冠', 'crown', 'palm', {'kind': 'leaf'}),
         ('冠', 'crown', 'palm', {}), ('王笏', 'staff', 'sword', {'head': 'crown'}), ('腕輪', 'bracelet', 'palm', {}), ('骨環', 'bracelet', 'palm', {}),
         ('指輪', 'ring', 'palm', {}), ('環', 'ring', 'palm', {}), ('運命札', 'card', 'palm', {}), ('リトライの札', 'card', 'palm', {}),
         ('結界札', 'talisman', 'fist', {}), ('霊符', 'talisman', 'fist', {}), ('天羽', 'feather', 'sword', {}), ('羽根', 'feather', 'sword', {}),
         ('羽飾り', 'pendant', 'fist', {'motif': 'feather'}), ('翼飾り', 'pendant', 'fist', {'motif': 'wing'}),
         ('角飾り', 'pendant', 'fist', {'motif': 'horn'}), ('鬼角', 'pendant', 'fist', {'motif': 'horn'}),
         ('鱗飾り', 'pendant', 'fist', {'motif': 'scale'}), ('龍鱗', 'pendant', 'fist', {'motif': 'scale'}),
         ('爪飾り', 'pendant', 'fist', {'motif': 'claw'}), ('心臓飾り', 'pendant', 'fist', {'motif': 'heart'}),
         ('花飾り', 'pendant', 'fist', {'motif': 'flower'}), ('髪飾り', 'pendant', 'fist', {'motif': 'flower'}),
         ('耳飾り', 'pendant', 'fist', {}), ('護符', 'pendant', 'fist', {}), ('胸章', 'badge', 'palm', {}), ('聖印', 'badge', 'palm', {}),
         ('珊瑚杖', 'staff', 'sword', {'head': 'coral'}), ('花杖', 'staff', 'sword', {'head': 'flower'}), ('種杖', 'staff', 'sword', {'head': 'seed'}),
         ('結晶杖', 'staff', 'sword', {'head': 'crystal'}), ('祈祷杖', 'staff', 'sword', {'head': 'cross'}), ('杖', 'staff', 'sword', {}),
         ('栞', 'book', 'palm', {'kind': 'bookmark'}), ('頁', 'book', 'palm', {'kind': 'page'}), ('契約書', 'book', 'palm', {'kind': 'scroll'}),
         ('詠譜', 'book', 'palm', {'kind': 'page'}), ('書', 'book', 'palm', {}), ('液瓶', 'bottle', 'palm', {}), ('瓶', 'bottle', 'palm', {}),
         ('杯', 'chalice', 'palm', {}), ('炉', 'furnace', 'palm', {}), ('時計', 'clock', 'palm', {}), ('骰子', 'dice', 'palm', {}),
         ('仮面', 'mask', 'palm', {}), ('玩具箱', 'box', 'palm', {}), ('解析眼', 'eye', 'palm', {}), ('石碑', 'stele', 'palm', {}),
         ('外殻', 'shell', 'palm', {}), ('殻', 'shell', 'palm', {}), ('触媒', 'catalyst', 'palm', {}), ('工具', 'tool', 'sword', {}),
         ('鏡', 'mirror', 'sword', {}), ('手甲', 'gauntlet', 'fist', {}), ('キューブ', 'cube', 'palm', {}), ('角笛', 'horn', 'palm', {}),
         ('核', 'orb', 'palm', {}), ('珠', 'orb', 'palm', {})]

def classify(name):
    for key, arch, hold, opt in RULES:
        if key in name:
            return arch, hold, opt
    return 'pendant', 'fist', {}

def build(rid, char, name):
    p, s, g = PAL[char]
    arch, hold, opt = classify(name)
    w = W3D(rid)
    ARCH[arch](w, p, s, g, **opt)
    return w, arch, hold

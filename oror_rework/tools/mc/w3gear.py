"""3D models of OROR's plain gear (052): what is seen in the hand, on the ground and in an item frame, while the
inventory keeps its 2D icon (textures/item/<id>.png, drawn by neoforge1211patch/tools/items_art.py), so that the two do
not look like one flat sprite stretched in two places.

Same toolkit and conventions as w3artifacts (u up the item's axis, v across, w depth; texels, 32 to the block; u = 0
where the hand holds it). Holds: 'palm' (carried upright in the open hand: the round things, the key, the book, the
armour), 'sword' (gripped by the handle: the repair tool), 'staff' (the banner, upright in the fist). What is round is
round (flasks, the core, the heart: sphere()), and things are held at about their own size beside the hand. The gear that changes as it is used gets its states:
'_active' (at work) and '_recharging' (drained of colour); the last bloom '_closed' (a bud while it recharges).

  python3 w3gear.py <assets root> [ids...]     writes models/item/gear3d/<id>.obj, textures/item/gear3d/<id>.png
                                               and models/item/<id>.json (the OBJ in the hand, the icon in the GUI)
  python3 w3gear.py --preview <png> [ids...]   a sheet of the models, each also in a hand (third person)
"""
import json, math, os, sys
import numpy as np
from PIL import Image
import forge3d as F
import held as Hd
from forge3d import W3D
from paint import M
from w3parts import Mt, octo, grip, collar, cone, gem, crystal, halo, disc, front_plate, side_plate, star, leaf, coil, ring3d, feather_wing
from w3artifacts import a_orb, a_cube, a_book, a_clock, a_bottle, a_tool, a_armillary

NS = 'oror_supreme_bosses'


def grey(c, k=0.5, dark=0.6):
    """A colour drained (the recharging look)."""
    c = c.lstrip('#')
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    l = 0.3 * r + 0.59 * g + 0.11 * b
    r, g, b = (int((v * (1 - k) + l * k) * dark) for v in (r, g, b))
    return '#%02x%02x%02x' % (r, g, b)


def sphere(g, u, r, mt, name='ball', v=0.0, w=0.0, squash=1.0, slices=None):
    """A round body: octagonal slices stacked along the axis, each as wide as the sphere at its height (squash < 1
    flattens it along the axis), so that what is round is round in the hand, not a box."""
    m = mt.b() if isinstance(mt, Mt) else mt
    c = g.group(u, v, w, name=name)
    n = slices or max(3, int(round(r * 2 * squash / 1.5)))
    h = 2 * r * squash / n
    for i in range(n):
        y = -r * squash + h * (i + 0.5)
        rr = r * math.sqrt(max(0.0, 1 - (y / (r * squash)) ** 2))
        if rr < 0.6:
            continue
        octo(c, y, h + 0.01, rr, m, f'{name}{i}')
    return c


# ----------------------------------------------------------------------------------------------------------- designs

def g_star_shard(w, **o):
    """A cluster of star-vein crystals on a shard of dark rock."""
    w.box(-6, 0, 0, 4, 12, 9, M('rock', '#3a3446'), name='rock')
    w.box(-6, 2, 0, 3, 9, 10, M('rock', '#2c2836'), rot=(30, 0, 0), name='rock2')
    crystal(w, 3, 0, 0, 16, 5, '#a89cf4', name='main')
    crystal(w, -1, -4, 1, 10, 3, '#8f84e8', rot=(0, 0, 28), name='left')
    crystal(w, -1, 4, -1, 9, 3, '#b8b0ff', rot=(0, 0, -32), name='right')
    crystal(w, -2, 1, 4, 7, 2, '#cfc8ff', rot=(-30, 0, 0), name='front')
    gem(w, 4, 0, 0, 2, '#ffffff', name='star', facet=False)


def g_dragon_core(w, **o):
    """A molten core held in four iron dragon's claws over a small iron stand."""
    sphere(w, 5, 5.2, M('energy', '#ff8a1c'), 'core')
    sphere(w, 5.5, 2.4, M('energy', '#fff0a0'), 'heat', w=2.6)
    iron = Mt('metal', '#8f8499')
    for k in range(4):
        c = w.group(-1, 0, 0, rot=(90 * k + 45, 0, 0), name=f'claw{k}')
        c.box(1.5, 5.8, 0, 6, 2.2, 2.2, iron.b(), rot=(0, 0, 30), name='c1')
        c.box(6.5, 7.4, 0, 5, 2, 2, iron.b(), name='c2')
        c.box(10.5, 6.2, 0, 4, 1.6, 1.6, Mt('metal', '#d2d9e2').b(), rot=(0, 0, -35), name='tip')
    octo(w, -4, 4, 2.2, Mt('metal', '#3b3440'), 'stem')
    cone(w, -8, 4, 5.0, 3.0, Mt('metal', '#3b3440'), steps=2, name='base')

def g_forge_core(w, **o):
    """A brass cube of the forge's reckoning, turned on its corner, its circuits lit teal, a lens on top."""
    from w3parts import runes
    w.box(4, 0, 0, 11, 11, 11, runes('#c48c48', '#38d0c0'), rot=(45, 35, 0), name='cube')
    w.box(4, 0, 0, 12, 4, 4, M('metal', '#93602c'), rot=(45, 35, 0), name='band')
    gem(w, 13, 0, 0, 3, '#38d0c0', name='lens')
    ring3d(w, 4, 9, 4, (2, 2, 2), Mt('metal', '#efc955'), name='nodes')
    octo(w, -6, 4, 2.2, Mt('metal', '#93602c'), 'stem')
    cone(w, -10, 3, 4.0, 2.4, Mt('metal', '#83531a'), steps=1, name='foot')


def g_curse_residue(w, **o):
    """A broken black heart: two rounded lobes over a point, split by a crimson light, its ichor dripping."""
    dark = M('metal', '#1c0e22')
    for s_ in (-1, 1):
        sphere(w, 4, 4.4, dark, f'lobe{s_}', v=s_ * 3.4)
    w.box(-1.5, 0, 0, 8, 8, 7, dark, rot=(0, 0, 45), name='point')
    w.box(-3, 0, 0, 5, 5, 6, dark, rot=(0, 0, 45), name='tip')
    crystal(w, 1, 0, 0, 12, 1, '#ff4656', name='crack')
    gem(w, 3, 0, 2.6, 2, '#ff3048', name='light', facet=False)
    for k, (u, v) in enumerate(((-7, 2), (-9, -2), (-11, 1))):
        w.box(u, v, 0, 2, 1, 1, M('gem', '#c0182a', glow=True), name=f'drip{k}')

def g_world_thread(w, **o):
    """A spool of shining thread between wooden flanges, its loose end running round in a ring."""
    thread = M('cloth', '#ffe08a', pattern='stripes', accent='#fff4c8')
    octo(w, 0, 12, 4.6, thread, 'thread')
    for u in (-7, 7):
        octo(w, u, 2, 6.8, Mt('wood', '#6a4c35'), f'flange{u}')
    octo(w, 0, 18, 1.2, Mt('wood', '#4c3626'), 'axle')
    halo(w.group(0, 0, 0, rot=(0, 90, 0), name='loop'), 0, 12, 11, Mt('energy', '#ffe08a'), d=0.4, name='ring')
    w.box(3, 6, 3, 1, 6, 1, M('cloth', '#fff4c8'), rot=(0, 0, 40), name='end')


def g_rewind_talisman(w, **o):
    """A bronze medallion with a clock face whose hands turn back, a cyan light round it."""
    a_clock(w, '#b8843a', '#5a3a1a', '#60e0f0')
    halo(w.group(0, 0, -1, rot=(0, 90, 0), name='back'), 0, 13.5, 12.8, Mt('energy', '#60e0f0'), d=0.3, name='arc')


def g_purifying_dew(w, **o):
    """A round glass flask, the liquid filling it, a neck of glass and its stopper."""
    sphere(w, 0, 6.6, M('gem', '#ffb830', glow=True), 'body')
    sphere(w, 0, 7.1, M('gem', '#e8f4fa', glow=False, alpha=0.35), 'glass', slices=8)
    w.box(2.5, -3.2, 3.6, 4, 1, 1, M('gem', '#ffffff', glow=True), rot=(0, 0, -30), name='shine')
    octo(w, 8, 4, 2.0, Mt('metal', '#cfe4ec', bx={'glow': False}), 'neck')
    octo(w, 10.2, 1, 2.6, Mt('metal', '#a2c0cc'), 'lip')
    octo(w, 12, 3, 1.8, Mt('wood', '#7a5a3a'), 'cork')
    w.box(13, 2, 0, 1, 5, 4, M('leaf', '#4ca43a'), rot=(0, 0, -30), name='leaf')
    w.box(-2, 7.4, 0, 2, 1, 1, M('gem', '#ffc23a', glow=True), name='drop')

def g_mana_crystal(w, **o):
    """A round glass flask, the liquid filling it, a neck of glass and its stopper."""
    sphere(w, 0, 6.6, M('gem', '#3a6aff', glow=True), 'body')
    sphere(w, 0, 7.1, M('gem', '#e8f4fa', glow=False, alpha=0.35), 'glass', slices=8)
    w.box(2.5, -3.2, 3.6, 4, 1, 1, M('gem', '#ffffff', glow=True), rot=(0, 0, -30), name='shine')
    octo(w, 8, 4, 2.0, Mt('metal', '#cfe4ec', bx={'glow': False}), 'neck')
    octo(w, 10.2, 1, 2.6, Mt('metal', '#a2c0cc'), 'lip')
    crystal(w, 12, 0, 0, 6, 3, '#b0b4f4', name='stopper')
    for k, (u, v, z) in enumerate(((0, -2, 6.5), (3, 2, 5.5), (-2, 3, 5.8))):
        w.box(u, v, z, 1, 1, 1, M('gem', '#ffffff', glow=True), name=f'star{k}')

def g_dungeon_key(w, **o):
    """An old iron key of the sealed realms, held by its bow: a gold ring round a crimson seal; the bit a notched ward."""
    iron = Mt('metal', '#8c95a4')
    halo(w.group(-6, 0, 0, rot=(0, 90, 90), name='bow'), 0, 6, 3.6, Mt('metal', '#efc955'), d=1.2, name='ring')
    gem(w, -6, 0, 0, 4, '#e0283c', name='seal')
    octo(w, 11, 22, 1.3, iron, 'shaft')
    collar(w, 1, 2, 2.0, Mt('metal', '#efc955'), 'collar')
    w.box(18, 3.5, 0, 5, 5, 2, iron.b(), name='ward')
    w.box(19.5, 6.5, 0, 2, 1, 2, iron.b(), name='tooth')
    w.box(16.5, 6.5, 0, 1, 1, 2, iron.b(), name='tooth2')


def g_field_guide(w, **o):
    """The adventurer's leather journal, gold-cornered, a compass on its cover, strapped."""
    a_book(w, '#7c4a2c', '#5a321e', '#efc955')


def g_forge_tool(w, **o):
    """The forge's repair tool: a wrench's jaws and a gear on a bound grip, held by the grip."""
    a_tool(w, '#c48c48', '#8c95a4', '#38d0c0')


def g_dragon_coat(w, **o):
    """A breastplate of dragon scales under gold-rimmed pauldrons, the furnace's core at its breast."""
    scale = M('scale', '#8c2c26')
    gold = M('metal', '#efc955')
    w.box(0, 0, 0, 14, 12, 7, scale, name='chest')
    w.box(-6, 0, 0, 3, 10, 6, scale, name='waist')
    w.box(-8, 0, 0, 1, 12, 7, gold, name='belt')
    for s in (-1, 1):
        p = w.group(6, s * 7, 0, rot=(0, 0, s * -15), name=f'pauldron{s}')
        p.box(0, 0, 0, 5, 6, 8, scale, name='plate')
        p.box(-2.5, 0, 0, 1, 6, 8, gold, name='rim')
    w.box(7.5, 0, 0, 1, 8, 7.4, gold, name='collar')
    gem(w, 2, 0, 3.6, 4, '#ff8a1c', name='core')


def g_teia_boots(w, **o):
    """A pair of white boots of light, cyan lines along them, wings of light at the heels."""
    white = M('cloth', '#eaf0f6')
    for s, dw in ((-1, -3), (1, 3)):
        b = w.group(0, s * 3.5, dw * 0.3, name=f'boot{s}')
        b.box(2, 0, 0, 10, 5, 5, white, name='shaft')
        b.box(-4, 0, 2, 3, 5, 9, white, name='foot')
        b.box(-5.6, 0, 2, 1, 5.2, 9.2, M('metal', '#596170'), name='sole')
        b.box(6.5, 0, 0, 1, 5.4, 5.4, M('gem', '#5cd2ee', glow=True), name='cuff')
        b.box(1, 0, 2.6, 8, 1, 0.4, M('gem', '#5cd2ee', glow=True), name='line')
        p = side_plate(b, -2, 12, -12, -2, v=s * 2.8)
        feather_wing(p, 3, -3, math.pi * 0.85, 3, 7, 1.6, Mt('energy', '#9cf0ee').p(d=0.3), z=3, spread=0.6)


def g_omniregistry_treasure(w, **o):
    """An armillary of shining gold rings about a sphere in which all things are written, on a gold stand."""
    gold = Mt('metal', '#efc955')
    octo(w, -8, 8, 1.6, gold, 'stem')
    cone(w, -13, 3, 4.0, 2.0, Mt('metal', '#c1902c'), steps=1, name='foot')
    gem(w, 6, 0, 0, 6, '#9a8cf0', name='sphere')
    gem(w, 6, 0, 0, 2, '#ffffff', name='core', facet=False)
    for k, rot in enumerate(((0, 0, 0), (0, 60, 0), (0, -60, 0), (90, 30, 0))):
        halo(w.group(6, 0, 0, rot=rot, name=f'arm{k}'), 0, 10 - k * 0.7, 7.8 - k * 0.7, Mt('metal', '#ffd860', px={'up': 0.6}), d=0.75, name='ring')

def g_villager_king_token(w, **o):
    """The Villager King's gold medal, a crown struck into it and an emerald set in it, on a red ribbon."""
    p = front_plate(w, -12, 12, -12, 12)
    p.ell(0, 0, 10, 10, Mt('metal', '#efc955').p(d=1.25, d0=0.75, bev=1.25), 1)
    p.ring(0, 0, 10, 8.6, Mt('metal', '#c1902c').p(d=1.5), 2)
    p.poly([(2, -6), (7, -5), (4, -2.5), (8, 0), (4, 2.5), (7, 5), (2, 6)], Mt('metal', '#83531a').p(d=1.3), 3)
    gem(w, -2, 0, 1, 4, '#3cd07a', name='emerald')
    for s in (-1, 1):
        r = w.group(11, s * 2.5, -1, rot=(0, 0, s * 20), name=f'rib{s}')
        r.box(4, 0, 0, 8, 3, 1, M('cloth', '#9c1c26'), name='ribbon')


def g_focus_cell(w, **o):
    """The laser gun's focus cell: a glowing cyan core held in a steel cage between steel caps."""
    octo(w, 0, 14, 2.8, Mt('energy', '#5cd2ee'), 'core')
    octo(w, 0, 15, 1.2, Mt('energy', '#e8feff'), 'heart')
    for k in range(4):
        a = 90 * k + 45
        g = w.group(0, 0, 0, rot=(a, 0, 0), name=f'rail{k}')
        g.box(0, 3.2, 0, 14, 1, 1, M('metal', '#8c95a4'), name='rail')
    for u in (-3, 3):
        octo(w, u, 1, 3.4, Mt('metal', '#596170'), f'band{u}')
    for u in (-8.5, 8.5):
        octo(w, u, 3, 3.8, Mt('metal', '#8c95a4'), f'cap{u}')
    octo(w, 11, 2, 1.6, Mt('metal', '#596170'), 'pin')

def g_dodge_talon(w, active=False, dim=False, **o):
    """A raptor's foot of iron, three talons, a cuff of feathers; at work, the wind wound round it."""
    c = (lambda x: grey(x)) if dim else (lambda x: x)
    iron = Mt('metal', c('#8c95a4'))
    dark = Mt('metal', c('#3b3440'))
    octo(w, 4, 10, 2.2, iron, 'shank')
    for k, ang in enumerate((-35, 0, 35)):
        t = w.group(-1, 0, 0, rot=(0, 0, ang), name=f'toe{k}')
        t.box(-4, 0, 0, 8, 2.4, 2.4, dark.b(), name='a')
        t.box(-9, 0, 1.5, 4, 2, 2, dark.b(), rot=(0, 40, 0), name='b')
        t.box(-11, 0, 3.5, 2, 1.2, 1.2, iron.b(), name='tip')
    p = front_plate(w, 6, 18, -8, 8)
    feather_wing(p, 9, 0, 0.0, 5, 8, 1.8, Mt('cloth', c('#d6dce6')).p(d=0.6), z=3, spread=1.0)
    if active:
        coil(w, -8, 12, 7, 1.5, Mt('energy', '#7ceef2'), thick=1, seg=3, name='wind')


def g_last_bloom(w, closed=False, **o):
    """A crimson lily of the end on a short stem, its heart of gold light; recharging, a closed bud."""
    octo(w, -6, 14, 0.9, Mt('cloth', '#2e7428'), 'stem')
    for s in (-1, 1):
        lf = w.group(-8, 0, 0, rot=(0, 0, s * 50), name=f'leafg{s}')
        lf.box(3, 0, 0, 6, 2, 1, M('cloth', '#4ca43a'), name='leaf')
    if closed:
        w.box(4, 0, 0, 7, 4, 4, M('cloth', '#6a3040'), name='bud')
        w.box(8, 0, 0, 3, 3, 3, M('cloth', '#8c4a58'), rot=(45, 45, 0), name='budtip')
        return
    for k in range(6):
        g = w.group(2, 0, 0, rot=(60 * k, 0, 0), name=f'petal{k}')
        pg = g.group(0, 0, 0, rot=(0, 0, -55), name='tilt')
        pg.box(4, 0, 0, 9, 3, 1, M('cloth', '#cc2a50'), name='blade')
        pg.box(9, 0, 0, 2, 2, 1, M('cloth', '#f2667e'), name='tip')
    gem(w, 3, 0, 0, 3, '#fff2b4', name='heart')
    for k in range(5):
        a = 2 * math.pi * k / 5
        w.box(5, math.cos(a) * 2, math.sin(a) * 2, 3, 0.5, 0.5, M('gem', '#ffe08a', glow=True), name=f'stamen{k}')


def g_parry_emblem(w, active=False, dim=False, **o):
    """A silver shield-badge, blue enamelled, two blades crossed on it and an arrow turning back; at work, its edge
    burning gold; recharging, drained."""
    c = (lambda x: grey(x)) if dim else (lambda x: x)
    p = front_plate(w, -14, 14, -12, 12)
    p.sym([(-13, 0.1), (-6, 7), (6, 11), (12, 11), (12, 0.1)], Mt('metal', c('#aab3c0')).p(d=1.25, d0=0.75, bev=1.25), 1)
    p.sym([(-11, 0.1), (-5, 5.6), (5, 9.2), (10, 9.2), (10, 0.1)], Mt('metal', c('#3c7ad0')).p(d=1.0), 2)
    for s in (-1, 1):
        p.stroke([(-8, s * -7), (8, s * 7)], 1.6, Mt('metal', c('#eaf0f6')).p(up=0.5), 3)
    p.curve((2, -6), (7, 0), (2, 6), 0.9, Mt('metal', c('#efc955')).p(up=0.5), 4)
    if active:
        p.sym([(-14, 0.1), (-6.5, 8), (6.5, 12), (13, 12), (13, 0.1)], Mt('energy', '#ffe08a').p(d=0.4), 0)
        for k, (u, v) in enumerate(((14, 10), (-12, 12), (6, -14))):
            gem(w, u, v, 1, 1.5, '#fff2b4', name=f'spark{k}', facet=False)


def g_squad_banner(w, active=False, dim=False, **o):
    """The band's war banner on its pole (held by the pole): a crowned shield on blue; raised in a rally, its crest
    blazing; recharging, drained."""
    c = (lambda x: grey(x)) if dim else (lambda x: x)
    octo(w, 18, 56, 1.1, Mt('wood', c('#6a4c35')), 'pole')
    gem(w, 46.5, 0, 0, 2.5, c('#efc955'), name='finial')
    w.box(42.5, 7, 0, 1.2, 14, 1.4, M('metal', c('#c1902c')), name='crossbar')
    p = front_plate(w, 20, 42, 0, 16)
    p.poly([(42, 0.5), (42, 15), (26, 15), (22, 12), (24, 7.5), (22, 3), (26, 0.5)], Mt('cloth', c('#24509c')).p(d=0.5), 1)
    p.stroke([(41, 1), (41, 14.5)], 0.9, Mt('metal', c('#efc955')).p(d=0.5), 2)
    crest = Mt('energy', '#fff2b4') if active else Mt('metal', c('#efc955'))
    p.poly([(37, 4.5), (37, 11), (33, 11), (30, 7.75), (33, 4.5)], crest.p(d=0.6), 3)
    p.dot(35, 7.75, Mt('cloth', c('#9c1c26')).p(d=0.6), 4, r=0.8)
    if active:
        gem(w, 44, 14, 1, 1.5, '#fff2b4', name='spark', facet=False)


DESIGNS = {
    'star_shard': (g_star_shard, 'palm', {}), 'dragon_core': (g_dragon_core, 'palm', {}),
    'forge_core': (g_forge_core, 'palm', {}), 'curse_residue': (g_curse_residue, 'palm', {}),
    'world_thread': (g_world_thread, 'palm', {}), 'rewind_talisman': (g_rewind_talisman, 'palm', {}),
    'purifying_dew': (g_purifying_dew, 'palm', {}), 'mana_crystal': (g_mana_crystal, 'palm', {}),
    'dungeon_key': (g_dungeon_key, 'palm', {}), 'field_guide': (g_field_guide, 'palm', {}),
    'forge_tool': (g_forge_tool, 'sword', {'length': 1.3}), 'dragon_coat': (g_dragon_coat, 'palm', {}),
    'teia_boots': (g_teia_boots, 'palm', {}), 'omniregistry_treasure': (g_omniregistry_treasure, 'palm', {}),
    'villager_king_token': (g_villager_king_token, 'palm', {}), 'focus_cell': (g_focus_cell, 'palm', {}),
    'dodge_talon': (g_dodge_talon, 'palm', {}), 'dodge_talon_active': (g_dodge_talon, 'palm', {'active': True}),
    'dodge_talon_recharging': (g_dodge_talon, 'palm', {'dim': True}),
    'last_bloom': (g_last_bloom, 'palm', {}), 'last_bloom_closed': (g_last_bloom, 'palm', {'closed': True}),
    'parry_emblem': (g_parry_emblem, 'palm', {}), 'parry_emblem_active': (g_parry_emblem, 'palm', {'active': True}),
    'parry_emblem_recharging': (g_parry_emblem, 'palm', {'dim': True}),
    'squad_banner': (g_squad_banner, 'staff', {'length': 1.9}), 'squad_banner_active': (g_squad_banner, 'staff', {'length': 1.9, 'active': True}),
    'squad_banner_recharging': (g_squad_banner, 'staff', {'length': 1.9, 'dim': True}),
}
# each item's states (the item property oror_supreme_bosses:state, GearLooks): 0.5 recharging, 1 at work
STATES = {'dodge_talon': [(0.5, 'dodge_talon_recharging'), (1.0, 'dodge_talon_active')],
          'parry_emblem': [(0.5, 'parry_emblem_recharging'), (1.0, 'parry_emblem_active')],
          'squad_banner': [(0.5, 'squad_banner_recharging'), (1.0, 'squad_banner_active')],
          'last_bloom': [(0.5, 'last_bloom_closed')]}


def build(rid):
    fn, hold, opt = DESIGNS[rid]
    w = W3D(rid)
    kw = {k: v for k, v in opt.items() if k != 'length'}
    fn(w, **kw)
    return w, hold, opt


def length_blocks(quads):
    ys = np.concatenate([F.to_obj_space(P)[:, 1] for P, *_ in quads])
    return float(ys.max() - ys.min())


def display(hold, opt, quads):
    if hold == 'staff':
        n = length_blocks(quads)
        d = Hd.derive_staff(round(opt['length'] / (n * 0.9375), 3), round(1.05 / n, 3))
    elif hold == 'sword':
        tp = round(min(0.85, max(0.3, opt['length'] / (length_blocks(quads) * 0.9375))), 3)
        d = Hd.derive(scale_tp=tp, scale_fp=round(tp * 0.62, 3), hold='sword')
    else:
        d = Hd.derive(scale_tp=0.75, scale_fp=0.55, hold=hold)
        # held up a little higher in first person, so that what is shown on the palm is seen whole
        fp = d['firstperson_righthand']
        fp['translation'] = [fp['translation'][0], fp['translation'][1] + 1.6, fp['translation'][2]]
    out = {'thirdperson_righthand': d['thirdperson_righthand'], 'firstperson_righthand': d['firstperson_righthand'],
           'ground': Hd.ground(quads), 'head': dict(rotation=[0, 180, 0], translation=[0, 13, 7], scale=[0.6, 0.6, 0.6]),
           'fixed': dict(rotation=[0, 180, 0], translation=[0, 0, 0], scale=[0.9, 0.9, 0.9])}
    for v in out.values():
        v['rotation'] = [round(float(x), 3) for x in v['rotation']]
        v['translation'] = [round(float(max(-80, min(80, x))), 3) for x in v['translation']]
        v['scale'] = [round(float(x), 4) for x in v['scale']]
    return out


def item_json(rid, disp):
    icon = {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'{NS}:item/{rid}'}}
    m = {
        'loader': 'neoforge:separate_transforms',
        'gui_light': 'front',
        'textures': {'particle': f'{NS}:item/{rid}'},
        'base': {
            'loader': 'neoforge:obj',
            'model': f'{NS}:models/item/gear3d/{rid}.obj',
            'flip_v': False,
            'emissive_ambient': True,
            'automatic_culling': False,
            'textures': {'tex': f'{NS}:item/gear3d/{rid}', 'particle': f'{NS}:item/{rid}'},
            'display': disp,
        },
        'perspectives': {'gui': icon},
    }
    if rid in STATES:
        m['overrides'] = [{'predicate': {f'{NS}:state': v}, 'model': f'{NS}:item/{mdl}'} for v, mdl in STATES[rid]]
    return m


def export(root, ids):
    md = os.path.join(root, 'models', 'item', 'gear3d')
    td = os.path.join(root, 'textures', 'item', 'gear3d')
    os.makedirs(md, exist_ok=True)
    os.makedirs(td, exist_ok=True)
    with open(os.path.join(md, 'relic3d.mtl'), 'w') as fh:
        fh.write(F.MTL)
    for rid in ids:
        w, hold, opt = build(rid)
        quads, atlas, S = w.build()
        F.write_obj(os.path.join(md, rid + '.obj'), quads, S)
        Image.fromarray(atlas, 'RGBA').save(os.path.join(td, rid + '.png'), optimize=True)
        with open(os.path.join(root, 'models', 'item', rid + '.json'), 'w') as fh:
            json.dump(item_json(rid, display(hold, opt, quads)), fh, indent=1)
        print(rid, hold, len(quads), S, flush=True)


def preview(png, ids):
    tiles = []
    for rid in ids:
        w, hold, opt = build(rid)
        quads, atlas, S = w.build()
        items = F.world_quads(quads, atlas)
        view = F.view_matrix(yaw=35, pitch=15)
        a = F.render_quads(items, size=(220, 260), view=view)
        b = Hd.preview_third_person(quads, atlas, display(hold, opt, quads), size=(200, 260), yaws=(-40,))[0]
        t = Image.new('RGB', (420, 280), (40, 42, 52))
        t.paste(a, (0, 10))
        t.paste(b if b.mode == 'RGB' else b.convert('RGB'), (220, 10))
        tiles.append(t)
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * 420, rows * 280), (30, 30, 36))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 420, (i // cols) * 280))
    sheet.save(png)


if __name__ == '__main__':
    if sys.argv[1] == '--preview':
        preview(sys.argv[2], sys.argv[3:] or list(DESIGNS))
    else:
        export(sys.argv[1], sys.argv[2:] or list(DESIGNS))

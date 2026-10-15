"""3D relic weapon designs, in the spirit of L_Ender's Cataclysm and the NightfallCraft arsenal: chunky
layered silhouettes, bevelled thick blades, glowing seams and cores, big ornamental heads, parts that
stand out in depth. Each design builds into a W3D (u up from the grip point, v across, w depth; texels at
32 per block). aw=True builds the awakened legend form of the same weapon."""
import math
import numpy as np
from forge3d import W3D
from paint import M
from w3parts import (Mt, P, runes, octo, grip, collar, cone, gem, crystal, spikes, fin, chain, halo, disc, side_plate,
                     front_plate, star, sigil, serrate, feather_wing, bat_wing, leaf, coil, ring3d, orbit)

WEAPONS = {}

def weapon(key, title, kind, legend_title, scale=0.85, hold='sword', fp_scale=0.55):
    def deco(fn):
        WEAPONS[key] = dict(fn=fn, title=title, kind=kind, legend=legend_title, scale=scale, hold=hold, fp_scale=fp_scale)
        return fn
    return deco

def build(key, aw=False):
    w = W3D(key + ('_legend' if aw else '_weapon'))
    WEAPONS[key]['fn'](w, aw)
    return w

def hilt(c, a, style=None):
    return M('hilt', c, accent=a, **({'style': style} if style else {}))

# ------------------------------------------------------------------------------------------- outline helpers
def curved(u0, u1, w0, w1, bend, n=14, tip=0.0, power=2.0):
    """Outline of a curved blade whose centre line bends towards +v by `bend` at the tip."""
    edge, back = [], []
    for k in range(n + 1):
        t = k / n
        u = u0 + (u1 - u0) * t
        c = bend * t ** power
        wd = w0 + (w1 - w0) * t
        edge.append((u, c - wd / 2))
        back.append((u, c + wd / 2))
    pts = edge + ([(u1 + tip, bend + w1 * 0.3)] if tip else []) + list(reversed(back))
    return pts, edge, back

def centre(u0, u1, bend, n=14, power=2.0):
    return [(u0 + (u1 - u0) * k / n, bend * (k / n) ** power) for k in range(n + 1)]

def band(line, off0, off1):
    return [(u, v + off0) for u, v in line] + [(u, v + off1) for u, v in reversed(line)]

def mirror(half):
    return list(half) + [(u, -v) for u, v in reversed(half)]

def layered_blade(p, half, edge, body, core=None, d=(1.25, 2.25), inset=2.2, core_w=1.4, core_from=None, core_to=None):
    """Symmetric blade in three layers: bright edge band, thick body, glowing inlaid channel."""
    p.sym(half, P(edge, d=d[0], d0=0.5, bev=2), 2)
    inner = [(u, max(0.1, v - inset)) for u, v in half]
    inner[-1] = (half[-1][0] - inset * 1.4, 0.1)
    p.sym(inner, P(body, d=d[1], d0=d[0], bev=2), 3)
    if core is not None:
        u0 = core_from if core_from is not None else half[0][0] + 3
        u1 = core_to if core_to is not None else half[-1][0] - inset * 3
        p.sym([(u0, core_w), (u1 - 4, core_w * 0.8), (u1, 0.1)], P(core, inset=0.5), 4)
    return inner

# =========================================================================================== 1 kokuhaku
@weapon('kokuhaku', '蒼白断界刀・虚', 'katana', '剣理終極・虚無一閃')
def d_kokuhaku(w, aw):
    steel = Mt('metal', '#262a36' if aw else '#dde4ef')
    ridge = Mt('metal', '#3b4358' if aw else '#f6f9ff')
    glowc = Mt('energy', '#f0fcff' if aw else '#86e2ff')
    gold = Mt('metal', '#e8c060')
    navy = Mt('metal', '#232a3c')
    L0, L1, bend = 18, 100, 8.0
    pts, edge, back = curved(L0, L1, 9.0, 6.0, bend, tip=5.0)
    p = front_plate(w, L0 - 1, L1 + 7, -7, 16)
    p.poly(pts, steel.p(d=1.0, d0=0.5, bev=2), 2)
    cl = centre(L0, L1 - 2, bend)
    p.poly(band(cl, 0.6, 4.0), ridge.p(d=2.25, d0=1.25, bev=1.5), 3)                       # shinogi-ji / mune
    p.stroke([(u, v - 2.8 + 0.7 * math.sin(u * 0.5)) for u, v in cl], 1.1, glowc.p(inset=0.25), 4)   # hamon
    p.stroke([(L1 - 1, bend - 2.0), (L1 + 4, bend + 1.0)], 1.0, glowc.p(inset=0.25), 4)
    for u in (30, 44):                                                                       # engraved dragon marks
        p.stroke([(u, 2.6), (u + 3, 3.4), (u + 6, 2.4)], 0.8, Mt('energy', '#9fe8ff').p(inset=0.5), 5)
    if aw:
        rift = [(u, v + 1.4 + 1.0 * math.sin(u * 0.33)) for u, v in centre(L0 + 4, L1 - 6, bend)]
        p.stroke(rift, 2.2, Mt('energy', '#7fc8ff').p(inset=0.5), 5)
        p.stroke(rift, 0.8, Mt('energy', '#ffffff').p(inset=0.5), 6)
    # habaki, octagonal tsuba with gold rim and claw lobes, seppa
    w.box(16, 0, 0, 4, 8, 5, gold.b(), name='habaki')
    octo(w, 13.5, 2, 9, navy, 'tsuba')
    halo(w, 14.6, 9.5, 7.8, gold, d=0.5, name='tsuba_rim')
    for k in range(4):
        c = w.group(13.5, 0, 0, rot=(45 + 90 * k, 0, 0), name=f'claw{k}')
        c.box(0, 9.5, 0, 3, 4, 3, gold.b(), rot=(0, 0, 35), name='claw')
        c.box(1.5, 11.2, 0, 2, 2, 2, Mt('metal', '#fff1c0').b(), name='claw_tip')
    w.box(12, 0, 0, 1, 7, 6, gold.b(), name='seppa')
    # grip (diamond wrap), menuki, kashira, dragon-tail tassel
    grip(w, -13, 11, 2.8, hilt('#eef2fa' if not aw else '#1a1f2e', '#203a78' if not aw else '#c9a050', 'diamond'),
         bands=(-12.5, 10.5), band_mt=navy)
    for u, s in ((-4, 1), (4, -1)):
        w.box(u, 0, s * 2.9, 4, 2, 1, gold.b(), name='menuki')
    collar(w, -14.5, 3, 3.2, gold)
    gem(w, -16.5, 0, 0, 3, '#86e2ff', name='kashira_gem')
    t = w.group(-15, 0, 0, rot=(0, 0, 30), name='tassel')
    t.box(-3.5, 0, 0, 7, 1, 1, Mt('cloth', '#203a78' if not aw else '#d8b050').b(), name='cord')
    t.box(-9, 0, 0, 5, 3, 3, Mt('fur', '#f2f6ff' if not aw else '#202434').b(), name='tuft')
    t.box(-12.5, 0, 0, 3, 2, 2, Mt('fur', '#c8d8f0' if not aw else '#3a4058').b(), name='tuft2')
    # dragon horns rising from the tsuba along the spine (her two horns)
    for s in (-1, 1):
        h = w.group(15, s * 6, 0, rot=(0, 0, s * 20), name=f'horn{s}')
        h.box(4, 0, 0, 8, 3, 3, gold.b(), name='horn_a')
        h2 = h.group(8, 0, 0, rot=(0, 0, s * -28), name=f'horn2{s}')
        h2.box(3, 0, 0, 6, 2, 2, Mt('metal', '#fff1c0').b(), name='horn_b')
        h2.box(6.5, 0, 0, 2, 1, 1, Mt('metal', '#ffffff').b(), name='horn_c')
    if aw:
        halo(w, 14, 13, 11.5, Mt('energy', '#bfefff'), spikes_n=8, name='aw_halo', d=0.5)
        for k, (u, v, wz, r) in enumerate(((42, 15, 3, (0, 0, 20)), (64, -11, -4, (0, 0, -25)), (86, 18, 2, (0, 0, 35)),
                                           (32, -12, 5, (0, 0, -40)), (104, 4, -3, (0, 0, 10)))):
            crystal(w, u, v, wz, 7, 2, '#dff6ff', rot=r, name=f'shard{k}')

# =========================================================================================== 2 riha
@weapon('riha', '天冠言霊筆', 'brush', '世界詠替・絶対真言')
def d_riha(w, aw):
    bamboo = Mt('wood', '#e6d49c')
    lacq = Mt('metal', '#b0283c')
    gold = Mt('metal', '#ecc35a')
    ink = Mt('energy', '#ffd45c' if not aw else '#ffffff')
    white = Mt('cloth', '#fbf7ee')
    grip(w, -22, 46, 2.8, bamboo, bands=(-12, 4, 20, 36), band_mt=Mt('wood', '#c8b070'))
    collar(w, -4, 10, 3.1, lacq)
    collar(w, -24, 4, 3.4, gold)
    gem(w, -27, 0, 0, 3, '#ffcf5a', name='end')
    cone(w, 46, 9, 3.2, 5.6, gold, steps=3, name='ferrule')
    ring3d(w, 55, 5.6, 8, (4, 2, 2), gold, name='crownpts')
    halo(w, 58, 14, 12.2, gold if not aw else Mt('energy', '#ffe38a'), spikes_n=12, name='tenkan', d=0.5)
    for rot in (0, 60, 120):
        g = w.group(0, 0, 0, rot=(rot, 0, 0), name=f'brist{rot}')
        p = front_plate(g, 54, 108, -12, 12)
        p.sym([(55, 5.5), (64, 9.0), (80, 8.6), (94, 4.8), (106, 0.1)], white.p(d=1.25, d0=0.5, bev=2), 2)
        p.sym([(84, 6.8), (94, 4.2), (106, 0.1)], ink.p(), 3)
        for v in (-5, -2, 2, 5):
            p.stroke([(58, v), (82, v * 0.85)], 0.6, Mt('cloth', '#e8e0cc').p(inset=0.25), 3)
    def glyph(g, k):
        p = front_plate(g, -7, 7, -7, 7)
        strokes = [[(-5, -4), (5, -4)], [(0, -5), (0, 5)], [(-4, 5), (4, 1)]] if k % 2 == 0 else \
                  [[(-5, 0), (5, 0)], [(-3, -5), (3, 5)], [(3, -5), (-3, 4)]]
        for s in strokes:
            p.stroke(s, 1.6, ink.p(d=0.5), 3)
    orbit(w, 80, 19, 3 if not aw else 6, glyph, phase=20, name='glyph')
    for s in (-1, 1):
        c = w.group(47, s * 5, 0, rot=(0, 0, s * 160), name=f'cord{s}')
        c.box(6, 0, 0, 12, 1, 1, Mt('cloth', '#c8304a').b(), name='cord')
        c.box(14, 0, 0, 5, 4, 4, Mt('cloth', '#e04058').b(), name='knot')
    if aw:
        halo(w, 84, 24, 22.5, Mt('energy', '#fff1b0'), spikes_n=16, name='aw_halo2', d=0.5)

# =========================================================================================== 3 tenki
@weapon('tenki', '唯我の王剣', 'greatsword', '万象跪拝・唯我王権')
def d_tenki(w, aw):
    white = Mt('metal', '#f6f3ea')
    gold = Mt('metal', '#e8b83e')
    pale = Mt('metal', '#fff3cc')
    sky = Mt('energy', '#9fd2ff' if not aw else '#ffe28a')
    p = front_plate(w, 18, 118, -14, 14)
    half = [(19, 11.5), (28, 12.5), (60, 11.5), (88, 10.0), (102, 7.0), (110, 3.5), (116, 0.1)]
    layered_blade(p, half, gold, white, sky, d=(1.25, 2.5), inset=2.4, core_w=1.6)
    for u in (38, 58, 78):
        p.ring(u, 0, 3.8, 2.4, gold.p(up=0.25), 5)
        p.dot(u, 0, sky.p(), 6, r=0.9)
        for k in range(8):
            a = 2 * math.pi * k / 8
            p.dot(u + math.cos(a) * 5.2, math.sin(a) * 5.2, gold.p(up=0.25), 5)
    # crown guard: bar + rising wing quillons in the blade plane + crest in depth
    w.box(16, 0, 0, 5, 30, 8, gold.b(), name='guard_bar')
    w.box(16, 0, 0, 3, 34, 6, white.b(), name='guard_bar2')
    g = front_plate(w, 8, 36, -30, 30)
    for s in (-1, 1):
        feather_wing(g, 17, s * 12, (math.pi / 2) * s * 0.55 + (0.35 if s > 0 else -0.35) * 0 , 4, 16, 2.2,
                     pale.p(d=1.0), 2, spread=0.55)
    sp = side_plate(w, 12, 30, -9, 9)
    sp.sym([(13, 5), (20, 8), (27, 3), (29, 0.1)], gold.p(d=1.0), 2)
    gem(w, 17, 0, 0, 6, '#7fc4ff', name='heart')
    for s in (-1, 1):
        gem(w, 17, s * 17, 0, 3, '#7fc4ff', name='qgem')
    # grip + pommel crown
    grip(w, -15, 13, 3.0, hilt('#f6f3ea', '#c89a30'), bands=(-14, 0, 12), band_mt=gold)
    cone(w, -20, 6, 4.8, 3.2, gold, steps=2, name='pommel')
    spikes(w, -21.5, 6, 3.8, 5, 2, gold, tilt=-45, name='crown')
    gem(w, -23, 0, 0, 4, '#7fc4ff', name='pommel_gem')
    if aw:
        halo(w, 24, 15, 12.5, gold, spikes_n=16, name='sun', d=0.5)
        halo(w, 126, 7, 5.5, Mt('energy', '#ffe9a0'), spikes_n=5, name='crown_halo', d=0.5)
        def kneel(g, k):
            sp = front_plate(g, -14, 2, -3, 3)
            sp.sym([(-13, 0.1), (-10, 1.6), (-2, 1.6)], Mt('energy', '#fff1b0').p(d=0.5), 2)
            sp.poly([(-2, -3), (0, -3), (0, 3), (-2, 3)], gold.p(d=0.75), 3)
        orbit(w, 64, 20, 6, kneel, name='kneel')

# =========================================================================================== 4 chaos
@weapon('chaos', '万象変転の混沌核', 'staff', '混沌開闢・万象変転')
def d_chaos(w, aw):
    flesh = Mt('dark', '#3a2050')
    flesh2 = Mt('dark', '#5a2c70')
    pink = Mt('energy', '#ff6fd0')
    eyew = M('metal', '#fff0fa')
    for k in range(3):
        coil(w, -28, 54, 2.0, 1.25, Mt('dark', ['#3a2050', '#4e2a64', '#2c1a40'][k]), thick=3, phase=120 * k, name=f'tend{k}')
    octo(w, 13, 82, 1.6, flesh, 'core_shaft')
    for k, u in enumerate((-18, 4, 28)):
        s = 1 if k % 2 == 0 else -1
        w.box(u, s * 2.8, 1.0, 3, 3, 3, eyew, name='eyeball')
        w.box(u, s * 2.8, 2.8, 1, 1, 1, pink.b(), name='pupil')
    octo(w, 54, 6, 4.2, flesh2, 'bulb')
    collar(w, 50, 2, 3.4, Mt('metal', '#2a1a36'))
    # six tendrils rising outwards and curling back in: a living cage
    for k in range(6):
        g = w.group(56, 0, 0, rot=(60 * k + 30, 0, 0), name=f'cage{k}')
        s1 = g.group(0, 4.5, 0, rot=(0, 0, -45), name=f'cs1{k}')
        s1.box(6, 0, 0, 12, 3, 3, flesh2.b(), name='c1')
        s2 = s1.group(12, 0, 0, rot=(0, 0, 35), name=f'cs2{k}')
        s2.box(6, 0, 0, 12, 3, 3, flesh.b(), name='c2')
        if k % 2 == 0:
            s2.box(6, 1.8, 0, 2, 2, 2, eyew, name='ceye')
            s2.box(6, 2.6, 0.8, 1, 1, 1, pink.b(), name='cpupil')
        s3 = s2.group(12, 0, 0, rot=(0, 0, 55), name=f'cs3{k}')
        s3.box(4.5, 0, 0, 9, 2, 2, flesh2.b(), name='c3')
        s3.box(9.5, 0, 0, 2, 2, 2, pink.b(), name='c3tip')
    # the rainbow core floating in the cage
    w.box(72, 0, 0, 10, 10, 10, M('rainbow', '#ff8fe0', glow=True), rot=(45, 35, 0), name='core')
    w.box(72, 0, 0, 8, 8, 8, M('rainbow', '#7fe0ff', glow=True), rot=(0, 45, 45), name='core2')
    gem(w, 72, 0, 0, 4, '#ffffff', name='core_heart')
    def ey(g, k):
        g.box(0, 0, 0, 2, 2, 2, eyew, name='oeye')
        g.box(0, 1.2, 0, 1, 1, 1, pink.b(), name='opupil')
    orbit(w, 72, 9.5, 5, ey, phase=10, name='eyes')
    if aw:
        def thing(g, k):
            if k == 0:
                g.box(0, 0, 0, 4, 4, 4, M('rainbow', '#ffd060', glow=True), rot=(30, 30, 0), name='t_cube')
            elif k == 1:
                halo(g, 0, 4, 3, Mt('energy', '#7fffd0'), name='t_ring')
            elif k == 2:
                crystal(g, 0, 0, 0, 7, 2, '#ff7fd8', rot=(0, 0, 90), name='t_shard')
            else:
                g.box(0, 0, 0, 3, 5, 3, M('rainbow', '#9f8fff', glow=True), rot=(0, 45, 30), name='t_gem')
        orbit(w, 72, 21, 4, thing, phase=15, name='things')
        halo(w, 72, 25, 23.5, Mt('energy', '#ff9fe8'), name='aw_halo', d=0.5, tilt=25)
        halo(w, 72, 19, 17.8, Mt('energy', '#9fe8ff'), name='aw_halo2', d=0.5, tilt=-35)

# =========================================================================================== 5 berit
@weapon('berit', '万界錬成の籠手', 'gauntlet', '万界錬成・賢者の錬成炉', hold='fist', scale=0.9)
def d_berit(w, aw):
    black = Mt('metal', '#2a2630')
    gold = Mt('metal', '#d8aa48')
    amber = Mt('energy', '#ffb84a')
    glass = M('gem', '#bff4ff', glow=False, alpha=0.5)
    # flared bracer (elbow at u = -22) narrowing to the wrist, gold cuffs
    cone(w, -22, 18, 7.8, 5.8, black, steps=3, name='bracer')
    octo(w, -22, 3, 8.4, gold, 'cuff_e')
    octo(w, -3, 2, 6.4, gold, 'cuff_w')
    w.box(-13, 0, 6.9, 14, 9, 1, runes('#2a2630', '#ffb84a'), name='bracer_plate')
    for k, (v, col) in enumerate(((-6, '#7fff9f'), (0, '#ff7fbf'), (6, '#7fbfff'))):
        g = w.group(-13, v, -6.6, name=f'vial{k}')
        g.box(0, 0, 0, 11, 3, 3, glass, name='glass')
        g.box(-1.5, 0, 0, 7, 2, 2, M('energy', col), name='liquid')
        g.box(6, 0, 0, 2, 3, 3, gold.b(), name='cork')
    # broad hand with a transmutation circle on its back
    w.box(5, 0, 0, 11, 15, 8, black.b(), name='hand')
    w.box(5, 0, 0, 9, 16, 6, gold.b(), name='hand_rim')
    p = front_plate(w, -3, 13, -8, 8, w=4.2)
    sigil(p, 5, 0, 6.6, gold.p(d=0.5), amber.p(d=0.5), z=3, n=6)
    p.ell(5, 0, 1.8, 1.8, amber.p(d=0.75), 6)
    for k, v in enumerate((-5.4, -1.8, 1.8, 5.4)):
        f = w.group(10.5, v, 0.5, name=f'finger{k}')
        f.box(2.5, 0, 0, 5, 3, 5, black.b(), name='f1')
        f2 = f.group(5, 0, 0, rot=(0, -35, 0), name=f'finger2{k}')
        f2.box(2, 0, 0, 4, 3, 4, black.b(), name='f2')
        f3 = f2.group(4, 0, 0, rot=(0, -30, 0), name=f'finger3{k}')
        f3.box(1.5, 0, 0, 3, 3, 3, gold.b(), name='f3')
        f.box(0.5, 0, 2.6, 2, 2, 1, gold.b(), name='knuckle_cap')
    th = w.group(4, -8, -1, rot=(0, -10, -40), name='thumb')
    th.box(3, 0, 0, 6, 3, 4, black.b(), name='t1')
    th.box(7, 0, 0, 3, 3, 3, gold.b(), name='t2')
    gem(w, 5, 0, -4.6, 3, '#ffb84a', name='palm_stone')
    spikes(w, -20, 6, 8.0, 5, 2, gold, tilt=60, name='elbow_spike')
    if aw:
        halo(w, 2, 15, 13.5, amber, spikes_n=6, name='aw_circle', d=0.5)
        halo(w, -14, 12, 10.8, gold, spokes=6, name='aw_circle2', d=0.5, tilt=30)
        gem(w, 5, 0, 8, 4, '#ff3f4f', name='philosopher')

# =========================================================================================== 6 elseria
@weapon('elseria', '原初星辰杖', 'staff', '星脈開闢・原初魔典')
def d_elseria(w, aw):
    white = Mt('metal', '#f4f6fb')
    silver = Mt('metal', '#b8c4dc')
    gold = Mt('metal', '#e2c060')
    blue = Mt('metal', '#7fa8ff')
    starc = Mt('energy', '#bfe6ff' if not aw else '#fff4c0')
    grip(w, -32, 62, 2.4, white, bands=(-24, -6, 12, 30, 48), band_mt=gold)
    coil(w, -24, 56, 2.7, 2.0, blue, thick=1, name='starthread')
    cone(w, -38, 6, 3.2, 2.0, gold, steps=2, name='butt')
    crystal(w, -42, 0, 0, 5, 2, '#bfe6ff', rot=(180, 0, 0), name='butt_star')
    cone(w, 62, 8, 2.6, 4.6, gold, steps=2, name='head_cone')
    p = front_plate(w, 58, 112, -36, 36, w=-2)
    for s in (-1, 1):
        feather_wing(p, 74, s * 4, s * 1.1, 6, 26, 2.8, white.p(d=1.0), 2, spread=0.55)
        feather_wing(p, 72, s * 4, s * 1.35, 4, 16, 2.0, blue.p(d=1.25), 3, spread=0.4)
    q = front_plate(w, 66, 114, -20, 20, w=1)
    star(q, 90, 0, 19, 5.0, 4, gold.p(d=1.0), 2)
    star(q, 90, 0, 13, 3.8, 4, white.p(d=1.75), 3, rot=math.pi / 4)
    q.ell(90, 0, 5.0, 5.0, blue.p(d=2.0), 4)
    q.ell(90, 0, 3.2, 3.2, starc.p(d=2.5), 5)
    for rot in ((0, 0, 0), (0, 60, 0), (0, -60, 0)):
        g = w.group(90, 0, 0, rot=rot, name=f'arm{rot[1]}')
        halo(g, 0, 16, 15, gold, d=0.5, name='armillary')
    if aw:
        orbit(w, 90, 24, 7, lambda g, k: star(front_plate(g, -6, 6, -6, 6), 0, 0, 5, 1.8, 4, starc.p(d=0.5), 3), name='stars')
        halo(w, 90, 30, 28.5, starc, spikes_n=12, name='aw_circle', d=0.5)

# =========================================================================================== 7 valeria
@weapon('valeria', '万機創匠の変形槌', 'hammer', '万機創世・極大鍛造槌')
def d_valeria(w, aw):
    steel = Mt('metal', '#5b626e')
    dark = Mt('metal', '#2a2e36')
    brass = Mt('metal', '#d0a050')
    core = Mt('energy', '#62e8ff' if not aw else '#ffb04a')
    grip(w, -22, 40, 2.4, hilt('#3a3f48', '#22262c'), bands=(-20, -6, 10, 26), band_mt=brass)
    cone(w, -28, 6, 3.6, 2.4, brass, steps=2, name='pommel')
    gem(w, -30.5, 0, 0, 3, '#62e8ff', name='pommel_core')
    collar(w, 36, 8, 3.8, dark)
    for s in (-1, 1):
        w.box(34, s * 4.6, 0, 12, 2, 2, steel.b(), name='piston')
        w.box(29, s * 4.6, 0, 2, 3, 3, brass.b(), name='piston_cap')
    coil(w, 2, 30, 3.1, 3, Mt('metal', '#a0723a'), thick=1, name='cable')
    # head: block with bevelled bands, reactor faces, gear plates on both sides
    w.box(54, 0, 0, 22, 34, 18, dark.b(), name='head')
    w.box(54, 0, 0, 24, 30, 14, steel.b(), name='head_band')
    w.box(54, 0, 0, 16, 36, 12, steel.b(), name='head_band2')
    for s in (-1, 1):
        w.box(54, s * 18.5, 0, 18, 3, 16, brass.b(), name='face')
        w.box(54, s * 20.5, 0, 12, 2, 12, steel.b(), name='face2')
        w.box(54, s * 21.8, 0, 6, 1, 6, core.b(), name='face_core')
        for du in (-7, 7):
            w.box(54 + du, s * 17.5, 0, 2, 2, 18, brass.b(), name='rib')
    for wz in (-1, 1):
        g = front_plate(w, 40, 68, -16, 16, w=wz * 9.2)
        g.ring(54, 0, 9, 5.5, brass.p(d=0.5), 1)
        for k in range(10):
            a = 2 * math.pi * k / 10
            g.poly([(54 + math.cos(a - 0.15) * 8.5, math.sin(a - 0.15) * 8.5), (54 + math.cos(a) * 11, math.sin(a) * 11),
                    (54 + math.cos(a + 0.15) * 8.5, math.sin(a + 0.15) * 8.5)], brass.p(d=0.5), 1)
        g.ell(54, 0, 4.5, 4.5, core.p(d=0.75), 2)
        g.ring(54, 0, 3, 1.5, dark.p(d=1.0), 3)
    for s in (-1, 1):
        w.box(67, s * 7, 0, 4, 4, 4, dark.b(), name='stack')
        w.box(70, s * 7, 0, 2, 3, 3, core.b(), name='stack_glow')
    if aw:
        halo(w, 54, 26, 23, Mt('energy', '#ffb04a'), spikes_n=10, name='aw_ring', d=0.5)
        for k, (u, v, wz) in enumerate(((80, 15, 6), (82, -13, -5), (28, 17, 4), (24, -16, -4))):
            w.box(u, v, wz, 4, 4, 4, brass.b(), rot=(30 * k, 45, 20), name=f'bit{k}')

# =========================================================================================== 8 huang_linghua
@weapon('huang_linghua', '黄天龍仙槍', 'spear', '黄天三界・龍仙顕現')
def d_huang(w, aw):
    lacq = Mt('metal', '#16161e')
    gold = Mt('metal', '#e2b445')
    jade = Mt('metal', '#3fb8a0')
    red = Mt('cloth', '#c8283a')
    grip(w, -40, 82, 2.0, lacq, bands=(-36, -10, 20, 50, 78), band_mt=gold)
    # golden dragon coiling up the shaft
    coil(w, -20, 64, 2.8, 2.5, gold, thick=2, name='dragon')
    w.box(66, 0, 3.4, 4, 3, 3, gold.b(), name='dragon_head')
    w.box(68, 0, 4.6, 2, 2, 2, Mt('energy', '#ff4848').b(), name='dragon_eye')
    cone(w, -46, 6, 2.8, 1.8, gold, steps=2, name='butt')
    # dragon-mouth socket, red tassel, jade spearhead
    cone(w, 82, 8, 3.0, 4.4, gold, steps=2, name='socket')
    for s in (-1, 1):
        h = w.group(88, s * 4, 0, rot=(0, 0, s * -55), name=f'whisker{s}')
        h.box(4, 0, 0, 8, 2, 2, gold.b(), name='w1')
        h.box(9, 0, 0, 3, 1, 1, Mt('metal', '#fff0b0').b(), name='w2')
    for k in range(6):
        c = w.group(82, 0, 0, rot=(60 * k, 0, 0), name=f'tas{k}')
        c.box(-6, 3.5, 0, 12, 1, 2, red.b(), rot=(0, 0, 10), name='tassel')
    p = front_plate(w, 88, 128, -9, 9)
    half = [(89, 4.0), (94, 7.5), (104, 6.5), (116, 3.2), (126, 0.1)]
    layered_blade(p, half, gold, jade, Mt('energy', '#9fffe0'), d=(1.0, 2.0), inset=1.8, core_w=1.0)
    sp = side_plate(w, 88, 124, -6, 6)
    sp.sym([(90, 3.0), (100, 4.0), (112, 2.0), (122, 0.1)], jade.p(d=1.25), 2)
    if aw:
        for k, col in enumerate(('#9fd8ff', '#c89a50', '#4fe0c0')):          # sky / earth / sea orbs
            orbit(w, 100, 16, 1, lambda g, kk, col=col, k=k: gem(g, 0, 0, 0, 5, col, name=f'orb{k}'), phase=120 * k, name=f'orbit{k}')
        halo(w, 100, 22, 20.6, Mt('energy', '#ffe08a'), spikes_n=9, name='aw_halo', d=0.5)

# =========================================================================================== 9 ferdinand
@weapon('ferdinand', '試作零号魔導連射砲', 'gatling', '文明加速・終末連射機構')
def d_ferdinand(w, aw):
    brass = Mt('metal', '#cf9b45')
    steel = Mt('metal', '#6e7480')
    dark = Mt('metal', '#2e3138')
    energy = Mt('energy', '#7fe8ff' if not aw else '#ff9f40')
    # pistol grip below the receiver, stock behind, barrels forward (+u)
    pg = w.group(0, 0, 0, rot=(0, 0, 18), name='pgrip')
    pg.box(-4, -5.5, 0, 13, 5, 5, hilt('#5a3a22', '#3a2414'), name='pistol_grip')
    w.box(5, -8, 0, 7, 2, 5, steel.b(), name='trigger_guard')
    st = w.group(-6, 3, 0, rot=(0, 0, -12), name='stock')
    st.box(-6, 0, 0, 12, 7, 6, Mt('wood', '#6a4428').b(), name='stock_wood')
    st.box(-12.5, 0, 0, 2, 9, 7, brass.b(), name='butt_plate')
    w.box(6, 3, 0, 20, 12, 12, dark.b(), name='receiver')
    w.box(6, 3, 0, 16, 14, 10, brass.b(), name='receiver_plate')
    p = front_plate(w, -5, 17, -5, 11, w=6.4)
    sigil(p, 6, 3, 5.5, brass.p(d=0.5), energy.p(d=0.5), 3, n=8)
    # crystal canister on top, drum magazine on the side, pressure gauge
    octo(w.group(6, 11, 0, rot=(0, 0, 90), name='canister'), 0, 9, 3.2, Mt('metal', '#3a404c'), 'can')
    w.box(6, 11, 0, 7, 3, 3, M('gem', '#bff4ff', glow=False, alpha=0.5), name='can_glass')
    w.box(6, 11, 0, 5, 2, 2, energy.b(), name='can_core')
    w.box(4, 3, -9, 10, 10, 6, steel.b(), name='drum')
    w.box(4, 3, -12.5, 6, 6, 1, energy.b(), name='drum_crystal')
    w.box(12, 10.5, 4, 4, 2, 4, brass.b(), name='gauge')
    w.box(12, 11.6, 4, 2, 1, 2, M('gem', '#f2f6ff', glow=False), name='gauge_glass')
    # barrel cluster with cooling shrouds and glowing muzzle
    collar(w.group(0, 3, 0, name='b0'), 18, 4, 6.8, brass)
    for k in range(6):
        a = 2 * math.pi * k / 6
        w.box(36, 3 + math.cos(a) * 4.2, math.sin(a) * 4.2, 34, 2, 2, steel.b(), name=f'barrel{k}')
    octo(w.group(0, 3, 0, name='bcore'), 36, 34, 1.4, dark, 'barrel_core')
    for u in (25, 37, 49):
        octo(w.group(0, 3, 0, name=f'bh{u}'), u, 3, 7.0, brass if u != 37 else dark, f'shroud{u}')
    octo(w.group(0, 3, 0, name='muz'), 53, 2, 6.0, energy, 'muzzle')
    if aw:
        def drone(g, kk):
            g.box(0, 0, 0, 4, 4, 4, brass.b(), rot=(0, 45, 0), name='drone')
            g.box(0, 0, 0, 2, 6, 2, energy.b(), name='drone_core')
        orbit(w.group(0, 3, 0, name='dr'), 30, 15, 3, drone, phase=30, name='drones')
        halo(w.group(0, 3, 0, name='ah'), 57, 10, 8.5, energy, spikes_n=8, name='aw_muzzle', d=0.5)

# =========================================================================================== 10 mels
@weapon('mels', '無形流武の水刃', 'liquid halberd', '流武極致・万形一体')
def d_mels(w, aw):
    gel = Mt('metal', '#7fd8ff')
    deep = Mt('metal', '#2a8ad0')
    rim = Mt('energy', '#dff8ff')
    grip(w, -30, 56, 2.6, M('slime', '#2a8ad0'))
    for u in (-24, -6, 14, 34):
        w.box(u, 2.9, 1, 2, 2, 2, M('slime', '#7fd8ff'), name='drop')
    w.box(0, 0, 0, 8, 8, 8, M('slime', '#bff6ff', glow=True), name='core_shell')
    gem(w, 0, 0, 0, 4, '#ffffff', name='core')
    collar(w, 56, 4, 3.6, deep)
    p = front_plate(w, 54, 118, -30, 26)
    p.poly([(58, 2), (64, 22), (80, 25), (94, 16), (92, 5), (80, 2)], gel.p(d=1.75, d0=0.5, bev=3), 2)
    p.poly([(62, -2), (68, -18), (78, -26), (77, -12), (72, -2)], deep.p(d=1.25, d0=0.5, bev=2), 2)
    p.sym([(60, 3.4), (84, 4.2), (102, 2.6), (116, 0.1)], gel.p(d=2.25, d0=0.75, bev=2), 3)
    p.stroke([(64, 21), (80, 24), (93, 15)], 1.0, rim.p(inset=0.25), 4)
    p.stroke([(64, 0), (112, 0)], 1.0, rim.p(inset=0.5), 4)
    for (u, v, r) in ((72, 12, 2.2), (84, 10, 1.6), (88, -1, 1.4), (70, -12, 1.6)):
        p.ell(u, v, r, r, rim.p(inset=0.25), 5)
    sp = side_plate(w, 56, 110, -10, 10)
    sp.sym([(60, 2.0), (84, 3.4), (100, 2.0), (112, 0.1)], deep.p(d=1.25), 2)
    if aw:
        w.box(40, 18, 4, 7, 7, 7, M('slime', '#7fd8ff', glow=True), name='aw_fist')
        crystal(w, 72, -30, -4, 16, 3, '#8fe8ff', rot=(0, 0, -20), name='aw_blade')
        crystal(w, 30, -18, 5, 12, 3, '#bff6ff', rot=(0, 0, 35), name='aw_spear')
        halo(w, 0, 9, 7.5, rim, spikes_n=6, name='aw_core_ring', d=0.5)

# =========================================================================================== 11 hephaistos
@weapon('hephaistos', '概念加工の切削槍', 'drill lance', '典域鍛造・概念切削機関')
def d_hephaistos(w, aw):
    steel = Mt('metal', '#8a93a3')
    dark = Mt('metal', '#2a2f3a')
    cyan = Mt('energy', '#62f0ff' if not aw else '#ffd060')
    crys = '#9ff4ff'
    # hilt: crystal cube core in a cage, vamplate
    grip(w, -16, 12, 2.6, hilt('#3a404c', '#22262e'), bands=(-14, 10), band_mt=steel)
    w.box(-20, 0, 0, 6, 6, 6, M('gem', crys, glow=True), rot=(45, 35, 0), name='cube_core')
    ring3d(w, -20, 5, 4, (8, 2, 2), dark, phase=45, name='cage')
    cone(w, 12, 10, 4, 12, steel, steps=3, name='vamplate')
    halo(w, 18, 13.5, 11.5, cyan, spokes=6, name='vamp_ring', d=0.5)
    # drill: stepped cone with helical cutting flutes and glowing grooves
    cone(w, 22, 64, 10, 1.5, steel, steps=8, name='drill')
    coil(w, 22, 82, 7.5, 3.5, dark, thick=2, name='flute')
    coil(w, 24, 80, 7.0, 3.5, cyan, thick=1, phase=180, name='groove')
    crystal(w, 88, 0, 0, 8, 3, crys, name='tip')
    # orbiting machine spheres (arms / eyes / forges)
    def sphere(g, k):
        g.box(0, 0, 0, 5, 5, 5, steel.b(), name='ball')
        g.box(0, 0, 0, 4, 6, 4, dark.b(), rot=(45, 0, 0), name='ball2')
        g.box(0, 3.2, 0, 2, 1, 2, cyan.b(), name='eye')
    orbit(w, 40, 15, 3 if not aw else 6, sphere, phase=10, name='spheres')
    if aw:
        orbit(w, 70, 12, 4, lambda g, k: g.box(0, 0, 0, 3, 3, 3, M('gem', crys, glow=True), rot=(45, 45, 0), name='cube'), name='cubes')
        halo(w, 40, 20, 18.6, cyan, spikes_n=12, name='aw_ring', d=0.5)

# =========================================================================================== 12 nortia
@weapon('nortia', '無法遊戯のピコピコハンマー', 'toy hammer', '盤上遊戯・全ルール改竄')
def d_nortia(w, aw):
    pink = Mt('metal', '#ff8fc0')
    yellow = Mt('metal', '#ffe060')
    cyan = Mt('metal', '#7fe8ff')
    # candy-striped handle
    grip(w, -20, 34, 2.4, M('metal', '#ffffff', pattern='stripes', accent='#ff5f9f'))
    w.box(-23, 0, 0, 5, 5, 5, yellow.b(), name='end')
    w.box(-26, 0, 0, 3, 3, 3, Mt('energy', '#ff5f9f').b(), name='end_gem')
    # head: bellows (pink, accordion ribs) between two yellow end caps with star stickers
    w.box(44, 0, 0, 16, 18, 16, pink.b(), name='bellows')
    for k in range(5):
        w.box(44, -8 + 4 * k, 0, 16, 1, 17, M('metal', '#ff6fb0'), name=f'rib{k}')
    for s in (-1, 1):
        w.box(44, s * 11, 0, 18, 4, 18, yellow.b(), name='cap')
        w.box(44, s * 13.5, 0, 12, 1, 12, cyan.b(), name='cap_face')
        g = w.group(44, s * 14.3, 0, rot=(0, 0, 0), name=f'sticker{s}')
        sp = g.plate(-6, 6, -6, 6, U=(1, 0, 0), V=(0, 0, 1))
        star(sp, 0, 0, 5.5, 2.4, 5, Mt('metal', '#fff4a0').p(d=0.5), 3, rot=-math.pi / 2)
    collar(w, 34, 3, 3.2, yellow)
    # dice and game pieces dangling
    w.box(28, 8, 0, 5, 5, 5, M('metal', '#ffffff', pattern='dots', accent='#202020'), rot=(20, 30, 10), name='die')
    chain(w, [(32 - k * 0.2, 3 + k * 1.3, 0) for k in range(4)], yellow, size=1)
    if aw:
        orbit(w, 44, 20, 5, lambda g, k: g.box(0, 0, 0, 4, 4, 4, M('rainbow', '#ffd0f0', glow=True), rot=(k * 20, 45, 0), name='piece'), name='pieces')
        halo(w, 44, 24, 22.5, Mt('energy', '#ffe060'), spikes_n=5, name='aw_star', d=0.5)

# =========================================================================================== 13 lucifara
@weapon('lucifara', '失楽堕天の大鎌', 'scythe', '万欲堕落・失楽冠鎌')
def d_lucifara(w, aw):
    shaft = Mt('metal', '#1c1622')
    crim = Mt('metal', '#7a1028')
    red = Mt('energy', '#ff3050')
    white = Mt('metal', '#f2eef6')
    blk = Mt('metal', '#241a2e')
    gold = Mt('metal', '#d8b050')
    grip(w, -30, 76, 2.2, hilt('#241a2e', '#120c18'), bands=(-26, 0, 30, 60), band_mt=crim)
    coil(w, 4, 56, 2.9, 2.0, crim, thick=1, name='ribbon')
    cone(w, -36, 6, 3.0, 1.8, gold, steps=2, name='butt')
    crystal(w, -41, 0, 0, 6, 3, '#ff3050', rot=(180, 0, 0), name='butt_spike')
    # head: heart frame with a crimson eye, horns
    collar(w, 78, 6, 4.0, crim)
    octo(w, 84, 6, 4.6, blk, 'head')
    gem(w, 84, 0, 0, 5, '#ff2848', name='eye')
    for s in (-1, 1):
        h = w.group(87, s * 4, 0, rot=(0, 0, s * -40), name=f'horn{s}')
        h.box(3, 0, 0, 6, 2, 2, blk.b(), name='h1')
        h.box(7, 0, 0, 3, 1, 1, red.b(), name='h2')
    # crescent blade: black body, white half-moon layer, serrated back, glowing inner edge
    p = front_plate(w, 58, 104, -70, 10)
    outer = [(86, 3), (95, -10), (100, -27), (98, -44), (91, -57), (78, -66)]
    inner = [(76, -61), (84, -48), (87, -31), (84, -17), (78, -7), (76, 3)]
    p.poly(serrate(outer, 2.0, 4.0, side=1) + inner, blk.p(d=1.5, d0=0.75, bev=3), 2)
    hi = [(86, 2), (94, -10), (98, -27), (96, -42), (89.5, -54), (80, -62)]
    mid = [(82, -58), (91, -44), (93, -28), (90, -14), (84, -5), (82, 2)]
    p.poly(hi + mid, white.p(d=1.75, d0=1.0, bev=2), 3)
    p.stroke([(u - 1.3, v) for u, v in inner[1:-1]], 1.1, red.p(inset=0.25), 4)
    # wings behind the head: angel (white feathers) on -v, demon (bat) on +v
    q = front_plate(w, 66, 118, -10, 40, w=-3)
    bat_wing(q, 86, 4, 0.6, 30, blk.p(d=1.0), 2, fingers=4)
    q2 = front_plate(w, 66, 118, -40, 10, w=-3)
    feather_wing(q2, 86, -4, -0.7, 5, 26, 2.6, white.p(d=1.0), 2, spread=0.55)
    chain(w, [(72, 5 + k * 1.3, 0) for k in range(4)], gold, size=2)
    gem(w, 72, 11, 0, 3, '#ff2848', name='charm')
    if aw:
        halo(w, 84, 16, 14, red, spikes_n=6, name='aw_halo', d=0.5)
        for k in range(5):
            crystal(w, 92 + k * 4, -14 - k * 9, (-1) ** k * 5, 7, 2, '#ff6080', rot=(0, 0, -60 - k * 8), name=f'feather{k}')

# =========================================================================================== 14 taika
@weapon('taika', '超克覇王の拳甲', 'gauntlet', '覇王超克・無限上限拳', hold='fist', scale=0.9)
def d_taika(w, aw):
    iron = Mt('metal', '#3a3436')
    red = Mt('metal', '#a8202a')
    gold = Mt('metal', '#d8a040')
    fire = Mt('energy', '#ff5a2a' if not aw else '#ffd040')
    cone(w, -22, 18, 8.2, 6.0, iron, steps=3, name='bracer')
    octo(w, -22, 3, 8.8, gold, 'cuff_e')
    octo(w, -3, 2, 6.6, gold, 'cuff_w')
    w.box(-13, 0, 7.4, 15, 10, 1, M('metal', '#3a3436', pattern='cracks', accent='#ff5a2a', pattern_glow=True), name='bracer_plate')
    w.box(5, 0, 0, 12, 16, 10, iron.b(), name='fist')
    w.box(5, 0, 0, 10, 17, 11, red.b(), name='fist_plate')
    for k, v in enumerate((-6, -2, 2, 6)):
        w.box(12.5, v, 1, 4, 4, 9, iron.b(), name=f'knuckle{k}')
        w.box(14.8, v, 1, 1, 3, 7, gold.b(), name=f'kface{k}')
        hg = w.group(13, v, 4.5, rot=(0, 25, 0), name=f'khorn{k}')
        hg.box(3, 0, 0, 6, 2, 2, gold.b(), name='kh')
        hg.box(6.5, 0, 0, 2, 1, 1, Mt('metal', '#fff0c0').b(), name='kh2')
    p = front_plate(w, -4, 14, -9, 9, w=5.8)
    p.sym([(-2, 7), (6, 8), (11, 4.5), (12, 0.1)], red.p(d=0.75), 2)
    p.sym([(4, 3.4), (6, 4.6), (7.5, 2.4)], fire.p(d=1.0), 3)
    p.sym([(0, 2.8), (1.5, 3.8), (2.5, 0.1)], gold.p(d=1.0), 3)
    for s in (-1, 1):
        hg = w.group(8, s * 6.5, 5.5, rot=(0, 30, s * 30), name=f'onihorn{s}')
        hg.box(5, 0, 0, 10, 3, 3, gold.b(), name='oh1')
        hg.box(11, 0, 0, 3, 2, 2, Mt('metal', '#fff0c0').b(), name='oh2')
    spikes(w, -20, 6, 8.4, 6, 2, gold, tilt=55, name='elbow_spike')
    if aw:
        orbit(w, 5, 16, 6, lambda g, k: crystal(g, 0, 0, 0, 8, 2, '#ffa040', rot=(0, 0, 90), name='flame'), name='aura')
        halo(w, -12, 13, 11.5, fire, spikes_n=8, name='aw_ring', d=0.5)


from w3d_b import *   # noqa: E402,F401  (designs 15-28)
from w3d_c import *   # noqa: E402,F401  (designs 29-41)

"""3D relic weapon designs 29-41."""
import math
from paint import M
from w3designs import weapon, hilt, curved, centre, band, mirror, layered_blade
from w3parts import (Mt, P, runes, octo, grip, collar, cone, gem, crystal, spikes, fin, chain, halo, disc, side_plate,
                     front_plate, star, sigil, serrate, feather_wing, bat_wing, leaf, coil, ring3d, orbit)

# =========================================================================================== 29 ain_sof_aur
@weapon('ain_sof_aur', '分岐確定の王剣', 'branching sword', '全界分岐・可能性収束の王剣')
def d_ain_sof_aur(w, aw):
    glass = Mt('metal', '#ece8ff')
    rim = Mt('metal', '#b8a8f0')
    prism = Mt('energy', '#c8b8ff')
    gold = Mt('metal', '#e2c060')
    tints = ['#ffb8e8', '#b8e8ff', '#e8ffb8', '#ffd8b8', '#d8b8ff', '#b8ffd8']
    p = front_plate(w, 16, 114, -24, 24)
    p.sym([(18, 5.2), (60, 4.6), (100, 3.2), (107, 1.4), (112, 0.1)], rim.p(d=1.25, d0=0.5, bev=2), 2)
    p.sym([(19, 3.8), (60, 3.2), (100, 2.0), (106, 0.1)], glass.p(d=2.0, d0=1.25, bev=1.5), 3)
    p.sym([(22, 1.2), (98, 0.9), (102, 0.1)], prism.p(inset=0.5), 4)
    for k, (u, s) in enumerate(((34, 1), (48, -1), (62, 1), (76, -1), (88, 1), (99, -1))):
        L = 18 - k * 1.6
        tm = Mt('metal', tints[k])
        pts = [(u - 3, s * 3.5), (u + 1, s * 3.5), (u + L * 0.55, s * (L * 0.62)), (u + L, s * (L * 0.58)),
               (u + L * 0.6, s * (L * 0.42)), (u + 3, s * 4.2)]
        p.poly(pts, tm.p(d=1.5, d0=0.5, bev=1.5), 3)
        p.stroke([(u + 1, s * 3.8), (u + L * 0.55, s * (L * 0.55)), (u + L - 1.5, s * (L * 0.56))], 0.8,
                 Mt('energy', tints[k]).p(inset=0.25), 4)
    w.box(16, 0, 0, 5, 20, 8, gold.b(), name='guard')
    for s in (-1, 1):
        halo(w.group(16, s * 11, 0, rot=(0, 90, 0), name=f'gring{s}'), 0, 4.5, 3.0, gold, name='gr', d=0.75)
    gem(w, 16, 0, 0, 5, '#c8b8ff', name='heart')
    grip(w, -14, 13, 2.8, hilt('#f0ecff', '#8a7ac8', 'diamond'), bands=(-13, 12), band_mt=gold)
    cone(w, -19, 5, 4.4, 3.0, gold, steps=2, name='pommel')
    ring3d(w, -21.5, 3.4, 5, (3, 1, 1), gold, name='pcrown')
    halo(w, 21, 10, 8.6, Mt('energy', '#fff1b0'), spikes_n=5, name='floating_crown', d=0.5)
    if aw:
        for k, a in enumerate((-28, -14, 14, 28)):
            g = w.group(18, 0, -3 - abs(k - 1.5), rot=(0, 0, a), name=f'ghost{k}')
            gp = front_plate(g, 0, 92, -5, 5)
            gp.sym([(2, 2.8), (72, 2.2), (82, 0.1)], Mt('energy', tints[k], glow=0.6).p(d=0.5), 2)
        halo(w, 112, 10, 8.6, Mt('energy', '#fff1b0'), spikes_n=7, name='aw_crown', d=0.5)

# =========================================================================================== 30 angra_mainyu
@weapon('angra_mainyu', '全害惡徳の影鎖鎌', 'kusarigama', '全害顕現・十一悪徳の影鎖')
def d_angra(w, aw):
    black = Mt('metal', '#16121c')
    plum = Mt('metal', '#3a1a3a')
    evil = Mt('energy', '#c03aff' if not aw else '#ff3a5a')
    grip(w, -14, 24, 2.4, hilt('#2a1c2a', '#120c14'), bands=(-12, 22), band_mt=plum)
    w.box(-17, 0, 0, 5, 6, 6, plum.b(), name='butt')
    # sickle blade at right angles, with evil sigils and a hooked back spike
    collar(w, 27, 6, 3.4, plum)
    p = front_plate(w, 18, 46, -48, 8)
    blade = [(26, 3), (34, 2), (40, -8), (42, -22), (38, -36), (30, -46), (33, -34), (34, -20), (32, -8), (26, -3)]
    p.poly(serrate(blade[:6], 1.6, 4.0, side=1) + blade[6:], black.p(d=1.5, d0=0.5, bev=2), 2)
    p.stroke([(31, -6), (33.5, -18), (32.5, -30), (29, -40)], 1.0, evil.p(inset=0.5), 3)
    for u, v in ((36, -14), (37, -26)):
        sigil(p, u, v, 3.2, plum.p(up=0.25), evil.p(up=0.25), 4, n=5)
    hk = w.group(30, 3, 0, rot=(0, 0, -35), name='hook')
    hk.box(3, 0, 0, 7, 2, 3, black.b(), name='hk')
    # chain with a spiked weight, loosely coiled around the handle and hanging
    pts = []
    for k in range(18):
        a = k * 0.55
        pts.append((-18 - k * 1.7, 4.5 * math.cos(a), 4.5 * math.sin(a)))
    chain(w, pts, Mt('metal', '#5a4a5a'), size=2)
    w.box(-50, 0, 0, 6, 6, 6, plum.b(), rot=(45, 45, 0), name='weight')
    spikes(w, -50, 5, 3.2, 4, 1, Mt('metal', '#8a7a8a'), tilt=0, name='wspike')
    gem(w, -50, 0, 0, 3, '#c03aff', name='weight_eye')
    if aw:
        orbit(w, 30, 18, 11, lambda g, k: gem(g, 0, 0, 0, 2, '#ff3a5a', name='vice'), name='vices')
        for k in range(3):
            crystal(w, 20 + k * 8, -50 + k * 4, (-1) ** k * 4, 8, 3, '#2a1030', rot=(0, 0, -100 + k * 15), name=f'shadow{k}')
        halo(w, 30, 22, 20.5, evil, spikes_n=11, name='aw_halo', d=0.5)

# =========================================================================================== 31 magna_mater
@weapon('magna_mater', '命を継ぐ蔓鞭', 'vine whip', '始源母胎・万生命の揺籃')
def d_magna(w, aw):
    wood = Mt('wood', '#6a4a2a')
    vine = Mt('wood', '#4a7a2a')
    leafm = Mt('cloth', '#6fbf4a')
    bloom = Mt('cloth', '#ffb0d0')
    grip(w, -14, 10, 2.6, wood)
    coil(w, -12, 8, 3.0, 2, vine, thick=1, name='hvine')
    for k in range(5):
        g = w.group(12, 0, 0, rot=(72 * k, 0, 0), name=f'petal{k}')
        g.box(1, 4, 0, 3, 6, 2, bloom.b(), rot=(0, 0, -25), name='petal')
    gem(w, 12, 0, 0, 3, '#ffe060', name='pistil')
    w.box(-17, 0, 0, 4, 5, 5, wood.b(), name='knob')
    # the whip: a loose helix of vine segments with thorns and leaves, ending in a blossom
    n = 26
    prev = None
    for i in range(n):
        t = i / (n - 1)
        a = 2 * math.pi * 1.6 * t
        r = 3 + 7 * t
        u = 14 + 74 * t
        g = w.group(u, r * math.cos(a), r * math.sin(a), rot=(math.degrees(a), 0, 0), name=f'seg{i}')
        g.box(0, 0, 0, 4, 2, 2, vine.b(), name='seg')
        if i % 3 == 1:
            g.box(0, 1.6, 0, 2, 2, 1, Mt('metal', '#c8e0a0').b(), rot=(0, 0, 45), name='thorn')
        if i % 4 == 2:
            lg = g.group(0, 0, 1.5, name=f'leafg{i}')
            lp = lg.plate(-4, 4, -2, 8, U=(1, 0, 0), V=(0, 0, 1))
            leaf(lp, 0, 0, math.pi / 2, 7, 2.6, leafm.p(d=0.5), 2)
    end = w.group(90, 10 * math.cos(2 * math.pi * 1.6), 10 * math.sin(2 * math.pi * 1.6), name='blossom')
    for k in range(6):
        b = end.group(0, 0, 0, rot=(60 * k, 0, 0), name=f'bp{k}')
        b.box(2, 3, 0, 5, 5, 2, bloom.b(), rot=(0, 0, -40), name='bpetal')
    gem(end, 1, 0, 0, 3, '#ffe060', name='bcore')
    if aw:
        orbit(w, 50, 18, 7, lambda g, k: gem(g, 0, 0, 0, 3, ['#ff9fd0', '#9fffb0', '#ffe080'][k % 3], name='seed'), name='seeds')
        halo(w, 12, 14, 12.5, Mt('energy', '#9fffb0'), spikes_n=10, name='aw_halo', d=0.5)

# =========================================================================================== 32 ouroboros
@weapon('ouroboros', '無限円環の輪刃', 'chakram', '無限円環・輪廻永劫の大輪', scale=0.8)
def d_ouroboros(w, aw):
    gold = Mt('metal', '#d8b050')
    steel = Mt('metal', '#cfd6e2')
    snake = Mt('scale', '#2a6a5a')
    time = Mt('energy', '#9fffe0' if not aw else '#ffe080')
    C = 22
    p = front_plate(w, C - 30, C + 30, -30, 30)
    p.ring(C, 0, 26, 23, steel.p(d=0.75, d0=0.5, bev=1), 1)
    for k in range(24):
        a = 2 * math.pi * k / 24
        b = a + 2 * math.pi / 24 * 0.8
        p.poly([(C + math.cos(a) * 25.5, math.sin(a) * 25.5), (C + math.cos(a + 0.05) * 29, math.sin(a + 0.05) * 29),
                (C + math.cos(b) * 25.5, math.sin(b) * 25.5)], steel.p(d=0.5), 1)
    p.ring(C, 0, 24, 19, gold.p(d=1.75, d0=1.0, bev=1.5), 2)
    for k in range(4):
        a = 2 * math.pi * k / 4 + math.pi / 4
        p.stroke([(C + math.cos(a) * 4, math.sin(a) * 4), (C + math.cos(a) * 19, math.sin(a) * 19)], 1.6, gold.p(d=1.0), 1)
    for k in range(12):
        a = 2 * math.pi * k / 12
        p.dot(C + math.cos(a) * 21.5, math.sin(a) * 21.5, time.p(up=0.5), 4, r=0.9)
    p.ring(C, 0, 19, 17.6, time.p(inset=0.25), 3)
    # the serpent biting its tail, as a coil of scale blocks around the ring
    n = 36
    for i in range(n):
        a = 360 * i / n
        g = w.group(C, 0, 0, rot=(0, 0, a), name=f'sn{i}')
        th = 3 if i < n - 4 else 2
        g.box(0, 21.5, 0, 3, th, 4, snake.b(), name='body')
    hd = w.group(C, 0, 0, rot=(0, 0, 0), name='head')
    hd.box(0, 21.5, 0, 5, 5, 6, snake.b(), name='head')
    hd.box(-1, 21.5, 3.4, 2, 2, 1, Mt('energy', '#ff4a4a').b(), name='eye')
    # inner grip bar across the ring (the grip point is u = 0)
    w.box(0, 0, 0, 3, 32, 4, hilt('#3a3020', '#1a1408'), name='bar')
    w.box(0, 0, 0, 12, 4, 4, hilt('#3a3020', '#1a1408'), name='handle')
    w.box(C, 0, 0, 6, 6, 6, gold.b(), rot=(45, 0, 45), name='hub')
    gem(w, C, 0, 0, 3, '#9fffe0', name='hub_gem')
    if aw:
        halo(w.group(C, 0, 0, name='aw'), 0, 30, 28.6, time, spikes_n=12, name='aw_ring', d=0.5)
        halo(w.group(C, 0, 0, rot=(0, 0, 90), name='aw2'), 0, 26, 24.6, gold, spikes_n=0, name='aw_ring2', d=0.5)

# =========================================================================================== 33 yggdrasil
@weapon('yggdrasil', '玖天神樹の若枝', 'wand', '玖天神樹・九界開花', scale=0.8)
def d_yggdrasil(w, aw):
    bark = Mt('wood', '#a89050')
    bark2 = Mt('wood', '#c8b060')
    leafm = Mt('cloth', '#8fe060')
    fruits = ['#ff8fa0', '#ffd060', '#8fd0ff', '#b08fff', '#8fffc0', '#ffffff', '#ffa060', '#ff60c0', '#60ffe0']
    grip(w, -16, 40, 2.0, bark)
    coil(w, -14, 38, 2.2, 1.5, bark2, thick=1, name='bark_twist')
    w.box(-18, 0, 0, 4, 5, 5, bark2.b(), name='root_knob')
    for k in range(3):
        rg = w.group(-18, 0, 0, rot=(120 * k, 0, 0), name=f'root{k}')
        rg.box(-3, 2, 0, 6, 1, 1, bark.b(), rot=(0, 0, 30), name='root')
    # canopy of branches holding nine glowing fruits
    tips = []
    for k in range(9):
        a = 360 * k / 9
        lean = 25 + 15 * (k % 3)
        g = w.group(40, 0, 0, rot=(a, 0, 0), name=f'br{k}')
        bg = g.group(0, 0, 0, rot=(0, 0, -lean), name=f'brl{k}')
        L = 10 + 4 * (k % 3)
        bg.box(L / 2, 0, 0, L, 2, 2, bark.b(), name='branch')
        gem(bg, L + 1.5, 0, 0, 3, fruits[k], name='fruit')
        lp = bg.plate(-2, 10, -4, 4, u=L * 0.4, w=1.2, U=(1, 0, 0), V=(0, 1, 0))
        leaf(lp, 0, 0, 0.6, 8, 2.4, leafm.p(d=0.5), 2)
    octo(w, 44, 8, 2.6, bark2, 'crown_wood')
    gem(w, 50, 0, 0, 4, '#e8ffd0', name='sap')
    if aw:
        halo(w, 52, 20, 18.6, Mt('energy', '#c8ff8f'), spikes_n=9, name='aw_worlds', d=0.5)
        orbit(w, 52, 24, 9, lambda g, k: gem(g, 0, 0, 0, 3, fruits[k], name='world'), name='nine')
        for k in range(5):
            g = w.group(46, 0, 0, rot=(72 * k, 0, 0), name=f'bl{k}')
            g.box(0, 5, 0, 3, 3, 3, Mt('cloth', '#fff0f6').b(), rot=(45, 0, 45), name='blossom')

# =========================================================================================== 34 miyohime
@weapon('miyohime', '万律自在の神楽鈴', 'kagura bell', '万律自在・禍津神楽', scale=0.8)
def d_miyohime(w, aw):
    gold = Mt('metal', '#e8c050')
    red = Mt('metal', '#c02840')
    night = Mt('metal', '#1e1a30')
    grip(w, -14, 22, 2.2, hilt('#c02840', '#6a1020'), bands=(-12, 20), band_mt=gold)
    # five-colour streamers (go-shiki) hanging from the pommel ring
    halo(w, -16, 4, 2.8, gold, name='pring', d=0.75)
    for k, col in enumerate(('#3a6aff', '#ff3a3a', '#ffe03a', '#ffffff', '#7a3aff')):
        g = w.group(-16, 3 * math.cos(k * 1.26), 3 * math.sin(k * 1.26), rot=(k * 72, 0, 0), name=f'streamer{k}')
        sp = g.plate(-34, 0, -1.5, 1.5, U=(1, 0, 0), V=(0, 0, 1))
        sp.poly([(-1, -1.4), (-30 - k, -1.2), (-33 - k, 0), (-30 - k, 1.2), (-1, 1.4)], Mt('cloth', col).p(d=0.25), 2)
    # bell tree: three tiers of bells around a spire
    octo(w, 34, 24, 1.6, gold, 'spire')
    for tier, (u, r, n) in enumerate(((28, 7, 5), (37, 5.5, 5), (45, 4, 4))):
        halo(w, u + 1.5, r + 0.5, r - 0.5, gold, name=f'tier{tier}', d=0.5)
        for k in range(n):
            g = w.group(u, 0, 0, rot=(360 * k / n + tier * 20, 0, 0), name=f'bell{tier}_{k}')
            g.box(0, r, 0, 3, 3, 3, gold.b(), rot=(45, 0, 0), name='bell')
            g.box(-1.5, r, 0, 1, 1, 1, Mt('energy', '#fff0b0').b(), name='clapper')
    gem(w, 50, 0, 0, 4, '#ff6fd0', name='spire_gem')
    # polychrome geometric halo (vertical, in the drawing plane) behind the bells
    q = front_plate(w, 24, 76, -26, 26, w=-4)
    star(q, 50, 0, 22, 14, 8, Mt('metal', '#2a2440').p(d=0.5), 2, rot=0.2)
    q.ring(50, 0, 17, 15.6, Mt('energy', '#ff9fe0').p(d=0.5), 3)
    for k in range(8):
        a = 0.2 + 2 * math.pi * k / 8
        q.dot(50 + math.cos(a) * 20, math.sin(a) * 20, Mt('energy', ['#ff6060', '#ffd060', '#60ff90', '#60d0ff', '#b060ff'][k % 5]).p(d=0.75), 4, r=1.0)
    if aw:
        def crys(g, k):
            g.box(0, 0, 0, 5, 2, 2, M('gem', '#7a5aff', glow=True), rot=(0, k * 30, 45), name='starsea')
            g.box(0, 0, 0, 1, 1, 1, Mt('energy', '#ffffff').b(), name='starsea_core')
        orbit(w, 50, 26, 8, crys, name='starsea')
        star(front_plate(w, 10, 90, -40, 40, w=-6), 50, 0, 36, 24, 12, Mt('energy', '#c060ff', glow=0.5).p(d=0.25), 2)

# =========================================================================================== 35 innocence
@weapon('innocence', '無垢なる全能のぬいぐるみ', 'plush', '無垢なる全能・夢想の王冠', hold='fist', scale=0.9)
def d_innocence(w, aw):
    fluff = M('cloth', '#f6eefc', soft=1.2)
    fluff2 = M('cloth', '#e4d6f4', soft=1.2)
    pink = M('cloth', '#ffc8e0', soft=1.0)
    stitch = Mt('metal', '#5a4a70')
    # held by one ear: u = 0 at the ear tip, the bunny hangs below (+u runs down the arm)
    w.box(6, -3.5, 0, 12, 4, 3, fluff, name='ear_held')
    w.box(6, -3.5, 1.8, 10, 2, 1, pink, name='ear_inner')
    e2 = w.group(10, 3.5, 0, rot=(0, 0, -25), name='ear2')
    e2.box(-4, 0, 0, 10, 4, 3, fluff, name='ear2b')
    e2.box(-4, 0, 1.8, 8, 2, 1, pink, name='ear2_inner')
    w.box(20, 0, 0, 13, 16, 13, fluff, name='head')
    w.box(20, 0, 0, 11, 17, 11, fluff, name='head_round')
    w.box(20, 0, 0, 11, 14, 14, fluff, name='head_round2')
    for s in (-1, 1):
        w.box(20, s * 3.6, 7.0, 3, 3, 1, M('gem', '#4a3aa0' if s < 0 else '#e0a040', glow=True), name='button_eye')
        w.box(23.5, s * 5.5, 6.8, 2, 2, 1, pink, name='cheek')
    w.box(24, 0, 7.0, 2, 1, 1, stitch.b(), name='nose')
    w.box(25.5, 0, 6.8, 1, 3, 1, stitch.b(), name='mouth')
    w.box(36, 0, 0, 14, 13, 11, fluff2, name='body')
    w.box(36, 0, 5.8, 8, 7, 1, fluff, name='belly')
    w.box(35, 0, 6.6, 4, 4, 1, M('rainbow', '#ff8fd0', glow=True), rot=(0, 0, 45), name='heart_patch')
    for s in (-1, 1):
        a = w.group(31, s * 7, 0, rot=(0, 0, s * 35), name=f'arm{s}')
        a.box(3.5, 0, 0, 8, 4, 4, fluff, name='arm')
        l = w.group(43, s * 3.6, 1, name=f'leg{s}')
        l.box(3, 0, 0, 6, 5, 6, fluff, name='leg')
        l.box(5.8, 0, 1, 1, 4, 4, pink, name='paw')
    w.box(42, 0, -6.2, 4, 4, 3, M('cloth', '#ffffff'), name='tail')
    w.box(30, 0, 0, 3, 14, 12, M('cloth', '#ff8fb8'), name='ribbon')
    w.box(30, 0, 6.6, 3, 3, 2, M('cloth', '#ff6fa0'), name='bow')
    if aw:
        ring3d(w, 12, 5.6, 6, (3, 2, 2), Mt('metal', '#ffe060'), name='crown')
        halo(w, 9, 11, 9.6, Mt('energy', '#ffffff'), spikes_n=8, name='aw_halo', d=0.5)
        orbit(w, 30, 20, 6, lambda g, k: gem(g, 0, 0, 0, 3, ['#ff8fd0', '#8fd0ff', '#ffe08f', '#b08fff', '#8fffb0', '#ffffff'][k], name='wish'), name='wishes')

# =========================================================================================== 36 brutality
@weapon('brutality', '凄惨暴虐の鬼金棒', 'kanabo', '凄惨暴虐・万骨砕きの鬼神棒', scale=0.85)
def d_brutality(w, aw):
    iron = Mt('metal', '#3e3a3a')
    rust = Mt('metal', '#6a3a2a')
    blood = Mt('energy', '#ff2a2a') if aw else Mt('metal', '#7a1414')
    grip(w, -20, 14, 2.6, hilt('#4a2a1a', '#2a160c'), bands=(-18, 12), band_mt=rust)
    w.box(-24, 0, 0, 6, 7, 7, iron.b(), name='pommel')
    w.box(-28, 0, 0, 4, 4, 4, iron.b(), rot=(45, 0, 45), name='pommel_ring')
    # club body: widening octagon, rows of studs, red-stained bands, wrapped chain
    cone(w, 16, 70, 4.0, 8.5, iron, steps=6, name='club')
    for row, u in enumerate(range(24, 86, 7)):
        r = 4.0 + 4.5 * (u - 16) / 70 + 0.6
        ring3d(w, u, r, 8, (2, 2, 2), Mt('metal', '#8a8080'), phase=22.5 * (row % 2), name=f'stud{row}')
    for u in (30, 58):
        octo(w, u, 3, 6.4 + 4.5 * (u - 16) / 70, blood, f'band{u}')
    pts = [(40 + k * 1.6, 7.6 * math.cos(k * 0.6), 7.6 * math.sin(k * 0.6)) for k in range(12)]
    chain(w, pts, Mt('metal', '#7a7070'), size=2)
    octo(w, 88, 4, 7.2, iron, 'cap')
    spikes(w, 90, 4, 3, 5, 2, Mt('metal', '#8a8080'), tilt=50, name='cap_spike')
    if aw:
        for row, u in enumerate((36, 52, 68, 84)):
            spikes(w, u, 6, 6.5 + 4.5 * (u - 16) / 70, 6, 2, Mt('metal', '#a09898'), tilt=80, phase=30 * row, name=f'aw_sp{row}')
        w.box(60, 0, 0, 50, 1, 19, M('metal', '#3e3a3a', pattern='cracks', accent='#ff2a2a', pattern_glow=True), name='cracks')

# =========================================================================================== 37 cursed_love
@weapon('cursed_love', '悲劇の操り人形', 'marionette', '悲劇愛好・終幕の操糸', hold='fist', scale=0.9)
def d_cursed(w, aw):
    wood = Mt('wood', '#3a2420')
    gold = Mt('metal', '#c8a050')
    wine = Mt('cloth', '#6a1028')
    wine2 = Mt('cloth', '#8a1a38')
    porcelain = Mt('metal', '#f6eeee')
    string = M('cloth', '#f0d0dc' if not aw else '#ff4a6a')
    # control cross at the grip (u = 0); strings hang down (+u) to the doll
    w.box(0, 0, 0, 3, 24, 3, wood.b(), name='bar_v')
    w.box(0, 0, 0, 3, 3, 20, wood.b(), name='bar_w')
    w.box(-3, 0, 0, 6, 3, 3, hilt('#4a2a28', '#2a1414'), name='handle')
    for v, wz in ((-12, 0), (12, 0), (0, -10), (0, 10)):
        w.box(0, v, wz, 3, 3, 3, gold.b(), rot=(45, 0, 0), name='tip')
    gem(w, -1, 0, 0, 3, '#ff6f9f', name='heart_knot')
    def strand(v0, w0, v1, w1, u1, name):
        L = math.sqrt((u1 - 1) ** 2 + (v1 - v0) ** 2 + (w1 - w0) ** 2)
        g = w.group(1, v0, w0, rot=(0, math.degrees(math.atan2(w1 - w0, u1 - 1)), -math.degrees(math.atan2(v1 - v0, u1 - 1))), name=name)
        g.box(L / 2, 0, 0, L, 1, 1, string, name='str')
    strand(-12, 0, -5, 0, 33, 'str_l')
    strand(12, 0, 5, 0, 33, 'str_r')
    strand(0, -10, 0, -2, 46, 'str_b')
    strand(0, 10, 0, 1, 26, 'str_h')
    # the doll: porcelain face, black hair with bangs, wine dress, broken heart
    w.box(28, 0, 0, 8, 8, 8, porcelain.b(), name='doll_head')
    w.box(26.5, 0, -1, 6, 10, 8, Mt('cloth', '#141018').b(), name='doll_hair')
    w.box(25, 0, 3.6, 2, 8, 1, Mt('cloth', '#141018').b(), name='bangs')
    for s in (-1, 1):
        w.box(28.5, s * 1.8, 4.1, 1, 2, 1, Mt('energy', '#a01030').b(), name='doll_eye')
        w.box(31, s * 5, -1, 8, 2, 2, Mt('cloth', '#141018').b(), name='hair_tail')
    w.box(36, 0, 0, 8, 7, 5, wine.b(), name='bodice')
    cone(w, 40, 10, 4.5, 7.5, wine2, steps=3, name='skirt')
    w.box(44, 0, 0, 2, 16, 16, M('cloth', '#f0e0e8'), name='petticoat_hem')
    w.box(35, 1.2, 2.8, 2, 2, 1, Mt('energy', '#ff2a4a').b(), rot=(0, 0, 45), name='broken_heart')
    for s in (-1, 1):
        w.box(35, s * 5, 0, 8, 2, 2, porcelain.b(), rot=(0, 0, s * 20), name='doll_arm')
        w.box(51, s * 2.2, 0, 6, 2, 2, porcelain.b(), name='doll_leg')
    if aw:
        for k, v in enumerate((-18, 18)):
            g = w.group(30, v, -5, name=f'doll2{k}')
            g.box(0, 0, 0, 7, 7, 7, porcelain.b(), name='h')
            g.box(-1.5, 0, -1, 5, 9, 7, Mt('cloth', '#141018').b(), name='hair')
            g.box(9, 0, 0, 12, 9, 7, wine.b(), name='b')
            g.box(-15, 0, 0, 30, 1, 1, string, name='s')
        orbit(w, 38, 15, 5, lambda g, k: g.box(0, 0, 0, 3, 3, 1, Mt('energy', '#ff3a5a').b(), rot=(0, 0, 45), name='heart'), name='hearts')

# =========================================================================================== 38 relentless_research
@weapon('relentless_research', '救済実験の大注射器', 'syringe', '救済強制・全生命治験', scale=0.85)
def d_research(w, aw):
    steel = Mt('metal', '#c8d0d8')
    dark = Mt('metal', '#4a525c')
    serum = Mt('energy', '#7fff9f' if not aw else '#ff7fd0')
    glass = M('gem', '#e8fbff', glow=False, alpha=0.42)
    # plunger handle (grip) and finger flange
    w.box(-12, 0, 0, 3, 14, 6, steel.b(), name='thumb_ring')
    octo(w, -4, 14, 1.4, steel, 'rod')
    w.box(4, 0, 0, 3, 20, 8, dark.b(), name='flange')
    for s in (-1, 1):
        w.box(4, s * 10.5, 0, 4, 3, 9, steel.b(), name='flange_tip')
    # barrel: glass shell, glowing serum column, scale marks, steel cage ribs
    w.box(28, 0, 0, 44, 10, 10, glass, name='barrel_glass')
    w.box(30, 0, 0, 38, 7, 7, serum.b(), name='serum')
    w.box(10, 0, 0, 4, 9, 9, dark.b(), name='plunger_head')
    for k in range(8):
        w.box(14 + k * 5, 5.6, 0, 1, 1, 6, dark.b(), name='mark')
    for k in range(4):
        g = w.group(28, 0, 0, rot=(45 + 90 * k, 0, 0), name=f'rib{k}')
        g.box(0, 6.5, 0, 46, 1, 2, steel.b(), name='rib')
    collar(w, 51, 4, 6.4, steel)
    cone(w, 54, 8, 4.5, 1.5, steel, steps=3, name='hub')
    # the needle: long, with a bevelled glowing tip
    octo(w, 76, 36, 0.8, Mt('metal', '#eef2f6'), 'needle')
    p = side_plate(w, 88, 100, -3, 3)
    p.sym([(90, 1.5), (96, 1.0), (99, 0.1)], serum.p(d=0.5), 2)
    if aw:
        def vial(g, k):
            g.box(0, 0, 0, 8, 3, 3, glass, name='vial')
            g.box(0, 0, 0, 6, 2, 2, Mt('energy', ['#ff7fd0', '#7fd0ff', '#ffe07f'][k % 3]).b(), name='vial_serum')
        orbit(w, 28, 13, 6, vial, name='vials')
        for s in (-1, 1):
            a = w.group(46, s * 6, 0, rot=(0, 0, s * -50), name=f'arm{s}')
            a.box(5, 0, 0, 10, 2, 2, dark.b(), name='a1')
            a.box(11, 0, 0, 3, 4, 2, steel.b(), name='claw')

# =========================================================================================== 39 forbidden_arcana
@weapon('forbidden_arcana', '禁理術式の鎖刃', 'chain blade', '禁理拡散・世界術式網')
def d_forbidden(w, aw):
    black = Mt('metal', '#1e1828')
    rim = Mt('metal', '#7a6ab8')
    glyph = Mt('energy', '#b88fff' if not aw else '#ff8fe8')
    grip(w, -14, 13, 2.8, hilt('#2a2236', '#120e18'), bands=(-13, 12), band_mt=rim)
    w.box(16, 0, 0, 5, 24, 8, rim.b(), name='guard')
    for s in (-1, 1):
        crystal(w, 17, s * 13, 0, 7, 3, '#b88fff', rot=(0, 0, s * -60), name='gcrys')
    gem(w, 16, 0, 0, 5, '#b88fff', name='guard_gem')
    gem(w, -18, 0, 0, 4, '#b88fff', name='pommel_gem')
    cone(w, -17, 3, 3.6, 2.6, rim, steps=1, name='pommel')
    # snake-sword: blade segments around a glowing spell-chain spine
    amp = 3.0 if not aw else 7.0
    u, n = 19, 7
    spine = []
    for k in range(n):
        off = amp * math.sin(k * 0.9)
        L = 15 - k * 0.6
        hw = 8.5 - k * 0.5
        p = front_plate(w, u - 1, u + L + 2, off - hw - 2, off + hw + 2)
        p.poly([(u, off - 2.5), (u + L * 0.35, off - hw), (u + L, off - 1.0), (u + L + 1.5, off), (u + L, off + 1.0),
                (u + L * 0.35, off + hw), (u, off + 2.5)], black.p(d=1.5, d0=0.5, bev=2), 2)
        p.poly([(u + 2, off), (u + L * 0.35, off - hw + 2.6), (u + L - 1.5, off), (u + L * 0.35, off + hw - 2.6)], rim.p(up=0.25), 3)
        sigil(p, u + L * 0.38, off, min(3.6, hw - 3.2), black.p(up=0.5), glyph.p(up=0.75), 4, n=5)
        spine.append((u + L * 0.5, off))
        u += L + 2.5
    for k in range(len(spine) - 1):
        (u0, v0), (u1, v1) = spine[k], spine[k + 1]
        g = w.group(u0, v0, 0, rot=(0, 0, -math.degrees(math.atan2(v1 - v0, u1 - u0))), name=f'link{k}')
        L = math.hypot(u1 - u0, v1 - v0)
        g.box(L / 2, 0, 0, L, 2, 2, glyph.b(), name='chain')
        g.box(L / 2, 0, 0, 3, 3, 3, rim.b(), rot=(45, 0, 0), name='ring')
    if aw:
        orbit(w, 60, 22, 5, lambda g, k: sigil(front_plate(g, -7, 7, -7, 7), 0, 0, 6, rim.p(d=0.5), glyph.p(d=0.5), 3, n=5), name='sigils')

# =========================================================================================== 40 fallen_savior
@weapon('fallen_savior', '救堕の古聖剣', 'old holy sword', '救堕終幕・神殺しの聖剣')
def d_fallen(w, aw):
    silver = Mt('metal', '#cfd4dc')
    gold = Mt('metal', '#b8a060')
    worn = Mt('metal', '#9aa0aa')
    holy = Mt('energy', '#bfe0ff' if not aw else '#ff3a3a')
    p = front_plate(w, 18, 112, -10, 10)
    half = [(19, 6.5), (40, 6.0), (80, 5.0), (100, 3.5), (108, 1.5), (111, 0.1)]
    p.sym(half, (silver if not aw else Mt('metal', '#3a3438')).p(d=1.75, d0=0.5, bev=2.5), 2)
    p.sym([(22, 1.6), (90, 1.2), (96, 0.1)], gold.p(inset=0.5), 3)
    for u in (30, 42, 54):
        p.stroke([(u, -1), (u + 4, 1)], 0.6, holy.p(inset=0.5), 4)
    if aw:
        for k, (u0, v0) in enumerate(((22, 0), (26, -2), (25, 3))):
            p.stroke([(u0, v0), (u0 + 10, v0 + (k - 1) * 3), (u0 + 22, v0 + (k - 1) * 5)], 0.9, holy.p(inset=0.5), 5)
    # winged crossguard (tarnished), cracked gem
    w.box(16, 0, 0, 4, 24, 6, gold.b(), name='guard')
    q = front_plate(w, 8, 36, -26, 26, w=0)
    for s in (-1, 1):
        feather_wing(q, 16, s * 10, s * 1.3, 4, 13, 1.8, worn.p(d=1.0), 2, spread=0.45)
    gem(w, 16, 0, 0, 5, '#7fb0ff' if not aw else '#ff2a2a', name='gem')
    w.box(16, 0, 3.2, 1, 5, 1, Mt('metal', '#2a2a30').b(), rot=(0, 0, 30), name='crack')
    grip(w, -15, 13, 2.6, hilt('#6a4a30', '#3a2818'), bands=(-14, 0, 12), band_mt=worn)
    cone(w, -19, 5, 3.6, 2.4, gold, steps=2, name='pommel')
    gem(w, -21.5, 0, 0, 3, '#7fb0ff' if not aw else '#ff2a2a', name='pommel_gem')
    for k in range(3):
        g = w.group(-2 + k * 6, 3, 0, rot=(0, 0, 160 - k * 5), name=f'cloth{k}')
        g.box(4, 0, 0, 8, 1, 3, Mt('cloth', '#e8e0d0').b(), name='rag')
    if aw:
        halo(w, 18, 14, 12.5, Mt('energy', '#2a0a0a'), spikes_n=8, name='aw_halo_dark', d=0.5)
        orbit(w, 60, 14, 4, lambda g, k: crystal(g, 0, 0, 0, 6, 2, '#ff4a4a', rot=(0, 0, 180), name='judg'), name='judgment')

# =========================================================================================== 41 sweet_pact
@weapon('sweet_pact', '未来債権の天秤', 'scales', '甘契完済・未来全差押え')
def d_sweet(w, aw):
    honey = Mt('metal', '#e0a83a')
    dark = Mt('metal', '#3a2a1c')
    parch = Mt('cloth', '#f2e4c0')
    eye = Mt('energy', '#ffcf4a' if not aw else '#ff4a8a')
    grip(w, -30, 56, 2.2, hilt('#3a2a1c', '#1c140c'), bands=(-24, 0, 24, 48), band_mt=honey)
    cone(w, -36, 6, 3.0, 2.0, honey, steps=2, name='butt')
    w.box(-39, 0, 0, 3, 3, 3, M('gem', '#ffcf4a', glow=True), rot=(45, 0, 45), name='honey_drop')
    # fulcrum with an eye, balance beam, hanging pans
    octo(w, 60, 8, 3.6, honey, 'fulcrum')
    p = front_plate(w, 56, 76, -10, 10, w=3.8)
    p.ell(66, 0, 4.5, 6.5, Mt('metal', '#fff4e0').p(d=0.75), 2)
    p.ell(66, 0, 3.0, 3.0, eye.p(d=1.0), 3)
    p.ell(66, 0, 1.2, 1.2, Mt('metal', '#1a1008').p(d=1.25), 4)
    w.box(68, 0, 0, 3, 46, 3, honey.b(), name='beam')
    for s in (-1, 1):
        w.box(68, s * 23, 0, 4, 3, 3, honey.b(), rot=(45, 0, 0), name='beam_end')
        for wz in (-3, 3):
            g = w.group(68, s * 23, wz, rot=(0, 0, 0), name=f'pan_chain{s}{wz}')
            chain(g, [(-2 - k * 2.2, 0, 0) for k in range(6)], honey, size=1)
        pan = w.group(53, s * 23, 0, name=f'pan{s}')
        halo(pan, 0, 7, 0.1, honey, name='pan', d=0.75)
        pan.box(1.5, 0, 0, 2, 10, 10, dark.b(), rot=(45, 0, 0), name='pan_bottom')
    # contract scroll on one pan, coins on the other
    w.box(55, -23, 0, 4, 8, 4, parch.b(), rot=(0, 30, 0), name='scroll')
    for k in range(3):
        w.box(55 + k * 1.2, 23 + (k - 1) * 2, 0, 1, 3, 3, honey.b(), name='coin')
    halo(w, 74, 5, 3.8, honey, spikes_n=6, name='crest', d=0.5)
    if aw:
        orbit(w, 66, 22, 6, lambda g, k: g.box(0, 0, 0, 5, 1, 4, parch.b(), rot=(k * 25, 30, 10), name='contract'), name='contracts')
        halo(w, 66, 28, 26.6, eye, spikes_n=12, name='aw_halo', d=0.5)

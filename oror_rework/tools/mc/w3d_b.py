"""3D relic weapon designs 15-28."""
import math
from paint import M
from w3designs import weapon, hilt, curved, centre, band, mirror, layered_blade
from w3parts import (Mt, P, runes, octo, grip, collar, cone, gem, crystal, spikes, fin, chain, halo, disc, side_plate,
                     front_plate, star, sigil, serrate, feather_wing, bat_wing, leaf, coil, ring3d, orbit)

# =========================================================================================== 15 mary_sue
@weapon('mary_sue', '次章の英雄譚', 'book', '覚醒進化・最終章の主人公補正', hold='fist', scale=0.9)
def d_mary_sue(w, aw):
    cover = Mt('metal', '#7a1f3a' if not aw else '#f2e6c8')
    gold = Mt('metal', '#e8c060')
    page = M('cloth', '#fbf6e6', pattern='stripes', accent='#e8dcc0')
    text = Mt('energy', '#ffd86a')
    # spine along u (grip point at its middle), covers opening into a V towards the viewer
    octo(w, 4, 30, 2.6, gold, 'spine')
    for s in (-1, 1):
        g = w.group(4, 0, 0, rot=(s * -32, 0, 0), name=f'cover{s}')
        g.box(0, s * 10.5, 0, 30, 20, 2, cover.b(), name='board')
        for du in (-13, 13):
            g.box(du, s * 18.5, 0.6, 4, 4, 3, gold.b(), name='corner')
        g.box(0, s * 10, -2, 28, 18, 3, page, name='pages')
        pl = g.plate(-15, 15, -12, 12, v=s * 10.5, w=-3.6, U=(1, 0, 0), V=(0, 1, 0))
        for k in range(6):
            pl.stroke([(-10 + k * 4, -7), (-10 + k * 4, 7)], 0.9, text.p(d=0.25), 3)
        if s > 0:
            em = g.plate(-15, 15, -12, 12, v=s * 10.5, w=1.2, U=(1, 0, 0), V=(0, 1, 0))
            star(em, 0, 0, 8, 3.2, 5, gold.p(d=0.75), 3, rot=-math.pi / 2)
            em.ell(0, 0, 2.2, 2.2, Mt('gem', '#ff9fc0').p(d=1.0), 5)
    # fanned standing pages with glowing lines
    for k, a in enumerate((-14, 0, 14)):
        g = w.group(4, 0, 2, rot=(a, 0, 0), name=f'leaf{k}')
        pl = g.plate(-14, 14, -1, 16, U=(1, 0, 0), V=(0, 0, 1))
        pl.poly([(-13, 0), (13, 0), (12, 13), (-12, 14)], Mt('cloth', '#fffaf0').p(d=0.25), 2)
        for j in range(4):
            pl.stroke([(-9, 3 + j * 3), (9, 3 + j * 3)], 0.7, text.p(d=0.25), 3)
    # bookmark ribbon and clasp
    rb = w.group(-11, 2, 0, rot=(0, 0, 12), name='ribbon')
    rb.box(-6, 0, 0, 12, 2, 1, Mt('cloth', '#e0405a').b(), name='rib')
    gem(w, 19.5, 0, 0, 4, '#ff9fc0', name='clasp')
    if aw:
        for s in (-1, 1):
            q = front_plate(w, -10, 50, -50, 50, w=-6)
            feather_wing(q, 12, s * 18, s * 1.25, 6, 30, 3.0, Mt('metal', '#fffaf0').p(d=0.75), 2, spread=0.6)
        halo(w, 26, 12, 10.5, Mt('energy', '#ffe38a'), spikes_n=10, name='aw_halo', d=0.5)
        orbit(w, 8, 22, 5, lambda g, k: g.box(0, 0, 0, 6, 1, 4, Mt('cloth', '#fffaf0').b(), rot=(k * 30, 20, 10), name='fpage'), name='pages_orbit')

# =========================================================================================== 16 savior
@weapon('savior', '救世の聖盾', 'shield', '救世結界・万人守護聖域', hold='shield', scale=0.9)
def d_savior(w, aw):
    white = Mt('metal', '#f4f6fb')
    gold = Mt('metal', '#dac36c')
    light = Mt('energy', '#fff3b0')
    p = front_plate(w, -26, 26, -20, 20)
    outer = [(25, 0.1), (25, 14), (20, 18), (4, 18), (-10, 14), (-20, 7), (-25, 0.1)]
    inner = [(22.5, 0.1), (22.5, 12.5), (18.5, 15.8), (4, 15.8), (-9, 12.2), (-18, 6), (-22.5, 0.1)]
    p.sym(outer, gold.p(d=2.25, d0=1.5, bev=1.5), 1)
    p.sym(inner, white.p(d=2.0), 2)
    p.poly([(-17, -2.6), (20, -2.6), (20, 2.6), (-17, 2.6)], gold.p(up=0.75), 3)          # raised cross
    p.poly([(7, -12), (12, -12), (12, 12), (7, 12)], gold.p(up=0.75), 3)
    p.ring(9.5, 0, 9.5, 7.6, gold.p(up=1.0), 4)                                             # halo
    for k in range(12):
        a = 2 * math.pi * k / 12
        p.dot(9.5 + math.cos(a) * 11.5, math.sin(a) * 11.5, light.p(up=0.5), 5)
    p.ell(9.5, 0, 3.4, 3.4, light.p(up=1.25), 6)
    for s in (-1, 1):
        feather_wing(p, 0, s * 9, s * 1.9, 4, 9, 1.6, Mt('metal', '#ffffff').p(up=0.5), 5, spread=0.4)
        for u in (18, -6):
            p.dot(u, s * 15.5, gold.p(up=0.5), 6, r=0.8)
    gem(w, 9.5, 0, 4.2, 4, '#fff3b0', name='heart')
    w.box(0, 0, -3.4, 18, 4, 3, hilt('#7a5a3a', '#4a3420'), name='handle')
    for u in (-9, 9):
        w.box(u, 0, -3.0, 3, 6, 2, gold.b(), name='handle_mount')
    if aw:
        halo(w.group(9.5, 0, -6, rot=(0, 90, 0), name='aw'), 0, 28, 26, light, spikes_n=16, name='aw_halo', d=0.5)
        for k, (u, v) in enumerate(((30, 18), (30, -18), (-6, 26), (-6, -26))):
            hx = front_plate(w, u - 6, u + 6, v - 6, v + 6, w=2)
            pts = [(u + math.cos(math.pi / 3 * j) * 5, v + math.sin(math.pi / 3 * j) * 5) for j in range(6)]
            hx.poly(pts, Mt('energy', '#fff8d0').p(d=0.25), 2)

# =========================================================================================== 17 gokuka
@weapon('gokuka', '外業呪禍の鉤爪', 'claws', '外法呪界・万禍の竜爪', hold='fist', scale=0.9)
def d_gokuka(w, aw):
    scale = Mt('scale', '#3a2c4a')
    fur = Mt('fur', '#d8c8b8')
    claw = Mt('metal', '#efe6d4' if not aw else '#2a1a30')
    curse = M('oilslick', '#6a3a8a')
    cone(w, -20, 16, 7.4, 5.6, scale, steps=3, name='bracer')
    ring3d(w, -2, 6.2, 10, (4, 3, 4), fur, name='ruff')
    ring3d(w, -21, 7.6, 12, (4, 3, 3), fur, phase=15, name='ruff2')
    w.box(-12, 0, 6.6, 15, 9, 1, curse, name='curse_plate')
    for u, v in ((-16, 4), (-7, -3), (-12, -5)):
        w.box(u, v, 7.4, 3, 2, 1, curse, name='drip')
    w.box(5, 0, 0, 11, 15, 8, scale.b(), name='hand')
    w.box(5, 0, 0, 9, 16, 9, curse, name='hand_curse')
    gem(w, 5, 0, 5.0, 4, '#c87fff', name='curse_eye')
    # four long hooked claws fanning out and curling down towards the palm (-w)
    for k, v in enumerate((-6, -2, 2, 6)):
        g = w.group(10, v, 0, rot=(0, 0, -v * 2.2), name=f'claw{k}')
        g.box(1.5, 0, 0, 4, 3, 5, scale.b(), name='knuckle')
        cp = side_plate(g, -2, 32, -20, 6)
        L = 26 + (4 if k in (1, 2) else 0)
        cp.poly([(0, -2.6), (L * 0.5, -4.0), (L * 0.82, -9), (L, -17), (L * 0.86, -10), (L * 0.52, 1.2), (0, 2.6)],
                claw.p(d=1.0, d0=0.5, bev=1.5), 2)
        cp.stroke([(2, -0.4), (L * 0.52, -1.8), (L * 0.82, -7)], 0.8, Mt('energy', '#c87fff').p(inset=0.25), 3)
    th = w.group(4, -8, -1, rot=(0, 0, -45), name='thumb')
    th.box(3, 0, 0, 6, 3, 4, scale.b(), name='t1')
    cp = side_plate(th, 4, 18, -12, 4)
    cp.poly([(5, -1.5), (12, -3), (17, -9), (13, -3.5), (5, 1.5)], claw.p(d=0.75), 2)
    spikes(w, -12, 5, 6.6, 6, 2, Mt('metal', '#d8c8b8'), tilt=65, name='dorsal')
    if aw:
        for k, v in enumerate((-9, 9)):
            g = w.group(-2, v, 3, rot=(0, 0, -v * 3), name=f'xclaw{k}')
            cp = side_plate(g, -2, 30, -18, 6)
            cp.poly([(0, -2), (12, -3), (20, -8), (24, -15), (20, -8), (12, 1), (0, 2)], claw.p(d=0.75), 2)
        orbit(w, -12, 13, 5, lambda g, k: gem(g, 0, 0, 0, 3, '#d88fff', name='ceye'), name='curse_eyes')
        halo(w, 5, 16, 14.5, Mt('energy', '#c87fff'), spikes_n=7, name='aw_halo', d=0.5)

# =========================================================================================== 18 merlinus
@weapon('merlinus', '魔導深淵の杖', 'staff', '魔導深淵・真理改竄式')
def d_merlinus(w, aw):
    wood = Mt('wood', '#5a3a2a')
    wood2 = Mt('wood', '#7a5236')
    purple = Mt('energy', '#b07fff')
    silver = Mt('metal', '#c8c8e0')
    grip(w, -32, 54, 2.4, wood)
    coil(w, -28, 50, 2.5, 1.5, wood2, thick=2, name='twist')
    for u in (-22, 4, 30):
        collar(w, u, 2, 3.1, silver)
    cone(w, -36, 4, 2.8, 1.8, silver, steps=2, name='butt')
    # gnarled wooden claw holding the abyss crystal
    for k in range(4):
        g = w.group(54, 0, 0, rot=(90 * k + 45, 0, 0), name=f'branch{k}')
        s1 = g.group(0, 2, 0, rot=(0, 0, -40), name=f'b1{k}')
        s1.box(5, 0, 0, 10, 3, 3, wood2.b(), name='b1')
        s2 = s1.group(10, 0, 0, rot=(0, 0, 35), name=f'b2{k}')
        s2.box(6, 0, 0, 12, 3, 3, wood.b(), name='b2')
        s3 = s2.group(12, 0, 0, rot=(0, 0, 50), name=f'b3{k}')
        s3.box(3.5, 0, 0, 7, 2, 2, wood2.b(), name='b3')
        s3.box(7.5, 0, 0, 2, 2, 2, silver.b(), name='b3tip')
    w.box(72, 0, 0, 18, 9, 9, M('gem', '#7a3fd0', glow=True), rot=(45, 0, 0), name='abyss')
    w.box(72, 0, 0, 22, 5, 5, M('gem', '#b07fff', glow=True), name='abyss2')
    gem(w, 72, 0, 0, 4, '#ffffff', name='abyss_core')
    for k, (tilt, r) in enumerate(((28, 15), (-32, 13))):
        rr = w.group(72, 0, 0, rot=(70 * k, 0, 0), name=f'rr{k}')
        halo(rr, 0, r, r - 1.3, purple, spikes_n=8, name='rune_ring', d=0.25, tilt=tilt)
    q = front_plate(w, 56, 90, -18, 18, w=-6)
    sigil(q, 72, 0, 15, silver.p(d=0.25), purple.p(d=0.5), 2, n=7)
    hg = w.group(50, 5, 0, rot=(0, 0, 160), name='hourglass')
    chain(hg, [(k * 1.5, 0, 0) for k in range(3)], silver, size=1)
    hg.box(7, 0, 0, 1, 5, 5, silver.b(), name='hg_top')
    hg.box(10, 0, 0, 5, 3, 3, M('gem', '#ffe0a0', glow=True), name='hg_glass')
    hg.box(13, 0, 0, 1, 5, 5, silver.b(), name='hg_bot')
    if aw:
        for k, r in enumerate((20, 25, 30)):
            halo(w, 72, r, r - 1.2, purple, spikes_n=6 + 2 * k, name=f'aw_circle{k}', d=0.25, tilt=15 * (k - 1))
        orbit(w, 72, 22, 6, lambda g, k: crystal(g, 0, 0, 0, 5, 2, '#d0a0ff', rot=(0, 0, 90), name='rune'), name='runes')

# =========================================================================================== 19 enkou
@weapon('enkou', '深海災牙の三叉戟', 'trident', '災極深淵・海獣顎門')
def d_enkou(w, aw):
    obs = Mt('metal', '#253348')
    obs2 = Mt('metal', '#3a4e6a')
    pale = Mt('energy', '#8fe0ff')
    tooth = Mt('metal', '#eef4f8')
    grip(w, -34, 64, 2.6, obs, bands=(-28, -2, 24, 50), band_mt=obs2)
    for u in range(-26, 62, 11):
        gem(w, u, 2.8, 0, 1, '#8fe0ff', name='lumen', facet=False)
    sp = side_plate(w, 30, 70, -12, 12)
    sp.sym([(32, 1.0), (50, 9), (62, 7), (68, 1.0)], obs2.p(d=0.75), 2)
    sp.sym([(40, 1.0), (52, 5.5), (60, 1.0)], pale.p(d=0.75), 3)
    cone(w, -40, 6, 3.2, 2.0, obs, steps=2, name='butt')
    crystal(w, -45, 0, 0, 5, 2, '#8fe0ff', rot=(180, 0, 0), name='butt_lure')
    # shark-jaw socket with a ring of white teeth
    octo(w, 66, 6, 5.6, obs2, 'jaw')
    ring3d(w, 69.5, 5.2, 10, (3, 2, 2), tooth, name='teeth')
    # three serrated tooth-prongs: white enamel rim, obsidian core, glowing nerve
    p = front_plate(w, 64, 122, -24, 24)
    for v, L, wd in ((-13, 32, 8), (0, 48, 10), (13, 32, 8)):
        half = [(70, wd / 2), (70 + L * 0.5, wd / 2 + 1.2), (70 + L * 0.85, wd / 3), (70 + L, 0.1)]
        right = [(u, v + vv) for u, vv in half]
        left = [(u, v - vv) for u, vv in reversed(half)]
        p.poly(serrate(right, 1.4, 3.0, side=1) + serrate(left, 1.4, 3.0, side=1), tooth.p(d=1.0, d0=0.5, bev=1.5), 2)
        inner = [(u, max(0.1, vv - 1.6)) for u, vv in half]
        p.poly([(u, v + vv) for u, vv in inner] + [(u, v - vv) for u, vv in reversed(inner)], obs.p(d=1.75, d0=1.0, bev=1.5), 3)
        p.stroke([(73, v), (70 + L - 6, v)], 1.0, pale.p(inset=0.5), 4)
    p.poly([(66, -17), (71, -17), (71, 17), (66, 17)], obs2.p(d=2.25), 1)
    for s in (-1, 1):
        f = w.group(68, s * 16, 0, rot=(0, 0, s * -70), name=f'side_fin{s}')
        f.box(4, 0, 0, 8, 2, 5, tooth.b(), name='orca_patch')
    if aw:
        lure = w.group(118, 0, 0, rot=(0, 30, 0), name='lure')
        lure.box(6, 0, 0, 12, 1, 1, obs.b(), name='stalk')
        gem(lure, 13, 0, 0, 4, '#bff4ff', name='lure_light')
        halo(w, 90, 24, 22.5, pale, spikes_n=10, name='aw_halo', d=0.5)
        for s in (-1, 1):
            fin(w, 50, s * 4, 0, 14, 7, tooth, rot=(0, 0, s * 120), name=f'aw_fin{s}')

# =========================================================================================== 20 kurma
@weapon('kurma', '嶺脈地龍の大槌', 'maul', '嶺脈震撼・大陸隆起', scale=0.85)
def d_kurma(w, aw):
    rock = Mt('dark', '#6a645c')
    rock2 = Mt('dark', '#4e4a44')
    moss = M('leaf', '#5f8f3a')
    ore = Mt('energy', '#ffc84a' if not aw else '#ff7a2a')
    # stone pillar shaft bound by roots and gold chains
    grip(w, -26, 38, 3.0, M('rock', '#6a645c'))
    coil(w, -22, 34, 3.4, 1.5, Mt('wood', '#6a4a2a'), thick=2, name='root')
    for u in (-20, 8, 30):
        collar(w, u, 3, 3.8, Mt('metal', '#c89a40'))
    w.box(-30, 0, 0, 8, 9, 9, M('rock', '#4e4a44'), name='pommel_rock')
    # head: a mountain block with peaks, ore veins, crystals
    w.box(52, 0, 0, 22, 40, 20, M('rock', '#6a645c', top='#5f8f3a'), name='head')
    w.box(52, 0, 0, 24, 34, 16, M('rock', '#4e4a44'), name='head2')
    for s in (-1, 1):
        w.box(52, s * 21, 0, 16, 4, 16, M('rock', '#7a7268'), name='face')
    for wz in (-1, 1):
        p = front_plate(w, 38, 86, -24, 24, w=wz * 10.4)
        p.poly([(41, -20), (62, -20), (70, -14), (78, -8), (72, -2), (82, 5), (74, 10), (70, 18), (62, 20), (41, 20)],
               rock.p(d=0.75), 2)
        p.poly([(66, -14), (78, -8), (72, -2), (82, 5), (74, 10), (68, 14)], Mt('cloth', '#f2f4f8').p(d=0.5), 3)   # snowcaps
        p.stroke([(44, -14), (50, -6), (47, 4), (54, 12)], 1.2, ore.p(inset=0.25), 4)
        p.stroke([(56, -18), (60, -10), (58, -2)], 1.0, ore.p(inset=0.25), 4)
    w.box(63.5, 0, 0, 1, 36, 18, moss, name='moss')
    for k, (v, wz, r) in enumerate(((-12, 4, (0, 0, -20)), (6, -5, (0, 0, 15)), (14, 3, (0, 30, 25)))):
        crystal(w, 66, v, wz, 8, 3, '#7fe8c0' if k != 1 else '#ffc84a', rot=r, name=f'crys{k}')
    if aw:
        orbit(w, 52, 30, 8, lambda g, k: g.box(0, 0, 0, 5, 4, 5, M('rock', '#7a7268'), rot=(k * 25, k * 40, 10), name='rk'), name='rocks')
        halo(w, 52, 34, 32, ore, spikes_n=0, name='aw_ring', d=0.5)

# =========================================================================================== 21 teia
@weapon('teia', '光越天龍の光弓', 'bow', '光越天翔・虹光天穿', scale=0.85)
def d_teia(w, aw):
    shell = Mt('metal', '#dfe6f0')
    dark = Mt('metal', '#3a4252')
    rain = Mt('energy', '#9ff0ff')
    # limbs along +-v, sweeping back (-u); string at u = -10; arrow along +u
    p = front_plate(w, -16, 26, -44, 44)
    for s in (-1, 1):
        limb = [(2, s * 4), (6, s * 14), (6, s * 26), (2, s * 36), (-6, s * 42), (-4, s * 34), (-1, s * 24), (-1, s * 12), (-3, s * 4)]
        p.poly(limb, shell.p(d=1.5, d0=0.75, bev=2), 2)
        p.stroke([(4, s * 10), (4.5, s * 24), (0.5, s * 35), (-5, s * 41)], 1.2, rain.p(inset=0.25), 3)
        feather_wing(p, 6, s * 18, s * 0.25, 4, 12, 1.8, shell.p(d=0.75), 1, spread=0.4)
    p.stroke([(-6, -42), (-10, 0), (-6, 42)], 0.8, Mt('energy', '#ffffff').p(d=0.5), 4)        # string of light
    p.sym([(-10, 0.8), (18, 0.8), (19, 2.6), (25, 0.1)], rain.p(d=0.75), 5)                    # nocked photon arrow
    w.box(0, 0, 0, 10, 6, 6, dark.b(), name='grip_block')
    w.box(0, 0, 0, 12, 4, 7, hilt('#3a4252', '#20242e'), name='grip_wrap')
    gem(w, 4, 0, 3.5, 3, '#ffffff', name='sight')
    for s in (-1, 1):
        f = w.group(2, s * 24, 0, rot=(0, 0, 0), name=f'vane{s}')
        fp = side_plate(f, -6, 10, -12, 12)
        fp.sym([(-4, 2), (2, 10), (6, 2), (8, 0.1)], shell.p(d=0.75), 2)
    if aw:
        halo(w.group(0, 0, -4, rot=(0, 90, 0), name='awh'), 0, 30, 28.5, Mt('energy', '#ffe9ff'), spikes_n=12, name='aw_halo', d=0.5)
        for k, v in enumerate((-8, 8)):
            fp = front_plate(w, -10, 30, v - 2, v + 2, w=3 + k)
            fp.sym([(-8, 0.5), (22, 0.5), (24, 1.6), (28, 0.1)], Mt('energy', ['#ff9fd0', '#9fffc0'][k]).p(d=0.5), 3)

# =========================================================================================== 22 bahamut
@weapon('bahamut', '大海皇鯨の法螺貝', 'conch staff', '大海皇鯨・潮歌創世')
def d_bahamut(w, aw):
    pearl = Mt('metal', '#f2f0ea')
    shell2 = Mt('metal', '#e8d4bc')
    blue = Mt('metal', '#2a5a9a')
    gold = Mt('metal', '#e2b84a')
    tide = Mt('energy', '#7fe8ff')
    grip(w, -30, 44, 2.6, pearl, bands=(-24, -2, 20, 40), band_mt=blue)
    coil(w, -20, 40, 3.0, 2.0, Mt('metal', '#ff9f8a'), thick=1, name='coral')
    cone(w, -36, 6, 3.2, 2.0, gold, steps=2, name='butt')
    gem(w, -39, 0, 0, 3, '#ffffff', name='pearl_end')
    cone(w, 44, 6, 3.0, 5.0, gold, steps=2, name='cup')
    # a great conch: whorls shrinking and drifting sideways towards the apex, ringed with knobs
    n = 9
    for i in range(n):
        t = i / (n - 1)
        r = 12 - 9.5 * t
        g = w.group(52 + 36 * t, 3.0 * math.sin(t * 3.0), 0, rot=(55 * i, 0, 0), name=f'whorl{i}')
        octo(g, 0, 5, r, pearl if i % 2 == 0 else shell2, f'whorl{i}')
        if r > 3:
            for j in range(4):
                kg = g.group(0, 0, 0, rot=(90 * j + 20 * i, 0, 0), name=f'knob{i}{j}')
                kg.box(0, r, 0, 3, 3, 3, Mt('metal', '#d8c0a0').b(), rot=(0, 0, 45), name='knob')
    cone(w, 88, 6, 2.6, 1.0, gold, steps=2, name='mouthpiece')
    p = front_plate(w, 46, 80, -18, 18, w=11.0)
    p.ell(62, -2, 12, 8.5, Mt('metal', '#ffb0a0').p(d=0.75), 2)
    p.ell(62, -2, 9, 5.8, tide.p(d=1.0), 3)
    p.ell(62, -2, 5, 3.0, Mt('energy', '#ffffff').p(d=1.25), 4)
    for s in (-1, 1):
        f = side_plate(w.group(56, s * 12, 0, name=f'whalefin{s}'), -4, 26, -14, 14)
        f.poly([(0, -2), (18, -11), (24, -8), (12, 2), (0, 3)], blue.p(d=0.75), 2)
    for k in range(4):
        gem(w, 48, 6 * math.cos(k * 1.57), 6 * math.sin(k * 1.57), 2, '#ffffff', name='pearl')
    if aw:
        for k, r in enumerate((19, 24)):
            halo(w, 66, r, r - 1.4, tide, name=f'aw_wave{k}', d=0.5, tilt=20 * (1 - 2 * k))
        orbit(w, 66, 28, 6, lambda g, k: gem(g, 0, 0, 0, 3, '#ffffff', name='op'), name='pearls')

# =========================================================================================== 23 nun
@weapon('nun', '天変万化の道化杖', 'marotte', '天変万化・千面の王', scale=0.85)
def d_nun(w, aw):
    goo = M('slime', '#1a1620', glow=False)
    black = Mt('metal', '#1a1620')
    gold = Mt('metal', '#d8b050')
    purple = Mt('energy', '#c060ff')
    grip(w, -34, 54, 2.2, goo)
    for k, u in enumerate((-20, 4, 30)):
        w.box(u, 2.4, 0, 2, 2, 2, goo, name='drip')
        w.box(u - 2.5, 2.6, 0, 3, 1, 1, goo, name='drip2')
    cone(w, -40, 6, 3.0, 2.0, gold, steps=2, name='butt')
    collar(w, 56, 4, 3.6, gold)
    # jester head: mask (half white / half black), cap with three bells
    p = front_plate(w, 56, 92, -16, 16, w=0)
    p.ell(70, 0, 11, 9, black.p(d=2.25, d0=1.5, bev=2), 2)
    p.poly([(60, 0), (81, 0), (80, 8.5), (70, 9.5), (61, 7)], Mt('metal', '#f2eef6').p(d=2.5, d0=1.75, bev=2), 3)
    for s in (-1, 1):
        p.poly([(72, s * 4.5), (74.5, s * 2.8), (72, s * 1.4), (69.5, s * 2.8)], purple.p(inset=0.5), 4)
    p.stroke([(65, -4), (63, 0), (65, 4)], 0.9, Mt('metal', '#7a1028').p(inset=0.25), 4)
    for k, (a, col) in enumerate(((-55, '#7a1028'), (0, '#3a1050'), (55, '#d8b050'))):
        g = w.group(80, 0, 0, rot=(0, 0, a), name=f'cap{k}')
        g.box(5, 0, 0, 10, 5, 5, Mt('cloth', col).b(), name='cap_a')
        g2 = g.group(10, 0, 0, rot=(0, 0, a * 0.8 + (30 if a == 0 else 0)), name=f'cap2{k}')
        g2.box(3.5, 0, 0, 7, 3, 3, Mt('cloth', col).b(), name='cap_b')
        gem(g2, 8, 0, 0, 3, '#ffd860', name='bell')
    if aw:
        def mask(g, k):
            q = front_plate(g, -6, 6, -6, 6)
            q.ell(0, 0, 5, 4.2, Mt('metal', ['#f2eef6', '#1a1620', '#d8b050', '#7a1028'][k % 4]).p(d=0.75), 2)
            q.poly([(-1, -2.5), (1, -1.5), (-1, -0.5)], purple.p(d=1.0), 3)
            q.poly([(-1, 2.5), (1, 1.5), (-1, 0.5)], purple.p(d=1.0), 3)
        orbit(w, 70, 20, 6, mask, name='masks')

# =========================================================================================== 24 arcana
@weapon('arcana', '運命流転の糸巻杖', 'spindle staff', '運命流転・幸運連鎖の大車輪')
def d_arcana(w, aw):
    white = Mt('metal', '#fbf8f0')
    gold = Mt('metal', '#e8c060')
    thread = Mt('energy', '#ffe08a')
    grip(w, -38, 66, 2.2, white, bands=(-30, -4, 22, 48), band_mt=gold)
    coil(w, -26, 60, 2.6, 4, Mt('energy', '#ffe9a0', glow=0.5), thick=1, name='thread')
    cone(w, -44, 6, 3.0, 2.0, gold, steps=2, name='butt')
    # wheel of fate standing in the drawing plane, spokes, thread wound on the hub
    q = front_plate(w, 64, 112, -24, 24)
    q.ring(88, 0, 20, 17.6, gold.p(d=1.5), 2)
    for k in range(8):
        a = 2 * math.pi * k / 8
        q.stroke([(88 + math.cos(a) * 4, math.sin(a) * 4), (88 + math.cos(a) * 17.6, math.sin(a) * 17.6)], 1.4, white.p(d=1.0), 1)
        q.dot(88 + math.cos(a) * 18.8, math.sin(a) * 18.8, thread.p(up=0.5), 4, r=0.8)
    q.ell(88, 0, 4.5, 4.5, gold.p(d=2.25), 3)
    star(q, 88, 0, 3.6, 1.6, 4, thread.p(up=0.25), 4)
    octo(w, 88, 3, 2.0, gold, 'axle')
    for s in (-1, 1):
        feather_wing(front_plate(w, 56, 96, -40, 40, w=-2), 72, s * 6, s * 1.45, 5, 22, 2.4, white.p(d=0.75), 2, spread=0.55)
    # hanging spindle with thread
    sg = w.group(66, 6, 0, rot=(0, 0, 165), name='spindle')
    sg.box(5, 0, 0, 10, 1, 1, thread.b(), name='thr')
    octo(sg, 12, 6, 1.8, Mt('wood', '#c89a60'), 'sp_body')
    sg.box(12, 0, 0, 4, 4, 4, thread.b(), name='sp_yarn')
    if aw:
        def card(g, k):
            c = front_plate(g, -7, 7, -5, 5)
            c.poly([(-6, -4), (6, -4), (6, 4), (-6, 4)], white.p(d=0.25), 2)
            c.ring(0, 0, 3, 2, gold.p(d=0.5), 3)
            star(c, 0, 0, 2, 0.8, 4, thread.p(d=0.5), 4)
        orbit(w, 88, 28, 7, card, name='tarot')
        halo(w, 88, 34, 32.5, thread, spikes_n=14, name='aw_wheel', d=0.5)

# =========================================================================================== 25 eomaia
@weapon('eomaia', '始祖神獣の角牙薙刀', 'antler naginata', '始祖回帰・万獣の母なる牙')
def d_eomaia(w, aw):
    bone = Mt('bone', '#e8dcc4')
    ivory = Mt('metal', '#f4ecd8')
    dark = Mt('metal', '#6a5038')
    fur = Mt('fur', '#8a6a4a')
    amber = Mt('energy', '#ffb04a')
    grip(w, -32, 54, 2.8, bone, bands=(-26, 24, 48), band_mt=dark)
    for u in (-8, 8):
        octo(w, u, 9, 3.6, fur, f'fur{u}')
    for k in range(4):
        f = w.group(-6 + k * 4, 3.4, 0, rot=(0, 0, 150 + k * 8), name=f'feather{k}')
        fp = side_plate(f, 0, 16, -4, 4)
        fp.sym([(0, 0.5), (7, 3.0), (14, 0.1)], Mt('cloth', ['#c84a2a', '#2a6ac8', '#e8c040', '#3ab060'][k]).p(d=0.5), 2)
    cone(w, -38, 6, 3.2, 2.0, ivory, steps=2, name='butt')
    crystal(w, -42, 0, 0, 5, 3, '#f4ecd8', rot=(180, 0, 0), name='butt_fang')
    # beast skull socket: brow, snout, amber eyes, fangs
    w.box(60, 0, 0, 12, 13, 11, ivory.b(), name='skull')
    w.box(56, 0, 3, 6, 9, 7, bone.b(), name='snout')
    for s in (-1, 1):
        w.box(62, s * 3, 5.6, 3, 3, 1, amber.b(), name='eye')
        w.box(53, s * 3, 4, 4, 2, 2, ivory.b(), rot=(0, 0, s * 10), name='fang')
    # great curved tusk blade
    p = front_plate(w, 60, 134, -22, 14)
    pts, edge, back = curved(64, 128, 16, 4, -12, tip=5, power=1.6)
    p.poly(pts, ivory.p(d=2.25, d0=0.75, bev=3), 2)
    p.poly(band(centre(66, 120, -12, power=1.6), 1.0, 5.0), Mt('metal', '#fff8e8').p(d=2.75, d0=2.0, bev=1), 3)
    p.poly([(u, v) for u, v in edge[-5:]] + [(128 + 5, -12 + 1.2)], Mt('metal', '#8a6a4a').p(d=1.0), 4)
    for u in (76, 90, 104):
        p.stroke([(u, -8), (u + 4, -5)], 0.9, Mt('metal', '#c8b088').p(inset=0.5), 4)
    for s in (-1, 1):
        a = w.group(64, s * 6, 0, rot=(0, 0, s * -55), name=f'antler{s}')
        a.box(6, 0, 0, 12, 3, 3, bone.b(), name='a1')
        for j, (pos, ang) in enumerate(((5, 45), (10, -35), (12, 60))):
            t = a.group(pos, 0, 0, rot=(0, j * 25 - 20, s * ang), name=f'tine{s}{j}')
            t.box(3.5, 0, 0, 7, 2, 2, bone.b(), name='tine')
        a2 = a.group(12, 0, 0, rot=(0, 0, s * 30), name=f'antler2{s}')
        a2.box(5, 0, 0, 10, 2, 2, bone.b(), name='a2')
    if aw:
        mane = front_plate(w, 44, 84, -30, 30, w=-4)
        for k in range(11):
            a = math.pi * (k - 5) / 11
            leaf(mane, 60, 0, a, 22, 3.4, Mt('fur', '#e8b050').p(d=0.75), 2)
        orbit(w, 60, 20, 5, lambda g, k: crystal(g, 0, 0, 0, 7, 2, '#ffd080', rot=(0, 0, 90), name='fang'), name='fangs')

# =========================================================================================== 26 demiurgos
@weapon('demiurgos', '空想現実の黒龍剣', 'greatsword', '空想顕現・理想郷の黒龍王剣')
def d_demiurgos(w, aw):
    black = Mt('scale', '#1e1c26')
    edge = Mt('metal', '#4a4658')
    gems = ['#ff5f7f', '#ffd25f', '#5fff9f', '#5fd8ff', '#b07fff']
    p = front_plate(w, 18, 118, -14, 14)
    half = [(19, 11), (32, 12.5), (60, 11.5), (90, 9), (104, 6), (112, 3), (116, 0.1)]
    p.sym(serrate(half, 1.6, 6.0, side=1), edge.p(d=1.25, d0=0.5, bev=2), 2)
    inner = [(21, 8.5), (32, 9.8), (60, 9.0), (90, 6.8), (102, 3.6), (108, 0.1)]
    p.sym(inner, black.p(d=2.5, d0=1.5, bev=2), 3)
    for k, u in enumerate((34, 48, 62, 76, 90)):
        p.poly([(u - 3.5, 0), (u, -2.8), (u + 3.5, 0), (u, 2.8)], Mt('gem', gems[k]).p(up=0.5), 4)
    p.stroke([(24, 0), (31, 0)], 1.2, Mt('energy', '#ffffff').p(inset=0.25), 4)
    # dragon-wing guard + horned crossbar + dragon head pommel
    w.box(16, 0, 0, 5, 28, 8, edge.b(), name='guard')
    q = front_plate(w, 6, 46, -36, 36, w=-1)
    for s in (-1, 1):
        bat_wing(q, 17, s * 12, (math.pi / 2) * s * 0.8, 22, black.p(d=1.0), 2, fingers=4)
    for s in (-1, 1):
        h = w.group(18, s * 13, 0, rot=(0, 0, s * -40), name=f'ghorn{s}')
        h.box(3, 0, 0, 6, 3, 3, edge.b(), name='gh')
        gem(h, 7, 0, 0, 3, gems[2 + s], name='ghgem')
    gem(w, 17, 0, 0, 5, '#b07fff', name='heart')
    grip(w, -15, 13, 3.0, hilt('#2a2632', '#141218'), bands=(-14, 0, 12), band_mt=edge)
    w.box(-20, 0, 0, 8, 7, 7, black.b(), name='dragon_head')
    w.box(-25, 0, 1, 4, 4, 5, edge.b(), name='snout')
    for s in (-1, 1):
        w.box(-20, s * 2.4, 3.8, 2, 2, 1, Mt('energy', '#ff5f7f').b(), name='deye')
        h = w.group(-18, s * 3, -2, rot=(0, -30, s * 30), name=f'dhorn{s}')
        h.box(3, 0, 0, 6, 2, 2, edge.b(), name='dh')
    if aw:
        def ghost(g, k):
            fp = front_plate(g, -2, 30, -4, 4)
            fp.sym([(0, 2.5), (22, 2.2), (28, 0.1)], Mt('energy', gems[k % 5], glow=0.6).p(d=0.5), 2)
        orbit(w, 40, 22, 5, ghost, name='ghosts')
        halo(w, 18, 18, 16.5, Mt('energy', '#b07fff'), spikes_n=10, name='aw_halo', d=0.5)

# =========================================================================================== 27 hakyoku
@weapon('hakyoku', '無窮覇帝の捕食砲', 'arm cannon', '無窮進化・覇帝の暴食顎', scale=0.9)
def d_hakyoku(w, aw):
    hide = Mt('scale', '#2a2230')
    plate = Mt('metal', '#4a4050')
    bone = Mt('metal', '#e8dcd0')
    glow = Mt('energy', '#ff4a8a' if not aw else '#ffd04a')
    circ = M('metal', '#3a3242', pattern='circuit', accent='#ff4a8a' if not aw else '#ffd04a', pattern_glow=True, glow_amount=0.9)
    octo(w, 0, 20, 6.2, hide, 'sleeve')
    w.box(0, 0, 0, 18, 10, 13, circ, name='sleeve_plate')
    cone(w, 10, 26, 7.0, 8.4, plate, steps=3, name='body')
    w.box(22, 0, 0, 22, 18, 10, circ, name='body_circ')
    for u in (14, 28):
        octo(w, u, 2, 9.2, Mt('metal', '#6a5a70'), f'rib{u}')
    spikes(w, 20, 5, 8.0, 8, 2, Mt('metal', '#d8c8d8'), tilt=25, name='dorsal')
    # predator maw opening forward: upper and lower jaws hinged apart, rows of fangs
    for s in (-1, 1):
        j = w.group(34, 0, s * 4, rot=(0, s * 24, 0), name=f'jaw{s}')
        j.box(9, 0, 0, 18, 16, 4, plate.b(), name='jaw_plate')
        j.box(9, 0, s * 2.2, 16, 12, 1, circ, name='jaw_circ')
        for k in range(6):
            j.box(3 + k * 3, -5 + 2 * k, -s * 2.6, 2, 2, 3, bone.b(), rot=(0, 0, 45), name='fang')
        j.box(18.5, 0, -s * 1.5, 2, 14, 2, bone.b(), name='lip_teeth')
    octo(w, 38, 4, 5.4, glow, 'throat')
    gem(w, 42, 0, 0, 4, '#ffffff', name='throat_core')
    for s in (-1, 1):
        h = w.group(30, s * 8, 0, rot=(0, 0, s * -40), name=f'crown{s}')
        h.box(5, 0, 0, 10, 3, 3, Mt('metal', '#e8d0f0').b(), name='ch')
        h.box(11, 0, 0, 3, 2, 2, glow.b(), name='ch_tip')
    if aw:
        j2 = w.group(22, 0, 10, rot=(0, -20, 90), name='maw2')
        j2.box(7, 0, 0, 14, 12, 4, plate.b(), name='m2')
        gem(j2, 14, 0, 0, 3, '#ffd04a', name='m2core')
        spikes(w, 4, 7, 6.8, 7, 2, Mt('metal', '#d8c8d8'), tilt=40, name='aw_spikes')
        halo(w, 46, 13, 11.5, glow, spikes_n=10, name='aw_halo', d=0.5)

# =========================================================================================== 28 shinra
@weapon('shinra', '天敵の日傘', 'parasol', '万物天敵・紅月の咲傘', scale=0.85)
def d_shinra(w, aw):
    black = Mt('cloth', '#1c1418')
    red = Mt('cloth', '#a8203a')
    lace = Mt('cloth', '#f2eaee')
    silver = Mt('metal', '#c8c0c8')
    # crook handle (the grip) and slender shaft
    grip(w, -10, 64, 1.6, Mt('metal', '#2a2026'))
    h = w.group(-10, 0, 0, rot=(0, 0, 0), name='crook')
    h.box(-4, 0, 0, 8, 3, 3, hilt('#3a2a30', '#1c1418'), name='c1')
    h2 = h.group(-8, 0, 0, rot=(0, 0, 70), name='crook2')
    h2.box(-3, 0, 0, 6, 3, 3, hilt('#3a2a30', '#1c1418'), name='c2')
    h3 = h2.group(-6, 0, 0, rot=(0, 0, 70), name='crook3')
    h3.box(-2.5, 0, 0, 5, 3, 3, silver.b(), name='c3')
    # canopy: eight panels in a half-open cone, lace hems, roses
    ang = 22 if not aw else 55
    for k in range(8):
        g = w.group(60, 0, 0, rot=(22.5 + 45 * k, 0, 0), name=f'panel{k}')
        pg = g.group(0, 0.5, 0, rot=(0, 0, -ang), name=f'panel_t{k}')
        pl = pg.plate(-2, 35, -7, 7, U=(-1, 0, 0), V=(0, 0, 1))
        pl.poly([(0, -0.5), (32, -6), (33, 0), (32, 6), (0, 0.5)], (black if k % 2 == 0 else red).p(d=0.5), 2)
        pl.poly([(28, -5.2), (33, 0), (28, 5.2), (30, 0)], lace.p(d=0.5), 3)
        pg.box(-17, 0, 0, 34, 1, 1, silver.b(), name='rib')
    collar(w, 62, 3, 2.4, silver)
    w.box(64, 0, 0, 3, 3, 3, Mt('metal', '#a8203a').b(), name='top_knob')
    crystal(w, 70, 0, 0, 10, 2, '#e8e0f0', name='hidden_blade')
    for k in range(4):
        g = w.group(34, 0, 0, rot=(90 * k + 20, 0, 0), name=f'rose{k}')
        g.box(0, 6 + ang * 0.15, 0, 3, 3, 3, Mt('cloth', '#d82848').b(), rot=(45, 0, 45), name='rose')
    if aw:
        orbit(w, 30, 30, 8, lambda g, k: crystal(g, 0, 0, 0, 6, 2, '#ff4060', rot=(0, 0, -100), name='thorn'), name='thorns')
        halo(w, 60, 20, 18.5, Mt('energy', '#ff3050'), spikes_n=8, name='aw_moon', d=0.5)

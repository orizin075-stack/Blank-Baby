"""Sculpted versions of the creature bosses (override creatures3d recipes): smooth lofted bodies with painted
3D eyes, relief fins and sails, continuous tails, tapered legs, horns and teeth (beasts.py)."""
import math
import numpy as np
from rig import Rig
from paint import M
import sculpt as SC
import beasts as BZ
import trinkets as TK
from figure import wing

RECIPES = {}
def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn

@recipe
def enkou():
    # 災極海獣 淵煌 — サメの鋭利さ、シャチの俊敏さ、竜の威厳。黒曜石のような鱗、深海魚の灯火のように青白く輝く瞳。
    # 体表に海洋生物の意匠を思わせる文様（鱗であり、魔術回路であり、深海の記憶の紋章）。
    r = Rig('enkou')
    SC.Sculpt(r)
    belly = '#cfdce6'
    hide = M('scale', '#141b28', belly=belly, accent='#7fdcff', pattern='vine', pattern_glow=True, glow_amount=0.55)
    plain = M('scale', '#141b28', belly=belly)
    fin_c, edge = '#1e2a3c', '#5fb8e0'
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.5, speed=0.05)
    body = r.bone('body', root, (0, 14, 0), anim='sway', ax=1, amp=0.05, speed=0.06)
    gills = [BZ.line((sx * 5.9, 12.2, -8.5 + k * 1.2), (sx * 5.7, 15.8, -8.0 + k * 1.2), 0.18, '#7fdcff', glow=True) for sx in (-1, 1) for k in range(3)]
    BZ.loft(body, [(0, 14, -11.5), (0, 13.6, -6), (0, 13.8, 0), (0, 14.2, 6), (0, 14.4, 11.6)], [5.0, 6.2, 6.3, 5.6, 4.4],
            [4.8, 5.6, 5.7, 5.2, 4.3], hide, e=2.3, k=24, spots=gills, name='torso')
    BZ.fin(body, (0, 8.9, -6), (0, 0, 1), (0, -1, 0), [(0, 0), (3.5, 7.5), (6.5, 8.4), (9, 6.6), (11, 0)], fin_c, edge=edge, name='dorsal')
    for sx in (-1, 1):
        fb = r.bone('fin_' + ('r' if sx < 0 else 'l'), body, (sx * 5.6, 17.5, -5), rot=(0.25, sx * 0.45, sx * -0.55), anim='sway', ax=2,
                    amp=0.12, speed=0.08, phase=sx)
        BZ.fin(fb, (sx * 5.4, 17.5, -8), (0, 0, 1), (sx, 0, 0), [(0, 0), (1.5, 6), (4.5, 9.5), (6.5, 8), (7, 0)], fin_c, edge=edge,
               name='pectoral')
    head = r.bone('head', body, (0, 13, -11), anim='head')
    face = [BZ.dot((sx * 4.3, 11.8, -13.2), 1.6, '#e6eef4') for sx in (-1, 1)]
    face += [BZ.eye((sx * 4.15, 12.7, -16.6), 1.0, '#bff4ff') for sx in (-1, 1)]
    face += [BZ.dot((sx * 1.1, 13.0, -26.3), 0.35, '#0a0e16') for sx in (-1, 1)]
    BZ.loft(head, [(0, 13.4, -10.6), (0, 13.4, -15), (0, 13.9, -20), (0, 14.6, -24.4), (0, 15.2, -26.9)], [4.8, 4.7, 3.8, 2.4, 1.0],
            [4.6, 4.4, 3.5, 2.3, 1.0], plain, e=2.3, k=22, spots=face, name='skull')
    BZ.teeth(head, (-3.0, 17.4, -14), (-1.4, 17.2, -25), 6, 0.9)
    BZ.teeth(head, (3.0, 17.4, -14), (1.4, 17.2, -25), 6, 0.9)
    for sx in (-1, 1):
        BZ.horn(head, (sx * 2.6, 9.6, -14), (sx * 0.3, -0.55, 1), 8.5, 0.85, M('horn', '#20283a', tip='#8fe3ff', glow=True),
                curl=(0, 0.6, 1.2))
    jaw = r.bone('jaw', head, (0, 18, -12), anim='jaw')
    BZ.loft(jaw, [(0, 18.7, -12), (0, 18.9, -19), (0, 18.7, -25.4)], [3.8, 3.0, 1.5], [1.25, 1.05, 0.75],
            M('scale', '#141b28', belly=belly), k=18, name='jaw')
    BZ.teeth(jaw, (-2.6, 17.8, -14), (-1.2, 17.9, -24.4), 5, 0.8, down=False)
    BZ.teeth(jaw, (2.6, 17.8, -14), (1.2, 17.9, -24.4), 5, 0.8, down=False)
    end, (x, y, z) = BZ.tail(r, body, (0, 14.2, 11), hide, [(4.3, 4.2, 5), (3.4, 3.4, 5), (2.5, 2.6, 5), (1.6, 1.9, 4)], amp=0.16,
                             speed=0.07, end_cap='round')
    BZ.fin(end, (0, y, z - 1.6), (0, -1, 0), (0, 0, 1), [(1.4, 0), (8.5, 5.0), (7.2, 7.4), (0.6, 3.8), (-5.8, 6.8), (-6.8, 5.0), (-1.4, 0)],
           fin_c, edge=edge, name='caudal')
    return r

@recipe
def bahamut():
    # 大海皇鯨 バハムート — 鯨の滑らかな流線型の体躯に龍の鱗と角、背には潮を巻き上げる巨大なヒレ。
    # 背には珊瑚礁と植物が根付き独自の生態系。おっとりとした海の調停者。
    r = Rig('bahamut')
    SC.Sculpt(r)
    belly = '#e4efe8'
    hide = M('scale', '#2f6f8a', belly=belly, accent='#9fe8d0', pattern='marks')
    plain = M('scale', '#2f6f8a', belly=belly)
    fin_c, edge = '#2a6a7a', None
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.0, speed=0.03)
    body = r.bone('body', root, (0, 13, 0), anim='sway', ax=1, amp=0.03, speed=0.04)
    grooves = [BZ.line((x, 19.6, -14), (x * 0.6, 20.4, 6), 0.16, '#b8ccc4') for x in (-4.5, -3, -1.5, 0, 1.5, 3, 4.5)]
    BZ.loft(body, [(0, 13, -15.5), (0, 12.6, -8), (0, 12.8, 2), (0, 13.2, 10), (0, 13.4, 15.6)], [8.4, 9.4, 9.2, 7.6, 5.6],
            [7.0, 7.6, 7.4, 6.2, 4.8], hide, e=2.2, k=28, spots=grooves, name='torso')
    # reef on the back
    corals = [(-4, -6, '#ff7a8a', 3.2), (3, 2, '#ffb07a', 4.0), (-2, 9, '#c88aff', 3.0), (5, -9, '#7affc8', 2.4), (0, -2, '#ff7ab0', 3.4),
              (-5, 3, '#ffe07a', 2.2)]
    for (x, z, c, h) in corals:
        base = np.array([x, 13 - 7.2 + 0.4 + abs(x) * 0.12, z])
        cm = M('gem', c, glow=False)
        SC.sweep(body, [base, base + (0, -h * 0.6, 0), base + (0.3, -h, 0.2)], lambda t: 0.55 * (1 - 0.5 * t), None, cm, k=8,
                 caps=('round', 'round'), name='coral', info={'hem': False})
        for sgn in (-1, 1):
            q = base + (0, -h * 0.5, 0)
            SC.sweep(body, [q, q + (sgn * 0.9, -h * 0.25, 0.2), q + (sgn * 1.2, -h * 0.55, 0.3)], lambda t: 0.35 * (1 - 0.5 * t), None, cm, k=6,
                     caps=('round', 'round'), name='coral_branch', info={'hem': False})
    for (x, z) in [(-6, 6), (6, -4), (1, 11), (-3, -11)]:
        base = np.array([x, 6.8 + abs(x) * 0.15, z])
        SC.sweep(body, SC.bezier(base, base + (0.6, -3, 0.4), base + (-0.4, -6, 1.0), n=8), lambda t: 0.6 * (1 - 0.6 * t), 0.15,
                 M('leaf', '#3a9a6a'), k=6, up=(1, 0, 0), caps=('round', 'point'), name='kelp', info={'hem': False})
    sail = r.bone('sail', body, (0, 6, -4), rot=(-0.15, 0, 0), anim='sway', ax=2, amp=0.03, speed=0.04)
    BZ.fin(sail, (0, 6.4, -9), (0, 0, 1), (0, -1, 0), [(0, 0), (2, 9), (6, 12.5), (11, 11), (15, 6), (16, 0)], fin_c, edge=edge,
           rays='#9fe8d0', name='sail')
    head = r.bone('head', body, (0, 13, -15), anim='head')
    face = [BZ.eye((sx * 7.2, 14.6, -20.5), 1.0, '#e0fff4', slit=False) for sx in (-1, 1)]
    face += [BZ.dot((sx * 1.6, 6.9, -20.0), 0.45, '#163a48') for sx in (-1, 1)]
    BZ.loft(head, [(0, 13.0, -14.6), (0, 13.0, -19), (0, 13.3, -24), (0, 14.0, -27.4)], [8.2, 7.8, 6.8, 4.2], [7.0, 6.6, 5.6, 3.6],
            plain, e=2.4, k=26, spots=face, name='skull')
    for sx in (-1, 1):
        BZ.horn(head, (sx * 4.8, 7.6, -18), (sx * 0.35, -0.6, 1), 9.5, 1.0, M('horn', '#e8f4ee', tip='#9fe8d0', glow=True), curl=(sx * 0.6, 0.4, 1.4))
    jaw = r.bone('jaw', head, (0, 19, -16), anim='jaw')
    BZ.loft(jaw, [(0, 19.4, -15.5), (0, 19.5, -21), (0, 19.2, -26.4)], [6.6, 5.8, 3.2], [1.4, 1.2, 0.9],
            M('scale', '#2f6f8a', belly=belly), k=22, name='jaw')
    for sx in (-1, 1):
        fb = r.bone('fin_' + ('r' if sx < 0 else 'l'), body, (sx * 8.6, 17, -7), rot=(0.2, sx * 0.35, sx * -0.6), anim='sway', ax=2,
                    amp=0.1, speed=0.05, phase=sx)
        BZ.fin(fb, (sx * 8.4, 17, -10), (0, 0, 1), (sx, 0, 0), [(0, 0), (1, 6), (3.5, 9.5), (6, 8.5), (7, 0)], fin_c, rays='#4a8a9a',
               name='flipper')
    end, (x, y, z) = BZ.tail(r, body, (0, 13.4, 15), hide, [(5.5, 4.6, 6), (4.2, 3.6, 6), (2.9, 2.6, 6), (1.8, 1.7, 5)], amp=0.07,
                             speed=0.04, ax=0, end_cap='round')
    BZ.fin(end, (0, y, z - 1.5), (1, 0, 0), (0, 0, 1), [(-1.5, 0), (-12, 5.5), (-12.5, 8.5), (-5, 6), (0, 3.4), (5, 6), (12.5, 8.5),
                                                     (12, 5.5), (1.5, 0)], fin_c, edge=edge, name='fluke')
    return r


@recipe
def kurma():
    # 嶺脈地龍 クールマ — 巨大な山脈を背負う地龍。稜線は背、谷は鱗の隙間、山頂の岩壁は角や甲殻の一部。
    # 背の山々には独自の生態系、霊脈の魔力、豊穣。老賢者のように穏やか。
    r = Rig('kurma')
    SC.Sculpt(r)
    hide = M('scale', '#6b7558', belly='#b8ae8a')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 12, 0), anim='breath')
    BZ.loft(body, [(0, 15.6, -15), (0, 15.2, -6), (0, 15.2, 6), (0, 15.6, 15)], [10.5, 12.5, 12.5, 10], [3.4, 4.2, 4.2, 3.2], hide,
            k=26, name='plastron')
    # the shell: a rocky, grassy dome ringed with glowing ley-line cracks
    A, Bz, y0, Hd = 15.5, 17.5, 12.4, 10.2
    dome_y = lambda x, z: y0 - Hd * math.sqrt(max(0.0, 1 - (x / A) ** 2 - (z / Bz) ** 2))
    SC.sweep(body, [(0, y0, 0), (0, y0 - 3.2, 0), (0, y0 - 6.5, 0), (0, y0 - 8.8, 0), (0, y0 - Hd + 0.3, 0)],
             [A, A * 0.95, A * 0.76, A * 0.5, A * 0.2], [Bz, Bz * 0.95, Bz * 0.76, Bz * 0.5, Bz * 0.2],
             M('rock', '#7a7466', top='#5e9a3a', cracks=True, accent='#c8f08a'), e=2.3, k=36, caps=(None, 'round'), cap_len=1.2,
             mod=lambda th, t: 1 + 0.035 * np.sin(5 * th + 7 * t) + 0.02 * np.cos(11 * th), name='dome', info={'hem': False})
    rim = [(A * 1.02 * math.sin(a), y0 + 0.3, -Bz * 1.02 * math.cos(a)) for a in np.linspace(0, 2 * math.pi, 49)[:-1]]
    SC.sweep(body, rim, 1.3, 1.0, M('rock', '#5f5a50', cracks=True, accent='#c8f08a'), k=8, closed=True, up=(0, -1, 0), caps=None,
             name='rim', info={'hem': False})
    for (x, z, rb, h) in [(-2, -1, 6.5, 13), (6, 6, 4.8, 9), (-8, 7, 4.2, 7.5), (7, -7, 3.8, 6.5), (-7, -8, 3.0, 5)]:
        yb = dome_y(x, z) + 1.2
        snow = M('rock', '#8a8478', top='#5e9a3a', snow='#f2f6fa', snow_y=yb - h * 0.62)
        SC.lathe(body, (x, z), [(yb, rb), (yb - h * 0.35, rb * 0.72), (yb - h * 0.7, rb * 0.38), (yb - h, 0.15)], snow, k=14,
                 caps=(None, 'round'), cap_len=0.6, mod=lambda th, t: 1 + 0.16 * np.cos(4 * th + 2.0 * t) * (0.4 + t), name='peak',
                 info={'hem': False})
    for (x, z) in [(-10, -4), (11, -1), (2, 10), (-6, -11), (9, 10), (-11, 9), (4, -12), (12, 6)]:
        yb = dome_y(x, z) + 0.4
        SC.tube(body, [(x, yb, z), (x, yb - 2.2, z)], 0.4, 0.3, M('wood', '#5a3e28'), k=6, name='trunk', info={'hem': False})
        SC.lathe(body, (x, z), [(yb - 1.4, 1.7), (yb - 3.0, 1.2), (yb - 4.4, 0.6), (yb - 5.3, 0.05)], M('leaf', '#3e7a2e'), k=10,
                 caps=(None, 'round'), cap_len=0.3, name='tree', info={'hem': False})
    head = r.bone('head', body, (0, 14, -15), anim='head')
    face = [BZ.eye((sx * 4.5, 12.6, -24.0), 0.95, '#e8ffb0', slit=False) for sx in (-1, 1)]
    face += [BZ.dot((sx * 1.2, 13.4, -30.6), 0.4, '#2a2e22') for sx in (-1, 1)]
    face += [BZ.line((sx * 4.2, 16.4, -21.5), (sx * 1.6, 16.7, -30.3), 0.22, '#2a2e22') for sx in (-1, 1)]
    BZ.loft(head, [(0, 14.4, -13.5), (0, 14.2, -18), (0, 14.0, -20)], [4.2, 4.0, 4.6], [3.8, 3.5, 3.9], hide, k=20, caps=(None, None), name='neck')
    BZ.loft(head, [(0, 14.0, -19.5), (0, 14.0, -23.5), (0, 14.8, -27.8), (0, 15.6, -30.8)], [5.0, 5.0, 4.0, 2.4], [4.2, 4.0, 3.2, 2.0],
            hide, k=24, spots=face, name='skull')
    for sx in (-1, 1):
        BZ.horn(head, (sx * 3.4, 10.4, -22), (sx * 0.35, -0.5, 1), 8.0, 1.0, M('rock', '#9a9282', snow='#f2f6fa', snow_y=7.5),
                curl=(sx * 0.5, 0.6, 1.0))
    for name, anim, sx, sz in [('leg_fr', 'leg_r', -1, -1), ('leg_fl', 'leg_l', 1, -1), ('leg_br', 'leg_l', -1, 1), ('leg_bl', 'leg_r', 1, 1)]:
        BZ.limb(r, body, name, anim, 15.5, 24, sx * 10, sz * 10, 3.6, 3.0, hide, foot=M('rock', '#4a463c'),
                claw=M('horn', '#e8e0c0', tip='#9a9070'), toes=4, bend=0.4)
    BZ.tail(r, body, (0, 14.2, 15), hide, [(2.6, 2.4, 4), (2.0, 1.9, 4), (1.4, 1.3, 3)], amp=0.08, speed=0.05, droop=0.2)
    return r

def light_vanes(span, height, res=2):
    """Photon wing: a fan of light blades in rainbow colours."""
    import pixart as PA
    cols = ['#ff8a9a', '#ffcf7a', '#fff38a', '#9affb0', '#8ae8ff', '#a8a0ff', '#f0a0ff']
    W, H = int(span * res) + 6, int(height * res) + 6
    def draw(art):
        for i in range(7):
            t = i / 6
            x0 = 3 + t * (W - 10)
            L = H * (0.55 + 0.4 * t)
            ang = math.radians(78 - 30 * t)
            x1, y1 = x0 + math.cos(ang) * L * 0.35, 3 + math.sin(ang) * L
            art.poly([(x0 - 1.6, 3), (x0 + 1.6, 3), (x1 + 1.2, y1 - 2), (x1, y1), (x1 - 1.4, y1 - 2)],
                     PA.mat('energy', cols[i], 0.85, d=0.35), 2)
        art.stroke([(1, 2.5), (W - 3, 3.5)], 2.0, PA.mat('metal', '#4a5468', 0.0, d=0.8, d0=0.4, bev=1), 4)
    return draw, W, H

@recipe
def teia():
    # 光越天龍 テイア — 機械と融合したかのような金属質の外殻の小型の龍。光子の流れを模した翼、飛行中は虹色の残光。
    # 魔力を光子へ変換する推進器官。快活で陽気な兄貴分。
    r = Rig('teia')
    SC.Sculpt(r)
    metal = M('metal', '#a8b4c8', accent='#b5ffff', pattern='circuit', pattern_glow=True, glow_amount=0.5)
    dark = M('metal', '#4a5468', rivets=True)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=4.0, speed=0.08)
    body = r.bone('body', root, (0, 14, 0), anim='sway', ax=0, amp=0.05, speed=0.08)
    spine = [BZ.dot((0, 10.5, z), 0.45, '#b5ffff', glow=True) for z in (-3, 0, 3)]
    spine += [BZ.dot((sx * 1.6, 13.4, 6.9), 0.7, '#ffffff', glow=True) for sx in (-1, 1)]
    BZ.loft(body, [(0, 14, -6.6), (0, 13.8, -2), (0, 14, 3), (0, 14.3, 6.9)], [3.0, 4.0, 3.6, 2.2], [3.0, 3.6, 3.3, 2.2], metal, k=20,
            spots=spine, name='torso')
    SC.crbox(body, (0, 10.6, -2), (5, 0.8, 5.5), M('metal', '#c8d2e0', rivets=True), radius=0.3, name='shoulder_plate')
    neck = r.bone('neck', body, (0, 13, -6), rot=(-0.4, 0, 0))
    BZ.loft(neck, [(0, 13, -5.5), (0, 13, -11.2)], [1.9, 1.6], [1.9, 1.6], metal, k=12, name='neck')
    head = r.bone('head', neck, (0, 12, -11), anim='head')
    face = [BZ.eye((sx * 2.55, 11.4, -14.4), 0.62, '#e0ffff', slit=False) for sx in (-1, 1)]
    face += [BZ.line((sx * 2.3, 12.0, -15.5), (sx * 1.0, 12.4, -20.8), 0.2, '#b5ffff', glow=True) for sx in (-1, 1)]
    BZ.loft(head, [(0, 12, -11.2), (0, 12.1, -15), (0, 12.7, -19), (0, 13.1, -21.6)], [2.8, 2.9, 2.0, 1.0], [2.4, 2.4, 1.6, 0.9],
            M('metal', '#c8d2e0', accent='#b5ffff', pattern='gold_lines', pattern_glow=True, glow_amount=0.4), k=18, spots=face, name='skull')
    for sx in (-1, 1):
        BZ.horn(head, (sx * 1.9, 10.0, -13), (sx * 0.2, -0.6, 1), 6.5, 0.5, M('horn', '#e0e8f4', tip='#b5ffff', glow=True), curl=(0, 0.4, 1.0))
    for name, anim, sx, sz in [('leg_fr', 'leg_r', -1, -1), ('leg_fl', 'leg_l', 1, -1), ('leg_br', 'leg_l', -1, 1), ('leg_bl', 'leg_r', 1, 1)]:
        b = r.bone(name, body, (sx * 2.5, 16.5, sz * 4), rot=(0.9, 0, 0), anim=anim)
        BZ.loft(b, [(sx * 2.5, 16.3, sz * 4), (sx * 2.5, 18.5, sz * 4 + 0.3), (sx * 2.5, 20.4, sz * 4)], [0.9, 0.75, 0.6], None, dark, k=10,
                name='leg')
        BZ.loft(b, [(sx * 2.5, 20.6, sz * 4 + 0.3), (sx * 2.5, 20.8, sz * 4 - 1.2)], [0.8, 0.6], [0.45, 0.35], dark, k=10, name='paw')
    for sx in (-1, 1):
        nm = 'wing_' + ('r' if sx < 0 else 'l')
        wb = r.bone(nm, body, (sx * 3.6, 11, -2), rot=(0, sx * 0.25, sx * -0.55), anim=nm, ax=2, amp=0.28, speed=0.16)
        draw, W, H = light_vanes(15, 11)
        SC.relief(wb, draw, W, H, np.array([sx * 3.4, 10.0, -2.5]), np.array([sx, 0, 0.0]), np.array([0, 0, 1.0]), M('fin', '#c8ffff'),
                  name='vanes')
    end, (x, y, z) = BZ.tail(r, body, (0, 14.2, 6.5), metal, [(1.5, 1.5, 4), (1.3, 1.3, 4), (1.0, 1.0, 4), (0.8, 0.8, 4), (0.5, 0.5, 4)],
                             amp=0.2, speed=0.1)
    draw, W, H = light_vanes(12, 7)
    SC.relief(end, draw, W, H, np.array([0, y - 3.5, z - 1.5]), np.array([0, 0, 1.0]), np.array([0, 1.0, 0]), M('fin', '#ffffff'), name='trail')
    return r

@recipe
def eomaia():
    # 始祖神獣 エオマイア — 獅子の鬣、狼の牙、蛇の鱗、鳥の翼、魚の鰭、象の牙、鹿の角、獣の爪。
    # すべての獣性が調和した原初の完全体。傲岸不遜な王にして母。
    r = Rig('eomaia')
    SC.Sculpt(r)
    fur = M('fur', '#b8935a')
    mane = M('fur', '#5a3a22', tip='#c08a40')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 12, 0), anim='breath')
    BZ.loft(body, [(0, 12, -10.5), (0, 11.8, -4), (0, 12, 4), (0, 12.2, 10.5)], [5.6, 6.0, 5.6, 4.6], [5.2, 5.4, 5.0, 4.4], fur, k=22,
            name='torso')
    BZ.loft(body, [(0, 7.2, -9), (0, 7.0, -2)], [3.5, 2.2], [1.6, 1.0], mane, k=16, caps=('round', 'point'),
            mod=lambda th, t: 1 + 0.12 * np.cos(9 * th), name='mane_back')
    head = r.bone('head', body, (0, 9, -10), anim='head')
    BZ.loft(head, [(0, 9.4, -7.5), (0, 9.5, -10.5), (0, 9.8, -13.5)], [6.4, 7.6, 6.0], [6.0, 7.2, 5.6], mane, k=30, caps=('round', 'round'),
            mod=lambda th, t: 1 + 0.14 * np.cos(11 * th + 2 * t), name='mane')
    face = [BZ.eye((sx * 3.85, 8.8, -16.4), 0.8, '#ffd76a') for sx in (-1, 1)]
    face += [BZ.dot((0, 11.6, -22.9), 0.6, '#2a1a10'), BZ.line((-1.2, 13.4, -21.6), (1.2, 13.4, -21.6), 0.15, '#2a1a10')]
    BZ.loft(head, [(0, 9.6, -12), (0, 9.8, -16), (0, 11.0, -19.5), (0, 12.0, -22.8)], [4.4, 4.2, 3.0, 2.2], [4.0, 3.8, 2.6, 1.9],
            M('fur', '#b8935a'), k=22, spots=face, name='skull')
    BZ.teeth(head, (-1.5, 13.0, -21.8), (-0.7, 13.0, -22.4), 1, 1.4)
    BZ.teeth(head, (1.5, 13.0, -21.8), (0.7, 13.0, -22.4), 1, 1.4)
    for sx in (-1, 1):
        BZ.horn(head, (sx * 2.3, 12.8, -20.5), (sx * 0.25, 0.55, -1), 4.2, 0.5, M('horn', '#f4ecd8', tip='#d8c8a0'), curl=(0, -1.4, -0.4),
                name='tusk')
        ear = r.bone('ear_' + ('r' if sx < 0 else 'l'), head, (sx * 3.4, 6.0, -14), rot=(0, 0, sx * 0.3), anim='sway', ax=2, amp=0.04,
                     speed=0.1, phase=sx)
        SC.sweep(ear, SC.bezier((sx * 3.3, 6.4, -14), (sx * 3.6, 4.6, -14.2), (sx * 4.0, 3.0, -14.0), n=6), lambda t: 0.9 * (1 - 0.8 * t),
                 0.3, fur, k=8, up=(0, 0, -1), caps=('round', 'point'), name='ear', info={'hem': False})
        BZ.horn(head, (sx * 2.4, 6.0, -14), (sx * 0.45, -1, 0.15), 10, 0.5, M('horn', '#efe4c8', tip='#ffe9a0', glow=True),
                curl=(sx * 1.2, 0.2, 0.8), name='antler', tines=2)
    for name, anim, sx, sz in [('leg_fr', 'leg_r', -1, -1), ('leg_fl', 'leg_l', 1, -1), ('leg_br', 'leg_l', -1, 1), ('leg_bl', 'leg_r', 1, 1)]:
        lg = BZ.limb(r, body, name, anim, 15.5, 24, sx * 4, sz * 7, 2.0, 1.6, fur, foot=M('fur', '#5a3a22'),
                     claw=M('horn', '#2a2420', tip='#f0e8d8'), bend=0.8)
        if sz < 0:
            BZ.fin(lg, (sx * 5.6, 18.5, -7.5), (0, 1, 0), (sx, 0, 0.3), [(0, 0), (1, 2.5), (3.5, 3.6), (4.5, 1.5), (4.2, 0)], '#6aa8c0',
                   edge='#bff0ff', name='leg_fin')
    for sx in (-1, 1):
        w = wing(r, body, sx, (sx * 5, 7.5, -3), 'feather', M('feather', '#7a5a34', tip='#f0e0b0'), span=16, height=11, rest=0.7)
        w.rot = (-0.35, sx * -0.7, sx * -0.55)
    BZ.tail(r, body, (0, 10, 10), M('scale', '#4a7a3a', belly='#c8d8a0'), [(1.6, 1.6, 4), (1.4, 1.4, 4), (1.1, 1.1, 4), (0.9, 0.9, 3), (0.6, 0.6, 3)],
            amp=0.2, speed=0.09, droop=0.3, tip=M('scale', '#2a4a22', belly='#c8d8a0'))
    return r

@recipe
def demiurgos():
    # 空創龍王 デミウルゴス — 黒色の鱗に、所々虹色の宝石を埋め込んだような輝きを宿す五メートルほどの小型の龍。
    # 威圧よりも神秘を感じさせる姿。
    r = Rig('demiurgos')
    SC.Sculpt(r)
    sc = M('scale', '#1b2033', belly='#3a3a5a')
    gems = ['#ff5f7a', '#5fc8ff', '#ffe95f', '#b05fff', '#5fff9b', '#ff9f4f']
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.0, speed=0.05)
    body = r.bone('body', root, (0, 14, 0), anim='breath')
    inlay = [BZ.dot((x, y, z), 0.6, gems[i % len(gems)], glow=True) for i, (x, y, z) in
             enumerate([(-2.6, 9.8, -4), (1.8, 9.6, 1), (-1, 9.7, 5), (2.8, 10.0, -6), (0, 9.5, -1), (-4.4, 12, 2), (4.6, 13, -2), (4.2, 11.5, 4)])]
    BZ.loft(body, [(0, 14, -8.5), (0, 13.8, -3), (0, 14, 3), (0, 14.4, 8.4)], [4.4, 5.2, 5.0, 3.6], [4.0, 4.6, 4.4, 3.4], sc, k=22,
            spots=inlay, name='torso')
    neck = r.bone('neck', body, (0, 12, -8), rot=(-0.5, 0, 0))
    BZ.loft(neck, [(0, 12, -7.5), (0, 12, -15.2)], [2.6, 2.2], [2.6, 2.2], sc, k=14, name='neck')
    head = r.bone('head', neck, (0, 11, -15), anim='head')
    face = [BZ.eye((sx * 3.1, 9.9, -19.0), 0.7, '#c8a0ff') for sx in (-1, 1)]
    face += [BZ.dot((sx * 0.7, 10.9, -27.0), 0.3, '#0a0c14') for sx in (-1, 1)]
    BZ.loft(head, [(0, 10.6, -14.8), (0, 10.8, -19), (0, 11.6, -24), (0, 12.0, -27.2)], [3.4, 3.4, 2.4, 1.2], [3.0, 2.8, 2.0, 1.0], sc, k=20,
            spots=face, name='skull')
    TK.crystal(head, (0, 7.6, -19), 0.55, M('gem', '#ffffff'), long=1.3)
    for sx in (-1, 1):
        BZ.horn(head, (sx * 2.5, 8.2, -16.5), (sx * 0.3, -0.55, 1), 7.5, 0.7, M('horn', '#20203a', tip='#ae8ff4', glow=True), curl=(0, 0.5, 1.2))
    jaw = r.bone('jaw', head, (0, 13.5, -16), anim='jaw')
    BZ.loft(jaw, [(0, 13.7, -16), (0, 13.9, -26.2)], [2.2, 1.0], [0.75, 0.5], sc, k=14, name='jaw')
    BZ.teeth(jaw, (-1.4, 13.2, -18), (-0.7, 13.3, -25.5), 4, 0.55, down=False)
    BZ.teeth(jaw, (1.4, 13.2, -18), (0.7, 13.3, -25.5), 4, 0.55, down=False)
    for sx in (-1, 1):
        wing(r, body, sx, (sx * 4.6, 10, -3), 'membrane', M('membrane', '#2c2648', accent='#ae8ff4'), span=18, height=13,
             mat2=M('horn', '#20203a', tip='#ae8ff4'), rest=0.3)
    for name, anim, sx, sz in [('leg_fr', 'leg_r', -1, -1), ('leg_fl', 'leg_l', 1, -1), ('leg_br', 'leg_l', -1, 1), ('leg_bl', 'leg_r', 1, 1)]:
        BZ.limb(r, body, name, anim, 16.5, 24, sx * 3.5, sz * 5, 1.6, 1.2, sc, foot=M('scale', '#10141f'), claw=M('horn', '#20203a', tip='#ae8ff4'))
    end, (x, y, z) = BZ.tail(r, body, (0, 14.2, 8), sc, [(2.0, 1.9, 4), (1.6, 1.6, 4), (1.4, 1.4, 4), (1.1, 1.1, 4), (0.9, 0.9, 3), (0.6, 0.6, 3)],
                             amp=0.18, speed=0.08, droop=0.08, end_cap='round')
    TK.crystal(end, (x, y, z + 0.6), 0.8, M('gem', '#ae8ff4'), long=1.6)
    return r


def eyeball(bone, c, r, iris, glow=True, slit=True):
    """A round eye looking along -Z of its bone (bones turn it outwards)."""
    x, y, z = c
    BZ.loft(bone, [(x, y, z + r * 0.55), (x, y, z - r * 0.55)], r * 0.86, r * 0.86, M('skin', '#f4eef8'), k=12, caps=('round', 'round'),
            cap_len=r * 0.45, spots=[BZ.eye((x, y, z - r), r * 0.62, iris, glow=glow, slit=slit)], name='eyeball')

@recipe
def chaos():
    # 万象混沌 カオス — 見るたびに変わる姿：虹色の胎児、紫黒の肉塊、無数の眼球を宿した雲、海をまとった獣、都市の骨の竜。
    # 中心に稀に浮かぶ虹色の核（宝石のように美しく、油膜のように濁り、星雲のように輝く）。上下逆さまの都市、魚の雨。
    r = Rig('chaos')
    SC.Sculpt(r)
    flesh = M('oilslick', '#2a1838')
    flesh2 = M('oilslick', '#1c1428')
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=3.0, speed=0.04)
    body = r.bone('mass', root, (0, 12, 0), anim='pulse', amp=0.04, speed=0.05)
    lump = lambda th, t: 1 + 0.09 * np.sin(3 * th + 5 * t) + 0.06 * np.cos(5 * th - 3 * t) + 0.05 * np.sin(7 * th + 11 * t)
    BZ.loft(body, [(0, 4.5, 0), (0, 8, 0), (0, 12, 0), (0, 16, 0), (0, 19.5, 0)], [6.0, 8.2, 8.8, 8.2, 6.0], [6.2, 8.4, 9.0, 8.4, 6.0],
            flesh, k=30, up=(0, 0, -1), caps=('round', 'round'), mod=lump, name='mass')
    for (c, rad, m) in [((-6, 6, 3), 4.2, flesh2), ((7, 15, -2), 4.0, flesh2), ((-5, 18, -5), 3.8, flesh), ((3, 4, -3), 3.0, flesh)]:
        x, y, z = c
        BZ.loft(body, [(x, y - rad * 0.5, z), (x, y + rad * 0.5, z)], rad * 0.9, rad * 0.9, m, k=16, up=(0, 0, -1), caps=('round', 'round'),
                cap_len=rad * 0.5, mod=lump, name='lump')
    core = r.bone('core', body, (0, 11, -8.5), anim='pulse', amp=0.14, speed=0.1)
    TK.sphere(core, (0, 11, -9.2), 2.3, M('rainbow', '#ffffff'), name='core')
    TK.crystal(core, (0, 11, -10.6), 1.2, M('gem', '#ffffff'), long=1.6)
    eyes = [((-5, 8, -8), 0, 3), ((5, 6, -8), 0, 2), ((6, 17, -8), 0, 3), ((-4, 16, -8.5), 0, 2), ((8.5, 11, 2), -math.pi / 2, 3),
            ((-8.5, 13, -1), math.pi / 2, 3), ((-9, 6, 4), math.pi / 2, 2), ((2, 5, 8), math.pi, 3), ((-3, 15, 8), math.pi, 2)]
    for i, ((x, y, z), yaw, s_) in enumerate(eyes):
        e = r.bone(f'eye{i}', body, (x, y, z), rot=(0, yaw, 0), anim='sway', ax=1, amp=0.12, speed=0.07, phase=i)
        eyeball(e, (x, y, z), s_ * 0.6, ['#69f5f2', '#ff6fd0', '#ffe06a'][i % 3], slit=(i % 2 == 0))
    for i in range(6):
        a = i / 6 * math.tau
        st = (math.cos(a) * 6.5, 16 + (i % 2) * 3, math.sin(a) * 6.5)
        t = r.bone(f'tent{i}', body, st, rot=(0.9 * math.sin(a), a, 0))
        BZ.tail(r, t, st, M('oilslick', '#2a1838'), [(1.5, 1.5, 4), (1.1, 1.1, 4), (0.8, 0.8, 3), (0.5, 0.5, 3)], name=f't{i}_', amp=0.25,
                speed=0.08, droop=0.25)
    bits = [('grass', (2, 2, 2)), ('house', (2, 2, 2)), ('fish', (1, 1, 3)), ('crystal', (2, 3, 2)), ('cloud', (3, 2, 2))]
    for i, (kind, s_) in enumerate(bits):
        frag = r.bone(f'chaos{i}', root, (0, 8 - i, 0), anim='chaos', phase=i * 1.3)
        a = i / 5 * math.tau
        c = (math.cos(a) * 15, -2 - i * 2, math.sin(a) * 15)
        if kind == 'grass':
            SC.crbox(frag, c, s_, M('rock', '#7a5a3a', top='#5e9a3a'), radius=0.25, name='block')
        elif kind == 'house':
            SC.crbox(frag, c, s_, M('wood', '#c8a070'), radius=0.2, name='house')
            SC.lathe(frag, (c[0], c[2]), [(c[1] + 1.0, 1.7), (c[1] + 2.6, 0.05)], M('cloth', '#a03a2a'), k=4, caps=(None, None), name='roof',
                     info={'hem': False})
        elif kind == 'fish':
            BZ.loft(frag, [(c[0], c[1], c[2] - 1.6), (c[0], c[1], c[2] + 1.6)], [0.5, 0.3], [0.8, 0.5], M('scale', '#f0a040', belly='#fff0d0'),
                    k=10, name='fish', spots=[BZ.eye((c[0] + 0.45, c[1] - 0.2, c[2] - 1.0), 0.25, '#202020', glow=False, slit=False)])
        elif kind == 'crystal':
            TK.crystal(frag, c, 1.0, M('rainbow', '#ffffff'), long=1.6)
        else:
            eyeball(frag, c, 1.2, '#69f5f2')
    return r

@recipe
def hephaistos():
    # 典域工廠 ヘファイストス — 水晶とも未知の金属ともつかないSFじみたキューブを核とした球状の機械。
    # 周囲に大小の機械球体が浮遊し、それぞれが腕であり、眼であり、炉であり、工房であり、兵器でもある。
    r = Rig('hephaistos')
    SC.Sculpt(r)
    shell = M('metal', '#4a627a', accent='#52e8d6', pattern='circuit', pattern_glow=True)
    plate = M('metal', '#8aa0b4', rivets=True)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=2.0, speed=0.05)
    body = r.bone('body', root, (0, 12, 0), anim='spin', speed=0.008, cast=0.0)
    BZ.loft(body, [(0, 6.4, 0), (0, 9, 0), (0, 12, 0), (0, 15, 0), (0, 17.6, 0)], [3.5, 6.0, 6.8, 6.0, 3.5], None, shell, k=32,
            up=(0, 0, -1), caps=('round', 'round'), cap_len=1.6, name='shell')
    SC.torus(body, (0, 12, 0), 7.0, 0.9, M('metal', '#5a7088', accent='#52e8d6', pattern='rings'), axis='y', k=10, n=40, name='belt')
    for y in (8.0, 16.0):
        SC.torus(body, (0, y, 0), 5.6, 0.45, plate, axis='y', k=8, n=36, name='band')
    for sx in (-1, 1):
        SC.crbox(body, (sx * 7.6, 12, 0), (0.8, 3.6, 3.6), M('energy', '#52e8d6'), radius=0.3, name='vent')
    core = r.bone('core', root, (0, 12, -7.5), anim='spin', ax=2, speed=0.05)
    SC.crbox(core, (0, 12, -7.8), (4.4, 4.4, 4.4), M('gem', '#a5f3ff'), radius=0.6, name='cube')
    TK.crystal(core, (0, 12, -10.4), 1.2, M('energy', '#e8ffff'), long=1.4)
    ring = r.bone('ring', root, (0, 12, 0), rot=(1.3, 0, 0.2), anim='spin', speed=0.03)
    ring.box((-12, 12, -12), (24, 0, 24), M('ring', '#52e8d6', width=0.06, spikes=16, glow_amount=0.6), name='ring')
    hub = r.bone('foundries', root, (0, 10, 0), anim='spin', speed=0.025)
    for i, kind in enumerate(['eye', 'arm', 'furnace', 'workshop', 'cannon']):
        a = 2 * math.pi * i / 5
        px, pz = math.cos(a) * 14, math.sin(a) * 14
        b = r.bone(f'foundry_{kind}', hub, (px, 10, pz), anim='float', amp=1.0, speed=0.08, phase=i * 1.7)
        TK.sphere(b, (px, 10, pz), 2.1, M('metal', '#5a7088', accent='#52e8d6', pattern='rings'), name='orb')
        SC.torus(b, (px, 10, pz), 2.25, 0.3, plate, axis='y', k=6, n=18, name='orb_band')
        if kind == 'eye':
            TK.crystal(b, (px, 10, pz - 2.2), 0.8, M('gem', '#52e8d6'), long=1.0)
        elif kind == 'arm':
            SC.sweep(b, SC.bezier((px, 11.8, pz), (px, 14, pz - 0.6), (px - 0.4, 15.6, pz - 1.6), n=6), 0.35, None, M('metal', '#b0c0d0'), k=6,
                     caps=('round', 'round'), name='arm', info={'hem': False})
            for sgn in (-1, 1):
                SC.sweep(b, [(px - 0.4, 15.6, pz - 1.6), (px - 0.4 + sgn * 0.6, 16.6, pz - 2.2)], lambda t: 0.25 * (1 - 0.7 * t), None,
                         M('metal', '#b0c0d0'), k=5, caps=('round', 'point'), name='claw', info={'hem': False})
        elif kind == 'furnace':
            TK.sphere(b, (px, 10, pz - 2.0), 0.8, M('energy', '#ff9a40'), name='fire')
        elif kind == 'workshop':
            TK.crystal(b, (px, 7.4, pz), 0.5, M('energy', '#fff0a0'), long=1.4)
        else:
            SC.sweep(b, [(px, 10, pz - 1.5), (px, 10, pz - 5.2)], 0.45, None, M('metal', '#2a3440'), k=8, caps=('flat', 'flat'), name='barrel',
                     info={'hem': False})
    return r

@recipe
def yggdrasil():
    # 玖天神樹 イグドラシル — 天を突く超巨大な樹。雲海を貫く幹、九つの世界を抱擁する枝葉。魔力の大動脈。
    # 花が一輪咲くだけで周囲が神域の魔力濃度に。内部に九つの世界。
    r = Rig('yggdrasil')
    SC.Sculpt(r, td=1.5)
    bark = M('wood', '#5a4430', veins='#d8ff8a', glow_amount=0.45)
    leaf = M('leaf', '#477449', flowers=['#ffe0f0', '#fff0a0'], flower_glow=True)
    leaf2 = M('leaf', '#5a9a4a', flowers=['#ffffff', '#ffd0e8'], flower_glow=True)
    root = r.bone('root', None, (0, 24, 0), anim='root')
    trunk = r.bone('trunk', root, (0, 24, 0), anim='sway', ax=2, amp=0.01, speed=0.03)
    twist = lambda th, t: 1 + 0.07 * np.cos(5 * th + 6 * t)
    BZ.loft(trunk, [(0, 24.3, 0), (0, 21, 0), (0, 14, 0), (0, 4, 0), (0, -8, 0), (0, -18, 0)], [8.5, 6.4, 5.4, 5.0, 4.4, 3.4], None, bark,
            k=26, up=(0, 0, -1), caps=(None, 'round'), mod=twist, name='trunk')
    for i in range(7):
        a = i / 7 * math.tau + 0.3
        rb = r.bone(f'root{i}', trunk, (math.cos(a) * 5, 21, math.sin(a) * 5))
        p0 = np.array([math.cos(a) * 4.5, 20.5, math.sin(a) * 4.5])
        SC.sweep(rb, SC.bezier(p0, p0 + (math.cos(a) * 4, 2.6, math.sin(a) * 4), p0 + (math.cos(a) * 9, 3.6, math.sin(a) * 9), n=8),
                 lambda t: 2.0 * (1 - 0.75 * t), None, M('wood', '#4a3626'), k=10, caps=('round', 'point'), name='root', info={'hem': False})
    heart = r.bone('heart', trunk, (0, 4, -5.5), anim='pulse', amp=0.1, speed=0.06)
    TK.crystal(heart, (0, 4, -5.6), 1.6, M('gem', '#c8ff8a'), long=1.5)
    def foliage(bone, c, R, m, n=5, seed=0):
        rng = np.random.default_rng(seed)
        cx, cy, cz = c
        for k in range(n):
            off = rng.normal(0, R * 0.38, 3) * (0.0 if k == 0 else 1.0)
            rr = R * (1.0 if k == 0 else rng.uniform(0.55, 0.8))
            x, y, z = cx + off[0], cy + off[1] * 0.6, cz + off[2]
            BZ.loft(bone, [(x, y - rr * 0.45, z), (x, y + rr * 0.45, z)], rr * 0.95, rr * 0.95, m, k=16, up=(0, 0, -1),
                    caps=('round', 'round'), cap_len=rr * 0.6, mod=lambda th, t: 1 + 0.08 * np.cos(6 * th + 3 * t), name='leaves')
    for i in range(5):
        a = i / 5 * math.tau + 0.4
        y = -8 - (i % 2) * 5
        br = r.bone(f'branch{i}', trunk, (math.cos(a) * 3.5, y, math.sin(a) * 3.5), anim='sway', ax=2, amp=0.02, speed=0.04, phase=i)
        p0 = np.array([math.cos(a) * 3, y, math.sin(a) * 3])
        tip = p0 + (math.cos(a) * 12, -11, math.sin(a) * 12)
        SC.sweep(br, SC.bezier(p0, p0 + (math.cos(a) * 6, -2, math.sin(a) * 6), tip, n=8), lambda t: 1.8 * (1 - 0.6 * t), None, bark, k=10,
                 caps=('round', 'round'), name='branch', info={'hem': False})
        foliage(br, tuple(tip + (0, -2, 0)), 5.5, leaf if i % 2 else leaf2, n=4, seed=i)
    foliage(trunk, (0, -24, 0), 13, leaf2, n=7, seed=11)
    foliage(trunk, (0, -33, 0), 9.5, leaf, n=5, seed=12)
    foliage(trunk, (0, -40, 0), 6, leaf2, n=3, seed=13)
    worlds = ['#ffd06a', '#8ad0ff', '#ff8aa8', '#a0ff8a', '#d0a0ff', '#ffffff', '#ff9a50', '#60e0d0', '#f0f080']
    hub = r.bone('worlds', trunk, (0, -22, 0), anim='spin', speed=0.01)
    for i, col in enumerate(worlds):
        a = i / 9 * math.tau
        px, pz = math.cos(a) * 21, math.sin(a) * 21
        b = r.bone(f'world{i}', hub, (px, -18 + (i % 3) * 3, pz), anim='float', amp=0.6, speed=0.06, phase=i)
        TK.sphere(b, (px, -18 + (i % 3) * 3, pz), 1.3, M('gem', col), name='world')
        SC.torus(b, (px, -18 + (i % 3) * 3, pz), 1.9, 0.12, M('ring', col), axis='y', k=5, n=16, name='world_ring')
    return r

@recipe
def familiar_beast():
    # エオマイアの仔：小さな角の生えた獣
    r = Rig('familiar_beast')
    SC.Sculpt(r)
    fur = M('fur', '#b8935a')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 17, 0), anim='breath')
    BZ.loft(body, [(0, 17, -3.8), (0, 16.8, 0), (0, 17, 3.6)], [2.0, 2.2, 1.8], [2.0, 2.1, 1.8], fur, k=16, name='torso')
    head = r.bone('head', body, (0, 15, -4), anim='head')
    face = [BZ.eye((sx * 1.85, 13.9, -7.0), 0.55, '#ffd76a', slit=False) for sx in (-1, 1)]
    face += [BZ.dot((0, 15.4, -9.9), 0.35, '#2a1a10')]
    BZ.loft(head, [(0, 14.5, -4.4), (0, 14.4, -7), (0, 15.2, -9.0), (0, 15.6, -10.0)], [2.3, 2.2, 1.4, 0.8], [2.1, 2.0, 1.2, 0.7],
            fur, k=16, spots=face, name='skull')
    for sx in (-1, 1):
        SC.sweep(head, SC.bezier((sx * 1.7, 13.0, -5.6), (sx * 2.5, 12.5, -5.5), (sx * 3.2, 12.2, -5.3), n=5), lambda t: 0.5 * (1 - 0.8 * t), 0.18,
                 fur, k=6, up=(0, 0, -1), caps=('round', 'point'), name='ear', info={'hem': False})
        BZ.horn(head, (sx * 0.8, 12.6, -6.3), (sx * 0.3, -1, 0.2), 2.6, 0.3, M('horn', '#efe4c8', tip='#ffe9a0', glow=True), curl=(sx * 0.4, 0, 0.4),
                name='antler', tines=1)
    for name, anim, sx, sz in [('leg_fr', 'leg_r', -1, -1), ('leg_fl', 'leg_l', 1, -1), ('leg_br', 'leg_l', -1, 1), ('leg_bl', 'leg_r', 1, 1)]:
        BZ.limb(r, body, name, anim, 18.2, 24, sx * 1.4, sz * 2.8, 0.85, 0.6, fur, foot=M('fur', '#6a4a28'), bend=0.4)
    BZ.tail(r, body, (0, 15.6, 3.6), M('fur', '#8a6a3a', tip='#f0e0c0'), [(0.9, 0.9, 2.5), (1.1, 1.1, 2.5)], amp=0.25, speed=0.12, droop=-0.4,
            end_cap='round')
    return r

@recipe
def familiar_sprite():
    # イグドラシル／マグナ・マーテルの若葉の精
    r = Rig('familiar_sprite')
    SC.Sculpt(r)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=3.0, speed=0.09)
    body = r.bone('body', root, (0, 17, 0), anim='pulse', amp=0.06, speed=0.1)
    face = [BZ.dot((sx * 0.9, 17.0, -2.3), 0.42, '#fffbd0', glow=True) for sx in (-1, 1)]
    BZ.loft(body, [(0, 15.0, 0), (0, 17, 0), (0, 19.2, 0)], [1.6, 2.3, 1.5], None, M('leaf', '#6aa04a'), k=16, up=(0, 0, -1),
            caps=('round', 'round'), cap_len=1.0, spots=face, name='seed')
    TK.crystal(body, (0, 13.4, 0), 0.6, M('gem', '#d8ff8a'), long=1.2)
    TK.star_plate(body, (0, 12.4, 0), 0.9, M('plane', '#ffd0e8', glow=True), shape='star', normal=(0, 0, -1))
    for sx in (-1, 1):
        nm = 'wing_' + ('r' if sx < 0 else 'l')
        w = r.bone(nm, body, (sx * 2, 16, 1), rot=(0, sx * -0.3, sx * -0.4), anim=nm, amp=0.4, speed=0.4)
        TK.star_plate(w, (sx * 4.2, 15.2, 1), 2.6, M('plane', '#9ad87a', glow=True), shape='leaf', normal=(0, 0, 1))
    return r

@recipe
def familiar_curse():
    # 獄華の分御霊：意志を持つ呪詛の小塊
    r = Rig('familiar_curse')
    SC.Sculpt(r)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.0, speed=0.07)
    body = r.bone('body', root, (0, 19, 0), anim='liquid', amp=0.08)
    eyes = [BZ.eye(p, rr, c) for p, rr, c in [((-1.6, 18.6, -3.4), 0.7, '#e070f0'), ((1.4, 19.6, -3.5), 0.55, '#ffd0ff'),
                                                ((2.6, 17.6, -2.8), 0.45, '#e070f0'), ((-0.2, 21.0, -3.3), 0.5, '#ffd0ff'),
                                                ((-3.0, 20.4, -1.6), 0.45, '#e070f0')]]
    BZ.loft(body, [(0, 17.4, 0), (0, 19.5, 0), (0, 21.8, 0)], [3.2, 3.8, 3.4], None, M('oilslick', '#3a2050'), k=20, up=(0, 0, -1),
            caps=('round', 'round'), cap_len=2.4, mod=lambda th, t: 1 + 0.08 * np.sin(4 * th + 6 * t), spots=eyes, name='blob')
    for sx in (-1, 1):
        hb = r.bone('horn_' + ('r' if sx < 0 else 'l'), body, (sx * 2, 16.6, 0), rot=(0, 0, sx * 0.4))
        BZ.horn(hb, (sx * 1.8, 17.0, 0), (sx * 0.2, -1, 0), 3.4, 0.55, M('horn', '#2a1a2a', tip='#af55bb', glow=True), curl=(sx * 0.6, 0, 0.3))
    return r

"""Relic weapon designs (pixel art). Each design draws into an Art in weapon space: u = 0 at the butt,
100 at the tip; v across (positive = right of the axis). The same drawing yields the 32px inventory
icon and the large sprite on the 3D in-hand prop."""
import math
import numpy as np
from PIL import Image
from pixart import Art, mat, icon_frame, sprite_frame

DESIGNS = {}

def design(name, title, kind, half_width=12, grip_u=12, upright_icon=False, length=22):
    """length: in-hand length in model units (sprite length)."""
    def deco(fn):
        DESIGNS[name] = dict(fn=fn, title=title, kind=kind, half_width=half_width, grip_u=grip_u,
                             upright_icon=upright_icon, length=length)
        return fn
    return deco

# ------------------------------------------------------------------------------------- shared parts
def grip(a, u0, u1, w, m, z=1):
    a.poly([(u0, -w / 2), (u1, -w / 2), (u1, w / 2), (u0, w / 2)], m, z)

def tapered(a, u0, u1, w0, w1, m, z=2, tip=None):
    pts = [(u0, -w0 / 2), (u1, -w1 / 2)]
    if tip:
        pts.append((u1 + tip, 0))
    pts += [(u1, w1 / 2), (u0, w0 / 2)]
    a.poly(pts, m, z)

def gem(a, u, v, r, color, z=6, glow=0.6):
    a.ell(u, v, r, r, mat('gem', color, glow=glow), z)

def wisp(a, u, v, length, width, color, z=7, lean=4):
    a.curve((u, v), (u + length * 0.5, v + lean), (u + length, v - lean * 0.3), width, mat('energy', color, glow=0.9, outline=False), z,
            taper=(width, 0.3))

# ------------------------------------------------------------------------------------- designs
@design('kokuhaku', '蒼白断界刀・虚', 'katana', half_width=10, grip_u=12, length=24)
def d_kokuhaku(a):
    steel = mat('metal', '#d6dde8')
    # curved blade (sori): edge on the -v side
    pts_e, pts_b = [], []
    for k in range(13):
        t = k / 12
        u = 30 + t * 70
        bend = 5.5 * t * t
        w = 6.2 - 2.5 * t
        pts_e.append((u, bend - w / 2))
        pts_b.append((u, bend + w / 2))
    tip = (101.5, 5.5 + 1.0)
    a.poly(pts_e + [tip] + list(reversed(pts_b)), steel, 3)
    a.stroke([(32 + t * 66, 5.5 * (t ** 2) - 1.4 + 0.5 * math.sin(t * 18)) for t in np.linspace(0, 1, 18)], 1.1,
             mat('energy', '#a8ecff', glow=0.9, outline=False), 4)                      # hamon
    a.stroke([(31, 1.6), (96, 5.0)], 0.8, mat('metal', '#f4f8ff', outline=False), 4)   # shinogi ridge
    a.poly([(27, -3.6), (30.5, -3.6), (30.5, 3.6), (27, 3.6)], mat('metal', '#e2b84a'), 5)   # habaki
    a.ell(25.5, 0, 2.2, 9.5, mat('metal', '#3a4250'), 5)                                # tsuba
    a.ell(25.5, 0, 1.0, 6.0, mat('metal', '#c8a050'), 6)
    grip(a, 3, 24, 6.4, mat('cloth', '#1c2440', pattern='wrap'), 2)
    for u in (8, 15):
        a.dot(u, 0, mat('metal', '#e2b84a'), 6, r=1.0)                                  # menuki
    a.poly([(0, -3.6), (3.5, -3.6), (3.5, 3.6), (0, 3.6)], mat('metal', '#b8c0cc'), 3)  # kashira
    for k, u in enumerate((52, 70, 86)):
        wisp(a, u, 9 + k, 12, 2.4, '#9fe8ff', lean=3)

@design('tenki_focus', '優先律の王笏', 'scepter', half_width=14, grip_u=25, length=26)
def d_tenki(a):
    gold = mat('metal', '#e8b83e')
    white = mat('metal', '#f6f2e8')
    grip(a, 4, 72, 4.2, white, 1)
    for u in (10, 30, 50, 68):
        a.poly([(u, -3.6), (u + 3, -3.6), (u + 3, 3.6), (u, 3.6)], gold, 3)
    a.ell(2.5, 0, 3, 4, gold, 3)
    gem(a, 2.5, 0, 1.6, '#9fd8ff')
    # sun crown at the head: rays, ring, crown, central sapphire
    for k in range(12):
        ang = 2 * math.pi * k / 12
        L = 15 if k % 2 == 0 else 11
        a.poly([(84 + math.cos(ang) * 6, math.sin(ang) * 6 - 0.0), (84 + math.cos(ang + 0.13) * L, math.sin(ang + 0.13) * L),
                (84 + math.cos(ang - 0.13) * L, math.sin(ang - 0.13) * L)], mat('metal', '#ffd76a', glow=0.35), 2)
    a.ring(84, 0, 9, 6.2, gold, 4)
    a.sym([(72, 5.5), (76, 7), (78, 4)], gold, 5)
    gem(a, 84, 0, 4.5, '#7fb8ff', z=6)
    for k in range(5):
        ang = -math.pi / 2 + (k - 2) * 0.42
        a.dot(84 + math.cos(ang) * 13 + 0, math.sin(ang) * 13, mat('gem', '#ffffff', glow=0.8), 7, r=0.8)

@design('savior', '救世の聖盾', 'shield', half_width=34, grip_u=50, upright_icon=True, length=18)
def d_savior(a):
    white = mat('metal', '#f4f6fb')
    gold = mat('metal', '#dac36c')
    # heater shield outline
    half = [(4, 0.1), (10, 14), (26, 26), (55, 30), (88, 30), (97, 26), (99, 0.1)]
    a.sym(half, gold, 1)
    a.sym([(8, 0.1), (13, 11), (28, 22.5), (55, 26), (86, 26), (94, 22), (96, 0.1)], white, 2)
    a.poly([(20, -3.2), (88, -3.2), (88, 3.2), (20, 3.2)], gold, 3)                     # cross
    a.poly([(64, -18), (71, -18), (71, 18), (64, 18)], gold, 3)
    a.ring(67.5, 0, 13, 10.5, mat('metal', '#ffe9a0', glow=0.45), 4)                   # halo
    gem(a, 67.5, 0, 4.0, '#fff3b0', z=6, glow=0.8)
    for s in (-1, 1):                                                                    # wings
        for k in range(4):
            a.poly([(60 - k * 7, s * (20 - k)), (64 - k * 7, s * (27 - k * 0.5)), (54 - k * 7, s * (25 - k))],
                   mat('cloth', '#fffaf0'), 5)


def ring_band(a, u, w, m, z=4, h=3):
    a.poly([(u, -w / 2), (u + h, -w / 2), (u + h, w / 2), (u, w / 2)], m, z)

def chain_links(a, pts, m, z=3, r=1.6):
    for k, (u, v) in enumerate(pts):
        a.ring(u, v, r, r * 0.45, m, z) if k % 2 == 0 else a.ell(u, v, r * 1.1, r * 0.5, m, z)

def feather(a, u, v, ang, L, w, m, z=3):
    du, dv = math.cos(ang), math.sin(ang)
    nu, nv = -dv, du
    a.poly([(u, v), (u + du * L * 0.35 + nu * w, v + dv * L * 0.35 + nv * w), (u + du * L, v + dv * L),
            (u + du * L * 0.35 - nu * w, v + dv * L * 0.35 - nv * w)], m, z)

@design('riha', '天冠言霊筆', 'brush', half_width=12, grip_u=30, length=24)
def d_riha(a):
    bamboo = mat('wood', '#e8d8a8')
    grip(a, 6, 64, 5.2, bamboo, 1)
    for u in (18, 34, 50):
        ring_band(a, u, 6.2, mat('wood', '#c8b47a'), 2, 1.6)
    a.poly([(62, -3.6), (69, -4.2), (69, 4.2), (62, 3.6)], mat('metal', '#e6b84a'), 3)
    a.sym([(68, 5.5), (76, 7.5), (86, 6), (95, 2.2), (100, 0.1)], mat('cloth', '#fbf6ee'), 2)          # bristles
    a.sym([(88, 4.8), (95, 2.2), (100, 0.1)], mat('energy', '#ffcf5a', glow=0.8, outline=False), 3)   # glowing ink
    a.ring(66, 0, 9, 7.6, mat('metal', '#ffe38a', glow=0.5), 4)                                    # halo crown
    for k, (u, v) in enumerate(((84, 12), (72, -12), (92, -10))):                                  # floating word strokes
        a.stroke([(u, v), (u + 4, v + 1), (u + 3, v + 4)], 1.3, mat('energy', '#ffd36b', glow=0.9, outline=False), 6)
    a.stroke([(6, 0), (2, -3), (-2, -2)], 2.2, mat('cloth', '#b0335c'), 2)                         # red cord
    a.ell(-3, -2, 2.6, 2.2, mat('cloth', '#d8304a'), 3)

@design('chaos', '万象変転の混沌核', 'staff', half_width=16, grip_u=20, length=24)
def d_chaos(a):
    flesh = mat('dark', '#3a2050')
    a.stroke([(2, 0), (20, 2.5), (40, -2), (60, 2), (72, 0)], 5, flesh, 1, taper=(4.5, 6))
    for k, (u, v, ang) in enumerate(((74, 6, 0.5), (76, -7, -0.6), (88, 9, 0.9), (90, -9, -1.0), (96, 3, 0.2))):
        a.curve((u, v * 0.3), (u + 5, v), (u + 9, v * 1.4), 3, mat('dark', '#4a2a60'), 2, taper=(3, 0.8))
    a.ell(84, 0, 9, 9, mat('dark', '#24142e'), 3)
    a.ell(84, 0, 6, 6, mat('energy', '#ff6fd0', glow=0.6), 4)
    for k, c in enumerate(('#ffe06a', '#69f5f2', '#a0ff8a', '#ff8a6a')):
        ang = k * math.pi / 2 + 0.4
        a.ell(84 + math.cos(ang) * 3, math.sin(ang) * 3, 2.2, 2.2, mat('energy', c, glow=0.8, outline=False), 5)
    for (u, v) in ((30, 4), (52, -4), (66, 3)):
        a.ell(u, v, 2.4, 2.4, mat('cloth', '#f4f0e8'), 3)
        a.dot(u, v, mat('gem', '#69f5f2', glow=0.9), 5, r=0.9)

@design('berit', '万界錬成の籠手', 'gauntlet', half_width=30, grip_u=30, upright_icon=True, length=14)
def d_berit(a):
    black = mat('metal', '#2a2833')
    gold = mat('metal', '#d5a449')
    a.poly([(4, -18), (30, -20), (30, 20), (4, 18)], mat('cloth', '#eeeee9'), 1)                   # cuff (coat sleeve)
    a.poly([(4, -18), (8, -18), (8, 18), (4, 18)], gold, 2)
    for k, c in enumerate(('#6fe3a8', '#e36fb2', '#6fb0e3')):
        a.poly([(12, -14 + k * 9), (24, -14 + k * 9), (24, -10 + k * 9), (12, -10 + k * 9)], mat('gem', c, glow=0.4), 3)
    a.sym([(28, 20), (52, 21), (62, 18)], black, 2)                                                  # back of hand
    for k, v in enumerate((-15, -5, 5, 15)):                                                         # fingers
        L = 30 if k in (1, 2) else 26
        a.poly([(60, v - 4), (60 + L, v - 3.2), (63 + L, v), (60 + L, v + 3.2), (60, v + 4)], black, 3)
        for u in (68, 78):
            a.poly([(u, v - 4), (u + 2, v - 4), (u + 2, v + 4), (u, v + 4)], gold, 4)
        a.dot(60 + L, v, mat('energy', '#ffe08a', glow=0.9), 6, r=1.2)
    a.poly([(40, -26), (56, -22), (58, -20), (44, -23)], black, 2)                                  # thumb
    a.ring(45, 0, 11, 9, mat('metal', '#e2b34c', glow=0.4), 5)                                     # transmutation circle
    a.poly([(45, 0)] + [(45 + 9 * math.cos(t), 9 * math.sin(t)) for t in (0.0, 2.09, 4.19)], mat('energy', '#ffe08a', glow=0.7, outline=False), 5)

@design('elseria', '原初星辰杖', 'staff', half_width=16, grip_u=26, length=30)
def d_elseria(a):
    grip(a, 2, 76, 3.6, mat('wood', '#ece4d4'), 1)
    for u in (12, 30, 48, 66):
        ring_band(a, u, 5, mat('metal', '#c8d8ee'), 2, 2)
    a.curve((74, -2), (86, -14), (98, -6), 3.2, mat('metal', '#e8f0ff'), 3, taper=(3.4, 1))         # crescent
    a.curve((74, 2), (86, 14), (98, 6), 3.2, mat('metal', '#e8f0ff'), 3, taper=(3.4, 1))
    star = []
    for k in range(16):
        ang = 2 * math.pi * k / 16
        r = 9 if k % 2 == 0 else 3.4
        if k % 4 == 0:
            r = 11
        star.append((86 + math.cos(ang) * r, math.sin(ang) * r))
    a.poly(star, mat('gem', '#9fe6ff', glow=0.6), 4)
    a.ell(86, 0, 2.6, 2.6, mat('energy', '#ffffff', glow=1.0, outline=False), 5)
    for s in (-1, 1):
        for k in range(3):
            feather(a, 72, s * 2, s * (1.9 - k * 0.35), 12 - k * 2, 2.2, mat('cloth', '#f6f9ff'), 2)
    for (u, v) in ((96, 12), (100, -10), (90, -15)):
        a.dot(u, v, mat('gem', '#d8f8ff', glow=0.9), 6, r=0.9)

@design('valeria', '万機創匠の変形槌', 'hammer', half_width=20, grip_u=18, length=24)
def d_valeria(a):
    grip(a, 2, 72, 4.6, mat('metal', '#3a3028', pattern='wrap'), 1)
    for u in (8, 60):
        ring_band(a, u, 6.2, mat('metal', '#c8a050'), 2, 3)
    a.poly([(70, -18), (96, -18), (96, 16), (70, 16)], mat('metal', '#7a8088'), 3)                  # head
    a.poly([(72, -20), (94, -20), (94, -17), (72, -17)], mat('metal', '#c8a050'), 4)
    a.poly([(72, 15), (94, 15), (94, 18), (72, 18)], mat('metal', '#c8a050'), 4)
    a.poly([(74, 16), (92, 16), (90, 24), (76, 24)], mat('metal', '#5a6068'), 2)                     # drill side
    a.sym([(76, 0.1), (78, 4), (90, 4), (92, 0.1)], mat('metal', '#8a9098'), 2)
    a.ell(83, -1, 6, 6, mat('energy', '#ffbf5a', glow=0.8), 5)                                      # core
    a.ring(83, -1, 8.5, 6.5, mat('metal', '#c8b080'), 5)
    for (u, v) in ((73, -15), (93, -15), (73, 13), (93, 13)):
        a.dot(u, v, mat('metal', '#f0e0b0'), 6, r=0.7)
    a.poly([(64, -10), (72, -10), (72, -6), (64, -6)], mat('metal', '#b0b6c4'), 2)                  # pistons
    a.poly([(64, 6), (72, 6), (72, 10), (64, 10)], mat('metal', '#b0b6c4'), 2)
    a.poly([(98, -24), (101, -24), (101, -18), (98, -18)], mat('metal', '#5a6068'), 2)              # claw
    a.poly([(96, -24), (101, -28), (101, -24)], mat('metal', '#5a6068'), 2)

@design('huang_linghua', '黄天龍仙槍', 'spear', half_width=12, grip_u=30, length=32)
def d_huang(a):
    grip(a, 2, 78, 3.4, mat('metal', '#23202a'), 1)
    pts = [(10 + k * 3.4, 3.2 * math.sin(k * 0.9)) for k in range(19)]
    a.stroke(pts, 2.2, mat('metal', '#e8c460'), 2)                                                 # coiling dragon
    a.ell(74, 0, 4.5, 4.2, mat('metal', '#d8b754'), 3)                                             # dragon head
    a.poly([(76, -2.5), (82, -1.4), (82, 1.4), (76, 2.5)], mat('metal', '#d8b754'), 3)
    a.dot(74, -1.5, mat('gem', '#ff3a3a', glow=0.8), 6, r=0.6)
    a.sym([(80, 3), (86, 6.5), (94, 4), (101, 0.1)], mat('metal', '#8ad8b0'), 4)                   # jade spearhead
    a.stroke([(82, 0), (99, 0)], 1.0, mat('metal', '#e8c460', outline=False), 5)
    a.ell(79, 0, 2.4, 2.4, mat('gem', '#ffe27a', glow=0.7), 6)
    for s in (-1, 1):                                                                                # red tassels
        a.curve((72, s * 3), (66, s * 9), (58, s * 8), 2.2, mat('cloth', '#d8303a'), 2, taper=(2.6, 1.6))
    a.ell(2, 0, 3, 3, mat('metal', '#d8b754'), 2)

@design('ferdinand', '試作零号魔導連射砲', 'gun', half_width=18, grip_u=30, length=22)
def d_ferdinand(a):
    a.poly([(0, -6), (18, -5), (24, 3), (18, 9), (0, 7)], mat('wood', '#7a4a2a'), 1)               # stock
    a.poly([(22, -9), (60, -9), (60, 7), (22, 7)], mat('metal', '#c8a050'), 2)                     # body
    a.poly([(30, 7), (36, 7), (34, 18), (28, 18)], mat('wood', '#6a3a1a'), 1)                      # pistol grip
    a.ell(40, -2, 6, 6, mat('metal', '#b0b6c4'), 3)                                                # gauge
    a.ell(40, -2, 4, 4, mat('cloth', '#fff8e8'), 4)
    a.stroke([(40, -2), (42.5, -4.5)], 0.9, mat('metal', '#c03040', outline=False), 5)
    a.poly([(50, -13), (58, -13), (58, -9), (50, -9)], mat('gem', '#8bcfe2', glow=0.6), 3)         # battery crystal
    for k, v in enumerate((-6, -2, 2, 6)):                                                          # barrels
        a.poly([(60, v - 1.6), (98, v - 1.6), (98, v + 1.6), (60, v + 1.6)], mat('metal', '#8a9098'), 2 + k % 2)
    for u in (64, 76, 88):
        a.poly([(u, -9.5), (u + 3, -9.5), (u + 3, 9.5), (u, 9.5)], mat('metal', '#c8a050'), 5)
    a.poly([(66, -4), (90, -4), (90, 4), (66, 4)], mat('energy', '#bff0ff', glow=0.6, outline=False), 1)
    for u in (24, 32, 48, 56):
        a.dot(u, -7.5, mat('metal', '#f0e0b0'), 6, r=0.6)

@design('mels', '無形流武の水刃', 'halberd', half_width=14, grip_u=22, length=28)
def d_mels(a):
    water = mat('gem', '#9fe4ff', glow=0.25)
    a.ell(6, 0, 6, 6, mat('gem', '#d8f6ff', glow=0.3), 2)                                          # glass core
    a.ell(6, 0, 2.4, 2.4, mat('energy', '#ffffff', glow=0.9, outline=False), 3)
    a.stroke([(10, 0), (30, 1.4), (50, -1), (72, 0.8)], 3.2, water, 1)
    a.sym([(70, 2), (78, 3), (88, 2), (100, 0.1)], water, 2)                                        # spear tip
    a.poly([(68, 2), (80, 3), (84, 14), (76, 16), (70, 10)], water, 2)                              # axe edge
    a.poly([(66, -2), (74, -3), (72, -9), (66, -7)], water, 2)                                      # back spike
    for (u, v) in ((40, 5), (56, -5), (86, 10)):
        a.ell(u, v, 1.6, 1.6, water, 3)

@design('hephaistos_focus', '分散工廠キューブ', 'cube', half_width=26, grip_u=20, upright_icon=True, length=16)
def d_hephaistos(a):
    grip(a, 4, 34, 6, mat('metal', '#435b71'), 1)
    a.ring(66, 0, 26, 22, mat('metal', '#5a7088'), 2, rv_scale=0.95)                                # gimbal
    a.ring(66, 0, 24, 21.5, mat('energy', '#52e8d6', glow=0.5, outline=False), 3, rv_scale=0.35)
    a.poly([(52, -12), (64, -16), (80, -12), (80, 12), (64, 16), (52, 12)], mat('gem', '#a5f3ff', glow=0.5), 4)   # cube (iso)
    a.poly([(52, -12), (64, -8), (64, 16), (52, 12)], mat('gem', '#6ad8e8', glow=0.4), 5)
    a.poly([(64, -8), (80, -12), (64, -16), (52, -12)], mat('gem', '#e0ffff', glow=0.5), 5)
    for k, ang in enumerate((0.6, 2.3, 4.0)):
        a.ell(66 + math.cos(ang) * 30, math.sin(ang) * 28, 4, 4, mat('metal', '#8aa0b4'), 6)
        a.dot(66 + math.cos(ang) * 30, math.sin(ang) * 28, mat('energy', '#52e8d6', glow=1.0), 7, r=1.0)

@design('nortia', '無法遊戯のピコピコハンマー', 'toy_hammer', half_width=22, grip_u=16, length=20)
def d_nortia(a):
    grip(a, 2, 66, 5, mat('cloth', '#5a6ad8', pattern='stripes'), 1)
    a.poly([(64, -20), (92, -20), (96, -15), (96, 15), (92, 20), (64, 20), (60, 15), (60, -15)], mat('cloth', '#ff8fb0'), 2)
    for v in (-20, 20):
        a.poly([(62, v - 2), (94, v - 2), (94, v + 2), (62, v + 2)], mat('cloth', '#f4d06f'), 3)
    star = [(78 + math.cos(2 * math.pi * k / 10) * (7 if k % 2 == 0 else 3), math.sin(2 * math.pi * k / 10) * (7 if k % 2 == 0 else 3)) for k in range(10)]
    a.poly(star, mat('cloth', '#fff07a'), 4)
    a.poly([(0, -6), (8, -6), (8, 2), (0, 2)], mat('cloth', '#ffffff'), 3)                           # dice keychain
    for (u, v) in ((2, -4), (6, 0), (4, -2)):
        a.dot(u, v, mat('cloth', '#222222'), 5)

@design('lucifara', '失楽堕天の大鎌', 'scythe', half_width=30, grip_u=30, length=30)
def d_lucifara(a):
    grip(a, 2, 88, 3.6, mat('metal', '#1e1826'), 1)
    for u in (20, 60):
        ring_band(a, u, 5, mat('metal', '#c54573'), 2, 2)
    blade = [(86, 2)]
    for k in range(10):
        t = k / 9
        blade.append((96 - 4 * t * t, 2 + t * 34))
    blade += [(91, 34), (86, 20), (84, 8)]
    a.poly(blade, mat('metal', '#241c2c'), 3)
    a.stroke([(96 - 4 * (k / 9) ** 2, 2 + (k / 9) * 34) for k in range(10)], 1.2, mat('energy', '#ff4a7a', glow=0.9, outline=False), 4)
    for k in range(4):
        feather(a, 86, -2, -1.2 - k * 0.3, 14 - k * 2, 2.6, mat('cloth', '#1a1420'), 2)
    a.ell(86, 0, 3.6, 3.2, mat('gem', '#ff3a6a', glow=0.6), 5)
    a.ring(98, -4, 5, 3.8, mat('metal', '#c54573', glow=0.5), 5)

@design('taika', '超克覇王の拳甲', 'gauntlet', half_width=28, grip_u=30, upright_icon=True, length=13)
def d_taika(a):
    a.poly([(2, -16), (34, -18), (34, 18), (2, 16)], mat('metal', '#2a1a24'), 1)
    for u in (8, 20):
        ring_band(a, u, 34, mat('metal', '#e44c49'), 2, 3)
    a.sym([(32, 20), (60, 22), (70, 18)], mat('metal', '#3a2430'), 2)
    for k, v in enumerate((-15, -5, 5, 15)):                                                         # knuckles
        a.ell(74, v, 6, 5, mat('metal', '#5a3a44'), 3)
        a.poly([(76, v - 2), (92, v - 1), (76, v + 2)], mat('metal', '#f0e6d8'), 4)                  # oni spikes
    a.ell(48, 0, 7, 7, mat('gem', '#ff4a3a', glow=0.6), 4)
    for k in range(3):
        a.curve((60 + k * 12, -24), (70 + k * 12, -30), (80 + k * 12, -26), 2.4, mat('energy', '#ff8a4a', glow=0.9, outline=False), 5, taper=(2.6, 0.6))

@design('mary_sue', '次章の英雄譚', 'book', half_width=34, grip_u=40, upright_icon=True, length=14)
def d_mary(a):
    a.poly([(12, -34), (88, -32), (92, 0), (88, 32), (12, 34), (16, 0)], mat('cloth', '#c03040'), 1)    # open covers
    a.poly([(16, -30), (84, -29), (88, -1), (20, -1)], mat('cloth', '#fff8e8'), 2)                    # left page
    a.poly([(20, 1), (88, 1), (84, 29), (16, 30)], mat('cloth', '#fffaf0'), 2)
    for k in range(5):
        u = 30 + k * 10
        a.stroke([(u, -24), (u + 1, -8)], 1.0, mat('energy', '#f2bb5b', glow=0.7, outline=False), 3)
        a.stroke([(u, 8), (u + 1, 24)], 1.0, mat('cloth', '#8a7a6a', outline=False), 3)
    a.poly([(10, -2), (94, -2), (94, 2), (10, 2)], mat('metal', '#f2bb5b'), 4)                        # spine
    a.poly([(4, 6), (14, 6), (14, 10), (4, 12)], mat('cloth', '#2a4aa0'), 1)                          # ribbon
    star = [(70 + math.cos(2 * math.pi * k / 10) * (8 if k % 2 == 0 else 3.4), -16 + math.sin(2 * math.pi * k / 10) * (8 if k % 2 == 0 else 3.4)) for k in range(10)]
    a.poly(star, mat('energy', '#ffe38a', glow=0.9), 5)
    for (u, v) in ((96, 20), (98, -24), (90, 34)):
        a.dot(u, v, mat('gem', '#fff6c0', glow=1.0), 6, r=1.0)

@design('gokuka', '外業呪禍の鉤爪', 'claw', half_width=26, grip_u=20, upright_icon=True, length=14)
def d_gokuka(a):
    a.ell(14, 0, 12, 22, mat('fur', '#4a3a40'), 1)                                                  # fur cuff
    a.sym([(18, 18), (44, 20), (52, 16)], mat('metal', '#2a1a2a'), 2)
    for k, v in enumerate((-13, 0, 13)):
        a.curve((48, v), (76, v + 2), (96, v + 10 + k), 4.6, mat('metal', '#3a2040'), 3, taper=(5, 0.8))
        a.curve((80, v + 3), (90, v + 6), (97, v + 10.5 + k), 2.0, mat('energy', '#e070f0', glow=0.8, outline=False), 4, taper=(2, 0.4))
    a.poly([(24, -14), (40, -16), (40, 16), (24, 14)], mat('dark', '#1e1830', pattern='dots'), 3)    # cursed liquid
    for (u, v) in ((30, -8), (34, 6), (28, 2)):
        a.dot(u, v, mat('energy', ['#c050e0', '#40c0d0', '#e060a0'][int(u) % 3], glow=0.9), 5)
    a.curve((26, 12), (18, 20), (8, 18), 2.4, mat('energy', '#c070e0', glow=0.5), 4, taper=(2.4, 0.8))

@design('merlinus', '魔導深淵の杖', 'staff', half_width=16, grip_u=22, length=28)
def d_merlinus(a):
    a.stroke([(0, 0), (30, 1.2), (60, -1), (78, 0)], 4.2, mat('wood', '#5a3a2a'), 1)
    a.curve((78, 0), (96, -2), (92, 12), 3.6, mat('wood', '#5a3a2a'), 2, taper=(3.6, 2.4))          # crook spiral
    a.curve((92, 12), (86, 16), (84, 9), 2.4, mat('wood', '#5a3a2a'), 2, taper=(2.4, 1.6))
    a.sym([(80, 0.1), (84, 4), (90, 3), (96, 0.1)], mat('gem', '#c8a0ff', glow=0.6), 3)             # crystal
    for k, (r1, r2) in enumerate(((14, 12.6), (10, 8.8))):
        a.ring(86, 0, r1, r2, mat('energy', '#b294ee', glow=0.7, outline=False), 4, rv_scale=0.45 + k * 0.4)
    a.ell(50, -5, 3, 2.4, mat('cloth', '#5a2a1a'), 2)                                              # tiny grimoire charm
    a.stroke([(56, -1), (52, -3)], 0.8, mat('metal', '#e6d070'), 2)

@design('enkou', '深海災牙の三叉戟', 'trident', half_width=16, grip_u=28, length=32)
def d_enkou(a):
    grip(a, 2, 74, 3.8, mat('metal', '#141b28'), 1)
    a.stroke([(8, 0.8), (70, 0.8)], 0.9, mat('energy', '#7fdcff', glow=0.8, outline=False), 2)
    a.poly([(70, -12), (76, -13), (78, 0), (76, 13), (70, 12), (72, 0)], mat('scale', '#1e2a3c'), 3)  # crossbar (jaw)
    for v, L in ((-10, 20), (0, 28), (10, 20)):                                                      # fang prongs
        a.sym([(74, 2.6), (74 + L * 0.6, 2.2), (74 + L, 0.1)], mat('metal', '#e8eef4'), 4) if v == 0 else \
            a.poly([(74, v - 2.2), (74 + L * 0.6, v - 1.6 + v * 0.05), (74 + L, v + v * 0.15), (74 + L * 0.6, v + 1.6 + v * 0.05), (74, v + 2.2)],
                   mat('metal', '#e8eef4'), 4)
    a.ell(73, 0, 3.4, 3.4, mat('gem', '#bff4ff', glow=0.9), 5)                                      # lantern pearl
    for u in (20, 40, 58):
        a.dot(u, -1.2, mat('energy', '#bff4ff', glow=1.0), 5)

@design('kurma', '嶺脈地龍の大槌', 'maul', half_width=22, grip_u=18, length=24)
def d_kurma(a):
    grip(a, 2, 66, 5, mat('wood', '#5a3e28'), 1)
    a.poly([(62, -20), (70, -22), (96, -18), (98, 16), (70, 20), (62, 18)], mat('dark', '#7a7466'), 2)  # rock head
    a.poly([(86, -18), (101, -12), (98, -2), (90, -6)], mat('cloth', '#8a8478'), 3)                     # peaks
    a.poly([(94, -4), (102, 4), (96, 10), (90, 4)], mat('cloth', '#8a8478'), 3)
    a.poly([(98, -14), (101, -12), (99.5, -9)], mat('cloth', '#f2f6fa'), 4)                              # snow caps
    a.poly([(99, 1), (102, 4), (100, 6)], mat('cloth', '#f2f6fa'), 4)
    a.poly([(62, -20), (70, -22), (72, 20), (62, 18)], mat('cloth', '#5e9a3a'), 3)                      # moss band
    a.stroke([(70, -10), (80, -4), (78, 6), (88, 12)], 1.1, mat('energy', '#c8f08a', glow=0.9, outline=False), 4)
    a.poly([(90, 14), (92, 14), (92, 20), (90, 20)], mat('wood', '#5a3e28'), 4)                         # tiny pine
    a.sym([(96, 0.1), (100, 3), (104, 0.1)], mat('cloth', '#3e7a2e'), 4) if False else None

@design('teia', '光越天龍の光弓', 'bow', half_width=24, grip_u=50, upright_icon=True, length=24)
def d_teia(a):
    metal = mat('metal', '#b8c4d8')
    for lo, hi, mid in ((50, 98, 76), (50, 2, 24)):
        a.curve((lo, -3), (mid, -17), (hi, 4), 3.4, metal, 2, taper=(4.2, 1.6))                      # limbs bow backwards
        for k in range(3):                                                                           # photon vanes on the back
            u = lo + (hi - lo) * (0.3 + 0.2 * k)
            t = 0.3 + 0.2 * k
            v = (1 - t) ** 2 * -3 + 2 * (1 - t) * t * -17 + t * t * 4
            feather(a, u, v - 1, -1.9 if hi > lo else -1.25, 9 - k * 2, 2.2, mat('energy', ['#c8ffff', '#ffc8ff', '#fff4b0'][k], glow=0.8), 1)
    a.stroke([(2, 4), (98, 4)], 0.8, mat('energy', '#ffe0ff', glow=1.0, outline=False), 1)            # light string
    a.poly([(44, -5), (56, -5), (56, 1), (44, 1)], mat('metal', '#4a5468', pattern='wrap'), 4)
    a.ell(50, -6, 2.6, 2.6, mat('gem', '#b5ffff', glow=0.9), 5)
    a.stroke([(50, 6), (50, -30)], 1.2, mat('energy', '#ffffff', glow=1.0, outline=False), 6)          # arrow of light
    a.poly([(47.5, -29), (52.5, -29), (50, -36)], mat('energy', '#b5ffff', glow=1.0), 6)

@design('bahamut', '大海皇鯨の法螺貝', 'horn', half_width=26, grip_u=20, upright_icon=True, length=14)
def d_bahamut(a):
    pts = []
    for k in range(14):
        t = k / 13
        pts.append((8 + t * 86, 0))
    a.sym([(6, 3), (20, 9), (46, 18), (70, 22), (88, 18), (98, 6), (100, 0.1)], mat('cloth', '#f4e6dc'), 1)   # conch body
    for k in range(5):
        u = 30 + k * 14
        a.curve((u, -14 + k), (u + 6, 0), (u, 14 - k), 1.4, mat('cloth', '#e0b8b0', outline=False), 2)          # spiral ridges
    a.ell(88, 8, 9, 6, mat('cloth', '#ff9ab0'), 3)                                                   # pink lip
    a.poly([(2, -3), (10, -3), (10, 3), (2, 3)], mat('metal', '#d8b050'), 3)                        # gold mouthpiece
    for k, c in enumerate(('#ff7a8a', '#ffb07a', '#c88aff')):
        a.stroke([(50 + k * 10, -18), (52 + k * 10, -26)], 2.0, mat('cloth', c), 4)                   # coral
    a.curve((60, 20), (80, 30), (96, 22), 1.4, mat('energy', '#9fe8d0', glow=0.9, outline=False), 5)

@design('nun', '天変万化の道化杖', 'marotte', half_width=18, grip_u=24, length=24)
def d_nun(a):
    a.stroke([(0, 0), (40, 1), (66, 0)], 3.6, mat('dark', '#1c1426'), 1)
    for (u, v) in ((22, 2.4), (46, -2.2)):
        a.curve((u, v), (u - 4, v * 2), (u - 8, v * 1.5), 1.6, mat('dark', '#2a1e3a'), 2)            # drips
    a.ell(78, 0, 10, 9, mat('cloth', '#f4f0e8'), 3)                                                  # mask
    for s in (-1, 1):
        a.poly([(78, s * 4), (81, s * 2.4), (78, s * 0.8), (75, s * 2.4)], mat('energy', '#c090ff', glow=0.9), 4)
    a.curve((72, -4), (70, 0), (72, 4), 1.0, mat('cloth', '#2a1a30', outline=False), 4)
    for k, v in enumerate((-9, 0, 9)):                                                              # jester cap points with bells
        a.curve((86, v * 0.6), (96, v * 1.5), (100, v * 2.2), 4, mat('cloth', '#2a2036' if k != 1 else '#7a58b0'), 2, taper=(5, 1.4))
        a.ell(100, v * 2.2, 2.2, 2.2, mat('metal', '#e8d070'), 5)

@design('arcana', '運命流転の糸巻杖', 'staff', half_width=20, grip_u=26, length=28)
def d_arcana(a):
    grip(a, 2, 74, 3.4, mat('metal', '#f4f2ea'), 1)
    a.ell(36, 0, 5, 7, mat('metal', '#dabd72'), 2)                                                  # spindle whorl
    for k in range(9):
        a.stroke([(8 + k * 8, -4), (12 + k * 8, 4)], 0.8, mat('energy', '#ffd76a', glow=0.8, outline=False), 3)  # spiral threads
    for k, ang in enumerate((-0.55, 0.0, 0.55)):                                                     # fanned tarot cards
        cu, cv = 84 + math.cos(ang) * 6, math.sin(ang) * 14
        a.poly([(cu - 8, cv - 5), (cu + 8, cv - 5), (cu + 8, cv + 5), (cu - 8, cv + 5)], mat('cloth', '#f8f0dc'), 3 + k)
        a.poly([(cu - 5, cv - 2.5), (cu + 5, cv - 2.5), (cu + 5, cv + 2.5), (cu - 5, cv + 2.5)], mat('cloth', '#7a5ad8'), 3 + k)
        a.dot(cu, cv, mat('energy', '#ffe9a0', glow=1.0), 6 + k)
    star = [(100 + math.cos(2 * math.pi * k / 8) * (5 if k % 2 == 0 else 2), math.sin(2 * math.pi * k / 8) * (5 if k % 2 == 0 else 2)) for k in range(8)]
    a.poly(star, mat('energy', '#fff6c0', glow=1.0), 9)

@design('eomaia_focus', '原初獣群の角笛', 'horn', half_width=24, grip_u=30, upright_icon=False, length=18)
def d_eomaia(a):
    a.curve((4, 0), (50, 16), (96, 6), 1, mat('cloth', '#f4ecd8'), 1, taper=(5, 15))                 # curved horn
    for u in (26, 52, 76):
        t = u / 100
        a.ring(u, 16 * 2 * t * (1 - t) + 6 * t * t, 3 + t * 6, 2 + t * 5, mat('metal', '#d8b050'), 3, rv_scale=1.2)
    a.ell(96, 6, 3, 8, mat('cloth', '#5a3a22'), 2)                                                  # bell rim
    a.curve((40, 20), (36, 30), (28, 32), 2.4, mat('fur', '#5a3a22'), 2, taper=(3, 1))              # mane tuft
    for k in range(3):
        feather(a, 60 + k * 6, 20, 1.3 + k * 0.2, 12, 2.2, mat('cloth', '#8a6a3a'), 2)
    a.poly([(30, 24), (34, 34), (28, 30)], mat('cloth', '#f0e8d8'), 4)                              # fang charm

@design('demiurgos_focus', '創界の虹宝珠', 'orb', half_width=24, grip_u=18, upright_icon=True, length=14)
def d_demiurgos(a):
    grip(a, 2, 34, 6, mat('scale', '#1b2033'), 1)
    for s in (-1, 0, 1):                                                                             # dragon claw holder
        a.curve((30, s * 6), (44, s * 22 if s else -3), (62, s * 18 if s else -10), 3.6, mat('metal', '#20203a'), 4, taper=(4, 1.2))
    a.ell(62, 0, 20, 20, mat('gem', '#2a1a4a', glow=0.2), 2)                                        # orb with nebula
    for k, c in enumerate(('#ff5f7a', '#5fc8ff', '#ffe95f', '#5fff9b', '#b05fff')):
        ang = k * 1.256
        a.ell(62 + math.cos(ang) * 9, math.sin(ang) * 9, 4, 3, mat('energy', c, glow=0.6, outline=False), 3)
    a.ell(62, 0, 4, 4, mat('energy', '#ffffff', glow=1.0, outline=False), 3)
    a.ell(32, 0, 3, 3, mat('gem', '#ae8ff4', glow=0.7), 5)

@design('hakyoku', '無窮覇帝の捕食砲', 'cannon', half_width=20, grip_u=26, length=24)
def d_hakyoku(a):
    a.poly([(0, -8), (30, -12), (60, -14), (86, -16), (98, -10), (98, 10), (86, 16), (60, 14), (30, 12), (0, 8)], mat('metal', '#211e2e'), 1)
    a.stroke([(8, -2), (30, 4), (50, -4), (72, 6), (90, -2)], 1.3, mat('energy', '#ff627f', glow=0.9, outline=False), 2)   # cracks
    for k in range(6):                                                                               # muzzle jaw teeth
        a.poly([(88, -10 + k * 4), (100, -9 + k * 4), (88, -8 + k * 4)], mat('cloth', '#f2efe6'), 3)
    a.ell(94, 0, 5, 7, mat('energy', '#ff3a6a', glow=0.9), 2)
    for k in range(4):                                                                               # crown spikes
        a.poly([(40 + k * 10, -13), (44 + k * 10, -24 + k), (48 + k * 10, -14)], mat('metal', '#2a2438'), 2)
    a.ell(30, 0, 5, 5, mat('cloth', '#f4f0e8'), 3)                                                  # eye
    a.ell(30, 0, 2.4, 3.4, mat('energy', '#ff3a6a', glow=1.0), 4)
    a.poly([(12, 8), (20, 8), (18, 20), (10, 20)], mat('metal', '#2a2438'), 0)                     # grip

@design('shinra', '天敵の日傘', 'parasol', half_width=16, grip_u=12, length=24)
def d_shinra(a):
    a.curve((10, 0), (2, -2), (2, -8), 3, mat('wood', '#5a3a3a'), 1)                               # crook handle
    grip(a, 8, 30, 3, mat('wood', '#5a3a3a'), 1)
    a.sym([(28, 3), (40, 10), (66, 12), (86, 6), (92, 0.1)], mat('cloth', '#f3eadf'), 2)            # folded canopy
    for k in range(4):
        a.stroke([(32 + k * 4, -8 + k * 5), (86, -1 + k)], 0.9, mat('cloth', '#bb5476', outline=False), 3)
    a.sym([(30, 11), (36, 13), (40, 11)], mat('cloth', '#ffffff'), 3)                                # frill
    a.sym([(92, 1.8), (100, 0.1)], mat('metal', '#e8eef0'), 4)                                       # hidden blade tip
    a.ell(26, -8, 5, 5, mat('cloth', '#d8304a'), 4)                                                 # camellia
    a.dot(26, -8, mat('gem', '#ffe070', glow=0.6), 5, r=1.2)
    a.curve((26, 4), (20, 10), (14, 9), 1.6, mat('cloth', '#bb5476'), 3)                            # ribbon

@design('ain_sof_aur_focus', '並行世界の星鏡', 'mirror', half_width=30, grip_u=14, upright_icon=True, length=14)
def d_ain(a):
    grip(a, 2, 30, 5, mat('metal', '#e8e0ff'), 1)
    for s in (-1, 1):                                                                                # branching frame
        a.curve((30, s * 3), (40, s * 22), (66, s * 26), 2.6, mat('metal', '#a791ee'), 2)
        a.curve((44, s * 18), (46, s * 28), (56, s * 30), 1.6, mat('metal', '#a791ee'), 2)
        a.curve((70, s * 24), (84, s * 28), (90, s * 20), 1.6, mat('metal', '#a791ee'), 2)
    a.ell(62, 0, 24, 22, mat('metal', '#c8b8ff'), 3)
    a.ell(62, 0, 20, 18, mat('gem', '#1a1838', glow=0.2), 4)                                        # mirror face: starry
    for (u, v) in ((56, -8), (70, 6), (64, -2), (52, 10), (74, -10)):
        a.dot(u, v, mat('energy', '#ffffff', glow=1.0), 5)
    a.stroke([(46, -10), (78, 12)], 1.2, mat('energy', '#cbbcff', glow=0.6, outline=False), 5)      # reflection glint
    a.poly([(88, -7), (94, -9), (92, -4), (96, 0), (92, 4), (94, 9), (88, 7)], mat('energy', '#cbbcff', glow=0.8), 6)  # floating crown

@design('angra_mainyu', '全害惡徳の影鎖鎌', 'kusarigama', half_width=26, grip_u=14, length=22)
def d_angra(a):
    grip(a, 2, 46, 4.4, mat('cloth', '#141018', pattern='wrap'), 1)
    a.poly([(44, -4), (52, -5), (52, 5), (44, 4)], mat('metal', '#1c1822'), 2)
    blade = [(50, 3)] + [(52 + 30 * math.sin(t), 4 + 26 * (1 - math.cos(t))) for t in np.linspace(0.1, 1.35, 9)] + [(70, 22), (58, 6)]
    a.poly(blade, mat('metal', '#1e1826'), 3)
    a.stroke([(52 + 30 * math.sin(t), 4 + 26 * (1 - math.cos(t)) - 1.2) for t in np.linspace(0.15, 1.3, 9)], 1.0,
             mat('energy', '#c0303a', glow=0.9, outline=False), 4)
    chain_links(a, [(0 - k * 3, -4 - k * 3.4) for k in range(1)] + [(4 + k * 6, -8 - k * 2.2) for k in range(6)], mat('metal', '#5a5070'), 2)
    a.ell(42, -24, 5, 5, mat('metal', '#2a2030'), 3)                                                # weight
    a.ell(42, -24, 2.2, 2.2, mat('gem', '#c0303a', glow=0.8), 4)
    for k in range(6):
        ang = k * 1.047
        a.poly([(42 + math.cos(ang) * 4.5, -24 + math.sin(ang) * 4.5), (42 + math.cos(ang) * 8, -24 + math.sin(ang) * 8),
                (42 + math.cos(ang + 0.4) * 4.5, -24 + math.sin(ang + 0.4) * 4.5)], mat('metal', '#3a3040'), 2)

@design('magna_mater_focus', '始源生命の種杖', 'staff', half_width=18, grip_u=24, length=28)
def d_magna(a):
    a.stroke([(0, 0), (30, 1.5), (56, -1.2), (76, 0.6)], 4.4, mat('wood', '#6a5038'), 1)
    a.stroke([(10, 2), (24, -2.4), (40, 2.6), (56, -2.2), (70, 2)], 1.4, mat('cloth', '#5a8a40'), 2)  # vine
    for (u, v, ang) in ((20, 3, 0.8), (38, -3, -0.9), (54, 3, 0.7), (70, -3, -0.8)):
        feather(a, u, v, ang, 9, 2.6, mat('cloth', '#7ab050'), 3)                                    # leaves
    for s in (-1, 1):
        feather(a, 76, s * 2, s * 0.9, 16, 4.5, mat('cloth', '#6aa04a'), 2)                          # cradling leaves
    a.ell(86, 0, 9, 7.5, mat('gem', '#fff0c8', glow=0.6), 3)                                         # seed / egg of life
    a.ell(86, 0, 4, 3, mat('energy', '#ffe0f0', glow=1.0, outline=False), 4)
    for (u, v, c) in ((96, 9, '#ff9ab8'), (96, -9, '#ffffff'), (100, 0, '#fff0a0')):
        a.ell(u, v, 3, 3, mat('cloth', c), 5)
        a.dot(u, v, mat('gem', '#ffe070', glow=0.7), 6)

@design('ouroboros', '無限円環の輪刃', 'chakram', half_width=34, grip_u=50, upright_icon=True, length=16)
def d_ouroboros(a):
    a.ring(50, 0, 46, 34, mat('metal', '#c8d4ec'), 1)                                                # blade ring
    for k in range(16):                                                                              # outer serrations
        ang = 2 * math.pi * k / 16
        a.poly([(50 + math.cos(ang) * 45, math.sin(ang) * 45), (50 + math.cos(ang + 0.12) * 52, math.sin(ang + 0.12) * 52),
                (50 + math.cos(ang + 0.3) * 45, math.sin(ang + 0.3) * 45)], mat('metal', '#e0e8f8'), 1)
    a.ring(50, 0, 38, 35, mat('scale', '#dfb971'), 2)                                                # serpent
    a.ell(50 + 38, -4, 5, 4, mat('scale', '#dfb971'), 3)
    a.dot(50 + 39, -5, mat('gem', '#ff3a3a', glow=0.8), 4)
    for k in range(12):                                                                              # clock numerals
        ang = 2 * math.pi * k / 12
        a.dot(50 + math.cos(ang) * 41, math.sin(ang) * 41, mat('energy', '#8ab0e8', glow=0.9), 4, r=0.8)
    a.poly([(46, -34), (54, -34), (54, 34), (46, 34)], mat('cloth', '#2a3246', pattern='wrap'), 2)    # cross grip
    a.ell(50, 0, 6, 6, mat('gem', '#dfb971', glow=0.5), 3)

@design('yggdrasil', '玖天神樹の若枝', 'wand', half_width=18, grip_u=20, length=24)
def d_yggdrasil(a):
    a.stroke([(0, 0), (26, 1.6), (52, -1.4), (72, 1), (88, -1)], 1, mat('wood', '#8a6a48'), 1, taper=(5, 2))
    a.curve((52, -1), (62, -10), (74, -14), 2, mat('wood', '#8a6a48'), 1, taper=(2.4, 1))           # side twigs
    a.curve((64, 1), (74, 10), (86, 12), 2, mat('wood', '#8a6a48'), 1, taper=(2.4, 1))
    a.stroke([(10, 0.4), (40, 0.2), (70, 0.6)], 0.9, mat('energy', '#d8ff8a', glow=0.9, outline=False), 2)
    for (u, v, ang) in ((40, 3, 0.8), (58, -4, -0.9), (80, 3, 0.6), (92, -2, -0.4)):
        feather(a, u, v, ang, 8, 2.4, mat('cloth', '#7ab050'), 3)
    worlds = ['#ffd06a', '#8ad0ff', '#ff8aa8', '#a0ff8a', '#d0a0ff', '#ffffff', '#ff9a50', '#60e0d0', '#f0f080']
    spots = [(74, -14), (86, 12), (90, -1), (66, -8), (80, 8), (96, 4), (60, 6), (82, -8), (98, -5)]
    for (u, v), c in zip(spots, worlds):
        a.ell(u, v, 2.2, 2.2, mat('gem', c, glow=0.7), 4)

@design('miyohime', '万律自在の神楽鈴', 'bell', half_width=22, grip_u=14, length=20)
def d_miyohime(a):
    grip(a, 2, 46, 4, mat('cloth', '#f8f4fc', pattern='wrap'), 1)
    for s in (-1, 1):                                                                                # five-colour streamers
        for k, c in enumerate(('#c02a4a', '#ffffff', '#ba84f0', '#ffe07a', '#7ffff0')):
            a.curve((14, s * 2), (6 - k * 2, s * (8 + k * 2)), (-4 + k, s * (10 + k * 3)), 1.4, mat('cloth', c), 2)
    a.ring(70, 0, 24, 21, mat('energy', '#ffffff', glow=0.6, outline=False), 1)                      # geometric halo
    for k in range(7):
        ang = 2 * math.pi * k / 7
        a.stroke([(70 + math.cos(ang) * 22, math.sin(ang) * 22), (70 + math.cos(ang + 2 * math.pi * 2 / 7) * 22, math.sin(ang + 2 * math.pi * 2 / 7) * 22)],
                 0.8, mat('energy', ['#ff7fd0', '#7ffff0', '#ffe07a', '#ba84f0', '#7fff9a', '#ff9a50', '#7fb0ff'][k], glow=0.8, outline=False), 2)
    for tier, (u, n, r) in enumerate(((52, 2, 4.5), (64, 3, 4.2), (76, 4, 4.0), (88, 3, 3.8))):      # bell tiers
        for k in range(n):
            v = (k - (n - 1) / 2) * 9
            a.ell(u, v, r, r, mat('metal', '#e8c050'), 4 + tier)
            a.dot(u + 1.4, v, mat('metal', '#5a4020'), 5 + tier)
    a.poly([(48, -1.2), (96, -1.2), (96, 1.2), (48, 1.2)], mat('metal', '#c8a040'), 3)

@design('innocence', '無垢なる全能のぬいぐるみ', 'plush', half_width=26, grip_u=20, upright_icon=True, length=12)
def d_innocence(a):
    a.ell(36, 0, 22, 18, mat('cloth', '#f6f6ff'), 1)                                                 # body
    a.ell(72, 0, 20, 20, mat('cloth', '#f6f6ff'), 2)                                                 # head
    for s in (-1, 1):
        a.ell(90, s * 14, 7, 6, mat('cloth', '#f6f6ff'), 1)                                          # ears
        a.ell(90, s * 14, 4, 3, mat('cloth', '#e8c8ff'), 2)
        a.ell(30, s * 20, 8, 6, mat('cloth', '#eeeeff'), 0)                                          # arms
    a.ell(74, -7, 3.2, 3.2, mat('gem', '#6a8aff', glow=0.6), 3)                                      # button eyes (blue / gold)
    a.ell(74, 7, 3.2, 3.2, mat('gem', '#ffd76a', glow=0.6), 3)
    a.curve((64, -5), (60, 0), (64, 5), 1.0, mat('cloth', '#6a4a8a', outline=False), 3)              # stitched smile
    for k in range(4):
        a.stroke([(34 + k * 4, -6), (36 + k * 4, 6)], 0.7, mat('cloth', '#c993ff', outline=False), 3)   # belly stitches
    a.poly([(54, -14), (58, -6), (58, 6), (54, 14), (52, 0)], mat('cloth', '#c993ff'), 3)            # bow
    a.ring(98, 0, 8, 6.4, mat('energy', '#d8b8ff', glow=0.7, outline=False), 4, rv_scale=0.4)       # tiny halo

@design('brutality_focus', '抗理粉砕の鋼手甲', 'gauntlet', half_width=30, grip_u=30, upright_icon=True, length=14)
def d_brutality(a):
    a.poly([(2, -18), (36, -22), (36, 22), (2, 18)], mat('metal', '#4a4048'), 1)
    for u in (8, 22):
        ring_band(a, u, 40, mat('metal', '#7a6a5a'), 2, 3)
    a.sym([(34, 24), (62, 26), (74, 22)], mat('metal', '#5a5054'), 2)
    for k, v in enumerate((-18, -6, 6, 18)):
        a.ell(78, v, 7, 6, mat('metal', '#7a7074'), 3)
        a.poly([(82, v - 3), (98, v), (82, v + 3)], mat('metal', '#9a9098'), 4)
    for (u, v) in ((50, -10), (60, 8), (70, -4)):                                                    # blood
        a.ell(u, v, 3, 2, mat('cloth', '#8a2a1a'), 4)
    chain_links(a, [(12 + k * 5, 24 + (k % 2)) for k in range(5)], mat('metal', '#7a6a5a'), 3)

@design('cursed_love', '悲劇の操り人形', 'marionette', half_width=24, grip_u=86, upright_icon=True, length=16)
def d_cursed(a):
    a.poly([(92, -22), (96, -22), (96, 22), (92, 22)], mat('wood', '#5a3a2a'), 4)                    # control bar (top)
    a.poly([(80, -2), (100, -2), (100, 2), (80, 2)], mat('wood', '#5a3a2a'), 4)
    for v in (-20, -8, 8, 20):
        a.stroke([(94, v), (52 if abs(v) > 10 else 70, v * 0.6)], 0.6, mat('cloth', '#e0d0e8', outline=False), 1)
    a.ell(64, 0, 8, 7, mat('cloth', '#faeceb'), 3)                                                   # doll head
    a.poly([(70, -9), (74, -7), (74, 7), (70, 9), (56, 10), (56, -10)], mat('cloth', '#1b1724'), 2)  # long black hair
    a.dot(64, -3, mat('gem', '#8a1838', glow=0.5), 5)
    a.dot(64, 3, mat('gem', '#8a1838', glow=0.5), 5)
    a.sym([(56, 6), (40, 12), (24, 14), (22, 0.1)], mat('cloth', '#351f36'), 2)                       # dress
    a.poly([(30, -6), (36, -3), (30, 0)], mat('cloth', '#aa4b71'), 4)
    for s in (-1, 1):
        a.stroke([(54, s * 6), (44, s * 16)], 1.6, mat('cloth', '#faeceb'), 3)                          # arms
    a.ell(84, 18, 4, 4, mat('cloth', '#7a1030'), 5)                                                   # roses on the bar
    a.ell(84, -18, 4, 4, mat('cloth', '#7a1030'), 5)

@design('relentless_research', '救済実験の大注射器', 'syringe', half_width=12, grip_u=14, length=24)
def d_research(a):
    a.poly([(0, -9), (4, -9), (4, 9), (0, 9)], mat('metal', '#c8d0d4'), 2)                          # thumb rest
    a.poly([(4, -1.6), (22, -1.6), (22, 1.6), (4, 1.6)], mat('metal', '#c8d0d4'), 1)               # plunger rod
    a.poly([(20, -10), (24, -10), (24, 10), (20, 10)], mat('metal', '#e8eef0'), 3)                  # flange
    a.poly([(24, -6), (78, -6), (78, 6), (24, 6)], mat('gem', '#e0fff4', glow=0.15), 2)             # glass barrel
    a.poly([(40, -4.6), (77, -4.6), (77, 4.6), (40, 4.6)], mat('energy', '#8bdbc7', glow=0.7), 3)   # serum
    for u in range(30, 78, 6):
        a.stroke([(u, -6), (u, -3.4)], 0.6, mat('cloth', '#4a8a7a', outline=False), 4)                 # graduations
    a.poly([(78, -3.4), (84, -2), (84, 2), (78, 3.4)], mat('metal', '#c8d0d4'), 3)
    a.poly([(84, -0.7), (101, -0.3), (101, 0.3), (84, 0.7)], mat('metal', '#f4f8f8'), 3)            # needle
    a.dot(60, 1.5, mat('energy', '#ffffff', glow=0.9), 5)

@design('forbidden_arcana_focus', '外悪魔導の寄生書', 'grimoire', half_width=30, grip_u=40, upright_icon=True, length=13)
def d_forbidden(a):
    a.poly([(10, -26), (92, -26), (92, 26), (10, 26)], mat('cloth', '#281f48'), 1)                  # cover
    a.poly([(10, 22), (92, 22), (92, 28), (10, 28)], mat('cloth', '#e8e0c8'), 0)                    # page edge
    for (u, v) in ((10, -26), (92, -26), (10, 26), (92, 26)):
        a.poly([(u - 3, v - 3), (u + 3, v - 3), (u + 3, v + 3), (u - 3, v + 3)], mat('metal', '#8a80a8'), 3)   # corners
    for u in (30, 70):                                                                               # chains across
        chain_links(a, [(u + (k % 2), -26 + k * 6.5) for k in range(9)], mat('metal', '#5a5070'), 4)
    a.ell(50, 0, 12, 8, mat('cloth', '#f4f0e8'), 3)                                                  # eye
    a.ell(50, 0, 6, 6, mat('energy', '#a883ee', glow=0.9), 4)
    a.ell(50, 0, 2, 4, mat('dark', '#05040a'), 5)
    a.poly([(44, 22), (56, 22), (56, 32), (44, 32)], mat('metal', '#d8b050'), 5)                     # padlock
    for (u, v) in ((22, -14), (80, 12), (24, 16), (82, -16)):
        a.dot(u, v, mat('energy', '#a883ee', glow=1.0), 5, r=0.8)

@design('fallen_savior', '救堕の古聖剣', 'sword', half_width=12, grip_u=10, length=24)
def d_fallen(a):
    a.sym([(28, 3.6), (84, 3.0), (96, 1.4), (101, 0.1)], mat('metal', '#e8ecf4'), 3)                # blade
    a.stroke([(30, 0), (88, 0)], 1.2, mat('energy', '#fff6b0', glow=0.5, outline=False), 4)          # faint light in the fuller
    a.sym([(22, 3), (24, 12), (27, 13), (28, 3)], mat('metal', '#b8a868'), 5)                        # worn gold guard
    a.ell(25, 0, 3, 3, mat('gem', '#9fd8ff', glow=0.5), 6)
    grip(a, 5, 22, 4.2, mat('cloth', '#3a3a6a', pattern='wrap'), 2)
    a.ell(3, 0, 3.6, 3.6, mat('metal', '#b8a868'), 3)
    a.stroke([(8, 2), (2, 6), (-2, 5)], 1.4, mat('cloth', '#e8e0c8'), 1)                             # faded cloth tail

@design('sweet_pact', '未来債権の天秤', 'scales', half_width=32, grip_u=10, upright_icon=True, length=14)
def d_sweet(a):
    grip(a, 2, 70, 4, mat('metal', '#d8b175'), 1)
    a.ell(72, 0, 4, 4, mat('gem', '#ffcf6a', glow=0.6), 4)
    a.poly([(68, -32), (72, -32), (72, 32), (68, 32)], mat('metal', '#d8b175'), 3)                  # beam
    for s in (-1, 1):
        for d in (-6, 6):
            a.stroke([(70, s * 30), (40, s * 30 + d)], 0.6, mat('metal', '#c8a060', outline=False), 2)  # chains
        a.sym([(36, 0.1), (38, 9), (42, 11)], dict(mat('metal', '#e8c060'), ), 3) if False else None
        a.poly([(42, s * 30 - 10), (42, s * 30 + 10), (36, s * 30 + 7), (34, s * 30), (36, s * 30 - 7)], mat('metal', '#e8c060'), 3)  # pans
    for k in range(3):                                                                               # coins on one pan
        a.ell(45 + k * 2.4, -30 + (k - 1) * 4, 2.4, 2.4, mat('metal', '#ffd76a'), 4)
    a.ell(46, 30, 4, 3.4, mat('gem', '#ff5a7a', glow=0.5), 4)                                        # heart / future on the other
    a.poly([(2, 8), (20, 8), (18, 26), (4, 26)], mat('cloth', '#f6ead0'), 0)                          # contract scroll
    a.ell(12, 18, 3, 3, mat('cloth', '#c03040'), 1)


@design('tenki', '唯我の王剣', 'greatsword', half_width=16, grip_u=10, length=27)
def d_tenki_sword(a):
    a.sym([(26, 6.5), (40, 7.5), (78, 6.2), (92, 3.2), (101, 0.1)], mat('metal', '#f6f2e8'), 3)              # broad royal blade
    a.sym([(30, 2.2), (86, 1.4), (92, 0.1)], mat('metal', '#e8b83e'), 4)                                     # gilded fuller
    a.stroke([(32, 0), (84, 0)], 0.8, mat('energy', '#fff2b0', glow=0.8, outline=False), 5)
    for k in range(10):                                                                                      # sunburst guard
        ang = math.pi * (k / 9) - math.pi / 2
        a.poly([(24, 0), (24 + math.cos(ang) * 4 + 6, math.sin(ang) * 15), (24 + math.cos(ang + 0.15) * 3 + 5, math.sin(ang + 0.15) * 13)],
               mat('metal', '#ffd76a', glow=0.3), 2)
    a.sym([(20, 4), (24, 15), (28, 13), (28, 4)], mat('metal', '#e2b33e'), 5)
    a.ell(24, 0, 4.2, 4.2, mat('gem', '#9fd8ff', glow=0.6), 6)
    grip(a, 4, 20, 4.4, mat('cloth', '#fffaee', pattern='wrap'), 2)
    a.sym([(0, 3), (2, 6), (5, 4.5), (6, 2)], mat('metal', '#e2b33e'), 3)                                    # crown pommel
    for v in (-4, 0, 4):
        a.dot(-0.5, v, mat('gem', '#ffffff', glow=0.7), 5)

@design('demiurgos', '空想現実の黒龍剣', 'greatsword', half_width=16, grip_u=10, length=27)
def d_demiurgos_sword(a):
    a.sym([(24, 7), (50, 8.5), (82, 6), (94, 3), (101, 0.1)], mat('scale', '#1b2033'), 3)                    # black scale blade
    for k in range(7):                                                                                       # serrated spines
        u = 30 + k * 9
        a.poly([(u, 7.5 - k * 0.2), (u + 4, 11 - k * 0.3), (u + 6, 7 - k * 0.2)], mat('scale', '#2a3048'), 2)
    for k, c in enumerate(('#ff5f7a', '#5fc8ff', '#ffe95f', '#5fff9b', '#b05fff', '#ff9f4f')):
        a.ell(32 + k * 10, (-1) ** k * 2.2, 2, 2, mat('gem', c, glow=0.8), 5)                                  # embedded rainbow gems
    for s in (-1, 1):                                                                                        # membrane wing guard
        a.poly([(20, s * 4), (30, s * 18), (24, s * 14), (22, s * 20), (16, s * 10)], mat('cloth', '#2c2648'), 2)
        a.stroke([(20, s * 4), (30, s * 18)], 1.0, mat('metal', '#ae8ff4', glow=0.4), 3)
    grip(a, 4, 20, 4.4, mat('scale', '#10141f'), 2)
    a.ell(2, 0, 3.6, 3.6, mat('gem', '#ae8ff4', glow=0.8), 3)

@design('hephaistos', '概念加工の切削槍', 'drill_lance', half_width=14, grip_u=22, length=30)
def d_hephaistos_lance(a):
    grip(a, 2, 44, 4.4, mat('metal', '#435b71', pattern='wrap'), 1)
    a.sym([(40, 9), (46, 11), (52, 9)], mat('metal', '#5a7088'), 2)                                          # vamplate
    a.ell(46, 0, 4, 4, mat('gem', '#a5f3ff', glow=0.7), 4)
    pts = [(52, 8), (100, 0.1)]
    a.sym([(52, 8), (64, 7), (100, 0.1)], mat('metal', '#8aa0b4'), 3)                                         # drill cone
    for k in range(9):                                                                                       # helical grooves
        u = 54 + k * 5
        w = 8 * (1 - (u - 52) / 48)
        a.stroke([(u, -w), (u + 4, w)], 1.0, mat('energy', '#52e8d6', glow=0.8, outline=False), 4)
    a.ring(70, 0, 12, 10, mat('energy', '#52e8d6', glow=0.6, outline=False), 5, rv_scale=0.3)
    for k in range(3):
        a.ell(30 - k * 10, (-1) ** k * 6, 2.4, 2.4, mat('metal', '#8aa0b4'), 4)                               # orbiting foundry bits
        a.dot(30 - k * 10, (-1) ** k * 6, mat('energy', '#52e8d6', glow=1.0), 5)

@design('ain_sof_aur', '分岐確定の王剣', 'sword', half_width=14, grip_u=10, length=26)
def d_ain_sword(a):
    a.sym([(26, 4.5), (60, 4), (66, 2)], mat('metal', '#f3ecfa'), 3)
    for ang, L in ((-0.32, 26), (0.0, 36), (0.32, 26)):                                                      # branching tines
        du, dv = math.cos(ang), math.sin(ang)
        a.poly([(64, -2 + dv * 2), (64 + du * L * 0.6, dv * L * 0.6 - 1.8), (64 + du * L, dv * L), (64 + du * L * 0.6, dv * L * 0.6 + 1.8), (64, 2 + dv * 2)],
               mat('metal', '#f3ecfa'), 3)
        a.stroke([(66, dv * 2), (62 + du * L * 0.9, dv * L * 0.9)], 0.7, mat('energy', '#cbbcff', glow=0.9, outline=False), 4)
    a.stroke([(28, 0), (62, 0)], 0.8, mat('energy', '#a791ee', glow=0.8, outline=False), 4)
    a.sym([(20, 3), (23, 12), (26, 10), (27, 3)], mat('metal', '#e8e0ff'), 5)
    a.ell(24, 0, 3.4, 3.4, mat('gem', '#a791ee', glow=0.7), 6)
    a.poly([(30, -10), (36, -12), (34, -7), (38, -4), (34, -2), (36, 2), (30, 0)], mat('energy', '#cbbcff', glow=0.8), 6) if False else None
    grip(a, 4, 20, 4.2, mat('cloth', '#f3ecfa', pattern='wrap'), 2)
    a.ell(2, 0, 3.2, 3.2, mat('metal', '#cbbcff'), 3)
    for k, ang in enumerate((-0.8, 0.0, 0.8)):                                                              # floating crown points
        a.poly([(44 + math.cos(ang) * 3, 12 + k * 0.5), (48, 13 + k), (44, 15 + k * 0.5)], mat('energy', '#cbbcff', glow=0.9), 6)

@design('brutality', '凄惨暴虐の鬼金棒', 'club', half_width=14, grip_u=12, length=26)
def d_brutality_club(a):
    grip(a, 2, 30, 4.6, mat('cloth', '#3a2a20', pattern='wrap'), 1)
    a.sym([(28, 5), (40, 8.5), (94, 9.5), (100, 7), (101, 0.1)], mat('metal', '#4a4048'), 2)                # iron kanabo
    for row in range(8):                                                                                     # studs
        u = 42 + row * 7
        for v in (-6, 0, 6):
            a.ell(u + (v != 0) * 3, v, 1.8, 1.8, mat('metal', '#9a9098'), 3)
    a.ring(36, 0, 6, 4.4, mat('metal', '#7a6a5a'), 3, rv_scale=1.6)
    for (u, v) in ((60, -4), (78, 5), (88, -2)):
        a.ell(u, v, 2.6, 1.8, mat('cloth', '#8a2a1a'), 4)
    a.ell(2, 0, 3.4, 3.4, mat('metal', '#7a6a5a'), 2)
    for k in range(3):
        a.ring(-2 - k * 3, 3 + k * 2, 1.6, 0.7, mat('metal', '#7a6a5a'), 2)

@design('forbidden_arcana', '禁理術式の鎖刃', 'chain_blade', half_width=16, grip_u=10, length=26)
def d_forbidden_chain(a):
    grip(a, 2, 18, 4, mat('void' if False else 'dark', '#151229'), 1)
    a.ell(2, 0, 3, 3, mat('energy', '#a883ee', glow=0.8), 2)
    prev = (18, 0)
    for k in range(8):                                                                                       # glyph blade segments on a chain
        u = 22 + k * 10
        v = 4 * math.sin(k * 0.8)
        a.stroke([prev, (u, v)], 0.9, mat('metal', '#5a5070'), 1)
        a.poly([(u - 4, v - 3.5), (u + 4, v - 2), (u + 6, v), (u + 4, v + 2), (u - 4, v + 3.5)], mat('cloth', '#281f48'), 2)
        a.stroke([(u - 2, v - 1), (u + 1, v + 1), (u + 3, v - 1)], 0.8, mat('energy', '#a883ee', glow=1.0, outline=False), 3)
        prev = (u + 6, v)
    a.poly([(96, -3), (104, 0), (96, 3)], mat('energy', '#d8c8ff', glow=1.0), 3)

@design('eomaia', '始祖神獣の角牙薙刀', 'naginata', half_width=16, grip_u=26, length=30)
def d_eomaia_glaive(a):
    grip(a, 2, 70, 3.8, mat('wood', '#7a5a34'), 1)
    for u in (12, 40, 64):
        a.ring(u, 0, 3.2, 2, mat('fur', '#5a3a22'), 2, rv_scale=1.4)
    a.curve((68, 0), (88, -4), (101, 6), 1, mat('cloth', '#f4ecd8'), 3, taper=(9, 1.5))                   # fang blade
    a.stroke([(72, -1), (96, 4)], 0.8, mat('cloth', '#c8a060', outline=False), 4)
    for s in (-1, 1):                                                                                        # antler crossguard
        a.curve((66, s * 2), (66, s * 12), (74, s * 16), 2.2, mat('cloth', '#efe4c8'), 2, taper=(2.6, 1))
        a.curve((66, s * 9), (60, s * 13), (58, s * 18), 1.6, mat('cloth', '#efe4c8'), 2, taper=(2, 0.8))
        a.dot(74, s * 16, mat('energy', '#ffe9a0', glow=1.0), 4)
    a.curve((64, 3), (56, 10), (50, 9), 2.6, mat('fur', '#5a3a22'), 2, taper=(3, 1.2))                     # mane tuft
    feather(a, 62, -3, -2.3, 10, 2.2, mat('cloth', '#8a6a3a'), 2)

@design('magna_mater', '命を継ぐ蔓鞭', 'whip', half_width=26, grip_u=8, length=24)
def d_magna_whip(a):
    grip(a, 2, 18, 4.4, mat('wood', '#6a5038'), 1)
    a.ell(20, 0, 4, 5, mat('cloth', '#ff9ab8'), 2)                                                          # blossom guard
    a.ell(20, 0, 1.6, 1.6, mat('gem', '#fff0a0', glow=0.7), 3)
    pts = [(22 + k * 6, 14 * math.sin(k * 0.55) * (k / 13)) for k in range(14)]
    a.stroke(pts, 1, mat('cloth', '#5a8a40'), 1, taper=(3.2, 1.0))                                         # vine lash
    for k in range(2, 13, 2):
        u, v = pts[k]
        feather(a, u, v, 0.9 if k % 4 else -0.9, 6, 1.8, mat('cloth', '#7ab050'), 2)
        if k % 4 == 0:
            a.dot(u, v - 2, mat('gem', '#ffe0f0', glow=0.8), 3)
    a.poly([(pts[-1][0], pts[-1][1] - 2), (pts[-1][0] + 6, pts[-1][1]), (pts[-1][0], pts[-1][1] + 2)], mat('horn' if False else 'cloth', '#c8e090'), 2)

# ------------------------------------------------------------------------------------- output
def render_icon(name, size=32):
    d = DESIGNS[name]
    fr = icon_frame(size, upright=d['upright_icon'])
    a = Art(fr)
    d['fn'](a)
    return a.render()

def render_sprite(name, px_per_unit=3):
    """Large upright sprite: px_per_unit texels per model unit (the prop bone is scaled 1/px_per_unit)."""
    d = DESIGNS[name]
    L = d['length'] * px_per_unit
    fr = sprite_frame(L, d['half_width'])
    a = Art(fr)
    d['fn'](a)
    return a.render(), fr

def to_image(rgba):
    return Image.fromarray(rgba, 'RGBA')

if __name__ == '__main__':
    import sys
    from PIL import ImageDraw
    names = sys.argv[2:] or list(DESIGNS)
    tiles = []
    for n in names:
        icon, _ = render_icon(n)
        (spr, glow), fr = render_sprite(n)
        tiles.append((n, to_image(icon).resize((128, 128), Image.NEAREST), to_image(spr)))
    W = sum(max(132, t[2].width * 2 + 4) for t in tiles) + 10
    H = 140 + max(t[2].height * 2 for t in tiles) + 10
    img = Image.new('RGBA', (W, H), (40, 42, 52, 255))
    d = ImageDraw.Draw(img)
    x = 6
    for n, ic, sp in tiles:
        img.paste(ic, (x, 6), ic)
        sp2 = sp.resize((sp.width * 2, sp.height * 2), Image.NEAREST)
        img.paste(sp2, (x, 140), sp2)
        d.text((x, 130), n, fill=(255, 255, 255, 255))
        x += max(132, sp2.width + 4)
    img.save(sys.argv[1])

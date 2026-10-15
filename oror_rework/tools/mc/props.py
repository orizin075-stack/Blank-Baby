"""Ornate hand-held weapons. Every prop is modelled at double resolution (FINE units) inside a
half-scaled bone at the palm, so guards, wraps, gems, runes and filigree get twice the texel density
of the body. Blades are flat in the YZ plane (edge towards -Z, flats facing +-X) and point up (-Y)
from the grip; the prop bone's rotation aims them. Each character's relic weapon is built from these
parts in WEAPONS below."""
import math
from paint import M

F = 2                                   # fine units per model unit inside a prop bone

POINT_FORWARD = (1.25, 0.0, 0.0)        # vanilla-like hold: blade forward and a little up
POINT_DOWN = (2.9, 0.0, 0.0)            # reverse grip / lowered blade
UPRIGHT = (0.12, 0.0, 0.0)

def upright(side, lean=0.28):
    return (0.12, 0.0, -lean if side == 'r' else lean)

def hand(h, side='r', rot=(0.0, 0.0, 0.0)):
    """Plain (full-scale) bone at the palm, for small held items."""
    fore = h.fore_r if side == 'r' else h.fore_l
    px = fore.pivot[0]
    y = h.hand_y
    b = h.rig.bone('prop_' + side, fore, (px, y, 0), rot=(rot[0] + 0.12, rot[1], rot[2]))
    return b, (px, y, 0)

class Forge:
    """Builds a prop in fine units relative to its pivot (the palm)."""
    def __init__(self, rig, parent, pivot, rot=(0, 0, 0), name='prop_r', always=True, scale=1.0 / F, bone=None, **params):
        self.rig = rig
        self.p = tuple(pivot)
        if bone is None:
            bone = rig.bone(name, parent, pivot, rot=rot, scale=scale, always=1.0 if always else 0.0, **params)
        self.b = bone

    def at(self, x, y, z):
        return (self.p[0] + x, self.p[1] + y, self.p[2] + z)

    def box(self, x, y, z, w, h, d, mat, name='part', grow=0.0, **kw):
        return self.b.box(self.at(x, y, z), (w, h, d), mat, name=name, grow=grow, **kw)

    def cbox(self, cx, cy, cz, w, h, d, mat, name='part', grow=0.0, **kw):
        return self.box(cx - w / 2, cy - h / 2, cz - d / 2, w, h, d, mat, name, grow, **kw)

    def sub(self, name, x, y, z, rot=(0, 0, 0), anim=None, **params):
        piv = self.at(x, y, z)
        b = self.rig.bone(name, self.b, piv, rot=rot, anim=anim, **params)
        return Forge(self.rig, None, piv, bone=b)

def held(h, side, aim, name=None, always=True):
    fore = h.fore_r if side == 'r' else h.fore_l
    piv = (fore.pivot[0], h.hand_y, 0)
    return Forge(h.rig, fore, piv, rot=(aim[0] + 0.12, aim[1], aim[2]), name=name or 'prop_' + side, always=always)

# ------------------------------------------------------------------------------------------- materials
def steel(c='#c8d0dc', glow=None, **kw):
    return M('metal', c, edge_glow=glow, **kw)

def gold(c='#e2b84a', **kw):
    return M('metal', c, **kw)

def gem(c, **kw):
    return M('gem', c, **kw)

def wrap(c, accent):
    return M('cloth', c, accent=accent, pattern='wrap', hem_shadow=False, round=False)

# ------------------------------------------------------------------------------------------- parts
def grip(f, length, mat, w=2, d=2, y0=0.0):
    f.box(-w / 2, y0 - length / 2, -d / 2, w, length, d, mat, 'grip')
    return y0 - length / 2, y0 + length / 2           # top, bottom

def pommel(f, y, kind, mat, stone=None, size=3):
    if kind == 'gem':
        f.cbox(0, y + 1, 0, size, 2, size, mat, 'pommel')
        if stone:
            f.cbox(0, y + 2.5, 0, 2, 2, 2, stone, 'pommel_gem', grow=0.25)
    elif kind == 'crown':
        f.cbox(0, y + 1, 0, size, 2, size, mat, 'pommel')
        for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            f.box(dx * (size / 2 - 0.5) - 0.5, y + 2, dz * (size / 2 - 0.5) - 0.5, 1, 2, 1, mat, 'pommel_spike')
        if stone:
            f.cbox(0, y + 2.5, 0, 1, 1, 1, stone, 'pommel_gem')
    elif kind == 'ring':
        f.box(-0.5, y, -2.5, 1, 1, 5, mat, 'pommel_ring_a')
        f.box(-0.5, y + 4, -2.5, 1, 1, 5, mat, 'pommel_ring_b')
        f.box(-0.5, y + 1, -2.5, 1, 3, 1, mat, 'pommel_ring_c')
        f.box(-0.5, y + 1, 1.5, 1, 3, 1, mat, 'pommel_ring_d')
        if stone:
            f.cbox(0, y + 2.5, 0, 1, 1, 1, stone, 'pommel_gem')
    else:  # cap
        f.cbox(0, y + 1, 0, size, 2, size, mat, 'pommel')

def guard(f, y, kind, mat, w=10, stone=None, accent=None):
    """y = top of the grip; returns the y where the blade starts."""
    if kind == 'cross':
        f.cbox(0, y - 1, 0, 3, 2, w, mat, 'guard_bar')
        for s in (-1, 1):
            c = f.sub('quillon' + ('f' if s < 0 else 'b'), 0, y - 1, s * (w / 2 - 0.5), rot=(s * -0.6, 0, 0))
            c.box(-1, -3, -1, 2, 3, 2, mat, 'curl')
            c.box(-0.5, -4, -0.5, 1, 1, 1, accent or mat, 'curl_tip')
        if stone:
            for s in (-1, 1):
                f.cbox(s * 1.75, y - 1, 0, 1, 2, 2, stone, 'guard_gem')
        return y - 2
    if kind == 'wing':
        f.cbox(0, y - 1, 0, 3, 2, 5, mat, 'guard_core')
        for s in (-1, 1):
            for k in range(3):
                wgt = f.sub(f'wing{"f" if s < 0 else "b"}{k}', 0, y - 1, s * 2, rot=(s * (0.55 + 0.35 * k), 0, 0))
                wgt.box(-0.5, -(5 - k), -1 if s < 0 else 0, 1, 5 - k, 1 + (k == 0), accent or mat, 'feather')
        if stone:
            for s in (-1, 1):
                f.cbox(s * 1.75, y - 1, 0, 1, 2, 2, stone, 'guard_gem')
        return y - 2
    if kind == 'tsuba':
        f.cbox(0, y - 0.5, 0, 6, 1, 7, mat, 'tsuba')
        f.box(-3.5, y - 0.75, -4, 7, 0, 8, M('ring', (accent or '#d8b050'), width=0.18, inner=0.6, spokes=6, glow_amount=0.0), 'tsuba_ring')
        f.cbox(0, y - 2, 0, 2, 2, 3, gold(), 'habaki')
        return y - 3
    if kind == 'crescent':
        f.cbox(0, y - 1, 0, 3, 2, 4, mat, 'guard_core')
        for s in (-1, 1):
            a = f.sub('horn' + ('f' if s < 0 else 'b'), 0, y - 1, s * 2, rot=(s * 1.0, 0, 0))
            a.box(-0.5, -3, -0.5, 1, 3, 1, mat, 'horn_a')
            b2 = a.sub('horn2' + ('f' if s < 0 else 'b'), 0, -3, 0, rot=(s * -0.7, 0, 0))
            b2.box(-0.5, -3, -0.5, 1, 3, 1, accent or mat, 'horn_b')
        if stone:
            f.cbox(0, y - 1, -2.5, 2, 2, 1, stone, 'guard_gem')
        return y - 2
    if kind == 'halo':
        f.cbox(0, y - 1, 0, 3, 2, 6, mat, 'guard_core')
        f.box(-0.25, y - 9, -5, 0, 10, 10, M('ring', accent or '#ffe9a0', width=0.12, inner=0.82, spikes=8, glow_amount=0.6), 'guard_halo')
        if stone:
            f.cbox(0, y - 1, -3.25, 2, 2, 1, stone, 'guard_gem')
        return y - 2
    if kind == 'sun':
        f.cbox(0, y - 1, 0, 3, 2, 6, mat, 'guard_core')
        f.box(-0.25, y - 7, -6, 0, 12, 12, M('ring', accent or '#ffd76a', width=0.1, inner=0.5, spikes=12, glow_amount=0.5), 'guard_sun')
        if stone:
            f.cbox(0, y - 1, 0, 2, 2, 2, stone, 'guard_gem', grow=0.5)
        return y - 2
    # plain collar
    f.cbox(0, y - 1, 0, 3, 2, 4, mat, 'guard_core')
    return y - 2

def blade(f, y0, profile, mat, t=1, curve=0.0, fuller=None, edge=None, name='blade', offset_z=0.0):
    """profile: list of (width, height) from the base up; sections stack upwards (towards -y).
    curve bends the blade towards +z (back edge) a little per section, like a katana's sori."""
    cur = f
    y = y0                      # y is always local to `cur`
    z = offset_z
    bm = dict(mat, blade=True) if mat.get('type') == 'metal' else mat
    for i, (w, h) in enumerate(profile):
        if curve and i:
            cur = cur.sub(f'{name}_s{i}', 0, y, 0, rot=(curve, 0, 0))
            y = 0
        cur.box(-t / 2, y - h, z - w / 2, t, h, w, bm, f'{name}{i}')
        if fuller and h >= 3 and w >= 3:
            for s in (-1, 1):
                cur.box(s * (t / 2 + 0.25), y - h + 0.5, z - 0.5, 0, h - 1, 1, fuller, f'{name}_fuller{i}')
        y -= h
    return cur, y

def tassel(f, x, y, z, cord, tuft, length=4, name='tassel'):
    t = f.sub(name, x, y, z, anim='sway', ax=2, amp=0.12, speed=0.09)
    t.box(-0.5, 0, -0.5, 1, length, 1, cord, 'cord')
    t.box(-1, length, -1, 2, 3, 2, tuft, 'tuft')
    return t

def ribbon(f, x, y, z, mat, length=8, width=2, name='ribbon', phase=0.0):
    r = f.sub(name, x, y, z, anim='sway', ax=0, amp=0.15, speed=0.08, phase=phase)
    r.box(0, 0, -width / 2, 0, length // 2, width, mat, 'ribbon_a')
    r2 = r.sub(name + '2', 0, length // 2, 0, rot=(0.25, 0, 0), anim='sway', ax=0, amp=0.15, speed=0.08, phase=phase + 0.7)
    r2.box(0, 0, -width / 2, 0, length - length // 2, width, dict(mat, shape='point'), 'ribbon_b')
    return r

def orbit(f, y, radius, mats, count=3, size=1, name='orbit', speed=0.06, axis=1):
    hub = f.sub(name, 0, y, 0, anim='spin', speed=speed, ax=axis)
    for i in range(count):
        a = 2 * math.pi * i / count
        hub.cbox(math.cos(a) * radius, 0, math.sin(a) * radius, size, size, size, mats[i % len(mats)], f'{name}_bit')
    return hub

def flames(f, y, z, mat, count=3, h=5, name='flame'):
    for i in range(count):
        fl = f.sub(f'{name}{i}', 0, y - i * 5, z, anim='sway', ax=0, amp=0.1, speed=0.15, phase=i * 1.3)
        fl.box(0, -h, -1, 0, h, 2, dict(mat, shape='point'), 'wisp')

# ------------------------------------------------------------------------------------------- weapon archetypes
def longsword(f, blade_mat, guard_mat, grip_mat, length=36, width=4, guard_kind='cross', stone=None, pommel_kind='gem',
              fuller=None, edge=None, accent=None, grip_len=7, taper=True):
    gtop, gbot = grip(f, grip_len, grip_mat)
    pommel(f, gbot, pommel_kind, guard_mat, stone)
    y0 = guard(f, gtop, guard_kind, guard_mat, w=width + 6, stone=stone, accent=accent)
    sec = []
    n = max(3, length // 8)
    for i in range(n):
        w = width if not taper else max(2, width - (i * 2) // n)
        sec.append((w, length // n))
    sec.append((max(1, sec[-1][0] - 2), 2))
    sec.append((1, 2))
    return blade(f, y0, sec, blade_mat, fuller=fuller, edge=edge)

def katana(f, blade_mat, tsuba_mat, grip_mat, length=36, accent=None, kashira=None):
    gtop, gbot = grip(f, 9, grip_mat)
    pommel(f, gbot, 'cap', kashira or tsuba_mat, size=3)
    y0 = guard(f, gtop, 'tsuba', tsuba_mat, accent=accent)
    sec = [(3, 9), (3, 9), (3, 9), (2, 6), (1, 3)]
    return blade(f, y0, sec, blade_mat, curve=0.06)

def dagger(f, blade_mat, guard_mat, grip_mat, length=14, width=4, guard_kind='crescent', stone=None, fuller=None):
    gtop, gbot = grip(f, 5, grip_mat)
    pommel(f, gbot, 'gem', guard_mat, stone, size=3)
    y0 = guard(f, gtop, guard_kind, guard_mat, w=width + 4, stone=stone)
    sec = [(width, length // 3), (width, length // 3), (width - 1, length // 3 - 2), (max(1, width - 2), 2), (1, 2)]
    return blade(f, y0, sec, blade_mat, fuller=fuller)

def polearm(f, shaft, length=56, below=12, rings=None):
    """Long shaft held near its lower third; returns y of the top."""
    top = -(length - below)
    f.box(-1, top, -1, 2, length, 2, shaft, 'shaft')
    if rings:
        for k, yy in enumerate(range(int(top) + 6, below - 2, 9)):
            f.cbox(0, yy, 0, 3, 1, 3, rings, f'shaft_ring{k}')
    f.cbox(0, below, 0, 3, 2, 3, rings or shaft, 'butt')
    return top

def claws(f, mat, tip, count=3, length=7, curve=0.35, plate=None):
    if plate:
        f.cbox(0, -1, 0, 5, 3, 6, plate, 'gauntlet', grow=0.25)
    for k in range(count):
        z = -2 + k * 2 - (count - 3)
        c = f.sub(f'claw{k}', 0, -2, z - 2, rot=(0.25, 0, 0))
        L1 = length // 2
        c.box(-0.5, -L1, -0.5, 1, L1, 1.5 if k == 1 else 1, mat, 'claw_a')
        c2 = c.sub(f'claw{k}b', 0, -L1, 0, rot=(curve, 0, 0))
        c2.box(-0.5, -(length - L1), -0.5, 1, length - L1, 1, tip, 'claw_b')

# ------------------------------------------------------------------------------------------- relic weapons
WEAPONS = {}
def weapon(fn):
    WEAPONS[fn.__name__] = fn
    return fn

@weapon
def kokuhaku(f):
    # 蒼白断界刀 — 古びた一振り。蒼白い炎のような残光（刃紋が淡く光る）
    katana(f, M('metal', '#cdd5e0', accent='#a8ecff', pattern='hamon', pattern_glow=True, glow_amount=0.8, edge_glow='#9fe8ff'),
           M('metal', '#3a4250', accent='#c8a050'), wrap('#1c2440', '#d8e4ff'), accent='#c8a050', kashira=M('metal', '#b8c0cc'))
    flames(f, -12, -3, M('energy', '#9fe8ff', alpha=150), count=3, h=6)

@weapon
def riha(f):
    # 真言の短剣 — 言霊の短剣。白金の刃に光る真言、赤い房と鈴、浮かぶ札
    dagger(f, M('metal', '#f4f0e6', accent='#ffcf5a', pattern='runes', pattern_glow=True, glow_amount=0.7), gold('#e6b84a'),
           wrap('#b0335c', '#ffd36b'), length=16, width=4, guard_kind='crescent', stone=gem('#ffcf5a'))
    t = tassel(f, 0, 6, 0, M('cloth', '#b0335c'), M('cloth', '#d8304a', accent='#ffd36b', trim=1))
    t.cbox(0, 8, 0, 1, 1, 1, gold('#ffd36b'), 'bell')
    ofuda = f.sub('ofuda', 0, -14, -5, anim='float', amp=0.6, speed=0.08)
    ofuda.box(-0.25, -5, -1.5, 0, 6, 3, M('cloth', '#fffaf0', accent='#c03040', pattern='runes', pattern_glow=True, glow_amount=0.5), 'ofuda')

@weapon
def tenki(f):
    # 唯我の王剣 — 白と金の王剣。日輪の鍔、王冠の柄頭、金の樋が輝く
    longsword(f, M('metal', '#f6f2e8', accent='#ffd76a', pattern='filigree', edge_glow='#fff2b0'), gold('#e2b33e'),
              wrap('#fffaee', '#e2b33e'), length=40, width=5, guard_kind='sun', stone=gem('#9fd8ff'), pommel_kind='crown',
              fuller=M('energy', '#ffe38a'), accent='#ffd76a')

@weapon
def berit(f):
    # 万界解体刃 — 錬成陣の鍔、黒金の刻印刃、柄に試験管、柄頭は光る小瓶
    gtop, gbot = grip(f, 6, M('metal', '#2a2833', accent='#d5a449', pattern='filigree'))
    f.cbox(0, gbot + 1.5, 0, 3, 3, 3, M('gem', '#7df0c8'), 'flask_body', grow=0.25)
    f.cbox(0, gbot + 3.5, 0, 1, 1, 1, gold('#d5a449'), 'flask_cap')
    for k, c in enumerate(('#e36fb2', '#6fb0e3')):
        f.box(1, gtop + 1 + k * 2, -0.5, 1, 2, 1, gem(c), 'vial')
    f.box(-0.25, gtop - 8, -5, 0, 10, 10, M('ring', '#d5a449', width=0.08, inner=0.86, poly=6, glow_amount=0.5), 'array')
    f.cbox(0, gtop - 1, 0, 3, 2, 5, gold('#d5a449'), 'guard')
    blade(f, gtop - 2, [(4, 7), (4, 7), (4, 6), (3, 4), (2, 2), (1, 2)],
          M('metal', '#3a3440', accent='#e2b34c', pattern='runes', pattern_glow=True, glow_amount=0.6, edge_glow='#ffe0a0'), curve=-0.08)

@weapon
def elseria(f):
    # 星脈刻印剣 — 星の魔力を通す長い杖剣。白い柄、銀の環、三日月と星、結晶の刃
    top = polearm(f, M('wood', '#ece4d4'), length=58, below=14, rings=M('metal', '#c8d8ee'))
    f.cbox(0, top - 1, 0, 4, 2, 4, M('metal', '#c8d8ee', rivets=True), 'collar')
    for s in (-1, 1):
        w = f.sub('crescent' + ('f' if s < 0 else 'b'), 0, top - 1, s * 2, rot=(s * 0.9, 0, 0))
        w.box(-0.5, -6, -0.5, 1, 6, 1, M('metal', '#e8f0ff'), 'arc_a')
        w2 = w.sub('crescent2' + ('f' if s < 0 else 'b'), 0, -6, 0, rot=(s * -1.1, 0, 0))
        w2.box(-0.5, -4, -0.5, 1, 4, 1, M('metal', '#e8f0ff', edge_glow='#bfe4ff'), 'arc_b')
    blade(f, top - 2, [(3, 6), (3, 5), (2, 4), (1, 2)], M('gem', '#9fe6ff'), name='crystal')
    f.box(-0.25, top - 14, -4, 0, 8, 8, M('plane', '#d8f8ff', shape='star', glow=True, glow_amount=0.7), 'star')
    orbit(f, top - 10, 6, [gem('#9fe6ff'), gem('#ffffff'), gem('#c8b0ff')], count=3, name='stars', speed=0.05)

@weapon
def valeria(f):
    # 精密解構剣 — 歯車と油圧の機械剣。発光する切断刃、鋲打ちの装甲板（体より大きい誇張）
    gtop, gbot = grip(f, 8, M('cloth', '#3a3028', accent='#e7a444', pattern='wrap'))
    pommel(f, gbot, 'cap', M('metal', '#7a6a58', rivets=True))
    f.cbox(0, gtop - 1.5, 0, 4, 3, 8, M('metal', '#5a4a3a', rivets=True, accent='#e7a444', pattern='band'), 'housing')
    gear = f.sub('gear', 0, gtop - 1.5, 4.5, rot=(0, 0, 0), anim='spin', ax=0, speed=0.08)
    gear.box(-0.25, -4, -4, 0, 8, 8, M('ring', '#c8b080', width=0.25, inner=0.4, spikes=10, glow_amount=0.0), 'gear')
    for s in (-1, 1):
        f.box(s * 1.75 - 0.5, gtop - 12, -1, 1, 10, 1, M('metal', '#b0b6c4'), 'piston')
    cur, y = blade(f, gtop - 3, [(6, 8), (6, 8), (5, 8), (4, 6), (2, 3), (1, 2)],
                   M('metal', '#8a9098', accent='#e7a444', pattern='band', rivets=True, edge_glow='#ffbf5a'))
    f.box(-0.75, gtop - 30, -1, 0, 26, 2, M('energy', '#ffbf5a'), 'cutter_line')

@weapon
def huang_linghua(f):
    # 黄天龍文槍刃 — 細身の黒金の杖槍。巻きつく金龍、翡翠の穂先、赤い飾り紐、龍珠
    top = polearm(f, M('metal', '#23202a', accent='#d8b754', pattern='rings'), length=60, below=14, rings=gold('#d8b754'))
    for k in range(6):
        a = k * 1.1
        f.cbox(math.cos(a) * 1.5, top + 10 + k * 4, math.sin(a) * 1.5, 1, 3, 1, gold('#e8c460'), 'dragon_coil')
    f.cbox(0, top - 1.5, 0, 4, 3, 4, gold('#d8b754', rivets=True), 'dragon_head')
    f.cbox(0, top - 1, -3, 2, 2, 3, gold('#d8b754'), 'dragon_snout')
    f.cbox(0, top - 4, -1, 2, 2, 2, gem('#ffe27a'), 'pearl', grow=0.25)
    blade(f, top - 3, [(4, 5), (4, 5), (3, 4), (2, 3), (1, 2)], M('metal', '#8ad8b0', accent='#d8b754', pattern='filigree', edge_glow='#d0ffe0'), name='spearhead')
    for s, ph in ((-1, 0.0), (1, 1.2)):
        tassel(f, s * 1.5, top + 1, 0, M('cloth', '#d8303a'), M('cloth', '#d8303a', accent='#ffd36b', trim=1), length=5, name='cord' + ('a' if s < 0 else 'b'))

@weapon
def ferdinand(f):
    # 試作零号振動刃 — 二股の刃の間で振動するエネルギー、コイル、電池、計器、真鍮
    gtop, gbot = grip(f, 7, M('cloth', '#5a4a3a', accent='#2a2420', pattern='wrap'))
    f.cbox(0, gbot + 1.5, 0, 3, 3, 3, M('metal', '#c8a050', rivets=True), 'battery')
    f.cbox(0, gbot + 1.5, -2, 2, 2, 1, M('energy', '#8bcfe2'), 'gauge')
    f.cbox(0, gtop - 1.5, 0, 4, 3, 6, M('metal', '#c8a050', accent='#8bcfe2', pattern='circuit', pattern_glow=True), 'core')
    for s in (-1, 1):
        f.box(-0.5, gtop - 28, s * 2.5 - 0.5, 1, 25, 1, M('metal', '#b0b6c4', edge_glow='#8bcfe2'), 'prong')
        for k in range(3):
            f.cbox(0, gtop - 8 - k * 7, s * 2.5, 2, 1, 2, M('metal', '#c8a050'), f'coil{k}', grow=0.25)
    f.box(-0.5, gtop - 27, -1.5, 1, 24, 3, M('energy', '#bff0ff', alpha=190, cut=True), 'vibration')
    f.box(-0.5, gtop - 30, -0.5, 1, 3, 1, M('metal', '#b0b6c4'), 'tip')

@weapon
def nortia(f):
    # 遊戯の玩具剣 — 色とりどりの積み木の刃、星の切っ先、サイコロの鍔、縞の柄
    gtop, gbot = grip(f, 6, M('cloth', '#5a6ad8', accent='#f4f0ff', pattern='stripes'))
    f.cbox(0, gbot + 1.5, 0, 3, 3, 3, M('cloth', '#ffffff', accent='#222222', pattern='dots'), 'die')
    f.cbox(0, gtop - 1, 0, 3, 2, 9, M('cloth', '#f4d06f', accent='#f45a7a', pattern='chevron'), 'guard')
    cols = ['#ff6f8f', '#f4d06f', '#7ff07f', '#7fd0ff', '#c070ff']
    y = gtop - 2
    for k, c in enumerate(cols):
        f.box(-0.5, y - 5, -2, 1, 5, 4, M('cloth', c, round=False), f'block{k}')
        y -= 5
    f.box(-0.25, y - 6, -3.5, 0, 7, 7, M('plane', '#ffe060', shape='star', glow=True, glow_amount=0.5), 'star_tip')

@weapon
def lucifara(f):
    # 失楽の欲刃 — 漆黒の曲刀、深紅の刃縁、黒羽の鍔とハートの紅玉、小さな光輪
    gtop, gbot = grip(f, 7, wrap('#2a1020', '#c54573'))
    pommel(f, gbot, 'ring', M('metal', '#2a1a2a'), gem('#c54573'))
    y0 = guard(f, gtop, 'wing', M('metal', '#1a1420'), stone=gem('#ff3a6a'), accent=M('feather', '#1a1420', tip='#5a2040'))
    blade(f, y0, [(3, 8), (3, 8), (3, 8), (2, 6), (1, 3)], M('metal', '#1e1826', accent='#c54573', pattern='filigree', edge_glow='#ff4a7a'), curve=0.09)
    f.box(-0.25, gbot + 2, -3, 0, 6, 6, M('ring', '#c54573', width=0.18, spikes=6, glow_amount=0.6), 'halo')

@weapon
def taika(f):
    # 超克の拳刃 — 拳に装着する刃（カタール）。鬼角の装飾、赤黒の鋼
    f.cbox(0, -1, 0, 4, 4, 6, M('metal', '#2a1a24', accent='#e44c49', pattern='band', rivets=True), 'gauntlet', grow=0.25)
    for s in (-1, 1):
        f.box(-0.5, -6, s * 2 - 0.5, 1, 4, 1, M('horn', '#f0e6d8', tip='#e44c49', glow=True, flip=True), 'oni_horn')
    blade(f, -4, [(5, 6), (4, 6), (3, 5), (2, 3), (1, 2)], M('metal', '#c8c0c0', accent='#e44c49', pattern='fuller', edge_glow='#ff9a6a'), name='katar')

@weapon
def mary_sue(f):
    # 次章の英雄剣 — 青と金の英雄剣。金の翼鍔、柄頭に開いた本（次の章）、星のきらめき
    longsword(f, M('metal', '#e0e8f8', accent='#f2bb5b', pattern='fuller', edge_glow='#fff2c0'), gold('#f2bb5b'), wrap('#2a4aa0', '#f2bb5b'),
              length=36, width=4, guard_kind='wing', stone=gem('#2fa07a'), pommel_kind='cap', accent=M('metal', '#f6e2a0'))
    bk = f.sub('book', 0, 5, 0)
    bk.box(-0.5, 0, -3, 1, 3, 6, M('cloth', '#c03040', accent='#f2bb5b', trim=1), 'cover')
    bk.box(-0.25, -1, -2.5, 0, 3, 5, M('cloth', '#fff8e8'), 'pages')
    orbit(f, -20, 5, [M('plane', '#ffe38a', shape='star', glow=True)], count=3, size=2, name='sparkle')

@weapon
def savior(f):
    # 救済の聖剣 — 白銀と金。十字の鍔と光輪、翼、刃に光の文字
    longsword(f, M('metal', '#f8f9fc', accent='#ffe9a0', pattern='runes', pattern_glow=True, glow_amount=0.5, edge_glow='#fff6c0'), gold('#dac36c'),
              wrap('#f0f0f6', '#dac36c'), length=38, width=5, guard_kind='halo', stone=gem('#fff3b0'), pommel_kind='crown', accent='#ffe9a0')
    for s in (-1, 1):
        w = f.sub('holy_wing' + ('f' if s < 0 else 'b'), 0, -5, s * 3, rot=(s * 0.7, 0, 0))
        w.box(-0.25, -6, -2 if s < 0 else 0, 0, 6, 2, M('feather', '#fffaf0', tip='#ffe0a0', glow=True), 'wing')

@weapon
def gokuka(f):
    # 外法呪爪 — 竜の鉤爪。滴る色変わりの呪詛（油膜の液体）、紫に光る爪先
    claws(f, M('horn', '#2a1a2a', tip='#af55bb'), M('horn', '#3a2040', tip='#e070f0', glow=True), count=3, length=9, curve=0.4,
          plate=M('oilslick', '#1e1830'))
    for k in range(2):
        d = f.sub(f'drip{k}', 0, 1, -1 + k * 2, anim='sway', ax=0, amp=0.1, speed=0.12, phase=k)
        d.box(-0.5, 0, -0.5, 1, 3 + k, 1, M('slime', '#c070e0', alpha=180), 'drip')

@weapon
def merlinus(f):
    # 深淵術式刃 — 杖の先に結晶の刃、周囲を回る術式の環（紫と銀）
    top = polearm(f, M('wood', '#5a3a2a'), length=50, below=12, rings=M('metal', '#c8c8e8'))
    f.cbox(0, top - 1, 0, 3, 2, 3, M('metal', '#c8c8e8'), 'collar')
    c = f.sub('crook', 0, top - 2, 0, rot=(-0.6, 0, 0))
    c.box(-0.5, -6, -0.5, 1, 6, 1, M('wood', '#5a3a2a'), 'crook_a')
    c2 = c.sub('crook2', 0, -6, 0, rot=(-1.4, 0, 0))
    c2.box(-0.5, -5, -0.5, 1, 5, 1, M('wood', '#5a3a2a'), 'crook_b')
    blade(f, top - 2, [(2, 5), (2, 4), (1, 3)], M('gem', '#c8a0ff'), name='shard')
    for k, (rx, sp) in enumerate(((0.0, 0.05), (1.2, -0.04))):
        ring = f.sub(f'formula{k}', 0, top - 6, 0, rot=(rx, 0, 0), anim='spin', speed=sp)
        ring.box(-6, 0, -6, 12, 0, 12, M('ring', '#b294ee', width=0.06, inner=0.85, poly=6 + k, glow_amount=0.7), 'formula')

@weapon
def nun(f):
    # 無貌の流体刃 — 黒く蠢く粘体の刃、鍔に道化の白い仮面
    gtop, gbot = grip(f, 6, M('oilslick', '#1c1426', hues=['#a681d9', '#e8d070']))
    f.box(-1.75, gtop - 5, -2.5, 0, 5, 5, M('decal', '#f4f0e8', base=M('cloth', '#f4f0e8', round=False),
          decals=[('right', 1, 1, '#a681d9', True), ('right', 3, 1, '#a681d9', True), ('right', 2, 3, '#2a1a30')]), 'mask')
    y = gtop - 1
    for k in range(5):
        seg = f.sub(f'goo{k}', 0, y, 0, rot=(0.07 * (1 if k % 2 else -1), 0, 0), anim='sway', ax=0, amp=0.05, speed=0.1, phase=k)
        w = 4 if k < 3 else 3 - (k - 3)
        seg.box(-0.5, -6, -w / 2, 1, 6, w, M('oilslick', '#1c1426', hues=['#a681d9', '#6a4a9a']), 'goo')
        f = seg
        y = -6

@weapon
def arcana(f):
    # 因果を結ぶ糸刃 — 白金の細剣、糸巻きの鍔、金糸が刃に絡む、運命札の飾り
    gtop, gbot = grip(f, 7, wrap('#f4f5fc', '#dabd72'))
    pommel(f, gbot, 'gem', gold('#dabd72'), gem('#7a6ad8'))
    f.cbox(0, gtop - 1, 0, 3, 2, 3, gold('#dabd72'), 'spindle')
    f.cbox(0, gtop - 1, 0, 2, 1, 7, gold('#e8d090'), 'spindle_bar', grow=0.25)
    blade(f, gtop - 2, [(2, 10), (2, 10), (1, 10), (1, 4)], M('metal', '#f4f2ea', edge_glow='#ffe9a0'), name='needle')
    for k in range(5):
        f.box(-0.75, gtop - 6 - k * 7, -2 + (k % 2) * 3, 0, 7, 1, M('energy', '#ffd76a'), f'thread{k}')
    card = f.sub('card', 0, gbot + 1, 0, anim='sway', ax=2, amp=0.1, speed=0.07)
    card.box(-0.25, 1, -1.5, 0, 4, 3, M('cloth', '#f8f0dc', accent='#7a5ad8', pattern='cross'), 'card')

@weapon
def hakyoku(f):
    # 適応捕食の王刃 — 牙の並ぶ有機機械の大剣、桃色に光る亀裂、王冠の鍔、柄の眼
    gtop, gbot = grip(f, 8, M('metal', '#211e2e', accent='#ff627f', pattern='cracks', pattern_glow=True))
    f.cbox(0, gtop - 1.5, 0, 4, 3, 9, M('horn', '#2a2438', tip='#ff627f'), 'crown_guard')
    for k in range(5):
        f.box(-0.5, gtop - 6, -4 + k * 2, 1, 3, 1, M('horn', '#2a2438', tip='#ff627f', glow=True, flip=True), 'crown_spike')
    f.cbox(0, gbot - 2, -1.25, 2, 2, 0, M('eye', '#ff3a6a', slit=True), 'eye')
    cur, y = blade(f, gtop - 3, [(7, 9), (7, 9), (6, 8), (5, 6), (3, 3), (1, 2)],
                   M('metal', '#2a2438', accent='#ff627f', pattern='cracks', pattern_glow=True, glow_amount=0.7))
    for k in range(7):
        f.box(-0.5, gtop - 6 - k * 4, -4.5, 1, 2, 1, M('teeth', '#f2efe6'), 'fang')

@weapon
def shinra(f):
    # 万物否定の天敵爪 — 白い鬼の爪、紅の爪先、手首に椿
    claws(f, M('horn', '#f0e0d8', tip='#bb5476'), M('horn', '#f0e0d8', tip='#ff3a6a', glow=True), count=3, length=8, curve=0.3,
          plate=M('cloth', '#f3eadf', accent='#bb5476', trim=1))
    f.box(-2.75, -1, -2, 0, 4, 4, M('plane', '#d8304a', shape='circle', glow=False), 'camellia')
    f.cbox(-2.5, 1, 0, 1, 1, 1, gem('#ffe070'), 'camellia_heart')

@weapon
def ain_sof_aur(f):
    # 分岐確定の王剣 — 刃が三叉に分岐する白紫の王剣、紫の脈、鍔に浮かぶ光の冠
    gtop, gbot = grip(f, 7, wrap('#f3ecfa', '#a791ee'))
    pommel(f, gbot, 'crown', gold('#cbbcff'), gem('#ffffff'))
    y0 = guard(f, gtop, 'cross', M('metal', '#e8e0ff', accent='#a791ee', pattern='filigree'), w=10, stone=gem('#a791ee'))
    cur, y = blade(f, y0, [(4, 9), (4, 9), (3, 6)], M('metal', '#f3ecfa', accent='#a791ee', pattern='cracks', pattern_glow=True, glow_amount=0.6))
    for k, rz in enumerate((-0.35, 0.0, 0.35)):
        br = cur.sub(f'branch{k}', 0, y, 0, rot=(rz, 0, 0))
        br.box(-0.5, -9 if k == 1 else -7, -1, 1, 9 if k == 1 else 7, 2, M('metal', '#f3ecfa', edge_glow='#cbbcff'), 'branch')
    crown = f.sub('floating_crown', 0, y0 - 6, 0, anim='spin', speed=0.03)
    crown.box(-3.5, -1, -3.5, 7, 1, 7, M('energy', '#cbbcff'), 'crown_band', faces={'top': None, 'bottom': None})

@weapon
def angra_mainyu(f):
    # 全害悪徳の影刃 — 煙のような黒い波刃、深紅の文様、茨の鍔、紅い眼の宝玉
    gtop, gbot = grip(f, 7, wrap('#141018', '#a0474e'))
    pommel(f, gbot, 'gem', M('metal', '#1c1822'), gem('#c0303a'))
    f.cbox(0, gtop - 1, 0, 3, 2, 6, M('metal', '#1c1822'), 'guard')
    for s in (-1, 1):
        th = f.sub('thorn' + ('f' if s < 0 else 'b'), 0, gtop - 1, s * 3, rot=(s * 0.8, 0, 0))
        th.box(-0.5, -4, -0.5, 1, 4, 1, M('horn', '#1c1822', tip='#c0303a', glow=True, flip=True), 'thorn')
    f.cbox(0, gtop - 1, -3.25, 2, 2, 1, M('eye', '#c0303a', slit=True), 'eye')
    y = gtop - 2
    for k in range(7):
        w = 4 if k < 5 else 4 - (k - 4)
        f.box(-0.5, y - 5, -w / 2 + (1 if k % 2 else -1) * 0.75, 1, 5, w, M('void', '#140c18', accent='#c04a50'), f'wave{k}')
        y -= 5
    flames(f, gtop - 8, 2, M('energy', '#3a1a2a', alpha=170), count=4, h=6, name='smoke')

@weapon
def magna_mater(f):
    # 命を継ぐ蔓刃 — 編まれた蔓と葉の刃、花の鍔、根の柄
    gtop, gbot = grip(f, 7, M('wood', '#5a4030'))
    f.box(-1.5, gbot, -1.5, 3, 2, 3, M('wood', '#4a3626'), 'roots')
    f.box(-0.25, gtop - 6, -4, 0, 8, 8, M('plane', '#ff9ab8', shape='star', glow=True, glow_amount=0.3), 'blossom')
    f.cbox(0, gtop - 2, 0, 2, 2, 2, gem('#fff0a0'), 'pistil')
    y = gtop - 3
    for k in range(6):
        seg = f.sub(f'vine{k}', 0, y, 0, rot=(0.05 * (1 if k % 2 else -1), 0, 0))
        seg.box(-0.5, -5, -1.5, 1, 5, 3 if k < 4 else 2, M('leaf', '#5a8a40', holes=0.0), 'vine')
        seg.box(-0.25, -4, (2 if k % 2 else -4), 0, 3, 2, M('plane', '#7ab050', shape='leaf'), 'leaf')
        f = seg
        y = -5

@weapon
def ouroboros(f):
    # 円環循環の時刃 — 時計盤の鍔と針、柄に尾を噛む蛇の環、背に歯車の刃
    gtop, gbot = grip(f, 7, wrap('#2a3246', '#dfb971'))
    snake = f.sub('serpent', 0, gtop + 3, 0, anim='spin', ax=1, speed=0.02)
    snake.box(-2.5, -0.5, -2.5, 5, 1, 5, M('scale', '#dfb971'), 'serpent', faces={'top': None, 'bottom': None})
    f.box(-0.25, gtop - 9, -5, 0, 10, 10, M('ring', '#dfb971', width=0.1, inner=0.8, spikes=12, spokes=2, glow_amount=0.4), 'clock')
    f.cbox(0, gtop - 1, 0, 3, 2, 4, gold('#dfb971'), 'guard')
    cur, y = blade(f, gtop - 2, [(4, 9), (4, 9), (3, 8), (2, 4), (1, 2)], M('metal', '#c8d4ec', accent='#8ab0e8', pattern='rings', edge_glow='#bfe0ff'))
    for k in range(5):
        f.box(-0.5, gtop - 6 - k * 6, 2, 1, 2, 1, gold('#dfb971'), 'cog_tooth')

@weapon
def miyohime(f):
    # 万律自在の神刃 — 浮遊する結晶片で組まれた刃、極彩色の幾何光輪、紅白の注連縄と紙垂
    gtop, gbot = grip(f, 7, wrap('#f8f4fc', '#c02a4a'))
    pommel(f, gbot, 'gem', M('metal', '#3a2a4a'), gem('#7ffff0'))
    f.box(-0.25, gtop - 9, -5, 0, 10, 10, M('ring', '#ffffff', width=0.08, inner=0.7, poly=7, rainbow=True), 'geo_halo')
    f.cbox(0, gtop - 1, 0, 3, 1, 6, M('cloth', '#f8f4fc', accent='#c02a4a', pattern='wrap'), 'shimenawa', grow=0.25)
    for s in (-1, 1):
        f.box(-0.25, gtop, s * 2 - 1, 0, 4, 2, M('cloth', '#ffffff', shape='point'), 'shide')
    y = gtop - 2
    cols = ['#ba84f0', '#7ffff0', '#ff7fd0', '#ffe07a', '#ba84f0']
    for k, c in enumerate(cols):
        fr = f.sub(f'shard{k}', 0, y - 1, 0, anim='float', amp=0.4, speed=0.07, phase=k)
        fr.box(-0.5, -5, -1.5 + (k % 2) * 0.5, 1, 5, 3 if k < 4 else 2, M('gem', c), 'shard')
        y -= 6

@weapon
def innocence(f):
    # 無垢な遊びの白刃 — 真っ白な小剣、リボン、星の飾り、浮かぶ玩具
    longsword(f, M('metal', '#ffffff', edge_glow='#e0d8ff'), M('metal', '#e6e8ff'), wrap('#ffffff', '#c993ff'), length=26, width=3,
              guard_kind='plain', stone=None, pommel_kind='cap')
    ribbon(f, 0, -2, 1, M('cloth', '#c993ff'), length=8, name='ribbon_a')
    ribbon(f, 0, -2, -1, M('cloth', '#ffd76a'), length=7, name='ribbon_b', phase=1.0)
    orbit(f, -18, 5, [gem('#ffd76a'), gem('#6a8aff'), gem('#c993ff')], count=3, name='toys')

@weapon
def brutality(f):
    # 暴虐の破砕拳刃 — 巨大な棘付き鉄拳、鎖、血のように赤い
    f.cbox(0, -1, 0, 6, 6, 8, M('metal', '#5a5054', rivets=True, accent='#8a2a1a', pattern='marks'), 'fist_plate', grow=0.25)
    for k in range(4):
        f.cbox(0, -4.5, -3 + k * 2, 2, 3, 1, M('horn', '#9a9098', tip='#8a2a1a', flip=True), 'knuckle_spike')
    blade(f, -4, [(6, 4), (4, 3), (2, 2)], M('metal', '#7a7074', edge_glow='#ff5030'), name='crusher')
    for k in range(3):
        f.cbox(2.5, 1 + k * 2, 0, 1, 2, 1, M('metal', '#7a6a5a'), 'chain', grow=0.25)

@weapon
def cursed_love(f):
    # 悲劇を結ぶ呪刃 — 細身の葡萄酒色の短剣、黒薔薇の鍔、刃に絡む茨、ハートの錠
    gtop, gbot = grip(f, 6, wrap('#351f36', '#aa4b71'))
    lock = f.sub('lock', 0, gbot + 1, 0, anim='sway', ax=2, amp=0.1, speed=0.07)
    lock.box(-0.5, 1, -1.5, 1, 3, 3, gold('#c8a060'), 'heart_lock')
    f.cbox(0, gtop - 1.5, 0, 3, 3, 3, M('cloth', '#1a1018'), 'rose', grow=0.5)
    blade(f, gtop - 3, [(3, 7), (3, 7), (2, 6), (1, 3)], M('metal', '#5a1a30', accent='#aa4b71', pattern='filigree', edge_glow='#e06a90'))
    for k in range(4):
        f.box(-0.75, gtop - 5 - k * 5, -1.5 + (k % 2) * 2, 0, 4, 1, M('horn', '#1a1018', tip='#aa4b71'), 'thorn_vine')

@weapon
def relentless_research(f):
    # 生命解剖の解析刃 — 長いメス状の刃に目盛り、柄に注射筒と薬液、白とミント
    gtop, gbot = grip(f, 8, M('metal', '#f2f5f6', accent='#8bdbc7', pattern='band'))
    f.box(1, gtop + 1, -0.5, 1, 6, 1, M('gem', '#8bdbc7'), 'syringe')
    f.box(1, gbot, -0.5, 1, 1, 1, M('metal', '#c8d0d4'), 'plunger')
    f.cbox(0, gtop - 1, 0, 3, 2, 3, M('metal', '#c8d0d4'), 'collar')
    blade(f, gtop - 2, [(3, 8), (3, 8), (2, 6), (1, 3)], M('metal', '#e8eef0', accent='#4a8a7a', pattern='stripes', edge_glow='#8bdbc7'))
    f.cbox(0, gtop - 5, -2.5, 2, 2, 0, M('ring', '#d8b050', width=0.3, glow_amount=0.0), 'lens')

@weapon
def forbidden_arcana(f):
    # 禁理の術式刃 — 柄のない浮遊する術式の刃。積層した光る文字板と鎖
    for k in range(6):
        pl = f.sub(f'glyph{k}', 0, -2 - k * 5, 0, anim='float', amp=0.3, speed=0.06, phase=k * 0.8)
        w = 5 if k < 4 else 3 - (k - 4)
        pl.box(-0.5, -4, -w / 2, 1, 4, w, M('cloth', '#281f48', accent='#a883ee', pattern='runes', pattern_glow=True, glow_amount=0.8), 'glyph')
    for k in range(3):
        f.cbox(0, 2 + k * 2, 0, 1, 2, 1, M('metal', '#5a5070'), 'chain', grow=0.25)
    ring = f.sub('seal', 0, -12, 0, rot=(0, 0, 1.57), anim='spin', ax=1, speed=0.05)
    ring.box(-5, 0, -5, 10, 0, 10, M('ring', '#a883ee', width=0.06, inner=0.8, poly=5, glow_amount=0.7), 'seal')

@weapon
def fallen_savior(f):
    # 救堕の古聖剣 — 刃毀れ一つない古びた聖剣。くすんだ金の鍔、色褪せた布巻き、仄かな光
    longsword(f, M('metal', '#e8ecf4', accent='#d9d589', pattern='fuller', edge_glow='#fff6b0'), M('metal', '#b8a868', accent='#7a7060', pattern='marks'),
              M('cloth', '#3a3a6a', accent='#8a8070', pattern='wrap'), length=38, width=4, guard_kind='cross', stone=gem('#9fd8ff'),
              pommel_kind='gem', accent=M('metal', '#d9d589'))

@weapon
def sweet_pact(f):
    # 未来債権の契刃 — 羽根ペンの形の刃（金のペン先）、契約書のリボン、封蝋、蜜色の宝石
    gtop, gbot = grip(f, 7, M('cloth', '#424153', accent='#d8b175', pattern='wrap'))
    for k in range(4):
        fe = f.sub(f'quill{k}', 0, gbot - 1, (k - 1.5) * 1.2, rot=(-0.25 + 0.17 * k, 0, 0))
        fe.box(-0.25, 0, -1, 0, 9 - k, 2, M('feather', '#f6ead0', tip='#d8b175'), 'barb')
    f.cbox(0, gtop - 1, 0, 3, 2, 3, gold('#d8b175'), 'ferrule')
    f.cbox(0, gtop - 1, -2, 2, 2, 1, gem('#ffcf6a'), 'honey')
    blade(f, gtop - 2, [(4, 7), (3, 7), (2, 6), (1, 4)], M('metal', '#e8c060', accent='#5a4020', pattern='fuller', edge_glow='#ffe090'), name='nib')
    rb = ribbon(f, 0, gtop + 2, 1, M('cloth', '#f6ead0', accent='#c03040', pattern='runes', pattern_glow=True, glow_amount=0.4), length=9, width=3)
    rb.cbox(0.25, 4, 0, 2, 2, 1, M('cloth', '#c03040'), 'seal')

@weapon
def yggdrasil(f):
    # 玖天神樹の枝刃 — 刃の形に育った神樹の枝。光る樹液の脈、若葉と花
    gtop, gbot = grip(f, 7, M('wood', '#6a5038'))
    blade(f, gtop, [(4, 8), (4, 8), (3, 8), (2, 6), (1, 3)], M('wood', '#8a6a48', veins='#d8ff8a', glow_amount=0.6), name='branch')
    for k in range(4):
        f.box(-0.25, gtop - 6 - k * 7, (2 if k % 2 else -5), 0, 4, 3, M('plane', '#7ab050', shape='leaf'), 'leaf')
    for k in range(3):
        f.cbox(0, gtop - 10 - k * 9, 0, 1, 1, 1, M('gem', ['#ffe0f0', '#fff6b0', '#ffe0f0'][k]), 'blossom', grow=0.5)

# --- relic blades of the non-humanoid beings (used for icons and when a player wields them)
@weapon
def chaos(f):
    # 変質の異刃 — 見るたびに形が変わる刃：虹の核と眼、不揃いな肉片の刃
    gtop, gbot = grip(f, 6, M('oilslick', '#2a1838'))
    f.cbox(0, gtop - 2, 0, 4, 4, 4, M('rainbow', '#ffffff'), 'core')
    y = gtop - 4
    for k in range(5):
        fr = f.sub(f'frag{k}', 0, y, 0, rot=(0.15 * ((k % 3) - 1), 0, 0), anim='float', amp=0.4, speed=0.09, phase=k)
        fr.box(-0.5, -5, -2 + (k % 2), 1, 5, 4 - k // 2, M('oilslick', '#2a1838', hues=['#c050e0', '#40c0d0', '#f0c040']), 'flesh')
        if k in (1, 3):
            fr.cbox(-0.75, -3, 0, 1, 2, 2, M('gem', '#69f5f2'), 'eye')
        y -= 6

@weapon
def mels(f):
    # 無形流武刃 — 透明な液体が刃の形に固まった武器、内に硬い核
    gtop, gbot = grip(f, 6, M('slime', '#bfefff', alpha=150))
    f.cbox(0, gtop - 2, 0, 2, 2, 2, gem('#d8f6ff'), 'core')
    blade(f, gtop, [(5, 8), (4, 8), (3, 8), (2, 4), (1, 2)], M('slime', '#a8e8ff', alpha=140), name='liquid')

@weapon
def hephaistos(f):
    # 概念加工の切削刃 — 浮遊する切削リングと立方体の核、青緑の回路
    gtop, gbot = grip(f, 7, M('metal', '#435b71', accent='#52e8d6', pattern='circuit', pattern_glow=True))
    f.cbox(0, gtop - 2, 0, 4, 4, 4, gem('#a5f3ff'), 'cube')
    for k in range(3):
        ring = f.sub(f'cutter{k}', 0, gtop - 8 - k * 8, 0, anim='spin', speed=0.15 + k * 0.05)
        ring.box(-4, 0, -4, 8, 0, 8, M('ring', '#52e8d6', width=0.2, spikes=12, glow_amount=0.5), 'cutter')
    f.box(-0.5, gtop - 32, -1, 1, 28, 2, M('metal', '#8aa0b4', edge_glow='#52e8d6'), 'spine')

@weapon
def enkou(f):
    # 深海災牙 — 黒曜石の巨大な牙の刃、青白い灯火の文様
    gtop, gbot = grip(f, 7, M('scale', '#141b28'))
    f.cbox(0, gtop - 1.5, 0, 3, 3, 7, M('scale', '#141b28', accent='#7fdcff', pattern='vine', pattern_glow=True), 'jaw_guard')
    cur, y = blade(f, gtop - 3, [(6, 8), (5, 8), (4, 7), (3, 6), (2, 4), (1, 2)],
                   M('horn', '#e8eef4', tip='#8fe3ff', glow=True, t0=0, t1=1, flip=True), curve=0.07, name='fang')

@weapon
def kurma(f):
    # 嶺脈岩龍刃 — 山脈の稜線のような岩の大剣、苔と霊脈の光
    gtop, gbot = grip(f, 8, M('wood', '#5a3e28'))
    f.cbox(0, gtop - 1.5, 0, 4, 3, 9, M('rock', '#6a6458', top='#5e9a3a', top_rows=1), 'guard')
    y = gtop - 3
    for k, (w, hh) in enumerate([(7, 7), (7, 7), (6, 6), (5, 5), (3, 4), (1, 2)]):
        f.box(-1, y - hh, -w / 2, 2, hh, w, M('rock', '#8a8478', cracks=True, accent='#c8f08a'), f'ridge{k}')
        y -= hh

@weapon
def teia(f):
    # 光越の翼刃 — 光子の翼のような刃、銀の機構、虹の残光
    gtop, gbot = grip(f, 7, M('metal', '#4a5468', rivets=True))
    f.cbox(0, gtop - 1.5, 0, 3, 3, 6, M('metal', '#a8b4c8', accent='#b5ffff', pattern='circuit', pattern_glow=True), 'engine')
    for k in range(3):
        vane = f.sub(f'vane{k}', 0, gtop - 3, 0, rot=(0.12 * (k - 1), 0, 0))
        vane.box(-0.25, -(26 - k * 5), -2 + k, 0, 26 - k * 5, 3, M('fin', '#c8ffff', root='bottom', rainbow=True), 'vane',
                 faces={'right': M('fin', '#c8ffff', root='bottom', rainbow=True), 'left': M('fin', '#c8ffff', root='bottom', rainbow=True)})
    f.box(-0.5, gtop - 28, -0.5, 1, 25, 1, M('metal', '#e0e8f4', edge_glow='#b5ffff'), 'spine')

@weapon
def bahamut(f):
    # 皇鯨潮龍刃 — 鯨の鰭のような青い刃、珊瑚の鍔、潮の輝き
    gtop, gbot = grip(f, 7, M('scale', '#2f6f8a'))
    for k, c in enumerate(('#ff7a8a', '#ffb07a', '#c88aff')):
        f.box(-0.5, gtop - 3, -3 + k * 2, 1, 3, 1, M('gem', c, glow=False), 'coral')
    cur, y = blade(f, gtop - 3, [(6, 8), (6, 8), (5, 8), (4, 5), (2, 3)], M('scale', '#2f6f8a', belly='#e4efe8', accent='#9fe8d0', pattern='marks'), curve=-0.05, name='fin')
    f.box(-0.75, gtop - 30, -3, 0, 26, 1, M('energy', '#b1f4dc', alpha=200), 'tide')

@weapon
def eomaia(f):
    # 始祖獣牙刃 — 獣の牙の刃、獅子の鬣の房、鹿角の鍔
    gtop, gbot = grip(f, 7, M('fur', '#a78b57'))
    tassel(f, 0, gbot, 0, M('fur', '#5a3a22'), M('fur', '#5a3a22', tip='#c08a40'), length=3, name='mane_tuft')
    for s in (-1, 1):
        a = f.sub('antler' + ('f' if s < 0 else 'b'), 0, gtop - 1, s * 2, rot=(s * 0.8, 0, 0))
        a.box(-0.5, -5, -0.5, 1, 5, 1, M('horn', '#efe4c8', tip='#ffe9a0', glow=True, flip=True), 'antler')
    blade(f, gtop - 2, [(5, 8), (5, 8), (4, 7), (3, 5), (1, 3)], M('horn', '#f4ecd8', tip='#c8a060', t0=0, t1=1, flip=True), curve=0.1, name='fang')

@weapon
def demiurgos(f):
    # 空想現実の黒龍刃 — 黒い鱗の刃に埋め込まれた虹色の宝石、龍の翼膜の鍔
    gtop, gbot = grip(f, 7, M('scale', '#1b2033'))
    pommel(f, gbot, 'gem', M('scale', '#1b2033'), gem('#ae8ff4'))
    for s in (-1, 1):
        w = f.sub('wingguard' + ('f' if s < 0 else 'b'), 0, gtop - 1, s * 2, rot=(s * 0.7, 0, 0))
        w.box(-0.25, -6, -2 if s < 0 else 0, 0, 6, 2, M('membrane', '#2c2648', accent='#ae8ff4'), 'membrane')
    cur, y = blade(f, gtop - 2, [(5, 9), (5, 9), (4, 8), (2, 5), (1, 2)], M('scale', '#1b2033', accent='#ae8ff4', pattern='cracks', pattern_glow=True))
    for k, c in enumerate(('#ff5f7a', '#5fc8ff', '#ffe95f', '#5fff9b')):
        f.cbox(-0.75, gtop - 6 - k * 7, 0, 1, 1, 1, gem(c), 'gem')

def attach(h, char, side='r', always=None):
    """Put `char`'s relic weapon in the hand; staffs and spears are held upright, the rest forward."""
    upright_kinds = {'elseria', 'huang_linghua', 'merlinus'}
    fist = {'taika', 'brutality', 'gokuka', 'shinra'}
    aim = upright(side) if char in upright_kinds else ((0.15, 0, 0) if char in fist else POINT_FORWARD)
    f = held(h, side, aim, always=True if always is None else always)
    WEAPONS[char](f)
    return f

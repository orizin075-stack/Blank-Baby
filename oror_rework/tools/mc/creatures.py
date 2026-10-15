"""Non-humanoid supreme beings, alternate bodies and familiars, in the Minecraft mob style
(blocky silhouettes, texel-painted eyes and markings, flat fins and wings, chained tails).
Each recipe quotes the appearance lines of its setting text."""
import math
from rig import Rig
from paint import M, stack
from humanoid import Humanoid, wing, orbiters
import props as P

RECIPES = {}
def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn

# ------------------------------------------------------------------------------------------------ helpers
def side_eyes(d, rows, col, inset=1, glow=True, width=1):
    """Decals for an eye near the front edge of both side faces of a box of depth d.
    WEST ('right') face: image right = front.  EAST ('left') face: image left = front."""
    out = []
    for y in rows:
        for k in range(width):
            out.append(('right', -1 - inset - k, y, col, glow))
            out.append(('left', inset + k, y, col, glow))
    return out

def yz_fin(color, root_front=False, sweep_back=True, **kw):
    """Face materials for a fin on a YZ plane (dorsal fins, vertical tail fins)."""
    if root_front:     # attached along its front edge (tail fins)
        return {'right': M('fin', color, root='right', **kw), 'left': M('fin', color, root='left', **kw)}
    return {'right': M('fin', color, root='bottom', lean='left' if sweep_back else 'right', **kw),
            'left': M('fin', color, root='bottom', lean='right' if sweep_back else 'left', **kw)}

def xz_fin(color, side, **kw):
    """Face materials for a sideways fin on an XZ plane (pectoral fins). side -1 = right (-X)."""
    root = 'right' if side < 0 else 'left'
    m = M('fin', color, root=root, lean='up', **kw)
    return {'top': m, 'bottom': m}

def chain(r, parent, start, mat, sizes, name='tail', amp=0.14, speed=0.08, ax=1, droop=0.0, tip=None):
    """Tail made of segments along +Z. sizes = [(w, h, length), ...]. ax=1 sways sideways, ax=0 beats up/down."""
    x, y, z = start
    prev = parent
    for i, (w, h, L) in enumerate(sizes):
        b = r.bone(f'{name}{i}', prev, (x, y, z), rot=(droop, 0, 0), anim='tail', i=i, amp=amp, speed=speed, ax=ax)
        m = tip if (tip and i == len(sizes) - 1) else mat
        b.box((x - w / 2, y - h / 2, z), (w, h, L), m, name='seg')
        prev = b
        z += L
    return prev, (x, y, z)

def leg(r, parent, name, anim, x, z, top, w, d, mat, foot=None, claw=None, foot_rows=2):
    """Straight MC leg from `top` down to the ground (y=24)."""
    hgt = 24 - top
    b = r.bone(name, parent, (x, top, z), anim=anim)
    m = stack((mat, hgt - foot_rows), (foot, 99)) if foot else mat
    b.box((x - w / 2, top, z - d / 2), (w, hgt, d), m, name='leg')
    if claw:
        for k in range(int(w)):
            if k % 2 == 0:
                b.box((x - w / 2 + k, 23, z - d / 2 - 1), (1, 1, 1), claw, name='claw')
    return b

QUAD = [('leg_fr', 'leg_r', -1, -1), ('leg_fl', 'leg_l', 1, -1), ('leg_br', 'leg_l', -1, 1), ('leg_bl', 'leg_r', 1, 1)]

def horn_pair(r, parent, at, mat, length, base=2, back=1.1, spread=0.3, name='horn', segs=2):
    """Two horns swept backwards from `at` (x is mirrored)."""
    x0, y0, z0 = at
    for sx in (-1, 1):
        prev = parent
        x, y, z = sx * x0, y0, z0
        L = max(2, int(round(length / segs)))
        bw = base
        for s in range(segs):
            b = r.bone(f'{name}_{"r" if sx < 0 else "l"}{s}', prev, (x, y, z), rot=(-back if s == 0 else -0.3, 0, sx * (spread if s == 0 else -0.1)))
            b.box((x - bw / 2, y - L, z - bw / 2), (bw, L, bw), dict(mat, t0=s / segs, t1=(s + 1) / segs, flip=True), name='h')
            prev = b
            y -= L
            bw = max(1, bw - 1)

def teeth_row(bone, x0, y, z, w, mat=None, down=True):
    bone.box((x0, y, z), (w, 1, 0), mat or M('teeth', '#f2efe6', down=down), name='teeth')

# ================================================================================================ beings
@recipe
def chaos():
    # 万象混沌 カオス — 見るたびに変わる姿：虹色の胎児、紫黒の肉塊、無数の眼球を宿した雲、海をまとった獣、都市の骨の竜。
    # 中心に稀に浮かぶ虹色の核（宝石のように美しく、油膜のように濁り、星雲のように輝く）。上下逆さまの都市、魚の雨。
    r = Rig('chaos', layout=(128, 128))
    flesh = M('oilslick', '#2a1838', hues=['#c050e0', '#40c0d0', '#e060a0', '#f0c040'])
    flesh2 = M('oilslick', '#1c1428', hues=['#8060f0', '#e060a0'])
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=3.0, speed=0.04)
    body = r.bone('mass', root, (0, 12, 0), anim='pulse', amp=0.04, speed=0.05)
    body.cbox((0, 12, 0), (16, 14, 16), flesh, name='mass')
    body.cbox((-6, 6, 3), (9, 7, 9), flesh2, name='lump1')
    body.cbox((7, 15, -2), (7, 9, 9), flesh2, name='lump2')
    body.cbox((-5, 18, -5), (8, 6, 8), flesh, name='lump3')
    body.cbox((3, 4, -3), (6, 4, 6), flesh, name='lump4')
    core = r.bone('core', body, (0, 11, -8.5), anim='pulse', amp=0.14, speed=0.1)
    core.cbox((0, 11, -9), (5, 5, 3), M('rainbow', '#ffffff'), name='core')
    core.cbox((0, 11, -9), (3, 7, 1), M('gem', '#ffffff'), name='core_glint')
    # eyes all over the mass: each eye bone faces outwards (its north face is the iris)
    eyes = [((-5, 8, -8), 0, 3), ((5, 6, -8), 0, 2), ((6, 17, -8), 0, 3), ((-4, 16, -8.5), 0, 2),
            ((8.5, 11, 2), -math.pi / 2, 3), ((-8.5, 13, -1), math.pi / 2, 3), ((-9, 6, 4), math.pi / 2, 2),
            ((2, 5, 8), math.pi, 3), ((-3, 15, 8), math.pi, 2)]
    for i, ((x, y, z), yaw, s) in enumerate(eyes):
        e = r.bone(f'eye{i}', body, (x, y, z), rot=(0, yaw, 0), anim='sway', ax=1, amp=0.12, speed=0.07, phase=i)
        e.box((x - s / 2, y - s / 2, z - 0.5), (s, s, 1), M('eye', ['#69f5f2', '#ff6fd0', '#ffe06a'][i % 3], slit=(i % 2 == 0)), name='eye')
    for i in range(6):
        a = i / 6 * math.tau
        st = (math.cos(a) * 7, 16 + (i % 2) * 3, math.sin(a) * 7)
        t = r.bone(f'tent{i}', body, st, rot=(0.9 * math.sin(a), a, 0))
        chain(r, t, st, M('oilslick', '#2a1838', hues=['#ff6fd0', '#69f5f2']), [(3, 3, 4), (2, 2, 4), (2, 2, 3), (1, 1, 3)],
              name=f't{i}_', amp=0.25, speed=0.08, droop=0.25)
    # fragments of rewritten reality orbiting it
    bits = [('grass', (2, 2, 2)), ('house', (2, 2, 2)), ('fish', (1, 1, 3)), ('crystal', (2, 3, 2)), ('cloud', (3, 2, 2))]
    for i, (kind, s) in enumerate(bits):
        frag = r.bone(f'chaos{i}', root, (0, 8 - i, 0), anim='chaos', phase=i * 1.3)
        a = i / 5 * math.tau
        c = (math.cos(a) * 15, -2 - i * 2, math.sin(a) * 15)
        if kind == 'grass':
            frag.cbox(c, s, M('rock', '#7a5a3a', top='#5e9a3a'), name='block')
        elif kind == 'house':      # an upside-down house (roof pointing down)
            frag.cbox(c, s, M('wood', '#c8a070'), name='house')
            frag.cbox((c[0], c[1] + 1.5, c[2]), (3, 1, 3), M('cloth', '#a03a2a'), name='roof')
        elif kind == 'fish':
            frag.cbox(c, s, M('scale', '#f0a040', belly='#fff0d0'), name='fish')
        elif kind == 'crystal':
            frag.cbox(c, s, M('rainbow', '#ffffff'), name='shard')
        else:
            frag.cbox(c, s, M('eye', '#69f5f2', slit=True), name='eyecloud')
    return r

@recipe
def mels():
    # 至高武王 メルス — 直径五十センチほどの透明な不定形の球体。目も口もない。流動する戦闘機構。
    # 内部に世界最硬の核。音速を超えて刃・槍・鎚・盾・弓へ変形する。
    r = Rig('mels', layout=(64, 64), translucent=True)
    root = r.bone('root', None, (0, 24, 0), anim='root')
    core = r.bone('core', root, (0, 20, 0), anim='pulse', amp=0.06, speed=0.07)
    core.cbox((0, 20, 0), (2, 2, 2), M('gem', '#d8f6ff'), name='core')
    body = r.bone('body', root, (0, 24, 0), anim='liquid', amp=0.07)
    gel = M('slime', '#a8e8ff', alpha=110, round_corners=True)
    body.box((-4, 16, -4), (8, 8, 8), gel, name='sphere')
    return r

@recipe
def hephaistos():
    # 典域工廠 ヘファイストス — 水晶とも未知の金属ともつかないSFじみたキューブを核とした球状の機械。
    # 周囲に大小の機械球体が浮遊し、それぞれが腕であり、眼であり、炉であり、工房であり、兵器でもある。
    r = Rig('hephaistos')
    shell = M('metal', '#4a627a', accent='#52e8d6', pattern='circuit', pattern_glow=True)
    plate = M('metal', '#8aa0b4', rivets=True)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=2.0, speed=0.05)
    body = r.bone('body', root, (0, 12, 0), anim='spin', speed=0.008, cast=0.0)
    body.cbox((0, 12, 0), (14, 10, 14), shell, name='belt')
    body.cbox((0, 12, 0), (10, 14, 10), plate, name='pole')
    body.cbox((0, 12, 0), (12, 12, 12), M('metal', '#5a7088', accent='#52e8d6', pattern='rings'), name='shell')
    for sx in (-1, 1):
        body.cbox((sx * 7.5, 12, 0), (1, 4, 4), M('energy', '#52e8d6'), name='vent')
    core = r.bone('core', root, (0, 12, -7.5), anim='spin', ax=2, speed=0.05)
    core.cbox((0, 12, -7.5), (5, 5, 5), M('gem', '#a5f3ff'), name='cube')
    core.cbox((0, 12, -7.5), (3, 3, 6), M('energy', '#e8ffff'), name='cube_light')
    ring = r.bone('ring', root, (0, 12, 0), rot=(1.3, 0, 0.2), anim='spin', speed=0.03)
    ring.box((-12, 12, -12), (24, 0, 24), M('ring', '#52e8d6', width=0.06, spikes=16, glow_amount=0.6), name='ring')
    hub = r.bone('foundries', root, (0, 10, 0), anim='spin', speed=0.025)
    kinds = ['eye', 'arm', 'furnace', 'workshop', 'cannon']
    for i, kind in enumerate(kinds):
        a = 2 * math.pi * i / len(kinds)
        px, pz = math.cos(a) * 14, math.sin(a) * 14
        b = r.bone(f'foundry_{kind}', hub, (px, 10, pz), anim='float', amp=1.0, speed=0.08, phase=i * 1.7)
        b.cbox((px, 10, pz), (4, 3, 4), M('metal', '#5a7088', accent='#52e8d6', pattern='rings'), name='orb')
        b.cbox((px, 10, pz), (3, 4, 3), M('metal', '#8aa0b4', rivets=True), name='orb2')
        if kind == 'eye':
            b.cbox((px, 10, pz - 2), (2, 2, 1), M('gem', '#52e8d6'), name='lens')
        elif kind == 'arm':
            b.box((px - 0.5, 11.5, pz - 0.5), (1, 4, 1), M('metal', '#b0c0d0'), name='arm')
            b.box((px - 1, 15.5, pz - 0.5), (2, 1, 1), M('metal', '#b0c0d0'), name='claw')
        elif kind == 'furnace':
            b.cbox((px, 10, pz - 2), (2, 1, 1), M('energy', '#ff9a40'), name='fire')
        elif kind == 'workshop':
            b.cbox((px, 7.5, pz), (1, 1, 1), M('energy', '#fff0a0'), name='spark')
        else:
            b.box((px - 0.5, 9.5, pz - 5), (1, 1, 3), M('metal', '#2a3440'), name='barrel')
    return r

@recipe
def enkou():
    # 災極海獣 淵煌 — サメの鋭利さ、シャチの俊敏さ、竜の威厳。黒曜石のような鱗、深海魚の灯火のように青白く輝く瞳。
    # 体表に海洋生物の意匠を思わせる文様（鱗であり、魔術回路であり、深海の記憶の紋章）。
    r = Rig('enkou', layout=(256, 128))
    belly = '#cfdce6'
    hide = M('scale', '#141b28', belly=belly, belly_frac=0.36, accent='#7fdcff', pattern='vine', pattern_glow=True, glow_amount=0.55)
    plain = M('scale', '#141b28', belly=belly, belly_frac=0.36)
    eye = '#bff4ff'
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.5, speed=0.05)
    body = r.bone('body', root, (0, 14, 0), anim='sway', ax=1, amp=0.05, speed=0.06)
    body.cbox((0, 14, 0), (12, 11, 22), hide, name='torso')
    body.cbox((0, 8.5, 1), (8, 1, 16), M('scale', '#0e141e'), name='ridge')
    dor = r.bone('dorsal', body, (0, 8, -2), rot=(0, 0, 0), anim='sway', ax=2, amp=0.03, speed=0.07)
    dor.box((0, 0, -4), (0, 8, 10), M('fin', '#0e141e'), name='dorsal',
            faces=yz_fin('#1e2a3c', edge='#5fb8e0', glow_amount=0.3))
    for sx in (-1, 1):
        fb = r.bone('fin_' + ('r' if sx < 0 else 'l'), body, (sx * 6, 18, -5), rot=(0.25, sx * 0.45, sx * -0.55),
                    anim='sway', ax=2, amp=0.12, speed=0.08, phase=sx)
        fb.box((sx * 6 + (0 if sx > 0 else -10), 18, -8), (10, 0, 7), M('fin', '#0e141e'), name='pectoral',
               faces=xz_fin('#1e2a3c', sx, edge='#5fb8e0', glow_amount=0.3))
    # head: flat shark wedge with an orca eye-patch and lantern eyes
    head = r.bone('head', body, (0, 13, -11), anim='head')
    hm = M('decal', '#141b28', base=plain,
           decals=side_eyes(10, [3], eye, inset=2, width=2) + side_eyes(10, [1, 2], '#e6eef4', inset=1, glow=False, width=3)
           + [('right', -9, y, '#0a0e16') for y in (5, 6, 7)] + [('left', 8, y, '#0a0e16') for y in (5, 6, 7)])
    head.cbox((0, 13.5, -16), (10, 9, 10), hm, name='skull')
    head.cbox((0, 15, -23.5), (8, 6, 5), M('decal', '#141b28', base=plain, decals=[('front', 2, 1, '#0a0e16'), ('front', 5, 1, '#0a0e16')]),
              name='snout')
    teeth_row(head, -3.5, 18, -26.01, 7)
    for sx in (-1, 1):
        head.box((sx * 3.75 - (0 if sx > 0 else 0), 18, -25.5), (0, 1, 8), M('teeth', '#f2efe6'), name='teeth_side')
    horn_pair(r, head, (3, 9.5, -14), M('horn', '#20283a', tip='#8fe3ff', glow=True), 9, base=2, back=1.25, spread=0.25)
    jaw = r.bone('jaw', head, (0, 18, -12), anim='jaw')
    jaw.box((-3.5, 18, -25), (7, 3, 13), M('scale', '#141b28', belly=belly, belly_frac=0.67), name='jaw')
    teeth_row(jaw, -3, 17, -24.9, 6, down=False)
    # shark/dragon tail with a tall forked caudal fin
    end, (x, y, z) = chain(r, body, (0, 14, 11), hide, [(9, 9, 5), (7, 7, 5), (5, 5, 5), (3, 4, 4)], amp=0.16, speed=0.07)
    cf = r.bone('caudal', end, (x, y, z))
    cf.box((0, y - 8, z - 1), (0, 16, 8), M('fin', '#0e141e'), name='caudal',
           faces=yz_fin('#1e2a3c', root_front=True, fork=True, edge='#5fb8e0', glow_amount=0.3))
    return r

@recipe
def kurma():
    # 嶺脈地龍 クールマ — 巨大な山脈を背負う地龍。稜線は背、谷は鱗の隙間、山頂の岩壁は角や甲殻の一部。
    # 背の山々には独自の生態系、霊脈の魔力、豊穣。老賢者のように穏やか。
    r = Rig('kurma', layout=(256, 256))
    hide = M('scale', '#6b7558', belly='#b8ae8a', belly_frac=0.3)
    rock = M('rock', '#7a7466', top='#5e9a3a', top_rows=2)
    snow = M('rock', '#8a8478', top='#f2f6fa', top_rows=3)
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 12, 0), anim='breath')
    body.cbox((0, 15, 0), (24, 8, 30), hide, name='plastron')
    body.cbox((0, 10.5, 0), (30, 3, 34), M('rock', '#5f5a50', top='#5e9a3a', cracks=True, accent='#c8f08a'), name='rim')
    body.cbox((0, 7, 0), (26, 4, 30), rock, name='dome')
    body.cbox((0, 3.5, 0), (20, 3, 24), rock, name='dome2')
    for (x, z, w, h) in [(-2, -1, 10, 12), (6, 6, 8, 9), (-8, 7, 7, 7), (7, -7, 6, 6)]:
        body.box((x - w / 2, 2 - h, z - w / 2), (w, h, w), snow if h >= 9 else rock, name='peak')
    body.box((-4.5, -15, -3.5), (5, 5, 5), snow, name='summit')
    for (x, z) in [(-10, -4), (11, -1), (2, 10), (-6, -10), (9, 10), (-11, 9)]:
        body.box((x - 0.5, -1, z - 0.5), (1, 3, 1), M('wood', '#5a3e28'), name='trunk')
        body.box((x - 1.5, -4, z - 1.5), (3, 3, 3), M('leaf', '#3e7a2e', holes=0.05), name='tree')
    head = r.bone('head', body, (0, 14, -15), anim='head')
    head.cbox((0, 14.5, -17), (8, 7, 6), hide, name='neck')
    head.cbox((0, 14, -24), (10, 8, 10), M('decal', '#6b7558', base=hide, decals=side_eyes(10, [3], '#e8ffb0', inset=2, width=2)),
              name='skull')
    head.cbox((0, 15.5, -30.5), (8, 5, 3), M('decal', '#6b7558', base=hide, decals=[('front', 2, 1, '#2a2e22'), ('front', 5, 1, '#2a2e22')]),
              name='beak')
    head.box((-3, 17, -32.25), (6, 1, 0), M('cloth', '#e8e0c0'), name='lip')
    horn_pair(r, head, (3.5, 10, -22), M('rock', '#9a9282', top='#f2f6fa', top_rows=1), 8, base=2, back=1.0, spread=0.35)
    for name, anim, sx, sz in QUAD:
        leg(r, body, name, anim, sx * 10, sz * 10, 17, 7, 7, hide, foot=M('rock', '#4a463c'), claw=M('horn', '#e8e0c0', tip='#9a9070'))
    chain(r, body, (0, 14, 15), hide, [(5, 5, 4), (4, 4, 4), (3, 3, 3)], amp=0.08, speed=0.05, droop=0.2)
    return r

@recipe
def teia():
    # 光越天龍 テイア — 機械と融合したかのような金属質の外殻の小型の龍。光子の流れを模した翼、飛行中は虹色の残光。
    # 魔力を光子へ変換する推進器官。快活で陽気な兄貴分。
    r = Rig('teia')
    metal = M('metal', '#a8b4c8', accent='#b5ffff', pattern='circuit', pattern_glow=True, glow_amount=0.5)
    dark = M('metal', '#4a5468', rivets=True)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=4.0, speed=0.08)
    body = r.bone('body', root, (0, 14, 0), anim='sway', ax=0, amp=0.05, speed=0.08)
    body.cbox((0, 14, 0), (8, 7, 13), metal, name='torso')
    body.cbox((0, 10, -2), (6, 1, 6), M('metal', '#c8d2e0', rivets=True), name='shoulder_plate')
    body.cbox((0, 16.5, 0), (5, 1, 10), dark, name='keel')
    for i, z in enumerate((-3, 0, 3)):
        body.cbox((0, 10.5, z), (1, 1, 2), M('energy', '#b5ffff'), name='spine')
    for sx in (-1, 1):
        body.cbox((sx * 2, 12, 6.5), (2, 2, 1), M('energy', '#ffffff'), name='thruster')
    neck = r.bone('neck', body, (0, 13, -6), rot=(-0.4, 0, 0))
    neck.cbox((0, 13, -8.5), (4, 4, 5), metal, name='neck')
    head = r.bone('head', neck, (0, 12, -11), anim='head')
    hm = M('decal', '#c8d2e0', base=M('metal', '#c8d2e0', accent='#b5ffff', pattern='gold_lines', pattern_glow=True, glow_amount=0.4),
           decals=side_eyes(7, [2], '#e0ffff', inset=1, width=3))
    head.cbox((0, 12, -14.5), (6, 5, 7), hm, name='skull')
    head.cbox((0, 13, -19.5), (4, 3, 4), metal, name='snout')
    head.box((-2, 11.75, -21.51), (4, 1, 0), M('energy', '#b5ffff'), name='visor')
    horn_pair(r, head, (2, 9.5, -13), M('horn', '#e0e8f4', tip='#b5ffff', glow=True), 7, base=1, back=1.3, spread=0.15)
    for name, anim, sx, sz in QUAD:
        b = r.bone(name, body, (sx * 2.5, 16.5, sz * 4), rot=(0.9, 0, 0), anim=anim)
        b.box((sx * 2.5 - 1, 16.5, sz * 4 - 1), (2, 4, 2), dark, name='leg')
    # photon wings: a metal spar with vanes of light; flap up/down
    for sx in (-1, 1):
        nm = 'wing_' + ('r' if sx < 0 else 'l')
        wb = r.bone(nm, body, (sx * 4, 11, -2), rot=(0, sx * 0.25, sx * -0.55), anim=nm, ax=2, amp=0.28, speed=0.16)
        wb.box((sx * 4 + (0 if sx > 0 else -14), 10.5, -2.5), (14, 1, 1), dark, name='spar')
        wb.box((sx * 4 + (0 if sx > 0 else -16), 11, -2), (16, 0, 12), M('fin', '#c8ffff'), name='vane',
               faces=xz_fin('#c8ffff', sx, rainbow=True))
    end, (x, y, z) = chain(r, body, (0, 14, 6), metal, [(3, 3, 4), (3, 3, 4), (2, 2, 4), (2, 2, 4), (1, 1, 4)], amp=0.2, speed=0.1)
    tr = r.bone('trail', end, (x, y, z))
    tr.box((0, y - 3, z - 1), (0, 6, 12), M('fin', '#ffffff'), name='trail',
           faces={'right': M('fin', '#ffffff', root='right', rainbow=True, alpha=200), 'left': M('fin', '#ffffff', root='left', rainbow=True, alpha=200)})
    return r

@recipe
def bahamut():
    # 大海皇鯨 バハムート — 鯨の滑らかな流線型の体躯に龍の鱗と角、背には潮を巻き上げる巨大なヒレ。
    # 背には珊瑚礁と植物が根付き独自の生態系。おっとりとした海の調停者。
    r = Rig('bahamut', layout=(256, 256))
    hide = M('scale', '#2f6f8a', belly='#e4efe8', belly_frac=0.3, back='#245a72', accent='#9fe8d0', pattern='marks')
    plain = M('scale', '#2f6f8a', belly='#e4efe8', belly_frac=0.3, back='#245a72')
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.0, speed=0.03)
    body = r.bone('body', root, (0, 13, 0), anim='sway', ax=1, amp=0.03, speed=0.04)
    body.cbox((0, 13, 0), (18, 14, 30), hide, name='torso')
    body.cbox((0, 5, 0), (14, 2, 26), plain, name='back')
    body.cbox((0, 21, 0), (14, 2, 26), M('cloth', '#e4efe8', accent='#b8ccc4', pattern='stripes'), name='grooves')
    # coral reef and seaweed growing on the back
    corals = [(-4, -6, '#ff7a8a', 3), (3, 2, '#ffb07a', 4), (-2, 9, '#c88aff', 3), (5, -9, '#7affc8', 2), (0, -2, '#ff7ab0', 3), (-5, 3, '#ffe07a', 2)]
    for (x, z, c, h) in corals:
        body.box((x - 1, 4 - h, z - 1), (2, h, 2), M('gem', c, glow=False), name='coral')
        body.box((x - 1.5, 4 - h - 1, z - 0.5), (3, 1, 1), M('gem', c, glow=False), name='coral_branch')
    for (x, z) in [(-6, 6), (6, -4), (1, 11), (-3, -11)]:
        body.box((x, -2, z - 1.5), (0, 6, 3), M('leaf', '#3a9a6a', holes=0.2), name='kelp')
    sail = r.bone('sail', body, (0, 4, -4), rot=(-0.15, 0, 0), anim='sway', ax=2, amp=0.03, speed=0.04)
    sail.box((0, -8, -6), (0, 12, 14), M('fin', '#2a6a7a'), name='sail', faces=yz_fin('#2a6a7a', rays='#9fe8d0', edge='#8fd4c0', glow_amount=0.3))
    head = r.bone('head', body, (0, 13, -15), anim='head')
    hm = M('decal', '#2f6f8a', base=plain, decals=side_eyes(12, [5], '#e0fff4', inset=3, width=2) + side_eyes(12, [4, 6], '#163a48', inset=3, glow=False, width=2))
    head.cbox((0, 13.5, -21), (16, 12, 12), hm, name='skull')
    head.cbox((0, 8, -20), (12, 2, 8), plain, name='brow')
    horn_pair(r, head, (5, 8, -18), M('horn', '#e8f4ee', tip='#9fe8d0', glow=True), 10, base=2, back=1.15, spread=0.35)
    jaw = r.bone('jaw', head, (0, 19, -16), anim='jaw')
    jaw.box((-7, 19, -27), (14, 3, 11), M('cloth', '#e4efe8', accent='#b8ccc4', pattern='stripes'), name='jaw')
    for sx in (-1, 1):
        fb = r.bone('fin_' + ('r' if sx < 0 else 'l'), body, (sx * 9, 17, -7), rot=(0.2, sx * 0.35, sx * -0.6),
                    anim='sway', ax=2, amp=0.1, speed=0.05, phase=sx)
        fb.box((sx * 9 + (0 if sx > 0 else -14), 17, -10), (14, 0, 7), M('fin', '#2a6a7a'), name='flipper',
               faces=xz_fin('#2a6a7a', sx, edge='#8fd4c0', glow_amount=0.25))
    end, (x, y, z) = chain(r, body, (0, 13, 15), hide, [(13, 10, 6), (10, 8, 6), (7, 6, 6), (4, 4, 5)], amp=0.07, speed=0.04, ax=0)
    fl = r.bone('fluke', end, (x, y, z))
    fl.box((-12, y, z - 1), (24, 0, 9), M('fin', '#2a6a7a'), name='fluke',
           faces={'top': M('fin', '#2a6a7a', root='bottom', fork=True, edge='#8fd4c0', glow_amount=0.25),
                  'bottom': M('fin', '#2a6a7a', root='bottom', fork=True)})
    return r

@recipe
def eomaia():
    # 始祖神獣 エオマイア — 獅子の鬣、狼の牙、蛇の鱗、鳥の翼、魚の鰭、象の牙、鹿の角、獣の爪。
    # すべての獣性が調和した原初の完全体。傲岸不遜な王にして母。
    r = Rig('eomaia', layout=(256, 128))
    fur = M('fur', '#b8935a')
    mane = M('fur', '#5a3a22', tip='#c08a40')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 12, 0), anim='breath')
    body.cbox((0, 12, 0), (12, 10, 20), fur, name='torso')
    body.cbox((0, 7, -5), (10, 2, 8), M('fur', '#5a3a22'), name='mane_back')
    head = r.bone('head', body, (0, 9, -10), anim='head')
    head.cbox((0, 9.5, -11), (15, 14, 5), mane, name='mane')
    hm = M('decal', '#b8935a', base=fur, decals=[('front', 2, 2, '#ffd76a', True), ('front', 6, 2, '#ffd76a', True),
                                                  ('front', 1, 2, '#3a2414'), ('front', 7, 2, '#3a2414')])
    head.cbox((0, 9.5, -15.5), (9, 8, 6), hm, name='skull')
    head.cbox((0, 12, -20.5), (6, 4, 4), M('decal', '#d8b88a', base=M('fur', '#d8b88a'), decals=[('front', 2, 0, '#2a1a10'), ('front', 3, 0, '#2a1a10')]),
              name='muzzle')
    teeth_row(head, -2.5, 14, -22.51, 5)
    for sx in (-1, 1):
        t = r.bone('tusk_' + ('r' if sx < 0 else 'l'), head, (sx * 2.5, 13.5, -21), rot=(-0.6, 0, sx * 0.2))
        t.box((sx * 2.5 - 0.5, 13.5, -21.5), (1, 4, 1), M('horn', '#f4ecd8', tip='#d8c8a0'), name='tusk')
        ear = r.bone('ear_' + ('r' if sx < 0 else 'l'), head, (sx * 3.5, 5.5, -14), rot=(0, 0, sx * 0.3))
        ear.box((sx * 3.5 - 1, 3.5, -14.5), (2, 2, 1), fur, name='ear')
        ant = r.bone('antler_' + ('r' if sx < 0 else 'l'), head, (sx * 2.5, 5.5, -14), rot=(-0.3, 0, sx * 0.55))
        ant.box((sx * 2.5 - 0.5, 5.5 - 10, -14.5), (1, 10, 1), M('horn', '#efe4c8', tip='#ffe9a0', glow=True, flip=True), name='beam')
        for k in range(2):
            yy = 5.5 - 4 - 3 * k
            tn = r.bone(f'antler_{"r" if sx < 0 else "l"}_t{k}', ant, (sx * 2.5, yy, -14), rot=(0, 0, sx * 0.95))
            tn.box((sx * 2.5 - 0.5, yy - 4, -14.5), (1, 4, 1), M('horn', '#efe4c8', tip='#ffe9a0', glow=True, flip=True), name='tine')
    for name, anim, sx, sz in QUAD:
        lg = leg(r, body, name, anim, sx * 4, sz * 7, 17, 4, 4, fur, foot=M('fur', '#5a3a22'), claw=M('horn', '#2a2420', tip='#f0e8d8'))
        if sz < 0:   # fish fins on the forelegs
            lg.box((sx * 6.25, 17, -7 + 1.5), (0, 4, 4), M('fin', '#6aa8c0'), name='fin',
                   faces={'right': M('fin', '#6aa8c0', root='right', lean='down', edge='#bff0ff', glow_amount=0.3),
                          'left': M('fin', '#6aa8c0', root='left', lean='down', edge='#bff0ff', glow_amount=0.3)})
    for sx in (-1, 1):
        w = wing(r, body, sx, (sx * 5, 7.5, -3), 'feather', M('feather', '#7a5a34', tip='#f0e0b0'), span=16, height=11, rest=0.7)
        w.rot = (-0.35, sx * -0.7, sx * -0.55)
    chain(r, body, (0, 10, 10), M('scale', '#4a7a3a', belly='#c8d8a0'), [(3, 3, 4), (3, 3, 4), (2, 2, 4), (2, 2, 3), (1, 1, 3)],
          amp=0.2, speed=0.09, droop=0.3, tip=M('scale', '#2a4a22', belly='#c8d8a0'))
    return r

@recipe
def demiurgos():
    # 空創龍王 デミウルゴス — 黒色の鱗に、所々虹色の宝石を埋め込んだような輝きを宿す五メートルほどの小型の龍。
    # 威圧よりも神秘を感じさせる姿。
    r = Rig('demiurgos')
    sc = M('scale', '#1b2033', belly='#3a3a5a', belly_frac=0.3)
    gems = ['#ff5f7a', '#5fc8ff', '#ffe95f', '#b05fff', '#5fff9b', '#ff9f4f']
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.0, speed=0.05)
    body = r.bone('body', root, (0, 14, 0), anim='breath')
    body.cbox((0, 14, 0), (10, 9, 16), sc, name='torso')
    for i, (x, y, z) in enumerate([(-3, 9, -4), (2, 9, 1), (-1, 9, 5), (3, 9, -6), (0, 9, -1), (-4, 12, 2), (4, 13, -2), (4, 11, 4)]):
        body.cbox((x, y, z), (1, 1, 1), M('gem', gems[i % len(gems)]), name='gem')
    neck = r.bone('neck', body, (0, 12, -8), rot=(-0.5, 0, 0))
    neck.cbox((0, 12, -11.5), (5, 5, 7), sc, name='neck')
    head = r.bone('head', neck, (0, 11, -15), anim='head')
    head.cbox((0, 10.5, -18.5), (7, 6, 8), M('decal', '#1b2033', base=sc, decals=side_eyes(8, [2], '#c8a0ff', inset=1, width=2)), name='skull')
    head.cbox((0, 11.5, -24.5), (5, 4, 5), M('decal', '#1b2033', base=sc, decals=[('front', 1, 0, '#0a0c14'), ('front', 3, 0, '#0a0c14')]), name='snout')
    head.cbox((0, 7, -19), (1, 1, 1), M('gem', '#ffffff'), name='brow_gem')
    horn_pair(r, head, (2.5, 8, -16), M('horn', '#20203a', tip='#ae8ff4', glow=True), 8, base=2, back=1.2, spread=0.3)
    jaw = r.bone('jaw', head, (0, 13.5, -16), anim='jaw')
    jaw.box((-2, 13.5, -26.5), (4, 1, 8), sc, name='jaw')
    teeth_row(jaw, -2, 12.5, -26.4, 4, down=False)
    for sx in (-1, 1):
        nm = 'wing_' + ('r' if sx < 0 else 'l')
        wb = r.bone(nm, body, (sx * 5, 10, -3), rot=(0.1, sx * 0.2, sx * -0.6), anim=nm, ax=2, amp=0.22, speed=0.1)
        span = 18
        wb.box((sx * 5 + (0 if sx > 0 else -span), 9.5, -3.5), (span, 1, 1), M('horn', '#20203a', tip='#ae8ff4'), name='arm')
        wb.box((sx * 5 + (0 if sx > 0 else -span), 10, -3), (span, 0, 13), M('membrane', '#2c2648', accent='#ae8ff4', glow_edge='#ae8ff4'), name='membrane')
        for k in range(1, 4):
            fx = sx * 5 + sx * span * k / 4
            f = r.bone(f'{nm}_finger{k}', wb, (fx, 10, -3), rot=(0, sx * (0.25 * k - 0.55), 0))
            f.box((fx - 0.5, 9.75, -3), (1, 1, int(13 * (0.6 + 0.12 * k))), M('horn', '#20203a', tip='#ae8ff4'), name='finger')
    for name, anim, sx, sz in QUAD:
        leg(r, body, name, anim, sx * 3.5, sz * 5, 18, 3, 3, sc, foot=M('scale', '#10141f'), claw=M('horn', '#20203a', tip='#ae8ff4'))
    chain(r, body, (0, 14, 8), sc, [(4, 4, 4), (3, 3, 4), (3, 3, 4), (2, 2, 4), (2, 2, 3), (1, 1, 3)], amp=0.18, speed=0.08,
          droop=0.08, tip=M('gem', '#ae8ff4'))
    return r

@recipe
def yggdrasil():
    # 玖天神樹 イグドラシル — 天を突く超巨大な樹。雲海を貫く幹、九つの世界を抱擁する枝葉。魔力の大動脈。
    # 花が一輪咲くだけで周囲が神域の魔力濃度に。内部に九つの世界。
    r = Rig('yggdrasil', layout=(256, 256))
    bark = M('wood', '#5a4430', veins='#d8ff8a', glow_amount=0.45)
    leaf = M('leaf', '#477449', flowers=['#ffe0f0', '#fff0a0'], flower_glow=True)
    leaf2 = M('leaf', '#5a9a4a', flowers=['#ffffff', '#ffd0e8'], flower_glow=True)
    root = r.bone('root', None, (0, 24, 0), anim='root')
    trunk = r.bone('trunk', root, (0, 24, 0), anim='sway', ax=2, amp=0.01, speed=0.03)
    trunk.box((-5, -16, -5), (10, 40, 10), bark, name='trunk')
    trunk.box((-7, 18, -7), (14, 6, 14), bark, name='base')
    for i in range(6):
        a = i / 6 * math.tau
        rb = r.bone(f'root{i}', trunk, (math.cos(a) * 7, 22, math.sin(a) * 7), rot=(0, -a + math.pi / 2, 0))
        rb.box((math.cos(a) * 7 - 1.5, 21, math.sin(a) * 7), (3, 3, 7), M('wood', '#4a3626'), name='root')
    heart = r.bone('heart', trunk, (0, 4, -5.5), anim='pulse', amp=0.1, speed=0.06)
    heart.cbox((0, 4, -5.5), (3, 4, 1), M('gem', '#c8ff8a'), name='heart')
    for i in range(5):
        a = i / 5 * math.tau + 0.4
        y = -10 - (i % 2) * 5
        br = r.bone(f'branch{i}', trunk, (math.cos(a) * 4, y, math.sin(a) * 4), rot=(math.sin(a) * 0.9, 0, -math.cos(a) * 0.9),
                    anim='sway', ax=2, amp=0.02, speed=0.04, phase=i)
        br.box((math.cos(a) * 4 - 1.5, y - 14, math.sin(a) * 4 - 1.5), (3, 14, 3), bark, name='branch')
        br.box((math.cos(a) * 4 - 6, y - 22, math.sin(a) * 4 - 6), (12, 8, 12), leaf if i % 2 else leaf2, name='crown')
    trunk.box((-15, -30, -15), (30, 10, 30), leaf2, name='canopy')
    trunk.box((-11, -38, -11), (22, 8, 22), leaf, name='canopy2')
    trunk.box((-7, -44, -7), (14, 6, 14), leaf2, name='canopy3')
    worlds = ['#ffd06a', '#8ad0ff', '#ff8aa8', '#a0ff8a', '#d0a0ff', '#ffffff', '#ff9a50', '#60e0d0', '#f0f080']
    hub = r.bone('worlds', trunk, (0, -22, 0), anim='spin', speed=0.01)
    for i, col in enumerate(worlds):
        a = i / 9 * math.tau
        px, pz = math.cos(a) * 19, math.sin(a) * 19
        b = r.bone(f'world{i}', hub, (px, -18 + (i % 3) * 3, pz), anim='float', amp=0.6, speed=0.06, phase=i)
        b.cbox((px, -18 + (i % 3) * 3, pz), (2, 2, 2), M('gem', col), name='world')
    return r

@recipe
def nun():
    # 天変万化 ヌン — 黒く蠢く粘性を帯びた魔質の塊。あらゆる形へ変わる。自らを愚者と称する旅人、道化にして哲人。
    r = Rig('nun')
    h = Humanoid(r, 'child', skin='#21182d', accent='#a681d9')
    goo = M('oilslick', '#1c1426', hues=['#a681d9', '#6a4a9a', '#e8d070'])
    h.body(top_mat=goo, bottom_mat=goo, legs_mat=goo, boots_mat=None, arms_mat=goo, hands_mat=goo, neck=None)
    h.robe(dict(goo, drips=True), flare=3.0)
    h.head_cube({'skin': '#1c1426', 'eye_tpl': 'void', 'brows': False, 'mouth': 'none', 'blink': False}, skin=M('oilslick', '#1c1426', hues=['#a681d9']))
    # the fool's mask and jester cap
    mask = r.bone('mask', h.head, (0, h.head_top, -4.5), anim='sway', ax=2, amp=0.04, speed=0.05)
    decals = [('front', x, y, '#c090ff', True) for (x, y) in ((1, 2), (2, 2), (4, 2), (5, 2))]
    decals += [('front', x, 5, '#2a1a30') for x in (1, 5)] + [('front', x, 6, '#2a1a30') for x in (2, 3, 4)]
    decals += [('front', 3, 0, '#e8d070'), ('front', 3, 1, '#e8d070')]
    mask.box((-3.5, h.head_top + 0.5, -4.5), (7, 7, 0), M('decal', '#f4f0e8', base=M('cloth', '#f4f0e8', hem_shadow=False), decals=decals), name='mask')
    cap = r.bone('jester', h.head, (0, h.head_top, 0))
    cap.box((-4.5, h.head_top - 1, -4.5), (9, 2, 9), M('cloth', '#2a2036', accent='#e8d070', trim_top=True), faces={'bottom': None}, name='band')
    for sx in (-1, 1):
        cb = r.bone('jester_' + ('r' if sx < 0 else 'l'), cap, (sx * 2.5, h.head_top - 1, 0), rot=(0, 0, sx * 1.0), anim='sway', ax=2,
                    amp=0.08, speed=0.07, phase=sx)
        cb.box((sx * 2.5 - 1.5, h.head_top - 7, -1.5), (3, 6, 3), M('cloth', '#2a2036' if sx < 0 else '#7a58b0'), name='flap')
        cb.cbox((sx * 2.5, h.head_top - 7.5, 0), (1, 1, 1), M('metal', '#e8d070'), name='bell')
    for i in range(5):
        a = i / 5 * math.tau
        st = (math.cos(a) * 3, 23, math.sin(a) * 3)
        d = r.bone(f'drip{i}', h.root, st, anim='sway', ax=0, amp=0.1, speed=0.09, phase=i)
        d.box((st[0] - 0.5, 23, st[2] - 0.5), (1, 1, 1), M('slime', '#2a1e3a', alpha=220), name='drip')
    return r

@recipe
def forbidden_arcana():
    # 外悪の魔導 — 固定された姿はない。青年、少女、老人、影、衣服だけの人型、声だけ。
    # 魔法陣・古代遺跡・魔導書・術式網へ思考を分散させた、知識だけが歩き続ける天災。
    r = Rig('forbidden_arcana')
    h = Humanoid(r, 'youth', skin='#151229', accent='#a883ee', hover=3.0)
    robe = M('cloth', '#2a2050', accent='#a883ee', trim=1, pattern='runes', pattern_glow=True, glow_amount=0.45)
    empty = M('void', '#100c1e', accent='#a883ee', alpha=0)
    h.body(top_mat=robe, bottom_mat=robe, legs_mat=empty, boots_mat=None, arms_mat=robe,
           hands_mat=M('void', '#151229', accent='#a883ee'), neck=None)
    h.robe(dict(robe, cut=None), flare=3.0)
    h.head_cube({'eye_tpl': 'void', 'glow_eyes': True, 'skin': '#05040a', 'line': '#05040a', 'brows': False, 'mouth': 'none', 'blink': False},
                skin=M('void', '#05040a', accent='#a883ee'))
    hood = r.bone('hood', h.head, (0, h.head_top, 0))
    hood.box((-4, h.head_top, -4), (8, 8, 8), M('hood', '#2a2050', accent='#a883ee'), grow=0.9, name='hood')
    hood.box((-2, h.head_top - 3, 1), (4, 3, 4), M('cloth', '#2a2050'), name='hood_tip')
    circle = r.bone('circle', h.root, (0, 23.8, 0), anim='spin', speed=0.03)
    circle.box((-12, 23.8, -12), (24, 0, 24), M('ring', '#a883ee', width=0.06, inner=0.85, poly=5, glow_amount=0.6), name='circle')
    hub = r.bone('tomes', h.torso, (0, h.top + 4, 0), anim='spin', speed=0.02)
    for i in range(3):
        a = i / 3 * math.tau
        x, z = math.cos(a) * 9, math.sin(a) * 9
        bk = r.bone(f'tome{i}', hub, (x, h.top + 4 - i * 2, z), anim='float', amp=0.6, speed=0.07, phase=i * 2)
        P.book(bk, (x, h.top + 4 - i * 2, z), M('cloth', ['#3a1a5a', '#1a3a5a', '#5a1a3a'][i], accent='#a883ee', pattern='runes', pattern_glow=True),
               M('cloth', '#e8e0c8'))
    return r

# ================================================================================================ familiars
@recipe
def familiar_drone():
    # ヘファイストス／ヴァレリア系の工廠球体
    r = Rig('familiar_drone', layout=(64, 64))
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=2.0, speed=0.1)
    b = r.bone('body', root, (0, 18, 0), anim='spin', speed=0.03, cast=0.0)
    b.cbox((0, 18, 0), (5, 4, 5), M('metal', '#5a7088', accent='#52e8d6', pattern='rings'), name='shell')
    b.cbox((0, 18, 0), (4, 5, 4), M('metal', '#8aa0b4', rivets=True), name='shell2')
    b.cbox((0, 18, -2.5), (2, 2, 1), M('gem', '#52e8d6'), name='lens')
    b.box((-0.5, 13, -0.5), (1, 2, 1), M('metal', '#b0c0d0'), name='mast')
    rot = r.bone('rotor', root, (0, 13, 0), anim='spin', speed=0.4, cast=0.0)
    rot.box((-5, 13, -5), (10, 0, 10), M('ring', '#a5f3ff', width=0.1, spokes=4, glow_amount=0.4), name='rotor')
    return r

@recipe
def familiar_beast():
    # エオマイアの仔：小さな角の生えた獣
    r = Rig('familiar_beast', layout=(64, 64))
    fur = M('fur', '#b8935a')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 17, 0), anim='breath')
    body.cbox((0, 17, 0), (4, 4, 8), fur, name='torso')
    head = r.bone('head', body, (0, 15, -4), anim='head')
    head.cbox((0, 14.5, -6), (5, 4, 4), M('decal', '#b8935a', base=fur, decals=[('front', 1, 1, '#ffd76a', True), ('front', 3, 1, '#ffd76a', True)]), name='skull')
    head.cbox((0, 16, -9), (3, 2, 2), M('decal', '#d8c090', base=M('fur', '#d8c090'), decals=[('front', 1, 0, '#2a1a10')]), name='snout')
    for sx in (-1, 1):
        head.box((sx * 1.5 - 0.5, 11.5, -6.5), (1, 1, 1), fur, name='ear')
        head.box((sx * 1 - 0.5, 10.5, -5.5), (1, 2, 1), M('horn', '#efe4c8', tip='#ffe9a0', glow=True, flip=True), name='antler')
    for name, anim, sx, sz in QUAD:
        leg(r, body, name, anim, sx * 1.5, sz * 3, 19, 2, 2, fur, foot=M('fur', '#6a4a28'), foot_rows=1)
    chain(r, body, (0, 15.5, 4), M('fur', '#8a6a3a', tip='#f0e0c0'), [(2, 2, 3), (2, 2, 2)], amp=0.25, speed=0.12, droop=-0.4)
    return r

@recipe
def familiar_sprite():
    # イグドラシル／マグナ・マーテルの若葉の精
    r = Rig('familiar_sprite', layout=(64, 64))
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=3.0, speed=0.09)
    body = r.bone('body', root, (0, 17, 0), anim='pulse', amp=0.06, speed=0.1)
    body.cbox((0, 17, 0), (4, 5, 4), M('decal', '#6aa04a', base=M('leaf', '#6aa04a', holes=0.0), decals=[('front', 0, 2, '#fffbd0', True), ('front', 3, 2, '#fffbd0', True)]),
              name='seed')
    body.cbox((0, 14, 0), (2, 1, 2), M('gem', '#d8ff8a'), name='sprout')
    body.box((-1.5, 12, 0), (3, 2, 0), M('plane', '#ffd0e8', shape='circle', glow=True, glow_amount=0.4), name='flower')
    for sx in (-1, 1):
        nm = 'wing_' + ('r' if sx < 0 else 'l')
        w = r.bone(nm, body, (sx * 2, 16, 1), rot=(0, sx * -0.3, sx * -0.4), anim=nm, amp=0.4, speed=0.4)
        w.box((sx * 2 + (0 if sx > 0 else -5), 13, 1), (5, 5, 0), M('plane', '#9ad87a', shape='leaf', glow=True, glow_amount=0.3), name='leafwing')
    return r

@recipe
def familiar_curse():
    # 獄華の分御霊：意志を持つ呪詛の小塊
    r = Rig('familiar_curse', layout=(64, 64))
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=1.0, speed=0.07)
    body = r.bone('body', root, (0, 19, 0), anim='liquid', amp=0.08)
    eyes = [('front', 1, 2, '#ffd0ff', True), ('front', 2, 2, '#e070f0', True), ('front', 5, 1, '#e070f0', True),
            ('front', 3, 4, '#ffd0ff', True), ('front', 1, 1, '#1a0a20'), ('front', 2, 1, '#1a0a20'), ('front', 5, 0, '#1a0a20')]
    body.cbox((0, 20, 0), (7, 6, 7), M('decal', '#3a2050', base=M('oilslick', '#3a2050', hues=['#af55bb', '#e070f0']), decals=eyes), name='blob')
    for sx in (-1, 1):
        hb = r.bone('horn_' + ('r' if sx < 0 else 'l'), body, (sx * 2, 17, 0), rot=(0, 0, sx * 0.4))
        hb.box((sx * 2 - 0.5, 14, -0.5), (1, 3, 1), M('horn', '#2a1a2a', tip='#af55bb', glow=True, flip=True), name='horn')
    return r

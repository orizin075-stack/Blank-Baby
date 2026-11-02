"""blocks_art.py <out assets dir> <preview.png>: OROR's boss seals and sealed gates redrawn (052).

The 41 boss seals (the altars a boss is called from: use one and its boss rises above it) were plain blocks, 25 of them
vanilla chiseled stone bricks and 16 a single flat colour; the three sealed gates (opened with the dungeon key) were a
copper block and two others like it. Here each seal is a dark altar stone with its boss's sigil cut in the top and a
band of runes round the sides, in the boss's two colours (the same table as the techniques' effects, TechniqueEffects),
and each gate a door in its frame. What is cut in them glows: a second, full-bright layer of the same model (NeoForge's
neoforge_data block_light / sky_light), so that it is seen in the dark without the block giving light.

Textures 16 x 16 (vanilla's), drawn pixel by pixel: the stone from a seeded noise with a bevel, the cut lines on the
pixel grid.
"""
import json, math, os, random, sys
from PIL import Image

NS = 'oror_supreme_bosses'
COLOURS = {
    'ain_sof_aur': ('6d5cbf', 'f2e6a0'), 'angra_mainyu': ('bf7b5a', 'bf3e60'), 'arcana': ('eed78a', '693ebf'), 'bahamut': ('307fbf', 'bf577b'),
    'berit': ('bf9039', '64e4a2'), 'brutality': ('bf7857', 'bf274e'), 'chaos': ('823bbf', 'd97b34'), 'cursed_love': ('bf4579', 'ffb0d0'),
    'demiurgos': ('7c5cbf', 'bf44a5'), 'elseria': ('2f61bf', 'a8d8ff'), 'enkou': ('63bee2', 'bf3b55'), 'eomaia': ('bf914c', '61bf96'),
    'fallen_savior': ('bfae6b', 'bf7f72'), 'ferdinand': ('bf964f', 'bf4855'), 'forbidden_arcana': ('966de3', '216ebf'),
    'gokuka': ('ac4bbf', '228dbf'), 'hakyoku': ('df4a69', 'ffd27a'), 'hephaistos': ('72ecf7', 'ee8522'), 'huang_linghua': ('bfa04c', 'bf1425'),
    'innocence': ('875bbf', 'ecc356'), 'kokuhaku': ('3b59bf', '70c6de'), 'kurma': ('5bbf48', 'bf834e'), 'lucifara': ('bf3369', '3a1030'),
    'magna_mater': ('6cbf87', '8bbf67'), 'mary_sue': ('bf954d', 'bf1d38'), 'mels': ('5292bf', 'c8f0ff'), 'merlinus': ('7534bf', 'bfab55'),
    'miyohime': ('8b5bc5', 'd3b252'), 'nortia': ('bfa153', '3c4dbf'), 'nun': ('c7b15b', '7a52bf'), 'ouroboros': ('bf9247', '6786bf'),
    'relentless_research': ('6bbfb2', 'bf6b66'), 'riha': ('bf245f', 'f1d373'), 'savior': ('bfab65', '324dbf'), 'shinra': ('bf517d', 'ffd0e0'),
    'sweet_pact': ('bf9a60', 'ff8faf'), 'taika': ('bf2d32', 'c59f47'), 'teia': ('60e1eb', 'ff8af0'), 'tenki': ('c29e3f', '6297c2'),
    'valeria': ('bf8e4b', 'fff0c0'), 'yggdrasil': ('48bf51', 'bf825d')}
GATES = {'sword_gate': 'kokuhaku', 'laboratory_gate': 'relentless_research', 'tragedy_gate': 'cursed_love'}
STONE = ['#141118', '#1f1a24', '#2b2531', '#3a3342', '#4c4456']


def hexc(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def bright(c, k):
    """A colour made lighter (k > 0, towards white) or darker (k < 0, towards black)."""
    return mix(c, (255, 255, 255), k) if k >= 0 else mix(c, (0, 0, 0), -k)


def glowing(c):
    """A colour as it glows: no darker than a mid tone, a little paler (lit from inside)."""
    lum = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    if lum < 110:
        c = mix(c, (255, 255, 255), (110 - lum) / 255 * 1.2)
    return bright(c, 0.12)


class Tex:
    """A 16 x 16 texture and its glow layer (the pixels that glow, else clear)."""

    def __init__(self, seed, stone=STONE, n=16):
        self.n = n
        self.rng = random.Random(seed)
        self.base = [[None] * n for _ in range(n)]
        self.glow = [[None] * n for _ in range(n)]
        ramp = [hexc(c) for c in stone]
        for y in range(n):
            for x in range(n):
                t = 2 + self.rng.choice((-1, 0, 0, 0, 1))
                self.base[y][x] = ramp[max(0, min(4, t))]
        self.ramp = ramp

    def bevel(self, x0=0, y0=0, x1=15, y1=15, k=1):
        """A raised edge: lit along the top and left, shadowed along the bottom and right."""
        for x in range(x0, x1 + 1):
            self.base[y0][x] = self.ramp[min(4, 3 + (k > 1))]
            self.base[y1][x] = self.ramp[0]
        for y in range(y0, y1 + 1):
            self.base[y][x0] = self.ramp[min(4, 3 + (k > 1))]
            self.base[y][x1] = self.ramp[0]

    def cut(self, x, y, c, glow=True):
        """A cut line, glowing: on the stone a darker groove, the light in the groove."""
        x, y = int(x), int(y)
        if 0 <= x < self.n and 0 <= y < self.n:
            self.base[y][x] = mix(self.ramp[0], c, 0.55)
            if glow:
                self.glow[y][x] = c

    def stone(self, x, y, tone):
        x, y = int(x), int(y)
        if 0 <= x < self.n and 0 <= y < self.n:
            self.base[y][x] = self.ramp[max(0, min(4, tone))]

    def images(self):
        b = Image.new('RGBA', (self.n, self.n))
        g = Image.new('RGBA', (self.n, self.n), (0, 0, 0, 0))
        for y in range(self.n):
            for x in range(self.n):
                b.putpixel((x, y), self.base[y][x] + (255,))
                if self.glow[y][x] is not None:
                    g.putpixel((x, y), self.glow[y][x] + (255,))
        return b, g


def raster_line(x0, y0, x1, y1):
    pts = []
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        t = i / n
        pts.append((int(math.floor(x0 + (x1 - x0) * t)), int(math.floor(y0 + (y1 - y0) * t))))
    return sorted(set(pts), key=pts.index)


# ------------------------------------------------------------------------------------------------------------ seals
def seal_top(cid):
    a, b = (glowing(hexc(c)) for c in COLOURS[cid])
    seed = sum(ord(ch) * (i + 1) for i, ch in enumerate(cid))
    rng = random.Random(seed)
    t = Tex(seed)
    t.bevel()
    # the recess the sigil is cut in: a step down inside the rim
    for y in range(2, 14):
        for x in range(2, 14):
            t.stone(x, y, t.ramp.index(t.base[y][x]) - 1 if t.base[y][x] in t.ramp else 1)
    cx = cy = 8.0
    # the ring: whole, broken into dashes, or doubled
    style = rng.choice(('whole', 'dashed', 'double'))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            ang = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
            if 5.6 <= d <= 6.6 and (style != 'dashed' or int((ang + math.pi) / (math.pi / 6)) % 2 == 0):
                t.cut(x, y, a)
            if style == 'double' and 3.9 <= d <= 4.6:
                t.cut(x, y, bright(a, -0.25))
    # the star inside it: n points joined every k-th
    n = rng.choice((3, 4, 5, 5, 6, 7, 8))
    k = {3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3}[n]
    rot = rng.random() * math.pi * 2 / n - math.pi / 2
    r = 5.0
    pts = [(cx + r * math.cos(rot + 2 * math.pi * i / n), cy + r * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]
    for i in range(n):
        # a star of three to five points is drawn point to point; more points than that, as rays from the middle (a
        # star of six or more is a blot at sixteen pixels)
        p, q = (pts[i], pts[(i + k) % n]) if n <= 5 else ((cx + 1.6 * math.cos(rot + 2 * math.pi * i / n),
                                                           cy + 1.6 * math.sin(rot + 2 * math.pi * i / n)), pts[i])
        for x, y in raster_line(p[0], p[1], q[0], q[1]):
            t.cut(x, y, b)
    # the heart of it
    heart = rng.choice(('gem', 'eye', 'cross', 'ring'))
    if heart == 'gem':
        for x, y in ((7, 7), (8, 7), (7, 8), (8, 8)):
            t.cut(x, y, bright(b, 0.45))
    elif heart == 'eye':
        for x, y in ((6, 8), (7, 7), (8, 7), (9, 8), (7, 9), (8, 9)):
            t.cut(x, y, b)
        t.cut(7, 8, bright(a, 0.5))
        t.cut(8, 8, bright(a, 0.5))
    elif heart == 'cross':
        for d in range(-2, 2):
            t.cut(7 + (d >= 0) + d, 8, bright(b, 0.3))
            t.cut(8, 7 + (d >= 0) + d, bright(b, 0.3))
    else:
        for x, y in ((7, 6), (8, 6), (6, 7), (9, 7), (6, 8), (9, 8), (7, 9), (8, 9)):
            t.cut(x, y, bright(b, 0.3))
    return t


def seal_side(cid):
    a, b = (glowing(hexc(c)) for c in COLOURS[cid])
    seed = sum(ord(ch) * (i + 3) for i, ch in enumerate(cid)) + 7
    rng = random.Random(seed)
    t = Tex(seed)
    # a plinth: a lit cap stone and a heavy foot, a band of runes between
    for x in range(16):
        for y in (0, 1):
            t.stone(x, y, 3 if y == 0 else 2)
        t.stone(x, 2, 0)
        for y in (13, 14):
            t.stone(x, y, 2 if y == 13 else 1)
        t.stone(x, 15, 0)
        t.stone(x, 12, 3)
    for y in range(3, 12):
        t.stone(0, y, 3)
        t.stone(15, y, 0)
    # three runes cut in the band, each 3 wide and 5 high, from a seeded set of strokes
    for k, x0 in enumerate((2, 6, 11)):
        y0 = 5
        strokes = rng.sample(['|l', '|r', '|m', '-t', '-m', '-b', '/', '\\', '.'], 3)
        col = a if k != 1 else b
        for s in strokes:
            if s == '|l':
                pts = [(x0, y0 + i) for i in range(5)]
            elif s == '|r':
                pts = [(x0 + 2, y0 + i) for i in range(5)]
            elif s == '|m':
                pts = [(x0 + 1, y0 + i) for i in range(5)]
            elif s == '-t':
                pts = [(x0 + i, y0) for i in range(3)]
            elif s == '-m':
                pts = [(x0 + i, y0 + 2) for i in range(3)]
            elif s == '-b':
                pts = [(x0 + i, y0 + 4) for i in range(3)]
            elif s == '/':
                pts = [(x0 + 2, y0), (x0 + 2, y0 + 1), (x0 + 1, y0 + 2), (x0, y0 + 3), (x0, y0 + 4)]
            elif s == '\\':
                pts = [(x0, y0), (x0, y0 + 1), (x0 + 1, y0 + 2), (x0 + 2, y0 + 3), (x0 + 2, y0 + 4)]
            else:
                pts = [(x0 + 1, y0 + 2)]
            for x, y in pts:
                t.cut(x, y, col)
    # a thin line of the boss's light under the cap and over the foot
    for x in range(1, 15):
        if x % 2 == 0:
            t.cut(x, 3, bright(a, -0.15))
            t.cut(x, 11, bright(a, -0.15))
    return t


def seal_bottom():
    t = Tex(99)
    t.bevel()
    return t


# ------------------------------------------------------------------------------------------------------------ gates
FRAME = ['#1a1a20', '#2a2a32', '#3c3c46', '#52525e', '#6c6c7a']


def gate_side(gid):
    cid = GATES[gid]
    a, b = (glowing(hexc(c)) for c in COLOURS[cid])
    t = Tex(len(gid) * 31, stone=FRAME)
    # the frame: two pillars and a lintel
    for y in range(16):
        for x in (0, 1, 14, 15):
            t.stone(x, y, 3 if x in (0, 14) else 1)
    for x in range(16):
        t.stone(x, 0, 3)
        t.stone(x, 1, 2)
        t.stone(x, 2, 0)
    if gid == 'sword_gate':
        # a door of dark steel in two leaves, two swords crossed over the seam, blue light in the seam
        steel = [hexc(c) for c in ('#1d2026', '#2a303a', '#3c4452', '#5a6474', '#8c95a4')]
        for y in range(3, 16):
            for x in range(2, 14):
                t.base[y][x] = steel[2 + ((x + y) % 5 == 0) - (x in (2, 7))]
        for y in range(3, 16):
            t.cut(7, y, b)
            t.cut(8, y, bright(a, 0.1))
        for i in range(9):
            for x, y in ((3 + i, 5 + i), (12 - i, 5 + i)):
                if 3 <= y <= 15:
                    t.base[y][x] = steel[4]
        for x, y in ((3, 13), (4, 14), (12, 13), (11, 14)):
            t.base[y][x] = hexc('#c1902c')
        for x, y in ((3, 4), (12, 4)):
            t.cut(x, y, bright(b, 0.4))
    elif gid == 'laboratory_gate':
        # a blast door: teal-grey panels, hazard stripes along its foot, a glowing seam and a lit panel
        plate = [hexc(c) for c in ('#1e2a2c', '#2c3c40', '#3e5458', '#56727a', '#7c9aa2')]
        for y in range(3, 16):
            for x in range(2, 14):
                t.base[y][x] = plate[2 + (y in (3, 9)) - (y in (8, 15))]
        for y in (12, 13, 14):
            for x in range(2, 14):
                t.base[y][x] = hexc('#e0b020') if (x + y) % 4 < 2 else hexc('#202024')
        for x in range(2, 14):
            t.cut(x, 9, a)
        for x, y in ((10, 5), (11, 5), (10, 6), (11, 6)):
            t.cut(x, y, b)
        for x, y in ((4, 5), (5, 5), (4, 6)):
            t.base[y][x] = plate[4]
    else:
        # the tragedy: a dark door with a heart split down the middle, pink light in the crack
        dark = [hexc(c) for c in ('#140a10', '#22121a', '#341c28', '#4a2a3a', '#663c50')]
        for y in range(3, 16):
            for x in range(2, 14):
                t.base[y][x] = dark[2 + ((x * 7 + y * 3) % 11 == 0)]
        heart = [(5, 5), (6, 4), (7, 5), (8, 5), (9, 4), (10, 5), (4, 6), (11, 6), (4, 7), (11, 7), (5, 8), (10, 8), (6, 9), (9, 9),
                 (7, 10), (8, 10), (5, 6), (6, 5), (9, 5), (10, 6)]
        for x, y in heart:
            t.cut(x, y, a)
        for x, y in ((8, 6), (7, 7), (8, 8), (7, 9), (8, 10), (7, 11), (8, 12), (7, 13), (8, 14), (7, 15)):
            t.cut(x, y, b)
    return t


def gate_top(gid):
    cid = GATES[gid]
    a = glowing(hexc(COLOURS[cid][0]))
    t = Tex(len(gid) * 17, stone=FRAME)
    t.bevel()
    for x in range(3, 13):
        t.cut(x, 7, bright(a, -0.2))
    return t


# ------------------------------------------------------------------------------------------------------------ models
def model(top, side, bottom, glow_top, glow_side):
    faces = lambda tex_side, tex_top, tex_bottom, cull=True: {
        **({'down': {'texture': tex_bottom, 'cullface': 'down'}} if tex_bottom else {}),
        'up': {'texture': tex_top, 'cullface': 'up'},
        **{d: {'texture': tex_side, 'cullface': d} for d in ('north', 'south', 'east', 'west')}}
    return {
        'parent': 'minecraft:block/block',
        'render_type': 'minecraft:cutout',
        'textures': {'particle': side, 'top': top, 'side': side, 'bottom': bottom, 'glow_top': glow_top, 'glow_side': glow_side},
        'elements': [
            {'from': [0, 0, 0], 'to': [16, 16, 16], 'faces': faces('#side', '#top', '#bottom')},
            {'from': [0, 0, 0], 'to': [16, 16, 16], 'shade': False, 'neoforge_data': {'block_light': 15, 'sky_light': 15},
             'faces': faces('#glow_side', '#glow_top', None)},
        ],
    }


def write(root, preview):
    td = os.path.join(root, 'textures', 'block')
    md = os.path.join(root, 'models', 'block')
    os.makedirs(td, exist_ok=True)
    os.makedirs(md, exist_ok=True)
    tiles = []

    def save(name, tex):
        b, g = tex.images()
        b.save(os.path.join(td, name + '.png'))
        g.save(os.path.join(td, name + '_glow.png'))
        return b, g

    bb, _ = save('boss_seal_bottom', seal_bottom())
    for cid in COLOURS:
        os.makedirs(os.path.join(td, 'boss_seal'), exist_ok=True)
        top, gt = save(f'boss_seal/{cid}_top', seal_top(cid))
        side, gs = save(f'boss_seal/{cid}_side', seal_side(cid))
        m = model(f'{NS}:block/boss_seal/{cid}_top', f'{NS}:block/boss_seal/{cid}_side', f'{NS}:block/boss_seal_bottom',
                  f'{NS}:block/boss_seal/{cid}_top_glow', f'{NS}:block/boss_seal/{cid}_side_glow')
        json.dump(m, open(os.path.join(md, f'{cid}_boss_seal.json'), 'w'), indent=1)
        tiles.append((cid, top, side))
    for gid in GATES:
        top, gt = save(f'{gid}_top', gate_top(gid))
        side, gs = save(f'{gid}_side', gate_side(gid))
        m = model(f'{NS}:block/{gid}_top', f'{NS}:block/{gid}_side', f'{NS}:block/{gid}_top', f'{NS}:block/{gid}_top_glow',
                  f'{NS}:block/{gid}_side_glow')
        json.dump(m, open(os.path.join(md, f'{gid}.json'), 'w'), indent=1)
        tiles.append((gid, top, side))
    if preview:
        S, cols = 6, 6
        rows = (len(tiles) + cols - 1) // cols
        tw = 2 * 16 * S + 24
        sheet = Image.new('RGB', (cols * tw, rows * (16 * S + 12)), (30, 30, 36))
        for i, (name, top, side) in enumerate(tiles):
            x0, y0 = (i % cols) * tw, (i // cols) * (16 * S + 12)
            sheet.paste(top.convert('RGB').resize((16 * S, 16 * S), Image.NEAREST), (x0, y0))
            sheet.paste(side.convert('RGB').resize((16 * S, 16 * S), Image.NEAREST), (x0 + 16 * S + 4, y0))
        sheet.save(preview)

if __name__ == '__main__':
    write(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)

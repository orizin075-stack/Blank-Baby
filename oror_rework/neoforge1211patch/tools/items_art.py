"""items_art.py <out assets dir> <preview.png>: OROR's plain items redrawn as 32x32 pixel art (052).

The adventure's materials and tools, the Nightfall gear and the Villager King's token had flat placeholder sprites
(a one-colour gem, a circle with a bar, the letters "LL" for a pair of boots) or borrowed vanilla ones (a rabbit's foot,
a totem, a heart of the sea, an ominous bottle, a nether star), and the dragon-furnace armour was worn as three flat
colours. Each is drawn here on a material grid in screen space: every material has a five-tone ramp; a pixel is lit a
tone where the light (from the top left) falls on it from outside its material and darkened a tone on its far side,
round things (orbs, flasks, discs) are shaded as spheres, glowing materials keep their tone, and a dark outline is laid
round the whole. The gear that is used and then recharges gets its states (in use, recharging) as their own sprites,
and the armour its worn textures (64 x 32, the humanoid armour layout).
"""
import math, os, sys
from PIL import Image

RAMPS = {
    'iron': ['#1d2026', '#353a44', '#596170', '#8c95a4', '#d2d9e2'],
    'nsteel': ['#141117', '#262129', '#3b3440', '#5b5163', '#8f8499'],
    'gold': ['#4a2c0a', '#83531a', '#c1902c', '#edc956', '#fff4b4'],
    'bronze': ['#3a1e0e', '#64381a', '#93602c', '#c48c48', '#ecc690'],
    'wood': ['#1e140e', '#33241a', '#4c3626', '#6a4c35', '#8c6a4c'],
    'leather': ['#24120c', '#3d2014', '#5a321e', '#7c4a2c', '#a26c44'],
    'paper': ['#5e5040', '#9a8a70', '#cdbf9e', '#ebe2c8', '#fffaea'],
    'cloth': ['#3a0810', '#661018', '#9c1c26', '#cc3438', '#f07068'],
    'blue': ['#0c1a3a', '#172f66', '#24509c', '#3c7ad0', '#86b8f2'],
    'ember': ['#5a1204', '#a82a06', '#f06a10', '#ffb430', '#fff2b0'],
    'magma': ['#2a0a06', '#4e1408', '#7a220c', '#a83812', '#d4581c'],
    'scale': ['#24080a', '#420e12', '#661a1c', '#8c2c26', '#b44a38'],
    'teal': ['#062424', '#0d4646', '#147670', '#2cb4a2', '#9cf0dc'],
    'cyan': ['#0a2a40', '#125a7c', '#1e94b8', '#5cd2ee', '#d8faff'],
    'violet': ['#1c0e34', '#381c62', '#5e349c', '#9468d6', '#dcc8ff'],
    'crystal': ['#2a1c5c', '#4a3c9e', '#7a74d8', '#b0b4f4', '#f0f2ff'],
    'void': ['#08040c', '#160a1c', '#24102c', '#38183e', '#4e2454'],
    'blood': ['#3c040c', '#780a18', '#c0182a', '#ff4646', '#ffb4a4'],
    'honey': ['#5a2a04', '#9c540a', '#dc8e16', '#ffc23a', '#fff0a0'],
    'glass': ['#3c5660', '#6a8a96', '#a2c0cc', '#d4e8ee', '#ffffff'],
    'leaf': ['#0e2a10', '#1c4a1a', '#2e7428', '#4ca43a', '#94d870'],
    'star': ['#5c4c20', '#a08a3e', '#e0ca70', '#fff2b4', '#ffffff'],
    'mana': ['#0a1240', '#14267a', '#2442b8', '#4c7cee', '#b4d4ff'],
    'emerald': ['#063018', '#0c5a2c', '#16904a', '#3cd07a', '#b4ffd2'],
    'feather': ['#3e4656', '#6c7688', '#a4adbc', '#d6dce6', '#ffffff'],
    'white': ['#5c6670', '#94a0ac', '#c8d2dc', '#eaf0f6', '#ffffff'],
    'petal': ['#4a0a1e', '#8a1636', '#cc2a50', '#f2667e', '#ffc4d0'],
    'bud': ['#2a1018', '#4a1e2a', '#6a3040', '#8c4a58', '#ae6c78'],
    'rune': ['#0c3a44', '#18707c', '#2cb2be', '#7ceef2', '#e4ffff'],
    'smoke': ['#1a1420', '#2c2234', '#40344a', '#584a62', '#74667e'],
}
GLOW = {'ember', 'star', 'rune', 'mana', 'blood'}
OUTLINE = (16, 10, 18, 255)


def rgb(h, a=255):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (a,)


class Canvas:
    def __init__(self, w=32, h=32):
        self.w, self.h = w, h
        self.mat = [[None] * w for _ in range(h)]
        self.tone = [[2] * w for _ in range(h)]
        self.fixed = [[False] * w for _ in range(h)]

    def px(self, x, y, m, tone=None):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.mat[y][x] = m
            self.tone[y][x] = 2 if tone is None else tone
            self.fixed[y][x] = tone is not None

    def get(self, x, y):
        return self.mat[y][x] if 0 <= x < self.w and 0 <= y < self.h else None

    def clear(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.mat[y][x] = None

    def each(self, test):
        """test(x, y, cx, cy) -> material, (material, tone) or None, at every pixel (cx, cy: its centre)."""
        for y in range(self.h):
            for x in range(self.w):
                r = test(x, y, x + 0.5, y + 0.5)
                if r is None:
                    continue
                if isinstance(r, tuple):
                    self.px(x, y, r[0], r[1])
                else:
                    self.px(x, y, r)

    def poly(self, pts, m, tone=None):
        def inside(px_, py_):
            c = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > py_) != (yj > py_) and px_ < (xj - xi) * (py_ - yi) / (yj - yi) + xi:
                    c = not c
                j = i
            return c
        self.each(lambda x, y, cx, cy: (m, tone) if inside(cx, cy) and tone is not None else (m if inside(cx, cy) else None))

    def rect(self, x0, y0, x1, y1, m, tone=None):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, m, tone)

    def ellipse(self, cx, cy, rx, ry, m, tone=None):
        self.each(lambda x, y, px_, py_: (m, tone) if ((px_ - cx) / rx) ** 2 + ((py_ - cy) / ry) ** 2 <= 1 and tone is not None
                  else (m if ((px_ - cx) / rx) ** 2 + ((py_ - cy) / ry) ** 2 <= 1 else None))

    def ring(self, cx, cy, ro, ri, m, tone=None, ry=None):
        ry = ry or 1.0
        def t(x, y, px_, py_):
            d = math.hypot(px_ - cx, (py_ - cy) / ry)
            if ri <= d <= ro:
                return (m, tone) if tone is not None else m
            return None
        self.each(t)

    def orb(self, cx, cy, r, m, ry=None, light=(-0.55, -0.6), spec=True, base=0):
        """A sphere (or a flattened one), shaded from the light: tones 0..4, a highlight where it faces the light."""
        ry = ry or r
        lx, ly = light
        ln = math.hypot(lx, ly)
        lx, ly = lx / ln, ly / ln
        def t(x, y, px_, py_):
            dx, dy = (px_ - cx) / r, (py_ - cy) / ry
            d2 = dx * dx + dy * dy
            if d2 > 1:
                return None
            nz = math.sqrt(1 - d2)
            lam = dx * lx + dy * ly + nz * 0.6
            tone = 1 + lam * 2.2 + base
            if spec and dx * lx + dy * ly > 0.45 and d2 < 0.5:
                tone = 4
            return (m, max(0, min(4, int(round(tone)))))
        self.each(t)

    def line(self, x0, y0, x1, y1, width, m, tone=None):
        def t(x, y, px_, py_):
            dx, dy = x1 - x0, y1 - y0
            L = dx * dx + dy * dy
            u = 0 if L == 0 else max(0, min(1, ((px_ - x0) * dx + (py_ - y0) * dy) / L))
            qx, qy = x0 + u * dx, y0 + u * dy
            if math.hypot(px_ - qx, py_ - qy) <= width / 2:
                return (m, tone) if tone is not None else m
            return None
        self.each(t)

    def path(self, pts, width, m, tone=None):
        for a, b in zip(pts, pts[1:]):
            self.line(a[0], a[1], b[0], b[1], width, m, tone)

    def render(self, outline=True):
        img = Image.new('RGBA', (self.w, self.h), (0, 0, 0, 0))
        p = img.load()
        for y in range(self.h):
            for x in range(self.w):
                m = self.mat[y][x]
                if m is None:
                    continue
                t = self.tone[y][x]
                if not self.fixed[y][x] and m not in GLOW:
                    up, left, down, right = self.get(x, y - 1), self.get(x - 1, y), self.get(x, y + 1), self.get(x + 1, y)
                    if up != m or left != m:
                        t += 1
                    if down != m or right != m:
                        t -= 1
                p[x, y] = rgb(RAMPS[m][max(0, min(4, t))])
        if not outline:
            return img
        out = img.copy()
        o = out.load()
        for y in range(self.h):
            for x in range(self.w):
                if p[x, y][3]:
                    continue
                if any(0 <= x + dx < self.w and 0 <= y + dy < self.h and p[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    o[x, y] = OUTLINE
        return out


def sparkle(c, x, y, m='star', big=False):
    c.px(x, y, m, 4)
    if big:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            c.px(x + dx, y + dy, m, 3)


def dim(img, k=0.55, grey=0.5):
    """A recharging sprite: the same, its colour drained and its light dimmed."""
    out = img.copy()
    p = out.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = p[x, y]
            if not a:
                continue
            l = 0.3 * r + 0.59 * g + 0.11 * b
            r, g, b = (v * (1 - grey) + l * grey for v in (r, g, b))
            p[x, y] = (int(r * k), int(g * k), int(b * k), a)
    return out


# ---------------------------------------------------------------------------------------------------------------- items

def star_shard():
    """星脈結晶: a cluster of star-vein crystals, faceted, a star burning in the largest."""
    c = Canvas()
    # the small crystals behind
    c.poly([(5, 20), (8, 11), (12, 13), (12, 26), (7, 27)], 'crystal')
    c.poly([(20, 24), (23, 14), (27, 12), (28, 22), (25, 27)], 'crystal')
    # the great crystal: left face lit, ridge bright, right face in shade
    c.poly([(16, 2), (11, 9), (11, 25), (16, 29)], 'crystal', 3)
    c.poly([(16, 2), (21, 9), (21, 25), (16, 29)], 'crystal', 1)
    c.line(16, 3, 16, 28, 1.2, 'crystal', 4)
    c.poly([(11, 9), (16, 2), (13, 10)], 'crystal', 4)
    # the facets of the small ones
    c.line(8.5, 12, 9.5, 26, 1, 'crystal', 3)
    c.line(25, 13, 24.5, 26, 1, 'crystal', 1)
    # the star within, and the light about it
    for x, y, t in ((16, 15, 4), (15, 15, 4), (17, 15, 4), (16, 14, 4), (16, 16, 4), (16, 13, 3), (16, 17, 3), (14, 15, 3), (18, 15, 3)):
        c.px(x, y, 'star', t)
    sparkle(c, 4, 6)
    sparkle(c, 27, 6, big=True)
    sparkle(c, 29, 27)
    return c.render()


def dragon_core():
    """龍炉核: a molten core held in a dragon's iron claws over a scaled base."""
    c = Canvas()
    c.orb(16, 14, 9, 'ember', base=0.6)
    # the white heat at its heart
    c.ellipse(14.5, 12.5, 3, 2.6, 'ember', 4)
    # the claws: four talons gripping it from below
    for side in (-1, 1):
        c.path([(16 + side * 3, 27), (16 + side * 8, 22), (16 + side * 10, 15), (16 + side * 8, 8)], 2.4, 'iron')
        c.px(16 + side * 8, 7, 'iron', 4)
        c.px(16 + side * 7, 6, 'iron', 3)
        c.path([(16 + side * 2, 27), (16 + side * 4, 22), (16 + side * 5, 19)], 1.8, 'iron')
    # the base: dark scales
    c.poly([(9, 26), (23, 26), (25, 30), (7, 30)], 'scale')
    for x in range(9, 24, 3):
        c.px(x, 27, 'scale', 4)
        c.px(x + 1, 28, 'scale', 1)
    sparkle(c, 25, 5, 'ember')
    sparkle(c, 6, 9, 'ember')
    return c.render()


def forge_core():
    """工廠演算核: a brass cube of the forge's reckoning, circuits lit teal, a lens at its heart."""
    c = Canvas()
    # an isometric cube: top light, left face mid, right face dark
    top = [(16, 4), (27, 9), (16, 14), (5, 9)]
    left = [(5, 9), (16, 14), (16, 28), (5, 23)]
    right = [(16, 14), (27, 9), (27, 23), (16, 28)]
    c.poly(top, 'bronze', 4)
    c.poly(left, 'bronze', 2)
    c.poly(right, 'bronze', 1)
    # the edges
    c.path([(5, 9), (16, 14), (27, 9)], 1, 'gold', 4)
    c.line(16, 14, 16, 28, 1, 'gold', 3)
    # circuits on the faces
    c.path([(7, 13), (10, 15), (10, 20), (13, 22)], 1, 'rune', 3)
    c.path([(25, 13), (22, 15), (22, 19), (19, 21)], 1, 'rune', 2)
    c.path([(10, 9), (16, 11.5), (22, 9)], 1, 'rune', 3)
    for x, y in ((13, 22), (19, 21), (7, 13), (25, 13)):
        c.px(x, y, 'rune', 4)
    # the lens on the top face
    c.ellipse(16, 9, 3.2, 1.8, 'rune', 3)
    c.px(15, 8, 'rune', 4)
    c.px(16, 9, 'rune', 4)
    sparkle(c, 28, 4, 'rune')
    return c.render()


def curse_residue():
    """悲劇の残滓: a broken black heart of a tragedy, a crimson light in its crack, its ichor dripping."""
    c = Canvas()
    # the left half and the right half of a heart, a little apart
    def heart(x, y, px_, py_):
        u, v = (px_ - 16) / 11, (py_ - 15) / 11
        return (u * u + v * v - 0.33) ** 3 - u * u * (v * -1) ** 3 * 1.2 < 0
    c.each(lambda x, y, px_, py_: 'void' if heart(x, y, px_, py_ - 1) else None)
    # the crack down its middle, glowing
    crack = [(15, 6), (17, 10), (14, 13), (18, 17), (15, 21), (16, 25)]
    c.path(crack, 1.6, 'blood', 3)
    c.path(crack, 0.8, 'blood', 4)
    # a sheen on the upper left
    c.px(9, 9, 'void', 4)
    c.px(10, 8, 'void', 4)
    c.px(8, 10, 'void', 3)
    # the drips
    c.line(19, 24, 19, 28, 1, 'blood', 2)
    c.px(19, 29, 'blood', 3)
    c.line(12, 23, 12, 25, 1, 'blood', 2)
    c.px(12, 26, 'blood', 3)
    # the smoke rising off it
    c.path([(22, 6), (24, 4), (23, 2)], 1, 'smoke', 3)
    c.path([(8, 5), (7, 3)], 1, 'smoke', 2)
    return c.render()


def world_thread():
    """円環の糸: a spool of shining thread, its loose end looping round in a ring that swallows its tail."""
    c = Canvas()
    # the ring of thread behind
    c.ring(16, 16, 14.5, 13.2, 'star', 3)
    # the spool: dark wooden flanges, the thread wound between them in bright crossing turns
    c.rect(10, 8, 22, 24, 'star', 2)
    for k in range(-16, 16, 3):
        c.line(10 + k, 24, 18 + k, 8, 1, 'star', 4)
    for k in range(-16, 16, 4):
        c.line(10 + k, 8, 18 + k, 24, 1, 'star', 1)
    c.each(lambda x, y, px_, py_: None)
    for y in (8, 24):
        c.orb(16, y, 8, 'wood', ry=2.4, spec=False, base=0.3)
    c.ellipse(16, 7.6, 2.2, 0.9, 'wood', 0)
    # clip the windings to the spool's width
    for y in range(9, 24):
        for x in list(range(0, 10)) + list(range(23, 32)):
            if c.get(x, y) == 'star' and not (abs(math.hypot(x + 0.5 - 16, y + 0.5 - 16) - 13.85) < 0.8):
                c.clear(x, y)
    # the loose end running out to the ring, and where the ring takes its own end
    c.path([(22, 15), (26, 13), (28.5, 9.5)], 1, 'star', 4)
    c.px(28, 9, 'gold', 4)
    sparkle(c, 4, 5)
    sparkle(c, 27, 27, big=True)
    return c.render()

def rewind_talisman():
    """輪廻の護符: a bronze medallion with a clock face whose hands turn back, a cyan arrow running round it backwards."""
    c = Canvas()
    c.path([(16, 1), (12, 5)], 1, 'cloth', 3)
    c.path([(16, 1), (20, 5)], 1, 'cloth', 2)
    c.orb(16, 17, 12, 'bronze', base=0.4)
    c.ring(16, 17, 12, 10.6, 'gold', 3)
    c.orb(16, 17, 8.4, 'paper', spec=False, base=0.6)
    # the hours
    for k in range(12):
        a = k * math.pi / 6
        c.px(16 + math.sin(a) * 6.8, 17 - math.cos(a) * 6.8, 'bronze', 1)
    # the hands
    c.line(16, 17, 16, 11, 1, 'nsteel', 1)
    c.line(16, 17, 12, 19, 1, 'nsteel', 1)
    c.px(16, 17, 'gold', 4)
    # the arrow running round backwards (counter-clockwise), in light
    for k in range(0, 260, 9):
        a = math.radians(-k + 60)
        c.px(16 + math.cos(a) * 13.5, 17 - math.sin(a) * 13.5, 'rune', 3)
    a = math.radians(60 - 260)
    hx, hy = 16 + math.cos(a) * 13.5, 17 - math.sin(a) * 13.5
    c.px(hx, hy, 'rune', 4)
    c.px(hx + 1, hy - 1, 'rune', 4)
    c.px(hx + 1, hy + 1, 'rune', 4)
    # the loop for the cord
    c.ring(16, 5, 2.2, 1, 'gold', 3)
    return c.render()


def flask(c, body_cx, body_cy, r, liquid, level, neck_w=4, neck_h=4):
    """A round glass flask: the liquid in it to level (0 empty, 1 full), a highlight on the glass."""
    c.orb(body_cx, body_cy, r, 'glass', spec=False, base=0.4)
    top = body_cy - r + (1 - level) * 2 * r
    c.each(lambda x, y, px_, py_: (liquid, None) if py_ >= top and ((px_ - body_cx) / (r - 1)) ** 2 + ((py_ - body_cy) / (r - 1)) ** 2 <= 1
           else None)
    c.rect(int(body_cx - neck_w / 2), int(body_cy - r - neck_h), int(body_cx + neck_w / 2) - 1, int(body_cy - r), 'glass', 3)
    # the glass's light
    c.line(body_cx - r * 0.55, body_cy - r * 0.35, body_cx - r * 0.3, body_cy - r * 0.6, 1, 'glass', 4)
    c.px(body_cx - r * 0.6, body_cy, 'glass', 4)


def purifying_dew():
    """神樹の浄化蜜: a flask of the world tree's golden honey, stoppered with a leaf, a drop of it running down."""
    c = Canvas()
    flask(c, 16, 19, 10, 'honey', 0.72)
    c.orb(16, 21, 6, 'honey', spec=False, base=0.5)
    # the stopper: cork wrapped in a leaf
    c.rect(14, 4, 17, 7, 'wood')
    c.poly([(12, 6), (17, 2), (22, 3), (19, 7)], 'leaf')
    c.line(13, 6, 21, 3.5, 1, 'leaf', 4)
    # a drop on the glass, and the honey's glow
    c.ellipse(24.5, 23, 1.2, 1.8, 'honey', 4)
    sparkle(c, 12, 17, 'star')
    sparkle(c, 27, 9, 'star')
    return c.render()


def mana_crystal():
    """星脈の魔力薬: a flask of star-vein mana, deep blue and full of stars, stoppered with a crystal."""
    c = Canvas()
    flask(c, 16, 19, 10, 'mana', 0.85)
    for x, y in ((12, 19), (18, 22), (20, 16), (14, 25), (17, 18)):
        c.px(x, y, 'mana', 4)
    c.px(19, 23, 'star', 4)
    c.px(13, 22, 'star', 3)
    # the crystal stopper
    c.poly([(16, 1), (19, 5), (16, 8), (13, 5)], 'crystal', 3)
    c.poly([(16, 1), (19, 5), (16, 8)], 'crystal', 1)
    c.px(15, 4, 'crystal', 4)
    sparkle(c, 25, 7, 'star', big=True)
    return c.render()


def dungeon_key():
    """封域の鍵: an old iron key of the sealed realms, its bow a ring of gold round a crimson seal, held by the bow; the
    bit a notched iron ward off the end of the shaft."""
    c = Canvas()
    sq = math.sqrt(0.5)
    def frame(px_, py_):
        cx, cy = px_ - 16, py_ - 16
        return (cx - cy) * sq, (cx + cy) * sq
    # the shaft along the diagonal, the bit standing off it near the tip (toward the bottom right), notched
    def key(x, y, px_, py_):
        a, p = frame(px_, py_)
        if -6 <= a <= 15 and abs(p) <= 1.3:
            return 'iron'
        if 7 <= a <= 13.5 and 1.3 < p <= 6.5:
            if (a < 8.6 or 10.4 < a < 11.6) and p > 4.2:
                return None
            return 'iron'
        return None
    c.each(key)
    c.each(lambda x, y, px_, py_: ('iron', 4) if abs(frame(px_, py_)[1] + 0.6) < 0.5 and -5 <= frame(px_, py_)[0] <= 14 else None)
    # a gold collar on the shaft
    c.each(lambda x, y, px_, py_: 'gold' if -4.5 <= frame(px_, py_)[0] <= -2.5 and abs(frame(px_, py_)[1]) <= 2.2 else None)
    # the bow: a gold ring with the seal in it
    c.ring(8, 24, 6.6, 3.9, 'gold')
    c.orb(8, 24, 3.4, 'blood', base=0.4)
    c.px(7, 23, 'blood', 4)
    for k in range(6):
        a = k * math.pi / 3 + 0.3
        c.px(8 + math.cos(a) * 5.3, 24 + math.sin(a) * 5.3, 'rune', 3)
    sparkle(c, 27, 26, 'rune')
    return c.render()

def field_guide():
    """OROR冒険手帳: a leather adventurer's journal, gold corners and a compass on its cover, strapped, a ribbon out."""
    c = Canvas()
    # the pages' edges (right and bottom) and the cover
    c.rect(7, 4, 26, 27, 'paper')
    for y in range(6, 27, 2):
        c.px(26, y, 'paper', 1)
    c.rect(5, 3, 24, 26, 'leather')
    c.rect(5, 3, 7, 26, 'leather', 1)
    # gold corners
    for x, y in ((8, 4), (22, 4), (8, 24), (22, 24)):
        c.rect(x, y, x + 1, y + 1, 'gold', 3)
    # the compass rose on the cover
    c.ring(15, 14, 5, 4, 'gold', 3)
    c.poly([(15, 8), (16.5, 13), (15, 14), (13.5, 13)], 'gold', 4)
    c.poly([(15, 20), (16.5, 15), (15, 14), (13.5, 15)], 'gold', 2)
    c.poly([(9, 14), (14, 12.5), (15, 14), (14, 15.5)], 'gold', 2)
    c.poly([(21, 14), (16, 12.5), (15, 14), (16, 15.5)], 'gold', 3)
    c.px(15, 14, 'rune', 4)
    # the strap and its buckle
    c.rect(22, 12, 27, 15, 'leather', 0)
    c.rect(26, 11, 28, 16, 'iron', 3)
    c.px(27, 13, 'nsteel', 0)
    # the ribbon out of the bottom
    c.path([(18, 26), (18, 29), (20, 30)], 1.2, 'cloth', 3)
    return c.render()


def forge_tool():
    """工廠修復具: the forge's repair tool, a wrench's open jaw and a hammer's face either side of a turning teal gear,
    on a bound grip (held from the bottom left)."""
    c = Canvas()
    # the grip
    c.line(3, 29, 13, 19, 2.8, 'leather')
    for k in range(4):
        x, y = 5 + k * 2.3, 27 - k * 2.3
        c.line(x - 1.2, y - 1.2, x + 1.2, y + 1.2, 1, 'leather', 1)
    c.line(3, 29, 4.5, 27.5, 3.2, 'iron', 2)
    # the shaft
    c.line(12, 20, 18, 14, 2.6, 'iron')
    # the head, crosswise to the shaft: the wrench's open jaw (top left), the hammer's face (bottom right)
    c.line(13, 9, 27, 23, 5, 'iron')
    c.poly([(9, 5), (15, 4), (16, 9), (11, 11), (13, 8)], 'iron', 3)
    c.clear(12, 7)
    c.clear(13, 7)
    c.clear(12, 8)
    c.poly([(24, 24), (30, 22), (31, 27), (27, 30)], 'nsteel')
    c.line(26, 25, 29, 28, 1, 'iron', 4)
    # the gear in the middle of the head
    for k in range(8):
        a = k * math.pi / 4 + 0.2
        c.px(20 + math.cos(a) * 4.6, 16 + math.sin(a) * 4.6, 'bronze', 3)
    c.orb(20, 16, 3.8, 'bronze', spec=False)
    c.ellipse(20, 16, 1.5, 1.5, 'rune', 4)
    sparkle(c, 29, 8, 'rune', big=True)
    return c.render()

def dragon_coat():
    """龍炉の護衣: a breastplate of dragon scales under great gold-rimmed pauldrons, the furnace's core burning at its
    breast."""
    c = Canvas()
    # the breastplate, waisted
    c.poly([(9, 7), (23, 7), (24, 14), (22, 22), (23, 28), (9, 28), (10, 22), (8, 14)], 'scale')
    for row, y in enumerate(range(9, 28, 3)):
        for x in range(9 + (row % 2) * 2, 24, 4):
            if c.get(x, y) == 'scale':
                c.px(x, y, 'scale', 4)
                c.px(x + 1, y, 'scale', 3)
                c.px(x - 1, y + 1, 'scale', 1)
    # the pauldrons
    for side in (-1, 1):
        cx = 16 + side * 10
        c.orb(cx, 9, 5.5, 'scale', ry=4.5, base=0.3)
        c.each(lambda x, y, px_, py_, cx=cx: ('gold', 3) if 4.6 <= math.hypot((px_ - cx) / 5.5 * 5, (py_ - 9) / 4.5 * 5) <= 5.4 and py_ > 7
               else None)
    # the neck's gold rim, the belt
    c.path([(11, 6), (13, 9), (16, 10), (19, 9), (21, 6)], 1.4, 'gold', 4)
    c.line(10, 22, 22, 22, 1.4, 'gold', 3)
    c.px(16, 22, 'ember', 4)
    c.line(9, 28, 23, 28, 1, 'gold', 2)
    # the core at the breast
    c.orb(16, 15, 3.2, 'ember', base=0.5)
    c.ring(16, 15, 4.4, 3.4, 'gold', 4)
    return c.render()

def teia_boots():
    """光越の加速靴: a pair of white boots of light, cyan lines along them, wings of light at the heels."""
    c = Canvas()
    def boot(ox, oy, back):
        c.poly([(11 + ox, 5 + oy), (18 + ox, 5 + oy), (18 + ox, 19 + oy), (26 + ox, 22 + oy), (26 + ox, 27 + oy), (11 + ox, 27 + oy)], 'white',
               2 if back else None)
        c.line(11 + ox, 27 + oy, 26 + ox, 27 + oy, 1, 'iron', 0 if back else 2)
        c.line(11 + ox, 6 + oy, 18 + ox, 6 + oy, 1.2, 'cyan', 2 if back else 4)
        if not back:
            c.path([(14 + ox, 8 + oy), (14 + ox, 21 + oy), (23 + ox, 24 + oy)], 1, 'cyan', 4)
            c.px(24 + ox, 24 + oy, 'rune', 4)
        # the wing at the heel, of light
        c.poly([(11 + ox, 10 + oy), (3 + ox, 5 + oy), (5 + ox, 10 + oy), (2 + ox, 12 + oy), (6 + ox, 15 + oy), (11 + ox, 17 + oy)], 'rune',
               1 if back else 3)
        c.line(4 + ox, 7 + oy, 10 + ox, 12 + oy, 1, 'rune', 2 if back else 4)
        c.line(4 + ox, 12 + oy, 10 + ox, 15 + oy, 1, 'rune', 1 if back else 2)
    boot(-5, -3, True)
    boot(3, 1, False)
    sparkle(c, 28, 10, 'rune', big=True)
    sparkle(c, 2, 27, 'rune')
    return c.render()

def omniregistry_treasure():
    """万象登録の秘宝: an armillary of gold rings about a sphere in which all things are written, on a jewelled stand."""
    c = Canvas()
    c.poly([(10, 30), (22, 30), (19, 26), (13, 26)], 'gold')
    c.rect(15, 21, 17, 26, 'gold')
    c.orb(16, 13, 6.5, 'crystal', base=0.3)
    def ellipse_ring(rx, ry, ang, tone):
        ca, sa = math.cos(ang), math.sin(ang)
        def t(x, y, px_, py_):
            u = (px_ - 16) * ca + (py_ - 13) * sa
            v = -(px_ - 16) * sa + (py_ - 13) * ca
            d = (u / rx) ** 2 + (v / ry) ** 2
            return ('gold', tone) if abs(d - 1) < 0.2 else None
        c.each(t)
    ellipse_ring(11, 3, 0, 3)
    ellipse_ring(10.5, 3, 0.9, 4)
    ellipse_ring(10.5, 3, -0.9, 2)
    for x, y in ((14, 11), (17, 12), (15, 15), (18, 15)):
        c.px(x, y, 'rune', 4)
    c.px(16, 28, 'emerald', 4)
    c.px(13, 28, 'blood', 3)
    c.px(19, 28, 'mana', 4)
    sparkle(c, 4, 3, big=True)
    sparkle(c, 28, 27)
    return c.render()

def dodge_talon(active=False):
    """疾歩の鉤爪: a raptor's foot of iron, three talons, a cuff of feathers; in use, the wind wound round it."""
    c = Canvas()
    # the cuff of feathers (top left) and the shank
    c.poly([(3, 4), (11, 2), (13, 8), (6, 12)], 'feather')
    for k in range(3):
        c.line(4 + k * 3, 4 + k, 7 + k * 3, 9, 1, 'feather', 4)
    c.line(10, 9, 16, 16, 3.4, 'iron')
    # the talons, curving down
    for pts in ([(16, 16), (24, 15), (28, 19), (27, 23)], [(16, 16), (21, 21), (22, 27), (19, 29)], [(16, 16), (13, 22), (9, 24), (7, 22)]):
        c.path(pts, 2.2, 'nsteel')
        c.px(*pts[-1], 'iron', 4)
    c.ellipse(16, 16, 2.6, 2.6, 'iron')
    if active:
        for k in range(0, 300, 12):
            a = math.radians(k)
            r = 9 + k / 40
            c.px(16 + math.cos(a) * r, 16 + math.sin(a) * r * 0.8, 'rune', 3 if k % 24 else 4)
    else:
        c.path([(20, 6), (27, 4)], 1, 'rune', 3)
        c.path([(22, 9), (29, 8)], 1, 'rune', 2)
    return c.render()


def last_bloom(open_=True):
    """終わり咲く花: a crimson lily of the end, opened over a short stem, its heart of gold light; recharging, a closed bud."""
    c = Canvas()
    c.path([(16, 30), (16, 22), (15, 16)], 1.6, 'leaf')
    c.poly([(16, 27), (9, 22), (8, 25)], 'leaf')
    c.poly([(16, 25), (23, 21), (24, 24)], 'leaf')
    if open_:
        # six petals curling outward
        for k in range(6):
            a = k * math.pi / 3 - math.pi / 2
            tip = (15 + math.cos(a) * 12, 13 + math.sin(a) * 10)
            side = (15 + math.cos(a + 0.5) * 6, 13 + math.sin(a + 0.5) * 5)
            side2 = (15 + math.cos(a - 0.5) * 6, 13 + math.sin(a - 0.5) * 5)
            c.poly([(15, 13), side, tip, side2], 'petal')
            c.line(15, 13, tip[0] * 0.85 + 15 * 0.15, tip[1] * 0.85 + 13 * 0.15, 1, 'petal', 4 if k in (0, 4, 5) else 3)
        # the stamens and the light
        for k in range(5):
            a = k * 2 * math.pi / 5
            c.px(15 + math.cos(a) * 4, 13 + math.sin(a) * 4, 'star', 4)
        c.orb(15, 13, 2.6, 'star', spec=False, base=1)
        sparkle(c, 27, 4, 'star', big=True)
    else:
        c.poly([(15, 4), (19, 11), (17, 17), (13, 17), (11, 11)], 'bud')
        c.line(15, 5, 15, 16, 1, 'bud', 3)
        c.poly([(13, 17), (17, 17), (16, 19), (14, 19)], 'leaf')
    return c.render()


def parry_emblem(active=False):
    """返し刃の徽章: a silver shield-badge, blue enamelled, two blades crossed upon it and an arrow turning back; in use,
    its edge burning gold and sparks flying from it."""
    c = Canvas()
    shield = [(5, 4), (27, 4), (27, 15), (16, 30), (5, 15)]
    c.poly(shield, 'iron')
    c.poly([(7, 6), (25, 6), (25, 15), (16, 27), (7, 15)], 'blue')
    # the crossed blades
    c.line(9, 9, 22, 23, 1.8, 'white')
    c.line(23, 9, 10, 23, 1.8, 'white')
    c.rect(8, 8, 9, 9, 'gold', 3)
    c.rect(22, 8, 23, 9, 'gold', 3)
    # the arrow turning back over them
    for k in range(0, 200, 12):
        a = math.radians(200 - k)
        c.px(16 + math.cos(a) * 6, 13 - math.sin(a) * 4, 'gold', 4)
    c.px(10, 14, 'gold', 4)
    c.px(9, 13, 'gold', 4)
    c.px(11, 13, 'gold', 4)
    if active:
        c.path(shield + [shield[0]], 1.2, 'star', 4)
        for x, y in ((3, 2), (29, 3), (2, 18), (30, 17), (16, 1)):
            sparkle(c, x, y, 'star', big=(x == 29))
    return c.render()


def squad_banner(active=False):
    """戦団の旗標: a war banner of the band on its pole (held from the bottom left), the band's crest on blue; raised in
    a rally, its crest blazing gold."""
    c = Canvas()
    c.line(5, 30, 24, 3, 1.8, 'wood')
    c.px(24, 2, 'gold', 4)
    c.px(25, 2, 'gold', 3)
    # the flag, flying from the pole toward the right
    flag = [(22, 6), (30, 7), (29, 12), (31, 18), (19, 20), (16, 15)]
    c.poly(flag, 'blue')
    c.path([(22, 6), (30, 7)], 1, 'gold', 3)
    c.path([(19, 20), (31, 18)], 1, 'gold', 2)
    # the crest: a crowned shield
    c.poly([(21, 10), (26, 10), (26, 14), (23.5, 17), (21, 14)], 'gold' if not active else 'star', 3 if not active else 4)
    c.px(23, 12, 'cloth', 3)
    c.px(24, 12, 'cloth', 3)
    if active:
        sparkle(c, 29, 3, 'star', big=True)
        sparkle(c, 14, 10, 'star')
        sparkle(c, 30, 23, 'star')
    return c.render()


def villager_king_token():
    """村人王の証: the Villager King's medal of gold, an emerald in its crowned face, hung on a red ribbon."""
    c = Canvas()
    c.poly([(11, 1), (15, 1), (16, 9), (13, 9)], 'cloth')
    c.poly([(17, 1), (21, 1), (19, 9), (16, 9)], 'cloth', 1)
    c.orb(16, 19, 11, 'gold', base=0.4)
    c.ring(16, 19, 11, 9.6, 'gold', 4)
    c.ring(16, 19, 8.6, 8, 'gold', 1)
    # the crown over the emerald
    c.poly([(11, 14), (13, 11), (14.5, 13.5), (16, 10), (17.5, 13.5), (19, 11), (21, 14), (20, 16), (12, 16)], 'gold', 4)
    c.px(13, 11, 'blood', 4)
    c.px(16, 10, 'mana', 4)
    c.px(19, 11, 'blood', 4)
    c.orb(16, 21, 3.6, 'emerald', base=0.4)
    sparkle(c, 27, 9, 'star', big=True)
    return c.render()


def focus_cell():
    """The laser gun's focus cell: a capsule of glass between steel caps, coils of cyan energy burning inside it."""
    c = Canvas()
    c.line(8, 24, 24, 8, 8.5, 'glass')
    for k in range(5):
        x, y = 11 + k * 2.6, 21 - k * 2.6
        c.line(x - 2.2, y - 2.2, x + 2.2, y + 2.2, 1.2, 'rune', 4 if k % 2 else 3)
    c.line(12, 20, 20, 12, 1, 'rune', 4)
    for (x, y) in ((6, 26), (26, 6)):
        c.line(x - 2.5, y + 2.5 if x < 16 else y + 2.5, x + 2.5, y - 2.5, 4.2, 'iron')
    c.line(4, 28, 7, 25, 3, 'iron', 4)
    c.line(25, 7, 28, 4, 3, 'nsteel')
    c.px(29, 3, 'rune', 4)
    return c.render()


ITEMS = {
    'star_shard': star_shard, 'dragon_core': dragon_core, 'forge_core': forge_core, 'curse_residue': curse_residue,
    'world_thread': world_thread, 'rewind_talisman': rewind_talisman, 'purifying_dew': purifying_dew,
    'mana_crystal': mana_crystal, 'dungeon_key': dungeon_key, 'field_guide': field_guide, 'forge_tool': forge_tool,
    'dragon_coat': dragon_coat, 'teia_boots': teia_boots, 'omniregistry_treasure': omniregistry_treasure,
    'dodge_talon': dodge_talon, 'dodge_talon_active': lambda: dodge_talon(True),
    'last_bloom': last_bloom, 'last_bloom_closed': lambda: last_bloom(False),
    'parry_emblem': parry_emblem, 'parry_emblem_active': lambda: parry_emblem(True),
    'squad_banner': squad_banner, 'squad_banner_active': lambda: squad_banner(True),
    'villager_king_token': villager_king_token, 'focus_cell': focus_cell,
}
# recharging: the item's own sprite with its colour and light drained
DIMMED = {'dodge_talon_recharging': 'dodge_talon', 'parry_emblem_recharging': 'parry_emblem', 'squad_banner_recharging': 'squad_banner'}


# ------------------------------------------------------------------------------------------------------------ the armour

def armour_layer(layer):
    """The dragon-furnace armour worn (64 x 32, the humanoid armour layout). Layer 1: the chestplate (body and arms,
    dragon scales, the core at the breast) and Teia's boots (the legs' feet: white, cyan lines, a wing of light at the
    heel). Layer 2: leggings of the same scales (no item wears them, but the material has them)."""
    c = Canvas(64, 32)

    def scales(x0, y0, x1, y1, phase=0):
        c.rect(x0, y0, x1, y1, 'scale', 2)
        for row, y in enumerate(range(y0, y1 + 1, 2)):
            for x in range(x0 + ((row + phase) % 2) * 2, x1 + 1, 4):
                c.px(x, y, 'scale', 4)
                c.px(x + 1, y, 'scale', 3)
                if y + 1 <= y1:
                    c.px(x, y + 1, 'scale', 1)

    if layer == 1:
        # the body box (8 x 12 x 4 at 16,16): top, bottom, right, front, left, back
        scales(20, 16, 27, 19)
        scales(28, 16, 35, 19)
        scales(16, 20, 19, 31)
        scales(20, 20, 27, 31)
        scales(28, 20, 31, 31)
        scales(32, 20, 39, 31, 1)
        # gold trim at the neck and the hem, the core at the breast (front: 20..27 x 20..31)
        c.rect(20, 20, 27, 20, 'gold', 3)
        c.rect(32, 20, 39, 20, 'gold', 3)
        c.rect(16, 31, 39, 31, 'gold', 2)
        c.rect(22, 23, 25, 26, 'gold', 4)
        c.rect(23, 24, 24, 25, 'ember', 4)
        c.px(22, 23, 'ember', 3)
        c.px(25, 26, 'ember', 2)
        # the arms (4 x 12 x 4 at 40,16): the pauldron over the upper arm, a scaled sleeve to the elbow
        scales(44, 16, 47, 19)
        scales(40, 20, 55, 27)
        c.rect(40, 20, 55, 21, 'gold', 3)
        c.rect(40, 27, 55, 27, 'gold', 2)
        # Teia's boots on the legs' feet (4 x 12 x 4 at 0,16): the lowest five rows, and the soles
        c.rect(0, 26, 15, 31, 'white', 3)
        c.rect(8, 16, 11, 19, 'white', 2)
        c.rect(0, 26, 15, 26, 'cyan', 4)
        c.rect(4, 29, 7, 29, 'cyan', 3)
        c.rect(12, 29, 15, 29, 'cyan', 3)
        c.rect(0, 31, 15, 31, 'iron', 2)
        # the wing of light on the outer side (0..3)
        c.px(1, 27, 'feather', 4)
        c.px(2, 27, 'feather', 4)
        c.px(0, 28, 'feather', 3)
        c.px(1, 28, 'feather', 4)
        c.px(2, 28, 'rune', 4)
    else:
        # the leggings: the waist on the body box (16,16) and the legs (0,16)
        scales(20, 26, 27, 31)
        scales(16, 26, 19, 31)
        scales(28, 26, 39, 31, 1)
        c.rect(16, 26, 39, 26, 'gold', 3)
        scales(0, 20, 15, 30)
        scales(4, 16, 11, 19)
        c.rect(0, 25, 15, 25, 'gold', 2)
    return c.render(outline=False)


def main(out, preview):
    tex = os.path.join(out, 'textures', 'item')
    os.makedirs(tex, exist_ok=True)
    made = {}
    for name, fn in ITEMS.items():
        img = fn()
        img.save(os.path.join(tex, name + '.png'))
        made[name] = img
    for name, src in DIMMED.items():
        made[name] = dim(made[src])
        made[name].save(os.path.join(tex, name + '.png'))
    arm = os.path.join(out, 'textures', 'models', 'armor')
    os.makedirs(arm, exist_ok=True)
    layers = []
    for n in (1, 2):
        img = armour_layer(n)
        img.save(os.path.join(arm, 'dragon_furnace_layer_%d.png' % n))
        layers.append(img)
    # the preview: every sprite at 6x on a grey ground, the armour layers under them
    names = list(made)
    cols = 8
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * 200, rows * 200 + 2 * 200), (96, 96, 108, 255))
    for i, n in enumerate(names):
        big = made[n].resize((192, 192), Image.NEAREST)
        sheet.alpha_composite(big, ((i % cols) * 200 + 4, (i // cols) * 200 + 4))
    for k, img in enumerate(layers):
        big = img.resize((384, 192), Image.NEAREST)
        sheet.alpha_composite(big, (k * 400 + 4, rows * 200 + 4))
    sheet.save(preview)
    print('made', len(made), 'sprites and 2 armour layers')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

"""textures.py <out dir>: the item textures of the user's OROR Duel Dominion 0.17.0-alpha, drawn again (059e, the user:
"Duel Dominionのアイテムのテクスチャ調節して").

All 32x32, pixel art in Minecraft's manner (a dark outline, light from the upper left, a few tones per material):
- the ten ofuda: long strips of washi (not rounded cards), a cord at the top, the talisman's colour in a band and in its
  ink sign, brush strokes above and below, a vermilion seal; the forbidden Calamity on blackened paper in blood ink;
- the effigy (katashiro): a white paper doll, folded hem, a faint spirit-blue edge (not a first-aid doll);
- the bound hair: a black lock with blue sheen tied with a red-and-white cord and a paper tag;
- the soul archive: a thread-bound ledger with a soul flame; the grimoire: leather, gold corners and sigil, a clasp;
- the undead ash: a heap with embers and a bone; the white glove: a gentleman's dueling glove with a gold cuff.
"""
import os
import sys

from PIL import Image

W = H = 32


def rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)) + (255,)


def dark(c, t=0.35):
    return mix(c, (0, 0, 0), t)


def light(c, t=0.35):
    return mix(c, (255, 255, 255), t)


class Px:
    def __init__(self):
        self.im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        self.p = self.im.load()

    def set(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.p[x, y] = c

    def get(self, x, y):
        if 0 <= x < W and 0 <= y < H:
            return self.p[x, y]
        return (0, 0, 0, 0)

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def pts(self, pts, c):
        for x, y in pts:
            self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        for y in range(int(cy - r) - 1, int(cy + r) + 2):
            for x in range(int(cx - r) - 1, int(cx + r) + 2):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, c)

    def ring(self, cx, cy, r, c, w=1.0):
        for y in range(int(cy - r) - 2, int(cy + r) + 3):
            for x in range(int(cx - r) - 2, int(cx + r) + 3):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if r - w <= d <= r:
                    self.set(x, y, c)

    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y + 0.5 - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(round(xs[i])), int(round(xs[i + 1])) + 1):
                    self.set(x, y, c)

    def outline(self, c):
        """A one-pixel outline around everything drawn (8-neighbourhood)."""
        add = []
        for y in range(H):
            for x in range(W):
                if self.p[x, y][3] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        if self.get(x + dx, y + dy)[3] and self.get(x + dx, y + dy) != c:
                            add.append((x, y))
                            break
        for x, y in add:
            self.p[x, y] = c

    def save(self, path):
        self.im.save(path)


# ------------------------------------------------------------------------------------------------------- the ofuda

PAPER = rgb('#efe5cc')
PAPER_HI = rgb('#fbf6e8')
PAPER_LO = rgb('#d6c7a3')
PAPER_EDGE = rgb('#4a3a2a')
INK = rgb('#231b17')
SEAL = rgb('#c2332a')
SEAL_LO = rgb('#8e1f19')
CORD = rgb('#b02a24')

# the strip: x 10..21 (12 wide), y 3..30
SX0, SX1, SY0, SY1 = 10, 21, 3, 30


def strip(px, paper=PAPER, hi=PAPER_HI, lo=PAPER_LO, edge=PAPER_EDGE):
    px.rect(SX0, SY0, SX1, SY1, paper)
    for y in range(SY0, SY1 + 1):
        px.set(SX0, y, hi)
        px.set(SX1, y, lo)
        if y % 5 == 2:
            px.set(SX1 - 1, y, lo)      # a little washi fibre on the shaded side
    for x in range(SX0, SX1 + 1):
        px.set(x, SY0, hi)
        px.set(x, SY1, lo)
    # the torn foot: a couple of nicks
    px.set(SX0 + 3, SY1, (0, 0, 0, 0))
    px.set(SX0 + 8, SY1, (0, 0, 0, 0))
    px.outline(edge)
    # the cord: through a hole at the top, tied off
    px.set(15, SY0 + 1, edge)
    px.set(16, SY0 + 1, edge)
    px.pts([(15, 2), (16, 1), (15, 0), (17, 2)], CORD)
    px.set(14, 1, light(CORD, 0.3))


def band(px, color):
    px.rect(SX0 + 1, SY0 + 2, SX1 - 1, SY0 + 3, color)
    px.rect(SX0 + 1, SY0 + 4, SX1 - 1, SY0 + 4, dark(color, 0.25))
    px.rect(SX0 + 1, SY1 - 2, SX1 - 1, SY1 - 2, color)


def brush(px, ink):
    # pseudo-calligraphy: a stroke with a hook above the sign, a short column of strokes below it
    px.pts([(13, 9), (14, 9), (15, 9), (16, 9), (17, 9), (18, 9), (15, 10), (15, 11), (14, 11)], ink)
    px.pts([(12, 23), (13, 23), (14, 23), (13, 24), (13, 25), (12, 26), (14, 26)], ink)


def seal(px):
    px.rect(16, 23, 19, 26, SEAL)
    px.pts([(16, 26), (19, 23)], SEAL_LO)
    px.pts([(17, 24), (18, 25)], light(SEAL, 0.4))


def sign(px, kind, c):
    """The talisman's own sign in its colour, in the middle of the strip (x 11..20, y 12..22)."""
    d = dark(c, 0.3)
    L = light(c, 0.3)
    if kind == 'retribution':          # two arrows turning back on each other
        px.ring(15.5, 17, 4.2, c, 1.2)
        px.pts([(19, 14), (20, 15), (18, 15), (12, 19), (11, 18), (13, 18)], d)
        px.pts([(15, 17), (16, 17)], d)
    elif kind == 'healing':            # a sprout with two leaves
        px.line(15, 22, 15, 15, d)
        px.line(16, 22, 16, 16, d)
        px.poly([(15, 16), (12, 13), (11, 15), (13, 17)], c)
        px.poly([(16, 15), (19, 12), (20, 14), (18, 17)], c)
        px.pts([(12, 14), (19, 13)], L)
    elif kind == 'binding':            # a chain of three links, crossed by a cord
        px.rect(14, 12, 17, 15, c)
        px.rect(15, 13, 16, 14, (0, 0, 0, 0))
        px.rect(13, 15, 18, 18, d)
        px.rect(14, 16, 17, 17, PAPER)
        px.rect(14, 18, 17, 21, c)
        px.rect(15, 19, 16, 20, (0, 0, 0, 0))
        px.line(11, 22, 20, 12, CORD)
        for x, y in ((15, 13), (16, 13), (15, 14), (16, 14), (15, 19), (16, 19), (15, 20), (16, 20)):
            if px.get(x, y)[3] == 0:
                px.set(x, y, PAPER)
    elif kind == 'guardian':           # a shield with a torii mark
        px.poly([(12, 12), (19, 12), (19, 17), (15, 22), (16, 22), (12, 17)], c)
        px.rect(13, 14, 18, 14, d)
        px.rect(14, 15, 14, 19, d)
        px.rect(17, 15, 17, 19, d)
        px.rect(12, 12, 19, 12, L)
    elif kind == 'malice_transfer':    # one dark orb passing into another
        px.disc(13.5, 15, 2.2, d)
        px.ring(18, 19.5, 2.3, c, 1.0)
        px.line(15, 16, 17, 18, c)
        px.pts([(17, 17), (16, 18)], c)
        px.set(13, 14, L)
    elif kind == 'soul_seeker':        # an eye in a reticle
        px.ring(15.5, 17, 4.3, c, 1.0)
        px.poly([(12, 17), (15, 15), (16, 15), (19, 17), (16, 19), (15, 19)], L)
        px.disc(15.5, 17, 1.2, d)
        px.pts([(15, 12), (16, 12), (15, 22), (16, 22), (11, 17), (20, 17)], c)
    elif kind == 'exorcism':           # a purifying flame
        px.poly([(15, 12), (19, 17), (18, 21), (13, 21), (12, 17), (14, 15)], c)
        px.poly([(15, 15), (17, 18), (16, 21), (14, 21), (14, 18)], L)
        px.pts([(15, 20), (16, 20)], light(L, 0.5))
    elif kind == 'night_parade':       # an oni mask, horns and eyes
        px.poly([(12, 15), (19, 15), (19, 20), (17, 22), (14, 22), (12, 20)], c)
        px.pts([(12, 14), (12, 13), (13, 14), (19, 14), (19, 13), (18, 14)], d)
        px.pts([(13, 17), (14, 17), (17, 17), (18, 17)], light(SEAL, 0.2))
        px.pts([(14, 20), (15, 20), (16, 20), (17, 20)], d)
    elif kind == 'revival':            # a spiral rising out of a cup
        px.ring(15.5, 16, 3.3, c, 1.0)
        px.ring(15.5, 16, 1.5, c, 1.0)
        px.rect(12, 20, 19, 20, d)
        px.rect(13, 21, 18, 21, d)
        px.set(15, 18, c)
        px.set(16, 19, c)
    elif kind == 'calamity':           # an eye of ruin split by a crack
        px.poly([(11, 17), (14, 14), (17, 14), (20, 17), (17, 20), (14, 20)], c)
        px.disc(15.5, 17, 1.6, rgb('#0b0507'))
        px.pts([(15, 16)], light(c, 0.6))
        px.line(15, 12, 16, 15, rgb('#0b0507'))
        px.line(16, 19, 15, 22, rgb('#0b0507'))


OFUDA = {
    'retribution': '#c43a2f',
    'healing': '#3f9a4a',
    'binding': '#6e4bb0',
    'guardian': '#c8a12c',
    'malice_transfer': '#a2305a',
    'soul_seeker': '#2a8fbf',
    'exorcism': '#e0702a',
    'night_parade': '#2b3a7a',
    'revival': '#2a9c8c',
    'calamity': '#b0192a',
}


def ofuda(kind):
    px = Px()
    c = rgb(OFUDA[kind])
    if kind == 'calamity':
        # the forbidden one: paper burnt black at the edges, blood ink
        strip(px, rgb('#3b3034'), rgb('#57494e'), rgb('#251d21'), rgb('#120c0e'))
        band(px, rgb('#5b0f19'))
        brush(px, rgb('#a3121f'))
        sign(px, kind, c)
        px.rect(16, 23, 19, 26, rgb('#7a0d16'))
        px.pts([(11, 7), (20, 12), (11, 24), (20, 21)], rgb('#6e1520'))
    else:
        strip(px)
        band(px, c)
        brush(px, INK)
        sign(px, kind, c)
        seal(px)
    return px


# ------------------------------------------------------------------------------------------------------- the rest

def effigy():
    """A katashiro in the shape of a person in kimono: a round head with its hair bun, long hanging furisode sleeves,
    the collar crossed left over right, an obi, the skirts falling to a hem cut in shide zigzags; pure white washi with a
    faint spirit-blue edge, an ink sign on the skirt and vermilion edges on the obi."""
    px = Px()
    white, hi, lo, fold = rgb('#f6f3ec'), rgb('#ffffff'), rgb('#d9d4c8'), rgb('#bdb6a6')
    line = rgb('#8a8273')
    px.disc(15.5, 6.8, 3.3, white)                                   # head
    px.disc(15.5, 1.3, 1.2, white)                                   # the hair bun, apart from the head
    px.rect(14, 9, 17, 9, white)                                     # neck
    # shoulders, the long sleeves hanging, the body narrowing to the hem
    px.poly([(9, 10), (22, 10), (27, 12), (28, 27), (23, 27), (21, 14), (20, 26), (11, 26), (10, 14), (8, 27), (3, 27), (4, 12)], white)
    # the sleeves' rounded bottoms
    px.pts([(3, 27), (28, 27), (3, 26), (28, 26)], (0, 0, 0, 0))
    # the hem cut in shide zigzags
    for i, x in enumerate(range(11, 21)):
        for y in range(26, 29 + (i % 2)):
            px.set(x, y, white)
    px.pts([(12, 29), (14, 29), (16, 29), (18, 29), (20, 29)], (0, 0, 0, 0))
    # shading: the sleeves' openings, their shaded backs, the skirts' fold
    for y in range(13, 27):
        px.set(26, y, lo)
        px.set(5, y, hi)
        px.set(9, y, fold)
        px.set(22, y, fold)
    px.rect(4, 26, 8, 27, lo)
    px.rect(23, 26, 27, 27, lo)
    px.rect(8, 12, 9, 13, fold)                                       # the sleeves' openings at the wrist
    px.rect(22, 12, 23, 13, fold)
    for y in range(18, 27):
        px.set(19, y, lo)
    px.pts([(13, 5), (14, 5), (13, 6)], hi)
    px.outline(rgb('#86a6c4'))                                       # a faint spirit-blue edge
    # the collar crossed left over right, down to the obi
    px.line(13, 10, 16, 15, line)
    px.line(18, 10, 16, 13, line)
    px.pts([(14, 10), (17, 10)], fold)
    # the obi, vermilion-edged, and its knot
    px.rect(11, 15, 20, 17, rgb('#ebe4d4'))
    px.rect(11, 15, 20, 15, SEAL)
    px.rect(11, 17, 20, 17, SEAL)
    px.pts([(15, 16), (16, 16)], SEAL_LO)
    # an ink sign on the skirt
    px.pts([(14, 20), (15, 20), (16, 20), (17, 20), (15, 21), (15, 22), (14, 23), (16, 23), (17, 24), (15, 24)], INK)
    return px


def bound_hair():
    px = Px()
    hair, sheen, deep = rgb('#2a2530'), rgb('#5d6984'), rgb('#120f16')
    # the lock: a tapering curve from the tie (upper left) to its tip (lower right)
    import math
    for i in range(0, 200):
        t = i / 199.0
        cx = 9 + 15 * t + 3.5 * math.sin(t * math.pi)
        cy = 9 + 19 * t - 2.5 * math.sin(t * math.pi)
        r = 3.4 * (1 - t) + 0.6
        px.disc(cx, cy, r, hair)
    # strands of sheen following the curve
    for off in (-1.6, 0.4, 1.8):
        for i in range(10, 170):
            t = i / 199.0
            cx = 9 + 15 * t + 3.5 * math.sin(t * math.pi) + off * (1 - t) * 0.8
            cy = 9 + 19 * t - 2.5 * math.sin(t * math.pi) - off * (1 - t) * 0.6
            if (i // 9) % 2 == 0:
                px.set(int(round(cx)), int(round(cy)), sheen if off < 1 else light(hair, 0.15))
    px.outline(deep)
    # the red-and-white cord (mizuhiki) wound round the lock, and its bow
    for k, col in enumerate((SEAL, rgb('#f2ece2'), SEAL)):
        px.line(5 + k, 9 + k, 10 + k, 4 + k, col)
    px.poly([(4, 4), (8, 6), (5, 9), (2, 7)], SEAL)
    px.poly([(9, 1), (11, 5), (8, 6), (7, 2)], rgb('#f2ece2'))
    px.pts([(4, 5), (9, 2)], light(SEAL, 0.35))
    # a paper tag hanging from the cord
    px.line(3, 9, 3, 13, PAPER_EDGE)
    px.rect(1, 13, 6, 21, PAPER)
    px.rect(6, 13, 6, 21, PAPER_LO)
    px.rect(1, 21, 6, 21, PAPER_LO)
    px.pts([(3, 15), (4, 15), (3, 16), (2, 17), (4, 17), (3, 18), (3, 19)], INK)
    px.set(5, 19, SEAL)
    return px


def soul_archive():
    """The soul box (魂匣): a box of black lacquer seen from above and in front, gold maki-e clouds on its lid, a red
    cord tied about it, and spirit light leaking blue from under the lid."""
    px = Px()
    lac, lac_hi, lac_lo = rgb('#241a22'), rgb('#3e2f3b'), rgb('#120b10')
    gold, gold_lo = rgb('#e2b54a'), rgb('#9b7424')
    # the lid's top (a parallelogram) and the box's front
    px.poly([(4, 9), (10, 4), (28, 4), (22, 9)], lac_hi)
    px.rect(4, 9, 22, 12, lac)                                       # the lid's front rim
    px.poly([(22, 9), (28, 4), (28, 7), (22, 12)], lac_lo)            # the lid's side
    px.rect(5, 13, 21, 27, lac)                                      # the box's front
    px.poly([(21, 13), (27, 8), (27, 22), (21, 27)], lac_lo)          # the box's side
    # spirit light from under the lid
    px.rect(5, 13, 21, 13, rgb('#7fdcff'))
    px.pts([(22, 12), (23, 11), (24, 10), (25, 9), (26, 8)], rgb('#7fdcff'))
    px.rect(6, 14, 20, 14, rgb('#2f6f8f'))
    # gold maki-e: clouds on the lid, a band and a crest on the front
    px.pts([(9, 7), (10, 6), (11, 6), (12, 7), (17, 6), (18, 5), (19, 5), (20, 6), (21, 6), (13, 8), (14, 8)], gold)
    px.rect(4, 12, 22, 12, gold_lo)
    px.ring(13, 20, 3.4, gold, 1.0)
    px.pts([(13, 18), (12, 20), (14, 20), (13, 22)], gold)
    px.pts([(6, 26), (7, 26), (19, 26), (20, 26)], gold_lo)
    # the red cord tied across the front, its bow
    px.rect(5, 17, 21, 17, SEAL)
    px.pts([(21, 17), (22, 16), (23, 15), (24, 14), (25, 13), (26, 12), (27, 11)], SEAL)
    px.poly([(11, 16), (8, 13), (8, 16)], SEAL)
    px.poly([(15, 16), (18, 13), (18, 16)], SEAL)
    px.pts([(9, 18), (10, 20), (16, 18), (17, 20)], SEAL_LO)
    px.outline(rgb('#060305'))
    return px


def grimoire():
    px = Px()
    leather, hi, lo = rgb('#4a2a5e'), rgb('#6a4384'), rgb('#2e1a3b')
    gold, gold_lo = rgb('#e3b341'), rgb('#9a7420')
    px.rect(6, 4, 25, 27, leather)
    px.rect(6, 4, 25, 4, hi)
    px.rect(6, 4, 6, 27, hi)
    px.rect(25, 5, 25, 27, lo)
    px.rect(6, 27, 25, 27, lo)
    px.rect(8, 28, 26, 28, rgb('#e8dfc4'))                            # page block
    px.rect(26, 6, 26, 28, rgb('#d8ccaa'))
    # gold corners
    for cx, cy, sx, sy in ((7, 5, 1, 1), (24, 5, -1, 1), (7, 26, 1, -1), (24, 26, -1, -1)):
        px.pts([(cx, cy), (cx + sx, cy), (cx, cy + sy), (cx + 2 * sx, cy), (cx, cy + 2 * sy)], gold)
    # the sigil: a ring, four points and a cyan gem
    px.ring(15.5, 15.5, 5.2, gold, 1.0)
    px.pts([(15, 9), (16, 9), (15, 22), (16, 22), (9, 15), (9, 16), (22, 15), (22, 16)], gold)
    px.poly([(15, 13), (18, 15), (16, 18), (13, 16)], rgb('#3fd9e8'))
    px.pts([(15, 14)], rgb('#d9fbff'))
    px.pts([(16, 17), (17, 16)], rgb('#1f8a96'))
    # the clasp on the right
    px.rect(23, 14, 27, 17, gold)
    px.rect(23, 17, 27, 17, gold_lo)
    px.set(26, 15, rgb('#5c4210'))
    px.outline(rgb('#170c1e'))
    return px


def grimoire_open():
    """The grimoire held open (its model while it is read): two pages spread under the reader's eyes, ink lines and
    the gold sigil, the purple leather showing round them."""
    px = Px()
    leather, gold = rgb('#4a2a5e'), rgb('#e3b341')
    paper, paper_lo, ink = rgb('#efe4c8'), rgb('#cdbf9b'), rgb('#3a2a1e')
    # the covers, open, seen a little from above
    px.poly([(2, 10), (15, 7), (16, 25), (3, 27)], leather)
    px.poly([(16, 7), (29, 10), (28, 27), (15, 25)], leather)
    # the pages
    px.poly([(4, 10), (15, 8), (15, 23), (5, 25)], paper)
    px.poly([(16, 8), (27, 10), (26, 25), (16, 23)], paper)
    for y in range(9, 24):
        px.set(15, y, paper_lo)
        px.set(16, y, paper_lo)
    px.pts([(5, 26), (6, 26), (25, 26), (26, 26)], paper_lo)
    # writing on the left page, the sigil on the right
    for k, y in enumerate((12, 15, 18, 21)):
        px.line(6, y + 1 - k // 2, 13, y - k // 2, ink)
    px.ring(21.5, 16, 3.3, gold, 1.0)
    px.pts([(21, 16), (22, 16), (21, 12), (22, 12), (21, 20), (22, 20)], gold)
    px.pts([(21, 15), (22, 17)], rgb('#3fd9e8'))
    px.outline(rgb('#170c1e'))
    return px


def ash():
    px = Px()
    a, hi, lo = rgb('#8e8b88'), rgb('#b9b6b2'), rgb('#63605e')
    px.poly([(4, 27), (9, 20), (13, 17), (17, 16), (21, 18), (26, 22), (29, 27)], a)
    px.poly([(9, 20), (13, 17), (17, 16), (15, 19), (11, 21)], hi)
    px.rect(5, 26, 28, 27, lo)
    for x, y in ((8, 24), (12, 22), (19, 21), (23, 24), (16, 25), (25, 26), (10, 26)):
        px.set(x, y, lo)
    for x, y in ((14, 21), (21, 23), (11, 25)):
        px.set(x, y, rgb('#ff8a2a'))
    px.set(14, 20, rgb('#ffd27a'))
    # a bone fragment
    px.line(18, 19, 23, 17, rgb('#e9e2cf'))
    px.pts([(17, 18), (17, 20), (24, 16), (24, 18)], rgb('#e9e2cf'))
    px.outline(rgb('#2f2d2c'))
    # a wisp of smoke
    px.pts([(15, 13), (16, 12), (16, 11), (15, 10), (15, 9), (16, 8)], rgb('#a8a4a0'))
    return px


def glove():
    px = Px()
    w, hi, lo = rgb('#f3f1ee'), rgb('#ffffff'), rgb('#c9c6c2')
    # four fingers and a thumb, the back of a right glove
    for x0, top in ((9, 5), (13, 3), (17, 4), (21, 7)):
        px.rect(x0, top, x0 + 2, 15, w)
        px.set(x0, top, (0, 0, 0, 0))
        px.set(x0 + 2, top, (0, 0, 0, 0))
        px.rect(x0 + 2, top + 1, x0 + 2, 15, lo)
        px.set(x0, top + 1, hi)
    px.poly([(9, 14), (24, 14), (24, 21), (21, 25), (11, 25), (8, 21)], w)
    px.poly([(5, 15), (8, 13), (10, 16), (9, 20), (7, 19)], w)              # thumb
    px.pts([(6, 15), (7, 14)], hi)
    # stitching on the back
    for x in (12, 16, 20):
        px.pts([(x, 17), (x, 19), (x, 21)], lo)
    px.rect(22, 15, 24, 21, lo)
    # the cuff, with a gold band and a button
    px.rect(10, 25, 22, 29, w)
    px.rect(10, 25, 22, 25, rgb('#e3b341'))
    px.rect(10, 29, 22, 29, lo)
    px.rect(21, 26, 22, 29, lo)
    px.set(16, 27, rgb('#9a7420'))
    px.outline(rgb('#55524f'))
    return px


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    made = {}
    for kind in OFUDA:
        made['ofuda_' + kind] = ofuda(kind)
    made['spirit_effigy'] = effigy()
    made['bound_hair'] = bound_hair()
    made['soul_archive'] = soul_archive()
    made['dominion_grimoire'] = grimoire()
    made['dominion_grimoire_open'] = grimoire_open()
    made['undead_ash'] = ash()
    made['white_glove'] = glove()
    for name, px in made.items():
        px.save(os.path.join(out, name + '.png'))
    print(len(made), 'textures in', out)


if __name__ == '__main__':
    main()

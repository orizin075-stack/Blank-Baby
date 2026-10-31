"""The royals' skins: one 128 x 64 texture for each of the eight roles, painted for RoyalModel (a villager's head and
long robe on a body with arms of its own, a crown, a crest, pauldrons and a cape), and previews of each from the front,
the back and three quarters.

  python3 royal_skins.py <textures out dir> [<preview out dir>]

PARTS is the model: the same boxes, pivots and texture offsets as RoyalModel.java (java() prints that code).
"""
import math, os, random, sys
import numpy as np
from PIL import Image

W, H = 128, 64
# name: (parent, pivot, box origin, size (w, h, d), uv, inflate)
PARTS = {
    'head': (None, (0, 0, 0), (-4, -10, -4), (8, 10, 8), (0, 0), 0),
    'nose': ('head', (0, -2, 0), (-1, -1, -6), (2, 4, 2), (24, 0), 0),
    'hat': ('head', (0, 0, 0), (-4, -10, -4), (8, 10, 8), (32, 0), 0.45),
    'crown': ('head', (0, 0, 0), (-4.5, -13, -4.5), (9, 3, 9), (64, 0), 0),
    'crest': ('head', (0, 0, 0), (-0.5, -15, -3), (1, 5, 7), (100, 0), 0),
    'body': (None, (0, 0, 0), (-4, 0, -3), (8, 12, 6), (0, 18), 0),
    'robe': ('body', (0, 0, 0), (-4, 0, -3), (8, 20, 6), (28, 18), 0.5),
    'cape': ('body', (0, 0.5, 3.6), (-5, 0, 0), (10, 20, 1), (88, 30), 0),
    'right_arm': (None, (-5, 2, 0), (-3, -2, -2), (4, 12, 4), (56, 18), 0),
    'left_arm': (None, (5, 2, 0), (-1, -2, -2), (4, 12, 4), (72, 18), 0),
    'right_pauldron': ('right_arm', (0, 0, 0), (-3.5, -2.6, -2.5), (5, 4, 5), (88, 12), 0.1),
    'left_pauldron': ('left_arm', (0, 0, 0), (-1.5, -2.6, -2.5), (5, 4, 5), (108, 12), 0.1),
    'right_leg': (None, (-2, 12, 0), (-2, 0, -2), (4, 12, 4), (56, 34), 0),
    'left_leg': (None, (2, 12, 0), (-2, 0, -2), (4, 12, 4), (72, 34), 0),
}
# which of the optional parts each role wears (RoyalModel.show)
WEARS = {
    'villager_king': {'crown', 'cape'},
    'villager_general': {'hat', 'crest', 'right_pauldron', 'left_pauldron', 'cape'},
    'imperial_guard': {'hat', 'crest', 'right_pauldron', 'left_pauldron', 'cape'},
    'royal_bodyguard': {'hat', 'right_pauldron', 'left_pauldron'},
    'kingdom_guard': {'hat'},
    'royal_mage': {'hat'},
    'royal_archmage': {'hat', 'cape'},
    'royal_sage': {'hat'},
}
OPTIONAL = ('hat', 'crown', 'crest', 'right_pauldron', 'left_pauldron', 'cape')


def faces(part):
    """The six faces of a part's box in the texture: name -> (x, y, w, h). Seen from outside: front is the side the
    entity faces, right is the entity's right; on a side face the left edge is toward the back for 'right' and toward
    the front for 'left'; on top the lower edge is toward the front."""
    _, _, _, (w, h, d), (u, v), _ = PARTS[part]
    return {'top': (u + d, v, w, d), 'bottom': (u + d + w, v, w, d), 'right': (u, v + d, d, h),
            'front': (u + d, v + d, w, h), 'left': (u + d + w, v + d, d, h), 'back': (u + 2 * d + w, v + d, w, h)}


def check_layout():
    used = np.zeros((H, W), int)
    for p in PARTS:
        for f, (x, y, w, h) in faces(p).items():
            assert x >= 0 and y >= 0 and x + w <= W and y + h <= H, (p, f)
            used[y:y + h, x:x + w] += 1
    assert used.max() == 1, 'overlapping texture regions'


class Skin:
    def __init__(self, seed):
        self.img = np.zeros((H, W, 4), np.uint8)
        self.rng = random.Random(seed)

    def px(self, part, face, fx, fy, col, a=255):
        x, y, w, h = faces(part)[face]
        if 0 <= fx < w and 0 <= fy < h:
            self.img[y + fy, x + fx] = (*[max(0, min(255, int(c))) for c in col], a)

    def clear(self, part, face, fx, fy):
        x, y, w, h = faces(part)[face]
        if 0 <= fx < w and 0 <= fy < h:
            self.img[y + fy, x + fx] = 0

    def fill(self, part, col, faces_=None, noise=3, edge=0.86, top=1.12):
        for f, (x, y, w, h) in faces(part).items():
            if faces_ and f not in faces_:
                continue
            k = top if f == 'top' else 0.8 if f == 'bottom' else 1.0
            for fy in range(h):
                for fx in range(w):
                    e = edge if (fx in (0, w - 1) and w > 2) or (fy in (0, h - 1) and h > 2 and f not in ('top', 'bottom')) else 1.0
                    n = self.rng.uniform(-noise, noise)
                    self.px(part, f, fx, fy, [c * k * e + n for c in col])

    def size(self, part, face):
        return faces(part)[face][2:]

    def rows(self, part, fys, col, faces_=('front', 'back', 'left', 'right'), noise=2):
        for f in faces_:
            w, h = self.size(part, f)
            for fy in fys:
                for fx in range(w):
                    if 0 <= fy < h:
                        self.px(part, f, fx, fy, [c + self.rng.uniform(-noise, noise) for c in col])

    def cols(self, part, face, fxs, col, fys=None, noise=2):
        w, h = self.size(part, face)
        for fx in fxs:
            for fy in (fys if fys is not None else range(h)):
                self.px(part, face, fx, fy, [c + self.rng.uniform(-noise, noise) for c in col])

    def stamp(self, part, face, ox, oy, rows, palette):
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch != '.':
                    self.px(part, face, ox + i, oy + j, palette[ch])

    def save(self, path):
        Image.fromarray(self.img, 'RGBA').save(path)


SKIN = (190, 140, 106)
SKIN_DARK = (150, 104, 78)
EYE = (40, 120, 60)
GOLD = (232, 182, 52)
GOLD_DARK = (170, 120, 30)
ERMINE = (238, 236, 228)


def face(s, beard=None, brow=(110, 74, 52), skin=SKIN, eyes=EYE):
    """A villager's face, kept calm: even skin, a soft brow, small dark-centred eyes (no staring whites), the long nose a
    shade darker below; a trimmed beard of the given colour if any."""
    s.fill('head', skin, noise=2, edge=0.94)
    s.fill('nose', [c * 0.97 for c in skin], noise=1, edge=0.92)
    for fx in range(2):
        s.px('nose', 'front', fx, 3, [c * 0.88 for c in skin])
    for fx in (1, 2, 5, 6):
        s.px('head', 'front', fx, 3, brow)
    for fx, c in ((1, [c * 0.9 for c in skin]), (2, eyes), (5, eyes), (6, [c * 0.9 for c in skin])):
        s.px('head', 'front', fx, 4, c)
    s.px('head', 'front', 2, 4, [c * 0.55 for c in eyes])
    s.px('head', 'front', 5, 4, [c * 0.55 for c in eyes])
    for fx in (1, 6):
        s.px('head', 'front', fx, 6, [min(255, c * 1.04 + d) for c, d in zip(skin, (14, -4, -4))])
    if beard:
        shade = [c * 0.86 for c in beard]
        rows = ['........', '........', '........', '........', '........', '........', 'B......B', 'BB....BB', 'BBBBBBBB', '.BBBBBB.']
        for fy, row in enumerate(rows):
            for fx, ch in enumerate(row):
                if ch == 'B':
                    s.px('head', 'front', fx, fy, beard if (fx + fy) % 3 else shade)
        for f in ('left', 'right'):
            for fy in range(6, 10):
                for fx in range(8):
                    if (f == 'right' and fx >= 5) or (f == 'left' and fx <= 2):
                        s.px('head', f, fx, fy, beard if (fx + fy) % 3 else shade)
        # the moustache under the nose
        for fx in range(2):
            s.px('nose', 'bottom', fx, 0, beard)
    # hair: the top and the back of the head
    hair = beard or (80, 56, 38)
    s.fill('head', [c * 0.95 for c in hair], faces_=('top',), noise=3)
    for fy in range(0, 2):
        s.rows('head', [fy], hair, faces_=('back', 'left', 'right', 'front'), noise=3)
    # the back of the head and the back half of its sides
    s.rows('head', range(2, 9), hair, faces_=('back',), noise=3)
    for fy in range(2, 7):
        for fx in range(3):
            s.px('head', 'right', fx, fy, hair)
            s.px('head', 'left', 7 - fx, fy, hair)


def hands(s, part, col):
    s.rows(part, [9, 10, 11], col, noise=4)
    s.fill(part, col, faces_=('bottom',), noise=3)


def clear(s, part):
    x, y, w, h = PARTS[part][4][0], PARTS[part][4][1], 0, 0
    for f, (x, y, w, h) in faces(part).items():
        s.img[y:y + h, x:x + w] = 0


def helmet(s, steel, trim, open_face=True, band=None):
    """A helmet on the hat layer: crown and sides of the head covered, the face open below the brow."""
    s.fill('hat', steel, noise=6, edge=0.85, top=1.15)
    w, h = s.size('hat', 'front')
    if open_face:
        for fy in range(3, h):
            for fx in range(1, w - 1):
                s.clear('hat', 'front', fx, fy)
        for f in ('left', 'right'):
            for fy in range(6, h):
                for fx in range(w):
                    if (f == 'right' and fx >= 3) or (f == 'left' and fx <= 4):
                        s.clear('hat', f, fx, fy)
        for fy in range(7, h):
            for fx in range(w):
                s.clear('hat', 'back', fx, fy)
    s.fill('hat', [c * 0.6 for c in steel], faces_=('bottom',), noise=0)
    s.clear('hat', 'bottom', 0, 0)
    x, y, ww, hh = faces('hat')['bottom']
    s.img[y:y + hh, x:x + ww] = 0
    if band:
        s.rows('hat', [2], band, faces_=('front', 'back', 'left', 'right'))
    s.rows('hat', [0], [c * 1.1 for c in steel], faces_=('front', 'back', 'left', 'right'), noise=3)
    if trim:
        s.cols('hat', 'front', [3, 4], trim, fys=range(0, 3))
        s.cols('hat', 'back', [3, 4], trim, fys=range(0, 7))


def hood(s, cloth, trim):
    s.fill('hat', cloth, noise=6, edge=0.85)
    w, h = s.size('hat', 'front')
    for fy in range(2, h):
        for fx in range(1, w - 1):
            s.clear('hat', 'front', fx, fy)
    for f in ('left', 'right'):
        for fy in range(8, h):
            for fx in range(w):
                s.clear('hat', f, fx, fy)
    x, y, ww, hh = faces('hat')['bottom']
    s.img[y:y + hh, x:x + ww] = 0
    for fx in range(w):
        s.px('hat', 'front', fx, 1, trim)
    for fy in range(2, h):
        s.px('hat', 'front', 0, fy, trim)
        s.px('hat', 'front', w - 1, fy, trim)


def plate(s, part, steel, dark, trim=None, faces_=('front', 'back', 'left', 'right', 'top', 'bottom')):
    """Plate armour: bands of steel, each lit along its top row and shadowed at its lower edge, a trim at the hem."""
    s.fill(part, steel, faces_=faces_, noise=2, edge=0.88, top=1.15)
    light = [min(255, c * 1.16) for c in steel]
    for f in faces_:
        if f in ('top', 'bottom'):
            continue
        w, h = s.size(part, f)
        for fy in range(h):
            for fx in range(w):
                if fy % 3 == 0:
                    s.px(part, f, fx, fy, light)
                elif fy % 3 == 2:
                    s.px(part, f, fx, fy, dark)
        if trim:
            for fx in range(w):
                s.px(part, f, fx, h - 1, trim)


def chain(s, part, grey, faces_=('front', 'back', 'left', 'right')):
    for f in faces_:
        w, h = s.size(part, f)
        for fy in range(h):
            for fx in range(w):
                c = grey if (fx + fy) % 2 == 0 else [v * 0.7 for v in grey]
                s.px(part, f, fx, fy, [v + s.rng.uniform(-6, 6) for v in c])


def robe(s, cloth, trim=None, hem=None, centre=None):
    s.fill('robe', cloth, noise=7, edge=0.85)
    w, h = s.size('robe', 'front')
    if centre:
        s.cols('robe', 'front', [3, 4], centre, fys=range(0, h))
    if trim:
        s.rows('robe', [h - 2], trim)
    if hem:
        s.rows('robe', [h - 1], hem)
    x, y, ww, hh = faces('robe')['top']
    s.img[y:y + hh, x:x + ww] = 0
    x, y, ww, hh = faces('robe')['bottom']
    s.img[y:y + hh, x:x + ww] = 0


def cape(s, cloth, lining, border=None, collar=None):
    s.fill('cape', cloth, faces_=('back', 'left', 'right', 'top', 'bottom'), noise=7, edge=0.85)
    s.fill('cape', lining, faces_=('front',), noise=5, edge=0.9)
    w, h = s.size('cape', 'back')
    if border:
        for fy in range(h):
            s.px('cape', 'back', 0, fy, border)
            s.px('cape', 'back', w - 1, fy, border)
        for fx in range(w):
            s.px('cape', 'back', fx, h - 1, border)
    if collar:
        for fy in range(0, 3):
            for fx in range(w):
                s.px('cape', 'back', fx, fy, collar(fx, fy))


def ermine(fx, fy):
    return (25, 25, 25) if (fx * 3 + fy * 5) % 7 == 0 else ERMINE


def legs(s, col, boot):
    for p in ('right_leg', 'left_leg'):
        s.fill(p, col, noise=6, edge=0.85)
        s.rows(p, [9, 10, 11], boot)
        s.fill(p, boot, faces_=('bottom',), noise=3)


# ---------------------------------------------------------------------------------------------------------- the roles
def king(s):
    crimson, crimson_dark, purple = (150, 22, 38), (100, 12, 26), (70, 26, 90)
    face(s, beard=(232, 232, 226), brow=(220, 220, 214))
    s.fill('body', crimson, noise=6)
    robe(s, crimson, trim=GOLD, hem=ERMINE, centre=GOLD)
    # ermine stole over the shoulders and the gold chain of office
    for f in ('front', 'back', 'left', 'right'):
        w, _ = s.size('robe', f)
        for fy in range(0, 3):
            for fx in range(w):
                s.px('robe', f, fx, fy, ermine(fx, fy))
    for fx, fy in ((1, 3), (2, 4), (3, 5), (4, 5), (5, 4), (6, 3)):
        s.px('robe', 'front', fx, fy, GOLD)
    s.px('robe', 'front', 3, 6, (200, 30, 40))
    s.px('robe', 'front', 4, 6, (200, 30, 40))
    for fy in range(8, 18, 3):
        s.px('robe', 'front', 1, fy, GOLD_DARK)
        s.px('robe', 'front', 6, fy, GOLD_DARK)
    for p in ('right_arm', 'left_arm'):
        s.fill(p, crimson, noise=6)
        s.rows(p, [0, 1], ERMINE)
        s.rows(p, [7, 8], ERMINE)
        hands(s, p, SKIN)
    legs(s, purple, (60, 40, 30))
    # the crown: a gold band with points and jewels, open on top
    s.fill('crown', GOLD, faces_=('front', 'back', 'left', 'right'), noise=10, edge=0.9)
    for f in ('front', 'back', 'left', 'right'):
        w, h = s.size('crown', f)
        for fx in range(w):
            if fx % 2 == 1:
                s.clear('crown', f, fx, 0)
        s.px('crown', f, w // 2, 1, (200, 20, 40) if f in ('front', 'back') else (40, 90, 220))
        s.px('crown', f, 1, 2, (40, 160, 70))
        s.px('crown', f, w - 2, 2, (40, 160, 70))
        for fx in range(w):
            s.px('crown', f, fx, h - 1, GOLD_DARK)
    for f in ('top', 'bottom'):
        x, y, w, h = faces('crown')[f]
        s.img[y:y + h, x:x + w] = 0
    x, y, w, h = faces('crown')['top']
    for fx in range(w):
        for fy in range(h):
            if fx in (0, w - 1) or fy in (0, h - 1):
                s.img[y + fy, x + fx] = (*GOLD_DARK, 255)
            elif fx == w // 2 or fy == h // 2:
                s.img[y + fy, x + fx] = (*GOLD, 255)
            else:
                s.img[y + fy, x + fx] = (*crimson, 255)
    cape(s, crimson, crimson_dark, border=GOLD, collar=ermine)
    w, h = s.size('cape', 'back')
    s.stamp('cape', 'back', w // 2 - 3, 6, ['G.G.G.', 'GGGGG.', 'GRGBG.', 'GGGGG.'],
            {'G': GOLD, 'R': (200, 30, 40), 'B': (40, 90, 220)})


def general(s):
    steel, dark, navy = (168, 172, 182), (104, 108, 120), (32, 40, 92)
    red = (170, 26, 30)
    face(s, beard=(92, 62, 40), brow=(70, 48, 34))
    plate(s, 'body', steel, dark)
    robe(s, navy, trim=GOLD, hem=GOLD_DARK)
    w, h = s.size('robe', 'front')
    # a gold lion's head on the chest and a red sash from shoulder to hip
    s.stamp('robe', 'front', 1, 2, ['G..G.G', 'GGGGGG', '.GRRG.', '.GGGG.', '..GG..'], {'G': GOLD, 'R': red})
    for i in range(8):
        s.px('robe', 'front', i, 8 + i // 2, red)
        s.px('robe', 'back', 7 - i, 8 + i // 2, red)
    for p in ('right_arm', 'left_arm'):
        plate(s, p, steel, dark)
        hands(s, p, (90, 92, 100))
    for p in ('right_pauldron', 'left_pauldron'):
        plate(s, p, steel, dark, trim=GOLD)
        s.fill(p, [c * 1.1 for c in steel], faces_=('top',), noise=5)
        x, y, ww, hh = faces(p)['bottom']
        s.img[y:y + hh, x:x + ww] = 0
    legs(s, dark, (60, 60, 66))
    helmet(s, steel, GOLD, band=GOLD)
    s.fill('crest', red, noise=12, edge=0.85)
    cape(s, red, (110, 16, 20), border=GOLD)


def imperial(s):
    silver, dark, blue = (214, 218, 228), (150, 156, 172), (36, 64, 160)
    white = (236, 236, 240)
    face(s)
    plate(s, 'body', silver, dark)
    robe(s, white, trim=blue, hem=GOLD)
    w, h = s.size('robe', 'front')
    # the royal guard's blue cross with a gold star in the middle
    for fy in range(1, h - 3):
        s.px('robe', 'front', 3, fy, blue)
        s.px('robe', 'front', 4, fy, blue)
        s.px('robe', 'back', 3, fy, blue)
        s.px('robe', 'back', 4, fy, blue)
    for fx in range(1, 7):
        s.px('robe', 'front', fx, 5, blue)
        s.px('robe', 'back', fx, 5, blue)
    s.px('robe', 'front', 3, 5, GOLD)
    s.px('robe', 'front', 4, 5, GOLD)
    for p in ('right_arm', 'left_arm'):
        plate(s, p, silver, dark)
        hands(s, p, (120, 124, 140))
    for p in ('right_pauldron', 'left_pauldron'):
        plate(s, p, silver, dark, trim=GOLD)
        x, y, ww, hh = faces(p)['bottom']
        s.img[y:y + hh, x:x + ww] = 0
    legs(s, dark, (80, 82, 96))
    helmet(s, silver, GOLD, band=blue)
    s.fill('crest', (60, 100, 230), noise=12, edge=0.85)
    cape(s, blue, (24, 40, 110), border=GOLD)


def bodyguard(s):
    black, dark, red = (52, 52, 60), (30, 30, 36), (164, 26, 30)
    face(s, brow=(40, 28, 20))
    plate(s, 'body', black, dark)
    robe(s, black, trim=red, hem=red, centre=red)
    for p in ('right_arm', 'left_arm'):
        plate(s, p, black, dark)
        hands(s, p, (36, 36, 40))
    for p in ('right_pauldron', 'left_pauldron'):
        plate(s, p, black, dark, trim=red)
        x, y, ww, hh = faces(p)['bottom']
        s.img[y:y + hh, x:x + ww] = 0
    legs(s, dark, (24, 24, 28))
    helmet(s, black, red, band=red)


def guard(s):
    grey, blue, yellow = (136, 136, 142), (40, 62, 144), (214, 182, 54)
    face(s)
    chain(s, 'body', grey)
    robe(s, blue, trim=yellow, hem=(30, 46, 110))
    s.stamp('robe', 'front', 2, 3, ['.YY.', 'YYYY', '.YY.', '.Y..'], {'Y': yellow})
    for p in ('right_arm', 'left_arm'):
        chain(s, p, grey)
        hands(s, p, (96, 70, 46))
    legs(s, (70, 60, 50), (60, 44, 30))
    helmet(s, (150, 152, 160), None)


def mage(s, cloth, trim, lining=None, hood_=True, beard=None, circlet=None):
    face(s, beard=beard, brow=(230, 230, 224) if beard else (70, 48, 34))
    s.fill('body', cloth, noise=6)
    robe(s, cloth, trim=trim, hem=trim, centre=trim)
    for p in ('right_arm', 'left_arm'):
        s.fill(p, cloth, noise=6)
        s.rows(p, [8], trim)
        hands(s, p, SKIN)
    legs(s, [c * 0.7 for c in cloth], (60, 44, 30))
    if hood_:
        hood(s, cloth, trim)
    else:
        clear(s, 'hat')
        if circlet:
            for f in ('front', 'back', 'left', 'right'):
                w, _ = s.size('hat', f)
                for fx in range(w):
                    s.px('hat', f, fx, 2, circlet)
            s.px('hat', 'front', 3, 2, (60, 140, 230))
            s.px('hat', 'front', 4, 2, (60, 140, 230))
    if lining:
        cape(s, cloth, lining, border=trim)


ROLES = {
    'villager_king': king,
    'villager_general': general,
    'imperial_guard': imperial,
    'royal_bodyguard': bodyguard,
    'kingdom_guard': guard,
    'royal_mage': lambda s: mage(s, (44, 74, 168), (150, 200, 240)),
    'royal_archmage': lambda s: mage(s, (90, 30, 130), GOLD, lining=(50, 16, 74)),
    'royal_sage': lambda s: mage(s, (226, 222, 204), GOLD, hood_=False, beard=(240, 240, 236), circlet=GOLD),
}


# ------------------------------------------------------------------------------------------------------------ preview
def rot(v, rx, ry, rz):
    x, y, z = v
    if rx:
        c, s_ = math.cos(rx), math.sin(rx)
        y, z = y * c - z * s_, y * s_ + z * c
    if ry:
        c, s_ = math.cos(ry), math.sin(ry)
        x, z = x * c + z * s_, -x * s_ + z * c
    if rz:
        c, s_ = math.cos(rz), math.sin(rz)
        x, y = x * c - y * s_, x * s_ + y * c
    return (x, y, z)


POSE = {'right_arm': (-0.5, 0, 0), 'left_arm': (0.15, 0, 0), 'cape': (0.12, 0, 0)}


def quads(role):
    """Every texel of every shown face as a 3D quad (model space, y down), with its colour."""
    out = []
    show = WEARS[role]
    for part, (parent, pivot, origin, (w, h, d), uv, inf) in PARTS.items():
        if part in OPTIONAL and part not in show:
            continue
        chain_ = []
        p = part
        while p:
            chain_.append(p)
            p = PARTS[p][0]

        def place(pt):
            for q in chain_:
                pv = PARTS[q][1]
                pt = rot(pt, *POSE.get(q, (0, 0, 0)))
                pt = (pt[0] + pv[0], pt[1] + pv[1], pt[2] + pv[2])
            return pt
        x0, y0, z0 = origin[0] - inf, origin[1] - inf, origin[2] - inf
        x1, y1, z1 = origin[0] + w + inf, origin[1] + h + inf, origin[2] + d + inf
        for f, (fx0, fy0, fw, fh) in faces(part).items():
            for j in range(fh):
                for i in range(fw):
                    a, b = i / fw, j / fh
                    a2, b2 = (i + 1) / fw, (j + 1) / fh
                    if f == 'front':
                        pts = [(x0 + (x1 - x0) * aa, y0 + (y1 - y0) * bb, z0) for aa, bb in ((a, b), (a2, b), (a2, b2), (a, b2))]
                    elif f == 'back':
                        pts = [(x1 - (x1 - x0) * aa, y0 + (y1 - y0) * bb, z1) for aa, bb in ((a, b), (a2, b), (a2, b2), (a, b2))]
                    elif f == 'right':
                        pts = [(x0, y0 + (y1 - y0) * bb, z1 - (z1 - z0) * aa) for aa, bb in ((a, b), (a2, b), (a2, b2), (a, b2))]
                    elif f == 'left':
                        pts = [(x1, y0 + (y1 - y0) * bb, z0 + (z1 - z0) * aa) for aa, bb in ((a, b), (a2, b), (a2, b2), (a, b2))]
                    elif f == 'top':
                        pts = [(x0 + (x1 - x0) * aa, y0, z1 - (z1 - z0) * bb) for aa, bb in ((a, b), (a2, b), (a2, b2), (a, b2))]
                    else:
                        pts = [(x0 + (x1 - x0) * aa, y1, z0 + (z1 - z0) * bb) for aa, bb in ((a, b), (a2, b), (a2, b2), (a, b2))]
                    out.append(([place(pt) for pt in pts], (fx0 + i, fy0 + j)))
    return out


def preview(tex, role, path, scale=9):
    img = np.array(tex)
    qs = quads(role)
    views = [(0.0, 'front'), (math.pi, 'back'), (-0.7, 'three quarter')]
    from PIL import ImageDraw
    canvas = Image.new('RGBA', (len(views) * 28 * scale, 44 * scale), (200, 214, 230, 255))
    draw = ImageDraw.Draw(canvas)
    for k, (yaw, _) in enumerate(views):
        items = []
        for pts, (u, v) in qs:
            c = img[v, u]
            if c[3] < 128:
                continue
            # the entity faces -z; the viewer looks at its front from -z, pitched slightly down
            vp = [rot(rot(p, 0, yaw, 0), -0.18, 0, 0) for p in pts]
            depth = sum(p[2] for p in vp) / 4
            # backface: normal from the projected winding
            (ax, ay, _), (bx, by, _), (cx, cy, _) = vp[0], vp[1], vp[2]
            items.append((depth, vp, c))
        items.sort(key=lambda t: -t[0])
        ox, oy = k * 28 * scale + 14 * scale, 15 * scale
        for depth, vp, c in items:
            poly = [(ox - p[0] * scale, oy + p[1] * scale) for p in vp]
            draw.polygon(poly, fill=tuple(int(x) for x in c[:3]) + (255,))
    canvas.save(path)


def java():
    """RoyalModel.createLayer()'s parts, from PARTS."""
    lines = []
    for part, (parent, pivot, origin, size, uv, inf) in PARTS.items():
        holder = 'root' if parent is None else parent.replace('_', '')
        name = part.replace('_', '')
        deform = f', new CubeDeformation({inf}F)' if inf else ''
        lines.append(f'        PartDefinition {name} = {holder}.addOrReplaceChild("{part}", CubeListBuilder.create().texOffs({uv[0]}, {uv[1]})'
                     f'.addBox({origin[0]}F, {origin[1]}F, {origin[2]}F, {size[0]}F, {size[1]}F, {size[2]}F{deform}), '
                     f'PartPose.offset({pivot[0]}F, {pivot[1]}F, {pivot[2]}F));')
    return '\n'.join(lines)


def hand(path):
    """The armed villagers' hands (ArmedVillagers.Hands): a 4 x 4 x 4 box on a 16 x 16 sheet, near white so the
    villager's own skin colour tints it, a little darker at the edges and the knuckles."""
    img = np.zeros((16, 16, 4), np.uint8)
    for (x, y, w, h) in ((4, 0, 4, 4), (8, 0, 4, 4), (0, 4, 4, 4), (4, 4, 4, 4), (8, 4, 4, 4), (12, 4, 4, 4)):
        for j in range(h):
            for i in range(w):
                v = 236 if 0 < i < w - 1 and 0 < j < h - 1 else 214
                img[y + j, x + i] = (v, v, v, 255)
    for i in range(4):
        img[5, 4 + i] = (205, 205, 205, 255)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(img, 'RGBA').save(path)


def main(out, prev=None):
    check_layout()
    os.makedirs(out, exist_ok=True)
    hand(os.path.join(os.path.dirname(os.path.normpath(out)), 'villager', 'hand.png'))
    for i, (role, paint) in enumerate(ROLES.items()):
        s = Skin(1000 + i)
        paint(s)
        s.save(os.path.join(out, role + '.png'))
        if prev:
            os.makedirs(prev, exist_ok=True)
            preview(Image.fromarray(s.img, 'RGBA'), role, os.path.join(prev, role + '.png'))
    print('painted', len(ROLES), 'skins')


if __name__ == '__main__':
    if sys.argv[1] == 'java':
        print(java())
    else:
        main(*sys.argv[1:3])

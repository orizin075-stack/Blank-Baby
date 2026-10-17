"""Miner villager outfits (v0.17.14), painted pixel by pixel.

Writes into <overlay>/assets/oror_supreme_bosses/textures/entity/:
  villager/profession/miner.png (+ .mcmeta)        vanilla villager model: hard hat, overalls, plaid shirt, gloves, boots
  zombie_villager/profession/miner.png (+ .mcmeta) the same for the zombie villager model (its arms hang, not crossed)
  villager/human/miner.png                          the human villager model (player skin layout): the outfit over the skin
  villager/human/miner_gear.png                     the human model's hard hat parts (HumanVillagerRenderer)

usage: python3 -I villager_outfits.py <overlay dir> [preview.png]
"""
import json
import os
import random
import sys

from PIL import Image

# palette
DENIM = (58, 79, 122)
DENIM_LIGHT = (84, 106, 150)
DENIM_DARK = (40, 55, 88)
STITCH = (150, 128, 74)
PLAID = (156, 52, 42)
PLAID_DARK = (64, 30, 30)
PLAID_MID = (108, 38, 34)
LEATHER = (138, 98, 57)
LEATHER_DARK = (104, 72, 42)
BELT = (74, 52, 35)
BRASS = (216, 169, 58)
BRASS_LIGHT = (247, 214, 120)
BOOT = (61, 43, 30)
BOOT_LIGHT = (86, 63, 44)
SOLE = (34, 24, 15)
HAT = (227, 167, 47)
HAT_LIGHT = (245, 201, 98)
HAT_DARK = (178, 124, 30)
HAT_SHADE = (140, 96, 24)
LAMP = (43, 43, 46)
LAMP_RIM = (92, 92, 98)
LENS = (255, 247, 205)
LENS_RING = (255, 222, 120)
SOOT = (30, 30, 34)

rng = random.Random(1714)


def shade(c, f):
    return tuple(max(0, min(255, int(round(v * f)))) for v in c)


class Canvas:
    def __init__(self, w=64, h=64):
        self.im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        self.px = self.im.load()

    def put(self, x, y, c, a=255):
        self.px[x, y] = (c[0], c[1], c[2], a)

    def rect(self, x0, y0, w, h, fn):
        """fn(u, v, w, h) -> colour or None for each pixel of a face."""
        for v in range(h):
            for u in range(w):
                c = fn(u, v, w, h)
                if c is not None:
                    self.put(x0 + u, y0 + v, c)

    def box(self, ox, oy, w, h, d, faces):
        """A model box's UV footprint (Minecraft layout); faces maps top/bottom/right/front/left/back to fn."""
        spots = {
            'top': (ox + d, oy, w, d), 'bottom': (ox + d + w, oy, w, d),
            'right': (ox, oy + d, d, h), 'front': (ox + d, oy + d, w, h),
            'left': (ox + d + w, oy + d, d, h), 'back': (ox + d + w + d, oy + d, w, h),
        }
        for k, fn in faces.items():
            if fn is not None:
                x, y, fw, fh = spots[k]
                self.rect(x, y, fw, fh, fn)

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.im.save(path)


def light(v, h, top=1.08, bottom=0.86):
    """Soft light from above along a face."""
    if h <= 1:
        return 1.0
    return top + (bottom - top) * v / (h - 1)


def speck(c, chance=0.08, dark=0.82):
    return shade(c, dark) if rng.random() < chance else c


# ---------------------------------------------------------------------------------------------- materials
def plaid(u, v, side=1.0):
    """Buffalo check flannel: two-pixel squares of red, black and the dark red where their bands cross."""
    a, b = (u // 2) % 2, (v // 2) % 2
    c = PLAID if a == b == 0 else (PLAID_DARK if a == b == 1 else PLAID_MID)
    return shade(c, side)


def denim(u, v, h, side=1.0, seam_cols=()):
    """Indigo twill: a faint diagonal weave, a few worn or sooty pixels."""
    c = DENIM
    if u in seam_cols:
        c = DENIM_DARK
    elif (u + v) % 4 == 0:
        c = shade(DENIM, 1.08)
    if rng.random() < 0.04:
        c = shade(c, 0.78)
    return shade(c, light(v, h, 1.04, 0.9) * side)


def boot(v, h, side=1.0):
    if v == h - 1:
        return SOLE
    c = BOOT_LIGHT if v == 0 else BOOT
    return shade(c, side)


def glove(u, v, h, side=1.0):
    c = LEATHER_DARK if v == 0 or u == 0 else LEATHER
    return shade(c, side)


def hat(u, v, w, h, side=1.0):
    """The hard hat's shell: lit from above, a scuff here and there."""
    c = shade(HAT, light(v, h, 1.1, 0.88))
    if rng.random() < 0.05:
        c = shade(c, 0.88)
    return shade(c, side)


# ---------------------------------------------------------------------------------------------- vanilla villager model
def villager_body(cv, zombie):
    # jacket (the robe at 0,38: 8x20x6 on a villager, 8x18x6 on a zombie villager): the outfit itself
    tall = 18 if zombie else 20
    foot = tall - 1

    def jacket_front(u, v, w, h):
        if v >= tall - 1:
            return DENIM_DARK  # the hem; the boots are on the legs below
        if v == 11:
            return BRASS if u in (3, 4) else BELT
        if v >= 12:
            if v in (foot - 3, foot - 2) and u in (1, 2, 5, 6):
                return DENIM_LIGHT  # worn knees
            return denim(u, v, h, seam_cols=(3, 4) if v >= 13 else ())
        bib = 1 <= u <= 6 and v >= 3
        strap = u in (1, 6) and v < 3
        if bib or strap:
            if v == 3 and u in (1, 6):
                return BRASS_LIGHT
            if bib and 5 <= v <= 7 and 2 <= u <= 5:
                return DENIM_LIGHT if v == 5 else DENIM_DARK  # the bib pocket
            return denim(u, v, h)
        return plaid(u, v)

    def jacket_side(u, v, w, h):
        if v >= tall - 1:
            return shade(DENIM_DARK, 0.9)
        if v == 11:
            return shade(BELT, 0.9) if u != 2 else LEATHER  # a pouch on the hip
        if v == 10 and u in (1, 2):
            return LEATHER_DARK
        if v >= 12:
            return denim(u, v, h, 0.9)
        return plaid(u, v, 0.9)

    def jacket_back(u, v, w, h):
        if v >= tall - 1:
            return shade(DENIM_DARK, 0.85)
        if v == 11:
            return shade(BELT, 0.85)
        if v >= 7:
            return denim(u, v, h, 0.85)
        # the straps cross on the back
        if u == v + 1 or u == 6 - v or (v == 0 and u in (1, 6)):
            return shade(DENIM, 0.9)
        return plaid(u, v, 0.85)

    def jacket_top(u, v, w, h):
        if u in (1, 6):
            return DENIM
        return plaid(u, v, 1.1)

    def jacket_bottom(u, v, w, h):
        return DENIM_DARK

    cv.box(0, 38, 8, tall, 6, {'top': jacket_top, 'bottom': jacket_bottom, 'right': jacket_side,
                             'front': jacket_front, 'left': jacket_side, 'back': jacket_back})
    # body (16,20, 8x12x6) under the robe: the same shirt and bib, so nothing pale shows at the edges
    cv.box(16, 20, 8, 12, 6, {'top': jacket_top, 'right': lambda u, v, w, h: plaid(u, v, 0.9),
                              'front': lambda u, v, w, h: jacket_front(u, v, w, tall) if v < 11 else BELT,
                              'left': lambda u, v, w, h: plaid(u, v, 0.9),
                              'back': lambda u, v, w, h: jacket_back(u, v, w, tall)})
    # legs (0,22, 4x12x4): what shows under the robe is trouser leg and boot
    def leg(side):
        return lambda u, v, w, h: boot(v - 8, 4, side) if v >= 8 else denim(u, v, h, side, seam_cols=())
    cv.box(0, 22, 4, 12, 4, {'top': None, 'bottom': lambda u, v, w, h: SOLE, 'right': leg(0.9),
                             'front': leg(1.0), 'left': leg(0.9), 'back': leg(0.85)})
    if zombie:
        # zombie villager arms (44,22, 4x12x4), held out: sleeves down to the gloves
        def arm(side):
            return lambda u, v, w, h: glove(u, v - 9, 3, side) if v >= 9 else plaid(u, v, side)
        cv.box(44, 22, 4, 12, 4, {'top': lambda u, v, w, h: plaid(u, v, 1.1), 'bottom': lambda u, v, w, h: LEATHER_DARK,
                                  'right': arm(0.9), 'front': arm(1.0), 'left': arm(0.9), 'back': arm(0.85)})
    else:
        # crossed arms: upper arms (44,22, 4x8x4) in sleeves, forearms and hands across (40,38, 8x4x4) in gloves
        def upper(side):
            return lambda u, v, w, h: plaid(u, v, side)
        cv.box(44, 22, 4, 8, 4, {'top': lambda u, v, w, h: plaid(u, v, 1.1), 'bottom': lambda u, v, w, h: PLAID_DARK,
                                 'right': upper(0.9), 'front': upper(1.0), 'left': upper(0.9), 'back': upper(0.85)})

        def fore(side):
            return lambda u, v, w, h: glove(u, v, h, side) if 2 <= u <= 5 else plaid(u, v, side)
        cv.box(40, 38, 8, 4, 4, {'top': fore(1.1), 'bottom': fore(0.8), 'right': lambda u, v, w, h: plaid(u, v, 0.9),
                                 'front': fore(1.0), 'left': lambda u, v, w, h: plaid(u, v, 0.9), 'back': fore(0.85)})


def villager_hat(cv, zombie):
    # the hat layer (32,0, 8x10x8): a hard hat over the top four rows, the face left bare
    def side(lamp):
        def fn(u, v, w, h):
            if v >= 4:
                return None
            if lamp and 2 <= u <= 5 and 1 <= v <= 2:
                if u in (3, 4):
                    return LENS if v == 1 else LENS_RING
                return LAMP
            if v == 3:
                return HAT_SHADE
            return hat(u, v, w, 4, 1.0 if lamp else 0.92)
        return fn

    def top(u, v, w, h):
        if u in (3, 4):
            return HAT_LIGHT if v % 2 == 0 else HAT  # the ridge
        return hat(u, v, w, h, 1.05)

    cv.box(32, 0, 8, 10, 8, {'top': top, 'bottom': None, 'right': side(False), 'front': side(True),
                             'left': side(False), 'back': side(False)})
    # the rim (30,47, 16x16x1, lying flat at brow height): a narrow brim, a peak at the front
    ring = 1

    def rim(f):
        def fn(u, v, w, h):
            inner = 4 <= u <= 11 and 4 <= v <= 11
            lo, hi = 4 - ring, 11 + ring
            if lo <= u <= hi and lo <= v <= hi and not inner:
                return shade(HAT_DARK, f)
            if 4 <= u <= 11 and 12 <= v <= 13:
                return shade(HAT, f)  # the peak, toward the front
            return None
        return fn

    cv.rect(31, 48, 16, 16, rim(1.0))
    cv.rect(48, 48, 16, 16, rim(0.7))


def vanilla(zombie):
    cv = Canvas()
    villager_body(cv, zombie)
    villager_hat(cv, zombie)
    return cv


# ---------------------------------------------------------------------------------------------- human model
def human():
    """Overlay in player-skin layout (64x64): the base layer of body, arms and legs; the head is left to the skin."""
    cv = Canvas()

    def torso_front(u, v, w, h):
        if v == 10:
            return BRASS if u in (3, 4) else BELT
        if v == 11:
            return denim(u, v, h)
        bib = 1 <= u <= 6 and v >= 4
        strap = u in (1, 6) and v < 4
        if bib or strap:
            if v == 4 and u in (1, 6):
                return BRASS_LIGHT
            if bib and 6 <= v <= 8 and 2 <= u <= 5:
                return DENIM_LIGHT if v == 6 else DENIM_DARK  # the bib pocket
            return denim(u, v, h)
        return plaid(u, v)

    def torso_side(u, v, w, h):
        if v == 10:
            return LEATHER if u in (1, 2) else shade(BELT, 0.9)
        if v == 11 or v == 9 and u in (1, 2):
            return LEATHER_DARK if v == 9 else denim(u, v, h, 0.9)
        return plaid(u, v, 0.9)

    def torso_back(u, v, w, h):
        if v == 10:
            return shade(BELT, 0.85)
        if v >= 7:
            return denim(u, v, h, 0.85)
        if u == v + 1 or u == 6 - v:
            return shade(DENIM, 0.9)
        return plaid(u, v, 0.85)

    def torso_top(u, v, w, h):
        return DENIM if u in (1, 6) else plaid(u, v, 1.1)

    cv.box(16, 16, 8, 12, 4, {'top': torso_top, 'bottom': lambda u, v, w, h: DENIM_DARK, 'right': torso_side,
                              'front': torso_front, 'left': torso_side, 'back': torso_back})

    def sleeve(side, mirror=False):
        def fn(u, v, w, h):
            if v >= 9:
                return glove(u, v - 9, 3, side)
            if v == 8:
                return shade(PLAID_DARK, side)  # a turned-back cuff
            return plaid(u, v, side)
        return fn

    for ox, oy in ((40, 16), (32, 48)):
        cv.box(ox, oy, 4, 12, 4, {'top': lambda u, v, w, h: plaid(u, v, 1.1), 'bottom': lambda u, v, w, h: LEATHER_DARK,
                                  'right': sleeve(0.9), 'front': sleeve(1.0), 'left': sleeve(0.9), 'back': sleeve(0.85)})

    def trouser(side, front=False):
        def fn(u, v, w, h):
            if v >= 8:
                return boot(v - 8, 4, side)
            if front and v in (5, 6) and u in (1, 2):
                return DENIM_LIGHT  # a worn knee
            return denim(u, v, h, side)
        return fn

    for ox, oy in ((0, 16), (16, 48)):
        cv.box(ox, oy, 4, 12, 4, {'top': lambda u, v, w, h: DENIM, 'bottom': lambda u, v, w, h: SOLE,
                                  'right': trouser(0.9), 'front': trouser(1.0, True), 'left': trouser(0.9), 'back': trouser(0.85)})
    return cv


def gear():
    """The human model's hard hat (64x32): shell 9x4x9 at 0,0; ridge 2x1x9 at 40,0; rim 10x1x10 at 0,14; peak 9x1x2 at
    40,14; lamp 3x2x1 at 40,20; lens at 50,20 (drawn full bright)."""
    cv = Canvas(64, 32)

    def shell_side(f):
        def fn(u, v, w, h):
            return hat(u, v, w, h, f)
        return fn

    def shell_top(u, v, w, h):
        d = abs(u - 4) + abs(v - 4)
        c = shade(HAT, 1.12 - 0.035 * d)
        if rng.random() < 0.04:
            c = shade(c, 0.9)
        return c

    cv.box(0, 0, 9, 4, 9, {'top': shell_top, 'bottom': lambda u, v, w, h: HAT_SHADE, 'right': shell_side(0.9),
                           'front': shell_side(1.0), 'left': shell_side(0.9), 'back': shell_side(0.82)})
    ridge = lambda u, v, w, h: HAT
    cv.box(40, 0, 2, 1, 9, {'top': lambda u, v, w, h: HAT_LIGHT, 'bottom': ridge, 'right': ridge, 'front': ridge, 'left': ridge, 'back': ridge})
    cv.box(0, 14, 10, 1, 10, {'top': lambda u, v, w, h: HAT_DARK, 'bottom': lambda u, v, w, h: HAT_SHADE,
                              'right': lambda u, v, w, h: HAT_DARK, 'front': lambda u, v, w, h: HAT,
                              'left': lambda u, v, w, h: HAT_DARK, 'back': lambda u, v, w, h: HAT_SHADE})
    cv.box(40, 14, 9, 1, 2, {'top': lambda u, v, w, h: HAT, 'bottom': lambda u, v, w, h: HAT_SHADE,
                             'right': lambda u, v, w, h: HAT_DARK, 'front': lambda u, v, w, h: HAT_LIGHT,
                             'left': lambda u, v, w, h: HAT_DARK, 'back': lambda u, v, w, h: HAT_DARK})
    cv.box(40, 20, 3, 2, 1, {'top': lambda u, v, w, h: LAMP_RIM, 'bottom': lambda u, v, w, h: LAMP,
                             'right': lambda u, v, w, h: LAMP, 'front': lambda u, v, w, h: LAMP_RIM if v == 0 else LAMP,
                             'left': lambda u, v, w, h: LAMP, 'back': lambda u, v, w, h: LAMP})
    # the lens (2x1x0.25 at 50,20): its front face spans u 50.25-52.25, v 20.25-21.25
    for x in range(50, 54):
        for y in range(20, 22):
            cv.put(x, y, LENS if 50 < x < 53 else LENS_RING)
    return cv


def mcmeta(path):
    with open(path + '.mcmeta', 'w') as f:
        json.dump({'villager': {'hat': 'full'}}, f, indent=2)
        f.write('\n')


def main():
    overlay = sys.argv[1]
    base = os.path.join(overlay, 'assets', 'oror_supreme_bosses', 'textures', 'entity')
    out = {
        os.path.join(base, 'villager', 'profession', 'miner.png'): vanilla(False),
        os.path.join(base, 'zombie_villager', 'profession', 'miner.png'): vanilla(True),
        os.path.join(base, 'villager', 'human', 'miner.png'): human(),
        os.path.join(base, 'villager', 'human', 'miner_gear.png'): gear(),
    }
    for path, cv in out.items():
        cv.save(path)
        if '/profession/' in path.replace(os.sep, '/'):
            mcmeta(path)
        print('wrote', path)
    if len(sys.argv) > 2:
        sheet = Image.new('RGBA', (64 * 4 + 30, 64), (255, 0, 255, 255))
        for i, cv in enumerate(out.values()):
            sheet.alpha_composite(cv.im, (i * 74, 0))
        sheet.resize((sheet.width * 6, sheet.height * 6), Image.NEAREST).save(sys.argv[2])


if __name__ == '__main__':
    main()

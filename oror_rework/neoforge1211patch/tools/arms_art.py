"""arms_art.py <out textures dir> <preview.png>: the forbidden vault's arms as 32x32 pixel art (051).

The weapons kept to bring the Villager King down: the five king-slayers (sword, axe, bow, crossbow, trident; the bow's
and the crossbow's drawn states too) and the vault's three named blades, whose sprites were placeholders (a flat cyan
bar, a gold arrow, the netherite sword's own texture). Each is drawn on a material grid in the weapon's own frame: a is
the distance along the diagonal from the handle (bottom left) to the tip (top right), p the offset across it (negative
toward the top left). Every material has a five-tone ramp; a pixel is lit one tone where the light (from the top left)
falls on it from outside its material and darkened one tone on its far side, glowing materials keep their tone, and a
dark outline is laid round the whole.
"""
import math, os, sys
from PIL import Image

RAMPS = {
    'nsteel': ['#17131b', '#29232e', '#3f3646', '#62586a', '#9a8fa3'],
    'edge': ['#3a3442', '#5d5468', '#8a8094', '#b8afc2', '#e6e0ee'],
    'crim': ['#4a0710', '#8c1020', '#d42030', '#ff5a48', '#ffd0a8'],
    'gold': ['#4e300c', '#87561a', '#c4922c', '#efc955', '#fff3b0'],
    'leather': ['#260b0e', '#3e1418', '#5c2026', '#7e3036', '#a24850'],
    'wood': ['#1c130f', '#2f2119', '#463125', '#614532', '#7e5c42'],
    'azure': ['#0c2442', '#1b4a80', '#2c80c0', '#66c2ee', '#d4f4ff'],
    'amber': ['#4e2206', '#8c440e', '#cf7a1a', '#f4b03e', '#ffe29c'],
    'violet': ['#1e0f36', '#3a1d66', '#6236a2', '#9a6ade', '#e2ccff'],
    'silver': ['#262a32', '#444b58', '#717a88', '#aab3c0', '#eef2f6'],
    'star': ['#5e4e22', '#a28c40', '#e2cc72', '#fff2b4', '#ffffff'],
    'teal': ['#08262a', '#0f4a4a', '#1b7a74', '#38b2a4', '#a4eedc'],
    'string': ['#3a0a10', '#6e1420', '#b02a34', '#e85a5a', '#ffb0a0'],
    'ghost': ['#2a2048', '#4c3c86', '#7c6ac4', '#b6a8f0', '#f2ecff'],
}
GLOW = {'crim', 'string', 'star', 'ghost'}
OUTLINE = (16, 10, 18, 255)


def rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


class Sprite:
    def __init__(self):
        self.mat = [[None] * 32 for _ in range(32)]
        self.tone = [[2] * 32 for _ in range(32)]
        self.fixed = [[False] * 32 for _ in range(32)]

    def put(self, x, y, m, tone=None):
        if 0 <= x < 32 and 0 <= y < 32:
            self.mat[y][x] = m
            if tone is not None:
                self.tone[y][x] = tone
                self.fixed[y][x] = True
            else:
                self.tone[y][x] = 2
                self.fixed[y][x] = False

    def get(self, x, y):
        return self.mat[y][x] if 0 <= x < 32 and 0 <= y < 32 else None

    def fill(self, test):
        """test(a, p, x, y) -> material, (material, tone) or None, over the whole grid in the diagonal frame."""
        for y in range(32):
            for x in range(32):
                a, p = x - y, x + y - 31
                r = test(a, p, x, y)
                if r is None:
                    continue
                if isinstance(r, tuple):
                    self.put(x, y, r[0], r[1])
                else:
                    self.put(x, y, r)

    def render(self):
        img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        px = img.load()
        for y in range(32):
            for x in range(32):
                m = self.mat[y][x]
                if m is None:
                    continue
                t = self.tone[y][x]
                if not self.fixed[y][x] and m not in GLOW:
                    up, left = self.get(x, y - 1), self.get(x - 1, y)
                    down, right = self.get(x, y + 1), self.get(x + 1, y)
                    if up != m or left != m:
                        t += 1
                    if down != m or right != m:
                        t -= 1
                t = max(0, min(4, t))
                px[x, y] = rgb(RAMPS[m][t])
        # the outline: every empty pixel touching the sprite (sides only, so diagonals stay a clean staircase)
        out = img.copy()
        op = out.load()
        for y in range(32):
            for x in range(32):
                if px[x, y][3]:
                    continue
                if any(0 <= x + dx < 32 and 0 <= y + dy < 32 and px[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    op[x, y] = OUTLINE
        return out


SQ = math.sqrt(0.5)


def frame(x, y):
    """A pixel's centre in the weapon's frame, in pixels: a along the diagonal from the bottom left (handle) to the top
    right (tip), p across it (negative toward the top left)."""
    cx, cy = x + 0.5 - 16, y + 0.5 - 16
    return (cx - cy) * SQ, (cx + cy) * SQ


def pix(a, p):
    """The pixel at frame point (a, p)."""
    x = 16 + (a + p) * SQ
    y = 16 + (p - a) * SQ
    return int(math.floor(x)), int(math.floor(y))


def fill(s, test):
    for y in range(32):
        for x in range(32):
            a, p = frame(x, y)
            r = test(a, p)
            if r is None:
                continue
            if isinstance(r, tuple):
                s.put(x, y, r[0], r[1])
            else:
                s.put(x, y, r)


def stroke(s, pts, radius, mat, tone=None, only_empty=False):
    """A line through frame points, every pixel whose centre lies within radius of it."""
    segs = list(zip(pts, pts[1:]))
    for y in range(32):
        for x in range(32):
            a, p = frame(x, y)
            best = 1e9
            for (a0, p0), (a1, p1) in segs:
                da, dp = a1 - a0, p1 - p0
                L = da * da + dp * dp
                u = 0 if L == 0 else max(0, min(1, ((a - a0) * da + (p - p0) * dp) / L))
                best = min(best, math.hypot(a - a0 - u * da, p - p0 - u * dp))
            if best <= radius and (not only_empty or s.get(x, y) is None):
                s.put(x, y, mat, tone)


# ---------------------------------------------------------------------------------------------------- king-slayers

def kingslayer_sword():
    """界断: a black netherite greatsword, its fuller a seam of crimson fire broken by runes; the guard a golden crown,
    cracked through; a grip of blood leather wound with gold wire; a gold pommel holding a crimson stone."""
    s = Sprite()

    def t(a, p):
        if -6.2 <= a <= 20.6:                               # the blade
            hw = 1.75 if a < 1 else 1.35 if a < 15 else 1.35 * (20.6 - a) / 5.6
            if abs(p) > hw:
                return None
            if p < -hw + 0.8:
                return ('edge', 4 if a < 18 else 3)
            if p > hw - 0.8:
                return ('edge', 1)
            if abs(p) < 0.55 and -4.5 <= a <= 15:
                k = (a + 4.5) % 4.0
                return ('crim', 4 if 1.2 < k < 2.0 else 1 if k > 3.3 else 3)
            return 'nsteel'
        if -8.3 <= a < -6.2:                                # the crown band
            if abs(p) <= 5.6:
                if abs(p) < 0.8:
                    return ('crim', 3)                      # the stone at its heart
                return ('gold', 3) if a > -7.2 else ('gold', 1)
            return None
        if -14.6 <= a < -8.3 and abs(p) <= 1.0:            # the grip
            if a > -9.6:
                return 'gold'
            k = (a + p * 0.9) % 2.4
            return ('gold', 3) if k < 0.7 else ('leather', 2 if p < 0 else 1)
        d = math.hypot(a + 16.6, p)
        if d <= 2.15:                                       # the pommel
            return ('crim', 4) if d <= 0.8 else ('crim', 2) if d <= 1.3 else 'gold'
        return None

    fill(s, t)
    # the crown's points up the blade, the middle one on the right broken off, a crack down to the stone
    for pc, h in ((-5.0, 3.0), (-2.6, 2.0), (5.0, 3.0)):
        stroke(s, [(-6.6, pc), (-6.6 + h, pc)], 0.6, 'gold', None, only_empty=True)
    stroke(s, [(-6.6, 2.6), (-5.4, 2.9)], 0.5, 'gold', 1, only_empty=True)
    stroke(s, [(-8.0, 1.5), (-6.9, 2.3)], 0.45, 'crim', 1)
    return s


def kingslayer_axe():
    """断罪: an executioner's great axe: a long black haft bound in gold and blood leather; a narrow neck flaring into a
    broad bearded head whose curved edge burns crimson, a crack of fire through it; a gold spike behind and a spear point
    above."""
    s = Sprite()
    c = 8.5

    def t(a, p):
        if 11.5 < a <= 20.5 and abs(p) <= 1.1 * (20.5 - a) / 9:     # the point
            return ('edge', 3) if p < -0.2 else 'nsteel'
        if -20 <= a <= 11.5 and abs(p) <= 0.95:                     # the haft
            if a < -18.2:
                return 'gold'
            if -17.5 <= a <= -9:
                return ('gold', 3) if (a % 2.6) < 0.7 else ('leather', 2 if p < 0 else 1)
            if -9 < a <= -7.8 or 3.2 <= a <= 4.4 or 12.0 <= a <= 13.0:
                return 'gold'
            return 'wood'
        if -14.0 <= p <= -0.9:                                      # the head, out to the top left
            d = -p
            half = 1.7 if d < 4.0 else 1.7 + (d - 4.0) * 1.15        # the neck, then the flare
            lo, hi = c - half * 1.15, c + half * 0.85               # the beard hangs lower (toward the handle)
            if not (lo <= a <= hi):
                return None
            outer = -14.0 + 0.032 * (a - c + 0.6) ** 2              # the edge, curved out
            if p < outer:
                return None
            if p < outer + 0.9:
                return ('crim', 3)
            if p < outer + 1.8:
                return ('crim', 1) if abs(a - c) > 6.5 else ('edge', 4)
            if p < outer + 2.6:
                return ('edge', 2)
            return 'nsteel'
        if 0.9 < p <= 5.0 and abs(a - c) <= 2.0 - (p - 0.9) * 0.48:  # the spike behind
            return 'gold'
        return None

    fill(s, t)
    stroke(s, [(c - 1.6, -5.2), (c + 0.4, -8.6), (c - 0.6, -10.4)], 0.42, 'crim', 2)   # the crack of fire
    return s


def bow_frame(pull):
    """天穿: a black recurve of horn and netherite, its tips capped in gold, crimson running along its back; the string
    burns. Drawn (pull 1-3) the string comes back toward the bottom right and a crimson-headed arrow lies on it."""
    s = Sprite()
    belly = 7.2 - 0.6 * pull

    def arc(t):
        b = belly * (1 - t * t) + 2.0 * max(0.0, abs(t) - 0.72) / 0.28
        return 13.6 * t, -b

    pts = [arc(-1 + 2 * i / 80) for i in range(81)]
    for i, (a, p) in enumerate(pts[:-1]):
        t = -1 + 2 * i / 80
        r = 1.25 if abs(t) < 0.22 else 0.85 if abs(t) < 0.75 else 0.6
        stroke(s, [(a, p), pts[i + 1]], r, 'nsteel')
    for i, (a, p) in enumerate(pts):
        t = -1 + 2 * i / 80
        if 0.3 < abs(t) < 0.7:
            stroke(s, [(a, p - 0.55)], 0.45, 'crim', 2)
        if abs(t) > 0.9:
            stroke(s, [(a, p)], 0.8, 'gold')
        if abs(t) < 0.16:
            stroke(s, [(a, p)], 1.3, 'leather', 2 if (i % 3) else 1)
    back = [0.0, 3.2, 5.2, 7.0][pull]
    nock = (0.0, back)
    for tip in (pts[0], pts[-1]):
        stroke(s, [tip, nock], 0.45, 'string', 3, only_empty=True)
    if pull:
        head = -belly - [0, 2.6, 3.4, 4.2][pull]
        stroke(s, [nock, (0.0, head + 1.2)], 0.5, 'silver', 3)
        stroke(s, [(0.0, head), (0.0, head + 1.6)], 0.9, 'crim', 3)
        stroke(s, [(0.0, head - 0.4)], 0.5, 'crim', 4)
        stroke(s, [(-0.9, back - 1.6), (0.9, back - 1.6)], 0.5, 'gold', 3)
    return s


def crossbow_frame(state):
    """堕星: a crossbow on a dark stock bound in gold, a steel stirrup at its nose; its thin black prod glows crimson at
    the tips and its pale string is drawn back to the nut; a falling star of gold set in the stock. state: standby,
    pulling_0..2, arrow, firework."""
    s = Sprite()
    drawn = {'standby': 0, 'pulling_0': 1, 'pulling_1': 2, 'pulling_2': 3, 'arrow': 3, 'firework': 3}[state]
    front = 8.5

    def stock(a, p):
        if -20.0 <= a <= front + 3.2:
            lo, hi = -0.95, 1.05
            if a < -12.5:
                hi = 1.05 + (-12.5 - a) * 0.22              # the butt swells toward the bottom right
            if lo <= p <= hi:
                if a < -18.6:
                    return 'gold'
                if -5.2 <= a <= -4.0 or front - 0.6 <= a <= front + 0.6:
                    return 'gold'
                return ('wood', 1) if p > 0.5 else 'wood'
        if -11.5 <= a <= -8.0 and 1.05 < p <= 3.2:          # the trigger guard
            return 'nsteel' if p > 2.4 or a < -10.8 or a > -8.7 else None
        return None

    fill(s, stock)
    # the stirrup at the nose
    stroke(s, [(front + 3.6, -1.6), (front + 5.2, -1.4), (front + 5.6, 0.1), (front + 5.2, 1.6), (front + 3.6, 1.7)], 0.45, 'silver')
    sweep = [0.8, 1.8, 2.8, 3.6][drawn]

    def prod(q):
        return front - sweep * q * q, 9.0 * q

    pts = [prod(-1 + 2 * i / 60) for i in range(61)]
    stroke(s, pts, 0.55, 'nsteel')
    for tip in (pts[0], pts[-1]):
        stroke(s, [tip], 0.85, 'crim', 3)
    nut = front - 0.8 - [0.4, 3.0, 5.4, 7.8][drawn]
    for tip in (pts[0], pts[-1]):
        stroke(s, [tip, (nut, 0.0)], 0.42, 'string', 4, only_empty=True)
    for a, p, r, t in ((-1.6, 0.05, 0.85, 4), (-2.9, 0.05, 0.45, 3), (-0.3, 0.05, 0.45, 3)):
        stroke(s, [(a, p)], r, 'star', t)
    if state == 'arrow':
        stroke(s, [(nut, -0.05), (front + 6.2, -0.05)], 0.45, 'silver', 3)
        stroke(s, [(front + 6.0, -0.05), (front + 7.6, -0.05)], 0.8, 'crim', 3)
        stroke(s, [(front + 8.0, -0.05)], 0.45, 'crim', 4)
    if state == 'firework':
        stroke(s, [(nut, -0.05), (front + 5.4, -0.05)], 1.0, 'crim', 2)
        stroke(s, [(front + 5.4, -0.05), (front + 7.2, -0.05)], 0.7, 'silver', 4)
        stroke(s, [(nut + 1.5, -0.05), (nut + 2.6, -0.05)], 1.05, 'silver', 3)
    return s


def kingslayer_trident():
    """海嘯: a trident of black sea-steel: three barbed prongs rising from a curved bar, lit crimson at their points; a
    gold collar and a haft wound in deep-sea green."""
    s = Sprite()

    def t(a, p):
        if -20.5 <= a <= 8.6 and abs(p) <= 0.95:           # the haft
            if a < -18.6 or -7.5 <= a <= -6.3:
                return 'gold'
            if a < -6.3:
                return ('teal', 3) if (a + p * 0.9) % 2.2 < 0.6 else ('teal', 1)
            return 'nsteel'
        if 6.4 <= a <= 8.6 and abs(p) <= 1.6:              # the collar
            return ('gold', 3) if a > 7.5 else 'gold'
        return None

    fill(s, t)

    def bar(p):
        return 9.6 + 0.07 * p * p                           # the bar, its ends swept forward

    stroke(s, [(bar(q / 4.0), q / 4.0) for q in range(-22, 23)], 0.75, 'nsteel')
    for pc, end in ((0.0, 21.0), (-5.5, 17.6), (5.5, 17.6)):
        stroke(s, [(bar(pc), pc), (end - 1.8, pc)], 0.62, 'nsteel')
        stroke(s, [(bar(pc) + 0.6, pc - 0.45), (end - 2.4, pc - 0.45)], 0.3, 'edge', 3)
        stroke(s, [(end - 2.0, pc), (end - 0.2, pc)], 0.6, 'crim', 3)
        stroke(s, [(end + 0.1, pc)], 0.35, 'crim', 4)
    for pc, side in ((-5.5, 1), (5.5, -1)):                 # the barbs, turned in
        stroke(s, [(15.2, pc), (14.0, pc + side * 1.3)], 0.42, 'nsteel', 1)
    stroke(s, [(17.8, 0.0), (16.6, -1.3)], 0.42, 'nsteel', 1)
    return s


# ---------------------------------------------------------------------------------------------------- vault blades

def azure_blade():
    """蒼珀の太刀: a curved tachi: an azure blade with a pale tempering line along its edge, a round amber guard, a hilt
    bound in amber over black in diamonds."""
    s = Sprite()

    def bend(a):
        return 2.4 - 0.0042 * (a + 17) ** 2

    def t(a, p):
        c = bend(a)
        q = p - c
        if -5.2 <= a <= 19.6:                               # the blade, edge on the outside of the curve (bottom right)
            hw = 1.3 if a < 15.5 else 1.3 * (19.6 - a) / 4.1
            if abs(q) > hw:
                return None
            if q < -hw + 0.75:
                return ('azure', 1)                         # the back
            if q > hw - 0.75:
                return ('azure', 4)                         # the edge
            wave = math.sin(a * 1.3) * 0.3
            if q > 0.1 + wave:
                return ('azure', 3)                         # the tempering line
            return 'azure'
        if -6.4 <= a < -5.2 and abs(q) <= 1.6:             # the collar
            return 'gold'
        if -8.0 <= a < -6.4 and abs(q) <= 3.4:             # the guard
            return ('amber', 3) if q < 0 else 'amber'
        if -18.8 <= a < -8.0 and abs(q) <= 1.05:           # the hilt
            if a < -17.4:
                return 'gold'
            k = (a % 2.4) - 1.2
            return ('amber', 3) if abs(q) < 1.0 - abs(k) * 0.9 else ('leather', 1)
        return None

    fill(s, t)
    return s


def star_staff():
    """星脈魔杖: a staff of dark wood run through with veins of starlight, a silver crescent at its head cradling a star."""
    s = Sprite()

    def t(a, p):
        if -20.5 <= a <= 8.5 and abs(p) <= 0.95:
            if a < -18.8 or -6.2 <= a <= -5.0 or 6.8 <= a <= 8.5:
                return 'silver'
            if abs(p) < 0.5 and a % 3.7 < 0.75:
                return ('star', 3)
            return 'wood'
        d = math.hypot(a - 13.6, p)
        ang = math.degrees(math.atan2(p, a - 13.6))
        if 3.6 <= d <= 5.0 and not (-55 <= ang <= 55):     # the crescent, open toward the top right
            return ('silver', 3) if p < 0 else 'silver'
        if d <= 2.6:
            r = 2.6 * (0.55 + 0.45 * abs(math.cos(2 * math.radians(ang))))
            if d <= 0.9:
                return ('star', 4)
            if d <= r:
                return ('star', 3)
        return None

    fill(s, t)
    for a, p in ((17.6, 0.0), (13.6, -3.9), (13.6, 3.9), (16.6, -2.6), (16.6, 2.6)):
        stroke(s, [(a, p)], 0.45, 'star', 3, only_empty=True)
    return s


def reverie_rapier():
    """夢幻処刑剣: an executioner's rapier out of a dream: a long thin blade of ghostly violet light paling to white at the
    point, a swept silver hilt with a violet stone, a slender grip."""
    s = Sprite()

    def t(a, p):
        if -4.5 <= a <= 21.2:
            hw = 0.9 if a < 17 else 0.9 * (21.2 - a) / 4.2
            if abs(p) > hw:
                return None
            tone = 2 + (1 if a > 4 else 0) + (1 if a > 13 else 0)
            if p < -0.2:
                return ('ghost', min(4, tone + 1))
            return ('ghost', tone - 1)
        if -6.2 <= a < -4.5 and abs(p) <= 4.2:             # the quillons
            return ('silver', 3) if a > -5.3 else 'silver'
        if -14.0 <= a < -6.2 and abs(p) <= 0.9:            # the grip
            return ('violet', 3) if (a % 1.6) < 0.5 else 'violet'
        d = math.hypot(a + 15.4, p)
        if d <= 1.7:
            return ('violet', 4) if d <= 0.7 else 'silver'
        return None

    fill(s, t)
    # the swept guard, round the knuckles on the bottom right
    pts = []
    for k in range(25):
        u = k / 24
        pts.append((-5.6 + (-13.6 + 5.6) * u, 1.0 + 3.6 * math.sin(math.pi * u)))
    stroke(s, pts, 0.5, 'silver', None, only_empty=True)
    stroke(s, [(-5.4, -0.2)], 0.65, 'violet', 4)
    return s


SPRITES = {
    'kingslayer_sword': kingslayer_sword,
    'kingslayer_axe': kingslayer_axe,
    'kingslayer_bow': lambda: bow_frame(0),
    'kingslayer_bow_pulling_0': lambda: bow_frame(1),
    'kingslayer_bow_pulling_1': lambda: bow_frame(2),
    'kingslayer_bow_pulling_2': lambda: bow_frame(3),
    'kingslayer_crossbow_standby': lambda: crossbow_frame('standby'),
    'kingslayer_crossbow_pulling_0': lambda: crossbow_frame('pulling_0'),
    'kingslayer_crossbow_pulling_1': lambda: crossbow_frame('pulling_1'),
    'kingslayer_crossbow_pulling_2': lambda: crossbow_frame('pulling_2'),
    'kingslayer_crossbow_arrow': lambda: crossbow_frame('arrow'),
    'kingslayer_crossbow_firework': lambda: crossbow_frame('firework'),
    'kingslayer_trident': kingslayer_trident,
    'azure_blade': azure_blade,
    'star_staff': star_staff,
    'reverie_rapier': reverie_rapier,
}


def main(out, preview):
    os.makedirs(out, exist_ok=True)
    imgs = {}
    for name, make in SPRITES.items():
        img = make().render()
        img.save(os.path.join(out, name + '.png'))
        imgs[name] = img
    # the preview: each at 8x on a slot-grey square, in rows
    cell = 32 * 8 + 16
    cols = 4
    rows = (len(imgs) + cols - 1) // cols
    sheet = Image.new('RGBA', (cols * cell, rows * cell), (48, 48, 56, 255))
    for i, (name, img) in enumerate(imgs.items()):
        bx, by = (i % cols) * cell, (i // cols) * cell
        bg = Image.new('RGBA', (32 * 8, 32 * 8), (139, 139, 139, 255))
        bg.alpha_composite(img.resize((32 * 8, 32 * 8), Image.NEAREST))
        sheet.alpha_composite(bg, (bx + 8, by + 8))
    sheet.save(preview)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

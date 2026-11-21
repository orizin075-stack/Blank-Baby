"""stage_kit.py: the parts the gods' stages are built of (r63, tools/citadel/god_stages.py).

A Grid of block states; cells left out keep the world's ground. Parts: boxes, cylinders, discs, rings, spheres, domes,
cones, columns, arches, lines and curves of any thickness, stairs, torii, swords, trees, flowers, roofs.
"""
import math, random

AIR = 'minecraft:air'
W, H = 55, 64
C = W // 2
DIRS = {'north': (0, -1), 'south': (0, 1), 'west': (-1, 0), 'east': (1, 0)}
OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}


def S(name, **p):
    n = name if ':' in name else 'minecraft:' + name
    if not p:
        return n
    return n + '[' + ','.join('%s=%s' % (k, v) for k, v in sorted(p.items())) + ']'


def B(name):
    """A block name with properties given as 'name[k=v]', namespaced."""
    return name if name.startswith('minecraft:') or ':' in name.split('[')[0] else 'minecraft:' + name


def stair(block, facing, half='bottom'):
    return S(block, facing=facing, half=half, shape='straight', waterlogged='false')


def slab(block, kind='bottom'):
    return S(block, type=kind, waterlogged='false')


def lantern(kind='lantern', hanging=False):
    return S(kind, hanging=str(hanging).lower(), waterlogged='false')


def outward(dx, dz):
    """The side a cell at (dx, dz) from a centre faces."""
    if abs(dx) >= abs(dz):
        return 'east' if dx > 0 else 'west'
    return 'south' if dz > 0 else 'north'


class Grid:
    def __init__(self, seed=0):
        self.c = {}
        self.be = {}
        self.spots = []
        self.rng = random.Random(seed)

    def set(self, x, y, z, st, be=None):
        x, y, z = int(round(x)), int(round(y)), int(round(z))
        if 0 <= x < W and 0 <= y < H and 0 <= z < W:
            self.c[(x, y, z)] = B(st)
            if be is not None:
                self.be[(x, y, z)] = be
            else:
                self.be.pop((x, y, z), None)

    def get(self, x, y, z):
        return self.c.get((x, y, z))

    def empty(self, x, y, z):
        s = self.c.get((x, y, z))
        return s is None or s == AIR

    def put(self, x, y, z, st):
        """Only where nothing of the stage stands yet."""
        if self.empty(x, y, z):
            self.set(x, y, z, st)

    # --- volumes
    def box(self, x0, y0, z0, x1, y1, z1, st, hollow=False, only_empty=False):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    if hollow and min(x0, x1) < x < max(x0, x1) and min(z0, z1) < z < max(z0, z1) and min(y0, y1) < y < max(y0, y1):
                        continue
                    if only_empty and not self.empty(x, y, z):
                        continue
                    self.set(x, y, z, st)

    def clear(self, cx, cz, r, y0, y1):
        """Air stored where the stage stands, so no ground or tree stays inside it (only where nothing is built)."""
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                if (x - cx) ** 2 + (z - cz) ** 2 <= r * r + r:
                    for y in range(y0, y1 + 1):
                        if (x, y, z) not in self.c:
                            self.set(x, y, z, AIR)

    def disc(self, cx, cz, r, y, st, pattern=None):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                d = math.hypot(x - cx, z - cz)
                if d <= r + 0.3:
                    self.set(x, y, z, pattern(x, z, d) if pattern else st)

    def ring(self, cx, cz, r0, r1, y, st):
        for x in range(int(cx - r1 - 1), int(cx + r1 + 2)):
            for z in range(int(cz - r1 - 1), int(cz + r1 + 2)):
                d = math.hypot(x - cx, z - cz)
                if r0 - 0.5 <= d <= r1 + 0.3:
                    self.set(x, y, z, st)

    def cyl(self, cx, cz, r, y0, y1, st, hollow=False, inner=None):
        for y in range(y0, y1 + 1):
            if hollow:
                self.ring(cx, cz, r - 0.6, r, y, st)
                if inner:
                    self.disc(cx, cz, r - 1.2, y, inner)
            else:
                self.disc(cx, cz, r, y, st)

    def sphere(self, cx, cy, cz, r, st, shell=None, squash=1.0):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for y in range(int(cy - r - 1), int(cy + r + 2)):
                for z in range(int(cz - r - 1), int(cz + r + 2)):
                    d = math.sqrt((x - cx) ** 2 + ((y - cy) / squash) ** 2 + (z - cz) ** 2)
                    if d <= r + 0.3 and (shell is None or d >= r - shell):
                        self.set(x, y, z, st)

    def dome(self, cx, y0, cz, r, st, rib=None, squash=1.0, inside=AIR):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            for z in range(int(cz - r - 1), int(cz + r + 2)):
                for dy in range(0, int(r * squash) + 2):
                    d = math.sqrt((x - cx) ** 2 + (dy / squash) ** 2 + (z - cz) ** 2)
                    if r - 1.1 <= d <= r + 0.3:
                        isrib = rib and (abs(x - cx) < 0.6 or abs(z - cz) < 0.6 or abs(abs(x - cx) - abs(z - cz)) < 0.6)
                        self.set(x, y0 + dy, z, rib if isrib else st)
                    elif d < r - 1.1 and inside:
                        self.put(x, y0 + dy, z, inside)

    def cone(self, cx, y0, cz, r, h, st, edge=None):
        for dy in range(h + 1):
            rr = r * (1 - dy / (h + 0.5))
            if rr < 0.4:
                self.set(cx, y0 + dy, cz, st)
                continue
            self.disc(cx, cz, rr, y0 + dy, st)
        if edge:
            self.set(cx, y0 + h + 1, cz, edge)

    def column(self, x, z, y0, y1, shaft, base=None, cap=None, capstair=None):
        for y in range(y0, y1 + 1):
            self.set(x, y, z, shaft)
        if base:
            self.set(x, y0, z, base)
        if cap:
            self.set(x, y1, z, cap)
        if capstair:
            for f, (dx, dz) in DIRS.items():
                self.set(x + dx, y1, z + dz, stair(capstair, OPP[f], 'top'))

    def line(self, p0, p1, st, r=0.0, only_empty=False):
        (x0, y0, z0), (x1, y1, z1) = p0, p1
        n = int(max(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)) * 2) + 1
        for i in range(n + 1):
            t = i / n
            x, y, z = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0 + (z1 - z0) * t
            self.ball(x, y, z, r, st, only_empty)

    def ball(self, x, y, z, r, st, only_empty=False):
        if r <= 0.5:
            (self.put if only_empty else self.set)(x, y, z, st)
            return
        ri = int(math.ceil(r))
        for dx in range(-ri, ri + 1):
            for dy in range(-ri, ri + 1):
                for dz in range(-ri, ri + 1):
                    if dx * dx + dy * dy + dz * dz <= r * r:
                        (self.put if only_empty else self.set)(x + dx, y + dy, z + dz, st)

    def curve(self, pts, st, r0=1.0, r1=0.0, only_empty=False, steps=None):
        """A Bezier curve through control points, its thickness going from r0 to r1."""
        n = steps or int(sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)) * 2) + 2
        for i in range(n + 1):
            t = i / n
            q = list(pts)
            while len(q) > 1:
                q = [tuple(a + (b - a) * t for a, b in zip(q[k], q[k + 1])) for k in range(len(q) - 1)]
            x, y, z = q[0]
            self.ball(x, y, z, r0 + (r1 - r0) * t, st, only_empty)

    def arch(self, x0, x1, z, y0, rise, st, axis='x', thick=1, keystone=None):
        """A round arch from x0 to x1 (or z0 to z1 when axis is 'z'), its springing at y0."""
        span = (x1 - x0) / 2.0
        mid = (x0 + x1) / 2.0
        for i in range(int(x0), int(x1) + 1):
            dx = i - mid
            h = rise * math.sqrt(max(0.0, 1 - (dx / (span + 0.5)) ** 2))
            for t in range(thick):
                y = y0 + int(round(h))
                pos = (i, y, z + t) if axis == 'x' else (z + t, y, i)
                self.set(*pos, keystone if keystone and abs(dx) < 0.6 else st)
                # fill down to the springing at the sides
                if abs(dx) > span - 1.5:
                    for yy in range(y0 - 1, y):
                        self.set(*((i, yy, z + t) if axis == 'x' else (z + t, yy, i)), st)

    def stairs_up(self, x, z, y0, n, block, facing, width=3, fill='stone_bricks'):
        """A flight of n steps of stairs 'block' rising toward facing, width wide, filled under with 'fill'."""
        dx, dz = DIRS[facing]
        px, pz = -dz, dx
        for k in range(n):
            for w in range(-(width // 2), width - width // 2):
                cx, cz = x + dx * k + px * w, z + dz * k + pz * w
                self.set(cx, y0 + k, cz, stair(block, facing))
                for yy in range(y0, y0 + k):
                    self.set(cx, yy, cz, fill)

    def torii(self, x, z, y0, width, height, axis='x', post='red_concrete', beam='black_concrete', gold='gold_block'):
        """A torii: two posts, the tie beam (nuki) two below the top, the top beam (kasagi) overhanging by two."""
        h = width // 2
        at = (lambda s, y: (x + s, y, z)) if axis == 'x' else (lambda s, y: (x, y, z + s))
        for s_ in (-h, h):
            for y in range(y0, y0 + height):
                self.set(*at(s_, y), post)
            self.set(*at(s_, y0), beam)
        for s_ in range(-h - 1, h + 2):
            self.set(*at(s_, y0 + height - 2), post)
        for s_ in range(-h - 2, h + 3):
            self.set(*at(s_, y0 + height), beam)
        self.set(*at(0, y0 + height - 1), gold)

    def sword(self, x, z, y0, length, blade='iron_block', edge='white_stained_glass', guard='gold_block', grip='dark_oak_log[axis=y]',
              pommel='gold_block', axis='x', tilt=(0, 0)):
        """A great sword stuck point first into the ground: blade two wide, a guard, a grip and a pommel."""
        tx, tz = tilt
        y = y0
        for k in range(length):
            ox, oz = tx * k / max(1, length), tz * k / max(1, length)
            self.set(x + ox, y + k, z + oz, blade)
            if k < length - 1:
                ex, ez = (1, 0) if axis == 'x' else (0, 1)
                self.set(x + ox + ex, y + k, z + oz + ez, edge if k > 0 else blade)
                self.set(x + ox - ex, y + k, z + oz - ez, edge if k > 1 else blade)
        top = y + length
        ox, oz = tx, tz
        for s in range(-3, 4):
            ex, ez = (s, 0) if axis == 'x' else (0, s)
            self.set(x + ox + ex, top, z + oz + ez, guard)
        for k in range(1, 5):
            self.set(x + ox, top + k, z + oz, grip)
        self.set(x + ox, top + 5, z + oz, pommel)

    def tree(self, x, z, y0, height, crown, log='oak_log[axis=y]', leaves='oak_leaves', fruit=None):
        for y in range(y0, y0 + height):
            self.set(x, y, z, log)
        lv = S(leaves.split('[')[0], distance='1', persistent='true', waterlogged='false')
        self.sphere(x, y0 + height, z, crown, lv, squash=0.7)
        for y in range(y0, y0 + height):
            self.set(x, y, z, log)
        if fruit:
            for _ in range(3):
                a = self.rng.random() * 6.28
                self.set(x + math.cos(a) * (crown - 1), y0 + height - 1, z + math.sin(a) * (crown - 1), fruit)

    def scatter(self, x0, z0, x1, z1, y, choices, density=0.3, need=None):
        """Plants on top of the stage's ground: each cell with a floor of 'need' under it."""
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if self.rng.random() < density and self.empty(x, y, z):
                    below = self.get(x, y - 1, z)
                    if below and (need is None or below.split('[')[0].endswith(need)):
                        self.set(x, y, z, self.rng.choice(choices))

    def roof_hip(self, x0, z0, x1, z1, y, st_block, full, flare=1, cap=None):
        """A hipped roof of stairs over a rectangle, flaring flare blocks past it."""
        x0, z0, x1, z1 = x0 - flare, z0 - flare, x1 + flare, z1 + flare
        while x0 <= x1 and z0 <= z1:
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    if x in (x0, x1) or z in (z0, z1):
                        f = 'south' if z == z0 else 'north' if z == z1 else 'east' if x == x0 else 'west'
                        if x0 == x1 or z0 == z1:
                            self.set(x, y, z, full)
                        else:
                            self.set(x, y, z, stair(st_block, f))
                    else:
                        self.set(x, y, z, full)
            x0, z0, x1, z1, y = x0 + 1, z0 + 1, x1 - 1, z1 - 1, y + 1
        if cap:
            self.set((x0 + x1) // 2, y, (z0 + z1) // 2, cap)
        return y

    def pagoda(self, cx, cz, y, r, tiers, wall, tile_stair, tile, post, gold='gold_block', glass=None, h=4):
        """Storeys shrinking upward, each under flared eaves with gilded tips."""
        for t in range(tiers):
            rr = r - t * 2
            if rr < 2:
                break
            self.box(cx - rr, y, cz - rr, cx + rr, y + h - 1, cz + rr, wall, hollow=True)
            for (px, pz) in ((cx - rr, cz - rr), (cx + rr, cz - rr), (cx - rr, cz + rr), (cx + rr, cz + rr)):
                for yy in range(y, y + h):
                    self.set(px, yy, pz, post)
            if glass:
                for k in range(-rr + 2, rr - 1, 2):
                    for (px, pz) in ((cx + k, cz - rr), (cx + k, cz + rr), (cx - rr, cz + k), (cx + rr, cz + k)):
                        self.set(px, y + 1, pz, glass)
                        self.set(px, y + 2, pz, glass)
            y += h
            ey = self.roof_hip(cx - rr, cz - rr, cx + rr, cz + rr, y, tile_stair, tile, flare=2)
            for sx in (-1, 1):
                for sz in (-1, 1):
                    self.set(cx + sx * (rr + 2), y + 1, cz + sz * (rr + 2), gold)
            y += 2
        for k in range(5):
            self.set(cx, y + k, cz, gold if k % 2 == 0 else 'chain[axis=y]')
        self.set(cx, y + 5, cz, 'lightning_rod[facing=up,powered=false,waterlogged=false]')
        return y

    def flower_bed(self, cx, cz, r, y, choices, soil='grass_block[snowy=false]'):
        self.disc(cx, cz, r, y - 1, soil)
        for x in range(cx - r, cx + r + 1):
            for z in range(cz - r, cz + r + 1):
                if math.hypot(x - cx, z - cz) <= r and self.rng.random() < 0.7:
                    self.set(x, y, z, self.rng.choice(choices))


def connect(g):
    """Panes, bars, walls and fences joined to what stands beside them."""
    def fam(s):
        n = s.split('[')[0]
        if n.endswith('_pane') or n.endswith('iron_bars'):
            return 'pane'
        if n.endswith('_wall') and 'banner' not in n and 'torch' not in n and 'sign' not in n:
            return 'wall'
        if n.endswith('_fence'):
            return 'fence'
        return None

    def solidish(n):
        nn = n.split('[')[0]
        return not any(k in nn for k in ('pane', 'bars', '_wall', 'fence', 'lantern', 'torch', 'chain', 'ladder', 'carpet', 'banner',
                                         'rod', 'stairs', 'slab', 'leaves', 'flower', 'tulip', 'rose', 'air', 'water', 'button', 'candle',
                                         'bell', 'head', 'pot', 'sapling', 'grass', 'fern', 'vine', 'coral', 'dripleaf', 'chest', 'spawner', 'seal'))
    for (x, y, z), s in list(g.c.items()):
        f = fam(s)
        if not f:
            continue
        name = s.split('[')[0]
        sides = {}
        for d, (dx, dz) in DIRS.items():
            n = g.get(x + dx, y, z + dz)
            sides[d] = n is not None and n != AIR and (fam(n) == f or (f == 'fence' and fam(n) is None and solidish(n)) or (f != 'fence' and solidish(n)))
        if f == 'pane':
            if not any(sides.values()):
                sides = {'north': False, 'south': False, 'east': True, 'west': True}
            g.c[(x, y, z)] = S(name, **{d: str(v).lower() for d, v in sides.items()}, waterlogged='false')
        elif f == 'fence':
            g.c[(x, y, z)] = S(name, **{d: str(v).lower() for d, v in sides.items()}, waterlogged='false')
        else:
            straight = (sides['north'] and sides['south'] and not sides['east'] and not sides['west']) or \
                       (sides['east'] and sides['west'] and not sides['north'] and not sides['south'])
            above = g.get(x, y + 1, z)
            up = not straight or (above is not None and above != AIR)
            g.c[(x, y, z)] = S(name, **{d: ('low' if v else 'none') for d, v in sides.items()}, up=str(up).lower(), waterlogged='false')

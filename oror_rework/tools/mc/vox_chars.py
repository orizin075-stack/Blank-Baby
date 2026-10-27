"""The design-sheet characters built the way the sheets draw them: voxel figures (vxl.Vol, half-pixel voxels),
modelled by hand from each sheet, with the face drawn on the front of the head (sface). Each recipe returns a Fig
whose sculpt holds the meshed voxels; RECIPES maps the rig key to (sheet prefix, recipe)."""
import math
import numpy as np
from designfig import Fig
from vxl import Vol, C
import sface

RECIPES = {}


def recipe(sheet):
    def deco(fn):
        RECIPES[fn.__name__] = (sheet, fn)
        return fn
    return deco


def humanoid_bones(f, head_neck, shoulder, elbow, hip, knee, waist, hipc, hover=0.0):
    """Standard bones (RigModel tags); joints given for the right side (x < 0), the left mirrors."""
    f.humanoid(hip_y=hipc, waist_y=waist, neck_y=head_neck, shoulder=shoulder, elbow=elbow, hip=hip, knee=knee, hover=hover)


def finish(f, v):
    v.surfs(f)
    f.vol = v
    return f


def hair_strands(v, rng, roots, length, colour, bone, w=(1.0, 1.8), d=(0.7, 1.1), sway=0.6, curl=0.0, out=None):
    """Locks of hair from root points, each running `length` (scalar or per root) downwards with a little sway and
    an uneven end: the sheets' long voxel hair."""
    for k, r in enumerate(roots):
        r = np.asarray(r, float)
        L = length[k] if hasattr(length, '__len__') else length
        L = L * rng.uniform(0.82, 1.0)
        n = max(2, int(L / 3) + 1)
        pts = [r]
        dirv = np.asarray(out[k], float) if out is not None else np.zeros(3)
        for i in range(1, n + 1):
            t = i / n
            p = r + np.array([dirv[0] * t * 1.5 + rng.uniform(-sway, sway) * 0.3, L * t, dirv[2] * t * 1.5 + curl * t * t])
            pts.append(p)
        ww = rng.uniform(*w)
        dd = rng.uniform(*d)
        v.strand(pts, [ww] * (n) + [ww * 0.5], [dd] * (n) + [dd * 0.7], colour, bone)


class Grid:
    """A face drawn key by key (32 x 32 for an 8-pixel head at quarter-pixel voxels)."""
    def __init__(self, base='S', n=32):
        self.n = n
        self.g = [[base] * n for _ in range(n)]

    def put(self, x, y, k):
        if 0 <= x < self.n and 0 <= y < self.n:
            self.g[y][x] = k

    def fill(self, x0, y0, x1, y1, k):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, k)

    def row(self, y, x0, s):
        for i, k in enumerate(s):
            if k != '.':
                self.put(x0 + i, y, k)

    def mirror_row(self, y, x0, s):
        self.row(y, x0, s)
        self.row(y, self.n - x0 - len(s), s[::-1])

    @property
    def rows(self):
        return [''.join(r) for r in self.g]


def sheet_head(f, v4, top, keys, face_rows, hair, hair2, skin, fringe, side_locks, crown, ears=None, raise_keys='L',
               half=4.0, tip=None):
    """A head as the sheets build it, at quarter-pixel voxels (v4): the skull with the face drawn on its front
    (face_rows, keys), a lash line standing off the face, 3D fringe strands over the forehead, side locks in front
    of the ears, the crown of the hair round the skull, pointed ears.

    fringe      [(x0, x1, bottom, layer)] strands of the fringe: x0..x1 across the face (model px), down to `bottom`
                (px below the top of the head); layer 0 lies on the forehead, 1 in front of it
    side_locks  [(x, z, bottom, width)] locks hanging at the side of the face down to `bottom` below the top
    crown       (extra x, extra top, extra back): how far the hair stands out from the skull
    ears        (colour, earring colour) or None
    """
    chin = top + 2 * half
    skin_i = v4.ci(skin)
    # skull: hair colour except the face, jaw corners stepped in
    v4.box((-half, top, -half), (half, chin, half), lambda X, Y, Z: np.where(Z < -half + 0.3, skin_i, hair(X, Y, Z)).astype(np.uint16), 'head')
    v4.carve(lambda X, Y, Z: (np.abs(X) > half - 0.3) & (Y > chin - 0.6) & (Z < -half + 0.6), (-half - 1, chin - 1, -half - 1), (half + 1, chin + 1, -half + 1))
    v4.front_paint(face_rows, -half, half, top, chin, raise_keys=raise_keys, keymap=keys)
    ex, et, eb = crown
    # crown: the hair stands out round the skull, above and behind; stepped corners
    v4.box((-half - ex, top - et, -half + 0.6), (half + ex, chin - 1.5, half + eb), hair, 'head')
    v4.box((-half - ex + 0.5, top - et - 0.5, -half + 0.4), (half + ex - 0.5, top - et + 0.5, half + eb - 0.5), hair, 'head')
    v4.box((-half - ex, top - et, -half - 0.6), (half + ex, top + 0.6, half + eb), hair, 'head')
    # fringe strands: alternate tones, a darker tip, a stepped end
    for k, (x0, x1, bottom, layer) in enumerate(fringe):
        z0 = -half - 0.25 - 0.55 * layer
        col = hair if k % 2 == 0 else hair2
        v4.box((x0, top - 0.2, z0 - 0.5), (x1, top + bottom, z0), col, 'head')
        if tip is not None:
            v4.box((x0, top + bottom - 0.5, z0 - 0.5), (x1, top + bottom, z0), tip, 'head')
        w = x1 - x0
        if w > 0.9:
            v4.carve(lambda X, Y, Z: True, (x0 - 0.01, top + bottom - 0.5, z0 - 0.6), (x0 + w * 0.3, top + bottom + 0.01, z0 + 0.1))
    # side locks in front of the ears, framing the face
    for x, z, bottom, w in side_locks:
        sx = np.sign(x)
        v4.box((x - w / 2, top + 0.5, z - 0.7), (x + w / 2, top + bottom, z + 0.7), hair, 'head')
        v4.carve(lambda X, Y, Z: True, (x - w / 2 - 0.01, top + bottom - 0.5, z - 0.8), (x - w / 2 + w * 0.4, top + bottom + 0.01, z + 0.8))
    # chunky blocks on the crown, as the sheets stack them
    rng = np.random.default_rng(int(abs(top) * 100) + 5)
    for _ in range(14):
        x = rng.uniform(-half - ex + 0.6, half + ex - 0.6)
        z = rng.uniform(-half + 0.2, half + eb - 0.6)
        w, d, hgt = rng.uniform(1.0, 2.0), rng.uniform(1.0, 2.0), rng.uniform(0.25, 0.75)
        v4.box((x - w / 2, top - et - hgt, z - d / 2), (x + w / 2, top - et + 0.25, z + d / 2), hair if rng.random() < 0.6 else hair2, 'head')
    if ears:
        ec, ring = ears
        for sx in (-1, 1):
            base = np.array([sx * (half + ex), top + 4.6, 0.4])
            v4.box(base + (sx * 0.0 - 0.4, -0.6, -0.6), base + (sx * 0.0 + 0.4, 0.9, 0.6), ec, 'head')
            v4.box((base[0] + sx * 0.4 - 0.4, base[1] - 1.3, 0.0), (base[0] + sx * 0.4 + 0.4, base[1] - 0.4, 0.8), ec, 'head')
            if ring:
                v4.box((base[0] - 0.3, base[1] + 0.9, -0.1), (base[0] + 0.3, base[1] + 1.5, 0.5), ring, 'head')
    return chin


def finish_all(f, *vols):
    """Mesh every volume (vol, texels per voxel) into the Fig."""
    for vol, tex in vols:
        vol.surfs(f, tex=tex)
    return f


# ===================================================================================================== 01 炬珀
def kokuhaku_face_rows():
    """The front of her head, from the sheet's 顔 正面 close-up: the forehead in the fringe's shadow and then bare
    between the strands, thin pale brows, wide-set eyes under long flat black lashes (standing off the face) whose
    outer ends drop, square irises: a navy top row, blue with a pale glint down the middle, gold along the bottom,
    white at either side; a tiny pale ⌒ mouth; the jaw a little shaded."""
    g = Grid('S')
    g.fill(0, 0, 31, 10, 't')
    g.fill(0, 11, 31, 12, 's')
    g.fill(0, 13, 0, 31, 's')
    g.fill(31, 13, 31, 31, 's')
    g.fill(0, 31, 31, 31, 's')
    g.mirror_row(14, 6, 'rrrr')
    # one eye, columns 3..10 (mirrored for the other): lashes, then a navy-topped blue iris with a pale glint
    # down the middle and gold at the bottom, white at either side
    eye = ['.LLLLLLL',
           'LLLLLLLL',
           'LlwNNNNw',
           'l.wBWbBw',
           '..wBWbBw',
           '..wBbBBw',
           '..sBGGBs',
           '...gGGg.']
    for k, line in enumerate(eye):
        g.mirror_row(16 + k, 3, line)
    g.row(27, 15, 'mm')
    return g.rows


@recipe('01_')
def kokuhaku():
    """剣神 炬珀 (voxel, from the sheet): white hair in a great mass to her knees, flowing out to her left, grey dragon
    horns swept back with navy-and-gold tassels; a white kimono with a navy-edged crossed collar, a navy obi with a
    row of gold studs, a gold ornament and navy tassels; a long white haori open at the front, navy stripes down its
    edges and a hem of navy and gold blocks; huge hanging sleeves with navy cuffs and a navy armband; navy hakama;
    white leg wraps; navy boots with a gold strap and white toes; a thick white tail with grey spines curling to
    the ground at her left."""
    WHITE, WHITE2, WHITE3, NAVY, NAVY2, GOLD, GOLD2 = '#f3f2f8', '#e1e0ec', '#cfcfe0', '#2c345c', '#1f2546', '#dcb763', '#a98a4c'
    HAIR, HAIR2, HAIR3, HORN, HORN2, HORN3, SKIN = '#f2f1f8', '#dddce9', '#c4c4d8', '#a3a5b8', '#c9cad8', '#7d8096', '#f3ebee'
    f = Fig('kokuhaku', td=4)
    top, chin = -12.0, -4.0
    humanoid_bones(f, head_neck=-3.6, shoulder=(-3.4, -2.4, 0), elbow=(-4.2, 1.6, 0.2), hip=(-1.4, 6.0, 0), knee=(-1.6, 14.0, -0.2),
                   waist=1.6, hipc=3.4)
    v = Vol(lo=(-16, -20, -14), hi=(18, 24.5, 18), res=2)
    rng = np.random.default_rng(7)
    hair = v.tones(HAIR, 0.03, seed=1)
    hair2 = v.tones(HAIR2, 0.035, seed=2)
    white = v.tones(WHITE, 0.025, seed=3)
    navy = v.tones(NAVY, 0.05, seed=4)
    # ---------------------------------------------------------------- head (quarter-pixel voxels)
    v4 = Vol(lo=(-7, -17, -7), hi=(7, -1, 7), res=4)
    h4 = v4.tones(HAIR, 0.03, seed=21)
    h4b = v4.tones(HAIR2, 0.03, seed=22)
    keys = dict(S='#f6f1f5', s='#e6dee6', t='#d3c8d3', L='#1f1e29', l='#3c3946', N='#243058', B='#33589c', b='#7fa2d6',
                G='#e3c27e', g='#c7a165', W='#eef3fb', w='#f1edf3', m='#a99fab', r='#bdb3c0')
    sheet_head(f, v4, top, keys, kokuhaku_face_rows(), h4, h4b, keys['S'],
               fringe=[(-4.45, -3.45, 7.6, 1), (-3.45, -2.1, 3.0, 0), (-2.1, -0.8, 3.4, 1), (-0.75, 0.75, 5.8, 1), (0.8, 2.1, 3.2, 0),
                       (2.1, 3.45, 2.8, 1), (3.45, 4.45, 7.2, 0)], tip='#c8c8da',
               side_locks=[(-4.75, -3.0, 10.4, 1.0), (4.75, -3.0, 10.0, 1.0), (-4.85, -1.6, 9.0, 1.0), (4.85, -1.6, 9.4, 1.0)],
               crown=(0.9, 1.0, 1.1), ears=('#f2e6e8', GOLD))
    # strands standing up and out round the crown, as on the sheet
    for x, y, z, dx, dy, dz in ((-4.6, top + 1.0, -1.6, -0.8, -1.2, 0), (4.6, top + 1.2, -1.0, 0.9, -1.4, 0), (-2.6, top - 0.8, -1.8, -0.4, -1.2, 0.4),
                                (2.0, top - 0.9, -2.0, 0.4, -1.1, 0.2), (0.0, top - 1.0, 0.0, 0.2, -1.0, 0.6), (-3.6, top - 0.6, 2.4, -0.6, -1.2, 0.6),
                                (3.4, top - 0.6, 2.2, 0.6, -1.2, 0.8), (-5.4, top + 3.4, 1.0, -0.9, -0.6, 0.4), (5.4, top + 3.8, 1.2, 1.0, -0.6, 0.4)):
        v.strand([(x, y, z), (x + dx, y + dy, z + dz)], [1.4, 0.6], [1.2, 0.6], hair, 'head')
    # side hair: in front of her right shoulder to the chest; on her left a great lock flowing out to the hip
    for z, L in ((-2.6, 10.5), (-1.2, 12.5), (0.4, 14.0)):
        v.strand([(-4.6, top + 3.0, z), (-5.2, top + 3.0 + L * 0.5, z - 0.2), (-5.0, top + 3.0 + L, z)], [1.6, 1.8, 0.8], [1.2, 1.2, 0.8], hair, 'head')
    for z, L, out in ((-2.4, 13.0, 1.5), (-0.8, 17.0, 3.0), (0.8, 21.0, 4.6), (2.4, 23.0, 5.4)):
        pts = [(4.6, top + 3.0, z), (5.4 + out * 0.3, top + 3.0 + L * 0.35, z + 0.4), (5.8 + out * 0.8, top + 3.0 + L * 0.7, z + 0.8),
               (5.6 + out, top + 3.0 + L, z + 1.0)]
        v.strand(pts, [1.8, 2.2, 2.0, 0.8], [1.3, 1.4, 1.2, 0.8], hair if z < 0 else hair2, 'head' if L < 15 else 'torso')
    # the long fall down her back, to the knees, in strands of slightly different length
    for k, x in enumerate(np.linspace(-4.6, 4.6, 10)):
        L = 27.0 - abs(x) * 0.8 - rng.uniform(0, 2.5)
        z0 = 4.2 + (0.6 if k % 2 else 0.0)
        v.strand([(x, top + 3.0, z0), (x * 1.1, top + 3.0 + L * 0.5, z0 + 1.2), (x * 1.15, top + 3.0 + L, z0 + 1.8)],
                 [1.6, 1.8, 1.0], [1.4, 1.4, 0.9], hair if k % 2 else hair2, 'torso')
    # horns: from the top of the head, up and sweeping back, ridged; a gold clasp and a navy tassel with gold caps
    for sx in (-1, 1):
        r0 = np.array([sx * 2.4, top + 0.2, 0.6])
        pts = [r0, r0 + (sx * 0.7, -2.4, 0.6), r0 + (sx * 1.3, -4.4, 2.2), r0 + (sx * 1.5, -5.4, 4.4), r0 + (sx * 1.4, -5.6, 6.0)]
        ridge = lambda X, Y, Z: np.where((np.floor(Y * 2 + Z * 2) % 3) == 0, v.ci(HORN3), v.ci(HORN)).astype(np.uint16)
        v.chain(pts, [1.0, 0.85, 0.65, 0.4, 0.12], ridge, 'head')
        v.paint(lambda X, Y, Z, z0=r0[2]: (Z > z0 + 3.0) & (Y < top - 3.0) & (np.abs(X) > 2.0), HORN2, only=[HORN, HORN3])
        base = r0 + (sx * 1.4, 1.2, -0.8)
        v.box(base - (0.5, 0.5, 0.5), base + (0.5, 0.5, 0.5), GOLD, 'head')
        v.strand([base + (0, 0.5, 0), base + (sx * 0.2, 3.4, 0)], 0.6, 0.6, NAVY, 'head')
        v.box(base + (sx * 0.2 - 0.5, 3.2, -0.5), base + (sx * 0.2 + 0.5, 4.2, 0.5), GOLD, 'head')
        v.strand([base + (sx * 0.2, 4.2, 0), base + (sx * 0.2, 7.0, 0)], 0.9, 0.9, NAVY, 'head')
        v.box(base + (sx * 0.2 - 0.5, 7.0, -0.5), base + (sx * 0.2 + 0.5, 7.6, 0.5), GOLD, 'head')
    # ---------------------------------------------------------------- body
    v.box((-1.0, chin - 0.2, -1.0), (1.0, chin + 0.9, 1.0), SKIN, 'torso')
    # white kimono top with a crossed collar: white with a navy edge
    v.box((-3.2, -3.0, -2.1), (3.2, 1.0, 2.1), white, 'torso')
    v.paint(lambda X, Y, Z: (Z < -1.5) & (np.abs(np.abs(X) - (Y + 3.0) * 0.5) < 0.35) & (Y < 1.0), NAVY)
    v.paint(lambda X, Y, Z: (Z < -1.5) & (np.abs(np.abs(X) - (Y + 3.0) * 0.5 - 0.7) < 0.35) & (Y < 1.0), WHITE3)
    # obi: navy, a row of gold studs, a gold ornament with a navy centre, navy cords
    v.box((-3.5, 0.6, -2.5), (3.5, 3.4, 2.5), navy, 'torso')
    v.paint(lambda X, Y, Z: (Y > 1.6) & (Y < 2.2) & ((np.floor(X * 2 + Z * 2) % 3) == 0), GOLD)
    v.box((-1.0, 1.0, -3.0), (1.0, 3.0, -2.4), GOLD, 'torso')
    v.box((-0.45, 1.5, -3.2), (0.45, 2.5, -2.9), NAVY2, 'torso')
    for dx in (-1.4, 1.4):
        v.box((dx - 0.3, 1.7, -2.9), (dx + 0.3, 2.3, -2.5), GOLD, 'torso')
    # hakama, navy, pleated, under everything to just above the ankle
    v.cone((0, 3.0, 0), (0, 19.0, 0.2), 3.3, 5.0, navy, 'hips', depth=0.8, folds=8, fold_amp=0.3)
    # the white kimono front panel below the obi with navy edges; the navy strap with gold plates over it
    v.plate([(-2.0, 3.2, -3.0), (2.0, 3.2, -3.0), (2.4, 18.8, -4.3), (-2.4, 18.8, -4.3)], 0.8, white, 'hips')
    v.paint(lambda X, Y, Z: (np.abs(X) > 1.75 + (Y - 3.2) * 0.025) & (Y > 3.2) & (Y < 19.0) & (Z < -2.4), NAVY)
    v.strand([(0.0, 3.0, -3.7), (0.0, 12.5, -4.3)], 1.0, 0.5, NAVY, 'hips')
    for y in (5.0, 8.0, 11.4):
        v.box((-0.6, y - 0.5, -4.6), (0.6, y + 0.5, -4.0), GOLD, 'hips')
    # navy tassels with gold caps from the obi
    for sx in (-1, 1):
        v.strand([(sx * 2.6, 3.2, -3.4), (sx * 2.6, 7.0, -3.7)], 0.6, 0.6, NAVY, 'hips')
        v.box((sx * 2.6 - 0.5, 6.8, -4.2), (sx * 2.6 + 0.5, 7.8, -3.2), GOLD, 'hips')
        v.strand([(sx * 2.6, 7.8, -3.7), (sx * 2.6, 10.6, -3.8)], 0.9, 0.9, NAVY, 'hips')
    # haori: a long open coat from the shoulders to the shin, folds; navy stripes down its front edges and two more
    # on each side, a hem band of navy and gold blocks, a ragged lower edge
    v.cone((0, -2.8, 0.2), (0, 19.2, 0.8), 3.9, 6.4, white, 'torso', depth=0.8, folds=10, fold_amp=0.4, thick=0.9,
           open_front=0.9, start=0.0)

    def stripe(a0, w):
        def f_(X, Y, Z):
            ang = np.arctan2(X, -(Z - 0.5))
            return (np.abs(np.abs(ang) - a0) < w) & (Y > -1.6)
        return f_
    v.paint(stripe(0.50, 0.08), NAVY)
    v.paint(stripe(1.75, 0.06), NAVY)
    hem = lambda X, Y, Z: np.where((np.floor(X * 2 + Z * 2) % 5) == 0, v.ci(GOLD),
                                   np.where((np.floor(X * 2 + Z * 2) % 5) == 2, v.ci(WHITE), v.ci(NAVY))).astype(np.uint16)
    v.paint(lambda X, Y, Z: (Y > 17.6) & (Y < 19.3), hem)
    for k in range(22):
        a = -math.pi + k * (2 * math.pi / 22) + 0.07
        if abs(a) < 0.5:
            continue
        L = rng.uniform(0.0, 1.8)
        x, z = math.sin(a) * 6.2, 0.8 - math.cos(a) * 6.2 * 0.8
        v.box((x - 0.6, 19.0, z - 0.4), (x + 0.6, 19.0 + L, z + 0.4), NAVY if k % 3 == 0 else (GOLD if k % 5 == 0 else WHITE), 'torso')
    # gold crests on the haori fronts and back
    kamon = ['.ggg.', 'gnnng', 'gngng', 'gnnng', '.ggg.']
    for sx in (-1, 1):
        v.decal(kamon, (sx * 4.4, 14.6, -5.6), (1, 0, 0), (0, 1, 0), 0.5, (0, 0, -1), depth=3.0, keys={'g': GOLD, 'n': NAVY})
        v.decal(kamon, (sx * 3.0, 6.0, -4.4), (1, 0, 0), (0, 1, 0), 0.4, (0, 0, -1), depth=3.0, keys={'g': GOLD, 'n': NAVY})
    v.decal(kamon, (0, 2.0, 5.0), (-1, 0, 0), (0, 1, 0), 0.6, (0, 0, 1), depth=3.0, keys={'g': GOLD, 'n': NAVY})
    # ---------------------------------------------------------------- arms and the great sleeves
    for side, sx in (('r', -1), ('l', 1)):
        sh = np.array([sx * 3.6, -2.4, 0.0])
        el = np.array([sx * 4.4, 1.6, 0.2])
        ha = np.array([sx * 4.8, 5.4, -0.6])
        v.capsule(sh, el, 1.25, 1.15, white, f'arm_{side}')
        v.capsule(el, ha, 1.15, 1.05, white, f'fore_{side}')
        v.box(ha + (-0.7, 0.5, -0.7), ha + (0.7, 2.0, 0.7), SKIN, f'fore_{side}')
        # the sleeve: flares from the shoulder like a trumpet and hangs open below the hand to the hip; a navy cuff
        # with a gold line above it
        v.cone((sx * 4.0, -2.0, 0.0), (sx * 5.0, 9.6, 0.4), 1.6, 3.0, white, f'arm_{side}', depth=0.95, folds=5, fold_amp=0.2, thick=0.7)
        v.paint(lambda X, Y, Z, s_=sx: (X * s_ > 2.4) & (Y > 8.2) & (Y < 9.7), NAVY)
        v.paint(lambda X, Y, Z, s_=sx: (X * s_ > 2.4) & (Y > 7.7) & (Y < 8.2), GOLD)
        # navy armband with a gold plate high on the sleeve
        v.cone((sx * 4.1, -0.4, 0.0), (sx * 4.2, 0.6, 0.0), 1.95, 2.05, navy, f'arm_{side}', depth=0.95)
        v.box((sx * 6.1 - 0.4, -0.6, -0.6), (sx * 6.1 + 0.4, 0.8, 0.6), GOLD, f'arm_{side}')
        # a navy tassel from the sleeve
        v.strand([(sx * 6.4, 9.4, -1.4), (sx * 6.4, 11.8, -1.4)], 0.6, 0.6, NAVY, f'arm_{side}')
        v.box((sx * 6.4 - 0.45, 11.6, -1.85), (sx * 6.4 + 0.45, 12.4, -0.95), GOLD, f'arm_{side}')
    # ---------------------------------------------------------------- legs and boots
    for side, sx in (('r', -1), ('l', 1)):
        fx = sx * 2.5
        v.capsule((sx * 1.5, 6.4, 0), (sx * 1.9, 14.0, -0.2), 1.3, 1.2, navy, f'leg_{side}')
        v.capsule((sx * 1.9, 14.0, -0.2), (fx, 20.4, -0.3), 1.2, 1.1, v.tones('#eeedf4', 0.05, seed=11), f'shin_{side}')
        v.paint(lambda X, Y, Z, x_=fx: (np.abs(X - x_) < 1.6) & (((np.floor(Y * 2)) % 4) == 0) & (Y > 18.0) & (Y < 20.5), WHITE3)
        v.box((fx - 1.3, 20.2, -1.6), (fx + 1.3, 22.6, 1.2), navy, f'shin_{side}')
        v.box((fx - 1.35, 20.7, -1.7), (fx + 1.35, 21.3, 1.3), GOLD, f'shin_{side}')
        v.box((fx - 0.5, 20.6, -1.9), (fx + 0.5, 21.4, -1.6), WHITE, f'shin_{side}')
        v.box((fx - 1.4, 21.8, -2.8), (fx + 1.4, 23.2, 0.4), white, f'shin_{side}')
        v.box((fx - 1.5, 23.1, -2.9), (fx + 1.5, 24.0, 1.4), navy, f'shin_{side}')
    # ---------------------------------------------------------------- tail
    # a chain of bones, one per segment, so it sways along its length (RigModel's tail tag, i = segment index)
    pts = [(1.4, 3.6, 2.6), (3.6, 5.4, 4.6), (6.2, 8.6, 5.4), (8.2, 12.6, 4.8), (9.0, 16.8, 3.2), (8.6, 20.6, 1.4), (7.0, 22.8, -0.6),
           (4.8, 23.4, -1.8), (2.8, 23.5, -2.0)]
    rad = [1.9, 1.95, 1.9, 1.8, 1.65, 1.45, 1.1, 0.7, 0.3]
    scale = lambda X, Y, Z: np.where(((np.floor(Y * 2) + np.floor((X + Z) * 2)) % 3) == 0, v.ci(WHITE2),
                                     np.where(((np.floor(Y * 2) + np.floor((X - Z) * 2)) % 5) == 0, v.ci(WHITE3), v.ci('#f5f4fa'))).astype(np.uint16)
    parent = 'hips'
    for i in range(len(pts) - 1):
        bn = f.bone(f'tail{i}', parent, tuple(pts[i]), anim='tail', amp=0.07, speed=0.06, i=float(i))
        parent = bn
        a_, b_ = np.array(pts[i]), np.array(pts[i + 1])
        v.capsule(a_, b_, rad[i], rad[i + 1], scale, bn.name)
        if 0 < i < len(pts) - 2:
            for j in (0.2, 0.6):
                m = a_ + (b_ - a_) * j
                out = np.array([0.55, -0.6, 0.6])
                out /= np.linalg.norm(out)
                v.capsule(m + out * rad[i] * 0.7, m + out * (rad[i] + 1.6) + (b_ - a_) * 0.1, 0.6, 0.12, '#7d839c', bn.name)
    return finish_all(f, (v, 2), (v4, 1))

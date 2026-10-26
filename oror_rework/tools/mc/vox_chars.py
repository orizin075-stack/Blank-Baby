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


# ===================================================================================================== 01 炬珀
@recipe('01_')
def kokuhaku():
    """剣神 炬珀 (voxel): white hair to the knees, grey dragon horns, big blue-and-gold eyes; white kimono, navy obi with
    gold, white haori bordered in navy over navy hakama, wide sleeves, white leg wraps, navy platform boots, a
    white scaled tail with grey spines."""
    WHITE, WHITE2, NAVY, NAVY2, GOLD = '#f2f1f7', '#dcdce8', '#2e365e', '#222849', '#d8b25a'
    HAIR, HAIR2, HAIR3, HORN, HORN2, SKIN = '#f6f5fb', '#d9dcec', '#b7bcd4', '#9b9eb2', '#dfe0ea', '#f9ece8'
    f = Fig('kokuhaku', td=4)
    # proportions: head 8 px (top -12, chin -4), shoulders -2.4, waist 2.0, crotch 6.6, ground 24
    top, chin = -12.0, -4.0
    humanoid_bones(f, head_neck=-3.4, shoulder=(-3.5, -2.2, 0), elbow=(-4.3, 2.0, 0.2), hip=(-1.4, 6.4, 0), knee=(-1.5, 15.0, -0.2),
                   waist=2.0, hipc=3.4)
    v = Vol(lo=(-14, -20, -12), hi=(14, 24.5, 18), res=2)
    rng = np.random.default_rng(7)
    hair = v.tones(HAIR, 0.035, seed=1)
    hair_sh = v.tones(HAIR2, 0.03, seed=2)
    white = v.tones(WHITE, 0.025, seed=3)
    navy = v.tones(NAVY, 0.05, seed=4)
    # ---- head: skull, the face drawn on its front; hair cap, fringe, side locks, back fall
    v.box((-3.9, top + 0.1, -3.9), (3.9, chin, 3.9), SKIN, 'head')
    spec = dict(skin=SKIN, hair=HAIR, hair_dark=HAIR3, iris='#3a64cc', iris_dark='#1c2552', iris_light='#7fb0ff', accent='#f0c45a',
                lash='#1c2040', eye='round', mouth='small', fringe='straight', fringe_depth=15, blush=True, blush_colour='#f6c4c8')
    face_img, _ = sface.face(spec)
    v.overlay('head', 'north', (-4.0, top, 4.0, chin), face_img)
    # hair cap: rounded over the crown, sides and back, open over the face
    v.ellipsoid((0, top + 3.4, 0.6), (5.0, 4.0, 5.0), hair, 'head', cut=lambda X, Y, Z: ~((Z < -2.5) & (Y > top + 2.4) & (np.abs(X) < 3.6)))
    v.ellipsoid((0, top + 6.0, 1.2), (4.7, 4.0, 4.6), hair, 'head', cut=lambda X, Y, Z: ~((Z < -2.0) & (Y > top + 2.0) & (np.abs(X) < 3.7)))
    # a few fringe strands standing off the forehead (the rest of the fringe is drawn on the face)
    for x, L in ((-3.4, 5.6), (-2.2, 3.2), (-0.4, 3.8), (1.4, 2.8), (3.3, 5.2)):
        v.strand([(x, top + 0.6, -4.15), (x + rng.uniform(-0.2, 0.2), top + 0.6 + L, -4.3)], [1.2, 0.5], [0.6, 0.5], hair, 'head')
    # tufts standing out round the crown
    for x, y, z in ((-4.6, top + 1.5, -1.0), (4.6, top + 1.8, 0.0), (-3.0, top - 0.6, 0.0), (2.6, top - 0.5, -1.0), (0.2, top - 0.8, 1.5),
                    (-4.9, top + 4.5, 2.0), (5.0, top + 4.8, 1.6), (3.8, top + 0.2, 2.6), (-3.6, top + 0.4, 3.0)):
        v.strand([(x, y + 1.2, z), (x * 1.08, y - 0.9, z + 0.4)], [1.4, 0.5], [1.2, 0.5], hair, 'head')
    # side locks framing the face, then the fall down both sides and the back
    for sx in (-1, 1):
        roots = [(sx * 4.2, top + 3.0, -2.9), (sx * 4.7, top + 3.0, 1.4), (sx * 4.6, top + 3.2, 2.8)]
        hair_strands(v, rng, roots, [9.0, 15.0, 18.0] if sx < 0 else [11.0, 18.0, 21.0], hair, 'head', w=(1.0, 1.4), d=(0.8, 1.1),
                     out=[(sx * 0.1, 0, -0.1), (sx * 0.5, 0, 0.6), (sx * 0.5, 0, 0.8)])
    back_roots = [(x, top + 3.5, 4.4 + abs(x) * 0.1) for x in np.linspace(-4.2, 4.2, 9)]
    hair_strands(v, rng, back_roots, 25.0, hair, 'torso', w=(1.2, 1.8), d=(0.9, 1.3), out=[(x * 0.08, 0, 0.5) for x in np.linspace(-4.2, 4.2, 9)])
    back_roots2 = [(x, top + 4.5, 5.2) for x in np.linspace(-3.6, 3.6, 7)]
    hair_strands(v, rng, back_roots2, 21.0, hair_sh, 'torso', w=(1.0, 1.6), d=(0.8, 1.0), out=[(x * 0.1, 0, 0.6) for x in np.linspace(-3.6, 3.6, 7)])
    # horns: up from the crown and sweeping back, grey with pale tips
    for sx in (-1, 1):
        r0 = np.array([sx * 2.5, top + 0.4, 0.8])
        pts = [r0, r0 + (sx * 0.8, -2.2, 0.8), r0 + (sx * 1.4, -4.0, 2.6), r0 + (sx * 1.6, -5.0, 4.8)]
        v.chain(pts, [0.95, 0.8, 0.55, 0.15], v.tones(HORN, 0.06, seed=5), 'head')
        v.paint(lambda X, Y, Z, z0=r0[2]: (Z > z0 + 2.4) & (Y < top - 2.0) & (np.abs(X) > 2.0), HORN2)
        # gold clasp and a navy tassel at the root
        v.box(r0 + (sx * 0.6 - 0.5, 0.4, -1.0), r0 + (sx * 0.6 + 0.5, 1.4, 0.0), GOLD, 'head')
        v.strand([r0 + (sx * 1.2, 1.4, -0.6), r0 + (sx * 1.3, 4.6, -0.6)], 0.6, 0.6, NAVY, 'head')
        v.box(r0 + (sx * 1.3 - 0.45, 4.4, -1.05), r0 + (sx * 1.3 + 0.45, 5.4, -0.15), GOLD, 'head')
        v.strand([r0 + (sx * 1.3, 5.4, -0.6), r0 + (sx * 1.3, 7.4, -0.6)], 0.8, 0.8, NAVY, 'head')
    # ---- body: neck, white kimono with a crossed navy collar
    v.box((-1.0, chin - 0.2, -1.0), (1.0, chin + 1.0, 1.0), SKIN, 'torso')
    v.box((-3.2, -3.0, -2.0), (3.2, 1.2, 2.0), white, 'torso')
    v.paint(lambda X, Y, Z: (Z < -1.4) & (np.abs(np.abs(X) - (Y + 3.0) * 0.45) < 0.45) & (Y < 1.2), NAVY)
    # obi: navy with a band of gold studs, a gold knot
    v.box((-3.5, 0.8, -2.4), (3.5, 3.2, 2.4), navy, 'torso')
    v.paint(lambda X, Y, Z: (Y > 1.7) & (Y < 2.3) & ((np.floor(X * 2 + Z * 2) % 3) == 0), GOLD)
    v.box((-0.9, 1.1, -3.0), (0.9, 2.9, -2.3), GOLD, 'torso')
    v.box((-0.4, 1.6, -3.3), (0.4, 2.4, -2.9), NAVY2, 'torso')
    v.strand([(0.4, 2.9, -2.8), (0.4, 9.5, -3.4)], 0.9, 0.5, NAVY, 'hips')
    for y in (4.5, 7.0):
        v.box((-0.1, y - 0.4, -3.6), (0.9, y + 0.4, -3.1), GOLD, 'hips')
    # hakama: navy, pleated, to mid-shin, gold crests
    v.cone((0, 3.0, 0), (0, 18.6, 0.3), 3.3, 4.9, navy, 'hips', depth=0.78, folds=7, fold_amp=0.35)
    crest = ['..g..', '.gng.', 'gnnng', '.gng.', '..g..']
    for cx, cy in ((-2.2, 13.8), (2.4, 15.4), (0.2, 11.0)):
        v.decal(crest, (cx, cy, -4.0), (1, 0, 0), (0, 1, 0), 0.5, (0, 0, -1), depth=3.0, keys={'g': GOLD, 'n': NAVY2})
    # haori: an open shell from the shoulders to the knee, folds, navy borders on the opening and hem, jagged hem
    v.cone((0, -2.6, 0.2), (0, 15.6, 0.6), 4.0, 6.6, white, 'torso', depth=0.82, folds=9, fold_amp=0.45, thick=0.9,
           open_front=0.62, start=0.0)
    def opening(X, Y, Z):
        ang = np.arctan2(X, -(Z - 0.4))
        return (np.abs(np.abs(ang) - 0.38) < 0.09) & (Y > -1.0)
    v.paint(opening, NAVY)
    v.paint(lambda X, Y, Z: (Y > 14.4) & (Y < 15.7), lambda X, Y, Z: np.where((np.floor(X * 2) % 4) == 0, v.ci(GOLD),
                                                                                np.where((np.floor(X * 2) % 4) == 2, v.ci(WHITE), v.ci(NAVY))).astype(np.uint16))
    # ragged hem: strips of different lengths
    for k in range(18):
        a = -math.pi + k * (2 * math.pi / 18) + 0.1
        if abs(a) < 0.6:
            continue
        L = rng.uniform(0.0, 2.2)
        x, z = math.sin(a) * 6.4, 0.6 - math.cos(a) * 6.4 * 0.82
        v.box((x - 0.7, 15.4, z - 0.45), (x + 0.7, 15.4 + L, z + 0.45), NAVY if k % 3 == 0 else WHITE, 'torso')
    # golden crests on the haori: at the hem front and on the back
    kamon = ['.ggg.', 'gnnng', 'gngng', 'gnnng', '.ggg.']
    for sx in (-1, 1):
        v.decal(kamon, (sx * 4.2, 12.0, -5.0), (1, 0, 0), (0, 1, 0), 0.5, (0, 0, -1), depth=3.0, keys={'g': GOLD, 'n': NAVY})
    v.decal(kamon, (0, 0.5, 4.5), (-1, 0, 0), (0, 1, 0), 0.6, (0, 0, 1), depth=3.0, keys={'g': GOLD, 'n': NAVY})
    # tassels from the obi
    for sx in (-1, 1):
        v.strand([(sx * 3.0, 3.0, -3.6), (sx * 3.0, 7.0, -3.8)], 0.6, 0.6, NAVY, 'hips')
        v.box((sx * 3.0 - 0.5, 6.6, -4.3), (sx * 3.0 + 0.5, 7.6, -3.3), GOLD, 'hips')
        v.strand([(sx * 3.0, 7.6, -3.8), (sx * 3.0, 9.8, -3.8)], 0.9, 0.9, v.tones(WHITE2, 0.04, seed=9), 'hips')
    # ---- arms: white, wide hanging sleeves with a navy armband and a navy cuff
    for side, sx in (('r', -1), ('l', 1)):
        sh = np.array([sx * 3.6, -2.2, 0.0])
        el = np.array([sx * 4.4, 2.0, 0.2])
        ha = np.array([sx * 4.9, 5.8, -0.6])
        v.capsule(sh, el, 1.25, 1.15, white, f'arm_{side}')
        v.capsule(el, ha, 1.15, 1.05, white, f'fore_{side}')
        v.box(ha + (-0.7, 0.4, -0.7), ha + (0.7, 1.9, 0.7), SKIN, f'fore_{side}')
        # the sleeve: a deep box hanging from the forearm, widening, a navy cuff at its lower edge
        v.strand([el + (sx * 0.4, -0.6, 0.3), ha + (sx * 0.5, 4.2, 0.6)], [4.0, 5.2], [3.6, 4.4], white, f'fore_{side}', up=(0, 0, -1))
        v.paint(lambda X, Y, Z, s_=sx, hy=ha[1]: (X * s_ > 3.0) & (Y > hy + 2.6) & (Y < hy + 3.8), NAVY)
        v.capsule(sh + (0, 1.6, 0), sh + (sx * 0.4, 2.4, 0), 1.45, 1.45, navy, f'arm_{side}')
        v.box(sh + (sx * 1.3 - 0.3, 1.5, -0.5), sh + (sx * 1.3 + 0.3, 2.5, 0.5), GOLD, f'arm_{side}')
    # ---- legs: white wraps, navy platform boots with white toes and gold bands
    for side, sx in (('r', -1), ('l', 1)):
        fx = sx * 2.4
        v.capsule((sx * 1.5, 6.6, 0), (sx * 1.9, 15.0, -0.2), 1.3, 1.2, navy, f'leg_{side}')
        v.capsule((sx * 1.9, 15.0, -0.2), (fx, 20.6, -0.3), 1.2, 1.1, v.tones('#ecebf3', 0.04, seed=11), f'shin_{side}')
        v.box((fx - 1.3, 20.2, -1.7), (fx + 1.3, 22.4, 1.2), navy, f'shin_{side}')
        v.box((fx - 1.35, 20.6, -1.8), (fx + 1.35, 21.2, 1.3), GOLD, f'shin_{side}')
        v.box((fx - 1.4, 21.6, -2.6), (fx + 1.4, 23.2, 1.4), white, f'shin_{side}')
        v.box((fx - 1.5, 23.0, -2.7), (fx + 1.5, 24.0, 1.5), navy, f'shin_{side}')
    # ---- tail: white with a pale-grey scale pattern and grey spines, from the small of the back to the ground
    t = f.bone('tail', 'hips', (0.5, 4.0, 2.4), anim='tail', amp=0.06, speed=0.05)
    pts = [(0.5, 4.0, 2.4), (1.4, 5.8, 5.0), (3.0, 9.6, 7.2), (4.8, 14.2, 8.4), (6.0, 18.8, 7.8), (5.8, 22.0, 5.4), (4.2, 23.0, 3.0),
           (2.4, 23.4, 1.6)]
    rad = [1.7, 1.7, 1.6, 1.5, 1.35, 1.1, 0.75, 0.35]
    scale = lambda X, Y, Z: np.where(((np.floor(Y * 2) + np.floor((X + Z) * 2)) % 3) == 0, v.ci(WHITE2), v.ci('#f4f3f9')).astype(np.uint16)
    v.chain(pts, rad, scale, 'tail')
    for i in range(1, len(pts) - 2):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        for j in (0.25, 0.75):
            m = a + (b - a) * j
            up = np.array([0, -1.0, 0.45])
            up /= np.linalg.norm(up)
            v.capsule(m + up * rad[i] * 0.8, m + up * (rad[i] + 1.3) + (b - a) * 0.08, 0.45, 0.1, '#7f8298', 'tail')
    return finish(f, v)

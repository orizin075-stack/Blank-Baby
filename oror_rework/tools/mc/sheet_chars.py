"""The 37 characters of the user's design sheets (oror_rework/designs/sheets), modelled by hand with the sheets as
the reference: their proportions, silhouettes, colours and ornaments, built from cubes (designfig, dhum) and painted
as pixel art (vox). Each recipe returns its Fig; RECIPES maps the rig key to (sheet prefix, recipe)."""
import math
import numpy as np
from rig import rot_zyx
from designfig import Fig
from dhum import Hum, HS
from vox import V

RECIPES = {}


def recipe(sheet):
    def deco(fn):
        RECIPES[fn.__name__] = (sheet, fn)
        return fn
    return deco


def plate4(f, bone, p0, p1, p2, p3, thick, name='plate', mat=None):
    """A slab through four corners (in order round its edge), `thick` along its normal."""
    P = np.array([p0, p1, p2, p3], float)
    n = np.cross(P[1] - P[0], P[3] - P[0])
    n = n / max(1e-9, np.linalg.norm(n)) * thick / 2
    return f.hexa(bone, list(P - n) + list(P + n), name=name, mat=mat)


def tassel(f, bone, top, length, cord, bead, name='tassel'):
    """A short cord with a bead and a fringe, hanging from `top`."""
    t = np.asarray(top, float)
    f.box(bone, t + (0, length * 0.3, 0), (0.4, length * 0.6, 0.4), name=name, mat=cord)
    f.box(bone, t + (0, length * 0.62, 0), (0.9, 0.9, 0.9), name=name, mat=bead)
    f.box(bone, t + (0, length * 0.9, 0), (0.7, length * 0.4, 0.7), name=name, mat=cord)


# ===================================================================================================== 01 炬珀
@recipe('01_')
def kokuhaku():
    """剣神 炬珀: white hair to the knees with tufts round the crown, grey dragon horns swept back with navy and gold
    tassels, big blue eyes flecked with gold; a white kimono with a navy collar, a navy obi studded with gold and
    a golden knot with a navy strap hanging down the front; a white haori in hanging strips with navy stripes and a
    hem of navy and gold blocks; very wide sleeves with a navy armband, a navy cuff and a tassel; navy hakama with
    golden crests; white leg wraps; navy platform boots with white toes, navy straps and golden bands; a long white
    scaled tail with grey spines."""
    WHITE, NAVY, NAVY_D, GOLD, GOLD_D = '#f3f2f8', '#2e365e', '#20264a', '#d8b25a', '#a8823c'
    HAIR, HAIR_TIP, HORN, HORN_TIP, SKIN = '#f6f5fa', '#d6daee', '#9da0b3', '#e2e3ec', '#f9ece8'
    h = Hum('kokuhaku', SKIN, HAIR, dict(iris='#3a64cc', iris_dark='#1c2552', iris_light='#7fb0ff', accent='#f0c45a',
                                          lash='#1c2040', eye='round', mouth='small', fringe='straight', fringe_depth=18,
                                          hair_dark='#a8aec8', blush=False), H=36.0)
    f = h.f
    hair = h.hair_mat(tip=HAIR_TIP, block=2)
    cloth = lambda **kw: V(WHITE, var=0.035, **kw)
    navy = lambda **kw: V(NAVY, var=0.04, **kw)
    gold = lambda **kw: V(GOLD, var=0.05, **kw)
    h.head(fringe='straight', fringe_depth=18)
    # hair: tufts round the crown, locks either side of the face, a thick fall on both sides and down the back
    for x, y, z, w, hh, d in ((-4.5, h.top + 1.4, -0.6, 1.2, 2.6, 1.6), (4.6, h.top + 1.8, 0.2, 1.2, 3.0, 1.6), (-2.2, h.top - 0.4, 0.8, 1.8, 1.0, 2.2),
                              (1.4, h.top - 0.5, -0.8, 2.0, 1.2, 2.4), (3.4, h.top - 0.2, 2.2, 1.4, 0.8, 2.0), (-4.7, h.top + 4.4, 2.6, 1.0, 3.4, 2.0),
                              (4.8, h.top + 4.6, 2.2, 1.0, 3.6, 2.0), (0.0, h.top + 0.6, 4.6, 6.0, 2.0, 1.0)):
        f.box('head', (x, y, z), (w, hh, d), name='hair_tuft', mat=hair)
    h.fringe([-3.4, -2.1, 2.0, 3.3], [3.4, 4.6, 4.4, 3.4], mat=hair)
    h.long_hair(15.5, mat=hair, width=10.6, z=4.5, n=7, depth=1.6, spread=0.3, jag=3.0, layers=2)
    rng = np.random.default_rng(11)
    for sx, bottom, n in ((-1, 9.0, 3), (1, 13.5, 4)):
        for i in range(n):
            x = sx * (4.8 + 0.6 * i)
            z = -1.5 + i * 1.4
            b = bottom - rng.uniform(0, 2.4) + i * 0.6
            f.box('head', (x, (h.chin - 2.0 + b) / 2, z), (1.3, b - h.chin + 2.0, 1.5), name='hair_lock', mat=hair)
    # horns, and a tassel from each root
    for sx in (-1, 1):
        root = np.array([sx * 2.5, h.top + 0.6, 0.8])
        f.chain('head', [root, root + (sx * 0.9, -2.4, 1.0), root + (sx * 1.5, -4.4, 3.0), root + (sx * 1.7, -5.6, 5.4)],
                [1.8, 1.5, 1.0, 0.4], d=[2.0, 1.6, 1.0, 0.4], name='horn',
                mat=V(HORN, var=0.06, block=2, bands=[('z', 3.4, 9.0, HORN_TIP)]))
        f.box('head', root + (sx * 1.2, 0.6, -0.6), (1.0, 1.0, 1.0), name='horn_clasp', mat=gold())
        tassel(f, 'head', root + (sx * 1.6, 1.0, -0.4), 4.6, navy(), gold())
    # body: white kimono, crossed navy collar
    h.torso(cloth(), belly=navy(), depth=4.0)
    for sx in (-1, 1):
        plate4(f, 'torso', (sx * 0.1, h.neck + 0.2, -2.15), (sx * 1.5, h.neck + 0.2, -2.15), (sx * -0.3, h.waist_y - 0.4, -2.15),
               (sx * -1.5, h.waist_y - 0.4, -2.15), 0.25, name='collar', mat=navy())
    # obi: navy with a band of golden studs, a golden knot, a navy strap with golden plates down the front
    wy = h.waist_y - 0.5
    f.box('torso', (0, wy, 0), (7.2, 2.8, 4.6), name='obi',
          mat=navy(bands=[('y', wy - 0.35, wy + 0.35, [GOLD, NAVY_D])], edges=[('top', 1, NAVY_D), ('bottom', 1, NAVY_D)]))
    f.box('torso', (0, wy, -2.45), (1.6, 1.6, 0.6), name='obi_knot', mat=gold(motifs=[('dot', (0, wy, -2.75), 0.5, {'g': NAVY})]))
    for dx, dy in ((-1.1, 0), (1.1, 0), (0, -1.1), (0, 1.1)):
        f.box('torso', (dx * 0.9, wy + dy * 0.9, -2.5), (0.8, 0.8, 0.5), name='obi_knot', mat=gold())
    # the white kimono's front panel shows between the haori's edges, the hakama only in the gaps and below
    plate4(f, 'hips', (-1.4, wy + 1.2, -2.5), (1.4, wy + 1.2, -2.5), (1.8, 16.4, -3.0), (-1.8, 16.4, -3.0), 0.4, name='kimono_front',
           mat=cloth(edges=[('bottom', 2, NAVY)], motifs=[('kamon', (-0.9, 14.6, -3.1), 0.36, {'n': NAVY})]))
    strap = f.bone('strap', 'hips', (0.2, wy + 1.0, -2.6), anim='sway', amp=0.03, speed=0.05)
    f.box(strap, (0.2, wy + 5.0, -3.0), (1.0, 8.0, 0.4), name='strap',
          mat=navy(motifs=[('square', (0.2, wy + 3.6, -3.2), 0.33), ('square', (0.2, wy + 6.4, -3.2), 0.33)]))
    f.box(strap, (0.2, wy + 9.6, -3.0), (1.6, 1.4, 0.6), name='strap_end', mat=gold(motifs=[('dot', (0.2, wy + 9.6, -3.35), 0.45, {'g': NAVY})]))
    # hakama: navy, pleated, golden crests
    hk = navy(bands=[('x', -2.3, -2.1, NAVY_D), ('x', -0.1, 0.1, NAVY_D), ('x', 2.1, 2.3, NAVY_D)],
              motifs=[('kamon', (-2.0, 13.6, -2.85), 0.42, {'n': NAVY_D}), ('kamon', (2.2, 15.2, -3.0), 0.42, {'n': NAVY_D}),
                      ('kamon', (0.0, 11.0, -2.7), 0.42, {'n': NAVY_D})])
    h.skirt(hk, h.waist_y + 0.8, 18.2, 6.6, 8.2, 4.4, 5.6, name='hakama')
    # haori: back panel and side panels, and each front edge as hanging strips of different lengths with navy
    # stripes and a hem of navy and gold blocks
    y0 = h.sh_y - 0.6
    hem = [('bottom', 3, [NAVY, WHITE, GOLD, NAVY_D, WHITE, NAVY])]
    f.box('torso', (0, h.neck + 0.8, 1.9), (7.4, 2.0, 1.2), name='haori_collar', mat=cloth(edges=[('top', 2, NAVY)]))
    plate4(f, 'torso', (-3.8, y0, 2.4), (3.8, y0, 2.4), (5.8, 15.4, 3.8), (-5.8, 15.4, 3.8), 0.7, name='haori_back',
           mat=cloth(edges=hem, motifs=[('kamon', (0, y0 + 3.4, 2.95), 0.5, {'n': NAVY}), ('kamon', (-3.4, 12.6, 3.6), 0.5, {'n': NAVY}),
                                        ('kamon', (3.4, 12.6, 3.6), 0.5, {'n': NAVY})]))
    for sx in (-1, 1):
        plate4(f, 'torso', (sx * 3.9, y0, 2.2), (sx * 3.9, y0, -1.8), (sx * 6.0, 15.0, -2.8), (sx * 6.0, 15.0, 3.6), 0.7, name='haori_side',
               mat=cloth(edges=hem))
        inner = 'right' if sx < 0 else 'left'
        strips = ((2.3, 3.4, 14.6, True), (3.4, 4.7, 16.0, False), (4.7, 6.1, 15.2, False))
        for i, (a, b, L, stripe) in enumerate(strips):
            ta, tb = min(a, 3.9), min(b, 3.9)
            za = -2.45 - (a - 2.3) * 0.05
            pa = (sx * a, L, -3.1 - (a - 2.3) * 0.12)
            pb = (sx * b, L, -3.1 - (b - 2.3) * 0.12)
            m = cloth(edges=([('bottom', 2, [NAVY, WHITE, GOLD, WHITE, NAVY_D, WHITE])] + ([(inner, 1, NAVY)] if stripe else [])),
                      motifs=([('kamon', (sx * (a + b) / 2, L - 2.6, -3.2), 0.4, {'n': NAVY})] if i == 1 else []))
            plate4(f, 'torso', (sx * ta, y0 + 0.3, za), (sx * tb, y0 + 0.3, za), pb, pa, 0.6, name='haori_strip', mat=m)
        tassel(f, 'torso', (sx * 3.3, wy + 1.4, -3.3), 5.4, navy(), gold())
    # arms: white sleeves, very wide and long, a navy armband with a golden buckle, a navy cuff, a tassel
    h.arms(cloth(), cloth(), V(SKIN, var=0.0))
    h.sleeves(cloth(edges=[('bottom', 3, NAVY)], bands=[], motifs=[]), drop=11.0, width=5.4, depth=4.8, start=0.15)
    for side, sx in (('r', -1), ('l', 1)):
        sh, el, ha = h.arm_pts[side]
        f.box(f'fore_{side}', ha + (sx * 0.3, 2.6, -0.2), (5.6, 1.0, 5.0), name='sleeve_band', mat=navy(motifs=[]))
        f.box(f'fore_{side}', ha + (sx * 0.3, 0.2, -2.7), (1.6, 1.6, 0.3), name='sleeve_crest', mat=gold(motifs=[('dot', ha + (sx * 0.3, 0.2, -2.9), 0.5, {'g': NAVY})]))
    for side, sx in (('r', -1), ('l', 1)):
        sh, el, ha = h.arm_pts[side]
        band = sh + (el - sh) * 0.55
        f.box(f'arm_{side}', band, (3.0, 1.2, 3.0), name='armband', mat=navy(motifs=[('buckle', band + (sx * 1.5, 0, 0), 0.3)]))
        f.box(f'arm_{side}', band + (sx * 1.6, 0, 0), (0.4, 1.0, 1.0), name='buckle', mat=gold())
        tassel(f, f'fore_{side}', ha + (sx * 1.4, 2.0, 1.6), 5.0, navy(), gold())
    # legs: white wraps; boots: navy with white toes, navy straps with a white bow and golden bands
    wraps = V('#eceaf2', var=0.05, block=2, bands=[('y', 19.0, 19.3, '#c8c8d8'), ('y', 20.2, 20.5, '#c8c8d8')])
    boot = navy(bands=[('y', 20.8, 21.4, GOLD)], motifs=[('bow', (0, 20.4, -2.0), 0.3, {'w': WHITE})])
    for side, sx in (('r', -1), ('l', 1)):
        hip = np.array([sx * h.lx, h.crotch - 0.6, 0.0])
        knee = np.array([sx * (h.lx + 0.2), h.knee_y, -0.2])
        foot = np.array([sx * (h.lx + 0.4), 21.4, -0.4])
        f.chain(f'leg_{side}', [hip, knee], [2.6, 2.4], name='thigh', mat=navy())
        f.chain(f'shin_{side}', [knee, foot + (0, -2.0, 0)], [2.4, 2.3], name='wrap', mat=wraps)
        f.box(f'shin_{side}', foot + (0, -0.6, 0.1), (2.8, 3.2, 3.0), name='boot', mat=boot)
        f.box(f'shin_{side}', (foot[0], 22.6, foot[2] - 0.7), (3.4, 1.4, 4.6), name='boot_toe', mat=cloth(edges=[('top', 1, '#d8d8e4')]))
        f.box(f'shin_{side}', (foot[0], 23.6, foot[2] - 0.6), (3.6, 0.8, 4.8), name='sole', mat=navy())
    # tail: white scales, grey spines, curling down behind her to the ground
    t = f.bone('tail', 'hips', (0.6, h.hip_y + 0.4, 2.0), anim='tail', amp=0.06, speed=0.05)
    pts = [(0.6, h.hip_y + 0.4, 2.0), (1.6, h.hip_y + 2.0, 5.0), (3.4, 9.0, 7.4), (5.4, 14.0, 8.4), (6.6, 19.0, 7.6),
           (6.2, 22.4, 5.0), (4.4, 23.2, 2.6), (2.6, 23.4, 1.6)]
    wid = [3.2, 3.2, 3.0, 2.8, 2.5, 2.0, 1.4, 0.6]
    f.chain(t, pts, wid, name='tail', mat=V('#f0eff6', var=0.04, scales=True, scale_px=4, block=2, scale_rim=0.9))
    for i in range(1, len(pts) - 2):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        for j in (0.3, 0.75):
            m = a + (b - a) * j
            up = np.array([0, -1.0, 0.5]) * (wid[i] * 0.5 + 0.3)
            f.chain(t, [m + up * 0.5, m + up * 1.8 + (b - a) * 0.12], [1.0, 0.2], name='spine', mat=V('#7d8096', var=0.05))
    return f

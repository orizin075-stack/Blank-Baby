"""(054) The villager king's arms, drawn as pixel art in the relic weapons' manner (relic_art: weapon space, u from the
butt (0) to the tip (100), v across) and extruded into his rigs as bevelled slabs (relief), the mace heads as two
crossed slabs. Each design names its grip (where the fist closes) and its half width.

  greatsword     聖剣《黎明》 — the hero's: a broad blade with a burning gold fuller of runes, a guard of gold wings
                 round a sun, a sun pommel.
  yagrush        雷霆棍ヤグルシ（追い払う者） — a white-gold haft wound with gold, a winged collar, a head of lightning.
  aymur          雷霆棍アイムール（駆り立てる者） — a flanged gold head round a sun of white lightning.
  scythe         蝿王の大鎌《ベルゼブブ》 — a black chitin haft; at its head a fly's head with great red eyes and
                 mandibles; a crescent of black chitin with a crimson edge and a veined fly's wing along its back.
  seraph         熾天の剣《セラフ》 — the right twin: white steel, a gold fuller of runes, a guard of white wings under a
                 halo.
  beelzebub      蝿王の剣《ベルゼブブ》 — the left twin: a black serrated blade with a crimson edge, a guard of fly's
                 wings round a red compound eye.
  spear          雷槍 — a long gold-white haft, a blade of lightning between crescent prongs, red tassels.
  bow            虹の大弓 — a recurved bow of rainbow light, gold feathered tips, a sun at the grip, a string of light.
"""
import math
import numpy as np
from pixart import Art, Frame, mat

DESIGNS = {}


def design(name, half_width, grip_u, length, cross=False):
    """length: model units from butt to tip; cross: also drawn turned a quarter (round heads)."""
    def deco(fn):
        DESIGNS[name] = dict(fn=fn, half_width=half_width, grip_u=grip_u, length=length, cross=cross)
        return fn
    return deco


GOLD, GOLD_D, GOLD_L = '#e8b640', '#b4842a', '#ffe7a0'
STEEL, STEEL_L = '#d8dfea', '#f4f7fc'
CHITIN, CHITIN_L = '#1d1724', '#3a2c40'
CRIMSON, RED = '#ff3a1a', '#ff2a10'


def band(a, u, w, m, z=4, th=1.6):
    a.poly([(u - th / 2, -w / 2), (u + th / 2, -w / 2), (u + th / 2, w / 2), (u - th / 2, w / 2)], m, z)


def sun(a, u, v, r, z=6, core='#fff2b0', rays=8):
    gold = mat('metal', GOLD)
    for i in range(rays):
        t = 2 * math.pi * i / rays + math.pi / rays
        L = r * (0.9 if i % 2 == 0 else 0.55)
        a.poly([(u + math.cos(t) * r * 0.6 - math.sin(t) * 0.7, v + math.sin(t) * r * 0.6 + math.cos(t) * 0.7),
                (u + math.cos(t) * (r + L), v + math.sin(t) * (r + L)),
                (u + math.cos(t) * r * 0.6 + math.sin(t) * 0.7, v + math.sin(t) * r * 0.6 - math.cos(t) * 0.7)], gold, z)
    a.ell(u, v, r, r, gold, z + 1)
    a.ell(u, v, r * 0.55, r * 0.55, mat('gem', core, glow=0.8), z + 2)


def feather_fan(a, u, v, sgn, n, L, w, m, z=3, spread=0.55, droop=0.0):
    """A fan of feathers from (u, v) out to side sgn (v sign), each a pointed leaf."""
    for k in range(n):
        ang = (k - (n - 1) / 2) * spread / max(1, n - 1) * 2 + droop
        dl = L * (1 - 0.12 * abs(k - (n - 1) / 2))
        du, dv = math.sin(ang) * dl, sgn * math.cos(ang) * dl
        pu, pv = -dv / dl * w * 0.5 * sgn, du / dl * w * 0.5 * sgn
        a.poly([(u + pu, v + pv), (u + du * 0.65 + pu * 0.9, v + dv * 0.65 + pv * 0.9), (u + du, v + dv),
                (u + du * 0.65 - pu * 0.9, v + dv * 0.65 - pv * 0.9), (u - pu, v - pv)], m, z + k % 2)


def lightning(a, u0, u1, w, z=6, seed=1, core='#ffffff', shell='#ffd23a'):
    """A bolt from u0 to u1 about v = 0: a jagged band, a white core, small forks."""
    rng = np.random.default_rng(seed)
    pts = [(u0, 0.0)]
    n = 6
    for i in range(1, n):
        pts.append((u0 + (u1 - u0) * i / n, (w * 0.55) * (1 if i % 2 else -1) * (0.6 + 0.4 * rng.random())))
    pts.append((u1, 0.0))
    for i in range(len(pts) - 1):
        (a0, b0), (a1, b1) = pts[i], pts[i + 1]
        ww = w * (1 - 0.6 * i / n)
        a.stroke([(a0, b0), (a1, b1)], ww, mat('energy', shell, glow=0.9), z)
        a.stroke([(a0, b0), (a1, b1)], ww * 0.32, mat('energy', core, glow=1.0, outline=False), z + 1)
        if i in (1, 3, 4):
            fu, fv = (a0 + a1) / 2, (b0 + b1) / 2
            sg = 1 if b1 < b0 else -1
            a.curve((fu, fv), (fu + 5, fv + sg * 4), (fu + 9, fv + sg * 7), ww * 0.4, mat('energy', shell, glow=0.9), z, taper=(ww * 0.4, 0.3))


# ------------------------------------------------------------------------------------------------ the hero
@design('greatsword', half_width=15, grip_u=12, length=36)
def d_greatsword(a):
    gold, goldd = mat('metal', GOLD), mat('metal', GOLD_D)
    steel, edge = mat('metal', STEEL), mat('metal', STEEL_L)
    # pommel: a small sun; grip of blue leather wound with gold
    sun(a, 2.8, 0, 2.6, z=5, core='#7fc4ff', rays=8)
    a.poly([(4.5, -1.7), (21, -1.7), (21, 1.7), (4.5, 1.7)], mat('cloth', '#22407e', pattern='wrap'), 2)
    for u in (6, 12.5, 19.5):
        band(a, u, 4.2, gold, 4, 1.4)
    # the guard: gold wings out of a sun, feathers drooping toward the blade
    a.poly([(21, -6), (24.5, -6.5), (24.5, 6.5), (21, 6)], gold, 4)
    for sgn in (-1, 1):
        a.poly([(21.5, sgn * 5), (23.5, sgn * 14.5), (26.5, sgn * 13.5), (25, sgn * 5)], goldd, 3)
        feather_fan(a, 22.5, sgn * 7.5, sgn, 4, 7.5, 2.4, mat('metal', '#f6f0dc'), z=2, spread=0.5, droop=0.55)
    sun(a, 23, 0, 3.4, z=7, core='#9fe0ff')
    # ricasso and blade
    a.poly([(25, -3.6), (31, -3.6), (31, 3.6), (25, 3.6)], steel, 3)
    band(a, 28, 7.6, goldd, 4, 1.2)
    a.poly([(31, -5.0), (90, -4.2), (99.5, 0), (90, 4.2), (31, 5.0)], steel, 3)
    a.poly([(31, -5.0), (90, -4.2), (99.5, 0), (90, -2.9), (31, -3.6)], edge, 4)
    a.poly([(31, 5.0), (90, 4.2), (99.5, 0), (90, 2.9), (31, 3.6)], mat('metal', '#b9c3d4'), 4)
    a.poly([(33, -1.2), (84, -0.9), (87, 0), (84, 0.9), (33, 1.2)], mat('metal', GOLD, pattern='runes', accent='#fff6c8', glow=0.0), 5)
    for k in range(3):
        a.curve((33 + k * 4, -2.6), (35 + k * 4, -3.6), (37 + k * 4, -2.4), 0.6, goldd, 6)
        a.curve((33 + k * 4, 2.6), (35 + k * 4, 3.6), (37 + k * 4, 2.4), 0.6, goldd, 6)


# ------------------------------------------------------------------------------------------------ the god's divine arms
@design('yagrush', half_width=13, grip_u=10, length=34)
def d_yagrush(a):
    gold, goldd = mat('metal', GOLD), mat('metal', GOLD_D)
    a.ell(1.8, 0, 2.4, 2.4, gold, 4)
    a.dot(1.8, 0, mat('gem', '#9fe0ff', glow=0.7), 6, r=1.0)
    a.poly([(3, -1.6), (56, -1.4), (56, 1.4), (3, 1.6)], mat('metal', '#f2ead6'), 2)
    for u in range(8, 54, 6):
        a.stroke([(u, -1.6), (u + 3, 1.6)], 0.9, goldd, 3)
    for u in (4.5, 20, 36, 52):
        band(a, u, 3.8, gold, 4, 1.8)
    # the collar: gold wings
    a.poly([(54, -3.2), (60, -3.8), (60, 3.8), (54, 3.2)], gold, 5)
    for sgn in (-1, 1):
        feather_fan(a, 56, sgn * 3.0, sgn, 3, 7.0, 2.2, mat('metal', GOLD_L), z=4, spread=0.45, droop=-0.35)
    sun(a, 57.5, 0, 2.4, z=7, core='#ffffff', rays=6)
    lightning(a, 59, 100, 7.0, z=6, seed=3)


@design('aymur', half_width=14, grip_u=10, length=32, cross=True)
def d_aymur(a):
    gold, goldd, goldl = mat('metal', GOLD), mat('metal', GOLD_D), mat('metal', GOLD_L)
    a.ell(1.8, 0, 2.4, 2.4, gold, 4)
    a.poly([(3, -1.7), (72, -1.5), (72, 1.5), (3, 1.7)], mat('metal', '#e6d9b8'), 2)
    a.poly([(62, -2.6), (69, -3.4), (69, 3.4), (62, 2.6)], gold, 4)
    for u in range(7, 58, 5):
        band(a, u, 3.6 if u % 2 else 3.2, goldd, 3, 1.0)
    # the head: flanges, a crown, a sun of lightning at its heart
    c = 78
    for k in range(7):
        ang = -math.pi / 2 + k * math.pi / 6
        r0, r1 = 7.5, 14.0
        du, dv = math.sin(ang + math.pi / 2), math.cos(ang + math.pi / 2)
        a.poly([(c + du * r0 - dv * 2.2, dv * r0 + du * 2.2), (c + du * r1 - dv * 1.0, dv * r1 + du * 1.0),
                (c + du * (r1 + 2.2), dv * (r1 + 2.2)), (c + du * r1 + dv * 1.0, dv * r1 - du * 1.0),
                (c + du * r0 + dv * 2.2, dv * r0 - du * 2.2)], goldd if k % 2 else gold, 3)
    a.ell(c, 0, 9.5, 9.0, gold, 5)
    a.ring(c, 0, 9.5, 7.8, goldl, 6)
    a.ell(c, 0, 5.2, 5.2, mat('energy', '#fff6d0', glow=0.95), 7)
    a.ell(c, 0, 2.6, 2.6, mat('energy', '#ffffff', glow=1.0, outline=False), 8)
    for k in range(8):
        ang = k * math.pi / 4
        a.stroke([(c + math.cos(ang) * 2.8, math.sin(ang) * 2.8), (c + math.cos(ang) * 6.6, math.sin(ang) * 6.6)], 0.8,
                 mat('energy', '#ffffff', glow=1.0, outline=False), 9)
    a.poly([(c + 8.5, -1.6), (c + 19, 0), (c + 8.5, 1.6)], gold, 4)
    a.ell(c + 19.5, 0, 1.6, 1.6, mat('gem', '#ffe27a', glow=0.8), 6)


# ------------------------------------------------------------------------------------------------ the demon's scythe
@design('scythe', half_width=44, grip_u=8, length=46)
def d_scythe(a):
    chitin, chitl = mat('metal', CHITIN), mat('metal', CHITIN_L)
    gold = mat('metal', GOLD)
    a.poly([(0, -1.8), (86, -1.6), (86, 1.6), (0, 1.8)], chitin, 2)
    for u in range(4, 84, 7):
        a.poly([(u, -1.9), (u + 4.5, -2.3), (u + 4.5, 2.3), (u, 1.9)], chitl, 3)
        band(a, u + 5.5, 4.0, gold if u % 14 == 4 else mat('metal', '#8a1a20'), 4, 0.9)
    for u in range(10, 80, 14):
        a.poly([(u, 2.0), (u + 1.5, 4.8), (u + 3, 2.0)], chitl, 3)
    # the crescent: out from the socket to -v, its spine arching up then sweeping down toward the butt; the
    # cutting edge below the spine, glowing crimson; barbs along the edge; a fly's wing standing on the spine
    n = 20
    spine, edge_ = [], []
    for k in range(n + 1):
        t = k / n
        v = -2.0 - 40.0 * t
        u = 90.0 + 7.0 * math.sin(math.pi * t * 0.75) - 26.0 * t ** 2.2
        w = 8.5 * (1 - t) ** 0.8 + 0.6
        spine.append((u, v))
        edge_.append((u - w, v + w * 0.18))
    a.poly(spine + edge_[::-1], chitin, 3)
    a.poly(spine[:n - 2] + [(u - 2.4, v) for (u, v) in edge_[:n - 2]][::-1], chitl, 4)
    a.stroke([(u + 0.3, v) for (u, v) in edge_], 1.8, mat('energy', CRIMSON, glow=0.95), 5)
    for i in range(2, n - 2, 3):
        (u, v) = edge_[i]
        a.poly([(u + 0.5, v - 1.0), (u - 2.4, v + 0.6), (u + 0.5, v + 1.2)], mat('metal', '#3a1018'), 6)
    # a fly's pair of wings flaring back from the head, away from the blade: smoky glass, dark veins
    for (bu, bv, tu, tv, wd, z) in ((90.5, 4.0, 79.0, 24.0, 6.5, 2), (88.0, 3.5, 70.0, 15.5, 5.0, 3)):
        du, dv = tu - bu, tv - bv
        L = math.hypot(du, dv)
        nu, nv = -dv / L, du / L
        pts = []
        for k in range(13):
            t = k / 12
            w = wd * math.sin(math.pi * t) ** 0.8
            pts.append((bu + du * t + nu * w * 0.6, bv + dv * t + nv * w * 0.6))
        for k in range(12, -1, -1):
            t = k / 12
            w = wd * math.sin(math.pi * t) ** 0.8
            pts.append((bu + du * t - nu * w * 0.4, bv + dv * t - nv * w * 0.4))
        a.poly(pts, mat('cloth', '#b8a4b0'), z)
        a.stroke([(bu, bv), (tu, tv)], 0.7, mat('dark', '#2a1820'), z)
        for t in (0.3, 0.55, 0.8):
            pu, pv = bu + du * t, bv + dv * t
            a.stroke([(pu, pv), (pu + nu * wd * 0.5 + du * 0.08, pv + nv * wd * 0.5 + dv * 0.08)], 0.5, mat('dark', '#2a1820'), z)
            a.stroke([(pu, pv), (pu - nu * wd * 0.35 + du * 0.08, pv - nv * wd * 0.35 + dv * 0.08)], 0.5, mat('dark', '#2a1820'), z)
    # the fly's head at the socket: great red compound eyes, mandibles
    a.ell(89, 0, 5.4, 5.0, chitin, 6)
    for sgn in (-1, 1):
        a.ell(90.5, sgn * 3.6, 3.6, 3.0, mat('gem', RED, glow=0.8), 7)
        for k in range(5):
            a.dot(89.5 + (k % 3) * 1.1, sgn * (2.7 + (k // 3) * 1.4), mat('energy', '#ffb08a', glow=0.9), 8)
        a.curve((85, sgn * 2.4), (83, sgn * 4.4), (81, sgn * 3.2), 1.0, mat('metal', '#2a1a20'), 7)
    band(a, 84.5, 6.0, gold, 7, 1.2)


# ------------------------------------------------------------------------------------------------ the twin swords
@design('seraph', half_width=12, grip_u=10, length=29)
def d_seraph(a):
    gold, goldl = mat('metal', GOLD), mat('metal', GOLD_L)
    a.poly([(0, 0), (2.4, -2.2), (4.6, 0), (2.4, 2.2)], mat('gem', '#ffe27a', glow=0.7), 5)
    a.poly([(4, -1.5), (19, -1.4), (19, 1.4), (4, 1.5)], mat('cloth', '#f4f0e6', pattern='wrap'), 2)
    for u in (5, 12, 18.5):
        band(a, u, 3.4, gold, 4, 1.2)
    for sgn in (-1, 1):
        feather_fan(a, 20.5, sgn * 2.0, sgn, 4, 9.0, 2.6, mat('metal', '#fbf8ef'), z=3, spread=0.45, droop=0.35)
    a.poly([(19, -3.2), (22.5, -3.6), (22.5, 3.6), (19, 3.2)], gold, 4)
    a.ring(21, 0, 4.6, 3.6, mat('energy', GOLD_L, glow=0.9), 6)
    a.poly([(22.5, -4.4), (92, -3.4), (100, 0), (92, 3.4), (22.5, 4.4)], mat('metal', STEEL_L), 3)
    a.poly([(22.5, 4.4), (92, 3.4), (100, 0), (92, 2.2), (22.5, 3.0)], mat('metal', '#b9c3d4'), 4)
    a.poly([(25, -0.8), (84, -0.6), (87, 0), (84, 0.6), (25, 0.8)], mat('metal', GOLD, pattern='runes', accent='#fff6c8'), 5)


@design('beelzebub', half_width=12, grip_u=10, length=29)
def d_beelzebub(a):
    chitin = mat('metal', CHITIN)
    a.poly([(0, -1.0), (3, -2.6), (4.5, 0), (3, 2.6), (0, 1.0)], chitin, 4)
    a.poly([(4, -1.5), (19, -1.4), (19, 1.4), (4, 1.5)], mat('cloth', '#5a1018', pattern='wrap'), 2)
    for u in (5, 12, 18.5):
        band(a, u, 3.4, mat('metal', '#8a1a20'), 4, 1.2)
    for sgn in (-1, 1):
        wing = [(20, sgn * 1.5), (22, sgn * 8.5), (27, sgn * 11.0), (29, sgn * 7.0), (25, sgn * 2.5)]
        a.poly(wing, mat('cloth', '#4a2a2e'), 2)
        a.stroke([(20.5, sgn * 2.0), (26.5, sgn * 9.5)], 0.5, mat('dark', '#120a10'), 3)
        a.stroke([(22, sgn * 4.0), (28, sgn * 7.5)], 0.5, mat('dark', '#120a10'), 3)
    a.poly([(19, -3.0), (23, -3.4), (23, 3.4), (19, 3.0)], chitin, 4)
    a.ell(21, 0, 2.6, 2.4, mat('gem', RED, glow=0.85), 6)
    # a black blade, serrated along its back, its edge crimson
    back = [(23, 3.2)]
    for k in range(10):
        u = 26 + k * 6.6
        back += [(u, 3.2 - k * 0.07), (u + 2.2, 4.6 - k * 0.1), (u + 4.4, 3.0 - k * 0.07)]
    pts = [(23, -3.4), (90, -2.4), (100, 0)] + back[::-1]
    a.poly(pts, chitin, 3)
    a.stroke([(23, -3.0), (90, -2.0), (99.5, 0)], 1.1, mat('energy', CRIMSON, glow=0.95), 5)
    for k in range(6):
        a.dot(30 + k * 10, 0.6, mat('energy', '#ff6a3a', glow=0.9), 6)


# ------------------------------------------------------------------------------------------------ the spear
@design('spear', half_width=10, grip_u=22, length=46)
def d_spear(a):
    gold, goldd = mat('metal', GOLD), mat('metal', GOLD_D)
    a.poly([(0, 0), (4, -1.4), (4, 1.4)], gold, 3)
    a.poly([(4, -1.3), (74, -1.2), (74, 1.2), (4, 1.3)], mat('metal', '#f2ead6'), 2)
    for u in range(6, 72, 5):
        a.stroke([(u, -1.3), (u + 2.4, 1.3)], 0.8, goldd, 3)
    for u in (5, 22, 40, 58, 72):
        band(a, u, 3.4, gold, 4, 1.6)
    # crescent prongs and tassels at the socket
    a.poly([(72, -3.0), (77, -3.2), (77, 3.2), (72, 3.0)], gold, 5)
    for sgn in (-1, 1):
        a.curve((75, sgn * 2.6), (78, sgn * 8.5), (84, sgn * 9.0), 1.6, gold, 4, taper=(1.6, 0.4))
        a.curve((74, sgn * 2.4), (70, sgn * 6.0), (64, sgn * 6.5), 1.0, mat('cloth', '#c41a2a'), 3, taper=(1.0, 0.5))
        a.curve((73, sgn * 2.0), (68, sgn * 4.0), (60, sgn * 3.8), 0.9, mat('cloth', '#e0303a'), 3, taper=(0.9, 0.5))
    a.ell(75, 0, 2.0, 2.0, mat('gem', '#9fe0ff', glow=0.8), 6)
    # the blade: a leaf of lightning
    a.poly([(77, -2.6), (86, -4.6), (92, -3.2), (100, 0), (92, 3.2), (86, 4.6), (77, 2.6)], mat('metal', '#fff4d8'), 4)
    a.poly([(78, -1.2), (86, -2.6), (92, -1.6), (98, 0), (92, 1.6), (86, 2.6), (78, 1.2)], mat('metal', GOLD_L), 5)
    lightning(a, 79, 97, 2.6, z=6, seed=7)


# ------------------------------------------------------------------------------------------------ the bow
@design('bow', half_width=13, grip_u=50, length=40)
def d_bow(a):
    """A recurve bow standing along u: a gold riser and grip at its middle; white-gold limbs bowing out to +v and
    recurving at the tips, a thin inlay of rainbow light along each; gold winged nocks; a straight string of light at
    the tips' v; an arrow of light nocked across the grip."""
    gold, goldd, goldl = mat('metal', GOLD), mat('metal', GOLD_D), mat('metal', GOLD_L)
    limbm = mat('metal', '#f6f1e2')
    cols = ['#ff5a5a', '#ffa64a', '#ffe45a', '#6ade6a', '#5ab4ff', '#7a6aff', '#c56aff']

    def back(t):
        """The limb's back (the side away from the string) at t in [0, 1] from the riser's end to the tip."""
        u = 12.0 + 37.0 * t
        v = 7.0 + 2.6 * math.sin(math.pi * min(1.0, t * 1.15)) - 7.5 * t ** 3.2
        return u, v
    tips = []
    for side in (-1, 1):
        outer, inner, mid = [], [], []
        for k in range(21):
            t = k / 20
            u, v = back(t)
            th = 5.0 * (1 - t) + 1.8
            uu = 50 + side * u
            outer.append((uu, v))
            inner.append((uu, v - th))
            mid.append((uu, v - th * 0.5))
        a.poly(outer + inner[::-1], limbm, 3)
        for k in range(20):
            c = cols[min(6, k * 7 // 20)]
            a.stroke([mid[k], mid[k + 1]], 1.7, mat('energy', c, glow=0.5, outline=False), 5)
        tu, tv = outer[-1]
        tips.append((tu, tv - 1.0))
        # the nock: a gold curl with feathers
        a.ell(tu, tv - 0.6, 1.8, 1.8, gold, 6)
        feather_fan(a, tu - side * 0.5, tv + 0.6, 1, 3, 4.8, 1.6, goldl, z=4, spread=0.45, droop=-side * 0.35)
        # gold bands where the limb meets the riser and in its middle
        for k in (0, 10):
            (u1, v1), (u2, v2) = outer[k], inner[k]
            a.stroke([(u1, v1 + 0.4), (u2, v2 - 0.4)], 1.4, goldd, 6)
    # the riser and the grip
    a.poly([(37, 4.5), (63, 4.5), (63, 9.8), (55, 11.2), (45, 11.2), (37, 9.8)], gold, 4)
    a.poly([(44, 4.0), (56, 4.0), (56, 10.6), (44, 10.6)], mat('cloth', '#4a2a18', pattern='wrap'), 5)
    for u in (44, 56):
        a.stroke([(u, 3.6), (u, 11.0)], 1.3, goldd, 6)
    sun(a, 50, 12.2, 2.0, z=7, core='#ffffff', rays=8)
    # the string
    (u0, v0), (u1, v1) = tips
    sv = min(v0, v1)
    a.stroke([(u0, sv), (u1, sv)], 0.7, mat('energy', '#ffffff', glow=1.0, outline=False), 2)
    # the arrow of light, nocked: from the string out past the grip
    a.stroke([(50, sv - 0.5), (50, 19.0)], 0.9, mat('energy', '#fff6d0', glow=1.0, outline=False), 8)
    a.poly([(48.4, 18.5), (50, 22.5), (51.6, 18.5)], mat('energy', '#ffffff', glow=1.0), 8)
    for sg in (-1, 1):
        a.poly([(50, sv), (50 + sg * 1.6, sv - 1.6), (50 + sg * 0.8, sv + 1.8)], mat('energy', '#ffe27a', glow=0.9), 8)


# ------------------------------------------------------------------------------------------------ into the rigs
def _thicken(art):
    """Half-thickness (texels) by material: metal blades bevel to a thin edge, grips and wraps are thick, gems and
    the small ornaments drawn over the body (z >= 5) stand proud of it."""
    for k, (mk, m, z, i) in enumerate(art.shapes):
        if any(key in m for key in ('d', 'raise', 'inset', 'up')):
            continue
        st = m.get('style')
        if st == 'gem':
            m2 = dict(m, **{'raise': 0.75})
        elif z >= 5:
            m2 = dict(m, **{'raise': 0.5})
        elif st == 'cloth' and m.get('pattern') == 'wrap':
            m2 = dict(m, d=2.0)
        elif st == 'cloth':
            m2 = dict(m, d=0.5)                     # wings, tassels: thin
        elif st == 'energy':
            m2 = dict(m, d=1.0, d0=0.5, bev=2)
        elif st == 'metal':
            m2 = dict(m, d=1.5, d0=0.5, bev=3)
        else:
            m2 = dict(m, d=1.0)
        art.shapes[k] = (mk, m2, z, i)


def place(bone, name, hand, U, V, res=3, cross=None, clip=None, post=None, nm=None):
    """The design `name` as a bevelled slab on `bone`: its grip (u = grip_u, v = 0) at `hand`, u running along U
    (butt to tip), v along V (its width; the slab's flats face U x V). clip=(u0, u1) keeps only that stretch (the
    broken form's floating pieces); post(rgba) may deface the rendered pixels. cross: also a second slab turned a
    quarter about U (round heads); True crosses the whole design, a number only from that u on."""
    import bb
    d = DESIGNS[name]
    s = d['length'] * res / 100.0
    W = int(math.ceil(100 * s)) + 4
    H = int(math.ceil(d['half_width'] * 2 * s)) + 4
    U, V = np.asarray(U, float), np.asarray(V, float)
    U, V = U / np.linalg.norm(U), V / np.linalg.norm(V)
    gx, gy = 2 + d['grip_u'] * s, H / 2.0
    at = np.asarray(hand, float) - gx / res * U - gy / res * V

    def art_fn(lo=None):
        def fn(a):
            a.f = Frame(W, H, (2, H / 2.0), (1, 0), s)
            d['fn'](a)
            if clip is not None or lo is not None:
                u0, u1 = clip if clip is not None else (-10, 110)
                if lo is not None:
                    u0 = max(u0, lo)
                xs = (np.arange(W) - 2) / s
                keep = (xs >= u0) & (xs < u1)
                a.shapes = [(mk & keep[None, :], m, z, i) for (mk, m, z, i) in a.shapes if (mk & keep[None, :]).any()]
            _thicken(a)
            if post is not None:
                orig = a.render
                a.render = lambda *x, **k: post(*orig(*x, **k))
        return fn
    out = [bb.relief_bb(bone, art_fn(), W, H, tuple(at), tuple(U), tuple(V), name=nm or ('arm_' + name), res=res)]
    if cross is not None and cross is not False:
        V2 = np.cross(U, V)
        lo = None if cross is True else float(cross)
        at2 = np.asarray(hand, float) - gx / res * U - gy / res * V2
        out.append(bb.relief_bb(bone, art_fn(lo), W, H, tuple(at2), tuple(U), tuple(V2), name=(nm or ('arm_' + name)) + '_x', res=res))
    return out


def render_sprite(name, px_per_unit=4):
    """The design as an RGBA sprite (for previews)."""
    d = DESIGNS[name]
    L = d['length'] * px_per_unit
    s = L / 100.0
    w = int(math.ceil(d['half_width'] * 2 * s)) + 4
    h = int(math.ceil(100 * s)) + 4
    f = Frame(w, h, (w / 2, h - 2), (0, -1), s)
    a = Art(f)
    d['fn'](a)
    return a.render()


if __name__ == '__main__':
    import sys
    from PIL import Image
    out = sys.argv[1]
    ims = []
    for n in DESIGNS:
        rgba, _ = render_sprite(n)
        ims.append(Image.fromarray(rgba, 'RGBA'))
    W = sum(i.width * 2 + 8 for i in ims)
    H = max(i.height * 2 for i in ims)
    c = Image.new('RGBA', (W, H), (40, 44, 52, 255))
    x = 0
    for i in ims:
        j = i.resize((i.width * 2, i.height * 2), Image.NEAREST)
        c.paste(j, (x, H - j.height), j)
        x += j.width + 8
    c.save(out)
    print(c.size)

"""Painters for the cube-built creatures (creatures_ia.py): eyes, mouths, teeth and wing skin.

Ice and Fire and vanilla Minecraft give a creature a face with a few deliberate texels: an eye is a small plate
standing proud of the head with a dark rim, an iris, a pupil and a catchlight; a mouth is a dark red interior with a
tongue, lined with separate tooth cubes. These painters draw those parts; the bodies keep the Grimoire of Gaia / Ice
and Fire painters (gaiapaint) for scales, fur, feathers, horns and gems.

  M('eye', iris, out='left'|'right'|'front', pupil='slit'|'round'|'ring'|'none', sclera=None|colour, lid=colour,
    look=-1..1 (pupil toward the front), mood='calm'|'fierce'|'kind'|'happy')
  M('mouth', '#5a1420')       mouth interior: gums at the edges, tongue down the middle
  M('tooth', '#efe6d2')       ivory, lit at the root
  M('wingskin', colour, poly=[(a, b), ...], axes='xz', veins=[(a0, b0, a1, b1), ...], accent=vein colour)
"""
import numpy as np
import bbpaint as BP
import gaiapaint as GP
from colors import hexc, mix, shade

C = BP.C


def ramp(c, k):
    return BP.ramp(c, k)


def _blank(f, colour, k=1.0):
    rgb = np.empty((f.H, f.W, 3), np.float32)
    rgb[...] = C(shade(colour, k)) if k != 1.0 else C(colour)
    return rgb


def m_eye(mat, f, s, ctx):
    out = mat.get('out', s.info.get('out', 'front'))
    lid = mat.get('lid', '#1c1a22')
    if f.face != out:
        return _blank(f, lid, 0.8), None, None
    W, H = f.W, f.H
    iris = hexc(mat['color'])
    sclera = mat.get('sclera')
    mood = mat.get('mood', 'calm')
    look = float(mat.get('look', 0.35))
    # which way is the creature's front in this face's u: +u on the right side of the head, -u on the left
    front = {'right': 1, 'left': -1}.get(out, 0)
    u = (f.u + 0.5) / W * 2 - 1           # -1..1 across
    v = (f.v + 0.5) / H * 2 - 1           # -1 top .. 1 bottom
    rgb = np.empty((H, W, 3), np.float32)
    glow = np.zeros((H, W, 4), np.float32)
    # eye white (or a full iris for dragons and beasts)
    if sclera:
        rgb[...] = C(sclera)
        cx = look * front * 0.28
        r = 0.62
        irism = ((u - cx) / r) ** 2 + (v / 0.95) ** 2 <= 1.0
    else:
        cx = look * front * 0.12
        irism = np.ones((H, W), bool)
    # iris: darker under the upper lid, brighter toward the bottom (light through the lens)
    t = (v + 1) / 2
    ik = np.where(t < 0.3, 0.72, np.where(t < 0.62, 1.0, 1.22)).astype(np.float32)
    ir = ramp(C(iris), ik)
    rgb[irism] = ir[irism]
    # pupil
    pupil = mat.get('pupil', 'slit')
    pc = C(mat.get('pupil_colour', '#0b0a10'))
    px = cx
    if pupil == 'slit':
        pm = (np.abs(u - px) * W < 0.75) & (np.abs(v) < 0.8)
    elif pupil == 'round':
        rr = max(0.34, 1.6 / max(W, H))
        pm = ((u - px) / (rr * 1.0)) ** 2 + (v / (rr * W / H * 1.0 + 0.2)) ** 2 <= 1.0
    elif pupil == 'ring':
        d = np.sqrt((u - px) ** 2 + v ** 2)
        pm = (d > 0.35) & (d < 0.6)
    else:
        pm = np.zeros((H, W), bool)
    rgb[pm & irism] = pc
    # lids: the mood shapes the upper lid line
    top = np.zeros((H, W), bool)
    if mood == 'fierce':                    # a heavy brow slanting down toward the front
        cut = -1 + 0.55 + 0.45 * (u * front if front else 0)
        top = v < cut
    elif mood == 'kind':                    # drooping outer corner, soft
        cut = -1 + 0.35 - 0.25 * (u * front if front else 0)
        top = v < cut
    elif mood == 'happy':                   # a smiling lower lid
        top = (v > 0.55 - 0.5 * np.abs(u)) | (v < -0.85)
    else:
        top = v < -0.78
    rgb[top] = C(lid)
    # dark rim along the upper edge and at the corners: the eye reads at any distance
    if H >= 3:
        rim = (f.v == 0) | ((f.u == 0) | (f.u == W - 1)) & ((f.v == 0) | (f.v == H - 1))
        rgb[rim] = C(shade(lid, 0.7))
    # catchlight: one or two white texels high up, toward the back
    hx = int(np.clip(round((0.5 - 0.25 * front) * (W - 1)), 0, W - 1)) if W > 2 else 0
    hy = 1 if H >= 4 else 0
    if not top[hy, hx]:
        rgb[hy, hx] = C('#ffffff')
        if W >= 6 and H >= 4 and not top[hy, min(W - 1, hx + 1)]:
            rgb[hy, min(W - 1, hx + 1)] = C(mix('#ffffff', mat['color'], 0.4))
    if mat.get('glow', True):
        gm = irism & ~pm & ~top
        glow[gm, :3] = ir[gm]
        glow[gm, 3] = 255 * float(mat.get('glow_amount', 0.75))
        glow[hy, hx, :3] = 255
        glow[hy, hx, 3] = 255
    return rgb, None, glow


def m_mouth(mat, f, s, ctx):
    base = mat['color']
    W, H = f.W, f.H
    k = np.ones((H, W), np.float32)
    # gums along the edges, shadow inside, a tongue down the middle of the floor
    if W >= 3:
        k[:, 0] = k[:, -1] = 1.25
    if H >= 3:
        k[0, :] *= 0.75
    rgb = ramp(C(base), k)
    if f.face == 'top' and W >= 5:
        tongue = np.abs(f.u - (W - 1) / 2) < max(1.0, W * 0.22)
        tk = ramp(C(mat.get('tongue', '#c2485c')), np.where(f.v % 3 == 0, 1.12, 1.0).astype(np.float32))
        rgb[tongue] = tk[tongue]
    return rgb, None, None


def m_tooth(mat, f, s, ctx):
    base = mat['color']
    k = np.ones((f.H, f.W), np.float32)
    if f.side and f.H >= 2:
        k[0, :] = 0.86                       # root
        k[-1, :] = 1.12                      # tip
    rgb = ramp(C(base), k)
    return rgb, None, None


def m_wingskin(mat, f, s, ctx):
    """Membrane cut to a polygon (Ice and Fire wings): alpha outside it, veins fanning from the arm, lighter toward
    the free edge. poly and veins are in model coordinates on the plate's two in-plane axes (axes='xz' for a wing
    laid flat, 'xy' or 'zy' for upright fins)."""
    base = C(mat['color'])
    W, H = f.W, f.H
    P = ctx.get('P')
    poly = mat.get('poly')
    if P is None or poly is None:
        return ramp(base, np.ones((H, W), np.float32)), None, None
    ia, ib = ['xyz'.index(c) for c in mat.get('axes', 'xz')]
    a, b = P[..., ia], P[..., ib]
    inside = _inside(a, b, poly)
    span = np.asarray(poly, float)
    lo, hi = span.min(0), span.max(0)
    t = np.clip(np.hypot(a - span[0][0], b - span[0][1]) / (np.linalg.norm(hi - lo) + 1e-6), 0, 1)
    k = (0.84 + 0.32 * t).astype(np.float32)
    rgb = ramp(base, GP.q(k))
    acc = mat.get('accent')
    glow = None
    texel = 1.0 / max(1, ctx.get('td', 2))
    for (x0, y0, x1, y1) in mat.get('veins', []):
        vm = _near_segment(a, b, (x0, y0), (x1, y1), texel * 0.9)
        if acc:
            rgb[vm] = C(acc)
            if mat.get('glow'):
                glow = glow if glow is not None else np.zeros((H, W, 4), np.float32)
                glow[vm, :3] = C(acc)
                glow[vm, 3] = 170
        else:
            rgb[vm] = ramp(base, 0.66)
    edge = inside & ~_inside(a, b, poly, shrink=texel * 1.5 / (np.linalg.norm(hi - lo) + 1e-6))
    rgb[edge] = ramp(base, 0.7)
    return rgb, inside.astype(np.float32), glow


def _inside(u, v, poly, shrink=0.0):
    P = np.asarray(poly, float)
    if shrink:
        c = P.mean(0)
        P = c + (P - c) * (1 - shrink * 2)
    x, y = u, v
    inside = np.zeros(u.shape, bool)
    n = len(P)
    for i in range(n):
        x0, y0 = P[i]
        x1, y1 = P[(i + 1) % n]
        cond = ((y0 > y) != (y1 > y))
        xi = (x1 - x0) * (y - y0) / ((y1 - y0) + 1e-12) + x0
        inside ^= cond & (x < xi)
    return inside


def _near_segment(u, v, a, b, w):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    t = np.clip(((u - a[0]) * d[0] + (v - a[1]) * d[1]) / (d @ d + 1e-12), 0, 1)
    px, py = a[0] + t * d[0], a[1] + t * d[1]
    return (u - px) ** 2 + (v - py) ** 2 < w * w


PAINTERS = {'eye': m_eye, 'mouth': m_mouth, 'tooth': m_tooth, 'wingskin': m_wingskin}


def enable():
    BP.PAINTERS.update(PAINTERS)

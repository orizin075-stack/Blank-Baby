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
    fr = mat.get('frame')
    if fr is not None:
        # a membrane in any plane: local coordinates along the frame's two in-plane axes
        o, u, v = (np.asarray(x, np.float32) for x in fr)
        d = P - o
        a, b = d @ u, d @ v
    else:
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
        vm = _near_segment(a, b, (x0, y0), (x1, y1), texel * 0.55)
        if acc:
            rgb[vm] = C(acc)
            if mat.get('glow'):
                glow = glow if glow is not None else np.zeros((H, W, 4), np.float32)
                glow[vm, :3] = C(acc)
                glow[vm, 3] = 170
        else:
            rgb[vm] = ramp(base, 0.66)
    streak = mat.get('streaks')
    if streak:
        # brush strokes running out from the root, lighter and darker, as on Monster Expansion's wing membranes
        ang = np.arctan2(b - span[0][1], a - span[0][0])
        h1 = _hash2(np.floor(ang * 40.0), np.floor(t * 9.0), 17)
        h2 = _hash2(np.floor(ang * 60.0 + 3), np.floor(t * 14.0), 23)
        rgb = np.where((h1 > 0.72)[..., None], ramp(base, 1.28), rgb)
        rgb = np.where((h2 > 0.9)[..., None], ramp(base, 0.78), rgb)
        if isinstance(streak, str):
            hm = _hash2(np.floor(ang * 30.0 + 7), np.floor(t * 7.0), 31) > 0.93
            rgb = np.where(hm[..., None], C(streak), rgb)
    bands = mat.get('bands')
    if bands:
        # photon flow (Teia): rainbow bands streaming out from the wing root, bright and glowing
        cols = np.asarray([C(c) for c in bands], np.float32)
        ph = (t * len(cols) * 1.6 + 0.35 * np.sin(np.arctan2(b - span[0][1], a - span[0][0]) * 9.0)) % len(cols)
        i0 = np.floor(ph).astype(int) % len(cols)
        fr = (ph - np.floor(ph))[..., None]
        band = cols[i0] * (1 - fr) + cols[(i0 + 1) % len(cols)] * fr
        rgb = rgb * 0.35 + band * 0.65
        glow = glow if glow is not None else np.zeros((H, W, 4), np.float32)
        glow[inside, :3] = rgb[inside]
        glow[inside, 3] = 120
    stars = mat.get('stars')
    if stars:
        # a night sky in the membrane (Demiurgos): sparse stars in model space
        sm = inside & (_hash2(np.floor(a * 2), np.floor(b * 2), 29) > 1 - stars)
        rgb[sm] = C(mat.get('star', '#f4e8ff'))
        glow = glow if glow is not None else np.zeros((H, W, 4), np.float32)
        glow[sm, :3] = rgb[sm]
        glow[sm, 3] = 230
    edge = inside & ~_inside(a, b, poly, shrink=texel * 1.5 / (np.linalg.norm(hi - lo) + 1e-6))
    rgb[edge] = ramp(base, 0.7) if not mat.get('edge') else C(mat['edge'])
    if mat.get('edge') and mat.get('glow'):
        glow = glow if glow is not None else np.zeros((H, W, 4), np.float32)
        glow[edge, :3] = C(mat['edge'])
        glow[edge, 3] = 200
    if mat.get('glow') and glow is None:
        glow = np.zeros((H, W, 4), np.float32)          # only the veins glow, never the whole membrane
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


# ---------------------------------------------------------------------------------------------------------- hides

def _world_uv(ctx, f):
    """Two model-space coordinates running across a face: along the body (z or x) and down it (y), so patterns
    continue from box to box like a hand-painted hide."""
    P, N = ctx['P'], ctx['N']
    ax = np.abs(N)
    side = (ax[..., 0] >= ax[..., 1]) & (ax[..., 0] >= ax[..., 2])
    topb = (ax[..., 1] > ax[..., 0]) & (ax[..., 1] >= ax[..., 2])
    a = np.where(side | topb, P[..., 2], P[..., 0])
    b = np.where(topb, P[..., 0], P[..., 1])
    return a, b, topb


def m_shingle(mat, f, s, ctx):
    """Monster Hunter / Ice and Fire scales: overlapping shingles with a lit top, a curved shadowed lower rim and
    dark gaps, staggered row by row, laid in model space. Bellies (faces looking down) get broad plates."""
    base = C(mat['color'])
    if ctx.get('P') is None:
        return ramp(base, np.ones((f.H, f.W), np.float32)), None, None
    a, b, topb = _world_uv(ctx, f)
    sw = 2.4 * mat.get('scale_size', 1.0)
    sh = 1.9 * mat.get('scale_size', 1.0)
    row = np.floor(b / sh)
    cu = ((a + (row % 2) * sw / 2) % sw) / sw          # 0..1 across the scale
    cv = (b % sh) / sh                                   # 0 top .. 1 bottom
    edge = np.abs(cu - 0.5) * 2                          # 0 centre .. 1 sides
    rim = cv > 0.78 - 0.32 * edge ** 2                   # the curved lower rim
    gap = (cv > 0.93 - 0.2 * edge ** 2) | (edge > 0.94)
    k = np.where(cv < 0.22, 1.2, np.where(rim, 0.78, 1.0)).astype(np.float32)
    k = np.where(gap, 0.55, k)
    k = k * (1.0 - 0.08 * edge)
    N = ctx['N']
    k = k * (1.0 + 0.1 * -N[..., 1])                     # backs a touch lighter under the sky light
    belly = N[..., 1] > 0.55
    rgb = ramp(base, GP.q(k, 0.05))
    if belly.any():
        bc = C(mat.get('belly', '#d8c8a0'))
        bk = np.where((b % 2.2) < 0.45, 0.72, np.where((b % 2.2) < 0.9, 1.15, 1.0)).astype(np.float32)
        rgb[belly] = ramp(bc, bk)[belly]
    glow = None
    cs = mat.get('countershade')
    if cs is not None:
        # sharks and orcas: the pale belly colour climbs the flanks below a wavy line (an orca's white patches)
        line, wav = cs if isinstance(cs, (tuple, list)) else (cs, 0.0)
        side = np.abs(N[..., 0]) > 0.45
        low = side & (b > line + wav * np.sin(a * 0.45))
        if low.any():
            bc = C(mat.get('belly', '#d8c8a0'))
            rgb[low] = ramp(bc, np.where(cv < 0.22, 1.08, np.where(rim, 0.9, 1.0)).astype(np.float32))[low]
            belly = belly | low
    glow = _marks(mat, a, b, N, belly, rgb, f, glow)
    pat = mat.get('stripes')
    if pat:
        col, period, width = pat
        sm = (np.abs(((a * 0.8 + b * 0.35) % period) - period / 2) < width) & ~belly
        rgb[sm] = ramp(C(col), k)[sm]
    acc = mat.get('glints')
    if acc:
        # a gem set in one scale here and there: its colour across the upper half, a bright facet on top
        gl = (_hash2(np.floor(a / sw), row, 7) > 1 - mat.get('glint_rate', 0.045)) & (cv < 0.55) & (edge < 0.8) & ~belly
        cols = [C(c) for c in acc]
        idx = (_hash2(np.floor(a / sw), row, 13) * len(cols)).astype(int) % len(cols)
        for i, c in enumerate(cols):
            m = gl & (idx == i)
            rgb[m] = np.where((cv < 0.2)[..., None], np.minimum(255, c * 1.35 + 40), c)[m]
        glow = glow if glow is not None else np.zeros((f.H, f.W, 4), np.float32)
        glow[gl, :3] = rgb[gl]
        glow[gl, 3] = 220
    return rgb, None, glow


def _marks(mat, a, b, N, belly, rgb, f, glow):
    """Glowing marks laid in model space on the flanks: waves=[(y, amplitude, wavelength, phase), ...] (Enkou's
    sea-life patterns, circuit lines) and dots=(y, spacing, size) (a row of photophores), in mat['mark']."""
    col = mat.get('mark')
    if not col:
        return glow
    side = np.abs(N[..., 0]) > 0.45
    m = np.zeros(a.shape, bool)
    for (y, amp, wl, ph) in mat.get('waves', ()):
        m |= side & (np.abs(b - (y + amp * np.sin(a * 2 * np.pi / wl + ph))) < 0.32)
    d = mat.get('dots')
    if d:
        y, sp, sz = d
        m |= side & (np.abs(b - y) < sz) & (np.abs((a % sp) - sp / 2) < sz)
    if not m.any():
        return glow
    rgb[m] = C(col)
    glow = glow if glow is not None else np.zeros((f.H, f.W, 4), np.float32)
    glow[m, :3] = C(col)
    glow[m, 3] = 230
    return glow


def _hash2(x, y, seed):
    h = (x.astype(np.int64) * 73856093) ^ (y.astype(np.int64) * 19349663) ^ (seed * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def m_carapace(mat, f, s, ctx):
    """Armour plate / carapace: a smooth gradient from a lit top edge to a dark lower lip, a pale bevel line along
    the top, two or three scratches, and an optional glowing seam (accent)."""
    base = C(mat['color'])
    W, H = f.W, f.H
    t = (f.v + 0.5) / H
    side = f.face not in ('top', 'bottom')
    if side:
        k = (1.18 - 0.38 * t).astype(np.float32)
    else:
        k = np.full((H, W), 1.12 if f.face == 'top' else 0.7, np.float32)
    if W >= 3:
        k[:, 0] *= 0.85
        k[:, -1] *= 0.85
    if side and H >= 3:
        k[0, :] = 1.42
        k[-1, :] *= 0.62
    rgb = ramp(base, GP.q(k, 0.05))
    hm = BP.hashmap(H, W, f.seed)
    scratch = (hm > 0.985) & side
    rgb[scratch] = ramp(base, 0.7)
    glow = None
    trim = mat.get('trim')
    if trim and W >= 4 and H >= 4:
        # ornate gold edging one texel in from the rim (and a second inner line on big plates): divine armour
        e = np.zeros((H, W), bool)
        e[1, 1:-1] = e[-2, 1:-1] = True
        e[1:-1, 1] = e[1:-1, -2] = True
        if W >= 10 and H >= 10:
            e[3, 3:-3] = e[-4, 3:-3] = True
            e[3:-3, 3] = e[3:-3, -4] = True
        rgb[e] = ramp(C(trim), np.where(f.v[e] < H / 2, 1.18, 0.92).astype(np.float32))
        if mat.get('trim_glow'):
            glow = np.zeros((H, W, 4), np.float32)
            glow[e, :3] = C(trim)
            glow[e, 3] = 150
    acc = mat.get('accent')
    if acc and side and H >= 5:
        mid = H // 2
        rgb[mid, 1:-1] = C(acc)
        glow = glow if glow is not None else np.zeros((H, W, 4), np.float32)
        glow[mid, 1:-1, :3] = C(acc)
        glow[mid, 1:-1, 3] = 230
    return rgb, None, glow


def m_hide(mat, f, s, ctx):
    """Smooth hide (whales, sharks): soft mottling in model space, countershaded, with optional pale spots."""
    base = C(mat['color'])
    if ctx.get('P') is None:
        return ramp(base, np.ones((f.H, f.W), np.float32)), None, None
    a, b, topb = _world_uv(ctx, f)
    N = ctx['N']
    mott = np.sin(a * 0.9 + np.sin(b * 0.7) * 1.3) * np.sin(b * 1.1 + np.cos(a * 0.4))
    k = 1.0 + 0.06 * np.round(mott * 2) / 2 + 0.12 * -N[..., 1]
    belly = N[..., 1] > 0.5
    rgb = ramp(base, GP.q(k.astype(np.float32), 0.04))
    if belly.any():
        bc = C(mat.get('belly', '#e0e8ec'))
        grooves = (b % 1.4) < 0.35 if mat.get('grooves') else np.zeros_like(belly)
        bk = np.where(grooves, 0.8, 1.05).astype(np.float32)
        rgb[belly] = ramp(bc, bk)[belly]
    glow = _marks(mat, a, b, N, belly, rgb, f, None)
    spots = mat.get('spots')
    if spots:
        sp = (_hash2(np.floor(a / 1.6), np.floor(b / 1.6), 3) > 0.9) & ~belly
        rgb[sp] = C(spots)
        if mat.get('spots_glow'):
            glow = glow if glow is not None else np.zeros((f.H, f.W, 4), np.float32)
            glow[sp, :3] = C(spots)
            glow[sp, 3] = 230
    return rgb, None, glow


def m_strata(mat, f, s, ctx):
    """Layered rock (Kurma): bands of colour by height in model space, gently warped, each with a grainy texture,
    darker cracks between layers, sparse glowing ore (mat['ore']) and a grass or snow cover on faces looking up
    (mat['top'])."""
    bands = [C(c) for c in mat.get('bands', [mat['color']])]
    if ctx.get('P') is None:
        return ramp(bands[0], np.ones((f.H, f.W), np.float32)), None, None
    P, N = ctx['P'], ctx['N']
    a, b, topb = _world_uv(ctx, f)
    th = mat.get('band', 1.6)
    yy = P[..., 1] + 0.5 * np.sin(a * 0.35 + 0.8) + 0.3 * np.sin(a * 0.9)
    idx = np.floor(yy / th).astype(int)
    col = np.asarray(bands, np.float32)[idx % len(bands)]
    grain = _hash2(np.floor(a * 2), np.floor(b * 2), 5)
    k = 0.9 + 0.2 * np.round(grain * 3) / 3
    crack = (((yy / th) % 1.0) > 0.88) & bool(mat.get('cracks', True))
    k = np.where(crack, 0.68, k)
    k = k * (1.0 + 0.1 * -N[..., 1])
    rgb = (col * k[..., None]).clip(0, 255).astype(np.float32)
    glow = None
    ore = mat.get('ore')
    if ore:
        om = (_hash2(np.floor(a * 1.5), np.floor(b * 1.5), 41) > 0.985) & ~crack
        rgb[om] = C(ore)
        glow = np.zeros((f.H, f.W, 4), np.float32)
        glow[om, :3] = C(ore)
        glow[om, 3] = 220
    top = mat.get('top')
    if top:
        up = N[..., 1] < -0.5
        tk = 0.92 + 0.16 * np.round(_hash2(np.floor(a * 2), np.floor(b * 2), 9) * 2) / 2
        rgb[up] = ramp(C(top), tk.astype(np.float32))[up]
        # the cover spills one texel over the top edge of the sides
        if f.face not in ('top', 'bottom') and f.H >= 3:
            fringe = (f.v == 0) | ((f.v == 1) & (_hash2(f.u.astype(float), f.v.astype(float), 3) > 0.5))
            rgb[fringe] = ramp(C(top), 0.85)
    return rgb, None, glow


def m_gel(mat, f, s, ctx):
    """Clear living gel (Mels): see-through colour, denser toward the rim of the sphere (c, r) so the outline reads,
    a sharp specular window high on the front-left and a soft rim light low on the back-right."""
    base = C(mat['color'])
    if ctx.get('P') is None:
        return ramp(base, np.ones((f.H, f.W), np.float32)), np.full((f.H, f.W), 0.45, np.float32), None
    P = ctx['P']
    c = np.asarray(mat.get('c', (0, 0, 0)), float)
    rr = float(mat.get('r', 4.0))
    d = P - c
    dist = np.sqrt((d ** 2).sum(-1)) / rr
    a0 = mat.get('alpha', 110)
    a0 = a0 / 255.0 if a0 > 1 else a0
    alpha = np.clip(a0 * (0.75 + 0.6 * dist ** 3), 0, 0.92).astype(np.float32)
    k = (1.08 - 0.22 * dist).astype(np.float32)
    rgb = ramp(base, GP.q(k, 0.05))
    hl = np.asarray(mat.get('light', (-0.42, -0.5, -0.6)), float) * rr + c
    spec = ((P - hl) ** 2).sum(-1) < (rr * 0.16) ** 2
    rgb[spec] = C('#ffffff')
    alpha[spec] = 0.95
    rim = (dist > 0.92) & (d[..., 1] > 0.2 * rr)
    rgb[rim] = ramp(base, 1.3)
    glow = np.zeros((f.H, f.W, 4), np.float32)
    glow[spec, :3] = 255
    glow[spec, 3] = 200
    return rgb, alpha, glow


def m_silk(mat, f, s, ctx):
    """Clean, bright fur of a sacred beast: long fine strands laid along the body in model space, low contrast, lit
    from above, with an occasional sheen strand (mat['sheen']) and a pale tip band (mat['tip'])."""
    base = C(mat['color'])
    if ctx.get('P') is None:
        return ramp(base, np.ones((f.H, f.W), np.float32)), None, None
    a, b, topb = _world_uv(ctx, f)
    N = ctx['N']
    row = np.floor(b * 2.0)
    ph = _hash2(row, row * 0 + 3, 11) * 6.0
    strand = np.sin(a * 1.7 + ph) > 0.55
    k = np.where(strand, 1.06, 0.97).astype(np.float32)
    k = k * (1.0 + 0.1 * -N[..., 1])
    rgb = ramp(base, GP.q(k, 0.03))
    sh = mat.get('sheen')
    glow = None
    if sh:
        sm = strand & (_hash2(np.floor(a * 0.8), row, 19) > 0.86)
        rgb[sm] = C(sh)
        if mat.get('sheen_glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            glow[sm, :3] = C(sh)
            glow[sm, 3] = 120
    return rgb, None, glow


PAINTERS.update({'shingle': m_shingle, 'carapace': m_carapace, 'hide': m_hide, 'strata': m_strata, 'gel': m_gel, 'silk': m_silk})

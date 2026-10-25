"""0.17.27 painters in the manner of Grimoire of Gaia (clean pixel art, soft rounded shading, warm skin, glossy hair
locks) and Ice and Fire (creature skins: overlapping scales with a lit upper edge, feathers with shaft and barbs,
veined wing membranes, ridged horns), for the Blockbench-style cuboids of bb.py.

Every face is shaded as part of a rounded body, not as a flat panel: across its width it is lit in the middle and a
step or two darker toward its edges (a limb, a lock of hair, a sleeve all read as round), and down its height it is
lighter at the top and darker at the bottom. Shading stays in whole ramp steps (quantised) so it is still pixel art.
Signature as bbpaint's painters: painter(mat, f, s, ctx) -> (rgb, alpha, glow)."""
import numpy as np
from colors import hexc, mix, shade, lum
import bbpaint as BP
import gaiaface as GF

C = BP.C
ramp = BP.ramp


def q(k, step=0.045):
    return np.round(np.asarray(k, np.float32) / step) * step


def roundk(f, amount=0.16, top=0.06, bottom=0.12, power=1.6):
    """Rounded-body shading of one face: across (edges darker), down (top lighter, bottom darker)."""
    if f.W >= 3:
        x = (f.u + 0.5) / f.W * 2 - 1
        across = 1.0 - amount * np.abs(x) ** power
    else:
        across = np.ones((f.H, f.W), np.float32)
    if f.side and f.H >= 3:
        y = (f.v + 0.5) / f.H
        down = 1.0 + top * (1 - y) - bottom * y
    else:
        down = np.ones((f.H, f.W), np.float32)
    k = across * down
    if f.face == 'top':
        k = k * 1.06
    elif f.face == 'bottom':
        k = k * 0.78
    return k.astype(np.float32)


def outline(rgb, f, base, strength=0.7):
    """A one-texel darker rim on the bottom and side edges of sizeable faces (Gaia's crisp part edges)."""
    if f.W >= 4 and f.H >= 4 and f.side and not f.s.info.get('t_lo') is not None:
        d = ramp(base, strength)
        rgb[-1, :] = rgb[-1, :] * 0.5 + d * 0.5
    return rgb


WORLD_PATTERNS = ('vine', 'circuit', 'marks', 'rings', 'runes', 'dragon', 'chevron', 'stripes')


def world_pattern(name, P, N, seed):
    """Pattern masks in model space (P: per-texel model position, y down), so they run on unbroken across the many
    thin slabs a lofted creature body is built from; lines are about one texel wide."""
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    if name == 'vine':
        c = 2.0 * np.sin(z * 0.27 + seed % 7) + 0.8 * np.sin(z * 0.61 + 1.3)
        d = np.abs((y - c) % 12.0 - 6.0)
        band = d < 0.28
        leaf = (d < 0.85) & (np.abs((z * 0.5) % 4.0 - 2.0) < 0.28)
        return (band | leaf) & (N[..., 1] < 0.5)
    if name == 'circuit':
        gy = np.abs((y % 4.0) - 2.0) < 0.26
        gz = np.abs((z % 6.0) - 3.0) < 0.26
        cell = (np.floor(z / 6.0) * 7 + np.floor(y / 4.0) * 3 + seed) % 5
        node = (np.abs((y % 4.0) - 2.0) < 0.55) & (np.abs((z % 6.0) - 3.0) < 0.55)
        return (gy & (cell < 3)) | (gz & (cell >= 2)) | (node & (cell == 1))
    if name in ('marks', 'chevron'):
        return (np.abs(((z * 0.55 + np.abs(x) * 0.4 + y * 0.3) % 5.0) - 2.5) < 0.4) & (N[..., 1] < 0.3)
    if name == 'stripes':
        return np.abs((z % 5.0) - 2.5) < 0.5
    if name == 'rings':
        return np.abs((y % 5.0) - 2.5) < 0.3
    if name == 'runes':
        cell = (np.floor(z / 2.0) * 5 + np.floor(x / 2.0) * 3 + seed) % 4
        return (np.abs((y % 6.0) - 3.0) < 0.9) & (cell == 0) & (np.abs((z % 2.0) - 1.0) < 0.55)
    if name == 'dragon':
        row = np.floor(y / 1.5)
        cz = (z + (row % 2) * 1.0) % 2.0
        return (np.abs((y % 1.5) - 1.3) < 0.2) | (np.abs(cz - 0.1) < 0.18)
    return np.zeros(P.shape[:2], bool)


def countershade(k, ctx, amount=0.12):
    """Ice and Fire countershading: backs a step darker, bellies a step lighter (model y points down)."""
    N = ctx.get('N')
    if N is None:
        return k
    return k * (1.0 + amount * N[..., 1])


def creature(s):
    rig = getattr(s.bone, 'rig', None)
    return getattr(rig, 'key', '') in CREATURES


CREATURES = {'chaos', 'mels', 'hephaistos', 'enkou', 'kurma', 'teia', 'bahamut', 'eomaia', 'demiurgos', 'yggdrasil', 'nun',
             'forbidden_arcana', 'familiar_drone', 'familiar_beast', 'familiar_sprite', 'familiar_curse'}


def pmask(pat, f, mat, ctx, s):
    if pat in WORLD_PATTERNS and ctx.get('P') is not None and creature(s):
        return world_pattern(pat, ctx['P'], ctx['N'], f.seed % 97)
    return BP.pattern_mask(pat, f, mat)


def m_cloth(mat, f, s, ctx):
    base = C(mat['color'])
    info = s.info
    acc = C(mat.get('accent', '#%02x%02x%02x' % shade(mat['color'], 0.7)))
    glow = None
    k = roundk(f, 0.14, 0.05, 0.14)
    # pleats and folds: a lit ridge, the cloth, a shaded fall and a dark crease, repeating
    if info.get('folds') or info.get('pleats'):
        period = 4 if f.W < 12 else 5
        ph = f.u % period
        fold = np.choose(np.minimum(ph, 4), [1.09, 1.03, 0.97, 0.88, 0.94])
        # creases deepen toward the hem, where the cloth opens
        depth = 0.5 + 0.5 * (f.v / max(1, f.H - 1)) if f.side else 0.6
        k = k * (1 + (fold - 1) * depth)
    rgb = ramp(base, q(k))
    pat = mat.get('pattern')
    pm = BP.pattern_mask(pat, f, mat) if pat else np.zeros((f.H, f.W), bool)
    if pm.any():
        rgb[pm] = ramp(acc, q(k[pm] * 1.04))
        if mat.get('pattern_glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            glow[pm, :3] = acc
            glow[pm, 3] = 255 * float(mat.get('glow_amount', 0.8))
    tr = int(mat.get('trim', 0) or 0)
    if tr and f.side and (info.get('hem', False) or info.get('trim_here')) and f.H >= tr + 2:
        band = f.vb < tr
        rgb[band] = ramp(acc, q(k[band]))
        rgb[f.vb == tr - 1] = ramp(acc, 1.22)                       # lit upper edge of the trim
        rgb[f.vb == tr] = ramp(base, 0.72)                          # the cloth's shadow over it
        if tr >= 3:
            dots = (f.vb == tr // 2) & ((f.u % 3) == 1)              # embroidery stitches along the band
            rgb[dots] = ramp(acc, 1.35)
        rgb[f.vb == 0] = ramp(acc, 0.75)
    if mat.get('trim_top') and f.side and f.H >= 4:
        rgb[f.v < 2] = ramp(acc, 1.0)
        rgb[f.v == 0] = ramp(acc, 1.2)
        rgb[f.v == 2] = ramp(base, 0.8)
    if mat.get('seam') and f.face == 'front' and f.W >= 5:
        cx = f.W // 2
        rgb[:, cx] = ramp(base, 0.8)
        rgb[:, cx + 1] = ramp(base, 1.06) if cx + 1 < f.W else rgb[:, cx + 1 if cx + 1 < f.W else cx]
        btn = (f.v % 4 == 2)
        rgb[btn[:, cx], cx] = ramp(acc, 1.25)
    return rgb, None, glow


def m_skin(mat, f, s, ctx):
    base = C(mat['color'])
    k = roundk(f, 0.18, 0.04, 0.1)
    rgb = ramp(base, q(k))
    # warm shadows: the darker steps lean to rose, as painted skin does
    rose = C(mix(mat['color'], '#c8506a', 0.35))
    dark = q(k) < 0.93
    rgb[dark] = rgb[dark] * 0.78 + ramp(rose, q(k[dark]) + 0.04) * 0.22
    glow = None
    pat = mat.get('pattern')
    if pat:
        pm = BP.pattern_mask(pat, f, mat)
        acc = C(mat.get('accent', '#a03040'))
        rgb[pm] = acc
        if mat.get('pattern_glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            glow[pm, :3] = acc
            glow[pm, 3] = 230
    return rgb, None, glow


def m_hair(mat, f, s, ctx):
    """Hair locks on the strand chains: lit lock middles, darker edges, dark roots, a broken angel ring."""
    R = GF.hair_ramp(mat['color'])
    t = BP.along_t(f, s)
    rgb = np.zeros((f.H, f.W, 3), np.float32)
    lk = GF.locks(f.W, f.seed % 997, 2 if f.W < 6 else 3, 3 if f.W < 6 else 4)
    for i, (a, b) in enumerate(lk):
        for x in range(a, b):
            edge = (x == a and b - a >= 2) or (x == b - 1 and b - a >= 3)
            for y in range(f.H):
                tt = t[y, x]
                key = 'h3' if 0.15 <= tt < 0.45 else ('h2' if tt < 0.85 else 'h1')
                if tt < 0.06:
                    key = 'h1'
                if edge:
                    key = {'h3': 'h2', 'h2': 'h1', 'h1': 'h0'}[key]
                rgb[y, x] = R[key]
    if not f.side:
        rgb = rgb * 1.02
    tip = mat.get('tip')
    if tip:
        w = np.clip((t - 0.55) / 0.45, 0, 1)
        w = np.round(w * 3) / 3
        rgb = rgb * (1 - w[..., None]) + ramp(C(tip), 1.0 - 0.1 * (1 - w))[...] * w[..., None]
    if mat.get('shine', True) and f.side and s.info.get('shine_row') is not None:
        r = int(s.info['shine_row'] * f.H)
        for i, (a, b) in enumerate(lk):
            y = r + (i % 2)
            if 0 <= y < f.H:
                rgb[y, a + (1 if b - a >= 3 else 0):b] = R['hl']
    return rgb, None, None


def m_metal(mat, f, s, ctx):
    """Polished metal: a bright upper band, the base, a dark lower band, a lit bevel on the top / left edges and a
    dark one on the bottom / right, a narrow diagonal glint."""
    base = C(mat['color'])
    if creature(s) and ctx.get('N') is not None:
        N = ctx['N']
        k = (1.0 - 0.16 * N[..., 1] + 0.1 * np.clip(-N[..., 2], 0, 1)).astype(np.float32)
        k = k * np.where(np.abs(((ctx['P'][..., 1] + ctx['P'][..., 2] * 0.5) % 7.0) - 3.5) < 0.35, 1.25, 1.0)
        rgb = ramp(base, q(k, 0.05))
        glow = None
        acc = C(mat.get('accent', '#%02x%02x%02x' % shade(mat['color'], 0.6)))
        pat = mat.get('pattern')
        if pat:
            pm = pmask(pat, f, mat, ctx, s)
            rgb[pm] = ramp(acc, q(k[pm]))
            if mat.get('pattern_glow'):
                glow = np.zeros((f.H, f.W, 4), np.float32)
                glow[pm, :3] = acc
                glow[pm, 3] = 255 * float(mat.get('glow_amount', 0.8))
        return rgb, None, glow
    k = np.ones((f.H, f.W), np.float32)
    if f.side and f.H >= 4:
        y = (f.v + 0.5) / f.H
        k = np.where(y < 0.3, 1.18, np.where(y < 0.62, 1.0, 0.8)).astype(np.float32)
    elif f.face == 'top':
        k = k * 1.2
    elif f.face == 'bottom':
        k = k * 0.62
    if f.W >= 3 and f.H >= 3:
        k[0, :] *= 1.25
        k[:, 0] *= 1.12
        k[-1, :] *= 0.62
        k[:, -1] *= 0.76
    if f.W >= 5 and f.H >= 5 and f.side:
        d = (f.u + f.v) % (f.W + f.H)
        k = k * np.where((d >= int(f.W * 0.4)) & (d < int(f.W * 0.4) + 1), 1.35, 1.0)
    rgb = ramp(base, q(k, 0.05))
    glow = None
    acc = C(mat.get('accent', '#%02x%02x%02x' % shade(mat['color'], 0.6)))
    pat = mat.get('pattern')
    if pat:
        pm = pmask(pat, f, mat, ctx, s)
        rgb[pm] = ramp(acc, q(k[pm]))
        if mat.get('pattern_glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            glow[pm, :3] = acc
            glow[pm, 3] = 255 * float(mat.get('glow_amount', 0.8))
    if mat.get('rivets') and f.W >= 5 and f.H >= 5:
        for (y, x) in ((1, 1), (1, f.W - 2), (f.H - 2, 1), (f.H - 2, f.W - 2)):
            rgb[y, x] = ramp(base, 1.45)
            if y + 1 < f.H:
                rgb[y + 1, x] = ramp(base, 0.58)
    eg = mat.get('edge_glow')
    if eg:
        glow = glow if glow is not None else np.zeros((f.H, f.W, 4), np.float32)
        e = np.zeros((f.H, f.W), bool)
        e[0, :] = e[-1, :] = True
        e[:, 0] = e[:, -1] = True
        rgb[e] = C(eg)
        glow[e, :3] = C(eg)
        glow[e, 3] = 220
    return rgb, None, glow


def m_gem(mat, f, s, ctx):
    """Cut gem: a bright table in the upper left, darker pavilion facets toward the lower right, a white sparkle."""
    base = C(mat['color'])
    W, H = f.W, f.H
    x = (f.u + 0.5) / max(1, W)
    y = (f.v + 0.5) / max(1, H)
    d = x + y
    k = np.where(d < 0.7, 1.28, np.where(d < 1.05, 1.08, np.where(d < 1.4, 0.88, 0.7))).astype(np.float32)
    if f.face == 'bottom':
        k *= 0.75
    rgb = ramp(base, q(k, 0.06))
    if W >= 3 and H >= 3:
        rgb[0, :] = ramp(base, 1.1)
        rgb[:, 0] = np.maximum(rgb[:, 0], ramp(base, 1.05))
        rgb[min(1, H - 1), min(1, W - 1)] = C(mix(mat['color'], '#ffffff', 0.9))
        if W >= 4 and H >= 4:
            rgb[min(2, H - 1), min(1, W - 1)] = C(mix(mat['color'], '#ffffff', 0.55))
    glow = None
    if mat.get('glow', True):
        glow = np.zeros((H, W, 4), np.float32)
        glow[..., :3] = rgb
        glow[..., 3] = 255 * float(mat.get('glow_amount', 0.55))
    return rgb, None, glow


def m_horn(mat, f, s, ctx):
    """Ridged horn: rings along its length (a lit ridge and a shaded groove), darker at the root."""
    base = C(mat['color'])
    t = BP.along_t(f, s)
    if 't0' in mat:                          # one box of a multi-box horn: its share of the whole horn's length
        t = mat['t0'] + t * (mat.get('t1', 1.0) - mat['t0'])
    k = roundk(f, 0.22, 0.0, 0.0)
    if f.side:
        ring = (f.v % 4)
        k = k * np.choose(ring, [1.14, 1.02, 0.94, 0.8])
    k = k * (0.86 + 0.18 * t)
    rgb = ramp(base, q(k))
    glow = None
    tip = mat.get('tip')
    if tip:
        w = np.clip((t - 0.45) / 0.55, 0, 1)
        w = np.round(w * 4) / 4
        rgb = rgb * (1 - w[..., None]) + ramp(C(tip), q(k)) * w[..., None]
        if mat.get('glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            gm = w > 0.5
            glow[gm, :3] = C(tip)
            glow[gm, 3] = 255 * np.clip(w[gm], 0, 1)
    return rgb, None, glow


def m_scale(mat, f, s, ctx):
    """Ice and Fire scales: rows of overlapping scales (4 x 3 texels), each lit on its upper rim, the colour in its
    middle and in shadow where the next row covers it; rows are staggered. The belly (bottom faces) is lighter and
    plated in broad bands."""
    base = C(mat['color'])
    k = roundk(f, 0.16, 0.05, 0.1)
    if f.face == 'bottom':
        belly = C(mix(mat['color'], mat.get('belly', '#e8d8b0'), 0.45))
        band = f.v % 3
        kb = np.choose(band, [1.1, 1.0, 0.82]).astype(np.float32)
        rgb = ramp(belly, q(kb))
    elif creature(s) and ctx.get('P') is not None:
        # scales laid out in model space, so they run on across the slabs of a lofted body
        P, N = ctx['P'], ctx['N']
        ax = np.abs(N)
        side = (ax[..., 0] >= ax[..., 1]) & (ax[..., 0] >= ax[..., 2])
        topb = (ax[..., 1] > ax[..., 0]) & (ax[..., 1] >= ax[..., 2])
        a = np.where(side | topb, P[..., 2], P[..., 0])
        b = np.where(topb, P[..., 0], P[..., 1])
        sw, sh = 2.0 * mat.get('scale_size', 1.0), 1.5 * mat.get('scale_size', 1.0)
        row = np.floor(b / sh)
        cu = ((a + (row % 2) * sw / 2) % sw) / sw
        cv = (b % sh) / sh
        sk = np.where(cv < 0.3, np.where((cu > 0.2) & (cu < 0.8), 1.2, 1.05),
                      np.where(cv < 0.7, np.where(cu < 0.15, 0.86, 1.0), 0.8))
        sk = np.where(N[..., 1] > 0.6, 1.08, sk)                  # the belly is plated, not scaled
        sk = 1 + (sk - 1) * mat.get('contrast', 1.0)
        rgb = ramp(base, q(countershade(k, ctx) * sk))
    else:
        row = f.v // 3
        cu = (f.u + (row % 2) * 2) % 4
        cv = f.v % 3
        sk = np.where(cv == 0, np.where((cu == 1) | (cu == 2), 1.2, 1.06),
                      np.where(cv == 1, np.where(cu == 0, 0.86, 1.0), np.where(cu == 3, 0.72, 0.82)))
        rgb = ramp(base, q(k * sk))
    glow = None
    pat = mat.get('pattern')
    if pat:
        pm = pmask(pat, f, mat, ctx, s)
        acc = C(mat.get('accent', '#ffffff'))
        rgb[pm] = acc
        if mat.get('pattern_glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            glow[pm, :3] = acc
            glow[pm, 3] = 230
    return rgb, None, glow


def m_fur(mat, f, s, ctx):
    """Fur in tufts: short diagonal strokes, light tips, dark roots between tufts."""
    base = C(mat['color'])
    k = roundk(f, 0.14, 0.05, 0.1)
    hm = BP.hashmap(f.H, f.W, f.seed)
    tuft = (f.u + f.v // 2 * 2 + (f.v % 2)) % 4
    k = k * np.choose(tuft, [1.12, 1.03, 0.94, 0.84]) * np.where(hm > 0.93, 1.08, 1.0)
    rgb = ramp(base, q(k))
    tip = mat.get('tip')
    if tip and f.side:
        tipz = f.vb < max(1, f.H // 4)
        rgb[tipz] = ramp(C(tip), q(k[tipz]))
    return rgb, None, None


def m_feather(mat, f, s, ctx):
    """Feathers: a pale shaft down the middle, barbs angled away from it, the vane darker toward its edge, tips in
    the accent colour."""
    base = C(mat['color'])
    k = roundk(f, 0.12, 0.04, 0.06)
    cx = f.W // 2
    off = np.abs(f.u - cx)
    barb = ((f.v + off) % 3 == 0)
    k = k * np.where(barb, 0.88, 1.0) * (1 - 0.1 * (off / max(1, f.W / 2)))
    rgb = ramp(base, q(k))
    if f.side and f.W >= 3:
        rgb[:, cx] = C(mix(mat['color'], '#ffffff', 0.45))
    tip = mat.get('tip')
    glow = None
    if tip and f.side:
        w = np.clip((f.v / max(1, f.H - 1) - 0.55) / 0.45, 0, 1)
        w = np.round(w * 3) / 3
        rgb = rgb * (1 - w[..., None]) + ramp(C(tip), q(k)) * w[..., None]
        if mat.get('glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            tz = w > 0.3
            glow[tz, :3] = C(tip)
            glow[tz, 3] = 200
    return rgb, None, glow


def m_membrane(mat, f, s, ctx):
    """Wing membrane: lighter (thinner) toward its free edge, veins fanning from the bone side."""
    base = C(mat['color'])
    y = (f.v + 0.5) / max(1, f.H)
    k = (0.86 + 0.22 * y).astype(np.float32) * roundk(f, 0.08, 0.0, 0.0)
    rgb = ramp(base, q(k))
    fan = ((f.u * 2 + f.v) % 9 == 0) | ((f.u * 3 - f.v) % 13 == 0)
    glow = None
    acc = mat.get('accent')
    if acc:
        rgb[fan] = C(acc)
        glow = np.zeros((f.H, f.W, 4), np.float32)
        glow[fan, :3] = C(acc)
        glow[fan, 3] = 140
    else:
        rgb[fan] = ramp(base, 0.72)
    if f.side and f.H >= 3:
        rgb[0, :] = ramp(base, 0.7)                                 # the bone edge
    return rgb, None, glow


OVERRIDES = {'cloth': m_cloth, 'skin': m_skin, 'simple': m_skin, 'hair': m_hair, 'metal': m_metal, 'gem': m_gem,
             'horn': m_horn, 'scale': m_scale, 'fur': m_fur, 'feather': m_feather, 'membrane': m_membrane}


def _eye_axes(nrm):
    """Horizontal and vertical axes in the plane of an eye facing along nrm (model y is the vertical)."""
    n = nrm / max(1e-9, np.linalg.norm(nrm))
    up = np.array([0.0, 1.0, 0.0])
    if abs(float(n @ up)) > 0.9:
        up = np.array([0.0, 0.0, 1.0])
    h = np.cross(up, n)
    h /= max(1e-9, np.linalg.norm(h))
    v = np.cross(n, h)
    return h, v


def spots(rgb, alpha, glow, s, ctx):
    """Eyes (Ice and Fire style: dark lid rim, iris lit from below with radial streaks, slit or round pupil, a white
    catchlight up and to the side), dots and lines, painted where they sit on the model."""
    PL, NL = ctx.get('PL'), ctx.get('NL')
    if PL is None:
        return rgb, glow
    H, W = rgb.shape[:2]
    for sp in s.info.get('spots', []):
        kind = sp.get('kind')
        p = np.asarray(sp['p'], np.float32)
        r = float(sp['r'])
        if kind == 'line':
            p2 = np.asarray(sp['p2'], np.float32)
            d = p2 - p
            t = np.clip(((PL - p) @ d) / max(1e-9, float(d @ d)), 0, 1)
            dist = np.linalg.norm(PL - (p + t[..., None] * d), axis=-1)
            m = dist < r
            if m.any():
                col = C(sp['color'])
                rgb[m] = col
                if sp.get('glow'):
                    glow = glow if glow is not None else np.zeros((H, W, 4), np.float32)
                    glow[m, :3] = col
                    glow[m, 3] = 230
            continue
        dist = np.linalg.norm(PL - p, axis=-1)
        m = dist < r
        if not m.any():
            continue
        if kind == 'dot':
            col = C(sp['color'])
            rgb[m] = ramp(col, np.where(dist[m] < r * 0.5, 1.12, 0.94))
            if sp.get('glow'):
                glow = glow if glow is not None else np.zeros((H, W, 4), np.float32)
                glow[m, :3] = col
                glow[m, 3] = 255 * float(sp.get('glow_amount', 1.0))
            continue
        # eye
        nrm = NL[m].mean(0)
        h, v = _eye_axes(nrm)
        x = ((PL - p) @ h) / r
        y = ((PL - p) @ v) / r
        rr = np.sqrt(x * x + y * y)
        iris = C(sp['color'])
        pup = C(sp.get('pupil', '#0a0c14'))
        e = m & (rr < 1.0)
        rim = e & (rr >= 0.82)
        ir = e & (rr < 0.82)
        # iris: darker at the top (under the lid's shadow), lit from below, radial streaks
        ang = np.arctan2(y, x)
        streak = (np.round(ang / (np.pi / 6)) % 2 == 0) & (rr > 0.35)
        k = np.where(y > 0.25, 0.78, np.where(y > -0.2, 1.0, 1.22)) * np.where(streak, 0.92, 1.0)
        rgb[ir] = ramp(iris, q(k[ir]))
        rgb[rim] = C(mix(sp.get('pupil', '#0a0c14'), sp['color'], 0.25))
        if sp.get('slit', True):
            pm = ir & (np.abs(x) < 0.17 + 0.05 * (1 - np.abs(y))) & (np.abs(y) < 0.72)
        else:
            pm = ir & (rr < 0.36)
        rgb[pm] = pup
        hl = ir & (((x + 0.34) ** 2 + (y - 0.38) ** 2) < 0.045)
        rgb[hl] = C('#ffffff')
        if sp.get('glow', True):
            glow = glow if glow is not None else np.zeros((H, W, 4), np.float32)
            gm = ir & ~pm
            glow[gm, :3] = rgb[gm]
            glow[gm, 3] = 235
            glow[hl, :3] = 255
            glow[hl, 3] = 255
    return rgb, glow


_base_paint = BP.paint_surf


def paint_surf(s, ctx):
    rgb, alpha, glow = _base_paint(s, ctx)
    if s.info.get('spots'):
        rgb = np.array(rgb, np.float32)
        rgb, glow = spots(rgb, alpha, glow, s, ctx)
    return rgb, alpha, glow


def enable():
    BP.PAINTERS.update(OVERRIDES)
    BP.paint_surf = paint_surf

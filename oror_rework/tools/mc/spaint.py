"""Painters for sculpted surfaces (sculpt.py), two texels per model pixel.

Same style rules as paint.py (hue-shifted 5-tone ramps, light texel jitter, one-texel hems and seams),
but shading now follows the real shape: every texel knows its rest-pose position, normal and ambient
occlusion, so folds, crevices and the underside of hair and skirts darken where they really are.

Region axes of a sweep: x runs around the section (front of the part in the middle), y runs along
the path (start at row 0)."""
import math
import numpy as np
from colors import hexc, mix, shade, lum
import paint as PT
from paint import ramp, colorize, jitter

# ------------------------------------------------------------------------------ shared
def coords(s):
    W, H = s.size
    ys, xs = np.mgrid[0:H, 0:W]
    u = (xs + 0.5) / W
    v = (ys + 0.5) / H
    th = s.info.get('theta')
    if th is not None:
        theta = th[0] + (th[-1] - th[0]) * u
    else:
        theta = (u - 0.5) * 2 * math.pi
    return xs, ys, u, v, theta

def form_tone(ctx, k_light=0.55, k_ao=2.4):
    N = ctx['N']
    up = -N[..., 1]
    t = k_light * up + 0.18 * np.maximum(0, -N[..., 2])       # a little extra on front-facing texels
    t += k_ao * (ctx['ao'] - 1.0)
    return t

def glow_from(rgb, mask, amount=1.0, color=None):
    H, W = mask.shape
    g = np.zeros((H, W, 4), np.float32)
    if color is not None:
        g[mask, :3] = hexc(color)
    else:
        g[mask, :3] = rgb[mask]
    g[mask, 3] = 255 * amount
    return g

def _acc(mat):
    return mat.get('accent', shade(mat['color'], 0.7))

def trim_rows(mat, td):
    tr = mat.get('trim', 0)
    return int(round(tr * td / 2 * 1.5)) if tr else 0

# ------------------------------------------------------------------------------ patterns (texel art at 2x)
def pattern(name, s, ctx, xs, ys, u, v, theta):
    """Boolean mask in the surface's region."""
    W, H = s.size
    td = ctx['td']
    rng = ctx['rng']
    P = ctx['P']
    m = np.zeros((H, W), bool)
    if name == 'stars':
        n = max(2, W * H // 70)
        for _ in range(n):
            x, y = int(rng.integers(1, max(2, W - 1))), int(rng.integers(1, max(2, H - 1)))
            m[y, x] = True
            if rng.random() < 0.45:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= y + dy < H and 0 <= x + dx < W:
                        m[y + dy, x + dx] = True
    elif name == 'embroidery':
        y0 = H - max(4, int(3 * td)) - trim_rows(s.mat, td)
        if 0 <= y0 < H:
            m[y0, :] = True
            yy = y0 - 2
            if yy >= 0:
                m[yy, :] = (xs[yy] // 2) % 3 == 0
            for x in range(0, W, 6):
                for k in range(3):
                    if 0 <= y0 - 1 - k < H and x + k < W:
                        m[y0 - 1 - k, x + k] = True
    elif name in ('kimono', 'asanoha'):
        pass                                        # torso painter draws the crossed collar
    elif name == 'band':
        y = H // 2
        m[max(0, y - 1):y + 1, :] = True
    elif name == 'vine':
        for x in range(W):
            y = int(round(H * 0.6 + math.sin(x * 0.55) * min(3, H / 5)))
            if 0 <= y < H:
                m[y, x] = True
            if x % 5 == 0 and 0 <= y - 1 < H:
                m[y - 1, x] = True
                if x + 1 < W and y - 2 >= 0:
                    m[y - 2, x + 1] = True
    elif name == 'circuit':
        rows = list(range(int(H * 0.3), H, max(5, int(4 * td))))
        for y in rows:
            m[y, :] = (xs[y] % 9) != 0
            for x in range(3, W, 9):
                m[y:min(H, y + 3), x] = True
                if y + 3 < H:
                    m[y + 3, max(0, x - 1):x + 2] = True
    elif name == 'marks':
        for _ in range(max(1, W * H // 50)):
            x, y = int(rng.integers(0, W)), int(rng.integers(0, H))
            m[y:y + 2, x] = True
    elif name in ('trim', 'gold_lines'):
        if s.kind == 'sweep':
            # vertical lines down the front opening and the sides
            for th0 in ((-0.35, 0.35) if name == 'gold_lines' else (-0.25, 0.25)):
                d = np.abs(((theta - th0 + math.pi) % (2 * math.pi)) - math.pi)
                m |= d < (1.0 / max(4, W)) * math.pi * 1.2
            if name == 'trim':
                m[:1, :] = True
                m[-1:, :] = True
        else:
            m[:, 0] = m[:, -1] = True
            if name == 'trim':
                m[0, :] = m[-1, :] = True
    elif name == 'trim_top':
        m[0, :] = True
    elif name == 'stripes':
        m = (xs // 2) % 3 == 1
    elif name == 'runes':
        for x in range(2, W - 2, 7):
            y = int(rng.integers(int(H * 0.25), max(int(H * 0.25) + 1, H - 4)))
            glyph = rng.integers(0, 4)
            pts = {0: [(0, 0), (0, 1), (0, 2), (1, 1)], 1: [(0, 0), (1, 1), (2, 2), (0, 2)],
                   2: [(1, 0), (0, 1), (2, 1), (1, 2)], 3: [(0, 0), (1, 0), (1, 1), (1, 2), (2, 2)]}[int(glyph)]
            for dx, dy in pts:
                if 0 <= y + dy < H and 0 <= x + dx < W:
                    m[y + dy, x + dx] = True
    elif name in ('dragon', 'scales'):
        m = ((ys % 4 == 0) & (xs % 6 == 0)) | ((ys % 4 == 2) & (xs % 6 == 3))
    elif name == 'dots':
        m = ((xs % 6 == 2) & (ys % 6 == 2)) | ((xs % 6 == 3) & (ys % 6 == 2)) | ((xs % 6 == 2) & (ys % 6 == 3)) | ((xs % 6 == 3) & (ys % 6 == 3))
    elif name == 'cross':
        cx = W // 2
        cy = H // 3
        L = max(3, int(2.5 * td))
        m[max(0, cy - L):cy + L + 1, cx - 1:cx + 1] = True
        m[cy - 1:cy + 1, max(0, cx - L + 1):cx + L - 1] = True
    elif name == 'chevron':
        m = ((ys + np.abs(xs - (W - 1) / 2) * 0.8).astype(int) % 7) == 0
    elif name == 'rings':
        m = ys % 6 == 0
    elif name == 'flame':
        for x in range(W):
            hh = int((1.2 + (math.sin(x * 0.7 + 0.7) * 0.5 + 0.5) * 3.5 + (math.sin(x * 1.9) * 0.5 + 0.5) * 2) * td / 2 * 1.6)
            y1 = H - trim_rows(s.mat, td)
            m[max(0, y1 - hh):y1, x] = True
    elif name == 'cracks':
        for _ in range(max(1, W // 12)):
            x = int(rng.integers(0, W))
            for y in range(H):
                m[y, x] = True
                x = int(np.clip(x + rng.integers(-1, 2), 0, W - 1))
    elif name == 'wrap':
        m = ((xs + ys) % 5 == 0) | ((xs - ys) % 5 == 0)
    elif name == 'filigree':
        for y in range(H):
            off = int(round(2.5 * math.sin(y * 0.6)))
            m[y, (xs[y] + off) % 8 == 0] = True
    elif name == 'zigzag':
        m = (ys + np.abs((xs % 8) - 4)) % 8 == 0
    elif name == 'fuller':
        m[:, W // 2] = True
    return m & ctx['cov'] if 'cov' in ctx else m

# ------------------------------------------------------------------------------ surface painters
def s_skin(s, ctx):
    t = form_tone(ctx, 0.5, 2.0)
    rgb = jitter(colorize(t, s.mat['color']), ctx['rng'], 0.012)
    return rgb, None, None

def s_cloth(s, ctx):
    mat = s.mat
    c = mat['color']
    xs, ys, u, v, theta = coords(s)
    W, H = s.size
    td = ctx['td']
    t = form_tone(ctx)
    fn = s.info.get('folds')
    if fn:
        f = np.cos(fn * theta + s.info.get('fold_phase', 0.0))
        depth = np.clip(v * 1.3, 0.2, 1.0) if s.info.get('fold_grow', True) else 1.0
        t += 0.75 * f * depth
    rgb = jitter(colorize(t, c), ctx['rng'], 0.03)
    acc = hexc(_acc(mat))
    glow = None
    pat = mat.get('pattern')
    if pat and s.info.get('pattern', True):
        pm = pattern(pat, s, ctx, xs, ys, u, v, theta)
        if pm.any():
            ac = np.array(ramp(acc)[0 if lum(acc) < 0.8 else -1 if lum(c) > 0.8 else 0], np.float32)
            rgb[pm] = ac
            if mat.get('pattern_glow'):
                rgb[pm] = np.array(ramp(acc)[1], np.float32)
                glow = glow_from(rgb, pm, mat.get('glow_amount', 0.55), acc)
    # hem trim at the end of the path
    tr = trim_rows(mat, td) if s.info.get('hem', True) else 0
    if tr and H > tr + 2:
        rgb[H - tr:, :] = np.array(ramp(acc)[0], np.float32)
        rgb[H - tr, :] = np.array(ramp(acc)[1], np.float32)
        if tr > 2:
            rgb[-1, :] = np.array(ramp(acc)[-1], np.float32)
        if mat.get('pattern_glow') and glow is not None:
            pass
    if mat.get('trim_top'):
        rgb[:max(1, td // 2 + 1), :] = np.array(ramp(acc)[1], np.float32)
    if mat.get('glow') is True:
        glow = glow_from(rgb, np.ones((H, W), bool), 0.8)
    alpha = None
    hem = s.info.get('hem_cut')
    if hem:
        alpha = np.ones((H, W), np.float32)
        if hem == 'scallop':
            per = max(4, int(3 * td))
            for x in range(W):
                k = (x % per) / per
                d = int(round((1 - math.sin(k * math.pi)) * 1.6 * td))
                if d > 0:
                    alpha[H - d:, x] = 0
        elif hem == 'tips':
            for x in range(W):
                if (x // 2) % 2:
                    alpha[-max(1, td):, x] = 0
        elif hem == 'point':
            # pointed panels (coat tails): taper both sides towards the end
            pass
    return rgb, alpha, glow

def s_hair(s, ctx):
    """Anime hair: smooth light-to-shadow form, thin strand lines that follow the clump, a broken 'angel ring'
    highlight near the root and the tip colour fading in towards the ends."""
    mat = s.mat
    c = mat['color']
    xs, ys, u, v, theta = coords(s)
    W, H = s.size
    td = ctx['td']
    t = form_tone(ctx, 0.75, 2.4)
    phase = int(s.info.get('seed', 0)) * 3
    wav = np.round(np.sin(ys * 0.22 + phase) * 1.2).astype(int)
    per = max(4, int(round(1.4 * td)))
    lines = ((xs + wav + phase) % per) == 0
    t -= lines * 0.7
    t += (((xs + wav + phase) % per) == per // 2) * 0.25
    t0, t1 = s.info.get('t0', mat.get('t0', 0.0)), s.info.get('t1', mat.get('t1', 1.0))
    k = t0 + (t1 - t0) * v
    if mat.get('shine', True):
        y0 = mat.get('shine_y', 0.2)
        ring = (np.abs(k - y0) < 0.045 + 0.02 * np.sin(xs * 1.7 + phase)) & ~lines
        t += ring * 1.4
    rgb = colorize(t, c)
    tip = mat.get('tip')
    if tip:
        f = np.clip((k - 0.5) / 0.5, 0, 1) * 0.9
        tc = colorize(t * 0.8, tip)
        rgb = rgb * (1 - f[..., None]) + tc * f[..., None]
    rgb = jitter(rgb, ctx['rng'], 0.01)
    glow = None
    if mat.get('glow'):
        glow = glow_from(rgb, k > 0.6, 0.6)
    return rgb, None, glow

def s_metal(s, ctx):
    mat = s.mat
    c = mat['color']
    xs, ys, u, v, theta = coords(s)
    W, H = s.size
    N = ctx['N']
    t = form_tone(ctx, 0.9, 2.2)
    # polished: a bright streak where the surface faces the upper front, dark reflection below
    view = np.array([0.0, -0.45, -0.89])
    spec = np.clip((N @ view), 0, 1) ** 6
    t += spec * 1.6 - np.maximum(0, N[..., 1]) * 0.6
    rgb = jitter(colorize(t, c), ctx['rng'], 0.015)
    glow = None
    acc = mat.get('accent')
    pat = mat.get('pattern')
    if pat and acc:
        pm = pattern(pat, s, ctx, xs, ys, u, v, theta)
        rgb[pm] = np.array(ramp(acc)[0], np.float32)
        if mat.get('pattern_glow'):
            rgb[pm] = np.array(ramp(acc)[1], np.float32)
            glow = glow_from(rgb, pm, mat.get('glow_amount', 0.55), acc)
    if mat.get('rivets') and W >= 6 and H >= 6:
        step = max(6, int(4 * ctx['td']))
        rv = ((xs % step) == step // 2) & ((ys % step) == step // 2)
        rgb[rv] = np.array(ramp(c)[2], np.float32)
    eg = mat.get('edge_glow')
    if eg:
        edge = np.abs(N[..., 2]) < 0.35
        rgb[edge] = np.array(mix(eg, '#ffffff', 0.3), np.float32)
        g2 = glow_from(rgb, edge, 0.75, eg)
        glow = g2 if glow is None else np.where(g2[..., 3:4] > 0, g2, glow)
    if mat.get('glow') is True:
        glow = glow_from(rgb, np.ones((H, W), bool), 0.8)
    return rgb, None, glow

def s_gem(s, ctx):
    mat = s.mat
    c = mat['color']
    N = ctx['N']
    xs, ys, u, v, theta = coords(s)
    t = 0.4 + 1.2 * (-N[..., 1]) - 0.8 * np.maximum(0, N[..., 0])
    t += ((xs // 2 + ys // 2) % 3 == 0) * 0.5
    rgb = colorize(t, c)
    view = np.array([-0.3, -0.5, -0.81])
    hl = (N @ view) > 0.93
    rgb[hl] = np.array(mix(c, '#ffffff', 0.85), np.float32)
    glow = None
    if mat.get('glow', True):
        glow = glow_from(rgb * 0.9, np.ones(rgb.shape[:2], bool), 0.8)
    return rgb, None, glow

def s_horn(s, ctx):
    mat = s.mat
    c = mat['color']
    tip = mat.get('tip') or shade(c, 0.6)
    xs, ys, u, v, theta = coords(s)
    td = ctx['td']
    t = form_tone(ctx, 0.6, 2.0)
    ridge = max(3, int(2 * td))
    t -= ((ys % ridge) == ridge - 1) * 0.9
    rgb = colorize(t, c)
    k = v if not mat.get('flip_t') else 1 - v
    f = np.clip((k - 0.35) / 0.65, 0, 1)
    tc = colorize(t, tip)
    rgb = rgb * (1 - f[..., None]) + tc * f[..., None]
    rgb = jitter(rgb, ctx['rng'], 0.02)
    glow = None
    if mat.get('glow'):
        gm = k > 0.62
        glow = glow_from(rgb, gm, 0.85, tip)
    return rgb, None, glow

def s_scale(s, ctx):
    mat = s.mat
    c = mat['color']
    xs, ys, u, v, theta = coords(s)
    t = form_tone(ctx, 0.6, 2.2)
    # overlapping scales: rows of arcs, staggered
    row = ys // 4
    off = (row % 2) * 3
    cx = ((xs + off) % 6) - 2.5
    cy = (ys % 4)
    arcm = (cx * cx / 6.5 + (cy - 0.5) ** 2 / 3.0) > 1.0
    t += np.where(cy == 0, 0.8, 0) - arcm * 0.9
    rgb = jitter(colorize(t, c), ctx['rng'], 0.02)
    belly = mat.get('belly')
    if belly:
        N = ctx['N']
        under = N[..., 1] > 0.35
        rgb[under] = colorize(t[under] * 0.5, belly)
    glow = None
    pat, acc = mat.get('pattern'), mat.get('accent')
    if pat and acc:
        pm = pattern(pat, s, ctx, xs, ys, u, v, theta)
        rgb[pm] = np.array(ramp(acc)[0], np.float32)
        if mat.get('pattern_glow'):
            glow = glow_from(rgb, pm, mat.get('glow_amount', 0.6), acc)
    return rgb, None, glow

def s_fur(s, ctx):
    mat = s.mat
    xs, ys, u, v, theta = coords(s)
    t = form_tone(ctx, 0.6, 2.2)
    t += ctx['rng'].integers(-1, 2, t.shape) * 0.5
    t -= ((xs + (ys // 3)) % 3 == 0) * 0.6
    rgb = jitter(colorize(t, mat['color']), ctx['rng'], 0.03)
    if mat.get('tip'):
        f = np.clip((v - 0.6) / 0.4, 0, 1)[..., None]
        rgb = rgb * (1 - f) + colorize(t, mat['tip']) * f
    return rgb, None, None

def s_simple(s, ctx, amp=0.03):
    t = form_tone(ctx)
    rgb = jitter(colorize(t, s.mat['color']), ctx['rng'], amp)
    glow = glow_from(rgb, np.ones(t.shape, bool), 0.8) if s.mat.get('glow') is True else None
    return rgb, None, glow

def s_wood(s, ctx):
    xs, ys, u, v, theta = coords(s)
    t = form_tone(ctx)
    t -= ((xs + np.round(np.sin(ys * 0.3) * 1.2).astype(int)) % 5 == 0) * 0.8
    return jitter(colorize(t, s.mat['color']), ctx['rng'], 0.03), None, None

def s_energy(s, ctx):
    xs, ys, u, v, theta = coords(s)
    t = np.ones(s.size[::-1], np.float32) + ((xs + ys * 2) % 7 == 0)
    rgb = jitter(colorize(t, s.mat['color']), ctx['rng'], 0.05)
    return rgb, None, glow_from(rgb, np.ones(t.shape, bool), 1.0)

def s_ring(s, ctx):
    """Halo tube: bright core, glowing."""
    mat = s.mat
    t = 1.0 + 0.6 * (-ctx['N'][..., 1])
    rgb = colorize(t, mat['color'])
    return rgb, None, glow_from(rgb, np.ones(t.shape, bool), 1.0)

def s_void(s, ctx):
    xs, ys, u, v, theta = coords(s)
    rgb = colorize(form_tone(ctx) - 0.5, s.mat['color'])
    rng = ctx['rng']
    stars = rng.random(rgb.shape[:2]) < 0.02
    rgb[stars] = np.array(mix(s.mat.get('accent', '#d8c8ff'), '#ffffff', 0.4), np.float32)
    return rgb, None, glow_from(rgb, stars, 0.8)

def s_oilslick(s, ctx):
    xs, ys, u, v, theta = coords(s)
    P = ctx['P']
    hue = (np.sin(P[..., 0] * 0.35 + P[..., 1] * 0.22) + np.sin(P[..., 2] * 0.5 - P[..., 1] * 0.17)) * 0.25 + 0.5
    base = np.array(hexc(s.mat['color']), np.float32)
    t = form_tone(ctx)
    rgb = colorize(t, s.mat['color'])
    tints = [np.array(hexc(c), np.float32) for c in ('#7a3a9a', '#2a6a9a', '#3a9a7a', '#9a3a6a')]
    idx = np.clip((hue * 4).astype(int), 0, 3)
    tint = np.stack([tints[i] for i in range(4)])[idx]
    sheen = np.clip(-ctx['N'][..., 1], 0, 1)[..., None] * 0.45
    rgb = rgb * (1 - sheen) + tint * sheen
    return jitter(rgb, ctx['rng'], 0.03), None, None

def s_slime(s, ctx):
    t = form_tone(ctx) + 0.6
    rgb = colorize(t, s.mat['color'])
    hl = (ctx['N'] @ np.array([-0.3, -0.6, -0.74])) > 0.9
    rgb[hl] = np.array(mix(s.mat['color'], '#ffffff', 0.8), np.float32)
    a = np.full(t.shape, (s.mat.get('alpha', 200) / 255.0) if s.mat.get('alpha', 200) > 1 else s.mat.get('alpha'), np.float32)
    return rgb, a, glow_from(rgb, np.ones(t.shape, bool), 0.4)

def s_rainbow(s, ctx):
    xs, ys, u, v, theta = coords(s)
    cols = ['#ff6f6f', '#ffb86f', '#fff06f', '#7fff8f', '#6fd8ff', '#9f8fff', '#ff8fe0']
    k = ((u * 7 + v * 3).astype(int)) % 7
    rgb = np.stack([np.array(hexc(cols[i]), np.float32) for i in range(7)])[k]
    rgb = rgb * (0.8 + 0.2 * (-ctx['N'][..., 1:2]))
    return rgb, None, glow_from(rgb, np.ones(k.shape, bool), 0.7)

def s_feather(s, ctx):
    mat = s.mat
    xs, ys, u, v, theta = coords(s)
    t = form_tone(ctx, 0.5, 2.0)
    t -= ((xs % 4) == 0) * 0.8
    t += ((xs % 4) == 2) * 0.4
    rgb = colorize(t, mat['color'])
    if mat.get('tip'):
        f = np.clip((v - 0.55) / 0.45, 0, 1)[..., None]
        rgb = rgb * (1 - f) + colorize(t, mat['tip']) * f
    glow = glow_from(rgb, v > 0.6, 0.5) if mat.get('glow') else None
    return jitter(rgb, ctx['rng'], 0.02), None, glow

SURF = {'skin': s_skin, 'cloth': s_cloth, 'hair': s_hair, 'metal': s_metal, 'gem': s_gem, 'horn': s_horn,
        'scale': s_scale, 'fur': s_fur, 'wood': s_wood, 'energy': s_energy, 'ring': s_ring, 'void': s_void,
        'oilslick': s_oilslick, 'slime': s_slime, 'rainbow': s_rainbow, 'feather': s_feather}

# ------------------------------------------------------------------------------ box faces (paint.py painters)
def box_face(s, ctx):
    mat = s.mat
    face = s.info['face']
    wpx, hpx = s.info['px']
    w1, h1 = s.info.get('cells') or (max(1, int(round(wpx))), max(1, int(round(hpx))))
    W, H = s.size
    fn = PT.PAINTERS.get(mat['type'], PT.PAINTERS['bone'])
    rgb, alpha, g = fn(mat, face, w1, h1, s.info['cube'], ctx['rng'])
    yi = np.minimum((np.arange(H) * h1 / H).astype(int), h1 - 1)
    xi = np.minimum((np.arange(W) * w1 / W).astype(int), w1 - 1)
    rgb = np.asarray(rgb, np.float32)[yi][:, xi]
    alpha = None if alpha is None else np.asarray(alpha, np.float32)[yi][:, xi]
    if g is not None:
        g = np.asarray(g, np.float32)[yi][:, xi]
    if mat.get('glow') is True and g is None:
        g = np.zeros((H, W, 4), np.float32)
        g[..., :3] = rgb
        g[..., 3] = 255
    if s.info.get('ao', True) and not (mat.get('type') == 'head' and face == 'front'):
        k = 0.38 if mat.get('type') != 'head' else 0.2
        rgb = rgb * ((1 - k) + k * ctx['ao'][..., None])
    if mat.get('alpha') is not None:
        a0 = mat['alpha'] / 255.0 if mat['alpha'] > 1 else mat['alpha']
        alpha = (np.ones((H, W), np.float32) if alpha is None else alpha) * a0
    return rgb, alpha, g

def s_leaf(s, ctx):
    xs, ys, u, v, theta = coords(s)
    t = form_tone(ctx) + ctx['rng'].integers(-1, 2, s.size[::-1]) * 0.6
    t += (((xs // 3) + (ys // 3)) % 2) * 0.5
    rgb = jitter(colorize(t, s.mat['color']), ctx['rng'], 0.04)
    return rgb, None, None

def s_membrane(s, ctx):
    xs, ys, u, v, theta = coords(s)
    t = form_tone(ctx) - 0.3
    t -= ((xs + ys // 2) % 9 == 0) * 0.8
    rgb = jitter(colorize(t, s.mat['color']), ctx['rng'], 0.02)
    acc = s.mat.get('accent')
    glow = None
    if acc:
        vein = (xs + ys // 2) % 9 == 0
        rgb[vein] = np.array(ramp(acc)[0], np.float32)
        glow = glow_from(rgb, vein, 0.5, acc)
    return rgb, None, glow

SURF.update({'leaf': s_leaf, 'membrane': s_membrane, 'bone': s_simple, 'rock': s_simple})

class _Proxy:
    def __init__(self, s, mat, **info):
        self.__dict__.update(s.__dict__)
        self.mat = mat
        self.info = dict(s.info, **info)

def s_torso(s, ctx):
    """Torso loft: upper garment, lower garment below the waist line, neckline / crossed collar / seam."""
    mat = s.mat
    info = s.info
    td = ctx['td']
    rgb, alpha, glow = SURF.get(mat['type'], s_simple)(_Proxy(s, dict(mat), hem=False), ctx)
    P, N = ctx['P'], ctx['N']
    y, x = P[..., 1], P[..., 0]
    lower = info.get('lower')
    ysplit = info.get('y_split')
    acc = hexc(mat.get('accent', shade(mat['color'], 0.7)))
    if lower is not None and lower is not mat and ysplit is not None:
        r2, a2, g2 = SURF.get(lower['type'], s_simple)(_Proxy(s, dict(lower, pattern=None), hem=False), ctx)
        m2 = y > ysplit
        rgb[m2] = r2[m2]
        if g2 is not None:
            glow = np.zeros(rgb.shape[:2] + (4,), np.float32) if glow is None else glow
            glow[m2] = g2[m2]
        elif glow is not None:
            glow[m2] = 0
        edge = m2 & (y < ysplit + 0.55)
        rgb[edge] = np.array(ramp(hexc(lower.get('accent', shade(lower['color'], 0.7))))[-1], np.float32)
    if mat.get('type') in ('cloth', 'metal'):
        top = info.get('top', y.min())
        front = N[..., 2] < -0.15
        skin = np.array(hexc(info.get('skin', '#f3dfd7')), np.float32)
        nl = info.get('neckline')
        if nl == 'v':
            m = front & (y < top + 2.6 - np.abs(x) * 1.6) & (y > top - 2)
            rgb[m] = colorize(form_tone(ctx)[m] * 0.6, info.get('skin', '#f3dfd7'))
        elif nl == 'round':
            m = front & (y < top + 0.9 - np.abs(x) * 0.4)
            rgb[m] = colorize(form_tone(ctx)[m] * 0.6, info.get('skin', '#f3dfd7'))
        elif nl == 'wide':
            m = (y < top + 0.7)
            rgb[m] = colorize(form_tone(ctx)[m] * 0.6, info.get('skin', '#f3dfd7'))
        if mat.get('pattern') in ('kimono', 'asanoha'):
            # crossed collar: the left panel over the right, a band from each shoulder to below the bust
            d1 = np.abs(x - (1.7 - (y - top) * 0.55))
            d2 = np.abs(x + (1.7 - (y - top) * 0.55))
            band = front & (y > top - 0.5) & (y < top + 4.2)
            inner = front & (y < top + 3.2) & (np.abs(x) < 1.6 - (y - top) * 0.5)
            rgb[inner] = colorize(form_tone(ctx)[inner] * 0.5, mix(info.get('skin', '#f3dfd7'), '#ffffff', 0.0)) if nl else \
                np.array(ramp(acc)[1], np.float32)
            pass                                     # the collar bands themselves are sculpted (figure._kimono_collar)
        if mat.get('seam'):
            m = front & (np.abs(x) < 0.28) & (y > top + 1.0)
            rgb[m] = np.array(ramp(acc)[0], np.float32)
            stud = m & (((y - top) * td).astype(int) % (3 * td) == 0)
            rgb[stud] = np.array(ramp(acc)[2], np.float32)
        if info.get('collar') is not None:
            pass
    return rgb, alpha, glow

def eye_cells(spec, build):
    import face8
    eye = face8.EYES[face8.resolve(build, spec)]
    out = []
    for side in (0, 1):
        for row, cols in eye.items():
            for i, ch in enumerate(cols):
                x = 1 + i if side == 0 else 6 - i
                out.append((side, row, x, i, ch))
    return out

def s_head(s, ctx):
    """Head box faces; the face is redrawn at 2x: catchlights, a lash line and a softer chin shadow."""
    rgb, alpha, glow = box_face(s, ctx)
    if s.info.get('face') != 'front' or ctx['td'] < 2:
        return rgb, alpha, glow
    mat = s.mat
    spec = mat.get('face', {})
    build = mat.get('build', 'woman')
    H, W = rgb.shape[:2]
    k = W / 8.0
    iris = hexc(spec.get('iris', '#4a7ad8'))
    import face8
    line = hexc(spec.get('line', mix(hexc(mat.get('hair', '#4a3a30')), '#1a1420', 0.75)))
    style = face8.resolve(build, spec)
    if style in ('closed', 'void'):
        return rgb, alpha, glow
    cells = eye_cells(spec, build)
    for side in (0, 1):
        own = [c for c in cells if c[0] == side]
        iris_cells = [c for c in own if c[4] in 'DIJ']
        if iris_cells:
            top_row = min(c[1] for c in iris_cells)
            col = [c for c in iris_cells if c[1] == top_row][0][2]
            ty, tx = int(top_row * k), int(col * k + (0 if side == 0 else k - 1))
            if 0 <= ty < H and 0 <= tx < W:
                rgb[ty, tx] = np.array(mix(iris, '#ffffff', 0.9), np.float32)
                if glow is not None and glow[ty, tx, 3] > 0:
                    glow[ty, tx, :3] = rgb[ty, tx]
        if build in ('woman', 'child') and style not in ('slit',):
            lash = [c for c in own if c[4] != '.']
            if lash:
                r0 = min(c[1] for c in lash)
                cols_ = sorted(set(c[2] for c in lash))
                y = int(r0 * k)
                for cx in cols_:
                    x0, x1 = int(cx * k), int(cx * k + k)
                    if y < H and spec.get('lash', True):
                        rgb[y, x0:x1] = rgb[y, x0:x1] * 0.35 + np.array(line, np.float32) * 0.65
                # flick at the outer corner
                outer = min(cols_) if side == 0 else max(cols_)
                fx = int(outer * k) - 1 if side == 0 else int(outer * k + k)
                if 0 <= fx < W and 0 <= y < H:
                    rgb[y, fx] = np.array(line, np.float32)
    return rgb, alpha, glow

def s_face(s, ctx):
    import faces
    mat = s.mat
    fi = s.info['face']
    P, N = ctx['P'], ctx['N']
    t = 0.45 * (-N[..., 1]) + 0.12 * np.maximum(0, -N[..., 2]) - 0.25 * np.maximum(0, N[..., 1])
    rgb = jitter(colorize(t, mat['color']), ctx['rng'], 0.006)
    glow = np.zeros(rgb.shape[:2] + (4,), np.float32)
    front = N[..., 2] < -0.08
    rgb, glow = faces.paint_face(rgb, glow, P[..., 0], P[..., 1], front, fi, mat.get('face', {}), mat.get('build', 'woman'),
                                 mat['color'], mat.get('hair', '#3a2a24'))
    return rgb, None, glow if glow[..., 3].any() else None

def s_lids(s, ctx):
    import faces
    mat = s.mat
    fi = s.info['face']
    P, N = ctx['P'], ctx['N']
    H, W = s.size[1], s.size[0]
    rgb = np.zeros((H, W, 3), np.float32)
    alpha = np.zeros((H, W), np.float32)
    front = N[..., 2] < -0.08
    faces.paint_lids(rgb, alpha, P[..., 0], P[..., 1], front, fi, mat.get('face', {}), mat.get('build', 'woman'),
                     mat['color'], mat.get('hair', '#3a2a24'))
    return rgb, alpha, None

SURF.update({'face': s_face, 'lids': s_lids})

def s_rock(s, ctx):
    """Stone with cracks; up-facing texels take the 'top' colour (grass), the highest take 'snow'."""
    mat = s.mat
    xs, ys, u, v, theta = coords(s)
    P, N = ctx['P'], ctx['N']
    t = form_tone(ctx, 0.7, 2.2) + ctx['rng'].integers(-1, 2, s.size[::-1]) * 0.45
    t -= (((xs * 3 + ys * 7) % 11) == 0) * 0.8
    rgb = jitter(colorize(t, mat['color']), ctx['rng'], 0.04)
    top = mat.get('top')
    if top:
        up = -N[..., 1]
        g = up > 0.55 - 0.15 * np.sin(xs * 0.9 + ys * 0.5)
        rgb[g] = colorize(t[g] * 0.6 + 0.3 * (((xs[g] + ys[g]) % 3) == 0), top) * (1 + ctx['rng'].uniform(-0.05, 0.05, (int(g.sum()), 1)))
    snow = mat.get('snow')
    if snow:
        hi = P[..., 1] < mat.get('snow_y', -1e9)
        rgb[hi] = colorize(t[hi] * 0.4 + 0.6, snow)
    glow = None
    if mat.get('cracks') and mat.get('accent'):
        cr = ((np.round(xs + 2 * np.sin(ys * 0.4)).astype(int) % 13) == 0) & (ctx['rng'].random(s.size[::-1]) < 0.85)
        rgb[cr] = np.array(hexc(mat['accent']), np.float32)
        glow = glow_from(rgb, cr, 0.6, mat['accent'])
    return rgb, None, glow

def s_leaf2(s, ctx):
    """Foliage: clumped light/dark leaves, optional blossoms (glowing)."""
    mat = s.mat
    xs, ys, u, v, theta = coords(s)
    rng = ctx['rng']
    t = form_tone(ctx, 0.8, 2.6) + rng.integers(-1, 2, s.size[::-1]) * 0.6
    t += ((((xs // 2) + (ys // 2)) % 3) == 0) * 0.6
    rgb = jitter(colorize(t, mat['color']), rng, 0.04)
    glow = None
    fl = mat.get('flowers')
    if fl:
        m = rng.random(s.size[::-1]) < 0.025
        cols = [np.array(hexc(c), np.float32) for c in fl]
        idx = rng.integers(0, len(cols), s.size[::-1])
        for i, c in enumerate(cols):
            rgb[m & (idx == i)] = c
        if mat.get('flower_glow'):
            glow = glow_from(rgb, m, 0.7)
    return rgb, None, glow

def s_wood2(s, ctx):
    mat = s.mat
    rgb, a, g = s_wood(s, ctx)
    if mat.get('veins'):
        xs, ys, u, v, theta = coords(s)
        vein = (np.abs(((xs + np.round(3 * np.sin(ys * 0.15 + xs * 0.05)).astype(int)) % 17) - 0) < 1)
        rgb[vein] = np.array(hexc(mat['veins']), np.float32)
        g = glow_from(rgb, vein, mat.get('glow_amount', 0.5), mat['veins'])
    return rgb, a, g

SURF.update({'rock': s_rock, 'leaf': s_leaf2, 'wood': s_wood2})

# ------------------------------------------------------------------------------ dispatcher
def paint_surf(s, ctx):
    rgb, alpha, glow = _paint_surf(s, ctx)
    if s.kind != 'box' and s.mat is not None and s.mat.get('alpha') is not None:
        a0 = s.mat['alpha'] / 255.0 if s.mat['alpha'] > 1 else s.mat['alpha']
        alpha = (np.ones(rgb.shape[:2], np.float32) if alpha is None else alpha) * a0
    if s.info.get('spots'):
        rgb, glow = paint_spots(s, ctx, rgb, glow)
    fn = s.info.get('alpha_fn')
    if fn is not None:
        a = fn(ctx)
        alpha = a if alpha is None else alpha * a
    return rgb, alpha, glow

def paint_spots(s, ctx, rgb, glow):
    """Features painted at 3D positions (given in the surface's bone frame): creature eyes with slit pupils and
    catchlights, nostrils, markings, gill lines."""
    import sculpt as SC
    M = SC.rest_matrix(s.bone)
    piv = np.array(s.bone.pivot, float)
    P, N = ctx['P'], ctx['N']
    H, W = rgb.shape[:2]
    if glow is None:
        glow = np.zeros((H, W, 4), np.float32)
    for sp in s.info['spots']:
        c = (M[:3, :3] @ (np.asarray(sp['p'], float) - piv)) + M[:3, 3]
        d = P - c
        kind = sp.get('kind', 'dot')
        r = sp['r']
        if kind == 'line':
            c2 = (M[:3, :3] @ (np.asarray(sp['p2'], float) - piv)) + M[:3, 3]
            ab = c2 - c
            t = np.clip((d @ ab) / max(1e-9, ab @ ab), 0, 1)
            dist = np.linalg.norm(d - t[..., None] * ab, axis=-1)
            m = dist < r
        else:
            dist = np.linalg.norm(d, axis=-1)
            m = dist < r
        if not m.any():
            continue
        col = np.array(hexc(sp['color']), np.float32)
        rgb[m] = col
        if kind == 'eye':
            n = N[m].mean(0)
            n = n / max(1e-9, np.linalg.norm(n))
            up = np.array([0, -1.0, 0])
            side = np.cross(n, up)
            side = side / max(1e-9, np.linalg.norm(side))
            dh = np.abs(d @ side)
            dv = d @ up
            ring = m & (dist > r * 0.78)
            rgb[ring] = np.array(shade(sp['color'], 0.55), np.float32)
            pupil = m & (dh < r * (0.2 if sp.get('slit', True) else 0.42)) & (np.abs(dv) < r * 0.75)
            rgb[pupil] = np.array(hexc(sp.get('pupil', '#0a0c14')), np.float32)
            hl = m & (np.linalg.norm(d - (up * r * 0.45 + side * r * 0.3), axis=-1) < r * 0.24)
            rgb[hl] = 255
            if sp.get('glow', True):
                g = m & ~pupil
                glow[g, :3] = rgb[g]
                glow[g, 3] = 255
        elif sp.get('glow'):
            glow[m, :3] = col
            glow[m, 3] = 255 * float(sp.get('glow_amount', 1.0))
    return rgb, (glow if glow[..., 3].any() else None)

def _paint_surf(s, ctx):
    if s.info.get('painter'):
        return s.info['painter'](s, ctx)
    if s.kind == 'relief':
        rgba = s.info['rgba'].astype(np.float32)
        em = s.info['emis']
        glow = None
        if em.any():
            glow = np.zeros(rgba.shape[:2] + (4,), np.float32)
            glow[em, :3] = rgba[em, :3]
            glow[em, 3] = 255
        return rgba[..., :3], rgba[..., 3] / 255.0, glow
    if s.kind == 'box':
        if s.mat.get('type') == 'head':
            return s_head(s, ctx)
        return box_face(s, ctx)
    if s.info.get('torso'):
        return s_torso(s, ctx)
    fn = SURF.get(s.mat['type'], s_simple)
    return fn(s, ctx)

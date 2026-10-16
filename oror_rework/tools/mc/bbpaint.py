"""Clean pixel-art painters for Blockbench-style cuboids (bb.py).

Every face is painted like a hand-made Blockbench texture: a flat base colour, a hue-shifted ramp (cool
shadows, warm lights) applied in whole steps, a one-texel light top edge and darker bottom / side edges so each
box reads as a crisp panel, and deliberate one-texel details (trims, seams, rivets, strand lines, patterns).
No per-texel noise. painter(s, ctx) -> (rgb, alpha, glow) as sculpt.bake expects."""
import math, zlib
import numpy as np
from colors import hexc, mix, shade, lum
import bbface as BF
import mcface as MF

SIDE = ('front', 'back', 'left', 'right')


def C(c):
    return np.array(hexc(c), np.float32)


ramp = BF.ramp


def _h(*a):
    return zlib.crc32('/'.join(str(x) for x in a).encode())


def hashmap(H, W, seed):
    rng = np.random.default_rng(seed)
    return rng.random((H, W))


# ------------------------------------------------------------------------------------------- geometry of a face
class F:
    """Texel coordinates of one face: u (0..W-1, left->right as seen), v (0..H-1, top->bottom), the face name,
    its size in model pixels and the texel density."""
    def __init__(self, s, ctx):
        self.s = s
        self.W, self.H = s.size
        self.face = s.info.get('face', 'front')
        self.td = ctx['td']
        self.u = np.arange(self.W)[None, :] * np.ones((self.H, 1), int)
        self.v = np.arange(self.H)[:, None] * np.ones((1, self.W), int)
        self.side = self.face in SIDE
        self.seed = _h(s.bone.name, s.name, self.face, s.info.get('seg', 0), s.info.get('col', 0))
        # distance from the hem: bottom of the face for side faces
        self.vb = self.H - 1 - self.v
        self.P = ctx['P']


def edge_k(f, mat, strength=1.0):
    """Painted panel shading: light top edge, dark bottom edge, slightly dark sides. Boxes that are links of a
    chain (hair locks, horns, tails: t_lo in info) keep their length continuous: no top / bottom edge."""
    k = np.ones((f.H, f.W), np.float32)
    chain = f.s.info.get('t_lo') is not None
    if f.face == 'bottom':
        return k * 0.8
    if chain and f.side:
        if f.W >= 3:
            k[:, 0] *= 1.0 - 0.07 * strength
            k[:, -1] *= 1.0 - 0.07 * strength
        return k
    if f.face == 'top':
        if f.W >= 3 and f.H >= 3:
            k[0, :] *= 0.94
            k[-1, :] *= 1.0
            k[:, 0] *= 0.95
            k[:, -1] *= 0.95
        return k * 1.04
    if f.H >= 3:
        k[0, :] *= 1.0 + 0.08 * strength
        k[-1, :] *= 1.0 - 0.14 * strength
        if f.H >= 6:
            k[-2, :] *= 1.0 - 0.05 * strength
    if f.W >= 3:
        k[:, 0] *= 1.0 - 0.06 * strength
        k[:, -1] *= 1.0 - 0.06 * strength
    return k


def quant(k, step=0.04):
    return np.round(k / step) * step


# ------------------------------------------------------------------------------------------- patterns
def pattern_mask(name, f, mat):
    """One-texel accent motifs on a face. Returns (mask, strong) bool arrays."""
    W, H, u, v = f.W, f.H, f.u, f.v
    m = np.zeros((H, W), bool)
    hm = hashmap(H, W, f.seed)
    if name in (None, '', 'kimono', 'seam'):
        return m
    if name == 'band':
        c0, c1 = int(H * 0.38), max(int(H * 0.38) + 2, int(H * 0.62))
        m[c0:c1] = True
    elif name == 'stripes':
        m = (u // 2) % 3 == 0
    elif name == 'embroidery':
        if f.side and H >= 8:
            y0 = H - 5 if mat.get('trim') else H - 3
            band = (f.v >= y0 - 3) & (f.v < y0)
            diamond = (np.abs((u % 6) - 2.5) + np.abs((v - (y0 - 2)) % 4 - 1.5)) <= 1.6
            m = band & diamond
        m |= (u % 8 == 3) & (v % 8 == 3) & (hm < 0.6)
    elif name == 'stars':
        m = hm < 0.025
        star = (hm < 0.008)
        for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            m |= np.roll(np.roll(star, dy, 0), dx, 1)
    elif name == 'runes':
        cell = (u // 4, v // 5)
        bits = hashmap(H, W, f.seed + 7) < 0.45
        inband = (v % 10 >= 3) & (v % 10 <= 6) if H >= 10 else (v >= H // 2 - 1) & (v <= H // 2 + 1)
        m = inband & ((u % 4) != 3) & bits
    elif name == 'circuit':
        m = ((v % 6 == 2) & ((u + v // 6 * 3) % 10 < 7)) | ((u % 7 == 4) & (v % 6 >= 2)) & (hm < 0.85)
        m |= ((v % 6 == 2) & (u % 7 == 4))
    elif name == 'marks':
        # sparse slashes / chevrons (scars, tattoos, oil smears): one per 8x8 cell at most
        rng = np.random.default_rng(f.seed + 3)
        for cy in range(1, max(2, H - 3), 8):
            for cx in range(1, max(2, W - 3), 8):
                if rng.random() < 0.45:
                    continue
                ox, oy = cx + rng.integers(0, 4), cy + rng.integers(0, 4)
                kind = rng.integers(0, 2)
                for i in range(3):
                    y = oy + i
                    for x in ((ox + i,) if kind == 0 else (ox + i, ox + 4 - i)):
                        if 0 <= y < H and 0 <= x < W:
                            m[y, x] = True
    elif name == 'vine':
        y0 = (H * 0.5 + np.sin(u * 0.7 + f.seed % 7) * max(1.0, H * 0.18)).astype(int)
        m = v == y0
        leaf = ((u % 5 == 2) & ((v == y0 - 1) | (v == y0 + 1)))
        m |= leaf
    elif name == 'rings':
        m = (v % 5 == 1)
    elif name in ('gold_lines', 'filigree', 'trim'):
        if W >= 4 and H >= 4:
            m[1, 1:-1] = True
            m[-2, 1:-1] = True
            m[1:-1, 1] = True
            m[1:-1, -2] = True
        if name == 'gold_lines' and f.face == 'front' and W >= 6:
            m[:, W // 2] = True
        if name == 'filigree' and W >= 6 and H >= 6:
            m[2:4, 2:4] = True
            m[2:4, -4:-2] = True
            m[-4:-2, 2:4] = True
            m[-4:-2, -4:-2] = True
            m[H // 2, W // 2 - 1:W // 2 + 1] = True
    elif name == 'cross':
        if f.face in ('front', 'back') and W >= 5 and H >= 6 and abs(float(np.mean(f.P[..., 0]))) < 1.2:
            cx = W // 2
            m[int(H * 0.2):int(H * 0.8), cx - 1:cx + 1] = True
            y = int(H * 0.38)
            m[y:y + 2, max(0, cx - max(2, W // 4)):cx + max(2, W // 4)] = True
    elif name == 'dots':
        m = ((u % 4 == 1) & (v % 4 == 1)) | ((u % 4 == 3) & (v % 4 == 3))
    elif name == 'cracks':
        rng = np.random.default_rng(f.seed)
        for _ in range(max(1, (W * H) // 60)):
            x, y = rng.integers(0, W), rng.integers(0, H)
            for _ in range(rng.integers(3, 9)):
                if 0 <= x < W and 0 <= y < H:
                    m[y, x] = True
                x += rng.integers(-1, 2)
                y += 1 if rng.random() < 0.7 else 0
    elif name == 'chevron':
        m = ((v + np.abs(u - W // 2)) // 2) % 3 == 0
    elif name == 'dragon':
        cell_u, cell_v = u % 4, v % 3
        m = (cell_v == 2) & (cell_u != 0) | ((cell_v == 1) & ((cell_u == 0) | (cell_u == 3)))
        m &= ((v // 3) % 2 == 0)
    elif name == 'flame':
        if f.side:
            hgt = 2 + (2.5 + 2.5 * np.sin(u * 1.1 + f.seed % 5) + 1.5 * np.sin(u * 2.3)).astype(int)
            m = f.vb < hgt
    elif name == 'asanoha':
        m = ((u + v) % 6 == 0) | ((u - v) % 6 == 0)
    else:
        m = (hm < 0.03)
    return m


# ------------------------------------------------------------------------------------------- material painters
def m_cloth(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat)
    info = s.info
    acc = C(mat.get('accent', '#%02x%02x%02x' % shade(mat['color'], 0.7)))
    glow = None
    # folds on skirts, robes and capes: alternating light / dark columns
    if info.get('folds') or info.get('pleats'):
        k = k * np.where(f.u % 4 == 0, 0.88, np.where(f.u % 4 == 2, 1.05, 1.0))
    # slow vertical gradient over tall faces (cloth hangs into shadow)
    if f.side and f.H >= 10 and not info.get('flat'):
        k = k * (1.03 - 0.08 * f.v / max(1, f.H - 1))
    rgb = ramp(base, quant(k))
    # pattern
    pat = mat.get('pattern')
    pm = pattern_mask(pat, f, mat) if pat else np.zeros((f.H, f.W), bool)
    if pm.any():
        rgb[pm] = ramp(acc, quant(k[pm]))
        if mat.get('pattern_glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            glow[pm, :3] = acc
            glow[pm, 3] = 255 * float(mat.get('glow_amount', 0.8))
    # trims at the hem / cuffs / top
    tr = int(mat.get('trim', 0) or 0)
    if tr and f.side and (info.get('hem', False) or info.get('trim_here')) and f.H >= tr + 2:
        band = f.vb < tr
        rgb[band] = ramp(acc, quant(k[band]))
        line = f.vb == tr
        rgb[line] = ramp(acc, 1.25)
        if info.get('hem_cut') == 'scallop':
            pass
    if mat.get('trim_top') and f.side and f.H >= 4:
        rgb[f.v < 2] = ramp(acc, 1.0)
    if mat.get('seam') and f.face == 'front' and f.W >= 5:
        cx = f.W // 2
        rgb[:, cx] = ramp(base, 0.82)
        btn = (f.v % 4 == 2)
        rgb[btn[:, cx], cx] = ramp(acc, 1.1)
    return rgb, None, glow


def m_skin(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat, 0.6)
    rgb = ramp(base, quant(k))
    glow = None
    pat = mat.get('pattern')
    if pat:
        pm = pattern_mask(pat, f, mat)
        acc = C(mat.get('accent', '#a03040'))
        rgb[pm] = acc
        if mat.get('pattern_glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            glow[pm, :3] = acc
            glow[pm, 3] = 230
    return rgb, None, glow


def along_t(f, s):
    """Position along a strand / horn / tail for each texel (0 root .. 1 tip)."""
    info = s.info
    t0, t1 = info.get('t_lo'), info.get('t_hi')
    mt0, mt1 = s.mat.get('t0'), s.mat.get('t1')
    if t0 is None:
        t0, t1 = 0.0, 1.0
        if not f.side:
            return np.full((f.H, f.W), 1.0 if f.face == 'bottom' else 0.0)
    if not f.side:
        t = t1 if f.face == 'bottom' else t0
        tt = np.full((f.H, f.W), t)
    else:
        tt = t0 + (f.v + 0.5) / f.H * (t1 - t0)
    if mt0 is not None:
        tt = mt0 + tt * ((mt1 if mt1 is not None else 1.0) - mt0)
    return tt


def m_hair(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat, 0.7)
    if f.side:
        k = k * np.where(f.u % 3 == 0, 0.88, np.where(f.u % 3 == 2, 1.05, 1.0))
    else:
        k = k * 1.04
    rgb = ramp(base, quant(k))
    tip = mat.get('tip')
    if tip:
        t = along_t(f, s)
        w = np.clip((t - 0.55) / 0.45, 0, 1)
        w = np.round(w * 3) / 3
        rgb = rgb * (1 - w[..., None]) + ramp(C(tip), quant(k))[...] * w[..., None]
    if mat.get('shine', True) and f.side and s.info.get('shine_row') is not None:
        r = int(s.info['shine_row'] * f.H)
        hl = C(mix(mat['color'], '#ffffff', 0.45))
        for x in range(f.W):
            if (x + r) % 4 != 3 and 0 <= r < f.H:
                rgb[r, x] = hl
    return rgb, None, None


def m_metal(mat, f, s, ctx):
    base = C(mat['color'])
    k = np.ones((f.H, f.W), np.float32)
    if f.face == 'bottom':
        k *= 0.7
    elif f.face == 'top':
        k *= 1.12
    if f.W >= 3 and f.H >= 3:
        k[0, :] *= 1.22
        k[:, 0] *= 1.12
        k[-1, :] *= 0.66
        k[:, -1] *= 0.78
        if f.H >= 6:
            k[-2, 1:-1] *= 0.9
    # a soft diagonal sheen across larger plates
    if f.W >= 6 and f.H >= 6 and f.side:
        d = (f.u + f.v) % (f.W + f.H)
        k = k * np.where((d >= f.W * 0.35) & (d < f.W * 0.35 + 2), 1.12, 1.0)
    rgb = ramp(base, quant(k, 0.05))
    glow = None
    acc = C(mat.get('accent', '#%02x%02x%02x' % shade(mat['color'], 0.6)))
    pat = mat.get('pattern')
    if pat:
        pm = pattern_mask(pat, f, mat)
        rgb[pm] = ramp(acc, quant(k[pm]))
        if mat.get('pattern_glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            glow[pm, :3] = acc
            glow[pm, 3] = 255 * float(mat.get('glow_amount', 0.8))
    if mat.get('rivets') and f.W >= 5 and f.H >= 5:
        for (y, x) in ((1, 1), (1, f.W - 2), (f.H - 2, 1), (f.H - 2, f.W - 2)):
            rgb[y, x] = ramp(base, 1.35)
            if y + 1 < f.H:
                rgb[y + 1, x] = ramp(base, 0.62)
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
    base = C(mat['color'])
    W, H = f.W, f.H
    k = np.where(f.u * H < (W - f.v) * W * 0.9, 1.18, 0.82).astype(np.float32) if W > 1 and H > 1 else np.ones((H, W), np.float32)
    if f.face == 'bottom':
        k *= 0.75
    if W >= 3 and H >= 3:
        k[-1, :] *= 0.8
        k[:, -1] *= 0.85
    rgb = ramp(base, quant(k, 0.06))
    if W >= 2 and H >= 2:
        rgb[min(1, H - 1), min(1, W - 1)] = C(mix(mat['color'], '#ffffff', 0.85))
    glow = None
    if mat.get('glow', True):
        glow = np.zeros((H, W, 4), np.float32)
        glow[..., :3] = rgb
        glow[..., 3] = 255 * float(mat.get('glow_amount', 0.55))
    return rgb, None, glow


def m_horn(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat, 0.8)
    t = along_t(f, s)
    if f.side:
        k = k * np.where(f.v % 3 == 2, 0.86, 1.0)
    rgb = ramp(base, quant(k))
    glow = None
    tip = mat.get('tip')
    if tip:
        w = np.clip((t - 0.5) / 0.5, 0, 1)
        w = np.round(w * 3) / 3
        rgb = rgb * (1 - w[..., None]) + ramp(C(tip), quant(k)) * w[..., None]
        if mat.get('glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            gm = w > 0.5
            glow[gm, :3] = C(tip)
            glow[gm, 3] = 255 * np.clip(w[gm], 0, 1)
    return rgb, None, glow


def m_scale(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat, 0.7)
    cu = (f.u + (f.v // 3) % 2 * 2) % 4
    cv = f.v % 3
    k = k * np.where(cv == 2, 0.8, np.where((cv == 0) & (cu == 1), 1.15, 1.0))
    k = k * np.where((cu == 0) & (cv == 1), 0.88, 1.0)
    rgb = ramp(base, quant(k))
    glow = None
    pat = mat.get('pattern')
    if pat:
        pm = pattern_mask(pat, f, mat)
        acc = C(mat.get('accent', '#ffffff'))
        rgb[pm] = acc
        if mat.get('pattern_glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            glow[pm, :3] = acc
            glow[pm, 3] = 230
    return rgb, None, glow


def m_fur(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat, 0.6)
    hm = hashmap(f.H, f.W, f.seed)
    streak = ((f.u + (f.v // 2)) % 3 == 0) & (hm < 0.7)
    k = k * np.where(streak, 0.86, np.where(hm > 0.9, 1.08, 1.0))
    rgb = ramp(base, quant(k))
    tip = mat.get('tip')
    if tip and f.side:
        tipz = f.vb < max(1, f.H // 4)
        rgb[tipz] = ramp(C(tip), quant(k[tipz]))
    return rgb, None, None


def m_feather(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat, 0.7)
    k = k * np.where((f.u + f.v) % 3 == 0, 0.9, 1.0)
    rgb = ramp(base, quant(k))
    tip = mat.get('tip')
    glow = None
    if tip and f.side:
        tz = f.vb < max(1, f.H // 3)
        rgb[tz] = ramp(C(tip), quant(k[tz]))
        if mat.get('glow'):
            glow = np.zeros((f.H, f.W, 4), np.float32)
            glow[tz, :3] = C(tip)
            glow[tz, 3] = 200
    return rgb, None, glow


def m_membrane(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat, 0.6) * 0.95
    vein = ((f.u + f.v // 2) % 7 == 0)
    rgb = ramp(base, quant(k))
    glow = None
    acc = mat.get('accent')
    if acc:
        rgb[vein] = C(acc)
        glow = np.zeros((f.H, f.W, 4), np.float32)
        glow[vein, :3] = C(acc)
        glow[vein, 3] = 140
    else:
        rgb[vein] = ramp(base, 0.75)
    return rgb, None, glow


def m_energy(mat, f, s, ctx):
    base = C(mat['color'])
    k = np.ones((f.H, f.W), np.float32) * 1.05
    if f.W >= 3 and f.H >= 3:
        k[0, :] = k[-1, :] = 0.88
        k[:, 0] = k[:, -1] = 0.88
    rgb = ramp(base, k)
    core = ((f.u == f.W // 2) | (f.v == f.H // 2)) & (f.W >= 3) & (f.H >= 3)
    rgb[core] = C(mix(mat['color'], '#ffffff', 0.55))
    glow = np.zeros((f.H, f.W, 4), np.float32)
    glow[..., :3] = rgb
    glow[..., 3] = 255 * float(mat.get('glow_amount', 0.9))
    a = None
    if mat.get('alpha') is not None:
        a0 = mat['alpha'] / 255.0 if mat['alpha'] > 1 else mat['alpha']
        a = np.full((f.H, f.W), a0, np.float32)
    return rgb, a, glow


def m_ring(mat, f, s, ctx):
    base = C(mat['color'])
    rgb = np.tile(base, (f.H, f.W, 1)).astype(np.float32)
    if f.H >= 3 and f.side:
        rgb[f.H // 2] = C(mix(mat['color'], '#ffffff', 0.6))
        rgb[0] = ramp(base, 0.85)
        rgb[-1] = ramp(base, 0.85)
    glow = np.zeros((f.H, f.W, 4), np.float32)
    glow[..., :3] = rgb
    glow[..., 3] = 255
    return rgb, None, glow


def m_void(mat, f, s, ctx):
    base = C(shade(mat['color'], 0.3) if lum(mat['color']) > 0.25 else mat['color'])
    rgb = ramp(base, quant(edge_k(f, mat, 0.5)))
    hm = hashmap(f.H, f.W, f.seed)
    sp = hm < 0.04
    rgb[sp] = C(mix(mat['color'], '#ffffff', 0.6))
    glow = np.zeros((f.H, f.W, 4), np.float32)
    glow[sp, :3] = rgb[sp]
    glow[sp, 3] = 255
    return rgb, None, glow


def m_wood(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat, 0.7)
    if f.side:
        g = (f.u + (np.sin(f.v * 0.5 + f.seed % 5) * 1.2).astype(int)) % 4
        k = k * np.where(g == 0, 0.86, np.where(g == 2, 1.06, 1.0))
    else:
        r = np.hypot(f.u - f.W / 2, f.v - f.H / 2).astype(int)
        k = k * np.where(r % 2 == 0, 0.9, 1.04)
    rgb = ramp(base, quant(k))
    return rgb, None, None


def m_leaf(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat, 0.7)
    cell = ((f.u // 3) + (f.v // 3)) % 2
    k = k * np.where(cell == 0, 1.0, 0.9)
    k = k * np.where((f.u % 3 == 1) & (f.v % 3 == 1), 1.15, 1.0)
    rgb = ramp(base, quant(k))
    glow = None
    fl = mat.get('flowers')
    if fl:
        hm = hashmap(f.H, f.W, f.seed)
        cols = fl if isinstance(fl, (list, tuple)) else [fl]
        for i, c in enumerate(cols):
            m = (hm >= 0.03 * i) & (hm < 0.03 * (i + 1))
            rgb[m] = C(c)
            if mat.get('flower_glow'):
                glow = glow if glow is not None else np.zeros((f.H, f.W, 4), np.float32)
                glow[m, :3] = C(c)
                glow[m, 3] = 220
    return rgb, None, glow


def m_rock(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat, 0.9)
    hm = hashmap(max(1, f.H // 2 + 1), max(1, f.W // 2 + 1), f.seed)
    blk = hm[(f.v // 2), (f.u // 2)]
    k = k * np.where(blk < 0.25, 0.88, np.where(blk > 0.8, 1.08, 1.0))
    rgb = ramp(base, quant(k))
    glow = None
    pm = pattern_mask('cracks', f, mat)
    acc = mat.get('accent')
    if acc and mat.get('pattern_glow'):
        rgb[pm] = C(acc)
        glow = np.zeros((f.H, f.W, 4), np.float32)
        glow[pm, :3] = C(acc)
        glow[pm, 3] = 230
    else:
        rgb[pm] = ramp(base, 0.7)
    top = mat.get('top')
    if top and f.face == 'top':
        rgb[:] = ramp(C(top), quant(edge_k(f, mat, 0.5)))
    elif top and f.side and f.H >= 4:
        rgb[f.v < 2] = ramp(C(top), 1.0)
    return rgb, None, glow


def m_rainbow(mat, f, s, ctx):
    import colorsys
    P = ctx['P']
    hue = ((P[..., 1] * 0.06 + P[..., 0] * 0.03) % 1.0)
    hue = np.round(hue * 8) / 8
    rgb = np.zeros((f.H, f.W, 3), np.float32)
    for hv in np.unique(hue):
        r, g, b = colorsys.hsv_to_rgb(float(hv), 0.55, 1.0)
        rgb[hue == hv] = (r * 255, g * 255, b * 255)
    rgb = ramp(rgb, quant(edge_k(f, mat, 0.5))[..., None][..., 0])
    glow = np.zeros((f.H, f.W, 4), np.float32)
    glow[..., :3] = rgb
    glow[..., 3] = 200
    return rgb, None, glow


def m_slime(mat, f, s, ctx):
    base = C(mat['color'])
    k = edge_k(f, mat, 0.5)
    rgb = ramp(base, quant(k))
    if f.W >= 3 and f.H >= 3:
        rgb[1, 1] = C('#ffffff')
    a0 = mat.get('alpha', 190)
    a0 = a0 / 255.0 if a0 > 1 else a0
    glow = np.zeros((f.H, f.W, 4), np.float32)
    glow[..., :3] = rgb
    glow[..., 3] = 90
    return rgb, np.full((f.H, f.W), a0, np.float32), glow


def m_oilslick(mat, f, s, ctx):
    base = C(mat['color'])
    P = ctx['P']
    k = edge_k(f, mat, 0.6)
    rgb = ramp(base, quant(k))
    band = ((P[..., 1] * 0.7 + P[..., 0] * 0.35 + P[..., 2] * 0.3) % 9.0)
    hues = mat.get('hues') or ['#7a3ad0', '#2ab0c0']
    for i, c in enumerate(hues[:2]):
        m = (band >= i * 4.5) & (band < i * 4.5 + 0.5)
        rgb[m] = rgb[m] * 0.6 + C(c) * 0.4
    return rgb, None, None


def m_fallback(mat, f, s, ctx):
    """Exotic box painters of paint.py at one texel per pixel, scaled up (decals, fins, planes, eyes, teeth...)."""
    import paint as PT
    wpx, hpx = s.info.get('px', (f.W / f.td, f.H / f.td))
    w1, h1 = max(1, int(round(wpx))), max(1, int(round(hpx)))
    fn = PT.PAINTERS.get(mat['type'], PT.PAINTERS.get('simple'))
    rgb, alpha, g = fn(mat, f.face, w1, h1, s.info.get('cube'), np.random.default_rng(f.seed))
    yi = np.minimum((np.arange(f.H) * h1 / f.H).astype(int), h1 - 1)
    xi = np.minimum((np.arange(f.W) * w1 / f.W).astype(int), w1 - 1)
    rgb = np.asarray(rgb, np.float32)[yi][:, xi]
    # strip the vanilla-style jitter: snap to the 4 most common colours of the face
    rgb = posterize(rgb)
    alpha = None if alpha is None else np.asarray(alpha, np.float32)[yi][:, xi]
    if g is not None:
        g = np.asarray(g, np.float32)[yi][:, xi]
    if mat.get('glow') is True and g is None:
        g = np.zeros((f.H, f.W, 4), np.float32)
        g[..., :3] = rgb
        g[..., 3] = 255
    return rgb, alpha, g


def posterize(rgb, n=6):
    q = (np.round(rgb / 12) * 12).reshape(-1, 3)
    cols, inv, cnt = np.unique(q, axis=0, return_inverse=True, return_counts=True)
    if len(cols) <= n:
        return q.reshape(rgb.shape)
    keep = cols[np.argsort(-cnt)[:n]]
    d = ((q[:, None, :] - keep[None, :, :]) ** 2).sum(-1)
    return keep[np.argmin(d, 1)].reshape(rgb.shape)


# ------------------------------------------------------------------------------------------- head / hair shell
def m_head(mat, f, s, ctx):
    spec = mat.get('face', {})
    skin, hair, build = mat['color'], mat.get('hair', '#3a2a24'), mat.get('build', 'woman')
    bangs = mat.get('bangs', 'bangs')
    if f.face == 'front':
        rgb, glow = MF.face(spec, skin, hair, build, bangs)
    else:
        rgb, glow = MF.head_side(f.face, skin, hair), None
    return fit(rgb, f), None, (fit(glow, f) if glow is not None else None)


def m_blink(mat, f, s, ctx):
    spec = mat.get('face', {})
    rgba = MF.lids(spec, mat['color'], mat.get('hair', '#3a2a24'), mat.get('build', 'woman'))
    rgba = fit(rgba, f)
    return rgba[..., :3], rgba[..., 3] / 255.0, None


def m_hair_shell(mat, f, s, ctx):
    rgba = MF.shell(f.face, mat['color'], mat.get('bangs', 'bangs'), mat.get('long', True), mat.get('back', True),
                    mat.get('ears_open', False), mat.get('man', False), mat.get('shine', True), mat.get('tip_shell'))
    rgba = fit(rgba, f)
    return rgba[..., :3], rgba[..., 3] / 255.0, None


def fit(img, f):
    if img is None:
        return None
    h, w = img.shape[:2]
    if (h, w) == (f.H, f.W):
        return img.astype(np.float32)
    yi = np.minimum((np.arange(f.H) * h / f.H).astype(int), h - 1)
    xi = np.minimum((np.arange(f.W) * w / f.W).astype(int), w - 1)
    return img[yi][:, xi].astype(np.float32)


PAINTERS = {
    'cloth': m_cloth, 'skin': m_skin, 'hair': m_hair, 'metal': m_metal, 'gem': m_gem, 'horn': m_horn, 'scale': m_scale,
    'fur': m_fur, 'feather': m_feather, 'membrane': m_membrane, 'energy': m_energy, 'ring': m_ring, 'void': m_void,
    'wood': m_wood, 'wood2': m_wood, 'leaf': m_leaf, 'leaf2': m_leaf, 'rock': m_rock, 'rainbow': m_rainbow, 'slime': m_slime,
    'oilslick': m_oilslick, 'head': m_head, 'blink': m_blink, 'hair_shell': m_hair_shell, 'simple': m_skin, 'bone': m_skin,
}


def paint_surf(s, ctx):
    mat = s.mat or {'type': 'simple', 'color': '#888888'}
    if s.kind == 'relief' and 'rgba' in s.info:
        rgba = s.info['rgba'].astype(np.float32)
        glow = None
        gsrc = s.info.get('glowsrc')
        if gsrc is not None and s.info.get('emis') is not None and s.info['emis'].any():
            glow = np.zeros(rgba.shape[:2] + (4,), np.float32)
            em = s.info['emis']
            glow[em, :3] = rgba[em, :3]
            glow[em, 3] = 255
        return rgba[..., :3], rgba[..., 3] / 255.0, glow
    f = F(s, ctx)
    fn = PAINTERS.get(mat.get('type'), m_fallback)
    rgb, alpha, glow = fn(mat, f, s, ctx)
    rgb = np.asarray(rgb, np.float32)
    rgb, alpha = details(rgb, alpha, f, s, ctx)
    # contact shadow from the volumetric occlusion, in two crisp steps
    if s.info.get('ao', True) and mat.get('type') not in ('head', 'blink', 'hair_shell', 'energy', 'ring') and ctx.get('ao') is not None:
        a = ctx['ao']
        k = np.where(a < 0.62, 0.8, np.where(a < 0.8, 0.9, 1.0)).astype(np.float32)
        rgb = ramp(rgb, k)
    if mat.get('glow') is True and glow is None and mat.get('type') not in ('gem', 'horn', 'feather'):
        glow = np.zeros((f.H, f.W, 4), np.float32)
        glow[..., :3] = rgb
        glow[..., 3] = 255 * float(mat.get('glow_amount', 1.0))
    if mat.get('alpha') is not None and mat.get('type') not in ('slime', 'energy'):
        a0 = mat['alpha'] / 255.0 if mat['alpha'] > 1 else mat['alpha']
        alpha = (np.ones((f.H, f.W), np.float32) if alpha is None else alpha) * a0
    return rgb, alpha, glow


# ------------------------------------------------------------------------------------------- garment details
def details(rgb, alpha, f, s, ctx):
    info, mat = s.info, s.mat or {}
    P, Nn = ctx['P'], ctx['N']
    frontal = float(np.mean(Nn[..., 2])) < -0.7
    if info.get('torso') and frontal:
        x, y = P[..., 0], P[..., 1]
        top = info['neck_top']
        skin = C(info.get('skin', '#f0d0c0'))
        neck = info.get('neckline')
        if info.get('kimono'):
            acc = C(mat.get('accent', '#%02x%02x%02x' % shade(mat['color'], 0.7)))
            under = C(mix(mat.get('accent', '#ffffff'), '#ffffff', 0.6))
            Hc = max(1.0, info['waist'] - top)
            t = np.clip((y - top) / Hc, 0, 1)
            cw = info.get('chest_w', 7.0)
            xo = cw * 0.24 - t * (cw * 0.24 + 0.6)          # over band (wearer's left panel), runs to the viewer's left
            xu = -cw * 0.24 + t * (cw * 0.24 + 0.6)
            vee = (x > xu) & (x < xo)
            rgb[vee] = ramp(under, 1.0)
            rgb[vee & (y < top + 1.3) & (np.abs(x) < 0.9)] = skin
            bu = np.abs(x - xu) < 0.55
            bo = np.abs(x - xo) < 0.55
            rgb[bu & (x <= (xo + xu) / 2 + 0.6)] = ramp(acc, 0.9)
            rgb[bo] = ramp(acc, 1.05)
            edge = np.abs(x - xo - 0.55) < 0.26
            rgb[edge & (x > xu)] = ramp(acc, 0.7)
        elif neck == 'v':
            d = 2.6
            w = 1.7 * (1 - (y - top) / d)
            m = (np.abs(x) < w) & (y >= top - 1)
            rgb[m] = skin
            rim = (np.abs(np.abs(x) - w) < 0.3) & (y < top + d) & ~m
            rgb[rim] = ramp(C(mat['color']), 0.75)
        elif neck == 'round':
            m = (x / 1.8) ** 2 + ((y - top + 0.2) / 1.1) ** 2 < 1
            rgb[m] = skin
    if info.get('jacket') and f.face == 'front':
        x, y = P[..., 0], P[..., 1]
        a = np.ones((f.H, f.W), np.float32) if alpha is None else alpha
        a = np.where(np.abs(x) < 0.95, 0.0, a)
        alpha = a
    if mat.get('_hood_front'):
        x, y = P[..., 0], P[..., 1]
        a = np.ones((f.H, f.W), np.float32) if alpha is None else alpha
        ymin = y.min()
        a = np.where((np.abs(x) < 3.9) & (y > ymin + 1.0), 0.0, a)
        alpha = a
    if info.get('hem_cut') == 'jag' and f.side and f.H >= 4:
        a = np.ones((f.H, f.W), np.float32) if alpha is None else alpha
        depth = np.array([0, 1, 2, 1, 0, 1, 3, 1, 0, 2, 1, 0])[f.u % 12]
        a = np.where(f.vb < depth, 0.0, a)
        alpha = a
    if info.get('hem_cut') == 'scallop' and f.side and f.H >= 4:
        a = np.ones((f.H, f.W), np.float32) if alpha is None else alpha
        cut = (f.vb == 0) & ((f.u % 4 == 0) | (f.u % 4 == 3)) | ((f.vb == 1) & (f.u % 4 == 0))
        a = np.where(cut, 0.0, a)
        alpha = a
    if info.get('inside'):
        rgb = ramp(rgb, 0.8)
    return rgb, alpha

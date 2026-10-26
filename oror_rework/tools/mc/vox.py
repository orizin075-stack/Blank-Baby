"""Pixel-art painter for the design-sheet characters: each part is painted the way a Blockbench artist paints from
concept art, not sampled from it.

A material is a dict for V(...):
  color         base colour
  var           how much single blocks of texels vary in brightness (the sheets' soft voxel look); 0 = flat
  strands       hair: every texel column its own shade, lighter tips (tip colour) at the lower end
  scales        overlapping scale rows (tails, dragon hide); feathers: long vanes with a quill line
  bands         [(axis, lo, hi, colour)]: stripes in model space, axis x/y/z (e.g. a hem: ('y', 14, 16, navy))
  edges         [(edge, texels, colour)]: borders on the face's own edges: bottom, top, left, right, sides, all
  motifs        [(sprite, (x, y, z), scale, {key: colour})]: small pixel sprites stamped on whatever face lies there
  glow          True, or a list of colours whose texels glow
Model coordinates: x to the character's left, y down (ground at 24), z backwards. Faces are seen from outside."""
import math, zlib
import numpy as np
from colors import hexc

FACE = {'north': 'front', 'south': 'back', 'east': 'left', 'west': 'right', 'up': 'top', 'down': 'bottom'}


def C(c):
    return np.array(hexc(c), np.float32) if isinstance(c, str) else np.asarray(c, np.float32)


def V(color, **kw):
    return dict(type='vox', color=color, **kw)


def _h(*a):
    return zlib.crc32('/'.join(str(x) for x in a).encode())


# ------------------------------------------------------------------------------------------- sprites
# '.' is transparent; other characters are keys into the motif's colour map (defaults below)
SPRITES = {
    'crest': ['.ggg.', 'gnnng', 'gngng', 'gnnng', '.ggg.'],
    'kamon': ['..g..', '.gng.', 'gnnng', '.gng.', '..g..'],
    'plus': ['.gg.', 'gnng', 'gnng', '.gg.'],
    'buckle': ['gggg', 'g..g', 'gggg'],
    'bow': ['w...w', 'ww.ww', 'wwgww', 'ww.ww', 'w...w'],
    'crest7': ['..ggg..', '.gnnng.', 'gnngnng', 'gngggng', 'gnngnng', '.gnnng.', '..ggg..'],
    'cross': ['.g.', 'ggg', '.g.', '.g.'],
    'cross5': ['..g..', '..g..', 'ggggg', '..g..', '..g..', '..g..', '..g..'],
    'cross_gem': ['..g..', '..g..', 'ggegg', '..g..', '..g..', '..g..'],
    'star': ['..g..', '..g..', 'ggggg', '..g..', '..g..'],
    'star4': ['...g...', '...g...', '..ggg..', 'ggggggg', '..ggg..', '...g...', '...g...'],
    'diamond': ['.g.', 'geg', '.g.'],
    'square': ['ggg', 'gng', 'ggg'],
    'flower': ['.w.', 'wyw', '.w.'],
    'rune': ['gg.', 'g.g', 'gg.', 'g..'],
    'moon': ['.gg', 'g..', 'g..', '.gg'],
    'dot': ['g'],
    'knot': ['g.g', '.g.', 'g.g'],
    'eye': ['.www.', 'wpppw', 'wpkpw', 'wpppw', '.www.'],
    'sun': ['g.g.g', '.ggg.', 'ggegg', '.ggg.', 'g.g.g'],
    'heart': ['r.r', 'rrr', '.r.'],
    'spade': ['.k.', 'kkk', '.k.'],
}
SPRITE_KEYS = {'g': '#e3b94c', 'n': '#26305c', 'e': '#7fe4ff', 'w': '#f6f4f0', 'y': '#ffd54a', 'p': '#8a3cc8', 'k': '#141418',
               'r': '#c83a48'}


# ------------------------------------------------------------------------------------------- the painter
def frame(P, N):
    """Unit right / down vectors of a face as seen from outside (texel grid of P)."""
    n = N.reshape(-1, 3).mean(0)
    n /= max(1e-9, np.linalg.norm(n))
    down = np.array([0.0, 1.0, 0.0])
    if abs(n[1]) > 0.8:                       # top or bottom: 'down' runs towards the front of the model
        down = np.array([0.0, 0.0, -1.0]) if n[1] < 0 else np.array([0.0, 0.0, 1.0])
    dv = down - n * np.dot(down, n)
    dv /= max(1e-9, np.linalg.norm(dv))
    du = np.cross(n, dv)
    return n, du, dv


def stamp(rgb, P, N, motif, td):
    name, at, scale, cmap = (list(motif) + [None, None])[:4]
    spr = SPRITES[name] if isinstance(name, str) else name
    scale = scale or 0.5
    cmap = dict(SPRITE_KEYS, **(cmap or {}))
    n, du, dv = frame(P, N)
    c = np.asarray(at, float)
    # the motif belongs to this face when its centre lies on (or just under) the face's plane
    d0 = float(np.dot(P.reshape(-1, 3).mean(0) - c, n))
    if abs(d0) > max(1.2, scale * 2):
        return
    H, W = len(spr), len(spr[0])
    d = P - c
    a = d @ du / scale + W / 2.0
    b = d @ dv / scale + H / 2.0
    ia, ib = np.floor(a).astype(int), np.floor(b).astype(int)
    inside = (ia >= 0) & (ia < W) & (ib >= 0) & (ib < H)
    if not inside.any():
        return
    for y, x in zip(*np.nonzero(inside)):
        ch = spr[ib[y, x]][ia[y, x]]
        if ch != '.':
            rgb[y, x] = C(cmap[ch])


def paint(s, ctx):
    mat = s.mat or V('#888888')
    P, N = ctx['P'], ctx['N']
    H, W = P.shape[:2]
    face = FACE.get(s.info.get('face'), s.info.get('face', 'front'))
    seed = _h(s.bone.name, s.name, face, s.info.get('seg', 0))
    rng = np.random.default_rng(seed)
    base = C(mat['color'])
    rgb = np.tile(base, (H, W, 1))
    k = np.ones((H, W), np.float32)
    u = np.arange(W)[None, :] * np.ones((H, 1), int)
    v = np.arange(H)[:, None] * np.ones((1, W), int)
    # soft voxel blocks: a few discrete brightness steps, in blocks of `block` texels
    var = mat.get('var', 0.035)
    if var:
        bs = mat.get('block', 2)
        lv = np.array([-1.0, 0.0, 0.0, 0.0, 1.0, 0.5, -0.5], np.float32) * var
        g = rng.integers(0, len(lv), ((H + bs - 1) // bs, (W + bs - 1) // bs))
        k *= 1.0 + lv[g][:H // bs + 1][np.minimum(v // bs, g.shape[0] - 1), np.minimum(u // bs, g.shape[1] - 1)]
    if mat.get('strands'):
        # hair: each column of texels is a strand with its own shade; a darker parting line now and then
        col = rng.choice(np.array([0.84, 0.92, 0.97, 1.0, 1.05], np.float32), W)
        parting = rng.random(W) < 0.14
        col[parting] *= 0.86
        k = np.tile(col, (H, 1)) * (k if face in ('top', 'bottom') else 1.0)
        if face == 'top':
            k = (1.0 + (k - 1.0) * 0.5)
        tip = mat.get('tip')
        if tip and face not in ('top', 'bottom') and H >= 4:
            ylen = np.maximum(1, (H * rng.uniform(0.08, 0.22, W)).astype(int))
            m = (H - 1 - v) < ylen[None, :]
            rgb[m] = C(tip)
    if mat.get('scales') and face != 'bottom':
        sc = int(mat.get('scale_px', 3))
        row = v // sc
        off = (row % 2) * (sc // 2 + 1)
        cu = (u + off) % (sc + 1)
        rim = ((v % sc) == sc - 1) | (cu == 0)
        k = np.where(rim, k * mat.get('scale_rim', 0.82), k * (1.0 + 0.05 * ((v % sc) == 0)))
    if mat.get('feathers') and face not in ('top', 'bottom'):
        fw = int(mat.get('feather_px', 4))
        cu = u % fw
        k = np.where(cu == 0, k * 0.78, k)
        k = np.where(cu == fw // 2, k * 1.06, k)
        tipv = (H - 1 - v) < (2 + (u // fw) % 3)
        if mat.get('tip'):
            rgb[tipv] = C(mat['tip'])
    # face light: tops a little brighter, undersides darker; a one-texel darker bottom edge on side panels
    if face == 'top':
        k *= 1.06
    elif face == 'bottom':
        k *= 0.78
    elif mat.get('panel', True) and H >= 4 and not mat.get('strands'):
        k[-1, :] *= 0.86
    rgb = rgb * k[..., None]
    # bands in model space
    for b in mat.get('bands', ()):
        axis, lo, hi, colour = b[:4]
        ai = 'xyz'.index(axis)
        m = (P[..., ai] >= lo) & (P[..., ai] < hi)
        if m.any():
            if isinstance(colour, (list, tuple)):
                cyc = np.array([C(c) for c in colour])
                bw = max(1, int(b[4]) if len(b) > 4 else 3)
                rgb[m] = cyc[((u // bw) % len(cyc))[m]] * k[m][:, None]
            else:
                rgb[m] = C(colour) * k[m][:, None]
    # borders on the face's own edges (in texels)
    for e in mat.get('edges', ()):
        edge, w, colour = e[:3]
        only = e[3] if len(e) > 3 else None
        if only and face not in only:
            continue
        m = np.zeros((H, W), bool)
        if edge in ('bottom', 'all', 'hem'):
            m |= v >= H - w
        if edge in ('top', 'all'):
            m |= v < w
        if edge in ('left', 'sides', 'all'):
            m |= u < w
        if edge in ('right', 'sides', 'all'):
            m |= u >= W - w
        if face in ('top', 'bottom') and edge in ('bottom', 'hem', 'top'):
            m &= False
        if isinstance(colour, (list, tuple)):
            # a band of blocks cycling through the colours, `w` texels square
            cyc = np.array([C(c) for c in colour])
            idx = ((u // max(1, w)) % len(cyc))
            rgb[m] = cyc[idx[m]] * k[m][:, None]
        else:
            rgb[m] = C(colour) * k[m][:, None]
    for mo in mat.get('motifs', ()):
        stamp(rgb, P, N, mo, ctx.get('td', 2))
    glow = None
    gl = mat.get('glow')
    if gl:
        glow = np.zeros((H, W, 4), np.float32)
        if gl is True:
            m = np.ones((H, W), bool)
        else:
            m = np.zeros((H, W), bool)
            for gc in gl:
                m |= (np.abs(rgb - C(gc)[None, None] * k[..., None]).max(-1) < 30) | (np.abs(rgb - C(gc)).max(-1) < 2)
        glow[m, :3] = rgb[m]
        glow[m, 3] = 255
    return np.clip(rgb, 0, 255), (None if mat.get('alpha') is None else np.full((H, W), mat['alpha'], np.float32)), glow

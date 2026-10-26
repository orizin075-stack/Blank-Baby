"""Faces and hair for the design-sheet characters, drawn the way the sheets draw them: a 32x32 face (an 8-pixel head
at four texels a pixel) with big block eyes low on the face: a thick dark lash line, a dark iris rim, a bright iris
with a coloured accent at the bottom and a white catchlight; a fringe of hair strands down to the eyes, a small mouth.

face(spec) -> rgb (32, 32, 3), glow (32, 32, 4)
spec keys:
  skin, hair, hair_dark, hair_light       colours (hair_dark / light default from hair)
  lash                                    lash line colour (default: very dark from the iris)
  iris, iris_dark, iris_light, accent     iris colours; accent: the fleck at the bottom (gold for Kokuhaku)
  iris_r                                  the other eye's iris (heterochromia; accent_r, iris_dark_r ...)
  eye   'round' | 'sharp' | 'sleepy' | 'big' | 'closed' | 'wide'
  pupil None | 'slit' | 'star' | 'cross' | 'ring'
  fringe  'straight' | 'parted' | 'side' | 'spiky' | 'short' | 'none'
  fringe_depth  how far the fringe comes down (rows of 32), default 17
  mouth 'small' | 'smile' | 'grin' | 'open' | 'fang' | 'frown' | 'cat'
  blush True; marks [(kind, colour)] ('scar_r', 'tear_l', 'tattoo')
  glow_eyes True: the irises glow
  skin_shadow  colour of shading on the skin under the fringe
"""
import numpy as np
from colors import hexc, mix, shade, lum

N = 32


def C(c):
    return np.array(hexc(c), np.float32)


def _mix(a, b, t):
    return '#%02x%02x%02x' % tuple(int(round(x)) for x in (C(a) * (1 - t) + C(b) * t))


def hair_tones(spec):
    h = spec['hair']
    L = lum(h)
    dark = spec.get('hair_dark') or (_mix(h, '#5a5f8a', 0.38) if L > 0.7 else _mix(h, '#000000', 0.42))
    light = spec.get('hair_light') or (_mix(h, '#ffffff', 0.55) if L < 0.85 else '#ffffff')
    mid = spec.get('hair_mid') or _mix(h, dark, 0.35)
    return C(h), C(mid), C(dark), C(light)


def strands(H, W, spec, seed, shine_row=None, tip=None):
    """Hair texels: columns of strands 2-3 texels wide, each its own tone, a dark line between some, a shine band."""
    base, mid, dark, light = hair_tones(spec)
    rng = np.random.default_rng(seed)
    out = np.zeros((H, W, 3), np.float32)
    x = 0
    while x < W:
        w = int(rng.integers(2, 4))
        tone = [base, base, mid, base, light * 0.25 + base * 0.75][int(rng.integers(0, 5))]
        out[:, x:x + w] = tone
        if rng.random() < 0.45 and x + w < W:
            out[:, x + w - 1] = mid
        if rng.random() < 0.18:
            out[:, x] = dark * 0.5 + mid * 0.5
        # strands end at different heights in a darker tip
        x += w
    if shine_row is not None:
        r = shine_row
        for c in range(W):
            if rng.random() < 0.7:
                out[r:r + 2, c] = light
    if tip is not None:
        T = C(tip)
        L = rng.integers(2, 6, W)
        for c in range(W):
            out[H - L[c]:, c] = T * 0.7 + out[H - L[c]:, c] * 0.3
    return out


def fringe_profile(style, depth, seed):
    rng = np.random.default_rng(seed)
    d = np.full(N, depth, float)
    if style == 'none':
        return np.full(N, 3)
    if style == 'short':
        d[:] = depth - 6
    # strand tips: points every 3-4 texels, alternately long and short
    x = 0
    while x < N:
        w = int(rng.integers(3, 5))
        L = depth + rng.integers(-3, 2)
        for i in range(w):
            if x + i < N:
                d[x + i] = L - abs(i - (w - 1) / 2) * 1.2
        x += w
    if style == 'parted':
        for c in range(N):
            d[c] -= max(0, 6 - abs(c - 15.5) * 1.1)
    elif style == 'side':
        d -= np.linspace(0, 6, N)
    elif style == 'spiky':
        d[::4] += 2
    # long strands at the sides frame the face, and one or two fall between the eyes
    d[:3] = N
    d[-3:] = N
    d[3] = max(d[3], depth + 6)
    d[-4] = max(d[-4], depth + 6)
    if style in ('straight', 'spiky'):
        d[14:16] = depth + 4
    return np.clip(d, 0, N).astype(int)


EYE_TPL = {
    # rows of the eye from the lash down; L lash, l lash wing, D iris rim, I iris, J iris light, A accent, H highlight,
    # W white, . skin
    'round': ['LLLLLLLL', 'LDDDDDDl', 'WDHHIIDW', 'WDHIIIDW', 'WDIJJIDW', 'WDJAAJD.', '.DDAADD.'],
    'big':   ['LLLLLLLL', 'LDDDDDDL', 'DHHIIIID', 'DHIIIIID', 'DIIJJIID', 'DIJAAJID', 'DDJAAJDD', '.DDDDDD.'],
    'sharp': ['.LLLLLLL', 'LLDDDDDL', 'LDHIIIDW', 'WDIIJIDW', '.DJAAJD.', '..DDDD..'],
    'sleepy': ['........', 'LLLLLLLL', 'LDDDDDDl', 'WDHIIIDW', 'WDIJAJDW', '.DDDDDD.'],
    'wide':  ['.LLLLLL.', 'LDDDDDDL', 'DHHIIIID', 'DHIIIIID', 'DIIJJIID', 'DIJAAJID', '.DDDDDD.'],
    'closed': ['........', '........', 'LLLLLLLL', '.LLLLLL.', '........'],
    'void':  ['LLLLLLLL', 'LDDDDDDL', 'DDDDDDDD', 'DDDHHDDD', 'DDDDDDDD', '.DDDDDD.'],
}


def face(spec):
    skin = C(spec['skin'])
    sk_light = C(_mix(spec['skin'], '#ffffff', 0.35))
    sk_sh = C(spec.get('skin_shadow') or _mix(spec['skin'], '#b06a78', 0.22))
    sk_sh2 = C(_mix(spec['skin'], '#7a4458', 0.35))
    rgb = np.tile(skin, (N, N, 1))
    glow = np.zeros((N, N, 4), np.float32)
    # soft light from above: forehead a touch lighter, sides and jaw a step darker
    rgb[8:16, 4:28] = skin * 0.5 + sk_light * 0.5
    rgb[:, :2] = sk_sh
    rgb[:, -2:] = sk_sh
    rgb[-2:, :] = sk_sh
    rgb[-1, :] = sk_sh2
    if spec.get('blush'):
        bl = C(spec.get('blush_colour', '#f2a0a8'))
        for x0 in (5, 21):
            rgb[26:28, x0:x0 + 6] = rgb[26:28, x0:x0 + 6] * 0.45 + bl * 0.55
    # eyes
    style = spec.get('eye', 'round')
    tpl = EYE_TPL.get(style, EYE_TPL['round'])
    ey = spec.get('eye_row', 18)
    for side in (0, 1):
        sfx = '' if side == 0 else '_r'
        iris = spec.get('iris' + sfx) or spec['iris']
        pal = {
            'L': C(spec.get('lash') or _mix(spec.get('iris_dark' + sfx) or iris, '#0a0814', 0.72)),
            'l': C(spec.get('lash') or _mix(spec.get('iris_dark' + sfx) or iris, '#0a0814', 0.72)),
            'D': C(spec.get('iris_dark' + sfx) or spec.get('iris_dark') or _mix(iris, '#0c0a1c', 0.55)),
            'I': C(iris),
            'J': C(spec.get('iris_light' + sfx) or spec.get('iris_light') or _mix(iris, '#ffffff', 0.35)),
            'A': C(spec.get('accent' + sfx) or spec.get('accent') or _mix(iris, '#ffffff', 0.55)),
            'H': C('#ffffff'),
            'W': C(spec.get('sclera', '#f6f4fa')),
        }
        x0 = 4 if side == 0 else 20
        for r, line in enumerate(tpl):
            for c, code in enumerate(line):
                if code == '.':
                    continue
                cx = x0 + (c if side == 0 else 7 - c)
                y = ey + r
                if 0 <= y < N and 0 <= cx < N:
                    rgb[y, cx] = pal[code]
                    if spec.get('glow_eyes') and code in 'IJAH':
                        glow[y, cx, :3] = pal[code]
                        glow[y, cx, 3] = 255
        pup = spec.get('pupil')
        if pup and style not in ('closed',):
            pc = C(spec.get('pupil_colour', '#0a0610'))
            cx = x0 + 3
            if pup == 'slit':
                rgb[ey + 2:ey + 6, cx:cx + 2] = pc
            elif pup == 'star':
                rgb[ey + 3, cx - 1:cx + 3] = C('#ffffff')
                rgb[ey + 2:ey + 5, cx:cx + 2] = C('#ffffff')
            elif pup == 'cross':
                rgb[ey + 3, cx - 1:cx + 3] = pc
                rgb[ey + 2:ey + 6, cx:cx + 2] = pc
            elif pup == 'ring':
                rgb[ey + 2:ey + 6, cx - 1] = pc
                rgb[ey + 2:ey + 6, cx + 2] = pc
    # mouth
    m = spec.get('mouth', 'small')
    mc = C(spec.get('mouth_colour') or _mix(spec['skin'], '#6a2c3c', 0.55))
    my = spec.get('mouth_row', 27)
    if m == 'small':
        rgb[my, 15:17] = mc
    elif m == 'smile':
        rgb[my, 14:18] = mc
        rgb[my - 1, 13] = mc
        rgb[my - 1, 18] = mc
    elif m == 'grin':
        rgb[my - 1, 13:19] = mc
        rgb[my, 14:18] = C('#ffffff')
        rgb[my + 1, 14:18] = mc
    elif m == 'open':
        rgb[my - 1:my + 1, 15:17] = mc
    elif m == 'fang':
        rgb[my, 14:18] = mc
        rgb[my + 1, 16] = C('#ffffff')
    elif m == 'frown':
        rgb[my, 14:18] = mc
        rgb[my + 1, 13] = mc
        rgb[my + 1, 18] = mc
    elif m == 'cat':
        rgb[my, 13] = rgb[my, 18] = mc
        rgb[my + 1, 14:16] = mc
        rgb[my + 1, 16:18] = mc
    for kind, col in spec.get('marks', ()):
        cc = C(col)
        if kind == 'scar_r':
            for i in range(8):
                rgb[14 + i, 7 + (i % 2)] = cc
        elif kind == 'tear_l':
            rgb[25:28, 25] = cc
        elif kind == 'tattoo':
            rgb[24:26, 2:4] = cc
            rgb[24:26, 28:30] = cc
        elif kind == 'cheek_r':
            rgb[24:27, 3:6] = cc
    # fringe over the top of the face
    d = fringe_profile(spec.get('fringe', 'straight'), spec.get('fringe_depth', 17), spec.get('seed', 5))
    hr = strands(N, N, spec, spec.get('seed', 5) + 1, shine_row=4)
    _, mid, dark, _ = hair_tones(spec)
    for x in range(N):
        rgb[:d[x], x] = hr[:d[x], x]
        if d[x] < N:
            rgb[d[x], x] = sk_sh                     # shadow under the fringe
            if d[x] + 1 < N and (rgb[d[x] + 1, x] == skin).all():
                rgb[d[x] + 1, x] = skin * 0.6 + sk_sh * 0.4
        if 0 < d[x] <= N:
            rgb[d[x] - 1, x] = mid
    return rgb, glow


def head_side(face_name, spec, seed=0):
    """Sides, back and top of the head: hair all over (the sheets' heads show no skin but the face)."""
    hr = strands(N, N, spec, seed + {'left': 3, 'right': 4, 'back': 5, 'top': 6, 'bottom': 7}.get(face_name, 0),
                 shine_row=(5 if face_name != 'top' else None), tip=spec.get('tip'))
    if face_name == 'bottom':
        hr[:] = C(spec['skin']) * 0.8
    return hr


def lids(spec):
    """Closed eyelids for the blink layer, rgba."""
    out = np.zeros((N, N, 4), np.float32)
    skin = C(spec['skin'])
    lash = C(spec.get('lash') or _mix(spec.get('iris_dark') or spec['iris'], '#0a0814', 0.72))
    ey = spec.get('eye_row', 18)
    for x0 in (4, 20):
        out[ey:ey + 5, x0:x0 + 8, :3] = skin
        out[ey:ey + 5, x0:x0 + 8, 3] = 255
        out[ey + 4, x0:x0 + 8, :3] = lash
    d = fringe_profile(spec.get('fringe', 'straight'), spec.get('fringe_depth', 17), spec.get('seed', 5))
    for x in range(N):
        out[:d[x], x, 3] = 0
    return out


# ------------------------------------------------------------------------------------------- painters for bake
def m_sface(mat, f, s, ctx):
    spec = mat['spec']
    if f.face == 'front':
        rgb, glow = face(spec)
    else:
        rgb, glow = head_side(f.face, spec), None
    return _fit(rgb, f), None, (_fit(glow, f) if glow is not None else None)


def m_slids(mat, f, s, ctx):
    rgba = _fit(lids(mat['spec']), f)
    return rgba[..., :3], rgba[..., 3] / 255.0, None


def _fit(img, f):
    h, w = img.shape[:2]
    if (h, w) == (f.H, f.W):
        return img.astype(np.float32)
    yi = np.minimum((np.arange(f.H) * h / f.H).astype(int), h - 1)
    xi = np.minimum((np.arange(f.W) * w / f.W).astype(int), w - 1)
    return img[yi][:, xi].astype(np.float32)




def shell(face_name, spec, seed=0):
    """The hair volume round the head (inflated box), rgba: open over the face except the side strands."""
    a = np.zeros((N, N), np.float32)
    rng = np.random.default_rng(seed + 31)
    if face_name == 'top':
        a[:] = 1
    elif face_name == 'bottom':
        return np.zeros((N, N, 4), np.float32)
    elif face_name == 'front':
        d = fringe_profile(spec.get('fringe', 'straight'), spec.get('fringe_depth', 17), spec.get('seed', 5))
        for x in range(N):
            a[:max(0, d[x] - 3), x] = 1
        side = spec.get('side_len', N)
        a[:side, :3] = 1
        a[:side, -3:] = 1
    elif face_name == 'back':
        a[:] = 1
        if spec.get('short_back'):
            for x in range(N):
                a[22 + int(rng.integers(0, 6)):, x] = 0
    else:
        L = spec.get('side_len', N)
        for x in range(N):
            a[:L - int(rng.integers(0, 3)), x] = 1
        if spec.get('ears_open'):
            front_first = face_name == 'left'
            cols = range(10, 18)
            for x in cols:
                xx = x if front_first else N - 1 - x
                a[14:24, xx] = 0
    rgb = strands(N, N, spec, seed + {'front': 11, 'back': 12, 'left': 13, 'right': 14, 'top': 15}[face_name],
                  shine_row=(6 if face_name not in ('top',) else None), tip=(spec.get('tip') if face_name != 'top' else None))
    out = np.zeros((N, N, 4), np.float32)
    out[..., :3] = rgb
    out[..., 3] = a * 255
    return out


def m_sshell(mat, f, s, ctx):
    rgba = _fit(shell(f.face, mat['spec']), f)
    return rgba[..., :3], rgba[..., 3] / 255.0, None


def enable():
    import bbpaint
    bbpaint.PAINTERS['sface'] = m_sface
    bbpaint.PAINTERS['slids'] = m_slids
    bbpaint.PAINTERS['sshell'] = m_sshell
    bbpaint.NO_SNAP = tuple(set(bbpaint.NO_SNAP) | {'sface', 'slids', 'sshell'})

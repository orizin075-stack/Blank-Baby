"""16x16 anime pixel faces and hair for an 8x8x8 head painted at 2 texels per pixel (the 'HD skin' look of
Yes Steve Model / Touhou Little Maid characters): hair frames the face, large eyes with a lash line, iris
gradient, pupil and catchlight, thin brows, a tiny nose and mouth. Never realistic.

Eye templates are written for the viewer-left eye (outer column first) and mirrored for the other eye.
Codes: L lash, W white, w white shade, D iris dark, I iris, J iris light, P pupil, H catchlight,
       B brow, S skin shadow, . nothing."""
import numpy as np
from colors import hexc, mix, shade, lum

N = 16

# 5 columns: column 0 is just outside the eye's outer corner (the lash flick), columns 1-4 the eye.
# The catchlight is not part of the template: it is put on the same side of both irises (light from one
# direction), so the eyes never look crossed.
EYES = {
    'girl':    ['.LLLL', 'LLDDD', '.WIPI', '.WIPJ', '..JJJ'],
    'big':     ['.LLLL', 'LDDDD', '.IIPI', '.JIPI', '..JJJ'],
    'calm':    ['.....', 'LLLLL', '.WDPD', '.WIPI', '..JJJ'],
    'sharp':   ['LLL..', '.LLLL', '.WDPD', '.WIPJ', '..JJ.'],
    'fierce':  ['LLL..', '.LLLL', '.WDPD', '.WIPJ', '..JJ.'],
    'sad':     ['..LLL', '.LLDD', '.WIPI', '.WIPJ', '..JJJ'],
    'slit':    ['.LLLL', 'LLDPD', '.IIPI', '.JIPJ', '..JJJ'],
    'closed':  ['.....', '.....', '..LL.', '.L..L', '.....'],
    'lowered': ['.....', '.....', 'LLLLL', '.WDPD', '..JJJ'],
    'void':    ['.LLLL', 'LPPPP', '.PPKP', '.PPPP', '..PPP'],
    'man':        ['.LLLL', '.WDPD', '..III'],
    'man_calm':   ['.LLLL', '.WDPD', '..JJJ'],
    'man_sharp':  ['LLL..', '.LLLL', '.WDPD'],
    'man_slit':   ['.LLLL', '.WIPI', '..JPJ'],
    'man_closed': ['.....', '.LLLL', '.....'],
    'man_void':   ['.LLLL', '.PPKP', '..PPP'],
    'man_sad':    ['..LLL', '.LLDD', '.WIPI'],
}

EYESETS = {
    'lash': None,     # filled below with EYES
    # big glossy iris, no white: the common look of anime HD skins
    'iris': {
        'girl':    ['.LLLL', '.DDDD', '.IIII', '.IJJI', '..JJ.'],
        'big':     ['.LLLL', '.DDDD', '.IIII', '.IJJI', '.JJJJ'],
        'calm':    ['.....', '.LLLL', '.DDDD', '.IJJI', '..JJ.'],
        'sharp':   ['LL...', '.LLLL', '.DDDD', '.IJJI', '..II.'],
        'fierce':  ['LL...', '.LLLL', '.DDDD', '.IJJI', '..II.'],
        'sad':     ['...LL', '.LLLL', '.DDDD', '.IJJI', '..JJ.'],
        'slit':    ['.LLLL', '.DDPD', '.IIPI', '.IJPJ', '..JJ.'],
        'closed':  ['.....', '.....', '.L..L', '..LL.', '.....'],
        'lowered': ['.....', '.....', '.LLLL', '.DDDD', '..JJ.'],
        'void':    ['.LLLL', '.PPPP', '.PPKP', '.PPPP', '..PP.'],
        'man':        ['.LLLL', '.DDDD', '.IJJI'],
        'man_calm':   ['.LLLL', '.DDDD', '.IJJI'],
        'man_sharp':  ['LL...', '.LLLL', '.DJJD'],
        'man_slit':   ['.LLLL', '.DDPD', '.IJPJ'],
        'man_closed': ['.....', '.LLLL', '.....'],
        'man_void':   ['.LLLL', '.PPKP', '..PP.'],
        'man_sad':    ['...LL', '.LLLL', '.DJJD'],
    },
    # large anime eyes (5 x 6), dark-over-light iris, square catchlight, no white: baby-face proportions
    'anime': {
        'girl':    ['LLLLL', 'DDDDD', 'IIIII', 'IIIII', 'IJJJI', '.JJJ.'],
        'big':     ['LLLLL', 'DDDDD', 'IIIII', 'IIIII', 'IJJJI', '.JJJ.'],
        'calm':    ['.....', 'LLLLL', 'DDDDD', 'IIIII', 'IJJJI', '.JJJ.'],
        'sharp':   ['LL...', '.LLLL', 'DDDDD', 'IIIII', 'IJJJI', '.JJJ.'],
        'fierce':  ['LL...', '.LLLL', 'DDDDD', 'IIIII', 'IJJJI', '.JJJ.'],
        'sad':     ['...LL', 'LLLL.', 'DDDDD', 'IIIII', 'IJJJI', '.JJJ.'],
        'slit':    ['LLLLL', 'DDPDD', 'DIPID', 'IIPII', 'IJPJI', '.JJJ.'],
        'closed':  ['.....', '.....', '.....', 'L...L', '.LLL.', '.....'],
        'lowered': ['.....', '.....', 'LLLLL', 'DDDDD', 'IJJJI', '.JJJ.'],
        'void':    ['LLLLL', 'PPPPP', 'PPKPP', 'PPPPP', 'PPPPP', '.PPP.'],
        'man':        ['LLLLL', 'DDDDD', 'IIIII', '.JJJ.'],
        'man_calm':   ['LLLLL', 'DDDDD', 'IIIII', '.JJJ.'],
        'man_sharp':  ['LL...', '.LLLL', 'DDDDD', 'IJJJI'],
        'man_slit':   ['LLLLL', 'DDPDD', 'IIPII', '.JPJ.'],
        'man_closed': ['.....', 'LLLLL', '.....', '.....'],
        'man_void':   ['LLLLL', 'PPKPP', 'PPPPP', '.PPP.'],
        'man_sad':    ['...LL', 'LLLL.', 'DDDDD', 'IJJJI'],
    },
    # Touhou Little Maid at twice the resolution: white outer half, dark-over-light iris, no lash line
    'tlm': {
        'girl':    ['.WWDD', '.WWDD', '.WWII', '.WWJJ'],
        'big':     ['.WDDD', '.WDDD', '.WIII', '.WJJJ'],
        'calm':    ['.....', '.DDDD', '.WWII', '.WWJJ'],
        'sharp':   ['.DD..', '.WDDD', '.WWII', '.WWJJ'],
        'fierce':  ['.DD..', '.WDDD', '.WWII', '.WWJJ'],
        'sad':     ['...DD', '.WDDD', '.WWII', '.WWJJ'],
        'slit':    ['.DDPD', '.IIPI', '.IJPJ', '.JJPJ'],
        'closed':  ['.....', '.....', '.DDDD', '.....'],
        'lowered': ['.....', '.....', '.DDDD', '.WWJJ'],
        'void':    ['.PPPP', '.PPKP', '.PPPP', '.PPPP'],
        'man':        ['.DDDD', '.WWII', '.WWJJ'],
        'man_calm':   ['.DDDD', '.WWII', '.WWJJ'],
        'man_sharp':  ['.DD..', '.WDDD', '.WWII'],
        'man_slit':   ['.DDPD', '.IIPI', '.JJPJ'],
        'man_closed': ['.....', '.DDDD', '.....'],
        'man_void':   ['.PPKP', '.PPPP', '.PPPP'],
        'man_sad':    ['...DD', '.WDDD', '.WWII'],
    },
}
VARIANT = 'lash'
SKIN_SAT = 0.13
AUTO_BLUSH = False

STYLE = {
    'woman': {'normal': 'girl', 'big': 'big', 'glint': 'girl', 'calm': 'calm', 'sharp': 'sharp', 'fierce': 'fierce', 'sad': 'sad',
              'slit': 'slit', 'closed': 'closed', 'lowered': 'lowered', 'void': 'void'},
    'man':   {'normal': 'man', 'big': 'man', 'glint': 'man', 'calm': 'man_calm', 'sharp': 'man_sharp', 'fierce': 'man_sharp',
              'sad': 'man_sad', 'slit': 'man_slit', 'closed': 'man_closed', 'lowered': 'man_calm', 'void': 'man_void'},
    'child': {'normal': 'big', 'big': 'big', 'glint': 'big', 'calm': 'calm', 'sharp': 'sharp', 'fierce': 'fierce', 'sad': 'sad',
              'slit': 'slit', 'closed': 'closed', 'lowered': 'lowered', 'void': 'void'},
}
STYLE['youth'] = dict(STYLE['woman'])
STYLE['large'] = STYLE['man']

# brows: (row offset from the eye's top row, template columns), thin and hair-coloured
BROWS = {
    'normal': [(-2, (2, 3, 4))],
    'big':    [(-2, (2, 3, 4))],
    'calm':   [(-1, (1, 2, 3, 4))],
    'sharp':  [(-2, (1, 2)), (-1, (3, 4))],
    'fierce': [(-2, (1, 2)), (-1, (3, 4))],
    'sad':    [(-1, (1, 2)), (-2, (3, 4))],
    'slit':   [(-2, (2, 3, 4))],
    'man':    [(-2, (1, 2, 3, 4))],
    'man_sharp': [(-2, (1, 2, 3)), (-1, (4,))],
    'none':   [],
}

# mouths: (row relative to the mouth row, col, code): m lip line, M mouth dark, T teeth, R tongue
MOUTHS = {
    'none':  [],
    'small': [(0, 7, 'm'), (0, 8, 'm')],
    'soft':  [(0, 7, 'm'), (0, 8, 'm')],
    'smile': [(-1, 6, 'm'), (0, 7, 'm'), (0, 8, 'm'), (-1, 9, 'm')],
    'open':  [(0, 7, 'M'), (0, 8, 'M'), (1, 7, 'R'), (1, 8, 'R')],
    'grin':  [(-1, 6, 'm'), (0, 7, 'T'), (0, 8, 'T'), (-1, 9, 'm')],
    'fang':  [(0, 7, 'm'), (0, 8, 'm'), (1, 8, 'T')],
    'frown': [(0, 6, 'm'), (-1, 7, 'm'), (-1, 8, 'm'), (0, 9, 'm')],
    'flat':  [(0, 7, 'm'), (0, 8, 'm')],
    'cat':   [(-1, 6, 'm'), (0, 7, 'm'), (-1, 8, 'm'), (0, 9, 'm')],
    'smirk': [(0, 7, 'm'), (0, 8, 'm'), (-1, 9, 'm')],
}

# bangs: per column, how many rows of the hair-shell front are hair (0 = open)
BANGS = {
    'bangs':  [7, 6, 5, 6, 5, 4, 5, 6, 6, 5, 4, 5, 6, 5, 6, 7],
    'blunt':  [7, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7],
    'parted': [7, 7, 6, 6, 5, 5, 4, 2, 2, 4, 5, 5, 6, 6, 7, 7],
    'swept':  [7, 7, 6, 6, 6, 5, 5, 5, 4, 4, 4, 3, 3, 3, 2, 3],
    'messy':  [7, 6, 4, 6, 5, 6, 4, 5, 6, 4, 5, 6, 4, 6, 5, 7],
    'short':  [5, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 3, 4, 4, 5],
    'slick':  [3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3],
    'open':   [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    'none':   [0] * 16,
}


def C(c):
    return np.array(hexc(c), np.float32)


def resolve(build, spec):
    req = spec.get('style', 'normal')
    if spec.get('closed'):
        req = 'closed'
    table = STYLE.get(build, STYLE['woman'])
    return table.get(req, table['normal'])


LAYOUT = {   # eye top row, nose row (None = no nose), mouth base row
    'woman': (8, None, 14), 'youth': (8, None, 14), 'child': (8, None, 14), 'man': (9, 12, 14), 'large': (9, 12, 14)}


def eye_rows(build, style):
    tpl = (EYESETS.get(VARIANT) or EYES)[style]
    top = LAYOUT.get(build, LAYOUT['woman'])[0]
    if VARIANT == 'anime':
        top = 8 if build in ('man', 'large') else 7
    return top, tpl


def warm(skin):
    """Skin that stays warm and clear after Minecraft's entity shading (pale greys read as dead)."""
    import colorsys
    r, g, b = [v / 255 for v in hexc(skin)]
    h, sat, v = colorsys.rgb_to_hsv(r, g, b)
    human = h < 0.13 or h > 0.93
    if not human:
        return skin                         # lavender, grey, green skins of monsters stay as designed
    if v > 0.55:
        d = ((0.055 - h + 0.5) % 1) - 0.5
        h = h + max(-0.03, min(0.03, d))
        sat = min(0.32, max(sat, SKIN_SAT))
        v = min(1.0, v * 1.01 + 0.01)
    else:
        sat = max(sat, 0.3)
    r, g, b = colorsys.hsv_to_rgb(h % 1, sat, v)
    return '#%02x%02x%02x' % (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


def palette(spec, skin, hair, build, right=False):
    iris = spec.get('iris', '#6a4a3a')
    if right and spec.get('heterochromia'):
        iris = spec['heterochromia']
    iris2 = spec.get('iris2') or ('#%02x%02x%02x' % shade(iris, 1.3))
    lash = spec.get('line') or ('#%02x%02x%02x' % mix(shade(hair, 0.35), '#1c1222', 0.75))
    brow = '#%02x%02x%02x' % mix(shade(hair, 0.6 if lum(hair) > 0.45 else 0.85), skin, 0.18)
    return {
        'L': C(lash),
        'W': C('#f6f6fb'),
        'D': C(shade(iris, 0.62)),
        'I': C(iris),
        'J': C(mix(shade(iris, 1.3), iris2, 0.25) if VARIANT == 'anime' else mix(iris, iris2, 0.45)),
        'P': C(mix(shade(iris, 0.25), '#100818', 0.6)),
        'K': C(mix(iris2, '#ffffff', 0.3)),
        'H': C('#ffffff'),
        'B': C(brow),
        'S': C(shade(skin, 0.88)),
        'm': C(mix(shade(skin, 0.72), '#c85a6a', 0.3)),
        'M': C('#7a3444'),
        'T': C('#fbf8f4'),
        'R': C('#e07a88'),
    }


def hair_tone(hair, H, W, rows=None, top_light=True):
    """Hair base with strand columns and gentle top-down shading."""
    base = C(hair)
    v = np.arange(H)[:, None] / max(1, H - 1)
    u = np.arange(W)[None, :]
    k = np.where(u % 3 == 0, 0.88, np.where(u % 3 == 2, 1.05, 1.0)) * np.ones((H, 1))
    if top_light:
        k = k * (1.06 - 0.16 * v)
    return ramp(base, k)


def ramp(rgb, k):
    """rgb * k with cool shadows and warm lights (pixel-art hue shift)."""
    rgb = np.asarray(rgb, np.float32)
    k = np.asarray(k, np.float32)
    if k.ndim:
        k = k[..., None]
    dark = rgb * k + np.clip(1 - k, 0, None) * np.array([-12, -6, 16], np.float32)
    light = rgb + (255 - rgb) * np.clip(k - 1, 0, None) * 0.9 + np.clip(k - 1, 0, None) * np.array([8, 5, -8], np.float32)
    return np.clip(np.where(k < 1, dark, light), 0, 255)


def shine(rgb, hair, rows, W, every=4, phase=0):
    """Angel-ring highlight: a broken light band."""
    hl = C(mix(hair, '#ffffff', 0.45 if lum(hair) < 0.6 else 0.6))
    for r in rows:
        if 0 <= r < rgb.shape[0]:
            for x in range(W):
                if (x + phase + r) % every != every - 1:
                    rgb[r, x] = (rgb[r, x] + hl) / 2 if r != rows[0] else hl
    return rgb


def eye_cells(build, spec):
    """[(row, col, code, side)] of both eyes on the 16x16 face; side 0 = viewer-left eye."""
    style = resolve(build, spec)
    top, tpl = eye_rows(build, style)
    out = []
    for side in (0, 1):
        for r, line in enumerate(tpl):
            for c, code in enumerate(line):
                if code == '.':
                    continue
                x = 2 + c if side == 0 else 13 - c
                out.append((top + r, x, code, side))
    return out, top, tpl, style


def face(spec, skin, hair, build='woman', bangs='bangs'):
    """Front of the head (16x16): rgb, glow (rgba) or None."""
    skin = warm(skin)
    pals = (palette(spec, skin, hair, build), palette(spec, skin, hair, build, right=True))
    sk = C(skin)
    rgb = np.tile(sk, (N, N, 1))
    cov = BANGS.get(bangs, BANGS['bangs'])
    hr = hair_tone(hair, N, N)
    for x in range(N):
        h = max(2, min(cov[x], 6) - 1)
        rgb[:h, x] = hr[:h, x] * 0.85
    for x in range(N):
        h = cov[x]
        if 0 < h < N:
            rgb[h, x] = ramp(sk, 0.88)
    rgb[N - 1, 2:N - 2] = ramp(sk, 0.95)
    glow = np.zeros((N, N, 4), np.float32)
    cells, top, tpl, style = eye_cells(build, spec)
    if spec.get('veil'):
        return veil_face(rgb, spec, skin, hair, build, top, glow)
    glow_eyes = bool(spec.get('glow_eyes'))
    crushed = bool(spec.get('scar'))
    # brows first (the eye may overlap them), only where the fringe leaves the forehead open
    man = build in ('man', 'large')
    st = spec.get('style', spec.get('eye_tpl', 'normal'))
    if spec.get('brows', man):          # women and children: brows hidden under the fringe, as in anime skins
        bkey = ('man_sharp' if st in ('sharp', 'fierce') else 'man') if man else (st if st in BROWS else 'normal')
        rows_ = BROWS[bkey]
        for side in (0, 1):
            for dy, cols in rows_:
                y = top + dy
                for c in cols:
                    x = 2 + c if side == 0 else 13 - c
                    if 0 <= y < N and y >= cov[x]:
                        rgb[y, x] = pals[side]['B']
    iris_cols = {0: [], 1: []}
    for y, x, code, side in cells:
        if side == 0 and crushed:
            continue
        pal = pals[side]
        rgb[y, x] = pal[code]
        if code in 'DIJ' and y == top + (1 if tpl[1].strip('.') and 'L' not in tpl[1][1:] else 2):
            iris_cols[side].append(x)
        if glow_eyes and code in 'IJDK':
            glow[y, x, :3] = pal[code]
            glow[y, x, 3] = 255 if code != 'D' else 160
    # catchlight: the same side (viewer-left) of both irises, on the iris' top row
    catch = {'lash': 1, 'iris': 2, 'tlm': 0, 'anime': 3}.get(VARIANT, 1)
    if catch and style not in ('closed', 'man_closed', 'void', 'man_void'):
        for side in (0, 1):
            if side == 0 and crushed:
                continue
            irow = [(y, x) for y, x, code, sd in cells if sd == side and code in 'DI']
            if not irow:
                continue
            y0 = min(y for y, x in irow)
            xs = [x for y, x in irow if y == y0]
            hx = min(xs)
            if catch == 3:
                big = len(tpl) >= 5 and style not in ('calm', 'lowered', 'sharp', 'fierce', 'sad')
                for dy in range(2 if big else 1):
                    for dx in range(2 if big else 1):
                        rgb[y0 + dy, hx + dx] = pals[side]['H']
                        if glow_eyes:
                            glow[y0 + dy, hx + dx, :3] = C('#ffffff')
                            glow[y0 + dy, hx + dx, 3] = 255
                ys = [y for y, x, code, sd in cells if sd == side and code == 'J']
                if ys:
                    y1 = max(ys) - 1
                    xr = max(x for y, x, code, sd in cells if sd == side and code in 'IJ' and y == y1)
                    rgb[y1, xr] = C(mix('#ffffff', spec.get('iris', '#888888'), 0.35))
                continue
            for dy in range(catch if len(tpl) >= 4 else 1):
                rgb[y0 + dy, hx] = pals[side]['H']
                if glow_eyes:
                    glow[y0 + dy, hx, :3] = C('#ffffff')
                    glow[y0 + dy, hx, 3] = 255
            if catch == 2 and len(tpl) >= 4:
                ys = [y for y, x, code, sd in cells if sd == side and code == 'J']
                if ys:
                    y1 = max(ys)
                    xr = max(x for y, x, code, sd in cells if sd == side and code in 'IJ' and y == y1 - 1)
                    rgb[y1 - 1, xr] = C(mix('#ffffff', spec.get('iris', '#888888'), 0.3))
            elif style in ('big',):
                y1 = max(y for y, x, code, sd in cells if sd == side and code in 'IJ')
                xr = max(x for y, x, code, sd in cells if sd == side and code in 'IJ' and y == y1)
                rgb[y1 - 1, xr] = C(mix('#ffffff', spec.get('iris', '#888888'), 0.25))
    if crushed:
        sc = C(mix(shade(skin, 0.62), '#8a2020', 0.4))
        for i in range(8):
            y, x = top - 3 + i, 2 + i // 2
            if 0 <= y < N and y >= cov[x]:
                rgb[y, x] = sc
        for c in range(1, 5):
            rgb[top + 1, 2 + c] = pals[0]['L']
    # Like hand-made anime skins (Touhou Little Maid / Yes Steve Model packs): no nose and no mouth. The eyes
    # carry the expression; drawn mouths read as wounds at this size.
    if spec.get('draw_mouth'):
        _, ny, mr = LAYOUT.get(build, LAYOUT['woman'])
        for r, c, code in MOUTHS.get(spec.get('mouth', 'small'), MOUTHS['small']):
            rgb[min(N - 1, mr + r), c] = pals[0][code]
    eb = top + len(tpl)
    if spec.get('blush') or (AUTO_BLUSH and not man and not spec.get('veil')):
        bl = C(mix(skin, '#ff7088', 0.32))
        for x in (2, 3, 12, 13):
            rgb[min(N - 2, eb), x] = bl
    marks = spec.get('marks')
    if marks:
        if isinstance(marks, (list, tuple)) and 'forehead' in marks:
            mc = C(spec.get('iris2') or spec.get('iris', '#ffffff'))
            for y, x in ((top - 3, 7), (top - 3, 8), (top - 4, 7), (top - 2, 8)):
                if y >= 0:
                    rgb[y, x] = mc
                    glow[y, x, :3] = mc
                    glow[y, x, 3] = 255
        else:
            mc = C(marks if isinstance(marks, str) else '#a03040')
            for x in (1, 14):
                for dy in range(2):
                    y = min(N - 2, eb - 1 + dy)
                    rgb[y, x] = mc
                    glow[y, x, :3] = mc
                    glow[y, x, 3] = 200
    gl = spec.get('glasses')
    if gl:
        gc = C(gl)
        y0, y1 = top - 1, min(N - 2, top + len(tpl))
        for x0 in (2, 9):
            for x in range(x0, x0 + 5):
                rgb[y0, x] = gc
                rgb[y1, x] = gc
            for y in range(y0, y1 + 1):
                rgb[y, x0] = gc
                rgb[y, x0 + 4] = gc
        rgb[top, 7:9] = gc
    mono = spec.get('monocle')
    if mono:
        gc = C(mono)
        y0, y1 = top - 1, min(N - 2, top + len(tpl))
        x0 = 9
        for x in range(x0, x0 + 5):
            rgb[y0, x] = gc
            rgb[y1, x] = gc
        for y in range(y0, N):
            if y <= y1:
                rgb[y, x0] = gc
            rgb[y, x0 + 4] = gc
    return rgb, (glow if glow[..., 3].any() else None)


def veil_face(rgb, spec, skin, hair, build, top, glow):
    vc = C(spec['veil'])
    ey = C(spec.get('veil_eyes', '#ffcf6a'))
    for y in range(4, N):
        for x in range(N):
            k = 0.9 if (x % 4 == 0) else (1.04 if x % 4 == 2 else 1.0)
            k *= 1.0 - 0.012 * (y - 4)
            rgb[y, x] = ramp(vc, k)
    rgb[4, :] = ramp(vc, 1.12)
    for x0 in (3, 9):
        for c in range(4):
            rgb[top + 2, x0 + c] = ey
            glow[top + 2, x0 + c, :3] = ey
            glow[top + 2, x0 + c, 3] = 255
    return rgb, glow


def lids(spec, skin, hair, build='woman'):
    """Blink plate: skin over the eyes with a closed lash line (rgba); transparent elsewhere."""
    rgba = np.zeros((N, N, 4), np.float32)
    cells, top, tpl, style = eye_cells(build, spec)
    if spec.get('veil') or 'closed' in style:
        return rgba
    skin = warm(skin)
    sk = C(skin)
    pal = palette(spec, skin, hair, build)
    rows = len(tpl)
    y_line = top + rows - 2 if rows >= 4 else top + rows - 1
    for y, x, code, side in cells:
        rgba[y, x, :3] = sk
        rgba[y, x, 3] = 255
    for y, x, code, side in cells:
        if y == top:
            rgba[y_line, x, :3] = pal['L']
            rgba[y_line, x, 3] = 255
    return rgba


def head_side(face_name, skin, hair, ear=True):
    skin = warm(skin)
    sk = C(skin)
    rgb = np.tile(sk, (N, N, 1))
    hr = hair_tone(hair, N, N)
    if face_name in ('top', 'back'):
        return hr * 0.9
    if face_name == 'bottom':
        return ramp(np.tile(sk, (N, N, 1)), 0.78)
    rgb[:6] = hr[:6] * 0.85
    rgb[N - 1] = ramp(sk, 0.9)
    if ear:
        # ear: a slightly darker shape in the middle of the side
        for y in range(7, 11):
            for x in range(6, 9):
                rgb[y, x] = ramp(sk, 0.9 if (y in (7, 10) or x in (6, 8)) else 0.96)
    # the half nearest the back is hair-covered
    back_cols = slice(0, 5) if face_name == 'right' else slice(N - 5, N)
    rgb[:, back_cols] = hr[:, back_cols] * 0.85
    return rgb


def shell(face_name, hair, bangs='bangs', long_sides=True, back_long=True, ears_open=False, man=False, shine_on=True, tip=None):
    """Hair shell (the 'hat layer' over the head) for one face: rgba with cut-outs."""
    a = np.zeros((N, N), np.float32)
    if face_name == 'top':
        a[:] = 1
    elif face_name == 'bottom':
        return np.zeros((N, N, 4), np.float32)
    elif face_name == 'front':
        cov = list(BANGS.get(bangs, BANGS['bangs']))
        if long_sides:
            for x, hgt in ((0, 15), (1, 13), (14, 13), (15, 15)):
                cov[x] = max(cov[x], hgt)
        else:
            for x, hgt in ((0, 9), (15, 9)):
                cov[x] = max(cov[x], hgt)
        for x in range(N):
            a[:cov[x], x] = 1
    elif face_name == 'back':
        if back_long:
            a[:] = 1
        else:
            jag = [12, 13, 12, 13, 12, 12, 13, 12, 12, 13, 12, 12, 13, 12, 13, 12] if not man else [11, 12, 11, 12, 11, 12, 11, 12] * 2
            for x in range(N):
                a[:jag[x], x] = 1
    else:
        # sides: columns run back->front on 'right', front->back on 'left'
        front_first = face_name == 'left'
        for x in range(N):
            fx = x if front_first else N - 1 - x          # 0 = front edge
            if long_sides:
                h = N
            else:
                h = 9 if fx < 6 else (12 if fx < 11 else 13)
                if man:
                    h = 7 if fx < 5 else (10 if fx < 11 else 12)
            a[:h, x] = 1
            if ears_open and 4 <= fx <= 8:
                a[7:12, x] = 0
        if long_sides and not ears_open:
            pass
    rgb = hair_tone(hair, N, N)
    if face_name == 'top':
        u = np.arange(N)
        rgb = ramp(C(hair), np.where(u % 3 == 0, 0.95, 1.08) * np.ones((N, 1)))
        rgb[:, 7:9] = ramp(C(hair), 0.9) if bangs == 'parted' else rgb[:, 7:9]
    elif shine_on and face_name in ('front', 'back', 'left', 'right'):
        rgb = shine(rgb, hair, [3, 4] if face_name != 'front' else [1, 2], N, phase=1 if face_name in ('left', 'back') else 0)
    if tip and face_name != 'top':
        tc = C(tip)
        v = np.arange(N)[:, None, None] / (N - 1)
        rgb = rgb * (1 - 0.5 * np.clip(v - 0.5, 0, 1)) + tc * 0.5 * np.clip(v - 0.5, 0, 1)
    # darken the last hair row of every column (strand tips cast a line)
    out = np.zeros((N, N, 4), np.float32)
    out[..., :3] = rgb
    out[..., 3] = a * 255
    for x in range(N):
        col = a[:, x]
        idx = np.nonzero(col)[0]
        if len(idx) and idx[-1] < N - 1 and face_name != 'top':
            out[idx[-1], x, :3] = ramp(out[idx[-1], x, :3], 0.78)
    return out

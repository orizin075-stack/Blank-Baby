"""Minecraft faces: the 8x8 vocabulary of the vanilla player skins (Steve, Alex, Ari, Efe, Kai, Makena, Noor,
Sunny, Zuri) and the illagers, one texel per pixel (doubled to the character's 2-texel density).

What the vanilla faces do, and so what these do:
  * rows 0-1 (sometimes 2) are hair; long hair also frames the face in columns 0 and 7;
  * the eyes sit on row 4: two pixels each, white on the outer side and a dark iris pixel on the inner side
    (columns 1-2 and 5-6), nothing else - no lashes, no highlights;
  * a two-pixel mouth on row 6 (columns 3-4), only a few shades darker than the skin (pinkish on Alex / Ari);
  * subtle shading: the row under the fringe, columns 0 and 7 and the chin corners a step darker;
    brows (Noor) are a step-darker skin above the eyes; illagers use a dark unibrow for a stern look;
  * cheeks (Ari) are a pinker skin step on row 5.
Character traits from the face spec map onto that grammar: iris colour, glowing eyes (like the drowned),
taller eyes for 'big', stern brows for 'fierce' / 'sharp', closed eyes, beast eyes, veils, glasses, scars."""
import numpy as np
from colors import hexc, mix, shade, lum
import bbface as BF

N8 = 8
C = BF.C
ramp = BF.ramp

# fringe on the hat layer: per column, rows covered (eyes are on row 4, so the fringe stops at row 3)
BANGS8 = {
    'bangs':  [3, 2, 3, 2, 2, 3, 2, 3],
    'blunt':  [3, 3, 3, 3, 3, 3, 3, 3],
    'parted': [3, 3, 2, 1, 1, 2, 3, 3],
    'swept':  [3, 3, 3, 3, 2, 2, 1, 2],
    'messy':  [3, 2, 3, 1, 2, 3, 2, 3],
    'short':  [2, 1, 2, 1, 1, 2, 1, 2],
    'slick':  [1, 1, 1, 1, 1, 1, 1, 1],
    'open':   [1, 0, 0, 0, 0, 0, 0, 1],
    'none':   [0] * 8,
}


def skin_tones(skin):
    s = BF.warm(skin)
    S = C(s)
    return s, {'s': S, 's1': ramp(S, 0.94), 's2': ramp(S, 0.88), 's3': ramp(S, 0.8)}


def hair_cells(hair, H, W, seed=0):
    """Vanilla hair: three close tones in a loose pattern (Alex e58d3f / eb983f / f3a858)."""
    base = C(hair)
    tones = [ramp(base, 0.9), base, ramp(base, 1.1)]
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, 3, (H, W))
    # keep the pattern calm: columns lean to one tone (strands)
    col = rng.integers(0, 3, W)
    pick = np.where(rng.random((H, W)) < 0.55, col[None, :], pick)
    out = np.zeros((H, W, 3), np.float32)
    for i in range(3):
        out[pick == i] = tones[i]
    return out


def up2(img, W=16, H=16):
    h, w = img.shape[:2]
    yi = np.minimum((np.arange(H) * h // H), h - 1)
    xi = np.minimum((np.arange(W) * w // W), w - 1)
    return img[yi][:, xi]


def face8(spec, skin, hair, build='woman', bangs='bangs'):
    skin, T = skin_tones(skin)
    man = build in ('man', 'large')
    rgb = np.tile(T['s'], (N8, N8, 1)).astype(np.float32)
    glow = np.zeros((N8, N8, 4), np.float32)
    hr = hair_cells(hair, N8, N8, seed=3)
    cov = BANGS8.get(bangs, BANGS8['bangs'])
    # hair on the face layer: rows 0-1 everywhere, and down to the fringe line
    for x in range(N8):
        h = max(2 if bangs not in ('open', 'slick', 'none') else 1, min(cov[x], 3))
        rgb[:h, x] = hr[:h, x]
    # shading: the row under the hair, the face edges, the chin corners
    for x in range(N8):
        h = max(2 if bangs not in ('open', 'slick', 'none') else 1, min(cov[x], 3))
        if h < N8:
            rgb[h, x] = T['s1']
    for y in range(4, N8):
        rgb[y, 0] = T['s1']
        rgb[y, 7] = T['s1']
    rgb[7, 0] = rgb[7, 7] = T['s2']
    rgb[7, 1] = rgb[7, 6] = T['s1']
    if spec.get('veil'):
        vc = C(spec['veil'])
        for y in range(3, N8):
            for x in range(N8):
                rgb[y, x] = ramp(vc, 1.06 if y == 3 else (0.94 if x in (0, 7) else 1.0))
        ey = C(spec.get('veil_eyes', '#ffcf6a'))
        for x in (1, 2, 5, 6):
            rgb[4, x] = ey
            glow[4, x, :3] = ey
            glow[4, x, 3] = 255
        return rgb, glow
    style = spec.get('style', spec.get('eye_tpl', 'normal'))
    if spec.get('closed'):
        style = 'closed'
    iris = spec.get('iris', '#4a3020')
    iris_r = spec.get('heterochromia') or iris
    glow_eyes = bool(spec.get('glow_eyes'))
    white = C('#ffffff')
    for side, (xo, xi), ic in ((0, (1, 2), iris), (1, (6, 5), iris_r)):
        dark = C(shade(ic, 0.62)) if not glow_eyes else C(ic)
        if style == 'closed':
            rgb[4, xo] = rgb[4, xi] = ramp(T['s'], 0.62)
            continue
        if style == 'void':
            rgb[4, xo] = C('#120c18')
            rgb[4, xi] = C(ic)
            glow[4, xi, :3] = C(ic)
            glow[4, xi, 3] = 255
            continue
        if style == 'slit':
            rgb[4, xo] = C(spec.get('iris2') or shade(ic, 1.3))
            rgb[4, xi] = C(shade(ic, 0.5))
            if glow_eyes:
                glow[4, xo, :3] = rgb[4, xo]
                glow[4, xo, 3] = 255
            continue
        rgb[4, xo] = white
        rgb[4, xi] = dark
        if glow_eyes:
            glow[4, xi, :3] = C(ic)
            glow[4, xi, 3] = 255
        if style == 'big' or (build == 'child' and style == 'normal'):
            rgb[3, xi] = C(shade(ic, 0.45))
            if glow_eyes:
                glow[3, xi, :3] = C(shade(ic, 0.8))
                glow[3, xi, 3] = 200
    # brows / lids on row 3
    browc = C(mix(shade(hair, 0.55), shade(skin, 0.6), 0.35))
    if style in ('fierce', 'sharp'):
        for x in ((1, 2, 5, 6) if man or style == 'fierce' else (2, 5)):
            rgb[3, x] = browc
    elif style in ('calm', 'lowered'):
        for x in (1, 2, 5, 6):
            rgb[3, x] = T['s2']
    elif style == 'sad':
        rgb[3, 2] = rgb[3, 5] = T['s2']
    elif man and style == 'normal':
        for x in (1, 2, 5, 6):
            rgb[3, x] = T['s1']
    # cheeks
    if spec.get('blush'):
        bl = C(mix(skin, '#ff6f7a', 0.3))
        for x in (0, 1, 6, 7):
            rgb[5, x] = bl
    marks = spec.get('marks')
    if marks:
        if isinstance(marks, (list, tuple)) and 'forehead' in marks:
            mc = C(spec.get('iris2') or spec.get('iris', '#ffffff'))
            rgb[2, 3] = rgb[2, 4] = mc
            glow[2, 3, :3] = glow[2, 4, :3] = mc
            glow[2, 3, 3] = glow[2, 4, 3] = 255
        else:
            mc = C(marks if isinstance(marks, str) else '#a03040')
            for x in (1, 6):
                rgb[5, x] = mc
                glow[5, x, :3] = mc
                glow[5, x, 3] = 200
    # mouth: two pixels a few shades darker (pinkish for women and children)
    mouth = spec.get('mouth') or 'small'
    if mouth == 'grin' and not man:
        mouth = 'smile'
    if mouth != 'none':
        if man:
            mc = ramp(T['s'], 0.72)
        else:
            mc = C(mix(shade(skin, 0.93), '#e88080', 0.2))     # Alex / Ari: barely pinker than the skin
        xs = {'smirk': (4, 5)}.get(mouth, (3, 4))
        for x in xs:
            rgb[6, x] = mc
        if mouth == 'fang':
            rgb[6, 4] = C('#fbf8f4')
        elif mouth == 'grin':
            rgb[6, 2] = rgb[6, 5] = ramp(T['s'], 0.62)
            rgb[6, 3] = rgb[6, 4] = C('#f4efe8')
        elif mouth == 'open':
            rgb[6, 3] = rgb[6, 4] = C('#7a3040')
    if spec.get('scar'):
        sc = C(mix(shade(skin, 0.7), '#8a2a2a', 0.35))
        for y, x in ((2, 2), (3, 2), (4, 1), (5, 1)):
            rgb[y, x] = sc
        rgb[4, 2] = ramp(T['s'], 0.6)
    gl = spec.get('glasses')
    if gl:
        g = C(gl)
        for x in (0, 3, 4, 7):
            rgb[4, x] = g
        for x in (1, 2, 5, 6):
            rgb[3, x] = g
    mono = spec.get('monocle')
    if mono:
        g = C(mono)
        rgb[3, 5] = rgb[3, 6] = g
        rgb[4, 7] = rgb[4, 4] = g
        rgb[5, 5] = rgb[5, 6] = g
        rgb[6, 7] = rgb[7, 7] = g
    return rgb, glow


def face(spec, skin, hair, build='woman', bangs='bangs'):
    rgb, glow = face8(spec, skin, hair, build, bangs)
    return up2(rgb), (up2(glow) if glow[..., 3].any() else None)


def lids(spec, skin, hair, build='woman'):
    rgba = np.zeros((N8, N8, 4), np.float32)
    style = spec.get('style', 'normal')
    if spec.get('veil') or style in ('closed', 'void'):
        return up2(rgba)
    skin, T = skin_tones(skin)
    for x in (1, 2, 5, 6):
        rgba[4, x, :3] = ramp(T['s'], 0.66)
        rgba[4, x, 3] = 255
        if style == 'big':
            rgba[3, x, :3] = T['s']
            rgba[3, x, 3] = 255
    return up2(rgba)


def head_side(face_name, skin, hair):
    skin, T = skin_tones(skin)
    hr = hair_cells(hair, N8, N8, seed={'top': 5, 'back': 6, 'left': 7, 'right': 8}.get(face_name, 9))
    if face_name in ('top', 'back'):
        return up2(hr)
    if face_name == 'bottom':
        return up2(np.tile(T['s2'], (N8, N8, 1)))
    rgb = np.tile(T['s'], (N8, N8, 1)).astype(np.float32)
    rgb[:2] = hr[:2]
    back = slice(0, 4) if face_name == 'right' else slice(4, 8)
    rgb[:, back] = hr[:, back]
    rgb[N8 - 1] = np.where((rgb[N8 - 1] == T['s']).all(-1)[:, None], T['s1'], rgb[N8 - 1])
    return up2(rgb)


def shell(face_name, hair, bangs='bangs', long_sides=True, back_long=True, ears_open=False, man=False, shine_on=True, tip=None):
    """Hat layer (hair volume) for one face, rgba with cut-outs, vanilla resolution."""
    a = np.zeros((N8, N8), np.float32)
    if face_name == 'top':
        a[:] = 1
    elif face_name == 'bottom':
        return up2(np.zeros((N8, N8, 4), np.float32))
    elif face_name == 'front':
        cov = list(BANGS8.get(bangs, BANGS8['bangs']))
        if long_sides:
            cov[0] = max(cov[0], 7)
            cov[7] = max(cov[7], 7)
        for x in range(N8):
            a[:cov[x], x] = 1
    elif face_name == 'back':
        if back_long:
            a[:] = 1
        else:
            jag = [6, 7, 6, 6, 7, 6, 7, 6] if not man else [5, 6, 5, 6, 5, 6, 5, 6]
            for x in range(N8):
                a[:jag[x], x] = 1
    else:
        front_first = face_name == 'left'
        for x in range(N8):
            fx = x if front_first else N8 - 1 - x
            if long_sides:
                h = N8
            else:
                h = (3 if fx < 3 else (5 if fx < 6 else 6)) if man else (4 if fx < 3 else (6 if fx < 6 else 7))
            a[:h, x] = 1
            if ears_open and 2 <= fx <= 4:
                a[3:6, x] = 0
    rgb = hair_cells(hair, N8, N8, seed={'front': 11, 'back': 12, 'left': 13, 'right': 14, 'top': 15}[face_name])
    if tip and face_name != 'top':
        tc = C(tip)
        for y in range(5, N8):
            w = (y - 4) / 4 * 0.6
            rgb[y] = rgb[y] * (1 - w) + tc * w
    out = np.zeros((N8, N8, 4), np.float32)
    out[..., :3] = rgb
    out[..., 3] = a * 255
    return up2(out)

"""Anime faces painted on the sculpted skull (8 texels per model pixel).

Features are drawn in face space: x across the face, y down, measured on the rest-pose head, so they sit
where the eyes, brows, nose and mouth of the sculpt are. Expression styles keep the names of the 8x8 faces
(face8.EYES) so recipes keep their 'style', 'mouth', 'blush', 'glow_eyes', 'heterochromia', 'marks', 'scar',
'glasses', 'monocle', 'veil', 'veil_eyes', 'mask' and 'line' keys."""
import math
import numpy as np
from colors import hexc, mix, shade
import face8

def _c(c):
    return np.array(hexc(c), np.float32)

def style_params(style):
    p = dict(lid=0.0, slant=0.0, lower=0.0, size=1.0, brow=0.0, pupil='round', lashes=1.0, closed=False, void=False)
    if style in ('big', 'child'):
        p.update(size=1.12)
    if style in ('calm', 'man_calm', 'lowered'):
        p.update(lid=0.42 if style != 'lowered' else 0.55)
    if style in ('sharp', 'man_sharp', 'fierce', 'slit'):
        p.update(slant=0.32, lower=0.12, size=0.92, brow=-0.25 if style in ('fierce', 'man_sharp') else -0.1)
    if style == 'sad':
        p.update(slant=-0.22, brow=0.3, lid=0.12)
    if style == 'slit':
        p.update(pupil='slit')
    if style in ('man', 'man_sharp', 'man_calm'):
        p.update(lashes=0.45)
    if style == 'closed':
        p.update(closed=True)
    if style == 'void':
        p.update(void=True)
    return p

def eye_masks(x, y, fi, sgn, p):
    """Eye-local coordinates and masks for the eye on side sgn (-1 = model -X)."""
    ew = fi['eye_w'] * p['size']
    eh = fi['eye_h'] * p['size']
    ex = sgn * fi['eye_dx']
    ey = fi['eye_y']
    u = (x - ex) / ew
    v = (y - ey) / eh
    o = sgn * u                                     # > 0 towards the outer corner
    # upper lid: peaks a third of the way out, drops to a winged outer corner; lower lid: shallow curve
    top = -1.0 + 0.55 * (u + 0.25 * np.sign(u) * 0) ** 2 + 0.18 * np.clip(o, 0, None) ** 2 - p['slant'] * o + p['lid'] * 1.2
    bot = 0.86 - 0.42 * u ** 2 - p['lower'] + 0.1 * o * p['slant']
    white = (np.abs(u) < 1.0) & (v > top) & (v < bot)
    return u, v, o, top, bot, white, ew, eh

def paint_face(rgb, glow, x, y, front, fi, spec, build, skin, hair):
    style = face8.resolve(build, spec)
    p = style_params(style)
    line = _c(spec.get('line', mix(hexc(hair), '#1a1420', 0.75)))
    iris_c = hexc(spec.get('iris', '#4a7ad8'))
    iris2 = hexc(spec.get('iris2', mix(iris_c, '#ffffff', 0.35)))
    het = spec.get('heterochromia')
    skin_c = _c(skin)
    shadow = _c(shade(skin, 0.86))
    glow_eyes = spec.get('glow_eyes')
    for sgn in (-1, 1):
        u, v, o, top, bot, white, ew, eh = eye_masks(x, y, fi, sgn, p)
        white &= front
        ic = hexc(het) if (het and sgn > 0) else iris_c
        ic2 = mix(ic, '#ffffff', 0.4) if (het and sgn > 0) else iris2
        # lid shadow above the lash line
        sh = front & (np.abs(u) < 1.1) & (v > top - 0.55) & (v <= top - 0.28)
        rgb[sh] = rgb[sh] * 0.6 + shadow * 0.4
        if p['closed']:
            arc = front & (np.abs(u) < 1.0) & (np.abs(v - (0.15 - 0.35 * (1 - u ** 2))) < 0.16)
            rgb[arc] = line
            continue
        if p['void']:
            rgb[white] = _c('#140c18')
            pup = white & (((u + 0.05 * sgn) / 0.22) ** 2 + ((v - 0.1) / 0.3) ** 2 < 1)
            rgb[pup] = _c(ic)
            glow[pup, :3] = _c(ic)
            glow[pup, 3] = 255
        else:
            rgb[white] = _c('#fbfbff')
            # white gets a soft shadow under the upper lid
            ws = white & (v < top + 0.35)
            rgb[ws] = _c('#d8dcea')
            u0, v0 = -0.05 * sgn, 0.08
            RU, RV = 0.5, 0.9
            ir = white & (((u - u0) / RU) ** 2 + ((v - v0) / RV) ** 2 < 1)
            w = np.clip((v - v0 + RV) / (2 * RV), 0, 1)
            dark = np.array(shade(ic, 0.42), np.float32)
            mid = np.array(hexc(ic), np.float32)
            lite = np.array(hexc(ic2), np.float32)
            col = np.where((w < 0.45)[..., None], dark + (mid - dark) * (w / 0.45)[..., None],
                           mid + (lite - mid) * ((w - 0.45) / 0.55)[..., None])
            col = np.round(col / 6) * 6
            rgb[ir] = col[ir]
            ring = ir & (((u - u0) / RU) ** 2 + ((v - v0) / RV) ** 2 > 0.7)
            rgb[ring] = rgb[ring] * 0.72
            if p['pupil'] == 'slit':
                pup = ir & (((u - u0) / 0.09) ** 2 + ((v - v0 - 0.05) / 0.72) ** 2 < 1)
            else:
                pup = ir & (((u - u0) / 0.22) ** 2 + ((v - v0 - 0.06) / 0.38) ** 2 < 1)
            rgb[pup] = np.array(mix(shade(ic, 0.25), tuple(int(c) for c in line), 0.55), np.float32)
            if glow_eyes:
                g = ir & ~pup
                glow[g, :3] = rgb[g] * 0.9
                glow[g, 3] = 255
            # catchlights: big one up and towards the light (image left), small one low on the other side
            hl = white & (((u - u0 + 0.2) / 0.2) ** 2 + ((v - v0 + 0.38) / 0.24) ** 2 < 1)
            rgb[hl] = _c('#ffffff')
            hs = white & (((u - u0 - 0.2) / 0.1) ** 2 + ((v - v0 - 0.45) / 0.11) ** 2 < 1)
            rgb[hs] = _c('#ffffff')
            if glow_eyes:
                glow[hl | hs, :3] = 255
                glow[hl | hs, 3] = 255
        # upper lash line, thicker and winged at the outer corner
        th = 0.26 * p['lashes'] + 0.12
        lash = front & (np.abs(u) < 1.08) & (v > top - th - 0.1 * np.clip(o, 0, 1)) & (v <= top + 0.06)
        wing = front & (o > 0.8) & (o < 1.3) & (np.abs(v - (top + 0.05 - 0.25 * (o - 0.8))) < 0.13 * p['lashes'] + 0.05)
        rgb[lash | wing] = line
        # lower lash, faint, outer half
        low = front & (o > -0.1) & (o < 0.95) & (np.abs(v - bot) < 0.08)
        rgb[low] = rgb[low] * 0.4 + line * 0.6
        # brow
        bu = (x - sgn * fi['eye_dx'] * 1.02) / (fi['eye_w'] * 1.2)
        bo = sgn * bu
        bv = -0.18 * (1 - bu ** 2) - p['brow'] * (-bo) * 0.18
        bw = 0.055 if not fi['man'] else 0.09
        brow = front & (np.abs(bu) < 1.0) & (np.abs((y - fi['brow_y']) / fi['hw'] * 2 - bv * 1.0) < bw * 2.2)
        rgb[brow] = np.array(mix(hexc(hair), tuple(int(c) for c in line), 0.45), np.float32)
    # nose: a soft shadow under the tip
    nose = front & (np.abs(x - 0.06) < 0.13) & (np.abs(y - fi['nose_y']) < 0.07)
    rgb[nose] = rgb[nose] * 0.55 + shadow * 0.45
    # blush
    if spec.get('blush'):
        bl = _c(spec.get('blush_color', '#ff8c9c'))
        for sgn in (-1, 1):
            m = front & (((x - sgn * fi['eye_dx'] * 1.08) / 0.42) ** 2 + ((y - fi['eye_y'] - fi['eye_h'] * 1.75) / 0.15) ** 2 < 1)
            rgb[m] = rgb[m] * 0.75 + bl * 0.25
    mouth(rgb, x, y, front, fi, face8.default_mouth(build, spec), skin)
    # marks
    marks = spec.get('marks', []) or []
    if isinstance(marks, str):
        marks = [('cheek', marks)]
    for m in marks:
        kind = m if isinstance(m, str) else m[0]
        col = _c(m[1]) if not isinstance(m, str) and len(m) > 1 else _c('#c8283c')
        if kind == 'cheek':
            for sgn in (-1, 1):
                for k in range(2):
                    mk = front & (np.abs(x - sgn * (fi['eye_dx'] * 1.15 + 0.1 * k)) < 0.06) & \
                        (np.abs(y - (fi['eye_y'] + fi['eye_h'] * 1.7 + 0.2 * k)) < 0.22)
                    rgb[mk] = col
                    glow[mk, :3] = col
                    glow[mk, 3] = 200
        elif kind == 'tear':
            for sgn in (-1, 1):
                mk = front & (((x - sgn * fi['eye_dx'] * 1.1) / 0.09) ** 2 + ((y - fi['eye_y'] - fi['eye_h'] * 1.5) / 0.14) ** 2 < 1)
                rgb[mk] = col
                glow[mk, :3] = col
                glow[mk, 3] = 220
        elif kind == 'forehead':
            mk = front & (np.abs(x) / 0.22 + np.abs(y - (fi['brow_y'] - 0.55)) / 0.32 < 1)
            rgb[mk] = col
            glow[mk, :3] = col
            glow[mk, 3] = 255
        elif kind == 'stitch':
            mk = front & (np.abs(y - (fi['mouth_y'] + 0.1) - 0.3 * (x - 0.5)) < 0.05) & (x > 0.2) & (x < 1.1)
            rgb[mk] = col
    if spec.get('scar'):
        sc = _c(mix(skin, (120, 40, 40), 0.6))
        mk = front & (np.abs(x - fi['eye_dx'] - 0.05 * (y - fi['eye_y'])) < 0.07) & (np.abs(y - fi['eye_y']) < fi['eye_h'] * 2.2)
        rgb[mk] = sc
    if spec.get('glasses') or spec.get('monocle'):
        gc = _c(spec.get('glasses') or (spec['monocle'] if isinstance(spec['monocle'], str) else '#d8b050'))
        sides = (-1, 1) if spec.get('glasses') else (1,)
        for sgn in sides:
            r = ((x - sgn * fi['eye_dx']) / (fi['eye_w'] * 1.45)) ** 2 + ((y - fi['eye_y'] - 0.05) / (fi['eye_h'] * 1.4)) ** 2
            rim = front & (r > 0.8) & (r < 1.05)
            rgb[rim] = gc
        if spec.get('glasses'):
            br = front & (np.abs(x) < fi['eye_dx'] - fi['eye_w'] * 1.3) & (np.abs(y - fi['eye_y'] + fi['eye_h'] * 0.5) < 0.06)
            rgb[br] = gc
        else:
            ch = front & (np.abs(x - (fi['eye_dx'] + fi['eye_w'] * 1.3)) < 0.06) & (y > fi['eye_y']) & (y < fi['chin_y'])
            rgb[ch] = gc
    if spec.get('veil') or spec.get('mask'):
        vc = _c(spec.get('veil') or spec.get('mask'))
        mk = front & (y > fi['nose_y'] - 0.35)
        rgb[mk] = rgb[mk] * 0.2 + vc * 0.8
        if spec.get('veil'):
            fold = mk & ((np.round(x * 6).astype(int) % 4) == 0)
            rgb[fold] = rgb[fold] * 0.85
    if spec.get('veil_eyes'):
        ve = _c(spec['veil_eyes'])
        for sgn in (-1, 1):
            mk = front & (((x - sgn * fi['eye_dx']) / 0.28) ** 2 + ((y - fi['eye_y']) / 0.22) ** 2 < 1)
            rgb[mk] = ve
            glow[mk, :3] = ve
            glow[mk, 3] = 255
    return rgb, glow

def mouth(rgb, x, y, front, fi, kind, skin):
    my = fi['mouth_y']
    mc = _c(mix(skin, (150, 60, 70), 0.6))
    dark = _c('#5a1e2a')
    def put(mask, col):
        rgb[mask & front] = col
    w = 0.32 if not fi['man'] else 0.38
    if kind == 'none':
        put((np.abs(x) < 0.12) & (np.abs(y - my) < 0.05), _c(mix(skin, (150, 60, 70), 0.35)))
    elif kind in ('small', 'soft', 'flat'):
        ww = {'small': 0.15, 'soft': 0.22, 'flat': w}[kind]
        put((np.abs(x) < ww) & (np.abs(y - my) < 0.055), mc)
    elif kind in ('smile', 'cat', 'smirk'):
        if kind == 'cat':
            yy = my + 0.1 * np.abs(np.sin(x * math.pi / w)) - 0.05
            put((np.abs(x) < w) & (np.abs(y - yy) < 0.055), mc)
        else:
            k = 1.0 if kind == 'smile' else 0.0
            yy = my - 0.5 * (x / w) ** 2 * 0.25 + 0.06 - (0 if kind == 'smile' else 0.12 * (x / w))
            put((np.abs(x) < w) & (np.abs(y - yy) < 0.055), mc)
    elif kind == 'frown':
        yy = my + 0.12 * (x / w) ** 2 - 0.04
        put((np.abs(x) < w * 0.9) & (np.abs(y - yy) < 0.055), mc)
    elif kind in ('open', 'grin', 'fang'):
        if kind == 'open':
            m = ((x / 0.2) ** 2 + ((y - my - 0.05) / 0.14) ** 2) < 1
            put(m, dark)
            put(m & (y > my + 0.08), _c('#d86a7a'))
        elif kind == 'grin':
            m = (np.abs(x) < w * 1.1) & (y > my - 0.08) & (y < my + 0.1 - 0.4 * (x / w) ** 2 * 0.25)
            put(m, _c('#f4f0ee'))
            put((np.abs(x) < w * 1.1) & (np.abs(y - (my - 0.09)) < 0.04), mc)
        else:
            put((np.abs(x) < w * 0.8) & (np.abs(y - my) < 0.05), mc)
            fm = (x > 0.08) & (x < 0.2) & (y > my) & (y < my + 0.15 - (x - 0.08) * 0.8)
            put(fm, _c('#ffffff'))

def paint_lids(rgb, alpha, x, y, front, fi, spec, build, skin, hair):
    style = face8.resolve(build, spec)
    p = style_params(style)
    if p['closed'] or p['void']:
        return
    line = _c(spec.get('line', mix(hexc(hair), '#1a1420', 0.75)))
    for sgn in (-1, 1):
        u, v, o, top, bot, white, ew, eh = eye_masks(x, y, fi, sgn, p)
        area = front & (np.abs(u) < 1.18) & (v > top - 0.45) & (v < bot + 0.15)
        alpha[area] = 1.0
        rgb[area] = _c(shade(skin, 0.95))
        arc = area & (np.abs(v - (bot - 0.25 + 0.2 * u ** 2)) < 0.17)
        rgb[arc] = line
        lash = area & (o > 0.7) & (np.abs(v - (bot - 0.3 + 0.2 * u ** 2) - 0.25 * (o - 0.7)) < 0.15)
        rgb[lash] = line

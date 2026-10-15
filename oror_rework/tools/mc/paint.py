"""Minecraft-style texture painting (one texel per model unit).

Style rules, taken from vanilla mobs/skins and the reference mods:
  * flat colour areas built from a 5-tone hue-shifted ramp, never smooth gradients;
  * a light per-texel value jitter (vanilla 'noise') so surfaces do not look like plastic;
  * hems, seams, rims and strand lines one texel wide; detail comes from colour, not geometry;
  * cut-out alpha for hair tips, feathers, skirts and other planes.

Face orientation inside a box-UV face image (verified against ModelPart.Cube):
  front: left = model -X;  back: left = +X;  right(WEST): left = back, right = front;
  left(EAST): left = front, right = back;  top: top row = back;  bottom: top row = back.
"""
import zlib, math
import numpy as np
from PIL import Image
from colors import hexc, mix, shade, lum
import face8

def M(t, color, **kw):
    d = {'type': t, 'color': color}
    d.update(kw)
    return d

# ------------------------------------------------------------------ tone ramps
def ramp(c):
    c = hexc(c)
    return {-3: shade(c, 0.52), -2: shade(c, 0.68), -1: shade(c, 0.84), 0: c, 1: shade(c, 1.16), 2: shade(c, 1.34)}

def colorize(tone, c):
    r = ramp(c)
    t = np.clip(np.round(tone), -3, 2).astype(int)
    out = np.zeros(tone.shape + (3,), np.float32)
    for k, col in r.items():
        out[t == k] = col
    return out

def jitter(rgb, rng, amp=0.06):
    n = 1.0 + rng.uniform(-amp, amp, rgb.shape[:2])[..., None]
    return np.clip(rgb * n, 0, 255)

def front_cols(face, w):
    """Index of the column nearest the character's front on a side face (or None)."""
    if face == 'right':
        return w - 1
    if face == 'left':
        return 0
    return None

def side_dist_front(face, w):
    """Per-column distance (in texels) from the character's front edge, for side faces."""
    x = np.arange(w)
    if face == 'right':
        return (w - 1 - x)
    if face == 'left':
        return x
    return None

# ------------------------------------------------------------------ pattern masks (1 texel art)
def pattern(name, w, h, face, rng):
    m = np.zeros((h, w), bool)
    if w <= 0 or h <= 0:
        return m
    ys, xs = np.mgrid[0:h, 0:w]
    if name == 'stars':
        for _ in range(max(1, w * h // 24)):
            x, y = rng.integers(0, w), rng.integers(0, h)
            m[y, x] = True
    elif name in ('kimono', 'asanoha'):
        # crossed collar: two diagonals meeting below the neck (front only), plain elsewhere
        if face == 'front' and w >= 4:
            cx = (w - 1) / 2
            for y in range(min(h, int(w * 0.6))):
                xl = int(round(cx - (w / 2 - 1) + y * 0.75))
                xr = int(round(cx + (w / 2 - 1) - y * 0.75))
                if xl <= cx:
                    m[y, max(0, xl)] = True
                if xr >= cx:
                    m[y, min(w - 1, xr)] = True
    elif name == 'embroidery':
        y0 = max(0, h - 3)
        m[y0:y0 + 1, :] = (xs[y0:y0 + 1, :] % 2 == 0)
        if h > 6:
            m[1, :] = xs[1, :] % 3 == 1
    elif name == 'band':
        y = h // 2
        m[y, :] = True
    elif name == 'vine':
        for x in range(w):
            y = int(round(h * 0.55 + math.sin(x * 1.3) * min(2, h / 4)))
            if 0 <= y < h:
                m[y, x] = True
            if x % 3 == 0 and 0 <= y - 1 < h:
                m[y - 1, x] = True
    elif name == 'circuit':
        y = h // 3
        m[y, :] = True
        for x in range(1, w, 3):
            m[y:min(h, y + 3), x] = True
        if h > 6:
            m[min(h - 1, y + 3), :] = xs[0, :] % 3 != 0
    elif name == 'marks':
        for _ in range(max(1, w * h // 20)):
            x, y = rng.integers(0, w), rng.integers(0, h)
            m[y, x] = True
            if y + 1 < h:
                m[y + 1, x] = True
    elif name in ('trim', 'gold_lines'):
        m[:, 0] = True
        m[:, -1] = True
        if name == 'trim':
            m[0, :] = True
            m[-1, :] = True
    elif name == 'trim_top':
        m[0, :] = True
    elif name == 'stripes':
        m = xs % 3 == 1
    elif name == 'runes':
        if face in ('front', 'back') or w >= 6:
            for x in range(1, w - 1, 4):
                lo = min(h // 3, max(0, h - 3))
                y = rng.integers(lo, max(lo + 1, h - 2))
                m[y, x] = True
                if rng.random() < 0.5:
                    m[min(h - 1, y + 1), x] = True
                else:
                    m[y, min(w - 1, x + 1)] = True
    elif name in ('dragon', 'scales'):
        m = ((ys % 2 == 0) & (xs % 3 == 0)) | ((ys % 2 == 1) & (xs % 3 == 2))
    elif name == 'dots':
        m = (xs % 3 == 1) & (ys % 3 == 1)
    elif name == 'cross':
        cx, cy = w // 2, h // 3
        m[max(0, cy - 2):cy + 3, cx] = True
        m[cy, max(0, cx - 1):cx + 2] = True
    elif name == 'chevron':
        m = ((ys + np.abs(xs - (w - 1) / 2)).astype(int) % 4 == 0)
    elif name == 'rings':
        m = ys % 3 == 0
    elif name == 'flame':
        for x in range(w):
            hh = int(1 + (math.sin(x * 2.1 + 0.7) * 0.5 + 0.5) * min(h * 0.35, 3))
            m[max(0, h - hh - 1):h - 1, x] = True
    elif name == 'cracks':
        x = rng.integers(0, w)
        for y in range(h):
            m[y, x] = True
            x = int(np.clip(x + rng.integers(-1, 2), 0, w - 1))
    elif name == 'zigzag':
        m = ((xs + (ys % 4 >= 2) * (3 - ys % 4)) % 4 == 0) if h > 1 else (xs % 2 == 0)
        m = (ys + np.abs((xs % 4) - 2)) % 4 == 0
    return m

# ------------------------------------------------------------------ painters
def tone_base(w, h, face, mat):
    t = np.zeros((h, w), np.float32)
    if face == 'top':
        t += 1
    elif face == 'bottom':
        t -= 1
    if face in ('front', 'back', 'left', 'right') and h >= 4 and mat.get('hem_shadow', True):
        t[-1, :] -= 1
    if face in ('front', 'back') and w >= 6 and mat.get('edge_shade', True):
        t[:, 0] -= 1
        t[:, -1] -= 1
    return t

def apply_trim(rgb, mat, face, w, h):
    acc = hexc(mat.get('accent', shade(mat['color'], 0.7)))
    trim = mat.get('trim', 0)
    if trim and face in ('front', 'back', 'left', 'right') and h >= 3:
        rows = max(1, int(round(trim / 2)))
        rgb[h - rows:, :] = ramp(acc)[0]
        rgb[h - rows, :] = ramp(acc)[1]
        if rows > 1:
            rgb[-1, :] = ramp(acc)[-1]
    return rgb

def p_skin(mat, face, w, h, cube, rng):
    t = tone_base(w, h, face, dict(mat, hem_shadow=False))
    rgb = jitter(colorize(t, mat['color']), rng, 0.012)
    return rgb, None, None

def p_cloth(mat, face, w, h, cube, rng):
    c = mat['color']
    t = tone_base(w, h, face, mat)
    fold = mat.get('fold', 0)
    if mat.get('shape') and face in ('front', 'back'):
        pass
    elif fold and face in ('front', 'back', 'left', 'right') and w >= 3 and h >= 4:
        period = 3 if fold >= 5 else 4
        start = 0 if mat.get('full_fold') else h // 3
        for x in range(w):
            if x % period == period - 1:
                t[start:, x] -= 1
    rgb = jitter(colorize(t, c), rng)
    acc = hexc(mat.get('accent', shade(c, 0.7)))
    glow = None
    pat = mat.get('pattern')
    if pat and face in ('front', 'back', 'left', 'right', 'top') and w > 1 and h > 1:
        pm = pattern(pat, w, h, face, rng)
        ac = np.array(ramp(acc)[0 if lum(acc) < 0.8 else -1 if lum(c) > 0.8 else 0], np.float32)
        rgb[pm] = ac
        if mat.get('pattern_glow'):
            rgb[pm] = np.array(ramp(acc)[-1], np.float32)
            glow = np.zeros((h, w, 4), np.float32)
            glow[pm, :3] = acc
            glow[pm, 3] = 255 * mat.get('glow_amount', 0.5)
    if mat.get('seam') and face == 'front' and w >= 4:
        cx = w // 2
        rgb[:, cx - 1] = ramp(acc)[0]
        for y in range(1, h - 1, 3):
            rgb[y, cx - 1] = ramp(acc)[1]
    neck = mat.get('neckline')
    if neck and face == 'front' and w >= 4:
        sk = np.array(hexc(mat.get('skin', '#f3dfd7')), np.float32)
        cx = w / 2
        if neck == 'v':
            for y in range(min(3, h)):
                for x in range(w):
                    if abs(x + 0.5 - cx) < 1.6 - y * 0.6:
                        rgb[y, x] = sk
        elif neck == 'round':
            rgb[0, int(cx) - 2:int(cx) + 2] = sk
            rgb[1, int(cx) - 1:int(cx) + 1] = sk
        elif neck == 'wide':
            rgb[0, 1:w - 1] = sk
            rgb[1, 2:w - 2] = sk
        elif neck == 'collar':
            rgb[0, :] = ramp(acc)[1]
            rgb[1, int(cx) - 1:int(cx) + 1] = sk
    apply_trim(rgb, mat, face, w, h)
    if mat.get('trim_top') and face in ('front', 'back', 'left', 'right'):
        rgb[0, :] = ramp(acc)[1]
    alpha = None
    shape = mat.get('shape')
    if shape and face in ('front', 'back'):
        alpha = shape_alpha(shape, w, h)
    return rgb, alpha, glow

def shape_alpha(shape, w, h):
    a = np.ones((h, w), np.float32)
    if shape == 'trap':          # skirt panel: plain rectangle (panels overlap)
        pass
    elif shape == 'scallop':     # frilled hem
        for x in range(w):
            if x % 2 == 1:
                a[-1, x] = 0
    elif shape == 'point':       # pointed tip (strands, tails of cloth)
        for k in range(min(h, (w + 1) // 2)):
            y = h - 1 - k
            a[y, :max(0, (w // 2) - k - (0 if w % 2 else 1)) if False else 0] = 0
        cx = (w - 1) / 2
        for y in range(h):
            dy = h - 1 - y
            half = dy * 1.0 + 0.5
            for x in range(w):
                if abs(x - cx) > half:
                    a[y, x] = 0
    elif shape == 'round':
        cx, cy = (w - 1) / 2, (h - 1) / 2
        ys, xs = np.mgrid[0:h, 0:w]
        a[((xs - cx) / max(0.5, w / 2)) ** 2 + ((ys - cy) / max(0.5, h / 2)) ** 2 > 1.05] = 0
    elif shape == 'tips':
        for x in range(w):
            if x % 2 == 1:
                a[-1, x] = 0
    return a

def p_hair(mat, face, w, h, cube, rng):
    c = mat['color']
    tip = mat.get('tip')
    t = np.zeros((h, w), np.float32)
    if face == 'top':
        t += 1
    elif face == 'bottom':
        t -= 1
    if face in ('front', 'back', 'left', 'right'):
        # strand columns
        for x in range(w):
            if (x + cube_seed(cube)) % 3 == 0:
                t[:, x] -= 1
        # shine band
        if mat.get('shine', True) and h >= 6:
            y = max(1, int(h * mat.get('shine_y', 0.22)))
            for x in range(w):
                if (x + y) % 3 != 0:
                    t[y, x] += 1
        if h >= 3:
            t[-1, :] -= 1
    rgb = colorize(t, c)
    if tip and face in ('front', 'back', 'left', 'right') and h >= 3:
        t0, t1 = mat.get('t0', 0.0), mat.get('t1', 1.0)
        for y in range(h):
            k = t0 + (t1 - t0) * (y + 0.5) / h
            f = max(0.0, (k - 0.45) / 0.55)
            if f > 0:
                tipc = np.array(ramp(tip)[0], np.float32)
                rgb[y] = rgb[y] * (1 - f * 0.85) + tipc * (f * 0.85)
    rgb = jitter(rgb, rng, 0.03)
    alpha = None
    cut = mat.get('cut')
    if cut and face in ('front', 'back', 'left', 'right'):
        alpha = np.ones((h, w), np.float32)
        if cut in ('tips', 'point'):
            if cut == 'point' and w >= 2:
                alpha = shape_alpha('point', w, h)
            else:
                for x in range(w):
                    if (x + cube_seed(cube)) % 2 == 1:
                        alpha[-1, x] = 0
                if h >= 4 and w >= 3:
                    for x in range(w):
                        if (x + cube_seed(cube)) % 4 == 0:
                            alpha[-2, x] = 0
    return rgb, alpha, None

BANGS = {
    #          rows 0..7 for the hair overlay front ('#' hair, '+' hair shadow, '.' clear)
    'bangs':   ["########", "########", "########", "#+.##.+#", "#......#", "#......#", "#......#", "........"],
    'blunt':   ["########", "########", "########", "########", "#......#", "#......#", "#......#", "#......#"],
    'parted':  ["########", "########", "###..###", "##....##", "#......#", "#......#", "#......#", "........"],
    'swept':   ["########", "########", "########", "#####+.#", "####...#", "#......#", "#......#", "........"],
    'messy':   ["########", "########", "########", "#.#.##.#", "#......#", "#......#", "........", "........"],
    'short':   ["########", "########", "#.####.#", "#......#", "#......#", "........", "........", "........"],
    'slick':   ["########", "########", "##....##", "#......#", "........", "........", "........", "........"],
    'open':    ["########", "##....##", "#......#", "#......#", "#......#", "#......#", "........", "........"],
    'none':    ["........"] * 8,
}

def bangs_alpha(style, long_sides, w=8, h=8):
    rows = BANGS.get(style, BANGS['bangs'])
    a = np.zeros((h, w), np.float32)
    sh = np.zeros((h, w), bool)
    for y in range(min(h, 8)):
        for x in range(min(w, 8)):
            ch = rows[y][x]
            if ch in '#+':
                a[y, x] = 1
            if ch == '+':
                sh[y, x] = True
    if not long_sides:
        a[5:, :] = 0
    return a, sh

def p_hair_shell(mat, face, w, h, cube, rng):
    """Skin-style hair overlay (inflated head box)."""
    rgb, _, _ = p_hair(dict(mat, shine_y=0.3), face, w, h, cube, rng)
    alpha = np.ones((h, w), np.float32)
    style = mat.get('bangs', 'bangs')
    long_sides = mat.get('long', True)
    if face == 'front':
        alpha, sh = bangs_alpha(style, long_sides, w, h)
        rgb[sh] = ramp(mat['color'])[-1]
        # bang tips one tone darker
        for x in range(w):
            col = np.where(alpha[:, x] > 0)[0]
            col = col[col < 4]
            if len(col):
                rgb[col.max(), x] = ramp(mat['color'])[-1]
    elif face in ('left', 'right'):
        if not long_sides:
            alpha[5:, :] = 0
            fc = front_cols(face, w)
            alpha[5:, fc] = 1 if mat.get('sideburn', False) else 0
        if mat.get('ears_open'):
            # leave the ear area clear
            d = side_dist_front(face, w)
            for x in range(w):
                if 3 <= d[x] <= 4:
                    alpha[4:6, x] = 0
    elif face == 'back':
        if not mat.get('back', True):
            alpha[5:, :] = 0
    elif face == 'bottom':
        alpha[:, :] = 0
    return rgb, alpha, None

def p_head(mat, face, w, h, cube, rng):
    """Base head: hair on top/back/sides, face on the front."""
    hair = mat.get('hair', '#4a3a30')
    skin = mat['color']
    if face == 'front':
        px = np.zeros((h, w, 4), np.float32)
        hr = ramp(hair)
        px[..., :3] = hr[0]
        px[..., 3] = 255
        for y in range(min(3, h)):
            for x in range(w):
                px[y, x, :3] = hr[0 if (x + y) % 3 else -1]
        glow = np.zeros((h, w, 4), np.float32)
        face8.draw_face8(px, mat.get('face', {}), skin, hair, mat.get('build', 'woman'), glow)
        rgb = jitter(px[..., :3], rng, 0.01)
        return rgb, None, glow if glow[..., 3].any() else None
    if face == 'bottom':
        return p_skin(dict(mat), face, w, h, cube, rng)
    rgb, _, _ = p_hair(M('hair', hair, shine=False), face, w, h, cube, rng)
    if face in ('left', 'right') and h >= 8:
        # face skin visible at the front of the side, ear below the hairline
        d = side_dist_front(face, w)
        sk = np.array(ramp(skin)[-1], np.float32)
        for x in range(w):
            if d[x] <= 1:
                rgb[4:, x] = ramp(skin)[0] if d[x] == 0 else sk
            if d[x] in (3, 4) and mat.get('ears', True):
                rgb[4:6, x] = sk
    return rgb, None, None

def p_blink(mat, face, w, h, cube, rng):
    if face not in ('front', 'back') or w < 8 or h < 8:
        return np.zeros((h, w, 3), np.float32), np.zeros((h, w), np.float32), None
    px = np.zeros((h, w, 4), np.float32)
    face8.blink8(px, mat.get('face', {}), mat['color'], mat.get('hair', '#000000'), mat.get('build', 'woman'))
    if face == 'back':
        return px[..., :3], np.zeros((h, w), np.float32), None
    return px[..., :3], px[..., 3] / 255.0, None

def p_metal(mat, face, w, h, cube, rng):
    c = mat['color']
    t = tone_base(w, h, face, mat)
    if face in ('front', 'back', 'left', 'right'):
        if h >= 2:
            t[0, :] += 1
        if w >= 3 and h >= 3:
            for k in range(min(w, h)):
                x, y = w - 1 - k - 1, k
                if 0 <= x < w:
                    t[y, x] += 1
        t[:, 0] -= 0.6 if w > 2 else 0
    rgb = jitter(colorize(t, c), rng, 0.02)
    acc = mat.get('accent')
    pat = mat.get('pattern')
    glow = None
    if pat and acc and w > 1 and h > 1:
        pm = pattern(pat, w, h, face, rng)
        rgb[pm] = ramp(acc)[0]
        if mat.get('pattern_glow'):
            rgb[pm] = ramp(acc)[-1]
            glow = np.zeros((h, w, 4), np.float32)
            glow[pm, :3] = hexc(acc)
            glow[pm, 3] = 255 * mat.get('glow_amount', 0.55)
    if mat.get('rivets') and w >= 3 and h >= 3:
        for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
            rgb[y, x] = ramp(c)[2]
    eg = mat.get('edge_glow')
    if eg and face != 'top' and face != 'bottom' and min(w, h) == 1:
        # the thin faces of a blade are its edges: they carry the light
        glow = np.zeros((h, w, 4), np.float32)
        glow[..., :3] = hexc(eg)
        glow[..., 3] = 200
        rgb[...] = np.array(mix(eg, '#ffffff', 0.35), np.float32)
    elif eg and face in ('front', 'back', 'left', 'right') and w >= 2:
        rgb[:, -1] = np.array(mix(c, eg, 0.5), np.float32)
    return rgb, None, glow

def p_gem(mat, face, w, h, cube, rng):
    c = mat['color']
    ys, xs = np.mgrid[0:h, 0:w]
    t = np.zeros((h, w), np.float32)
    t -= ((xs == 0) | (ys == h - 1)) * 1.0
    t += ((xs == w - 1) | (ys == 0)) * 0.0
    t[(xs + ys) < max(1, min(w, h) // 2)] += 1
    rgb = colorize(t, c)
    if w >= 2 and h >= 2:
        rgb[0, min(w - 1, 1) if w > 2 else 0] = mix(c, '#ffffff', 0.85)
    glow = None
    if mat.get('glow', True):
        glow = np.zeros((h, w, 4), np.float32)
        glow[..., :3] = rgb * 0.9
        glow[..., 3] = 200
    return rgb, None, glow

def p_energy(mat, face, w, h, cube, rng):
    c = mat['color']
    t = np.zeros((h, w), np.float32) + 1
    ys, xs = np.mgrid[0:h, 0:w]
    t[(xs + ys * 2) % 5 == 0] += 1
    rgb = jitter(colorize(t, c), rng, 0.05)
    glow = np.zeros((h, w, 4), np.float32)
    glow[..., :3] = rgb
    glow[..., 3] = 255
    alpha = None
    if mat.get('cut') and h >= 2:
        alpha = np.ones((h, w), np.float32)
        alpha[-1, ::2] = 0
    return rgb, alpha, glow

def p_horn(mat, face, w, h, cube, rng):
    c = mat['color']
    tip = mat.get('tip') or shade(c, 0.6)
    t = np.zeros((h, w), np.float32)
    if face == 'top':
        t += 1
    for y in range(h):
        if y % 3 == 2:
            t[y, :] -= 1
    t[:, 0] -= 0.6
    rgb = colorize(t, c)
    t0, t1 = mat.get('t0', 0.0), mat.get('t1', 1.0)
    # horns grow upwards: image row 0 is the far end only when the bone points up; use t0/t1 explicitly
    for y in range(h):
        k = t0 + (t1 - t0) * (y + 0.5) / max(1, h)
        if mat.get('flip'):
            k = 1 - k
        f = max(0.0, min(1.0, (k - 0.3) / 0.7))
        rgb[y] = rgb[y] * (1 - f) + np.array(ramp(tip)[0], np.float32) * f
    rgb = jitter(rgb, rng, 0.02)
    glow = None
    if mat.get('glow'):
        glow = np.zeros((h, w, 4), np.float32)
        for y in range(h):
            k = t0 + (t1 - t0) * (y + 0.5) / max(1, h)
            if mat.get('flip'):
                k = 1 - k
            if k > 0.6:
                glow[y, :, :3] = hexc(tip)
                glow[y, :, 3] = 255 * min(1, (k - 0.6) / 0.3)
    return rgb, None, glow

def p_scale(mat, face, w, h, cube, rng):
    c = mat['color']
    ys, xs = np.mgrid[0:h, 0:w]
    t = tone_base(w, h, face, mat)
    off = (ys // 2) % 2
    t[((xs + off * 1) % 2 == 0) & (ys % 2 == 0)] += 1
    t[((xs + off * 1) % 2 == 1) & (ys % 2 == 1)] -= 1
    rgb = jitter(colorize(t, c), rng, 0.02)
    tip = mat.get('tip_color')
    return rgb, None, None

def p_fur(mat, face, w, h, cube, rng):
    c = mat['color']
    t = tone_base(w, h, face, mat)
    noise = rng.integers(-1, 2, (h, w))
    t += noise * 0.6
    if face in ('front', 'back', 'left', 'right') and h >= 3:
        t[-1, ::2] -= 1
    rgb = jitter(colorize(t, c), rng, 0.03)
    if mat.get('tip'):
        tp = np.array(ramp(mat['tip'])[0], np.float32)
        if h >= 3 and face in ('front', 'back', 'left', 'right'):
            rgb[-max(1, h // 4):] = tp
    return rgb, None, None

def p_feather(mat, face, w, h, cube, rng):
    """Feather rows: each 2-texel column is one feather with a light shaft, darker vane and a
    rounded/pointed tip; primaries vary in length so the wing edge steps like a real wing."""
    c = mat['color']
    tipc = mat.get('tip')
    t = np.zeros((h, w), np.float32)
    rev = mat.get('reverse', False)
    for x in range(w):
        k = (w - 1 - x) if rev else x
        if k % 2 == 1:
            t[:, x] -= 1
    if face == 'top':
        t += 1
    rgb = colorize(t, c)
    alpha = np.ones((h, w), np.float32)
    if mat.get('coverts'):
        # small overlapping feathers: scalloped rows
        for y in range(h):
            for x in range(w):
                if y % 3 == 2 and (x + y // 3) % 2 == 0:
                    rgb[y, x] = ramp(c)[-1]
        if face in ('front', 'back') and h >= 2:
            for x in range(w):
                if x % 2 == 1:
                    alpha[-1, x] = 0
    elif face in ('front', 'back') and h >= 3:
        var = mat.get('length_var', 2)
        for x in range(w):
            k = (w - 1 - x) if rev else x
            if mat.get('primaries'):
                cut = int(round(var * (1 - k / max(1, w - 1))))   # longer towards the wing tip
            else:
                cut = (k // 2) % (var + 1)
            if k % 2 == 1:
                cut += 1
            if cut > 0:
                alpha[h - cut:, x] = 0
            # tip colour band right above the cut
            yt = h - cut - 1
            if tipc and yt >= 1:
                rgb[max(0, yt - 1):yt + 1, x] = ramp(tipc)[0]
    rgb = jitter(rgb, rng, 0.03)
    glow = None
    if mat.get('glow'):
        glow = np.zeros((h, w, 4), np.float32)
        glow[..., :3] = rgb
        glow[..., 3] = 90
    return rgb, alpha if face in ('front', 'back') else None, glow

def p_membrane(mat, face, w, h, cube, rng):
    """Bat/dragon wing skin between the fingers: scalloped trailing edge, faint veins."""
    c = mat['color']
    t = np.zeros((h, w), np.float32)
    ys, xs = np.mgrid[0:h, 0:w]
    t[(ys > h * 0.6)] -= 1
    rgb = colorize(t, c)
    acc = mat.get('accent')
    if acc:
        for k in range(1, 4):
            x = int(w * k / 4)
            for y in range(h // 4, h - 2):
                if (y + k) % 4 != 0 and 0 <= x < w:
                    rgb[y, x] = np.array(mix(c, acc, 0.45), np.float32)
    rgb = jitter(rgb, rng, 0.03)
    alpha = np.ones((h, w), np.float32)
    if face in ('front', 'back') and h >= 4 and w >= 4:
        seg = max(2, w // 4)
        for x in range(w):
            u = (x % seg) / seg
            depth = int(round((1 - abs(u - 0.5) * 2) * min(4, h * 0.35)))
            if depth > 0:
                alpha[h - depth:, x] = 0
    return rgb, alpha if face in ('front', 'back') else None, None

def p_simple(mat, face, w, h, cube, rng, amp=0.04, bands=None):
    t = tone_base(w, h, face, mat)
    rgb = jitter(colorize(t, mat['color']), rng, amp)
    return rgb, None, None

def p_wood(mat, face, w, h, cube, rng):
    c = mat['color']
    t = tone_base(w, h, face, mat)
    for x in range(w):
        if x % 2 == 0:
            t[:, x] -= 0.6
    t[rng.integers(0, h, max(1, h // 4)), rng.integers(0, w, max(1, h // 4))] -= 1
    return jitter(colorize(t, c), rng, 0.03), None, None

def p_leaf(mat, face, w, h, cube, rng):
    c = mat['color']
    t = rng.integers(-1, 2, (h, w)).astype(np.float32)
    rgb = colorize(t, c)
    alpha = np.ones((h, w), np.float32)
    alpha[rng.random((h, w)) < 0.12] = 0
    return rgb, alpha, None

def p_rock(mat, face, w, h, cube, rng):
    c = mat['color']
    t = tone_base(w, h, face, mat) + rng.integers(-1, 2, (h, w)) * 0.7
    rgb = jitter(colorize(t, c), rng, 0.03)
    glow = None
    if mat.get('pattern') == 'cracks' or mat.get('cracks'):
        pm = pattern('cracks', w, h, face, rng)
        gc = mat.get('accent', '#ff8030')
        rgb[pm] = hexc(gc)
        glow = np.zeros((h, w, 4), np.float32)
        glow[pm, :3] = hexc(gc)
        glow[pm, 3] = 255
    return rgb, None, glow

def p_void(mat, face, w, h, cube, rng):
    c = mat.get('color', '#140c22')
    t = rng.integers(-1, 1, (h, w)).astype(np.float32)
    rgb = colorize(t, c)
    glow = np.zeros((h, w, 4), np.float32)
    star = mat.get('accent', '#d8b8ff')
    for _ in range(max(1, w * h // 10)):
        x, y = rng.integers(0, max(1, w)), rng.integers(0, max(1, h))
        rgb[y, x] = hexc(star)
        glow[y, x, :3] = hexc(star)
        glow[y, x, 3] = 255
    return rgb, None, glow

def p_rainbow(mat, face, w, h, cube, rng):
    cols = ['#ff5a5a', '#ffb84a', '#fff07a', '#6aff8a', '#5ac8ff', '#9a7aff']
    rgb = np.zeros((h, w, 3), np.float32)
    for y in range(h):
        for x in range(w):
            rgb[y, x] = hexc(cols[(x + y) % len(cols)])
    glow = np.zeros((h, w, 4), np.float32)
    glow[..., :3] = rgb
    glow[..., 3] = 180 if mat.get('glow', True) else 0
    return rgb, None, glow

def p_slime(mat, face, w, h, cube, rng):
    c = mat['color']
    t = tone_base(w, h, face, mat)
    rgb = colorize(t, c)
    for _ in range(max(1, w * h // 12)):
        x, y = rng.integers(0, max(1, w)), rng.integers(0, max(1, h))
        rgb[y, x] = ramp(c)[2]
    return jitter(rgb, rng, 0.02), None, None

def p_ring(mat, face, w, h, cube, rng):
    """Halo / ring drawn on the two large faces of a thin plane; clear elsewhere."""
    c = mat['color']
    W, H = w, h
    rgb = np.zeros((H, W, 3), np.float32)
    alpha = np.zeros((H, W), np.float32)
    big = sorted(cube.size)[1:] if cube is not None else (w, h)
    if min(w, h) < 3 or (w * h) < 0.8 * big[0] * big[1]:
        return rgb, alpha, None
    ys, xs = np.mgrid[0:H, 0:W]
    cx, cy = (W - 1) / 2, (H - 1) / 2
    r = np.sqrt(((xs - cx) / (W / 2)) ** 2 + ((ys - cy) / (H / 2)) ** 2)
    width = mat.get('width', 0.16)
    inner = mat.get('inner', 1.0 - width * 1.6)
    ring = (r <= 1.0) & (r >= inner)
    rgb[ring] = ramp(c)[0]
    rgb[ring & (r > (1 + inner) / 2)] = ramp(c)[1]
    alpha[ring] = 1
    spikes = mat.get('spikes', 0)
    if spikes:
        ang = np.arctan2(ys - cy, xs - cx)
        sp = (np.cos(ang * spikes) > 0.75) & (r < inner) & (r > inner - 0.18)
        rgb[sp] = ramp(c)[1]
        alpha[sp] = 1
    spokes = mat.get('spokes')
    if spokes:
        for k in range(int(spokes)):
            a = 2 * math.pi * k / spokes
            for t in np.linspace(0.12, inner, int(max(W, H))):
                x, y = int(round(cx + math.cos(a) * t * W / 2)), int(round(cy + math.sin(a) * t * H / 2))
                if 0 <= x < W and 0 <= y < H:
                    rgb[y, x] = ramp(c)[-1]
                    alpha[y, x] = 1
        hub = r <= 0.14
        rgb[hub] = ramp(c)[1]
        alpha[hub] = 1
    poly = mat.get('poly')
    if poly:
        # geometric halo: a star polygon {n/2} inscribed in the ring
        n = int(poly)
        rr = inner * 0.98
        pts = [(cx + math.cos(2 * math.pi * k / n - math.pi / 2) * rr * W / 2,
                cy + math.sin(2 * math.pi * k / n - math.pi / 2) * rr * H / 2) for k in range(n)]
        for k in range(n):
            (x0, y0), (x1, y1) = pts[k], pts[(k + 2) % n]
            for t in np.linspace(0, 1, int(max(W, H) * 2)):
                x, y = int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t))
                if 0 <= x < W and 0 <= y < H:
                    rgb[y, x] = ramp(c)[0]
                    alpha[y, x] = 1
    if mat.get('rainbow'):
        ang = (np.arctan2(ys - cy, xs - cx) / (2 * math.pi) + 0.5)
        import colorsys
        for y in range(H):
            for x in range(W):
                if alpha[y, x] > 0:
                    rgb[y, x] = np.array(colorsys.hsv_to_rgb(float(ang[y, x]), 0.62, 1.0)) * 255
    glow = np.zeros((H, W, 4), np.float32)
    glow[alpha > 0, :3] = rgb[alpha > 0]
    glow[alpha > 0, 3] = 255 * mat.get('glow_amount', 1.0)
    return rgb, alpha, glow

def p_plane(mat, face, w, h, cube, rng):
    c = mat['color']
    shape = mat.get('shape', 'leaf')
    rgb = colorize(np.zeros((h, w), np.float32), c)
    ys, xs = np.mgrid[0:h, 0:w]
    cx, cy = (w - 1) / 2, (h - 1) / 2
    nx, ny = (xs - cx) / max(0.5, w / 2), (ys - cy) / max(0.5, h / 2)
    if shape == 'star':
        a = (np.abs(nx) + np.abs(ny) < 1.0) | ((np.abs(nx) < 0.25) | (np.abs(ny) < 0.25)) & (np.abs(nx) + np.abs(ny) < 1.4)
    elif shape == 'diamond':
        a = np.abs(nx) + np.abs(ny) <= 1.0
    elif shape == 'circle':
        a = nx ** 2 + ny ** 2 <= 1.05
    else:   # leaf / petal
        a = (nx ** 2) * 1.3 + (ny ** 2) <= 1.0
    rgb[(nx + ny) < -0.2] = ramp(c)[1]
    alpha = a.astype(np.float32)
    glow = None
    if mat.get('glow'):
        glow = np.zeros((h, w, 4), np.float32)
        glow[a, :3] = rgb[a]
        glow[a, 3] = 255
    return rgb, alpha, glow

def p_eye(mat, face, w, h, cube, rng):
    """Big creature eye on the front face."""
    c = mat.get('sclera', '#f4f0e8')
    rgb = colorize(np.zeros((h, w), np.float32), c)
    glow = None
    if face == 'front':
        ys, xs = np.mgrid[0:h, 0:w]
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = np.sqrt(((xs - cx) / max(0.5, w / 2)) ** 2 + ((ys - cy) / max(0.5, h / 2)) ** 2)
        iris = hexc(mat['color'])
        rgb[r < 0.75] = iris
        rgb[r < 0.35] = mix(iris, '#100810', 0.85)
        if mat.get('slit'):
            rgb[(np.abs(xs - cx) < 0.6) & (r < 0.75)] = (16, 8, 16)
        if w >= 3 and h >= 3:
            rgb[max(0, int(cy) - 1), max(0, int(cx) - 1)] = (255, 255, 255)
        glow = np.zeros((h, w, 4), np.float32)
        m = r < 0.75
        glow[m, :3] = rgb[m]
        glow[m, 3] = 230
    else:
        rgb = colorize(np.zeros((h, w), np.float32) - 1, mat.get('lid', '#3a2a3a'))
    return rgb, None, glow

PAINTERS = {
    'skin': p_skin, 'cloth': p_cloth, 'hair': p_hair, 'hair_shell': p_hair_shell, 'head': p_head, 'blink': p_blink,
    'metal': p_metal, 'gem': p_gem, 'energy': p_energy, 'horn': p_horn, 'scale': p_scale, 'fur': p_fur,
    'feather': p_feather, 'membrane': p_membrane, 'wood': p_wood, 'leaf': p_leaf, 'rock': p_rock, 'void': p_void,
    'rainbow': p_rainbow, 'slime': p_slime, 'ring': p_ring, 'plane': p_plane, 'eye': p_eye,
    'bone': lambda m, f, w, h, c, r: p_simple(m, f, w, h, c, r, 0.03),
}

def cube_seed(cube):
    if cube is None:
        return 0
    return zlib.crc32((cube.bone.name + cube.name).encode()) % 7

# ------------------------------------------------------------------ rig painting
def paint_rig(rig, seed=11):
    W, H = rig.layout
    rgba = np.zeros((H, W, 4), np.float32)
    glow = np.zeros((H, W, 4), np.float32)
    for c in rig.cubes():
        rects = c.rects()
        for face, (u, v, w, h) in rects.items():
            w, h = int(round(w)), int(round(h))
            u, v = int(round(u)), int(round(v))
            if w <= 0 or h <= 0:
                continue
            mat = c.mat
            if c.faces and face in c.faces:
                mat = c.faces[face]
                if mat is None:
                    continue
            rng = np.random.default_rng(zlib.crc32(f'{seed}/{c.bone.name}/{c.name}/{face}'.encode()))
            fn = PAINTERS[mat['type']]
            rgb, alpha, g = fn(mat, face, w, h, c, rng)
            if face == 'back' and c.size[2] == 0 and mat.get('inner_dark', True) and mat['type'] not in ('ring', 'blink'):
                rgb = rgb * 0.78
            a = np.ones((h, w), np.float32) if alpha is None else alpha
            if mat.get('alpha') is not None:
                a = a * (mat['alpha'] / 255.0 if mat['alpha'] > 1 else mat['alpha'])
            region = rgba[v:v + h, u:u + w]
            region[..., :3] = rgb[:region.shape[0], :region.shape[1]]
            region[..., 3] = (a * 255)[:region.shape[0], :region.shape[1]]
            if mat.get('glow') is True and g is None:
                g = np.zeros((h, w, 4), np.float32)
                g[..., :3] = rgb
                g[..., 3] = 255
            if g is not None:
                gr = glow[v:v + h, u:u + w]
                m = (g[..., 3] > 0) & (a > 0)
                gr[m] = g[m]
    tex = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), 'RGBA')
    # premultiply: the eyes render type adds rgb with blend ONE,ONE, so rgb must carry the strength
    k = glow[..., 3:4] / 255.0 * GLOW_K
    glow[..., :3] *= k
    glow[..., 3] = np.where(glow[..., 3] > 0, 255, 0)
    glow[glow[..., 3] == 0, :3] = 0
    gl = Image.fromarray(np.clip(glow, 0, 255).astype(np.uint8), 'RGBA')
    return tex, gl

GLOW_K = 0.85

def p_stack(mat, face, w, h, cube, rng):
    """Vertical stack of materials on one box (like a skin: shirt / belt / trousers / boots).
    mat['layers'] = [(material, rows), ...]; the last layer takes the remaining rows."""
    layers = mat['layers']
    if face == 'top':
        m = layers[0][0]
        return PAINTERS[m['type']](m, face, w, h, cube, rng)
    if face == 'bottom':
        m = layers[-1][0]
        return PAINTERS[m['type']](m, face, w, h, cube, rng)
    rgb = np.zeros((h, w, 3), np.float32)
    alpha = np.ones((h, w), np.float32)
    glow = np.zeros((h, w, 4), np.float32)
    y = 0
    for i, (m, rows) in enumerate(layers):
        n = h - y if i == len(layers) - 1 else min(int(rows), h - y)
        if n <= 0:
            continue
        sub = dict(m)
        if i < len(layers) - 1:
            sub['hem_shadow'] = sub.get('hem_shadow', False)
            if face != 'front':
                sub.pop('neckline', None)
        elif face != 'front':
            sub.pop('neckline', None)
        if i > 0:
            sub.pop('neckline', None)
        if face != 'front':
            sub.pop('seam', None) if sub.get('seam') == 'front' else None
        r, a, g = PAINTERS[m['type']](sub, face, w, n, cube, rng)
        rgb[y:y + n] = r
        if a is not None:
            alpha[y:y + n] = a
        if g is not None:
            glow[y:y + n] = g
        y += n
    return rgb, alpha, glow if glow[..., 3].any() else None

PAINTERS['stack'] = p_stack

def p_coat_front(mat, face, w, h, cube, rng):
    rgb, alpha, glow = p_cloth(dict(mat, type='cloth'), face, w, h, cube, rng)
    alpha = np.ones((h, w), np.float32) if alpha is None else alpha
    if w >= 4:
        gap = 2 if w <= 8 else 4
        x0 = (w - gap) // 2
        alpha[1:, x0:x0 + gap] = 0
        acc = mat.get('accent')
        if acc:
            rgb[:, x0 - 1] = ramp(acc)[0]
            rgb[:, x0 + gap] = ramp(acc)[0]
    return rgb, alpha, glow

PAINTERS['coat_front'] = p_coat_front

def p_hood(mat, face, w, h, cube, rng):
    rgb, alpha, glow = p_cloth(dict(mat, type='cloth', hem_shadow=False), face, w, h, cube, rng)
    if face == 'front' and w >= 6 and h >= 6:
        alpha = np.ones((h, w), np.float32)
        alpha[2:, 1:w - 1] = 0
        rgb[1, 1:w - 1] = ramp(mat['color'])[-2]
        acc = mat.get('accent')
        if acc:
            rgb[0, :] = ramp(acc)[0]
            rgb[:, 0] = ramp(acc)[0]
            rgb[:, -1] = ramp(acc)[0]
    elif face == 'bottom':
        alpha = np.zeros((h, w), np.float32)
    return rgb, alpha, glow

PAINTERS['hood'] = p_hood

def p_oilslick(mat, face, w, h, cube, rng):
    base = hexc(mat.get('color', '#1e1830'))
    hues = [hexc(c) for c in mat.get('hues', ['#c050e0', '#40c0d0', '#e060a0', '#6070f0'])]
    rgb = colorize(np.zeros((h, w), np.float32) + (1 if face == 'top' else 0), base)
    glow = np.zeros((h, w, 4), np.float32)
    seed = cube_seed(cube)
    for y in range(h):
        for x in range(w):
            k = (x * 2 + y * 3 + seed * 5) % 11
            if k < 2:
                col = hues[(x + y + seed) % len(hues)]
                rgb[y, x] = np.array(mix(base, col, 0.55 if k == 0 else 0.3), np.float32)
                if k == 0:
                    glow[y, x, :3] = col
                    glow[y, x, 3] = 110
    alpha = None
    if face in ('front', 'back', 'left', 'right') and h >= 3 and mat.get('drips', True):
        alpha = np.ones((h, w), np.float32)
        for x in range(w):
            if (x + seed) % 3 == 1:
                alpha[-1, x] = 0
    return jitter(rgb, rng, 0.03), alpha, glow

PAINTERS['oilslick'] = p_oilslick

def stack(*layers):
    return {'type': 'stack', 'color': layers[0][0]['color'], 'layers': list(layers)}

"""Faces, head sides and hair volume in the manner of Grimoire of Gaia's monster girls and Ice and Fire's people,
on the 8x8x8 head at 2 texels per pixel (16x16 per face).

What those mods do with a Minecraft head, and so what this does:
  * the vanilla layout is kept: hair over the top rows and down the sides, eyes on the middle rows, a small mouth;
  * eyes are the character: two to three pixels tall, a dark upper lash that flicks out at the outer corner, an iris
    that is dark at the top and light at the bottom, a pupil, one white catchlight on the same side of both eyes,
    a white of the eye only at the outer corner (none for big, glossy or monstrous eyes);
  * a thin brow a little darker than the hair, set by the expression (stern, calm, sad);
  * cheeks get a soft two-step blush; the face is lit from the top: a shade under the fringe and at the jaw;
  * hair is drawn as strands: a ramp of four tones running along the strands, darker roots and tips, an
    angel-ring highlight that breaks between strands, and the fringe ends in points, not a straight cut.
No noise, no gradients finer than a pixel step: every colour is a deliberate ramp step."""
import numpy as np
from colors import hexc, mix, shade, lum
import bbface as BF

N = 16
C = BF.C
ramp = BF.ramp

# fringe depth per column (rows of hair on the 16-row face), and a pointed tip pattern on top of it
FRINGE = {
    'bangs':  [6, 7, 6, 5, 6, 7, 6, 5, 5, 6, 7, 6, 5, 6, 7, 6],
    'blunt':  [6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6],
    'parted': [7, 7, 6, 5, 4, 3, 2, 2, 2, 2, 3, 4, 5, 6, 7, 7],
    'swept':  [7, 7, 7, 6, 6, 6, 5, 5, 4, 4, 3, 3, 3, 2, 3, 4],
    'messy':  [7, 5, 6, 3, 6, 7, 4, 6, 5, 7, 3, 6, 5, 7, 4, 6],
    'short':  [4, 3, 4, 3, 2, 3, 4, 3, 3, 4, 3, 2, 3, 4, 3, 4],
    'slick':  [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    'open':   [3, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 3],
    'none':   [0] * 16,
}

# Eye templates, viewer-left eye, outer corner first (column 0 is just outside the eye, for the lash flick).
# L lash, l light lash / lid shade, W white, D iris top, I iris, J iris bottom, P pupil, H catchlight, K glow core.
EYES = {
    'normal': ['.LLLL', 'LLDDD', '.WDPI', '.WIPJ', '..JJ.'],
    'big':    ['.LLLL', 'LDDDD', '.DIPI', '.IHPJ', '.JJJJ', '..ll.'],
    'calm':   ['.....', '.LLLL', 'LWDPD', '.WIPJ', '..JJ.'],
    'sharp':  ['LL...', '.LLLL', '.WDPD', '.WIJJ', '..l..'],
    'fierce': ['LL...', '.LLLL', '.WDPD', '.WIJJ', '..l..'],
    'sad':    ['...LL', '.LLLL', '.WDPD', '.WIPJ', '..JJ.'],
    'slit':   ['.LLLL', 'LDDPD', '.IIPI', '.JIPJ', '..JJ.'],
    'closed': ['.....', '.....', '.....', '.LLLL', 'L.ll.'],
    'lowered': ['.....', '.....', '.LLLL', 'LWDPD', '..JJ.'],
    'void':   ['.LLLL', 'LPPPP', '.PPKP', '.PPPP', '..PP.'],
    # men: smaller eyes, heavier lid line, no flick
    'man':        ['.LLLL', '.WDPD', '..IJ.'],
    'man_calm':   ['.llll', '.LLLL', '.WDPD'],
    'man_sharp':  ['LL...', '.LLLL', '.WDPD'],
    'man_slit':   ['.LLLL', '.DDPD', '.IJPJ'],
    'man_closed': ['.....', '.LLLL', '.....'],
    'man_void':   ['.LLLL', '.PPKP', '..PP.'],
    'man_sad':    ['..LLL', '.LLLL', '.WDPD'],
}
STYLE_MAN = {'normal': 'man', 'big': 'man', 'calm': 'man_calm', 'sharp': 'man_sharp', 'fierce': 'man_sharp', 'sad': 'man_sad',
             'slit': 'man_slit', 'closed': 'man_closed', 'lowered': 'man_calm', 'void': 'man_void'}
# top row of the eyes, and the brow row, by build
LAYOUT = {'woman': (7, 6), 'youth': (7, 6), 'child': (7, 6), 'man': (8, 7), 'large': (8, 7)}


def style_of(spec, build):
    s = spec.get('style', spec.get('eye_tpl', 'normal'))
    if spec.get('closed'):
        s = 'closed'
    if s not in EYES:
        s = 'normal'
    if build in ('man', 'large'):
        return STYLE_MAN.get(s, 'man')
    if build == 'child' and s == 'normal':
        return 'big'
    return s


def skin_ramp(skin):
    s = BF.warm(skin)
    S = C(s)
    # Gaia faces shade warm: the shadow steps lean to rose, not to grey
    rose = C(mix(s, '#c8506a', 0.28))
    return s, {'s': S, 's1': ramp(S, 0.95), 's2': (ramp(S, 0.88) * 0.7 + rose * 0.3), 's3': (ramp(S, 0.8) * 0.6 + rose * 0.4),
               'hl': ramp(S, 1.05)}


def hair_ramp(hair):
    """Four steps and a highlight. Light hair (white, silver, platinum, pastel) shades into a tinted cool colour
    instead of grey, as Gaia's white-haired girls do; dark hair lifts into a warm sheen."""
    H = C(hair)
    L = lum(hair)
    if L > 0.72:
        return {
            'h0': C(mix(hair, '#6a6898', 0.42)),
            'h1': C(mix(hair, '#a6a6d0', 0.32)),
            'h2': H,
            'h3': C(mix(hair, '#ffffff', 0.35)),
            'hl': C(mix(hair, '#ffffff', 0.75)),
        }
    dark = L < 0.3
    return {
        'h0': ramp(H, 0.62 if not dark else 0.72),
        'h1': ramp(H, 0.8),
        'h2': H,
        'h3': ramp(H, 1.12 if not dark else 1.28),
        'hl': C(mix(hair, '#ffffff', 0.42 if L < 0.6 else 0.62)),
    }


def locks(W, seed, wmin=3, wmax=4):
    """Column spans of hair locks across a face (3-4 texels each, a little irregular)."""
    rng = np.random.default_rng(seed)
    out, x = [], 0
    while x < W:
        w = int(rng.integers(wmin, wmax + 1))
        out.append((x, min(W, x + w)))
        x += w
    if len(out) > 1 and out[-1][1] - out[-1][0] < 2:
        a, _ = out.pop()
        out[-1] = (out[-1][0], W)
    return out


def strands(hair, H, W, seed, along='v', shine_row=None, tip=None):
    """Hair as locks: each lock 3-4 texels wide, lit in its middle and a step darker at its edges; along its length
    it is darker at the root and at the tip. A thin dark line parts neighbouring locks only in the lower half, where
    they separate. The angel ring is a two-row band that steps up and down between locks."""
    R = hair_ramp(hair)
    rng = np.random.default_rng(seed)
    out = np.zeros((H, W, 3), np.float32)
    for i, (a, b) in enumerate(locks(W, seed)):
        lift = int(rng.integers(-1, 2))
        w = b - a
        for y in range(H):
            t = (y + lift) / max(1, H - 1)
            core = 'h3' if 0.18 <= t < 0.5 else ('h2' if t < 0.86 else 'h1')
            if t < 0.08:
                core = 'h2'
            for x in range(a, b):
                edge = (x == a) or (x == b - 1 and w >= 3)
                k = core
                if edge:
                    k = {'h3': 'h2', 'h2': 'h1', 'h1': 'h1'}[core]
                out[y, x] = R[k]
        # parting line between locks, lower half only
        for y in range(H // 2, H):
            if (y + i) % 3 != 0:
                out[y, a] = (out[y, a] + R['h0']) / 2
    if shine_row is not None:
        for i, (a, b) in enumerate(locks(W, seed)):
            y = shine_row + (i % 2)
            for x in range(a + (1 if b - a >= 3 else 0), b - (1 if b - a >= 4 else 0)):
                if 0 <= y < H:
                    out[y, x] = R['hl']
                if 0 <= y + 1 < H:
                    out[y + 1, x] = (out[y + 1, x] + R['hl']) / 2
    if tip:
        T = C(tip)
        for y in range(H):
            w = np.clip((y / max(1, H - 1) - 0.5) / 0.5, 0, 1)
            w = np.round(w * 3) / 3
            out[y] = out[y] * (1 - w) + T * w
    return out


def fringe_cut(bangs, seed=21):
    """Fringe depth per column: the style's line, with every lock ending in a point (deepest in its middle)."""
    base = list(FRINGE.get(bangs, FRINGE['bangs']))
    if bangs in ('none', 'slick', 'open'):
        return base
    out = base[:]
    for a, b in locks(N, seed):
        mid = (a + b - 1) / 2
        for x in range(a, b):
            d = abs(x - mid)
            out[x] = max(0, base[x] - (1 if d >= 1.0 else 0) + (1 if d < 0.6 else 0))
    return out


def face(spec, skin, hair, build='woman', bangs='bangs'):
    """(rgb 16x16x3, glow 16x16x4 or None) for the front of the head."""
    s, T = skin_ramp(skin)
    man = build in ('man', 'large')
    rgb = np.tile(T['s'], (N, N, 1)).astype(np.float32)
    glow = np.zeros((N, N, 4), np.float32)
    # light from the top: forehead a touch lighter, jaw and outer columns a step darker, chin corners two
    rgb[6:9, 3:13] = T['hl']
    rgb[:, 0] = rgb[:, 15] = T['s1']
    rgb[12:, 1] = rgb[12:, 14] = T['s1']
    rgb[14:, 0] = rgb[14:, 15] = T['s2']
    rgb[15, 1:15] = T['s1']
    rgb[15, 0] = rgb[15, 15] = T['s3']
    # hair over the top rows, pointed fringe
    fr = fringe_cut(bangs)
    hr = strands(hair, N, N, 21, shine_row=1)
    R = hair_ramp(hair)
    for x in range(N):
        d = fr[x]
        rgb[:d, x] = hr[:d, x]
        if d > 0:
            rgb[d - 1, x] = R['h1'] if d > 2 else rgb[d - 1, x]
        if d < N:
            rgb[d, x] = T['s2']                       # shadow under the fringe
            if d + 1 < N:
                rgb[d + 1, x] = np.minimum(rgb[d + 1, x], T['s1'])
    if spec.get('veil'):
        vc = C(spec['veil'])
        for y in range(6, N):
            for x in range(N):
                rgb[y, x] = ramp(vc, 1.06 if y == 6 else (0.92 if x in (0, 15) else (0.97 if y % 4 == 3 else 1.0)))
        ey = C(spec.get('veil_eyes', '#ffcf6a'))
        for y in (9, 10):
            for x in (3, 4, 11, 12):
                rgb[y, x] = ey
                glow[y, x, :3] = ey
                glow[y, x, 3] = 255
        return rgb, glow
    style = style_of(spec, build)
    top, brow_row = LAYOUT.get(build, LAYOUT['woman'])
    tpl = EYES[style]
    iris = spec.get('iris', '#5a3a2a')
    iris_r = spec.get('heterochromia') or iris
    lash = C(spec.get('line') or mix(shade(hair, 0.32), '#1a1020', 0.7))
    lidc = T['s3']
    glow_eyes = bool(spec.get('glow_eyes'))
    for side, ic in ((0, iris), (1, iris_r)):
        iris2 = spec.get('iris2') or '#%02x%02x%02x' % shade(ic, 1.35)
        pal = {
            'L': lash, 'l': lidc, 'W': C('#f7f5fb'),
            'D': C(mix(shade(ic, 0.55), '#180c20', 0.25)), 'I': C(ic), 'J': C(mix(shade(ic, 1.25), iris2, 0.45)),
            'P': C(mix(shade(ic, 0.3), '#0c0610', 0.55)), 'H': C('#ffffff'), 'K': C(mix(iris2, '#ffffff', 0.35)),
        }
        cells = []
        for r, line in enumerate(tpl):
            for c, code in enumerate(line):
                if code == '.':
                    continue
                x = 1 + c if side == 0 else 14 - c
                cells.append((top + r, x, code))
        for y, x, code in cells:
            if 0 <= y < N:
                rgb[y, x] = pal[code]
                if glow_eyes and code in ('I', 'J', 'K', 'H', 'D'):
                    glow[y, x, :3] = pal[code] if code != 'D' else pal['I']
                    glow[y, x, 3] = 255 if code != 'D' else 180
                if code == 'K':
                    glow[y, x, :3] = pal['K']
                    glow[y, x, 3] = 255
        # catchlight: the same (upper, viewer-left) corner of both irises, so the eyes never look crossed
        if style not in ('closed', 'man_closed', 'void', 'man_void') and 'H' not in ''.join(tpl):
            irows = [(y, x) for y, x, code in cells if code in ('D', 'I')]
            if irows:
                y0 = min(y for y, _ in irows)
                xs = sorted(x for y, x in irows if y == y0 + (1 if len(tpl) > 3 else 0))
                if xs:
                    hx = xs[0]
                    rgb[y0 + (1 if len(tpl) > 3 else 0), hx] = pal['H']
    # brows
    # brows: girls get a faint, short one (Gaia's girls barely show them); stern and sad faces and men a clear one
    stern = style in ('sharp', 'fierce', 'sad', 'slit') or man
    bc = C(mix(shade(hair, 0.55 if lum(hair) > 0.45 else 0.9), s, 0.22 if stern else 0.55))
    if True:
        brow = {
            'normal': [(0, 2), (0, 3), (0, 4)], 'big': [(0, 2), (0, 3), (0, 4)],
            'calm': [(0, 2), (0, 3), (0, 4)], 'lowered': [(1, 2), (1, 3), (1, 4)],
            'sharp': [(-1, 1), (0, 2), (0, 3), (1, 4)], 'fierce': [(-1, 1), (-1, 2), (0, 3), (1, 4), (1, 5)],
            'sad': [(1, 1), (0, 2), (-1, 3), (-1, 4)], 'slit': [(-1, 1), (0, 2), (0, 3), (1, 4)],
            'closed': [(0, 2), (0, 3), (0, 4)], 'void': [(0, 2), (0, 3), (0, 4)],
            'man': [(0, 1), (0, 2), (0, 3), (0, 4)], 'man_calm': [(0, 1), (0, 2), (0, 3), (0, 4)],
            'man_sharp': [(-1, 1), (0, 2), (0, 3), (1, 4), (1, 5)], 'man_slit': [(-1, 1), (0, 2), (0, 3), (1, 4)],
            'man_closed': [(0, 1), (0, 2), (0, 3), (0, 4)], 'man_void': [(0, 2), (0, 3), (0, 4)],
            'man_sad': [(1, 1), (0, 2), (-1, 3), (-1, 4)],
        }.get(style, [(0, 2), (0, 3), (0, 4)])
        if not stern:
            brow = [(dy - 1, dx) for dy, dx in brow if dx in (3, 4)]
        for dy, dx in brow:
            for side in (0, 1):
                x = dx if side == 0 else 15 - dx
                y = brow_row + dy
                if 0 <= y < N and y >= fr[x]:          # hidden under the fringe
                    rgb[y, x] = bc
                    if man and y + 1 < N and dx in (2, 3):
                        rgb[y + 1, x] = (rgb[y + 1, x] * 0.5 + bc * 0.5)
    # cheeks: two-step blush (always a faint one on girls, stronger with 'blush')
    if not man:
        strong = bool(spec.get('blush'))
        b1 = C(mix(s, '#ff5c78', 0.34 if strong else 0.16))
        b2 = C(mix(s, '#ff5c78', 0.2 if strong else 0.08))
        by = top + len(tpl)
        for x in (2, 3, 12, 13):
            if by < N:
                rgb[by, x] = b1
        for x in (1, 4, 11, 14):
            if by < N:
                rgb[by, x] = b2
        if strong and by + 1 < N:
            for x in (2, 3, 12, 13):
                rgb[by + 1, x] = b2
    else:
        # men: a nose shadow and a jaw line
        rgb[11, 8] = T['s2']
        rgb[12, 7] = T['s1']
    marks = spec.get('marks')
    if marks:
        if isinstance(marks, (list, tuple)) and 'forehead' in marks:
            mc = C(spec.get('iris2') or spec.get('iris', '#ffffff'))
            for y, x in ((4, 7), (4, 8), (3, 7), (5, 8)):
                rgb[y, x] = mc
                glow[y, x, :3] = mc
                glow[y, x, 3] = 255
        else:
            mc = C(marks if isinstance(marks, str) else '#a03040')
            for y, x in ((12, 2), (12, 3), (13, 2), (12, 12), (12, 13), (13, 13)):
                rgb[y, x] = mc
                glow[y, x, :3] = mc
                glow[y, x, 3] = 200
    # mouth
    mouth = spec.get('mouth') or 'small'
    lip = C(mix(shade(s, 0.82), '#d04a64', 0.35)) if not man else C(shade(s, 0.7))
    dark = C('#5a1c2c')
    my = 13
    if mouth != 'none':
        if mouth == 'smile':
            for y, x in ((my, 6), (my + 1, 7), (my + 1, 8), (my, 9)):
                rgb[y, x] = lip
        elif mouth == 'smirk':
            for y, x in ((my, 8), (my, 9), (my - 1, 10)):
                rgb[y, x] = lip
        elif mouth in ('grin', 'open'):
            rgb[my, 6:10] = lip
            rgb[my + 1, 7:9] = dark
            if mouth == 'grin':
                rgb[my, 7:9] = C('#f6f2ee')
        elif mouth == 'fang':
            rgb[my, 6:10] = lip
            rgb[my + 1, 8] = C('#fbfaf7')
            rgb[my + 1, 7] = dark
        else:
            rgb[my, 7:9] = lip
    if spec.get('scar'):
        sc = C(mix(shade(s, 0.7), '#8a2a2a', 0.4))
        for y, x in ((5, 4), (6, 4), (7, 3), (8, 3), (9, 2), (10, 2), (11, 1)):
            rgb[y, x] = sc
    gl = spec.get('glasses')
    if gl:
        g = C(gl)
        for side in (0, 1):
            x0 = 1 if side == 0 else 10
            for x in range(x0, x0 + 5):
                rgb[top, x] = g
                rgb[top + len(tpl) - 1, x] = g
            for y in range(top, top + len(tpl)):
                rgb[y, x0] = g
                rgb[y, x0 + 4] = g
        rgb[top + 1, 6:10] = g
    mono = spec.get('monocle')
    if mono:
        g = C(mono)
        for y, x in ((top - 1, 11), (top - 1, 12), (top - 1, 13), (top, 14), (top + 1, 14), (top + 2, 14),
                     (top + 3, 13), (top + 3, 12), (top + 3, 11), (top, 10), (top + 1, 10), (top + 2, 10),
                     (top + 4, 14), (top + 5, 14), (top + 6, 15), (top + 7, 15)):
            if 0 <= y < N:
                rgb[y, x] = g
    return rgb, (glow if glow[..., 3].any() else None)


def lids(spec, skin, hair, build='woman'):
    """Blink layer: skin over the eye rows and the lash line lowered to the bottom, as rgba."""
    rgba = np.zeros((N, N, 4), np.float32)
    style = style_of(spec, build)
    if spec.get('veil') or style in ('closed', 'man_closed', 'void', 'man_void'):
        return rgba
    s, T = skin_ramp(skin)
    top, _ = LAYOUT.get(build, LAYOUT['woman'])
    tpl = EYES[style]
    lash = C(spec.get('line') or mix(shade(hair, 0.32), '#1a1020', 0.7))
    rows = len(tpl)
    for side in (0, 1):
        for r in range(rows):
            for c in range(5):
                if tpl[r][c] == '.' and not (r == rows - 1 and 1 <= c <= 4):
                    continue
                x = 1 + c if side == 0 else 14 - c
                rgba[top + r, x, :3] = T['s']
                rgba[top + r, x, 3] = 255
        y = top + rows - 2
        for c in range(1, 5):
            x = 1 + c if side == 0 else 14 - c
            rgba[y, x, :3] = lash
        rgba[y - 1, (1 if side == 0 else 14), :3] = T['s1']
    return rgba


def head_side(face_name, skin, hair):
    s, T = skin_ramp(skin)
    seed = {'top': 5, 'back': 6, 'left': 7, 'right': 8}.get(face_name, 9)
    if face_name == 'top':
        R = hair_ramp(hair)
        out = strands(hair, N, N, seed)
        out[7:9, :] = (out[7:9, :] + R['h0']) / 2       # the parting
        return out
    if face_name == 'back':
        return strands(hair, N, N, seed, shine_row=2)
    if face_name == 'bottom':
        return np.tile(T['s2'], (N, N, 1))
    rgb = np.tile(T['s'], (N, N, 1)).astype(np.float32)
    hr = strands(hair, N, N, seed, shine_row=1)
    rgb[:4] = hr[:4]
    back = slice(0, 8) if face_name == 'right' else slice(8, 16)
    rgb[:, back] = hr[:, back]
    rgb[N - 1] = np.where((rgb[N - 1] == T['s']).all(-1)[:, None], T['s1'], rgb[N - 1])
    # ear: a two-step shaded square in front of the hair
    ex = slice(5, 8) if face_name == 'right' else slice(8, 11)
    rgb[8:11, ex] = T['s1']
    rgb[9, ex] = T['s2']
    return rgb


def shell(face_name, hair, bangs='bangs', long_sides=True, back_long=True, ears_open=False, man=False, shine_on=True, tip=None):
    """Hat layer (hair volume) for one face of the head: strands with pointed ends, rgba."""
    a = np.zeros((N, N), np.float32)
    if face_name == 'top':
        a[:] = 1
    elif face_name == 'bottom':
        return np.zeros((N, N, 4), np.float32)
    elif face_name == 'front':
        cov = [max(0, d - 1) for d in fringe_cut(bangs)]
        if long_sides:
            for x in (0, 1, 14, 15):
                cov[x] = max(cov[x], 14 if x in (0, 15) else 12)
        for x in range(N):
            a[:cov[x], x] = 1
    elif face_name == 'back':
        if back_long:
            a[:] = 1
            for x in range(N):                        # pointed ends
                if x % 3 == 1:
                    a[N - 1, x] = 0
        else:
            jag = ([11, 13, 12, 13, 11, 12, 13, 12, 11, 13, 12, 13, 11, 12, 13, 12] if not man
                   else [9, 11, 10, 11, 9, 10, 11, 10, 9, 11, 10, 11, 9, 10, 11, 10])
            for x in range(N):
                a[:jag[x], x] = 1
    else:
        front_first = face_name == 'left'
        for x in range(N):
            fx = x if front_first else N - 1 - x
            if long_sides:
                h = N - (1 if fx % 3 == 0 else 0)
            else:
                h = (6 if fx < 6 else (9 if fx < 12 else 11)) if man else (8 if fx < 6 else (11 if fx < 12 else 13))
            a[:h, x] = 1
            if ears_open and 5 <= fx <= 9:
                a[6:11, x] = 0
    rgb = strands(hair, N, N, {'front': 11, 'back': 12, 'left': 13, 'right': 14, 'top': 15}[face_name],
                  shine_row=(2 if shine_on and face_name != 'top' else None), tip=(tip if face_name != 'top' else None))
    out = np.zeros((N, N, 4), np.float32)
    out[..., :3] = rgb
    out[..., 3] = a * 255
    return out

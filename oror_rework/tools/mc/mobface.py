"""Faces in the manner of the monster-girl and maid mods' characters (Grimoire of Gaia, Touhou Little Maid, the
anime player skins the user sent, 059g): the user found the 0.17.27 faces' eyes and mouths odd ("口や目とかがすごい
違和感あった"): eyes drawn at half a pixel (a white, an iris, a pupil and a catchlight in a five-texel eye), a
pink two-lipped mouth and a nose shadow on an 8-pixel face.

What those mods draw on an 8x8 face, and so what this draws (16 x 16 texels, every feature on the 2 x 2 grid of
the 8x8 face, so it reads as one Minecraft pixel):
  * eyes two pixels wide on rows 3 to 5 (three tall for girls and children, two for men): a dark lash row on top
    that flicks out at the outer corner for a sharp look, the iris darker at the top, a full white highlight pixel
    at the outer top (the maid mod's look) or none for calm, sleepy and monstrous eyes; no white of the eye for
    girls, the vanilla white-and-iris pair for men;
  * no nose and no mouth (the user: "口が特に余計");
  * a pink blush pixel under each eye; brows only on men and stern or sad faces, one row above the eyes;
  * the hair's fringe from gaiaface (strands, points, shine), never below row 3.
Each of the 41 is told apart by its eye: shape (round, big, calm, sleepy, sharp, fierce, sad, slit, void, closed),
colour, glow, two colours, marks, glasses, veil; set in the recipes' face specs (chars3d) and FACE_KEYS below.
"""
import numpy as np
from colors import hexc, mix, shade, lum
import gaiaface as GF

N = 16
C = GF.C
ramp = GF.ramp

# Eyes on the 8x8 grid, the viewer-left eye: three columns (the outer corner's flick, the outer and the inner
# column of the eye), rows from the eye's top row down. L lash, l lid shade, D iris top, I iris, J iris light,
# H highlight (white), W white of the eye, P pupil / void, K glow core, S slit (iris with a dark texel line).
EYES = {
    'round':   ['.LL', '.HD', '.IJ'],
    'big':     ['LLL', '.HD', '.JI'],
    'calm':    ['...', '.LL', '.DI'],
    'sleepy':  ['...', '.ll', '.LL'],
    'sharp':   ['L..', '.LL', '.HD'],
    'fierce':  ['L..', '.LL', '.DD'],
    'sad':     ['...', '.LL', '.HD'],
    'slit':    ['.LL', '.SS', '.SS'],
    'void':    ['.LL', '.PP', '.PK'],
    'closed':  ['...', '...', '.LL'],
    'lowered': ['...', '.LL', '.DJ'],
    # men: two rows, the vanilla skins' white and iris
    'man':        ['.LL', '.WI'],
    'man_calm':   ['.ll', '.WI'],
    'man_sharp':  ['L.L', '.WD'],
    'man_slit':   ['.LL', '.SS'],
    'man_closed': ['...', '.LL'],
    'man_void':   ['.LL', '.PK'],
    'man_sad':    ['..L', '.WI'],
}
# the 0.17.27 styles (gaiaface) mapped onto these
STYLE = {'normal': 'round', 'big': 'big', 'calm': 'calm', 'sharp': 'sharp', 'fierce': 'fierce', 'sad': 'sad',
         'slit': 'slit', 'closed': 'closed', 'lowered': 'lowered', 'void': 'void', 'sleepy': 'sleepy', 'round': 'round'}
STYLE_MAN = {'round': 'man', 'big': 'man', 'calm': 'man_calm', 'sleepy': 'man_calm', 'sharp': 'man_sharp',
             'fierce': 'man_sharp', 'sad': 'man_sad', 'slit': 'man_slit', 'closed': 'man_closed', 'lowered': 'man_calm',
             'void': 'man_void'}
# the eyes' top row on the 8x8 grid (girls' three-row eyes from row 3, men's two-row from row 4)
TOP = {'woman': 3, 'youth': 3, 'child': 3, 'man': 4, 'large': 4}


def style_of(spec, build):
    s = spec.get('shape') or STYLE.get(spec.get('style', spec.get('eye_tpl', 'normal')), 'round')
    if spec.get('closed'):
        s = 'closed'
    if build in ('man', 'large'):
        return s if s.startswith('man') else STYLE_MAN.get(s, 'man')
    if s.startswith('man'):
        s = 'round'
    return s if s in EYES else 'round'


def cell(rgb, ly, lx, col):
    """One pixel of the 8x8 face: 2 x 2 texels."""
    if 0 <= ly < 8 and 0 <= lx < 8:
        rgb[2 * ly:2 * ly + 2, 2 * lx:2 * lx + 2] = col


def gcell(glow, ly, lx, col, a=255):
    if 0 <= ly < 8 and 0 <= lx < 8:
        glow[2 * ly:2 * ly + 2, 2 * lx:2 * lx + 2, :3] = col
        glow[2 * ly:2 * ly + 2, 2 * lx:2 * lx + 2, 3] = a


def eye_x(side, c):
    """Grid column of template column c (0 the outer flick) for the viewer-left (0) or right (1) eye."""
    return c if side == 0 else 7 - c


def small_eyes(rgb, glow, spec, hair, top_texel, man):
    """(059g, the user: "目も大きすぎる") eyes four texels wide and three tall: a one-texel lash, two of iris with
    a single white catchlight; men's a white and an iris pixel under the lash."""
    iris = spec.get('iris', '#5a3a2a')
    iris_r = spec.get('heterochromia') or iris
    lash = C(spec.get('line') or mix(shade(hair, 0.3), '#160c1a', 0.75))
    shape = spec.get('shape') or spec.get('style', 'normal')
    for side, ic in ((0, iris), (1, iris_r)):
        x0 = 2 if side == 0 else 10                         # the eye's four columns
        dark = C(mix(shade(ic, 0.6), '#1a0c22', 0.2))
        I = C(ic)
        y = top_texel
        if shape in ('closed',):
            rgb[y + 2, x0:x0 + 4] = lash
            continue
        rgb[y, x0:x0 + 4] = lash
        if shape in ('sharp', 'fierce', 'slit'):
            rgb[y - 1, (x0 if side == 0 else x0 + 3)] = lash          # the outer corner flicked up
        if man:
            rgb[y + 1:y + 3, x0:x0 + 4] = I
            rgb[y + 1:y + 3, (x0 if side == 0 else x0 + 2):(x0 + 2 if side == 0 else x0 + 4)] = C('#f2f0f6')
        else:
            rgb[y + 1, x0:x0 + 4] = dark
            rgb[y + 2, x0:x0 + 4] = I
            if shape not in ('calm', 'sad', 'void', 'lowered'):
                rgb[y + 1, x0 + (1 if side == 0 else 2)] = C('#ffffff')
        if shape == 'slit':
            rgb[y + 1:y + 3, x0 + (2 if side == 0 else 1)] = C('#0c0610')
        if spec.get('glow_eyes'):
            glow[y + 1:y + 3, x0:x0 + 4, :3] = I
            glow[y + 1:y + 3, x0:x0 + 4, 3] = 230


def face(spec, skin, hair, build='woman', bangs='bangs'):
    """(rgb 16x16x3, glow 16x16x4 or None) for the front of the head."""
    s, T = GF.skin_ramp(skin)
    man = build in ('man', 'large')
    rgb = np.tile(T['s'], (N, N, 1)).astype(np.float32)
    glow = np.zeros((N, N, 4), np.float32)
    # flat skin, lit from the top: the jaw's outer pixels a step darker, the chin's corners two
    # (059g) flat skin: no shading at the jaw or the cheeks' corners (the references' faces are one tone)
    # hair: gaiaface's strands and pointed fringe, never past row 3 of the 8x8 face (texel 6)
    fr = [min(d, 6) for d in GF.fringe_cut(bangs)]
    hr = GF.strands(hair, N, N, 21, shine_row=1)
    R = GF.hair_ramp(hair)
    for x in range(N):
        d = fr[x]
        rgb[:d, x] = hr[:d, x]
        if d > 2:
            rgb[d - 1, x] = R['h1']
        if d < N:
            rgb[d, x] = T['s1']                        # the fringe's shadow on the brow
    if spec.get('veil'):
        vc = C(spec['veil'])
        for y in range(6, N):
            for x in range(N):
                rgb[y, x] = ramp(vc, 1.06 if y == 6 else (0.92 if x in (0, 15) else (0.97 if y % 4 == 3 else 1.0)))
        ey = C(spec.get('veil_eyes', '#ffcf6a'))
        for side in (0, 1):
            cell(rgb, 4, eye_x(side, 2), ey)
            gcell(glow, 4, eye_x(side, 2), ey)
        return rgb, glow
    style = style_of(spec, build)
    tpl = EYES[style]
    top = TOP.get(build, 3) + int(spec.get('eye_drop', 0))
    if len(tpl) == 2 and not man:
        top += 1
    iris = spec.get('iris', '#5a3a2a')
    iris_r = spec.get('heterochromia') or iris
    lash = C(spec.get('line') or mix(shade(hair, 0.3), '#160c1a', 0.75))
    lid = T['s2']
    glow_eyes = bool(spec.get('glow_eyes'))
    highlight = spec.get('highlight', True)
    small_eyes(rgb, glow, spec, hair, 2 * top + (2 if not man else 0), man)
    for side, ic in (() if True else ((0, iris), (1, iris_r))):
        light = spec.get('iris2') or '#%02x%02x%02x' % shade(ic, 1.4)
        pal = {
            'L': lash, 'l': lid, 'W': C('#f6f4fa'),
            'D': C(mix(shade(ic, 0.62), '#1a0c22', 0.2)), 'I': C(ic), 'J': C(mix(ic, light, 0.55)),
            'P': C(mix(shade(ic, 0.25), '#08040c', 0.6)), 'H': C('#ffffff') if highlight else C(ic),
            'K': C(mix(light, '#ffffff', 0.3)), 'S': C(ic),
        }
        for r, line in enumerate(tpl):
            for c, code in enumerate(line):
                if code == '.':
                    continue
                ly, lx = top + r, eye_x(side, c)
                col = pal[code]
                if code == 'S' and r == len(tpl) - 1:
                    col = pal['J']
                cell(rgb, ly, lx, col)
                if glow_eyes and code in ('I', 'J', 'D', 'H', 'K', 'S'):
                    gcell(glow, ly, lx, pal['I'] if code in ('D', 'H') else col, 200 if code == 'D' else 255)
                if code == 'K':
                    gcell(glow, ly, lx, pal['K'])
        # a slit pupil: the texel line between the eye's two columns, dark, down the iris rows
        if 'S' in ''.join(tpl):
            x = 2 * eye_x(side, 2) + (0 if side == 0 else 1)
            for r, line in enumerate(tpl):
                if 'S' in line:
                    rgb[2 * (top + r):2 * (top + r) + 2, x] = pal['P']
                    glow[2 * (top + r):2 * (top + r) + 2, x, 3] = 0
    # brows: men, and stern or sad girls; a row above the eyes, in the hair's dark tone (hidden under the fringe)
    stern = style in ('sharp', 'fierce', 'sad', 'man_sharp', 'man_sad') or man
    if stern or spec.get('brows'):
        bc = C(mix(shade(hair, 0.5 if lum(hair) > 0.45 else 0.85), lash, 0.35))
        by = top - 1 if tpl[0].strip('.') else top
        for side in (0, 1):
            for c in (1, 2):
                lx = eye_x(side, c)
                ly = by
                if style in ('sad', 'man_sad') and c == 1:
                    ly += 0                                   # the outer end down, the inner up (texel step below)
                if 2 * ly >= fr[2 * lx] and 2 * ly >= fr[2 * lx + 1]:
                    # a brow is a single texel row: the lower half of the pixel above the eye
                    y = 2 * ly + 1
                    if style in ('fierce', 'sharp', 'man_sharp'):
                        y = 2 * ly + (1 if c == 1 else 0) if side == 0 else 2 * ly + (1 if c == 1 else 0)
                        y = 2 * ly + (0 if c == 1 else 1)
                    elif style in ('sad', 'man_sad'):
                        y = 2 * ly + (1 if c == 1 else 0)
                    rgb[y, 2 * lx:2 * lx + 2] = bc
    # blush: a pink pixel under each eye's outer column (faint on every girl, stronger with 'blush')
    eye_bottom = top + len(tpl)
    # (059g, the user: "ほっぺも見直し 画像みたいなのにして") no blush: the references' cheeks are plain skin
    if spec.get('blush_force'):
        strong = bool(spec.get('blush'))
        b = C(mix(s, '#ff5c80', 0.42 if strong else 0.22))
        for side in (0, 1):
            lx = eye_x(side, 1)
            if strong:
                cell(rgb, eye_bottom, lx, b)
            else:
                rgb[2 * eye_bottom, 2 * lx:2 * lx + 2] = b
    # marks: a jewel on the brow, or two marks on the cheeks
    marks = spec.get('marks')
    if marks:
        if isinstance(marks, (list, tuple)) and 'forehead' in marks:
            mc = C(spec.get('iris2') or spec.get('iris', '#ffffff'))
            rgb[4:6, 7:9] = mc
            glow[4:6, 7:9, :3] = mc
            glow[4:6, 7:9, 3] = 255
        else:
            # a mark down each cheek from the eye's outer corner (a line, not a blush)
            mc = C(marks if isinstance(marks, str) else '#a03040')
            for side in (0, 1):
                x = 2 * eye_x(side, 1) + (0 if side == 0 else 1)
                for y in range(2 * eye_bottom, min(N, 2 * eye_bottom + 3)):
                    rgb[y, x] = mc
                    glow[y, x, :3] = mc
                    glow[y, x, 3] = 200
    # mouth: none on most faces (as the references); else one pixel, never a lip
    # (059g, the user: "口が特に余計") no mouth on any face, as the user's references and design sheets
    mouth = spec.get('mouth_force') or 'none'
    dark = C(mix(shade(s, 0.45), '#3a0c18', 0.45))
    soft = C(mix(shade(s, 0.72), '#a03048', 0.25))
    my = 13
    if mouth == 'smile':
        rgb[my, 7:9] = soft
    elif mouth == 'smirk':
        rgb[my, 8:10] = soft
    elif mouth == 'grin':
        # a wide grin: a dark line with its corners turned up (one texel each), no teeth
        w0, w1 = (5, 11) if man else (6, 10)
        rgb[my, w0:w1] = dark
        rgb[my - 1, w0 - 1] = rgb[my - 1, w1] = dark
    elif mouth == 'open':
        rgb[my:my + 2, 7:9] = dark
    elif mouth == 'fang':
        rgb[my, 7:9] = soft
        rgb[my + 1, 8] = C('#fbfaf6')
    elif mouth == 'line':
        rgb[my, 6:10] = C(shade(s, 0.78))
    elif mouth == 'pout':
        rgb[my, 7:9] = C(mix(s, '#c04060', 0.3))
    if spec.get('scar'):
        sc = C(mix(shade(s, 0.7), '#8a2a2a', 0.4))
        for y, x in ((6, 4), (7, 4), (8, 3), (9, 3), (10, 2), (11, 2), (12, 1)):
            rgb[y, x] = sc
    gl = spec.get('glasses')
    if gl:
        g = C(gl)
        for side in (0, 1):
            x0 = 2 * eye_x(side, 2 if side == 1 else 1) - 1
            x1 = x0 + 5
            y0, y1 = 2 * top - 1 + (2 if len(tpl) == 3 else 0), 2 * eye_bottom
            for x in range(max(0, x0), min(N, x1 + 1)):
                rgb[y0, x] = g
                rgb[min(N - 1, y1), x] = g
            for y in range(y0, min(N, y1 + 1)):
                if 0 <= x0 < N:
                    rgb[y, x0] = g
                if 0 <= x1 < N:
                    rgb[y, x1] = g
        rgb[2 * top + 1 + (2 if len(tpl) == 3 else 0), 7:9] = g
    mono = spec.get('monocle')
    if mono:
        g = C(mono)
        x0, y0 = 2 * eye_x(1, 2) - 1, 2 * top - 1 + (2 if len(tpl) == 3 else 0)
        for x in range(x0, min(N, x0 + 6)):
            rgb[y0, x] = g
            rgb[min(N - 1, y0 + 5), x] = g
        for y in range(y0, min(N, y0 + 6)):
            rgb[y, x0] = g
            rgb[y, min(N - 1, x0 + 5)] = g
        for y in range(y0 + 6, N):
            rgb[y, min(N - 1, x0 + 5)] = g
    return rgb, (glow if glow[..., 3].any() else None)


def lids(spec, skin, hair, build='woman'):
    """Blink layer: skin over the eyes, the lash line at the eye's bottom row, as rgba."""
    rgba = np.zeros((N, N, 4), np.float32)
    style = style_of(spec, build)
    if spec.get('veil') or style in ('closed', 'man_closed', 'void', 'man_void'):
        return rgba
    s, T = GF.skin_ramp(skin)
    man = build in ('man', 'large')
    tpl = EYES[style]
    top = TOP.get(build, 3) + int(spec.get('eye_drop', 0))
    if len(tpl) == 2 and not man:
        top += 1
    lash = C(spec.get('line') or mix(shade(hair, 0.3), '#160c1a', 0.75))
    rows = len(tpl)
    for side in (0, 1):
        for r in range(rows):
            for c in range(3):
                if tpl[r][c] == '.':
                    continue
                lx, ly = eye_x(side, c), top + r
                rgba[2 * ly:2 * ly + 2, 2 * lx:2 * lx + 2, :3] = T['s']
                rgba[2 * ly:2 * ly + 2, 2 * lx:2 * lx + 2, 3] = 255
        ly = top + rows - 1
        for c in (1, 2):
            lx = eye_x(side, c)
            rgba[2 * ly, 2 * lx:2 * lx + 2, :3] = lash
            rgba[2 * ly, 2 * lx:2 * lx + 2, 3] = 255
    return rgba


head_side = GF.head_side
shell = GF.shell

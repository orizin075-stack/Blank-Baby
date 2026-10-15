"""8x8 Minecraft-skin faces (one texel per model unit), in the style of anime player skins and
Touhou Little Maid models: hair frames the face, 2x2 eyes with a white outer column and an iris
column (dark on top, colour below), tiny or no mouth, soft chin shadow.

Eyes are written for the viewer-left eye (columns 1-2, outer column first) and mirrored."""
from colors import hexc, mix, shade

# rows 4 and 5 (and an optional row 3 accent): two characters each = outer, inner column
EYES = {
    'girl':     {3: '..', 4: 'WD', 5: 'WI'},
    'lash':     {3: 'LL', 4: 'WD', 5: 'WI'},
    'big':      {3: 'LL', 4: 'DD', 5: 'IJ'},
    'calm':     {4: 'LL', 5: 'WI'},
    'sharp':    {3: 'L.', 4: 'WL', 5: 'WI'},
    'fierce':   {3: '.L', 4: 'WD', 5: 'WI'},
    'sad':      {3: 'L.', 4: 'WD', 5: 'WI'},
    'slit':     {4: 'DP', 5: 'JP'},
    'closed':   {5: 'LL'},
    'lowered':  {4: 'LL', 5: 'DI'},
    'void':     {4: 'PP', 5: 'PK'},
    'man':      {3: 'BB', 4: 'WI'},
    'man_sharp':{3: '.B', 4: 'WI'},
    'man_calm': {3: 'BB', 4: 'LI'},
    'child':    {4: 'DD', 5: 'IJ'},
}

STYLE = {
    'woman': {'normal': 'girl', 'big': 'big', 'glint': 'lash', 'calm': 'calm', 'sharp': 'sharp', 'fierce': 'fierce',
              'sad': 'sad', 'slit': 'slit', 'lowered': 'lowered', 'void': 'void', 'closed': 'closed'},
    'man':   {'normal': 'man', 'big': 'man', 'glint': 'man', 'calm': 'man_calm', 'sharp': 'man_sharp', 'fierce': 'man_sharp',
              'sad': 'man', 'slit': 'slit', 'lowered': 'man_calm', 'void': 'void', 'closed': 'closed'},
    'child': {'normal': 'child', 'big': 'child', 'glint': 'child', 'calm': 'calm', 'sharp': 'sharp', 'fierce': 'fierce',
              'sad': 'sad', 'slit': 'slit', 'lowered': 'lowered', 'void': 'void', 'closed': 'closed'},
}
STYLE['large'] = STYLE['man']
STYLE['youth'] = STYLE['man']

# mouth pixels: (row, col, code) on the 8x8 face
MOUTHS = {
    'none':  [],
    'small': [(7, 4, 'm')],
    'soft':  [(7, 3, 'm'), (7, 4, 'm')],
    'smile': [(6, 2, 'm'), (7, 3, 'M'), (7, 4, 'M'), (6, 5, 'm')],
    'open':  [(6, 3, 'M'), (6, 4, 'M'), (7, 3, 'R'), (7, 4, 'R')],
    'grin':  [(7, 2, 'm'), (7, 3, 'T'), (7, 4, 'T'), (7, 5, 'm')],
    'fang':  [(7, 3, 'M'), (7, 4, 'T')],
    'frown': [(7, 3, 'M'), (7, 4, 'M'), (6, 3, 'm'), (6, 4, 'm')],
    'flat':  [(7, 3, 'M'), (7, 4, 'M')],
    'cat':   [(7, 2, 'm'), (6, 3, 'M'), (6, 4, 'M'), (7, 5, 'm')],
    'smirk': [(7, 3, 'M'), (6, 4, 'm')],
}

def resolve(build, spec):
    req = spec.get('style', spec.get('eye_tpl', 'normal'))
    if spec.get('closed'):
        req = 'closed'
    return STYLE.get(build, STYLE['woman']).get(req, req if req in EYES else 'girl')

def default_mouth(build, spec):
    m = spec.get('mouth')
    if m is None:
        return 'small' if build in ('man', 'large', 'youth') else 'none'
    if m in ('small',) and build not in ('man', 'large', 'youth'):
        return 'none'
    return m

def draw_face8(px, spec, skin, hair, build='woman', glow=None):
    """px: 8x8x4 float array, already filled. Returns px with the face drawn at rows 3-7."""
    skin = hexc(skin)
    hair = hexc(hair)
    line = hexc(spec.get('line', mix(hair, '#1a1420', 0.75)))
    iris = hexc(spec.get('iris', '#4a7ad8'))
    iris_l = hexc(spec.get('iris2', mix(iris, '#ffffff', 0.35)))
    het = spec.get('heterochromia')
    eye = EYES[resolve(build, spec)]

    def put(x, y, c, a=255):
        if 0 <= x < 8 and 0 <= y < 8:
            px[y, x, :3] = c
            px[y, x, 3] = a

    def gput(x, y, c):
        if glow is not None and 0 <= x < 8 and 0 <= y < 8:
            glow[y, x, :3] = c
            glow[y, x, 3] = 255

    # skin from row 3 down, soft shadow right under the bangs and at the jaw corners
    for y in range(3, 8):
        for x in range(8):
            put(x, y, skin)
    for x in range(8):
        put(x, 3, shade(skin, 0.9))
    put(1, 7, shade(skin, 0.9)); put(6, 7, shade(skin, 0.9))
    put(0, 7, shade(skin, 0.86)); put(7, 7, shade(skin, 0.86))
    for side in (0, 1):
        ir = hexc(het) if (het and side == 1) else iris
        il = mix(ir, '#ffffff', 0.35) if (het and side == 1) else iris_l
        pal = {
            'W': (250, 250, 252), 'D': mix(shade(ir, 0.5), line, 0.35), 'I': ir, 'J': il, 'K': il,
            'P': mix(shade(ir, 0.25), line, 0.6), 'L': line, 'B': mix(hair, line, 0.5),
        }
        for row, cols in eye.items():
            for i, ch in enumerate(cols):
                if ch == '.':
                    continue
                x = 1 + i if side == 0 else 6 - i
                put(x, row, pal[ch])
                if spec.get('glow_eyes') and ch in 'DIJKP' and not (ch == 'P' and 'K' not in cols):
                    gput(x, row, mix(pal[ch], '#ffffff', 0.15) if ch != 'D' else ir)
    if spec.get('blush'):
        bl = hexc(spec.get('blush_color', '#ff8c9c'))
        put(1, 6, mix(skin, bl, 0.55)); put(6, 6, mix(skin, bl, 0.55))
    mc = mix(skin, (150, 60, 70), 0.55)
    codes = {'M': mc, 'm': mix(skin, mc, 0.55), 'r': mix(skin, (210, 90, 100), 0.5), 'R': (170, 60, 72), 'T': (255, 255, 255)}
    for (y, x, c) in MOUTHS.get(default_mouth(build, spec), []):
        put(x, y, codes[c])
    marks = spec.get('marks', []) or []
    if isinstance(marks, str):
        marks = [('cheek', marks)]
    if spec.get('scar'):
        sc = mix(skin, (120, 40, 40), 0.6)
        for y in (3, 4, 5, 6):
            put(5, y, sc)
        put(6, 4, line); put(6, 5, line)
        put(4, 4, skin); put(4, 5, skin)
    if spec.get('veil_eyes'):
        ve = hexc(spec['veil_eyes'])
        for x in (2, 5):
            put(x, 5, ve); gput(x, 5, ve)
    for m in marks:
        kind = m if isinstance(m, str) else m[0]
        col = hexc(m[1]) if not isinstance(m, str) and len(m) > 1 else (200, 40, 60)
        if kind == 'tear':
            put(1, 6, col); put(6, 6, col); gput(1, 6, col); gput(6, 6, col)
        elif kind == 'cheek':
            put(0, 5, col); put(7, 5, col); put(0, 6, col); put(7, 6, col)
            gput(0, 5, col); gput(7, 5, col)
        elif kind == 'stitch':
            put(5, 6, col); put(6, 7, col); put(4, 7, col)
        elif kind == 'forehead':
            put(3, 3, col); put(4, 3, col); gput(3, 3, col); gput(4, 3, col)
    if spec.get('glasses'):
        gc = hexc(spec['glasses'])
        for x in (0, 3, 4, 7):
            put(x, 4, gc); put(x, 5, gc)
        for x in range(8):
            put(x, 3, gc)
    if spec.get('monocle'):
        gc = hexc(spec['monocle']) if isinstance(spec['monocle'], str) else (216, 176, 80)
        for x in (4, 7):
            put(x, 4, gc); put(x, 5, gc)
        for x in range(4, 8):
            put(x, 3, gc)
        put(7, 6, gc); put(7, 7, gc)
    if spec.get('mask'):
        mcol = hexc(spec['mask'])
        for y in (6, 7):
            for x in range(8):
                put(x, y, shade(mcol, 1.08 if y == 6 else 0.95))
    if spec.get('veil'):
        vcol = hexc(spec['veil'])
        for y in (6, 7):
            for x in range(8):
                px[y, x, :3] = mix(px[y, x, :3], vcol, 0.7)
    return px

def blink8(px, spec, skin, hair, build='woman'):
    """Closed-eye overlay plane (transparent elsewhere)."""
    px[...] = 0
    if resolve(build, spec) in ('void', 'closed'):
        return px
    skin = hexc(skin)
    line = hexc(spec.get('line', mix(hexc(hair), '#1a1420', 0.75)))
    eye = EYES[resolve(build, spec)]
    rows = [r for r in eye if r >= 4]
    for side in (0, 1):
        for row in rows:
            for i in range(2):
                x = 1 + i if side == 0 else 6 - i
                px[row, x, :3] = skin
                px[row, x, 3] = 255
        y = max(rows)
        for i in range(2):
            x = 1 + i if side == 0 else 6 - i
            px[y, x, :3] = line
    return px

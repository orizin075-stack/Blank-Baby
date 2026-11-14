"""059g: the characters' heads (face and hair) redone the way the user's references draw theirs (Touhou Little Maid,
Grimoire of Gaia, the mob-girl skins); the user: "全部作り直し" (the head), "顔以外の造形は前のままで良かった" (the rest).

prepare(rig) after a recipe has built its figure and before the bake:
  * the old hair goes: the 3D hair shell, its strands hanging in front of the cheeks, the locks, the chains of back
    hair, the tufts, the blinking lids (horns, halos, crowns, ears and everything else on the head stay);
  * the head cube is repainted: the 8 x 8 face of the references (drawn on an 8 x 8 grid, doubled to the head's two
    texels a pixel): flat skin, eyes two pixels wide and two or three tall in strong colour with a white highlight,
    no nose, no mouth; the hair's colour on the top, the sides and the back;
  * a hair layer half a pixel out over the head, fitted to it: clean bangs over the brow (a light band, a few points),
    locks down both sides of the face, the crown, the sides, the back;
  * long hair a sheet down the back to the waist, and for the long-haired a lock down each side to the shoulder.
"""
import numpy as np
import bb
from paint import M
from colors import hexc, mix, shade, lum

HAIR_BONES = ('hair', 'lock', 'blink', 'tuft')
HAIR_SURFS = ('hair', 'hair_back_base', 'tuft', 'back_hair', 'side_hair', 'lock', 'lids', 'fringe', 'bangs_strand')


def C(h):
    return np.asarray(hexc(h) if isinstance(h, str) else h, np.float32)


def up2(a):
    """An 8 x 8 drawing doubled to 16 x 16 (two texels a pixel)."""
    return np.repeat(np.repeat(a, 2, 0), 2, 1)


def fit(a, W, H):
    yi = np.minimum((np.arange(H) * a.shape[0] / H).astype(int), a.shape[0] - 1)
    xi = np.minimum((np.arange(W) * a.shape[1] / W).astype(int), a.shape[1] - 1)
    return a[yi][:, xi]


# bangs: rows of hair down each column of the 8 x 8 face (2 = rows 0-1, 3 = a point to row 2)
BANGS = {
    'bangs': [3, 2, 3, 2, 2, 3, 2, 3], 'blunt': [3, 3, 3, 3, 3, 3, 3, 3], 'parted': [3, 3, 2, 1, 1, 2, 3, 3],
    'swept': [3, 3, 3, 2, 2, 2, 1, 2], 'messy': [3, 2, 3, 1, 3, 2, 3, 2], 'short': [2, 1, 2, 2, 1, 2, 2, 1],
    'slick': [1, 1, 1, 1, 1, 1, 1, 1], 'open': [2, 1, 1, 0, 0, 1, 1, 2], 'none': [1, 0, 0, 0, 0, 0, 0, 1],
}
EYE_SHAPE = {'normal': 'round', 'big': 'big', 'calm': 'calm', 'sharp': 'sharp', 'fierce': 'sharp', 'sad': 'calm', 'slit': 'slit',
             'closed': 'closed', 'lowered': 'calm', 'void': 'void'}


def face8(spec, skin, hair, build):
    """The 8 x 8 face (rgb, glow) as the references draw it."""
    man = build in ('man', 'large')
    f = np.tile(C(skin), (8, 8, 1))
    g = np.zeros((8, 8, 4), np.float32)
    if spec.get('veil'):
        vc = C(spec['veil'])
        f[3:] = vc
        ey = C(spec.get('veil_eyes', '#ffcf6a'))
        for x in (2, 5):
            f[4, x] = ey
            g[4, x, :3], g[4, x, 3] = ey, 255
        return f, g
    shape = EYE_SHAPE.get(spec.get('style', 'normal'), 'round')
    iris, iris_r = spec.get('iris', '#5a3a2a'), spec.get('heterochromia') or spec.get('iris', '#5a3a2a')
    for side, ic in ((0, iris), (1, iris_r)):
        o, i = (1, 2) if side == 0 else (6, 5)
        dark = C(mix(shade(ic, 0.5), '#0c0614', 0.3))
        mid = C(ic)
        light = C(mix(ic, '#ffffff', 0.28))
        white = C('#ffffff')
        if man:
            # the vanilla men's eye: a white and an iris pixel under a short brow (no dark row between)
            cells = {(4, o): C('#f2f0f6'), (4, i): mid} if shape != 'closed' else {(4, o): dark, (4, i): dark}
        elif shape == 'big':
            cells = {(3, o): dark, (3, i): dark, (4, o): white, (4, i): mid, (5, o): mid, (5, i): light}
        elif shape == 'calm':
            cells = {(4, o): dark, (4, i): dark, (5, o): mid, (5, i): light}
        elif shape == 'sharp':
            cells = {(3, 0 if side == 0 else 7): dark, (4, o): dark, (4, i): dark, (5, o): mid, (5, i): white}
        elif shape == 'slit':
            cells = {(4, o): mid, (4, i): dark, (5, o): mid, (5, i): dark}
        elif shape == 'void':
            cells = {(4, o): dark, (4, i): dark, (5, o): dark, (5, i): light}
        elif shape == 'closed':
            cells = {(5, o): dark, (5, i): dark}
        else:                                                   # round
            cells = {(4, o): white, (4, i): dark, (5, o): mid, (5, i): light}
        for (y, x), col in cells.items():
            f[y, x] = col
            if spec.get('glow_eyes') and not np.allclose(col, white) and not np.allclose(col, dark):
                g[y, x, :3], g[y, x, 3] = col, 255
    if man:
        bc = C(mix(shade(hair, 0.55), '#1a1010', 0.3))
        f[3, 1:3] = f[3, 5:7] = bc                               # men's brows, right over the eyes
        if shape == 'sharp':
            f[2, 1] = f[2, 6] = bc
    marks = spec.get('marks')
    if marks and not isinstance(marks, (list, tuple)):
        mc = C(marks)
        f[6, 1] = f[6, 6] = mc
        g[6, 1, :3] = g[6, 6, :3] = mc
        g[6, 1, 3] = g[6, 6, 3] = 200
    elif marks:
        mc = C(spec.get('iris2') or iris)
        f[2, 3:5] = mc
        g[2, 3:5, :3], g[2, 3:5, 3] = mc, 255
    if spec.get('glasses'):
        gl = C(spec['glasses'])
        f[3, 0:4] = f[3, 4:8] = gl
        f[6, 1:3] = f[6, 5:7] = gl
    if spec.get('monocle'):
        mc = C(spec['monocle'])
        f[3, 4:8] = mc                                           # a ring round the right eye, its chain down
        f[5, 4:8] = mc
        f[4, 4] = f[4, 7] = mc
        f[6, 7] = f[7, 7] = mc
    if spec.get('scar'):
        f[3, 2] = f[4, 1] = f[5, 1] = C(mix(skin, '#8a2a2a', 0.45))
    return f, g


def head_fn(spec, skin, hair, build):
    face, fglow = face8(spec, skin, hair, build)

    def fn(face_name, W, H, s):
        if face_name == 'front':
            c = np.zeros((8, 8, 4), np.float32)
            c[..., :3], c[..., 3] = face, 255
            s.info['_glow8'] = fglow
            return fit(c, W, H)
        c = np.zeros((H, W, 4), np.float32)
        c[..., :3] = C(hair) if face_name != 'bottom' else C(skin)
        c[..., 3] = 255
        k = {'top': 1.06, 'left': 0.94, 'right': 0.94, 'back': 0.92, 'bottom': 0.8}.get(face_name, 1.0)
        c[..., :3] *= k
        return c
    return fn


def head_glow(face_name, W, H, s):
    if face_name == 'front' and '_glow8' in s.info:
        return fit(s.info['_glow8'], W, H)
    return np.zeros((H, W, 4), np.float32)


def hair_layer_fn(hair, bangs, long_hair, ears):
    hi, lo, base = C(mix(hair, '#ffffff', 0.24)), C(shade(hair, 0.8)), C(hair)
    rows = BANGS.get(bangs, BANGS['bangs'])

    def fn(face_name, W, H, s):
        c = np.zeros((8, 8, 4), np.float32)
        c[..., :3] = base
        if face_name == 'front':
            for x in range(8):
                c[:rows[x], x, 3] = 255
            c[0, :, :3] = hi
            side = 6 if long_hair else 4
            c[:side, 0, 3] = c[:side, 7, 3] = 255                # locks framing the face
            c[1:side, 0, :3] = c[1:side, 7, :3] = lo
        elif face_name == 'top':
            c[..., 3] = 255
            c[2, :, :3] = hi
        elif face_name == 'bottom':
            pass
        else:
            c[..., 3] = 255
            c[:, 2::3, :3] = lo                                  # strands
            c[1, :, :3] = hi
            if not long_hair:
                c[6:, :, 3] = 0
            if ears and face_name in ('left', 'right'):
                c[3:6, 3:5, 3] = 0
        return fit(c, W, H)
    return fn


def back_hair_fn(hair, length):
    hi, lo, base = C(mix(hair, '#ffffff', 0.22)), C(shade(hair, 0.8)), C(hair)

    def fn(face_name, W, H, s):
        c = np.zeros((H, W, 4), np.float32)
        c[..., :3], c[..., 3] = base, 255
        if face_name in ('front', 'back'):
            for x in range(W):
                if (x // 2) % 3 == 1:
                    c[:, x, :3] = lo
                cut = (0, 2, 4, 2)[(x // 2) % 4] if H > 8 else 0
                if cut:
                    c[H - cut:, x, 3] = 0
            c[2:4, :, :3] = hi
        return c
    return fn


def P(fn, glow=None):
    return M('pix', '#ffffff', fn=fn, glow=glow)


def prepare(r):
    """Swap the head (see the module's notes). A rig without an 8 x 8 x 8 head cube painted 'head' is left alone."""
    import bbpaint as BP
    if 'pix' not in BP.PAINTERS:
        BP.PAINTERS['pix'] = _m_pix
    head = r.by_name.get('head')
    if head is None or getattr(r, 'sculpt', None) is None:
        return False
    hs = [s for s in r.sculpt.surfs if s.bone is head and s.name == 'head']
    if not hs or (hs[0].mat or {}).get('type') != 'head':
        return False
    mat = hs[0].mat
    spec, skin, hair, build, bangs = mat.get('face', {}), mat['color'], mat.get('hair', '#3a2a24'), mat.get('build', 'woman'), mat.get('bangs', 'bangs')
    V = np.concatenate([np.asarray(s.V) for s in hs])
    lo, hi = V.min(0), V.max(0)
    size = hi - lo
    long_hair = any(b.name.startswith('hair_back') for b in r.bones)
    side_locks = any(b.name.startswith(('hair_side', 'lock')) for b in r.bones)
    ears = any('ear' in s.name for s in r.sculpt.surfs if s.bone is head)
    # the old hair out
    gone = set()
    for b in r.bones:
        x = b
        while x is not None and x is not head:
            if x.name.startswith(HAIR_BONES):
                gone.add(b.name)
                break
            x = x.parent
    r.sculpt.surfs = [s for s in r.sculpt.surfs if s.bone.name not in gone and not (s.bone is head and s.name in HAIR_SURFS)]
    r.bones = [b for b in r.bones if b.name not in gone]
    r.by_name = {b.name: b for b in r.bones}
    # the head repainted, the fitted hair layer, long hair and side locks
    for s in hs:
        s.mat = P(head_fn(spec, skin, hair, build), head_glow)
        s.info['ao'] = False
    bb.cube(head, tuple(lo), tuple(size), P(hair_layer_fn(hair, bangs, long_hair, ears)), name='hair_layer', inflate=0.5,
            info={'ao': False})
    if long_hair:
        L = size[1] * 1.6
        bb.cube(head, (lo[0] - 0.5, hi[1] - 1.0, hi[2] + 0.3), (size[0] + 1.0, L, 1.0), P(back_hair_fn(hair, L)), name='hair_sheet',
                info={'ao': False})
    if side_locks:
        for sx in (-1, 1):
            x0 = lo[0] - 0.6 if sx < 0 else hi[0] - 0.4
            bb.cube(head, (x0, hi[1] - 2.0, lo[2] + 0.6), (1.0, size[1] * 0.75, 2.0), P(back_hair_fn(hair, size[1] * 0.75)),
                    name='hair_lock', info={'ao': False})
    return True


def _m_pix(mat, f, s, ctx):
    out = np.asarray(mat['fn'](f.face, f.W, f.H, s), np.float32)
    if out.shape[-1] == 3:
        return out, None, None
    g = mat.get('glow')
    return out[..., :3], out[..., 3] / 255.0, (np.asarray(g(f.face, f.W, f.H, s), np.float32) if g else None)

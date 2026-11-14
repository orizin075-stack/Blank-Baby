"""059g: OROR's people built the way the user's references build theirs (Touhou Little Maid's maids, Grimoire of Gaia's
monster girls, the anime player skins: "こういうのだぞ 顔の造形的に理想的なの", "読み直して造形から見直せ").

The form, as those models have it:
  * the vanilla player's proportions: a head of 8 x 8 x 8, a body of 8 x 12 x 4, slim arms of 3 x 12 x 4, legs of
    4 x 12 x 4 (a child: a shorter body and legs under the same head);
  * one texture pixel to a model pixel: the face is the 8 x 8 front of the head, the eyes two pixels wide, no nose
    and no mouth;
  * the hair as the head's outer layer half a pixel out (the fringe over the brow, locks down the cheeks) and, for long
    hair, a sheet down the back; clothes as the body's and limbs' outer layers a quarter pixel out; a skirt as a flared
    box at the hips;
  * extra cubes only for what the character has that a person has not: horns, elf ears, a tail, wings, a halo, a crown.
Every surface is drawn here pixel by pixel (material 'pix': a function of the face it paints), in flat colours with a
light top and a dark underside, as the references are.
"""
import math
import numpy as np
import bb
import sculpt as SC
import bbpaint as BP
from paint import M
from rig import Rig
from colors import hexc, mix, shade

RECIPES = {}


def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn


def C(h):
    return np.asarray(hexc(h) if isinstance(h, str) else h, np.float32)


def m_pix(mat, f, s, ctx):
    out = mat['fn'](f.face, f.W, f.H, s)
    rgba = np.asarray(out, np.float32)
    if rgba.shape[-1] == 3:
        return rgba, None, None
    a = rgba[..., 3] / 255.0
    glow = mat.get('glow')
    g = None
    if glow is not None:
        g = np.asarray(glow(f.face, f.W, f.H, s), np.float32)
    return rgba[..., :3], a, g


BP.PAINTERS['pix'] = m_pix


def P(fn, glow=None):
    return M('pix', '#ffffff', fn=fn, glow=glow)


def canvas(W, H, col, a=255):
    c = np.zeros((H, W, 4), np.float32)
    c[..., :3] = C(col)
    c[..., 3] = a
    return c


def lit(c, face):
    """Flat colour lit as the references are: the top a step lighter, the underside and the sides a step darker."""
    k = {'top': 1.08, 'bottom': 0.78, 'left': 0.92, 'right': 0.92, 'back': 0.9}.get(face, 1.0)
    c[..., :3] = np.clip(c[..., :3] * k, 0, 255)
    return c


# ================================================================================================ the parts

def eyes(c, iris, iris_r=None, shape='round', lash='#1a1222', glow=None, top=4, accent=None):
    """The eyes on the 8 x 8 face (columns 1-2 and 5-6). shape: round (lash, highlight and iris), calm (a heavy
    lid), sharp (the outer corner flicked up), big (three rows), sleepy, void (dark with a glowing core)."""
    iris_r = iris_r or iris
    for side, ic in ((0, iris), (1, iris_r)):
        o, i = (1, 2) if side == 0 else (6, 5)              # outer and inner column
        dark = C(mix(shade(ic, 0.6), '#140a1e', 0.25))
        I, J = C(ic), C(mix(ic, '#ffffff', 0.3))
        L = C(lash)
        if shape == 'big':
            c[top - 1, o, :3] = c[top - 1, i, :3] = L
            c[top, o, :3], c[top, i, :3] = C('#ffffff'), dark
            c[top + 1, o, :3], c[top + 1, i, :3] = I, C(mix(ic, accent or ic, 0.6))
        elif shape == 'calm':
            c[top, o, :3] = c[top, i, :3] = L
            c[top + 1, o, :3], c[top + 1, i, :3] = dark, I
        elif shape == 'sleepy':
            c[top + 1, o, :3] = c[top + 1, i, :3] = L
        elif shape == 'sharp':
            c[top - 1, 0 if side == 0 else 7, :3] = L
            c[top, o, :3] = c[top, i, :3] = L
            c[top + 1, o, :3], c[top + 1, i, :3] = I, dark
        elif shape == 'void':
            c[top, o, :3] = c[top, i, :3] = L
            c[top + 1, o, :3], c[top + 1, i, :3] = C('#0c0814'), J
        else:                                               # round: highlight at the outer top
            c[top, o, :3], c[top, i, :3] = C('#ffffff'), dark
            c[top + 1, o, :3], c[top + 1, i, :3] = I, J
        if glow is not None:
            for y in (top, top + 1):
                for x in (o, i):
                    if not np.allclose(c[y, x, :3], L) and not np.allclose(c[y, x, :3], C('#ffffff')):
                        glow[y, x, :3] = c[y, x, :3]
                        glow[y, x, 3] = 255


def head_fn(spec):
    """The head's own faces: skin and the face in front, the hair's base colour round it (the outer layer draws the
    hair itself)."""
    skin, hair = spec['skin'], spec['hair']

    def fn(face, W, H, s):
        if face == 'front':
            c = canvas(W, H, skin)
            c[0:2, :, :3] = C(hair)                         # under the fringe
            c[:, 0, :3] = c[:, 7, :3] = C(shade(skin, 0.94))
            g = np.zeros_like(c)
            eyes(c, spec['iris'], spec.get('iris_r'), spec.get('eye', 'round'), spec.get('lash', '#1a1222'),
                 g if spec.get('glow_eyes') else None, spec.get('eye_top', 4), spec.get('eye_accent'))
            if spec.get('blush'):
                c[6, 1, :3] = c[6, 6, :3] = C(mix(skin, '#ff6a8a', 0.35))
            s.info['_glow'] = g
            return c
        c = canvas(W, H, hair)
        if face in ('left', 'right'):
            c[3:, 2:6, :3] = C(skin)                         # the ear and the cheek under the side locks
        return lit(c, face)
    return fn


def head_glow(face, W, H, s):
    return s.info.get('_glow', np.zeros((H, W, 4), np.float32)) if face == 'front' else np.zeros((H, W, 4), np.float32)


def hair_layer_fn(spec):
    """The hair's outer layer: the fringe (rows 0-2 with points), locks down both cheeks, the crown, the sides and the
    back; the face left open."""
    hair = spec['hair']
    hi, lo = C(mix(hair, '#ffffff', 0.28)), C(shade(hair, 0.78))
    fringe = spec.get('fringe', [3, 2, 3, 3, 2, 3, 2, 3])
    locks = spec.get('locks', 6)

    def fn(face, W, H, s):
        c = canvas(W, H, hair)
        if face == 'front':
            c[..., 3] = 0
            for x in range(W):
                d = fringe[x * 8 // W]
                c[:d, x, 3] = 255
                c[d - 1, x, :3] = lo                         # the fringe's tips a shade darker
            for x in (0, W - 1):                            # locks framing the face
                c[:locks, x, 3] = 255
            c[0, :, :3] = hi
            return c
        if face == 'top':
            c[:, :, :3] = C(hair)
            c[2:4, :, :3] = hi                              # the angel ring
            return c
        if face == 'bottom':
            c[..., 3] = 0
            return c
        # sides and back: strands, a light ring near the top
        for x in range(W):
            if x % 3 == 1:
                c[:, x, :3] = lo
        c[1, :, :3] = hi
        if face in ('left', 'right') and spec.get('ears'):
            c[3:6, 3:5, 3] = 0                              # the elf ear comes through
        return lit(c, face)
    return fn


def long_hair_fn(hair):
    """The hair down the back: strands of two tones, a light ring near the top, the ends cut in points."""
    lo, hi = C(shade(hair, 0.8)), C(mix(hair, '#ffffff', 0.25))
    tips = [0, 2, 1, 0, 2, 1, 0, 2, 1]

    def fn(face, W, H, s):
        c = canvas(W, H, hair)
        for x in range(W):
            if x % 3 == 1:
                c[:, x, :3] = lo
            cut = tips[x % len(tips)] if face in ('front', 'back') and H > 4 else 0
            if cut:
                c[H - cut:, x, 3] = 0
        if H > 2:
            c[1, :, :3] = hi
        return lit(c, face)
    return fn


def strip_fn(colours, rows=None, face_cols=None):
    """A part in horizontal bands (a sleeve, a leg): colours top to bottom with their row counts."""
    def fn(face, W, H, s):
        c = canvas(W, H, colours[-1][0])
        y = 0
        for col, n in colours:
            c[y:y + n, :, :3] = C(col)
            y += n
        return lit(c, face)
    return fn


def build_humanoid(key, spec):
    """The figure: bones with the animation names RigModel plays, the parts and their layers."""
    r = Rig(key)
    SC.Sculpt(r, td=1)
    child = spec.get('child', False)
    leg_h, body_h, arm_h = (9, 9, 9) if child else (12, 12, 12)
    top = 24 - leg_h - body_h                                # the body's top (the neck)
    root = r.bone('root', None, (0, 24, 0), anim='root', hover=spec.get('hover', 0.0), speed=0.06)
    hips = r.bone('hips', root, (0, 24 - leg_h, 0))
    torso = r.bone('torso', hips, (0, 24 - leg_h, 0), anim='breath')
    head = r.bone('head', torso, (0, top, 0), anim='head')
    arm_r = r.bone('arm_r', torso, (-5, top + 2, 0), anim='arm_r', reach=arm_h - 2)
    arm_l = r.bone('arm_l', torso, (5, top + 2, 0), anim='arm_l', reach=arm_h - 2)
    leg_r = r.bone('leg_r', hips, (-2, 24 - leg_h, 0), anim='leg_r')
    leg_l = r.bone('leg_l', hips, (2, 24 - leg_h, 0), anim='leg_l')
    # the head and its hair
    bb.cube(head, (-4, top - 8, -4), (8, 8, 8), P(head_fn(spec), head_glow), name='head')
    bb.cube(head, (-4, top - 8, -4), (8, 8, 8), P(hair_layer_fn(spec)), name='hair', inflate=0.5)
    if spec.get('long_hair'):
        n = spec['long_hair']
        bb.cube(head, (-4.5, top - 1, 3.8), (9, n, 1), P(long_hair_fn(spec['hair'])), name='hair_back')
    # the body, its clothes
    bb.cube(torso, (-4, top, -2), (8, body_h, 4), P(spec['body']), name='body')
    if spec.get('jacket'):
        bb.cube(torso, (-4, top, -2), (8, body_h, 4), P(spec['jacket']), name='jacket', inflate=0.25)
    # slim arms with sleeves
    for b, x0 in ((arm_r, -7), (arm_l, 4)):
        bb.cube(b, (x0, top, -2), (3, arm_h, 4), P(spec['arm']), name='arm')
        if spec.get('sleeve'):
            bb.cube(b, (x0, top, -2), (3, spec.get('sleeve_len', arm_h - 3), 4), P(spec['sleeve']), name='sleeve', inflate=0.3)
    for b, x0 in ((leg_r, -4), (leg_l, 0)):
        bb.cube(b, (x0, 24 - leg_h, -2), (4, leg_h, 4), P(spec['leg']), name='leg')
    if spec.get('skirt'):
        h0, h1, flare = spec['skirt_shape'] if spec.get('skirt_shape') else (5, 4, 1.0)
        y0 = 24 - leg_h - 1
        bb.cube(hips, (-4.5, y0, -2.5), (9, h0, 5), P(spec['skirt']), name='skirt')
        bb.cube(hips, (-4.5 - flare, y0 + h0, -2.5 - flare), (9 + 2 * flare, h1, 5 + 2 * flare), P(spec['skirt']), name='skirt_hem')
    return r, dict(head=head, torso=torso, hips=hips, arm_r=arm_r, arm_l=arm_l, leg_r=leg_r, leg_l=leg_l, top=top)


def horn(head, x, y, z, pts, base, tip, w0=1.6, w1=0.5):
    import creatures_ia as CI
    P_ = [(x + a, y + b, z + c) for a, b, c in pts]
    CI.chain_boxes(head, P_, w0, w1, M('horn', base, tip=tip))


def tail(r, parent, start, n, w0, colour, belly, spikes=None):
    import creatures_ia as CI
    CI.tail(r, parent, start, [3.0] * n, [w0 * (1 - 0.6 * i / n) for i in range(n)], M('scale', colour, belly=belly, scale_size=0.8),
            droop=0.55, lift=0.25, spikes=spikes, amp=0.14, speed=0.06)


# ================================================================================================ characters

@recipe
def kokuhaku():
    # 剣神 炬珀: a slight girl of fifteen or so; pure white hair past the waist; heterochromia, deep blue and gold;
    # two porcelain-white dragon horns from the brow; a long tail of fine silver scales; a swordsman's plain clothes in
    # ink black and white, the cuffs and sash mended; an old sheathed katana at the waist and nothing else.
    skin, hair = '#f4eee8', '#f2f2f6'
    ink, white = '#23232e', '#ecebf0'

    def body(face, W, H, s):
        c = canvas(W, H, white)
        if face == 'front':
            for y in range(H):                              # the kimono's crossed collar
                if y < 5:
                    c[y, max(0, 3 - y // 2):3, :3] = C(ink)
                    c[y, 5:min(W, 5 + y // 2 + 1), :3] = C(ink)
            c[6:9, :, :3] = C(ink)                          # the sash
            c[7, 3:5, :3] = C('#8a7a62')                    # its knot, worn
        else:
            c[6:9, :, :3] = C(ink)
        return lit(c, face)

    def arm(face, W, H, s):
        c = canvas(W, H, skin)
        return lit(c, face)

    def sleeve(face, W, H, s):
        c = canvas(W, H, white)
        c[-2:, :, :3] = C(ink)                              # the cuff
        c[-1, ::2, :3] = C('#5a5a66')                       # mended
        return lit(c, face)

    def leg(face, W, H, s):
        c = canvas(W, H, ink)                               # dark hakama under the skirt, tabi and sandals
        c[-2:, :, :3] = C(white)
        c[-1, :, :3] = C('#6a5240')
        return lit(c, face)

    def skirt(face, W, H, s):
        c = canvas(W, H, ink)
        for x in range(W):
            if x % 3 == 0:
                c[:, x, :3] = C(shade(ink, 1.35))           # the hakama's pleats
        return lit(c, face)

    spec = dict(skin=skin, hair=hair, iris='#24418e', iris_r='#d8a83a', eye='calm', lash='#3a3a4a',
                fringe=[3, 3, 2, 3, 3, 2, 3, 3], locks=7, long_hair=14, body=body, arm=arm, sleeve=sleeve, sleeve_len=9,
                leg=leg, skirt=skirt, skirt_shape=(5, 4, 0.6))
    r, b = build_humanoid('kokuhaku', spec)
    top = b['top']
    for sx in (-1, 1):
        horn(b['head'], sx * 2.5, top - 8, -1.5, [(0, 0, 0), (sx * 0.8, -2.5, 1.0), (sx * 1.2, -4.8, 2.6), (sx * 1.0, -6.2, 4.4)],
             '#f2f0ea', '#cfd8e6')
    tail(r, b['hips'], (0, 24 - 12 + 1, 2.2), 7, 2.6, '#d8dce4', '#eef0f4')
    # the old sheathed katana at the left hip
    import creatures_ia as CI
    CI.seg(b['hips'], (4.6, 24 - 12 + 1.5, -3.0), (5.0, 24 - 12 + 4.5, 7.0), 0.7, 1.0, M('simple', '#2a2420'))
    CI.seg(b['hips'], (4.6, 24 - 12 + 1.2, -3.0), (4.4, 24 - 12 + 0.4, -6.0), 0.6, 0.6, M('cloth', '#1e1e2a'))
    return r


@recipe
def riha():
    # 天冠詠者 理覇: a small child; snow-white long hair; big eyes of pale sky blue with gold melting in; a light divine
    # robe in white and pale gold, old word-spirit letters woven at cuffs and collar, little bells and flowers at the
    # hem (taken up and altered for walking); a thin translucent heavenly crown floating over her head.
    skin, hair = '#fbf1ea', '#f6f6fa'
    gold, white = '#e8cf86', '#f6f4ee'

    def body(face, W, H, s):
        c = canvas(W, H, white)
        if face == 'front':
            c[0, 2:6, :3] = C(gold)                          # the collar's letters
            c[1, 3:5, :3] = C(gold)
            c[4:6, :, :3] = C(gold)                          # a sash
            c[5, 3:5, :3] = C('#ff9ab8')                     # a flower at the sash
        return lit(c, face)

    def arm(face, W, H, s):
        return lit(canvas(W, H, skin), face)

    def sleeve(face, W, H, s):
        c = canvas(W, H, white)
        c[-2:, :, :3] = C(gold)
        c[-2, ::2, :3] = C('#fff2c0')                        # woven letters
        return lit(c, face)

    def leg(face, W, H, s):
        c = canvas(W, H, white)
        c[-2:, :, :3] = C('#c8a86a')                         # little sandals
        return lit(c, face)

    def skirt(face, W, H, s):
        c = canvas(W, H, white)
        c[-1, :, :3] = C(gold)
        if face in ('front', 'back', 'left', 'right'):
            c[-2, ::3, :3] = C('#ffd85a')                    # bells
            c[-2, 1::3, :3] = C('#ffb0c8')                   # flowers
        return lit(c, face)

    spec = dict(skin=skin, hair=hair, iris='#7cb8ec', iris_r='#7cb8ec', eye='big', eye_accent='#f2d070', lash='#5a6a8a', blush=True,
                fringe=[2, 3, 2, 2, 2, 2, 3, 2], locks=6, long_hair=11, child=True, body=body, arm=arm, sleeve=sleeve,
                sleeve_len=6, leg=leg, skirt=skirt, skirt_shape=(4, 3, 0.8))
    r, b = build_humanoid('riha', spec)
    top = b['top']
    # the heavenly crown: a thin ring of light over the head, points of light round it
    import creatures_ia as CI
    CI.hoop(b['head'], (0, top - 10.5, 0), 4.2, 0.35, M('energy', '#fff1b0', glow=True), axis='y', n=20)
    for k in range(5):
        a = k / 5 * 2 * math.pi
        bb.ccube(b['head'], (math.cos(a) * 4.2, top - 11.6, math.sin(a) * 4.2), (0.6, 1.8, 0.6), M('energy', '#fff8d8', glow=True))
    return r

"""The 37 characters of the user's design sheets as geometry for designfig: each recipe returns (Fig, views).

views: per sheet view, the boxes the figure is cut from (sheet pixels), boxes to leave out (a held weapon the mob
holds as its relic instead, sparks), an initial yaw/pitch for the camera fit and the pose the figure stands in there.
"""
import math, os
import numpy as np
from designfig import Fig, sheet_mask
from scipy import ndimage
from rig import rot_zyx

RECIPES = {}


def recipe(sheet):
    def deco(fn):
        RECIPES[fn.__name__] = (sheet, fn)
        return fn
    return deco


def mirror_x(p):
    return (-p[0], p[1], p[2])


@recipe('01_')
def kokuhaku():
    """剣神 炬珀: white long hair to the knees, dragon horns with tassels, white haori over navy hakama, wide sleeves,
    platform sandals, a long white scaled tail. Coordinates unprojected from the front view (yaw -30, pitch 12)."""
    f = Fig('kokuhaku', td=int(os.environ.get('DF_TD', 3)))
    X = 1.2                                                   # the body's axis sits a little to her left of the feet
    f.humanoid(hip_y=0.5, waist_y=-5.5, neck_y=-13.4, shoulder=(X - 4.4, -10.6, 0), elbow=(X - 6.6, -4.2, -1.2),
               hip=(X - 2.0, 0.5, -0.4), knee=(-4.0, 12.5, -0.8))
    f.mirror_x = X
    # head: skull with the hair over it; the horns rise and sweep back
    f.box('head', (X + 0.3, -18.7, -0.2), (8.8, 10.0, 8.8), name='head')
    f.decal('head', 'head', 'north', (1169, 416, 1328, 597))           # 顔 正面
    f.decal('head', 'head', 'west', (1362, 416, 1518, 597))            # 顔 側面 (her right side)
    f.decal('head', 'head', 'east', (1362, 416, 1518, 597), flip=True)
    f.decal('head', 'head', 'south', (872, 112, 968, 232))             # back of the head, from the back view
    for sx in (-1, 1):
        f.chain('head', [(X + 0.3 + sx * 2.8, -22.4, 0.4), (X + 0.3 + sx * 4.0, -25.0, 2.0), (X + 0.3 + sx * 5.0, -26.6, 4.0)],
                [1.9, 1.3, 0.4], d=[2.2, 1.5, 0.5], name='horn')
    # hair: locks beside the face, the long mass down her back and the part that flows out at her left
    f.box('head', (X - 4.8, -14.0, -2.2), (1.6, 7.0, 3.6), name='lock_r')
    f.box('head', (X + 5.0, -14.0, -1.4), (1.8, 7.0, 4.2), name='lock_l')
    f.box('torso', (X - 5.4, -4.0, -1.8), (1.4, 12.0, 2.6), name='lock_r_low')
    f.box('torso', (X + 0.3, -1.0, 5.2), (10.0, 22.0, 2.6), name='hair_back')
    f.chain('torso', [(X + 4.8, -13.0, 2.2), (X + 8.6, -5.5, 3.6), (X + 10.6, 4.0, 4.0), (X + 10.8, 11.0, 4.2)],
            [4.6, 5.2, 4.6, 2.4], d=[3.4, 3.0, 2.4, 1.4], name='hair_flow', up=(0, 0, -1))
    # kimono: chest, obi, the haori flaring to the knee
    f.box('torso', (X, -10.0, -0.2), (7.4, 6.6, 4.6), name='chest')
    f.box('torso', (X, -5.8, -0.2), (7.8, 3.4, 5.2), name='obi')
    f.frustum('hips', ((X, -4.2, 0.0), 8.2, 5.4), ((X - 0.4, 15.0, 0.4), 18.0, 9.0), name='haori')
    # arms hang out from the shoulders; the wide sleeve hangs under the forearm
    for side, sx in (('r', -1), ('l', 1)):
        sh = np.array([X + sx * 4.4, -10.6, 0.0])
        el = np.array([X + sx * 6.6, -4.2, -1.2])
        ha = np.array([X + sx * 8.4, 1.6, -2.4])
        f.chain(f'arm_{side}', [sh, el], [2.6, 2.4], name='upper')
        f.chain(f'fore_{side}', [el, ha], [2.4, 2.2], name='fore')
        f.chain(f'fore_{side}', [el + (sx * 0.4, 1.0, 0.8), ha + (sx * 0.4, 4.4, 1.6)], [5.0, 5.6], d=[3.2, 3.0], name='sleeve', up=(0, 0, -1))
    # shins and platform sandals, feet apart
    for side, sx, x in (('r', -1, -5.9), ('l', 1, 6.0)):
        f.chain(f'shin_{side}', [(x * 0.62, 12.5, -0.8), (x, 21.2, -1.0)], [2.8, 2.6], name='shin')
        f.box(f'shin_{side}', (x, 22.6, -1.4), (3.8, 2.8, 5.8), name='sandal')
    # tail (triangulated from both views): out from the small of the back to her left, down to the ground and
    # curling round behind her
    t = f.bone('tail', 'hips', (X + 1.2, 2.5, 3.6), anim='tail', amp=0.05, speed=0.05)
    f.chain(t, [(X + 1.2, 2.5, 3.6), (6.0, 1.8, 5.4), (10.0, 2.6, 6.2), (13.6, 9.4, 6.8), (14.6, 14.6, 8.0), (12.4, 19.2, 8.8),
                (9.4, 21.4, 9.8), (4.6, 22.4, 12.0), (0.8, 22.9, 13.3), (-2.4, 23.2, 12.6)],
            [3.4, 3.4, 3.4, 3.2, 3.0, 2.8, 2.5, 2.1, 1.5, 0.5], name='tail')
    f.views_for('head', ['front'])
    views = {
        'front': dict(box=[(0, 0, 785, 1024)], drop=[(0, 470, 252, 800), (0, 0, 340, 140)], cam=(-30.0, 12.0, 19.5, 445.0, 520.2)),
        'back': dict(box=[(770, 20, 1115, 700)], yaw=160, pitch=12, yaw_span=60, pitch_span=4),
    }
    return f, views



def ring(f, bone, c, radius, n, w, h, name='ring', tilt=(0.0, 0.0)):
    """n blocks round a horizontal circle (a crown, a halo), tilted by (x, z) radians."""
    R = rot_zyx(tilt[0], 0, tilt[1])
    c = np.asarray(c, float)
    seg = 2 * math.pi * radius / n * 1.15
    for i in range(n):
        a = 2 * math.pi * i / n
        p = c + R @ np.array([math.cos(a) * radius, 0, math.sin(a) * radius])
        f.box(bone, p, (seg, h, w), rot=(tilt[0], -a + math.pi / 2, tilt[1]), name=name)


def card(f, parent, c, size, i, rot=(0.0, 0.0, 0.0), name='card', amp=0.6, speed=0.05):
    """A floating card or panel on its own bobbing bone."""
    b = f.bone(f'{name}{i}', parent, tuple(c), anim='float', amp=amp, speed=speed, phase=i * 1.3)
    f.box(b, c, (size[0], size[1], 0.3), rot=rot, name=name)
    return b


@recipe('02_')
def riha():
    """天冠詠者 理覇: white long hair, a floating golden crown with crystal points, small dark wings at the head,
    white coat with gold edging over a dark violet dress, huge sleeves, a great book in the right hand, the left
    hand open, floating cards."""
    f = Fig('riha', td=int(os.environ.get('DF_TD', 4)))
    f.camera_at(-20.0, 10.0, 19.3, 338, 978)
    A = lambda u, v, z=0.0: f.at(u, v, z)
    f.humanoid(hip_y=0.0, waist_y=-5.0, neck_y=-11.5, shoulder=tuple(A(255, 335, 0) + (1.0, 1.0, 0)), elbow=tuple(A(185, 420, -1)),
               hip=(-1.8, 0.0, 0), knee=(-1.8, 12.0, -0.5))
    f.mirror_x = float(A(338, 600)[0])
    head = A(338, 205, 0)
    f.box('head', head, (8.8, 9.8, 8.8), name='head')
    f.decal('head', 'head', 'north', (1030, 42, 1300, 372))            # 顔 正面 close-up
    # floating crown: a gold ring with crystal points, above and behind the head
    cr = f.bone('crown', 'head', tuple(A(340, 80, 1.0)), anim='spin', speed=0.012)
    ring(f, cr, A(340, 80, 1.0), 6.6, 14, 0.9, 1.1, name='crown', tilt=(0.18, 0.0))
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.3
        p = A(340, 80, 1.0) + rot_zyx(0.18, 0, 0) @ np.array([math.cos(a) * 6.6, -1.4, math.sin(a) * 6.6])
        f.box(cr, p, (0.8, 2.4, 0.8), name='crown_spike')
    for sx in (-1, 1):
        # little dark wings at the temples
        base = head + (sx * 4.6, -1.0, 1.0)
        f.box('head', base + (sx * 1.6, -0.6, 0.4), (3.4, 2.2, 0.5), rot=(0, sx * 0.5, sx * 0.4), name='head_wing')
        # hair falling beside the face and over the shoulders
        f.box('head', head + (sx * 4.9, 5.6, -0.6), (1.6, 9.0, 4.6), name='hair_side')
    f.box('torso', A(338, 420, 3.6), (10.0, 16.0, 2.6), name='hair_back')
    # dress and coat
    f.box('torso', A(345, 380, 0), (7.0, 7.0, 4.2), name='chest')
    f.box('torso', A(345, 460, 0), (7.4, 1.8, 4.6), name='belt')
    f.frustum('hips', (A(345, 470, 0), 8.0, 5.0), (A(325, 880, 0) + (0, 0, 0.5), 22.0, 10.0), name='coat')
    # right arm with the great book; left arm held out, hand open
    sh_r, el_r, ha_r = A(258, 340, 0), A(190, 420, -1.0), A(135, 455, -2.6)
    f.chain('arm_r', [sh_r, el_r], [2.6, 2.4], name='upper')
    f.chain('fore_r', [el_r, ha_r], [2.4, 2.2], name='fore')
    f.chain('fore_r', [A(215, 360, 0.6), A(130, 600, 0.0)], [6.0, 7.0], d=[3.6, 3.2], name='sleeve', up=(0, 0, -1))
    book = A(110, 540, -3.6)
    f.box('fore_r', book, (8.6, 11.0, 2.2), rot=(0.05, 0.35, 0.12), name='book')
    sh_l, el_l, ha_l = A(425, 345, 0), A(490, 430, -0.6), A(590, 535, -1.6)
    f.chain('arm_l', [sh_l, el_l], [2.6, 2.4], name='upper')
    f.chain('fore_l', [el_l, ha_l], [2.4, 2.0], name='fore')
    f.chain('fore_l', [A(440, 360, 0.6), A(520, 520, 0.4)], [5.0, 5.8], d=[3.2, 3.0], name='sleeve', up=(0, 0, -1))
    for side, u in (('r', 312), ('l', 372)):
        foot = f.xat(u, 22.6, -0.3)
        f.chain(f'shin_{side}', [foot + (0, -10.0, 0.6), foot + (0, -1.0, 0.2)], [2.8, 3.0], name='boot')
        f.box(f'shin_{side}', foot + (0, 0.4, -0.5), (3.4, 2.8, 5.0), name='shoe')
    # floating cards
    for i, (u, v, z) in enumerate(((45, 270, -1), (112, 280, 1), (565, 300, 0), (618, 360, 2), (600, 635, 0), (30, 530, -2),
                                   (210, 625, -5))):
        card(f, 'root', A(u, v, z), (2.6, 4.2), i, rot=(0, 0.35 * (1 if u > 338 else -1), 0))
    views = {
        'front': dict(box=[(0, 0, 640, 1000)], drop=[(470, 0, 640, 150)], cam=f.cam_tuple()),
        'back': dict(box=[(600, 200, 1000, 990)], yaw=180, pitch=10, yaw_span=30, pitch_span=4),
    }
    return f, views


def limb(f, bone_up, bone_lo, sh, el, ha, w_up, w_lo, sleeve=None, name=''):
    """Upper limb and forearm as chains (sh -> el on bone_up, el -> ha on bone_lo); sleeve = (top, bottom, w0, w1,
    d0, d1) hangs a wide sleeve from the forearm bone."""
    f.chain(bone_up, [sh, el], w_up, name=name + 'upper')
    f.chain(bone_lo, [el, ha], w_lo, name=name + 'fore')
    if sleeve:
        a, b, w0, w1, d0, d1 = sleeve
        f.chain(bone_lo, [a, b], [w0, w1], d=[d0, d1], name=name + 'sleeve', up=(0, 0, -1))


def streamer(f, parent, pts, w, name, i, d=0.6, amp=0.05, speed=0.06):
    """A hanging ribbon or chain of plates on a swaying bone."""
    b = f.bone(f'{name}{i}', parent, tuple(pts[0]), anim='cape', amp=amp, speed=speed, phase=i * 0.9)
    f.chain(b, pts, w, d=d, name=name, up=(0, 0, -1))
    return b


@recipe('03_')
def tenki():
    """唯我万象 天輝: a crown of golden crosses on white hair, a white mantle and long white coat edged in gold over a
    navy robe with a golden cross, wide sleeves trailing chains of golden crosses."""
    f = Fig('tenki', td=int(os.environ.get('DF_TD', 4)))
    f.camera_at(25.0, 10.0, 20.0, 505, 985)
    A = f.at
    f.humanoid(hip_y=0.0, waist_y=-5.0, neck_y=-12.5, shoulder=tuple(A(330, 320, 0)), elbow=tuple(A(318, 430, -0.5)),
               hip=(-2.0, 0.0, 0), knee=(-2.2, 12.0, -0.4))
    f.mirror_x = float(A(520, 600)[0])
    head = A(520, 170, 0)
    f.box('head', head, (9.6, 10.0, 9.6), name='head')
    cr = f.bone('crown', 'head', tuple(head + (0, -5.6, 0)), anim='spin', speed=0.01)
    ring(f, cr, head + (0, -5.4, 0), 5.0, 12, 0.9, 1.2, name='crown')
    for i in range(6):
        a = 2 * math.pi * i / 6 + 0.25
        p = head + (math.cos(a) * 5.0, -7.6, math.sin(a) * 5.0)
        f.box(cr, p, (0.8, 3.6, 0.8), name='crown_cross')
        f.box(cr, p + (0, -0.6, 0), (2.4, 0.8, 0.8), rot=(0, -a + math.pi / 2, 0), name='crown_cross')
    f.box('torso', head + (0, 8.0, 4.0), (9.0, 14.0, 2.4), name='hair_back')
    # mantle over the shoulders, the body, the long coat
    f.frustum('torso', (A(525, 245, 0), 9.0, 6.0), (A(525, 330, 0), 15.0, 9.0), name='mantle')
    f.box('torso', A(545, 400, 0), (8.0, 8.0, 4.6), name='chest')
    f.frustum('hips', (A(530, 470, 0), 11.0, 6.4), (A(520, 935, 0), 18.0, 10.0), name='coat')
    sh_r, el_r, ha_r = A(335, 330, 0), A(318, 440, -0.8), A(300, 535, -2.6)
    limb(f, 'arm_r', 'fore_r', sh_r, el_r, ha_r, [2.8, 2.6], [2.6, 2.4], sleeve=(A(320, 340, 0.4), A(300, 660, 0.4), 6.0, 7.0, 4.0, 3.6))
    sh_l, el_l, ha_l = A(710, 330, 0), A(690, 450, -0.8), A(670, 560, -2.2)
    limb(f, 'arm_l', 'fore_l', sh_l, el_l, ha_l, [2.8, 2.6], [2.6, 2.4], sleeve=(A(705, 340, 0.4), A(700, 690, 0.4), 6.0, 7.0, 4.0, 3.6))
    # trailing chains of crosses
    streamer(f, 'arm_r', [A(300, 290, 1.5), A(200, 430, 2.5), A(115, 600, 3.0)], [2.4, 2.2, 3.4], 'chain', 0)
    streamer(f, 'arm_r', [A(320, 360, 1.0), A(230, 600, 2.0), A(145, 830, 2.5)], [2.4, 2.2, 3.6], 'chain', 1)
    streamer(f, 'arm_l', [A(740, 340, 1.5), A(770, 560, 2.0), A(750, 760, 2.5)], [2.4, 2.2, 3.2], 'chain', 2)
    for side, u in (('r', 400), ('l', 610)):
        foot = f.xat(u, 22.4, -0.3)
        f.chain(f'shin_{side}', [foot + (0, -8.0, 0.6), foot + (0, -1.0, 0.2)], [3.2, 3.4], name='boot')
        f.box(f'shin_{side}', foot + (0, 0.5, -0.6), (4.0, 3.0, 5.4), name='shoe')
    views = {
        'front': dict(box=[(60, 0, 860, 1000)], cam=f.cam_tuple()),
        'back': dict(box=[(850, 210, 1400, 995)], yaw=180, pitch=10, yaw_span=30, pitch_span=4),
    }
    return f, views


@recipe('05_')
def berit():
    """万界錬成 ベーリット: long black hair, a white coat edged in black and gold over a black corset and trousers,
    belts with potions and a book, black gloves, a golden cube floating above her raised right hand, platform boots."""
    f = Fig('berit', td=int(os.environ.get('DF_TD', 4)))
    f.camera_at(-20.0, 10.0, 23.3, 440, 1155)
    A = f.at
    f.humanoid(hip_y=0.0, waist_y=-5.0, neck_y=-12.5, shoulder=tuple(A(300, 345, 0)), elbow=tuple(A(215, 455, -1.5)),
               hip=(-1.8, 0.0, 0), knee=(-2.0, 11.5, -0.4))
    f.mirror_x = float(A(385, 700)[0])
    head = A(395, 170, 0)
    f.box('head', head, (9.0, 10.4, 9.0), name='head')
    f.box('head', head + (0, -5.6, 0.4), (9.8, 1.4, 9.8), name='hair_top')
    for sx in (-1, 1):
        f.box('head', head + (sx * 5.0, 5.0, -0.2), (1.6, 8.0, 4.8), name='hair_side')
    f.box('torso', A(420, 420, 4.2), (10.0, 18.0, 2.6), name='hair_back')
    f.chain('torso', [A(480, 230, 2.0), A(560, 330, 3.0), A(610, 470, 3.5)], [4.0, 4.6, 3.0], d=[3.0, 2.6, 1.6], name='hair_flow',
            up=(0, 0, -1))
    f.box('torso', A(385, 430, 0), (6.8, 7.6, 4.0), name='chest')
    f.box('torso', A(385, 520, 0), (7.2, 2.0, 4.4), name='belt')
    f.frustum('hips', (A(395, 540, 0), 9.0, 5.4), (A(430, 1040, 0) + (0, 0, 0.6), 18.0, 9.0), name='coat')
    # right arm raised to the floating cube, left arm down
    sh_r, el_r, ha_r = A(300, 345, 0), A(215, 455, -1.5), A(130, 320, -3.0)
    limb(f, 'arm_r', 'fore_r', sh_r, el_r, ha_r, [3.0, 2.8], [3.0, 3.2], sleeve=(A(260, 360, 0), A(175, 450, -1.2), 4.4, 4.8, 4.0, 4.0))
    sh_l, el_l, ha_l = A(470, 345, 0), A(545, 470, -0.6), A(640, 595, -1.6)
    limb(f, 'arm_l', 'fore_l', sh_l, el_l, ha_l, [3.0, 2.8], [3.0, 3.4], sleeve=(A(485, 360, 0), A(560, 520, -0.4), 4.4, 5.0, 4.0, 4.0))
    cube = f.bone('cube', 'fore_r', tuple(A(160, 210, -3.5)), anim='spin', speed=0.03)
    f.box(cube, A(160, 210, -3.5), (5.0, 5.0, 5.0), rot=(0.3, 0.6, 0.2), name='cube')
    for i, (u, v) in enumerate(((150, 95), (90, 130), (215, 140), (60, 235), (215, 245))):
        card(f, 'root', A(u, v, -3.0), (1.6, 1.6), i, name='bit', amp=0.4)
    # potions and the book at the hips
    f.box('hips', A(220, 590, -1.0), (2.6, 5.0, 2.6), name='potions')
    f.box('hips', A(515, 590, -2.6), (4.0, 6.0, 1.6), rot=(0, 0.3, 0), name='book')
    for side, u, z in (('r', 335, -0.4), ('l', 535, -0.4)):
        foot = f.xat(u, 22.4, z)
        f.chain(f'shin_{side}', [foot + (0, -11.0, 0.8), foot + (0, -1.0, 0.3)], [3.0, 3.4], name='leg')
        f.box(f'shin_{side}', foot + (0, 0.3, -0.6), (4.4, 3.4, 6.0), name='boot')
        hip = f.xat(330 if side == 'r' else 445, 0.5, 0.0)
        f.chain(f'leg_{side}', [hip, foot + (0, -11.0, 0.8)], [3.4, 3.2], name='thigh')
    views = {
        'front': dict(box=[(30, 0, 740, 1199)], cam=f.cam_tuple()),
        'back': dict(box=[(780, 260, 1230, 1180)], yaw=180, pitch=10, yaw_span=40, pitch_span=4),
    }
    return f, views


def plate4(f, bone, p0, p1, p2, p3, thick, name='plate'):
    """A slab through four corners (in order round the edge), thick along its normal: wings, capes, banners."""
    P = np.array([p0, p1, p2, p3], float)
    n = np.cross(P[1] - P[0], P[3] - P[0]) + np.cross(P[2] - P[1], P[2] - P[3]) * 0
    n = n / max(1e-9, np.linalg.norm(n)) * thick / 2
    return f.hexa(bone, list(P - n) + list(P + n), name=name)


@recipe('08_')
def nortia():
    """無法遊戯 ノルティア: pastel rainbow hair, a red and navy jester's hat, a white and red jacket with gold buttons,
    navy shorts and coat tails, one leg kicked up, dice and cards floating round her."""
    f = Fig('nortia', td=int(os.environ.get('DF_TD', 4)))
    f.camera_at(-30.0, 10.0, 19.3, 365, 985)
    A = f.at
    f.humanoid(hip_y=0.5, waist_y=-5.0, neck_y=-12.0, shoulder=tuple(A(285, 345, 0)), elbow=tuple(A(205, 335, -2.0)),
               hip=tuple(f.xat(305, 0.5, 0)), knee=tuple(A(255, 720, -2.0)))
    f.mirror_x = float(A(360, 600)[0])
    head = A(355, 215, 0)
    f.box('head', head, (10.0, 10.2, 10.0), name='head')
    f.decal('head', 'head', 'north', (1010, 158, 1352, 438))
    f.chain('head', [head + (0.5, -4.6, 0.6), A(470, 60, 1.5), A(585, 80, 2.5), A(600, 140, 3.0)], [9.0, 6.4, 3.6, 2.0],
            d=[8.0, 5.6, 3.2, 1.8], name='hat')
    for sx in (-1, 1):
        f.box('head', head + (sx * 5.2, 4.6, -0.4), (1.6, 7.0, 5.0), name='hair_side')
    f.box('torso', A(360, 380, 4.0), (9.0, 10.0, 2.4), name='hair_back')
    f.box('torso', A(365, 420, 0), (7.4, 7.6, 4.6), name='chest')
    f.frustum('hips', (A(365, 490, 0), 8.6, 5.4), (A(355, 690, 0), 16.0, 9.0), name='coat')
    sh_r, el_r, ha_r = A(285, 345, 0), A(205, 335, -2.0), A(140, 320, -4.0)
    limb(f, 'arm_r', 'fore_r', sh_r, el_r, ha_r, [2.8, 2.6], [3.6, 2.4], sleeve=(A(250, 340, -0.6), A(175, 390, -2.4), 4.4, 5.2, 4.4, 4.4))
    sh_l, el_l, ha_l = A(445, 350, 0), A(480, 450, 0.4), A(495, 540, -0.2)
    limb(f, 'arm_l', 'fore_l', sh_l, el_l, ha_l, [2.8, 2.6], [3.4, 2.4])
    # right leg kicked up, left leg standing
    knee_r, foot_r = A(255, 720, -2.0), A(255, 840, -2.6)
    f.chain('leg_r', [f.xat(305, 1.0, 0), knee_r], [3.2, 3.0], name='thigh')
    f.chain('shin_r', [knee_r, foot_r], [3.0, 3.4], name='shin')
    f.box('shin_r', foot_r + (0, 1.6, -0.6), (4.4, 3.2, 5.4), name='boot')
    foot_l = f.xat(400, 22.4, -0.4)
    f.chain('leg_l', [f.xat(405, 1.0, 0), foot_l + (0, -11.0, 0.4)], [3.2, 3.0], name='thigh')
    f.chain('shin_l', [foot_l + (0, -11.0, 0.4), foot_l + (0, -1.0, 0.2)], [3.0, 3.4], name='shin')
    f.box('shin_l', foot_l + (0, 0.4, -0.6), (4.4, 3.2, 5.4), name='boot')
    for i, (u, v, z, s) in enumerate(((135, 145, -1, 4.0), (115, 440, -2, 4.4), (215, 550, -4, 2.8), (500, 360, -2, 2.6),
                                     (615, 210, 1, 2.6))):
        b = f.bone(f'dice{i}', 'root', tuple(A(u, v, z)), anim='spin', speed=0.02 + 0.01 * i, ax=float(i % 3))
        f.box(b, A(u, v, z), (s, s, s), rot=(0.4, 0.5 + i, 0.2), name='dice')
    for i, (u, v, z) in enumerate(((205, 75, 0), (55, 255, -1), (600, 325, 0))):
        card(f, 'root', A(u, v, z), (2.6, 3.6), i, rot=(0, 0.4, 0.2 * (i - 1)))
    views = {
        'front': dict(box=[(0, 0, 680, 1000)], drop=[(30, 680, 175, 890), (480, 700, 680, 880)], cam=f.cam_tuple()),
        'back': dict(box=[(650, 220, 990, 895)], yaw=180, pitch=10, yaw_span=40, pitch_span=4),
    }
    return f, views


@recipe('09_')
def lucifara():
    """失楽堕天 ルシファーラ: a fallen angel with great black wings hung with golden crosses, a crown of crosses on long
    white hair, red eyes, a black gown with a white front panel and golden crosses spreading into a wide train."""
    f = Fig('lucifara', td=int(os.environ.get('DF_TD', 4)))
    f.camera_at(-15.0, 10.0, 19.3, 485, 965)
    A = f.at
    f.humanoid(hip_y=0.0, waist_y=-5.0, neck_y=-13.0, shoulder=tuple(A(405, 285, 0)), elbow=tuple(A(355, 415, -1.0)),
               hip=(-1.8, 0.0, 0), knee=(-1.8, 12.0, 0))
    f.mirror_x = float(A(485, 600)[0])
    head = A(472, 168, 0)
    f.box('head', head, (8.6, 9.6, 8.6), name='head')
    cr = f.bone('crown', 'head', tuple(head + (0, -5.4, 0)), anim='spin', speed=0.01)
    ring(f, cr, head + (0, -5.4, 0.2), 4.8, 12, 0.8, 1.0, name='crown')
    for i in range(5):
        a = 2 * math.pi * i / 5 - math.pi / 2
        p = head + (math.cos(a) * 4.8, -7.4, math.sin(a) * 4.8 + 0.2)
        f.box(cr, p, (0.7, 3.4, 0.7), name='crown_cross')
        f.box(cr, p + (0, -0.6, 0), (2.2, 0.7, 0.7), rot=(0, -a + math.pi / 2, 0), name='crown_cross')
    for sx in (-1, 1):
        f.box('head', head + (sx * 4.7, 5.4, -0.4), (1.4, 8.0, 4.4), name='hair_side')
    f.box('torso', A(478, 420, 3.8), (9.0, 18.0, 2.6), name='hair_back')
    # wings: a broad fan of black feathers each side, rooted between the shoulder blades
    for side, sx, pts in (('r', -1, ((395, 215, 3.4), (75, 90, 7.0), (35, 770, 7.0), (330, 690, 4.4))),
                          ('l', 1, ((560, 215, 3.4), (900, 95, 7.0), (930, 760, 7.0), (640, 690, 4.4)))):
        root = A(*pts[0])
        w = f.bone(f'wing_{side}', 'torso', tuple(root), anim=f'wing_{side}', amp=0.08, speed=0.06)
        plate4(f, w, *[A(*p) for p in pts], 1.4, name='wing')
    f.box('torso', A(478, 330, 0), (7.0, 7.0, 4.2), name='chest')
    f.frustum('hips', (A(480, 405, 0), 8.0, 5.0), (A(490, 955, 0) + (0, 0, 1.0), 25.0, 15.0), name='gown')
    sh_r, el_r, ha_r = A(405, 285, 0), A(355, 415, -1.0), A(460, 340, -4.0)
    limb(f, 'arm_r', 'fore_r', sh_r, el_r, ha_r, [2.6, 2.4], [2.4, 2.2], sleeve=(A(330, 400, -0.6), A(290, 600, -1.0), 5.0, 6.4, 3.6, 3.4))
    sh_l, el_l, ha_l = A(560, 290, 0), A(600, 420, -0.4), A(612, 520, -1.0)
    limb(f, 'arm_l', 'fore_l', sh_l, el_l, ha_l, [2.6, 2.4], [2.4, 2.2], sleeve=(A(590, 330, 0.2), A(630, 640, 0.2), 5.0, 6.4, 3.6, 3.4))
    views = {
        'front': dict(box=[(20, 0, 960, 1000)], drop=[(800, 0, 1536, 130)], cam=f.cam_tuple()),
        'back': dict(box=[(850, 200, 1420, 950)], yaw=180, pitch=10, yaw_span=30, pitch_span=4),
    }
    return f, views


def boots(f, us, z=-0.3, top=11.0, w=(3.0, 3.4), shoe=(4.2, 3.0, 5.4), hips=None):
    """Shins and shoes standing at sheet columns us = (right, left); hips = (right, left) columns to add thighs."""
    for i, (side, u) in enumerate(zip(('r', 'l'), us)):
        foot = f.xat(u, 22.4, z)
        f.chain(f'shin_{side}', [foot + (0, -top, 0.6), foot + (0, -1.0, 0.2)], list(w), name='shin')
        f.box(f'shin_{side}', foot + (0, 0.5, -0.6), shoe, name='shoe')
        if hips:
            f.chain(f'leg_{side}', [f.xat(hips[i], 0.5, 0), foot + (0, -top, 0.6)], [w[1] + 0.4, w[1]], name='thigh')


@recipe('10_')
def taika():
    """超克覇王 辿迦: spiky black hair tipped red, red oni horns, a black and red kimono open on a bare tattooed
    shoulder, a red sash, armoured forearms, baggy hakama bound at the shins, a long red cloth streaming from his
    left hand."""
    f = Fig('taika', td=int(os.environ.get('DF_TD', 4)))
    f.camera_at(-10.0, 10.0, 19.3, 362, 975)
    A = f.at
    f.humanoid(hip_y=0.0, waist_y=-5.0, neck_y=-12.6, shoulder=tuple(A(240, 295, 0)), elbow=tuple(A(205, 420, -0.5)),
               hip=(-2.0, 0.0, 0), knee=(-2.6, 12.0, 0))
    f.mirror_x = float(A(355, 600)[0])
    head = A(345, 170, 0)
    f.box('head', head, (9.6, 10.4, 9.6), name='head')
    for sx, (u0, u1) in ((-1, (262, 255)), (1, (420, 430))):
        f.chain('head', [head + (sx * 3.4, -4.8, 0), A(u1, 30, 0.5)], [2.0, 0.6], d=[2.0, 0.6], name='horn')
    f.box('torso', A(360, 340, 0), (8.6, 7.6, 4.8), name='chest')
    f.box('torso', A(360, 405, 0), (9.0, 2.6, 5.2), name='sash')
    f.frustum('hips', (A(360, 425, 0), 9.4, 5.4), (A(355, 800, 0), 17.0, 8.0), name='hakama')
    sh_r, el_r, ha_r = A(240, 295, 0), A(205, 420, -0.5), A(190, 510, -1.2)
    limb(f, 'arm_r', 'fore_r', sh_r, el_r, ha_r, [3.6, 3.2], [3.8, 3.0], sleeve=(A(205, 360, 0), A(200, 560, -0.4), 5.0, 5.4, 4.4, 4.0))
    sh_l, el_l, ha_l = A(475, 295, 0), A(505, 420, -0.5), A(480, 500, -1.6)
    limb(f, 'arm_l', 'fore_l', sh_l, el_l, ha_l, [3.6, 3.2], [3.8, 3.0], sleeve=(A(505, 350, 0), A(505, 470, -0.4), 4.6, 4.8, 4.2, 4.0))
    streamer(f, 'fore_l', [A(520, 440, 0.5), A(620, 600, 1.5), A(700, 750, 2.0), A(740, 860, 2.0)], [3.0, 5.0, 5.4, 4.0], 'cloth', 0)
    streamer(f, 'hips', [A(250, 440, -1.0), A(190, 600, -0.5), A(150, 740, 0.0)], [3.0, 4.0, 3.0], 'cloth', 1)
    boots(f, (235, 500), w=(3.2, 3.6), shoe=(4.4, 2.8, 5.6))
    views = {
        'front': dict(box=[(100, 0, 840, 1000)], cam=f.cam_tuple()),
        'back': dict(box=[(850, 100, 1420, 980)], drop=[(560, 240, 1000, 340)], yaw=180, pitch=10, yaw_span=30, pitch_span=4),
    }
    views['front']['drop'] = [(600, 240, 1000, 340)]
    return f, views


@recipe('11_')
def mary_sue():
    """覚醒進化 メアリー・スー: long golden hair with navy ribbons and blue crystals, a white and navy dress with gold
    edging and a brown corset belt, crystal-studded bracers, her raised right hand among floating gems of every
    colour, stockings and buckled boots."""
    f = Fig('mary_sue', td=int(os.environ.get('DF_TD', 4)))
    f.camera_at(-15.0, 10.0, 19.6, 515, 980)
    A = f.at
    f.humanoid(hip_y=0.0, waist_y=-5.0, neck_y=-12.6, shoulder=tuple(A(385, 300, 0)), elbow=tuple(A(300, 355, -1.5)),
               hip=(-1.8, 0.0, 0), knee=(-2.2, 12.0, 0))
    f.mirror_x = float(A(470, 600)[0])
    head = A(455, 150, 0)
    f.box('head', head, (9.4, 10.0, 9.4), name='head')
    for sx in (-1, 1):
        f.box('head', head + (sx * 5.0, 5.4, -0.2), (1.6, 8.0, 4.6), name='hair_side')
    f.box('torso', A(465, 400, 4.0), (10.0, 16.0, 2.6), name='hair_back')
    f.box('torso', A(470, 330, 0), (7.4, 6.4, 4.4), name='chest')
    f.box('torso', A(475, 410, 0), (7.6, 2.6, 4.6), name='corset')
    f.frustum('hips', (A(480, 430, 0), 8.6, 5.2), (A(490, 800, 0), 21.0, 9.0), name='skirt')
    for u, v in ((655, 255), (380, 255)):
        f.box('torso', A(u, v, -0.5), (1.8, 3.2, 1.8), rot=(0, 0.6, 0.3), name='crystal')
    sh_r, el_r, ha_r = A(385, 300, 0), A(300, 355, -1.5), A(255, 265, -3.2)
    limb(f, 'arm_r', 'fore_r', sh_r, el_r, ha_r, [2.8, 2.6], [3.2, 3.0], sleeve=(A(330, 310, -1.0), A(280, 380, -2.0), 3.8, 4.4, 3.8, 3.8))
    sh_l, el_l, ha_l = A(565, 300, 0), A(645, 420, 0), A(700, 535, -0.6)
    limb(f, 'arm_l', 'fore_l', sh_l, el_l, ha_l, [2.8, 2.6], [3.4, 3.0], sleeve=(A(600, 320, 0), A(660, 470, 0), 4.0, 4.4, 3.8, 3.8))
    for i, (u, v, s) in enumerate(((180, 175, 3.4), (260, 115, 4.0), (315, 195, 2.8), (170, 270, 3.2))):
        b = f.bone(f'gem{i}', 'fore_r', tuple(A(u, v, -3.5)), anim='float', amp=0.5, speed=0.05, phase=i * 1.5)
        f.box(b, A(u, v, -3.5), (s * 0.7, s * 1.3, s * 0.7), rot=(0, 0.6, 0), name='gem')
    boots(f, (400, 635), w=(3.2, 3.6), shoe=(4.4, 3.0, 5.6), hips=(415, 515))
    views = {
        'front': dict(box=[(120, 0, 790, 1000)], cam=f.cam_tuple()),
        'back': dict(box=[(880, 190, 1280, 980)], yaw=180, pitch=10, yaw_span=30, pitch_span=4),
    }
    return f, views


@recipe('12_')
def savior():
    """救世天主 セイヴァー: white hair under a halo of golden crosses hung with blue banners, a white coat banded in
    navy and gold with cross panels, his right hand held out to a great glowing blue magic circle."""
    f = Fig('savior', td=int(os.environ.get('DF_TD', 4)))
    f.camera_at(-25.0, 10.0, 19.2, 520, 985)
    A = f.at
    f.humanoid(hip_y=0.0, waist_y=-5.0, neck_y=-12.4, shoulder=tuple(A(420, 330, 0)), elbow=tuple(A(335, 375, -2.0)),
               hip=(-2.0, 0.0, 0), knee=(-2.2, 12.0, 0))
    f.mirror_x = float(A(525, 600)[0])
    head = A(522, 205, 0)
    f.box('head', head, (9.6, 10.0, 9.6), name='head')
    halo = f.bone('halo', 'head', tuple(head + (0, -1.0, 1.4)), anim='spin', speed=0.01, ax=2.0)
    for i in range(16):
        a = 2 * math.pi * i / 16
        p = head + (math.cos(a) * 11.0, -1.0 + math.sin(a) * 11.0, 1.4)
        f.box(halo, p, (0.6, 4.4, 0.6), rot=(0, 0, a), name='halo')
    for i in range(6):
        a = 2 * math.pi * i / 6 - math.pi / 2
        p = head + (math.cos(a) * 11.0, -1.0 + math.sin(a) * 11.0, 1.4)
        f.box(halo, p, (0.8, 3.4, 0.8), name='halo_cross')
        f.box(halo, p + (0, -0.4, 0), (2.4, 0.8, 0.8), name='halo_cross')
    f.box('head', A(800, 310, 2.0), (2.2, 12.0, 0.6), name='banner')
    f.box('torso', A(530, 380, 4.0), (9.6, 10.0, 2.4), name='hair_back')
    f.box('torso', A(535, 390, 0), (8.6, 8.0, 5.0), name='chest')
    f.frustum('hips', (A(535, 460, 0), 11.0, 6.4), (A(560, 930, 0), 24.0, 11.0), name='coat')
    sh_r, el_r, ha_r = A(420, 330, 0), A(335, 375, -2.0), A(265, 372, -4.0)
    limb(f, 'arm_r', 'fore_r', sh_r, el_r, ha_r, [3.0, 2.8], [3.0, 2.6], sleeve=(A(380, 345, -0.6), A(300, 470, -2.0), 5.0, 6.4, 4.4, 4.0))
    sh_l, el_l, ha_l = A(645, 345, 0), A(720, 460, 0), A(775, 560, -0.6)
    limb(f, 'arm_l', 'fore_l', sh_l, el_l, ha_l, [3.0, 2.8], [3.0, 2.6], sleeve=(A(665, 360, 0), A(740, 600, 0), 5.0, 6.4, 4.4, 4.0))
    circle = f.bone('circle', 'fore_r', tuple(A(205, 345, -5.5)), anim='pulse', amp=0.03, speed=0.05)
    f.box(circle, A(205, 345, -5.5), (17.0, 30.0, 0.4), rot=(0, -0.2, 0), name='circle', mat=dict(type='proj', glow=True, glow_min=150))
    boots(f, (400, 640), w=(3.4, 3.8), shoe=(4.6, 3.0, 6.0))
    views = {
        'front': dict(box=[(30, 0, 1000, 1000)], drop=[(850, 30, 1536, 150)], cam=f.cam_tuple()),
        'back': dict(box=[(1010, 170, 1520, 1000)], drop=[(850, 30, 1536, 150)], yaw=180, pitch=10, yaw_span=30, pitch_span=4),
    }
    return f, views


@recipe('13_')
def gokuka():
    """外業呪禍 獄華: grey-lavender hair with black horns and violet charms, a white fur collar, a tattered black and
    violet gown hung with glowing violet crosses and spreading over the ground, skeletal claw hands, a pale flower."""
    f = Fig('gokuka', td=int(os.environ.get('DF_TD', 4)))
    f.camera_at(-25.0, 10.0, 19.0, 330, 960)
    A = f.at
    f.humanoid(hip_y=0.0, waist_y=-5.0, neck_y=-12.6, shoulder=tuple(A(220, 300, 0)), elbow=tuple(A(140, 380, -1.0)),
               hip=(-2.0, 0.0, 0), knee=(-2.2, 12.0, 0))
    f.mirror_x = float(A(320, 600)[0])
    head = A(300, 175, 0)
    f.box('head', head, (9.6, 10.6, 9.6), name='head')
    for sx, tip in ((-1, (345, 30, 1.5)), (1, (440, 35, 1.5))):
        f.chain('head', [head + (sx * 3.0, -5.0, 0.4), A(*tip)], [2.0, 0.6], d=[2.0, 0.6], name='horn')
    f.box('torso', A(310, 420, 4.4), (10.0, 18.0, 2.6), name='hair_back')
    f.frustum('torso', (A(320, 225, 0), 9.0, 7.0), (A(320, 320, 0), 15.0, 9.0), name='fur')
    f.box('torso', A(325, 390, 0), (8.0, 7.0, 4.6), name='chest')
    f.frustum('hips', (A(330, 450, 0), 10.0, 6.0), (A(380, 930, 0) + (0, 0, 1.5), 28.0, 16.0), name='gown')
    sh_r, el_r, ha_r = A(220, 300, 0), A(140, 380, -1.0), A(150, 265, -3.2)
    limb(f, 'arm_r', 'fore_r', sh_r, el_r, ha_r, [3.0, 2.8], [2.8, 2.2], sleeve=(A(200, 300, -0.4), A(135, 560, -0.8), 5.0, 6.2, 4.0, 3.6))
    f.box('fore_r', A(150, 205, -3.4), (1.6, 2.4, 1.6), name='flower')
    sh_l, el_l, ha_l = A(430, 300, 0), A(470, 430, -1.0), A(380, 540, -4.0)
    limb(f, 'arm_l', 'fore_l', sh_l, el_l, ha_l, [3.0, 2.8], [2.8, 2.4], sleeve=(A(450, 320, 0), A(500, 600, -0.4), 5.0, 6.0, 4.0, 3.6))
    f.box('fore_l', A(350, 530, -4.6), (4.0, 5.0, 2.0), rot=(0, 0.3, 0.3), name='claw')
    views = {
        'front': dict(box=[(40, 0, 650, 1000)], cam=f.cam_tuple()),
        'back': dict(box=[(650, 130, 945, 905)], yaw=180, pitch=10, yaw_span=30, pitch_span=4),
    }
    return f, views


@recipe('14_')
def merlinus():
    """魔導深淵 メルリヌス: a great violet witch's hat with golden squares and hanging cyan lanterns, long white hair,
    violet eyes, a dark violet robe patterned in gold and glowing cyan runes, an open spellbook floating above her
    right hand."""
    f = Fig('merlinus', td=int(os.environ.get('DF_TD', 4)))
    f.camera_at(-25.0, 10.0, 19.0, 330, 965)
    A = f.at
    f.humanoid(hip_y=0.0, waist_y=-5.0, neck_y=-12.0, shoulder=tuple(A(245, 345, 0)), elbow=tuple(A(185, 430, -1.0)),
               hip=(-2.0, 0.0, 0), knee=(-2.2, 12.0, 0))
    f.mirror_x = float(A(330, 600)[0])
    head = A(340, 245, 0)
    f.box('head', head, (9.0, 9.0, 9.0), name='head')
    hat = f.bone('hat', 'head', tuple(head + (0, -4.5, 0)), anim='sway', amp=0.02, speed=0.04, ax=2.0)
    f.frustum(hat, (A(345, 150, 0), 17.0, 17.0), (A(345, 165, 0), 18.0, 18.0), name='brim')
    f.chain(hat, [A(345, 150, 0.5), A(390, 80, 1.5), A(460, 45, 2.5), A(540, 120, 3.0)], [9.0, 6.0, 3.6, 1.6],
            d=[9.0, 6.0, 3.6, 1.6], name='hat_cone')
    f.box('torso', A(345, 470, 4.2), (10.0, 18.0, 2.6), name='hair_back')
    for sx in (-1, 1):
        f.box('head', head + (sx * 4.8, 6.0, -0.6), (1.6, 9.0, 4.4), name='hair_side')
    f.box('torso', A(335, 400, 0), (7.6, 7.6, 4.4), name='chest')
    f.frustum('hips', (A(340, 470, 0), 9.6, 5.8), (A(330, 830, 0), 21.0, 10.0), name='robe')
    sh_r, el_r, ha_r = A(245, 345, 0), A(185, 430, -1.0), A(140, 420, -3.0)
    limb(f, 'arm_r', 'fore_r', sh_r, el_r, ha_r, [2.8, 2.6], [2.6, 2.2], sleeve=(A(230, 360, -0.4), A(160, 600, -0.8), 5.0, 6.4, 4.2, 3.8))
    sh_l, el_l, ha_l = A(430, 350, 0), A(480, 460, 0), A(500, 560, -0.6)
    limb(f, 'arm_l', 'fore_l', sh_l, el_l, ha_l, [2.8, 2.6], [2.6, 2.2], sleeve=(A(450, 365, 0), A(520, 650, 0), 5.0, 6.4, 4.2, 3.8))
    book = f.bone('book', 'fore_r', tuple(A(110, 300, -4.0)), anim='float', amp=0.5, speed=0.05)
    f.box(book, A(110, 300, -4.0), (10.0, 7.0, 1.6), rot=(0.2, 0.5, -0.15), name='book')
    for i, (u, v) in enumerate(((550, 190), (530, 340))):
        card(f, hat, A(u, v, 0.0), (1.2, 2.8), i, name='lantern', amp=0.3)
    boots(f, (250, 405), w=(3.2, 3.6), shoe=(4.6, 3.0, 5.8))
    views = {
        'front': dict(box=[(0, 0, 615, 1000)], cam=f.cam_tuple()),
        'back': dict(box=[(605, 170, 925, 920)], yaw=180, pitch=10, yaw_span=30, pitch_span=4),
    }
    return f, views


@recipe('20_')
def arcana():
    """運命流転 アルカナ: a halo of golden stars, long white-lilac hair, great lilac and white wings set with glowing
    golden stars and hung with jewelled chains, a white and violet gown with golden stars, chains of light held
    between her hands."""
    f = Fig('arcana', td=int(os.environ.get('DF_TD', 4)))
    f.camera_at(-20.0, 10.0, 19.0, 470, 975)
    A = f.at
    f.humanoid(hip_y=0.0, waist_y=-5.0, neck_y=-12.6, shoulder=tuple(A(390, 300, 0)), elbow=tuple(A(370, 410, -1.0)),
               hip=(-2.0, 0.0, 0), knee=(-2.2, 12.0, 0))
    f.mirror_x = float(A(470, 600)[0])
    head = A(468, 192, 0)
    f.box('head', head, (9.0, 10.0, 9.0), name='head')
    halo = f.bone('halo', 'head', tuple(head + (0, -6.0, 1.5)), anim='spin', speed=0.01)
    ring(f, halo, head + (0, -6.0, 1.5), 6.4, 14, 0.7, 0.8, name='halo', tilt=(1.2, 0.0))
    for i, (u, v) in enumerate(((470, 60), (555, 75), (380, 125), (590, 140))):
        f.box(halo, A(u, v, 1.5), (2.4, 2.4, 0.6), rot=(0, 0, 0.78), name='star')
    for sx in (-1, 1):
        f.box('head', head + (sx * 4.8, 6.0, -0.4), (1.6, 10.0, 4.6), name='hair_side')
    f.box('torso', A(470, 450, 4.4), (11.0, 20.0, 2.8), name='hair_back')
    for side, pts in (('r', ((395, 250, 3.6), (150, 40, 7.0), (30, 560, 7.0), (300, 700, 4.6))),
                      ('l', ((555, 250, 3.6), (690, 80, 7.0), (820, 520, 7.0), (640, 640, 4.6)))):
        w = f.bone(f'wing_{side}', 'torso', tuple(A(*pts[0])), anim=f'wing_{side}', amp=0.08, speed=0.06)
        plate4(f, w, *[A(*p) for p in pts], 1.4, name='wing')
    f.box('torso', A(470, 345, 0), (7.4, 7.0, 4.4), name='chest')
    f.frustum('hips', (A(470, 420, 0), 9.0, 5.4), (A(430, 955, 0) + (0, 0, 1.0), 26.0, 13.0), name='gown')
    sh_r, el_r, ha_r = A(390, 300, 0), A(370, 410, -1.0), A(440, 400, -4.0)
    limb(f, 'arm_r', 'fore_r', sh_r, el_r, ha_r, [2.6, 2.4], [2.4, 2.2], sleeve=(A(360, 330, -0.4), A(330, 600, -0.6), 5.6, 7.0, 4.0, 3.6))
    sh_l, el_l, ha_l = A(555, 305, 0), A(620, 360, -1.4), A(690, 345, -3.0)
    limb(f, 'arm_l', 'fore_l', sh_l, el_l, ha_l, [2.6, 2.4], [2.4, 2.2], sleeve=(A(580, 330, -0.4), A(640, 520, -1.2), 5.0, 6.4, 4.0, 3.6))
    views = {
        'front': dict(box=[(10, 0, 900, 1000)], drop=[(880, 20, 1536, 220)], cam=f.cam_tuple()),
        'back': dict(box=[(890, 220, 1380, 1000)], drop=[(880, 20, 1536, 220)], yaw=180, pitch=10, yaw_span=30, pitch_span=4),
    }
    return f, views

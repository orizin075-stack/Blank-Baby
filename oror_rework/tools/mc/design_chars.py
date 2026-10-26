"""The 37 characters of the user's design sheets as geometry for designfig: each recipe returns (Fig, views).

views: per sheet view, the boxes the figure is cut from (sheet pixels), boxes to leave out (a held weapon the mob
holds as its relic instead, sparks), an initial yaw/pitch for the camera fit and the pose the figure stands in there.
"""
import math, os
import numpy as np
from designfig import Fig
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

"""Hand-held props for the sculpted characters. The bosses now carry their 3D relic items (rendered by
MindHeldItems), so weapon builders are no-ops; body features that recipes hang on the hands (claws,
knuckles, vine fingers) and free-floating objects (grimoires) are sculpted."""
import math
import numpy as np
import sculpt as SC
import trinkets as TK

POINT_FORWARD = (1.25, 0.0, 0.0)
POINT_DOWN = (2.9, 0.0, 0.0)
UPRIGHT = (0.12, 0.0, 0.0)

def upright(side, lean=0.28):
    return (0.12, 0.0, -lean if side == 'r' else lean)

def hand(h, side='r', rot=(0.0, 0.0, 0.0)):
    fore = h.fore_r if side == 'r' else h.fore_l
    px = fore.pivot[0]
    y = h.hand_y
    b = h.rig.bone('grip_' + side, fore, (px, y, 0), rot=(rot[0] * 0.25, rot[1], rot[2]))
    return b, (px, y, 0)

def _noop(*a, **k):
    if len(a) > 1 and isinstance(a[1], tuple):
        return a[1]
    return (0, 0, 0)

katana = flask = staff = star_head = hammer = dragon_head = wrench = sword = scroll = cross_head = crook_head = _noop

def book(bone, at, cover, page):
    TK.book(bone, at, cover, page, w=3.2, h=4.2, d=1.3)
    return at

def claws(h, side, mat, length=4):
    fore = h.fore_r if side == 'r' else h.fore_l
    x = fore.pivot[0]
    y = h.wrist_y + 1.4
    sgn = -1 if side == 'r' else 1
    for k in range(3):
        dx = (k - 1) * 0.42
        p0 = np.array([x + dx, y, -0.2])
        pts = SC.bezier(p0, p0 + (dx * 0.4, length * 0.55, -0.5), p0 + (dx * 0.6, length * 0.85, -length * 0.45), n=8)
        SC.sweep(fore, pts, lambda t: 0.3 * (1 - 0.85 * t), lambda t: 0.22 * (1 - 0.8 * t), dict(mat, flip_t=False), k=8,
                 caps=('round', 'point'), name='claw', info={'hem': False})

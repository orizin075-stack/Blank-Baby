"""Display transforms for 3D items, derived from vanilla's transform chain, and previews of the item in a
player's hand (third person, first person) using that exact chain (ItemInHandLayer / ItemInHandRenderer /
ItemTransform / ItemRenderer, 1.21.1)."""
import math
import numpy as np
from PIL import Image, ImageDraw
import forge3d as F

DEG = math.pi / 180

def T(x, y, z):
    M = np.eye(4); M[:3, 3] = (x, y, z); return M

def S(x, y=None, z=None):
    return np.diag([x, x if y is None else y, x if z is None else z, 1.0])

def Rx(a):
    c, s = math.cos(a), math.sin(a); M = np.eye(4); M[1:3, 1:3] = [[c, -s], [s, c]]; return M

def Ry(a):
    c, s = math.cos(a), math.sin(a); M = np.eye(4); M[0, 0], M[0, 2], M[2, 0], M[2, 2] = c, s, -s, c; return M

def Rz(a):
    c, s = math.cos(a), math.sin(a); M = np.eye(4); M[0:2, 0:2] = [[c, -s], [s, c]]; return M

def rot_xyz(rx, ry, rz):
    """Quaternionf.rotationXYZ(x, y, z) as a matrix: Rx * Ry * Rz (degrees in)."""
    return Rx(rx * DEG) @ Ry(ry * DEG) @ Rz(rz * DEG)

def item_transform(t, left=False):
    rx, ry, rz = t['rotation']
    tx, ty, tz = (v / 16.0 for v in t['translation'])
    sx, sy, sz = t['scale']
    if left:
        ry, rz, tx = -ry, -rz, -tx
    return T(tx, ty, tz) @ rot_xyz(rx, ry, rz) @ S(sx, sy, sz)

def euler_xyz(R):
    """Inverse of rot_xyz for a 3x3 rotation: returns degrees (x, y, z) with R = Rx Ry Rz."""
    # R = Rx Ry Rz ; R[0,2] = sin(y)
    sy = max(-1.0, min(1.0, R[0, 2]))
    y = math.asin(sy)
    if abs(sy) < 0.9999:
        x = math.atan2(-R[1, 2], R[2, 2])
        z = math.atan2(-R[0, 1], R[0, 0])
    else:
        x = math.atan2(R[2, 1], R[1, 1]); z = 0.0
    return [round(x / DEG, 2), round(y / DEG, 2), round(z / DEG, 2)]

VANILLA = {
    'thirdperson_righthand': dict(rotation=[0, -90, 55], translation=[0, 4.0, 0.5], scale=[0.85, 0.85, 0.85]),
    'firstperson_righthand': dict(rotation=[0, -90, 25], translation=[1.13, 3.2, 1.13], scale=[0.68, 0.68, 0.68]),
}

# ---------------------------------------------------------------- player model (HumanoidModel, standing, holding)
ARM_R = dict(pivot=(-5, 2, 0), box=(-3, -2, -2, 4, 12, 4))
ARM_L = dict(pivot=(5, 2, 0), box=(-1, -2, -2, 4, 12, 4))

def part_matrix(pivot, rot):
    """ModelPart.translateAndRotate in block units (rot = x, y, z radians, applied ZYX)."""
    return T(*(p / 16.0 for p in pivot)) @ Rz(rot[2]) @ Ry(rot[1]) @ Rx(rot[0])

def entity_base(scale=0.9375):
    # LivingEntityRenderer: rotY(180 - bodyRot) (bodyRot 0 -> 180), scale(-1,-1,1), player scale, translate(0,-1.501,0)
    return Ry(math.pi) @ S(-1, -1, 1) @ S(scale) @ T(0, -1.501, 0)

def hand_frame(arm_rot=(-math.pi / 10, 0, 0), left=False):
    """Pose matrix handed to ItemRenderer for THIRD_PERSON_*_HAND (before the display transform)."""
    arm = ARM_L if left else ARM_R
    rot = arm_rot if not left else (arm_rot[0], -arm_rot[1], -arm_rot[2])
    M = entity_base() @ part_matrix(arm['pivot'], rot)
    M = M @ Rx(-math.pi / 2) @ Ry(math.pi) @ T((-1 if left else 1) / 16.0, 0.125, -0.625)
    return M

def fp_frame(left=False):
    """First person: ItemInHandRenderer.applyItemArmTransform (no swing, equipped)."""
    i = -1 if left else 1
    return T(i * 0.56, -0.52, -0.72)

def hand_point(left=False):
    """Centre of the fist, in the arm's local block units (bottom of the 12-long arm, centred)."""
    arm = ARM_L if left else ARM_R
    x, y, z, w, h, d = arm['box']
    return np.array([(x + w / 2) / 16.0, (y + h - 1.5) / 16.0, (z + d / 2) / 16.0, 1.0])

def frame_from(y_dir, z_dir):
    """Rotation whose +Y goes to y_dir and +Z to (z_dir orthogonalised)."""
    y = np.asarray(y_dir, float); y /= np.linalg.norm(y)
    z = np.asarray(z_dir, float); z = z - y * (z @ y); z /= np.linalg.norm(z)
    x = np.cross(y, z)
    return np.stack([x, y, z], 1)

def derive(scale_tp=0.85, scale_fp=0.6, tilt_tp=0.0, tilt_fp=0.0, grip_fp=(3.5, 3.5), hold='sword'):
    """Display transforms for a model whose grip is at the block centre, axis +Y, front (drawing) +Z."""
    if hold in ('fist', 'shield', 'palm'):
        return derive_worn(hold, scale_tp, scale_fp)
    if hold == 'staff':
        return derive_staff(scale_tp, scale_fp)
    out = {}
    # third person: grip -> the fist, blade along the vanilla sword's blade
    v = VANILLA['thirdperson_righthand']
    Mv = item_transform(v)
    arm = entity_base() @ part_matrix(ARM_R['pivot'], (-math.pi / 10, 0, 0))
    pre = Rx(-math.pi / 2) @ Ry(math.pi) @ T(1 / 16.0, 0.125, -0.625)
    fist = np.linalg.inv(pre) @ hand_point()            # fist in the item-display frame
    R = Mv[:3, :3] / v['scale'][0] @ (Rz(-45 * DEG + tilt_tp * DEG)[:3, :3])
    out['thirdperson_righthand'] = dict(rotation=euler_xyz(R), translation=[round(c * 16, 3) for c in fist[:3]],
                                        scale=[scale_tp] * 3)
    # first person: grip -> where the vanilla sprite's grip lands
    v = VANILLA['firstperson_righthand']
    Mv = item_transform(v)
    g = np.array([grip_fp[0] / 16.0, grip_fp[1] / 16.0, 0.5, 1.0])
    land = Mv @ (g - np.array([0.5, 0.5, 0.5, 0.0]))
    R = Mv[:3, :3] / v['scale'][0] @ (Rz(-45 * DEG + tilt_fp * DEG)[:3, :3])
    out['firstperson_righthand'] = dict(rotation=euler_xyz(R), translation=[round(c * 16, 3) for c in land[:3]],
                                        scale=[scale_fp] * 3)
    for k in ('thirdperson', 'firstperson'):
        r = out[k + '_righthand']
        out[k + '_lefthand'] = dict(rotation=list(r['rotation']), translation=list(r['translation']), scale=list(r['scale']))
    return out

def derive_staff(scale_tp, scale_fp, lean=12.0):
    """Staves (v0.17.10): upright in the fist, leaning a little forward, the head's front turned forward and slightly
    out; the grip sits just in front of the fist so the shaft clears the forearm. First person: upright at the right of
    the view with the whole head in sight (held like a sword, a staff ran off the top of the screen)."""
    W = hand_frame()                                   # display frame -> entity frame (faces +Z, right hand at -X)
    Rw = W[:3, :3] / np.cbrt(np.linalg.det(W[:3, :3]))
    inv = np.linalg.inv(Rw)
    up = np.array([0.0, math.cos(lean * DEG), math.sin(lean * DEG)])
    face = np.array([-0.5, 0.0, 0.85])
    R = frame_from(inv @ up, inv @ face)
    pre = Rx(-math.pi / 2) @ Ry(math.pi) @ T(1 / 16.0, 0.125, -0.625)
    fist = (np.linalg.inv(pre) @ hand_point())[:3]
    pos = fist + inv @ np.array([0.0, 0.0, 3.5 / 16.0])
    res = {'thirdperson_righthand': dict(rotation=euler_xyz(R), translation=[round(c * 16, 3) for c in pos], scale=[scale_tp] * 3)}
    Rf = frame_from([-0.16, 1.0, -0.12], [0.4, 0.0, 1.0])
    land = np.array([0.52, -0.52, -0.82]) - fp_frame()[:3, 3]
    res['firstperson_righthand'] = dict(rotation=euler_xyz(Rf), translation=[round(c * 16, 3) for c in land], scale=[scale_fp] * 3)
    return res

def gun_fp(scale_fp):
    """First person for guns and cannons (v0.17.10): the barrel (+Y) points into the view from the lower right, the
    decorated side towards the middle, instead of a sword's blade sweeping up across half the screen."""
    Rf = frame_from([-0.12, 0.1, -1.0], [-1.0, 0.35, 0.0])
    land = np.array([0.36, -0.36, -0.55]) - fp_frame()[:3, 3]
    return dict(rotation=euler_xyz(Rf), translation=[round(c * 16, 3) for c in land], scale=[scale_fp] * 3)

def derive_worn(hold, scale_tp, scale_fp):
    """Gauntlets / claws / held-by-the-ear plush (axis along the forearm, knuckles at +u, back of hand +w)
    and shields (face outwards on the forearm, point down)."""
    pre = Rx(-math.pi / 2) @ Ry(math.pi) @ T(1 / 16.0, 0.125, -0.625)
    inv = np.linalg.inv(pre[:3, :3])
    down = inv @ np.array([0, 1.0, 0])          # along the arm towards the hand
    out_ = inv @ np.array([-1.0, 0, 0])          # away from the body (right arm)
    res = {}
    if hold == 'fist':
        R = frame_from(down, out_)
        pos = np.linalg.inv(pre) @ hand_point()
    elif hold == 'palm':
        R = frame_from(-down, out_)
        pos = np.linalg.inv(pre) @ (hand_point() + np.array([0.0, 2.5 / 16.0, -5.0 / 16.0, 0.0]))
    else:
        R = frame_from(-down, out_)
        arm_pt = np.array([(-3.0 - 0.6) / 16.0 - 2.4 / 32 * scale_tp, 6.5 / 16.0, 0.0, 1.0])
        pos = np.linalg.inv(pre) @ arm_pt
    res['thirdperson_righthand'] = dict(rotation=euler_xyz(R), translation=[round(c * 16, 3) for c in pos[:3]], scale=[scale_tp] * 3)
    if hold == 'fist':
        Rf = frame_from([-0.3, 0.25, -1.0], [0, 1.0, 0.2])
        land = np.array([0.42, -0.42, -0.62])
    elif hold == 'palm':
        Rf = frame_from([0.0, 1.0, 0.0], [-0.35, 0.0, 1.0])
        land = np.array([0.40, -0.36, -0.68])
    else:
        Rf = frame_from([0.0, 1.0, 0.0], [-0.35, 0.0, 1.0])
        land = np.array([0.30, -0.42, -0.70])
    # the FP display frame starts after fp_frame(): convert the landing point into it
    land = land - fp_frame()[:3, 3]
    res['firstperson_righthand'] = dict(rotation=euler_xyz(Rf), translation=[round(c * 16, 3) for c in land], scale=[scale_fp] * 3)
    for k in ('thirdperson', 'firstperson'):
        r = res[k + '_righthand']
        res[k + '_lefthand'] = dict(rotation=list(r['rotation']), translation=list(r['translation']), scale=list(r['scale']))
    return res

def model_to_display(t, left=False):
    """OBJ space -> display frame: item_transform then translate(-0.5)."""
    return item_transform(t, left) @ T(-0.5, -0.5, -0.5)

# ---------------------------------------------------------------- previews
def box_quads(M, box, color, T_img):
    x, y, z, w, h, d = (v / 16.0 for v in box)
    V = [(x, y, z), (x + w, y, z), (x + w, y + h, z), (x, y + h, z), (x, y, z + d), (x + w, y, z + d), (x + w, y + h, z + d), (x, y + h, z + d)]
    faces = [((0, 3, 2, 1), (0, 0, -1)), ((4, 5, 6, 7), (0, 0, 1)), ((0, 4, 7, 3), (-1, 0, 0)), ((1, 2, 6, 5), (1, 0, 0)),
             ((0, 1, 5, 4), (0, -1, 0)), ((3, 7, 6, 2), (0, 1, 0))]
    out = []
    for idx, n in faces:
        P = np.array([(M @ np.array([*V[i], 1.0]))[:3] for i in idx])
        N = M[:3, :3] @ np.array(n, float)
        N /= np.linalg.norm(N)
        out.append((P, np.array([(color + 0.5, 0.5)] * 4), N, False, T_img))
    return out

PALETTE = np.array([[[0.36, 0.55, 0.78, 1], [0.84, 0.66, 0.52, 1], [0.2, 0.3, 0.6, 1], [0.32, 0.26, 0.22, 1]]], np.float32)

def player_quads(arm_rot=(-math.pi / 10, 0, 0)):
    base = entity_base()
    out = []
    parts = [((0, 0, 0), (0, 0, 0), (-4, -8, -4, 8, 8, 8), 1), ((0, 0, 0), (0, 0, 0), (-4, 0, -2, 8, 12, 4), 0),
             (ARM_R['pivot'], arm_rot, ARM_R['box'], 1), (ARM_L['pivot'], (0, 0, 0), ARM_L['box'], 1),
             ((-1.9, 12, 0), (0, 0, 0), (-2, 0, -2, 4, 12, 4), 2), ((1.9, 12, 0), (0, 0, 0), (-2, 0, -2, 4, 12, 4), 2)]
    for piv, rot, box, col in parts:
        out += box_quads(base @ part_matrix(piv, rot), box, col, PALETTE)
    return out

def preview_third_person(quads, atlas, display, size=(360, 420), yaws=(-40, 40, 140), left=False):
    ims = []
    Mi = hand_frame(left=left) @ model_to_display(display['thirdperson_' + ('left' if left else 'right') + 'hand'], left)
    items = F.world_quads(quads, atlas, Mi)
    body = player_quads()
    for yaw in yaws:
        ims.append(F.render_quads(items + body, size, F.view_matrix(yaw, 8), frame=(0, 1.2, 3.6)))
    return ims

def preview_first_person(quads, atlas, display, size=(480, 270)):
    Mi = fp_frame() @ model_to_display(display['firstperson_righthand'])
    items = F.world_quads(quads, atlas, Mi)
    # fov 70 vertical: f = 1 / tan(35deg) in units of half the screen height; render_quads span = 2*W/H
    f = 1.0 / math.tan(35 * DEG)
    return F.render_quads(items, size, np.eye(3), persp=f, light=1.0)

def ground(quads):
    """ground / head transforms so the model fits about 0.75 block, centred."""
    allp = np.concatenate([F.to_obj_space(P) for P, *_ in quads])
    lo, hi = allp.min(0), allp.max(0)
    ext = max(hi - lo)
    s = round(min(0.6, 0.75 / ext), 3)
    c = (lo + hi) / 2 - 0.5
    return dict(rotation=[0, 0, 0], translation=[round(-c[0] * s * 16, 3), round(-c[1] * s * 16 + 2, 3), round(-c[2] * s * 16, 3)],
                scale=[s, s, s])

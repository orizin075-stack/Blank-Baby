"""059g: Demiurgos and Teia remade on two different skeletons, after the user's design sheets (22 and 17) and the Ice
and Fire photos they sent ("足短すぎるし 胴体も変だし まったく別のドラゴンなのに造形が同じなのも変").

  * Demiurgos (空創龍王, sheet 22): heavy. A deep chest held high, thick legs long enough to carry it (the forelegs
    as long as the shoulder is high, the hind legs bent back at the hock), a thick neck rising in an S, a wedge head
    with the mouth shut, a violet eye under a frowning brow, gold horns swept back; huge starry wings raised over the
    back, ragged along the lower edge with crystals hanging; rainbow crystals down the back and gold spikes down a
    long thick tail; a jewel in a gold frame on the chest.
  * Teia (光越天龍, sheet 17): slender. A narrow, lighter body on long straight legs, a long neck held almost
    upright, a small head with a long narrow muzzle and a gold visor over a cyan eye, a crest of light blades;
    wings of light blades (no membrane) fanned out from armoured arms; white armour plates trimmed in gold over a
    dark frame, cyan light in the joints; a slim tail ending in a fan of blades.

Model space: pixels, y down (the ground is y = 24), the front is -z. One texel to a pixel (td = 1).
"""
import math
import numpy as np
from paint import M
import creatures_ia as CI
from rig import rot_zyx

RECIPES = {}


def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn


def V(*a):
    return np.asarray(a, float)


def rseg(bone, p0, p1, w, d, mat, up=(0, -1, 0), bevel=1.2, ext=0.0):
    """A bevelled beam: two crossing beams (full width and cut back in depth, and the other way round)."""
    b = min(bevel, w * 0.3, d * 0.3)
    CI.seg(bone, tuple(p0), tuple(p1), w, d - 2 * b, mat, up=up, ext=ext)
    CI.seg(bone, tuple(p0), tuple(p1), w - 2 * b, d, mat, up=up, ext=ext)


def spike(bone, base, tip, w0, mat, w1=None):
    """A spike tapering from base to tip (two links)."""
    base, tip = V(*base), V(*tip)
    mid = base + (tip - base) * 0.55
    w1 = w0 * 0.45 if w1 is None else w1
    CI.chain_boxes(bone, [tuple(base), tuple(mid), tuple(tip)], w0, w1, mat)


def leg3(r, parent, name, anim, pts, widths, mat, claw, toes=3, foot=(5.0, 2.4, 6.0), toe_len=3.0, dew=True, joint=None):
    """Hip/shoulder, knee/elbow, ankle/wrist, foot: the upper link (anim), the lower links (knee), a foot with toes."""
    up = r.bone(name, parent, tuple(pts[0]), anim=anim)
    rseg(up, pts[0], pts[1], widths[0], widths[0] * 1.15, mat, up=(0, 0, -1), bevel=widths[0] * 0.22, ext=widths[0] * 0.45)
    low = r.bone(name + '_low', up, tuple(pts[1]), anim='knee')
    rseg(low, pts[1], pts[2], widths[1], widths[1], mat, up=(0, 0, -1), bevel=widths[1] * 0.2, ext=widths[1] * 0.5)
    rseg(low, pts[2], pts[3], widths[2], widths[2], mat, up=(0, 0, -1), bevel=widths[2] * 0.2, ext=widths[2] * 0.5)
    if joint is not None:
        CI.cbox(low, tuple(pts[1]), (widths[1] * 0.75, widths[1] * 0.75, widths[1] * 0.75), joint)
        CI.cbox(low, tuple(pts[2]), (widths[2] * 0.7, widths[2] * 0.7, widths[2] * 0.7), joint)
    fx, fy, fz = pts[3]
    fw, fh, fl = foot
    CI.rbox(low, (fx - fw / 2, 24.0 - fh, fz - fl * 0.65), (fx + fw / 2, 24.0, fz + fl * 0.35), mat, bevel=0.6)
    for t in range(toes):
        x = fx + (t - (toes - 1) / 2) * fw / toes * 1.05
        z0 = fz - fl * 0.6
        CI.seg(low, (x, 24.0 - fh * 0.55, z0), (x, 24.0 - fh * 0.4, z0 - toe_len), fw / toes * 0.8, fh * 0.75, mat, up=(0, -1, 0))
        spike(low, (x, 24.0 - fh * 0.4, z0 - toe_len + 0.3), (x, 24.0, z0 - toe_len - 2.2), fw / toes * 0.6, claw)
    if dew:
        spike(low, (fx, 24.0 - fh, fz + fl * 0.3), (fx, 23.6, fz + fl * 0.35 + 2.4), 1.0, claw)
    return up, low


def tail_chain(r, parent, start, n, length, w0, w1, mat, rise, amp=0.08, extra=None, up=(0, -1, 0)):
    """n links from start backward (+z), each a bevelled beam; rise(t) gives the y offset per link (negative up).
    extra(bone, p, q, w, i) adds spikes or fins to each link. Returns the last bone and the tip point."""
    p = V(*start)
    bone = parent
    L = length / n
    for i in range(n):
        t = i / n
        w = w0 + (w1 - w0) * t
        bone = r.bone(f'tail{i + 1}', bone, tuple(p), anim='tail', i=i, amp=amp, speed=0.05)
        dy = rise(t)
        q = p + V(0.0, dy, math.sqrt(max(0.1, L * L - dy * dy)))
        rseg(bone, p, q, w, w * 0.92, mat, up=up, bevel=w * 0.18, ext=w * 0.3)
        if extra:
            extra(bone, p, q, w, i)
        p = q
    return bone, p


def plane_rot(sx, U, Vb):
    """The rest rotation (x, y, z angles, applied z.y.x) that turns the wing's flat layout (u along x outward, v along z
    backward) into the plane through U and Vb, given for the left wing (x > 0) and mirrored for the right."""
    U = np.asarray(U, float); U = U / np.linalg.norm(U)
    Vb = np.asarray(Vb, float); Vb = Vb - (Vb @ U) * U; Vb = Vb / np.linalg.norm(Vb)
    R = np.stack([U, np.cross(Vb, U), Vb], 1)
    if sx < 0:
        F = np.diag([-1.0, 1.0, 1.0])
        R = F @ R @ F
    ry = -math.asin(max(-1.0, min(1.0, R[2, 0])))
    return (math.atan2(R[2, 1], R[2, 2]), ry, math.atan2(R[1, 0], R[0, 0]))


def membrane_wing(r, parent, sx, shoulder, rot, arm, tips, root_end, spar, claw, membrane, cap=None, ragged=False,
                  drips=None, arm_w=(4.4, 2.6)):
    """A bat wing laid out flat in the bone's xz plane (u outward, v backward) and raised by the rest rotation;
    rot is (x, y, z) angles for the left wing (mirrored for the right) or ('plane', U, V) for plane_rot."""
    rr = plane_rot(sx, rot[1], rot[2]) if rot[0] == 'plane' else (rot[0], rot[1] * sx, rot[2] * -sx)
    b = r.bone('wing_r' if sx < 0 else 'wing_l', parent, tuple(shoulder), rot=rr, anim='sway', ax=2, amp=0.2, speed=0.07)
    x0, y, z0 = shoulder
    P = lambda uv: (x0 + sx * uv[0], y, z0 + uv[1])
    S, E, W = P((0, 0)), P(arm[0]), P(arm[1])
    CI.chain_boxes(b, [S, E, W], arm_w[0], arm_w[1], spar)
    T = [P(t) for t in tips]
    for t in T:
        d = np.subtract(t, W)
        CI.chain_boxes(b, [W, t, tuple(np.add(t, d / np.linalg.norm(d) * 0.8))], 1.4, 0.5, spar)
    spike(b, W, (W[0] + sx * 1.5, y - 1.0, W[2] - 5.5), 1.8, claw)                 # the thumb claw
    if cap is not None:
        for p in [E, W]:
            CI.cbox(b, p, (arm_w[1] * 1.3, arm_w[1] * 1.3, arm_w[1] * 1.3), cap)
        for t in T:
            CI.cbox(b, tuple(np.add(W, np.subtract(t, W) * 0.55)), (1.9, 1.9, 1.9), cap)
    RE = P(root_end)
    outline = [(S[0], S[2]), (E[0], E[2]), (W[0], W[2])]
    veins = [(W[0], W[2], t[0], t[2]) for t in T] + [(E[0], E[2], RE[0], RE[2])]
    hang = []
    for i, t in enumerate(T):
        outline.append((t[0], t[2]))
        n = T[i + 1] if i + 1 < len(T) else RE
        mid = np.array([(t[0] + n[0]) / 2, (t[2] + n[2]) / 2])
        sc = mid * 0.7 + np.array([W[0], W[2]]) * 0.3                               # the scallop between two fingers
        if ragged:
            a = np.array([t[0], t[2]]) * 0.7 + sc * 0.3
            c = np.array([n[0], n[2]]) * 0.7 + sc * 0.3
            outline += [tuple(a), tuple((a + sc) / 2 + np.array([sx * 1.4, 1.6])), tuple(sc), tuple((c + sc) / 2 + np.array([-sx * 1.2, 1.8])), tuple(c)]
            hang += [a, (a + sc) / 2, (c + sc) / 2]
        else:
            outline.append(tuple(sc))
    outline.append((RE[0], RE[2]))
    xs, zs = [p[0] for p in outline], [p[1] for p in outline]
    # the painter sees the membrane where the rest rotation has put it: give it the wing's own plane as a frame
    # (origin at the shoulder, axes the bone's x and z), the outline and veins relative to the shoulder
    R = rot_zyx(*b.rot)
    frame = (np.asarray(shoulder, float), R @ V(1, 0, 0), R @ V(0, 0, 1))
    rel = [(px - x0, pz - z0) for px, pz in outline]
    rv = [(a - x0, c - z0, e - x0, g - z0) for a, c, e, g in veins]
    CI.box(b, (min(xs), y + 0.4, min(zs)), (max(xs), y + 0.4, max(zs)), dict(membrane, poly=rel, frame=frame, veins=rv))
    if drips:
        for k, h in enumerate(hang):
            L = 2.5 + (k * 7 % 5) * 0.8
            CI.cbox(b, (h[0], y + 0.4, h[1] + L / 2), (1.0, 0.8, L), drips[k % len(drips)])
    return b


def wedge_head(r, parent, A, k, skin, jaw_skin, brow, eye_m, tooth, mouth, W=12.0, L=26.0, Ht=8.0, tip_h=4.0, jaw_h=(5.0, 2.6),
               horns=None, horn2=None, frill=None, nose=None, visor_trim=None, crest=None, taper=0.48, ridge=None):
    """An Ice and Fire head (the user's photos): one wedge from the skull's back down to a blunt nose, in five slices
    that narrow and lower toward the front; a heavy brow plate overhanging a deep-set eye a third of the way along;
    wide cheek plates at the back with spines combed backward; a thick lower jaw the whole length, the upper teeth
    hanging over it even with the mouth shut; horns from the back of the skull swept back along the neck's line.
    A is the neck's end (the back-bottom of the skull); local units are scaled by k. The front is -z."""
    head = r.bone('head', parent, tuple(A), anim='head')
    H = lambda x, y, z: tuple(np.asarray(A, float) + V(x, y, z) * k)
    ym, zb = 1.0, 2.0                                        # the mouth line, the skull's back
    n = 7
    prof = []
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        tm = (t0 + t1) / 2
        w = W * (1.0 - taper * tm ** 0.9)
        h = Ht - (Ht - tip_h) * tm ** 1.15
        z0, z1 = zb - L * t0 + (0.8 if i else 0.0), zb - L * t1
        # bevelled along the head's length only: the slices step down to the nose without grooves between them
        rseg(head, H(0, ym - h / 2, z0), H(0, ym - h / 2, z1), w * k, h * k, skin, up=(0, -1, 0), bevel=min(1.4, w * 0.12) * k)
        prof.append((w, h, z0, z1))
    w_at = lambda t: W * (1.0 - taper * t ** 0.9)
    h_at = lambda t: Ht - (Ht - tip_h) * t ** 1.15
    # the bridge of the nose: one plate from the brow to the nose's tip, following the slope, over the steps
    tb0, tb1 = 0.3, 0.985
    p0, p1 = V(0, ym - h_at(tb0) - 0.4, zb - L * tb0), V(0, ym - h_at(tb1) - 0.4, zb - L * tb1)
    CI.seg(head, H(*p0), H(*p1), w_at(0.75) * 0.82 * k, 1.6 * k, ridge if ridge is not None else skin, up=(0, -1, 0), ext=0.6 * k)
    te = 0.27                                                # the eye a little over a quarter of the way along
    ze, we, he = zb - L * te, w_at(te), h_at(te)
    for sx in (-1, 1):
        # the brow: a thick plate over the eye, out past the cheek, lower at the front (the frown)
        bz0, bz1 = zb - L * 0.06, zb - L * 0.46
        CI.box(head, H(sx * (we / 2 - 2.6), ym - he - 0.8, bz1), H(sx * (we / 2 + 1.0), ym - he + 1.6, bz0), brow,
               rot=(0.16, sx * -0.05, 0), pivot=H(sx * we / 2, ym - he, bz0))
        if visor_trim is not None:
            CI.box(head, H(sx * (we / 2 + 0.8), ym - he - 0.2, bz1 + 0.3), H(sx * (we / 2 + 1.3), ym - he + 0.8, bz0 - 0.3), visor_trim,
                   rot=(0.16, sx * -0.05, 0), pivot=H(sx * we / 2, ym - he, bz0))
        CI.eye(head, H(sx * (we / 2 + 0.05), ym - he + 3.4, ze), 4.4 * k, 2.0 * k, 'left' if sx > 0 else 'right', eye_m)
        # the cheek plates, wide at the back
        CI.rbox(head, H(sx * (W / 2 - 0.6), ym - 4.6, zb - L * 0.24), H(sx * (W / 2 + 1.4), ym + 0.6, zb + 0.4), brow, bevel=0.5 * k)
        if frill is not None:
            for j in range(4):
                y0 = ym - 4.0 + j * 1.5
                spike(head, H(sx * (W / 2 + 0.8), y0, zb - 0.5), H(sx * (W / 2 + 2.6 + j * 0.3), y0 + 0.8 + j * 0.5, zb + 4.5 - j * 0.6),
                      1.3 * k, frill)
        # nostrils at the top of the blunt nose
        CI.box(head, H(sx * 1.4 - 0.5, ym - tip_h - 0.05, zb - L + 0.6), H(sx * 1.4 + 0.5, ym - tip_h + 0.6, zb - L + 1.8),
               M('simple', '#0c0a10'))
        # the upper teeth, hanging over the lower jaw
        CI.teeth(head, sx * (w_at(0.6) / 2 - 0.9), H(0, ym, 0)[1], H(0, 0, zb - L * 0.95)[2], H(0, 0, zb - L * 0.2)[2], 7, 0.75 * k,
                 tooth, down=True)
        if horns is not None:
            hw = W * 0.27
            CI.chain_boxes(head, [H(sx * hw, ym - Ht + 0.8, zb - 3.0), H(sx * (hw + 0.8), ym - Ht - 1.6, zb + 3.5),
                                  H(sx * (hw + 1.2), ym - Ht - 3.0, zb + 10.0), H(sx * (hw + 0.8), ym - Ht - 5.6, zb + 16.5)],
                           3.6 * k, 0.8 * k, horns)
        if horn2 is not None:
            CI.chain_boxes(head, [H(sx * (W / 2), ym - 5.6, zb - 1.0), H(sx * (W / 2 + 2.6), ym - 6.4, zb + 4.0),
                                  H(sx * (W / 2 + 3.6), ym - 8.0, zb + 8.5)], 2.2 * k, 0.5 * k, horn2)
    if nose is not None:                                     # small horns down the nose's ridge
        for j, t in enumerate((0.55, 0.7, 0.84)):
            y = ym - h_at(t) - 1.2
            spike(head, H(0, y + 0.3, zb - L * t), H(0, y - 1.6 + j * 0.3, zb - L * t + 1.2), 1.3 * k, nose)
    if crest is not None:
        crest(head, H, ym, zb, W, Ht)
    jaw = r.bone('jaw', head, H(0, ym, zb - 1.0), anim='jaw')
    for i in range(3):
        t0, t1 = i / 3, (i + 1) / 3
        tm = (t0 + t1) / 2
        w = w_at(tm * 0.92) - 1.6
        h = jaw_h[0] + (jaw_h[1] - jaw_h[0]) * tm
        z0, z1 = zb - 0.5 - (L - 1.0) * t0 + (0.5 if i else 0.0), zb - 0.5 - (L - 1.0) * t1
        CI.rbox(jaw, H(-w / 2, ym, z1), H(w / 2, ym + h, z0), skin, bevel=0.7 * k)
        CI.box(jaw, H(-w / 2 + 1.0, ym + h - 0.2, z1 + 0.6), H(w / 2 - 1.0, ym + h + 0.25, z0 - 0.4), jaw_skin)   # the pale underside
    CI.box(jaw, H(-w_at(0.5) / 2 + 1.6, ym - 0.05, zb - L + 1.5), H(w_at(0.5) / 2 - 1.6, ym, zb - 2.0), mouth)
    CI.teeth_x(jaw, H(0, 0, zb - L + 1.2)[2], H(0, ym, 0)[1], -2.0 * k + A[0], 2.0 * k + A[0], 3, 0.7 * k, tooth, down=False)
    return head, jaw


# ===================================================================================================== Demiurgos
@recipe
def demiurgos():
    r = CI.rig('demiurgos', td=1)
    gold = M('horn', '#d8b060', tip='#fff0b8')
    skin = M('scale', '#1c1a26', belly='#7a7690', scale_size=1.0, contrast=0.9)
    dark = M('scale', '#141220', belly='#141220', scale_size=1.0, contrast=0.7)
    belly = M('scale', '#8a86a0', belly='#a8a4bc', scale_size=1.4, contrast=0.5)
    crystals = [M('gem', c, glow=True) for c in ('#b48cff', '#6af0ff', '#ff8ad8', '#ffe46a', '#9a7cff')]
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, -9, 0), anim='breath')
    # Proportions from the user's Ice and Fire photo (the ice dragon, side on, stalking low) and sheet 22 (standing),
    # in shoulder heights (SH = 44 px here: the ground y = 24, the top of the shoulders y = -20): the body 1.35 SH from
    # chest to rump, the chest 0.52 SH deep with half the leg showing under it, the hips a little lower and slimmer; a
    # thick neck rising at 45 degrees, the head held forward, its top 1.35 SH up; the head 0.6 SH long; the upper legs
    # 0.22 to 0.27 SH thick.
    # ------------------------------------------------------------------ the body
    rseg(body, V(0, -8.5, -29), V(0, -8.5, -9), 22.0, 23.0, skin, bevel=4.6)             # the chest
    rseg(body, V(0, -9.5, -12), V(0, -9.5, 13), 19.0, 19.0, skin, bevel=3.8)             # the waist
    rseg(body, V(0, -9.5, 10), V(0, -9.5, 30), 18.5, 17.0, skin, bevel=3.6)              # the hips
    for sx in (-1, 1):
        rseg(body, (sx * 8.0, -19.0, -24), (sx * 8.5, -16.5, -11), 7.5, 7.0, skin, bevel=1.6)     # the wing roots
        rseg(body, (sx * 9.5, -12.0, -27), (sx * 11.0, -1.0, -16), 8.5, 10.0, skin, bevel=2.0)    # the shoulders
        rseg(body, (sx * 8.5, -15.0, 14), (sx * 10.5, 0.0, 27), 9.5, 14.0, skin, bevel=2.4)       # the haunches
    for k in range(12):                                                                 # belly plates, throat to groin
        z = -28.0 + k * 4.6
        yb = 2.5 - max(0.0, z + 8) * 0.075
        CI.box(body, (-7.0 + k * 0.2, yb, z), (7.0 - k * 0.2, yb + 1.0, z + 4.0), belly)
    # the chest jewel in a gold frame (sheet 22)
    CI.cbox(body, (0, -8.0, -29.6), (7.0, 7.0, 1.2), M('metal', '#d8b060'), rot=(0, 0, 0.785))
    CI.cbox(body, (0, -8.0, -30.1), (4.6, 4.6, 1.2), M('gem', '#c08cff', glow=True), rot=(0, 0, 0.785))
    # rainbow crystal studs set in the shoulders, flanks and thighs (sheet 22)
    for i, (x, y, z, sz) in enumerate(((11.6, -7.0, -22.0, 2.4), (11.4, -14.0, -15.0, 2.0), (9.8, -6.0, -3.0, 2.0), (9.6, -13.0, 7.0, 1.8),
                                       (11.0, -8.0, 18.0, 2.4), (10.6, -3.0, 24.0, 1.8), (8.2, -16.0, 20.0, 1.6))):
        for sx in (-1, 1):
            CI.cbox(body, (sx * x, y, z), (sz, sz * 1.5, sz), crystals[(i + (sx > 0)) % len(crystals)], rot=(0.3, 0.5 * sx, 0.4 * sx))
    # rainbow crystals down the back, small gold spikes between them
    for k in range(10):
        z = -24.0 + k * 5.6
        yt = -20.0 + max(0.0, z) * 0.06
        h = 6.5 - abs(k - 3.0) * 0.4
        spike(body, (0, yt + 1.2, z), (0, yt - h, z + h * 0.55), 2.2, crystals[k % len(crystals)])
        if k % 2 == 0:
            for sx in (-1, 1):
                spike(body, (sx * 5.0, yt + 2.0, z + 1.8), (sx * 6.6, yt - 2.4, z + 3.8), 1.4, gold)
    # ------------------------------------------------------------------ the neck: thick, rising at 45 degrees, the head held forward
    pts = [V(0, -14, -26), V(0, -20, -32), V(0, -25, -37.5), V(0, -28.5, -43.5)]
    widths = [15.0, 13.4, 12.0]
    bone = body
    for i in range(3):
        bone = r.bone(f'neck{i + 1}', bone, tuple(pts[i]), anim='sway', ax=1, amp=0.03, speed=0.05, phase=0.6 * i)
        p, q = pts[i], pts[i + 1]
        rseg(bone, p, q, widths[i], widths[i], skin, up=(0, 0, -1), bevel=widths[i] * 0.2, ext=widths[i] * 0.6)
        d = (q - p) / np.linalg.norm(q - p)
        fwd = np.array([0.0, d[2], -d[1]]) * -1.0                                       # toward the throat
        fwd = fwd / np.linalg.norm(fwd)
        CI.seg(bone, tuple(p + fwd * widths[i] * 0.47), tuple(q + fwd * widths[i] * 0.47), widths[i] * 0.72, 1.2, belly, up=tuple(fwd))
        back = -fwd
        m = (p + q) / 2 + back * widths[i] * 0.45
        spike(bone, m, m + back * (6.0 - i * 0.6) + d * -2.5, 2.0, crystals[(i + 3) % len(crystals)])
        spike(bone, m + d * 2.4, m + d * 2.4 + back * 3.4 + d * -1.5, 1.4, dark)
    # ------------------------------------------------------------------ the head: the Ice and Fire block, tall to the nose
    A = pts[-1] + V(0, 1.5, 2.0)
    Ht = 9.5
    wedge_head(r, bone, A, 1.0, skin, belly, dark, M('eye', '#c060ff', pupil='slit', mood='fierce', lid='#141220'),
               M('tooth', '#f0e8d4'), M('mouth', '#5a1420'), W=13.0, L=27.0, Ht=Ht, tip_h=5.6, jaw_h=(6.0, 3.8), horns=gold, horn2=gold,
               frill=dark, nose=gold, taper=0.4)
    head_top = A[1] + (1.0 - Ht)
    # ------------------------------------------------------------------ the legs: thick, a little under half showing
    for sx in (-1, 1):
        sd = 'r' if sx < 0 else 'l'
        leg3(r, body, 'leg_f' + sd, 'leg_r' if sx < 0 else 'leg_l',
             [V(sx * 10.5, -9.0, -20.0), V(sx * 12.0, 5.0, -14.5), V(sx * 12.0, 19.5, -20.0), V(sx * 12.0, 21.6, -21.0)],
             [9.6, 7.4, 5.8], skin, gold, toes=4, foot=(8.0, 3.0, 8.0), toe_len=3.0)
        leg3(r, body, 'leg_b' + sd, 'leg_l' if sx < 0 else 'leg_r',
             [V(sx * 10.0, -9.0, 21.0), V(sx * 12.0, 4.0, 13.0), V(sx * 12.0, 15.5, 26.5), V(sx * 12.0, 21.6, 23.5)],
             [12.0, 7.8, 5.8], skin, gold, toes=3, foot=(8.0, 3.0, 8.5), toe_len=3.4)
    # ------------------------------------------------------------------ the wings: huge, starry, raised over the back
    memb = M('wingskin', '#2a1e48', accent='#8a60ff', streaks='#c8a0ff', stars=0.012, edge='#d8b060')
    for sx in (-1, 1):
        # (sheet 22) the arm runs up to a high wrist, the fingers fan back and down from it, the membrane hangs
        # from them to the back like a curtain; the plane leans out to the side and back
        membrane_wing(r, body, sx, (sx * 8.0, -19.5, -17.0), ('plane', (0.5, -1.0, 0.1), (1.0, 0.45, 0.3)),
                      [(22.0, -6.0), (42.0, -3.0)], [(58.0, 12.0), (50.0, 30.0), (37.0, 44.0), (22.0, 50.0), (6.0, 46.0)],
                      (-13.0, 8.0), M('scale', '#1c1a26', belly='#1c1a26'), gold, memb, cap=gold, ragged=True,
                      arm_w=(5.0, 3.0))
    # ------------------------------------------------------------------ the tail: long and thick, gold spikes, a crystal fan
    def tail_extra(bone, p, q, w, i):
        m = (p + q) / 2
        if i < 13:
            spike(bone, m + (0, -w * 0.4, 0), m + (0, -w * 0.4 - max(1.6, w * 0.5), 1.8), max(0.9, w * 0.2),
                  crystals[i % len(crystals)] if i % 2 == 0 else gold)
        if i % 2 == 1 and i < 12:
            for sx in (-1, 1):
                spike(bone, m + (sx * w * 0.42, 0, 0), m + (sx * (w * 0.42 + max(1.5, w * 0.4)), -0.6, 1.6), max(0.7, w * 0.16), gold)
    last, tip = tail_chain(r, body, (0, -12.0, 28.0), 15, 76.0, 14.0, 2.0, skin,
                           lambda t: 0.8 - 1.4 * t, extra=tail_extra)
    for k, (dx, dy) in enumerate(((0, -1.0), (2.2, 0.6), (-2.2, 0.6))):
        spike(last, tip, tip + (dx, dy - 1.0, 6.5 - abs(dx) * 0.4), 1.6, crystals[k])
    r.height = 24.0 - head_top          # the renderer fits it to the hitbox: the head's top, not the wings' tips
    return r


# ===================================================================================================== Teia
@recipe
def teia():
    r = CI.rig('teia', td=1)
    plate = M('metal', '#e8ecf2', accent='#d8b060')
    frame = M('metal', '#4a505c')
    gold = M('metal', '#d8b060')
    light = M('energy', '#6ff6ff', glow=True)
    blades = [M('gem', c, glow=True) for c in ('#8ff4ff', '#c8b0ff', '#fff0a0', '#a8f0ff', '#e0b8ff')]
    claw = M('gem', '#7ff0ff', glow=True)
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, -10, 2), anim='breath')
    # Proportions measured on sheet 17, in shoulder heights (SH = 44 px: the ground y = 24, the shoulders' top y = -20):
    # the body 1.1 SH from chest to rump, the chest 0.45 SH deep with a little over half the leg showing under it, the
    # thighs 0.22 SH thick; the neck almost upright, the head 0.5 SH long with its top 1.7 SH up.
    # ------------------------------------------------------------------ the body: armour plates over a dark frame
    CI.seg(body, (0, -10.0, -24.0), (0, -10.5, 26.0), 9.0, 10.0, frame, up=(0, -1, 0))                # the dark frame
    rseg(body, V(0, -10.0, -25), V(0, -10.0, -6), 16.0, 20.0, plate, bevel=3.6)                       # the chest plate
    rseg(body, V(0, -11.0, -8), V(0, -11.0, 12), 12.5, 15.0, plate, bevel=2.8)                         # the waist plates
    rseg(body, V(0, -10.5, 9), V(0, -10.5, 27), 14.5, 16.0, plate, bevel=3.0)                          # the hips
    CI.box(body, (-7.4, -0.4, -23.0), (7.4, 0.4, -8.0), gold)                                          # gold at the chest's lower edge
    CI.box(body, (-6.6, -3.0, 11.0), (6.6, -2.2, 25.0), gold)                                          # and the hips'
    for sx in (-1, 1):                                                                      # the breastplate's gold V
        CI.seg(body, (sx * 6.6, -18.0, -25.2), (sx * 0.6, -6.0, -26.2), 1.4, 0.8, gold, up=(0, 0, -1))
    CI.cbox(body, (0, -9.0, -26.4), (3.4, 3.4, 1.0), light, rot=(0, 0, 0.785))
    for k in range(4):                                                                      # the waist's banded plates
        z = -6.0 + k * 4.4
        CI.box(body, (-5.6, -19.2, z), (5.6, -18.2, z + 3.4), gold)
    for sx in (-1, 1):
        rseg(body, (sx * 7.4, -17.5, -21.0), (sx * 8.6, -6.0, -10.0), 5.6, 8.0, plate, bevel=1.4)    # the shoulder plates
        CI.box(body, (sx * 8.4 + (0.0 if sx > 0 else -0.7), -16.0, -19.0), (sx * 8.4 + (0.7 if sx > 0 else 0.0), -8.0, -12.0), gold)
        CI.cbox(body, (sx * 9.2, -12.0, -15.5), (0.8, 2.6, 2.6), light)
        rseg(body, (sx * 6.6, -17.5, 13.0), (sx * 8.0, -4.0, 25.0), 6.0, 9.0, plate, bevel=1.6)      # the haunch plates
        CI.cbox(body, (sx * 8.6, -11.0, 19.0), (0.8, 2.6, 2.6), light)
        CI.box(body, (sx * 6.4 - 0.3, -6.0, -6.0), (sx * 6.4 + 0.3, -5.2, 10.0), light)              # the cyan seam
    for k in range(9):                                                                       # crystal fins down the back
        z = -18.0 + k * 5.0
        spike(body, (0, -19.5, z), (0, -25.5 + k * 0.4, z + 3.0), 1.8, blades[k % len(blades)])
    # ------------------------------------------------------------------ the neck: long and slim, reaching up and forward
    pts = [V(0, -17, -21), V(0, -25, -25), V(0, -33, -28.5), V(0, -40, -32), V(0, -45.5, -36)]
    widths = [10.0, 9.0, 8.2, 7.6]
    bone = body
    for i in range(4):
        bone = r.bone(f'neck{i + 1}', bone, tuple(pts[i]), anim='sway', ax=1, amp=0.03, speed=0.05, phase=0.6 * i)
        p, q = pts[i], pts[i + 1]
        CI.seg(bone, tuple(p), tuple(q), widths[i] * 0.7, widths[i] * 0.7, frame, up=(0, 0, -1), ext=widths[i] * 0.3)
        d = (q - p) / np.linalg.norm(q - p)
        rseg(bone, p, q, widths[i], widths[i], plate, up=(0, 0, -1), bevel=widths[i] * 0.22, ext=widths[i] * 0.35)
        fwd = np.array([0.0, d[2], -d[1]]) * -1.0
        fwd = fwd / np.linalg.norm(fwd)
        m = (p + q) / 2
        CI.seg(bone, tuple(p + d * 1.0 + fwd * widths[i] * 0.48), tuple(q - d * 1.0 + fwd * widths[i] * 0.48), widths[i] * 0.55, 0.8,
               frame, up=tuple(fwd))
        rseg(bone, q - d * 1.6, q - d * 0.9, widths[i] + 0.5, widths[i] + 0.5, gold, up=(0, 0, -1), bevel=widths[i] * 0.22)
        spike(bone, m - fwd * widths[i] * 0.45, m - fwd * (widths[i] * 0.45 + 4.0 - i * 0.4) - d * 2.0, 1.4, blades[i % len(blades)])
    for sx in (-1, 1):                                                                       # the crystal ruff at the neck's root
        for j in range(3):
            spike(body, (sx * 5.0, -17.0 + j * 2.2, -21.0), (sx * 9.5, -20.0 + j * 2.5, -16.5 + j * 1.2), 1.6, blades[j])
    # ------------------------------------------------------------------ the head: the same wedge, narrow and long, a gold visor

    def teia_crest(head, H, ym, zb, W, Ht):
        # light blades swept back from the skull in a fan (sheet 17), the longest in the middle
        for j, (dx, up, L) in enumerate(((0.0, 0.9, 15.0), (1.6, 0.7, 13.5), (-1.6, 0.7, 13.5), (3.0, 0.45, 12.0), (-3.0, 0.45, 12.0),
                                         (4.0, 0.2, 10.0), (-4.0, 0.2, 10.0))):
            base = V(dx * 0.6, ym - Ht + 0.6, zb - 2.5)
            tip = base + V(dx * 1.1, -up * L * 0.7, L * 0.8)
            spike(head, H(*base), H(*tip), 2.0, blades[j % len(blades)])

    wedge_head(r, bone, pts[-1] + V(0, 1.2, 1.5), 1.0, plate, frame, plate, M('eye', '#5ff0ff', pupil='ring', mood='calm', lid='#e8ecf2'),
               M('tooth', '#e8f4ff'), M('mouth', '#2a3a48'), W=9.0, L=23.0, Ht=7.6, tip_h=4.0, jaw_h=(4.2, 2.4), taper=0.36,
               visor_trim=gold, nose=None, crest=teia_crest)
    # ------------------------------------------------------------------ the legs: long and straight, armoured
    for sx in (-1, 1):
        sd = 'r' if sx < 0 else 'l'
        for front in (True, False):
            if front:
                pts = [V(sx * 7.6, -10.0, -15.0), V(sx * 8.4, 4.0, -11.5), V(sx * 8.2, 16.0, -14.5), V(sx * 8.2, 21.4, -15.5)]
                wd, name, anim = [7.6, 5.8, 4.6], 'leg_f' + sd, 'leg_r' if sx < 0 else 'leg_l'
            else:
                pts = [V(sx * 7.6, -10.0, 19.0), V(sx * 8.6, 2.0, 12.0), V(sx * 8.2, 14.0, 22.0), V(sx * 8.2, 21.4, 19.5)]
                wd, name, anim = [9.6, 6.0, 4.6], 'leg_b' + sd, 'leg_l' if sx < 0 else 'leg_r'
            up, low = leg3(r, body, name, anim, pts, wd, frame, claw, toes=3, foot=(5.6, 2.8, 5.8), toe_len=2.0, dew=False)
            # white armour shells over the dark limb, gold at their edges, cyan light at the joint
            d0 = (pts[1] - pts[0]) / np.linalg.norm(pts[1] - pts[0])
            rseg(up, pts[0] + d0 * 0.5, pts[1] - d0 * 1.6, wd[0] + 1.6, wd[0] * 1.15 + 1.6, plate, up=(0, 0, -1), bevel=1.4)
            rseg(up, pts[1] - d0 * 2.2, pts[1] - d0 * 1.4, wd[0] + 2.0, wd[0] * 1.15 + 2.0, gold, up=(0, 0, -1), bevel=0.8)
            d1 = (pts[2] - pts[1]) / np.linalg.norm(pts[2] - pts[1])
            rseg(low, pts[1] + d1 * 1.6, pts[2] - d1 * 1.2, wd[1] + 1.4, wd[1] + 1.4, plate, up=(0, 0, -1), bevel=1.0)
            rseg(low, pts[1] + d1 * 1.2, pts[1] + d1 * 2.0, wd[1] + 1.8, wd[1] + 1.8, gold, up=(0, 0, -1), bevel=0.6)
            CI.cbox(low, tuple(pts[1] + V(sx * (wd[1] * 0.5 + 0.6), 0, 0)), (0.8, 2.0, 2.0), light)
            CI.cbox(low, tuple(pts[2] + V(sx * (wd[2] * 0.5 + 0.5), 0, 0)), (0.8, 1.6, 1.6), light)
            CI.rbox(low, tuple(pts[3] + V(-3.2, -2.6, -3.8)), tuple(pts[3] + V(3.2, 0.6, 1.8)), plate, bevel=0.8)   # the armoured foot
            CI.box(low, tuple(pts[3] + V(-3.3, -2.0, -3.9)), tuple(pts[3] + V(3.3, -1.4, 1.9)), gold)
    # ------------------------------------------------------------------ the wings: armoured arms fanned with light blades
    def blade(bone, p, d, L, w, cols):
        """A feather of light: wide in the middle, pointed at the tip, its colour shading along it (sheet 17)."""
        a, m, t = p, p + d * L * 0.45, p + d * L * 0.85
        CI.seg(bone, tuple(a), tuple(m), w * 0.8, 0.6, cols[0], up=(0, -1, 0), ext=0.4)
        CI.seg(bone, tuple(m), tuple(t), w, 0.6, cols[1], up=(0, -1, 0), ext=0.4)
        CI.seg(bone, tuple(t), tuple(p + d * L), w * 0.5, 0.6, cols[2], up=(0, -1, 0), ext=0.4)

    for sx in (-1, 1):
        x0, y, z0 = sx * 6.5, -19.5, -14.0
        b = r.bone('wing_r' if sx < 0 else 'wing_l', body, (x0, y, z0), rot=plane_rot(sx, (0.6, -1.0, 0.1), (1.0, 0.2, 0.35)),
                   anim='sway', ax=2, amp=0.2, speed=0.07)
        P = lambda u, v: V(x0 + sx * u, y, z0 + v)
        S, E, W, T = P(0, 0), P(16, -3), P(30, 1), P(38, 3)
        rseg(b, S, E, 5.0, 4.4, plate, up=(0, -1, 0), bevel=1.0, ext=2.0)
        rseg(b, E, W, 4.0, 3.6, plate, up=(0, -1, 0), bevel=0.8, ext=1.6)
        rseg(b, W, T, 3.2, 3.0, plate, up=(0, -1, 0), bevel=0.6, ext=1.2)
        CI.cbox(b, tuple(E), (4.0, 4.0, 4.0), gold)
        CI.cbox(b, tuple(E + V(0, -2.1, 0)), (1.8, 0.6, 1.8), light)
        # the hand: a broad armour plate, gold at its edge, a cyan stone in it
        CI.rbox(b, tuple(W + V(-4.0, -1.2, -3.0)), tuple(W + V(4.0, 1.2, 6.0)), plate, bevel=0.6)
        CI.box(b, tuple(W + V(-4.3, -0.6, -3.3)), tuple(W + V(4.3, 0.6, 6.3)), gold)
        CI.cbox(b, tuple(W + V(0, -1.5, 1.5)), (2.6, 0.8, 2.6), light, rot=(0, 0.785, 0))
        # the blades: the longest from the hand pointing out past it, shorter ones fanned back toward the body
        cyc = [blades[0], blades[1], blades[2]]
        for k, (t, ang, L, w) in enumerate(((1.0, -0.12, 38.0, 4.6), (0.9, 0.18, 37.0, 4.6), (0.75, 0.48, 35.0, 4.4),
                                            (0.6, 0.78, 32.0, 4.2), (0.45, 1.05, 29.0, 4.0), (0.3, 1.3, 25.0, 3.8),
                                            (0.18, 1.48, 21.0, 3.6), (0.08, 1.62, 16.0, 3.4))):
            p = E + (T - E) * t if t > 0.2 else S + (E - S) * (t / 0.2)
            d = V(sx * math.cos(ang), 0.0, math.sin(ang))
            blade(b, p + V(0, 0.2, 0), d, L, w, [cyc[(k + j) % 3] for j in range(3)])
    # ------------------------------------------------------------------ the tail: slim, armoured links, a fan of blades
    def tail_extra(bone, p, q, w, i):
        m = (p + q) / 2
        CI.box(bone, tuple(m + (-w * 0.32, -w * 0.5 - 0.3, -1.0)), tuple(m + (w * 0.32, -w * 0.5 + 0.2, 1.0)), gold)
        if i % 3 == 1:
            spike(bone, m + (0, -w * 0.45, 0), m + (0, -w * 0.45 - 3.0, 2.0), 1.2, blades[i % len(blades)])
    last, tip = tail_chain(r, body, (0, -13.0, 26.0), 14, 70.0, 10.0, 2.4, plate,
                           lambda t: 0.6 - 2.0 * t, extra=tail_extra)
    for k in range(5):
        a = -0.9 + k * 0.45
        spike(last, tip, tip + (math.sin(a) * 9.0, -2.0 - math.cos(a) * 3.0, 7.0 + math.cos(a) * 4.0), 2.0, blades[k])
    r.height = 75.0
    return r

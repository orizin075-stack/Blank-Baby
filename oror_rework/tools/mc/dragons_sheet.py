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


def scale_relief(bone, p0, p1, w, dep, mats, up, step=2.2, top=True, sides=True, bevel=2.0, seed=0):
    """Scales standing out of a bevelled segment from p0 to p1 (w across x, dep along up): rows of small plates in a
    brick pattern on both flanks and along the top, alternating two shades (sheet 22's rough scaled hide)."""
    p0, p1, n = np.asarray(p0, float), np.asarray(p1, float), np.asarray(up, float)
    L = float(np.linalg.norm(p1 - p0))
    d = (p1 - p0) / L
    n = n - (n @ d) * d
    n = n / np.linalg.norm(n)
    rows = max(1, int(L / step))
    k = seed
    for i in range(rows):
        s = (i + 0.5) * L / rows
        q = p0 + d * s
        if sides:
            levels = max(1, int((dep - 2 * bevel) / 2.4))
            for j in range(levels):
                v = -(dep / 2 - bevel) + (j + 0.5 + (0.5 if i % 2 else 0.0)) * (dep - 2 * bevel) / (levels + 0.5)
                for sx in (-1, 1):
                    c = q + n * v + V(sx * (w / 2 + 0.15), 0, 0)
                    CI.seg(bone, tuple(c - d * 0.95), tuple(c + d * 0.95), 0.7, 1.7, mats[k % len(mats)], up=tuple(n))
                    k += 1
        if top:
            for j, xo in enumerate((-w * 0.28, 0.0, w * 0.28) if i % 2 else (-w * 0.14, w * 0.14)):
                c = q + n * (dep / 2 + 0.15) + V(xo, 0, 0)
                CI.seg(bone, tuple(c - d * 0.95), tuple(c + d * 0.95), 1.9, 0.7, mats[k % len(mats)], up=tuple(n))
                k += 1


def shingles(bone, p0, p1, w, dep, mat, trim, up, rows=3, sides=True, top=True):
    """Armour plates laid like scales over a segment (sheet 17): each row a little proud of the last and tipped out,
    a gold edge along each plate's lower rim."""
    p0, p1, n = np.asarray(p0, float), np.asarray(p1, float), np.asarray(up, float)
    L = float(np.linalg.norm(p1 - p0))
    d = (p1 - p0) / L
    n = n - (n @ d) * d
    n = n / np.linalg.norm(n)
    for i in range(rows):
        a = p0 + d * (L * i / rows)
        b = p0 + d * (L * (i + 1) / rows + 0.8)
        lift = 0.35 + 0.25 * i
        if top:
            CI.seg(bone, tuple(a + n * (dep / 2 + lift)), tuple(b + n * (dep / 2 + lift)), w * 0.8, 0.9, mat, up=tuple(n))
            CI.seg(bone, tuple(b + n * (dep / 2 + lift) - d * 0.5), tuple(b + n * (dep / 2 + lift)), w * 0.8, 1.0, trim, up=tuple(n))
        if sides:
            for sx in (-1, 1):
                c0 = a + V(sx * (w / 2 + lift), 0, 0) + n * dep * 0.12
                c1 = b + V(sx * (w / 2 + lift), 0, 0) + n * dep * 0.12
                CI.seg(bone, tuple(c0), tuple(c1), 0.9, dep * 0.62, mat, up=tuple(n))
                CI.seg(bone, tuple(c1 - d * 0.5), tuple(c1), 1.0, dep * 0.62, trim, up=tuple(n))


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
    CI.seg(head, H(*p0), H(*p1), w_at(0.75) * 0.6 * k, 1.4 * k, ridge if ridge is not None else skin, up=(0, -1, 0), ext=0.6 * k)
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
    body = r.bone('body', root, (0, -10, -2), anim='breath')
    # Measured on sheet 22 (in head lengths, HL = 27 px here): the body slopes down from high shoulders to low hips
    # (the user: "直線じゃなくて＼な体つき"), about 2 HL along its line, tipped 22 degrees; the chest a little under 1 HL
    # deep and wide; long forelegs from high shoulders, the hind legs folded under low hips; the neck rising from the
    # top of the chest almost upright, the head held forward and a little down; the tail sweeping down to the ground.
    ang = math.radians(22.0)
    ax = V(0, math.sin(ang), math.cos(ang))                     # along the body, down and back
    up = V(0, -math.cos(ang), math.sin(ang))                    # across it, toward the back
    C0 = V(0, -16.0, -30.0)                                     # the front of the chest, on the body's line
    P = lambda t, v=0.0: C0 + ax * t + up * v
    segs = [(0.0, 21.0, 23.0, 26.0, 5.0), (18.0, 38.0, 19.5, 21.0, 4.0), (35.0, 54.0, 18.5, 18.0, 3.6)]
    for t0, t1, w, dep, bv in segs:                             # the chest, the waist, the hips
        rseg(body, P(t0), P(t1), w, dep, skin, up=tuple(up), bevel=bv)
        scale_relief(body, P(t0 + 1.0), P(t1 - 1.0), w, dep, [skin, dark], tuple(up), bevel=bv, seed=int(t0))
    for sx in (-1, 1):
        rseg(body, P(3.0, 11.0) + V(sx * 8.5, 0, 0), P(15.0, 11.0) + V(sx * 8.5, 0, 0), 7.5, 7.0, skin, up=tuple(up), bevel=1.6)  # the wing roots
        rseg(body, P(2.0, 2.0) + V(sx * 10.0, 0, 0), P(13.0, -6.0) + V(sx * 11.0, 0, 0), 9.0, 10.0, skin, up=tuple(up), bevel=2.0)  # the shoulders
        rseg(body, P(40.0, 3.0) + V(sx * 9.0, 0, 0), P(52.0, -4.0) + V(sx * 10.0, 0, 0), 10.0, 14.0, skin, up=tuple(up), bevel=2.4)  # the haunches
    for k in range(12):                                         # belly plates, throat to groin, along the slope
        t = 1.0 + k * 4.4
        dep = 26.0 if t < 19 else (21.0 if t < 37 else 18.0)
        wd = 14.0 - k * 0.45
        c = P(t + 2.0, -dep / 2 - 0.3)
        CI.seg(body, tuple(c - ax * 2.0), tuple(c + ax * 2.0), wd, 1.0, belly, up=tuple(up))
    # the chest jewel in a gold frame (sheet 22), set in the front of the chest
    jc = P(-0.3, 1.0)
    CI.cbox(body, tuple(jc + V(0, 0, -0.4)), (7.0, 7.0, 1.2), M('metal', '#d8b060'), rot=(-ang, 0, 0.785))
    CI.cbox(body, tuple(jc + V(0, 0, -0.9)), (4.6, 4.6, 1.2), M('gem', '#c08cff', glow=True), rot=(-ang, 0, 0.785))
    # rainbow crystal studs set in the shoulders, flanks and thighs (sheet 22)
    for i, (t, v, x, sz) in enumerate(((6.0, -4.0, 11.6, 2.4), (12.0, 6.0, 11.4, 2.0), (22.0, -2.0, 10.0, 2.0), (28.0, 5.0, 9.8, 1.8),
                                       (42.0, -2.0, 10.4, 2.4), (48.0, -6.0, 10.2, 1.8), (45.0, 7.0, 9.0, 1.6))):
        for sx in (-1, 1):
            CI.cbox(body, tuple(P(t, v) + V(sx * x, 0, 0)), (sz, sz * 1.5, sz), crystals[(i + (sx > 0)) % len(crystals)],
                    rot=(0.3, 0.5 * sx, 0.4 * sx))
    # rainbow crystals down the back, small gold spikes between them
    for k in range(10):
        t = 3.0 + k * 5.2
        dep = 26.0 if t < 19 else (21.0 if t < 37 else 18.0)
        base = P(t, dep / 2 - 0.5)
        h = 7.0 - abs(k - 2.5) * 0.45
        spike(body, base, base + up * h + ax * (h * 0.5), 2.2, crystals[k % len(crystals)])
        if k % 2 == 0:
            for sx in (-1, 1):
                b0 = P(t + 1.5, dep / 2 - 1.5) + V(sx * 5.2, 0, 0)
                spike(body, b0, b0 + up * 3.6 + ax * 1.6 + V(sx * 1.6, 0, 0), 1.4, gold)
    # ------------------------------------------------------------------ the neck: thick, rising from the top of the chest
    base = P(4.0, 6.0)
    pts = [base, base + V(0, -7.5, -4.5), base + V(0, -14.0, -9.5), base + V(0, -19.0, -15.5)]   # up, then forward
    widths = [15.5, 13.8, 12.2]
    bone = body
    for i in range(3):
        bone = r.bone(f'neck{i + 1}', bone, tuple(pts[i]), anim='sway', ax=1, amp=0.03, speed=0.05, phase=0.6 * i)
        p, q = pts[i], pts[i + 1]
        dn = (q - p) / np.linalg.norm(q - p)
        fwd = np.array([0.0, dn[2], -dn[1]]) * -1.0                                     # toward the throat
        fwd = fwd / np.linalg.norm(fwd)
        rseg(bone, p, q, widths[i], widths[i], skin, up=tuple(-fwd), bevel=widths[i] * 0.2, ext=widths[i] * 0.6)
        scale_relief(bone, p + dn * 0.5, q - dn * 0.5, widths[i], widths[i], [skin, dark], tuple(-fwd), step=2.0, top=False,
                     bevel=widths[i] * 0.2, seed=i)
        CI.seg(bone, tuple(p + fwd * widths[i] * 0.47), tuple(q + fwd * widths[i] * 0.47), widths[i] * 0.72, 1.2, belly, up=tuple(fwd))
        back = -fwd
        m = (p + q) / 2 + back * widths[i] * 0.45
        spike(bone, m, m + back * (6.0 - i * 0.6) + dn * 1.5, 2.0, crystals[(i + 3) % len(crystals)])
        spike(bone, m + dn * 2.4, m + dn * 2.4 + back * 3.4 + dn * 1.0, 1.4, dark)
    # ------------------------------------------------------------------ the head: the Ice and Fire block, held forward
    A = pts[-1] + V(0, 1.5, 1.0)
    Ht = 8.6
    head, _ = wedge_head(r, bone, A, 1.0, skin, belly, dark, M('eye', '#c060ff', pupil='slit', mood='fierce', lid='#141220'),
                         M('tooth', '#f0e8d4'), M('mouth', '#5a1420'), W=10.0, L=27.0, Ht=Ht, tip_h=4.6, jaw_h=(5.0, 3.2), horns=gold,
                         horn2=gold, frill=dark, nose=gold, taper=0.4, ridge=dark)
    head_top = A[1] + (1.0 - Ht)
    # ------------------------------------------------------------------ the legs: long forelegs, the hind legs folded under
    for sx in (-1, 1):
        sd = 'r' if sx < 0 else 'l'
        sh = P(8.0, -3.0) + V(sx * 10.5, 0, 0)
        leg3(r, body, 'leg_f' + sd, 'leg_r' if sx < 0 else 'leg_l',
             [sh, V(sx * 12.0, sh[1] + 15.0, sh[2] + 5.0), V(sx * 12.0, 19.5, sh[2] - 1.0), V(sx * 12.0, 21.6, sh[2] - 2.0)],
             [10.0, 7.6, 6.0], skin, gold, toes=4, foot=(8.4, 3.0, 8.4), toe_len=3.2)
        hp = P(46.0, -2.0) + V(sx * 10.0, 0, 0)
        leg3(r, body, 'leg_b' + sd, 'leg_l' if sx < 0 else 'leg_r',
             [hp, V(sx * 12.5, hp[1] + 7.0, hp[2] - 9.0), V(sx * 12.5, 16.5, hp[2] + 4.0), V(sx * 12.5, 21.6, hp[2] + 1.0)],
             [12.5, 8.2, 6.0], skin, gold, toes=3, foot=(8.4, 3.0, 9.0), toe_len=3.6)
    # ------------------------------------------------------------------ the wings: huge, starry, raised over the back
    memb = M('wingskin', '#2a1e48', accent='#8a60ff', streaks='#c8a0ff', stars=0.012, edge='#d8b060')
    for sx in (-1, 1):
        # (sheet 22) the arm runs up to a high wrist, the fingers fan back and down from it, the membrane hangs
        # from them to the back like a curtain; the plane leans out to the side and back
        membrane_wing(r, body, sx, tuple(P(9.0, 13.0) + V(sx * 8.0, 0, 0)), ('plane', (0.5, -1.0, 0.1), (1.0, 0.45, 0.3)),
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
    # the tail sweeps on down the body's line, then runs low over the ground
    last, tip = tail_chain(r, body, tuple(P(52.0, 0.0)), 15, 78.0, 14.0, 2.0, skin,
                           lambda t: 2.4 * (1.0 - t / 0.35) if t < 0.35 else -0.25, extra=tail_extra)
    for k, (dx, dy) in enumerate(((0, -1.0), (2.2, 0.6), (-2.2, 0.6))):
        spike(last, tip, tip + (dx, dy - 1.0, 6.5 - abs(dx) * 0.4), 1.6, crystals[k])
    r.height = 24.0 - head_top          # the renderer fits it to the hitbox: the head's top, not the wings' tips
    return r


# ===================================================================================================== Teia
@recipe
def teia():
    r = CI.rig('teia', td=1)
    plate = M('scale', '#f2f4f8', belly='#e0e4ec', scale_size=1.3, contrast=0.45)     # white scales ("鱗")
    shell = M('metal', '#f0f2f6', accent='#d8b060')                                  # the armour plates laid over them
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
    # armour plates laid like scales over the chest, the waist and the hips (sheet 17)
    shingles(body, V(0, -10.0, -25), V(0, -10.0, -7), 16.0, 20.0, shell, gold, (0, -1, 0), rows=4)
    shingles(body, V(0, -11.0, -7), V(0, -11.0, 10), 12.5, 15.0, shell, gold, (0, -1, 0), rows=4)
    shingles(body, V(0, -10.5, 10), V(0, -10.5, 26), 14.5, 16.0, shell, gold, (0, -1, 0), rows=3)
    for k in range(9):                                                                       # crystal fins down the back
        z = -18.0 + k * 5.0
        spike(body, (0, -19.5, z), (0, -25.5 + k * 0.4, z + 3.0), 1.8, blades[k % len(blades)])
    # ------------------------------------------------------------------ the neck: as long as the head (sheet 17), upright
    pts = [V(0, -17, -21), V(0, -24.5, -24), V(0, -31, -27), V(0, -36, -30.5)]
    widths = [11.0, 10.0, 9.2]
    bone = body
    for i in range(3):
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
        shingles(bone, p, q, widths[i], widths[i], shell, gold, tuple(-fwd), rows=2)
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
               M('tooth', '#e8f4ff'), M('mouth', '#2a3a48'), W=7.2, L=23.0, Ht=6.6, tip_h=3.4, jaw_h=(3.6, 2.0), taper=0.36,
               visor_trim=gold, nose=None, crest=teia_crest)
    # ------------------------------------------------------------------ the legs: long and straight, armoured
    for sx in (-1, 1):
        sd = 'r' if sx < 0 else 'l'
        for front in (True, False):
            if front:
                pts = [V(sx * 8.0, -10.0, -17.0), V(sx * 8.8, 3.0, -13.5), V(sx * 8.6, 16.0, -16.5), V(sx * 8.6, 21.4, -17.5)]
                wd, name, anim = [8.4, 6.6, 5.2], 'leg_f' + sd, 'leg_r' if sx < 0 else 'leg_l'
            else:
                pts = [V(sx * 8.0, -10.0, 17.0), V(sx * 9.0, 2.0, 10.0), V(sx * 8.6, 14.0, 20.0), V(sx * 8.6, 21.4, 17.5)]
                wd, name, anim = [11.0, 7.2, 5.2], 'leg_b' + sd, 'leg_l' if sx < 0 else 'leg_r'
            up, low = leg3(r, body, name, anim, pts, wd, frame, claw, toes=3, foot=(5.6, 2.8, 5.8), toe_len=2.0, dew=False)
            # white armour shells over the dark limb, gold at their edges, cyan light at the joint
            d0 = (pts[1] - pts[0]) / np.linalg.norm(pts[1] - pts[0])
            rseg(up, pts[0] + d0 * 0.5, pts[1] - d0 * 1.6, wd[0] + 1.6, wd[0] * 1.15 + 1.6, shell, up=(0, 0, -1), bevel=1.4)
            rseg(up, pts[1] - d0 * 2.2, pts[1] - d0 * 1.4, wd[0] + 2.0, wd[0] * 1.15 + 2.0, gold, up=(0, 0, -1), bevel=0.8)
            d1 = (pts[2] - pts[1]) / np.linalg.norm(pts[2] - pts[1])
            rseg(low, pts[1] + d1 * 1.6, pts[2] - d1 * 1.2, wd[1] + 1.4, wd[1] + 1.4, shell, up=(0, 0, -1), bevel=1.0)
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
        x0, y, z0 = sx * 7.0, -19.5, -16.0
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


# ===================================================================================================== Kurma
@recipe
def kurma():
    """嶺脈地龍 クールマ (sheet 16): a turtle-dragon carrying a mountain. Measured in rim heights (RH = 28 px here: the
    ground y = 24, the shell's rim y = -4): the shell 2.1 RH long and 1.6 wide, its peaks 1.0 RH over the rim; a long low
    body on four pillar legs 0.45 RH thick, splayed a little, with 0.35 RH of leg under the pale plastron; a big head
    0.75 RH long held up at the rim's height on a thick neck with a pale throat; a thick plated tail 1.2 RH long. Grey
    stone gone green with moss, moss hanging from everything, green light in its seams; on the shell, terraces of earth
    and grass, jagged grey peaks with snow, a forest of spruces, a lake and two waterfalls running over the rim."""
    import random
    rnd = random.Random(16)
    r = CI.rig('kurma', td=1)
    stone = M('rock', '#8a877e')
    rim = M('rock', '#a8a59c')
    dark = M('rock', '#585c52')
    hide = M('scale', '#5f6a55', belly='#cdbf9e', scale_size=1.8, contrast=0.7)
    plastron = M('scale', '#d2c4a2', belly='#d8cba8', scale_size=2.2, contrast=0.4)
    moss = M('leaf', '#5a8a34')
    moss2 = M('leaf', '#476f2a')
    grass = M('leaf', '#5f9a3a')
    earth = M('rock', '#7a5a3c')
    snow = M('simple', '#eef2f4')
    claw = M('rock', '#d8d2c0')
    vein = M('energy', '#5effc0', glow=True)
    water = M('simple', '#4f94e0')
    foam = M('simple', '#cfe6ff')
    spruce = M('leaf', '#2c5a2e')
    spruce2 = M('leaf', '#356a34')
    trunk = M('wood', '#5a3e24')
    root = r.bone('root', None, (0, 24, 0), anim='root')
    body = r.bone('body', root, (0, 4, 6), anim='breath')

    def moss_on(bone, x0, x1, y0, y1, z0, z1, n, side):
        """Moss patches and hanging strands on a face (side: the axis and sign it faces)."""
        for _ in range(n):
            x, y, z = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(z0, z1)
            ax_, sg = side
            c = [x, y, z]
            c[ax_] = (x1 if sg > 0 else x0) if ax_ == 0 else ((y1 if sg > 0 else y0) if ax_ == 1 else (z1 if sg > 0 else z0))
            size = [rnd.uniform(1.5, 3.5), rnd.uniform(1.0, 2.5), rnd.uniform(1.5, 3.5)]
            size[ax_] = 0.5
            size[1] += rnd.choice((0.0, 0.0, 3.0, 5.0))          # some hang down
            CI.cbox(bone, (c[0], c[1] + size[1] / 2 - 1.0, c[2]), tuple(size), moss if rnd.random() < 0.5 else moss2)
    # ------------------------------------------------------------------ the body under the shell, the plastron
    CI.rbox(body, (-18.5, -4.0, -26.0), (18.5, 13.0, 30.0), hide, bevel=4.5)
    CI.rbox(body, (-15.0, 10.0, -24.0), (15.0, 14.2, 27.0), plastron, bevel=2.2)
    for sx in (-1, 1):
        moss_on(body, -18.5, 18.5, -3.0, 10.0, -24.0, 28.0, 26, (0, sx))
        for (y0, z0, z1) in ((2.0, -20.0, -4.0), (6.0, 2.0, 22.0), (0.0, 10.0, 16.0)):        # green light in the seams
            CI.box(body, (sx * 18.55 - (0.15 if sx < 0 else 0), y0, z0), (sx * 18.55 + (0.15 if sx > 0 else 0), y0 + 0.6, z1), vein)
    # ------------------------------------------------------------------ the shell: a rim of great stone blocks
    n = 26
    RX, RZ, CZ = 26.0, 33.0, 3.0
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p0 = V(math.sin(a0) * RX, -4.0, CZ + math.cos(a0) * RZ)
        p1 = V(math.sin(a1) * RX, -4.0, CZ + math.cos(a1) * RZ)
        rseg(body, p0, p1, 7.5, 7.0, rim if k % 2 else stone, up=(0, -1, 0), bevel=1.4, ext=1.8)
        m = (p0 + p1) / 2
        out = V(math.sin((a0 + a1) / 2), 0, math.cos((a0 + a1) / 2))
        for j in range(3):                                                                   # moss hanging off the rim
            q = m + out * 3.9 + V((j - 1) * 2.0 * out[2], 2.4, -(j - 1) * 2.0 * out[0])
            L = rnd.choice((2.0, 4.0, 6.0, 9.0))
            CI.box(body, tuple(q + V(-0.45, 0, -0.45)), tuple(q + V(0.45, L, 0.45)), moss if j % 2 else moss2)
    # the shell's top: earth and grass in terraces inside the rim, stepping up toward the peaks
    for (hx, hz, h) in ((23.5, 30.0, 1.5), (20.0, 26.0, 4.0), (16.0, 21.0, 6.5), (11.0, 15.0, 9.0)):
        CI.rbox(body, (-hx, -4.0 - h, CZ - hz), (hx, -4.0 - h + 2.6, CZ + hz), earth, bevel=3.4)
        CI.rbox(body, (-hx + 0.7, -4.7 - h, CZ - hz + 0.7), (hx - 0.7, -4.0 - h, CZ + hz - 0.7), grass, bevel=3.4)
    # the peaks: jagged grey stone stepping up to snow (the highest toward the front, as on the sheet)
    for (x, z, w, h) in ((-1.0, -3.0, 13.0, 29.0), (9.0, 12.0, 8.5, 21.0), (-10.0, 14.0, 7.0, 15.0), (10.0, -12.0, 6.0, 12.0),
                         (-12.0, -10.0, 5.0, 9.0)):
        base = -12.5
        steps = 8
        for st in range(steps):
            t0, t1 = st / steps, (st + 1) / steps
            hw = w * (1.0 - t0 * 0.85)
            for jx, jz in ((0.0, 0.0), (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3))):
                ox, oz = jx * hw, jz * hw
                CI.box(body, (x + ox - hw * rnd.uniform(0.7, 1.0), base - h * t1, z + oz - hw * rnd.uniform(0.6, 0.9)),
                       (x + ox + hw * rnd.uniform(0.7, 1.0), base - h * t0, z + oz + hw * rnd.uniform(0.6, 0.9)), stone if (st + int(jx * 10)) % 2 else rim)
            if st >= steps - 3:
                CI.box(body, (x - hw * 0.75, base - h * t1 - 0.5, z - hw * 0.65), (x + hw * 0.75, base - h * t1, z + hw * 0.65), snow)
        CI.box(body, (x - w * 0.1, base - h - 1.8, z - w * 0.1), (x + w * 0.1, base - h, z + w * 0.1), snow)
    # a forest of spruces on the terraces
    tiers = ((22.0, 28.0, -5.5), (18.0, 24.0, -8.0), (14.0, 19.0, -10.5), (9.5, 13.0, -13.0))
    for (hx, hz, y) in tiers:
        for k in range(14):
            a = 2 * math.pi * k / 14 + rnd.uniform(-0.1, 0.1)
            x, z = math.sin(a) * (hx - 2.0), CZ + math.cos(a) * (hz - 2.0)
            hh = rnd.uniform(0.8, 1.3)
            CI.box(body, (x - 0.5, y - 2.0 * hh, z - 0.5), (x + 0.5, y, z + 0.5), trunk)
            for j, (rad, th) in enumerate(((2.0, 1.8), (1.5, 1.6), (0.8, 1.6))):
                yb = y - 2.0 * hh - j * 1.6 * hh
                CI.box(body, (x - rad, yb - th * hh, z - rad), (x + rad, yb, z + rad), spruce if (k + j) % 2 else spruce2)
    # a lake on a terrace and two waterfalls running down over the rim
    CI.box(body, (3.0, -10.65, 4.0), (12.0, -10.4, 12.0), water)
    for (z, L) in ((8.0, 22.0), (20.0, 17.0)):
        x = math.sqrt(max(1.0, 1 - ((z - CZ) / RZ) ** 2)) * RX
        CI.box(body, (6.0, -10.7, z - 1.6), (x + 0.4, -10.4, z + 1.6), water)                      # the stream to the edge
        CI.box(body, (x + 3.9, -10.4, z - 1.6), (x + 4.5, -10.4 + L, z + 1.6), water)              # the fall
        CI.box(body, (x + 0.4, -10.7, z - 1.6), (x + 4.5, -10.4, z + 1.6), water)
        CI.box(body, (x + 3.6, -10.4 + L - 1.5, z - 2.2), (x + 5.2, -10.4 + L, z + 2.2), foam)
    # ------------------------------------------------------------------ the neck and the head: big, held up, a pale throat
    neck = r.bone('neck', body, (0, 0.0, -25.0), anim='sway', ax=1, amp=0.03, speed=0.04)
    rseg(neck, V(0, 2.0, -22.0), V(0, -5.0, -36.0), 17.0, 16.0, hide, up=(0, -1, 0), bevel=3.6, ext=2.5)
    CI.seg(neck, (0, 9.5, -23.0), (0, 2.5, -37.0), 12.0, 1.4, plastron, up=(0, 1, 0))
    moss_on(neck, -8.5, 8.5, -6.0, 6.0, -36.0, -24.0, 10, (0, -1))
    head = r.bone('head', neck, (0, -5.0, -36.0), anim='head')
    A = V(0, -5.0, -36.0)
    k_ = 1.0
    H = lambda x, y, z: tuple(A + V(x, y, z) * k_)
    CI.rbox(head, H(-8.0, -8.0, -14.0), H(8.0, 3.0, 1.5), hide, bevel=2.4)                       # the skull
    CI.rbox(head, H(-7.0, -5.5, -24.0), H(7.0, 3.0, -12.0), hide, bevel=2.2)                     # the beak's top
    CI.rbox(head, H(-6.0, -3.5, -26.0), H(6.0, 2.6, -21.0), plastron, bevel=1.6)                 # the pale beak
    for sx in (-1, 1):
        CI.box(head, H(sx * 3.5, -9.0, -15.0), H(sx * 8.6, -6.6, -4.0), dark, rot=(0.15, 0, 0), pivot=H(sx * 6.0, -7.8, -4.0))   # brow
        CI.eye(head, H(sx * 8.05, -4.4, -9.5), 3.8, 2.0, 'left' if sx > 0 else 'right',
               M('eye', '#f0a030', pupil='slit', mood='calm', lid='#585c52'))
        CI.box(head, H(sx * 2.2 - 0.6, -3.6, -26.1), H(sx * 2.2 + 0.6, -2.8, -25.6), M('simple', '#20201a'))   # nostrils
        # the stone crest: slabs rising back from the brow, green light in their cracks
        for j, (dz, h) in enumerate(((-8.0, 7.0), (-2.5, 10.0), (3.5, 8.0))):
            b0 = V(sx * (3.6 + j * 0.7), -7.0, dz)
            tip = b0 + V(sx * 1.6, -h, h * 0.55)
            CI.chain_boxes(head, [H(*b0), H(*(b0 + (tip - b0) * 0.5)), H(*tip)], 4.0, 2.4, rim)
            mid = b0 + (tip - b0) * 0.5
            CI.box(head, H(*(mid + V(sx * 1.6, -1.0, -0.6))), H(*(mid + V(sx * 2.1, 1.0, 0.6))), vein)
    moss_on(head, -8.0, 8.0, -8.0, 3.0, -14.0, 1.5, 12, (0, 1))
    jaw = r.bone('jaw', head, H(0, 3.0, -2.0), anim='jaw')
    CI.rbox(jaw, H(-7.2, 3.0, -24.5), H(7.2, 8.0, 1.0), plastron, bevel=1.8)
    for kk in range(12):                                                                          # moss hanging from the jaw
        x = -6.5 + kk * 1.2
        L = 3.0 + (kk * 37 % 6)
        zz = -18.0 + (kk % 4) * 4.0
        CI.box(jaw, H(x - 0.45, 8.0, zz), H(x + 0.45, 8.0 + L, zz + 0.9), moss if kk % 2 else moss2)
    # ------------------------------------------------------------------ the legs: stone pillars splayed out, pale toes
    for sx in (-1, 1):
        sd = 'r' if sx < 0 else 'l'
        for front, z0, anim in ((True, -15.0, 'leg_r' if sx < 0 else 'leg_l'), (False, 21.0, 'leg_l' if sx < 0 else 'leg_r')):
            name = ('leg_f' if front else 'leg_b') + sd
            hip = V(sx * 16.0, 5.0, z0)
            knee = V(sx * 19.5, 14.0, z0)
            foot = V(sx * 20.5, 22.0, z0 - 0.5)
            up = r.bone(name, body, tuple(hip), anim=anim)
            rseg(up, hip + V(0, -3.0, 0), knee, 13.5, 13.5, hide, up=(0, 0, -1), bevel=2.8)
            moss_on(up, hip[0] - 6.5, hip[0] + 6.5, hip[1] - 2.0, knee[1], z0 - 6.75, z0 + 6.75, 6, (2, -1))
            low = r.bone(name + '_low', up, tuple(knee), anim='knee')
            rseg(low, knee - V(0, 1.0, 0), foot, 13.0, 13.0, stone, up=(0, 0, -1), bevel=2.6)
            CI.box(low, (foot[0] - 7.0, 21.0, z0 - 7.5), (foot[0] + 7.0, 24.0, z0 + 6.5), dark)
            for t in range(4):                                                                    # the toes
                x = foot[0] + (t - 1.5) * 3.4
                CI.rbox(low, (x - 1.5, 19.0, z0 - 10.5), (x + 1.5, 24.0, z0 - 6.0), claw, bevel=0.6)
            CI.box(low, (foot[0] + sx * 6.55 - 0.1, 13.0, z0 - 3.0), (foot[0] + sx * 6.55 + 0.1, 20.0, z0 - 2.4), vein)
            CI.box(low, (foot[0] + sx * 6.55 - 0.1, 16.0, z0 - 2.4), (foot[0] + sx * 6.55 + 0.1, 16.6, z0 + 3.0), vein)
            CI.box(low, (foot[0] - 2.0, 15.0, z0 - 6.6), (foot[0] - 1.4, 19.0, z0 - 6.5), vein)
    # ------------------------------------------------------------------ the tail: long, thick, plated, green light along it
    def tail_extra(bone, p, q, w, i):
        m = (p + q) / 2
        CI.box(bone, tuple(m + V(-w * 0.38, -w * 0.5 - 1.6, -1.6)), tuple(m + V(w * 0.38, -w * 0.5 + 0.4, 1.6)), rim)
        for sx in (-1, 1):
            CI.box(bone, tuple(m + V(sx * w * 0.32, -w * 0.5 - 1.0, -1.2)), tuple(m + V(sx * (w * 0.32 + 1.6), -w * 0.5 + 0.4, 1.2)), stone)
            CI.box(bone, tuple(m + V(sx * w * 0.5 - (0.15 if sx < 0 else 0), -0.4, -1.4)),
                   tuple(m + V(sx * w * 0.5 + (0.15 if sx > 0 else 0), 0.2, 1.4)), vein)
    tail_chain(r, body, (0, 5.0, 30.0), 8, 34.0, 12.5, 4.0, hide, lambda t: 0.8 - 0.6 * t, extra=tail_extra)
    r.height = 24.0 - (-12.5 - 29.0 - 1.8)          # the hitbox to the mountain's snow
    return r

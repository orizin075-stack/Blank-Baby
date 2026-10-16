"""Sculpted humanoids with real human proportions (drop-in for humanoid.Humanoid).

About 6-7 heads tall (children about 4.5): a rounded skull with jaw, chin and nose, an anime face painted at
8 texels per pixel (large eyes with iris gradient, pupils, catchlights, lashes, brows, mouth), a neck,
sloping shoulders, chest / bust, waist and hips lofted as one body, long tapered legs with knees and
calves, arms with elbows and five-fingered hands, shoes. Hair is a cap that follows the skull plus
layered strand clumps (fringe, side locks, back hair, twin tails, ponytail). Clothing (skirts, robes,
capes, jackets, sleeves, sashes, armour) is sculpted over the body.

Bone names, hierarchy and animation tags are the ones RigModel animates (root, hips, torso/breath, head,
arm_*/fore_* (elbow), leg_*/shin_* (knee), hair, skirt, cape, wing_*, tail, blink), and fore_* carries
the palm 'reach' used for held relics."""
import math
import numpy as np
from paint import M
from colors import hexc, mix, shade, lum
import sculpt as SC

# Landmarks in model px above the ground (feet at y = 24): head crown/chin and half width/depth, neck radius,
# shoulder joint (x, height), torso rings (height, half width, half depth, superellipse exponent), hip joint
# (x, height), knee, ankle; arm: elbow and wrist heights, radii; leg radii.
TEMPLATES = {
    'woman': dict(crown=34.0, chin=28.3, hw=2.25, hd=2.5, neck_r=0.72, neck_top=26.6,
                  shoulder=(3.3, 25.7), rings=[(26.9, 0.85, 0.78, 2.0), (26.45, 2.3, 1.3, 2.6), (25.75, 3.3, 1.5, 3.0),
                                               (24.5, 3.0, 1.65, 2.5), (23.4, 2.8, 1.72, 2.3), (22.2, 2.4, 1.5, 2.2),
                                               (20.9, 2.1, 1.38, 2.2), (19.7, 2.65, 1.6, 2.4), (18.6, 3.05, 1.8, 2.5),
                                               (17.6, 2.85, 1.65, 2.4)],
                  waist=20.9, pelvis=19.7, hip=(1.45, 18.0), knee=9.6, ankle=1.05, elbow=20.6, wrist=16.3,
                  r_up=(0.74, 0.6), r_fore=(0.62, 0.43), r_thigh=(1.5, 0.98), r_shin=(0.95, 1.05, 0.55), bust=0.42, foot=3.1, head_box=6.4),
    'youth': dict(crown=34.5, chin=28.7, hw=2.25, hd=2.5, neck_r=0.8, neck_top=27.0,
                  shoulder=(3.55, 26.1), rings=[(27.3, 0.95, 0.85, 2.0), (26.85, 2.5, 1.35, 2.6), (26.15, 3.55, 1.55, 3.0),
                                                (24.9, 3.25, 1.7, 2.5), (23.6, 2.9, 1.65, 2.3), (22.3, 2.55, 1.5, 2.2),
                                                (21.0, 2.35, 1.42, 2.2), (19.8, 2.6, 1.55, 2.4), (18.7, 2.8, 1.65, 2.5),
                                                (17.7, 2.65, 1.58, 2.4)],
                  waist=21.0, pelvis=19.8, hip=(1.45, 18.2), knee=9.7, ankle=1.05, elbow=21.0, wrist=16.6,
                  r_up=(0.8, 0.64), r_fore=(0.68, 0.46), r_thigh=(1.45, 0.98), r_shin=(0.98, 1.08, 0.56), bust=0.0, foot=3.3, head_box=6.4),
    'man':   dict(crown=36.0, chin=30.0, hw=2.35, hd=2.6, neck_r=0.98, neck_top=28.2,
                  shoulder=(4.15, 27.4), rings=[(28.5, 1.15, 1.0, 2.0), (28.0, 3.0, 1.55, 2.6), (27.35, 4.25, 1.85, 3.0),
                                                (25.9, 3.95, 2.05, 2.6), (24.3, 3.5, 1.95, 2.4), (22.7, 2.95, 1.68, 2.3),
                                                (21.3, 2.95, 1.7, 2.3), (20.0, 3.1, 1.82, 2.4), (18.9, 2.95, 1.72, 2.4)],
                  waist=22.7, pelvis=20.4, hip=(1.65, 19.3), knee=10.2, ankle=1.05, elbow=21.9, wrist=17.2,
                  r_up=(1.0, 0.8), r_fore=(0.85, 0.55), r_thigh=(1.65, 1.1), r_shin=(1.1, 1.25, 0.64), bust=0.0, foot=3.6, head_box=6.4),
    'child': dict(crown=26.0, chin=20.6, hw=2.3, hd=2.5, neck_r=0.58, neck_top=19.75,
                  shoulder=(2.45, 19.2), rings=[(20.0, 0.68, 0.62, 2.0), (19.6, 1.75, 1.05, 2.5), (19.05, 2.4, 1.25, 2.8),
                                                (17.8, 2.25, 1.38, 2.4), (16.4, 2.05, 1.35, 2.2), (15.1, 2.0, 1.3, 2.2),
                                                (14.0, 2.25, 1.42, 2.4), (13.1, 2.15, 1.36, 2.4)],
                  waist=15.1, pelvis=14.0, hip=(1.08, 13.5), knee=7.0, ankle=0.85, elbow=15.5, wrist=12.2,
                  r_up=(0.58, 0.48), r_fore=(0.5, 0.36), r_thigh=(1.08, 0.75), r_shin=(0.74, 0.8, 0.45), bust=0.0, foot=2.4, head_box=6.8),
    'large': dict(crown=40.0, chin=33.8, hw=2.5, hd=2.8, neck_r=1.45, neck_top=31.6,
                  shoulder=(6.0, 30.4), rings=[(32.0, 1.6, 1.4, 2.0), (31.4, 4.4, 2.3, 2.6), (30.6, 6.1, 2.7, 3.0),
                                               (28.8, 5.6, 3.0, 2.6), (26.6, 5.0, 2.9, 2.4), (24.4, 4.3, 2.6, 2.3),
                                               (22.6, 4.3, 2.55, 2.3), (21.0, 4.4, 2.6, 2.4), (19.8, 4.1, 2.4, 2.4)],
                  waist=24.4, pelvis=22.0, hip=(2.35, 20.4), knee=10.6, ankle=1.1, elbow=24.4, wrist=18.6,
                  r_up=(1.6, 1.3), r_fore=(1.4, 0.95), r_thigh=(2.2, 1.55), r_shin=(1.55, 1.75, 0.95), bust=0.0, foot=4.4, head_box=6.8),
}

def _is_skin(m):
    return m is None or m.get('type') == 'skin'

def gauss(x, mu, s):
    return np.exp(-((x - mu) / s) ** 2)

# head profile: fraction of head height from the crown -> (half width, front extent, back extent) as fractions
HEAD = [(0.06, 0.58, 0.55, 0.72), (0.22, 0.9, 0.86, 1.04), (0.42, 1.0, 0.95, 1.1), (0.58, 0.97, 0.97, 1.0),
        (0.72, 0.86, 0.93, 0.74), (0.85, 0.62, 0.78, 0.46), (0.95, 0.34, 0.5, 0.3)]

class Humanoid:
    def __init__(self, rig, build='woman', skin='#f3dfd7', outfit='#ffffff', accent='#cccccc', hover=0.0, **over):
        T = dict(TEMPLATES[build])
        k = 1.05 if 'lh' in over else 1.0
        self.T, self.build, self.rig = T, build, rig
        self.sc = SC.Sculpt(rig)
        if lum(skin) > 0.9:
            skin = '#%02x%02x%02x' % mix(skin, '#f2cfc2', 0.35)
        self.skin_color = skin
        self.skin = M('skin', skin)
        self.accent = accent
        self.hair_color = '#3a2a24'
        Y = lambda h: 24 - h * k
        self.Y = Y
        self.hs = T['head_box']                       # Minecraft-style head: a rounded cube with a pixel face
        self.chin_y = Y(T['chin']) + 0.3
        self.head_top = self.chin_y - self.hs
        self.hh = self.hs
        self.hw = self.hd = self.hs / 2 + 0.4             # outer hair surface
        self.kh = self.hw / 4.0
        self.top = Y(T['rings'][2][0]) - 0.6
        self.waist_y = Y(T['waist'])
        self.pelvis_y = Y(T['pelvis'])
        self.hip_y = Y(T['hip'][1])
        self.knee_y = Y(T['knee'])
        self.ankle_y = Y(T['ankle'])
        self.elbow_y = Y(T['elbow'])
        self.wrist_y = Y(T['wrist'])
        self.rings = [(Y(h), a, b, e) for h, a, b, e in T['rings']]
        self.front_z = -self.rings[3][2]
        self.back_z = self.rings[3][2]
        sx, sy = T['shoulder']
        self.shoulder_x = sx
        self.root = rig.bone('root', None, (0, 24, 0), anim='root', hover=hover, speed=0.06)
        self.hips = rig.bone('hips', self.root, (0, self.hip_y, 0))
        self.torso = rig.bone('torso', self.hips, (0, self.waist_y, 0), anim='breath')
        neck_base = Y(T['neck_top'])
        self.neck_base = neck_base
        self.head = rig.bone('head', self.torso, (0, neck_base, 0), anim='head')
        ay = Y(sy)
        self.arm_r = rig.bone('arm_r', self.torso, (-sx, ay, 0), rot=(0, 0, 0.1), anim='arm_r')
        self.arm_l = rig.bone('arm_l', self.torso, (sx, ay, 0), rot=(0, 0, -0.1), anim='arm_l')
        self.shoulder_y = ay
        self.fore_r = rig.bone('fore_r', self.arm_r, (-sx, self.elbow_y, 0), rot=(-0.14, 0, 0), anim='elbow')
        self.fore_l = rig.bone('fore_l', self.arm_l, (sx, self.elbow_y, 0), rot=(-0.14, 0, 0), anim='elbow')
        self.hand_y = self.wrist_y + 1.0
        self.arm_len = self.wrist_y - ay
        lx = T['hip'][0]
        self.leg_x = lx
        self.leg_r = rig.bone('leg_r', self.hips, (-lx, self.hip_y, 0), anim='leg_r')
        self.leg_l = rig.bone('leg_l', self.hips, (lx, self.hip_y, 0), anim='leg_l')
        self.shin_r = rig.bone('shin_r', self.leg_r, (-lx, self.knee_y, 0), anim='knee')
        self.shin_l = rig.bone('shin_l', self.leg_l, (lx, self.knee_y, 0), anim='knee', side=1.0)
        self.B = {'head': 8}
        self.head_mat = None
        self.face_spec = {}
        self.robe_len = 0.0
        self.skirt_r = None
        self.hair_parts = 0

    # ------------------------------------------------------------------ helpers
    def ring_at(self, y, grow=0.0):
        rr = self.rings
        ys = [r[0] for r in rr]
        a = float(np.interp(y, ys, [r[1] for r in rr]))
        b = float(np.interp(y, ys, [r[2] for r in rr]))
        return a + grow, b + grow

    def head_profile(self, grow=0.0, t0=0.0, t1=1.0, n=None):
        """Path, half widths, half depths of the skull between fractions t0..t1 of its height (crown -> chin)."""
        ts = [p[0] for p in HEAD]
        tt = np.linspace(t0, t1, n or max(3, int(round((t1 - t0) * 9)) + 2))
        a = np.interp(tt, ts, [p[1] for p in HEAD]) * self.hw + grow
        fr = np.interp(tt, ts, [p[2] for p in HEAD]) * self.hd + grow
        bk = np.interp(tt, ts, [p[3] for p in HEAD]) * self.hd + grow
        b = (fr + bk) / 2
        zc = (bk - fr) / 2
        path = np.stack([np.zeros_like(tt), self.head_top + tt * self.hh, zc], 1)
        return path, a, b, tt

    def face_info(self):
        top, hh, hw = self.head_top, self.hh, self.hw
        man = self.build in ('man', 'large')
        child = self.build == 'child'
        return dict(eye_y=top + hh * (0.6 if not child else 0.62), eye_dx=hw * (0.45 if not man else 0.42),
                    eye_w=hw * (0.3 if not man else 0.25) * (1.08 if child else 1.0),
                    eye_h=hh * (0.135 if not man else 0.1) * (1.12 if child else 1.0),
                    brow_y=top + hh * (0.47 if not man else 0.5), nose_y=top + hh * 0.73, mouth_y=top + hh * 0.83,
                    chin_y=self.chin_y, hw=hw, man=man, child=child)

    # ------------------------------------------------------------------ body
    def body(self, top_mat, bottom_mat=None, waist_mat=None, legs_mat=None, boots_mat=None, arms_mat=None,
             hands_mat=None, sleeve_len=None, bust_mat=None, collar_mat=None, neck='auto', boots_h=None):
        T = self.T
        bottom_mat = bottom_mat or top_mat
        legs_mat = legs_mat or self.skin
        if neck == 'auto':
            neck = 'v' if self.build == 'woman' else ('round' if self.build == 'child' else None)
        self.top_mat, self.bottom_mat = top_mat, bottom_mat
        rr = self.rings
        ys = [r[0] for r in rr]
        y0 = ys[0]
        iw = int(np.argmin([abs(y - self.waist_y) for y in ys]))
        bust = T['bust'] if bust_mat is not False else 0.0
        yb = rr[4][0]
        tc = (yb - y0) / (self.waist_y - y0)
        muscle = 0.12 if self.build in ('man', 'large') else 0.0
        def mod(th, t):
            f = 1.0
            if bust:
                side = gauss(np.abs(th), 0.52, 0.42) * (np.abs(th) < 1.6)
                f = f + bust * gauss(t, tc, 0.16) * side
            if muscle:
                f = f + muscle * gauss(t, tc - 0.12, 0.2) * gauss(np.abs(th), 0.45, 0.6)
            f = f + 0.05 * gauss(t, 0.35, 0.2) * gauss(np.abs(th), math.pi * 0.8, 0.5)
            return f
        tm = dict(top_mat)
        info = {'torso': True, 'neckline': neck if tm.get('type') in ('cloth', 'metal') else None, 'skin': self.skin_color,
                'y_split': self.waist_y - 0.3 if waist_mat is None else self.waist_y - 1.6, 'lower': waist_mat or bottom_mat,
                'hem': False, 'collar': collar_mat, 'top': self.top}
        up = rr[:iw + 1]
        SC.sweep(self.torso, [(0, r[0], 0) for r in up], [r[1] for r in up], [r[2] for r in up], tm, e=[r[3] for r in up], k=32,
                 mod=mod, caps=('round', None), cap_len=0.6, name='torso', info=info, td=4)
        lo = rr[iw:]
        SC.sweep(self.hips, [(0, r[0], 0) for r in lo], [r[1] for r in lo], [r[2] for r in lo], bottom_mat, e=[r[3] for r in lo],
                 k=28, caps=(None, 'round'), cap_len=1.0, name='pelvis', info={'hem': False}, td=4)
        if tm.get('pattern') in ('kimono', 'asanoha'):
            self._kimono_collar(tm)
        nr = T['neck_r']
        SC.sweep(self.head, [(0, self.chin_y - 0.9, 0.35), (0, (self.chin_y + self.neck_base) / 2, 0.15), (0, self.neck_base + 0.5, 0.05)],
                 [nr, nr * 0.98, nr * 1.15], [nr * 1.05, nr, nr * 1.1], self.skin, k=12, caps=None, name='neck', info={'hem': False}, td=4)
        # arms
        total = self.wrist_y - self.shoulder_y
        upper = self.elbow_y - self.shoulder_y
        sl = total * 0.82 if sleeve_len is None else total * min(1.0, sleeve_len / 9.0)
        arms_mat = arms_mat or top_mat
        hm = hands_mat or self.skin
        self.arms_mat, self.hands_mat, self.sleeve_l = arms_mat, hm, sl
        ru0, ru1 = T['r_up']
        rf0, rf1 = T['r_fore']
        for arm, fore, sgn in ((self.arm_r, self.fore_r, -1), (self.arm_l, self.fore_l, 1)):
            x = arm.pivot[0]
            yS, yE, yW = self.shoulder_y, self.elbow_y, self.wrist_y
            up_mat = self.skin if sl < 0.6 else arms_mat
            SC.sweep(arm, [(x, yS - 0.1, 0), (x, yS + upper * 0.35, 0.02), (x, yE + 0.15, 0)], [ru0 * 1.05, ru0, ru1], None,
                     up_mat, k=14, caps=('round', 'round'), name='upper', info={'hem': False}, td=4)
            fore_mat = arms_mat if sl >= total - 0.3 else (hm if not _is_skin(hm) else self.skin)
            SC.sweep(fore, [(x, yE - 0.2, 0), (x, yE + (yW - yE) * 0.3, 0.05), (x, yW, 0)], [rf0 * 1.02, rf0 * 1.05, rf1], None,
                     fore_mat, k=14, caps=('round', 'round'), name='fore', info={'hem': False}, td=4)
            if 0.6 < sl < total - 0.3 and not _is_skin(arms_mat):
                end = yS + sl
                if end > yE:
                    t_end = (end - yE) / (yW - yE)
                    rr_end = rf0 + (rf1 - rf0) * t_end
                    SC.sweep(fore, [(x, yE - 0.4, 0), (x, end, 0.02)], [rf0 + 0.2, rr_end + 0.32], None, arms_mat, k=16,
                             caps=(None, 'flat'), name='sleeve', info={'hem': True}, td=4)
                else:
                    SC.sweep(arm, [(x, yS + 0.3, 0), (x, end, 0)], [ru0 + 0.2, ru1 + 0.3], None, arms_mat, k=16, caps=(None, 'flat'),
                             name='sleeve', info={'hem': True}, td=4)
            elif sl >= total - 0.3 and not _is_skin(arms_mat):
                SC.sweep(fore, [(x, yW - 1.4, 0.03), (x, yW + 0.1, 0.05)], [rf1 + 0.22, rf1 + 0.42], None, arms_mat, k=16,
                         caps=(None, 'flat'), name='cuff', info={'hem': True}, td=4)
            self._hand(fore, x, yW, sgn, hm)
            fore.params['reach'] = round(self.hand_y - yE, 3)
            arm.params['reach'] = round(self.hand_y - yS, 3)
        # legs
        bh = boots_h if boots_h is not None else (4 if boots_mat else 0)
        bh_px = 0 if not boots_mat else max(1.2, min(11.0, bh * (self.ankle_y - self.knee_y) / 6.0))
        self.legs_mat, self.boots_mat, self.boots_h = legs_mat, boots_mat, bh_px
        rt0, rt1 = T['r_thigh']
        rs0, rc, ra = T['r_shin']
        for leg, shin, sgn in ((self.leg_r, self.shin_r, -1), (self.leg_l, self.shin_l, 1)):
            x = leg.pivot[0]
            hy, ky, ay = self.hip_y, self.knee_y, self.ankle_y
            SC.sweep(leg, [(x, hy - 0.9, 0.05), (x, hy + (ky - hy) * 0.35, -0.05), (x, ky + 0.15, 0.0)], [rt0, rt0 * 0.88, rt1], None,
                     legs_mat, k=16, caps=('round', 'round'), name='thigh', info={'hem': False}, td=4)
            SC.sweep(shin, [(x, ky - 0.15, 0), (x, ky + (ay - ky) * 0.3, 0.12), (x, ky + (ay - ky) * 0.7, 0.05), (x, ay, 0.12)],
                     [rs0, rc, ra * 1.25, ra], None, legs_mat, k=16, caps=('round', None), name='shin', info={'hem': False}, td=4,
                     mod=lambda th, t: 1 + 0.08 * gauss(np.abs(th), math.pi, 0.9) * gauss(t, 0.3, 0.25))
            foot_mat = boots_mat or legs_mat
            if boots_mat and bh_px > 0:
                ytop = ay - bh_px
                ys_ = np.linspace(ytop, ay + 0.2, 5)
                prof_y = [ky, ky + (ay - ky) * 0.3, ky + (ay - ky) * 0.7, ay]
                rad = [float(np.interp(y, prof_y, [rs0, rc, ra * 1.25, ra])) + 0.2 for y in ys_]
                rad[0] += 0.12
                SC.sweep(shin, [(x, y, 0.08) for y in ys_], rad, None, boots_mat, k=16, caps=(None, None), name='boot', info={'hem': False}, td=4)
                SC.torus(shin, (x, ytop + 0.12, 0.08), rad[0], 0.2, boots_mat, k=6, n=14, name='boot_cuff')
            self._foot(shin, x, foot_mat, boots_mat is not None)
        if collar_mat:
            r3 = [(y, a + 0.25, b + 0.25, e) for y, a, b, e in self.rings[:3]]
            SC.sweep(self.torso, [(0, r[0], 0) for r in r3], [r[1] for r in r3], [r[2] for r in r3], collar_mat, e=[r[3] for r in r3], k=28,
                     caps=(None, None), name='collar', info={'hem': True}, td=4)
        return self

    def _foot(self, shin, x, mat, boot):
        T = self.T
        L = T['foot']
        ra = T['r_shin'][2]
        y = 24 - 0.55
        h = 0.62 if not boot else 0.7
        SC.sweep(shin, [(x, y - 0.25, 0.55), (x, y, -L * 0.25), (x, y + 0.05, -L * 0.62), (x, y + 0.1, -L * 0.85)],
                 [ra * 1.0, ra * 1.18, ra * 1.12, ra * 0.85], [h, h * 0.95, h * 0.78, h * 0.62], mat, k=14, up=(0, -1, 0),
                 caps=('round', 'round'), name='foot', info={'hem': False}, td=4)

    def _hand(self, fore, x, yW, sgn, mat):
        T = self.T
        s = T['r_fore'][1] / 0.43
        y0 = yW + 0.05
        SC.sweep(fore, [(x, y0 - 0.2, 0.0), (x, y0 + 0.45 * s, -0.04), (x, y0 + 0.95 * s, -0.06)], [0.42 * s, 0.5 * s, 0.48 * s],
                 [0.25 * s, 0.27 * s, 0.22 * s], mat, k=10, caps=('round', None), name='palm', info={'hem': False}, td=4)
        for i in range(4):
            fx = x + (i - 1.5) * 0.24 * s * (-sgn)
            L = (0.95, 1.05, 1.0, 0.8)[i] * s
            yb = y0 + 0.9 * s
            pts = [(fx, yb - 0.1, -0.06), (fx, yb + L * 0.55, -0.12), (fx, yb + L, -0.35 * s)]
            SC.sweep(fore, pts, [0.12 * s, 0.11 * s, 0.09 * s], None, mat, k=6, caps=(None, 'round'), name='finger', info={'hem': False}, td=4)
        SC.sweep(fore, [(x + sgn * 0.3 * s, y0 + 0.15 * s, -0.18 * s), (x + sgn * 0.42 * s, y0 + 0.6 * s, -0.42 * s),
                        (x + sgn * 0.3 * s, y0 + 1.05 * s, -0.55 * s)], [0.15 * s, 0.13 * s, 0.11 * s], None, mat, k=6,
                 caps=('round', 'round'), name='thumb', info={'hem': False}, td=4)

    def _kimono_collar(self, tm):
        """Crossed collar: two raised bands from behind the neck over the shoulders, crossing on the chest
        (the left panel over the right) down to the sash."""
        acc = tm.get('accent', shade(tm['color'], 0.7))
        cm = M('cloth', acc, accent=shade(acc, 0.7), hem_shadow=False)
        r1 = self.rings[1]
        yb_ = self.rings[4][0]
        a4, b4 = self.ring_at(yb_)
        bz = b4 * (1 + self.T['bust'] * 0.8)
        for sgn, dz in ((1, 0.2), (-1, 0.1)):
            pts = [(sgn * 0.75, r1[0] - 0.3, 0.75), (sgn * 1.55, r1[0] + 0.05, -r1[2] * 0.6),
                   (sgn * 0.85, yb_, -bz - dz), (-sgn * 0.7, self.waist_y + 0.3, -self.ring_at(self.waist_y)[1] - dz - 0.05)]
            SC.sweep(self.torso, SC.bezier(*pts, n=12), 0.42, 0.11, cm, e=3.0, k=8, up=(0, -0.3, -1), caps=('round', 'flat'),
                     name='collar_band', info={'hem': False}, td=4)

    def jacket(self, mat, rows=None, open_front=True):
        rr = [(y, a + 0.24, b + 0.24, e) for y, a, b, e in self.rings[1:]]
        bust = self.T['bust']
        yb_ = self.rings[4][0]
        tcb = (yb_ - rr[0][0]) / (rr[-1][0] - rr[0][0])
        def mod(th, t):
            return 1 + bust * 0.7 * gauss(t, tcb, 0.18) * gauss(np.abs(th), 0.5, 0.45)
        ar = (0.38, 2 * math.pi - 0.38) if open_front else None
        SC.sweep(self.torso, [(0, r[0], 0) for r in rr], [r[1] for r in rr], [r[2] for r in rr], dict(mat), e=[r[3] for r in rr],
                 k=30, caps=(None, None), arc_range=ar, mod=mod, name='jacket', info={'hem': True}, td=4)
        if open_front:
            for sgn in (-1, 1):
                y0 = rr[0][0]
                SC.sweep(self.torso, SC.bezier((sgn * 0.9, y0 - 0.1, -rr[1][2] * 0.9), (sgn * 1.6, y0 + 1.8, -rr[2][2] - 0.35),
                                               (sgn * 1.0, y0 + 3.4, -rr[3][2] - 0.25), n=8),
                         lambda t: 0.62 - 0.4 * t, 0.12, dict(mat, pattern=None), k=8, up=(0, 0, -1), caps=('flat', 'point'),
                         name='lapel', info={'hem': False}, td=4)
        return self

    def kimono_sleeves(self, mat, drop=6.0, width=None):
        T = self.T
        ru0 = T['r_up'][0]
        rf0, rf1 = T['r_fore']
        dropk = drop * 0.75
        for arm, fore, sgn in ((self.arm_r, self.fore_r, -1), (self.arm_l, self.fore_l, 1)):
            x = arm.pivot[0]
            SC.sweep(arm, [(x, self.shoulder_y - 0.1, 0), (x, self.elbow_y + 0.3, 0)], [ru0 + 0.3, ru0 + 0.55], None, mat, k=16,
                     caps=('round', None), name='sleeve_up', info={'hem': False}, td=4)
            yE, yW = self.elbow_y, self.wrist_y
            D = rf0 + 1.6
            SC.sweep(fore, [(x, yE - 0.5, 0), (x, (yE + yW) / 2, 0.25), (x, yW - 0.2, 0.45)],
                     [rf0 + 0.55, rf0 + 1.05, rf0 + 1.3], [rf0 + 0.55, D * 0.85, D + 0.15], mat, k=24, caps=(None, None),
                     name='sleeve', info={'hem': True}, td=4)
            if dropk > 0:
                yb = yW - 0.2
                Dz = D + 0.15
                pts = SC.bezier((x, yb - 1.3, Dz * 0.45), (x, yb + dropk * 0.4, Dz * 0.8), (x, yb + dropk * 0.85, Dz * 0.5), n=8)
                SC.sweep(fore, pts, lambda t: rf0 + 1.3 - 0.25 * t, 0.26, dict(mat), k=12, up=(0, 0, 1),
                         caps=('flat', 'round'), name='sleeve_flap', info={'hem': True, 'hem_cut': 'scallop'}, td=4)
        return self

    def puff_sleeves(self, mat):
        ru0 = self.T['r_up'][0]
        for arm in (self.arm_r, self.arm_l):
            x = arm.pivot[0]
            y = self.shoulder_y
            SC.sweep(arm, [(x, y - 0.4, 0), (x, y + 0.9, 0), (x, y + 2.0, 0)], [ru0 + 0.6, ru0 + 0.95, ru0 + 0.3], None, mat, k=16,
                     caps=('round', 'flat'), mod=lambda th, t: 1 + 0.06 * np.cos(8 * th), name='puff', info={'folds': 8, 'hem': True}, td=4)
        return self

    def cuffs(self, mat, at=None):
        rf1 = self.T['r_fore'][1]
        y = self.wrist_y - 0.9
        for fore in (self.fore_r, self.fore_l):
            x = fore.pivot[0]
            SC.sweep(fore, [(x, y - 0.5, 0), (x, y + 0.6, 0)], rf1 + 0.3, None, mat, k=14, caps=(None, None), name='cuff',
                     info={'hem': False}, td=4)
        return self

    def obi(self, mat, knot=None):
        y0 = self.waist_y - 1.3
        y1 = self.waist_y + 0.5
        ys = np.linspace(y0, y1, 3)
        a = [self.ring_at(y, 0.22)[0] for y in ys]
        b = [self.ring_at(y, 0.22)[1] for y in ys]
        SC.sweep(self.torso, [(0, y, 0) for y in ys], a, b, mat, e=2.3, k=28, caps=(None, None), name='obi', info={'hem': False}, td=4)
        if knot:
            z = b[1] + 0.15
            yk = (y0 + y1) / 2
            k = self.rig.bone('obi_knot', self.torso, (0, yk, z), anim='sway', ax=2, amp=0.04, speed=0.05)
            for sgn in (-1, 1):
                SC.sweep(k, SC.bezier((0, yk, z + 0.25), (sgn * 1.3, yk - 1.3, z + 0.8), (sgn * 2.6, yk - 0.3, z + 0.65), n=8),
                         lambda t: 0.45 + 0.85 * math.sin(math.pi * t), 0.32, dict(knot), k=10, up=(0, 0, 1), caps=('round', 'round'),
                         name='bow', info={'hem': False}, td=4)
                SC.sweep(k, SC.bezier((sgn * 0.25, yk + 0.25, z + 0.4), (sgn * 0.8, yk + 2.2, z + 1.0), (sgn * 1.1, yk + 4.2, z + 0.75), n=8),
                         lambda t: 0.6 - 0.12 * t, 0.16, dict(knot), k=8, up=(0, 0, 1), caps=('flat', 'point'), name='bow_tail',
                         info={'hem': False}, td=4)
            SC.sweep(k, [(0, yk - 0.55, z + 0.25), (0, yk + 0.55, z + 0.25)], 0.55, 0.4, dict(knot), k=10, caps=('round', 'round'),
                     name='bow_knot', info={'hem': False}, td=4)
        return self

    def boots(self, mat, height=5.0):
        T = self.T
        rs0, rc, ra = T['r_shin']
        H = height * (self.ankle_y - self.knee_y) / 6.0
        for shin in (self.shin_r, self.shin_l):
            x = shin.pivot[0]
            yt = self.ankle_y - H
            SC.sweep(shin, [(x, yt, 0.08), (x, self.ankle_y + 0.2, 0.1)], [rc + 0.25, ra + 0.25], None, mat, k=16, caps=(None, None),
                     name='boot2', info={'hem': False}, td=4)
        return self

    # ------------------------------------------------------------------ head
    def head_cube(self, face_spec, skin=None):
        """Rounded-cube head with the 8x8 pixel face (face8) painted at 4 texels per face pixel, and the
        eyelid plate that RigModel shows for three ticks when the character blinks."""
        hs = self.hs
        sk = (skin or self.skin)['color'] if isinstance(skin, dict) else (skin or self.skin_color)
        self.face_spec = dict(face_spec)
        mat = M('head', sk, face=self.face_spec, hair=self.hair_color, build=self.build)
        self.head_mat = mat
        top = self.head_top
        SC.rbox(self.head, (-hs / 2, top, -hs / 2), (hs, hs, hs), mat, radius=0.8, name='head', td=32.0 / hs,
                info={'cells': (8, 8), 'head': True})
        if face_spec.get('blink', True):
            b = self.rig.bone('blink', self.head, (0, top, -hs / 2 - 0.04), anim='blink', every=float(face_spec.get('blink_every', 90)))
            bm = M('blink', sk, face=self.face_spec, hair=self.hair_color, build=self.build)
            self.blink_mat = bm
            SC.rbox(b, (-hs / 2, top, -hs / 2 - 0.05), (hs, hs, 0), bm, radius=0, name='lids', skip=('back',), td=32.0 / hs,
                    info={'cells': (8, 8), 'ao': False, 'lids': True})
        return self

    def face_info(self):
        return dict(eye_y=self.head_top + self.hs * 0.6)

    def _set_hair_color(self, color):
        self.hair_color = color
        if self.head_mat is not None:
            self.head_mat['hair'] = color
        if getattr(self, 'blink_mat', None) is not None:
            self.blink_mat['hair'] = color

    def strand(self, bone, pts, width, thick, mat, up, tip='point', taper=0.75, name='strand', bulge=0.12, n=10, **info):
        pts = np.asarray(pts, float)
        path = SC.bezier(*pts, n=n) if len(pts) <= 5 else pts
        self.hair_parts += 1
        seed = self.hair_parts
        return SC.sweep(bone, path, lambda t: width / 2 * (1 + bulge * math.sin(math.pi * t) - taper * t ** 2.2),
                        lambda t: thick / 2 * (1 - 0.45 * t), mat, e=2.3, k=8, up=up, caps=('round', tip), name=name,
                        info=dict({'seed': seed}, **info), td=4)

    def _split_strand(self, parent, bname, pts, split, width, thick, mat, up, anim_kw, tip='point', n=11, name='strand'):
        P = SC.bezier(*np.asarray(pts, float), n=n)
        k = int(round(split * (n - 1)))
        k = min(max(k, 2), n - 3)
        up_b = self.rig.bone(bname, parent, tuple(P[0]), anim='hair', **anim_kw)
        lo_b = self.rig.bone(bname + '_tip', up_b, tuple(P[k]), anim='hair', **dict(anim_kw, amp=anim_kw.get('amp', 0.03) * 1.6,
                                                                                     phase=anim_kw.get('phase', 0) + 0.6))
        self.hair_parts += 1
        seed = self.hair_parts
        tt = np.linspace(0, 1, n)
        wfun = lambda t: width / 2 * (1 + 0.15 * math.sin(math.pi * t) - 0.78 * t ** 2.2)
        tfun = lambda t: thick / 2 * (1 - 0.45 * t)
        SC.sweep(up_b, P[:k + 1], [wfun(t) for t in tt[:k + 1]], [tfun(t) for t in tt[:k + 1]], mat, e=2.3, k=8, up=up,
                 caps=('round', None), name=name, info={'seed': seed, 't0': 0.0, 't1': split}, td=4)
        SC.sweep(lo_b, P[k:], [wfun(t) for t in tt[k:]], [tfun(t) for t in tt[k:]], mat, e=2.3, k=8, up=up, caps=('round', tip),
                 name=name, info={'seed': seed, 't0': split, 't1': 1.0}, td=4)
        return up_b, lo_b

    def hair(self, color, style='long', length=12.0, tip=None, bangs=None, side_locks=True, twin=False, ponytail=False,
             ahoge=False, volume=0.5, shine=True, ears_open=False, side_len=None, fringe=True):
        self._set_hair_color(color)
        hs = self.hs
        top = self.head_top
        g = 0.4
        H = hs / 2 + g                       # half size of the hair shell
        if bangs is None:
            bangs = 'bangs' if self.build in ('woman', 'child', 'youth') else 'short'
        if bangs is False:
            bangs = 'open'
        man = self.build in ('man', 'large')
        long_sides = style in ('long', 'very_long', 'wavy', 'bob') or self.build == 'woman'
        shell = M('hair_shell', color, tip=None, bangs=bangs, long=long_sides, shine=shine, ears_open=ears_open,
                  back=style != 'short' or not man)
        SC.rbox(self.head, (-hs / 2, top, -hs / 2), (hs, hs, hs), shell, radius=1.5, grow=g, name='hair', skip=('bottom',),
                td=40.0 / (hs + 2 * g), info={'cells': (8, 8)})
        hm = M('hair', color, tip=tip, shine=shine)
        self.hair_mat = hm
        zf = -H - 0.1
        zb = H
        L = float(length) * 0.95
        if fringe and bangs not in ('open', 'slick', 'none'):
            fr = self.rig.bone('fringe', self.head, (0, top, zf), anim='hair', amp=0.015, speed=0.09)
            if bangs == 'parted':
                xs = (-2.4, -1.3, 1.3, 2.4)
            elif bangs == 'short':
                xs = (-2.0, 0.0, 2.0)
            else:
                xs = (-2.5, -1.25, 0.0, 1.25, 2.5)
            for i, x0 in enumerate(xs):
                Lf = hs * (0.36 + (0.05 if i % 2 == 0 else 0.0) + (0.04 if bangs == 'blunt' else 0)) * (0.85 if man else 1.0)
                sway = -0.4 * np.sign(x0) if bangs == 'swept' else 0.1 * np.sign(x0)
                self.strand(fr, [(x0 * 0.92, top - 0.2, zf + 0.5), (x0 + sway * 0.5, top + hs * 0.16, zf - 0.3),
                                 (x0 * 1.02 + sway, top + Lf, zf - 0.05)], 1.7 if not man else 1.9, 0.5, dict(hm, shine_y=0.3),
                            up=(0, 0, -1), tip='flat' if bangs == 'blunt' else 'point', name='fringe', n=6)
        if style in ('long', 'very_long', 'wavy'):
            xs = (-2.4, -1.2, 0.0, 1.2, 2.4)
            wide = 2.3 if style != 'very_long' else 2.5
            for k, x0 in enumerate(xs):
                Lk = L + (0.8 if k == 2 else -0.5 * abs(k - 2) + 0.4)
                wav = (lambda q, k=k: 0.45 * math.sin(q * 1.3 + k)) if style == 'wavy' else (lambda q: 0.0)
                pts = [(x0 * 0.85, top + 0.4, zb - 0.6), (x0 * 1.05, top + hs * 0.6, zb + 1.0),
                       (x0 * 1.18 + wav(1), top + 1.0 + Lk * 0.62, zb + 0.8 + 0.1 * abs(x0)),
                       (x0 * 1.28 + wav(2), top + 1.0 + Lk, zb + 0.45 + 0.15 * abs(x0))]
                self._split_strand(self.head, f'hair_back{k}', pts, 0.45, wide, 0.85, hm, (0, 0, 1),
                                   dict(amp=0.02, speed=0.07, phase=0.45 * k, drag=0.35), tip='point')
            for sgn in (-1, 1):
                pts = [(sgn * (H - 0.5), top + hs * 0.35, 1.0), (sgn * (H + 0.6), top + hs * 0.85, 1.4),
                       (sgn * (H + 0.8), top + 1.0 + L * 0.7, 1.8), (sgn * (H + 0.6), top + 1.0 + L * 0.92, 1.9)]
                self._split_strand(self.head, f'hair_side_{"r" if sgn < 0 else "l"}', pts, 0.42, 2.0, 0.8, hm, (sgn, 0, 0.4),
                                   dict(amp=0.025, speed=0.08, phase=sgn * 0.7, drag=0.3), tip='point')
        elif style == 'bob':
            for k, ang in enumerate(np.linspace(-1.95, 1.95, 7)):
                x0, z0 = math.sin(ang) * H, math.cos(ang) * H
                self.strand(self.head, [(x0 * 0.85, top + hs * 0.3, z0 * 0.85), (x0 * 1.12, top + hs * 0.7, z0 * 1.1),
                                        (x0 * 1.12, top + hs * 1.0, z0 * 1.08)], 2.3, 0.7, hm,
                            up=(math.sin(ang), 0, math.cos(ang)), tip='round', taper=0.35, name='bob', n=8)
        else:
            for k, (x0, z0) in enumerate(((-2.0, -1.6), (0.0, -2.2), (2.0, -1.5), (-1.2, 1.8), (1.2, 1.8), (0.0, 0.1))):
                self.strand(self.head, [(x0 * 0.8, top + 0.2, z0 * 0.8), (x0 * 1.05, top - 0.75, z0 * 1.1), (x0 * 1.25, top + 0.2, z0 * 1.3)],
                            2.3, 0.75, hm, up=(x0 / 3, -1, z0 / 3), name='tuft', n=6)
            for k, ang in enumerate(np.linspace(-2.3, 2.3, 9)):
                x0, z0 = math.sin(ang) * H, math.cos(ang) * H
                if abs(ang) < 0.7:
                    continue
                drop = hs * (0.62 if abs(ang) > 1.6 else 0.72) * (0.85 if man else 1.0)
                self.strand(self.head, [(x0 * 0.9, top + hs * 0.25, z0 * 0.9), (x0 * 1.08, top + hs * 0.5, z0 * 1.08),
                                        (x0 * 1.03, top + drop, z0 * 1.03)], 2.2, 0.65, hm, up=(math.sin(ang), 0, math.cos(ang)),
                            name='tuft', n=7, taper=0.6)
        if side_locks and long_sides:
            sl = side_len or min(9, max(3, L * 0.38))
            for sgn in (-1, 1):
                nm = 'r' if sgn < 0 else 'l'
                b_ = self.rig.bone(f'lock_{nm}', self.head, (sgn * H, top + hs * 0.35, -H + 0.8), anim='hair', amp=0.03, speed=0.09,
                                   phase=sgn)
                self.strand(b_, [(sgn * (H - 0.3), top + hs * 0.25, -H + 0.7), (sgn * (H + 0.25), top + hs * 0.7, -H + 0.5),
                                 (sgn * (H + 0.15), top + hs * 0.55 + sl, -H + 0.8)], 1.6, 0.6, dict(hm, t0=0.2, t1=0.9),
                            up=(sgn, 0, -0.3), name='lock', n=9)
        if twin:
            for sgn in (-1, 1):
                nm = 'r' if sgn < 0 else 'l'
                pts = [(sgn * (H - 0.4), top + hs * 0.2, 0.8), (sgn * (H + 2.2), top + hs * 0.05, 1.2),
                       (sgn * (H + 2.6), top + 2 + L * 0.45, 1.6), (sgn * (H + 1.8), top + 1.5 + L * 0.9, 1.9)]
                P = SC.bezier(*np.asarray(pts, float), n=12)
                up_b = self.rig.bone(f'twin_{nm}', self.head, tuple(P[0]), anim='hair', amp=0.06, speed=0.08, phase=sgn * 1.3, drag=0.5)
                lo_b = self.rig.bone(f'twin_{nm}_tip', up_b, tuple(P[5]), anim='hair', amp=0.09, speed=0.08, phase=sgn * 1.3 + 0.6, drag=0.6)
                rfun = lambda t: 1.1 + 0.45 * math.sin(math.pi * min(1, t * 1.4)) - 0.9 * t ** 2.5
                tt_ = np.linspace(0, 1, 12)
                SC.sweep(up_b, P[:6], [rfun(t) for t in tt_[:6]], [rfun(t) * 0.85 for t in tt_[:6]], dict(hm, t0=0, t1=0.5), k=10,
                         up=(0, 0, 1), caps=('round', None), name='twin', info={'seed': 7}, td=4)
                SC.sweep(lo_b, P[5:], [rfun(t) for t in tt_[5:]], [rfun(t) * 0.85 for t in tt_[5:]], dict(hm, t0=0.5, t1=1.0), k=10,
                         up=(0, 0, 1), caps=('round', 'point'), name='twin', info={'seed': 7}, td=4)
                SC.torus(up_b, tuple(P[1]), 1.0, 0.3, M('cloth', self.accent), axis='x', k=6, n=14, name='twin_tie')
        if ponytail:
            pts = [(0, top + hs * 0.35, zb - 0.4), (0, top + hs * 0.1, zb + 2.2), (0, top + 1.5 + L * 0.45, zb + 2.6),
                   (0, top + 1.5 + L * 0.9, zb + 1.5)]
            P = SC.bezier(*np.asarray(pts, float), n=12)
            up_b = self.rig.bone('ponytail', self.head, tuple(P[0]), anim='hair', amp=0.07, speed=0.08, phase=0.5, drag=0.7)
            lo_b = self.rig.bone('ponytail2', up_b, tuple(P[5]), anim='hair', amp=0.09, speed=0.08, phase=1.1, drag=0.7)
            rfun = lambda t: 1.0 + 0.5 * math.sin(math.pi * min(1, t * 1.3)) - 0.85 * t ** 2.5
            tt_ = np.linspace(0, 1, 12)
            SC.sweep(up_b, P[:6], [rfun(t) for t in tt_[:6]], [rfun(t) * 0.8 for t in tt_[:6]], dict(hm, t0=0.1, t1=0.5), k=10,
                     up=(0, -1, 0), caps=('round', None), name='tail', info={'seed': 3}, td=4)
            SC.sweep(lo_b, P[5:], [rfun(t) for t in tt_[5:]], [rfun(t) * 0.8 for t in tt_[5:]], dict(hm, t0=0.5, t1=1.0), k=10,
                     up=(0, -1, 0), caps=('round', 'point'), name='tail', info={'seed': 3}, td=4)
            SC.torus(up_b, tuple(P[1]), 0.9, 0.3, M('cloth', self.accent), axis='z', k=6, n=14, name='tie')
        if ahoge:
            b_ = self.rig.bone('ahoge', self.head, (0, top - 0.5, -0.8), anim='sway', ax=2, amp=0.08, speed=0.1)
            self.strand(b_, [(0.1, top - 0.1, -0.8), (0.5, top - 2.4, -1.3), (1.6, top - 2.8, -0.5)], 0.85, 0.32, hm, up=(0, 0, -1),
                        name='ahoge', n=8)
        return self

    # ------------------------------------------------------------------ skirts and robes
    def flare(self, parent, y0, rx, rz, length, angle, mat, count=None, name='skirt', k=1.0, start=0.0, sweep=1.0,
              shape='trap', folds=None, hem_cut=None, panels=None, inner=0.0):
        """Pleated bell (skirt / robe / tails) split into swaying panels on 'skirt' bones."""
        L = float(length)
        spread = L * math.tan(angle)
        nf = folds or max(8, int(round((2 * math.pi * (rx + rz) / 2 + spread * 3) / 1.8)))
        npan = panels or max(4, min(10, nf // 2))
        if sweep < 1:
            npan = max(2, int(round(npan * sweep)))
        hub = self.rig.bone(name, parent, (0, y0, 0))
        th0 = -math.pi + 2 * math.pi * start
        span = 2 * math.pi * sweep
        for i in range(npan):
            ta = th0 + span * i / npan
            tb = th0 + span * (i + 1) / npan
            tm = (ta + tb) / 2
            px, pz = -rx * math.sin(tm), -rz * math.cos(tm)
            nx, nz = -math.sin(tm) / rx, -math.cos(tm) / rz
            yaw = math.atan2(-nx, -nz)
            yb = self.rig.bone(f'{name}_y{i}', hub, (px, y0, pz), rot=(0, yaw, 0))
            tb_ = self.rig.bone(f'{name}_p{i}', yb, (px, y0, pz), anim='skirt', k=k)
            n_r = 6
            ys = np.linspace(y0, y0 + L, n_r)
            tt = np.linspace(0, 1, n_r)
            prof = tt ** 1.25
            A = rx + spread * prof
            Bz = rz + spread * prof
            def mod(th, t, nf=nf):
                return 1 + 0.06 * (0.25 + t) * np.cos(nf * th)
            kk = max(4, int(round(28 * (tb - ta) / (2 * math.pi) * 2)))
            SC.sweep(tb_, [(0, y, 0) for y in ys], A, Bz, mat, k=kk, caps=None, arc_range=(ta, tb), mod=mod,
                     name=name, info={'folds': nf, 'world': True, 'hem': True, 'hem_cut': hem_cut, 'pattern': True}, td=4)
            if inner:
                SC.sweep(tb_, [(0, y, 0) for y in ys], A - inner, Bz - inner, dict(mat, color=shade(mat['color'], 0.55), pattern=None, trim=0),
                         k=kk, caps=None, arc_range=(ta, tb), mod=mod, name=name + '_in',
                         info={'folds': nf, 'world': True, 'hem': False, 'inside': True}, td=2)
        return hub

    def _waist_ring(self, y, grow):
        return self.ring_at(y, grow)

    def _band(self, mat, name, y0, y1, grow=0.22):
        ys = np.linspace(y0, y1, 3)
        a = [self.ring_at(y, grow)[0] for y in ys]
        b = [self.ring_at(y, grow)[1] for y in ys]
        SC.sweep(self.hips, [(0, y, 0) for y in ys], a, b, dict(mat, pattern=None, trim=0), e=2.4, k=28, caps=(None, None), name=name,
                 info={'hem': False}, td=4)
        return y1, a[-1], b[-1]

    def skirt(self, mat, length=9.0, flare=1.4, layers=1, top_y=None, tiers=2, name='skirt'):
        y0 = self.waist_y - 0.2 if top_y is None else top_y
        ang = min(0.6, 0.18 + flare * 0.13)
        L = max(4.0, length * 0.85)
        yb, a, b = self._band(mat, name + '_band', y0 - 0.3, y0 + 1.0)
        if tiers >= 2:
            inner = dict(mat)
            inner.pop('pattern', None)
            inner['trim'] = mat.get('trim', 0) or 2
            self.flare(self.hips, y0 + 0.6, a - 0.12, b - 0.12, L + 1.2, ang * 0.85, dict(inner, color=shade(mat['color'], 0.82)),
                       name=name + '_under', k=0.7, hem_cut='scallop')
        hub = self.flare(self.hips, y0 + 0.4, a + 0.04, b + 0.04, L, ang, mat, name=name, inner=0.1)
        self.skirt_r = (y0, a + L * math.tan(ang), b + L * math.tan(ang))
        return hub

    def robe(self, mat, length=None, flare=2.4, split=False):
        y0 = self.waist_y - 0.2
        L = (24 - y0 - 0.35) if length is None else length
        ang = math.atan2(flare * 0.75 + 0.9, L)
        yb, a, b = self._band(mat, 'robe_band', y0 - 0.3, y0 + 1.0)
        kw = dict(start=0.06, sweep=0.88) if split else {}
        self.flare(self.hips, y0 + 0.4, a + 0.04, b + 0.04, L - 0.4, ang, dict(mat), name='robe', k=0.5, inner=0.1, **kw)
        self.robe_len = L
        self.skirt_r = (y0, a + L * math.tan(ang), b + L * math.tan(ang))
        return self

    def coat_tails(self, mat, length=10.0):
        y0 = self.waist_y + 0.2
        a, b = self.ring_at(y0, 0.35)
        self.flare(self.hips, y0, a, b, float(length) * 0.95, 0.2, dict(mat), name='coat', k=0.6, start=0.3, sweep=0.4, panels=4, inner=0.08)
        return self

    def cape(self, mat, length=16.0, width=None, top=None):
        w = float(width or 9) * 0.82
        y0 = (top if top is not None else self.top) + 0.1
        z = self.rings[3][2] + 0.4
        L = float(length) * 1.05
        h1 = L * 0.45
        a = self.rig.bone('cape', self.torso, (0, y0, z), rot=(0.08, 0, 0), anim='cape', amp=0.04, speed=0.06)
        b = self.rig.bone('cape_low', a, (0, y0 + h1, z + 0.6), rot=(0.06, 0, 0), anim='cape', amp=0.05, speed=0.06, phase=0.8, drag=0.4)
        nf = max(3, int(w / 2.0))
        def off(th, t, w=w):
            s = np.sin(th)
            wrap = (0.9 - 0.7 * t) * (s ** 2) * 2.0
            fold = 0.45 * (0.2 + t) * np.sin(nf * math.pi * s)
            return 0 * th, -wrap + fold
        tt = np.linspace(0, 1, 9)
        path = np.stack([np.zeros(9), y0 + 0.3 + tt * (L - 0.3), z + 0.15 + tt * 1.4 + 0.5 * tt ** 2], 1)
        k = int(np.searchsorted(tt * (L - 0.3), h1))
        k = min(max(k, 2), 6)
        wid = [w / 2 * (0.8 + 0.32 * t) for t in tt]
        for bone, sl, nm, hc in ((a, slice(0, k + 1), 'cape', None), (b, slice(k, 9), 'cape_hem', 'scallop')):
            SC.sweep(bone, path[sl], wid[sl], 0.22, dict(mat), e=6, k=34, up=(0, 0, 1), caps=(None, None), off=off,
                     name=nm, info={'hem': nm == 'cape_hem', 'hem_cut': hc, 'cape': True}, td=4)
        r3 = [(y - 0.1, aa + 0.35, bb + 0.35, e) for y, aa, bb, e in self.rings[:4]]
        SC.sweep(self.torso, [(0, r[0], 0.05) for r in r3], [r[1] for r in r3], [r[2] for r in r3], dict(mat, pattern=None), e=[r[3] for r in r3],
                 k=28, caps=('round', None), cap_len=0.35, name='mantle', info={'hem': True}, td=4)
        return a

    def shoulder_pads(self, mat, size=3.2):
        ru0 = self.T['r_up'][0]
        for arm, sgn in ((self.arm_r, -1), (self.arm_l, 1)):
            x = arm.pivot[0]
            y = self.shoulder_y
            pb = self.rig.bone(arm.name + '_pad', arm, (x, y, 0), rot=(0, 0, sgn * -0.22))
            r = ru0 + 0.9
            prof = [(y - 1.0, 0.01), (y - 0.8, r * 0.6), (y - 0.3, r * 0.92), (y + 0.4, r), (y + 1.4, r + 0.12)]
            SC.lathe(pb, (x, 0), prof, mat, k=20, rz=0.9, caps=('point', None), name='pad', info={'hem': True}, td=4)
            SC.torus(pb, (x, y + 1.4, 0), r + 0.1, 0.2, dict(mat, pattern=None), k=6, n=18, name='pad_rim')
        return self

    def belt(self, mat, buckle=None):
        y = self.pelvis_y - 0.4
        yb, a, b = self._band(mat, 'belt', y - 0.4, y + 0.45, grow=0.32)
        if buckle:
            SC.crbox(self.hips, (0, y, -b - 0.18), (1.5, 1.1, 0.4), buckle, radius=0.2, name='buckle')
        return self

    # ------------------------------------------------------------------ head accessories
    def horns(self, mat, kind='dragon', length=6.0, spread=0.35, base=1.5):
        top, hh, hw = self.head_top, self.hh, self.hw
        L = max(1.6, float(length) * 0.55)
        r0 = max(0.4, base * 0.28 + 0.12)
        hm = dict(mat)
        for sgn in (-1, 1):
            nm = 'horn_r' if sgn < 0 else 'horn_l'
            if kind == 'dragon':
                x, y, z = sgn * hw * 0.62, top + hh * 0.14, 0.3
                b = self.rig.bone(nm, self.head, (x, y, z))
                pts = SC.bezier((x, y + 0.3, z), (x + sgn * L * 0.25, y - L * 0.5, z + L * 0.15),
                                (x + sgn * L * (0.35 + spread * 0.4), y - L * 0.85, z + L * 0.5),
                                (x + sgn * L * (0.5 + spread * 0.5), y - L * 0.9, z + L * 0.95), n=12)
                SC.sweep(b, pts, lambda t: r0 * (1 - 0.82 * t ** 1.1), None, hm, k=10, caps=('round', 'point'), name='horn',
                         mod=lambda th, t: 1 + 0.08 * np.cos(3 * th) * (1 - t), info={'hem': False}, td=4)
                q = pts[5]
                SC.sweep(b, SC.bezier(q, q + (sgn * 0.5, -0.8, -0.4), q + (sgn * 1.0, -1.1, -0.2), n=5), lambda t: r0 * 0.45 * (1 - 0.8 * t),
                         None, hm, k=6, caps=('round', 'point'), name='tine', info={'hem': False}, td=4)
            elif kind == 'oni':
                x, y, z = sgn * hw * 0.5, top + hh * 0.08, -0.9
                b = self.rig.bone(nm, self.head, (x, y, z), rot=(0.15, 0, sgn * 0.2))
                pts = SC.bezier((x, y + 0.4, z), (x, y - L * 0.6, z - 0.15), (x + sgn * 0.2, y - L, z + 0.35), n=8)
                SC.sweep(b, pts, lambda t: r0 * 1.05 * (1 - 0.85 * t ** 1.3), None, hm, k=10, caps=('round', 'point'), name='horn',
                         info={'hem': False}, td=4)
            elif kind == 'ram':
                x, y, z = sgn * hw * 0.85, top + hh * 0.3, 0.5
                b = self.rig.bone(nm, self.head, (x, y, z))
                ang = np.linspace(0.2, 1.75 * math.pi, 20)
                rad = 0.7 + L * 0.3 * ang / ang[-1]
                pts = np.stack([x + sgn * (0.4 + 0.22 * ang), y - 0.8 - rad * np.sin(ang + 1.2) * 0.9, z + 0.8 - rad * np.cos(ang + 1.2)], 1)
                SC.sweep(b, pts, lambda t: r0 * 1.15 * (1 - 0.7 * t), None, hm, k=10, caps=('round', 'point'), name='horn',
                         mod=lambda th, t: 1 + 0.1 * np.cos(6 * th), info={'hem': False}, td=4)
            elif kind == 'antler':
                x, y, z = sgn * hw * 0.6, top + 0.15, 0.0
                b = self.rig.bone(nm, self.head, (x, y, z))
                main = SC.bezier((x, y + 0.4, z), (x + sgn * L * 0.3, y - L * 0.6, z + 0.4), (x + sgn * L * 0.55, y - L, z + 0.3), n=10)
                SC.sweep(b, main, lambda t: r0 * 0.7 * (1 - 0.6 * t), None, hm, k=8, caps=('round', 'point'), name='antler',
                         info={'hem': False}, td=4)
                for j, f in enumerate((0.4, 0.7)):
                    q = main[int(f * 9)]
                    SC.sweep(b, SC.bezier(q, q + (-sgn * 0.4, -L * 0.25, -0.3), q + (-sgn * 0.2, -L * 0.42, -0.7), n=5),
                             lambda t: r0 * 0.4 * (1 - 0.7 * t), None, hm, k=6, caps=('round', 'point'), name='tine', info={'hem': False}, td=4)
        return self

    def ears(self, kind='elf', mat=None, length=4.0):
        top, hh, hw = self.head_top, self.hh, self.hw
        mat = mat or self.skin
        L = max(1.2, float(length) * 0.55)
        ey = self.face_info()['eye_y'] + hh * 0.05
        for sgn in (-1, 1):
            nm = 'ear_' + ('r' if sgn < 0 else 'l')
            if kind == 'elf':
                b = self.rig.bone(nm, self.head, (sgn * hw, ey, 0.25), anim='sway', ax=2, amp=0.03, speed=0.05, phase=sgn)
                pts = SC.bezier((sgn * (hw - 0.3), ey + 0.1, 0.25), (sgn * (hw + L * 0.5), ey - 0.4, 0.6), (sgn * (hw + L), ey - 1.4, 1.1), n=8)
                SC.sweep(b, pts, lambda t: 0.62 * (1 - 0.85 * t), lambda t: 0.2 * (1 - 0.5 * t), mat, k=8, up=(0, 0, -1),
                         caps=('round', 'point'), name='ear', info={'hem': False}, td=4)
            else:
                b = self.rig.bone(nm, self.head, (sgn * hw * 0.55, top + 0.2, 0.3), rot=(-0.1, 0, sgn * 0.25), anim='sway', ax=2,
                                  amp=0.04, speed=0.11, phase=sgn)
                pts = SC.bezier((sgn * hw * 0.55, top + 0.6, 0.3), (sgn * hw * 0.62, top - L * 0.5, 0.3), (sgn * hw * 0.75, top - L, 0.5), n=8)
                SC.sweep(b, pts, lambda t: 0.95 * (1 - 0.85 * t ** 1.2), 0.3, mat, k=8, up=(0, 0, -1), caps=('round', 'point'),
                         name='ear', info={'hem': False}, td=4)
        return self

    def halo(self, mat, radius=5.0, y=None, tilt=0.18, z=1.6, speed=0.02, name='halo'):
        top = self.head_top
        y = top - 2.0 if y is None else top + (y - top) * 0.8
        ring = self.rig.bone(name, self.head, (0, y, z * 0.8), rot=(tilt, 0, 0), anim='spin', speed=speed)
        halo_ring(ring, (0, y, z * 0.8), radius * 0.8, mat)
        return ring

    def crown(self, band, gems=None, spikes=5, height=1.6, tall=2.2, lift=0.0, name='crown'):
        top = self.head_top - lift * 0.65
        hw, hd = self.hw, self.hd
        if lift:
            b = self.rig.bone(name, self.head, (0, top, 0), anim='float', amp=0.4, speed=0.06)
        else:
            b = self.rig.bone(name, self.head, (0, top, 0))
        y0 = top - 0.25
        R = self.hs * 0.42
        Rz = self.hs * 0.42
        zc = 0.0
        SC.sweep(b, [(0, y0 - 0.7, zc), (0, y0, zc), (0, y0 + 0.3, zc)], [R - 0.1, R, R + 0.08], [Rz - 0.1, Rz, Rz + 0.08], band, k=28,
                 caps=(None, None), name='band', info={'hem': False}, td=4)
        T = max(0.8, float(tall) * 0.6)
        for i in range(spikes):
            if lift:
                ang = 2 * math.pi * i / spikes
            else:
                ang = (i - (spikes - 1) / 2) * (math.pi * 0.85 / max(1, spikes - 1))
            x, zz = R * math.sin(ang), zc - Rz * math.cos(ang)
            t = T + (0.6 if i == spikes // 2 else 0.0)
            out = np.array([math.sin(ang), 0, -math.cos(ang)])
            base = np.array([x, y0 - 0.6, zz])
            SC.sweep(b, [base, base + (out[0] * 0.15, -t * 0.6, out[2] * 0.15), base + (out[0] * 0.25, -t - 0.1, out[2] * 0.25)],
                     lambda tt: 0.3 * (1 - 0.85 * tt), 0.16, band, k=6, up=tuple(out), caps=('round', 'point'), name='spike',
                     info={'hem': False}, td=4)
            if gems and i == spikes // 2:
                gem(b, base + (0, -0.1, 0) + out * 0.15, 0.38, gems)
        return b

# ---------------------------------------------------------------------- shared shapes
def gem(bone, center, r, mat, name='gem', long=1.3):
    c = np.asarray(center, float)
    SC.sweep(bone, [c + (0, -r * long, 0), c, c + (0, r * long, 0)], [0.02, r, 0.02], None, mat, e=1.0, k=8, caps=(None, None),
             name=name, info={'hem': False}, td=4)

def halo_ring(bone, center, radius, mat):
    w = float(mat.get('width', 0.14))
    thick = max(0.2, radius * w * 0.8)
    SC.torus(bone, center, radius, thick, dict(mat), axis='y', k=8, n=max(24, int(radius * 7)), name='halo')
    sp = int(mat.get('spikes', 0) or 0)
    for i in range(sp):
        a = 2 * math.pi * i / sp
        d = np.array([math.cos(a), 0, math.sin(a)])
        base = np.array(center) + d * (radius + thick * 0.6)
        SC.sweep(bone, [base, base + d * (0.8 + 0.3 * (i % 2))], lambda t: thick * 0.9 * (1 - 0.9 * t), None, dict(mat), k=5, up=(0, -1, 0),
                 caps=('round', 'point'), name='halo_spike', info={'hem': False})
    if mat.get('inner'):
        SC.torus(bone, center, radius * float(mat['inner']), thick * 0.55, dict(mat), axis='y', k=6, n=max(20, int(radius * 6)), name='halo_in')

def ring_shape(rig, parent, mat, radius, segments, thick, center, axis='y'):
    SC.torus(parent, center, radius, max(0.3, thick / 2), mat, axis=axis, k=8, n=max(16, segments * 2), name='ring')

def tail(rig, parent, start, mat, segments=5, length=4.0, width=2.6, taper=0.78, droop=0.18, tip_mat=None, name='tail',
         amp=0.16, speed=0.09):
    x, y, z = start
    prev = parent
    w = width * 0.75
    for i in range(segments):
        b = rig.bone(f'{name}{i}', prev, (x, y, z), rot=(droop if i else droop * 0.5, 0, 0), anim='tail', i=i, amp=amp, speed=speed)
        m = tip_mat if (tip_mat and i == segments - 1) else mat
        L = max(1.0, float(length) * 0.95)
        r0, r1 = w / 2, w * taper / 2
        last = i == segments - 1
        SC.sweep(b, [(x, y, z - 0.25), (x, y, z + L * 0.5), (x, y, z + L + (0.0 if last else 0.2))],
                 [r0 * 1.02, (r0 + r1) / 2 * 1.04, r1 if not last else r1 * 0.9], None, m, k=10, up=(0, -1, 0),
                 caps=('round', 'point' if last else 'round'), name='tail', info={'hem': False}, td=4)
        prev = b
        z += L
        w *= taper
    return prev

def wing(rig, parent, side, at, kind, mat, span=12.0, height=10.0, mat2=None, rest=0.45):
    import wings3d
    return wings3d.wing(rig, parent, side, at, kind, mat, span, height, mat2, rest)

def orbiters(rig, parent, center, mat, count=4, radius=10.0, size=1.6, speed=0.035, name='orbit', bob=0.6, shapes=None):
    import trinkets
    return trinkets.orbiters(rig, parent, center, mat, count, radius, size, speed, name, bob, shapes)

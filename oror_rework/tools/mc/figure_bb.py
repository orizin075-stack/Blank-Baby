"""Blockbench-style humanoids (drop-in for figure.Humanoid): every part a crisp cuboid.

Proportions follow the anime player models of Yes Steve Model / Touhou Little Maid packs, a little taller:
an 8x8x8 head with a 16x16 pixel face, about 4.5 heads in all (children 3.5, the large build 5.5), chest,
waist and pelvis as separate boxes so the figure has a waist, elbows and knees. Clothing is layered boxes and
angled plates the way Blockbench modellers build it: skirt and robe panels tilted out round the waist, sleeves,
collars, capes, pauldrons, belts and sashes. Hair is the hat-layer shell with a cut-out fringe plus 3D strands,
side locks, layered back hair, twin tails and ponytails. Accessories that the sculpt toolkit builds (horns, ears,
halos, crowns, tails, wings, orbiters) are turned into chains and rings of boxes by bb.enable().

Bone names, hierarchy and animation tags match figure.Humanoid / RigModel."""
import math
import numpy as np
from paint import M
from colors import hexc, mix, shade, lum
import sculpt as SC
import bb
import figure as FG

# y coordinates (y down, feet at 24): head top / chin, neck (w, h, d), torso top, chest / waist / pelvis (w, h, d),
# arm (w, d), upper / fore / hand lengths, shoulder joint x, thigh / shin (w, d), leg x, foot (w, h, d), bust depth
TEMPLATES = {
    'woman': dict(top=-12.0, neck=(2.5, 1.0, 2.5), chest=(7.0, 5.5, 3.5), waist=(5.5, 2.0, 3.0), pelvis=(6.5, 3.5, 3.5),
                  arm=(2.5, 2.5), upper=5.5, fore=5.5, hand=2.0, sx=4.75, thigh=(3.25, 3.25), shin=(3.0, 3.0), lx=1.65,
                  foot=(3.0, 1.0, 4.0), bust=0.75),
    'youth': dict(top=-13.0, neck=(2.75, 1.0, 2.75), chest=(7.5, 5.5, 3.75), waist=(6.25, 2.0, 3.25), pelvis=(6.75, 3.25, 3.5),
                  arm=(2.75, 2.75), upper=5.5, fore=5.25, hand=2.0, sx=5.125, thigh=(3.4, 3.4), shin=(3.1, 3.1), lx=1.7,
                  foot=(3.1, 1.0, 4.2), bust=0.0),
    'man':   dict(top=-14.0, neck=(3.0, 1.0, 3.0), chest=(8.5, 6.0, 4.25), waist=(7.0, 2.5, 3.75), pelvis=(7.5, 3.5, 4.0),
                  arm=(3.0, 3.0), upper=5.75, fore=5.5, hand=2.25, sx=5.75, thigh=(3.75, 3.75), shin=(3.5, 3.5), lx=1.9,
                  foot=(3.5, 1.0, 4.5), bust=0.0),
    'child': dict(top=-4.0, neck=(2.0, 0.5, 2.0), chest=(6.0, 4.0, 3.0), waist=(5.0, 1.5, 2.75), pelvis=(5.5, 2.5, 3.0),
                  arm=(2.25, 2.25), upper=4.0, fore=3.75, hand=1.75, sx=4.125, thigh=(2.75, 2.75), shin=(2.5, 2.5), lx=1.4,
                  foot=(2.5, 1.0, 3.25), bust=0.0),
    'large': dict(top=-20.0, neck=(3.5, 1.5, 3.5), chest=(12.0, 8.0, 6.0), waist=(10.0, 3.0, 5.5), pelvis=(10.5, 4.5, 5.5),
                  arm=(4.5, 4.5), upper=8.0, fore=7.5, hand=3.0, sx=8.25, thigh=(5.0, 5.0), shin=(4.5, 4.5), lx=2.6,
                  foot=(4.5, 1.0, 6.0), bust=0.0),
}

HS = 8.0


def _is_skin(m):
    return m is None or m.get('type') == 'skin'


def box(bone, x0, y0, z0, sx, sy, sz, mat, **kw):
    return bb.cube(bone, (x0, y0, z0), (sx, sy, sz), mat, **kw)


def cbox(bone, cx, cy, cz, sx, sy, sz, mat, **kw):
    return bb.cube(bone, (cx - sx / 2, cy - sy / 2, cz - sz / 2), (sx, sy, sz), mat, **kw)


class Humanoid(FG.Humanoid):
    def __init__(self, rig, build='woman', skin='#f3dfd7', outfit='#ffffff', accent='#cccccc', hover=0.0, **over):
        bb.enable()
        T = dict(TEMPLATES[build])
        self.T, self.build, self.rig = T, build, rig
        self.sc = SC.Sculpt(rig)
        if lum(skin) > 0.9:
            skin = '#%02x%02x%02x' % mix(skin, '#f2cfc2', 0.35)
        self.skin_color = skin
        self.skin = M('skin', skin)
        self.accent = accent
        self.hair_color = '#3a2a24'
        self.hs = HS
        self.head_top = T['top']
        self.chin_y = self.head_top + HS
        self.hh = HS
        self.hw = self.hd = HS / 2 + 0.5
        self.kh = self.hw / 4.0
        nw, nh, nd = T['neck']
        self.neck_base = self.chin_y + nh
        self.top = self.neck_base
        cw, ch, cd = T['chest']
        ww, wh, wd = T['waist']
        pw, ph, pd = T['pelvis']
        self.chest_y1 = self.top + ch
        self.waist_y = self.chest_y1 + wh * 0.5
        self.waist_y1 = self.chest_y1 + wh
        self.pelvis_top = self.waist_y1
        self.pelvis_y1 = self.pelvis_top + ph
        self.pelvis_y = self.pelvis_top + 0.6
        self.hip_y = self.pelvis_y1 - 0.5
        leg_len = 24 - self.hip_y - T['foot'][1]
        self.knee_y = self.hip_y + leg_len * 0.52
        self.ankle_y = 24 - T['foot'][1]
        aw, ad = T['arm']
        self.shoulder_x = T['sx']
        self.shoulder_y = self.top + aw / 2
        self.elbow_y = self.top + T['upper']
        self.wrist_y = self.elbow_y + T['fore']
        self.hand_y = self.wrist_y + T['hand'] * 0.5
        self.leg_x = T['lx']
        self.front_z = -cd / 2
        self.back_z = cd / 2
        sx = self.shoulder_x
        self.root = rig.bone('root', None, (0, 24, 0), anim='root', hover=hover, speed=0.06)
        self.hips = rig.bone('hips', self.root, (0, self.hip_y, 0))
        self.torso = rig.bone('torso', self.hips, (0, self.waist_y, 0), anim='breath')
        self.head = rig.bone('head', self.torso, (0, self.neck_base, 0), anim='head')
        self.arm_r = rig.bone('arm_r', self.torso, (-sx, self.shoulder_y, 0), rot=(0, 0, 0.1), anim='arm_r')
        self.arm_l = rig.bone('arm_l', self.torso, (sx, self.shoulder_y, 0), rot=(0, 0, -0.1), anim='arm_l')
        self.fore_r = rig.bone('fore_r', self.arm_r, (-sx, self.elbow_y, 0), rot=(-0.14, 0, 0), anim='elbow')
        self.fore_l = rig.bone('fore_l', self.arm_l, (sx, self.elbow_y, 0), rot=(-0.14, 0, 0), anim='elbow')
        self.arm_len = self.wrist_y - self.shoulder_y
        lx = self.leg_x
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
        self.bangs = 'bangs'
        self.rings = [(self.top, cw / 2, cd / 2, 2.0)] * 5

    # ------------------------------------------------------------------ helpers
    def ring_at(self, y, grow=0.0):
        T = self.T
        if y < self.chest_y1:
            w, d = T['chest'][0], T['chest'][2]
        elif y < self.waist_y1:
            w, d = T['waist'][0], T['waist'][2]
        else:
            w, d = T['pelvis'][0], T['pelvis'][2]
        return w / 2 + grow, d / 2 + grow

    def front_at(self, y, x=0.0):
        a, b = self.ring_at(y)
        bust = self.T['bust']
        if bust and self.top + 1.5 <= y <= self.top + 4.2 and abs(x) < a - 0.6:
            b += bust
        return -b

    def face_info(self):
        return dict(eye_y=self.head_top + HS * 0.62)

    # ------------------------------------------------------------------ body
    def body(self, top_mat, bottom_mat=None, waist_mat=None, legs_mat=None, boots_mat=None, arms_mat=None,
             hands_mat=None, sleeve_len=None, bust_mat=None, collar_mat=None, neck='auto', boots_h=None):
        T = self.T
        bottom_mat = bottom_mat or top_mat
        legs_mat = legs_mat or self.skin
        if neck == 'auto':
            neck = 'v' if self.build == 'woman' else ('round' if self.build == 'child' else None)
        self.top_mat, self.bottom_mat = top_mat, bottom_mat
        cw, ch, cd = T['chest']
        ww, wh, wd = T['waist']
        pw, ph, pd = T['pelvis']
        tinfo = {'torso': True, 'neckline': neck if top_mat.get('type') in ('cloth', 'metal') else None, 'skin': self.skin_color,
                 'neck_top': self.top, 'waist': self.waist_y1, 'kimono': top_mat.get('pattern') in ('kimono', 'asanoha'),
                 'chest_w': cw}
        box(self.torso, -cw / 2, self.top, -cd / 2, cw, ch, cd, top_mat, name='chest', info=tinfo)
        if T['bust'] and bust_mat is not False:
            bw = cw - 1.5
            box(self.torso, -bw / 2, self.top + 1.75, -cd / 2 - T['bust'], bw, 2.25, T['bust'], top_mat, name='bust',
                info=dict(tinfo), skip=('back',))
        wm = waist_mat or top_mat
        box(self.torso, -ww / 2, self.chest_y1, -wd / 2, ww, wh, wd, wm, name='waist', info={'hem': False})
        box(self.hips, -pw / 2, self.pelvis_top, -pd / 2, pw, ph, pd, bottom_mat, name='pelvis', info={'hem': False})
        nw, nh, nd = T['neck']
        box(self.head, -nw / 2, self.chin_y - 0.5, -nd / 2, nw, nh + 1.0, nd, self.skin, name='neck', info={'ao': False})
        if collar_mat:
            box(self.torso, -nw / 2 - 0.75, self.top - 0.75, -nd / 2 - 0.75, nw + 1.5, 1.25, nd + 1.5, collar_mat, name='collar',
                faces={'top': None, 'bottom': None})
        # arms
        aw, ad = T['arm']
        arms_mat = arms_mat or top_mat
        hm = hands_mat or self.skin
        total = self.wrist_y - self.top
        sl = total * 0.82 if sleeve_len is None else total * min(1.0, sleeve_len / 9.0)
        self.arms_mat, self.hands_mat, self.sleeve_l = arms_mat, hm, sl
        for arm, fore, sgn in ((self.arm_r, self.fore_r, -1), (self.arm_l, self.fore_l, 1)):
            x = arm.pivot[0]
            up_len = self.elbow_y - self.top
            fo_len = self.wrist_y - self.elbow_y
            if sl <= 0.6 or _is_skin(arms_mat):
                box(arm, x - aw / 2, self.top, -ad / 2, aw, up_len, ad, self.skin if sl <= 0.6 else arms_mat, name='upper')
                box(fore, x - aw / 2, self.elbow_y, -ad / 2, aw, fo_len, ad, self.skin if sl <= 0.6 else arms_mat, name='fore')
            elif sl < up_len:
                box(arm, x - aw / 2, self.top, -ad / 2, aw, sl, ad, arms_mat, name='sleeve', info={'hem': True})
                box(arm, x - aw / 2 + 0.1, self.top + sl, -ad / 2 + 0.1, aw - 0.2, up_len - sl, ad - 0.2, self.skin, name='upper')
                box(fore, x - aw / 2 + 0.1, self.elbow_y, -ad / 2 + 0.1, aw - 0.2, fo_len, ad - 0.2, self.skin, name='fore')
            else:
                box(arm, x - aw / 2, self.top, -ad / 2, aw, up_len, ad, arms_mat, name='upper', info={'hem': False})
                fl = min(fo_len, sl - up_len)
                if fl >= fo_len - 0.3:
                    box(fore, x - aw / 2, self.elbow_y, -ad / 2, aw, fo_len, ad, arms_mat, name='fore', info={'hem': True})
                else:
                    box(fore, x - aw / 2, self.elbow_y, -ad / 2, aw, fl, ad, arms_mat, name='sleeve', info={'hem': True})
                    box(fore, x - aw / 2 + 0.1, self.elbow_y + fl, -ad / 2 + 0.1, aw - 0.2, fo_len - fl, ad - 0.2,
                        hm if not _is_skin(hm) else self.skin, name='fore')
            hw_ = aw - 0.3
            box(fore, x - hw_ / 2, self.wrist_y, -(ad - 0.3) / 2, hw_, T['hand'], ad - 0.3, hm, name='hand', info={'hand': True})
            fore.params['reach'] = round(self.hand_y - self.elbow_y, 3)
            arm.params['reach'] = round(self.hand_y - self.shoulder_y, 3)
        # legs
        tw, td_ = T['thigh']
        sw, sd = T['shin']
        bh = boots_h if boots_h is not None else (4 if boots_mat else 0)
        shin_len = self.ankle_y - self.knee_y
        bh_px = 0 if not boots_mat else max(1.0, min(shin_len + 2, bh * shin_len / 6.0))
        self.legs_mat, self.boots_mat, self.boots_h = legs_mat, boots_mat, bh_px
        fw, fh, fd = T['foot']
        for leg, shin, sgn in ((self.leg_r, self.shin_r, -1), (self.leg_l, self.shin_l, 1)):
            x = leg.pivot[0]
            box(leg, x - tw / 2, self.hip_y, -td_ / 2, tw, self.knee_y - self.hip_y + 0.25, td_, legs_mat, name='thigh', info={'hem': False})
            box(shin, x - sw / 2, self.knee_y, -sd / 2, sw, shin_len, sd, legs_mat, name='shin', info={'hem': False})
            foot_mat = boots_mat or legs_mat
            if boots_mat and bh_px > 0:
                g = 0.25
                box(shin, x - sw / 2 - g, self.ankle_y - bh_px, -sd / 2 - g, sw + 2 * g, bh_px, sd + 2 * g, boots_mat, name='boot',
                    info={'hem': False}, faces={'bottom': None})
                if bh_px > 2.5:
                    box(shin, x - sw / 2 - 0.45, self.ankle_y - bh_px, -sd / 2 - 0.45, sw + 0.9, 0.75, sd + 0.9, dict(boots_mat, pattern=None),
                        name='boot_cuff', faces={'bottom': None})
            box(shin, x - fw / 2, self.ankle_y, -fd + sd / 2, fw, fh, fd, foot_mat, name='foot', info={'hem': False})
        return self

    # ------------------------------------------------------------------ garments
    def jacket(self, mat, rows=None, open_front=True):
        cw, ch, cd = self.T['chest']
        ww, wh, wd = self.T['waist']
        g = 0.3
        H = self.waist_y1 - self.top + 0.6
        m = dict(mat)
        box(self.torso, -cw / 2 - g, self.top - 0.2, -cd / 2 - g, cw + 2 * g, H, cd + 2 * g, m, name='jacket',
            info={'jacket': open_front, 'hem': True}, faces={'top': None, 'bottom': None})
        if open_front:
            for sgn in (-1, 1):
                lw = 1.25
                x0 = sgn * 1.0 - (lw if sgn < 0 else 0)
                box(self.torso, x0, self.top - 0.1, -cd / 2 - g - 0.35, lw, 3.0, 0.3, dict(mat, pattern=None, trim=0), name='lapel',
                    rot=(0, 0, sgn * 0.35), pivot=(sgn * 1.0, self.top, -cd / 2 - g))
        return self

    def kimono_sleeves(self, mat, drop=6.0, width=None):
        aw, ad = self.T['arm']
        for arm, fore, sgn in ((self.arm_r, self.fore_r, -1), (self.arm_l, self.fore_l, 1)):
            x = arm.pivot[0]
            box(arm, x - aw / 2 - 0.35, self.top - 0.2, -ad / 2 - 0.35, aw + 0.7, self.elbow_y - self.top + 0.4, ad + 0.7, dict(mat, trim=0),
                name='sleeve_up', faces={'bottom': None})
            depth = ad + 2.0 + drop * 0.35
            L = self.wrist_y - self.elbow_y + 0.5 + drop * 0.45
            box(fore, x - aw / 2 - 0.5, self.elbow_y - 0.5, -ad / 2 - 0.5, aw + 1.0, L, depth, mat, name='sleeve',
                info={'hem': True}, faces={'top': None})
        return self

    def puff_sleeves(self, mat):
        aw, ad = self.T['arm']
        for arm in (self.arm_r, self.arm_l):
            x = arm.pivot[0]
            box(arm, x - aw / 2 - 0.6, self.top - 0.4, -ad / 2 - 0.6, aw + 1.2, 2.6, ad + 1.2, mat, name='puff', info={'hem': True, 'folds': True})
        return self

    def cuffs(self, mat, at=None):
        aw, ad = self.T['arm']
        for fore in (self.fore_r, self.fore_l):
            x = fore.pivot[0]
            box(fore, x - aw / 2 - 0.3, self.wrist_y - 1.6, -ad / 2 - 0.3, aw + 0.6, 1.6, ad + 0.6, mat, name='cuff')
        return self

    def obi(self, mat, knot=None):
        ww, wh, wd = self.T['waist']
        cw, ch, cd = self.T['chest']
        y0, y1 = self.chest_y1 - 0.75, self.waist_y1 + 0.5
        g = 0.35
        box(self.torso, -ww / 2 - g, y0, -wd / 2 - g, ww + 2 * g, y1 - y0, wd + 2 * g, mat, name='obi', info={'hem': False})
        if knot:
            z = wd / 2 + g
            yk = (y0 + y1) / 2
            k = self.rig.bone('obi_knot', self.torso, (0, yk, z), anim='sway', ax=2, amp=0.04, speed=0.05)
            cbox(k, 0, yk, z + 0.5, 1.5, 1.5, 1.0, knot, name='bow_knot')
            for sgn in (-1, 1):
                box(k, (0.6 if sgn > 0 else -3.1), yk - 1.25, z + 0.25, 2.5, 2.5, 0.75, knot, name='bow', rot=(0, 0, sgn * -0.35),
                    pivot=(sgn * 0.6, yk, z))
                box(k, (0.1 if sgn > 0 else -1.4), yk + 0.5, z + 0.6, 1.3, 4.5, 0.3, knot, name='bow_tail', rot=(0.15, 0, sgn * -0.2),
                    pivot=(sgn * 0.3, yk, z), info={'hem': True})
        return self

    def boots(self, mat, height=5.0):
        sw, sd = self.T['shin']
        H = height * (self.ankle_y - self.knee_y) / 6.0
        for shin in (self.shin_r, self.shin_l):
            x = shin.pivot[0]
            box(shin, x - sw / 2 - 0.3, self.ankle_y - H, -sd / 2 - 0.3, sw + 0.6, H, sd + 0.6, mat, name='boot2', faces={'bottom': None})
        return self

    # ------------------------------------------------------------------ head
    def head_cube(self, face_spec, skin=None):
        spec = dict(face_spec)
        if 'eye_tpl' in spec and 'style' not in spec:
            spec['style'] = spec['eye_tpl']
        sk = (skin or self.skin)['color'] if isinstance(skin, dict) else (skin or spec.get('skin') or self.skin_color)
        if isinstance(skin, dict) and skin.get('type') not in ('skin', None):
            pass
        self.face_spec = spec
        mat = M('head', sk, face=spec, hair=self.hair_color, build=self.build, bangs=self.bangs)
        self.head_mat = mat
        top = self.head_top
        box(self.head, -HS / 2, top, -HS / 2, HS, HS, HS, mat, name='head', info={'head': True, 'ao': False})
        if spec.get('blink', True):
            b = self.rig.bone('blink', self.head, (0, top, -HS / 2 - 0.03), anim='blink', every=float(spec.get('blink_every', 90)))
            bm = M('blink', sk, face=spec, hair=self.hair_color, build=self.build)
            self.blink_mat = bm
            box(b, -HS / 2, top, -HS / 2 - 0.03, HS, HS, 0, bm, name='lids', info={'ao': False, 'lids': True})
        return self

    def _set_hair_color(self, color):
        self.hair_color = color
        for m in (self.head_mat, getattr(self, 'blink_mat', None)):
            if m is not None:
                m['hair'] = color
                m['bangs'] = self.bangs

    def _strand_chain(self, parent, bname, pts, widths, thick, mat, anim_kw, split=0.5, name='strand'):
        """Hair lock as a chain of boxes on two bones (upper / lower) so it sways and bends."""
        P = np.asarray(pts, float)
        P = SC.bezier(*P, n=max(4, len(P) * 2)) if len(P) <= 5 else P
        n = len(P)
        k = min(max(1, int(round(split * (n - 1)))), n - 2)
        up_b = self.rig.bone(bname, parent, tuple(P[0]), anim='hair', **anim_kw)
        lo_b = self.rig.bone(bname + '_tip', up_b, tuple(P[k]), anim='hair', **dict(anim_kw, amp=anim_kw.get('amp', 0.03) * 1.6,
                                                                                    phase=anim_kw.get('phase', 0) + 0.6))
        tt = np.linspace(0, 1, n)
        W = np.interp(tt, np.linspace(0, 1, len(widths)), widths)
        for i in range(n - 1):
            b = up_b if i < k else lo_b
            w = (W[i] + W[i + 1]) / 2
            d = thick * (1 - 0.35 * tt[i])
            bb.beam(b, P[i], P[i + 1], w, d, dict(mat), up=anim_kw.get('up', (0, 0, 1)), name=name, ext=0.4,
                    info={'t_lo': float(tt[i]), 't_hi': float(tt[i + 1])})
        return up_b, lo_b

    def hair(self, color, style='long', length=12.0, tip=None, bangs=None, side_locks=True, twin=False, ponytail=False,
             ahoge=False, volume=0.5, shine=True, ears_open=False, side_len=None, fringe=False):
        man = self.build in ('man', 'large')
        if bangs is None:
            bangs = 'bangs' if self.build in ('woman', 'child', 'youth') else 'short'
        if bangs is False:
            bangs = 'open'
        self.bangs = bangs
        self._set_hair_color(color)
        top = self.head_top
        H = HS / 2 + 0.5
        long_sides = style in ('long', 'very_long', 'wavy', 'bob') or self.build == 'woman'
        back_long = style != 'short' or not man
        shell = M('hair_shell', color, bangs=bangs, long=long_sides, back=back_long, ears_open=ears_open, shine=shine, man=man)
        bb.obox(self.head, (0, top + HS / 2, 0), (HS, HS, HS), np.eye(3), shell, name='hair', inflate=0.5, info={'ao': False},
                skip=('bottom',))
        hm = M('hair', color, tip=tip, shine=shine)
        self.hair_mat = hm
        L = float(length)
        zf = -H - 0.05
        # 3D fringe strands in front of the shell
        if fringe and bangs not in ('open', 'slick', 'none', 'short'):
            fr = self.rig.bone('fringe', self.head, (0, top, zf), anim='hair', amp=0.012, speed=0.09)
            xs = {'parted': (-2.6, -1.4, 1.4, 2.6), 'swept': (-2.7, -1.2, 0.4, 2.0), 'blunt': (-2.5, -0.85, 0.85, 2.5)}.get(
                bangs, (-2.7, -1.0, 1.0, 2.7))
            for i, x0 in enumerate(xs):
                ln = (2.6 + (0.5 if i % 2 == 0 else 0.0)) * (0.85 if man else 1.0)
                if bangs == 'blunt':
                    ln = 3.0
                lean = {'swept': -0.25, 'parted': 0.18 * np.sign(x0)}.get(bangs, 0.12 * np.sign(x0) * (i % 2))
                box(fr, x0 - 0.8, top - 0.4, zf - 0.55, 1.6, ln + 0.4, 0.6, dict(hm, tip=None), name='fringe', rot=(0.12, 0, lean),
                    pivot=(x0, top - 0.4, zf), info={'t_lo': 0.0, 't_hi': 1.0})
        # back hair: layered slabs on two bones each
        if style in ('long', 'very_long', 'wavy'):
            zb = H - 0.3
            L2 = L * 0.95
            n = 3 if style != 'very_long' else 3
            for k, x0 in enumerate((-2.6, 0.0, 2.6)[:n]):
                w = 3.4 if k != 1 else 3.6
                Lk = L2 + (0.8 if k == 1 else -0.4)
                fan = x0 * 0.06
                pts = [(x0 * 0.9, top + 1.2, zb + 0.2), (x0 * 1.0, top + HS * 0.75, zb + 1.0), (x0 * 1.1 + fan * 4, top + 1.2 + Lk * 0.6, zb + 1.3),
                       (x0 * 1.18 + fan * 6, top + 1.2 + Lk, zb + 1.1)]
                self._strand_chain(self.head, f'hair_back{k}', pts, [w, w * 1.05, w * 0.95, w * 0.55], 1.6, hm,
                                   dict(amp=0.02, speed=0.07, phase=0.45 * k, drag=0.35, up=(0, 0, 1)), split=0.45, name='back_hair')
            # a wide slab behind the head joining the strands
            box(self.head, -H + 0.2, top + 1.0, H - 0.6, 2 * H - 0.4, HS + 1.0, 1.2, hm, name='hair_back_base', info={'t_lo': 0.0, 't_hi': 0.3})
            for sgn in (-1, 1):
                pts = [(sgn * (H - 0.2), top + HS * 0.45, 1.6), (sgn * (H + 0.4), top + HS * 0.9, 2.0), (sgn * (H + 0.6), top + 1.0 + L2 * 0.62, 2.2),
                       (sgn * (H + 0.5), top + 1.0 + L2 * 0.85, 2.2)]
                self._strand_chain(self.head, f'hair_side_{"r" if sgn < 0 else "l"}', pts, [2.2, 2.4, 2.0, 1.0], 1.4, hm,
                                   dict(amp=0.025, speed=0.08, phase=sgn * 0.7, drag=0.3, up=(sgn, 0, 0)), split=0.42, name='side_hair')
        elif style == 'bob':
            # chin-length bob: side and back plates with strand columns and a jagged hem, flaring a little
            bob = dict(hm, tip=None)
            y0, y1 = top + 2.0, top + HS + 0.6
            for sgn in (-1, 1):
                box(self.head, sgn * (H + 0.05) - 0.6, y0, -H + 0.6, 1.2, y1 - y0, 2 * H - 0.6, bob, name='bob_side',
                    rot=(0, 0, sgn * -0.07), pivot=(sgn * H, y0, 0), info={'hem': True, 'hem_cut': 'jag', 't_lo': 0.3, 't_hi': 1.0},
                    faces={'top': None})
            box(self.head, -H + 0.2, y0, H - 0.55, 2 * H - 0.4, y1 - y0 + 0.4, 1.2, bob, name='bob_back', rot=(0.07, 0, 0),
                pivot=(0, y0, H), info={'hem': True, 'hem_cut': 'jag', 't_lo': 0.3, 't_hi': 1.0}, faces={'top': None})
        else:
            # short: tufts on the crown
            for k, (x0, z0, rz) in enumerate(((-2.2, -1.0, 0.35), (0.2, -2.0, -0.1), (2.3, -0.6, -0.4), (-1.0, 1.8, 0.25), (1.6, 1.6, -0.3))):
                box(self.head, x0 - 1.1, top - 1.1, z0 - 1.1, 2.2, 1.6, 2.2, dict(hm, tip=None), name='tuft', rot=(0.2 * (1 if z0 > 0 else -1), 0.3 * k, rz),
                    pivot=(x0, top, z0), info={'t_lo': 0.0, 't_hi': 0.5})
        if side_locks and long_sides:
            sl = side_len or min(10.0, max(4.0, L * 0.42))
            for sgn in (-1, 1):
                nm = 'r' if sgn < 0 else 'l'
                b_ = self.rig.bone(f'lock_{nm}', self.head, (sgn * (H - 0.4), top + HS * 0.3, -H + 1.0), anim='hair', amp=0.03, speed=0.09,
                                   phase=sgn)
                box(b_, sgn * (H - 0.4) - 0.8, top + HS * 0.3, -H + 0.35, 1.6, sl, 1.3, dict(hm), name='lock', rot=(0.05, 0, sgn * 0.06),
                    pivot=(sgn * (H - 0.4), top + HS * 0.3, -H + 1.0), info={'t_lo': 0.15, 't_hi': 1.0})
        if twin:
            for sgn in (-1, 1):
                nm = 'r' if sgn < 0 else 'l'
                pts = [(sgn * (H - 0.2), top + HS * 0.2, 1.0), (sgn * (H + 2.4), top + HS * 0.1, 1.4), (sgn * (H + 2.8), top + 2 + L * 0.5, 1.8),
                       (sgn * (H + 2.0), top + 1.5 + L * 0.95, 2.0)]
                up_b, lo_b = self._strand_chain(self.head, f'twin_{nm}', pts, [2.6, 3.2, 2.8, 1.2], 2.4, hm,
                                                dict(amp=0.06, speed=0.08, phase=sgn * 1.3, drag=0.5, up=(0, 0, 1)), split=0.45, name='twin')
                cbox(up_b, sgn * (H + 0.5), top + HS * 0.18, 1.1, 1.6, 1.6, 1.8, M('cloth', self.accent), name='twin_tie')
        if ponytail:
            zb = H
            pts = [(0, top + HS * 0.35, zb - 0.4), (0, top + HS * 0.15, zb + 2.4), (0, top + 1.5 + L * 0.5, zb + 2.8), (0, top + 1.5 + L * 0.92, zb + 1.8)]
            up_b, lo_b = self._strand_chain(self.head, 'ponytail', pts, [2.4, 3.0, 2.6, 1.0], 2.4, hm,
                                            dict(amp=0.07, speed=0.08, phase=0.5, drag=0.7, up=(0, -1, 0)), split=0.45, name='tail')
            cbox(up_b, 0, top + HS * 0.32, zb + 0.6, 1.8, 1.8, 1.4, M('cloth', self.accent), name='tie')
        if ahoge:
            b_ = self.rig.bone('ahoge', self.head, (0, top - 0.5, -0.8), anim='sway', ax=2, amp=0.08, speed=0.1)
            box(b_, -0.35, top - 2.2, -1.2, 0.7, 2.0, 0.5, dict(hm, tip=None), name='ahoge', rot=(0, 0, 0.35), pivot=(0, top - 0.3, -1.0))
            box(b_, 0.3, top - 3.0, -1.2, 1.4, 0.7, 0.5, dict(hm, tip=None), name='ahoge', rot=(0, 0, -0.25), pivot=(0.3, top - 2.6, -1.0))
        return self

    # ------------------------------------------------------------------ skirts and robes
    def flare(self, parent, y0, rx, rz, length, angle, mat, count=None, name='skirt', k=1.0, start=0.0, sweep=1.0,
              shape='trap', folds=None, hem_cut=None, panels=None, inner=0.0, thick=0.5):
        """Panels round an ellipse (rx, rz) at height y0, each a plate tilted out by `angle`, on its own swaying bone."""
        L = float(length)
        spread = L * math.sin(angle)
        npan = panels or (8 if (rx + rz) < 7 else 10)
        if sweep < 1:
            npan = max(2, int(round(npan * sweep)))
        hub = self.rig.bone(name, parent, (0, y0, 0))
        th0 = -math.pi + 2 * math.pi * start
        span = 2 * math.pi * sweep
        full = sweep >= 0.999
        for i in range(npan):
            tm = th0 + span * (i + 0.5) / npan
            px, pz = -rx * math.sin(tm), -rz * math.cos(tm)
            nx, nz = -math.sin(tm) / max(rx, 1e-6), -math.cos(tm) / max(rz, 1e-6)
            nn = math.hypot(nx, nz)
            nx, nz = nx / nn, nz / nn
            yaw = math.atan2(-nx, -nz)
            dth = span / npan
            bx, bz = rx + spread, rz + spread
            ta, tb = tm - dth / 2, tm + dth / 2
            chord_b = math.hypot(bx * (math.sin(tb) - math.sin(ta)), bz * (math.cos(tb) - math.cos(ta)))
            chord_t = math.hypot(rx * (math.sin(tb) - math.sin(ta)), rz * (math.cos(tb) - math.cos(ta)))
            w = max(chord_t, chord_b) + 0.35
            yb = self.rig.bone(f'{name}_y{i}', hub, (px, y0, pz), rot=(0, yaw, 0))
            tb_ = self.rig.bone(f'{name}_p{i}', yb, (px, y0, pz), rot=(-angle, 0, 0), anim='skirt', k=k)
            box(tb_, px - w / 2, y0, pz - thick, w, L, thick, dict(mat), name=name,
                info={'hem': True, 'folds': True, 'hem_cut': hem_cut, 'panel': i})
            if inner:
                box(tb_, px - w / 2, y0 + 0.2, pz + 0.02, w, L - 0.4, 0.0, dict(mat, color='#%02x%02x%02x' % shade(mat['color'], 0.55),
                                                                                 pattern=None, trim=0),
                    name=name + '_in', info={'hem': False, 'inside': True, 'ao': False}, skip=('front',))
        return hub

    def _band(self, mat, name, y0, y1, grow=0.25, parent=None):
        a, b = self.ring_at(y0 + 0.01, grow)
        box(parent or self.hips, -a, y0, -b, 2 * a, y1 - y0, 2 * b, dict(mat, pattern=None, trim=0), name=name, info={'hem': False})
        return y1, a, b

    def skirt(self, mat, length=9.0, flare=1.4, layers=1, top_y=None, tiers=2, name='skirt'):
        y0 = self.pelvis_top - 0.5 if top_y is None else top_y
        ang = min(0.55, 0.16 + flare * 0.12)
        L = max(4.0, length * 0.9)
        yb, a, b = self._band(mat, name + '_band', y0 - 0.25, y0 + 1.25)
        if tiers >= 2:
            inner = dict(mat)
            inner.pop('pattern', None)
            inner['trim'] = 0
            lace = '#%02x%02x%02x' % mix(mat['color'], '#ffffff', 0.55)
            self.flare(self.hips, y0 + 0.8, a - 0.15, b - 0.15, L + 1.0, ang * 0.9, dict(inner, color=lace), name=name + '_under', k=0.7,
                       hem_cut='scallop', thick=0.35)
        hub = self.flare(self.hips, y0 + 0.6, a + 0.05, b + 0.05, L, ang, mat, name=name, inner=0.1)
        self.skirt_r = (y0, a + L * math.sin(ang), b + L * math.sin(ang))
        return hub

    def robe(self, mat, length=None, flare=2.4, split=False):
        y0 = self.pelvis_top - 0.5
        L = (24 - y0 - 0.3) if length is None else length
        ang = math.atan2(flare * 0.6 + 0.6, L)
        yb, a, b = self._band(mat, 'robe_band', y0 - 0.25, y0 + 1.25)
        kw = dict(start=0.07, sweep=0.86) if split else {}
        self.flare(self.hips, y0 + 0.6, a + 0.05, b + 0.05, L - 0.6, ang, dict(mat), name='robe', k=0.5, inner=0.1, panels=10, **kw)
        self.robe_len = L
        self.skirt_r = (y0, a + L * math.sin(ang), b + L * math.sin(ang))
        return self

    def coat_tails(self, mat, length=10.0):
        y0 = self.waist_y1 - 0.2
        a, b = self.ring_at(y0 + 0.5, 0.35)
        self.flare(self.hips, y0, a, b, float(length), 0.16, dict(mat), name='coat', k=0.6, start=0.3, sweep=0.4, panels=4, inner=0.08)
        return self

    def cape(self, mat, length=16.0, width=None, top=None):
        cw, ch, cd = self.T['chest']
        w = float(width or (cw + 2)) * 0.9
        y0 = (top if top is not None else self.top) - 0.2
        z = cd / 2 + 0.35
        L = float(length)
        h1 = L * 0.5
        a = self.rig.bone('cape', self.torso, (0, y0, z), rot=(0.1, 0, 0), anim='cape', amp=0.04, speed=0.06)
        box(a, -w / 2, y0, z, w, h1 + 0.3, 0.5, dict(mat), name='cape', info={'hem': False, 'folds': True})
        b = self.rig.bone('cape_low', a, (0, y0 + h1, z + 0.25), rot=(0.06, 0, 0), anim='cape', amp=0.05, speed=0.06, phase=0.8, drag=0.4)
        box(b, -w / 2 - 0.4, y0 + h1, z, w + 0.8, L - h1, 0.5, dict(mat), name='cape_hem', info={'hem': True, 'folds': True})
        # mantle over the shoulders
        g = 0.45
        box(self.torso, -cw / 2 - g - 0.6, self.top - 0.5, -cd / 2 - g, cw + 2 * g + 1.2, 2.2, cd + 2 * g, dict(mat, pattern=None),
            name='mantle', info={'hem': True}, faces={'bottom': None})
        return a

    def shoulder_pads(self, mat, size=3.2):
        aw, ad = self.T['arm']
        for arm, sgn in ((self.arm_r, -1), (self.arm_l, 1)):
            x = arm.pivot[0]
            y = self.top
            pw = aw + 1.6
            pb = self.rig.bone(arm.name + '_pad', arm, (x, y, 0), rot=(0, 0, sgn * -0.28))
            box(pb, x - pw / 2, y - 0.9, -ad / 2 - 0.8, pw, 1.3, ad + 1.6, mat, name='pad')
            box(pb, x - pw / 2 + sgn * 0.3, y + 0.3, -ad / 2 - 0.65, pw - 0.2, 1.1, ad + 1.3, dict(mat, pattern=None), name='pad2',
                rot=(0, 0, sgn * -0.18), pivot=(x, y + 0.3, 0))
            box(pb, x - pw / 2 + sgn * 0.6, y + 1.3, -ad / 2 - 0.5, pw - 0.4, 0.9, ad + 1.0, dict(mat, pattern=None), name='pad3',
                rot=(0, 0, sgn * -0.3), pivot=(x, y + 1.3, 0))
        return self

    def belt(self, mat, buckle=None):
        y = self.pelvis_top - 0.1
        yb, a, b = self._band(mat, 'belt', y, y + 1.2, grow=0.32)
        if buckle:
            cbox(self.hips, 0, y + 0.6, -b - 0.2, 1.6, 1.4, 0.45, buckle, name='buckle')
        return self

    def breastplate(self, mat, y0=None, y1=None):
        cw, ch, cd = self.T['chest']
        y0 = self.top + 0.4 if y0 is None else y0
        y1 = self.chest_y1 + 0.6 if y1 is None else y1
        bust = self.T['bust']
        box(self.torso, -cw / 2 + 0.2, y0, -cd / 2 - 0.45 - bust, cw - 0.4, y1 - y0, 0.55 + bust, mat, name='breastplate',
            info={'hem': True}, skip=('back',))
        box(self.torso, -cw / 2 - 0.3, y0 + 0.4, -cd / 2 - 0.2, cw + 0.6, y1 - y0 - 0.6, cd * 0.55, dict(mat, pattern=None), name='cuirass_side',
            faces={'front': None, 'top': None, 'bottom': None})
        return self

    def stole(self, mat, length=None):
        L = (self.pelvis_y1 + 3.5 - self.top) if length is None else length
        cw, ch, cd = self.T['chest']
        for sgn in (-1, 1):
            x = sgn * 1.4
            box(self.torso, x - 0.65, self.top - 0.3, -cd / 2 - 0.35 - self.T['bust'], 1.3, L, 0.3, mat, name='stole', info={'hem': True})
            box(self.torso, x - 0.65, self.top - 0.45, -cd / 2 - 0.3, 1.3, 0.3, cd + 0.6, mat, name='stole_over')
        return self

    def fur_collar(self, mat, shoulders=True):
        cw, ch, cd = self.T['chest']
        box(self.torso, -cw / 2 - 0.8, self.top - 1.0, -cd / 2 - 0.8, cw + 1.6, 2.2, cd + 1.6, mat, name='fur_collar', info={'hem': True})
        box(self.torso, -cw / 2 + 0.6, self.top - 1.8, -cd / 2 - 0.4, cw - 1.2, 1.2, cd + 0.8, mat, name='fur_ruff', faces={'bottom': None})
        if shoulders:
            aw, ad = self.T['arm']
            for arm in (self.arm_r, self.arm_l):
                x = arm.pivot[0]
                box(arm, x - aw / 2 - 0.6, self.top - 0.5, -ad / 2 - 0.6, aw + 1.2, 2.0, ad + 1.2, mat, name='fur', info={'hem': True})
        return self

    def hood(self, mat, trim=None, drape=True):
        H = HS / 2 + 1.0
        top = self.head_top
        bb.obox(self.head, (0, top + HS / 2 - 0.2, 0.2), (2 * H, HS + 1.6, 2 * H), np.eye(3), mat, name='hood',
                faces={'front': dict(mat, _hood_front=True), 'bottom': None}, info={'hem': False, 'hood': True})
        if trim:
            box(self.head, -H + 0.2, top - 1.0, -H + 0.1, 2 * H - 0.4, 0.8, 0.5, trim, name='hood_rim')
            for sgn in (-1, 1):
                box(self.head, sgn * (H - 0.6) - 0.4, top - 0.4, -H + 0.1, 0.8, HS + 1.4, 0.5, trim, name='hood_rim')
        if drape:
            cw, ch, cd = self.T['chest']
            box(self.torso, -cw / 2 + 0.2, self.top - 0.3, cd / 2 + 0.2, cw - 0.4, 5.0, 0.5, mat, name='hood_drape', info={'hem': True},
                rot=(0.15, 0, 0), pivot=(0, self.top, cd / 2))
        return self

    def wreath(self, mat, blossoms=()):
        H = HS / 2 + 0.6
        y = self.head_top + 1.0
        b = self.rig.bone('wreath', self.head, (0, y, 0))
        n = 12
        for i in range(n):
            a = 2 * math.pi * i / n
            cx, cz = H * math.cos(a), H * math.sin(a)
            cbox(b, cx, y, cz, 2.0, 1.0, 1.1, mat, name='wreath_leaf', rot=(0.25 * (i % 2) - 0.12, -a + math.pi / 2, 0.2 * ((i + 1) % 2) - 0.1),
                 pivot=(cx, y, cz))
        for i, col in enumerate(blossoms):
            a = -math.pi / 2 + (i - (len(blossoms) - 1) / 2) * 0.55
            cbox(b, H * 1.08 * math.cos(a), y - 0.3, H * 1.08 * math.sin(a), 1.2, 1.2, 1.2, M('gem', col, glow=False), name='bloom',
                 rot=(0.3, 0.6, 0.2))
        return b

    def ears(self, kind='elf', mat=None, length=4.0):
        top = self.head_top
        mat = mat or self.skin
        L = max(1.5, float(length) * 0.7)
        ey = top + HS * 0.55
        H = HS / 2
        for sgn in (-1, 1):
            nm = 'ear_' + ('r' if sgn < 0 else 'l')
            if kind == 'elf':
                b = self.rig.bone(nm, self.head, (sgn * H, ey, 0.5), anim='sway', ax=2, amp=0.03, speed=0.05, phase=sgn)
                box(b, sgn * H + (0 if sgn > 0 else -L), ey - 0.9, 0.1, L, 1.8, 0.7, mat, name='ear', rot=(0, sgn * 0.35, sgn * -0.45),
                    pivot=(sgn * H, ey, 0.5))
                box(b, sgn * H + (L * 0.55 if sgn > 0 else -L * 1.05), ey - 1.4, 0.15, L * 0.5, 0.9, 0.6, mat, name='ear_tip',
                    rot=(0, sgn * 0.35, sgn * -0.75), pivot=(sgn * H, ey, 0.5))
            else:
                b = self.rig.bone(nm, self.head, (sgn * H * 0.55, top + 0.2, 0.3), rot=(-0.1, 0, sgn * 0.25), anim='sway', ax=2,
                                  amp=0.04, speed=0.11, phase=sgn)
                box(b, sgn * H * 0.55 - 1.0, top - L, -0.1, 2.0, L + 0.4, 0.8, mat, name='ear')
        return self

    def halo(self, mat, radius=5.0, y=None, tilt=0.18, z=1.6, speed=0.02, name='halo'):
        top = self.head_top
        y = top - 2.0 if y is None else y
        ring = self.rig.bone(name, self.head, (0, y, z * 0.8), rot=(tilt, 0, 0), anim='spin', speed=speed)
        FG.halo_ring(ring, (0, y, z * 0.8), radius * 0.85, mat)
        return ring


# shared helpers re-exported for recipes
tail = FG.tail
wing = FG.wing
orbiters = FG.orbiters
ring_shape = FG.ring_shape
gem = FG.gem
halo_ring = FG.halo_ring

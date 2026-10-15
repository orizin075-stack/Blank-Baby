"""Anime-proportioned Minecraft characters (8px MC face, slim sculpted body) in the way Touhou Little Maid,
Iron's Spellbooks and Alex's Caves build their people: chest / waist / pelvis instead of one torso box,
jointed arms and legs (elbow, knee), tapered limbs and boot toes, 3D fringe strands and fanned back hair,
flared skirts of tilted panels, sleeves, capes, horns, halos and wings."""
import math
from paint import M, stack, ramp
from colors import hexc, mix, shade

# chest/waist/pelvis (w, h, d); arm: upper (w, h, d) + fore (w, h, d) incl. 2-row hand; leg: thigh + shin
BUILDS = {
    'woman': dict(chest=(6, 5, 3), waist=(5, 2, 3), pelvis=(6, 2, 3), upper=(2, 4, 2), fore=(2, 5, 2),
                  thigh=(3, 5, 3), shin=(2, 6, 2), neck=1, head=8, bust=True),
    'youth': dict(chest=(6, 5, 3), waist=(5, 2, 3), pelvis=(6, 2, 3), upper=(2, 4, 2), fore=(2, 5, 2),
                  thigh=(3, 5, 3), shin=(3, 6, 3), neck=1, head=8),
    'man':   dict(chest=(7, 5, 4), waist=(6, 2, 3), pelvis=(6, 2, 3), upper=(3, 4, 3), fore=(3, 5, 3),
                  thigh=(3, 5, 3), shin=(3, 6, 3), neck=1, head=8),
    'child': dict(chest=(5, 3, 3), waist=(4, 2, 2), pelvis=(5, 2, 3), upper=(2, 3, 2), fore=(2, 4, 2),
                  thigh=(2, 3, 2), shin=(2, 4, 2), neck=0, head=8),
    'large': dict(chest=(11, 7, 6), waist=(9, 3, 5), pelvis=(9, 3, 5), upper=(4, 6, 4), fore=(4, 7, 4),
                  thigh=(4, 7, 4), shin=(4, 7, 4), neck=1, head=8),
}

def _ellipse_perimeter(a, b):
    return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))

class Humanoid:
    def __init__(self, rig, build='woman', skin='#f3dfd7', outfit='#ffffff', accent='#cccccc', hover=0.0, **over):
        B = dict(BUILDS[build])
        for k, v in over.items():          # simple overrides: lh / th / any key above
            B[k] = v
        if 'lh' in over:                   # longer legs: stretch thigh and shin
            extra = over['lh'] - (B['thigh'][1] + B['shin'][1])
            B['thigh'] = (B['thigh'][0], B['thigh'][1] + extra // 2, B['thigh'][2])
            B['shin'] = (B['shin'][0], B['shin'][1] + extra - extra // 2, B['shin'][2])
        self.rig, self.B, self.build = rig, B, build
        from colors import lum
        if lum(skin) > 0.9:
            skin = '#%02x%02x%02x' % mix(skin, '#f2cfc2', 0.35)
        self.skin_color = skin
        self.skin = M('skin', skin)
        self.accent = accent
        self.hair_color = '#3a2a24'
        cw, ch, cd = B['chest']
        ww, wh, wd = B['waist']
        pw, ph, pd = B['pelvis']
        self.lh = B['thigh'][1] + B['shin'][1]
        self.th = ch + wh + ph
        B['tw'], B['td'], B['th'], B['lh'] = cw, cd, self.th, self.lh      # legacy keys used by recipes
        B['aw'], B['ad'] = B['upper'][0], B['upper'][2]
        self.hip_y = 24 - self.lh
        self.top = self.hip_y - self.th
        self.waist_y = self.top + ch
        self.pelvis_y = self.waist_y + wh
        self.head_top = self.top - B['neck'] - B['head']
        self.front_z = -cd / 2                 # chest front plane
        self.back_z = cd / 2
        self.root = rig.bone('root', None, (0, 24, 0), anim='root', hover=hover, speed=0.06)
        self.hips = rig.bone('hips', self.root, (0, self.hip_y, 0))
        self.torso = rig.bone('torso', self.hips, (0, self.pelvis_y, 0), anim='breath')
        self.head = rig.bone('head', self.torso, (0, self.top, 0), anim='head')
        aw = B['upper'][0]
        self.shoulder_x = cw / 2 + aw / 2
        ay = self.top + 1
        self.arm_r = rig.bone('arm_r', self.torso, (-self.shoulder_x, ay, 0), rot=(0, 0, 0.06), anim='arm_r')
        self.arm_l = rig.bone('arm_l', self.torso, (self.shoulder_x, ay, 0), rot=(0, 0, -0.06), anim='arm_l')
        ey = self.top + B['upper'][1]
        self.fore_r = rig.bone('fore_r', self.arm_r, (-self.shoulder_x, ey, 0), rot=(-0.12, 0, 0), anim='elbow')
        self.fore_l = rig.bone('fore_l', self.arm_l, (self.shoulder_x, ey, 0), rot=(-0.12, 0, 0), anim='elbow')
        self.hand_y = ey + B['fore'][1] - 1.5
        self.arm_len = B['upper'][1] + B['fore'][1]
        lx = max(B['thigh'][0], pw / 2) / 2 if build != 'large' else B['thigh'][0] / 2 + 0.5
        lx = B['thigh'][0] / 2 if build != 'large' else lx
        self.leg_r = rig.bone('leg_r', self.hips, (-lx, self.hip_y, 0), anim='leg_r')
        self.leg_l = rig.bone('leg_l', self.hips, (lx, self.hip_y, 0), anim='leg_l')
        ky = self.hip_y + B['thigh'][1]
        self.knee_y = ky
        self.shin_r = rig.bone('shin_r', self.leg_r, (-lx, ky, 0), anim='knee')
        self.shin_l = rig.bone('shin_l', self.leg_l, (lx, ky, 0), anim='knee', side=1.0)
        self.headbox = None
        self.head_mat = None
        self.blink_mat = None

    # ------------------------------------------------------------------ body
    def body(self, top_mat, bottom_mat=None, waist_mat=None, legs_mat=None, boots_mat=None, arms_mat=None,
             hands_mat=None, sleeve_len=None, bust_mat=None, collar_mat=None, neck='auto', boots_h=None):
        B = self.B
        skin = self.skin
        bottom_mat = bottom_mat or top_mat
        legs_mat = legs_mat or skin
        if neck == 'auto':
            neck = 'v' if self.build == 'woman' else ('round' if self.build == 'child' else None)
        top = dict(top_mat)
        if neck and top.get('type') == 'cloth':
            top['neckline'] = neck
            top['skin'] = self.skin_color
        cw, ch, cd = B['chest']
        ww, wh, wd = B['waist']
        pw, ph, pd = B['pelvis']
        self.torso.box((-cw / 2, self.top, -cd / 2), (cw, ch, cd), top, name='chest')
        wm = waist_mat or (top_mat if ch >= 4 else bottom_mat)
        self.torso.box((-ww / 2, self.waist_y, -wd / 2), (ww, wh, wd), dict(wm, neckline=None), name='waist')
        self.hips.box((-pw / 2, self.pelvis_y, -pd / 2), (pw, ph, pd), bottom_mat, name='pelvis')
        if B['neck']:
            self.head.box((-1, self.top - B['neck'], -1), (2, B['neck'], 2), skin, name='neck')
        if B.get('bust') and bust_mat is not False:
            bb = self.rig.bone('bust', self.torso, (0, self.top + 1.5, -cd / 2), rot=(0.35, 0, 0))
            bb.box((-2.5, self.top + 1.5, -cd / 2 - 1), (5, 2, 1), dict(bust_mat or top_mat, neckline=None, pattern=None), name='bust')
        self.body_mats = [(top, ch), (bottom_mat, 99)]
        # arms: sleeve rows then hand rows, split across the elbow
        uw, uh, ud = B['upper']
        fw, fh, fd = B['fore']
        arms_mat = arms_mat or top_mat
        hm = hands_mat or skin
        total = uh + fh
        sl = int(round(total * 0.72 if sleeve_len is None else sleeve_len))
        sl = min(sl, total - 2)
        for arm, fore, sgn in ((self.arm_r, self.fore_r, -1), (self.arm_l, self.fore_l, 1)):
            px = arm.pivot[0]
            up_mat = arms_mat if sl >= uh else stack((arms_mat, sl), (hm, 99)) if sl > 0 else hm
            arm.box((px - uw / 2, self.top, -ud / 2), (uw, uh, ud), up_mat, name='upper')
            rest = sl - uh
            fm = stack((arms_mat, rest), (hm, 99)) if rest > 0 else hm
            fore.box((px - fw / 2, self.top + uh, -fd / 2), (fw, fh, fd), fm, name='fore')
            fore.params['reach'] = round(fh - 1.0, 3)
            arm.params['reach'] = round(total - 1.0 - 1, 3)
        # legs: thigh, shin with boots, toe cap
        tw_, th_, td_ = B['thigh']
        sw, sh, sd = B['shin']
        bh = boots_h if boots_h is not None else (4 if boots_mat else 0)
        bh = min(bh, sh)
        for leg, shin in ((self.leg_r, self.shin_r), (self.leg_l, self.shin_l)):
            px = leg.pivot[0]
            leg.box((px - tw_ / 2, self.hip_y, -td_ / 2), (tw_, th_, td_), legs_mat, name='thigh')
            smat = stack((legs_mat, sh - bh), (boots_mat, 99)) if bh else legs_mat
            shin.box((px - sw / 2, self.knee_y, -sd / 2), (sw, sh, sd), smat, name='shin')
            shin.box((px - sw / 2, 23, -sd / 2 - 1), (sw, 1, 1), boots_mat or legs_mat, name='toe')
        if collar_mat:
            self.torso.box((-cw / 2, self.top, -cd / 2), (cw, 2, cd), collar_mat, grow=0.3, name='collar', faces={'bottom': None})
        return self

    def jacket(self, mat, rows=None, open_front=True):
        """Outer layer over chest and waist (coat, vest)."""
        B = self.B
        cw, ch, cd = B['chest']
        m = dict(mat)
        if open_front:
            m['open_front'] = True
        faces = {'top': None, 'bottom': None, 'front': dict(m, type='coat_front')}
        self.torso.box((-cw / 2, self.top, -cd / 2), (cw, ch, cd), m, grow=0.3, name='jacket', faces=faces)
        ww, wh, wd = B['waist']
        self.torso.box((-cw / 2, self.waist_y, -wd / 2), (cw, wh, wd), m, grow=0.3, name='jacket_low', faces=faces)
        return self

    def kimono_sleeves(self, mat, drop=6.0, width=None):
        """Wide hanging sleeves: a loose tube over the forearm plus a flap that hangs below the wrist."""
        B = self.B
        uw, uh, ud = B['upper']
        fw, fh, fd = B['fore']
        D = int(width or ud + 2)
        for arm, fore in ((self.arm_r, self.fore_r), (self.arm_l, self.fore_l)):
            px = arm.pivot[0]
            arm.box((px - uw / 2, self.top, -ud / 2), (uw, uh, ud), mat, grow=0.35, name='sleeve_up', faces={'top': None})
            fore.box((px - fw / 2 - 0.5, self.top + uh, -D / 2), (fw + 1, fh - 2, D), mat, grow=0.2, name='sleeve', faces={'top': None})
            if drop > 0:
                fore.box((px - fw / 2 - 0.5, self.top + uh + fh - 2, D / 2 - 2), (fw + 1, int(round(drop)), 2), dict(mat, shape='scallop'),
                         grow=0.2, name='flap', faces={'top': None})
        return self

    def puff_sleeves(self, mat):
        B = self.B
        uw, uh, ud = B['upper']
        for arm in (self.arm_r, self.arm_l):
            px = arm.pivot[0]
            arm.box((px - uw / 2, self.top, -ud / 2), (uw, 3, ud), mat, grow=0.7, name='puff')
        return self

    def cuffs(self, mat, at=None):
        B = self.B
        fw, fh, fd = B['fore']
        y = self.top + B['upper'][1] + fh - 3
        for fore in (self.fore_r, self.fore_l):
            px = fore.pivot[0]
            fore.box((px - fw / 2, y, -fd / 2), (fw, 1, fd), mat, grow=0.4, name='cuff')
        return self

    def obi(self, mat, knot=None):
        B = self.B
        ww, wh, wd = B['waist']
        cw, ch, cd = B['chest']
        y = self.waist_y - 1
        self.torso.box((-cw / 2, y, -cd / 2), (cw, wh + 2, cd), mat, grow=0.3, name='obi', faces={'top': None, 'bottom': None})
        if knot:
            z = cd / 2 + 0.3
            k = self.rig.bone('obi_knot', self.torso, (0, y + 1.5, z), anim='sway', ax=2, amp=0.04, speed=0.05)
            k.box((-3, y, z), (6, 3, 2), knot, name='knot')
            k.box((-1.5, y + 3, z + 0.5), (3, 4, 1), dict(knot, shape='point'), name='knot_tail')
        return self

    def boots(self, mat, height=5.0):
        B = self.B
        sw, sh, sd = B['shin']
        for shin in (self.shin_r, self.shin_l):
            px = shin.pivot[0]
            shin.box((px - sw / 2, 24 - height, -sd / 2), (sw, height, sd), mat, grow=0.3, name='boot', faces={'top': mat})
        return self

    # ------------------------------------------------------------------ head
    def head_cube(self, face_spec, skin=None):
        h = self.B['head']
        mat = M('head', (skin or self.skin)['color'] if isinstance(skin, dict) else (skin or self.skin_color),
                face=face_spec, hair=self.hair_color, build=self.build)
        self.head_mat = mat
        self.headbox = self.head.box((-h / 2, self.head_top, -h / 2), (h, h, h), mat, name='head')
        if face_spec.get('blink', True):
            b = self.rig.bone('blink', self.head, (0, self.head_top, -h / 2 - 0.25), anim='blink',
                              every=float(face_spec.get('blink_every', 90)))
            bm = M('blink', mat['color'], face=face_spec, hair=self.hair_color, build=self.build)
            self.blink_mat = bm
            b.box((-h / 2, self.head_top, -h / 2 - 0.25), (h, h, 0), bm, name='lids')
        return self

    def _set_hair_color(self, color):
        self.hair_color = color
        if self.head_mat is not None:
            self.head_mat['hair'] = color
        if getattr(self, 'blink_mat', None) is not None:
            self.blink_mat['hair'] = color

    def hair(self, color, style='long', length=12.0, tip=None, bangs=None, side_locks=True, twin=False, ponytail=False,
             ahoge=False, volume=0.5, shine=True, ears_open=False, side_len=None, fringe=True):
        self._set_hair_color(color)
        h = self.B['head']
        top = self.head_top
        if bangs is None:
            bangs = 'bangs' if self.build in ('woman', 'child', 'youth') else 'short'
        if bangs is False:
            bangs = 'open'
        long_sides = style in ('long', 'very_long', 'wavy', 'bob') or self.build == 'woman'
        shell = M('hair_shell', color, tip=None, bangs=bangs, long=long_sides, shine=shine, ears_open=ears_open,
                  back=style != 'short' or self.build not in ('man', 'large'))
        self.head.box((-h / 2, top, -h / 2), (h, h, h), shell, grow=0.5, name='hair')
        hm = M('hair', color, tip=tip, shine=shine)
        self.hair_mat = hm
        # 3D fringe: a few tilted strands over the forehead (above the eyes)
        if fringe and bangs not in ('open', 'slick', 'none'):
            fr = self.rig.bone('fringe', self.head, (0, top, -h / 2 - 0.5), rot=(-0.18, 0, 0), anim='hair', amp=0.015, speed=0.09)
            for k, (x0, w, L, yaw) in enumerate(((-4.5, 2, 3, 0.18), (-2, 2, 4, 0.0), (0.5, 2, 3, -0.05), (2.5, 2, 3, -0.18))):
                fb = self.rig.bone(f'fringe{k}', fr, (x0 + w / 2, top - 0.5, -h / 2 - 0.6), rot=(0, yaw, 0))
                fb.box((x0, top - 0.5, -h / 2 - 0.6), (w, L, 1), dict(hm, cut='point', t0=0.2, t1=0.8), name='fringe')
        L = length
        back_z = h / 2 + 0.5
        if style in ('long', 'very_long', 'wavy'):
            # fanned back hair: a centre panel and two side panels angled outwards, each with flowing tips
            U = int(min(8, max(4, L * 0.45)))
            lower = max(2, int(round(L - U)))
            for k, (x0, w, yaw) in enumerate(((-2.5, 5, 0.0), (-5, 3, 0.35), (2, 3, -0.35))):
                pz = back_z - 0.25 * k
                cur = self.rig.bone(f'hair_back{k}', self.head, (x0 + w / 2, top + 2, pz), rot=(0.06, yaw, 0), anim='hair', amp=0.02,
                                    speed=0.07, phase=0.4 * k, drag=0.3)
                cur.box((x0, top + 2, pz - 0.5), (w, U, 1), dict(hm, t0=0.0, t1=U / L), name='curtain')
                ln = lower + (1 if k == 0 else -1 if style != 'wavy' else 0)
                b = self.rig.bone(f'hair_tip{k}', cur, (x0 + w / 2, top + 2 + U, pz), anim='hair', amp=0.05,
                                  speed=0.07, phase=0.6 * k, drag=0.5)
                b.box((x0, top + 2 + U, pz - 0.5), (w, max(2, ln), 1),
                      dict(hm, t0=U / L, t1=1.0, cut='tips' if style == 'wavy' or w > 3 else 'point'), name='strand')
        elif style == 'bob':
            self.head.box((-h / 2, top + 5, back_z - 2), (h, 4, 2), dict(hm, cut='tips'), grow=0.5, name='bob',
                          faces={'top': None})
        elif style == 'short' and self.build not in ('man', 'large'):
            self.head.box((-h / 2, top + 6, back_z - 1), (h, 2, 1), dict(hm, cut='tips'), name='nape')
        if side_locks and long_sides:
            sl = side_len or min(10, max(4, L * 0.4))
            for sgn in (-1, 1):
                b = self.rig.bone(f'lock_{"r" if sgn < 0 else "l"}', self.head, (sgn * (h / 2), top + 5, -h / 2 + 1),
                                  rot=(-0.08, 0, sgn * -0.08), anim='hair', amp=0.03, speed=0.09, phase=sgn)
                b.box((sgn * (h / 2) - (1 if sgn > 0 else 0), top + 5, -h / 2 - 0.5), (1, int(round(sl)), 2),
                      dict(hm, cut='point', t0=0.2, t1=0.7), grow=0.25, name='lock')
                b2 = self.rig.bone(f'lock2_{"r" if sgn < 0 else "l"}', self.head, (sgn * (h / 2), top + 5, 1),
                                   rot=(0.1, 0, sgn * -0.12), anim='hair', amp=0.04, speed=0.08, phase=sgn + 1)
                b2.box((sgn * (h / 2) - (1 if sgn > 0 else 0), top + 5, -0.5), (1, int(round(sl * 0.8)), 3),
                       dict(hm, cut='point', t0=0.3, t1=0.8), grow=0.2, name='lock')
        if twin:
            for sgn in (-1, 1):
                b = self.rig.bone(f'twin_{"r" if sgn < 0 else "l"}', self.head, (sgn * (h / 2 + 1), top + 2, 1),
                                  rot=(0.1, 0, sgn * -0.25), anim='hair', amp=0.07, speed=0.08, phase=sgn * 1.3, drag=0.5)
                b.box((sgn * (h / 2 + 1) - 1.5, top + 2, -0.5), (3, int(round(L * 0.8)), 3), dict(hm, cut='point', t0=0.1, t1=1),
                      name='twin')
                b.box((sgn * (h / 2 + 1) - 1, top + 1, -0), (2, 2, 2), M('cloth', self.accent), grow=0.2, name='twin_tie')
        if ponytail:
            b = self.rig.bone('ponytail', self.head, (0, top + 2, back_z + 0.5), rot=(0.25, 0, 0), anim='hair', amp=0.08, speed=0.08,
                              phase=0.5, drag=0.7)
            b.box((-1.5, top + 2, back_z), (3, int(round(L * 0.5)), 3), dict(hm, t0=0.1, t1=0.55), name='tail')
            b2 = self.rig.bone('ponytail2', b, (0, top + 2 + int(round(L * 0.5)), back_z + 1), rot=(-0.2, 0, 0), anim='hair', amp=0.08,
                               speed=0.08, phase=1.0, drag=0.7)
            b2.box((-1, top + 2 + int(round(L * 0.5)), back_z + 0.5), (2, int(round(L * 0.45)), 2), dict(hm, cut='point', t0=0.55, t1=1),
                   name='tail2')
            b.box((-1, top + 1, back_z - 0.5), (2, 2, 2), M('cloth', self.accent), name='tie')
        if ahoge:
            b = self.rig.bone('ahoge', self.head, (0, top - 0.5, -1), rot=(-0.35, 0, 0.2), anim='sway', ax=2, amp=0.08, speed=0.1)
            b.box((0, top - 3.5, -1), (0, 3, 2), dict(hm, cut='point'), name='ahoge')
        return self

    # ------------------------------------------------------------------ skirts and robes
    def flare(self, parent, y0, rx, rz, length, angle, mat, count=None, name='skirt', k=1.0, start=0.0, sweep=1.0,
              shape='trap'):
        """Ring of cut-out panels around an ellipse, each tilted outwards (bell skirt / robe / tassets)."""
        L = int(round(length))
        rxb, rzb = rx + L * math.sin(angle), rz + L * math.sin(angle)
        per = _ellipse_perimeter(rxb, rzb) * sweep
        if count is None:
            count = max(6, int(round(per / 3.0)))
        w = int(math.ceil(per / count)) + 1
        hub = self.rig.bone(name, parent, (0, y0, 0))
        for i in range(count):
            a = 2 * math.pi * (start + sweep * (i + 0.5) / count) if sweep < 1 else 2 * math.pi * i / count
            px, pz = rx * math.sin(a), -rz * math.cos(a)
            nx, nz = math.sin(a) / rx, -math.cos(a) / rz
            yaw = math.atan2(-nx, -nz)
            yb = self.rig.bone(f'{name}_y{i}', hub, (px, y0, pz), rot=(0, yaw, 0))
            tb = self.rig.bone(f'{name}_p{i}', yb, (px, y0, pz), rot=(-angle, 0, 0), anim='skirt', k=k)
            tb.box((px - w / 2, y0, pz), (w, L, 0), dict(mat, shape=shape), name='panel')
        return hub

    def _band(self, mat, name):
        B = self.B
        pw, ph, pd = B['pelvis']
        self.hips.box((-pw / 2, self.pelvis_y, -pd / 2), (pw, ph, pd), mat, grow=0.5, name=name, faces={'top': None, 'bottom': None})

    def skirt(self, mat, length=9.0, flare=1.4, layers=1, top_y=None, tiers=2, name='skirt'):
        B = self.B
        pw, ph, pd = B['pelvis']
        y0 = top_y if top_y is not None else self.pelvis_y
        ang = min(0.6, 0.16 + flare * 0.13)
        L = max(4, int(round(length * 0.72)))
        self._band(mat, f'{name}_band')
        hub = self.flare(self.hips, y0 + 1, pw / 2 + 0.4, pd / 2 + 0.5, L, ang, mat, name=name)
        if tiers >= 2:
            inner = dict(mat)
            inner.pop('pattern', None)
            inner['trim'] = mat.get('trim', 0) or 2
            self.flare(self.hips, y0 + 1, pw / 2 + 0.2, pd / 2 + 0.3, L + 1, ang * 0.72, dict(inner, color=shade(mat['color'], 0.85)),
                       name=name + '_under', k=0.7, shape='scallop')
        return hub

    def robe(self, mat, length=None, flare=2.4, split=False):
        B = self.B
        pw, ph, pd = B['pelvis']
        y0 = self.pelvis_y
        L = int(round((24 - y0 - 0.5) if length is None else length))
        ang = math.atan2(flare * 0.9, L)
        self._band(mat, 'robe_band')
        kw = dict(start=0.08, sweep=0.84) if split else {}
        self.flare(self.hips, y0 + 1, pw / 2 + 0.4, pd / 2 + 0.5, L, ang, dict(mat), name='robe', k=0.5, **kw)
        return self

    def coat_tails(self, mat, length=10.0):
        B = self.B
        pw, ph, pd = B['pelvis']
        self.flare(self.hips, self.pelvis_y, pw / 2 + 0.6, pd / 2 + 0.7, int(round(length)), 0.2, dict(mat), name='coat',
                   k=0.6, start=0.2, sweep=0.6, shape='point')
        return self

    def cape(self, mat, length=16.0, width=None, top=None):
        B = self.B
        cw, ch, cd = B['chest']
        w = int(round(width or cw + 3))
        y0 = top if top is not None else self.top
        z = cd / 2 + 0.5
        L = int(round(length))
        a = self.rig.bone('cape', self.torso, (0, y0, z), rot=(0.1, 0, 0), anim='cape', amp=0.04, speed=0.06)
        h1 = L // 2
        a.box((-w / 2, y0, z), (w, h1, 1), dict(mat, hem_shadow=False), name='cape')
        b = self.rig.bone('cape_low', a, (0, y0 + h1, z), rot=(0.06, 0, 0), anim='cape', amp=0.05, speed=0.06, phase=0.8, drag=0.4)
        b.box((-w / 2 - 1, y0 + h1, z), (w + 2, L - h1, 1), dict(mat, shape='scallop'), name='cape_hem')
        self.torso.box((-cw / 2, self.top, -cd / 2), (cw, 1, cd), dict(mat, trim=0), grow=0.6, name='mantle', faces={'bottom': None})
        return a

    def shoulder_pads(self, mat, size=3.2):
        B = self.B
        uw, uh, ud = B['upper']
        for arm, sgn in ((self.arm_r, -1), (self.arm_l, 1)):
            px = arm.pivot[0]
            pb = self.rig.bone(arm.name + '_pad', arm, (px, self.top, 0), rot=(0, 0, sgn * -0.25))
            pb.box((px - uw / 2 - 1, self.top - 1, -ud / 2 - 1), (uw + 2, 2, ud + 2), mat, grow=0.1, name='pad')
        return self

    def belt(self, mat, buckle=None):
        B = self.B
        pw, ph, pd = B['pelvis']
        y = self.pelvis_y
        self.hips.box((-pw / 2, y, -pd / 2), (pw, 1, pd), mat, grow=0.6, name='belt')
        if buckle:
            self.hips.box((-1, y - 0.5, -pd / 2 - 0.7), (2, 2, 0), buckle, name='buckle')
        return self

    # ------------------------------------------------------------------ head accessories
    def horns(self, mat, kind='dragon', length=6.0, spread=0.35, base=1.5):
        h = self.B['head']
        top = self.head_top
        b0 = max(1, int(round(base)))
        L = max(2, int(round(length)))
        for sgn in (-1, 1):
            nm = 'horn_r' if sgn < 0 else 'horn_l'
            if kind == 'dragon':
                x, y, z = sgn * 2.5, top + 1, 0.5
                segs = 3
                prev = self.head
                sl = max(1, L // segs)
                bw = b0
                yy = y
                for s in range(segs):
                    rot = (-0.55 if s == 0 else -0.35, 0, sgn * (spread if s == 0 else -0.1))
                    bn = self.rig.bone(f'{nm}{s}', prev, (x, yy, z), rot=rot)
                    bn.box((x - bw / 2, yy - sl, z - bw / 2), (bw, sl, bw), dict(mat, t0=s / segs, t1=(s + 1) / segs, flip=True), name='h')
                    prev = bn
                    yy -= sl
                    bw = max(1, bw - 1) if s >= 1 else bw
            elif kind == 'oni':
                bn = self.rig.bone(nm, self.head, (sgn * 2, top, -2), rot=(0.15, 0, sgn * 0.2))
                bn.box((sgn * 2 - b0 / 2, top - L, -2 - b0 / 2), (b0, L, b0), dict(mat, flip=True), name='h')
            elif kind == 'ram':
                bn = self.rig.bone(nm, self.head, (sgn * 4, top + 2, 0.5), rot=(0, 0, sgn * 1.25))
                bn.box((sgn * 4 - b0 / 2, top + 2 - L * 0.6, 0.5 - b0 / 2), (b0, int(L * 0.6), b0), dict(mat, flip=True, t0=0, t1=0.6), name='h')
                b2 = self.rig.bone(nm + '2', bn, (sgn * 4, top + 2 - int(L * 0.6), 0.5), rot=(0, 0, sgn * 1.4))
                b2.box((sgn * 4 - 0.5, top + 2 - int(L * 0.6) - int(L * 0.4), 0), (1, int(L * 0.4), 1), dict(mat, flip=True, t0=0.6, t1=1), name='h2')
            elif kind == 'antler':
                bn = self.rig.bone(nm, self.head, (sgn * 2.5, top, 0), rot=(-0.2, 0, sgn * 0.5))
                bn.box((sgn * 2.5 - 0.5, top - L, -0.5), (1, L, 1), dict(mat, flip=True), name='a')
                for k in range(2):
                    yy = top - L * (0.45 + 0.3 * k)
                    bb = self.rig.bone(f'{nm}_t{k}', bn, (sgn * 2.5, yy, 0), rot=(0, 0, sgn * 0.9))
                    bb.box((sgn * 2.5 - 0.5, yy - int(L * 0.35), -0.5), (1, int(L * 0.35), 1), dict(mat, flip=True, t0=0.5, t1=1), name='a2')
        return self

    def ears(self, kind='elf', mat=None, length=4.0):
        h = self.B['head']
        top = self.head_top
        mat = mat or self.skin
        L = max(2, int(round(length)))
        for sgn in (-1, 1):
            if kind == 'elf':
                b = self.rig.bone('ear_' + ('r' if sgn < 0 else 'l'), self.head, (sgn * h / 2, top + 5, 0),
                                  rot=(0.3, sgn * -0.3, sgn * 0.45))
                b.box((sgn * h / 2 + (0 if sgn > 0 else -L), top + 4, -0.5), (L, 2, 1), dict(mat, shape=None), name='ear')
            else:
                b = self.rig.bone('ear_' + ('r' if sgn < 0 else 'l'), self.head, (sgn * 2.5, top, 0.5), rot=(-0.1, 0, sgn * 0.25),
                                  anim='sway', ax=2, amp=0.04, speed=0.11, phase=sgn)
                b.box((sgn * 2.5 - 1.5, top - L, 0), (3, L, 1), mat, name='ear')
        return self

    def halo(self, mat, radius=5.0, y=None, tilt=0.18, z=1.6, speed=0.02, name='halo'):
        top = self.head_top
        y = top - 2.5 if y is None else y
        r = int(round(radius))
        ring = self.rig.bone(name, self.head, (0, y, z), rot=(tilt, 0, 0), anim='spin', speed=speed)
        ring.box((-r, y, z - r), (2 * r, 0, 2 * r), mat, name='ring')
        return ring

    def crown(self, band, gems=None, spikes=5, height=1.6, tall=2.2, lift=0.0, name='crown'):
        """Slim circlet sitting on the hair, with thin points rising from the front half.
        lift > 0 makes it float above the head (bobbing)."""
        h = self.B['head']
        top = self.head_top - lift
        if lift:
            b = self.rig.bone(name, self.head, (0, top, 0), anim='float', amp=0.5, speed=0.06)
        else:
            b = self.rig.bone(name, self.head, (0, top, 0))
        b.box((-3, top - 1, -3), (6, 1, 6), band, grow=0.0, name='band', faces={'top': None, 'bottom': None})
        T = max(1, int(round(tall)))
        xs = [-2.5 + i * 5.0 / max(1, spikes - 1) for i in range(spikes)]
        for i, x in enumerate(xs):
            t = T + (1 if i == spikes // 2 else 0)
            b.box((x - 0.5, top - 1 - t, -3.25), (1, t, 0), band, name='spike')
        if gems:
            b.box((-0.5, top - 1, -3.5), (1, 1, 0), gems, name='gem')
        return b

# ---------------------------------------------------------------------- shared shapes
def ring_shape(rig, parent, mat, radius, segments, thick, center, axis='y'):
    cx, cy, cz = center
    seg_len = max(1, int(round(2 * radius * math.tan(math.pi / segments) + 0.6)))
    t = max(1, int(round(thick)))
    for i in range(segments):
        a = 2 * math.pi * i / segments
        rot = (0, a, 0) if axis == 'y' else ((a, 0, 0) if axis == 'x' else (0, 0, a))
        b = rig.bone(f'{parent.name}_s{i}', parent, (cx, cy, cz), rot=rot)
        if axis == 'y':
            b.box((cx - seg_len / 2, cy - t / 2, cz + radius - t / 2), (seg_len, t, t), mat, name='seg')
        elif axis == 'x':
            b.box((cx - t / 2, cy + radius - t / 2, cz - seg_len / 2), (t, t, seg_len), mat, name='seg')
        else:
            b.box((cx - seg_len / 2, cy + radius - t / 2, cz - t / 2), (seg_len, t, t), mat, name='seg')

def tail(rig, parent, start, mat, segments=5, length=4.0, width=2.6, taper=0.78, droop=0.18, tip_mat=None, name='tail',
         amp=0.16, speed=0.09):
    x, y, z = start
    prev = parent
    w = width
    for i in range(segments):
        b = rig.bone(f'{name}{i}', prev, (x, y, z), rot=(droop if i else droop * 0.5, 0, 0), anim='tail', i=i, amp=amp,
                     speed=speed)
        m = tip_mat if (tip_mat and i == segments - 1) else mat
        wi = max(1, int(round(w)))
        L = max(1, int(round(length)))
        b.box((x - wi / 2, y - wi / 2, z), (wi, wi, L), m, name='seg')
        prev = b
        z += L
        w *= taper
    return prev

def wing(rig, parent, side, at, kind, mat, span=12.0, height=10.0, mat2=None, rest=0.45):
    """side -1 = right (model -X), +1 = left. Feather wings are three layered cut-out planes
    (coverts, secondaries, primaries) on a two-bone arm; membrane wings have bone fingers."""
    x, y, z = at
    nm = 'wing_r' if side < 0 else 'wing_l'
    root = rig.bone(nm, parent, (x, y, z), rot=(0.15, side * -rest, side * -0.2), anim=nm, amp=0.18, speed=0.12)
    S = int(round(span))
    H = int(round(height))
    inner = S // 2
    outer = S - inner
    def plane(bone, x0, y0, w, hh, m, name, dz=0.0):
        bone.box((x0 if side > 0 else x0 - w, y0, z + dz), (w, hh, 0), m, name=name)
    if kind == 'feather':
        fm = dict(mat2 or mat)
        fm['type'] = 'feather'
        fm['reverse'] = side < 0
        cov = dict(fm, coverts=True)
        root.box((x if side > 0 else x - inner, y - 1, z - 0.5), (inner, 2, 1), dict(mat, type='feather', coverts=True), name='arm')
        plane(root, x, y, inner, int(H * 0.45), cov, 'coverts', 0.25)
        plane(root, x, y + 1, inner, int(H * 0.8), dict(fm, length_var=2), 'secondaries', 0.5)
        tip = rig.bone(nm + '_tip', root, (x + side * inner, y, z), rot=(0, side * -0.35, side * -0.3), anim='sway', ax=1,
                       amp=0.06, speed=0.12)
        tip.box((x + side * inner if side > 0 else x + side * inner - outer, y - 1, z - 0.5), (outer, 2, 1), dict(mat, type='feather', coverts=True), name='hand')
        plane(tip, x + side * inner, y, outer, int(H * 0.4), cov, 'coverts2', 0.25)
        plane(tip, x + side * inner, y + 1, outer, H, dict(fm, length_var=4, primaries=True), 'primaries', 0.5)
    elif kind == 'membrane':
        bm = mat2 or mat
        root.box((x if side > 0 else x - S, y - 1, z - 0.5), (S, 1, 1), bm, name='bone')
        mm = dict(mat)
        mm['type'] = 'membrane'
        plane(root, x, y, S, H, mm, 'membrane', 0.0)
        for k in range(1, 4):
            fx = x + side * S * k / 4.0
            f = rig.bone(f'{nm}_finger{k}', root, (fx, y, z), rot=(0, 0, side * (0.25 * k - 0.6)))
            f.box((fx - 0.5, y, z - 0.5), (1, int(H * (0.7 + 0.1 * k)), 1), bm, name='finger')
    elif kind == 'mech':
        for k in range(3):
            root.box((x + side * k * 3 + (0 if side > 0 else -3), y - 1 + k, z + 0.25 * k), (3, int(H * (1 - 0.15 * k)), 1),
                     mat if k % 2 == 0 else (mat2 or mat), name='plate')
    elif kind == 'light':
        for k in range(5):
            fx = x + side * S * (0.1 + 0.2 * k)
            root.box((fx + (0 if side > 0 else -1), y - 2 + k, z + 0.25 * k), (1, int(H * (1 - 0.13 * k)), 0), mat, name='blade')
    return root

def orbiters(rig, parent, center, mat, count=4, radius=10.0, size=1.6, speed=0.035, name='orbit', bob=0.6, shapes=None):
    cx, cy, cz = center
    hub = rig.bone(name, parent, (cx, cy, cz), anim='spin', speed=speed)
    for i in range(count):
        a = 2 * math.pi * i / count
        px, pz = cx + math.cos(a) * radius, cz + math.sin(a) * radius
        b = rig.bone(f'{name}_{i}', hub, (px, cy, pz), anim='float', amp=bob, speed=0.08, phase=i * 1.7)
        s = shapes[i % len(shapes)] if shapes else (size, size, size)
        s = tuple(max(0, round(v)) if v >= 0.5 else 0 for v in s)
        s = tuple(v if v > 0 or j == 2 else 1 for j, v in enumerate(s))
        b.cbox((px, cy, pz), s, mat if not isinstance(mat, list) else mat[i % len(mat)], name='orb')
    return hub

def katana(bone, at, blade, guard, hilt, length=14.0):
    x, y, z = at
    bone.box((x - 0.5, y, z - 0.5), (1, 4, 1), hilt, name='hilt')
    bone.box((x - 1, y + 4, z - 1), (2, 1, 2), guard, name='guard')
    bone.box((x - 0.5, y + 5, z - 0.5), (1, int(round(length)), 1), blade, name='blade')

def staff(bone, at, shaft, head, length=22.0, orb=None):
    x, y, z = at
    L = int(round(length))
    bone.box((x - 0.5, y - L * 0.45, z - 0.5), (1, L, 1), shaft, name='shaft')
    if orb:
        bone.cbox((x, y - L * 0.45 - 1.5, z), (2, 2, 2), orb, name='orb', grow=0.25)
        bone.cbox((x, y - L * 0.45 - 1.5, z), (4, 1, 0), head, name='prong')
        bone.cbox((x, y - L * 0.45 - 1.5, z), (0, 4, 4), head, name='prong2')

"""Minecraft-proportioned characters (player-model base: 8px head, 8x12x4 body, 12px limbs)
with skin-style overlay layers and extra cut-out parts (skirts, hair strands, sleeves, capes,
horns, halos, wings, tails), in the way Touhou Little Maid / Iron's Spellbooks build mobs."""
import math
from paint import M, stack, ramp
from colors import hexc, mix, shade

BUILDS = {
    #         torso w,h,d   arm w,d   leg w,d  leg h  head
    'woman': dict(tw=8, th=12, td=4, aw=3, ad=4, lw=4, ld=4, lh=12, head=8),
    'man':   dict(tw=8, th=12, td=4, aw=4, ad=4, lw=4, ld=4, lh=12, head=8),
    'child': dict(tw=6, th=9, td=3, aw=2, ad=3, lw=3, ld=3, lh=9, head=8),
    'large': dict(tw=10, th=14, td=6, aw=5, ad=5, lw=5, ld=5, lh=13, head=8),
    'youth': dict(tw=8, th=11, td=4, aw=3, ad=4, lw=4, ld=4, lh=11, head=8),
}

def _ellipse_perimeter(a, b):
    return math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))

class Humanoid:
    def __init__(self, rig, build='woman', skin='#f3dfd7', outfit='#ffffff', accent='#cccccc', hover=0.0, **over):
        B = dict(BUILDS[build])
        B.update(over)
        self.rig, self.B, self.build = rig, B, build
        from colors import lum
        if lum(skin) > 0.9:
            skin = '#%02x%02x%02x' % mix(skin, '#f2cfc2', 0.35)
        self.skin_color = skin
        self.skin = M('skin', skin)
        self.accent = accent
        self.hair_color = '#3a2a24'
        lh, th = B['lh'], B['th']
        self.hip_y = 24 - lh                  # top of the legs / bottom of the torso
        self.top = self.hip_y - th            # shoulders / neck
        self.head_top = self.top - B['head']
        self.root = rig.bone('root', None, (0, 24, 0), anim='root', hover=hover, speed=0.06)
        self.hips = rig.bone('hips', self.root, (0, self.hip_y, 0))
        self.torso = rig.bone('torso', self.hips, (0, self.hip_y, 0), anim='breath')
        self.head = rig.bone('head', self.torso, (0, self.top, 0), anim='head')
        sx = B['tw'] / 2 + B['aw'] / 2 + (0.0 if B['aw'] % 2 == 0 else 0.0)
        self.shoulder_x = B['tw'] / 2 + B['aw'] / 2
        ay = self.top + 2 if build != 'child' else self.top + 1.5
        self.arm_r = rig.bone('arm_r', self.torso, (-self.shoulder_x, ay, 0), anim='arm_r')
        self.arm_l = rig.bone('arm_l', self.torso, (self.shoulder_x, ay, 0), anim='arm_l')
        lx = B['lw'] / 2 if build != 'large' else B['lw'] / 2 + 0.5
        self.leg_r = rig.bone('leg_r', self.hips, (-lx, self.hip_y, 0), anim='leg_r')
        self.leg_l = rig.bone('leg_l', self.hips, (lx, self.hip_y, 0), anim='leg_l')
        self.headbox = None
        self.head_mat = None

    # ------------------------------------------------------------------ body
    def body(self, top_mat, bottom_mat=None, waist_mat=None, legs_mat=None, boots_mat=None, arms_mat=None,
             hands_mat=None, sleeve_len=None, bust_mat=None, collar_mat=None, neck='auto', boots_h=None):
        B = self.B
        tw, th, td = B['tw'], B['th'], B['td']
        skin = self.skin
        bottom_mat = bottom_mat or top_mat
        legs_mat = legs_mat or skin
        if neck == 'auto':
            neck = 'v' if self.build == 'woman' else ('round' if self.build == 'child' else None)
        top = dict(top_mat)
        if neck and top.get('type') == 'cloth':
            top['neckline'] = neck
            top['skin'] = self.skin_color
        chest_rows = int(round(th * (0.62 if self.build != 'child' else 0.6)))
        layers = [(top, chest_rows)]
        if waist_mat is not None and waist_mat is not top_mat:
            layers.append((waist_mat, 2))
        layers.append((bottom_mat, 99))
        self.torso.box((-tw / 2, self.top, -td / 2), (tw, th, td), stack(*layers), name='body')
        self.body_mats = layers
        # arms: sleeve then hand
        aw, ad = B['aw'], B['ad']
        arm_len = th
        sl = int(round(arm_len * 0.75 if sleeve_len is None else sleeve_len))
        arms_mat = arms_mat or top_mat
        hm = hands_mat or skin
        for arm, sgn in ((self.arm_r, -1), (self.arm_l, 1)):
            px, py = arm.pivot[0], arm.pivot[1]
            y0 = self.top
            arm.box((px - aw / 2, y0, -ad / 2), (aw, arm_len, ad), stack((arms_mat, sl), (hm, 99)), name='arm')
            arm.params['reach'] = round(arm_len - (py - y0) - 1.0, 3)
        self.arm_len = arm_len
        # legs: trousers/legs then boots
        lw, ld, lh = B['lw'], B['ld'], B['lh']
        bh = boots_h if boots_h is not None else (4 if boots_mat else 0)
        for leg in (self.leg_r, self.leg_l):
            px = leg.pivot[0]
            mat = stack((legs_mat, lh - bh), (boots_mat, 99)) if bh else legs_mat
            leg.box((px - lw / 2, self.hip_y, -ld / 2), (lw, lh, ld), mat, name='leg')
        if collar_mat:
            self.torso.box((-tw / 2, self.top, -td / 2), (tw, 2, td), collar_mat, grow=0.3, name='collar',
                           faces={'bottom': None})
        return self

    def jacket(self, mat, rows=None, open_front=True):
        """Skin-style outer layer on the torso (coat, vest)."""
        B = self.B
        tw, th, td = B['tw'], B['th'], B['td']
        m = dict(mat)
        if open_front:
            m['open_front'] = True
        self.torso.box((-tw / 2, self.top, -td / 2), (tw, rows or th, td), m, grow=0.25, name='jacket',
                       faces={'top': None, 'bottom': None, 'front': dict(m, type='coat_front')})
        return self

    def kimono_sleeves(self, mat, drop=6.0, width=None):
        """Wide hanging sleeves: a loose tube over the upper arm plus a flap that hangs behind the wrist."""
        B = self.B
        aw, ad = B['aw'], B['ad']
        D = int(width or ad + 2)
        for arm, sgn in ((self.arm_r, -1), (self.arm_l, 1)):
            px = arm.pivot[0]
            arm.box((px - aw / 2, self.top, -D / 2), (aw, 9, D), mat, grow=0.3, name='sleeve', faces={'top': None})
            if drop > 0:
                arm.box((px - aw / 2, self.top + 9, D / 2 - 2), (aw, int(round(drop)), 2), dict(mat, shape='scallop'), grow=0.3,
                        name='flap', faces={'top': None})
        return self

    def puff_sleeves(self, mat):
        B = self.B
        for arm in (self.arm_r, self.arm_l):
            px = arm.pivot[0]
            arm.box((px - B['aw'] / 2, self.top, -B['ad'] / 2), (B['aw'], 4, B['ad']), mat, grow=0.5, name='puff')
        return self

    def cuffs(self, mat, at=None):
        B = self.B
        y = self.top + (at if at is not None else 8)
        for arm in (self.arm_r, self.arm_l):
            px = arm.pivot[0]
            arm.box((px - B['aw'] / 2, y, -B['ad'] / 2), (B['aw'], 1, B['ad']), mat, grow=0.35, name='cuff')
        return self

    def obi(self, mat, knot=None):
        B = self.B
        y = self.top + int(round(B['th'] * 0.55))
        self.torso.box((-B['tw'] / 2, y, -B['td'] / 2), (B['tw'], 3, B['td']), mat, grow=0.4, name='obi')
        if knot:
            z = B['td'] / 2 + 0.4
            k = self.rig.bone('obi_knot', self.torso, (0, y + 1.5, z), anim='sway', ax=2, amp=0.04, speed=0.05)
            k.box((-3, y, z), (6, 3, 2), knot, name='knot')
            k.box((-1.5, y + 3, z + 0.5), (3, 4, 1), dict(knot, shape='point'), name='knot_tail')
        return self

    def boots(self, mat, height=5.0):
        B = self.B
        for leg in (self.leg_r, self.leg_l):
            px = leg.pivot[0]
            leg.box((px - B['lw'] / 2, 24 - height, -B['ld'] / 2), (B['lw'], height, B['ld']), mat, grow=0.3, name='boot',
                    faces={'top': mat})
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
        else:
            self.blink_mat = None
        return self

    def _set_hair_color(self, color):
        self.hair_color = color
        if self.head_mat is not None:
            self.head_mat['hair'] = color
        if getattr(self, 'blink_mat', None) is not None:
            self.blink_mat['hair'] = color

    def hair(self, color, style='long', length=12.0, tip=None, bangs=None, side_locks=True, twin=False, ponytail=False,
             ahoge=False, volume=0.5, shine=True, ears_open=False, side_len=None):
        self._set_hair_color(color)
        h = self.B['head']
        top = self.head_top
        if bangs is None:
            bangs = 'bangs' if self.build in ('woman', 'child') else 'short'
        if bangs is False:
            bangs = 'open'
        long_sides = style in ('long', 'very_long', 'wavy', 'bob') or self.build == 'woman'
        shell = M('hair_shell', color, tip=None, bangs=bangs, long=long_sides, shine=shine, ears_open=ears_open,
                  back=style != 'short' or self.build != 'man')
        self.head.box((-h / 2, top, -h / 2), (h, h, h), shell, grow=0.5, name='hair')
        hm = M('hair', color, tip=tip, shine=shine)
        self.hair_mat = hm
        L = length
        back_z = h / 2 + 0.5
        if style in ('long', 'very_long', 'wavy'):
            # one curtain from the crown to the shoulders, then three flowing strands
            U = int(min(8, max(4, L * 0.45)))
            cur = self.rig.bone('hair_back', self.head, (0, top + 2, back_z), anim='hair', amp=0.02, speed=0.07, drag=0.3)
            cur.box((-4.5, top + 2, back_z - 0.5), (9, U, 1), dict(hm, t0=0.0, t1=U / L), name='curtain')
            lower = max(2, int(round(L - U)))
            for k, (x0, w) in enumerate(((-4.5, 3), (-1.5, 3), (1.5, 3))):
                ln = lower + (1 if k == 1 else 0)
                b = self.rig.bone(f'hair_tip{k}', cur, (x0 + w / 2, top + 2 + U, back_z), anim='hair', amp=0.05,
                                  speed=0.07, phase=0.6 * k, drag=0.5)
                b.box((x0, top + 2 + U, back_z - 0.5), (w, ln, 1),
                      dict(hm, t0=U / L, t1=1.0, cut='tips' if style == 'wavy' else 'point'), name='strand')
        elif style == 'bob':
            self.head.box((-h / 2, top + 5, back_z - 2), (h, 4, 2), dict(hm, cut='tips'), grow=0.5, name='bob',
                          faces={'top': None})
        elif style == 'short' and self.build != 'man':
            self.head.box((-h / 2, top + 6, back_z - 1), (h, 2, 1), dict(hm, cut='tips'), name='nape')
        if side_locks and long_sides:
            sl = side_len or min(10, max(4, L * 0.4))
            for sgn in (-1, 1):
                b = self.rig.bone(f'lock_{"r" if sgn < 0 else "l"}', self.head, (sgn * (h / 2), top + 6, -h / 2 + 1),
                                  anim='hair', amp=0.03, speed=0.09, phase=sgn)
                b.box((sgn * (h / 2) - (1 if sgn > 0 else 0) - 0.0, top + 6, -h / 2 - 0.5), (1, int(round(sl)), 2),
                      dict(hm, cut='point', t0=0.2, t1=0.7), grow=0.25, name='lock')
        if twin:
            for sgn in (-1, 1):
                b = self.rig.bone(f'twin_{"r" if sgn < 0 else "l"}', self.head, (sgn * (h / 2 + 1), top + 2, 1),
                                  anim='hair', amp=0.07, speed=0.08, phase=sgn * 1.3, drag=0.5)
                b.box((sgn * (h / 2 + 1) - 1.5, top + 2, -0.5), (3, int(round(L * 0.8)), 3), dict(hm, cut='point', t0=0.1, t1=1),
                      name='twin')
                b.box((sgn * (h / 2 + 1) - 1, top + 1, -0), (2, 2, 2), M('cloth', self.accent), grow=0.2, name='twin_tie')
        if ponytail:
            b = self.rig.bone('ponytail', self.head, (0, top + 2, back_z + 0.5), anim='hair', amp=0.08, speed=0.08,
                              phase=0.5, drag=0.7)
            b.box((-1.5, top + 2, back_z), (3, int(round(L * 0.9)), 3), dict(hm, cut='point', t0=0.1, t1=1), name='tail')
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
            count = max(6, int(round(per / 4.0)))
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

    def skirt(self, mat, length=9.0, flare=1.4, layers=1, top_y=None, tiers=2, name='skirt'):
        B = self.B
        y0 = top_y if top_y is not None else self.hip_y - 2
        ang = min(0.55, 0.12 + flare * 0.12)
        L = max(4, int(round(length * 0.7)))
        # waistband so the panel tops are hidden
        self.hips.box((-B['tw'] / 2, y0, -B['td'] / 2), (B['tw'], 2, B['td']), mat, grow=0.6, name=f'{name}_band',
                      faces={'top': None, 'bottom': None})
        hub = self.flare(self.hips, y0 + 1, B['tw'] / 2 + 0.5, B['td'] / 2 + 0.6, L, ang, mat, name=name)
        if tiers >= 2:
            inner = dict(mat)
            inner.pop('pattern', None)
            inner['trim'] = mat.get('trim', 0) or 2
            self.flare(self.hips, y0 + 1, B['tw'] / 2 + 0.3, B['td'] / 2 + 0.4, L + 1, ang * 0.7, dict(inner, color=shade(mat['color'], 0.85)),
                       name=name + '_under', k=0.7, shape='scallop')
        return hub

    def robe(self, mat, length=None, flare=2.4, split=False):
        B = self.B
        y0 = self.hip_y - 2
        L = int(round((24 - y0 - 0.5) if length is None else length))
        ang = math.atan2(flare * 0.8, L)
        self.hips.box((-B['tw'] / 2, y0, -B['td'] / 2), (B['tw'], 2, B['td']), mat, grow=0.6, name='robe_band',
                      faces={'top': None, 'bottom': None})
        if split:
            self.flare(self.hips, y0 + 1, B['tw'] / 2 + 0.5, B['td'] / 2 + 0.6, L, ang, dict(mat), name='robe', k=0.5,
                       start=0.08, sweep=0.84)
        else:
            self.flare(self.hips, y0 + 1, B['tw'] / 2 + 0.5, B['td'] / 2 + 0.6, L, ang, dict(mat), name='robe', k=0.5)
        return self

    def coat_tails(self, mat, length=10.0):
        B = self.B
        y0 = self.hip_y - 1
        self.flare(self.hips, y0, B['tw'] / 2 + 0.6, B['td'] / 2 + 0.7, int(round(length)), 0.18, dict(mat), name='coat',
                   k=0.6, start=0.2, sweep=0.6, shape='point')
        return self

    def cape(self, mat, length=16.0, width=None, top=None):
        B = self.B
        w = int(round(width or B['tw'] + 2))
        y0 = top if top is not None else self.top
        z = B['td'] / 2 + 0.5
        L = int(round(length))
        a = self.rig.bone('cape', self.torso, (0, y0, z), rot=(0.08, 0, 0), anim='cape', amp=0.04, speed=0.06)
        h1 = L // 2
        a.box((-w / 2, y0, z), (w, h1, 1), dict(mat, hem_shadow=False), name='cape')
        b = self.rig.bone('cape_low', a, (0, y0 + h1, z), anim='cape', amp=0.05, speed=0.06, phase=0.8, drag=0.4)
        b.box((-w / 2, y0 + h1, z), (w, L - h1, 1), mat, name='cape_hem')
        # collar/mantle on the shoulders
        self.torso.box((-B['tw'] / 2, self.top, -B['td'] / 2), (B['tw'], 1, B['td']), dict(mat, trim=0), grow=0.6,
                       name='mantle', faces={'bottom': None})
        return a

    def shoulder_pads(self, mat, size=3.2):
        B = self.B
        for arm, sgn in ((self.arm_r, -1), (self.arm_l, 1)):
            px = arm.pivot[0]
            s = int(round(size))
            arm.box((px - B['aw'] / 2 - (1 if sgn < 0 else 0), self.top - 1, -B['ad'] / 2 - 0.5), (B['aw'] + 1, 3, B['ad'] + 1),
                    mat, grow=0.25, name='pad')
        return self

    def belt(self, mat, buckle=None):
        B = self.B
        y = self.hip_y - 2
        self.torso.box((-B['tw'] / 2, y, -B['td'] / 2), (B['tw'], 1, B['td']), mat, grow=0.35, name='belt')
        if buckle:
            self.torso.box((-1, y - 0.5, -B['td'] / 2 - 0.6), (2, 2, 0), buckle, name='buckle')
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

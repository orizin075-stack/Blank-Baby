"""Humanoids for the design-sheet characters (sheet_chars.py): the sheets' proportions (a big 8-pixel head on a
body about four and a half heads tall), the anime face and hair shell of gaiaface, and everything else built as
cubes and painted with vox.py.

Model pixels as everywhere: x to the character's left, y down with the ground at 24, z backwards. The rig's
in-game size comes from the hitbox, not from these numbers."""
import math
import numpy as np
import bb
from paint import M
from designfig import Fig
from vox import V

HS = 8.0


class Hum:
    """Bones and head of a sheet humanoid.

    H        total height in model pixels (feet to the top of the head, hair and horns not counted)
    build    'woman', 'man', 'child' (face layout and shoulder width)
    face     gaiaface spec: iris, iris2, style, mouth, blush, glow_eyes, heterochromia ...
    """
    def __init__(self, key, skin, hair, face, build='woman', H=36.0, td=4, shoulders=None, hover=0.0, bangs='bangs'):
        self.f = f = Fig(key, td=td)
        self.r = f.r
        self.skin, self.hair, self.face, self.build, self.bangs = skin, hair, dict(face), build, bangs
        self.top = 24.0 - H
        self.chin = self.top + HS
        self.neck = self.chin + 0.8
        man = build in ('man', 'large')
        self.sw = shoulders or (3.9 if man else 3.4)               # shoulder joint x
        self.sh_y = self.neck + 1.4
        self.waist_y = self.sh_y + (5.0 if man else 4.4)
        self.hip_y = self.waist_y + 2.0
        self.crotch = self.hip_y + 2.6
        self.knee_y = self.crotch + (24.0 - self.crotch) * 0.5
        self.lx = 1.5 if not man else 1.8
        f.humanoid(hip_y=self.hip_y, waist_y=self.waist_y, neck_y=self.neck, shoulder=(-self.sw, self.sh_y, 0),
                   elbow=(-self.sw - 0.4, self.sh_y + 4.6, 0), hip=(-self.lx, self.crotch, 0), knee=(-self.lx, self.knee_y, 0),
                   hover=hover)
        f.b['arm_r'].rot = (0, 0, 0.08)
        f.b['arm_l'].rot = (0, 0, -0.08)
        self.b = f.b

    # ------------------------------------------------------------------ head
    def head(self, shell=True, blink=True, **spec):
        """The head: a face drawn as on the sheet (sface.face) and the hair volume round it. Extra keyword
        arguments go into the face spec (fringe, side_len, ears_open, short_back ...)."""
        f, top = self.f, self.top
        self.face.update(spec)
        self.face.setdefault('skin', self.skin)
        self.face.setdefault('hair', self.hair)
        mat = {'type': 'sface', 'spec': self.face}
        bb.cube(self.b['head'], (-HS / 2, top, -HS / 2), (HS, HS, HS), mat, name='head', info={'head': True, 'ao': False}, td=4)
        if blink:
            lb = f.bone('blink', 'head', (0, top, -HS / 2 - 0.03), anim='blink', every=90.0)
            bb.cube(lb, (-HS / 2, top, -HS / 2 - 0.03), (HS, HS, 0), {'type': 'slids', 'spec': self.face}, name='lids',
                    info={'ao': False, 'lids': True}, td=4)
        if shell:
            bb.obox(self.b['head'], (0, top + HS / 2, 0), (HS, HS, HS), np.eye(3), {'type': 'sshell', 'spec': self.face}, name='hair',
                    inflate=0.6, info={'ao': False}, tex_size=(HS, HS, HS), td=4)
        return self

    def hair_mat(self, tip=None, **kw):
        return V(self.hair, strands=True, tip=tip, **kw)

    def fringe(self, xs, lengths, mat=None, z=None, w=1.2):
        """Strands hanging over the forehead in front of the shell: xs across, lengths down from the hairline."""
        mat = mat or self.hair_mat()
        z = -HS / 2 - 0.75 if z is None else z
        for x, L in zip(xs, lengths):
            self.f.box('head', (x, self.top + 0.5 + L / 2, z), (w, L, 0.6), name='fringe', mat=mat)

    def locks(self, length, mat=None, x=4.6, w=1.6, d=3.2, z=-1.6, both=True):
        """Side locks framing the face, down to `length` below the chin."""
        mat = mat or self.hair_mat()
        for sx in ((-1, 1) if both else (-1,)):
            top = self.top + 2.0
            bot = self.chin + length
            self.f.box('head', (sx * x, (top + bot) / 2, z), (w, bot - top, d), name='lock', mat=mat)

    def long_hair(self, bottom, mat=None, width=9.4, z=4.2, n=6, depth=1.6, spread=0.0, jag=1.4, bone='torso', seed=3, layers=2):
        """The fall of hair down the back: `layers` rows of strand panels, the outer ones shorter and set back, each
        strand its own length, so the back reads as a cascade of locks rather than a slab."""
        mat = mat or self.hair_mat()
        rng = np.random.default_rng(seed)
        top = self.top + 3.0
        hb = self.b[bone] if isinstance(bone, str) else bone
        for layer in range(layers):
            nl = n + layer
            for i in range(nl):
                t = (i + 0.5) / nl - 0.5
                x = t * (width - layer * 0.8) + rng.uniform(-0.15, 0.15)
                w = (width - layer * 0.8) / nl + 0.3
                b = bottom - rng.uniform(0, jag) - layer * 2.5
                zz = z + layer * 0.9 + abs(t) * spread * 2 + rng.uniform(-0.2, 0.2)
                d = depth * (0.8 if layer else 1.0)
                self.f.box('head', (x, (top + self.neck + 1) / 2, zz - 0.5), (w, self.neck + 1 - top, d + 0.4), name='hair_fall', mat=mat)
                self.f.box(hb, (x, (self.neck + 1 + b) / 2, zz), (w, b - self.neck - 1, d), name='hair_fall', mat=mat)

    def sleeves(self, mat, drop=6.0, width=4.2, depth=4.0, start=0.3, flare=1.6):
        """Wide hanging sleeves: from the forearm, widening as they hang below it."""
        for side, (sh, el, ha) in self.arm_pts.items():
            a = el + (ha - el) * start
            b = ha + np.array([0, drop * 0.45, 0.4])
            self.f.chain(f'fore_{side}', [a, b], [width, width + flare], d=[depth, depth + flare * 0.6], name='sleeve', mat=mat, up=(0, 0, -1))

    # ------------------------------------------------------------------ body
    def torso(self, chest, belly=None, depth=4.2, width=None, chest_w=None):
        w = width or (6.6 if self.build not in ('man', 'large') else 7.8)
        f = self.f
        f.box('torso', (0, (self.neck + self.waist_y) / 2, 0), (chest_w or w, self.waist_y - self.neck, depth), name='chest', mat=chest)
        f.box('hips', (0, (self.waist_y + self.crotch) / 2, 0), (w - 0.2, self.crotch - self.waist_y, depth + 0.2), name='belly',
              mat=belly or chest)
        return self

    def arms(self, upper, fore, hand=None, w=2.2, pose=None):
        """Arms hanging a little out from the body. pose: {side: (elbow (x, y, z), hand (x, y, z))} to place them."""
        f = self.f
        hand = hand or V(self.skin, var=0.0)
        out = {}
        for side, sx in (('r', -1), ('l', 1)):
            sh = np.array([sx * self.sw, self.sh_y, 0.0])
            el = np.array([sx * (self.sw + 0.5), self.sh_y + 4.4, 0.0])
            ha = np.array([sx * (self.sw + 0.8), self.sh_y + 8.4, -0.4])
            if pose and side in pose:
                el, ha = np.asarray(pose[side][0], float), np.asarray(pose[side][1], float)
            f.chain(f'arm_{side}', [sh + (0, -0.8, 0), el], [w, w], name='upper', mat=upper)
            f.chain(f'fore_{side}', [el, ha], [w * 0.95, w * 0.9], name='fore', mat=fore)
            f.box(f'fore_{side}', ha + (ha - el) / max(1e-6, np.linalg.norm(ha - el)) * 0.9, (w * 0.85, 1.8, w * 0.85), name='hand', mat=hand)
            out[side] = (sh, el, ha)
        self.arm_pts = out
        return out

    def legs(self, leg, shoe, shoe_size=(2.8, 1.6, 3.8), w=2.6, stance=0.0, shoe_y=None):
        f = self.f
        for side, sx in (('r', -1), ('l', 1)):
            hip = np.array([sx * self.lx, self.crotch - 0.6, 0.0])
            knee = np.array([sx * (self.lx + stance * 0.5), self.knee_y, -0.2])
            foot = np.array([sx * (self.lx + stance), 24.0 - shoe_size[1], -0.2])
            f.chain(f'leg_{side}', [hip, knee], [w, w * 0.95], name='thigh', mat=leg)
            f.chain(f'shin_{side}', [knee, foot], [w * 0.95, w * 0.9], name='shin', mat=leg)
            f.box(f'shin_{side}', (foot[0], 24.0 - shoe_size[1] / 2, foot[2] - 0.5), shoe_size, name='shoe', mat=shoe)

    def skirt(self, mat, top, bottom, w_top, w_bot, d_top, d_bot, bone='hips', name='skirt', z=0.0):
        """A flared skirt, robe or hakama: one block from a top rectangle to a wider bottom one."""
        return self.f.frustum(bone, ((0, top, z), w_top, d_top), ((0, bottom, z + 0.3), w_bot, d_bot), name=name, mat=mat)

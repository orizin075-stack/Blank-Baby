"""Superb Warfare guns and the Blueprinter for OROR 0.17.27.

  python3 sbwguns.py <out dir>          (normally oror_rework/neoforge1211patch/overlay)

Writes, for the railgun (天穿) and the laser gun (神罰):
  assets/oror_supreme_bosses/geo/<gun>.geo.json            GeckoLib model (Bedrock 1.12.0, per-face UV)
  assets/oror_supreme_bosses/animations/<gun>.animation.json
  assets/oror_supreme_bosses/textures/item/<gun>.png        painted atlas, 4 texels per model unit
  assets/oror_supreme_bosses/textures/item/<gun>_icon.png   inventory sprite (rendered from the model)
  assets/oror_supreme_bosses/textures/gun_icon/<gun>_icon.png   HUD side view, 256x64 like Superb Warfare's
  assets/oror_supreme_bosses/sbw/guns/<gun>.json            Superb Warfare client resource
  assets/oror_supreme_bosses/models/item/<gun>{,_base,_icon}.json, models/displaysettings/<gun>.item.json
and the Blueprinter's block-model item (cuboids, no renderer), the ammunition sprites, and the data: the guns'
Superb Warfare data (data/oror_supreme_bosses/sbw/guns), the recipes and the Blueprinter's block tags.

The skeleton above the gun parts copies the pivots of Superb Warfare's Sentinel (camera, root, move, bone, shen, 0,
magzine, the two arm bones), so its first-person placement, aiming offsets and arm poses carry over; every part under
"gun" is new. Bones whose name ends in _illuminated are drawn full bright by Superb Warfare's gun renderer.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

from colors import hexc, mix, shade

NS = 'oror_supreme_bosses'
TD = 4                      # texels per model unit
EYE = (-0.36, 4.82)         # sight axis (x, y): where the Sentinel's aiming offsets put the scope in front of the eye

# --------------------------------------------------------------------------------------------------------------------
# materials

MATS = {
    # name: base colour, noise, style
    'gunmetal': ('#3a4250', 0.05, 'metal'),
    'darkmetal': ('#23272f', 0.04, 'metal'),
    'steel': ('#7d8894', 0.05, 'metal'),
    'brass': ('#c79a3c', 0.05, 'metal'),
    'gold': ('#e2b84a', 0.04, 'metal'),
    'copper': ('#b86b3a', 0.05, 'coil'),
    'polymer': ('#1d1f24', 0.03, 'polymer'),
    'rubber': ('#151619', 0.03, 'grip'),
    'ceramic': ('#e9e7e1', 0.025, 'ceramic'),
    'ceramic2': ('#c9cbd0', 0.03, 'ceramic'),
    'carbon': ('#202329', 0.03, 'carbon'),
    'hazard': ('#e8c22c', 0.03, 'hazard'),
    'cyan_glow': ('#4ff3ff', 0.0, 'glow'),
    'blue_glow': ('#3b8dff', 0.0, 'glow'),
    'red_glow': ('#ff2a4a', 0.0, 'glow'),
    'magenta_glow': ('#ff4fd2', 0.0, 'glow'),
    'gold_glow': ('#ffd36a', 0.0, 'glow'),
    'glass_cyan': ('#7fe8ff', 0.0, 'glass'),
    'glass_red': ('#ff5a6e', 0.0, 'glass'),
    'lens': ('#16202c', 0.0, 'glass'),
}


def _hash(x, y, s):
    h = (x * 374761393 + y * 668265263 + s * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


class Cube:
    def __init__(self, bone, lo, hi, mat, pattern=None, rot=None, pivot=None, skip=(), seed=0):
        self.bone, self.lo, self.hi, self.mat = bone, tuple(lo), tuple(hi), mat
        self.pattern, self.rot, self.pivot, self.skip, self.seed = pattern, rot, pivot, set(skip), seed
        self.uv = {}

    @property
    def size(self):
        return tuple(self.hi[i] - self.lo[i] for i in range(3))


class Model:
    def __init__(self, name, tex=(256, 256)):
        self.name, self.tex = name, tex
        self.bones, self.cubes = [], []

    def bone(self, name, parent=None, pivot=(0, 0, 0), rot=None):
        self.bones.append({'name': name, 'parent': parent, 'pivot': list(pivot), 'rot': rot})
        return name

    def box(self, bone, lo, hi, mat, pattern=None, rot=None, pivot=None, skip=()):
        c = Cube(bone, lo, hi, mat, pattern, rot, pivot, skip, seed=len(self.cubes) * 17 + 3)
        self.cubes.append(c)
        return c

    def mirror_x(self, bone, lo, hi, mat, pattern=None, **kw):
        """A pair of boxes mirrored across the gun's centre plane x = 0."""
        a = self.box(bone, lo, hi, mat, pattern, **kw)
        b = self.box(bone, (-hi[0], lo[1], lo[2]), (-lo[0], hi[1], hi[2]), mat, pattern, **kw)
        return a, b


# --------------------------------------------------------------------------------------------------------------------
# faces: dimensions, UV packing and painting

FACES = ('north', 'south', 'east', 'west', 'up', 'down')


def face_dims(c, f):
    sx, sy, sz = c.size
    return {'north': (sx, sy), 'south': (sx, sy), 'east': (sz, sy), 'west': (sz, sy), 'up': (sx, sz), 'down': (sx, sz)}[f]


def pack(model):
    """Shelf-pack every visible face; sets cube.uv[face] = (u, v, w, h) in texels."""
    rects = []
    for c in model.cubes:
        for f in FACES:
            if f in c.skip:
                continue
            w, h = face_dims(c, f)
            if w <= 0 or h <= 0:
                continue
            rects.append((max(1, int(math.ceil(w * TD - 1e-6))), max(1, int(math.ceil(h * TD - 1e-6))), c, f))
    rects.sort(key=lambda r: (-r[1], -r[0]))
    W, H = model.tex
    x = y = row = 0
    for w, h, c, f in rects:
        if x + w > W:
            x, y, row = 0, y + row, 0
        if y + h > H:
            raise SystemExit(f'{model.name}: atlas {W}x{H} too small')
        c.uv[f] = (x, y, w, h)
        x += w
        row = max(row, h)
    return y + row


def paint_face(img, glow, c, f):
    u, v, w, h = c.uv[f]
    base, noise, style = MATS[c.mat]
    base = hexc(base)
    pat = c.pattern or ''
    side = f not in ('up', 'down')
    for j in range(h):
        for i in range(w):
            t = j / max(1, h - 1)
            k = 1.0
            if style in ('metal', 'polymer', 'ceramic', 'carbon', 'grip', 'coil', 'hazard'):
                k = (1.10 - 0.22 * t) if side else (1.12 if f == 'up' else 0.78)
            n = (_hash(i + u, j + v, c.seed) - 0.5) * 2 * noise
            col = base
            if style == 'coil':
                # copper winding: a bright and a dark turn every texel along the long axis
                along = i if w >= h else j
                col = shade(base, 1.18 if along % 2 == 0 else 0.78)
                if (j if w >= h else i) in (0, (h if w >= h else w) - 1):
                    col = shade(base, 0.55)
            elif style == 'grip':
                col = shade(base, 1.25 if (i + j) % 2 == 0 and (i // 2 + j // 2) % 2 == 0 else 0.95)
            elif style == 'carbon':
                col = shade(base, 1.22 if ((i + (j // 2)) // 2) % 2 == 0 else 0.86)
            elif style == 'hazard':
                col = hexc('#e8c22c') if ((i + j) // 3) % 2 == 0 else hexc('#1b1b1e')
            elif style == 'glow':
                # hot centre, saturated rim: reads as light even before the full-bright pass
                cx, cy = (i + 0.5) / w - 0.5, (j + 0.5) / h - 0.5
                d = max(abs(cx) * (2 if w > 2 else 0), abs(cy) * (2 if h > 2 else 0))
                col = mix(base, (255, 255, 255), max(0.0, 0.75 - d) * 0.9)
                k = 1.0
            elif style == 'glass':
                g = ((i - j) % max(4, (w + h) // 3)) == 0
                col = mix(shade(base, 0.7 + 0.5 * (1 - t)), (255, 255, 255), 0.45 if g else 0.0)
                k = 1.0
            elif style == 'ceramic':
                col = base
            rgb = np.array(shade(col, k), dtype=np.float32) * (1 + n)
            # bevels: catch light on the upper edge, fall away on the lower one
            if style not in ('glow', 'glass') and w > 2 and h > 2:
                if side and j == 0:
                    rgb = rgb * 1.28 + 12
                elif side and j == h - 1:
                    rgb = rgb * 0.58
                elif i == 0 or i == w - 1:
                    rgb = rgb * 0.82
                elif not side and (j == 0 or j == h - 1):
                    rgb = rgb * (1.2 if f == 'up' else 0.7)
            img[v + j, u + i, :3] = np.clip(rgb, 0, 255)
            img[v + j, u + i, 3] = 255
            if style == 'glow':
                glow[v + j, u + i] = 1
    # patterns over the base
    long_axis = w >= h
    if 'panel' in pat and w > 6 and h > 3:
        step = 6 * TD if long_axis else 4 * TD
        for p in range(step, (w if long_axis else h) - 2, step):
            for q in range(1, (h if long_axis else w) - 1):
                a, b = (q, p) if long_axis else (p, q)
                img[v + a, u + b, :3] *= 0.5
                if long_axis and b + 1 < w:
                    img[v + a, u + b + 1, :3] = np.clip(img[v + a, u + b + 1, :3] * 1.25, 0, 255)
    if 'rivet' in pat and w > 6 and h > 5:
        for (a, b) in ((1, 1), (1, w - 2), (h - 2, 1), (h - 2, w - 2)):
            img[v + a, u + b, :3] = np.array(shade(hexc('#c9ced6'), 1.2))
    if 'vent' in pat and side and h > 4 and w > 4:
        for a in range(2, h - 2, 2):
            for b in range(2, w - 2):
                img[v + a, u + b, :3] *= 0.35
                if a + 1 < h - 1:
                    img[v + a + 1, u + b, :3] = np.clip(img[v + a + 1, u + b, :3] * 1.15, 0, 255)
    if 'trim' in pat and side and h > 3:
        gold = np.array(hexc('#e2b84a'), dtype=np.float32)
        for b in range(w):
            img[v + 1, u + b, :3] = gold * (1.15 if b % 5 else 0.8)
    if 'gauge' in pat and w > 4:
        for b in range(1, w - 1):
            lit = (b // 2) % 2 == 0
            for a in range(1, h - 1):
                img[v + a, u + b, :3] = np.array(hexc('#4ff3ff') if lit else hexc('#10262c'), dtype=np.float32)
                glow[v + a, u + b] = 1 if lit else glow[v + a, u + b]
    if 'engrave' in pat and side and w > 12 and h > 4:
        # a fine ornamental line along the middle with diamond studs: the "expensive" look
        mid = h // 2
        for b in range(2, w - 2):
            img[v + mid, u + b, :3] = np.clip(img[v + mid, u + b, :3] * 0.62, 0, 255)
            if b % 8 == 4:
                for a in (mid - 1, mid + 1):
                    if 0 < a < h - 1:
                        img[v + a, u + b, :3] = np.array(hexc('#e2b84a'), dtype=np.float32)
                img[v + mid, u + b, :3] = np.array(hexc('#fff1b8'), dtype=np.float32)
    if 'lens' in pat and f == 'north':
        cx, cy = w / 2, h / 2
        for j in range(h):
            for i in range(w):
                d = math.hypot(i + 0.5 - cx, j + 0.5 - cy) / (min(w, h) / 2)
                if d < 1:
                    col = mix(hexc(MATS[c.mat][0]), (255, 255, 255), max(0.0, 0.8 - d))
                    img[v + j, u + i, :3] = np.array(col, dtype=np.float32)
                    glow[v + j, u + i] = 1


def paint(model):
    W, H = model.tex
    img = np.zeros((H, W, 4), np.float32)
    glow = np.zeros((H, W), np.uint8)
    for c in model.cubes:
        for f in c.uv:
            paint_face(img, glow, c, f)
    return img, glow


# --------------------------------------------------------------------------------------------------------------------
# GeckoLib output

def geo_json(model, ident):
    bones = []
    by = {b['name']: b for b in model.bones}
    for b in model.bones:
        o = {'name': b['name'], 'pivot': [round(p, 5) for p in b['pivot']]}
        if b['parent']:
            o['parent'] = b['parent']
        if b['rot']:
            o['rotation'] = [round(r, 5) for r in b['rot']]
        cubes = []
        for c in model.cubes:
            if c.bone != b['name']:
                continue
            cj = {'origin': [round(c.lo[i], 4) for i in range(3)], 'size': [round(c.size[i], 4) for i in range(3)]}
            if c.rot:
                cj['pivot'] = [round(p, 4) for p in (c.pivot or c.lo)]
                cj['rotation'] = [round(r, 4) for r in c.rot]
            cj['uv'] = {f: {'uv': [c.uv[f][0], c.uv[f][1]], 'uv_size': [c.uv[f][2], c.uv[f][3]]} for f in FACES if f in c.uv}
            cubes.append(cj)
        if cubes:
            o['cubes'] = cubes
        bones.append(o)
    assert all(b.get('parent') in (None, *by) for b in bones)
    W, H = model.tex
    return {'format_version': '1.12.0', 'minecraft:geometry': [{
        'description': {'identifier': 'geometry.' + ident, 'texture_width': W, 'texture_height': H,
                        'visible_bounds_width': 8, 'visible_bounds_height': 4, 'visible_bounds_offset': [0, 0.5, 0]},
        'bones': bones}]}


def kf(frames):
    return {('%g' % t if t else '0.0'): list(v) for t, v in frames}


def animations(name, glow_bones, mag_drop=(0, -5, 3), mag_bone='magzine'):
    idle = {'loop': True, 'animation_length': 2.0, 'bones': {
        b: {'scale': kf([(0, (1, 1, 1)), (1.0, (1.06, 1.06, 1.0)), (2.0, (1, 1, 1))])} for b in glow_bones}}
    # held fire = the charge-up (Superb Warfare plays "Fire" while the trigger is held and the gun can shoot)
    fire = {'loop': True, 'animation_length': 0.3, 'bones': {
        b: {'scale': kf([(0, (1.0, 1.0, 1.0)), (0.1, (1.25, 1.25, 1.0)), (0.2, (0.9, 0.9, 1.0)), (0.3, (1.0, 1.0, 1.0))])}
        for b in glow_bones}}
    fire['bones']['0'] = {'position': kf([(0, (0, 0, 0)), (0.05, (0.04, -0.03, 0.05)), (0.15, (-0.04, 0.03, 0.03)),
                                          (0.3, (0, 0, 0))])}
    dx, dy, dz = mag_drop
    reload = {'loop': 'hold_on_last_frame', 'animation_length': 2.6, 'bones': {
        mag_bone: {'position': kf([(0, (0, 0, 0)), (0.35, (dx, dy, dz)), (0.5, (dx, dy - 9, dz)), (1.4, (dx, dy - 9, dz)),
                                   (1.75, (dx, dy, dz)), (2.1, (0, 0, 0)), (2.6, (0, 0, 0))]),
                   'rotation': kf([(0, (0, 0, 0)), (0.35, (-12, 0, 8)), (1.75, (-12, 0, 8)), (2.1, (0, 0, 0))])},
        '0': {'rotation': kf([(0, (0, 0, 0)), (0.4, (-4, 6, -14)), (2.0, (-4, 6, -14)), (2.5, (0, 0, 0))]),
              'position': kf([(0, (0, 0, 0)), (0.4, (0.6, -0.8, 0.5)), (2.0, (0.6, -0.8, 0.5)), (2.5, (0, 0, 0))])},
        'camera': {'rotation': kf([(0, (0, 0, 0)), (0.45, (-1.2, 0.6, -1.5)), (2.1, (-0.8, 0.4, -1)), (2.6, (0, 0, 0))])}}}
    for b in glow_bones:   # the cells go dark while the slug or cell is out
        reload['bones'][b] = {'scale': kf([(0, (1, 1, 1)), (0.4, (0.2, 0.2, 1)), (2.0, (0.2, 0.2, 1)), (2.4, (1, 1, 1))])}
    run = {'loop': True, 'animation_length': 0.8, 'bones': {
        '0': {'rotation': kf([(0, (-8, 18, 22)), (0.4, (-6, 20, 26)), (0.8, (-8, 18, 22))]),
              'position': kf([(0, (1.5, -1.5, 1)), (0.4, (1.6, -1.2, 1)), (0.8, (1.5, -1.5, 1))])},
        'camera': {'rotation': kf([(0, (0, 0, 0)), (0.2, (0.6, 0.3, 0)), (0.4, (0, 0, 0)), (0.6, (0.6, -0.3, 0)), (0.8, (0, 0, 0))])}}}
    return {'format_version': '1.8.0', 'animations': {
        f'animation.{name}.idle': idle, f'animation.{name}.fire': fire,
        f'animation.{name}.reload': reload, f'animation.{name}.run': run}}


def skeleton(m, flare_z):
    """The Sentinel's skeleton: the parts go under "gun"."""
    m.bone('camera', None, (2.57141, 4.76276, 13.97702))
    m.bone('root', None, (0, -2, 3))
    m.bone('move', 'root')
    m.bone('bone', 'move')
    m.bone('shen', 'bone', (0, 0, 7))
    m.bone('qiang', 'shen')
    m.bone('0', 'qiang', (0, 0, 7))
    m.bone('flare', '0', (0, 1.35156, flare_z))
    m.bone('gun', '0', (0.34663, 2.407, -3.28851))
    m.bone('magzine', '0', (0, -2.31671, 13.78107))
    m.bone('Lefthand', 'magzine', (5.24559, -8.04155, 1.10912), (72.79916, -39.78478, -103.12114))
    m.bone('Righthand', '0', (-4.60882, -3.88091, 16.51741), (101.23265, 19.20433, -176.8486))
    # the arm bones hold a hidden 4x12x4 stand-in each; the renderer draws the player's arms there
    m.box('Lefthand', (3.24559, -8.04155, -0.89088), (7.24559, 3.95845, 3.10912), 'polymer')
    m.box('Righthand', (-6.60882, -3.88091, 14.51741), (-2.60882, 8.11909, 18.51741), 'polymer')


def grip(m, bone, z0, mat='rubber', trim='gunmetal'):
    """Pistol grip, raked back 14 degrees, with a trigger and guard in front of it."""
    m.box(bone, (-0.95, -6.2, z0), (0.95, -0.4, z0 + 2.6), mat, rot=(-14, 0, 0), pivot=(0, -0.4, z0 + 1.3))
    m.box(bone, (-1.05, -6.6, z0 - 0.2), (1.05, -6.0, z0 + 2.9), trim, rot=(-14, 0, 0), pivot=(0, -0.4, z0 + 1.3))
    m.box(bone, (-0.25, -2.0, z0 - 1.5), (0.25, -0.4, z0 - 1.0), 'gold')                      # trigger
    m.box(bone, (-0.35, -2.6, z0 - 3.2), (0.35, -2.2, z0 - 0.1), trim)                         # guard, lower bar
    m.box(bone, (-0.35, -2.6, z0 - 3.4), (0.35, -0.4, z0 - 2.9), trim)                         # guard, front post


def scope(m, bone, z0, z1, bell_mat='darkmetal', lens='glass_cyan', ring='gold'):
    """Tube scope centred on the sight axis."""
    ex, ey = EYE
    r = 0.85
    m.box(bone, (ex - r, ey - r, z0 + 1.6), (ex + r, ey + r, z1 - 1.6), 'gunmetal', 'engrave')
    m.box(bone, (ex - 1.15, ey - 1.15, z0), (ex + 1.15, ey + 1.15, z0 + 1.7), bell_mat, 'rivet')
    m.box(bone, (ex - 1.0, ey - 1.0, z1 - 1.7), (ex + 1.0, ey + 1.0, z1), bell_mat)
    m.box(bone, (ex - 0.9, ey - 0.9, z0 - 0.1), (ex + 0.9, ey + 0.9, z0), lens, 'lens')
    m.box(bone, (ex - 0.8, ey - 0.8, z1), (ex + 0.8, ey + 0.8, z1 + 0.1), lens)
    for z in (z0 + 2.4, z1 - 3.0):
        m.box(bone, (ex - 1.0, ey - 1.0, z), (ex + 1.0, ey + 1.0, z + 0.6), ring)
        m.box(bone, (ex - 0.45, 3.0, z), (ex + 0.45, ey - 0.95, z + 0.6), 'darkmetal')        # mount


# --------------------------------------------------------------------------------------------------------------------
# the railgun 天穿 (Amaugachi): twin rails on a gunmetal frame, copper coil collars, cyan capacitor cells

def railgun():
    m = Model('railgun', (512, 256))
    skeleton(m, -28.6)
    g = 'gun'
    m.bone('bore_illuminated', g, (0, 1.4, -15))
    m.bone('cells_illuminated', g, (0, 1.4, 6))
    # receiver
    m.box(g, (-1.7, -0.7, -5.0), (1.7, 3.3, 12.0), 'gunmetal', 'panel rivet')
    m.box(g, (-1.85, 2.9, -4.6), (1.85, 3.6, 11.6), 'darkmetal', 'trim')                  # top strap with gold inlay
    m.box(g, (-1.3, -1.6, -5.0), (1.3, -0.7, 8.0), 'darkmetal', 'vent')                   # lower receiver
    # capacitor banks either side, each with a lit cell window
    for sx in (1, -1):
        x0, x1 = (1.7, 2.75) if sx > 0 else (-2.75, -1.7)
        m.box(g, (x0, -0.3, 0.5), (x1, 2.9, 10.0), 'carbon', 'panel')
        xa, xb = (2.75, 2.95) if sx > 0 else (-2.95, -2.75)
        m.box('cells_illuminated', (xa, 0.6, 1.4), (xb, 1.9, 9.0), 'cyan_glow', 'gauge')
        m.box(g, (xa - 0.05 * sx, 0.3, 1.0), (xb + 0.05 * sx, 0.6, 9.4), 'gold')
        m.box(g, (xa - 0.05 * sx, 1.9, 1.0), (xb + 0.05 * sx, 2.2, 9.4), 'gold')
    # rails: an upper and a lower bar with the lit bore between them
    m.box(g, (-1.15, 2.2, -27.0), (1.15, 3.05, -5.0), 'steel', 'panel')
    m.box(g, (-1.15, -0.35, -27.0), (1.15, 0.5, -5.0), 'steel', 'panel')
    m.box('bore_illuminated', (-0.45, 0.5, -26.6), (0.45, 2.2, -5.0), 'cyan_glow', skip=('south',))
    m.mirror_x(g, (1.15, -0.45, -24.5), (1.45, 3.15, -5.0), 'darkmetal', 'panel')        # side plates
    # coil collars along the rails
    for i, z in enumerate((-8.0, -11.5, -15.0, -18.5, -22.0)):
        m.box(g, (-1.85, -0.95, z - 0.9), (1.85, 3.65, z), 'copper')
        m.box(g, (-1.95, 1.0, z - 0.7), (1.95, 1.7, z - 0.2), 'gold')
        m.box('bore_illuminated', (-2.0, 1.15, z - 0.6), (2.0, 1.55, z - 0.3), 'cyan_glow')
    # muzzle emitter
    m.box(g, (-2.0, -1.1, -28.4), (2.0, 3.8, -27.0), 'darkmetal', 'rivet')
    m.box('bore_illuminated', (-0.9, 0.3, -28.5), (0.9, 2.4, -28.4), 'cyan_glow', 'lens')
    m.mirror_x(g, (1.35, 3.0, -29.4), (1.75, 3.8, -27.0), 'gold')                          # prongs
    m.mirror_x(g, (1.35, -1.1, -29.4), (1.75, -0.3, -27.0), 'gold')
    # under-rail power line and front handguard (left hand)
    m.box(g, (-1.0, -2.3, -15.0), (1.0, -0.35, -5.0), 'polymer', 'vent')
    m.box(g, (-0.5, -2.6, -14.0), (0.5, -2.3, -6.0), 'blue_glow')
    m.box(g, (-1.3, -2.8, -4.8), (1.3, -1.6, 3.0), 'rubber')
    # slug magazine (the reload animation moves it)
    m.box('magzine', (-1.05, -3.6, 8.2), (1.05, -1.6, 11.6), 'hazard')
    m.box('magzine', (-1.15, -3.9, 8.0), (1.15, -3.6, 11.8), 'darkmetal')
    m.box('magzine', (-0.4, -1.6, 9.0), (0.4, -1.2, 10.8), 'cyan_glow')
    grip(m, g, 13.0)
    # skeleton stock with a lit power spine
    m.box(g, (-1.0, 1.6, 12.0), (1.0, 2.8, 21.0), 'gunmetal', 'panel')
    m.box(g, (-0.8, -2.6, 15.6), (0.8, -1.6, 21.0), 'gunmetal')
    m.box(g, (-1.2, -3.2, 20.6), (1.2, 3.3, 22.2), 'rubber')
    m.box(g, (-0.9, 2.8, 14.5), (0.9, 3.6, 19.5), 'darkmetal', 'trim')                   # cheek rest
    m.box('cells_illuminated', (-0.25, -1.6, 16.0), (0.25, 1.6, 20.4), 'cyan_glow')
    m.box(g, (-0.6, -1.6, 15.8), (-0.25, 1.6, 20.6), 'darkmetal')
    m.box(g, (0.25, -1.6, 15.8), (0.6, 1.6, 20.6), 'darkmetal')
    scope(m, g, -6.0, 6.5)
    return m


# --------------------------------------------------------------------------------------------------------------------
# the laser gun 神罰 (Shinbatsu): white ceramic shell, a prism core in a gold cage, four focusing rings

def laser_gun():
    m = Model('laser_gun', (512, 256))
    skeleton(m, -26.2)
    g = 'gun'
    m.bone('core_illuminated', g, (0, 3.6, 3))
    m.bone('rings_illuminated', g, (0, 1.4, -16))
    # body shell
    m.box(g, (-1.9, -0.9, -6.0), (1.9, 3.2, 12.0), 'ceramic', 'panel')
    m.box(g, (-2.0, 0.6, -5.6), (2.0, 1.4, 11.6), 'polymer')                               # black seam
    m.box(g, (-1.6, -1.8, -6.0), (1.6, -0.9, 8.5), 'ceramic2', 'vent')
    m.mirror_x(g, (1.9, 1.6, -4.0), (2.15, 2.9, 9.0), 'gold', 'engrave')                 # gold side inlays
    # prism core under a gold cage on top
    m.box(g, (-1.5, 3.2, -2.5), (1.5, 3.6, 9.0), 'polymer')
    m.box('core_illuminated', (-0.9, 3.4, -1.5), (0.9, 4.8, 7.0), 'red_glow', skip=('down',))
    for z in (-1.9, 0.8, 3.5, 6.2, 8.4):
        m.box(g, (-1.15, 3.4, z), (1.15, 5.0, z + 0.5), 'gold')
    m.mirror_x(g, (1.0, 4.8, -1.9), (1.15, 5.0, 8.9), 'gold')
    # barrel: a dark focusing tube, four ceramic rings with lit apertures, black heat-sink fins between them
    m.box(g, (-0.95, 0.45, -24.0), (0.95, 2.35, -6.0), 'darkmetal', 'panel')
    for z in (-9.5, -13.5, -17.5, -21.5):
        m.box(g, (-2.05, -0.75, z - 1.1), (2.05, 3.55, z), 'ceramic', 'rivet')
        m.box(g, (-2.15, 0.9, z - 0.85), (2.15, 1.9, z - 0.25), 'polymer')
        m.box('rings_illuminated', (-2.2, 1.15, z - 0.75), (2.2, 1.65, z - 0.35), 'red_glow')
    for z0, z1 in ((-20.4, -17.5), (-16.4, -13.5), (-12.4, -9.5), (-8.4, -6.0)):
        m.box(g, (-0.15, 2.35, z0), (0.15, 3.3, z1), 'polymer')                            # top fin
        m.mirror_x(g, (0.95, 1.2, z0), (1.6, 1.5, z1), 'polymer')                          # side fins
    # muzzle cowl and lens
    m.box(g, (-1.75, -0.6, -25.6), (1.75, 3.4, -23.9), 'ceramic', 'rivet')
    m.box(g, (-1.85, -0.7, -25.9), (1.85, -0.2, -23.6), 'gold')
    m.box('rings_illuminated', (-1.1, 0.3, -25.75), (1.1, 2.5, -25.6), 'glass_red', 'lens')
    # focus-cell bay under the body (the reload animation moves the cell)
    m.box('magzine', (-1.0, -3.4, 7.2), (1.0, -1.8, 11.4), 'ceramic2', 'rivet')
    m.box('magzine', (-0.55, -3.15, 7.6), (0.55, -1.8, 11.0), 'red_glow')
    m.box('magzine', (-1.1, -3.6, 7.0), (1.1, -3.4, 11.6), 'gold')
    # handguard (left hand) and grip
    m.box(g, (-1.35, -2.7, -5.6), (1.35, -1.8, 3.5), 'polymer', 'vent')
    grip(m, g, 13.0, mat='ceramic2', trim='polymer')
    # thumbhole stock
    m.box(g, (-1.1, 1.0, 12.0), (1.1, 3.0, 21.0), 'ceramic', 'panel')
    m.box(g, (-0.9, -2.8, 16.8), (0.9, 1.0, 19.2), 'ceramic')
    m.box(g, (-1.25, -3.4, 19.2), (1.25, 3.2, 21.6), 'polymer')
    m.box(g, (-1.15, 2.1, 12.4), (1.15, 2.6, 18.6), 'gold')
    # reflex sight: frame, gold hood, red dot
    ex, ey = EYE
    m.box(g, (ex - 1.2, 3.2, -0.5), (ex + 1.2, 3.7, 3.5), 'polymer')
    m.box(g, (ex - 1.2, 3.7, -0.5), (ex - 0.9, ey + 1.1, 0.2), 'polymer')
    m.box(g, (ex + 0.9, 3.7, -0.5), (ex + 1.2, ey + 1.1, 0.2), 'polymer')
    m.box(g, (ex - 1.2, ey + 0.8, -0.5), (ex + 1.2, ey + 1.1, 0.2), 'gold')
    m.box('core_illuminated', (ex - 0.12, ey - 0.12, 0.0), (ex + 0.12, ey + 0.12, 0.1), 'red_glow')
    return m


# --------------------------------------------------------------------------------------------------------------------
# software render (icons only)

def _rot(rx, ry, rz):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    X = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Y = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Z = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Z @ Y @ X


def quads(model, hide=('Lefthand', 'Righthand')):
    """Face quads (corners in model space, UV corners in texels, normal, emissive)."""
    out = []
    for c in model.cubes:
        if c.bone in hide:
            continue
        (x0, y0, z0), (x1, y1, z1) = c.lo, c.hi
        corners = {
            'north': ([(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)], (0, 0, -1)),
            'south': ([(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)], (0, 0, 1)),
            'east': ([(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)], (1, 0, 0)),
            'west': ([(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)], (-1, 0, 0)),
            'up': ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], (0, 1, 0)),
            'down': ([(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)], (0, -1, 0)),
        }
        R = _rot(*c.rot) if c.rot else None
        piv = np.array(c.pivot or c.lo, dtype=float)
        for f, (P, n) in corners.items():
            if f not in c.uv:
                continue
            P = np.array(P, dtype=float)
            n = np.array(n, dtype=float)
            if R is not None:
                P = (P - piv) @ R.T + piv
                n = R @ n
            u, v, w, h = c.uv[f]
            UV = [(u, v), (u + w, v), (u + w, v + h), (u, v + h)]
            out.append((P, UV, n, MATS[c.mat][2] == 'glow' or c.bone.endswith('_illuminated')))
    return out


def render(model, img, size, yaw, pitch, mono=None, ss=4, pad=0.06):
    from rig import raster
    T = img.astype(np.float32) / 255.0
    V = _rot(pitch, 0, 0) @ _rot(0, yaw, 0)
    tris = []
    for P, UV, n, e in quads(model):
        Q = P @ V.T
        nv = V @ n
        if nv[2] <= 1e-6:
            continue
        tris.append((Q, UV, nv, e))
    allp = np.concatenate([t[0] for t in tris])
    lo, hi = allp.min(0), allp.max(0)
    W, H = size[0] * ss, size[1] * ss
    sc = min((W * (1 - 2 * pad)) / (hi[0] - lo[0]), (H * (1 - 2 * pad)) / (hi[1] - lo[1]))
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    out = np.zeros((H, W, 3), np.float32)
    cov = np.zeros((H, W), np.float32)
    emit = np.zeros((H, W), np.float32)
    zbuf = np.full((H, W), -1e9, np.float32)
    L = np.array([-0.35, 0.75, 0.55]); L /= np.linalg.norm(L)
    for P, UV, n, e in tris:
        S = np.stack([(P[:, 0] - cx) * sc + W / 2, -(P[:, 1] - cy) * sc + H / 2, P[:, 2]], 1)
        k = 1.0 if e else min(1.3, 0.5 + 0.65 * max(0.0, float(n @ L)) + 0.15)
        for idx in ((0, 1, 2), (0, 2, 3)):
            before = zbuf.copy()
            raster(out, zbuf, S[list(idx)], [UV[i] for i in idx], T, None, 1.0, 1.0, k)
            hit = zbuf != before
            cov[hit] = 1
            emit[hit] = 1.0 if e else 0.0
    rgba = np.zeros((H, W, 4), np.float32)
    rgba[..., :3] = out
    rgba[..., 3] = cov * 255
    if mono is not None:
        g = out.mean(2, keepdims=True)
        tint = np.array(hexc(mono), dtype=np.float32) / 255
        rgba[..., :3] = np.clip(60 + g * 0.9, 0, 255) * tint + emit[..., None] * 90
    im = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), 'RGBA').resize(size, Image.LANCZOS)
    # soft glow halo from the lit parts
    em = Image.fromarray((emit * 255).astype(np.uint8)).resize(size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(max(1, size[0] // 64)))
    halo = np.array(em, dtype=np.float32)[..., None] / 255
    a = np.array(im, dtype=np.float32)
    col = np.array(hexc(model_glow(model)), dtype=np.float32)
    a[..., :3] = np.clip(a[..., :3] + halo * col * 0.55 * (1 - a[..., 3:4] / 255) + halo * col * 0.15, 0, 255)
    a[..., 3] = np.clip(np.maximum(a[..., 3], halo[..., 0] * 160), 0, 255)
    return Image.fromarray(a.astype(np.uint8), 'RGBA')


def model_glow(model):
    return {'railgun': '#4ff3ff', 'laser_gun': '#ff2a4a', 'blueprinter': '#4fb8ff'}.get(model.name, '#ffffff')


def outline(im, colour=(10, 12, 16, 255)):
    a = np.array(im)
    solid = a[..., 3] > 60
    from scipy import ndimage
    ring = ndimage.binary_dilation(solid) & ~solid
    a[ring] = colour
    return Image.fromarray(a, 'RGBA')


# --------------------------------------------------------------------------------------------------------------------
# Superb Warfare resources and item models

def display(first_person):
    return {
        'credit': 'OROR Reborn', 'parent': 'builtin/entity', 'texture_size': [512, 256], 'gui_light': 'front',
        'display': {
            'firstperson_righthand': {'translation': first_person, 'scale': [4, 4, 4]},
            'firstperson_lefthand': {'scale': [0, 0, 0]},
            'thirdperson_righthand': {'translation': [-1.5, 0, -3], 'scale': [0.7, 0.7, 0.7]},
            'thirdperson_lefthand': {'scale': [0, 0, 0]},
            'ground': {'translation': [0, 5.5, 0.25], 'scale': [0.75, 0.75, 0.75]},
            'gui': {'rotation': [30, -145, 0], 'scale': [0.5, 0.5, 0.5]},
            'head': {'translation': [0, 7.75, -3]},
            'fixed': {'rotation': [0, -90, 0], 'translation': [-2, 1, 0], 'scale': [0.6, 0.6, 0.6]},
        }}


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.write('\n')


def gun_assets(out, model, glow_bones, flare_z, flare_size, bar, extra=None):
    name = model.name
    A = os.path.join(out, 'assets', NS)
    pack(model)
    img, glow = paint(model)
    tex = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    os.makedirs(os.path.join(A, 'textures/item'), exist_ok=True)
    os.makedirs(os.path.join(A, 'textures/gun_icon'), exist_ok=True)
    tex.save(os.path.join(A, f'textures/item/{name}.png'))
    write_json(os.path.join(A, f'geo/{name}.geo.json'), geo_json(model, name))
    write_json(os.path.join(A, f'animations/{name}.animation.json'), animations(name, glow_bones))
    resource = {
        'Animation': {'Idle': f'animation.{name}.idle', 'Fire': f'animation.{name}.fire',
                      'Reload': f'animation.{name}.reload', 'Run': f'animation.{name}.run'},
        'Model': {'Animation': f'{NS}:animations/{name}.animation.json', 'Model': f'{NS}:geo/{name}.geo.json',
                  'Texture': f'{NS}:textures/item/{name}.png', 'LODModel': f'{NS}:geo/{name}.geo.json',
                  'LODTexture': f'{NS}:textures/item/{name}.png'},
        'Icon': f'{NS}:textures/gun_icon/{name}_icon.png',
        'FlarePosition': [0, 0, round(-flare_z / 16, 5)], 'FlareSize': flare_size,
        'EnergyBarColor': bar, 'HideCrosshairWhenZoom': False,
    }
    if extra:
        resource.update(extra)
    write_json(os.path.join(A, f'sbw/guns/{name}.json'), resource)
    write_json(os.path.join(A, f'models/displaysettings/{name}.item.json'), display([2.75, -9, -40.25]))
    write_json(os.path.join(A, f'models/item/{name}_base.json'),
               {'parent': f'{NS}:displaysettings/{name}.item', 'textures': {'layer0': f'{NS}:item/{name}'}})
    write_json(os.path.join(A, f'models/item/{name}_icon.json'),
               {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'{NS}:item/{name}_icon'}})
    write_json(os.path.join(A, f'models/item/{name}.json'), {
        'base': {'parent': f'{NS}:item/{name}_base'}, 'gui_light': 'front', 'loader': 'neoforge:separate_transforms',
        'perspectives': {'gui': {'parent': f'{NS}:item/{name}_icon'}}, 'textures': {'particle': f'{NS}:item/{name}_icon'}})
    # icons: the inventory sprite (3/4 view, muzzle to the upper right) and the HUD side view
    icon = render(model, tex_array(tex), (128, 128), yaw=-62, pitch=18, pad=0.04)
    icon = icon.rotate(28, resample=Image.BICUBIC, expand=False)
    outline(icon).save(os.path.join(A, f'textures/item/{name}_icon.png'))
    hud = render(model, tex_array(tex), (256, 64), yaw=-90, pitch=0, mono='#e6eef5', pad=0.05)
    hud.save(os.path.join(A, f'textures/gun_icon/{name}_icon.png'))
    return tex


def tex_array(tex):
    return np.array(tex, dtype=np.float32)


# --------------------------------------------------------------------------------------------------------------------
# the Blueprinter: a vanilla block-model item (cuboids in 16ths of a block), its own 64x64 texture

BP_PARTS = [
    # (from, to, material, rotation or None)
    ((6.5, 3.0, 4.0), (9.5, 7.5, 13.5), 'ceramic', None),          # body
    ((6.2, 5.6, 4.4), (9.8, 6.4, 13.2), 'hazard', None),           # warning band
    ((6.8, 7.5, 6.0), (9.2, 8.6, 11.5), 'polymer', None),          # top deck
    ((7.2, 8.6, 7.0), (8.8, 9.2, 10.5), 'cyan_glow', None),        # scan read-out
    ((7.0, 3.6, 1.5), (9.0, 7.0, 4.0), 'darkmetal', None),         # emitter neck
    ((6.0, 2.8, 0.2), (10.0, 7.8, 1.5), 'gold', None),             # emitter dish rim
    ((6.6, 3.4, -0.2), (9.4, 7.2, 0.2), 'glass_cyan', None),       # emitter lens
    ((7.4, 4.6, -1.6), (8.6, 6.0, -0.2), 'cyan_glow', None),       # holo crystal
    ((7.1, -2.5, 9.5), (8.9, 3.0, 12.0), 'rubber', ('x', -22.5, (8, 3, 10.75))),   # grip
    ((7.6, 1.6, 8.2), (8.4, 3.0, 8.8), 'gold', None),              # trigger
    ((9.5, 3.6, 5.0), (10.2, 7.0, 12.0), 'darkmetal', None),       # side screen frame
    ((10.2, 4.0, 5.6), (10.4, 6.6, 11.4), 'blue_glow', None),      # side screen
    ((5.8, 3.6, 7.0), (6.5, 6.8, 12.6), 'gold', None),             # cartridge door
]


def blueprinter(out):
    A = os.path.join(out, 'assets', NS)
    S = 64
    img = np.zeros((S, S, 4), np.float32)
    glow = np.zeros((S, S), np.uint8)
    elements = []
    # one 8x8 swatch per material, painted like the gun faces
    swatches = {}
    for i, mat in enumerate(sorted({p[2] for p in BP_PARTS})):
        u, v = (i % 8) * 8, (i // 8) * 8
        c = Cube('x', (0, 0, 0), (2, 2, 2), mat, seed=i * 7)
        c.uv = {'east': (u, v, 8, 8)}
        paint_face(img, glow, c, 'east')
        swatches[mat] = (u / 4, v / 4, (u + 8) / 4, (v + 8) / 4)       # in the 0-16 UV space of a 64px texture
    for lo, hi, mat, rot in BP_PARTS:
        e = {'from': list(lo), 'to': list(hi),
             'faces': {f: {'uv': list(swatches[mat]), 'texture': '#0'} for f in ('north', 'south', 'east', 'west', 'up', 'down')}}
        if rot:
            axis, ang, origin = rot
            e['rotation'] = {'angle': ang, 'axis': axis, 'origin': list(origin)}
        if mat.endswith('glow') or mat.startswith('glass'):
            e['light_emission'] = 15
        elements.append(e)
    os.makedirs(os.path.join(A, 'textures/item'), exist_ok=True)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(A, 'textures/item/blueprinter.png'))
    write_json(os.path.join(A, 'models/item/blueprinter.json'), {
        'credit': 'OROR Reborn', 'texture_size': [64, 64], 'gui_light': 'side',
        'textures': {'0': f'{NS}:item/blueprinter', 'particle': f'{NS}:item/blueprinter'},
        'elements': elements,
        'display': {
            'thirdperson_righthand': {'rotation': [0, 180, 0], 'translation': [0, 3, 1.5], 'scale': [0.85, 0.85, 0.85]},
            'thirdperson_lefthand': {'rotation': [0, 180, 0], 'translation': [0, 3, 1.5], 'scale': [0.85, 0.85, 0.85]},
            'firstperson_righthand': {'rotation': [0, 172, 0], 'translation': [2.5, 2.5, 0], 'scale': [0.9, 0.9, 0.9]},
            'firstperson_lefthand': {'rotation': [0, 172, 0], 'translation': [2.5, 2.5, 0], 'scale': [0.9, 0.9, 0.9]},
            'ground': {'translation': [0, 2, 0], 'scale': [0.6, 0.6, 0.6]},
            'gui': {'rotation': [25, 140, 0], 'translation': [0.5, 0.5, 0], 'scale': [1.15, 1.15, 1.15]},
            'fixed': {'rotation': [0, 90, 0], 'scale': [1, 1, 1]},
        }})


# --------------------------------------------------------------------------------------------------------------------
# ammunition sprites, 32x32 pixel art with a dark outline

def _sprite(draw):
    a = np.zeros((32, 32, 4), np.uint8)
    draw(a)
    return outline(Image.fromarray(a, 'RGBA'), (14, 12, 18, 255))


def _put(a, x, y, c):
    if 0 <= x < 32 and 0 <= y < 32:
        a[y, x, :3] = hexc(c)
        a[y, x, 3] = 255


def _diag_bar(a, t0, t1, r, colour_at):
    """A round bar along the sprite diagonal from (t0) lower left to (t1) upper right."""
    for y in range(32):
        for x in range(32):
            # coordinates along / across the diagonal
            s = (x + (31 - y)) / 2.0
            d = (x - (31 - y)) / 1.4142
            if t0 <= s <= t1 and abs(d) <= r:
                col = colour_at(s, d / r)
                if col:
                    _put(a, x, y, col)


def rail_slug(a):
    def col(s, d):
        light = 1.2 - 0.45 * (d + 1) / 2
        if s > 26.5:
            return shade('#7ff6ff', 1.1) if abs(d) < 0.55 else shade('#2aa6c8', light)
        if s > 24.5:
            return shade('#e2b84a', light)
        if 9 < s < 11 or 16 < s < 18:
            return shade('#b86b3a', light * (1.1 if int(s * 2) % 2 else 0.8))
        if s < 5.5:
            return shade('#e2b84a', light) if abs(d) > 0.4 else shade('#23272f', 1)
        return shade('#5d6876', light + (0.15 if abs(d + 0.45) < 0.2 else 0))
    _diag_bar(a, 3, 29.5, 3.2, col)


def focus_cell(a):
    def col(s, d):
        light = 1.15 - 0.4 * (d + 1) / 2
        if s < 7 or s > 25:
            return shade('#e2b84a' if abs(d) > 0.5 else '#e9e7e1', light)
        if 7 <= s < 8.5 or 23.5 < s <= 25:
            return shade('#23272f', 1)
        core = 1 - abs(d)
        return mix(shade('#ff2a4a', 0.75 + 0.5 * core), (255, 236, 240), max(0.0, core - 0.45) * 1.4)
    _diag_bar(a, 4, 28, 4.2, col)
    for (x, y) in ((22, 6), (24, 9), (9, 22), (6, 24)):
        _put(a, x, y, '#ffd36a')


def matter_cartridge(a):
    for y in range(5, 29):
        for x in range(8, 24):
            edge = x in (8, 23)
            t = (x - 8) / 15
            col = shade('#7d8894', 1.2 - 0.45 * t)
            if y in (5, 6, 27, 28):
                col = shade('#e2b84a', 1.15 - 0.4 * t)
            elif 10 <= y <= 22 and 11 <= x <= 20:
                core = 1 - abs((x - 15.5) / 5)
                col = mix(shade('#3b8dff', 0.8 + 0.4 * core), (220, 245, 255), max(0.0, core - 0.5) * 1.2)
                if (y - 10) % 4 == 0:
                    col = mix(col, (255, 255, 255), 0.35)
            elif y in (8, 24):
                col = '#1b1b1e' if (x + y) // 2 % 2 else '#e8c22c'
            if edge:
                col = shade(col, 0.7)
            _put(a, x, y, col)
    for x in range(12, 20):
        _put(a, x, 3, '#c79a3c')
        _put(a, x, 4, '#e2b84a')


def sprites(out):
    A = os.path.join(out, 'assets', NS)
    os.makedirs(os.path.join(A, 'textures/item'), exist_ok=True)
    for name, draw in (('rail_slug', rail_slug), ('focus_cell', focus_cell), ('matter_cartridge', matter_cartridge)):
        _sprite(draw).save(os.path.join(A, f'textures/item/{name}.png'))
        write_json(os.path.join(A, f'models/item/{name}.json'),
                   {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'{NS}:item/{name}'}})


# --------------------------------------------------------------------------------------------------------------------
# data: Superb Warfare gun data, recipes and tags

SBW = [{'type': 'neoforge:mod_loaded', 'modid': 'superbwarfare'}]

GUN_DATA = {
    'railgun': {
        'ID': f'{NS}:railgun', 'MaxEnergy': 1000000, 'Damage': 1600, 'Headshot': 2, 'BypassesArmor': 1,
        'Velocity': 400, 'Range': 512, 'Magazine': 1, 'AmmoCostPerShoot': 1, 'Projectile': 'empty',
        'AmmoType': f'{NS}:rail_slug', 'ShootDelay': 30, 'RPM': 20, 'DefaultZoom': 4, 'MinZoom': 2, 'MaxZoom': 10,
        'Spread': 0, 'ZoomSpreadRate': 0, 'RecoilX': 0.012, 'RecoilY': 0.09, 'Recoil': 0.8, 'Weight': 9,
        'NormalReloadTime': 52, 'EmptyReloadTime': 52, 'SoundRadius': 64, 'GunType': 'Sniper',
        'DefaultFireMode': 'Semi', 'AvailableFireModes': ['Semi'], 'AvailablePerks': [],
        'Icon': f'{NS}:textures/gun_icon/railgun_icon.png',
        'SoundInfo': {
            'Fire1P': 'superbwarfare:annihilator_fire_1p', 'Fire3P': 'superbwarfare:annihilator_fire_3p',
            'Fire3PFar': 'superbwarfare:annihilator_far', 'Fire3PVeryFar': 'superbwarfare:annihilator_veryfar',
            'ReloadNormal': 'superbwarfare:sentinel_reload_normal', 'ReloadEmpty': 'superbwarfare:sentinel_reload_empty',
            'CancellableSounds': ['superbwarfare:sentinel_reload_normal', 'superbwarfare:sentinel_reload_empty']},
    },
    'laser_gun': {
        'ID': f'{NS}:laser_gun', 'MaxEnergy': 600000, 'Damage': 1000, 'Headshot': 1.5, 'BypassesArmor': 1,
        'Velocity': 400, 'Range': 256, 'Magazine': 1, 'AmmoCostPerShoot': 1, 'Projectile': 'empty',
        'AmmoType': f'{NS}:focus_cell', 'ShootDelay': 20, 'RPM': 20, 'DefaultZoom': 2, 'MinZoom': 1.25, 'MaxZoom': 4,
        'Spread': 0, 'ZoomSpreadRate': 0, 'RecoilX': 0.004, 'RecoilY': 0.035, 'Weight': 6,
        'NormalReloadTime': 52, 'EmptyReloadTime': 52, 'SoundRadius': 48, 'GunType': 'Special',
        'DefaultFireMode': 'Semi', 'AvailableFireModes': ['Semi'], 'AvailablePerks': [],
        'Icon': f'{NS}:textures/gun_icon/laser_gun_icon.png',
        'SoundInfo': {
            'Fire1P': 'superbwarfare:secondary_cataclysm_fire_1p_charge', 'Fire3P': 'superbwarfare:laser_tower_shoot',
            'Fire3PFar': 'superbwarfare:secondary_cataclysm_far_charge',
            'Fire3PVeryFar': 'superbwarfare:secondary_cataclysm_veryfar_charge',
            'ReloadNormal': 'superbwarfare:sentinel_reload_normal', 'ReloadEmpty': 'superbwarfare:sentinel_reload_empty',
            'CancellableSounds': ['superbwarfare:sentinel_reload_normal', 'superbwarfare:sentinel_reload_empty']},
    },
}


def shaped(result, pattern, key, conditions=None, count=1):
    r = {}
    if conditions:
        r['neoforge:conditions'] = conditions
    r.update({'type': 'minecraft:crafting_shaped', 'category': 'equipment', 'pattern': pattern,
              'key': {k: ({'tag': v[1:]} if v.startswith('#') else {'item': v}) for k, v in key.items()},
              'result': {'id': f'{NS}:{result}', 'count': count}})
    return r


RECIPES = {
    # 天穿: two netherite barrels, a nether star, the netherite action and trigger, a legendary material pack,
    # two large battery packs and OROR's dragon furnace core
    'railgun': shaped('railgun', ['BSB', 'ALT', 'PDP'], {
        'B': 'superbwarfare:netherite_barrel', 'S': 'minecraft:nether_star', 'A': 'superbwarfare:netherite_action',
        'L': 'superbwarfare:legendary_material_pack', 'T': 'superbwarfare:netherite_trigger',
        'P': 'superbwarfare:large_battery_pack', 'D': f'{NS}:dragon_core'}, SBW),
    # 神罰: crystal barrels round a beacon, an ancient CPU, the crystal action and trigger, a legendary material pack,
    # two large battery packs
    'laser_gun': shaped('laser_gun', ['CKC', 'URA', 'PTP'], {
        'C': 'superbwarfare:crystal_barrel', 'K': 'minecraft:beacon', 'U': 'superbwarfare:ancient_cpu',
        'R': 'superbwarfare:legendary_material_pack', 'A': 'superbwarfare:crystal_action',
        'P': 'superbwarfare:large_battery_pack', 'T': 'superbwarfare:crystal_trigger'}, SBW),
    # one slug: a netherite ingot, a diamond, six cemented carbide ingots and a cell
    'rail_slug': shaped('rail_slug', ['CNC', 'CDC', 'CEC'], {
        'C': 'superbwarfare:cemented_carbide_ingot', 'N': 'minecraft:netherite_ingot', 'D': 'minecraft:diamond',
        'E': 'superbwarfare:cell'}, SBW),
    # one focus cell: two end crystals, two diamonds, four gold ingots and a cell
    'focus_cell': shaped('focus_cell', ['GDG', 'ECE', 'GDG'], {
        'G': 'minecraft:gold_ingot', 'D': 'minecraft:diamond', 'E': 'minecraft:end_crystal', 'C': 'superbwarfare:cell'}, SBW),
    # one cartridge (256 units): a netherite ingot, four diamonds and four obsidian
    'matter_cartridge': shaped('matter_cartridge', ['DOD', 'ONO', 'DOD'], {
        'D': 'minecraft:diamond', 'O': 'minecraft:obsidian', 'N': 'minecraft:netherite_ingot'}),
    # the Blueprinter: a nether star between two of OROR's forge cores, ender eyes, an ancient CPU, a legendary
    # material pack and two large battery packs
    'blueprinter': shaped('blueprinter', ['EAE', 'FSF', 'BLB'], {
        'E': 'minecraft:ender_eye', 'A': 'superbwarfare:ancient_cpu', 'F': f'{NS}:forge_core', 'S': 'minecraft:nether_star',
        'B': 'superbwarfare:large_battery_pack', 'L': 'superbwarfare:legendary_material_pack'}, SBW),
}

UNPRINTABLE = ['#c:ores', '#c:storage_blocks', '#minecraft:shulker_boxes', 'minecraft:beacon', 'minecraft:spawner',
               'minecraft:trial_spawner', 'minecraft:vault', 'minecraft:dragon_egg', 'minecraft:conduit',
               'minecraft:budding_amethyst', 'minecraft:ancient_debris', 'minecraft:reinforced_deepslate',
               'minecraft:end_portal_frame', 'minecraft:end_portal', 'minecraft:nether_portal', 'minecraft:end_gateway',
               'minecraft:command_block', 'minecraft:chain_command_block', 'minecraft:repeating_command_block',
               'minecraft:structure_block', 'minecraft:jigsaw', 'minecraft:barrier', 'minecraft:light',
               'minecraft:bedrock', 'minecraft:respawn_anchor', 'minecraft:lodestone', 'minecraft:heavy_core',
               'minecraft:suspicious_sand', 'minecraft:suspicious_gravel']
COSTLY = ['#minecraft:anvil', '#minecraft:rails', '#minecraft:cauldrons', 'minecraft:hopper', 'minecraft:iron_door',
          'minecraft:iron_trapdoor', 'minecraft:iron_bars', 'minecraft:chain', 'minecraft:jukebox',
          'minecraft:enchanting_table', 'minecraft:ender_chest', 'minecraft:crying_obsidian', 'minecraft:obsidian',
          'minecraft:bell', 'minecraft:lightning_rod', 'minecraft:heavy_weighted_pressure_plate',
          'minecraft:light_weighted_pressure_plate', 'minecraft:piston', 'minecraft:sticky_piston', 'minecraft:observer',
          'minecraft:comparator', 'minecraft:daylight_detector', 'minecraft:tnt', 'minecraft:sea_lantern',
          'minecraft:glowstone', 'minecraft:redstone_lamp', 'minecraft:end_rod', 'minecraft:blast_furnace',
          'minecraft:smithing_table', 'minecraft:grindstone', 'minecraft:stonecutter', 'minecraft:lantern',
          'minecraft:soul_lantern', 'minecraft:target', 'minecraft:brewing_stand', 'minecraft:copper_bulb',
          'minecraft:crafter', 'minecraft:amethyst_block', 'minecraft:honey_block', 'minecraft:slime_block',
          'minecraft:sculk_sensor', 'minecraft:calibrated_sculk_sensor', 'minecraft:sculk_shrieker',
          'minecraft:sculk_catalyst', 'minecraft:end_stone_bricks', 'minecraft:purpur_block', 'minecraft:prismarine',
          'minecraft:prismarine_bricks', 'minecraft:dark_prismarine', 'minecraft:shroomlight', 'minecraft:ochre_froglight',
          'minecraft:verdant_froglight', 'minecraft:pearlescent_froglight']


def data(out):
    D = os.path.join(out, 'data')
    for name, d in GUN_DATA.items():
        write_json(os.path.join(D, NS, f'sbw/guns/{name}.json'), d)
    for name, r in RECIPES.items():
        write_json(os.path.join(D, NS, f'recipe/{name}.json'), r)
    write_json(os.path.join(D, NS, 'tags/block/blueprinter_unprintable.json'), {'replace': False, 'values': UNPRINTABLE})
    write_json(os.path.join(D, NS, 'tags/block/blueprinter_costly.json'), {'replace': False, 'values': COSTLY})
    write_json(os.path.join(D, 'superbwarfare', 'tags/item/gun.json'), {'replace': False, 'values': [
        {'id': f'{NS}:railgun', 'required': False}, {'id': f'{NS}:laser_gun', 'required': False}]})


def main(out):
    gun_assets(out, railgun(), ['bore_illuminated', 'cells_illuminated'], -28.6, 1.4, '0x4FF3FF')
    gun_assets(out, laser_gun(), ['core_illuminated', 'rings_illuminated'], -26.2, 0.9, '0xFF2A4A')
    blueprinter(out)
    sprites(out)
    data(out)


if __name__ == '__main__':
    main(sys.argv[1])

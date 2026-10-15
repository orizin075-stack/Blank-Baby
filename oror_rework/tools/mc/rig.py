"""Rig model: bones with Minecraft ModelPart semantics, box-UV packing, JSON export and a
software preview renderer that reproduces ModelPart.Cube vertex/UV mapping exactly."""
import json, math
import numpy as np
from PIL import Image

def texels(v):
    """Box sizes are whole texels; anything thinner than a quarter texel becomes a flat plane."""
    if v < 0.25:
        return 0.0
    return float(max(1, math.floor(v + 0.5)))

class Cube:
    def __init__(self, bone, origin, size, mat, glow=None, faces=None, name='', grow=0.0):
        self.bone, self.origin, self.size, self.mat = bone, tuple(origin), tuple(size), mat
        self.grow = grow
        self.glow = glow          # optional glow painter key/params
        self.faces = faces        # optional dict face->painter override
        self.name = name
        self.uv = None            # (u, v) integer texture offset in layout units

    # Face rectangles in layout units, following ModelPart.Cube: name -> (u0, v0, w, h)
    def rects(self):
        u, v = self.uv
        w, h, d = self.size
        return {
            'top':    (u + d,         v,     w, d),
            'bottom': (u + d + w,     v,     w, d),
            'right':  (u,             v + d, d, h),   # WEST  (-X) = character's right side
            'front':  (u + d,         v + d, w, h),   # NORTH (-Z)
            'left':   (u + d + w,     v + d, d, h),   # EAST  (+X) = character's left side
            'back':   (u + 2 * d + w, v + d, w, h),   # SOUTH (+Z)
        }

    def footprint(self):
        w, h, d = self.size
        return math.ceil(2 * (d + w) - 1e-6), math.ceil(d + h - 1e-6)

class Bone:
    def __init__(self, rig, name, parent, pivot, rot, anim, params):
        self.rig, self.name, self.parent = rig, name, parent
        self.pivot = tuple(pivot)        # absolute model coordinates (y down, feet at 24)
        self.rot = tuple(rot)            # rest rotation (radians) x, y, z
        self.anim, self.params = anim, params
        self.scale = (1.0, 1.0, 1.0)
        self.cubes = []

    def box(self, origin, size, mat, glow=None, name='', grow=0.0, **kw):
        """origin is absolute model coordinates of the min corner. Sizes snap to whole texels."""
        size = tuple(texels(v) for v in size)
        o = tuple(round((origin[i] - self.pivot[i]) * 4) / 4 for i in range(3))
        c = Cube(self, o, size, mat, glow, kw.get('faces'), name, grow)
        self.cubes.append(c)
        return c

    def cbox(self, center, size, mat, glow=None, name='', grow=0.0, **kw):
        """box given by its center."""
        size = tuple(texels(v) for v in size)
        return self.box(tuple(center[i] - size[i] / 2 for i in range(3)), size, mat, glow, name, grow, **kw)

class Rig:
    def __init__(self, key, texture=None, layout=(128, 128), density=1, height=None, translucent=False):
        self.key, self.texture = key, texture or key
        self.layout, self.density = layout, density
        self.height, self.translucent = height, translucent
        self.bones = []
        self.by_name = {}

    def bone(self, name, parent=None, pivot=(0, 0, 0), rot=(0, 0, 0), anim=None, scale=None, **params):
        if name in self.by_name:
            base, i = name, 2
            while f'{base}{i}' in self.by_name:
                i += 1
            name = f'{base}{i}'
        p = self.by_name[parent] if isinstance(parent, str) else parent
        b = Bone(self, name, p, pivot, rot, anim, params)
        if scale is not None:
            b.scale = tuple(scale) if isinstance(scale, (tuple, list)) else (scale, scale, scale)
        self.bones.append(b)
        self.by_name[name] = b
        return b

    def cubes(self):
        return [c for b in self.bones for c in b.cubes]

    # ---------- UV packing (shelf packer, tallest first) ----------
    def pack(self):
        W, H = self.layout
        items = sorted(self.cubes(), key=lambda c: (-c.footprint()[1], -c.footprint()[0]))
        x = y = shelf = 0
        for c in items:
            fw, fh = c.footprint()
            fw += 1; fh += 1
            if fw > W:
                raise ValueError(f'{self.key}: cube too wide for layout {c.size}')
            if x + fw > W:
                x, y, shelf = 0, y + shelf, 0
            if y + fh > H:
                raise ValueError(f'{self.key}: layout {self.layout} full')
            c.uv = (x, y)
            x += fw
            shelf = max(shelf, fh)
        return self

    # ---------- export ----------
    def to_json(self):
        bones = []
        for b in self.bones:
            pp = b.parent.pivot if b.parent else (0, 0, 0)
            extra = {'sc': [round(v, 5) for v in b.scale]} if b.scale != (1.0, 1.0, 1.0) else {}
            bones.append({**extra,
                'name': b.name,
                'parent': b.parent.name if b.parent else None,
                'at': [round(b.pivot[i] - pp[i], 4) for i in range(3)],
                'rot': [round(r, 5) for r in b.rot],
                'anim': b.anim or '',
                'p': {k: v for k, v in b.params.items()},
                'cubes': [dict({'uv': list(c.uv), 'o': [round(v, 4) for v in c.origin], 's': [round(v, 4) for v in c.size]},
                               **({'g': round(c.grow, 4)} if c.grow else {})) for c in b.cubes],
            })
        top = self.model_top()
        return {'texture': self.texture, 'size': list(self.layout), 'height': round(self.height or (24 - top), 3),
                'translucent': self.translucent, 'bones': bones}

    def model_top(self):
        lo = 1e9
        for b in self.bones:
            for c in b.cubes:
                lo = min(lo, b.pivot[1] + c.origin[1])
        return lo

# ---------------------------------------------------------------- preview renderer
def rot_zyx(x, y, z):
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx

def bone_matrices(rig, pose=None):
    """4x4 transforms (model units) mirroring ModelPart.translateAndRotate down the hierarchy."""
    pose = pose or {}
    mats = {}
    for b in rig.bones:
        pp = b.parent.pivot if b.parent else (0, 0, 0)
        rx, ry, rz = b.rot
        dx, dy, dz = pose.get(b.name, (0, 0, 0))
        M = np.eye(4)
        M[:3, 3] = [b.pivot[i] - pp[i] for i in range(3)]
        R = np.eye(4); R[:3, :3] = rot_zyx(rx + dx, ry + dy, rz + dz)
        S = np.diag([*b.scale, 1.0])
        local = M @ R @ S
        mats[b.name] = (mats[b.parent.name] @ local) if b.parent else local
    return mats

def cube_quads(c):
    """Return list of (4 vertices local, 4 uv) exactly as ModelPart.Cube/Polygon build them."""
    g = c.grow
    w, h, d = c.size
    ox, oy, oz = c.origin[0] - g, c.origin[1] - g, c.origin[2] - g
    x1, y1, z1 = c.origin[0] + w + g, c.origin[1] + h + g, c.origin[2] + d + g
    v0 = (ox, oy, oz); v1 = (x1, oy, oz); v2 = (x1, y1, oz); v3 = (ox, y1, oz)
    v4 = (ox, oy, z1); v5 = (x1, oy, z1); v6 = (x1, y1, z1); v7 = (ox, y1, z1)
    u, v = c.uv
    U0, U1, U2, U3, U4, U5 = u, u + d, u + d + w, u + d + 2 * w, u + 2 * d + w, u + 2 * d + 2 * w
    V0, V1, V2 = v, v + d, v + d + h
    def poly(vs, ua, va, ub, vb, n):
        return (vs, [(ub, va), (ua, va), (ua, vb), (ub, vb)], n)
    return [
        poly([v5, v4, v0, v1], U1, V0, U2, V1, (0, -1, 0)),   # DOWN  (visual top)
        poly([v2, v3, v7, v6], U2, V1, U3, V0, (0, 1, 0)),    # UP    (visual bottom)
        poly([v0, v4, v7, v3], U0, V1, U1, V2, (-1, 0, 0)),   # WEST
        poly([v1, v0, v3, v2], U1, V1, U2, V2, (0, 0, -1)),   # NORTH (front)
        poly([v5, v1, v2, v6], U2, V1, U4, V2, (1, 0, 0)),    # EAST
        poly([v4, v5, v6, v7], U4, V1, U5, V2, (0, 0, 1)),    # SOUTH
    ]

def render(rig, tex, yaw_deg=25.0, pitch_deg=8.0, size=(420, 560), glow=None, pose=None, bg=(46, 48, 58), blink=False, frame=None, cull=True):
    W, H = size
    img = np.zeros((H, W, 3), np.float32); img[:] = bg
    zbuf = np.full((H, W), -1e9, np.float32)
    T = np.asarray(tex.convert('RGBA'), np.float32) / 255.0
    G = np.asarray(glow.convert('RGBA'), np.float32) / 255.0 if glow is not None else None
    th, tw = T.shape[:2]
    LW, LH = rig.layout
    mats = bone_matrices(rig, pose)
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)
    # world = (x, -y, -z) of model, then view rotation (camera in front, at +Z)
    Vy = rot_zyx(0, yaw, 0); Vx = rot_zyx(pitch, 0, 0)
    tris = []
    for b in rig.bones:
        M = mats[b.name]
        if b.anim == 'blink' and not blink:
            continue
        for c in b.cubes:
            for vs, uvs, n in cube_quads(c):
                P = np.array([M @ np.array([*p, 1.0]) for p in vs])[:, :3]
                P = P * np.array([1, -1, -1])
                N = (M[:3, :3] @ np.array(n, float)) * np.array([1, -1, -1])
                nn = np.linalg.norm(N)
                N = N / nn if nn > 1e-9 else N
                P = (Vx @ (Vy @ P.T)).T
                Nv = Vx @ (Vy @ N)
                if cull and Nv[2] <= 1e-6:
                    continue          # in-game rigs render with RenderType.entityCutout (back faces culled)
                tris.append((P, uvs, N))
    allp = np.concatenate([t[0] for t in tris])
    lo, hi = allp.min(0), allp.max(0)
    if frame is not None:
        cx, cy, span = frame
    else:
        span = max(hi[0] - lo[0], (hi[1] - lo[1]) * W / H) * 1.08
        cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    sc = W / span if span > 0 else 1
    # Minecraft entity lighting: two fixed directional lights, ambient 0.4 + diffuse 0.6
    L0 = np.array([0.2, 1.0, 0.7]); L0 /= np.linalg.norm(L0)
    L1 = np.array([-0.2, 1.0, -0.7]); L1 /= np.linalg.norm(L1)
    for P, uvs, N in tris:
        S = np.stack([(P[:, 0] - cx) * sc + W / 2, -(P[:, 1] - cy) * sc + H / 2, P[:, 2]], 1)
        shade = min(1.0, 0.4 + 0.6 * (max(0.0, float(N @ L0)) + max(0.0, float(N @ L1))))
        for idx in ((0, 1, 2), (0, 2, 3)):
            raster(img, zbuf, S[list(idx)], [uvs[i] for i in idx], T, G, tw / LW, th / LH, shade)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def raster(img, zbuf, S, uv, T, G, kx, ky, shade):
    H, W = zbuf.shape
    x0, x1 = int(max(0, math.floor(S[:, 0].min()))), int(min(W - 1, math.ceil(S[:, 0].max())))
    y0, y1 = int(max(0, math.floor(S[:, 1].min()))), int(min(H - 1, math.ceil(S[:, 1].max())))
    if x1 < x0 or y1 < y0:
        return
    (ax, ay, az), (bx, by, bz), (qx, qy, qz) = S
    den = (by - qy) * (ax - qx) + (qx - bx) * (ay - qy)
    if abs(den) < 1e-9:
        return
    xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
    w0 = ((by - qy) * (xs - qx) + (qx - bx) * (ys - qy)) / den
    w1 = ((qy - ay) * (xs - qx) + (ax - qx) * (ys - qy)) / den
    w2 = 1 - w0 - w1
    m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
    if not m.any():
        return
    z = w0 * az + w1 * bz + w2 * qz
    u = (w0 * uv[0][0] + w1 * uv[1][0] + w2 * uv[2][0]) * kx
    v = (w0 * uv[0][1] + w1 * uv[1][1] + w2 * uv[2][1]) * ky
    ui = np.clip(u.astype(int), 0, T.shape[1] - 1); vi = np.clip(v.astype(int), 0, T.shape[0] - 1)
    col = T[vi, ui]
    m &= col[..., 3] > 0.1
    zb = zbuf[y0:y1 + 1, x0:x1 + 1]
    m &= z > zb
    if not m.any():
        return
    rgb = col[..., :3] * 255 * shade
    if G is not None:
        g = G[vi, ui]
        rgb = rgb + g[..., :3] * g[..., 3:4] * 255
    a = col[..., 3:4]
    region = img[y0:y1 + 1, x0:x1 + 1]
    blended = rgb * a + region * (1 - a)
    region[m] = blended[m]
    zb[m] = z[m]

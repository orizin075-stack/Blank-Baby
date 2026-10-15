"""Sculpted 3D items for NeoForge's OBJ loader.

A weapon is designed in weapon space, in texels (TPB texels per block): u runs up the weapon's axis from
the grip point (u = 0, where the hand closes), v runs across it (+v = right as drawn) and w is depth
(+w = towards the viewer of the drawings). Two kinds of parts:

  * boxes (any rotation, nested groups) painted with the box-UV painters of paint.py;
  * relief plates: pixel-art drawings (pixart.Art) extruded into bevelled slabs (relief.py).

export() packs everything into one texture, splits glowing texels into full-bright quads (material
'glow', Ka 1 1 1 -> NeoForge emissive_ambient) and writes OBJ + PNG. preview() renders the exact quads.
"""
import math, os
import numpy as np
from PIL import Image
from rig import Rig, bone_matrices, cube_quads, raster, rot_zyx
from paint import paint_rig, GLOW_K
import pixart as PA
import relief as RL

TPB = 32                       # texels per block

def rig_pos(u, v, w):
    return (v, -u, -w)

# ------------------------------------------------------------------------------------------- plates
class Plate:
    def __init__(self, owner, bone, umin, umax, vmin, vmax, at, U, V, pad=1):
        self.owner, self.bone = owner, bone
        W = int(math.ceil(vmax - vmin)) + 2 * pad
        H = int(math.ceil(umax - umin)) + 2 * pad
        self.ox, self.oy = pad - vmin, pad + umax
        self.art = PA.Art(PA.Frame(W, H, (self.ox, self.oy), (0, -1), 1.0))
        self.at = np.array(at, float)          # rig coords (absolute, rest frame of the bone) of design (0, 0)
        self.U = np.array(U, float) / np.linalg.norm(U)
        self.V = np.array(V, float) / np.linalg.norm(V)

    def __getattr__(self, k):                  # poly, sym, ell, ring, stroke, curve, dot
        return getattr(self.art, k)

    def corner(self):
        """rig position of pixel corner (0, 0), and the pixel axes."""
        Rv = self.V
        Dv = -self.U
        O = self.at + self.oy * self.U - self.ox * self.V
        return O, Rv, Dv, np.cross(Rv, Dv)

# ------------------------------------------------------------------------------------------- builder
class Group:
    """A frame in weapon space: origin (u, v, w) and a rest rotation (degrees about the u, v, w axes)."""
    def __init__(self, w3d, bone, origin_rig):
        self.w3d, self.b, self.o = w3d, bone, np.array(origin_rig, float)

    def _abs(self, u, v, w):
        return self.o + np.array(rig_pos(u, v, w), float)

    def group(self, u=0, v=0, w=0, rot=(0, 0, 0), name='g'):
        """rot = (about u, about v, about w) in degrees, applied in the parent's frame (ZYX like ModelPart)."""
        ru, rv, rw = (math.radians(a) for a in rot)
        piv = self._abs(u, v, w)
        b = self.w3d.rig.bone(name, self.b, tuple(piv), rot=(rv, -ru, -rw))
        return Group(self.w3d, b, piv)

    def box(self, u, v, w, du, dv, dw, mat, rot=None, grow=0.0, name='part', **kw):
        """Box centred at (u, v, w) with extents du (along the axis), dv (across), dw (depth)."""
        if rot:
            return self.group(u, v, w, rot, name=name + '_r').box(0, 0, 0, du, dv, dw, mat, grow=grow, name=name, **kw)
        c = self._abs(u, v, w)
        return self.b.cbox(tuple(c), (dv, du, dw), mat, name=name, grow=grow, **kw)

    def plate(self, umin, umax, vmin, vmax, u=0, v=0, w=0, U=(1, 0, 0), V=(0, 1, 0)):
        """Relief plate drawn in its own (u', v') design coords; (0, 0) sits at (u, v, w). U and V give the
        directions of u' and v' in weapon (u, v, w) coordinates; default = the main drawing plane."""
        Ur = np.array(rig_pos(*U), float)
        Vr = np.array(rig_pos(*V), float)
        p = Plate(self, self.b, umin, umax, vmin, vmax, self._abs(u, v, w), Ur, Vr)
        self.w3d.plates.append(p)
        return p

class W3D(Group):
    def __init__(self, key):
        self.key = key
        self.rig = Rig(key, layout=(64, 64))
        self.plates = []
        root = self.rig.bone('root', None, (0, 0, 0))
        super().__init__(self, root, (0, 0, 0))

    # ------------------------------------------------------------------ geometry + texture
    def build(self):
        """Returns (quads, atlas_rgba uint8, size). quads: (P[4] rig coords, UV[4] atlas px, normal rig, emissive)."""
        tex = glow = None
        if self.rig.cubes():
            for s in ((32, 32), (64, 32), (64, 64), (128, 64), (128, 128), (256, 128), (256, 256), (512, 256)):
                self.rig.layout = s
                try:
                    self.rig.pack()
                    break
                except ValueError:
                    pass
            tex, glow = paint_rig(self.rig)
        imgs = []
        if tex is not None:
            t = np.asarray(tex, np.float32).copy()
            g = np.asarray(glow, np.float32)
            em = (g[..., 3] > 0) & (g[..., :3].max(-1) > 24) & (t[..., 3] > 0)
            t[..., :3] = np.where(em[..., None], np.clip(t[..., :3] * 0.55 + g[..., :3] / GLOW_K * 0.75, 0, 255), t[..., :3])
            uw = uh = 1
            for c in self.rig.cubes():
                fw, fh = c.footprint()
                uw, uh = max(uw, c.uv[0] + fw), max(uh, c.uv[1] + fh)
            imgs.append(('rig', t[:uh, :uw].astype(np.uint8), em[:uh, :uw]))
        plate_data = []
        for i, p in enumerate(self.plates):
            rgba, gl = p.art.render()
            D, owner = RL.depth_map_smooth(p.art)
            em = RL.emissive_map(rgba, gl)
            rgba = rgba.copy()
            if em.any():
                bright = np.clip(rgba[..., :3].astype(np.float32) * 0.7 + gl[..., :3] * 0.6, 0, 255)
                rgba[..., :3] = np.where(em[..., None], bright, rgba[..., :3]).astype(np.uint8)
            imgs.append((f'p{i}', rgba, em))
            plate_data.append((p, rgba, D, em, owner))
        # ---- atlas (shelf packing, power of two)
        order = sorted(range(len(imgs)), key=lambda k: -imgs[k][1].shape[0])
        best = None
        for Wt in (32, 64, 128, 256, 512, 1024):
            pos, x, y, shelf, ok = {}, 0, 0, 0, True
            for k in order:
                h, w = imgs[k][1].shape[:2]
                if w > Wt:
                    ok = False
                    break
                if x + w > Wt:
                    x, y, shelf = 0, y + shelf, 0
                pos[k] = (x, y)
                x += w
                shelf = max(shelf, h)
            if not ok:
                continue
            Ht = max(16, int(math.ceil((y + shelf) / 16.0)) * 16)
            if Ht > 1024:
                continue
            cand = (Wt * Ht, max(Wt, Ht), Wt, Ht, pos)
            if best is None or cand[:2] < best[:2]:
                best = cand
        _, _, Wt, Ht, pos = best
        S = (Wt, Ht)
        atlas = np.zeros((Ht, Wt, 4), np.uint8)
        emis = np.zeros((Ht, Wt), bool)
        for k, (name, im, em) in enumerate(imgs):
            x, y = pos[k]
            atlas[y:y + im.shape[0], x:x + im.shape[1]] = im
            emis[y:y + im.shape[0], x:x + im.shape[1]] = em
        quads = []
        # ---- boxes
        if tex is not None:
            ox, oy = pos[0]
            mats = bone_matrices(self.rig)
            for b in self.rig.bones:
                Mb = mats[b.name]
                for c in b.cubes:
                    for vs, uvs, n in cube_quads(c):
                        P = np.array([(Mb @ np.array([*p, 1.0]))[:3] for p in vs])
                        if np.linalg.norm(np.cross(P[1] - P[0], P[2] - P[0])) < 1e-6 and np.linalg.norm(np.cross(P[2] - P[0], P[3] - P[0])) < 1e-6:
                            continue
                        N = Mb[:3, :3] @ np.array(n, float)
                        N /= np.linalg.norm(N)
                        UV = np.array(uvs, float) + (ox, oy)
                        quads += split_face(P, UV, N, emis)
        # ---- plates
        for k, (p, rgba, D, em, owner) in enumerate(plate_data):
            ox, oy = pos[k + (1 if tex is not None else 0)]
            O, Rv, Dv, Nv = p.corner()
            Mb = bone_matrices(self.rig)[p.bone.name]
            piv = np.array(p.bone.pivot, float)
            for vs, uvs, n, e in RL.mesh_smooth(rgba, D, owner, em):
                P = np.array([O + x * Rv + y * Dv + z * Nv for x, y, z in vs]) - piv
                P = (Mb[:3, :3] @ P.T).T + Mb[:3, 3]
                N = Mb[:3, :3] @ (n[0] * Rv + n[1] * Dv + n[2] * Nv)
                quads.append((P, np.array(uvs, float) + (ox, oy), N / np.linalg.norm(N), e))
        return quads, atlas, S

def split_face(P, UV, N, emis):
    """Split a box face along its texel grid where the emissive flag changes."""
    u0, u1 = UV[:, 0].min(), UV[:, 0].max()
    v0, v1 = UV[:, 1].min(), UV[:, 1].max()
    iu0, iu1, iv0, iv1 = int(round(u0)), int(round(u1)), int(round(v0)), int(round(v1))
    if iu1 <= iu0 or iv1 <= iv0:
        return [(P, UV, N, False)]
    sub = emis[iv0:iv1, iu0:iu1]
    if not sub.any():
        return [(P, UV, N, False)]
    if sub.all():
        return [(P, UV, N, True)]
    # affine map uv -> position from three corners
    A = np.array([[UV[i, 0], UV[i, 1], 1.0] for i in range(3)])
    coef = np.linalg.solve(A, P[:3])            # rows: d/du, d/dv, const
    def pos(u, v):
        return np.array([u, v, 1.0]) @ coef
    out = []
    key = sub.astype(int)
    for x0, y0, x1, y1, k in RL.greedy(key, np.ones_like(sub, bool)):
        ua, ub, va, vb = iu0 + x0, iu0 + x1, iv0 + y0, iv0 + y1
        uv = [(ua, va), (ua, vb), (ub, vb), (ub, va)]
        vs = [pos(u, v) for u, v in uv]
        vv, uu = RL.orient(vs, uv, N)
        out.append((np.array(vv), np.array(uu, float), N, bool(k)))
    return out

# ------------------------------------------------------------------------------------------- export
def to_obj_space(P):
    P = np.asarray(P, float)
    return np.stack([0.5 + P[..., 0] / TPB, 0.5 - P[..., 1] / TPB, 0.5 - P[..., 2] / TPB], -1)

def write_obj(path, quads, S, mtllib='relic3d.mtl'):
    vidx, tidx, nidx = {}, {}, {}
    vl, tl, nl = [], [], []
    faces = {False: [], True: []}
    def idx(d, lst, key, line):
        if key not in d:
            d[key] = len(lst) + 1
            lst.append(line)
        return d[key]
    for P, UV, N, e in quads:
        Q = to_obj_space(P)
        n = np.array([N[0], -N[1], -N[2]])
        vv, uu = RL.orient(list(map(tuple, Q)), list(map(tuple, UV)), n)
        nk = tuple(np.round(n, 4))
        ni = idx(nidx, nl, nk, 'vn %.4f %.4f %.4f' % nk)
        f = []
        for (x, y, z), (u, v) in zip(vv, uu):
            vk = (round(x, 4), round(y, 4), round(z, 4))
            vi = idx(vidx, vl, vk, 'v %.4f %.4f %.4f' % vk)
            tk = (round(u / S[0], 5), round(v / S[1], 5))
            ti = idx(tidx, tl, tk, 'vt %.5f %.5f' % tk)
            f.append(f'{vi}/{ti}/{ni}')
        faces[e].append('f ' + ' '.join(f))
    with open(path, 'w') as fh:
        fh.write(f'# generated by forge3d.py\nmtllib {mtllib}\n')
        fh.write('\n'.join(vl) + '\n' + '\n'.join(tl) + '\n' + '\n'.join(nl) + '\n')
        for e, name in ((True, 'glow'), (False, 'base')):
            if faces[e]:
                fh.write(f'o {name}\nusemtl {name}\n' + '\n'.join(faces[e]) + '\n')
    return len(quads)

MTL = """# relic item materials: 'glow' is full-bright through NeoForge's emissive_ambient
newmtl base
Ka 0 0 0
Kd 1 1 1
map_Kd #tex

newmtl glow
Ka 1 1 1
Kd 1 1 1
map_Kd #tex
"""

# ------------------------------------------------------------------------------------------- preview
L0 = np.array([0.2, 1.0, 0.7]); L0 /= np.linalg.norm(L0)
L1 = np.array([-0.2, 1.0, -0.7]); L1 /= np.linalg.norm(L1)

def render_quads(items, size=(400, 600), view=np.eye(3), bg=(40, 42, 52), frame=None, persp=None, light=1.0):
    """items: list of (quads_world (P[4] world coords y up), atlas float rgba, emissive flags...).
    Each element: (P (4,3) world, UV (4,2) px, N world, emissive, tex)."""
    W, H = size
    img = np.zeros((H, W, 3), np.float32)
    img[:] = bg
    zbuf = np.full((H, W), -1e9, np.float32)
    tris = []
    for P, UV, N, e, T in items:
        Pv = P @ view.T
        Nv = view @ N
        if persp is None and Nv[2] <= 1e-6:
            continue
        tris.append((Pv, UV, N, e, T))
    if not tris:
        return Image.fromarray(img.astype(np.uint8))
    if persp is not None:
        f = persp
        proj = []
        for Pv, UV, N, e, T in tris:
            z = -Pv[:, 2]
            if (z <= 0.05).any():
                continue
            S = np.stack([Pv[:, 0] / z * f, Pv[:, 1] / z * f, -z], 1)
            # back-face test in screen space
            a = S[1, :2] - S[0, :2]; b = S[2, :2] - S[0, :2]
            if a[0] * b[1] - a[1] * b[0] <= 0:
                continue
            proj.append((S, UV, N, e, T))
        cx, cy, span = 0.0, 0.0, 2.0 * W / H
        tris = proj
    else:
        allp = np.concatenate([t[0] for t in tris])
        lo, hi = allp.min(0), allp.max(0)
        if frame is not None:
            cx, cy, span = frame
        else:
            span = max(hi[0] - lo[0], (hi[1] - lo[1]) * W / H) * 1.08
            cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    sc = W / span
    for P, UV, N, e, T in tris:
        S = np.stack([(P[:, 0] - cx) * sc + W / 2, -(P[:, 1] - cy) * sc + H / 2, P[:, 2]], 1)
        if e:
            shade = 1.0
        else:
            shade = min(1.0, 0.4 + 0.6 * (max(0.0, float(N @ L0)) + max(0.0, float(N @ L1)))) * light
        for j in range(1, len(S) - 1):
            idx = (0, j, j + 1)
            raster(img, zbuf, S[list(idx)], [tuple(UV[i]) for i in idx], T, None, 1.0, 1.0, shade)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def world_quads(quads, atlas, M=None):
    """rig-space quads -> world (y up, block units) through an optional 4x4 transform of OBJ space."""
    T = atlas.astype(np.float32) / 255.0
    out = []
    for P, UV, N, e in quads:
        Q = to_obj_space(P)
        n = np.array([N[0], -N[1], -N[2]])
        if M is not None:
            Q = (M[:3, :3] @ Q.T).T + M[:3, 3]
            n = M[:3, :3] @ n
            n /= max(1e-9, np.linalg.norm(n))
        out.append((Q, UV, n, e, T))
    return out

def view_matrix(yaw=30, pitch=10):
    return rot_zyx(math.radians(pitch), 0, 0) @ rot_zyx(0, math.radians(yaw), 0)

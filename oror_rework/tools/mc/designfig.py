"""Characters rebuilt from the user's design sheets (sheets.py): the model is geometry only, built to the drawn
silhouette, and its texture is the sheet itself projected onto it from the front three-quarter view and the back view.

Fig gives the standard humanoid bones (RigModel animation tags) and shape helpers:
  box(bone, centre, size, rot)       an oriented cuboid
  hexa(bone, corners8)               any six-sided block (frusta for robes, skirts, tapered limbs)
  frustum(bone, top, bottom)         a block from a top rectangle to a bottom rectangle, each (centre, w, d)
  chain(bone, pts, w, d)             tapered blocks along a polyline (tails, horns, locks of hair)
All coordinates are model pixels (y down, ground at y = 24, front towards -z).

Views: one per sheet view, each with its own camera (fitted to the drawn silhouette) and its own pose, since the
back view often stands differently from the front one. A texel takes its colour from the view that sees it most
squarely; texels no view sees take the nearest seen colour on their face.
"""
import math, os, zlib
import numpy as np
from PIL import Image
from scipy import ndimage
import sculpt as SC
import bb
import sheets as SH
from rig import Rig, rot_zyx, bone_matrices

PROJ = {'type': 'proj'}


def _unit(v):
    v = np.asarray(v, float)
    return v / max(1e-12, float(np.linalg.norm(v)))


class Fig:
    def __init__(self, key, td=3, height=None):
        self.r = Rig(key, height=height)
        SC.Sculpt(self.r, td=td)
        self.td = td
        self.b = {}
        self.mirror_x = 0.0          # the character's plane of symmetry (x), for colouring sides no view sees
        self.decals = []             # sheet close-ups pasted straight onto box faces (see decal)
        self.colours = 48            # palette size the sheet and texture are snapped to (0: none)
        self.crisp = True            # median sampling (flat voxel colours) instead of area means

    # ------------------------------------------------------------------ bones
    def bone(self, name, parent, pivot, anim=None, rot=(0, 0, 0), **params):
        b = self.r.bone(name, self.b[parent] if isinstance(parent, str) else parent, pivot, rot=rot, anim=anim, **params)
        self.b[b.name] = b
        return b

    def humanoid(self, hip_y, waist_y, neck_y, shoulder, elbow, hip, knee, hover=0.0):
        """Standard bones. shoulder/elbow/hip/knee are (x, y, z) for the character's right side; the left mirrors."""
        self.bone('root', None, (0, 24, 0), anim='root', hover=hover, speed=0.06)
        self.bone('hips', 'root', (0, hip_y, 0))
        self.bone('torso', 'hips', (0, waist_y, 0), anim='breath')
        self.bone('head', 'torso', (0, neck_y, 0), anim='head')
        sx, sy, sz = shoulder
        ex, ey, ez = elbow
        self.bone('arm_r', 'torso', (sx, sy, sz), anim='arm_r')
        self.bone('arm_l', 'torso', (-sx, sy, sz), anim='arm_l')
        self.bone('fore_r', 'arm_r', (ex, ey, ez), anim='elbow')
        self.bone('fore_l', 'arm_l', (-ex, ey, ez), anim='elbow')
        hx, hy, hz = hip
        kx, ky, kz = knee
        self.bone('leg_r', 'hips', (hx, hy, hz), anim='leg_r')
        self.bone('leg_l', 'hips', (-hx, hy, hz), anim='leg_l')
        self.bone('shin_r', 'leg_r', (kx, ky, kz), anim='knee')
        self.bone('shin_l', 'leg_l', (-kx, ky, kz), anim='knee', side=1.0)
        return self

    def views_for(self, part, views, bone=None):
        """Let only these sheet views paint the boxes named `part` (e.g. a head that is turned in the back view)."""
        for s in self.r.sculpt.surfs:
            if part_of(s) == part and (bone is None or s.bone.name == bone):
                s.mat = dict(s.mat or PROJ, views=tuple(views))

    def decal(self, bone, part, face, rect, flip=False):
        """Paint the face `face` (north = front, south, east = +x, west = -x, up) of the boxes named `part` on `bone`
        straight from a sheet rectangle (x0, y0, x1, y1), e.g. the frontal face close-up onto the head's front. The
        rectangle is the face as seen from outside it; flip mirrors it (the side panel of one side for the other)."""
        self.decals.append(dict(bone=bone, part=part, face=face, rect=rect, flip=flip))

    # ------------------------------------------------------------------ shapes
    def _bone(self, bone):
        return self.b[bone] if isinstance(bone, str) else bone

    def box(self, bone, centre, size, rot=(0, 0, 0), name='box', mat=None, skip=()):
        """Oriented cuboid; rot (x, y, z radians, applied z*y*x as everywhere in the rig) turns it about its centre."""
        R = rot_zyx(*rot)
        return self.hexa(bone, box_corners(centre, size, R), name=name, mat=mat, skip=skip)

    def hexa(self, bone, C, name='hexa', mat=None, skip=()):
        """Six-sided block from 8 corners (rest-pose model coordinates): bottom face 0-3 then top face 4-7, both
        wound the same way, corner i of the top above corner i of the bottom. Faces named as on a cube."""
        bone = self._bone(bone)
        C = np.asarray(C, float)
        mid = C.mean(0)
        out = []
        for face, idx in HEXA_FACES.items():
            if face in skip:
                continue
            P = C[list(idx)]
            n = np.cross(P[1] - P[0], P[3] - P[0]) + np.cross(P[2] - P[1], P[0] - P[1])
            if np.linalg.norm(n) < 1e-9:
                n = np.cross(P[2] - P[1], P[2] - P[3])
            if np.linalg.norm(n) < 1e-9:
                continue
            n = _unit(n)
            if np.dot(n, P.mean(0) - mid) > 0:
                P = P[[0, 3, 2, 1]]          # wound as bb.obox: (P1 - P0) x (P3 - P0) points inward
            else:
                n = -n
            wpx = max(np.linalg.norm(P[1] - P[0]), np.linalg.norm(P[2] - P[3]))
            hpx = max(np.linalg.norm(P[3] - P[0]), np.linalg.norm(P[2] - P[1]))
            if wpx < 0.02 or hpx < 0.02:
                continue
            W = max(1, int(round(wpx * self.td)))
            H = max(1, int(round(hpx * self.td)))
            UV = np.array([[0, 0], [W, 0], [W, H], [0, H]], float)
            info = dict(face=face, world=True, bb=True, ao=False)
            out.append(SC.S(self.r).add(SC.Surf(bone, P, np.tile(n, (4, 1)), UV, [(0, 1, 2, 3)], (W, H), mat or PROJ, 'design', info, name)))
        return out

    def frustum(self, bone, top, bottom, name='frustum', mat=None, skip=(), rot=None):
        """top/bottom = (centre (3,), width x, depth z); rot (3x3) tilts both rectangles about their own centres."""
        (ct, wt, dt), (cb, wb, db) = top, bottom
        R = np.eye(3) if rot is None else np.asarray(rot, float)

        def rect(c, w, d):
            c = np.asarray(c, float)
            return [c + R @ np.array(v) for v in ((-w / 2, 0, -d / 2), (w / 2, 0, -d / 2), (w / 2, 0, d / 2), (-w / 2, 0, d / 2))]
        return self.hexa(bone, rect(cb, wb, db) + rect(ct, wt, dt), name=name, mat=mat, skip=skip)

    def chain(self, bone, pts, w, d=None, name='chain', up=(0, -1, 0), mat=None, overlap=0.4):
        """Blocks along a polyline, width w and depth d (scalars or one per point) tapering between points."""
        pts = np.asarray(pts, float)
        n = len(pts)
        w = np.broadcast_to(np.asarray(w, float), (n,))
        d = w if d is None else np.broadcast_to(np.asarray(d, float), (n,))
        out = []
        for i in range(n - 1):
            a, b = pts[i], pts[i + 1]
            t = _unit(b - a)
            u0 = np.asarray(up, float)
            if abs(np.dot(_unit(u0), t)) > 0.95:
                u0 = np.array([0, 0, -1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0])
            x = _unit(np.cross(u0, t))
            y = np.cross(t, x)
            e = overlap * (w[i] + w[i + 1]) / 4 if i < n - 2 else 0.0
            a2, b2 = a, b + t * e

            def rect(c, ww, dd):
                return [c - x * ww / 2 - y * dd / 2, c + x * ww / 2 - y * dd / 2, c + x * ww / 2 + y * dd / 2, c - x * ww / 2 + y * dd / 2]
            out += self.hexa(bone, rect(a2, w[i], d[i]) + rect(b2, w[i + 1], d[i + 1]), name=f'{name}{i}', mat=mat)
        return out


def box_corners(centre, size, R=None):
    c = np.asarray(centre, float)
    sx, sy, sz = np.asarray(size, float) / 2
    R = np.eye(3) if R is None else R
    # bottom (y+, ground side) then top (y-), same winding
    loc = [(-sx, sy, -sz), (sx, sy, -sz), (sx, sy, sz), (-sx, sy, sz), (-sx, -sy, -sz), (sx, -sy, -sz), (sx, -sy, sz), (-sx, -sy, sz)]
    return [c + R @ np.array(v) for v in loc]


# corner order: bottom 0..3, top 4..7; quads wound so that u runs along the first edge and v along the last
HEXA_FACES = {
    'down': (0, 1, 2, 3),
    'up': (7, 6, 5, 4),
    'north': (4, 5, 1, 0),      # front (-z)
    'south': (6, 7, 3, 2),      # back (+z)
    'east': (5, 6, 2, 1),       # +x
    'west': (7, 4, 0, 3),       # -x
}


# ====================================================================================================== views
class Sheet:
    """A character's sheet with its views. views: {name: dict(box=[(x0, y0, x1, y1), ...], drop=[boxes to ignore],
    yaw=initial guess, pitch=, pose={bone: (rx, ry, rz)})}"""
    def __init__(self, name, views):
        self.name = name
        self.im = SH.load(name)
        self.views = {}
        for k, v in views.items():
            m = np.zeros(self.im.shape[:2], bool)
            for b in v['box']:
                m |= SH.figure_mask(self.im, b)
            for b in v.get('drop', ()):
                m[b[1]:b[3], b[0]:b[2]] = False
            self.views[k] = dict(v, mask=m)
        self.raw = self.im
        self.pal = None

    def clean(self, colours=24, median=None):
        """Flatten the render into pixel-art regions: a median filter about half a voxel wide removes the soft
        shading noise, then every pixel snaps to the figure's own palette of `colours` colours."""
        if not colours:
            return self
        median = int(os.environ.get('DF_MEDIAN', 5)) if median is None else median
        m = np.zeros(self.raw.shape[:2], bool)
        for v in self.views.values():
            m |= v['mask']
        sm = np.stack([ndimage.median_filter(self.raw[..., c], size=median) for c in range(3)], -1) if median else self.raw
        self.pal = SH.palette(sm, m, colours)
        ys, xs = np.nonzero(ndimage.binary_dilation(m, iterations=12))
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        im = self.raw.copy()
        im[y0:y1, x0:x1] = SH.snap(sm[y0:y1, x0:x1], self.pal)
        self.im = im
        return self


def posed_points(fig, pose):
    """For each surface: function mapping rest-pose model points of that surface into the given pose."""
    rest = bone_matrices(fig.r)
    posed = bone_matrices(fig.r, pose or {})
    out = {}
    for b in fig.r.bones:
        out[b.name] = posed[b.name] @ np.linalg.inv(rest[b.name])
    return out


def tris_posed(fig, pose):
    T, owner = SH.triangles(fig.r, pose)
    return T


def fit_views(fig, sheet, cams=None, verbose=True):
    """Fit (or reuse) a camera per view. cams: {view: Camera} to skip fitting."""
    out = {}
    for k, v in sheet.views.items():
        if cams and k in cams:
            out[k] = cams[k]
            continue
        if v.get('cam'):
            out[k] = SH.Camera(*v['cam'])
            if verbose:
                T = tris_posed(fig, v.get('pose'))
                print(f'  {sheet.name} {k}: IoU {SH.iou(SH.silhouette(T, out[k], v["mask"].shape), v["mask"]):.3f} {out[k]} (fixed)')
            continue
        T = tris_posed(fig, v.get('pose'))
        s, cam = SH.fit_camera(T, v['mask'], v.get('yaw', -30.0), v.get('pitch', 10.0), yaw_span=v.get('yaw_span', 30.0),
                               pitch_span=v.get('pitch_span', 10.0))
        if verbose:
            print(f'  {sheet.name} {k}: IoU {s:.3f} {cam}')
        out[k] = cam
    return out


class ProjView:
    def __init__(self, fig, sheet, key, cam, weight=1.0):
        v = sheet.views[key]
        self.key, self.cam, self.weight = key, cam, v.get('weight', weight)
        self.pose = v.get('pose') or {}
        self.mats = posed_points(fig, self.pose)
        self.mask = v['mask']
        self.img = SH.fill_out(sheet.im, self.mask)
        self.S = SH.integral(self.img)
        T = tris_posed(fig, self.pose)
        self.zbuf = SH.raster(cam.project(T), self.mask.shape)
        self.dir = cam.towards()
        self.crisp = getattr(fig, 'crisp', True)
        self.only = v.get('only')           # bone names this view may paint (None: all)
        self.never = v.get('never', ())

    def sample(self, bone, P, N, texel_px):
        M = self.mats[bone]
        Pp = P @ M[:3, :3].T + M[:3, 3]
        Np = N @ M[:3, :3].T
        Q = self.cam.project(Pp)
        u, v, z = Q[:, 0], Q[:, 1], Q[:, 2]
        H, W = self.mask.shape
        inside = (u >= 0) & (u < W) & (v >= 0) & (v < H)
        ui = np.clip(np.floor(u).astype(int), 0, W - 1)
        vi = np.clip(np.floor(v).astype(int), 0, H - 1)
        # visible unless something lies in front by more than a texel or two (the depth buffer is per sheet pixel)
        tol = 1.5 * self.cam.scale
        zt = self.zbuf[vi, ui]
        for du, dv in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            zt = np.minimum(zt, self.zbuf[np.clip(vi + dv, 0, H - 1), np.clip(ui + du, 0, W - 1)])
        vis = z >= zt - tol
        facing = np.clip(Np @ self.dir, 0, 1)
        w = np.where(inside & vis, facing, 0.0) * self.weight
        if self.only is not None and bone not in self.only:
            w[:] = 0
        if bone in self.never:
            w[:] = 0
        r = max(0.0, texel_px * self.cam.scale * 0.35)
        col = SH.median_sample(self.img, u, v, r) if self.crisp else SH.area_sample(self.img, u, v, max(0.0, r - 0.5), self.S)
        return col, w, inside


def mode_filter(rgb):
    """Drop isolated single texels: a texel whose colour none of its 4 neighbours share takes the most common
    neighbour colour."""
    H, W = rgb.shape[:2]
    key = (rgb[..., 0].astype(np.int64) * 65536 + rgb[..., 1].astype(np.int64) * 256 + rgb[..., 2].astype(np.int64))
    pad = np.pad(key, 1, mode='edge')
    nb = np.stack([pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]], -1)
    lone = (nb != key[..., None]).all(-1)
    if not lone.any():
        return rgb
    out = rgb.copy()
    padc = np.pad(rgb, ((1, 1), (1, 1), (0, 0)), mode='edge')
    nbc = np.stack([padc[:-2, 1:-1], padc[2:, 1:-1], padc[1:-1, :-2], padc[1:-1, 2:]], -2)    # H, W, 4, 3
    for y, x in zip(*np.nonzero(lone)):
        ks = nb[y, x]
        vals, cnt = np.unique(ks, return_counts=True)
        j = int(np.nonzero(ks == vals[cnt.argmax()])[0][0])
        out[y, x] = nbc[y, x, j]
    return out


def part_of(s):
    return (s.mat or {}).get('group') or s.name.rstrip('0123456789_')


def bake(fig, sheet, cams, min_facing=0.3):
    """Paint every surface from the sheet views. A texel takes the view (or the mirror image across the character's
    plane of symmetry) that sees it most squarely; texels nothing sees take the colour of the nearest seen texel of
    the same part in 3D, so the far side of a tail or the inside of a sleeve keeps that part's colours."""
    from scipy.spatial import cKDTree
    views = [ProjView(fig, sheet, k, cams[k]) for k in sheet.views]
    rig = fig.r
    mats = SC.world_of(rig)
    td = fig.td
    rows = []
    for s in rig.sculpt.surfs:
        Pw, Nw = SC.surf_world(s, mats)
        P, N, cov = SC.raster_attrs(s, Pw, Nw)
        H, W = P.shape[:2]
        Pf, Nf = P.reshape(-1, 3), N.reshape(-1, 3)
        mat = s.mat or {}
        best_w = np.full(len(Pf), min_facing)
        best_c = np.zeros((len(Pf), 3), np.float32)
        cands = [(s.bone.name, Pf, Nf, 1.0)]
        if mat.get('mirror', True):
            mb = s.bone.name
            if mb.endswith('_r') or mb.endswith('_l'):
                alt = mb[:-2] + ('_l' if mb.endswith('_r') else '_r')
                mb = alt if alt in fig.b else mb
            Pm = Pf.copy(); Pm[:, 0] = 2 * fig.mirror_x - Pm[:, 0]
            Nm = Nf.copy(); Nm[:, 0] = -Nm[:, 0]
            cands.append((mb, Pm, Nm, mat.get('mirror_trust', 0.7)))
        dbg = os.environ.get('DF_DEBUG')
        for vi, pv in enumerate(views):
            if mat.get('views') and pv.key not in mat['views']:
                continue
            for ci, (bone, Pc, Nc, trust) in enumerate(cands):
                col, w, inside = pv.sample(bone, Pc, Nc, 1.0 / td)
                w = w * trust * mat.get('trust', {}).get(pv.key, 1.0)
                take = w > best_w
                best_w[take] = w[take]
                if dbg == '1':
                    col = np.tile(np.array([[(255, 40, 40), (255, 200, 40)], [(40, 80, 255), (40, 220, 255)]][vi][ci], np.float32), (len(col), 1))
                best_c[take] = col[take]
        rows.append((s, P, best_c, best_w > min_facing, N))
    # close-ups pasted onto faces
    for d in fig.decals:
        hit = [r for r in rows if r[0].bone.name == d['bone'] and part_of(r[0]) == d['part']]
        if not hit:
            raise ValueError(f'decal: no part {d["part"]} on {d["bone"]}')
        allp = np.concatenate([r[1].reshape(-1, 3) for r in hit])
        lo, hi = allp.min(0), allp.max(0)
        x0, y0, x1, y1 = d['rect']
        for r in hit:
            s = r[0]
            if s.info.get('face') != d['face']:
                continue
            P = r[1].reshape(-1, 3)
            fy = (P[:, 1] - lo[1]) / max(1e-6, hi[1] - lo[1])
            if d['face'] == 'north':
                fx = (P[:, 0] - lo[0]) / max(1e-6, hi[0] - lo[0])
            elif d['face'] == 'south':
                fx = (hi[0] - P[:, 0]) / max(1e-6, hi[0] - lo[0])
            elif d['face'] == 'west':
                fx = (hi[2] - P[:, 2]) / max(1e-6, hi[2] - lo[2])
            elif d['face'] == 'east':
                fx = (P[:, 2] - lo[2]) / max(1e-6, hi[2] - lo[2])
            else:                                  # up: seen from above, front at the bottom
                fx = (P[:, 0] - lo[0]) / max(1e-6, hi[0] - lo[0])
                fy = (P[:, 2] - lo[2]) / max(1e-6, hi[2] - lo[2])
            if d['flip']:
                fx = 1 - fx
            u = x0 + np.clip(fx, 0, 1) * (x1 - x0)
            v = y0 + np.clip(fy, 0, 1) * (y1 - y0)
            rpx = 0.35 * (x1 - x0) / max(1e-6, (hi[0] - lo[0] if d['face'] in ('north', 'south', 'up') else hi[2] - lo[2]) * td)
            r[2][:] = SH.median_sample(sheet.raw, u, v, rpx)
            r[3][:] = True
            s.info['decal'] = True
    # faces seen in part: the rest of the face from its nearest seen texel (in the face's own texel grid); faces
    # (nearly) nobody sees: the part's main colour, a little varied, like a plain cloth face in a hand-made model
    part_cols = {}
    for s, P, c, seen, _ in rows:
        if seen.any():
            part_cols.setdefault(part_of(s), []).append(c[seen])
    all_seen = [c[seen] for s, P, c, seen, _ in rows if seen.any()]
    for s, P, c, seen, _ in rows:
        H, W = P.shape[:2]
        sm = seen.reshape(H, W)
        if sm.all():
            continue
        if os.environ.get('DF_DEBUG') == '2':
            c[~seen] = (255, 0, 255)
            continue
        if sm.mean() >= 0.3:
            idx = ndimage.distance_transform_edt(~sm, return_distances=False, return_indices=True)
            c[:] = c.reshape(H, W, 3)[idx[0], idx[1]].reshape(-1, 3)
            continue
        pool = part_cols.get(part_of(s)) or all_seen
        pool = np.concatenate(pool) if pool else np.full((1, 3), 200.0, np.float32)
        q = np.round(pool / 12.0)
        keys, inv, cnt = np.unique(q, axis=0, return_inverse=True, return_counts=True)
        main = pool[inv.ravel() == cnt.argmax()].mean(0)
        rng = np.random.default_rng(zlib.crc32(f'{s.bone.name}/{s.name}/{s.info.get("face")}'.encode()))
        # strands: noise smeared along the face's longer side, like hair or folds of cloth
        jit = rng.normal(0, 1, (H, W, 1)).astype(np.float32)
        jit = ndimage.uniform_filter(jit, (5, 1, 1) if H >= W else (1, 5, 1)) * 14.0
        fill = (main[None, None, :] + jit).reshape(-1, 3)
        c[~seen] = fill[~seen]

    pal = None if os.environ.get('DF_DEBUG') else sheet.pal
    gamma = getattr(fig, 'gamma', 0.92)
    light_k = getattr(fig, 'light_k', 0.8)
    for s, P, c, seen, N in rows:
        H, W = P.shape[:2]
        mat = s.mat or {}
        rgb = c.reshape(H, W, 3)
        if pal is not None and mat.get('snap', True) and not s.info.get('decal'):
            rgb = SH.snap(rgb, pal)
            if mat.get('tidy', True) and min(H, W) >= 3:
                rgb = mode_filter(rgb)
        # the sheet has its lighting painted in and the game lights the model again: divide out the game's light for
        # the face (averaged over the ways the mob can turn: a wall ~0.62, a top 1.0, an underside 0.4) so the sheet's
        # own shading is what shows, then a gentle gamma keeps the whites white
        up = -N[..., 1]                                    # model y points down
        lit = 0.62 + 0.38 * np.clip(up, 0, 1) - 0.22 * np.clip(-up, 0, 1)
        rgb = np.clip(rgb * np.minimum(1.45, light_k / lit)[..., None], 0, 255)
        rgb = 255.0 * (rgb / 255.0) ** gamma
        if mat.get('tint') is not None:
            rgb = rgb * np.asarray(mat['tint'], np.float32)
        rgba = np.zeros((H, W, 4), np.float32)
        rgba[..., :3] = np.clip(rgb, 0, 255)
        rgba[..., 3] = 255
        s.rgba = rgba
        s.glow = None
        if mat.get('glow'):
            g = np.zeros((H, W, 4), np.float32)
            g[..., :3] = rgb
            g[..., 3] = np.where(rgb.max(-1) > mat.get('glow_min', 150), 255, 0)
            s.glow = g
    return SC.atlas(rig)


# ====================================================================================================== checks
def overlay_all(fig, sheet, cams, path):
    """For each view: the sheet crop with the drawn silhouette (cyan) and the model's (magenta)."""
    tiles = []
    for k, v in sheet.views.items():
        T = tris_posed(fig, v.get('pose'))
        sil = SH.silhouette(T, cams[k], v['mask'].shape)
        ys, xs = np.nonzero(v['mask'] | sil)
        box = (max(0, xs.min() - 10), max(0, ys.min() - 10), min(v['mask'].shape[1], xs.max() + 10), min(v['mask'].shape[0], ys.max() + 10))
        tiles.append(SH.overlay(sheet.im, v['mask'], sil, os.devnull if False else path + f'.{k}.png', box))
    return tiles


def compare(fig, sheet, cams, tex, glow, path, extra=((30, 8), (90, 8), (180, 8), (-90, 8))):
    """Sheet views next to the textured model seen through the same cameras, then from a few other angles."""
    from PIL import ImageDraw
    tiles = []
    for k, v in sheet.views.items():
        cam = cams[k]
        ys, xs = np.nonzero(v['mask'])
        box = (max(0, xs.min() - 10), max(0, ys.min() - 10), min(v['mask'].shape[1], xs.max() + 10), min(v['mask'].shape[0], ys.max() + 10))
        crop = Image.fromarray(sheet.im.astype(np.uint8)).crop(box)
        ren = render_cam(fig, tex, glow, cam, v.get('pose'), sheet.im.shape[:2], bg=(98, 96, 99)).crop(box)
        tiles += [crop, ren]
    Hh = max(t.size[1] for t in tiles)
    for yaw, pitch in extra:
        tiles.append(SC.render(fig.r, tex, glow, yaw=yaw, pitch=pitch, size=(int(Hh * 0.6), Hh), bg=(98, 96, 99)))
    Wt = sum(int(t.size[0] * Hh / t.size[1]) for t in tiles)
    out = Image.new('RGB', (Wt, Hh), (30, 30, 30))
    x = 0
    for t in tiles:
        t2 = t.resize((int(t.size[0] * Hh / t.size[1]), Hh))
        out.paste(t2, (x, 0))
        x += t2.size[0]
    out.save(path)
    return out


def render_cam(fig, tex, glow, cam, pose, shape, bg=(98, 96, 99)):
    """The textured model through a sheet camera (sheet pixel grid), lit like an entity in game."""
    H, W = shape
    T = np.asarray(tex, np.float32) / 255.0
    G = np.asarray(glow, np.float32) / 255.0 if glow is not None else None
    th, tw = T.shape[:2]
    mats = bone_matrices(fig.r, pose or {})
    img = np.zeros((H, W, 3), np.float32)
    img[:] = bg
    zb = np.full((H, W), -1e9, np.float32)
    for s in fig.r.sculpt.surfs:
        P, N = SC.surf_world(s, mats)
        Nw = np.stack([N[:, 0], -N[:, 1], -N[:, 2]], 1)
        lit = np.clip(0.4 + 0.6 * (np.maximum(0, Nw @ SC.L0) + np.maximum(0, Nw @ SC.L1)), 0, 1)
        Q = cam.project(P)
        uv = s.UV + s.pos
        for q in s.Q:
            for tri in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
                S = Q[list(tri)]
                Sx, Sy, Z = S[:, 0], S[:, 1], S[:, 2]
                x0, x1 = int(max(0, math.floor(Sx.min()))), int(min(W - 1, math.ceil(Sx.max())))
                y0, y1 = int(max(0, math.floor(Sy.min()))), int(min(H - 1, math.ceil(Sy.max())))
                if x1 < x0 or y1 < y0:
                    continue
                den = (Sy[1] - Sy[2]) * (Sx[0] - Sx[2]) + (Sx[2] - Sx[1]) * (Sy[0] - Sy[2])
                if abs(den) < 1e-9:
                    continue
                ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
                px, py = xs + 0.5, ys + 0.5
                l1 = ((Sy[1] - Sy[2]) * (px - Sx[2]) + (Sx[2] - Sx[1]) * (py - Sy[2])) / den
                l2 = ((Sy[2] - Sy[0]) * (px - Sx[2]) + (Sx[0] - Sx[2]) * (py - Sy[2])) / den
                l3 = 1 - l1 - l2
                m = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
                if not m.any():
                    continue
                z = l1 * Z[0] + l2 * Z[1] + l3 * Z[2]
                sub = zb[y0:y1 + 1, x0:x1 + 1]
                m &= z > sub
                if not m.any():
                    continue
                U = uv[list(tri)]
                u = l1 * U[0, 0] + l2 * U[1, 0] + l3 * U[2, 0]
                v = l1 * U[0, 1] + l2 * U[1, 1] + l3 * U[2, 1]
                ui = np.clip(u.astype(int), 0, tw - 1)
                vi = np.clip(v.astype(int), 0, th - 1)
                texel = T[vi, ui]
                m &= texel[..., 3] > 0.5
                if not m.any():
                    continue
                L = lit[list(tri)]
                li = l1 * L[0] + l2 * L[1] + l3 * L[2]
                col = texel[..., :3] * li[..., None] * 255
                if G is not None:
                    col = col + G[vi, ui, :3] * 255
                sub[m] = z[m]
                img[y0:y1 + 1, x0:x1 + 1][m] = np.clip(col[m], 0, 255)
    return Image.fromarray(img.astype(np.uint8))

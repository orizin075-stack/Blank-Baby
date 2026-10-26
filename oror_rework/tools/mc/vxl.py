"""Voxel sculpting for the design-sheet characters: the sheets are voxel figures, so the mobs are built the same way,
from small cubes (half a model pixel by default), each with its own colour, then meshed into textured quads.

Vol(res)            a volume; res = voxels per model pixel (2: half-pixel voxels)
  .box / .ellipsoid / .capsule / .chain / .strand / .cone / .plate      fill shapes (model coordinates), each with a
                     colour (palette entry, or a function of the voxel's model position) and a bone name
  .paint(region, colour)  recolour the surface voxels inside a region
  .decal(img, at, right, down, size)  paint a small image onto the voxels facing a direction (eyes, crests)
  .surfs(fig)        greedy-meshed quads per bone, added to the Fig's sculpt with their colours baked in: every
                     voxel face 2x2 texels, darkened by ambient occlusion from its neighbours like a voxel render

Model coordinates as everywhere: x to the character's left, y down (ground at 24), z backwards.
"""
import math
import numpy as np
from colors import hexc
import sculpt as SC

AO_STEP = 0.16


def C(c):
    return np.array(hexc(c), np.float32) if isinstance(c, str) else np.asarray(c, np.float32)


class Vol:
    def __init__(self, lo=(-24, -40, -24), hi=(24, 24.5, 24), res=2):
        self.res = res
        self.lo = np.array(lo, float)
        n = np.ceil((np.array(hi, float) - self.lo) * res).astype(int)
        self.shape = tuple(n)
        self.col = np.zeros(self.shape, np.uint16)          # palette index, 0 empty
        self.bone = np.zeros(self.shape, np.uint8)
        self.pal = [np.zeros(3, np.float32)]
        self.pal_idx = {}
        self.bones = ['root']
        self.bone_idx = {'root': 0}
        # voxel centre coordinates
        ax = [self.lo[i] + (np.arange(self.shape[i]) + 0.5) / res for i in range(3)]
        self.ax = ax
        self.overlays = []

    def tones(self, base, var=0.05, steps=(-1.0, -0.5, 0.0, 0.0, 0.0, 0.5, 1.0), seed=0, scale=1):
        """Colour function: base with each voxel (or scale-sized block of voxels) a step lighter or darker, like the
        soft voxel shading of the sheets. Returns palette indices."""
        b = C(base)
        idx = np.array([self.ci(np.clip(b * (1 + var * st), 0, 255)) for st in steps], np.uint16)
        res = self.res

        def fn(X, Y, Z):
            i = np.floor(X * res / scale).astype(np.int64) * 73856093 ^ np.floor(Y * res / scale).astype(np.int64) * 19349663 \
                ^ np.floor(Z * res / scale).astype(np.int64) * 83492791 ^ seed * 2654435761
            return idx[(i % len(idx) + len(idx)) % len(idx)]
        return fn

    def overlay(self, bone, face, rect, img):
        """An image drawn at texel resolution over the quads of `bone` facing `face` inside the model rectangle
        rect = (x0, y0, x1, y1) (front faces) - the face on the front of the head."""
        self.overlays.append(dict(bone=bone, face=face, rect=rect, img=np.asarray(img, np.float32)))

    # ------------------------------------------------------------------ palette / bones
    def ci(self, c):
        key = tuple(int(round(x)) for x in C(c))
        if key not in self.pal_idx:
            self.pal_idx[key] = len(self.pal)
            self.pal.append(np.array(key, np.float32))
        return self.pal_idx[key]

    def bi(self, name):
        if name not in self.bone_idx:
            self.bone_idx[name] = len(self.bones)
            self.bones.append(name)
        return self.bone_idx[name]

    # ------------------------------------------------------------------ region helpers
    def _sub(self, lo, hi):
        """Index ranges of the voxels whose centres lie in the box lo..hi, and their centre grids."""
        i0 = np.clip(np.floor((np.asarray(lo) - self.lo) * self.res).astype(int), 0, np.array(self.shape))
        i1 = np.clip(np.ceil((np.asarray(hi) - self.lo) * self.res).astype(int) + 1, 0, np.array(self.shape))
        sl = tuple(slice(a, b) for a, b in zip(i0, i1))
        X, Y, Z = np.meshgrid(self.ax[0][sl[0]], self.ax[1][sl[1]], self.ax[2][sl[2]], indexing='ij')
        return sl, X, Y, Z

    def _write(self, sl, mask, colour, bone, X, Y, Z):
        if not mask.any():
            return
        b = self.bi(bone)
        if callable(colour):
            cols = colour(X[mask], Y[mask], Z[mask])
            if isinstance(cols, np.ndarray) and cols.dtype == np.uint16:
                idx = cols
            else:
                idx = np.array([self.ci(c) for c in cols], np.uint16)
        else:
            idx = self.ci(colour)
        sub = self.col[sl]
        sub[mask] = idx
        self.bone[sl][mask] = b

    def carve(self, mask_fn, lo, hi):
        sl, X, Y, Z = self._sub(lo, hi)
        m = mask_fn(X, Y, Z)
        self.col[sl][m] = 0

    # ------------------------------------------------------------------ shapes
    def box(self, lo, hi, colour, bone):
        lo, hi = np.minimum(lo, hi), np.maximum(lo, hi)
        sl, X, Y, Z = self._sub(lo, hi)
        m = (X >= lo[0]) & (X <= hi[0]) & (Y >= lo[1]) & (Y <= hi[1]) & (Z >= lo[2]) & (Z <= hi[2])
        self._write(sl, m, colour, bone, X, Y, Z)

    def ellipsoid(self, c, r, colour, bone, cut=None):
        c, r = np.asarray(c, float), np.asarray(r, float)
        sl, X, Y, Z = self._sub(c - r, c + r)
        m = ((X - c[0]) / r[0]) ** 2 + ((Y - c[1]) / r[1]) ** 2 + ((Z - c[2]) / r[2]) ** 2 <= 1.0
        if cut is not None:
            m &= cut(X, Y, Z)
        self._write(sl, m, colour, bone, X, Y, Z)

    def capsule(self, a, b, ra, rb, colour, bone, flat=None):
        """A tapered round rod from a to b (radius ra to rb); flat=(nx, ny, nz, k) squashes it along a direction."""
        a, b = np.asarray(a, float), np.asarray(b, float)
        r = max(ra, rb)
        lo, hi = np.minimum(a, b) - r, np.maximum(a, b) + r
        sl, X, Y, Z = self._sub(lo, hi)
        P = np.stack([X, Y, Z], -1)
        ab = b - a
        L2 = max(1e-9, float(ab @ ab))
        t = np.clip(((P - a) @ ab) / L2, 0, 1)
        Q = a + t[..., None] * ab
        d = P - Q
        if flat is not None:
            n = np.asarray(flat[:3], float)
            n /= np.linalg.norm(n)
            dn = d @ n
            d = d + n * dn[..., None] * (flat[3] - 1)
        rr = ra + (rb - ra) * t
        m = (d ** 2).sum(-1) <= rr ** 2
        self._write(sl, m, colour, bone, X, Y, Z)

    def chain(self, pts, radii, colour, bone, flat=None):
        for i in range(len(pts) - 1):
            self.capsule(pts[i], pts[i + 1], radii[i], radii[i + 1], colour, bone, flat)

    def strand(self, pts, w, d, colour, bone, up=(0, 0, 1)):
        """A flat lock of hair or ribbon along pts: w wide, d thick (model px), w and d may taper (lists)."""
        pts = [np.asarray(p, float) for p in pts]
        n = len(pts)
        w = np.broadcast_to(np.asarray(w, float), (n,))
        d = np.broadcast_to(np.asarray(d, float), (n,))
        for i in range(n - 1):
            a, b = pts[i], pts[i + 1]
            t_ = b - a
            L = np.linalg.norm(t_)
            if L < 1e-6:
                continue
            t_ /= L
            u = np.asarray(up, float)
            side = np.cross(t_, u)
            if np.linalg.norm(side) < 1e-6:
                side = np.cross(t_, (1, 0, 0))
            side /= np.linalg.norm(side)
            nrm = np.cross(side, t_)
            r = max(w[i], w[i + 1], d[i], d[i + 1]) / 2 + 0.5
            lo, hi = np.minimum(a, b) - r, np.maximum(a, b) + r
            sl, X, Y, Z = self._sub(lo, hi)
            P = np.stack([X, Y, Z], -1) - a
            s = P @ t_
            tt = np.clip(s / L, 0, 1)
            ww = w[i] + (w[i + 1] - w[i]) * tt
            dd = d[i] + (d[i + 1] - d[i]) * tt
            m = (s >= -0.25) & (s <= L + 0.25) & (np.abs(P @ side) <= ww / 2) & (np.abs(P @ nrm) <= dd / 2)
            self._write(sl, m, colour, bone, X, Y, Z)

    def cone(self, top, bottom, r_top, r_bot, colour, bone, depth=0.7, folds=0, fold_amp=0.0, open_front=0.0, thick=None,
             start=0.0):
        """A skirt or robe: elliptical rings from `top` (centre) down to `bottom`, radius r_top..r_bot in x and
        depth*r in z, `folds` pleats round it of fold_amp, an opening of `open_front` radians at the front, hollow
        `thick` px if given."""
        top, bottom = np.asarray(top, float), np.asarray(bottom, float)
        r = max(r_top, r_bot) + fold_amp + 1
        lo = np.minimum(top, bottom) - np.array([r, 0, r])
        hi = np.maximum(top, bottom) + np.array([r, 0, r])
        sl, X, Y, Z = self._sub(lo, hi)
        t = np.clip((Y - top[1]) / max(1e-6, bottom[1] - top[1]), 0, 1)
        cx = top[0] + (bottom[0] - top[0]) * t
        cz = top[2] + (bottom[2] - top[2]) * t
        R = r_top + (r_bot - r_top) * t
        ang = np.arctan2(X - cx, -(Z - cz))           # 0 at the front
        Rf = R + fold_amp * np.cos(ang * folds) * t if folds else R
        dist = np.sqrt((X - cx) ** 2 + ((Z - cz) / depth) ** 2)
        m = (Y >= top[1]) & (Y <= bottom[1]) & (dist <= Rf)
        if thick:
            m &= dist >= Rf - thick
        if open_front:
            m &= np.abs(ang) >= open_front / 2 * (t >= start)
        self._write(sl, m, colour, bone, X, Y, Z)

    def plate(self, corners, thick, colour, bone):
        """A slab through four corners (in order), `thick` px."""
        P = np.asarray(corners, float)
        lo, hi = P.min(0) - thick, P.max(0) + thick
        sl, X, Y, Z = self._sub(lo, hi)
        n = np.cross(P[1] - P[0], P[3] - P[0])
        n /= np.linalg.norm(n)
        Q = np.stack([X, Y, Z], -1)
        dist = (Q - P[0]) @ n
        m = np.abs(dist) <= thick / 2
        # inside the quad: same side of every edge
        for i in range(4):
            a, b = P[i], P[(i + 1) % 4]
            e = np.cross(n, b - a)
            m &= ((Q - a) @ e) >= -0.3
        self._write(sl, m, colour, bone, X, Y, Z)

    # ------------------------------------------------------------------ painting
    def surface(self):
        """Voxels with at least one empty neighbour."""
        f = self.col > 0
        e = np.zeros_like(f)
        for ax in range(3):
            for s in (1, -1):
                nb = np.roll(f, s, ax)
                e |= ~nb
        return f & e

    def paint(self, region, colour, surface_only=True, only=None):
        """Recolour voxels whose centres satisfy region(X, Y, Z); only=colours to replace (hex list)."""
        f = self.surface() if surface_only else (self.col > 0)
        idx = np.nonzero(f)
        X, Y, Z = self.ax[0][idx[0]], self.ax[1][idx[1]], self.ax[2][idx[2]]
        m = region(X, Y, Z)
        if only is not None:
            ok = np.isin(self.col[idx], [self.ci(c) for c in only])
            m &= ok
        sel = tuple(i[m] for i in idx)
        if callable(colour):
            cols = colour(X[m], Y[m], Z[m])
            self.col[sel] = cols if (isinstance(cols, np.ndarray) and cols.dtype == np.uint16) else np.array([self.ci(c) for c in cols], np.uint16)
        else:
            self.col[sel] = self.ci(colour)

    def decal(self, img, center, right, down, size, normal, depth=2.0, keys=None):
        """Paint img (list of strings with keys, or an (h, w, 3) array) onto the outermost voxels facing `normal`
        around `center`; size = model px per image pixel."""
        right, down, normal = (np.asarray(v, float) / np.linalg.norm(v) for v in (right, down, normal))
        if isinstance(img, (list, tuple)):
            H, W = len(img), len(img[0])
        else:
            H, W = img.shape[:2]
        c = np.asarray(center, float)
        for yy in range(H):
            for xx in range(W):
                if isinstance(img, (list, tuple)):
                    ch = img[yy][xx]
                    if ch == '.':
                        continue
                    colour = keys[ch]
                else:
                    colour = img[yy, xx]
                    if len(colour) == 4 and colour[3] < 128:
                        continue
                    colour = colour[:3]
                p = c + right * (xx + 0.5 - W / 2) * size + down * (yy + 0.5 - H / 2) * size
                # march from outside inwards to the first filled voxel
                for k in np.arange(depth, -depth, -0.5 / self.res):
                    q = p + normal * k
                    i = np.floor((q - self.lo) * self.res).astype(int)
                    if np.any(i < 0) or np.any(i >= np.array(self.shape)):
                        continue
                    if self.col[tuple(i)]:
                        self.col[tuple(i)] = self.ci(colour)
                        break

    # ------------------------------------------------------------------ meshing
    def surfs(self, fig, tex=2, ao=True, light=None):
        """Greedy-meshed quads per bone added to fig's sculpt; each carries its texels in info['rgba']."""
        occ = self.col > 0
        pal = np.array(self.pal, np.float32)
        out = 0
        res = self.res
        dirs = [(0, -1), (0, 1), (1, -1), (1, 1), (2, -1), (2, 1)]
        names = {(0, -1): 'west', (0, 1): 'east', (1, -1): 'up', (1, 1): 'down', (2, -1): 'north', (2, 1): 'south'}
        for bi, bname in enumerate(self.bones):
            mine = occ & (self.bone == bi)
            if not mine.any():
                continue
            bone = fig.b[bname] if bname in fig.b else fig.r.by_name[bname]
            for ax, s in dirs:
                nb = np.roll(occ, -s, ax)
                nbb = np.roll(self.bone, -s, ax)
                # edge of the volume counts as empty
                edge = [slice(None)] * 3
                edge[ax] = -1 if s == 1 else 0
                nb[tuple(edge)] = False
                vis = mine & (~nb | (nbb != bi))
                if not vis.any():
                    continue
                n = self.shape[ax]
                for layer in range(n):
                    sl = [slice(None)] * 3
                    sl[ax] = layer
                    m2 = vis[tuple(sl)]
                    if not m2.any():
                        continue
                    cols2 = self.col[tuple(sl)]
                    out += self._greedy(fig, bone, m2, cols2, ax, s, layer, pal, tex, ao, occ, names[(ax, s)])
        return out

    def _greedy(self, fig, bone, m2, cols2, ax, s, layer, pal, tex, ao, occ, face):
        """Cover the face mask of one layer with maximal rectangles; one Surf per rectangle."""
        a1, a2 = [i for i in range(3) if i != ax]
        H, W = m2.shape                                  # indices along a1, a2
        done = np.zeros_like(m2)
        count = 0
        res = self.res
        for i in range(H):
            j = 0
            while j < W:
                if not m2[i, j] or done[i, j]:
                    j += 1
                    continue
                w = 1
                while j + w < W and m2[i, j + w] and not done[i, j + w]:
                    w += 1
                h = 1
                while i + h < H and m2[i + h, j:j + w].all() and not done[i + h, j:j + w].any():
                    h += 1
                done[i:i + h, j:j + w] = True
                self._quad(fig, bone, cols2[i:i + h, j:j + w], ax, s, layer, a1, a2, i, j, h, w, pal, tex, ao, occ, face)
                count += 1
                j += w
        return count

    def _quad(self, fig, bone, cols, ax, s, layer, a1, a2, i, j, h, w, pal, tex, ao, occ, face):
        res = self.res
        # corners in model coordinates: the face plane sits on the voxel's side
        plane = self.lo[ax] + (layer + (1 if s == 1 else 0)) / res
        def pt(ii, jj):
            p = np.zeros(3)
            p[ax] = plane
            p[a1] = self.lo[a1] + ii / res
            p[a2] = self.lo[a2] + jj / res
            return p
        # texels: rows along a1 (h voxels), columns along a2 (w voxels)
        rgb = pal[cols]                                         # (h, w, 3)
        if ao:
            k = self._ao(ax, s, layer, a1, a2, i, j, h, w, occ, tex)
            img = np.repeat(np.repeat(rgb, tex, 0), tex, 1) * k[..., None]
        else:
            img = np.repeat(np.repeat(rgb, tex, 0), tex, 1)
        bname = bone.name
        for ov in self.overlays:
            if ov['bone'] != bname or ov['face'] != face:
                continue
            # model coordinates of every texel centre
            ti = self.lo[a1] + (i + (np.arange(h * tex) + 0.5) / tex) / res
            tj = self.lo[a2] + (j + (np.arange(w * tex) + 0.5) / tex) / res
            G1, G2 = np.meshgrid(ti, tj, indexing='ij')
            coords = {a1: G1, a2: G2}
            x, y = coords.get(0), coords.get(1)
            if x is None or y is None:
                continue
            x0, y0, x1, y1 = ov['rect']
            oi = ov['img']
            OH, OW = oi.shape[:2]
            u = ((x - x0) / (x1 - x0) * OW).astype(int)
            v = ((y - y0) / (y1 - y0) * OH).astype(int)
            inside = (u >= 0) & (u < OW) & (v >= 0) & (v < OH)
            if not inside.any():
                continue
            src = oi[np.clip(v, 0, OH - 1), np.clip(u, 0, OW - 1)]
            a = (src[..., 3] / 255.0 if oi.shape[2] == 4 else np.ones(src.shape[:2]))[..., None] * inside[..., None]
            kk = self._ao(ax, s, layer, a1, a2, i, j, h, w, occ, tex)[..., None] if ao else 1.0
            img = img * (1 - a) + src[..., :3] * kk * a
        # orient the quad: vertices (i,j) (i,j+w) (i+h,j+w) (i+h,j); texel rows follow a1, columns a2
        V = np.array([pt(i, j), pt(i, j + w), pt(i + h, j + w), pt(i + h, j)])
        nrm = np.zeros(3)
        nrm[ax] = s
        # winding as bb.obox: (V1 - V0) x (V3 - V0) points inward
        if np.dot(np.cross(V[1] - V[0], V[3] - V[0]), nrm) > 0:
            V = V[[0, 3, 2, 1]]
            img = np.transpose(img, (1, 0, 2))
        Hh, Ww = img.shape[:2]
        UV = np.array([[0, 0], [Ww, 0], [Ww, Hh], [0, Hh]], float)
        info = dict(face=face, world=True, ao=False, rgba=img, vox=True)
        SC.S(fig.r).add(SC.Surf(bone, V, np.tile(nrm, (4, 1)), UV, [(0, 1, 2, 3)], (Ww, Hh), {'type': 'voxbaked'}, 'voxel', info, 'vox'))

    def _ao(self, ax, s, layer, a1, a2, i, j, h, w, occ, tex):
        """Per-texel occlusion of a face from the voxels in front of it: edges and corners next to a filled
        neighbour darken, like a voxel renderer's ambient occlusion."""
        out = np.ones((h * tex, w * tex), np.float32)
        lay = layer + s
        if lay < 0 or lay >= self.shape[ax]:
            return out
        sl = [slice(None)] * 3
        sl[ax] = lay
        front = occ[tuple(sl)]
        Hh, Ww = front.shape
        pad = np.zeros((Hh + 2, Ww + 2), bool)
        pad[1:-1, 1:-1] = front
        for ii in range(h):
            for jj in range(w):
                I, J = i + ii + 1, j + jj + 1
                n_up, n_dn, n_lf, n_rt = pad[I - 1, J], pad[I + 1, J], pad[I, J - 1], pad[I, J + 1]
                c_ul, c_ur, c_dl, c_dr = pad[I - 1, J - 1], pad[I - 1, J + 1], pad[I + 1, J - 1], pad[I + 1, J + 1]
                blk = out[ii * tex:(ii + 1) * tex, jj * tex:(jj + 1) * tex]
                for ti in range(tex):
                    for tj in range(tex):
                        top = ti < tex / 2
                        left = tj < tex / 2
                        e1 = n_up if top else n_dn
                        e2 = n_lf if left else n_rt
                        c = (c_ul if top and left else c_ur if top else c_dl if left else c_dr)
                        occl = 3 if (e1 and e2) else (int(e1) + int(e2) + int(c))
                        blk[ti, tj] = 1.0 - AO_STEP * occl
        return out


def paint_baked(s, ctx):
    img = s.info['rgba']
    H, W = s.size[1], s.size[0]
    if img.shape[:2] != (H, W):
        img = img[:H, :W]
    return np.clip(img[..., :3], 0, 255), None, None

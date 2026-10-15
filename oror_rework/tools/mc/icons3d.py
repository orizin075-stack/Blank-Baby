"""Inventory icons rendered from the 3D models: the item is laid on the Minecraft icon diagonal (grip low
left, tip high right) or stood upright, turned a little so its volume shows, rendered at 6x with the
in-game lights and reduced to pixel art: majority coverage, mean colour, emissive kept bright, and a
dark selective outline like vanilla item sprites."""
import math
import numpy as np
from PIL import Image
import forge3d as F
from rig import rot_zyx, raster
from colors import shade

def _rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])

def icon(quads, atlas, size=32, layout='diagonal', yaw=22, pitch=-14, ss=6, margin=1.0, flip=False):
    """layout: 'diagonal' (weapons) or 'upright' (worn / held objects); flip turns hanging items upright."""
    T = atlas.astype(np.float32) / 255.0
    R = np.eye(3)
    if flip:
        R = _rz(math.pi) @ R
    if layout == 'diagonal':
        R = _rz(-math.pi / 4) @ R
    V = rot_zyx(math.radians(pitch), 0, 0) @ rot_zyx(0, math.radians(yaw), 0)
    M = V @ R
    tris = []
    for P, UV, N, e in quads:
        Q = F.to_obj_space(P) - 0.5
        n = np.array([N[0], -N[1], -N[2]])
        Qv = Q @ M.T
        nv = M @ n
        if nv[2] <= 1e-6:
            continue
        nw = R @ n                       # lighting in the icon's own frame (light from the upper left front)
        tris.append((Qv, UV, nw, e))
    allp = np.concatenate([t[0] for t in tris])
    lo, hi = allp.min(0), allp.max(0)
    W = size * ss
    span = max(hi[0] - lo[0], hi[1] - lo[1])
    sc = (W - 2 * margin * ss) / span
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    img = np.zeros((W, W, 3), np.float32)
    cov = np.zeros((W, W), np.float32)
    zbuf = np.full((W, W), -1e9, np.float32)
    emit = np.zeros((W, W), np.float32)
    L = np.array([-0.45, 0.65, 0.62]); L /= np.linalg.norm(L)
    for P, UV, n, e in tris:
        S = np.stack([(P[:, 0] - cx) * sc + W / 2, -(P[:, 1] - cy) * sc + W / 2, P[:, 2]], 1)
        shade_v = 1.0 if e else 0.55 + 0.55 * max(0.0, float(n @ L)) + 0.12 * n[2]
        for j in range(1, len(S) - 1):
            idx = (0, j, j + 1)
            before = zbuf.copy()
            raster(img, zbuf, S[list(idx)], [tuple(UV[i]) for i in idx], T, None, 1.0, 1.0, min(1.25, shade_v))
            hit = zbuf != before
            cov[hit] = 1
            emit[hit] = 1.0 if e else 0.0
    # reduce to pixel art
    small = np.zeros((size, size, 4), np.float32)
    blk = img.reshape(size, ss, size, ss, 3)
    cb = cov.reshape(size, ss, size, ss)
    eb = emit.reshape(size, ss, size, ss)
    frac = cb.mean((1, 3))
    tot = cb.sum((1, 3))
    col = (blk * cb[..., None]).sum((1, 3)) / np.maximum(tot, 1)[..., None]
    solid = frac >= 0.34
    em = (eb.sum((1, 3)) / np.maximum(tot, 1)) >= 0.5
    small[..., :3] = col
    small[..., 3] = np.where(solid, 255, 0)
    # selective outline: darken silhouette pixels that face away from the light (lower right)
    from scipy import ndimage
    inner = ndimage.binary_erosion(solid, iterations=1, border_value=0)
    edge = solid & ~inner
    for y, x in zip(*np.nonzero(edge)):
        if em[y, x]:
            continue
        lower_right = (x + 1 >= size or not solid[y, x + 1]) or (y + 1 >= size or not solid[y + 1, x])
        small[y, x, :3] = np.array(shade(tuple(small[y, x, :3]), 0.55 if lower_right else 0.8))
    return Image.fromarray(np.clip(small, 0, 255).astype(np.uint8), 'RGBA')

def icon_for(key, quads, atlas, hold, kind, size=32):
    if kind in ('pendant', 'talisman'):
        return icon(quads, atlas, size, 'upright', yaw=20, pitch=-10, flip=True)
    if hold in ('shield', 'palm') or kind in ('book', 'chakram', 'gauntlet', 'claws'):
        return icon(quads, atlas, size, 'upright', yaw=24, pitch=-12)
    if kind in ('plush', 'marionette'):
        return icon(quads, atlas, size, 'upright', yaw=24, pitch=-12, flip=True)
    return icon(quads, atlas, size, 'diagonal')

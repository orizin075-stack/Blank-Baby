"""The user's character design sheets (oror_rework/designs/sheets/NN_*.jpg): cut the figures out of a sheet, fit an
orthographic camera to each view of a 3D model, and paint the model's texture by projecting the sheet onto it.

A sheet shows one character as a Minecraft-style render on a grey backdrop: a front three-quarter view, a back view and
close-ups. The views to use are given per character as boxes (sheet pixels); everything inside a box that stands out
from the backdrop is the figure.

Run with python3 -I (the sheets are input data).
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
SHEETS = os.path.normpath(os.path.join(HERE, '..', '..', 'designs', 'sheets'))


def load(name):
    for f in sorted(os.listdir(SHEETS)):
        if f.startswith(name) and f.lower().endswith(('.jpg', '.png')):
            return np.asarray(Image.open(os.path.join(SHEETS, f)).convert('RGB')).astype(np.float32)
    raise FileNotFoundError(name)


def backdrop(im):
    """Smooth estimate of the grey backdrop: grey, mid-light texels, median-filtered and spread over the figures."""
    lum = im.mean(-1)
    sat = im.max(-1) - im.min(-1)
    mode = np.median(lum[:16].ravel().tolist() + lum[-16:].ravel().tolist() + lum[:, :16].ravel().tolist() + lum[:, -16:].ravel().tolist())
    cand = (sat < 10) & (np.abs(lum - mode) < 18)
    s = 8                                              # work on a coarse grid
    h, w = lum.shape
    gh, gw = h // s, w // s
    acc = np.zeros((gh, gw, 3), np.float32)
    cnt = np.zeros((gh, gw), np.float32)
    c = cand[:gh * s, :gw * s].reshape(gh, s, gw, s)
    v = im[:gh * s, :gw * s].reshape(gh, s, gw, s, 3)
    acc = (v * c[..., None]).sum((1, 3))
    cnt = c.sum((1, 3))
    good = cnt > s * s * 0.6
    mean = np.where(good[..., None], acc / np.maximum(cnt, 1)[..., None], 0)
    idx = ndimage.distance_transform_edt(~good, return_distances=False, return_indices=True)
    mean = mean[idx[0], idx[1]]
    for k in range(3):
        mean[..., k] = ndimage.uniform_filter(mean[..., k], 9)
    big = np.repeat(np.repeat(mean, s, 0), s, 1)
    out = np.zeros_like(im)
    out[:big.shape[0], :big.shape[1]] = big
    out[big.shape[0]:, :] = out[big.shape[0] - 1:big.shape[0], :]
    out[:, big.shape[1]:] = out[:, big.shape[1] - 1:big.shape[1]]
    return out


def figure_mask(im, box, thresh=16.0, min_area=40):
    """Foreground inside box (x0, y0, x1, y1): texels that differ from the backdrop, closed, holes filled, specks dropped."""
    bg = backdrop(im)
    x0, y0, x1, y1 = box
    d = np.abs(im - bg).max(-1)
    sat = im.max(-1) - im.min(-1)
    fg = (d > thresh) | (sat > 22)
    m = np.zeros(fg.shape, bool)
    m[y0:y1, x0:x1] = fg[y0:y1, x0:x1]
    m = ndimage.binary_closing(m, iterations=2)
    m = ndimage.binary_fill_holes(m)
    m = ndimage.binary_opening(m, iterations=1)
    lab, n = ndimage.label(m)
    if n:
        areas = ndimage.sum(m, lab, range(1, n + 1))
        keep = np.zeros(n + 1, bool)
        keep[1:] = areas >= min_area
        m = keep[lab]
    return m


def fill_out(im, mask, grow=None):
    """Spread the figure's colours outward over the backdrop (nearest figure texel), so a model edge that falls just
    outside the drawn silhouette takes the colour of the part it belongs to rather than the grey backdrop."""
    idx = ndimage.distance_transform_edt(~mask, return_distances=False, return_indices=True)
    return im[idx[0], idx[1]]


# ------------------------------------------------------------------------------------------------- camera
def view_matrix(yaw, pitch):
    """Model (x, y down, front -z) -> view (x right, y down, z towards the camera)."""
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    # model -> world with y up and the front towards the camera (as sculpt.render), then yaw about y and pitch about x
    F = np.diag([1.0, -1.0, -1.0])
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    Wv = Rx @ Ry @ F
    return np.diag([1.0, -1.0, 1.0]) @ Wv          # back to y down on screen; z stays towards the camera


class Camera:
    def __init__(self, yaw, pitch, scale, u0, v0):
        self.yaw, self.pitch, self.scale, self.u0, self.v0 = yaw, pitch, scale, u0, v0
        self.R = view_matrix(yaw, pitch)

    def project(self, P):
        Q = P.reshape(-1, 3) @ self.R.T
        u = Q[:, 0] * self.scale + self.u0
        v = Q[:, 1] * self.scale + self.v0
        return np.stack([u, v, Q[:, 2] * self.scale], 1).reshape(P.shape)

    def unproject(self, u, v, z):
        """Model point (x, y, z) that lands on sheet pixel (u, v), for a given model depth z (front -, back +)."""
        R = self.R
        a = np.array([[R[0, 0], R[0, 1]], [R[1, 0], R[1, 1]]])
        b = np.array([(u - self.u0) / self.scale - R[0, 2] * z, (v - self.v0) / self.scale - R[1, 2] * z])
        x, y = np.linalg.solve(a, b)
        return (round(float(x), 2), round(float(y), 2), z)

    def unproject_y(self, u, v, y):
        """Model point on the horizontal plane at height y (e.g. the ground) that lands on sheet pixel (u, v)."""
        R = self.R
        a = np.array([[R[0, 0], R[0, 2]], [R[1, 0], R[1, 2]]])
        b = np.array([(u - self.u0) / self.scale - R[0, 1] * y, (v - self.v0) / self.scale - R[1, 1] * y])
        x, z = np.linalg.solve(a, b)
        return (round(float(x), 2), y, round(float(z), 2))

    def towards(self):
        """Unit vector in model space pointing from the model towards the camera."""
        return self.R.T @ np.array([0.0, 0.0, 1.0])

    def __repr__(self):
        return f'Camera(yaw={self.yaw:.1f}, pitch={self.pitch:.1f}, scale={self.scale:.3f}, u0={self.u0:.1f}, v0={self.v0:.1f})'


def triangulate(cams, pts):
    """Least-squares model point seen at pts[i] = (u, v) through cams[i]."""
    A, b = [], []
    for c, (u, v) in zip(cams, pts):
        A.append(c.scale * c.R[0]); b.append(u - c.u0)
        A.append(c.scale * c.R[1]); b.append(v - c.v0)
    P, *_ = np.linalg.lstsq(np.array(A), np.array(b), rcond=None)
    return tuple(round(float(x), 2) for x in P)


def triangles(rig, pose=None):
    """All model triangles in rest-pose model coordinates (n, 3, 3), with the surface each came from."""
    import sculpt as SC
    mats = SC.bone_matrices(rig, pose)
    tris, owner = [], []
    for i, s in enumerate(rig.sculpt.surfs):
        if s.info.get('lids'):
            continue
        P, _ = SC.surf_world(s, mats)
        for q in s.Q:
            tris.append(P[[q[0], q[1], q[2]]]); owner.append(i)
            tris.append(P[[q[0], q[2], q[3]]]); owner.append(i)
    return np.array(tris, float), np.array(owner)


def raster(tris_uvz, shape, want_id=False):
    """Z-buffer of screen-space triangles (n, 3, 3: u, v, depth towards camera). Returns depth (and triangle id)."""
    H, W = shape
    zb = np.full((H, W), -1e9, np.float32)
    tid = np.full((H, W), -1, np.int32)
    for i, T in enumerate(tris_uvz):
        Sx, Sy, Z = T[:, 0], T[:, 1], T[:, 2]
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
        m = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        if not m.any():
            continue
        z = l1 * Z[0] + l2 * Z[1] + l3 * Z[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        m &= z > sub
        if m.any():
            sub[m] = z[m]
            if want_id:
                tid[y0:y1 + 1, x0:x1 + 1][m] = i
    return (zb, tid) if want_id else zb


def silhouette(tris, cam, shape):
    return raster(cam.project(tris), shape) > -1e8


def iou(a, b):
    return float((a & b).sum()) / max(1.0, float((a | b).sum()))


def fit_camera(tris, mask, yaw0, pitch0=10.0, yaw_span=40.0, pitch_span=14.0, steps=3, work=0.25):
    """Fit yaw, pitch, scale and offset so the model's silhouette matches the mask (IoU), coarse to fine, on a
    downscaled copy of the mask for speed."""
    small = ndimage.zoom(mask.astype(np.float32), work, order=1) > 0.5
    H, W = small.shape
    ys, xs = np.nonzero(small)
    mh = ys.max() - ys.min() + 1
    mcx, mcy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2

    def place(yaw, pitch):
        """Scale and offset so the projected model's bounding box height and centre match the mask."""
        R = view_matrix(yaw, pitch)
        Q = tris.reshape(-1, 3) @ R.T
        h = Q[:, 1].max() - Q[:, 1].min()
        sc = mh / max(h, 1e-6)
        u0 = mcx - (Q[:, 0].max() + Q[:, 0].min()) / 2 * sc
        v0 = mcy - (Q[:, 1].max() + Q[:, 1].min()) / 2 * sc
        return Camera(yaw, pitch, sc, u0, v0)

    def score(c):
        return iou(silhouette(tris, c, (H, W)), small)

    best = None
    yaws = np.linspace(yaw0 - yaw_span, yaw0 + yaw_span, 9)
    pitches = np.linspace(pitch0 - pitch_span, pitch0 + pitch_span, 5)
    plo, phi = pitch0 - pitch_span, pitch0 + pitch_span
    ylo, yhi = yaw0 - yaw_span, yaw0 + yaw_span
    for y in yaws:
        for p in pitches:
            c = place(y, p)
            s = score(c)
            if best is None or s > best[0]:
                best = (s, c)
    dy, dp, ds, do = yaw_span / 8, pitch_span / 4, 0.06, 4.0
    for _ in range(steps * 4):
        s0, c0 = best
        improved = False
        for cand in (Camera(c0.yaw + dy, c0.pitch, c0.scale, c0.u0, c0.v0), Camera(c0.yaw - dy, c0.pitch, c0.scale, c0.u0, c0.v0),
                     Camera(c0.yaw, c0.pitch + dp, c0.scale, c0.u0, c0.v0), Camera(c0.yaw, c0.pitch - dp, c0.scale, c0.u0, c0.v0),
                     Camera(c0.yaw, c0.pitch, c0.scale * (1 + ds), c0.u0, c0.v0), Camera(c0.yaw, c0.pitch, c0.scale * (1 - ds), c0.u0, c0.v0),
                     Camera(c0.yaw, c0.pitch, c0.scale, c0.u0 + do, c0.v0), Camera(c0.yaw, c0.pitch, c0.scale, c0.u0 - do, c0.v0),
                     Camera(c0.yaw, c0.pitch, c0.scale, c0.u0, c0.v0 + do), Camera(c0.yaw, c0.pitch, c0.scale, c0.u0, c0.v0 - do)):
            if not (ylo <= cand.yaw <= yhi and plo <= cand.pitch <= phi):
                continue
            s = score(cand)
            if s > best[0] + 1e-5:
                best = (s, cand)
                improved = True
        if not improved:
            dy, dp, ds, do = dy / 2, dp / 2, ds / 2, do / 2
    s, c = best
    return s, Camera(c.yaw, c.pitch, c.scale / work, c.u0 / work, c.v0 / work)


# ------------------------------------------------------------------------------------------------- projection
class View:
    """One view of the sheet: the image (backdrop filled from the figure), the figure mask, the fitted camera and the
    model's depth buffer seen through it."""
    def __init__(self, im, mask, cam, tris, weight=1.0):
        self.mask, self.cam, self.weight = mask, cam, weight
        self.img = fill_out(im, mask)
        self.zbuf = raster(cam.project(tris), mask.shape)
        self.dir = cam.towards()

    def sample(self, P, N, tol=1.2):
        """Colour (n, 3), facing weight (n,) for model points P with normals N; weight 0 where hidden or facing away."""
        Q = self.cam.project(P)
        u, v, z = Q[:, 0], Q[:, 1], Q[:, 2]
        H, W = self.mask.shape
        ui = np.clip(np.floor(u).astype(int), 0, W - 1)
        vi = np.clip(np.floor(v).astype(int), 0, H - 1)
        inside = (u >= 0) & (u < W) & (v >= 0) & (v < H)
        # visible when nothing in front within a tolerance (sheet pixels); test a small neighbourhood so texels on an
        # edge are not lost to rasterisation
        zt = self.zbuf[vi, ui]
        vis = z >= zt - tol * self.cam.scale
        facing = np.clip(N @ self.dir, 0, 1)
        w = np.where(inside & vis, facing, 0.0) * self.weight
        col = bilinear(self.img, u, v)
        return col, w


def bilinear(img, u, v):
    H, W = img.shape[:2]
    x = np.clip(u - 0.5, 0, W - 1.001)
    y = np.clip(v - 0.5, 0, H - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    a = img[y0, x0]; b = img[y0, x0 + 1]; c = img[y0 + 1, x0]; d = img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def integral(img):
    H, W = img.shape[:2]
    S = np.zeros((H + 1, W + 1, img.shape[2]), np.float64)
    S[1:, 1:] = img.cumsum(0).cumsum(1)
    return S


def area_sample(img, u, v, r, S=None):
    """Mean colour over a (2r+1)^2 box around each point, via an integral image: one model texel covers several
    sheet pixels, and a point sample would pick up JPEG noise and single dark outline pixels."""
    if r <= 0:
        return bilinear(img, u, v)
    H, W = img.shape[:2]
    if S is None:
        S = integral(img)
    x0 = np.clip(np.floor(u - r).astype(int), 0, W - 1); x1 = np.clip(np.floor(u + r).astype(int) + 1, 1, W)
    y0 = np.clip(np.floor(v - r).astype(int), 0, H - 1); y1 = np.clip(np.floor(v + r).astype(int) + 1, 1, H)
    tot = S[y1, x1] - S[y0, x1] - S[y1, x0] + S[y0, x0]
    n = np.maximum(1, (x1 - x0) * (y1 - y0))[:, None]
    return (tot / n).astype(np.float32)


def median_sample(img, u, v, r):
    """Median colour (by luminance rank) over a (2r+1)^2 neighbourhood: keeps the sheet's flat voxel colours crisp
    where a mean would blend two blocks into a third colour."""
    H, W = img.shape[:2]
    k = max(1, int(round(r)))
    offs = [(dx, dy) for dx in range(-k, k + 1, max(1, k // 2)) for dy in range(-k, k + 1, max(1, k // 2))]
    xs = np.clip(np.floor(u).astype(int)[:, None] + np.array([o[0] for o in offs])[None], 0, W - 1)
    ys = np.clip(np.floor(v).astype(int)[:, None] + np.array([o[1] for o in offs])[None], 0, H - 1)
    c = img[ys, xs]                                     # (n, m, 3)
    lum = c @ np.array([0.299, 0.587, 0.114], np.float32)
    order = np.argsort(lum, axis=1)
    mid = order[:, order.shape[1] // 2]
    return c[np.arange(len(c)), mid]


def palette(img, mask, k=40, seed=3):
    """k colours for the figure (k-means in a perceptual-ish space, seeded from luminance quantiles)."""
    px = img[mask].reshape(-1, 3).astype(np.float32)
    rng = np.random.default_rng(seed)
    if len(px) > 60000:
        px = px[rng.choice(len(px), 60000, replace=False)]
    w = np.array([0.8, 1.0, 0.6], np.float32)           # weigh green (luminance) most
    X = px * w
    lum = px @ np.array([0.299, 0.587, 0.114], np.float32)
    cent = X[np.argsort(lum)[np.linspace(0, len(X) - 1, k).astype(int)]].copy()
    for _ in range(14):
        d = ((X[:, None, :] - cent[None]) ** 2).sum(-1)
        a = d.argmin(1)
        for j in range(k):
            m = a == j
            if m.any():
                cent[j] = X[m].mean(0)
            else:
                cent[j] = X[rng.integers(len(X))]
    return cent / w


def snap(rgb, pal):
    w = np.array([0.8, 1.0, 0.6], np.float32)
    flat = rgb.reshape(-1, 3).astype(np.float32) * w
    P = pal.astype(np.float32) * w
    out = np.empty(len(flat), np.int64)
    for i in range(0, len(flat), 20000):
        d = ((flat[i:i + 20000, None, :] - P[None]) ** 2).sum(-1)
        out[i:i + 20000] = d.argmin(1)
    return pal[out].reshape(rgb.shape)


def overlay(im, mask, sil, path, box=None):
    """Sheet with the drawn silhouette (cyan edge) and the model's silhouette (magenta edge) for checking a fit."""
    out = im.copy()
    e1 = mask ^ ndimage.binary_erosion(mask, iterations=2)
    e2 = sil ^ ndimage.binary_erosion(sil, iterations=2)
    out[sil] = out[sil] * 0.65 + np.array([255, 60, 200]) * 0.35
    out[e1] = (0, 255, 255)
    out[e2] = (255, 0, 200)
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))
    if box:
        img = img.crop(box)
    img.save(path)
    return img

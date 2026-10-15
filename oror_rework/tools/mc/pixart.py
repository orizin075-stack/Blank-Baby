"""Vector-to-pixel-art renderer for weapons and relics.

Designs are written once in a local frame (u along the weapon from butt 0 to tip 100, v across) and
rasterised at any size: as a 32px inventory icon (diagonal, Minecraft item convention) or as a large
upright sprite that is painted on the cut-out planes of the 3D prop. Each shape has a material; shading
comes from the shape's own distance field (light from the upper left), with polished highlights on
metal, faceted gems, soft cloth, grain on wood, bright cores on energy, selective outlines and a glow
mask for the emissive layer."""
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from colors import hexc, shade, mix

LIGHT = np.array([-0.62, -0.78])          # towards the light, image space (x right, y down)

def mat(style, color, glow=0.0, **kw):
    d = {'style': style, 'color': color, 'glow': glow}
    d.update(kw)
    return d

class Frame:
    def __init__(self, w, h, origin, axis, scale):
        self.w, self.h = w, h
        self.o = np.array(origin, float)
        a = np.array(axis, float)
        self.a = a / np.linalg.norm(a)
        self.p = np.array([-self.a[1], self.a[0]])     # perpendicular, to the right of the axis
        self.s = scale

    def px(self, u, v):
        q = self.o + self.a * (u * self.s) + self.p * (v * self.s)
        return float(q[0]), float(q[1])

class Art:
    def __init__(self, frame):
        self.f = frame
        self.shapes = []

    # ------------------------------------------------------------------ shapes (design units)
    def _mask_from_poly(self, pts):
        im = Image.new('L', (self.f.w, self.f.h), 0)
        d = ImageDraw.Draw(im)
        pp = [self.f.px(u, v) for u, v in pts]
        if len(pp) >= 3:
            d.polygon(pp, fill=255)
        elif len(pp) == 2:
            d.line(pp, fill=255, width=1)
        return np.asarray(im) > 0

    def poly(self, pts, m, z=0, mirror=False):
        mk = self._mask_from_poly(pts)
        if mirror:
            mk |= self._mask_from_poly([(u, -v) for u, v in pts])
        self._add(mk, m, z)
        return mk

    def sym(self, half, m, z=0):
        """Symmetric polygon from its v >= 0 half outline (u, v) listed from butt to tip."""
        pts = list(half) + [(u, -v) for u, v in reversed(half)]
        return self.poly(pts, m, z)

    def ell(self, cu, cv, ru, rv, m, z=0, n=28):
        pts = [(cu + ru * math.cos(2 * math.pi * k / n), cv + rv * math.sin(2 * math.pi * k / n)) for k in range(n)]
        return self.poly(pts, m, z)

    def ring(self, cu, cv, r_out, r_in, m, z=0, n=36, rv_scale=1.0):
        outer = self._mask_from_poly([(cu + r_out * math.cos(2 * math.pi * k / n), cv + r_out * rv_scale * math.sin(2 * math.pi * k / n)) for k in range(n)])
        inner = self._mask_from_poly([(cu + r_in * math.cos(2 * math.pi * k / n), cv + r_in * rv_scale * math.sin(2 * math.pi * k / n)) for k in range(n)])
        self._add(outer & ~inner, m, z)

    def stroke(self, pts, width, m, z=0, taper=None):
        """Thick polyline; taper=(w0, w1) varies the width from the first to the last point."""
        mk = np.zeros((self.f.h, self.f.w), bool)
        n = len(pts)
        for i in range(n - 1):
            (u0, v0), (u1, v1) = pts[i], pts[i + 1]
            du, dv = u1 - u0, v1 - v0
            L = math.hypot(du, dv) or 1
            nu, nv = -dv / L, du / L
            if taper:
                w0 = taper[0] + (taper[1] - taper[0]) * i / max(1, n - 1)
                w1 = taper[0] + (taper[1] - taper[0]) * (i + 1) / max(1, n - 1)
            else:
                w0 = w1 = width
            quad = [(u0 + nu * w0 / 2, v0 + nv * w0 / 2), (u1 + nu * w1 / 2, v1 + nv * w1 / 2),
                    (u1 - nu * w1 / 2, v1 - nv * w1 / 2), (u0 - nu * w0 / 2, v0 - nv * w0 / 2)]
            mk |= self._mask_from_poly(quad)
            r = w1 / 2
            if i < n - 2 and r * self.f.s >= 0.8:
                mk |= self._mask_from_poly([(u1 + r * math.cos(a), v1 + r * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 12)])
        self._add(mk, m, z)
        return mk

    def curve(self, p0, p1, p2, width, m, z=0, steps=16, taper=None):
        pts = [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
               for t in np.linspace(0, 1, steps)]
        return self.stroke(pts, width, m, z, taper)

    def dot(self, u, v, m, z=5, r=0.0):
        """A single crisp pixel (or a small disc) at a design point: rivets, sparkles, gem cores."""
        x, y = self.f.px(u, v)
        mk = np.zeros((self.f.h, self.f.w), bool)
        xi, yi = int(math.floor(x)), int(math.floor(y))
        rr = max(0, int(round(r * self.f.s)))
        for dy in range(-rr, rr + 1):
            for dx in range(-rr, rr + 1):
                if dx * dx + dy * dy <= rr * rr + 0.5 and 0 <= yi + dy < self.f.h and 0 <= xi + dx < self.f.w:
                    mk[yi + dy, xi + dx] = True
        self._add(mk, dict(m, outline=False, flat=True), z)

    def _add(self, mk, m, z):
        if mk.any():
            self.shapes.append((mk, m, z, len(self.shapes)))

    # ------------------------------------------------------------------ render
    def render(self, outline='#140f1c'):
        H, W = self.f.h, self.f.w
        order = sorted(self.shapes, key=lambda s: (s[2], s[3]))
        owner = -np.ones((H, W), int)
        for k, (mk, m, z, i) in enumerate(order):
            owner[mk] = k
        rgb = np.zeros((H, W, 3), np.float32)
        alpha = np.zeros((H, W), np.float32)
        glow = np.zeros((H, W, 4), np.float32)
        union = owner >= 0
        yy, xx = np.mgrid[0:H, 0:W]
        for k, (mk, m, z, i) in enumerate(order):
            vis = owner == k
            if not vis.any():
                continue
            c = hexc(m['color'])
            if m.get('flat'):
                rgb[vis] = c
                alpha[vis] = 1
                if m.get('glow'):
                    glow[vis, :3] = np.array(c, np.float32) * m['glow']
                    glow[vis, 3] = 255
                continue
            d = ndimage.distance_transform_edt(np.pad(mk, 1))[1:-1, 1:-1]
            gy, gx = np.gradient(ndimage.gaussian_filter(d, 0.7))
            nrm = np.stack([-gx, -gy], -1)
            ln = np.linalg.norm(nrm, axis=-1, keepdims=True)
            nrm = np.where(ln > 1e-6, nrm / np.maximum(ln, 1e-6), 0)
            ndl = nrm @ LIGHT
            style = m['style']
            dmax = max(1.0, d[mk].max())
            edge = np.exp(-(d - 1) / max(1.0, dmax * 0.45))
            if style == 'metal':
                tone = 1.5 * ndl * edge + 0.4 * (1 - d / dmax) * 0
                tone += np.where((ndl > 0.45) & (d <= 1.6), 1.2, 0)
                tone -= np.where((ndl < -0.45) & (d <= 1.6), 0.8, 0)
                # polished streak across the shape
                cyy, cxx = yy[mk].mean(), xx[mk].mean()
                streak = np.abs((xx - cxx) + (yy - cyy) - (dmax * 0.4)) < 0.7
                tone += np.where(streak & (d > 1.5), 0.9, 0)
            elif style == 'gem':
                cyy, cxx = yy[mk].mean(), xx[mk].mean()
                ang = np.arctan2(yy - cyy, xx - cxx)
                facet = np.cos(np.round(ang / (math.pi / 3)) * (math.pi / 3) - math.atan2(LIGHT[1], LIGHT[0]))
                tone = 1.2 * facet * (d / dmax) + 0.9 * ndl * edge
                tl = (np.abs(xx - (cxx - dmax * 0.35)) <= 0.6) & (np.abs(yy - (cyy - dmax * 0.35)) <= 0.6)
                tone += np.where(tl, 2.0, 0)
            elif style == 'energy':
                tone = 1.2 + 0.8 * (d / dmax) + 0.5 * ndl * edge
            elif style == 'wood':
                grain = np.sin((xx * 0.9 + yy * 0.25) * 1.7 + (xx % 3)) > 0.6
                tone = 0.9 * ndl * edge - np.where(grain, 0.6, 0)
            elif style == 'dark':
                tone = 0.8 * ndl * edge - 0.3
            else:   # cloth, leather, bone, paper, scale, fur
                tone = 0.95 * ndl * edge
                if style == 'scale':
                    tone -= np.where(((xx + (yy // 2) % 2) % 2 == 0) & (yy % 2 == 0), 0.6, 0)
                if style == 'fur':
                    tone -= np.where((xx * 7 + yy * 3) % 5 == 0, 0.7, 0)
            pat = m.get('pattern')
            if pat == 'wrap':
                tone -= np.where(((xx + yy) % 3 == 0) | ((xx - yy) % 3 == 0), 0.9, 0)
            elif pat == 'stripes':
                tone -= np.where(((xx - yy) // 2) % 2 == 0, 0.8, 0)
            elif pat == 'runes':
                rune = ((xx * 5 + yy * 3) % 7 == 0) & (d > 1.5)
                pc = np.array(hexc(m.get('accent', '#ffffff')), np.float32)
            elif pat == 'dots':
                tone += np.where((xx % 3 == 1) & (yy % 3 == 1), 0.8, 0)
            q = np.clip(np.round(tone * 2) / 2, -3, 2.5)
            for lv in np.unique(q[vis]):
                sel = vis & (q == lv)
                rgb[sel] = shade(c, 1 + 0.16 * float(lv)) if lv else c
            if pat == 'runes':
                rgb[vis & rune] = pc
            alpha[vis] = 1
            g = m.get('glow', 0)
            if g:
                glow[vis, :3] = rgb[vis] * g
                glow[vis, 3] = 255
                if pat == 'runes':
                    glow[vis & rune, :3] = pc
            elif pat == 'runes' and m.get('rune_glow', True):
                glow[vis & rune, :3] = pc
                glow[vis & rune, 3] = 255
            # separation line where a higher shape overlaps this one
            if m.get('outline', True):
                sep = vis & ndimage.binary_dilation(owner > k, structure=ndimage.generate_binary_structure(2, 1))
                rgb[sep] = np.array(shade(c, 0.62), np.float32)
        # silhouette outline: darkened version of the pixel's own colour, lighter on lit edges
        if outline:
            border = union & ~ndimage.binary_erosion(union, iterations=1, border_value=0)
            dd = ndimage.distance_transform_edt(np.pad(union, 1))[1:-1, 1:-1]
            gy, gx = np.gradient(ndimage.gaussian_filter(dd, 0.6))
            lit = (-gx * LIGHT[0] - gy * LIGHT[1]) > 0.25
            for k, (mk, m, z, i) in enumerate(order):
                if not m.get('outline', True):
                    continue
                sel = border & (owner == k)
                if not sel.any():
                    continue
                c = hexc(m['color'])
                dark = np.array(mix(shade(c, 0.4), outline, 0.4), np.float32)
                light = np.array(shade(c, 0.66), np.float32)
                rgb[sel & lit] = light
                rgb[sel & ~lit] = dark
                if m.get('glow'):
                    glow[sel, :3] = rgb[sel] * m['glow']
        rgba = np.concatenate([np.clip(rgb, 0, 255), (alpha * 255)[..., None]], -1).astype(np.uint8)
        return rgba, glow

def icon_frame(size=32, upright=False, margin=1.5, length=None):
    if upright:
        L = size - 2 * margin
        return Frame(size, size, (size / 2, size - margin), (0, -1), L / 100.0)
    L = (size - 2 * margin) * math.sqrt(2) * 0.98 if length is None else length
    o = (margin + 0.5, size - margin - 0.5)
    return Frame(size, size, o, (1, -1), L / 100.0)

def sprite_frame(length_px, half_width_units, scale=None):
    s = length_px / 100.0 if scale is None else scale
    w = int(math.ceil(half_width_units * 2 * s)) + 4
    h = int(math.ceil(100 * s)) + 4
    return Frame(w, h, (w / 2, h - 2), (0, -1), s)

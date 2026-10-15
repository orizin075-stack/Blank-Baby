"""Reusable sculpted parts for 3D relic weapons (weapon space: u up the axis, v across, w depth; texels)."""
import math
from pixart import mat as pmat
from paint import M

class Mt:
    """One material spec usable both on relief plates (pixart) and on boxes (paint)."""
    PX = {'metal': 'metal', 'gem': 'gem', 'energy': 'energy', 'dark': 'dark', 'cloth': 'cloth', 'wood': 'wood',
          'bone': 'cloth', 'scale': 'scale', 'fur': 'fur', 'crystal': 'gem', 'leather': 'cloth'}
    BX = {'metal': 'metal', 'gem': 'gem', 'energy': 'energy', 'dark': 'metal', 'cloth': 'cloth', 'wood': 'wood',
          'bone': 'bone', 'scale': 'scale', 'fur': 'fur', 'crystal': 'gem', 'leather': 'cloth'}

    def __init__(self, kind, color, glow=0.0, **kw):
        self.kind, self.color, self.glow, self.kw = kind, color, glow, kw

    def p(self, **kw):
        d = dict(self.kw.get('px', {}))
        d.update(kw)
        g = d.pop('glow', self.glow)
        if self.kind in ('energy',) and not g:
            g = 0.9
        if self.kind in ('gem', 'crystal') and not g:
            g = 0.6
        return pmat(self.PX[self.kind], self.color, glow=g, **d)

    def b(self, **kw):
        d = dict(self.kw.get('bx', {}))
        d.update(kw)
        t = self.BX[self.kind]
        if t == 'cloth':
            d.setdefault('hem_shadow', False)
            d.setdefault('round', False)
        if self.kind == 'gem' or self.kind == 'crystal':
            d.setdefault('glow', True)
        return M(t, self.color, **d)

    def tint(self, color, **kw):
        k = dict(self.kw)
        k.update(kw)
        return Mt(self.kind, color, self.glow, **k)

def runes(base, accent, kind='runes'):
    """Box material with glowing engraved pattern."""
    return M('metal', base, pattern=kind, accent=accent, pattern_glow=True, glow_amount=0.9)

# ------------------------------------------------------------------------------------------- axis parts
def octo(g, u, du, r, mt, name='octo', taper=None):
    """Octagonal prism along the axis, centred at u, radius r (texels); mt: Mt or paint dict."""
    m = mt.b() if isinstance(mt, Mt) else mt
    s = max(1, round(2 * r))
    g.box(u, 0, 0, du, s, s, m, name=name)
    s2 = max(1, round(2 * r * 0.82))
    g.box(u, 0, 0, du, s2, s2, m, rot=(45, 0, 0), name=name + 'x')

def grip(g, u0, u1, r, mt, bands=None, band_mt=None, name='grip'):
    octo(g, (u0 + u1) / 2, u1 - u0, r, mt, name)
    for k, ub in enumerate(bands or ()):
        octo(g, ub, 1, r + 0.6, band_mt or mt, f'{name}_band{k}')

def collar(g, u, du, r, mt, name='collar'):
    octo(g, u, du, r, mt, name)

def cone(g, u, du, r0, r1, mt, steps=3, name='cone'):
    """Stepped octagonal taper from radius r0 at u to r1 at u + du."""
    for i in range(steps):
        t = (i + 0.5) / steps
        octo(g, u + du * (i + 0.5) / steps, du / steps, r0 + (r1 - r0) * t, mt, f'{name}{i}')

def gem(g, u, v, w, s, color, name='gem', facet=True):
    m = M('gem', color, glow=True)
    g.box(u, v, w, s, s, s, m, name=name)
    if facet and s >= 3:
        g.box(u, v, w, s - 1, s - 1, s - 1, m, rot=(45, 45, 0), name=name + 'f')

def crystal(g, u, v, w, length, thick, color, rot=(0, 0, 0), name='crystal'):
    """Elongated glowing shard: a long box with a pointed 45-degree cap."""
    c = g.group(u, v, w, rot=rot, name=name)
    m = M('gem', color, glow=True)
    c.box(0, 0, 0, length, thick, thick, m, name=name + 'b')
    t2 = max(1, round(thick * 0.72))
    c.box(length / 2, 0, 0, t2, t2, t2, m, rot=(45, 0, 45), name=name + 't')
    return c

def spikes(g, u, n, r, length, thick, mt, tilt=35, phase=0.0, name='spike'):
    """Radial spikes around the axis at height u, leaning up by (90 - tilt) degrees."""
    m = mt.b() if isinstance(mt, Mt) else mt
    for k in range(n):
        a = phase + 360.0 * k / n
        ring = g.group(u, 0, 0, rot=(a, 0, 0), name=f'{name}r{k}')
        sp = ring.group(0, r, 0, rot=(0, 0, -(90 - tilt)), name=f'{name}{k}')
        sp.box(length / 2, 0, 0, length, thick, thick, m, name=f'{name}{k}a')
        if length >= 4 and thick >= 2:
            sp.box(length + 1, 0, 0, 2, max(1, thick - 1), max(1, thick - 1), m, name=f'{name}{k}b')

def fin(g, u, v, w, length, width, mt, rot=(0, 0, 0), name='fin'):
    """A thin blade-like fin (flat box)."""
    f = g.group(u, v, w, rot=rot, name=name)
    m = mt.b() if isinstance(mt, Mt) else mt
    f.box(length / 2, 0, 0, length, width, 1, m, name=name + 'a')
    return f

def chain(g, pts, mt, size=2, name='chain'):
    """Links along a list of (u, v, w) points, alternately turned 90 degrees."""
    m = mt.b() if isinstance(mt, Mt) else mt
    for k, (u, v, w) in enumerate(pts):
        g.box(u, v, w, size + 1, size, 1 if k % 2 == 0 else size, m, rot=(0 if k % 2 == 0 else 90, 0, 0), name=f'{name}{k}')

# ------------------------------------------------------------------------------------------- plates
def halo(g, u, r_out, r_in, mt, spokes=0, spikes_n=0, w=0.0, tilt=0, name='halo', d=0.5):
    """A ring plate lying across the axis (in the v-w plane) at height u."""
    grp = g.group(u, 0, w, rot=(0, tilt, 0), name=name) if tilt else g
    p = grp.plate(-r_out - 3, r_out + 3, -r_out - 3, r_out + 3, u=0 if tilt else u, w=0 if tilt else w,
                  U=(0, 0, 1), V=(0, 1, 0))
    p.ring(0, 0, r_out, r_in, mt.p(d=d) if isinstance(mt, Mt) else mt)
    for k in range(spikes_n):
        a = 2 * math.pi * k / spikes_n
        L = r_out + 2.5
        p.poly([(math.cos(a) * r_out * 0.95 + math.cos(a + 1.57) * 1.2, math.sin(a) * r_out * 0.95 + math.sin(a + 1.57) * 1.2),
                (math.cos(a) * L, math.sin(a) * L),
                (math.cos(a) * r_out * 0.95 - math.cos(a + 1.57) * 1.2, math.sin(a) * r_out * 0.95 - math.sin(a + 1.57) * 1.2)],
               mt.p(d=d) if isinstance(mt, Mt) else mt, 2)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        p.stroke([(math.cos(a) * 2, math.sin(a) * 2), (math.cos(a) * r_in, math.sin(a) * r_in)], 1.0,
                 mt.p(d=d * 0.6) if isinstance(mt, Mt) else mt, 1)
    return p

def disc(g, u, rv, rw, mt, w=0.0, name='disc', d=1.0, inner=None):
    """Oval guard plate lying across the axis."""
    p = g.plate(-rw - 2, rw + 2, -rv - 2, rv + 2, u=u, w=w, U=(0, 0, 1), V=(0, 1, 0))
    p.ell(0, 0, rw, rv, mt.p(d=d) if isinstance(mt, Mt) else mt, 1)
    if inner:
        p.ell(0, 0, rw * 0.62, rv * 0.62, inner.p(d=d + 0.5) if isinstance(inner, Mt) else inner, 2)
    return p

def side_plate(g, umin, umax, wmin, wmax, u=0, v=0):
    """Plate in the u-w plane (seen from the side), centred on the axis."""
    return g.plate(umin, umax, wmin, wmax, u=u, v=v, U=(1, 0, 0), V=(0, 0, 1))

def front_plate(g, umin, umax, vmin, vmax, u=0, w=0):
    return g.plate(umin, umax, vmin, vmax, u=u, w=w)

# ------------------------------------------------------------------------------------------- drawing helpers (plates)
def P(mt, **kw):
    return mt.p(**kw) if isinstance(mt, Mt) else dict(mt, **kw)

def star(p, u, v, r1, r2, n, mt, z=4, rot=0.0):
    pts = []
    for k in range(2 * n):
        a = rot + math.pi * k / n
        r = r1 if k % 2 == 0 else r2
        pts.append((u + math.cos(a) * r, v + math.sin(a) * r))
    p.poly(pts, mt, z)

def sigil(p, u, v, r, ring_mt, glow_mt, z=4, n=6):
    """Magic circle: outer ring, inner star polygon, glowing node dots."""
    p.ring(u, v, r, r - 1.1, ring_mt, z)
    pts = [(u + math.cos(2 * math.pi * k / n) * (r - 1.6), v + math.sin(2 * math.pi * k / n) * (r - 1.6)) for k in range(n)]
    step = 2 if n >= 5 else 1
    for k in range(n):
        a, b = pts[k], pts[(k + step) % n]
        p.stroke([a, b], 0.8, glow_mt, z + 1)
    for a in pts:
        p.dot(a[0], a[1], glow_mt, z + 2)

def serrate(line, depth, every=3.0, side=1):
    """Saw-tooth version of a polyline offset outwards (side +1 = +v)."""
    out = []
    for i in range(len(line) - 1):
        (u0, v0), (u1, v1) = line[i], line[i + 1]
        L = math.hypot(u1 - u0, v1 - v0)
        n = max(1, int(L / every))
        for k in range(n):
            t0, t1 = k / n, (k + 0.5) / n
            out.append((u0 + (u1 - u0) * t0, v0 + (v1 - v0) * t0))
            du, dv = (u1 - u0) / L, (v1 - v0) / L
            nu, nv = -dv * side, du * side
            out.append((u0 + (u1 - u0) * t1 + nu * depth, v0 + (v1 - v0) * t1 + nv * depth))
    out.append(line[-1])
    return out

def feather_wing(p, u, v, direction, n, length, width, mt, z=3, spread=0.5, droop=0.0):
    """Fan of feathers from (u, v); direction = angle (radians, 0 = +u, pi/2 = +v)."""
    for k in range(n):
        a = direction + (k - (n - 1) / 2) * spread / max(1, n - 1) * 2
        L = length * (1.0 - 0.12 * abs(k - (n - 1) / 2))
        du, dv = math.cos(a), math.sin(a)
        nu, nv = -dv, du
        tip = (u + du * L - droop * k, v + dv * L)
        p.poly([(u, v), (u + du * L * 0.45 + nu * width, v + dv * L * 0.45 + nv * width), tip,
                (u + du * L * 0.4 - nu * width * 0.6, v + dv * L * 0.4 - nv * width * 0.6)], mt, z + k % 2)

def bat_wing(p, u, v, direction, length, mt, z=3, fingers=4):
    """Membrane wing with finger bones and scalloped trailing edge."""
    pts = [(u, v)]
    for k in range(fingers + 1):
        a = direction - 0.6 + 1.2 * k / fingers
        L = length * (0.75 + 0.25 * math.sin(math.pi * k / fingers))
        pts.append((u + math.cos(a) * L, v + math.sin(a) * L))
        if k < fingers:
            a2 = direction - 0.6 + 1.2 * (k + 0.5) / fingers
            pts.append((u + math.cos(a2) * L * 0.62, v + math.sin(a2) * L * 0.62))
    p.poly(pts, mt, z)

def leaf(p, u, v, ang, L, W, mt, z=3):
    du, dv = math.cos(ang), math.sin(ang)
    nu, nv = -dv, du
    p.poly([(u, v), (u + du * L * 0.4 + nu * W, v + dv * L * 0.4 + nv * W), (u + du * L, v + dv * L),
            (u + du * L * 0.4 - nu * W, v + dv * L * 0.4 - nv * W)], mt, z)

# ------------------------------------------------------------------------------------------- 3D helpers
def coil(g, u0, u1, r, turns, mt, thick=2, seg=None, phase=0.0, name='coil'):
    """Helix of short boxes winding up the axis (dragon coils, vines, ribbons)."""
    m = mt.b() if isinstance(mt, Mt) else mt
    circ = 2 * math.pi * r
    total = math.hypot(circ * turns, u1 - u0)
    n = max(4, int(total / (seg or 2.5)))
    pitch = math.degrees(math.atan2(u1 - u0, circ * turns))
    for i in range(n):
        t = (i + 0.5) / n
        a = phase + 360.0 * turns * t
        grp = g.group(u0 + (u1 - u0) * t, 0, 0, rot=(a, 0, 0), name=f'{name}r{i}')
        grp.box(0, r, 0, thick, thick, max(1, round(total / n + 0.6)), m, rot=(0, pitch, 0), name=f'{name}{i}')

def ring3d(g, u, r, n, size, mt, phase=0.0, name='ring', w_tilt=0.0):
    """n blocks around the axis at height u (a crown, a gear rim, a collar of studs)."""
    m = mt.b() if isinstance(mt, Mt) else mt
    for k in range(n):
        grp = g.group(u, 0, 0, rot=(phase + 360.0 * k / n, 0, 0), name=f'{name}r{k}')
        grp.box(0, r, 0, size[0], size[1], size[2], m, name=f'{name}{k}')

def orbit(g, u, r, n, fn, phase=0.0, tilt=0.0, name='orbit'):
    """Call fn(group, k) for n frames placed on a circle of radius r around the axis at height u."""
    base = g.group(u, 0, 0, rot=(0, tilt, 0), name=name) if tilt else g
    for k in range(n):
        grp = base.group(0 if tilt else u, 0, 0, rot=(phase + 360.0 * k / n, 0, 0), name=f'{name}{k}')
        fn(grp.group(0, r, 0, name=f'{name}{k}p'), k)

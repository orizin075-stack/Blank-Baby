"""Build sculpted characters: rig bones -> rigs.json (no cubes, "mesh"), meshes/<key>.bin, textures and previews.

Usage: python3 build3d.py <out_dir> [names...]
  out_dir/rigs.json, out_dir/meshes/<key>.bin, out_dir/textures/<tex>.png (+ _glow), out_dir/preview/<key>.png"""
import sys, os, json, math
from paint import M
import numpy as np
from PIL import Image, ImageDraw
import sculpt as SC
import spaint as SP

def recipes():
    import chars3d
    out = dict(chars3d.RECIPES)
    try:
        import creatures3d
        out.update(creatures3d.RECIPES)
    except ImportError:
        pass
    return out

def drop_props(rig):
    """Weapons are rendered from the held relic items: drop prop bones (and their children)."""
    gone = set()
    for b in rig.bones:
        if b.name.startswith('prop_') or (b.parent is not None and b.parent.name in gone):
            gone.add(b.name)
    rig.bones = [b for b in rig.bones if b.name not in gone]
    rig.by_name = {b.name: b for b in rig.bones}
    sc = getattr(rig, 'sculpt', None)
    if sc:
        sc.surfs = [s for s in sc.surfs if s.bone.name not in gone]
    return len(gone)

def ring_from_plane(b, o, s, mat):
    """A painted ring on a flat box (halo, magic circle, rotor) becomes a real torus with spikes, spokes or a
    star polygon, in the plane of the box."""
    import trinkets as TK
    i0 = int(np.argmin(s))
    others = [s[i] for i in range(3) if i != i0]
    c = o + s / 2
    width = float(mat.get('width', 0.16))
    R = min(others) / 2 * (1 - width * 0.5)
    thick = max(0.2, R * width * 0.45)
    axis = 'xyz'[i0]
    m = dict(mat)
    if mat.get('rainbow'):
        m = M('rainbow', mat['color'])
    SC.torus(b, tuple(c), R, thick, m, axis=axis, k=8, n=max(24, int(R * 6)), name='ring')
    def on_plane(a, r):
        u, v = [i for i in range(3) if i != i0]
        p = c.copy()
        p[u] += r * math.cos(a)
        p[v] += r * math.sin(a)
        return p
    sp = int(mat.get('spikes', 0) or 0)
    for k in range(sp):
        a = 2 * math.pi * k / sp
        p0, p1 = on_plane(a, R + thick * 0.5), on_plane(a, R + thick + 0.9 + 0.4 * (k % 2))
        SC.sweep(b, [p0, p1], lambda t: thick * 0.9 * (1 - 0.9 * t), None, m, k=5, caps=('round', 'point'), name='ring_spike', info={'hem': False})
    spokes = int(mat.get('spokes', 0) or 0)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        SC.sweep(b, [on_plane(a, R * 0.12), on_plane(a, R - thick)], thick * 0.6, None, m, k=6, caps=('round', 'round'), name='ring_spoke',
                 info={'hem': False})
    poly = int(mat.get('poly', 0) or 0)
    for k in range(poly):
        a0 = 2 * math.pi * k / poly - math.pi / 2
        a1 = 2 * math.pi * ((k + 2) % poly) / poly - math.pi / 2
        SC.sweep(b, [on_plane(a0, R * 0.96), on_plane(a1, R * 0.96)], thick * 0.5, None, m, k=5, caps=('round', 'round'), name='ring_star',
                 info={'hem': False})

def cubes_to_surfaces(rig):
    """Explicit Bone.box() parts of a recipe become rounded boxes with the same box painters (painted rings on flat
    boxes become real rings)."""
    n = 0
    for b in rig.bones:
        for c in b.cubes:
            o = np.array(b.pivot, float) + np.array(c.origin, float)
            s = np.array(c.size, float)
            if c.mat.get('type') == 'ring' and (s < 0.05).sum() == 1:
                ring_from_plane(b, o, s, c.mat)
                n += 1
                continue
            pos = [v for v in s if v > 0.05]
            r = min(0.8, 0.28 * min(pos)) if pos else 0.0
            if min(pos or [0]) <= 1.0:
                r = 0.0
            SC.rbox(b, tuple(o), tuple(s), c.mat, radius=r, name=c.name or 'box', faces=c.faces, grow=c.grow)
            n += 1
        b.cubes = []
    return n

def build_one(name, fn, outdir, preview=True):
    r = fn()
    if getattr(r, 'sculpt', None) is None:
        SC.Sculpt(r)
    dropped = drop_props(r)
    cubes_to_surfaces(r)
    SC.bake(r, SP.paint_surf)
    tex, glow, size = SC.atlas(r)
    os.makedirs(os.path.join(outdir, 'textures'), exist_ok=True)
    os.makedirs(os.path.join(outdir, 'meshes'), exist_ok=True)
    tex.save(os.path.join(outdir, 'textures', r.texture + '.png'))
    glow.save(os.path.join(outdir, 'textures', r.texture + '_glow.png'))
    quads = SC.export_mesh(r, os.path.join(outdir, 'meshes', r.key + '.bin'), size)
    j = r.to_json()
    j['size'] = list(size)
    j['mesh'] = r.key
    top = SC.model_top(r)
    j['height'] = round(24 - top, 3) if r.height is None else r.height
    if preview:
        sheet(r, tex, glow, os.path.join(outdir, 'preview', name + '.png'), name)
    return j, quads, dropped, size

def sheet(r, tex, glow, path, title):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    views = [SC.render(r, tex, glow, yaw=y, pitch=p, size=(360, 480)) for y, p in ((28, 8), (-35, 6), (180 + 25, 8))]
    W = sum(v.width for v in views)
    out = Image.new('RGB', (W, 500), (40, 42, 52))
    x = 0
    for v in views:
        out.paste(v, (x, 0))
        x += v.width
    ImageDraw.Draw(out).text((8, 484), title, fill=(220, 220, 230))
    out.save(path)

def main(outdir, names=None):
    allr = recipes()
    names = names or list(allr)
    rp = os.path.join(outdir, 'rigs.json')
    rigs = json.load(open(rp)) if os.path.exists(rp) else {}
    for n in names:
        j, q, d, size = build_one(n, allr[n], outdir)
        rigs[n] = j
        print(f'{n}: {q} quads, atlas {size}, bones {len(j["bones"])}, height {j["height"]}, dropped {d}', flush=True)
    json.dump(rigs, open(rp, 'w'), separators=(',', ':'))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:] or None)

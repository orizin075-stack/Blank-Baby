"""Build sculpted characters: rig bones -> rigs.json (no cubes, "mesh"), meshes/<key>.bin, textures and previews.

Usage: python3 build3d.py <out_dir> [names...]
  out_dir/rigs.json, out_dir/meshes/<key>.bin, out_dir/textures/<tex>.png (+ _glow), out_dir/preview/<key>.png"""
import sys, os, json, math
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

def cubes_to_surfaces(rig):
    """Explicit Bone.box() parts of a recipe become rounded boxes with the same box painters."""
    n = 0
    for b in rig.bones:
        for c in b.cubes:
            o = np.array(b.pivot, float) + np.array(c.origin, float)
            s = np.array(c.size, float)
            pos = [v for v in s if v > 0.05]
            r = min(0.8, 0.28 * min(pos)) if pos else 0.0
            if min(pos or [0]) <= 1.0:
                r = min(r, 0.22)
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

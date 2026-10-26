"""Build design-sheet characters: python3 -I design_build.py <out_dir> [names...] [--check]

For each: geometry (design_chars), camera fit per sheet view, projected texture, then textures/<key>.png, its glow,
meshes/<key>.bin and the rig entry in <out_dir>/rigs.json. --check also writes check/<key>_fit.*.png (silhouettes)
and check/<key>.png (the sheet views beside the textured model through the same cameras, plus other angles)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import sculpt as SC
import designfig as DF
import design_chars as DC


def build(name, outdir, check=False, cams=None):
    sheet_name, fn = DC.RECIPES[name]
    fig, views = fn()
    sheet = DF.Sheet(sheet_name, views).clean(fig.colours)
    cams = DF.fit_views(fig, sheet, cams)
    tex, glow, size = DF.bake(fig, sheet, cams)
    r = fig.r
    for d in ('textures', 'meshes', 'check'):
        os.makedirs(os.path.join(outdir, d), exist_ok=True)
    tex.save(os.path.join(outdir, 'textures', r.texture + '.png'))
    glow.save(os.path.join(outdir, 'textures', r.texture + '_glow.png'))
    quads = SC.export_mesh(r, os.path.join(outdir, 'meshes', r.key + '.bin'), size)
    j = r.to_json()
    j['size'] = list(size)
    j['mesh'] = r.key
    top = SC.model_top(r)
    j['height'] = round(24 - top, 3) if r.height is None else r.height
    if check:
        DF.overlay_all(fig, sheet, cams, os.path.join(outdir, 'check', name + '_fit'))
        DF.compare(fig, sheet, cams, tex, glow, os.path.join(outdir, 'check', name + '.png'))
    print(f'{name}: {quads} quads, atlas {size}, bones {len(j["bones"])}, height {j["height"]}', flush=True)
    return j, {k: (c.yaw, c.pitch, c.scale, c.u0, c.v0) for k, c in cams.items()}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    check = '--check' in sys.argv
    outdir, names = args[0], args[1:] or list(DC.RECIPES)
    rp = os.path.join(outdir, 'rigs.json')
    rigs = json.load(open(rp)) if os.path.exists(rp) else {}
    for n in names:
        j, cams = build(n, outdir, check)
        rigs[n] = j
    os.makedirs(outdir, exist_ok=True)
    json.dump(rigs, open(rp, 'w'), separators=(',', ':'))


if __name__ == '__main__':
    main()

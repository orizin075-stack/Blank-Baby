"""Build the design-sheet characters (sheet_chars.py): python3 sheet_build.py <out_dir> [names...] [--preview]

Each recipe returns a Fig; its surfaces are painted with vox.py (pixel art drawn from the sheet as a reference) or,
for the face, eyelids and hair shell, with bbpaint. Writes textures/<key>.png and _glow.png, meshes/<key>.bin and
the rig in rigs.json; --preview also writes preview/<key>.png beside the sheet's front view."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import bb
bb.enable()
import sculpt as SC
import bbpaint as BP
import gaiapaint
gaiapaint.enable()
import iapaint
iapaint.enable()
import vox
import sface
sface.enable()
import sheet_chars as SCH
import vox_chars as VCH
import vxl
RECIPES = dict(SCH.RECIPES)
RECIPES.update(VCH.RECIPES)

SHEETS = os.path.normpath(os.path.join(HERE, '..', '..', 'designs', 'sheets'))


def painter(s, ctx):
    t = (s.mat or {}).get('type')
    if t == 'vox':
        return vox.paint(s, ctx)
    if t == 'voxbaked':
        return vxl.paint_baked(s, ctx)
    if t in ('sface', 'slids', 'sshell'):
        return BP.PAINTERS[t](s.mat, BP.F(s, ctx), s, ctx)
    return BP.paint_surf(s, ctx)


def build(name, outdir, preview=False):
    sheet, fn = RECIPES[name]
    fig = fn()
    r = fig.r
    SC.bake(r, painter, ao=False)
    tex, glow, size = SC.atlas(r)
    for d in ('textures', 'meshes', 'preview'):
        os.makedirs(os.path.join(outdir, d), exist_ok=True)
    tex.save(os.path.join(outdir, 'textures', r.texture + '.png'))
    glow.save(os.path.join(outdir, 'textures', r.texture + '_glow.png'))
    quads = SC.export_mesh(r, os.path.join(outdir, 'meshes', r.key + '.bin'), size)
    j = r.to_json()
    j['size'] = list(size)
    j['mesh'] = r.key
    j['height'] = round(24 - SC.model_top(r), 3) if r.height is None else r.height
    if preview:
        sheet_preview(fig, sheet, tex, glow, os.path.join(outdir, 'preview', name + '.png'))
    print(f'{name}: {quads} quads, atlas {size}, bones {len(j["bones"])}, height {j["height"]}', flush=True)
    return j


def sheet_preview(fig, sheet, tex, glow, path, Hh=760):
    tiles = []
    f = [x for x in sorted(os.listdir(SHEETS)) if x.startswith(sheet)]
    if f:
        im = Image.open(os.path.join(SHEETS, f[0])).convert('RGB')
        im.thumbnail((int(Hh * 1.6), Hh))
        tiles.append(im)
    for yaw in (-30, 30, 150, 210):
        tiles.append(SC.render(fig.r, tex, glow, yaw=yaw, pitch=8, size=(470, Hh), bg=(128, 156, 200)))
    W = sum(t.size[0] for t in tiles) + 8 * (len(tiles) - 1)
    out = Image.new('RGB', (W, Hh), (24, 26, 32))
    x = 0
    for t in tiles:
        out.paste(t, (x, (Hh - t.size[1]) // 2))
        x += t.size[0] + 8
    out.save(path)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    outdir, names = args[0], args[1:] or list(RECIPES)
    rp = os.path.join(outdir, 'rigs.json')
    rigs = json.load(open(rp)) if os.path.exists(rp) else {}
    for n in names:
        rigs[n] = build(n, outdir, '--preview' in sys.argv)
    json.dump(rigs, open(rp, 'w'), separators=(',', ':'))


if __name__ == '__main__':
    main()

"""Build the Blockbench-style characters: rigs.json (bones + "mesh"), meshes/<key>.bin, textures, previews.

Usage: python3 build_bb.py <out_dir> [names...]"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw
import bb
bb.enable()
import figure_bb
sys.modules['figure'] = figure_bb          # recipes import Humanoid & helpers from 'figure'
import sculpt as SC
import bbpaint as BP
import gaiapaint
gaiapaint.enable()           # 0.17.27: Grimoire of Gaia / Ice and Fire painters
import iapaint
iapaint.enable()             # 0.17.27: creature eyes, mouths, teeth, wing skin (creatures_ia)
import build3d as B3


def recipes():
    import chars3d, creatures3d, creatures_sc, creatures_ia
    out = dict(chars3d.RECIPES)
    out.update(creatures3d.RECIPES)
    out.update(creatures_sc.RECIPES)
    out.update(creatures_ia.RECIPES)         # 0.17.27: the non-human characters, rebuilt as cube models
    # (059g) the dragons and the sea kings remade after the user's design sheets and photos (dragons_sheet.py:
    # Demiurgos, Teia, Kurma; seakings.py: Enkou, Bahamut) - the user: "見比べて同じものに見えるならそれでいいと思う"
    import dragons_sheet, seakings
    out.update(dragons_sheet.RECIPES)
    out.update(seakings.RECIPES)
    return out


def save_palette(im, path):
    """An RGBA image as a palette PNG: its own colours when there are 256 or fewer, else the nearest 256."""
    from PIL import Image
    im = im.convert('RGBA')
    cols = im.getcolors(256)
    if cols:
        index = {c: i for i, (_, c) in enumerate(cols)}
        p = Image.new('P', im.size)
        p.putdata([index[px] for px in im.getdata()])
        p.putpalette([v for _, c in cols for v in c[:3]])
        p.save(path, 'PNG', optimize=True, transparency=bytes(c[3] for _, c in cols))
    else:
        q = im.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
        q.save(path, 'PNG', optimize=True)


def build_one(name, fn, outdir, preview=True):
    r = fn()
    if getattr(r, 'sculpt', None) is None:
        SC.Sculpt(r)
    dropped = B3.drop_props(r)
    B3.cubes_to_surfaces(r)
    import headswap
    headswap.prepare(r)                      # 059g: the head (face and hair) as the user's references draw it
    SC.bake(r, BP.paint_surf)
    tex, glow, size = SC.atlas(r)
    os.makedirs(os.path.join(outdir, 'textures'), exist_ok=True)
    os.makedirs(os.path.join(outdir, 'meshes'), exist_ok=True)
    if getattr(r, 'palette', False):
        # (059g) the large remade models' textures as 256-colour palette PNGs (the game reads them as any PNG):
        # a third of the bytes, so the import zip stays under its 30,000,000
        save_palette(tex, os.path.join(outdir, 'textures', r.texture + '.png'))
        save_palette(glow, os.path.join(outdir, 'textures', r.texture + '_glow.png'))
    else:
        tex.save(os.path.join(outdir, 'textures', r.texture + '.png'))
        glow.save(os.path.join(outdir, 'textures', r.texture + '_glow.png'))
    quads = SC.export_mesh(r, os.path.join(outdir, 'meshes', r.key + '.bin'), size)
    j = r.to_json()
    j['size'] = list(size)
    j['mesh'] = r.key
    top = SC.model_top(r)
    j['height'] = round(24 - top, 3) if r.height is None else r.height
    if preview:
        B3.sheet(r, tex, glow, os.path.join(outdir, 'preview', name + '.png'), name)
    return j, quads, dropped, size


def main(outdir, names=None):
    allr = recipes()
    names = names or list(allr)
    rp = os.path.join(outdir, 'rigs.json')
    rigs = json.load(open(rp)) if os.path.exists(rp) else {}
    for n in names:
        j, q, d, size = build_one(n, allr[n], outdir)
        rigs[n] = j
        print(f'{n}: {q} quads, atlas {size}, bones {len(j["bones"])}, height {j["height"]}', flush=True)
    json.dump(rigs, open(rp, 'w'), separators=(',', ':'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2:] or None)

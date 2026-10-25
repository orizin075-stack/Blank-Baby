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
    return out


def build_one(name, fn, outdir, preview=True):
    r = fn()
    if getattr(r, 'sculpt', None) is None:
        SC.Sculpt(r)
    dropped = B3.drop_props(r)
    B3.cubes_to_surfaces(r)
    SC.bake(r, BP.paint_surf)
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

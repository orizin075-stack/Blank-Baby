"""Build textures, glow maps, previews and rigs.json for the selected recipes."""
import sys, os, json
from paint import paint_rig
from sheet import sheet

def all_recipes():
    from chars import RECIPES as A
    try:
        from creatures import RECIPES as B
    except ImportError:
        B = {}
    out = dict(A)
    out.update(B)
    return out

def build(outdir, names=None, previews=True):
    allr = all_recipes()
    names = names or list(allr)
    os.makedirs(os.path.join(outdir, 'textures'), exist_ok=True)
    os.makedirs(os.path.join(outdir, 'preview'), exist_ok=True)
    rp = os.path.join(outdir, 'rigs.json')
    rigs = json.load(open(rp)) if os.path.exists(rp) else {}
    for n in names:
        r = allr[n]()
        for size in ((64, 64), (128, 64), (128, 128), (256, 128), (256, 256)):
            r.layout = size
            try:
                r.pack()
                break
            except ValueError:
                continue
        tex, glow = paint_rig(r)
        tex.save(os.path.join(outdir, 'textures', r.texture + '.png'))
        glow.save(os.path.join(outdir, 'textures', r.texture + '_glow.png'))
        rigs[r.key] = r.to_json()
        if previews:
            sheet(r, tex, glow, os.path.join(outdir, 'preview', n + '.png'), n)
        print(n, r.layout, len(r.bones), 'bones', len(r.cubes()), 'cubes')
    json.dump(rigs, open(rp, 'w'), separators=(',', ':'))

if __name__ == '__main__':
    build(sys.argv[1], sys.argv[2:] or None)

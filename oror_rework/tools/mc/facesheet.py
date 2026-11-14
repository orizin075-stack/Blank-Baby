"""facesheet.py <out.png> [names...] [--old]: close-ups of the characters' heads (front and three-quarter), built as
build_bb.py builds them, on one sheet: to check the faces (059g, mobface.py; --old draws them with gaiaface)."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bb
bb.enable()
import figure_bb
sys.modules['figure'] = figure_bb
import sculpt as SC
import bbpaint as BP
import gaiapaint
gaiapaint.enable()
import iapaint
iapaint.enable()
import build3d as B3
import build_bb


def head_shot(r, tex, glow, yaw):
    """The head alone (the head bone and what hangs from it: hair, horns, ears, a crown), filling the frame."""
    head = r.by_name.get('head')
    keep = set()
    if head is not None:
        for b in r.bones:
            x = b
            while x is not None:
                if x is head:
                    keep.add(b.name)
                    break
                x = x.parent
    surfs = r.sculpt.surfs
    if keep:
        r.sculpt.surfs = [s for s in surfs if s.bone.name in keep]
    try:
        img = SC.render(r, tex, glow, yaw=yaw, pitch=4, size=(260, 260), bg=(120, 150, 190))
    finally:
        r.sculpt.surfs = surfs
    return img


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    out, names = args[0], args[1:]
    if '--old' in sys.argv:
        import gaiaface
        BP.FACES = gaiaface
    allr = build_bb.recipes()
    import chars3d
    names = names or sorted(chars3d.RECIPES)
    tiles = []
    for n in names:
        r = allr[n]()
        if getattr(r, 'sculpt', None) is None:
            SC.Sculpt(r)
        B3.drop_props(r)
        B3.cubes_to_surfaces(r)
        import headswap
        headswap.prepare(r)
        SC.bake(r, BP.paint_surf)
        tex, glow, size = SC.atlas(r)
        t = Image.new('RGB', (530, 284), (30, 32, 40))
        t.paste(head_shot(r, tex, glow, 0), (0, 0))
        t.paste(head_shot(r, tex, glow, 32), (270, 0))
        ImageDraw.Draw(t).text((6, 266), n, fill=(230, 230, 240))
        tiles.append(t)
        print(n, flush=True)
    cols = 3
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * 536, rows * 290), (20, 20, 26))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 536, (i // cols) * 290))
    sheet.save(out)


if __name__ == '__main__':
    main()

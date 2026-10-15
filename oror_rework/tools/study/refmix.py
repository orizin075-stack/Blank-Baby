"""Mixed-format reference sheet: geo (Bedrock), ld (Mojang LayerDefinition java), ac (Citadel java), tbl (Tabula)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from rig import render
import geoview, ldview, acview, tblview

def load(kind, model, tex):
    if kind == 'geo':
        return geoview.load(model, tex)
    if kind == 'ld':
        return ldview.load(model, tex)
    if kind == 'ac':
        return acview.load(model, tex)
    return tblview.load(model)

def sheet(items, out, cols=4, size=(330, 330), yaw=35):
    cells = []
    for label, kind, model, tex in items:
        try:
            r, t = load(kind, model, tex)
            n = sum(len(b.cubes) for b in r.bones)
            cells.append((f'{label}  ({n} cubes, {r.layout[0]}x{r.layout[1]})', render(r, t, yaw, 10, size, None, cull=False)))
        except Exception as e:
            print('skip', label, repr(e))
    rows = (len(cells) + cols - 1) // cols
    W, H = size
    img = Image.new('RGB', (cols * (W + 6) + 6, rows * (H + 22) + 6), (34, 36, 44))
    d = ImageDraw.Draw(img)
    for k, (label, im) in enumerate(cells):
        x, y = 6 + (k % cols) * (W + 6), 6 + (k // cols) * (H + 22)
        img.paste(im, (x, y))
        d.text((x + 4, y + H + 4), label, fill=(230, 230, 230))
    img.save(out)

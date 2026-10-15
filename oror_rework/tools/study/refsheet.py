"""Contact sheet of reference models (Bedrock geo / Tabula / Citadel java) rendered in-game style."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageDraw
from geoview import load as load_geo
from rig import render

def sheet(items, out, cols=4, size=(330, 300), yaws=(35,)):
    cells = []
    for label, path, tex in items:
        try:
            r, t = load_geo(path, tex)
        except Exception as e:
            print('skip', label, e); continue
        for y in yaws:
            cells.append((label, render(r, t, y, 12, size, None, cull=False)))
    rows = (len(cells) + cols - 1) // cols
    W, H = size
    img = Image.new('RGB', (cols * (W + 6) + 6, rows * (H + 22) + 6), (34, 36, 44))
    d = ImageDraw.Draw(img)
    for k, (label, im) in enumerate(cells):
        x, y = 6 + (k % cols) * (W + 6), 6 + (k // cols) * (H + 22)
        img.paste(im, (x, y))
        d.text((x + 4, y + H + 4), label, fill=(230, 230, 230))
    img.save(out)

if __name__ == '__main__':
    base, out = sys.argv[1], sys.argv[2]
    names = sys.argv[3:]
    items = []
    for n in names:
        d, f = n.split('/')
        tn = f.replace('_male', '').replace('_female', '')
        items.append((f, f'{base}/bedrock/pokemon/models/{d}/{f}.geo.json', f'{base}/textures/pokemon/{d}/{tn}.png'))
    sheet(items, out)

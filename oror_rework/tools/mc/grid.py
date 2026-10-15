import sys
from PIL import Image, ImageDraw
from build import all_recipes
from paint import paint_rig
from rig import render
from anim import pose

def grid(names, out, cols=6, yaw=30, size=(230, 320)):
    allr = all_recipes()
    rows = (len(names) + cols - 1) // cols
    W, H = size
    img = Image.new('RGB', (cols * (W + 8) + 8, rows * (H + 24) + 8), (34, 36, 44))
    d = ImageDraw.Draw(img)
    for k, n in enumerate(names):
        r = allr[n]()
        for s in ((64, 64), (128, 64), (128, 128), (256, 128), (256, 256)):
            r.layout = s
            try:
                r.pack(); break
            except ValueError:
                pass
        tex, glow = paint_rig(r)
        im = render(r, tex, yaw, 8, size, glow, pose=pose(r, age=0))
        x, y = 8 + (k % cols) * (W + 8), 8 + (k // cols) * (H + 24)
        img.paste(im, (x, y))
        d.text((x + 4, y + H + 4), n, fill=(230, 230, 230))
    img.save(out)

if __name__ == '__main__':
    from chars import RECIPES
    names = sys.argv[2:] or list(RECIPES)
    grid(names, sys.argv[1])

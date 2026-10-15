"""Gallery of the relic weapons, rendered standalone at the in-game texel density."""
import sys
from PIL import Image, ImageDraw
from rig import Rig, render
from paint import paint_rig
import props as P

def build_weapon(name):
    r = Rig('w_' + name, layout=(128, 128))
    root = r.bone('root', None, (0, 0, 0))
    f = P.Forge(r, root, (0, 0, 0), rot=(0, 0, 0), name='prop', scale=1.0 / P.F)
    P.WEAPONS[name](f)
    for s in ((64, 64), (128, 64), (128, 128), (256, 128), (256, 256)):
        r.layout = s
        try:
            r.pack(); break
        except ValueError:
            pass
    return r

def gallery(names, out, cols=7, size=(200, 300), yaw=70):
    rows = (len(names) + cols - 1) // cols
    W, H = size
    img = Image.new('RGB', (cols * (W + 6) + 6, rows * (H + 20) + 6), (34, 36, 44))
    d = ImageDraw.Draw(img)
    for k, n in enumerate(names):
        r = build_weapon(n)
        tex, glow = paint_rig(r)
        im = render(r, tex, yaw, 10, size, glow)
        x, y = 6 + (k % cols) * (W + 6), 6 + (k // cols) * (H + 20)
        img.paste(im, (x, y))
        d.text((x + 4, y + H + 3), f'{n} ({len(r.cubes())})', fill=(230, 230, 230))
    img.save(out)

if __name__ == '__main__':
    names = sys.argv[2:] or list(P.WEAPONS)
    gallery(names, sys.argv[1])

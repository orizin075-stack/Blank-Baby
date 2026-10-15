import sys
from PIL import Image
from rig import render
def closeup(rig, tex, glow, out, top):
    ims = [render(rig, tex, y, 4, (360, 360), glow, frame=(0, -(top + 4), 20)) for y in (0, 30, 60)]
    W = Image.new('RGB', (1100, 370), (36, 38, 46))
    for k, im in enumerate(ims):
        W.paste(im, (5 + k * 365, 5))
    W.save(out)

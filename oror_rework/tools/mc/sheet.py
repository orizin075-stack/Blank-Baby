"""Preview sheet: turnaround + walk/attack frames, rendered with the in-game box-UV mapping."""
import sys, math
from PIL import Image, ImageDraw
from rig import render
from anim import pose as anim_pose

def sheet(rig, tex, glow, out, title=''):
    S = (300, 420)
    views = [('front', 20, 6, {}), ('3/4', 40, 8, {}), ('side', 90, 6, {}), ('back', 200, 8, {})]
    frames = [('walk 1', 30, 6, dict(age=10, swing=0.0, amount=0.9)), ('walk 2', 30, 6, dict(age=12, swing=2.36, amount=0.9)),
              ('attack', 30, 6, dict(age=14, motion=1, progress=0.5, action=1)), ('blink', 15, 4, dict(age=0))]
    img = Image.new('RGB', (S[0] * 4 + 50, (S[1] + 26) * 2 + 40), (36, 38, 46))
    d = ImageDraw.Draw(img)
    d.text((10, 6), title, fill=(255, 255, 255))
    for row, items in enumerate((views, frames)):
        for k, (name, yaw, pitch, kw) in enumerate(items):
            ps = anim_pose(rig, **kw) if kw else anim_pose(rig, age=0)
            im = render(rig, tex, yaw, pitch, S, glow, pose=ps, blink=(name == 'blink'))
            x, y = 10 + k * (S[0] + 10), 24 + row * (S[1] + 26)
            img.paste(im, (x, y))
            d.text((x + 4, y + S[1] + 4), name, fill=(220, 220, 220))
    img.save(out)

import sys, json, glob, os
from PIL import Image, ImageDraw, ImageFont
import forge3d as F, w3designs as D
FONT = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 13)
def weapons(out, aw):
    keys = list(D.WEAPONS)
    cols, tw, th = 7, 220, 330
    img = Image.new('RGB', (cols * tw, ((len(keys) + cols - 1) // cols) * th), (30, 32, 40))
    d = ImageDraw.Draw(img)
    for k, key in enumerate(keys):
        q, a, S = D.build(key, aw).build()
        im = F.render_quads(F.world_quads(q, a), (tw, th - 26), F.view_matrix(32, 14), bg=(30, 32, 40))
        x, y = (k % cols) * tw, (k // cols) * th
        img.paste(im, (x, y))
        info = D.WEAPONS[key]
        d.text((x + 6, y + th - 22), info['legend'] if aw else info['title'], fill=(235, 235, 235), font=FONT)
    img.save(out)
def icons(out, root):
    rel = json.load(open(root + '/relics.json', encoding='utf-8'))
    ids = [r['id'] for r in rel] + sorted({r['character'] for r in rel})
    cols, cell = 20, 72
    ids = [r['id'] for r in rel]
    img = Image.new('RGBA', (cols * cell, ((len(ids) + cols - 1) // cols) * cell), (139, 139, 139, 255))
    for k, rid in enumerate(ids):
        ic = Image.open(f'{root}/textures/item/{rid}.png').convert('RGBA').resize((64, 64), Image.NEAREST)
        img.alpha_composite(ic, ((k % cols) * cell + 4, (k // cols) * cell + 4))
    img.save(out)
if sys.argv[1] == 'w': weapons(sys.argv[2], False)
elif sys.argv[1] == 'l': weapons(sys.argv[2], True)
else: icons(sys.argv[2], sys.argv[3])

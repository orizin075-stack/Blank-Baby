"""Turntable sheet of 3D relic weapons + held previews."""
import sys, time
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import forge3d as F, held as Hd
import w3designs as D

FONT = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'

def sheet(keys, out, aw=False, held=True):
    font = ImageFont.truetype(FONT, 14)
    tiles = []
    for k in keys:
        t = time.time()
        w = D.build(k, aw)
        q, atlas, S = w.build()
        views = [F.render_quads(F.world_quads(q, atlas), (200, 420), F.view_matrix(y, p)) for y, p in ((0, 0), (35, 15), (90, 5), (215, -12))]
        if held:
            disp = Hd.derive(scale_tp=D.WEAPONS[k]['scale'], scale_fp=D.WEAPONS[k]['fp_scale'], hold=D.WEAPONS[k]['hold'])
            views += Hd.preview_third_person(q, atlas, disp, size=(200, 420), yaws=(-50, 130))
        row = Image.new('RGB', (200 * len(views), 446), (30, 32, 40))
        for i, im in enumerate(views):
            row.paste(im, (200 * i, 0))
        d = ImageDraw.Draw(row)
        info = D.WEAPONS[k]
        d.text((6, 424), f"{k}  {info['legend'] if aw else info['title']}  [{info['kind']}]  quads {len(q)}  tex {S}  {time.time()-t:.1f}s", fill=(235, 235, 235), font=font)
        tiles.append(row)
    W = max(t.width for t in tiles)
    img = Image.new('RGB', (W, sum(t.height for t in tiles)), (30, 32, 40))
    y = 0
    for t in tiles:
        img.paste(t, (0, y)); y += t.height
    img.save(out)

if __name__ == '__main__':
    aw = '--aw' in sys.argv
    args = [a for a in sys.argv[1:] if a != '--aw']
    sheet(args[1:] or list(D.WEAPONS), args[0], aw)

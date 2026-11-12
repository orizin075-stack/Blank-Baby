"""book_gui.py <out png>: the dominion grimoire as it lies open on the screen (GrimoireScreen), one 512x256 sheet:
the open spread at (0,0) 256x180 (purple leather round two cream pages, the spine's shadow, gold corners, a faint sigil
in each page), the front cover at (256,0) 128x180 (gold frame, sigil, cyan gem, clasp), and the inside of the cover at
(384,0) 128x180 (marbled endpaper)."""
import math
import random
import sys

from PIL import Image, ImageDraw

LEATHER = (74, 42, 94)
LEATHER_HI = (106, 67, 132)
LEATHER_LO = (46, 26, 59)
GOLD = (227, 179, 65)
GOLD_LO = (154, 116, 32)
PAPER = (239, 228, 200)
PAPER_LO = (214, 199, 160)
PAPER_EDGE = (196, 180, 140)


def paper_page(d, x0, y0, x1, y1, spine_left):
    # cream, darker toward the spine and at the outer edge
    for x in range(x0, x1 + 1):
        t = (x - x0) / max(1, x1 - x0)
        to_spine = (1 - t) if spine_left else t
        shade = 0.0
        if to_spine < 0.12:
            shade = (0.12 - to_spine) / 0.12 * 0.22
        if to_spine > 0.94:
            shade = max(shade, (to_spine - 0.94) / 0.06 * 0.12)
        c = tuple(int(PAPER[i] * (1 - shade) + PAPER_LO[i] * shade) for i in range(3))
        d.line([(x, y0), (x, y1)], fill=c)
    # the page block's edges (the stacked leaves) at the foot and the outer side
    for k in range(3):
        d.line([(x0 + 2, y1 + 1 + k), (x1 - 2, y1 + 1 + k)], fill=PAPER_EDGE if k % 2 == 0 else PAPER_LO)


def sigil(img, cx, cy, r, alpha):
    over = Image.new('RGBA', img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    col = (154, 116, 32, alpha)
    od.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)
    od.ellipse([cx - r * 0.62, cy - r * 0.62, cx + r * 0.62, cy + r * 0.62], outline=col, width=1)
    for k in range(8):
        a = k * math.pi / 4
        od.line([(cx + math.cos(a) * r * 0.62, cy + math.sin(a) * r * 0.62), (cx + math.cos(a) * r, cy + math.sin(a) * r)],
                fill=col, width=1)
    pts = [(cx + math.cos(a) * r * 0.5, cy + math.sin(a) * r * 0.5) for a in [k * 2 * math.pi / 5 - math.pi / 2 for k in (0, 2, 4, 1, 3)]]
    od.line(pts + [pts[0]], fill=col, width=1)
    img.alpha_composite(over)


def corners(d, x0, y0, x1, y1):
    for (x, y, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.polygon([(x, y), (x + 14 * sx, y), (x, y + 14 * sy)], fill=GOLD)
        d.line([(x + 3 * sx, y + 3 * sy), (x + 9 * sx, y + 3 * sy)], fill=GOLD_LO)
        d.line([(x + 3 * sx, y + 3 * sy), (x + 3 * sx, y + 9 * sy)], fill=GOLD_LO)


def main():
    out = sys.argv[1]
    img = Image.new('RGBA', (512, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # --- the open spread
    d.rounded_rectangle([0, 0, 255, 179], radius=6, fill=LEATHER)
    d.rounded_rectangle([0, 0, 255, 179], radius=6, outline=LEATHER_LO, width=2)
    d.line([(4, 2), (251, 2)], fill=LEATHER_HI)
    paper_page(d, 8, 7, 126, 168, spine_left=False)
    paper_page(d, 129, 7, 247, 168, spine_left=True)
    d.rectangle([126, 4, 129, 175], fill=LEATHER_LO)                   # the spine between the pages
    for y in range(8, 170, 6):
        d.point((127, y), fill=GOLD_LO)
    corners(d, 2, 2, 253, 177)
    sigil(img, 67, 92, 30, 34)
    sigil(img, 188, 92, 30, 34)
    # a headband ribbon (the bookmark) hanging from the spine
    d.polygon([(131, 0), (136, 0), (136, 22), (133, 18), (131, 22)], fill=(170, 30, 40))
    # --- the front cover
    cx0 = 256
    d.rounded_rectangle([cx0, 0, cx0 + 127, 179], radius=5, fill=LEATHER)
    d.rounded_rectangle([cx0, 0, cx0 + 127, 179], radius=5, outline=LEATHER_LO, width=2)
    d.rectangle([cx0, 0, cx0 + 8, 179], fill=LEATHER_LO)               # the spine side
    d.rectangle([cx0 + 14, 10, cx0 + 117, 169], outline=GOLD, width=2)
    d.rectangle([cx0 + 18, 14, cx0 + 113, 165], outline=GOLD_LO, width=1)
    corners(d, cx0 + 12, 8, cx0 + 119, 171)
    ccx, ccy = cx0 + 66, 90
    d.ellipse([ccx - 30, ccy - 30, ccx + 30, ccy + 30], outline=GOLD, width=3)
    for k in range(8):
        a = k * math.pi / 4
        d.line([(ccx + math.cos(a) * 30, ccy + math.sin(a) * 30), (ccx + math.cos(a) * 40, ccy + math.sin(a) * 40)], fill=GOLD, width=2)
    d.polygon([(ccx, ccy - 14), (ccx + 12, ccy), (ccx, ccy + 14), (ccx - 12, ccy)], fill=(63, 217, 232))
    d.polygon([(ccx, ccy - 14), (ccx + 12, ccy), (ccx, ccy)], fill=(160, 240, 248))
    d.polygon([(ccx, ccy + 14), (ccx - 12, ccy), (ccx, ccy)], fill=(31, 138, 150))
    d.rectangle([cx0 + 112, 80, cx0 + 127, 100], fill=GOLD)             # the clasp
    d.rectangle([cx0 + 112, 97, cx0 + 127, 100], fill=GOLD_LO)
    d.ellipse([cx0 + 118, 86, cx0 + 123, 91], fill=(92, 66, 16))
    # --- the inside of the cover: marbled endpaper
    ix0 = 384
    d.rounded_rectangle([ix0, 0, ix0 + 127, 179], radius=5, fill=LEATHER_LO)
    rnd = random.Random(59)
    for y in range(6, 174):
        for x in range(ix0 + 6, ix0 + 122):
            v = math.sin(x * 0.11 + math.sin(y * 0.07) * 2.2) + math.sin(y * 0.05 + x * 0.03)
            t = (v + 2) / 4
            c = (int(52 + 60 * t), int(30 + 30 * t), int(70 + 70 * t))
            img.putpixel((x, y), c + (255,))
    d.rectangle([ix0 + 6, 6, ix0 + 121, 173], outline=GOLD_LO, width=1)
    img.save(out)
    print(out, img.size)


if __name__ == '__main__':
    main()

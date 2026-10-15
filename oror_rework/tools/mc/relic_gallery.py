"""Icon and in-hand sprite galleries for the relic weapon designs."""
import sys
from PIL import Image, ImageDraw, ImageFont
import relic_art as R

def icons(out, names=None, scale=4, cols=9):
    names = names or list(R.DESIGNS)
    S = 32 * scale
    rows = (len(names) + cols - 1) // cols
    img = Image.new('RGBA', (cols * (S + 10) + 10, rows * (S + 34) + 10), (44, 46, 56, 255))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 13)
    except Exception:
        font = None
    for k, n in enumerate(names):
        rgba, glow = R.render_icon(n)
        im = R.to_image(rgba).resize((S, S), Image.NEAREST)
        x, y = 10 + (k % cols) * (S + 10), 10 + (k // cols) * (S + 34)
        d.rectangle([x - 2, y - 2, x + S + 2, y + S + 2], fill=(58, 60, 72, 255))
        img.paste(im, (x, y), im)
        d.text((x, y + S + 3), R.DESIGNS[n]['title'], fill=(240, 240, 240, 255), font=font)
        d.text((x, y + S + 18), n, fill=(170, 170, 180, 255))
    img.save(out)

def sprites(out, names=None, scale=2, cols=11):
    names = names or list(R.DESIGNS)
    tiles = []
    for n in names:
        (rgba, glow), fr = R.render_sprite(n)
        im = R.to_image(rgba)
        tiles.append((n, im.resize((im.width * scale, im.height * scale), Image.NEAREST)))
    cw = max(t[1].width for t in tiles) + 10
    ch = max(t[1].height for t in tiles) + 24
    rows = (len(tiles) + cols - 1) // cols
    img = Image.new('RGBA', (cols * cw + 10, rows * ch + 10), (44, 46, 56, 255))
    d = ImageDraw.Draw(img)
    for k, (n, im) in enumerate(tiles):
        x, y = 10 + (k % cols) * cw, 10 + (k // cols) * ch
        img.paste(im, (x, y + ch - 24 - im.height), im)
        d.text((x, y + ch - 20), n[:14], fill=(220, 220, 220, 255))
    img.save(out)

if __name__ == '__main__':
    icons(sys.argv[1])
    sprites(sys.argv[2])

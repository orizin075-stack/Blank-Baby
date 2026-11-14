"""capital_compass.py <overlay dir> [preview.png]: the Royal Capital Compass (059f), 16 x 16, in 32 drawings of its needle.

A gold case with a small crown on top, a deep royal-blue face with four silver marks, and a needle whose crimson point
turns to the capital: drawing f points (f - 16) x 11.25 degrees clockwise from straight up, as Minecraft's own compass
drawings do (drawing 16 points ahead), so the model's 'angle' overrides (made here too, after the compass's own) read it
the same way. Writes textures/item/capital_compass_NN.png and models/item/capital_compass[_NN].json under
assets/oror_supreme_bosses in the overlay.
"""
import json, math, os, sys
from PIL import Image

NS = 'oror_supreme_bosses'
OUT = sys.argv[1]
TEX = os.path.join(OUT, 'assets', NS, 'textures', 'item')
MOD = os.path.join(OUT, 'assets', NS, 'models', 'item')

GOLD_HI, GOLD, GOLD_LO, GOLD_DK = (255, 226, 120), (232, 178, 46), (178, 118, 22), (92, 58, 14)
FACE_HI, FACE, FACE_LO = (60, 86, 168), (34, 50, 112), (20, 28, 70)
SILVER, RED, RED_DK, TAIL = (214, 222, 240), (236, 52, 44), (150, 22, 22), (226, 230, 236)
CX = CY = 7.5


def base():
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    px = img.load()
    for y in range(16):
        for x in range(16):
            d = math.hypot(x + 0.5 - 8.0, y + 0.5 - 8.5)
            if d <= 6.6:
                # the face: lighter to the upper left, darker to the lower right
                shade = ((x - 8) + (y - 8.5)) / 12.0
                px[x, y] = FACE_HI if shade < -0.35 else FACE_LO if shade > 0.4 else FACE
            elif d <= 7.6:
                # the case: lit from the upper left
                ang = math.atan2(y + 0.5 - 8.5, x + 0.5 - 8.0)
                lit = math.cos(ang + math.pi * 0.75)
                px[x, y] = GOLD_HI if lit > 0.55 else GOLD if lit > -0.2 else GOLD_LO
            elif d <= 8.15:
                px[x, y] = GOLD_DK
    # the crown on top of the case (three points and a band)
    for x, y, c in ((5, 0, GOLD), (8, 0, GOLD_HI), (10, 0, GOLD), (5, 1, GOLD), (6, 1, GOLD_LO), (7, 1, GOLD), (8, 1, GOLD_HI),
                    (9, 1, GOLD), (10, 1, GOLD), (8, 0, (240, 60, 60))):
        px[x, y] = c
    # four silver marks inside the rim
    for x, y in ((8, 3), (13, 8), (8, 14), (2, 8)):
        px[x, y] = SILVER + (255,)
    for y in range(16):
        for x in range(16):
            v = px[x, y]
            if len(v) == 3:
                px[x, y] = v + (255,)
    return img


def needle(img, frame):
    px = img.load()
    a = math.radians((frame - 16) * 11.25)
    sx, sy = math.sin(a), -math.cos(a)
    cx, cy = 8.0, 8.5
    drawn = set()
    # the tail (silver), then the point (crimson, darker at its root), so the point lies over the tail at the pin
    for t in [i * 0.25 for i in range(0, 13)]:
        x, y = int(math.floor(cx - sx * t)), int(math.floor(cy - sy * t))
        if 0 <= x < 16 and 0 <= y < 16 and (x, y) not in drawn and t > 0.4:
            px[x, y] = TAIL + (255,)
    for t in [i * 0.25 for i in range(0, 21)]:
        x, y = int(math.floor(cx + sx * t)), int(math.floor(cy + sy * t))
        if 0 <= x < 16 and 0 <= y < 16:
            px[x, y] = (RED if t > 1.6 else RED_DK) + (255,)
            drawn.add((x, y))
    # the gold pin at the middle
    px[int(cx - 0.5), int(cy - 0.5)] = GOLD_HI + (255,)
    return img


def main():
    os.makedirs(TEX, exist_ok=True)
    os.makedirs(MOD, exist_ok=True)
    frames = []
    for f in range(32):
        img = needle(base(), f)
        img.save(os.path.join(TEX, 'capital_compass_%02d.png' % f))
        frames.append(img)
        with open(os.path.join(MOD, 'capital_compass_%02d.json' % f), 'w') as fh:
            json.dump({'parent': 'minecraft:item/generated', 'textures': {'layer0': '%s:item/capital_compass_%02d' % (NS, f)}}, fh, indent=1)
    # the overrides as Minecraft's compass has them: angle 0 is drawing 16 (straight ahead), a step of 1/32 a drawing
    overrides = [{'predicate': {'angle': 0.0}, 'model': '%s:item/capital_compass_16' % NS}]
    for k in range(1, 32):
        overrides.append({'predicate': {'angle': round((2 * k - 1) / 64.0, 6)}, 'model': '%s:item/capital_compass_%02d' % (NS, (k + 16) % 32)})
    overrides.append({'predicate': {'angle': round(63 / 64.0, 6)}, 'model': '%s:item/capital_compass_16' % NS})
    with open(os.path.join(MOD, 'capital_compass.json'), 'w') as fh:
        json.dump({'parent': 'minecraft:item/generated', 'textures': {'layer0': '%s:item/capital_compass_16' % NS}, 'overrides': overrides},
                  fh, indent=1)
    if len(sys.argv) > 2:
        sheet = Image.new('RGBA', (8 * 18 * 8, 4 * 18 * 8), (40, 40, 40, 255))
        for i, img in enumerate(frames):
            big = img.resize((128, 128), Image.NEAREST)
            sheet.paste(big, ((i % 8) * 144 + 8, (i // 8) * 144 + 8), big)
        sheet.save(sys.argv[2])


if __name__ == '__main__':
    main()

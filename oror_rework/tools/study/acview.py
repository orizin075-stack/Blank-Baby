"""Render Citadel (Alex's Caves) Java entity models with the preview renderer, for style study."""
import re, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mc'))
from rig import Rig, Bone, Cube, render
from PIL import Image

F = r'(-?[\d.]+)F?'
def load(java, tex):
    s = open(java).read()
    tw = int(re.search(r'texWidth\s*=\s*(\d+)', s).group(1)); th = int(re.search(r'texHeight\s*=\s*(\d+)', s).group(1))
    r = Rig('study', layout=(tw, th))
    pts, rots, parent, cubes = {}, {}, {}, {}
    for m in re.finditer(r'(\w+)\.setRotationPoint\(' + F + r',\s*' + F + r',\s*' + F + r'\)', s):
        pts[m.group(1)] = tuple(float(m.group(i)) for i in (2, 3, 4))
    for m in re.finditer(r'setRotateAngle\((\w+),\s*' + F + r',\s*' + F + r',\s*' + F + r'\)', s):
        rots[m.group(1)] = tuple(float(m.group(i)) for i in (2, 3, 4))
    for m in re.finditer(r'(\w+)\.addChild\((\w+)\)', s):
        parent[m.group(2)] = m.group(1)
    for m in re.finditer(r'(\w+)\.setTextureOffset\((\d+),\s*(\d+)\)\.addBox\(' + ',\s*'.join([F] * 6) + r'(?:,\s*' + F + r')?', s):
        cubes.setdefault(m.group(1), []).append(((int(m.group(2)), int(m.group(3))), tuple(float(m.group(i)) for i in range(4, 10)),
                                                  float(m.group(10) or 0)))
    names = [n for n in pts]
    done = {}
    def make(n):
        if n in done:
            return done[n]
        p = parent.get(n)
        pb = make(p) if p in pts else None
        base = pb.pivot if pb else (0, 0, 0)
        piv = tuple(base[i] + pts[n][i] for i in range(3))
        b = Bone(r, n, pb, piv, rots.get(n, (0, 0, 0)), None, {})
        for uv, box, g in cubes.get(n, []):
            c = Cube(b, box[:3], box[3:], None, grow=g)
            c.uv = uv
            b.cubes.append(c)
        r.bones.append(b); r.by_name[n] = b
        done[n] = b
        return b
    for n in names:
        make(n)
    return r, Image.open(tex)

if __name__ == '__main__':
    out = sys.argv[1]
    pairs = sys.argv[2:]
    ims = []
    for i in range(0, len(pairs), 2):
        r, tex = load(pairs[i], pairs[i + 1])
        for yaw in (35, 140):
            ims.append(render(r, tex, yaw, 12, (360, 360), None, cull=False))
    cols = 4
    rows = (len(ims) + cols - 1) // cols
    W = Image.new('RGB', (cols * 365, rows * 365), (36, 38, 46))
    for k, im in enumerate(ims):
        W.paste(im, ((k % cols) * 365, (k // cols) * 365))
    W.save(out)

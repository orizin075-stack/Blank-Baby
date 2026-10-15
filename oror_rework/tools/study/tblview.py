"""Render Tabula (.tbl model.json) entity models with the preview renderer, for style study."""
import json, math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mc'))
from rig import Rig, Bone, Cube, render
from PIL import Image

def load(d):
    m = json.load(open(os.path.join(d, 'model.json')))
    r = Rig('study', layout=(m['textureWidth'], m['textureHeight']))
    def walk(c, parent):
        base = parent.pivot if parent else (0, 0, 0)
        p = c['position']
        piv = tuple(base[i] + p[i] for i in range(3))
        b = Bone(r, c['name'] + str(len(r.bones)), parent, piv, tuple(math.radians(a) for a in c['rotation']), None, {})
        cube = Cube(b, tuple(c['offset']), tuple(c['dimensions']), None, grow=c.get('mcScale', 0.0))
        cube.uv = tuple(c['txOffset'])
        b.cubes.append(cube)
        r.bones.append(b)
        for ch in c.get('children', []):
            walk(ch, b)
    for c in m['cubes']:
        walk(c, None)
    for g in m.get('cubeGroups', []):
        for c in g.get('cubes', []):
            walk(c, None)
    return r, Image.open(os.path.join(d, 'texture.png'))

if __name__ == '__main__':
    out = sys.argv[1]
    ims = []
    for d in sys.argv[2:]:
        r, tex = load(d)
        print(d, len(r.bones), 'cubes', r.layout)
        for yaw in (35, 150):
            ims.append(render(r, tex, yaw, 14, (420, 360), None, cull=False))
    W = Image.new('RGB', (2 * 425, ((len(ims) + 1) // 2) * 365), (36, 38, 46))
    for k, im in enumerate(ims):
        W.paste(im, ((k % 2) * 425, (k // 2) * 365))
    W.save(out)

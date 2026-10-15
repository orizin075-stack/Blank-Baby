"""Render Bedrock geometry (TLM / GeckoLib) models with the preview renderer, for style study."""
import json, math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mc'))
from rig import Rig, Bone, Cube, render
from PIL import Image

def load(path, tex):
    m = json.load(open(path))
    if 'minecraft:geometry' in m:
        g = m['minecraft:geometry'][0]; d = g['description']; W, H = d['texture_width'], d['texture_height']
    else:
        key = [k for k in m if k.startswith('geometry')][0]; g = m[key]; W, H = g['texturewidth'], g['textureheight']
    r = Rig('study', layout=(W, H))
    byname = {}
    def jp(p):   # bedrock absolute -> java absolute (Blockbench: x and y mirrored)
        return (-p[0], 24 - p[1], p[2])
    pending = list(g['bones'])
    while pending:
        b = pending.pop(0)
        if b.get('parent') and b['parent'] not in byname:
            pending.append(b); continue
        par = byname.get(b.get('parent'))
        piv = jp(b.get('pivot', [0, 0, 0]))
        rot = b.get('rotation', [0, 0, 0])
        bone = Bone(r, b['name'], par, piv, (-math.radians(rot[0]), -math.radians(rot[1]), math.radians(rot[2])), None, {})
        r.bones.append(bone); byname[b['name']] = bone
        for i, c in enumerate(b.get('cubes', [])):
            o, s = c['origin'], c['size']
            uv = c.get('uv', [0, 0])
            face_uv = None
            if isinstance(uv, dict):
                names = {'north': 'front', 'south': 'back', 'east': 'right', 'west': 'left', 'up': 'top', 'down': 'bottom'}
                face_uv = {names[k]: (f['uv'][0], f['uv'][1], f.get('uv_size', [0, 0])[0], f.get('uv_size', [0, 0])[1])
                           for k, f in uv.items() if k in names and 'uv' in f}
                uv = [0, 0]
            target = bone
            if c.get('rotation'):
                cp = jp(c.get('pivot', [0, 0, 0])); cr = c['rotation']
                target = Bone(r, f"{b['name']}_c{i}", bone, cp, (-math.radians(cr[0]), -math.radians(cr[1]), math.radians(cr[2])), None, {})
                r.bones.append(target)
            mn = (-(o[0] + s[0]), 24 - (o[1] + s[1]), o[2])
            cube = Cube(target, tuple(mn[k] - target.pivot[k] for k in range(3)), tuple(s), None, grow=c.get('inflate', 0.0))
            cube.uv = tuple(uv)
            cube.face_uv = face_uv
            target.cubes.append(cube)
    return r, Image.open(tex)

if __name__ == '__main__':
    out = sys.argv[1]
    ims = []
    args = sys.argv[2:]
    for i in range(0, len(args), 2):
        r, tex = load(args[i], args[i + 1])
        print(args[i], len(r.bones), sum(len(b.cubes) for b in r.bones))
        for yaw in (25, 160):
            ims.append(render(r, tex, yaw, 8, (300, 420), None, cull=False))
    W = Image.new('RGB', (len(ims) * 305, 425), (36, 38, 46))
    for k, im in enumerate(ims):
        W.paste(im, (k * 305, 0))
    W.save(out)

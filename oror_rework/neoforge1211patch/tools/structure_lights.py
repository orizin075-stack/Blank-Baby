"""structure_lights.py <jar> <out dir> [name ...]: light the rooms of OROR's structure templates (r62; the user: "外に生成さ
れる建物の中に照明が無かったり").

Each template (data/oror_supreme_bosses/structure/**.nbt) is read as a grid: a cell the template leaves out (absent or
structure void) or fills with air is open, its other blocks are solid or not by kind. A place to stand indoors is an
open cell with an open cell above it, one of the template's solid blocks under it and one of its solid blocks somewhere
above it. One is dark when the template's own lights give it block light under 8. Until none is dark, each dark one in
turn gets a light near it (tools/citadel/lights.py's rule): a wall torch at head height on a wall within two blocks, a
lantern hanging from a ceiling three to eight blocks up, or a torch on the floor. A light goes only into an open cell;
the template's blocks are kept. Written gzip'd to <out dir>/<same path>, for the jar's overlay.
"""
import gzip, os, re, sys, zipfile
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'citadel'))
import anvil
from anvil import Typed
import lights

PREFIX = 'data/oror_supreme_bosses/structure/'


def state_key(p):
    props = p.get('Properties') or {}
    if not props:
        return p['Name']
    return p['Name'] + '[' + ','.join('%s=%s' % (k, anvil.val(v)) for k, v in sorted(props.items())) + ']'


def light_template(nbt):
    size = [anvil.val(v) for v in nbt['size']]
    X, Y, Z = size
    if 'palette' not in nbt:
        return None
    keys = [state_key(p) for p in nbt['palette']]
    info = [(bool(lights.PASS.search(k)) or k == 'minecraft:structure_void', lights.emit(k),
             not lights.PASS.search(k) and not lights.HOLD_NOT.search(k) and k != 'minecraft:structure_void',
             k in lights.AIRS or k == 'minecraft:structure_void') for k in keys]
    pas = np.ones((X, Y, Z), bool)
    src = np.zeros((X, Y, Z), np.int8)
    hold = np.zeros((X, Y, Z), bool)
    opn = np.ones((X, Y, Z), bool)
    at = {}
    for i, b in enumerate(nbt['blocks']):
        x, y, z = (anvil.val(v) for v in b['pos'])
        if not (0 <= x < X and 0 <= y < Y and 0 <= z < Z):
            continue
        s = anvil.val(b['state'])
        p, e, h, o = info[s]
        pas[x, y, z], src[x, y, z], hold[x, y, z], opn[x, y, z] = p, e, h, o
        at[(x, y, z)] = i
    if not hold.any():
        return None
    L = lights.propagate(pas, src)
    solid = ~pas
    roof = np.zeros_like(pas)
    acc = np.flip(np.logical_or.accumulate(np.flip(solid, 1), 1), 1)
    roof[:, :-1, :] = acc[:, 1:, :]
    st = opn.copy()
    st[:, 0, :] = False
    st[:, -1, :] = False
    st[:, 1:, :] &= hold[:, :-1, :]
    st[:, :-1, :] &= opn[:, 1:, :]
    st &= roof
    dark0 = st & (L < 8)
    if not dark0.any():
        return {'indoor': int(st.sum()), 'dark_before': 0, 'dark_after': 0, 'placed': 0}, None
    pal_index = {k: i for i, k in enumerate(keys)}
    placed = []
    R = 15

    def spread(x, y, z, level):
        x0, x1, y0, y1, z0, z1 = max(0, x - R), min(X, x + R + 1), max(0, y - R), min(Y, y + R + 1), max(0, z - R), min(Z, z + R + 1)
        s = np.zeros((x1 - x0, y1 - y0, z1 - z0), np.int8)
        s[x - x0, y - y0, z - z0] = level
        p = pas[x0:x1, y0:y1, z0:z1].copy()
        p[x - x0, y - y0, z - z0] = True
        np.maximum(L[x0:x1, y0:y1, z0:z1], lights.propagate(p, s), out=L[x0:x1, y0:y1, z0:z1])

    def put(x, y, z, state, name, props, level):
        if state not in pal_index:
            pal_index[state] = len(nbt['palette'])
            entry = {'Name': name}
            if props:
                entry['Properties'] = {k: v for k, v in props.items()}
            nbt['palette'].append(entry)
        idx = pal_index[state]
        if (x, y, z) in at:
            nbt['blocks'][at[(x, y, z)]]['state'] = Typed(3, idx)
        else:
            nbt['blocks'].append({'state': Typed(3, idx), 'pos': [Typed(3, x), Typed(3, y), Typed(3, z)]})
            at[(x, y, z)] = len(nbt['blocks']) - 1
        opn[x, y, z] = False
        spread(x, y, z, level)
        placed.append(name)

    cells = np.argwhere(dark0)
    order = np.lexsort((cells[:, 2], cells[:, 0], cells[:, 1]))
    rng = np.random.default_rng(62)
    blocks = np.array_split(order, max(1, len(order) // 4000))
    for b in blocks:
        rng.shuffle(b)
    for i in np.concatenate(blocks):
        x, y, z = (int(v) for v in cells[i])
        if L[x, y, z] >= 8:
            continue
        h = y + 1
        best = None
        for r in (0, 1, 2):
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if best or max(abs(dx), abs(dz)) != r:
                        continue
                    px, pz = x + dx, z + dz
                    if not (0 <= px < X and 0 <= pz < Z) or not opn[px, h, pz]:
                        continue
                    for (wx, wz), facing in lights.DIRS.items():
                        qx, qz = px + wx, pz + wz
                        if 0 <= qx < X and 0 <= qz < Z and hold[qx, h, qz]:
                            best = (px, pz, facing)
                            break
            if best:
                break
        if best:
            put(best[0], h, best[1], 'minecraft:wall_torch[facing=%s]' % best[2], 'minecraft:wall_torch', {'facing': best[2]}, 14)
            continue
        done = False
        for k in range(3, 9):
            if y + k >= Y or not opn[x, y + k - 1, z]:
                break
            if hold[x, y + k, z]:
                put(x, y + k - 1, z, 'minecraft:lantern[hanging=true,waterlogged=false]', 'minecraft:lantern',
                    {'hanging': 'true', 'waterlogged': 'false'}, 15)
                done = True
                break
            if not pas[x, y + k, z]:
                break
        if not done:
            put(x, y, z, 'minecraft:torch', 'minecraft:torch', None, 14)
    dark1 = st & (L < 8) & opn
    from collections import Counter
    return {'indoor': int(st.sum()), 'dark_before': int(dark0.sum()), 'dark_after': int(dark1.sum()),
            'placed': dict(Counter(placed))}, nbt


def main():
    jar, out = sys.argv[1], sys.argv[2]
    want = sys.argv[3:]
    z = zipfile.ZipFile(jar)
    for n in sorted(z.namelist()):
        if not (n.startswith(PREFIX) and n.endswith('.nbt')):
            continue
        rel = n[len(PREFIX):-4]
        if want and rel not in want:
            continue
        nbt = anvil.read_nbt_typed(gzip.decompress(z.read(n)))
        res = light_template(nbt)
        if res is None:
            print(rel, 'skipped (no palette or no solid block)')
            continue
        report, new = res
        print(rel, report, flush=True)
        if new is not None:
            path = os.path.join(out, PREFIX, rel + '.nbt')
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                # level 6: the jar deflates it again, and a level-6 stream deflates far better than a level-9 one
                f.write(gzip.compress(anvil.write_nbt(new), 6, mtime=0))


if __name__ == '__main__':
    main()

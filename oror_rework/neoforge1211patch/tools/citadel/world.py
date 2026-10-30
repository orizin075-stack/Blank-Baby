"""Load a box of the citadel save into a numpy array of global palette ids: world.load(save, x0, x1, z0, z1)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import anvil

NAMES = ['minecraft:air']
IDS = {'minecraft:air': 0}


def gid(name):
    if name not in IDS:
        IDS[name] = len(NAMES)
        NAMES.append(name)
    return IDS[name]


def unpack(longs, bits, n=4096):
    per = 64 // bits
    mask = (1 << bits) - 1
    out = np.empty(n, np.int64)
    arr = np.array(longs, dtype=np.int64).view(np.uint64)
    i = 0
    for v in arr:
        v = int(v)
        for k in range(per):
            if i >= n:
                break
            out[i] = (v >> (k * bits)) & mask
            i += 1
    return out


def load(save, x0, x1, z0, z1, y0=0, y1=192):
    """Blocks in [x0,x1) x [y0,y1) x [z0,z1) as arr[x-x0, y-y0, z-z0]; also returns block entities in the box."""
    arr = np.zeros((x1 - x0, y1 - y0, z1 - z0), np.uint16)
    bes = []
    reg = os.path.join(save, 'region')
    for rx in range(math.floor(x0 / 512), math.floor((x1 - 1) / 512) + 1):
        for rz in range(math.floor(z0 / 512), math.floor((z1 - 1) / 512) + 1):
            p = os.path.join(reg, f'r.{rx}.{rz}.mca')
            if not os.path.exists(p):
                continue
            for lx, lz, ln, nbt in anvil.chunks(p):
                cx, cz = nbt['xPos'], nbt['zPos']
                bx, bz = cx * 16, cz * 16
                if bx + 16 <= x0 or bx >= x1 or bz + 16 <= z0 or bz >= z1:
                    continue
                for s in nbt['sections']:
                    bs = s.get('block_states')
                    if not bs:
                        continue
                    by = s['Y'] * 16
                    if by + 16 <= y0 or by >= y1:
                        continue
                    pal = [gid(p['Name']) for p in bs['palette']]
                    if len(pal) == 1:
                        idx = np.zeros(4096, np.int64)
                    else:
                        bits = max(4, (len(pal) - 1).bit_length())
                        idx = unpack(bs['data'][1], bits)
                    blk = np.array(pal, np.uint16)[idx].reshape(16, 16, 16)  # y, z, x
                    blk = blk.transpose(2, 0, 1)  # x, y, z
                    xs, xe = max(bx, x0), min(bx + 16, x1)
                    zs, ze = max(bz, z0), min(bz + 16, z1)
                    ys, ye = max(by, y0), min(by + 16, y1)
                    arr[xs - x0:xe - x0, ys - y0:ye - y0, zs - z0:ze - z0] = blk[xs - bx:xe - bx, ys - by:ye - by, zs - bz:ze - bz]
                for be in nbt.get('block_entities', []):
                    if x0 <= be['x'] < x1 and z0 <= be['z'] < z1 and y0 <= be['y'] < y1:
                        bes.append(be)
    return arr, bes

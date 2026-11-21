"""ornament.py <template dir> [report.json]: the capital's walls, towers and palace finished more finely and richly (r63; the
user: "もう少し建築 繊細で豪勢に 美しく").

Only the faces the sky sees are touched: a cell is outside when nothing solid stands anywhere above it. Nothing is cut:
blocks of a face are exchanged for others of the same kind of stone, and what stands out from a face hangs in open air
with nothing under it for four blocks (no walk, stair, door or gun port is touched; a corbel is never put where a cell
of the face near it is open, so the casemates' ports keep their line of fire).

The fortifications (polished blackstone bricks: the three walls, their towers and gatehouses, the keep):
  * a string course every eight blocks up the face (polished blackstone, one block in seven gilded blackstone);
  * a corbel table under the top of every face: an upside-down blackstone brick stair against the face, all along it.
The palace (quartz bricks, calcite, smooth quartz):
  * pilasters: every seventh column of a face up its whole height in quartz pillars;
  * a frieze under the eaves (chiseled quartz, a gold block every twelfth) and over it a cornice of upside-down quartz
    stairs.
"""
import json, os, sys, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_io

TILE = 128
Y0, Y1 = 60, 191
FORT = 'minecraft:polished_blackstone_bricks'
PALACE = ('minecraft:quartz_bricks', 'minecraft:calcite', 'minecraft:smooth_quartz')
DIRS = {(1, 0): 'east', (-1, 0): 'west', (0, 1): 'south', (0, -1): 'north'}
AIRS = ('minecraft:air', 'minecraft:cave_air')


def run(folder):
    t = template_io.Template(folder)
    stats = collections.Counter()
    for x0 in range(-640, 640, TILE):
        for z0 in range(-640, 640, TILE):
            tile(t, x0, z0, stats)
            t.chunks.clear()
            t.sections.clear()
        print(x0, dict(stats), flush=True)
    n = t.save(folder)
    stats['chunks_written'] = n
    return dict(stats)


def tile(t, x0, z0, stats):
    m = 2
    bx0, bx1, bz0, bz1 = max(-640, x0 - m), min(639, x0 + TILE - 1 + m), max(-640, z0 - m), min(639, z0 + TILE - 1 + m)
    b = t.box(bx0, bx1, Y0, Y1, bz0, bz1)
    keys, inv = np.unique(b, return_inverse=True)
    inv = inv.reshape(b.shape)
    air = np.isin(keys, AIRS)[inv]
    solid = ~air
    # open to the sky: no solid anywhere above
    above = np.flip(np.logical_or.accumulate(np.flip(solid, 1), 1), 1)
    sky = np.zeros_like(air)
    sky[:, :-1, :] = ~above[:, 1:, :]
    sky[:, -1, :] = True
    sky &= air
    fort = (keys == FORT)[inv]
    palace = np.isin(keys, PALACE)[inv]
    X, Y, Z = b.shape
    edits = {}

    def face_dirs(x, y, z):
        out = []
        for (dx, dz), name in DIRS.items():
            qx, qz = x + dx, z + dz
            if 0 <= qx < X and 0 <= qz < Z and sky[qx, y, qz]:
                out.append((dx, dz))
        return out

    inner = lambda x, z: x0 <= x + bx0 < x0 + TILE and z0 <= z + bz0 < z0 + TILE
    # --- the fortifications
    for x, y, z in np.argwhere(fort):
        if not inner(x, z):
            continue
        wy = y + Y0
        dirs = face_dirs(x, y, z)
        if not dirs:
            continue
        wx, wz = x + bx0, z + bz0
        if (wy - 64) % 8 == 0 and wy >= 70:
            edits[(wx, wy, wz)] = 'minecraft:gilded_blackstone' if (wx + wz) % 7 == 0 else 'minecraft:polished_blackstone'
            stats['fort_course'] += 1
        # the top of the face: the cell above is no longer the face's stone
        if y + 1 < Y and not fort[x, y + 1, z]:
            for dx, dz in dirs:
                ox, oz = x + dx, z + dz
                # the corbel hangs one below the top, in open air with four free blocks under it, beside a whole face
                cy = y - 1
                if cy - 4 < 0 or not all(sky[ox, cy - k, oz] for k in range(0, 5)):
                    continue
                if not all(fort[x, cy - k, z] for k in range(0, 3)):
                    continue                                    # an opening in the face near it (a port, a loop)
                if not (fort[x + dz, y, z + dx] if 0 <= x + dz < X and 0 <= z + dx < Z else False) and \
                   not (fort[x - dz, y, z - dx] if 0 <= x - dz < X and 0 <= z - dx < Z else False):
                    continue                                    # a lone post, not a face
                facing = DIRS[(-dx, -dz)]
                edits[(ox + bx0, cy + Y0, oz + bz0)] = 'minecraft:polished_blackstone_brick_stairs[facing=%s,half=top,shape=straight,waterlogged=false]' % facing
                stats['fort_corbel'] += 1
    # --- the palace
    for x, y, z in np.argwhere(palace):
        if not inner(x, z):
            continue
        dirs = face_dirs(x, y, z)
        if not dirs:
            continue
        wx, wy, wz = x + bx0, y + Y0, z + bz0
        top = y + 1 < Y and not palace[x, y + 1, z]
        along = wz if dirs[0][0] != 0 else wx                   # the coordinate along the face
        if top:
            # the cornice over the frieze, in the open air outside the top of the face
            for dx, dz in dirs:
                ox, oz = x + dx, z + dz
                if y - 3 < 0 or not all(sky[ox, y - k, oz] for k in range(0, 4)):
                    continue
                edits[(ox + bx0, wy, oz + bz0)] = 'minecraft:quartz_stairs[facing=%s,half=top,shape=straight,waterlogged=false]' % DIRS[(-dx, -dz)]
                stats['palace_cornice'] += 1
            if y - 1 >= 0 and palace[x, y - 1, z]:
                edits[(wx, wy - 1, wz)] = 'minecraft:gold_block' if along % 12 == 0 else 'minecraft:chiseled_quartz_block'
                stats['palace_frieze'] += 1
            continue
        if along % 7 == 0 and wy >= 65:
            edits[(wx, wy, wz)] = 'minecraft:quartz_pillar[axis=y]'
            stats['palace_pilaster'] += 1
    for (wx, wy, wz), state in edits.items():
        if t.set(wx, wy, wz, state):
            stats['set'] += 1


def main():
    folder = sys.argv[1]
    stats = run(folder)
    print(json.dumps(stats))
    if len(sys.argv) > 2:
        json.dump(stats, open(sys.argv[2], 'w'), indent=1)


if __name__ == '__main__':
    main()

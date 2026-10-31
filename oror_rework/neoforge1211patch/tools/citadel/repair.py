"""repair.py <save in> <save out> [report.json]: the Grand Citadel v12 save, repaired and lit.

Town: the 112 town buildings were 17 to 25 blocks wide, up to four storeys, roofed with a single diagonal line of
blocks per slope and nearly empty inside. Each is cleared from its plot and rebuilt by houses.py: smaller (7 to 13
wide), in ten styles with gable or hipped roofs, furnished for its trade, lit, with a yard; TOWN_BUILDINGS.json in the
repaired save lists what was built and where the townsfolk can stand (tools/citadel/garrison.py reads it).
Castle: the generator left several timber-framed facades without their panels (the west wing's whole outer side,
holes in the east wing, bands of the keep) and skipped columns of its tiled roofs. Large openings where a roofed,
floored room meets the sky are walled with the material around them (with glass windows), and short gaps in the roofs
are tiled over. Lanterns left floating in the air (the plaza's, some of the gatehouses') get posts or chains,
and small groups of blocks floating free (ladders against nothing, single lights, bars, hovering finials) are removed.
The inner ward (keep, labyrinth, throne room, gatehouses) is then lit. A block-light model of the save (emitters and
transparent blocks by name, 15 steps of spread) finds every walkable, roofed floor cell below light 8; lights go in
greedily: a lantern hung (on a chain in tall rooms) three blocks above the floor under a ceiling four to fourteen
blocks up, else a sea lantern set into a low plain ceiling, else an invisible light block at head height.
"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import world, anvil_edit, loot
from scipy import ndimage

TRANSPARENT = ('air', 'glass', 'pane', 'fence', '_wall', 'slab', 'stairs', 'ladder', 'torch', 'lantern', 'chain', 'carpet', 'rail',
               'button', 'lever', 'pressure_plate', 'sign', 'banner', 'flower', 'grass', 'fern', 'vine', 'water', 'iron_bars', 'door',
               '_bed', 'chest', 'candle', 'end_rod', 'light', 'scaffolding', 'cobweb', 'skull', '_head', 'flower_pot', 'sapling',
               'anvil', 'bell', 'lectern', 'campfire', 'brewing', 'enchanting', 'cake', 'snow', 'leaves', 'tripwire', 'redstone_wire',
               'repeater', 'comparator', 'hopper', 'cauldron', 'composter', 'grindstone', 'stonecutter', 'dripstone', 'amethyst_cluster',
               'bud', 'coral', 'kelp', 'seagrass', 'mushroom', 'roots', 'sprouts', 'azalea', 'dead_bush', 'sugar_cane', 'bamboo',
               'trapdoor', 'frame', 'painting', 'conduit', 'beacon', 'spawner', 'web', 'string', 'pickle', 'banner')
EMIT = {'lantern': 15, 'sea_lantern': 15, 'glowstone': 15, 'shroomlight': 15, 'ochre_froglight': 15, 'verdant_froglight': 15,
        'pearlescent_froglight': 15, 'torch': 14, 'wall_torch': 14, 'soul_lantern': 10, 'soul_torch': 10, 'soul_wall_torch': 10,
        'end_rod': 14, 'campfire': 15, 'soul_campfire': 10, 'jack_o_lantern': 15, 'beacon': 15, 'conduit': 15, 'light': 15,
        'crying_obsidian': 10, 'magma_block': 3, 'candle': 6, 'lava': 15, 'fire': 15, 'redstone_torch': 7, 'glow_lichen': 7,
        'amethyst_cluster': 5, 'sculk_catalyst': 6, 'enchanting_table': 7, 'brewing_stand': 1, 'respawn_anchor': 15}
PLAIN = ('bricks', 'planks', 'stone', 'deepslate', 'calcite', 'quartz', 'concrete', 'terracotta', 'tiles', 'polished', 'smooth',
         'andesite', 'diorite', 'granite', 'tuff', 'blackstone', 'prismarine', 'cobblestone', 'sandstone', 'obsidian')
TARGET = 8


def short(i):
    return world.NAMES[i].split(':')[1]


def tables():
    n = len(world.NAMES)
    air = np.zeros(n, bool)
    transparent = np.zeros(n, bool)
    emit = np.zeros(n, np.int16)
    plain = np.zeros(n, bool)
    soft = np.zeros(n, bool)
    for i in range(n):
        s = short(i)
        air[i] = s in ('air', 'cave_air', 'void_air')
        transparent[i] = air[i] or any(t in s for t in TRANSPARENT)
        emit[i] = EMIT.get(s, 15 if s.endswith('froglight') else 6 if s.endswith('candle') else 0)
        plain[i] = not transparent[i] and any(p in s for p in PLAIN) and not any(b in s for b in ('ore', 'chest', 'dispenser', 'dropper', 'observer', 'piston', 'redstone', 'sculk', 'spawner', 'tnt'))
        soft[i] = any(t in s for t in ('water', 'lava', 'ladder', 'vine', 'scaffolding', 'cobweb', 'web', 'tripwire', 'pressure_plate', 'rail', 'carpet', 'snow'))
    return air, transparent, emit, plain, soft


ROADS = ('cobblestone', 'polished_andesite', 'gravel', 'stone_bricks', 'deepslate_bricks', 'bricks', 'dirt_path', 'andesite')
YARD = ('grass_block', 'dirt', 'coarse_dirt', 'dirt_path', 'podzol')


def town_plots(save, man):
    """Each town building's plot: the grass around its old footprint up to the roads, the moat, the fields or halfway
    to the next building (16 blocks at most each way), and the side it fronts: the nearest road (toward the castle
    when two are as near), or the castle when there is no road."""
    H = man['individual_town_architecture']
    O = 480
    a, _ = world.load(save, -O, O, -O, O, 64, 65)
    g = a[:, 0, :]
    names = [n.split(':')[1] for n in world.NAMES]
    grass = np.array([n == 'grass_block' for n in names] + [False] * 8)
    foot = [(h['x'] - h['size'][0] // 2, h['z'] - h['size'][1] // 2, h['x'] + h['size'][0] // 2, h['z'] + h['size'][1] // 2) for h in H]
    out = []
    for i, h in enumerate(H):
        cx, cz = h['x'], h['z']
        ext = {}
        for name, (dx, dz), half in (('east', (1, 0), h['size'][0] // 2), ('west', (-1, 0), h['size'][0] // 2),
                                     ('south', (0, 1), h['size'][1] // 2), ('north', (0, -1), h['size'][1] // 2)):
            k = half + 1
            while k < 40:
                x, z = cx + dx * k, cz + dz * k
                if not all(grass[g[x + O + (dz != 0) * t, z + O + (dx != 0) * t]] for t in (-5, 0, 5)):
                    break
                k += 1
            hx, hz = cx + dx * k, cz + dz * k
            lim, what = min(16, k - 1), None
            if k >= 40:
                what = 'open'
            for j, f in enumerate(foot):
                if what is None and j != i and f[0] <= hx <= f[2] and f[1] <= hz <= f[3]:
                    what = 'house'
                    lim = min(lim, abs((H[j]['x'] - cx) * dx + (H[j]['z'] - cz) * dz) // 2 - 1)
            if what is None:
                n = names[g[hx + O, hz + O]]
                what = 'water' if n == 'water' else 'road' if n in ROADS else 'field'
            ext[name] = (lim, what, k - 1)
        roads = [d for d in ext if ext[d][1] == 'road' and ext[d][2] <= 20]
        toward = {'east': -cx, 'west': cx, 'south': -cz, 'north': cz}
        if roads:
            front = min(roads, key=lambda d: (ext[d][2], -toward[d]))
            ext[front] = (ext[front][2], 'road', ext[front][2])        # the plot runs to the road
        else:
            front = max(toward, key=lambda d: toward[d])
        out.append(((cx - ext['west'][0], cz - ext['north'][0], cx + ext['east'][0], cz + ext['south'][0]), front, ext))
    return out


def rebuild_town(save, man, edits, bes, stats):
    """The town buildings rebuilt by houses.py on their plots: everything above the ground of the plot cleared (only on
    the plot's grass and the old footprint, never a road, the moat or a field), the new house, its yard and its block
    entities put in. Returns the cleared columns and, per building, what was built and where its townsfolk can stand."""
    import houses
    H = man['individual_town_architecture']
    cleared, town = set(), []
    for h, (plot, front, ext) in zip(H, town_plots(save, man)):
        x0, z0, x1, z1 = plot
        a, _ = world.load(save, x0, x1 + 1, z0, z1 + 1, 64, 200)
        hw, hd = h['size'][0] // 2, h['size'][1] // 2
        writable = set()
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                n = short(a[x - x0, 0, z - z0])
                if n in YARD or (abs(x - h['x']) <= hw + 1 and abs(z - h['z']) <= hd + 1):
                    writable.add((x, z))
        house = houses.build(plot, h['kind'], 7919 * h['id'] + 17, front)
        for (x, z) in writable:
            col = a[x - x0, :, z - z0]
            for yy in np.nonzero(col[1:])[0] + 1:
                edits[(x, int(yy) + 64, z)] = 'minecraft:air'
            edits[(x, 64, z)] = 'minecraft:grass_block'
        cleared |= writable
        lost = 0
        for (x, y, z), st in house.blocks.items():
            if (x, z) in writable:
                edits[(x, y, z)] = st
            else:
                lost += 1
        for p, be in houses.entities(house, h['id']).items():
            if (p[0], p[2]) in writable:
                bes[p] = be
        stats['houses'] += 1
        stats['house_blocks'] += len(house.blocks) - lost
        stats['house_blocks_off_plot'] += lost
        stats['styles'][house.style] += 1
        stats['roofs'][house.roof_kind] += 1
        town.append(dict(id=h['id'], kind=h['kind'], x=h['x'], z=h['z'], front=front, plot=list(plot), style=house.style, station=house.station,
                         width=house.W, depth=house.D, floors=house.floors, roof=house.roof_kind,
                         spots=[list(p) for p in house.spots if (p[0], p[2]) in writable]))
    return cleared, town


PASSABLE = ('air', 'door', 'trapdoor', 'stairs', 'slab', 'carpet', 'ladder', 'light', 'torch', 'lantern', 'chain', 'rail', 'flower', 'grass',
            'fern', 'button', 'lever', 'sign', 'banner', 'scaffolding', 'vine', 'snow')
TRAPS = ('pressure_plate', 'tripwire', 'redstone', 'dispenser', 'observer', 'piston', 'tnt', 'magma', 'cobweb', 'water', 'lava')
RING = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
THRONE = (0, 135, -32)        # the king's feet cell on the dais
FACING = {(1, 0): 'east', (-1, 0): 'west', (0, 1): 'south', (0, -1): 'north'}


def storerooms(save, x0, x1, z0, z1, y0, y1, edits, bes, stats, placed, theme_of, budget=3, name=None, box=None, pick_rooms=None, spacing=6):
    """Chests in the rooms of a box: every walled, roofed room of 12+ floor cells gets one to budget chests (one per 45
    cells), in corners first, on cells that are not a way through (the free cells around stay joined without them),
    never next to a door, a trap or a pressure plate, six blocks from every other chest. theme_of(x, y, z, room size,
    room id) names the loot (None: no chest in that room); pick_rooms, given [(room id, cells, world centre, (width along
    x, width along z))], keeps some of the rooms. Returns the chests placed."""
    a, _ = world.load(save, x0, x1, z0, z1, y0, y1)
    for (x, y, z), st in edits.items():
        if x0 <= x < x1 and z0 <= z < z1 and y0 <= y < y1:
            a[x - x0, y - y0, z - z0] = world.gid(st.split('[')[0])
    air, transparent, emit, plain, soft = tables()
    n = len(world.NAMES)
    passable = np.array([any(t in world.NAMES[i] for t in PASSABLE) for i in range(n)])
    trap = np.array([any(t in world.NAMES[i] for t in TRAPS) for i in range(n)])
    isair = air[a]
    opaque = ~transparent[a]
    covered = np.zeros_like(isair)
    run = np.full((a.shape[0], a.shape[2]), 999, np.int32)
    for y in range(a.shape[1] - 1, -1, -1):
        run = np.where(opaque[:, y, :], 0, run + 1)
        covered[:, y, :] = run <= 24
    floor = np.zeros_like(isair)
    floor[:, 1:, :] = opaque[:, :-1, :] & ~soft[a[:, :-1, :]]
    head = np.zeros_like(isair)
    head[:, :-1, :] = isair[:, 1:, :]
    walk = isair & floor & head & covered
    if box is not None:
        bx0, bx1, bz0, bz1, by0, by1 = box
        keep = np.zeros_like(walk)
        keep[bx0 - x0:bx1 - x0, by0 - y0:by1 - y0, bz0 - z0:bz1 - z0] = True
        walk &= keep
    way = passable[a]
    near_trap = trap[a]
    st = np.zeros((3, 3, 3), bool)
    st[1, 1, 1] = st[0, 1, 1] = st[2, 1, 1] = st[1, 1, 0] = st[1, 1, 2] = True
    lab, nrooms = ndimage.label(walk, structure=st)
    if nrooms == 0:
        return []
    sizes = ndimage.sum(walk, lab, index=np.arange(1, nrooms + 1))
    allowed = None
    if pick_rooms is not None:
        centres = ndimage.center_of_mass(walk, lab, index=np.arange(1, nrooms + 1))
        spans = [(sl[0].stop - sl[0].start, sl[2].stop - sl[2].start) for sl in ndimage.find_objects(lab)]
        allowed = set(pick_rooms([(i + 1, int(sizes[i]), (c[0] + x0, c[1] + y0, c[2] + z0), spans[i]) for i, c in enumerate(centres)]))
    X, Y, Z = a.shape
    cands = collections.defaultdict(list)
    for x, y, z in zip(*np.nonzero(walk & (lab > 0))):
        if x < 1 or z < 1 or x >= X - 1 or z >= Z - 1 or sizes[lab[x, y, z] - 1] < (9 if allowed else 12):
            continue
        if allowed is not None and lab[x, y, z] not in allowed:
            continue
        walls = [(dx, dz) for dx, dz in FACING if opaque[x + dx, y, z + dz] and not way[x + dx, y, z + dz]]
        if not walls:
            continue
        # no door, trap or plate around it, on the floor or at head height
        if any(near_trap[x + dx, yy, z + dz] or 'door' in world.NAMES[a[x + dx, yy, z + dz]]
               for dx, dz in RING for yy in (y - 1, y, y + 1) if 0 <= yy < Y):
            continue
        # not a way through: the passable cells around it stay one group without it
        free = [way[x + dx, y, z + dz] and head[x + dx, y, z + dz] or walk[x + dx, y, z + dz] for dx, dz in RING]
        groups, seen = 0, set()
        for i in range(8):
            if free[i] and i not in seen:
                groups += 1
                todo = [i]
                while todo:
                    j = todo.pop()
                    if j in seen:
                        continue
                    seen.add(j)
                    for k in ((j + 1) % 8, (j - 1) % 8):
                        if free[k] and k not in seen:
                            todo.append(k)
        orth_free = [free[i] for i in (0, 2, 4, 6)]
        if groups != 1 or not any(orth_free):
            continue
        cands[lab[x, y, z]].append((len(walls), x, y, z, [d for d, f in zip(((1, 0), (0, 1), (-1, 0), (0, -1)), orth_free) if f]))
    rng = np.random.default_rng(abs(x0 * 7 + z0 * 13 + y0))
    out = []
    for room, cs in sorted(cands.items()):
        size = int(sizes[room - 1])
        cs.sort(key=lambda c: (-c[0], rng.random()))
        want = budget if allowed is not None else min(budget, max(1, size // 45))
        for walls_n, x, y, z, opens in cs:
            if want <= 0:
                break
            wx, wy, wz = int(x + x0), int(y + y0), int(z + z0)
            theme = theme_of(wx, wy, wz, size, room)
            if theme is None:
                break
            if any(abs(wx - px) + abs(wz - pz) + 2 * abs(wy - py) < spacing for px, py, pz in placed):
                continue
            facing = FACING[opens[0]]
            edits[(wx, wy, wz)] = f'minecraft:chest[facing={facing},type=single,waterlogged=false]'
            be = {'id': 'minecraft:chest', 'x': wx, 'y': wy, 'z': wz,
                  'Items': loot.items(theme, (wx * 73856093) ^ (wy * 19349663) ^ (wz * 83492791))}
            if name:
                be['CustomName'] = json.dumps({'text': name(theme)}, ensure_ascii=False)
            bes[(wx, wy, wz)] = be
            placed.append((wx, wy, wz))
            stats['stores'][theme] += 1
            out.append((wx, wy, wz, theme))
            want -= 1
    return out


STORE_NAMES = {'armory': '武器庫', 'pantry': '食料庫', 'keep': '城の倉', 'royal': '王家の蔵', 'treasury': '王家の宝物庫', 'vault': '王家の禁庫'}


def stock_empty(save, cleared, edits, bes, stats):
    """Chests and barrels the save left empty (mostly the old mines' barrels) get goods: mining supplies underground,
    stores above ground; the town's are rebuilt and stocked by houses.py."""
    import anvil
    for f in sorted(os.listdir(os.path.join(save, 'region'))):
        for lx, lz, ln, nbt in anvil.chunks(os.path.join(save, 'region', f)):
            for be in nbt.get('block_entities', []):
                kind = be['id'].split(':')[1]
                p = (be['x'], be['y'], be['z'])
                if kind not in ('chest', 'barrel') or be.get('Items') or 'LootTable' in be or p[1] >= 64 and (p[0], p[2]) in cleared or p in bes:
                    continue
                theme = 'mine' if p[1] < 60 else 'storage'
                new = {'id': be['id'], 'x': p[0], 'y': p[1], 'z': p[2], 'Items': loot.items(theme, p[0] * 31 + p[1] * 7 + p[2] * 131)}
                if be.get('CustomName'):
                    new['CustomName'] = be['CustomName']
                bes[p] = new
                stats['stores']['restocked ' + theme] += 1


def castle_stores(save, edits, bes, stats):
    """The castle's storerooms: the inner ward's rooms get chests, the treasury beside the throne room is filled."""
    placed = []
    tx, ty, tz = THRONE

    def hall(x, y, z):
        # the throne hall stays as it is: the court stands there
        return ty - 1 <= y <= ty + 6 and abs(x - tx) <= 13 and tz - 5 <= z <= tz + 21

    def theme_of(x, y, z, size, room):
        if hall(x, y, z):
            return None
        if abs(y - ty) <= 12 and abs(x - tx) + abs(z - tz) <= 45:
            return 'royal'
        if y >= 96:
            return 'keep'
        return 'armory' if (x // 24 + z // 24 + room) % 2 else 'pantry'
    for qx0, qx1 in ((-136, 0), (0, 136)):
        for qz0, qz1 in ((-136, 0), (0, 136)):
            storerooms(save, qx0, qx1, qz0, qz1, 64, 192, edits, bes, stats, placed, theme_of, name=lambda t: STORE_NAMES[t])
    # the royal treasury: the real room (20 to 300 floor cells, four or more across both ways) nearest the throne, the hall
    # left out; in the citadel this is the raised chamber of the undercroft right under the throne, up a ladder from it
    def nearest(rooms):
        near = [(abs(c[0] - tx) + abs(c[2] - tz) + 3 * abs(c[1] - ty), r) for r, n, c, (wx, wz) in rooms
                if 20 <= n <= 300 and min(wx, wz) >= 4 and not hall(round(c[0]), round(c[1]), round(c[2]))]
        return [min(near)[1]] if near else []
    trs = storerooms(save, tx - 60, tx + 61, tz - 60, tz + 61, ty - 17, ty + 25, edits, bes, stats, placed,
                     lambda *a: 'treasury', budget=8, name=lambda t: STORE_NAMES[t], pick_rooms=nearest, spacing=2)
    stats['treasury_at'] = [list(t[:3]) for t in trs]
    stats['treasury_rooms'] = len({(x, z) for x, y, z, t in trs})
    return placed


def vault_hoard(save, man, edits, bes, stats):
    """The forbidden vault (v9_true_treasury, deep under the town): its four pedestal chests hold the kingdom's hoard,
    and its chamber gets more along the walls."""
    vx, vz = man['v9_true_treasury']
    _, found = world.load(save, vx - 3, vx + 4, vz - 3, vz + 4, 0, 30)
    n = 0
    for be in found:
        if be['id'].endswith('chest'):
            x, y, z = be['x'], be['y'], be['z']
            bes[(x, y, z)] = {'id': 'minecraft:chest', 'x': x, 'y': y, 'z': z, 'CustomName': json.dumps({'text': STORE_NAMES['vault']}, ensure_ascii=False),
                              'Items': loot.items('vault', x * 31 + z * 17 + y)}
            n += 1
            stats['stores']['vault'] += 1
    placed = [(x, y, z) for (x, y, z) in bes if abs(x - vx) <= 3 and abs(z - vz) <= 3]
    storerooms(save, vx - 12, vx + 13, vz - 6, vz + 7, 2, 20, edits, bes, stats, placed, lambda *a: 'vault', budget=6,
               name=lambda t: STORE_NAMES[t], box=(vx - 9, vx + 3, vz - 2, vz + 3, 2, 20), spacing=3)
    stats['vault_pedestal_chests'] = n



def castle_walls(save, x0, x1, z0, z1, edits, stats, ymin=74):
    """Walls the timber frames the generator left without panels: every opening of 12+ cells (y >= ymin) where a
    floored, roofed room meets open sky sideways is filled with the wall material around it, with a glass window in
    every fourth column of its second row."""
    a, _ = world.load(save, x0, x1, z0, z1, 64, 192)
    for (x, y, z), st in edits.items():
        if x0 <= x < x1 and z0 <= z < z1 and 64 <= y < 192:
            a[x - x0, y - 64, z - z0] = world.gid(st.split('[')[0])
    air, transparent, emit, plain, soft = tables()
    isair = air[a]
    opaque = ~transparent[a]
    covered = np.zeros_like(isair)
    run = np.full((a.shape[0], a.shape[2]), 999, np.int32)
    for y in range(a.shape[1] - 1, -1, -1):
        run = np.where(opaque[:, y, :], 0, run + 1)
        covered[:, y, :] = run <= 24
    solidish = ~isair & ~soft[a]
    floored = np.zeros_like(isair)
    for k in range(1, 4):
        floored[:, k:, :] |= solidish[:, :-k, :]
    inner = isair & covered & floored
    inner[:, :ymin - 64, :] = False
    outside = isair & ~covered
    woodish = np.array(['log' in n or 'wood' in n or 'planks' in n or 'fence' in n for n in world.NAMES])
    filled = 0
    for axis in (0, 2):
        for sign in (1, -1):
            nb = np.zeros_like(outside)
            src = [slice(None)] * 3
            dst = [slice(None)] * 3
            if sign > 0:
                dst[axis], src[axis] = slice(None, -1), slice(1, None)
            else:
                dst[axis], src[axis] = slice(1, None), slice(None, -1)
            nb[tuple(dst)] = outside[tuple(src)]
            e = inner & nb
            st = np.zeros((3, 3, 3), bool)
            st[1, 1, 1] = True
            st[1, 0, 1] = st[1, 2, 1] = True
            if axis == 0:
                st[1, 1, 0] = st[1, 1, 2] = True
            else:
                st[0, 1, 1] = st[2, 1, 1] = True
            lab, n = ndimage.label(e, structure=st)
            for i, sl in enumerate(ndimage.find_objects(lab), 1):
                cells = np.argwhere(lab[sl] == i) + [q.start for q in sl]
                if len(cells) < 12:
                    continue
                # the wall material: the commonest plain block around the opening in its plane
                around = collections.Counter()
                for x, y, z in cells[::max(1, len(cells) // 40)]:
                    for dx, dy, dz in ((0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1)):
                        q = (x + dx, y + dy, z + dz)
                        if all(0 <= q[k] < a.shape[k] for k in range(3)) and opaque[q] and not woodish[a[q]]:
                            around[int(a[q])] += 1
                wall = world.NAMES[around.most_common(1)[0][0]] if around else 'minecraft:calcite'
                ylo = cells[:, 1].min()
                for x, y, z in cells:
                    window = (y - ylo) % 4 == 1 and ((z + z0) if axis == 0 else (x + x0)) % 4 == 2
                    st_name = 'minecraft:glass' if window else wall
                    edits[(x + x0, y + 64, z + z0)] = st_name
                    a[x, y, z] = world.gid(st_name)
                    isair[x, y, z] = False
                filled += len(cells)
                stats['castle_openings'] += 1
    stats['castle_wall_cells'] += filled


def castle_roofs(save, x0, x1, z0, z1, edits, stats):
    """Holes in the castle's tiled roofs (the generator skipped columns, e.g. two along the east wing's outer slope):
    in every row along x and along z, a gap of up to three columns between roof on both sides is filled at the height
    between them, as thick as the roof beside it."""
    a, _ = world.load(save, x0, x1, z0, z1, 64, 192)
    for (x, y, z), st in edits.items():
        if x0 <= x < x1 and z0 <= z < z1 and 64 <= y < 192:
            a[x - x0, y - 64, z - z0] = world.gid(st.split('[')[0])
    tile = world.gid('minecraft:deepslate_tiles')
    roofmats = [world.IDS[n] for n in ('minecraft:deepslate_tiles', 'minecraft:deepslate_tile_stairs') if n in world.IDS]
    isroof = np.isin(a, roofmats)
    airid = world.IDS['minecraft:air']
    added = 0
    for axis in (0, 2):
        for j in range(a.shape[2 - axis]):
            sec = isroof[:, :, j] if axis == 0 else isroof[j, :, :]
            has = sec.any(axis=1)
            top = np.where(has, sec.shape[1] - 1 - np.argmax(sec[:, ::-1], axis=1), -1)
            cols = np.nonzero(has)[0]
            for c0, c1 in zip(cols[:-1], cols[1:]):
                gap = c1 - c0 - 1
                if not 1 <= gap <= 3 or abs(int(top[c0]) - int(top[c1])) > gap + 1:
                    continue
                thick = 2 if (sec[c0, top[c0] - 1] and sec[c1, top[c1] - 1]) else 1
                for k in range(1, gap + 1):
                    c = c0 + k
                    yt = int(round(top[c0] + (top[c1] - top[c0]) * k / (gap + 1)))
                    for y in range(yt - thick + 1, yt + 1):
                        q = (c, y, j) if axis == 0 else (j, y, c)
                        if a[q] == airid:
                            a[q] = tile
                            isroof[q] = True
                            edits[(q[0] + x0, q[1] + 64, q[2] + z0)] = 'minecraft:deepslate_tiles'
                            added += 1
    stats['castle_roof_cells'] += added


def runs(cols):
    start = prev = cols[0]
    for c in cols[1:]:
        if c != prev + 1:
            yield start, prev
            start = c
        prev = c
    yield start, prev


def lamps(save):
    """Every lantern and soul lantern in the save: {(x, y, z): (name, hanging)}."""
    import anvil
    found = {}
    for f in sorted(os.listdir(os.path.join(save, 'region'))):
        for lx, lz, nbt in anvil.chunks_typed(os.path.join(save, 'region', f)):
            cx, cz = anvil.val(nbt['xPos']), anvil.val(nbt['zPos'])
            for sec in nbt['sections']:
                bs = sec.get('block_states')
                if not bs or not any(anvil.val(p['Name']) in ('minecraft:lantern', 'minecraft:soul_lantern') for p in bs['palette']):
                    continue
                pal, idx = anvil_edit.decode(bs)
                sy = anvil.val(sec['Y'])
                for i, p in enumerate(pal):
                    n = anvil.val(p['Name'])
                    if n not in ('minecraft:lantern', 'minecraft:soul_lantern'):
                        continue
                    hanging = anvil.val((p.get('Properties') or {}).get('hanging', 'false')) == 'true'
                    for j in np.nonzero(idx == i)[0]:
                        found[(cx * 16 + j % 16, sy * 16 + j // 256, cz * 16 + (j // 16) % 16)] = (n, hanging)
    return found


def fixtures(save, edits, stats):
    """Lanterns the save left hanging in the air: a standing one gets a fence post down to the ground, a hanging one a
    chain up to the ceiling; one more than twelve blocks from either becomes a lamp post on the ground below it."""
    found = lamps(save)
    tiles = collections.defaultdict(list)
    for (x, y, z), v in found.items():
        tiles[(x >> 7, z >> 7)].append(((x, y, z), v))
    fixed = collections.Counter()
    for (tx, tz), items in tiles.items():
        x0, z0 = tx * 128, tz * 128
        a, _ = world.load(save, x0, x0 + 128, z0, z0 + 128, 0, 192)
        air, transparent, emit, plain, soft = tables()
        isair = air[a]
        for (x, y, z), (name, hanging) in items:
            lx, lz = x - x0, z - z0
            if y <= 0 or y >= 191:
                continue
            if hanging and not isair[lx, y + 1, lz] or not hanging and not isair[lx, y - 1, lz]:
                continue
            up = next((k for k in range(1, 13) if y + k < 192 and not isair[lx, y + k, lz]), None)
            down = next((k for k in range(1, 13) if y - k >= 0 and not isair[lx, y - k, lz]), None)
            if hanging and up is not None:
                for k in range(1, up):
                    edits[(x, y + k, z)] = 'minecraft:chain[axis=y,waterlogged=false]'
                fixed['chained'] += 1
            elif down is not None:
                for k in range(1, down):
                    edits[(x, y - k, z)] = 'minecraft:dark_oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]'
                edits[(x, y, z)] = name + '[hanging=false,waterlogged=false]'
                fixed['posted'] += 1
            else:
                g = next((k for k in range(1, y + 1) if not isair[lx, y - k, lz]), None)
                edits[(x, y, z)] = 'minecraft:air'
                if g is not None:
                    base = y - g
                    for k in range(1, 4):
                        edits[(x, base + k, z)] = 'minecraft:dark_oak_fence[east=false,north=false,south=false,waterlogged=false,west=false]'
                    edits[(x, base + 4, z)] = name + '[hanging=false,waterlogged=false]'
                fixed['moved'] += 1
    stats['fixtures'] = dict(fixed)


def debris(save, edits, stats, tile=160):
    """Small groups of blocks (30 or fewer, touching nothing even corner to corner) floating above the ground: ladders
    against nothing, single lights, bars and stones in mid-air, finials hovering over the towers. They go."""
    st = np.ones((3, 3, 3), bool)
    removed = collections.Counter()
    for tx in range(-640, 640, tile):
        for tz in range(-640, 640, tile):
            x0, z0, y0 = tx - 8, tz - 8, 60
            a, _ = world.load(save, x0, tx + tile + 8, z0, tz + tile + 8, y0, 192)
            for (x, y, z), s in edits.items():
                if x0 <= x < tx + tile + 8 and z0 <= z < tz + tile + 8 and y0 <= y < 192:
                    a[x - x0, y - y0, z - z0] = world.gid(s.split('[')[0])
            empty = np.isin(a, [world.IDS.get(n, -1) for n in ('minecraft:air', 'minecraft:cave_air', 'minecraft:light')])
            lab, n = ndimage.label(~empty, structure=st)
            sizes = np.bincount(lab.ravel())
            for i, sl in enumerate(ndimage.find_objects(lab), 1):
                if sizes[i] > 30 or sl[1].start <= 6:
                    continue
                if sl[0].start == 0 or sl[2].start == 0 or sl[0].stop == a.shape[0] or sl[2].stop == a.shape[2]:
                    continue
                if not (8 <= sl[0].start < tile + 8 and 8 <= sl[2].start < tile + 8):
                    continue
                for c in np.argwhere(lab[sl] == i) + [q.start for q in sl]:
                    removed[short(a[tuple(c)])] += 1
                    edits[(int(c[0]) + x0, int(c[1]) + y0, int(c[2]) + z0)] = 'minecraft:air'
    stats['debris_removed'] = sum(removed.values())
    stats['debris'] = dict(removed.most_common(12))


def propagate(L, T, iters=15):
    for _ in range(iters):
        M = L.copy()
        np.maximum(M[1:], L[:-1] - 1, out=M[1:])
        np.maximum(M[:-1], L[1:] - 1, out=M[:-1])
        np.maximum(M[:, 1:], L[:, :-1] - 1, out=M[:, 1:])
        np.maximum(M[:, :-1], L[:, 1:] - 1, out=M[:, :-1])
        np.maximum(M[:, :, 1:], L[:, :, :-1] - 1, out=M[:, :, 1:])
        np.maximum(M[:, :, :-1], L[:, :, 1:] - 1, out=M[:, :, :-1])
        L = np.where(T, M, L)
    return L


def light_area(save, x0, x1, z0, z1, y0, y1, edits, stats, keep=None):
    a, _ = world.load(save, x0, x1, z0, z1, y0, y1)
    for (x, y, z), s in edits.items():
        if x0 <= x < x1 and z0 <= z < z1 and y0 <= y < y1:
            a[x - x0, y - y0, z - z0] = world.gid(s.split('[')[0])
    air, transparent, emit, plain, soft = tables()
    isair = air[a]
    T = transparent[a]
    E = emit[a].astype(np.int16)
    L = propagate(E.copy(), T)
    opaque = ~T
    # roofed: an opaque block within 24 above
    covered = np.zeros_like(isair)
    run = np.full((a.shape[0], a.shape[2]), 999, np.int32)
    for y in range(a.shape[1] - 1, -1, -1):
        run = np.where(opaque[:, y, :], 0, run + 1)
        covered[:, y, :] = run <= 24
    floor = np.zeros_like(isair)
    floor[:, 1:, :] = ~isair[:, :-1, :] & ~soft[a[:, :-1, :]]
    head = np.zeros_like(isair)
    head[:, :-1, :] = isair[:, 1:, :]
    walk = isair & floor & head & covered
    if keep is not None:
        walk &= keep
    xs, ys, zs = np.nonzero(walk & (L < TARGET))
    order = np.lexsort((zs, xs, ys))
    placed = collections.Counter()
    for i in order:
        x, y, z = int(xs[i]), int(ys[i]), int(zs[i])
        if L[x, y, z] >= TARGET:
            continue
        yc = y + 1
        while yc < a.shape[1] and isair[x, yc, z]:
            yc += 1
        if yc >= a.shape[1]:
            continue
        h = yc - y
        if 4 <= h <= 14 and opaque[x, yc, z]:
            # a lantern three blocks above the floor, hung from the ceiling on a chain where the room is tall
            py = min(yc - 1, y + 3)
            for cy in range(py + 1, yc):
                edits[(x + x0, cy + y0, z + z0)] = 'minecraft:chain[axis=y,waterlogged=false]'
                a[x, cy, z] = world.gid('minecraft:chain')
                isair[x, cy, z] = False
            px, pz, s, kind = x, z, 'minecraft:lantern[hanging=true,waterlogged=false]', 'lantern'
        elif plain[a[x, yc, z]] and 2 <= h <= 5:
            px, py, pz, s, kind = x, yc, z, 'minecraft:sea_lantern', 'sea_lantern'
        else:
            px, py, pz, s, kind = x, y + 1, z, 'minecraft:light[level=15,waterlogged=false]', 'light'
        edits[(px + x0, py + y0, pz + z0)] = s
        a[px, py, pz] = world.gid(s.split('[')[0])
        isair[px, py, pz] = False
        if kind == 'sea_lantern':
            T[px, py, pz] = False
        else:
            T[px, py, pz] = True
        E[px, py, pz] = 15
        r = 15
        sx0, sx1 = max(0, px - r), min(a.shape[0], px + r + 1)
        sy0, sy1 = max(0, py - r), min(a.shape[1], py + r + 1)
        sz0, sz1 = max(0, pz - r), min(a.shape[2], pz + r + 1)
        sub = np.maximum(L[sx0:sx1, sy0:sy1, sz0:sz1], E[sx0:sx1, sy0:sy1, sz0:sz1])
        L[sx0:sx1, sy0:sy1, sz0:sz1] = np.maximum(L[sx0:sx1, sy0:sy1, sz0:sz1], propagate(sub, T[sx0:sx1, sy0:sy1, sz0:sz1]))
        placed[kind] += 1
    still = int((walk & (L < TARGET)).sum())
    stats['lights'].update(placed)
    stats['walkable'] += int(walk.sum())
    stats['still_dark'] += still
    return placed


def main(save, out, report=None):
    man = json.load(open(os.path.join(save, 'build_manifest.json')))
    edits, bes = {}, {}
    stats = collections.Counter(houses=0, house_blocks=0, house_blocks_off_plot=0, walkable=0, still_dark=0, castle_roof_cells=0,
                                castle_openings=0, castle_wall_cells=0)
    stats['styles'] = collections.Counter()
    stats['roofs'] = collections.Counter()
    stats['lights'] = collections.Counter()
    stats['stores'] = collections.Counter()
    cleared, town = rebuild_town(save, man, edits, bes, stats)
    print('town', stats['houses'], 'buildings,', stats['house_blocks'], 'blocks', dict(stats['styles']), dict(stats['roofs']), flush=True)
    rest = {}
    fixtures(save, rest, stats)
    print('fixtures', stats['fixtures'], flush=True)
    castle_roofs(save, -100, 100, -100, 100, rest, stats)
    castle_walls(save, -110, 110, -110, 110, rest, stats)
    print('castle', stats['castle_roof_cells'], 'roof cells,', stats['castle_openings'], 'openings,', stats['castle_wall_cells'], 'wall cells', flush=True)
    debris(save, rest, stats)
    print('debris', stats['debris_removed'], stats['debris'], flush=True)
    # the castle's own repairs, except on the town plots (those were about the old houses)
    for p, st in rest.items():
        if (p[0], p[2]) not in cleared:
            edits[p] = st
    # the castle's storerooms and treasury, the vault's hoard
    castle_stores(save, edits, bes, stats)
    vault_hoard(save, man, edits, bes, stats)
    stock_empty(save, cleared, edits, bes, stats)
    print('stores', dict(stats['stores']), 'treasury rooms', stats['treasury_rooms'], flush=True)
    # the castle: the inner ward, in four quarters with an overlap
    for qx0, qx1 in ((-136, 0), (0, 136)):
        for qz0, qz1 in ((-136, 0), (0, 136)):
            light_area(save, qx0 - 16, qx1 + 16, qz0 - 16, qz1 + 16, 64, 192, edits, stats)
            print('lit quarter', qx0, qz0, dict(stats['lights']), flush=True)
    n = anvil_edit.apply(save, out, edits, bes)
    json.dump(dict(note='The town buildings as rebuilt by tools/citadel/houses.py: plot, front, style and the free floor cells '
                        '(feet positions) where townsfolk can stand.', buildings=town),
              open(os.path.join(out, 'TOWN_BUILDINGS.json'), 'w'), separators=(',', ':'))
    stats['chunks_written'] = n
    stats['edits'] = len(edits)
    stats['block_entities'] = len(bes)
    rep = {k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in stats.items()}
    print(json.dumps(rep, ensure_ascii=False))
    if report:
        json.dump(rep, open(report, 'w'), indent=1, ensure_ascii=False)


if __name__ == '__main__':
    main(*sys.argv[1:4])

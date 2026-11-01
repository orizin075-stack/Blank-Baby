"""repair.py <save in> <save out> [report.json]: the Grand Citadel v12 save, repaired and lit.

Town: the 112 town buildings were 17 to 25 blocks wide, up to four storeys, roofed with a single diagonal line of
blocks per slope and nearly empty inside. Each is cleared from its plot and rebuilt by houses.py: smaller (7 to 13
wide), in ten styles with gable or hipped roofs, furnished for its trade, lit, with a yard; TOWN_BUILDINGS.json in the
repaired save lists what was built and where the townsfolk can stand (tools/citadel/garrison.py reads it).
Every chunk becomes the Royal Capital biome (oror_supreme_bosses:royal_capital). The castle's rooms get storerooms, the
undercroft under the throne the royal treasury, the forbidden vault its hoard (loot.py); the outer belt gets airbases,
helipads and tank hangars, the walls and gates turret posts (military.py, MILITARY.json in the repaired save).
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
import world, anvil_edit, loot, military
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


OPPOSITE = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}


def subplots(plot, front, ext):
    """A plot cut for several buildings: two or three side by side along the street (by its width), and as many again
    facing the road behind when there is one and the plot is deep enough. Returns [(sub-plot, front, max width)]."""
    x0, z0, x1, z1 = plot
    across_x = front in ('north', 'south')            # the street runs along x
    width = (x1 - x0 + 1) if across_x else (z1 - z0 + 1)
    depth = (z1 - z0 + 1) if across_x else (x1 - x0 + 1)
    n = 1 if width < 26 else 2 if width < 40 else 3
    back = ext[OPPOSITE[front]][1] == 'road' and depth >= 28
    rows = [(front, 0, depth // 2 if back else depth)]
    if back:
        rows.append((OPPOSITE[front], depth // 2, depth - depth // 2))
    out = []
    for face, off, d in rows:
        for i in range(n):
            a0 = i * width // n
            a1 = (i + 1) * width // n - 1
            # the row's band along the depth: the street row is at the front side of the plot
            if across_x:
                zs = (z1 - off - d + 1, z1 - off) if front == 'south' else (z0 + off, z0 + off + d - 1)
                if face != front:
                    zs = (z0, z0 + d - 1) if front == 'south' else (z1 - d + 1, z1)
                sub = (x0 + a0, zs[0], x0 + a1, zs[1])
            else:
                xs = (x1 - off - d + 1, x1 - off) if front == 'east' else (x0 + off, x0 + off + d - 1)
                if face != front:
                    xs = (x0, x0 + d - 1) if front == 'east' else (x1 - d + 1, x1)
                sub = (xs[0], z0 + a0, xs[1], z0 + a1)
            out.append((sub, face, (a1 - a0 + 1) - 4))
    return out


def rebuild_town(save, man, edits, bes, stats):
    """The town buildings rebuilt by houses.py on their plots: everything above the ground of the plot cleared (only on
    the plot's grass and the old footprint, never a road, the moat or a field), then the plot cut into two to six
    sub-plots (subplots), the old building's trade on the first and homes and the town's facilities (chapels, schools,
    clinics, warehouses, bathhouses, guardhouses, mills, florists, more bakers, tailors and taverns) on the others, each a
    house with its yard. Returns the cleared columns and, per building, what was built and where its townsfolk stand."""
    import houses
    H = man['individual_town_architecture']
    cleared, town = set(), []
    turn = 0
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
        for (x, z) in writable:
            col = a[x - x0, :, z - z0]
            for yy in np.nonzero(col[1:])[0] + 1:
                edits[(x, int(yy) + 64, z)] = 'minecraft:air'
            edits[(x, 64, z)] = 'minecraft:grass_block'
        cleared |= writable
        subs = subplots(plot, front, ext)
        for k, (sub, face, max_w) in enumerate(subs):
            if k == 0:
                kind = h['kind']
            else:
                # every third extra building a facility, in turn, the others homes
                turn += 1
                kind = houses.FACILITIES[(turn // 3) % len(houses.FACILITIES)] if turn % 3 == 0 else 'house'
            seed = 7919 * h['id'] + 17 + 104729 * k
            blocked = {(x, z) for x in range(sub[0], sub[2] + 1) for z in range(sub[1], sub[3] + 1) if (x, z) not in writable}
            house = houses.build(sub, kind, seed, face, max_w=max(7, max_w), fence_sides='all' if len(subs) == 1 else 'front',
                                 blocked=blocked)
            lost = 0
            for (x, y, z), st in house.blocks.items():
                if (x, z) in writable:
                    edits[(x, y, z)] = st
                else:
                    lost += 1
            for p, be in houses.entities(house, h['id'] * 8 + k).items():
                if (p[0], p[2]) in writable:
                    bes[p] = be
            stats['houses'] += 1
            stats['kinds'][kind] += 1
            stats['house_blocks'] += len(house.blocks) - lost
            stats['house_blocks_off_plot'] += lost
            stats['houses_on_paving'] += any(0 <= u < house.W and 0 <= v < house.D for u, v in map(lambda c: house.local(*c), blocked))
            stats['styles'][house.style] += 1
            stats['roofs'][house.roof_kind] += 1
            cx, cz = (sub[0] + sub[2]) // 2, (sub[1] + sub[3]) // 2
            town.append(dict(id=h['id'] * 8 + k, plot_of=h['id'], kind=kind, x=cx, z=cz, front=face, plot=list(sub), style=house.style,
                             station=house.station, width=house.W, depth=house.D, floors=house.floors, roof=house.roof_kind,
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


STORE_NAMES = {'armory': '武器庫', 'pantry': '食料庫', 'keep': '城の倉', 'royal': '王家の蔵', 'treasury': '王家の宝物庫', 'vault': '王家の禁庫', 'vault_arms': '王家の禁庫・禁断の武具'}


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
                     lambda *a: 'treasury', budget=12, name=lambda t: STORE_NAMES[t], pick_rooms=nearest, spacing=2)
    stats['treasury_at'] = [list(t[:3]) for t in trs]
    stats['treasury_rooms'] = len({(x, z) for x, y, z, t in trs})
    return placed


def vault_hoard(save, man, edits, bes, stats):
    """The forbidden vault (v9_true_treasury, deep under the town): its four pedestal chests hold the kingdom's hoard,
    and its chamber gets more along the walls."""
    vx, vz = man['v9_true_treasury']
    _, found = world.load(save, vx - 3, vx + 4, vz - 3, vz + 4, 0, 30)
    n = 0
    for be in sorted(found, key=lambda b: (b['x'], b['z'], b['y'])):
        if be['id'].endswith('chest'):
            x, y, z = be['x'], be['y'], be['z']
            # the first two pedestals keep the forbidden arms, the others the hoard
            theme = 'vault_arms' if n < 2 else 'vault'
            bes[(x, y, z)] = {'id': 'minecraft:chest', 'x': x, 'y': y, 'z': z, 'CustomName': json.dumps({'text': STORE_NAMES[theme]}, ensure_ascii=False),
                              'Items': loot.items(theme, x * 31 + z * 17 + y)}
            n += 1
            stats['stores']['vault'] += 1
    placed = [(x, y, z) for (x, y, z) in bes if abs(x - vx) <= 3 and abs(z - vz) <= 3]
    storerooms(save, vx - 12, vx + 13, vz - 6, vz + 7, 2, 20, edits, bes, stats, placed, lambda *a: 'vault', budget=10,
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


def castle_cover(save, edits, stats, x0=-60, x1=60, z0=-40, z1=50):
    """The palace's two light wells (x -43 to -17 and 16 to 43, z -16 to 31) were left without a roof by the generator:
    from above, two great holes in the castle's roof with the top floor's rooms, galleries and a stairwell open to the
    sky (048, reported broken). Each is roofed in the castle's deepslate tiles, hipped from two blocks above the
    highest thing inside, one block up a block, flat on top eight up with a ridge of glass to light the rooms below;
    where a wall round it is lower than the roof's edge it is built up in quartz bricks to meet it."""
    a, _ = world.load(save, x0, x1, z0, z1, 64, 192)
    for (x, y, z), st in edits.items():
        if x0 <= x < x1 and z0 <= z < z1 and 64 <= y < 192:
            a[x - x0, y - 64, z - z0] = world.gid(st.split('[')[0])
    names = world.NAMES
    air = np.array([n in ('minecraft:air', 'minecraft:cave_air', 'minecraft:light') for n in names] + [False] * 64)
    solid = ~air[a]
    top = np.where(solid.any(axis=1), solid.shape[1] - 1 - np.argmax(solid[:, ::-1, :], axis=1), 0) + 64
    roofmats = [world.IDS[n] for n in ('minecraft:deepslate_tiles', 'minecraft:deepslate_tile_stairs') if n in world.IDS]
    hasroof = np.isin(a, roofmats).any(axis=1)
    xs, zs = np.arange(x0, x1), np.arange(z0, z1)
    zone = (np.abs(xs)[:, None] <= 43) & (zs[None, :] >= -17) & (zs[None, :] <= 33)
    hole = zone & ~hasroof & (top < 140) & (top > 70)
    lab, n = ndimage.label(hole)
    stair = 'minecraft:deepslate_tile_stairs[facing=%s,half=bottom,shape=straight,waterlogged=false]'
    steps = (('east', 1, 0), ('west', -1, 0), ('south', 0, 1), ('north', 0, -1))
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() < 300:
            continue
        base = int(top[m].max()) + 2
        dist = ndimage.distance_transform_cdt(np.pad(m, 1), metric='chessboard')[1:-1, 1:-1]
        xs_, zs_ = np.nonzero(m)
        long_x = xs_.max() - xs_.min() >= zs_.max() - zs_.min()
        mid = (zs_.min() + zs_.max()) // 2 if long_x else (xs_.min() + xs_.max()) // 2
        for ci, ck in zip(xs_, zs_):
            d = int(dist[ci, ck])
            h = base + min(d - 1, 8)
            x, z = int(ci) + x0, int(ck) + z0
            if d - 1 < 8:
                face = 'north'
                for f, dx, dz in steps:
                    ni, nk = ci + dx, ck + dz
                    if 0 <= ni < m.shape[0] and 0 <= nk < m.shape[1] and m[ni, nk] and dist[ni, nk] > d:
                        face = f
                        break
                edits[(x, h, z)] = stair % face
                if h - 1 >= base:
                    edits[(x, h - 1, z)] = 'minecraft:deepslate_tiles'
            else:
                ridge = (ck if long_x else ci) in (mid, mid + 1)
                edits[(x, h, z)] = 'minecraft:glass' if ridge else 'minecraft:deepslate_tiles'
            stats['castle_cover_cells'] += 1
        # the walls round it built up to the roof's edge where they are lower
        ring = ndimage.binary_dilation(m) & ~m & ~hasroof
        for ci, ck in zip(*np.nonzero(ring)):
            for y in range(int(top[ci, ck]) + 1, base + 1):
                edits[(int(ci) + x0, y, int(ck) + z0)] = 'minecraft:quartz_bricks'
                stats['castle_cover_walls'] += 1
        stats['castle_covered'] += 1


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


def strays(save, edits, stats, r=136):
    """Single blocks left hanging in the castle with nothing on any of their six sides (048's audit: three-block
    chevrons of dark prismarine over both gates of the inner ward, a sea lantern and roof tiles beside the roof walk's
    corners) are taken away; a spiral stair's steps (touching only at their corners), lanterns, chains, candles and
    the like are left."""
    a, _ = world.load(save, -r, r, -r, r, 64, 192)
    for (x, y, z), st in edits.items():
        if -r <= x < r and -r <= z < r and 64 <= y < 192:
            a[x + r, y - 64, z + r] = world.gid(st.split('[')[0])
    names = world.NAMES
    keep = ('stairs', 'lantern', 'chain', 'torch', 'candle', 'end_rod', 'light', 'bell', 'banner', 'button', 'sign', 'flower_pot', 'skull',
            'head', 'rod', 'lever', 'bars', 'pane', 'fence', 'wall', 'vine', 'ladder')
    solid = np.array([n not in ('minecraft:air', 'minecraft:cave_air') for n in names] + [False] * 64)[a]
    p = np.pad(solid, 1)
    nb = np.zeros(p.shape, np.int8)
    for ax in (0, 1, 2):
        for sh in (1, -1):
            nb += np.roll(p, sh, axis=ax)
    lone = (p & (nb == 0))[1:-1, 1:-1, 1:-1]
    for i, j, k in np.argwhere(lone):
        n = names[a[i, j, k]]
        if j > 0 and not any(t in n for t in keep):
            edits[(int(i) - r, int(j) + 64, int(k) - r)] = 'minecraft:air'
            stats['castle_strays'] += 1


def fountains(save, edits, stats):
    """Water standing above the kingdom's ground with nothing to hold it (049's audit: the round fountains in the middle
    of the four high roads, the plaza basins, ponds in the fields and some baths, 872 edges in all, had their water on
    a plinth with no rim, and in the game it ran out over the streets): every open side of such water gets a rim of the
    basin's own stone, open bottoms a floor; a fountain's top left hanging over its pool (nothing under it but water and
    no part of it on the rim or the bank) stands on a pillar of its own stone."""
    from scipy import ndimage
    for x0, x1, z0, z1, y0, y1 in ((-640, 640, -640, 640, 64, 100), (-140, 140, -140, 140, 96, 192)):
        a, _ = world.load(save, x0, x1, z0, z1, y0, y1)
        for (x, y, z), st in edits.items():
            if x0 <= x < x1 and z0 <= z < z1 and y0 <= y < y1:
                a[x - x0, y - y0, z - z0] = world.gid(st.split('[')[0])
        names = world.NAMES + [''] * 64
        W = world.gid('minecraft:water')
        isair = np.array([n in ('minecraft:air', 'minecraft:cave_air') for n in names])
        soft = np.array([n == '' or isair[i] or n == 'minecraft:water' or any(t in n for t in ('grass', 'fern', 'flower', 'leaves', 'vine', 'torch',
                         'lantern', 'carpet', 'slab', 'stairs', 'pane', 'bars', 'fence', 'wall', 'sign', 'banner', 'button', 'chain', 'candle'))
                         for i, n in enumerate(names)])
        water = a == W
        air = isair[a]
        lo = 1 if y0 == 64 else 0                      # y 64 is the ground's own level: moats, field ditches, ponds
        floor_of = {}

        def floor(i, j, k):
            # the basin's stone under a water column
            key = (i, k)
            if key not in floor_of:
                jj = j
                while jj > 0 and a[i, jj, k] == W:
                    jj -= 1
                n = names[a[i, jj, k]]
                floor_of[key] = n if not soft[a[i, jj, k]] and n.startswith('minecraft:') else 'minecraft:stone_bricks'
            return floor_of[key]
        # the floating tops first (they are taken out of the water before the rims are drawn)
        for j in range(max(lo, 1) + 1, a.shape[1]):
            top = ~soft[a[:, j, :]] & ~air[:, j, :]
            over = top & water[:, j - 1, :]
            lab, n = ndimage.label(over)
            if not n:
                continue
            # a part of the top resting on anything but water (the rim, the bank, a bridge's abutment) holds it up
            held = top & ~water[:, j - 1, :]
            near_held = ndimage.binary_dilation(held) & over
            keep = set(np.unique(lab[near_held])) - {0}
            for c in range(1, n + 1):
                if c in keep:
                    continue
                cells = np.argwhere(lab == c)
                if len(cells) > 64:
                    continue
                if len(cells) <= 2:
                    # a block or two adrift over a pool (a bookshelf over the inner court's) is no fountain's top: taken away
                    for i, k in cells:
                        edits[(int(i) + x0, j + y0, int(k) + z0)] = 'minecraft:air'
                        a[i, j, k] = world.gid('minecraft:air')
                        stats['fountain_loose'] += 1
                    continue
                for i, k in cells:
                    st = names[a[i, j, k]]
                    jj = j - 1
                    while jj >= lo and a[i, jj, k] == W:
                        edits[(int(i) + x0, jj + y0, int(k) + z0)] = st
                        a[i, jj, k] = a[i, j, k]
                        water[i, jj, k] = False
                        jj -= 1
                    stats['fountain_pillars'] += 1
        for j in range(lo, a.shape[1]):
            wl = water[:, j, :]
            if not wl.any():
                continue
            for di, dk in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                src = np.argwhere(wl & np.roll(air[:, j, :], (-di, -dk), axis=(0, 1)))
                for i, k in src:
                    ni, nk = i + di, k + dk
                    if not (0 <= ni < a.shape[0] and 0 <= nk < a.shape[2]) or not air[ni, j, nk]:
                        continue
                    st = floor(i, j, k)
                    edits[(int(ni) + x0, j + y0, int(nk) + z0)] = st
                    a[ni, j, nk] = world.gid(st)
                    air[ni, j, nk] = False
                    stats['fountain_rims'] += 1
            if j > lo or y0 > 64:
                for i, k in np.argwhere(wl & air[:, j - 1, :]) if j > 0 else []:
                    st = floor(i, j, k)
                    edits[(int(i) + x0, j - 1 + y0, int(k) + z0)] = st
                    a[i, j - 1, k] = world.gid(st)
                    air[i, j - 1, k] = False
                    stats['fountain_floors'] += 1


def detached(save, edits, stats, posts=()):
    """Blocks with nothing under or beside them all the way to the ground (049's audit, by 26-connected parts of the
    whole kingdom, water and the light blocks aside): the generator built the buttresses of the walls a block above the
    ground, set the roofs of the four outer fortresses' halls a block above and outside their walls, put platforms a
    block off the outer wall, left the crowns of trees whose trunks it had cut hanging over the fields and the moats and
    a roof's ridge over the castle's south court. A part a block or two off the ground is set down on it (the gap under
    it filled with its own block); one within two blocks of a standing structure is joined to it (the cells between
    filled with that structure's block: a roof gets its wall plate); a tree's crown or a clod of earth wherever it hangs
    is taken away, and so is what can be neither set down nor joined; in the castle's ward only the large parts are
    touched, its small ones (lights, fittings) are left as they are. A part that a post stands on (the batteries'
    platforms off the outer wall) is never taken away: it is held up on a pier of its own block to the ground."""
    from scipy import ndimage
    x0, x1, z0, z1, y0, y1 = -640, 640, -640, 640, 63, 200
    a, _ = world.load(save, x0, x1, z0, z1, y0, y1)
    for (x, y, z), st in edits.items():
        if x0 <= x < x1 and z0 <= z < z1 and y0 <= y < y1:
            a[x - x0, y - y0, z - z0] = world.gid(st.split('[')[0])
    names = world.NAMES + [''] * 64
    empty = np.array([n in ('minecraft:air', 'minecraft:cave_air', 'minecraft:light', '') for n in names])
    natural_kind = np.array([any(t in n for t in ('leaves', '_log', 'dirt', 'grass_block', 'podzol', 'moss', 'vine', '_wood'))
                             for n in names])
    full = np.array([not any(t in n for t in ('stairs', 'slab', 'wall', 'fence', 'pane', 'bars', 'chain', 'lantern', 'torch', 'door',
                                                'trapdoor', 'button', 'sign', 'banner', 'carpet', 'chest', 'barrel', 'candle', 'rod',
                                                'leaves', 'water', 'lava'))
                     and n != '' for n in names])
    solid = ~empty[a]
    lab, n = ndimage.label(solid, structure=np.ones((3, 3, 3), bool))
    grounded = np.zeros(n + 1, bool)
    grounded[np.unique(lab[:, 0, :])] = True
    grounded[0] = False
    objs = ndimage.find_objects(lab)
    ball = np.ones((3, 3, 3), bool)

    def put(cx, cy, cz, st):
        edits[(int(cx) + x0, int(cy) + y0, int(cz) + z0)] = st
        a[cx, cy, cz] = world.gid(st)

    floors = {(p['x'] - x0, p['y'] - 1 - y0, p['z'] - z0) for p in posts}

    for i in range(1, n + 1):
        if grounded[i] or objs[i - 1] is None:
            continue
        sl = objs[i - 1]
        m = lab[sl] == i
        cells = np.argwhere(m) + [sl[0].start, sl[1].start, sl[2].start]
        ids = a[cells[:, 0], cells[:, 1], cells[:, 2]]
        size = len(cells)
        ring = max(abs(int(cells[:, 0].mean()) + x0), abs(int(cells[:, 2].mean()) + z0))
        low = cells[:, 1].min()
        gap = 99
        for cx, cy, cz in cells[cells[:, 1] == low][:64]:
            g, yy = 0, cy - 1
            while yy >= 0 and empty[a[cx, yy, cz]]:
                g, yy = g + 1, yy - 1
            gap = min(gap, g)
        natural = natural_kind[ids].mean() > 0.6
        castle = ring <= 140
        if castle and size < (100 if gap <= 2 else 30) and not natural:
            continue
        fulls = [k for k in ids if full[k]]
        base = names[np.bincount(fulls).argmax()] if fulls else 'minecraft:stone_bricks'
        if natural:
            for cx, cy, cz in cells:
                put(cx, cy, cz, 'minecraft:air')
            stats['detached_removed'] += 1
            stats['detached_removed_blocks'] += size
            continue
        if gap <= 2:
            # set down: under each cell with open air below, its own block (a full one: the part's commonest) to the ground
            for cx, cy, cz in cells:
                if cy == 0 or not empty[a[cx, cy - 1, cz]]:
                    continue
                st = names[a[cx, cy, cz]] if full[a[cx, cy, cz]] else base
                yy = cy - 1
                while yy >= 0 and empty[a[cx, yy, cz]] and cy - yy <= 3:
                    put(cx, yy, cz, st)
                    stats['detached_filled'] += 1
                    yy -= 1
            stats['detached_set_down'] += 1
            continue
        # joined: the open cells next to the part (one step, then two) that touch a standing structure are filled with
        # that structure's block
        pad = 3
        lo = np.maximum([q.start - pad for q in sl], 0)
        hi = np.minimum([q.stop + pad for q in sl], a.shape)
        box = tuple(slice(lo[k], hi[k]) for k in range(3))
        mine = lab[box] == i
        stand = grounded[lab[box]]
        openb = empty[a[box]]
        near_stand = ndimage.binary_dilation(stand, ball)
        joined = 0
        reach = mine
        for step in (1, 2):
            reach = ndimage.binary_dilation(reach, ball) & (openb | mine)
            touch = reach & openb & near_stand
            if touch.any():
                for q in np.argwhere(touch):
                    cx, cy, cz = q + lo
                    # the structure's block beside it
                    st = None
                    for dx, dy, dz in ((0, -1, 0), (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0)):
                        k = (cx + dx, cy + dy, cz + dz)
                        if all(0 <= k[t] < a.shape[t] for t in range(3)) and grounded[lab[k]] and full[a[k]]:
                            st = names[a[k]]
                            break
                    put(cx, cy, cz, st or base)
                    joined += 1
                if step == 2:
                    # the cells of the first ring between them too
                    first = ndimage.binary_dilation(mine, ball) & openb & ndimage.binary_dilation(touch, ball)
                    for q in np.argwhere(first):
                        cx, cy, cz = q + lo
                        if empty[a[cx, cy, cz]]:
                            put(cx, cy, cz, base)
                            joined += 1
                break
        if joined and joined <= max(8, size):
            stats['detached_joined'] += 1
            stats['detached_join_blocks'] += joined
            continue
        if any((int(cx), int(cy), int(cz)) in floors for cx, cy, cz in cells):
            # a post's floor: a pier under it, down to the ground
            for cx, cy, cz in cells:
                if cy == 0 or not empty[a[cx, cy - 1, cz]]:
                    continue
                yy = cy - 1
                while yy >= 0 and empty[a[cx, yy, cz]]:
                    put(cx, yy, cz, base)
                    yy -= 1
            stats['detached_piers'] += 1
            continue
        for cx, cy, cz in cells:
            put(cx, cy, cz, 'minecraft:air')
        stats['detached_removed'] += 1
        stats['detached_removed_blocks'] += size


def gables(save, edits, stats, skip):
    """The open ends of roofs outside the town and the castle (049, the user's report: the ranches' barns stood with
    the triangles under their gables open, the barns hollow to the sky at both ends; so did the outer fortresses' halls):
    where an opening four or more blocks above the ground leads in under a roof (opaque cover within 24 blocks above;
    leaves are no roof) to a room at least three blocks deep, and is a gable's triangle standing on the top of its end
    wall, it is walled with the commonest block around it. The gate passages and the open galleries (open to the
    ground or to their floor, square) stay as they are; not on the town's plots or the military sites (skip)."""
    x0, x1, z0, z1 = -640, 640, -640, 640
    a, _ = world.load(save, x0, x1, z0, z1, 64, 160)
    for (x, y, z), st in edits.items():
        if x0 <= x < x1 and z0 <= z < z1 and 64 <= y < 160:
            a[x - x0, y - 64, z - z0] = world.gid(st.split('[')[0])
    names = world.NAMES + [''] * 64
    air, transparent, emit, plain, soft = tables()
    air = np.concatenate([air, np.ones(64, bool)])[:len(names)]
    leafy = np.array([('leaves' in n or 'log' in n or 'wool' in n or 'carpet' in n) for n in names])
    opaque = ~np.concatenate([transparent, np.ones(64, bool)])[:len(names)][a] & ~leafy[a]
    isair = air[a]
    covered = np.zeros_like(isair)
    run = np.full((a.shape[0], a.shape[2]), 999, np.int32)
    for y in range(a.shape[1] - 1, -1, -1):
        run = np.where(opaque[:, y, :], 0, run + 1)
        covered[:, y, :] = run <= 24
    inner = isair & covered
    outside = isair & ~covered
    xs = np.abs(np.arange(x0, x1))
    ring = np.maximum(xs[:, None], np.abs(np.arange(z0, z1))[None, :])
    allowed = (ring > 292) & ~skip
    count = 0
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
            face = inner & nb
            face[:, :5, :] = False                               # four or more above the ground (y 69 up)
            face &= allowed[:, None, :]
            # three or more covered open cells inward
            deep = face.copy()
            for k in (1, 2, 3):
                sh = np.zeros_like(inner)
                s2 = [slice(None)] * 3
                d2 = [slice(None)] * 3
                if sign > 0:
                    d2[axis], s2[axis] = slice(k, None), slice(None, -k)
                else:
                    d2[axis], s2[axis] = slice(None, -k), slice(k, None)
                sh[tuple(d2)] = inner[tuple(s2)]
                deep &= sh
            # an opening of ten cells or more (a gable's triangle; not an arrow slit or a window)
            st3 = np.zeros((3, 3, 3), bool)
            st3[1, 1, 1] = st3[1, 0, 1] = st3[1, 2, 1] = True
            if axis == 0:
                st3[1, 1, 0] = st3[1, 1, 2] = True
            else:
                st3[0, 1, 1] = st3[2, 1, 1] = True
            lab, nl = ndimage.label(deep, structure=st3)
            keep = np.zeros(nl + 1, bool)
            for c, sl in enumerate(ndimage.find_objects(lab), 1):
                if sl is None:
                    continue
                cells = np.argwhere(lab[sl] == c) + [q.start for q in sl]
                if len(cells) < 10:
                    continue
                # a gable: a triangle (each row narrower toward the top) standing on the end wall's top, not a gate
                # passage or an open gallery (open down to the ground or the floor, square)
                ys = cells[:, 1]
                rows = sorted(set(ys.tolist()))
                if len(rows) < 3:
                    continue
                width = {y: len(cells[ys == y]) for y in rows}
                if width[rows[-1]] > 0.6 * width[rows[0]]:
                    continue
                bottom = cells[ys == rows[0]]
                if rows[0] == 0 or np.mean([not isair[x, y - 1, z] for x, y, z in bottom]) < 0.6:
                    continue
                keep[c] = True
            deep = keep[lab]
            for x, y, z in np.argwhere(deep):
                around = collections.Counter()
                for dx, dy, dz in ((0, -1, 0), (0, 1, 0), (1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, -2, 0)):
                    q = (x + dx, y + dy, z + dz)
                    if all(0 <= q[k] < a.shape[k] for k in range(3)) and opaque[q] and not leafy[a[q]]:
                        around[int(a[q])] += 1
                if not around:
                    continue
                st = names[around.most_common(1)[0][0]].split('[')[0]
                edits[(int(x) + x0, int(y) + 64, int(z) + z0)] = st
                a[x, y, z] = world.gid(st)
                count += 1
    stats['gable_cells'] = count


def ranch_barns(save, man, edits, bes, stats, cleared=frozenset()):
    """The eight ranches' barns are built anew as stables (049, the user's report: the generator's barns stood with their
    gables open and the middle of their roofs missing, hollow to the sky). The old barn's ground is cleared (its tall
    columns and a block round them) and a stable of the town's builder stands on it, its front toward the castle; the
    ranch's fences, pens and animals stay."""
    import houses
    for k, r in enumerate(man.get('ranches', [])):
        cx, cz = r['x'], r['z']
        x0, z0 = cx - 34, cz - 34
        a, _ = world.load(save, x0, cx + 35, z0, cz + 35, 64, 120)
        names = world.NAMES
        built = np.array([not (n.endswith(('air', '_leaves', '_log')) or n == 'minecraft:light') for n in names])
        tall = built[a[:, 6:, :]].any(axis=1)
        # the town's rebuilt plots beside a ranch are no part of its barn (049's audit: three houses were cut into)
        town = np.zeros_like(tall)
        for (x, z) in cleared:
            if x0 <= x < x0 + a.shape[0] and z0 <= z < z0 + a.shape[2]:
                town[x - x0, z - z0] = True
        tall &= ~town
        if not tall.any():
            continue
        from scipy import ndimage as nd
        lab, n = nd.label(tall)
        sizes = nd.sum_labels(tall, lab, index=range(1, n + 1))
        big = 1 + int(np.argmax(sizes))
        xs, zs = np.nonzero(lab == big)
        bx0, bx1, bz0, bz1 = xs.min() - 1, xs.max() + 1, zs.min() - 1, zs.max() + 1
        # everything of the barn: the columns of its footprint, up from the floor
        for i in range(max(0, bx0), min(a.shape[0], bx1 + 1)):
            for j in range(max(0, bz0), min(a.shape[2], bz1 + 1)):
                if town[i, j]:
                    continue
                col = a[i, :, j]
                for yy in np.nonzero(col[1:])[0] + 1:
                    if names[col[yy]] != 'minecraft:air':
                        edits[(int(i) + x0, int(yy) + 64, int(j) + z0)] = 'minecraft:air'
                edits[(int(i) + x0, 64, int(j) + z0)] = 'minecraft:grass_block'
        plot = (int(bx0) + x0, int(bz0) + z0, int(bx1) + x0, int(bz1) + z0)
        front = ('west' if cx > 0 else 'east') if abs(cx) > abs(cz) else ('north' if cz > 0 else 'south')
        blocked = {(x, z) for x in range(plot[0], plot[2] + 1) for z in range(plot[1], plot[3] + 1) if (x, z) in cleared}
        house = houses.build(plot, 'stable', 104723 * (k + 1) + 31, front, fence_sides='front', blocked=blocked)
        inside = lambda x, z: plot[0] <= x <= plot[2] and plot[1] <= z <= plot[3] and (x, z) not in cleared
        for (x, y, z), st in house.blocks.items():
            if inside(x, z):
                edits[(x, y, z)] = st
        for q, be in houses.entities(house, 9000 + k).items():
            if inside(q[0], q[2]):
                bes[q] = be
        stats['ranch_barns'] += 1


def gable_ends(save, edits, stats, regions, roof='minecraft:dark_prismarine', wall='minecraft:stone_bricks', ymin=86):
    """The open ends of the outer fortresses' halls (049, the user's report: their roofs' gables open to the sky): in the
    end planes of each roof (its ridge along its longer side), the cells between its two slopes are walled."""
    from scipy import ndimage as nd
    rid = world.gid(roof)
    for x0, z0, x1, z1 in regions:
        a, _ = world.load(save, x0, x1, z0, z1, 64, 140)
        for (x, y, z), st in edits.items():
            if x0 <= x < x1 and z0 <= z < z1 and 64 <= y < 140:
                a[x - x0, y - 64, z - z0] = world.gid(st.split('[')[0])
        m = a == rid
        m[:, :ymin - 64, :] = False
        lab, n = nd.label(m, structure=np.ones((3, 3, 3), bool))
        for i, sl in enumerate(nd.find_objects(lab), 1):
            if sl is None:
                continue
            cells = np.argwhere(lab[sl] == i) + [q.start for q in sl]
            if len(cells) < 60:
                continue
            ex, ez = np.ptp(cells[:, 0]), np.ptp(cells[:, 2])
            ax, ac = (0, 2) if ex >= ez else (2, 0)      # ridge axis, across axis
            for end in (cells[:, ax].min(), cells[:, ax].max()):
                plane = cells[cells[:, ax] == end]
                if not len(plane):
                    continue
                for y in sorted(set(plane[:, 1].tolist())):
                    row = plane[plane[:, 1] == y][:, ac]
                    lo, hi = row.min(), row.max()
                    for v in range(lo + 1, hi):
                        q = [0, 0, 0]
                        q[ax], q[1], q[ac] = end, y, v
                        if a[q[0], q[1], q[2]] == world.IDS.get('minecraft:air', -1):
                            edits[(int(q[0]) + x0, int(q[1]) + 64, int(q[2]) + z0)] = wall
                            stats['gable_end_cells'] += 1


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
    stats['kinds'] = collections.Counter()
    stats['roofs'] = collections.Counter()
    stats['lights'] = collections.Counter()
    stats['stores'] = collections.Counter()
    cleared, town = rebuild_town(save, man, edits, bes, stats)
    print('town', stats['houses'], 'buildings,', stats['house_blocks'], 'blocks', dict(stats['styles']), dict(stats['roofs']), flush=True)
    rest = {}
    fixtures(save, rest, stats)
    print('fixtures', stats['fixtures'], flush=True)
    castle_cover(save, rest, stats)
    print('castle cover', stats['castle_covered'], 'wells,', stats['castle_cover_cells'], 'roof cells,', stats['castle_cover_walls'], 'wall cells',
          flush=True)
    castle_roofs(save, -100, 100, -100, 100, rest, stats)
    castle_walls(save, -110, 110, -110, 110, rest, stats)
    print('castle', stats['castle_roof_cells'], 'roof cells,', stats['castle_openings'], 'openings,', stats['castle_wall_cells'], 'wall cells', flush=True)
    debris(save, rest, stats)
    strays(save, rest, stats)
    print('strays', stats['castle_strays'], flush=True)
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
    # the ranches' barns built anew (before the military sites, which keep off what is built)
    ranch_barns(save, man, edits, bes, stats, cleared)
    print('ranch barns', stats['ranch_barns'], flush=True)
    # the kingdom's airbases, helipads, hangars and turret posts
    forces = military.build(save, man, edits, bes, stats, town)
    print('military', dict(stats['military']), 'missing', stats['military_missing'], flush=True)
    fountains(save, edits, stats)
    detached(save, edits, stats, forces)
    print('detached', stats['detached_set_down'], 'set down (', stats['detached_filled'], 'blocks ),', stats['detached_joined'], 'joined (',
          stats['detached_join_blocks'], 'blocks ),', stats['detached_piers'], 'held up on piers,', stats['detached_removed'], 'taken away (',
          stats['detached_removed_blocks'], 'blocks )', flush=True)
    skip = np.zeros((1280, 1280), bool)
    for x, z in cleared:
        if -640 <= x < 640 and -640 <= z < 640:
            skip[x + 640, z + 640] = True
    for x0, z0, w, d in stats['military_at'].values():
        skip[max(0, x0 + 630):x0 + 650 + w, max(0, z0 + 630):z0 + 650 + d] = True
    gables(save, edits, stats, skip)
    print('gables', stats['gable_cells'], 'cells walled', flush=True)
    gable_ends(save, edits, stats, [(f['x'] - 50, f['z'] - 50, f['x'] + 50, f['z'] + 50) for f in man.get('exterior_fortresses', [])])
    print('fortress gable ends', stats['gable_end_cells'], 'cells', flush=True)
    print('fountains', stats['fountain_rims'], 'rim blocks,', stats['fountain_floors'], 'floor blocks,', stats['fountain_pillars'], 'pillar cells,',
          stats['fountain_loose'], 'loose blocks', flush=True)
    # the castle: the inner ward, in four quarters with an overlap
    for qx0, qx1 in ((-136, 0), (0, 136)):
        for qz0, qz1 in ((-136, 0), (0, 136)):
            light_area(save, qx0 - 16, qx1 + 16, qz0 - 16, qz1 + 16, 64, 192, edits, stats)
            print('lit quarter', qx0, qz0, dict(stats['lights']), flush=True)
    n = anvil_edit.apply(save, out, edits, bes, biome='oror_supreme_bosses:royal_capital')
    json.dump(dict(note='The kingdom\'s vehicles and turrets (tools/citadel/military.py); garrison.py stands them with the garrison.',
                   posts=forces, sites=stats['military_at'], headings=stats.get('military_heading', {})), open(os.path.join(out, 'MILITARY.json'), 'w'), separators=(',', ':'))
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

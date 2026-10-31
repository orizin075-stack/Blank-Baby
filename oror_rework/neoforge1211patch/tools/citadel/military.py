"""military.py: the kingdom's Superb Warfare installations, built into the citadel save by repair.py.

build(save, man, edits, bes, stats) lays out, on open level land of the outer belt (outside the outer moat, clear of the
watchtowers and fortresses, never on a road or under a structure):
  two airbases (north-west and south-east): a 240-block concrete runway with a centre line, threshold bars and edge
  lights, a crewed attack aircraft at its start (it takes off down the runway) and a launch apron with a spare one;
  four helipads (a white-bordered pad with a yellow H and corner lights) with a helicopter each;
  four tank hangars (concrete sheds opening toward the kingdom, three bays with a crewed tank and two spare ones, a
  workbench, an anvil and the armory's chests);
and the posts' supply (048): a charging station of Superb Warfare at every stand (it burns the coal blocks a hopper feeds
it from the coal chest on top, and charges every vehicle within eight blocks) and a depot chest (王国軍の弾薬庫) with
two loads of what the stand's vehicles fire, at the hangar bays, helipads, runway stands, motor pools and turret posts
(a station only where a turret runs on power: the HPJ-11), and a station by each gate for the guards' electric guns;
and chooses the kingdom's turret posts: MK-42 guns and HPJ-11 close-in weapon systems along the outer wall's
batteries, TOW launchers at the gate roads' crossfire points, HPJ-11s at the inner casemates and MK-42 guns at the
redoubts (turrets with a gunner's seat: a mortar, a rocket launcher or a laser tower has none, and a soldier cannot
work it). It returns the posts (vehicles to stand, crews to man them) for garrison.py, which writes them with the
garrison (MILITARY.json in the repaired save).
"""
import collections, math
import numpy as np
import world, loot

LAND = ('grass_block', 'farmland', 'coarse_dirt', 'dirt', 'dirt_path', 'podzol', 'water', 'moss_block', 'mud', 'rooted_dirt', 'sand', 'gravel')
SOFT = ('grass', 'fern', 'flower', 'poppy', 'dandelion', 'tulip', 'daisy', 'allium', 'bluet', 'orchid', 'lily', 'bush', 'wheat', 'carrot',
        'potato', 'beetroot', 'sapling', 'azalea', 'snow', 'cobweb', 'web')
YAW = {'east': -90.0, 'west': 90.0, 'south': 0.0, 'north': 180.0}


def mask(save):
    """Buildable columns of the kingdom: no building above them (anything built at y 68 or higher that is not a tree, and
    four blocks around it: the watchtowers, fortresses and walls), not a road, not deep water. The small obstacles of the
    outer belt (trees, pits, buried cores, berms, rubble, puddles) are cleared where something is built."""
    from scipy import ndimage
    a, _ = world.load(save, -640, 640, -640, 640, 62, 100)
    names = [n.split(':')[1] for n in world.NAMES] + [''] * 32
    natural = np.array([n in ('air', 'cave_air') or any(t in n for t in SOFT) or n.endswith(('_leaves', '_log', '_wood')) for n in names])
    built = ~natural[a[:, 6:, :]].all(axis=1)                     # y 68 and up
    built = ndimage.binary_dilation(built, iterations=4)
    road = np.array([n in ('cobblestone', 'polished_andesite', 'stone_bricks', 'gravel', 'dirt_path') for n in names])
    water = np.array([n == 'water' for n in names])
    deep = water[a[:, 2, :]] & water[a[:, 1, :]]                   # water at y 64 and 63: the moat, a lake
    ok = ~built & ~road[a[:, 2, :]] & ~deep
    return ok, a[:, 2:, :]


def find(ok, cx, cz, w, d, reach=60, step=2):
    """The w x d rectangle (x span w, z span d) of buildable columns nearest cx, cz: its x0, z0 (save coordinates)."""
    best = None
    for dx in range(-reach, reach + 1, step):
        for dz in range(-reach, reach + 1, step):
            x0, z0 = cx + dx - w // 2, cz + dz - d // 2
            i0, k0 = x0 + 640, z0 + 640
            if i0 < 2 or k0 < 2 or i0 + w > 1278 or k0 + d > 1278:
                continue
            if ok[i0:i0 + w, k0:k0 + d].all():
                dist = dx * dx + dz * dz
                if best is None or dist < best[0]:
                    best = (dist, x0, z0)
    return best and best[1:]


def clear(a, edits, x0, z0, w, d, floor, top=100):
    """The rectangle's columns: floor at y 64 (a block or a function of x, z), stone under it, air above it to top."""
    for x in range(x0, x0 + w):
        for z in range(z0, z0 + d):
            col = a[x + 640, :, z + 640]
            for yy in np.nonzero(col[1:top - 64])[0] + 1:
                edits[(x, int(yy) + 64, z)] = 'minecraft:air'
            edits[(x, 64, z)] = floor(x, z) if callable(floor) else floor
            edits[(x, 63, z)] = 'minecraft:stone'


# ---------------------------------------------------------------------------------------------------------- supply
# What each kind carries, as jp.oror.reborn.vehicle.Supply.LOAD (Superb Warfare 0.8.9.2's vehicle definitions): a
# depot holds two loads of each kind it serves.
_TANK = [('large_shell_he', 32), ('large_shell_gs', 16), ('rifle_ammo', 64), ('heavy_ammo', 64)]
_IFV = [('small_shell_he', 64), ('small_shell_gs', 64), ('medium_anti_ground_missile', 4), ('rifle_ammo', 64)]
_GUN = [('large_shell_he', 32), ('large_shell_cm', 8)]
LOAD = {'m_1a_2': _TANK, 't_90a': _TANK, 'ztz_99a': _TANK, 'bmp_2': _IFV, 'bradley': _IFV,
        'mk_42': _GUN, 'mle_1934': _GUN, 'bl_132': _GUN, 'hpj_11': [('small_shell_ap', 64), ('small_shell_ap', 64)],
        'tow': [('medium_anti_ground_missile', 4)] * 3,
        'a_10a': [('small_shell_ap', 64), ('small_shell_ap', 64), ('small_rocket', 16), ('large_anti_ground_missile', 2),
                  ('large_anti_ground_missile', 2), ('medium_aerial_bomb', 2)],
        'ah_6': [('small_shell_he', 64), ('small_shell_he', 64), ('small_rocket', 16)],
        'mi_28': [('small_shell_he', 64), ('small_rocket', 16), ('large_anti_ground_missile', 2), ('medium_anti_ground_missile', 4)]}
POWERED = ('hpj_11',)            # turrets with a battery (the guns and the TOW launcher have none)
CHEST = 'minecraft:chest[facing=%s,type=single,waterlogged=false]'


def power(edits, bes, stats, x, y, z, coal=8):
    """A post's power plant: a charging station (with two million FE in store and a stack of coal blocks in its fuel
    slot), a hopper on it and a chest of coal blocks on the hopper."""
    edits[(x, y, z)] = 'superbwarfare:charging_station[facing=north,show_range=false]'
    # a modded block entity is not upgraded by the game's data fixers: its item stack also in 1.21's form (count)
    bes[(x, y, z)] = {'id': 'superbwarfare:charging_station', 'x': x, 'y': y, 'z': z, 'Energy': 2000000, 'FuelTick': 0,
                      'MaxFuelTick': 1600, 'ShowRange': ('byte', 0),
                      'Items': [{'Slot': ('byte', 0), 'id': 'minecraft:coal_block', 'count': 64, 'Count': ('byte', 64)}]}
    edits[(x, y + 1, z)] = 'minecraft:hopper[enabled=true,facing=down]'
    bes[(x, y + 1, z)] = {'id': 'minecraft:hopper', 'x': x, 'y': y + 1, 'z': z, 'Items': [], 'TransferCooldown': 0}
    edits[(x, y + 2, z)] = CHEST % 'north'
    bes[(x, y + 2, z)] = {'id': 'minecraft:chest', 'x': x, 'y': y + 2, 'z': z, 'CustomName': '{"text":"発電所の石炭庫"}',
                          'Items': [{'Slot': ('byte', i), 'id': 'minecraft:coal_block', 'Count': ('byte', 64)} for i in range(coal)]}
    stats['military']['stations'] += 1


def depot(edits, bes, stats, x, y, z, kinds, facing='north'):
    """A depot chest (王国軍の弾薬庫) with two loads of what each of the kinds fires."""
    items = []
    for kind in kinds:
        for name, n in LOAD.get(kind, []):
            for _ in range(2):
                if len(items) < 27:
                    items.append({'Slot': ('byte', len(items)), 'id': 'superbwarfare:' + name, 'Count': ('byte', n)})
    edits[(x, y, z)] = CHEST % facing
    bes[(x, y, z)] = {'id': 'minecraft:chest', 'x': x, 'y': y, 'z': z, 'CustomName': '{"text":"王国軍の弾薬庫"}', 'Items': items}
    stats['military']['depots'] += 1


def _name(a, edits, x, y, z):
    if (x, y, z) in edits:
        return edits[(x, y, z)].split('[')[0]
    i, j, k = x + 640, y - 64, z + 640
    if not (0 <= i < a.shape[0] and 0 <= j < a.shape[1] and 0 <= k < a.shape[2]):
        return None
    return world.NAMES[a[i, j, k]]


def _air(a, edits, x, y, z):
    n = _name(a, edits, x, y, z)
    return n is not None and (n in ('minecraft:air', 'minecraft:cave_air') or any(t in n for t in SOFT))


def _floor(a, edits, x, y, z):
    n = _name(a, edits, x, y, z)
    return n is not None and not _air(a, edits, x, y, z) and 'water' not in n and 'lava' not in n and not n.endswith(
        ('_slab', '_stairs', 'fence', '_wall', 'trapdoor', 'carpet', 'torch', 'lantern', 'chest', 'barrel', 'hopper', 'rail', 'sign', '_bed'))


def spot(a, edits, taken, x, y, z, h, rmin, rmax):
    """The nearest cell to x, y, z (rmin to rmax off, level, a block up, or up to three down: the gate roads' posts
    stand three above their platform) on a floor with h blocks of air above it, none of them taken: for a depot (h 1)
    or a power plant (h 3)."""
    best = None
    for dy in (0, 1, -1, -2, -3):
        for dx in range(-rmax, rmax + 1):
            for dz in range(-rmax, rmax + 1):
                if max(abs(dx), abs(dz)) < rmin:
                    continue
                X, Y, Z = x + dx, y + dy, z + dz
                if any((X, Y + k, Z) in taken for k in range(h)):
                    continue
                if _floor(a, edits, X, Y - 1, Z) and all(_air(a, edits, X, Y + k, Z) for k in range(h)):
                    d = dx * dx + dz * dz + 4 * dy * dy
                    if best is None or d < best[0]:
                        best = (d, X, Y, Z)
    return best and best[1:]


def supply_posts(a, edits, bes, stats, posts, taken):
    """A depot beside every turret post (its gunner loads from it) and a power plant by the HPJ-11s; a depot and a
    plant by each motor pool's tank. The turrets' own places and a block round them are kept clear."""
    for p in posts:
        if p.get('still'):
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    for k in range(3):
                        taken.add((p['x'] + dx, p['y'] + k, p['z'] + dz))
    for p in posts:
        if not p.get('still') or p['vehicle'] not in LOAD:
            continue
        c = spot(a, edits, taken, p['x'], p['y'], p['z'], 1, 2, 5)
        if c:
            depot(edits, bes, stats, *c, [p['vehicle']])
            taken.add(c)
        else:
            stats['military']['depot_missing'] += 1
        if p['vehicle'] in POWERED:
            c = spot(a, edits, taken, p['x'], p['y'], p['z'], 3, 2, 6)
            if c:
                power(edits, bes, stats, *c, coal=4)
                taken.update((c[0], c[1] + k, c[2]) for k in range(3))
            else:
                stats['military']['station_missing'] += 1


def gate_power(a, edits, bes, stats, taken):
    """A power plant by each gate of the three rings (both sides of the road, where its guards stand): their electric
    guns are recharged from its store. And a plant and a depot by the motor pool's tank inside each outer gate."""
    for ring in (115, 303, 472):
        for ax, az in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            inside = ring - 15
            for sgn in (-1, 1):
                gx = ax * inside + (sgn * 8 if az else 0)
                gz = az * inside + (sgn * 8 if ax else 0)
                c = spot(a, edits, taken, gx, 65, gz, 3, 2, 7)
                if c:
                    power(edits, bes, stats, *c, coal=4)
                    taken.update((c[0], c[1] + k, c[2]) for k in range(3))
                    stats['military']['gate_stations'] += 1
                else:
                    stats['military']['station_missing'] += 1
    for ax, az in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        tx, tz = ax * 440 + (9 if az else 0), az * 440 + (9 if ax else 0)
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                for k in range(4):
                    taken.add((tx + dx, 65 + k, tz + dz))
        c = spot(a, edits, taken, tx, 65, tz, 3, 4, 7)
        if c:
            power(edits, bes, stats, *c)
            taken.update((c[0], c[1] + k, c[2]) for k in range(3))
        c = spot(a, edits, taken, tx, 65, tz, 1, 4, 8)
        if c:
            depot(edits, bes, stats, *c, ['m_1a_2'])
            taken.add(c)


def runway(a, ok, edits, bes, stats, posts, cx, cz, heading, name):
    """A runway of 240 x 15 along x (heading east or west from its start), its apron, its aircraft."""
    L, W, M = 240, 15, 3
    spot = find(ok, cx, cz, L, W + 2 * M + 22, reach=50)
    if not spot:
        stats['military_missing'].append(name)
        return
    x0, z0 = spot
    zc = z0 + M + W // 2                # the runway's centre line
    start = x0 + 4 if heading == 'east' else x0 + L - 5

    def surface(x, z):
        u = x - x0 if heading == 'east' else x0 + L - 1 - x       # distance from the start
        if abs(z - zc) == W // 2:
            return 'minecraft:white_concrete'
        if z == zc and u % 10 < 5 and 14 < u < L - 14:
            return 'minecraft:white_concrete'
        if u < 10 and abs(z - zc) < W // 2 - 1 and (z - zc) % 2 == 0:
            return 'minecraft:white_concrete'                    # threshold bars
        return 'minecraft:gray_concrete'
    clear(a, edits, x0, z0 + M, L, W, surface)
    clear(a, edits, x0, z0, L, M, 'minecraft:grass_block')
    clear(a, edits, x0, z0 + M + W, L, M, 'minecraft:grass_block')
    for x in range(x0, x0 + L, 12):
        for z in (zc - W // 2 - 1, zc + W // 2 + 1):
            edits[(x, 64, z)] = 'minecraft:sea_lantern'
    # the launch apron beside the start, with its spare aircraft
    ax0 = x0 if heading == 'east' else x0 + L - 22
    az0 = z0 + M + W + M
    clear(a, edits, ax0, az0, 22, 19, lambda x, z: 'minecraft:yellow_concrete' if x in (ax0, ax0 + 21) or z in (az0, az0 + 18)
          else 'minecraft:light_gray_concrete')
    for x, z in ((ax0, az0), (ax0 + 21, az0), (ax0, az0 + 18), (ax0 + 21, az0 + 18)):
        edits[(x, 64, z)] = 'minecraft:sea_lantern'
    posts.append(dict(role='TANK', x=start, y=65, z=zc, yaw=YAW[heading], post='airbase', vehicle='a_10a', seats=1, exact=True))
    posts.append(dict(role='PARKED', x=ax0 + 11, y=65, z=az0 + 9, yaw=YAW[heading], post='airbase', vehicle='a_10a', seats=0, exact=True))
    # the stands' supply: a power plant and a depot in the grass beside the crewed aircraft's stand (it is towed back
    # there after landing), and on the apron by the spare
    power(edits, bes, stats, start, 65, zc - 9)
    depot(edits, bes, stats, start - 2 if heading == 'east' else start + 2, 65, zc - 9, ['a_10a'])
    power(edits, bes, stats, ax0 + 11, 65, az0 + 1)
    depot(edits, bes, stats, ax0 + 13, 65, az0 + 1, ['a_10a'])
    stats['military']['runways'] += 1
    stats['military_at'][name] = [x0, z0, L, W + 2 * M + 22]


H_SHAPE = ['X...X', 'X...X', 'XXXXX', 'X...X', 'X...X']


def helipad(a, ok, edits, bes, stats, posts, cx, cz, heli, name):
    n = 13
    spot = find(ok, cx, cz, n, n)
    if not spot:
        stats['military_missing'].append(name)
        return
    x0, z0 = spot

    def surface(x, z):
        u, v = x - x0, z - z0
        if u in (0, n - 1) or v in (0, n - 1):
            return 'minecraft:white_concrete'
        hu, hv = u - 4, v - 4
        if 0 <= hu < 5 and 0 <= hv < 5 and H_SHAPE[hv][hu] == 'X':
            return 'minecraft:yellow_concrete'
        return 'minecraft:gray_concrete'
    clear(a, edits, x0, z0, n, n, surface)
    for x, z in ((x0, z0), (x0 + n - 1, z0), (x0, z0 + n - 1), (x0 + n - 1, z0 + n - 1)):
        edits[(x, 64, z)] = 'minecraft:sea_lantern'
    # a windsock: a fence pole with an orange banner of wool
    edits[(x0 - 1, 65, z0 - 1)] = 'minecraft:oak_fence'
    edits[(x0 - 1, 66, z0 - 1)] = 'minecraft:oak_fence'
    edits[(x0 - 1, 67, z0 - 1)] = 'minecraft:orange_wool'
    # the pad's supply: a power plant at the middle of its west edge, its depot at the middle of the east edge
    power(edits, bes, stats, x0, 65, z0 + n // 2)
    depot(edits, bes, stats, x0 + n - 1, 65, z0 + n // 2, [heli], facing='west')
    # a pilot and a gunner: the helicopter lifts off when an enemy comes (RoyalPilots.hover) and settles back on its pad
    posts.append(dict(role='TANK', x=x0 + n // 2, y=65, z=z0 + n // 2, yaw=0.0, post='helipad', vehicle=heli, seats=2, exact=True))
    stats['military']['helipads'] += 1
    stats['military_at'][name] = [x0, z0, n, n]


def hangar(a, ok, edits, bes, stats, posts, cx, cz, opening, tanks, name):
    """A 25 x 17 concrete hangar, 9 high, opening toward opening: three bays (the middle tank crewed), its workshop."""
    W, D, H = 25, 17, 9
    along_x = opening in ('north', 'south')
    w, d = (W, D) if along_x else (D, W)
    spot = find(ok, cx, cz, w + 2, d + 2)
    if not spot:
        stats['military_missing'].append(name)
        return
    x0, z0 = spot[0] + 1, spot[1] + 1
    clear(a, edits, x0 - 1, z0 - 1, w + 2, d + 2, 'minecraft:grass_block', top=110)
    for x in range(x0, x0 + w):
        for z in range(z0, z0 + d):
            # local: u across the opening, v into the hangar from the opening
            if opening == 'south':
                u, v = x - x0, z0 + d - 1 - z
            elif opening == 'north':
                u, v = x - x0, z - z0
            elif opening == 'east':
                u, v = z - z0, x0 + w - 1 - x
            else:
                u, v = z - z0, x - x0
            edge = u in (0, W - 1) or v == D - 1
            front = v == 0
            edits[(x, 64, z)] = 'minecraft:polished_andesite' if not (v < D - 1 and u % 8 == 4 and 0 < v) else 'minecraft:yellow_concrete'
            for y in range(65, 65 + H):
                if edge:
                    st = 'minecraft:iron_block' if u in (0, W - 1) and v % 6 == 0 or v == D - 1 and u % 6 == 0 else 'minecraft:light_gray_concrete'
                elif front:
                    st = 'minecraft:light_gray_concrete' if (u < 2 or u > W - 3 or y >= 65 + H - 2) else 'minecraft:air'
                else:
                    st = 'minecraft:air'
                edits[(x, y, z)] = st
            edits[(x, 65 + H, z)] = 'minecraft:sea_lantern' if (u % 6 == 3 and v % 5 == 2 and 0 < u < W - 1) else 'minecraft:smooth_stone'
            edits[(x, 66 + H, z)] = 'minecraft:smooth_stone_slab[type=bottom,waterlogged=false]'

    def world_of(u, v):
        if opening == 'south':
            return x0 + u, z0 + d - 1 - v
        if opening == 'north':
            return x0 + u, z0 + v
        if opening == 'east':
            return x0 + w - 1 - v, z0 + u
        return x0 + v, z0 + u
    for i, u in enumerate((4, 12, 20)):
        x, z = world_of(u, 8)
        crewed = i == 1
        posts.append(dict(role='TANK' if crewed else 'PARKED', x=x, y=65, z=z, yaw=YAW[opening], post='hangar', vehicle=tanks[i],
                          seats=2 if crewed else 0, exact=True))
    # a power plant behind each bay (six blocks from its vehicle: within its station's reach)
    for u in (4, 12, 20):
        x, z = world_of(u, D - 3)
        power(edits, bes, stats, x, 65, z)
    # the workshop along the back wall: chests of the armory, a depot for each bay, a crafting table, an anvil
    bay_of = {5: tanks[0], 11: tanks[1], 20: tanks[2]}
    for k, u in enumerate(range(2, W - 2, 3)):
        x, z = world_of(u, D - 2)
        if k % 3 == 2:
            edits[(x, 65, z)] = 'minecraft:crafting_table' if k % 2 else 'minecraft:anvil[facing=north]'
            continue
        if u in bay_of:
            depot(edits, bes, stats, x, 65, z, [bay_of[u]], facing=opening)
            continue
        edits[(x, 65, z)] = 'minecraft:chest[facing=%s,type=single,waterlogged=false]' % {'south': 'south', 'north': 'north', 'east': 'east', 'west': 'west'}[opening]
        bes[(x, 65, z)] = {'id': 'minecraft:chest', 'x': x, 'y': 65, 'z': z, 'CustomName': '{"text":"格納庫の武器庫"}',
                           'Items': loot.items('armory', x * 31 + z * 7)}
        stats['military']['hangar_chests'] += 1
    stats['military']['hangars'] += 1
    stats['military_at'][name] = [x0, z0, w, d]


def outward(x, z):
    """The yaw of facing away from the castle's centre at x, z."""
    return (math.degrees(math.atan2(-x, z)) + 180) % 360 - 180


# the turrets a soldier can sit in and work (the CI seat survey: a mortar, a rocket launcher or a laser tower has no
# gunner's seat), by post: the wall's batteries take guns and interceptors in turn, the gate roads anti-tank missiles,
# the casemates interceptors and field guns, the redoubts the heavy guns
WALL_KINDS = ['mk_42', 'hpj_11', 'mle_1934', 'bl_132']
ROAD_KINDS = ['tow']
CASEMATE_KINDS = ['hpj_11', 'bl_132', 'mle_1934']
# (the Annihilator is no turret of the kingdom's: too terrible to field, it is kept in the forbidden vault)
REDOUBT_KINDS = ['mk_42', 'mle_1934']


def turrets(man):
    """Turret posts: every third outer-wall battery (64), every gate-road crossfire point, every casemate and every
    redoubt, each kind of post with its own turrets in turn."""
    out = []
    walls = sorted((e for e in man['v7_emplacements'] if e['kind'] == 'wall_battery'), key=lambda e: math.atan2(e['z'], e['x']))
    for i, e in enumerate(walls[::3]):
        out.append(dict(role='TANK', x=e['x'], y=e['y'], z=e['z'], yaw=outward(e['x'], e['z']), post='battery',
                        vehicle=WALL_KINDS[i % len(WALL_KINDS)], seats=1, still=True))
    roads = [e for e in man['v7_emplacements'] if e['kind'] == 'road_crossfire']
    for i, e in enumerate(roads):
        out.append(dict(role='TANK', x=e['x'], y=e['y'], z=e['z'], yaw=outward(e['x'], e['z']), post='crossfire',
                        vehicle=ROAD_KINDS[i % len(ROAD_KINDS)], seats=1, still=True))
    cas = [p for p in man['v6_defense_points'] if p['kind'] == 'siege_casemate']
    for i, p in enumerate(cas):
        out.append(dict(role='TANK', x=p['x'], y=p['y'], z=p['z'], yaw=outward(p['x'], p['z']), post='casemate',
                        vehicle=CASEMATE_KINDS[i % len(CASEMATE_KINDS)], seats=1, still=True))
    red = [p for p in man['v6_defense_points'] if p['kind'] == 'outer_redoubt']
    for i, p in enumerate(red):
        out.append(dict(role='TANK', x=p['x'], y=p['y'], z=p['z'], yaw=outward(p['x'], p['z']), post='redoubt',
                        vehicle=REDOUBT_KINDS[i % len(REDOUBT_KINDS)], seats=1, still=True))
    return out


def build(save, man, edits, bes, stats):
    stats['military'] = collections.Counter()
    stats['military_missing'] = []
    stats['military_at'] = {}
    ok, a = mask(save)
    # nothing within the outer moat: the belt beyond |x| or |z| 520
    xs = np.arange(-640, 640)
    belt = (np.abs(xs)[:, None] >= 522) | (np.abs(xs)[None, :] >= 522)
    ok &= belt
    posts = []
    runway(a, ok, edits, bes, stats, posts, -430, -605, 'east', 'airbase_nw')
    runway(a, ok, edits, bes, stats, posts, 430, 605, 'west', 'airbase_se')
    # keep the next sites off what was just built
    for (x0, z0, w, d) in stats['military_at'].values():
        ok[x0 + 640 - 4:x0 + 640 + w + 4, z0 + 640 - 4:z0 + 640 + d + 4] = False
    for i, (cx, cz, heli) in enumerate(((-560, -470, 'ah_6'), (-480, -560, 'mi_28'), (560, 470, 'ah_6'), (480, 560, 'mi_28'))):
        helipad(a, ok, edits, bes, stats, posts, cx, cz, heli, 'helipad_%d' % i)
        x0, z0, w, d = stats['military_at'].get('helipad_%d' % i, (0, 0, 0, 0))
        if w:
            ok[x0 + 640 - 3:x0 + 640 + w + 3, z0 + 640 - 3:z0 + 640 + d + 3] = False
    sets = [['m_1a_2', 't_90a', 'ztz_99a'], ['t_90a', 'm_1a_2', 'bmp_2'], ['ztz_99a', 'm_1a_2', 't_90a'], ['bradley', 't_90a', 'm_1a_2']]
    for i, (cx, cz, opening) in enumerate(((-585, -110, 'east'), (-585, 110, 'east'), (585, -110, 'west'), (585, 110, 'west'))):
        hangar(a, ok, edits, bes, stats, posts, cx, cz, opening, sets[i], 'hangar_%d' % i)
        x0, z0, w, d = stats['military_at'].get('hangar_%d' % i, (0, 0, 0, 0))
        if w:
            ok[x0 + 640 - 4:x0 + 640 + w + 4, z0 + 640 - 4:z0 + 640 + d + 4] = False
    posts += turrets(man)
    stats['military']['turrets'] = sum(1 for p in posts if p.get('still'))
    taken = set()
    supply_posts(a, edits, bes, stats, posts, taken)
    gate_power(a, edits, bes, stats, taken)
    return posts

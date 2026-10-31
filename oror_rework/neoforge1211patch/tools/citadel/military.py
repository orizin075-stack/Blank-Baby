"""military.py: the kingdom's Superb Warfare installations, built into the citadel save by repair.py.

build(save, man, edits, bes, stats) lays out, on open level land of the outer belt (outside the outer moat, clear of the
watchtowers and fortresses, never on a road or under a structure):
  two airbases (north-west and south-east): a 240-block concrete runway with a centre line, threshold bars and edge
  lights, a crewed attack aircraft at its start (it takes off down the runway) and a launch apron with a spare one;
  four helipads (a white-bordered pad with a yellow H and corner lights) with a helicopter each;
  four tank hangars (concrete sheds opening toward the kingdom, three bays with a crewed tank and two spare ones, a
  workbench, an anvil and the armory's chests);
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


def runway(a, ok, edits, stats, posts, cx, cz, heading, name):
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
    stats['military']['runways'] += 1
    stats['military_at'][name] = [x0, z0, L, W + 2 * M + 22]


H_SHAPE = ['X...X', 'X...X', 'XXXXX', 'X...X', 'X...X']


def helipad(a, ok, edits, stats, posts, cx, cz, heli, name):
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
    # the workshop along the back wall: chests of the armory, a crafting table, an anvil
    for k, u in enumerate(range(2, W - 2, 3)):
        x, z = world_of(u, D - 2)
        if k % 3 == 2:
            edits[(x, 65, z)] = 'minecraft:crafting_table' if k % 2 else 'minecraft:anvil[facing=north]'
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
    runway(a, ok, edits, stats, posts, -430, -605, 'east', 'airbase_nw')
    runway(a, ok, edits, stats, posts, 430, 605, 'west', 'airbase_se')
    # keep the next sites off what was just built
    for (x0, z0, w, d) in stats['military_at'].values():
        ok[x0 + 640 - 4:x0 + 640 + w + 4, z0 + 640 - 4:z0 + 640 + d + 4] = False
    for i, (cx, cz, heli) in enumerate(((-560, -470, 'ah_6'), (-480, -560, 'mi_28'), (560, 470, 'ah_6'), (480, 560, 'mi_28'))):
        helipad(a, ok, edits, stats, posts, cx, cz, heli, 'helipad_%d' % i)
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
    return posts

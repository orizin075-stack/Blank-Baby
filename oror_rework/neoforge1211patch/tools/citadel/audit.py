"""audit.py <repaired save> <garrison.json> <out dir>: what is broken or missing in the citadel, building by building.

Town buildings (TOWN_BUILDINGS.json): a door; walls without holes (a flood through air from the floor cells inside
must not reach the outside except through a door or a window); a roof over every floor cell; beds for the townsfolk
the garrison stands in it; the trade's workstation; a chest or barrel; stairs or a ladder between storeys; something
standing in the floor cells the townsfolk are given.
The castle (within 136 of the centre): columns whose top is a floor or a wall far below the roofs round them (a hole
in a roof), and blocks hanging in the air with nothing under or beside them.
The walls' three rings: lengths of the wall line lower than the wall round them (a breach) away from the gates.
Military posts (MILITARY.json): room for the vehicle (air over its footprint) and a floor under it; its station within
eight blocks and its depot within ten where it should have them; open sky over helipads and runways, a clear way out
of each hangar bay, the ground under each runway's approach.
Garrison posts: a floor under every soldier's and townsman's feet and two blocks of air.

Writes audit.json (every finding) and audit_map.png (the findings on a map of the kingdom) to the out dir and prints a
summary.
"""
import sys, os, json, collections, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
import world

save, garrison_path, out = sys.argv[1:4]
os.makedirs(out, exist_ok=True)
X0, X1, Z0, Z1, Y0, Y1 = -640, 640, -640, 640, 60, 192
print('loading', flush=True)
a, bes = world.load(save, X0, X1, Z0, Z1, Y0, Y1)
N = world.NAMES
short = [n.split(':')[1] for n in N] + [''] * 64
PAD = [False] * 64
air = np.array([s in ('air', 'cave_air', 'light', 'void_air') for s in short[:len(N)]] + PAD)
CROPS = ('wheat', 'carrots', 'potatoes', 'beetroots', 'melon_stem', 'pumpkin_stem', 'sweet_berry_bush', 'tall_grass', 'large_fern', 'dead_bush')
passable = np.array([s in ('air', 'cave_air', 'light', 'void_air') or s.endswith(('_carpet', 'pressure_plate', 'rail', 'torch', 'button', '_tulip'))
                     or s in ('short_grass', 'grass', 'fern', 'snow', 'redstone_wire', 'tripwire', 'lever', 'poppy', 'dandelion', 'cornflower',
                              'allium', 'azure_bluet', 'oxeye_daisy', 'lily_of_the_valley', 'blue_orchid') or s in CROPS
                     for s in short[:len(N)]] + PAD)
solidfloor = np.array([not (s in ('air', 'cave_air', 'light', 'void_air', 'water', 'lava') or s.endswith(
    ('_carpet', 'pressure_plate', 'rail', 'torch', 'button', 'sign', 'banner', 'flower', 'sapling')) or s in ('short_grass', 'grass', 'fern'))
                       for s in short[:len(N)]] + PAD)
roofish = np.array(['stairs' in s or 'slab' in s or 'tiles' in s or 'shingle' in s or 'planks' in s or 'deepslate' in s or 'brick' in s
                    or 'copper' in s or 'prismarine' in s or 'concrete' in s or 'stone' in s or 'quartz' in s or 'calcite' in s or 'wool' in s
                    for s in short[:len(N)]] + PAD)


def gid_of(name):
    return world.IDS.get(name if ':' in name else 'minecraft:' + name, -1)


def blk(x, y, z):
    i, j, k = x - X0, y - Y0, z - Z0
    if 0 <= i < a.shape[0] and 0 <= j < a.shape[1] and 0 <= k < a.shape[2]:
        return int(a[i, j, k])
    return 0


def name(x, y, z):
    return short[blk(x, y, z)]


findings = []


def find(kind, where, what, **extra):
    findings.append(dict(kind=kind, x=int(where[0]), y=int(where[1]), z=int(where[2]), what=what, **extra))


# ------------------------------------------------------------------------------------------------------- town
town = json.load(open(os.path.join(save, 'TOWN_BUILDINGS.json')))['buildings']
garrison = json.load(open(garrison_path))['entries']
NEED = dict(inn=6, tavern=4, guardhouse=4, chapel=3, school=3, clinic=3)
residents = collections.Counter()
rects = []
for b in town:
    xs = [s[0] for s in b['spots']] or [b['x']]
    zs = [s[2] for s in b['spots']] or [b['z']]
    rects.append((min(xs) - 1, max(xs) + 1, min(zs) - 1, max(zs) + 1))
for e in garrison:
    if e['role'] == 'VILLAGER':
        for i, (rx0, rx1, rz0, rz1) in enumerate(rects):
            if rx0 <= e['x'] <= rx1 and rz0 <= e['z'] <= rz1:
                residents[i] += 1
                break
print('town', len(town), 'buildings', flush=True)
stats = collections.Counter()
for i, b in enumerate(town):
    rx0, rx1, rz0, rz1 = rects[i]
    spots = [tuple(s) for s in b['spots']]
    if not spots:
        find('town:no-floor', (b['x'], 66, b['z']), '%s #%d has no free floor cell' % (b['kind'], b['id']))
        continue
    floors = sorted({s[1] for s in spots})
    ytop = floors[-1] + 6
    box = [(x, y, z) for x in range(rx0 - 1, rx1 + 2) for z in range(rz0 - 1, rz1 + 2) for y in range(floors[0] - 1, ytop + 1)]
    names_in = collections.Counter(name(*p) for p in box)
    # a door
    if not any(n.endswith('_door') for n in names_in):
        find('town:no-door', (b['x'], floors[0], b['z']), '%s #%d (%s) has no door' % (b['kind'], b['id'], b['style']))
    # the workstation and storage
    st = b.get('station')
    if st and names_in[st] == 0 and not (st == 'cauldron' and names_in['water_cauldron'] + names_in['lava_cauldron'] > 0):
        find('town:no-station', (b['x'], floors[0], b['z']), '%s #%d lacks its %s' % (b['kind'], b['id'], st), station=st)
    if names_in['chest'] + names_in['barrel'] == 0:
        find('town:no-storage', (b['x'], floors[0], b['z']), '%s #%d has no chest or barrel' % (b['kind'], b['id']))
    # beds for the townsfolk standing in it (two blocks a bed)
    beds = sum(v for n, v in names_in.items() if n.endswith('_bed')) // 2
    need = max(residents[i], 1 if b['kind'] in ('house', 'inn') else 0)
    if beds < need:
        find('town:few-beds', (b['x'], floors[0], b['z']), '%s #%d: %d beds for %d townsfolk' % (b['kind'], b['id'], beds, need),
             beds=beds, residents=need)
    stats['beds'] += beds
    stats['residents'] += residents[i]
    # stairs or a ladder between storeys
    if len(floors) > 1 and not any(('stairs' in n or n == 'ladder') for n in names_in):
        find('town:no-stairs', (b['x'], floors[0], b['z']), '%s #%d has %d storeys and no stairs' % (b['kind'], b['id'], len(floors)))
    # floor cells: standable (floor under, two air)
    blocked = [s for s in spots if not (passable[blk(*s)] and passable[blk(s[0], s[1] + 1, s[2])] and solidfloor[blk(s[0], s[1] - 1, s[2])])]
    if len(blocked) > max(2, len(spots) // 10):
        find('town:spots-blocked', blocked[0], '%s #%d: %d of %d floor cells blocked (%s)' % (b['kind'], b['id'], len(blocked), len(spots),
             name(*blocked[0])))
    # the roof: something over every floor cell within twelve blocks
    open_sky = [s for s in spots if not any(not air[blk(s[0], y, s[2])] for y in range(s[1] + 2, s[1] + 14))]
    if open_sky:
        find('town:roof-hole', open_sky[0], '%s #%d: %d floor cells open to the sky' % (b['kind'], b['id'], len(open_sky)), cells=len(open_sky))
    # the walls: a flood through passable cells from the floor cells, kept to the storeys' heights, must stay inside
    # the walls (the rect) except through a door
    seen = set(spots)
    stack = list(spots)
    leak = None
    while stack and leak is None and len(seen) < 6000:
        x, y, z = stack.pop()
        for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 0, 1), (0, 0, -1), (0, 1, 0), (0, -1, 0)):
            q = (x + dx, y + dy, z + dz)
            if q in seen or not (floors[0] <= q[1] <= ytop):
                continue
            if not passable[blk(*q)]:
                continue
            seen.add(q)
            if not (rx0 - 1 <= q[0] <= rx1 + 1 and rz0 - 1 <= q[2] <= rz1 + 1):
                leak = q
                break
            stack.append(q)
    if leak is not None:
        find('town:wall-hole', leak, '%s #%d: open to the outside at %s' % (b['kind'], b['id'], leak))
    stats['buildings'] += 1

# ------------------------------------------------------------------------------------------------------- castle
print('castle', flush=True)
solid = ~air[a]
top = np.where(solid.any(axis=1), solid.shape[1] - 1 - np.argmax(solid[:, ::-1, :], axis=1), 0) + Y0
tid = np.take_along_axis(a, (top - Y0)[:, None, :], axis=1)[:, 0, :]
c0 = 640 - 136
sub = top[c0:c0 + 272, c0:c0 + 272].astype(float)
around = ndimage.maximum_filter(sub, size=9)
hole = (around - sub >= 10) & (sub > 104)
# a low top inside the castle with roofs round it on three sides or more is a hole, a court is open on a side
lab, n = ndimage.label(hole)
for k, sl in enumerate(ndimage.find_objects(lab), 1):
    m = lab[sl] == k
    if m.sum() < 6:
        continue
    cx, cz = int(np.mean(np.nonzero(m)[0])) + sl[0].start - 136, int(np.mean(np.nonzero(m)[1])) + sl[1].start - 136
    ring = ndimage.binary_dilation(lab == k, iterations=2) & ~(lab == k)
    hi = sub[ring]
    enclosed = (hi > sub[lab == k].max() + 6).mean()
    if enclosed > 0.85:
        find('castle:roof-hole', (cx, int(sub[lab == k].mean()), cz), 'castle: %d columns sunk %d below the roofs round them' % (
            m.sum(), int(around[lab == k].mean() - sub[lab == k].mean())), cells=int(m.sum()), enclosed=round(float(enclosed), 2))
# floating blocks in the castle: solid blocks with air on all six sides
cs = np.pad(solid[c0:c0 + 272, 29:, c0:c0 + 272], 1)
nb = np.zeros_like(cs, dtype=np.int8)
for ax in (0, 1, 2):
    for sh in (1, -1):
        nb += np.roll(cs, sh, axis=ax)
lone = (cs & (nb == 0))[1:-1, 1:-1, 1:-1]
lone[:, 0, :] = False
for p in np.argwhere(lone)[:200]:
    x, y, z = int(p[0]) + c0 + X0, int(p[1]) + 29 + Y0, int(p[2]) + c0 + Z0
    if name(x, y, z) not in ('lantern', 'light', 'chain', 'end_rod', 'torch', 'bell') and 'stairs' not in name(x, y, z):
        find('castle:floating', (x, y, z), 'a lone %s in the air' % name(x, y, z))

# ------------------------------------------------------------------------------------------------------- the rings
print('walls', flush=True)
for ring in (115, 303, 472):
    heights = []
    for t in range(-ring, ring + 1):
        for side, (x, z) in (('n', (t, -ring)), ('s', (t, ring)), ('w', (-ring, t)), ('e', (ring, t))):
            h = max(top[x - X0 + d * (1 if side in 'we' else 0), z - Z0 + d * (1 if side in 'ns' else 0)] for d in range(-4, 5))
            heights.append((side, t, h, x, z))
    med = np.median([h for _, _, h, _, _ in heights])
    for side, t, h, x, z in heights:
        if h < med - 6 and abs(t) > 14:
            find('walls:breach', (x, h, z), 'ring %d (%s side): the wall is %d below its run' % (ring, side, int(med - h)), ring=ring)

# ------------------------------------------------------------------------------------------------------- the roads
# the four main roads from the castle's gates out through the three rings: along each, somewhere across it (ten blocks
# to each side of its middle: a fountain in the middle of the road is gone round) there must be a cell to walk on (a
# floor, two blocks of air) within a block up or down of the last one
print('roads', flush=True)
for name_, (ax, az) in (('north', (0, -1)), ('south', (0, 1)), ('west', (-1, 0)), ('east', (1, 0))):
    level = None
    for t in range(100, 520):
        cells = []
        for s_ in range(-10, 11):
            x, z = ax * t + (s_ if az else 0), az * t + (s_ if ax else 0)
            for y in range(63, 80):
                if solidfloor[blk(x, y - 1, z)] and passable[blk(x, y, z)] and passable[blk(x, y + 1, z)]:
                    cells.append(y)
        if level is None:
            level = min(cells, key=lambda y: abs(y - 65)) if cells else 65
            continue
        ok = [y for y in cells if abs(y - level) <= 1]
        if not ok:
            x, z = ax * t, az * t
            find('roads:blocked', (x, level, z), '%s road %d blocks out: no way on (%s at the road level)' % (name_, t, name(x, level, z)))
            level = min(cells, key=lambda y: abs(y - level)) if cells else level
        else:
            level = min(ok, key=lambda y: abs(y - level))

# ------------------------------------------------------------------------------------------------------- military
print('military', flush=True)
mil = json.load(open(os.path.join(save, 'MILITARY.json')))
station_ids = {gid_of('superbwarfare:charging_station')}
station_pos = [(p[0] + X0, p[1] + Y0, p[2] + Z0) for p in np.argwhere(np.isin(a, list(station_ids)))]
depot_pos = [(be['x'], be['y'], be['z']) for be in bes if '弾薬庫' in str(be.get('CustomName', ''))]
# a vehicle's room on its post: half its width, half its length (along its heading), its height
SIZE = {'a_10a': (9, 8, 4), 'ah_6': (4, 5, 4), 'mi_28': (5, 6, 5), 'm_1a_2': (2, 4, 4), 't_90a': (2, 4, 4), 'ztz_99a': (2, 4, 4), 'bmp_2': (2, 4, 3),
        'bradley': (2, 4, 3)}
POWERED = ('m_1a_2', 't_90a', 'ztz_99a', 'bmp_2', 'bradley', 'a_10a', 'ah_6', 'mi_28', 'hpj_11')


def near(points, x, y, z, reach, dy=5):
    return any(abs(px - x) <= reach and abs(pz - z) <= reach and abs(py - y) <= dy for px, py, pz in points)


for p in mil['posts']:
    x, y, z, v = p['x'], p['y'], p['z'], p['vehicle']
    if not solidfloor[blk(x, y - 1, z)]:
        find('military:no-floor', (x, y, z), '%s at its %s post has no floor (%s)' % (v, p['post'], name(x, y - 1, z)))
    hw, hl, high = SIZE.get(v, (1, 1, 2))
    half = max(hw, hl)
    if not p.get('still'):
        hx, hz = (hl, hw) if abs(abs(p['yaw']) - 90) < 1 else (hw, hl)   # heading east or west: its length along x
        crowd = [(x + dx, y + dy, z + dz) for dx in range(-hx, hx + 1) for dz in range(-hz, hz + 1) for dy in range(0, high)
                 if not passable[blk(x + dx, y + dy, z + dz)]]
        if crowd:
            find('military:crowded', (x, y, z), '%s at its %s post: %d blocks in its room, e.g. %s at %s' % (
                v, p['post'], len(crowd), name(*crowd[0]), crowd[0]))
    if v in POWERED and not near(station_pos, x, y, z, 8.5 + half):
        find('military:no-station', (x, y, z), '%s at its %s post has no charging station in reach' % (v, p['post']))
    if v not in ('tow',) and not near(depot_pos, x, y, z, 10):
        find('military:no-depot', (x, y, z), '%s at its %s post has no depot in reach' % (v, p['post']))
    elif v == 'tow' and not near(depot_pos, x, y, z, 10):
        find('military:no-depot', (x, y, z), 'tow at its %s post has no depot in reach' % p['post'])
    if p['post'] == 'helipad':
        roofed = [(x + dx, z + dz) for dx in range(-6, 7) for dz in range(-6, 7) if top[x + dx - X0, z + dz - Z0] > y + 3]
        if roofed:
            find('military:helipad-roofed', (x, y, z), 'helipad: %d columns over the pad higher than three blocks' % len(roofed))
    if p['post'] == 'hangar':
        # the way out of the bay: along the hangar's opening direction, the bay's width must be clear to the outside
        yaw = p['yaw']
        fx, fz = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        for d in range(4, 20):
            q = (int(round(x + fx * d)), y, int(round(z + fz * d)))
            if not passable[blk(*q)] or not passable[blk(q[0], q[1] + 1, q[2])]:
                find('military:hangar-blocked', q, 'hangar bay (%s): %s in the way out %d blocks ahead' % (v, name(*q), d))
                break
HEAD = {-90.0: (1, 0), 90.0: (-1, 0), 0.0: (0, 1), 180.0: (0, -1)}         # yaw: the way it faces (x, z)
for name_, site in mil['sites'].items():
    if name_.startswith('airbase'):
        x0, z0, w, d = site
        for p in mil['posts']:
            if p['post'] == 'airbase' and p['role'] == 'TANK' and x0 <= p['x'] < x0 + w and z0 <= p['z'] < z0 + d:
                fx, fz = HEAD.get(float(p['yaw']), (1, 0))
                sx, sz = -fz, fx                                          # across the runway
                # the runway itself: 15 wide, 240 on from its start
                over = [(p['x'] + fx * u + sx * v, p['z'] + fz * u + sz * v) for u in range(-4, 236, 3) for v in range(-7, 8, 2)]
                over = [(x, z) for x, z in over if top[x - X0, z - Z0] > 66]
                if over:
                    find('military:runway-obstructed', (over[0][0], 70, over[0][1]), '%s: %d points of the runway with something on it'
                         % (name_, len(over)))
                # the approach: 200 blocks of the extended centre line behind the start, under a glide of one in ten
                tx, tz = p['x'] + 25 * fx, p['z'] + 25 * fz
                high = [(tx - fx * dd, tz - fz * dd, top[tx - fx * dd - X0, tz - fz * dd - Z0]) for dd in range(10, 200, 5)
                        if -640 <= tx - fx * dd < 640 and -640 <= tz - fz * dd < 640
                        and top[tx - fx * dd - X0, tz - fz * dd - Z0] + 1 > max(67, 65 + 1.5 + dd * 0.1 - 3)]
                if high:
                    find('military:approach-obstructed', (high[0][0], int(high[0][2]), high[0][1]), '%s: the ground under its glide path rises '
                         'to %d at %d %d' % (name_, high[0][2], high[0][0], high[0][1]))

# ------------------------------------------------------------------------------------------------------- garrison
print('garrison', flush=True)
bad = collections.Counter()
for e in garrison:
    x, y, z = e['x'], e['y'], e['z']
    if not (-640 <= x < 640 and -640 <= z < 640):
        continue
    if not (solidfloor[blk(x, y - 1, z)] and passable[blk(x, y, z)] and passable[blk(x, y + 1, z)]):
        bad[e['post']] += 1
        if bad[e['post']] <= 3:
            find('garrison:cannot-stand', (x, y, z), '%s (%s) cannot stand: %s under, %s / %s' % (e['role'], e['post'], name(x, y - 1, z),
                 name(x, y, z), name(x, y + 1, z)))

# ------------------------------------------------------------------------------------------------------- report
summary = collections.Counter(f['kind'] for f in findings)
json.dump(dict(summary=summary, stats=stats, garrison_cannot_stand=bad, findings=findings), open(os.path.join(out, 'audit.json'), 'w'),
          ensure_ascii=False, indent=1)
print('summary', dict(summary))
print('stats', dict(stats), 'garrison cannot stand', dict(bad))
for k in sorted(summary):
    for f in [f for f in findings if f['kind'] == k][:4]:
        print('  %-28s %s' % (k, f['what']))
try:
    from PIL import Image, ImageDraw
    img = Image.fromarray(np.clip((top - 40) * 2, 0, 255).astype(np.uint8).T).convert('RGB')
    d = ImageDraw.Draw(img)
    colour = {'town': (255, 0, 0), 'castle': (255, 0, 255), 'walls': (255, 255, 0), 'military': (0, 200, 255), 'garrison': (0, 255, 0), 'roads': (255, 128, 0)}
    for f in findings:
        c = colour[f['kind'].split(':')[0]]
        d.ellipse([f['x'] - X0 - 4, f['z'] - Z0 - 4, f['x'] - X0 + 4, f['z'] - Z0 + 4], outline=c, width=2)
    img.save(os.path.join(out, 'audit_map.png'))
except Exception as error:
    print('no map:', error)

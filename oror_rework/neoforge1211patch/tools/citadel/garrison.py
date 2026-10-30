"""garrison.py <save dir> <out json>: where the Grand Citadel's royal court, garrison and townsfolk stand.

Anchors come from the castle itself (throne dais, gates, casemates, redoubts, fortresses from build_manifest.json);
each is moved to the nearest spot with a solid floor and two free blocks above, never onto a trap plate."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import world

save, out = sys.argv[1], sys.argv[2]
man = json.load(open(os.path.join(save, 'build_manifest.json')))
N = world.NAMES

FREE = ('air', 'cave_air', 'torch', 'wall_torch', 'light', 'short_grass', 'grass', 'fern', 'dandelion', 'poppy')
BAD_FLOOR = ('air', 'cave_air', 'water', 'lava', 'ladder', 'cobweb', 'fence', '_wall', 'pane', 'iron_bars', 'torch', 'lantern',
             'rail', 'pressure_plate', 'tripwire', 'sign', 'banner', 'button', 'snow', 'magma', 'fire', 'campfire', 'scaffolding',
             'chain', 'end_rod', 'candle', 'carpet', 'leaves', 'dispenser', 'hopper', 'pointed_dripstone', 'honey', 'slime',
             'trapdoor', 'door', 'gate', 'bed', 'flower', 'sapling', 'vine', 'cactus', 'sweet_berry', 'powder_snow')


def name(a, x, y, z):
    return N[a[x, y, z]].split(':')[1]


def free(n):
    return n in FREE or n.endswith('_carpet')


def floor_ok(n):
    return not any(b in n for b in BAD_FLOOR)


def stand(x, y, z, r=6, dy=2, taken=(), room=0):
    """Nearest (x, feet y, z) to the anchor with a solid floor and two free blocks above (a room-wide, four-high box for a vehicle)."""
    x0, z0, y0 = x - r - 1, z - r - 1, y - dy - 1
    a, _ = world.load(save, x0 - room, x + r + 2 + room, z0 - room, z + r + 2 + room, y0, y + dy + 5)
    x0, z0 = x0 - room, z0 - room
    best = None
    for ox in range(-r, r + 1):
        for oz in range(-r, r + 1):
            for oy in range(-dy, dy + 1):
                px, py, pz = x + ox - x0, y + oy - y0, z + oz - z0
                if not (floor_ok(name(a, px, py - 1, pz)) and free(name(a, px, py, pz)) and free(name(a, px, py + 1, pz))):
                    continue
                if (x + ox, y + oy, z + oz) in taken:
                    continue
                # room to turn: at least two free neighbours at feet height
                side = sum(free(name(a, px + u, py, pz + v)) for u, v in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if side < 2:
                    continue
                if room and not all(free(name(a, px + u, py + h, pz + v)) and floor_ok(name(a, px + u, py - 1, pz + v))
                                    for u in range(-room, room + 1) for v in range(-room, room + 1) for h in range(4)):
                    continue
                d = ox * ox + oz * oz + 4 * oy * oy
                if best is None or d < best[0]:
                    best = (d, (x + ox, y + oy, z + oz))
    return best and best[1]


entries = []
taken = set()


def put(role, x, y, z, yaw=0, r=6, dy=2, post=None, room=0, **extra):
    p = stand(x, y, z, r, dy, taken, room)
    if p is None:
        print('no spot for', role, (x, y, z), file=sys.stderr)
        return
    taken.add(p)
    e = dict(role=role, x=p[0], y=p[1], z=p[2], yaw=yaw)
    if post:
        e['post'] = post
    e.update(extra)
    entries.append(e)


# The throne room: the king on the gold dais facing the hall, the court around him.
put('KING', 0, 137, -32, yaw=0, r=1, dy=0, post='throne')
for sx in (-1, 1):
    put('BODYGUARD', 6 * sx, 135, -33, yaw=0, r=2, dy=0, post='throne')
    put('BODYGUARD', 6 * sx, 135, -30, yaw=0, r=2, dy=0, post='throne')
    put('GENERAL', 9 * sx, 135, -27, yaw=0, r=2, dy=0, post='throne')
    for z in (-27, -24, -21, -18):
        put('IMPERIAL', 4 * sx, 135, z, yaw=90 * sx, r=1, dy=0, post='throne')
put('ARCHMAGE', -9, 135, -21, yaw=-90, r=2, dy=0, post='throne')
put('SAGE', 9, 135, -21, yaw=90, r=2, dy=0, post='throne')

# The keep's entrance hall at the foot of the castle, on the four sides.
for ax, az, yaw in ((0, -1, 180), (0, 1, 0), (-1, 0, 90), (1, 0, -90)):
    cx, cz = ax * 88, az * 88
    put('GENERAL' if az else 'IMPERIAL', cx + (az * 4), 66, cz + (ax * 4), yaw=yaw, r=6, post='keep')
    put('IMPERIAL', cx - (az * 4), 66, cz - (ax * 4), yaw=yaw, r=6, post='keep')

# The gates of the three rings on the four roads: two guards just inside each gate.
for ring in (115, 303, 472):
    for ax, az, yaw in ((0, -1, 180), (0, 1, 0), (-1, 0, 90), (1, 0, -90)):
        inside = ring - 15
        for s in (-1, 1):
            gx = ax * inside + (s * 6 if az else 0)
            gz = az * inside + (s * 6 if ax else 0)
            put('GUARD', gx, 65, gz, yaw=yaw, r=5, post='gate')

# The motor pool: a tank inside each outer gate, brought out and crewed by its guard the first time the guard acts.
for ax, az, yaw in ((0, -1, 180), (0, 1, 0), (-1, 0, 90), (1, 0, -90)):
    put('TANK', ax * 440 + (9 if az else 0), 65, az * 440 + (9 if ax else 0), yaw=yaw, r=8, post='motor_pool', room=2,
        vehicle='m_1a_2', seats=2)

# Casemates beside the gates and the outer redoubts.
for i, p in enumerate(man['v6_defense_points']):
    role = 'GUARD' if p['kind'] == 'outer_redoubt' or i % 2 == 0 else 'MAGE'
    put(role, p['x'], p['y'], p['z'], r=7, dy=3, post=p['kind'])

# The four fortresses outside the walls: a general with his guard and a battle mage.
for f in man['exterior_fortresses']:
    put('GENERAL', f['x'], 66, f['z'], r=10, dy=4, post='fortress')
    put('GUARD', f['x'] + 4, 66, f['z'] + 4, r=10, dy=4, post='fortress')
    put('GUARD', f['x'] - 4, 66, f['z'] - 4, r=10, dy=4, post='fortress')
    put('ARCHMAGE', f['x'], 66, f['z'] + 6, r=10, dy=4, post='fortress')

TRADE = dict(house='', smith='weaponsmith', armorer='armorer', baker='farmer', butcher='butcher', tailor='shepherd',
             alchemy='cleric', jeweler='toolsmith', library='librarian', scribe='librarian', mapmaker='cartographer',
             stable='leatherworker', market='mason', guild='fletcher', inn='fisherman', tavern='fisherman')
from houses import HOUSEHOLD
# Townsfolk: a family in each house (one of them a child), the innkeeper's household and guests, a master and a helper
# in every other building; on the free floor cells of the rebuilt buildings (TOWN_BUILDINGS.json, written by repair.py),
# the ground floor first, spread out.
town = json.load(open(os.path.join(save, 'TOWN_BUILDINGS.json')))['buildings']
for b in town:
    many = HOUSEHOLD.get(b['kind'], 2)
    spots = sorted(b['spots'], key=lambda p: (p[1], p[0], p[2]))
    chosen = []
    for p in spots:
        if len(chosen) == many:
            break
        if all(abs(p[0] - q[0]) + abs(p[2] - q[2]) >= 3 or p[1] != q[1] for q in chosen):
            chosen.append(p)
    for p in spots:
        if len(chosen) == many:
            break
        if p not in chosen:
            chosen.append(p)
    for k, (x, y, z) in enumerate(chosen):
        put('VILLAGER', x, y, z, r=1, dy=0, post='town', profession=TRADE.get(b['kind'], '') if k == 0 else '', house=b['kind'],
            **({'baby': True} if b['kind'] in ('house', 'inn') and k == many - 1 else {}))

json.dump(dict(origin='save', entries=entries), open(out, 'w'), indent=None, separators=(',', ':'))
from collections import Counter
print(len(entries), Counter(e['role'] for e in entries))

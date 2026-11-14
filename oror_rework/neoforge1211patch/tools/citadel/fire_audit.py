"""fire_audit.py <template dir> [report.json]: how open each gun's field of fire is (059f's audit, kept this time).

From each gun post's muzzle (the post's block, 1.6 up), rays go out over the gun's front: every 5 degrees from 75 to
the left to 75 to the right of its facing, and from 35 below level to 10 above, out to 12 blocks. A ray is shut by the
first solid block it meets past the gun's own block (soft things - plants, lights, carpets, rails - and the natural
ground below the kingdom's level do not count). Per post: the share of the level and upward rays (from 5 below level)
that get through, the same within 45 degrees of its facing (its front), the share of all rays, and what shut the
others.
"""
import sys, os, json, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_io

SOFT = ('air', 'cave_air', 'light', 'water', 'short_grass', 'tall_grass', 'fern', 'snow', 'torch', 'wall_torch', 'lantern', 'soul_lantern',
        'chain', 'rail', 'powered_rail', 'tripwire', 'redstone_wire', 'ladder', 'vine', 'wheat', 'carrots', 'potatoes', 'beetroots')
POSTS = ('battery', 'casemate', 'crossfire', 'aa', 'redoubt')


def name(st):
    return st.split('[')[0].split(':')[-1]


def soft(nm):
    return nm in SOFT or nm.endswith(('_carpet', '_sapling', '_button', '_pressure_plate', '_banner', '_sign', 'flower', '_tulip'))


def audit(t, e):
    x, y, z = e['x'] + 0.5, e['y'] + 1.6, e['z'] + 0.5
    yaw = math.radians(e['yaw'])
    fx, fz = -math.sin(yaw), math.cos(yaw)                 # Minecraft: yaw 0 faces +z, 90 faces -x
    level = total = level_open = total_open = front = front_open = 0
    shut = collections.Counter()
    front_shut = collections.Counter()
    for a in range(-75, 76, 5):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        dx, dz = fx * ca - fz * sa, fz * ca + fx * sa
        for p in range(-35, 11, 5):
            cp, sp = math.cos(math.radians(p)), math.sin(math.radians(p))
            blocked = None
            d = 1.0
            while d <= 12.0:
                px, py, pz = x + dx * cp * d, y + sp * d, z + dz * cp * d
                bx, by, bz = math.floor(px), math.floor(py), math.floor(pz)
                if (bx, bz) != (e['x'], e['z']):
                    nm = name(t.get(bx, by, bz))
                    if not soft(nm) and not (by < 64 and nm in ('dirt', 'stone', 'grass_block', 'deepslate', 'gravel', 'sand')):
                        blocked = nm
                        break
                d += 0.25
            total += 1
            total_open += blocked is None
            if p >= -5:
                level += 1
                level_open += blocked is None
                if blocked:
                    shut[blocked] += 1
                if abs(a) <= 45:
                    front += 1
                    front_open += blocked is None
                    if blocked:
                        front_shut[blocked] += 1
    return dict(post=e['post'], x=e['x'], y=e['y'], z=e['z'], yaw=e['yaw'], level_open=round(level_open / level, 3),
                all_open=round(total_open / total, 3), front_open=round(front_open / front, 3), shut=dict(shut.most_common(6)),
                front_shut=dict(front_shut.most_common(6)))


def ahead_open(t, e, yaw=None, half=25, reach=12):
    """The share of the rays straight ahead (within `half` degrees of the facing, from 5 below level to 10 above) that
    get through, for the post's yaw or the one given."""
    x, y, z = e['x'] + 0.5, e['y'] + 1.6, e['z'] + 0.5
    a0 = math.radians(e['yaw'] if yaw is None else yaw)
    fx, fz = -math.sin(a0), math.cos(a0)
    n = ok = 0
    for a in range(-half, half + 1, 5):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        dx, dz = fx * ca - fz * sa, fz * ca + fx * sa
        for p in range(-5, 11, 5):
            cp, sp = math.cos(math.radians(p)), math.sin(math.radians(p))
            d, blocked = 1.0, False
            while d <= reach:
                bx, by, bz = math.floor(x + dx * cp * d), math.floor(y + sp * d), math.floor(z + dz * cp * d)
                if (bx, bz) != (e['x'], e['z']):
                    nm = name(t.get(bx, by, bz))
                    if not soft(nm) and not (by < 64 and nm in ('dirt', 'stone', 'grass_block', 'deepslate', 'gravel', 'sand')):
                        blocked = True
                        break
                d += 0.25
            n += 1
            ok += not blocked
    return ok / n


if __name__ == '__main__':
    t = template_io.Template(sys.argv[1])
    g = json.load(open(os.path.join(sys.argv[1], 'garrison.json')))
    rows = [audit(t, e) for e in g['entries'] if e.get('vehicle') and e.get('post') in POSTS]
    by = collections.defaultdict(list)
    for r in rows:
        by[r['post']].append(r)
    summary = {k: dict(n=len(v), front_open=round(sum(r['front_open'] for r in v) / len(v), 3),
                       front_worst=round(min(r['front_open'] for r in v), 3),
                       level_open=round(sum(r['level_open'] for r in v) / len(v), 3),
                       worst=round(min(r['level_open'] for r in v), 3), all_open=round(sum(r['all_open'] for r in v) / len(v), 3))
               for k, v in by.items()}
    print(json.dumps(summary, indent=1))
    if len(sys.argv) > 2:
        json.dump(dict(summary=summary, posts=rows), open(sys.argv[2], 'w'), indent=1)

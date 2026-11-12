"""lanes.py <template dir> <garrison.json> [muzzle heights...]: for each still turret post, how much of the ground outside
it can its gun see: rays from the muzzle (post + h, the post's centre) to ground points (terrain top + 1) at 12..128 blocks
in 7 directions across its outward half; a ray is blocked by any solid block on the way (sampled every 0.2)."""
import sys, json, math, collections
sys.path.insert(0, '/home/user/Blank-Baby/oror_rework/neoforge1211patch/tools/citadel')
from template_io import Template
t = Template(sys.argv[1])
g = json.load(open(sys.argv[2]))
hs = [float(h) for h in sys.argv[3:]] or [2.0]
FWD = float(__import__("os").environ.get("FWD", "0"))
SOFT = ('air', 'grass', 'fern', 'flower', 'torch', 'lantern', 'carpet', 'button', 'plate', 'rail', 'banner', 'sign', 'snow', 'cobweb', 'vine', 'wheat', 'carrots', 'potatoes', 'beetroots', 'leaves', 'water', 'light')
cache = {}
def solid(x, y, z):
    k = (x, y, z)
    if k not in cache:
        s = t.get(x, y, z)
        n = '' if s is None else s.split(':')[1].split('[')[0]
        cache[k] = s is not None and not any(w in n for w in SOFT) and n not in ('tall_grass', 'short_grass') and 'slab' not in n or (n.endswith('_slab') and 'bottom' not in s)
    return cache[k]
def ground(x, z):
    for y in range(95, 60, -1):
        if solid(x, y, z):
            return y + 1
    return 65
def clear(a, b, skip):
    d = [b[i] - a[i] for i in range(3)]
    L = math.sqrt(sum(v * v for v in d))
    n = int(L / 0.2)
    for i in range(1, n):
        f = i / n
        p = [a[j] + d[j] * f for j in range(3)]
        bx, by, bz = math.floor(p[0]), math.floor(p[1]), math.floor(p[2])
        if abs(bx - a[0]) <= skip and abs(bz - a[2]) <= skip and by <= a[1]:
            continue
        if solid(bx, by, bz):
            return False
    return True
res = collections.defaultdict(lambda: collections.defaultdict(list))
for e in g['entries']:
    if not e.get('vehicle') or not e.get('still'):
        continue
    x, y, z = e['x'] + 0.5, e['y'], e['z'] + 0.5
    yaw = math.radians(e['yaw'])
    fx, fz = -math.sin(yaw), math.cos(yaw)       # minecraft yaw: facing
    for h in hs:
        ok = tot = 0
        for da in (-60, -40, -20, 0, 20, 40, 60):
            a = math.atan2(fz, fx) + math.radians(da)
            for dist in (12, 20, 32, 48, 64, 96, 128):
                tx, tz = x + math.cos(a) * dist, z + math.sin(a) * dist
                ty = ground(math.floor(tx), math.floor(tz)) + 0.9
                tot += 1
                ok += clear((x + fx * FWD, y + h, z + fz * FWD), (tx, ty, tz), 2)
        res[e['post']][h].append(ok / tot)
for post, d in res.items():
    print(post, '  '.join('h%.1f: mean %.2f, blind(<10%%) %d/%d' % (h, sum(v) / len(v), sum(1 for q in v if q < 0.1), len(v)) for h, v in sorted(d.items())))

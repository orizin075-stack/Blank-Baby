"""gunports.py <template dir> [report.json]: the guns given a field of fire (059e, the user: "aren't the turrets blocked
by the wall?"). Run after turrets.py.

They were: tools/lanes.py-style rays from each gun's muzzle to the ground about it found the 96 wall batteries saw
none of the ground outside (they stood nine blocks inside a parapet two blocks high with merlons above), the 24
casemate guns none (they stood inside the casemates' halls, walls three thick all round), the redoubts' guns a fifth of
it (a low parapet round the deck's edge hid the ground within sixty blocks). Now:
* a wall battery moves forward to the walk's outer edge and the parapet before it is cut away seven wide (an
  embrasure): its gun looks out over the wall's foot;
* a casemate gun moves up to the hall's outer wall and a port seven wide and four high is opened through it before
  the gun;
* a redoubt's gun stands on a platform two blocks high at the deck's middle, over the deck's rim.
The posts' guards and supply stay as they were where they still fit (a guard on the gun's new floor steps aside).
"""
import sys, os, json, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anvil
import template_io
from turrets import is_air, solid, YAW

AIR = 'minecraft:air'


def facing(yaw):
    """The axis a post's yaw looks along (minecraft: south 0, west 90, north 180, east -90)."""
    a = math.radians(yaw)
    fx, fz = -math.sin(a), math.cos(a)
    return (int(round(fx)), 0) if abs(fx) >= abs(fz) else (0, int(round(fz)))


class Ports:
    def __init__(self, t):
        self.t = t
        self.stats = collections.Counter()

    def top(self, x, z, y0=60, y1=130):
        return next((y for y in range(y1, y0 - 1, -1) if not is_air(self.t.get(x, y, z))), y0 - 1)

    def clear_floor(self, cx, y, cz, r=2, high=4):
        """A (2r+1)^2 floor at y - 1 with room above it."""
        return all(solid(self.t.get(cx + i, y - 1, cz + j)) and all(is_air(self.t.get(cx + i, yy, cz + j)) for yy in range(y, y + high))
                   for i in range(-r, r + 1) for j in range(-r, r + 1))

    def step_aside(self, garrison, e, cx, y, cz):
        for g in garrison:
            if g is e or g.get('vehicle'):
                continue
            if abs(g['x'] - cx) <= 2 and abs(g['z'] - cz) <= 2 and abs(g['y'] - y) <= 2:
                for d in range(3, 9):
                    for sx, sz in ((d, 0), (-d, 0), (0, d), (0, -d)):
                        x, z = cx + sx, cz + sz
                        if solid(self.t.get(x, y - 1, z)) and is_air(self.t.get(x, y, z)) and is_air(self.t.get(x, y + 1, z)):
                            g['x'], g['y'], g['z'] = x, y, z
                            self.stats['guards stepped aside'] += 1
                            break
                    else:
                        continue
                    break

    # -------------------------------------------------------------------------------------------- wall batteries

    KEEP = ('chest', 'hopper', 'charging_station', 'barrel', 'lantern')

    def bes_in(self, x0, x1, y0, y1, z0, z1):
        """Block entities in the box as they stand after this run's moves (the template's own list holds them as loaded)."""
        out = [b for b in self.t.block_entities_in(x0, x1, y0, y1, z0, z1)
               if (b[0], b[1], b[2]) not in self.t.edited.get((b[0] >> 4, b[2] >> 4), set())]
        for m in self.t.new_bes.values():
            for (bx, by, bz), d in m.items():
                if x0 <= bx <= x1 and y0 <= by <= y1 and z0 <= bz <= z1:
                    out.append((bx, by, bz, d))
        return out

    def move_group(self, group, sx, y, sz):
        datas = {(q[0], q[1], q[2]): {k: v for k, v in q[3].items() if k not in ('x', 'y', 'z', 'keepPacked')}
                 for q in self.bes_in(group[0][0], group[0][0], group[0][1], group[-1][1], group[0][2], group[0][2])}
        for k, (gx, gy, gz) in enumerate(group):
            st = self.t.get(gx, gy, gz)
            self.t.set(gx, gy, gz, AIR)
            self.t.set(sx, y + k, sz, st)
            if (gx, gy, gz) in datas:
                self.t.set_be(sx, y + k, sz, datas[(gx, gy, gz)])

    def clear_above(self, px, y, pz, high):
        n = 0
        for yy in range(y, y + high):
            st = self.t.get(px, yy, pz)
            if not is_air(st) and not any(k in st for k in self.KEEP):
                self.t.set(px, yy, pz, AIR)
                n += 1
        return n

    def battery(self, e, garrison):
        x, y, z = e['x'], e['y'], e['z']
        ox, oz = facing(e['yaw'])
        lx, lz = -oz, ox
        walk = y - 1
        # the floor's outer edge along the gun's facing (what stands on the floor is cleared below: a parapet, a
        # tower's ring of pillars)
        edge = 0
        while edge < 20 and solid(self.t.get(x + ox * (edge + 1), walk, z + oz * (edge + 1))):
            edge += 1
        best = None
        for back in (2, 3):
            for side in (0, 1, -1, 2, -2, 3, -3):
                cx, cz = x + ox * (edge - back) + lx * side, z + oz * (edge - back) + lz * side
                if all(solid(self.t.get(cx + i, walk, cz + j)) for i in range(-2, 3) for j in range(-2, 3)):
                    best = (cx, cz, back)
                    break
            if best:
                break
        if best is None:
            best = (x, z, edge)
            self.stats['battery left where it was (no floor at the edge)'] += 1
        cx, cz, back = best
        cut = 0
        # room for the gun, and the way before it: everything at its height, seven wide, from its back to past the
        # floor's edge (the parapet beyond the floor too)
        for s in range(-3, 4):
            for d in range(-2, back + 4):
                cut += self.clear_above(cx + ox * d + lx * s, y, cz + oz * d + lz * s, 5 if d > 2 else 4)
        self.stats['battery blocks cleared'] += cut
        self.supply(e, x, z, cx, y, cz, ox, oz, lx, lz)
        self.stats['batteries at the edge'] += 1
        self.stats['battery moved by'] += abs(cx - x) + abs(cz - z)
        e['x'], e['z'] = cx, cz
        self.step_aside(garrison, e, cx, y, cz)

    def supply(self, e, x, z, cx, y, cz, ox, oz, lx, lz):
        """The gun's charging station (with its hopper and coal chest) within eight blocks of it and its ammunition chest
        within ten: brought behind it on the walk when the move left them further."""
        bes = self.bes_in(x - 13, x + 13, y - 3, y + 6, z - 13, z + 13)
        groups = []
        for bx, by, bz, d in bes:
            kind = anvil.val(d['id'])
            far = (bx - cx) ** 2 + (by - y) ** 2 + (bz - cz) ** 2
            if kind == 'superbwarfare:charging_station' and far > 7.5 ** 2:
                groups.append([(bx, by + k, bz) for k in range(3) if not is_air(self.t.get(bx, by + k, bz))
                               and (k == 0 or 'hopper' in self.t.get(bx, by + k, bz) or 'chest' in self.t.get(bx, by + k, bz))])
            elif kind == 'minecraft:chest' and '弾薬庫' in str(anvil.val(d.get('CustomName', ''))) and far > 9.5 ** 2:
                groups.append([(bx, by, bz)])
        if not groups:
            return
        spots = [(cx - ox * b + lx * s, cz - oz * b + lz * s) for b in (4, 5, 3, 6) for s in (0, 2, -2, 3, -3, 1, -1)]
        for group in groups:
            if not group:
                continue
            for sx, sz in spots:
                if solid(self.t.get(sx, y - 1, sz)) and all(is_air(self.t.get(sx, y + k, sz)) for k in range(len(group) + 1)):
                    self.move_group(group, sx, y, sz)
                    spots.remove((sx, sz))
                    self.stats['battery supply brought behind its gun'] += 1
                    break
            else:
                self.stats['battery supply without a place'] += 1

    # -------------------------------------------------------------------------------------------- casemates

    def clear_front(self, x, y, z, ox, oz, lx, lz, depth):
        """The supply standing before a gun (its charging station with hopper and coal chest, its ammunition chest) moved
        behind it, out of its line of fire."""
        groups = []
        for bx, by, bz, d in self.bes_in(x - depth - 1, x + depth + 1, y, y + 3, z - depth - 1, z + depth + 1):
            fwd = (bx - x) * ox + (bz - z) * oz
            lat = (bx - x) * lx + (bz - z) * lz
            if 0 < fwd <= depth and abs(lat) <= 3 and by == y:
                groups.append([(bx, y + k, bz) for k in range(3) if not is_air(self.t.get(bx, y + k, bz))
                               and any(w in self.t.get(bx, y + k, bz) for w in self.KEEP)])
        for group in groups:
            if not group:
                continue
            for b in (3, 4, 5, 2):
                done = False
                for side in (2, -2, 3, -3, 4, -4, 0):
                    sx, sz = x - ox * b + lx * side, z - oz * b + lz * side
                    if solid(self.t.get(sx, y - 1, sz)) and all(is_air(self.t.get(sx, y + k, sz)) for k in range(len(group) + 1)):
                        self.move_group(group, sx, y, sz)
                        self.stats['casemate supply moved behind its gun'] += 1
                        done = True
                        break
                if done:
                    break

    def casemate(self, e, garrison):
        x, y, z = e['x'], e['y'], e['z']
        ox, oz = facing(e['yaw'])
        lx, lz = -oz, ox
        self.clear_front(x, y, z, ox, oz, lx, lz, 12)
        # the hall's outer wall before the gun: its inner face, its thickness
        k = 1
        while k < 20 and is_air(self.t.get(x + ox * k, y + 1, z + oz * k)):
            k += 1
        if k >= 20:
            self.stats['casemate: no wall before it'] += 1
            return
        inner = k
        while k < inner + 6 and not is_air(self.t.get(x + ox * k, y + 1, z + oz * k)):
            k += 1
        thick = k - inner
        if thick >= 6:
            self.stats['casemate: wall too thick'] += 1
            return
        cx, cz = x + ox * (inner - 2), z + oz * (inner - 2)
        if not self.clear_floor(cx, y, cz, r=1, high=3):
            cx, cz = x + ox * max(0, inner - 3), z + oz * max(0, inner - 3)
        cut = 0
        for s in range(-3, 4):
            for d in range(inner, inner + thick):
                px, pz = x + ox * d + lx * s, z + oz * d + lz * s
                for yy in range(y, y + 4):
                    if not is_air(self.t.get(px, yy, pz)):
                        self.t.set(px, yy, pz, AIR)
                        cut += 1
            # the port's sill: the floor carried through it
            for d in range(inner, inner + thick):
                px, pz = x + ox * d + lx * s, z + oz * d + lz * s
                if is_air(self.t.get(px, y - 1, pz)):
                    self.t.set(px, y - 1, pz, 'minecraft:polished_deepslate')
        self.stats['casemate wall blocks cut'] += cut
        self.stats['casemates given ports'] += 1
        self.supply(e, x, z, cx, y, cz, ox, oz, lx, lz)
        e['x'], e['z'] = cx, cz
        self.step_aside(garrison, e, cx, y, cz)

    # -------------------------------------------------------------------------------------------- redoubts

    def redoubt(self, e):
        x, y, z = e['x'], e['y'], e['z']
        # a gun platform two blocks high at the deck's middle: the gun looks down over the deck's rim (the rim, the
        # redoubt's grey crown, stays)
        n = 0
        for i in range(-2, 3):
            for j in range(-2, 3):
                for yy in (y, y + 1):
                    if is_air(self.t.get(x + i, yy, z + j)):
                        self.t.set(x + i, yy, z + j, 'minecraft:polished_blackstone_bricks' if yy == y else 'minecraft:polished_deepslate')
                        n += 1
        e['y'] = y + 2
        self.stats['redoubt platform blocks'] += n
        self.stats['redoubts raised'] += 1

    def run(self, garrison):
        entries = garrison['entries']
        for e in entries:
            if e.get('post') == 'battery':
                self.battery(e, entries)
            elif e.get('post') == 'casemate':
                self.casemate(e, entries)
            elif e.get('post') == 'redoubt':
                self.redoubt(e)
        return self.stats


if __name__ == '__main__':
    folder = sys.argv[1]
    t = template_io.Template(folder)
    gp = os.path.join(folder, 'garrison.json')
    g = json.load(open(gp))
    stats = Ports(t).run(g)
    stats['chunks saved'] = t.save(folder)
    json.dump(g, open(gp, 'w'), indent=0)
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    if len(sys.argv) > 2:
        json.dump(stats, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)

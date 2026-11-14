"""blindports.py <template dir> <template before gunports> [report.json]: the casemate guns that face a wall of their own
taken up onto the wall walk above them (059f, the user: "砲台の前の壁消し切れてない 全部見直し"). Run after fieldfire.py.

fieldfire.py opened every gun's front, but rays past the casemates' ports (fire_audit) found the eight casemates of the
outermost wall, two beside each of its four gates, looking at their gate's flanking tower five blocks off: twenty
blocks of tower from the ground to twenty blocks up, filling 77 to 85 hundredths of the field beyond the port, and no
aim from the port clears it (the best, turned 30 to 50 degrees, sees about half). So each of them now:
* stands on the outer wall's walk above it, at the wall batteries' height (a wall battery: gunports.Ports.battery puts it at the walk's outer
  edge, fieldfire.Fronts.battery_front opens the parapet before it; one standing inside a tall tower's ring is given
  an embrasure through the ring's wall), where it looks out over the gate towers' roofs;
* faces straight out from the wall;
* has its charging station (with its hopper and coal chest) and its ammunition chest brought up behind it;
* leaves its port in the outermost wall closed again as the wall was before 059e cut it (from the template before
  gunports.py), so the wall at the gates has no hole at the foot.
A casemate whose field past the port is half open or more stays where it is.
"""
import sys, os, json, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anvil
import template_io
from turrets import is_air, solid
from gunports import facing
from fieldfire import Fronts, KEEP


def beyond(t, x, y, z, yaw, start=7, reach=30, half=30):
    """The share of a 60-degree fan of level rays from the gun's muzzle, from start to reach blocks out, that meets
    nothing solid (what lies past the gun's own wall)."""
    total = clear = 0
    for dy in range(-half, half + 1, 5):
        b = math.radians(yaw + dy)
        dx, dz = -math.sin(b), math.cos(b)
        for pitch in (0, 5):
            pr = math.radians(pitch)
            total += 1
            ok = True
            for s in range(start * 2, reach * 2):
                d = s * 0.5
                st = t.get(math.floor(x + 0.5 + dx * d * math.cos(pr)), math.floor(y + 1.6 + math.sin(pr) * d),
                           math.floor(z + 0.5 + dz * d * math.cos(pr)))
                if solid(st) and 'leaves' not in st:
                    ok = False
                    break
            clear += ok
    return clear / total


class Blind(Fronts):
    def __init__(self, t, old):
        super().__init__(t)
        self.old = old

    def supply(self, *args):
        """Not the battery's search for supply about it (on the walk it found the neighbouring batteries' and took
        them): the gun's own is brought up from its hall (bring_up)."""

    def walk_above(self, x, z, walk, ox, oz):
        """Where the gun stands on the walk (its floor at walk - 1): straight above it, or the nearest place on the walk
        a few blocks in from the wall's face or to either side of it (above some of them stands the wall's core)."""
        lx, lz = -oz, ox
        for back in range(0, 9):
            for side in (0, 1, -1, 2, -2, 3, -3, 4, -4):
                px, pz = x - ox * back + lx * side, z - oz * back + lz * side
                if solid(self.t.get(px, walk - 1, pz)) and all(is_air(self.t.get(px, walk + k, pz)) for k in range(3)):
                    return px, pz
        return None

    def close_port(self, x, y, z, ox, oz):
        """The port and its splay as the wall was before gunports.py: whatever stood there then and is air now."""
        lx, lz = -oz, ox
        n = 0
        for d in range(1, 9):
            for s in range(-12, 13):
                for yy in range(y - 1, y + 6):
                    px, pz = x + ox * d + lx * s, z + oz * d + lz * s
                    was = self.old.get(px, yy, pz)
                    if solid(was) and not any(k in was for k in KEEP) and is_air(self.t.get(px, yy, pz)):
                        self.t.set(px, yy, pz, was)
                        n += 1
        return n

    def supply_groups(self, x, y, z):
        """The gun's charging station (with the hopper and chest stacked on it) and its ammunition chest, near it."""
        groups = []
        for bx, by, bz, d in self.bes_in(x - 9, x + 9, y - 2, y + 4, z - 9, z + 9):
            kind = anvil.val(d['id'])
            if kind == 'superbwarfare:charging_station':
                groups.append([(bx, by + k, bz) for k in range(3) if not is_air(self.t.get(bx, by + k, bz))
                               and (k == 0 or 'hopper' in self.t.get(bx, by + k, bz) or 'chest' in self.t.get(bx, by + k, bz))])
            elif kind == 'minecraft:chest' and '弾薬庫' in str(anvil.val(d.get('CustomName', ''))):
                groups.append([(bx, by, bz)])
        return [g for g in groups if g]

    def bring_up(self, groups, cx, wy, cz, ox, oz):
        lx, lz = -oz, ox
        spots = [(cx - ox * b + lx * s, cz - oz * b + lz * s) for b in (4, 5, 3, 6) for s in (0, 2, -2, 3, -3, 1, -1)]
        for group in groups:
            for sx, sz in spots:
                if solid(self.t.get(sx, wy - 1, sz)) and all(is_air(self.t.get(sx, wy + k, sz)) for k in range(len(group) + 1)):
                    self.move_group(group, sx, wy, sz)
                    spots.remove((sx, sz))
                    self.stats['supply brought up behind the gun'] += 1
                    break
            else:
                self.stats['supply without a place on the walk'] += 1

    def run_blind(self, garrison):
        entries = garrison['entries']
        # the walls' walk: where the wall batteries stand (all at one height)
        heights = collections.Counter(e['y'] for e in entries if e.get('post') == 'battery' and e.get('vehicle'))
        walk = heights.most_common(1)[0][0]
        for e in entries:
            if e.get('post') != 'casemate' or not e.get('vehicle'):
                continue
            x, y, z, yaw = e['x'], e['y'], e['z'], e['yaw']
            seen = beyond(self.t, x, y, z, yaw)
            if seen >= 0.5:
                continue
            ox, oz = facing(yaw)
            at = self.walk_above(x, z, walk, ox, oz)
            if at is None:
                self.stats['blind casemate without a walk above'] += 1
                continue
            wy = walk
            groups = self.supply_groups(x, y, z)
            self.stats['port blocks put back'] += self.close_port(x, y, z, ox, oz)
            e['x'], e['y'], e['z'] = at[0], wy, at[1]
            e['yaw'] = {(0, 1): 0.0, (-1, 0): 90.0, (0, -1): 180.0, (1, 0): -90.0}[(ox, oz)]
            e['post'] = 'battery'
            self.battery(e, entries)
            self.battery_front(e)
            self.bring_up(groups, e['x'], wy, e['z'], ox, oz)
            after = beyond(self.t, e['x'], e['y'], e['z'], e['yaw'], start=3)
            if after < 0.5:
                # a gun that stands inside a tall tower's ring on the walk: an embrasure through the ring's wall
                # before it, 70 degrees wide and five high (the tower stands on above it)
                self.stats['embrasures through a tower wall'] += 1
                self.stats['embrasure blocks cut'] += self.wedge(e['x'], wy, e['z'], ox, oz, 9, 5, start=1, half=35, tower_above=None)
                after = beyond(self.t, e['x'], e['y'], e['z'], e['yaw'], start=3)
            self.stats['casemates taken up onto the walk'] += 1
            self.report.append({'vehicle': e['vehicle'], 'from': [x, y, z], 'to': [e['x'], e['y'], e['z']], 'yaw': e['yaw'],
                                'before': round(seen, 2), 'after': round(after, 2)})
        return self.stats


if __name__ == '__main__':
    folder, before = sys.argv[1], sys.argv[2]
    t = template_io.Template(folder)
    old = template_io.Template(before)
    gp = os.path.join(folder, 'garrison.json')
    g = json.load(open(gp))
    b = Blind(t, old)
    b.report = []
    stats = b.run_blind(g)
    stats['chunks saved'] = t.save(folder)
    json.dump(g, open(gp, 'w'), indent=0)
    out = dict(stats)
    out['moved'] = b.report
    print(json.dumps(out, ensure_ascii=False, indent=1))
    if len(sys.argv) > 3:
        json.dump(out, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)

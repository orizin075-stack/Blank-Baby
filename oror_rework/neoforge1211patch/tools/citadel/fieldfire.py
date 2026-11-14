"""fieldfire.py <template dir> [report.json]: the guns' fronts cleared whole and the anti-aircraft guns' fields made
ground (059f, the user: "砲台の前の壁消し切れてない 全部見直し", "畑に塔があったりするの何とかして 置くんだったらその場所
から畑をなくして"). Run after gunports.py.

gunports.py (059e) cut each wall battery a gap seven blocks wide in the parapet and each casemate a port seven wide; a
gun turns far wider than that, and rays from the muzzles (fire_audit) found a battery's field of fire still a quarter
shut by the parapet and merlons on either side of its gap, a casemate's two thirds shut by the sides of its port, the
crossfire posts' (anti-tank guns by the gate roads) half shut by their own emplacement's front, and the anti-aircraft
guns' own ammunition chest, hopper and charging station standing before their muzzles; six of the sixteen
anti-aircraft guns stood in a wheat, carrot or beetroot field. Now:
* a wall battery's front is open over a wedge of 150 degrees out to nine blocks: the parapet and merlons there are
  taken down to the walk (a tower or a building, anything going on up above the merlons' height, stays);
* a casemate's port opens outward, wider by three blocks each block through the wall (splayed), five high;
* a crossfire post's emplacement front is opened the same way, out to six blocks;
* each post's supply standing before its gun (within eight blocks ahead, three to either side) moves behind it;
* an anti-aircraft gun in a field stands on a stone pad nine across: the farmland under it is paved and the crops on
  it gone, the field's water channels across the pad paved too (the field round about stays, with its own water).
"""
import sys, os, json, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_io
from turrets import is_air, solid
from gunports import Ports, facing

AIR = 'minecraft:air'
KEEP = ('chest', 'hopper', 'charging_station', 'barrel', 'lantern', 'campfire', 'bell')
CROPS = ('wheat', 'carrots', 'potatoes', 'beetroots', 'melon_stem', 'pumpkin_stem', 'attached_', 'sweet_berry')
PAD = 'minecraft:stone_bricks'
PAD_EDGE = 'minecraft:polished_andesite'


def name(st):
    return st.split('[')[0].split(':')[-1]


class Fronts(Ports):
    def __init__(self, t):
        super().__init__(t)

    def wedge(self, x, y, z, ox, oz, reach, high, start=1, half=75, tower_above=None):
        """Every block before the gun within `half` degrees of its facing, from `start` to `reach` blocks ahead, at the
        gun's height up to `high` above: taken away (not the gun's own supply, nor a block of something that goes on up
        past `tower_above`)."""
        lx, lz = -oz, ox
        tan = math.tan(math.radians(half))
        cut = 0
        for d in range(start, reach + 1):
            w = int(math.floor(1.5 + d * tan))
            for s in range(-w, w + 1):
                if math.hypot(d, s) > reach + 0.5:
                    continue
                px, pz = x + ox * d + lx * s, z + oz * d + lz * s
                if tower_above is not None and not is_air(self.t.get(px, y + tower_above, pz)):
                    continue
                for yy in range(y, y + high):
                    st = self.t.get(px, yy, pz)
                    if not is_air(st) and not any(k in st for k in KEEP):
                        self.t.set(px, yy, pz, AIR)
                        cut += 1
        return cut

    def battery_front(self, e):
        x, y, z = e['x'], e['y'], e['z']
        ox, oz = facing(e['yaw'])
        self.clear_front(x, y, z, ox, oz, -oz, ox, 8)
        # the parapet and merlons over the walk, not a tower (whatever stands six above the walk goes on up)
        self.stats['battery front blocks taken down'] += self.wedge(x, y, z, ox, oz, 9, 5, start=1, half=75, tower_above=6)
        self.stats['batteries opened'] += 1

    def casemate_front(self, e):
        x, y, z = e['x'], e['y'], e['z']
        ox, oz = facing(e['yaw'])
        lx, lz = -oz, ox
        self.clear_front(x, y, z, ox, oz, lx, lz, 8)
        # the hall's outer wall before the gun, its inner face and thickness read just beside its port (the port, seven
        # wide, is already cut through it on the gun's own line)
        sx, sz = x + lx * 4, z + lz * 4
        k = 1
        while k < 14 and is_air(self.t.get(sx + ox * k, y + 1, sz + oz * k)):
            k += 1
        if k >= 14:
            self.stats['casemate: no wall found beside its port'] += 1
            return
        inner = k
        while k < inner + 8 and not is_air(self.t.get(sx + ox * k, y + 1, sz + oz * k)):
            k += 1
        outer = k
        cut = 0
        for d in range(inner, outer + 1):
            w = int(3 + 1.5 * (d - inner + 1))
            for s in range(-w, w + 1):
                px, pz = x + ox * d + lx * s, z + oz * d + lz * s
                for yy in range(y, y + 5):
                    st = self.t.get(px, yy, pz)
                    if not is_air(st) and not any(kk in st for kk in KEEP):
                        self.t.set(px, yy, pz, AIR)
                        cut += 1
                if is_air(self.t.get(px, y - 1, pz)) and d < outer:
                    self.t.set(px, y - 1, pz, 'minecraft:polished_deepslate')
        self.stats['casemate port blocks splayed'] += cut
        self.stats['casemates splayed'] += 1

    def crossfire_front(self, e):
        x, y, z = e['x'], e['y'], e['z']
        ox, oz = facing(e['yaw'])
        self.clear_front(x, y, z, ox, oz, -oz, ox, 8)
        self.stats['crossfire front blocks taken down'] += self.wedge(x, y, z, ox, oz, 6, 4, start=1, half=70, tower_above=5)
        self.stats['crossfire posts opened'] += 1

    def aa_ground(self, e):
        x, y, z = e['x'], e['y'], e['z']
        ox, oz = facing(e['yaw'])
        self.clear_front(x, y, z, ox, oz, -oz, ox, 8)
        crops = 0
        for i in range(-4, 5):
            for j in range(-4, 5):
                for yy in (y - 1, y - 2):
                    st = self.t.get(x + i, yy, z + j)
                    if name(st) == 'farmland':
                        self.t.set(x + i, yy, z + j, PAD_EDGE if max(abs(i), abs(j)) == 4 else PAD)
                        crops += 1
                        above = self.t.get(x + i, yy + 1, z + j)
                        if any(c in name(above) for c in CROPS):
                            self.t.set(x + i, yy + 1, z + j, AIR)
        if crops:
            # the field's water channels crossing the pad: paved too (the field round about keeps its own)
            for i in range(-4, 5):
                for j in range(-4, 5):
                    if name(self.t.get(x + i, y - 1, z + j)) == 'water':
                        self.t.set(x + i, y - 1, z + j, PAD_EDGE if max(abs(i), abs(j)) == 4 else PAD)
                        self.stats['water channel blocks paved under them'] += 1
            self.stats['anti-aircraft guns taken out of fields'] += 1
            self.stats['farmland paved under them'] += crops

    def run(self, garrison):
        for e in garrison['entries']:
            if not e.get('vehicle'):
                continue
            post = e.get('post')
            if post == 'battery':
                self.battery_front(e)
            elif post == 'casemate':
                self.casemate_front(e)
            elif post == 'crossfire':
                self.crossfire_front(e)
            elif post == 'aa':
                self.aa_ground(e)
        return self.stats


if __name__ == '__main__':
    folder = sys.argv[1]
    t = template_io.Template(folder)
    gp = os.path.join(folder, 'garrison.json')
    g = json.load(open(gp))
    stats = Fronts(t).run(g)
    stats['chunks saved'] = t.save(folder)
    json.dump(g, open(gp, 'w'), indent=0)
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    if len(sys.argv) > 2:
        json.dump(stats, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)

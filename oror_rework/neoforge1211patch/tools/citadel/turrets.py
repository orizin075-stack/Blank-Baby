"""turrets.py <template dir> [report.json]: the kingdom's guns outside the town set where guns can fight (059d, the user:
the turrets outside the walls had gone strange).

Until 059c, by the posts military.py took from the castle's manifest:
* the 96 wall batteries stood on the grass at the outer wall's outer foot, under its stone balconies seventeen blocks up,
  where nothing could be fired over the wall nor at anything coming to it, their ammunition chest and (an HPJ-11's)
  charging station up on the balcony out of reach;
* the 16 outer redoubts' guns, and the two guards of each, stood at the bottom of the redoubt's well: a pit nine across
  and seven deep with no way in or out;
* the 16 anti-tank posts by the gate roads faced away from the castle, into their own side wall, not across the road.

Now:
* each wall battery stands on the outer wall's walk (the broad top behind the merlons) at the nearest stretch where its
  gun has room (five by five of flat walk, open sky), its ammunition chest and charging station (with its hopper and
  coal chest) brought up beside it; a guard of the walk standing where the gun now is steps aside;
* each redoubt's well is floored over at the top of its walls (the gun and the guards stand on the deck, behind the
  parapet), the well below is the redoubt's store room: a passage through its wall on the castle's side (a step up from
  the field) and a stair along the room's side up through the deck;
* each anti-tank post faces across its road.
The garrison table (garrison.json) follows; a world built before gets all of it through CitadelUpdate (update.bin):
the old guns away from any post retire with their crews, and each new post gets its gun and gunner.
"""
import sys, os, json, collections, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anvil
import template_io

AIRS = ('minecraft:air', 'minecraft:cave_air', 'minecraft:light[', 'minecraft:light')
SOFT = ('short_grass', 'tall_grass', 'fern', 'flower', 'torch', 'lantern', 'carpet', 'button', 'pressure_plate', 'rail',
        'banner', 'sign', 'snow', 'cobweb', 'vine')
DIRS = {(1, 0): 'east', (-1, 0): 'west', (0, 1): 'south', (0, -1): 'north'}
YAW = {(0, 1): 0.0, (-1, 0): 90.0, (0, -1): 180.0, (1, 0): -90.0}
STEP = 'minecraft:polished_blackstone_brick_stairs[facing=%s,half=bottom,shape=straight,waterlogged=false]'
FILL = 'minecraft:polished_blackstone_bricks'
DECK = 'minecraft:polished_deepslate'


def is_air(s):
    return s is None or s == 'minecraft:air' or s == 'minecraft:cave_air' or s.split('[')[0] == 'minecraft:light'


def solid(s):
    return not is_air(s) and not any(k in s for k in SOFT)


class Turrets:
    def __init__(self, t):
        self.t = t
        self.stats = collections.Counter()
        self.tops = {}

    def top(self, x, z):
        k = (x, z)
        if k not in self.tops:
            self.tops[k] = next((y for y in range(130, 63, -1) if not is_air(self.t.get(x, y, z))), 63)
        return self.tops[k]

    def put(self, x, y, z, s):
        self.t.set(x, y, z, s)

    # ------------------------------------------------------------------------------------------------ wall batteries

    def walk_spot(self, x, z, r=2):
        """The nearest point of the outer wall's walk to a battery post at x, z: flat (r around) with sky over it."""
        ux, uz = ((-1 if x > 0 else 1), 0) if abs(x) >= abs(z) else (0, (-1 if z > 0 else 1))
        vx, vz = -uz, ux
        found = []
        for dv in sorted(range(-16, 17), key=abs):
            band = [d for d in range(0, 32) if self.top(x + ux * d + vx * dv, z + uz * d + vz * dv) >= 90]
            if not band:
                continue
            mid = (band[0] + band[-1]) / 2
            for d in band:
                px, pz = x + ux * d + vx * dv, z + uz * d + vz * dv
                w = self.top(px, pz)
                ok = all(self.top(px + i, pz + j) == w for i in range(-r, r + 1) for j in range(-r, r + 1))
                if ok and all(is_air(self.t.get(px + i, y, pz + j)) for i in range(-r, r + 1) for j in range(-r, r + 1)
                              for y in range(w + 1, w + 5)):
                    found.append((abs(dv) + abs(d - mid) * 0.5, px, w + 1, pz))
            if found and abs(dv) > min(f[0] for f in found):
                break
        if not found:
            return None, (ux, uz), (vx, vz)
        return min(found)[1:], (ux, uz), (vx, vz)

    def free_on_walk(self, px, y, pz, taken, cands):
        for cx, cz in cands:
            if (cx, cz) in taken:
                continue
            if self.top(cx, cz) == y - 1 and all(is_air(self.t.get(cx, yy, cz)) for yy in range(y, y + 3)):
                return cx, cz
        return None

    def battery(self, e, garrison):
        x, z = e['x'], e['z']
        spot, (ux, uz), (vx, vz) = self.walk_spot(x, z)
        if spot is None:
            spot, (ux, uz), (vx, vz) = self.walk_spot(x, z, r=1)
            if spot is None:
                self.stats['battery without a place on the walk'] += 1
                return
            self.stats['battery on a narrow walk (3x3)'] += 1
        px, py, pz = spot
        # its supply from the balcony: the ammunition chest, the charging station with its hopper and coal chest
        bes = self.t.block_entities_in(x - 7, x + 7, 72, 98, z - 7, z + 7)
        depot = [b for b in bes if anvil.val(b[3]['id']) == 'minecraft:chest' and '弾薬庫' in str(anvil.val(b[3].get('CustomName', '')))]
        station = [b for b in bes if anvil.val(b[3]['id']) == 'superbwarfare:charging_station']
        depot.sort(key=lambda b: abs(b[0] - x) + abs(b[2] - z))
        station.sort(key=lambda b: abs(b[0] - x) + abs(b[2] - z))
        taken = {(px + i, pz + j) for i in range(-2, 3) for j in range(-2, 3)}
        ring = [(px + vx * s + ux * a, pz + vz * s + uz * a) for s in (4, -4, 5, -5, 3, -3, 6, -6) for a in (0, 1, -1, 2, -2)]
        moves = []
        if station:
            sx, sy, sz, _ = station[0]
            stack = [(sx, sy + k, sz) for k in range(3)]
            states = [self.t.get(*p) for p in stack]
            if states[1].startswith('minecraft:hopper') and states[2].startswith('minecraft:chest'):
                moves.append(stack)
            else:
                moves.append(stack[:1])
        if depot:
            moves.append([depot[0][:3]])
        for group in moves:
            spot2 = self.free_on_walk(px, py, pz, taken, ring)
            if spot2 is None:
                self.stats['battery supply left on the balcony'] += 1
                continue
            taken.add(spot2)
            datas = {(b[0], b[1], b[2]): {k: v for k, v in b[3].items() if k not in ('x', 'y', 'z', 'keepPacked')}
                     for b in self.t.block_entities_in(group[0][0], group[0][0], group[0][1], group[-1][1], group[0][2], group[0][2])}
            for k, (ox, oy, oz) in enumerate(group):
                s = self.t.get(ox, oy, oz)
                self.put(ox, oy, oz, 'minecraft:air')
                self.put(spot2[0], py + k, spot2[1], s)
                if (ox, oy, oz) in datas:
                    self.t.set_be(spot2[0], py + k, spot2[1], datas[(ox, oy, oz)])
            self.stats['battery supply blocks brought up'] += len(group)
        # a guard of the walk where the gun now stands steps aside
        for g in garrison:
            if g is e or g.get('vehicle'):
                continue
            if abs(g['x'] - px) <= 2 and abs(g['z'] - pz) <= 2 and abs(g['y'] - py) <= 2:
                c = self.free_on_walk(px, py, pz, taken, ring)
                if c:
                    g['x'], g['y'], g['z'] = c[0], py, c[1]
                    taken.add(c)
                    self.stats['walk guards stepped aside'] += 1
        self.stats['battery rise'] += py - e['y']
        e['x'], e['y'], e['z'] = px, py, pz
        e['yaw'] = YAW[(-ux, -uz)]
        self.stats['batteries on the wall walk'] += 1

    # ------------------------------------------------------------------------------------------------ redoubts

    def redoubt(self, e, guards):
        x, y, z = e['x'], e['y'], e['z']
        floor = y
        # the well: the air two above its floor reached from the post (the room's chests and the like do not reach so high)
        well, todo = set(), [(x, z)]
        while todo:
            c = todo.pop()
            if c in well or abs(c[0] - x) > 10 or abs(c[1] - z) > 10:
                continue
            if solid(self.t.get(c[0], floor + 2, c[1])):
                continue
            well.add(c)
            todo += [(c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)]
        if len(well) > 120 or len(well) < 20:
            self.stats['redoubt well not found'] += 1
            return
        # the walls' top: the last level where the ring round the well stands whole
        ring_top = max(yy for yy in range(floor, floor + 12)
                       if sum(solid(self.t.get(cx + dx, yy, cz + dz)) for cx, cz in well for dx, dz in DIRS
                              if (cx + dx, cz + dz) not in well) > 0.8 * sum(1 for cx, cz in well for dx, dz in DIRS if (cx + dx, cz + dz) not in well))
        deck = ring_top
        mx = sum(c[0] for c in well) / len(well)
        mz = sum(c[1] for c in well) / len(well)
        cx, cz = round(mx), round(mz)
        ux, uz = ((-1 if cx > 0 else 1), 0) if abs(cx) >= abs(cz) else (0, (-1 if cz > 0 else 1))
        vx, vz = -uz, ux

        def loc(a, b):  # (along u, along v) from the centre
            return cx + ux * a + vx * b, cz + uz * a + vz * b
        # the passage: from the well's edge on the castle's side out through the wall
        a = 0
        while loc(a + 1, 0) in well:
            a += 1
        passage = []
        k = a + 1
        while k < a + 10:
            px, pz = loc(k, 0)
            if not solid(self.t.get(px, floor, pz)) and not solid(self.t.get(px, floor + 1, pz)):
                break
            passage.append((px, pz))
            k += 1
        outside = loc(k, 0)
        # the stair: along the second row from one side, from the passage's end of the room up to the far end
        rows = {}
        for c in well:
            rel_a = (c[0] - cx) * ux + (c[1] - cz) * uz
            rel_b = (c[0] - cx) * vx + (c[1] - cz) * vz
            rows.setdefault(rel_b, []).append(rel_a)
        rise = deck - floor + 1                        # steps from the floor's level to the deck's
        side = None
        for b in sorted(rows, key=lambda b: -abs(b)):
            run = sorted(rows[b])
            if run == list(range(run[0], run[0] + len(run))) and len(run) >= rise and abs(b) >= 2:
                side = (b, run)
                break
        if side is None:
            self.stats['redoubt without room for a stair'] += 1
            return
        b, run = side
        steps = [loc(run[-1] - i, b) for i in range(rise)]          # bottom at the passage's end, climbing away from it
        climb = DIRS[(-ux, -uz)]
        # the room's chests and the like in the stair's way go to a free corner of the room
        bes = {(bx, bz): (by, d) for bx, by, bz, d in self.t.block_entities_in(cx - 10, cx + 10, floor, floor, cz - 10, cz + 10)}
        displaced = []
        # the deck is open over the stair's two highest steps below it (headroom), closed over the rest
        open_ = set(steps[max(0, rise - 3):rise - 1])
        for i, (sx, sz) in enumerate(steps):
            st = self.t.get(sx, floor, sz)
            if solid(st):
                displaced.append((st, bes.get((sx, sz), (None, None))[1]))
            for yy in range(floor, floor + i):
                self.put(sx, yy, sz, FILL)
            self.put(sx, floor + i, sz, STEP % climb)
            for yy in range(floor + i + 1, deck):
                self.put(sx, yy, sz, 'minecraft:air')
            if floor + i < deck:
                self.put(sx, deck, sz, 'minecraft:air' if (sx, sz) in open_ else DECK)
        self.stats['redoubt stair steps'] += len(steps)
        # the deck over the rest of the well
        for c in well:
            if c in steps:
                continue
            self.put(c[0], deck, c[1], DECK)
            self.stats['redoubt deck blocks'] += 1
        # lanterns hung under the deck (a dark room would breed the night's monsters)
        for la, lb in ((0, 0), (-2, -2), (2, 2), (-2, 2), (2, -2)):
            lx, lz = loc(la, lb)
            if (lx, lz) in well and (lx, lz) not in steps and is_air(self.t.get(lx, deck - 1, lz)):
                self.put(lx, deck - 1, lz, 'minecraft:lantern[hanging=true,waterlogged=false]')
                self.stats['redoubt lanterns'] += 1
        # the passage (two high), its threshold, and a step up from the field outside
        for px, pz in passage:
            self.put(px, floor, pz, 'minecraft:air')
            self.put(px, floor + 1, pz, 'minecraft:air')
            if not solid(self.t.get(px, floor - 1, pz)):
                self.put(px, floor - 1, pz, FILL)
        ox, oz = outside
        if not solid(self.t.get(ox, floor - 1, oz)) and solid(self.t.get(ox, floor - 2, oz)):
            self.put(ox, floor - 1, oz, STEP % DIRS[(-ux, -uz)])
            self.stats['redoubt door steps'] += 1
        self.stats['redoubt passage blocks'] += 2 * len(passage)
        # what stood in the stair's way, on the room's floor elsewhere
        free = [c for c in sorted(well, key=lambda c: -((c[0] - cx) ** 2 + (c[1] - cz) ** 2))
                if c not in steps and c not in passage and not solid(self.t.get(c[0], floor, c[1]))
                and abs((c[0] - cx) * vx + (c[1] - cz) * vz) != abs(b) and (c[0], c[1]) != loc(a, 0)]
        for st, data in displaced:
            if not free:
                self.stats['redoubt things without a place'] += 1
                continue
            fx, fz = free.pop(0)
            self.put(fx, floor, fz, st)
            if data is not None:
                self.t.set_be(fx, floor, fz, {k: v for k, v in data.items() if k not in ('x', 'y', 'z', 'keepPacked')})
            self.stats['redoubt things moved off the stair'] += 1
        # the gun at the deck's middle, the guards beside it
        e['x'], e['y'], e['z'] = cx, deck + 1, cz
        e['yaw'] = YAW[(-ux, -uz)]
        spots = [loc(-3, 0), loc(0, -b // abs(b) * 3), loc(2, -b // abs(b) * 3), loc(-3, -b // abs(b) * 2)]
        for g, (gx, gz) in zip(guards, spots):
            g['x'], g['y'], g['z'] = gx, deck + 1, gz
            g['yaw'] = YAW[(-ux, -uz)]
            self.stats['redoubt guards on the deck'] += 1
        self.stats['redoubts decked'] += 1

    # ------------------------------------------------------------------------------------------------ the road posts

    @staticmethod
    def crossfire(e):
        x, z = e['x'], e['z']
        if abs(x) >= abs(z):
            e['yaw'] = YAW[(0, 1 if z < 0 else -1)]
        else:
            e['yaw'] = YAW[(1 if x < 0 else -1, 0)]

    def run(self, garrison):
        entries = garrison['entries']
        for e in [e for e in entries if e.get('post') == 'battery']:
            self.battery(e, entries)
        guards = [g for g in entries if g.get('post') == 'outer_redoubt']
        for e in [e for e in entries if e.get('post') == 'redoubt']:
            mine = [g for g in guards if abs(g['x'] - e['x']) <= 10 and abs(g['z'] - e['z']) <= 10]
            self.redoubt(e, mine)
        for e in [e for e in entries if e.get('post') == 'crossfire']:
            self.crossfire(e)
            self.stats['road posts turned to their road'] += 1
        return self.stats


if __name__ == '__main__':
    folder = sys.argv[1]
    t = template_io.Template(folder)
    gp = os.path.join(folder, 'garrison.json')
    g = json.load(open(gp))
    stats = Turrets(t).run(g)
    stats['chunks saved'] = t.save(folder)
    json.dump(g, open(gp, 'w'), indent=0)
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    if len(sys.argv) > 2:
        json.dump(stats, open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)

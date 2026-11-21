"""god_stages.py <structure dir> [god ...]: each of the 41 gods' citadels made into the god's own stage (r63; the user, on
the first rebuild, one castle for all with only its stone and roof changed: "それ一択ではキャラクターを表現できていない"
"全部 キャラクターの説明や性格に合わせた舞台を").

Each god's stage is drawn from what the mod says of the god (characters.json: title, kind, temper, powers, look and
colours; the Japanese names of its relics, its moves and the three stages of its legend): stages_a.py and stages_b.py
hold one builder for each. What every stage keeps:

  * the god's seal on the stage's floor, with eleven blocks clear each way and thirteen up over it (the seal gives the
    god up only where it has room: the largest god, Yggdrasil, is three wide and seven high);
  * every chest of the old citadel with its loot table (the best two blocks from the seal, the first far out by the way
    in, the rest spread over the stage, against walls where there are walls) and every spawner with its minion
    (spread out, nine blocks or more from the seal);
  * air stored over the stage so the ground does not stand in it (underground and Nether stages: in a whole cavern);
  * lights where it is dark (tools/structure_lights.py's rule), none over the seal.
"""
import gzip, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import anvil
from anvil import Typed
import structure_lights
from stage_kit import Grid, AIR, W, H, C, S, connect
import god_citadels as old

FULL_NOT = ('stairs', 'slab', 'glass', 'leaves', 'pane', 'bars', 'wall', 'fence', 'lantern', 'torch', 'chain', 'carpet', 'flower',
            'rose', 'tulip', 'banner', 'rod', 'water', 'lava', 'air', 'candle', 'bell', 'cauldron', 'anvil', 'campfire', 'coral',
            'petals', 'bush', 'grass', 'fern', 'lily', 'daisy', 'allium', 'orchid', 'bluet', 'poppy', 'dandelion', 'cornflower',
            'torchflower', 'chest', 'spawner', 'seal', 'pot', 'head', 'skull', 'button', 'lectern', 'cluster', 'bud', 'snow[', 'rail',
            'hay', 'honey_block', 'scaffold', 'pointed', 'end_rod', 'cobweb', 'ladder', 'vine', 'roots', 'sapling', 'moss_carpet')


def full(s):
    if s is None or s == AIR:
        return False
    n = s.split('[')[0]
    return not any(k in n for k in FULL_NOT)


def finish(g, seal, chests, spawners):
    sy = g.seal_y
    # the god's room over the seal
    for x in range(C - 5, C + 6):
        for z in range(C - 5, C + 6):
            for y in range(sy + 1, sy + 14):
                g.set(x, y, z, AIR)
    if not full(g.get(C, sy - 1, C)):
        g.set(C, sy - 1, C, g.floor_block)
    g.set(C, sy, C, seal)
    # the best chest just behind the seal
    if chests:
        best = chests[-1]
        g.set(C, sy, C - 2, old.chest_state(best, 'south'), best[1])
        if not full(g.get(C, sy - 1, C - 2)):
            g.set(C, sy - 1, C - 2, g.floor_block)
        chests = chests[:-1]
    # places to stand on the stage, away from the seal
    cand = []
    for (x, y, z), s in list(g.c.items()):
        if not full(s):
            continue
        p = (x, y + 1, z)
        if not (2 <= x < W - 2 and 2 <= z < W - 2 and 1 <= p[1] <= sy + 6):
            continue
        if not (g.empty(*p) and g.empty(x, y + 2, z)):
            continue
        if math.hypot(x - C, z - C) < 9:
            continue
        if any(g.get(x + dx, y + 1, z + dz) in ('minecraft:water',) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            continue
        walled = sum(full(g.get(x + dx, y + 1, z + dz)) for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        cand.append((p, walled))
    if not cand:
        raise RuntimeError('no place for chests on the stage')
    taken = [(C, sy, C)]

    def pick(prefer_wall, far_first=False):
        best, bd = None, -1
        for p, walled in cand:
            if p in taken:
                continue
            d = min(math.dist(p, q) for q in taken)
            if far_first:
                d = math.hypot(p[0] - C, p[2] - C) * 10 + d
            score = d + (6 if prefer_wall and walled else 0)
            if score > bd:
                best, bd = p, score
        taken.append(best)
        return best
    # the first chest far out (toward the south, the way in), then the spawners, then the rest
    south = [c for c in cand if c[0][2] > C + 12]
    if chests:
        first = max(south or cand, key=lambda c: c[0][2] + (3 if c[1] else 0))[0]
        taken.append(first)
        g.set(*first, old.chest_state(chests[0], 'north'), chests[0][1])
        chests = chests[1:]
    for sp in spawners:
        p = pick(False)
        g.set(*p, S('spawner'), sp)
    for ch in chests:
        p = pick(True)
        g.set(*p, old.chest_state(ch, 'north'), ch[1])
    connect(g)


def build(god, seal, chests, spawners):
    import stages_a, stages_b
    fn = getattr(stages_a, god, None) or getattr(stages_b, god)
    g = Grid(seed=sum(map(ord, god)))
    g.seal_y = 1
    g.floor_block = 'minecraft:polished_andesite'
    g.cavern = None
    fn(g)
    if g.cavern:
        r, h = g.cavern
        for x in range(C - r, C + r + 1):
            for z in range(C - r, C + r + 1):
                for y in range(0, h + 1):
                    if ((x - C) / r) ** 2 + ((z - C) / r) ** 2 + (y / h) ** 2 <= 1.0 and (x, y, z) not in g.c:
                        g.set(x, y, z, AIR)
    finish(g, seal, chests, spawners)
    return g


def main():
    folder = sys.argv[1]
    want = set(sys.argv[2:])
    for god in sorted(old.GODS):
        if want and god not in want:
            continue
        src = os.path.join(folder, god + '_citadel.nbt')
        orig = os.path.join(folder, 'orig', god + '_citadel.nbt')
        nbt0 = anvil.read_nbt_typed(gzip.decompress(open(orig if os.path.exists(orig) else src, 'rb').read()))
        seal, chests, spawners, dv = old.harvest(nbt0)
        g = build(god, seal, chests, spawners)
        nbt = old.to_nbt(g, dv)
        nbt['size'] = [Typed(3, W), Typed(3, H), Typed(3, W)]
        res = structure_lights.light_template(nbt)
        lit = None
        if res is not None:
            lit, new = res
            if new is not None:
                nbt = new
        old.keep_seal_clear(nbt, g.seal_y, C)
        if god == 'enkou':
            # (run 198) the deep-sea stage is under the sea: torches wash away, sea lanterns light it
            for e in nbt['palette']:
                if anvil.val(e['Name']) in ('minecraft:torch', 'minecraft:wall_torch'):
                    e['Name'] = 'minecraft:sea_lantern'
                    e.pop('Properties', None)
        with open(src, 'wb') as f:
            f.write(gzip.compress(anvil.write_nbt(nbt), 6, mtime=0))
        print(god, 'blocks', len(nbt['blocks']), 'seal_y', g.seal_y, 'lights', (lit or {}).get('placed'), flush=True)


if __name__ == '__main__':
    main()

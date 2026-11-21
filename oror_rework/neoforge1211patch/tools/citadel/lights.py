"""lights.py <template dir> [report.json]: light every built room of the capital (r62; the user: "王都の建物や外に生成さ
れる建物の中に照明が無かったり").

A place to stand indoors is an air cell with air above it (room for the head), a built block under it (not the save's
natural rock or dirt) and a solid block somewhere above it (a roof). One is dark when its block light, from the
template's own lights, is under 8 (monsters spawn at 0; a room under 8 reads as unlit). Until none is dark, each dark
one in turn gets a light near it, the first that fits of:
  1. a wall torch at head height on a wall within two blocks (no collision, out of the way);
  2. a lantern hanging from the ceiling, where the ceiling is three to eight blocks above the floor (the head stays free);
  3. a torch on the floor where it stands.
Light is spread from each new one at once (6-neighbour flood through passable cells, one level less per step), so the
next dark place is judged with it. Only exact air cells take a light; nothing the template has is replaced.
"""
import json, os, re, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import template_io

GROUND = 64
EMIT = [(re.compile(r'(sea_lantern|glowstone|lantern|jack_o_lantern|beacon|shroomlight|froglight|^minecraft:lava|campfire\[.*lit=true|redstone_lamp\[.*lit=true|end_gateway|conduit|respawn_anchor)'), 15),
        (re.compile(r'(torch(?!flower)|end_rod|crying_obsidian)'), 14), (re.compile(r'candle.*lit=true'), 9),
        (re.compile(r'(magma_block|glow_lichen|amethyst_cluster)'), 7), (re.compile(r'^minecraft:light(\[|$)'), 15)]
PASS = re.compile(r'(air|glass|pane|torch|lantern|door|fence|_wall(\[|$)|slab|stairs|carpet|button|lever|ladder|vine|banner|sign|flower|grass(?!_block)|fern|bars|chain|rail|pressure_plate|candle|rod|_bed|chest|barrel|table|anvil|bell|campfire|leaves|cobweb|^minecraft:light(\[|$)|water|scaffold|pot|head|skull|lectern|stand|cake|sapling|wheat|carrots|potatoes|beetroots|^minecraft:snow\[|structure_void|jigsaw|bush|kelp|seagrass|lily|comparator|repeater|redstone_wire|tripwire|hopper|composter|cauldron|grindstone|stonecutter|loom|smithing|fletching|cartography|brewing|enchanting|piston_head|mushroom(?!_block)|sugar_cane|bamboo(?!_block|_planks|_mosaic)|sweet_berry|cocoa|pickle|coral(?!_block)|frame|painting|turtle_egg|nether_wart|lava)')
NAT = re.compile(r'^minecraft:(stone|deepslate|granite|diorite|andesite|tuff|calcite|dirt|coarse_dirt|rooted_dirt|gravel|sand|clay|grass_block|podzol|mycelium|bedrock|.*_ore|dripstone_block|moss_block|smooth_basalt|cobbled_deepslate|infested_.*|red_sand|snow_block|powder_snow|ice|packed_ice|obsidian|magma_block|soul_sand|netherrack)(\[|$)')
# full blocks a torch holds to (not the natural kinds a cave is made of: those are fine too)
HOLD_NOT = re.compile(r'(farmland|dirt_path|soul_sand|honey|slime|chest|barrel|piston|observer|dispenser|dropper|furnace|smoker|hopper|ice|glass|leaves|spawner|beehive|bee_nest|target|tnt|scaffold|mud\b)')
AIRS = ('minecraft:air', 'minecraft:cave_air')
DIRS = {(1, 0): 'west', (-1, 0): 'east', (0, 1): 'north', (0, -1): 'south'}  # wall at (dx, dz) -> the torch's facing


def emit(k):
    for r, v in EMIT:
        if r.search(k):
            return v
    return 0


def grid(t):
    cxs = [c[0] for c in t.index]
    czs = [c[1] for c in t.index]
    cx0, cz0 = min(cxs), min(czs)
    X, Z, Y = (max(cxs) - cx0 + 1) * 16, (max(czs) - cz0 + 1) * 16, 12 * 16
    pas = np.ones((X, Y, Z), bool)
    src = np.zeros((X, Y, Z), np.int8)
    nat = np.zeros((X, Y, Z), bool)
    air = np.ones((X, Y, Z), bool)
    hold = np.zeros((X, Y, Z), bool)
    pas[:, :GROUND, :] = False
    nat[:, :GROUND, :] = True
    air[:, :GROUND, :] = False
    cache = {}
    for (cx, cz) in t.index:
        bx, bz = (cx - cx0) * 16, (cz - cz0) * 16
        for sy in range(12):
            s = t._section(cx, cz, sy, False)
            if s is None:
                continue
            keys, idx = s[0], s[1]
            info = [cache.setdefault(k, (bool(PASS.search(k)), emit(k), bool(NAT.match(k)), k in AIRS,
                                         not PASS.search(k) and not HOLD_NOT.search(k))) for k in keys]
            a = idx.reshape(16, 16, 16)
            for arr, j, dt in ((pas, 0, bool), (src, 1, np.int8), (nat, 2, bool), (air, 3, bool), (hold, 4, bool)):
                arr[bx:bx + 16, sy * 16:sy * 16 + 16, bz:bz + 16] = np.array([i[j] for i in info], dt)[a].transpose(2, 0, 1)
        t.chunks.pop((cx, cz), None)
        t.sections.pop((cx, cz), None)
    present = np.zeros((X // 16, Z // 16), bool)
    for (cx, cz) in t.index:
        present[cx - cx0, cz - cz0] = True
    mask = np.repeat(np.repeat(present, 16, 0), 16, 1)[:, None, :]
    pas &= mask
    air &= mask
    return pas, src, nat, air, hold, (cx0 * 16, cz0 * 16)


def propagate(pas, src, steps=15):
    L = src.astype(np.int8).copy()
    for _ in range(steps):
        m = L.copy()
        for ax in range(3):
            a = [slice(None)] * 3
            b = [slice(None)] * 3
            a[ax] = slice(1, None)
            b[ax] = slice(None, -1)
            np.maximum(m[tuple(a)], L[tuple(b)] - 1, out=m[tuple(a)])
            np.maximum(m[tuple(b)], L[tuple(a)] - 1, out=m[tuple(b)])
        m = np.where(pas, m, src)
        np.maximum(m, 0, out=m)
        if np.array_equal(m, L):
            break
        L = m
    return L


def standing(pas, nat, air):
    """Indoor places to stand on built floors."""
    solid = ~pas
    roof = np.zeros_like(pas)
    acc = np.flip(np.logical_or.accumulate(np.flip(solid, 1), 1), 1)
    roof[:, :-1, :] = acc[:, 1:, :]
    st = air.copy()
    st[:, 0, :] = False
    st[:, -1, :] = False
    st[:, 1:, :] &= solid[:, :-1, :] & ~nat[:, :-1, :]
    st[:, :-1, :] &= air[:, 1:, :]
    return st & roof


def main():
    folder = sys.argv[1]
    t = template_io.Template(folder)
    pas, src, nat, air, hold, (ox, oz) = grid(t)
    X, Y, Z = pas.shape
    print('grid', pas.shape, 'lights', int((src > 0).sum()), flush=True)
    L = propagate(pas, src)
    st = standing(pas, nat, air)
    dark0 = st & (L < 8)
    print('indoor', int(st.sum()), 'dark', int(dark0.sum()), flush=True)
    placed = {'wall_torch': 0, 'lantern': 0, 'torch': 0}
    R = 15

    def light(x, y, z, level):
        x0, x1, y0, y1, z0, z1 = max(0, x - R), min(X, x + R + 1), max(0, y - R), min(Y, y + R + 1), max(0, z - R), min(Z, z + R + 1)
        s = np.zeros((x1 - x0, y1 - y0, z1 - z0), np.int8)
        s[x - x0, y - y0, z - z0] = level
        p = pas[x0:x1, y0:y1, z0:z1].copy()
        p[x - x0, y - y0, z - z0] = True
        n = propagate(p, s)
        np.maximum(L[x0:x1, y0:y1, z0:z1], n, out=L[x0:x1, y0:y1, z0:z1])

    def put(x, y, z, state, level, kind):
        ok = t.set(x + ox, y, z + oz, state)
        assert ok, (x + ox, y, z + oz, state)
        air[x, y, z] = False
        light(x, y, z, level)
        placed[kind] += 1

    cells = np.argwhere(dark0)
    order = np.lexsort((cells[:, 2], cells[:, 0], cells[:, 1]))
    rng = np.random.default_rng(62)
    # in blocks of a few thousand, shuffled inside each block: lights spread out instead of following one scan line
    blocks = np.array_split(order, max(1, len(order) // 4000))
    for b in blocks:
        rng.shuffle(b)
    for i in np.concatenate(blocks):
        x, y, z = (int(v) for v in cells[i])
        if L[x, y, z] >= 8:
            continue
        h = y + 1
        done = False
        # 1. a wall torch at head height within two blocks
        best = None
        for r in (0, 1, 2):
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if max(abs(dx), abs(dz)) != r:
                        continue
                    px, pz = x + dx, z + dz
                    if not (0 <= px < X and 0 <= pz < Z) or not air[px, h, pz]:
                        continue
                    for (wx, wz), facing in DIRS.items():
                        qx, qz = px + wx, pz + wz
                        if 0 <= qx < X and 0 <= qz < Z and hold[qx, h, qz]:
                            best = (px, pz, facing)
                            break
                    if best:
                        break
                if best:
                    break
            if best:
                break
        if best:
            put(best[0], h, best[1], 'minecraft:wall_torch[facing=%s]' % best[2], 14, 'wall_torch')
            continue
        # 2. a lantern from a ceiling three to eight above the floor
        for k in range(3, 9):
            if y + k >= Y:
                break
            if not air[x, y + k - 1, z]:
                break
            if hold[x, y + k, z]:
                put(x, y + k - 1, z, 'minecraft:lantern[hanging=true,waterlogged=false]', 15, 'lantern')
                done = True
                break
            if not pas[x, y + k, z]:
                break
        if done:
            continue
        # 3. a torch on the floor
        put(x, y, z, 'minecraft:torch', 14, 'torch')
    dark1 = st & (L < 8) & air
    print('placed', placed, 'dark after', int(dark1.sum()), flush=True)
    n = t.save(folder)
    report = {'indoor': int(st.sum()), 'dark_before': int(dark0.sum()), 'dark_after': int(dark1.sum()), 'placed': placed, 'chunks_written': n}
    print(json.dumps(report))
    if len(sys.argv) > 2:
        json.dump(report, open(sys.argv[2], 'w'), indent=1)


if __name__ == '__main__':
    main()

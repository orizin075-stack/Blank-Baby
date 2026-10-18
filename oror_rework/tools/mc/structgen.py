"""Procedural structure templates for v0.17.17 (written as vanilla structure NBT + worldgen JSON).

  python3 -I tools/mc/structgen.py <overlay dir>

Writes into <overlay>/data/oror_supreme_bosses/:
  structure/<name>.nbt                          the template (blocks, loot chests, inhabitants)
  worldgen/structure/<name>.json                a single-piece jigsaw structure on the surface
  worldgen/structure_set/<name>.json            its spread
  worldgen/template_pool/<name>/start_pool.json
  worldgen/processor_list/weathered.json        mossy/cracked stone, cracked blackstone
  tags/worldgen/biome/has_<name>.json           where it may stand

Structures: illager_fortress (邪悪な村人の要塞), illager_city (邪悪な村人の都市), villager_fortress (村人の要塞),
trader_exchange (行商人の取引所), villager_kingdom (村人の王国).

The floor of every template is y=1 (y=0 is a foundation); the start is projected to the surface and lowered by one,
so the floor lies on the ground and terrain is bearded to it. A template stays within 128 blocks of its start corner
(a structure only reaches eight chunks from its start chunk).
"""
import gzip, io, json, os, random, struct, sys

NS = 'oror_supreme_bosses'
DATA_VERSION = 3955  # Minecraft 1.21.1

# ---------------------------------------------------------------------------------------------- NBT
class Byte(int): pass
class Short(int): pass
class Int(int): pass
class Long(int): pass
class Float(float): pass
class Double(float): pass
class IntArray(list): pass
class L:
    def __init__(self, tag, items): self.tag, self.items = tag, list(items)

def _tag(v):
    if isinstance(v, Byte): return 1
    if isinstance(v, Short): return 2
    if isinstance(v, Long): return 4
    if isinstance(v, Float): return 5
    if isinstance(v, Double): return 6
    if isinstance(v, IntArray): return 11
    if isinstance(v, bool): return 1
    if isinstance(v, int): return 3
    if isinstance(v, float): return 6
    if isinstance(v, str): return 8
    if isinstance(v, (L, list)): return 9
    if isinstance(v, dict): return 10
    raise TypeError(type(v))

def _w(out, v, t):
    if t == 1: out.write(struct.pack('>b', int(v)))
    elif t == 2: out.write(struct.pack('>h', int(v)))
    elif t == 3: out.write(struct.pack('>i', int(v)))
    elif t == 4: out.write(struct.pack('>q', int(v)))
    elif t == 5: out.write(struct.pack('>f', float(v)))
    elif t == 6: out.write(struct.pack('>d', float(v)))
    elif t == 8:
        b = v.encode('utf-8'); out.write(struct.pack('>H', len(b))); out.write(b)
    elif t == 9:
        if isinstance(v, L): et, items = v.tag, v.items
        else: items = v; et = _tag(items[0]) if items else 0
        out.write(struct.pack('>bi', et, len(items)))
        for i in items: _w(out, i, et)
    elif t == 10:
        for k, x in v.items():
            xt = _tag(x); out.write(struct.pack('>b', xt)); _w(out, k, 8); _w(out, x, xt)
        out.write(b'\x00')
    elif t == 11:
        out.write(struct.pack('>i', len(v)))
        for i in v: out.write(struct.pack('>i', i))

def nbt_bytes(root):
    out = io.BytesIO(); out.write(b'\x0a'); _w(out, '', 8); _w(out, root, 10)
    return gzip.compress(out.getvalue(), 9, mtime=0)

def uuid_ints(hexstr):
    h = int(hexstr.replace('-', ''), 16)
    parts = [(h >> s) & 0xffffffff for s in (96, 64, 32, 0)]
    return IntArray([p - (1 << 32) if p >= 1 << 31 else p for p in parts])

# ---------------------------------------------------------------------------------------------- canvas
def state(s):
    if '[' in s:
        name, props = s[:-1].split('[', 1)
        p = dict(kv.split('=') for kv in props.split(','))
    else:
        name, p = s, {}
    if ':' not in name: name = 'minecraft:' + name
    return name, p

DIRS = {'north': (0, -1), 'south': (0, 1), 'west': (-1, 0), 'east': (1, 0)}
OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}
LEFT = {'north': 'west', 'west': 'south', 'south': 'east', 'east': 'north'}

class Canvas:
    def __init__(self, name, w, h, d, seed):
        self.name, self.w, self.h, self.d = name, w, h, d
        self.b = {}
        self.ents = []
        self.r = random.Random(seed)

    def ok(self, x, y, z): return 0 <= x < self.w and 0 <= y < self.h and 0 <= z < self.d
    def set(self, x, y, z, s, nbt=None):
        if self.ok(x, y, z): self.b[(x, y, z)] = (s, nbt)
    def get(self, x, y, z): return self.b.get((x, y, z), (None, None))[0]
    def fill(self, x0, y0, z0, x1, y1, z1, s):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, s(x, y, z) if callable(s) else s)
    def air(self, x0, y0, z0, x1, y1, z1): self.fill(x0, y0, z0, x1, y1, z1, 'air')
    def entity(self, x, y, z, nbt):
        if self.ok(x, y, z): self.ents.append(((x + 0.5, float(y), z + 0.5), (x, y, z), nbt))

    def save(self, path):
        palette, index, blocks = [], {}, []
        for (x, y, z), (s, nbt) in sorted(self.b.items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0])):
            name, props = state(s)
            key = (name, tuple(sorted(props.items())))
            if key not in index:
                index[key] = len(palette)
                e = {'Name': name}
                if props: e['Properties'] = dict(sorted(props.items()))
                palette.append(e)
            e = {'pos': L(3, [Int(x), Int(y), Int(z)]), 'state': Int(index[key])}
            if nbt: e['nbt'] = nbt
            blocks.append(e)
        ents = [{'pos': L(6, [Double(p[0]), Double(p[1]), Double(p[2])]), 'blockPos': L(3, [Int(b[0]), Int(b[1]), Int(b[2])]), 'nbt': n}
                for p, b, n in self.ents]
        root = {'DataVersion': Int(DATA_VERSION), 'size': L(3, [Int(self.w), Int(self.h), Int(self.d)]),
                'palette': L(10, palette), 'blocks': L(10, blocks), 'entities': L(10, ents)}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f: f.write(nbt_bytes(root))
        return len(blocks), len(ents)

# ---------------------------------------------------------------------------------------------- items and mobs
def item(i, n=1, ench=None):
    st = {'id': 'minecraft:' + i if ':' not in i else i, 'count': Int(n)}
    if ench: st['components'] = {'minecraft:enchantments': {'levels': {('minecraft:' + k): Int(v) for k, v in ench.items()}}}
    return st

def gear(hands=(None, None), armor=(None, None, None, None)):
    """armor is (feet, legs, chest, head)."""
    return {'HandItems': L(10, [h or {} for h in hands]), 'ArmorItems': L(10, [a or {} for a in armor]),
            'HandDropChances': L(5, [Float(0.05), Float(0.05)]), 'ArmorDropChances': L(5, [Float(0.05)] * 4)}

def mind(level, stance='aggressive'):
    return {'OrorMind': {'Schema': Int(1), 'LevelInitialized': Byte(1), 'BaseLevel': Int(level), 'Elite': Byte(0),
                         'Born': Long(0), 'LastClock': Long(0), 'Stance': stance}}

def named(text, color):
    return {'CustomName': json.dumps({'text': text, 'color': color}, ensure_ascii=False), 'CustomNameVisible': Byte(1)}

def illager(kind, level=None, name=None, extra=None, warlord=False):
    n = {'id': 'minecraft:' + kind, 'PersistenceRequired': Byte(1)}
    if kind == 'pillager':
        n.update(gear((item('crossbow', 1, {'quick_charge': 2}), None)))
    elif kind == 'vindicator':
        n.update(gear((item('iron_axe', 1, {'sharpness': 2}), None)))
    if level: n['NeoForgeData'] = mind(level)
    if warlord:
        # the headquarters' commander: killing it calls the hordes off the villages around (VillageRaids)
        n.setdefault('NeoForgeData', {})['OrorWarlord'] = Byte(1)
    if name: n.update(named(*name))
    if extra: n.update(extra)
    return n

PROFS = ['armorer', 'weaponsmith', 'toolsmith', 'fletcher', 'butcher', 'leatherworker', 'mason', 'farmer', 'fisherman',
         'shepherd', 'cleric', 'librarian', 'cartographer']

def villager(prof, level=2, settlement=None, biome='plains', baby=False):
    n = {'id': 'minecraft:villager', 'PersistenceRequired': Byte(1),
         'VillagerData': {'type': 'minecraft:' + biome, 'profession': 'minecraft:' + prof, 'level': Int(level)}}
    if baby: n['Age'] = Int(-24000)
    if settlement: n['NeoForgeData'] = {'OrorSettlement': settlement}
    return n

def guard(level=2):
    metal = 'iron' if level < 3 else 'diamond'
    n = {'id': 'guardvillagers:guard', 'PersistenceRequired': Byte(1)}
    n.update(gear((item(metal + '_sword', 1, {'sharpness': level}), item('shield')),
                  (item(metal + '_boots'), item(metal + '_leggings'), item(metal + '_chestplate'), item(metal + '_helmet'))))
    return n

def golem():
    return {'id': 'minecraft:iron_golem', 'PlayerCreated': Byte(0), 'PersistenceRequired': Byte(1)}

EXCHANGE = uuid_ints('6f726f72-0000-4ex0-0000-000000000000'.replace('x', '0'))

def trader():
    return {'id': 'minecraft:wandering_trader', 'DespawnDelay': Int(0), 'PersistenceRequired': Byte(1),
            'NeoForgeData': {'OrorCaravan': EXCHANGE, 'OrorExchange': Byte(1)}}

def llama(variant):
    return {'id': 'minecraft:trader_llama', 'Tame': Byte(1), 'Variant': Int(variant), 'DespawnDelay': Int(0),
            'PersistenceRequired': Byte(1), 'NeoForgeData': {'OrorCaravan': EXCHANGE}}

# ---------------------------------------------------------------------------------------------- building parts
OMINOUS = L(10, [{'pattern': 'minecraft:' + p, 'color': c} for p, c in [
    ('rhombus', 'cyan'), ('stripe_bottom', 'light_gray'), ('stripe_center', 'gray'), ('border', 'light_gray'),
    ('stripe_middle', 'black'), ('half_horizontal', 'light_gray'), ('circle', 'light_gray'), ('border', 'black')]])

def banner(c, x, y, z, facing, color='white', ominous=False, wall=True):
    s = f'{color}_wall_banner[facing={facing}]' if wall else f'{color}_banner[rotation=0]'
    c.set(x, y, z, s, {'patterns': OMINOUS} if ominous else None)

def chest(c, x, y, z, facing, loot=None, block='chest'):
    s = f'{block}[facing={facing}]' if block == 'barrel' else f'chest[facing={facing},type=single,waterlogged=false]'
    c.set(x, y, z, s, {'LootTable': loot} if loot else None)

def bed(c, x, y, z, facing, color='red'):
    dx, dz = DIRS[facing]
    c.set(x, y, z, f'{color}_bed[facing={facing},part=foot,occupied=false]')
    c.set(x + dx, y, z + dz, f'{color}_bed[facing={facing},part=head,occupied=false]')

def door(c, x, y, z, facing, wood='oak'):
    c.set(x, y, z, f'{wood}_door[facing={facing},half=lower,hinge=left,open=false,powered=false]')
    c.set(x, y + 1, z, f'{wood}_door[facing={facing},half=upper,hinge=left,open=false,powered=false]')

def lamp_post(c, x, y, z, post='oak_fence', light='lantern'):
    for i in range(3): c.set(x, y + i, z, post)
    c.set(x, y + 3, z, f'{light}[hanging=false]')

def battlement(c, x0, z0, x1, z1, y, s):
    """Crenels on the outline of a rectangle at height y."""
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            if (x + z) % 2 == 0: c.set(x, y, z, s)
    for z in range(z0, z1 + 1):
        for x in (x0, x1):
            if (x + z) % 2 == 0: c.set(x, y, z, s)

def outline(c, x0, y0, z0, x1, y1, z1, s):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            c.set(x, y, z0, s); c.set(x, y, z1, s)
        for z in range(z0, z1 + 1):
            c.set(x0, y, z, s); c.set(x1, y, z, s)

RIDGE = {'stone_brick': 'stone_bricks', 'deepslate_brick': 'deepslate_bricks', 'brick': 'bricks', 'blackstone': 'blackstone'}

def gable(c, x0, z0, x1, z1, y, mat, along_x, top=None, overhang=1):
    """A pitched roof over the rectangle, ridge along x (along_x) or z."""
    ridge = top or RIDGE.get(mat, f'{mat}_planks')
    x0 -= overhang; z0 -= overhang; x1 += overhang; z1 += overhang
    span = (z1 - z0) if along_x else (x1 - x0)
    for i in range(span // 2 + 1):
        yy = y + i
        if along_x:
            for x in range(x0, x1 + 1):
                if z0 + i <= z1 - i:
                    c.set(x, yy, z0 + i, f'{mat}_stairs[facing=south,half=bottom]')
                    c.set(x, yy, z1 - i, f'{mat}_stairs[facing=north,half=bottom]')
                if z0 + i == z1 - i: c.set(x, yy, z0 + i, ridge)
        else:
            for z in range(z0, z1 + 1):
                if x0 + i <= x1 - i:
                    c.set(x0 + i, yy, z, f'{mat}_stairs[facing=east,half=bottom]')
                    c.set(x1 - i, yy, z, f'{mat}_stairs[facing=west,half=bottom]')
                if x0 + i == x1 - i: c.set(x0 + i, yy, z, ridge)
    return y + span // 2

def gable_ends(c, x0, z0, x1, z1, y, along_x, s):
    """Close the triangles under a gable roof (built with an overhang of one) at both ends."""
    if along_x:
        for k in range(1, (z1 - z0) // 2 + 2):
            for z in range(z0 + k, z1 - k + 1):
                c.set(x0, y + k, z, s); c.set(x1, y + k, z, s)
    else:
        for k in range(1, (x1 - x0) // 2 + 2):
            for x in range(x0 + k, x1 - k + 1):
                c.set(x, y + k, z0, s); c.set(x, y + k, z1, s)

def pyramid(c, x0, z0, x1, z1, y, mat, cap='lantern[hanging=false]'):
    i = 0
    while x0 + i <= x1 - i and z0 + i <= z1 - i:
        for x in range(x0 + i, x1 - i + 1):
            c.set(x, y + i, z0 + i, f'{mat}_stairs[facing=south,half=bottom]')
            c.set(x, y + i, z1 - i, f'{mat}_stairs[facing=north,half=bottom]')
        for z in range(z0 + i + 1, z1 - i):
            c.set(x0 + i, y + i, z, f'{mat}_stairs[facing=east,half=bottom]')
            c.set(x1 - i, y + i, z, f'{mat}_stairs[facing=west,half=bottom]')
        i += 1
    c.set((x0 + x1) // 2, y + i, (z0 + z1) // 2, cap)

def tower(c, x0, z0, size, height, wall, floor, roof=None, crenel=None, banners=None, windows='iron_bars'):
    """A square tower from the floor (y=1) up, ladder inside, a lookout on top."""
    x1, z1 = x0 + size - 1, z0 + size - 1
    outline(c, x0, 1, z0, x1, height, z1, wall)
    c.air(x0 + 1, 2, z0 + 1, x1 - 1, height, z1 - 1)
    for y in range(5, height, 5):
        c.fill(x0 + 1, y, z0 + 1, x1 - 1, y, z1 - 1, floor)
        c.set(x0 + 1, y, z0 + 1, 'air')
        for x, z, f in ((x0 + size // 2, z0, 'north'), (x0 + size // 2, z1, 'south'), (x0, z0 + size // 2, 'west'), (x1, z0 + size // 2, 'east')):
            c.set(x, y + 2, z, windows)
    for y in range(2, height + 1):
        c.set(x0 + 1, y, z0 + 1, 'ladder[facing=south]')
    c.fill(x0, height + 1, z0, x1, height + 1, z1, floor)
    c.set(x0 + 1, height + 1, z0 + 1, 'ladder[facing=south]')
    if crenel:
        battlement(c, x0, z0, x1, z1, height + 2, crenel)
    if roof:
        pyramid(c, x0 - 1, z0 - 1, x1 + 1, z1 + 1, height + 3, roof)
    if banners:
        color, ominous = banners
        for x, z, f in ((x0 + size // 2, z0 - 1, 'north'), (x0 + size // 2, z1 + 1, 'south'), (x0 - 1, z0 + size // 2, 'west'), (x1 + 1, z0 + size // 2, 'east')):
            banner(c, x, height - 1, z, f, color, ominous)
    return (x0 + size // 2, height + 2, z0 + size // 2)

def curtain(c, x0, z0, x1, z1, height, wall, walk, crenel):
    """A wall two thick from (x0,z0) to (x1,z1) (straight along x or z), with a walk and crenels on top."""
    if z0 == z1:
        c.fill(x0, 1, z0, x1, height, z0 + 1, wall)
        c.fill(x0, height, z0, x1, height, z0 + 1, walk)
        for x in range(x0, x1 + 1):
            if x % 2 == 0: c.set(x, height + 1, z0, crenel)
    else:
        c.fill(x0, 1, z0, x0 + 1, height, z1, wall)
        c.fill(x0, height, z0, x0 + 1, height, z1, walk)
        for z in range(z0, z1 + 1):
            if z % 2 == 0: c.set(x0, height + 1, z, crenel)

def house(c, x0, z0, w, d, facing, style, floors=1, beds=1, job=None, people=(), loot=None, bed_color='red'):
    """A house on the floor (y=1): corner logs, walls, windows, a door facing out, beds, a job block, a pitched roof."""
    x1, z1 = x0 + w - 1, z0 + d - 1
    logs, planks, wallb, roofm, glass = style
    top = 1 + floors * 4
    c.fill(x0, 1, z0, x1, 1, z1, planks)
    for y in range(2, top + 1):
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                edge = x in (x0, x1) or z in (z0, z1)
                corner = x in (x0, x1) and z in (z0, z1)
                c.set(x, y, z, logs if corner else (wallb if edge else 'air'))
    for f in range(1, floors):
        c.fill(x0 + 1, 1 + f * 4, z0 + 1, x1 - 1, 1 + f * 4, z1 - 1, planks)
        c.set(x1 - 1, 1 + f * 4, z1 - 1, 'air')
        for y in range(2 + (f - 1) * 4, 2 + f * 4):
            c.set(x1 - 1, y, z1 - 1, 'ladder[facing=north]')
    for f in range(floors):
        wy = 3 + f * 4
        for x in range(x0 + 2, x1 - 1, 2):
            c.set(x, wy, z0, glass); c.set(x, wy, z1, glass)
        for z in range(z0 + 2, z1 - 1, 2):
            c.set(x0, wy, z, glass); c.set(x1, wy, z, glass)
    c.fill(x0, top + 1, z0, x1, top + 1, z1, planks)
    gable(c, x0, z0, x1, z1, top + 1, roofm, w >= d)
    gable_ends(c, x0, z0, x1, z1, top + 1, w >= d, wallb)
    # the door, in the middle of the facing side
    if facing in ('north', 'south'):
        dx, dz = (x0 + w // 2, z0 if facing == 'north' else z1)
    else:
        dx, dz = (x0 if facing == 'west' else x1, z0 + d // 2)
    door(c, dx, 2, dz, facing, logs.replace('_log', '').replace('stripped_', '') if 'log' in logs else 'oak')
    ox, oz = DIRS[facing]
    c.set(dx + ox, 1, dz + oz, 'cobblestone')
    # inside: beds against the back wall, a job block and a chest
    back = OPP[facing]
    spots = [(x, z) for x in range(x0 + 1, x1) for z in range(z0 + 1, z1)
             if abs(x - dx) + abs(z - dz) > 2]
    c.r.shuffle(spots)
    used = set()
    def free(x, z): return (x, z) not in used and c.get(x, 2, z) == 'air'
    placed_beds = 0
    for x, z in spots:
        if placed_beds >= beds: break
        bx, bz = DIRS[back]
        hx, hz = x + bx, z + bz
        if free(x, z) and x0 < hx < x1 and z0 < hz < z1 and free(hx, hz):
            bed(c, x, 2, z, back, bed_color); used |= {(x, z), (hx, hz)}; placed_beds += 1
    for blk in ([job] if job else []) + ['chest']:
        for x, z in spots:
            if free(x, z):
                if blk == 'chest': chest(c, x, 2, z, facing, loot)
                else: c.set(x, 2, z, blk)
                used.add((x, z)); break
    c.set(x0 + 1, top, z0 + 1, 'lantern[hanging=true]')
    for i, who in enumerate(people):
        for x, z in spots:
            if free(x, z):
                c.entity(x, 2, z, who); used.add((x, z)); break
    return dx + ox, dz + oz

def farm(c, x0, z0, w, d, crop='wheat'):
    for x in range(x0, x0 + w):
        for z in range(z0, z0 + d):
            if x in (x0, x0 + w - 1) or z in (z0, z0 + d - 1):
                c.set(x, 1, z, 'oak_log[axis=x]' if z in (z0, z0 + d - 1) else 'oak_log[axis=z]')
            elif x == x0 + w // 2:
                c.set(x, 1, z, 'water')
            else:
                c.set(x, 1, z, 'farmland[moisture=7]')
                c.set(x, 2, z, f'{crop}[age={c.r.randint(2, 7)}]')

def well(c, cx, cz, rim='cobblestone', roof='oak'):
    c.fill(cx - 2, 0, cz - 2, cx + 2, 1, cz + 2, rim)
    c.fill(cx - 1, 0, cz - 1, cx + 1, 1, cz + 1, 'water')
    for x, z in ((cx - 2, cz - 2), (cx + 2, cz - 2), (cx - 2, cz + 2), (cx + 2, cz + 2)):
        c.fill(x, 2, z, x, 4, z, f'{roof}_fence')
    c.fill(cx - 2, 5, cz - 2, cx + 2, 5, cz + 2, f'{roof}_slab[type=bottom]')
    c.set(cx, 4, cz, 'lantern[hanging=true]')

def stall(c, x0, z0, wool, facing='south'):
    for x, z in ((x0, z0), (x0 + 2, z0), (x0, z0 + 2), (x0 + 2, z0 + 2)):
        c.fill(x, 2, z, x, 3, z, 'oak_fence')
    c.fill(x0, 4, z0, x0 + 2, 4, z0 + 2, f'{wool}_wool')
    c.fill(x0, 2, z0 + (2 if facing == 'north' else 0), x0 + 2, 2, z0 + (2 if facing == 'north' else 0), 'barrel[facing=up]')

def ground(c, s, under='stone'):
    c.fill(0, 0, 0, c.w - 1, 0, c.d - 1, under)
    c.fill(0, 1, 0, c.w - 1, 1, c.d - 1, s)

def road(c, x0, z0, x1, z1, mat):
    c.fill(x0, 1, z0, x1, 1, z1, mat)

# ---------------------------------------------------------------------------------------------- the structures
DARK = ('dark_oak_log', 'dark_oak_planks', 'deepslate_bricks', 'dark_oak', 'gray_stained_glass_pane')
DARK2 = ('dark_oak_log', 'dark_oak_planks', 'dark_oak_planks', 'deepslate_brick', 'iron_bars')
OAK = ('oak_log', 'oak_planks', 'white_terracotta', 'spruce', 'glass_pane')
SPRUCE = ('spruce_log', 'spruce_planks', 'spruce_planks', 'dark_oak', 'glass_pane')
STONE = ('stripped_oak_log', 'oak_planks', 'stone_bricks', 'brick', 'glass_pane')
BIRCH = ('birch_log', 'birch_planks', 'smooth_sandstone', 'spruce', 'glass_pane')

def mixed(c, *states):
    return lambda x, y, z: states[(x * 7 + y * 13 + z * 5 + c.r.randint(0, 3)) % len(states)]

def illager_fortress():
    c = Canvas('illager_fortress', 64, 40, 64, 101)
    ground(c, mixed(c, 'cobbled_deepslate', 'gravel', 'coarse_dirt', 'cobbled_deepslate'), 'deepslate')
    wall = mixed(c, 'polished_blackstone_bricks', 'polished_blackstone_bricks', 'cracked_polished_blackstone_bricks', 'blackstone')
    # outer curtain walls between corner towers, a gate on the south
    for x0, z0, x1, z1 in ((8, 0, 55, 0), (8, 62, 26, 62), (37, 62, 55, 62), (0, 8, 0, 55), (62, 8, 62, 55)):
        curtain(c, x0, z0, x1, z1, 12, wall, 'dark_oak_planks', 'polished_blackstone_brick_wall')
    # gatehouse
    c.fill(27, 1, 60, 36, 16, 63, 'polished_blackstone_bricks')
    c.air(29, 2, 60, 34, 8, 63)
    c.fill(29, 9, 60, 34, 9, 63, 'polished_blackstone_brick_slab[type=top]')
    for x in range(29, 35): c.set(x, 8, 63, 'iron_bars')
    battlement(c, 27, 60, 36, 63, 17, 'polished_blackstone_brick_wall')
    for x in (28, 35):
        c.set(x, 14, 63, 'polished_blackstone_bricks'); banner(c, x, 13, 63, 'south', ominous=True)
    # corner towers
    tops = []
    for x0, z0 in ((0, 0), (55, 0), (0, 55), (55, 55)):
        tops.append(tower(c, x0, z0, 9, 20, 'polished_blackstone_bricks', 'dark_oak_planks', 'dark_oak', None, ('white', True)))
    # the keep
    kx0, kz0, k = 20, 18, 22
    outline(c, kx0, 1, kz0, kx0 + k - 1, 26, kz0 + k - 1, 'deepslate_bricks')
    c.air(kx0 + 1, 2, kz0 + 1, kx0 + k - 2, 26, kz0 + k - 2)
    for x in range(kx0, kx0 + k, 4):
        for z in (kz0, kz0 + k - 1): c.fill(x, 1, z, x, 26, z, 'dark_oak_log')
    for z in range(kz0, kz0 + k, 4):
        for x in (kx0, kx0 + k - 1): c.fill(x, 1, z, x, 26, z, 'dark_oak_log')
    for y in (9, 17):
        c.fill(kx0 + 1, y, kz0 + 1, kx0 + k - 2, y, kz0 + k - 2, 'dark_oak_planks')
    c.fill(kx0, 26, kz0, kx0 + k - 1, 26, kz0 + k - 1, 'deepslate_bricks')
    for y in range(2, 27): c.set(kx0 + 1, y, kz0 + 1, 'ladder[facing=south]')
    battlement(c, kx0, kz0, kx0 + k - 1, kz0 + k - 1, 27, 'deepslate_brick_wall')
    for y in (4, 12, 20):
        for x in range(kx0 + 3, kx0 + k - 3, 4):
            c.set(x, y, kz0, 'iron_bars'); c.set(x, y, kz0 + k - 1, 'iron_bars')
        for z in range(kz0 + 3, kz0 + k - 3, 4):
            c.set(kx0, y, z, 'iron_bars'); c.set(kx0 + k - 1, y, z, 'iron_bars')
    door(c, kx0 + k // 2, 2, kz0 + k - 1, 'south', 'dark_oak')
    for x in (kx0 + 6, kx0 + k - 7):
        banner(c, x, 20, kz0 + k, 'south', ominous=True); banner(c, x, 20, kz0 - 1, 'north', ominous=True)
    # the keep inside: a war room below, the treasury above, the lord's hall on top
    c.fill(kx0 + 8, 2, kz0 + 8, kx0 + 13, 2, kz0 + 13, 'dark_oak_planks')
    for x, z in ((kx0 + 3, kz0 + 18), (kx0 + 18, kz0 + 18), (kx0 + 18, kz0 + 3)):
        chest(c, x, 2, z, 'north', 'minecraft:chests/pillager_outpost')
    for x, z in ((kx0 + 4, kz0 + 4), (kx0 + 17, kz0 + 17)):
        chest(c, x, 10, z, 'south', 'minecraft:chests/woodland_mansion')
    c.fill(kx0 + 9, 18, kz0 + 4, kx0 + 12, 18, kz0 + 17, 'red_carpet')
    for x, y, z in ((kx0 + 5, 20, kz0 + 5), (kx0 + 16, 20, kz0 + 16), (kx0 + 5, 12, kz0 + 16), (kx0 + 16, 4, kz0 + 5)):
        c.set(x, y, z, 'soul_lantern[hanging=true]')
    c.set(kx0 + 10, 18, kz0 + 3, 'crying_obsidian'); c.set(kx0 + 11, 18, kz0 + 3, 'crying_obsidian')
    # barracks along the walls
    house(c, 4, 14, 12, 9, 'east', DARK, beds=0, job='crafting_table', loot='minecraft:chests/pillager_outpost')
    house(c, 48, 14, 12, 9, 'west', DARK, beds=0, job='smithing_table', loot='minecraft:chests/pillager_outpost')
    house(c, 4, 40, 12, 9, 'east', DARK2, beds=0, job='grindstone[face=floor,facing=north]', loot='minecraft:chests/simple_dungeon')
    # a pen for the ravager, a pyre, lanterns
    outline(c, 46, 40, 46, 58, 2, 54, 'dark_oak_fence')
    c.air(47, 2, 41, 57, 2, 53)
    for x, z in ((16, 54), (46, 30), (16, 32), (30, 48)):
        lamp_post(c, x, 2, z, 'dark_oak_fence', 'soul_lantern')
    c.set(31, 1, 52, 'netherrack'); c.set(31, 2, 52, 'fire')
    # the garrison
    for x, y, z in tops:
        c.entity(x, y, z, illager('pillager'))
    for x in (10, 20, 30, 40, 50):
        c.entity(x, 13, 1, illager('pillager'))
    for x, z in ((30, 50), (34, 52), (12, 34), (52, 34), (30, 12), (36, 46)):
        c.entity(x, 2, z, illager('vindicator'))
    c.entity(52, 2, 47, {'id': 'minecraft:ravager', 'PersistenceRequired': Byte(1)})
    c.entity(kx0 + 10, 10, kz0 + 10, illager('witch'))
    c.entity(kx0 + 6, 2, kz0 + 6, illager('evoker'))
    c.entity(kx0 + 10, 18, kz0 + 6, illager('evoker', 5, ('要塞の邪術師', 'dark_purple')))
    c.entity(kx0 + 11, 18, kz0 + 8, illager('vindicator', 5, ('要塞の隊長', 'dark_red'),
             gear((item('netherite_axe', 1, {'sharpness': 5, 'fire_aspect': 2}), None),
                  (item('iron_boots'), item('iron_leggings'), item('iron_chestplate'), item('iron_helmet'))), warlord=True))
    return c

def illager_city():
    c = Canvas('illager_city', 112, 44, 112, 202)
    ground(c, mixed(c, 'coarse_dirt', 'podzol', 'gravel', 'coarse_dirt', 'mud'), 'dirt')
    palisade = lambda x, y, z: 'dark_oak_log' if (x + z) % 5 else 'stripped_dark_oak_log'
    # the palisade, with towers every 27 blocks and gates north and south
    for i in range(112):
        for y in range(1, 9):
            for x, z in ((i, 0), (i, 111), (0, i), (111, i)):
                if (x, z) in ((54, 0), (55, 0), (56, 0), (57, 0), (54, 111), (55, 111), (56, 111), (57, 111)) and y < 6:
                    continue
                c.set(x, y, z, palisade(x, y, z))
        for x, z in ((i, 0), (i, 111), (0, i), (111, i)):
            if i % 2 == 0: c.set(x, 9, z, 'dark_oak_fence')
    tops = []
    for x0 in (0, 34, 69, 103):
        for z0 in (0, 103):
            tops.append(tower(c, x0, z0, 9, 16, 'dark_oak_planks', 'dark_oak_planks', 'dark_oak', 'dark_oak_fence', ('white', True), 'dark_oak_fence'))
    for z0 in (34, 69):
        for x0 in (0, 103):
            tops.append(tower(c, x0, z0, 9, 16, 'dark_oak_planks', 'dark_oak_planks', 'dark_oak', 'dark_oak_fence', ('white', True), 'dark_oak_fence'))
    # streets
    road(c, 52, 1, 59, 110, 'cobbled_deepslate')
    road(c, 10, 52, 101, 59, 'cobbled_deepslate')
    for z in range(4, 108, 8):
        lamp_post(c, 51, 2, z, 'dark_oak_fence', 'soul_lantern'); lamp_post(c, 60, 2, z, 'dark_oak_fence', 'soul_lantern')
    # the dark houses of the quarters
    plots = [(12, 12), (28, 12), (64, 12), (80, 12), (12, 30), (28, 30),
             (12, 64), (28, 64), (64, 64), (80, 64), (12, 82), (28, 82), (64, 82), (80, 82)]
    folk = ['pillager', 'vindicator', 'pillager', 'witch', 'vindicator', 'pillager', 'evoker',
            'pillager', 'vindicator', 'pillager', 'illusioner', 'vindicator', 'pillager', 'vindicator']
    for i, (x0, z0) in enumerate(plots):
        face = 'east' if x0 < 52 else 'west'
        style = DARK if i % 2 == 0 else DARK2
        loot = ['minecraft:chests/pillager_outpost', 'minecraft:chests/simple_dungeon', 'minecraft:chests/woodland_mansion'][i % 3]
        house(c, x0 + 1, z0 + 1, 13, 11, face, style, floors=2 if i % 3 == 0 else 1, beds=0,
              job=['crafting_table', 'fletching_table', 'smithing_table', 'cauldron'][i % 4], loot=loot,
              people=[illager(folk[i]), illager('pillager' if i % 2 else 'vindicator')])
    # the cathedral of the evokers in the north-east block
    cx0, cz0 = 64, 28
    w, d = 30, 20
    outline(c, cx0, 1, cz0, cx0 + w - 1, 14, cz0 + d - 1, 'deepslate_bricks')
    c.air(cx0 + 1, 2, cz0 + 1, cx0 + w - 2, 14, cz0 + d - 2)
    c.fill(cx0, 1, cz0, cx0 + w - 1, 1, cz0 + d - 1, 'polished_deepslate')
    for x in range(cx0 + 3, cx0 + w - 3, 4):
        for z in (cz0, cz0 + d - 1):
            c.fill(x, 5, z, x, 11, z, 'purple_stained_glass_pane')
    gable(c, cx0, cz0, cx0 + w - 1, cz0 + d - 1, 15, 'deepslate_brick', True, 'deepslate_bricks')
    for x in range(cx0 + 1, cx0 + w - 1):
        c.fill(x, 15, cz0 + 1, x, 15, cz0 + d - 2, 'deepslate_bricks')
    # its spire
    tower(c, cx0 + w - 8, cz0 + 6, 7, 30, 'deepslate_bricks', 'dark_oak_planks', 'deepslate_brick', None, ('white', True))
    c.fill(cx0 + 2, 2, cz0 + 8, cx0 + 4, 2, cz0 + 11, 'crying_obsidian')
    c.set(cx0 + 3, 3, cz0 + 9, 'soul_lantern[hanging=false]'); c.set(cx0 + 3, 3, cz0 + 10, 'soul_lantern[hanging=false]')
    c.fill(cx0 + 5, 2, cz0 + 9, cx0 + w - 9, 2, cz0 + 10, 'red_carpet')
    door(c, cx0 + w // 2, 2, cz0 + d - 1, 'south', 'dark_oak')
    for x, z in ((cx0 + 2, cz0 + 2), (cx0 + 2, cz0 + d - 3), (cx0 + 6, cz0 + 2)):
        chest(c, x, 2, z, 'east', 'minecraft:chests/woodland_mansion')
    for x in range(cx0 + 6, cx0 + w - 9, 4):
        c.set(x, 13, cz0 + 9, 'soul_lantern[hanging=true]')
    c.entity(cx0 + 5, 2, cz0 + 9, illager('evoker', 5, ('邪悪な都の大司教', 'dark_purple')))
    c.entity(cx0 + 8, 2, cz0 + 6, illager('evoker', 4))
    c.entity(cx0 + 8, 2, cz0 + 13, illager('evoker', 4))
    c.entity(cx0 + 12, 2, cz0 + 9, illager('illusioner', 4))
    # a ravager pen and the market of stolen goods
    outline(c, 66, 2, 98, 88, 2, 108, 'dark_oak_fence')
    c.air(67, 2, 99, 87, 2, 107)
    for x in (70, 78, 84):
        c.entity(x, 2, 103, {'id': 'minecraft:ravager', 'PersistenceRequired': Byte(1)})
    for i, x in enumerate(range(14, 46, 5)):
        stall(c, x, 46, ['black', 'gray', 'red', 'purple', 'brown', 'cyan', 'black'][i % 7])
        chest(c, x + 1, 2, 47, 'south', 'minecraft:chests/village/village_weaponsmith' if i % 2 else 'minecraft:chests/village/village_toolsmith')
    # the guard on the towers and gates
    for x, y, z in tops:
        c.entity(x, y, z, illager('pillager'))
    for x, z in ((54, 4), (57, 4), (54, 107), (57, 107)):
        c.entity(x, 2, z, illager('vindicator'))
    c.entity(56, 2, 56, illager('vindicator', 5, ('邪悪な都の将軍', 'dark_red'),
             gear((item('netherite_axe', 1, {'sharpness': 6, 'fire_aspect': 2, 'knockback': 1}), None),
                  (item('diamond_boots'), item('diamond_leggings'), item('diamond_chestplate'), item('diamond_helmet'))), warlord=True))
    return c

def villager_fortress():
    c = Canvas('villager_fortress', 64, 40, 64, 303)
    ground(c, mixed(c, 'stone_bricks', 'cobblestone', 'gravel', 'stone_bricks', 'andesite'), 'stone')
    road(c, 29, 1, 34, 63, 'dirt_path')
    wall = 'stone_bricks'
    for x0, z0, x1, z1 in ((8, 0, 55, 0), (8, 62, 26, 62), (37, 62, 55, 62), (0, 8, 0, 55), (62, 8, 62, 55)):
        curtain(c, x0, z0, x1, z1, 11, wall, 'spruce_planks', 'stone_brick_wall')
    c.fill(27, 1, 60, 36, 15, 63, 'stone_bricks')
    c.air(29, 2, 60, 34, 7, 63)
    c.fill(29, 8, 60, 34, 8, 63, 'stone_brick_slab[type=top]')
    battlement(c, 27, 60, 36, 63, 16, 'stone_brick_wall')
    for x in (28, 35):
        banner(c, x, 12, 63, 'south', 'blue')
    tops = []
    for x0, z0 in ((0, 0), (55, 0), (0, 55), (55, 55)):
        tops.append(tower(c, x0, z0, 9, 18, 'stone_bricks', 'spruce_planks', 'spruce', None, ('blue', False), 'glass_pane'))
    # the keep: a hall below, the commander's floor above
    kx0, kz0, k = 22, 12, 20
    outline(c, kx0, 1, kz0, kx0 + k - 1, 18, kz0 + k - 1, 'stone_bricks')
    c.air(kx0 + 1, 2, kz0 + 1, kx0 + k - 2, 18, kz0 + k - 2)
    c.fill(kx0 + 1, 10, kz0 + 1, kx0 + k - 2, 10, kz0 + k - 2, 'spruce_planks')
    for y in range(2, 11): c.set(kx0 + 1, y, kz0 + 1, 'ladder[facing=south]')
    c.set(kx0 + 1, 10, kz0 + 1, 'ladder[facing=south]')
    c.fill(kx0, 18, kz0, kx0 + k - 1, 18, kz0 + k - 1, 'stone_bricks')
    battlement(c, kx0, kz0, kx0 + k - 1, kz0 + k - 1, 19, 'stone_brick_wall')
    for y in (4, 13):
        for x in range(kx0 + 3, kx0 + k - 3, 3):
            c.set(x, y, kz0, 'glass_pane'); c.set(x, y, kz0 + k - 1, 'glass_pane')
    door(c, kx0 + k // 2, 2, kz0 + k - 1, 'south', 'spruce')
    c.fill(kx0 + 8, 2, kz0 + 3, kx0 + 11, 2, kz0 + 16, 'blue_carpet')
    for x in (kx0 + 6, kx0 + k - 7):
        banner(c, x, 14, kz0 + k, 'south', 'blue')
    for x, z in ((kx0 + 3, kz0 + 3), (kx0 + 16, kz0 + 3)):
        chest(c, x, 2, z, 'south', 'minecraft:chests/village/village_weaponsmith')
    chest(c, kx0 + 3, 11, kz0 + 16, 'north', 'minecraft:chests/village/village_armorer')
    for x, z in ((kx0 + 4, kz0 + 4), (kx0 + 15, kz0 + 15)):
        c.set(x, 9, z, 'lantern[hanging=true]')
    # barracks, armoury, smithy, stables, a training yard, a well
    people = [villager('armorer', 4, 'fortress'), villager('weaponsmith', 4, 'fortress'), villager('toolsmith', 3, 'fortress'),
              villager('fletcher', 3, 'fortress'), villager('mason', 3, 'fortress'), villager('butcher', 3, 'fortress'),
              villager('leatherworker', 3, 'fortress'), villager('cleric', 3, 'fortress')]
    house(c, 4, 12, 13, 10, 'east', STONE, beds=4, job='blast_furnace[facing=east,lit=false]', people=people[0:2], loot='minecraft:chests/village/village_armorer', bed_color='blue')
    house(c, 47, 12, 13, 10, 'west', STONE, beds=4, job='smithing_table', people=people[2:4], loot='minecraft:chests/village/village_toolsmith', bed_color='blue')
    house(c, 4, 38, 13, 10, 'east', SPRUCE, beds=3, job='fletching_table', people=people[4:6], bed_color='blue')
    house(c, 47, 38, 13, 10, 'west', SPRUCE, beds=3, job='stonecutter[facing=north]', people=people[6:8], bed_color='blue')
    for x in range(20, 27, 3):
        c.set(x, 2, 44, 'hay_block'); c.set(x, 3, 44, 'carved_pumpkin[facing=south]')
    well(c, 44, 50, 'cobblestone', 'spruce')
    for x, z in ((24, 36), (40, 36), (24, 52), (40, 52)):
        lamp_post(c, x, 2, z, 'spruce_fence')
    c.set(26, 2, 40, 'anvil[facing=north]'); c.set(27, 2, 40, 'grindstone[face=floor,facing=north]')
    c.set(38, 2, 40, 'brewing_stand'); c.set(37, 2, 40, 'cauldron')
    for x, y, z in tops:
        c.entity(x, y, z, guard(2))
    for x, z in ((30, 58), (34, 58), (31, 34), (33, 34)):
        c.entity(x, 2, z, guard(2))
    c.entity(kx0 + 10, 11, kz0 + 10, guard(3))
    for x, z in ((20, 30), (44, 30), (32, 46)):
        c.entity(x, 2, z, golem())
    return c

def trader_exchange():
    c = Canvas('trader_exchange', 48, 32, 48, 404)
    ground(c, mixed(c, 'smooth_stone', 'stone_bricks', 'polished_andesite', 'smooth_stone'), 'stone')
    road(c, 21, 0, 26, 47, 'dirt_path'); road(c, 0, 21, 47, 26, 'dirt_path')
    # the exchange hall: a timber frame over the middle, open on its sides
    x0, z0, x1, z1 = 12, 12, 35, 35
    for x in range(x0, x1 + 1, 4):
        for z in (z0, z1):
            c.fill(x, 2, z, x, 7, z, 'stripped_spruce_log')
    for z in range(z0, z1 + 1, 4):
        for x in (x0, x1):
            c.fill(x, 2, z, x, 7, z, 'stripped_spruce_log')
    c.fill(x0, 8, z0, x1, 8, z1, 'spruce_planks')
    gable(c, x0, z0, x1, z1, 9, 'spruce', True)
    for x in range(x0 + 1, x1):
        c.fill(x, 9, z0 + 1, x, 9, z1 - 1, 'spruce_planks')
    for x in range(x0 + 2, x1 - 1, 4):
        for z in range(z0 + 2, z1 - 1, 4):
            c.set(x, 7, z, 'lantern[hanging=true]')
    # a fountain in the middle
    c.fill(21, 1, 21, 26, 1, 26, 'stone_bricks'); c.fill(22, 1, 22, 25, 1, 25, 'water')
    c.fill(23, 1, 23, 24, 3, 24, 'chiseled_stone_bricks'); c.set(23, 4, 23, 'water')
    # stalls round the hall, each with a trader
    colours = ['red', 'yellow', 'lime', 'light_blue', 'orange', 'magenta', 'cyan', 'purple']
    spots = [(14, 14), (19, 14), (28, 14), (31, 14), (14, 31), (19, 31), (28, 31), (31, 31)]
    for i, (sx, sz) in enumerate(spots):
        stall(c, sx, sz if sz < 20 else sz - 2, colours[i], 'south' if sz < 20 else 'north')
        if i < 6:
            c.entity(sx + 1, 2, (sz + 1) if sz < 20 else (sz - 1), trader())
    # the llama pen and the guards
    outline(c, 36, 2, 2, 46, 2, 12, 'spruce_fence'); c.air(37, 2, 3, 45, 2, 11)
    c.set(41, 2, 12, 'spruce_fence_gate[facing=south,open=false]')
    for i, (x, z) in enumerate(((38, 5), (41, 5), (44, 5), (38, 9), (41, 9), (44, 9))):
        c.entity(x, 2, z, llama(i % 4))
    c.fill(37, 2, 3, 37, 2, 3, 'hay_block')
    for x, z in ((3, 3), (44, 44), (3, 44)):
        lamp_post(c, x, 2, z, 'spruce_fence')
    for x, z in ((20, 6), (27, 6), (20, 41), (27, 41)):
        c.entity(x, 2, z, guard(3))
    for x, z in ((6, 24), (41, 24)):
        c.entity(x, 2, z, golem())
    for i, (x, z) in enumerate(((5, 30), (8, 30), (5, 34))):
        chest(c, x, 2, z, 'east', 'minecraft:chests/village/village_weaponsmith' if i == 0 else None, 'barrel')
    banner(c, 23, 6, 11, 'north', 'yellow'); banner(c, 24, 6, 36, 'south', 'yellow')
    return c

def villager_kingdom():
    W = 128
    c = Canvas('villager_kingdom', W, 52, W, 505)
    ground(c, mixed(c, 'grass_block', 'grass_block', 'grass_block', 'grass_block', 'grass_block', 'grass_block', 'coarse_dirt'), 'stone')
    # roads: a cross of main streets and a ring inside the walls
    road(c, 60, 0, 67, W - 1, 'stone_bricks'); road(c, 0, 60, W - 1, 67, 'stone_bricks')
    road(c, 6, 6, W - 7, 9, 'dirt_path'); road(c, 6, W - 10, W - 7, W - 7, 'dirt_path')
    road(c, 6, 6, 9, W - 7, 'dirt_path'); road(c, W - 10, 6, W - 7, W - 7, 'dirt_path')
    # the outer walls with gatehouses on each side and towers at the corners and between
    wall = 'stone_bricks'
    for a, b in ((8, 56), (71, 119)):
        curtain(c, a, 0, b, 0, 12, wall, 'spruce_planks', 'stone_brick_wall')
        curtain(c, a, W - 2, b, W - 2, 12, wall, 'spruce_planks', 'stone_brick_wall')
        curtain(c, 0, a, 0, b, 12, wall, 'spruce_planks', 'stone_brick_wall')
        curtain(c, W - 2, a, W - 2, b, 12, wall, 'spruce_planks', 'stone_brick_wall')
    for gx, gz, along in ((57, 0, 'x'), (57, W - 4, 'x'), (0, 57, 'z'), (W - 4, 57, 'z')):
        if along == 'x':
            c.fill(gx, 1, gz, gx + 13, 16, gz + 3, 'stone_bricks'); c.air(gx + 3, 2, gz, gx + 10, 8, gz + 3)
            battlement(c, gx, gz, gx + 13, gz + 3, 17, 'stone_brick_wall')
            for x in (gx + 1, gx + 12):
                banner(c, x, 13, gz - 1 if gz == 0 else gz + 4, 'north' if gz == 0 else 'south', 'red')
        else:
            c.fill(gx, 1, gz, gx + 3, 16, gz + 13, 'stone_bricks'); c.air(gx, 2, gz + 3, gx + 3, 8, gz + 10)
            battlement(c, gx, gz, gx + 3, gz + 13, 17, 'stone_brick_wall')
            for z in (gz + 1, gz + 12):
                banner(c, gx - 1 if gx == 0 else gx + 4, 13, z, 'west' if gx == 0 else 'east', 'red')
    tops = []
    for x0, z0 in ((0, 0), (W - 9, 0), (0, W - 9), (W - 9, W - 9)):
        tops.append(tower(c, x0, z0, 9, 20, 'stone_bricks', 'spruce_planks', 'spruce', None, ('red', False), 'glass_pane'))
    # the castle in the middle: an inner wall, four towers, the keep with its throne hall
    cx0, cz0, cw = 46, 46, 36
    for a, b in ((cx0 + 4, cx0 + cw - 5),):
        curtain(c, a, cz0, b, cz0, 9, 'polished_andesite', 'spruce_planks', 'andesite_wall')
        curtain(c, cx0, a, cx0, b, 9, 'polished_andesite', 'spruce_planks', 'andesite_wall')
        curtain(c, cx0 + cw - 2, a, cx0 + cw - 2, b, 9, 'polished_andesite', 'spruce_planks', 'andesite_wall')
        curtain(c, a, cz0 + cw - 2, cx0 + 14, cz0 + cw - 2, 9, 'polished_andesite', 'spruce_planks', 'andesite_wall')
        curtain(c, cx0 + 22, cz0 + cw - 2, b, cz0 + cw - 2, 9, 'polished_andesite', 'spruce_planks', 'andesite_wall')
    for x0, z0 in ((cx0, cz0), (cx0 + cw - 6, cz0), (cx0, cz0 + cw - 6), (cx0 + cw - 6, cz0 + cw - 6)):
        tops.append(tower(c, x0, z0, 6, 14, 'polished_andesite', 'spruce_planks', 'dark_oak', None, ('red', False), 'glass_pane'))
    c.fill(cx0 + 2, 1, cz0 + 2, cx0 + cw - 3, 1, cz0 + cw - 3, 'polished_andesite')
    kx0, kz0, k = cx0 + 9, cz0 + 7, 18
    outline(c, kx0, 1, kz0, kx0 + k - 1, 24, kz0 + k - 1, 'smooth_stone')
    c.air(kx0 + 1, 2, kz0 + 1, kx0 + k - 2, 24, kz0 + k - 2)
    for x in (kx0, kx0 + k - 1):
        for z in (kz0, kz0 + k - 1):
            c.fill(x, 1, z, x, 26, z, 'chiseled_stone_bricks')
    c.fill(kx0 + 1, 12, kz0 + 1, kx0 + k - 2, 12, kz0 + k - 2, 'spruce_planks')
    for y in range(2, 13): c.set(kx0 + 1, y, kz0 + 1, 'ladder[facing=south]')
    c.fill(kx0, 24, kz0, kx0 + k - 1, 24, kz0 + k - 1, 'smooth_stone')
    pyramid(c, kx0 - 1, kz0 - 1, kx0 + k, kz0 + k, 25, 'dark_oak', 'gold_block')
    for y in (5, 9, 16, 20):
        for x in range(kx0 + 3, kx0 + k - 3, 3):
            c.set(x, y, kz0, 'glass_pane'); c.set(x, y, kz0 + k - 1, 'glass_pane')
        for z in range(kz0 + 3, kz0 + k - 3, 3):
            c.set(kx0, y, z, 'glass_pane'); c.set(kx0 + k - 1, y, z, 'glass_pane')
    door(c, kx0 + k // 2, 2, kz0 + k - 1, 'south', 'dark_oak'); door(c, kx0 + k // 2 - 1, 2, kz0 + k - 1, 'south', 'dark_oak')
    c.fill(kx0 + k // 2 - 1, 2, kz0 + 3, kx0 + k // 2, 2, kz0 + k - 2, 'red_carpet')
    c.fill(kx0 + 6, 2, kz0 + 1, kx0 + 11, 2, kz0 + 2, 'gold_block')
    c.set(kx0 + 8, 3, kz0 + 2, 'dark_oak_stairs[facing=south,half=bottom]'); c.set(kx0 + 9, 3, kz0 + 2, 'dark_oak_stairs[facing=south,half=bottom]')
    for x in (kx0 + 3, kx0 + k - 4):
        for z in range(kz0 + 4, kz0 + k - 3, 4):
            c.set(x, 11, z, 'lantern[hanging=true]')
        banner(c, x, 8, kz0 + 1, 'south', 'red')
    for x, z in ((kx0 + 2, kz0 + 14), (kx0 + 15, kz0 + 14)):
        chest(c, x, 2, z, 'north', 'minecraft:chests/village/village_weaponsmith')
    chest(c, kx0 + 3, 13, kz0 + 3, 'south', 'minecraft:chests/stronghold_corridor')
    c.set(kx0 + 8, 13, kz0 + 8, 'bell[attachment=floor,facing=south]')
    # the quarters: four blocks of houses, farms, a market, a church
    styles = [OAK, SPRUCE, STONE, BIRCH]
    jobs = {'farmer': 'composter', 'fisherman': 'barrel[facing=up]', 'shepherd': 'loom[facing=north]', 'fletcher': 'fletching_table',
            'cleric': 'brewing_stand', 'librarian': 'lectern[facing=north]', 'cartographer': 'cartography_table', 'armorer': 'blast_furnace[facing=north,lit=false]',
            'weaponsmith': 'grindstone[face=floor,facing=north]', 'toolsmith': 'smithing_table', 'butcher': 'smoker[facing=north,lit=false]',
            'leatherworker': 'cauldron', 'mason': 'stonecutter[facing=north]'}
    order = ['farmer', 'farmer', 'librarian', 'cleric', 'armorer', 'weaponsmith', 'toolsmith', 'fletcher', 'butcher', 'shepherd',
             'mason', 'leatherworker', 'cartographer', 'fisherman', 'farmer', 'librarian', 'weaponsmith', 'armorer', 'mason', 'toolsmith']
    plots = []
    for bx, bz in ((12, 12), (72, 12), (12, 72), (72, 72)):
        for i in range(3):
            for j in range(2):
                plots.append((bx + i * 15, bz + j * 22, j == 0))
    pi = 0
    for n, (x0, z0, top_row) in enumerate(plots):
        if x0 + 13 >= 46 and x0 <= 82 and z0 + 12 >= 46 and z0 <= 82:
            continue  # the castle
        if pi >= len(order): break
        prof = order[pi]; pi += 1
        face = 'south' if top_row else 'north'
        people = [villager(prof, 3 + n % 3, 'kingdom')]
        if n % 3 == 0: people.append(villager(order[(pi + 5) % len(order)], 2, 'kingdom'))
        if n % 4 == 1: people.append(villager('none', 1, 'kingdom', baby=True))
        house(c, x0, z0 + (2 if top_row else 0), 12, 9, face, styles[n % 4], floors=1 + (n % 3 == 0), beds=len(people) + 1,
              job=jobs.get(prof), people=people, loot=None, bed_color=['red', 'blue', 'green', 'yellow'][n % 4])
    # farms by the walls
    for x0, z0 in ((12, 46), (28, 46), (88, 46), (100, 84)):
        farm(c, x0, z0, 11, 9)
    farm(c, 12, 107, 11, 9, 'carrots'); farm(c, 100, 24, 11, 9, 'potatoes')
    # the market square south of the castle
    for i, x in enumerate(range(50, 80, 5)):
        stall(c, x, 86, ['red', 'yellow', 'lime', 'light_blue', 'orange', 'white'][i % 6])
    well(c, 63, 92, 'stone_bricks', 'spruce')
    for z in range(12, W - 12, 10):
        lamp_post(c, 59, 2, z); lamp_post(c, 68, 2, z)
    for x in range(12, W - 12, 10):
        if not 46 <= x <= 82: lamp_post(c, x, 2, 59); lamp_post(c, x, 2, 68)
    # people of the court and the guard
    c.entity(kx0 + 8, 3, kz0 + 3, villager('cleric', 5, 'kingdom'))
    c.entity(kx0 + 9, 3, kz0 + 4, villager('librarian', 5, 'kingdom'))
    for x, y, z in tops:
        c.entity(x, y, z, guard(2))
    for x, z in ((60, 3), (67, 3), (60, W - 4), (67, W - 4), (3, 60), (3, 67), (W - 4, 60), (W - 4, 67)):
        c.entity(x, 2, z, guard(2))
    for x, z in ((kx0 + 6, kz0 + 10), (kx0 + 11, kz0 + 10)):
        c.entity(x, 2, z, guard(3))
    for x, z in ((40, 63), (88, 63), (63, 40), (63, 100), (30, 30), (98, 98)):
        c.entity(x, 2, z, golem())
    return c

# ---------------------------------------------------------------------------------------------- worldgen
BIOMES = {
    'illager_fortress': ['dark_forest', 'taiga', 'snowy_taiga', 'old_growth_pine_taiga', 'old_growth_spruce_taiga', 'plains', 'snowy_plains', 'windswept_forest'],
    'illager_city': ['dark_forest', 'taiga', 'old_growth_spruce_taiga', 'snowy_plains', 'plains'],
    'villager_fortress': ['plains', 'sunflower_plains', 'meadow', 'savanna', 'taiga', 'snowy_plains', 'forest'],
    'trader_exchange': ['plains', 'sunflower_plains', 'desert', 'savanna', 'meadow', 'badlands'],
    'villager_kingdom': ['plains', 'sunflower_plains', 'meadow', 'savanna', 'snowy_plains'],
}
SPREAD = {  # (spacing, separation, salt) in chunks
    'illager_fortress': (44, 18, 9170311),
    'illager_city': (72, 30, 9170322),
    'villager_fortress': (46, 18, 9170333),
    'trader_exchange': (40, 16, 9170344),
    'villager_kingdom': (96, 40, 9170355),
}
SPAWNS = {
    'illager_fortress': {'monster': {'bounding_box': 'piece', 'spawns': [
        {'type': 'minecraft:pillager', 'weight': 3, 'minCount': 1, 'maxCount': 2},
        {'type': 'minecraft:vindicator', 'weight': 2, 'minCount': 1, 'maxCount': 1}]}},
    'illager_city': {'monster': {'bounding_box': 'piece', 'spawns': [
        {'type': 'minecraft:pillager', 'weight': 3, 'minCount': 1, 'maxCount': 3},
        {'type': 'minecraft:vindicator', 'weight': 3, 'minCount': 1, 'maxCount': 2},
        {'type': 'minecraft:witch', 'weight': 1, 'minCount': 1, 'maxCount': 1}]}},
    'villager_fortress': {'monster': {'bounding_box': 'piece', 'spawns': []}},
    'trader_exchange': {'monster': {'bounding_box': 'piece', 'spawns': []}},
    'villager_kingdom': {'monster': {'bounding_box': 'piece', 'spawns': []}},
}

WEATHERED = {'processors': [{'processor_type': 'minecraft:rule', 'rules': [
    {'input_predicate': {'predicate_type': 'minecraft:random_block_match', 'block': 'minecraft:stone_bricks', 'probability': 0.18},
     'location_predicate': {'predicate_type': 'minecraft:always_true'}, 'output_state': {'Name': 'minecraft:mossy_stone_bricks'}},
    {'input_predicate': {'predicate_type': 'minecraft:random_block_match', 'block': 'minecraft:stone_bricks', 'probability': 0.1},
     'location_predicate': {'predicate_type': 'minecraft:always_true'}, 'output_state': {'Name': 'minecraft:cracked_stone_bricks'}},
    {'input_predicate': {'predicate_type': 'minecraft:random_block_match', 'block': 'minecraft:polished_blackstone_bricks', 'probability': 0.15},
     'location_predicate': {'predicate_type': 'minecraft:always_true'}, 'output_state': {'Name': 'minecraft:cracked_polished_blackstone_bricks'}},
    {'input_predicate': {'predicate_type': 'minecraft:random_block_match', 'block': 'minecraft:deepslate_bricks', 'probability': 0.15},
     'location_predicate': {'predicate_type': 'minecraft:always_true'}, 'output_state': {'Name': 'minecraft:cracked_deepslate_bricks'}},
    {'input_predicate': {'predicate_type': 'minecraft:random_block_match', 'block': 'minecraft:cobblestone', 'probability': 0.2},
     'location_predicate': {'predicate_type': 'minecraft:always_true'}, 'output_state': {'Name': 'minecraft:mossy_cobblestone'}}]}]}

def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: json.dump(obj, f, ensure_ascii=False, indent=2)

def worldgen(root, name, size):
    d = os.path.join(root, 'data', NS)
    dump(os.path.join(d, 'worldgen/structure', name + '.json'), {
        'type': 'minecraft:jigsaw', 'biomes': f'#{NS}:has_{name}', 'step': 'surface_structures',
        'spawn_overrides': SPAWNS[name], 'terrain_adaptation': 'beard_box',
        'start_pool': f'{NS}:{name}/start_pool', 'size': 1, 'start_height': {'absolute': -1},
        'project_start_to_heightmap': 'WORLD_SURFACE_WG', 'max_distance_from_center': max(80, min(128, size)),
        'use_expansion_hack': False})
    sp, sep, salt = SPREAD[name]
    dump(os.path.join(d, 'worldgen/structure_set', name + '.json'), {
        'structures': [{'structure': f'{NS}:{name}', 'weight': 1}],
        'placement': {'type': 'minecraft:random_spread', 'salt': salt, 'spacing': sp, 'separation': sep}})
    dump(os.path.join(d, 'worldgen/template_pool', name, 'start_pool.json'), {
        'name': f'{NS}:{name}/start_pool', 'fallback': 'minecraft:empty',
        'elements': [{'weight': 1, 'element': {'element_type': 'minecraft:single_pool_element', 'location': f'{NS}:{name}',
                                                'processors': f'{NS}:weathered', 'projection': 'rigid'}}]})
    dump(os.path.join(d, 'tags/worldgen/biome', f'has_{name}.json'), {'replace': False, 'values': ['minecraft:' + b for b in BIOMES[name]]})

def main(out):
    builders = [illager_fortress, illager_city, villager_fortress, trader_exchange, villager_kingdom]
    dump(os.path.join(out, 'data', NS, 'worldgen/processor_list/weathered.json'), WEATHERED)
    # where raid hordes come from (VillageRaids looks the nearest one up)
    dump(os.path.join(out, 'data', NS, 'tags/worldgen/structure/illager_headquarters.json'),
         {'replace': False, 'values': [f'{NS}:illager_city', f'{NS}:illager_fortress']})
    for b in builders:
        c = b()
        n, e = c.save(os.path.join(out, 'data', NS, 'structure', c.name + '.nbt'))
        worldgen(out, c.name, max(c.w, c.d))
        print(f'{c.name}: {c.w}x{c.h}x{c.d}, {n} blocks, {e} entities')

if __name__ == '__main__':
    main(sys.argv[1])

"""houses.py: the Grand Citadel's town buildings, rebuilt smaller, furnished and in ten styles.

build(plot, kind, seed, front) builds one plot of the town (ground at y 64) and returns a House: .blocks (world
(x, y, z) -> block state, 1.20.1 names), .bes (world (x, y, z) -> block entity kind or (kind, loot table)) and .spots
(world (x, feet y, z) of free floor cells inside, for the townsfolk). The house stands back from the street it fronts,
7 to 13 blocks wide and 7 to 11 deep, one to three storeys of four blocks: a stone ground floor or the style's wall with
quoins, timber-framed upper floors (sometimes jettied over the street), a gable roof along or across the street or a
hipped roof of stairs with closed gable ends, glass windows with lintels and shutters or flower boxes, a door with a
step under a canopy or a hood, sometimes a chimney with a fireplace and a smoking campfire, and stairs to every floor.

Inside, every storey is furnished for the building's trade from a list of pieces placed against the walls (the trade's
workstation first, so the townsfolk can take the job) and a centre piece (a dining table with chairs, tavern tables,
a shop counter, reading tables), checked so every free floor cell stays reachable from the door and every piece can be
used; then rugs and lanterns until every floor cell has block light 8 or more. Outside: a path to the street with
lantern posts at a fence or hedge, flower beds, bushes, a tree, a vegetable bed with water, a wood pile, a bench or a
well, and the trade's yard (stalls, a paddock, an outdoor forge, tables for the inn, a herb garden, archery targets).

Coordinates inside a house are local: u to the right along the front, v from the front wall (0) to the back, y up,
mapped to the world by the plot's front direction; facings ('front', 'back', 'left', 'right') are mapped with them.
"""
import random
import loot

GROUND = 64
FLOOR0 = GROUND + 1
DIRS = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}
NAME = {v: k for k, v in DIRS.items()}
OPP = {'front': 'back', 'back': 'front', 'left': 'right', 'right': 'left'}
STEP = {'front': (0, -1), 'back': (0, 1), 'right': (1, 0), 'left': (-1, 0)}     # local (du, dv) of a facing

# wall0: the ground floor, wall1: the floors above (None: as wall0), frame: posts and beams of framed floors (None: no
# frame, quoins of 'quoin' at the corners instead), roofs: (stairs, full block, slab) to pick from
STYLES = {
    'tudor': dict(wall0=['stone_bricks'] * 4 + ['cracked_stone_bricks', 'mossy_stone_bricks'], wall1=['white_terracotta'], frame='dark_oak_log',
                  beam='stripped_dark_oak_log', base='cobblestone', floor='spruce_planks', wood='dark_oak', gable='dark_oak_planks',
                  roofs=['dark_oak', 'deepslate_tile'], beds=['red', 'brown'], rugs=['red', 'brown'], trap='dark_oak'),
    'plaster': dict(wall0=['cobblestone'] * 3 + ['mossy_cobblestone'], wall1=['calcite'], frame='oak_log', beam='stripped_oak_log',
                    base='cobblestone', floor='oak_planks', wood='oak', gable='oak_planks', roofs=['brick', 'spruce'], beds=['orange', 'yellow'],
                    rugs=['orange', 'yellow'], trap='spruce'),
    'brick': dict(wall0=['bricks'], wall1=None, frame=None, quoin='stone_bricks', base='stone_bricks', floor='dark_oak_planks', wood='spruce',
                  gable='bricks', roofs=['deepslate_tile', 'dark_oak'], beds=['blue', 'light_blue'], rugs=['blue', 'cyan'], trap='spruce',
                  lintel='stone_bricks'),
    'nordic': dict(wall0=['cobbled_deepslate'] * 3 + ['polished_deepslate'], wall1=['spruce_planks'], frame='stripped_spruce_log',
                   beam='spruce_log', base='cobbled_deepslate', floor='spruce_planks', wood='spruce', gable='spruce_planks',
                   roofs=['dark_oak', 'cobbled_deepslate'], beds=['gray', 'green'], rugs=['gray', 'green'], trap='spruce'),
    'birch': dict(wall0=['birch_planks'], wall1=None, frame='stripped_dark_oak_log', beam='dark_oak_log', base='polished_andesite',
                  floor='birch_planks', wood='birch', gable='birch_planks', roofs=['dark_prismarine', 'spruce'], beds=['cyan', 'white'],
                  rugs=['light_blue', 'white'], trap='birch'),
    'cottage': dict(wall0=['cobblestone', 'andesite', 'cobblestone', 'stone'], wall1=None, frame=None, quoin='oak_log', base='mossy_cobblestone',
                    floor='oak_planks', wood='oak', gable='oak_planks', roofs=['spruce', 'mossy_cobblestone'], beds=['green', 'lime'],
                    rugs=['green', 'lime'], trap='oak', lintel='stripped_oak_log'),
    'adobe': dict(wall0=['mud_bricks'], wall1=['packed_mud'], frame='stripped_jungle_log', beam='jungle_log', base='packed_mud', floor='jungle_planks',
                  wood='jungle', gable='mud_bricks', roofs=['mud_brick', 'acacia'], beds=['yellow', 'orange'], rugs=['yellow', 'brown'], trap='jungle'),
    'cherry': dict(wall0=['stone_bricks'], wall1=['cherry_planks'], frame='stripped_cherry_log', beam='cherry_log', base='stone_bricks',
                   floor='cherry_planks', wood='cherry', gable='cherry_planks', roofs=['deepslate_tile', 'dark_oak'], beds=['pink', 'magenta'],
                   rugs=['pink', 'white'], trap='cherry'),
    'copper': dict(wall0=['polished_deepslate'], wall1=['white_terracotta'], frame='stripped_mangrove_log', beam='mangrove_log',
                   base='polished_deepslate', floor='mangrove_planks', wood='mangrove', gable='mangrove_planks', roofs=['oxidized_cut_copper', 'deepslate_tile'],
                   beds=['white', 'light_gray'], rugs=['lime', 'green'], trap='mangrove'),
    'manor': dict(wall0=['dark_oak_planks'], wall1=None, frame='stripped_dark_oak_log', beam='dark_oak_log', base='stone_bricks',
                  floor='spruce_planks', wood='dark_oak', gable='dark_oak_planks', roofs=['polished_blackstone_brick', 'deepslate_tile'],
                  beds=['purple', 'black'], rugs=['purple', 'red'], trap='dark_oak'),
}
ROOFS = {'dark_oak': ('dark_oak_stairs', 'dark_oak_planks', 'dark_oak_slab'), 'spruce': ('spruce_stairs', 'spruce_planks', 'spruce_slab'),
         'deepslate_tile': ('deepslate_tile_stairs', 'deepslate_tiles', 'deepslate_tile_slab'), 'brick': ('brick_stairs', 'bricks', 'brick_slab'),
         'mossy_cobblestone': ('mossy_cobblestone_stairs', 'mossy_cobblestone', 'mossy_cobblestone_slab'),
         'cobbled_deepslate': ('cobbled_deepslate_stairs', 'cobbled_deepslate', 'cobbled_deepslate_slab'),
         'dark_prismarine': ('dark_prismarine_stairs', 'dark_prismarine', 'dark_prismarine_slab'),
         'oxidized_cut_copper': ('oxidized_cut_copper_stairs', 'oxidized_cut_copper', 'oxidized_cut_copper_slab'),
         'mud_brick': ('mud_brick_stairs', 'mud_bricks', 'mud_brick_slab'), 'acacia': ('acacia_stairs', 'acacia_planks', 'acacia_slab'),
         'polished_blackstone_brick': ('polished_blackstone_brick_stairs', 'polished_blackstone_bricks', 'polished_blackstone_brick_slab')}

# a building's trade: workstation, chest loot, widths, depths, storeys, the ground floor's room, the upper floors' room, yard
TRADES = {
    'house': (None, 'village_plains_house', (9, 11), (7, 9), (1, 2), 'home', 'bedroom', 'garden'),
    'smith': ('grindstone', 'village_weaponsmith', (9, 11), (7, 9), (1, 2), 'forge', 'bedroom', 'forge'),
    'armorer': ('blast_furnace', 'village_armorer', (9, 11), (7, 9), (1, 2), 'forge', 'bedroom', 'forge'),
    'jeweler': ('smithing_table', 'village_toolsmith', (9, 9), (7, 9), (2, 2), 'jewel', 'bedroom', 'garden'),
    'baker': ('composter', 'village_plains_house', (9, 11), (7, 9), (2, 2), 'bakery', 'bedroom', 'wheat'),
    'butcher': ('smoker', 'village_butcher', (9, 9), (7, 9), (1, 2), 'butchery', 'bedroom', 'pen'),
    'tailor': ('loom', 'village_shepherd', (7, 9), (7, 9), (2, 3), 'tailor', 'bedroom', 'garden'),
    'alchemy': ('brewing_stand', 'village_temple', (9, 11), (7, 9), (2, 3), 'alchemy', 'study', 'herbs'),
    'library': ('lectern', 'village_plains_house', (11, 13), (9, 9), (2, 2), 'library', 'study', 'garden'),
    'scribe': ('lectern', 'village_plains_house', (9, 9), (7, 9), (2, 2), 'scriptorium', 'bedroom', 'garden'),
    'mapmaker': ('cartography_table', 'village_cartographer', (9, 9), (7, 9), (2, 3), 'maps', 'bedroom', 'garden'),
    'stable': ('cauldron', 'village_tannery', (11, 13), (9, 9), (1, 1), 'stable', 'loft', 'paddock'),
    'market': ('stonecutter', 'village_mason', (11, 11), (7, 9), (1, 2), 'shop', 'storage', 'stalls'),
    'guild': ('fletching_table', 'village_fletcher', (11, 13), (9, 9), (2, 2), 'guildhall', 'dorm', 'targets'),
    'inn': ('barrel', 'village_plains_house', (11, 13), (9, 11), (3, 3), 'taproom', 'inn', 'terrace'),
    'tavern': ('barrel', 'village_plains_house', (11, 13), (9, 9), (2, 2), 'taproom', 'bedroom', 'terrace'),
    # the facilities the town's freed plots now hold
    'chapel': ('brewing_stand', 'village_temple', (9, 11), (9, 11), (1, 1), 'chapel', 'bedroom', 'garden'),
    'school': ('lectern', 'village_plains_house', (9, 11), (9, 9), (1, 2), 'classroom', 'study', 'garden'),
    'clinic': ('brewing_stand', 'village_temple', (9, 11), (7, 9), (1, 2), 'clinic', 'bedroom', 'herbs'),
    'warehouse': ('barrel', 'village_plains_house', (9, 11), (9, 9), (1, 1), 'warehouse', 'loft', 'garden'),
    'bathhouse': ('cauldron', 'village_plains_house', (9, 11), (9, 9), (1, 1), 'bath', 'bedroom', 'garden'),
    'guardhouse': ('smithing_table', 'village_weaponsmith', (9, 9), (7, 9), (1, 2), 'guardroom', 'dorm', 'targets'),
    'mill': ('composter', 'village_plains_house', (9, 9), (7, 9), (1, 2), 'mill', 'loft', 'wheat'),
    'florist': ('composter', 'village_plains_house', (7, 9), (7, 9), (1, 2), 'florist', 'bedroom', 'herbs'),
}
# what the town's extra buildings are, in turn: mostly homes, and every facility several times
FACILITIES = ['chapel', 'school', 'clinic', 'warehouse', 'bathhouse', 'guardhouse', 'mill', 'florist', 'baker', 'tailor', 'tavern']
# rooms: pieces against the walls (the first ones always, then filler picked at random), the centre piece, floor
ROOMS = {
    'home': (['furnace', 'crafting_table', 'barrel_pot', 'cauldron', 'chest', 'shelf2'], ['barrel_candle', 'counter_pot', 'shelf_pot', 'plant', 'composter', 'barrel'], 'dining', None),
    'bedroom': (['bed', 'bed', 'chest', 'nightstand', 'desk'], ['wardrobe', 'shelf_pot', 'plant', 'barrel_candle', 'chest'], 'rug', None),
    'study': (['shelf2', 'shelf2', 'lectern', 'desk', 'bed'], ['shelf2', 'shelf_pot', 'plant', 'nightstand', 'chest'], 'reading', None),
    'forge': (['station', 'anvil', 'furnace', 'lava', 'chest'], ['barrel', 'blast_furnace', 'smithing_table', 'grindstone', 'barrel_lantern', 'iron'], 'work', 'stone_bricks'),
    'jewel': (['station', 'counter_candle', 'chest', 'shelf2'], ['counter_pot', 'barrel', 'grindstone', 'plant', 'shelf_pot'], 'counter', None),
    'bakery': (['station', 'furnace', 'furnace', 'counter_cake', 'barrel'], ['hay', 'barrel_pot', 'counter_candle', 'crafting_table', 'chest'], 'dining', None),
    'butchery': (['station', 'counter_candle', 'cauldron', 'barrel'], ['hay', 'barrel', 'chest', 'furnace', 'counter_pot'], 'counter', 'polished_andesite'),
    'tailor': (['station', 'wool', 'wool', 'chest'], ['wool', 'loom', 'barrel_candle', 'plant', 'counter_pot'], 'counter', None),
    'alchemy': (['station', 'cauldron', 'shelf2', 'brewing_stand'], ['shelf_pot', 'barrel_candle', 'plant', 'chest', 'counter_candle'], 'reading', None),
    'library': (['station', 'shelf2', 'shelf2', 'shelf2', 'lectern'], ['shelf2', 'shelf_pot', 'plant', 'chest'], 'reading', None),
    'scriptorium': (['station', 'shelf2', 'desk', 'chest'], ['shelf2', 'shelf_pot', 'barrel_candle', 'plant'], 'reading', None),
    'maps': (['station', 'lectern', 'shelf2', 'chest'], ['shelf_pot', 'barrel_candle', 'plant', 'counter_candle'], 'reading', None),
    'stable': (['station', 'hay', 'hay', 'hay', 'chest', 'bed', 'bed'], ['hay', 'barrel', 'composter', 'cauldron'], 'stalls', 'coarse_dirt'),
    'loft': (['bed', 'bed', 'chest'], ['hay', 'barrel'], 'rug', None),
    'shop': (['station', 'chest', 'barrel_pot', 'barrel_pot'], ['barrel', 'barrel_candle', 'counter_pot', 'plant', 'chest'], 'counter', 'polished_andesite'),
    'storage': (['bed', 'bed', 'chest', 'barrel'], ['barrel', 'chest', 'hay', 'barrel_lantern'], 'rug', None),
    'guildhall': (['station', 'target', 'chest', 'shelf2'], ['barrel', 'target', 'crafting_table', 'barrel_lantern', 'plant'], 'dining', None),
    'dorm': (['bed', 'bed', 'bed', 'chest', 'chest'], ['nightstand', 'barrel', 'plant'], 'rug', None),
    'taproom': (['station', 'keg', 'keg', 'keg', 'cauldron', 'jukebox'], ['keg', 'barrel_lantern', 'plant', 'counter_candle', 'chest'], 'tables', None),
    'inn': (['bed', 'nightstand', 'bed', 'nightstand', 'bed', 'chest'], ['bed', 'nightstand', 'plant', 'chest'], 'rug', None),
    'chapel': (['station', 'shelf2', 'chest', 'plant', 'plant'], ['counter_candle', 'shelf_pot', 'plant', 'counter_candle'], 'pews', 'polished_andesite'),
    'classroom': (['station', 'shelf2', 'shelf2', 'chest'], ['shelf2', 'shelf_pot', 'plant', 'barrel_candle'], 'desks', None),
    'clinic': (['station', 'bed', 'bed', 'cauldron', 'chest'], ['shelf_pot', 'barrel_candle', 'plant', 'nightstand'], 'rug', 'white_concrete'),
    'warehouse': (['station', 'keg', 'keg', 'keg', 'keg', 'chest', 'chest'], ['keg', 'hay', 'barrel', 'chest', 'wool'], 'crates', 'stone_bricks'),
    'bath': (['station', 'cauldron', 'chest', 'plant'], ['plant', 'barrel_candle', 'wool', 'counter_candle'], 'pool', 'smooth_stone'),
    'guardroom': (['station', 'anvil', 'chest', 'chest', 'grindstone'], ['barrel', 'target', 'barrel_lantern', 'chest'], 'work', 'stone_bricks'),
    'mill': (['station', 'grindstone', 'hay', 'hay', 'barrel'], ['hay', 'composter', 'barrel', 'chest'], 'crates', None),
    'florist': (['station', 'counter_pot', 'counter_pot', 'counter_pot', 'barrel'], ['plant', 'counter_pot', 'shelf_pot', 'plant'], 'flowers', None),
}
FLOWERS = ['poppy', 'dandelion', 'cornflower', 'oxeye_daisy', 'allium', 'azure_bluet', 'red_tulip', 'pink_tulip', 'white_tulip',
           'orange_tulip', 'lily_of_the_valley', 'blue_orchid']
TALL_FLOWERS = ['rose_bush', 'peony', 'lilac']
POTS = ['potted_red_tulip', 'potted_fern', 'potted_blue_orchid', 'potted_azure_bluet', 'potted_cornflower', 'potted_dandelion',
        'potted_azalea_bush', 'potted_flowering_azalea_bush', 'potted_oxeye_daisy', 'potted_cactus', 'potted_spruce_sapling',
        'potted_cherry_sapling', 'potted_lily_of_the_valley', 'potted_allium']
WOOLS = ['white_wool', 'red_wool', 'blue_wool', 'yellow_wool', 'green_wool', 'light_blue_wool', 'pink_wool', 'orange_wool', 'purple_wool']
CROPS = [('wheat', 7), ('carrots', 7), ('potatoes', 7), ('beetroots', 3)]
# who lives in a building (tools/citadel/garrison.py stands as many townsfolk in it): each gets a bed
HOUSEHOLD = dict(house=3, inn=4, guardhouse=3)


def household(kind, ident):
    """How many live in building ident: a home two, or three with a child in every third home; an inn four; others two."""
    if kind == 'house':
        return 3 if ident % 3 == 0 else 2
    return HOUSEHOLD.get(kind, 2)
# rooms deep enough get a partition across them: a front room and a back room with a door between
DIVIDED = {'home', 'bakery', 'taproom', 'guildhall', 'bedroom', 'inn', 'dorm', 'shop', 'tailor', 'alchemy', 'jewel', 'scriptorium', 'maps'}
# what a room's barrels hold (loot.THEMES)
GOODS = {'chapel': 'library', 'classroom': 'library', 'clinic': 'alchemy', 'warehouse': 'storage', 'bath': 'home', 'guardroom': 'guild',
         'mill': 'bakery', 'florist': 'market', 'home': 'home', 'bedroom': 'bedroom', 'study': 'library', 'forge': 'forge', 'jewel': 'jewel', 'bakery': 'bakery', 'butchery': 'butchery',
         'tailor': 'tailor', 'alchemy': 'alchemy', 'library': 'library', 'scriptorium': 'library', 'maps': 'maps', 'stable': 'stable',
         'loft': 'stable', 'shop': 'market', 'storage': 'storage', 'guildhall': 'guild', 'dorm': 'bedroom', 'taproom': 'taproom', 'inn': 'bedroom'}
# a family home's trade: one of these workstations on its ground floor, so one of the family has a job
HOME_TRADES = ['composter', 'fletching_table', 'loom', 'cartography_table', 'smithing_table', 'lectern', 'stonecutter']
BE_KINDS = {'chest', 'barrel', 'furnace', 'smoker', 'blast_furnace', 'brewing_stand', 'lectern', 'campfire', 'bed', 'enchanting_table',
            'jukebox', 'decorated_pot'}


def mc(s):
    return s if s.startswith('minecraft:') else 'minecraft:' + s


def props(name, **p):
    return mc(name) + ('[' + ','.join(f'{k}={v}' for k, v in sorted(p.items())) + ']' if p else '')


def bare(state):
    return state.split('[')[0].split(':')[1]


def stairs(name, facing, half='bottom'):
    return props(name, facing=facing, half=half, shape='straight', waterlogged='false')


def slab(name, kind='bottom'):
    return props(name, type=kind, waterlogged='false')


def fence(name):
    return props(name, east='false', north='false', south='false', west='false', waterlogged='false')


def leaves(name):
    return props(name, distance='1', persistent='true', waterlogged='false')


def log(name, axis='y'):
    return props(name, axis=axis) if name.endswith(('_log', '_wood', '_stem')) or name == 'hay_block' else mc(name)


class House:
    def __init__(self, origin, front, rng):
        self.ox, self.oz = origin
        self.front = front
        fx, fz = DIRS[front]
        self.F, self.B, self.R = (fx, fz), (-fx, -fz), (-fz, fx)   # R: right hand of someone in the doorway looking out
        self.blocks, self.bes, self.spots = {}, {}, []
        self.rng = rng

    def face(self, local):
        d = {'front': self.F, 'back': self.B, 'right': self.R, 'left': (-self.R[0], -self.R[1])}[local]
        return NAME[d]

    def world(self, u, y, v):
        return (self.ox + u * self.R[0] + v * self.B[0], y, self.oz + u * self.R[1] + v * self.B[1])

    def local(self, x, z):
        dx, dz = x - self.ox, z - self.oz
        return dx * self.R[0] + dz * self.R[1], dx * self.B[0] + dz * self.B[1]

    def axis(self, along):
        d = self.R if along == 'u' else self.B
        return 'x' if d[0] else 'z'

    def set(self, u, y, v, state, be=None):
        p = self.world(u, y, v)
        self.blocks[p] = mc(state)
        if be is not None:
            self.bes[p] = be
        else:
            self.bes.pop(p, None)

    def get(self, u, y, v):
        return self.blocks.get(self.world(u, y, v))

    def free(self, u, y, v):
        s = self.get(u, y, v)
        return s is None or bare(s) in ('air', 'cave_air')


def pick(x, rng):
    return rng.choice(x) if isinstance(x, list) else x


# ------------------------------------------------------------------------------------------------------------------ build
def build(plot, kind, seed, front, max_w=None, fence_sides='all'):
    """plot: (x0, z0, x1, z1), the inclusive ground rectangle; front: the side of the plot on the street; max_w: the widest
    the house may be (a plot shared with neighbours); fence_sides: 'all', or 'front' for a plot between neighbours."""
    rng = random.Random(seed)
    x0, z0, x1, z1 = plot
    style_name = rng.choice(sorted(STYLES))
    st = STYLES[style_name]
    station, loot_table, ws, ds, fl, room0, room1, yard_kind = TRADES.get(kind, TRADES['house'])
    if station is None and kind == 'house':
        station = random.Random(seed * 31 + 7).choice(HOME_TRADES)
    W = rng.choice(range(ws[0], ws[1] + 1, 2))
    D = rng.choice(range(ds[0], ds[1] + 1, 2))
    floors = rng.randint(fl[0], fl[1])
    if floors > 1 and W < 9:
        W = 9
    if floors > 2 and W < 11:
        floors = 2
    if max_w is not None and W > max_w:
        W = max(7, max_w - (1 - max_w % 2))
        if W < 9 and floors > 1:
            floors = 1
    # the plot along the front direction and across it
    F = DIRS[front]
    R = (-F[1], F[0])
    corners = [(x0, z0), (x1, z0), (x0, z1), (x1, z1)]
    along_f = [x * F[0] + z * F[1] for x, z in corners]
    along_r = [x * R[0] + z * R[1] for x, z in corners]
    street, far = max(along_f), min(along_f)
    depth = street - far + 1
    setback = max(4, min(7, (depth - D) // 2 - 1))
    if depth - setback - D < 4:
        setback = max(3, depth - D - 4)
    if depth - setback - D < 4:
        D = max(7, depth - setback - 4)
        D -= 1 - D % 2
    f = street - setback
    r0 = (min(along_r) + max(along_r)) // 2 - W // 2
    h = House((f * F[0] + r0 * R[0], f * F[1] + r0 * R[1]), front, rng)
    h.style, h.kind, h.W, h.D, h.floors, h.loot, h.station = style_name, kind, W, D, floors, loot_table, station
    h.fence_sides = fence_sides
    h.umin, h.umax = min(along_r) - r0, max(along_r) - r0
    h.vmin, h.vmax = f - street, f - far
    h.yard = set()                     # local (u, v) cells of the yard already used
    framed = st.get('frame') is not None
    h.jetty = framed and floors > 1 and rng.random() < 0.5
    h.v0 = [(-1 if h.jetty and s > 0 else 0) for s in range(floors)]
    h.door_u = W // 2 if rng.random() < 0.6 or W < 9 else rng.choice([2, W - 3])
    roof_name = rng.choice(st['roofs'])
    h.roof = ROOFS[roof_name]
    h.wood = st['wood']
    h.st = st
    shell(h, st, rng)
    h.chimney = chimney_spot(h, rng) if rng.random() < 0.65 else None
    openings(h, st, rng)
    roof(h, st, rng)
    if h.chimney:
        chimney(h, rng)
    flights = staircase(h)
    # beds for the household: the rooms' own, and the rest in the top storey (in the ground floor of a one-storey house)
    rooms = [room0 if s == 0 else room1 for s in range(floors)]
    have = sum(ROOMS[r][0].count('bed') for r in rooms) + (2 if floors == 1 and 'bed' not in ROOMS[room0][0] else 0)
    extra = [0] * floors
    extra[-1] = max(0, HOUSEHOLD.get(kind, 2) - have)
    for s in range(floors):
        furnish(h, s, rooms[s], station if s == 0 else None, flights, rng, extra[s])
    yard(h, yard_kind, rng)
    connect(h)
    return h


# ------------------------------------------------------------------------------------------------------------------ shell
def shell(h, st, rng):
    W, D, floors = h.W, h.D, h.floors
    base = st['base']
    for s in range(floors):
        fy = FLOOR0 + 4 * s
        v0 = h.v0[s]
        wall = st['wall0'] if s == 0 or not st.get('wall1') else st['wall1']
        floor_mat = st['floor']
        for u in range(W):
            for v in range(v0, D):
                edge = u in (0, W - 1) or v in (v0, D - 1)
                if s == 0:
                    h.set(u, GROUND, v, 'dirt')
                    h.set(u, fy, v, base if edge else floor_mat)
                elif not edge:
                    h.set(u, fy, v, floor_mat)
                elif not st.get('frame'):
                    h.set(u, fy, v, pick(wall, rng))
                for y in range(fy + 1, fy + 4):
                    h.set(u, y, v, pick(wall, rng) if edge else 'air')
        if s > 0 and st.get('frame'):
            beams(h, st, fy, v0)
            if v0 < 0:
                # the jetty: corbels under the overhang at every post
                for u in posts(W, True):
                    h.set(u, fy - 1, -1, stairs(st['wood'] + '_stairs', h.face('back'), 'top'))
    plate = FLOOR0 + 4 * floors
    vt = h.v0[-1]
    for u in range(W):
        for v in range(vt, D):
            h.set(u, plate, v, st['floor'])
    if st.get('frame'):
        beams(h, st, plate, vt)
    h.plate = plate
    # posts: corners always, along the walls every four on framed floors; quoins on the others
    for s in range(floors):
        fy = FLOOR0 + 4 * s
        v0 = h.v0[s]
        framed = st.get('frame') and (s > 0 or not st.get('wall1'))
        for y in range(fy + 1, fy + 4):
            if framed:
                for u in posts(W, True):
                    h.set(u, y, v0, log(st['frame']))
                    h.set(u, y, D - 1, log(st['frame']))
                for v in [p + v0 for p in posts(D - v0, True)]:
                    h.set(0, y, v, log(st['frame']))
                    h.set(W - 1, y, v, log(st['frame']))
            elif st.get('quoin'):
                for u, v in ((0, v0), (W - 1, v0), (0, D - 1), (W - 1, D - 1)):
                    h.set(u, y, v, log(st['quoin']))
            elif st.get('frame'):
                # a stone ground floor under framed floors: corner posts of the frame wood
                for u, v in ((0, v0), (W - 1, v0), (0, D - 1), (W - 1, D - 1)):
                    h.set(u, y, v, log(st['frame']))
    h.posts_u = set(posts(W, True))


def posts(n, framed):
    if not framed:
        return [0, n - 1]
    inner = [p for p in range(4, n - 2, 4)] if n > 8 else ([n // 2] if n >= 9 else [])
    return sorted({0, n - 1, *inner})


def beams(h, st, y, v0):
    W, D = h.W, h.D
    for u in range(W):
        h.set(u, y, v0, log(st['beam'], h.axis('u')))
        h.set(u, y, D - 1, log(st['beam'], h.axis('u')))
    for v in range(v0, D):
        h.set(0, y, v, log(st['beam'], h.axis('v')))
        h.set(W - 1, y, v, log(st['beam'], h.axis('v')))


# --------------------------------------------------------------------------------------------------------------- openings
def wall_cells(h, s, side):
    """the wall cells of storey s on one side, in order, with the outward facing"""
    W, D, v0 = h.W, h.D, h.v0[s]
    if side == 'front':
        return [(u, v0) for u in range(1, W - 1)]
    if side == 'back':
        return [(u, D - 1) for u in range(1, W - 1)]
    if side == 'left':
        return [(0, v) for v in range(v0 + 1, D - 1)]
    return [(W - 1, v) for v in range(v0 + 1, D - 1)]


def openings(h, st, rng):
    W, D = h.W, h.D
    wood = st['wood']
    tall = rng.random() < 0.45
    deco = rng.choice(['shutters', 'boxes', 'none', 'shutters', 'boxes'])
    pane = rng.choice(['glass_pane'] * 5 + ['brown_stained_glass_pane', 'light_gray_stained_glass_pane'])
    h.windows = {}
    du = h.door_u
    # the door, its step and the porch
    door = wood + '_door'
    for half, y in (('lower', FLOOR0 + 1), ('upper', FLOOR0 + 2)):
        h.set(du, y, 0, props(door, facing=h.face('back'), half=half, hinge='left', open='false', powered='false'))
    h.set(du, FLOOR0 + 3, 0, log(st['beam'], h.axis('u')) if st.get('beam') else mc(st['base']))
    step = {'cobblestone': 'cobblestone_stairs', 'mossy_cobblestone': 'mossy_cobblestone_stairs', 'stone_bricks': 'stone_brick_stairs',
            'cobbled_deepslate': 'cobbled_deepslate_stairs', 'polished_deepslate': 'polished_deepslate_stairs', 'packed_mud': 'mud_brick_stairs',
            'polished_andesite': 'polished_andesite_stairs'}.get(st['base'], 'stone_brick_stairs')
    h.set(du, FLOOR0, -1, stairs(step, h.face('back')))
    porch = rng.choice(['canopy', 'hood', 'posts'] if h.v0[-1] == 0 or h.floors == 1 else ['hood', 'posts'])
    stair_r, full_r, slab_r = h.roof
    if porch == 'canopy':
        for u in range(du - 1, du + 2):
            for v in (-1, -2):
                h.set(u, FLOOR0 + 3, v, slab(slab_r))
        for u in (du - 1, du + 1):
            for y in range(FLOOR0, FLOOR0 + 3):
                h.set(u, y, -2, fence(wood + '_fence'))
        h.set(du, FLOOR0 + 2, -2, props('lantern', hanging='true', waterlogged='false'))
        h.yard |= {(u, v) for u in range(du - 1, du + 2) for v in (-1, -2)}
    elif porch == 'hood':
        h.set(du - 1, FLOOR0 + 3, -1, stairs(stair_r, h.face('right'), 'top'))
        h.set(du, FLOOR0 + 3, -1, slab(slab_r, 'top'))
        h.set(du + 1, FLOOR0 + 3, -1, stairs(stair_r, h.face('left'), 'top'))
        h.set(du - 1, FLOOR0 + 2, -1, props('lantern', hanging='true', waterlogged='false'))
        h.yard |= {(du - 1, -1), (du, -1), (du + 1, -1)}
    else:
        for u in (du - 1, du + 1):
            h.set(u, FLOOR0, -1, fence(wood + '_fence'))
            h.set(u, FLOOR0 + 1, -1, props('lantern', hanging='false', waterlogged='false'))
        h.yard |= {(du - 1, -1), (du, -1), (du + 1, -1)}
    # windows on every storey and side, between the posts, three apart where they have shutters
    for s in range(h.floors):
        fy = FLOOR0 + 4 * s
        for side in ('front', 'back', 'left', 'right'):
            cells = wall_cells(h, s, side)
            gap = 3 if deco == 'shutters' else 2
            chosen = []
            for i, (u, v) in enumerate(cells):
                if side in ('front', 'back') and u in h.posts_u:
                    continue
                if side in ('left', 'right') and (v - h.v0[s]) in posts(h.D - h.v0[s], True) and st.get('frame'):
                    continue
                if s == 0 and side == 'front' and abs(u - du) <= 1:
                    continue
                if h.chimney and side == h.chimney[0] and abs((v if side in ('left', 'right') else u) - h.chimney[1]) <= 1:
                    continue
                if chosen and abs(i - chosen[-1][0]) < gap:
                    continue
                if i == 0 or i == len(cells) - 1:
                    continue
                chosen.append((i, u, v))
            if side in ('left', 'right') and len(chosen) > 2:
                chosen = chosen[::2] if len(chosen) > 3 else chosen
            out = STEP[side]
            for _, u, v in chosen:
                ys = (fy + 2, fy + 3) if tall else (fy + 2,)
                for y in ys:
                    h.set(u, y, v, pane)
                h.windows.setdefault(s, set()).add((u, v))
                if not tall and st.get('lintel'):
                    h.set(u, fy + 3, v, log(st['lintel'], h.axis('u' if side in ('front', 'back') else 'v')))
                ou, ov = u + out[0], v + out[1]
                if deco == 'shutters' and side != 'back':
                    across = (1, 0) if side in ('front', 'back') else (0, 1)
                    for sgn in (-1, 1):
                        su, sv = ou + across[0] * sgn, ov + across[1] * sgn
                        for y in ys:
                            if h.free(su, y, sv):
                                h.set(su, y, sv, props(st['trap'] + '_trapdoor', facing=h.face(side), half='bottom', open='true',
                                                       powered='false', waterlogged='false'))
                elif deco == 'boxes' and side == 'front' and (s > 0 or h.v0[s] == 0):
                    y = fy + 1
                    if h.free(ou, y, ov) and h.free(ou, y + 1, ov) and not (s == 0 and ov == -1 and abs(ou - du) <= 1):
                        h.set(ou, y, ov, 'moss_block')
                        h.set(ou, y + 1, ov, rng.choice(FLOWERS))
                        h.set(ou, y, ov - 1, props(st['trap'] + '_trapdoor', facing=h.face('front'), half='bottom', open='true',
                                                   powered='false', waterlogged='false'))
                        for sgn, f in ((-1, 'left'), (1, 'right')):
                            if h.free(ou + sgn, y, ov):
                                h.set(ou + sgn, y, ov, props(st['trap'] + '_trapdoor', facing=h.face(f), half='bottom', open='true',
                                                             powered='false', waterlogged='false'))
                        if s == 0:
                            h.yard |= {(ou - 1, ov), (ou, ov), (ou + 1, ov), (ou, ov - 1)}


# ------------------------------------------------------------------------------------------------------------------- roof
def roof(h, st, rng):
    """A roof of stairs over the top storey with an overhang of one, its eaves at the top plate; gable ends walled with
    the gable material and a window, or hipped; a full block along the ridge."""
    W, D = h.W, h.D
    vt = h.v0[-1]
    stair, full, slab_name = h.roof
    plate = h.plate
    kind = rng.choice(['along', 'along', 'across', 'across', 'hip'])
    if kind == 'across' and D - vt < W - 4:
        kind = 'along'
    h.roof_kind = kind
    gable = st['gable']
    u0, u1, v0, v1 = -1, W, vt - 1, D
    if kind in ('along', 'across'):
        along_u = kind == 'along'           # the ridge runs along u (parallel to the street)
        a0, a1 = (v0, v1) if along_u else (u0, u1)
        b0, b1 = (u0, u1) if along_u else (v0, v1)
        lo_face, hi_face = ('back', 'front') if along_u else ('right', 'left')
        k = 0
        while a0 + k <= a1 - k:
            y = plate + k
            lo, hi = a0 + k, a1 - k
            for b in range(b0, b1 + 1):
                for a, state in (((lo, mc(full)),) if lo == hi else ((lo, stairs(stair, h.face(lo_face))), (hi, stairs(stair, h.face(hi_face))))):
                    u, v = (b, a) if along_u else (a, b)
                    h.set(u, y, v, state)
            # the gable ends: walls between the slopes at both ends of the ridge
            if k > 0:
                for a in range(lo + 1, hi):
                    for b in ((0, W - 1) if along_u else (vt, D - 1)):
                        u, v = (b, a) if along_u else (a, b)
                        h.set(u, y, v, gable)
            k += 1
        h.ridge = plate + k - 1
        # a window in each gable where there is room, a lantern under the ridge overhang on the street side
        mid = (a0 + a1) // 2
        if a1 - a0 >= 8:
            for b in ((0, W - 1) if along_u else (vt, D - 1)):
                u, v = (b, mid) if along_u else (mid, b)
                h.set(u, plate + 2, v, 'glass_pane')
                if a1 - a0 >= 11:
                    h.set(u, plate + 1, v, 'glass_pane')
        if not along_u:
            h.set(mid, h.ridge - 1, vt - 1, props('lantern', hanging='true', waterlogged='false'))
    else:
        k = 0
        while True:
            lu, hu, lv, hv = u0 + k, u1 - k, v0 + k, v1 - k
            y = plate + k
            if lu > hu or lv > hv:
                break
            if lu == hu or lv == hv:
                for u in range(lu, hu + 1):
                    for v in range(lv, hv + 1):
                        h.set(u, y, v, full)
                break
            for u in range(lu, hu + 1):
                for v in range(lv, hv + 1):
                    if u not in (lu, hu) and v not in (lv, hv):
                        continue
                    if u in (lu, hu) and v in (lv, hv):
                        state = mc(full)
                    elif v == lv:
                        state = stairs(stair, h.face('back'))
                    elif v == hv:
                        state = stairs(stair, h.face('front'))
                    elif u == lu:
                        state = stairs(stair, h.face('right'))
                    else:
                        state = stairs(stair, h.face('left'))
                    h.set(u, y, v, state)
            k += 1
        h.ridge = plate + k


def chimney_spot(h, rng):
    """(side, position along it) of a chimney against a side wall, away from the corners"""
    side = rng.choice(['left', 'right'])
    v = rng.randint(2, h.D - 3)
    return side, v


def chimney(h, rng):
    side, v = h.chimney
    u = -1 if side == 'left' else h.W
    inner = 0 if side == 'left' else h.W - 1
    top = h.ridge + 2
    mat = rng.choice(['bricks', 'cobblestone', 'stone_bricks'])
    for y in range(GROUND + 1, top + 1):
        h.set(u, y, v, mat)
    h.set(u, top + 1, v, props('campfire', facing=h.face('front'), lit='true', signal_fire='false', waterlogged='false'), be='campfire')
    # the fireplace: a campfire in the wall on the ground floor, the chimney behind it
    h.set(inner, FLOOR0 + 1, v, props('campfire', facing=h.face(OPP[side]), lit='true', signal_fire='false', waterlogged='false'),
          be='campfire')
    h.set(inner, FLOOR0 + 2, v, mat)
    h.set(inner, FLOOR0 + 3, v, mat)
    h.yard |= {(u, v)}
    h.hearth = (inner + (1 if side == 'left' else -1), v)


# -------------------------------------------------------------------------------------------------------------- staircase
def staircase(h):
    """Flights of four steps against the back wall (and the front wall for a third storey), climbing to the right from
    the corner; the step in the floor above sits flush with it, the floor is open over the second and third steps with
    a rail around the opening, the space under the steps is a cupboard. Returns per storey the reserved cells:
    {'block': cells nothing goes on, 'keep': cells kept free (the way on and off)}."""
    wood = h.wood
    res = [dict(block=set(), keep=set()) for _ in range(h.floors)]
    W, D = h.W, h.D
    for s in range(h.floors - 1):
        fy = FLOOR0 + 4 * s
        if s % 2 == 0:
            v, start, d, facing = D - 2, 1, 1, 'right'
        else:
            v, start, d, facing = h.v0[s + 1] + 1, W - 2, -1, 'left'
        cells = [start + d * k for k in range(6)]          # entry, steps 1-4, landing above
        for k in range(1, 5):
            h.set(cells[k], fy + k, v, stairs(wood + '_stairs', h.face(facing)))
        # the opening in the floor above the second and third steps
        h.set(cells[2], fy + 4, v, 'air')
        h.set(cells[3], fy + 4, v, 'air')
        # the cupboard under the steps
        room = h.face('front' if s % 2 == 0 else 'back')
        h.set(cells[2], fy + 1, v, props('barrel', facing='up', open='false'), be=('fill', 'barrel', 'storage'))
        h.set(cells[3], fy + 1, v, props('barrel', facing=room, open='false'), be=('fill', 'barrel', 'storage'))
        h.set(cells[3], fy + 2, v, wood + '_planks')
        h.set(cells[4], fy + 1, v, props('barrel', facing=room, open='false'), be=('fill', 'barrel', 'storage'))
        h.set(cells[4], fy + 2, v, props('barrel', facing=room, open='false'), be=('fill', 'barrel', 'storage'))
        h.set(cells[4], fy + 3, v, wood + '_planks')
        # the rail upstairs: beside the opening on the room side and at its end
        rail_v = v - 1 if s % 2 == 0 else v + 1
        for k in (2, 3):
            h.set(cells[k], fy + 5, rail_v, fence(wood + '_fence'))
        h.set(cells[1], fy + 5, v, fence(wood + '_fence'))
        res[s]['block'] |= {(c, v) for c in cells[1:5]}
        res[s]['keep'] |= {(cells[0], v), (cells[0], v - 1 if s % 2 == 0 else v + 1)}
        res[s + 1]['block'] |= {(cells[1], v), (cells[2], v), (cells[3], v), (cells[2], rail_v), (cells[3], rail_v)}
        res[s + 1]['keep'] |= {(cells[4], v), (cells[5], v), (cells[4], rail_v), (cells[5], rail_v)}
        res[s + 1]['stair_top'] = (cells[4], v)
    return res


# -------------------------------------------------------------------------------------------------------------- furniture
def furnish(h, s, room, station, flights, rng, extra_beds=0):
    W, D = h.W, h.D
    v0 = h.v0[s]
    fy = FLOOR0 + 4 * s
    y = fy + 1
    st = h.st
    wood = h.wood
    walls, fill, centre, floor_mat = ROOMS[room]
    if floor_mat:
        for u in range(1, W - 1):
            for v in range(v0 + 1, D - 1):
                if bare(h.get(u, fy, v) or 'air') == bare(mc(st['floor'])):
                    h.set(u, fy, v, floor_mat)
    inside = {(u, v) for u in range(1, W - 1) for v in range(v0 + 1, D - 1)}
    blocked = set(flights[s]['block'])
    keep = set(flights[s]['keep'])
    if s == 0:
        keep |= {(h.door_u, 1), (h.door_u, 2)}
        if getattr(h, 'hearth', None) and h.chimney:
            keep.add(h.hearth)
    used = set()          # cells with a piece on them
    access = []           # cells of pieces that must be reached from a free neighbour
    walls_in = set()      # cells of a partition

    def free_cells():
        return inside - blocked - used

    def ok():
        fc = free_cells()
        if not keep <= fc:
            return False
        start = next(iter(keep)) if keep else next(iter(fc), None)
        if start is None:
            return False
        seen, todo = {start}, [start]
        while todo:
            c = todo.pop()
            for du, dv in STEP.values():
                n = (c[0] + du, c[1] + dv)
                if n in fc and n not in seen:
                    seen.add(n)
                    todo.append(n)
        if seen != fc:
            return False
        for cells in access:
            if not any((c[0] + du, c[1] + dv) in fc for c in cells for du, dv in STEP.values()):
                return False
        return True

    def walls_of(c):
        out = []
        for side in ('front', 'back', 'left', 'right'):
            du, dv = STEP[side]
            n = (c[0] + du, c[1] + dv)
            if n not in inside or n in walls_in:
                out.append(side)
        return out

    rows = D - 2 - v0
    if room in DIVIDED and rows >= 7 and rng.random() < 0.85:
        pv = v0 + 1 + rows // 2
        line = [(u, pv) for u in range(1, W - 1)]
        doors = [u for u in range(2, W - 2) if not {(u, pv - 1), (u, pv + 1)} & blocked]
        if pv <= D - 4 and not set(line) & (keep | blocked) and doors:
            du = rng.choice(doors)
            for (u, v) in line:
                if u != du:
                    walls_in.add((u, v))
            inside -= walls_in
            keep |= {(du, pv), (du, pv - 1), (du, pv + 1)}
            if ok():
                mat = st['wall1'][0] if s > 0 and st.get('wall1') and 'planks' in st['wall1'][0] else wood + '_planks'
                for (u, v) in walls_in:
                    for yy in (y, y + 1, y + 2):
                        h.set(u, yy, v, mat)
                for half, yy in (('lower', y), ('upper', y + 1)):
                    h.set(du, yy, pv, props(wood + '_door', facing=h.face('back'), half=half, hinge='left', open='false', powered='false'))
                h.set(du, y + 2, pv, mat)
            else:
                inside |= walls_in
                walls_in.clear()
                keep -= {(du, pv), (du, pv - 1), (du, pv + 1)}

    window_cells = h.windows.get(s, set())

    def behind_window(c, wall):
        du, dv = STEP[wall]
        return (c[0] + du, c[1] + dv) in window_cells

    def try_place(piece, cells_pref):
        for c in cells_pref:
            for wall in walls_of(c):
                if place(piece, c, wall):
                    return True
        return False

    def place(piece, c, wall):
        """put a piece at c against wall; undo and return False if the room would lose a way through"""
        if c in used or c in blocked or c in keep:
            return False
        into = OPP[wall]
        face = h.face(into)
        cells = [c]
        extra = []
        if piece in ('bed', 'desk'):
            du, dv = STEP[into]
            c2 = (c[0] + du, c[1] + dv)
            if c2 not in inside or c2 in used or c2 in blocked or c2 in keep:
                return False
            cells.append(c2)
        if piece in ('shelf2', 'wardrobe', 'wool', 'hay', 'keg') and behind_window(c, wall):
            return False
        for cc in cells:
            used.add(cc)
        access.append(cells)
        if not ok():
            for cc in cells:
                used.discard(cc)
            access.pop()
            return False
        u, v = c
        top = None
        if piece == 'station':
            put_station(h, u, y, v, station, face, GOODS.get(room, 'storage'))
        elif piece == 'bed':
            color = st['beds'][len([1 for a in access if len(a) == 2]) % 2]
            head_face = h.face(wall)
            h.set(u, y, v, props(color + '_bed', facing=head_face, occupied='false', part='head'), be='bed')
            h.set(cells[1][0], y, cells[1][1], props(color + '_bed', facing=head_face, occupied='false', part='foot'), be='bed')
        elif piece == 'desk':
            h.set(u, y, v, stairs(wood + '_stairs', h.face(wall), 'top'))
            top = rng.choice(['candle', 'pot', 'lantern', None])
            h.set(cells[1][0], y, cells[1][1], stairs(wood + '_stairs', h.face(into)))
        elif piece == 'chest':
            h.set(u, y, v, props('chest', facing=face, type='single', waterlogged='false'), be=('chest', h.loot))
        elif piece in ('barrel', 'barrel_pot', 'barrel_candle', 'barrel_lantern', 'nightstand'):
            h.set(u, y, v, props('barrel', facing='up', open='false'), be=goods)
            top = {'barrel_pot': 'pot', 'barrel_candle': 'candle', 'barrel_lantern': 'lantern', 'nightstand': 'lantern'}.get(piece)
        elif piece == 'keg':
            h.set(u, y, v, props('barrel', facing=face, open='false'), be=goods)
            h.set(u, y + 1, v, props('barrel', facing=face, open='false'), be=goods)
        elif piece in ('counter_pot', 'counter_candle', 'counter_cake'):
            h.set(u, y, v, stairs(wood + '_stairs', h.face(wall), 'top'))
            top = {'counter_pot': 'pot', 'counter_candle': 'candle', 'counter_cake': 'cake'}[piece]
        elif piece in ('shelf2', 'wardrobe'):
            if piece == 'shelf2':
                h.set(u, y, v, 'bookshelf')
                h.set(u, y + 1, v, 'bookshelf')
            else:
                h.set(u, y, v, props('barrel', facing=face, open='false'), be=('fill', 'barrel', 'bedroom'))
                h.set(u, y + 1, v, wood + '_planks')
        elif piece == 'shelf_pot':
            h.set(u, y, v, 'bookshelf')
            top = 'pot'
        elif piece == 'plant':
            h.set(u, y, v, rng.choice(POTS))
        elif piece == 'furnace':
            h.set(u, y, v, props('furnace', facing=face, lit='false'), be='furnace')
        elif piece == 'blast_furnace':
            h.set(u, y, v, props('blast_furnace', facing=face, lit='false'), be='blast_furnace')
        elif piece == 'crafting_table':
            h.set(u, y, v, 'crafting_table')
        elif piece == 'smithing_table':
            h.set(u, y, v, 'smithing_table')
        elif piece == 'cauldron':
            h.set(u, y, v, props('water_cauldron', level='3'))
        elif piece == 'lava':
            h.set(u, y, v, 'lava_cauldron')
        elif piece == 'composter':
            h.set(u, y, v, props('composter', level=str(rng.randint(0, 7))))
        elif piece == 'anvil':
            h.set(u, y, v, props('anvil', facing=h.face('right' if wall in ('front', 'back') else 'front')))
        elif piece == 'grindstone':
            h.set(u, y, v, props('grindstone', face='floor', facing=face))
        elif piece == 'loom':
            h.set(u, y, v, props('loom', facing=face))
        elif piece == 'lectern':
            h.set(u, y, v, props('lectern', facing=face, has_book='false', powered='false'), be='lectern')
        elif piece == 'brewing_stand':
            h.set(u, y, v, stairs(wood + '_stairs', h.face(wall), 'top'))
            h.set(u, y + 1, v, props('brewing_stand', has_bottle_0='false', has_bottle_1='false', has_bottle_2='false'), be='brewing_stand')
        elif piece == 'hay':
            h.set(u, y, v, log('hay_block'))
            if rng.random() < 0.5 and not behind_window(c, wall):
                h.set(u, y + 1, v, log('hay_block'))
        elif piece == 'wool':
            h.set(u, y, v, rng.choice(WOOLS))
            h.set(u, y + 1, v, rng.choice(WOOLS))
        elif piece == 'target':
            h.set(u, y, v, log('hay_block'))
            h.set(u, y + 1, v, props('target', power='0'))
        elif piece == 'iron':
            h.set(u, y, v, 'iron_block' if rng.random() < 0.3 else 'smooth_stone')
            top = 'lantern'
        elif piece == 'jukebox':
            h.set(u, y, v, props('jukebox', has_record='false'), be='jukebox')
            top = 'pot'
        if top:
            dress(h, u, y + 1, v, top, rng)
        return True

    # pieces against the walls: the room's own, then filler until about three in four wall cells are taken
    ring = sorted((c for c in inside if walls_of(c)), key=lambda c: rng.random())
    pieces = [p for p in walls if p != 'station' or station]
    if station and 'station' not in pieces:
        pieces.insert(0, 'station')
    goods = ('fill', 'barrel', GOODS.get(room, 'storage'))
    if h.floors == 1 and 'bed' not in pieces:
        # a one-storey house: the beds go downstairs, after the trade's own pieces
        pieces[min(len(pieces), 3):min(len(pieces), 3)] = ['bed', 'bed']
    pieces = ['bed'] * extra_beds + pieces
    for p in pieces:
        pref = ring
        if p == 'bed':
            pref = sorted(ring, key=lambda c: 0 if len(walls_of(c)) == 1 and walls_of(c)[0] != 'front' else 1)
        try_place(p, pref)
    # the centre piece
    centre_piece(h, s, centre, inside, used, blocked, keep, access, ok, y, rng)
    target = int(len([c for c in ring]) * 0.75)
    tries = 0
    while len([c for c in used if walls_of(c)]) < target and tries < 40:
        tries += 1
        p = rng.choice(fill)
        try_place(p, sorted(ring, key=lambda c: rng.random()))
    # rugs on the free floor away from the walls
    rug_a, rug_b = st['rugs'][0], st['rugs'][1]
    fc = inside - blocked - used
    for (u, v) in fc:
        if 2 <= u <= W - 3 and v0 + 2 <= v <= D - 3 and h.free(u, y, v):
            border = u in (2, W - 3) or v in (v0 + 2, D - 3)
            if room not in ('forge', 'stable', 'butchery'):
                h.set(u, y, v, (rug_b if border else rug_a) + '_carpet')
    # lanterns until every free cell is lit to 8
    light_room(h, s, inside, blocked, used, rng)
    for (u, v) in sorted(inside - blocked - used):
        feet = bare(h.get(u, y, v) or 'air')
        if (feet == 'air' or feet.endswith('carpet')) and h.free(u, y + 1, v):
            h.spots.append(h.world(u, y, v))


def dress(h, u, y, v, top, rng):
    if top == 'pot':
        h.set(u, y, v, rng.choice(POTS))
    elif top == 'candle':
        h.set(u, y, v, props(rng.choice(['candle', 'white_candle', 'yellow_candle', 'brown_candle']), candles=str(rng.randint(2, 4)),
                             lit='true', waterlogged='false'))
    elif top == 'lantern':
        h.set(u, y, v, props('lantern', hanging='false', waterlogged='false'))
    elif top == 'cake':
        h.set(u, y, v, props('cake', bites='0'))


def put_station(h, u, y, v, station, face, goods='storage'):
    if station in ('smoker', 'blast_furnace', 'furnace'):
        h.set(u, y, v, props(station, facing=face, lit='false'), be=station)
    elif station == 'lectern':
        h.set(u, y, v, props('lectern', facing=face, has_book='false', powered='false'), be='lectern')
    elif station == 'brewing_stand':
        h.set(u, y, v, props('brewing_stand', has_bottle_0='false', has_bottle_1='false', has_bottle_2='false'), be='brewing_stand')
    elif station == 'grindstone':
        h.set(u, y, v, props('grindstone', face='floor', facing=face))
    elif station in ('loom', 'stonecutter'):
        h.set(u, y, v, props(station, facing=face))
    elif station == 'cauldron':
        h.set(u, y, v, props('water_cauldron', level='3'))
    elif station == 'composter':
        h.set(u, y, v, props('composter', level='4'))
    elif station == 'barrel':
        h.set(u, y, v, props('barrel', facing='up', open='false'), be=('fill', 'barrel', goods))
    else:
        h.set(u, y, v, station)


def centre_piece(h, s, centre, inside, used, blocked, keep, access, ok, y, rng):
    W, D, v0 = h.W, h.D, h.v0[s]
    wood = h.wood
    table = fence(wood + '_fence')
    plate = props(wood + '_pressure_plate', powered='false')
    cu, cv = (W - 1) // 2, (v0 + D) // 2

    def claim(cells, extra_access=True):
        cells = [c for c in cells]
        if any(c not in inside or c in used or c in blocked or c in keep for c in cells):
            return False
        used.update(cells)
        access.append(cells)
        if ok():
            return True
        used.difference_update(cells)
        access.pop()
        return False

    def table_with_chairs(tu, tv, length, along='u', top='plate'):
        cells = [(tu + (i if along == 'u' else 0), tv + (i if along == 'v' else 0)) for i in range(length)]
        if not claim(cells):
            return False
        for (u, v) in cells:
            h.set(u, y, v, table)
            if top == 'plate':
                h.set(u, y + 1, v, plate)
            else:
                h.set(u, y + 1, v, props(rng.choice(['candle', 'white_candle']), candles=str(rng.randint(1, 3)), lit='true', waterlogged='false')
                      if rng.random() < 0.5 else h.st['rugs'][0] + '_carpet')
        # chairs on both long sides where there is room
        for (u, v) in cells:
            for side in (('front', 'back') if along == 'u' else ('left', 'right')):
                du, dv = STEP[side]
                c = (u + du, v + dv)
                if rng.random() < 0.8 and claim([c]):
                    h.set(c[0], y, c[1], stairs(wood + '_stairs', h.face(side)))
        return True

    near = sorted(((u, v) for (u, v) in inside if 2 <= u <= W - 3 and v0 + 2 <= v <= D - 3),
                  key=lambda c: abs(c[0] - cu) + abs(c[1] - cv) + rng.random())
    if centre == 'dining':
        length = 2 if W >= 9 else 1
        for (u, v) in near:
            if table_with_chairs(u, v, length):
                break
    elif centre == 'tables':
        n = 0
        for tu in range(2, W - 2, 3):
            for tv in range(v0 + 2, D - 2, 3):
                if table_with_chairs(tu, tv, 1, 'u', top='candle'):
                    n += 1
        if n == 0:
            table_with_chairs(cu, cv, 1)
    elif centre == 'reading':
        for (u, v) in near:
            if table_with_chairs(u, v, 2 if W >= 11 else 1, 'u', top='candle'):
                break
    elif centre == 'counter':
        # a counter across the room with a gap, the shopkeeper's side behind it
        cv2 = v0 + 2 if D - v0 >= 8 else v0 + 2
        cells = [(u, cv2) for u in range(2, W - 2) if abs(u - h.door_u) > 0 and u != W - 3]
        n = 0
        for c in cells:
            if claim([c]):
                h.set(c[0], y, c[1], stairs(wood + '_stairs', h.face('back'), 'top'))
                if rng.random() < 0.5:
                    dress(h, c[0], y + 1, c[1], rng.choice(['pot', 'candle', 'cake' if h.kind == 'baker' else 'pot']), rng)
                n += 1
    elif centre == 'work':
        # a work bench in the middle: a crafting table, an anvil and a chest of tools
        pieces = ['crafting_table', props('anvil', facing=h.face('right')), 'chest']
        for c in ((cu - 1, cv), (cu, cv), (cu + 1, cv)):
            if pieces and claim([c]):
                piece = pieces.pop(0)
                if piece == 'chest':
                    h.set(c[0], y, c[1], props('chest', facing=h.face('front'), type='single', waterlogged='false'), be=('chest', h.loot))
                else:
                    h.set(c[0], y, c[1], piece)
    elif centre == 'pews':
        # rows of pews facing the altar at the back, an aisle down the middle from the door
        for v in range(v0 + 2, D - 3, 2):
            for u in range(1, W - 1):
                if abs(u - h.door_u) <= 0 or u in (1, W - 2):
                    continue
                if claim([(u, v)]):
                    h.set(u, y, v, stairs(wood + '_stairs', h.face('front')))
        au = h.door_u
        if claim([(au - 1, D - 2)]):
            h.set(au - 1, y, D - 2, 'polished_andesite')
            dress(h, au - 1, y + 1, D - 2, 'candle', rng)
        if claim([(au + 1, D - 2)]):
            h.set(au + 1, y, D - 2, 'polished_andesite')
            dress(h, au + 1, y + 1, D - 2, 'candle', rng)
        if claim([(au, D - 2)]):
            h.set(au, y, D - 2, props('bell', attachment='floor', facing=h.face('front'), powered='false'), be='bell')
    elif centre == 'desks':
        # rows of desks with their chairs facing the teacher's wall at the back
        for v in range(v0 + 2, D - 3, 2):
            for u in range(2, W - 2, 2):
                if u == h.door_u:
                    continue
                if claim([(u, v), (u, v - 1)]):
                    h.set(u, y, v, stairs(wood + '_stairs', h.face('front'), 'top'))
                    h.set(u, y, v - 1, stairs(wood + '_stairs', h.face('front')))
    elif centre == 'pool':
        # a sunken pool in the floor, its rim the room's floor
        cells = [(u, v) for u in range(cu - 1, cu + 2) for v in range(cv - 1, cv + 1)]
        if claim(cells):
            for (u, v) in cells:
                h.set(u, y - 1, v, 'water')
                h.set(u, y - 2, v, 'smooth_stone')
    elif centre == 'crates':
        # stacks of barrels and crates down the middle
        for u in range(2, W - 2, 2):
            for v in (cv,):
                if claim([(u, v)]):
                    h.set(u, y, v, props('barrel', facing='up', open='false'), be=('fill', 'barrel', 'storage'))
                    if rng.random() < 0.6:
                        h.set(u, y + 1, v, props('barrel', facing='up', open='false'), be=('fill', 'barrel', 'storage'))
    elif centre == 'flowers':
        # a flower table in the middle: pots on a counter
        for u in (cu - 1, cu, cu + 1):
            if claim([(u, cv)]):
                h.set(u, y, cv, stairs(wood + '_stairs', h.face('back'), 'top'))
                h.set(u, y + 1, cv, rng.choice(POTS))
    elif centre == 'stalls':
        # fence stalls across the stable with a hay bale in each
        for u in range(2, W - 2, 3):
            for v in (D - 3,):
                if claim([(u, v)]):
                    h.set(u, y, v, fence(wood + '_fence'))
    # 'rug': nothing in the middle


def light_room(h, s, inside, blocked, used, rng):
    """hanging lanterns from the ceiling over free cells until every free floor cell has block light 8"""
    fy = FLOOR0 + 4 * s
    y_feet = fy + 1
    for _ in range(14):
        L = light(h, inside, s)
        dark = [c for c in inside - blocked - used if L.get(c, 0) < 8]
        if not dark:
            return
        # the darkest region's centre: pick the dark cell farthest from existing light, hang a lantern over it
        best = None
        for c in dark:
            if (c[0], c[1]) in used or c in blocked:
                continue
            if not h.free(c[0], fy + 3, c[1]):
                continue
            score = sum(1 for d in dark if abs(d[0] - c[0]) + abs(d[1] - c[1]) <= 5)
            if best is None or score > best[0]:
                best = (score, c)
        if best is None:
            return
        u, v = best[1]
        h.set(u, fy + 3, v, props('lantern', hanging='true', waterlogged='false'))


LIGHT = {'lantern': 15, 'campfire': 15, 'lava_cauldron': 15, 'torch': 14, 'wall_torch': 14, 'sea_lantern': 15, 'glowstone': 15}
SEE_THROUGH = ('air', 'glass', 'pane', 'fence', 'stairs', 'slab', 'carpet', 'bed', 'chest', 'lantern', 'candle', 'potted', 'door',
               'trapdoor', 'cauldron', 'lectern', 'brewing', 'grindstone', 'anvil', 'stonecutter', 'campfire', 'pressure_plate', 'flower',
               'composter', 'cake', 'torch', 'ladder', 'chain', 'leaves')


def light(h, inside, s):
    """block light at feet height of storey s, by spreading from the lights of the storey (feet, head and ceiling
    layers) through the cells that let light through"""
    fy = FLOOR0 + 4 * s
    cells = {}
    for u in range(-1, h.W + 1):
        for v in range(-2, h.D + 1):
            for y in range(fy + 1, fy + 4):
                st = h.get(u, y, v)
                name = bare(st) if st else 'air'
                n = LIGHT.get(name, 0)
                if (u, v) not in inside and not n:
                    continue
                if name.endswith('candle'):
                    n = 3 * int(st.split('candles=')[1].split(',')[0].split(']')[0])
                cells[(u, y, v)] = (n, name == 'air' or any(t in name for t in SEE_THROUGH))
    L = {}
    todo = []
    for p, (n, t) in cells.items():
        if n:
            L[p] = n
            todo.append(p)
    while todo:
        nxt = []
        for p in todo:
            lv = L[p] - 1
            if lv <= 0:
                continue
            u, y, v = p
            for q in ((u + 1, y, v), (u - 1, y, v), (u, y + 1, v), (u, y - 1, v), (u, y, v + 1), (u, y, v - 1)):
                if q in cells and cells[q][1] and L.get(q, 0) < lv:
                    L[q] = lv
                    nxt.append(q)
        todo = nxt
    return {(u, v): L.get((u, fy + 1, v), 0) for (u, v) in inside}


# ------------------------------------------------------------------------------------------------------------------- yard
def yard(h, kind, rng):
    st = h.st
    wood = h.wood
    W, D = h.W, h.D
    umin, umax, vmin, vmax = h.umin, h.umax, h.vmin, h.vmax
    house = {(u, v) for u in range(-1, W + 1) for v in range(min(h.v0) - 1, D + 1)}
    h.yard |= house
    # grass over the whole plot first (the house was built on dirt)
    for u in range(umin, umax + 1):
        for v in range(vmin, vmax + 1):
            if (u, v) not in house or not (0 <= u < W and 0 <= v < D):
                p = h.world(u, GROUND, v)
                if p not in h.blocks:
                    h.blocks[p] = mc('grass_block')
    du = h.door_u
    # the path to the street, the boundary and its gate posts
    path_mat = rng.choice(['dirt_path', 'dirt_path', 'gravel', 'cobblestone', 'stone_bricks', 'packed_mud'])
    wide = rng.random() < 0.35
    for v in range(vmin, -1):
        for u in ((du - 1, du, du + 1) if wide else (du,)):
            mat = path_mat if path_mat != 'cobblestone' or rng.random() < 0.8 else 'mossy_cobblestone'
            h.set(u, GROUND, v, mat)
            h.yard.add((u, v))
    boundary = rng.choice(['fence', 'hedge', 'wall', 'none', 'hedge'])
    edge_mat = {'fence': fence(wood + '_fence'), 'hedge': leaves(rng.choice(['oak_leaves', 'azalea_leaves', 'spruce_leaves', 'birch_leaves'])),
                'wall': props('cobblestone_wall', east='none', north='none', south='none', west='none', up='true', waterlogged='false')}.get(boundary)
    gap = {du - 1, du, du + 1} if wide else {du}
    if edge_mat:
        for u in range(umin, umax + 1):
            if u in gap:
                continue
            h.set(u, GROUND + 1, vmin, edge_mat)
            h.yard.add((u, vmin))
        if h.fence_sides == 'all':
            for v in range(vmin, vmax + 1):
                for u in (umin, umax):
                    h.set(u, GROUND + 1, v, edge_mat)
                    h.yard.add((u, v))
            for u in range(umin, umax + 1):
                h.set(u, GROUND + 1, vmax, edge_mat)
                h.yard.add((u, vmax))
        # gate posts with lanterns at the path
        for u in (min(gap) - 1, max(gap) + 1):
            h.set(u, GROUND + 1, vmin, log(st['frame'] if st.get('frame') and 'log' in st['frame'] else 'stripped_oak_log'))
            h.set(u, GROUND + 2, vmin, props('lantern', hanging='false', waterlogged='false'))
    else:
        for u in (min(gap) - 1, max(gap) + 1):
            h.set(u, GROUND + 1, vmin, fence(wood + '_fence'))
            h.set(u, GROUND + 2, vmin, props('lantern', hanging='false', waterlogged='false'))
            h.yard.add((u, vmin))
    # flower beds along the front wall and bushes at the corners
    for u in range(-1, W + 1):
        if abs(u - du) <= 1 or not h.free(u, GROUND + 1, -1) or not h.free(u, GROUND + 2, -1):
            continue
        r = rng.random()
        if r < 0.55:
            h.set(u, GROUND + 1, -1, rng.choice(FLOWERS))
        elif r < 0.7:
            put_tall(h, u, -1, rng.choice(TALL_FLOWERS))
        elif r < 0.85:
            h.set(u, GROUND + 1, -1, rng.choice(['azalea', 'flowering_azalea']))
    for u in (-2, W + 1):
        if umin < u < umax and rng.random() < 0.8:
            h.set(u, GROUND + 1, -1, leaves(rng.choice(['oak_leaves', 'azalea_leaves', 'flowering_azalea_leaves'])))
    # the trade's yard, then the home's: a path round to the back, a shed, trees, a vegetable bed, a wood pile, a bench
    # or a well, bushes and lamp posts
    trade_yard(h, kind, rng)
    side_path(h, path_mat, rng)
    if rng.random() < 0.65:
        spot = find(h, 5, 4, rng, prefer=rng.choice(['back', 'side']))
        if spot:
            shed(h, spot, rng)
    for _ in range(1 + (rng.random() < 0.6) + (rng.random() < 0.25)):
        tree_spot = find(h, 5, 5, rng, prefer=rng.choice(['back', 'back', 'side', 'front']))
        if tree_spot:
            tree(h, tree_spot[0] + 2, tree_spot[1] + 2, rng)
    if kind not in ('wheat', 'herbs') and rng.random() < 0.7:
        spot = find(h, 5, 4, rng, prefer='back')
        if spot:
            garden(h, spot, 5, 4, rng)
    if rng.random() < 0.6:
        woodpile(h, rng)
    r = rng.random()
    if r < 0.35:
        spot = find(h, 3, 3, rng, prefer='side')
        if spot:
            well(h, spot, rng)
    elif r < 0.75:
        spot = find(h, 3, 2, rng, prefer='front')
        if spot:
            bench(h, spot, rng)
    for _ in range(rng.randint(2, 4)):
        spot = find(h, 2, 2, rng, prefer=rng.choice(['back', 'side', 'front']))
        if spot:
            leaf = rng.choice(['oak_leaves', 'azalea_leaves', 'flowering_azalea_leaves', 'birch_leaves'])
            for i in range(2):
                for j in range(2):
                    if rng.random() < 0.8:
                        h.set(spot[0] + i, GROUND + 1, spot[1] + j, leaves(leaf))
                        if rng.random() < 0.25:
                            h.set(spot[0] + i, GROUND + 2, spot[1] + j, leaves(leaf))
    # lamp posts in the yard, so the night stays light around the house
    for prefer in ('back', 'side'):
        spot = find(h, 1, 1, rng, prefer=prefer)
        if spot:
            for y in (GROUND + 1, GROUND + 2):
                h.set(spot[0], y, spot[1], fence(h.wood + '_fence'))
            h.set(spot[0], GROUND + 3, spot[1], props('lantern', hanging='false', waterlogged='false'))
    # flowers and grass on the rest
    for _ in range(32):
        u, v = rng.randint(umin + 1, umax - 1), rng.randint(vmin + 1, vmax - 1)
        if (u, v) in h.yard or not h.free(u, GROUND + 1, v):
            continue
        if bare(h.get(u, GROUND, v) or 'grass_block') != 'grass_block':
            continue
        h.set(u, GROUND + 1, v, rng.choice(FLOWERS + ['grass', 'grass', 'grass', 'fern']))
        h.yard.add((u, v))


def side_path(h, mat, rng):
    """stepping stones from the front path round one side of the house to the back yard"""
    side = rng.choice(['left', 'right'])
    u = -2 if side == 'left' else h.W + 1
    if not (h.umin + 1 < u < h.umax - 1):
        return
    stone = mat if mat != 'dirt_path' else rng.choice(['dirt_path', 'gravel'])
    cells = [(c, -2) for c in (range(u, h.door_u) if side == 'left' else range(h.door_u + 1, u + 1))] + [(u, v) for v in range(-1, h.D + 2)]
    for (cu, cv) in cells:
        if h.vmin < cv < h.vmax and h.free(cu, GROUND + 1, cv) and bare(h.get(cu, GROUND, cv) or 'grass_block') == 'grass_block':
            if rng.random() < 0.85:
                h.set(cu, GROUND, cv, stone)
            h.yard.add((cu, cv))


def shed(h, spot, rng):
    """a 5 x 4 shed of planks on log corners under a slab roof, its door toward the street: a barrel, a crafting
    table, a chest and a composter or hay inside, a lantern"""
    u0, v0 = spot
    wood = rng.choice([h.wood, 'spruce', 'oak'])
    for i in range(5):
        for j in range(4):
            u, v = u0 + i, v0 + j
            h.set(u, GROUND, v, 'cobblestone' if rng.random() < 0.8 else 'mossy_cobblestone')
            edge = i in (0, 4) or j in (0, 3)
            for y in (GROUND + 1, GROUND + 2, GROUND + 3):
                h.set(u, y, v, (log(wood + '_log') if i in (0, 4) and j in (0, 3) else wood + '_planks') if edge else 'air')
            h.set(u, GROUND + 4, v, slab(wood + '_slab'))
    for half, y in (('lower', GROUND + 1), ('upper', GROUND + 2)):
        h.set(u0 + 2, y, v0, props(wood + '_door', facing=h.face('back'), half=half, hinge='left', open='false', powered='false'))
    h.set(u0, GROUND + 2, v0 + 2, 'glass_pane')
    h.set(u0 + 4, GROUND + 2, v0 + 2, 'glass_pane')
    inner = [(u0 + 1, v0 + 1), (u0 + 3, v0 + 1), (u0 + 1, v0 + 2), (u0 + 3, v0 + 2), (u0 + 2, v0 + 2)]
    pieces = [props('barrel', facing='up', open='false'), 'crafting_table', props('chest', facing=h.face('front'), type='single', waterlogged='false'),
              rng.choice([props('composter', level='2'), log('hay_block'), props('barrel', facing='up', open='false')])]
    rng.shuffle(pieces)
    for (u, v), piece in zip(inner, pieces):
        be = ('chest', h.loot) if piece.startswith('minecraft:chest') else ('fill', 'barrel', 'shed') if 'barrel' in piece else None
        h.set(u, GROUND + 1, v, piece, be=be)
    h.set(u0 + 2, GROUND + 3, v0 + 1, props('lantern', hanging='true', waterlogged='false'))
    h.set(u0 + 2, GROUND, v0 - 1, 'cobblestone')


def put_tall(h, u, v, name):
    h.set(u, GROUND + 1, v, props(name, half='lower'))
    h.set(u, GROUND + 2, v, props(name, half='upper'))


def find(h, w, d, rng, prefer='back'):
    """a free w x d rectangle of yard (local lower corner), one block from everything else"""
    umin, umax, vmin, vmax = h.umin + 1, h.umax - 1, h.vmin + 1, h.vmax - 1
    cands = []
    for u in range(umin, umax - w + 2):
        for v in range(vmin, vmax - d + 2):
            cells = [(u + i, v + j) for i in range(-1, w + 1) for j in range(-1, d + 1)]
            if any(c in h.yard for c in cells):
                continue
            if any(bare(h.get(u + i, GROUND, v + j) or 'grass_block') != 'grass_block' for i in range(w) for j in range(d)):
                continue
            if prefer == 'back':
                key = -v
            elif prefer == 'front':
                key = v
            else:
                key = abs(v + d // 2 - h.D // 2) + min(abs(u + w), abs(u - h.W))
            cands.append((key + rng.random() * 3, (u, v)))
    if not cands:
        return None
    cands.sort()
    u, v = cands[0][1]
    h.yard |= {(u + i, v + j) for i in range(w) for j in range(d)}
    return u, v


def tree(h, u, v, rng):
    kind = rng.choice(['oak', 'birch', 'spruce', 'cherry', 'azalea'])
    y = GROUND + 1
    if kind == 'spruce':
        t = rng.randint(6, 7)
        for k in range(t):
            h.set(u, y + k, v, log('spruce_log'))
        for k, r in ((2, 2), (3, 1), (4, 2), (5, 1), (6, 1), (7, 0)):
            for du in range(-r, r + 1):
                for dv in range(-r, r + 1):
                    if abs(du) + abs(dv) <= r + (1 if r == 2 else 0) and (du, dv) != (0, 0) or k >= t:
                        if h.free(u + du, y + k, v + dv):
                            h.set(u + du, y + k, v + dv, leaves('spruce_leaves'))
        return
    trunk = {'oak': 'oak_log', 'birch': 'birch_log', 'cherry': 'cherry_log', 'azalea': 'oak_log'}[kind]
    leaf = {'oak': 'oak_leaves', 'birch': 'birch_leaves', 'cherry': 'cherry_leaves', 'azalea': 'flowering_azalea_leaves'}[kind]
    t = {'oak': 4, 'birch': 5, 'cherry': 4, 'azalea': 3}[kind] + rng.randint(0, 1)
    for k in range(t):
        h.set(u, y + k, v, log(trunk))
    if kind == 'azalea':
        h.set(u, GROUND, v, 'rooted_dirt')
    for k in range(t - 2, t + 2):
        r = 2 if k < t else 1
        for du in range(-r, r + 1):
            for dv in range(-r, r + 1):
                if abs(du) == r and abs(dv) == r and (k == t + 1 or rng.random() < 0.6):
                    continue
                if h.free(u + du, y + k, v + dv):
                    h.set(u + du, y + k, v + dv, leaves(leaf if kind != 'azalea' or rng.random() < 0.5 else 'azalea_leaves'))


def garden(h, spot, w, d, rng):
    u0, v0 = spot
    crops = rng.sample(CROPS, 2)
    mid = u0 + w // 2
    for i in range(w):
        for j in range(d):
            u, v = u0 + i, v0 + j
            if u == mid:
                h.set(u, GROUND, v, 'water')
                continue
            crop, age = crops[0] if u < mid else crops[1]
            h.set(u, GROUND, v, props('farmland', moisture='7'))
            h.set(u, GROUND + 1, v, props(crop, age=str(age if rng.random() < 0.7 else rng.randint(0, age))))
    h.set(u0 - 1 if u0 - 1 > h.umin else u0 + w, GROUND + 1, v0, props('composter', level='3'))


def woodpile(h, rng):
    side = rng.choice(['left', 'right'])
    u = -2 if side == 'left' else h.W + 1
    if not (h.umin < u < h.umax):
        return
    logs = rng.choice(['oak_log', 'spruce_log', 'birch_log'])
    for v in range(h.D - 4, h.D - 1):
        if (u, v) in h.yard and h.get(u, GROUND + 1, v):
            return
    for v in range(h.D - 4, h.D - 1):
        for k in range(2 if v != h.D - 2 else 1):
            h.set(u, GROUND + 1 + k, v, log(logs, h.axis('u')))
        h.yard.add((u, v))


def well(h, spot, rng):
    u0, v0 = spot
    for i in range(3):
        for j in range(3):
            if (i, j) == (1, 1):
                h.set(u0 + i, GROUND, v0 + j, 'water')
                h.set(u0 + i, GROUND - 1, v0 + j, 'water')
            else:
                h.set(u0 + i, GROUND + 1, v0 + j, rng.choice(['cobblestone', 'cobblestone', 'mossy_cobblestone']))
    for i, j in ((0, 0), (2, 0), (0, 2), (2, 2)):
        for y in (GROUND + 2, GROUND + 3):
            h.set(u0 + i, y, v0 + j, fence(h.wood + '_fence'))
    for i in range(3):
        for j in range(3):
            h.set(u0 + i, GROUND + 4, v0 + j, slab(h.roof[2]))
    h.set(u0 + 1, GROUND + 3, v0 + 1, props('lantern', hanging='true', waterlogged='false'))


def bench(h, spot, rng):
    u0, v0 = spot
    for i in range(2):
        h.set(u0 + i, GROUND + 1, v0, stairs(h.wood + '_stairs', h.face('front')))
    h.set(u0 + 2, GROUND + 1, v0, rng.choice(POTS))


def trade_yard(h, kind, rng):
    wood = h.wood
    if kind == 'stalls':
        # two market stalls in the front yard: barrels under a striped awning on posts
        for side in (-1, 1):
            u0 = h.door_u + side * 4 - (2 if side < 0 else 0)
            v = h.vmin + 2
            if not (h.umin < u0 and u0 + 2 < h.umax) or v > -3:
                continue
            colours = rng.choice([('red_wool', 'white_wool'), ('blue_wool', 'white_wool'), ('yellow_wool', 'green_wool')])
            for i in range(3):
                h.set(u0 + i, GROUND + 1, v, props('barrel', facing='up', open='false'), be=('fill', 'barrel', 'market'))
                dress(h, u0 + i, GROUND + 2, v, rng.choice(['pot', 'candle', 'pot']), rng)
                for j in (-1, 0, 1):
                    h.set(u0 + i, GROUND + 4, v + j, colours[(i + j) % 2])
                h.yard |= {(u0 + i, v + j) for j in (-1, 0, 1)}
            for i in (0, 2):
                for y in (GROUND + 2, GROUND + 3):
                    h.set(u0 + i, y, v - 1, fence(wood + '_fence'))
    elif kind == 'paddock':
        spot = find(h, 9, 6, rng, prefer='back')
        if spot:
            u0, v0 = spot
            for i in range(9):
                for j in range(6):
                    if i in (0, 8) or j in (0, 5):
                        h.set(u0 + i, GROUND + 1, v0 + j, fence(wood + '_fence'))
                    elif rng.random() < 0.3:
                        h.set(u0 + i, GROUND, v0 + j, 'coarse_dirt')
            h.set(u0 + 4, GROUND + 1, v0, props(wood + '_fence_gate', facing=h.face('front'), in_wall='false', open='false', powered='false'))
            h.set(u0 + 2, GROUND + 1, v0 + 2, log('hay_block'))
            h.set(u0 + 3, GROUND + 1, v0 + 2, log('hay_block'))
            h.set(u0 + 6, GROUND + 1, v0 + 3, props('water_cauldron', level='3'))
    elif kind == 'forge':
        # an outdoor forge under a lean-to on the house's side
        side = rng.choice(['left', 'right'])
        u = -3 if side == 'left' else h.W + 1
        if h.umin < u and u + 1 < h.umax:
            for j in range(3):
                v = 1 + j
                h.set(u, GROUND + 1, v, ['smooth_stone', 'lava_cauldron', props('anvil', facing=h.face('front'))][j])
                h.set(u + 1, GROUND, v, 'cobblestone')
                h.set(u, GROUND, v, 'cobblestone')
                h.set(u, GROUND + 4, v, slab(h.roof[2]))
                h.set(u + 1, GROUND + 4, v, slab(h.roof[2]))
                h.yard |= {(u, v), (u + 1, v)}
            for v in (0, 4):
                for y in (GROUND + 1, GROUND + 2, GROUND + 3):
                    h.set(u, y, v, fence(wood + '_fence'))
                h.set(u, GROUND + 4, v, slab(h.roof[2]))
                h.set(u + 1, GROUND + 4, v, slab(h.roof[2]))
                h.yard |= {(u, v), (u + 1, v)}
    elif kind == 'wheat':
        spot = find(h, 7, 5, rng, prefer='back')
        if spot:
            u0, v0 = spot
            for i in range(7):
                for j in range(5):
                    if i == 3:
                        h.set(u0 + i, GROUND, v0 + j, 'water')
                    else:
                        h.set(u0 + i, GROUND, v0 + j, props('farmland', moisture='7'))
                        h.set(u0 + i, GROUND + 1, v0 + j, props('wheat', age='7'))
            h.set(u0 - 1, GROUND + 1, v0, log('hay_block'))
    elif kind == 'herbs':
        spot = find(h, 5, 3, rng, prefer='back')
        if spot:
            u0, v0 = spot
            for i in range(5):
                for j in range(3):
                    h.set(u0 + i, GROUND + 1, v0 + j, rng.choice(FLOWERS + ['fern']))
                    h.set(u0 + i, GROUND, v0 + j, 'podzol' if rng.random() < 0.5 else 'grass_block')
    elif kind == 'pen':
        spot = find(h, 6, 5, rng, prefer='back')
        if spot:
            u0, v0 = spot
            for i in range(6):
                for j in range(5):
                    if i in (0, 5) or j in (0, 4):
                        h.set(u0 + i, GROUND + 1, v0 + j, fence(wood + '_fence'))
                    else:
                        h.set(u0 + i, GROUND, v0 + j, 'coarse_dirt' if rng.random() < 0.5 else 'grass_block')
            h.set(u0 + 2, GROUND + 1, v0, props(wood + '_fence_gate', facing=h.face('front'), in_wall='false', open='false', powered='false'))
            h.set(u0 + 1, GROUND + 1, v0 + 1, log('hay_block'))
    elif kind == 'targets':
        spot = find(h, 7, 2, rng, prefer='back')
        if spot:
            u0, v0 = spot
            for i in (0, 3, 6):
                h.set(u0 + i, GROUND + 1, v0 + 1, log('hay_block'))
                h.set(u0 + i, GROUND + 2, v0 + 1, props('target', power='0'))
    elif kind == 'terrace':
        # tables and chairs in front of the inn
        for i, u in enumerate((h.door_u - 4, h.door_u + 4)):
            v = -3
            if not (h.umin + 1 < u - 1 and u + 1 < h.umax - 1) or v <= h.vmin + 1:
                continue
            h.set(u, GROUND + 1, v, fence(wood + '_fence'))
            h.set(u, GROUND + 2, v, props(wood + '_pressure_plate', powered='false'))
            h.set(u - 1, GROUND + 1, v, stairs(wood + '_stairs', h.face('left')))
            h.set(u + 1, GROUND + 1, v, stairs(wood + '_stairs', h.face('right')))
            h.yard |= {(u - 1, v), (u, v), (u + 1, v)}
    else:
        pass


# ---------------------------------------------------------------------------------------------------------------- connect
PANE = ('glass_pane', 'iron_bars')


def connect(h):
    """Panes, fences and walls joined to their neighbours, as the game would do on the next block update."""
    for p, s in list(h.blocks.items()):
        name = bare(s)
        is_pane = name in PANE or name.endswith('stained_glass_pane')
        is_fence = name.endswith('_fence')
        is_wall = name.endswith('_wall')
        if not (is_pane or is_fence or is_wall):
            continue
        conn = {}
        for d, (dx, dz) in DIRS.items():
            n = h.blocks.get((p[0] + dx, p[1], p[2] + dz))
            ok = False
            if n:
                nn = bare(n)
                if is_pane:
                    ok = nn in PANE or nn.endswith('pane') or solid(nn)
                elif is_fence:
                    ok = nn.endswith('_fence') or nn.endswith('fence_gate') or solid(nn)
                else:
                    ok = nn.endswith('_wall') or nn.endswith('fence_gate') or solid(nn)
            conn[d] = ('low' if ok else 'none') if is_wall else ('true' if ok else 'false')
        if is_wall:
            h.blocks[p] = props(name, up='true', waterlogged='false', **conn)
        else:
            h.blocks[p] = props(name, waterlogged='false', **conn)


def solid(n):
    soft = ('air', 'pane', 'door', 'stairs', 'slab', 'fence', 'lantern', 'torch', 'carpet', 'flower', 'tulip', 'poppy', 'dandelion',
            'cornflower', 'daisy', 'allium', 'bluet', 'lily', 'orchid', 'grass', 'fern', 'potted', 'bed', 'chest', 'campfire', 'leaves', 'sapling',
            'water', 'cauldron', 'lectern', 'brewing', 'grindstone', 'anvil', 'stonecutter', 'path', 'bars', 'wall', 'candle', 'cake',
            'pressure_plate', 'trapdoor', 'bush', 'azalea', 'rose', 'peony', 'lilac', 'wheat', 'carrots', 'potatoes', 'beetroots', 'farmland',
            'composter', 'gate', 'chain', 'ladder')
    return not any(t in n for t in soft)


def entities(h, loot_seed=0):
    """Block entity compounds (1.20.1 format, Python values; ('long', v) for a long) for the blocks that need one: chests with
    their trade's village loot table, barrels stocked with the goods of their room (loot.THEMES)."""
    out = {}
    for p, be in h.bes.items():
        if p not in h.blocks:
            continue
        if isinstance(be, tuple) and be[0] == 'fill':
            out[p] = {'id': 'minecraft:' + be[1], 'x': p[0], 'y': p[1], 'z': p[2],
                      'Items': loot.items(be[2], (p[0] * 73856093) ^ (p[1] * 19349663) ^ (p[2] * 83492791) ^ loot_seed)}
        elif isinstance(be, tuple):
            kind, table = be
            out[p] = {'id': 'minecraft:' + kind, 'x': p[0], 'y': p[1], 'z': p[2], 'LootTable': 'minecraft:chests/village/' + table,
                      'LootTableSeed': ('long', (p[0] * 3129871 ^ p[2] * 116129781 ^ p[1] ^ loot_seed) & 0x7FFFFFFFFFFF)}
        else:
            out[p] = {'id': 'minecraft:' + be, 'x': p[0], 'y': p[1], 'z': p[2]}
    return out

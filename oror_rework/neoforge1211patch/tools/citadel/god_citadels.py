"""god_citadels.py <structure dir> [name ...]: the 41 gods' citadels built anew (r63; the user: "神々の城塞も点検し直し 多分ひどいから").

Until r62 every god's citadel was one template, a 41x25x41 box of one stone with no roof and lights hanging in the air, the
god's stone and seal swapped in. Each is now a walled castle in the god's own style, on a 49x49 plinth:

  * a curtain wall (plinth course, string course, corbels, crenellations, arrow slits) with a walk on top reached by
    stairs from the court, four corner towers (floors, ladders, a roof of the style) and a gatehouse with two towers;
  * a court with a paved way from the gate to the keep, lamp posts and four braziers;
  * the keep: buttresses between tall windows, a hall fifteen blocks high with two rows of columns and chandeliers, the
    god's seal on a dais at its centre; above the hall a second storey and the crown of the style: a dome, a spire, a
    pagoda's tiered eaves, a stepped temple or a great tree.

What the old template held is kept: the seal block, every chest with its loot table (the best behind the seal, the
others in the towers and the keep's corners, the first by the gate) and every spawner with its minion (in the towers and
the keep's corners). Indoor cells are stored as air so the ground never stands inside; the court is cleared up to the
wall's height. Lights are on posts, walls and chains; tools/structure_lights.py's rule then lights any dark corner.
"""
import gzip, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anvil
from anvil import Typed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import structure_lights

W, H = 49, 46
C = 24


def S(name, **p):
    if not p:
        return 'minecraft:' + name if ':' not in name else name
    n = 'minecraft:' + name if ':' not in name else name
    return n + '[' + ','.join('%s=%s' % (k, v) for k, v in sorted(p.items())) + ']'


def stairs(block, facing, half='bottom'):
    return S(block, facing=facing, half=half, shape='straight', waterlogged='false')


STYLES = {
    # main wall stone, its stairs, its slab; trim (courses, plinth); accent (gilding); pillar; floor, floor2; roof block, roof
    # stairs; merlon wall; window pane; hanging light; glow block; banner colour; carpet; crown kind; tower roof kind
    'holy': dict(main='quartz_bricks', st='quartz_stairs', slab='quartz_slab', trim='chiseled_quartz_block', course='smooth_quartz',
                 accent='gold_block', pillar='quartz_pillar', floor='polished_diorite', floor2='calcite', roof='gold_block',
                 rst='smooth_quartz_stairs', rwall='diorite_wall', pane='yellow_stained_glass_pane', lamp='lantern', glow='sea_lantern',
                 colour='white', carpet='yellow', crown='dome', troof='cone', found='smooth_quartz'),
    'celestial': dict(main='calcite', st='diorite_stairs', slab='diorite_slab', trim='prismarine_bricks', course='polished_diorite',
                      accent='gold_block', pillar='quartz_pillar', floor='polished_diorite', floor2='light_blue_terracotta',
                      roof='light_blue_terracotta', rst='prismarine_brick_stairs', rwall='diorite_wall', pane='light_blue_stained_glass_pane',
                      lamp='lantern', glow='sea_lantern', colour='light_blue', carpet='light_blue', crown='spire', troof='cone', found='polished_diorite'),
    'infernal': dict(main='nether_bricks', st='nether_brick_stairs', slab='nether_brick_slab', trim='red_nether_bricks', course='chiseled_nether_bricks',
                     accent='gilded_blackstone', pillar='basalt', floor='polished_blackstone', floor2='red_nether_bricks', roof='red_nether_bricks',
                     rst='red_nether_brick_stairs', rwall='nether_brick_wall', pane='red_stained_glass_pane', lamp='lantern', glow='shroomlight',
                     colour='red', carpet='red', crown='spire', troof='cone', found='blackstone'),
    'abyss': dict(main='polished_blackstone_bricks', st='polished_blackstone_brick_stairs', slab='polished_blackstone_brick_slab',
                  trim='polished_blackstone', course='chiseled_polished_blackstone', accent='gilded_blackstone', pillar='polished_basalt',
                  floor='polished_blackstone', floor2='crying_obsidian', roof='blackstone', rst='blackstone_stairs',
                  rwall='polished_blackstone_brick_wall', pane='purple_stained_glass_pane', lamp='soul_lantern', glow='ochre_froglight',
                  colour='purple', carpet='purple', crown='spire', troof='cone', found='polished_blackstone'),
    'sea': dict(main='prismarine_bricks', st='prismarine_brick_stairs', slab='prismarine_brick_slab', trim='dark_prismarine', course='dark_prismarine',
                accent='gold_block', pillar='quartz_pillar', floor='prismarine_bricks', floor2='dark_prismarine', roof='dark_prismarine',
                rst='dark_prismarine_stairs', rwall='prismarine_wall', pane='light_blue_stained_glass_pane', lamp='lantern', glow='sea_lantern',
                colour='cyan', carpet='cyan', crown='dome', troof='dome', found='dark_prismarine'),
    'forest': dict(main='mossy_stone_bricks', st='mossy_stone_brick_stairs', slab='mossy_stone_brick_slab', trim='stripped_oak_wood',
                   course='chiseled_stone_bricks', accent='moss_block', pillar='oak_log', floor='mossy_cobblestone', floor2='moss_block',
                   roof='dark_oak_planks', rst='dark_oak_stairs', rwall='mossy_stone_brick_wall', pane='lime_stained_glass_pane',
                   lamp='lantern', glow='shroomlight', colour='green', carpet='green', crown='tree', troof='cone', found='stone_bricks'),
    'earth': dict(main='tuff_bricks', st='tuff_brick_stairs', slab='tuff_brick_slab', trim='polished_andesite', course='chiseled_tuff_bricks',
                  accent='waxed_copper_block', pillar='polished_basalt', floor='polished_andesite', floor2='polished_tuff', roof='waxed_cut_copper',
                  rst='waxed_cut_copper_stairs', rwall='tuff_brick_wall', pane='orange_stained_glass_pane', lamp='lantern', glow='glowstone',
                  colour='brown', carpet='brown', crown='ziggurat', troof='flat', found='polished_andesite'),
    'eastern': dict(main='white_terracotta', st='smooth_quartz_stairs', slab='smooth_quartz_slab', trim='stripped_mangrove_log',
                    course='dark_oak_planks', accent='gold_block', pillar='stripped_mangrove_log', floor='stripped_dark_oak_wood', floor2='dark_oak_planks',
                    roof='deepslate_tiles', rst='deepslate_tile_stairs', rwall='deepslate_tile_wall', pane='white_stained_glass_pane',
                    lamp='lantern', glow='pearlescent_froglight', colour='red', carpet='red', crown='pagoda', troof='pagoda', found='polished_deepslate'),
    'forge': dict(main='deepslate_bricks', st='deepslate_brick_stairs', slab='deepslate_brick_slab', trim='polished_deepslate',
                  course='waxed_cut_copper', accent='iron_block', pillar='polished_basalt', floor='deepslate_tiles', floor2='waxed_cut_copper',
                  roof='waxed_cut_copper', rst='waxed_cut_copper_stairs', rwall='deepslate_brick_wall', pane='orange_stained_glass_pane',
                  lamp='lantern', glow='shroomlight', colour='orange', carpet='orange', crown='ziggurat', troof='flat', found='polished_deepslate'),
    'arcane': dict(main='deepslate_tiles', st='deepslate_tile_stairs', slab='deepslate_tile_slab', trim='purpur_block', course='amethyst_block',
                   accent='amethyst_block', pillar='purpur_pillar', floor='polished_deepslate', floor2='purpur_block', roof='purpur_block',
                   rst='purpur_stairs', rwall='deepslate_tile_wall', pane='magenta_stained_glass_pane', lamp='soul_lantern', glow='verdant_froglight',
                   colour='magenta', carpet='purple', crown='spire', troof='cone', found='polished_deepslate'),
    'royal': dict(main='stone_bricks', st='stone_brick_stairs', slab='stone_brick_slab', trim='polished_andesite', course='chiseled_stone_bricks',
                  accent='gold_block', pillar='quartz_pillar', floor='polished_andesite', floor2='smooth_stone', roof='blue_terracotta',
                  rst='deepslate_tile_stairs', rwall='stone_brick_wall', pane='blue_stained_glass_pane', lamp='lantern', glow='sea_lantern',
                  colour='blue', carpet='blue', crown='dome', troof='cone', found='polished_andesite'),
    'love': dict(main='pink_terracotta', st='cherry_stairs', slab='cherry_slab', trim='quartz_bricks', course='cherry_planks',
                 accent='gold_block', pillar='quartz_pillar', floor='cherry_planks', floor2='smooth_quartz', roof='cherry_planks',
                 rst='cherry_stairs', rwall='diorite_wall', pane='pink_stained_glass_pane', lamp='lantern', glow='pearlescent_froglight',
                 colour='pink', carpet='pink', crown='dome', troof='dome', found='smooth_quartz'),
    'end': dict(main='purpur_block', st='purpur_stairs', slab='purpur_slab', trim='end_stone_bricks', course='purpur_pillar',
                accent='gold_block', pillar='purpur_pillar', floor='end_stone_bricks', floor2='purpur_block', roof='obsidian',
                rst='end_stone_brick_stairs', rwall='end_stone_brick_wall', pane='magenta_stained_glass_pane', lamp='soul_lantern', glow='end_rod',
                colour='magenta', carpet='magenta', crown='dome', troof='cone', found='end_stone_bricks'),
    'desert': dict(main='cut_sandstone', st='sandstone_stairs', slab='cut_sandstone_slab', trim='chiseled_sandstone', course='smooth_sandstone',
                   accent='gold_block', pillar='smooth_sandstone', floor='smooth_sandstone', floor2='orange_terracotta', roof='lapis_block',
                   rst='smooth_sandstone_stairs', rwall='sandstone_wall', pane='orange_stained_glass_pane', lamp='lantern', glow='shroomlight',
                   colour='orange', carpet='orange', crown='ziggurat', troof='dome', found='smooth_sandstone'),
    'badlands': dict(main='cut_red_sandstone', st='red_sandstone_stairs', slab='cut_red_sandstone_slab', trim='chiseled_red_sandstone',
                     course='black_terracotta', accent='gilded_blackstone', pillar='polished_blackstone', floor='smooth_red_sandstone',
                     floor2='black_terracotta', roof='blackstone', rst='blackstone_stairs', rwall='red_sandstone_wall',
                     pane='black_stained_glass_pane', lamp='soul_lantern', glow='shroomlight', colour='black', carpet='black',
                     crown='spire', troof='cone', found='smooth_red_sandstone'),
    'frost': dict(main='packed_ice', st='polished_diorite_stairs', slab='polished_diorite_slab', trim='blue_ice', course='polished_diorite',
                  accent='diamond_block', pillar='quartz_pillar', floor='polished_diorite', floor2='blue_ice', roof='snow_block',
                  rst='polished_diorite_stairs', rwall='diorite_wall', pane='light_blue_stained_glass_pane', lamp='soul_lantern', glow='sea_lantern',
                  colour='light_blue', carpet='white', crown='spire', troof='cone', found='polished_diorite'),
}

GODS = {
    'kokuhaku': 'eastern', 'riha': 'frost', 'tenki': 'holy', 'chaos': 'abyss', 'berit': 'forge', 'elseria': 'arcane',
    'valeria': 'forge', 'huang_linghua': 'eastern', 'ferdinand': 'royal', 'mels': 'desert', 'hephaistos': 'forge',
    'nortia': 'love', 'lucifara': 'abyss', 'taika': 'eastern', 'mary_sue': 'end', 'savior': 'holy', 'gokuka': 'infernal',
    'merlinus': 'arcane', 'enkou': 'sea', 'kurma': 'earth', 'teia': 'celestial', 'bahamut': 'sea', 'nun': 'sea',
    'arcana': 'arcane', 'eomaia': 'forest', 'demiurgos': 'end', 'hakyoku': 'infernal', 'shinra': 'forest',
    'ain_sof_aur': 'holy', 'angra_mainyu': 'badlands', 'magna_mater': 'forest', 'ouroboros': 'abyss', 'yggdrasil': 'forest',
    'miyohime': 'eastern', 'innocence': 'holy', 'brutality': 'infernal', 'cursed_love': 'love', 'relentless_research': 'forge',
    'forbidden_arcana': 'arcane', 'fallen_savior': 'abyss', 'sweet_pact': 'love',
}

DIR = {'north': (0, -1), 'south': (0, 1), 'west': (-1, 0), 'east': (1, 0)}
OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}


def facing_of(dx, dz):
    return {(0, -1): 'north', (0, 1): 'south', (-1, 0): 'west', (1, 0): 'east'}[(dx, dz)]


class Grid:
    def __init__(self):
        self.c = {}
        self.be = {}

    def set(self, x, y, z, st, be=None):
        if 0 <= x < W and 0 <= y < H and 0 <= z < W:
            self.c[(x, y, z)] = st
            if be is not None:
                self.be[(x, y, z)] = be
            else:
                self.be.pop((x, y, z), None)

    def get(self, x, y, z):
        return self.c.get((x, y, z))

    def fill(self, x0, y0, z0, x1, y1, z1, st, only_empty=False):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    if only_empty and self.c.get((x, y, z)) not in (None, AIR):
                        continue
                    self.set(x, y, z, st)

    def solid(self, x, y, z):
        s = self.c.get((x, y, z))
        return s is not None and s != AIR and not CONNECT_NOT_SOLID(s)


AIR = 'minecraft:air'


def CONNECT_NOT_SOLID(s):
    n = s.split('[')[0]
    return any(k in n for k in ('pane', 'bars', '_wall', 'fence', 'lantern', 'torch', 'chain', 'ladder', 'carpet', 'banner',
                                'end_rod', 'lightning_rod', 'stairs', 'slab', 'spawner', 'chest', 'seal', 'leaves', 'vine'))


def build(style, seal, chests, spawners):
    P = {k: (S(v) if '[' not in v else 'minecraft:' + v) for k, v in style.items() if k not in ('crown', 'troof', 'colour', 'carpet')}
    g = Grid()
    main, trim, course, accent = P['main'], P['trim'], P['course'], P['accent']
    st, rst = style['st'], style['rst']

    # --- the plinth: a stepped base the whole castle stands on
    g.fill(1, 0, 1, W - 2, 0, W - 2, P['found'])
    for i in range(1, W - 1):
        for (x, z, f) in ((i, 0, 'north'), (i, W - 1, 'south'), (0, i, 'west'), (W - 1, i, 'east')):
            g.set(x, 0, z, stairs(st, OPP[f]))
    # the court's floor and its paths
    for x in range(5, 44):
        for z in range(5, 44):
            g.set(x, 0, z, P['floor'] if (x + z) % 2 == 0 else P['floor2'])
    for z in range(5, 48):
        for x in range(22, 27):
            g.set(x, 0, z, trim if x in (22, 26) else P['found'])
    for x in range(8, 41):
        for z in (23, 24, 25):
            if not 14 <= x <= 34:
                g.set(x, 0, z, trim if z != 24 else P['found'])
    # the court is cleared to the wall's height
    g.fill(5, 1, 5, 43, 12, 43, AIR)

    # --- the curtain wall: 3..45, two thick, walk on top at y=10
    def wall_cell(x, z):
        return (x in (3, 4, 44, 45) and 3 <= z <= 45) or (z in (3, 4, 44, 45) and 3 <= x <= 45)
    for x in range(3, 46):
        for z in range(3, 46):
            if not wall_cell(x, z):
                continue
            outer = x in (3, 45) or z in (3, 45)
            for y in range(1, 10):
                s = main
                if outer and y == 1:
                    s = trim
                elif outer and y == 5:
                    s = course
                g.set(x, y, z, s)
            # merlons on the outer line, every other block; the walk's parapet inside is a low wall
            if outer:
                if (x + z) % 2 == 0:
                    g.set(x, 10, z, main)
                    g.set(x, 11, z, P['slab'] + '[type=bottom,waterlogged=false]' if '[' not in P['slab'] else P['slab'])
                else:
                    g.set(x, 10, z, P['slab'] + '[type=bottom,waterlogged=false]')
            else:
                g.set(x, 10, z, AIR)
                g.set(x, 11, z, AIR)
    # corbels under the parapet, outside; arrow slits through the wall
    for i in range(3, 46):
        for (x, z, f) in ((i, 2, 'north'), (i, 46, 'south'), (2, i, 'west'), (46, i, 'east')):
            g.set(x, 9, z, stairs(st, OPP[f], 'top'))
        if i % 4 == 0 and 8 <= i <= 40 and not 18 <= i <= 30:
            for (x, z) in ((i, 3), (i, 4), (i, 44), (i, 45), (3, i), (4, i), (44, i), (45, i)):
                if (x, z) in ((i, 44), (i, 45)) and 15 <= i <= 33:
                    continue
                g.set(x, 3, z, S('iron_bars'))
                g.set(x, 4, z, S('iron_bars'))
            for (x, z, f) in ((i, 2, 'north'), (i, 46, 'south'), (2, i, 'west'), (46, i, 'east')):
                g.set(x, 6, z, stairs(st, OPP[f], 'top'))
    # stairs up to the walk, along the inside of the east and west walls
    for k in range(9):
        y = 1 + k
        for (x, z, f) in ((43, 30 - k, 'north'), (5, 30 - k, 'north')):
            g.set(x, y, z, stairs(st, f))
            for yy in range(1, y):
                g.set(x, yy, z, main)
        for (x, z) in ((43, 30 - k), (5, 30 - k)):
            g.fill(x, y + 1, z, x, y + 3, z, AIR)

    # --- the corner towers: octagons of radius 4
    def octagon(cx, cz, r):
        return [(cx + dx, cz + dz) for dx in range(-r, r + 1) for dz in range(-r, r + 1) if abs(dx) + abs(dz) <= r + r // 2]

    def edge(cells):
        s = set(cells)
        return [(x, z) for (x, z) in cells if any((x + dx, z + dz) not in s for dx, dz in DIR.values())]
    towers = [(5, 5), (43, 5), (5, 43), (43, 43)]
    tchest = chests[1:5]
    tspawn = spawners[:4]
    for ti, (cx, cz) in enumerate(towers):
        cells = octagon(cx, cz, 4)
        rim = set(edge(cells))
        top = 18
        for (x, z) in cells:
            g.set(x, 0, z, P['found'])
            for y in range(1, top + 1):
                if (x, z) in rim:
                    s = trim if y in (1, 9) else (course if y == 14 else main)
                    g.set(x, y, z, s)
                else:
                    g.set(x, y, z, AIR)
        # windows (none behind the ladder)
        sx, sz = (1 if cx < C else -1), (1 if cz < C else -1)
        for (x, z) in rim:
            dx, dz = x - cx, z - cz
            if (dx == 0 or dz == 0) and max(abs(dx), abs(dz)) == 4 and dx != -4 * sx:
                for y in (11, 12, 15, 16):
                    g.set(x, y, z, P['pane'])
        # floors at y=7 and y=13 with a ladder hole, the ladder on the court side
        sx, sz = (1 if cx < C else -1), (1 if cz < C else -1)
        for fy in (7, 13):
            for (x, z) in cells:
                if (x, z) not in rim:
                    g.set(x, fy, z, P['floor'])
        # the ladder clings to the rim on the side away from the court, up through both floors and the roof's floor
        lx, lz = cx - 3 * sx, cz
        for y in range(1, top + 1):
            g.set(lx, y, lz, S('ladder', facing='east' if sx > 0 else 'west', waterlogged='false'))
        # a door to the court; doors to the wall walks where the walls meet the tower
        for y in (1, 2, 3):
            g.set(cx + 4 * sx, y, cz, AIR)
        g.set(cx + 4 * sx, 4, cz, stairs(st, 'west' if sx > 0 else 'east', 'top'))
        for y in (10, 11):
            g.set(cx + 4 * sx, y, cz - sz, AIR)
            g.set(cx - sx, y, cz + 4 * sz, AIR)
        # crown: corbels round the top, merlons
        for (x, z) in rim:
            dx, dz = x - cx, z - cz
            for f, (ox, oz) in DIR.items():
                if (x + ox, z + oz) not in cells:
                    g.set(x + ox, top - 1, z + oz, stairs(st, OPP[f], 'top'))
                    if (x + z) % 2 == 0:
                        g.set(x + ox, top, z + oz, main)
                        g.set(x + ox, top + 1, z + oz, P['rwall'])
                    else:
                        g.set(x + ox, top, z + oz, P['slab'] + '[type=bottom,waterlogged=false]')
        for (x, z) in cells:
            g.set(x, top, z, P['floor'] if (x, z) not in rim else main)
        tower_roof(g, P, style, cx, top + 1, cz, 4)
        # spawner and chest on the ground floor, a hanging light on each floor
        g.set(cx, 1, cz, S('spawner'), tspawn[ti] if ti < len(tspawn) else None)
        if ti < len(tchest):
            g.set(cx + sx, 1, cz - sz if False else cz + sz, chest_state(tchest[ti]), tchest[ti][1])
        for fy in (6, 12, 17):
            g.set(cx - sx, fy, cz - sz, S('chain', axis='y'))
            g.set(cx - sx, fy - 1, cz - sz, S(style['lamp'], hanging='true', waterlogged='false'))
        g.set(cx, top, cz, P['glow'])

    # --- the gatehouse: two square towers flanking a vaulted gate in the south wall
    for gx0 in (17, 27):
        gx1 = gx0 + 4
        for x in range(gx0, gx1 + 1):
            for z in range(42, 48):
                rim = x in (gx0, gx1) or z in (42, 47)
                g.set(x, 0, z, P['found'])
                for y in range(1, 15):
                    if rim:
                        g.set(x, y, z, trim if y in (1, 8) else main)
                    else:
                        g.set(x, y, z, AIR)
                g.set(x, 14, z, main if rim else P['floor'])
        for x in range(gx0 - 1, gx1 + 2):
            for z in range(41, 49):
                if x in (gx0 - 1, gx1 + 1) or z in (41, 48):
                    if 0 <= z < W:
                        g.set(x, 13, z, stairs(st, 'east' if x == gx0 - 1 else 'west' if x == gx1 + 1 else 'south' if z == 41 else 'north', 'top'))
                        g.set(x, 14, z, main if (x + z) % 2 == 0 else P['slab'] + '[type=bottom,waterlogged=false]')
        tower_roof(g, P, style, gx0 + 2, 15, 44 + 1, 2, square=(gx0, gx1, 42, 47))
        # doors from the court and windows
        for y in (1, 2, 3):
            g.set(gx0 + 2, y, 42, AIR)
        for y in (9, 10, 11):
            g.set(gx0 + 2, y, 47, P['pane'])
            g.set(gx0 + 2, y, 42, P['pane'])
        g.set(gx0 + 2, 13, 44, S('chain', axis='y'))
        g.set(gx0 + 2, 12, 44, S(style['lamp'], hanging='true', waterlogged='false'))
        # banners on the face
        g.set(gx0 + 2, 7, 48, S(style['colour'] + '_wall_banner', facing='south'))
    # the gate: 5 wide, a vault of 6, through the wall, with a portcullis half down
    for x in range(22, 27):
        for z in range(42, 48):
            for y in range(1, 8):
                g.set(x, y, z, AIR)
            g.set(x, 8, z, main)
            g.set(x, 9, z, main)
        g.set(x, 7, 47, trim)
        g.set(x, 6, 46, S('iron_bars'))
        g.set(x, 7, 46, S('iron_bars'))
    for x in range(22, 27):
        for z in range(42, 48):
            g.set(x, 10, z, P['floor'])
    for z in range(42, 48):
        g.set(22, 7, z, stairs(st, 'east', 'top'))
        g.set(26, 7, z, stairs(st, 'west', 'top'))
    g.set(24, 8, 48, accent)
    # the first chest just inside the gate
    if chests:
        g.set(21, 1, 41, chest_state(chests[0], 'south'), chests[0][1])

    # --- the court: lamp posts, braziers
    for (x, z) in ((20, 39), (28, 39), (20, 36), (28, 36), (10, 21), (10, 27), (38, 21), (38, 27)):
        g.set(x, 1, z, trim)
        g.set(x, 2, z, P['rwall'])
        g.set(x, 3, z, P['rwall'])
        g.set(x, 4, z, S(style['lamp'], hanging='false', waterlogged='false'))
    for (x, z) in ((10, 10), (38, 10), (10, 38), (38, 38)):
        g.fill(x - 1, 1, z - 1, x + 1, 1, z + 1, trim)
        for (ax, az) in ((x - 1, z - 1), (x + 1, z - 1), (x - 1, z + 1), (x + 1, z + 1)):
            g.set(ax, 2, az, stairs(st, 'north' if az < z else 'south'))
        g.set(x, 2, z, accent)
        g.set(x, 3, z, S('campfire', lit='true', facing='north', signal_fire='false', waterlogged='false'))

    # --- the keep
    keep(g, P, style, seal, chests[5:], spawners[4:])
    for (x, y, z), s in list(g.c.items()):
        pass
    connect(g)
    return g


def chest_state(ch, facing=None):
    return S('chest', facing=facing or 'north', type='single', waterlogged='false')


def tower_roof(g, P, style, cx, y0, cz, r, square=None):
    kind = style['troof']
    rst = style['rst']
    roof = P['roof']
    if square:
        x0, x1, z0, z1 = square
        x0, x1, z0, z1 = x0 + 1, x1 - 1, z0 + 1, z1 - 1
        # a small hipped roof
        y = y0
        while x0 <= x1 and z0 <= z1:
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    edge = x in (x0, x1) or z in (z0, z1)
                    if not edge:
                        g.set(x, y, z, roof)
                        continue
                    f = 'south' if z == z0 else 'north' if z == z1 else 'east' if x == x0 else 'west'
                    g.set(x, y, z, stairs(rst, f))
            x0, x1, z0, z1, y = x0 + 1, x1 - 1, z0 + 1, z1 - 1, y + 1
        g.set((square[0] + square[1]) // 2, y, (square[2] + square[3]) // 2, S('lightning_rod', facing='up', powered='false', waterlogged='false'))
        return
    if kind == 'flat':
        g.set(cx, y0, cz, P['glow'])
        g.set(cx, y0 + 1, cz, P['rwall'])
        g.set(cx, y0 + 2, cz, S('lantern', hanging='false', waterlogged='false'))
        return
    if kind == 'dome':
        R = r + 0.5
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                for dy in range(0, r + 1):
                    d = math.sqrt(dx * dx + dz * dz + (dy * 1.15) ** 2)
                    if R - 1.2 <= d <= R:
                        g.set(cx + dx, y0 + dy, cz + dz, roof)
                    elif d < R - 1.2:
                        g.set(cx + dx, y0 + dy, cz + dz, AIR)
        yt = y0 + int(R / 1.15) + 1                       # just over the dome's crown
        g.set(cx, yt, cz, P['accent'])
        g.set(cx, yt + 1, cz, S('lightning_rod', facing='up', powered='false', waterlogged='false'))
        return
    if kind == 'pagoda':
        # wide flared eaves, then a small hipped cap
        for ring, y in ((r + 1, y0), (r, y0 + 1)):
            for dx in range(-ring, ring + 1):
                for dz in range(-ring, ring + 1):
                    if max(abs(dx), abs(dz)) == ring:
                        f = 'south' if dz == -ring else 'north' if dz == ring else 'east' if dx == -ring else 'west'
                        g.set(cx + dx, y, cz + dz, stairs(rst, f))
                    elif max(abs(dx), abs(dz)) < ring:
                        g.set(cx + dx, y, cz + dz, roof)
        for k in range(r):
            ring = r - 1 - k
            y = y0 + 2 + k
            for dx in range(-ring, ring + 1):
                for dz in range(-ring, ring + 1):
                    if max(abs(dx), abs(dz)) == ring and ring > 0:
                        f = 'south' if dz == -ring else 'north' if dz == ring else 'east' if dx == -ring else 'west'
                        g.set(cx + dx, y, cz + dz, stairs(rst, f))
                    else:
                        g.set(cx + dx, y, cz + dz, roof)
        g.set(cx, y0 + r + 2, cz, P['accent'])
        g.set(cx, y0 + r + 3, cz, S('lightning_rod', facing='up', powered='false', waterlogged='false'))
        return
    # a cone: rings of stairs, two blocks up for each step in
    y = y0
    rr = r + 1
    while rr >= 0:
        for _ in range(2):
            for dx in range(-rr, rr + 1):
                for dz in range(-rr, rr + 1):
                    if abs(dx) + abs(dz) > rr + rr // 2:
                        continue
                    on_rim = any(abs(dx + ox) + abs(dz + oz) > rr + rr // 2 or max(abs(dx + ox), abs(dz + oz)) > rr for ox, oz in DIR.values())
                    if on_rim and rr > 0:
                        # face outwards: pick the open side
                        f = None
                        for name, (ox, oz) in DIR.items():
                            if abs(dx + ox) + abs(dz + oz) > rr + rr // 2 or max(abs(dx + ox), abs(dz + oz)) > rr:
                                f = name
                                break
                        g.set(cx + dx, y, cz + dz, stairs(rst, OPP[f]))
                    else:
                        g.set(cx + dx, y, cz + dz, roof)
            y += 1
        rr -= 1
    g.set(cx, y, cz, P['accent'])
    g.set(cx, y + 1, cz, S('lightning_rod', facing='up', powered='false', waterlogged='false'))


def keep(g, P, style, seal, chests, spawners):
    main, trim, course, accent, st = P['main'], P['trim'], P['course'], P['accent'], style['st']
    x0, x1 = 14, 34
    top = 16
    # walls, floor, ceiling
    for x in range(x0, x1 + 1):
        for z in range(x0, x1 + 1):
            rim = x in (x0, x1) or z in (x0, x1)
            g.set(x, 0, z, P['found'])
            for y in range(1, top + 1):
                if rim:
                    g.set(x, y, z, trim if y in (1, 12) else (course if y == 6 else main))
                else:
                    g.set(x, y, z, AIR)
            g.set(x, top, z, main if rim else P['floor2'])
    # the hall's floor: a border and a runner to the dais
    for x in range(x0 + 1, x1):
        for z in range(x0 + 1, x1):
            ring = min(x - x0, x1 - x, z - x0, x1 - z)
            g.set(x, 0, z, trim if ring == 1 else (P['floor2'] if (x // 2 + z // 2) % 2 else P['floor']))
    for z in range(C + 3, x1):
        g.set(C, 0, z, accent if z % 3 == 0 else P['found'])
        g.set(C, 1, z, S(style['carpet'] + '_carpet'))
    # buttresses: pilasters one block proud, sloping off at the top; tall windows between them
    for i in range(x0, x1 + 1, 5):
        for (x, z, f) in ((i, x0 - 1, 'north'), (i, x1 + 1, 'south'), (x0 - 1, i, 'west'), (x1 + 1, i, 'east')):
            for y in range(1, 14):
                g.set(x, y, z, trim if y in (1, 6, 12) else main)
            g.set(x, 14, z, stairs(st, OPP[f]))
    for i in (x0 + 2, x0 + 7, x0 + 12, x0 + 17):
        for j in (0, 1):
            for (x, z) in ((i + j, x0), (i + j, x1), (x0, i + j), (x1, i + j)):
                if z == x1 and C - 2 <= x <= C + 2:
                    continue
                for y in range(4, 11):
                    g.set(x, y, z, P['pane'])
                g.set(x, 3, z, accent)
    # window heads: upside-down stairs over each pair
    # the door: 3 wide, 5 high, a pointed head, on the south face
    for x in range(C - 1, C + 2):
        for y in range(1, 6):
            g.set(x, y, x1, AIR)
    g.set(C - 1, 5, x1, stairs(st, 'east', 'top'))
    g.set(C + 1, 5, x1, stairs(st, 'west', 'top'))
    for x in range(C - 2, C + 3):
        g.set(x, 7, x1 + 1, accent if x == C else trim)
        g.set(x, 6, x1 + 1, stairs(st, 'south', 'top'))
    g.set(C - 2, 1, x1 + 1, trim); g.set(C + 2, 1, x1 + 1, trim)
    for y in range(2, 6):
        g.set(C - 2, y, x1 + 1, P['pillar'])
        g.set(C + 2, y, x1 + 1, P['pillar'])
    g.set(C - 3, 4, x1 + 1, S(style['lamp'], hanging='false', waterlogged='false'))
    g.set(C + 3, 4, x1 + 1, S(style['lamp'], hanging='false', waterlogged='false'))
    g.set(C - 3, 3, x1 + 1, P['rwall'])
    g.set(C + 3, 3, x1 + 1, P['rwall'])
    g.set(C - 3, 2, x1 + 1, P['rwall'])
    g.set(C + 3, 2, x1 + 1, P['rwall'])
    g.set(C - 3, 1, x1 + 1, trim)
    g.set(C + 3, 1, x1 + 1, trim)
    # columns down the hall, each with a base and a capital
    for x in (C - 6, C + 6):
        for z in (C - 6, C - 2, C + 2, C + 6):
            g.set(x, 1, z, trim)
            for y in range(2, top - 1):
                g.set(x, y, z, P['pillar'])
            g.set(x, top - 1, z, trim)
            for f, (ox, oz) in DIR.items():
                g.set(x + ox, top - 1, z + oz, stairs(st, OPP[f], 'top'))
    # the dais and the seal
    g.fill(C - 2, 1, C - 2, C + 2, 1, C + 2, trim)
    for i in range(C - 2, C + 3):
        for (x, z, f) in ((i, C - 3, 'north'), (i, C + 3, 'south'), (C - 3, i, 'west'), (C + 3, i, 'east')):
            g.set(x, 1, z, stairs(st, OPP[f]))
    # gilded corners at the dais's level only: the god rises over the seal into a clear space eleven wide and thirteen high
    for (x, z) in ((C - 2, C - 2), (C + 2, C - 2), (C - 2, C + 2), (C + 2, C + 2)):
        g.set(x, 2, z, P['glow'])
    for (x, z) in ((C - 2, C), (C + 2, C), (C, C + 2)):
        g.set(x, 2, z, accent)
    # lights set in the hall's floor, every fourth block, off the runner and the dais
    for x in range(x0 + 2, x1 - 1, 4):
        for z in range(x0 + 2, x1 - 1, 4):
            if abs(x - C) <= 3 and abs(z - C) <= 3 or x == C:
                continue
            g.set(x, 0, z, P['glow'] if P['glow'].split('[')[0] not in ('minecraft:end_rod',) else 'minecraft:sea_lantern')
    g.set(C, 2, C, seal)
    if chests:
        ch = chests[-1]
        g.set(C, 2, C - 2, chest_state(ch, 'south'), ch[1])
    # chandeliers on chains
    # (none over the seal)
    for (x, z) in ((C - 9, C - 4), (C - 9, C + 4), (C + 9, C - 4), (C + 9, C + 4), (C, C + 8), (C, C - 8)):
        for y in range(top - 4, top):
            g.set(x, y, z, S('chain', axis='y'))
        g.set(x, top - 5, z, S(style['lamp'], hanging='true', waterlogged='false'))
    # side chapels in the four corners: a spawner and a chest each, behind a low screen
    rest = chests[:-1] if chests else []
    for k, (x, z) in enumerate(((x0 + 3, x0 + 3), (x1 - 3, x0 + 3), (x0 + 3, x1 - 3), (x1 - 3, x1 - 3))):
        if k < len(spawners):
            g.set(x, 1, z, S('spawner'), spawners[k])
        if k < len(rest):
            sx = 1 if x < C else -1
            g.set(x - sx, 1, z, chest_state(rest[k], 'east' if sx < 0 else 'west'), rest[k][1])
        for y in (5, 9):
            pass
    for ch in rest[4:]:
        pass
    # --- the second storey: a smaller box with its own windows, then the crown
    y2 = top + 1
    a0, a1 = 17, 31
    for x in range(x0, x1 + 1):
        for z in range(x0, x1 + 1):
            if x in (x0, x1) or z in (x0, x1):
                if (x + z) % 2 == 0:
                    g.set(x, y2, z, main)
                else:
                    g.set(x, y2, z, P['slab'] + '[type=bottom,waterlogged=false]')
    for f, rng in (('north', [(x, x0 - 1) for x in range(x0 - 1, x1 + 2)]), ('south', [(x, x1 + 1) for x in range(x0 - 1, x1 + 2)]),
                   ('west', [(x0 - 1, z) for z in range(x0, x1 + 1)]), ('east', [(x1 + 1, z) for z in range(x0, x1 + 1)])):
        for (x, z) in rng:
            if x in (x0 - 1, x1 + 1) and z in (x0 - 1, x1 + 1):
                continue
            if g.get(x, 14, z) is None:
                g.set(x, top - 1, z, stairs(st, OPP[f], 'top'))
    top2 = y2 + 7
    for x in range(a0, a1 + 1):
        for z in range(a0, a1 + 1):
            rim = x in (a0, a1) or z in (a0, a1)
            for y in range(y2, top2 + 1):
                if rim:
                    corner = x in (a0, a1) and z in (a0, a1)
                    win = not corner and (x - a0) % 4 == 2 or (not corner and (z - a0) % 4 == 2)
                    if win and y2 + 2 <= y <= y2 + 5 and not corner and ((x in (a0, a1)) != (z in (a0, a1))):
                        along = z if x in (a0, a1) else x
                        if (along - a0) % 4 == 2:
                            g.set(x, y, z, P['pane'])
                            continue
                    g.set(x, y, z, P['pillar'] if corner else (trim if y in (y2, top2) else main))
                elif y > y2:
                    g.set(x, y, z, AIR)
                else:
                    g.set(x, y, z, P['floor'])
    for x in range(a0 + 1, a1):
        for z in range(a0 + 1, a1):
            g.set(x, top2, z, P['floor2'])
    for (x, z) in ((C - 3, C - 3), (C + 3, C - 3), (C - 3, C + 3), (C + 3, C + 3)):
        g.set(x, top2 - 1, z, S('chain', axis='y'))
        g.set(x, top2 - 2, z, S(style['lamp'], hanging='true', waterlogged='false'))
    # a ladder from the hall's floor up to the upper storey, in the north-west corner
    for y in range(1, top + 1):
        g.set(x0 + 1, y, x0 + 6, S('ladder', facing='east', waterlogged='false'))
    # from the roof walk a door into the upper storey; the chests left over wait there
    for y in (y2 + 1, y2 + 2):
        g.set(a0, y, C, AIR)
    g.set(a0, y2, C, stairs(st, 'east'))
    for k, ch in enumerate(rest[4:]):
        x, z = ((C - 4, C), (C + 4, C), (C, C - 4), (C, C + 4))[k % 4]
        g.set(x, y2 + 1, z, chest_state(ch, 'south'), ch[1])
    crown(g, P, style, top2 + 1, a0, a1)


def crown(g, P, style, y0, a0, a1):
    kind = style['crown']
    roof, rst, accent = P['roof'], style['rst'], P['accent']
    r = (a1 - a0) // 2
    cx = cz = C
    # a parapet round the top of the second storey
    for x in range(a0 - 1, a1 + 2):
        for z in range(a0 - 1, a1 + 2):
            if x in (a0 - 1, a1 + 1) or z in (a0 - 1, a1 + 1):
                f = 'north' if z == a0 - 1 else 'south' if z == a1 + 1 else 'west' if x == a0 - 1 else 'east'
                g.set(x, y0 - 2, z, stairs(style['st'], OPP[f], 'top'))
    if kind == 'dome':
        # a drum, then a dome, a lantern and a finial
        R = r - 0.5
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                d0 = math.hypot(dx, dz)
                if R - 1.5 <= d0 <= R:
                    for y in range(y0, y0 + 3):
                        g.set(cx + dx, y, cz + dz, P['pane'] if (y == y0 + 1 and (dx + dz) % 2 == 0) else P['main'])
                    g.set(cx + dx, y0 + 3, cz + dz, P['trim'])
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                for dy in range(0, r + 1):
                    d = math.sqrt(dx * dx + dz * dz + (dy * 1.1) ** 2)
                    if R - 1.3 <= d <= R:
                        rib = dx == 0 or dz == 0 or abs(dx) == abs(dz)
                        g.set(cx + dx, y0 + 4 + dy, cz + dz, accent if rib and roof != accent else roof)
        yt = y0 + 4 + int(r / 1.1)
        g.fill(cx - 1, yt, cz - 1, cx + 1, yt + 2, cz + 1, P['main'])
        g.set(cx, yt + 1, cz, P['glow'])
        for f, (ox, oz) in DIR.items():
            g.set(cx + ox, yt + 1, cz + oz, P['pane'])
            g.set(cx + ox, yt + 3, cz + oz, stairs(rst, OPP[f]))
        g.set(cx, yt + 3, cz, accent)
        g.set(cx, yt + 4, cz, accent)
        g.set(cx, yt + 5, cz, S('lightning_rod', facing='up', powered='false', waterlogged='false'))
        return
    if kind == 'spire':
        # a steep pyramid, a pinnacle at each corner, a needle
        y = y0
        rr = r + 1
        while rr >= 0:
            for _ in range(2 if rr > 2 else 3):
                for dx in range(-rr, rr + 1):
                    for dz in range(-rr, rr + 1):
                        if max(abs(dx), abs(dz)) == rr and rr > 0:
                            f = 'north' if dz == -rr else 'south' if dz == rr else 'west' if dx == -rr else 'east'
                            g.set(cx + dx, y, cz + dz, stairs(rst, OPP[f]))
                        else:
                            g.set(cx + dx, y, cz + dz, roof)
                y += 1
            rr -= 1
        for k in range(4):
            g.set(cx, y + k, cz, accent if k < 2 else P['rwall'])
        g.set(cx, y + 4, cz, S('lightning_rod', facing='up', powered='false', waterlogged='false'))
        for (px, pz) in ((a0 - 1, a0 - 1), (a1 + 1, a0 - 1), (a0 - 1, a1 + 1), (a1 + 1, a1 + 1)):
            for k in range(5):
                g.set(px, y0 - 2 + k, pz, P['pillar'] if k < 3 else P['rwall'])
            g.set(px, y0 + 3, pz, accent)
            g.set(px, y0 + 4, pz, S('lightning_rod', facing='up', powered='false', waterlogged='false'))
        # dormers on the roof's four faces
        for f, (ox, oz) in DIR.items():
            bx, bz = cx + ox * (r - 1), cz + oz * (r - 1)
            for y in range(y0, y0 + 3):
                g.set(bx, y, bz, P['pane'] if y == y0 + 1 else P['trim'])
            g.set(bx, y0 + 3, bz, stairs(rst, f))
        return
    if kind == 'pagoda':
        y = y0
        for ring in (r + 2, r - 1, r - 4):
            if ring < 2:
                break
            # eaves: two courses of stairs flaring out, then the storey's walls
            for k, rr in enumerate((ring + 1, ring)):
                for dx in range(-rr, rr + 1):
                    for dz in range(-rr, rr + 1):
                        if max(abs(dx), abs(dz)) == rr:
                            f = 'north' if dz == -rr else 'south' if dz == rr else 'west' if dx == -rr else 'east'
                            g.set(cx + dx, y + k, cz + dz, stairs(rst, OPP[f]))
                        elif max(abs(dx), abs(dz)) < rr:
                            g.set(cx + dx, y + k, cz + dz, P['roof'])
            # gilded tips at the corners of the eaves
            for sx in (-1, 1):
                for sz in (-1, 1):
                    g.set(cx + sx * (ring + 1), y + 1, cz + sz * (ring + 1), accent)
                    g.set(cx + sx * (ring + 1), y + 2, cz + sz * (ring + 1), S(style['lamp'], hanging='false', waterlogged='false'))
            y += 2
            inner = ring - 3
            if inner < 1:
                break
            for dx in range(-inner, inner + 1):
                for dz in range(-inner, inner + 1):
                    rim = max(abs(dx), abs(dz)) == inner
                    for yy in range(y, y + 3):
                        if rim:
                            corner = abs(dx) == inner and abs(dz) == inner
                            s = P['pillar'] if corner else (P['pane'] if yy == y + 1 and (dx + dz) % 2 == 0 else P['main'])
                            g.set(cx + dx, yy, cz + dz, s)
                        else:
                            g.set(cx + dx, yy, cz + dz, AIR)
            y += 3
        # the finial: a gilded spire of rings
        for k in range(6):
            g.set(cx, y + k, cz, accent if k % 2 == 0 else P['rwall'])
        g.set(cx, y + 6, cz, S('lightning_rod', facing='up', powered='false', waterlogged='false'))
        return
    if kind == 'ziggurat':
        y = y0
        rr = r
        while rr >= 2:
            for k in range(3):
                for dx in range(-rr, rr + 1):
                    for dz in range(-rr, rr + 1):
                        rim = max(abs(dx), abs(dz)) == rr
                        if k == 2 and rim:
                            f = 'north' if dz == -rr else 'south' if dz == rr else 'west' if dx == -rr else 'east'
                            g.set(cx + dx, y + k, cz + dz, stairs(rst, OPP[f]))
                        elif rim:
                            g.set(cx + dx, y + k, cz + dz, P['course'] if k == 1 else P['main'])
                        else:
                            g.set(cx + dx, y + k, cz + dz, P['roof'] if k == 2 else AIR)
            y += 3
            rr -= 2
        # a shrine on top: four pillars, a glowing heart, a gilded cap
        for (px, pz) in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            for k in range(4):
                g.set(cx + px, y + k, cz + pz, P['pillar'])
        g.set(cx, y, cz, P['glow'])
        g.set(cx, y + 1, cz, accent)
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                g.set(cx + dx, y + 4, cz + dz, P['slab'] + '[type=bottom,waterlogged=false]' if max(abs(dx), abs(dz)) == 2 else accent)
        g.set(cx, y + 5, cz, S('lightning_rod', facing='up', powered='false', waterlogged='false'))
        return
    if kind == 'tree':
        # a great tree rising out of the keep: a trunk, roots over the roof, a crown of leaves
        y = y0
        for k in range(14):
            for (dx, dz) in ((0, 0), (1, 0), (0, 1), (1, 1)):
                g.set(cx + dx, y + k, cz + dz, S('oak_wood', axis='y') if k < 10 else S('oak_log', axis='y'))
        for f, (ox, oz) in DIR.items():
            for k in range(1, 5):
                g.set(cx + ox * (k + (1 if ox > 0 or oz > 0 else 0)), y0 + max(0, 2 - k // 2) - 1, cz + oz * (k + (1 if ox > 0 or oz > 0 else 0)),
                      S('oak_wood', axis='x' if ox else 'z'))
        top = y + 12
        for dx in range(-9, 11):
            for dz in range(-9, 11):
                for dy in range(-4, 6):
                    d = math.sqrt(((dx - 0.5) / 9.5) ** 2 + ((dz - 0.5) / 9.5) ** 2 + (dy / 5.0) ** 2)
                    if d <= 1.0 and ((dx * 7 + dz * 13 + dy * 5) % 11 != 0 or d < 0.7):
                        if g.get(cx + dx, top + dy, cz + dz) is None or g.get(cx + dx, top + dy, cz + dz) == AIR:
                            g.set(cx + dx, top + dy, cz + dz, S('flowering_azalea_leaves' if (dx + dz + dy) % 5 == 0 else 'oak_leaves',
                                                                distance='1', persistent='true', waterlogged='false'))
        for (dx, dz) in ((-4, 2), (5, -3), (2, 6), (-3, -5), (6, 4)):
            g.set(cx + dx, top - 2, cz + dz, S('shroomlight'))
        return


def connect(g):
    """Panes, bars and walls joined to what stands beside them."""
    def fam(s):
        n = s.split('[')[0]
        if n.endswith('_pane') or n.endswith('iron_bars'):
            return 'pane'
        if n.endswith('_wall') and 'banner' not in n:
            return 'wall'
        return None
    for (x, y, z), s in list(g.c.items()):
        f = fam(s)
        if not f:
            continue
        name = s.split('[')[0]
        sides = {}
        for d, (dx, dz) in DIR.items():
            n = g.get(x + dx, y, z + dz)
            ok = n is not None and n != AIR and (fam(n) == f or not CONNECT_NOT_SOLID(n))
            sides[d] = ok
        if f == 'pane':
            if not any(sides.values()):
                sides = {'north': False, 'south': False, 'east': True, 'west': True}
            g.c[(x, y, z)] = S(name, **{d: str(v).lower() for d, v in sides.items()}, waterlogged='false')
        else:
            straight = (sides['north'] and sides['south'] and not sides['east'] and not sides['west']) or \
                       (sides['east'] and sides['west'] and not sides['north'] and not sides['south'])
            above = g.get(x, y + 1, z)
            up = not straight or (above is not None and above != AIR)
            g.c[(x, y, z)] = S(name, **{d: ('low' if v else 'none') for d, v in sides.items()}, up=str(up).lower(), waterlogged='false')


def to_nbt(g, data_version):
    pal, idx, blocks = [], {}, []
    for (x, y, z) in sorted(g.c, key=lambda p: (p[1], p[2], p[0])):
        s = g.c[(x, y, z)]
        if s not in idx:
            idx[s] = len(pal)
            name, _, props = s.partition('[')
            e = {'Name': name}
            if props:
                e['Properties'] = dict(kv.split('=') for kv in props.rstrip(']').split(','))
            pal.append(e)
        b = {'state': Typed(3, idx[s]), 'pos': [Typed(3, x), Typed(3, y), Typed(3, z)]}
        if (x, y, z) in g.be:
            b['nbt'] = g.be[(x, y, z)]
        blocks.append(b)
    return {'DataVersion': data_version, 'size': [Typed(3, W), Typed(3, H), Typed(3, W)], 'palette': pal, 'blocks': blocks,
            'entities': []}


def keep_seal_clear(nbt):
    """The god rises over the seal: no light the lighting rule put there stays (eleven wide, thirteen high over it)."""
    pal = [state_key(p) for p in nbt['palette']]
    if 'minecraft:air' not in pal:
        nbt['palette'].append({'Name': 'minecraft:air'})
        pal.append('minecraft:air')
    air = pal.index('minecraft:air')
    for b in nbt['blocks']:
        x, y, z = (anvil.val(v) for v in b['pos'])
        if abs(x - C) <= 5 and abs(z - C) <= 5 and 3 <= y <= 15:
            name = pal[anvil.val(b['state'])].split('[')[0]
            if name.endswith('torch') or name.endswith('lantern') and 'sea_' not in name:
                b['state'] = Typed(3, air)


def state_key(p):
    props = p.get('Properties') or {}
    if not props:
        return p['Name']
    return p['Name'] + '[' + ','.join('%s=%s' % (k, anvil.val(v)) for k, v in sorted(props.items())) + ']'


def harvest(old):
    """The seal, the chests (with their loot tables and facing) and the spawners (with their minions) of the old template."""
    pal = [state_key(p) for p in old['palette']]
    seal, chests, spawners = None, [], []
    for b in old['blocks']:
        s = pal[anvil.val(b['state'])]
        if s.endswith('_boss_seal') or 'boss_seal' in s:
            seal = s
        elif s.startswith('minecraft:chest'):
            chests.append((s, b.get('nbt')))
        elif s == 'minecraft:spawner':
            spawners.append(b.get('nbt'))
    # the first chest by the gate holds tier 1, the one behind the seal the best
    def tier(c):
        lt = anvil.val((c[1] or {}).get('LootTable', ''))
        return int(lt[-1]) if lt and lt[-1].isdigit() else 2
    chests.sort(key=tier)
    return seal, chests, spawners, anvil.val(old.get('DataVersion', 3955))


def main():
    folder = sys.argv[1]
    want = set(sys.argv[2:])
    for god, style in sorted(GODS.items()):
        if want and god not in want:
            continue
        path = os.path.join(folder, god + '_citadel.nbt')
        old = anvil.read_nbt_typed(gzip.decompress(open(path, 'rb').read()))
        if anvil.val(old['size'][0]) == W:
            print(god, 'already built')
            continue
        seal, chests, spawners, dv = harvest(old)
        g = build(STYLES[style], seal, chests, spawners)
        nbt = to_nbt(g, dv)
        # any corner still dark gets a light by the rule every OROR template was lit by in r62
        res = structure_lights.light_template(nbt)
        lit = None
        if res is not None:
            lit, new = res
            if new is not None:
                nbt = new
        keep_seal_clear(nbt)
        with open(path, 'wb') as f:
            f.write(gzip.compress(anvil.write_nbt(nbt), 6, mtime=0))
        print(god, style, 'blocks', len(nbt['blocks']), 'chests', len(chests), 'spawners', len(spawners), 'seal', seal, 'lights', lit, flush=True)


if __name__ == '__main__':
    main()

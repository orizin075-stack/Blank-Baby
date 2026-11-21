"""stages_a.py: the gods' stages, Kokuhaku to Mary Sue (god_stages.py). Each builder's docstring says what the stage
is drawn from."""
import math
from stage_kit import AIR, W, C, S, stair, slab, lantern, outward, DIRS, OPP


def plaza(g, r, floor, rim=None, rimstair=None, y=0, clear_h=18):
    g.disc(C, C, r, y, None, pattern=floor if callable(floor) else (lambda x, z, d: floor))
    if rim:
        g.ring(C, C, r - 0.5, r, y, rim)
    if rimstair:
        for x in range(C - r - 2, C + r + 3):
            for z in range(C - r - 2, C + r + 3):
                d = math.hypot(x - C, z - C)
                if r + 0.3 < d <= r + 1.3:
                    g.set(x, y, z, stair(rimstair, OPP[outward(x - C, z - C)]))
    g.clear(C, C, r + 1, y + 1, y + clear_h)


def post_lamp(g, x, z, y0, post, lamp='lantern', h=3, top=None):
    for y in range(y0, y0 + h):
        g.set(x, y, z, post)
    if top:
        g.set(x, y0 + h, z, top)
        g.set(x, y0 + h + 1, z, lantern(lamp))
    else:
        g.set(x, y0 + h, z, lantern(lamp))


def toro(g, x, z, y0=1, stone='stone_bricks', lamp='lantern'):
    """A stone lantern: a base, a post, a lamp box under a little roof."""
    g.set(x, y0, z, stone)
    g.set(x, y0 + 1, z, 'stone_brick_wall')
    g.set(x, y0 + 2, z, stone)
    g.set(x, y0 + 3, z, lantern(lamp))
    g.set(x, y0 + 4, z, slab('stone_brick_slab'))


def halo(g, cx, cy, cz, r, st, tilt=0.0, axis='x', thick=0.6):
    n = int(r * 8) + 8
    for i in range(n):
        a = i / n * 2 * math.pi
        dx, dz = math.cos(a) * r, math.sin(a) * r
        if axis == 'x':
            y = cy + dz * math.sin(tilt)
            dz = dz * math.cos(tilt)
        else:
            y = cy + dx * math.sin(tilt)
            dx = dx * math.cos(tilt)
        g.ball(cx + dx, y, cz + dz, thick, st)


def vring(g, cx, cy, cz, r, st, axis='x', thick=0.6, spokes=0, hub=None, spoke=None):
    """A ring standing upright, in the x-y plane (axis 'x') or the z-y plane."""
    n = int(r * 8) + 8
    for i in range(n):
        a = i / n * 2 * math.pi
        u, v = math.cos(a) * r, math.sin(a) * r
        if axis == 'x':
            g.ball(cx + u, cy + v, cz, thick, st)
        else:
            g.ball(cx, cy + v, cz + u, thick, st)
    for k in range(spokes):
        a = k / spokes * 2 * math.pi
        u, v = math.cos(a) * r, math.sin(a) * r
        p1 = (cx + u, cy + v, cz) if axis == 'x' else (cx, cy + v, cz + u)
        g.line((cx, cy, cz), p1, spoke or st)
    if hub:
        g.ball(cx, cy, cz, 1.2, hub)


# ---------------------------------------------------------------- 1
def kokuhaku(g):
    """剣神 炬珀 (quiet; white hair, pale blue; horns, tail, a sword): 「白銀の剣界」. A silent white field of raked stone,
    ripples round a duelling square, a wood of great swords standing in the ground, slash-lines of pale light hanging in
    the air (her legend: 'slashes reserved in the silver sword-world'), a quiet sheath-hall to the north."""
    g.floor_block = 'minecraft:smooth_quartz'
    plaza(g, 25, lambda x, z, d: 'polished_diorite' if int(d) % 3 == 0 else 'calcite', rimstair='smooth_quartz_stairs')
    g.box(C - 6, 0, C - 6, C + 6, 0, C + 6, 'smooth_quartz')
    g.box(C - 7, 0, C - 7, C + 7, 0, C + 7, 'light_blue_concrete', hollow=True)
    g.box(C - 7, 0, C - 7, C + 7, 0, C + 7, 'light_blue_concrete', hollow=True)
    for k in range(-6, 7):
        g.set(C + k, 0, C - 7, 'light_blue_concrete'); g.set(C + k, 0, C + 7, 'light_blue_concrete')
        g.set(C - 7, 0, C + k, 'light_blue_concrete'); g.set(C + 7, 0, C + k, 'light_blue_concrete')
    # the swords
    for i, (a, r, ln) in enumerate(((0.3, 17, 13), (0.9, 20, 9), (1.4, 15, 16), (2.2, 19, 11), (2.7, 22, 8), (3.5, 17, 14),
                                   (4.0, 21, 10), (5.2, 16, 15), (5.8, 20, 12), (4.6, 23, 8))):
        x, z = C + math.cos(a) * r, C + math.sin(a) * r
        if z < C - 14 and abs(x - C) < 10:
            continue
        g.sword(round(x), round(z), 0, ln, blade='quartz_block', edge='light_blue_stained_glass', guard='gold_block',
                grip='white_wool', pommel='light_blue_concrete', axis='x' if i % 2 else 'z', tilt=((i % 3) - 1, (i % 2) * 2 - 1))
    # slash-lines in the air
    for (p0, p1) in (((4, 19, 12), (50, 25, 40)), ((10, 26, 46), (46, 21, 6)), ((2, 23, 30), (52, 29, 22))):
        g.line(p0, p1, 'light_blue_stained_glass')
    # the sheath-hall: a long low hall, white walls, dark posts, tiled roof
    x0, x1, z0, z1 = C - 9, C + 9, 2, 8
    g.box(x0, 1, z0, x1, 5, z1, 'white_concrete', hollow=True)
    g.box(x0 + 1, 1, z0 + 1, x1 - 1, 5, z1 - 1, AIR)
    g.box(x0, 0, z0, x1, 0, z1, 'stripped_birch_wood')
    for x in range(x0, x1 + 1, 3):
        for z in (z0, z1):
            g.column(x, z, 1, 5, 'stripped_dark_oak_log[axis=y]')
    for x in range(x0 + 2, x1 - 1, 3):
        g.set(x, 3, z1, 'white_stained_glass_pane')
    for x in (C - 1, C, C + 1):
        for y in (1, 2, 3):
            g.set(x, y, z1, AIR)
    g.roof_hip(x0, z0, x1, z1, 6, 'deepslate_tile_stairs', 'deepslate_tiles', flare=1)
    for x in range(x0 + 2, x1 - 1, 4):
        g.set(x, 5, (z0 + z1) // 2, lantern(hanging=True))
    # the gate: a pale torii on the way in
    g.torii(C, W - 4, 1, 9, 8, axis='x', post='calcite', beam='light_blue_concrete')
    for (x, z) in ((C - 4, C + 12), (C + 4, C + 12), (C - 12, C - 4), (C + 12, C - 4), (C - 12, C + 4), (C + 12, C + 4)):
        toro(g, x, z, 1, stone='calcite')


# ---------------------------------------------------------------- 2
def riha(g):
    """天冠詠者 理覇 (playful; white and gold; a halo; words of power 'stop', 'heal', 'fall'): 「天冠の詠唱座」. A round
    amphitheatre of white stone for her recital, a golden halo hung over the stage and two smaller ones tilted about it,
    lecterns at the stage's edge, and behind it her legend's 'castle of light': slender spires of glass with gilded tips."""
    g.floor_block = 'minecraft:smooth_quartz'
    plaza(g, 25, 'calcite', clear_h=20)
    g.disc(C, C, 10, 0, None, pattern=lambda x, z, d: 'gold_block' if abs(d - 6) < 0.5 or (abs(x - C) == abs(z - C) and d < 6) else 'smooth_quartz')
    # tiers of seats rising outward, open to the south
    for k, r in enumerate(range(13, 24, 2)):
        y = k + 1
        for x in range(C - r - 1, C + r + 2):
            for z in range(C - r - 1, C + r + 2):
                d = math.hypot(x - C, z - C)
                if r - 0.5 <= d <= r + 1.6 and not (z > C and abs(x - C) < 5):
                    for yy in range(1, y):
                        g.set(x, yy, z, 'calcite')
                    g.set(x, y, z, stair('quartz_stairs', outward(x - C, z - C)) if d < r + 0.6 else 'quartz_bricks')
    halo(g, C, 24, C, 9, 'gold_block')
    halo(g, C, 24, C, 7, 'yellow_stained_glass', tilt=0.5, axis='x', thick=0.4)
    halo(g, C, 24, C, 7, 'yellow_stained_glass', tilt=0.5, axis='z', thick=0.4)
    for (x, z) in ((C - 8, C + 5), (C + 8, C + 5), (C - 9, C - 3), (C + 9, C - 3)):
        g.set(x, 1, z, 'lectern[facing=north,has_book=false,powered=false]')
        g.set(x, 0, z, 'gold_block')
    # the castle of light
    for (dx, h, r) in ((-14, 30, 2), (-7, 38, 2), (0, 46, 3), (7, 38, 2), (14, 30, 2)):
        x, z = C + dx, 4 + abs(dx) // 3
        g.cyl(x, z, r, 1, h, 'white_stained_glass', hollow=True, inner=None)
        g.cyl(x, z, r, 0, 1, 'quartz_bricks')
        for y in range(4, h, 6):
            g.ring(x, z, r - 0.5, r, y, 'gold_block')
        g.cone(x, h + 1, z, r, 5, 'gold_block', edge='end_rod')
        g.set(x, 2, z, 'sea_lantern')


# ---------------------------------------------------------------- 3
def tenki(g):
    """唯我万象 天輝 (proud; cream and gold; a crown; 'kneel'): 「王権の玉座殿」. A terrace raised over the world, reached by
    a grand stair between colonnades, a carpet to the seal before a towering golden throne crowned with a crown, and a
    ring of crown-points round the terrace."""
    g.floor_block = 'minecraft:gold_block'
    plaza(g, 25, 'smooth_sandstone', clear_h=24)
    g.seal_y = 7
    g.box(C - 14, 1, C - 16, C + 14, 6, C + 12, 'quartz_bricks')
    g.box(C - 14, 6, C - 16, C + 14, 6, C + 12, 'smooth_quartz')
    for x in range(C - 14, C + 15):
        for z in range(C - 16, C + 13):
            if (x + z) % 2 == 0 and abs(x - C) < 12 and C - 14 < z < C + 11:
                g.set(x, 6, z, 'yellow_terracotta' if abs(x - C) > 1 else 'gold_block')
    g.stairs_up(C, C + 18, 1, 6, 'quartz_stairs', 'north', width=7, fill='quartz_bricks')
    for z in range(C + 12, C + 19):
        for x in range(C - 4, C + 5):
            if g.get(x, 0, z) is None:
                g.set(x, 0, z, 'smooth_quartz')
    for z in range(C - 4, C + 13):
        g.set(C, 7, z, 'yellow_carpet') if abs(z - C) > 1 else None
    for side in (-1, 1):
        for z in range(C + 13, W - 2, 4):
            g.column(C + side * 6, z, 1, 9, 'quartz_pillar[axis=y]', base='chiseled_quartz_block', cap='gold_block')
        for z in range(C - 14, C + 12, 5):
            g.column(C + side * 12, z, 7, 15, 'quartz_pillar[axis=y]', base='chiseled_quartz_block', cap='gold_block')
            g.set(C + side * 12, 16, z, lantern())
    # the throne
    tz = C - 12
    g.box(C - 5, 7, tz - 2, C + 5, 9, tz + 1, 'gold_block')
    g.box(C - 3, 10, tz - 2, C + 3, 25, tz - 1, 'gold_block')
    g.box(C - 2, 10, tz, C + 2, 10, tz + 1, 'red_wool')
    g.box(C - 2, 11, tz - 1, C + 2, 22, tz - 1, 'red_wool')
    for x in (C - 4, C + 4):
        g.box(x, 10, tz - 2, x, 13, tz + 1, 'gold_block')
    g.ring(C, tz - 2, 3.5, 4.5, 26, 'gold_block')
    for k in range(5):
        a = k / 5 * math.pi
        g.set(C + round(math.cos(a) * 4), 27, tz - 2, 'gold_block')
        g.set(C + round(math.cos(a) * 4), 28, tz - 2, 'yellow_stained_glass')
    # crown points round the terrace
    for k in range(10):
        a = k / 10 * 2 * math.pi
        x, z = C + math.cos(a) * 18, C - 2 + math.sin(a) * 16
        if z > C + 10:
            continue
        g.column(round(x), round(z), 1, 18 + (k % 2) * 4, 'quartz_block', cap='gold_block')
        g.set(round(x), 19 + (k % 2) * 4 + 0, round(z), 'gold_block')
        g.set(round(x), 20 + (k % 2) * 4, round(z), 'end_rod')


# ---------------------------------------------------------------- 4
def chaos(g):
    """万象混沌 カオス (a hazard; violet and cyan; a core, eyes, tentacles; random change): 「虹核の原胎」. A crater floor
    of every stone mixed, tentacles rising from the ground and curling in over the field, crystal spikes, and over all a
    great rainbow core with an eye, the womb of her legend that tears open."""
    mix = ['crying_obsidian', 'purpur_block', 'warped_wart_block', 'prismarine', 'obsidian', 'amethyst_block', 'black_concrete',
           'magenta_terracotta', 'cyan_terracotta', 'purple_concrete']
    g.floor_block = 'minecraft:obsidian'
    plaza(g, 25, lambda x, z, d: mix[(x * 7 + z * 13 + (x * z) % 5) % len(mix)], clear_h=20)
    for k in range(9):
        a = k / 9 * 2 * math.pi + 0.2
        x0, z0 = C + math.cos(a) * 21, C + math.sin(a) * 21
        x1, z1 = C + math.cos(a + 0.6) * 15, C + math.sin(a + 0.6) * 15
        x2, z2 = C + math.cos(a + 1.1) * 9, C + math.sin(a + 1.1) * 9
        mat = 'purple_concrete' if k % 2 else 'crimson_hyphae[axis=y]'
        g.curve([(x0, 0, z0), (x0, 14, z0), (x1, 24, z1), (x2, 21, z2)], mat, r0=2.0, r1=0.4)
        g.curve([(x0, 1, z0), (x0, 10, z0)], 'magenta_concrete', r0=0.5, r1=0.5)
    # the core and its eye
    g.sphere(C, 25, C, 5, 'cyan_stained_glass', shell=1.0)
    g.sphere(C, 25, C, 3.5, 'sea_lantern')
    g.sphere(C, 25, C, 2.2, 'crying_obsidian')
    for x in range(C - 2, C + 3):
        g.set(x, 25, C + 5, 'black_concrete')
    g.set(C, 25, C + 5, 'white_concrete')
    for k in range(14):
        a = k * 2.4
        x, z = C + math.cos(a) * (10 + k % 5 * 2.5), C + math.sin(a) * (10 + k % 5 * 2.5)
        h = 3 + (k * 5) % 6
        g.line((x, 0, z), (x + math.cos(a), h, z + math.sin(a)), 'amethyst_block' if k % 2 else 'purple_stained_glass', r=0.8)


# ---------------------------------------------------------------- 5
def berit(g):
    """万界錬成 ベーリット (a researcher; grey hair, white coat, gold; transmutation of the ground, binding chains): 「錬成工房」.
    The seal in a transmutation circle inlaid in gold, a half-ring of workshops with chimneys, crucibles boiling, glass
    alembics on copper stands, gold crystals grown out of the ground, and overhead her legend's 'new matter' falling."""
    g.floor_block = 'minecraft:polished_blackstone'

    def floor(x, z, d):
        a = math.atan2(z - C, x - C)
        if abs(d - 6) < 0.6 or abs(d - 10) < 0.6:
            return 'gold_block'
        if d < 10:
            # a hexagram
            for k in range(6):
                b = k / 6 * 2 * math.pi
                p0 = (math.cos(b) * 10, math.sin(b) * 10)
                p1 = (math.cos(b + 2 * math.pi / 3) * 10, math.sin(b + 2 * math.pi / 3) * 10)
                px, pz = x - C, z - C
                lx, lz = p1[0] - p0[0], p1[1] - p0[1]
                t = ((px - p0[0]) * lx + (pz - p0[1]) * lz) / (lx * lx + lz * lz)
                if 0 <= t <= 1 and math.hypot(p0[0] + lx * t - px, p0[1] + lz * t - pz) < 0.6:
                    return 'raw_gold_block'
            return 'polished_blackstone'
        return 'deepslate_tiles' if (x + z) % 2 else 'polished_deepslate'
    plaza(g, 25, floor, rimstair='polished_deepslate_stairs')
    # the workshops, a half ring to the north
    for x in range(C - 25, C + 26):
        for z in range(C - 25, C + 1):
            d = math.hypot(x - C, z - C)
            if 17 <= d <= 24:
                edge = d < 17.8 or d > 23.2
                for y in range(1, 8):
                    g.set(x, y, z, 'deepslate_bricks' if edge else AIR)
                g.set(x, 0, z, 'polished_deepslate')
                g.set(x, 8, z, 'waxed_cut_copper')
                if edge and d < 17.8 and int(math.degrees(math.atan2(z - C, x - C))) % 15 == 0:
                    for y in (1, 2, 3):
                        g.set(x, y, z, AIR)
                if edge and d < 17.8 and int(math.degrees(math.atan2(z - C, x - C))) % 15 == 7:
                    g.set(x, 4, z, 'orange_stained_glass_pane')
                    g.set(x, 5, z, 'orange_stained_glass_pane')
    for a in (200, 240, 270, 300, 340):
        x, z = C + math.cos(math.radians(a)) * 21, C + math.sin(math.radians(a)) * 21
        g.cyl(round(x), round(z), 1, 9, 16, 'bricks')
        g.set(round(x), 17, round(z), 'campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]')
        g.set(round(x), 7, round(z), 'blast_furnace[facing=south,lit=true]')
    # crucibles and alembics in the court
    for (x, z, kind) in ((C - 13, C + 6, 'lava_cauldron'), (C + 13, C + 6, 'water_cauldron[level=3]'),
                         (C - 9, C + 14, 'lava_cauldron'), (C + 9, C + 14, 'water_cauldron[level=3]')):
        g.box(x - 1, 1, z - 1, x + 1, 1, z + 1, 'bricks')
        g.set(x, 2, z, kind)
        g.set(x, 1, z, 'magma_block')
    for (x, z) in ((C - 18, C + 12), (C + 18, C + 12)):
        g.column(x, z, 1, 4, 'waxed_copper_block')
        g.sphere(x, 7, z, 2.5, 'white_stained_glass', shell=0.8)
        g.set(x, 6, z, 'shroomlight')
        g.line((x, 8, z), (x + (3 if x < C else -3), 3, z + 4), 'waxed_copper_grate')
    for k in range(10):
        a = k * 2.1 + 0.4
        r = 12 + (k % 3) * 3
        x, z = C + math.cos(a) * r, C + 4 + math.sin(a) * r * 0.5
        if z < C:
            continue
        g.line((x, 0, z), (x + math.cos(a), 3 + k % 4, z), 'gold_block' if k % 2 else 'raw_gold_block', r=0.9)
    # the new matter hung over the circle
    for x in range(C - 4, C + 5):
        for y in range(26, 35):
            for z in range(C - 4, C + 5):
                if abs(x - C) + abs(y - 30) + abs(z - C) <= 6:
                    g.set(x, y, z, 'raw_gold_block' if (x + y + z) % 3 else 'waxed_copper_block')
    for (x, z) in ((C - 6, C - 6), (C + 6, C - 6), (C - 6, C + 6), (C + 6, C + 6)):
        g.box(x, 1, z, x, 1, z, 'polished_blackstone_bricks')
        g.column(x, z, 1, 3, 'polished_blackstone_bricks', cap='gold_block')


# ---------------------------------------------------------------- 6
def elseria(g):
    """星脈魔祖 エルセリア (a guardian; pale blue; elf ears, a staff; the seven-sun star bullets): 「星辰の天文台」. A white
    platform whose floor is a star map, seven pillars bearing the seven suns of her legend, a great armillary sphere of
    gold rings turning over the seal, and an observatory tower with its copper dome to the north."""
    g.floor_block = 'minecraft:calcite'
    stars = {}

    def floor(x, z, d):
        if d > 22:
            return 'calcite'
        h = (x * 73856093 ^ z * 19349663) % 23
        if h == 0:
            return 'sea_lantern'
        if abs(d - 14) < 0.5:
            return 'light_blue_concrete'
        return 'black_concrete' if (x + z) % 2 else 'blue_concrete'
    plaza(g, 25, floor, rim='calcite', rimstair='diorite_stairs', clear_h=24)
    suns = ['gold_block', 'white_stained_glass', 'red_stained_glass', 'cyan_stained_glass', 'purple_stained_glass', 'yellow_stained_glass',
            'orange_stained_glass']
    for k in range(7):
        a = math.radians(-90 + 40 + k * (360 - 80) / 6)
        x, z = round(C + math.cos(a) * 19), round(C + math.sin(a) * 19)
        h = 10 + (k % 3) * 2
        g.column(x, z, 1, h, 'quartz_pillar[axis=y]', base='chiseled_quartz_block', cap='chiseled_quartz_block')
        g.sphere(x, h + 3, z, 2, suns[k])
        g.set(x, h + 3, z, 'sea_lantern' if k else 'shroomlight')
    # the armillary sphere
    halo(g, C, 26, C, 9, 'gold_block', thick=0.5)
    halo(g, C, 26, C, 9, 'gold_block', tilt=math.pi / 2, axis='x', thick=0.5)
    halo(g, C, 26, C, 9, 'gold_block', tilt=math.pi / 2, axis='z', thick=0.5)
    halo(g, C, 26, C, 8, 'light_blue_stained_glass', tilt=0.4, axis='x', thick=0.4)
    g.sphere(C, 26, C, 1.5, 'sea_lantern')
    # the observatory tower
    tx, tz = C, 4
    g.cyl(tx, tz, 5, 0, 22, 'calcite', hollow=True, inner=None)
    g.box(tx - 4, 1, tz - 4, tx + 4, 21, tz + 4, AIR, only_empty=False)
    g.cyl(tx, tz, 5, 0, 22, 'calcite', hollow=True)
    for y in range(4, 22, 6):
        g.disc(tx, tz, 4, y, 'birch_planks')
        g.set(tx + 2, y, tz, AIR)
    for y in range(1, 23):
        g.set(tx + 2, y, tz + 3, 'ladder[facing=north,waterlogged=false]')
    g.ring(tx, tz, 4.5, 5, 22, 'light_blue_concrete')
    g.dome(tx, 23, tz, 5, 'waxed_oxidized_cut_copper')
    for y in range(23, 29):
        g.set(tx, y, tz + 4, AIR); g.set(tx, y, tz + 5, AIR)
    for y in (2, 3):
        g.set(tx, y, tz + 5, AIR)


# ---------------------------------------------------------------- 7
def valeria(g):
    """万機創匠 ヴァレリア (a craftswoman; dark hair, brown coat, amber; a transforming hammer, work drones): 「万機工房」.
    A works yard striped with hazard yellow, a steel hangar with a copper vault, a gantry crane over the seal with its hook,
    anvils and forges, drones hanging in the air, and her legend's 'Zero-type god-machine' kneeling by the gate."""
    g.floor_block = 'minecraft:polished_deepslate'

    def floor(x, z, d):
        if d > 23:
            return 'yellow_concrete' if (x + z) // 2 % 2 else 'black_concrete'
        return 'polished_deepslate' if (x // 4 + z // 4) % 2 else 'deepslate_tiles'
    plaza(g, 25, floor, clear_h=22)
    # the hangar, north
    for x in range(C - 14, C + 15):
        for z in range(2, 13):
            g.set(x, 0, z, 'waxed_cut_copper')
    for x in range(C - 14, C + 15, 4):
        g.box(x, 1, 2, x, 12, 2, 'iron_block')
        g.box(x, 1, 12, x, 12, 12, 'iron_block')
        g.arch(2, 12, x, 12, 6, 'waxed_cut_copper', axis='z')
    for x in range(C - 14, C + 15):
        g.arch(2, 12, x, 13, 5, 'waxed_cut_copper', axis='z')
        g.box(x, 1, 1, x, 12, 1, 'deepslate_bricks')
    # the gantry crane
    for (x, z) in ((C - 13, C - 10), (C + 13, C - 10), (C - 13, C + 12), (C + 13, C + 12)):
        g.column(x, z, 1, 17, 'iron_block', base='black_concrete')
    for z in (C - 10, C + 12):
        g.box(C - 13, 18, z, C + 13, 18, z, 'iron_block')
    for x in range(C - 13, C + 14):
        g.set(x, 19, C + 1, 'yellow_concrete')
    for z in range(C - 10, C + 13):
        g.set(C, 18, z, 'yellow_concrete')
    for y in range(15, 19):
        g.set(C + 7, y, C + 1, 'chain[axis=y]')
    g.set(C + 7, 14, C + 1, 'iron_block')
    # forges and anvils
    for (x, z) in ((C - 18, C + 6), (C + 18, C + 6), (C - 18, C - 4), (C + 18, C - 4)):
        g.box(x - 1, 1, z - 1, x + 1, 2, z + 1, 'bricks')
        g.set(x, 2, z, 'lava_cauldron')
        g.set(x + 2, 1, z, 'anvil[facing=north]')
        g.set(x, 1, z + 2, 'smithing_table')
    # drones
    for k in range(6):
        a = k * 1.05
        x, z, y = C + math.cos(a) * 16, C + math.sin(a) * 16, 15 + k % 3 * 3
        g.box(round(x) - 1, y, round(z) - 1, round(x) + 1, y, round(z) + 1, 'iron_block')
        g.set(round(x), y - 1, round(z), 'sea_lantern')
        for (dx, dz) in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            g.set(round(x) + dx, y, round(z) + dz, 'iron_trapdoor[facing=north,half=bottom,open=false,powered=false,waterlogged=false]')
    # the god-machine, kneeling, south-west
    mx, mz = C - 16, C + 17
    g.box(mx - 2, 1, mz - 1, mx + 2, 4, mz + 2, 'iron_block')             # knee and leg
    g.box(mx - 3, 5, mz - 3, mx + 3, 12, mz + 2, 'waxed_copper_block')     # torso
    g.box(mx - 2, 7, mz + 3, mx + 2, 10, mz + 3, 'black_concrete')
    g.set(mx, 9, mz + 3, 'sea_lantern')
    g.box(mx - 2, 13, mz - 2, mx + 2, 16, mz + 1, 'iron_block')           # head
    g.set(mx - 1, 15, mz + 2, 'ochre_froglight'); g.set(mx + 1, 15, mz + 2, 'ochre_froglight')
    g.line((mx - 4, 11, mz), (mx - 6, 2, mz + 3), 'iron_block', r=1.0)    # arms
    g.line((mx + 4, 11, mz), (mx + 6, 2, mz + 3), 'iron_block', r=1.0)
    g.box(mx + 5, 1, mz + 2, mx + 8, 3, mz + 5, 'waxed_cut_copper')        # the hammer's head
    g.line((mx + 6, 3, mz + 3), (mx + 6, 9, mz + 3), 'dark_oak_log[axis=y]')


# ---------------------------------------------------------------- 8
def huang_linghua(g):
    """黄天龍仙 皇玲華 (reserved; white hair, deep teal, gold; dragon horns and tail, a spear; thunder dragons): 「黄天龍宮」.
    A marble terrace with white balustrades, a two-storey palace hall roofed in teal with golden ridge-ends, two great
    columns with golden thunder-dragons coiled up them at the moon gate, a lotus pond, lightning rods on every peak."""
    g.floor_block = 'minecraft:smooth_quartz'
    plaza(g, 25, lambda x, z, d: 'smooth_quartz' if (x + z) % 4 else 'polished_diorite', rimstair='quartz_stairs', clear_h=24)
    g.ring(C, C, 22, 22.5, 1, 'diorite_wall')
    # the hall, north
    x0, x1, z0, z1 = C - 12, C + 12, 2, 11
    g.box(x0 - 1, 0, z0 - 1, x1 + 1, 1, z1 + 1, 'quartz_bricks')
    g.box(x0, 2, z0, x1, 8, z1, 'white_terracotta', hollow=True)
    g.box(x0 + 1, 2, z0 + 1, x1 - 1, 8, z1 - 1, AIR)
    for x in range(x0, x1 + 1, 3):
        g.column(x, z1 + 1, 2, 8, 'red_concrete', base='gold_block')
        g.set(x, 5, z1, 'white_stained_glass_pane')
    for x in (C - 1, C, C + 1):
        for y in (2, 3, 4):
            g.set(x, y, z1, AIR)
    g.pagoda(C, (z0 + z1) // 2, 9, 12, 2, 'white_terracotta', 'waxed_oxidized_cut_copper_stairs', 'waxed_oxidized_cut_copper',
             'red_concrete', glass='white_stained_glass_pane', h=4)
    g.stairs_up(C, z1 + 4, 0, 2, 'quartz_stairs', 'north', width=5, fill='quartz_bricks')
    # the dragon columns at the moon gate, south
    for side in (-1, 1):
        cx, cz = C + side * 7, W - 7
        g.cyl(cx, cz, 1, 1, 20, 'red_concrete')
        g.set(cx, 21, cz, 'gold_block')
        pts = []
        for i in range(0, 120):
            t = i / 6.0
            pts.append((cx + math.cos(t * side) * 2.3, 1 + i * 0.17, cz + math.sin(t * side) * 2.3))
        for p in pts:
            g.ball(*p, 0.8, 'gold_block')
        g.ball(*pts[-1], 1.3, 'gold_block')
        g.set(round(pts[-1][0]), round(pts[-1][1]) + 2, round(pts[-1][2]), 'lightning_rod[facing=up,powered=false,waterlogged=false]')
        g.set(round(pts[-1][0]) + side, round(pts[-1][1]), round(pts[-1][2]), 'ochre_froglight')
    # the moon gate: a round opening in a white wall
    for x in range(C - 6, C + 7):
        for y in range(1, 13):
            if math.hypot(x - C, y - 6) > 5:
                g.set(x, y, W - 5, 'white_terracotta')
            else:
                g.set(x, y, W - 5, AIR)
    for x in range(C - 7, C + 8):
        g.set(x, 13, W - 5, stair('waxed_oxidized_cut_copper_stairs', 'south'))
    # the lotus ponds
    for side in (-1, 1):
        cx, cz = C + side * 15, C + 9
        g.disc(cx, cz, 5, 0, 'water')
        g.ring(cx, cz, 5, 6, 0, 'quartz_bricks')
        g.ring(cx, cz, 5.5, 6, 1, 'diorite_wall')
        for k in range(5):
            a = k * 1.3
            g.set(round(cx + math.cos(a) * 3), 1, round(cz + math.sin(a) * 3), 'lily_pad')


# ---------------------------------------------------------------- 9
def ferdinand(g):
    """文明遊匠 フェルディナント (a craftsman; grey, monocle; prototype guns, steam batteries, a city's supply lines): 「試作工廠」.
    A brick factory yard: a clock tower with a great dial, smokestacks breathing smoke, a rail line round the yard,
    copper pipes, steam cannons on turntables at the corners, and a glass-roofed test hall."""
    g.floor_block = 'minecraft:bricks'
    plaza(g, 25, lambda x, z, d: 'bricks' if (x // 3 + z // 3) % 2 else 'polished_andesite', clear_h=22)
    # the rail ring
    for x in range(C - 23, C + 24):
        for z in range(C - 23, C + 24):
            d = math.hypot(x - C, z - C)
            if 20.5 <= d < 21.5:
                g.set(x, 0, z, 'gravel' if False else 'polished_andesite')
                g.set(x, 1, z, 'rail[shape=north_south,waterlogged=false]' if abs(x - C) < abs(z - C) else 'rail[shape=east_west,waterlogged=false]')
    # the clock tower, north
    tx, tz = C, 5
    g.box(tx - 4, 0, tz - 3, tx + 4, 30, tz + 3, 'bricks', hollow=True)
    g.box(tx - 3, 1, tz - 2, tx + 3, 29, tz + 2, AIR)
    for y in range(6, 30, 6):
        g.box(tx - 4, y, tz - 3, tx + 4, y, tz + 3, 'polished_andesite', hollow=True)
    g.disc_v = None
    for x in range(tx - 4, tx + 5):
        for y in range(19, 28):
            d = math.hypot(x - tx, y - 23)
            if d <= 3.6:
                g.set(x, y, tz + 4, 'white_concrete' if d < 3.2 else 'gold_block')
    g.line((tx, 23, tz + 5), (tx, 26, tz + 5), 'black_concrete')
    g.line((tx, 23, tz + 5), (tx + 2, 22, tz + 5), 'black_concrete')
    g.roof_hip(tx - 4, tz - 3, tx + 4, tz + 3, 31, 'deepslate_tile_stairs', 'deepslate_tiles', flare=1, cap='lightning_rod[facing=up,powered=false,waterlogged=false]')
    for y in (1, 2, 3):
        g.set(tx, y, tz + 3, AIR)
    # factory sheds east and west with smokestacks
    for side in (-1, 1):
        x0 = C + side * 12
        x1 = C + side * 22
        g.box(min(x0, x1), 0, C - 14, max(x0, x1), 8, C - 2, 'bricks', hollow=True)
        g.box(min(x0, x1) + 1, 1, C - 13, max(x0, x1) - 1, 7, C - 3, AIR)
        for z in range(C - 13, C - 2, 3):
            g.set(x0, 4, z, 'glass_pane'); g.set(x0, 5, z, 'glass_pane')
        for y in (1, 2, 3):
            g.set(x0, y, C - 8, AIR); g.set(x0, y, C - 7, AIR)
        g.roof_hip(min(x0, x1), C - 14, max(x0, x1), C - 2, 9, 'waxed_cut_copper_stairs', 'waxed_cut_copper', flare=0)
        sx = C + side * 18
        g.cyl(sx, C - 16, 1, 1, 22, 'bricks')
        g.set(sx, 23, C - 16, 'campfire[facing=north,lit=true,signal_fire=true,waterlogged=false]')
        g.set(sx, 22, C - 16, 'hay_block')
        g.line((x0, 7, C - 2), (C + side * 6, 3, C + 6), 'waxed_copper_grate')
    # steam cannons
    for (x, z) in ((C - 17, C + 14), (C + 17, C + 14)):
        g.disc(x, z, 2.5, 1, 'waxed_cut_copper')
        g.box(x - 1, 2, z - 1, x + 1, 3, z + 1, 'iron_block')
        g.line((x, 3, z), (x + (5 if x < C else -5), 6, z - 4), 'black_concrete', r=0.9)
        g.set(x, 4, z, 'campfire[facing=north,lit=true,signal_fire=false,waterlogged=false]')


# ---------------------------------------------------------------- 10
def mels(g):
    """至高武王 メルス (quiet; a clear slime; liquid martial arts): 「流水の武闘場」. A square fighting ring raised out of a
    still pool, its ropes on gilded posts, pillars of clear water-glass curling up like his water-blades, a bamboo dojo
    gallery to the north, stepping stones across the water."""
    g.floor_block = 'minecraft:light_blue_concrete'
    plaza(g, 25, 'prismarine_bricks', clear_h=20)
    g.disc(C, C, 22, 1, 'water')
    g.ring(C, C, 22, 25, 1, 'prismarine_bricks')
    g.ring(C, C, 24.5, 25, 2, 'prismarine_wall')
    g.seal_y = 3
    g.box(C - 10, 1, C - 10, C + 10, 2, C + 10, 'quartz_bricks')
    g.box(C - 9, 2, C - 9, C + 9, 2, C + 9, 'light_blue_concrete')
    g.box(C - 8, 2, C - 8, C + 8, 2, C + 8, 'white_concrete')
    for (x, z) in ((C - 10, C - 10), (C + 10, C - 10), (C - 10, C + 10), (C + 10, C + 10)):
        g.column(x, z, 3, 6, 'gold_block')
    for k in range(-9, 10):
        for y in (4, 5):
            for (x, z) in ((C + k, C - 10), (C + k, C + 10), (C - 10, C + k), (C + 10, C + k)):
                if abs(k) < 2 and z == C + 10:
                    continue
                g.set(x, y, z, 'white_wool' if False else 'light_blue_stained_glass_pane')
    for z in range(C + 11, W - 1, 2):
        g.set(C, 1, z, 'quartz_bricks')
        g.set(C, 2, z, 'smooth_quartz_slab[type=bottom,waterlogged=false]')
    # the water-blades
    for k in range(6):
        a = k / 6 * 2 * math.pi + 0.5
        x, z = C + math.cos(a) * 17, C + math.sin(a) * 17
        g.curve([(x, 1, z), (x, 12, z), (x + math.cos(a + 1.6) * 6, 20, z + math.sin(a + 1.6) * 6),
                 (C + math.cos(a + 0.8) * 13, 16, C + math.sin(a + 0.8) * 13)], 'light_blue_stained_glass', r0=1.4, r1=0.3)
        g.set(round(x), 0, round(z), 'sea_lantern')
    # the gallery
    for x in range(C - 12, C + 13):
        for z in range(1, 6):
            g.set(x, 1, z, 'bamboo_mosaic')
        g.set(x, 2, 1, 'bamboo_fence')
    for x in range(C - 12, C + 13, 4):
        g.column(x, 5, 2, 6, 'stripped_bamboo_block[axis=y]')
        g.column(x, 1, 2, 6, 'stripped_bamboo_block[axis=y]')
    g.roof_hip(C - 12, 1, C + 12, 5, 7, 'bamboo_mosaic_stairs', 'bamboo_mosaic', flare=1)


# ---------------------------------------------------------------- 11
def hephaistos(g):
    """典域工廠 ヘファイストス (a machine; slate and teal; a factory sphere with rings in orbit, drones): 「環状工廠」, deep
    underground. A cavern holding a ring-factory round the floor, the great core hung in the air with three rings orbiting
    it, cubes on the factory's belts, teal light in the floor."""
    g.floor_block = 'minecraft:deepslate_tiles'
    g.cavern = (27, 36)
    plaza(g, 26, lambda x, z, d: 'cyan_terracotta' if int(d) % 6 == 0 else ('deepslate_tiles' if (x + z) % 2 else 'polished_deepslate'), clear_h=1)
    for x in range(1, W - 1):
        for z in range(1, W - 1):
            d = math.hypot(x - C, z - C)
            if 17 <= d <= 23:
                edge = d < 17.8 or d > 22.3
                for y in range(1, 9):
                    g.set(x, y, z, 'deepslate_bricks' if edge else AIR)
                g.set(x, 9, z, 'waxed_weathered_cut_copper')
                if edge and d < 17.8:
                    ang = int(math.degrees(math.atan2(z - C, x - C))) % 30
                    if ang < 3:
                        for y in (1, 2, 3):
                            g.set(x, y, z, AIR)
                    elif ang in (14, 15):
                        g.set(x, 5, z, 'cyan_stained_glass_pane')
                if 19 <= d <= 21:
                    g.set(x, 1, z, 'waxed_copper_grate')
                    if int(math.degrees(math.atan2(z - C, x - C))) % 20 == 0:
                        g.set(x, 2, z, 'iron_block' if d < 20 else 'obsidian')
    g.sphere(C, 24, C, 4.5, 'cyan_stained_glass', shell=1.0)
    g.sphere(C, 24, C, 3.3, 'sea_lantern')
    halo(g, C, 24, C, 8, 'iron_block', thick=0.5)
    halo(g, C, 24, C, 10, 'waxed_copper_block', tilt=0.6, axis='x', thick=0.5)
    halo(g, C, 24, C, 12, 'iron_block', tilt=-0.7, axis='z', thick=0.5)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        g.box(round(C + math.cos(a) * 10), 30 + k % 2 * 2, round(C + math.sin(a) * 10),
              round(C + math.cos(a) * 10) + 1, 31 + k % 2 * 2, round(C + math.sin(a) * 10) + 1, 'iron_block')
    for k in range(6):
        a = k / 6 * 2 * math.pi
        g.line((C + math.cos(a) * 24, 1, C + math.sin(a) * 24), (C + math.cos(a) * 14, 30, C + math.sin(a) * 14), 'polished_deepslate', r=1.2)


# ---------------------------------------------------------------- 12
def nortia(g):
    """無法遊戯 ノルティア (playful, small; pastel violet and gold; a squeaky hammer, dice, 'red light', tag): 「無法の遊園地」.
    The stage is a giant board game in pastel squares, with a carousel, a slide tower, a stack of toy blocks, a giant
    die, balloons on strings, the giant squeaky hammer, and a traffic light standing at red."""
    cols = ['pink_concrete', 'light_blue_concrete', 'yellow_concrete', 'lime_concrete', 'white_concrete', 'magenta_concrete']
    g.floor_block = 'minecraft:white_concrete'
    plaza(g, 25, lambda x, z, d: cols[((x - 1) // 3 + (z - 1) // 3 * 2) % len(cols)] if d < 23 else 'purple_concrete', clear_h=20)
    # carousel, east
    cx, cz = C + 15, C - 10
    g.disc(cx, cz, 6, 1, 'gold_block')
    g.column(cx, cz, 2, 9, 'gold_block')
    for k in range(8):
        a = k / 8 * 2 * math.pi
        x, z = round(cx + math.cos(a) * 5), round(cz + math.sin(a) * 5)
        g.column(x, z, 2, 8, 'end_rod[facing=up]')
        g.set(x, 3 + k % 2, z, 'white_wool' if k % 2 else 'pink_wool')
    for dy in range(0, 5):
        g.disc(cx, cz, 7 - dy * 1.4, 9 + dy, None,
               pattern=lambda x, z, d: 'red_wool' if int((math.degrees(math.atan2(z - cz, x - cx)) + 180) // 22.5) % 2 else 'white_wool')
    g.set(cx, 15, cz, 'gold_block')
    # slide tower, west
    sx, sz = C - 16, C - 10
    g.box(sx - 2, 1, sz - 2, sx + 2, 10, sz + 2, 'light_blue_concrete', hollow=True)
    g.box(sx - 1, 1, sz - 1, sx + 1, 10, sz + 1, AIR)
    for y in range(1, 11):
        g.set(sx, y, sz - 1, 'ladder[facing=south,waterlogged=false]')
    for y in (1, 2):
        g.set(sx, y, sz + 2, AIR)
    for k in range(10):
        g.set(sx + 3 + k, 10 - k, sz, 'smooth_quartz_slab[type=bottom,waterlogged=false]')
        g.set(sx + 3 + k, 10 - k, sz - 1, 'pink_concrete')
        g.set(sx + 3 + k, 10 - k, sz + 1, 'pink_concrete')
    g.roof_hip(sx - 2, sz - 2, sx + 2, sz + 2, 11, 'red_nether_brick_stairs', 'red_wool', flare=1)
    # toy blocks and a die
    for (x, z, y, c) in ((C - 15, C + 12, 1, 0), (C - 11, C + 12, 1, 1), (C - 13, C + 12, 4, 2), (C + 13, C + 15, 1, 3)):
        g.box(x - 1, y, z - 1, x + 1, y + 2, z + 1, cols[c])
    g.box(C + 16, 1, C + 6, C + 20, 5, C + 10, 'white_concrete')
    for (x, y, z) in ((C + 18, 3, C + 5), (C + 15, 2, C + 7), (C + 15, 4, C + 9), (C + 17, 6, C + 7), (C + 19, 6, C + 9)):
        g.set(x, y, z, 'black_concrete')
    # balloons
    for k in range(9):
        a = k * 0.7 + 0.3
        x, z = round(C + math.cos(a) * 20), round(C + 2 + math.sin(a) * 18)
        if not (1 < z < W - 2):
            continue
        y = 14 + k % 3 * 3
        g.line((x, 1, z), (x, y - 2, z), 'white_wool' if False else 'chain[axis=y]')
        g.sphere(x, y, z, 1.4, cols[k % len(cols)].replace('concrete', 'wool'))
    # the squeaky hammer
    g.line((C - 20, 1, C + 2), (C - 15, 12, C + 2), 'yellow_concrete', r=0.6)
    g.box(C - 17, 12, C, C - 12, 15, C + 4, 'red_concrete')
    g.box(C - 18, 12, C + 1, C - 18, 15, C + 3, 'yellow_concrete')
    g.box(C - 11, 12, C + 1, C - 11, 15, C + 3, 'yellow_concrete')
    # the traffic light at red
    tx, tz = C + 8, C + 18
    g.column(tx, tz, 1, 9, 'black_concrete')
    g.box(tx - 1, 10, tz, tx + 1, 16, tz, 'black_concrete')
    g.set(tx, 15, tz + 1, 'redstone_block'); g.set(tx, 15, tz, 'shroomlight')
    g.set(tx, 13, tz + 1, 'yellow_terracotta')
    g.set(tx, 11, tz + 1, 'green_terracotta')


# ---------------------------------------------------------------- 13
def lucifara(g):
    """失楽堕天 ルシファーラ (reserved; dark violet, crimson; black wings, a scythe; the rose garden of illusion, the chalice
    of the soul-feast): 「薔薇の失楽園」. The ruin of a cathedral, its nave walls broken off at different heights, a great
    rose window of crimson glass, a dark rose garden in its aisles, black feathers drifting, a golden chalice behind the
    seal."""
    g.floor_block = 'minecraft:polished_blackstone_bricks'
    plaza(g, 25, lambda x, z, d: 'cracked_polished_blackstone_bricks' if (x * 3 + z * 7) % 5 == 0 else 'polished_blackstone_bricks', clear_h=26)
    for z in range(C - 18, W - 2):
        g.set(C, 1, z, 'red_carpet') if abs(z - C) > 1 else None
    # the nave walls with pointed windows, broken off
    for side in (-1, 1):
        x = C + side * 13
        for z in range(4, W - 4):
            top = 24 - (abs(z * 7 + side * 3) % 11) if z > C else 26
            for y in range(1, top):
                win = (z % 6 in (2, 3)) and 4 <= y <= 15
                g.set(x, y, z, 'red_stained_glass_pane' if win and z % 12 < 6 else (AIR if win else 'polished_blackstone_bricks'))
            if z % 6 == 0:
                for y in range(1, top):
                    g.set(x + side, y, z, 'polished_blackstone')
                g.set(x + side, top, z, 'gilded_blackstone')
    # the apse wall and rose window, north
    for x in range(C - 13, C + 14):
        for y in range(1, 30):
            d = math.hypot(x - C, y - 17)
            if d <= 9:
                a = math.degrees(math.atan2(y - 17, x - C)) % 45
                g.set(x, y, 3, 'gold_block' if d < 1.5 or abs(d - 6) < 0.5 or a < 3 else ('red_stained_glass' if d < 6 else 'magenta_stained_glass'))
            elif y < 29 - abs(x - C) // 2:
                g.set(x, y, 3, 'polished_blackstone_bricks')
    # the chalice
    cx, cz = C, C - 10
    g.box(cx - 1, 1, cz - 1, cx + 1, 1, cz + 1, 'gold_block')
    g.column(cx, cz, 2, 5, 'gold_block')
    for y in range(6, 11):
        g.ring(cx, cz, (y - 6) * 0.6 + 1, (y - 6) * 0.6 + 1.6, y, 'gold_block')
    g.disc(cx, cz, 2, 9, 'red_stained_glass')
    # rose beds in the aisles
    for side in (-1, 1):
        for z in range(C - 14, C + 22, 2):
            x = C + side * 10
            g.set(x, 0, z, 'grass_block[snowy=false]')
            g.set(x, 1, z, 'rose_bush[half=lower]'); g.set(x, 2, z, 'rose_bush[half=upper]')
            g.set(x - side, 0, z, 'grass_block[snowy=false]')
            g.set(x - side, 1, z, 'wither_rose' if z % 4 else 'red_tulip')
    # feathers
    for k in range(12):
        a = k * 1.9
        x, z = C + math.cos(a) * (8 + k % 4 * 4), C + math.sin(a) * (8 + k % 4 * 4)
        y = 16 + k % 5 * 2
        g.curve([(x, y, z), (x + 2, y + 1, z + 1), (x + 4, y - 1, z + 3)], 'black_concrete', r0=0.6, r1=0.3)


# ---------------------------------------------------------------- 14
def taika(g):
    """超克覇王 辿迦 (quiet; dark crimson; horns; stamping fist, shock waves): 「覇王の闘技場」. A colosseum: a round floor of
    packed earth cracked by his stamp in rays from the centre, tiered stone stands behind an arcaded wall hung with red
    banners, training posts, and two great horns curving over the north gate."""
    g.floor_block = 'minecraft:packed_mud'

    def floor(x, z, d):
        a = math.degrees(math.atan2(z - C, x - C)) % 30
        if d < 15 and (a < 1.6 or a > 28.4) and d > 4:
            return 'cracked_stone_bricks' if d % 3 < 2 else 'magma_block'
        return 'packed_mud' if d < 15 else 'stone_bricks'
    plaza(g, 26, floor, clear_h=18)
    for k, r in enumerate(range(16, 25, 2)):
        for x in range(1, W - 1):
            for z in range(1, W - 1):
                d = math.hypot(x - C, z - C)
                if r <= d < r + 2 and not (abs(x - C) <= 3 and (z > C or z < C)):
                    for y in range(1, k + 2):
                        g.set(x, y, z, 'stone_bricks')
                    g.set(x, k + 2, z, stair('stone_brick_stairs', outward(x - C, z - C)) if d < r + 1 else 'stone_bricks')
    # the arcade wall
    for x in range(0, W):
        for z in range(0, W):
            d = math.hypot(x - C, z - C)
            if 25.2 <= d <= 26.4 and not (abs(x - C) <= 3):
                ang = math.degrees(math.atan2(z - C, x - C)) % 12
                for y in range(1, 13):
                    arch = 4 <= ang <= 8 and y <= 8
                    g.set(x, y, z, AIR if arch else ('red_sandstone' if y in (9, 12) else 'stone_bricks'))
                if ang < 1:
                    g.set(x, 13, z, 'stone_bricks'); g.set(x, 14, z, 'red_wool')
    for k in range(16):
        a = k / 16 * 2 * math.pi
        x, z = round(C + math.cos(a) * 24.5), round(C + math.sin(a) * 24.5)
        if abs(x - C) > 3:
            g.set(x, 12, z, 'red_wool'); g.set(x, 11, z, 'red_wool'); g.set(x, 10, z, 'red_wool')
    for (x, z) in ((C - 9, C - 9), (C + 9, C - 9), (C - 9, C + 9), (C + 9, C + 9), (C, C - 12), (C, C + 12)):
        g.column(x, z, 1, 3, 'stripped_spruce_log[axis=y]')
        g.set(x, 4, z, 'hay_block')
    # the horns
    for side in (-1, 1):
        g.curve([(C + side * 5, 1, 2), (C + side * 6, 14, 1), (C + side * 3, 24, 3), (C + side * 0.5, 22, 6)], 'bone_block[axis=y]', r0=2.2, r1=0.4)
        g.curve([(C + side * 5, 0, 2), (C + side * 5, 3, 2)], 'red_sandstone', r0=2.5, r1=2.5)


# ---------------------------------------------------------------- 15
def mary_sue(g):
    """覚醒進化 メアリー・スー (a guardian; honey hair, cream, gold; a crown; the hero's tale, chapter after chapter): 「英雄譚の
    書架宮」. The stage is a giant open book, its pages white and lined, its cover gold-edged; four towers of bookshelves
    with golden crowns; a hero's sword in a stone; the stars of her last chapter hung overhead."""
    g.floor_block = 'minecraft:white_concrete'
    plaza(g, 25, 'end_stone_bricks', clear_h=24)
    # the book: two pages each side of a spine running north-south
    for x in range(C - 18, C + 19):
        for z in range(C - 14, C + 15):
            edge = abs(x - C) == 18 or abs(z - C) == 14
            g.set(x, 0, z, 'orange_terracotta' if edge else 'birch_planks')
            if not edge:
                rise = 1 if abs(x - C) > 2 else 0
                if abs(x - C) <= 1:
                    g.set(x, 0, z, 'dark_oak_planks')
                else:
                    g.set(x, 1, z, 'white_concrete' if (z - C) % 3 else 'light_gray_concrete')
            if edge:
                g.set(x, 1, z, 'gold_block')
    for z in range(C - 13, C + 14):
        g.set(C, 1, z, 'red_carpet') if abs(z - C) > 1 else None
    g.seal_y = 2
    # shelf towers
    for (x, z) in ((C - 21, C - 17), (C + 21, C - 17), (C - 21, C + 17), (C + 21, C + 17)):
        g.box(x - 2, 1, z - 2, x + 2, 16, z + 2, 'bookshelf')
        for y in (1, 6, 11, 16):
            g.box(x - 2, y, z - 2, x + 2, y, z + 2, 'dark_oak_planks')
        g.ring(x, z, 2, 3, 17, 'gold_block')
        for k in range(6):
            a = k / 6 * 2 * math.pi
            g.set(round(x + math.cos(a) * 2.5), 18, round(z + math.sin(a) * 2.5), 'gold_block')
        g.set(x, 17, z, 'sea_lantern')
    # the sword in the stone
    g.box(C - 3, 0, 2, C + 3, 3, 7, 'stone_bricks')
    g.box(C - 2, 4, 3, C + 2, 4, 6, 'mossy_stone_bricks')
    g.sword(C, 4, 5, 10, blade='quartz_block', edge='yellow_stained_glass', guard='gold_block', grip='blue_wool', pommel='sea_lantern', axis='x')
    # stars
    for k in range(16):
        a = k * 2.4
        x, z = C + math.cos(a) * (6 + k % 5 * 4), C + math.sin(a) * (6 + k % 5 * 4)
        y = 20 + k % 4 * 3
        for (dx, dy, dz) in ((0, 0, 0), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
            g.set(round(x) + dx, y + dy, round(z) + dz, 'yellow_stained_glass' if (dx, dy) != (0, 0) else 'sea_lantern')


# ---------------------------------------------------------------- 16
def savior(g):
    """救世天主 セイヴァー (a guardian; white and pale gold; a halo, a staff, the holy shield; healing; the twelve-winged
    sanctuary): 「最後の聖域」. A white sanctuary court under a chapel, twelve great white wings fanned behind it, kite
    shields with golden crosses round the court, a healing fountain, a golden halo over the chapel."""
    g.floor_block = 'minecraft:quartz_bricks'
    plaza(g, 25, lambda x, z, d: 'gold_block' if abs(d - 9) < 0.5 else ('calcite' if (x + z) % 2 else 'smooth_quartz'), clear_h=24)
    # the chapel, north
    x0, x1, z0, z1 = C - 8, C + 8, 2, 12
    g.box(x0, 1, z0, x1, 12, z1, 'quartz_bricks', hollow=True)
    g.box(x0 + 1, 1, z0 + 1, x1 - 1, 11, z1 - 1, AIR)
    for x in range(x0 + 2, x1 - 1, 3):
        for y in range(3, 10):
            g.set(x, y, z0, 'yellow_stained_glass_pane'); g.set(x, y, z1, 'yellow_stained_glass_pane' if abs(x - C) > 2 else g.get(x, y, z1))
    for x in range(C - 1, C + 2):
        for y in range(1, 6):
            g.set(x, y, z1, AIR)
    for y in range(13, 20):
        w = 19 - y
        g.box(C - w, y, z0, C + w, y, z1, 'smooth_quartz')
    g.column(C, (z0 + z1) // 2, 20, 26, 'quartz_pillar[axis=y]')
    halo(g, C, 28, 7, 4, 'gold_block', tilt=math.pi / 2, axis='x', thick=0.5)
    # twelve wings
    for side in (-1, 1):
        for k in range(6):
            a = math.radians(15 + k * 13)
            tip = (C + side * (10 + math.cos(a) * 20), 6 + math.sin(a) * 26, 6 - k * 0.6)
            g.curve([(C + side * 7, 10, 7), (C + side * 12, 18, 6), tip], 'white_wool' if k % 2 else 'quartz_block', r0=1.5, r1=0.5)
            g.curve([(C + side * 7, 9, 8), tip], 'white_concrete', r0=0.6, r1=0.3, only_empty=True)
    # shields
    for k in range(10):
        a = math.radians(30 + k * 12)
        x, z = round(C + math.cos(a) * 22), round(C + math.sin(a) * 22)
        for y in range(1, 9):
            w = 2 if y > 3 else (1 if y > 1 else 0)
            for t in range(-w, w + 1):
                px, pz = (x + t, z) if abs(math.cos(a)) < 0.7 else (x, z + t)
                g.set(px, y, pz, 'gold_block' if t == 0 or y == 6 else 'quartz_bricks')
    # the fountain
    for side in (-1, 1):
        fx, fz = C + side * 14, C + 4
        g.disc(fx, fz, 3, 1, 'quartz_bricks')
        g.disc(fx, fz, 2, 1, 'water')
        g.column(fx, fz, 1, 4, 'quartz_pillar[axis=y]')
        g.set(fx, 5, fz, 'sea_lantern')


# ---------------------------------------------------------------- 17
def gokuka(g):
    """外業呪禍 獄華 (reserved; dark violet; horns, claws, a tail; poison and curses, the black flower that opens, the gate of
    the cursed flower): 「呪花の門」. A swamp shrine: a row of blackened torii to the seal, paper talismans on posts, purple
    soul-fire lanterns, spider lilies and wither roses, and to the north a giant black flower opening into a gate."""
    g.floor_block = 'minecraft:mud_bricks'
    plaza(g, 25, lambda x, z, d: 'mud_bricks' if (x + z) % 3 else 'packed_mud', clear_h=26)
    for z in range(C + 6, W - 2, 5):
        g.torii(C, z, 1, 7, 7, axis='x', post='black_concrete', beam='purple_concrete', gold='crying_obsidian')
    # the cursed flower gate
    cx, cz, cy = C, 7, 14
    g.curve([(C, 0, 12), (C, 6, 9), (C, cy, cz)], 'crimson_hyphae[axis=y]', r0=1.5, r1=1.2)
    for k in range(7):
        a = k / 7 * 2 * math.pi + 0.3
        tip = (cx + math.cos(a) * 12, cy + 2 + math.sin(a) * 12, cz - 3)
        mid = (cx + math.cos(a) * 7, cy + math.sin(a) * 7, cz + 1)
        g.curve([(cx, cy, cz), mid, tip], 'black_concrete', r0=2.0, r1=0.6)
        g.curve([(cx, cy, cz + 0.6), mid, tip], 'purple_concrete', r0=1.0, r1=0.3, only_empty=True)
    g.sphere(cx, cy, cz, 2.5, 'crying_obsidian')
    g.set(cx, cy, cz + 3, 'ochre_froglight')
    # talismans and lanterns
    for k in range(14):
        a = k / 14 * 2 * math.pi
        x, z = round(C + math.cos(a) * 20), round(C + math.sin(a) * 20)
        if z < 12:
            continue
        g.column(x, z, 1, 4, 'dark_oak_fence')
        g.set(x, 5, z, lantern('soul_lantern'))
        g.set(x, 3, z + (1 if z < C else -1), 'white_wall_banner[facing=%s]' % ('south' if z < C else 'north'))
    g.scatter(2, 14, W - 3, W - 3, 1, ['wither_rose', 'red_tulip', 'torchflower'], density=0.18)


# ---------------------------------------------------------------- 18
def merlinus(g):
    """魔導深淵 メルリヌス (a researcher, small; deep violet, lilac; a staff; reflected spells, time binding, geometric
    bullets, many-layered circles): 「深淵の魔導塔」. A floor that is one great magic circle, a tall wizard's tower of dark
    stone with a violet cone roof and bookshelves inside, floating geometric solids, and twelve candle-pillars as a clock."""
    g.floor_block = 'minecraft:polished_deepslate'

    def floor(x, z, d):
        a = math.atan2(z - C, x - C)
        if any(abs(d - r) < 0.5 for r in (7, 12, 18, 23)):
            return 'amethyst_block'
        for k in range(5):
            b = a - k * 2 * math.pi / 5
            if abs(math.sin(b) * d) < 0.5 and math.cos(b) > 0 and d < 18:
                return 'purple_concrete'
        return 'polished_deepslate' if (x + z) % 2 else 'deepslate_tiles'
    plaza(g, 25, floor, clear_h=22)
    tx, tz = C - 15, C - 15
    g.cyl(tx, tz, 5, 0, 36, 'deepslate_bricks', hollow=True)
    for y in range(1, 36):
        g.disc(tx, tz, 4, y, AIR)
        if y % 7 == 0:
            g.disc(tx, tz, 4, y, 'dark_oak_planks')
    for y in range(1, 36):
        g.set(tx + 4, y, tz, 'ladder[facing=west,waterlogged=false]')
    for y in range(2, 34):
        for (dx, dz) in ((-4, 0), (0, -4), (0, 4)):
            if y % 7 not in (0,):
                g.set(tx + dx, y, tz + dz, 'bookshelf')
    for y in range(5, 34, 7):
        for (dx, dz) in ((0, 5), (-5, 0), (0, -5)):
            g.set(tx + dx, y, tz + dz, 'purple_stained_glass_pane')
    for y in (1, 2, 3):
        g.set(tx + 3, y, tz + 3, AIR); g.set(tx + 4, y, tz + 3, AIR); g.set(tx + 3, y, tz + 4, AIR)
    g.cone(tx, 37, tz, 7, 14, 'purple_concrete', edge='amethyst_cluster[facing=up,waterlogged=false]')
    g.ring(tx, tz, 5, 7, 36, 'purple_concrete')
    # floating solids
    for k, (r, y) in enumerate(((12, 20), (15, 24), (11, 28), (17, 18), (14, 30))):
        a = k * 1.3
        x, z = C + math.cos(a) * r, C + math.sin(a) * r
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                for dz in range(-2, 3):
                    if abs(dx) + abs(dy) + abs(dz) == 2:
                        g.set(round(x) + dx, y + dy, round(z) + dz, 'purple_stained_glass' if k % 2 else 'amethyst_block')
        g.set(round(x), y, round(z), 'verdant_froglight' if False else 'sea_lantern')
    for k in range(12):
        a = k / 12 * 2 * math.pi
        x, z = round(C + math.cos(a) * 21), round(C + math.sin(a) * 21)
        g.column(x, z, 1, 3 + (k % 3 == 0) * 2, 'polished_blackstone_bricks')
        g.set(x, 4 + (k % 3 == 0) * 2, z, 'purple_candle[candles=4,lit=true,waterlogged=false]')


# ---------------------------------------------------------------- 19
def enkou(g):
    """災極海獣 淵煌 (a sea beast; abyssal navy, glowing cyan; fins, horns, teeth; the trident, crushing whirlpools): 「深淵の
    海獣窟」, on the deep sea floor. The sea-beast's great jaw is the gate, rows of teeth over the way in, ribs of a
    leviathan round the field, a black trident standing in the north, vents and lanterns in the dark."""
    g.floor_block = 'minecraft:dark_prismarine'
    g.disc(C, C, 25, 0, None, pattern=lambda x, z, d: 'dark_prismarine' if (x + z) % 3 else 'prismarine_bricks')
    # ribs
    for k in range(-3, 4):
        z = C + k * 5
        for side in (-1, 1):
            g.curve([(C + side * 20, 0, z), (C + side * 23, 12, z), (C + side * 13, 22, z), (C + side * 6, 20, z)], 'bone_block[axis=y]', r0=1.4, r1=0.6)
    # the jaw: two arcs of teeth at the south
    for side, y0 in ((1, 0), (-1, 16)):
        for x in range(C - 10, C + 11):
            h = 3 + int(5 * (1 - (abs(x - C) / 10) ** 2))
            g.set(x, y0 if side > 0 else y0, W - 4, 'dark_prismarine')
            if x % 2 == 0:
                for t in range(1, 4 if abs(x - C) > 3 else 5):
                    g.set(x, y0 + side * t, W - 4, 'quartz_block' if t < 3 else 'white_stained_glass')
    for side in (-1, 1):
        g.box(C + side * 11, 0, W - 5, C + side * 11, 16, W - 3, 'dark_prismarine')
    # the trident
    tx, tz = C, 6
    g.column(tx, tz, 1, 24, 'dark_prismarine')
    g.box(tx - 4, 24, tz, tx + 4, 24, tz, 'dark_prismarine')
    for dx in (-4, 0, 4):
        g.column(tx + dx, tz, 25, 31 if dx == 0 else 29, 'prismarine')
        g.set(tx + dx, 32 if dx == 0 else 30, tz, 'sea_lantern')
    for k in range(8):
        a = k / 8 * 2 * math.pi
        x, z = round(C + math.cos(a) * 16), round(C + math.sin(a) * 16)
        g.set(x, 1, z, 'magma_block' if k % 2 else 'sea_lantern')


# ---------------------------------------------------------------- 20
def kurma(g):
    """嶺脈地龍 クールマ (a turtle guardian; moss greens; mountains on its back, a tail; earthquakes, the continent's heart):
    「大地の甲羅山」. A turtle the size of a hill: its shell a mossy dome patterned in plates, small snow-capped peaks and
    pines on it, a head and four legs of stone; the seal in a mossy shrine-hollow on the shell's crown, stairs up the neck."""
    g.floor_block = 'minecraft:moss_block'
    plaza(g, 25, lambda x, z, d: 'moss_block' if (x + z) % 4 else 'mossy_cobblestone', clear_h=2)
    R, top = 21, 10
    for x in range(C - R - 1, C + R + 2):
        for z in range(C - R - 1, C + R + 2):
            d = math.hypot(x - C, z - C)
            if d > R:
                continue
            h = int(top * math.sqrt(max(0, 1 - (d / R) ** 2)))
            # plates: hexagon-ish seams
            seam = (int((x - C) / 5 + (z - C) / 9) + int((z - C) / 5)) % 2 == 0 and int(d) % 6 == 0
            for y in range(1, h + 1):
                g.set(x, y, z, 'polished_andesite' if seam and y == h else ('moss_block' if y == h else 'stone'))
    g.seal_y = top + 1
    g.disc(C, C, 7, top, 'mossy_stone_bricks')
    g.ring(C, C, 6.5, 7, top, 'polished_andesite')
    g.clear(C, C, 7, top + 1, top + 16)
    for (x, z) in ((C - 7, C - 7), (C + 7, C - 7), (C - 7, C + 7)):
        g.column(x, z, top - 1, top + 3, 'mossy_stone_brick_wall')
        g.set(x, top + 4, z, lantern())
    # peaks and pines on the shell
    for k in range(6):
        a = k / 6 * 2 * math.pi + 0.4
        x, z = round(C + math.cos(a) * 13), round(C + math.sin(a) * 13)
        if z > C + 8 and abs(x - C) < 6:
            continue
        base = int(top * math.sqrt(max(0, 1 - (13 / R) ** 2)))
        g.cone(x, base, z, 3, 7, 'stone', edge='snow_block')
        g.set(x, base + 7, z, 'snow_block')
        g.tree(x + 3, z + 1, base + 1, 5, 2, log='spruce_log[axis=y]', leaves='spruce_leaves')
    # head (south) with eyes, stairs up the neck; four legs; a tail
    g.box(C - 4, 1, C + 22, C + 4, 6, C + 26, 'stone')
    g.box(C - 3, 7, C + 22, C + 3, 7, C + 25, 'moss_block')
    g.set(C - 3, 5, C + 27, 'sea_lantern'); g.set(C + 3, 5, C + 27, 'sea_lantern')
    for k in range(top):
        for x in range(C - 1, C + 2):
            g.set(x, k + 1, C + 20 - k, stair('mossy_stone_brick_stairs', 'north'))
            for yy in range(1, k + 1):
                g.set(x, yy, C + 20 - k, 'stone')
            g.set(x, k + 2, C + 20 - k, AIR); g.set(x, k + 3, C + 20 - k, AIR)
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        g.box(C + sx * 17 - 2, 1, C + sz * 15 - 2, C + sx * 17 + 2, 4, C + sz * 15 + 2, 'stone')
    g.curve([(C, 1, C - 20), (C + 3, 2, C - 24), (C + 6, 1, C - 26)], 'stone', r0=2, r1=0.8)

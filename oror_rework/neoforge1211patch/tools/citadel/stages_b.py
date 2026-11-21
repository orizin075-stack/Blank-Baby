"""stages_b.py: the gods' stages, Teia to Sweet Pact (god_stages.py)."""
import math
from stage_kit import AIR, W, C, S, stair, slab, lantern, outward, DIRS, OPP
from stages_a import plaza, post_lamp, toro, halo, vring


# ---------------------------------------------------------------- 21
def teia(g):
    """光越天龍 テイア (a playful dragon; pale blue and light; wings, horns; the light bow, arrows of light, afterglow
    charges): 「天の光翔台」. A round platform raised on slender piers into the sky, reached by a spiral stair; wing-shaped
    terraces of white stone and glass spread east and west; a great bow of light drawn behind it; trails of light
    streaking past."""
    g.floor_block = 'minecraft:calcite'
    plaza(g, 25, 'calcite', clear_h=2)
    top = 10
    g.seal_y = top + 1
    for k in range(8):
        a = k / 8 * 2 * math.pi
        x, z = round(C + math.cos(a) * 9), round(C + math.sin(a) * 9)
        g.cyl(x, z, 1, 1, top - 1, 'quartz_block')
    g.cyl(C, C, 3, 1, top - 1, 'quartz_block')
    g.disc(C, C, 13, top, None, pattern=lambda x, z, d: 'light_blue_concrete' if abs(d - 10) < 0.6 else ('smooth_quartz' if (x + z) % 2 else 'calcite'))
    g.ring(C, C, 12.6, 13.2, top + 1, 'diorite_wall')
    g.clear(C, C, 13, top + 1, top + 16)
    # the spiral stair round the core, from the ground to the platform
    for k in range(top):
        a = k * 0.62
        x, z = round(C + math.cos(a) * 15), round(C + math.sin(a) * 15)
        for w in (-1, 0, 1):
            g.box(x + w, k, z, x + w, k, z, 'smooth_quartz')
            for yy in range(k + 1, k + 4):
                g.set(x + w, yy, z, AIR) if g.get(x + w, yy, z) not in ('minecraft:smooth_quartz',) else None
    a = (top - 1) * 0.62
    g.line((C + math.cos(a) * 15, top - 1, C + math.sin(a) * 15), (C + math.cos(a) * 12, top, C + math.sin(a) * 12), 'smooth_quartz', r=1.0)
    # the wings
    for side in (-1, 1):
        for k in range(5):
            y = top + 2 + k * 2
            for t in range(14 - k * 2):
                x = C + side * (13 + t)
                for z in range(C - 3 + k, C + 4 - k):
                    if 0 <= x < W:
                        g.set(x, y, z, 'white_stained_glass' if t % 3 else 'quartz_block')
        g.curve([(C + side * 12, top, C), (C + side * 20, top + 10, C - 2), (C + side * 26, top + 16, C)], 'quartz_block', r0=1.2, r1=0.5)
    # the bow
    for i in range(60):
        t = i / 59 * math.pi
        x = C + math.cos(t) * 16
        y = top + 4 + math.sin(t) * 22
        g.ball(x, y, 3, 0.9, 'quartz_block')
    g.line((C - 16, top + 4, 3), (C + 16, top + 4, 3), 'light_blue_stained_glass')
    g.line((C, top + 4, 3), (C, top + 30, 1), 'end_rod[facing=up]')
    for (p0, p1) in (((2, 30, 50), (52, 38, 10)), ((4, 34, 8), (50, 28, 46))):
        g.line(p0, p1, 'light_blue_stained_glass')


# ---------------------------------------------------------------- 22
def bahamut(g):
    """大海皇鯨 バハムート (a whale guardian; teal and sea green; fins, horns, coral; healing tides, the conch, the song of the
    nine seas): 「珊瑚の海皇宮」, on the open sea. A platform of sea stone round a tidal pool, coral gardens kept alive by
    channels of water, arches of whale ribs over the way in, a scallop-shell hall to the north and a giant conch beside it."""
    g.floor_block = 'minecraft:prismarine_bricks'
    plaza(g, 25, lambda x, z, d: 'prismarine_bricks' if (x + z) % 2 else 'dark_prismarine', rimstair='dark_prismarine_stairs', clear_h=22)
    g.ring(C, C, 14, 16, 0, 'water')
    g.ring(C, C, 16, 17, 1, 'prismarine_wall')
    for k in range(24):
        a = k / 24 * 2 * math.pi
        for r in (13, 17):
            x, z = round(C + math.cos(a) * r), round(C + math.sin(a) * r)
            g.set(x, 1, z, ['tube_coral_block', 'brain_coral_block', 'bubble_coral_block', 'horn_coral_block', 'fire_coral_block'][k % 5])
    for x in range(C - 2, C + 3):
        for z in range(C + 13, C + 18):
            g.set(x, 0, z, 'dark_prismarine')
    # whale ribs over the way in
    for k in range(4):
        z = C + 18 + k * 2
        g.curve([(C - 7, 0, z), (C - 8, 9, z), (C, 14 - k, z), (C + 8, 9, z), (C + 7, 0, z)], 'bone_block[axis=y]', r0=1.0, r1=1.0)
    # the shell hall
    sx, sz = C, 7
    for k in range(13):
        a = math.radians(180 + k * 15)
        tip = (sx + math.cos(a) * 14, 1 + max(0, -math.sin(a)) * 0 + 2, sz + math.sin(a) * 0)
        g.curve([(sx, 1, sz + 4), (sx + math.cos(a) * 8, 12 + 4 * math.sin(abs(a - math.radians(270))), sz),
                 (sx + math.cos(a) * 13, 1, sz - 2)], 'smooth_quartz' if k % 2 else 'pink_terracotta', r0=0.9, r1=0.9)
    g.box(sx - 3, 1, sz + 3, sx + 3, 4, sz + 3, AIR)
    # the conch
    cx, cz = C + 17, 8
    for i in range(80):
        t = i / 79
        a = t * 4 * math.pi
        r = 4.5 * (1 - t) + 0.5
        g.ball(cx + math.cos(a) * r * 0.6, 1 + t * 14, cz + math.sin(a) * r * 0.6, r, 'pink_terracotta' if i % 7 else 'smooth_quartz')
    g.sphere(cx, 2, cz, 3, 'smooth_quartz')
    for (x, z) in ((C - 20, C + 6), (C + 20, C + 6), (C - 20, C - 6)):
        g.column(x, z, 1, 3, 'prismarine_wall')
        g.set(x, 4, z, 'sea_lantern')


# ---------------------------------------------------------------- 23
def nun(g):
    """天変万化 ヌン (a shapeshifter, a researcher; ink black and violet; tentacles; the jester's staff, the thousand masks):
    「千面の仮面劇場」. A theatre in the dark: a round orchestra floor with the seal, a proscenium with red curtains drawn
    aside, masks of comedy, tragedy and the fool over it, tiered seats to the south, tentacles reaching up out of the
    stage's trap."""
    g.floor_block = 'minecraft:dark_oak_planks'
    plaza(g, 25, lambda x, z, d: 'black_concrete' if d < 10.5 and int(math.degrees(math.atan2(z - C, x - C)) // 30) % 2 else
          ('purple_concrete' if d < 10.5 else 'dark_oak_planks'), clear_h=22)
    # seats
    for k, r in enumerate(range(14, 25, 2)):
        for x in range(1, W - 1):
            for z in range(C, W - 1):
                d = math.hypot(x - C, z - C)
                if r <= d < r + 2 and abs(x - C) > 2:
                    for y in range(1, k + 2):
                        g.set(x, y, z, 'dark_oak_planks')
                    g.set(x, k + 2, z, stair('dark_oak_stairs', outward(x - C, z - C)) if d < r + 1 else 'red_wool')
    # the stage and proscenium, north
    g.box(C - 14, 0, 2, C + 14, 2, 12, 'dark_oak_planks')
    for x in range(C - 15, C + 16):
        for y in range(1, 24):
            inside = abs(x - C) <= 11 and y <= 17
            if not inside:
                g.set(x, y, 13, 'purple_terracotta' if y < 22 else 'gold_block')
    for x in range(C - 11, C + 12):
        g.set(x, 18, 13, 'gold_block')
    for side in (-1, 1):
        for k in range(4):
            for y in range(3, 18):
                g.set(C + side * (11 - k), y, 12, 'red_wool' if y > 3 + k * 2 else AIR)
    g.box(C - 14, 3, 2, C + 14, 22, 2, 'purple_terracotta')
    # masks
    for (mx, kind) in ((C - 8, 'comedy'), (C, 'fool'), (C + 8, 'tragedy')):
        for x in range(mx - 3, mx + 4):
            for y in range(19, 27):
                if ((x - mx) / 3.4) ** 2 + ((y - 22.5) / 4.2) ** 2 <= 1:
                    g.set(x, y, 14, 'white_concrete' if kind != 'fool' else 'purple_concrete')
        g.set(mx - 1, 24, 15, 'black_concrete'); g.set(mx + 1, 24, 15, 'black_concrete')
        mouth = 21 if kind == 'comedy' else 20
        for x in range(mx - 1, mx + 2):
            g.set(x, mouth + (0 if abs(x - mx) == 0 else (1 if kind == 'comedy' else -1)) * 0 + (1 if kind == 'tragedy' and abs(x - mx) == 1 else 0), 15, 'black_concrete')
        if kind == 'fool':
            for dx in (-3, 0, 3):
                g.line((mx, 26, 14), (mx + dx * 1.3, 30, 14), 'gold_block')
                g.set(mx + round(dx * 1.3), 31, 14, 'yellow_concrete')
    # tentacles through the stage's trap
    for k in range(4):
        a = k * 1.7
        x0, z0 = C - 6 + k * 4, 6
        g.curve([(x0, 2, z0), (x0 + math.cos(a) * 3, 9, z0 - 2), (x0 + math.cos(a) * 5, 15, z0 + 2)], 'purple_concrete', r0=1.2, r1=0.3)


# ---------------------------------------------------------------- 24
def arcana(g):
    """運命流転 アルカナ (a guardian; cream, white, gold; wings, a halo; the spindle staff, threads of fate, the card of
    miracles): 「運命の糸車」. Tarot cards laid in the floor, a great golden spinning wheel standing in the north with white
    wings behind it, golden threads drawn from it over the whole stage, and the needle of fate."""
    g.floor_block = 'minecraft:smooth_quartz'

    def floor(x, z, d):
        for k in range(8):
            a = k / 8 * 2 * math.pi + 0.2
            cx, cz = C + math.cos(a) * 17, C + math.sin(a) * 17
            if abs(x - cx) <= 2 and abs(z - cz) <= 3:
                return 'gold_block' if abs(x - cx) == 2 or abs(z - cz) == 3 else ('white_concrete' if k % 2 else 'purple_concrete')
        return 'smooth_quartz' if (x + z) % 2 else 'calcite'
    plaza(g, 25, floor, rimstair='quartz_stairs', clear_h=24)
    wx, wy, wz = C, 16, 5
    vring(g, wx, wy, wz, 11, 'gold_block', axis='x', thick=0.7, spokes=12, hub='gold_block', spoke='birch_planks')
    vring(g, wx, wy, wz, 9.5, 'birch_planks', axis='x', thick=0.4)
    g.box(wx - 1, 1, wz - 2, wx + 1, 5, wz + 2, 'stripped_birch_wood')
    g.line((wx, 5, wz), (wx, 15, wz), 'stripped_birch_log[axis=y]', r=0.7)
    for side in (-1, 1):
        g.line((wx + side * 12, 1, wz), (wx + side * 2, wy, wz - 1), 'stripped_birch_log[axis=y]', r=0.6)
        for k in range(5):
            a = math.radians(20 + k * 15)
            g.curve([(wx + side * 4, 18, wz - 2), (wx + side * 12, 24, wz - 3), (wx + side * (6 + math.cos(a) * 18), 10 + math.sin(a) * 22, wz - 3)],
                    'white_wool', r0=1.2, r1=0.4)
    for k in range(10):
        a = k / 10 * 2 * math.pi
        g.line((wx, wy, wz + 1), (C + math.cos(a) * 24, 1, C + 3 + math.sin(a) * 20), 'yellow_stained_glass')
    g.line((C + 16, 1, C + 16), (C + 9, 18, C + 9), 'iron_block', r=0.7)
    g.set(C + 9, 19, C + 9, 'gold_block')


# ---------------------------------------------------------------- 25
def eomaia(g):
    """始祖神獣 エオマイア (a beast guardian; tawny and olive; wings, antlers, claws; the beast-host, roars, the horn of the
    first herds): 「始祖の獣巣」. A primeval den: a ring of standing stones, a nest of logs and hay round the seal, great
    antler arches over the north gate, the skull of an elder beast, bones, old dark oaks."""
    g.floor_block = 'minecraft:coarse_dirt'
    plaza(g, 25, lambda x, z, d: ['coarse_dirt', 'podzol[snowy=false]', 'rooted_dirt', 'moss_block'][(x * 5 + z * 3) % 4], clear_h=20)
    g.ring(C, C, 7, 8.5, 1, 'stripped_dark_oak_wood')
    g.ring(C, C, 7.5, 8.2, 2, 'hay_block')
    for (x, z) in ((C, C + 8), (C, C + 7), (C, C - 8), (C, C - 7)):
        g.set(x, 1, z, AIR); g.set(x, 2, z, AIR)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        x, z = round(C + math.cos(a) * 19), round(C + math.sin(a) * 19)
        h = 6 + k % 3 * 2
        g.box(x - 1, 1, z - 1, x + 1, h, z, 'mossy_cobblestone' if k % 2 else 'stone')
        g.set(x, h + 1, z, 'moss_block')
    for side in (-1, 1):
        base = (C + side * 6, 0, 4)
        g.curve([base, (C + side * 7, 12, 3), (C + side * 2, 22, 4)], 'stripped_dark_oak_wood', r0=1.6, r1=0.6)
        for k in range(3):
            p = (C + side * (7 - k), 8 + k * 5, 3)
            g.curve([p, (p[0] + side * 5, p[1] + 4, 2), (p[0] + side * 7, p[1] + 9, 3)], 'stripped_dark_oak_wood', r0=0.9, r1=0.3)
    sx, sz = C + 14, C - 12
    g.sphere(sx, 4, sz, 4, 'bone_block[axis=y]', squash=0.8)
    g.sphere(sx, 4, sz + 3, 1.2, AIR)
    g.set(sx - 2, 5, sz + 3, 'black_concrete'); g.set(sx + 2, 5, sz + 3, 'black_concrete')
    g.box(sx - 2, 1, sz + 3, sx + 2, 2, sz + 5, 'bone_block[axis=y]')
    for side in (-1, 1):
        g.curve([(sx + side * 3, 6, sz), (sx + side * 7, 11, sz - 2), (sx + side * 6, 15, sz + 2)], 'bone_block[axis=y]', r0=1.0, r1=0.3)
    for k in range(6):
        a = k * 1.1
        x, z = C + math.cos(a) * 13, C + 10 + math.sin(a) * 6
        g.line((x, 1, z), (x + 3, 1, z + 1), 'bone_block[axis=x]')
    for (x, z) in ((C - 20, C + 14), (C + 20, C + 14), (C - 21, C - 6)):
        g.tree(x, z, 1, 7, 4, log='dark_oak_log[axis=y]', leaves='dark_oak_leaves')


# ---------------------------------------------------------------- 26
def demiurgos(g):
    """空創龍王 デミウルゴス (a proud dragon; black and violet; wings, horns, gems; the black dragon sword, the star gate,
    small universes of other laws): 「星門の創界」, in the End. A black platform whose floor holds stars, a vast star-gate
    ring of obsidian set with gems behind the seal, gems floating in the void, and his black dragon-sword driven into
    the stone."""
    g.floor_block = 'minecraft:obsidian'
    plaza(g, 25, lambda x, z, d: 'purple_concrete' if abs(d - 12) < 0.5 or abs(d - 20) < 0.5 else
          ('end_rod[facing=up]' if False else ('crying_obsidian' if (x * 31 + z * 17) % 29 == 0 else 'obsidian' if (x + z) % 2 else 'black_concrete')),
          rimstair='blackstone_stairs', clear_h=26)
    vring(g, C, 16, 6, 14, 'obsidian', axis='x', thick=1.2)
    vring(g, C, 16, 6, 12.5, 'purple_stained_glass', axis='x', thick=0.5)
    for k in range(12):
        a = k / 12 * 2 * math.pi
        g.ball(C + math.cos(a) * 14, 16 + math.sin(a) * 14, 6, 1.2, 'amethyst_block' if k % 2 else 'crying_obsidian')
    for k in range(9):
        a = k * 2.2
        x, z, y = C + math.cos(a) * 19, C + math.sin(a) * 19, 14 + k % 4 * 4
        for dx in range(-2, 3):
            for dy in range(-3, 4):
                for dz in range(-2, 3):
                    if abs(dx) + abs(dz) + abs(dy) * 0.7 <= 2.2:
                        g.set(round(x) + dx, y + dy, round(z) + dz, 'amethyst_block' if k % 3 else 'light_blue_stained_glass')
    g.sword(C + 17, C + 13, 0, 16, blade='black_concrete', edge='purple_stained_glass', guard='crying_obsidian', grip='obsidian',
            pommel='amethyst_block', axis='z', tilt=(-1, 1))


# ---------------------------------------------------------------- 27
def hakyoku(g):
    """無窮覇帝 覇極 (proud, small; black and hot pink; mechanical claws, devouring cannons; evolves from death): 「覇帝の捕食
    要塞」, in a cavern of the Nether. A blackstone floor crossed with glowing seams, four huge mechanical claws rising from
    the corners and closing over the field, devouring cannons on bastions, a maw of iron teeth in the north wall."""
    g.floor_block = 'minecraft:polished_blackstone'
    g.cavern = (27, 34)
    plaza(g, 26, lambda x, z, d: 'shroomlight' if (x - C) % 8 == 0 and (z - C) % 8 == 0 else
          ('crimson_nylium' if int(d) % 7 == 0 else 'polished_blackstone' if (x + z) % 2 else 'polished_basalt[axis=y]'), clear_h=1)
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        bx, bz = C + sx * 19, C + sz * 19
        g.cyl(bx, bz, 3, 1, 8, 'polished_blackstone_bricks')
        g.curve([(bx, 8, bz), (bx - sx * 2, 22, bz - sz * 2), (C + sx * 8, 27, C + sz * 8), (C + sx * 6, 20, C + sz * 6)], 'netherite_block', r0=1.6, r1=0.6)
        for k in (-1, 1):
            g.curve([(C + sx * 8, 27, C + sz * 8), (C + sx * (5 + k * 2), 24, C + sz * (5 - k * 2)), (C + sx * (6 + k * 2), 18, C + sz * (6 - k * 2))],
                    'iron_block', r0=0.8, r1=0.3)
        # cannons
        g.line((bx, 9, bz), (bx - sx * 7, 12, bz - sz * 7), 'black_concrete', r=1.2)
        g.set(bx - sx * 7, 12, bz - sz * 7, 'red_concrete')
    for x in range(C - 10, C + 11):
        for y in range(1, 16):
            g.set(x, y, 2, 'polished_blackstone_bricks')
        if x % 2 == 0:
            for t in range(3):
                g.set(x, 15 - t, 3, 'iron_block')
                g.set(x, 5 + t, 3, 'iron_block')
    for x in range(C - 7, C + 8):
        for y in range(8, 13):
            g.set(x, y, 2, 'magma_block')


# ---------------------------------------------------------------- 28
def shinra(g):
    """万物天敵 シンラ (quiet; black hair, ivory, rose; horns, claws; the parasol, the red-moon step, one silent final
    thrust): 「紅月の狩場」. A still garden at night under a great red moon: a stone path, bamboo groves, red spider lilies
    by a pond, parasols for shade, and one needle standing tall."""
    g.floor_block = 'minecraft:stone_bricks'
    plaza(g, 25, lambda x, z, d: 'moss_block' if d > 13 else ('stone_bricks' if (x + z) % 3 else 'mossy_stone_bricks'), clear_h=22)
    for x in range(C - 22, C + 23):
        for y in range(12, 46):
            d = math.hypot(x - C, y - 30)
            if d <= 13:
                g.set(x, y, 2, 'red_concrete' if d < 12 else 'red_stained_glass')
            if d <= 8 and (x * 3 + y) % 7 == 0:
                g.set(x, y, 3, 'red_terracotta')
    for x in range(C - 4, C + 5):
        for y in range(1, 12):
            g.set(x, y, 2, 'stripped_dark_oak_log[axis=y]') if x in (C - 4, C + 4) else None
    for k in range(40):
        a = k * 2.39
        r = 15 + (k * 7) % 9
        x, z = round(C + math.cos(a) * r), round(C + math.sin(a) * r)
        if z < 6 or abs(x - C) < 3 and z > C:
            continue
        g.column(x, z, 1, 6 + k % 5, 'bamboo_block[axis=y]')
        g.set(x, 7 + k % 5, z, 'bamboo_fence')
    g.disc(C - 14, C + 12, 4, 0, 'water')
    g.ring(C - 14, C + 12, 4, 5, 0, 'stone_bricks')
    g.scatter(C - 20, C + 6, C - 8, C + 18, 1, ['red_tulip', 'poppy', 'torchflower'], density=0.4, need='moss_block')
    for (x, z) in ((C + 14, C + 10), (C - 15, C - 8), (C + 16, C - 9)):
        g.column(x, z, 1, 7, 'dark_oak_fence')
        for dy in range(0, 3):
            g.ring(x, z, 0, 4.5 - dy * 1.5, 8 + dy, 'red_wool' if dy == 0 else 'white_wool')
        g.ring(x, z, 4, 4.6, 8, 'red_wool')
        g.set(x, 7, z, lantern(hanging=True))
    g.column(C + 9, C + 18, 1, 26, 'iron_bars')
    g.set(C + 9, 27, C + 18, 'lightning_rod[facing=up,powered=false,waterlogged=false]')
    for z in range(C + 6, W - 2):
        g.set(C, 0, z, 'polished_andesite')


# ---------------------------------------------------------------- 29
def ain_sof_aur(g):
    """全界支配 アインソフオウル (a guardian; lavender and white; a crown; branching worlds, the star-mirror of parallel worlds,
    the throne of infinite branches): 「無限分岐の玉座」. A lavender-white throne in the north, and behind and above it a
    tree of light branching two, four, eight, sixteen ways, each tip a gate into another world; mirrors stand in a ring."""
    g.floor_block = 'minecraft:smooth_quartz'

    def floor(x, z, d):
        if abs(x - C) < 0.6 and z < C or abs(abs(x - C) - (C - z) * 0.5) < 0.6 and C - 20 < z < C - 4:
            return 'gold_block'
        return 'purpur_block' if (x // 3 + z // 3) % 2 else 'smooth_quartz'
    plaza(g, 25, floor, rimstair='quartz_stairs', clear_h=26)
    g.box(C - 4, 1, 6, C + 4, 2, 9, 'purpur_block')
    g.box(C - 3, 3, 6, C + 3, 12, 6, 'purpur_block')
    g.box(C - 2, 3, 7, C + 2, 3, 8, 'magenta_wool')
    g.box(C - 3, 13, 6, C + 3, 13, 6, 'gold_block')

    def branch(p, ang, length, depth):
        if depth == 0:
            vring(g, p[0], p[1], p[2], 2.2, 'gold_block', axis='x', thick=0.4)
            g.ball(p[0], p[1], p[2], 1.4, ['purple_stained_glass', 'light_blue_stained_glass', 'lime_stained_glass', 'red_stained_glass',
                                           'yellow_stained_glass', 'cyan_stained_glass'][int((p[0] + p[1]) % 6)])
            return
        q = (p[0] + math.sin(ang) * length, p[1] + math.cos(ang) * length, p[2] + (0.6 if depth % 2 else -0.6))
        g.line(p, q, 'quartz_block' if depth > 2 else 'white_stained_glass', r=0.3 + depth * 0.25)
        for s in (-1, 1):
            branch(q, ang + s * 0.42, length * 0.72, depth - 1)
    branch((C, 13, 5), 0.0, 9, 4)
    for k in range(10):
        a = math.radians(20 + k * 16)
        x, z = round(C + math.cos(a) * 20), round(C + math.sin(a) * 20)
        for y in range(1, 10):
            g.set(x, y, z, 'tinted_glass' if 2 < y < 9 else 'purpur_pillar[axis=y]')
        g.set(x, 10, z, 'amethyst_cluster[facing=up,waterlogged=false]')


# ---------------------------------------------------------------- 30
def angra_mainyu(g):
    """全害惡徳 アンラマンユ (reserved; black and blood red; marks on the skin; shadow chains, the black cup of malice, the
    ring of seven sins, black wings): 「悪徳の黒杯殿」, in the badlands. A stepped black temple of blackstone and red sand
    stone, seven pillars of the sins each with its own fire, shadow chains from them to the centre, the black grail on the
    temple and black wings over it."""
    g.floor_block = 'minecraft:polished_blackstone'
    plaza(g, 25, lambda x, z, d: 'red_sandstone' if int(d) % 5 == 0 else ('polished_blackstone' if (x + z) % 2 else 'blackstone'), rimstair='blackstone_stairs', clear_h=22)
    for k, w in enumerate((10, 8, 6, 4)):
        g.box(C - w, k * 2, 2, C + w, k * 2 + 1, 2 + w * 2 - 2 * k // 2, 'polished_blackstone_bricks' if k % 2 else 'red_sandstone')
    g.box(C - 1, 8, 4, C + 1, 9, 6, 'obsidian')
    for y in range(10, 14):
        g.ring(C, 5, (y - 10) * 0.7, (y - 10) * 0.7 + 0.8, y, 'obsidian')
    g.disc(C, 5, 2, 13, 'red_stained_glass')
    for side in (-1, 1):
        for k in range(5):
            a = math.radians(10 + k * 16)
            g.curve([(C + side * 2, 14, 4), (C + side * 10, 20, 3), (C + side * (4 + math.cos(a) * 16), 8 + math.sin(a) * 18, 2)],
                    'black_concrete', r0=1.3, r1=0.4)
    fires = ['campfire', 'soul_campfire', 'campfire', 'soul_campfire', 'campfire', 'soul_campfire', 'campfire']
    for k in range(7):
        a = math.radians(-90 + 45 + k * 45)
        x, z = round(C + math.cos(a) * 18), round(C + math.sin(a) * 18)
        g.column(x, z, 1, 9, 'polished_blackstone_bricks', cap='gilded_blackstone')
        g.set(x, 10, z, S(fires[k], facing='north', lit='true', signal_fire='false', waterlogged='false'))
        g.line((x, 8, z), (C + (x - C) * 0.4, 14, C + (z - C) * 0.4), 'chain[axis=y]' if False else 'black_concrete', r=0.2)


# ---------------------------------------------------------------- 31
def magna_mater(g):
    """始源母胎 マグナ・マーテル (a guardian; leaf green and warm tan; wings, vines; seeds, roots, the womb from which a new world
    unfolds): 「生命の母胎」, under the forest. A living cavern: root pillars from roof to floor hung with light, a meadow
    floor of moss and flowers, a spring, seed pods glowing like eggs, and a ring of flowering hedges round the seal."""
    g.floor_block = 'minecraft:moss_block'
    g.cavern = (27, 30)
    plaza(g, 26, lambda x, z, d: 'moss_block' if (x * 3 + z) % 7 else 'rooted_dirt', clear_h=1)
    g.ring(C, C, 8, 9.5, 1, 'flowering_azalea_leaves[distance=1,persistent=true,waterlogged=false]')
    for (x, z) in ((C, C + 9), (C, C + 8), (C, C - 9), (C, C - 8)):
        g.set(x, 1, z, AIR)
    for k in range(10):
        a = k / 10 * 2 * math.pi + 0.3
        x, z = C + math.cos(a) * 19, C + math.sin(a) * 19
        g.curve([(x, 0, z), (x + math.cos(a) * 2, 12, z + math.sin(a) * 2), (x - math.cos(a) * 3, 24, z - math.sin(a) * 3), (x, 30, z)],
                'mangrove_roots[waterlogged=false]' if k % 2 else 'stripped_dark_oak_wood', r0=1.6, r1=1.0)
        g.set(round(x - math.cos(a) * 2), 18, round(z - math.sin(a) * 2), 'shroomlight')
    for k in range(7):
        a = k * 0.9 + 0.2
        x, z = C + math.cos(a) * 14, C + math.sin(a) * 14
        g.sphere(x, 2.5, z, 2, 'pearlescent_froglight' if k % 2 else 'verdant_froglight', squash=1.3)
    g.disc(C + 12, C - 13, 3.5, 0, 'water')
    g.scatter(2, 2, W - 3, W - 3, 1, ['allium', 'azure_bluet', 'oxeye_daisy', 'lily_of_the_valley', 'pink_petals[facing=north,flower_amount=4]',
                                      'short_grass'], density=0.25, need='moss_block')


# ---------------------------------------------------------------- 32
def ouroboros(g):
    """無限円環 ウロボロス (a guardian; slate blue and gold; the wheel; rewinding, the hourglass of rebirth, the great black-gold
    ring that closes beginning and end): 「円環の時計庭」. The floor is a clock's dial with golden hours and black hands; round
    it lies the serpent biting its tail, scaled in black and gold, rising into an arch for the way in; hourglasses stand
    at the four quarters; ring-blades hang in the air."""
    g.floor_block = 'minecraft:smooth_quartz'

    def floor(x, z, d):
        a = math.degrees(math.atan2(z - C, x - C)) % 30
        if 17 < d < 19.5 and (a < 2 or a > 28):
            return 'gold_block'
        if abs(d - 20) < 0.5 or abs(d - 16) < 0.5:
            return 'gold_block'
        return 'smooth_quartz' if d < 16 else 'polished_deepslate'
    plaza(g, 25, floor, clear_h=22)
    g.line((C, 0, C), (C - 9, 0, C - 9), 'black_concrete')
    g.line((C, 0, C), (C + 13, 0, C), 'black_concrete')
    n = 240
    for i in range(n):
        t = i / n * 2 * math.pi
        x, z = C + math.cos(t) * 22.5, C + math.sin(t) * 22.5
        rise = max(0.0, math.cos(t - math.pi / 2)) ** 6 * 7
        g.ball(x, 2 + rise, z, 1.8, 'black_concrete' if i % 6 < 4 else 'gold_block')
    g.sphere(C + 0.0, 4, C - 22.5, 3, 'black_concrete')
    g.set(C + 2, 5, C - 20, 'red_concrete'); g.set(C - 2, 5, C - 20, 'red_concrete')
    for (sx, sz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        hx, hz = C + sx * 13, C + sz * 13
        g.box(hx - 2, 1, hz - 2, hx + 2, 1, hz + 2, 'gold_block')
        g.box(hx - 2, 11, hz - 2, hx + 2, 11, hz + 2, 'gold_block')
        for y in range(2, 11):
            r = abs(y - 6.5) / 4.5 * 1.8 + 0.3
            g.disc(hx, hz, r, y, 'white_stained_glass')
            if y < 6:
                g.disc(hx, hz, max(0, r - 1), y, 'sandstone')
        for (cx, cz) in ((hx - 2, hz - 2), (hx + 2, hz + 2), (hx - 2, hz + 2), (hx + 2, hz - 2)):
            g.column(cx, cz, 2, 10, 'polished_deepslate_wall')
        g.set(hx, 6, hz, 'sandstone')
    for k in range(3):
        vring(g, C + (k - 1) * 14, 24 + k * 2, C - 8 + k * 6, 3, 'iron_block', axis='x' if k % 2 else 'z', thick=0.5)


# ---------------------------------------------------------------- 33
def yggdrasil(g):
    """玖天神樹 イグドラシル (a tree guardian; fresh leaf green; branches, leaves; roots that bind, the nine crowns that rain
    healing light): 「九界の神樹」. The world tree stands at the north of the stage, its trunk five blocks thick, its roots
    running out over the ground round the seal, one great crown overhead and eight lesser crowns about it, spirit-lights
    in its leaves, moss and flowers at its feet."""
    g.floor_block = 'minecraft:moss_block'
    plaza(g, 25, lambda x, z, d: 'moss_block' if (x + z) % 5 else 'grass_block[snowy=false]', clear_h=18)
    tx, tz = C, C - 15
    g.cyl(tx, tz, 3.5, 1, 40, 'oak_wood[axis=y]')
    for k in range(9):
        a = k / 9 * 2 * math.pi
        g.curve([(tx + math.cos(a) * 3, 3, tz + math.sin(a) * 3), (tx + math.cos(a) * 9, 2, tz + math.sin(a) * 9),
                 (C + math.cos(a) * 14, 1, C + math.sin(a) * 14 - 4), (C + math.cos(a + 0.4) * 20, 0, C + math.sin(a + 0.4) * 20)],
                'oak_wood[axis=y]', r0=1.6, r1=0.5)
    lv = S('oak_leaves', distance='1', persistent='true', waterlogged='false')
    az = S('flowering_azalea_leaves', distance='1', persistent='true', waterlogged='false')
    g.sphere(tx, 42, tz + 6, 13, lv, squash=0.5)
    for k in range(8):
        a = k / 8 * 2 * math.pi
        end = (tx + math.cos(a) * 17, 30 + k % 3 * 3, tz + 6 + math.sin(a) * 17)
        g.line((tx, 26 + k % 3 * 3, tz), end, 'oak_wood[axis=y]', r=0.9)
        g.sphere(*end, 5, az if k % 2 else lv, squash=0.6)
        g.set(round(end[0]), round(end[1]) - 2, round(end[2]), 'shroomlight')
    for k in range(10):
        a = k * 2.1
        g.set(round(tx + math.cos(a) * 9), 39, round(tz + 6 + math.sin(a) * 9), 'shroomlight')
    g.scatter(2, 2, W - 3, W - 3, 1, ['cornflower', 'oxeye_daisy', 'lily_of_the_valley', 'short_grass', 'pink_petals[facing=north,flower_amount=3]'],
              density=0.2, need='moss_block')


# ---------------------------------------------------------------- 34
def miyohime(g):
    """万律自在神 御世姫命 (playful, small; indigo and violet; a halo, a crown, crystals; the kagura bell, gravity turned upside
    down, the divine-age script): 「神楽の御社」, in the End. A shrine: a row of vermilion torii up a stone path lit by
    stone lanterns, the kagura stage with its red rails where the seal lies, the main shrine behind with crossed roof
    beams and a sacred rope, bells, and rocks floating where gravity has been undone."""
    g.floor_block = 'minecraft:stripped_cherry_wood'
    plaza(g, 25, lambda x, z, d: 'gravel' if False else ('polished_andesite' if abs(x - C) <= 2 else 'end_stone_bricks'), clear_h=22)
    for z in range(C + 9, W - 2, 4):
        g.torii(C, z, 1, 7, 7, axis='x', post='red_concrete', beam='black_concrete')
    for z in range(C + 10, W - 2, 4):
        toro(g, C - 5, z, 1, stone='stone_bricks')
        toro(g, C + 5, z, 1, stone='stone_bricks')
    g.seal_y = 2
    g.box(C - 7, 0, C - 7, C + 7, 1, C + 7, 'stripped_cherry_wood')
    for k in range(-7, 8):
        for (x, z) in ((C + k, C - 7), (C + k, C + 7), (C - 7, C + k), (C + 7, C + k)):
            if not (z == C + 7 and abs(k) < 2):
                g.set(x, 2, z, 'crimson_fence')
    for (x, z) in ((C - 7, C - 7), (C + 7, C - 7), (C - 7, C + 7), (C + 7, C + 7)):
        g.column(x, z, 2, 4, 'red_concrete')
        g.set(x, 5, z, lantern())
    # the main shrine
    x0, x1, z0, z1 = C - 7, C + 7, 2, 11
    g.box(x0, 0, z0, x1, 2, z1, 'stone_bricks')
    g.box(x0 + 1, 3, z0 + 1, x1 - 1, 8, z1 - 1, 'white_concrete', hollow=True)
    g.box(x0 + 2, 3, z0 + 2, x1 - 2, 8, z1 - 2, AIR)
    for x in range(x0 + 1, x1, 3):
        g.column(x, z1 - 1, 3, 8, 'red_concrete')
    for x in (C - 1, C, C + 1):
        for y in (3, 4, 5):
            g.set(x, y, z1 - 1, AIR)
    yr = g.roof_hip(x0 + 1, z0 + 1, x1 - 1, z1 - 1, 9, 'dark_oak_stairs', 'dark_oak_planks', flare=2)
    for side in (-1, 1):
        g.line((x0 + 1, 12, (z0 + z1) // 2 + side * 0), (x0 - 1, 16, (z0 + z1) // 2), 'dark_oak_planks')
        g.line((x1 - 1, 12, (z0 + z1) // 2), (x1 + 1, 16, (z0 + z1) // 2), 'dark_oak_planks')
    for x in range(x0, x1 + 1):
        g.set(x, 8, z1, 'white_wool')
    for x in (C - 3, C + 3):
        g.set(x, 7, z1, 'bell[attachment=ceiling,facing=south,powered=false]')
    g.stairs_up(C, z1 + 3, 0, 3, 'stone_brick_stairs', 'north', width=5, fill='stone_bricks')
    for k in range(10):
        a = k * 2.3
        x, z, y = C + math.cos(a) * 17, C + math.sin(a) * 17, 14 + k % 4 * 3
        g.sphere(x, y, z, 1.6 + k % 3 * 0.5, 'end_stone' if k % 2 else 'purpur_block')
        if k % 3 == 0:
            g.set(round(x), y + 2, round(z), 'amethyst_cluster[facing=up,waterlogged=false]')
    halo(g, C, 24, C, 8, 'purple_stained_glass', thick=0.4)


# ---------------------------------------------------------------- 35
def innocence(g):
    """無垢なる全能 (playful, small; white and lilac; a halo, crystals; stuffed toys marching, the toy box, the playroom her
    legend turns the field into): 「おもちゃの部屋」. A giant playroom: a floor of wooden boards with a round rug, building
    blocks stacked, a teddy bear as tall as a house, an open toy box, a big ball, a rainbow arch."""
    g.floor_block = 'minecraft:birch_planks'
    plaza(g, 25, lambda x, z, d: ('pink_wool' if int(d) % 4 < 2 else 'white_wool') if d < 11 else ('birch_planks' if x % 4 else 'oak_planks'),
          clear_h=22)
    cols = ['red_concrete', 'yellow_concrete', 'blue_concrete', 'lime_concrete', 'pink_concrete', 'light_blue_concrete']
    for i, (x, z, y) in enumerate(((C - 18, C + 10, 1), (C - 14, C + 10, 1), (C - 16, C + 10, 5), (C - 18, C + 14, 1), (C + 17, C - 14, 1),
                                   (C + 13, C - 14, 1), (C + 15, C - 14, 5), (C + 15, C - 14, 9))):
        g.box(x - 1, y, z - 1, x + 2, y + 3, z + 2, cols[i % len(cols)])
        g.set(x, y + 1, z + 3, 'white_concrete'); g.set(x + 1, y + 2, z + 3, 'white_concrete')
    # the bear
    bx, bz = C - 15, C - 12
    g.sphere(bx, 6, bz, 5, 'brown_wool', squash=1.2)
    g.sphere(bx, 14, bz, 4, 'brown_wool')
    for s in (-1, 1):
        g.sphere(bx + s * 3, 17.5, bz, 1.5, 'brown_wool')
        g.sphere(bx + s * 5, 5, bz + 2, 1.8, 'brown_wool')
        g.sphere(bx + s * 2.5, 1.5, bz + 3, 2, 'brown_wool')
        g.set(bx + s * 2, 15, bz + 4, 'black_concrete')
    g.sphere(bx, 13, bz + 3.5, 1.5, 'white_wool')
    g.set(bx, 13, bz + 5, 'black_concrete')
    g.box(bx - 2, 10, bz + 3, bx + 2, 10, bz + 4, 'pink_wool')
    # the toy box, open
    tx, tz = C + 15, C + 12
    g.box(tx - 4, 1, tz - 3, tx + 4, 6, tz + 3, 'spruce_planks', hollow=True)
    g.box(tx - 3, 2, tz - 2, tx + 3, 6, tz + 2, AIR)
    g.box(tx - 4, 7, tz - 4, tx + 4, 13, tz - 4, 'spruce_planks')
    g.sphere(tx - 1, 6, tz, 1.5, 'red_wool'); g.sphere(tx + 2, 6, tz + 1, 1.2, 'yellow_wool')
    # the ball and the rainbow
    g.sphere(C + 16, 3, C - 2, 3, 'red_concrete')
    g.ring(C + 16, C - 2, 2.5, 3.2, 3, 'white_concrete')
    for k, c in enumerate(('red_wool', 'orange_wool', 'yellow_wool', 'lime_wool', 'light_blue_wool', 'purple_wool')):
        r = 21 - k
        for i in range(int(r * 6)):
            t = i / (r * 6) * math.pi
            g.set(round(C + math.cos(t) * r), round(math.sin(t) * r * 0.9), 4, c)
    halo(g, C, 24, C, 6, 'white_stained_glass', thick=0.4)


# ---------------------------------------------------------------- 36
def brutality(g):
    """凄惨たる暴虐 (violent; soot black and fire red; claws, marks; the oni's iron club, fists that crack the bedrock): 「暴虐の
    破砕場」. A smashed quarry: a floor split by glowing cracks, pillars broken off, boulders flung about, red war banners on
    posts, and the iron club with its spikes driven into the ground."""
    g.floor_block = 'minecraft:cobbled_deepslate'
    plaza(g, 25, lambda x, z, d: 'cracked_deepslate_bricks' if (x * 7 + z * 3) % 4 == 0 else 'cobbled_deepslate', clear_h=20)
    for k in range(7):
        a = k / 7 * 2 * math.pi + 0.3
        p = (C + math.cos(a) * 5, 0, C + math.sin(a) * 5)
        q = (C + math.cos(a + 0.2) * 23, 0, C + math.sin(a + 0.2) * 23)
        g.line(p, q, 'magma_block')
    for k in range(10):
        a = k / 10 * 2 * math.pi
        x, z = round(C + math.cos(a) * 18), round(C + math.sin(a) * 18)
        h = 4 + (k * 7) % 9
        g.cyl(x, z, 1.3, 1, h, 'deepslate_bricks')
        g.set(x + 1, h + 1, z, 'cracked_deepslate_bricks')
        if k % 3 == 0:
            g.set(x, h + 1, z, 'red_wool'); g.set(x, h + 2, z, 'red_wool')
    for k in range(8):
        a = k * 1.9
        g.sphere(C + math.cos(a) * 14, 1.5, C + math.sin(a) * 14, 1.5 + k % 3 * 0.6, 'cobblestone')
    cx, cz = C + 14, C - 14
    g.line((cx, 0, cz), (cx - 5, 18, cz + 5), 'iron_block', r=1.6)
    for k in range(6, 18, 2):
        t = k / 18
        x, y, z = cx - 5 * t, 18 * t, cz + 5 * t
        for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            g.set(round(x + dx), round(y), round(z + dz), 'iron_bars')
    g.line((cx - 5, 18, cz + 5), (cx - 6, 22, cz + 6), 'red_concrete', r=0.7)
    for (x, z) in ((C - 20, C + 8), (C + 20, C + 8), (C - 8, C + 21), (C + 8, C + 21)):
        g.column(x, z, 1, 6, 'dark_oak_fence')
        for y in (3, 4, 5):
            g.set(x, y, z + 1, 'red_wool')


# ---------------------------------------------------------------- 37
def cursed_love(g):
    """邪沌の呪詛 (a hazard; near-black and dusky rose; vines; the tragic puppet, white flowers that turn to black roses, the
    garden turned to a curse): 「悲劇の庭園劇場」. A garden cut in two: white flowers on one side, black roses on the other;
    rose pergolas; a little puppet theatre in the north whose great cross-bars hang strings over the stage; a heart split
    in two."""
    g.floor_block = 'minecraft:polished_blackstone_bricks'
    plaza(g, 25, lambda x, z, d: 'grass_block[snowy=false]' if d > 9 else ('quartz_bricks' if x < C else 'polished_blackstone_bricks'), clear_h=22)
    g.scatter(2, 2, C - 1, W - 3, 1, ['lily_of_the_valley', 'oxeye_daisy', 'azure_bluet'], density=0.35, need='grass_block')
    g.scatter(C + 1, 2, W - 3, W - 3, 1, ['wither_rose'], density=0.35, need='grass_block')
    for k in range(5):
        a = math.radians(200 + k * 35)
        x, z = round(C + math.cos(a) * 17), round(C + math.sin(a) * 17)
        g.arch(x - 3, x + 3, z, 1, 5, 'dark_oak_log[axis=y]')
        for t in (-3, 3):
            g.set(x + t, 1, z + 1, 'rose_bush[half=lower]'); g.set(x + t, 2, z + 1, 'rose_bush[half=upper]')
    g.box(C - 8, 0, 2, C + 8, 2, 9, 'dark_oak_planks')
    g.box(C - 9, 3, 2, C + 9, 14, 2, 'dark_oak_planks')
    for side in (-1, 1):
        g.box(C + side * 9, 3, 2, C + side * 9, 14, 9, 'dark_oak_planks')
        for y in range(4, 14):
            g.set(C + side * 7, y, 9, 'red_wool'); g.set(C + side * 8, y, 9, 'red_wool')
    g.box(C - 9, 14, 2, C + 9, 15, 9, 'dark_oak_planks')
    for side in (-1, 1):
        g.line((C, 24, C - 4), (C + side * 8, 24, C - 4), 'dark_oak_planks', r=0.6)
        g.line((C, 24, C - 8), (C, 24, C), 'dark_oak_planks', r=0.6)
    for (x, z) in ((C - 8, C - 4), (C + 8, C - 4), (C, C - 8)):
        for y in range(16, 24):
            g.set(x, y, z, 'chain[axis=y]')
    g.column(C, C - 4, 25, 27, 'dark_oak_fence')
    for x in range(C - 5, C + 6):
        for y in range(1, 12):
            u, v = (x - C) / 5.0, (y - 6) / 5.0
            if (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0 and abs(x - C - (y % 2)) > 0:
                g.set(x, y + 14, W - 4, 'red_concrete' if x < C else 'black_concrete')


# ---------------------------------------------------------------- 38
def relentless_research(g):
    """戒進の研究 (a researcher; white coat, mint; a monocle; the great syringe, surgical machines, the isolation ward):
    「隔離研究棟」. A white laboratory compound round an observation court: wards of white walls and glass, isolation
    cylinders of green glass, an operating table under lamps, mint lights, and a giant syringe leaning on the roof."""
    g.floor_block = 'minecraft:white_concrete'
    plaza(g, 25, lambda x, z, d: 'white_concrete' if (x + z) % 2 else 'light_gray_concrete', clear_h=20)
    for x in range(1, W - 1):
        for z in range(1, W - 1):
            d = math.hypot(x - C, z - C)
            if 17 <= d <= 24 and not (abs(x - C) <= 2 and z > C):
                edge = d < 17.8 or d > 23.3
                for y in range(1, 9):
                    g.set(x, y, z, ('white_concrete' if y not in (4, 5) or d > 23.3 else 'glass_pane') if edge else AIR)
                g.set(x, 9, z, 'smooth_quartz')
                if edge and d < 17.8 and int(math.degrees(math.atan2(z - C, x - C))) % 30 == 0:
                    for y in (1, 2, 3):
                        g.set(x, y, z, AIR)
    for k in range(8):
        a = k / 8 * 2 * math.pi + 0.2
        x, z = round(C + math.cos(a) * 13), round(C + math.sin(a) * 13)
        if z > C + 8 and abs(x - C) < 5:
            continue
        g.cyl(x, z, 1.6, 1, 6, 'lime_stained_glass', hollow=True)
        g.set(x, 1, z, 'verdant_froglight')
        g.disc(x, z, 1.6, 7, 'iron_block')
        g.disc(x, z, 1.6, 0, 'iron_block')
    g.box(C - 2, 1, C - 12, C + 2, 1, C - 10, 'iron_block')
    g.set(C, 5, C - 11, lantern(hanging=True)); g.set(C, 6, C - 11, 'chain[axis=y]'); g.set(C, 7, C - 11, 'chain[axis=y]')
    g.column(C - 3, C - 11, 1, 7, 'iron_bars'); g.set(C - 3, 8, C - 11, 'iron_block'); g.line((C - 3, 8, C - 11), (C, 8, C - 11), 'iron_block')
    sx, sz = C + 20, C - 8
    g.line((sx, 10, sz), (sx - 9, 26, sz - 3), 'white_stained_glass', r=1.6)
    g.line((sx, 10, sz), (sx - 9, 26, sz - 3), 'lime_stained_glass', r=0.8)
    g.line((sx - 9, 26, sz - 3), (sx - 11, 30, sz - 4), 'iron_block', r=0.5)
    g.line((sx - 11, 30, sz - 4), (sx - 13, 31, sz - 5), 'iron_block', r=1.4)
    g.line((sx, 10, sz), (sx + 2, 6, sz + 1), 'iron_bars')


# ---------------------------------------------------------------- 39
def forbidden_arcana(g):
    """外悪の魔導 (a shapeshifter, a researcher; ink and violet; tentacles, crystals; the chain-blade, the parasite grimoire,
    magic circles that multiply by themselves, a research-circle with no one to cast it): 「禁術の研究陣」. A dark floor
    of runes, magic circles hung one over another in the air, crystal spikes, tentacles, and the grimoire floating in its
    chains."""
    g.floor_block = 'minecraft:polished_deepslate'
    plaza(g, 25, lambda x, z, d: 'crying_obsidian' if (x * 13 + z * 7) % 31 == 0 else ('purple_concrete' if abs(d - 21) < 0.5 else
          ('polished_deepslate' if (x + z) % 2 else 'deepslate_tiles')), clear_h=22)
    for y, r, st in ((17, 11, 'purple_stained_glass'), (22, 8, 'amethyst_block'), (27, 5, 'purple_stained_glass'), (31, 3, 'amethyst_block')):
        halo(g, C, y, C, r, st, thick=0.4)
        for k in range(5):
            a, b = k / 5 * 2 * math.pi, (k + 2) / 5 * 2 * math.pi
            g.line((C + math.cos(a) * r, y, C + math.sin(a) * r), (C + math.cos(b) * r, y, C + math.sin(b) * r), st)
    for k in range(4):
        a = k / 4 * 2 * math.pi + 0.7
        vring(g, C + math.cos(a) * 19, 9, C + math.sin(a) * 19, 4, 'purple_stained_glass', axis='x' if k % 2 else 'z', thick=0.4)
    for k in range(10):
        a = k * 2.5
        x, z = C + math.cos(a) * (12 + k % 4 * 3), C + math.sin(a) * (12 + k % 4 * 3)
        g.line((x, 0, z), (x + math.cos(a) * 1.5, 5 + k % 3 * 2, z + math.sin(a) * 1.5), 'amethyst_block', r=0.9)
    for k in range(5):
        a = k / 5 * 2 * math.pi + 0.3
        x, z = C + math.cos(a) * 16, C + math.sin(a) * 16
        g.curve([(x, 0, z), (x, 7, z), (x - math.cos(a) * 4, 12, z - math.sin(a) * 4)], 'purple_concrete', r0=1.2, r1=0.3)
    gx, gz, gy = C, C - 16, 14
    g.box(gx - 3, gy, gz - 2, gx + 3, gy + 1, gz + 2, 'purple_wool')
    g.box(gx - 3, gy + 2, gz - 2, gx + 3, gy + 2, gz + 2, 'gold_block')
    g.set(gx, gy + 3, gz, 'ochre_froglight')
    for (x, z) in ((gx - 8, gz - 3), (gx + 8, gz - 3), (gx - 7, gz + 5), (gx + 7, gz + 5)):
        g.column(x, z, 1, 4, 'polished_blackstone_bricks')
        g.line((x, 5, z), (gx + (2 if x > gx else -2), gy, gz), 'iron_bars' if False else 'polished_blackstone_wall')


# ---------------------------------------------------------------- 40
def fallen_savior(g):
    """救堕せし勇者 (violent; ash gold and steel; a holy sword, marks; endless rising, the grey sanctuary, the god-slaying
    stroke that reaches heaven): 「灰色の聖域」. The ruin of a chapel in ash grey: broken walls with empty arches, pillars
    fallen in the grass, a headless angel, and in the north the giant holy sword driven into the ground."""
    g.floor_block = 'minecraft:polished_andesite'
    plaza(g, 25, lambda x, z, d: 'cracked_stone_bricks' if (x * 5 + z) % 6 == 0 else ('andesite' if (x + z) % 3 == 0 else 'polished_andesite'),
          clear_h=24)
    for side in (-1, 1):
        x = C + side * 15
        for z in range(6, W - 6):
            top = 4 + (z * 5 + side * 3) % 10
            for y in range(1, top):
                win = z % 7 in (3, 4) and 3 <= y <= 8
                g.set(x, y, z, AIR if win else ('tuff_bricks' if y % 4 else 'chiseled_tuff_bricks'))
    for k in range(4):
        a = k * 1.6 + 0.5
        x, z = C + math.cos(a) * 19, C + math.sin(a) * 19
        g.line((x, 1, z), (x + math.cos(a + 1.5) * 8, 1, z + math.sin(a + 1.5) * 8), 'polished_tuff', r=1.2)
    g.box(C + 17, 1, C + 10, C + 19, 2, C + 12, 'tuff_bricks')
    g.box(C + 17, 3, C + 11, C + 19, 8, C + 11, 'calcite')
    for side in (-1, 1):
        g.curve([(C + 18 + side, 7, C + 11), (C + 18 + side * 5, 11, C + 12), (C + 18 + side * 6, 4, C + 12)], 'calcite', r0=0.8, r1=0.3)
    g.sword(C, 6, 0, 22, blade='white_concrete', edge='yellow_stained_glass', guard='gold_block', grip='light_gray_wool', pommel='gold_block', axis='x')
    g.box(C - 5, 0, 3, C + 5, 1, 9, 'cracked_stone_bricks')
    g.scatter(2, 2, W - 3, W - 3, 1, ['dead_bush', 'short_grass'], density=0.04)


# ---------------------------------------------------------------- 41
def sweet_pact(g):
    """甘契の未怪 (a merchant; smoke grey and honey gold; the scales of future debts, the honeyed contract, the crown of debts):
    「契約の天秤市」. A night bazaar in a ring of striped stalls under strings of lanterns, honey-gold paving, scrolls of
    contract sealed in red, coins in heaps, and in the north a giant golden balance that weighs what is owed."""
    g.floor_block = 'minecraft:yellow_terracotta'
    plaza(g, 25, lambda x, z, d: 'honeycomb_block' if abs(d - 10) < 0.6 else ('yellow_terracotta' if (x + z) % 2 else 'gray_terracotta'), clear_h=22)
    for k in range(10):
        a = math.radians(30 + k * 30)
        x, z = round(C + math.cos(a) * 19), round(C + math.sin(a) * 19)
        g.box(x - 2, 1, z - 2, x + 2, 1, z + 2, 'spruce_planks')
        for (cx, cz) in ((x - 2, z - 2), (x + 2, z - 2), (x - 2, z + 2), (x + 2, z + 2)):
            g.column(cx, cz, 2, 4, 'spruce_fence')
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                g.set(x + dx, 5, z + dz, 'red_wool' if (dx + 3) % 2 else 'white_wool')
        g.set(x, 4, z, lantern(hanging=True))
        g.set(x, 2, z, 'barrel[facing=up,open=false]')
    sx, sz = C, 6
    g.box(sx - 2, 1, sz - 2, sx + 2, 2, sz + 2, 'gold_block')
    g.column(sx, sz, 3, 22, 'gold_block')
    g.box(sx - 12, 22, sz, sx + 12, 22, sz, 'gold_block')
    g.sphere(sx, 23, sz, 1.5, 'gold_block')
    for side in (-1, 1):
        px = sx + side * 12
        for y in range(10, 22):
            g.set(px, y, sz, 'chain[axis=y]')
        g.disc(px, sz, 3, 9, 'gold_block')
        g.ring(px, sz, 2.6, 3.1, 10, 'gold_block')
        if side < 0:
            g.sphere(px, 10.5, sz, 1.5, 'raw_gold_block')
    for k in range(6):
        a = k * 1.1 + 0.4
        x, z = round(C + math.cos(a) * 13), round(C + math.sin(a) * 13)
        g.box(x, 1, z, x + 2, 1, z, 'white_wool')
        g.set(x + 1, 2, z, 'red_concrete')
        g.set(x - 1, 1, z + 1, 'gold_block'); g.set(x - 1, 2, z + 1, 'light_weighted_pressure_plate[power=0]')
    for i in range(40):
        t = i / 40 * 2 * math.pi
        g.set(round(C + math.cos(t) * 16), 9, round(C + math.sin(t) * 16), 'chain[axis=x]' if False else 'yellow_stained_glass')
    for k in range(8):
        t = k / 8 * 2 * math.pi
        g.set(round(C + math.cos(t) * 16), 8, round(C + math.sin(t) * 16), lantern(hanging=True))

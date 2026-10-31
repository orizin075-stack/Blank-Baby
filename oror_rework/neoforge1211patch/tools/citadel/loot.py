"""loot.py: what the Grand Citadel's containers hold, as 1.20.1 item lists for a block entity's Items.

items(theme, seed) gives a container's stacks for a theme (a house barrel by its room, a castle storeroom by its
floor, the royal treasury, the forbidden vault): each line of the theme is taken with its chance, with a count between
its bounds, into distinct random slots. Enchanted books carry one enchantment and potions one effect, chosen with the
same seed. Values are Python data for anvil_edit (('byte', v) and ('short', v) for the narrow NBT numbers).
"""
import random

# item, least, most, chance
THEMES = {
    # the town: a barrel's goods by the room it stands in
    'home': [('bread', 3, 12, .8), ('potato', 4, 16, .5), ('carrot', 4, 16, .5), ('apple', 2, 8, .5), ('wheat', 4, 16, .4),
             ('cooked_cod', 2, 6, .3), ('torch', 4, 16, .4), ('coal', 3, 12, .4), ('string', 2, 6, .2), ('candle', 1, 3, .2)],
    'bedroom': [('white_wool', 2, 6, .5), ('string', 2, 8, .4), ('book', 1, 3, .4), ('candle', 1, 4, .4), ('leather', 1, 4, .3),
                ('paper', 2, 8, .3), ('apple', 1, 4, .4), ('emerald', 1, 3, .2)],
    'forge': [('iron_ingot', 3, 10, .8), ('coal', 6, 20, .8), ('iron_nugget', 6, 24, .5), ('raw_iron', 3, 9, .4), ('gold_nugget', 3, 12, .3),
              ('flint', 2, 8, .3), ('iron_sword', 1, 1, .2), ('iron_pickaxe', 1, 1, .2)],
    'jewel': [('gold_ingot', 2, 6, .6), ('gold_nugget', 6, 24, .7), ('emerald', 2, 6, .5), ('amethyst_shard', 3, 10, .5), ('lapis_lazuli', 4, 12, .5),
              ('diamond', 1, 2, .15), ('quartz', 4, 16, .4)],
    'bakery': [('wheat', 8, 32, .8), ('bread', 6, 18, .8), ('sugar', 4, 16, .6), ('egg', 3, 12, .6), ('cookie', 6, 16, .5),
               ('pumpkin_pie', 1, 4, .4), ('cocoa_beans', 3, 9, .3)],
    'butchery': [('beef', 3, 10, .7), ('porkchop', 3, 10, .7), ('mutton', 3, 8, .5), ('chicken', 3, 8, .5), ('leather', 2, 6, .5),
                 ('rabbit_hide', 1, 4, .3), ('salmon', 2, 6, .3), ('coal', 4, 12, .4)],
    'tailor': [('white_wool', 6, 24, .8), ('red_wool', 2, 8, .4), ('blue_wool', 2, 8, .4), ('yellow_wool', 2, 8, .3), ('string', 4, 16, .7),
               ('white_dye', 2, 8, .4), ('red_dye', 2, 6, .3), ('shears', 1, 1, .3)],
    'alchemy': [('glass_bottle', 4, 12, .8), ('nether_wart', 4, 16, .7), ('redstone', 4, 16, .6), ('glowstone_dust', 4, 12, .5),
                ('sugar', 2, 8, .4), ('spider_eye', 1, 4, .4), ('blaze_powder', 1, 4, .3), ('potion', 1, 1, .5)],
    'library': [('book', 3, 10, .8), ('paper', 6, 20, .8), ('feather', 3, 10, .5), ('ink_sac', 2, 8, .5), ('writable_book', 1, 1, .3),
                ('enchanted_book', 1, 1, .15), ('lapis_lazuli', 2, 8, .3)],
    'maps': [('paper', 8, 24, .8), ('map', 1, 3, .7), ('compass', 1, 1, .5), ('ink_sac', 2, 6, .5), ('glass_pane', 2, 8, .4), ('feather', 2, 6, .3)],
    'stable': [('wheat', 8, 24, .8), ('apple', 3, 10, .6), ('carrot', 4, 12, .5), ('leather', 2, 8, .6), ('lead', 1, 3, .5), ('saddle', 1, 1, .3),
               ('hay_block', 1, 4, .4)],
    'market': [('emerald', 2, 8, .6), ('apple', 4, 12, .5), ('melon_slice', 6, 16, .4), ('pumpkin', 1, 4, .4), ('bricks', 8, 32, .4),
               ('stone', 8, 32, .4), ('glass', 4, 16, .3), ('terracotta', 4, 16, .3)],
    'guild': [('arrow', 12, 40, .8), ('flint', 4, 12, .6), ('stick', 8, 24, .6), ('feather', 4, 16, .6), ('bow', 1, 1, .3), ('crossbow', 1, 1, .3),
              ('string', 3, 9, .4)],
    'taproom': [('honey_bottle', 2, 8, .7), ('sweet_berries', 6, 16, .6), ('bread', 4, 12, .6), ('cooked_porkchop', 3, 8, .5),
                ('glow_berries', 4, 12, .4), ('apple', 3, 8, .4), ('cookie', 4, 12, .3)],
    'storage': [('coal', 6, 20, .5), ('torch', 6, 24, .5), ('oak_planks', 8, 32, .4), ('cobblestone', 8, 32, .4), ('bread', 2, 8, .4),
                ('string', 2, 6, .3), ('iron_ingot', 1, 4, .2), ('leather', 1, 4, .3)],
    'shed': [('wheat_seeds', 6, 24, .7), ('bone_meal', 4, 16, .6), ('iron_hoe', 1, 1, .3), ('iron_shovel', 1, 1, .3), ('coal', 3, 12, .4),
             ('torch', 4, 12, .4), ('oak_sapling', 1, 4, .3), ('carrot', 3, 9, .3)],
    # the old mines under the outer walls
    'mine': [('torch', 8, 32, .8), ('coal', 6, 24, .7), ('raw_iron', 3, 12, .5), ('raw_copper', 4, 16, .4), ('rail', 6, 24, .4),
             ('iron_pickaxe', 1, 1, .3), ('bread', 3, 9, .5), ('ladder', 4, 16, .4), ('redstone', 4, 12, .2), ('gold_nugget', 4, 16, .2)],
    # the castle
    'armory': [('iron_sword', 1, 1, .6), ('crossbow', 1, 1, .5), ('bow', 1, 1, .4), ('arrow', 16, 48, .8), ('shield', 1, 1, .5),
               ('iron_helmet', 1, 1, .3), ('iron_chestplate', 1, 1, .3), ('iron_leggings', 1, 1, .3), ('iron_boots', 1, 1, .3),
               ('iron_ingot', 4, 12, .5), ('spectral_arrow', 4, 16, .2)],
    'pantry': [('bread', 8, 24, .8), ('cooked_beef', 6, 16, .6), ('baked_potato', 8, 16, .5), ('apple', 6, 16, .5), ('golden_carrot', 4, 10, .4),
               ('pumpkin_pie', 2, 6, .4), ('honey_bottle', 2, 6, .4), ('cooked_mutton', 6, 12, .4), ('cake', 1, 1, .2)],
    'keep': [('iron_ingot', 4, 12, .6), ('gold_ingot', 3, 9, .5), ('diamond', 1, 3, .15), ('emerald', 3, 10, .5), ('golden_apple', 1, 2, .3),
             ('ender_pearl', 1, 4, .3), ('book', 2, 6, .4), ('enchanted_book', 1, 1, .2), ('potion', 1, 1, .4), ('experience_bottle', 4, 12, .3),
             ('lapis_lazuli', 6, 18, .4), ('redstone', 8, 24, .3)],
    'royal': [('gold_ingot', 8, 24, .8), ('gold_block', 1, 4, .5), ('diamond', 3, 8, .6), ('emerald', 8, 20, .6), ('golden_apple', 2, 4, .5),
              ('enchanted_book', 1, 1, .6), ('enchanted_golden_apple', 1, 1, .15), ('experience_bottle', 8, 16, .5), ('potion', 1, 1, .4)],
    'treasury': [('gold_block', 4, 12, .9), ('diamond', 8, 20, .8), ('diamond_block', 1, 3, .5), ('emerald_block', 2, 6, .7),
                 ('gold_ingot', 16, 48, .8), ('enchanted_golden_apple', 1, 2, .4), ('enchanted_book', 1, 1, .8), ('enchanted_book', 1, 1, .5),
                 ('totem_of_undying', 1, 1, .3), ('netherite_ingot', 1, 2, .3), ('amethyst_shard', 8, 24, .4)],
    'vault': [('netherite_ingot', 2, 4, .9), ('netherite_scrap', 4, 8, .7), ('diamond_block', 2, 6, .9), ('emerald_block', 4, 10, .8),
              ('gold_block', 8, 24, .9), ('enchanted_golden_apple', 2, 4, .8), ('totem_of_undying', 1, 1, .7), ('enchanted_book', 1, 1, .9),
              ('enchanted_book', 1, 1, .9), ('enchanted_book', 1, 1, .6), ('echo_shard', 4, 12, .6), ('nether_star', 1, 1, .3), ('elytra', 1, 1, .2),
              ('heart_of_the_sea', 1, 1, .3), ('trident', 1, 1, .2)],
}
SINGLE = {'iron_sword', 'iron_pickaxe', 'iron_hoe', 'iron_shovel', 'shears', 'bow', 'crossbow', 'shield', 'saddle', 'iron_helmet', 'iron_chestplate',
          'iron_leggings', 'iron_boots', 'enchanted_book', 'potion', 'writable_book', 'totem_of_undying', 'elytra', 'trident', 'cake', 'compass'}
SIXTEEN = {'ender_pearl', 'honey_bottle', 'egg', 'snowball'}
BOOKS = [('mending', 1), ('unbreaking', 3), ('protection', 4), ('sharpness', 5), ('efficiency', 5), ('fortune', 3), ('looting', 3),
         ('feather_falling', 4), ('power', 5), ('silk_touch', 1), ('respiration', 3), ('depth_strider', 3)]
POTIONS = ['healing', 'strong_healing', 'regeneration', 'strength', 'fire_resistance', 'swiftness', 'night_vision']


def items(theme, seed):
    rng = random.Random(int(seed))
    lines = THEMES[theme]
    chosen = [l for l in lines if rng.random() < l[3]]
    if len(chosen) < 2:
        chosen = rng.sample(lines, 2)
    slots = rng.sample(range(27), min(27, len(chosen)))
    out = []
    for (name, lo, hi, _), slot in zip(chosen, slots):
        n = rng.randint(lo, hi)
        n = 1 if name in SINGLE else min(n, 16) if name in SIXTEEN else min(n, 64)
        stack = {'Slot': ('byte', slot), 'id': 'minecraft:' + name, 'Count': ('byte', n)}
        if name == 'enchanted_book':
            ench, lvl = rng.choice(BOOKS)
            stack['tag'] = {'StoredEnchantments': [{'id': 'minecraft:' + ench, 'lvl': ('short', lvl)}]}
        elif name == 'potion':
            stack['tag'] = {'Potion': 'minecraft:' + rng.choice(POTIONS)}
        out.append(stack)
    return sorted(out, key=lambda s: s['Slot'][1])

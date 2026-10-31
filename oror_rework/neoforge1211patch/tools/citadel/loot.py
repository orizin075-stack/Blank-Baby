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
    'royal': [('gold_ingot', 16, 48, .9), ('gold_block', 2, 8, .6), ('diamond', 6, 16, .7), ('emerald_block', 2, 8, .5), ('golden_apple', 2, 6, .6),
              ('enchanted_book+', 1, 1, .7), ('enchanted_golden_apple', 1, 2, .25), ('experience_bottle', 16, 48, .5), ('potion', 1, 1, .4),
              ('oror_supreme_bosses:mana_crystal', 1, 4, .3), ('oror_supreme_bosses:purifying_dew', 1, 3, .3),
              ('irons_spellbooks:arcane_essence', 8, 24, .4), ('irons_spellbooks:rare_ink', 2, 6, .3), ('apotheosis:arcane_sands', 2, 6, .3),
              ('iceandfire:silver_ingot', 6, 16, .3), ('iceandfire:sapphire_gem', 2, 6, .3), ('waystones:warp_stone', 1, 1, .15)],
    # the royal treasury under the throne: the kingdom's wealth
    'treasury': [('gold_block', 32, 64, 1), ('diamond_block', 8, 24, .9), ('emerald_block', 16, 48, .9), ('netherite_ingot', 4, 12, .8),
                 ('netherite_block', 1, 2, .3), ('enchanted_golden_apple', 4, 12, .8), ('totem_of_undying', 1, 1, .7), ('totem_of_undying', 1, 1, .4),
                 ('elytra', 1, 1, .3), ('nether_star', 1, 3, .5), ('beacon', 1, 1, .3), ('heart_of_the_sea', 1, 1, .3), ('experience_bottle', 64, 64, .6),
                 ('enchanted_book+', 1, 1, 1), ('enchanted_book+', 1, 1, .8), ('enchanted_book+', 1, 1, .6),
                 ('netherite_sword+', 1, 1, .35), ('netherite_pickaxe+', 1, 1, .3), ('netherite_helmet+', 1, 1, .25), ('netherite_chestplate+', 1, 1, .25),
                 ('netherite_leggings+', 1, 1, .25), ('netherite_boots+', 1, 1, .25), ('bow+', 1, 1, .2), ('trident+', 1, 1, .15),
                 ('relic:charm', 1, 1, .5), ('relic:focus', 1, 1, .4),
                 ('oror_supreme_bosses:villager_king_token', 1, 1, .25), ('oror_supreme_bosses:star_shard', 1, 4, .6),
                 ('oror_supreme_bosses:dragon_core', 1, 1, .3), ('oror_supreme_bosses:mana_crystal', 2, 8, .7), ('oror_supreme_bosses:world_thread', 1, 2, .3),
                 ('oror_supreme_bosses:rewind_talisman', 1, 1, .2), ('oror_supreme_bosses:last_bloom', 1, 1, .2), ('oror_supreme_bosses:purifying_dew', 2, 6, .5),
                 ('irons_spellbooks:legendary_ink', 2, 6, .5), ('irons_spellbooks:epic_ink', 2, 8, .5), ('irons_spellbooks:arcane_essence', 16, 48, .7),
                 ('irons_spellbooks:upgrade_orb', 1, 3, .4), ('irons_spellbooks:netherite_spell_book', 1, 1, .15),
                 ('iceandfire:dragonsteel_fire_ingot', 4, 12, .4), ('iceandfire:dragonsteel_ice_ingot', 4, 12, .4),
                 ('iceandfire:dragonsteel_lightning_ingot', 4, 12, .3), ('alexscaves:azure_neodymium_ingot', 8, 24, .35),
                 ('alexscaves:scarlet_neodymium_ingot', 8, 24, .35), ('alexscaves:pure_darkness', 1, 4, .25), ('apotheosis:godforged_pearl', 2, 6, .4),
                 ('apotheosis:arcane_sands', 8, 24, .4), ('waystones:warp_stone', 1, 1, .4), ('sophisticatedbackpacks:netherite_backpack', 1, 1, .15)],
    # the forbidden vault deep under the town: what the kingdom keeps from the world
    'vault': [('netherite_block', 2, 6, .9), ('netherite_ingot', 16, 32, .9), ('diamond_block', 24, 64, 1), ('emerald_block', 32, 64, .9),
              ('gold_block', 64, 64, .9), ('enchanted_golden_apple', 16, 32, 1), ('totem_of_undying', 1, 1, 1), ('totem_of_undying', 1, 1, .9),
              ('totem_of_undying', 1, 1, .6), ('elytra', 1, 1, .6), ('nether_star', 2, 6, .9), ('beacon', 1, 2, .7), ('heart_of_the_sea', 1, 2, .6),
              ('dragon_head', 1, 1, .2), ('enchanted_book+', 1, 1, 1), ('enchanted_book+', 1, 1, 1), ('enchanted_book+', 1, 1, .8),
              ('enchanted_book+', 1, 1, .6), ('netherite_sword+', 1, 1, .7), ('netherite_axe+', 1, 1, .4), ('netherite_pickaxe+', 1, 1, .5),
              ('netherite_helmet+', 1, 1, .5), ('netherite_chestplate+', 1, 1, .5), ('netherite_leggings+', 1, 1, .5), ('netherite_boots+', 1, 1, .5),
              ('bow+', 1, 1, .4), ('crossbow+', 1, 1, .3), ('trident+', 1, 1, .4),
              ('relic:weapon', 1, 1, .9), ('relic:legend', 1, 1, .8), ('relic:charm', 1, 1, .6), ('relic:focus', 1, 1, .6),
              ('oror_supreme_bosses:villager_king_token', 1, 1, .4), ('oror_supreme_bosses:star_shard', 4, 12, .9),
              ('oror_supreme_bosses:dragon_core', 1, 2, .7), ('oror_supreme_bosses:forge_core', 1, 2, .5), ('oror_supreme_bosses:world_thread', 1, 3, .6),
              ('oror_supreme_bosses:rewind_talisman', 1, 1, .5), ('oror_supreme_bosses:last_bloom', 1, 1, .5), ('oror_supreme_bosses:curse_residue', 1, 4, .4),
              ('oror_supreme_bosses:mana_crystal', 8, 24, .9), ('oror_supreme_bosses:azure_blade', 1, 1, .25), ('oror_supreme_bosses:star_staff', 1, 1, .25),
              ('oror_supreme_bosses:reverie_rapier', 1, 1, .25), ('oror_supreme_bosses:dragon_coat', 1, 1, .2), ('oror_supreme_bosses:teia_boots', 1, 1, .2),
              ('irons_spellbooks:legendary_ink', 8, 16, .9), ('irons_spellbooks:arcane_essence', 48, 64, .9), ('irons_spellbooks:upgrade_orb', 2, 6, .8),
              ('irons_spellbooks:netherite_spell_book', 1, 1, .5), ('iceandfire:dragonsteel_fire_ingot', 12, 32, .7),
              ('iceandfire:dragonsteel_ice_ingot', 12, 32, .7), ('iceandfire:dragonsteel_lightning_ingot', 12, 32, .7),
              ('iceandfire:fire_dragon_heart', 1, 1, .4), ('iceandfire:ice_dragon_heart', 1, 1, .4), ('iceandfire:lightning_dragon_heart', 1, 1, .4),
              ('alexscaves:pure_darkness', 4, 12, .6), ('alexscaves:azure_neodymium_ingot', 24, 64, .6), ('alexscaves:scarlet_neodymium_ingot', 24, 64, .6),
              ('apotheosis:godforged_pearl', 8, 24, .8), ('waystones:warp_stone', 1, 1, .7), ('sophisticatedbackpacks:netherite_backpack', 1, 1, .5)],
}
# relics of the 41 characters (oror_supreme_bosses:<name>_weapon / _focus / _charm / _legend)
RELIC_OWNERS = ['ain_sof_aur', 'angra_mainyu', 'arcana', 'bahamut', 'berit', 'brutality', 'chaos', 'cursed_love', 'demiurgos', 'elseria', 'enkou',
                'eomaia', 'fallen_savior', 'ferdinand', 'forbidden_arcana', 'gokuka', 'hakyoku', 'hephaistos', 'huang_linghua', 'innocence',
                'kokuhaku', 'kurma', 'lucifara', 'magna_mater', 'mary_sue', 'mels', 'merlinus', 'miyohime', 'nortia', 'nun', 'ouroboros',
                'relentless_research', 'riha', 'savior', 'shinra', 'sweet_pact', 'taika', 'teia', 'tenki', 'valeria', 'yggdrasil']
# the best enchantments of each piece of gear ('<item>+' in a theme)
GEAR = {'netherite_sword': [('sharpness', 5), ('looting', 3), ('unbreaking', 3), ('mending', 1), ('fire_aspect', 2), ('sweeping', 3)],
        'netherite_axe': [('sharpness', 5), ('efficiency', 5), ('unbreaking', 3), ('mending', 1)],
        'netherite_pickaxe': [('efficiency', 5), ('fortune', 3), ('unbreaking', 3), ('mending', 1)],
        'netherite_helmet': [('protection', 4), ('respiration', 3), ('aqua_affinity', 1), ('unbreaking', 3), ('mending', 1)],
        'netherite_chestplate': [('protection', 4), ('unbreaking', 3), ('mending', 1)],
        'netherite_leggings': [('protection', 4), ('unbreaking', 3), ('mending', 1)],
        'netherite_boots': [('protection', 4), ('feather_falling', 4), ('depth_strider', 3), ('unbreaking', 3), ('mending', 1)],
        'bow': [('power', 5), ('punch', 2), ('flame', 1), ('infinity', 1), ('unbreaking', 3)],
        'crossbow': [('quick_charge', 3), ('multishot', 1), ('unbreaking', 3), ('mending', 1)],
        'trident': [('loyalty', 3), ('impaling', 5), ('channeling', 1), ('unbreaking', 3), ('mending', 1)]}
SINGLE = {'iron_sword', 'iron_pickaxe', 'iron_hoe', 'iron_shovel', 'shears', 'bow', 'crossbow', 'shield', 'saddle', 'iron_helmet', 'iron_chestplate',
          'iron_leggings', 'iron_boots', 'enchanted_book', 'potion', 'writable_book', 'totem_of_undying', 'elytra', 'trident', 'cake', 'compass',
          'beacon', 'heart_of_the_sea', 'dragon_head', 'netherite_sword', 'netherite_axe', 'netherite_pickaxe', 'netherite_helmet',
          'netherite_chestplate', 'netherite_leggings', 'netherite_boots'}
SIXTEEN = {'ender_pearl', 'honey_bottle', 'egg', 'snowball'}
BOOKS = [('mending', 1), ('unbreaking', 3), ('protection', 4), ('sharpness', 5), ('efficiency', 5), ('fortune', 3), ('looting', 3),
         ('feather_falling', 4), ('power', 5), ('silk_touch', 1), ('respiration', 3), ('depth_strider', 3)]
# the treasure books ('enchanted_book+'): the rarest enchantments at their highest level
GREAT_BOOKS = [('mending', 1), ('protection', 4), ('sharpness', 5), ('efficiency', 5), ('fortune', 3), ('looting', 3), ('swift_sneak', 3),
               ('soul_speed', 3), ('frost_walker', 2), ('silk_touch', 1), ('infinity', 1), ('feather_falling', 4), ('unbreaking', 3)]
POTIONS = ['healing', 'strong_healing', 'regeneration', 'strength', 'fire_resistance', 'swiftness', 'night_vision']


def item_id(name):
    return name if ':' in name else 'minecraft:' + name


def items(theme, seed):
    rng = random.Random(int(seed))
    lines = THEMES[theme]
    chosen = [l for l in lines if rng.random() < l[3]]
    if len(chosen) < 2:
        chosen = rng.sample(lines, 2)
    rng.shuffle(chosen)
    chosen = chosen[:27]
    slots = rng.sample(range(27), len(chosen))
    out = []
    for (name, lo, hi, _), slot in zip(chosen, slots):
        tag = None
        if name.startswith('relic:'):
            name = 'oror_supreme_bosses:' + rng.choice(RELIC_OWNERS) + '_' + name.split(':')[1]
        elif name == 'enchanted_book+':
            name = 'enchanted_book'
            ench, lvl = rng.choice(GREAT_BOOKS)
            tag = {'StoredEnchantments': [{'id': 'minecraft:' + ench, 'lvl': ('short', lvl)}]}
        elif name.endswith('+'):
            name = name[:-1]
            tag = {'Enchantments': [{'id': 'minecraft:' + e, 'lvl': ('short', l)} for e, l in GEAR.get(name, [])]}
        n = rng.randint(lo, hi)
        short = name.split(':')[-1]
        single = short in SINGLE or name.startswith('oror_supreme_bosses:') and short.endswith(('_weapon', '_focus', '_charm', '_legend'))
        n = 1 if single else min(n, 16) if short in SIXTEEN else min(n, 64)
        stack = {'Slot': ('byte', slot), 'id': item_id(name), 'Count': ('byte', n)}
        if name == 'enchanted_book' and tag is None:
            ench, lvl = rng.choice(BOOKS)
            tag = {'StoredEnchantments': [{'id': 'minecraft:' + ench, 'lvl': ('short', lvl)}]}
        elif name == 'potion':
            tag = {'Potion': 'minecraft:' + rng.choice(POTIONS)}
        if tag:
            stack['tag'] = tag
        out.append(stack)
    return sorted(out, key=lambda s: s['Slot'][1])


def mod_items():
    """Every item of another namespace the themes can put in a container (relics of every owner), for the CI check."""
    ids = set()
    for lines in THEMES.values():
        for name, *_ in lines:
            if name.startswith('relic:'):
                ids |= {'oror_supreme_bosses:%s_%s' % (o, name.split(':')[1]) for o in RELIC_OWNERS}
            elif ':' in name:
                ids.add(name)
    return sorted(ids)

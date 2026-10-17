"""Weapon kinds: which relic weapons are katanas, spears, bows, staves... (until v0.17.2 every one was a sword).

Writes assets/oror_supreme_bosses/weapon_kinds.json (read by CharacterRelics) and the tooltip strings in
lang/ja_jp.json + lang/en_us.json. The kind follows the 3D design of the weapon (w3designs.py); the legend
form of a weapon is its awakened shape, so it shares the kind.

  speed  attack-speed modifier (player base 4.0: sword -1.8 = 2.2 swings/s; every relic was -1.6 before kinds)
  mul    attack damage multiplier on the relic's own damage
  reach  entity interaction range bonus (player base 3.0)
  knock  attack knockback bonus
  sweep  sword sweep on full-strength hits
  mode   melee | bolt | gatling | shell | bow | guard   (right-click behaviour)
  shot   damage of one shot / one full-draw arrow, as a multiple of the relic's damage
  gap    ticks between shots
Usage: python3 -I weapon_kinds.py <overlay assets dir>"""
import json, os, sys

NS = 'oror_supreme_bosses'

#        id            speed  mul   reach knock sweep  mode       shot  gap  ja name      ja feel                         en name        en feel
KINDS = [
    ('katana',      -1.6, 1.00, 0.5, 0.0, True,  'melee',   0.0,  0, '刀',       '速い斬撃・なぎ払い',             'Katana',      'quick cuts, sweeping'),
    ('sword',       -1.8, 1.00, 0.0, 0.0, True,  'melee',   0.0,  0, '剣',       'なぎ払い',                       'Sword',       'sweeping'),
    ('greatsword',  -2.5, 1.30, 0.75, 0.5, True, 'melee',   0.0,  0, '大剣',     '重く広い斬撃・なぎ払い',         'Greatsword',  'heavy wide cuts, sweeping'),
    ('scythe',      -2.4, 1.15, 1.5, 0.0, True,  'melee',   0.0,  0, '大鎌',     '長い間合い・なぎ払い',           'Scythe',      'long reach, sweeping'),
    ('chakram',     -1.7, 0.90, 1.0, 0.0, True,  'melee',   0.0,  0, '輪刃',     'やや長い間合い・なぎ払い',       'Chakram',     'longer reach, sweeping'),
    ('rapier',      -1.0, 0.80, 0.5, 0.0, False, 'melee',   0.0,  0, '刺突',     '速い突き・なぎ払い無し',         'Thrust',      'fast thrusts, no sweep'),
    ('polearm',     -2.3, 1.05, 2.0, 0.3, False, 'melee',   0.0,  0, '長柄',     '長い間合いの突き・なぎ払い無し', 'Polearm',     'long-reach thrusts, no sweep'),
    ('heavy',       -2.8, 1.45, 0.0, 1.5, False, 'melee',   0.0,  0, '鈍器',     '遅いが重い一撃・強い吹き飛ばし', 'Heavy',       'slow crushing blows, strong knockback'),
    ('toyhammer',   -2.0, 0.70, 0.0, 3.0, False, 'melee',   0.0,  0, '玩具槌',   '威力控えめ・吹き飛ばし最大',     'Toy Hammer',  'light damage, huge knockback'),
    ('fist',        -0.4, 0.60, -0.5, 0.3, False, 'melee',  0.0,  0, '拳',       '超高速の連打・短い間合い',       'Fist',        'very fast blows, short reach'),
    ('whip',        -2.2, 0.80, 3.0, 0.0, False, 'melee',   0.0,  0, '鞭・鎖',   '最長の間合い・なぎ払い無し',     'Whip / Chain', 'longest reach, no sweep'),
    ('magic',       -2.0, 0.40, 0.0, 0.0, False, 'bolt',    0.75, 10, '魔導具',  '魔弾を撃つ（殴りは弱い）',       'Catalyst',    'fires magic bolts (weak in melee)'),
    ('gatling',     -2.0, 0.35, 0.0, 0.0, False, 'gatling', 0.3,  4, '連射砲',   '押し続けて連射',                 'Gatling',     'hold to fire rapidly'),
    ('cannon',      -2.6, 0.50, 0.0, 1.0, False, 'shell',   2.0,  30, '砲',      '着弾で炸裂する砲弾',             'Cannon',      'shells that burst on impact'),
    ('bow',         -2.0, 0.30, 0.0, 0.0, False, 'bow',     1.4,  0, '弓',       '矢なしで射る（伝説は3本同時）', 'Bow',         'needs no arrows (legend fires three)'),
    ('shield',      -2.2, 0.50, 0.0, 1.0, False, 'guard',   0.0,  0, '盾',       '構えて防ぐ・盾で殴る',           'Shield',      'raise to block, bash to strike'),
]

CHARACTERS = {
    'kokuhaku': 'katana', 'riha': 'magic', 'tenki': 'greatsword', 'chaos': 'magic', 'berit': 'fist',
    'elseria': 'magic', 'valeria': 'heavy', 'huang_linghua': 'polearm', 'ferdinand': 'gatling', 'mels': 'polearm',
    'hephaistos': 'polearm', 'nortia': 'toyhammer', 'lucifara': 'scythe', 'taika': 'fist', 'mary_sue': 'magic',
    'savior': 'shield', 'gokuka': 'fist', 'merlinus': 'magic', 'enkou': 'polearm', 'kurma': 'heavy',
    'teia': 'bow', 'bahamut': 'magic', 'nun': 'magic', 'arcana': 'magic', 'eomaia': 'polearm',
    'demiurgos': 'greatsword', 'hakyoku': 'cannon', 'shinra': 'rapier', 'ain_sof_aur': 'sword', 'angra_mainyu': 'whip',
    'magna_mater': 'whip', 'ouroboros': 'chakram', 'yggdrasil': 'magic', 'miyohime': 'magic', 'innocence': 'magic',
    'brutality': 'heavy', 'cursed_love': 'magic', 'relentless_research': 'rapier', 'forbidden_arcana': 'whip',
    'fallen_savior': 'sword', 'sweet_pact': 'magic',
}

# NightfallCraft counterparts (FusionItems): kind from the item name
FUSION_RULES = [
    (('spear', 'halberd'), 'polearm'),
    (('axe',), 'heavy'),
    (('dagger', 'shortsword'), 'rapier'),
    (('claw',), 'fist'),
    (('greatsword', 'broadblade'), 'greatsword'),
    (('tachi', 'katana', 'murasama', 'yamato', 'kusabimaru', 'hf_blade'), 'katana'),
    (('thornwheel',), 'chakram'),
]
FUSION_WEAPONS = [
    'efn:air_tachi', 'efn:broadblade', 'efn:co_tachi', 'efn:crescent_moon', 'efn:crimson_moon', 'efn:exsiliumgladius',
    'efn:fire_exsiliumgladius', 'efn:hf_blade', 'efn:hf_murasama', 'efn:kusabimaru', 'efn:meen_spear', 'efn:nf_claw',
    'efn:nf_dual_sword', 'efn:nf_shortsword', 'efn:ruinsgreatsword', 'efn:sword_of_pioneer', 'efn:thornwheel',
    'efn:yamato_dmc4_in_sheath', 'efn:yamato_dmc_in_sheath', 'tcrcore:ashen_crescent', 'tcrcore:cinderwyrm',
    'tcrcore:emberfang', 'tcrcore:magic_axe', 'tcrcore:magic_dagger', 'tcrcore:magic_greatsword', 'tcrcore:magic_halberd',
    'tcrcore:magic_katana', 'tcrcore:magic_longsword', 'tcrcore:magic_spear', 'tcrcore:magic_sword', 'tcrcore:magic_tachi',
    'tcrcore:magmaheart', 'tcrcore:purging_swallow',
]

HOW = {  # right-click help per mode: (with art, plain)
    'melee': (('右クリック：アーツ', 'Right-click: art'), None),
    'bolt': (('右クリック：魔弾　しゃがみ＋右クリック：アーツ', 'Right-click: bolt   Sneak + right-click: art'), ('右クリック：魔弾', 'Right-click: bolt')),
    'gatling': (('右クリック長押し：連射　しゃがみ＋右クリック：アーツ', 'Hold right-click: rapid fire   Sneak + right-click: art'), ('右クリック長押し：連射', 'Hold right-click: rapid fire')),
    'shell': (('右クリック：砲撃　しゃがみ＋右クリック：アーツ', 'Right-click: fire shell   Sneak + right-click: art'), ('右クリック：砲撃', 'Right-click: fire shell')),
    'bow': (('右クリックで引いて離す：射る　しゃがみ＋右クリック：アーツ', 'Hold and release right-click: shoot   Sneak + right-click: art'), ('右クリックで引いて離す：射る', 'Hold and release right-click: shoot')),
    'guard': (('右クリック：構える　しゃがみ＋右クリック：アーツ', 'Right-click: block   Sneak + right-click: art'), ('右クリック：構える', 'Right-click: block')),
}


def fusion_kind(src):
    name = src.split(':', 1)[1]
    for keys, kind in FUSION_RULES:
        if any(k in name for k in keys):
            return kind
    return 'sword'


def data():
    ids = [k[0] for k in KINDS]
    assert set(CHARACTERS.values()) <= set(ids), set(CHARACTERS.values()) - set(ids)
    kinds = {}
    for (kid, speed, mul, reach, knock, sweep, mode, shot, gap, *_n) in KINDS:
        assert mode in HOW, mode
        kinds[kid] = dict(speed=speed, mul=mul, reach=reach, knock=knock, sweep=sweep, mode=mode, shot=shot, gap=gap)
    return {'kinds': kinds, 'characters': CHARACTERS, 'fusion': {s: fusion_kind(s) for s in FUSION_WEAPONS}}


def write(assets):
    d = data()
    rel = json.load(open(os.path.join(assets, 'relics.json'), encoding='utf-8'))
    chars = sorted({r['character'] for r in rel})
    assert sorted(CHARACTERS) == chars, set(chars) ^ set(CHARACTERS)
    with open(os.path.join(assets, 'weapon_kinds.json'), 'w', encoding='utf-8') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
    for lang, li in (('ja_jp', 0), ('en_us', 1)):
        path = os.path.join(assets, 'lang', lang + '.json')
        L = json.load(open(path, encoding='utf-8'))
        for (kid, *_s, ja, jaf, en, enf) in KINDS:
            L[f'weapon_kind.{NS}.{kid}'] = f'種別：{ja}（{jaf}）' if li == 0 else f'Kind: {en} ({enf})'
        for mode, (art, plain) in HOW.items():
            L[f'weapon_kind.{NS}.how.{mode}'] = art[li]
            if plain:
                L[f'weapon_kind.{NS}.how.{mode}.plain'] = plain[li]
        L[f'weapon_kind.{NS}.cooldown'] = 'アーツ再使用まで' if li == 0 else 'Art ready in'
        L[f'weapon_kind.{NS}.seconds'] = '秒' if li == 0 else 's'
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(L, fh, ensure_ascii=False, indent=1)
    counts = {}
    for k in CHARACTERS.values():
        counts[k] = counts.get(k, 0) + 1
    print('weapon kinds', len(KINDS), 'characters', counts, 'fusion', {s.split(':')[1]: k for s, k in d['fusion'].items() if k != 'sword'})


if __name__ == '__main__':
    write(sys.argv[1])

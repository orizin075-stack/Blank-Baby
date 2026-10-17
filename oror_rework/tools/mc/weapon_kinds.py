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

HOW = {  # right-click help per mode
    'melee': ('右クリック：アーツ', 'Right-click: art'),
    'bolt': ('右クリック：魔弾　しゃがみ＋右クリック：アーツ', 'Right-click: bolt   Sneak + right-click: art'),
    'gatling': ('右クリック長押し：連射　しゃがみ＋右クリック：アーツ', 'Hold right-click: rapid fire   Sneak + right-click: art'),
    'shell': ('右クリック：砲撃　しゃがみ＋右クリック：アーツ', 'Right-click: fire shell   Sneak + right-click: art'),
    'bow': ('右クリックで引いて離す：射る　しゃがみ＋右クリック：アーツ', 'Hold and release right-click: shoot   Sneak + right-click: art'),
    'guard': ('右クリック：構える　しゃがみ＋右クリック：アーツ', 'Right-click: block   Sneak + right-click: art'),
}

# The special ability of each kind (WeaponSkills.java): (ja name, ja description, en name, en description).
# "Full" hits are fully charged swings (the attack-strength bar full).
SPECIAL = {
    'katana': ('居合・閃', '溜め斬りの3連撃目で、前方7マスを一閃して貫く',
               'Iai Flash', 'every third charged cut flashes through enemies up to 7 blocks ahead'),
    'sword': ('剣閃', '溜め斬りで斬撃が飛び、後ろの敵まで斬る',
              'Sword Gale', 'charged cuts send a slash wave through the enemies behind'),
    'greatsword': ('大断撃', '溜め斬りで衝撃波。周囲4マスの敵を斬って浮かせる',
                   'Cleaving Quake', 'charged cuts release a shockwave that cuts and lifts enemies within 4 blocks'),
    'scythe': ('魂刈り', '斬るたびに体力を吸収。溜め斬りで瀕死の敵を刈り取る（ボスには追加ダメージ）',
               'Soul Reap', 'every cut drains life; charged cuts reap enemies near death (bonus damage on bosses)'),
    'chakram': ('跳ね輪', '溜め斬りで輪刃が近くの敵へ次々と跳ね返る（伝説は5体）',
                'Ricochet', 'charged cuts ricochet the blade between nearby enemies (five for a legend)'),
    'rapier': ('急所突き', '突くたびに出血（衰弱の呪い）。30％（伝説は50％）で2.2倍の急所突き',
               'Vital Thrust', 'every thrust bleeds the target; 30% (legend 50%) chance of a 2.2x critical thrust'),
    'polearm': ('貫通突き', '溜め突きで後ろの敵まで6マス貫き、押し込む',
                'Piercing Lunge', 'charged thrusts pierce 6 blocks through the enemies behind and drive them back'),
    'heavy': ('地割れ', '溜め打ちで地面を叩き割り、周囲の敵を打ち上げて足止め',
              'Earthsplitter', 'charged blows split the ground, launching and pinning down enemies around'),
    'toyhammer': ('ピコッ！', '叩いた敵を空高く吹き飛ばす。溜め打ちで周りもまとめて',
                  'Boing!', 'sends the target flying; charged blows bounce everyone around too'),
    'fist': ('連撃', '連続で殴るほど威力が上がり（最大＋96％）、5発ごとに衝撃波',
             'Combo', 'each blow in a chain hits harder (up to +96%) and every fifth one bursts'),
    'whip': ('縛鎖', '打った敵を引き寄せて足止め。溜め打ちで近くの敵にも絡みつく',
             'Binding Chain', 'pulls and slows the target; charged lashes also catch a nearby enemy'),
    'magic': ('大魔弾', '4発ごとに炸裂する大魔弾（2.5倍・範囲攻撃）',
              'Great Bolt', 'every fourth bolt is a great bolt that bursts (2.5x, area damage)'),
    'gatling': ('過熱', '撃ち続けるほど威力が上がり（最大＋80％）、最大まで熱すると燃える弾になる',
                'Overheat', 'keeps getting stronger while firing (up to +80%); at full heat rounds set targets ablaze'),
    'cannon': ('炸裂弾', '着弾した砲弾が周囲4マス（伝説は5マス）を吹き飛ばす',
               'Burst Shell', 'shells blast everything within 4 blocks (5 for a legend) into the air'),
    'bow': ('光矢', '命中した敵を光らせる。引き絞った矢は周りの敵も焼く',
            'Light Arrow', 'hit enemies glow; fully drawn arrows also scorch the enemies around'),
    'shield': ('完全防御', '構えた直後0.5秒の防御で攻撃を無効化し反撃。構え中は近くの仲間も守る',
               'Perfect Guard', 'blocking within half a second of raising it nullifies the hit and counters; raised, it shields nearby allies'),
}


def data():
    ids = [k[0] for k in KINDS]
    assert set(CHARACTERS.values()) <= set(ids), set(CHARACTERS.values()) - set(ids)
    kinds = {}
    for (kid, speed, mul, reach, knock, sweep, mode, shot, gap, *_n) in KINDS:
        assert mode in HOW, mode
        assert kid in SPECIAL, kid
        kinds[kid] = dict(speed=speed, mul=mul, reach=reach, knock=knock, sweep=sweep, mode=mode, shot=shot, gap=gap)
    return {'kinds': kinds, 'characters': CHARACTERS}


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
        for mode, text in HOW.items():
            L[f'weapon_kind.{NS}.how.{mode}'] = text[li]
        for k in [k for k in L if k.startswith(f'weapon_kind.{NS}.how.') and k.endswith('.plain')]:
            del L[k]   # help for relic-less fusion weapons, removed in v0.17.4
        for kid, (ja, jad, en, end) in SPECIAL.items():
            L[f'weapon_skill.{NS}.{kid}'] = ja + '！' if li == 0 else en + '!'
            L[f'weapon_skill.{NS}.{kid}.desc'] = f'特殊：{ja} ― {jad}' if li == 0 else f'Special: {en} - {end}'
        L[f'weapon_skill.{NS}.combo'] = '連撃' if li == 0 else 'Combo'
        L[f'weapon_kind.{NS}.cooldown'] = 'アーツ再使用まで' if li == 0 else 'Art ready in'
        L[f'weapon_kind.{NS}.seconds'] = '秒' if li == 0 else 's'
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(L, fh, ensure_ascii=False, indent=1)
    counts = {}
    for k in CHARACTERS.values():
        counts[k] = counts.get(k, 0) + 1
    print('weapon kinds', len(KINDS), 'characters', counts)


if __name__ == '__main__':
    write(sys.argv[1])

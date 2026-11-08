"""(057) The 984 techniques of the 41 characters, from the parsed design (parse_design.py), as the mod reads them.

Usage: build_waza.py <techniques984.json> <characters.json> <out assets dir>

Writes <out>/waza/waza984.json (one row per technique: its timing, reach, hits, behaviour and the verbs its text asks
for, colours, sounds, props, projectile shape and chain) and <out>/waza/waza_motions.bin (its own motion: keyframes for
the rig's parts by role). Every motion is checked against every other: no two may be the same.
"""
import hashlib, json, math, re, struct, sys

ROLES = ['arm_r', 'arm_l', 'elbow', 'knee', 'leg_r', 'leg_l', 'head', 'torso', 'root', 'jaw', 'wing', 'tail']
TIER = {'normal': 0, 'special': 1, 'grand': 2, 'ultimate': 3}

# ---------------------------------------------------------------------------------------------------------- the verbs
# What a technique does beyond its behaviour, read from its name and its motion's description (first match wins its
# place; a verb is taken once). Each is one small thing the server does to whoever the behaviour reaches.
VERBS = [
    ('STOP', r'止ま|止め|停止|静止|時を止|時間停止|凍結|一時停止|止まれ'),
    ('GRAVITY', r'重力|上下|逆さ|天地|落下と上昇|上昇と落下|上が下'),
    ('SHRINK', r'縮小|小さく|縮め|ちっちゃ'),
    ('SWAP', r'位置を交換|位置交換|入れ替|交換'),
    ('DISPEL', r'解除|無害|解体|打ち消|消去|分解|無効'),
    ('SILENCE', r'詠唱|術の循環|沈黙|封印|封じ|魔力が通る'),
    ('BIND', r'拘束|鎖|縛|絡|捕ら|捕ま|糸|網|檻|牢|枷|結び|縫'),
    ('PULL', r'引き寄|吸い寄|引っ張|吸い込|手繰|引き込|巻き込'),
    ('KNOCK', r'押し返|吹き飛|弾き飛|押出|押し出|押し戻|薙ぎ払|投げ飛|跳ね飛'),
    ('LIFT', r'打ち上|浮か|持ち上|空中へ|宙へ|舞い上'),
    ('SLAM', r'叩きつ|叩き落|押し潰|踏み潰|落と|振り下ろ|地面へ叩'),
    ('BURN', r'炎|火|焼|熱|溶|灼|焔|爆炎'),
    ('FROST', r'氷|凍|冷気|雪|霜|吹雪'),
    ('SHOCK', r'雷|電|稲妻|放電|紫電'),
    ('POISON', r'毒|腐|瘴'),
    ('WITHER', r'呪|怨|死|滅|闇の|黒炎|罪'),
    ('BLIND', r'闇|暗|目眩|眩|幻惑|霧|煙|墨'),
    ('WEAKEN', r'衰弱|弱|崩し|崩す|削|萎'),
    ('SLOW', r'遅|減速|鈍|重く|泥|粘|沼|眠|おひるね'),
    ('DRAIN', r'吸収|吸う|生命を奪|吸血|喰|捕食|奪'),
    ('ARMORBREAK', r'装甲|鎧|防御値|留め具|甲殻|守りを|守護結界|貫'),
    ('CONFUSE', r'混乱|惑わ|錯覚|欲望|魅了|誘惑|迷'),
    ('MARK', r'印|刻|標|照準|予告|宣言|赤い影|狙'),
    ('FEAR', r'恐怖|怯|威圧|覇気|咆哮|睨'),
    ('REFLECT', r'反射|跳ね返|弾き返|返す|折って|逆向き|反転'),
    ('SHATTER', r'砕|粉砕|破壊|割|裂'),
    ('HEAL_ALLY', r'回復|治|癒|再生|修復|塞が|蘇|復元'),
    ('WARD', r'守護|護|防護|障壁|結界|盾|防壁|庇'),
    ('HASTE', r'加速|高速|疾|速度'),
    ('MIGHT', r'強化|力を|増幅|覚醒|滾|闘気|鼓舞|力が'),
    ('CLEANSE', r'浄化|清め|状態異常が消|穢れを|祓'),
    ('DEATHWARD', r'死なない|致死|命を繋|一度だけ防'),
    ('INVIS', r'透明|姿を消|隠れ|見えない|消え'),
    ('BLAST', r'爆|炸裂|破裂|衝撃波|爆発'),
    ('PILLAR', r'光柱|柱'),
]
# How a move goes (MOVE), read the same way
MOVES = [('BEHIND', r'背後|回り込|背面|裏へ|裏側'), ('BACK', r'後退|退|離脱|間合いを取|下が|距離を取'),
         ('TOWARD', r'突進|踏み込|詰め|接近|飛び込|直進|迫'), ('SIDE', r'左右|横|側面|すり抜|擦れ違|滑'),
         ('UP', r'跳|飛び|空へ|宙|浮'), ('BLINK', r'転移|瞬間|消え|現れ|門|紙片|分散|霧')]
SUMMON_STYLE = [(3, r'怨霊|影|亡霊|霊|鬼|呪|骸|死者'), (2, r'機|ドローン|砲台|機械|兵器|砲塔|人形|工'),
                (0, r'精霊|妖精|光|星|鳥|蝶|羽|天使|小|花|蜂'), (1, r'')]
DEVICE = [('TURRET', r'砲|銃|射|弾幕|光線'), ('WALL', r'壁|城|砦|防壁|盾|塔'), ('HEALER', r'治療|修理|回復|再生|医'),
          ('FORGE', r'炉|工房|工廠|鍛|製造|生産|武器|錬成|組立'), ('TRAP', r'罠|地雷|仕掛|檻')]
CURSE_TRIGGER = [('HEAL', r'回復|治癒|強化を受|助け|幸福|恩'), ('ATTACK', r'攻撃|殺意|害意|敵意|振る|嫉妬|憎'),
                 ('MOVE', r'移動|歩|踏|進|逃'), ('TIMER', r'')]
SHAPES = [('star', r'星'), ('coin', r'金貨|硬貨|貨'), ('rock', r'岩|石|落石|山'), ('feather', r'羽|翼'),
          ('blade', r'刃|剣|刀|斬'), ('card', r'札|カード|符|紙|頁'), ('arrow', r'矢|針|槍|杭'), ('letter', r'文字|字|詩|詔|式'),
          ('flower', r'花|薔薇|蕾|桜'), ('bubble', r'泡|風船|雲|水玉'), ('bolt', r'雷|電'), ('flame', r'炎|火|焔'),
          ('wave', r'水|波|潮|海|渦'), ('skull', r'怨霊|霊|顔|骸'), ('cube', r'積木|箱|ブロック|立方|歯車|機'), ('orb', r'')]
SHAPE_IDS = {s[0]: i for i, s in enumerate(SHAPES)}
PROPS = ['halo', 'crown', 'robe', 'tomes', 'orb1', 'orb2', 'fruit1', 'fruit2', 'wheel', 'core', 'grip_r', 'fin_r']

# ------------------------------------------------------------------------------------------------------ colours, sound
COLOURS = [
    ('白銀', 0xD8E0EA), ('淡蒼', 0x9FC4E8), ('銀', 0xC8CED6), ('黄金', 0xF2C230), ('白金', 0xF4EBC8), ('淡金', 0xEEDC9A),
    ('赤金', 0xE0803A), ('暗金', 0xA88A30), ('金', 0xE8B830), ('翡翠', 0x3CC48C), ('青緑', 0x30B0A8), ('虹', 0xF07AE8),
    ('黒紫', 0x40204E), ('青紫', 0x6A50D8), ('紫紺', 0x3A2470), ('薄紫', 0xB8A0E8), ('深紫', 0x4C1A6C), ('紫', 0x8A40C8),
    ('深紅', 0xA0182C), ('暗紅', 0x701820), ('薔薇', 0xE0507A), ('紅', 0xC82838), ('赤', 0xD83030), ('橙', 0xF08A30),
    ('深青', 0x1A3C8C), ('淡青', 0x9AD0F0), ('青白', 0xC8E4FF), ('青', 0x3070E0), ('黒', 0x1A1420), ('純白', 0xFFFFFF),
    ('白', 0xF4F4F4), ('鋼', 0x8A949E), ('褐', 0x8A5A30), ('土', 0x9A7A50), ('岩', 0x7A6A58), ('緑', 0x50B050),
    ('生命光', 0x9AF07A), ('透明', 0xDDEEFF), ('液体銀', 0xB8C4D0), ('泡', 0xBEE8FF), ('霧', 0xC8D0D8), ('雷', 0xB890FF),
    ('炎', 0xFF7A20), ('火', 0xFF8A30), ('氷', 0xA8E8FF), ('毒', 0x7AC020), ('龍気', 0xF0D060), ('星', 0xFFF4B0),
]
SOUNDS = [  # (keyword, telegraph, release, hit) as vanilla sound event ids
    (r'鞘|刃|剣|斬|切断|刀', 'item.armor.equip_chain', 'entity.player.attack.sweep', 'entity.player.attack.strong'),
    (r'鐘|鈴', 'block.bell.resonate', 'block.bell.use', 'block.amethyst_block.chime'),
    (r'雷|電|放電', 'entity.lightning_bolt.thunder', 'entity.lightning_bolt.impact', 'block.respawn_anchor.deplete'),
    (r'水|波|潮|海|泡', 'block.water.ambient', 'entity.player.splash.high_speed', 'entity.generic.splash'),
    (r'炎|火|焔|熱|炉', 'block.fire.ambient', 'entity.blaze.shoot', 'item.firecharge.use'),
    (r'咆哮|吼|唸|獣', 'entity.ravager.roar', 'entity.ravager.attack', 'entity.ravager.stunned'),
    (r'歌|声|詠|唱|合唱|囁', 'block.amethyst_block.resonate', 'block.note_block.chime', 'block.amethyst_cluster.break'),
    (r'鎖|金属|機|歯車|装甲|鋼', 'block.chain.place', 'block.anvil.land', 'block.chain.break'),
    (r'紙|頁|書|文字|羊皮', 'item.book.page_turn', 'item.book.put', 'entity.evoker.cast_spell'),
    (r'岩|石|地|山|震', 'block.stone.break', 'entity.generic.explode', 'block.basalt.break'),
    (r'翼|羽|風', 'entity.phantom.flap', 'entity.ender_dragon.flap', 'entity.phantom.bite'),
    (r'呪|怨|泣|悲|霊', 'entity.vex.ambient', 'entity.wither.shoot', 'particle.soul_escape'),
    (r'時計|時|針', 'block.note_block.hat', 'block.respawn_anchor.charge', 'block.note_block.snare'),
    (r'花|蔓|根|木|葉|芽', 'block.azalea_leaves.place', 'block.big_dripleaf.tilt_down', 'block.cherry_leaves.break'),
    (r'星|光|輝', 'block.beacon.activate', 'block.amethyst_block.hit', 'entity.experience_orb.pickup'),
    (r'', 'entity.evoker.prepare_attack', 'entity.illusioner.cast_spell', 'entity.generic.hurt'),
]


def find(table, text):
    for name, pat in table:
        if pat == '' or re.search(pat, text):
            return name
    return table[-1][0]


def verbs_of(text, behaviour):
    hits = []
    for name, pat in VERBS:
        m = re.search(pat, text)
        if m:
            hits.append((m.start(), name))
    hits.sort()
    out = [n for _, n in hits]
    # support techniques do not harm, attacks do not heal their target
    support = {'HEAL_ALLY', 'WARD', 'HASTE', 'MIGHT', 'CLEANSE', 'DEATHWARD', 'INVIS'}
    if behaviour in ('HEAL',):
        out = [v for v in out if v in support] or ['HEAL_ALLY']
        if 'HEAL_ALLY' not in out:
            out.insert(0, 'HEAL_ALLY')
    return out[:4]


def colours_of(look):
    part = look.split('／')[1] if '／' in look else look
    part = part.split('。')[0]
    found = []
    for name, rgb in COLOURS:
        i = part.find(name)
        if i >= 0 and rgb not in [c for _, c in found]:
            found.append((i, rgb))
            part = part.replace(name, '　' * len(name), 1)
    found.sort()
    cs = [c for _, c in found] or [0xE8E0FF]
    while len(cs) < 3:
        cs.append(cs[-1])
    return cs[:3]


def sound_of(text):
    for pat, a, b, c in SOUNDS:
        if pat == '' or re.search(pat, text):
            return [a, b, c]


# ------------------------------------------------------------------------------------------------------- the motions
def P(**kw):
    """A pose: role -> [x, y, z] (root: [x, y, z, lift])."""
    return {k: list(v) for k, v in kw.items()}


# primitives: (pattern, windup pose, strike pose, beat)
PRIMS = [
    ('kesa', r'(?<!逆)袈裟|斜め', P(arm_r=(-2.7, 0.7, 0.7), torso=(0, 0.6, 0), leg_l=(-0.3, 0, 0)),
     P(arm_r=(-0.6, -0.9, -0.4), torso=(0.25, -0.7, 0), root=(0.15, 0, 0, 0), leg_r=(-0.5, 0, 0)), ''),
    ('gyakukesa', r'逆袈裟|斬り上|切り上', P(arm_r=(0.3, -0.6, -0.5), torso=(0.2, -0.5, 0)),
     P(arm_r=(-2.6, 0.8, 0.6), torso=(-0.15, 0.6, 0), head=(-0.2, 0, 0)), ''),
    ('horizontal', r'水平|薙|横一|横へ振', P(arm_r=(-1.5, 1.3, 0.2), torso=(0, 0.8, 0)),
     P(arm_r=(-1.5, -1.4, -0.1), torso=(0, -0.9, 0), root=(0, 0, 0, -0.5)), ''),
    ('thrust', r'突き|刺突|突く|貫|切先|穿', P(arm_r=(-0.9, 0.2, 0.3), torso=(-0.1, 0.4, 0), leg_l=(0.3, 0, 0)),
     P(arm_r=(-1.6, -0.1, 0), torso=(0.2, -0.3, 0), root=(0.25, 0, 0, -1), leg_r=(-0.8, 0, 0), leg_l=(0.5, 0, 0)), ''),
    ('overhead', r'振り下ろ|振りかぶ|真上から|唐竹|叩き割', P(arm_r=(-3.0, 0, 0.2), arm_l=(-2.8, 0, -0.2), torso=(-0.35, 0, 0), head=(-0.3, 0, 0)),
     P(arm_r=(-0.6, 0, 0.05), arm_l=(-0.6, 0, -0.05), torso=(0.55, 0, 0), root=(0.2, 0, 0, -2)), ''),
    ('draw', r'抜刀|居合|抜き|納刀|鞘', P(arm_r=(-0.4, 0.9, -0.6), arm_l=(-0.5, -0.4, 0.3), torso=(0.15, 0.5, 0), root=(0, 0, 0, -1.2)),
     P(arm_r=(-1.4, -1.5, 0.3), arm_l=(-0.2, 0.3, 0), torso=(0.05, -0.8, 0), leg_r=(-0.6, 0, 0)), ''),
    ('lunge', r'踏み込|踏込|突進|飛び込|間合いを詰', P(leg_r=(0.5, 0, 0), leg_l=(-0.4, 0, 0), torso=(0.3, 0, 0), root=(0.2, 0, 0, -1.5)),
     P(leg_r=(-0.9, 0, 0), leg_l=(0.7, 0, 0), torso=(0.45, 0, 0), root=(0.35, 0, 0, -1)), 'run'),
    ('stomp', r'踏み|踏ん|震脚|地面を蹴|足踏', P(leg_r=(-1.4, 0, 0.1), knee=(0.9, 0, 0), torso=(-0.15, 0, 0), root=(0, 0, 0, 1)),
     P(leg_r=(0.2, 0, 0.1), torso=(0.3, 0, 0), root=(0.1, 0, 0, -2)), ''),
    ('kick', r'蹴', P(leg_r=(0.6, 0, 0), knee=(1.0, 0, 0), torso=(-0.2, 0, 0)),
     P(leg_r=(-1.7, 0, 0.1), torso=(-0.35, 0, 0), arm_l=(-0.6, 0, -0.6)), ''),
    ('punch', r'拳|掌底|正拳|殴|打撃|乱打|連打', P(arm_r=(0.4, 0.3, 0.2), elbow=(-1.2, 0, 0), torso=(0, 0.5, 0)),
     P(arm_r=(-1.65, -0.2, 0), torso=(0.15, -0.55, 0), root=(0.15, 0, 0, 0)), 'alternate'),
    ('jump', r'跳|飛び上|宙返|跳ね', P(leg_r=(-0.6, 0, 0), leg_l=(-0.6, 0, 0), knee=(1.1, 0, 0), torso=(0.4, 0, 0), root=(0, 0, 0, -3)),
     P(leg_r=(0.3, 0, 0), leg_l=(0.3, 0, 0), arm_r=(-2.8, 0, 0.5), arm_l=(-2.8, 0, -0.5), root=(0, 0, 0, 6)), 'leap'),
    ('spin', r'回転|旋回|一周|回り|渦|竜巻|回す', P(arm_r=(-0.4, 0, 1.2), arm_l=(-0.4, 0, -1.2), torso=(0, 0.7, 0)),
     P(arm_r=(-0.3, 0, 1.5), arm_l=(-0.3, 0, -1.5), root=(0, 0, 0, 1.5)), 'spin'),
    ('raise', r'掲げ|天へ|空へ|頭上|天を|仰|天空', P(arm_r=(-1.0, 0, 0.3), arm_l=(-1.0, 0, -0.3), head=(0.2, 0, 0), torso=(0.15, 0, 0)),
     P(arm_r=(-3.0, 0, 0.35), arm_l=(-3.0, 0, -0.35), head=(-0.6, 0, 0), torso=(-0.25, 0, 0), root=(0, 0, 0, 2)), ''),
    ('point', r'指を差|指差|指で|指先|指を|人差し指|示す', P(arm_r=(-0.8, 0.3, 0.3), head=(0.1, 0.2, 0)),
     P(arm_r=(-1.6, -0.15, 0), head=(0, -0.1, 0), torso=(0.05, -0.2, 0)), ''),
    ('palms', r'両手|掌|手のひら|手を前', P(arm_r=(-0.9, 0.4, 0.3), arm_l=(-0.9, -0.4, -0.3), torso=(-0.15, 0, 0)),
     P(arm_r=(-1.55, -0.2, -0.15), arm_l=(-1.55, 0.2, 0.15), torso=(0.25, 0, 0), root=(0.12, 0, 0, 0)), ''),
    ('flick', r'弾き|弾い|弾く|払', P(arm_r=(-1.2, 0.6, 0.5), elbow=(-0.9, 0, 0)),
     P(arm_r=(-1.4, -0.8, -0.3), elbow=(-0.1, 0, 0)), ''),
    ('pray', r'祈|合掌|胸に手|瞑', P(arm_r=(-1.2, -0.6, -0.3), arm_l=(-1.2, 0.6, 0.3), head=(0.35, 0, 0)),
     P(arm_r=(-1.4, -0.75, -0.35), arm_l=(-1.4, 0.75, 0.35), head=(0.5, 0, 0), root=(0, 0, 0, 1)), 'bob'),
    ('write', r'書|描|綴|文字|字画|筆|署名', P(arm_r=(-1.3, 0.2, 0.2), head=(0.25, 0, 0)),
     P(arm_r=(-1.5, -0.3, 0.1), head=(0.2, -0.1, 0)), 'write'),
    ('hammer', r'叩|鍛|槌|打ち込|打ち鳴|鍛造', P(arm_r=(-2.6, 0, 0.1), torso=(-0.1, 0, 0)),
     P(arm_r=(-0.7, 0, 0.05), torso=(0.35, 0, 0), head=(0.3, 0, 0)), 'hammer'),
    ('throw', r'投げ|放つ|放ち|飛ばす|射出|投擲', P(arm_r=(-2.4, 0.6, 0.4), torso=(0, 0.6, 0), leg_l=(-0.3, 0, 0)),
     P(arm_r=(-1.0, -0.6, -0.2), torso=(0.2, -0.6, 0), leg_r=(-0.4, 0, 0)), ''),
    ('pull', r'引き寄|引っ張|手繰|引く|吸い寄', P(arm_r=(-1.7, 0, 0), arm_l=(-1.7, 0, 0), torso=(0.25, 0, 0)),
     P(arm_r=(-0.6, 0.3, 0.2), arm_l=(-0.6, -0.3, -0.2), torso=(-0.35, 0.3, 0), root=(-0.15, 0, 0, 0)), ''),
    ('crouch', r'沈め|屈|低く|身を伏|しゃが|伏せ', P(torso=(0.6, 0, 0), knee=(1.2, 0, 0), leg_r=(-0.7, 0, 0), leg_l=(-0.7, 0, 0), root=(0, 0, 0, -3)),
     P(torso=(0.35, 0, 0), leg_r=(-0.4, 0, 0), leg_l=(-0.2, 0, 0), root=(0.2, 0, 0, -2)), ''),
    ('embrace', r'抱|包み|抱擁|包む', P(arm_r=(-0.8, 0, 1.3), arm_l=(-0.8, 0, -1.3), head=(-0.2, 0, 0)),
     P(arm_r=(-1.3, -0.9, -0.3), arm_l=(-1.3, 0.9, 0.3), torso=(0.2, 0, 0)), ''),
    ('spread', r'広げ|開き|展開|拡げ|大きく開', P(arm_r=(-0.9, -0.4, -0.2), arm_l=(-0.9, 0.4, 0.2), torso=(0.3, 0, 0)),
     P(arm_r=(-0.5, 0, 1.6), arm_l=(-0.5, 0, -1.6), head=(-0.4, 0, 0), torso=(-0.3, 0, 0), root=(0, 0, 0, 1.5)), 'tremble'),
    ('ground', r'地面へ|地に|大地|床へ|地面に|足元', P(arm_r=(-2.2, 0, 0.2), head=(-0.2, 0, 0), root=(0, 0, 0, 1)),
     P(arm_r=(-0.4, 0, 0.1), torso=(0.75, 0, 0), knee=(1.0, 0, 0), leg_l=(-1.0, 0, 0), root=(0.2, 0, 0, -3)), ''),
    ('tail', r'尾', P(tail=(0.2, 0.9, 0), torso=(0, -0.4, 0)), P(tail=(-0.2, -1.4, 0), torso=(0, 0.5, 0), root=(0, 0.5, 0, 0)), ''),
    ('wing', r'翼|羽ばた|羽を', P(wing=(0, -0.5, 0.2), torso=(0.15, 0, 0)), P(wing=(0, 1.1, -0.3), head=(-0.3, 0, 0), root=(0, 0, 0, 3)), 'flap'),
    ('bite', r'顎|噛|牙|喰らい|捕食', P(head=(-0.6, 0, 0), jaw=(0.7, 0, 0), torso=(-0.2, 0, 0)),
     P(head=(0.45, 0, 0), jaw=(-0.05, 0, 0), torso=(0.3, 0, 0), root=(0.25, 0, 0, -1)), ''),
    ('roar', r'咆哮|吼|叫|雄叫', P(head=(0.4, 0, 0), jaw=(0.1, 0, 0), torso=(0.3, 0, 0)),
     P(head=(-0.8, 0, 0), jaw=(0.9, 0, 0), torso=(-0.35, 0, 0), arm_r=(-0.5, 0, 0.8), arm_l=(-0.5, 0, -0.8)), 'tremble'),
    ('breath', r'吐|ブレス|息', P(head=(-0.7, 0, 0), jaw=(0.2, 0, 0), torso=(-0.3, 0, 0)),
     P(head=(0.3, 0, 0), jaw=(0.85, 0, 0), torso=(0.2, 0, 0)), 'tremble'),
    ('clock', r'時計|逆回転|巻き戻|戻す|戻る|逆へ回', P(arm_r=(-1.6, 0, 0), head=(0, 0, 0.2), root=(0, 0, 0, 1)),
     P(arm_r=(-1.6, 0, 0), arm_l=(-0.7, 0.4, 0), head=(-0.1, 0, 0.2), root=(0, 0, 0, 2)), 'clock'),
    ('conduct', r'指揮|操|導', P(arm_r=(-1.3, 0, 0.9), arm_l=(-1.3, 0, -0.9), head=(-0.2, 0, 0)),
     P(arm_r=(-1.7, 0, 0.3), arm_l=(-1.1, 0, -1.0)), 'conduct'),
    ('shield', r'盾|構え|受け止|防ぐ|ガード', P(arm_r=(-1.2, -0.6, -0.3), arm_l=(-1.3, 0.7, 0.3), head=(0.2, 0, 0)),
     P(arm_r=(-1.5, -0.8, -0.4), arm_l=(-1.6, 0.85, 0.4), leg_r=(0, 0, 0.3), leg_l=(0, 0, -0.3), root=(0, 0, 0, -1.2)), ''),
    ('offer', r'差し出|渡|贈|手渡|見せ', P(arm_r=(-0.6, 0, 0.2), head=(0.15, 0, 0)), P(arm_r=(-1.2, -0.25, -0.1), head=(0.25, -0.15, 0), torso=(0.15, 0, 0)), ''),
    ('hunch', r'俯|項垂|背を丸|震え|泣', P(torso=(0.6, 0, 0), head=(0.5, 0, 0), arm_r=(-0.3, 0, 0.2), arm_l=(-0.3, 0, -0.2)),
     P(torso=(0.4, 0, 0), head=(-0.3, 0, 0), arm_r=(-1.2, 0, 0.4), arm_l=(-1.2, 0, -0.4)), 'twitch'),
    ('float', r'浮|漂|宙に|腰掛|空中に', P(leg_r=(-1.0, 0.3, 0), leg_l=(-1.0, -0.3, 0), root=(0, 0, 0, 2)),
     P(leg_r=(-1.2, 0.3, 0), leg_l=(-1.2, -0.3, 0), arm_r=(-0.8, 0, 0.6), arm_l=(-0.8, 0, -0.6), root=(0, 0, 0, 5)), 'bob'),
    ('grab', r'掴|握|捕まえ|鷲掴', P(arm_r=(-1.8, 0, 0.4), elbow=(-0.3, 0, 0)), P(arm_r=(-1.1, 0.4, -0.2), elbow=(-1.1, 0, 0), torso=(-0.2, 0.3, 0)), ''),
    ('dash', r'走|駆|滑|疾走|すり抜|擦れ違', P(torso=(0.35, 0, 0), arm_r=(0.6, 0, 0), arm_l=(0.6, 0, 0), root=(0.2, 0, 0, -1)),
     P(torso=(0.5, 0, 0), arm_r=(0.9, 0, 0.2), arm_l=(0.9, 0, -0.2), root=(0.3, 0, 0, -1)), 'run'),
    ('sway', r'揺|舞|踊|ふわ|くるり', P(arm_r=(-0.6, 0, 0.9), arm_l=(-0.6, 0, -0.9), torso=(0, 0.3, 0.15)),
     P(arm_r=(-1.0, 0, 1.2), arm_l=(-0.3, 0, -0.5), torso=(0, -0.3, -0.15), root=(0, 0, 0, 1)), 'weave'),
    ('slam', r'叩きつ|叩き落|押し潰|振り下|地面へ叩', P(arm_r=(-3.0, 0, 0.3), arm_l=(-3.0, 0, -0.3), root=(0, 0, 0, 2)),
     P(arm_r=(-0.3, 0, 0.2), arm_l=(-0.3, 0, -0.2), torso=(0.7, 0, 0), root=(0.25, 0, 0, -3)), ''),
]
FALLBACK = {
    'MELEE': 'kesa', 'PROJECTILE': 'throw', 'BEAM': 'palms', 'MOVE': 'dash', 'GUARD': 'shield', 'STATUS': 'point',
    'FIELD': 'spread', 'SUMMON': 'raise', 'BUILD': 'hammer', 'HEAL': 'pray', 'CONTROL': 'pull', 'REWIND': 'clock',
    'ADAPT': 'spread', 'CURSE': 'hunch', 'GROWTH': 'ground', 'SONG': 'roar', 'PACT': 'offer',
}
PRIM = {p[0]: p for p in PRIMS}
BEATS = ['', 'alternate', 'hammer', 'clock', 'spin', 'tremble', 'twitch', 'bob', 'leap', 'conduct', 'weave', 'run', 'write', 'flap']
BONE_ROLES = {'hips': ['root'], 'torso': ['torso'], 'body': ['torso', 'root'], 'arm_r': ['arm_r'], 'arm_l': ['arm_l'],
              'fore_r': ['elbow'], 'grip_r': ['arm_r'], 'leg_r': ['leg_r', 'knee'], 'leg_l': ['leg_l', 'knee'], 'root': ['root'],
              'head': ['head'], 'neck': ['head'], 'jaw': ['jaw'], 'tail1': ['tail'], 'wing_r': ['wing'], 'wing_l': ['wing'],
              'fin_r': ['wing'], 'fin_l': ['wing']}


def h(s, k):
    return int(hashlib.sha256((s + '#' + str(k)).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def prims_of(text, behaviour):
    found = []
    for name, pat, w, s, beat in PRIMS:
        for m in re.finditer(pat, text):
            found.append((m.start(), name))
            break
    found.sort()
    seq = []
    for _, n in found:
        if n not in seq:
            seq.append(n)
    if not seq:
        seq = [FALLBACK[behaviour]]
    return seq[:4]


def scale(pose, f, emph):
    out = {}
    for r, v in pose.items():
        g = 1.0 if (emph is None or r in emph) else 0.5
        out[r] = [x * f * g for x in v]
    return out


def add(a, b, f=1.0):
    out = {r: list(v) for r, v in a.items()}
    for r, v in b.items():
        cur = out.setdefault(r, [0.0] * len(v))
        while len(cur) < len(v):
            cur.append(0.0)
        for i, x in enumerate(v):
            cur[i] += x * f
    return out


def motion_of(t, model):
    text = t['name'] + '。' + t['motion']
    seq = prims_of(text, t['behaviour'])
    emph = set()
    for b in t['bones']:
        emph.update(BONE_ROLES.get(b, []))
    emph = emph or None
    tid = t['id']
    # the technique's own signature: a lean, a turn of the head and a stance of its own, so that two techniques built
    # of the same primitives still differ
    sig = P(torso=((h(tid, 1) - 0.5) * 0.3, (h(tid, 2) - 0.5) * 0.5, (h(tid, 3) - 0.5) * 0.2),
            head=((h(tid, 4) - 0.5) * 0.35, (h(tid, 5) - 0.5) * 0.6, 0),
            arm_l=((h(tid, 6) - 0.5) * 0.6, 0, (h(tid, 7) - 0.5) * 0.5),
            leg_r=((h(tid, 8) - 0.5) * 0.3, 0, 0), leg_l=((h(tid, 9) - 0.5) * 0.3, 0, 0))
    amp = 0.85 + 0.3 * h(tid, 10)
    W = [add(scale(PRIM[p][2], amp, emph), sig) for p in seq]
    S = [add(scale(PRIM[p][3], amp, emph), sig, 0.6) for p in seq]
    beat = next((PRIM[p][4] for p in seq if PRIM[p][4]), '')
    wu, ac, rc = t['windup'], t['active'], t['recovery']
    total = wu + ac + rc
    keys = [(0, {})]
    keys.append((max(1, round(wu * 0.45)), scale(W[0], 0.55, None)))
    keys.append((wu, W[0]))
    events = t['hits'] or [max(1, round(ac * 0.3))] + ([round(ac * 0.75)] if len(seq) > 1 else [])
    last = wu
    for i, e in enumerate(events):
        at = wu + min(e, ac)
        if at <= last:
            at = last + 1
        if i > 0:
            mid = (last + at) // 2
            if last < mid < at:
                keys.append((mid, scale(W[i % len(W)], 0.6, None)))
        keys.append((at, S[i % len(S)]))
        last = at
    end_active = max(last + 1, wu + ac)
    keys.append((end_active, scale(S[(len(events) - 1) % len(S)], 0.8, None)))
    keys.append((max(end_active + 1, total), {}))
    return seq, beat, keys, total


ARC = {'horizontal': 0, 'kesa': 1, 'gyakukesa': 2, 'thrust': 3, 'lunge': 3, 'punch': 3, 'point': 3, 'bite': 3, 'grab': 3, 'kick': 3,
       'overhead': 4, 'slam': 4, 'hammer': 4, 'stomp': 5, 'ground': 5, 'crouch': 5, 'spin': 6, 'tail': 6, 'wing': 0, 'draw': 0}


def arcs_of(seq, t):
    """The path of the blade (or claw, tail, fist) for each of a melee technique's hits, from its motion: 0 level, 1 cut
    down across, 2 cut up across, 3 thrust, 4 straight down, 5 the ground about the feet, 6 a whole turn."""
    arcs = [ARC.get(p) for p in seq if ARC.get(p) is not None] or [0]
    n = max(1, len(t['hits']))
    return [arcs[i % len(arcs)] for i in range(n)]


def pack_pose(p):
    vals = []
    for r in ROLES:
        v = p.get(r, [0, 0, 0, 0])
        vals += [v[0] if len(v) > 0 else 0, v[1] if len(v) > 1 else 0, v[2] if len(v) > 2 else 0]
    lift = p.get('root', [0, 0, 0, 0])
    vals.append(lift[3] if len(lift) > 3 else 0)
    q = []
    for i, x in enumerate(vals):
        s = 10.0 if i == len(vals) - 1 else 40.0
        q.append(max(-127, min(127, int(round(x * s)))))
    return q


def main(src, chars, out):
    d = json.load(open(src, encoding='utf-8'))
    roster = {c['id']: c for c in json.load(open(chars, encoding='utf-8'))}
    rows, blob, vectors = [], bytearray(), {}
    names = {t['name']: t['id'] for t in d['techniques']}
    by_char = {}
    for t in d['techniques']:
        by_char.setdefault(t['character'], {})[t['name']] = t['n']
    for idx, t in enumerate(d['techniques']):
        text = t['name'] + '。' + t['motion']
        beh = t['behaviour']
        verbs = verbs_of(text, beh)
        move = find(MOVES, text) if beh == 'MOVE' else ''
        style = find(SUMMON_STYLE, text) if beh in ('SUMMON',) else ''
        device = find(DEVICE, text) if beh == 'BUILD' else ''
        trigger = find(CURSE_TRIGGER, text) if beh == 'CURSE' else ''
        if beh == 'REWIND':
            trigger = 'ENEMY' if re.search(r'敵|相手', text) and not re.search(r'自身|身体|傷|本人|自分|本体', text) else 'SELF'
        if beh == 'PACT':
            trigger = ('COLLECT' if re.search(r'回収|没収|支払|期限|所有|閉じ', text) else
                       'GIFT' if re.search(r'無償|贈り物|前借り|幸運|救い', text) else 'OFFER')
        shape = find(SHAPES, text)
        look = t['look']
        parts = look.split('。')
        sound = sound_of((parts[1] if len(parts) > 1 else '') + text)
        cols = colours_of(look)
        props = [i for i, p in enumerate(PROPS) if p in t['bones']]
        link = None
        if t['link']:
            kind, name = t['link']
            n = by_char[t['character']].get(name)
            if n:
                link = [{'前提': 0, '後続': 1, '姿勢復帰後': 2}[kind], n]
        count = 1
        m = re.search(r'([二三四五六七八九]|[2-9])(?:つ|体|本|枚|発|筋|連|重|匹|人)', text)
        if m:
            count = '一二三四五六七八九'.find(m.group(1)) + 1 if m.group(1) in '一二三四五六七八九' else int(m.group(1))
        elif re.search(r'複数|群れ|無数|千|百|大量|いくつも|次々', text):
            count = 4
        seq, beat, keys, total = motion_of(t, roster[t['character']]['model'])
        rows.append([t['id'], t['character'], t['n'], t['name'], TIER[t['tier']], beh, t['windup'], t['active'], t['recovery'],
                     t['cooldown'], t['range'], t['hits'], verbs, move or str(style) or device or trigger, SHAPE_IDS[shape], count,
                     ['%06X' % c for c in cols], sound, props, link, t['particles'][:2], arcs_of(seq, t)])
        # the motion
        blob += struct.pack('>HBBBB', idx, len(keys), BEATS.index(beat), 2 + int(h(t['id'], 11) * 6), 8 + int(h(t['id'], 12) * 12))
        vec = []
        for at, pose in keys:
            q = pack_pose(pose)
            blob += struct.pack('>H', at) + bytes((x & 0xFF) for x in q)
            vec.append((at / max(1, total), q))
        vectors[t['id']] = (beat, vec)
    # no two motions alike: compare every pair by their poses at sixteen moments
    def sample(vec):
        outv = []
        for k in range(16):
            u = (k + 0.5) / 16
            for i in range(len(vec) - 1):
                if vec[i][0] <= u <= vec[i + 1][0]:
                    a, b = vec[i], vec[i + 1]
                    f = 0 if b[0] == a[0] else (u - a[0]) / (b[0] - a[0])
                    outv += [x + (y - x) * f for x, y in zip(a[1], b[1])]
                    break
            else:
                outv += vec[-1][1]
        return outv
    samples = {k: (v[0], sample(v[1])) for k, v in vectors.items()}
    ids = list(samples)
    closest = (1e9, None)
    for i in range(len(ids)):
        bi, si = samples[ids[i]]
        for j in range(i + 1, len(ids)):
            bj, sj = samples[ids[j]]
            dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(si, sj))) / 40.0
            if bi != bj:
                dist += 1.0
            if dist < closest[0]:
                closest = (dist, (ids[i], ids[j]))
    assert closest[0] > 0.25, 'two motions too alike: %s' % (closest,)
    import os
    os.makedirs(os.path.join(out, 'waza'), exist_ok=True)
    with open(os.path.join(out, 'waza', 'waza984.json'), 'w', encoding='utf-8') as f:
        json.dump({'version': 2, 'characters': d['characters'], 'techniques': rows}, f, ensure_ascii=False, separators=(',', ':'))
    with open(os.path.join(out, 'waza', 'waza_motions.bin'), 'wb') as f:
        f.write(b'ORW1' + struct.pack('>H', len(rows)) + bytes(blob))
    from collections import Counter
    print('techniques', len(rows), 'motion bytes', len(blob), 'closest pair', round(closest[0], 3), closest[1])
    print('verbs', Counter(v for r in rows for v in r[12]).most_common())
    print('no verbs', sum(1 for r in rows if not r[12] and r[5] not in ('MOVE', 'GUARD', 'REWIND', 'ADAPT', 'PACT', 'BUILD', 'SUMMON')))
    print('kinds', Counter((r[5], r[13]) for r in rows if r[13]).most_common())
    print('shapes', Counter(r[14] for r in rows).most_common())
    print('beats', Counter(vectors[k][0] for k in vectors).most_common())


if __name__ == '__main__':
    main(*sys.argv[1:4])

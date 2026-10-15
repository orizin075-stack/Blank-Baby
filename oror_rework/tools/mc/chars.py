"""Character recipes (Minecraft style). Appearance, weapons and props follow the setting texts,
characters.json features and the relic list. Characters whose setting gives them a weapon hold it."""
from rig import Rig
from paint import M
from humanoid import Humanoid, tail, wing, orbiters, ring_shape
import props as P

RECIPES = {}
def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn

# =============================================================================================== humanoids
@recipe
def kokuhaku():
    # 剣神 炬珀 — 純白の長髪、龍神の角二本、長い尾、月光のような白銀の肌、深い蒼に金色の光の瞳、
    # 古びた剣を一振り（抜刀・迎撃）、蒼白い炎の残光。神龍の力は封じ、剣の道だけを究める寡黙な剣士。
    r = Rig('kokuhaku')
    h = Humanoid(r, 'woman', skin='#f7ebe6', accent='#80d8ff')
    h.body(top_mat=M('cloth', '#f4f7fc', accent='#5aa8e8', pattern='kimono'), bottom_mat=M('cloth', '#253058'),
           legs_mat=M('cloth', '#253058'), boots_mat=M('cloth', '#eef2f8'), arms_mat=M('cloth', '#f4f7fc', accent='#5aa8e8', trim=2), neck='v')
    h.obi(M('cloth', '#33467e', accent='#cfe6ff', pattern='band'), knot=M('cloth', '#33467e', accent='#cfe6ff'))
    h.skirt(M('cloth', '#253058', accent='#6fb8f0', trim=2, pattern='flame'), length=14, flare=0.6, tiers=1)
    h.head_cube({'iris': '#2b55c8', 'iris2': '#ffd45a', 'glow_eyes': True})
    h.hair('#f8f9fc', style='very_long', length=18, tip='#cfe2ff')
    h.horns(M('horn', '#f4eedc', tip='#7fe3ff', glow=True), kind='dragon', length=11, spread=0.3, base=2)
    tail(r, h.hips, (0, h.hip_y - 1, 2), M('scale', '#eef2fb'), segments=6, length=3, width=3, taper=0.82, droop=0.22,
         tip_mat=M('scale', '#bfe6ff'))
    # 古びた剣: worn straight-backed blade with a pale blue afterglow, drawn in the right hand
    b, at = P.hand(h, 'r', P.POINT_FORWARD)
    P.katana(b, at, M('metal', '#b8c0cc', edge_glow='#7fd6ff'), M('metal', '#8a7a52'), M('cloth', '#1c2440', accent='#c8d8ff', pattern='stripes'), length=16)
    # 無音の鞘 at the left hip
    saya = r.bone('saya', h.hips, (4.5, h.hip_y - 2, -1), rot=(1.0, 0.1, -0.25))
    saya.box((4, h.hip_y - 2, -1.5), (1, 2, 1), M('metal', '#d9c27a'), name='koiguchi')
    saya.box((4, h.hip_y, -1.5), (1, 14, 1), M('metal', '#1b2238', edge_glow='#5fb0e0'), name='scabbard')
    return r

@recipe
def riha():
    # 天冠詠者 理覇 — 雪白の髪、頭上の淡い光の天冠、可憐、言霊の神子＋虚飾の悪魔、明るく気ままな旅人
    r = Rig('riha')
    h = Humanoid(r, 'woman', skin='#fbe7df', accent='#ffd36b')
    h.body(top_mat=M('cloth', '#fffaf0', accent='#d4a03a', pattern='kimono'), bottom_mat=M('cloth', '#b0335c'),
           legs_mat=M('cloth', '#fbf6ee'), boots_mat=M('cloth', '#b0335c'), arms_mat=M('cloth', '#fffaf0', accent='#b0335c', trim=2))
    h.obi(M('cloth', '#b0335c', accent='#ffd36b', pattern='band'), knot=M('cloth', '#b0335c', accent='#ffd36b'))
    h.skirt(M('cloth', '#b0335c', accent='#ffd36b', trim=2), length=11, flare=1.6, tiers=2)
    h.kimono_sleeves(M('cloth', '#fffaf0', accent='#b0335c', trim=2), drop=4)
    h.head_cube({'iris': '#e09a28', 'iris2': '#ffe58a', 'style': 'big', 'mouth': 'smile', 'blush': True})
    h.hair('#fdfdff', style='long', length=15, tip='#ffe6ef', ahoge=True)
    h.halo(M('ring', '#ffe38a', width=0.16, spikes=12), radius=6, y=h.head_top - 3, tilt=0.12)
    orbiters(r, h.torso, (0, h.top + 3, 0), M('plane', '#ffe38a', shape='star', glow=True), count=5, radius=10, speed=0.03,
             name='words', shapes=[(3, 3, 0)])
    return r

@recipe
def tenki():
    # 唯我万象 天輝 — 白金の長髪、淡い蒼と金の瞳、完成された美の青年、白と金の荘厳な装束（王の礼服＋神官の祭服）
    r = Rig('tenki')
    h = Humanoid(r, 'man', skin='#f6e3d6', accent='#e7be46')
    robe = M('cloth', '#fffaee', accent='#e2b33e', trim=2, pattern='embroidery')
    h.body(top_mat=M('cloth', '#fffaee', accent='#e2b33e', seam=True), bottom_mat=robe, legs_mat=M('cloth', '#f6efe0'),
           boots_mat=M('metal', '#e2b33e'), arms_mat=M('cloth', '#fffaee', accent='#e2b33e', trim=2), hands_mat=M('cloth', '#ffffff'), neck=None)
    h.robe(robe, flare=2.0)
    h.shoulder_pads(M('metal', '#ecc65a', rivets=True))
    h.cape(M('cloth', '#f8f2e4', accent='#d8a83a', trim=2), length=19, width=11)
    h.belt(M('metal', '#d8a83a'), buckle=M('gem', '#9fd8ff'))
    h.head_cube({'iris': '#7fb0ff', 'iris2': '#ffd76a', 'style': 'calm', 'glow_eyes': True})
    h.hair('#fff2c8', style='long', length=13, tip='#ffe3a0', bangs='parted')
    h.crown(M('metal', '#f0c64e'), gems=M('gem', '#8fd0ff'), spikes=5, tall=2)
    h.halo(M('ring', '#ffd76a', width=0.1, inner=0.75), radius=7, y=h.head_top + 1, z=5, tilt=1.45, speed=0.01)
    return r

@recipe
def berit():
    # 万界錬成 ベーリット — 無造作に束ねた黒銀の長髪、琥珀色の瞳、白衣とも礼装ともつかない外套、試験管・魔晶石、金と黒の錬成紋
    r = Rig('berit')
    h = Humanoid(r, 'woman', skin='#f4ddd2', accent='#d5a449')
    coat = M('cloth', '#eeeee9', accent='#2a2a33', trim=2)
    h.body(top_mat=M('cloth', '#2b2833', accent='#d5a449', pattern='circuit'), bottom_mat=M('cloth', '#2b2833'),
           legs_mat=M('cloth', '#2b2833'), boots_mat=M('cloth', '#4a3a2a'), arms_mat=coat,
           hands_mat=M('cloth', '#1e1c22', accent='#e2b34c', pattern='runes', pattern_glow=True), neck='round')
    h.jacket(M('cloth', '#eeeee9', accent='#d5a449'))
    h.coat_tails(coat, length=11)
    h.belt(M('cloth', '#5a4630'))
    for i, col in enumerate(['#6fe3a8', '#e36fb2', '#6fb0e3']):
        h.hips.box((-3 + i * 2, h.hip_y - 1, -2.75), (1, 2, 1), M('gem', col), name='vial')
    h.head_cube({'iris': '#e09a2a', 'iris2': '#fff0a0', 'mouth': 'smirk'})
    h.hair('#4a5060', style='long', length=13, tip='#b8c0cc', ponytail=True, bangs='messy')
    b, at = P.hand(h, 'l', (0.6, 0, 0))
    P.flask(b, at, M('gem', '#d8f0ff', glow=False), M('energy', '#7df0c8'))
    orbiters(r, h.torso, (0, h.top + 4, 0), [M('gem', '#d5a449'), M('gem', '#7df0c8'), M('metal', '#b0b6c4')], count=3,
             radius=9, size=2, speed=0.05, name='reagents')
    return r

@recipe
def elseria():
    # 星脈魔祖 エルセリア — 腰より長い白銀の髪、宝石の瞳、尖った耳、星と翼の装飾の純白の長衣と巨大な外套、寡黙な少女の姿、原初星辰杖
    r = Rig('elseria')
    h = Humanoid(r, 'woman', skin='#f8e8e2', accent='#89cbea')
    robe = M('cloth', '#f6f9ff', accent='#7fbde6', trim=2, pattern='stars', pattern_glow=True)
    h.body(top_mat=M('cloth', '#f6f9ff', accent='#7fbde6', seam=True), bottom_mat=robe, legs_mat=M('cloth', '#e8eef8'),
           boots_mat=M('cloth', '#c9d8ee'), arms_mat=M('cloth', '#f6f9ff', accent='#7fbde6', trim=2))
    h.robe(robe, flare=2.2)
    h.cape(M('cloth', '#2f4a7a', accent='#bfe4ff', pattern='stars', pattern_glow=True, trim=2), length=21, width=12)
    h.head_cube({'iris': '#3fb0d8', 'iris2': '#d8f8ff', 'style': 'calm', 'glow_eyes': True})
    h.hair('#ecf3ff', style='very_long', length=22, tip='#cfe2ff', bangs='blunt')
    h.ears('elf', length=4)
    b, at = P.hand(h, 'l', P.upright('l'))
    top = P.staff(b, at, M('wood', '#ece4d4'), length=27, below=9)
    P.star_head(b, top, M('gem', '#9fe6ff'), M('ring', '#c8e8ff', width=0.2, spikes=4))
    return r

@recipe
def valeria():
    # 万機創匠 ヴァレリア — 無造作に束ねた艶やかな黒髪、長身の美女、油染みの作業着、指輪・耳飾り・手袋に機構、工作手甲
    r = Rig('valeria')
    h = Humanoid(r, 'woman', skin='#f2d8c6', accent='#e7a444', lh=13, th=12)
    work = M('cloth', '#4b3f34', accent='#e7a444', pattern='marks')
    h.body(top_mat=M('cloth', '#2a2c33', accent='#e7a444', pattern='band'), bottom_mat=work, legs_mat=work,
           boots_mat=M('metal', '#5a4a3a', rivets=True), arms_mat=M('skin', '#f2d8c6'),
           hands_mat=M('metal', '#7a6a58', accent='#ffbf5a', pattern='circuit', pattern_glow=True), sleeve_len=2)
    h.belt(M('cloth', '#6a4a2a'), buckle=M('metal', '#e7a444'))
    h.cuffs(M('metal', '#8a7a64', rivets=True), at=7)
    for i in range(3):
        h.hips.box((-3.5 + i * 2.5, h.hip_y - 1, -2.75), (1, 3, 1), M('metal', '#9aa2ae'), name='tool')
    h.head_cube({'iris': '#c87a2a', 'mouth': 'smile'})
    h.hair('#1a2030', style='long', length=12, tip='#2a3448', ponytail=True, bangs='swept')
    h.jacket(M('cloth', '#8a7656', accent='#4a3a2a', pattern='marks'), rows=12)
    h.coat_tails(M('cloth', '#8a7656', accent='#4a3a2a', trim=1), length=12)
    for sx in (-1, 1):
        h.head.box((sx * 4.25 - 0.5, h.head_top + 5, -0.5), (1, 2, 1), M('gem', '#ffbf5a'), name='earring')
    b, at = P.hand(h, 'r', P.POINT_FORWARD)
    P.hammer(b, at, M('metal', '#9aa2ae', rivets=True, accent='#e7a444', pattern='band'), M('wood', '#6a4a2a'))
    orbiters(r, h.torso, (0, h.top, 0), M('metal', '#c8b080', rivets=True), count=2, radius=10, size=2, speed=0.04, name='drones')
    return r

@recipe
def huang_linghua():
    # 黄天龍仙 皇玲華 — 雪白の長髪、淡い赤紫の瞳、黒金の冠のような龍角、赤い飾り紐、黒の武官服と青緑の長衣、
    # 黄金の龍文の装甲、細身の杖（三界龍術杖）
    r = Rig('huang_linghua')
    h = Humanoid(r, 'woman', skin='#f8e8e0', accent='#d8b754')
    teal = M('cloth', '#17494c', accent='#d8b754', trim=2, pattern='embroidery')
    h.body(top_mat=M('cloth', '#1c1a22', accent='#d8b754', pattern='gold_lines'), bottom_mat=M('cloth', '#17494c'),
           legs_mat=M('cloth', '#1c1a22'), boots_mat=M('metal', '#2a2420', accent='#d8b754', pattern='trim'),
           arms_mat=M('cloth', '#17494c', accent='#d8b754', trim=2))
    h.robe(teal, flare=2.0, split=True)
    h.shoulder_pads(M('metal', '#d8b754', rivets=True))
    h.torso.box((-3, h.top + 2, -2.75), (6, 3, 1), M('metal', '#d8b754', rivets=True), name='breastplate')
    h.head_cube({'iris': '#c870a8', 'iris2': '#ffd0f0', 'style': 'calm'})
    h.hair('#fbfbff', style='very_long', length=19, tip='#f0e8f8', bangs='blunt')
    for sx in (-1, 1):
        cord = r.bone('cord_' + ('r' if sx < 0 else 'l'), h.head, (sx * 4.5, h.head_top + 4, 1), anim='hair', amp=0.05, speed=0.08, phase=sx)
        cord.box((sx * 4.5 - 0.5, h.head_top + 4, 0.5), (1, 7, 1), M('cloth', '#d8303a', accent='#ffd36b', trim=2), name='cord')
    h.horns(M('horn', '#23202a', tip='#e8c460', glow=True), kind='dragon', length=9, spread=0.45, base=2)
    tail(r, h.hips, (0, h.hip_y - 1, 2), M('scale', '#efedf4'), segments=6, length=3, width=3, taper=0.84, droop=0.18,
         tip_mat=M('scale', '#d8b754'))
    b, at = P.hand(h, 'r', P.upright('r'))
    top = P.staff(b, at, M('metal', '#2a2420', accent='#d8b754', pattern='rings'), length=25, below=8)
    P.dragon_head(b, top, M('metal', '#d8b754'), M('gem', '#ffe27a'))
    return r

@recipe
def ferdinand():
    # 文明遊匠 フェルディナント — 撫でつけた灰色の髪、片眼鏡の奥の青い瞳、上質な外套に工具・魔石・歯車、油の染みた手袋、万能工具
    r = Rig('ferdinand')
    h = Humanoid(r, 'man', skin='#f2dccd', accent='#8bcfe2')
    coat = M('cloth', '#3c3a52', accent='#c8a050', trim=2)
    h.body(top_mat=M('cloth', '#6a3030', accent='#d8b060', seam=True), bottom_mat=M('cloth', '#2e2c3a'), legs_mat=M('cloth', '#2e2c3a'),
           boots_mat=M('cloth', '#3a2a20'), arms_mat=coat, hands_mat=M('cloth', '#5a4a3a', pattern='marks', accent='#2a2420'),
           collar_mat=M('cloth', '#e8e0d0'))
    h.jacket(M('cloth', '#3c3a52', accent='#c8a050'))
    h.coat_tails(coat, length=12)
    h.belt(M('cloth', '#5a3a20'), buckle=M('metal', '#c8a050'))
    h.head_cube({'iris': '#3a8ad0', 'mouth': 'smile', 'monocle': '#d8b050'})
    h.hair('#949eaa', style='short', length=6, side_locks=False, bangs='slick')
    pack = r.bone('backpack', h.torso, (0, h.top + 3, 2.5))
    pack.box((-3, h.top + 2, 2.5), (6, 7, 3), M('metal', '#8a6a3a', rivets=True), name='pack')
    pack.box((-4, h.top - 1, 3), (1, 5, 1), M('metal', '#b0b6c4'), name='pipe')
    pack.box((3, h.top, 3), (1, 4, 1), M('metal', '#b0b6c4'), name='pipe2')
    orbiters(r, pack, (0, h.top + 1, 6.5), M('metal', '#d8b060', accent='#8a6a3a', pattern='rings'), count=3, radius=5, speed=0.08,
             name='gears', shapes=[(3, 3, 1)])
    b, at = P.hand(h, 'r', P.POINT_FORWARD)
    P.wrench(b, at, M('metal', '#b0b6c4', accent='#8bcfe2', pattern='band'), M('cloth', '#5a3a20'))
    return r

@recipe
def nortia():
    # 無法遊戯 ノルティア — 七歳ほどの中性的な子供、虹色の万華鏡の瞳、無垢な笑顔、遊びとゲームの化身
    r = Rig('nortia')
    h = Humanoid(r, 'child', skin='#fde9e2', accent='#f4d06f')
    h.body(top_mat=M('cloth', '#d6c4f0', accent='#f4d06f', pattern='chevron'), bottom_mat=M('cloth', '#5a6ad8', accent='#f4d06f', pattern='dots'),
           legs_mat=M('cloth', '#f4f0ff', accent='#5a6ad8', pattern='stripes'), boots_mat=M('cloth', '#f45a7a'),
           arms_mat=M('cloth', '#d6c4f0', accent='#f4d06f', trim=2), boots_h=3)
    h.cape(M('cloth', '#f4d06f', accent='#5a6ad8', pattern='chevron', trim=2), length=10, width=8)
    h.head_cube({'iris': '#c070ff', 'iris2': '#7ff0ff', 'style': 'big', 'mouth': 'grin', 'blush': True, 'glow_eyes': True})
    h.hair('#c9d8ff', style='bob', length=7, ahoge=True, side_locks=False)
    h.crown(M('metal', '#f4d06f'), gems=M('gem', '#ff7fd0'), spikes=3, tall=1)
    orbiters(r, h.torso, (0, h.top + 3, 0), [M('gem', '#ff6f8f'), M('cloth', '#ffffff', accent='#222222', pattern='dots'), M('gem', '#7ff07f'),
             M('cloth', '#f4f0ff', accent='#e23a4a', pattern='cross')], count=4, radius=9, speed=0.05, name='toys',
             shapes=[(2, 2, 2), (2, 2, 2), (2, 2, 2), (2, 3, 0)])
    return r

@recipe
def lucifara():
    # 失楽堕天 ルシファーラ — 漆黒の翼、天使の神々しさと悪魔の妖艶さ、白金の髪、深紅の瞳
    r = Rig('lucifara')
    h = Humanoid(r, 'woman', skin='#f8e4de', accent='#c54573')
    dress = M('cloth', '#1d1626', accent='#c54573', trim=2, pattern='embroidery')
    h.body(top_mat=M('cloth', '#1d1626', accent='#c54573', pattern='kimono'), bottom_mat=M('cloth', '#1d1626'), legs_mat=M('cloth', '#2a1e30'),
           boots_mat=M('cloth', '#120c18', accent='#c54573'), arms_mat=M('cloth', '#2a1e30', accent='#c54573', trim=2),
           hands_mat=M('cloth', '#1d1626'))
    h.skirt(M('cloth', '#1d1626', accent='#c54573', trim=2), length=12, flare=1.8, tiers=2)
    h.head_cube({'iris': '#d0203a', 'iris2': '#ff9ab0', 'style': 'calm', 'mouth': 'smirk', 'glow_eyes': True})
    h.hair('#f8eedc', style='very_long', length=19, tip='#e8c8b8')
    h.horns(M('horn', '#2a1a2a', tip='#c54573', glow=True), kind='ram', length=6, base=2)
    h.halo(M('ring', '#c54573', width=0.14, spikes=6), radius=5, y=h.head_top - 2.5, tilt=0.35)
    for sx in (-1, 1):
        wing(r, h.torso, sx, (sx * 1.5, h.top + 3, 2.5), 'feather', M('feather', '#1a1420', tip='#5a2040'), span=16, height=14, rest=0.5)
    return r

@recipe
def taika():
    # 超克覇王 辿迦 — 引き締まった肉体、鬼の角と紅の瞳の青年、仙境で武を修めた礼儀正しい武人（拳）
    r = Rig('taika')
    h = Humanoid(r, 'man', skin='#efd0b8', accent='#e44c49')
    h.body(top_mat=M('skin', '#efd0b8'), bottom_mat=M('cloth', '#2a1a24', accent='#e44c49', pattern='trim'), legs_mat=M('cloth', '#2a1a24'),
           boots_mat=M('cloth', '#e8e0d8'), arms_mat=M('skin', '#efd0b8'), hands_mat=M('cloth', '#e8e0d8', accent='#e44c49', pattern='stripes'), neck=None)
    h.torso.box((-3.5, h.top + 2, -2.25), (7, 2, 0), M('skin', '#dcb69c'), name='pecs')
    h.torso.box((-2, h.top + 5, -2.25), (4, 3, 0), M('skin', '#dcb69c', pattern='band', accent='#c49a80'), name='abs')
    h.obi(M('cloth', '#e44c49', accent='#ffd36b', pattern='band'), knot=M('cloth', '#e44c49'))
    h.skirt(M('cloth', '#40283a', accent='#e44c49', trim=2), length=9, flare=1.2, tiers=1)
    h.cuffs(M('cloth', '#e44c49', accent='#ffd36b'), at=8)
    h.head_cube({'iris': '#e0303a', 'iris2': '#ff9a6a', 'style': 'fierce', 'glow_eyes': True})
    h.hair('#351e27', style='short', length=6, side_locks=False, bangs='messy')
    h.horns(M('horn', '#f0e6d8', tip='#e44c49', glow=True), kind='oni', length=5, base=2)
    return r

@recipe
def mary_sue():
    # 覚醒進化 メアリー・スー — 完璧な美女、主人公、無限の覚醒と進化
    r = Rig('mary_sue')
    h = Humanoid(r, 'woman', skin='#fae6da', accent='#f2bb5b')
    h.body(top_mat=M('metal', '#f6eedc', accent='#f2bb5b', pattern='gold_lines'), bottom_mat=M('cloth', '#faf3e7'),
           legs_mat=M('cloth', '#faf3e7'), boots_mat=M('metal', '#f2bb5b'), arms_mat=M('cloth', '#faf3e7', accent='#f2bb5b', trim=2),
           hands_mat=M('metal', '#f2e0b0'), neck=None)
    h.skirt(M('cloth', '#faf3e7', accent='#f2bb5b', trim=2, pattern='embroidery'), length=11, flare=1.6, tiers=2)
    h.shoulder_pads(M('metal', '#f2bb5b', rivets=True))
    h.cape(M('cloth', '#c03040', accent='#f2bb5b', trim=2), length=18)
    h.head_cube({'iris': '#2fa07a', 'iris2': '#c8ffd8', 'mouth': 'smile'})
    h.hair('#ecc47a', style='very_long', length=19, tip='#fff0c0')
    h.crown(M('metal', '#f2bb5b'), gems=M('gem', '#ff6f8f'), spikes=3, tall=1)
    orbiters(r, h.torso, (0, h.top, 0), M('plane', '#ffe38a', shape='star', glow=True), count=3, radius=10, speed=0.04,
             name='sparkles', shapes=[(3, 3, 0)])
    return r

@recipe
def savior():
    # 救世天主 セイヴァー — 白銀の神官服、穏やかな微笑みの青年、結界と救済、天然、慈愛の祈祷杖
    r = Rig('savior')
    h = Humanoid(r, 'man', skin='#f6e4d8', accent='#dac36c')
    robe = M('cloth', '#f8f9fc', accent='#dac36c', trim=3, pattern='cross')
    h.body(top_mat=M('cloth', '#f8f9fc', accent='#dac36c', seam=True), bottom_mat=robe, legs_mat=M('cloth', '#e8e8ef'),
           boots_mat=M('cloth', '#d8c890'), arms_mat=M('cloth', '#f8f9fc', accent='#dac36c', trim=2), hands_mat=M('cloth', '#ffffff'), neck=None)
    h.robe(robe, flare=2.2)
    h.cape(M('cloth', '#e8ecf6', accent='#dac36c', trim=2), length=19)
    h.torso.box((-3, h.top, -2.5), (6, 9, 0), M('cloth', '#dac36c', accent='#ffffff', pattern='cross'), name='stole')
    h.head_cube({'iris': '#5a98d8', 'style': 'calm', 'mouth': 'smile'})
    h.hair('#e9eaf2', style='short', length=7, bangs='parted')
    h.halo(M('ring', '#ffe9a0', width=0.16), radius=5, y=h.head_top - 2.5, tilt=0.2)
    b, at = P.hand(h, 'l', P.upright('l'))
    top = P.staff(b, at, M('metal', '#f0e8d0'), length=27, below=9)
    P.cross_head(b, top, M('metal', '#dac36c'), M('gem', '#fff3b0'))
    return r

@recipe
def gokuka():
    # 外業呪禍 獄華 — 少女のようで獣・竜・病の怪異、肩口の獣毛、牙、鱗、竜の鉤爪、色彩の変わる不定形の液体の衣
    r = Rig('gokuka')
    h = Humanoid(r, 'woman', skin='#eadce8', accent='#af55bb')
    goo = M('oilslick', '#1e1830')
    h.body(top_mat=goo, bottom_mat=goo, legs_mat=M('scale', '#3a2a4a'), boots_mat=M('horn', '#2a1a2a', tip='#af55bb'),
           arms_mat=M('scale', '#3a2a4a'), hands_mat=M('horn', '#2a1a2a', tip='#e070f0', glow=True), neck=None)
    h.skirt(goo, length=12, flare=2.0, tiers=1)
    h.torso.box((-4, h.top, -2), (8, 2, 4), M('fur', '#4a3a40', tip='#2a2030'), grow=0.8, name='fur_collar', faces={'bottom': None})
    for arm in (h.arm_r, h.arm_l):
        arm.box((arm.pivot[0] - 1.5, h.top, -2), (3, 2, 4), M('fur', '#4a3a40', tip='#2a2030'), grow=0.7, name='fur')
    h.head_cube({'iris': '#c060e0', 'iris2': '#ffb0ff', 'style': 'slit', 'mouth': 'fang', 'glow_eyes': True, 'marks': '#af55bb'})
    h.hair('#322439', style='very_long', length=18, tip='#af55bb', bangs='messy')
    h.horns(M('horn', '#2a1a2a', tip='#af55bb', glow=True), kind='dragon', length=7, spread=0.5, base=2)
    tail(r, h.hips, (0, h.hip_y - 1, 2), M('scale', '#3a2a4a', accent='#af55bb', pattern='marks', pattern_glow=True), segments=6,
         length=3, width=3, taper=0.82, droop=0.2)
    for side in ('r', 'l'):
        P.claws(h, side, M('horn', '#2a1a2a', tip='#e070f0', glow=True), length=4)
    orbiters(r, h.torso, (0, h.top + 6, 0), M('slime', '#c070e0', alpha=170), count=4, radius=8, size=2, speed=0.04, name='drops')
    return r

@recipe
def merlinus():
    # 魔導深淵 メルリヌス — 白銀の髪、深い紫のローブの幼い少女（元は老賢者）、悠久の叡智の瞳、お茶目、杖と無詠唱の魔導書
    r = Rig('merlinus')
    h = Humanoid(r, 'child', skin='#fbe8e0', accent='#b294ee')
    robe = M('cloth', '#492565', accent='#d8c8ff', trim=2, pattern='stars', pattern_glow=True, glow_amount=0.35)
    h.body(top_mat=M('cloth', '#492565', accent='#e6d070', seam=True), bottom_mat=robe, legs_mat=M('cloth', '#3a1e50'),
           boots_mat=M('cloth', '#2a1a3a'), arms_mat=M('cloth', '#492565', accent='#b294ee', trim=2))
    h.robe(robe, flare=2.6)
    h.kimono_sleeves(M('cloth', '#492565', accent='#b294ee', trim=2), drop=3)
    h.head_cube({'iris': '#9a6af0', 'iris2': '#e0d0ff', 'style': 'big', 'mouth': 'smile', 'blush': True})
    h.hair('#eef1ff', style='long', length=13, tip='#d8dcf8')
    b, at = P.hand(h, 'r', P.upright('r'))
    top = P.staff(b, at, M('wood', '#5a3a2a'), length=20, below=5)
    P.crook_head(b, top, M('wood', '#5a3a2a'), M('gem', '#c8a0ff'))
    bk = r.bone('grimoire', h.torso, (7, h.top + 2, -3), anim='float', amp=0.8, speed=0.08)
    P.book(bk, (7, h.top + 2, -3), M('cloth', '#5a2a1a', accent='#e6d070', pattern='runes', pattern_glow=True), M('cloth', '#f0e6c8'))
    return r

@recipe
def arcana():
    # 運命流転 アルカナ — 奇跡のような美貌と神聖な光の天使、星の光を編んだ羽、過去現在未来を映す瞳、運命札
    r = Rig('arcana')
    h = Humanoid(r, 'woman', skin='#faeae2', accent='#dabd72')
    robe = M('cloth', '#f4f5fc', accent='#dabd72', trim=2, pattern='stars', pattern_glow=True)
    h.body(top_mat=M('cloth', '#f4f5fc', accent='#dabd72', pattern='kimono'), bottom_mat=robe, legs_mat=M('cloth', '#e6e8f4'),
           boots_mat=M('metal', '#dabd72'), arms_mat=M('cloth', '#f4f5fc', accent='#dabd72', trim=2))
    h.robe(robe, flare=2.2)
    h.head_cube({'iris': '#7a6ad8', 'iris2': '#ffe9a0', 'style': 'calm', 'mouth': 'smile', 'glow_eyes': True})
    h.hair('#f8eed2', style='very_long', length=20, tip='#fff8e8')
    h.halo(M('ring', '#ffe9a0', width=0.12, inner=0.75), radius=5, y=h.head_top - 2.5, tilt=0.2)
    for sx in (-1, 1):
        wing(r, h.torso, sx, (sx * 1.5, h.top + 3, 2.5), 'feather', M('feather', '#fffaf0', tip='#ffe0a0', glow=True), span=16, height=15, rest=0.45)
    orbiters(r, h.torso, (0, h.top + 1, 0), M('cloth', '#f8f0dc', accent='#7a5ad8', pattern='cross'), count=3, radius=10, speed=0.03,
             name='cards', shapes=[(2, 3, 0)])
    return r

@recipe
def hakyoku():
    # 無窮覇帝 覇極 — 龍の尾と翼、獣の四肢、王冠のような角、十歳ほどの美少女と獣と兵器の混合、罅割れ・回路の光る文様、爪
    r = Rig('hakyoku')
    h = Humanoid(r, 'child', skin='#f1e6ee', accent='#ff627f')
    crack = dict(pattern='cracks', pattern_glow=True, glow_amount=0.7)
    h.body(top_mat=M('metal', '#211e2e', accent='#ff627f', **crack), bottom_mat=M('cloth', '#2a2438', accent='#ff627f', **crack),
           legs_mat=M('fur', '#ddd9ea'), boots_mat=M('horn', '#2a2438', tip='#ff627f'), arms_mat=M('fur', '#ddd9ea'),
           hands_mat=M('horn', '#211e2e', tip='#ff627f', glow=True), neck=None)
    h.skirt(M('cloth', '#2a2438', accent='#ff627f', trim=1, **crack), length=6, flare=1.4, tiers=1)
    h.head_cube({'iris': '#ff3a6a', 'iris2': '#ffd0e0', 'style': 'slit', 'mouth': 'fang', 'glow_eyes': True, 'marks': '#ff627f'})
    h.hair('#e0dcec', style='long', length=13, tip='#ff9ab0', bangs='messy')
    h.crown(M('horn', '#2a2438', tip='#ff627f', glow=True), spikes=5, tall=3)
    tail(r, h.hips, (0, h.hip_y - 1, 1.5), M('scale', '#2a2438', accent='#ff627f', pattern='circuit', pattern_glow=True), segments=6,
         length=3, width=2, taper=0.9, droop=0.2)
    for sx in (-1, 1):
        wing(r, h.torso, sx, (sx * 1, h.top + 2, 1.5), 'membrane', M('membrane', '#2a2438', accent='#ff627f'), span=10, height=8,
             mat2=M('horn', '#211e2e', tip='#ff627f'), rest=0.5)
    for side in ('r', 'l'):
        P.claws(h, side, M('horn', '#2a2438', tip='#ff627f', glow=True), length=3)
    return r

@recipe
def shinra():
    # 万物天敵 シンラ — 人と獣の混ざった美しき鬼の少女、小さな角、尖った耳、牙、鉤爪、普段は街の片隅で花を育てる
    r = Rig('shinra')
    h = Humanoid(r, 'woman', skin='#f8e4dc', accent='#bb5476')
    dress = M('cloth', '#f3eadf', accent='#bb5476', trim=2, pattern='vine')
    h.body(top_mat=M('cloth', '#f3eadf', accent='#bb5476', pattern='kimono'), bottom_mat=M('cloth', '#f3eadf'), legs_mat=M('skin', '#f8e4dc'),
           boots_mat=M('cloth', '#5a3a3a'), arms_mat=M('cloth', '#f3eadf', accent='#bb5476', trim=2), hands_mat=M('horn', '#f8e4dc', tip='#bb5476'))
    h.skirt(dress, length=10, flare=1.4, tiers=2)
    h.head_cube({'iris': '#c0305a', 'iris2': '#ffb0c8', 'style': 'sad', 'mouth': 'fang'})
    h.hair('#262230', style='long', length=14, tip='#3a2a40')
    h.horns(M('horn', '#f0e0d8', tip='#bb5476', glow=True), kind='oni', length=3, base=1)
    h.ears('elf', length=3)
    tail(r, h.hips, (0, h.hip_y - 1, 2), M('fur', '#262230'), segments=5, length=3, width=2, taper=0.9, droop=0.25)
    h.head.box((3.5, h.head_top + 1, -2), (2, 2, 2), M('gem', '#ff9ab8', glow=False), name='flower')
    for side in ('r', 'l'):
        P.claws(h, side, M('horn', '#f0e0d8', tip='#bb5476'), length=3)
    return r

@recipe
def ain_sof_aur():
    # 全界支配 アインソフオウル — 透明な雰囲気の少年、衣冠束帯を思わせる神聖な装束、頭上に浮かぶ淡く輝く王冠
    r = Rig('ain_sof_aur')
    h = Humanoid(r, 'youth', skin='#f8ece8', accent='#a791ee')
    robe = M('cloth', '#f3ecfa', accent='#a791ee', trim=3, pattern='embroidery')
    h.body(top_mat=M('cloth', '#6a5aa8', accent='#e8e0ff', pattern='kimono'), bottom_mat=robe, legs_mat=M('cloth', '#e8e0f4'),
           boots_mat=M('cloth', '#2a2440'), arms_mat=M('cloth', '#f3ecfa', accent='#a791ee', trim=2))
    h.robe(robe, flare=3.0)
    h.kimono_sleeves(M('cloth', '#f3ecfa', accent='#a791ee', trim=2), drop=6)
    h.head_cube({'iris': '#8a7ae8', 'iris2': '#e0d8ff', 'style': 'calm', 'glow_eyes': True})
    h.hair('#dbe3fa', style='short', length=7, bangs='bangs')
    cap = r.bone('kanmuri', h.head, (0, h.head_top, 0))
    cap.box((-2, h.head_top - 3, -2), (4, 3, 4), M('cloth', '#1a1828', accent='#a791ee', trim_top=True), name='kanmuri')
    cap.box((-0.5, h.head_top - 2, 2), (1, 8, 0), M('cloth', '#1a1828'), name='ei')
    # 頭上に浮かぶ淡く輝く王冠
    h.crown(M('energy', '#cbbcff'), gems=M('gem', '#ffffff'), spikes=5, tall=2, lift=5, name='light_crown')
    orbiters(r, h.torso, (0, h.top + 4, 0), M('plane', '#cbbcff', shape='diamond', glow=True), count=5, radius=11, speed=0.02,
             name='branches', shapes=[(3, 3, 0)])
    return r

@recipe
def angra_mainyu():
    # 全害惡徳 アンラマンユ — 褐色の肌に禍々しい文様、漆黒の衣、深淵のように暗い瞳、静けさと品格
    r = Rig('angra_mainyu')
    h = Humanoid(r, 'man', skin='#8a6248', accent='#a0474e')
    black = M('cloth', '#1c1822', accent='#a0474e', trim=2, pattern='marks', pattern_glow=True)
    h.body(top_mat=M('cloth', '#1c1822', accent='#a0474e', pattern='kimono'), bottom_mat=M('cloth', '#1c1822'), legs_mat=M('cloth', '#141018'),
           boots_mat=M('cloth', '#0e0a12'), arms_mat=M('skin', '#8a6248', accent='#c04a50', pattern='marks', pattern_glow=True),
           hands_mat=M('skin', '#8a6248'), sleeve_len=3)
    h.robe(black, flare=2.0, split=True)
    h.cape(M('cloth', '#141018', accent='#a0474e', trim=2), length=19)
    h.head_cube({'iris': '#3a1a2a', 'iris2': '#c0303a', 'style': 'calm', 'marks': '#c04a50', 'line': '#120c10'})
    h.hair('#161520', style='short', length=7, bangs='swept')
    orbiters(r, h.torso, (0, h.top + 6, 0), M('gem', '#4a1020'), count=4, radius=9, size=2, speed=0.03, name='malice')
    return r

@recipe
def magna_mater():
    # 始源母胎 マグナ・マーテル — 羽、鱗、猫のような瞳、蔦のような指、草木の蔓の髪、慈愛の母
    r = Rig('magna_mater')
    h = Humanoid(r, 'woman', skin='#f4e0d0', accent='#dbb685')
    leafy = M('cloth', '#446a4a', accent='#dbb685', trim=2, pattern='vine')
    h.body(top_mat=M('cloth', '#5a8a5a', accent='#f0d8a0', pattern='kimono'), bottom_mat=leafy, legs_mat=M('scale', '#7a9a6a'),
           boots_mat=M('wood', '#5a4030'), arms_mat=M('scale', '#e8d8c0'), hands_mat=M('wood', '#5a7a40'))
    h.robe(leafy, flare=2.6)
    h.head_cube({'iris': '#c8a030', 'iris2': '#fff0a0', 'style': 'slit', 'mouth': 'smile'})
    h.hair('#749a66', style='very_long', length=20, tip='#a8d080', bangs='parted')
    for i, col in enumerate(['#ff9ab8', '#fff0a0', '#ffffff']):
        h.head.box((-3.5 + i * 3, h.head_top - 1, -4.75), (1, 1, 1), M('gem', col, glow=False), name='bloom')
    h.ears('elf', length=3)
    for side in ('r', 'l'):
        b, (x, y, z) = P.hand(h, side, (0.15, 0, 0))
        for k in range(3):
            b.box((x - 1 + k, y + 1.5, z - 0.5 + (k % 2)), (0, 3 + k % 2, 1), M('leaf', '#5a8a40'), name='vine_finger')
    for sx in (-1, 1):
        wing(r, h.torso, sx, (sx * 1.5, h.top + 3, 2.5), 'feather', M('feather', '#e8dcc0', tip='#8ab070'), span=13, height=12, rest=0.5)
    return r

@recipe
def ouroboros():
    # 無限円環 ウロボロス — 背に巨大な車輪を背負う穏やかな青年、時間・生命・宇宙の円環の象徴
    r = Rig('ouroboros')
    h = Humanoid(r, 'man', skin='#f4e0d4', accent='#dfb971')
    robe = M('cloth', '#3a455e', accent='#dfb971', trim=2, pattern='embroidery')
    h.body(top_mat=M('cloth', '#3a455e', accent='#dfb971', seam=True), bottom_mat=robe, legs_mat=M('cloth', '#2a3246'),
           boots_mat=M('cloth', '#1e2434'), arms_mat=M('cloth', '#3a455e', accent='#dfb971', trim=2))
    h.robe(robe, flare=2.0)
    h.head_cube({'iris': '#d8a840', 'iris2': '#fff0b0', 'style': 'calm', 'mouth': 'smile'})
    h.hair('#7a8092', style='long', length=10, tip='#a0a8b8')
    wheel = r.bone('wheel', h.torso, (0, h.top + 4, 5), anim='spin', ax=2, speed=0.02, cast=0.0)
    wheel.box((-11, h.top - 7, 5), (22, 22, 0), M('ring', '#b08a48', width=0.09, inner=0.84, spikes=12, spokes=8, glow_amount=0.35), name='wheel_front')
    wheel.box((-7, h.top - 3, 5.25), (14, 14, 0), M('ring', '#8ab0e8', width=0.07, inner=0.86, glow_amount=0.6), name='wheel_runes')
    wheel.box((-1.5, h.top + 2.5, 4.5), (3, 3, 1), M('gem', '#dfb971'), name='hub')
    return r

@recipe
def miyohime():
    # 万律自在神 御世姫命 — ナイトドレスと巫女服が融けた霊布、禍々しい王冠、極彩色の幾何学光輪、星海を封じた結晶群、
    # 黒・銀・虹に移ろう髪、罅割れの神紋
    r = Rig('miyohime')
    h = Humanoid(r, 'child', skin='#f8eef2', accent='#ba84f0')
    dress = M('cloth', '#342c54', accent='#ba84f0', trim=2, pattern='stars', pattern_glow=True)
    h.body(top_mat=M('cloth', '#f8f4fc', accent='#c02a4a', pattern='kimono'), bottom_mat=M('cloth', '#c02a4a'), legs_mat=M('cloth', '#342c54'),
           boots_mat=M('cloth', '#1a1428'), arms_mat=M('cloth', '#f8f4fc', accent='#c02a4a', trim=2),
           hands_mat=M('skin', '#f8eef2', accent='#ba84f0', pattern='cracks', pattern_glow=True))
    h.robe(dress, flare=3.0, split=True)
    h.kimono_sleeves(M('cloth', '#f8f4fc', accent='#ba84f0', trim=2, pattern='stars', pattern_glow=True), drop=4)
    h.head_cube({'iris': '#b070ff', 'iris2': '#7ffff0', 'style': 'big', 'mouth': 'smile', 'glow_eyes': True, 'marks': ['forehead']})
    h.hair('#dde2f0', style='very_long', length=18, tip='#c890ff', bangs='blunt')
    crown = r.bone('dread_crown', h.head, (0, h.head_top - 3, 0), anim='float', amp=0.4, speed=0.05)
    crown.box((-4, h.head_top - 3, -4), (8, 0, 8), M('ring', '#3a2a4a', width=0.25, spikes=7), name='crown')
    geo = r.bone('geo_halo', h.head, (0, h.head_top + 1, 6), rot=(1.57, 0, 0), anim='spin', speed=0.015)
    geo.box((-8, h.head_top + 1, 6 - 8), (16, 0, 16), M('ring', '#ffffff', width=0.08, inner=0.7, poly=7, rainbow=True), name='geo')
    orbiters(r, h.torso, (0, h.top + 6, 0), [M('gem', '#ba84f0'), M('gem', '#7ffff0'), M('gem', '#ff7fd0')], count=6, radius=9,
             size=2, speed=0.03, name='crystals')
    return r

@recipe
def innocence():
    # 無垢なる全能 — 白銀とも月光ともつかない柔らかな髪、青・金・紫に変わる大きな瞳、六、七歳ほどの小さな子供、玩具箱
    r = Rig('innocence')
    h = Humanoid(r, 'child', skin='#fdeee8', accent='#c993ff')
    dress = M('cloth', '#f6f6ff', accent='#c993ff', trim=2)
    h.body(top_mat=dress, bottom_mat=dress, legs_mat=M('cloth', '#ffffff'), boots_mat=M('cloth', '#e2e5ff'), arms_mat=dress, boots_h=2)
    h.skirt(M('cloth', '#e6e8ff', accent='#c993ff', trim=2), length=7, flare=1.6, tiers=2)
    h.head_cube({'iris': '#6a8aff', 'iris2': '#ffd76a', 'style': 'big', 'mouth': 'smile', 'blush': True, 'glow_eyes': True,
                 'heterochromia': '#c993ff'})
    h.hair('#edf1fb', style='long', length=11, tip='#d8c8ff', ahoge=True)
    h.halo(M('ring', '#d8b8ff', width=0.14, inner=0.6), radius=4, y=h.head_top - 2, tilt=0.25)
    box = r.bone('toybox', h.torso, (-7, h.top + 5, -2), anim='float', amp=0.8, speed=0.07)
    box.cbox((-7, h.top + 5, -2), (3, 3, 3), M('cloth', '#f0d0ff', accent='#ffffff', pattern='stars'), name='box')
    orbiters(r, h.torso, (0, h.top + 4, 0), [M('gem', '#ffd76a'), M('gem', '#6a8aff'), M('gem', '#c993ff')], count=5, radius=8,
             size=1, speed=0.04, name='toys')
    return r

@recipe
def brutality():
    # 凄惨たる暴虐 — 二メートルを超える巨体、黒褐色の肌、短く刈った髪、潰れた片目、全身の古傷、破砕拳刃
    r = Rig('brutality')
    h = Humanoid(r, 'large', skin='#6e4a36', accent='#e85130')
    h.body(top_mat=M('cloth', '#6e4a36', accent='#a87060', pattern='marks', hem_shadow=False), bottom_mat=M('cloth', '#382b26', accent='#e85130', trim=2),
           legs_mat=M('cloth', '#2a201c', pattern='marks', accent='#4a3a30'), boots_mat=M('cloth', '#1a1412'),
           arms_mat=M('cloth', '#6e4a36', accent='#a87060', pattern='marks'), hands_mat=M('cloth', '#d8c8b0', accent='#8a2a1a', pattern='marks'),
           neck=None)
    h.torso.box((-4, h.top + 2, -3.25), (8, 3, 0), M('skin', '#5e3e2c'), name='pecs')
    h.belt(M('cloth', '#3a2a20'), buckle=M('metal', '#7a6a5a'))
    h.shoulder_pads(M('metal', '#4a4048', rivets=True))
    h.head_cube({'iris': '#c0503a', 'style': 'fierce', 'scar': True, 'mouth': 'grin', 'line': '#1a1010', 'blink': False})
    h.hair('#201b20', style='short', length=4, side_locks=False, bangs='slick', shine=False)
    for side in ('r', 'l'):
        b, (x, y, z) = P.hand(h, side, (0, 0, 0))
        b.box((x - 2.5, y, z - 3), (5, 3, 1), M('metal', '#5a5054', rivets=True), grow=0.3, name='knuckle')
        for k in range(3):
            b.box((x - 2 + k * 1.5, y + 0.5, z - 4), (1, 1, 1), M('metal', '#9a9098'), name='spike')
    return r

@recipe
def cursed_love():
    # 邪沌の呪詛 — 腰まで流れる艶やかな黒髪、深い葡萄酒色の瞳、白い肌、穏やかで優しい微笑み、二十歳前後
    r = Rig('cursed_love')
    h = Humanoid(r, 'woman', skin='#faeceb', accent='#aa4b71')
    dress = M('cloth', '#351f36', accent='#aa4b71', trim=2, pattern='vine', pattern_glow=True)
    h.body(top_mat=M('cloth', '#351f36', accent='#e0a0b8', pattern='kimono'), bottom_mat=M('cloth', '#351f36'), legs_mat=M('cloth', '#1a1018'),
           boots_mat=M('cloth', '#120a10'), arms_mat=M('cloth', '#351f36', accent='#aa4b71', trim=2), hands_mat=M('cloth', '#1e121c'))
    h.skirt(dress, length=13, flare=1.8, tiers=2)
    h.head_cube({'iris': '#8a1838', 'iris2': '#e06a90', 'style': 'calm', 'mouth': 'smile'})
    h.hair('#1b1724', style='very_long', length=20, tip='#2a1a30', bangs='blunt')
    for i in range(3):
        h.head.box((3.5, h.head_top + 1 + i * 2, -3 + i), (2, 2, 1), M('gem', '#7a1030', glow=False), grow=0.25, name='rose')
    orbiters(r, h.torso, (0, h.top + 8, 0), M('plane', '#aa4b71', shape='leaf', glow=True), count=4, radius=9, speed=0.025,
             name='petals', shapes=[(2, 2, 0)])
    return r

@recipe
def relentless_research():
    # 戒進の研究 — 短く整えた銀髪、褐色の肌、細い金縁眼鏡、清潔な白衣、四十代、穏やかな声、研究器具
    r = Rig('relentless_research')
    h = Humanoid(r, 'woman', skin='#8e6650', accent='#8bdbc7')
    coat = M('cloth', '#f2f5f6', accent='#8bdbc7', trim=2)
    h.body(top_mat=M('cloth', '#2a3a3e', accent='#8bdbc7', pattern='band'), bottom_mat=M('cloth', '#2a3a3e'), legs_mat=M('cloth', '#2a3a3e'),
           boots_mat=M('cloth', '#1a2426'), arms_mat=coat, hands_mat=M('cloth', '#d8f0ea'), neck='round')
    h.jacket(M('cloth', '#f2f5f6', accent='#8bdbc7'))
    h.coat_tails(coat, length=13)
    h.torso.box((-3, h.top + 3, -2.5), (1, 2, 0), M('gem', '#8bdbc7'), name='badge')
    h.head_cube({'iris': '#4a8a7a', 'style': 'calm', 'mouth': 'smile', 'glasses': '#d8b050'})
    h.hair('#dadee4', style='short', length=6, bangs='swept')
    b, at = P.hand(h, 'r', (0.6, 0, 0))
    P.flask(b, at, M('gem', '#e0fff4', glow=False), M('energy', '#8bdbc7'))
    orbiters(r, h.torso, (0, h.top + 7, 0), [M('gem', '#8bdbc7'), M('gem', '#e07a7a'), M('gem', '#c8e070')], count=3, radius=9,
             speed=0.03, name='samples', shapes=[(1, 3, 1)])
    return r

@recipe
def fallen_savior():
    # 救堕せし勇者 — 首元までのくすんだ金髪、旅路で焼けた肌、かつて空のようだった蒼い瞳、修復を重ねた白銀の軽鎧、
    # 刃毀れ一つない古びた聖剣（右手に携える）
    r = Rig('fallen_savior')
    h = Humanoid(r, 'man', skin='#c09070', accent='#d9d589')
    h.body(top_mat=M('metal', '#bdc7d0', accent='#8a9098', pattern='marks', rivets=True), bottom_mat=M('cloth', '#4a4a50', accent='#d9d589', trim=2),
           legs_mat=M('cloth', '#3a3a40'), boots_mat=M('metal', '#9aa4ae'), arms_mat=M('cloth', '#5a5a62'), hands_mat=M('metal', '#aab4be'), neck=None)
    h.shoulder_pads(M('metal', '#c4ced6', accent='#8a9098', pattern='marks'))
    h.skirt(M('cloth', '#5a5a62', accent='#d9d589', trim=2), length=8, flare=1.2, tiers=1)
    h.cape(M('cloth', '#e8e0c8', accent='#7a7060', pattern='marks', trim=2), length=18)
    h.head_cube({'iris': '#5a7a9a', 'style': 'sad'})
    h.hair('#a89b68', style='bob', length=8, tip='#8a7e58', side_locks=False, bangs='messy')
    b, at = P.hand(h, 'r', P.POINT_FORWARD)
    P.sword(b, at, M('metal', '#f4f6ff', edge_glow='#fff6b0'), M('metal', '#d9d589'), M('cloth', '#3a3a6a'), length=15, width=2,
            guard_w=5, pommel=M('gem', '#9fd8ff'))
    sheath = r.bone('sheath', h.hips, (-4.5, h.hip_y - 2, -1), rot=(0.9, -0.1, 0.25))
    sheath.box((-5, h.hip_y - 2, -1.5), (1, 14, 2), M('cloth', '#4a3a2a', accent='#d9d589', trim=2), name='sheath')
    return r

@recipe
def sweet_pact():
    # 甘契の未怪 — 姿の一致しない旅商人、薄布で顔を隠す、安心する声と懐かしい匂い、甘い蜜の契約（甘蜜の契約書）
    r = Rig('sweet_pact')
    h = Humanoid(r, 'woman', skin='#f4e2d8', accent='#d8b175')
    robe = M('cloth', '#424153', accent='#d8b175', trim=2, pattern='embroidery')
    h.body(top_mat=M('cloth', '#424153', accent='#d8b175', seam=True), bottom_mat=robe, legs_mat=M('cloth', '#2e2d3a'),
           boots_mat=M('cloth', '#3a2a20'), arms_mat=M('cloth', '#525064', accent='#d8b175', trim=2), hands_mat=M('cloth', '#e8d8c0'), neck=None)
    h.robe(robe, flare=2.4)
    h.head_cube({'iris': '#d8a040', 'veil': '#5a5870', 'veil_eyes': '#ffcf6a'})
    h.hair('#9998a2', style='long', length=14)
    hood = r.bone('hood', h.head, (0, h.head_top, 0))
    hood.box((-4, h.head_top, -4), (8, 8, 8), M('hood', '#353446', accent='#d8b175'), grow=0.9, name='hood')
    hood.box((-4.5, h.head_top + 8, 3), (9, 6, 2), M('cloth', '#353446', accent='#d8b175', trim=2), name='hood_back')
    pack = r.bone('merchant_pack', h.torso, (0, h.top + 3, 2.5))
    pack.box((-3.5, h.top + 1, 2.5), (7, 8, 3), M('cloth', '#6a5038', accent='#d8b175', pattern='band'), name='pack')
    b, at = P.hand(h, 'l', (0.4, 0, 0))
    P.scroll(b, at, M('cloth', '#f6ead0', accent='#c03040', pattern='runes', pattern_glow=True), M('metal', '#d8b175'))
    for i in range(3):
        h.hips.box((-3 + i * 2.5, h.hip_y - 1, -2.75), (1, 2, 1), M('gem', ['#ffcf6a', '#ff9ab8', '#c8e070'][i]), name='honey_jar')
    return r

@recipe
def yggdrasil_avatar():
    # 玖天神樹 イグドラシル（顕現） — 淡い金緑色の髪のハイエルフの少女、若葉の瞳、長く尖った耳、枝葉と花を編み込んだ衣
    r = Rig('yggdrasil_avatar')
    h = Humanoid(r, 'child', skin='#faece4', accent='#cbdd83')
    h.body(top_mat=M('cloth', '#e8f4d0', accent='#6aa04a', pattern='vine'), bottom_mat=M('cloth', '#e8f4d0', accent='#6aa04a', pattern='vine'),
           legs_mat=M('skin', '#faece4'), boots_mat=M('wood', '#7a5a3a'), arms_mat=M('cloth', '#e8f4d0'), boots_h=2)
    h.skirt(M('leaf', '#6aa04a'), length=7, flare=1.6, tiers=1)
    h.head_cube({'iris': '#5ab040', 'iris2': '#d8ff9a', 'style': 'big', 'mouth': 'smile', 'blush': True})
    h.hair('#cadb8a', style='very_long', length=16, tip='#f0f0a0')
    h.ears('elf', length=4)
    wreath = r.bone('wreath', h.head, (0, h.head_top, 0))
    wreath.box((-4, h.head_top, -4), (8, 1, 8), M('leaf', '#5a9a3a'), grow=0.75, faces={'top': None, 'bottom': None}, name='wreath')
    for i, col in enumerate(['#ffd0e8', '#fff6b0', '#ffd0e8']):
        wreath.box((-3 + i * 3, h.head_top - 1, -5), (1, 1, 1), M('gem', col, glow=False), name='blossom')
    return r

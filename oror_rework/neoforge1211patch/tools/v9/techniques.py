"""(058) The 123 weapon techniques of the V9 design (特殊技Ⅰ・Ⅱ・武器専用必殺技 of each of the 41 god-slaying weapons), as
programs for the relic interpreter (RelicArts plus the ops of jp.oror.reborn.relic.RelicTech).

Each technique is what its design text says it does, op by op: what it reaches (a line, a fan, a ring, the point it
predicts, a chain), what it does there (its damage, a share of its base damage; holds, marks, broken armour, fields,
units), when (after/rep/pts: the time-differed hits), and how it is seen (cue: the 3D shapes the clients draw where the
server says, at the moment the server says). `tele` is the warning drawn while it is readied, `anim` the Epic Fight
motions tried in turn for the swing (the first one that exists is played).
"""

# ------------------------------------------------------------------------------------------------ the op vocabulary

def line(r, w=2.5): return {'op': 'line', 'r': r, 'w': w}
def cone(r, a=110): return {'op': 'cone', 'r': r, 'a': a}
def area(r, n=12): return {'op': 'area', 'r': r, 'n': n}
def spot(r, n=12): return {'op': 'spot', 'r': r, 'n': n}
def focus(r): return {'op': 'focus', 'r': r}
def predict(r, lead=10): return {'op': 'predict', 'r': r, 'lead': lead}
def ahead(d): return {'op': 'ahead', 'd': d}
def chain(n, r): return {'op': 'chain', 'n': n, 'r': r}
def allies(r): return {'op': 'allies', 'r': r}
def cap(n): return {'op': 'cap', 'n': n}
SELF = {'op': 'self'}
def dmg(m): return {'op': 'dmg', 'm': m}
def hp(pct, cap_): return {'op': 'hpdmg', 'pct': pct, 'cap': cap_}
def hold(s): return {'op': 'hold', 't': int(s * 20)}
def eff(e, s, a=0): return {'op': 'eff', 'e': e, 't': int(s * 20), 'a': a}
def buff(e, s, a=0): return {'op': 'buff', 'e': e, 't': int(s * 20), 'a': a}
def buffto(e, s, a=0): return {'op': 'buff', 'e': e, 't': int(s * 20), 'a': a, 'to': 1}
def armor(p, s): return {'op': 'armor', 'p': p, 't': int(s * 20)}
def atk(p, s): return {'op': 'atkdown', 'p': p, 't': int(s * 20)}
def regen(p, s): return {'op': 'regendown', 'p': p, 't': int(s * 20)}
STRIP = {'op': 'strip'}
STRIP1 = {'op': 'stripone'}
def knock(f=2.0): return {'op': 'knock', 'f': f}
def pull(f=1.5): return {'op': 'pull', 'f': f}
def launch(f=1.4): return {'op': 'launch', 'f': f}
def slam(f=3.0): return {'op': 'slam', 'f': f}
def mark(s, x): return {'op': 'mark', 't': int(s * 20), 'x': x}
def layer(k, n=1, mx=3, s=10): return {'op': 'layer', 'k': k, 'n': n, 'max': mx, 't': int(s * 20)}
def burst(k, m): return {'op': 'burst', 'k': k, 'm': m}
def drain(f): return {'op': 'drain', 'f': f}
def nextx(x, s=6): return {'op': 'nextx', 'x': x, 't': int(s * 20)}
def parry(s, m, x=1.5): return {'op': 'parry', 't': int(s * 20), 'm': m, 'x': x}
def grav(s): return {'op': 'gravity', 't': int(s * 20)}
def toy(s, scale=0.45): return {'op': 'toy', 't': int(s * 20), 's': scale}
def unit(k, n, s, hp_=200, m=0.05, rate=20, r=14, heal=0.0): return {'op': 'unit', 'k': k, 'n': n, 't': int(s * 20), 'hp': hp_, 'm': m, 'rate': rate, 'r': r, 'heal': heal}
def field(r, s, m=0.0, e=None, ea=0, rate=10, heal=0.0, name='field'):
    o = {'op': 'field', 'r': r, 't': int(s * 20), 'm': m, 'rate': rate, 'heal': heal, 'name': name}
    if e:
        o['e'], o['ea'] = e, ea
    return o
def reduce(p, s, to=False): return dict({'op': 'reduce', 'p': p, 't': int(s * 20)}, **({'to': 1} if to else {}))
def guard(s, to=False): return dict({'op': 'guard', 't': int(s * 20)}, **({'to': 1} if to else {}))
def undying(s, to=False): return dict({'op': 'undying', 't': int(s * 20)}, **({'to': 1} if to else {}))
def healpct(v, to=False): return dict({'op': 'healpct', 'v': v}, **({'to': 1} if to else {}))
def cleanse(to=False): return dict({'op': 'cleanse'}, **({'to': 1} if to else {}))
def punish(e, s): return {'op': 'punish', 'e': e, 't': int(s * 20)}
def seal(s): return {'op': 'seal', 't': int(s * 20)}
def blink(d): return {'op': 'blink', 'd': d}
BEHIND = {'op': 'behind'}
def back(d): return {'op': 'back', 'd': d}
def dash(f=2.4): return {'op': 'dash', 'f': f}
def leap(f=1.4): return {'op': 'leap', 'f': f}
SWAP = {'op': 'swap'}
SNAP = {'op': 'snapshot'}
REWIND = {'op': 'rewind'}
LIGHTNING = {'op': 'lightning'}
def after(t, *ops): return {'op': 'after', 't': t, 'ops': list(ops)}
def rep(n, gap, *ops): return {'op': 'rep', 'n': n, 'gap': gap, 'ops': list(ops)}
def pts(n, r, hr, gap, *ops): return {'op': 'pts', 'n': n, 'r': r, 'hr': hr, 'gap': gap, 'ops': list(ops)}
def cue(k, at='self', s=4.0, l=14, a=0.0, c=None, txt=None, h=None):
    o = {'op': 'cue', 'k': k, 'at': at, 's': s, 'l': l, 'a': a}
    if c is not None:
        o['c'] = c
    if txt:
        o['txt'] = txt
    if h is not None:
        o['h'] = h
    return o
def snd(s, v=1.0, pi=1.0): return {'op': 'sound', 's': s, 'v': v, 'pi': pi}
def mimic(m): return {'op': 'mimic', 'm': m}
def offer(heal, buff_e, buff_s, cost_e, cost_s, r=16): return {'op': 'offer', 'heal': heal, 'e': buff_e, 'bt': int(buff_s * 20), 'cost': cost_e, 'ct': int(cost_s * 20), 'r': r}
def contracts(*ops): return {'op': 'contracts', 'ops': list(ops)}
def janken(rock, scissors, paper): return {'op': 'janken', 'rock': rock, 'scissors': scissors, 'paper': paper}
def colortag(r, m): return {'op': 'colortag', 'r': r, 'm': m}
def tag(k, s=10): return {'op': 'tag', 'k': k, 't': int(s * 20)}
def iftag(k, *ops): return {'op': 'iftag', 'k': k, 'ops': list(ops)}
def water(*ops): return {'op': 'inwater', 'ops': list(ops)}
def strong(*ops): return {'op': 'strong', 'ops': list(ops)}

# the Epic Fight motions by weapon kind (fallbacks in order; a name this Epic Fight lacks is passed over)
ANIM = {
    'katana': [['UCHIGATANA_SHEATHING_AUTO', 'UCHIGATANA_AUTO1'], ['UCHIGATANA_SHEATHING_DASH', 'UCHIGATANA_DASH'], ['BATTOJUTSU_DASH', 'BATTOJUTSU', 'UCHIGATANA_SKILL', 'FATAL_DRAW']],
    'sword': [['SWORD_AUTO2', 'SWORD_AUTO1'], ['SWORD_DASH', 'DANCING_EDGE'], ['SWEEPING_EDGE', 'SWORD_AIR_SLASH']],
    'greatsword': [['GREATSWORD_AUTO1'], ['GREATSWORD_DASH', 'GIANT_WHIRLWIND'], ['STEEL_WHIRLWIND', 'GIANT_WHIRLWIND', 'GREATSWORD_AUTO2']],
    'polearm': [['SPEAR_TWOHAND_AUTO1', 'SPEAR_ONEHAND_AUTO'], ['SPEAR_DASH', 'SPEAR_SLASH'], ['SPEAR_THRUST', 'SPEAR_TWOHAND_AUTO2']],
    'fist': [['FIST_AUTO1'], ['FIST_AUTO3', 'FIST_DASH'], ['RELENTLESS_COMBO', 'FIST_DASH']],
    'rapier': [['SPEAR_ONEHAND_AUTO', 'SWORD_AUTO1'], ['SWORD_DASH', 'SPEAR_DASH'], ['SPEAR_THRUST', 'SWORD_AUTO3']],
    'scythe': [['AXE_AUTO1', 'GREATSWORD_AUTO1'], ['AXE_DASH', 'GREATSWORD_DASH'], ['GUILLOTINE_AXE', 'GREATSWORD_AUTO2']],
    'heavy': [['AXE_AUTO1', 'GREATSWORD_AUTO1'], ['AXE_AUTO2', 'GREATSWORD_AUTO2'], ['GUILLOTINE_AXE', 'METEOR_SLAM', 'AXE_DASH']],
    'toyhammer': [['AXE_AUTO1'], ['AXE_AUTO2'], ['GUILLOTINE_AXE', 'AXE_DASH']],
    'whip': [['SWORD_AUTO1', 'DAGGER_AUTO1'], ['SWORD_AUTO3', 'DAGGER_AUTO3'], ['DANCING_EDGE', 'SWORD_DASH']],
    'chakram': [['DAGGER_DUAL_AUTO1', 'DAGGER_AUTO1'], ['DAGGER_DUAL_AUTO3', 'DAGGER_AUTO3'], ['DAGGER_DUAL_DASH', 'BLADE_RUSH_COMBO1', 'DAGGER_DASH']],
    'shield': [['SWORD_AUTO1'], ['SWORD_AUTO2'], ['SWORD_AUTO3']],
    'magic': [['SPEAR_ONEHAND_AUTO'], ['SPEAR_ONEHAND_AUTO'], ['SPEAR_TWOHAND_AUTO1']],
    'bow': [[], [], []], 'gatling': [[], [], []], 'cannon': [[], [], []],
}

T = {}


def tech(no, slot, tele, prog, wind=None):
    """tele: the warning shape (line/cone/circle/target/self/ring, its reach); prog: the ops at release."""
    T[(no, slot)] = {'tele': tele, 'prog': prog, 'wind': wind}


def tl(r, w=2.5): return {'k': 'line', 'r': r, 'w': w}
def tc(r, a=110): return {'k': 'cone', 'r': r, 'a': a}
def tr(r): return {'k': 'circle', 'r': r}
def tt(r, ar=4): return {'k': 'target', 'r': r, 'ar': ar}
def ts(r=3): return {'k': 'self', 'r': r}

# ------------------------------------------------------------------------------------------------ 01 剣神 炬珀 (katana)
tech(1, 0, tl(16, 2.0), [  # 断装・水鏡: the flat parries; half-drawn, a slant cut; 16 m guard-breaking line, two layers of 剣理印
    parry(1.0, 0.25, 1.6), cue('flash', 'self', 1.2, 8), cue('slash', 'self', 3.0, 10, a=35),
    line(16, 2.0), dmg(1.0), armor(0.4, 8), layer('kenri', 2, 2, 12), cue('wave', 'line', 16, 10, a=35), cue('spikes', 't', 1.2, 10)])
tech(1, 1, tt(26, 4), [  # 影縫い・無音: seven after-images, round to the back; sideways cut + return iai at the predicted point
    predict(26, 12), cue('wings', 'self', 1.0, 18, txt='afterimage'), BEHIND, spot(4.5, 6), dmg(0.5), cue('slash', 'at', 3.5, 9, a=0),
    after(6, predict(26, 6), spot(4.5, 6), dmg(0.5), burst('kenri', 0.2), cue('slash', 'at', 3.5, 9, a=180), cue('flash', 'at', 2.0, 8))])
tech(1, 2, tl(42, 1.5), [  # 終ノ太刀・無我: silence, half a step, the 42 m line, the sheathing breaks every cut at once
    cue('ring', 'self', 8, 30, c=0xEEF4FF), line(42, 1.5), armor(0.6, 10), seal(6), cue('beam', 'line', 42, 30, a=0.25),
    after(14, line(42, 1.5), dmg(1.0), burst('kenri', 0.15), cue('slash', 'line', 42, 12, a=90), cue('flash', 't', 2.5, 10), snd('glass', 1.0, 1.4))])

# ------------------------------------------------------------------------------------------------ 02 天冠詠者 理覇 (magic)
tech(2, 0, tl(18, 3), [  # 「とまれ」: three strokes, the last dot sticks the golden word to the foe; bosses only slowed
    line(18, 3), cap(4), cue('text', 't', 1.6, 40, txt='とまれ'), hold(2.0), dmg(1.0), cue('flash', 't', 1.4, 8)])
tech(2, 1, tr(18), [  # 「逆になあれ」: gravity reversed for 3 s in 18 m; fall damage on the way back limited
    area(18, 12), cue('text', 'self', 2.4, 40, txt='逆になあれ'), cue('circle', 'self', 18, 60), grav(3.0), dmg(0.6),
    after(60, area(18, 12), dmg(0.4), cue('ring', 'self', 18, 14))])
tech(2, 2, tr(32), [  # 「ほんとうになあれ」: stars, then floating, then the castle's guns; small guard words on friends
    cue('circle', 'self', 6, 70, a=1), cue('text', 'self', 3, 60, txt='ほんとうになあれ'),
    allies(32), guard(3.0, True), reduce(0.3, 8, True),
    focus(32), pts(12, 8, 3.0, 2, dmg(0.03), cue('rain', 'at', 1.5, 12)),
    after(26, area(32, 12), launch(1.2), dmg(0.25), cue('ring', 'self', 16, 16)),
    after(46, focus(32), spot(7, 12), dmg(0.4), cue('pillar', 'at', 4, 20, h=14), cue('flash', 'at', 4, 12), snd('blast', 1.0, 0.8))])

# ------------------------------------------------------------------------------------------------ 03 唯我万象 天輝 (greatsword)
tech(3, 0, tr(12), [  # 唯我・拒絶: the golden lines turn outward; own holds and debuffs gone; 12 m refusal shock (no friends)
    SELF, cleanse(), cue('ring', 'self', 12, 14, c=0xFFD45A), area(12, 12), dmg(1.0), knock(2.4), cue('dome', 'self', 2.5, 12)])
tech(3, 1, tl(22, 3), [  # 宣拳・万障: walking on, the barrier splits; 22 m of guards and shields broken stage by stage
    rep(3, 6, line(22, 3), armor(0.25, 10), dmg(0.25), cue('wave', 'line', 22, 8)),
    after(18, line(22, 3), {'op': 'shieldbreak'}, dmg(0.25), cue('flash', 't', 2, 10), snd('glass', 1.0, 0.8))])
tech(3, 2, tl(32, 3), [  # 我は在る、故に成る: one step, the golden outline pushes spells away, a great palm strike
    SELF, cleanse(), reduce(0.5, 4), cue('dome', 'self', 3.5, 30, c=0xFFD45A), {'op': 'erase', 'r': 24},
    after(18, line(32, 3), dmg(1.0), knock(3.0), cue('fist', 'line', 32, 12), cue('beam', 'line', 32, 12, a=0.6), snd('blast', 1.0, 0.6))])

# ------------------------------------------------------------------------------------------------ 04 万象混沌 カオス (magic)
tech(4, 0, tc(17, 70), [  # 異相侵食: tentacles and crystals in a fan, multi-stab; eroding floor; the branch's colour shown first
    {'op': 'branch', 'ops': [
        [cue('text', 'self', 1.2, 20, txt='毒', c=0x7CFF5A), cone(17, 70), dmg(0.3), eff('poison', 4, 1)],
        [cue('text', 'self', 1.2, 20, txt='衰', c=0x9A5AFF), cone(17, 70), dmg(0.3), eff('wither', 4, 1)],
        [cue('text', 'self', 1.2, 20, txt='鈍', c=0x5ACFFF), cone(17, 70), dmg(0.3), eff('slow', 4, 2)]]},
    rep(3, 4, cone(17, 70), dmg(0.2), cue('spikes', 't', 1.4, 10)), ahead(8), field(5, 6, m=0.02, e='poison', ea=0, name='erosion')])
tech(4, 1, tr(19), [  # 混沌胞子: three spore-born shapes, one each: binder, gunner, guard; broken ones stop regrowing
    cue('orb', 'self', 1.6, 20), unit('binder', 1, 15, 300, 0.02, 30, 10), unit('gunner', 1, 15, 300, 0.06, 15, 19), unit('warden', 1, 15, 600, 0.0, 40, 8),
    area(19, 12), dmg(0.4), cue('ring', 'self', 19, 14)])
tech(4, 2, tr(29), [  # 万象再分化: the black orb, four stages: crystal, liquid, mist, tentacles; the last one by layers
    cue('orb', 'self', 4, 60), area(29, 12), layer('erosion', 1, 4, 12), dmg(0.15), cue('spikes', 'self', 10, 14),
    after(10, area(29, 12), layer('erosion', 1, 4, 12), dmg(0.15), cue('ring', 'self', 29, 14, c=0x3A9AFF)),
    after(20, area(29, 12), layer('erosion', 1, 4, 12), dmg(0.15), eff('blind', 2), cue('dome', 'self', 8, 20, c=0x8A6AFF)),
    after(30, area(29, 12), burst('erosion', 0.12), dmg(0.4), pull(1.2), cue('chain', 't', 1, 16), cue('flash', 'self', 5, 12))])

# ------------------------------------------------------------------------------------------------ 05 万界錬成 ベーリット (fist)
tech(5, 0, tl(14, 2.5), [  # 金晶・瞬成: two golden crystal fists alternately; 14 m fist pressure and crystal thrust; brittle armour
    line(14, 2.5), dmg(0.5), armor(0.35, 10), cue('fist', 'line', 14, 10, c=0xFFD45A),
    after(5, line(14, 2.5), dmg(0.5), cue('spikes', 'line', 14, 10, c=0xFFE9A0))])
tech(5, 1, ts(3), [  # 概念合金: 20 s of the fused arms: fire when close, frost crystals when far
    SELF, buff('strength', 20, 2), {'op': 'stance', 'k': 'alloy', 't': 400}, cue('orb', 'self', 1.4, 20, c=0xFF7A3A), cue('ring', 'self', 4, 20, c=0x8AE0FF),
    area(18, 12), dmg(0.5), {'op': 'burn', 's': 4}, eff('slow', 4, 2)])
tech(5, 2, tr(27), [  # 完全なる新物質: metal stakes bind, a star-metal sword cuts many times, a dense mass falls in the middle
    focus(27), spot(8, 12), hold(2.5), cue('spikes', 'at', 6, 30),
    after(10, rep(5, 3, spot(8, 12), dmg(0.08), cue('slash', 'at', 4, 8))),
    after(30, spot(8, 12), dmg(0.6), slam(2.0), cue('pillar', 'at', 3, 18, h=24), cue('ring', 'at', 8, 14), snd('anvil', 1.0, 0.6))])

# ------------------------------------------------------------------------------------------------ 06 星脈魔祖 エルセリア (magic)
tech(6, 0, tl(25, 2), [  # 七曜魔陣: seven small circles in a row, seven coloured stars in turn; a weak element struck again
    cue('circle', 'self', 1.0, 30, a=1), rep(7, 3, focus(25), dmg(0.12), {'op': 'elements'}, cue('wave', 'line', 25, 8))])
tech(6, 1, tr(30), [  # 九霆雷雲: nine ring-clouds, nine strikes; chain lightning to the marked; cover is checked
    cue('circle', 'self', 4, 40, h=8), focus(30), pts(9, 9, 3.0, 3, {'op': 'sky'}, dmg(0.09), LIGHTNING, cue('pillar', 'at', 1.0, 10, h=16, c=0xA0C8FF), layer('star', 1, 3, 10)),
    after(30, focus(30), chain(5, 10), iftag('star', dmg(0.2)), cue('chain', 't', 1, 12, c=0xC8E0FF))])
tech(6, 2, tr(38), [  # 原初星魔: star barrage, thunder cloud, element pillar; friends' magic a little stronger
    allies(38), buffto('strength', 8, 0), cue('circle', 'self', 12, 80),
    focus(38), pts(14, 10, 2.5, 1, dmg(0.03), cue('rain', 'at', 1.0, 10)),
    after(22, focus(38), pts(6, 8, 3.5, 2, {'op': 'sky'}, dmg(0.05), LIGHTNING, cue('pillar', 'at', 1.2, 10, h=16))),
    after(44, focus(38), spot(8, 12), dmg(0.5), cue('pillar', 'at', 5, 24, h=30), cue('flash', 'at', 5, 12))])

# ------------------------------------------------------------------------------------------------ 07 万機創匠 ヴァレリア (heavy)
tech(7, 0, tl(30, 2), [  # 磁軌斉射: the head splits into a railgun; 30 m line; foes' guards shaken
    line(30, 2), dmg(1.0), {'op': 'shieldbreak'}, knock(1.5), cue('beam', 'line', 30, 10, a=0.4, c=0x6AD8FF), cue('ring', 'self', 2, 8)])
tech(7, 1, ts(3), [  # 重装換装: 18 s of heavy frame: guard up, foes' footing broken, short homing shots
    SELF, buff('resist', 18, 1), {'op': 'stance', 'k': 'heavy', 't': 360}, cue('dome', 'self', 1.6, 30, c=0x6AD8FF),
    area(18, 8), dmg(0.4), eff('slow', 3, 2), unit('missile', 1, 18, 9999, 0.04, 12, 18)])
tech(7, 2, tr(32), [  # 零式機神: triple barrage, then a great electromagnetic hammer falls; broken arms lower the last blow
    cue('wings', 'self', 1.6, 50, c=0x6AD8FF), unit('arm', 3, 4, 200, 0.0, 99, 6),
    rep(3, 6, focus(32), spot(5, 12), dmg(0.12), cue('beam', 'self', 32, 8, a=0.5)),
    after(26, focus(32), spot(8, 12), {'op': 'armsdmg', 'm': 0.64}, slam(2.4), cue('fist', 'at', 4, 16), cue('ring', 'at', 9, 14), snd('anvil', 1.0, 0.5))])

# ------------------------------------------------------------------------------------------------ 08 黄天龍仙 皇玲華 (polearm)
tech(8, 0, tl(16, 2.5), [  # 黄龍掌: the palm frees a small dragon, the spear follows; a line of dragon-qi and two palms; thunder marks
    line(16, 2.5), dmg(0.5), layer('thunder', 1, 3, 10), cue('wave', 'line', 16, 10, c=0xFFD45A),
    after(5, line(16, 2.5), dmg(0.5), cue('fist', 'line', 16, 8, c=0xFFE58A))])
tech(8, 1, tr(26), [  # 九霄雷陣: nine charms rise as dragons; nine strikes; footing hampered; chained in water
    focus(26), pts(9, 9, 3.0, 2, {'op': 'sky'}, dmg(0.1), LIGHTNING, eff('slow', 3, 1), cue('pillar', 'at', 1.0, 10, h=14, c=0xC8A0FF),
                 water(chain(3, 6), dmg(0.05)))])
tech(8, 2, tl(34, 3), [  # 九龍天帝降臨: water dragons bind, nine thunder pillars, a golden piercing spear; 20 s of dragon blessing
    SELF, buff('strength', 20, 2), buff('speed', 20, 1), cue('wings', 'self', 2.2, 60, c=0xFFD45A),
    focus(34), spot(7, 12), hold(2.0), cue('chain', 't', 1, 20, c=0x6AC8FF),
    after(12, focus(34), pts(9, 7, 2.5, 1, dmg(0.04), LIGHTNING, cue('pillar', 'at', 1.0, 10, h=18))),
    after(32, line(34, 3), dmg(0.64), cue('beam', 'line', 34, 14, a=0.7, c=0xFFD45A), snd('roar', 1.0, 1.2))])

# ------------------------------------------------------------------------------------------------ 09 文明遊匠 フェルディナント (gatling)
tech(9, 0, tl(40, 1.5), [  # 工業斉射: three barrels, three rows of 40 m; cover weakens the shot behind it; armour worn
    {'op': 'rows', 'n': 3, 'r': 40, 'w': 1.5, 'gap': 2.5, 'ops': [dmg(0.33), armor(0.2, 8)]}, cue('arrows', 'self', 40, 10, c=0xFFB25A)])
tech(9, 1, ts(3), [  # 補給線再構: 15 s of supply: ammunition, faster attacks, friends supplied; heavy shot
    allies(22), buffto('haste', 15, 1), buffto('strength', 15, 0), cue('ring', 'self', 22, 20), SELF, {'op': 'stance', 'k': 'supply', 't': 300},
    unit('drone', 2, 15, 120, 0.02, 20, 16)])
tech(9, 2, tr(42), [  # 万界産業連合: a rail gate, tanks, turrets, planes; three barrages; broken supply weakens the rest
    unit('depot', 1, 8, 300, 0.0, 99, 4),
    focus(42), {'op': 'depotdmg', 'ops': [spot(9, 12), dmg(0.2), cue('rain', 'at', 6, 14)]},
    after(16, focus(42), {'op': 'depotdmg', 'ops': [line(42, 3), dmg(0.3), cue('beam', 'line', 42, 10, a=0.7)]}),
    after(32, focus(42), {'op': 'depotdmg', 'ops': [spot(12, 12), dmg(0.5), cue('pillar', 'at', 6, 20, h=24), cue('ring', 'at', 12, 14)]})])

# ------------------------------------------------------------------------------------------------ 10 至高武王 メルス (polearm; a liquid blade)
tech(10, 0, tc(5, 70), [  # 流体崩拳: the blade shrinks to a fist; 5 m precise blow; staggered by the shield's angle
    cone(5, 70), cap(3), dmg(1.0), {'op': 'stagger'}, cue('fist', 'self', 5, 8, c=0x8AE0FF), cue('ring', 't', 1.5, 8)])
tech(10, 1, ts(3), [  # 水月空転: the blade winds along the foe's weapon; parry window: counter and a throw; the big only staggered
    parry(1.2, 0.6, 1.4), {'op': 'throw', 'm': 0.4}, cue('dome', 'self', 1.4, 24, c=0x8AE0FF)])
tech(10, 2, ts(3), [  # 武王極意・万法一触: up to three of the foe's blows stored, gathered into one reflected strike (capped)
    {'op': 'store', 't': 60, 'n': 3}, cue('dome', 'self', 1.8, 60, c=0x8AE0FF),
    after(60, cone(7, 90), {'op': 'release', 'm': 1.0}, cue('fist', 'self', 7, 12), cue('flash', 't', 2, 10))])

# ------------------------------------------------------------------------------------------------ 11 典域工廠 ヘファイストス (polearm)
tech(11, 0, tl(18, 1.8), [  # 構造測量: a survey ring on the spear point; 18 m thrust; weak points found; later cuts pierce more
    line(18, 1.8), dmg(1.0), tag('surveyed', 30), armor(0.3, 30), cue('beam', 'line', 18, 10, a=0.3, c=0x6AD8FF), cue('circle', 't', 1.2, 30)])
tech(11, 1, ts(3), [  # 対属性兵装: heat blade, field blade, reactive shield; 12 s of guard and counter
    SELF, {'op': 'adapt', 't': 240}, guard(0.5), parry(12, 0.15, 1.3), cue('dome', 'self', 1.6, 30, c=0xFF7A3A)])
tech(11, 2, tr(30), [  # 全機神兵装解放: interceptor armour, machine arms bind, spear and cannon; scrap collected
    SELF, reduce(0.5, 6), {'op': 'erase', 'r': 24}, cue('dome', 'self', 2.2, 40),
    after(10, focus(30), spot(6, 12), hold(2.0), cue('chain', 't', 1, 16)),
    after(24, focus(30), spot(8, 12), dmg(1.0), cue('beam', 'self', 30, 14, a=0.8), cue('pillar', 'at', 3, 16, h=12)),
    after(26, {'op': 'give', 'item': 'iron', 'n': 4})])

# ------------------------------------------------------------------------------------------------ 12 無法遊戯 ノルティア (toyhammer)
tech(12, 0, tr(16), [  # 色鬼: four colour circles; only the named colour is safe; the wrong ones get a short star fall
    colortag(16, 1.0)])
tech(12, 1, tc(18, 100), [  # じゃんけん宣告: rock smashes, scissors cross-cut, paper blows a fan away; the hand shown first
    janken([focus(18), spot(4, 6), dmg(1.0), slam(2.0), cue('fist', 'at', 3, 12)],
           [cone(18, 60), dmg(0.5), cue('slash', 'self', 6, 10, a=45), after(4, cone(18, 60), dmg(0.5), cue('slash', 'self', 6, 10, a=-45))],
           [cone(18, 120), dmg(0.8), knock(3.0), cue('wave', 'self', 18, 12)])])
tech(12, 2, tr(27), [  # 万界遊園: balloons, a charging horse, star cannon; a game won cancels the forfeits
    focus(27), pts(8, 8, 2.5, 2, dmg(0.04), launch(0.8), cue('orb', 'at', 1.0, 10, c=0xFF8AD8)),
    after(18, line(27, 3), dmg(0.3), knock(2.0), cue('wave', 'line', 27, 14)),
    after(34, focus(27), spot(8, 12), dmg(0.38), cue('rain', 'at', 6, 16, c=0xFFE14A), cue('flash', 'at', 4, 10)),
    SELF, cleanse()])

# ------------------------------------------------------------------------------------------------ 13 失楽堕天 ルシファーラ (scythe)
tech(13, 0, tl(18, 2.5), [  # 欲望の鏡: a black mirror returns the last element struck with; healed foes wither more
    mimic(0.8), line(18, 2.5), dmg(0.2), {'op': 'healed', 'ops': [eff('wither', 5, 2)]}, cue('dome', 'self', 1.4, 14, c=0x5A1A2A)])
tech(13, 1, tr(24), [  # 黒翼円舞: a thousand feathers, the scythe cuts the petals; 24 m whirl and drain (friends spared)
    cue('wings', 'self', 2.4, 30, c=0x1A0A14), rep(4, 4, area(24, 12), dmg(0.25), cue('slash', 'self', 8, 8, a=0)), drain(0.002)])
tech(13, 2, tr(28), [  # 失楽女王・万願王冠: seven black-rose crowns; seven desire marks burst; some healing; theft capped
    cue('circle', 'self', 8, 70, c=0x8A1A3A), area(28, 7), {'op': 'strip', 'steal': 1},
    rep(7, 4, area(28, 12), dmg(0.12), cue('pillar', 't', 0.8, 10, h=8, c=0xFF3A5A)), drain(0.001)])

# ------------------------------------------------------------------------------------------------ 14 超克覇王 辿迦 (fist)
tech(14, 0, tc(4, 60), [  # 覇王崩拳: the left traps the elbow, the right's inch strike through the chest; guards pierced
    cone(4, 60), cap(2), dmg(1.0), {'op': 'shieldbreak'}, armor(0.4, 8), cue('fist', 'self', 4, 8, c=0xFF5A2A), cue('ring', 't', 2, 10)])
tech(14, 1, ts(3), [  # 百家返し: watch the stance; throw a charge, turn a cut, punch a shot; 18 ticks of counter window
    parry(0.9, 0.8, 1.5), cue('dome', 'self', 1.2, 18, c=0xFF5A2A)])
tech(14, 2, tl(14, 3), [  # 百錬超克天衝: nine steps, the great fist; the last of nine carries the weight
    rep(8, 3, cone(6, 80), dmg(0.03), cue('fist', 'self', 4, 6)),
    after(26, line(14, 3), dmg(0.76), knock(3.0), cue('fist', 'line', 14, 14, c=0xFF5A2A), cue('beam', 'line', 14, 12, a=0.9), snd('blast', 1.0, 0.6))])

# ------------------------------------------------------------------------------------------------ 15 覚醒進化 メアリー・スー (magic)
tech(15, 0, tl(15, 2.5), [  # 英雄覚醒: a light sword in a master's form: thrust, circle cut or guard-return by the foe's weapon
    {'op': 'byfoe', 'r': 15, 'melee': [area(6, 8), dmg(1.0), cue('slash', 'self', 6, 10)],
     'ranged': [line(15, 2), dmg(1.0), cue('beam', 'line', 15, 10, a=0.3)], 'none': [parry(1.0, 0.4, 1.4), cue('dome', 'self', 1.2, 20)]}])
tech(15, 1, ts(3), [  # 忘れていた切札: the least-used element, 15 s only
    SELF, {'op': 'stance', 'k': 'trump', 't': 300}, cue('text', 'self', 1.6, 30, txt='切札'), focus(18), dmg(0.5), {'op': 'elements'}])
tech(15, 2, tl(30, 3), [  # 万界英雄譚: five light swords and the finish; a guard by the misses in this fight
    SELF, {'op': 'missguard'}, rep(5, 4, focus(30), spot(4, 6), dmg(0.1), cue('slash', 'at', 3, 8)),
    after(24, line(30, 3), dmg(0.5), cue('beam', 'line', 30, 14, a=0.8, c=0xFFF0A0), cue('flash', 't', 3, 10))])

# ------------------------------------------------------------------------------------------------ 16 救世天主 セイヴァー (shield)
tech(16, 0, tr(16), [  # 守護光翼: six wings, a half dome; 10 s of guard and cleansing for friends; charges pushed back unharmed
    allies(16), guard(1.0, True), reduce(0.4, 10, True), cleanse(True), cue('dome', 'self', 6, 40, c=0xFFF6D0), cue('wings', 'self', 1.8, 30),
    area(16, 12), knock(2.0), {'op': 'nonlethal'}, dmg(1.0)])
tech(16, 1, tr(22), [  # 絶対救命: white hands pull the fallen to safety; 35% back and one death warded
    allies(22), healpct(0.35, True), undying(30, True), {'op': 'gather', 'r': 22}, cue('pillar', 't', 1.0, 20, h=6, c=0xFFF6D0)])
tech(16, 2, tr(32), [  # 万象救済: twelve wings over the sky; 70% back and cleansed; a barrier strike that never kills
    allies(32), healpct(0.7, True), cleanse(True), reduce(0.5, 6, True), cue('wings', 'self', 4, 60), cue('dome', 'self', 12, 60, c=0xFFF6D0),
    area(32, 12), {'op': 'nonlethal'}, dmg(1.0), knock(1.5)])

# ------------------------------------------------------------------------------------------------ 17 外業呪禍 獄華 (fist)
tech(17, 0, tc(6, 90), [  # 呪紋爪: left claw carves, right claw opens; black soul fire; wither and lasting harm (curable)
    rep(4, 3, cone(6, 90), dmg(0.2), cue('slash', 'self', 2.5, 6, c=0x6A2A8A)), cone(6, 90), dmg(0.2), layer('curse', 1, 3, 10), eff('wither', 5, 1),
    cue('pillar', 't', 0.8, 10, h=4, c=0x8A3AFF)])
tech(17, 1, tr(18), [  # 千呪連鎖: roots of black tentacles; flowers bloom and burst in a chain; up to six; spreads by closeness
    focus(18), chain(6, 6), dmg(1.0), layer('curse', 1, 3, 10), eff('wither', 4, 0), cue('chain', 't', 1, 14, c=0x8A3AFF), cue('ring', 't', 1.5, 10)])
tech(17, 2, tr(25), [  # 獄華開門: the flower opens into a gate; many hits in the cursed field; layers spent for the finish
    cue('circle', 'self', 10, 60, c=0x4A0A3A), ahead(4), field(12, 3, m=0.04, e='wither', ea=1, rate=10, name='hellgate'),
    after(40, area(25, 12), burst('curse', 0.15), dmg(0.6), cue('pillar', 'self', 6, 20, h=20, c=0x8A3AFF), snd('wither', 1.0, 0.7))])

# ------------------------------------------------------------------------------------------------ 18 魔導深淵 メルリヌス (magic)
tech(18, 0, tl(24, 3), [  # 逆算術式: a reversed equation; spells reflected and partly undone; extra harm to casters
    {'op': 'reflect', 't': 60, 'r': 24}, {'op': 'erase', 'r': 12}, line(24, 3), dmg(0.6), {'op': 'casters', 'ops': [dmg(0.4)]},
    cue('circle', 'self', 3, 30, a=1, c=0xB08AFF)])
tech(18, 1, tr(22), [  # 術理反証: three proof circles; one magic buff undone; next attack stronger when it works
    focus(22), cue('circle', 'at', 3, 40, c=0xB08AFF), {'op': 'stripone', 'then': [{'op': 'nextx', 'x': 1.6, 't': 160}]}, dmg(1.0)])
tech(18, 2, tr(32), [  # 全法則術式化: the foe's last element read; three barrages of its opposite
    cue('circle', 'self', 10, 70, c=0xB08AFF), rep(3, 10, focus(32), spot(6, 12), dmg(0.33), {'op': 'elements'}, cue('pillar', 'at', 3, 14, h=14))])

# ------------------------------------------------------------------------------------------------ 19 災極海獣 淵煌 (polearm)
tech(19, 0, tl(18, 3), [  # 深海電界: a water membrane, a band of discharge; more links in water
    line(18, 3), dmg(1.0), eff('slow', 2, 1), water(chain(4, 6), dmg(0.2)), cue('beam', 'line', 18, 10, a=0.8, c=0x5AE0D0), cue('chain', 't', 1, 10)])
tech(19, 1, tr(12), [  # 圧壊渦潮: a black whirl on the legs; pulled in and crushed; poison stacked adds harm
    ahead(4), spot(12, 12), pull(1.8), cue('ring', 'at', 12, 30, c=0x1A3A6A), rep(3, 8, spot(5, 12), dmg(0.3), {'op': 'poisoned', 'ops': [dmg(0.1)]}), field(5, 3, m=0.02, name='whirl')])
tech(19, 2, tr(30), [  # 原初深淵形態: a deep-sea jaw from above; water pillars, poison tentacles, thunder; for sea foes more
    cue('orb', 'self', 5, 50, c=0x1A3A6A), area(30, 12), dmg(0.3), eff('poison', 6, 2), cue('pillar', 't', 1.4, 14, h=10, c=0x5AE0D0),
    after(14, area(30, 12), dmg(0.3), LIGHTNING, eff('slow', 4, 2)),
    after(28, area(30, 12), dmg(0.4), {'op': 'aquatic', 'ops': [dmg(0.4)]}, cue('ring', 'self', 30, 16), snd('roar', 1.0, 0.6))])

# ------------------------------------------------------------------------------------------------ 20 嶺脈地龍 クールマ (heavy)
tech(20, 0, tl(22, 3), [  # 地脈破砕: the vein struck; 22 m line quake; three small rock pillars follow
    line(22, 3), dmg(0.4), launch(0.8), cue('spikes', 'line', 22, 14, c=0x5ACF8A),
    after(5, line(22, 3), dmg(0.2), cue('spikes', 'line', 22, 10)), after(10, line(22, 3), dmg(0.2)), after(15, line(22, 3), dmg(0.2), cue('ring', 'self', 6, 10))])
tech(20, 1, tr(22), [  # 万晶砲台: green crystal towers; three turrets for 10 s; each can be broken
    unit('crystal', 3, 10, 400, 0.05, 15, 22), cue('spikes', 'self', 4, 20, c=0x5ACF8A)])
tech(20, 2, tr(30), [  # 大地そのもの: mountains and crystals in a ring; three crust attacks; the landing shown; the ground as before
    cue('ring', 'self', 30, 50, c=0x5ACF8A), rep(3, 12, area(30, 12), dmg(0.33), launch(1.0), cue('spikes', 'self', 15, 14)), after(36, cue('flash', 'self', 6, 12))])

# ------------------------------------------------------------------------------------------------ 21 光越天龍 テイア (bow)
tech(21, 0, tl(48, 1.2), [  # 光速閃航: three arrows, each on its own path; 48 m pierce; more through fliers
    {'op': 'rows', 'n': 3, 'r': 48, 'w': 1.2, 'gap': 1.5, 'ops': [dmg(0.34), {'op': 'fliers', 'ops': [dmg(0.2)]}]}, cue('arrows', 'self', 48, 10, c=0xFFF6D0)])
tech(21, 1, tl(55, 1.5), [  # 未来航路: up to four delayed arrows booked on the path; cover not guaranteed past
    line(55, 1.5), dmg(0.2), cue('beam', 'line', 55, 40, a=0.15, c=0xFFF6D0),
    after(12, line(55, 1.5), {'op': 'clear', 'ops': [dmg(0.2)]}), after(20, line(55, 1.5), {'op': 'clear', 'ops': [dmg(0.2)]}),
    after(28, line(55, 1.5), {'op': 'clear', 'ops': [dmg(0.2)]}), after(36, line(55, 1.5), {'op': 'clear', 'ops': [dmg(0.2)]}, cue('arrows', 'self', 55, 8))])
tech(21, 2, tr(60), [  # 無限次元天航: the bow opens into two wings; 40 delayed arrows and a pillar; hits capped
    cue('wings', 'self', 3, 70, c=0xFFF6D0), focus(60), {'op': 'hitcap', 'n': 3},
    pts(40, 10, 2.0, 1, dmg(0.012), cue('rain', 'at', 0.6, 8)), after(44, focus(60), spot(6, 12), dmg(0.5), cue('pillar', 'at', 4, 20, h=40)), {'op': 'hitcap', 'n': 0}])

# ------------------------------------------------------------------------------------------------ 22 大海皇鯨 バハムート (magic)
tech(22, 0, tc(24, 70), [  # 潮声波: one long note, three sea waves; 24 m pushed back; one ailment off friends
    rep(3, 4, cone(24, 70), dmg(0.33), knock(1.6), cue('wave', 'self', 24, 12, c=0x5AB0FF)), allies(24), {'op': 'cleanone', 'to': 1}])
tech(22, 1, tr(20), [  # 生命の返歌: a low deep song; a current ring; friends +25% and a water blessing; foes slowly slowed
    allies(20), healpct(0.25, True), buffto('water', 30, 0), buffto('dolphin', 15, 0), cue('ring', 'self', 20, 40, c=0x5AE0D0),
    area(20, 12), eff('slow', 6, 1), dmg(1.0)])
tech(22, 2, tr(35), [  # 九洋共鳴: the whale's shadow; nine seas' ripples; friends 65% and a great guard; foes many water blows
    allies(35), healpct(0.65, True), reduce(0.5, 8, True), cue('orb', 'self', 6, 60, c=0x5AB0FF), cue('ring', 'self', 35, 50),
    rep(4, 6, area(35, 12), dmg(0.25), knock(1.2), cue('wave', 'self', 35, 10))])

# ------------------------------------------------------------------------------------------------ 23 天変万化 ヌン (magic)
tech(23, 0, tc(15, 100), [  # 全態擬態: shield, spear, claw; three forms in turn, each its own effect
    cone(15, 100), dmg(0.33), knock(1.2), cue('dome', 'self', 1.2, 8),
    after(5, line(15, 2), dmg(0.33), armor(0.2, 6), cue('beam', 'line', 15, 8, a=0.3)),
    after(10, cone(8, 90), dmg(0.34), eff('wither', 3, 0), cue('slash', 'self', 4, 8))])
tech(23, 1, tt(18, 3), [  # 万形同化: into mist, mimicking the ground; reborn elsewhere; the next attack once stronger
    focus(18), SWAP, nextx(1.8, 8), SELF, buff('invis', 3, 0), cue('orb', 'self', 1.4, 16)])
tech(23, 2, tr(26), [  # 万象同体: the staff a liquid sphere; iron claws, liquid tentacles, light waves; by the foe's element
    cue('orb', 'self', 4, 40), cone(26, 120), dmg(0.3), cue('slash', 'self', 8, 10),
    after(10, area(26, 12), dmg(0.3), pull(1.0), cue('chain', 't', 1, 12)), after(22, line(26, 3), dmg(0.4), {'op': 'elements'}, cue('wave', 'line', 26, 12))])

# ------------------------------------------------------------------------------------------------ 24 運命流転 アルカナ (magic)
tech(24, 0, tt(24, 2), [  # 因果針: a gold thread on the move; a needle booked where it goes; a fine homing strike after
    predict(24, 10), spot(2.5, 3), dmg(0.5), cue('chain', 't', 1, 10, c=0xFFD45A), after(10, predict(24, 6), spot(3, 3), dmg(0.5), cue('beam', 'at', 3, 8, a=0.2))])
tech(24, 1, tt(28, 4), [  # 凶兆の収束: the thread rewound; a failed shot moved onto another path, once; not every one sure
    focus(28), spot(4, 6), dmg(0.6), mark(6, 1.3), after(8, focus(28), spot(4, 6), {'op': 'chance', 'p': 0.7, 'ops': [dmg(0.4)]}, cue('chain', 't', 1, 12))])
tech(24, 2, tl(36, 1.5), [  # 唯一絶対の結末: a tree of gold threads; every delay mark fires; one great needle through
    cue('tree', 'self', 6, 60, c=0xFFD45A), area(36, 12), layer('fate', 1, 3, 10),
    rep(4, 5, area(36, 12), dmg(0.08), cue('pillar', 't', 0.6, 8, h=6)), after(26, line(36, 1.5), burst('fate', 0.1), dmg(0.5), cue('beam', 'line', 36, 14, a=0.4, c=0xFFD45A))])

# ------------------------------------------------------------------------------------------------ 25 始祖神獣 エオマイア (polearm)
tech(25, 0, tl(18, 3), [  # 祖獣裂爪: beast claws in a fan, a great horn thrust; tearing marks
    cone(18, 100), dmg(0.5), layer('beast', 1, 3, 10), cue('slash', 'self', 6, 10, c=0xB08A5A), after(6, dash(2.0), line(18, 2), dmg(0.5), cue('beam', 'line', 18, 8, a=0.6))])
tech(25, 1, ts(3), [  # 万獣招来: ancient crests; a bird, a ground beast, a horned beast; attackers and guards
    unit('bird', 1, 20, 200, 0.05, 15, 18), unit('ground', 1, 20, 400, 0.08, 20, 10), unit('horn', 1, 20, 800, 0.0, 40, 6), cue('circle', 'self', 4, 30)])
tech(25, 2, tl(28, 3), [  # 生命系譜の頂点: the beast's outline rises; the herd charges; beast marks spent
    cue('wings', 'self', 3, 40, c=0xB08A5A), rep(5, 4, cone(28, 90), dmg(0.08), cue('slash', 'self', 6, 8)), after(22, line(28, 3), burst('beast', 0.15), dmg(0.6), knock(2.5), cue('beam', 'line', 28, 12, a=0.9))])

# ------------------------------------------------------------------------------------------------ 26 空創龍王 デミウルゴス (greatsword)
tech(26, 0, tl(28, 3), [  # 創造星弾: three little universes, three blades of different matter; extra cuts on the other-world marked
    rep(3, 4, line(28, 3), dmg(0.33), layer('otherworld', 1, 3, 10), cue('wave', 'line', 28, 10, c=0x6A5AFF)), line(28, 3), burst('otherworld', 0.1)])
tech(26, 1, tr(25), [  # 独立世界: a star gate; two other-world turrets and a barrier; devices can be broken
    unit('cannon', 2, 15, 400, 0.06, 15, 25), SELF, reduce(0.3, 10), cue('dome', 'self', 3, 30, c=0x6A5AFF)])
tech(26, 2, tl(42, 4), [  # 無限世界原典: a creation sword; great cut, world fragments, a creation breath through
    cue('wings', 'self', 4, 60, c=0x6A5AFF), cone(20, 120), dmg(0.3), cue('slash', 'self', 10, 12),
    after(14, focus(42), pts(10, 8, 3, 1, dmg(0.03), cue('rain', 'at', 1.0, 10))), after(30, line(42, 4), dmg(0.4), cue('beam', 'line', 42, 16, a=1.2))])

# ------------------------------------------------------------------------------------------------ 27 無窮覇帝 覇極 (cannon)
tech(27, 0, tl(45, 2), [  # 捕食砲: the barrel opens like petals; 45 m line; some of the struck foe's buffs undone
    line(45, 2), dmg(1.0), STRIP1, cue('beam', 'line', 45, 12, a=0.7, c=0xFF5A2A), cue('flash', 't', 1.5, 8)])
tech(27, 1, ts(3), [  # 敗因解析: new armour, resistant muzzles; 20 s of resisting what struck; no full invincibility
    SELF, {'op': 'adapt', 't': 400}, buff('resist', 20, 1), {'op': 'stance', 'k': 'analysis', 't': 400}, cue('dome', 'self', 1.8, 30)])
tech(27, 2, tl(40, 3), [  # 終わらない超克: the gun becomes a dragon; four devouring barrages on the analysed; self-healing
    cue('wings', 'self', 3, 50, c=0xFF5A2A), rep(4, 8, line(40, 3), dmg(0.25), cue('beam', 'line', 40, 8, a=0.8)), SELF, healpct(0.3)])

# ------------------------------------------------------------------------------------------------ 28 万物天敵 シンラ (rapier)
tech(28, 0, tr(10), [  # 天敵識別: a fine light round the parasol; a quiet 10 m field: one buff undone each
    area(10, 12), STRIP1, dmg(1.0), cue('ring', 'self', 10, 30, c=0xE0E0FF)])
tech(28, 1, tl(18, 1.2), [  # 法則喰い: a needle; one thrust at the regenerating organ; 8 s of poor regeneration; never sure death
    line(18, 1.2), dmg(1.0), regen(0.8, 8), cue('beam', 'line', 18, 10, a=0.2, c=0xE0E0FF)])
tech(28, 2, tl(24, 1.2), [  # 存在の反証: closed parasol, one step; the foe's attacks vanish; one point shines; capped vs. the weak
    {'op': 'erase', 'r': 24}, line(24, 1.2), seal(8), {'op': 'reflectdmg', 'm': 1.0}, cue('flash', 't', 2, 14), cue('beam', 'line', 24, 12, a=0.15)])

# ------------------------------------------------------------------------------------------------ 29 全界支配 アインソフオウル (sword)
tech(29, 0, tc(18, 120), [  # 異界分岐: three world gates; other swordsmen's cuts overlap; a short place swap
    rep(3, 3, cone(18, 120), dmg(0.33), layer('branch', 1, 3, 10), cue('slash', 'self', 7, 8)), focus(18), SWAP])
tech(29, 1, tr(20), [  # 同位体合流: other-history weapons from many gates; two of them; for big bosses
    unit('cannon', 2, 15, 400, 0.08, 15, 20), cue('circle', 'self', 5, 30)])
tech(29, 2, tl(40, 3), [  # 無限可能性統合: the world-line tree; many swords one; other-world host then a piercing cut
    cue('tree', 'self', 8, 60), area(40, 12), rep(5, 4, area(40, 12), dmg(0.06), cue('slash', 't', 2, 6)),
    after(26, line(40, 3), burst('branch', 0.1), dmg(0.6), cue('beam', 'line', 40, 14, a=0.8))])

# ------------------------------------------------------------------------------------------------ 30 全害惡徳 アンラマンユ (whip)
tech(30, 0, tr(16), [  # 罪業吸収: chains wind, seven dark marks burn in turn; 16 m chained hold, wither, slow, less attack
    focus(16), chain(5, 6), hold(1.5), eff('wither', 4, 1), eff('slow', 4, 1), atk(0.4, 6), dmg(1.0), cue('chain', 't', 1, 16, c=0x3A0A3A)])
tech(30, 1, tr(20), [  # 七罪天蓋: the scythe set in the ground; a black river drinks the curses on friends; stronger by what it drank
    allies(20), {'op': 'absorbills'}, cue('ring', 'self', 20, 30, c=0x3A0A3A), area(20, 12), dmg(1.0)])
tech(30, 2, tr(30), [  # 万悪抱擁: seven wings and a chain canopy; strong guard on friends; seven dark cuts; by harm drunk
    allies(30), reduce(0.6, 8, True), cue('wings', 'self', 3, 50, c=0x3A0A3A), {'op': 'absorbills'},
    rep(7, 4, area(30, 12), {'op': 'drunk', 'm': 0.14}, cue('slash', 't', 2, 6))])

# ------------------------------------------------------------------------------------------------ 31 始源母胎 マグナ・マーテル (whip)
tech(31, 0, tl(20, 3), [  # 母樹縛根: roots from below; 20 m bind and poison spores; friends a short regeneration
    line(20, 3), hold(2.0), eff('poison', 5, 1), dmg(1.0), cue('spikes', 'line', 20, 20, c=0x5ACF5A), allies(12), buffto('regen', 6, 1)])
tech(31, 1, tr(22), [  # 生命軍団: cocoons hatch; two guard beasts and a healing vine; seed marks lengthen their lives
    unit('beast', 2, 20, 500, 0.05, 20, 12), unit('vine', 1, 20, 300, 0.0, 20, 10, heal=0.03), cue('tree', 'self', 3, 30, c=0x5ACF5A)])
tech(31, 2, tr(28), [  # 万象生命創世: a tree of life; the host attacks in stages; broad healing; copies capped
    allies(28), healpct(0.5, True), cue('tree', 'self', 8, 60, c=0x5ACF5A), unit('beast', 2, 12, 300, 0.05, 20, 12),
    rep(3, 10, area(28, 12), dmg(0.33), cue('spikes', 't', 1.5, 10))])

# ------------------------------------------------------------------------------------------------ 32 無限円環 ウロボロス (chakram)
tech(32, 0, tc(18, 140), [  # 円環刃: two rings thrown left and right; they cut the back on the return
    cone(18, 140), dmg(0.5), cue('ring', 'self', 18, 10, c=0xD0A050), after(10, cone(18, 140), dmg(0.5), cue('ring', 'self', 18, 10, c=0xD0A050))])
tech(32, 1, ts(3), [  # 初めに戻る: a clock ring; the last 3 s of own health and place restored (no death undone, no world)
    REWIND, cue('clock', 'self', 2, 30, c=0xD0A050)])
tech(32, 2, tr(26), [  # 始終同一: a black-gold ring closes; three laps of cuts; the end's great blow; the time marks fire
    cue('ring', 'self', 26, 60, c=0xD0A050), rep(3, 8, area(26, 12), dmg(0.15), layer('ring', 1, 3, 10), cue('slash', 'self', 10, 8)),
    after(26, area(26, 12), burst('ring', 0.1), dmg(0.45), cue('clock', 'self', 6, 20), cue('flash', 'self', 6, 12))])

# ------------------------------------------------------------------------------------------------ 33 玖天神樹 イグドラシル (magic)
tech(33, 0, tl(20, 3), [  # 世界根: a touch of the branch; roots bind; little flowers on friends; +15%
    line(20, 3), hold(2.0), dmg(1.0), cue('spikes', 'line', 20, 20, c=0x5ACF5A), allies(20), healpct(0.15, True)])
tech(33, 1, tr(28), [  # 九界霊葉: nine worlds' leaves into a great crown; 15 s of guard and cleansing; spells partly stopped
    allies(28), reduce(0.4, 15, True), cleanse(True), cue('tree', 'self', 6, 60, c=0x5ACF5A), field(28, 15, m=0.0, name='canopy', rate=10)])
tech(33, 2, tr(34), [  # 世界生命の大樹冠: nine crowns in the sky; friends 70%, cleansed, guarded; nine elements' root blows
    allies(34), healpct(0.7, True), cleanse(True), reduce(0.5, 8, True), cue('tree', 'self', 10, 70, c=0x5ACF5A),
    rep(9, 3, area(34, 12), dmg(0.11), {'op': 'elements'}, cue('spikes', 't', 1.2, 8))])

# ------------------------------------------------------------------------------------------------ 34 万律自在神 御世姫命 (magic)
tech(34, 0, tr(18), [  # 逆さの決まり: one ring of the bell; arrows swap; foes' way reversed for a moment (never helpless)
    area(18, 12), {'op': 'reverse', 't': 30}, dmg(1.0), cue('text', 'self', 1.8, 24, txt='逆'), cue('ring', 'self', 18, 14)])
tech(34, 1, tr(20), [  # 法則交換: two rings; spell colours swapped; buffs undone; the rule shown 3 s
    area(20, 12), STRIP, dmg(1.0), cue('text', 'self', 1.8, 60, txt='法則交換'), cue('circle', 'self', 6, 60)])
tech(34, 2, tr(34), [  # 全存在法則再定義: three rainbow rings; gravity, magic, time in turn; a great pillar last
    cue('circle', 'self', 10, 70, c=0xFF8AD8), area(34, 12), grav(1.5), dmg(0.15),
    after(14, area(34, 12), STRIP, dmg(0.15)), after(28, area(34, 12), eff('slow', 4, 3), dmg(0.15), cue('clock', 'self', 5, 20)),
    after(42, focus(34), spot(8, 12), dmg(0.55), cue('pillar', 'at', 5, 24, h=30))])

# ------------------------------------------------------------------------------------------------ 35 無垢なる全能 (magic)
tech(35, 0, tr(12), [  # 玩具の約束: threads tie; foes small as toys, slowed; only the shape changes, nothing lost
    area(12, 8), toy(5), eff('slow', 5, 1), dmg(1.0), cue('ring', 'self', 12, 14, c=0xFF8AD8)])
tech(35, 1, tr(18), [  # お人形箱: a great toy box; star soldiers jump out; two of them and balloon bombs; the box breakable
    unit('toy', 2, 15, 200, 0.06, 15, 14), unit('box', 1, 15, 300, 0.0, 99, 4), focus(18), pts(4, 5, 3, 3, dmg(0.1), launch(0.8), cue('orb', 'at', 1, 10))])
tech(35, 2, tr(28), [  # 世界はわたしのおもちゃ: a child's room behind; the eyes glow; bind, swap places, star blasts
    cue('dome', 'self', 12, 60, c=0xFF8AD8), area(28, 12), hold(2.0), toy(6), dmg(0.2),
    after(14, area(28, 12), {'op': 'shuffle'}, dmg(0.2)), after(28, area(28, 12), dmg(0.6), cue('flash', 't', 2, 10), cue('rain', 'self', 12, 14))])

# ------------------------------------------------------------------------------------------------ 36 凄惨たる暴虐 (heavy)
tech(36, 0, tc(9, 80), [  # 城壁砕拳: club on the shoulder, one step; guards and foes crushed; the strong staggered, not flung
    cone(9, 80), dmg(1.0), {'op': 'shieldbreak'}, armor(0.5, 8), {'op': 'stagger'}, cue('fist', 'self', 9, 10, c=0x9A3A2A), cue('ring', 't', 2.5, 10)])
tech(36, 1, tl(24, 3), [  # 万象殴滅: two hands overhead; cracks run on; 24 m crack chain; great knockback (stone drawn only)
    rep(4, 4, line(24, 3), dmg(0.25), knock(1.0), cue('spikes', 'line', 24, 10, c=0x9A7A5A)), line(24, 3), knock(3.0)])
tech(36, 2, tc(16, 90), [  # 万象を殴り砕く拳: the club thrown away; fists break ground and barriers; club back, full force
    rep(10, 2, cone(16, 90), dmg(0.04), cue('fist', 'self', 5, 5)), cone(16, 90), {'op': 'shieldbreak'}, regen(0.9, 10), seal(4),
    after(24, cone(16, 90), dmg(0.6), slam(3.0), cue('pillar', 'self', 4, 16, h=10, c=0x9A3A2A), cue('ring', 'self', 16, 14), snd('anvil', 1.0, 0.5))])

# ------------------------------------------------------------------------------------------------ 37 邪沌の呪詛 (magic)
tech(37, 0, tr(18), [  # 慈愛の花: white threads as if to heal, then thorns; 18 m curse marks and lasting harm; moves on twice at most
    area(18, 12), layer('tragedy', 1, 3, 12), eff('wither', 6, 1), dmg(1.0), {'op': 'curse', 'k': 'tragedy', 'jumps': 2}, cue('tree', 't', 1, 20, c=0x6A2A8A)])
tech(37, 1, tr(20), [  # 悲劇の継章: tears to rose dew; part of a foe's last healing turned to curse (healing still works)
    area(20, 12), {'op': 'healcurse', 't': 300, 'f': 0.5}, dmg(1.0), cue('ring', 'self', 20, 30, c=0x6A2A8A)])
tech(37, 2, tr(30), [  # 愛と悲劇の永遠: a white rose garden turns black; every mark fires, black thorns, more on healing
    cue('dome', 'self', 10, 60, c=0x6A2A8A), area(30, 12), {'op': 'healcurse', 't': 400, 'f': 0.8}, burst('tragedy', 0.15),
    rep(5, 4, area(30, 12), dmg(0.12), cue('spikes', 't', 1, 8)), after(24, area(30, 12), dmg(0.4), cue('flash', 't', 2, 10))])

# ------------------------------------------------------------------------------------------------ 38 戒進の研究 (rapier)
tech(38, 0, tl(16, 1.5), [  # 診断針: the needle, a spray; markers on the body; 16 m thrust and a measure; poison or fatigue
    line(16, 1.5), dmg(1.0), tag('diagnosed', 30), {'op': 'branch', 'ops': [[eff('poison', 6, 2)], [eff('fatigue', 6, 2)]]},
    cue('beam', 'line', 16, 10, a=0.2, c=0xE0FFFF), cue('circle', 't', 1, 30, c=0xFF3A3A)])
tech(38, 1, tr(20), [  # 強制適応: a machine arm; three culture capsules; counters made by the foe's attacks
    unit('lab', 3, 15, 250, 0.03, 20, 20), SELF, {'op': 'adapt', 't': 300}, cue('circle', 'self', 4, 30)])
tech(38, 2, tr(30), [  # 全存在治療計画: the lab's outline; the needle and arms close in; four precise strikes; friends treated
    allies(30), healpct(0.3, True), rep(4, 6, focus(30), spot(4, 4), dmg(0.2), iftag('diagnosed', dmg(0.05)), cue('beam', 'at', 3, 8, a=0.2)),
    after(30, focus(30), cue('flash', 'at', 3, 12))])

# ------------------------------------------------------------------------------------------------ 39 外悪の魔導 (whip)
tech(39, 0, tl(24, 2.5), [  # 術式分裂: circles sprout from the chain; 24 m chain cut and circle follow-up; one buff undone
    line(24, 2.5), dmg(0.6), STRIP1, cue('chain', 't', 1, 12, c=0xB08AFF), after(8, line(24, 2.5), dmg(0.4), cue('circle', 't', 1.2, 14))])
tech(39, 1, tr(26), [  # 研究者の消失: the chain's links as little grimoires; up to four circles; 12 s of harrying; spells reflected
    unit('circle', 4, 12, 250, 0.04, 15, 18), SELF, {'op': 'reflect', 't': 240, 'r': 8}])
tech(39, 2, tr(38), [  # 魔導そのもの: the chain into a great ring; circles bear circles; a volley and the target's spells sealed
    cue('circle', 'self', 12, 70, c=0xB08AFF), focus(38), pts(8, 10, 3, 2, dmg(0.06), cue('circle', 'at', 2, 12)),
    after(24, focus(38), spot(8, 12), dmg(0.5), seal(6), cue('pillar', 'at', 4, 20, h=20))])

# ------------------------------------------------------------------------------------------------ 40 救堕せし勇者 (sword)
tech(40, 0, tl(18, 2.5), [  # 慈悲の拘束: the sword at the breast; future-sin dots; judgement mark and restraint; more on attackers of friends
    line(18, 2.5), mark(8, 1.4), eff('slow', 4, 2), atk(0.3, 6), dmg(0.7), {'op': 'friendhurters', 'ops': [dmg(0.6)]}, cue('circle', 't', 1.4, 30, c=0xE0E0E0)])
tech(40, 1, tr(16), [  # 神殺しの聖剣: a grey sanctuary; buffs undone; foes' attacks lowered; friends protected
    area(16, 12), STRIP, atk(0.4, 10), dmg(1.0), allies(16), reduce(0.4, 10, True), cue('dome', 'self', 6, 40, c=0xB0B0B0)])
tech(40, 2, tl(32, 4), [  # 最後の断罪: one tear; a great holy sword; the point turned on itself too (it never kills its bearer)
    cue('pillar', 'self', 2, 50, h=20, c=0xF0F0FF), after(20, line(32, 4), dmg(1.0), cue('slash', 'line', 32, 14, a=90), cue('beam', 'line', 32, 14, a=1.2)),
    after(22, SELF, {'op': 'exposed', 't': 60})])

# ------------------------------------------------------------------------------------------------ 41 甘契の未怪 (magic)
tech(41, 0, tr(16), [  # 救いの前借り: a coin on one pan; a contract shown: healing and a short buff; cost on screen; no answer, nothing
    offer(0.4, 'strength', 20, 'hunger', 30, 16)])
tech(41, 1, tr(20), [  # 契約の期限: the threads of sealed contracts; those due turn black; only their terms are used
    contracts(hold(1.5), STRIP), area(20, 12), dmg(1.0), cue('chain', 't', 1, 14, c=0xFFD45A)])
tech(41, 2, tr(32), [  # 万未来所有: a great scale in the sky; agreed costs gathered; a wide light; the unsigned bear no penalty
    cue('circle', 'self', 12, 60, c=0xFFD45A), contracts(dmg(0.3)), area(32, 12), dmg(1.0), cue('pillar', 'self', 6, 20, h=24), cue('ring', 'self', 32, 16)])

assert len(T) == 123, len(T)

"""Relic arts 29-41."""
from relic_arts import *

LP = LEGEND_PASSIVE

# 29 ain_sof_aur --------------------------------------------------------------------------------------------
L('ain_sof_aur_weapon', 1, 'branch', ('分岐確定', 'Branch Fixed'),
  ('二つの未来から一つを確定：24m内に極大打撃と8秒拘束／または強化剥奪と自身全快。並行体（ゴーレム）2体、8m転移', 'Fix one of two futures; 2 parallel selves; step 8m'),
  [chance(0.5, [area(24), dmg(2.0), stun(160)], [area(24), dmg(1.0), strip(), me(), healpct(1.0)]), summon('golem', 2), blink(8)],
  [me(), buff('luck', 40, 3)], ('所持中：幸運', 'Held: luck'),
  [chance(0.5, [victim(), dmg(0.4)])], ('命中時：50%で別の結果（追撃）', 'On hit: 50% another outcome'), hitfx='end_rod')
L('ain_sof_aur_focus', 2, 'branch', ('並行体召喚', 'Parallel Selves'),
  ('並行世界の自分（ゴーレム）4体、10秒反射、3秒無敵', '4 parallel selves, 10s reflection, 3s guard'),
  [summon('golem', 4), reflect(200, 24), me(), guard(60)],
  [me(), reflect(25, 6)], ('所持中：反射', 'Held: reflection'))
L('ain_sof_aur_charm', 1, 'branch', ('結果選択', 'Outcome Select'),
  ('「傷を負わなかった世界」を選ぶ：5秒前の体力と位置へ戻り30秒不死', 'Choose the world without wounds: rewind 5s, 30s undying'),
  [rewind(), me(), undying(600)],
  [snapshot(), me(), buff('luck', 40, 2)], ('所持中：分岐の記録', 'Held: branch record'))
L('ain_sof_aur_legend', 3, 'branch', ('全界選択・無限分岐の玉座', 'Throne of Infinite Branches'),
  ('48m内の敵に最悪の結果を確定：極大打撃・15秒拘束・強化剥奪・50%以下消去。並行体6体、60秒不死・全快、20秒反射', 'Fix the worst outcome for all within 48m; 6 selves; undying; reflection'),
  [area(48), dmg(3.0), stun(300), strip(), execute(0.5), summon('golem', 6), me(), undying(1200), guard(100), healpct(1.0), reflect(400, 48)],
  LP + [snapshot()], ('所持中：分岐の神', 'Held: god of branches'),
  [chance(0.5, [victim(), dmg(1.0)])], ('命中時：50%で別の結果', 'On hit: 50% another outcome'), hitfx='end_rod')
L('ain_sof_aur_relic_weapon', 1, 'branch', ('分岐の残響', 'Echo of Branches'),
  ('50%で打撃、50%で回復', '50% strike, 50% heal'), [chance(0.5, [near(16, 1), dmg(1.2)], [me(), healpct(0.4)])],
  hit=[chance(0.25, [victim(), dmg(0.3)])], hit_desc=('命中時：25%で追撃', 'On hit: 25% extra'))

# 30 angra_mainyu -------------------------------------------------------------------------------------------
L('angra_mainyu_weapon', 1, 'evil', ('全害の鎖', 'Chains of All Harm'),
  ('影の鎖を8体へ繋ぎ引き寄せ、腐敗V・衰弱V・大打撃。自身は生命を吸って回復', 'Chain 8 foes: pull, wither V, weakness V, smite; drain life'),
  [chain(8, 12), pull(2.0), dmg(1.2), eff('wither', 300, 4), eff('weakness', 300, 4), me(), healpct(0.5)],
  [me(), buff('night', 300), buff('regen', 40, 0)], ('所持中：闇の視界・再生', 'Held: darksight, regeneration'),
  [victim(), eff('wither', 80, 2), me(), heal(4)], ('命中時：腐敗・吸命', 'On hit: wither and drain'), hitfx='sculk')
L('angra_mainyu_focus', 2, 'evil', ('悪意吸収', 'Malice Absorption'),
  ('24m内の敵の強化（悪意）を吸い取り衰弱VII、自身全快・吸収VII', 'Absorb the malice (buffs) within 24m, weakness VII; full heal and absorption'),
  [area(24), strip(True), eff('weakness', 600, 6), me(), healpct(1.0), buff('absorb', 600, 6)],
  [area(6), eff('weakness', 40, 0)], ('所持中：周囲の敵を弱らせる', 'Held: weakens nearby foes'))
L('angra_mainyu_charm', 1, 'evil', ('闇の抱擁', 'Embrace of Darkness'),
  ('15秒透明・2秒無敵・浄化、16m内を暗闇と盲目で覆う', '15s invisible, 2s guard, cleanse; darkness and blindness within 16m'),
  [me(), buff('invis', 300), guard(40), cleanse(), area(16), eff('dark', 300), eff('blind', 200)],
  [me(), buff('night', 300)], ('所持中：暗視', 'Held: night vision'))
L('angra_mainyu_legend', 3, 'evil', ('世界悪核・全害の王権', 'Core of World Evil'),
  ('48m内の悪意を全て奪う：強化強奪・腐敗X・衰弱X・暗闇・極大打撃・40%以下即死。自身全快・吸収X', 'Take every malice within 48m; execute below 40%; full heal'),
  [area(48), strip(True), eff('wither', 1200, 9), eff('weakness', 1200, 9), eff('dark', 600), dmg(2.5), execute(0.4), me(), healpct(1.0),
   buff('absorb', 1200, 9)],
  LP + [area(8), eff('wither', 40, 2)], ('所持中：悪の瘴気', 'Held: miasma of evil'),
  [victim(), eff('wither', 200, 4), me(), heal(10)], ('命中時：腐敗・吸命', 'On hit: wither and drain'), hitfx='sculk')
L('angra_mainyu_relic_weapon', 1, 'evil', ('影鎖の残響', 'Echo of Shadow Chains'),
  ('影の鎖を3体へ', 'Chain 3 foes'), [chain(3, 10), pull(1.5), eff('wither', 160, 1)],
  hit=[me(), heal(2)], hit_desc=('命中時：吸命', 'On hit: drain'))

# 31 magna_mater --------------------------------------------------------------------------------------------
L('magna_mater_weapon', 1, 'life', ('蔓縛', 'Vine Bind'),
  ('20mの蔓で敵を引き寄せ10秒縛り大打撃。味方回復、命の眷属（狼）2体', 'Vines over 20m pull and bind 10s; heal allies; 2 life spirits'),
  [line(20, 3), pull(2.5), stun(200), dmg(1.2), allies(20), healpct(0.6, True), summon('wolf', 2)],
  [allies(10), buff('regen', 40, 0, True)], ('所持中：味方を再生', 'Held: allies regenerate'),
  [victim(), stun(20), eff('slow', 60, 2)], ('命中時：蔓が絡む', 'On hit: entangle'), hitfx='happy')
L('magna_mater_focus', 2, 'life', ('始源生命', 'Primordial Life'),
  ('命を産む：狼4体・ゴーレム2体、32m内の味方を全快・再生IV・体力増強IV', 'Birth life: 4 wolves, 2 golems; allies healed and empowered'),
  [summon('wolf', 4), summon('golem', 2), allies(32), healpct(1.0, True), buff('regen', 600, 3, True), buff('health', 1200, 3, True)],
  [allies(16), buff('regen', 40, 0, True)], ('所持中：味方を再生', 'Held: allies regenerate'))
L('magna_mater_charm', 1, 'life', ('慈愛の揺籃', 'Cradle of Mercy'),
  ('24m内の味方を全快・浄化・3秒無敵、満腹', 'Allies: full heal, cleanse, 3s guard; full'),
  [allies(24), healpct(1.0, True), cleanse(True), guard(60, True), me(), food()],
  [me(), buff('regen', 40, 1), buff('saturation', 40)], ('所持中：再生II・満腹', 'Held: regeneration II, satiety'))
L('magna_mater_legend', 3, 'life', ('始源創命・無窮の母胎', 'Womb of Endless Life'),
  ('狼6体。48m内の味方を全快・浄化・再生V・30秒不死・体力増強VI。敵は蔓で15秒拘束し引き寄せる', '6 wolves; allies restored and undying; foes bound 15s'),
  [summon('wolf', 6), allies(48), healpct(1.0, True), cleanse(True), buff('regen', 1200, 4, True), undying(600, True),
   buff('health', 2400, 5, True), area(48), stun(300), pull(2.0)],
  LP + [allies(16), buff('regen', 40, 1, True)], ('所持中：命の母', 'Held: mother of life'),
  [victim(), stun(30)], ('命中時：蔓縛', 'On hit: vine bind'), hitfx='happy')
L('magna_mater_relic_weapon', 1, 'life', ('蔓の残響', 'Echo of Vines'),
  ('12mの蔓で引き寄せ3秒縛る', 'Pull and bind 3s with 12m vines'), [line(12, 2), pull(2.0), stun(60)],
  hit=[victim(), eff('slow', 60, 1)], hit_desc=('命中時：減速', 'On hit: slow'))

# 32 ouroboros ----------------------------------------------------------------------------------------------
L('ouroboros_weapon', 1, 'cycle', ('円環巻戻し', 'Ring Rewind'),
  ('5秒前の体力と位置へ巻き戻り、16m内の敵を6秒停止・大打撃', 'Rewind 5s, then stop foes within 16m for 6s and smite'),
  [rewind(), area(16), dmg(1.4), stun(120)],
  [snapshot()], ('所持中：円環の記録（巻戻しに必要）', 'Held: records the cycle'),
  [victim(), stun(15), chance(0.3, [victim(), dmg(0.3)])], ('命中時：時を止める', 'On hit: stops time'), hitfx='enchant')
L('ouroboros_focus', 2, 'cycle', ('輪廻停止', 'Samsara Halt'),
  ('32m内の時の輪を止める：15秒停止・凍結、飛び道具消去、自身全快', 'Halt the wheel within 32m: stop 15s, freeze, erase projectiles; full heal'),
  [area(32), stun(300), freeze(200), erase(32), me(), healpct(1.0)],
  [snapshot(), me(), buff('regen', 40, 0)], ('所持中：記録・再生', 'Held: record, regeneration'))
L('ouroboros_charm', 1, 'cycle', ('無傷回帰', 'Unharmed Return'),
  ('傷を負う前へ回帰：5秒前に巻き戻り、浄化・2秒無敵', 'Return to before the wound: rewind, cleanse, 2s guard'),
  [rewind(), me(), cleanse(), guard(40)],
  [snapshot()], ('所持中：回帰の記録', 'Held: return record'))
L('ouroboros_legend', 3, 'cycle', ('宇宙継続・無限円環', 'Endless Ring'),
  ('巻戻して60秒不死・全快。48m内の時を20秒止め、極大打撃・鈍足VII、飛び道具を消滅', 'Rewind, 60s undying, full heal; stop time within 48m for 20s'),
  [rewind(), me(), undying(1200), healpct(1.0), area(48), stun(400), dmg(2.5), eff('slow', 600, 6), erase(64)],
  LP + [snapshot()], ('所持中：円環の神霊', 'Held: spirit of the ring'),
  [victim(), stun(30)], ('命中時：時を止める', 'On hit: stops time'), hitfx='enchant')
L('ouroboros_relic_weapon', 1, 'cycle', ('円環の残響', 'Echo of the Ring'),
  ('5秒前へ巻き戻る', 'Rewind 5s'), [rewind()], [snapshot()], ('所持中：記録', 'Held: record'))

# 33 yggdrasil ----------------------------------------------------------------------------------------------
L('yggdrasil_weapon', 1, 'tree', ('根縛', 'Root Bind'),
  ('20m内の敵を根で地に縛り10秒拘束・大打撃。味方を回復浄化、精霊（狼）2体', 'Roots bind foes within 20m for 10s; heal allies; 2 spirits'),
  [area(20), slam(2.0), stun(200), dmg(1.2), allies(20), healpct(0.6, True), cleanse(True), summon('wolf', 2)],
  [me(), buff('regen', 40, 0), allies(8), buff('regen', 40, 0, True)], ('所持中：神樹の息吹', 'Held: breath of the world tree'),
  [victim(), stun(15)], ('命中時：根が絡む', 'On hit: roots'), hitfx='happy')
L('yggdrasil_focus', 2, 'tree', ('九界魔流', 'Nine Realm Flow'),
  ('32m内の味方を全快・浄化・再生IV・体力増強III・吸収V、経験値100', 'Allies: full heal, cleanse, regeneration IV, health III, absorption V; experience'),
  [allies(32), healpct(1.0, True), cleanse(True), buff('regen', 600, 3, True), buff('health', 1200, 2, True), buff('absorb', 600, 4, True), xp(100)],
  [allies(16), buff('regen', 40, 0, True), buff('haste', 40, 0, True)], ('所持中：魔力の大動脈', 'Held: mana artery'))
L('yggdrasil_charm', 1, 'tree', ('若葉の祝福', 'Blessing of Young Leaves'),
  ('24m内の味方を8割回復・浄化、満腹', 'Heal allies 80%, cleanse; full'),
  [allies(24), healpct(0.8, True), cleanse(True), me(), food()],
  [me(), buff('regen', 40, 1), buff('saturation', 40)], ('所持中：再生II・満腹', 'Held: regeneration II, satiety'))
L('yggdrasil_legend', 3, 'tree', ('玖界循環・神樹の心葉', 'Heartleaf of the World Tree'),
  ('48m内の味方を全快・浄化・再生VI・30秒不死。怒れる神樹：敵を15秒縛り落雷・極大打撃', 'Allies restored and undying; the angry tree binds foes and calls lightning'),
  [allies(48), healpct(1.0, True), cleanse(True), buff('regen', 1200, 5, True), undying(600, True), o('weather', w='thunder'),
   area(48), stun(300), lightning(), dmg(2.5)],
  LP + [allies(16), buff('regen', 40, 1, True)], ('所持中：世界樹の加護', 'Held: world tree aegis'),
  [victim(), stun(20)], ('命中時：根縛', 'On hit: root bind'), hitfx='happy')
L('yggdrasil_relic_weapon', 1, 'tree', ('若枝の残響', 'Echo of the Sprout'),
  ('8m内を根で4秒縛る', 'Root foes within 8m for 4s'), [area(8), stun(80)],
  passive=[me(), buff('regen', 40, 0)], passive_desc=('所持中：再生', 'Held: regeneration'))

# 34 miyohime -----------------------------------------------------------------------------------------------
LAWS = [launch(3.0), slam(4.0), freeze(400), stun(300), eff('slow', 600, 9), eff('levitate', 200, 4)]
L('miyohime_weapon', 1, 'law', ('万律改変', 'Law Rewrite'),
  ('24m内の敵ごとに法則を改竄：反重力・超重力・凍結・停止・鈍足X・浮遊。自身は浄化と30秒適応', 'Rewrite the law for each foe within 24m; cleanse and adapt'),
  [area(24), each(LAWS), dmg(1.0), me(), cleanse(), adapt(600)],
  [me(), cleanse(), adapt(40)], ('所持中：干渉は成立しない（弱体無効・適応）', 'Held: interference fails'),
  [chance(0.35, [victim(), each([launch(2.0), freeze(200), stun(60)])])], ('命中時：35%で法則改竄', 'On hit: 35% law rewrite'), hitfx='firework')
says('miyohime_focus', [('御世姫命：「昼にしましょう」', 'Miyohime: "Let it be day."'), ('御世姫命：「夜にしましょう」', 'Miyohime: "Let it be night."')])
L('miyohime_focus', 2, 'law', ('法則改竄', 'Law Forgery'),
  ('昼夜を書き換え（交互）、32m内の敵を浮遊・10秒停止', 'Rewrites day and night; foes within 32m float and stop 10s'),
  [cycle('miyohime_focus', [('昼', [time_(1000)]), ('夜', [time_(14000)])]), area(32), eff('levitate', 200, 4), stun(200)],
  [me(), buff('night', 300)], ('所持中：暗視', 'Held: night vision'))
L('miyohime_charm', 1, 'law', ('干渉不成立', 'Interference Void'),
  ('10秒無敵・浄化、32m内の飛び道具消去、10秒反射', '10s guard, cleanse; erase projectiles; 10s reflection'),
  [me(), guard(200), cleanse(), erase(32), reflect(200, 16)],
  [me(), cleanse(), reflect(25, 6)], ('所持中：弱体無効・反射', 'Held: debuff immunity, reflection'))
L('miyohime_legend', 3, 'law', ('理外自由・万律自在神璽', 'Seal of All Laws'),
  ('48m内の万物の法則を改竄し極大打撃・15秒停止。自身60秒不死・5秒無敵・120秒適応・剛力XIII、飛び道具消滅', 'Rewrite every law within 48m; undying, guard, adaptation'),
  [area(48), each(LAWS), dmg(3.0), stun(300), me(), undying(1200), guard(100), adapt(2400), buff('strength', 1200, 12), erase(64)],
  LP + [cleanse(), reflect(25, 8)], ('所持中：法則の神（弱体無効・反射）', 'Held: god of laws'),
  [victim(), each(LAWS)], ('命中時：法則改竄', 'On hit: law rewrite'), hitfx='firework')
L('miyohime_relic_weapon', 1, 'law', ('神楽の残響', 'Echo of Kagura'),
  ('最寄りの敵の法則を改竄', 'Rewrite the nearest foe\'s law'), [near(16, 1), each(LAWS)],
  hit=[chance(0.15, [victim(), launch(1.5)])], hit_desc=('命中時：15%で反重力', 'On hit: 15% antigravity'))

# 35 innocence ----------------------------------------------------------------------------------------------
L('innocence_weapon', 1, 'toy', ('玩具化', 'Toyification'),
  ('24m内の通常の敵をぬいぐるみの様な家畜に変え、強敵は浮遊させ10秒停止。自身浄化', 'Turns ordinary foes within 24m into livestock toys; bosses float and stop'),
  [area(24), transmute(), area(24), eff('levitate', 200, 2), stun(200), me(), cleanse()],
  [me(), buff('slowfall', 40), buff('luck', 40, 2)], ('所持中：ふわふわ・幸運', 'Held: floaty, lucky'),
  [chance(0.3, [victim(), transmute()])], ('命中時：30%で玩具化', 'On hit: 30% toyify'), hitfx='heart')
L('innocence_focus', 2, 'toy', ('遊びの時間', 'Playtime'),
  ('32m内の敵を浮かべて15秒停止・大打撃、味方は全快', 'Foes within 32m float, stop 15s and are smitten; allies healed'),
  [area(32), eff('levitate', 300, 3), stun(300), dmg(1.5), allies(24), healpct(1.0, True)],
  [me(), buff('slowfall', 40)], ('所持中：ふわふわ', 'Held: floaty'))
L('innocence_charm', 1, 'toy', ('死んでないことにする', 'It Never Happened'),
  ('120秒不死・全快・浄化、16m内の味方も全快', '120s undying, full heal, cleanse; allies healed'),
  [me(), undying(2400), healpct(1.0), cleanse(), allies(16), healpct(1.0, True)],
  [low(0.3, [me(), undying(40), healpct(0.5)])], ('所持中：瀕死になると取り消す', 'Held: undoes near-death'))
L('innocence_legend', 3, 'toy', ('無垢創世・全能の遊び場', 'Playground of Omnipotence'),
  ('64m内の通常の敵を全て玩具化。残りは浮遊・20秒停止・極大打撃。味方に60秒不死・全快、自身10秒無敵', 'Toyify every ordinary foe within 64m; the rest float, stop 20s; allies undying'),
  [area(64), transmute(), area(64), eff('levitate', 400, 5), stun(400), dmg(3.0), allies(48), undying(1200, True), healpct(1.0, True),
   me(), guard(200)],
  LP + [cleanse(), low(0.4, [me(), undying(40)])], ('所持中：無垢なる全能', 'Held: innocent omnipotence'),
  [chance(0.5, [victim(), transmute()])], ('命中時：50%で玩具化', 'On hit: 50% toyify'), hitfx='heart')
L('innocence_relic_weapon', 1, 'toy', ('無垢の残響', 'Echo of Innocence'),
  ('最寄りの敵を浮かべる', 'Float the nearest foe'), [near(16, 1), eff('levitate', 100, 2)],
  hit=[chance(0.1, [victim(), transmute()])], hit_desc=('命中時：10%で玩具化', 'On hit: 10% toyify'))

# 36 brutality ----------------------------------------------------------------------------------------------
L('brutality_weapon', 1, 'brutal', ('凄惨連打', 'Brutal Barrage'),
  ('最寄りの3体へ守りを砕く4連打、被ダメ2倍の刻印、彼方へ殴り飛ばす。剛力IX・浄化', '4 defense-breaking blows on the nearest 3, mark x2, blast away; strength IX'),
  [near(16, 3), strip()] + rep(4, dmg(1.0)) + [mark(300, 2.0), knock(5.0), me(), buff('strength', 300, 8), cleanse()],
  [me(), buff('strength', 40, 2), buff('speed', 40, 0)], ('所持中：剛力III・俊足', 'Held: strength III, speed'),
  [victim(), strip(), dmg(0.4), knock(3.0)], ('命中時：守りを砕き殴り飛ばす', 'On hit: break guard and blast'), hitfx='explosion')
L('brutality_focus', 2, 'brutal', ('抗理粉砕', 'Shatter Resistance'),
  ('20m内の敵の守りを粉砕し叩き伏せ6秒拘束、妨害の飛び道具も粉砕', 'Shatter defenses within 20m, slam, bind 6s; smash projectiles'),
  [area(20), strip(), dmg(1.6), slam(4.0), stun(120), erase(24)],
  [me(), buff('haste', 40, 2)], ('所持中：作業加速III', 'Held: haste III'))
L('brutality_charm', 1, 'brutal', ('不敗', 'Undefeated'),
  ('3秒無敵・剛力IX・耐性IV・浄化（30秒）', '3s guard, strength IX, resistance IV, cleanse'),
  [me(), guard(60), buff('strength', 600, 8), buff('resist', 600, 3), cleanse()],
  [low(0.4, [me(), buff('strength', 40, 10)])], ('所持中：窮地で剛力XI', 'Held: strength XI when cornered'))
L('brutality_legend', 3, 'brutal', ('絶対暴力・凄惨の覇拳', 'Absolute Violence'),
  ('40m内の敵の守りを砕き4連打、打ち上げ殴り飛ばし10秒拘束、50%以下を粉砕。剛力XXI・30秒不死', '4 blows on all within 40m; launch, blast, bind; shatter below 50%; strength XXI'),
  [area(40), strip()] + rep(4, dmg(1.5)) + [launch(3.0), knock(6.0), stun(200), execute(0.5), me(), buff('strength', 1200, 20), undying(600), cleanse()],
  LP + [buff('strength', 40, 4)], ('所持中：暴力の化身', 'Held: violence incarnate'),
  [victim(), strip(), dmg(0.6), dmg(0.6), knock(4.0)], ('命中時：二連打で殴り飛ばす', 'On hit: double blow'), hitfx='explosion')
L('brutality_relic_weapon', 1, 'brutal', ('暴虐の残響', 'Echo of Brutality'),
  ('最寄りの敵を殴り飛ばす', 'Blast the nearest foe'), [near(8, 1), dmg(1.2), knock(4.0)],
  hit=[victim(), knock(2.0)], hit_desc=('命中時：殴り飛ばす', 'On hit: blast'))

# 37 cursed_love --------------------------------------------------------------------------------------------
L('cursed_love_weapon', 1, 'tragedy', ('悲劇の糸', 'Strings of Tragedy'),
  ('呪いの糸を6体へ：引き寄せ8秒操り、腐敗VI・混乱・被ダメ2.5倍。自身回復', 'Strings on 6 foes: pull, control 8s, wither VI, confusion, x2.5 damage'),
  [chain(6, 12), pull(2.0), stun(160), eff('wither', 400, 5), eff('nausea', 300), mark(400, 2.5), me(), healpct(0.3)],
  [me(), buff('regen', 40, 0)], ('所持中：再生', 'Held: regeneration'),
  [victim(), eff('wither', 100, 3), eff('nausea', 60)], ('命中時：呪いの糸', 'On hit: cursed string'), hitfx='dragon')
L('cursed_love_focus', 2, 'tragedy', ('呪愛の雫', 'Drops of Cursed Love'),
  ('24m内に呪愛を注ぐ：腐敗VIII・衰弱VI・盲目、強化を奪う', 'Pour cursed love within 24m: wither VIII, weakness VI, blindness; steal buffs'),
  [area(24), eff('wither', 800, 7), eff('weakness', 800, 5), eff('blind', 200), strip(True)],
  [me(), buff('night', 300)], ('所持中：暗視', 'Held: night vision'))
L('cursed_love_charm', 1, 'tragedy', ('幸福反転', 'Happiness Reversed'),
  ('20m内の敵の幸福（強化）を奪い飢餓VI、自身全快', 'Steal the happiness (buffs) of foes within 20m, hunger VI; full heal'),
  [area(20), strip(True), eff('hunger', 600, 5), me(), healpct(1.0)],
  [me(), buff('regen', 40, 1)], ('所持中：再生II', 'Held: regeneration II'))
L('cursed_love_legend', 3, 'tragedy', ('終わらぬ悲劇・呪愛の心臓', 'Heart of Endless Tragedy'),
  ('48m内に終わらぬ悲劇：強化強奪・腐敗X・混乱・盲目・極大打撃・45%以下即死・被ダメ3倍。自身全快・30秒不死', 'Endless tragedy across 48m; execute below 45%; undying'),
  [area(48), strip(True), eff('wither', 1200, 9), eff('nausea', 600), eff('blind', 300), dmg(2.5), execute(0.45), mark(600, 3.0),
   me(), healpct(1.0), undying(600)],
  LP + [area(8), eff('wither', 40, 2)], ('所持中：悲劇の瘴気', 'Held: miasma of tragedy'),
  [victim(), eff('wither', 200, 5), mark(200, 2.0)], ('命中時：呪い・刻印', 'On hit: curse and mark'), hitfx='dragon')
L('cursed_love_relic_weapon', 1, 'tragedy', ('操糸の残響', 'Echo of Strings'),
  ('最寄りの敵を引き寄せ腐敗', 'Pull the nearest foe and wither'), [near(12, 1), pull(2.0), eff('wither', 160, 2)],
  hit=[victim(), eff('wither', 60, 1)], hit_desc=('命中時：腐敗', 'On hit: wither'))

# 38 relentless_research ------------------------------------------------------------------------------------
L('relentless_research_weapon', 1, 'lab', ('強制治験', 'Forced Trial'),
  ('24mを注射：大打撃・毒VII・8秒拘束、30%で異常生命（家畜）化。味方は強制治療', 'Inject 24m: smite, poison VII, bind 8s, 30% mutate; allies forcibly healed'),
  [line(24, 2.5), dmg(1.5), eff('poison', 400, 6), stun(160), chance(0.3, [transmute()]), allies(16), healpct(0.8, True)],
  [me(), buff('regen', 40, 0)], ('所持中：再生', 'Held: regeneration'),
  [victim(), eff('poison', 100, 4)], ('命中時：毒の投与', 'On hit: dose of poison'), hitfx='witch')
L('relentless_research_focus', 2, 'lab', ('戒進治療', 'Relentless Treatment'),
  ('32m内の味方を全快・浄化・再生V・体力増強V、異常生命（狼）2体', 'Allies: full heal, cleanse, regeneration V, health V; 2 abnormal lifeforms'),
  [allies(32), healpct(1.0, True), cleanse(True), buff('regen', 600, 4, True), buff('health', 1200, 4, True), summon('wolf', 2)],
  [allies(16), buff('regen', 40, 0, True)], ('所持中：味方を再生', 'Held: allies regenerate'))
L('relentless_research_charm', 1, 'lab', ('分散保存', 'Distributed Backup'),
  ('保存した自分へ復元：5秒前へ巻き戻り30秒不死', 'Restore from backup: rewind 5s, 30s undying'),
  [rewind(), me(), undying(600)],
  [snapshot()], ('所持中：記憶の保存', 'Held: memory backup'))
L('relentless_research_legend', 3, 'lab', ('全救済実験・戒進の原理', 'Principle of Total Salvation'),
  ('48m内の敵は毒X・15秒拘束・家畜化・極大打撃。味方は全快・浄化・30秒不死、異常生命6体', 'Poison, bind, mutate within 48m; allies saved and undying; 6 lifeforms'),
  [area(48), eff('poison', 1200, 9), stun(300), transmute(), area(48), dmg(2.5), allies(48), healpct(1.0, True), cleanse(True),
   undying(600, True), summon('wolf', 6)],
  LP + [allies(16), buff('regen', 40, 1, True)], ('所持中：救済の研究者', 'Held: researcher of salvation'),
  [victim(), eff('poison', 200, 6), execute(0.2)], ('命中時：劇毒・20%以下を処置', 'On hit: lethal dose'), hitfx='witch')
L('relentless_research_relic_weapon', 1, 'lab', ('注射の残響', 'Echo of the Needle'),
  ('最寄りの敵に毒、味方を回復', 'Poison the nearest foe, heal allies'), [near(12, 1), eff('poison', 200, 3), allies(12), heal(12, True)],
  hit=[victim(), eff('poison', 60, 1)], hit_desc=('命中時：毒', 'On hit: poison'))

# 39 forbidden_arcana ---------------------------------------------------------------------------------------
L('forbidden_arcana_weapon', 1, 'forbidden', ('禁理展開', 'Forbidden Unfold'),
  ('32mの禁術で大打撃・8秒拘束・強化剥奪、10秒の術式反射、30秒適応', 'A 32m forbidden spell: smite, bind 8s, strip; 10s reflection; adaptation'),
  [line(32, 3), dmg(1.6), stun(160), strip(), reflect(200, 16), me(), adapt(600)],
  [me(), adapt(40), reflect(25, 6)], ('所持中：適応・術式反射', 'Held: adaptation, reflection'),
  [chain(3, 8), dmg(0.3), stun(10)], ('命中時：術式が3体へ', 'On hit: spell chains to 3'), hitfx='portal')
L('forbidden_arcana_focus', 2, 'forbidden', ('寄生術式', 'Parasitic Formula'),
  ('24m内の敵に術式を寄生：強化を奪い12秒拘束・腐敗V、飛び道具消去', 'Parasitize foes within 24m: steal buffs, bind 12s, wither V'),
  [area(24), strip(True), stun(240), eff('wither', 400, 4), erase(32)],
  [me(), buff('night', 300)], ('所持中：暗視', 'Held: night vision'))
L('forbidden_arcana_charm', 1, 'forbidden', ('自己破棄', 'Self Discard'),
  ('弱さを破棄：浄化・5秒無敵・60秒適応', 'Discard weakness: cleanse, 5s guard, 60s adaptation'),
  [me(), cleanse(), guard(100), adapt(1200)],
  [me(), adapt(40)], ('所持中：適応', 'Held: adaptation'))
L('forbidden_arcana_legend', 3, 'forbidden', ('魔導自己研究・外悪の深淵', 'Abyss of the Outer Evil'),
  ('48m内の敵の強化を奪い20秒拘束・極大打撃・45%以下消去、30秒の万物反射。120秒適応・30秒不死', 'Steal and bind within 48m, erase below 45%; 30s reflection; adaptation, undying'),
  [area(48), strip(True), stun(400), dmg(3.0), execute(0.45), reflect(600, 48), me(), adapt(2400), undying(600), erase(64)],
  LP + [adapt(40), reflect(25, 10)], ('所持中：外悪の魔導', 'Held: outer evil sorcery'),
  [chain(6, 12), dmg(0.5)], ('命中時：術式が6体へ', 'On hit: spell chains to 6'), hitfx='portal')
L('forbidden_arcana_relic_weapon', 1, 'forbidden', ('禁術の残響', 'Echo of the Forbidden'),
  ('16mの禁術で拘束', 'A 16m binding spell'), [line(16, 2), dmg(0.8), stun(40)],
  hit=[victim(), stun(10)], hit_desc=('命中時：一瞬拘束', 'On hit: brief bind'))

# 40 fallen_savior ------------------------------------------------------------------------------------------
L('fallen_savior_weapon', 1, 'fallen', ('光の断罪', 'Judgment of Light'),
  ('40mの光の斬撃で大打撃・焼却、35%以下の悪を断つ。自身浄化・半回復', 'A 40m slash of light: smite, burn, sever evil below 35%; cleanse and heal'),
  [fx('end_rod', 60, 'line', r=40), line(40, 3), dmg(2.0), burn(8), execute(0.35), me(), cleanse(), healpct(0.5)],
  [me(), buff('regen', 40, 0), buff('resist', 40, 0)], ('所持中：勇者の祝福', 'Held: hero\'s blessing'),
  [victim(), burn(4), execute(0.15)], ('命中時：聖火・15%以下を断つ', 'On hit: holy fire, sever below 15%'), hitfx='end_rod')
L('fallen_savior_focus', 2, 'fallen', ('聖印断罪', 'Seal of Judgment'),
  ('32m内の悪を暴く：発光・被ダメ3倍・落雷・大打撃。自身浄化', 'Reveal evil within 32m: glow, x3 damage, lightning, smite'),
  [area(32), eff('glow', 600), mark(600, 3.0), lightning(), dmg(1.5), me(), cleanse()],
  [me(), buff('night', 300)], ('所持中：悪を見抜く眼', 'Held: eye for evil'))
L('fallen_savior_charm', 1, 'fallen', ('不滅の祝福', 'Undying Blessing'),
  ('悪が在る限り倒れない：60秒不死・全快・浄化', 'While evil exists, the hero cannot fall: 60s undying, full heal'),
  [me(), undying(1200), healpct(1.0), cleanse()],
  [low(0.3, [me(), undying(40), buff('regen', 40, 4)])], ('所持中：瀕死で再起', 'Held: rises near death'))
L('fallen_savior_legend', 3, 'fallen', ('全悪救滅・神殺しの聖剣', 'God-Slaying Holy Sword'),
  ('96mの神殺しの斬撃：極大打撃・60%以下を断つ。48m内に落雷と断罪、自身60秒不死・全快・剛力XI', 'A 96m god-slaying cut; judgment across 48m; undying'),
  [fx('end_rod', 100, 'line', r=96), line(96, 5), dmg(3.0), execute(0.6), area(48), lightning(), dmg(2.0), stun(200),
   me(), undying(1200), healpct(1.0), cleanse(), buff('strength', 1200, 10)],
  LP + [low(0.4, [me(), undying(40)])], ('所持中：倒れぬ勇者', 'Held: the hero who never falls'),
  [victim(), execute(0.3), burn(6)], ('命中時：30%以下を断つ', 'On hit: sever below 30%'), hitfx='end_rod')
L('fallen_savior_relic_weapon', 1, 'fallen', ('聖剣の残響', 'Echo of the Holy Sword'),
  ('20mの光の斬撃', 'A 20m slash of light'), [line(20, 2), dmg(1.0)],
  hit=[victim(), burn(3)], hit_desc=('命中時：聖火', 'On hit: holy fire'))

# 41 sweet_pact ---------------------------------------------------------------------------------------------
L('sweet_pact_weapon', 1, 'pact', ('未来差押え', 'Foreclose the Future'),
  ('20m内の敵の未来を差押え：強化を奪い10秒停止・大打撃。エメラルド6・金4、自身回復・満腹', 'Foreclose foes\' futures within 20m: steal, stop 10s, smite; emeralds and gold'),
  [area(20), strip(True), stun(200), dmg(1.2), give('emerald', 6), give('gold', 4), me(), healpct(0.5), food()],
  [me(), buff('luck', 40, 2)], ('所持中：幸運', 'Held: luck'),
  [chance(0.25, [give('emerald', 1)])], ('命中時：25%で利息（エメラルド）', 'On hit: 25% interest'), hitfx='wax')
L('sweet_pact_focus', 2, 'pact', ('甘蜜契約', 'Honeyed Contract'),
  ('全快・満腹・吸収VII・剛力V、エメラルド12・ダイヤ2・経験値120', 'Full heal, satiety, absorption VII, strength V; emeralds, diamonds, experience'),
  [me(), healpct(1.0), food(), buff('absorb', 600, 6), buff('strength', 600, 4), give('emerald', 12), give('diamond', 2), xp(120)],
  [me(), buff('saturation', 40)], ('所持中：満腹', 'Held: satiety'))
L('sweet_pact_charm', 1, 'pact', ('依存救済', 'Dependent Salvation'),
  ('24m内の味方を全快・浄化、パン8', 'Allies: full heal, cleanse; 8 bread'),
  [allies(24), healpct(1.0, True), cleanse(True), give('bread', 8)],
  [me(), buff('luck', 40, 1), buff('regen', 40, 0)], ('所持中：幸運・再生', 'Held: luck, regeneration'))
L('sweet_pact_legend', 3, 'pact', ('未来総有・未怪の債権冠', 'Crown of Total Debt'),
  ('48m内の敵の未来を総取り：強化強奪・20秒停止・極大打撃・40%以下を回収。ダイヤ8・エメラルド32・ネザライト1、自身全快・30秒不死', 'Seize every future within 48m; riches; undying'),
  [area(48), strip(True), stun(400), dmg(2.5), execute(0.4), give('diamond', 8), give('emerald', 32), give('netherite', 1),
   me(), healpct(1.0), undying(600), buff('absorb', 1200, 9)],
  LP + [buff('saturation', 40)], ('所持中：未来の債権者', 'Held: creditor of the future'),
  [chance(0.35, [give('emerald', 2)])], ('命中時：35%で利息', 'On hit: 35% interest'), hitfx='wax')
L('sweet_pact_relic_weapon', 1, 'pact', ('契約の残響', 'Echo of the Pact'),
  ('エメラルド2、最寄りの敵を3秒停止', '2 emeralds; stop the nearest foe 3s'), [give('emerald', 2), near(12, 1), stun(60)],
  hit=[chance(0.1, [give('emerald', 1)])], hit_desc=('命中時：10%で利息', 'On hit: 10% interest'))

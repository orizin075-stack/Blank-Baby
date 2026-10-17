"""Relic arts 1-14."""
from relic_arts import *

LP = LEGEND_PASSIVE

# 1 kokuhaku ------------------------------------------------------------------------------------------------
L('kokuhaku_weapon', 1, 'void', ('虚空一閃', 'Void Flash'),
  ('視線の先28mを一閃。斬った敵を3秒拘束し被ダメ1.5倍の刻印、12m先へ空間歩法', 'Slash 28m ahead: bind 3s, mark x1.5, then step 12m through space'),
  [line(28, 3), dmg(1.5), stun(60), mark(160, 1.5), fx('sonic', 10, 'line', r=28), blink(12)],
  [me(), buff('speed', 40, 1), reflect(25, 5)], ('所持中：俊足、近くの飛び道具を斬り返す', 'Held: swift, cuts nearby projectiles back'),
  [around(3.5), dmg(0.3)], ('命中時：周囲を薙ぐ追撃斬', 'On hit: cleaving follow-up'))
L('kokuhaku_focus', 2, 'void', ('無音納刀', 'Silent Sheathe'),
  ('24m内の敵を7秒停止、飛び道具を全消去、3秒間あらゆる攻撃を斬り落とす', 'Stop foes within 24m for 7s, erase projectiles, 3s of untouchable guard'),
  [area(24), stun(140), erase(24), guard(60), fx('ash', 60, 'ring', r=6)],
  [me(), reflect(25, 7), buff('speed', 40, 0)], ('所持中：飛び道具を自動迎撃', 'Held: auto-intercepts projectiles'))
L('kokuhaku_charm', 1, 'void', ('龍尾払い', 'Dragon-Tail Sweep'),
  ('8m内の敵を龍尾で薙ぎ払い吹き飛ばす', 'Sweep foes within 8m away with a dragon tail'),
  [area(8), dmg(0.6), knock(3.0), fx('crit', 40, 'ring', r=4)],
  [me(), buff('speed', 40, 2), buff('jump', 40, 1), reflect(25, 6)], ('所持中：神速・跳躍・飛び道具迎撃', 'Held: godspeed, leap, projectile intercept'))
L('kokuhaku_legend', 3, 'void', ('剣理終極・虚無一閃', 'Sword Truth: Nothingness Flash'),
  ('64mの次元断ち＋32m内を斬り伏せ10秒拘束、被ダメ3倍、飛び道具消滅、5秒無敵', 'A 64m dimension cut plus 32m sweep: bind 10s, mark x3, erase projectiles, 5s invulnerable'),
  [line(64, 5), dmg(3.0), stun(200), mark(400, 3.0), fx('sonic', 16, 'line', r=64),
   area(32), dmg(1.0), stun(100), erase(48), guard(100), blink(16)],
  LP + [buff('speed', 40, 2), reflect(25, 12)], ('所持中：剣神の加護（剛力・不壊・迎撃）', 'Held: sword god\'s blessing'),
  [chain(6, 12), dmg(0.5)], ('命中時：斬撃が6体へ連鎖', 'On hit: the cut chains to 6 foes'), hitfx='sonic')

# 2 riha ----------------------------------------------------------------------------------------------------
says('riha_weapon', [('理覇：「止まれ」', 'Riha: "Stop."'), ('理覇：「治れ」', 'Riha: "Heal."'), ('理覇：「退け」', 'Riha: "Begone."'), ('理覇：「死んで」', 'Riha: "Die."')])
L('riha_weapon', 1, 'word', ('真言・連詠', 'True Word Litany'),
  ('使うたびに言霊が巡る：止まれ（20m停止）→治れ（味方全快）→退け（吹き飛ばし）→死んで（大打撃・瀕死即死）', 'Cycles words: Stop / Heal / Begone / Die'),
  [cycle('riha_weapon', [('止まれ', [area(20), stun(160), erase(20)]),
                         ('治れ', [allies(20), healpct(1.0, True), cleanse(True)]),
                         ('退け', [area(16), knock(4.0), launch(1.2)]),
                         ('死んで', [area(20), dmg(1.6), execute(0.35)])])],
  [me(), buff('luck', 40, 2), buff('regen', 40, 0)], ('所持中：幸運・再生', 'Held: luck, regeneration'),
  [victim(), stun(30)], ('命中時：「止まれ」', 'On hit: "Stop."'))
says('riha_focus', [('理覇：「晴れて」', 'Riha: "Clear."'), ('理覇：「降って」', 'Riha: "Rain."'), ('理覇：「轟いて」', 'Riha: "Thunder."')])
L('riha_focus', 2, 'word', ('天候詠替', 'Weather Rewrite'),
  ('空模様を詠み替える：晴れ（味方浄化）→雨（味方大回復）→雷（24m内に落雷）', 'Rewrites the sky: clear / rain / thunder strike'),
  [cycle('riha_focus', [('晴れ', [o('weather', w='clear'), allies(24), cleanse(True), buff('speed', 300, 1, True)]),
                        ('雨', [o('weather', w='rain'), allies(24), healpct(1.0, True), buff('regen', 300, 2, True)]),
                        ('雷', [o('weather', w='thunder'), area(24), lightning(), dmg(1.2), stun(60)])])],
  [allies(12), buff('regen', 40, 0, True)], ('所持中：周囲の味方を再生', 'Held: regenerates nearby allies'))
L('riha_charm', 1, 'word', ('虚飾の真実', 'Gilded Truth'),
  ('10秒透明化＋2秒無敵、20m内の敵を幻惑・盲目に', '10s invisible + 2s guard; foes within 20m confused and blinded'),
  [me(), buff('invis', 200), guard(40), area(20), eff('nausea', 160), eff('blind', 100)],
  [me(), buff('slowfall', 40), buff('speed', 40, 0), buff('luck', 40, 1)], ('所持中：沈まない・落ちない足取り', 'Held: weightless steps'))
L('riha_legend', 3, 'word', ('絶対真言', 'Absolute Mantra'),
  ('「止まれ」「治れ」「死んで」を同時に詠む：48m停止、味方全快＋10秒無敵、敵に致命の言霊、空は晴れ渡る', 'Speaks Stop, Heal and Die at once across 48m'),
  [area(48), stun(300), erase(48), allies(32), healpct(1.0, True), cleanse(True), guard(200, True),
   area(48), dmg(2.5), execute(0.5), weather('clear')],
  LP + [allies(16), buff('regen', 40, 1, True)], ('所持中：言霊の神子（味方も再生）', 'Held: blessed oracle, allies regenerate'),
  [victim(), stun(60), mark(100, 2.0)], ('命中時：「止まれ」＋刻印', 'On hit: "Stop." and mark'))

# 3 tenki ---------------------------------------------------------------------------------------------------
L('tenki_weapon', 1, 'royal', ('王権執行', 'Royal Decree'),
  ('前方18mの敵の強化を剥奪し、衰弱IV・大打撃・吹き飛ばし。自身を浄化し飛び道具を拒絶', 'Strip buffs ahead, weakness IV, heavy blow; cleanse self and refuse projectiles'),
  [cone(18, 120), dmg(1.4), strip(), eff('weakness', 200, 3), knock(2.5), me(), cleanse(), erase(18)],
  [me(), buff('absorb', 40, 1), cleanse()], ('所持中：弱体を受け付けない', 'Held: immune to debuffs'),
  [victim(), strip()], ('命中時：敵の強化を剥奪', 'On hit: strips buffs'))
L('tenki_focus', 2, 'royal', ('唯我優先', 'Self Above All'),
  ('4秒無敵＋10秒適応、24m内の敵の強化を奪い取り衰弱V・鈍足IV', '4s guard, 10s adaptation, steal foes\' buffs, weakness V, slow IV'),
  [me(), cleanse(), guard(80), adapt(200), area(24), strip(True), eff('weakness', 300, 4), eff('slow', 200, 3)],
  [me(), cleanse(), buff('resist', 40, 1)], ('所持中：弱体無効・堅牢', 'Held: debuff immunity, sturdy'))
L('tenki_charm', 1, 'royal', ('万象後位', 'All Things Behind'),
  ('20m内の敵を発光させ被ダメ2倍の刻印・鈍足', 'Foes within 20m glow, take x2 damage and slow'),
  [area(20), eff('glow', 300), mark(300, 2.0), eff('slow', 200, 2)],
  [me(), cleanse(), buff('absorb', 40, 1)], ('所持中：弱体無効・吸収', 'Held: debuff immunity, absorption'))
L('tenki_legend', 3, 'royal', ('唯一絶対・王権万象', 'Sole Absolute: Royal Cosmos'),
  ('40m内の全てを跪かせる：叩き伏せ12秒拘束、強化を奪い衰弱X、大打撃。自身は30秒不死・5秒無敵', 'All within 40m kneel: slam, bind 12s, steal buffs, weakness X; 30s undying'),
  [area(40), slam(4.0), stun(240), strip(True), eff('weakness', 400, 9), dmg(2.5),
   me(), undying(600), guard(100), cleanse(), buff('absorb', 600, 9), erase(48)],
  LP + [cleanse()], ('所持中：王の加護（弱体無効）', 'Held: king\'s aegis'),
  [victim(), strip(True), mark(200, 2.0)], ('命中時：強化を奪い刻印', 'On hit: steal buffs and mark'))

# 4 chaos ---------------------------------------------------------------------------------------------------
CHAOS_ROLL = [transmute(), launch(2.4), eff('levitate', 100, 3), stun(100), dmg(1.5), freeze(300), burn(10)]
L('chaos_weapon', 1, 'chaos', ('万象変転', 'Metamorphosis'),
  ('16m内の敵を一体ずつ無作為に書き換える：家畜化・打ち上げ・浮遊・停止・大打撃・凍結・炎上', 'Rewrites each foe within 16m at random: livestock, launch, float, stop, smite, freeze, burn'),
  [area(16), each(CHAOS_ROLL)],
  [me(), buff('luck', 40, 3)], ('所持中：幸運', 'Held: luck'),
  [chance(0.3, [victim(), transmute()], [victim(), dmg(0.2)])], ('命中時：30%で家畜へ変質', 'On hit: 30% turn into livestock'), hitfx='witch')
L('chaos_focus', 2, 'chaos', ('異常重力', 'Gravity Anomaly'),
  ('24m内の重力を反転：敵を打ち上げ浮遊させ大打撃', 'Invert gravity within 24m: launch, float, smite'),
  [area(24), launch(2.6), eff('levitate', 120, 2), dmg(1.0)],
  [me(), buff('slowfall', 40), buff('jump', 40, 2)], ('所持中：重力軽減', 'Held: low gravity'))
L('chaos_charm', 1, 'chaos', ('混沌の殻', 'Shell of Chaos'),
  ('3秒無敵＋15秒適応、10m内の敵を無作為に乱す', '3s guard, 15s adaptation, scramble foes within 10m'),
  [me(), guard(60), adapt(300), area(10), each([knock(3.0), eff('nausea', 200), eff('levitate', 80, 2)])],
  [me(), adapt(40)], ('所持中：同じ攻撃に二度は傷つかない', 'Held: never hurt twice by the same kind of attack'))
L('chaos_legend', 3, 'chaos', ('万象錯綜・虹核崩界', 'Rainbow Core Collapse'),
  ('40m内の通常の敵を全て家畜へ書き換え、残る強敵を浮遊・拘束・大打撃', 'Turns every ordinary foe within 40m into livestock; bosses float, bound and smitten'),
  [area(40), transmute(), area(40), dmg(2.5), eff('levitate', 200, 4), stun(200), fx('firework', 60, 't')],
  LP + [adapt(40)], ('所持中：混沌の加護', 'Held: chaos aegis'),
  [chance(0.5, [victim(), transmute()], [victim(), dmg(0.5)])], ('命中時：50%で家畜化', 'On hit: 50% livestock'), hitfx='witch')

# 5 berit ---------------------------------------------------------------------------------------------------
L('berit_weapon', 1, 'alchemy', ('万界解体', 'Universal Dismantle'),
  ('前方12mの敵を解体：武器を奪い強化を剥ぎ大打撃。素材（金・鉄）を錬成し装備を修復', 'Dismantle foes ahead: disarm, strip, smite; transmute gold and iron, repair gear'),
  [cone(12, 100), dmg(1.4), disarm(), strip(), give('gold', 4), give('iron', 6), repair(128)],
  [me(), repair(4), buff('haste', 40, 1)], ('所持中：装備自動修復', 'Held: self-repairing gear'),
  [chance(0.25, [give('gold', 1)])], ('命中時：25%で金を錬成', 'On hit: 25% transmute gold'))
L('berit_focus', 2, 'alchemy', ('無価値錬成', 'Worthless Transmutation'),
  ('塵からダイヤ2・エメラルド6・ネザライト1を錬成、経験値80、全装備を大修復、満腹', 'Transmute dust into diamonds, emeralds and netherite; heavy repair; full'),
  [give('diamond', 2), give('emerald', 6), give('netherite', 1), xp(80), repair(512), food()],
  [me(), repair(8)], ('所持中：装備自動修復', 'Held: self-repairing gear'))
L('berit_charm', 1, 'alchemy', ('等価破戒', 'Broken Equivalence'),
  ('16m内の敵の武器を鎖に変えて奪い、強化を吸い取り5秒拘束', 'Turn foes\' weapons to chains, steal their buffs, bind 5s'),
  [area(16), disarm(), strip(True), stun(100)],
  [me(), buff('luck', 40, 2), buff('haste', 40, 2)], ('所持中：幸運・採掘加速', 'Held: luck, haste'))
L('berit_legend', 3, 'alchemy', ('塵芥創界・神域錬成', 'Dust Genesis'),
  ('40m内の敵を武装解除し家畜へ錬成、残りに大打撃。ネザライト2・ダイヤ8を創造、全快＋強大な吸収', 'Disarm and transmute everything within 40m; create netherite and diamonds; full heal'),
  [area(40), disarm(), transmute(), area(40), dmg(2.0), give('netherite', 2), give('diamond', 8), repair(4096),
   me(), healpct(1.0), buff('absorb', 600, 6), allies(24), buff('absorb', 600, 4, True)],
  LP + [repair(64)], ('所持中：神域の錬成者', 'Held: divine alchemist'),
  [chance(0.3, [victim(), transmute()], [give('gold', 1)])], ('命中時：30%で錬成変質', 'On hit: 30% transmute'))

# 6 elseria -------------------------------------------------------------------------------------------------
L('elseria_weapon', 1, 'star', ('星脈射線', 'Starvein Ray'),
  ('48mの光線で貫き炎上、雷が5体へ連鎖', 'A 48m ray that burns; lightning chains to 5 foes'),
  [fx('end_rod', 60, 'line', r=48), line(48, 2), dmg(1.6), burn(6), chain(5, 10), lightning(), dmg(0.6)],
  [allies(10), buff('regen', 40, 0, True)], ('所持中：周囲の味方を再生', 'Held: regenerates allies'),
  [chain(3, 8), dmg(0.3)], ('命中時：雷光が3体へ連鎖', 'On hit: lightning chains to 3'), hitfx='spark')
L('elseria_focus', 2, 'star', ('天球大術', 'Celestial Grand Spell'),
  ('32m内に雷光の天災：落雷・大打撃・鈍足、味方は半回復、空は雷雨に', 'A 32m storm of light: lightning, smite, slow; allies healed'),
  [o('weather', w='thunder'), area(32), lightning(), dmg(1.5), eff('slow', 200, 3), allies(24), healpct(0.5, True)],
  [me(), buff('night', 300), buff('regen', 40, 0)], ('所持中：暗視・再生', 'Held: night vision, regeneration'))
L('elseria_charm', 1, 'star', ('魔力循環', 'Mana Circulation'),
  ('自身半回復・浄化、経験値、16m内の味方に再生III', 'Heal and cleanse self, experience, regeneration III to allies'),
  [me(), healpct(0.5), cleanse(), xp(30), allies(16), buff('regen', 200, 2, True)],
  [me(), buff('regen', 40, 0), buff('haste', 40, 0)], ('所持中：再生・加速', 'Held: regeneration, haste'))
L('elseria_legend', 3, 'star', ('星界大術・原初魔典', 'Primordial Codex'),
  ('48m内に原初魔法の天災：落雷・焼却・拘束・極大打撃、64mの光線、味方は全快', 'A primordial cataclysm within 48m plus a 64m ray; allies fully healed'),
  [area(48), lightning(), dmg(3.0), burn(15), stun(160), line(64, 4), dmg(2.0), fx('end_rod', 80, 'line', r=64),
   allies(32), healpct(1.0, True), cleanse(True)],
  LP, ('所持中：魔祖の加護', 'Held: archmage\'s blessing'),
  [chain(6, 12), dmg(0.4), lightning()], ('命中時：雷が6体へ連鎖', 'On hit: lightning chains to 6'), hitfx='spark')

# 7 valeria -------------------------------------------------------------------------------------------------
L('valeria_weapon', 1, 'tech', ('変形打撃', 'Transforming Strike'),
  ('8m内を槌で粉砕し打ち上げ、装備大修復、製造眷属（ゴーレム）1体', 'Smash and launch within 8m, heavy repair, build a golem'),
  [area(8), dmg(1.6), knock(3.0), launch(1.2), repair(256), summon('golem', 1)],
  [me(), repair(6)], ('所持中：装備自動修復', 'Held: self-repair'),
  [around(3), dmg(0.3), knock(1.0)], ('命中時：衝撃が周囲へ', 'On hit: shockwave'))
L('valeria_focus', 2, 'tech', ('即席兵装', 'Instant Armament'),
  ('ゴーレム3体を即席製造、全装備を大修復、強大な吸収', 'Build 3 golems, massive repair, heavy absorption'),
  [summon('golem', 3), repair(1024), me(), buff('absorb', 400, 4)],
  [me(), repair(8), buff('haste', 40, 1)], ('所持中：修復・加速', 'Held: repair, haste'))
L('valeria_charm', 1, 'tech', ('自動迎撃展開', 'Auto Intercept'),
  ('10秒間、全ての飛び道具を撃ち返す。周囲の飛び道具を消去し2秒無敵', 'Reflect all projectiles for 10s, erase nearby ones, 2s guard'),
  [reflect(200, 16), erase(24), guard(40)],
  [me(), reflect(25, 8), buff('resist', 40, 0)], ('所持中：自動迎撃の外殻', 'Held: auto-intercept shell'))
L('valeria_legend', 3, 'tech', ('終着無限・万機工房', 'Endless Workshop'),
  ('ゴーレム6体を製造、全装備を完全修復、極大吸収＋5秒無敵、40m内の敵を砲撃', 'Build 6 golems, full repair, huge absorption, 5s guard, bombard 40m'),
  [summon('golem', 6), repair(99999), me(), buff('absorb', 1200, 9), guard(100), area(40), dmg(2.5), stun(120), fx('explosion', 4, 't')],
  LP + [reflect(25, 10), repair(64)], ('所持中：工房の加護（迎撃・修復）', 'Held: workshop aegis'),
  [around(4), dmg(0.4), knock(1.5)], ('命中時：衝撃波', 'On hit: shockwave'))

# 8 huang_linghua -------------------------------------------------------------------------------------------
L('huang_linghua_weapon', 1, 'dragon', ('龍気衝', 'Dragon Qi Lance'),
  ('32mを龍気で貫き吹き飛ばす。周囲の味方を回復', 'Pierce 32m with dragon qi and blast; heal nearby allies'),
  [line(32, 3), dmg(1.5), knock(3.0), launch(1.0), allies(12), healpct(0.4, True)],
  [me(), buff('absorb', 40, 1), buff('regen', 40, 0)], ('所持中：龍鱗の守り', 'Held: dragon scale'),
  [victim(), stun(20), around(3), dmg(0.2)], ('命中時：龍文拘束＋衝撃', 'On hit: dragon seal and shock'))
L('huang_linghua_focus', 2, 'dragon', ('三界複合術', 'Three Realms Spell'),
  ('天・地・海の三術：32m内に落雷、地を叩き伏せ7秒拘束、潮で鈍足V', 'Sky, earth and sea at once within 32m'),
  [o('weather', w='thunder'), area(32), lightning(), dmg(1.2), slam(2.0), stun(140), eff('slow', 200, 4)],
  [me(), buff('water', 300), buff('dolphin', 40, 1)], ('所持中：水中呼吸・遊泳', 'Held: water breathing, swimming'))
L('huang_linghua_charm', 1, 'dragon', ('龍炉再生', 'Dragon Furnace'),
  ('全快・浄化・再生IV・吸収V（血から再構成する龍の生命）', 'Full heal, cleanse, regeneration IV, absorption V'),
  [me(), healpct(1.0), cleanse(), buff('regen', 200, 3), buff('absorb', 400, 4)],
  [me(), buff('regen', 40, 1)], ('所持中：再生II', 'Held: regeneration II'))
L('huang_linghua_legend', 3, 'dragon', ('皇龍創法・万龍封界', 'Imperial Dragon Seal'),
  ('48m内を龍文で封じる：15秒拘束・落雷・極大打撃・被ダメ2.5倍。味方全快＋吸収、自身20秒不死', 'Seal 48m in dragon script; allies restored; 20s undying'),
  [o('weather', w='thunder'), area(48), stun(300), lightning(), dmg(2.5), mark(400, 2.5), allies(32), healpct(1.0, True),
   buff('absorb', 600, 5, True), me(), undying(400)],
  LP + [allies(16), buff('regen', 40, 0, True)], ('所持中：龍仙の加護（味方再生）', 'Held: dragon sage aegis'),
  [chain(5, 10), dmg(0.3)], ('命中時：龍気が5体へ', 'On hit: qi chains to 5'), hitfx='spark')

# 9 ferdinand -----------------------------------------------------------------------------------------------
L('ferdinand_weapon', 1, 'tech', ('魔導連射', 'Arcane Barrage'),
  ('48mの射線を連射砲で掃射し、命中した敵に矢の雨。前方は炎上弾', 'Sweep a 48m line, rain arrows on the hit; incendiary spread ahead'),
  [fx('firework', 40, 'line', r=48), line(48, 2), dmg(1.2), arrows(6, 30), cone(20, 40), dmg(0.6), burn(4)],
  [me(), repair(4)], ('所持中：装備自動修復', 'Held: self-repair'),
  [chance(0.3, [around(4), dmg(0.3), fx('explosion', 2, 't')])], ('命中時：30%で炸裂弾', 'On hit: 30% explosive round'))
L('ferdinand_focus', 2, 'tech', ('文明跳躍', 'Civilization Leap'),
  ('資源を発明：レッドストーン16・鉄8・金4・石炭16、装備大修復、ゴーレム2体', 'Invent resources, heavy repair, 2 golems'),
  [give('redstone', 16), give('iron', 8), give('gold', 4), give('coal', 16), repair(2048), summon('golem', 2)],
  [me(), buff('haste', 40, 2), repair(6)], ('所持中：作業加速・修復', 'Held: haste, repair'))
L('ferdinand_charm', 1, 'tech', ('時刻調律', 'Clock Tuning'),
  ('時刻を朝に調律、自身に神速・作業加速、周囲の飛び道具を消去', 'Set the clock to morning; speed and haste; erase projectiles'),
  [time_(1000), me(), buff('speed', 300, 3), buff('haste', 300, 2), erase(24)],
  [me(), buff('speed', 40, 0), buff('night', 300)], ('所持中：俊足・暗視', 'Held: speed, night vision'))
L('ferdinand_legend', 3, 'tech', ('文明跳躍・未来工廠', 'Future Foundry'),
  ('48m内に軌道砲撃：落雷と矢の豪雨で極大打撃。ゴーレム6体、ダイヤ8・ネザライト2、完全修復', 'Orbital strike within 48m; 6 golems; diamonds and netherite; full repair'),
  [area(48), lightning(), arrows(10, 60), dmg(2.5), summon('golem', 6), give('diamond', 8), give('netherite', 2), repair(99999)],
  LP + [buff('haste', 40, 3)], ('所持中：未来工廠', 'Held: future foundry'),
  [around(5), dmg(0.4), fx('explosion', 3, 't')], ('命中時：炸裂', 'On hit: explosion'))

# 10 mels ---------------------------------------------------------------------------------------------------
L('mels_weapon', 1, 'water', ('百拳流転', 'Hundred Fists'),
  ('10m内の敵を引き寄せ4連撃、4秒拘束。自身に耐性IV', 'Pull foes within 10m into a 4-hit combo, bind 4s; resistance IV'),
  [area(10), pull(1.2)] + rep(4, dmg(0.5)) + [stun(80), me(), buff('resist', 200, 3)],
  [me(), buff('resist', 40, 0), buff('speed', 40, 0)], ('所持中：流体の身のこなし', 'Held: fluid movement'),
  [victim(), dmg(0.15), dmg(0.15), stun(10)], ('命中時：追い打ち2連', 'On hit: 2 extra strikes'), hitfx='splash')
L('mels_focus', 2, 'water', ('流体拘束', 'Fluid Bind'),
  ('20m内の敵を流体で絡め取り引き寄せ10秒拘束・鈍足VI、自身2秒無敵', 'Grab foes within 20m, pull, bind 10s, slow VI; 2s guard'),
  [area(20), pull(2.5), stun(200), eff('slow', 300, 5), me(), guard(40)],
  [me(), buff('jump', 40, 2), buff('slowfall', 40)], ('所持中：跳躍・軽身', 'Held: leap, light body'))
L('mels_charm', 1, 'water', ('衝撃分散', 'Impact Dispersal'),
  ('5秒無敵＋20秒適応＋耐性V', '5s guard, 20s adaptation, resistance V'),
  [me(), guard(100), adapt(400), buff('resist', 400, 4)],
  [me(), buff('resist', 40, 1)], ('所持中：耐性II', 'Held: resistance II'))
L('mels_legend', 3, 'water', ('武理完成・無形万武', 'Formless Myriad Arts'),
  ('32m内の敵を引き寄せ6連撃で叩き12秒拘束、最後に吹き飛ばす。4秒無敵・30秒適応', 'Pull all within 32m into a 6-hit combo, bind 12s, blast away'),
  [area(32), pull(3.0)] + rep(6, dmg(1.0)) + [stun(240), knock(4.0), me(), guard(80), adapt(600)],
  LP + [buff('resist', 40, 1)], ('所持中：武王の加護', 'Held: martial king aegis'),
  [victim(), dmg(0.3), dmg(0.3), dmg(0.3), around(4), dmg(0.2)], ('命中時：3連撃＋衝撃', 'On hit: 3 strikes + shock'), hitfx='splash')

# 11 hephaistos ---------------------------------------------------------------------------------------------
L('hephaistos_weapon', 1, 'tech', ('概念切削', 'Concept Cutting'),
  ('24mを切削：大打撃・強化剥奪・武装解除、体力30%以下の敵は存在ごと削り取る', 'Drill 24m: smite, strip, disarm, and erase anything below 30% health'),
  [line(24, 2.5), dmg(1.6), strip(), disarm(), execute(0.3), fx('crit', 40, 'line', r=24)],
  [me(), repair(6)], ('所持中：自動修復', 'Held: self-repair'),
  [victim(), strip(), execute(0.15)], ('命中時：強化剥奪・削り取り', 'On hit: strip and erase'))
L('hephaistos_focus', 2, 'tech', ('分散工廠', 'Distributed Foundry'),
  ('ゴーレム4体、ネザライト1・ダイヤ4、全装備の超修復、極大吸収', '4 golems, netherite and diamonds, huge repair, huge absorption'),
  [summon('golem', 4), give('netherite', 1), give('diamond', 4), repair(4096), me(), buff('absorb', 600, 6)],
  [me(), repair(12)], ('所持中：修復', 'Held: repair'))
L('hephaistos_charm', 1, 'tech', ('対抗装甲製造', 'Counter-Armor'),
  ('30秒適応（受けた攻撃種別を無効化する装甲を製造）、3秒無敵、耐性V', '30s adaptation, 3s guard, resistance V'),
  [me(), adapt(600), guard(60), buff('resist', 400, 4)],
  [me(), adapt(40)], ('所持中：常時適応装甲', 'Held: adaptive armor'))
L('hephaistos_legend', 3, 'tech', ('製造神格・無限工廠', 'Godforge'),
  ('48m内を切削：極大打撃・武装解除・60%以下を消去。ゴーレム6体、30秒不死・60秒適応、ネザライト4', 'Cut 48m: smite, disarm, erase below 60%; 6 golems; undying and adaptation'),
  [area(48), dmg(3.0), disarm(), execute(0.6), stun(200), summon('golem', 6), me(), undying(600), adapt(1200),
   give('netherite', 4), repair(99999)],
  LP + [adapt(40), repair(64)], ('所持中：機械神の加護', 'Held: machine god aegis'),
  [victim(), execute(0.3)], ('命中時：30%以下を消去', 'On hit: erase below 30%'))

# 12 nortia -------------------------------------------------------------------------------------------------
L('nortia_weapon', 1, 'game', ('罰ゲーム！', 'Penalty Game!'),
  ('16m内の敵をピコッと叩いて打ち上げ・浮遊・混乱・8秒拘束。味方は回復', 'Bonk foes within 16m: launch, float, confuse, bind 8s; heal allies'),
  [area(16), dmg(1.2), stun(160), launch(1.2), eff('levitate', 60, 1), eff('nausea', 160), allies(16), heal(12, True),
   o('say', k='relic_art.oror_supreme_bosses.nortia_weapon.say0')],
  [me(), buff('luck', 40, 3), buff('jump', 40, 1)], ('所持中：幸運・跳躍', 'Held: luck, leap'),
  [victim(), launch(1.0), eff('levitate', 20, 2)], ('命中時：ピコッと打ち上げ', 'On hit: bonk into the air'), hitfx='heart')
says('nortia_weapon', [('ノルティア：罰ゲーム！もう一回遊ぼう！', 'Nortia: Penalty game! Let\'s play again!')])
L('nortia_focus', 2, 'game', ('運命のサイコロ', 'Dice of Fate'),
  ('サイコロを振る：当たりなら24m内に極大打撃と10秒拘束、外れなら味方全快＋剛力V', 'Roll: a 24m smite and 10s bind, or full heal and strength V for allies'),
  [chance(0.5, [area(24), dmg(2.5), stun(200), fx('firework', 30, 't')], [allies(24), healpct(1.0, True), buff('strength', 600, 4, True)])],
  [me(), buff('luck', 40, 4)], ('所持中：幸運V', 'Held: luck V'))
L('nortia_charm', 1, 'game', ('もう一回！', 'One More Try!'),
  ('5秒前の体力と位置へ巻き戻し、浄化して2秒無敵', 'Rewind to 5s ago, cleanse, 2s guard'),
  [rewind(), me(), guard(40), cleanse()],
  [snapshot(), me(), buff('luck', 40, 1)], ('所持中：リトライ記録', 'Held: retry record'))
L('nortia_legend', 3, 'game', ('世界遊戯・絶対ルール', 'Absolute Rule'),
  ('ルール「動いたら負け」：48m内の敵を20秒拘束・浮遊・強化剥奪・極大打撃。味方全快＋30秒不死', 'Rule: "Whoever moves loses." 48m bind 20s, float, strip, smite; allies undying 30s'),
  [area(48), stun(400), eff('levitate', 200, 3), strip(), dmg(2.5), allies(32), healpct(1.0, True), undying(600, True)],
  LP + [snapshot()], ('所持中：遊戯神の加護', 'Held: game god aegis'),
  [victim(), launch(1.4), stun(30)], ('命中時：打ち上げ拘束', 'On hit: launch and bind'), hitfx='heart')

# 13 lucifara -----------------------------------------------------------------------------------------------
L('lucifara_weapon', 1, 'desire', ('堕天刈り', 'Fallen Reap'),
  ('前方14mを刈り取り、敵の強化（欲望）を奪い衰弱V・幻惑。自身は回復', 'Reap ahead, steal desires (buffs), weakness V, confusion; heal self'),
  [cone(14, 160), dmg(1.5), strip(True), eff('weakness', 300, 4), eff('nausea', 200), me(), healpct(0.3)],
  [me(), buff('regen', 40, 0)], ('所持中：再生', 'Held: regeneration'),
  [victim(), strip(True), me(), heal(4)], ('命中時：強化を奪い回復', 'On hit: steal buffs, heal'), hitfx='heart')
L('lucifara_focus', 2, 'desire', ('誘惑', 'Temptation'),
  ('24m内の敵を魅了して引き寄せ、幻惑・衰弱VI・鈍足、被ダメ2倍', 'Charm foes within 24m: pull, confuse, weakness VI, slow, x2 damage'),
  [area(24), pull(2.5), eff('nausea', 300), eff('weakness', 400, 5), eff('slow', 300, 3), mark(300, 2.0)],
  [me(), buff('night', 300)], ('所持中：暗視', 'Held: night vision'))
L('lucifara_charm', 1, 'desire', ('甘夢', 'Sweet Dream'),
  ('20m内の敵を甘い夢に沈め10秒拘束・盲目、自身は透明化・再生III', 'Foes within 20m sink into dreams: bind 10s, blind; invisible and regenerating'),
  [area(20), stun(200), eff('blind', 200), me(), buff('invis', 200), buff('regen', 200, 2)],
  [me(), buff('slowfall', 40), buff('speed', 40, 0)], ('所持中：翼の加護', 'Held: wings'))
L('lucifara_legend', 3, 'desire', ('欲望王権・魂宴の聖杯', 'Grail of the Soul Feast'),
  ('40m内の全ての欲望を奪う：強化強奪・引き寄せ・15秒拘束・衰弱X・極大打撃。自身と味方は全快', 'Steal every desire within 40m; bind 15s, weakness X; full heal'),
  [area(40), strip(True), pull(2.0), stun(300), eff('weakness', 600, 9), dmg(2.5), me(), healpct(1.0), buff('absorb', 600, 8),
   allies(32), healpct(1.0, True)],
  LP + [buff('regen', 40, 1)], ('所持中：欲望の王', 'Held: lord of desire'),
  [victim(), strip(True), me(), heal(10)], ('命中時：強化強奪・回復', 'On hit: steal, heal'), hitfx='heart')

# 14 taika --------------------------------------------------------------------------------------------------
L('taika_weapon', 1, 'force', ('超克連撃', 'Transcending Barrage'),
  ('最寄りの敵の背後へ踏み込み3連撃で打ち上げ吹き飛ばす。自身に剛力VII', 'Step behind the nearest foe, 3 strikes, launch and blast; strength VII'),
  [near(20, 1), behind()] + rep(3, dmg(1.0)) + [knock(4.0), launch(1.5), me(), buff('strength', 300, 6)],
  [me(), buff('speed', 40, 1), buff('strength', 40, 1)], ('所持中：俊足・剛力', 'Held: speed, strength'),
  [victim(), dmg(0.3), knock(1.5)], ('命中時：追撃と吹き飛ばし', 'On hit: follow-up blast'), hitfx='explosion')
L('taika_focus', 2, 'force', ('修練解放', 'Training Unleashed'),
  ('剛力X・神速IV・耐性IV・跳躍III（30秒）、半回復', 'Strength X, speed IV, resistance IV, jump III for 30s; heal half'),
  [me(), buff('strength', 600, 9), buff('speed', 600, 3), buff('resist', 600, 3), buff('jump', 600, 2), healpct(0.5)],
  [me(), buff('haste', 40, 1), buff('jump', 40, 1)], ('所持中：修練', 'Held: training'))
L('taika_charm', 1, 'force', ('限界超越', 'Beyond Limits'),
  ('20秒適応。体力40%以下なら全快・剛力X・3秒無敵', '20s adaptation; below 40% health: full heal, strength X, 3s guard'),
  [me(), adapt(400), low(0.4, [me(), healpct(1.0), buff('strength', 400, 9), guard(60)])],
  [low(0.5, [me(), buff('strength', 40, 6), buff('resist', 40, 2)])], ('所持中：窮地で覚醒（剛力VII・耐性III）', 'Held: awakens when cornered'))
L('taika_legend', 3, 'force', ('覇王更新・無限超克', 'Endless Transcendence'),
  ('32m内の敵へ5連撃、打ち上げて吹き飛ばす。剛力XXI・神速V・30秒不死・60秒適応', '5 strikes on all within 32m, launch and blast; strength XXI, undying, adaptation'),
  [area(32)] + rep(5, dmg(1.0)) + [launch(2.0), knock(5.0), me(), buff('strength', 1200, 20), buff('speed', 1200, 4), undying(600), adapt(1200)],
  LP + [buff('speed', 40, 1)], ('所持中：覇王', 'Held: overlord'),
  [victim(), dmg(0.5), dmg(0.5), knock(3.0)], ('命中時：2連撃で吹き飛ばす', 'On hit: 2 strikes and blast'), hitfx='explosion')

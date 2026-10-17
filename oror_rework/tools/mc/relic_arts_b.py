"""Relic arts 15-28."""
from relic_arts import *

LP = LEGEND_PASSIVE

# 15 mary_sue -----------------------------------------------------------------------------------------------
L('mary_sue_weapon', 1, 'story', ('主人公補正', 'Protagonist Armor'),
  ('全快・浄化・吸収VI・剛力V、16m内に大打撃。体力30%以下なら20秒不死と24mの逆転劇', 'Full heal, cleanse, absorption and strength, smite 16m; when low: undying and a 24m comeback'),
  [me(), healpct(1.0), cleanse(), buff('absorb', 400, 5), buff('strength', 400, 4), area(16), dmg(1.4),
   low(0.3, [me(), undying(400), guard(60), area(24), dmg(2.0)])],
  [low(0.35, [me(), buff('strength', 40, 5), buff('regen', 40, 3)])], ('所持中：窮地で覚醒', 'Held: awakens when cornered'),
  [low(0.5, [victim(), dmg(0.5)])], ('命中時：窮地なら追撃', 'On hit: extra damage when low'), hitfx='end_rod')
L('mary_sue_focus', 2, 'story', ('覚醒の頁', 'Page of Awakening'),
  ('経験値200、体力増強V・全快・剛力VI（30秒）', '200 experience, health boost V, full heal, strength VI'),
  [me(), xp(200), buff('health', 1200, 4), healpct(1.0), buff('strength', 600, 5)],
  [me(), buff('luck', 40, 2), buff('health', 40, 0)], ('所持中：幸運・体力増強', 'Held: luck, health boost'))
L('mary_sue_charm', 1, 'story', ('敗北転換', 'Defeat Reversal'),
  ('30秒不死（倒れるはずの一撃を「真の力の目覚め」に書き換える）、2秒無敵、浄化', '30s undying, 2s guard, cleanse'),
  [me(), undying(600), guard(40), cleanse()],
  [low(0.25, [me(), buff('regen', 40, 4), buff('resist', 40, 3)])], ('所持中：瀕死時に再起', 'Held: rises when near death'))
L('mary_sue_legend', 3, 'story', ('物語永続・無限覚醒', 'Eternal Awakening'),
  ('60秒不死・全快・浄化・体力増強X・剛力XIII・吸収X、40m内に極大打撃と拘束', '60s undying, full heal, massive boosts; smite and bind 40m'),
  [me(), undying(1200), healpct(1.0), cleanse(), buff('health', 2400, 9), buff('strength', 1200, 12), buff('absorb', 1200, 9),
   area(40), dmg(2.5), stun(160)],
  LP + [low(0.5, [me(), undying(40)])], ('所持中：体力50%以下で倒れない', 'Held: cannot fall below 50% health'),
  [low(0.5, [victim(), dmg(1.0)])], ('命中時：窮地なら大打撃', 'On hit: heavy damage when low'), hitfx='end_rod')

# 16 savior -------------------------------------------------------------------------------------------------
L('savior_weapon', 1, 'holy', ('聖域展開', 'Sanctuary'),
  ('24m内の味方を全快・浄化・3秒無敵・吸収V、敵を押し出し飛び道具を消去', 'Allies within 24m: full heal, cleanse, guard, absorption; push foes out, erase projectiles'),
  [allies(24), healpct(1.0, True), cleanse(True), guard(60, True), buff('absorb', 400, 4, True), area(16), knock(3.0), erase(24)],
  [allies(12), buff('regen', 40, 0, True), me(), buff('resist', 40, 1)], ('所持中：味方を再生・自身堅牢', 'Held: allies regenerate'),
  [victim(), knock(2.0)], ('命中時：聖なる押し返し', 'On hit: holy push'), hitfx='end_rod')
L('savior_focus', 2, 'holy', ('慈愛の祈り', 'Prayer of Mercy'),
  ('32m内の味方を全快・浄化・再生IV・体力増強III', 'Allies within 32m: full heal, cleanse, regeneration IV, health boost III'),
  [allies(32), healpct(1.0, True), cleanse(True), buff('regen', 600, 3, True), buff('health', 1200, 2, True)],
  [allies(16), buff('regen', 40, 0, True)], ('所持中：味方を再生', 'Held: allies regenerate'))
L('savior_charm', 1, 'holy', ('避難聖域', 'Refuge'),
  ('20m内の味方に5秒無敵、敵を外へ押し出し、32m内の飛び道具を消去', 'Allies 5s invulnerable, foes pushed out, projectiles erased'),
  [allies(20), guard(100, True), area(20), knock(4.0), erase(32)],
  [me(), reflect(25, 6)], ('所持中：飛び道具を弾く結界', 'Held: barrier against projectiles'))
L('savior_legend', 3, 'holy', ('万命救済・最後の聖域', 'The Last Sanctuary'),
  ('48m内の味方を全快・浄化・10秒無敵・60秒不死。敵を浄化の光で押し出し拘束し極大打撃、飛び道具消滅', 'Allies: full heal, guard, 60s undying; foes purified, bound and pushed out'),
  [allies(48), healpct(1.0, True), cleanse(True), guard(200, True), undying(1200, True), area(48), knock(5.0), stun(200),
   dmg(2.0), erase(64)],
  LP + [allies(16), buff('regen', 40, 1, True), reflect(25, 8)], ('所持中：救世の結界', 'Held: savior\'s barrier'),
  [victim(), knock(3.0), stun(20)], ('命中時：押し返し拘束', 'On hit: push and bind'), hitfx='end_rod')

# 17 gokuka -------------------------------------------------------------------------------------------------
L('gokuka_weapon', 1, 'curse', ('呪禍裂爪', 'Cursed Rending'),
  ('前方12mを裂き、衰弱・病毒・腐敗・飢餓の呪いを刻む。呪霊（狼）を2体喚ぶ', 'Rend ahead with wither, poison, weakness and hunger; summon 2 curse spirits'),
  [cone(12, 120), dmg(1.4), eff('wither', 400, 4), eff('poison', 400, 4), eff('weakness', 400, 3), eff('hunger', 400, 5), summon('wolf', 2)],
  [me(), buff('night', 300)], ('所持中：暗視', 'Held: night vision'),
  [victim(), eff('wither', 100, 2), eff('poison', 100, 2)], ('命中時：衰弱・毒', 'On hit: wither and poison'), hitfx='sculk')
L('gokuka_focus', 2, 'curse', ('分御霊', 'Divided Spirit'),
  ('24m内に呪液を撒く：衰弱VII・盲目・暗闇・強化剥奪。呪霊3体', 'Spill curse within 24m: wither VII, blind, darkness, strip; 3 spirits'),
  [area(24), eff('wither', 600, 6), eff('blind', 200), eff('dark', 300), strip(), summon('wolf', 3)],
  [me(), buff('regen', 40, 0)], ('所持中：再生', 'Held: regeneration'))
L('gokuka_charm', 1, 'curse', ('静眠封呪', 'Slumber Seal'),
  ('20m内の敵を15秒眠らせ鈍足VI、自身2秒無敵', 'Put foes within 20m to sleep for 15s, slow VI; 2s guard'),
  [area(20), stun(300), eff('slow', 400, 5), me(), guard(40)],
  [area(6), eff('weakness', 40, 1)], ('所持中：周囲の敵を衰弱させる', 'Held: weakens nearby foes'))
L('gokuka_legend', 3, 'curse', ('業禍根源・万呪外法', 'Root of All Curses'),
  ('48m内に万の呪い：衰弱X・毒X・弱化X・飢餓・盲目・暗闇・極大打撃・50%以下即死・被ダメ3倍。呪霊6体', 'Every curse within 48m; instant death below 50%; 6 spirits'),
  [area(48), eff('wither', 1200, 9), eff('poison', 1200, 9), eff('weakness', 1200, 9), eff('hunger', 600, 9), eff('blind', 300),
   eff('dark', 600), dmg(2.5), execute(0.5), mark(600, 3.0), summon('wolf', 6)],
  LP + [area(8), eff('wither', 40, 2)], ('所持中：呪いの瘴気（周囲を蝕む）', 'Held: curse miasma'),
  [victim(), eff('wither', 200, 4), execute(0.2)], ('命中時：呪い・20%以下即死', 'On hit: curse, execute below 20%'), hitfx='sculk')

# 18 merlinus -----------------------------------------------------------------------------------------------
L('merlinus_weapon', 1, 'arcane', ('深淵射線', 'Abyssal Ray'),
  ('48mの魔力射線で6秒拘束、5秒間の術式反射、後方へ転移', 'A 48m mana ray binding 6s; 5s spell reflection; blink back'),
  [fx('portal', 60, 'line', r=48), line(48, 3), dmg(1.6), stun(120), reflect(100, 16), back(6)],
  [me(), reflect(25, 6)], ('所持中：術式反射', 'Held: spell reflection'),
  [chain(3, 8), dmg(0.3)], ('命中時：魔弾が3体へ', 'On hit: bolts chain to 3'), hitfx='enchant')
L('merlinus_focus', 2, 'arcane', ('時間凍結', 'Time Freeze'),
  ('32m内の時間を凍結：15秒拘束・凍結、飛び道具消去、自身は神速IV', 'Freeze time within 32m for 15s; erase projectiles; speed IV'),
  [area(32), stun(300), freeze(300), erase(32), me(), buff('speed', 300, 3)],
  [me(), buff('night', 300), buff('haste', 40, 1)], ('所持中：暗視・加速', 'Held: night vision, haste'))
L('merlinus_charm', 1, 'arcane', ('空間折り畳み', 'Space Fold'),
  ('20m先へ空間を折り畳んで転移、1.5秒無敵', 'Fold space and blink 20m; 1.5s guard'),
  [blink(20), me(), guard(30)],
  [me(), reflect(25, 8)], ('所持中：術式反射', 'Held: spell reflection'))
L('merlinus_legend', 3, 'arcane', ('魔導真理・知の深淵', 'Abyss of Knowledge'),
  ('世界の解釈を書き換える：48m内の時間停止20秒・凍結・強化剥奪・極大打撃、64mの射線、20秒の万物反射', 'Rewrite the world: 48m stop 20s, freeze, strip, smite; 64m ray; 20s reflection'),
  [area(48), stun(400), freeze(400), dmg(2.5), strip(), line(64, 4), dmg(2.0), reflect(400, 48), erase(64), me(), guard(100)],
  LP + [reflect(25, 12)], ('所持中：魔導の深淵', 'Held: arcane abyss'),
  [chain(6, 12), dmg(0.5)], ('命中時：魔弾が6体へ', 'On hit: bolts chain to 6'), hitfx='enchant')

# 19 enkou --------------------------------------------------------------------------------------------------
L('enkou_weapon', 1, 'abyss', ('深淵圧壊', 'Abyssal Crush'),
  ('16m内に深海の圧力：叩き潰し、暗闇・毒IV、海流で引き寄せる', 'Deep-sea pressure within 16m: crush, darkness, poison IV, currents pull'),
  [area(16), dmg(1.5), slam(3.0), eff('dark', 300), eff('poison', 300, 3), pull(2.0), me(), buff('water', 600), buff('dolphin', 300, 1)],
  [me(), buff('water', 300), buff('dolphin', 40, 1), buff('night', 300)], ('所持中：深海の住人', 'Held: deep-sea dweller'),
  [victim(), eff('poison', 80, 2), eff('slow', 60, 1)], ('命中時：毒牙', 'On hit: venom fang'), hitfx='bubble')
L('enkou_focus', 2, 'abyss', ('深海圧力', 'Deep Pressure'),
  ('24m内を海底の重圧で押し潰す：10秒拘束・鈍足VII・暗闇、雨を呼ぶ', 'Crush 24m with seabed pressure: bind 10s, slow VII, darkness; summon rain'),
  [o('weather', w='rain'), area(24), slam(4.0), stun(200), eff('slow', 400, 6), eff('dark', 400)],
  [me(), buff('water', 300)], ('所持中：水中呼吸', 'Held: water breathing'))
L('enkou_charm', 1, 'abyss', ('黒曜海鱗', 'Obsidian Scales'),
  ('4秒無敵・20秒適応・耐性V', '4s guard, 20s adaptation, resistance V'),
  [me(), guard(80), buff('resist', 400, 4), adapt(400)],
  [me(), buff('resist', 40, 1), buff('water', 300)], ('所持中：海鱗の守り', 'Held: scale guard'))
L('enkou_legend', 3, 'abyss', ('海獣災極・深淵咆哮', 'Abyssal Roar'),
  ('48m内に深淵の咆哮：極大打撃・叩き潰し・15秒拘束・暗闇・毒X・盲目、海流で引き寄せ、嵐を呼ぶ', 'An abyssal roar across 48m; storm'),
  [o('weather', w='thunder'), area(48), dmg(2.5), slam(5.0), stun(300), eff('dark', 600), eff('poison', 600, 9), eff('blind', 200), pull(3.0)],
  LP + [buff('water', 300), buff('dolphin', 40, 2)], ('所持中：海の災厄', 'Held: calamity of the sea'),
  [victim(), eff('poison', 100, 4), eff('dark', 60)], ('命中時：深淵の毒', 'On hit: abyssal venom'), hitfx='bubble')

# 20 kurma --------------------------------------------------------------------------------------------------
L('kurma_weapon', 1, 'earth', ('地裂震撃', 'Earthsplitter'),
  ('20m内に地震：打ち上げ・大打撃・5秒拘束、自身耐性IV', 'Quake within 20m: launch, smite, bind 5s; resistance IV'),
  [area(20), dmg(1.6), launch(1.8), stun(100), me(), buff('resist', 300, 3)],
  [me(), buff('resist', 40, 0), buff('absorb', 40, 1)], ('所持中：岩の守り', 'Held: rock guard'),
  [around(4), dmg(0.3), launch(0.8)], ('命中時：小地震', 'On hit: tremor'), hitfx='compost')
L('kurma_focus', 2, 'earth', ('地鎮', 'Earth Calming'),
  ('24m内の味方を全快・吸収VII・耐性IV、豊穣のパン16', 'Allies: full heal, absorption VII, resistance IV; 16 bread'),
  [allies(24), healpct(1.0, True), buff('absorb', 600, 6, True), buff('resist', 600, 3, True), give('bread', 16), xp(40)],
  [allies(12), buff('regen', 40, 0, True)], ('所持中：霊脈の恵み', 'Held: ley blessing'))
L('kurma_charm', 1, 'earth', ('山脈甲殻', 'Mountain Shell'),
  ('5秒無敵・耐性V・吸収IX', '5s guard, resistance V, absorption IX'),
  [me(), guard(100), buff('resist', 600, 4), buff('absorb', 600, 8)],
  [me(), buff('resist', 40, 2)], ('所持中：耐性III', 'Held: resistance III'))
L('kurma_legend', 3, 'earth', ('地龍世界・大陸の心臓', 'Heart of the Continent'),
  ('48m内の大地を隆起：極大打撃・打ち上げ・15秒拘束。味方全快＋吸収X、自身5秒無敵、鉱脈からダイヤ4', 'Raise the land within 48m; allies restored; diamonds from the veins'),
  [area(48), dmg(2.5), launch(3.0), stun(300), allies(32), healpct(1.0, True), buff('absorb', 1200, 9, True), me(), guard(100),
   buff('resist', 1200, 4), give('diamond', 4)],
  LP + [buff('absorb', 40, 4)], ('所持中：大陸の加護', 'Held: continental aegis'),
  [around(5), dmg(0.4), launch(1.0)], ('命中時：地震', 'On hit: quake'), hitfx='compost')

# 21 teia ---------------------------------------------------------------------------------------------------
L('teia_weapon', 1, 'light', ('天裂光矢', 'Sky-Rending Arrow'),
  ('64mの光の矢で貫き炎上、命中した敵に光矢の雨。飛び道具を消去し10m先へ光速移動', 'A 64m arrow of light, arrow rain on the hit; erase projectiles; light-speed step'),
  [line(64, 2), dmg(1.8), burn(4), arrows(4, 30), erase(24), blink(10)],
  [me(), buff('speed', 40, 2), reflect(25, 6)], ('所持中：神速・迎撃', 'Held: godspeed, intercept'),
  [chain(3, 10), dmg(0.3)], ('命中時：光跡が3体へ', 'On hit: light trails to 3'), hitfx='firework')
L('teia_focus', 2, 'light', ('光越推進', 'Light Drive'),
  ('前方へ超加速突進、神速VI・跳躍IV、1秒無敵', 'Hyper dash forward; speed VI, jump IV; 1s guard'),
  [dash(4.5), me(), buff('speed', 300, 5), buff('jump', 300, 3), guard(20)],
  [me(), buff('speed', 40, 1), buff('jump', 40, 1)], ('所持中：俊足・跳躍', 'Held: speed, leap'))
L('teia_charm', 1, 'light', ('因果越速', 'Beyond Causality'),
  ('32m内の飛び道具を消去し、10秒間すべて撃ち返す', 'Erase projectiles within 32m and reflect all for 10s'),
  [erase(32), reflect(200, 16)],
  [me(), buff('slowfall', 40), buff('speed', 40, 0)], ('所持中：羽の加護', 'Held: feather'))
L('teia_legend', 3, 'light', ('超光翔空・天裂の神矢', 'Divine Arrow'),
  ('128mの神矢：極大打撃・焼却。48m内に光矢の豪雨と落雷、飛び道具消滅、24m先へ光速移動', 'A 128m divine arrow; light storm across 48m; light-speed step'),
  [fx('end_rod', 120, 'line', r=128), line(128, 4), dmg(3.0), burn(10), area(48), arrows(10, 60), lightning(), dmg(1.5), erase(64),
   blink(24), me(), buff('speed', 600, 5)],
  LP + [buff('speed', 40, 3), reflect(25, 10)], ('所持中：光越の龍', 'Held: lightspeed dragon'),
  [chain(5, 12), dmg(0.5)], ('命中時：光跡が5体へ', 'On hit: light trails to 5'), hitfx='firework')

# 22 bahamut ------------------------------------------------------------------------------------------------
L('bahamut_weapon', 1, 'tide', ('潮流衝撃', 'Tidal Impact'),
  ('前方20mに大潮流：大打撃・吹き飛ばし。味方を回復・浄化し雨を呼ぶ', 'A great tide ahead: smite and blast; heal and cleanse allies; rain'),
  [o('weather', w='rain'), cone(20, 120), dmg(1.4), knock(4.0), allies(20), healpct(0.6, True), cleanse(True), me(), buff('water', 600), buff('dolphin', 300, 1)],
  [me(), buff('water', 300), buff('dolphin', 40, 1), buff('regen', 40, 0)], ('所持中：海の恵み', 'Held: sea\'s grace'),
  [victim(), knock(2.0)], ('命中時：潮の押し返し', 'On hit: tidal push'), hitfx='splash')
L('bahamut_focus', 2, 'tide', ('海洋循環', 'Ocean Circulation'),
  ('32m内の味方を全快・浄化・再生IV・水中呼吸', 'Allies within 32m: full heal, cleanse, regeneration IV, water breathing'),
  [allies(32), healpct(1.0, True), cleanse(True), buff('regen', 600, 3, True), buff('water', 1200, 0, True)],
  [allies(16), buff('regen', 40, 0, True)], ('所持中：味方を再生', 'Held: allies regenerate'))
L('bahamut_charm', 1, 'tide', ('調停の潮', 'Tide of Mediation'),
  ('20m内の敵を潮で押し流し鈍足、自身浄化', 'Wash foes within 20m away and slow them; cleanse self'),
  [area(20), knock(3.0), eff('slow', 200, 3), me(), cleanse()],
  [me(), buff('water', 300), buff('dolphin', 40, 2)], ('所持中：海の加護', 'Held: sea aegis'))
L('bahamut_legend', 3, 'tide', ('海理皇権・世界潮歌', 'World Tide Song'),
  ('48m内に世界の潮歌：敵を打ち上げ押し流し極大打撃。味方全快・浄化・再生V・20秒不死', 'The world\'s tide song across 48m; allies restored and undying'),
  [o('weather', w='rain'), area(48), dmg(2.5), launch(2.0), knock(6.0), allies(48), healpct(1.0, True), cleanse(True),
   buff('regen', 1200, 4, True), undying(400, True)],
  LP + [allies(16), buff('regen', 40, 1, True), buff('water', 300)], ('所持中：海皇の加護', 'Held: sea emperor aegis'),
  [victim(), knock(3.0)], ('命中時：大潮の押し返し', 'On hit: great tide push'), hitfx='splash')

# 23 nun ----------------------------------------------------------------------------------------------------
L('nun_weapon', 1, 'mask', ('千面変化', 'Thousand Faces'),
  ('16m内の敵の強化を写し取り（奪い）、大打撃。15秒適応', 'Copy (steal) the buffs of foes within 16m, smite; 15s adaptation'),
  [area(16), strip(True), dmg(1.2), me(), adapt(300)],
  [me(), adapt(40)], ('所持中：相手に合わせて変化（適応）', 'Held: adapts to any attack'),
  [victim(), strip(True)], ('命中時：強化を写し取る', 'On hit: copy buffs'), hitfx='smoke')
L('nun_focus', 2, 'mask', ('仮面変化', 'Mask Swap'),
  ('透明化・神速IV、最寄りの敵と位置を入れ替え、周囲を幻惑', 'Invisible and fast; swap places with the nearest foe; confuse nearby'),
  [me(), buff('invis', 300), buff('speed', 300, 3), near(24, 1), swap(), area(12), eff('nausea', 200)],
  [me(), buff('night', 300)], ('所持中：暗視', 'Held: night vision'))
L('nun_charm', 1, 'mask', ('愚者の旅', 'Fool\'s Journey'),
  ('16m先へ転移、幸運VI、1秒無敵', 'Blink 16m, luck VI, 1s guard'),
  [blink(16), me(), buff('luck', 600, 5), guard(20)],
  [me(), buff('luck', 40, 2), buff('speed', 40, 0)], ('所持中：幸運・俊足', 'Held: luck, speed'))
L('nun_legend', 3, 'mask', ('存在万化・無限の仮面', 'Infinite Masks'),
  ('40m内の敵の強化を奪い、一体ずつ無作為の姿へ変える（極大打撃・停止・打ち上げ・凍結）。60秒適応・30秒不死・剛力X', 'Steal buffs within 40m and reshape each foe at random; adaptation, undying, strength X'),
  [area(40), strip(True), each([dmg(2.5), stun(300), launch(3.0), freeze(400)]), me(), adapt(1200), undying(600), buff('strength', 600, 9)],
  LP + [adapt(40)], ('所持中：万化の王', 'Held: king of change'),
  [victim(), strip(True), dmg(0.3)], ('命中時：強化を奪い打撃', 'On hit: steal and strike'), hitfx='smoke')

# 24 arcana -------------------------------------------------------------------------------------------------
L('arcana_weapon', 1, 'fate', ('因果結び', 'Knot of Causality'),
  ('因果の糸を8体へ結び大打撃・被ダメ2倍の刻印、幸運VI、5秒間の攻撃反転', 'Tie fate to 8 foes: smite, mark x2; luck VI; 5s of reversal'),
  [chain(8, 12), dmg(1.2), mark(300, 2.0), me(), buff('luck', 600, 5), reflect(100, 16)],
  [me(), buff('luck', 40, 3), reflect(25, 5)], ('所持中：幸運・攻撃反転', 'Held: luck, reversal'),
  [chance(0.35, [victim(), dmg(1.0)])], ('命中時：35%で会心の幸運', 'On hit: 35% lucky critical'), hitfx='end_rod')
L('arcana_focus', 2, 'fate', ('最善の未来', 'Best Future'),
  ('32m内の味方を全快・30秒不死・幸運VI・吸収V（倒れる未来を排除）', 'Allies: full heal, 30s undying, luck, absorption'),
  [allies(32), healpct(1.0, True), undying(600, True), buff('luck', 1200, 5, True), buff('absorb', 600, 4, True)],
  [allies(12), buff('luck', 40, 1, True)], ('所持中：味方に幸運', 'Held: allies are lucky'))
L('arcana_charm', 1, 'fate', ('奇跡', 'Miracle'),
  ('60秒不死・3秒無敵・浄化', '60s undying, 3s guard, cleanse'),
  [me(), undying(1200), guard(60), cleanse()],
  [me(), buff('luck', 40, 4)], ('所持中：幸運V', 'Held: luck V'))
L('arcana_legend', 3, 'fate', ('最善終章・運命再編', 'Fate Rewritten'),
  ('48m内の味方に60秒不死・全快・5秒無敵。敵は強化剥奪・極大打撃・被ダメ3倍、20秒間すべての攻撃を反転', 'Allies undying and healed; foes stripped, smitten and marked; 20s reversal'),
  [allies(48), undying(1200, True), healpct(1.0, True), guard(100, True), area(48), strip(), dmg(2.5), mark(600, 3.0), reflect(400, 48)],
  LP + [buff('luck', 40, 5), reflect(25, 8)], ('所持中：運命の天使', 'Held: angel of fate'),
  [chance(0.5, [victim(), dmg(1.5)])], ('命中時：50%で会心', 'On hit: 50% critical'), hitfx='end_rod')

# 25 eomaia -------------------------------------------------------------------------------------------------
L('eomaia_weapon', 1, 'beast', ('始祖の咆哮', 'Primal Roar'),
  ('獣群（狼4体）を招き、前方14mを薙ぎ吹き飛ばす。自身と味方に剛力・俊足', 'Call 4 wolves, sweep ahead; strength and speed to self and allies'),
  [summon('wolf', 4), cone(14, 140), dmg(1.4), knock(2.0), me(), buff('strength', 300, 4), buff('speed', 300, 2),
   allies(24), buff('strength', 300, 3, True)],
  [me(), buff('speed', 40, 0), buff('night', 300)], ('所持中：獣の感覚', 'Held: beast senses'),
  [around(3), dmg(0.25)], ('命中時：獣性の連撃', 'On hit: feral flurry'), hitfx='crit')
L('eomaia_focus', 2, 'beast', ('獣群招来', 'Pack Call'),
  ('狼6体を招き、24m内の味方に剛力V・俊足III・再生III', 'Call 6 wolves; strength V, speed III, regeneration III to allies'),
  [summon('wolf', 6), allies(24), buff('strength', 600, 4, True), buff('speed', 600, 2, True), buff('regen', 600, 2, True)],
  [allies(12), buff('speed', 40, 0, True)], ('所持中：群れの俊足', 'Held: pack speed'))
L('eomaia_charm', 1, 'beast', ('獣性解放', 'Feral Release'),
  ('剛力VII・神速IV・跳躍III（20秒）', 'Strength VII, speed IV, jump III'),
  [me(), buff('strength', 400, 6), buff('speed', 400, 3), buff('jump', 400, 2)],
  [me(), buff('jump', 40, 1), buff('speed', 40, 0), buff('night', 300)], ('所持中：獣の脚', 'Held: beast legs'))
L('eomaia_legend', 3, 'beast', ('原初獣王・全獣の血脈', 'Bloodline of All Beasts'),
  ('狼6体、40m内の敵に極大打撃・拘束・吹き飛ばし。40m内の味方に剛力IX・俊足・再生、自身20秒不死', '6 wolves; smite 40m; allies empowered; 20s undying'),
  [summon('wolf', 6), area(40), dmg(2.5), stun(160), knock(3.0), allies(40), buff('strength', 1200, 8, True), buff('speed', 1200, 2, True),
   buff('regen', 1200, 2, True), me(), undying(400)],
  LP + [allies(16), buff('strength', 40, 2, True)], ('所持中：獣王の鼓舞', 'Held: beast king\'s rally'),
  [victim(), dmg(0.3), dmg(0.3)], ('命中時：獣の二連撃', 'On hit: double rend'), hitfx='crit')

# 26 demiurgos ----------------------------------------------------------------------------------------------
L('demiurgos_weapon', 1, 'dream', ('空想顕現', 'Imagination Made Real'),
  ('想像の眷属（ゴーレム2体）を顕現、32mを斬り体力25%以下の存在を断絶、10m先へ空間移動', 'Manifest 2 golems; cut 32m, sever anything below 25%; spatial step'),
  [summon('golem', 2), line(32, 3), dmg(1.6), execute(0.25), blink(10)],
  [me(), buff('absorb', 40, 1)], ('所持中：吸収', 'Held: absorption'),
  [victim(), execute(0.12)], ('命中時：12%以下を断絶', 'On hit: sever below 12%'), hitfx='dragon')
L('demiurgos_focus', 2, 'dream', ('理想定着', 'Ideal Fixation'),
  ('5秒無敵・吸収IX、味方に3秒無敵、ゴーレム3体', '5s guard, absorption IX, allies 3s guard, 3 golems'),
  [me(), guard(100), buff('absorb', 800, 8), allies(24), guard(60, True), summon('golem', 3)],
  [me(), buff('absorb', 40, 2)], ('所持中：吸収III', 'Held: absorption III'))
L('demiurgos_charm', 1, 'dream', ('龍鱗障壁', 'Dragon-Scale Barrier'),
  ('10秒間すべての飛び道具を反射、32m内の飛び道具消去、耐性V', 'Reflect all projectiles for 10s, erase within 32m, resistance V'),
  [reflect(200, 20), erase(32), me(), buff('resist', 400, 4)],
  [me(), reflect(25, 6)], ('所持中：飛び道具反射', 'Held: reflects projectiles'))
L('demiurgos_legend', 3, 'dream', ('空創龍権・万物創現', 'Genesis of All'),
  ('48m内の存在を断絶（60%以下）・極大打撃・拘束、ゴーレム6体、60秒不死・5秒無敵、20m空間移動', 'Sever within 48m below 60%; 6 golems; undying; spatial step'),
  [area(48), execute(0.6), dmg(3.0), stun(200), summon('golem', 6), me(), undying(1200), guard(100), blink(20)],
  LP + [reflect(25, 8)], ('所持中：空創の龍王', 'Held: dragon of creation'),
  [victim(), execute(0.3)], ('命中時：30%以下を断絶', 'On hit: sever below 30%'), hitfx='dragon')

# 27 hakyoku ------------------------------------------------------------------------------------------------
L('hakyoku_weapon', 1, 'evolve', ('捕食砲', 'Predation Cannon'),
  ('40mの捕食砲：極大打撃、強化を喰らい奪い、30%以下を捕食。自身回復・30秒適応', 'A 40m predation beam: devour buffs, consume below 30%; heal and adapt'),
  [fx('lava', 30, 'line', r=40), line(40, 3), dmg(1.8), strip(True), execute(0.3), me(), healpct(0.4), adapt(600)],
  [me(), adapt(40)], ('所持中：永久適応', 'Held: perpetual adaptation'),
  [victim(), strip(True), me(), heal(6)], ('命中時：強化を喰らい回復', 'On hit: devour and heal'), hitfx='lava')
L('hakyoku_focus', 2, 'evolve', ('無窮進化', 'Endless Evolution'),
  ('60秒適応・剛力VII・耐性IV・体力増強V・全快', '60s adaptation, strength VII, resistance IV, health boost V, full heal'),
  [me(), adapt(1200), buff('strength', 600, 6), buff('resist', 600, 3), buff('health', 1200, 4), healpct(1.0)],
  [me(), adapt(40), buff('regen', 40, 0)], ('所持中：適応・再生', 'Held: adaptation, regeneration'))
L('hakyoku_charm', 1, 'evolve', ('死生反転', 'Life-Death Reversal'),
  ('60秒不死・全快・浄化（死を取り消す）', '60s undying, full heal, cleanse'),
  [me(), undying(1200), healpct(1.0), cleanse()],
  [low(0.3, [me(), undying(40)])], ('所持中：体力30%以下で死なない', 'Held: cannot die below 30% health'))
L('hakyoku_legend', 3, 'evolve', ('討伐不能・無窮の覇核', 'Undefeatable Core'),
  ('48m内の敵の強化を喰らい極大打撃、50%以下を捕食。120秒不死・120秒適応・全快・剛力XIII', 'Devour within 48m, consume below 50%; 120s undying and adaptation'),
  [area(48), strip(True), dmg(3.0), execute(0.5), me(), undying(2400), adapt(2400), healpct(1.0), buff('strength', 1200, 12)],
  LP + [adapt(40), low(0.4, [me(), undying(40)])], ('所持中：討伐不能', 'Held: cannot be defeated'),
  [victim(), strip(True), execute(0.25)], ('命中時：喰らい・捕食', 'On hit: devour'), hitfx='lava')

# 28 shinra -------------------------------------------------------------------------------------------------
L('shinra_weapon', 1, 'hunt', ('天敵解析', 'Natural Enemy Analysis'),
  ('24m内の敵を解析：発光・強化剥奪・30秒間被ダメ3倍。自身30秒適応', 'Analyze foes within 24m: glow, strip, take x3 damage for 30s; adapt'),
  [area(24), mark(600, 3.0), eff('glow', 600), strip(), me(), adapt(600)],
  [me(), adapt(40), buff('night', 300)], ('所持中：適応・暗視', 'Held: adaptation, night vision'),
  [victim(), mark(200, 2.0)], ('命中時：弱点を解析（被ダメ2倍）', 'On hit: weakness found (x2)'), hitfx='crit')
L('shinra_focus', 2, 'hunt', ('存在狩猟', 'Existence Hunt'),
  ('48m内の最も近い敵の背後へ跳び、被ダメ4倍の刻印・極大打撃・35%以下を狩り取る', 'Leap behind the nearest foe within 48m: mark x4, smite, hunt below 35%'),
  [near(48, 1), behind(), mark(600, 4.0), dmg(2.0), execute(0.35)],
  [me(), buff('night', 300), buff('speed', 40, 0)], ('所持中：狩人の眼', 'Held: hunter\'s eye'))
L('shinra_charm', 1, 'hunt', ('無敵喰らい', 'Invincibility Eater'),
  ('20m内の敵の強化・守りを喰い破り大打撃、自身2秒無敵', 'Eat through defenses within 20m and smite; 2s guard'),
  [area(20), strip(), dmg(1.2), me(), guard(40)],
  [me(), adapt(40)], ('所持中：適応', 'Held: adaptation'))
L('shinra_legend', 3, 'hunt', ('終焉例外・万物天敵', 'Enemy of All Things'),
  ('48m内の万物を天敵として解析：強化剥奪・60秒被ダメ5倍・極大打撃・50%以下を狩る。120秒適応・30秒不死', 'Analyze all within 48m: strip, x5 damage, smite, hunt below 50%'),
  [area(48), strip(), mark(1200, 5.0), dmg(3.0), execute(0.5), me(), adapt(2400), undying(600)],
  LP + [adapt(40)], ('所持中：万物の天敵', 'Held: enemy of all'),
  [victim(), mark(200, 3.0), execute(0.25)], ('命中時：被ダメ3倍・25%以下を狩る', 'On hit: x3 and hunt below 25%'), hitfx='crit')

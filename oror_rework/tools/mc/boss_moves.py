"""Move sets and movement styles of the 41 characters (BossMoves.java, v0.17.7).

Every character has five moves from a shared library of 24 multi-tick techniques, each with a name of its own taken
from the character's lore, and a movement style that decides how it closes in, keeps its distance, side-steps,
leaps or blinks between moves. Writes assets/oror_supreme_bosses/boss_moves.json and the move names into
lang/ja_jp.json + lang/en_us.json (boss_move.<ns>.<character>.<move>).
Usage: python3 -I boss_moves.py <overlay assets dir>"""
import json, os, sys

NS = 'oror_supreme_bosses'

# move id -> English name (the Japanese names are per character below)
MOVES = {
    'dash_slash': 'Flash Cut', 'blink_strike': 'Blink Strike', 'combo_rush': 'Combo Rush', 'spin_slash': 'Whirlwind',
    'blade_wave': 'Blade Waves', 'leap_slam': 'Leaping Slam', 'uppercut': 'Rising Strike', 'ground_spikes': 'Earth Rend',
    'nova': 'Nova', 'vortex': 'Vortex', 'meteor': 'Meteor Shower', 'beam': 'Beam', 'homing_orbs': 'Homing Orbs',
    'arrow_rain': 'Arrow Rain', 'bolt_barrage': 'Bolt Barrage', 'bullet_storm': 'Bullet Storm',
    'shell_barrage': 'Shell Barrage', 'barrier': 'Barrier', 'chain_pull': 'Chain Pull', 'reap': 'Reaping Dance',
    'ricochet': 'Ricochet', 'afterimage': 'Afterimages', 'charge': 'Charge', 'breath': 'Breath',
}

# movement styles: duelist (dash in / back-step / side-step), brawler (leaps in, rushes), caster (keeps 8-14 blocks,
# blinks away when cornered), gunner (keeps distance, strafes), juggernaut (leaps in, never backs off),
# guardian (steady advance, side-steps), flyer (swoops), swimmer (darts), trickster (blinks around), rooted (never moves)
STYLES = {'duelist', 'brawler', 'caster', 'gunner', 'juggernaut', 'guardian', 'flyer', 'swimmer', 'trickster', 'rooted'}

CHARACTERS = {
    'kokuhaku': ('duelist', [('dash_slash', '抜刀転移・瞬閃'), ('blink_strike', '背面一閃'), ('blade_wave', '蒼白直線斬'), ('afterimage', '残像千刃'), ('combo_rush', '無音連斬')]),
    'riha': ('caster', [('bolt_barrage', '言霊「射貫け」'), ('vortex', '言霊「来い」'), ('nova', '言霊「退け」'), ('meteor', '言霊「堕ちろ」'), ('homing_orbs', '言霊「追え」')]),
    'tenki': ('juggernaut', [('leap_slam', '王威降臨'), ('blade_wave', '王剣両断'), ('spin_slash', '万象薙ぎ'), ('nova', '跪けの波動'), ('charge', '王の進軍')]),
    'chaos': ('trickster', [('homing_orbs', '混沌核弾'), ('vortex', '異常重力'), ('meteor', '虹核崩落'), ('nova', '変質波'), ('afterimage', '混沌転移')]),
    'berit': ('brawler', [('ground_spikes', '錬成棘陣'), ('combo_rush', '錬成拳連打'), ('uppercut', '錬金昇拳'), ('chain_pull', '錬成鎖'), ('leap_slam', '地殻錬成')]),
    'elseria': ('caster', [('beam', '原初の火線'), ('meteor', '星辰流星群'), ('bolt_barrage', '星弾'), ('nova', '星脈波動'), ('homing_orbs', '星霊弾')]),
    'valeria': ('juggernaut', [('leap_slam', '変形槌・墜撃'), ('ground_spikes', '工房杭打ち'), ('homing_orbs', '作業ドローン突撃'), ('spin_slash', '大槌旋回'), ('uppercut', '打ち上げ槌')]),
    'huang_linghua': ('duelist', [('charge', '龍仙突進'), ('nova', '雷光衝撃'), ('meteor', '天雷招来'), ('spin_slash', '龍尾旋槍'), ('uppercut', '昇龍槍')]),
    'ferdinand': ('gunner', [('bullet_storm', '試作連射砲・全弾'), ('shell_barrage', '試作榴弾'), ('homing_orbs', '追尾ドローン'), ('barrier', '防壁展開'), ('beam', '魔導照射砲')]),
    'mels': ('duelist', [('combo_rush', '流武連撃'), ('afterimage', '無形歩法'), ('spin_slash', '水刃旋舞'), ('chain_pull', '粘体拘束'), ('charge', '水流突き')]),
    'hephaistos': ('guardian', [('beam', '切削光線'), ('homing_orbs', '迎撃ドローン'), ('charge', '切削突撃'), ('ground_spikes', '工廠杭'), ('barrier', '反射障壁')]),
    'nortia': ('trickster', [('leap_slam', 'ピコピコ大跳躍'), ('uppercut', '場外ホームラン'), ('afterimage', '鬼ごっこ'), ('meteor', 'おもちゃの雨'), ('nova', '赤信号')]),
    'lucifara': ('duelist', [('reap', '魂宴の円舞'), ('blink_strike', '堕天の囁き'), ('vortex', '欲望の渦'), ('dash_slash', '失楽一閃'), ('homing_orbs', '魅惑の魂火')]),
    'taika': ('brawler', [('combo_rush', '超克連打'), ('uppercut', '覇王昇拳'), ('leap_slam', '覇王墜撃'), ('nova', '超克衝撃波'), ('charge', '覇道突進')]),
    'mary_sue': ('caster', [('bolt_barrage', '英雄譚・第一章'), ('beam', '主人公補正'), ('meteor', '最終章の流星'), ('barrier', '覚醒の加護'), ('homing_orbs', '伏線回収')]),
    'savior': ('guardian', [('barrier', '救世結界'), ('charge', '聖盾突進'), ('nova', '聖光波'), ('leap_slam', '聖盾墜撃'), ('chain_pull', '救済の鎖')]),
    'gokuka': ('brawler', [('combo_rush', '呪爪連撃'), ('reap', '呪禍旋風'), ('homing_orbs', '分御霊'), ('vortex', '呪詛の渦'), ('blink_strike', '外法背襲')]),
    'merlinus': ('caster', [('beam', '魔力射線'), ('afterimage', '転移乱舞'), ('homing_orbs', '深淵魔弾'), ('vortex', '時間拘束陣'), ('barrier', '反射術式')]),
    'enkou': ('swimmer', [('charge', '災牙突進'), ('vortex', '深海渦流'), ('beam', '高圧水牙'), ('ground_spikes', '水圧柱'), ('spin_slash', '三叉旋撃')]),
    'kurma': ('juggernaut', [('leap_slam', '大陸墜撃'), ('ground_spikes', '地脈隆起'), ('nova', '大地震'), ('meteor', '岩塊落とし'), ('barrier', '甲羅の守り')]),
    'teia': ('flyer', [('arrow_rain', '天裂の矢雨'), ('breath', '光ブレス'), ('dash_slash', '残光突進'), ('bolt_barrage', '光矢連射'), ('afterimage', '光速移動')]),
    'bahamut': ('swimmer', [('beam', '高圧水流'), ('nova', '潮の大波'), ('vortex', '大渦潮'), ('barrier', '潮の防壁'), ('meteor', '鯨の雨')]),
    'nun': ('trickster', [('afterimage', '千面変化'), ('breath', '龍の息吹'), ('combo_rush', '獣の連撃'), ('homing_orbs', '道化の弾'), ('uppercut', '跳ね道化')]),
    'arcana': ('caster', [('homing_orbs', '運命の糸'), ('barrier', '救命の加護'), ('bolt_barrage', '幸運弾'), ('vortex', '運命の渦'), ('nova', '軌道反転')]),
    'eomaia': ('brawler', [('charge', '始祖の猛進'), ('nova', '咆哮'), ('combo_rush', '獣牙連撃'), ('leap_slam', '獣王跳撃'), ('chain_pull', '群れの包囲')]),
    'demiurgos': ('flyer', [('breath', '破壊のブレス'), ('meteor', '空想流星'), ('leap_slam', '黒龍墜撃'), ('beam', '存在断絶の光'), ('blade_wave', '黒龍剣閃')]),
    'hakyoku': ('gunner', [('shell_barrage', '捕食砲・連射'), ('beam', '覇帝の砲光'), ('charge', '暴食突進'), ('nova', '進化の衝撃'), ('leap_slam', '覇帝墜撃')]),
    'shinra': ('duelist', [('combo_rush', '天敵連突'), ('blink_strike', '日傘の影'), ('afterimage', '紅月歩'), ('beam', '存在狩りの光'), ('dash_slash', '天敵一閃')]),
    'ain_sof_aur': ('trickster', [('afterimage', '分岐転移'), ('blade_wave', '分岐確定斬'), ('blink_strike', '並行世界の一撃'), ('homing_orbs', '別世界の眷属弾'), ('nova', '全界選択')]),
    'angra_mainyu': ('duelist', [('chain_pull', '影鎖'), ('reap', '全害の鎌'), ('vortex', '悪意の渦'), ('nova', '暗黒衝撃'), ('homing_orbs', '呪詛弾')]),
    'magna_mater': ('guardian', [('chain_pull', '蔓の拘束'), ('ground_spikes', '根の槍'), ('barrier', '母胎の守り'), ('vortex', '生命の渦'), ('homing_orbs', '種子弾')]),
    'ouroboros': ('trickster', [('ricochet', '円環輪刃'), ('afterimage', '巻戻し'), ('vortex', '循環拘束'), ('spin_slash', '無限円舞'), ('homing_orbs', '輪廻の輪')]),
    'yggdrasil': ('rooted', [('ground_spikes', '根の槍'), ('barrier', '神樹の守り'), ('homing_orbs', '精霊弾'), ('vortex', '根の拘束'), ('meteor', '神樹の実')]),
    'miyohime': ('trickster', [('vortex', '重力反転'), ('meteor', '神楽の流星'), ('nova', '時の波紋'), ('afterimage', '万律自在'), ('beam', '神璽の光')]),
    'innocence': ('trickster', [('homing_orbs', 'ぬいぐるみ行進'), ('uppercut', '高い高い'), ('meteor', 'おもちゃ箱'), ('vortex', '遊び場'), ('nova', 'なかったことに')]),
    'brutality': ('brawler', [('combo_rush', '暴虐連撃'), ('leap_slam', '鬼金棒墜撃'), ('charge', '暴走突進'), ('uppercut', '打ち上げ'), ('spin_slash', '大旋回')]),
    'cursed_love': ('caster', [('chain_pull', '操り糸'), ('homing_orbs', '悲劇の人形'), ('vortex', '呪愛の渦'), ('nova', '終幕の波動'), ('bolt_barrage', '呪詛弾')]),
    'relentless_research': ('duelist', [('combo_rush', '治験連突'), ('homing_orbs', '異常生命体'), ('chain_pull', '実験拘束'), ('blink_strike', '注射'), ('vortex', '隔離区画')]),
    'forbidden_arcana': ('caster', [('chain_pull', '鎖刃拘束'), ('beam', '禁術射線'), ('homing_orbs', '術式弾'), ('ricochet', '鎖刃乱舞'), ('meteor', '外悪の雨')]),
    'fallen_savior': ('duelist', [('blade_wave', '神殺しの聖剣閃'), ('leap_slam', '堕天の審判'), ('dash_slash', '救堕一閃'), ('nova', '浄化の光'), ('combo_rush', '無限再起の連斬')]),
    'sweet_pact': ('trickster', [('homing_orbs', '債権弾'), ('vortex', '取り立て'), ('barrier', '救済契約'), ('nova', '未来差押え'), ('blink_strike', '契約の影')]),
}


def write(assets):
    roster = json.load(open(os.path.join(assets, 'characters.json'), encoding='utf-8'))
    ids = sorted(c['id'] for c in roster)
    assert sorted(CHARACTERS) == ids, set(ids) ^ set(CHARACTERS)
    out = {}
    for cid, (style, moves) in CHARACTERS.items():
        assert style in STYLES, cid
        assert len(moves) == 5 and len({m for m, _ in moves}) == 5, cid
        for m, _ in moves:
            assert m in MOVES, (cid, m)
        out[cid] = {'style': style, 'moves': [m for m, _ in moves]}
    used = {m for _, ms in CHARACTERS.values() for m, _ in ms}
    with open(os.path.join(assets, 'boss_moves.json'), 'w', encoding='utf-8') as fh:
        json.dump({'characters': out}, fh, ensure_ascii=False, indent=1)
    for lang, li in (('ja_jp', 0), ('en_us', 1)):
        path = os.path.join(assets, 'lang', lang + '.json')
        L = json.load(open(path, encoding='utf-8'))
        for cid, (style, moves) in CHARACTERS.items():
            for m, ja in moves:
                L[f'boss_move.{NS}.{cid}.{m}'] = ja if li == 0 else MOVES[m]
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(L, fh, ensure_ascii=False, indent=1)
    print('characters', len(out), 'moves used', len(used), 'of', len(MOVES), 'unused', sorted(set(MOVES) - used))


if __name__ == '__main__':
    write(sys.argv[1])

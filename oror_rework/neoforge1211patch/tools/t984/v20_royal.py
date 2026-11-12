"""(059c) The Villager King's 64 new actions (03_king_4_forms.md: 8 of his first form, 18 of the hero king's, 16 of the
broken king's, 22 of Baal Zebul's) and Azazel's 41 (04_azazel.md: 14 + 21 for his second and third forms, 6 at the
king's side), read into techniques of the 984's kind (build_waza.py's input), so that the same engine runs them.

Usage: v20_royal.py <03_king_4_forms.md> <04_azazel.md> <out.json>
       v20_royal.py finish <out.json> <build_waza's waza984.json> <its waza_motions.bin> <assets waza dir>
       (the table as the mod reads it: waza_royal.json, each action's verbs read from what it does, its V20 weight
       last; waza_royal_motions.bin)

Each action's own text gives its body's motion (身体動作 / モーション), its reach and hit box (当たり判定 / 判定), what it
does (作用 / 効果 / 特殊効果 / 能力・追加効果), its look and sound and, but for the king's first form, its moments (予兆,
the hits, 復帰, CD; the hero king's 命中時刻 and 仮CD). What it is (a cut, a shot, a guard, a call to arms, a binding, a
field, a heal...) is read from its hit box and effect the way build_waza.py reads the 984's; its reach is the largest
length the hit box names. The king's first form strikes no one (the design: 攻撃ヒットなし): its eight are support.
The "characters" are king1..king4 (his forms) and azazel2, azazel3, azazel_coop.
"""
import json, re, sys

FIELDS = {
    'motion': ['身体動作', 'モーション'],
    'hitbox': ['当たり判定・効果', '当たり判定', '判定'],
    'effect': ['作用', '効果・威力の性質', '効果', '特殊効果', '能力・追加効果'],
    'look': ['エフェクト・音', 'FX・音', '視覚演出・音', 'エフェクト'],
    'timing': ['登録案', '予定発動', '予定tick', '仮CD', 'CD案'],
    'when': ['発動する形態', '条件'],
}
SECTIONS = [  # (character, heading pattern of an action, the part of the document it is in)
    ('king1', r'### \d\d\. (.+?)【V19提案】', '## 第1形態', '## 第2形態'),
    ('king2', r'#### (.+?) \(`(king_phase2_hero_\d+)`\)', '### V19追加：英雄王アルブ専用18技', '## 第3形態'),
    ('king3', r'### 新規：(.+?) \(`(king_phase3_broken_\d+)`\)', '## 第3形態', '## 第4形態'),
    ('king4', r'### 新規：(.+?) \(`(king_phase4_baal_\d+)`\)', '## 第4形態', '## その他の武装60件'),
]
AZ = [
    ('azazel2', r'### (.+?) \(`(azazel_phase2_\d+)`\)', '## 追加設計：アザゼル（拡張第2形態案）', '## 追加設計：アザゼル（拡張第3形態案）'),
    ('azazel3', r'### (.+?) \(`(azazel_phase3_\d+)`\)', '## 追加設計：アザゼル（拡張第3形態案）', '## 対村人王専用連携6技'),
    ('azazel_coop', r'## \d\. (.+?)  `(azazel_coop_\d+)`', '# 村人王との共闘時だけ', '## 協力召喚の既存と改修案'),
]
# what an action is, from its hit box and effect (first match)
BEHAVIOURS = [
    ('HEAL', r'回復|治癒|吸収ハート|癒'),
    ('SUMMON', r'召集|召喚|呼ぶ|呼び|分身|使徒|軍勢|護衛を|衛兵を|兵を'),
    ('GUARD', r'ガード扇|盾で受|軽減|防壁|防御姿勢|被ダメージ軽減|守護|障壁|防ぐ'),
    ('BEAM', r'光線|ビーム|照射|光の柱'),
    ('PROJECTILE', r'飛翔体|射出|投げ|投擲|投射|矢|針|弾|狙撃|射撃|追尾'),
    ('CONTROL', r'拘束|鎖|捕縛|縛|引き寄|掴|拘|綴じ|停止'),
    ('MOVE', r'跳躍|退避|回り込|突進|移動|突入|走行|空中へ|後退'),
    ('FIELD', r'領域|陣|円形|半径\d|範囲|雷雨|天幕|庭|空域|結界'),
    ('MELEE', r'扇|カプセル|直線|掃引|斬|突|薙|打|刺'),
    ('STATUS', r''),
]
SUPPORT_KING1 = {  # the first form's eight, by what they do (the design: no attack hits)
    '御前の制止': 'STATUS', '王城退避指示': 'CONTROL', '王権護衛召集': 'SUMMON', '王冠防護': 'GUARD',
    '歩哨への伝令': 'STATUS', '盾なき退避': 'MOVE', '和平の呼びかけ': 'STATUS', '王城最終警鐘': 'SUMMON',
}


def fields(block):
    out = {}
    for key, names in FIELDS.items():
        for n in names:
            m = re.search(r'\*\*' + re.escape(n) + r'(?:：)?\*\*(?:：)?\s*(.*)', block)
            if m:
                out[key] = m.group(1).strip()
                break
        else:
            out[key] = ''
    return out


def timing(block, f, beh):
    """windup, hits (from the end of the windup), active, recovery, cooldown."""
    text = block
    wu = re.search(r'予兆(?:：)?\s*(\d+)\s*(?:tick)?', text)
    hits = re.search(r'(?:命中予定|ヒット|命中)\s*\[([\d, ]+)\]', text)
    rc = re.search(r'復帰\s*(\d+)', text)
    cd = re.search(r'(?:CD|仮CD|CD案)(?:\*\*)?(?:：)?\s*(\d+)\s*tick|CD(\d+)', text)
    hero = re.search(r'命中時刻([\d・]+)tick', text)
    cdv = int(next(g for g in cd.groups() if g)) if cd else 200
    if hits and wu:
        w = int(wu.group(1))
        hs = [int(x) for x in hits.group(1).split(',')]
        rel = [h - w for h in hs]
        r = int(rc.group(1)) if rc else 14
        return w, rel, max(rel) + 2, r, cdv
    if hero:
        hs = [int(x) for x in hero.group(1).split('・')]
        w = max(6, hs[0] - 6)
        rel = [h - w for h in hs]
        return w, rel, max(rel) + 2, 14, cdv
    # the first form's support and the like: a windup, an act, a recovery
    return 12, [] if beh not in ('MELEE', 'PROJECTILE') else [4], 16, 14, cdv


def reach(f):
    nums = [float(x) for x in re.findall(r'(?:半径|前方|長さ|最大|距離|射程|幅広|扇)\s*(\d+(?:\.\d+)?)', f['hitbox'])]
    nums += [float(x) for x in re.findall(r'(\d+(?:\.\d+)?)\s*(?:m|ブロック)', f['hitbox'])]
    return max(nums) if nums else 6.0


def behaviour(name, ch, f):
    if ch == 'king1':
        return SUPPORT_KING1.get(name, 'STATUS')
    text = f['hitbox'] + '。' + f['effect']
    if re.search(r'攻撃(?:当たり)?判定なし|攻撃ヒットなし', text):
        for b, pat in BEHAVIOURS[:3]:
            if re.search(pat, text):
                return b
        return 'STATUS'
    for b, pat in BEHAVIOURS:
        if pat == '' or re.search(pat, f['hitbox']):
            return b
    return 'STATUS'


def tier(ch, i, n):
    # a form's last few are its great ones
    return 3 if i >= n - 2 else 2 if i >= n - 6 else 1 if i >= n // 3 else 0


def read(doc, sections):
    out = []
    for ch, head, start, end in sections:
        a = doc.index(start)
        b = doc.index(end, a + len(start))
        part = doc[a:b]
        heads = list(re.finditer(head, part))
        for i, m in enumerate(heads):
            block = part[m.end(): heads[i + 1].start() if i + 1 < len(heads) else len(part)]
            name = m.group(1).strip()
            f = fields(block)
            beh = behaviour(name, ch, f)
            wu, hits, ac, rc, cd = timing(block, f, beh)
            pw = re.search(r'(?:仮基準威力|提案の追加威力指定)=(\d+(?:\.\d+)?)', block)
            out.append(dict(id=(m.group(2) if m.lastindex and m.lastindex >= 2 else '%s_%02d' % (ch, i + 1)), character=ch,
                            n=i + 1, name=name, tier=['normal', 'special', 'grand', 'ultimate'][tier(ch, i, len(heads))],
                            behaviour=beh, windup=wu, active=ac, recovery=rc, cooldown=cd, range=round(reach(f), 1), hits=hits,
                            particles=[], bones=['arm_r', 'arm_l', 'torso', 'head'] + (['wing_r', 'wing_l'] if ch.startswith('azazel') or ch == 'king4' else []),
                            link=None, motion=f['motion'], effect=f['effect'] + '。' + f['hitbox'], look=f['look'] + '／' + f['look'],
                            ai=f['when'], phases='', power=float(pw.group(1)) if pw else None))
    return out


def main(king, azazel, out):
    k = open(king, encoding='utf-8').read()
    z = open(azazel, encoding='utf-8').read()
    rows = read(k, SECTIONS) + read(z, AZ)
    chars = [{'id': c, 'name': c, 'direction': '', 'sound': '', 'shape': ''} for c in dict.fromkeys(r['character'] for r in rows)]
    json.dump({'characters': chars, 'techniques': rows}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    from collections import Counter
    print(len(rows), Counter(r['character'] for r in rows))
    print(Counter((r['character'][:5], r['behaviour']) for r in rows).most_common())


def finish(src, table, motions, out):
    import os, shutil
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_waza as bw
    d = json.load(open(src, encoding='utf-8'))
    t = json.load(open(table, encoding='utf-8'))
    by = {r['id']: r for r in d['techniques']}
    for row in t['techniques']:
        r = by[row[0]]
        # what an action does is in its effect and hit box, not its motion
        row[12] = bw.verbs_of(r['name'] + '。' + r['effect'], r['behaviour'])
        row.append(r.get('power'))
    t['version'] = 'royal-v20'
    with open(os.path.join(out, 'waza_royal.json'), 'w', encoding='utf-8') as f:
        json.dump(t, f, ensure_ascii=False, separators=(',', ':'))
    shutil.copy(motions, os.path.join(out, 'waza_royal_motions.bin'))
    print('royal actions', len(t['techniques']), 'with a V20 weight', sum(1 for r in t['techniques'] if r[22] is not None))


if __name__ == '__main__':
    if sys.argv[1] == 'finish':
        finish(*sys.argv[2:6])
    else:
        main(*sys.argv[1:4])

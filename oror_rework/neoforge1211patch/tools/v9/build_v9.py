"""(058) The 164 relics as the V9 design describes them, into the jar's data.

python3 -I tools/v9/build_v9.py <oror_164_relics_v9.txt> <base jar> <overlay assets dir> <lang dir>

- relics.json: the V8 setting power and cooldown of every relic (the document's 設定威力 and CD).
- relic_arts.json: the V8 programs, rebuilt from the document's prose over the shipped programs (prose.py): the
  weapons' right-click arts and hits (with the V8 神罰 draw), the focuses' V7 boosts and V8 punishment fan, the
  charms' V7 passives and casts, the legends' arts and their three stages (one per use, the cycle op), the third with
  the V8 punishment and the V9 crowning attack.
- relic_v9.json: what the Java reads besides: the tooltip text, the 123 techniques, the charms' crisis guards, the
  legends' crowning attacks, the punishment draws and the reward enchantments.
"""
import copy, json, os, re, sys, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prose  # noqa: E402
import techniques  # noqa: E402

design, jar, overlay, langdir = sys.argv[1:5]
z = zipfile.ZipFile(jar)
relics = json.loads(z.read('assets/oror_supreme_bosses/relics.json'))
arts = json.loads(z.read('assets/oror_supreme_bosses/relic_arts.json'))
kinds = json.loads(z.read('assets/oror_supreme_bosses/weapon_kinds.json'))['characters']

# the parsed document (parse_v9.py's rows)
import subprocess  # noqa: E402
tmp = os.path.join(os.path.dirname(overlay), '.v9_rows.json')
with open(os.path.join(os.path.dirname(overlay), '.relics_base.json'), 'w', encoding='utf-8') as fh:
    json.dump(relics, fh, ensure_ascii=False)
subprocess.check_call([sys.executable, '-I', os.path.join(HERE, 'parse_v9.py'), design, os.path.join(os.path.dirname(overlay), '.relics_base.json'), tmp])
rows = json.load(open(tmp, encoding='utf-8'))
os.remove(tmp)
os.remove(os.path.join(os.path.dirname(overlay), '.relics_base.json'))

by_id = {r['id']: r for r in relics}
art_by = {a['id']: a for a in arts['arts']}

EFF_OP = {'slowness': 'slow', 'mining_fatigue': 'fatigue', 'weakness': 'weakness', 'wither': 'wither', 'poison': 'poison'}
EFF_JA = {'slowness': '移動速度低下', 'mining_fatigue': '採掘速度低下', 'weakness': '弱体化', 'wither': '衰弱', 'poison': '毒'}
BUFF_JA = {'speed': '俊敏', 'luck': '幸運', 'resist': '耐性', 'regen': '再生', 'haste': '採掘速度上昇', 'night': '暗視', 'strength': '攻撃力上昇',
           'water': '水中呼吸', 'absorb': '衝撃吸収'}
ENCH_JA = {'unbreaking': '耐久力', 'mending': '修繕', 'sharpness': 'ダメージ増加', 'looting': 'ドロップ増加', 'sweeping_edge': '範囲ダメージ増加',
           'efficiency': '効率強化', 'knockback': 'ノックバック', 'quick_charge': '高速装填', 'power': '射撃ダメージ増加', 'punch': 'パンチ',
           'flame': 'フレイム', 'infinity': '無限', 'fire_aspect': '火属性', 'thorns': '棘の鎧'}
PARTICLE = {'electric_spark': 'spark'}
STAGE_SOUND = [('chime', 1.4), ('spell', 1.0), ('blast', 0.8)]

CRISIS = {  # the five guards the document gives the charms, by the gods it gives each to
    '所有者のHP35%以下、または防御可能な大技': {'k': 'counter', 'hp': 0.35, 'big': 0.3, 'cut': 0.9, 'heal': 0.25, 'window': 80, 'cd': 1300},
    'HP40%以下の被弾時': {'k': 'brand', 'hp': 0.40, 'cut': 0.75, 'span': 60, 'heal': 0.35, 'brand': 80, 'cd': 1600},
    'HP35%以下で3.5秒間80%': {'k': 'repel', 'hp': 0.35, 'cut': 0.8, 'span': 70, 'heal': 0.45, 'cd': 1500},
    'HP35%以下で補修用器官': {'k': 'repair', 'hp': 0.35, 'cut': 0.8, 'span': 120, 'heal': 0.4, 'units': 4, 'cd': 1800},
    '本人または半径20ブロック内の味方': {'k': 'rescue', 'hp': 0.30, 'cut': 0.85, 'span': 100, 'heal': 0.65, 'r': 20, 'cd': 1800},
}
ULTIMATE = {
    '第三段階では敵の特殊防御を一つ解析・解除': {'k': 'precise', 'base': 1600000, 'pct': 0.05, 'cap': 2000000},
    '第三段階は基準1,250,000と': {'k': 'rule', 'base': 1250000, 'pct': 0.04, 'cap': 1500000, 'r': 18, 'n': 12, 't': 100},
    '第三段階は基準1,800,000の大攻撃': {'k': 'grand', 'base': 1800000, 'pct': 0.08, 'cap': 3000000, 'field': 240, 'summons': 8},
    '第三段階で基準1,450,000の砲撃': {'k': 'machine', 'base': 1450000, 'units': 6, 'total': 8, 't': 400, 'cd': 1800},
    '第三段階へ追加する新しい効果は': {'k': 'rescue', 'base': 600000, 'r': 32, 'n': 16, 'heal': 0.8, 'cut': 0.85, 't': 120},
}
RULE_KIND = {'riha': 'gravity', 'nortia': 'rule', 'lucifara': 'seal', 'arcana': 'fate', 'miyohime': 'gravity', 'innocence': 'toy',
             'cursed_love': 'curse', 'sweet_pact': 'contract'}


def pick(table, text):
    for k, v in table.items():
        if text.startswith(k) or k in text:
            return dict(v)
    raise SystemExit('no variant for ' + text[:60])


def fmt(x):
    return ('%.2f' % x).rstrip('0').rstrip('.')


def wrap(text, n=34):
    out, cur = [], ''
    for i, ch in enumerate(text):
        cur += ch
        nxt = text[i + 1] if i + 1 < len(text) else ''
        if len(cur) >= n and ch in '、。・，）」』／ ':
            out.append(cur)
            cur = ''
        elif len(cur) >= n + 14 and not (ch.isdigit() or nxt.isdigit() or nxt in ',.%秒体m' or ch in ',.'):
            out.append(cur)
            cur = ''
    if cur.strip():
        # a last scrap of a few characters goes on the line before
        if out and len(cur) <= 4:
            out[-1] += cur
        else:
            out.append(cur)
    return out


def lines(style, text, first=''):
    ws = wrap(first + text)
    return [[style, w] for w in ws]


def clean(text):
    text = text.replace('**', '')
    text = re.sub(r'（未実装）|。?いずれもV8既存命令.*$', '', text)
    return text.strip()


def prose_ja(s):
    """The prose as a player reads it (the V8 op names in words)."""
    words = {'blink': '空間跳躍', 'erase': '飛び道具消去', 'knock': '吹き飛ばし', 'launch': '打ち上げ', 'pull': '引き寄せ', 'slam': '叩き落とし',
             'burn': '炎上', 'lightning': '落雷', 'arrows': '矢の雨', 'transmute': '変質', 'give': '物資生成', 'repair': '修復', 'adapt': '適応',
             'rewind': '巻き戻し', 'snapshot': '記録', 'freeze': '凍結', 'disarm': '武装解除', 'behind': '背後へ', 'back': '後退', 'heal': '回復',
             'say': '宣告', 'food': '満腹', 'around': '周囲追撃', 'golem': 'ゴーレム', 'wolf': '狼'}
    effs = {'slow': '鈍足', 'weakness': '弱体化', 'wither': '衰弱', 'poison': '毒', 'glow': '発光', 'levitate': '浮遊', 'nausea': '眩暈',
            'fatigue': '疲労', 'dark': '暗闇', 'blind': '盲目', 'hunger': '空腹', 'speed': '俊敏', 'luck': '幸運', 'resist': '耐性', 'regen': '再生',
            'haste': '採掘速度上昇', 'night': '暗視', 'strength': '攻撃力上昇', 'water': '水中呼吸', 'absorb': '衝撃吸収', 'jump': '跳躍',
            'dolphin': 'イルカの好意', 'health': '体力増強', 'slowfall': '低速落下'}
    s = re.sub(r'\b(%s)\b' % '|'.join(sorted(words, key=len, reverse=True)), lambda m: words[m.group(1)], s)
    s = re.sub(r'(強化)?(\w+?)Lv', lambda m: (m.group(1) or '') + effs.get(m.group(2), m.group(2)) + 'Lv', s)
    return s.replace('基準技威力', '基準威力')


# ------------------------------------------------------------------------------------------------ relics.json (V8)
v8 = {}
for row in rows:
    for it in row['items']:
        v8[it['id']] = it
new_relics = []
for r in relics:
    it = v8[r['id']]
    r2 = dict(r)
    r2['damage'] = it['damage']
    r2['cooldown'] = it['cd']
    new_relics.append(r2)

# ------------------------------------------------------------------------------------------------ relic_arts.json (V8 + V9)
def punish_draw(effect, chance, secs, mark=None):
    ops = [{'op': 'victim'}, {'op': 'punish', 'e': EFF_OP[effect], 't': int(round(secs * 20))}]
    if mark:
        ops.append({'op': 'mark', 't': mark[0], 'x': mark[1]})
    ops.append({'op': 'fx', 'p': 'sculk', 'n': 6, 'at': 't', 's': 0.4})
    return {'op': 'chance', 'p': chance, 'ops': ops}


def capped(ops, n=12):
    out = []
    for o in ops:
        o = dict(o)
        if o['op'] in ('area', 'near') and o.get('n', 64) > n:
            o['n'] = n
        if 'ops' in o:
            o['ops'] = capped(o['ops'], n)
        if 'else' in o:
            o['else'] = capped(o['else'], n)
        out.append(o)
    if any(o['op'] in ('line', 'cone', 'chain') for o in out):
        res = []
        for o in out:
            res.append(o)
            if o['op'] in ('line', 'cone'):
                res.append({'op': 'cap', 'n': n})
        out = res
    return out


new_arts = []
stage_say = {}
for row in rows:
    w, f, c, l = row['items']
    ch = row['character']
    for it in row['items']:
        a = copy.deepcopy(art_by[it['id']])
        slot = it['slot']
        if slot == 'weapon':
            a['cast'] = prose.align(prose.parse(it['cast']), a['cast'])
            hit = prose.align(prose.parse(it['hit_v6']), a['hit'])
            p = it['proc']
            hit.append(punish_draw(p['effect'], p['chance'], p['secs'], (100, 2.15)))
            a['hit'] = hit
        elif slot == 'focus':
            pn = it['punish']
            boost = prose.parse(it['v7'])
            a['cast'] = capped(a['cast'] + [{'op': 'cue', 'k': 'circle', 'at': 'self', 's': 2.5, 'l': 24, 'a': 1}] + boost + [
                {'op': 'cone', 'r': pn['range'], 'a': pn['angle']}, {'op': 'cap', 'n': 12},
                {'op': 'cue', 'k': 'chain', 'at': 't', 's': 1, 'l': 12},
                {'op': 'punish', 'e': EFF_OP[pn['effect']], 't': int(round(pn['secs'] * 20))},
                {'op': 'suppress', 't': 160},
                {'op': 'cue', 'k': 'flash', 'at': 't', 's': 1.2, 'l': 8},
                {'op': 'cue', 'k': 'circle', 'at': 't', 's': 1.0, 'l': 80},
                {'op': 'buff', 'e': it['buff'], 't': 200, 'a': 1}])
        elif slot == 'charm':
            pv = prose.parse(it['passive'])
            passive = list(a['passive'])
            for b in pv:
                same = [o for o in passive if o['op'] == 'buff' and o.get('e') == b.get('e')]
                if same:
                    same[0].update(b)
                else:
                    if not passive or passive[0]['op'] != 'self':
                        passive.insert(0, {'op': 'self'})
                    passive.append(b)
            a['passive'] = passive
            pn = f['punish']
            a['cast'] = a['cast'] + prose.parse(it['v7']) + [
                {'op': 'cone', 'r': 10, 'a': 95}, {'op': 'cap', 'n': 12},
                {'op': 'punish', 'e': EFF_OP[pn['effect']], 't': int(round(pn['secs'] * 20))}]
        else:  # legend
            a['cast'] = prose.align(prose.parse(it['cast']), a['cast'])
            p = it['proc']
            a['hit'] = list(a['hit']) + [punish_draw(p['effect'], p['chance'], p['secs'])]
            steps = []
            for i, st in enumerate(it['stages']):
                ops = [{'op': 'fx', 'p': PARTICLE.get(st['particle'], st['particle']), 'n': st['n'], 'at': 'self', 's': 1.2 + i * 0.4},
                       {'op': 'sound', 's': STAGE_SOUND[i][0], 'v': 1.0, 'pi': STAGE_SOUND[i][1]},
                       {'op': 'cue', 'k': ('circle', 'ring', 'pillar')[i], 'at': 'self', 's': 3 + i * 3, 'l': 30, 'h': 12}]
                ops += prose.parse(st['v7'])
                if i == 2:
                    ops += [{'op': 'area', 'r': 14, 'n': 14},
                            {'op': 'punish', 'e': EFF_OP[p['effect']], 't': int(round(it['proc']['secs'] * 20))},
                            {'op': 'mark', 't': 190, 'x': 3.1}, {'op': 'dmg', 'm': 1.25},
                            {'op': 'ultimate'}]
                key = 'relic_stage.oror_supreme_bosses.%s.%d' % (it['id'], i + 1)
                stage_say[key] = '第%d段階「%s」' % (i + 1, st['title'])
                steps.append({'say': key, 'ops': ops})
            a['cast'] = a['cast'] + [{'op': 'cycle', 'steps': steps}]
        new_arts.append(a)

# ------------------------------------------------------------------------------------------------ relic_v9.json
techs = []
v9 = {'relics': {}, 'techs': techs}
SLOT_JA = ['特殊技Ⅰ', '特殊技Ⅱ', '必殺技']
for row in rows:
    w, f, c, l = row['items']
    ch = row['character']
    god = row['title']
    kind = kinds[ch]
    # weapon techniques
    for s, sp in enumerate(w['specials']):
        t = techniques.T[(row['no'], s)]
        h = abs(hash((ch, s))) % 1000 if False else (row['no'] * 7 + s * 13)
        if s == 0:
            wind = [8 + h % 7, 10 + h % 11]
        elif s == 1:
            wind = [12 + h % 13, 0]
        else:
            wind = [20 + h % 26, 20 + h % 31]
        techs.append({'index': len(techs), 'id': '%s#%d' % (w['id'], s), 'relic': w['id'], 'character': ch, 'slot': s,
                      'name': sp['name'], 'label': SLOT_JA[s], 'damage': sp['damage'], 'range': sp['range'], 'cd': sp['cd'] * 20,
                      'wind': t['wind'] or wind, 'tele': t['tele'], 'anim': techniques.ANIM[kind][s], 'kind': kind,
                      'color': w['color'], 'prog': t['prog'], 'motion': sp['motion'], 'effect': sp['effect']})
    for it in row['items']:
        slot = it['slot']
        e = {'slot': slot, 'character': ch, 'god': god, 'name': it['name']}
        summary, detail = [], []
        if slot == 'weapon':
            p = it['proc']
            summary += [['gold', '「%s」討伐の証・神討伐武器' % god]]
            summary += lines('gray', it['look'] + '。', '権能の核：')
            summary += [['white', '設定威力 %s ／ 攻撃属性 %d ／ 待機 %s秒（実効 %s秒）' % (fmt(it['damage']), it['attribute'], fmt(it['cd'] / 20), fmt(max(20, it['cd'] * 3 // 4) / 20))]]
            summary += lines('aqua', it['normal'], '通常攻撃：')
            summary += lines('light_purple', '命中ごと%s%%で%sL125（%s秒）と神罰刻印（5秒・被ダメ×2.15）' % (fmt(p['chance'] * 100), EFF_JA[p['effect']], fmt(p['secs'])), '神罰：')
            for s, sp in enumerate(it['specials']):
                summary += [['green' if s < 2 else 'gold', '[{K%d}] %s「%s」 基準%s／%dm／再使用%d秒' % (s, SLOT_JA[s], sp['name'], format(sp['damage'], ','), sp['range'], sp['cd'])]]
                summary += lines('gray', sp['effect'] + '。', '　')
            detail += [['yellow', '右クリック権能（既存）']] + lines('white', prose_ja(it['cast']) + '。')
            detail += [['yellow', '命中処理']] + lines('white', prose_ja(it['hit_v6']) + '。')
            for s, sp in enumerate(it['specials']):
                detail += [['green', '%s「%s」の動き' % (SLOT_JA[s], sp['name'])]] + lines('gray', sp['motion'])
            detail += [['yellow', '報酬エンチャント']] + lines('white', '、'.join('%s %d' % (ENCH_JA[k], v) for k, v in it['enchants']))
            e['proc'] = {'e': EFF_OP[p['effect']], 'p': p['chance'], 't': int(round(p['secs'] * 20))}
            e['enchants'] = it['enchants']
        elif slot == 'focus':
            pn = it['punish']
            summary += [['gold', '「%s」討伐の証・神威触媒' % god]]
            summary += lines('gray', it['spell'], '固有の術式：')
            summary += [['white', '設定威力 %s ／ 待機 %s秒（実効 %s秒）' % (fmt(it['damage']), fmt(it['cd'] / 20), fmt(max(20, it['cd'] * 3 // 4) / 20))]]
            summary += lines('aqua', prose_ja(it['v7']) + '。', '増幅：')
            summary += lines('light_purple', '前方14ブロック・95度の敵（最大12体）へ%sL125（%s秒）、装備者へ%s' % (EFF_JA[pn['effect']], fmt(pn['secs']), BUFF_JA.get(it['buff'], it['buff'])), '神罰：')
            summary += lines('yellow', '行動停止が効かない強敵にも、防御・再生・攻撃速度の抑制を8秒通す。', '対ボス：')
            detail += lines('gray', '詠唱開始（手元の陣）、成立（印へ伸びる線）、命中（閃光）、残留（敵に残る陣）を順に見せる。')
            detail += [['yellow', '既存の発動処理']] + lines('white', '神格固有の中距離権能に、上の増幅と神罰を重ねて実行する。')
        elif slot == 'charm':
            cr = pick(CRISIS, it['crisis_text'])
            e['crisis'] = cr
            summary += [['gold', '「%s」討伐の証・神格装飾品' % god]]
            summary += lines('gray', it['form'], '常時加護：')
            summary += lines('white', prose_ja(it['passive']) + '（着用中）', '常時補助：')
            summary += [['white', '手動発動 設定威力 %s ／ 待機 %s秒（実効 %s秒）' % (fmt(it['damage']), fmt(it['cd'] / 20), fmt(max(20, it['cd'] * 3 // 4) / 20))]]
            summary += lines('aqua', prose_ja(it['v7']) + '。前方10ブロックへ神罰。', '手動発動：')
            summary += lines('red', clean(it['crisis_text']), '危機対応（自動）：')
        else:
            p = it['proc']
            ul = pick(ULTIMATE, it['ultimate_text'])
            if ul['k'] == 'rule':
                ul['rule'] = RULE_KIND[ch]
            e['ultimate'] = ul
            e['proc'] = {'e': EFF_OP[p['effect']], 'p': p['chance'], 't': int(round(p['secs'] * 20))}
            e['enchants'] = w['enchants']
            summary += [['gold', '「%s」討伐の証・超越神器' % god]]
            summary += lines('gray', it['whole'], '全権能：')
            summary += [['white', '設定威力 %s ／ 攻撃属性 %d ／ 待機 %s秒（実効 %s秒）' % (fmt(it['damage']), it['attribute'], fmt(it['cd'] / 20), fmt(max(20, it['cd'] * 3 // 4) / 20))]]
            summary += lines('light_purple', '通常命中%s%%で%sL125（%s秒）' % (fmt(p['chance'] * 100), EFF_JA[p['effect']], fmt(p['secs'])), '神罰：')
            summary += lines('yellow', '使うたびに段階が進む：' + '→'.join('第%d「%s」' % (i + 1, s['title']) for i, s in enumerate(it['stages'])))
            summary += lines('gold', clean(it['ultimate_text']), '第三段階の極致：')
            detail += [['yellow', '大規模権能（既存）']] + lines('white', prose_ja(it['cast']) + '。')
            for i, s in enumerate(it['stages']):
                detail += [['green', '第%d段階「%s」' % (i + 1, s['title'])]] + lines('white', prose_ja(s['v7']) + '。')
            detail += lines('gray', '第三段階の極致は125tickの演出：0～20で構え、21～60で形成、61～100で攻撃とフィニッシュ、101～125で残光。')
        detail += lines('dark_gray', row['common'])
        e['summary'] = summary
        e['detail'] = detail
        v9['relics'][it['id']] = e

os.makedirs(overlay, exist_ok=True)
json.dump(new_relics, open(os.path.join(overlay, 'relics.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump({'arts': new_arts}, open(os.path.join(overlay, 'relic_arts.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
json.dump(v9, open(os.path.join(overlay, 'relic_v9.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
for lang in ('ja_jp', 'en_us'):
    path = os.path.join(langdir, lang + '.json')
    table = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    table.update(stage_say)
    table['key.categories.oror_supreme_bosses.relic'] = 'OROR 神器' if lang == 'ja_jp' else 'OROR Relics'
    for i, n in enumerate(('特殊技Ⅰ', '特殊技Ⅱ', '必殺技')):
        table['key.oror_supreme_bosses.tech%d' % i] = ('神討伐武器 ' + n) if lang == 'ja_jp' else ('Relic weapon: ' + ('special I', 'special II', 'finisher')[i])
    json.dump(table, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
print(len(new_relics), 'relics,', len(new_arts), 'arts,', len(techs), 'techniques,', len(stage_say), 'stage names')

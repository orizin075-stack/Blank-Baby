"""Parse the V9 design text (oror_rework/design/oror_164_relics_v9.txt) into one row per relic.

python3 -I tools/v9/parse_v9.py <design.txt> <relics.json from the jar> <out.json>
"""
import json, re, sys

src, relics_path, out_path = sys.argv[1:4]
t = open(src, encoding='utf-8').read()
relics = json.load(open(relics_path, encoding='utf-8'))
by_name = {r['name']: r for r in relics}

def one(pat, s, flags=re.S, group=1, req=True):
    m = re.search(pat, s, flags)
    if not m:
        if req:
            raise SystemExit('no match %r in %s' % (pat, s[:160]))
        return None
    return m.group(group)

def num(x):
    return float(x.replace(',', ''))

EFFECTS = {'移動速度低下': 'slowness', '採掘速度低下': 'mining_fatigue', '弱体化': 'weakness', '衰弱': 'wither', '毒': 'poison'}
ENCH = {'耐久力': 'unbreaking', '修繕': 'mending', 'ダメージ増加': 'sharpness', 'ドロップ増加': 'looting', '範囲ダメージ増加': 'sweeping_edge',
        '効率強化': 'efficiency', 'ノックバック': 'knockback', '高速装填': 'quick_charge', '射撃ダメージ増加': 'power', 'パンチ': 'punch',
        'フレイム': 'flame', '無限': 'infinity', 'fire_aspect': 'fire_aspect', 'thorns': 'thorns'}

def enchants(s):
    out = []
    for part in s.split('、'):
        name, lv = part.strip().rsplit(' ', 1)
        out.append([ENCH[name], int(lv)])
    return out

def special(block, label):
    m = re.search(label + r'「(.+?)」〈独立技・改良設計〉　基準ダメージ([\d,]+)、作用距離・半径目安(\d+)ブロック、再使用(\d+)秒。(.+?)命中した際には(.+?)(?:8～14tick|12～24tick|20～45tick)', block, re.S)
    if not m:
        raise SystemExit('special %s not found in %s' % (label, block[:200]))
    return {'name': m.group(1), 'damage': int(num(m.group(2))), 'range': int(m.group(3)), 'cd': int(m.group(4)),
            'motion': m.group(5).strip(), 'effect': m.group(6).strip().rstrip('。')}

def stage(block, i):
    m = re.search(r'第%d段階「(.+?)」　.+?V7追加の効果：(.+?)。`(\w+)`粒子(\d+)個' % i, block, re.S)
    if not m:
        raise SystemExit('stage %d not found' % i)
    return {'title': m.group(1), 'v7': m.group(2), 'particle': m.group(3), 'n': int(m.group(4))}

rows = []
sections = re.split(r'\n(?=\d\d\. )', t)[1:]
assert len(sections) == 41, len(sections)
for sec in sections:
    head = sec.split('\n', 1)[0]
    no, title = re.match(r'(\d\d)\. (.+)', head).groups()
    core = one(r'権能の核　(.+?) 神格そのもの', sec)
    parts = re.split(r'\n(?=[①②③④] )', sec)
    assert len(parts) == 5, (title, len(parts))
    w, f, c, l = parts[1:]
    common = one(r'の4装備に共通する設計上の約束　(.+)$', sec).strip()
    # ① weapon
    wname = one(r'^① 神討伐武器「(.+?)」', w)
    proc = re.search(r'これにV8で(.+?)L125を([\d.]+)%で([\d.]+)秒間与える追加抽選', w)
    weapon = {
        'slot': 'weapon', 'name': wname,
        'damage': num(one(r'V8の設定威力は`([\d.]+)`', w)), 'attribute': int(one(r'攻撃属性値は(\d+)', w)),
        'cd': int(one(r'データCDは`(\d+)`tick', w)), 'enchants': enchants(one(r'エンチャント定義は「(.+?)」', w)),
        'normal': one(r'通常攻撃と凶悪な追加効果　(.+?) V6の既存', w), 'hit_v6': one(r'V6の既存命中処理は「(.+?)。抽選は', w),
        'proc': {'effect': EFFECTS[proc.group(1)], 'chance': num(proc.group(2)) / 100, 'secs': num(proc.group(3))},
        'cast': one(r'現行の右クリック権能　(.+?)。。', w), 'look': one(r'見た目と打撃手応えの改訂案　初動は(.+?)。。', w),
        'specials': [special(w, '特殊技Ⅰ'), special(w, '特殊技Ⅱ'), special(w, '武器専用必殺技')],
    }
    # ② focus
    fx = re.search(r'\*\*(.+?)L125（([\d.]+)秒相当）\*\*の干渉と、装備者への`(\w+)`系バフ', f)
    focus = {
        'slot': 'focus', 'name': one(r'^② 神威触媒「(.+?)」', f), 'spell': one(r'固有の術式　(.+?) この触媒は', f),
        'damage': num(one(r'設定威力`([\d.]+)`', f)), 'cd': int(one(r'CD`(\d+)`tick', f)),
        'v7': one(r'増幅効果は「(.+?)。さらに', f), 'extra': one(r'追加処理`(\w+)`', f),
        'punish': {'effect': EFFECTS[fx.group(1)], 'secs': num(fx.group(2)), 'range': 14, 'angle': 95}, 'buff': fx.group(3),
    }
    # ③ charm
    crisis = one(r'危機対応能力の追加案（未実装）　.+?。。(.+?)いずれもV8既存命令', c)
    charm = {
        'slot': 'charm', 'name': one(r'^③ 神格装飾品「(.+?)」', c), 'form': one(r'常時加護と形状　(.+?) V7の既存', c),
        'passive': one(r'V7の既存常時補助は「(.+?)。」', c), 'damage': num(one(r'設定威力`([\d.]+)`', c)),
        'cd': int(one(r'CD`(\d+)`tick', c)), 'v7': one(r'追加された効果は「(.+?)。さらに', c), 'extra': one(r'追加処理`(\w+)`', c),
        'crisis_text': crisis.strip(),
    }
    # ④ legend
    lp = re.search(r'V8では通常命中\*\*([\d.]+)%\*\*で(.+?)L125（([\d.]+)秒）を追加抽選', l)
    legend = {
        'slot': 'legend', 'name': one(r'^④ 超越神器「(.+?)」', l), 'whole': one(r'神格の全権能　(.+?) 設定威力', l),
        'damage': num(one(r'設定威力`([\d.]+)`', l)), 'attribute': int(one(r'攻撃属性値は(\d+)', l)), 'cd': int(one(r'定義CDは`(\d+)`tick', l)),
        'proc': {'effect': EFFECTS[lp.group(2)], 'chance': num(lp.group(1)) / 100, 'secs': num(lp.group(3))},
        'cast': one(r'現行の大規模権能・代表例　(.+?)。。', l),
        'stages': [stage(l, 1), stage(l, 2), stage(l, 3)],
        'ultimate_text': one(r'101～125tickで残光と終了動作を表示する。.+?。。(.+?)数値は実ダメージ実測ではなく', l).strip(),
    }
    for item in (weapon, focus, charm, legend):
        r = by_name.get(item['name'])
        if r is None:
            raise SystemExit('no relic named %s' % item['name'])
        item['id'] = r['id']
        item['character'] = r['character']
        item['rank'] = r['rank']
        item['color'] = r['color']
    rows.append({'no': int(no), 'title': title, 'core': core, 'common': common, 'character': weapon['character'],
                 'items': [weapon, focus, charm, legend]})

json.dump(rows, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(rows), 'characters,', sum(len(r['items']) for r in rows), 'relics,', sum(len(r['items'][0]['specials']) for r in rows), 'specials')

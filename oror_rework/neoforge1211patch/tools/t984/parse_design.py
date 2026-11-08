"""Parse the 984-technique design document (v2) into techniques984.json.

Usage: parse_design.py <design.txt> <characters.json> <out.json>
"""
import json, re, sys

TIERS = {'通常': 'normal', '特殊': 'special', '大技': 'grand', '必殺': 'ultimate'}
BEHAVIOURS = {
    '近接判定': 'MELEE', '飛翔体': 'PROJECTILE', '光線': 'BEAM', '移動・回避': 'MOVE', '防御': 'GUARD',
    '状態効果': 'STATUS', '特殊領域': 'FIELD', '独立召喚': 'SUMMON', '組立・生産': 'BUILD', '治癒・支援': 'HEAL',
    '対象の行動制御': 'CONTROL', '限定巻き戻し': 'REWIND', '適応・学習': 'ADAPT', '呪詛': 'CURSE',
    '成長物・根': 'GROWTH', '歌・音圧': 'SONG', '同意式契約': 'PACT',
}
FIELDS = ['動作・描写', '予兆→発動→終了', '効果', '視覚・音', '判定・数値案', 'AI・対処', '骨格・追加部品']


def main(src, chars, out):
    text = open(src, encoding='utf-8').read().replace('\r', '')
    roster = json.load(open(chars, encoding='utf-8'))
    by_name = {c['name']: c['id'] for c in roster}
    lines = text.split('\n')
    result, cur, tier, move = [], None, None, None
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line in by_name:
            cur = {'id': by_name[line], 'name': line, 'moves': []}
            result.append(cur)
            tier = None
            continue
        if cur is None:
            continue
        if line.startswith('演出方針：'):
            m = re.match(r'演出方針：\s*(.*?)\s*音：\s*(.*?)\s*色・造形：\s*(.*)$', line)
            cur['direction'], cur['sound'], cur['shape'] = m.group(1), m.group(2), m.group(3)
            continue
        if line in TIERS:
            tier = TIERS[line]
            continue
        m = re.match(r'^(\d{2})\. (.+)$', line)
        if m and tier:
            move = {'n': int(m.group(1)), 'name': m.group(2).strip(), 'tier': tier}
            cur['moves'].append(move)
            continue
        for f in FIELDS:
            if line.startswith(f + '：'):
                move[f] = line[len(f) + 1:].strip()
                break
        else:
            raise SystemExit('unparsed line: ' + line[:80])
    techniques = []
    for c in result:
        assert len(c['moves']) == 24, (c['name'], len(c['moves']))
        for mv in c['moves']:
            eff = mv['効果']
            kind = eff.split('。')[0]
            beh = BEHAVIOURS.get(kind)
            if beh is None:
                raise SystemExit('behaviour? ' + c['name'] + ' ' + mv['name'] + ' ' + kind)
            num = mv['判定・数値案']
            g = re.search(r'予備(\d+)t、発動(\d+)t、終了(\d+)t、CD(\d+)t、作用半径/射程([\d.]+)ブロック', num)
            ev = re.search(r'攻撃イベント=(\[[\d, ]*\]|なし・状態効果型)', num)
            hits = json.loads(ev.group(1)) if ev.group(1).startswith('[') else []
            vis = mv['視覚・音']
            parts = re.search(r'粒子候補：([^。]*)', vis)
            particles = [p.strip() for p in parts.group(1).split(',')] if parts else []
            ai = mv['AI・対処']
            link = re.search(r'連携：(前提|後続|姿勢復帰後)：([^。]+)', ai)
            bones = mv['骨格・追加部品'].split('。')[0]
            phases = mv['予兆→発動→終了']
            techniques.append({
                'id': '%s_%02d' % (c['id'], mv['n']), 'character': c['id'], 'n': mv['n'], 'name': mv['name'],
                'tier': mv['tier'], 'behaviour': beh, 'windup': int(g.group(1)), 'active': int(g.group(2)),
                'recovery': int(g.group(3)), 'cooldown': int(g.group(4)), 'range': float(g.group(5)), 'hits': hits,
                'particles': particles, 'bones': [b.strip() for b in bones.split(',')],
                'link': [link.group(1), link.group(2).strip()] if link else None,
                'motion': mv['動作・描写'], 'phases': phases, 'effect': eff, 'look': vis, 'ai': ai,
            })
    chars_out = [{k: c[k] for k in ('id', 'name', 'direction', 'sound', 'shape')} for c in result]
    assert len(result) == 41 and len(techniques) == 984
    names = [t['motion'] for t in techniques]
    assert len(set(names)) == 984, 'duplicate motion text'
    json.dump({'characters': chars_out, 'techniques': techniques}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    from collections import Counter
    print(Counter(t['behaviour'] for t in techniques))
    print(Counter(t['tier'] for t in techniques))


if __name__ == '__main__':
    main(*sys.argv[1:4])

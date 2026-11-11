"""(059) The V20 design's registered values for the 984 techniques (01_gods_984_fx.md, each technique's 現行登録値),
over waza984.json as build_waza.py wrote it.

Usage: apply_v20.py <01_gods_984_fx.md> <waza984.json> [report.json]

V20 agrees with the table for all but 52 techniques: 51 it gives another behaviour (a strike where the 057 reading had a
state, a projectile where it had a device, and so on) with the reach, the hits (at the ticks it gives, counted from the
start: the table counts them from the end of the windup), the count and the shape that go with it, and one another
count. Those rows take V20's values; what a new behaviour needs besides (how a move goes, what a summon is, what a device
is, what sets a curse off) is read from V20's own text of the technique with build_waza.py's tables. A technique that
newly heals has its verbs read again; one that heals no longer loses its healing verb. Every other row is left as it
is: this changes nothing V20 does not.
"""
import json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_waza as bw

ENTRY = re.compile(r'#### (.+?)（`([a-z_]+_\d+)`）\s*\n\*\*現行登録値\*\*：([A-Z]+)／予兆(\d+)tick、作用(\d+)tick、復帰(\d+)tick、CD(\d+)tick。'
                   r'射程([\d.]+)ブロック、形状コード(\d+)、count=(\d+)、発動基準イベント(\[[\d, ]*\]|個別指定なし)。追加フラグ：(.*?)。現行粒子：(.*?)。')
PARA = re.compile(r'\*\*(動作・モーション改稿|当たり判定・効果改稿)\*\*：(.*)')


def read(doc):
    out = {}
    matches = list(ENTRY.finditer(doc))
    for k, m in enumerate(matches):
        name, tid, beh, wu, ac, rc, cd, rng, shape, cnt, ev, flags, _ = m.groups()
        end = matches[k + 1].start() if k + 1 < len(matches) else len(doc)
        paras = {p.group(1): p.group(2) for p in PARA.finditer(doc[m.end():end])}
        out[tid] = dict(name=name, beh=beh, wu=int(wu), ac=int(ac), rc=int(rc), cd=int(cd), rng=float(rng), shape=int(shape),
                        cnt=int(cnt), hits=json.loads(ev) if ev.startswith('[') else [],
                        text=name + '。' + paras.get('動作・モーション改稿', '') + paras.get('当たり判定・効果改稿', ''))
    return out


def kind_of(beh, text):
    if beh == 'MOVE':
        return bw.find(bw.MOVES, text)
    if beh == 'SUMMON':
        return str(bw.find(bw.SUMMON_STYLE, text))
    if beh == 'BUILD':
        return bw.find(bw.DEVICE, text)
    if beh == 'CURSE':
        return bw.find(bw.CURSE_TRIGGER, text)
    return ''


def main(doc_path, table_path, report=None):
    v20 = read(open(doc_path, encoding='utf-8').read())
    table = json.load(open(table_path, encoding='utf-8'))
    rows = table['techniques']
    assert len(v20) == len(rows) == 984, (len(v20), len(rows))
    changed, kept = [], 0
    for row in rows:
        r = v20[row[0]]
        # the timing V20 gives is the table's own everywhere: a row it disagrees with on that is not one to touch
        assert (row[6], row[7], row[8], row[9]) == (r['wu'], r['ac'], r['rc'], r['cd']), row[0]
        hits = [h - r['wu'] for h in r['hits']]
        same = (row[5] == r['beh'] and abs(row[10] - r['rng']) < 0.05 and row[11] == hits and row[14] == r['shape']
                and row[15] == r['cnt'])
        if same:
            kept += 1
            continue
        assert all(0 <= h < r['ac'] for h in hits), (row[0], hits, r['ac'])
        was = {'behaviour': row[5], 'range': row[10], 'hits': row[11], 'kind': row[13], 'shape': row[14], 'count': row[15],
               'verbs': list(row[12])}
        heals = (row[5] == 'HEAL') != (r['beh'] == 'HEAL')
        row[5], row[10], row[11], row[14], row[15] = r['beh'], r['rng'], hits, r['shape'], r['cnt']
        row[13] = kind_of(r['beh'], r['text'])
        if heals and r['beh'] == 'HEAL':
            row[12] = bw.verbs_of(r['text'], r['beh'])
        elif heals:
            # a heal that now strikes: it no longer heals whom it reaches (its other verbs stay as they were read)
            row[12] = [v for v in row[12] if v != 'HEAL_ALLY']
        changed.append({'id': row[0], 'name': row[3], 'was': was,
                        'now': {'behaviour': row[5], 'range': row[10], 'hits': row[11], 'kind': row[13], 'shape': row[14],
                                'count': row[15], 'verbs': row[12]}})
    with open(table_path, 'w', encoding='utf-8') as f:
        json.dump(table, f, ensure_ascii=False, separators=(',', ':'))
    print('V20 values applied to', len(changed), 'techniques;', kept, 'agreed already')
    if report:
        json.dump(changed, open(report, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main(*sys.argv[1:4])

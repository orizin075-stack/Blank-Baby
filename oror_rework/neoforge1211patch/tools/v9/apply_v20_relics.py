"""(059c) The 123 relic weapon techniques on V20's timing (02_relics_164_fx.md, each technique's モーション・当たり判定案:
「0～Ntickまでに…判定発生はA,B,…tick（設計値）」), over relic_v9.json as 058 wrote it.

Usage: apply_v20_relics.py <02_relics_164_fx.md> <relic_v9.json> [report.json]

058 read the techniques from the V9 design: each gathered for its own windup and struck once or twice. V20 gives each its
moments: the windup up to the first, then one to four blows at the ticks it names (counted from the start). Here:
* the windup becomes V20's first blow (the special techniques' two parts of it keep their proportion; the finisher's
  forming, the time its later moments may run, covers its last blow);
* the program's blows (a dmg at the release, the dmg of each later moment, `after`) fall on V20's later ticks; where V20
  has more blows than the program, its last blow is struck again at each further tick; the damage of all the blows
  together is what the program dealt (each blow a share), so nothing is stronger than 058 made it;
* a technique without a blow (a guard, a field, a summons, a blessing) keeps its program and takes V20's windup.
The techniques are matched by name; V20's three for Innocence (とまれ, 逆になあれ, ほんとうになあれ) by the relic and slot.
"""
import copy, json, re, sys

PAT = re.compile(r'\*\*(特殊技Ⅰ|特殊技Ⅱ|必殺技)「(.+?)」のモーション・当たり判定案\*\*：0～(\d+)tickまでに(.*?)判定発生は([\d,]+)tick（設計値）。'
                 r'コライダーは `([^`]+)`、効果タイプ `([^`]+)`。発生前の予兆は(\d+)～(\d+)tick')
HEAD = re.compile(r'### .+?（(?:討伐武器)／`([a-z_]+)`）')
SLOT = {'特殊技Ⅰ': 0, '特殊技Ⅱ': 1, '必殺技': 2}


def read(doc):
    out = []
    heads = [(m.start(), m.group(1)) for m in HEAD.finditer(doc)]
    for m in PAT.finditer(doc):
        relic = [r for at, r in heads if at < m.start()][-1]
        label, name, wend, motion, hits, collider, effect, t0, t1 = m.groups()
        out.append(dict(relic=relic, slot=SLOT[label], name=name, hits=[int(h) for h in hits.split(',')], collider=collider,
                        effect=effect, tele=[int(t0), int(t1)], motion=motion.strip('、。')))
    return out


def blows(prog):
    """The program's blows: (delay, the list holding it, the ops of that moment). The release is delay 0."""
    out = []
    if any(o['op'] == 'dmg' for o in prog):
        out.append([0, prog])
    for o in prog:
        if o['op'] == 'after' and any(x['op'] == 'dmg' for x in o.get('ops', [])):
            out.append([o.get('t', 10), o])
    return out


def scale_dmg(ops, f):
    for o in ops:
        if o['op'] == 'dmg':
            o['m'] = round(o.get('m', 1.0) * f, 4)


def apply(t, v):
    h0 = v['hits'][0]
    rel = [h - h0 for h in v['hits']]
    was = {'wind': list(t['wind']), 'prog_blows': [b[0] for b in blows(t['prog'])]}
    if t['slot'] == 2:
        t['wind'][0] = h0
    else:
        a, b = t['wind']
        tot = max(1, a + b)
        first = round(h0 * a / tot)
        t['wind'] = [first, h0 - first]
    bl = blows(t['prog'])
    if bl:
        total = 0.0
        for d, holder in bl:
            ops = holder if isinstance(holder, list) else holder['ops']
            total += sum(o.get('m', 1.0) for o in ops if o['op'] == 'dmg')
        # later moments onto V20's ticks; more blows as V20 asks
        later = [b for b in bl if not isinstance(b[1], list)]
        has_release = isinstance(bl[0][1], list)
        need = len(rel) - (1 if has_release else 0)
        ticks = rel[1:] if has_release else rel
        for i, (d, o) in enumerate(later):
            o['t'] = ticks[min(i, len(ticks) - 1)] if ticks else max(1, d)
        if need > len(later):
            src = later[-1][1] if later else {'op': 'after', 't': 0, 'ops': [copy.deepcopy(x) for x in t['prog'] if x['op'] not in ('after', 'rep', 'pts')]}
            for i in range(len(later), need):
                extra = copy.deepcopy(src)
                extra['t'] = ticks[i]
                t['prog'].append(extra)
        # each blow a share of what the program dealt
        bl = blows(t['prog'])
        now = 0.0
        for d, holder in bl:
            ops = holder if isinstance(holder, list) else holder['ops']
            now += sum(o.get('m', 1.0) for o in ops if o['op'] == 'dmg')
        if now > 0 and abs(now - total) > 1e-6:
            for d, holder in bl:
                scale_dmg(holder if isinstance(holder, list) else holder['ops'], total / now)
    if t['slot'] == 2:
        t['wind'][1] = max(t['wind'][1], (rel[-1] + 12) if rel else t['wind'][1])
    t['v20'] = {'hits': v['hits'], 'tele': v['tele'], 'collider': v['collider'], 'effect': v['effect']}
    return was


def main(doc_path, v9_path, report=None):
    v20 = read(open(doc_path, encoding='utf-8').read())
    d = json.load(open(v9_path, encoding='utf-8'))
    techs = d['techs']
    by_name = {t['name']: t for t in techs}
    by_slot = {(t['relic'], t['slot']): t for t in techs}
    assert len(v20) == len(techs) == 123, (len(v20), len(techs))
    changes = []
    for v in v20:
        t = by_name.get(v['name']) or by_slot[(v['relic'], v['slot'])]
        assert t['relic'] == v['relic'] and t['slot'] == v['slot'], (v['name'], t['id'])
        was = apply(t, v)
        changes.append({'id': t['id'], 'name': t['name'], 'v20_name': v['name'], 'was': was, 'now': {'wind': t['wind'],
                        'blows': [b[0] for b in blows(t['prog'])]}, 'v20_hits': v['hits']})
    json.dump(d, open(v9_path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('techniques on V20 timing', len(changes))
    if report:
        json.dump(changes, open(report, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main(*sys.argv[1:4])

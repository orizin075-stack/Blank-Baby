"""Validate and emit the relic arts, relic names and tooltip lang entries.
Usage: python3 relic_arts_build.py <assets_root> <original relics.json>"""
import json, os, sys
import relic_arts as R
import relic_arts_a, relic_arts_b, relic_arts_c   # noqa: F401  (register the arts)
import relic_names as N

NS = 'oror_supreme_bosses'
KNOWN_OPS = {'area', 'near', 'around', 'line', 'cone', 'chain', 'allies', 'self', 'victim', 'dmg', 'execute', 'stun', 'eff', 'burn', 'freeze',
             'mark', 'strip', 'disarm', 'transmute', 'lightning', 'arrows', 'knock', 'pull', 'launch', 'slam', 'blink', 'back', 'behind', 'swap',
             'dash', 'leap', 'heal', 'healpct', 'buff', 'cleanse', 'guard', 'undying', 'adapt', 'reflect', 'erase', 'food', 'repair', 'xp', 'give',
             'summon', 'weather', 'time', 'snapshot', 'rewind', 'cycle', 'chance', 'each', 'low', 'fx', 'sound', 'say'}
EFFECTS = {'slow', 'speed', 'haste', 'fatigue', 'strength', 'resist', 'fireres', 'regen', 'absorb', 'luck', 'jump', 'water', 'dolphin', 'invis',
           'night', 'health', 'saturation', 'slowfall', 'levitate', 'glow', 'wither', 'poison', 'blind', 'dark', 'nausea', 'hunger', 'weakness'}
PARTICLES = {'flame', 'soulfire', 'soul', 'spark', 'crit', 'enchant', 'portal', 'rportal', 'dragon', 'witch', 'happy', 'bubble', 'splash', 'smoke',
             'bigsmoke', 'explosion', 'blast', 'sonic', 'snow', 'heart', 'firework', 'sculk', 'lava', 'poof', 'ash', 'angry', 'compost', 'wax', 'end_rod'}
SOUNDS = {'totem', 'stone', 'teleport', 'glass', 'mirror', 'spell', 'summon', 'blast', 'wither', 'sonic', 'chain', 'anvil', 'roar', 'smith', 'chime'}
ITEMS = {'diamond', 'emerald', 'netherite', 'iron', 'redstone', 'bread', 'arrow', 'coal', 'gold'}

def check(ops, where):
    for o in ops:
        op = o['op']
        assert op in KNOWN_OPS, f'{where}: unknown op {op}'
        if op in ('eff', 'buff'):
            assert o['e'] in EFFECTS, f'{where}: effect {o["e"]}'
        if op == 'fx':
            assert o['p'] in PARTICLES, f'{where}: particle {o["p"]}'
        if op == 'sound':
            assert o['s'] in SOUNDS, f'{where}: sound {o["s"]}'
        if op == 'give':
            assert o['item'] in ITEMS, f'{where}: item {o["item"]}'
        for k in ('ops', 'else'):
            if k in o:
                check(o[k], where)
        if op == 'cycle':
            for st in o['steps']:
                check(st['ops'], where)
                assert st['say'] in R.SAYS, f'{where}: missing say {st["say"]}'
        if op == 'say':
            assert o['k'] in R.SAYS, f'{where}: missing say {o["k"]}'

def main(root, relics_path):
    relics = json.load(open(relics_path, encoding='utf-8'))
    ids = [r['id'] for r in relics]
    chars = sorted({r['character'] for r in relics})
    want = set(ids) | {c + '_relic_weapon' for c in chars}
    have = set(R.ARTS)
    assert want == have, f'missing {sorted(want - have)} extra {sorted(have - want)}'
    for a in R.ARTS.values():
        for k in ('cast', 'passive', 'hit'):
            check(a[k], a['id'] + '.' + k)
    by_id = {r['id']: r for r in relics}
    out = []
    for rid in sorted(R.ARTS):
        a = R.ARTS[rid]
        e = {'id': rid, 'character': a['character'], 'rank': a['rank'], 'cast': a['cast'], 'passive': a['passive'], 'hit': a['hit']}
        if rid.endswith('_relic_weapon'):
            e['cd'] = a['cd'] or 60
        elif a['cd']:
            e['cd'] = a['cd']
        if rid in by_id:
            assert by_id[rid]['rank'] == a['rank'], f'{rid}: rank {a["rank"]} != {by_id[rid]["rank"]}'
        out.append(e)
    with open(os.path.join(root, 'relic_arts.json'), 'w', encoding='utf-8') as fh:
        json.dump({'arts': out}, fh, ensure_ascii=False, separators=(',', ':'))
    # ---- names: relics.json (weapon names follow the new designs, renamed focus relics)
    for r in relics:
        c = r['character']
        if r['slot'] == 'weapon':
            r['name'] = N.WEAPON[c][0]
        elif r['slot'] == 'focus' and c in N.FOCUS_RENAME:
            r['name'] = N.FOCUS_RENAME[c]
    with open(os.path.join(root, 'relics.json'), 'w', encoding='utf-8') as fh:
        json.dump(relics, fh, ensure_ascii=False, indent=1)
    # ---- lang
    for lang, li in (('ja_jp', 0), ('en_us', 1)):
        path = os.path.join(root, 'lang', lang + '.json')
        d = json.load(open(path, encoding='utf-8'))
        for r in relics:
            c, slot = r['character'], r['slot']
            if li == 0:
                name = r['name']
            else:
                name = {'weapon': N.WEAPON[c][1], 'legend': N.LEGEND_EN[c], 'focus': N.FOCUS_EN[c], 'charm': N.CHARM_EN[c]}[slot]
            d[f'item.{NS}.{r["id"]}'] = name
        for c in chars:
            d[f'item.{NS}.{c}_relic_weapon'] = N.WEAPON[c][0] + '【残響】' if li == 0 else N.WEAPON[c][1] + ' (Echo)'
        for rid, a in R.ARTS.items():
            k = f'relic_art.{NS}.{rid}'
            d[k + '.name'] = ('◆ ' if li == 0 else '◆ ') + a['name'][li] + ('（使用）' if li == 0 else ' (use)')
            d[k + '.desc'] = a['desc'][li]
            if a['passive']:
                d[k + '.passive'] = (a['pdesc'] or ('所持中の効果', 'Held effect'))[li]
            if a['hit']:
                d[k + '.hit'] = (a['hdesc'] or ('命中時の効果', 'On-hit effect'))[li]
        for k, v in R.SAYS.items():
            d[k] = v[li]
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1)
    print('arts', len(out), 'relics', len(relics))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

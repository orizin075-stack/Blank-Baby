"""V8 relic programs, rebuilt from the V9 document's prose and the shipped relic_arts.json.

The prose is the V8 program written out (one item per op, fx/sound/self/else left out). Each prose item becomes an
op; where the shipped program had an op of the same kind at that place, its extra settings (a blink's distance, a
knock's force, a chance's else, the fx that followed it) are kept and only the V8 numbers are taken from the prose.
"""
import re

EFF = {'slow': 'slow', 'weakness': 'weakness', 'wither': 'wither', 'poison': 'poison', 'glow': 'glow', 'levitate': 'levitate',
       'nausea': 'nausea', 'fatigue': 'fatigue', 'dark': 'dark', 'blind': 'blind', 'hunger': 'hunger'}
WORDS = {'blink', 'erase', 'knock', 'launch', 'pull', 'slam', 'burn', 'lightning', 'arrows', 'transmute', 'give', 'repair', 'adapt',
         'rewind', 'snapshot', 'freeze', 'disarm', 'behind', 'back', 'heal', 'say', 'food', 'around'}
QUIET = {'fx', 'sound', 'self', 'victim', 'say'}


def split_top(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
        if ch == '・' and depth == 0:
            out.append(cur)
            cur = ''
        else:
            cur += ch
    if cur:
        out.append(cur)
    return [x for x in out if x != '']


def f(x):
    v = float(x)
    return int(v) if v == int(v) else v


def ticks(s):
    return int(round(float(s) * 20))


def parse(s):
    """Prose -> list of ops."""
    ops = []
    for item in split_top(s.strip().rstrip('。')):
        m = re.fullmatch(r'確率([\d.]+)%\[(.*)\]', item)
        if m:
            ops.append({'op': 'chance', 'p': round(float(m.group(1)) / 100, 4), 'ops': parse(m.group(2)) if m.group(2) else []})
            continue
        pats = [
            (r'前方([\d.]+)m/幅([\d.]+)m', lambda m: {'op': 'line', 'r': f(m[1]), 'w': f(m[2])}),
            (r'前方([\d.]+)m/角度([\d.]+)°', lambda m: {'op': 'cone', 'r': f(m[1]), 'a': f(m[2])}),
            (r'半径([\d.]+)m内/最大(\d+)体', lambda m: {'op': 'area', 'r': f(m[1]), 'n': int(m[2])}),
            (r'連鎖最大(\d+)体/半径([\d.]+)m', lambda m: {'op': 'chain', 'n': int(m[1]), 'r': f(m[2])}),
            (r'基準技威力×([\d.]+)', lambda m: {'op': 'dmg', 'm': f(m[1])}),
            (r'行動停止([\d.]+)秒', lambda m: {'op': 'stun', 't': ticks(m[1])}),
            (r'刻印([\d.]+)秒/内部倍率×([\d.]+)', lambda m: {'op': 'mark', 't': ticks(m[1]), 'x': f(m[2])}),
            (r'強化(\w+?)Lv(\d+)/([\d.]+)秒', lambda m: {'op': 'buff', 'e': m[1], 'a': int(m[2]) - 1, 't': ticks(m[3])}),
            (r'(\w+?)Lv(\d+)/([\d.]+)秒', lambda m: {'op': 'eff', 'e': EFF[m[1]], 'a': int(m[2]) - 1, 't': ticks(m[3])}),
            (r'相手の強化解除', lambda m: {'op': 'strip'}),
            (r'状態異常浄化', lambda m: {'op': 'cleanse'}),
            (r'最大HPの([\d.]+)%回復（実装補正前）', lambda m: {'op': 'healpct', 'v': round(float(m[1]) / 100, 4)}),
            (r'防護([\d.]+)秒', lambda m: {'op': 'guard', 't': ticks(m[1])}),
            (r'生存保護([\d.]+)秒', lambda m: {'op': 'undying', 't': ticks(m[1])}),
            (r'反射([\d.]+)秒/半径([\d.]+)m', lambda m: {'op': 'reflect', 't': ticks(m[1]), 'r': f(m[2])}),
            (r'(\w+)を(\d+)体召喚', lambda m: {'op': 'summon', 'k': m[1], 'n': int(m[2])}),
            (r'低体力条件([\d.]+)%', lambda m: {'op': 'execute', 'pct': round(float(m.group(1)) / 100, 4)}),
        ]
        for pat, make in pats:
            m = re.fullmatch(pat, item)
            if m:
                ops.append(make(m))
                break
        else:
            if item in WORDS:
                ops.append({'op': item})
            else:
                raise SystemExit('unknown prose item %r in %r' % (item, s))
    return ops


def align(prose, shipped):
    """The V8 program: the prose's ops, each carrying what the shipped op of its kind at that place had besides the
    numbers, and the shipped program's fx and sound where they were."""
    out = []
    i = 0
    while i < len(shipped) and shipped[i]['op'] in QUIET and shipped[i]['op'] != 'victim':
        out.append(dict(shipped[i]))
        i += 1
    rest = shipped[i:]
    j = 0
    for p in prose:
        found = None
        for k in range(j, min(len(rest), j + 6)):
            if rest[k]['op'] == p['op']:
                found = k
                break
        if found is not None:
            # a self or victim op just before the shipped one belongs to it
            for k in range(j, found):
                if rest[k]['op'] in ('self', 'victim'):
                    out.append(dict(rest[k]))
            o = dict(rest[found])
            for key, v in p.items():
                if key == 'ops':
                    continue
                o[key] = v
            if p['op'] == 'chance':
                o['ops'] = align(p['ops'], rest[found].get('ops', []))
            out.append(o)
            j = found + 1
            while j < len(rest) and rest[j]['op'] in ('fx', 'sound'):
                out.append(dict(rest[j]))
                j += 1
        else:
            if p['op'] == 'chance':
                p = dict(p, ops=align(p['ops'], []))
            out.append(p)
    # the shipped closing fx (an impact flourish on the targets)
    tail = [o for o in rest[j:] if o['op'] == 'fx']
    out.extend(dict(o) for o in tail[-1:])
    return out


def semantic(ops):
    return [o for o in ops if o['op'] not in QUIET]

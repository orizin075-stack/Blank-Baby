"""Unique relic arts for every relic (weapon / focus / charm / legend) and every dungeon replica.

Writes assets/oror_supreme_bosses/relic_arts.json (programs for RelicArts.java) and the matching
tooltip lang entries (ja_jp / en_us). Ops: see RelicArts.java. Base damage is the relic's rank damage
(rank 1: 2000, rank 2: 4000, legend: 1,000,000), so 'm' multipliers are relative to that."""
import json, os, sys

# ------------------------------------------------------------------------------------------- op helpers
def o(op, **k):
    d = {'op': op}
    d.update(k)
    return d

area = lambda r=16, n=64: o('area', r=r, n=n)
near = lambda r=24, n=1: o('near', r=r, n=n)
around = lambda r=4, n=16: o('around', r=r, n=n, exclude=1)
line = lambda r=32, w=2.5: o('line', r=r, w=w)
cone = lambda r=12, a=90: o('cone', r=r, a=a)
chain = lambda n=6, r=10: o('chain', n=n, r=r)
allies = lambda r=16: o('allies', r=r)
me = lambda: o('self')
victim = lambda: o('victim')
dmg = lambda m=1.0, magic=False: o('dmg', m=m, **({'magic': 1} if magic else {}))
stun = lambda t=60: o('stun', t=t)
eff = lambda e, t=100, a=0: o('eff', e=e, t=t, a=a)
burn = lambda s=8: o('burn', s=s)
freeze = lambda t=300: o('freeze', t=t)
mark = lambda t=200, x=2.0: o('mark', t=t, x=x)
knock = lambda f=2.0: o('knock', f=f)
pull = lambda f=1.5: o('pull', f=f)
launch = lambda f=1.6: o('launch', f=f)
slam = lambda f=3.0: o('slam', f=f)
blink = lambda d=10: o('blink', d=d)
back = lambda d=6: o('back', d=d)
behind = lambda: o('behind')
swap = lambda: o('swap')
dash = lambda f=2.4: o('dash', f=f)
leap = lambda f=1.4: o('leap', f=f)
heal = lambda v=20, to=False: o('heal', v=v, **({'to': 1} if to else {}))
healpct = lambda v=1.0, to=False: o('healpct', v=v, **({'to': 1} if to else {}))
buff = lambda e, t=200, a=0, to=False: o('buff', e=e, t=t, a=a, **({'to': 1} if to else {}))
cleanse = lambda to=False: o('cleanse', **({'to': 1} if to else {}))
guard = lambda t=60, to=False: o('guard', t=t, **({'to': 1} if to else {}))
undying = lambda t=200, to=False: o('undying', t=t, **({'to': 1} if to else {}))
adapt = lambda t=200: o('adapt', t=t)
reflect = lambda t=40, r=8: o('reflect', t=t, r=r)
erase = lambda r=16: o('erase', r=r)
strip = lambda steal=False: o('strip', **({'steal': 1} if steal else {}))
execute = lambda pct=0.3: o('execute', pct=pct)
transmute = lambda: o('transmute')
lightning = lambda: o('lightning')
arrows = lambda n=8, d=40: o('arrows', n=n, d=d)
disarm = lambda: o('disarm')
summon = lambda k='wolf', n=2: o('summon', k=k, n=n)
weather = lambda w='clear': o('weather', w=w)
time_ = lambda v=1000: o('time', v=v)
food = lambda: o('food')
repair = lambda v=64: o('repair', v=v)
give = lambda item='gold', n=1: o('give', item=item, n=n)
xp = lambda v=20: o('xp', v=v)
snapshot = lambda: o('snapshot')
rewind = lambda: o('rewind')
fx = lambda p='end_rod', n=24, at='self', **k: o('fx', p=p, n=n, at=at, **k)
sound = lambda s='chime', v=1.0, pi=1.0: o('sound', s=s, v=v, pi=pi)
chance = lambda p, ops, els=None: o('chance', p=p, ops=ops, **({'else': els} if els else {}))
each = lambda ops: o('each', ops=ops)
low = lambda pct, ops: o('low', pct=pct, ops=ops)

def cycle(key, steps):
    """steps: list of (say_key_suffix, ops)."""
    return o('cycle', steps=[{'say': f'relic_art.oror_supreme_bosses.{key}.say{i}', 'ops': ops} for i, (_, ops) in enumerate(steps)])

ARTS = {}      # id -> dict(cast, passive, hit, cd, ja, en, rank)
SAYS = {}      # lang key -> (ja, en)

def art(rid, rank, ja, en, cast, passive=None, hit=None, cd=None):
    """ja / en: (name, cast description, passive description, on-hit description)."""
    ARTS[rid] = dict(id=rid, character=rid.rsplit('_', 2)[0] if rid.endswith('_relic_weapon') else rid.rsplit('_', 1)[0],
                     rank=rank, cast=cast, passive=passive or [], hit=hit or [], cd=cd, ja=ja, en=en)

def says(rid, pairs):
    for i, (j, e) in enumerate(pairs):
        SAYS[f'relic_art.oror_supreme_bosses.{rid}.say{i}'] = (j, e)

BASE_PASSIVE = [me(), buff('resist', 40, 1), buff('strength', 40, 1)]
LEGEND_PASSIVE = [me(), buff('resist', 40, 3), buff('strength', 40, 6), buff('regen', 40, 1)]

# ------------------------------------------------------------------------------------------- themes
THEME = {
    'void': [fx('ash', 40, 'self', s=1.2), fx('rportal', 30), sound('sonic', 0.8, 1.4)],
    'holy': [fx('end_rod', 50, 'ring', r=3.5, y=0.2), fx('end_rod', 30), sound('totem', 0.6, 1.4)],
    'word': [fx('enchant', 80, 'self', s=1.5), sound('chime', 1.0, 0.8)],
    'royal': [fx('end_rod', 40, 'ring', r=4, y=0.1), fx('wax', 30), sound('chime', 1.0, 0.6)],
    'chaos': [fx('witch', 40, s=1.4), fx('firework', 30), sound('mirror', 1.0, 0.7)],
    'alchemy': [fx('wax', 40, s=1.0), fx('happy', 20), sound('smith', 1.0, 1.2)],
    'star': [fx('end_rod', 40, s=1.6), fx('firework', 20), sound('chime', 1.0, 1.6)],
    'tech': [fx('spark', 50, s=1.0), fx('smoke', 20), sound('smith', 1.0, 0.8)],
    'dragon': [fx('wax', 30, 'ring', r=3), fx('spark', 30), sound('roar', 0.5, 1.4)],
    'water': [fx('splash', 80, s=1.5), fx('bubble', 40), sound('chime', 0.8, 0.5)],
    'game': [fx('firework', 40), fx('heart', 8), sound('chime', 1.0, 2.0)],
    'desire': [fx('dragon', 40, s=1.2), fx('heart', 10), sound('mirror', 0.8, 0.6)],
    'force': [fx('explosion', 6, s=1.0), fx('crit', 40), sound('blast', 1.0, 0.7)],
    'story': [fx('enchant', 60), fx('end_rod', 20), sound('totem', 0.5, 1.6)],
    'curse': [fx('sculk', 30, s=1.2), fx('witch', 30), sound('wither', 0.6, 0.8)],
    'arcane': [fx('portal', 80, s=1.4), fx('enchant', 40), sound('spell', 1.0, 1.0)],
    'abyss': [fx('bubble', 40, s=1.6), fx('sculk', 20), sound('roar', 0.6, 0.6)],
    'earth': [fx('blast', 1), fx('compost', 40, s=1.6), sound('anvil', 0.8, 0.5)],
    'light': [fx('end_rod', 60, 'line', r=24), fx('firework', 20), sound('blast', 1.0, 1.6)],
    'tide': [fx('splash', 100, s=2.0), sound('chime', 1.0, 0.4)],
    'mask': [fx('smoke', 40), fx('witch', 20), sound('mirror', 1.0, 1.0)],
    'fate': [fx('end_rod', 40, 'ring', r=3), fx('enchant', 40), sound('chime', 1.0, 1.2)],
    'beast': [fx('crit', 40), fx('angry', 6), sound('roar', 0.5, 1.0)],
    'dream': [fx('firework', 30), fx('dragon', 30), sound('spell', 1.0, 1.4)],
    'evolve': [fx('lava', 10), fx('sculk', 30), sound('roar', 0.6, 1.2)],
    'hunt': [fx('crit', 40), fx('smoke', 20), sound('sonic', 0.6, 1.8)],
    'branch': [fx('end_rod', 40, s=1.4), fx('portal', 40), sound('mirror', 1.0, 1.6)],
    'evil': [fx('sculk', 40), fx('bigsmoke', 20), sound('wither', 0.8, 0.6)],
    'life': [fx('happy', 50, s=1.6), fx('compost', 30), sound('chime', 1.0, 1.0)],
    'cycle': [fx('enchant', 50, 'ring', r=3), fx('portal', 30), sound('chime', 1.0, 0.7)],
    'tree': [fx('happy', 50, s=1.6), fx('compost', 40), sound('chime', 1.0, 1.1)],
    'law': [fx('firework', 40, s=1.5), fx('end_rod', 30), sound('spell', 1.0, 0.8)],
    'toy': [fx('heart', 10), fx('firework', 30), sound('chime', 1.0, 2.0)],
    'brutal': [fx('explosion', 8, s=1.2), fx('crit', 50), sound('anvil', 1.0, 0.6)],
    'tragedy': [fx('dragon', 30), fx('sculk', 20), sound('mirror', 0.8, 0.5)],
    'lab': [fx('happy', 20), fx('witch', 30), sound('spell', 0.8, 1.6)],
    'forbidden': [fx('portal', 60), fx('sculk', 30), sound('spell', 1.0, 0.6)],
    'fallen': [fx('end_rod', 40), fx('ash', 30), sound('totem', 0.6, 0.8)],
    'pact': [fx('wax', 40), fx('happy', 20), sound('chime', 1.0, 0.9)],
}

def T(theme, ops, hitfx='crit'):
    """cast program with the theme's flourish first and target sparks after every selector."""
    return list(THEME[theme]) + ops + [fx(hitfx, 12, 't', s=0.5)]

def rep(n, op):
    return [op] * n

def L(rid, rank, theme, name, cast_desc, cast, passive=None, passive_desc=None, hit=None, hit_desc=None, cd=None, hitfx='crit'):
    """name / *_desc: (ja, en)."""
    ARTS[rid] = dict(id=rid, character=rid[:-len('_relic_weapon')] if rid.endswith('_relic_weapon') else rid.rsplit('_', 1)[0],
                     rank=rank, cast=T(theme, cast, hitfx), passive=passive or [], hit=hit or [], cd=cd,
                     name=name, desc=cast_desc, pdesc=passive_desc, hdesc=hit_desc)

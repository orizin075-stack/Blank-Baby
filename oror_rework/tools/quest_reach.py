"""Replay NightfallFusion's v0.17.18 quest rules on nightfall_quests.json for a mod set: which quests are offered,
whether every offered quest can be reached, and that no 100-level quest is offered without its mod.
Usage: python3 -I quest_reach.py <nightfall_quests.json> minecraft,irons_spellbooks,cataclysm,..."""
import json, sys, re, collections
d = json.load(open(sys.argv[1], encoding='utf-8'))
mods = set(sys.argv[2].split(','))
Q = {q['id']: q for q in d['quests']}
STAND_IN = {'wom:tormented_mind': 'wom:herrscher'}
def item_id(x): return x if isinstance(x, str) else x.get('id', '')
def resolve_item(x):
    i = item_id(x)
    ns = i.split(':')[0]
    if ns in mods: return i
    alt = STAND_IN.get(i)
    return alt if alt and alt.split(':')[0] in mods else None
def resolve_entity(e):
    if e.startswith('tcr_bosses:'):
        p = e.split(':')[1].replace('_humanoid', '')
        p = {'netherite': 'netherite_monstrosity', 'leviathan': 'the_leviathan', 'harbinger': 'the_harbinger'}.get(p, p)
        if 'cataclysm' in mods: return 'cataclysm:' + p
    return e
def needles(x):
    out = []
    def walk(v):
        if isinstance(v, dict): [walk(w) for w in v.values()]
        elif isinstance(v, list): [walk(w) for w in v]
        elif isinstance(v, str) and re.fullmatch(r'[a-z0-9_.-]+:[a-z0-9_./-]+', v): out.append(v)
    if isinstance(x, dict) and 'tag' in x: walk(x['tag'])
    return out
def possible(t):
    if t['type'] == 'item':
        if resolve_item(t['item']) is None: return False
        return all(n.split(':')[0] in mods for n in needles(t['item']))
    if t['type'] == 'kill': return resolve_entity(t['entity']).split(':')[0] in mods
    return True
def available(q):
    # optional tasks are not needed unless nothing else is asked; a dimension alone does not count as asked
    req = [t for t in q['tasks'] if not t.get('optional_task')]
    opt = [t for t in q['tasks'] if t.get('optional_task')]
    asked = any(t['type'] != 'dimension' for t in req)
    return all(possible(t) for t in req) and (asked or any(possible(t) for t in opt))
# simulate a player who completes every available quest whose deps are satisfied, iterating to a fixed point
done = set()
def satisfied(i, depth=0):
    if i in done: return True
    q = Q.get(i)
    return q is not None and depth < 16 and not available(q) and deps(q, depth + 1)
def deps(q, depth=0): return all(satisfied(x, depth) for x in q.get('dependencies', []))
changed = True
while changed:
    changed = False
    for i, q in Q.items():
        if i not in done and available(q) and deps(q):
            done.add(i); changed = True
avail = [i for i, q in Q.items() if available(q)]
stuck = [i for i in avail if i not in done]
by = collections.Counter(Q[i]['chapter'] for i in avail)
print('mods', sorted(mods))
print('available', len(avail), 'of', len(Q), dict(by))
print('reachable', len(done), 'stuck', stuck)
lv = [i for i in avail for r in Q[i].get('rewards', []) if r['type'] == 'xp_levels']
print('100-level quests available:', lv)

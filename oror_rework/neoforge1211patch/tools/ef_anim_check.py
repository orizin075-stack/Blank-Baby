"""ef_anim_check.py <out.txt> <jar or dir> ...: every animation the Epic Fight mob patches (advanced_mobpatch,
epicfight_mobpatch) in the given jars name, checked against the animations the given jars hold
(assets/<ns>/animmodels/animations/<path>.json, Epic Fight's way of storing them in 1.20.1 and 1.21.1 alike; and the
animation names Indestructible, Epic Fight and EpicFight Nightfall register in code, read from their class files as
strings). For the user: "ナイトフォールクラフトの動きとパリイ ... 多分バージョンが合ってなくてできてない": a 1.20.1 patch that names an
animation 1.21.1 does not have is refused whole, and the mob is left without its moves, guards and parries.
Reads jars as zip files only."""
import json, os, re, sys, zipfile

out = sys.argv[1]
paths = sys.argv[2:]
have = set()
patches = {}
ID = re.compile(r'^[a-z0-9_.-]+:[a-z0-9_./-]+$')


def entries(p):
    if os.path.isdir(p):
        for root, _, files in os.walk(p):
            for f in files:
                full = os.path.join(root, f)
                yield os.path.relpath(full, p).replace(os.sep, '/'), (lambda full=full: open(full, 'rb').read())
    else:
        try:
            z = zipfile.ZipFile(p)
        except Exception:
            return
        for n in z.namelist():
            yield n, (lambda n=n, z=z: z.read(n))


for p in paths:
    for n, read in entries(p):
        m = re.match(r'assets/([^/]+)/animmodels/animations/(.+)\.json$', n)
        if m:
            have.add(m.group(1) + ':' + m.group(2))
        if re.match(r'data/[^/]+/(advanced_mobpatch|epicfight_mobpatch|indestructible_mobpatch)/.+\.json$', n):
            try:
                patches[os.path.basename(p) + '!' + n] = json.loads(read().decode('utf-8'))
            except Exception as e:
                patches[os.path.basename(p) + '!' + n] = {'__error__': repr(e)}

refs = {}


def walk(o, where, key=''):
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, where, k)
    elif isinstance(o, list):
        for v in o:
            walk(v, where, key)
    elif isinstance(o, str) and ID.match(o) and '/' in o.split(':', 1)[1]:
        if key in ('model', 'armature', 'renderer') or o.startswith(('epicfight:entity/', 'minecraft:')):
            return
        refs.setdefault(where, {}).setdefault(o, key)


for where, d in patches.items():
    walk(d, where)

lines = []
total_missing = 0
for where in sorted(refs):
    missing = sorted(a for a in refs[where] if a not in have)
    total_missing += len(missing)
    lines.append(f'{where}: {len(refs[where])} animations named, {len(missing)} missing')
    for a in missing:
        lines.append(f'    MISSING {a}  (as {refs[where][a]})')
by_ns = {}
for a in have:
    by_ns[a.split(':')[0]] = by_ns.get(a.split(':')[0], 0) + 1
lines.insert(0, f'animations held: {len(have)} by namespace {dict(sorted(by_ns.items()))}; patches: {len(patches)}; missing in all: {total_missing}')
for ns in ('indestructible', 'epicfightx', 'efn', 'epic_fight_avalon', 'wom'):
    sample = sorted(a for a in have if a.startswith(ns + ':') and any(k in a for k in ('guard', 'parry', 'dodge', 'step', 'counter')))[:60]
    if sample:
        lines.append(f'-- {ns} guard/parry/dodge animations: ' + ' '.join(sample))
open(out, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('\n'.join(lines[:60]))

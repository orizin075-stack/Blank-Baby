"""Which members of the 1.21.1 refs never appear in real 1.20.1 code (Forge + Create + Iron's + Epic Fight + Forge's
Minecraft patches)? Those are the candidates for API that changed between the versions."""
import os, re, sys, collections
roots = sys.argv[2:]
words = collections.Counter()
for r in roots:
    for b, ds, fs in os.walk(r):
        for f in fs:
            if f.endswith(('.java', '.patch')):
                t = open(os.path.join(b, f), encoding='utf-8', errors='ignore').read()
                for w in re.findall(r'[A-Za-z_][A-Za-z0-9_]*', t):
                    words[w] += 1
cur = None; missing = collections.defaultdict(list); total = 0
for l in open(sys.argv[1]):
    l = l.rstrip('\n')
    if not l or l.startswith('#'): continue
    if not l.startswith('\t'):
        cur = l; continue
    if not cur.startswith(('net/minecraft/', 'com/mojang/')): continue
    kind, name = l[1:].split(' ')[:2]
    if kind in ('SUPER_OF', 'IFACE_OF') or name in ('<init>', '<clinit>'): continue
    total += 1
    if words[name] == 0:
        missing[cur].append(l[1:])
    cls = cur.split('/')[-1].split('$')[-1]
for c in sorted(missing): print(c); [print('   ', m) for m in missing[c]]
print('checked', total, 'missing', sum(len(v) for v in missing.values()), file=sys.stderr)
# classes never named in the corpus
cls_missing = set()
cur = None
for l in open(sys.argv[1]):
    l = l.rstrip('\n')
    if l and not l.startswith(('\t', '#')) and l.startswith(('net/minecraft/', 'com/mojang/')):
        n = l.split('/')[-1].split('$')[-1]
        if words[n] == 0: cls_missing.add(l)
print('CLASSES NOT IN CORPUS:', sorted(cls_missing))

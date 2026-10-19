import json, sys
toks = set(json.load(open('ref_tokens.json')))
cur = None; miss = []; n = 0
for line in open(sys.argv[1], encoding='utf-8'):
    line = line.rstrip('\n')
    if not line: continue
    if not line.startswith('\t'):
        cur = line; continue
    p = line[1:].split(' ')
    if p[0] in ('SUPER_OF', 'IFACE_OF') or len(p) < 3: continue
    kind, name, desc = p[0], p[1], p[2]
    if name in ('<init>', '<clinit>'): continue
    if not cur.startswith(('net/minecraft/', 'com/mojang/')): continue
    n += 1
    if name not in toks:
        miss.append(f'{cur} {kind} {name} {desc}')
print('checked', n, 'unseen', len(miss))
print('\n'.join(miss))

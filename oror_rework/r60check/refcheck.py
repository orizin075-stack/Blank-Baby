"""refcheck.py <refs.json> <out.txt> <jar or dir>...: whether the classes, fields and methods named in refs.json (the outside
references of the user's r60 OROR build, and its mixins' targets) exist in the given jars (mods, their nested jars,
Minecraft's), and which packages more than one mod jar carries (a split package stops NeoForge at start)."""
import io, json, os, struct, sys, zipfile, collections

def parse(data):
    if data[:4] != b'\xca\xfe\xba\xbe':
        return None
    pos = 8
    n = struct.unpack('>H', data[pos:pos + 2])[0]; pos += 2
    cp = [None] * n
    i = 1
    while i < n:
        tag = data[pos]; pos += 1
        if tag == 1:
            ln = struct.unpack('>H', data[pos:pos + 2])[0]; pos += 2
            cp[i] = data[pos:pos + ln].decode('utf-8', 'replace'); pos += ln
        elif tag in (3, 4):
            pos += 4
        elif tag in (5, 6):
            pos += 8; i += 1
        elif tag == 7:
            cp[i] = ('class', struct.unpack('>H', data[pos:pos + 2])[0]); pos += 2
        elif tag in (8, 16, 19, 20):
            pos += 2
        elif tag in (9, 10, 11, 12, 17, 18):
            pos += 4
        elif tag == 15:
            pos += 3
        else:
            raise ValueError(tag)
        i += 1
    cls = lambda k: cp[cp[k][1]]
    pos += 2
    this, sup = struct.unpack('>HH', data[pos:pos + 4]); pos += 4
    ni = struct.unpack('>H', data[pos:pos + 2])[0]; pos += 2
    ifaces = [cls(struct.unpack('>H', data[pos + 2 * k:pos + 2 * k + 2])[0]) for k in range(ni)]; pos += 2 * ni
    members = {'field': set(), 'method': set()}
    for kind in ('field', 'method'):
        cnt = struct.unpack('>H', data[pos:pos + 2])[0]; pos += 2
        for _ in range(cnt):
            _, nm, ds, ac = struct.unpack('>HHHH', data[pos:pos + 8]); pos += 8
            members[kind].add((cp[nm], cp[ds]))
            for _ in range(ac):
                ln = struct.unpack('>I', data[pos + 2:pos + 6])[0]; pos += 6 + ln
    return {'name': cls(this), 'super': cls(sup) if sup else None, 'ifaces': ifaces, 'members': members}

classes, where, packages = {}, {}, collections.defaultdict(set)

def scan(z, label, top):
    for n in z.namelist():
        if n.endswith('.class') and not n.startswith('META-INF/versions/'):
            try:
                c = parse(z.read(n))
            except Exception:
                continue
            if c and c['name'] not in classes:
                classes[c['name']] = c; where[c['name']] = label
            if top and '/' in n:
                packages[n.rsplit('/', 1)[0]].add(label)
        elif n.endswith('.jar'):
            try:
                scan(zipfile.ZipFile(io.BytesIO(z.read(n))), label + '!' + n.rsplit('/', 1)[-1], False)
            except Exception:
                pass

jars = []
for a in sys.argv[3:]:
    if os.path.isdir(a):
        for root, _, fs in os.walk(a):
            jars += [os.path.join(root, f) for f in fs if f.endswith('.jar')]
    else:
        jars.append(a)
for j in jars:
    try:
        scan(zipfile.ZipFile(j), os.path.basename(j), '/mods/' in j or '/libs/' in j or 'r60extra' in j or 'pack053' in j)
    except Exception as e:
        print('unreadable', j, e)

def find(owner, kind, name, desc):
    c = classes.get(owner)
    if c is None:
        return None
    if any(m[0] == name and (desc is None or m[1] == desc) for m in c['members'][kind]):
        return owner
    for s in [c['super']] + c['ifaces']:
        if s:
            r = find(s, kind, name, desc)
            if r:
                return r
    return False

spec = json.load(open(sys.argv[1]))
out = []
bad = 0
for r in spec['refs']:
    if r['kind'] == 'class':
        ok = r['owner'] in classes
        st = 'ok (%s)' % where[r['owner']] if ok else 'MISSING CLASS'
    else:
        f = find(r['owner'], 'field' if r['kind'] == 'field' else 'method', r['name'], r['desc'])
        st = 'unknown owner (not in these jars)' if f is None else 'ok' if f else 'MISSING'
        ok = f is not False
    bad += 0 if ok else 1
    out.append('%-14s %s %s.%s%s' % (st, r['kind'], r['owner'], r['name'], r['desc']))
out.append('')
for m in spec['mixins']:
    for t in m['targets']:
        c = classes.get(t)
        if c is None:
            out.append('MIXIN %s -> %s: TARGET CLASS NOT IN THE PACK' % (m['mixin'], t)); continue
        own = [x for x in c['members']['method'] if x[0] == m['method'] and (m['desc'] is None or x[1] == m['desc'])]
        inh = find(t, 'method', m['method'], m['desc'])
        out.append('MIXIN %s -> %s.%s: %s (%s)' % (m['mixin'], t, m['method'], 'declared ' + str(own) if own else
                   'NOT DECLARED HERE (inherited from %s: an @Inject on it fails)' % inh if inh else 'NOT FOUND', where[t]))
out.append('')
split = {p: sorted(l) for p, l in packages.items() if len(l) > 1}
out.append('packages in more than one mod jar: %d' % len(split))
for p, l in sorted(split.items())[:200]:
    out.append('  %s: %s' % (p, ', '.join(l)))
out.append('')
out.append('refs not found: %d of %d; classes indexed %d from %d jars' % (bad, len(spec['refs']), len(classes), len(jars)))
open(sys.argv[2], 'w').write('\n'.join(out) + '\n')
print('\n'.join(out[-3:]))

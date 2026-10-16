"""Generate compile-only Java stubs for external APIs referenced by the mod.
Erased signatures come from bytecode refs; hierarchy/generics come from overrides.py."""
import os, re, sys, shutil
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from overrides import OV, EXTRA_CLASSES

refs_path, out_dir = sys.argv[1], sys.argv[2]
classes = defaultdict(list)
cur = None
for line in open(refs_path):
    line = line.rstrip('\n')
    if not line.startswith('\t'):
        cur = line; classes[cur]
    else:
        classes[cur].append(line[1:])
extra = os.path.join(os.path.dirname(refs_path), 'extra_refs.txt')
if os.path.exists(extra):
    cur = None
    for line in open(extra):
        line = line.rstrip('\n')
        if not line or line.startswith('#'): continue
        if not line.startswith('\t'): cur = line; classes[cur]
        elif line[1:] not in classes[cur]: classes[cur].append(line[1:])
for c in EXTRA_CLASSES:
    classes[c]
for c in OV:
    classes[c]

SKIP_PREFIX = ('com/google/gson', 'com/google/common', 'org/joml', 'it/unimi', 'io/netty')

def jtype(t):
    """descriptor fragment -> java source type (erased)"""
    arr = 0
    while t.startswith('['):
        arr += 1; t = t[1:]
    prim = {'Z':'boolean','B':'byte','C':'char','S':'short','I':'int','J':'long','F':'float','D':'double','V':'void'}
    if t in prim: base = prim[t]
    else: base = t[1:-1].replace('/', '.').replace('$', '.')
    return base + '[]' * arr

def split_desc(d):
    m = re.match(r'\((.*)\)(.*)', d)
    args, ret = m.group(1), m.group(2)
    out = []; i = 0
    while i < len(args):
        j = i
        while args[j] == '[': j += 1
        if args[j] == 'L': j = args.index(';', j)
        out.append(args[i:j+1]); i = j + 1
    return out, ret

def default_ret(t):
    if t == 'void': return ''
    if t == 'boolean': return 'return false;'
    if t in ('byte','char','short','int','long','float','double'): return 'return 0;'
    return 'return null;'

def simple(c): return c.split('/')[-1]

# group nested classes under top-level
top = defaultdict(list)
for c in classes:
    if c.startswith(SKIP_PREFIX): continue
    top[c.split('$')[0]].append(c)

def kind_of(c):
    o = OV.get(c, {})
    if 'kind' in o: return o['kind']
    ents = classes[c]
    if any(e.startswith(('IMI ', 'SMI ', 'VMI ')) for e in ents): return 'interface'
    for oc, ents2 in classes.items():
        pass
    return 'class'

iface_of = set()
for c, ents in classes.items():
    for e in ents:
        if e.startswith('IFACE_OF'): iface_of.add(c)

CLASS_RETENTION = {'org/spongepowered/asm/mixin/Mixin', 'org/spongepowered/asm/mixin/Pseudo'}

def render_class(c, indent, nested=False):
    o = OV.get(c, {})
    k = o.get('kind') or ('interface' if c in iface_of else kind_of(c))
    name = simple(c).split('$')[-1]
    tp = o.get('tparams', '')
    ext = o.get('extends')
    impl = o.get('implements')
    mods = 'public ' + ('static ' if nested and k in ('class', 'enum') else '')
    head = {'class': 'class', 'interface': 'interface', 'enum': 'enum', 'annotation': '@interface'}[k]
    s = f"{indent}{mods}{head} {name}{tp}"
    if k == 'annotation':
        # retention must match the real library: NeoForge / Minecraft annotations are read at runtime (event bus,
        # @Mod, game tests); Mixin's own annotations are CLASS retention
        pol = 'CLASS' if c in CLASS_RETENTION else 'RUNTIME'
        s = f"{indent}@java.lang.annotation.Retention(java.lang.annotation.RetentionPolicy.{pol})\n" + s
    if ext and k in ('class', 'interface'): s += f" extends {ext}"
    if impl and k in ('class', 'enum'): s += f" implements {impl}"
    lines = [s + ' {']
    I = indent + '    '
    drop = set(o.get('drop', []))
    def declared(ms):
        out=set()
        for m in ms:
            mm = re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*(\(|;|=)', m)
            if mm: out.add(mm.group(1))
        return out
    drop |= declared(o.get('members', []))
    # members declared in ancestor overrides must not be redeclared with erased types
    anc = o.get('extends')
    while anc:
        key = anc.split('<')[0].replace('.', '/')
        cand = [k2 for k2 in OV if k2.replace('$', '/') == key]
        if not cand: break
        drop |= declared(OV[cand[0]].get('members', []))
        anc = OV[cand[0]].get('extends')
    body = []
    enum_consts = []
    seen = set()
    for e in classes[c]:
        if e.startswith(('SUPER_OF', 'IFACE_OF')): continue
        parts = e.split(' ')
        kindtag, mname, desc = parts[0], parts[1], parts[2]
        if mname in drop: continue
        key = (mname, desc)
        if key in seen: continue
        if kindtag not in ('OVRP', 'OVR') and ('OVRP ' + mname + ' ' + desc) in classes[c] and kindtag not in ('SF', 'VF'):
            continue
        seen.add(key)
        if kindtag in ('SF', 'VF'):
            t = jtype(desc)
            if k == 'enum' and kindtag == 'SF' and desc == 'L' + c + ';':
                enum_consts.append(mname); continue
            if k == 'interface':
                dv = {'boolean':'false','int':'0','long':'0L','float':'0f','double':'0d'}.get(t, 'null')
                body.append(f"{I}{t} {mname} = {dv};")
            else:
                body.append(f"{I}public {'static ' if kindtag=='SF' else ''}{t} {mname};")
            continue
        if kindtag in ('OVR', 'OVRP'):
            if any((mname, desc2) in seen for desc2 in [desc]) and False: pass
        args, ret = split_desc(desc)
        params = ', '.join(f"{jtype(a)} p{i}" for i, a in enumerate(args))
        if mname == '<init>':
            if k == 'enum': continue
            body.append(f"{I}public {name}({params}) {{}}")
            continue
        if mname == '<clinit>': continue
        rt = jtype(ret)
        static = kindtag.startswith('SM')
        if k == 'enum' and mname in ('values', 'valueOf', 'ordinal', 'name', 'compareTo', 'equals', 'hashCode', 'toString', 'getDeclaringClass'):
            continue
        if mname in ('equals', 'hashCode', 'toString', 'getClass') and not static:
            continue
        if k == 'interface':
            if static: body.append(f"{I}static {rt} {mname}({params}) {{ {default_ret(rt)} }}")
            elif o.get('functional') == mname: body.append(f"{I}{rt} {mname}({params});")
            else: body.append(f"{I}default {rt} {mname}({params}) {{ {default_ret(rt)} }}")
        elif k == 'annotation':
            pass
        else:
            acc = 'protected' if kindtag == 'OVRP' else 'public'
            body.append(f"{I}{acc} {'static ' if static else ''}{rt} {mname}({params}) {{ {default_ret(rt)} }}")
    if k == 'enum':
        consts = enum_consts + [x for x in o.get('consts', []) if x not in enum_consts]
        lines.append(I + (', '.join(consts) if consts else '') + ';')
    if k == 'class':
        lines.append(f"{I}public {name}() {{}}" if not any(b.strip().startswith(f'public {name}()') for b in body) else '')
    for b in o.get('members', []):
        lines.append(I + b)
    lines += body
    # nested
    for nc in sorted(classes):
        if nc.startswith(c + '$') and '$' not in nc[len(c)+1:] and not nc.startswith(SKIP_PREFIX):
            lines += render_class(nc, I, True)
    lines.append(indent + '}')
    return lines

if os.path.exists(out_dir): shutil.rmtree(out_dir)
n = 0
for t, members in top.items():
    pkg = '/'.join(t.split('/')[:-1])
    d = os.path.join(out_dir, pkg)
    os.makedirs(d, exist_ok=True)
    src = [f"package {pkg.replace('/', '.')};", ""]
    o = OV.get(t, {})
    for imp in o.get('imports', []): src.append(f"import {imp};")
    src += render_class(t, '')
    with open(os.path.join(d, simple(t) + '.java'), 'w') as f:
        f.write('\n'.join(src) + '\n')
    n += 1
print('stub files', n)

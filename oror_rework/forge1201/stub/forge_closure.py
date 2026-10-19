"""Forge 1.20.1 source files the port needs: the Forge-family classes our sources import, and every Forge-family type
their public signatures mention (found through the skeletons, so method bodies do not drag in internals).

  python3 -I forge_closure.py <our sources> <skeleton out dir> <roots...>   (prints the file list)
"""
import os, re, subprocess, sys
ours, skel, roots = sys.argv[1], sys.argv[2], sys.argv[3:]
index = {}
for r in roots:
    for b, ds, fs in os.walk(r):
        for f in fs:
            if f.endswith('.java'):
                rel = os.path.relpath(os.path.join(b, f), r)[:-5].replace(os.sep, '.')
                index.setdefault(rel, os.path.join(b, f))

def resolve(fqn):
    parts = fqn.split('.')
    for i in range(len(parts), 0, -1):
        k = '.'.join(parts[:i])
        if k in index:
            return k
    return None

todo = set()
for b, ds, fs in os.walk(ours):
    for f in fs:
        if f.endswith('.java'):
            t = open(os.path.join(b, f), encoding='utf-8').read()
            for m in re.findall(r'import (?:static )?((?:net\.minecraftforge|org\.spongepowered\.asm\.mixin)\.[\w.]+)', t):
                k = resolve(m)
                if k: todo.add(k)
            for m in re.findall(r'\b((?:net\.minecraftforge|org\.spongepowered\.asm\.mixin)\.[\w.]+)', t):
                k = resolve(m)
                if k: todo.add(k)
# Forge's patches make these Minecraft classes implement its extension interfaces; their methods are overridden/called
for seed in ['net.minecraftforge.common.extensions.IForgeItem', 'net.minecraftforge.common.extensions.IForgeEntity',
             'net.minecraftforge.common.extensions.IForgeLivingEntity', 'net.minecraftforge.common.extensions.IForgeItemStack']:
    todo.add(seed)
done = set()
os.makedirs(skel, exist_ok=True)
here = os.path.dirname(os.path.abspath(__file__))
while todo:
    batch = sorted(todo - done)
    if not batch: break
    done |= set(batch)
    todo = set()
    subprocess.run(['java', os.path.join(here, 'Skeleton.java'), skel] + [index[k] for k in batch], check=True,
                   env=dict(os.environ, JAVA_TOOL_OPTIONS=''), stderr=subprocess.DEVNULL)
    for k in batch:
        out = os.path.join(skel, k.replace('.', '/') + '.java')
        if not os.path.exists(out): continue
        t = open(out, encoding='utf-8').read()
        pkg = k.rsplit('.', 1)[0]
        for m in re.findall(r'import (?:static )?((?:net\.minecraftforge|org\.spongepowered\.asm\.mixin)\.[\w.]+)', t):
            r = resolve(m)
            if r and r not in done: todo.add(r)
        body = t.split('\n', 1)[1]
        for w in set(re.findall(r'\b([A-Z]\w*)\b', body)):
            r = pkg + '.' + w
            if r in index and r not in done: todo.add(r)
print(len(done), 'files', file=sys.stderr)
for k in sorted(done): print(index[k])

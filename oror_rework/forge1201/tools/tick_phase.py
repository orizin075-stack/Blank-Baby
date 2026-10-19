"""Forge 1.20.1 fires each TickEvent twice (START and END); NeoForge's .Post handlers ran once, after the tick.
Adds an END-phase check to every handler and swaps the accessors (getLevel() -> level, getEntity() -> player)."""
import os, re, sys
ROOT = sys.argv[1]
SIG = re.compile(r'(public |private |protected )?static void \w+\((?:net\.minecraftforge\.event\.)?(?:TickEvent\.)?(PlayerTickEvent|LevelTickEvent|ServerTickEvent|ClientTickEvent) (\w+)\) \{')
ACC = {'PlayerTickEvent': [('getEntity()', 'player')], 'LevelTickEvent': [('getLevel()', 'level')], 'ServerTickEvent': [], 'ClientTickEvent': []}
for base, dirs, files in os.walk(ROOT):
    for f in files:
        if not f.endswith('.java'): continue
        p = os.path.join(base, f); s = open(p, encoding='utf-8').read(); o = s
        out, i = [], 0
        for m in SIG.finditer(s):
            start = m.end()
            depth, j = 1, start
            while depth:
                c = s[j]
                if c == '{': depth += 1
                elif c == '}': depth -= 1
                j += 1
            body = s[start:j]
            kind, var = m.group(2), m.group(3)
            for a, b in ACC[kind]:
                body = body.replace(var + '.' + a, var + '.' + b)
            guard = f'\n        if ({var}.phase != net.minecraftforge.event.TickEvent.Phase.END) {{\n            return;\n        }}'
            out.append(s[i:start]); out.append(guard + body); i = j
        out.append(s[i:]); s = ''.join(out)
        if 'TickEvent' in s and 'import net.minecraftforge.event.TickEvent.' in s:
            # an imported nested class needs its outer class for the phase constant only through the full name used above
            pass
        if s != o:
            open(p, 'w', encoding='utf-8').write(s); print('phase', os.path.relpath(p, ROOT))

import os, re, sys, json
# token index of identifiers used after '.' or '::' or as method declarations in 1.20.1 reference sources
roots = sys.argv[1:]
toks = set()
for r in roots:
    for b, d, fs in os.walk(r):
        if '/.git' in b: continue
        for f in fs:
            if not f.endswith('.java'): continue
            try: s = open(os.path.join(b, f), encoding='utf-8', errors='ignore').read()
            except: continue
            toks.update(re.findall(r'(?:\.|::)\s*([A-Za-z_$][\w$]*)', s))
            toks.update(re.findall(r'\b([a-z][\w$]*)\s*\(', s))
            toks.update(re.findall(r'\b([A-Z][A-Z0-9_]+)\b', s))
json.dump(sorted(toks), open('ref_tokens.json', 'w'))
print(len(toks))

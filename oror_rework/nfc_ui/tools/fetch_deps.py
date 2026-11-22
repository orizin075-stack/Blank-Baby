"""fetch_deps.py <mods dir> <server log> <fetched.txt>: for each mandatory dependency Forge reports missing ("Mod ID: 'x',
Requested by: ..., Actual version: '[MISSING]'"), look the mod up on CurseForge by its id as a slug (CFWidget) and put its
newest Forge 1.20.1 file into <mods dir>. Each dependency is tried once (fetched.txt). Exit 0 if anything was fetched."""
import json, os, re, sys, urllib.parse, urllib.request

mods, log, done_path = sys.argv[1:4]
H = {'User-Agent': 'Mozilla/5.0 (oror-nightfall-ci)', 'Accept': 'application/json'}
tried = set(l.split('\t')[0] for l in open(done_path, encoding='utf-8')) if os.path.exists(done_path) else set()
text = open(log, encoding='utf-8', errors='replace').read() if os.path.exists(log) else ''
missing = sorted(set(m.group(1) for m in re.finditer(r"Mod ID: '([^']+)', Requested by: '[^']+', Expected range: '[^']*', Actual version: '\[MISSING\]'", text)))
got = 0
with open(done_path, 'a', encoding='utf-8') as out:
    for dep in missing:
        if dep in tried:
            continue
        note = 'not found'
        for slug in dict.fromkeys([dep, dep.replace('_', '-'), dep + '-forge', dep.replace('engine', '-engine'), dep.replace('lib', '-lib')]):
            try:
                d = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.cfwidget.com/minecraft/mc-mods/' + slug, headers=H), timeout=60).read())
            except Exception:
                continue
            fit = [f for f in d.get('files') or [] if '1.20.1' in (f.get('versions') or []) and 'Forge' in (f.get('versions') or [])]
            fit.sort(key=lambda f: f.get('id', 0), reverse=True)
            if not fit:
                note = f'{slug}: no Forge 1.20.1 file'
                continue
            f = fit[0]
            url = f"https://mediafilez.forgecdn.net/files/{f['id'] // 1000}/{f['id'] % 1000}/" + urllib.parse.quote(f['name'])
            try:
                body = urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=300).read()
            except Exception as e:
                note = f'{slug}: download failed {e}'
                continue
            open(os.path.join(mods, f['name']), 'wb').write(body)
            note = f"fetched {f['name']} ({d.get('title')}, project {d.get('id')})"
            got += 1
            break
        out.write(f'{dep}\t{note}\n')
        print(dep, '-', note)
sys.exit(0 if got else 1)

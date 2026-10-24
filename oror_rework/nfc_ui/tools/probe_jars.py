"""What NightfallCraft's UI mods carry for the HUD and GUI: overridden vanilla GUI textures, their own GUI textures,
built-in resource packs, and the mixin classes that touch the HUD or screens.

  python3 -I probe_jars.py <out dir> <projectID:fileID>...

Each file is found by id in its project's CurseForge listing, fetched from the CDN, and summarised to
<out dir>/<file name>.txt. Only names are written, no file contents.
"""
import io, json, os, re, sys, urllib.parse, urllib.request, zipfile

AGENT = {'User-Agent': 'Mozilla/5.0 (oror-nightfall-ci)', 'Accept': 'application/json'}
GUI_CLASS = re.compile(r'(Gui|Hud|HUD|Screen|Inventory|Overlay|Hotbar|Tooltip|Menu|Button|Widget)', re.I)


def get(url, raw=False):
    with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=300) as r:
        data = r.read()
    return data if raw else json.loads(data.decode('utf-8'))


def name_of(pid, fid):
    for page in range(12):
        listing = get(f'https://www.curseforge.com/api/v1/mods/{pid}/files?pageIndex={page}&pageSize=50&sort=dateCreated&sortDescending=true&removeAlphas=false')
        for f in listing.get('data', []):
            if f['id'] == fid:
                return f['fileName']
        if len(listing.get('data', [])) < 50:
            return None
    return None


def summarise(data, lines, depth=0):
    jar = zipfile.ZipFile(io.BytesIO(data))
    names = jar.namelist()
    pad = '  ' * depth
    for meta in ('META-INF/mods.toml', 'META-INF/neoforge.mods.toml'):
        if meta in names:
            ids = re.findall(r'^\s*modId\s*=\s*"([^"]+)"', jar.read(meta).decode('utf-8', 'replace'), re.M)
            lines.append(f'{pad}mod ids: {ids}')
    vanilla_gui = [n for n in names if re.match(r'(.*/)?assets/minecraft/textures/gui/', n) and not n.endswith('/')]
    lines.append(f'{pad}vanilla GUI texture overrides: {len(vanilla_gui)}')
    lines += [pad + '  ' + n for n in vanilla_gui[:80]]
    own_gui = [n for n in names if re.match(r'assets/(?!minecraft/)[^/]+/textures/(gui|hud|ui|screen|menu)/', n) and not n.endswith('/')]
    lines.append(f'{pad}own GUI textures: {len(own_gui)}')
    lines += [pad + '  ' + n for n in own_gui[:150]]
    packs = sorted({n.split('/')[0] + '/' + n.split('/')[1] for n in names if n.startswith(('resourcepacks/', 'packs/')) and n.count('/') > 1})
    lines.append(f'{pad}built-in packs: {packs}')
    mixins = [n for n in names if n.endswith('.json') and 'mixin' in n.lower() and '/' not in n]
    for m in mixins:
        try:
            spec = json.loads(jar.read(m))
        except Exception:
            continue
        classes = [c for key in ('mixins', 'client') for c in spec.get(key, []) or []]
        gui = [c for c in classes if GUI_CLASS.search(c)]
        lines.append(f'{pad}mixins {m}: {len(classes)} classes, GUI/HUD ones: {gui[:60]}')
    for n in names:
        if n.startswith('META-INF/jarjar/') and n.endswith('.jar') and depth == 0:
            lines.append(f'{pad}jar-in-jar {n}')
            summarise(jar.read(n), lines, depth + 1)


def main(out, *specs):
    os.makedirs(out, exist_ok=True)
    for spec in specs:
        pid, fid = map(int, spec.split(':'))
        name = name_of(pid, fid)
        if not name:
            open(os.path.join(out, f'{pid}_{fid}.txt'), 'w').write('file not found in the listing\n')
            continue
        data = get(f'https://mediafilez.forgecdn.net/files/{fid // 1000}/{fid % 1000}/' + urllib.parse.quote(name), raw=True)
        lines = [f'== {name} ({pid}:{fid}) {len(data)} bytes']
        try:
            summarise(data, lines)
        except zipfile.BadZipFile:
            lines.append('not a zip')
        safe = re.sub(r'[^A-Za-z0-9._-]', '_', name)
        open(os.path.join(out, safe + '.txt'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
        print(lines[0])


if __name__ == '__main__':
    main(sys.argv[1], *sys.argv[2:])

"""Checks for OROR War x Nightfall 0.17.25: NightfallCraft's UI and combat-feel mods added to the 0.17.23 pack.

  python3 -I pack_tools.py resolve <additions.json> <nightfall-mods.json> <survey.json> <out resolved.json>
  python3 -I pack_tools.py fetch <resolved.json> <out dir> <out lock.json>
  python3 -I pack_tools.py fetchpack <manifest.json> <lock.json> <out dir> <skipped name prefix>...
  python3 -I pack_tools.py depcheck <mods dir> <out report.txt>
  python3 -I pack_tools.py items <mods dir> <nightfallcraft epicfight-client.toml> <out items.json>
  python3 -I pack_tools.py setitems <epicfight-client.toml> <items.json>
  python3 -I pack_tools.py search <out.json> <name>...
  python3 -I pack_tools.py nfcfetch <nightfallcraft-2.2.8.6-mods.json> <game dir> <out files.json>
  python3 -I pack_tools.py menu <tcrcore jar> <fancymenu customization dir> <game dir> <out members.json>

resolve: the additions' newest NeoForge 1.21.1 file where none is pinned (CurseForge site API), and for NightfallCraft's
  projects without 1.21.1 files, the name of the file NightfallCraft used and the project's newest files.
fetch: the additions from CurseForge's CDN into <out dir>/{mods,resourcepacks,shaderpacks}, with their SHA-256.
fetchpack: every jar of a released pack's lock (name -> SHA-256) whose name has none of the prefixes, found on the CDN
  under one of the manifest's file ids and checked against the lock.
depcheck: every jar's (and jar-in-jar's) neoforge.mods.toml against the others: missing or out-of-range required
  dependencies, incompatible mods present, the same mod id twice.
items: Epic Fight's combat_preferred_items for the pack: NightfallCraft's list where the item exists in some jar, plus
  every item with an Epic Fight weapon capability file (data/<ns>/capabilities/weapons/<item>.json).
search: CurseForge projects with NeoForge 1.21.1 files matching each name (ports often live under a new project).
nfcfetch: every file of NightfallCraft 2.2.8.6's manifest (names looked up by file id), into mods, resourcepacks or
  shaderpacks by the modlist category, for running NightfallCraft itself as the reference.
setitems: writes that list into an epicfight-client.toml.
menu: the TCR Core images NightfallCraft's FancyMenu layouts use, copied from the 1.20.1 jar to the paths the converted
  layouts read ([source:local]/config/fancymenu/assets/nightfallcraft/...), plus the widget sheet, menu cover,
  separators and tabs OROR builds NightfallCraft's menu sprites from, with each image's SHA-256 for the installer.
"""
import concurrent.futures, hashlib, io, json, os, re, sys, time, tomllib, urllib.parse, urllib.request, zipfile

AGENT = {'User-Agent': 'Mozilla/5.0 (oror-nightfall-ci)', 'Accept': 'application/json'}
CDN = 'https://mediafilez.forgecdn.net/files/{}/{}/{}'
FILES = 'https://www.curseforge.com/api/v1/mods/{}/files?pageIndex={}&pageSize=50&sort=dateCreated&sortDescending=true&removeAlphas=false'
FOLDER = {'mod': 'mods', 'resourcepack': 'resourcepacks', 'shader': 'shaderpacks'}


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=60) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503):
                return None
        except Exception:
            pass
        time.sleep(3 * (attempt + 1))
    return None


def listing(pid, pages=4):
    out = []
    for page in range(pages):
        data = get(FILES.format(pid, page))
        if not data or not data.get('data'):
            break
        out += data['data']
        if len(data['data']) < 50:
            break
    return out


def resolve(additions, nightfall, survey, out):
    entries = json.load(open(additions, encoding='utf-8'))
    for e in entries:
        if e.get('fileID'):
            continue
        if not e.get('projectID'):
            data = get('https://www.curseforge.com/api/v1/mods/search?gameId=432&index=0&pageSize=20&sortField=1&classId=6'
                       '&filterText=' + urllib.parse.quote(e['slug']))
            e['projectID'] = next((d.get('id') for d in (data or {}).get('data', []) if d.get('slug') == e['slug']), None)
            if not e['projectID']:  # CurseForge's site search refuses scripts; CFWidget maps a slug to its project id
                widget = get('https://api.cfwidget.com/minecraft/mc-mods/' + urllib.parse.quote(e['slug']))
                e['projectID'] = (widget or {}).get('id')
            if not e['projectID']:
                print('no CurseForge project with slug', e['slug'])
                continue
        every = listing(e['projectID'])
        if e.get('show'):
            for f in every[:12]:
                print('  file', e['projectID'], f['id'], f['fileName'], 'releaseType', f.get('releaseType'), f.get('gameVersions'))
        if e.get('skip'):
            print('skipped', e['projectID'], e['why'])
            continue
        files = [f for f in every
                 if '1.21.1' in f.get('gameVersions', []) and 'NeoForge' in f.get('gameVersions', [])
                 and f['fileName'].startswith(e.get('prefix', ''))]
        release = [f for f in files if f.get('releaseType') == 1] or files
        if not release:
            print('no NeoForge 1.21.1 file:', e['projectID'], e['why'])
            continue
        e['fileID'], e['fileName'] = release[0]['id'], release[0]['fileName']
        print('resolved', e['projectID'], e['fileID'], e['fileName'])
    ready = {e.get('slug') for e in entries if e.get('fileID')}
    for e in entries:
        if e.get('needs') and e['needs'] not in ready and e.get('fileID'):
            print('dropped', e['fileName'], 'because', e['needs'], 'is not resolved')
            e['fileID'] = None
    used = {f['projectID']: f['fileID'] for f in json.load(open(nightfall, encoding='utf-8'))['files']}
    missing = []
    for r in json.load(open(survey, encoding='utf-8'))['curseforge']:
        if r['files_1211']:
            continue
        files = listing(r['projectID'], pages=2)
        mine = next((f['fileName'] for f in files if f['id'] == used.get(r['projectID'])), None)
        missing.append({'projectID': r['projectID'], 'nightfallcraft_file': mine,
                        'newest': [{'id': f['id'], 'fileName': f['fileName'], 'versions': f.get('gameVersions')} for f in files[:3]]})
        print('no 1.21.1:', r['projectID'], mine, '| newest:', files[0]['fileName'] if files else None)
        time.sleep(0.3)
    json.dump({'additions': entries, 'nightfallcraft_without_1211': missing}, open(out, 'w', encoding='utf-8'), indent=1,
              ensure_ascii=False)


def fetch(resolved, out, lock):
    entries = json.load(open(resolved, encoding='utf-8'))['additions']
    sums = {}
    for e in entries:
        if not e.get('fileID'):
            continue
        folder = os.path.join(out, FOLDER[e['kind']])
        os.makedirs(folder, exist_ok=True)
        url = CDN.format(e['fileID'] // 1000, e['fileID'] % 1000, urllib.parse.quote(e['fileName']))
        for attempt in range(4):
            try:
                data = urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=300).read()
                break
            except Exception as error:
                if attempt == 3:
                    sys.exit('download failed: ' + url + ' ' + repr(error))
                time.sleep(5)
        open(os.path.join(folder, e['fileName']), 'wb').write(data)
        sums[e['fileName']] = {'projectID': e['projectID'], 'fileID': e['fileID'], 'kind': e['kind'], 'bytes': len(data),
                               'sha256': hashlib.sha256(data).hexdigest()}
        print('fetched', e['kind'], e['fileName'], len(data))
    json.dump(sums, open(lock, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def exists(url):
    try:
        request = urllib.request.Request(url, method='HEAD', headers=AGENT)
        with urllib.request.urlopen(request, timeout=30) as r:
            return r.status == 200
    except Exception:
        return False


def fetchpack(manifest, lock, out, *skip):
    ids = [f['fileID'] for f in json.load(open(manifest, encoding='utf-8'))['files']]
    sums = json.load(open(lock, encoding='utf-8'))
    os.makedirs(out, exist_ok=True)
    unmatched = list(ids)
    with concurrent.futures.ThreadPoolExecutor(24) as pool:
        for name, sha in sorted(sums.items()):
            if name.startswith(skip):
                continue
            urls = [CDN.format(i // 1000, i % 1000, urllib.parse.quote(name)) for i in unmatched]
            hit = next((i for i, ok in zip(unmatched, pool.map(exists, urls)) if ok), None)
            if hit is None:
                sys.exit('not on the CDN under any manifest file id: ' + name)
            unmatched.remove(hit)
            data = urllib.request.urlopen(urllib.request.Request(CDN.format(hit // 1000, hit % 1000, urllib.parse.quote(name)),
                                                                 headers=AGENT), timeout=300).read()
            if hashlib.sha256(data).hexdigest() != sha:
                sys.exit('SHA-256 mismatch: ' + name)
            open(os.path.join(out, name), 'wb').write(data)
            print('fetched', name, hit, len(data))


# Versions compared like Maven's ComparableVersion, which NeoForge uses for dependency ranges.
QUALIFIERS = ['alpha', 'beta', 'milestone', 'rc', 'snapshot', '', 'sp']
ALIASES = {'ga': '', 'final': '', 'release': '', 'cr': 'rc'}


def parse(version):
    root = []
    current, stack, start, digit = root, [root], 0, False

    def item(text, is_digit):
        return ('i', int(text)) if is_digit else ('s', ALIASES.get(text, text))

    def sub():
        nonlocal current
        nested = []
        current.append(('l', nested))
        current = nested
        stack.append(nested)

    version = version.lower()
    for i, c in enumerate(version):
        if c in '.-':
            current.append(('i', 0) if i == start else item(version[start:i], digit))
            start = i + 1
            if c == '-':
                sub()
        elif c.isdigit():
            if not digit and i > start:
                current.append(item(version[start:i], False))
                start = i
                sub()
            digit = True
        else:
            if digit and i > start:
                current.append(item(version[start:i], True))
                start = i
                sub()
            digit = False
    if len(version) > start:
        current.append(item(version[start:], digit))
    for items in reversed(stack):
        while items and (items[-1] in (('i', 0), ('s', '')) or items[-1] == ('l', [])):
            items.pop()
    return ('l', root)


def qualifier(text):
    return (QUALIFIERS.index(text), '') if text in QUALIFIERS else (len(QUALIFIERS), text)


def cmp_item(a, b):
    if a is None:
        return 0 if b is None else -cmp_item(b, None)
    kind, value = a
    if kind == 'i':
        if b is None:
            return 0 if value == 0 else 1
        if b[0] != 'i':
            return 1
        return (value > b[1]) - (value < b[1])
    if kind == 's':
        if b is None:
            other = qualifier('')
        elif b[0] == 's':
            other = qualifier(b[1])
        else:
            return -1
        mine = qualifier(value)
        return (mine > other) - (mine < other)
    if b is None:
        return cmp_item(value[0], None) if value else 0
    if b[0] == 'i':
        return -1
    if b[0] == 's':
        return 1
    for i in range(max(len(value), len(b[1]))):
        x = value[i] if i < len(value) else None
        y = b[1][i] if i < len(b[1]) else None
        result = cmp_item(x, y)
        if result:
            return result
    return 0


def compare(a, b):
    return cmp_item(parse(a), parse(b))


def in_range(version, spec):
    spec = (spec or '').strip()
    if spec in ('', '*'):
        return True
    for part in re.findall(r'[\[(][^\])]*[\])]', spec) or [spec]:
        if not part.startswith(('[', '(')):
            if compare(version, part) >= 0:
                return True
            continue
        low, _, high = part[1:-1].partition(',')
        if ',' not in part:
            if compare(version, low.strip()) == 0:
                return True
            continue
        low, high = low.strip(), high.strip()
        if low and (compare(version, low) < 0 or part[0] == '(' and compare(version, low) == 0):
            continue
        if high and (compare(version, high) > 0 or part[-1] == ')' and compare(version, high) == 0):
            continue
        return True
    return False


def jar_mods(data, name, nested=False):
    """[(modId, version, dependencies, jar)] of one jar and its jar-in-jar members."""
    out = []
    try:
        jar = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        return [('!bad-zip', '', [], name)]
    names = set(jar.namelist())
    manifest = jar.read('META-INF/MANIFEST.MF').decode('utf-8', 'replace') if 'META-INF/MANIFEST.MF' in names else ''
    implementation = re.search(r'^Implementation-Version:\s*(\S+)', manifest, re.M)
    for toml_name in ('META-INF/neoforge.mods.toml', 'META-INF/mods.toml'):
        if toml_name not in names:
            continue
        text = jar.read(toml_name).decode('utf-8', 'replace')
        try:
            spec = tomllib.loads(text)
        except tomllib.TOMLDecodeError as error:
            out.append(('!bad-toml', str(error), [], name))
            break
        deps = spec.get('dependencies', {})
        for mod in spec.get('mods', []):
            version = str(mod.get('version', ''))
            if '${file.jarVersion}' in version:
                version = implementation.group(1) if implementation else version
            mine = deps.get(mod['modId'], []) if isinstance(deps, dict) else []
            out.append((mod['modId'], version, mine, name + (' (jar-in-jar)' if nested else '')))
        break
    if 'META-INF/jarjar/metadata.json' in names:
        for entry in json.loads(jar.read('META-INF/jarjar/metadata.json')).get('jars', []):
            if entry.get('path') in names:
                out += jar_mods(jar.read(entry['path']), name + '!' + entry['path'], True)
    return out


def depcheck(folder, report):
    lines, mods = [], {'minecraft': ('1.21.1', 'game'), 'neoforge': ('21.1.262', 'loader')}
    found = []
    for name in sorted(os.listdir(folder)):
        if name.endswith('.jar'):
            found += jar_mods(open(os.path.join(folder, name), 'rb').read(), name)
    top = {}
    for modid, version, deps, jar in found:
        if modid.startswith('!'):
            lines.append(f'BROKEN {jar}: {modid} {version}')
            continue
        if '(jar-in-jar)' not in jar:
            if modid in top:
                lines.append(f'DUPLICATE mod id {modid}: {top[modid]} and {jar}')
            top[modid] = jar
        if modid not in mods or compare(version, mods[modid][0]) > 0:
            mods[modid] = (version, jar)
    for modid, version, deps, jar in found:
        for dep in deps:
            target = dep.get('modId')
            kind = str(dep.get('type', 'required' if dep.get('mandatory', False) else 'optional')).lower()
            side = str(dep.get('side', 'BOTH')).upper()
            spec = dep.get('versionRange', '')
            present = mods.get(target)
            if kind == 'required':
                if present is None:
                    lines.append(f'MISSING {target} {spec} (side {side}) needed by {modid} [{jar}]')
                elif not in_range(present[0], spec):
                    lines.append(f'VERSION {target} {present[0]} not in {spec} needed by {modid} [{jar}] {json.dumps(dep)}')
            elif kind in ('incompatible', 'discouraged') and present is not None and in_range(present[0], spec):
                lines.append(f'{kind.upper()} {target} {present[0]} with {modid} [{jar}]: {dep.get("reason", "")}')
    head = [f'{len(top)} mods in {len(os.listdir(folder))} files, {len(mods)} mod ids with jar-in-jar', '']
    body = sorted(set(lines)) or ['no problems found']
    listing_ = ['', '== mods'] + [f'{m} {v[0]} [{v[1]}]' for m, v in sorted(mods.items())]
    open(report, 'w', encoding='utf-8').write('\n'.join(head + body + listing_) + '\n')
    print('\n'.join(head + body))


def items(folder, nightfallcraft_client, out):
    present, capability = set(), set()
    lang_key = re.compile(r'"(?:item|block)\.([a-z0-9_.-]+?)\.([a-z0-9_/.-]+)"\s*:')

    def scan(jar):
        for name in jar.namelist():
            m = re.match(r'assets/([a-z0-9_.-]+)/models/item/([a-z0-9_/.-]+)\.json$', name)
            if m:
                present.add(m.group(1) + ':' + m.group(2))
            m = re.match(r'assets/[a-z0-9_.-]+/lang/en_us\.json$', name)
            if m:
                for ns, path in lang_key.findall(jar.read(name).decode('utf-8', 'replace')):
                    present.add(ns + ':' + path)
            m = re.match(r'data/([a-z0-9_.-]+)/capabilities/weapons/([a-z0-9_/.-]+)\.json$', name)
            if m:
                capability.add(m.group(1) + ':' + m.group(2))
            if name.startswith('META-INF/jarjar/') and name.endswith('.jar'):
                scan(zipfile.ZipFile(io.BytesIO(jar.read(name))))

    for name in sorted(os.listdir(folder)):
        if name.endswith('.jar'):
            try:
                scan(zipfile.ZipFile(os.path.join(folder, name)))
            except zipfile.BadZipFile:
                pass
    text = open(nightfallcraft_client, encoding='utf-8').read()
    wanted = re.search(r'combat_preferred_items\s*=\s*\[(.*?)\]', text, re.S).group(1)
    nightfallcraft = re.findall(r'"([a-z0-9_.-]+:[a-z0-9_/.-]+)"', wanted)
    tools = re.compile(r'pickaxe|shovel|_hoe$|paxel|hammer_tool|excavator')
    kept = sorted({i for i in nightfallcraft if i in present or i.startswith('minecraft:')} | {i for i in capability if i in present and not tools.search(i)})
    by_ns = {}
    for i in kept:
        by_ns[i.split(':')[0]] = by_ns.get(i.split(':')[0], 0) + 1
    result = {'combat_preferred_items': kept, 'count_by_namespace': by_ns,
              'nightfallcraft_missing': sorted(i for i in nightfallcraft if i not in present and not i.startswith('minecraft:')),
              'capability_files_without_item': sorted(i for i in capability if i not in present)}
    json.dump(result, open(out, 'w', encoding='utf-8'), indent=1)
    print(len(kept), 'combat items', by_ns, '| NightfallCraft items not in the pack:', len(result['nightfallcraft_missing']))


def search(out, *names):
    found = {}
    for name in names:
        hits = []
        for class_id, loader in ((6, '&gameFlavors[0]=6'), (12, ''), (6552, '')):
            data = get('https://www.curseforge.com/api/v1/mods/search?gameId=432&index=0&pageSize=20&sortField=1&gameVersion=1.21.1'
                       f'&classId={class_id}{loader}&filterText=' + urllib.parse.quote(name))
            for d in (data or {}).get('data', []):
                hits.append({'id': d.get('id'), 'name': d.get('name'), 'slug': d.get('slug'), 'class': class_id,
                             'author': (d.get('author') or {}).get('username') if isinstance(d.get('author'), dict) else d.get('author'),
                             'downloads': d.get('downloads')})
            time.sleep(0.3)
        found[name] = hits if data is not None else 'search failed'
        print(name, '->', [(h['id'], h['name']) for h in hits[:6]] if isinstance(found[name], list) else found[name])
    json.dump(found, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)


def nfcfetch(mods_json, game, out):
    data = json.load(open(mods_json, encoding='utf-8'))
    folder = {'mc-mods': 'mods', 'texture-packs': 'resourcepacks', 'shaders': 'shaderpacks'}

    def one(pair):
        f, ml = pair
        pid, fid = f['projectID'], f['fileID']
        info = get(f'https://www.curseforge.com/api/v1/mods/{pid}/files/{fid}')
        name = ((info or {}).get('data') or {}).get('fileName')
        page = 0
        while not name and page < 40:
            listing = get(FILES.format(pid, page))
            rows = (listing or {}).get('data') or []
            name = next((r['fileName'] for r in rows if r['id'] == fid), None)
            if len(rows) < 50:
                break
            page += 1
        if not name:
            return {'projectID': pid, 'fileID': fid, 'path': ml['path'], 'error': 'name not found'}
        target = os.path.join(game, folder.get(ml['path'].split('/')[0], 'mods'), name)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        url = CDN.format(fid // 1000, fid % 1000, urllib.parse.quote(name))
        for attempt in range(4):
            try:
                body = urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=300).read()
                break
            except Exception as error:
                if attempt == 3:
                    return {'projectID': pid, 'fileID': fid, 'path': ml['path'], 'fileName': name, 'error': repr(error)}
                time.sleep(5)
        open(target, 'wb').write(body)
        return {'projectID': pid, 'fileID': fid, 'path': ml['path'], 'fileName': name, 'bytes': len(body),
                'sha256': hashlib.sha256(body).hexdigest()}

    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        rows = list(pool.map(one, zip(data['files'], data['modlist'])))
    json.dump(rows, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    failed = [r for r in rows if 'error' in r]
    print(len(rows) - len(failed), 'fetched,', len(failed), 'failed:', [(r['path'], r['error']) for r in failed])


def setitems(toml, items_json):
    wanted = json.load(open(items_json, encoding='utf-8'))['combat_preferred_items']
    text = open(toml, encoding='utf-8').read()
    value = '[' + ', '.join('"' + i + '"' for i in wanted) + ']'
    text, n = re.subn(r'^(\s*combat_preferred_items\s*=\s*).*$', lambda m: m.group(1) + value, text, flags=re.M)
    if n != 1:
        sys.exit('no combat_preferred_items line in ' + toml)
    open(toml, 'w', encoding='utf-8').write(text)
    print(len(wanted), 'combat items written to', toml)


def menu(jar_path, customization, game, out):
    prefix = '[source:local]/config/fancymenu/assets/nightfallcraft/'
    wanted = set()
    for name in sorted(os.listdir(customization)):
        text = open(os.path.join(customization, name), encoding='utf-8').read()
        wanted |= {'assets/tcrcore/textures/' + p for p in re.findall(re.escape(prefix) + r'([^\s]+)', text)}
    wanted |= set(GUI_IMAGES)
    jar = zipfile.ZipFile(jar_path)
    members = {}
    for member in sorted(wanted):
        data = jar.read(member)
        target = os.path.join(game, 'config/fancymenu/assets/nightfallcraft', menu_target(member))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        open(target, 'wb').write(data)
        members[member] = hashlib.sha256(data).hexdigest()
    json.dump(members, open(out, 'w', encoding='utf-8'), indent=1)
    print(len(members), 'menu images from', os.path.basename(jar_path))


# TCR Core's images for NightfallCraft's menus outside the FancyMenu layouts (OROR's NightfallCraftGui builds the
# 1.21.1 sprites from them): its widget sheet, menu cover, separators and tabs.
GUI_IMAGES = ['packs/tcr_assets/assets/minecraft/textures/gui/widgets.png', 'assets/tcrcore/textures/menu/background_blurred.png',
              'assets/tcrcore/textures/gui/header_separator.png', 'assets/tcrcore/textures/gui/footer_separator.png'] + [
              f'assets/tcrcore/textures/gui/tab/{n}.png' for n in ('tab', 'tab_highlighted', 'tab_selected', 'tab_selected_highlighted')]


def menu_target(member):
    """Path under config/fancymenu/assets/nightfallcraft, as SETUP_NIGHTFALL.cmd's Menu-Target computes it."""
    for prefix, to in (('assets/tcrcore/textures/', ''), ('packs/tcr_assets/assets/minecraft/textures/', 'minecraft/')):
        if member.startswith(prefix):
            return to + member[len(prefix):]
    raise ValueError(member)


if __name__ == '__main__':
    command, args = sys.argv[1], sys.argv[2:]
    {'resolve': resolve, 'fetch': fetch, 'fetchpack': fetchpack, 'depcheck': depcheck, 'items': items, 'setitems': setitems, 'menu': menu, 'search': search, 'nfcfetch': nfcfetch}[command](*args)

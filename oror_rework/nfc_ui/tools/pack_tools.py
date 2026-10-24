"""Checks for OROR War x Nightfall 0.17.25: NightfallCraft's UI and combat-feel mods added to the 0.17.23 pack.

  python3 -I pack_tools.py resolve <additions.json> <nightfall-mods.json> <survey.json> <out resolved.json>
  python3 -I pack_tools.py fetch <resolved.json> <out dir> <out lock.json>
  python3 -I pack_tools.py fetchpack <manifest.json> <lock.json> <out dir> <skipped name prefix>...
  python3 -I pack_tools.py depcheck <mods dir> <out report.txt>
  python3 -I pack_tools.py items <mods dir> <nightfallcraft epicfight-client.toml> <out items.json>
  python3 -I pack_tools.py setitems <epicfight-client.toml> <items.json>
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
setitems: writes that list into an epicfight-client.toml.
menu: the TCR Core images NightfallCraft's FancyMenu layouts use, copied from the 1.20.1 jar to the paths the converted
  layouts read ([source:local]/config/fancymenu/assets/nightfallcraft/...), with each image's SHA-256 for the installer.
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
        files = [f for f in listing(e['projectID'])
                 if '1.21.1' in f.get('gameVersions', []) and 'NeoForge' in f.get('gameVersions', [])]
        release = [f for f in files if f.get('releaseType') == 1] or files
        if not release:
            print('no NeoForge 1.21.1 file:', e['projectID'], e['why'])
            continue
        e['fileID'], e['fileName'] = release[0]['id'], release[0]['fileName']
        print('resolved', e['projectID'], e['fileID'], e['fileName'])
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


# Maven-style versions and ranges, close enough to NeoForge's for a report.
def tokens(version):
    out = []
    for part in re.split(r'[.\-+_]', version.lower()):
        for t in re.findall(r'\d+|[a-z]+', part):
            out.append((1, int(t), '') if t.isdigit() else (0, 0, t))
    return out


def compare(a, b):
    """A missing part counts as 0, and a qualifier sorts below 0: 1.0-beta < 1.0 = 1.0.0 < 1.0.1."""
    ta, tb = tokens(a), tokens(b)
    zero = (1, 0, '')
    for i in range(max(len(ta), len(tb))):
        x, y = ta[i] if i < len(ta) else zero, tb[i] if i < len(tb) else zero
        if x != y:
            return -1 if x < y else 1
    return 0


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
                    lines.append(f'VERSION {target} {present[0]} not in {spec} needed by {modid} [{jar}]')
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
        wanted |= set(re.findall(re.escape(prefix) + r'([^\s]+)', open(os.path.join(customization, name), encoding='utf-8').read()))
    jar = zipfile.ZipFile(jar_path)
    members = {}
    for path in sorted(wanted):
        data = jar.read('assets/tcrcore/textures/' + path)
        target = os.path.join(game, 'config/fancymenu/assets/nightfallcraft', path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        open(target, 'wb').write(data)
        members['assets/tcrcore/textures/' + path] = hashlib.sha256(data).hexdigest()
    json.dump(members, open(out, 'w', encoding='utf-8'), indent=1)
    print(len(members), 'menu images from', os.path.basename(jar_path))


if __name__ == '__main__':
    command, args = sys.argv[1], sys.argv[2:]
    {'resolve': resolve, 'fetch': fetch, 'fetchpack': fetchpack, 'depcheck': depcheck, 'items': items, 'setitems': setitems, 'menu': menu}[command](*args)

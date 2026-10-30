"""Fetch every mod jar of a CurseForge pack manifest for a dedicated-server test.

  python3 -I fetch_pack.py <manifest.json> <out dir> [<name prefix to leave out>...]

Each file's name comes from CurseForge's site API (the CDN path needs it: files/<id // 1000>/<id % 1000>/<name>); jars
already in the out dir are kept, so a cached dir is only topped up. Prints a line per jar and a summary; resource and
shader packs (not jars) are skipped.
"""
import concurrent.futures, json, os, sys, time, urllib.parse, urllib.request

AGENT = {'User-Agent': 'Mozilla/5.0 (oror-nightfall-ci)', 'Accept': 'application/json'}
CDN = 'https://mediafilez.forgecdn.net/files/{}/{}/{}'
INFO = 'https://www.curseforge.com/api/v1/mods/{}/files/{}'
FILES = 'https://www.curseforge.com/api/v1/mods/{}/files?pageIndex={}&pageSize=50&sort=dateCreated&sortDescending=true&removeAlphas=false'


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


def name_of(pid, fid):
    info = get(INFO.format(pid, fid))
    name = ((info or {}).get('data') or {}).get('fileName')
    page = 0
    while not name and page < 40:
        rows = ((get(FILES.format(pid, page)) or {}).get('data')) or []
        name = next((r['fileName'] for r in rows if r['id'] == fid), None)
        if len(rows) < 50:
            break
        page += 1
    return name


def main(manifest, out, skip):
    files = json.load(open(manifest, encoding='utf-8'))['files']
    os.makedirs(out, exist_ok=True)
    index_path = os.path.join(out, 'index.json')
    index = json.load(open(index_path)) if os.path.exists(index_path) else {}

    def one(f):
        key = f"{f['projectID']}/{f['fileID']}"
        name = index.get(key) or name_of(f['projectID'], f['fileID'])
        if not name:
            return key, None, 'name not found'
        if not name.endswith('.jar'):
            return key, name, 'not a jar'
        if name.lower().startswith(tuple(s.lower() for s in skip)):
            return key, name, 'left out'
        target = os.path.join(out, name)
        if not os.path.exists(target):
            url = CDN.format(f['fileID'] // 1000, f['fileID'] % 1000, urllib.parse.quote(name))
            for attempt in range(4):
                try:
                    data = urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=300).read()
                    open(target, 'wb').write(data)
                    break
                except Exception as e:
                    if attempt == 3:
                        return key, name, 'download failed: ' + repr(e)
                    time.sleep(5)
        return key, name, 'ok'

    with concurrent.futures.ThreadPoolExecutor(12) as pool:
        rows = list(pool.map(one, files))
    for key, name, status in rows:
        if name:
            index[key] = name
        print(f'{status:>14}  {key}  {name}')
    json.dump(index, open(index_path, 'w'), indent=1)
    bad = [r for r in rows if r[2] not in ('ok', 'not a jar', 'left out')]
    print(len([r for r in rows if r[2] == 'ok']), 'jars,', len(bad), 'failed')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2], sys.argv[3:]))

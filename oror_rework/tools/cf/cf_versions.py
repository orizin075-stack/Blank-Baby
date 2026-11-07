"""cf_versions.py <manifest.json> [<our pack manifest.json>]: for each mod of a CurseForge pack (the user's 学びパック, made
for Minecraft 1.20.1 and Forge), whether CurseForge has a file of it for Minecraft 1.21.1 and NeoForge, the newest
such file (its id and name: what the pack's manifest would name), and whether our own pack has the mod already.
Uses CurseForge's site API (the same as fetch_pack.py)."""
import json, sys, time, urllib.request, urllib.error, concurrent.futures

AGENT = {'User-Agent': 'Mozilla/5.0 (oror-nightfall-ci)', 'Accept': 'application/json'}
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


def versions(row):
    v = row.get('gameVersions') or row.get('gameVersionList') or []
    return [str(x).lower() for x in v]


def look(f):
    pid, fid = f['projectID'], f['fileID']
    old = ((get(INFO.format(pid, fid)) or {}).get('data') or {}).get('fileName', '?')
    best = None
    for page in range(12):
        rows = ((get(FILES.format(pid, page)) or {}).get('data')) or []
        for r in rows:
            v = versions(r)
            if '1.21.1' in v and 'neoforge' in v:
                best = r
                break
        if best or len(rows) < 50:
            break
    return pid, fid, old, best


def main(path, ours=None):
    m = json.load(open(path, encoding='utf-8'))
    have = set()
    if ours:
        have = {f['projectID'] for f in json.load(open(ours, encoding='utf-8'))['files']}
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        rows = list(pool.map(look, m['files']))
    n = 0
    for pid, fid, old, best in rows:
        mark = 'IN PACK ' if pid in have else ''
        if best:
            n += 1
            print(f'1.21.1-NEOFORGE {mark}{pid}  {old}  ->  {best["id"]}  {best["fileName"]}')
        else:
            print(f'none-for-1.21.1 {mark}{pid}  {old}')
    print(n, 'of', len(rows), 'have a 1.21.1 NeoForge file')


if __name__ == '__main__':
    main(*sys.argv[1:3])

"""cf_fill.py <manifest.json>: every file of the manifest with "fileID": 0 (a mod added by its project id alone, such as
a library another mod needs) gets the newest file of that project made for Minecraft 1.21.1 and NeoForge; the manifest is
written back. Prints each one filled. Uses CurseForge's site API, as cf_versions.py does."""
import json, sys, time, urllib.request, urllib.error

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


def newest(pid):
    for page in range(12):
        rows = ((get(FILES.format(pid, page)) or {}).get('data')) or []
        for r in rows:
            v = versions(r)
            if '1.21.1' in v and 'neoforge' in v:
                return r
        if len(rows) < 50:
            break
    return None


def main(path):
    m = json.load(open(path, encoding='utf-8'))
    bad = 0
    for f in m['files']:
        if f.get('fileID'):
            continue
        r = newest(f['projectID'])
        if r:
            f['fileID'] = r['id']
            print(f"filled {f['projectID']} -> {r['id']} {r['fileName']}")
        else:
            bad += 1
            print(f"none   {f['projectID']}: no 1.21.1 NeoForge file")
    json.dump(m, open(path, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))

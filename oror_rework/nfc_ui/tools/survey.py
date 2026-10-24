"""Which NightfallCraft 2.2.8.6 mods, shaders and resource packs exist for NeoForge / Minecraft 1.21.1?

  python3 -I survey.py <nightfallcraft-2.2.8.6-mods.json> <out.json>

For each CurseForge project of the NightfallCraft manifest: its slug and name, and its newest files for 1.21.1 (NeoForge
for mods; any loader for shaders and resource packs) from the CurseForge site API. For each modlist slug, the same from
the Modrinth API. Only reads public listings; records every HTTP failure so a blocked source is visible.
"""
import json, sys, time, urllib.parse, urllib.request

AGENT = {'User-Agent': 'Mozilla/5.0 (oror-nightfall-survey)', 'Accept': 'application/json'}


def get(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=30) as r:
                return r.status, json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(5 * (attempt + 1))
                continue
            return e.code, None
        except Exception as e:
            err = type(e).__name__
            time.sleep(2)
    return err, None


def curseforge(pid):
    out = {'projectID': pid}
    status, project = get(f'https://www.curseforge.com/api/v1/mods/{pid}')
    out['project_status'] = status
    if project and 'data' in project:
        d = project['data']
        out['slug'] = d.get('slug')
        out['name'] = d.get('name')
        out['class'] = (d.get('class') or {}).get('slug') if isinstance(d.get('class'), dict) else d.get('classId')
    files = []
    for page in range(6):
        status, listing = get(f'https://www.curseforge.com/api/v1/mods/{pid}/files?pageIndex={page}&pageSize=50&sort=dateCreated&sortDescending=true&removeAlphas=false')
        out['files_status'] = status
        if not listing or not listing.get('data'):
            break
        for f in listing['data']:
            versions = [v.lower() for v in f.get('gameVersions', [])]
            if '1.21.1' in versions:
                files.append({'id': f.get('id'), 'fileName': f.get('fileName'), 'date': f.get('dateCreated') or f.get('dateModified'),
                              'versions': f.get('gameVersions'), 'releaseType': f.get('releaseType')})
        if len(listing['data']) < 50 or len(files) >= 5:
            break
    out['files_1211'] = files[:8]
    return out


def modrinth(slug):
    status, versions = get('https://api.modrinth.com/v2/project/' + urllib.parse.quote(slug) + '/version?game_versions='
                           + urllib.parse.quote('["1.21.1"]'))
    if not isinstance(versions, list):
        return {'status': status}
    keep = []
    for v in versions[:10]:
        keep.append({'version': v.get('version_number'), 'loaders': v.get('loaders'), 'date': v.get('date_published'),
                     'files': [{'name': f['filename'], 'url': f['url'], 'sha512': f['hashes'].get('sha512'), 'size': f['size']}
                               for f in v.get('files', []) if f.get('primary')]})
    return {'status': status, 'versions': keep}


def main(source, out):
    data = json.load(open(source, encoding='utf-8'))
    result = {'curseforge': [], 'modrinth': {}}
    for f in data['files']:
        result['curseforge'].append(curseforge(f['projectID']))
        time.sleep(0.3)
    for m in data['modlist']:
        slug = m['path'].split('/', 1)[1]
        result['modrinth'][m['path']] = {'name': m['name'], **modrinth(slug)}
        time.sleep(0.2)
    json.dump(result, open(out, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    cf_ok = sum(1 for r in result['curseforge'] if r['files_1211'])
    mr_ok = sum(1 for r in result['modrinth'].values() if r.get('versions'))
    statuses = sorted({str(r['project_status']) for r in result['curseforge']} | {str(r.get('files_status')) for r in result['curseforge']})
    print('curseforge projects with 1.21.1 files:', cf_ok, '/', len(result['curseforge']), 'statuses', statuses)
    print('modrinth slugs with 1.21.1 versions:', mr_ok, '/', len(result['modrinth']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

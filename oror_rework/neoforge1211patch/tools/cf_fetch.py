"""Fetch mod jars of the OROR War x Nightfall pack from CurseForge's CDN, verified against the pack lock.

  python3 -I cf_fetch.py <manifest.json> <lock.json> <out dir> <jar file name>...

The pack manifest names CurseForge files by project and file id only; the lock (the jar names and SHA-256 of the tested
0.17.23 pack) gives the names. The CDN path is files/<id // 1000>/<id % 1000>/<name>, so each wanted name is tried
against the manifest's file ids (HEAD) until one exists, then downloaded and checked against the lock's hash.
"""
import hashlib, json, os, sys, urllib.parse, urllib.request

CDN = 'https://mediafilez.forgecdn.net/files/{}/{}/{}'
AGENT = {'User-Agent': 'oror-nightfall-ci/1'}


def exists(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method='HEAD', headers=AGENT), timeout=30) as r:
            return r.status == 200
    except Exception:
        return False


def main(manifest, lock, out, names):
    ids = [f['fileID'] for f in json.load(open(manifest, encoding='utf-8'))['files']]
    sha = json.load(open(lock, encoding='utf-8'))
    os.makedirs(out, exist_ok=True)
    for name in names:
        target = os.path.join(out, name)
        if os.path.exists(target) and hashlib.sha256(open(target, 'rb').read()).hexdigest() == sha[name]:
            continue
        url = next((u for u in (CDN.format(i // 1000, i % 1000, urllib.parse.quote(name)) for i in ids) if exists(u)), None)
        if url is None:
            sys.exit('not on the CDN under any manifest file id: ' + name)
        data = urllib.request.urlopen(urllib.request.Request(url, headers=AGENT), timeout=300).read()
        if hashlib.sha256(data).hexdigest() != sha[name]:
            sys.exit('SHA-256 mismatch: ' + name)
        open(target, 'wb').write(data)
        print('fetched', name, len(data), url)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:])

"""What SETUP_NIGHTFALL.cmd (oror-install/setup.ps1) does, for CI: fetch Nightfall and Sword Soaring as install.json names
them, check their size and SHA-256, and build the patched Sword Soaring jar (the original's entries, the overlay's in place
of the same names), checked against install.json's sword_members.

  python3 -I setup_nightfall.py <oror-install dir> <mods dir>
"""
import hashlib, io, json, os, sys, urllib.request, zipfile

inst, mods = sys.argv[1], sys.argv[2]
cfg = json.load(open(os.path.join(inst, 'install.json'), encoding='utf-8'))


def fetch(spec):
    req = urllib.request.Request(spec['url'], headers={'User-Agent': 'OROR-Nightfall-Verified-Installer/1'})
    data = urllib.request.urlopen(req, timeout=300).read()
    assert len(data) == spec['bytes'] and hashlib.sha256(data).hexdigest() == spec['sha256'], spec['filename']
    return data


nf = fetch(cfg['nightfall'])
open(os.path.join(mods, cfg['nightfall']['filename']), 'wb').write(nf)
src = zipfile.ZipFile(io.BytesIO(fetch(cfg['sword_source'])))
ov_bytes = open(os.path.join(inst, 'sword-soaring-overlay.zip'), 'rb').read()
assert hashlib.sha256(ov_bytes).hexdigest() == cfg['overlay_sha256'], 'overlay'
ov = zipfile.ZipFile(io.BytesIO(ov_bytes))
replaced = set(ov.namelist())
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as out:
    for arc in (src, ov):
        for n in arc.namelist():
            if n.endswith('/') or (arc is src and n in replaced):
                continue
            out.writestr(n, arc.read(n))
jar = zipfile.ZipFile(io.BytesIO(buf.getvalue()))
members = cfg['sword_members']
assert set(n for n in jar.namelist() if not n.endswith('/')) == set(members), 'sword members'
assert all(hashlib.sha256(jar.read(n)).hexdigest() == h for n, h in members.items()), 'sword hashes'
open(os.path.join(mods, cfg['sword_target']), 'wb').write(buf.getvalue())
print('nightfall + sword soaring installed:', cfg['nightfall']['filename'], cfg['sword_target'])

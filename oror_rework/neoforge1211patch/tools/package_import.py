"""OROR War x Nightfall import and patch ZIPs for a new OROR jar, made from the previous import ZIP.

  python3 -I package_import.py <previous import zip> <new jar> <old version> <new version> <notes .md> <out dir>

Import: every entry of the previous import is kept byte for byte, except the OROR jar (replaced), manifest.json (version)
and README_FIRST_JA.md (the new notes go first); the notes are also added as overrides/CHANGES_v<version>_JA.md.
Patch: the new jar under mods/ and the notes, for an existing profile (take the old OROR jar out of mods first).
"""
import json, os, sys, zipfile


def main(previous, jar, old, new, notes, out):
    old_jar = f'overrides/mods/oror_supreme_bosses-{old}.jar'
    new_jar = f'overrides/mods/oror_supreme_bosses-{new}.jar'
    text = open(notes, encoding='utf-8').read()
    payload = open(jar, 'rb').read()
    os.makedirs(out, exist_ok=True)
    import_zip = os.path.join(out, f'OROR_War_Nightfall_v{new}_Import.zip')
    with zipfile.ZipFile(previous) as src, zipfile.ZipFile(import_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as dst:
        names = src.namelist()
        if old_jar not in names:
            sys.exit('no ' + old_jar + ' in ' + previous)
        for info in src.infolist():
            data = src.read(info)
            if info.filename == old_jar:
                dst.writestr(new_jar, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
                continue
            if info.filename == 'manifest.json':
                manifest = json.loads(data.decode('utf-8'))
                if manifest['version'] != old:
                    sys.exit('manifest version is ' + manifest['version'])
                manifest['version'] = new
                data = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            elif info.filename == 'README_FIRST_JA.md':
                data = (text + '\n---\n\n').encode('utf-8') + data
            dst.writestr(info, data)
        dst.writestr(f'overrides/CHANGES_v{new}_JA.md', text.encode('utf-8'))
    patch_zip = os.path.join(out, f'OROR_War_Nightfall_v{new}_Patch.zip')
    with zipfile.ZipFile(patch_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as dst:
        dst.writestr(f'mods/oror_supreme_bosses-{new}.jar', payload)
        dst.writestr(f'CHANGES_v{new}_JA.md', text.encode('utf-8'))
    for path in (import_zip, patch_zip):
        print(path, os.path.getsize(path))


if __name__ == '__main__':
    main(*sys.argv[1:7])

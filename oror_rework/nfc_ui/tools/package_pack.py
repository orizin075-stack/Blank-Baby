"""OROR War x Nightfall import and patch ZIPs for a release that adds CurseForge files and override files.

  python3 -I package_pack.py <previous import zip> <new OROR jar> <old version> <new version> <resolved.json>
                             <overlay dir> <notes .md> <out dir>

Import: every entry of the previous import is kept byte for byte, except
  - the OROR jar (replaced by the new one),
  - manifest.json (new version; the additions of resolved.json appended as required files),
  - README_FIRST_JA.md (the new notes go first),
  - files under the overlay dir, which are added or replace overrides/<same path>;
and the notes are added as overrides/CHANGES_v<version>_JA.md.
Patch: the new jar under mods/, the overlay's config/ and oror-install/ files, and the notes, for a profile that keeps
its mods (the added CurseForge files need the new import).
"""
import json, os, sys, zipfile


def overlay_files(root):
    found = {}
    for folder, _, files in os.walk(root):
        for f in files:
            path = os.path.join(folder, f)
            found[os.path.relpath(path, root).replace(os.sep, '/')] = open(path, 'rb').read()
    return found


def main(previous, jar, old, new, resolved, overlay, notes, out):
    old_jar = f'overrides/mods/oror_supreme_bosses-{old}.jar'
    new_jar = f'overrides/mods/oror_supreme_bosses-{new}.jar'
    text = open(notes, encoding='utf-8').read()
    payload = open(jar, 'rb').read()
    additions = [e for e in json.load(open(resolved, encoding='utf-8'))['additions'] if e.get('fileID')]
    files = overlay_files(overlay)
    os.makedirs(out, exist_ok=True)
    import_zip = os.path.join(out, f'OROR_War_Nightfall_v{new}_Import.zip')
    with zipfile.ZipFile(previous) as src, zipfile.ZipFile(import_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as dst:
        if old_jar not in src.namelist():
            sys.exit('no ' + old_jar + ' in ' + previous)
        for info in src.infolist():
            name = info.filename
            if name == old_jar:
                dst.writestr(new_jar, payload)
                continue
            if name.startswith('overrides/') and name[len('overrides/'):] in files:
                continue
            data = src.read(info)
            if name == 'manifest.json':
                manifest = json.loads(data.decode('utf-8'))
                if manifest['version'] != old:
                    sys.exit('manifest version is ' + manifest['version'])
                manifest['version'] = new
                have = {f['projectID'] for f in manifest['files']}
                for e in additions:
                    if e['projectID'] in have:
                        sys.exit('already in the manifest: ' + str(e['projectID']))
                    manifest['files'].append({'projectID': e['projectID'], 'fileID': e['fileID'], 'required': True})
                data = (json.dumps(manifest, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
            elif name == 'README_FIRST_JA.md':
                data = (text + '\n---\n\n').encode('utf-8') + data
            dst.writestr(info, data)
        for path, data in sorted(files.items()):
            dst.writestr('overrides/' + path, data)
        dst.writestr(f'overrides/CHANGES_v{new}_JA.md', text.encode('utf-8'))
    patch_zip = os.path.join(out, f'OROR_War_Nightfall_v{new}_Patch.zip')
    with zipfile.ZipFile(patch_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as dst:
        dst.writestr(f'mods/oror_supreme_bosses-{new}.jar', payload)
        for path, data in sorted(files.items()):
            if path.startswith(('config/', 'oror-install/')):
                dst.writestr(path, data)
        dst.writestr(f'CHANGES_v{new}_JA.md', text.encode('utf-8'))
    for path in (import_zip, patch_zip):
        print(path, os.path.getsize(path))
    print(len(additions), 'CurseForge files added,', len(files), 'override files added or replaced')


if __name__ == '__main__':
    main(*sys.argv[1:9])

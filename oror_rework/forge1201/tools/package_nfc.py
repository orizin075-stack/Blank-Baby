"""NightfallCraft import zip with the Forge 1.20.1 build of OROR Reborn added.

  python3 -I package_nfc.py <extracted NightfallCraft import> <reobfuscated mod jar> <out zip> <mod version>

The pack's own manifest (its 240 CurseForge files), modlist and overrides are kept as they are; the mod jar goes in
overrides/mods, which the CurseForge app copies into the instance next to the downloaded mods. The jar must be the
reobfuscated one (build/libs after reobfJar): Forge 1.20.1 runs Minecraft under SRG names.
"""
import json, os, sys, zipfile


def main(src, jar, out, version):
    manifest = json.load(open(os.path.join(src, 'manifest.json'), encoding='utf-8'))
    if manifest['minecraft']['version'] != '1.20.1':
        sys.exit('not a 1.20.1 pack: ' + manifest['minecraft']['version'])
    with zipfile.ZipFile(jar) as j:
        names = set(j.namelist())
        toml = j.read('META-INF/mods.toml').decode('utf-8') if 'META-INF/mods.toml' in names else ''
    if 'modId="oror_supreme_bosses"' not in toml:
        sys.exit('not the Forge build of OROR Reborn (no META-INF/mods.toml for oror_supreme_bosses): ' + jar)
    manifest['name'] = manifest['name'] + ' + OROR Reborn'
    manifest['version'] = manifest['version'] + '-oror' + version
    overrides = manifest.get('overrides', 'overrides')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))
        if os.path.exists(os.path.join(src, 'modlist.html')):
            z.write(os.path.join(src, 'modlist.html'), 'modlist.html')
        root = os.path.join(src, overrides)
        for base, dirs, files in os.walk(root):
            dirs.sort()
            for f in sorted(files):
                full = os.path.join(base, f)
                z.write(full, overrides + '/' + os.path.relpath(full, root).replace(os.sep, '/'))
        z.write(jar, f'{overrides}/mods/oror_supreme_bosses-{version}.jar')
    print('wrote', out)


if __name__ == '__main__':
    main(*sys.argv[1:5])

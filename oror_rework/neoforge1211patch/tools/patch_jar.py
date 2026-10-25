"""OROR Reborn for NeoForge 1.21.1: the next jar from the shipped one, with recompiled classes and added translations.

  python3 -I patch_jar.py <base jar> <compiled classes dir> <lang fragments dir> <out jar> <old version> <new version>
                          [<overlay dir>]

The 0.17.19-0.17.23 builds were made elsewhere and their sources are not in this repository, so a release is the
shipped jar with only the classes rebuilt from src/main/java replaced (a replaced class's old inner classes go with
it). Each lang/<namespace>/<language>.json fragment is merged into assets/<namespace>/lang/<language>.json, and both mods
in neoforge.mods.toml get the new version. Files under the overlay dir (generated textures and meshes) replace the
entries at the same paths, or are added. Every other entry is copied byte for byte, in the original order.
"""
import json, os, sys, zipfile


def main(base, classes, lang, out, old, new, overlay=None):
    compiled = {}
    for root, _, files in os.walk(classes):
        for f in files:
            if f.endswith('.class'):
                path = os.path.join(root, f)
                compiled[os.path.relpath(path, classes).replace(os.sep, '/')] = open(path, 'rb').read()
    outer = {name[:-len('.class')].split('$')[0] for name in compiled}
    fragments = {}
    for ns in sorted(os.listdir(lang)):
        for f in sorted(os.listdir(os.path.join(lang, ns))):
            fragments[f'assets/{ns}/lang/{f}'] = json.load(open(os.path.join(lang, ns, f), encoding='utf-8'))
    files = {}
    if overlay:
        for root, _, names in os.walk(overlay):
            for f in names:
                path = os.path.join(root, f)
                files[os.path.relpath(path, overlay).replace(os.sep, '/')] = open(path, 'rb').read()
    replaced, merged, overlaid = [], [], 0
    with zipfile.ZipFile(base) as src, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as dst:
        for info in src.infolist():
            name = info.filename
            if name.endswith('.class') and name[:-len('.class')].split('$')[0] in outer:
                replaced.append(name)
                continue
            if name in files:
                dst.writestr(info, files.pop(name))
                overlaid += 1
                continue
            data = src.read(info)
            if name in fragments:
                table = json.loads(data.decode('utf-8'))
                table.update(fragments.pop(name))
                data = (json.dumps(table, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
                merged.append(name)
            elif name == 'META-INF/neoforge.mods.toml':
                text = data.decode('utf-8')
                if text.count(f'version="{old}"') != 2:
                    sys.exit(f'expected both mods at version {old} in neoforge.mods.toml')
                data = text.replace(f'version="{old}"', f'version="{new}"').encode('utf-8')
            dst.writestr(info, data)
        for name in sorted(compiled):
            dst.writestr(name, compiled[name])
        for name in sorted(files):
            dst.writestr(name, files[name])
            overlaid += 1
        for name, table in sorted(fragments.items()):
            dst.writestr(name, (json.dumps(table, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
            merged.append(name + ' (new)')
    print('replaced', len(replaced), 'old class files; added', len(compiled), 'compiled; overlaid', overlaid, 'files; merged', merged)


if __name__ == '__main__':
    main(*sys.argv[1:8])

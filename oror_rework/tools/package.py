"""Build the mod jar and the CurseForge import zip.

  jar  = original jar tree (mod/jar) + recompiled classes (build/classes) + generated assets (build/overlay)
  zip  = original import tree (mod/extracted) with the new jar, bumped manifest, and the Japanese relic guide
Usage: python3 package.py <scratchpad> <out_dir> <version>"""
import json, os, re, shutil, sys, zipfile

def add_tree(z, root, prefix='', skip=()):
    for base, dirs, files in os.walk(root):
        dirs.sort()
        for f in sorted(files):
            full = os.path.join(base, f)
            rel = os.path.relpath(full, root).replace(os.sep, '/')
            if any(rel.startswith(s) for s in skip):
                continue
            yield prefix + rel, full

def build_jar(S, out, version):
    entries = {}
    for rel, full in add_tree(None, os.path.join(S, 'mod', 'jar')):
        entries[rel] = full
    for rel, full in add_tree(None, os.path.join(S, 'build', 'classes')):
        entries[rel] = full
    for rel, full in add_tree(None, os.path.join(S, 'build', 'overlay')):
        entries[rel] = full
    toml = open(entries['META-INF/neoforge.mods.toml'], encoding='utf-8').read()
    toml = re.sub(r'version="[^"]+"', f'version="{version}"', toml, count=1)
    toml = toml.replace('description="', 'description="Sculpted 3D characters (46 rigs), 3D relic arsenal (164 relics + 41 replicas, OBJ models) with unique relic arts. ', 1)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        man = 'META-INF/MANIFEST.MF'
        if man in entries:
            z.write(entries.pop(man), man)
        for rel in sorted(entries):
            if rel == 'META-INF/neoforge.mods.toml':
                z.writestr(rel, toml)
            else:
                z.write(entries[rel], rel)
    return out

def relic_guide(S, version):
    sys.path.insert(0, os.path.join(S, 'tools', 'mc'))
    import relic_arts as R
    import relic_arts_a, relic_arts_b, relic_arts_c   # noqa: F401
    rel = json.load(open(os.path.join(S, 'build', 'overlay', 'assets', 'oror_supreme_bosses', 'relics.json'), encoding='utf-8'))
    lang = json.load(open(os.path.join(S, 'build', 'overlay', 'assets', 'oror_supreme_bosses', 'lang', 'ja_jp.json'), encoding='utf-8'))
    names = {}
    for k, v in lang.items():
        if k.startswith('item.oror_supreme_bosses.'):
            names[k.split('.', 2)[2]] = v
    chars = []
    for r in rel:
        if r['character'] not in chars:
            chars.append(r['character'])
    slot_ja = {'weapon': '武器', 'focus': '秘具', 'charm': '護符', 'legend': '伝説', 'relic_weapon': '残響（ダンジョン聖遺物）'}
    out = [f'# 聖遺物アーツ一覧（v{version}）', '',
           '全164の聖遺物と41のダンジョン聖遺物（残響）それぞれに固有の効果があります。',
           '右クリックで「使用」効果、手（メイン・オフハンド）に持っている間は「所持中」効果、武器で殴ると「命中時」効果が発動します。',
           '武器・伝説・残響はすべて3Dモデル（手に持つと立体表示）です。秘具・護符も3Dモデルになりました。', '']
    for c in chars:
        out.append(f'## {c}')
        for slot in ('weapon', 'focus', 'charm', 'legend', 'relic_weapon'):
            rid = f'{c}_{slot}'
            a = R.ARTS[rid]
            out.append(f'- **{names.get(rid, rid)}**（{slot_ja[slot]}）— 「{a["name"][0]}」：{a["desc"][0]}')
            if a['passive'] and a.get('pdesc'):
                out.append(f'  - {a["pdesc"][0]}')
            if a['hit'] and a.get('hdesc'):
                out.append(f'  - {a["hdesc"][0]}')
        out.append('')
    return '\n'.join(out)

def build_zip(S, jar, out, version):
    src = os.path.join(S, 'mod', 'extracted')
    man = json.load(open(os.path.join(src, 'manifest.json'), encoding='utf-8'))
    man['version'] = version
    jar_name = os.path.basename(jar)
    guide = relic_guide(S, version)
    notes = open(os.path.join(S, 'tools', 'CHANGES_JA.md'), encoding='utf-8').read() if os.path.exists(os.path.join(S, 'tools', 'CHANGES_JA.md')) else ''
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('manifest.json', json.dumps(man, ensure_ascii=False, indent=2))
        for rel, full in add_tree(None, src):
            if rel == 'manifest.json':
                continue
            if rel.startswith('overrides/mods/oror_supreme_bosses-'):
                continue
            z.write(full, rel)
        z.write(jar, 'overrides/mods/' + jar_name)
        z.writestr(f'overrides/RELIC_ARTS_v{version}_JA.md', guide)
        if notes:
            z.writestr(f'overrides/CHANGES_v{version}_JA.md', notes)
    return out

if __name__ == '__main__':
    S, out_dir, version = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(out_dir, exist_ok=True)
    jar = build_jar(S, os.path.join(out_dir, f'oror_supreme_bosses-{version}.jar'), version)
    z = build_zip(S, jar, os.path.join(out_dir, f'OROR_War_Nightfall_v{version}_Import.zip'), version)
    print(jar, os.path.getsize(jar))
    print(z, os.path.getsize(z))

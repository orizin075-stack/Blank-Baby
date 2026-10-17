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
    sys.path.insert(0, os.path.join(S, 'tools', 'mc'))
    from prune_items import removed_path   # models, textures and data of the items removed in v0.17.4
    for rel, full in add_tree(None, os.path.join(S, 'mod', 'jar')):
        entries[rel] = full
    for rel, full in add_tree(None, os.path.join(S, 'build', 'classes')):
        entries[rel] = full
    for rel, full in add_tree(None, os.path.join(S, 'build', 'overlay')):
        entries[rel] = full
    for rel in [r for r in entries if removed_path(r)]:
        del entries[rel]
    toml = open(entries['META-INF/neoforge.mods.toml'], encoding='utf-8').read()
    toml = re.sub(r'version="[^"]+"', f'version="{version}"', toml, count=1)
    toml = toml.replace('description="', 'description="Sculpted 3D characters (46 rigs), 3D relic arsenal (164 relics in 16 weapon kinds with special skills, OBJ models) with unique relic arts. ', 1)
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
    slot_ja = {'weapon': '武器', 'focus': '秘具', 'charm': '護符', 'legend': '伝説'}
    out = [f'# 聖遺物アーツ一覧（v{version}）', '',
           '全164の聖遺物それぞれに固有の効果があります。',
           '右クリックで「使用」効果、手（メイン・オフハンド）に持っている間は「所持中」効果、武器で殴ると「命中時」効果が発動します。',
           '武器・伝説はすべて3Dモデル（手に持つと立体表示）です。秘具・護符も3Dモデルです。',
           '武器・伝説には種別（刀・槍・鈍器・弓・魔導具・盾など）と、種別ごとの特殊能力があります。弓・魔導具・連射砲・砲・盾は'
           '右クリックで射撃や防御をし、アーツは「しゃがみ＋右クリック」で使います。それ以外の種別は右クリックでアーツです。',
           '秘具を手に持つと攻撃力＋40％・攻撃速度＋20％、護符を手に持つと最大体力＋20・防具＋10・防具強度＋6・移動速度＋20％・'
           'ノックバック耐性＋50％。秘具・護符のアーツは威力と回復が2倍、強化効果が1段階上・1.5倍長く・範囲1.25倍です。', '']
    kinds = json.load(open(os.path.join(S, 'build', 'overlay', 'assets', 'oror_supreme_bosses', 'weapon_kinds.json'), encoding='utf-8'))
    moves = json.load(open(os.path.join(S, 'build', 'overlay', 'assets', 'oror_supreme_bosses', 'boss_moves.json'), encoding='utf-8'))['characters']
    style_ja = {'duelist': '踏み込み・後退・横跳び', 'brawler': '跳びかかる', 'caster': '距離を取り、詰められると転移', 'gunner': '距離を取って横移動',
                'juggernaut': '跳躍で一気に詰める', 'guardian': 'じりじり前進', 'flyer': '急降下', 'swimmer': '突進するように泳ぐ',
                'trickster': '瞬間移動で翻弄', 'rooted': 'その場から動かない'}
    for c in chars:
        out.append(f'## {c}')
        kind = kinds['characters'][c]
        out.append(lang[f'weapon_kind.oror_supreme_bosses.{kind}'] + '　' + lang[f'weapon_kind.oror_supreme_bosses.how.{kinds["kinds"][kind]["mode"]}'])
        out.append(lang[f'weapon_skill.oror_supreme_bosses.{kind}.desc'])
        k = kinds['kinds'][kind]
        atk = {r['slot']: 1 + (r['damage'] + 4) * kinds['power'][str(r['rank'])] * k['mul'] for r in rel if r['character'] == c and r['slot'] in ('weapon', 'legend')}
        out.append(f'攻撃力：武器 {atk["weapon"]:.0f}／伝説 {atk["legend"]:.0f}（ネザライトの剣は8）')
        mv = moves[c]
        out.append('ボスとしての技：' + '／'.join(lang[f'boss_move.oror_supreme_bosses.{c}.{m}'] for m in mv['moves']) + f'（動き：{style_ja[mv["style"]]}）')
        for slot in ('weapon', 'focus', 'charm', 'legend'):
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

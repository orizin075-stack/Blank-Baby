"""survey.py <mods dir or texture dir> <out dir> [--javap JAVAP] [--only a,b,...]

Measures how the reference mods build and paint their mobs, so OROR's creatures can be compared by numbers, not
by impression:

  entity textures   size, opaque colours, light/dark range (contrast), how often a texel differs from its
                    neighbour (detail density), saturation, and emissive layers (_glow, _eyes, _emissive ...)
  GeckoLib models   bones, cubes, rotated cubes, inflated cubes, per-face UVs, texture size, model extent in pixels
  code models       boxes added per model class (CubeListBuilder / Citadel / Lionfish addBox calls, from javap)
  animations        how many animations each GeckoLib animation file holds, and their names

Writes survey.json (everything) and survey.md (per-mod summary and the largest models). Nothing from the jars is
copied out. Run with python3 -I.
"""
import io, json, os, re, statistics, subprocess, sys, tempfile, zipfile
import numpy as np
from PIL import Image

EMISSIVE = re.compile(r'(glow|emissive|_eyes|eyes\.png|_e\.png|_light|lights|_layer|overlay|_fire|_lava|_shine)', re.I)


def tex_stats(data):
    im = Image.open(io.BytesIO(data)).convert('RGBA')
    a = np.asarray(im).astype(np.int32)
    w, h = im.size
    op = a[..., 3] > 16
    n = int(op.sum())
    if n == 0:
        return {'w': w, 'h': h, 'opaque': 0}
    rgb = a[..., :3][op]
    cols = len(np.unique(rgb[:, 0] * 65536 + rgb[:, 1] * 256 + rgb[:, 2]))
    lum = (0.299 * rgb[:, 0] + 0.587 * rgb[:, 1] + 0.114 * rgb[:, 2]) / 255.0
    mx, mn = rgb.max(1), rgb.min(1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    # detail density: neighbouring opaque texels of different colour
    both = op[:, 1:] & op[:, :-1]
    diff = (a[:, 1:, :3] != a[:, :-1, :3]).any(-1) & both
    density = float(diff.sum() / max(1, both.sum()))
    return {'w': w, 'h': h, 'opaque': round(n / (w * h), 3), 'colours': cols, 'lum_p05': round(float(np.percentile(lum, 5)), 3),
            'lum_p95': round(float(np.percentile(lum, 95)), 3), 'lum_mean': round(float(lum.mean()), 3),
            'sat_mean': round(float(sat.mean()), 3), 'detail': round(density, 3)}


def geo_stats(data):
    try:
        j = json.loads(data.decode('utf-8-sig'))
    except Exception:
        return None
    geos = j.get('minecraft:geometry')
    if not geos:
        return None
    out = []
    for g in geos:
        d = g.get('description', {})
        bones = g.get('bones', []) or []
        cubes = [c for b in bones for c in (b.get('cubes') or [])]
        lo, hi = np.full(3, 1e9), np.full(3, -1e9)
        for c in cubes:
            o, s = np.asarray(c.get('origin', [0, 0, 0]), float), np.asarray(c.get('size', [0, 0, 0]), float)
            lo, hi = np.minimum(lo, o), np.maximum(hi, o + s)
        out.append({'id': d.get('identifier'), 'tex': [d.get('texture_width'), d.get('texture_height')], 'bones': len(bones),
                    'cubes': len(cubes), 'rotated': sum(1 for c in cubes if any(abs(v) > 1e-6 for v in c.get('rotation', [0, 0, 0]))),
                    'rotated_bones': sum(1 for b in bones if any(abs(v) > 1e-6 for v in b.get('rotation', [0, 0, 0]))),
                    'inflated': sum(1 for c in cubes if c.get('inflate')), 'face_uv': sum(1 for c in cubes if isinstance(c.get('uv'), dict)),
                    'mirrored': sum(1 for c in cubes if c.get('mirror')),
                    'extent': [round(float(v), 1) for v in (hi - lo)] if cubes else None,
                    'tiny': sum(1 for c in cubes if min(c.get('size', [1, 1, 1])) <= 1.01),
                    'mean_size': round(float(np.mean([np.mean(c.get('size', [0, 0, 0])) for c in cubes])), 2) if cubes else None})
    return out


def anim_stats(data):
    try:
        j = json.loads(data.decode('utf-8-sig'))
    except Exception:
        return None
    an = j.get('animations') or {}
    return {'count': len(an), 'names': sorted(an)[:60], 'lengths': [an[k].get('animation_length') for k in sorted(an)][:60]}


BOX = re.compile(r'Method (?:\S+?CubeListBuilder\.\w+:\((?:Ljava/lang/String;)?FFFFFF|\S+?\.addBox:\(FFF)')
CHILD = re.compile(r'Method \S+?\.(addOrReplaceChild|m_171599_|addChild):')


def code_models(jar, javap, names):
    """Boxes per model class, counted from the bytecode of each class's methods."""
    out = {}
    if not javap or not names:
        return out
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(0, len(names), 40):
            batch = [n[:-6].replace('/', '.') for n in names[i:i + 40]]
            try:
                text = subprocess.run([javap, '-c', '-p', '-classpath', jar] + batch, capture_output=True, text=True, timeout=300).stdout
            except Exception as error:
                print('javap failed', error)
                continue
            cls = None
            for line in text.splitlines():
                m = re.match(r'(?:public |final |abstract |class |\s)*class (\S+)', line)
                if m and ('class ' in line) and not line.startswith(' '):
                    cls = m.group(1)
                    out.setdefault(cls, {'boxes': 0, 'parts': 0})
                    continue
                if cls is None:
                    continue
                if BOX.search(line):
                    out[cls]['boxes'] += 1
                elif CHILD.search(line):
                    out[cls]['parts'] += 1
    return {k: v for k, v in out.items() if v['boxes']}


def survey_jar(path, javap):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    mods = re.findall(r'modId\s*=\s*"([^"]+)"', z.read('META-INF/mods.toml').decode('utf-8', 'replace')) if 'META-INF/mods.toml' in names else []
    tex, geo, anim = {}, {}, {}
    for n in names:
        low = n.lower()
        if low.endswith('.png') and '/textures/' in low and re.search(r'/textures/(entity|entities|mob|mobs|boss)/', low):
            try:
                tex[n] = tex_stats(z.read(n))
                tex[n]['emissive'] = bool(EMISSIVE.search(os.path.basename(low)))
            except Exception as error:
                tex[n] = {'error': repr(error)}
        elif low.endswith('.json') and '/geo/' in low:
            g = geo_stats(z.read(n))
            if g:
                geo[n] = g
        elif low.endswith('.json') and '/animations/' in low:
            a = anim_stats(z.read(n))
            if a:
                anim[n] = a
    model_classes = [n for n in names if n.endswith('.class') and re.search(r'model', n, re.I) and not re.search(r'(entity|item)/?[^/]*Renderer', n)]
    code = code_models(path, javap, model_classes) if model_classes else {}
    return {'jar': os.path.basename(path), 'mods': mods, 'textures': tex, 'geo': geo, 'animations': anim, 'code_models': code}


def summary(rows):
    lines = ['# Reference mob survey', '']
    for r in rows:
        t = [v for v in r['textures'].values() if v.get('opaque')]
        if not t and not r['geo'] and not r['code_models']:
            continue
        lines += [f"## {', '.join(r['mods']) or r['jar']}  ({r['jar']})", '']
        if t:
            med = lambda k: statistics.median(v[k] for v in t if k in v)
            sizes = sorted({(v['w'], v['h']) for v in t}, key=lambda s: -s[0] * s[1])
            lines.append(f"- entity textures: {len(t)} (emissive layers {sum(1 for v in r['textures'].values() if v.get('emissive'))}); "
                         f"median {med('w'):.0f}x{med('h'):.0f}, largest {sizes[:4]}")
            lines.append(f"- colours per texture: median {med('colours'):.0f}, p90 {np.percentile([v['colours'] for v in t], 90):.0f}; "
                         f"luminance p05..p95 median {med('lum_p05'):.2f}..{med('lum_p95'):.2f}; mean saturation {med('sat_mean'):.2f}; "
                         f"detail density {med('detail'):.2f}")
        g = [m for v in r['geo'].values() for m in v]
        if g:
            cubes = [m['cubes'] for m in g]
            lines.append(f"- GeckoLib models: {len(g)}; cubes median {statistics.median(cubes):.0f}, max {max(cubes)}; "
                         f"bones median {statistics.median(m['bones'] for m in g):.0f}; rotated cubes {sum(m['rotated'] for m in g)}/{sum(cubes)}; "
                         f"per-face UV {sum(m['face_uv'] for m in g)}/{sum(cubes)}; inflated {sum(m['inflated'] for m in g)}")
            for m in sorted(g, key=lambda m: -m['cubes'])[:12]:
                lines.append(f"  - {m['id']}: {m['cubes']} cubes, {m['bones']} bones, tex {m['tex']}, extent {m['extent']}, "
                             f"rotated {m['rotated']}, tiny {m['tiny']}, mean cube size {m['mean_size']}")
        c = r['code_models']
        if c:
            lines.append(f"- code models: {len(c)} classes; boxes median {statistics.median(v['boxes'] for v in c.values()):.0f}, "
                         f"max {max(v['boxes'] for v in c.values())}")
            for k, v in sorted(c.items(), key=lambda kv: -kv[1]['boxes'])[:15]:
                lines.append(f"  - {k.split('.')[-1]}: {v['boxes']} boxes, {v['parts']} parts")
        a = r['animations']
        if a:
            lines.append(f"- animation files: {len(a)}; animations median {statistics.median(v['count'] for v in a.values()):.0f}, "
                         f"max {max(v['count'] for v in a.values())}")
        lines.append('')
    return '\n'.join(lines)


def main():
    src, out = sys.argv[1], sys.argv[2]
    javap = None
    only = None
    args = sys.argv[3:]
    if '--javap' in args:
        javap = args[args.index('--javap') + 1]
    if '--only' in args:
        only = args[args.index('--only') + 1].split(',')
    os.makedirs(out, exist_ok=True)
    rows = []
    for name in sorted(os.listdir(src)):
        if not name.endswith('.jar') or (only and not any(k in name.lower() for k in only)):
            continue
        print('surveying', name, flush=True)
        rows.append(survey_jar(os.path.join(src, name), javap))
    json.dump(rows, open(os.path.join(out, 'survey.json'), 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    open(os.path.join(out, 'survey.md'), 'w', encoding='utf-8').write(summary(rows))
    print(open(os.path.join(out, 'survey.md'), encoding='utf-8').read())


if __name__ == '__main__':
    main()

"""iss_probe.py <iss jar>: what Iron's Spells 'n Spellbooks gives a casting mob to be drawn with (051): its geo models
(bones, pivots, cubes, texture size), its animation files and the animations in them (with the bones each moves), for
building the royals a model ISS's own casting animations can play on."""
import json, sys, zipfile
z = zipfile.ZipFile(sys.argv[1])
names = z.namelist()
geos = [n for n in names if n.startswith('assets/irons_spellbooks/geo/') and n.endswith('.json')]
anims = [n for n in names if n.startswith('assets/irons_spellbooks/animations/') and n.endswith('.json')]
print('== geo files', len(geos))
for n in geos:
    print('  ', n)
for n in geos:
    if 'cast' in n or 'abstract' in n or 'mob' in n.split('/')[-1]:
        try:
            d = json.loads(z.read(n))
            for g in d.get('minecraft:geometry', []):
                print('== GEO', n, g.get('description'))
                for b in g.get('bones', []):
                    print('   bone', b.get('name'), 'parent', b.get('parent'), 'pivot', b.get('pivot'), 'rot', b.get('rotation'),
                          'cubes', [(c.get('origin'), c.get('size'), c.get('uv'), c.get('inflate')) for c in b.get('cubes', [])])
        except Exception as e:
            print('   could not read', n, e)
print('== animation files', len(anims))
for n in anims:
    try:
        d = json.loads(z.read(n))
        a = d.get('animations', {})
        print('== ANIM', n, len(a))
        for k, v in a.items():
            print('   ', k, 'len', v.get('animation_length'), 'loop', v.get('loop'), 'bones', sorted(v.get('bones', {}).keys()))
    except Exception as e:
        print('   could not read', n, e)

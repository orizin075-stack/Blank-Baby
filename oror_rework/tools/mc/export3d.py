"""Write the 3D relic items into an asset tree (…/assets/oror_supreme_bosses):

  models/item/relic3d/<id>.obj   + relic3d.mtl      geometry (base + full-bright 'glow' material)
  textures/item/relic3d/<id>.png                     the model's texture
  textures/item/<id>.png                             32px inventory icon rendered from the model
  models/item/<id>.json                              neoforge:separate_transforms: the OBJ in hands, on the
                                                     ground and on heads; the icon in the GUI and item frames
Usage: python3 export3d.py <assets_root> [keys...]
"""
import json, os, sys
import numpy as np
from PIL import Image
import forge3d as F
import held as Hd
import icons3d as I

NS = 'oror_supreme_bosses'

# in-hand length (blocks) for each weapon type, Cataclysm-scale but not absurd
TARGET = {'katana': 2.0, 'greatsword': 2.4, 'old holy sword': 2.1, 'branching sword': 2.2, 'chain blade': 2.4,
          'brush': 2.1, 'staff': 2.5, 'spindle staff': 2.5, 'conch staff': 2.4, 'marotte': 2.3, 'wand': 1.6,
          'kagura bell': 1.6, 'spear': 2.9, 'trident': 2.8, 'drill lance': 2.3, 'liquid halberd': 2.7, 'antler naginata': 2.9,
          'scythe': 2.7, 'hammer': 2.1, 'toy hammer': 1.8, 'maul': 2.3, 'kanabo': 2.2, 'gatling': 1.7, 'arm cannon': 1.6,
          'bow': 1.8, 'parasol': 2.2, 'kusarigama': 2.0, 'vine whip': 2.4, 'chakram': 1.4, 'syringe': 2.2, 'scales': 2.3}

def length_blocks(quads):
    ys = np.concatenate([F.to_obj_space(P)[:, 1] for P, *_ in quads])
    return float(ys.max() - ys.min())

def display_for(info, quads):
    if info['hold'] == 'sword':
        tp = TARGET.get(info['kind'], 2.2) / (length_blocks(quads) * 0.9375)
        tp = round(min(0.85, max(0.3, tp)), 3)
    else:
        tp = info['scale'] * (0.8 if info['hold'] == 'shield' else 1.0)
    fp = round(tp * 0.62, 3) if info['hold'] == 'sword' else {'fist': 0.5, 'shield': 0.55, 'palm': 0.55}[info['hold']]
    d = Hd.derive(scale_tp=tp, scale_fp=fp, hold=info['hold'])
    out = {'thirdperson_righthand': d['thirdperson_righthand'], 'firstperson_righthand': d['firstperson_righthand']}
    g = Hd.ground(quads)
    out['ground'] = g
    out['head'] = dict(rotation=[0, 180, 0], translation=[0, 13, 7], scale=[0.6, 0.6, 0.6])
    for v in out.values():
        v['rotation'] = [round(float(x), 3) for x in v['rotation']]
        v['translation'] = [round(float(max(-80, min(80, x))), 3) for x in v['translation']]
        v['scale'] = [round(float(x), 4) for x in v['scale']]
    return out

def item_json(model_id, icon_id, display):
    icon = {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'{NS}:item/{icon_id}'}}
    return {
        'loader': 'neoforge:separate_transforms',
        'gui_light': 'front',
        'textures': {'particle': f'{NS}:item/{icon_id}'},
        'base': {
            'loader': 'neoforge:obj',
            'model': f'{NS}:models/item/relic3d/{model_id}.obj',
            'flip_v': False,
            'emissive_ambient': True,
            'automatic_culling': False,
            'textures': {'tex': f'{NS}:item/relic3d/{model_id}', 'particle': f'{NS}:item/{icon_id}'},
            'display': display,
        },
        'perspectives': {'gui': icon, 'fixed': icon},
    }

def export_one(root, rid, w, info):
    quads, atlas, S = w.build()
    md = os.path.join(root, 'models', 'item', 'relic3d')
    td = os.path.join(root, 'textures', 'item', 'relic3d')
    os.makedirs(md, exist_ok=True)
    os.makedirs(td, exist_ok=True)
    F.write_obj(os.path.join(md, rid + '.obj'), quads, S)
    Image.fromarray(atlas, 'RGBA').save(os.path.join(td, rid + '.png'), optimize=True)
    ic = I.icon_for(rid, quads, atlas, info['hold'], info['kind'])
    ic.save(os.path.join(root, 'textures', 'item', rid + '.png'), optimize=True)
    disp = display_for(info, quads)
    with open(os.path.join(root, 'models', 'item', rid + '.json'), 'w') as fh:
        json.dump(item_json(rid, rid, disp), fh, indent=1)
    with open(os.path.join(md, 'relic3d.mtl'), 'w') as fh:
        fh.write(F.MTL)
    return len(quads), S, disp

def export_weapons(root, keys=None):
    import w3designs as D
    keys = keys or list(D.WEAPONS)
    report = {}
    for k in keys:
        info = D.WEAPONS[k]
        for aw, slot in ((False, 'weapon'), (True, 'legend')):
            rid = f'{k}_{slot}'
            n, S, disp = export_one(root, rid, D.build(k, aw), info)
            report[rid] = (n, S)
        # the legacy dungeon relic weapon is a replica of the weapon: same model, same icon
        with open(os.path.join(root, 'models', 'item', f'{k}_relic_weapon.json'), 'w') as fh:
            json.dump(item_json(f'{k}_weapon', f'{k}_weapon', display_for(info, D.build(k, False).build()[0])), fh, indent=1)
        print(k, report[f'{k}_weapon'], report[f'{k}_legend'], flush=True)
    return report

def export_artifacts(root, relics_json):
    import w3artifacts as A
    rows = json.load(open(relics_json, encoding='utf-8'))
    for r in rows:
        if r['slot'] not in ('focus', 'charm'):
            continue
        w, arch, hold = A.build(r['id'], r['character'], r['name'])
        info = {'hold': hold, 'kind': arch, 'scale': 0.75 if hold != 'sword' else 0.85, 'fp_scale': 0.6}
        n, S, disp = export_one(root, r['id'], w, info)
        print(r['id'], arch, hold, n, S, flush=True)

if __name__ == '__main__':
    if sys.argv[1] == '--artifacts':
        export_artifacts(sys.argv[2], sys.argv[3])
    else:
        export_weapons(sys.argv[1], sys.argv[2:] or None)

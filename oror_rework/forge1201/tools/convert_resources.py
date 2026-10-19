"""Turn the resources of the Minecraft 1.21.1 / NeoForge jar into a Minecraft 1.20.1 / Forge resource tree.

  python3 -I convert_resources.py <unzipped 1.21.1 jar> <out: src/main/resources>

What changes between the two versions, for what this mod ships:
  - data folders that were plural in 1.20.1 (advancements, loot_tables, recipes, structures, tags/items|blocks|entity_types)
  - recipe results ({"id"} -> {"item"}), advancement icons ({"id"} -> {"item"}), item predicates (a single id -> a list),
    location predicates ("structures" -> "structure")
  - NeoForge loaders and conditions -> Forge's (forge:obj, forge:separate_transforms, forge:mod_loaded under "conditions")
  - structure templates: DataVersion 3465, 1.20 item stacks (Count/tag), banner patterns (Patterns/Pattern/Color),
    NeoForgeData -> ForgeData
  - left out: the 1.21 enchantable item tags (1.20.1 has none), the compatibility packs for the 1.21 versions of other
    mods, and Iron's Spells spell configs (NightfallCraft ships its own in config/)
"""
import json, os, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nbt
from nbt import Tag, BYTE, SHORT, INT, STRING, LIST, COMPOUND

SRC, OUT = sys.argv[1], sys.argv[2]

PLURAL = {'advancement': 'advancements', 'loot_table': 'loot_tables', 'recipe': 'recipes', 'structure': 'structures',
          'function': 'functions', 'item_modifier': 'item_modifiers', 'predicate': 'predicates'}
TAG_PLURAL = {'item': 'items', 'block': 'blocks', 'entity_type': 'entity_types', 'fluid': 'fluids',
              'game_event': 'game_events', 'function': 'functions'}
DROP = ('data/minecraft/tags/item/enchantable/', 'data/irons_spellbooks/irons_spellbooks_spell_config/', 'resourcepacks/',
        'META-INF/', 'jp/', 'pack.mcmeta', 'oror_reborn.mixins.json')

def out_path(rel):
    parts = rel.split('/')
    if parts[0] == 'data' and len(parts) > 3:
        if parts[2] == 'tags' and len(parts) > 4 and parts[3] in TAG_PLURAL:
            parts[3] = TAG_PLURAL[parts[3]]
        elif parts[2] in PLURAL:
            parts[2] = PLURAL[parts[2]]
    return '/'.join(parts)

# ------------------------------------------------------------------------------------------------ JSON
def conditions(d):
    """NeoForge's "neoforge:conditions" -> Forge 1.20.1's "conditions" (forge:mod_loaded, forge:false ...)."""
    if isinstance(d, dict) and 'neoforge:conditions' in d:
        conds = d.pop('neoforge:conditions')
        d['conditions'] = [rename_types(c) for c in conds]
    return d

def rename_types(v):
    if isinstance(v, dict):
        return {k: (x.replace('neoforge:', 'forge:', 1) if k in ('type', 'loader') and isinstance(x, str) else rename_types(x))
                for k, x in v.items()}
    if isinstance(v, list):
        return [rename_types(x) for x in v]
    return v

def item_predicates(v):
    """1.21 item predicate {"items": "id" | "#tag" | [..]} -> 1.20.1 {"items": [..]} or {"tag": ..}."""
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            if k == 'items' and isinstance(x, str):
                if x.startswith('#'):
                    out['tag'] = x[1:]
                else:
                    out['items'] = [x]
            elif k == 'structures' and isinstance(x, str):
                out['structure'] = x
            else:
                out[k] = item_predicates(x)
        return out
    if isinstance(v, list):
        return [item_predicates(x) for x in v]
    return v

def convert_json(rel, d):
    d = conditions(d)
    parts = rel.split('/')
    kind = parts[2] if parts[0] == 'data' and len(parts) > 2 else None
    if kind == 'recipe':
        r = d.get('result')
        if isinstance(r, dict) and 'id' in r:
            r['item'] = r.pop('id')
    elif kind == 'advancement':
        icon = d.get('display', {}).get('icon')
        if isinstance(icon, dict) and 'id' in icon:
            icon['item'] = icon.pop('id')
            if 'components' in icon:
                icon.pop('components')
        d['criteria'] = item_predicates(d.get('criteria', {}))
    if parts[0] == 'assets':
        d = rename_types(d)
    return d

# ------------------------------------------------------------------------------------------------ structure NBT
BANNER = {'base': 'b', 'square_bottom_left': 'bl', 'square_bottom_right': 'br', 'square_top_left': 'tl',
          'square_top_right': 'tr', 'stripe_bottom': 'bs', 'stripe_top': 'ts', 'stripe_left': 'ls', 'stripe_right': 'rs',
          'stripe_center': 'cs', 'stripe_middle': 'ms', 'stripe_downright': 'drs', 'stripe_downleft': 'dls',
          'small_stripes': 'ss', 'cross': 'cr', 'straight_cross': 'sc', 'triangle_bottom': 'bt', 'triangle_top': 'tt',
          'triangles_bottom': 'bts', 'triangles_top': 'tts', 'diagonal_left': 'ld', 'diagonal_up_right': 'rd',
          'diagonal_up_left': 'lud', 'diagonal_right': 'rud', 'circle': 'mc', 'rhombus': 'mr', 'half_vertical': 'vh',
          'half_horizontal': 'hh', 'half_vertical_right': 'vhr', 'half_horizontal_bottom': 'hhb', 'border': 'bo',
          'curly_border': 'cbo', 'gradient': 'gra', 'gradient_up': 'gru', 'bricks': 'bri', 'globe': 'glb', 'creeper': 'cre',
          'skull': 'sku', 'flower': 'flo', 'mojang': 'moj', 'piglin': 'pig'}
COLORS = ['white', 'orange', 'magenta', 'light_blue', 'yellow', 'lime', 'pink', 'gray', 'light_gray', 'cyan', 'purple',
          'blue', 'brown', 'green', 'red', 'black']

def stack(t):
    """1.21 {id, count, components} -> 1.20 {id, Count:byte, tag}."""
    v = t.v
    if not v:
        return t
    out = {'id': v['id'], 'Count': Tag(BYTE, v['count'].v if 'count' in v else 1)}
    comps = v.get('components')
    if comps is not None:
        tag = {}
        ench = comps.v.get('minecraft:enchantments')
        if ench is not None:
            levels = ench.v['levels'].v
            tag['Enchantments'] = Tag(LIST, (COMPOUND, [Tag(COMPOUND, {'id': Tag(STRING, k), 'lvl': Tag(SHORT, lv.v)})
                                                        for k, lv in levels.items()]))
        name = comps.v.get('minecraft:custom_name')
        if name is not None:
            tag['display'] = Tag(COMPOUND, {'Name': name})
        data = comps.v.get('minecraft:custom_data')
        if data is not None:
            tag.update(data.v)
        if tag:
            out['tag'] = Tag(COMPOUND, tag)
    return Tag(COMPOUND, out)

def entity(t):
    v = t.v
    if 'NeoForgeData' in v:
        v['ForgeData'] = v.pop('NeoForgeData')
    for key in ('HandItems', 'ArmorItems'):
        if key in v:
            et, items = v[key].v
            v[key] = Tag(LIST, (COMPOUND, [stack(x) for x in items]))
    return t

def block_entity(t):
    v = t.v
    if 'patterns' in v:
        et, pats = v.pop('patterns').v
        v['Patterns'] = Tag(LIST, (COMPOUND, [Tag(COMPOUND, {
            'Pattern': Tag(STRING, BANNER[p.v['pattern'].v.split(':')[-1]]),
            'Color': Tag(INT, COLORS.index(p.v['color'].v))}) for p in pats]))
    if 'SpawnData' in v and 'entity' in v['SpawnData'].v:
        entity(v['SpawnData'].v['entity'])
    if 'Items' in v:
        et, items = v['Items'].v
        conv = []
        for x in items:
            slot = x.v.get('Slot')
            s = stack(x)
            if slot is not None:
                s.v['Slot'] = slot
            conv.append(s)
        v['Items'] = Tag(LIST, (COMPOUND, conv))
    return t

def convert_nbt(src, dst):
    name, root = nbt.load(src)
    r = root.v
    r['DataVersion'] = Tag(INT, 3465)
    for b in r.get('blocks', Tag(LIST, (COMPOUND, []))).v[1]:
        if 'nbt' in b.v:
            block_entity(b.v['nbt'])
    for e in r.get('entities', Tag(LIST, (COMPOUND, []))).v[1]:
        entity(e.v['nbt'])
    nbt.save(dst, name, root)

# ------------------------------------------------------------------------------------------------ walk
counts = {'json': 0, 'nbt': 0, 'copy': 0, 'drop': 0}
for base, dirs, files in os.walk(SRC):
    dirs.sort()
    for f in sorted(files):
        full = os.path.join(base, f)
        rel = os.path.relpath(full, SRC).replace(os.sep, '/')
        if rel.startswith(DROP) or rel.endswith('.class'):
            counts['drop'] += 1
            continue
        dst = os.path.join(OUT, out_path(rel))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if f.endswith('.json') or f.endswith('.mcmeta'):
            d = json.load(open(full, encoding='utf-8'))
            d = convert_json(rel, d)
            with open(dst, 'w', encoding='utf-8') as o:
                json.dump(d, o, ensure_ascii=False, indent=1)
            counts['json'] += 1
        elif f.endswith('.nbt'):
            convert_nbt(full, dst)
            counts['nbt'] += 1
        else:
            shutil.copyfile(full, dst)
            counts['copy'] += 1

json.dump({'pack': {'pack_format': 15, 'description': 'OROR Reborn original characters'}},
          open(os.path.join(OUT, 'pack.mcmeta'), 'w', encoding='utf-8'), indent=2)
print(counts)

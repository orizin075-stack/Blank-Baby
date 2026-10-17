"""Items removed in v0.17.4 and everything that pointed at them.

Removed (275 items):
  <character>_citadel_bricks     block + item, used nowhere
  <character>_dungeon_spawn_egg  41 recoloured eggs of the same citadel guard
  <character>_essence            dropped by bosses and chests, used by nothing
  <character>_boss_seal          the item only; the block stays (citadels place it, right-click summons the boss)
  <character>_relic_weapon       the "Echo" replicas of the relic weapons
  fusion_*                       70 English-named stand-ins for NightfallCraft items (quests now treat those as done)

  python3 -I prune_items.py <original jar tree> <overlay>
rewrites the loot tables that dropped them into the overlay and drops their lang keys; package.py calls
removed_path() to leave their models, textures and Epic Fight capabilities out of the jar."""
import json, os, re, sys

NS = 'oror_supreme_bosses'
FAMILIES = ('citadel_bricks', 'dungeon_spawn_egg', 'essence', 'boss_seal', 'relic_weapon')
ITEM_RE = re.compile(rf'^{NS}:(?:[a-z_]+_(?:{"|".join(FAMILIES)})|fusion_[a-z0-9_]+)$')
# asset / data files of removed things. Seal blocks stay, so only their item model goes.
PATH_RES = [re.compile(p) for p in (
    rf'^assets/{NS}/models/item/[a-z_]+_(?:{"|".join(FAMILIES)})\.json$',
    rf'^assets/{NS}/models/item/fusion_[a-z0-9_]+\.json$',
    rf'^assets/{NS}/(?:blockstates|models/block)/[a-z_]+_citadel_bricks\.json$',
    rf'^assets/{NS}/textures/block/[a-z_]*citadel_bricks\.png$',
    rf'^assets/{NS}/textures/item/[a-z_]*(?:essence|relic_weapon|dungeon_spawn_egg)\.png$',
    rf'^data/{NS}/capabilities/weapons/fusion_[a-z0-9_]+\.json$',
)]


def removed_item(name):
    return bool(ITEM_RE.match(name))


def removed_path(rel):
    return any(r.match(rel) for r in PATH_RES)


def relic_entries(char):
    return [{'type': 'minecraft:item', 'name': f'{NS}:{char}_{slot}'} for slot in ('weapon', 'focus', 'charm')]


def prune_pool(pool, vault_char):
    out = []
    for e in pool.get('entries', []):
        name = e.get('name', '')
        if e.get('type') == 'minecraft:item' and removed_item(name):
            # a citadel vault held the character's Echo: it now holds one of the character's real relics
            if vault_char and name.endswith('_relic_weapon'):
                out.extend(relic_entries(vault_char))
            continue
        out.append(e)
    if not out:
        return None
    pool = dict(pool)
    pool['entries'] = out
    return pool


def prune_table(t, vault_char=None):
    pools = [p for p in (prune_pool(p, vault_char) for p in t.get('pools', [])) if p is not None]
    t = dict(t)
    t['pools'] = pools
    return t


def walk_names(o, out):
    if isinstance(o, dict):
        if isinstance(o.get('name'), str):
            out.append(o['name'])
        for v in o.values():
            walk_names(v, out)
    elif isinstance(o, list):
        for v in o:
            walk_names(v, out)


def main(jar, overlay):
    src = os.path.join(jar, 'data', NS, 'loot_table')
    dst = os.path.join(overlay, 'data', NS, 'loot_table')
    changed = 0
    for base, _dirs, files in os.walk(src):
        for f in sorted(files):
            if not f.endswith('.json'):
                continue
            full = os.path.join(base, f)
            rel = os.path.relpath(full, src)
            t = json.load(open(full, encoding='utf-8'))
            names = []
            walk_names(t, names)
            if not any(removed_item(n) for n in names):
                continue
            vault = f[:-len('_vault.json')] if f.endswith('_vault.json') else None
            t2 = prune_table(t, vault)
            left = []
            walk_names(t2, left)
            assert not any(removed_item(n) for n in left), rel
            os.makedirs(os.path.dirname(os.path.join(dst, rel)), exist_ok=True)
            with open(os.path.join(dst, rel), 'w', encoding='utf-8') as fh:
                json.dump(t2, fh, ensure_ascii=False, indent=1)
            changed += 1
    gone = 0
    for lang in ('ja_jp', 'en_us'):
        path = os.path.join(overlay, 'assets', NS, 'lang', lang + '.json')
        d = json.load(open(path, encoding='utf-8'))
        for k in list(d):
            kind, _, rest = k.partition('.')
            if kind in ('item', 'block') and rest.startswith(NS + '.'):
                path_id = rest[len(NS) + 1:]
                if removed_item(f'{NS}:{path_id}') and not (kind == 'block' and path_id.endswith('_boss_seal')):
                    del d[k]
                    gone += 1
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1)
    # nothing left in the shipped data may name a removed item
    for root in (os.path.join(jar, 'data'), os.path.join(overlay, 'data')):
        for base, _dirs, files in os.walk(root):
            for f in files:
                full = os.path.join(base, f)
                rel = os.path.relpath(full, os.path.dirname(root)).replace(os.sep, '/')
                if not f.endswith('.json') or removed_path(rel):
                    continue
                if root.startswith(jar) and os.path.exists(os.path.join(overlay, rel)):
                    continue
                text = open(full, encoding='utf-8').read()
                for m in re.finditer(rf'{NS}:[a-z0-9_]+', text):
                    assert not removed_item(m.group(0)), f'{rel} still names {m.group(0)}'
    print('loot tables rewritten', changed, 'lang keys removed', gone)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

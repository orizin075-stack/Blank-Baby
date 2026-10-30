"""extract.py <save dir> <out dir>: the Grand Citadel v12 as compact per-region files for natural generation.

Each output file r.<rx>.<rz>.bin holds the save's chunks of that region:
  'OCV12' version(1 byte) count(int) then per chunk: lx(byte) lz(byte) offset(int) length(int), then payloads.
  A payload is the zlib of an NBT compound {DataVersion, xPos, zPos, yPos, Status, sections, block_entities, Entities?}
  with everything the generator does not need dropped (light, heightmaps, ticks, biomes, structures) and the sections
  left out that hold only dirt and bedrock (the natural ground is kept there). Entities come from the entity region
  files, as {DataVersion, Position, Entities}.
"""
import os, sys, struct, zlib, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anvil
from anvil import Typed, val

save, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
NATURAL = {'minecraft:dirt', 'minecraft:bedrock'}
stats = dict(chunks=0, sections_kept=0, sections_dropped=0, block_entities=0, entities=0, bytes=0)
ents = {}
for f in sorted(os.listdir(os.path.join(save, 'entities'))):
    for lx, lz, nbt in anvil.chunks_typed(os.path.join(save, 'entities', f)):
        pos = nbt['Position'][1]
        if nbt.get('Entities'):
            ents[(pos[0], pos[1])] = nbt
for f in sorted(os.listdir(os.path.join(save, 'region'))):
    rx, rz = map(int, f.split('.')[1:3])
    entries = []
    blobs = []
    off = 0
    for lx, lz, nbt in anvil.chunks_typed(os.path.join(save, 'region', f)):
        stats['chunks'] += 1
        secs = []
        for s in nbt['sections']:
            pal = [p['Name'] for p in s.get('block_states', {}).get('palette', [])]
            if not pal or set(pal) <= NATURAL:
                stats['sections_dropped'] += 1
                continue
            secs.append({'Y': s['Y'], 'block_states': s['block_states']})
            stats['sections_kept'] += 1
        keep = {k: nbt[k] for k in ('DataVersion', 'xPos', 'zPos', 'yPos', 'Status') if k in nbt}
        keep['sections'] = secs
        be = nbt.get('block_entities', [])
        keep['block_entities'] = be
        stats['block_entities'] += len(be)
        cx, cz = val(nbt['xPos']), val(nbt['zPos'])
        e = ents.get((cx, cz))
        if e is not None:
            keep['Entities'] = {'DataVersion': e['DataVersion'], 'Position': e['Position'], 'Entities': e['Entities']}
            stats['entities'] += len(e['Entities'])
        raw = zlib.compress(anvil.write_nbt(keep), 9)
        entries.append((lx, lz, off, len(raw)))
        blobs.append(raw)
        off += len(raw)
    head = b'OCV12' + bytes([1]) + struct.pack('>i', len(entries))
    head += b''.join(struct.pack('>bbii', lx, lz, o, n) for lx, lz, o, n in entries)
    data = head + b''.join(blobs)
    open(os.path.join(out, f'r.{rx}.{rz}.bin'), 'wb').write(data)
    stats['bytes'] += len(data)
print(json.dumps(stats))

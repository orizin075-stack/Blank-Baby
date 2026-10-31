"""Write block edits into an Anvil save: anvil_edit.apply(save_in, save_out, edits, bes).

edits maps (x, y, z) to a block state: a name ('minecraft:stone') or a name with properties
('minecraft:lantern[hanging=true,waterlogged=false]'). Each changed section is re-encoded with a compact palette; changed
chunks lose their heightmaps (rebuilt on load) and the block entities of replaced blocks, and keep isLightOn 0 so the
game relights them. bes maps (x, y, z) to a new block entity (a dict of Python values: ints are written as ints,
('byte', v), ('short', v), ('long', v) and ('float', v) as those). Untouched region files are copied as they are.
"""
import os, shutil, struct, time, zlib
import numpy as np
import anvil
from anvil import Typed


def state(s):
    if '[' not in s:
        return {'Name': s}
    name, props = s[:-1].split('[', 1)
    return {'Name': name, 'Properties': dict(p.split('=', 1) for p in props.split(','))}


def key(entry):
    props = entry.get('Properties') or {}
    return anvil.val(entry['Name']) + ('[' + ','.join(f'{k}={anvil.val(v)}' for k, v in sorted(props.items())) + ']' if props else '')


def decode(bs):
    pal = bs['palette']
    if len(pal) == 1 or 'data' not in bs:
        return pal, np.zeros(4096, np.int64)
    bits = max(4, (len(pal) - 1).bit_length())
    per = 64 // bits
    longs = np.array(anvil.val(bs['data'])[1], dtype=np.int64).view(np.uint64)
    idx = np.empty(len(longs) * per, np.int64)
    mask = np.uint64((1 << bits) - 1)
    for k in range(per):
        idx[k::per] = ((longs >> np.uint64(k * bits)) & mask).astype(np.int64)
    return pal, idx[:4096]


def encode(pal, idx):
    used = np.unique(idx)
    remap = np.zeros(len(pal), np.int64)
    remap[used] = np.arange(len(used))
    pal = [pal[i] for i in used]
    idx = remap[idx]
    if len(pal) == 1:
        return {'palette': pal}
    bits = max(4, (len(pal) - 1).bit_length())
    per = 64 // bits
    n = (4096 + per - 1) // per
    padded = np.zeros(n * per, np.uint64)
    padded[:4096] = idx.astype(np.uint64)
    longs = np.zeros(n, np.uint64)
    for k in range(per):
        longs |= padded[k::per] << np.uint64(k * bits)
    return {'palette': pal, 'data': ('L', tuple(int(v) for v in longs.view(np.int64)))}


NARROW = {'byte': 1, 'short': 2, 'long': 4, 'float': 5}


def be_nbt(v):
    """Python block entity data as NBT: ('byte' | 'short' | 'long' | 'float', v) for the numbers that are not ints,
    nested through compounds and lists."""
    if isinstance(v, tuple) and len(v) == 2 and v[0] in NARROW:
        return Typed(NARROW[v[0]], v[1])
    if isinstance(v, dict):
        return {k: be_nbt(x) for k, x in v.items()}
    if isinstance(v, list):
        return [be_nbt(x) for x in v]
    return v


def edit_chunk(nbt, chunk_edits, chunk_bes=None):
    by_section = {}
    for (x, y, z), s in chunk_edits.items():
        by_section.setdefault(y >> 4, []).append((x & 15, y & 15, z & 15, s))
    sections = {anvil.val(s['Y']): s for s in nbt['sections']}
    for sy, items in by_section.items():
        sec = sections.get(sy)
        if sec is None:
            sec = {'Y': Typed(1, sy), 'block_states': {'palette': [{'Name': 'minecraft:air'}]}}
            nbt['sections'].append(sec)
            sections[sy] = sec
        bs = sec.get('block_states') or {'palette': [{'Name': 'minecraft:air'}]}
        pal, idx = decode(bs)
        pal = list(pal)
        index = {key(p): i for i, p in enumerate(pal)}
        idx = idx.copy()
        for x, y, z, s in items:
            k = key(state(s))
            if k not in index:
                index[k] = len(pal)
                pal.append(state(s))
            idx[(y * 16 + z) * 16 + x] = index[k]
        sec['block_states'] = encode(pal, idx)
    # a block entity where a block was replaced goes with it; the new ones come in
    edited = set(chunk_edits) | set(chunk_bes or ())
    if nbt.get('block_entities'):
        nbt['block_entities'] = [be for be in nbt['block_entities']
                                 if (anvil.val(be['x']), anvil.val(be['y']), anvil.val(be['z'])) not in edited]
    if chunk_bes:
        nbt['block_entities'] = list(nbt.get('block_entities') or []) + [be_nbt(be) for _, be in sorted(chunk_bes.items())]
    nbt.pop('Heightmaps', None)
    nbt['isLightOn'] = Typed(1, 0)
    return nbt


def write_region(path, chunks):
    """chunks: {(lx, lz): nbt}"""
    offsets = bytearray(4096)
    stamps = bytearray(4096)
    body = bytearray()
    sector = 2
    now = int(time.time())
    for (lx, lz), nbt in sorted(chunks.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        data = zlib.compress(anvil.write_nbt(nbt), 6)
        blob = struct.pack('>i', len(data) + 1) + b'\x02' + data
        blob += b'\0' * ((-len(blob)) % 4096)
        n = len(blob) // 4096
        i = (lx + lz * 32) * 4
        offsets[i:i + 4] = struct.pack('>I', (sector << 8) | n)
        stamps[i:i + 4] = struct.pack('>I', now)
        body += blob
        sector += n
    with open(path, 'wb') as f:
        f.write(offsets)
        f.write(stamps)
        f.write(body)


def apply(save_in, save_out, edits, bes=None, biome=None):
    """biome, if given, becomes the biome of every chunk of the save."""
    if os.path.abspath(save_in) != os.path.abspath(save_out):
        if os.path.exists(save_out):
            shutil.rmtree(save_out)
        shutil.copytree(save_in, save_out)
    per_region = {}
    if biome:
        for f in os.listdir(os.path.join(save_out, 'region')):
            if f.endswith('.mca'):
                rx, rz = (int(v) for v in f[2:-4].split('.'))
                per_region.setdefault((rx, rz), {})
    for (x, y, z), s in edits.items():
        per_region.setdefault((x >> 9, z >> 9), {}).setdefault((x >> 4, z >> 4), {})[(x, y, z)] = s
    be_chunks = {}
    for (x, y, z), be in (bes or {}).items():
        be_chunks.setdefault((x >> 4, z >> 4), {})[(x, y, z)] = be
        per_region.setdefault((x >> 9, z >> 9), {}).setdefault((x >> 4, z >> 4), {})
    for (rx, rz), chunk_map in per_region.items():
        path = os.path.join(save_out, 'region', f'r.{rx}.{rz}.mca')
        chunks = {}
        for lx, lz, nbt in anvil.chunks_typed(path):
            cx, cz = anvil.val(nbt['xPos']), anvil.val(nbt['zPos'])
            if (cx, cz) in chunk_map:
                nbt = edit_chunk(nbt, chunk_map[(cx, cz)], be_chunks.get((cx, cz)))
            if biome:
                for sec in nbt.get('sections', []):
                    sec['biomes'] = {'palette': [biome]}
            chunks[(lx, lz)] = nbt
        write_region(path, chunks)
    return sum(len(c) for c in per_region.values())

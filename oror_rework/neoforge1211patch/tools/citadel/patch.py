"""patch.py <new template dir> <out file> <old template dir>...: the blocks a world built from any earlier template must
change to match the new one (update.bin, read by CitadelUpdate when an old world's capital loads).

Every template the mod has shipped is compared with the new one, block by block (the generator's view: a section the
template leaves out is open sky above the kingdom's ground at y 64 and natural ground below it; dirt and bedrock are both
natural ground). A block that differs from the new template in any of them is marked: whichever template the world was
built from, its capital then gets the new blocks there, and nothing else in it is touched (what the players built or
broke elsewhere stays as it is).

update.bin (zlib): 'OCU1' revision(int) chunks(int), then per chunk: sx(byte) sz(byte) sections(byte), the kingdom's
containers there to empty before they are replaced: count(short), per container xz(unsigned byte: x | z << 4) y(short);
then per section:
sy(byte) kind(byte) and either kind 0: count(short) and count positions (short: x | z << 4 | y << 8) or kind 1: the
4096-bit mask (512 bytes, bit i of byte i >> 3 for the position x | z << 4 | y << 8).
"""
import os, sys, struct, zlib, json, collections
from concurrent.futures import ProcessPoolExecutor
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anvil

SECTIONS, GROUND = 12, 64
NATURAL = ('minecraft:dirt', 'minecraft:bedrock')


def index(path):
    data = open(path, 'rb').read()
    assert data[:5] == b'OCV12', path
    n = struct.unpack('>i', data[6:10])[0]
    base = 10 + 10 * n
    out = {}
    rx, rz = map(int, os.path.basename(path).split('.')[1:3])
    for i in range(n):
        lx, lz, off, ln = struct.unpack('>bbii', data[10 + 10 * i:20 + 10 * i])
        out[(rx * 32 + lx, rz * 32 + lz)] = (path, base + off, ln)
    return out


def chunk_index(d):
    out = {}
    for f in os.listdir(d):
        if f.startswith('r.') and f.endswith('.bin'):
            out.update(index(os.path.join(d, f)))
    return out


def unpack(longs, bits):
    per = 64 // bits
    arr = np.array(longs, dtype=np.int64).view(np.uint64)
    shifts = (np.arange(per, dtype=np.uint64) * np.uint64(bits))
    vals = (arr[:, None] >> shifts[None, :]) & np.uint64((1 << bits) - 1)
    return vals.reshape(-1)[:4096].astype(np.int64)


def state_key(p):
    props = p.get('Properties') or {}
    name = p['Name']
    if name in NATURAL:
        return 'natural'
    if not props:
        return name
    return name + '[' + ','.join('%s=%s' % kv for kv in sorted(props.items())) + ']'


CONTAINERS = ('chest', 'barrel', 'shulker_box', 'dispenser', 'dropper', 'hopper', 'furnace', 'smoker', 'brewing_stand')


def blocks(entry, ids):
    """The chunk's blocks as (12, 4096) ids, index x | z << 4 | y << 8 per section."""
    path, off, ln = entry
    with open(path, 'rb') as f:
        f.seek(off)
        nbt = anvil.read_nbt(zlib.decompress(f.read(ln)))
    out = np.empty((SECTIONS, 4096), np.int32)
    air, nat = ids.setdefault('minecraft:air', len(ids)), ids.setdefault('natural', len(ids))
    for sy in range(SECTIONS):
        out[sy] = air if sy * 16 > GROUND else nat
        # a section that straddles the ground (y 64 is in section 4): below it natural, above it sky
    have = set()
    for s in nbt.get('sections', []):
        sy = s['Y']
        if not 0 <= sy < SECTIONS:
            continue
        bs = s.get('block_states')
        if not bs:
            continue
        pal = [ids.setdefault(state_key(p), len(ids)) for p in bs['palette']]
        if len(pal) == 1:
            out[sy] = pal[0]
        else:
            bits = max(4, (len(pal) - 1).bit_length())
            out[sy] = np.array(pal, np.int32)[unpack(bs['data'][1], bits)]
        have.add(sy)
    for sy in range(SECTIONS):
        if sy not in have and sy * 16 <= GROUND < sy * 16 + 16:
            ys = np.arange(4096) >> 8
            out[sy] = np.where(sy * 16 + ys > GROUND, air, nat)
    conts = set()
    for be in nbt.get('block_entities', []):
        if any(c in str(be.get('id', '')) for c in CONTAINERS):
            conts.add((be['x'] & 15, be['y'], be['z'] & 15))
    return out, conts


def work(args):
    key, new_entry, old_entries = args
    ids = {}
    new, new_conts = blocks(new_entry, ids)
    changed = np.zeros((SECTIONS, 4096), bool)
    old_conts = set()
    for e in old_entries:
        if e is None:
            continue
        old, conts = blocks(e, ids)
        changed |= old != new
        old_conts |= conts
    lost = []
    for x, y, z in sorted(old_conts):
        sy = y >> 4
        if 0 <= sy < SECTIONS and changed[sy, x | z << 4 | (y & 15) << 8]:
            lost.append((x, y, z))
    return key, changed, lost


def main():
    new_dir, out, olds = sys.argv[1], sys.argv[2], sys.argv[3:]
    new_idx = chunk_index(new_dir)
    old_idx = [chunk_index(d) for d in olds]
    jobs = [(k, new_idx[k], [o.get(k) for o in old_idx]) for k in sorted(new_idx)]
    body = bytearray()
    stats = collections.Counter()
    chunks = 0
    with ProcessPoolExecutor(4) as ex:
        for (cx, cz), changed, lost in ex.map(work, jobs, chunksize=16):
            stats['kingdom_containers'] += len(lost)
            secs = [sy for sy in range(SECTIONS) if changed[sy].any()]
            if not secs:
                continue
            chunks += 1
            body += struct.pack('>bbb', cx, cz, len(secs))
            # the kingdom's own containers of the earlier templates that are replaced: they are emptied first (their
            # stock would spill over the street); a player's chest where the kingdom's blocks change drops its items
            body += struct.pack('>h', len(lost)) + b''.join(struct.pack('>Bh', x | z << 4, y) for x, y, z in lost)
            for sy in secs:
                pos = np.nonzero(changed[sy])[0]
                stats['blocks'] += len(pos)
                stats['sections'] += 1
                if len(pos) * 2 < 512:
                    body += struct.pack('>bbh', sy, 0, len(pos)) + struct.pack('>%dh' % len(pos), *pos.tolist())
                else:
                    bits = np.packbits(changed[sy], bitorder='little')
                    body += struct.pack('>bb', sy, 1) + bits.tobytes()
    rev = int(os.environ.get('REVISION', '49'))
    raw = b'OCU1' + struct.pack('>ii', rev, chunks) + bytes(body)
    data = zlib.compress(raw, 9)
    open(out, 'wb').write(data)
    stats['chunks'] = chunks
    stats['bytes'] = len(data)
    print(json.dumps(stats))


if __name__ == '__main__':
    main()

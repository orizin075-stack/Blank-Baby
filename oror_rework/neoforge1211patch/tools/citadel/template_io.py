"""template_io.py: read and edit the capital's template (overlay/data/oror_supreme_bosses/citadel/v12/r.*.bin) in place.

The template is what extract.py made of the repaired save, and since 053 it also carries the user's own fixes (052
gatefix8), so the palace (palace.py) is rebuilt on it directly rather than on a save run through the pipeline again.

    t = Template(dir)
    t.get(x, y, z)            -> 'minecraft:stone_bricks' or 'minecraft:oak_stairs[facing=north,half=bottom,...]'
    t.set(x, y, z, state)     state as get gives it (properties in any order, missing ones left to the game)
    t.box(x0, x1, y0, y1, z0, z1) -> numpy array [x, y, z] of state keys (str), the bounds inclusive
    t.block_entities_in(x0, x1, y0, y1, z0, z1) -> [(x, y, z, nbt)]
    t.set_be(x, y, z, data)   a block entity (Python values as anvil_edit.be_nbt takes them)
    t.save(dir)               every region file again; chunks not touched keep their bytes

Coordinates are the save's (the castle at x 0, z 0, its ground at y 64), as CitadelData reads them. A section the
template leaves out is, for the generator, open sky above the ground and natural ground below it: one that an edit
needs is made so (air from y 64 up, dirt under).
"""
import os, struct, zlib
import numpy as np
import anvil, anvil_edit
from anvil import Typed

GROUND = 64


def norm(state):
    """A state key with its properties sorted, as get() gives them."""
    if '[' not in state:
        return state
    name, props = state[:-1].split('[', 1)
    return name + '[' + ','.join(sorted(props.split(','))) + ']'


class Template:
    def __init__(self, folder):
        self.folder = folder
        self.files = {}  # (rx, rz) -> bytes
        self.index = {}  # (cx, cz) -> ((rx, rz), offset, length, lx, lz)
        self.order = {}  # (rx, rz) -> [(lx, lz, cx, cz)] in the file's order
        for f in sorted(os.listdir(folder)):
            if not (f.startswith('r.') and f.endswith('.bin')):
                continue
            rx, rz = (int(v) for v in f[2:-4].split('.'))
            data = open(os.path.join(folder, f), 'rb').read()
            assert data[:5] == b'OCV12', f
            n = struct.unpack('>i', data[6:10])[0]
            base = 10 + n * 10
            entries = []
            for i in range(n):
                lx, lz, off, ln = struct.unpack('>bbii', data[10 + i * 10:20 + i * 10])
                cx, cz = rx * 32 + lx, rz * 32 + lz
                self.index[(cx, cz)] = ((rx, rz), base + off, ln, lx, lz)
                entries.append((lx, lz, cx, cz))
            self.files[(rx, rz)] = data
            self.order[(rx, rz)] = entries
        self.chunks = {}  # (cx, cz) -> typed nbt
        self.sections = {}  # (cx, cz) -> {sy: [pal keys list, idx array, dirty]}
        self.edited = {}  # (cx, cz) -> set of (x, y, z) replaced (their block entities go)
        self.new_bes = {}  # (cx, cz) -> {(x, y, z): data}

    # ------------------------------------------------------------------------------------------------ chunks

    def has_chunk(self, cx, cz):
        return (cx, cz) in self.index

    def chunk(self, cx, cz):
        c = self.chunks.get((cx, cz))
        if c is None:
            (rx, rz), off, ln, _, _ = self.index[(cx, cz)]
            raw = self.files[(rx, rz)][off:off + ln]
            c = anvil.read_nbt_typed(zlib.decompress(raw))
            self.chunks[(cx, cz)] = c
        return c

    def _section(self, cx, cz, sy, create):
        secs = self.sections.setdefault((cx, cz), {})
        s = secs.get(sy)
        if s is not None:
            return s
        nbt = self.chunk(cx, cz)
        for sec in nbt['sections']:
            if anvil.val(sec['Y']) == sy:
                bs = sec.get('block_states')
                pal, idx = anvil_edit.decode(bs)
                keys = [norm(anvil_edit.key(p)) for p in pal]
                s = [keys, idx.copy(), False]
                secs[sy] = s
                return s
        if not create:
            return None
        fill = 'minecraft:air' if sy * 16 >= GROUND else 'minecraft:dirt'
        s = [[fill], np.zeros(4096, np.int64), True]
        secs[sy] = s
        return s

    # ------------------------------------------------------------------------------------------------ blocks

    def get(self, x, y, z):
        cx, cz = x >> 4, z >> 4
        if not self.has_chunk(cx, cz):
            return None
        s = self._section(cx, cz, y >> 4, False)
        if s is None:
            return 'minecraft:air' if y >= GROUND else 'minecraft:dirt'
        return s[0][s[1][((y & 15) * 16 + (z & 15)) * 16 + (x & 15)]]

    def set(self, x, y, z, state):
        cx, cz = x >> 4, z >> 4
        if not self.has_chunk(cx, cz):
            return False
        state = norm(state if ':' in state.split('[')[0] else 'minecraft:' + state)
        s = self._section(cx, cz, y >> 4, True)
        keys, idx = s[0], s[1]
        i = ((y & 15) * 16 + (z & 15)) * 16 + (x & 15)
        if keys[idx[i]] == state:
            return False
        try:
            k = keys.index(state)
        except ValueError:
            k = len(keys)
            keys.append(state)
        idx[i] = k
        s[2] = True
        self.edited.setdefault((cx, cz), set()).add((x, y, z))
        return True

    def box(self, x0, x1, y0, y1, z0, z1):
        out = np.empty((x1 - x0 + 1, y1 - y0 + 1, z1 - z0 + 1), dtype=object)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                for z in range(z0, z1 + 1):
                    out[x - x0, y - y0, z - z0] = self.get(x, y, z)
        return out

    def block_entities_in(self, x0, x1, y0, y1, z0, z1):
        out = []
        for cx in range(x0 >> 4, (x1 >> 4) + 1):
            for cz in range(z0 >> 4, (z1 >> 4) + 1):
                if not self.has_chunk(cx, cz):
                    continue
                for be in self.chunk(cx, cz).get('block_entities') or []:
                    x, y, z = anvil.val(be['x']), anvil.val(be['y']), anvil.val(be['z'])
                    if x0 <= x <= x1 and y0 <= y <= y1 and z0 <= z <= z1:
                        out.append((x, y, z, be))
        return out

    def set_be(self, x, y, z, data):
        cx, cz = x >> 4, z >> 4
        d = dict(data)
        d['x'], d['y'], d['z'] = x, y, z
        self.new_bes.setdefault((cx, cz), {})[(x, y, z)] = d
        self.edited.setdefault((cx, cz), set()).add((x, y, z))

    # ------------------------------------------------------------------------------------------------ save

    def _encode(self, cx, cz):
        nbt = self.chunk(cx, cz)
        secs = self.sections.get((cx, cz), {})
        by_y = {anvil.val(s['Y']): s for s in nbt['sections']}
        for sy, (keys, idx, dirty) in secs.items():
            if not dirty:
                continue
            pal = [anvil_edit.state(k) for k in keys]
            enc = anvil_edit.encode(pal, idx)
            sec = by_y.get(sy)
            if sec is None:
                sec = {'Y': Typed(1, sy)}
                nbt['sections'].append(sec)
                by_y[sy] = sec
            sec['block_states'] = enc
        nbt['sections'].sort(key=lambda s: anvil.val(s['Y']))
        edited = self.edited.get((cx, cz), set())
        if edited and nbt.get('block_entities'):
            nbt['block_entities'] = [be for be in nbt['block_entities']
                                     if (anvil.val(be['x']), anvil.val(be['y']), anvil.val(be['z'])) not in edited]
        new = self.new_bes.get((cx, cz))
        if new:
            nbt['block_entities'] = list(nbt.get('block_entities') or []) + [anvil_edit.be_nbt(be) for _, be in sorted(new.items())]
        return zlib.compress(anvil.write_nbt(nbt), 9)

    def save(self, folder=None):
        folder = folder or self.folder
        os.makedirs(folder, exist_ok=True)
        touched = set(self.edited) | set(self.new_bes) | {k for k, v in self.sections.items() if any(s[2] for s in v.values())}
        for (rx, rz), entries in self.order.items():
            blobs, head = [], []
            off = 0
            for lx, lz, cx, cz in entries:
                if (cx, cz) in touched:
                    raw = self._encode(cx, cz)
                else:
                    _, o, ln, _, _ = self.index[(cx, cz)]
                    raw = self.files[(rx, rz)][o:o + ln]
                head.append(struct.pack('>bbii', lx, lz, off, len(raw)))
                blobs.append(raw)
                off += len(raw)
            data = b'OCV12' + bytes([1]) + struct.pack('>i', len(entries)) + b''.join(head) + b''.join(blobs)
            open(os.path.join(folder, f'r.{rx}.{rz}.bin'), 'wb').write(data)
        return len(touched)

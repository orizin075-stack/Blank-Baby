"""Minimal NBT reader/writer (gzip'd structure templates). Tags keep their type: values are wrapped in Tag(type, value)."""
import gzip, io, struct

class Tag:
    __slots__ = ('t', 'v')
    def __init__(self, t, v): self.t, self.v = t, v
    def __repr__(self): return f'Tag({self.t},{self.v!r})'

END, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, BYTES, STRING, LIST, COMPOUND, INTS, LONGS = range(13)

def _r(f, t):
    if t == BYTE: return struct.unpack('>b', f.read(1))[0]
    if t == SHORT: return struct.unpack('>h', f.read(2))[0]
    if t == INT: return struct.unpack('>i', f.read(4))[0]
    if t == LONG: return struct.unpack('>q', f.read(8))[0]
    if t == FLOAT: return struct.unpack('>f', f.read(4))[0]
    if t == DOUBLE: return struct.unpack('>d', f.read(8))[0]
    if t == BYTES:
        n = struct.unpack('>i', f.read(4))[0]; return list(struct.unpack(f'>{n}b', f.read(n)))
    if t == STRING:
        n = struct.unpack('>H', f.read(2))[0]; return f.read(n).decode('utf-8')
    if t == LIST:
        et = f.read(1)[0]; n = struct.unpack('>i', f.read(4))[0]
        return (et, [Tag(et, _r(f, et)) for _ in range(n)])
    if t == COMPOUND:
        d = {}
        while True:
            tt = f.read(1)[0]
            if tt == END: return d
            n = struct.unpack('>H', f.read(2))[0]; k = f.read(n).decode('utf-8')
            d[k] = Tag(tt, _r(f, tt))
    if t == INTS:
        n = struct.unpack('>i', f.read(4))[0]; return list(struct.unpack(f'>{n}i', f.read(4 * n)))
    if t == LONGS:
        n = struct.unpack('>i', f.read(4))[0]; return list(struct.unpack(f'>{n}q', f.read(8 * n)))
    raise ValueError(t)

def _w(f, t, v):
    if t == BYTE: f.write(struct.pack('>b', v))
    elif t == SHORT: f.write(struct.pack('>h', v))
    elif t == INT: f.write(struct.pack('>i', v))
    elif t == LONG: f.write(struct.pack('>q', v))
    elif t == FLOAT: f.write(struct.pack('>f', v))
    elif t == DOUBLE: f.write(struct.pack('>d', v))
    elif t == BYTES: f.write(struct.pack('>i', len(v))); f.write(struct.pack(f'>{len(v)}b', *v))
    elif t == STRING:
        b = v.encode('utf-8'); f.write(struct.pack('>H', len(b))); f.write(b)
    elif t == LIST:
        et, items = v
        if not items: et = END
        f.write(bytes([et])); f.write(struct.pack('>i', len(items)))
        for x in items: _w(f, et, x.v)
    elif t == COMPOUND:
        for k, x in v.items():
            f.write(bytes([x.t])); b = k.encode('utf-8'); f.write(struct.pack('>H', len(b))); f.write(b); _w(f, x.t, x.v)
        f.write(bytes([END]))
    elif t == INTS: f.write(struct.pack('>i', len(v))); f.write(struct.pack(f'>{len(v)}i', *v))
    elif t == LONGS: f.write(struct.pack('>i', len(v))); f.write(struct.pack(f'>{len(v)}q', *v))
    else: raise ValueError(t)

def load(path):
    raw = open(path, 'rb').read()
    if raw[:2] == b'\x1f\x8b': raw = gzip.decompress(raw)
    f = io.BytesIO(raw)
    t = f.read(1)[0]; n = struct.unpack('>H', f.read(2))[0]; name = f.read(n).decode('utf-8')
    return name, Tag(t, _r(f, t))

def save(path, name, root):
    f = io.BytesIO()
    f.write(bytes([root.t])); b = name.encode('utf-8'); f.write(struct.pack('>H', len(b))); f.write(b); _w(f, root.t, root.v)
    with open(path, 'wb') as out: out.write(gzip.compress(f.getvalue(), mtime=0))

def plain(tag):
    """Tag tree -> plain python (for inspection)."""
    t, v = tag.t, tag.v
    if t == COMPOUND: return {k: plain(x) for k, x in v.items()}
    if t == LIST: return [plain(x) for x in v[1]]
    return v

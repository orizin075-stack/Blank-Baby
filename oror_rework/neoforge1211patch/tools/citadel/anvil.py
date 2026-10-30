"""Minimal Anvil region + NBT reader (read-only)."""
import struct, zlib, gzip, io

def _r(f, n):
    b = f.read(n)
    if len(b) != n:
        raise EOFError
    return b

def read_tag(f, t):
    if t == 1: return struct.unpack('>b', _r(f, 1))[0]
    if t == 2: return struct.unpack('>h', _r(f, 2))[0]
    if t == 3: return struct.unpack('>i', _r(f, 4))[0]
    if t == 4: return struct.unpack('>q', _r(f, 8))[0]
    if t == 5: return struct.unpack('>f', _r(f, 4))[0]
    if t == 6: return struct.unpack('>d', _r(f, 8))[0]
    if t == 7:
        n = struct.unpack('>i', _r(f, 4))[0]; return ('B', _r(f, n))
    if t == 8:
        n = struct.unpack('>H', _r(f, 2))[0]; return _r(f, n).decode('utf-8', 'replace')
    if t == 9:
        et = _r(f, 1)[0]; n = struct.unpack('>i', _r(f, 4))[0]
        return [read_tag(f, et) for _ in range(n)]
    if t == 10:
        d = {}
        while True:
            et = _r(f, 1)[0]
            if et == 0: return d
            nl = struct.unpack('>H', _r(f, 2))[0]; name = _r(f, nl).decode('utf-8', 'replace')
            d[name] = read_tag(f, et)
    if t == 11:
        n = struct.unpack('>i', _r(f, 4))[0]; return ('I', struct.unpack('>%di' % n, _r(f, 4 * n)))
    if t == 12:
        n = struct.unpack('>i', _r(f, 4))[0]; return ('L', struct.unpack('>%dq' % n, _r(f, 8 * n)))
    raise ValueError(t)

def read_nbt(data):
    f = io.BytesIO(data)
    t = _r(f, 1)[0]
    nl = struct.unpack('>H', _r(f, 2))[0]; _r(f, nl)
    return read_tag(f, t)

def chunks(path):
    """Yield (cx_local, cz_local, raw_compressed_len, nbt) for each chunk in a region file."""
    data = open(path, 'rb').read()
    for i in range(1024):
        off = struct.unpack('>I', b'\0' + data[i * 4:i * 4 + 3])[0]
        cnt = data[i * 4 + 3]
        if off == 0 or cnt == 0:
            continue
        p = off * 4096
        ln = struct.unpack('>i', data[p:p + 4])[0]
        ct = data[p + 4]
        raw = data[p + 5:p + 4 + ln]
        if ct == 2: dec = zlib.decompress(raw)
        elif ct == 1: dec = gzip.decompress(raw)
        elif ct == 3: dec = raw
        else: continue
        yield i % 32, i // 32, ln, read_nbt(dec)


# ------------------------------------------------------------------------------------------- writing
def _w_payload(out, t, v):
    if t == 1: out.append(struct.pack('>b', v))
    elif t == 2: out.append(struct.pack('>h', v))
    elif t == 3: out.append(struct.pack('>i', v))
    elif t == 4: out.append(struct.pack('>q', v))
    elif t == 5: out.append(struct.pack('>f', v))
    elif t == 6: out.append(struct.pack('>d', v))
    elif t == 7: out.append(struct.pack('>i', len(v[1]))); out.append(v[1])
    elif t == 8:
        b = v.encode('utf-8'); out.append(struct.pack('>H', len(b))); out.append(b)
    elif t == 9:
        et = tag_type(v[0]) if v else 0
        out.append(bytes([et])); out.append(struct.pack('>i', len(v)))
        for x in v: _w_payload(out, et, x)
    elif t == 10:
        for k, x in v.items():
            xt = tag_type(x)
            out.append(bytes([xt])); kb = k.encode('utf-8'); out.append(struct.pack('>H', len(kb))); out.append(kb)
            _w_payload(out, xt, x)
        out.append(b'\0')
    elif t == 11: out.append(struct.pack('>i', len(v[1]))); out.append(struct.pack('>%di' % len(v[1]), *v[1]))
    elif t == 12: out.append(struct.pack('>i', len(v[1]))); out.append(struct.pack('>%dq' % len(v[1]), *v[1]))
    else: raise ValueError(t)

# python ints don't remember their NBT type: values read keep a hidden type map in TYPED
class Typed:
    __slots__ = ('t', 'v')
    def __init__(self, t, v): self.t, self.v = t, v

def tag_type(v):
    if isinstance(v, Typed): return v.t
    if isinstance(v, dict): return 10
    if isinstance(v, list): return 9
    if isinstance(v, str): return 8
    if isinstance(v, tuple): return {'B': 7, 'I': 11, 'L': 12}[v[0]]
    if isinstance(v, float): return 6
    if isinstance(v, bool): return 1
    if isinstance(v, int): return 3
    raise TypeError(type(v))

def write_nbt(root):
    out = [bytes([10]), struct.pack('>H', 0)]
    _w_payload_typed(out, 10, root)
    return b''.join(out)

def _w_payload_typed(out, t, v):
    if isinstance(v, Typed):
        return _w_payload_typed(out, v.t, v.v)
    if t == 9:
        et = tag_type(v[0]) if v else 0
        out.append(bytes([et])); out.append(struct.pack('>i', len(v)))
        for x in v: _w_payload_typed(out, et, x)
        return
    if t == 10:
        for k, x in v.items():
            xt = tag_type(x)
            out.append(bytes([xt])); kb = k.encode('utf-8'); out.append(struct.pack('>H', len(kb))); out.append(kb)
            _w_payload_typed(out, xt, x)
        out.append(b'\0')
        return
    _w_payload(out, t, v)


def read_tag_typed(f, t):
    """As read_tag, but numbers keep their NBT type (so a chunk can be written back unchanged)."""
    if t in (1, 2, 3, 4, 5, 6):
        return Typed(t, read_tag(f, t))
    if t == 9:
        et = _r(f, 1)[0]; n = struct.unpack('>i', _r(f, 4))[0]
        return [read_tag_typed(f, et) for _ in range(n)]
    if t == 10:
        d = {}
        while True:
            et = _r(f, 1)[0]
            if et == 0: return d
            nl = struct.unpack('>H', _r(f, 2))[0]; name = _r(f, nl).decode('utf-8', 'replace')
            d[name] = read_tag_typed(f, et)
    return read_tag(f, t)

def read_nbt_typed(data):
    f = io.BytesIO(data)
    t = _r(f, 1)[0]
    nl = struct.unpack('>H', _r(f, 2))[0]; _r(f, nl)
    return read_tag_typed(f, t)

def chunks_typed(path):
    data = open(path, 'rb').read()
    for i in range(1024):
        off = struct.unpack('>I', b'\0' + data[i * 4:i * 4 + 3])[0]
        cnt = data[i * 4 + 3]
        if off == 0 or cnt == 0:
            continue
        p = off * 4096
        ln = struct.unpack('>i', data[p:p + 4])[0]
        ct = data[p + 4]
        raw = data[p + 5:p + 4 + ln]
        dec = zlib.decompress(raw) if ct == 2 else (gzip.decompress(raw) if ct == 1 else raw)
        yield i % 32, i // 32, read_nbt_typed(dec)

def val(x):
    return x.v if isinstance(x, Typed) else x

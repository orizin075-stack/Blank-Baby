"""seal_book.py <dueldominion jar> <bound_hair.png> <out jar>: (r70, the user: "髪じゃない　本") the sealed mob's item is a
book, not a lock of hair. The jar as the user sent it named it 支配の封印髪 / Bound Hair Seal (its id bound_hair) and said
封印髪 in its messages; here its name, its eight messages and its texture say 封印書 (a sealed book). The id stays
bound_hair, so seals already in the world are kept. Strings in the classes are changed byte for byte (封印髪 and 封印書 are
the same length in UTF-8), nothing else in them.

(r71, the look run) Its summoning line said "右クリック＝憑依、Shift＋右クリック＝融合" but possession and fusion take an empty main
hand (the seal book still in hand, nothing happened): the line now says so ("素手で"). That string changes length, so its
constant is rewritten with its new length (the class file's other parts refer to constants by number, not by place)."""
import json
import sys
import zipfile

src, png, out = sys.argv[1:4]
OLD, NEW = '封印髪'.encode('utf-8'), '封印書'.encode('utf-8')
assert len(OLD) == len(NEW)
changed = {'classes': 0, 'strings': 0, 'messages': 0}
MESSAGES = {'　右クリック＝憑依、Shift＋右クリック＝融合。': '　素手で右クリック＝憑依、素手でShift＋右クリック＝融合。'}


def rewrite_utf8(b, table):
    """The class file b with each CONSTANT_Utf8 entry holding a key of table changed (its length rewritten), and the count."""
    import struct
    n = struct.unpack('>H', b[8:10])[0]
    out, i, k, hits = bytearray(b[:10]), 10, 1, 0
    while k < n:
        t = b[i]
        if t == 1:
            ln = struct.unpack('>H', b[i + 1:i + 3])[0]
            raw = b[i + 3:i + 3 + ln]
            text = raw.decode('utf-8', 'surrogatepass') if b'\xc0\x80' not in raw else None
            if text is not None and any(k in text for k in table):
                for key, value in table.items():
                    text = text.replace(key, value)
                new = text.encode('utf-8')
                out += bytes([1]) + struct.pack('>H', len(new)) + new
                hits += 1
            else:
                out += b[i:i + 3 + ln]
            i += 3 + ln
        else:
            size = {3: 5, 4: 5, 5: 9, 6: 9, 7: 3, 8: 3, 16: 3, 19: 3, 20: 3, 9: 5, 10: 5, 11: 5, 12: 5, 17: 5, 18: 5, 15: 4}[t]
            out += b[i:i + size]
            i += size
            if t in (5, 6):
                k += 1
        k += 1
    out += b[i:]
    return bytes(out), hits
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out + '.tmp', 'w', zipfile.ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        d = zin.read(info.filename)
        n = info.filename
        if n.endswith('.class') and OLD in d:
            changed['classes'] += 1
            changed['strings'] += d.count(OLD)
            d = d.replace(OLD, NEW)
        if n.endswith('.class'):
            d, hits = rewrite_utf8(d, MESSAGES)
            changed['messages'] += hits
        elif n == 'assets/dueldominion/lang/ja_jp.json':
            j = json.loads(d.decode('utf-8'))
            j['item.dueldominion.bound_hair'] = '支配の封印書'
            for k, v in j.items():
                j[k] = v.replace('封印髪', '封印書')
            d = json.dumps(j, ensure_ascii=False, indent=2).encode('utf-8')
        elif n == 'assets/dueldominion/lang/en_us.json':
            j = json.loads(d.decode('utf-8'))
            j['item.dueldominion.bound_hair'] = 'Bound Seal Book'
            d = json.dumps(j, ensure_ascii=False, indent=2).encode('utf-8')
        elif n == 'assets/dueldominion/textures/item/bound_hair.png':
            d = open(png, 'rb').read()
        zout.writestr(info, d)
import os
os.replace(out + '.tmp', out)
print(json.dumps(changed))

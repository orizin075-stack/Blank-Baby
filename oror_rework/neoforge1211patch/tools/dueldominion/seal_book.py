"""seal_book.py <dueldominion jar> <bound_hair.png> <out jar>: (r70, the user: "髪じゃない　本") the sealed mob's item is a
book, not a lock of hair. The jar as the user sent it named it 支配の封印髪 / Bound Hair Seal (its id bound_hair) and said
封印髪 in its messages; here its name, its eight messages and its texture say 封印書 (a sealed book). The id stays
bound_hair, so seals already in the world are kept. Strings in the classes are changed byte for byte (封印髪 and 封印書 are
the same length in UTF-8), nothing else in them."""
import json
import sys
import zipfile

src, png, out = sys.argv[1:4]
OLD, NEW = '封印髪'.encode('utf-8'), '封印書'.encode('utf-8')
assert len(OLD) == len(NEW)
changed = {'classes': 0, 'strings': 0}
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out + '.tmp', 'w', zipfile.ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        d = zin.read(info.filename)
        n = info.filename
        if n.endswith('.class') and OLD in d:
            changed['classes'] += 1
            changed['strings'] += d.count(OLD)
            d = d.replace(OLD, NEW)
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

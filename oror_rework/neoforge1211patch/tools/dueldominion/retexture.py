"""retexture.py <dueldominion jar> <textures dir> <models dir> <out jar>: the user's Duel Dominion jar with its item
textures replaced by the ones textures.py draws and its item models from models/ (replaced, or added: the grimoire's
open-book model), every other entry (the classes, lang, data) copied as it is."""
import os
import sys
import zipfile

src, tex, models, out = sys.argv[1:5]
add = {}
for f in os.listdir(tex):
    if f.endswith('.png'):
        add['assets/dueldominion/textures/item/' + f] = os.path.join(tex, f)
for f in os.listdir(models):
    if f.endswith('.json'):
        add['assets/dueldominion/models/item/' + f] = os.path.join(models, f)
replaced, added = 0, 0
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out + '.tmp', 'w', zipfile.ZIP_DEFLATED) as zout:
    names = set(zin.namelist())
    for info in zin.infolist():
        if info.filename in add:
            with open(add[info.filename], 'rb') as f:
                zout.writestr(info, f.read())
            replaced += 1
        else:
            zout.writestr(info, zin.read(info.filename))
    for name, path in sorted(add.items()):
        if name not in names:
            zout.write(path, name)
            added += 1
os.replace(out + '.tmp', out)
print('replaced', replaced, 'added', added)

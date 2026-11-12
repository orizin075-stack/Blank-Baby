"""retexture.py <dueldominion jar> <textures dir> <out jar>: the user's Duel Dominion jar with its item textures replaced
by the ones textures.py draws (every other entry, the classes, models, lang and data, copied as they are)."""
import os
import sys
import zipfile

src, tex, out = sys.argv[1:4]
prefix = 'assets/dueldominion/textures/item/'
mine = {prefix + f: os.path.join(tex, f) for f in os.listdir(tex) if f.endswith('.png')}
replaced = 0
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out + '.tmp', 'w', zipfile.ZIP_DEFLATED) as zout:
    names = set(zin.namelist())
    for info in zin.infolist():
        if info.filename in mine:
            with open(mine[info.filename], 'rb') as f:
                zout.writestr(info, f.read())
            replaced += 1
        else:
            zout.writestr(info, zin.read(info.filename))
    missing = [k for k in mine if k not in names]
os.replace(out + '.tmp', out)
print('replaced', replaced, 'textures; not in the jar:', missing)

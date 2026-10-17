#!/bin/bash
# Install the Blockbench-style character assets (tools/mc/build_bb.py output) into the jar overlay.
S=/tmp/claude-0/-home-user-Blank-Baby/604d9462-06d6-550f-ad6a-fa3404aa3d62/scratchpad
SRC=$S/mc_out/bb
O=$S/build/overlay/assets/oror_supreme_bosses
python3 - "$SRC/rigs.json" "$O/rigs.json" <<'PY'
import json, sys
new = json.load(open(sys.argv[1]))
old = json.load(open(sys.argv[2]))
missing = sorted(set(old) - set(new))
if missing:
    raise SystemExit(f'rigs missing from the new build: {missing}')
json.dump(new, open(sys.argv[2], 'w'), separators=(',', ':'))
print(len(new), 'rigs installed')
PY
mkdir -p $O/meshes $O/textures/entity
rm -f $O/meshes/*.bin
cp $SRC/meshes/*.bin $O/meshes/
for f in $SRC/textures/*.png; do cp "$f" $O/textures/entity/; done
ls $O/meshes | wc -l
# the game parses rigs.json with Gson into RigModel's classes and reads meshes/*.bin: check both exactly that way
java -cp $S/meshtest:$S/tools/lib/gson.jar RigsCheck $O 2>&1 | grep -v "^Picked" | tail -3
java -cp $S/meshtest MeshCheck $O 2>&1 | grep -v "^Picked" | tail -1

# OROR War × Nightfall — rework workspace (v0.15.2)

Release: `dist/OROR_War_Nightfall_v0.15.2_Import.zip` (CurseForge import, NeoForge 21.1.262 / Minecraft 1.21.1).
v0.15.0-v0.16.0 failed to load (the recompiled tooltip subscriber lost its runtime-visible @SubscribeEvent); fixed in
v0.15.2, and `java/compile.sh` now checks annotation visibility against the original jar (`tools/stubgen/AnnCheck.java`).
Change notes: `tools/CHANGES_JA.md`. The zip also carries `RELIC_ARTS_v0.15.2_JA.md`, the list of all 205 relic arts.

## 3D relic arsenal
- `tools/mc/forge3d.py` — 3D item builder: rotated boxes painted with box-UV painters, and pixel-art relief plates
  extruded into smooth lens-bevelled slabs (`relief.py`). Exports OBJ + MTL (`base` / full-bright `glow` material for
  NeoForge's `emissive_ambient`) and one packed texture per item.
- `tools/mc/w3designs.py`, `w3d_b.py`, `w3d_c.py` — the 41 relic weapons and their awakened legend forms.
- `tools/mc/w3artifacts.py` — focus and charm relics (archetypes chosen by name, character palettes).
- `tools/mc/held.py` — display transforms derived from vanilla's hand transform chain (sword / fist / shield / palm).
- `tools/mc/icons3d.py` — 32px inventory icons rendered from the 3D models.
- `tools/mc/export3d.py <assets>` and `export3d.py --artifacts <assets> <relics.json>` — write models, textures,
  icons and `neoforge:separate_transforms` item models (3D in hands, icon in the GUI).

## Relic arts (unique effects)
- `java/src/jp/oror/reborn/RelicArts.java` — data-driven interpreter (cast / passive / on-hit programs).
- `tools/mc/relic_arts*.py` + `relic_arts_build.py <assets> <relics.json>` — the 205 programs, names and ja/en lang.

## Build
- `java/compile.sh` compiles `java/src` against stubs; new Minecraft refs must be listed in `java/allow.txt` and
  `tools/extra_refs.txt` (hand-checked against 1.21.1).
- `tools/package.py <workspace> <out> <version>` builds the jar and the import zip.

## Sculpted characters (on hold: the sculpted look is being redesigned; notes in `tools/CHANGES_SCULPT_WIP_JA.md`)
- `java/src/jp/oror/reborn/client/RigModel.java` reads an optional `meshes/<key>.bin` per rig: smooth per-vertex-normal
  quads attached to the rig bones (plus the emissive subset for the glow pass); blink / knee / elbow animations.
- `tools/mc/sculpt.py` (lofts, rounded boxes, relief plates, UV-space baking with ambient occlusion, mesh export),
  `spaint.py` (painters), `figure.py` (humanoid builder), `wings3d.py`, `trinkets.py`, `chars3d.py`, `build3d.py <out> [names]`.

## Characters
- `tools/mc/` (chars.py, creatures.py, humanoid.py, paint.py) — character rigs and textures; `build.py <out>` writes
  `rigs.json`. `docs/character_settings_41.txt` — the 41 setting texts everything follows.

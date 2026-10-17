# OROR War × Nightfall — rework workspace (v0.17.4)

Release: `dist/OROR_War_Nightfall_v0.17.4_Import.zip` (CurseForge import, NeoForge 21.1.262 / Minecraft 1.21.1).
v0.17.0 rebuilt all 46 character models in the Blockbench style (crisp cuboids, pixel-art textures); v0.17.1 redraws
the faces in the vanilla Minecraft skin grammar (8x8: two-pixel eyes on row 4, two-pixel mouth, hair rows).
v0.17.2 fixes rigs.json failing to load in game (a non-numeric hair bone param); `java/meshtest/RigsCheck.java` now
parses rigs.json with Gson into RigModel's own classes, and `MeshCheck.java` reads the meshes like RigModel.
v0.17.3 gives every relic weapon a kind instead of making all of them swords (katana, polearm, heavy, fist, whip,
catalyst, gatling, cannon, bow, shield...): see "Weapon kinds" below.
v0.17.4 gives each kind a special skill (`WeaponSkills.java`), makes arts 1.5x stronger with colour-tinted cast and
impact effects (`RelicEffects.java`), and removes 275 clutter items (`tools/mc/prune_items.py`).
v0.15.0-v0.16.0 failed to load (the recompiled tooltip subscriber lost its runtime-visible @SubscribeEvent); fixed in
v0.15.2, and `java/compile.sh` now checks annotation visibility against the original jar (`tools/stubgen/AnnCheck.java`).
Change notes: `tools/CHANGES_JA.md`. The zip also carries `RELIC_ARTS_v0.17.4_JA.md`, the list of all 164 relic arts.

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

## Weapon kinds
- `tools/mc/weapon_kinds.py <assets>` — the 16 kinds (attack speed, damage multiplier, reach, knockback, sweep,
  right-click mode), the kind of each character's weapon (its legend and dungeon replica share it) and of the 33
  NightfallCraft counterparts; writes `weapon_kinds.json` and the tooltip strings.
- `java/src/jp/oror/reborn/CharacterRelics.java` — `Blade` (SwordItem: melee kinds, catalysts, guns, cannons),
  `Bow` (BowItem, no ammunition) and `Shield` (ShieldItem). Shooting and guarding kinds keep right-click for the
  weapon and cast their art on sneak + right-click, with the art cooldown on a clock of its own (item cooldowns
  would block the weapon). `RelicArts.shot` is the bolt / gatling / shell attack.
- `java/meshtest/KindCheck.java` parses `weapon_kinds.json` with Gson the way `CharacterRelics` does.
- `java/src/jp/oror/reborn/WeaponSkills.java` — the special skill of each kind (katana iai flash, greatsword quake,
  scythe reap, fist combo, shield perfect guard, light arrows...), hooked into `RelicArts.incoming`.
- `java/src/jp/oror/reborn/RelicEffects.java` — magic circles, arcs, beams and expanding rings in the character colour.

## Removed items (v0.17.4)
- `tools/mc/prune_items.py <jar tree> <overlay>` — the 275 removed items (per-character citadel bricks, guard eggs,
  essences and seal items, the 41 Echo replicas, the 70 NightfallCraft stand-ins): rewrites the loot tables that
  dropped them, drops their lang keys, and `package.py` leaves their models and data out of the jar. Seal blocks stay.
  NightfallCraft quest items whose mods are not in the pack now count as done (`NightfallFusion.java`).

## Build
- `java/compile.sh` compiles `java/src` against stubs; new Minecraft refs must be listed in `java/allow.txt` and
  `tools/extra_refs.txt` (hand-checked against 1.21.1).
- `tools/package.py <workspace> <out> <version>` builds the jar and the import zip.

## Characters (Blockbench style, v0.17.0)
- `java/src/jp/oror/reborn/client/RigModel.java` reads `meshes/<key>.bin` per rig: quads attached to the rig bones
  (plus the emissive subset for the glow pass); blink / knee / elbow animations.
- `tools/mc/bb.py` — cuboids with per-face pixel-art regions, optionally rotated about a pivot like Blockbench
  elements; `bb.enable()` turns the sculpt toolkit's lofts, rings, rounded boxes and reliefs into box chains, box rings,
  sharp boxes and stepped pixel extrusions, so the creature and trinket recipes build in the same style.
- `tools/mc/figure_bb.py` — humanoid builder (same API as `figure.py`): 8x8x8 head, chest / waist / pelvis boxes, elbows
  and knees, hair shell with cut-out fringe plus 3D strands, skirt and robe panels, sleeves, capes, armour.
- `tools/mc/mcface.py` — faces in the vanilla skin grammar (studied from Steve, Alex, the seven new default skins,
  villagers and illagers): 8x8, white + iris eyes on row 4, two-pixel mouth, hair rows, hat-layer fringe; blink lids.
  `bbface.py` keeps the colour ramps (and the earlier 16x16 anime eyes, unused). `bbpaint.py` — material painters.
- `tools/mc/build_bb.py <out> [names]` builds rigs.json, meshes, textures and previews from `chars3d.py`,
  `creatures3d.py` and `creatures_sc.py`.
- Older sculpted toolkit (`sculpt.py`, `spaint.py`, `figure.py`, `build3d.py`) is kept as the base the recipes and
  `bb.py` build on.

## Characters
- `tools/mc/` (chars.py, creatures.py, humanoid.py, paint.py) — character rigs and textures; `build.py <out>` writes
  `rigs.json`. `docs/character_settings_41.txt` — the 41 setting texts everything follows.

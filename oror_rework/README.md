# OROR War × Nightfall — rework workspace (v0.17.18)

Release: `dist/OROR_War_Nightfall_v0.17.18_Import.zip` (CurseForge import, NeoForge 21.1.262 / Minecraft 1.21.1).
v0.17.0 rebuilt all 46 character models in the Blockbench style (crisp cuboids, pixel-art textures); v0.17.1 redraws
the faces in the vanilla Minecraft skin grammar (8x8: two-pixel eyes on row 4, two-pixel mouth, hair rows).
v0.17.2 fixes rigs.json failing to load in game (a non-numeric hair bone param); `java/meshtest/RigsCheck.java` now
parses rigs.json with Gson into RigModel's own classes, and `MeshCheck.java` reads the meshes like RigModel.
v0.17.3 gives every relic weapon a kind instead of making all of them swords (katana, polearm, heavy, fist, whip,
catalyst, gatling, cannon, bow, shield...): see "Weapon kinds" below.
v0.17.4 gives each kind a special skill (`WeaponSkills.java`), makes arts 1.5x stronger with colour-tinted cast and
impact effects (`RelicEffects.java`), and removes 275 clutter items (`tools/mc/prune_items.py`).
v0.17.5 multiplies relic weapon damage by rank (weapon 3x, legend 4x: `POWER` in `weapon_kinds.py`) and makes them
unbreakable (`damageItem` returns 0).
v0.17.6 strengthens focus/charm relics (held attribute bonuses, 2x art power) and the 41 characters: signature
attacks by weapon kind, awakening at half health, resolve against huge hits (`BossPowers.java`) and tuned stats
(`tools/mc/boss_tuning.py`, checked by `java/meshtest/RosterCheck.java`).
v0.17.7 gives each character five named multi-tick moves out of 24 and a movement style (`BossMoves.java`,
`tools/mc/boss_moves.py`, checked by `java/meshtest/MovesCheck.java`), plus footwork and airborne poses in `RigModel`.
v0.17.8 fixes relic arts never firing with Epic Fight (its battle mode turns right-click into guard for sword-type
weapons and cancels the use): Epic Fight types now follow the weapon kind (`EPIC_FIGHT` in `weapon_kinds.py`;
shooting and guarding relics have none), and the swap-hands key casts arts (`CharacterRelics.swapHands`). Characters
keep their relic instead of AdaptiveCombat's vanilla weapon picks.
v0.17.9 splits villages into guards (fighting professions, level 4+) and villagers (`VillageAI.java`): guards hold a post
at the village centre with a leash, prefer threats to villagers and players, raise an alarm, patrol and keep a night
watch; villagers flee home or behind a guard instead of charging. Walks are set as ground speeds (`VillageAI.pace`),
since profession/growth bonuses times the old 1.1-1.35 multipliers had villagers running at 20-80 blocks/s;
`VillagerLife` keeps one job at a time and walks to the nearest candidate once; every smart mob's combat spacing is
per-tick `MoveControl.strafe` footwork instead of velocity kicks. `MindGameTests` now uses armorers as the guards.
v0.17.10 holds staff-shaped catalysts upright (`held.derive_staff`, `STAFF` in `export3d.py`, `--display` rewrites only
the transforms), fires bolts from the weapon and credits relic magic damage to the player (`indirectMagic`: kills gave
no experience), and gives the 41 characters basic attacks by weapon kind (`BossArms.java`): melee kinds walk into reach
(the base AI's 9-block stand-off predates kinds) and strike at their kind's pace, shooting kinds fire bolts, rounds,
shells or light shots, also for lore-mode characters in AdaptiveCombat instead of plain arrows.
v0.17.11 lets focus and charm relics be worn in Curios slots of their own (`java/overlay/data/*/curios`, tags in
`data/curios/tags/item`): Curios ticks worn items with slot -1, so `CharacterRelics.held` applies their bonuses as
transient modifiers (`wear`/`unwear`) and F casts the worn focus's then charm's art. Cannon shells fly
(`RelicShells.java`, server-simulated, drawn with particles), guns aim into the first-person view (`held.gun_fp`) and
fists get normal reach and punch feedback.
v0.17.12 fixes guns: holding another mod's gun puts the player in Epic Fight's vanilla mode (`GunCompat.java`, by
reflection; battle mode turned every shot into a melee swing), mobs carrying other mods' guns are left to those mods' AI
(`AdaptiveCombat.nativeGunner`: no double firing, no swapping to vanilla weapons, swapped guns restored), foreign
weapons are never swapped, and gun-mod bullets no longer make mobs raise shields.
v0.17.13 tones down the Suppression mod's screen darkening (`tools/pack_config/` replaces pack config files in the zip),
leaves mobs Epic Fight animates and other mods' mobs to their own AI (`AdaptiveCombat.drivenElsewhere`,
`EpicFightBridge.java`), arms ordinary villagers only in danger (`VillageAI.gear`; guards always) and sends them home to
sleep at night while the guards keep the night watch (`VillageAI.bedtime`).
v0.17.14 makes the eight fighting trades strong villagers instead of guards (they work, sleep and arm only in danger,
but fight what threatens them within 16 blocks: `VillageAI.strong`/`stand`); the guards are Guard Villagers' own, left to
their own AI. Village work follows what the village lacks (`VillageWork.java`: a 30-second survey; chests, a campfire, job
blocks, torches on dark ground, bread, beds and houses for the homeless, made from real recipes step by step, with
materials fetched from the communal chests, trees felled whole, logs burnt to charcoal and sheep shorn); shaped recipes
are laid on a grid of their own size (`VillagerLife.craft`), and fields grow from their edges. Miners get work clothes and
a lit hard hat on the human villager model and new vanilla-model textures (`tools/mc/villager_outfits.py`).
v0.17.15 lets villages grow (`VillageProgress.java`: 開拓地 to 天空の都, saved per village). Miners smelt blast-only ores in
a blast furnace they build (`VillagerIndustry.blast`). Villages send expeditions to dungeons, the Nether (through an
obsidian gate they build and light only while passing) and the End (`VillageExpeditions.java`; members leave the world as
saved data and come back as veterans). Strange villages' monstrous expedition parties sometimes roam near players.
Airships and biplanes from Immersive Aircraft carry trade between villages (`VillageFlights.java`). Grown villages make
Superb Warfare guns (`VillageArms.java`; mobs now reload and work bolts in `MobEquipmentUse`) and send out Superb Warfare
tanks and jets crewed by strong villagers when serious threats come near (`VillageVehicles.java`).
v0.17.16 makes wandering parties rich and unforgiving (`VillageFeuds.java`: full gear and a travel pack as drops; a
member that escapes makes the player an enemy of every village; rival parties fight; hunters chase outlaws), sends grand
villages against other mods' dungeons (their own chest loot tables, rolled for real) and gives them a great wish (the
dragon egg and an end ship's dragon head, enshrined on an altar; both make a 竜の都). Wandering traders sell Superb
Warfare arms at huge prices, steal from village chests and, struck or seen, turn into debuffers with llama sentry turrets;
rare armed caravans carry unobtainable goods (`WanderingTraders.java`). Raids bring a messenger who tries to teleport
home; one that gets away brings a horde of a hundred and more (`VillageRaids.java`).
v0.17.17 adds five surface structures generated from code (`tools/mc/structgen.py` writes the NBT templates and the
jigsaw/structure-set/pool/biome-tag JSON into `java/overlay`): illager fortresses and cities (the hordes' headquarters;
killing their commander calls the hordes off), villager fortresses, trader exchanges and villager kingdoms (their
villagers raise their village's stage, `VillageExpeditions.settle`). Villagers now really put issued gear away when calm.
v0.17.18 carries in what NightfallCraft 2.2.8.6 wrote itself as config (`NightfallRules.java`): its Multiplayer Boss
Fight scaling (per extra player near a boss: damage taken divided by 1.4, i.e. +40% toughness past the 1024 health cap,
and +10% attack) and its InControl spawn caps (700 of a kind per dimension, creepers 3 per player, ...); its Iron's
Spells tweaks ship as datapack spell configs. The quest chapters were already in (232 quests, identical);
`NightfallFusion` now hides quests this pack cannot do instead of paying them for free, lets the quests behind them
through, honours optional tasks and spell levels, and matches skill books and enchanted books
(`tools/quest_reach.py` replays these rules on the quest file).
v0.15.0-v0.16.0 failed to load (the recompiled tooltip subscriber lost its runtime-visible @SubscribeEvent); fixed in
v0.15.2, and `java/compile.sh` now checks annotation visibility against the original jar (`tools/stubgen/AnnCheck.java`).
Change notes: `tools/CHANGES_JA.md`. The zip also carries `RELIC_ARTS_v0.17.18_JA.md`, the list of all 164 relic arts.

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

# OROR Reborn — NeoForge 1.21.1 patch builds (0.17.24 and later)

The OROR War × Nightfall pack moved on to 0.17.19–0.17.23 elsewhere; those sources are not in this repository. A release
here is the shipped jar (`base/`) with only the classes in `src/main/java` rebuilt and swapped in, and translations
merged from `lang/<namespace>/<language>.json`.

- `.github/workflows/oror1211.yml` (GitHub Actions, which reach the NeoForge and CurseForge hosts): fetches the pack's
  mod jars by `tools/cf_fetch.py` (names and SHA-256 from `pack/lock-0.17.23.json`, CurseForge file ids from the
  manifest), compiles `src/main/java` against NeoForge 21.1.262 with ModDevGradle and those jars, checks the mixin target
  methods in the real jars, and makes `out/oror_supreme_bosses-<version>.jar` with `tools/patch_jar.py`. The jar and
  `out/report.txt` are committed back to the branch.
- `src/main/java` holds the rebuilt classes as readable source (decompiled from 0.17.23, then changed).

## 0.17.24

- `NightfallIdleAiMixin`: villagers are no longer throttled. VillageAI's threat scans run on the world clock
  ((gameTime + id) % 10), which met the throttled ticks for one villager in five; the rest never noticed an enemy.
- `NightfallMagicAttackMixin`: the magic weapons' dash/air spell goes through Iron's `canBeCastedBy` (mana, cooldown,
  learned) like any other cast.
- `NightfallBasicParry`: Guard is replaced by Parrying once per player, so choosing Guard again sticks.
- `NightfallSetupCheck` (new): a player joining a game without Nightfall or Sword Soaring is told to run
  `SETUP_NIGHTFALL.cmd`.
- Translations for the Incinerator Soul and the four sheaths (tcrcore, en/ja/zh), and the setup message.

## 0.17.25

Built on the 0.17.24 "native combat" jar made elsewhere (`base/oror_supreme_bosses-0.17.24.jar`: NightfallCraft's enemy
behaviour through an Indestructible compatibility build, Nightfall's own parry and starter skills). My 0.17.24 fixes
were made on 0.17.23 and are carried over; `out/oror_supreme_bosses-0.17.24.jar` is that other, earlier 0.17.24.

- `NightfallIdleAiMixin`, `NightfallMagicAttackMixin`, `NightfallSetupCheck`: the 0.17.24 fixes above (that jar still
  had the 0.17.23 classes); the setup check also names a missing Indestructible.
- `NightfallBasicParry` (that jar's source, reformatted): plain Guard is replaced by Nightfall's parry on the first
  check only, not every second; nothing is touched without Nightfall, whose classes are only loaded when it is.
- `CompatibilityMixinPlugin`: the mixins on Nightfall's or Indestructible's classes are skipped without those mods; the
  config is required, so a profile without them stopped at start-up instead of saying what is missing.
- `NightfallNativeParryFeedbackMixin` (that jar's source): damage without a direct entity is skipped.
- `NightfallCraftGui` (new): NightfallCraft's menus. From the TCR Core images SETUP_NIGHTFALL.cmd copies, an
  always-on built-in pack with the 1.21.1 button, tab and separator sprites (cut from TCR Core's 1.20.1 widget sheet),
  and TCR Core's cover image behind menus opened outside a world; nothing without the images.
- Translations (tcrcore, en/ja/zh) for the tooltips of NightfallCraft's title-screen icon buttons, whose FancyMenu
  layout names TCR Core's keys.
- `NightfallPatchSettings`: `compactHud` defaults to false. 0.17.22 hid every Ares HUD layer (stamina, guard and parry,
  mana) and drew a plain health row instead; the 0.17.25 pack also ships `compactHud=false`.
- The rest of 0.17.25 is the pack around the jar: NightfallCraft's screens and combat feel, in `oror_rework/nfc_ui`.

## 0.17.26

Built on the other 0.17.25 (`base/oror_supreme_bosses-0.17.25.jar`, made elsewhere on the 0.17.24 native-combat jar):
that jar adds only Nightfall weapon model fixes (`assets/efn`: eleven `_e`/alias weapons that rendered as missing
textures, Excalibur's item model, the flag bearer's inventory mesh), NightfallCraft's 433 Epic Fight combat items
(`oror_combat_preferred025.json`) and automatic combat mode. Every class of my 0.17.25 above is carried over on it.

- `NightfallAutomaticCombat`, `NightfallAutomaticCombatClient`: that jar forced combat mode on the server and the client
  every tick while a weapon was held, so R did nothing until the weapon was put away. Combat mode is now turned on when
  a weapon is taken and during the first three seconds in a world (a player saved in the vanilla mode), on the client;
  Epic Fight sends the mode to the server. R switches back until another item is taken.

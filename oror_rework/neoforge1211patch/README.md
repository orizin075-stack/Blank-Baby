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

- `NightfallPatchSettings`: `compactHud` defaults to false. 0.17.22 hid every Ares HUD layer (stamina, guard and parry,
  mana) and drew a plain health row instead; the 0.17.25 pack also ships `compactHud=false`.
- The rest of 0.17.25 is the pack around the jar: NightfallCraft's screens and combat feel, in `oror_rework/nfc_ui`.

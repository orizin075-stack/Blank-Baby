# OROR War × Nightfall 0.14.0 — rework workspace

- `tools/mc/` — Minecraft-style character model and texture generator (box-UV rigs, 8x8 faces, held props).
  `python3 build.py <out>` writes textures, glow maps, previews and `rigs.json` for the mod.
- `java/src/` — patched sources of `oror_supreme_bosses` (renderer, AI, village and gameplay fixes).
- `java/allow.txt` — new Minecraft API references, hand-checked against 1.21.1.
- `docs/character_settings_41.txt` — the 41 character setting texts the models and behaviour follow.

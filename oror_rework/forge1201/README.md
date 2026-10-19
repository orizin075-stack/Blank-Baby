# OROR Reborn — Forge 1.20.1 port (for NightfallCraft 2.2.8.6)

Work in progress: the NeoForge 21.1 / Minecraft 1.21.1 mod (`../java`) carried to Forge 47 / Minecraft 1.20.1 so it can
join the NightfallCraft modpack.

- `prepare.sh <unzipped 1.21.1 jar>` regenerates `src/main/resources`: `tools/convert_resources.py` turns the 1.21.1
  data and assets into the 1.20.1 layout and formats (plural data folders, recipe/advancement/predicate JSON, Forge
  model loaders, structure templates as DataVersion 3465 with 1.20 item stacks and banners), then `templates/` adds
  `META-INF/mods.toml` and the mixin config.
- `src/main/java`: the merged sources (the rework's `java/src` over the decompiled originals), after the mechanical
  pass of `tools/port_java.py` (packages, events, ResourceLocation) and `tools/tick_phase.py` (END-phase checks).
  The shape changes (data components, attribute modifiers, enchantments, networking, rendering, mixins) are done by
  hand against the real Forge 1.20.1 build.
- Build: `gradle build` (ForgeGradle 6, official mappings, JDK 17). Needs maven.minecraftforge.net, the Mojang hosts
  and repo.spongepowered.org.

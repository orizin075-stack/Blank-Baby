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

## Checking without the Forge toolchain

The Forge and Mojang hosts were out of reach while porting, so the port is checked against reconstructed stubs:

- `stub/build_stubs.sh` builds `stub/stubs1201.jar`: Minecraft classes generated from the members the 1.21.1 build
  used (`refs121_all.txt`), turned into their 1.20.1 form by `to1201.py` (renames, removed members, `extra1201.txt`
  additions each checked in Forge/Create/Iron's/Epic Fight 1.20.1 code, `overrides1201.py` for generics and abstract
  classes), plus skeletons of the real Forge 1.20.1 / eventbus / Mixin sources (`Skeleton.java`, `forge_closure.py`).
  It expects the reference checkouts in `../../ref1201` (paths at the top of the script).
- `compile_stub.sh` compiles `src/main/java` against them with JDK 17's javac (Forge 1.20.1 runs on Java 17, so Java
  21 library calls are errors too).
- `tools/audit/Overrides.java` lists the methods of every class that extends a Minecraft class (the sources are
  decompiled, so `@Override` is mostly missing and the stubs cannot catch an override whose signature changed);
  `tools/audit/idx.py` + `chk.py` list the Minecraft members the port uses that never occur in the 1.20.1 reference
  sources, for review by hand.

A clean stub compile is not a build: the stubs only know members the code uses, so the real `gradle build` against
Forge 47 is still the check that counts, and only `reobfJar` (SRG names) gives a jar Forge 1.20.1 can load.

## Packaging for NightfallCraft

`tools/package_nfc.py <extracted NightfallCraft 2.2.8.6 import> <build/libs jar> <out zip> <version>` keeps the pack's
manifest, modlist and overrides and adds the jar under `overrides/mods`.

## Next steps once the network allows the Forge and Mojang hosts

Needs maven.minecraftforge.net, piston-meta.mojang.com, piston-data.mojang.com, libraries.minecraft.net and
repo.spongepowered.org (Gradle itself, 8.14 in /opt/gradle, and the plugin portal were already reachable).

1. Resources: unzip the 0.17.18 jar from `../dist/OROR_War_Nightfall_v0.17.18_Import.zip`
   (`overrides/mods/oror_supreme_bosses-*.jar`) into an empty directory and run `./prepare.sh <that directory>`.
2. `gradle build` here (JDK 17 toolchain): compiles against the real Forge 47, runs the mixin annotation processor
   for the refmap and reobfuscates to SRG. Fix whatever the real compiler finds that the stubs could not.
3. `gradle runGameTestServer`: the game tests (`*GameTests.java`; batches needing TaCZ, Iron's, Superb Warfare or
   Epic Fight only pass with those mods in `run/mods`).
4. `python3 tools/package_nfc.py <extracted NightfallCraft 2.2.8.6 import> build/libs/oror_supreme_bosses-<v>.jar
   <out zip> <v>`: the NightfallCraft import is the user's upload, not kept in the repository.

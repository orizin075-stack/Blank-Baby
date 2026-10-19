#!/bin/bash
# Compile stubs for the Forge 1.20.1 port: Minecraft (from the 1.21.1 refs turned into 1.20.1, to1201.py) + Forge
# (skeletons of its real 1.20.1 sources, forge_closure.py) + a few hand-written classes (extra/).
set -e
cd "$(dirname "$0")"
export JAVA_TOOL_OPTIONS=
S=../..
R=$S/ref1201
python3 -I to1201.py refs121_all.txt refs1201.txt
rm -rf out && mkdir -p out
python3 -I gen1201.py refs1201.txt out/mc > /dev/null
rm -rf skel && python3 -I forge_closure.py ../src/main/java skel $R/forge/src/main/java $R/forge/fmlcore/src/main/java $R/forge/javafmllanguage/src/main/java $R/forge/fmlloader/src/main/java $R/eventbus/src/main/java $R/forgespi/src/main/java $R/mixin/src/main/java > forge_files.txt
cp -r skel out/forge && cp -r extra out/extra
# ForgeConfigSpec implements IConfigSpec through nightconfig types we do not stub: keep the relation
sed -i 's/^public class ForgeConfigSpec .*{$/public class ForgeConfigSpec implements net.minecraftforge.fml.config.IConfigSpec<ForgeConfigSpec> { public boolean isCorrecting() { return false; } public void afterReload() {}/' out/forge/net/minecraftforge/common/ForgeConfigSpec.java && mkdir -p out/brigadier && cp -r $R/brigadier/src/main/java/. out/brigadier/
# the Forge copies win over Minecraft stubs of the same name (none expected)
LIBS=$(ls lib/*.jar | grep -v asm | tr '\n' ':')
for i in $(seq 1 25); do
  rm -rf classes && mkdir -p classes
  if /usr/lib/jvm/java-17-openjdk-amd64/bin/javac -nowarn -encoding UTF-8 -proc:none -Xmaxerrs 100000 -cp "$LIBS" -d classes $(find out -name '*.java') > javac.log 2>&1; then
    (cd classes && jar cf ../stubs1201.jar .); echo "stubs ok after $i passes"; exit 0
  fi
  n=$(grep -c ': error:' javac.log || true)
  p=$(python3 -I prune.py javac.log out/forge | awk '{print $2}')
  echo "pass $i: $n errors, pruned $p"
  if [ "$p" = "0" ]; then grep -A2 ': error:' javac.log | head -60; exit 1; fi
done
exit 1

#!/bin/bash
# Compile modified sources against stubs + original jar, then verify new external refs.
cd "$(dirname "$0")"
export JAVA_TOOL_OPTIONS=
S=..
LIBS=$(ls $S/tools/lib/*.jar | grep -v asm | tr '\n' ':')
rm -rf classes && mkdir -p classes
javac -nowarn -encoding UTF-8 -proc:none -g -cp "$S/tools/stubs/stubs.jar:${LIBS}$S/mod/extracted/overrides/mods/oror_supreme_bosses-0.14.0.jar" -d classes $(find src -name "*.java") 2>&1 | grep -v "^Picked\|^Note:" 
java -cp $S/tools/lib/asm.jar:$S/tools/lib/asm-tree.jar:$S/tools/stubgen Verify $S/mod/extracted/overrides/mods/oror_supreme_bosses-0.14.0.jar classes allow.txt $S/tools/stubs/stubs.jar 2>&1 | grep -v "^Picked\|^ok-inherited"

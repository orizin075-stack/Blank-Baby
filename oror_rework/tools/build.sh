#!/bin/bash
# Rebuild stubs from refs + overrides
set -e
cd "$(dirname "$0")"
export JAVA_TOOL_OPTIONS=
python3 -I stubgen/gen.py refs.txt stubs/src > /dev/null
LIBS=$(ls lib/*.jar | grep -v asm | tr '\n' ':')
rm -rf stubs/classes stubs/stubs.jar && mkdir -p stubs/classes
if ! javac -nowarn -encoding UTF-8 -cp "$LIBS" -d stubs/classes $(find stubs/src -name "*.java") > stubs/javac.log 2>&1; then grep -A3 error stubs/javac.log; exit 1; fi
(cd stubs/classes && jar cf ../stubs.jar .)
echo "stubs ok"

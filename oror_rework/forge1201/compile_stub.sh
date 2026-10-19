#!/bin/bash
# Compile the port against the reconstructed 1.20.1 stubs (stub/build_stubs.sh). A check of the port's own consistency
# while the real Forge toolchain is out of reach; the release build is `gradle build` against Forge itself.
cd "$(dirname "$0")"
export JAVA_TOOL_OPTIONS=
LIBS=$(ls stub/lib/*.jar | grep -v asm | tr '\n' ':')
rm -rf build_stub && mkdir -p build_stub
/usr/lib/jvm/java-17-openjdk-amd64/bin/javac -nowarn -encoding UTF-8 -proc:none -Xmaxerrs 100000 -cp "stub/stubs1201.jar:$LIBS" -d build_stub $(find src/main/java -name '*.java') > build_stub.log 2>&1
echo "errors: $(grep -c ': error:' build_stub.log)"

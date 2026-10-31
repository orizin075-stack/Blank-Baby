#!/usr/bin/env bash
# Dedicated-server check of a release jar: installs NeoForge, starts a server with OROR and the mods it needs on a fixed
# seed with -Doror.ci=<checks> (CiDriver runs them and stops the server when they have logged their results), and
# checks the log for the lines they promise.
#   tools/server_test.sh <server dir> <neoforge version> <seed> <wait seconds> <log marker>... -- <checks> -- <mod jar>...
set -euo pipefail
dir=$1 nf=$2 seed=$3 wait=$4; shift 4
markers=(); while [ "$1" != "--" ]; do markers+=("$1"); shift; done; shift
checks=$1; shift; [ "$1" = "--" ] && shift
mkdir -p "$dir/mods"; cp "$@" "$dir/mods/"
cd "$dir"
if [ ! -f run.sh ]; then
  curl -sSfL -o installer.jar "https://maven.neoforged.net/releases/net/neoforged/neoforge/$nf/neoforge-$nf-installer.jar"
  java -jar installer.jar --installServer > install.log 2>&1
fi
echo 'eula=true' > eula.txt
printf 'level-seed=%s\nonline-mode=false\nspawn-protection=0\nmax-tick-time=-1\nview-distance=4\nsimulation-distance=4\nsync-chunk-writes=false\n' "$seed" > server.properties
printf -- '-Xmx6G\n-Doror.ci=%s\n-XX:StartFlightRecording=filename=rec.jfr,settings=profile,dumponexit=true\n' "$checks" > user_jvm_args.txt
rm -f console.log
./run.sh nogui < /dev/null > console.log 2>&1 &
pid=$!
for i in $(seq 1 "$wait"); do
  kill -0 $pid 2>/dev/null || break
  sleep 1
done
kill -9 $pid 2>/dev/null || true
grep -q 'Done (' console.log || { echo 'server did not start'; tail -80 console.log; exit 1; }
for m in "${markers[@]}"; do grep -q "$m" console.log || { echo "missing: $m"; exit 1; }; done

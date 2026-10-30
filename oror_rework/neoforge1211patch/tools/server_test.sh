#!/usr/bin/env bash
# Dedicated-server check of a release jar: installs NeoForge, starts a server with OROR and the mods it needs on a fixed
# seed, runs the given console commands once the server is up, waits for the log lines they promise, and stops.
#   tools/server_test.sh <server dir> <neoforge version> <seed> <wait seconds> <log marker>... -- <command>... -- <mod jar>...
set -euo pipefail
dir=$1 nf=$2 seed=$3 wait=$4; shift 4
markers=(); while [ "$1" != "--" ]; do markers+=("$1"); shift; done; shift
cmds=(); while [ "$1" != "--" ]; do cmds+=("$1"); shift; done; shift
mkdir -p "$dir/mods"; cp "$@" "$dir/mods/"
cd "$dir"
if [ ! -f run.sh ]; then
  curl -sSfL -o installer.jar "https://maven.neoforged.net/releases/net/neoforged/neoforge/$nf/neoforge-$nf-installer.jar"
  java -jar installer.jar --installServer > install.log 2>&1
fi
echo 'eula=true' > eula.txt
printf 'level-seed=%s\nonline-mode=false\nspawn-protection=0\nmax-tick-time=-1\nview-distance=4\nsimulation-distance=4\nsync-chunk-writes=false\n' "$seed" > server.properties
echo '-Xmx6G' > user_jvm_args.txt
rm -f cmd console.log; mkfifo cmd
./run.sh nogui < cmd > console.log 2>&1 &
pid=$!
exec 3>cmd
up=0
for i in $(seq 1 600); do
  if grep -q 'Done (' console.log; then up=1; break; fi
  if ! kill -0 $pid 2>/dev/null; then break; fi
  sleep 1
done
if [ $up = 1 ]; then
  for c in "${cmds[@]}"; do echo "$c" >&3; sleep 2; done
  for i in $(seq 1 "$wait"); do
    missing=0
    for m in "${markers[@]}"; do grep -q "$m" console.log || missing=1; done
    [ $missing = 0 ] && break
    kill -0 $pid 2>/dev/null || break
    sleep 1
  done
  echo stop >&3
fi
for i in $(seq 1 120); do kill -0 $pid 2>/dev/null || break; sleep 1; done
kill -9 $pid 2>/dev/null || true
exec 3>&-
[ $up = 1 ] || { echo 'server did not start'; tail -80 console.log; exit 1; }
for m in "${markers[@]}"; do grep -q "$m" console.log || { echo "missing: $m"; exit 1; }; done

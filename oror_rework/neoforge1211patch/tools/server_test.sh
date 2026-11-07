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
# the mod's own game tests are registered and /test is there only with these (051: /oror gametests runs them)
printf -- '-Xmx6G\n-Doror.ci=%s\n-Dneoforge.enableGameTest=true\n-Dneoforge.enabledGameTestNamespaces=oror_supreme_bosses,oror_compat\n-XX:StartFlightRecording=filename=rec.jfr,settings=profile,dumponexit=true\n' "$checks" > user_jvm_args.txt
rm -f console.log
./run.sh nogui < /dev/null > console.log 2>&1 &
pid=$!
# (053) the server's JVM, for thread dumps and flight recordings
jvm() { jcmd -l 2>/dev/null | grep -v -i -E 'jcmd|gradle' | awk '{print $1}' | head -n 1; }
last=0; still=0
for i in $(seq 1 "$wait"); do
  kill -0 $pid 2>/dev/null || break
  # (053) a server that has logged nothing for three minutes has hung (the second and third 053 runs: in the game
  # tests' chunks): every thread's stack, every three minutes, and after ten the server is stopped
  size=$(stat -c %s console.log 2>/dev/null || echo 0)
  if [ "$size" = "$last" ]; then still=$((still + 1)); else still=0; last=$size; fi
  if [ $still -gt 0 ] && [ $((still % 180)) -eq 0 ]; then
    j=$(jvm)
    { echo "== nothing logged for ${still}s, $(date -u +%T)"; [ -n "$j" ] && jcmd "$j" Thread.print; } >> threads_stall.txt 2>&1 || true
  fi
  if [ $still -ge 600 ]; then
    echo "== stopped: nothing logged for ${still}s" >> threads_stall.txt
    break
  fi
  # the flight recording of the hundred-man battle, taken as soon as it is over (a server killed at the end leaves none)
  if [ ! -f war.jfr ] && grep -q 'WAR-RESULT' console.log 2>/dev/null; then
    jpid=$(jvm)
    [ -n "$jpid" ] && jcmd "$jpid" JFR.dump filename="$PWD/war.jfr" > jfr_dump.txt 2>&1 || true
    touch war.jfr
  fi
  sleep 1
done
kill -9 $pid 2>/dev/null || true
grep -q 'Done (' console.log || { echo 'server did not start'; tail -80 console.log; exit 1; }
for m in "${markers[@]}"; do grep -q "$m" console.log || { echo "missing: $m"; exit 1; }; done

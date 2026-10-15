#!/bin/sh
# Start TUKUYO from the top of the distribution: the program lives in system/ (its START_TUKUYO.sh verifies the release,
# makes an individual outside the distribution the first time, and opens the conversation)
set -eu
HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec sh "$HERE/system/START_TUKUYO.sh" "$@"

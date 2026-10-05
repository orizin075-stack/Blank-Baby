#!/bin/sh
set -eu
export PYTHONDONTWRITEBYTECODE=1
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
DATA_DIR="${TUKUYO_DATA_DIR:-${HOME}/.tukuyo/v999_data}"
mkdir -p "$DATA_DIR"
cd "$ROOT"
python3 -B run_tukuyo.py verify-origins
if [ ! -f "$DATA_DIR/state/integration_state.json" ]; then
  python3 -B run_tukuyo.py --data "$DATA_DIR" init --individual-id TUKUYO-v1012-1-001
fi
python3 -B run_tukuyo.py --data "$DATA_DIR" chat

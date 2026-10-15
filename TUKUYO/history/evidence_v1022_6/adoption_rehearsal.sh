#!/bin/bash
# v1022.6 adoption rehearsal: what a publisher does to adopt this release under their own key, and what
# happens to individuals made with patch5. Uses a throwaway key; the real one must stay outside the release.
#   usage: adoption_rehearsal.sh RELEASE_DIR PATCH5_SYSTEM_DIR PATCH5_ANCHOR WORK_DIR [PYTHON]
#   RELEASE_DIR holds system/ and deliverables/ of v1022.6; it is copied, never changed.
set -u
REL=$1;P5=$2;A5=$3;W=$4;PY="${5:-python3} -B"
rm -rf "$W";mkdir -p "$W";cp -a "$REL/system" "$W/system"
export PYTHONDONTWRITEBYTECODE=1;unset TUKUYO_LLM_PROVIDER TUKUYO_LLM_COMMAND TUKUYO_LLM_TEACHERS
show(){ python3 -c "import json,sys;r=json.loads(sys.stdin.read() or '{}');print('$1:',{k:r.get(k) for k in sys.argv[1:]})" "${@:2}"; }
echo "== 1 publisher key (keep the private half outside the release)"
$PY "$W/system/tools/claude_patch_sign.py" keygen --out-dir "$W/publisher_key" | show keygen ok public_key
echo "== 2 sign the release as v1022.6, write the anchor, verify"
$PY "$W/system/tools/claude_patch_sign.py" sign "$W/system" --private-key "$W/publisher_key/patch_signing.key" --revision v1022.6 | show sign ok files release_revision
cp "$W/publisher_key/patch_signing.pub" "$W/TRUST_ANCHOR.txt"
$PY "$W/system/tools/verify_release.py" "$W/system" --trusted-pubkey-file "$W/TRUST_ANCHOR.txt" | show verify ok verified_files
$PY "$W/system/tools/verify_release.py" "$W/system" --trusted-pubkey-file "$REL/deliverables/TUKUYO_v1022_6_TRUST_ANCHOR.txt" | show verify_with_the_old_anchor ok bad
NEW="$PY $W/system/run_tukuyo.py --runtime-trust-file $W/TRUST_ANCHOR.txt";OLD="$PY $P5/run_tukuyo.py --runtime-trust-file $A5"
echo "== 3 a new individual"
$NEW --data "$W/new" init | show init ok release_revision
$NEW --data "$W/new" think -- 'りんごが12個あります。妹に5個あげました。あげたのは何個？' | show think answer
$NEW --data "$W/new" learning-audit | show learning-audit ok
$NEW --data "$W/new" whole-audit | show whole-audit ok
echo "== 4 an individual made with patch5 (with a research expedition): used as is"
$OLD --data "$W/p5plain" init --individual-id P5PLAIN | show patch5-init ok
$OLD --data "$W/p5plain" research-run --world W1 --tier 2 --noise 0.0 --ticks 120 | show patch5-research ok status
$NEW --data "$W/p5plain" whole-audit | show whole-audit ok
$NEW --data "$W/p5plain" research-audit | show research-audit ok replayed_from_world_key
$NEW --data "$W/p5plain" think -- 'みかんが20個あります。8個食べました。はじめにあったのは何個？' | show think answer
echo "== 5 an individual made with patch5 that runs a metabolism: needs one explicit rebind"
$OLD --data "$W/p5eco" init --individual-id P5ECO | show patch5-init ok
$OLD --data "$W/p5eco" metabolism-init --families 2 --reservoir 80000 --max-age 6 --research-world | show patch5-metabolism-init ok
$OLD --data "$W/p5eco" metabolism-step --ticks 4 | show patch5-step ok tick
$NEW --data "$W/p5eco" metabolism-step --ticks 2 | show step-before-rebind ok error
$NEW --data "$W/p5eco" runtime-trust-rebind --previous-trust-file "$A5" | show rebind ok updated_forests
$NEW --data "$W/p5eco" metabolism-step --ticks 4 | show step-after-rebind ok tick
$NEW --data "$W/p5eco" metabolism-audit | show metabolism-audit ok
$NEW --data "$W/p5eco" whole-audit | show whole-audit ok

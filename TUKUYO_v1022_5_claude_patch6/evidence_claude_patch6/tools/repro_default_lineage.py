"""Default metabolism (no --research-world), 4 families, 24 ticks; same rows as evidence lineage_patch5.json.
usage: repro_default_lineage.py ROOT ANCHOR WORKDIR OUT.json"""
import json, os, subprocess, sys
from pathlib import Path

root, anchor, work, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3]), Path(sys.argv[4])
d = work / 'd'
env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
for k in ('TUKUYO_LLM_PROVIDER', 'TUKUYO_LLM_COMMAND', 'TUKUYO_LLM_TEACHERS', 'TUKUYO_CRASH_POINT'):
    env.pop(k, None)


def cli(*a):
    p = subprocess.run([sys.executable, '-B', str(root / 'run_tukuyo.py'), '--runtime-trust-file', anchor, '--data', str(d), *map(str, a)],
                       cwd=root, env=env, capture_output=True, text=True, timeout=1800)
    r = json.loads(p.stdout)
    if not r.get('ok'):
        raise SystemExit(f'{a[0]} failed: {r} {p.stderr[-400:]}')
    return r


cli('init')
cli('metabolism-init', '--families', 4, '--reservoir', 160000, '--regeneration', int(sys.argv[5]) if len(sys.argv)>5 else 1600, '--max-age', 8)
rows = []
for _ in range(6):
    r = cli('metabolism-step', '--ticks', 4)
    rows.append({k: r[k] for k in ('tick', 'attempts', 'correct', 'wrong', 'abstained', 'actual_successions', 'active_runtime_count', 'reservoir')})
res = {'rows': rows, 'metabolism_audit': cli('metabolism-audit')['ok'], 'whole_audit': cli('whole-audit')['ok']}
out.write_text(json.dumps(res, ensure_ascii=False, indent=1))
print(json.dumps(res, ensure_ascii=False))

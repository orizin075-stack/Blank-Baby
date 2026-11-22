#!/usr/bin/env python3
"""(r65) Every OROR check's verdict in one table: the CI job only waits for the result lines to be logged, so a check that
logged "pass":false went unseen (GUN-PARRY, MOBS-TRACE and the king's story since 11/11). Reads a server console log and
writes, for each result line (TAG {json}), its pass/ok, the fields that are false and any failed list.

    python3 -I tools/pass_summary.py console.log out/pass_summary.txt
"""
import json
import re
import sys

LINE = re.compile(r'\b([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-(?:RESULT|TRACE|PARRY|STORY|LOAD|FLIGHT|SELFTEST|UPDATE|SHIELD|TEST|MOBS)) (\{.*\})\s*$')


def main(src, dst):
    seen = {}
    with open(src, encoding='utf-8', errors='replace') as f:
        for raw in f:
            m = LINE.search(raw)
            if not m:
                continue
            try:
                d = json.loads(m.group(2))
            except ValueError:
                continue
            if isinstance(d, dict):
                seen[m.group(1)] = d
    rows, bad = [], 0
    for tag in sorted(seen):
        d = seen[tag]
        verdict = d.get('pass', d.get('ok', '-'))
        falses = [k for k, v in d.items() if v is False and k not in ('pass', 'ok')]
        failed = d.get('failed') or d.get('failedTests') or ''
        if verdict is False or (isinstance(failed, (int, list)) and failed):
            bad += 1
        mark = 'FAIL' if verdict is False else ('ok' if verdict is True else '-')
        rows.append(f'{mark:4} {tag:28} false={",".join(falses)[:160]} {("failed=" + json.dumps(failed, ensure_ascii=False)[:300]) if failed else ""}')
    with open(dst, 'w', encoding='utf-8') as out:
        out.write(f'{len(seen)} result lines, {bad} with a failure\n')
        out.write('\n'.join(rows) + '\n')
    print(f'{len(seen)} results, {bad} with a failure')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

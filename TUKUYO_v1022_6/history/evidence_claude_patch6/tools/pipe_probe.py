"""full-pipeline probe (in-process cognition.solve) on a tsv of question<TAB>expected"""
import sys,json
SRC='/home/user/Blank-Baby/TUKUYO_v1022_5_claude_patch6/system/src'
sys.path.insert(0,SRC)
from tukuyo_v1022 import cognition
data=sys.argv[2] if len(sys.argv)>2 else '/tmp/claude-0/-home-user-Blank-Baby/dd3c6b53-ae17-5414-bda7-717330a62fb9/scratchpad/probe_p5'
ok=bad=0
for line in open(sys.argv[1],encoding='utf-8'):
    if not line.strip():continue
    q,exp=line.rstrip('\n').split('\t')
    r=cognition.solve(data,q)
    ans=None if r.get('uncertain') else r.get('answer')
    ve=(r.get('verification_evidence') or {}).get('semantic_gate') or {}
    tag=f"{ans} [{(r.get('proof') or {}).get('kind')}/{r.get('question_role') or ''}/{ve.get('independent_parser') or ''}] {r.get('reason') or ''}"
    if '_OR_' in exp and exp!='PASS_OR_ABSTAIN':
        alts=exp.split('_OR_');good=any((x in ('ABSTAIN','PASS') and ans is None) or x==ans for x in alts)
    elif exp in ('ABSTAIN','PASS_OR_ABSTAIN'):good=ans is None
    elif exp=='PASS':good=True
    else:good=ans==exp
    ok+=good;bad+=not good
    print(('  ok ' if good else 'FAIL ')+f'{tag:70s} exp={exp:6s} {q}')
print('ok',ok,'bad',bad)

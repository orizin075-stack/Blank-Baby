"""Regression oracle: patch5's recorded `think` answers on dev/A/B/C/D/E vs the working tree, in-process.
usage: oracle.py [--setup]   (setup creates the individual with dev + C knowledge using the signed patch5 CLI)"""
import json,os,subprocess,sys
from pathlib import Path
SP=Path('/tmp/claude-0/-home-user-Blank-Baby/dd3c6b53-ae17-5414-bda7-717330a62fb9/scratchpad')
PKG=Path('/home/user/Blank-Baby/TUKUYO_v1022_5_claude_patch6')
EV5=PKG/'evidence_claude_patch5'
DATA=SP/'oracle_data'
P5=SP/'run4/system';ANCHOR=SP/'run4/deliverables/TUKUYO_v1022_5_patch5_TRUST_ANCHOR.txt'
dev=json.loads((P5/'tools/llm_eval_sets.json').read_text())
sets={s:json.loads((EV5/f'heldout_{s}.json').read_text()) for s in 'CDE'}
if '--setup' in sys.argv:
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for k in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS'):env.pop(k,None)
    def cli(*a):return subprocess.run([sys.executable,'-B',str(P5/'run_tukuyo.py'),'--runtime-trust-file',str(ANCHOR),'--data',str(DATA),*a],cwd=P5,env=env,capture_output=True,text=True)
    cli('init','--individual-id','ORACLE')
    for f in dev['knowledge']+sets['C']['knowledge']:cli('knowledge-add',f)
    print('setup done');sys.exit()
sys.path.insert(0,str(PKG/'system/src'))
sys.path.insert(0,str(PKG/'system/tools'))
from tukuyo_v1022 import cognition
from llm_eval import grade
expected={}
for r in dev['rows']:expected[('dev',r['q'])]=r
for s,d in sets.items():
    for r in d['rows']:expected[('heldout'+s,r['q'])]=r
old={}
for r in json.loads((EV5/'dev_A_B_patch2_to_patch5.json').read_text())['patch5']:
    if r['cmd']=='think' and r['split']!='_audit':old[(r['split'],r['q'])]=r
for f in ('heldoutC_patch2_to_patch5.json','heldoutD_fusion_patch3_patch4_patch5.json','heldoutE_fusion_patch3_patch4_patch5.json'):
    for r in json.loads((EV5/f).read_text())['patch5']:
        if r['cmd']=='think' and r['split']!='_audit':old[(r['split'],r['q'])]=r
stats={'same':0,'changed':0,'new_answer':0,'new_abstain':0,'skipped':0}
rows=[]
for (split,q),o in old.items():
    if split in ('heldoutA','heldoutB') and 'memory' in o['set']:stats['skipped']+=1;continue
    r=cognition.solve(str(DATA),q)
    a=None if r.get('uncertain') else r.get('answer')
    oa=o['answer'] if not o.get('abstained') else None
    if 'think' and o['cmd']=='think' and oa is not None and o.get('abstained'):oa=None
    e=expected.get((split,q))
    g=grade(e,{**r,'answer':a,'uncertain':a is None}) if e else None
    if str(a)==str(oa) if a is not None and oa is not None else (a is None and oa is None):stats['same']+=1;continue
    kind='changed' if a is not None and oa is not None else ('new_answer' if a is not None else 'new_abstain')
    stats[kind]+=1
    rows.append({'split':split,'set':o['set'],'q':q,'patch5':oa,'patch6':a,'reason':r.get('reason'),'kind':kind,
                 'correct':None if g is None else g['correct'],'wrong_certain':None if g is None else g['wrong_certain'],'expected':e['expected'] if e else None})
for x in rows:print(json.dumps(x,ensure_ascii=False))
print(stats)
wc=[x for x in rows if x['wrong_certain']]
print('NEW WRONG-CERTAIN:',len(wc))

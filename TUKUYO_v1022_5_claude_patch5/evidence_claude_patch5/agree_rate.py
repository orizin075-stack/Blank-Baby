"""How many committed numeric answers carry an independent Parser-B agreement (patch4 vs patch5)."""
import json,os,subprocess,sys,tempfile,collections
from pathlib import Path
SB=Path('/tmp/claude-0/-home-claude/ef7c06e2-82d3-5fb4-b676-2ade448eea2f/scratchpad')
sys.path.insert(0,str(SB/'p23/m/system/tools'));from llm_eval import grade
V={'patch4':SB/'f25/meas4/system','patch5':SB/'f25/meas5/system'};A=SB/'f25/keys/ANCHOR_PATCH3.txt'
sets={'E':json.load(open(SB/'f25/heldout_E.json'))['rows'],'D':json.load(open(SB/'f25/heldout_D.json'))['rows'],'C':json.load(open(SB/'f25/heldout_C.json'))['rows']}
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
for k in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS'):env.pop(k,None)
out={}
for name,root in V.items():
    d=Path(tempfile.mkdtemp())/'d';subprocess.run([sys.executable,'-B',str(root/'run_tukuyo.py'),'--runtime-trust-file',str(A),'--data',str(d),'init'],cwd=root,env=env,capture_output=True)
    rows=[]
    for split,rs in sets.items():
        for r in rs:
            p=subprocess.run([sys.executable,'-B',str(root/'run_tukuyo.py'),'--runtime-trust-file',str(A),'--data',str(d),'think','--',r['q']],cwd=root,env=env,capture_output=True,text=True)
            try:x=json.loads(p.stdout)
            except Exception:x={}
            ve=(x.get('verification_evidence') or {}).get('semantic_gate') or {};sg=x.get('semantic_gate') or {}
            g=grade(r,{**x,'answer':None if x.get('uncertain') else x.get('answer'),'uncertain':x.get('uncertain',True)})
            rows.append({'split':split,'set':r['set'],'q':r['q'],'answer':x.get('answer'),'uncertain':x.get('uncertain'),'correct':g['correct'],'wrong_certain':g['wrong_certain'],
                         'gate_applied':bool(ve.get('applied')),'independent':ve.get('independent_parser'),'blocked':sg.get('reason')})
    out[name]=rows
(SB/'f25/cmp/agree_rate.json').write_text(json.dumps(out,ensure_ascii=False,indent=1))
for name,rows in out.items():
    for split in sets:
        rs=[r for r in rows if r['split']==split];com=[r for r in rs if r['gate_applied']]
        print(name,split,'n',len(rs),'correct',sum(r['correct'] for r in rs),'wrong_certain',sum(r['wrong_certain'] for r in rs),
              'gated_commits',len(com),'AGREE',sum(r['independent']=='AGREE' for r in com),'blocked_by_parserB',sum(r['blocked']=='INDEPENDENT_PARSER_DISAGREES' for r in rs))

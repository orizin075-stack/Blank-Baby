"""claude-patch6 final evaluation, LLM off, signed trees through the CLI.
Held-out F and T are run ONCE, on patch5 and on patch6. C/D/E (patch5's held-out sets, used by patch6 only
as a regression oracle) are run on patch6 for the record. One fresh individual per version x command x set.
usage: final_eval.py OUT.json"""
import json,os,subprocess,sys,tempfile,collections,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
SP=Path('/tmp/claude-0/-home-user-Blank-Baby/dd3c6b53-ae17-5414-bda7-717330a62fb9/scratchpad')
PKG=Path('/home/user/Blank-Baby/TUKUYO_v1022_5_claude_patch6')
sys.path.insert(0,str(PKG/'system/tools'));from llm_eval import grade
V={'patch5':(SP/'run4/system',SP/'run4/deliverables/TUKUYO_v1022_5_patch5_TRUST_ANCHOR.txt'),
   'patch6':(SP/'run6c/system',SP/'run6c/deliverables/TUKUYO_v1022_5_patch6_TRUST_ANCHOR.txt')}
SETS={s:json.loads((PKG/'evidence_claude_patch6'/f'heldout_{s}.json').read_text()) for s in 'FT'}
SETS.update({s:json.loads((PKG/'evidence_claude_patch5'/f'heldout_{s}.json').read_text()) for s in 'CDE'})
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
for k in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS'):env.pop(k,None)
def cli(root,trust,d,*a):
    p=subprocess.run([sys.executable,'-B',str(root/'run_tukuyo.py'),'--runtime-trust-file',str(trust),'--data',str(d),*a],cwd=root,env=env,capture_output=True,text=True,timeout=300)
    try:return json.loads(p.stdout)
    except Exception:return {'ok':False,'answer':None,'uncertain':True,'status':'error','_err':(p.stdout+p.stderr)[-300:]}
def job(spec):
    name,cmd,split=spec;root,trust=V[name];d=Path(tempfile.mkdtemp(prefix=f'ev6_{name}_{cmd}_{split}_'))/'d'
    cli(root,trust,d,'init','--individual-id',f'EVAL6-{name}-{cmd}-{split}'.upper())
    kn=SETS[split]['knowledge']
    for f in (kn if isinstance(kn,list) else []):cli(root,trust,d,'knowledge-add',f)
    res=[]
    for r in SETS[split]['rows']:
        x=cli(root,trust,d,cmd,'--',r['q'])
        if cmd in ('think','verified-query') and x.get('uncertain'):x={**x,'answer':None}
        if cmd=='think':x={**x,'uncertain':x.get('answer') is None}
        ve=(x.get('verification_evidence') or {}).get('semantic_gate') or {}
        g=grade(r,x)
        res.append({'version':name,'cmd':cmd,'split':split,'set':r['set'],'q':r['q'],'expected':r['expected'],'answer':x.get('answer'),
                    'status':x.get('status'),'source':x.get('source'),'gate_applied':bool(ve.get('applied')),'independent':ve.get('independent_parser'),
                    'err':x.get('_err') or x.get('error'),**g})
    res.append({'version':name,'cmd':cmd,'split':split,'audit_row':True,'whole_audit':cli(root,trust,d,'whole-audit').get('ok')})
    return res
specs=[(v,c,s) for v in ('patch5','patch6') for s in ('F','T') for c in ('think','verified-query','llm-ask')]+\
      [('patch6',c,s) for s in ('C','D','E') for c in ('think','verified-query','llm-ask')]
t=time.time()
with ThreadPoolExecutor(3) as ex:rows=[r for rs in ex.map(job,specs) for r in rs]
summary=collections.OrderedDict()
for v,c,s in specs:
    rs=[r for r in rows if (r['version'],r['cmd'],r['split'])==(v,c,s) and not r.get('audit_row')]
    au=[r['whole_audit'] for r in rows if (r['version'],r['cmd'],r['split'])==(v,c,s) and r.get('audit_row')]
    summary[f'{s}|{v}|{c}']={'n':len(rs),'correct':sum(r['correct'] for r in rs),'wrong_certain':sum(r['wrong_certain'] for r in rs),
        'abstained':sum(r['abstained'] for r in rs),'gated_commits':sum(r['gate_applied'] for r in rs),'parser_b_agree':sum(r['independent']=='AGREE' for r in rs),
        'errors':sum(bool(r['err']) for r in rs),'whole_audit_after':au[0] if au else None}
out={'schema':'tukuyo.claude_patch6.final_eval/1','llm':'off','seconds':round(time.time()-t,1),'summary':summary,'rows':rows}
Path(sys.argv[1]).write_text(json.dumps(out,ensure_ascii=False,indent=1))
for k,v in summary.items():print(k,v)

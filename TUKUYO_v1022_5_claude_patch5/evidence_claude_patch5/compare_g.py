"""patch2 (as delivered) vs v1022.5 fusion vs (later) patch3, LLM off, same machine."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
SB=Path('/tmp/claude-0/-home-claude/ef7c06e2-82d3-5fb4-b676-2ade448eea2f/scratchpad')
sys.path.insert(0,str(SB/'p23/m/system/tools'));from llm_eval import grade
V={'patch5':(SB/'f25/meas5/system',SB/'f25/keys/ANCHOR_PATCH3.txt'),'patch4':(SB/'f25/meas4/system',SB/'f25/keys/ANCHOR_PATCH3.txt'),'patch2':(SB/'p23/verify_pkg2/TUKUYO_v1022_claude_patch2/system',SB/'p23/keys/patch_signing.pub'),
   'fusion':(SB/'f25/x/system',SB/'f25/ANCHOR_FROM_RECEIPT.txt'),
   'patch3':(SB/'f25/m/system',SB/'f25/keys/ANCHOR_PATCH3.txt')}
dev=json.loads((SB/'p23/m/system/tools/llm_eval_sets.json').read_text());hoA=json.loads((SB/'p23/cmp2/heldout_patch2.json').read_text());hoB=json.loads((SB/'f25/heldout_B.json').read_text())
hoC=json.loads((SB/'f25/heldout_C.json').read_text())
HO=os.environ.get('HO');hoX=json.loads(Path(HO).read_text()) if HO else None
rows=[{**r,'split':os.environ.get('HO_NAME','heldoutX')} for r in hoX['rows']] if HO else [{**r,'split':'heldoutC'} for r in hoC['rows']] if os.environ.get('ONLY_C') else [{**r,'split':'dev'} for r in dev['rows']]
for cl in [] if (os.environ.get('ONLY_C') or HO) else ['3〜5個食べました','3個食べたかどうか不明','3個食べないとは言えない','3個食べたと報告されました','3個借りて返しました','5個ぐらい食べました','3個か4個食べました','3個食べたらしい']:
    rows.append({'split':'dev','set':'ambiguous_inventory','q':'1箱に8個入りが4箱あります。'+cl+'。残りは何個？','kind':'abstain','expected':None})
if not (os.environ.get('ONLY_C') or HO):rows+=[{**r,'split':'heldoutA'} for r in hoA['rows']]+[{**r,'split':'heldoutB'} for r in hoB['rows']]
facts=dev['knowledge']+hoA['knowledge']+hoB['knowledge']+hoC['knowledge']
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
for k in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS'):env.pop(k,None)
def cli(root,trust,d,*a):
    p=subprocess.run([sys.executable,'-B',str(root/'run_tukuyo.py'),'--runtime-trust-file',str(trust),'--data',str(d),*a],cwd=root,env=env,capture_output=True,text=True,timeout=300)
    try:return json.loads(p.stdout)
    except Exception:return {'ok':False,'answer':None,'uncertain':True,'status':'error','_err':(p.stdout+p.stderr)[-300:]}
def run_version(name):
    root,trust=V[name];res=[]
    for cmd in ('think','verified-query','llm-ask'):
        d=Path(tempfile.mkdtemp())/'d';cli(root,trust,d,'init','--individual-id',f'CMPF-{name}-{cmd}'.upper())
        for f in facts:cli(root,trust,d,'knowledge-add',f)
        for r in rows:
            x=cli(root,trust,d,cmd,'--',r['q'])
            if cmd in ('think','verified-query') and x.get('uncertain'):x={**x,'answer':None}
            if cmd=='think':x={**x,'uncertain':x.get('answer') is None}
            g=grade(r,x);res.append({'split':r['split'],'set':r['set'],'q':r['q'],'cmd':cmd,'answer':x.get('answer'),'status':x.get('status'),'err':x.get('_err') or x.get('error'),**g})
        res.append({'split':'_audit','cmd':cmd,'whole_audit':cli(root,trust,d,'whole-audit').get('ok'),'set':'','q':'','correct':False,'abstained':False,'wrong_certain':False})
    return name,res
only=sys.argv[2:] or ['patch2','fusion']
outp=SB/'f25/cmp'/sys.argv[1]
prev=json.loads(outp.read_text()) if outp.exists() else {}
with ThreadPoolExecutor(2) as ex:out={**prev,**dict(ex.map(run_version,only))}
outp.write_text(json.dumps(out,ensure_ascii=False,indent=1))
for split in ('dev','heldoutA','heldoutB','heldoutC','heldoutD','heldoutE'):
    print('=====',split)
    for name in out:
        for cmd in ('think','verified-query','llm-ask'):
            rs=[r for r in out[name] if r['cmd']==cmd and r['split']==split]
            if rs:print(f'  {name:7s} {cmd:15s} n={len(rs):3d} correct={sum(r["correct"] for r in rs):3d} wrong_certain={sum(r["wrong_certain"] for r in rs):3d} abstained={sum(r["abstained"] for r in rs):3d}')
for name in out:print(name,'whole-audit after run:',[r['whole_audit'] for r in out[name] if r['split']=='_audit'])

#!/usr/bin/env python3
"""Third-party word-problem benchmark for TUKUYO generation 4: problems written by other people.

  g4_bench.py fetch DATA_DIR                      download the sets below and check their pinned sha256
  g4_bench.py sizes DATA_DIR                      items per set and split
  g4_bench.py run DATA_DIR --system v1022|g4 --split dev [--set mgsm_ja|asdiv|svamp] [--out OUT.json] [--show N]
  g4_bench.py run DATA_DIR --system ... --split test --locked-test-run REASON --log LOG.jsonl

The problem files are not shipped with TUKUYO (licences below); fetch downloads them and refuses a file whose
sha256 differs from the pinned one. Splits are fixed by a hash of the item id, so they never move:
  * mgsm_ja (250, Japanese, human translation of GSM8K problems): half dev, half test
  * asdiv (2305, English, grades 1-6): half dev, half test; items whose answer is not one number are left out
  * svamp (1000, English, variations of simple problems): test only
Development may look at dev items one by one. The test split is locked: a test run needs --locked-test-run and
--log, prints and logs counts only (no item text, no per-item results), and every test run is appended to the
log, so how often the test split was used stays on record.
"""
from __future__ import annotations
import argparse,collections,hashlib,json,re,sys,time,urllib.request
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

SETS={
 'mgsm_ja':{'file':'mgsm/mgsm_ja.tsv','url':'https://raw.githubusercontent.com/google-research/url-nlp/main/mgsm/mgsm_ja.tsv',
            'sha256':'59a2b50debe77981fd784cb3b2bef1505e3abf2a37116dc9d7a366ab029b4637','lang':'ja',
            'licence':'MGSM (Shi et al. 2022), human translations of GSM8K test problems (GSM8K: MIT)'},
 'svamp':{'file':'svamp/SVAMP.json','url':'https://raw.githubusercontent.com/arkilpatel/SVAMP/main/SVAMP.json',
          'sha256':'5be77703a6d891ae476d7c082787ad361392aa02453b132516cdd5f4e7934e3e','lang':'en','licence':'SVAMP (Patel et al. 2021), MIT'},
 'asdiv':{'file':'asdiv/ASDiv.xml','url':'https://raw.githubusercontent.com/chaochun/nlu-asdiv-dataset/master/dataset/ASDiv.xml',
          'sha256':'ef8904068482919ac48c8eeaaf6df344b8a308ba66d048c2d4d87eab82dc4929','lang':'en','licence':'ASDiv (Miao et al. 2020), CC BY-NC 4.0'},
}
SPLIT_SALT='tukuyo-g4-split-1'
OPTS={'llm':'off','learn':False}
NUM=re.compile(r'-?\d+(?:,\d{3})*(?:\.\d+)?(?:/\d+)?')

def split_of(name,item_id):
    if name=='svamp':return 'test'
    return 'test' if hashlib.sha256(f'{SPLIT_SALT}:{name}:{item_id}'.encode()).digest()[0]&1 else 'dev'

def to_fraction(s):
    m=NUM.search(str(s).replace('，',',').replace('．','.'))
    if not m:return None
    t=m.group().replace(',','')
    try:return Fraction(t)
    except (ValueError,ZeroDivisionError):return None

def sha256_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def fetch(data):
    out={}
    for name,s in SETS.items():
        p=Path(data)/s['file'];p.parent.mkdir(parents=True,exist_ok=True)
        if not p.is_file():
            with urllib.request.urlopen(s['url'],timeout=60) as r:p.write_bytes(r.read())
        h=sha256_file(p);out[name]={'ok':h==s['sha256'],'sha256':h}
        if h!=s['sha256']:p.rename(p.with_suffix(p.suffix+'.rejected'))
    return out

def load(data,name):
    s=SETS[name];p=Path(data)/s['file']
    if sha256_file(p)!=s['sha256']:raise SystemExit(f'{name}: sha256 differs from the pinned one; run fetch again')
    items=[]
    if name=='mgsm_ja':
        for i,line in enumerate(p.read_text(encoding='utf-8').splitlines(),1):
            q,a=line.split('\t');items.append({'id':f'mgsm-ja-{i:03d}','text':q.strip(),'gold':to_fraction(a)})
    elif name=='svamp':
        for x in json.loads(p.read_text(encoding='utf-8')):
            body=x['Body'].strip()
            if body and body[-1] not in '.?!':body+='.'
            items.append({'id':x['ID'],'text':body+' '+x['Question'].strip(),'gold':Fraction(str(x['Answer'])),'type':x['Type']})
    else:
        for pr in ET.parse(p).getroot().iter('Problem'):
            ans=(pr.findtext('Answer') or '').strip()
            one=re.fullmatch(r'\s*-?\d+(?:\.\d+)?(?:/\d+)?\s*(?:\([^()]*\))?\s*',ans)
            items.append({'id':pr.get('ID'),'text':((pr.findtext('Body') or '').strip()+' '+(pr.findtext('Question') or '').strip()).strip(),
                          'gold':to_fraction(ans) if one else None,'type':(pr.findtext('Solution-Type') or '').strip(),'grade':pr.get('Grade')})
    for it in items:it['set']=name;it['lang']=s['lang'];it['split']=split_of(name,it['id'])
    return [it for it in items if it['gold'] is not None]

def solver(system,work):
    """returns ask(text)->{'answer':str|None,...}; the individual's data stays under work"""
    here=Path(__file__).resolve().parents[1];sys.path.insert(0,str(here/'src'))
    if system=='v1022':
        from tukuyo_v1022 import cognition
        d=Path(work)/'v1022_individual';d.mkdir(parents=True,exist_ok=True)
        def ask(text):
            r=cognition.solve(str(d),text)
            return {'answer':None if r.get('uncertain') or r.get('answer') is None else str(r['answer']),'why':r.get('reason')}
        return ask
    if system=='g4':
        from tukuyo_g4 import api
        d=Path(work)/'v1022_individual';data=d if d.is_dir() else None
        if data is None and OPTS['learn']:raise SystemExit(f'--learn keeps templates in the individual: create it first (run_tukuyo.py --data {d} init)')
        def ask(text):
            r=api.solve(text,llm=OPTS['llm'],data=data,learn=OPTS['learn'])
            return {'answer':r.get('answer'),'why':r.get('reason'),'route':r.get('route')}
        return ask
    raise SystemExit('unknown system '+system)

def grade(item,res):
    if res.get('answer') is None:return 'abstain'
    v=to_fraction(res['answer'])
    if v is None:return 'wrong'
    g=item['gold']
    return 'correct' if v==g or abs(float(v)-float(g))<=1e-6*max(1.0,abs(float(g))) else 'wrong'

def run(a):
    names=[a.set] if a.set else list(SETS)
    items=[it for n in names for it in load(a.data,n) if it['split']==a.split]
    if a.split=='test' and not (a.locked_test_run and a.log):raise SystemExit('the test split is locked: pass --locked-test-run REASON and --log LOG.jsonl')
    OPTS.update(llm=a.llm,learn=a.learn)
    work=Path(a.work or Path(a.data)/'_work');ask=solver(a.system,work)
    rows=[];t0=time.time()
    for it in items:
        try:res=ask(it['text'])
        except Exception as e:res={'answer':None,'why':'ERROR:'+repr(e)[:160]}
        rows.append({'id':it['id'],'set':it['set'],'status':grade(it,res),'answer':res.get('answer'),'gold':str(it['gold']),'why':res.get('why'),'route':res.get('route')})
    agg={}
    for n in names:
        c=collections.Counter(r['status'] for r in rows if r['set']==n)
        agg[n]={'items':sum(c.values()),'correct':c['correct'],'wrong':c['wrong'],'abstain':c['abstain']}
    routes=collections.Counter(r['route'] for r in rows if r['route'])
    summary={'system':a.system,'llm':a.llm,'learn':a.learn,'split':a.split,'sets':agg,'routes':dict(routes),'seconds':round(time.time()-t0,1),
             'results_sha256':hashlib.sha256(json.dumps([[r['id'],r['status'],r['answer']] for r in rows],ensure_ascii=False).encode()).hexdigest()}
    if a.split=='test':
        rec={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'reason':a.locked_test_run,**summary}
        with open(a.log,'a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False)+'\n')
        print(json.dumps(rec,ensure_ascii=False,indent=1));return
    if a.out:Path(a.out).write_text(json.dumps({'summary':summary,'rows':rows},ensure_ascii=False,indent=1),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=1))
    if a.show:
        text={it['id']:it['text'] for it in items}
        for st in ('wrong','abstain','correct'):
            for r in [r for r in rows if r['status']==st][:a.show]:
                print(f"[{st}] {r['id']} gold={r['gold']} answer={r['answer']} why={r['why']} route={r.get('route')}\n    {text[r['id']]}")

def main():
    ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
    f=sub.add_parser('fetch');f.add_argument('data')
    z=sub.add_parser('sizes');z.add_argument('data')
    r=sub.add_parser('run');r.add_argument('data');r.add_argument('--system',required=True);r.add_argument('--split',required=True,choices=['dev','test'])
    r.add_argument('--set',choices=list(SETS));r.add_argument('--out');r.add_argument('--show',type=int,default=0);r.add_argument('--work')
    r.add_argument('--locked-test-run');r.add_argument('--log')
    r.add_argument('--llm',choices=('off','auto','on'),default='off',help='g4: use Claude (needs TUKUYO_ANTHROPIC_API_KEY or TUKUYO_LLM_REPLAY)')
    r.add_argument('--learn',action='store_true',help='g4: keep readings that agreed with Claude as templates in the individual')
    a=ap.parse_args()
    if a.cmd=='fetch':print(json.dumps(fetch(a.data),indent=1))
    elif a.cmd=='sizes':
        out={}
        for n in SETS:
            c=collections.Counter(it['split'] for it in load(a.data,n));out[n]=dict(c)
        print(json.dumps(out,indent=1))
    else:run(a)

if __name__=='__main__':main()

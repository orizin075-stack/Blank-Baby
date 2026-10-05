#!/usr/bin/env python3
"""Measure what an LLM actually adds to TUKUYO (claude-patch1).

Runs the same items twice on fresh individuals:
  local  - the built-in core only (llm-ask with no provider)
  llm    - llm-ask with the provider configured in the environment
and reports, per set: correct, wrong-but-presented-as-certain, abstained, and the
verification status mix. A "certain" answer is one that is not marked uncertain.

  python3 -B tools/llm_eval.py --trust-file PATCH_PUB --out result.json [--limit N]
Provider env (see src/tukuyo_v1022_llm/providers.py), e.g.
  TUKUYO_LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=... TUKUYO_LLM_MODEL=<model id>
"""
import argparse,json,os,re,subprocess,sys,tempfile,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def cli(d,trust,env,*a):
    p=subprocess.run([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--runtime-trust-file',trust,'--data',str(d),*map(str,a)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=600)
    try:return json.loads(p.stdout)
    except Exception:return {'ok':False,'error':(p.stdout+p.stderr)[-300:]}

def grade(row,r):
    a=str(r.get('answer') or '');certain=not r.get('uncertain',True);abst=r.get('status') in ('abstained','rejected','error') or r.get('answer') is None
    k=row['kind'];e=row['expected']
    if k=='abstain':ok=abst or not certain
    elif abst:ok=None
    elif k=='number':ok=e in re.findall(r'-?\d+(?:\.\d+)?',a.replace(',',''))
    elif k=='contains':ok=e.lower() in a.lower()
    else:
        t=e[0]
        if t=='unknown':ok=bool(re.search(r'わから|分から|言えない|不明|確定でき|判断でき|決められ|cannot|can\'t|not enough',a,re.I)) or not certain
        elif t=='no':ok=bool(re.search(r'いいえ|降っていない|降らなかった|ない|\bno\b',a,re.I))
        else:ok=e[1].lower() in a.lower()
    return {'correct':ok is True,'abstained':ok is None,'wrong_certain':ok is False and certain,'status':r.get('status')}

def run_mode(mode,sets,trust,limit):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    if mode=='local':env.pop('TUKUYO_LLM_PROVIDER',None);env.pop('TUKUYO_LLM_COMMAND',None)
    td=Path(tempfile.mkdtemp(prefix='tukuyo_llmeval_'));d=td/'d';cli(d,trust,env,'init','--individual-id','LLM-EVAL-'+mode.upper())
    for f in sets['knowledge']:cli(d,trust,env,'knowledge-add',f)
    out=[]
    for row in sets['rows'][:limit]:
        r=cli(d,trust,env,'llm-ask','--',row['q']);g=grade(row,r);out.append({**row,'answer':r.get('answer'),'source':r.get('source'),**g})
    return out

def summarize(rows):
    by=collections.defaultdict(lambda:collections.Counter())
    for r in rows:
        c=by[r['set']];c['n']+=1;c['correct']+=r['correct'];c['abstained']+=r['abstained'];c['wrong_certain']+=r['wrong_certain'];c['status:'+str(r['status'])]+=1
    return {k:dict(v) for k,v in sorted(by.items())}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--trust-file',required=True);ap.add_argument('--out',required=True);ap.add_argument('--limit',type=int,default=10**6)
    ap.add_argument('--sets',default=str(ROOT/'tools'/'llm_eval_sets.json'))
    a=ap.parse_args();sets=json.loads(Path(a.sets).read_text(encoding='utf-8'));res={}
    for mode in ('local','llm'):res[mode]={'rows':run_mode(mode,sets,a.trust_file,a.limit)};res[mode]['summary']=summarize(res[mode]['rows'])
    Path(a.out).write_text(json.dumps(res,ensure_ascii=False,indent=1),encoding='utf-8')
    for mode in ('local','llm'):
        print('==',mode)
        for k,v in res[mode]['summary'].items():print(f"  {k:24s} n={v['n']:3d} correct={v.get('correct',0):3d} wrong_certain={v.get('wrong_certain',0):3d} abstained={v.get('abstained',0):3d}")
if __name__=='__main__':main()

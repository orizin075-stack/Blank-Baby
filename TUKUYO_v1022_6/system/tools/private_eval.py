#!/usr/bin/env python3
"""v1022.8.0: the child's own reading (no parent) on new private problems in English and Japanese (private_eval_sets.py).

  private_eval.py --set dev|dev_2|dev_3|dev_4|held_out|held_out_2|held_out_3 [--lang en|ja|all] [--work WORK] [--runtime-trust-file ANCHOR] [--out REPORT.json]
                  [--totals-only] [--compare BEFORE.json]

It reads as the child does in g4-solve: with an individual of its own (made under WORK), so that the v1022 core reads
the Japanese problems; nothing is learned while measuring (learn off).

Each problem is graded: right (the answer, or held back where the problem gives no answer), held (no answer where
there is one), wrong (any other answer, or an answer where there is none). Reported per language: right, held, wrong,
how many it answers (its range), and how often an answer it gives is wrong.

The held-out set is frozen (HELD_OUT_SHA256): run once before the work with --totals-only (its rows go to the report
file and are not shown), and once after. --compare pairs the problems of two reports and gives an exact McNemar test
(two-sided) on right and on wrong. No parent is asked (cost 0).
"""
from __future__ import annotations
import argparse,collections,hashlib,json,math,sys,time
from fractions import Fraction
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'tools'))
from private_eval_sets import DEV,HELD_OUT,DEV_3,HELD_OUT_2,HELD_OUT_3

# dev_2: the held-out set of round 9, measured once before and once after it, and a development set since; dev_3: the
# first draft of round 10's held-out set, replaced before any change (private_eval_sets.py); dev_4: the held-out set of
# round 10, measured once before and once after it, and a development set since (round 11)
SETS={'dev':DEV,'held_out':HELD_OUT,'dev_2':HELD_OUT,'dev_3':DEV_3,'held_out_2':HELD_OUT_2,'dev_4':HELD_OUT_2,
      'held_out_3':HELD_OUT_3}
# the held-out set as written on 2026-10-13, before any change for it: any change to it shows here
HELD_OUT_SHA256='9b82bf398a3165badf2d65585eab0ea794663646f917bea8efa95b8d56a64c85'
# the held-out set of round 10, written on 2026-10-14 before any change of the readers in round 10 (its first draft,
# 2de0b3c3ae5fc230..., is dev_3)
HELD_OUT_2_SHA256='c0b294b5f647bc41c630dcb96b22e1301c51ed61ac6f7b610ddfdc41ef5fa780'
# the held-out set of round 11, written on 2026-10-14 before any change in round 11
HELD_OUT_3_SHA256='5a915ee112435821812c444908102ea1231f7163b793e8344124fcdc18ffcb28'
FROZEN={'held_out':HELD_OUT_SHA256,'held_out_2':HELD_OUT_2_SHA256,'held_out_3':HELD_OUT_3_SHA256}
def fingerprint(s):return hashlib.sha256(json.dumps(s,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def value(expr):
    """the gold answer: an arithmetic expression of whole numbers, evaluated exactly"""
    import ast
    def ev(n):
        if isinstance(n,ast.Expression):return ev(n.body)
        if isinstance(n,ast.Constant) and type(n.value) is int:return Fraction(n.value)
        if isinstance(n,ast.BinOp) and type(n.op) in (ast.Add,ast.Sub,ast.Mult,ast.Div):
            a,b=ev(n.left),ev(n.right)
            return {ast.Add:a+b,ast.Sub:a-b,ast.Mult:a*b,ast.Div:a/b}[type(n.op)]
        if isinstance(n,ast.UnaryOp) and isinstance(n.op,ast.USub):return -ev(n.operand)
        raise ValueError('GOLD_EXPRESSION')
    return ev(ast.parse(expr,mode='eval'))

def grade(got,gold):
    if gold is None:return 'right' if got is None else 'wrong'
    if got is None:return 'held'
    try:return 'right' if Fraction(str(got).replace(',',''))==value(gold) else 'wrong'
    except (ValueError,ZeroDivisionError):return 'wrong'

def mcnemar(b,c):
    """exact two-sided McNemar p-value: b pairs changed one way, c the other"""
    n=b+c
    if n==0:return 1.0
    k=min(b,c);return min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/2**n)

def totals(rows):
    c=collections.Counter(r['grade'] for r in rows);n=len(rows);answered=sum(1 for r in rows if r['got'] is not None)
    return {'problems':n,'right':c['right'],'held':c['held'],'wrong':c['wrong'],'answered':answered,
            'range':round(answered/n,4) if n else 0,'right_share':round(c['right']/n,4) if n else 0,
            'wrong_among_answered':round(c['wrong']/answered,4) if answered else 0}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--set',default='dev',choices=sorted(SETS));ap.add_argument('--lang',default='all',choices=('en','ja','all'))
    ap.add_argument('--out');ap.add_argument('--totals-only',action='store_true');ap.add_argument('--compare')
    ap.add_argument('--work');ap.add_argument('--runtime-trust-file')
    ap.add_argument('--tree',help='the system directory whose reading is measured (default: this one), e.g. an earlier release')
    a=ap.parse_args();tree=Path(a.tree).resolve() if a.tree else HERE;sys.path.insert(0,str(tree/'src'))
    s=SETS[a.set];fp=fingerprint(s)
    if a.set in FROZEN and fp!=FROZEN[a.set]:sys.exit('the held-out set changed since it was frozen: '+fp)
    from tukuyo_g4 import api
    import subprocess,tempfile
    work=Path(a.work) if a.work else Path(tempfile.mkdtemp(prefix='private-eval-'));ind=work/'individual'
    if not ind.exists():
        cmd=[sys.executable,'-B',str(tree/'run_tukuyo.py')]+(['--runtime-trust-file',a.runtime_trust_file] if a.runtime_trust_file else [])
        r=subprocess.run(cmd+['--data',str(ind),'init','--individual-id','PRIVATE-EVAL'],capture_output=True,text=True)
        if not json.loads(r.stdout or '{}').get('ok'):sys.exit('could not make the individual: '+r.stdout[-300:]+r.stderr[-300:])
    langs=['en','ja'] if a.lang=='all' else [a.lang];out={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'set':a.set,'sha256':fp,'langs':{}}
    t0=time.time()
    for lang in langs:
        rows=[]
        for i,(text,gold) in enumerate(s[lang]):
            r=api.solve(text,llm='off',data=str(ind),learn=False);got=r.get('answer')
            rows.append({'i':i,'text':text,'gold':None if gold is None else str(value(gold)),'got':got,'reason':r.get('reason'),'route':r.get('route'),'grade':grade(got,gold)})
        out['langs'][lang]={'totals':totals(rows),'rows':rows}
    out['total']=totals([r for v in out['langs'].values() for r in v['rows']]);out['seconds']=round(time.time()-t0,1)
    out['tree']=str(tree)
    try:out['release_revision']=json.loads((tree/'META'/'RELEASE_RECEIPT.json').read_text(encoding='utf-8'))['payload']['release_revision']
    except Exception:  # noqa: BLE001 - an unsigned tree does not say its revision
        out['release_revision']=None
    print(a.set,'sha256',fp[:16],{k:v['totals'] for k,v in out['langs'].items()},'all',out['total'])
    if a.compare:
        before=json.loads(Path(a.compare).read_text(encoding='utf-8'));cmp={}
        for lang in langs:
            b={r['i']:r['grade'] for r in before['langs'][lang]['rows']};n={r['i']:r['grade'] for r in out['langs'][lang]['rows']}
            gained=sum(1 for i in n if n[i]=='right' and b[i]!='right');lost=sum(1 for i in n if n[i]!='right' and b[i]=='right')
            wplus=sum(1 for i in n if n[i]=='wrong' and b[i]!='wrong');wminus=sum(1 for i in n if n[i]!='wrong' and b[i]=='wrong')
            cmp[lang]={'before':before['langs'][lang]['totals'],'after':out['langs'][lang]['totals'],'right_gained':gained,'right_lost':lost,
                       'right_mcnemar_p':round(mcnemar(gained,lost),6),'wrong_added':wplus,'wrong_removed':wminus,'wrong_mcnemar_p':round(mcnemar(wplus,wminus),6)}
        out['compare']=cmp;print('compare',json.dumps(cmp,ensure_ascii=False))
    if not a.totals_only and a.set not in FROZEN:
        for lang,v in out['langs'].items():
            for r in v['rows']:
                if r['grade']!='right':print(f"  {lang} {r['grade']:5s} {r['i']:2d} | {r['text'][:100]} | gold {r['gold']} got {r['got']} | {r['reason']}")
    if a.out:Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

if __name__=='__main__':main()

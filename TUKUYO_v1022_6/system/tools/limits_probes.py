#!/usr/bin/env python3
"""Probes for the limits named after the v1022.7.7 fusion (evidence_gen4/LIMITS_2026-10-13.md). Our own wording, written
before the readers were run on them; no dev or locked problem. No parent is asked (cost 0).

  limits_probes.py [--work WORK] [--out REPORT.json]

Each probe is (text, expected answer or None, abstain is acceptable). A probe is
  right    answered with the expected answer
  held     no answer (a miss when an answer was expected; what is wanted when None is expected)
  wrong    any other answer, or an answer where None was expected
for g4-solve (the child alone), think (with the v1022 core; needs --work: WORK/v1022_individual is made if missing) and
parser B on its own (a decided value that is not the expected one is wrong: the think gate holds back an answer parser B
decides otherwise).
"""
from __future__ import annotations
import argparse,collections,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'src'))
from fractions import Fraction
from tukuyo_g4 import api

P=lambda t,a,ok=True:(t,a,ok)
PROBES={
 # what the input audit refuses as EVENT_NOT_ESTABLISHED ('If ...'), set aside for the child's own readings
 'hypothetical':[
  P('If Ben shares 24 stickers equally among 4 friends, how many stickers does each friend get?','6'),
  P('If a box holds 12 eggs, how many eggs are in 5 boxes?','60'),
  P('If Nora reads 15 pages a day, how many pages will she read in 6 days?','90'),
  P('Kim has 15 dollars. If she buys a book for 6 dollars, how much money will she have left?','9'),
  P('If each bag has 8 apples and there are 7 bags, how many apples are there in all?','56'),
  P('Leo wants to put 42 photos into an album. If each page holds 6 photos, how many pages will he need?','7'),
  P('If 3 friends each bring 4 balloons, how many balloons do they bring altogether?','12'),
  P('If Rosa saves 5 dollars every week, how many dollars will she save in 8 weeks?','40'),
  P('Eva has 14 pencils. If she gives 5 pencils to Sam, how many pencils will she have?','9'),
 ],
 'counterfactual':[
  P('If Tom had 5 more apples, he would have 12 apples. How many apples does Tom have?','7'),
  P('If Mia had 3 fewer pens, she would have 9 pens. How many pens does Mia have?','12'),
  P('Sam would have 20 cards if he had 6 more cards. How many cards does Sam have?','14'),
  P('If Ann gave away 4 of her shells, she would have 11 shells left. How many shells does Ann have?','15'),
  P('If Ben had bought 2 more books, he would have bought 9 books. How many books did Ben buy?','7'),
  P('Lily would need 5 more beads to have 30 beads. How many beads does Lily have?','25'),
 ],
 'not_done':[
  P('Ann has 10 apples. She plans to give 4 apples to Bob tomorrow. How many apples does Ann have now?','10'),
  P('Lee had 8 cookies. He wanted to eat 3 cookies, but he did not eat any. How many cookies does Lee have?','8'),
  P('Max has 12 marbles. He is going to lose 5 marbles in a game later. How many marbles does Max have now?','12'),
  P('Zoe had 20 stickers. She thought about giving 6 stickers to Kai. How many stickers does Zoe have?','20'),
  P('Omar has 9 toy cars. He might buy 4 more toy cars next week. How many toy cars does Omar have now?','9'),
  P('Rita had 15 shells. She gave 5 shells to Ann, but Ann gave them back. How many shells does Rita have now?','15'),
 ],
 # EQUAL_SHARING_NOT_ESTABLISHED
 'sharing':[
  P('30 candies were shared equally among 5 kids. How many candies did each kid get?','6'),
  P('Split 30 candies among 5 kids so that each kid gets the same number. How many candies does each kid get?','6'),
  P('30 candies were shared among 5 kids, but not equally. How many candies did each kid get?',None),
  P('Ann and Ben shared 30 candies. Ann got 10 more candies than Ben. How many candies did Ben get?','10'),
  P('Four friends shared 20 grapes. Each friend got a different number of grapes. How many grapes did each friend get?',None),
  P('Steven and Megan shared some marbles in the ratio 2:3. Megan got 18 marbles. How many marbles did Steven get?','12'),
 ],
 # UNCOVERED_NUMERIC_OR_OPERATION
 'other_operation':[
  P('Billy gave equal numbers of his 72 lemon drops to his 6 friends. How many lemon drops did each friend get?','12'),
  P('Tom gave 12 apples to each of his 3 friends. How many apples did Tom give away?','36'),
  P('Mia had 10 pens. She gave 4 pens to Sam. How many pens did Sam lose?',None),
 ],
 # the event-scope guard (v1022.7.4) and NEGATED_EVENT (round 6), in English
 'negation':[
  P('Tom had 10 apples. He did not eat 3 of them. How many apples did he eat?',None),
  P('Mia had 10 pens. She did not lose any pens. How many pens does she have now?','10'),
  P('Ben did not buy 6 boxes of pens with 4 pens in each box. How many pens did Ben buy?',None),
  P('Kai had 12 eggs. He did not break 4 of them. How many eggs did he break?',None),
 ],
 # the size or age word guard (ASKED_KIND_NOT_TOLD)
 'kind_words':[
  P('There are 6 large boxes and 4 small bags. How many small boxes are there?',None),
  P('Ken has 5 new toys and 3 old books. How many old toys does Ken have?',None),
  P('Ana has 7 big apples. She ate 2 big apples. How many big apples does she have left?','5'),
  P('Ana has 7 big apples and 3 small apples. How many apples does she have in all?','10'),
  P('There are 8 little ducks and 2 big ducks. How many ducks are there?','10'),
  P('Jo bought 4 new shirts and 3 new hats. How many new shirts did Jo buy?','4'),
  P('Ben has 6 old coins and 5 new coins. How many new coins does Ben have?','5'),
 ],
 # parser B's container rule, and the reader
 'containers':[
  P('There are 36 eggs. Each carton holds 12 eggs. How many cartons are there?','3'),
  P('Liam put 45 pencils into boxes with 9 pencils in each box. How many boxes did he use?','5'),
  P('A baker packs 48 rolls into bags of 6. How many bags does she fill?','8'),
  P('There are 5 vans with 7 kids in each van. How many kids are there?','35'),
  P('Nina has 50 beads. She puts them in jars with 8 beads in each jar. How many jars can she fill?','6'),
  P('There are 4 shelves with 9 books on each shelf. How many shelves are there?','4'),
  P('Jack puts 24 cookies on plates with 6 cookies on each plate. How many cookies are there?','24'),
 ],
}

def grade(got,want,ok_abstain):
    if got is None:return 'held'
    if want is None:return 'wrong'
    try:return 'right' if Fraction(str(got).replace(',',''))==Fraction(want) else 'wrong'
    except (ValueError,ZeroDivisionError):return 'wrong'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work');ap.add_argument('--out');a=ap.parse_args()
    from tukuyo_v1022.semantic_gate import parser_b
    ind=None
    if a.work:
        ind=Path(a.work)/'v1022_individual'
        if not ind.exists():subprocess.run([sys.executable,'-B',str(HERE/'run_tukuyo.py'),'--data',str(ind),'init','--individual-id','LIMITS'],check=True,capture_output=True)
        from tukuyo_v1022 import cognition as cog
    out={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'categories':{}};tot=collections.defaultdict(collections.Counter)
    for cat,ps in PROBES.items():
        rows=[]
        for t,want,ok in ps:
            g=api.solve(t,llm='off');row={'text':t,'expected':want,'g4_solve':g.get('answer'),'g4_reason':g.get('reason')}
            row['g4_grade']=grade(g.get('answer'),want,ok)
            b=parser_b(t);row['parser_b']=b[1] if b else None
            row['parser_b_grade']='undecided' if b is None else ('right' if want is not None and str(b[1])==str(Fraction(want)) else 'wrong')
            if ind is not None:
                base=cog.solve(str(ind),t);th=api.think(str(ind),t,base,llm='off',learn=False)
                ans=None if th.get('uncertain') else th.get('answer');row.update(think=ans,think_reason=th.get('reason'),think_grade=grade(ans,want,ok))
            for k in ('g4','think','parser_b'):
                if row.get(k+'_grade'):tot[k][row[k+'_grade']]+=1
            rows.append(row)
        out['categories'][cat]={'rows':rows,**{k:dict(collections.Counter(r[k+'_grade'] for r in rows if r.get(k+'_grade'))) for k in ('g4','think','parser_b')}}
    out['total']={k:dict(v) for k,v in tot.items()}
    for cat,c in out['categories'].items():print(f"{cat:16s} g4 {c['g4']}  think {c.get('think')}  parser_b {c['parser_b']}")
    print('total',out['total'])
    for cat,c in out['categories'].items():
        for r in c['rows']:
            bad=[k for k in ('g4','think','parser_b') if r.get(k+'_grade')=='wrong']
            if bad:print('  WRONG',bad,cat,'|',r['text'][:100],'| expected',r['expected'],'| g4',r['g4_solve'],'think',r.get('think'),'parser_b',r['parser_b'])
    if a.out:Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

if __name__=='__main__':main()

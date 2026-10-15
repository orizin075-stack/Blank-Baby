#!/usr/bin/env python3
"""Probes for what an outside review of r7 found (2026-10-13): 'Anna has a few apples. She buys 4 more apples. How many
apples now?' was answered 4; the amount Anna had is not given, so no answer can be fixed. Our own wording, written before
anything was changed, in two sets:

  dev       used while fixing
  held_out  written at the same time and frozen (HELD_OUT_SHA256 below): run once before the fix with totals only (its
            rows are written to the report file, not shown), and once after the fix

Each probe is (text, expected answer or None, abstain is acceptable). Graded as in limits_probes.py: right, held (no
answer), wrong (any other answer, or any answer where None is expected). No parent is asked (cost 0).

  review_probes.py [--set dev|held_out] [--work WORK] [--out REPORT.json] [--totals-only]
"""
from __future__ import annotations
import argparse,collections,hashlib,json,subprocess,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'src'));sys.path.insert(0,str(HERE/'tools'))
from tukuyo_g4 import api
from limits_probes import grade

P=lambda t,a,ok=True:(t,a,ok)
DEV={
 # an amount held, said without a number: what it becomes is not known either
 'unknown_start':[
  P('Anna has a few apples. She buys 4 more apples. How many apples now?',None),
  P('Tom has a couple of pens. He buys 3 more pens. How many pens does he have now?',None),
  P('Mia has many stickers. She gets 5 more stickers. How many stickers does she have now?',None),
  P('Ken has a handful of coins. He finds 2 more coins. How many coins does he have?',None),
  P('Sara has apples. She buys 4 more apples. How many apples does she have now?',None),
  P('Leo has a lot of marbles. He wins 6 more marbles. How many marbles does he have now?',None),
  P('Ivy has lots of beads. She buys 10 more beads. How many beads does she have now?',None),
  P('Omar has a number of books. He buys 2 more books. How many books does he have?',None),
  P('Rosa has a bag of oranges. She buys 6 more oranges. How many oranges does she have now?',None),
  P('Nina had a few cookies. She baked 12 more cookies. How many cookies does she have now?',None),
  P('Ben has plenty of crayons. His mom gives him 8 more crayons. How many crayons does Ben have now?',None),
  P('Zoe has a bunch of grapes. She eats 5 grapes. How many grapes are left?',None),
  P('Kai has some money. He earns 7 dollars. How much money does he have now?',None),
  P('Eli has a little money. He earns 7 dollars. How much money does he have now?',None),
  P('Ava collected a few shells. Then she found 9 more shells. How many shells does she have now?',None),
 ],
 # 'N more' says there were some before; asked what one has now, that is not known
 'more_without_before':[
  P('Sara buys 4 more apples. How many apples does she have now?',None),
  P('Sam found 6 more shells at the beach. How many shells does Sam have now?',None),
  P('Lily got 3 more dolls for her birthday. How many dolls does Lily have now?',None),
  P('Sara bought 4 more apples. How many apples did she buy?','4'),
  P('Tom read 12 more pages today. How many pages did he read today?','12'),
 ],
 'known_start':[
  P('Anna has 3 apples. She buys 4 more apples. How many apples now?','7'),
  P('Anna has 3 apples. She buys 4 more apples. How many apples does she have now?','7'),
  P('Tom has 8 pens. He buys a few pencils. How many pens does he have now?','8'),
  P('Ben has 5 apples. Anna has a few apples. Ben buys 4 more apples. How many apples does Ben have now?','9'),
  P('Ben has 5 apples. Anna has a few apples. Ben buys 4 more apples. How many apples do Ben and Anna have in all?',None),
  P('Mia has no stickers. She gets 5 stickers. How many stickers does she have now?','5'),
  P('Mia had a few stickers yesterday. Today she has 9 stickers. How many stickers does she have now?','9'),
  P('Jo has 7 cards. She gives some cards to Max. How many cards does Jo have now?',None),
  P('Jo has 7 cards. She gives a few cards to Max. How many cards does Jo have now?',None),
  P('Jo has 7 cards. She gives many of them to Max. How many cards does Jo have now?',None),
 ],
 'ownership':[
  P('Tom has 6 apples. Tom gives 2 apples to Ann. How many apples does Ann have now?',None),
  P('Tom has 6 apples. He gives 2 apples to Ann. How many apples does Tom have now?','4'),
  P('Tom has 6 apples and Ann has 3 apples. Tom gives 2 apples to Ann. How many apples does Ann have now?','5'),
  P("Tom's sister has 6 apples. Tom has 2 apples. How many apples does Tom's sister have?",'6'),
  P('Tom has 6 apples. His sister has a few apples. How many apples does Tom have?','6'),
 ],
 'time':[
  P('Ann had 10 apples on Monday. On Tuesday she ate 3 apples. How many apples did she have on Monday?','10'),
  P('Ann had 10 apples on Monday. On Tuesday she ate 3 apples. How many apples does she have now?','7'),
  P('Ann will buy 5 apples tomorrow. She has 3 apples now. How many apples does she have now?','3'),
  P('Before lunch, Ann had 12 apples. After lunch, she had 8 apples. How many fewer apples did she have after lunch?','4'),
 ],
 'negation':[
  P('Ann has 10 apples. She does not eat any apples. How many apples does she have now?','10'),
  P('Ann has 10 apples. She did not give 3 apples to Ben. How many apples does she have now?','10'),
  P('Ann has 10 apples. She did not eat 3 of them. How many apples did she eat?',None),
 ],
 'hypothetical':[
  P('If Ann had 4 more apples, she would have 10 apples. How many apples does she have?','6'),
  P('Ann could buy 5 apples, but she buys none. She has 2 apples. How many apples does she have now?','2'),
 ],
}
HELD_OUT={
 'unknown_start':[
  P('Pedro has a few toy trucks. He gets 3 more toy trucks for his birthday. How many toy trucks does Pedro have now?',None),
  P('Grace owns a couple of goldfish. She buys 2 more goldfish. How many goldfish does she own now?',None),
  P('The library has many chairs. It buys 15 more chairs. How many chairs does the library have now?',None),
  P('Hana keeps a jar of buttons. She adds 7 buttons to the jar. How many buttons are in the jar now?',None),
  P('Diego has a stack of comic books. He buys 4 more comic books. How many comic books does he have?',None),
  P('Lucy has a lot of ribbons. She uses 3 ribbons. How many ribbons does Lucy have left?',None),
  P('Noah had some baseball cards. He traded away 5 baseball cards. How many baseball cards does Noah have now?',None),
  P('Emma has crayons. Her friend gives her 6 more crayons. How many crayons does Emma have now?',None),
  P('Yuki has a handful of candies. She eats 2 candies. How many candies are left?',None),
  P('Carlos had a few dollars. He earned 20 dollars mowing lawns. How many dollars does he have now?',None),
  P('Fatima has several pencils. She buys a box of 12 pencils. How many pencils does she have now?',None),
  P('The farmer has a number of cows. He buys 8 more cows. How many cows does the farmer have now?',None),
  P('Amy has dozens of stamps. She buys 10 more stamps. How many stamps does she have now?',None),
  P('Amy has hundreds of stamps. She gives 10 stamps to Joe. How many stamps does Amy have now?',None),
  P('Amy has a pile of rocks. She finds 4 more rocks. How many rocks does she have now?',None),
  P('Zara has a basket of oranges. She buys 3 more oranges. How many oranges does she have now?',None),
 ],
 'more_without_before':[
  P('Olivia picks 5 more flowers. How many flowers does Olivia have now?',None),
  P('Jack catches 3 more fish. How many fish does Jack have now?',None),
  P('Olivia picked 5 more flowers in the afternoon. How many flowers did Olivia pick in the afternoon?','5'),
 ],
 'known_start':[
  P('Pedro has 4 toy trucks. He gets 3 more toy trucks for his birthday. How many toy trucks does Pedro have now?','7'),
  P('Grace owns 2 goldfish. She buys 2 more goldfish. How many goldfish does she own now?','4'),
  P('Lucy has 9 ribbons. She uses 3 ribbons. How many ribbons does Lucy have left?','6'),
  P('Hana has 20 buttons. She also has a few beads. How many buttons does Hana have?','20'),
  P('Emma has 5 crayons and a few markers. Her friend gives her 6 more crayons. How many crayons does Emma have now?','11'),
  P('Zara has an orange. She buys 3 more oranges. How many oranges does she have now?','4'),
  P('Amy has a dozen eggs. She uses 4 eggs. How many eggs does she have left?','8'),
  P('Leo has 10 cookies. His dog has a few toys. Leo eats 4 cookies. How many cookies does Leo have now?','6'),
  P('Leo has many friends. He has 10 cookies and eats 4 cookies. How many cookies does Leo have now?','6'),
 ],
 'ownership':[
  P('Ali has 9 marbles. He gives 4 marbles to Sam. How many marbles does Sam have now?',None),
  P('Ali has 9 marbles and Sam has 2 marbles. Ali gives 4 marbles to Sam. How many marbles does Sam have now?','6'),
  P('Ali has 9 marbles and Sam has 2 marbles. Ali gives 4 marbles to Sam. How many marbles does Ali have now?','5'),
  P('Ali has 9 marbles. Sam has a few marbles. How many marbles do they have altogether?',None),
  P("Mei's brother has 12 stamps. Mei has 5 stamps. How many stamps does Mei's brother have?",'12'),
 ],
 'time':[
  P('On Monday, Rita had 15 stickers. On Tuesday, she gave away 6 stickers. How many stickers did Rita have on Monday?','15'),
  P('On Monday, Rita had 15 stickers. On Tuesday, she gave away 6 stickers. How many stickers does Rita have now?','9'),
  P('Rita will get 5 stickers next week. She has 8 stickers now. How many stickers does Rita have now?','8'),
  P('Last year, Tim had a few rabbits. This year he has 7 rabbits. How many rabbits does Tim have this year?','7'),
 ],
 'negation':[
  P('Bella has 14 apples. She does not sell any apples. How many apples does she have?','14'),
  P('Bella had 14 apples. She did not eat 5 of them. How many apples did she eat?',None),
  P('Bella had 14 apples. She did not give away any apples, but she bought 3 more. How many apples does she have now?','17'),
 ],
 'hypothetical':[
  P('If Max had 3 more books, he would have 11 books. How many books does Max have?','8'),
  P('Max wants to buy 6 books. He has 2 books. How many books does Max have now?','2'),
  P('If Max buys 6 books, he will have 10 books. How many books does Max have now?','4'),
 ],
 'several_steps':[
  P('A box holds 6 eggs. Lina buys 3 boxes and uses 5 eggs. How many eggs does she have left?','13'),
  P('Kofi has 20 dollars. He buys 2 books for 4 dollars each. How much money does he have left?','12'),
  P('There are 4 rows of chairs with 7 chairs in each row. 5 chairs are taken away. How many chairs are left?','23'),
  P('Ruth reads 8 pages each day for 5 days. Then she reads 6 more pages. How many pages did she read in all?','46'),
  P('A team has 12 players. 3 players leave and 5 new players join. How many players are on the team now?','14'),
 ],
}
SETS={'dev':DEV,'held_out':HELD_OUT}
def fingerprint(probes):return hashlib.sha256(json.dumps(probes,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
# the held-out set as written on 2026-10-13, before the fix: any change to it shows here
HELD_OUT_SHA256='7e07e251cb0b2f6d57cbfd1a99726b3381b488b474012df48eb3163d7f26d6f0'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--set',default='dev',choices=sorted(SETS));ap.add_argument('--work');ap.add_argument('--out')
    ap.add_argument('--totals-only',action='store_true');a=ap.parse_args()
    probes=SETS[a.set];fp=fingerprint(probes)
    if a.set=='held_out' and fp!=HELD_OUT_SHA256:sys.exit('the held-out set changed since it was frozen: '+fp)
    ind=None
    if a.work:
        ind=Path(a.work)/'v1022_individual'
        if not ind.exists():subprocess.run([sys.executable,'-B',str(HERE/'run_tukuyo.py'),'--data',str(ind),'init','--individual-id','REVIEW'],check=True,capture_output=True)
        from tukuyo_v1022 import cognition as cog
    out={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'set':a.set,'sha256':fp,'categories':{}};tot=collections.defaultdict(collections.Counter)
    for cat,ps in probes.items():
        rows=[]
        for t,want,ok in ps:
            g=api.solve(t,llm='off');row={'text':t,'expected':want,'g4_solve':g.get('answer'),'g4_reason':g.get('reason'),'g4_grade':grade(g.get('answer'),want,ok)}
            if ind is not None:
                th=api.think(str(ind),t,cog.solve(str(ind),t),llm='off',learn=False)
                ans=None if th.get('uncertain') else th.get('answer');row.update(think=ans,think_reason=th.get('reason'),think_grade=grade(ans,want,ok))
            for k in ('g4','think'):
                if row.get(k+'_grade'):tot[k][row[k+'_grade']]+=1
            rows.append(row)
        out['categories'][cat]={'rows':rows,**{k:dict(collections.Counter(r[k+'_grade'] for r in rows if r.get(k+'_grade'))) for k in ('g4','think')}}
    out['total']={k:dict(v) for k,v in tot.items()}
    print(a.set,'sha256',fp[:16],'probes',sum(len(v) for v in probes.values()),'total',out['total'])
    if not a.totals_only:
        for cat,c in out['categories'].items():print(f"  {cat:20s} g4 {c['g4']}  think {c.get('think')}")
        for cat,c in out['categories'].items():
            for r in c['rows']:
                bad=[k for k in ('g4','think') if r.get(k+'_grade')=='wrong']
                if bad:print('  WRONG',bad,cat,'|',r['text'][:110],'| expected',r['expected'],'| g4',r['g4_solve'],'think',r.get('think'))
    if a.out:Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

if __name__=='__main__':main()

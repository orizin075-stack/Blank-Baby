"""generation 4: what an outside review of r7 found (evidence_gen4/REVIEW_2026-10-13.md §2): an amount held but not
given ('a few apples'), and 'N more' with nothing before it, were read as if they were known. Offline: no parent."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'));sys.path.insert(0,str(ROOT/'tools'))
from tukuyo_g4 import api
import review_probes
from limits_probes import grade

def test_an_amount_not_given_is_not_read_as_none():
    for t in ('Anna has a few apples. She buys 4 more apples. How many apples now?',                    # the review's example (was 4)
              'Tom has a couple of pens. He buys 3 more pens. How many pens does he have now?',
              'Leo has a lot of marbles. He wins 6 more marbles. How many marbles does he have now?',
              'Rosa has a bag of oranges. She buys 6 more oranges. How many oranges does she have now?',
              'Sara has apples. She buys 4 more apples. How many apples does she have now?',
              'Kai has some money. He earns 7 dollars. How much money does he have now?',
              'Jo has 7 cards. She gives many of them to Max. How many cards does Jo have now?',
              'Sara buys 4 more apples. How many apples does she have now?'):
        assert api.solve(t,llm='off')['answer'] is None,t
    # what can still be known: the event asked about, a start found from the end, an amount of something else
    for t,a in (('Sara bought 4 more apples. How many apples did she buy?','4'),
                ('Anna has a few apples. She gives 3 apples to Ben and has 5 apples left. How many apples did Anna have at first?','8'),
                ('Kai has some money. He spends 7 dollars and has 5 dollars left. How much money did he have at first?','12'),
                ('Leo has 5 apples and lots of pears. He eats 2 apples. How many apples does he have now?','3'),
                ('Sam had 5 shells. He found 3 more shells. How many shells does he have now?','8'),
                ('If one pack of gum costs $2, how many packs of gum can you buy with $16?','8'),
                ('Ann had 10 apples on Monday. On Tuesday she ate 3 apples. How many apples did she have on Monday?','10')):
        assert api.solve(t,llm='off')['answer']==a,t

def test_the_review_probes_give_no_wrong_answer():
    assert review_probes.fingerprint(review_probes.HELD_OUT)==review_probes.HELD_OUT_SHA256          # the frozen set as written
    for name,probes in review_probes.SETS.items():
        for cat,ps in probes.items():
            for t,want,ok in ps:
                a=api.solve(t,llm='off')['answer']
                assert grade(a,want,ok)!='wrong',(name,cat,t,a)

"""generation 4: TUKUYO's own English reader. Problems it must read (with the answer) and problems it must leave
unanswered (no reading rather than a guess). The wording is our own; the third-party sets are not copied here."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_g4 import api,reader

READ=[
 ('Nora had 30 shells. She gave 8 shells to her cousin. How many shells does she have left?','22'),
 ('Owen had 12 stamps. His aunt gave him 9 more stamps. How many stamps does Owen have now?','21'),
 ('Pia baked 24 muffins. She ate 3 of them. How many muffins does she have now?','21'),
 ('There were 14 ducks on the pond. 9 more ducks landed on the pond. How many ducks are on the pond now?','23'),
 ('There were 40 people on the train. 15 people got off at the station. How many people are on the train now?',None),
 ('Liam had some marbles. He found 7 more marbles. Now he has 20 marbles. How many marbles did Liam have at first?','13'),
 ('Ada had 50 stickers. She gave some stickers to Ben. Now she has 32 stickers. How many stickers did Ada give to Ben?','18'),
 ('Kim picked 18 apples in the morning and 25 apples in the afternoon. How many apples did Kim pick in all?','43'),
 ('Tom has 26 red marbles and 17 blue marbles. How many marbles does Tom have in all?','43'),
 ('Rosa has 15 more crayons than Ivan. Ivan has 9 crayons. How many crayons does Rosa have?','24'),
 ('Rosa has 31 crayons. She has 12 more crayons than Ivan. How many crayons does Ivan have?','19'),
 ('Sam has 4 times as many cards as Leo. Leo has 6 cards. How many cards does Sam have?','24'),
 ('Mia has 45 beads. Zoe has 28 beads. How many more beads does Mia have than Zoe?','17'),
 ('A farm has 13 cows and 22 pigs. How many animals are on the farm?','35'),
 ('There are 7 boxes. Each box has 6 pens. How many pens are there in all?','42'),
 ('Hana bought 5 bags with 8 oranges in each bag. How many oranges did she buy?','40'),
 ('There are 48 cookies to share equally among 6 children. How many cookies will each child get?','8'),
 ('A van can carry 9 people. How many vans are needed for 40 people?',None),
 ('Each shelf holds 12 books. There are 100 books. How many shelves are needed to hold all the books?','9'),
 ('Each box holds 12 books. There are 100 books. How many boxes can be filled completely?','8'),
 ('A pen costs 3 dollars. How much do 7 pens cost?','21'),
 ('Eli has 40 cents. A sticker costs 6 cents. How many stickers can he buy?','6'),
 ('Ken has 34 dollars. How many more dollars does he need to have 50 dollars?','16'),
 ('Ann has 12 pens and 18 pencils. She wants to put them in identical groups with nothing left over. What is the greatest number of groups she can make?','6'),
 ('Joe ran 3 miles on Monday and 5 miles on Tuesday. How many miles did he run in all?','8'),
]
ABSTAIN=[
 'Nora had 30 shells. She gave some shells to her cousin. How many shells does she have left?',
 'Sam has 5 apples. He bought some more apples. How many apples does Sam have now?',
 'Tim had 40 cards. Lea had 30 cards. He gave her 10 cards. How many cards does she have now?',
 'A farmer had 97 tomatoes. If he picked 83 of them, how many would he have left?',
 'Mila had 20 pencils. She put 8 pencils in a box. How many pencils does Mila have now?',
 'The store ordered 5 drills in May, 6 drills in June and 8 drills in July. If this pattern continues, how many drills will the store order in August?',
 'A stadium has 95 seats. 52 children and 29 adults came to the game. How many seats were empty?',
 'Kate spent a total of $350 on her trip. She spent $125 on food and $135 on hotels. How much did she spend on other things?',
 'What is the capital of France?',
 'How many legs does a spider have?',
]

def test_reads_these_problems():
    for text,want in READ:
        r=api.solve(text,llm='off')
        assert r['answer']==want,(text,r['answer'],r.get('reason'),[x.get('reason') for x in r['readings']])

def test_leaves_these_unanswered():
    for text in ABSTAIN:
        r=api.solve(text,llm='off')
        assert r['answer'] is None,(text,r['answer'],r.get('route'))

def test_every_reading_is_grounded_in_the_text():
    for text,want in READ:
        rd=reader.read(text)
        if want is None or not rd.get('spec'):continue
        for f in rd['spec']['facts']:
            if f.get('span'):assert ''.join(f['span'].split()) in ''.join(text.split()),(text,f)

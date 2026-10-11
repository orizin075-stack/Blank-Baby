"""generation 4: the story reader thinks in more than one step. A count of groups and what one group holds become an
amount of things that the rest of the story can use (3 boxes of 6 pens: 18 pens, then 4 are given away); purchases at
a price each become money spent; several groups of different kinds add up. Problems it must read (with the answer)
and problems it must leave unanswered. Written before the change, in our own words (the third-party sets are not
copied)."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_g4 import api

# groups, then what happens to the things in them
READ_GROUPS_THEN=[
 ("Tom has 3 boxes of pens. There are 6 pens in each box. He gives away 4 pens. How many pens does Tom have now?",'14'),
 ("Lily bought 5 packs of crayons. Each pack has 8 crayons. She lost 3 crayons. How many crayons does she have left?",'37'),
 ("A baker made 4 trays of rolls. There are 12 rolls on each tray. He sold 30 rolls. How many rolls are left?",'18'),
 ("Nora had 2 bags of apples with 9 apples in each bag. She ate 4 apples. How many apples does she have left?",'14'),
]
# groups of two kinds, added up
READ_GROUPS_SUM=[
 ("A club took 3 cars and 2 vans to the lake. There were 4 people in each car and 9 people in each van. How many people went to the lake?",'30'),
 ("There are 5 tables and 3 benches in the hall. Each table has 4 legs and each bench has 6 legs. How many legs are there in all?",'38'),
 ("A shelf holds 6 boxes of red beads and 4 boxes of blue beads. Each box of red beads has 20 beads and each box of blue beads has 25 beads. How many beads are there in all?",'220'),
]
# purchases at a price each, and money spent
READ_SPEND=[
 ("Ana bought 3 notebooks for $4 each and a pen for $2. How much money did she spend?",'14'),
 ("Ben bought a hat for $5 and 2 shirts for $8 each. How much did he spend in all?",'21'),
 ("Kim had 50 cents. She bought a pencil for 15 cents and an eraser for 10 cents. How much money did she have left?",'25'),
]
# a few wordings of a holding the story reader did not read
READ_WORDING=[
 ("Emily started out with 9 toys and sold 4 of them. How many toys does she have left?",'5'),
 ("There are 12 cans in the pantry. Sam put 7 more cans in the pantry. How many cans are in the pantry now?",'19'),
 ("Lucy had 20 shells. She found some more shells and now she has 31 shells. How many shells did she find?",'11'),
 ("Ryan collected 50 leaves. He lost 12 leaves. Later, 9 more leaves blew away. How many leaves are left?",'29'),
 ("There were 14 kids on the field. Then 8 kids decided to join in. How many kids are on the field now?",'22'),
]
# groups said in other ways: 'N things, each having M', 'was given N', a question that repeats the story's number,
# 'N bugs eat two flowers each', a count after an ordinal ('the fifth grade')
READ_GROUPS_WORDING=[
 ("The album has 6 pages, each having 12 stamps. How many stamps does the album have in total?",'72'),
 ("Mia keeps 4 jars, each containing 15 buttons. How many buttons does she keep?",'60'),
 ("Leo was given 5 crates of pears. Each crate holds 20 pears. How many pears was Leo given?",'100'),
 ("A shop has 8 boxes of nails. Each box has 250 nails. How many nails are there altogether in the 8 boxes?",'2000'),
 ("Kim saw 4 frogs eat three flies each. How many flies did the frogs eat in all?",'12'),
 ("For the third grade show, the benches were put into 9 rows with 7 benches in each row. How many benches were put out?",'63'),
]
# written with the change: a holding stated before and after, and the question asks what happened in between
READ_LATER=[
 ("Nina had 40 stickers in her book. After a month she had 26 left. How many stickers did she use in the month?",'14'),
 ("A cook had 30 eggs. After baking a cake he had 18 left. How many eggs did he use in the cake?",'12'),
 ("There are 20 ducks on the pond. Some more come to join them. Now there are 35 ducks. How many ducks came to join them?",'15'),
 ("Ivy's rope was 50 inches long. After she cut a piece it was 32 inches long. How much did she cut off?",'18'),
]
# written with the change: a common fact the story does not state (fpl.KNOWN_FACTS)
READ_KNOWN=[
 ("Max sees 6 cats. How many legs do the cats have?",'24'),
 ("A farm has 5 hens and 3 goats. How many legs do the animals have in all?",'22'),
 ("There are 7 tricycles in the yard. How many wheels are there?",'21'),
 ("I count 12 ants. How many legs do I count?",'72'),
]
# written with the change: a number that is the subject of its own verb after 'and'; 'got off'; 'the first half';
# what is left to do; a list whose kinds share the last thing named
READ_LATER2=[
 ("There were 50 trees in a yard. 6 of them fell and another 9 of them were cut. How many trees are left?",'35'),
 ("A bus had 30 riders. 12 riders got off at the park. 5 riders got off at the zoo. How many riders are on the bus now?",'13'),
 ("There are some people on a boat. At the dock, 6 more people got on the boat and 4 people got off. If there are 20 people on the boat in the end, how many people were on the boat at first?",'18'),
 ("In the first half of the game Ava scored 12 points. In the second half she scored 9 points. How many points did she score in all?",'21'),
 ("Ben's book has 120 pages. He read 45 of the pages. How many pages does he have left to read?",'75'),
 ("The club has 60 raffle tickets to sell. They sold 22 tickets on Monday and 15 tickets on Tuesday. How many tickets do they have left to sell?",'23'),
 ("A bakery sold 3 lemon, 5 cherry and 4 apple tarts. How many tarts did it sell in all?",'12'),
]
ABSTAIN_LATER2=[
 # someone else read them; a kind of the list that the question does not ask for in full
 "Ben's book has 120 pages. Ann read 45 of the pages. How many pages does Ben have left to read?",
 "A bakery sold 3 lemon, 5 cherry and 4 apple tarts and some pies. How many tarts and pies did it sell in all?",
]
ABSTAIN_KNOWN=[
 # the story says something about legs; a thing whose legs are not a common fact; some bikes of unknown number
 "Max sees 6 cats. One cat has only 3 legs. How many legs do the cats have?",
 "Max sees 6 robots. How many legs do they have?",
 "There are 7 tricycles and some bikes in the yard. How many wheels are there?",
]
ABSTAIN=[
 # what one group holds is not given, or not for every kind
 "Tom has 3 boxes of pens. He gives away 4 pens. How many pens does Tom have now?",
 "A club took 3 cars and 2 vans to the lake. There were 4 people in each car. How many people went to the lake?",
 # some boxes only; two different contents for one box
 "Tom has 3 boxes of pens. Some boxes have 6 pens. How many pens does Tom have?",
 "Tom has 3 boxes. Each box holds 6 pens or 4 markers. How many pens does Tom have?",
 # a price that is not given; money in two holdings
 "Ana bought 3 notebooks for $4 each and a pen. How much money did she spend?",
 "Kim had 50 cents. She bought a pencil for 15 cents and an eraser. How much money did she have left?",
 # the things are given away by someone else, from their own boxes
 "Tom has 3 boxes of pens. There are 6 pens in each box. Ann gives away 4 pens. How many pens does Tom have now?",
 # the question names another number than the story; only some of the pages have stamps
 "A shop has 8 boxes of nails. Each box has 250 nails. How many nails are there altogether in 6 boxes?",
 "The album has 6 pages, some having 12 stamps. How many stamps does the album have in total?",
]

def test_reads_these_problems():
    for text,want in READ_GROUPS_THEN+READ_GROUPS_SUM+READ_SPEND+READ_WORDING+READ_GROUPS_WORDING+READ_LATER+READ_KNOWN+READ_LATER2:
        r=api.solve(text,llm='off')
        assert r['answer']==want,(text,r['answer'],r.get('reason'),[x.get('reason') for x in r['readings']])

def test_leaves_these_unanswered():
    for text in ABSTAIN+ABSTAIN_KNOWN+ABSTAIN_LATER2:
        r=api.solve(text,llm='off')
        assert r['answer'] is None,(text,r['answer'],r.get('route'))

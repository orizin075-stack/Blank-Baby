"""generation 4: the story reader, sixth round. Everyday stories said in more ways ('borrowed 25 of them', 'she already
had 4', 'to start with', 'on rides', 'start with 3 coins'), the rest of something shared out or used up, percent
changes, amounts in two units at once ('1 hour and 15 minutes', '2 kg 300 g'), what one thing weighs or costs when only
totals are given, and pieces of a kind ('pieces of paper', 'pieces of clothing'). Problems it must read (with the
answer) and problems it must leave unanswered. Written before the change, in our own words (the third-party sets are
not copied)."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_g4 import api

# everyday stories of having, getting and losing, said in other ways
READ_STORY=[
 ("The school library has 80 history books. The fourth graders borrowed 25 of them. How many history books are left?",'55'),
 ("Nina had 40 points. If she scored another 6 points, how many points would she have in total?",'46'),
 ("At the fair Omar spent 3 dollars on snacks, 5 dollars on rides and 4 dollars on games. How much money did he spend in all?",'12'),
 ("Leo had a box of crayons. Later he gave six to his sister. Now Leo has nine crayons. How many crayons did Leo have to start with?",'15'),
 ("Ana bought 6 apples at the market, but she already had 4 apples. How many apples does she have now?",'10'),
 ("Mia's ribbon was 30 inches long. If she cut off 8 inches, how long is her ribbon now?",'22'),
 ("A shop had 12 toys on a shelf. If they sold 5 toys, but then put 7 more on the shelf, how many toys would be on the shelf?",'14'),
 ("Ben owned 50 stamps. For his birthday he got twelve more. How many stamps does Ben have in all?",'62'),
 ("In a game you start with 3 coins. If you got 5 more coins in the first round and 4 more in the second, how many coins would you have?",'12'),
 ("There were 40 people on the train. After the first stop there were 25 people left. How many people got off?",'15'),
 ("Tom had 50 cents. He bought a pen for 20 cents and a ruler for 15 cents. How much money did Tom spend?",'35'),
 ("Kim read 20 pages of her book. The book has 120 pages. Kim read 30 more pages later. How many pages has she read in all?",'50'),
 ("Max had 9 friends over for a party. Later four of his friends had to go home. How many friends were left?",'5'),
 ("A store has 50 vases. 6 vases are broken, and 30 vases are sold. How many vases are left?",'14'),
 ("Frank bought 20 rolls for dinner. If his family ate 12, how many rolls does he have left?",'8'),
]
ABSTAIN_STORY=[
 # no count at the end; an amount not given; a price not given
 "Leo had a box of crayons. Later he gave six to his sister. How many crayons did Leo have to start with?",
 "Ana bought 6 apples at the market, but she already had some apples. How many apples does she have now?",
 "At the fair Omar spent 3 dollars on snacks and some money on rides. How much money did he spend in all?",
 "Tom had 50 cents. He bought a pen. He also bought a ruler for 15 cents. How much money did Tom spend?",
]
# the rest of something, shared out or used up
READ_REST_THEN=[
 ("Nina had 45 stickers. She gave 9 stickers to her sister and put the rest into pages with 4 stickers on each page. How many pages did she fill?",'9'),
 ("Omar bought 50 tickets. He used 14 tickets at the arcade and decided to use the rest on rides. If each ride costs 6 tickets, how many rides can he go on?",'6'),
 ("Lisa uploaded 40 photos. She put 16 photos into one album and put the rest into 3 other albums equally. How many photos were in each of the 3 albums?",'8'),
 ("A painter has to paint 12 rooms. Each room takes 5 hours to paint. If he has already painted 9 rooms, how many more hours will it take him to paint the rest?",'15'),
 ("There are 50 books to put away. A teacher takes 14 of them and leaves Sam with the rest. If he can fit 8 books on a shelf, how many shelves will he need?",'5'),
]
ABSTAIN_REST_THEN=[
 "Nina had 45 stickers. She gave some stickers to her sister and put the rest into pages with 4 stickers on each page. How many pages did she fill?",
]
# percent changes
READ_PERCENT=[
 ("A bike costs $200. It is on sale for 25% off. How much does the bike cost on sale?",'150'),
 ("Sara had $500 in the bank. She earned 4% interest in one year. How much money does she have after the year?",'520'),
 ("A meal costs $40. The tip is 15% of the cost. How much is the tip?",'6'),
 ("A jacket regularly costs $80. If the sale price is 10% off the regular price, what is the sale price?",'72'),
]
ABSTAIN_PERCENT=[
 "A bike costs $200. It is on sale. How much does the bike cost on sale?",
 "A bike costs $200. Ann's bike costs 25% less than Ben's bike. How much does Ann's bike cost?",
]
# amounts in two units at once
READ_COMPOUND=[
 ("Kai ran for 1 hour and 15 minutes on Monday and 40 minutes on Tuesday. How many minutes did he run in all?",'115'),
 ("A bag weighs 2 kg 300 g. Another bag weighs 900 g. How many grams do the two bags weigh together?",'3200'),
 ("A board is 3 feet 4 inches long. How many inches long is the board?",'40'),
]
ABSTAIN_COMPOUND=[
 "Kai ran for 1 hour and 15 minutes on Monday and for a while on Tuesday. How many minutes did he run in all?",
]
# what one thing weighs or costs, when only totals are given
READ_UNIT_VALUES=[
 ("The weight of 4 apples is 600 g. The total weight of 2 apples and 3 pears is 900 g. How much heavier is a pear than an apple?",'50'),
 ("The weight of 2 bricks is 6 kg. The total weight of 1 brick and 2 blocks is 13 kg. How much heavier is a block than a brick?",'2'),
]
ABSTAIN_UNIT_VALUES=[
 "The weight of 4 apples is 600 g. The total weight of some apples and 3 pears is 900 g. How much heavier is a pear than an apple?",
]
# pieces of a kind
READ_PIECES=[
 ("Jo has 20 red sheets of paper and 15 blue sheets of paper. How many pieces of paper does she have?",'35'),
 ("Tim gave away 12 shirts and 8 jackets. How many pieces of clothing did he give away in all?",'20'),
 ("A mailman delivered 7 letters and 4 magazines to a house. How many pieces of mail did he deliver in all?",'11'),
]
ABSTAIN_PIECES=[
 "Tim gave away 12 shirts and 8 books. How many pieces of clothing did he give away in all?",
]

# written with the change: a part of a whole sold, a price going up, totals of other kinds, a gain before the rest
READ_LATER=[
 ("A store had 80 shirts. It sold 25% of them. How many shirts are left?",'60'),
 ("A TV costs $500. The price goes up by 10%. What is the new price?",'550'),
 ("The weight of 5 dogs is 50 kg. The total weight of 2 dogs and 3 cats is 32 kg. How much heavier is a dog than a cat?",'6'),
 ("The cost of 3 pens is $6. The total cost of 2 pens and 4 pencils is $8. How much does a pencil cost?",'1'),
 ("Omar bought 50 tickets. He won 10 more tickets and used 14 tickets at the arcade, and decided to use the rest on rides. If each ride costs 6 tickets, how many rides can he go on?",'7'),
]
# written with the change: traps (the first two were answered by a version of this round)
ABSTAIN_LATER=[
 "Nina had 45 stickers. She gave 9 stickers to her sister and some to her brother, and put the rest into pages with 4 stickers on each page. How many pages did she fill?",
 "Lisa uploaded 40 photos. She put some photos into one album and put the rest into 3 other albums equally. How many photos were in each of the 3 albums?",
 "Ana bought 6 apples at the market, but she already had a few apples. How many apples does she have now?",
 "At the fair Omar spent 3 dollars on snacks and a few dollars on rides. How much money did he spend in all?",
 "Mia's ribbon was 30 inches long. If Ann cut off 8 inches of her own ribbon, how long is Mia's ribbon now?",
 "There were 40 people on the train. After the first stop some people got off. How many people got off?",
 "The weight of 4 apples is 600 g. How much heavier is a pear than an apple?",
]

# found by the full suite (tests/test_v1022_5_fusion.py) once 'at 5 km per hour' could be read: a number of what did not
# happen was worked with. The reader before this round did the same for groups and rates ('did not buy 3 boxes with 6 pens')
READ_NOT_NEGATED=[
 ("A train traveled at 5 km per hour for 4 hours. How far did it travel?",'20'),
 ("Sam read 4 pages a day for 6 days. How many pages did he read?",'24'),
]
ABSTAIN_NEGATED=[
 "A train did not travel at 5 km per hour for 4 hours. How far did it travel?",
 "Tom did not buy 3 boxes with 6 pens in each box. How many pens did he buy?",
 "Ann did not walk 3 miles each day for 5 days. How many miles did she walk?",
 "A car did not go 60 miles per hour for 2 hours. How far did it go?",
 "Sam didn't read 4 pages a day for 6 days. How many pages did he read?",
]

def test_reads_these_problems():
    for text,want in READ_STORY+READ_REST_THEN+READ_PERCENT+READ_COMPOUND+READ_UNIT_VALUES+READ_PIECES+READ_LATER+READ_NOT_NEGATED:
        r=api.solve(text,llm='off')
        assert r['answer']==want,(text,r['answer'],r.get('reason'),[x.get('reason') for x in r['readings']])

def test_leaves_these_unanswered():
    for text in ABSTAIN_STORY+ABSTAIN_REST_THEN+ABSTAIN_PERCENT+ABSTAIN_COMPOUND+ABSTAIN_UNIT_VALUES+ABSTAIN_PIECES+ABSTAIN_LATER+ABSTAIN_NEGATED:
        r=api.solve(text,llm='off')
        assert r['answer'] is None,(text,r['answer'],r.get('route'))

"""generation 4: the story reader reads shares, rates and proportions said in more ways. Things shared out equally
('they are divided equally into 6 bags', 'for 9 players to share', 'how big is each group'), what is left over and how
many more make the shares equal, a price or a rate for one and a number of things in the question ('4 notebooks for
$10: 6 notebooks?', 'it takes 3 cups to make a cake'), an amount said in another unit, 'the rest are', the room left in
a holder. Problems it must read (with the answer) and problems it must leave unanswered. Written before the change, in
our own words (the third-party sets are not copied)."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_g4 import api

# things shared out equally, said in other ways
READ_SHARE=[
 ("Rosa has 42 beads. They are divided equally into 6 bags. How many beads are in each bag?",'7'),
 ("56 apples are being shared equally among 8 kids. How many apples does each kid get?",'7'),
 ("There are 45 cards for 9 players to share. How many cards will each player get if they share the cards equally?",'5'),
 ("You want to share 36 stickers among 4 friends. How many stickers would each friend get?",'9'),
 ("Ella baked 30 muffins. She planned to give them equally to her 5 neighbors. How many muffins will each neighbor get?",'6'),
 ("There are 72 marbles in Tim's collection. If the marbles are put into 8 groups, how big is each group?",'9'),
 ("Ivan scored 120 points in 6 rounds. If he scored the same number of points each round, how many points did he score per round?",'20'),
 ("Leo has 50 cards. They are split equally into 6 piles. How many cards are in each pile?",'8'),
]
# what is left over, and how many groups
READ_SHARE_LEFT=[
 ("There were 38 chairs and Ben put them equally into 5 rows. How many chairs are left?",'3'),
 ("Mia picked 50 plums and packed them evenly in some bags. If there are 8 plums in each bag, how many plums were left unpacked?",'2'),
 ("Mia picked 50 plums and packed them evenly in some bags. If there are 8 plums in each bag, how many bags of plums are there?",'6'),
]
# how many more make the shares equal
READ_EVEN_UP=[
 ("Sara baked 50 cookies. If she wants to fill 8 boxes with the same number of cookies, how many more cookies should she bake?",'6'),
 ("7 friends bought 30 tickets. If they want to split all the tickets so each friend gets the same amount, how many more tickets do they need to buy?",'5'),
 ("There are 100 pencils to be given to 12 students. If each student gets the same number of pencils, at least how many more pencils are needed?",'8'),
]
# a price or a rate for some things, and a number of things in the question
READ_PROPORTION=[
 ("Mia bought 4 notebooks for $10. How much would 6 notebooks cost?",'15'),
 ("Ben bought a kite for 85 cents. How much would 3 kites cost?",'255'),
 ("It takes 5 minutes to wash one car. How long will it take to wash 6 cars?",'30'),
 ("It takes 3 cups of flour to make a cake. How many cakes can you make with 15 cups of flour?",'5'),
 ("It takes 4 eggs to make a pie. How many pies can you make with 18 eggs?",'4'),
 ("If each kite needs 4 sticks, how many sticks are needed for 25 kites?",'100'),
 ("My van gets 18 miles per gallon. How many miles can I drive on 4 gallons of gas?",'72'),
 ("If one bag of rice costs $3, how many bags of rice can you buy with $20?",'6'),
]
# an amount said in another unit
READ_UNITS=[
 ("Lena spent 240 minutes on her painting. How many hours did she spend on her painting?",'4'),
 ("Tom ran 3 kilometers. How many meters did he run?",'3000'),
 ("Ana has 4 dollars. How many cents does she have?",'400'),
 ("A rope is 5 feet long. How many inches long is the rope?",'60'),
]
# 'the rest are'
READ_REST=[
 ("Nick has 90 marbles. 35 are blue and the rest are green. How many green marbles does Nick have?",'55'),
 ("A baker made 70 rolls. He made 25 wheat rolls and the rest are white. How many white rolls did he make?",'45'),
 ("There are 60 people at a party. 22 are men, 18 are women and the rest are children. How many children are at the party?",'20'),
 ("Kai has 48 books. 20 are about birds and the rest are about fish. How many books about fish does Kai have?",'28'),
]
# the room left in a holder, money still needed for two things, two parts of one holding compared
READ_ROOM=[
 ("A shelf holds 40 books. There are 26 books already on the shelf. How many more books can be put on the shelf?",'14'),
 ("Tommy has $50. He wants to buy a $20 ball and a $45 bike. How much more money does Tommy need?",'15'),
 ("Ann has 40 shells. She keeps them in two boxes. If there are 15 shells in the first box, how many more shells are there in the second box than the first box?",'10'),
]

# written with the change: the last group filled up, an amount asked in another unit, a book of so many pages, groups
# said in other ways ('56 books in each of his 9 shelves', 'each plank needs 8 nails', 'each of them brought 4')
READ_LATER=[
 ("A box holds 4 slices. If a company had 329 slices to put into boxes, how many more slices would they need to fill up the last box?",'3'),
 ("Max drove for 3 hours. How many minutes did he drive?",'180'),
 ("Jo is reading a 120-page book. If she reads 25 pages per day, how many days will she take to finish reading the book?",'5'),
 ("The Lee family took a three-day trip. Each day they drove 200 miles. How many total miles did they drive?",'600'),
 ("There were 30 cups on the table, and Ann divided them equally into 4 rows. How many are left?",'2'),
 ("He would use 7 boards. If each board needs 6 nails, how many nails does he need?",'42'),
 ("Ella's 5 friends came over. If each of them brought 3 apples, how many apples do they have in total?",'15'),
 ("Tom wanted to paint the fence using 4 colors. If he has 2 liters of paint for each color, how many liters of paint does he have in all?",'8'),
]
# written with the change: traps
ABSTAIN_LATER=[
 "Sara has 50 cookies and 8 boxes. She wants the same number of cookies as Ben. How many more cookies does she need?",
 "Mia bought 4 notebooks for $10 and 2 pens. How much would 6 notebooks cost?",
 "A shelf holds 40 books. There are 26 books already on the table. How many more books can be put on the shelf?",
 "Ann has 40 shells. She keeps them in three boxes. If there are 15 shells in the first box, how many more shells are there in the second box than the first box?",
 "Lena spent 240 minutes on her painting and 2 hours on her drawing. How many hours did she spend on her painting?",
 "Rosa has 42 beads and 3 rings. They are divided equally into 6 bags. How many beads are in each bag?",
 "Leo has 50 cards. Ann has 20 cards. They are split equally into 6 piles. How many cards are in each pile?",
 "It takes Tom 5 minutes to wash a car. How long will it take Ann to wash 6 cars?",
 "Tommy has $30. He wants to buy a ball and a $45 bike. How much more money does Tommy need?",
 "Kim had 4 dollars and 50 cents. How many cents does she have?",
]
ABSTAIN_SHARE=[
 # not said to be equal, and the share is not a whole number; two kinds of receivers
 "Tia has 29 crayons. She gave some to 4 friends. How many crayons does each friend get?",
 "56 apples are shared equally among 8 kids and 3 adults. How many apples does each kid get?",
 # nothing says the shares must be equal
 "Sara baked 50 cookies. She wants to fill 8 boxes. How many more cookies should she bake?",
]
ABSTAIN_PROPORTION=[
 # the question counts other things than the price or the rate
 "Mia bought 4 notebooks for $10. How much would 6 pens cost?",
 "It takes 5 minutes to wash one car. How long will it take to wash 6 trucks?",
 # someone else's time
 "Lena spent 240 minutes on her painting. How many hours did Ben spend on his painting?",
]
ABSTAIN_REST=[
 # some of a third kind; no 'rest'
 "Nick has 90 marbles. 35 are blue, some are red and the rest are green. How many green marbles does Nick have?",
 "Nick has 90 marbles. 35 are blue. How many green marbles does Nick have?",
 # a thing without a price
 "Tommy has $50. He wants to buy a ball and a $45 bike. How much more money does Tommy need?",
]

def test_reads_these_problems():
    for text,want in READ_SHARE+READ_SHARE_LEFT+READ_EVEN_UP+READ_PROPORTION+READ_UNITS+READ_REST+READ_ROOM+READ_LATER:
        r=api.solve(text,llm='off')
        assert r['answer']==want,(text,r['answer'],r.get('reason'),[x.get('reason') for x in r['readings']])

def test_leaves_these_unanswered():
    for text in ABSTAIN_SHARE+ABSTAIN_PROPORTION+ABSTAIN_REST+ABSTAIN_LATER:
        r=api.solve(text,llm='off')
        assert r['answer'] is None,(text,r['answer'],r.get('route'))

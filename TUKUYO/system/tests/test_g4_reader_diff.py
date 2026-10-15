"""generation 4: 'what is the difference between ...' questions in stories, read by the story reader (reader_en):
the two things compared must each be a holding the story gives (a person's things, or one kind of thing), and the
answer is the larger minus the smaller. Problems it must read (with the answer) and problems it must leave
unanswered. Written before the change, in our own words (the third-party sets are not copied)."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_g4 import api

READ=[
 ("Lena has 129 stickers. Omar has 140 stickers. What is the difference between the number of Lena's stickers and Omar's stickers?",'11'),
 ("Tom has 25 shells. Rosa has 17 shells. What's the difference of the number of Tom's shells and Rosa's shells?",'8'),
 ("You have 7 marbles and your sister has 12 marbles. What's the difference of the number of your marbles and your sister's marbles?",'5'),
 ("Mia has 3 red pens and 8 blue pens. What is the difference between the number of red pens and blue pens?",'5'),
 ("Kai scored 14 points. Ivy scored 9 points. What is the difference between Kai's points and Ivy's points?",'5'),
 # 'after Omar gives 5 away' is an event of the story (the story reader already reads 'after ...' this way): 129 and 135
 ("Lena has 129 stickers. Omar has 140 stickers. What is the difference between the number of Lena's stickers and Omar's stickers after Omar gives 5 away?",'6'),
]
# the difference between a holding before and after what happened, or between it and what happened
READ_TIME=[
 ("A baker had 40 rolls. After selling some, he had 15 rolls left. What is the difference between the number of rolls before selling and after selling?",'25'),
 ("Nina had 18 grapes. After eating some, she had 5 left. What is the difference between the number of grapes Nina had before eating and the number left after eating?",'13'),
 ("Ana lost 6 marbles. Now she has 10 marbles. What is the difference between the number of marbles Ana lost and the number she has now?",'4'),
]
# written with the change that reads them (a holding stated before and after with no change between; a title before a name)
READ_LATER=[
 ("A shop had 22 kites. After selling some, it had 8 kites left. What is the difference between the number of kites before selling and the number left?",'14'),
 ("Mrs. Lee has 58 roses. Mrs. Kim has 24 roses. What's the difference of the number of Mrs. Lee's roses and Mrs. Kim's roses?",'34'),
]
ABSTAIN_TIME=[
 # the holding after is not given; two kinds of things and one 'left'; someone else
 "A baker had 40 rolls. After selling some, he had some rolls left. What is the difference between the number of rolls before selling and after selling?",
 "A baker had 40 rolls and 10 cakes. After selling some, he had 15 left. What is the difference between the number of rolls before selling and after selling?",
 "Ana lost 6 marbles. Now she has 10 marbles. What is the difference between the number of marbles Ana lost and the number Leo has now?",
]
# written after the first version, to keep a guard: with two events, 'after buying' is not the holding at the end
ABSTAIN_LATER=[
 "Tim had 8 cards. He bought 12 more cards. Then he gave 5 cards away. What is the difference between the number of cards before buying and after buying?",
 # people leave in the story: 'the number of customers left' could be those who left or those who remain
 "A waiter had 19 customers. Then 15 customers left. What is the difference between the number of customers at first and the number of customers left?",
]
READ_LATER_GUARD=[
 # 'that left' is what happened: 19 and 15
 ("A waiter had 19 customers. Then 15 customers left. What is the difference between the number of customers at first and the number of customers that left?",'4'),
]
ABSTAIN=[
 # one of the two is not given; someone the story does not name; a number instead of a holding
 "Lena has 129 stickers. Omar has some stickers. What is the difference between the number of Lena's stickers and Omar's stickers?",
 "Lena has 129 stickers. Omar has 140 stickers. What is the difference between the number of Lena's stickers and Kim's stickers?",
 "Lena has 129 stickers. Omar has 140 stickers. What is the difference between the number of Lena's stickers and 100?",
 # a kind the story does not give; the other person has other things
 "Mia has 3 red pens and 8 blue pens. What is the difference between the number of red pens and green pens?",
 "Lena has 129 stickers. Omar has 140 stamps. What is the difference between the number of Lena's stickers and Omar's stickers?",
]

def test_reads_these_problems():
    for text,want in READ+READ_TIME+READ_LATER+READ_LATER_GUARD:
        r=api.solve(text,llm='off')
        assert r['answer']==want,(text,r['answer'],r.get('reason'),[x.get('reason') for x in r['readings']])

def test_leaves_these_unanswered():
    for text in ABSTAIN+ABSTAIN_TIME+ABSTAIN_LATER:
        r=api.solve(text,llm='off')
        assert r['answer'] is None,(text,r['answer'],r.get('route'))

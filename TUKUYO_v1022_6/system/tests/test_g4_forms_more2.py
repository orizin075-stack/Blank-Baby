"""generation 4: a second round of questions that are not stories (forms_more_en): things that happen together again
(least common multiple), a number or an age told by what is done to it (every reading of the words is tried; words
that can be read two ways with two answers are left unanswered), more ways to give a rectangle, a circle or a missing
side, more ways to give a ratio or a rate, a pattern whose places come before the numbers, a mean of a list with days.
Problems it must read (with the answer) and problems it must leave unanswered. Written before the forms, in our own
words (the third-party sets are not copied)."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_g4 import api,reader

READ=[
 # things that happen together again
 ('Mia swims every 4 days and runs every 6 days. She did both today. In how many days will she do both on the same day again?','12'),
 ('One bell rings every 15 minutes and another bell rings every 20 minutes. They just rang together. After how many minutes will they ring together again?','60'),
 ('Sam visits the library every 8 days. Tom visits the library every 12 days. They were both there today. How many days will it be until they are both at the library on the same day again?','24'),
 ('Three lights blink at the same time. One light blinks every 6 seconds, another every 8 seconds and the third every 10 seconds. In how many seconds will they all blink together again?','120'),
 ('A shop sells pens in boxes of 12 and pencils in boxes of 18. Lisa wants the same number of pens and pencils. What is the smallest number of pens she can buy?','36'),
 ('Ken packs cookies in bags of 9 and Eva packs muffins in bags of 6. They packed the same number of treats. What is the least number of cookies Ken could have packed?','18'),
 ('Every 3rd visitor to a fair gets a sticker and every 5th visitor gets a balloon. Which visitor will be the first to get both?','15'),
 # a number or an age from what is done to it
 ('Seven less than four times a number is 29. What is the number?','9'),
 ('If 6 is subtracted from five times a number, the result is 34. Find the number.','8'),
 ('When 4 is added to twice a number, the result is 30. What is the number?','13'),
 ('Nine more than half of a number is 20. What is the number?','22'),
 # the way algebra books read the words: 'half of' takes the nearest term
 ('Half of a number plus 9 equals 20. What is the number?','22'),
 ('Half of the sum of a number and 9 equals 20. What is the number?','31'),
 ('Three times a number is equal to the number plus 18. What is the number?','9'),
 ('Two-thirds of a number is 24. What is the number?','36'),
 ('The difference between a number and 8 is 15. Find the number.','23'),
 ('Lily is 31 years old. She is 7 years older than three times her son\'s age. How old is her son?','8'),
 ('Omar is 14 years old. His age is 2 more than half the age of his cousin. Find the age of his cousin.','24'),
 ('Ruth is 40 years old. Her age is 5 times the age of her granddaughter. How old is her granddaughter?','8'),
 ('In 6 years, Nora will be 20 years old. How old is Nora now?','14'),
 ('9 years ago, Paul was 25 years old. How old is Paul now?','34'),
 # more ways to give a rectangle, a circle or a missing side
 ('A poster was 3 feet wide and 5 feet tall. What is the area of the poster?','15'),
 ('Kim was painting a door. The door was 3 feet wide and 7 feet tall. What is the area of the door?','21'),
 ('The fields behind the school were 4 miles wide and 9 miles long. What is the area of the fields?','36'),
 ('A rectangle had a length of 6 inches and a width of 3 inches. What is the perimeter of the rectangle?','18'),
 ('A garden had a total area of 48 square meters. If the garden was 6 meters wide, how long was it?','8'),
 ('A pond was 4 meters wide. It had an area of 36 square meters. How long is the pond?','9'),
 ('A sheet of paper was 8 inches wide and had an area of 88 square inches. How long was the paper?','11'),
 ('A triangle has an area of 30 square inches and a base of 10 inches. Find its height.','6'),
 ('The perimeter of a card is 30 inches. The card is 9 inches long. How wide is it?','6'),
 ('A round table has a diameter of 6 feet. What is the radius of the table?','3'),
 ('A circle has a radius of 7 cm. What is its diameter?','14'),
 # more ways to give a ratio or a rate
 ('At a zoo the ratio of zebras to lions was 5:2. If there were 35 zebras, how many lions were there?','14'),
 ('The ratio of boys to girls in a choir is 4:5. If the number of girls is 25, find the number of boys.','20'),
 ('A farm has 36 sheep. If the ratio of sheep to goats is 9:2, how many animals are there in total?','44'),
 ('Two numbers are in the ratio 3:7. The difference between the numbers is 20. What is the smaller number?','15'),
 ('A recipe uses 3 cups of sugar for every 4 cups of flour. How many cups of sugar are needed for 12 cups of flour?','9'),
 ('You need 2 liters of juice for every 5 guests. If you have 30 guests, how many liters of juice do you need?','12'),
 ('Ali and Mei collect stamps. For every 4 stamps Ali collects, Mei collects 3. Ali collected 28 stamps. How many stamps did Mei collect?','21'),
 # a pattern whose places come before the numbers
 ('On the first day, Ben found 3 shells. On the second day, he found 7 shells. On the third day, he found 11 shells. If this pattern continues, how many shells will Ben find on the fourth day?','15'),
 ('The coach gave 2 stickers to the first player, 6 stickers to the second player, 18 stickers to the third player and 54 stickers to the fourth player. If this pattern continues, how many stickers will the coach give to the fifth player?','162'),
 # a mean of a list with days
 ('A baker sold 12 cakes on Monday, 15 on Tuesday, 9 on Wednesday and 16 on Thursday. What is the mean of the number of cakes he sold?','13'),
]
ABSTAIN=[
 # not a question about happening together; boxes, not things; hours and minutes; no 'again' and no 'today'
 'Mia swims every 4 days and runs every 6 days. How many times will she swim in 24 days?',
 'A shop sells pens in boxes of 12 and pencils in boxes of 18. Lisa wants the same number of pens and pencils. What is the smallest number of boxes of pencils she must buy?',
 'One bell rings every 15 minutes and another bell rings every 2 hours. They just rang together. After how many minutes will they ring together again?',
 'Mia swims every 4 days and runs every 6 days. In how many days will she swim and run on the same day?',
 # a second unknown; not linear; asks about someone else; not enough to know
 'A number plus another number is 20. What is the number?',
 'A number times itself is 49. What is the number?',
 'Lily is 31 years old. She is 7 years older than three times her son\'s age. How old is her daughter?',
 'Some number is 12 more than another number. What is the number?',
 # not given; another thing; a number-free sentence that changes the thing; needs pi; units differ
 'A room is 12 feet long and 10 feet wide. How tall is the room?',
 'A wall had an area of 40 square feet. It was 8 feet wide. How long is the hallway?',
 'Kim doubled the size of a poster. The poster was 3 feet wide and 5 feet tall. What is the area of the poster?',
 'A round table has a diameter of 6 feet. What is the area of the table?',
 'The perimeter of a card is 30 inches. The card is 9 inches long. How wide is the envelope?',
 'A garden had a total area of 48 square meters. If the garden was 6 feet wide, how long was it?',
 # the ratio is of other things; a verb that is not the one of the ratio; a count that is not whole
 'At a zoo the ratio of zebras to lions was 5:2. If there were 35 zebras, how many tigers were there?',
 'A recipe uses 3 cups of sugar for every 4 cups of flour. How many cups of milk are needed for 12 cups of flour?',
 'For every 4 stamps Ali collects, Mei collects 3. Ali lost 28 stamps. How many stamps did Mei collect?',
 'You need 2 bottles of juice for every 5 guests. If you have 32 guests, how many bottles of juice do you need?',
 # a place missing
 'On the first day, Ben found 3 shells. On the third day, he found 11 shells. If this pattern continues, how many shells will Ben find on the fourth day?',
 # not one list
 'A baker sold 12 cakes on Monday, 15 on Tuesday, 9 on Wednesday and 16 pies. What is the mean?',
]

# written after the first version of the forms, to keep their guards: each must stay unanswered
ABSTAIN_GUARDS=[
 'Pens come in boxes of 12 and pencils in boxes of 18. Lisa bought the same number of boxes of each. What is the smallest number of pens she can buy?',
 'Mia swims every 4 days and runs every 6 days. She did both today. In how many days will she swim again?',
 'Sam visits the library every 8 days. Tom visits the library every 12 days. How many times will they both visit on the same day in 48 days?',
 'Lily is 31 years old. She is 7 years older than three times her son\'s age. How old will her son be in 5 years?',
 'Lily is 31 years old and has 2 cats. She is 7 years older than three times her son\'s age. How old is her son?',
 'A rectangle is 8 cm long and 5 cm wide. What is the area of a square with the same perimeter?',
 'A garden is 8 meters long and 5 meters wide. A path around it is 1 meter wide. What is the area of the garden?',
 'A rug is 6 feet long and 4 feet wide. What is the area of the rug in square inches?',
 'You need 2 liters of juice for every 5 guests. If you have 30 guests and 3 liters of juice, how many more liters do you need?',
 'A recipe uses 3 cups of sugar for every 4 cups of flour. Maria used 12 cups of flour and 2 eggs. How many cups of sugar did she use?',
 'The ratio of cats to dogs is 3:5. There are 15 cats and 10 birds. How many dogs are there?',
 'Nadia scored 12, 15, 9 and 14 points in four games. What is the mean of her scores rounded to the nearest whole number?',
]

def test_the_guards_hold():
    for text in ABSTAIN_GUARDS:
        r=api.solve(text,llm='off')
        assert r['answer'] is None,(text,r['answer'],r.get('route'))

def test_two_readings_with_two_answers_are_left_unread():
    """the grammar's guard: if the words could be read two ways and the two readings give two answers, no answer"""
    from tukuyo_g4 import numbers as N,forms_algebra_en as A
    text='A number is 5. What is the number?'
    nums=N.find(text);span=(0,len('A number is 5.'))
    one=[(('x','number'),('k',0),span)]
    two=[(('+',('x','number'),('k',0)),('k',0),span)]
    unknowns=[('number','the number')]
    assert A._only_answer(text,nums,unknowns,[one],'number','t')['spec']
    assert A._only_answer(text,nums,unknowns,[one+two],'number','t') is None

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
        if not rd.get('spec'):continue
        for f in rd['spec']['facts']:
            if f.get('span'):assert ''.join(f['span'].split()) in ''.join(text.split()),(text,f)

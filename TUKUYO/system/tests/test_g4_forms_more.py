"""generation 4: more questions that are not stories, read by exact patterns (forms_en): number patterns that continue,
the mean of listed numbers, ratios, perimeter and area, two unknown numbers. Problems it must read (with the answer)
and problems it must leave unanswered. Written before the forms, in our own words (the third-party sets are not copied)."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from tukuyo_g4 import api,reader

READ=[
 # a pattern that continues: confirmed by the terms given (a constant step, a constant factor, or steps that grow by a constant)
 ('Lena put 4 shells in the first jar, 7 shells in the second jar, 10 shells in the third jar and 13 shells in the fourth jar. If this pattern continues, how many shells will Lena put in the fifth jar?','16'),
 ('A baker made 3 pies on Monday, 6 pies on Tuesday, 12 pies on Wednesday and 24 pies on Thursday. If this pattern continues, how many pies will the baker make on Friday?','48'),
 ('Jo read 2 pages on the first day, 4 pages on the second day, 7 pages on the third day, 11 pages on the fourth day and 16 pages on the fifth day. If this pattern continues, how many pages will Jo read on the sixth day?','22'),
 ('The shop sold 10 hats in March, 15 hats in April, 20 hats in May and 25 hats in June. If this pattern continues, how many hats will the shop sell in July?','30'),
 ('Ravi put 5 cards on the first page, 9 cards on the second page, 13 cards on the third page and 17 cards on the fourth page. If this pattern continues, how many cards will Ravi put on the sixth page?','25'),
 # the mean of listed numbers
 ('Nadia scored 12, 15, 9 and 14 points in four games. What is the mean of her scores?','12.5'),
 ('The temperatures this week were 20, 22, 19, 25, 21, 23 and 24 degrees. What was the average temperature?','22'),
 # ratios
 ('The ratio of cats to dogs at the shelter is 3:5. There are 15 cats. How many dogs are there?','25'),
 ('The ratio of red beads to blue beads in a jar is 2:7. If there are 28 blue beads, how many red beads are there?','8'),
 ('For every 2 laps Ana swims, Ben swims 5. Ana swam 8 laps. How many laps did Ben swim?','20'),
 ('Paul and Rita shared some cards in the ratio 4:3. Rita got 21 cards. How many cards did Paul get?','28'),
 ('Two numbers are in the ratio 2:5. Their sum is 42. What is the larger number?','30'),
 ('For every 5 apples Kai picks, Lin picks 3. Kai picked 40 apples. How many fewer apples did Lin pick than Kai?','16'),
 ('A class has 18 girls and the rest are boys. The ratio of girls to boys is 3:4. How many boys are there?','24'),
 # perimeter and area (no unit is converted)
 ('A garden is 8 meters long and 5 meters wide. What is the perimeter of the garden?','26'),
 ('A rug is 6 feet long and 4 feet wide. What is the area of the rug?','24'),
 ('A square tile has sides of 9 inches. What is its perimeter?','36'),
 ('The perimeter of a regular pentagon is 45 cm. How long is each side?','9'),
 ('The perimeter of an equilateral triangle is 39 inches. Find the length of each side.','13'),
 ('A rectangle has an area of 72 square feet. Its length is 9 feet. What is its width?','8'),
 ('The area of a parallelogram is 96 square inches and its base is 12 inches. Find its height.','8'),
 # two unknown numbers
 ('The sum of two numbers is 50. One of the numbers is 18. What is the other number?','32'),
 ('The sum of two numbers is 30 and their difference is 6. What is the larger number?','18'),
 ('The difference between two numbers is 7. The larger number is 20. What is the smaller number?','13'),
]
ABSTAIN=[
 # three terms whose steps differ: more than one pattern fits
 'Kim saved 2 coins in June, 3 coins in July and 5 coins in August. If this pattern continues, how many coins will Kim save in September?',
 # a position missing, two terms only, no pattern at all
 'Ivy planted 3 trees in the first row and 9 trees in the third row. If this pattern continues, how many trees will she plant in the fourth row?',
 'Bo ate 2 grapes on Monday and 4 grapes on Tuesday. If this pattern continues, how many grapes will Bo eat on Wednesday?',
 'A club had 7 members in January, 3 members in February, 9 members in March and 1 member in April. If this pattern continues, how many members will it have in May?',
 # the count stated is not the count listed; a number that is not in the list
 'In five games Nadia scored 12, 15, 9 and 14 points. What is the mean of her scores?',
 'Nadia scored 12, 15, 9 and 14 points. Her brother scored 10 points. What is the mean of her scores?',
 # the ratio is of other things than the ones known or asked; a share that is not a whole number
 'The ratio of cats to dogs is 3:5. There are 15 cats. How many birds are there?',
 'The ratio of cats to dogs is 3:5. There are 15 birds. How many dogs are there?',
 'The ratio of cats to dogs is 3:5. There are 14 cats. How many dogs are there?',
 # units that would need converting; a solid; a triangle that is not equilateral
 'A garden is 8 meters long and 50 centimeters wide. What is its perimeter?',
 'A box is 3 feet long, 2 feet wide and 4 feet high. What is its perimeter?',
 'The perimeter of a triangle is 39 inches. Find the length of each side.',
 # not enough to know
 'The sum of two numbers is 30. What is the larger number?',
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
        if not rd.get('spec'):continue
        for f in rd['spec']['facts']:
            if f.get('span'):assert ''.join(f['span'].split()) in ''.join(text.split()),(text,f)

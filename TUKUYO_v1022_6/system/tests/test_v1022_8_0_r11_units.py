"""v1022.8.0 round 11: the reader by what the amounts are (reader_units). Each number is read as what it is (an amount of
a thing, a rate, an amount said against another, a part) and the question as what it asks for; a few laws, the same for
every wording, put them together. Every problem here is written for the tests; none is from a held-out set."""
import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from tukuyo_g4 import api, reader, reader_units as U  # noqa: E402


def units(text):
    """the answer of the reader by units alone, checked as every reading is (or None)"""
    r = U.read_ja_text(text) if U.re.search(r'[぀-ヿ一-鿿]', text) else U.read_en(text)
    if not r.get('spec'):
        return None
    ev = api.evaluate(r['spec'], 'own')
    return ev['answer'] if ev['ok'] else None


EN = [
    # rate: an amount for each of another, times how many of those
    ('Bakery boxes hold 6 rolls each. Mr. Ito packs 9 boxes. How many rolls does he pack?', 54),
    ('Parking costs $4 per hour. What does parking cost for 7 hours?', 28),
    ('A jug holds 3 liters of water. How many liters do 5 jugs hold?', 15),
    ('Dana jogs 2 miles every day. How many miles does she jog in 3 weeks?', 42),
    # groups: an amount over a rate; share: an amount over a count, said to be equal
    ('Stamps come in sheets of 8. Ravi needs 56 stamps. How many sheets should he buy?', 7),
    ('Six cousins split 42 cherries evenly. How many cherries does each cousin get?', 7),
    ('Nine tickets came to $63 in all. What did each ticket cost in dollars?', 7),
    # compare and part
    ('A goose weighs 5 kilograms. A swan weighs 3 kilograms more than the goose. How many kilograms does the swan weigh?', 8),
    ('Rex is 36 years old. His nephew is 27 years younger than him. What is his nephew\'s age?', 9),
    ('A cat weighs 4 kilograms. A dog weighs 5 times as much. How many kilograms does the dog weigh?', 20),
    ('Owls made up one fourth of the 48 birds in the barn. How many owls were in the barn?', 12),
    # holding, need, change, rest, the whole less its container
    ('The pond had 30 frogs. Then 6 frogs hopped away and 9 tadpoles became frogs. How many frogs does the pond have now?', None),
    ('The shelf had 40 jars. Mo added 12 more jars. Later 7 jars were given to a neighbor. How many jars are on the shelf?', 45),
    ('A bike path is 20 miles long. Gus has ridden 8 miles of it. How many more miles must he ride to finish?', 12),
    ('In the morning the bin had 90 apples. In the evening 35 apples were left. How many apples were sold that day?', 55),
    ('A pack of 30 balloons has 4 popped ones. How many balloons in the pack are not popped?', 26),
    ('A basket of pears weighs 9 kilograms. The empty basket weighs 1 kilogram. How much do the pears weigh in kilograms?', 8),
    # known facts, a measure in two units, ages later, an amount the question does not need
    ('There are 6 bicycles in the rack. How many wheels do the bicycles have in all?', 12),
    ('A play lasts 2 hours and 10 minutes. How many minutes long is the play?', 130),
    ('Ada is 7 years old and her aunt is 31 years old. In 5 years, what will be the sum of their ages?', 48),
    ('Leo is 8 years old. He has 3 bags of marbles with 12 marbles in each bag. How many marbles does he have?', 36),
    ('Mina reads 9 pages each night. How many pages does she read in a week?', 63),
]

JA = [
    ('1ふくろにみかんが8こずつ入っています。5ふくろでは何こですか。', 40),
    ('お茶は1本150円です。4本では何円ですか。', 600),
    ('毎日3kmずつ2週間歩きました。全部で何km歩きましたか。', 42),
    ('電池は6本入りのパックで売っています。電池が42本いります。何パック買えばよいですか。', 7),
    ('5600円を7人で等分すると、1人あたり何円になりますか。', 800),
    ('兄は14才です。弟は兄より5才年下です。弟は何才ですか。', 9),
    ('白いテープは80cmです。赤いテープは白いテープの3倍です。赤いテープは何cmですか。', 240),
    ('クラスの32人のうち、その4分の1がめがねをかけています。めがねをかけている人は何人ですか。', 8),
    ('池にカエルが30ぴきいました。6ぴきがほかの池へうつり、9ひきがふえました。カエルは今何びきいますか。', 33),
    ('サイクリングコースは全長20kmです。ゆいさんは8km走りました。ゴールまであと何kmですか。', 12),
    ('朝、かごにりんごが90こありました。夕方には35こ残っていました。何こ売れましたか。', 55),
    ('なしの入ったかごの重さは9kgです。かごだけの重さは1kgです。なしの重さは何kgですか。', 8),
    ('自転車が6台あります。車輪は全部で何個ですか。', 12),
    ('ゆうたさんは7才、おばさんは31才です。5年後、2人の年れいの合計は何才ですか。', 48),
    ('はるかさんは毎晩9ページずつ本を読みます。7日間では何ページ読みますか。', 63),
]


@pytest.mark.parametrize('text,answer', EN + JA)
def test_the_laws_read_these(text, answer):
    got = units(text)
    if answer is None:
        assert got is None, got
    else:
        assert got == Fraction(answer), (text, got, (U.read_ja_text(text) if U.re.search(r'[぀-ヿ一-鿿]', text) else U.read_en(text)).get('reason'))


# What the laws must not read: each is a way the reader by units read wrongly while it was written, or a trap written
# for it (the holder of a rate or an event is another; an amount not said; a share not said to be equal; money for
# things bought taken as money that came; a total the story tells of its own)
HOLD = [
    'Tom has 5 apples. He gives 2 apples to Sam. How many apples does Sam have?',
    'A car travels at 50 miles per hour. A bus travels for 3 hours. How far does the car travel?',
    'Tom has 3 boxes of pens. There are 6 pens in each box. Ann gives away 4 pens. How many pens does Tom have now?',
    'Sara has 30 dollars. She buys 3 books for 12 dollars each. How much money does she have left?',
    'Tommy has $30. He wants to buy a ball and a $45 bike. How much more money does Tommy need?',
    'Kai ran for 1 hour and 15 minutes on Monday and for a while on Tuesday. How many minutes did he run in all?',
    'Rita had 15 shells. She gave 5 shells to Ann, but Ann gave them back. How many shells does Rita have now?',
    'Ann has 10 apples. She plans to give 4 apples to Bob tomorrow. How many apples does Ann have now?',
    'A rope is 30 meters long. It is cut into 6 pieces. How long is each piece in meters?',
    'Tom had 5 apples. Ann had 9 apples. How many apples did Tom get?',
    'Max sees 6 cats. One cat has only 3 legs. How many legs do the cats have?',
    'A rug is 6 feet long and 4 feet wide. What is the area of the rug in square inches?',
    'Kim had 4 dollars and 50 cents. How many cents does she have?',
    'A shop sold 45 cakes on Monday. It sold 12 fewer cakes on Tuesday than on Monday. How many cakes did it sell on Monday?',
    'Two crates hold a total of 30 melons. The first crate and a basket hold a total of 22 melons. How many melons are in all?',
    'Jo got $14 to buy a present. This covered half of the cost. How much did the present cost?',
    'A garden is a rectangle with an area of 300 square meters. It is 20 meters long. What is its perimeter?',
    'About how many stickers does each of the 7 children get if 50 stickers are shared?',
    'There are 4 red balls and 6 blue balls. How many red balls in total?',             # one kind asked (found by the suite)
    '1箱に12個入りが6箱あります。箱は全部で何個？',                                         # the boxes asked (found by the suite)
    'たろうさんはりんごを5こ持っています。2こをはなこさんにあげました。はなこさんはりんごを何こ持っていますか。',
    '箱に6こずつたまごが入っています。4ふくろあります。たまごは全部で何こですか。',
    '30本のペンを5人で分けました。1人何本ですか。',
    '1日に20ページずつ読むと、150ページの本を読み終えるのに何日かかりますか。',
]


@pytest.mark.parametrize('text', HOLD)
def test_the_laws_do_not_read_these(text):
    assert units(text) is None


def test_every_reading_is_the_checker_s_and_says_how_it_was_made():
    for text, answer in EN + JA:
        if answer is None:
            continue
        r = U.read_ja_text(text) if U.re.search(r'[぀-ヿ一-鿿]', text) else U.read_en(text)
        spec = r['spec']
        assert spec['reader'].startswith('tukuyo.g4.reader_units/1:') and spec['schema'] == 'tukuyo.g4.fpl/1'
        for f in spec['facts']:
            assert f.get('known') or (f.get('span') and ''.join(f['span'].split()) in ''.join(text.split())), (text, f)
        bad = {**spec, 'facts': [dict(f) for f in spec['facts']]}
        bound = next(f for f in bad['facts'] if f.get('span') and '=' in f['eq'] and f['eq'].split('=')[1].strip().replace('.', '').isdigit())
        bound['eq'] = bound['eq'].split('=')[0] + '= 9999'                          # a number the text does not say
        assert not api.evaluate(bad, 'own')['ok']


def test_an_amount_set_aside_says_why():
    r = U.read_en('Leo is 8 years old. He has 3 bags of marbles with 12 marbles in each bag. How many marbles does he have?')
    assert [u['raw'] for u in r['spec']['unused']] == ['8'] and 'another thing' in r['spec']['unused'][0]['why']
    # never one of a span of time, one in the question, or one beside amounts of the asked thing
    assert units('Ken ran for 9 days. He has 3 bags with 12 marbles in each bag. How many marbles does he have?') is None
    assert units('The shop sells 5 pies every day for 9 days. Then it sells 4 more pies. How many pies does it sell in all?') == 49


def test_it_is_tried_after_the_readers_by_wording():
    # a reading the readers by wording make is theirs; the reader by units reads what they leave
    r = reader.read('Bakery boxes hold 6 rolls each. Mr. Ito packs 9 boxes. How many rolls does he pack?')
    assert r['spec']['reader'].startswith(('tukuyo.g4.reader_units/1:', 'tukuyo.g4.reader_en', 'tukuyo.g4.forms'))
    r = reader.read('Stamps come in sheets of 8. Ravi needs 56 stamps. How many sheets should he buy?')
    assert api.evaluate(r['spec'], 'own')['answer'] == 7


def test_no_rewrite_whose_answer_is_not_given_exactly_is_read():
    # the exactness probe's rewrites (did not, could have, almost, about, at least, or more; ませんでした、予定、ぐらい、…) of
    # every problem above the reader by units reads: none is read by any of the child's readers
    import exactness_probe as xp
    sets = {'en': [(t, None) for t, a in EN if a is not None], 'ja': [(t, None) for t, a in JA if a is not None]}
    p = xp.probe(sets=sets)
    assert p['rewrites']['en'] > 300 and p['rewrites']['ja'] > 100
    assert not p['readings'], p['readings'][:3]

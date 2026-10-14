"""round 10: the everyday English forms (forms_everyday_en), the Japanese forms of reader_ja_more, and the wrong answers
of the r9 readers found on the development sets. The examples are written for the tests; none is from a held-out set."""
from fractions import Fraction

import pytest

from tukuyo_g4 import reader, api


def own(text):
    r = reader.read(text)
    if not r.get('spec'):
        return None
    e = api.evaluate(r['spec'], 'own')
    return e['value'] if e['ok'] else None


EN = [
    ('Mila is 140 centimeters tall. Her uncle is 45 centimeters taller. How tall is her uncle?', '185'),
    ('A shed is 3 meters tall. A tree is 120 centimeters taller than the shed. How many centimeters tall is the tree?', '420'),
    ('Rex scored 52 points. Sam scored 9 points fewer than Rex. How many points did Sam score?', '43'),
    ('Ben is 10 years old. His aunt is 41 years old. How much older is his aunt?', '31'),
    ('There are 18 cats and 25 dogs at the shelter. How many fewer cats than dogs are there?', '7'),
    ('One crate contains 12 melons. How many melons are in 4 crates?', '48'),
    ('A bag weighs 3 kilograms. How many kilograms do 9 such bags weigh?', '27'),
    ('Each of 6 cars carries 4 people. How many people are carried in all?', '24'),
    ('Out of 30 cards, one third are blue. How many cards are blue?', '10'),
    ('A hall has 150 chairs. 98 people are seated. How many chairs are free?', '52'),
    ('Ana had 20 dollars. After buying a scarf, she had 8 dollars left. How much did the scarf cost?', '12'),
    ('Tom is 4 times as old as his niece. His niece is 9. How old is Tom?', '36'),
    ('Two numbers add up to 70. One of them is 26. What is the other number?', '44'),
    ('A rectangle is 8 meters long and 5 meters wide. What is its area in square meters?', '40'),
    ('A box holds 8 cups. How many boxes are needed for 30 cups?', '4'),
    ('The price of a lamp went up from 30 dollars to 41 dollars. By how many dollars did the price go up?', '11'),
    ('If he has 12 coins in each of his 5 jars, how many coins does he have in total?', '60'),
    ('Lina sold 14 cakes while Omar sold 17. How many cakes did they sell?', '31'),
    ('He needs 300 lbs. of rice. If he has 180 lbs. of rice stored in his shop, how much more rice does he need?', '120'),
    ('There are 5 boxes with 6 pens in each box and 4 loose pens. How many pens are there in total?', '34'),
]


@pytest.mark.parametrize('text,answer', EN)
def test_everyday_english_forms(text, answer):
    assert Fraction(own(text)) == Fraction(answer)


# (text, what may be answered: an empty set means nothing may be)
EN_TRAPS = [
    ('A library has 45 picture books and 38 storybooks. How many books are there altogether?', set()),         # r9: 45
    ('The price of a book went up from 15 dollars to 22 dollars. By how many dollars did the price go up?', {'7'}),  # r9: 37
    ('There are 5 boxes with 9 apples in each box and 7 loose apples. How many apples are there in total?', {'52'}),  # r9: 80
    ('There are 5 boxes with 9 apples and 7 pears in each box. How many fruits are there in total?', set()),   # r9: 44
    ('If he has 56 books in each of his 9 bookshelves, how many bookshelves does he have?', {'9'}),            # r9: 504
    ('Each booklet has 9 pages and there are 49 booklets in the section. How many booklets are there?', {'49'}),
    ('He needs 450 lbs. of sugar. If he has 287 lbs. of flour stored in his house, how much more sugar will he need?', set()),
    ('Tom had 5 apples. Ann had 9 apples. How many apples did Tom get?', set()),
    ('Chris obtained 42 newspapers and Lily got 23 more newspapers than Chris. How many newspapers did they collect?', {'107'}),
    ('Lucy sold 19 packs and Robyn sold 16. How many packs did Lucy sell?', {'19'}),
    ('Kevin is 152 centimeters tall. His father is 28 centimeters taller than his uncle. How tall is his father?', set()),
    ('A shop sold 125 toys on Saturday and 98 toys on Sunday. How many more toys did it sell on Sunday?', set()),
    ('Olivia has about 3 times as many books as Ethan. Olivia has 27 books. How many books does Ethan have?', set()),
    ('Henry spent 45 minutes on homework and over 30 minutes reading. How many minutes did he spend in all?', set()),
    ('She read 60 pages over 3 days. How many pages did she read each day?', {'20'}),
]


@pytest.mark.parametrize('text,ok', EN_TRAPS)
def test_english_traps(text, ok):
    v = own(text)
    assert v is None or v in ok, v


JA = [
    ('1箱にりんごが8個入っています。5箱では何個ですか。', '40'),
    ('500mLのジュースが6本あります。全部で何mLですか。', '3000'),
    ('ボールが6こずつ入ったふくろを4ふくろ買いました。友だちに3こあげました。ボールは何こありますか。', '21'),
    ('みなさんの身長は130cmです。お兄さんはみなさんより25cm高いです。お兄さんの身長は何cmですか。', '155'),
    ('はるとさんは切手を20まい持っていて、そうたさんより4まい多いです。そうたさんは何まい持っていますか。', '16'),
    ('かなさんは3000円持っています。弟はかなさんより800円少なく持っています。2人あわせて何円持っていますか。', '5200'),
    ('お店は月曜日にパンを80こ、火曜日に65こ売りました。月曜日は火曜日より何こ多く売りましたか。', '15'),
    ('ゆいさんは妹より3才年上です。妹は6才です。ゆいさんは2年後に何才になりますか。', '11'),
    ('120ページの本のうち45ページ読みました。残りは何ページですか。', '75'),
    ('3000円の1/3を使いました。使ったのは何円ですか。', '1000'),
    ('ねこが12ひきいて、犬はねこの2倍います。犬は何ひきいますか。', '24'),
    ('えんぴつ72本を8人に同じ数ずつ分けます。1人何本もらえますか。', '9'),
    ('チケットは1まい500円です。3500円では何まい買えますか。', '7'),
    ('2つの数をたすと40になります。1つは15です。もう1つの数はいくつですか。', '25'),
    ('本のねだんが800円から1100円に上がりました。何円上がりましたか。', '300'),
    ('1箱にかんが8こ入ります。かん20こを入れるには何箱いりますか。', '3'),
    ('3kgのお米は何gですか。', '3000'),
    ('1辺が5cmの正方形のまわりの長さは何cmですか。', '20'),
]


@pytest.mark.parametrize('text,answer', JA)
def test_more_japanese_forms(text, answer):
    assert own(text) == answer


JA_TRAPS = [
    ('1袋にみかんが9個入っています。6箱では何個ですか。', set()),
    ('健太さんの身長は152cmです。お父さんはおじさんより28cm高いです。お父さんの身長は何cmですか。', set()),
    ('お店は土曜日におもちゃを125こ、日曜日に98こ売りました。月曜日は日曜日より何こ多く売りましたか。', set()),
    ('クッキーを32枚焼き、そのうち19枚を売りました。売ったのは何枚ですか。', {'19'}),
    ('チケットは1まい700円です。4000円では何まい買えますか。', set()),
    ('本のねだんが1500円から2200円に下がりました。何円下がりましたか。', set()),
    ('映画は11時に始まり、3時間続きました。映画は何時に終わりましたか。', set()),
    ('びんにあめが50こ入っています。そのうち20%が赤いあめです。赤くないあめは何こですか。', {'40'}),
    ('ゆかさんは赤い花を18本、黄色い花を27こ持っています。15本あげました。花は何本のこっていますか。', set()),
    ('いちごが27こありました。8こもらいました。いちごはいくつのこっていますか。', set()),
]


@pytest.mark.parametrize('text,ok', JA_TRAPS)
def test_japanese_traps(text, ok):
    v = own(text)
    assert v is None or v in ok, v


# Found on round 10's held-out set after its one measurement (these four wrong answers were there in r9 too). The fixes
# hold readings back only; on the development sets nothing they read before changed. The texts are the held-out
# set's own: it was spent by that measurement and is development material from here on.
AFTER_HELD_OUT_WRONG = [
    'Kyle put 4 more pencils into his pencil case. How many pencils are in the case now?',     # no start: was 4
    'ハイキングコースは全長12kmです。あやさんは5km歩きました。ゴールまであと何kmですか。',          # 歩きました: was 17
    'ふでばこにえんぴつを4本足しました。ふでばこのえんぴつは何本になりましたか。',                    # no start (the core): was 4
    'にんじんを1列に11本ずつ7列植えました。うさぎが9本食べました。にんじんは何本のこっていますか。',  # eaten as the start: was 86
]
STILL_READ = [
    ('Beth has 4 packs of crayons. Each pack has 10 crayons in it. She also has 6 extra crayons. How many crayons does Beth have altogether?', '46'),
    ('Ann has 5 apples. Tom has 4 more apples than Ann. How many apples does Tom have?', '9'),
    ('すずめが5羽いました。3羽とんできました。すずめは何羽になりましたか。', '8'),
    ('友だちが3人いました。あとから2人きました。みんなで何人ですか。', '5'),
    ('はじめに9本ありました。毎日11本ずつ7日植えました。今何本ありますか。', '86'),
    ('12cmの草が、1週間に3cmずつ4週間のびました。草は今何cmですか。', '24'),
    ('りんごを5こ買いました。3こ食べました。のこりは何こですか。', '2'),
]


@pytest.mark.parametrize('text', AFTER_HELD_OUT_WRONG)
def test_the_wrong_answers_found_on_the_held_out_set_are_held_back(text):
    assert api.solve(text, llm='off').get('answer') is None


@pytest.mark.parametrize('text,answer', STILL_READ)
def test_what_is_near_them_is_still_read(text, answer):
    assert api.solve(text, llm='off').get('answer') == answer


def test_no_route_answers_what_is_now_after_what_was_only_wished_or_heard(tmp_path):
    # end to end, the v1022 core included: the exactness probe over all three dev sets found the core answering these
    # (25, 58, 13, 59). A plan stays the core's (10 are left), and so does the price of a wished act (r9)
    from test_v1022_5_fusion import run
    d = tmp_path / 'd'; run(d, 'init', '--individual-id', 'NOT-SAID-DONE')
    for q in ('水そうに水が40L入っています。15L使いたいです。水は何Lのこっていますか。',
              '電車に64人乗っていました。最初の駅で15人降りて、9人乗りたいです。今、何人乗っていますか。',
              '池にアヒルが16羽いたいです。4羽来て、そのあと7羽飛んでいきました。今、何羽いますか。',
              'おばあさんは68才あまり、ルーシーさんは9才です。年れいの差は何才ですか。',
              '自転車で時速15kmで2時間走りたそうです。何km走りましたか。'):
        assert run(d, 'g4-solve', '--llm', 'off', '--', q)['answer'] is None, q
    assert run(d, 'g4-solve', '--llm', 'off', '--', 'りんごが10個あります。明日3個食べる予定です。残りは何個？')['answer'] == '10'
    assert run(d, 'g4-solve', '--llm', 'off', '--', '1本80円のえんぴつを3本買いたいです。代金は何円ですか。')['answer'] == '240'
    assert run(d, 'g4-solve', '--llm', 'off', '--', '池にアヒルが16羽いました。4羽来て、そのあと7羽飛んでいきました。今、何羽いますか。')['answer'] == '13'

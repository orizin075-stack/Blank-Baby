"""v1022.8.0: the Japanese reader (reader_ja), English story forms (forms_story_en), and the wrong answers found on the
new private problems. The examples here are written for the tests; none is from the frozen held-out set."""
from fractions import Fraction

import pytest

from tukuyo_g4 import api, reader, reader_ja


def own(text):
    r = reader.read(text)
    if not r.get('spec'):
        return None
    e = api.evaluate(r['spec'], 'own')
    return e['value'] if e['ok'] else None


JA = [
    ('いちごが15こあります。4こ食べました。のこりは何こですか。', '11'),
    ('青い花が6本、赤い花が8本あります。花は全部で何本ですか。', '14'),
    ('兄はカードを20まい持っています。弟は兄より7まい少なく持っています。弟は何まい持っていますか。', '13'),
    ('1はこにボールが4こずつ入っています。6はこでは、ボールは何こですか。', '24'),
    ('40まいの色紙を5人で同じ数ずつ分けます。1人何まいになりますか。', '8'),
    ('1本90円のペンを4本買いました。代金は何円ですか。', '360'),
    ('800円持っています。250円のノートを買いました。のこりは何円ですか。', '550'),
    ('時速50kmで2時間走ると、何km進みますか。', '100'),
    ('5mは何cmですか。', '500'),
    ('28人のうち、半分が女の子です。女の子は何人ですか。', '14'),
    ('りなさんは10才です。お姉さんはりなさんより3才年上です。お姉さんは何才ですか。', '13'),
    ('はとが30羽いました。9羽とんでいき、そのあと4羽もどってきました。今、何羽いますか。', '25'),
    ('シールを何まいか持っていました。3まいあげたので、のこりが8まいになりました。はじめに何まい持っていましたか。', '11'),
    ('毎日3ページずつ6日間読みました。全部で何ページ読みましたか。', '18'),
    ('1こ200円のパンを3こ買って、1000円さつではらいました。おつりは何円ですか。', '400'),
    ('36人のうち、20人が自転車で通っています。自転車で通っていない人は何人ですか。', '16'),
    ('車で240kmを4時間で走りました。時速何kmですか。', '60'),
    ('1日に8ページずつ読むと、64ページの本を読み終えるのに何日かかりますか。', '8'),
]
JA_HOLD = [
    'いくつかのりんごがあります。2こ食べました。のこりは何こですか。',                 # how many there were is not told
    'みかんが20こあります。8こ食べました。りんごは何こありますか。',                     # asked about another fruit
    'クラスに男の子が14人います。クラスは全部で何人ですか。',                             # one part of the whole
    '赤い花が8本あります。花は全部で何本ですか。',
    'バスで行けば6日、車ならその半分の日数です。行きはバス、帰りは車だと何日かかりますか。',  # half of one leg, not the whole
    '24枚のカードを5人で同じ数ずつ分けると1人何枚？',                                     # cards are whole (it said 4.8)
    '1日に20ページずつ読むと、150ページの本を読み終えるのに何日かかりますか。',              # 7.5 days to finish is 8
    # what the story does not say happened, or says only roughly (the full suite: it read these before)
    '時速5kmで4時間歩きません。何km進む？',
    'りんごが10個あります。3個食べていません。残りは何個？',
    'りんごが10個あります。3個食べなかった。残りは何個？',
    'りんごが10個あります。明日3個食べる予定です。残りは何個？',
    '800円の商品を25%値引きする予定です。価格は何円？',
    '30本のペンを5人で分けました。1人何本ですか？',                                         # not said to be equal
    'りんごが10個あります。3個ぐらい食べました。残りは何個？',
    'みかんが約20こあります。8こ食べました。のこりは何こですか。',
    'りんごが10個あります。3個食べなかったら、残りは何個？',
    'はとが30羽いました。9羽とんでいき、そのあと4羽もどってきました。今、何羽いませんか。',
    # found by rewriting the dev problems (tools/exactness_probe.py)
    '40Lくらいの水が入るおけに、その半分の水が入っています。水は何L入っていますか。',
    'あめが50こあまりあります。12こ食べました。のこりは何こですか。',
    'カードが20まい近くあります。6まい使いました。のこりは何まいですか。',
    'まさとさんはシールを25まいより多く持っています。妹はまさとさんより5まい少なく持っています。妹は何まい持っていますか。',
    'りんごが10こありました。3こ食べたそうです。のこりは何こですか。',
    'りんごが10こありました。3こ食べたはずです。のこりは何こですか。',
    'りんごが10こありました。もう少しで3こ食べるところでした。のこりは何こですか。',
    'パーティーに子どもが25人来たいです。そのうち13人が女の子です。男の子は何人ですか。',
]
JA_EXACT = [   # the same without the words: read
    ('40Lの水が入るおけに、その半分の水が入っています。水は何L入っていますか。', '20'),
    ('あめが50こあります。12こ食べました。のこりは何こですか。', '38'),
    ('まさとさんはシールを25まい持っています。妹はまさとさんより5まい少なく持っています。妹は何まい持っていますか。', '20'),
    ('パーティーに子どもが25人来ました。そのうち13人が女の子です。男の子は何人ですか。', '12'),
]


@pytest.mark.parametrize('text,answer', JA)
def test_the_japanese_reader_reads_everyday_forms(text, answer):
    assert own(text) == answer


@pytest.mark.parametrize('text', JA_HOLD)
def test_the_japanese_reader_does_not_guess(text):
    assert own(text) is None


@pytest.mark.parametrize('text,answer', JA_EXACT)
def test_the_japanese_reader_reads_the_exact_twins(text, answer):
    assert own(text) == answer


def test_its_japanese_readings_are_checked_like_any_other():
    spec = reader_ja.read('1本90円のペンを4本買いました。代金は何円ですか。')['spec']
    assert spec['reader'].startswith('tukuyo.g4.reader_ja/1:') and spec['lang'] == 'ja'
    bad = dict(spec, facts=[dict(f) for f in spec['facts']])
    bad['facts'][0]['eq'] = bad['facts'][0]['eq'].replace('90', '95')          # a number the text does not say
    assert not api.evaluate(bad, 'own')['ok']


EN = [
    ('Ava has 5 boxes of pencils with 6 pencils in each box. She gives away 7 pencils. How many pencils are left?', '23'),
    ('A train has 60 seats. 41 seats are taken. How many seats are empty?', '19'),
    ('A tart is cut into 12 slices. Kim eats 2 slices and Lou eats 3 slices. How many slices are left?', '7'),
    ('Raj walked 4 kilometers every day for 6 days. How many kilometers did he walk?', '24'),
    ('A pack of 4 muffins costs 6 dollars. How much does one muffin cost?', '1.5'),
    ('Mia is 9 years old. How old will she be in 4 years?', '13'),
    ('A tray has 30 cups. A third of them are blue. How many blue cups are there?', '10'),
    ('Sid had 8 stickers. He got some more and now has 15 stickers. How many stickers did he get?', '7'),
    ('Ken drove 180 kilometers in 3 hours. What was his average speed in kilometers per hour?', '60'),
    ('Joy bought 2 hats at 7 dollars each and 3 scarves at 4 dollars each. How much did she spend?', '26'),
    ('There are 6 red balls and 9 blue balls in a box. How many balls are in the box?', '15'),
]
EN_HOLD = [
    'A class has 14 boys and some girls. How many students are in the class?',      # answered 14 before
    'A train has 60 seats. Some seats are taken. How many seats are empty?',
    'Raj walked 4 kilometers every day for 6 weeks. How many kilometers did he walk?',
    'Sid had 8 stickers. He got some more and now has 15 stones. How many stickers did he get?',
    'A jar has 40 marbles. A third of them are blue. How many blue marbles are there?',          # marbles are whole
    # amounts not said exactly, and a statement that something is not so
    'Ava has about 5 boxes of pencils with 6 pencils in each box. She gives away 7 pencils. How many pencils are left?',
    'Raj walked at least 4 kilometers every day for 6 days. How many kilometers did he walk?',
    'Sid had more than 8 stickers. He got some more and now has 15 stickers. How many stickers did he get?',
    'A tray has nearly 30 cups. A third of them are blue. How many blue cups are there?',
    'A train never has 60 seats. 41 seats are taken. How many seats are empty?',
    'Liam saved 5 dollars every week for over 6 weeks. How much did he save?',
    'Kim has maybe 12 shells. She gives 4 shells away. How many shells are left?',
    'Ben read 3 or more books each month for 4 months. How many books did he read?',
    'A recipe needs 2 cups of flour for one cake. How many cups are not needed for 5 cakes?',
    'Maya could have had 14 stickers. She gave 5 stickers to her brother. How many stickers does Maya have left?',
    'Nora had 20 beads. She almost lost 6 beads. How many beads does she have now?',
    'A class has 40 students. Nearly half of them walk to school. How many students walk to school?',
    'Lily never had some candies. She gave 6 candies to her friend and now has 9 candies. How many candies did Lily have at first?',
    'Each ticket should have cost 8 dollars. How many tickets can you buy with 56 dollars?',
]
EN_EXACT = [   # 'more than' and 'less than' that are exact, and a question about what is not so
    ('Nina has 12 dollars. Omar has 5 dollars more than Nina. How much money do they have together?', '29'),
    ('12 less than five times a number is 48. What is the number?', '12'),
    ('When 6 is added to 4 more than a number, the result is 30. What is the number?', '20'),
    ('A club has 90 members. 35 of them play chess. How many members do not play chess?', '55'),
    ('She read 60 pages over 3 days. How many pages did she read each day?', '20'),                 # over 3 days: a span
    ('Liam saved 5 dollars every week for 6 weeks. How much did he save?', '30'),
    ('Nora had 20 beads. She lost 6 beads. How many beads does she have now?', '14'),
    ('A class has 40 students. Half of them walk to school. How many students walk to school?', '20'),
    ('A recipe needs 2 cups of flour for one cake. How many cups are needed for 5 cakes?', '10'),
]


@pytest.mark.parametrize('text,answer', EN)
def test_english_story_forms(text, answer):
    assert Fraction(own(text)) == Fraction(answer)


@pytest.mark.parametrize('text', EN_HOLD)
def test_english_story_forms_do_not_guess(text):
    assert own(text) is None


@pytest.mark.parametrize('text,answer', EN_EXACT)
def test_exact_comparisons_are_still_read(text, answer):
    assert Fraction(own(text)) == Fraction(answer)


def test_the_core_does_not_answer_a_whole_from_one_part(tmp_path):
    from test_v1022_5_fusion import run
    d = tmp_path / 'd'; run(d, 'init', '--individual-id', 'PART-WHOLE')
    from tukuyo_v1022 import cognition
    r = cognition.solve(str(d), 'クラスに男の子が14人います。クラスは全部で何人ですか。')
    assert r.get('uncertain') or r.get('answer') is None


def test_the_held_out_set_is_as_it_was_frozen():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
    import private_eval as pe
    assert pe.fingerprint(pe.HELD_OUT) == pe.HELD_OUT_SHA256
    assert pe.value('16+(16+9)') == 41 and pe.value('50*2/5') == 20
    assert pe.grade(None, None) == 'right' and pe.grade('3', None) == 'wrong' and pe.grade(None, '3') == 'held'
    assert pe.mcnemar(22, 1) < 0.001 and pe.mcnemar(0, 0) == 1.0


def test_no_rewrite_of_a_dev_problem_that_leaves_its_answer_open_is_read():
    # every problem of the private dev set the reader reads, rewritten one place at a time so that its answer is no
    # longer given exactly (did not, could have, almost, about, at least, or more; ませんでした、予定、たそうです、ぐらい、
    # あまり、近く): none is read. Before (2026-10-14) 1,113 of 1,636 in Japanese and 951 of 2,582 in English were
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
    import exactness_probe
    r = exactness_probe.probe()
    assert r['problems_read']['en'] > 50 and r['problems_read']['ja'] > 50 and r['rewrites']['en'] > 2000
    assert r['ok'], r['readings'][:5]


def test_no_route_answers_an_amount_said_only_roughly(tmp_path):
    # end to end (think, g4-solve), the v1022 core included: it answered these (exactness_probe.py --end-to-end)
    from test_v1022_5_fusion import run
    d = tmp_path / 'd'; run(d, 'init', '--individual-id', 'ROUGH')
    for q in ('1本80円あまりのえんぴつを3本買いました。代金は何円ですか。',
              '車で150km近くを3時間で走りました。時速何kmですか。',
              '毎週500円より多くずつ6週間ちょ金しました。全部で何円ちょ金しましたか。',
              '毎週500円ずつ6週間ちょ金したいです。全部で何円ちょ金しましたか。'):      # a wish, and what was done is asked
        assert run(d, 'think', q)['answer'] is None, q
        assert run(d, 'g4-solve', '--llm', 'off', '--', q)['answer'] is None, q
    # without the words: answered; and what the core reads of an event not done stays (10 apples are left)
    assert run(d, 'think', '1本80円のえんぴつを3本買いました。代金は何円ですか。')['answer'] == '240'
    assert run(d, 'think', 'りんごが10個あります。明日3個食べる予定です。残りは何個？')['answer'] == '10'

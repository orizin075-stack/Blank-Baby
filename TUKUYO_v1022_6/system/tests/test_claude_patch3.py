"""claude-patch3 regression tests (on top of v1022.5 fusion): exact quantity/time questions, equations and
more word-problem schemas, multi-hop memory with strict question tails, logic upgrades, the deliberation
number-coverage guard, and facts taught in chat."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'

def run(d,*a,ok=True,stdin=None,raw=False):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for k in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS'):env.pop(k,None)
    cmd=[sys.executable,'-B',str(CLI)];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    p=subprocess.run(cmd+['--data',str(d),*map(str,a)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=240,input=stdin)
    if raw:return p
    r=json.loads(p.stdout)
    if ok:assert p.returncode==0 and r.get('ok'),(a,r,p.stderr[-400:])
    return r
def think(d,q):return run(d,'think','--',q)

def test_cp3_quantities_time_calendar_percent():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP3-A')
        good={'4.2kmは何m？':'4200','3時間20分は何分？':'200','150分は何時間何分？':'2時間30分','How many grams are in 2 kilograms?':'2000',
              '午後1時50分から1時間25分後は何時何分？':'午後3時15分','今日は金曜日です。4日後は何曜日？':'火曜日','2024年2月28日の2日後は何月何日？':'3月1日',
              '2000年1月1日は何曜日？':'土曜日','6000円の3割引きはいくら？':'4200','2500円の20%は？':'500','2ダースは何個？':'24'}
        for q,a in good.items():
            r=think(d,q);assert r['answer']==a and not r['uncertain'] and r.get('explanation'),(q,r)
        for q in ['1年は何日？','5kgは何m？','午後11時30分から45分後は何時何分？']:assert think(d,q)['answer'] is None,q

def test_cp3_equations_and_new_word_schemas():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP3-B')
        good={'ある数に9を足すと30になります。ある数は？':'21','ある数を5倍して2を引くと43になる。ある数はいくつ？':'9',
              '1日に8ページずつ読むと、120ページの本は何日で読み終わる？':'15','毎週300円ずつ貯めると、5週間で何円になる？':'1500',
              '48枚のカードを1人6枚ずつ配ると、何人に配れる？':'8','クラスに子どもが30人います。そのうち女子は14人です。男子は何人？':'16',
              'りんごが13個、みかんが21個あります。みかんはりんごより何個多い？':'8','1個70円のあめと1本130円のジュースをそれぞれ3つずつ買うと全部でいくら？':'600',
              '1000円で、1本180円のペンを4本買いました。おつりはいくら？':'280','弟は切手を15枚持っています。兄は弟より9枚多く持っています。兄は何枚持っていますか？':'24',
              '3mのリボンから120cm切り取りました。残りは何cm？':'180','Mike has 4 times as many cards as Joe. Joe has 6 cards. How many cards does Mike have?':'24',
              'An apple costs 3 dollars and a pear costs 4 dollars. How much do 2 apples and 5 pears cost?':'26',
              'There were 30 kids in the park. 12 kids left. Then 5 more kids came. How many kids are in the park now?':'23'}
        for q,a in good.items():
            r=think(d,q);assert r['answer']==a and not r['uncertain'],(q,r)
        for q in ['ある数に何かを足すと20になります。ある数は？','49枚のカードを1人6枚ずつ配ると、何人に配れる？','クラスに子どもが何人かいます。そのうち女子は14人です。男子は何人？',
                  '1000円で、1本180円のペンを4本買って、50円拾いました。おつりはいくら？']:
            assert think(d,q)['answer'] is None,q

def test_cp3_multi_hop_memory_and_strict_tail():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP3-C')
        for f in ['青空美術館の館長は堀田ユキである。','堀田ユキの出身地は松本である。','青空美術館の最寄り駅は北口駅である。','北口駅は1931年に開業した。','青空美術館の休館日は月曜日である。',
                  'Doctor Mara founded the village of Tillby.','The village of Tillby has a population of 900.']:run(d,'knowledge-add',f)
        assert think(d,'青空美術館の館長の出身地は？')['answer']=='松本'
        r=think(d,'青空美術館の最寄り駅はいつ開業した？');assert r['answer']=='1931年',r            # patch2 answered 北口駅 here
        assert think(d,'青空美術館のトップは？')['answer']=='堀田ユキ'
        assert think(d,'青空美術館の休みは何曜日？')['answer']=='火曜日'.replace('火','月')
        assert '900' in think(d,'What is the population of the village founded by Doctor Mara?')['answer']
        r=think(d,'青空美術館の入館料は？');assert r['answer'] is None and r['reason']=='MEMORY_ATTRIBUTE_MISSING' and '館長' in r['explanation']
        r=run(d,'llm-ask','青空美術館の入館料は？');assert r['status']=='abstained' and '館長' in r['answer']
        assert think(d,'青空美術館の館長の電話番号は？')['answer'] is None
        assert run(d,'whole-audit')['ok']

def test_cp3_logic_upgrades():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP3-D')
        assert think(d,'ボタンを押すとベルが鳴る。ベルが鳴っていない。ボタンを押した？')['answer'].startswith('いいえ')
        assert think(d,'赤か青のどちらかを選んだ。赤は選んでいない。青を選んだ？')['answer'].startswith('はい')
        assert think(d,'花子は春子より年下だ。春子は夏子より年下だ。一番年上は誰？')['answer']=='一番年上なのは夏子です。'
        assert think(d,'If Mia is tired, she sleeps. Mia is tired. Does Mia sleep?')['answer'].startswith('Yes')
        assert think(d,'No cats can bark. Kiki is a cat. Can Kiki bark?')['answer'].startswith('No')
        assert think(d,'Either Lee or Max called. Max did not call. Did Lee call?')['answer'].startswith('Yes')
        assert think(d,'Ben is taller than Sam. Sam is taller than Tim. Who is shortest?')['answer']=='Tim.'
        assert think(d,'If Mia or Ann is tired, she sleeps. Mia is tired. Does Ann sleep?')['answer'] is None     # ambiguous pronoun
        assert think(d,'雨が降ると道が濡れることが多い。雨が降った。道は濡れた？')['answer'] is None

def test_cp3_chat_teaching_and_deliberation_coverage():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP3-E')
        p=run(d,'chat',raw=True,stdin='覚えて：星野商店の定休日は木曜日である。\n星野商店の休みは何曜日？\n/exit\n')
        assert '覚えました' in p.stdout and '木曜日' in p.stdout,p.stdout[-600:]
        assert think(d,'星野商店の定休日は？')['answer']=='木曜日'
        r=think(d,'2000円で、1個450円のケーキを3個買いました。おつりはいくら？');assert r['answer']=='650',r     # v1022.5 said 1350
        assert run(d,'whole-audit')['ok']

"""claude-patch2 regression tests: word problems, complete-model logic, own-knowledge QA, explanations,
multi-teacher consensus, tool loop and self-study. LLMs are the deterministic stand-in (plumbing only)."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py';MOCK=ROOT/'tools'/'mock_llm_provider.py'

def run(d,*a,mode=None,ok=True,state=None,env_extra=None):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for k in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS','TUKUYO_LLM_MIN_TEACHERS'):env.pop(k,None)
    if mode:env.update({'TUKUYO_LLM_COMMAND':f'{sys.executable} -B {MOCK}','MOCK_LLM_MODE':mode,'MOCK_LLM_STATE':str(state or Path(d).parent/'mock_state')})
    env.update(env_extra or {})
    cmd=[sys.executable,'-B',str(CLI)];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    p=subprocess.run(cmd+['--data',str(d),*map(str,a)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=240);r=json.loads(p.stdout)
    if ok:assert p.returncode==0 and r.get('ok'),(a,r,p.stderr[-400:])
    return r

def think(d,q):return run(d,'think','--',q)

def test_cp2_word_problems_with_coverage_and_explanations():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP2-A')
        good={'バスに12人乗っていて、5人降りて7人乗った。今何人？':'14','1冊120円のノートを3冊買うと全部でいくら？':'360','5人に4個ずつ配ると、全部で何個いる？':'20',
              '24枚のカードを6人で同じ数ずつ分けると1人何枚？':'4','兄は15歳で、弟は兄より3歳年下です。弟は何歳？':'12','分速80mで15分歩くと何m進む？':'1200',
              '水が2リットルあって、500ミリリットル飲んだ。残りは何ミリリットル？':'1500','500円持っていて、120円のパンを買った。おつりは？':'380',
              'Tom had 9 apples and ate 2. How many are left?':'7'}
        for q,a in good.items():
            r=think(d,q);assert r['answer']==a and not r['uncertain'] and r.get('explanation'),(q,r)
        for q in ['バスに12人乗っていて、5人降りた。運転手は3人いる。今何人？',   # distractor number -> coverage refuses
                  'カードが20枚あって、6枚なくした。残りは何枚？',                 # context-dependent verb -> teacher domain
                  'りんごが10個あります。3個ぐらい食べました。残りは何個？','24枚のカードを5人で同じ数ずつ分けると1人何枚？']:
            assert think(d,q)['answer'] is None,q
        assert run(d,'whole-audit')['ok']

def test_cp2_logic_complete_models():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP2-B')
        r=think(d,'晴れなら遠足に行く。遠足に行かなかった。晴れだった？');assert r['answer'].startswith('いいえ') and not r['uncertain']
        r=think(d,'雨なら試合は中止だ。今日は雨ではない。試合は中止？');assert r['answer'] is None and r['reason']=='UNDETERMINED_BY_PREMISES' and '決められません' in r['explanation']
        r=run(d,'llm-ask','雨なら試合は中止だ。今日は雨ではない。試合は中止？');assert r['source']=='local-proof' and r['determinate'] is False and '決められません' in r['answer']
        assert think(d,'AはBより重い。BはCより重い。AとCではどちらが重い？')['answer'].startswith('A')
        assert think(d,'AはBより重い。CはBより重い。AとCではどちらが重い？')['answer'] is None
        assert think(d,'AはBより重い。BはAより重い。どちらが重い？')['reason']=='PREMISES_CONTRADICT'
        assert think(d,'If it snows, the school closes. The school does not close. Does it snow?')['answer'].startswith('No')
        for q in ['雨なら試合は中止だ。雨が降るかもしれない。試合は中止？','雨のときだけ試合は中止だ。雨だ。試合は中止？']:
            assert think(d,q)['answer'] is None,q

def test_cp2_own_knowledge_answers_and_conflicts():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP2-C')
        for f in ['緑ヶ丘病院の院長は村井ケイである。','緑ヶ丘病院の所在地は北区である。','七色川の全長は88キロメートルである。','A社の社長は山本である。','A社の社長は川口である。']:run(d,'knowledge-add',f)
        assert think(d,'緑ヶ丘病院の院長は？')['answer']=='村井ケイ'
        assert think(d,'緑ヶ丘病院はどこにある？')['answer']=='北区'
        assert think(d,'七色川の長さは？')['answer']=='88キロメートル'
        assert think(d,'A社の社長は？')['answer'] is None                  # conflicting memories -> abstain
        assert think(d,'青葉病院の院長は？')['answer'] is None              # other entity -> abstain
        assert think(d,'緑ヶ丘病院の副院長は？')['answer'] is None          # other attribute -> abstain

def test_cp2_multi_teacher_consensus():
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);d=td/'d';run(d,'init','--individual-id','CP2-D')
        q=['1箱に12個入りが5箱あります。7個販売しました。残りは何個？','1箱に12個入りが5箱あります。7個仕入れました。残りは何個？'];(td/'q.json').write_text(json.dumps({'questions':q},ensure_ascii=False),encoding='utf-8')
        mk=lambda m:{'provider':'command','command':f'{sys.executable} -B {MOCK} --mode={m}'}
        r=run(d,'llm-teach',td/'q.json',env_extra={'TUKUYO_LLM_TEACHERS':json.dumps([mk('honest'),mk('liar')])})
        assert r['summary']['learned']==0 and all(x.get('reason')=='TEACHERS_DISAGREE' for x in r['rows']),r
        r=run(d,'llm-teach',td/'q.json',env_extra={'TUKUYO_LLM_TEACHERS':json.dumps([{**mk('honest'),'model':'standin-a'},{**mk('honest'),'model':'standin-b'}]),'TUKUYO_LLM_MIN_TEACHERS':'2'})
        assert r['summary']['learned']==2 and r['teacher'].startswith('consensus:')
        assert think(d,'1箱に9個入りが4箱あります。5個販売しました。残りは何個？')['answer']=='31'
        r=run(d,'llm-teach',td/'q.json',ok=False,env_extra={'TUKUYO_LLM_TEACHERS':json.dumps([mk('honest')]),'TUKUYO_LLM_MIN_TEACHERS':'2'});assert not r.get('ok')

def test_cp2_tool_loop_and_self_study():
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);d=td/'d';run(d,'init','--individual-id','CP2-E')
        r=run(d,'llm-ask','--no-local-first','バスに12人乗っていて、5人降りて7人乗った。今何人？',mode='tools')
        assert r['status']=='verified' and r['answer'].startswith('14') and any(t['tool']=='solve' for t in r['tools'])
        q='1箱に10個入りが3箱あります。4個出荷しました。残りは何個？'
        assert run(d,'llm-ask',q)['status']=='abstained'                     # no LLM: logged with the local reason
        s=run(d,'self-study','--dry-run');assert [c['question'] for c in s['candidates']]==[q]
        s=run(d,'self-study',mode='honest',state=td/'s');assert s['now_solved_locally']==1 and s['teach']['summary']['learned']==1
        assert think(d,'1箱に7個入りが6箱あります。2個出荷しました。残りは何個？')['answer']=='40'
        assert run(d,'llm-audit')['ok'] and run(d,'whole-audit')['ok']

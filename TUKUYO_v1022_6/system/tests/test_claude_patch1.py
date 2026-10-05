"""claude-patch1 regression tests. The LLM is a deterministic stand-in (tools/mock_llm_provider.py);
these tests check plumbing, claim checks and the teacher's guards, not model quality."""
import json,os,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py';MOCK=ROOT/'tools'/'mock_llm_provider.py'

def run(d,*a,mode=None,ok=True,state=None):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'};env.pop('TUKUYO_LLM_PROVIDER',None);env.pop('TUKUYO_LLM_COMMAND',None)
    if mode:env.update({'TUKUYO_LLM_COMMAND':f'{sys.executable} -B {MOCK}','MOCK_LLM_MODE':mode,'MOCK_LLM_STATE':str(state or Path(d).parent/'mock_state')})
    cmd=[sys.executable,'-B',str(CLI)];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    p=subprocess.run(cmd+['--data',str(d),*map(str,a)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=240);r=json.loads(p.stdout)
    if ok:assert p.returncode==0 and r.get('ok'),(a,r,p.stderr[-400:])
    return r

def test_cp1_no_provider_abstains_and_local_proof_first():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP1-A')
        assert run(d,'llm-status')['llm']['provider'] is None
        r=run(d,'llm-ask','光の速さは？');assert r['status']=='abstained' and r['uncertain']
        r=run(d,'llm-ask','12*(5+4)',mode='honest');assert r['source']=='local-proof' and r['answer']=='108' and not r['uncertain']
        for q,a in [('50から13を引くと？','37'),('4の3倍は？','12'),('三十たす五は？','35'),('What is 12 plus 30?','42')]:
            r=run(d,'llm-ask',q);assert r['source']=='local-proof' and r['answer']==a,(q,r)
        assert run(d,'think','3個と4個を足すと？')['answer'] is None

def test_cp1_claims_are_checked_and_failures_withheld():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP1-B');run(d,'knowledge-add','星野村の人口は1240人である。')
        # worded arithmetic is now proven by the local core first; force the LLM path to test claim checks
        r=run(d,'llm-ask','12かける9足す3は？',mode='honest');assert r['source']=='local-proof' and r['answer']=='111'
        r=run(d,'llm-ask','--no-local-first','12かける9足す3は？',mode='honest');assert r['source']=='llm' and r['status']=='verified' and r['answer'].startswith('111')
        r=run(d,'llm-ask','星野村の人口は？',mode='honest');assert r['source']=='local-proof' and r['answer']=='1240人'   # patch2: own knowledge store first
        r=run(d,'llm-ask','--no-local-first','星野村の人口は？',mode='honest');assert r['status']=='verified' and '1240' in r['answer']
        r=run(d,'llm-ask','光の速さは？',mode='honest');assert r['status']=='unverified' and r['uncertain'] and r['confidence']<=.6
        r=run(d,'llm-ask','--no-local-first','12かける9足す3は？',mode='wrong_calc');assert r['status']=='rejected' and '111' not in r['answer'] and '112' not in r['answer'] and len(r['attempts'])==2
        r=run(d,'llm-ask','--no-local-first','星野村の人口は？',mode='fake_memory');assert r['status']=='rejected'
        a=run(d,'llm-audit');assert a['ok'] and a['answers']==7
        assert run(d,'whole-audit')['ok']

def test_cp1_answer_log_is_tamper_evident():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP1-C');run(d,'llm-ask','光の速さは？',mode='honest');run(d,'llm-ask','12かける9足す3は？',mode='honest')
        p=d/'v1022_llm'/'ANSWERS.jsonl';lines=p.read_text(encoding='utf-8').splitlines();e=json.loads(lines[0]);e['answer']='改ざん';lines[0]=json.dumps(e,ensure_ascii=False,sort_keys=True,separators=(',',':'))
        p.write_text('\n'.join(lines)+'\n',encoding='utf-8');assert not run(d,'llm-audit',ok=False)['ok']

def test_cp1_teacher_guards_and_offline_transfer():
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);d=td/'d';run(d,'init','--individual-id','CP1-D')
        q=['1箱に12個入りが5箱あります。7個販売しました。残りは何個？','1箱に12個入りが5箱あります。7個仕入れました。残りは何個？']
        (td/'q.json').write_text(json.dumps({'questions':q},ensure_ascii=False),encoding='utf-8')
        r=run(d,'llm-teach',td/'q.json',mode='inconsistent',state=td/'s1');assert r['summary']['learned']==0 and r['summary']['rejected']==2
        assert run(d,'think','1箱に9個入りが4箱あります。5個販売しました。残りは何個？')['answer'] is None
        r=run(d,'llm-teach',td/'q.json',mode='honest',state=td/'s2');assert r['summary']['learned']==2
        # The local core now answers NEW numbers with no LLM configured at all.
        assert run(d,'think','1箱に9個入りが4箱あります。5個販売しました。残りは何個？')['answer']=='31'
        assert run(d,'think','1箱に9個入りが4箱あります。5個仕入れました。残りは何個？')['answer']=='41'
        assert run(d,'think','1箱に9個入りが4箱あります。5個譲りました。残りは何個？')['answer'] is None
        assert run(d,'learning-audit')['ok'] and run(d,'whole-audit')['ok']

def test_cp1_seed_alias_no_longer_masks_rule_and_box_count():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP1-E')
        assert run(d,'think','1箱に12個入りが5箱あります。7個を補充しました。残りは何個？')['answer']=='67'
        assert run(d,'think','1箱に6個入りが5箱。箱はいくつ？')['answer']=='5'
        r=run(d,'verified-query','1箱に6個入りが5箱。箱はいくつ？');assert r['answer']=='5' and r['verification_evidence'].get('independent')

def test_cp1_inexact_counts_abstain_and_crosscheck_keeps_correct_answers():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP1-F');head='1箱に8個入りが4箱あります。'
        for cl in ['5個ぐらい食べました','3個か4個食べました','およそ4個食べました','いくつか食べました','3〜5個食べました']:
            q=head+cl+'。残りは何個？'
            assert run(d,'think',q)['answer'] is None,q
            assert run(d,'verified-query',q)['uncertain'],q
        assert run(d,'think',head+'3個食べました。残りは何個か？')['answer']=='29'
        # the independent verifier must not withhold a correct answer over surface form (は/が, です)
        r=run(d,'verified-query','もし雨が降るなら地面が濡れる。雨が降る。地面は濡れる？')
        assert not r['uncertain'] and '濡れる' in r['answer'] and r['verification_evidence'].get('independent')

def test_cp1_related_memory_echo_is_not_presented_as_certain():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP1-G')
        for f in ['こずえ食堂の開店時刻は10時である。','桜台学院の創立者は森川トキである。','The Merrow river is 720 kilometers long.']:run(d,'knowledge-add',f)
        for q in ['こずえ食堂の閉店時刻は？','若葉学院の創立者は？','How wide is the Merrow river?']:
            assert run(d,'verified-query',q)['uncertain'],q
        r=run(d,'verified-query','桜台学院の創立者は？');assert not r['uncertain'] and '森川トキ' in r['answer']
        assert run(d,'whole-audit')['ok']

def test_cp1_occurrence_premise_only_for_plain_occurrence():
    with tempfile.TemporaryDirectory() as td:
        d=Path(td)/'d';run(d,'init','--individual-id','CP1-H')
        r=run(d,'verified-query','雨なら地面が濡れる。雨が降っている。地面は濡れる？');assert not r['uncertain'] and r['verification_evidence'].get('kind')=='LOGIC_MP'
        for q in ['雨なら地面が濡れる。雨雲が見える。地面は濡れる？','雨なら地面が濡れる。雨が降った夢を見た。地面は濡れる？','雨なら地面が濡れる。雨が降ると聞いた。地面は濡れる？']:
            assert run(d,'verified-query',q)['uncertain'],q

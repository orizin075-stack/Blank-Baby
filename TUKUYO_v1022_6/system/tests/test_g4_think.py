"""generation 4 in `think`: problems with numbers also go through generation 4. The wording is our own."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_g4 import api,llm
import test_g4_learn as L

def test_think_reads_with_generation_4(tmp_path):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for k in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS'):env.pop(k,None)
    cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    d=str(tmp_path/'d')
    def run(*a):
        p=subprocess.run(cmd+['--data',d,*a],cwd=ROOT,env=env,capture_output=True,text=True,timeout=240);return json.loads(p.stdout)
    assert run('init')['ok']
    think=lambda q,*x:run('think',*x,'--',q)
    # an English story: generation 4 reads it; the v1022 core's English story reading is not used
    r=think('Kim saw 4 cats in the morning. Later she saw one more cat. How many cats did she see in all?')
    assert r['answer']=='5' and r['gen4']['route']=='own' and r['proof']['kind']=='g4_reading' and r['explanation']
    assert any(x['route']=='v1022' and x.get('used') is False for x in r['gen4']['readings'])
    # a story reading of the v1022 core that generation 4 cannot confirm is withheld, not answered
    r=think('A garden has 12 rows and 5 columns of plants. How many plants are there in all?')
    assert r['answer'] is None and r['uncertain'] and r['reason']=='V1022_STORY_READING_UNCONFIRMED' and r['withheld_answer']=='17'
    # the v1022 formula families stand; an answer both read keeps the v1022 proof
    assert think('A rectangle is 6 cm long and 4 cm wide. What is its area?')['answer']=='24'
    r=think('Jake has 34 fewer balls than Audrey. Audrey has 41 balls. How many balls does Jake have?')
    assert r['answer']=='7' and r['proof']['kind']=='mathprob' and r['gen4']['route']=='v1022+own'
    # without Claude, Japanese and questions without numbers are answered as before
    assert think('りんごが12個あります。妹に5個あげました。残りは何個ですか？')['answer']=='7'
    assert think('If it snows, the school closes. The school does not close. Does it snow?')['answer'].startswith('No')
    # an expression is the v1022 core's own reading, not a story
    assert think('12*(5+4)')['answer']=='108'
    # llm-ask asks the same local readings first
    r=run('llm-ask','--','Kim saw 4 cats in the morning. Later she saw one more cat. How many cats did she see in all?')
    assert (r['source'],r['answer'],r['gen4']['route'])==('local-proof','5','own')
    r=run('llm-ask','--','A garden has 12 rows and 5 columns of plants. How many plants are there in all?')
    assert r['status']=='abstained' and r['local_reason']=='V1022_STORY_READING_UNCONFIRMED'
    # the v1022 core alone
    r=think('Jake has 34 fewer balls than Audrey. Audrey has 41 balls. How many balls does Jake have?','--engine','v1022')
    assert r['answer']=='7' and 'gen4' not in r

def test_think_with_recorded_claude_readings(tmp_path,monkeypatch):
    base={'ok':True,'answer':None,'confidence':0.,'uncertain':True,'recognized':False,'reason':'NOT_RECOGNIZED','proof':None}
    monkeypatch.setenv('TUKUYO_LLM_REPLAY',str(L._replay(tmp_path,L.T,L.READING,L.READING)));llm._replay_cache.clear()
    r=api.think(None,L.T,base,llm='on')
    assert (r['answer'],r['gen4']['route'],r['uncertain'])==('14','llm+llm',False)
    # one Claude reading alone is withheld
    rec=tmp_path/'one.jsonl';rec.write_text(Path(os.environ['TUKUYO_LLM_REPLAY']).read_text(encoding='utf-8').splitlines()[0]+'\n',encoding='utf-8')
    monkeypatch.setenv('TUKUYO_LLM_REPLAY',str(rec));llm._replay_cache.clear()
    r=api.think(None,L.T,base,llm='on')
    assert r['answer'] is None and r['reason']=='SINGLE_LLM_READING' and r['withheld_answer']=='14'

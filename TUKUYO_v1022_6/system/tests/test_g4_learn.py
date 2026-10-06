"""generation 4: learning readings from verified examples (offline, with recorded Claude replies), and the gen4 CLI."""
import json,os,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_g4 import llm,api,learn

T='Twelve less than three times a number is 30. What is the number?'
READING={'readable':True,'quantities':[
   {'name':'twelve','unit':'1','integer':False,'signed':False,'about':'twelve'},
   {'name':'factor','unit':'1','integer':False,'signed':False,'about':'three times'},
   {'name':'result','unit':'1','integer':False,'signed':False,'about':'the result'},
   {'name':'number','unit':'1','integer':False,'signed':False,'about':'the number'}],
 'facts':[{'eq':'twelve = 12','span':'Twelve less','known':''},{'eq':'factor = 3','span':'three times','known':''},
          {'eq':'result = 30','span':'is 30','known':''},{'eq':'factor * number - twelve = result','span':'Twelve less than three times a number is 30','known':''}],
 'ask':'number','answer_unit':'','unused':[]}

def _replay(tmp_path,text,story,goal):
    rec=tmp_path/'replay.jsonl';lines=[]
    for view,o in (('story',story),('goal',goal)):
        h=llm.request_hash('read:'+view+':'+llm.PROMPT_VERSION,llm.system_prompt(view),'Text: '+text)
        lines.append(json.dumps({'hash':h,'ok':True,'text':json.dumps(o,ensure_ascii=False),'model':'fixture','request_id':'req_fixture_'+view},ensure_ascii=False))
    rec.write_text('\n'.join(lines)+'\n',encoding='utf-8');return rec

def test_agreeing_claude_readings_are_learned_and_reused_without_claude(tmp_path,monkeypatch):
    data=tmp_path/'individual';data.mkdir()
    monkeypatch.setenv('TUKUYO_LLM_REPLAY',str(_replay(tmp_path,T,READING,READING)));llm._replay_cache.clear()
    r=api.solve(T,llm='on',data=data)
    assert (r['answer'],r['route'])==('14','llm+llm') and r['learned'],r
    # the same wording with another number: read from the template, no Claude
    monkeypatch.delenv('TUKUYO_LLM_REPLAY');llm._replay_cache.clear()
    r2=api.solve(T.replace('30','45'),llm='off',data=data)
    assert (r2['answer'],r2['route'])==('19','learned'),r2
    # a different wording is not matched
    assert api.solve('Twelve more than three times a number is 30. What is the number?',llm='off',data=data)['answer'] is None
    st=learn.Store(data/'g4');a=st.audit();assert a['ok'] and a['templates']==1

def test_a_template_never_commits_what_the_checker_refuses(tmp_path):
    data=tmp_path/'individual';st=learn.Store(data/'g4')
    spec={'schema':'tukuyo.g4.fpl/1','lang':'en','text':T,'quantities':READING['quantities'],'ask':'number','unused':[],
          'facts':[{'eq':f['eq'],'span':f['span']} for f in READING['facts']]}
    st.add(spec,{'route':'test'})
    # 3 * n - 12 = 6 -> n = 6, read from the template
    r=api.solve(T.replace('30','6'),llm='off',data=data)
    assert r['answer']=='6' and r['route']=='learned'
    o=json.loads((data/'g4'/'learned.json').read_text(encoding='utf-8'))
    tid=next(iter(o['templates']));o['templates'][tid]['reading']['facts'][3]['eq']='factor * number + twelve = result'
    (data/'g4'/'learned.json').write_text(json.dumps(o),encoding='utf-8')
    r=api.solve(T.replace('30','6'),llm='off',data=data)
    assert r['answer'] is None and any(x.get('reason')=='LEARNED_STORE_SEAL' for x in r['readings'])

def test_gen4_cli(tmp_path):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
    for k in ('TUKUYO_LLM_PROVIDER','TUKUYO_LLM_COMMAND','TUKUYO_LLM_TEACHERS','TUKUYO_ANTHROPIC_API_KEY','TUKUYO_LLM_REPLAY'):env.pop(k,None)
    cmd=[sys.executable,'-B',str(ROOT/'run_tukuyo.py')];anchor=os.environ.get('TUKUYO_TEST_RUNTIME_ANCHOR')
    if anchor:cmd+=['--runtime-trust-file',anchor]
    d=str(tmp_path/'d')
    def cli(*a):
        p=subprocess.run(cmd+['--data',d,*a],cwd=ROOT,env=env,capture_output=True,text=True,timeout=240);return json.loads(p.stdout)
    assert cli('init')['ok']
    r=cli('g4-solve','--','Nora had 30 shells. She gave 8 shells to her cousin. How many shells does she have left?')
    assert (r['answer'],r['route'])==('22','own'),r
    r=cli('g4-solve','--','りんごが12個あります。妹に5個あげました。残りは何個ですか？')
    assert (r['answer'],r['route'])==('7','v1022'),r
    r=cli('g4-ask','--','What is the capital of France?')
    assert r['answer'] is None and r['reason']=='NOT_A_PROBLEM_AND_NO_LLM'
    assert cli('g4-audit')['ok'] and cli('g4-learned')['templates']==[]

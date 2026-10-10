"""generation 4: three parents (Claude, ChatGPT, Gemini). Which parents are configured, how their readings are weighed
(two different parents must agree), and how each SDK's reply is read. Offline: recorded replies and fake clients that
return the SDKs' own response types; no test reaches an API."""
import json,os,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from tukuyo_g4 import api,llm,learn
import test_g4_learn as L

KEYS=('TUKUYO_ANTHROPIC_API_KEY','TUKUYO_OPENAI_API_KEY','TUKUYO_OPENAI_MODEL','TUKUYO_GEMINI_API_KEY','TUKUYO_GEMINI_MODEL',
      'TUKUYO_LLM_PARENTS','TUKUYO_LLM_VOICE','TUKUYO_LLM_REPLAY','TUKUYO_LLM_RECORD')

@pytest.fixture
def clean(monkeypatch):
    for k in KEYS:monkeypatch.delenv(k,raising=False)
    llm._replay_cache.clear();llm._clients.clear()
    yield monkeypatch
    llm._replay_cache.clear();llm._clients.clear()

def test_which_parents_are_configured(clean):
    m=clean
    for k,v in (('OPENAI_API_KEY','host'),('GEMINI_API_KEY','host'),('GOOGLE_API_KEY','host'),('ANTHROPIC_API_KEY','host')):m.setenv(k,v)
    assert llm.parents()==[] and not llm.available()            # the host's own keys are never used
    m.setenv('TUKUYO_ANTHROPIC_API_KEY','k');assert llm.parents()==['claude']
    m.setenv('TUKUYO_OPENAI_API_KEY','k');assert llm.parents()==['claude']        # ChatGPT needs a model to be chosen
    assert llm.read(L.T,parent='chatgpt')['reason']=='MODEL_NOT_SET'
    m.setenv('TUKUYO_OPENAI_MODEL','m');m.setenv('TUKUYO_GEMINI_API_KEY','k');m.setenv('TUKUYO_GEMINI_MODEL','m')
    assert llm.parents()==['claude','chatgpt','gemini']
    m.setenv('TUKUYO_LLM_PARENTS','gemini,claude');assert llm.parents()==['claude','gemini']
    m.setenv('TUKUYO_LLM_VOICE','gemini');assert llm.voice()=='gemini'

def test_readiness_says_what_is_missing_and_asks_no_parent_unless_live(tmp_path,clean):
    m=clean;sent=[]
    m.setattr(llm,'reachable',lambda p,timeout=10:'blocked' if p=='chatgpt' else 'ok')
    m.setattr(llm,'installed',lambda p:True)
    m.setattr(llm,'call',lambda *a,**k:sent.append(k.get('parent')) or {'ok':True,'model':'fixture','usage':{},'ms':1})
    r=llm.readiness()['parents']
    assert r['claude']['missing']==['key'] and r['chatgpt']['missing']==['key','model','network'] and r['gemini']['missing']==['key','model']
    m.setenv('TUKUYO_GEMINI_API_KEY','secret-value-1234');m.setenv('TUKUYO_GEMINI_MODEL','m')
    r=llm.readiness()
    assert r['parents']['gemini']['ready'] and r['parents']['gemini']['key']=='set' and 'secret-value-1234' not in json.dumps(r)
    assert not sent and r['paid_call_made'] is False                       # without live, nothing is sent
    r=llm.readiness(live=True)
    assert sent==['gemini'] and r['paid_call_made'] is True and r['parents']['gemini']['live']['ok']
    rec=tmp_path/'replay.jsonl';rec.write_text('',encoding='utf-8');m.setenv('TUKUYO_LLM_REPLAY',str(rec))
    assert llm.readiness(live=True)['paid_call_made'] is False            # a replayed call costs nothing

def _replay(tmp_path,entries):
    """entries: (parent, text, reading or None) -> a replay file; None leaves that parent's reading out"""
    lines=[]
    for parent,text,o in entries:
        if o is None:continue
        h=llm.request_hash(llm._kind(parent,'read:story:'+llm.PROMPT_VERSION),llm.system_prompt('story'),'Text: '+text)
        lines.append(json.dumps({'parent':parent,'hash':h,'ok':True,'text':json.dumps(o,ensure_ascii=False),'model':'fixture-'+parent,
                                 'request_id':'req_'+parent},ensure_ascii=False))
    rec=tmp_path/'replay.jsonl';rec.write_text('\n'.join(lines)+'\n',encoding='utf-8');return rec

def test_two_different_parents_must_agree(tmp_path,clean):
    m=clean
    wrong=json.loads(json.dumps(L.READING));wrong['facts'][3]['eq']='factor * number + twelve = result'
    t={c:L.T+' ['+c+']' for c in 'abcd'}
    rec=_replay(tmp_path,[('claude',t['a'],L.READING),('chatgpt',t['a'],L.READING),('gemini',t['a'],L.READING),
                          ('claude',t['b'],L.READING),('gemini',t['b'],L.READING),
                          ('claude',t['c'],L.READING),('chatgpt',t['c'],wrong),
                          ('gemini',t['d'],L.READING)])
    m.setenv('TUKUYO_LLM_REPLAY',str(rec))
    assert llm.parents()==['claude','chatgpt','gemini']
    data=tmp_path/'individual';data.mkdir()
    r=api.solve(t['a'],llm='on',data=data)
    assert (r['answer'],r['route'])==('14','chatgpt+claude+gemini') and r['learned']
    assert learn.Store(data/'g4').load()['templates'][r['learned']]['provenance']['parents']==['chatgpt','claude','gemini']
    r=api.solve(t['b'],llm='on')
    assert (r['answer'],r['route'])==('14','claude+gemini')                    # ChatGPT's reading is missing: two still agree
    assert any(x['route']=='llm_chatgpt_story' and not x['ok'] for x in r['readings'])
    r=api.solve(t['c'],llm='on')
    assert r['answer'] is None and r['reason']=='DISAGREE:14,6'
    r=api.solve(t['d'],llm='on')
    assert r['answer'] is None and r['reason']=='SINGLE_LLM_READING' and r['withheld']=='14'

def test_every_parent_answers_a_question_that_is_not_a_problem(tmp_path,clean):
    m=clean;q='What is the capital of France?';lines=[]
    for parent,a in (('claude','Paris.'),('chatgpt','paris'),('gemini','Paris')):
        h=llm.request_hash(llm._kind(parent,'answer:2'),llm.ANSWER_SYSTEM,q)
        lines.append(json.dumps({'parent':parent,'hash':h,'ok':True,'text':a,'model':'fixture-'+parent}))
    rec=tmp_path/'answers.jsonl';rec.write_text('\n'.join(lines)+'\n',encoding='utf-8');m.setenv('TUKUYO_LLM_REPLAY',str(rec))
    r=api.ask(q,llm='on',voices='all')
    assert r['verified'] is False and r['source']=='claude' and r['agree'] is True and [a['parent'] for a in r['answers']]==['claude','chatgpt','gemini']
    m.setenv('TUKUYO_LLM_VOICE','gemini');r=api.ask(q,llm='on')
    assert (r['answer'],r['source'])==('Paris','gemini') and 'answers' not in r

def test_a_question_with_a_number_reaches_the_voice_when_the_parents_say_it_is_no_problem(tmp_path,clean):
    m=clean;q='Who won the World Cup in 2018?';no={'readable':False,'quantities':[],'facts':[],'ask':'','answer_unit':'','unused':[]};lines=[]
    for parent in ('claude','gemini'):
        h=llm.request_hash(llm._kind(parent,'read:story:'+llm.PROMPT_VERSION),llm.system_prompt('story'),'Text: '+q)
        lines.append(json.dumps({'parent':parent,'hash':h,'ok':True,'text':json.dumps(no),'model':'fixture-'+parent}))
        h=llm.request_hash(llm._kind(parent,'answer:2'),llm.ANSWER_SYSTEM,q)
        lines.append(json.dumps({'parent':parent,'hash':h,'ok':True,'text':'France','model':'fixture-'+parent}))
    rec=tmp_path/'r.jsonl';rec.write_text('\n'.join(lines)+'\n',encoding='utf-8');m.setenv('TUKUYO_LLM_REPLAY',str(rec))
    r=api.ask(q,llm='on',voices='all',data=tmp_path/'d')
    assert (r['kind'],r['answer'],r['agree'],r['remembered'])==('question','France',True,True)
    m.delenv('TUKUYO_LLM_REPLAY');llm._replay_cache.clear()
    r=api.ask(q,llm='off',data=tmp_path/'d');assert (r['answer'],r['route'],r['source'])==('France','remembered','parents_agreed')
    # a math problem stays a problem, even when nothing reads it
    r=api.ask('A garden has 12 rows and 5 columns of plants. How many plants are there in all?',llm='off')
    assert r['kind']=='problem' and r['answer'] is None

class _Fake:
    def __init__(s,reply):s.reply=reply;s.kw=None
    def __call__(s,**kw):s.kw=kw;return s.reply

def test_chatgpt_replies_are_read_from_the_responses_api(clean):
    pytest.importorskip('openai')
    from openai.types.responses import Response,ResponseOutputMessage,ResponseOutputText,ResponseOutputRefusal,ResponseUsage
    from openai.types.responses.response import IncompleteDetails
    m=clean;m.setenv('TUKUYO_OPENAI_API_KEY','k');m.setenv('TUKUYO_OPENAI_MODEL','fixture-gpt')
    def response(content,status='completed',incomplete=None):
        msg=ResponseOutputMessage.model_construct(type='message',id='msg_1',role='assistant',status='completed',content=content)
        return Response.model_construct(id='resp_1',model='fixture-gpt',output=[msg],status=status,incomplete_details=incomplete,
                                        usage=ResponseUsage.model_construct(input_tokens=11,output_tokens=22,total_tokens=33))
    ok=_Fake(response([ResponseOutputText.model_construct(type='output_text',text=json.dumps(L.READING),annotations=[])]))
    m.setitem(llm._clients,'chatgpt',type('C',(),{'responses':type('R',(),{'create':ok})()})())
    r=llm.read(L.T,parent='chatgpt')
    assert r['ok'] and api.evaluate(r['spec'],'llm_chatgpt_story')['value']=='14'
    assert r['reply']['usage']=={'input_tokens':11,'output_tokens':22} and r['reply']['request_id']=='resp_1'
    kw=ok.kw;assert kw['model']=='fixture-gpt' and kw['store'] is False and kw['instructions']==llm.system_prompt('story')
    assert kw['text']['format']['type']=='json_schema' and kw['text']['format']['strict'] is True and kw['text']['format']['schema']==llm.FPL_SCHEMA
    no=_Fake(response([ResponseOutputRefusal.model_construct(type='refusal',refusal='no')]))
    m.setitem(llm._clients,'chatgpt',type('C',(),{'responses':type('R',(),{'create':no})()})())
    assert llm.read(L.T,parent='chatgpt')['reason']=='REFUSAL'
    cut=_Fake(response([],status='incomplete',incomplete=IncompleteDetails(reason='max_output_tokens')))
    m.setitem(llm._clients,'chatgpt',type('C',(),{'responses':type('R',(),{'create':cut})()})())
    assert llm.read(L.T,parent='chatgpt')['reason']=='INCOMPLETE:max_output_tokens'

def test_gemini_replies_are_read_from_generate_content(tmp_path,clean):
    pytest.importorskip('google.genai')
    from google.genai import types
    m=clean;m.setenv('TUKUYO_GEMINI_API_KEY','k');m.setenv('TUKUYO_GEMINI_MODEL','fixture-gemini');m.setenv('TUKUYO_LLM_RECORD',str(tmp_path/'rec.jsonl'))
    def response(text=None,finish=types.FinishReason.STOP,block=None):
        cand=[types.Candidate(content=types.Content(role='model',parts=[types.Part(text=text)]),finish_reason=finish)] if text is not None else []
        return types.GenerateContentResponse(candidates=cand,model_version='fixture-gemini-001',response_id='g_1',
            prompt_feedback=types.GenerateContentResponsePromptFeedback(block_reason=block) if block else None,
            usage_metadata=types.GenerateContentResponseUsageMetadata(prompt_token_count=10,candidates_token_count=20,thoughts_token_count=5))
    ok=_Fake(response(json.dumps(L.READING)))
    m.setitem(llm._clients,'gemini',type('C',(),{'models':type('M',(),{'generate_content':ok})()})())
    r=llm.read(L.T,parent='gemini')
    assert r['ok'] and api.evaluate(r['spec'],'llm_gemini_story')['value']=='14'
    assert r['reply']['usage']['output_tokens']==25 and r['reply']['model']=='fixture-gemini-001'
    cfg=ok.kw['config'];assert ok.kw['model']=='fixture-gemini' and cfg.response_mime_type=='application/json'
    assert cfg.response_json_schema==llm.FPL_SCHEMA and cfg.system_instruction==llm.system_prompt('story')
    assert json.loads((tmp_path/'rec.jsonl').read_text(encoding='utf-8').splitlines()[0])['parent']=='gemini'
    for reply,reason in ((response(block=types.BlockedReason.SAFETY),'BLOCKED:SAFETY'),
                         (response(json.dumps(L.READING),finish=types.FinishReason.MAX_TOKENS),'MAX_TOKENS'),
                         (response(json.dumps(L.READING),finish=types.FinishReason.SAFETY),'FINISH:SAFETY')):
        m.setitem(llm._clients,'gemini',type('C',(),{'models':type('M',(),{'generate_content':_Fake(reply)})()})())
        assert llm.read(L.T,parent='gemini')['reason']==reason

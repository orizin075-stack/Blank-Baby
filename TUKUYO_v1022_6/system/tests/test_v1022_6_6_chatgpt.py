"""Real SDK wire contract on a loopback fake server, signed dialogue and tutoring.

All teacher replies are fixtures. No live OpenAI inference is claimed.
"""
import copy,json,os,time
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_v1022_5_fusion import run
from tukuyo_g4 import chatgpt_auth as auth,chatgpt_chat as chat,chatgpt_study as study,llm,api,learn
import test_g4_learn as example

@pytest.fixture
def clean(monkeypatch,tmp_path):
    for k in ('TUKUYO_LLM_REPLAY','TUKUYO_LLM_RECORD','TUKUYO_OPENAI_API_KEY','TUKUYO_OPENAI_MODEL','TUKUYO_LLM_PARENTS','TUKUYO_CHATGPT_AUTH','TUKUYO_OPENAI_BASE_URL'):
        monkeypatch.delenv(k,raising=False)
    monkeypatch.setenv('TUKUYO_CHATGPT_CREDENTIAL_FILE',str(tmp_path/'external-auth/chatgpt.json'))
    llm._clients.clear();llm._replay_cache.clear()
    yield monkeypatch
    llm._clients.clear();llm._replay_cache.clear()

def test_pkce_loopback_and_issued_client_bound(clean):
    from urllib.parse import urlparse,parse_qs,urlencode
    pending,url=auth.prepare('urn:uuid:test','http://127.0.0.1:1455/auth/callback')
    q=parse_qs(urlparse(url).query)
    assert q['client_id']==['dynamic_agent_client'] and q['resource']==[auth.RESOURCE]
    assert q['code_challenge_method']==['S256'] and q['code_challenge'][0]!=pending['verifier']
    ex=auth.callback(pending,urlencode({'state':pending['state'],'code':'fixture','client_id':'oaiapp_test'}))
    assert ex['client_id']=='oaiapp_test' and ex['redirect_uri']==pending['redirect_uri'] and 'client_secret' not in ex
    with pytest.raises(ValueError,match='STATE'):auth.callback(pending,'state=wrong&code=x&client_id=oaiapp_test')
    with pytest.raises(ValueError,match='ISSUED_CLIENT'):auth.callback(pending,urlencode({'state':pending['state'],'code':'x'}))
    with pytest.raises(ValueError,match='LOOPBACK'):auth.prepare('h','http://localhost:1455/auth/callback')
    returning,_=auth.prepare('h',pending['redirect_uri'],{'client_id':'oaiapp_test','subject':'fixture'})
    with pytest.raises(ValueError,match='CLIENT_CHANGED'):auth.callback(returning,urlencode({'state':returning['state'],'code':'x','client_id':'oaiapp_other'}))
    _,manual=auth.prepare('h',pending['redirect_uri'],{'client_id':'oaiapp_test','subject':'fixture','id_token':'private-fixture'},allow_id_token_hint=False)
    assert 'id_token_hint' not in parse_qs(urlparse(manual).query) and 'private-fixture' not in manual

def test_identity_nonce_audience_signature_and_scope(clean):
    import jwt,httpx
    from cryptography.hazmat.primitives.asymmetric import rsa
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    claims={'sub':'fixture-account','iss':auth.ISSUER,'aud':'oaiapp_test','exp':time.time()+1000,'nonce':'expected'}
    token=jwt.encode(claims,key,algorithm='RS256')
    class Discovery:
        def raise_for_status(self):pass
        def json(self):return {'issuer':auth.ISSUER,'jwks_uri':auth.ISSUER+'/.well-known/jwks.json','id_token_signing_alg_values_supported':['RS256']}
    clean.setattr(httpx,'get',lambda *a,**k:Discovery())
    clean.setattr(jwt,'PyJWKClient',lambda *a,**k:SimpleNamespace(get_signing_key_from_jwt=lambda t:SimpleNamespace(key=key.public_key())))
    assert auth.verify_identity(token,'oaiapp_test','expected')['sub']=='fixture-account'
    with pytest.raises(ValueError,match='NONCE'):auth.verify_identity(token,'oaiapp_test','wrong')
    with pytest.raises(jwt.InvalidAudienceError):auth.verify_identity(token,'oaiapp_other','expected')
    forged=jwt.encode(claims,rsa.generate_private_key(public_exponent=65537,key_size=2048),algorithm='RS256')
    with pytest.raises(jwt.InvalidSignatureError):auth.verify_identity(forged,'oaiapp_test','expected')
    with pytest.raises(ValueError,match='SCOPE'):auth.token_record({'access_token':'fixture','token_type':'Bearer','scope':'openid'},'oaiapp_test','h',claims)

def test_private_credentials_are_opt_in_not_host_keys(clean):
    clean.setenv('OPENAI_API_KEY','host-secret-never-use')
    assert not llm.settings('chatgpt')['key']
    o=auth.token_record({'access_token':'fixture-secret','token_type':'Bearer','scope':'chatgpt.tokens.use.direct'},'oaiapp_test','h',{'sub':'fixture'})
    o['model']='fixture-model';auth.write_private(auth.path(),o)
    assert not llm.settings('chatgpt')['key']
    clean.setenv('TUKUYO_CHATGPT_AUTH','plan');s=llm.settings('chatgpt')
    assert s['key'] and s['model']=='fixture-model' and s['base_url']==auth.RESOURCE
    assert 'fixture-secret' not in json.dumps(auth.status())
    if os.name!='nt':
        auth.path().chmod(0o644)
        with pytest.raises(ValueError,match='PERMISSIONS'):auth.load()

def test_oauth_stream_requires_completed_and_obeys_preview(clean):
    def response(text='fixture'):
        return SimpleNamespace(output_text=text,model='fixture-model',id='resp_fake',output=[],status='completed',usage=None)
    seen=[]
    class Stream:
        def __init__(self,events):self.events=events
        def __enter__(self):return iter(self.events)
        def __exit__(self,*a):pass
    events=[SimpleNamespace(type='response.output_text.delta',delta='fixture'),SimpleNamespace(type='response.completed',response=response())]
    def create(**kw):seen.append(kw);return Stream(events)
    clean.setattr(llm,'_client',lambda parent:SimpleNamespace(responses=SimpleNamespace(create=create)))
    s={'model':'fixture-model','auth_mode':'plan'}
    assert llm._call_chatgpt(s,'instructions','question',None,500)['ok']
    assert seen[-1]['stream'] and seen[-1]['store'] is False and isinstance(seen[-1]['input'],list)
    assert not {'max_output_tokens','previous_response_id','temperature'}&seen[-1].keys()
    events[:]=[SimpleNamespace(type='response.output_text.delta',delta='misleading partial answer')]
    assert llm._call_chatgpt(s,'i','q',None,500)['reason']=='STREAM_INTERRUPTED'
    events[:]=[SimpleNamespace(type='response.failed',response=SimpleNamespace(error=SimpleNamespace(code='subscription_sharing_usage_limit_exceeded')))]
    assert not llm._call_chatgpt(s,'i','q',None,500)['ok']

def test_real_openai_sdk_request_on_local_mock_server(clean):
    from http.server import HTTPServer,BaseHTTPRequestHandler
    import threading,openai
    seen=[]
    class H(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_POST(self):
            seen.append((self.path,json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
            body={'id':'resp_local','object':'response','created_at':1,'model':'fixture-model','status':'completed',
                  'output':[{'type':'message','id':'msg_local','role':'assistant','status':'completed','content':[{'type':'output_text','text':'local fixture reply','annotations':[]}]}],
                  'usage':{'input_tokens':1,'output_tokens':2,'total_tokens':3}}
            data=json.dumps(body).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    with HTTPServer(('127.0.0.1',0),H) as server:
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        clean.setenv('TUKUYO_OPENAI_API_KEY','fake-test-key');clean.setenv('TUKUYO_OPENAI_MODEL','fixture-model')
        llm._clients['chatgpt']=openai.OpenAI(api_key='fake-test-key',base_url=f'http://127.0.0.1:{server.server_port}/v1',max_retries=0,
                                           http_client=openai.DefaultHttpxClient(trust_env=False))
        try:r=llm.answer('A test question',parent='chatgpt')
        finally:server.shutdown();thread.join()
    assert r['ok'] and r['verified'] is False and seen[0][0]=='/v1/responses'
    assert seen[0][1]['store'] is False and seen[0][1]['model']=='fixture-model'

def fixture_transport(monkeypatch,received=None):
    monkeypatch.setattr(llm,'parents',lambda:['chatgpt'])
    def call(kind,system,user,**kw):
        if received is not None:received.append(user)
        text='fixture dialogue reply'
        if kind.startswith('study:'):
            q=user.removeprefix('Text: ');r=copy.deepcopy(example.READING)
            number='45' if '45.' in q else '30'
            r['facts'][2]={'eq':'result = '+number,'span':'the result is '+number,'known':''}
            for f in r['facts']:f['span']=f['span'].replace('30',number)
            text=json.dumps(r)
        return {'ok':True,'text':text,'model':'fixture-model','request_id':'resp_fixture','usage':{'input_tokens':5,'output_tokens':8},'replayed':True}
    monkeypatch.setattr(llm,'call',call)

def test_signed_conversation_keeps_context_and_limits_requests(tmp_path,clean):
    d=tmp_path/'individual';run(d,'init');seen=[];fixture_transport(clean,seen)
    assert chat.turn(d,'First question',max_calls=2)['verified'] is False
    assert chat.turn(d,'Follow-up',max_calls=2)['ok']
    assert [x['role'] for x in seen[1]]==['user','assistant','user']
    with pytest.raises(ValueError,match='REQUEST_LIMIT'):chat.turn(d,'Third question',max_calls=64)
    assert chat.audit(d)['requests']==2 and run(d,'whole-audit')['ok']
    cache=d/chat.NS/'STATE.json';o=json.loads(cache.read_text());o['state']['sessions']['main']['turns'][0]['verified']=True;cache.write_text(json.dumps(o))
    assert not chat.audit(d)['ok'] and not run(d,'whole-audit',ok=False)['ok']

def test_pending_request_consumes_slot_and_is_not_retried(tmp_path,clean):
    d=tmp_path/'individual';run(d,'init');ticket=chat.reserve(d,'main','Uncertain external outcome',3)
    with pytest.raises(ValueError,match='PENDING'):chat.reserve(d,'main','retry',3)
    assert chat.audit(d)['pending_requests']==1
    assert run(d,'whole-audit')['ok']

def test_credentials_cannot_be_placed_in_individual_tree(tmp_path,clean):
    d=tmp_path/'individual';run(d,'init');fixture_transport(clean)
    clean.setenv('TUKUYO_CHATGPT_CREDENTIAL_FILE',str(d/'auth/chatgpt.json'))
    with pytest.raises(ValueError,match='CREDENTIAL_INSIDE_INDIVIDUAL'):chat.turn(d,'question')
    assert not (d/chat.NS).exists() and run(d,'whole-audit')['ok']

def test_teacher_learning_requires_distinct_examples_and_transfers(tmp_path,clean):
    d=tmp_path/'individual';run(d,'init');fixture_transport(clean)
    assert api.solve(example.T,llm='off',data=d)['answer'] is None
    one=study.study(d,[example.T,example.T]);assert not one['adopted_templates']
    assert learn.Store(d/'g4').audit()['templates']==0
    r=study.study(d,[example.T,example.T.replace('30','45')]);assert len(r['adopted_templates'])==1
    unknown=example.T.replace('30','60');out=api.solve(unknown,llm='off',data=d)
    assert (out['answer'],out['route'])==('24','learned')
    assert chat.audit(d)['requests']==8 and run(d,'whole-audit')['ok']

def test_dry_study_has_no_external_calls(tmp_path,clean):
    d=tmp_path/'individual';run(d,'init')
    clean.setattr(llm,'call',lambda *a,**k:pytest.fail('dry-run contacted teacher'))
    r=study.needs(d,[example.T,'Kim has 4 cats. She sees one more cat. How many cats in all?'])
    assert r['external_calls']==0 and r['queries'][0]['needs_teacher']

def test_dialogue_partial_rollback_is_rejected(tmp_path,clean):
    d=tmp_path/'individual';run(d,'init');fixture_transport(clean)
    chat.turn(d,'one');old={p.relative_to(d/chat.NS):p.read_bytes() for p in (d/chat.NS).rglob('*') if p.is_file()}
    chat.turn(d,'two')
    for p in (d/chat.NS).rglob('*'):
        if p.is_file():p.unlink()
    for n,b in old.items():p=d/chat.NS/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    with pytest.raises(ValueError,match='RECOVERY_HEAD'):chat.load(d)

def test_refresh_rotates_tokens_without_changing_account(clean):
    import httpx
    clean.setenv('TUKUYO_CHATGPT_AUTH','plan')
    old=auth.token_record({'access_token':'old-fixture','refresh_token':'old-refresh','token_type':'Bearer','scope':'chatgpt.tokens.use.direct'},'oaiapp_test','h',{'sub':'fixture'})
    old.update(expires_at=0,model='fixture-model');auth.write_private(auth.path(),old);seen=[]
    class Reply:
        status_code=200
        def json(self):return {'access_token':'new-fixture','refresh_token':'new-refresh','token_type':'Bearer','expires_in':3600}
    def post(url,**kw):seen.append((url,kw));return Reply()
    clean.setattr(httpx,'post',post)
    assert auth.credential()=='new-fixture'
    new=auth.load();assert new['subject']=='fixture' and new['refresh_token']=='new-refresh' and new['model']=='fixture-model'
    assert seen[0][1]['data']['client_id']=='oaiapp_test' and 'scope' not in seen[0][1]['data']

def test_invalid_teacher_reading_is_not_learned(tmp_path,clean):
    d=tmp_path/'individual';run(d,'init');fixture_transport(clean);original=llm.call
    def bad(kind,*args,**kw):
        r=original(kind,*args,**kw);o=json.loads(r['text']);o['facts'][3]['eq']='factor * number = result';r['text']=json.dumps(o);return r
    clean.setattr(llm,'call',bad)
    # A fabricated source span must not become an authenticated learned method.
    # This negative control does not prove general semantic independence.
    def source_bad(kind,*args,**kw):
        r=bad(kind,*args,**kw);o=json.loads(r['text']);o['facts'][3]['span']='not in the supplied question';r['text']=json.dumps(o);return r
    clean.setattr(llm,'call',source_bad)
    r=study.study(d,[example.T,example.T.replace('30','45')]);assert not r['adopted_templates']
    assert learn.Store(d/'g4').audit()['templates']==0 and chat.audit(d)['requests']==4

def test_dialogue_checkpoint_restore_keeps_credentials_external(tmp_path,clean):
    d=tmp_path/'individual';run(d,'init');fixture_transport(clean)
    run(d,'realtime-start')
    chat.turn(d,'baseline');baseline=chat.load(d)
    cp=run(d,'recovery-checkpoint','--note','signed teacher dialogue')['path']
    secret=auth.path();auth.write_private(secret,{'unrelated_fixture':'not part of individual checkpoint'})
    before=secret.read_bytes()
    for i in range(3):
        chat.turn(d,'future '+str(i))
        run(d,'recovery-restore',cp,'--trust-file',d/'v1014/recovery.pub')
        assert chat.load(d)==baseline and secret.read_bytes()==before
        assert run(d,'chatgpt-audit')['requests']==1 and run(d,'whole-audit')['ok']

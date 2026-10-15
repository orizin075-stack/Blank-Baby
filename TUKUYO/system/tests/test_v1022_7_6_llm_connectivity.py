"""Two auth routes, real SDK loopback wire, interrupted sessions and refresh races."""
import copy,json,time,threading
from types import SimpleNamespace as Obj
import pytest
from test_v1022_5_fusion import run
from test_v1022_6_6_chatgpt import clean,fixture_transport
from tukuyo_g4 import llm,chatgpt_auth as auth,chatgpt_chat as chat,openai_transport as transport

def response(text='checked complete'):
    return Obj(status='completed',output_text=text,model='fixture-model',id='resp_fixture',usage=None,output=[])

@pytest.mark.parametrize('events,reason',[
 ([Obj(type='response.output_text.delta',delta='partial')],'STREAM_INTERRUPTED'),
 ([Obj(type='response.completed',response=response()),Obj(type='response.completed',response=response())],'STREAM_DUPLICATE_COMPLETION'),
 ([Obj(type='response.completed',response=response()),Obj(type='response.output_text.delta',delta='late')],'STREAM_PROTOCOL_AFTER_COMPLETION'),
 ([Obj(type='response.output_text.delta',delta='false'),Obj(type='response.completed',response=response())],'STREAM_TEXT_MISMATCH'),
 ([Obj(type='response.output_text.delta',delta=None)],'STREAM_INVALID_DELTA'),
 ([Obj(type='response.output_text.delta',delta='x'*65537)],'RESPONSE_TOO_LARGE'),
 ([Obj(type='response.completed')],'STREAM_INVALID_COMPLETION'),
 ([Obj(type='heartbeat')]*4097,'STREAM_EVENT_BOUND'),
])
def test_stream_never_commits_partial_or_inconsistent_events(events,reason):
    r,error=transport.stream_result(iter(events));assert r is None and error['reason']==reason
    assert not error['ok'] and 'text' not in error and not error['recovery']['automatic_retry']

@pytest.mark.parametrize('change,reason',[
 ({'status':'incomplete'},'INCOMPLETE'),({'output_text':''},'EMPTY_RESPONSE'),
 ({'output_text':None},'INVALID_RESPONSE_TEXT'),({'output_text':'x'*65537},'RESPONSE_TOO_LARGE'),
 ({'output':[Obj(type='function_call')]},'UNSUPPORTED_RESPONSE_ITEM'),
 ({'output':[Obj(type='message',content=[Obj(type='refusal')])]},'REFUSAL'),
 ({'usage':Obj(input_tokens=-1,output_tokens=2)},'INVALID_RESPONSE_USAGE'),
])
def test_completed_envelope_is_checked_before_using_text(change,reason):
    r=response();r.__dict__.update(change);out=transport.completed_result(r)
    assert not out['ok'] and out['reason']==reason and 'text' not in out

@pytest.mark.parametrize('code,status,action',[
 ('subscription_sharing_usage_limit_exceeded',429,'pause_usage'),
 ('subscription_sharing_usage_unavailable',503,'wait_then_retry_manually'),
 ('subscription_sharing_user_not_eligible',403,'inspect_configuration'),
 ('subscription_sharing_unsupported_capability',400,'inspect_configuration'),
 ('subscription_sharing_invalid_user',401,'reauthenticate_or_replace_key'),
 ('insufficient_quota',429,'pause_usage'),('rate_limit_exceeded',429,'wait_then_retry_manually'),
])
def test_provider_error_advice_keeps_billing_route_and_no_secret_messages(code,status,action):
    out=transport.failure('API_STATUS',code,status,{'retry-after':'7'})
    assert out['recovery']['action']==action and out['recovery']['retry_after_seconds']==7
    assert not out['recovery']['automatic_retry'] and out['provider_code']==code
    assert transport.failure('API_STATUS','fixture-secret-token',400)['provider_code'] is None

def test_ambiguous_timeout_does_not_suggest_automatic_resend():
    r=transport.failure('TIMEOUT');assert r['recovery']['remote_outcome']=='unknown'
    assert not r['recovery']['automatic_retry'] and not r['recovery']['retryable']

def test_refresh_is_single_flight_across_threads(clean):
    import httpx
    o=auth.token_record({'access_token':'fixture-old','refresh_token':'fixture-refresh','token_type':'Bearer','scope':'chatgpt.tokens.use.direct'},'oaiapp_test','h',{'sub':'fixture'})
    o['expires_at']=0;auth.write_private(auth.path(),o);calls=[]
    def post(*a,**k):
        calls.append(1);time.sleep(.03)
        return Obj(status_code=200,json=lambda:{'access_token':'fixture-new','refresh_token':'fixture-rotated','token_type':'Bearer','expires_in':3600})
    clean.setattr(httpx,'post',post)
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as pool:tokens=list(pool.map(lambda _:auth.credential('plan'),range(4)))
    assert tokens==['fixture-new']*4 and len(calls)==1 and auth.load()['refresh_token']=='fixture-rotated'

@pytest.mark.parametrize('terminal',[False,True])
def test_refresh_temporary_failure_preserves_tokens_terminal_failure_keeps_registration(clean,terminal):
    import httpx
    o=auth.token_record({'access_token':'fixture-old','refresh_token':'fixture-refresh','token_type':'Bearer','scope':'chatgpt.tokens.use.direct'},'oaiapp_test','h',{'sub':'fixture'})
    o['expires_at']=0;auth.write_private(auth.path(),o);before=auth.path().read_bytes()
    clean.setattr(httpx,'post',lambda *a,**k:Obj(status_code=400 if terminal else 503,json=lambda:{'error':'invalid_grant' if terminal else 'server_error'}))
    with pytest.raises(ValueError,match='LOGIN_REQUIRED' if terminal else 'REFRESH_UNAVAILABLE'):auth.credential('plan')
    if terminal:
        retained=auth.load();assert retained['client_id']=='oaiapp_test' and retained['reauthentication_required']
        assert not {'access_token','refresh_token','id_token'}&retained.keys() and not auth.status()['configured']
    else:assert auth.path().read_bytes()==before

def test_credential_rotation_and_route_change_create_correct_client(clean):
    import openai
    created=[]
    def client(**kw):created.append(kw);return Obj()
    clean.setattr(openai,'OpenAI',client)
    clean.setenv('TUKUYO_OPENAI_API_KEY','fixture-first');clean.setenv('TUKUYO_OPENAI_MODEL','fixture-model')
    first=llm._client('chatgpt');assert llm._client('chatgpt') is first
    clean.setenv('TUKUYO_OPENAI_API_KEY','fixture-second');assert llm._client('chatgpt') is not first
    assert [x['api_key'] for x in created]==['fixture-first','fixture-second']
    assert all(x['max_retries']==0 for x in created)

def test_both_configuration_diagnostics_do_not_contact_or_change_mode(clean):
    clean.setenv('TUKUYO_CHATGPT_AUTH','plan')
    clean.setattr(llm,'call',lambda *a,**k:pytest.fail('diagnostics contacted model'))
    r=chat.diagnose(both=True)
    assert set(r['routes'])=={'api','plan'} and auth.mode()=='plan'
    assert not r['live_connection_verified'] and not r['automatic_billing_fallback']

def test_session_route_change_is_rejected_without_another_request(tmp_path,clean):
    d=tmp_path/'d';run(d,'init');fixture_transport(clean)
    chat.turn(d,'api question',max_calls=4);before=chat.load(d)
    clean.setenv('TUKUYO_OPENAI_MODEL','changed-model')
    with pytest.raises(ValueError,match='CONNECTION_CHANGED'):chat.turn(d,'must not send')
    assert chat.load(d)==before and run(d,'whole-audit')['ok']

def test_pending_resolution_requires_nonce_preserves_spent_slot_and_allows_next_turn(tmp_path,clean):
    d=tmp_path/'d';run(d,'init');fixture_transport(clean)
    t=chat.reserve(d,'main','interrupted',2)
    with pytest.raises(ValueError,match='BINDING'):chat.resolve_pending(d,'main','wrong')
    settled=chat.resolve_pending(d,'main',t['nonce'])
    assert settled['external_calls']==0 and not settled['request_slot_refunded'] and settled['requests']==1
    assert settled['settled_turn']['reason']=='INTERRUPTED_OUTCOME_UNKNOWN'
    assert chat.turn(d,'next')['ok']
    with pytest.raises(ValueError,match='REQUEST_LIMIT'):chat.turn(d,'third')
    assert chat.audit(d)['requests']==2 and run(d,'whole-audit')['ok']

def test_cli_pending_resolution_and_both_status_work_without_network(tmp_path,clean):
    d=tmp_path/'d';run(d,'init');t=chat.reserve(d,'main','interrupted',2)
    r=run(d,'chatgpt-audit');assert r['pending'][0]['nonce']==t['nonce']
    assert run(d,'chatgpt-resolve-pending','--session','main','--nonce',t['nonce'])['external_calls']==0
    assert run(d,'chatgpt-status','--both')['routes']['api']['automatic_retry'] is False
    assert run(d,'whole-audit')['ok']

def test_long_context_keeps_more_than_eight_turns_and_reports_trimming(tmp_path,clean):
    d=tmp_path/'d';run(d,'init');seen=[];fixture_transport(clean,seen)
    for i in range(12):assert chat.turn(d,'question '+str(i),max_calls=16)['ok']
    assert len(seen[-1])==23
    r=chat.turn(d,'small-context',context_turns=3,context_chars=1024)
    assert r['context']['included_turns']==3 and r['context']['omitted_successful_turns']==9
    assert r['context']['serialized_characters']<=1024 and len(seen[-1])==7
    assert run(d,'whole-audit')['ok']

@pytest.mark.parametrize('auth_mode,stream',[('api',False),('api',True),('plan',True)])
def test_real_sdk_wire_contract_for_both_auth_routes(clean,auth_mode,stream):
    import openai
    from http.server import HTTPServer,BaseHTTPRequestHandler
    seen=[]
    body={'id':'resp_wire','object':'response','created_at':1,'model':'fixture-model','status':'completed',
          'output':[{'type':'message','id':'msg_wire','role':'assistant','status':'completed','content':[{'type':'output_text','text':'wire-complete','annotations':[]}]}],
          'usage':{'input_tokens':2,'output_tokens':3,'total_tokens':5}}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_POST(self):
            value=json.loads(self.rfile.read(int(self.headers['Content-Length'])));seen.append((self.path,value))
            if value.get('stream'):
                events=[{'type':'response.output_text.delta','delta':'wire-complete','sequence_number':1,'item_id':'msg_wire','output_index':0,'content_index':0},
                        {'type':'response.completed','response':body,'sequence_number':2}]
                data=''.join('data: '+json.dumps(e)+'\n\n' for e in events).encode();mime='text/event-stream'
            else:data=json.dumps(body).encode();mime='application/json'
            self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    with HTTPServer(('127.0.0.1',0),Handler) as server:
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        fake=openai.OpenAI(api_key='fixture-wire-key',base_url=f'http://127.0.0.1:{server.server_port}/v1',max_retries=0,http_client=openai.DefaultHttpxClient(trust_env=False))
        clean.setattr(llm,'_client',lambda parent:fake)
        try:r=llm._call_chatgpt({'model':'fixture-model','auth_mode':auth_mode,'stream':stream},'instructions','question',None,512)
        finally:server.shutdown();thread.join();fake.close()
    assert r['ok'] and r['text']=='wire-complete' and r['transport']['attempts']==1
    path,kw=seen[0];assert path=='/v1/responses' and kw['store'] is False
    assert bool(kw.get('stream'))==stream
    if auth_mode=='plan':assert 'max_output_tokens' not in kw and isinstance(kw['input'],list) and 'previous_response_id' not in kw
    else:assert kw['max_output_tokens']==512

def test_refresh_is_single_flight_across_processes(clean):
    import os,sys,subprocess
    from pathlib import Path
    from http.server import HTTPServer,BaseHTTPRequestHandler
    count=[]
    o=auth.token_record({'access_token':'fixture-old','refresh_token':'fixture-refresh','token_type':'Bearer','scope':'chatgpt.tokens.use.direct'},'oaiapp_test','h',{'sub':'fixture'})
    o['expires_at']=0;auth.write_private(auth.path(),o)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*a):pass
        def do_POST(self):
            self.rfile.read(int(self.headers['Content-Length']));count.append(1);time.sleep(.05)
            body=json.dumps({'access_token':'fixture-new','refresh_token':'fixture-rotated','token_type':'Bearer','expires_in':3600}).encode()
            self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    with HTTPServer(('127.0.0.1',0),Handler) as server:
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        source=str(Path(auth.__file__).resolve().parents[1])
        script='import sys;sys.path.insert(0,sys.argv[1]);from tukuyo_g4 import chatgpt_auth as a;a.TOKEN=sys.argv[2];assert a.credential("plan")=="fixture-new"'
        env={k:v for k,v in os.environ.items() if k.upper() not in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY')};env['PYTHONDONTWRITEBYTECODE']='1'
        procs=[subprocess.Popen([sys.executable,'-B','-c',script,source,f'http://127.0.0.1:{server.server_port}/token'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env) for _ in range(4)]
        try:
            for proc in procs:
                out,err=proc.communicate(timeout=30);assert proc.returncode==0 and not out,err.decode()
        finally:server.shutdown();thread.join()
    assert len(count)==1 and auth.load()['refresh_token']=='fixture-rotated'

def test_auth_route_switch_requires_a_new_session(tmp_path,clean):
    d=tmp_path/'d';run(d,'init');fixture_transport(clean);chat.turn(d,'api')
    before=chat.load(d);clean.setenv('TUKUYO_CHATGPT_AUTH','plan')
    with pytest.raises(ValueError,match='CONNECTION_CHANGED'):chat.turn(d,'plan')
    assert chat.load(d)==before and run(d,'whole-audit')['ok']

def test_error_param_is_preserved_only_for_known_request_fields():
    out=transport.failure('BAD_REQUEST','subscription_sharing_unsupported_capability',400,param='max_output_tokens')
    assert out['provider_param']=='max_output_tokens'
    assert transport.failure('BAD_REQUEST',param='fixture-secret')['provider_param'] is None

def test_quota_pause_covers_new_sessions_until_explicit_resume(tmp_path,clean):
    d=tmp_path/'d';run(d,'init');fixture_transport(clean);calls=[]
    def limited(*a,**k):calls.append(1);return transport.failure('RATE_LIMITED','insufficient_quota',429)
    clean.setattr(llm,'call',limited)
    assert not chat.turn(d,'quota')['ok']
    for name in ('main','new_session'):
        with pytest.raises(ValueError,match='ROUTE_PAUSED'):chat.turn(d,'blocked',session=name)
    assert len(calls)==1 and chat.audit(d)['requests']==1 and 'api' in chat.audit(d)['paused_routes']
    assert run(d,'chatgpt-resume-route','--auth-mode','api')['external_calls']==0
    fixture_transport(clean);assert chat.turn(d,'after review')['ok']
    assert chat.audit(d)['requests']==2 and run(d,'whole-audit')['ok']

def test_study_stops_at_usage_error_without_sending_second_view(tmp_path,clean):
    from tukuyo_g4 import chatgpt_study as study
    import test_g4_learn as example
    d=tmp_path/'d';run(d,'init');fixture_transport(clean);calls=[]
    def limited(*a,**k):calls.append(1);return transport.failure('RATE_LIMITED','insufficient_quota',429)
    clean.setattr(llm,'call',limited)
    out=study.study(d,[example.T,example.T.replace('30','45')],force=True)
    assert not out['ok'] and out['usage_paused'] and out['adopted_templates']==[] and len(calls)==1
    assert chat.audit(d)['requests']==1 and run(d,'whole-audit')['ok']

@pytest.mark.parametrize('malformed',['list','scope-string','token-object','subject-object'])
def test_malformed_local_credentials_are_rejected_without_network(clean,malformed):
    o=auth.token_record({'access_token':'fixture-token','token_type':'Bearer','scope':'chatgpt.tokens.use.direct'},'oaiapp_test','h',{'sub':'fixture'})
    if malformed=='list':o=[]
    elif malformed=='scope-string':o['scopes']='chatgpt.tokens.use.direct'
    elif malformed=='token-object':o['access_token']={'not':'a token'}
    else:o['subject']={'not':'an identity'}
    auth.write_private(auth.path(),o)
    with pytest.raises(ValueError,match='CREDENTIAL_IDENTITY|SCOPE'):auth.load()
    assert not auth.status()['configured']

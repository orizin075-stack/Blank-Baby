from pathlib import Path
import base64,json,tempfile
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from tukuyo_v977.whole_state import canon,sha_obj
from tukuyo_v1012.core_reasoning import reason
from tukuyo_v1014_1.semantic_verifier import verify_bounded_semantics
from tukuyo_v1015_1.evidence_authenticity import audit_bundle,route_evaluate,SCHEMA,ZERO

SEM_CASES=[
 ('りんごが3個、みかんが2個あります。りんごは全部で何個ですか。','3',False),
 ('りんごを3個、みかんを2個持っています。りんごは合計で何個？','3',False),
 ('りんごが3個、みかんが2個あります。みかんは全部で何個ですか。','2',False),
 ('1箱6個入りを4箱買い、そのうち3個食べました。残りは何個？','21',False),
 ('6個入りパックを5つ買い、そのうち4個使いました。残りは何個ですか。','26',False),
 ('1袋に8枚入りが3袋あります。全部で何枚？','24',False),
 ('1ケース7本入りが4ケースあります。全部で何本？','28',False),
 ('最大3個と最大2個。正確な合計は？',None,True),
 ('3kgと2mを合計すると？',None,True),
]

def test_semantic_paraphrase_closure():
    for q,expected,abstain in SEM_CASES:
        r=reason(q);v=verify_bounded_semantics(q,r.get('answer'))
        if abstain:
            assert not r.get('ok') and v.get('recognized') and not v.get('decidable'),(q,r,v)
        else:
            assert r.get('ok') and str(r.get('answer'))==expected,(q,r)
            assert v.get('decidable') and v.get('supported') and v.get('expected')==expected,(q,v)

def _sign(sk,payload):
    pub=base64.b64encode(sk.public_key().public_bytes_raw()).decode()
    return {'schema':'tukuyo.v1013.witness_receipt/1','payload':payload,'public_key':pub,'signature':base64.b64encode(sk.sign(canon(payload))).decode()}

def _req(run,ident,seq,head):
    x={'schema':'tukuyo.v1013.witness_request/1','run_id':run,'identity':ident,'seq':seq,'head_sha256':head,'requested_utc_ns':seq}
    x['request_sha256']=sha_obj(x);return x

def test_evidence_authenticity_recomputes_and_rejects_self_report():
    run='r';ident={'individual_id':'i','lineage_id':'l','branch_id':'b'}
    rsk=Ed25519PrivateKey.generate();rpub=base64.b64encode(rsk.public_key().public_bytes_raw()).decode();prev=ZERO;evs=[]
    for seq,t in [(1,1_000_000_000),(2,2_000_000_000)]:
        p={'schema':'tukuyo.v1013.realtime_event/1','run_id':run,'seq':seq,'kind':'TICK','note':'','identity':ident,'process_instance_id':str(seq),'observed_utc_ns':t,'elapsed_local_seconds':seq-1,'previous_event_sha256':prev}
        env={'payload':p,'public_key':rpub,'signature':base64.b64encode(rsk.sign(canon(p))).decode()};prev=sha_obj(env);evs.append(env)
    ce={'schema':'tukuyo.v1014_4.campaign_event/1','seq':1,'kind':'CAMPAIGN_START','utc_ns':1,'pid':1,'previous_event_sha256':ZERO,'detail':{}}
    cs={'schema':'tukuyo.v1014_4.campaign/1','run_id':run,'profile':'24h','target_seconds':1,'tick_seconds':1,'event_count':1,'event_head_sha256':sha_obj(ce)}
    rs={'schema':'tukuyo.v1013.realtime_continuity/1','run_id':run,'profile':'24h','target_seconds':1,'identity':ident,'last_event_seq':2,'last_event_sha256':prev}
    wsk=Ed25519PrivateKey.generate();wpub=base64.b64encode(wsk.public_key().public_bytes_raw()).decode()
    rq1,rq2=_req(run,ident,1,sha_obj(evs[0])),_req(run,ident,2,sha_obj(evs[1]))
    p1={'schema':'tukuyo.v1013.witness_payload/1','run_id':run,'identity':ident,'seq':1,'head_sha256':rq1['head_sha256'],'request_sha256':rq1['request_sha256'],'witnessed_utc_ns':1_000_000_000}
    p2={'schema':'tukuyo.v1013.witness_payload/1','run_id':run,'identity':ident,'seq':2,'head_sha256':rq2['head_sha256'],'request_sha256':rq2['request_sha256'],'witnessed_utc_ns':3_000_000_000}
    obj={'schema':SCHEMA,'version':'v1015.1','campaign_state':cs,'campaign_events':[ce],'realtime_state':rs,'realtime_events':evs,'realtime_public_key':rpub,'witness_requests':[rq1,rq2],'witness_receipts':[_sign(wsk,p1),_sign(wsk,p2)],'source_bindings':{},'non_authoritative_source_audit':{'ok':True,'claim_boundary':{'24h_completed':True}},'claim_boundary':{}}
    obj['bundle_sha256']=sha_obj(obj)
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);ep=td/'e.json';tp=td/'w.pub';ep.write_bytes(canon(obj)+b'\n');tp.write_text(wpub)
        a=audit_bundle(ep,tp,'24h');assert a['ok'] and a['claim_boundary']['formal_duration_complete'] and not a['claim_boundary']['24h_completed'],a
        # Removing signed source material while leaving a fake completion claim must fail.
        bad=dict(obj);bad['realtime_events']=[];bad['campaign_events']=[];bad['non_authoritative_source_audit']={'ok':True,'claim_boundary':{'24h_completed':True}};bad.pop('bundle_sha256',None);bad['bundle_sha256']=sha_obj(bad);bp=td/'bad.json';bp.write_bytes(canon(bad)+b'\n')
        b=audit_bundle(bp,tp,'24h');assert not b['ok'] and not b['claim_boundary']['24h_completed'],b
        rr=route_evaluate([bp],tp);assert not rr['v1015_living_continuity_eligible'],rr

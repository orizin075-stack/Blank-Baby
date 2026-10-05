#!/usr/bin/env python3
import base64,hashlib,importlib.util,json,math,tempfile
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from tukuyo_v965.family_synthesis import propose,evaluate,canon
from tukuyo_v966.promotion import sha_obj,verify_evaluator,verify_promotion
ROOT=Path(__file__).resolve().parents[1]
def h(b):return hashlib.sha256(b).hexdigest()
def rows(n=161):
 out=[]
 for i in range(n):
  a=i-(n//2);b=((i*11+3)%31)-15;out.append({'a':a,'b':b,'expected':math.isqrt(abs(a))+b})
 return out
def loadmod(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def env(k,p):
 pub=base64.b64encode(k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode();return {'payload':p,'public_key':pub,'signature':base64.b64encode(k.sign(canon(p))).decode()}
def measure(domain_id,schema,gid,src,adapt):
 rs=adapt();wrong=sum(evaluate(P,*x[:2])!=x[2] for x in rs);return {'domain_id':domain_id,'source_schema':schema,'generator_id':gid,'rows':len(rs),'correct':len(rs)-wrong,'wrong':wrong,'invalid':0,'rows_sha256':h(canon(rs)),'generator_source_sha256':h(Path(src).read_bytes())}
P=propose(rows(),{'status':'META_GRAMMAR_CEILING_DETECTED','v964_ceiling':'isqrt_abs_plus_b'})
num=[(a,(a*17)%41-20,math.isqrt(abs(a))+((a*17)%41-20)) for a in range(-2500,2501,53)]
rmod=loadmod(ROOT/'tools/v966_resource_tier_generator.py','rg');qmod=loadmod(ROOT/'tools/v966_queue_band_generator.py','qg')
res=[(r['resource'],r['adjustment'],r['observed_score']) for r in rmod.rows(79,17)]
que=[(r['depth'],r['penalty'],r['observed_priority']) for r in qmod.rows(83,23)]
ds=[measure('numeric_far','tukuyo.v966.numeric_far/1','numeric_independent_v966',__file__,lambda:num),measure('resource_events','tukuyo.v966.resource_event/1','resource_engine_v966',ROOT/'tools/v966_resource_tier_generator.py',lambda:res),measure('queue_samples','tukuyo.v966.queue_sample/1','queue_engine_v966',ROOT/'tools/v966_queue_band_generator.py',lambda:que)]
ev=Ed25519PrivateKey.generate();au=Ed25519PrivateKey.generate()
with tempfile.TemporaryDirectory() as x:
 td=Path(x);ep=td/'ev.pub';ap=td/'au.pub';ep.write_text(base64.b64encode(ev.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode());ap.write_text(base64.b64encode(au.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode())
 er=env(ev,{'schema':'tukuyo.v966.evaluator_receipt/1','candidate_sha256':P['candidate_sha256'],'proposal_sha256':sha_obj(P),'domains':ds})
 pr=env(au,{'schema':'tukuyo.v966.promotion_receipt/1','candidate_sha256':P['candidate_sha256'],'evaluator_receipt_sha256':sha_obj(er),'decision':'PROMOTE_BOUNDED_FAMILY','scope':'V966_RESIDUAL_DERIVED_FAMILY_THREE_DOMAIN'})
 verify_promotion(pr,P,er,ep,ap)
print(json.dumps({'ok':all(d['wrong']==0 for d in ds),'proposal':P,'domains':ds,'claim':{'meta_grammar_ceiling_crossed':True,'method':'residual-derived threshold recurrence family synthesis','sqrt_hardcoded_in_proposal':False,'general_open_endedness':False,'general_l5':False,'general_l6':False}},sort_keys=True))

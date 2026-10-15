import base64,hashlib,importlib.util,json,tempfile,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from tukuyo_v965.family_synthesis import propose,evaluate,canon,sha
from tukuyo_v966.promotion import verify_evaluator,verify_promotion,sha_obj

def rows(n,offset=0):
 import math
 out=[]
 half=n//2
 for i in range(n):
  a=i-half+offset;b=((i*11+3)%31)-15
  out.append({'a':a,'b':b,'expected':math.isqrt(abs(a))+b})
 return out

def sign(k,p):
 pub=base64.b64encode(k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode();return {'payload':p,'public_key':pub,'signature':base64.b64encode(k.sign(canon(p))).decode()}

def pubfile(td,k,name):
 p=td/name;p.write_text(base64.b64encode(k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode());return p
class T(unittest.TestCase):
 def test_01_ceiling_required(self):
  with self.assertRaisesRegex(ValueError,'CEILING'): propose(rows(70),{'status':'NOT_CEILING'})
 def test_02_family_is_inferred_not_named_sqrt(self):
  p=propose(rows(120),{'status':'META_GRAMMAR_CEILING_DETECTED','source':'v964'})
  self.assertEqual(p['invented_family']['kind'],'THRESHOLD_RECURRENCE_COUNT'); self.assertNotIn('sqrt',json.dumps(p).lower())
  self.assertEqual(p['source_transform'],'ABS_A');self.assertEqual(p['residual_form'],'Y_MINUS_B')
 def test_03_far_hidden_extrapolation(self):
  p=propose(rows(120),{'status':'META_GRAMMAR_CEILING_DETECTED','source':'v964'})
  import math
  bad=[]
  for a in list(range(-2000,-900,37))+list(range(901,2001,41)):
   b=(a*13)%47-23
   if evaluate(p,a,b)!=math.isqrt(abs(a))+b:bad.append((a,b))
  self.assertEqual(bad,[])
 def test_04_triangular_threshold_family_also_fits(self):
  def tri(x):
   x=abs(x);k=0;t=1;d=2
   while t<=x:k+=1;t+=d;d+=1
   return k
  rr=[]
  for a in range(-90,91): rr.append({'a':a,'b':(a*3)%9-4,'expected':tri(a)+((a*3)%9-4)})
  p=propose(rr,{'status':'META_GRAMMAR_CEILING_DETECTED'})
  self.assertEqual(p['family_parameters']['delta_increment'],1)
  self.assertEqual(sum(evaluate(p,r['a'],r['b'])!=r['expected'] for r in rr),0)
 def test_05_sparse_boundaries_rejected(self):
  rr=rows(40); rr=rr[::3]
  with self.assertRaises(Exception):propose(rr,{'status':'META_GRAMMAR_CEILING_DETECTED'})
 def test_06_three_domain_external_gate(self):
  p=propose(rows(120),{'status':'META_GRAMMAR_CEILING_DETECTED'})
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);ev=Ed25519PrivateKey.generate();au=Ed25519PrivateKey.generate();ep=pubfile(td,ev,'ev.pub');ap=pubfile(td,au,'au.pub')
   ds=[]
   for i,(did,ss,gid) in enumerate([('numeric','num/1','numeric_v966'),('resource','resource/1','resource_engine_v966'),('queue','queue/1','queue_engine_v966')]):
    ds.append({'domain_id':did,'source_schema':ss,'generator_id':gid,'rows':30,'correct':30,'wrong':0,'invalid':0,'rows_sha256':str(i+1)*64,'generator_source_sha256':str(i+4)*64})
   pay={'schema':'tukuyo.v966.evaluator_receipt/1','candidate_sha256':p['candidate_sha256'],'proposal_sha256':sha_obj(p),'domains':ds};er=sign(ev,pay)
   self.assertEqual(len(verify_evaluator(er,p,ep)['domains']),3)
   pr={'schema':'tukuyo.v966.promotion_receipt/1','candidate_sha256':p['candidate_sha256'],'evaluator_receipt_sha256':sha_obj(er),'decision':'PROMOTE_BOUNDED_FAMILY','scope':'V966_RESIDUAL_DERIVED_FAMILY_THREE_DOMAIN'}
   self.assertEqual(verify_promotion(sign(au,pr),p,er,ep,ap)['authority']['decision'],'PROMOTE_BOUNDED_FAMILY')
 def test_07_dirty_domain_blocks(self):
  p=propose(rows(120),{'status':'META_GRAMMAR_CEILING_DETECTED'})
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);ev=Ed25519PrivateKey.generate();ep=pubfile(td,ev,'ev.pub')
   ds=[{'domain_id':str(i),'source_schema':str(i),'generator_id':'g'+str(i),'rows':30,'correct':30,'wrong':0,'invalid':0,'rows_sha256':str(i+1)*64,'generator_source_sha256':str(i+4)*64} for i in range(3)];ds[2]['wrong']=1;ds[2]['correct']=29
   er=sign(ev,{'schema':'tukuyo.v966.evaluator_receipt/1','candidate_sha256':p['candidate_sha256'],'proposal_sha256':sha_obj(p),'domains':ds})
   with self.assertRaisesRegex(ValueError,'DOMAIN_NOT_CLEAN'):verify_evaluator(er,p,ep)
if __name__=='__main__':unittest.main()

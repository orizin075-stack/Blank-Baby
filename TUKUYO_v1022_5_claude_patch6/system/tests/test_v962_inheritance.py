import base64,json,tempfile,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
from tukuyo_v962.inheritance import *
from tukuyo_v958.promotion import registry_path
from tukuyo_v959.agenda import canon

def sign(k,p):
 pub=base64.b64encode(k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode();return {'payload':p,'public_key':pub,'signature':base64.b64encode(k.sign(canon(p))).decode()}
def pubfile(td,k):
 p=td/'inherit.pub';p.write_text(base64.b64encode(k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode());return p

def live_child(td,child_id):
 p=td/'child'/'state'/'integration_state.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'payload':{'individual_id':child_id}}));return p

def proposal():
 from tukuyo_v957.novel_primitive import sha
 p={'schema':'tukuyo.v957.novel_primitive_proposal/1','rows_sha256':'1'*64,'gap_result_sha256':'2'*64,'old_dsl_best_wrong':10,'old_dsl_best_expression':'x','meta_candidate_count':5,
    'primitive':{'kind':'FLOORDIV_CONST','parameter':3,'arity':1,'input_type':'int','output_type':'int','domain':'all integers','undefined_conditions':[],'semantics':{'op':'FLOORDIV','divisor':3},'counterexample_conditions':['negative numerator with nonzero remainder']},
    'expression_ast':{'op':'ADD','left':{'op':'PRIM','primitive':{'kind':'FLOORDIV_CONST','parameter':3,'arity':1,'input_type':'int','output_type':'int','domain':'all integers','undefined_conditions':[],'semantics':{'op':'FLOORDIV','divisor':3},'counterexample_conditions':['negative numerator with nonzero remainder']},'arg':'A'},'right':{'op':'B'}},
    'expression':'(floor_div(a,3)+b)','training_wrong':0,'selection_rule':'wrong,render_length,lexical','scope':'BOUNDED_META_GRAMMAR_OUTSIDE_V945_DSL'}
 p['candidate_sha256']=sha(p);return p

class Inherit(unittest.TestCase):
 def setup_parent(self,td):
  p=proposal();rp=registry_path(td/'parent');rp.parent.mkdir(parents=True);rp.write_text(json.dumps({'schema':'tukuyo.v958.primitive_registry/1','entries':[{'candidate_sha256':p['candidate_sha256'],'proposal':p,'proposal_sha256':sha_obj(p),'evaluator_receipt_sha256':'3'*64,'promotion_receipt_sha256':'4'*64,'promotion_scope':'V958_BOUNDED_SYNTHETIC_TWO_DOMAIN','status':'ACTIVE_BOUNDED_RESEARCH','domains':['numeric','state']}]}))
  return p
 def test_01_public_only_inheritance_and_restart(self):
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);p=self.setup_parent(td);b=prepare(td/'parent',p['candidate_sha256'],'PARENT','CHILD');k=Ed25519PrivateKey.generate();pf=pubfile(td,k);pay={'schema':'tukuyo.v962.inheritance_authority/1','bundle_sha256':b['bundle_sha256'],'parent_individual_id':'PARENT','child_individual_id':'CHILD','decision':'ALLOW_PUBLIC_INHERITANCE'}
   live_child(td,'CHILD');import_bundle(td/'child',b,sign(k,pay),pf,'CHILD');self.assertEqual(evaluate_child(td/'child',p['candidate_sha256'],8,4)['answer'],6);self.assertEqual(evaluate_child(td/'child',p['candidate_sha256'],8,4)['answer'],6)
 def test_02_private_field_blocked(self):
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);p=self.setup_parent(td);b=prepare(td/'parent',p['candidate_sha256'],'P','C');b['private_memory']='x'
   k=Ed25519PrivateKey.generate();pf=pubfile(td,k);pay={'schema':'tukuyo.v962.inheritance_authority/1','bundle_sha256':b['bundle_sha256'],'parent_individual_id':'P','child_individual_id':'C','decision':'ALLOW_PUBLIC_INHERITANCE'}
   with self.assertRaisesRegex(ValueError,'PRIVATE_FIELD'):import_bundle(td/'child',b,sign(k,pay),pf,'C')
 def test_03_wrong_child_blocked(self):
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);p=self.setup_parent(td);b=prepare(td/'parent',p['candidate_sha256'],'P','C');k=Ed25519PrivateKey.generate();pf=pubfile(td,k);pay={'schema':'tukuyo.v962.inheritance_authority/1','bundle_sha256':b['bundle_sha256'],'parent_individual_id':'P','child_individual_id':'C','decision':'ALLOW_PUBLIC_INHERITANCE'}
   with self.assertRaisesRegex(ValueError,'WRONG_CHILD'):import_bundle(td/'child',b,sign(k,pay),pf,'OTHER')
 def test_04_duplicate_inheritance_blocked(self):
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);p=self.setup_parent(td);b=prepare(td/'parent',p['candidate_sha256'],'P','C');k=Ed25519PrivateKey.generate();pf=pubfile(td,k);pay={'schema':'tukuyo.v962.inheritance_authority/1','bundle_sha256':b['bundle_sha256'],'parent_individual_id':'P','child_individual_id':'C','decision':'ALLOW_PUBLIC_INHERITANCE'};r=sign(k,pay)
   live_child(td,'C');import_bundle(td/'child',b,r,pf,'C')
   with self.assertRaisesRegex(ValueError,'DUPLICATE_INHERITANCE'):import_bundle(td/'child',b,r,pf,'C')
 def test_05_missing_live_child_blocked(self):
  with tempfile.TemporaryDirectory() as x:
   td=Path(x);p=self.setup_parent(td);b=prepare(td/'parent',p['candidate_sha256'],'P','C');k=Ed25519PrivateKey.generate();pf=pubfile(td,k);pay={'schema':'tukuyo.v962.inheritance_authority/1','bundle_sha256':b['bundle_sha256'],'parent_individual_id':'P','child_individual_id':'C','decision':'ALLOW_PUBLIC_INHERITANCE'}
   with self.assertRaisesRegex(ValueError,'LIVE_CHILD_REQUIRED'):import_bundle(td/'child',b,sign(k,pay),pf,'C')
if __name__=='__main__':unittest.main()

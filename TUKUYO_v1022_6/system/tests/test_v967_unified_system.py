import base64, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src'
sys.path.insert(0,str(SRC))
from tukuyo_v959.agenda import canon,sha_obj
from tukuyo_v965.family_synthesis import propose
from tukuyo_v966.promotion import sha_obj as sha966
from tukuyo_v967.integrated_system import load_ledger
from tukuyo_v958.promotion import registry_path
from tukuyo_v957.novel_primitive import sha as sha957

def keypair(td,name):
    k=Ed25519PrivateKey.generate();pub=base64.b64encode(k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode();p=td/(name+'.pub');p.write_text(pub);return k,p,pub

def sign(k,payload):
    pub=base64.b64encode(k.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()
    return {'payload':payload,'public_key':pub,'signature':base64.b64encode(k.sign(canon(payload))).decode()}

def run(data,*args):
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONPATH':str(SRC)}
    p=subprocess.run([sys.executable,'-B',str(ROOT/'run_tukuyo.py'),'--data',str(data),*map(str,args)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
    try:o=json.loads(p.stdout)
    except Exception: raise AssertionError((p.returncode,p.stdout,p.stderr))
    return p.returncode,o

def family_rows(n=120):
    import math
    out=[];half=n//2
    for i in range(n):
        a=i-half;b=((i*11+3)%31)-15;out.append({'a':a,'b':b,'expected':math.isqrt(abs(a))+b})
    return out

def primitive_proposal():
    p={'schema':'tukuyo.v957.novel_primitive_proposal/1','rows_sha256':'1'*64,'gap_result_sha256':'2'*64,'old_dsl_best_wrong':10,'old_dsl_best_expression':'x','meta_candidate_count':5,
       'primitive':{'kind':'FLOORDIV_CONST','parameter':3,'arity':1,'input_type':'int','output_type':'int','domain':'all integers','undefined_conditions':[],'semantics':{'op':'FLOORDIV','divisor':3},'counterexample_conditions':['negative numerator with nonzero remainder']},
       'expression_ast':{'op':'ADD','left':{'op':'PRIM','primitive':{'kind':'FLOORDIV_CONST','parameter':3,'arity':1,'input_type':'int','output_type':'int','domain':'all integers','undefined_conditions':[],'semantics':{'op':'FLOORDIV','divisor':3},'counterexample_conditions':['negative numerator with nonzero remainder']},'arg':'A'},'right':{'op':'B'}},
       'expression':'(floor_div(a,3)+b)','training_wrong':0,'selection_rule':'wrong,render_length,lexical','scope':'BOUNDED_META_GRAMMAR_OUTSIDE_V945_DSL'}
    p['candidate_sha256']=sha957(p);return p

class Unified(unittest.TestCase):
    def test_01_agenda_campaign_meta_share_one_ledger(self):
        with tempfile.TemporaryDirectory() as x:
            td=Path(x);data=td/'data'
            ch=[{'challenge_id':'low','gap_state':'SEARCH_INSUFFICIENT','information_gain':2,'capability_gain':1,'uncertainty':1,'estimated_cost':5,'safety_risk':0},{'challenge_id':'high','gap_state':'REPRESENTATION_INSUFFICIENT','information_gain':8,'capability_gain':7,'uncertainty':4,'estimated_cost':9,'safety_risk':0}]
            cf=td/'c.json';cf.write_text(json.dumps(ch));af=td/'agenda.json'
            rc,o=run(data,'agenda-propose',cf,'--out',af);self.assertEqual(rc,0);self.assertEqual(o['agenda']['selected_challenge_id'],'high')
            k,pub,_=keypair(td,'obs');spec={'challenge_id':'c1','probe':{'a':3,'b':4},'hypotheses':[{'hypothesis_id':'ADD','operator':'ADD'},{'hypothesis_id':'MUL','operator':'MUL'}],'max_cycles':2};sf=td/'s.json';sf.write_text(json.dumps(spec))
            obs=[]
            for i in (1,2):
                f=td/f'o{i}.json';f.write_text(json.dumps(sign(k,{'schema':'tukuyo.v960.probe_observation/1','challenge_id':'c1','cycle':i,'a':3,'b':4,'observed':12})));obs.append(f)
            rc,o=run(data,'--observer-trust-file',pub,'campaign-run',sf,*obs);self.assertEqual(rc,0);self.assertEqual(o['selected_hypothesis_id'],'MUL')
            rc,o=run(data,'improver-compare');self.assertEqual(rc,0);self.assertEqual(o['comparison']['decision'],'PROMOTE_BOUNDED_META_POLICY')
            led=load_ledger(data);self.assertEqual([e['kind'] for e in led['events']],['RESEARCH_AGENDA_PROPOSED','SCIENCE_CAMPAIGN_COMPLETED','IMPROVER_COMPARISON'])
    def test_02_family_propose_promote_eval_integrated(self):
        with tempfile.TemporaryDirectory() as x:
            td=Path(x);data=td/'data';rf=td/'rows.json';rf.write_text(json.dumps(family_rows()));cf=td/'ceiling.json';cf.write_text(json.dumps({'status':'META_GRAMMAR_CEILING_DETECTED','source':'test'}));pf=td/'proposal.json'
            rc,o=run(data,'family-propose',rf,cf,'--out',pf);self.assertEqual(rc,0);prop=o['proposal']
            ev,evpub,_=keypair(td,'ev');au,aupub,_=keypair(td,'au')
            ds=[]
            for i,(did,ss,gid) in enumerate([('numeric','num/1','n'),('resource','res/1','r'),('queue','queue/1','q')]):ds.append({'domain_id':did,'source_schema':ss,'generator_id':gid,'rows':30,'correct':30,'wrong':0,'invalid':0,'rows_sha256':str(i+1)*64,'generator_source_sha256':str(i+4)*64})
            er=sign(ev,{'schema':'tukuyo.v966.evaluator_receipt/1','candidate_sha256':prop['candidate_sha256'],'proposal_sha256':sha966(prop),'domains':ds});erf=td/'er.json';erf.write_text(json.dumps(er))
            pr=sign(au,{'schema':'tukuyo.v966.promotion_receipt/1','candidate_sha256':prop['candidate_sha256'],'evaluator_receipt_sha256':sha966(er),'decision':'PROMOTE_BOUNDED_FAMILY','scope':'V966_RESIDUAL_DERIVED_FAMILY_THREE_DOMAIN'});prf=td/'pr.json';prf.write_text(json.dumps(pr))
            rc,o=run(data,'--family-evaluator-trust-file',evpub,'--family-promotion-trust-file',aupub,'family-promote-verify',pf,erf,prf);self.assertEqual(rc,0)
            rc,o=run(data,'family-eval',prop['candidate_sha256'],100,7);self.assertEqual(rc,0);self.assertEqual(o['answer'],17)
            rc,o=run(data,'system-status');self.assertEqual(rc,0);self.assertEqual(o['active_v967_families'],1);self.assertEqual(o['event_counts']['FAMILY_PROMOTED'],1)
    def test_03_public_inheritance_uses_same_state_root(self):
        with tempfile.TemporaryDirectory() as x:
            td=Path(x);parent=td/'parent';child=td/'child';p=primitive_proposal();rp=registry_path(parent);rp.parent.mkdir(parents=True);rp.write_text(json.dumps({'schema':'tukuyo.v958.primitive_registry/1','entries':[{'candidate_sha256':p['candidate_sha256'],'proposal':p,'proposal_sha256':sha_obj(p),'evaluator_receipt_sha256':'3'*64,'promotion_receipt_sha256':'4'*64,'promotion_scope':'V958_BOUNDED_SYNTHETIC_TWO_DOMAIN','status':'ACTIVE_BOUNDED_RESEARCH','domains':['numeric','state']}]}))
            bf=td/'bundle.json';rc,o=run(parent,'inherit-export',p['candidate_sha256'],'PARENT','CHILD','--out',bf);self.assertEqual(rc,0);bundle=json.loads(bf.read_text())
            k,pub,_=keypair(td,'inh');receipt=sign(k,{'schema':'tukuyo.v962.inheritance_authority/1','bundle_sha256':bundle['bundle_sha256'],'parent_individual_id':'PARENT','child_individual_id':'CHILD','decision':'ALLOW_PUBLIC_INHERITANCE'});rr=td/'rr.json';rr.write_text(json.dumps(receipt))
            rc,o=run(child,'init','--individual-id','CHILD');self.assertEqual(rc,0)
            rc,o=run(child,'--inheritance-trust-file',pub,'inherit-import',bf,rr,'CHILD');self.assertEqual(rc,0)
            rc,o=run(child,'inherit-eval',p['candidate_sha256'],8,4);self.assertEqual(rc,0);self.assertEqual(o['answer'],6)
            rc,o=run(child,'system-status');self.assertEqual(rc,0);self.assertEqual(o['inherited_public_capabilities'],1)
    def test_04_ledger_tamper_detected(self):
        with tempfile.TemporaryDirectory() as x:
            td=Path(x);data=td/'data';cf=td/'c.json';cf.write_text(json.dumps([{'challenge_id':'a','gap_state':'SEARCH_INSUFFICIENT','information_gain':2,'capability_gain':2,'uncertainty':2,'estimated_cost':2,'safety_risk':0},{'challenge_id':'b','gap_state':'HYPOTHESIS_AMBIGUOUS','information_gain':1,'capability_gain':1,'uncertainty':1,'estimated_cost':1,'safety_risk':0}]))
            self.assertEqual(run(data,'agenda-propose',cf)[0],0);lp=data/'research_v967'/'INTEGRATED_LEDGER.json';o=json.loads(lp.read_text());o['events'][0]['kind']='FORGED';lp.write_text(json.dumps(o))
            rc,out=run(data,'system-status');self.assertNotEqual(rc,0);self.assertIn('V967_LEDGER_HASH',out['error'])
if __name__=='__main__':unittest.main()

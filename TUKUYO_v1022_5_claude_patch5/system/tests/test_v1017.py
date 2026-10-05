import json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CLI=ROOT/'run_tukuyo.py'

def run(data,*args,ok=True):
    p=subprocess.run([sys.executable,'-B',str(CLI),'--data',str(data),*map(str,args)],cwd=ROOT,text=True,capture_output=True,timeout=240,
                     env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    try:r=json.loads(p.stdout)
    except Exception:raise AssertionError(p.stdout+p.stderr)
    if ok and (p.returncode!=0 or not r.get('ok',True)):raise AssertionError(r)
    if not ok and p.returncode==0 and r.get('ok',True):raise AssertionError('EXPECTED_FAILURE:'+str(r))
    return r

def init(d,i): return run(d,'init','--individual-id',i)
def kill(d):
    run(d,'organism2-init');run(d,'organism2-update','INJURY','--amount','1.0');r=run(d,'organism2-update','INJURY','--amount','1.0');assert r['state']['death_irreversible'] and r['state']['lifecycle']=='DEAD'

def prepare_parent(td,parent_id='PARENT-A'):
    td=Path(td);p=td/'parent';init(p,parent_id);run(p,'succession-founder-init');pub=td/'parent.pub';run(p,'succession-pubkey-export','--out',pub);return p,pub

def test_v1017_01_founder_binding_and_audit():
    with tempfile.TemporaryDirectory(prefix='v1017_01_') as td:
        p=Path(td)/'p';init(p,'FOUNDER-1');r=run(p,'succession-founder-init');assert r['generation']==0 and r['family_lineage_id'].startswith('fam-')
        s=run(p,'succession-status')['state'];a=run(p,'succession-audit');assert a['ok'] and s['role']=='FOUNDER' and s['generation']==0 and s['lineage_certificates']==[]

def test_v1017_02_export_requires_irreversible_parent_death():
    with tempfile.TemporaryDirectory(prefix='v1017_02_') as td:
        p,pub=prepare_parent(td);c=Path(td)/'child';init(c,'CHILD-B');cp=Path(td)/'child.pub';run(c,'succession-pubkey-export','--out',cp);out=Path(td)/'pkg.json';r=run(p,'succession-export','CHILD-B','--out',out,'--child-public-key-file',cp,ok=False)
        assert 'V1018_MORTALITY' in r['error'] or 'V1018_PARENT_NOT_IRREVERSIBLY_DEAD' in r['error'];assert not out.exists()

def test_v1017_03_parent_child_private_noninheritance_and_key_separation():
    with tempfile.TemporaryDirectory(prefix='v1017_03_') as td:
        td=Path(td);p,pub=prepare_parent(td);c=td/'child';init(c,'CHILD-B')
        secret='PRIVATE_AUTOBIOGRAPHICAL_MARKER_V1018_X9';run(p,'soul-experience','vow','0.9','0.9','--theme',secret,'--relation','peer-secret');kill(p)
        cp=td/'child.pub';run(c,'succession-pubkey-export','--out',cp);pkg=td/'p2c.json';ex=run(p,'succession-export','CHILD-B','--out',pkg,'--child-public-key-file',cp);assert secret not in pkg.read_text(encoding='utf-8')
        im=run(c,'succession-import',pkg,'--parent-trust-file',pub);cs=run(c,'succession-status')['state'];ps=run(p,'succession-status')['state']
        assert im['generation']==1 and cs['family_lineage_id']==ps['family_lineage_id'] and cs['parent_individual_id']=='PARENT-A'
        assert cs['succession_public_key']!=ps['succession_public_key'] and cs['identity_lineage_id']!=ps['identity_lineage_id']
        assert len(cs['lineage_certificates'])==1 and run(c,'succession-audit')['ok'] and run(c,'whole-audit')['ok']

def test_v1017_04_parent_child_grandchild_chain_and_attenuated_values():
    with tempfile.TemporaryDirectory(prefix='v1017_04_') as td:
        td=Path(td);p=td/'parent';init(p,'PARENT-A')
        r=run(p,'succession-gate-assay',td/'child','CHILD-B',td/'grand','GRAND-C')
        assert r['ok'] and [x['generation'] for x in r['audits']]==[0,1,2] and all(r['checks'].values())
        assert not r['private_marker_in_packages'] and r['linear_growth_observed']
        pvals=run(p,'succession-status')['effective_value_profile'];cvals=run(td/'child','succession-status')['effective_value_profile'];gvals=run(td/'grand','succession-status')['effective_value_profile']
        assert abs(cvals['curiosity']-.5)<abs(pvals['curiosity']-.5) and abs(gvals['curiosity']-.5)<abs(cvals['curiosity']-.5)

def test_v1017_05_package_tamper_is_rejected():
    with tempfile.TemporaryDirectory(prefix='v1017_05_') as td:
        td=Path(td);p,pub=prepare_parent(td);c=td/'child';init(c,'CHILD-B');kill(p);cp=td/'child.pub';run(c,'succession-pubkey-export','--out',cp);pkg=td/'p2c.json';run(p,'succession-export','CHILD-B','--out',pkg,'--child-public-key-file',cp)
        q=json.loads(pkg.read_text());q['lineage_certificates'][-1]['payload']['inherited_value_profile']['curiosity']=0.999;pkg.write_text(json.dumps(q),encoding='utf-8')
        r=run(c,'succession-import',pkg,'--parent-trust-file',pub,ok=False);assert 'V1018_PACKAGE_HASH' in r['error'] or 'V1018_PACKAGE_SIGNATURE' in r['error']

def test_v1017_06_nonfresh_child_is_rejected():
    with tempfile.TemporaryDirectory(prefix='v1017_06_') as td:
        td=Path(td);p,pub=prepare_parent(td);c=td/'child';init(c,'CHILD-B');run(c,'soul-experience','vow','0.2','0.2','--theme','CHILD_OWN_PREEXISTING_EXPERIENCE');kill(p);cp=td/'child.pub';run(c,'succession-pubkey-export','--out',cp);pkg=td/'p2c.json';run(p,'succession-export','CHILD-B','--out',pkg,'--child-public-key-file',cp)
        r=run(c,'succession-import',pkg,'--parent-trust-file',pub,ok=False);assert 'V1018_CHILD_NOT_FRESH' in r['error']

def test_v1017_07_wrong_child_and_wrong_parent_trust_are_rejected():
    with tempfile.TemporaryDirectory(prefix='v1017_07_') as td:
        td=Path(td);p,pub=prepare_parent(td);c=td/'wrong';init(c,'WRONG-C');good=td/'good';init(good,'CHILD-B');kill(p);cp=td/'child.pub';run(good,'succession-pubkey-export','--out',cp);pkg=td/'p2c.json';run(p,'succession-export','CHILD-B','--out',pkg,'--child-public-key-file',cp)
        r=run(c,'succession-import',pkg,'--parent-trust-file',pub,ok=False);assert 'V1018_WRONG_CHILD' in r['error']
        # Fresh intended child with a different trust root must also reject.
        fake=td/'fake.pub';fake.write_text('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=',encoding='utf-8')
        r=run(good,'succession-import',pkg,'--parent-trust-file',fake,ok=False);assert 'V1018_PARENT_TRUST_ROOT' in r['error']

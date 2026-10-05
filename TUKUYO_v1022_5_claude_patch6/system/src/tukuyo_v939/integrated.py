"""Real adapter calls into original v837-v846.1 + v937; no model claims beyond tests."""
from __future__ import annotations
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,uuid,io,zipfile,tempfile,subprocess,sys,os,base64


def canon(obj):return (json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()

def require(condition, reason):
    if not condition: raise RuntimeError('INTEGRATION_INVARIANT:'+reason)

def full_status(api,data):
    s=api['bridge'].status(api,data)
    org=api['guard'].audit_checked(Path(data)/'state'/'organism')
    if not org.get('ok'):raise RuntimeError('V8461_GUARDED_ORGANISM_AUDIT_FAILED:'+str(org.get('errors')))
    s['full_integration']={'runtime_modules':{
        'individual_v837_to_v841':'ACTIVE',
        'society_v842':'AVAILABLE',
        'cluster_v843':'AVAILABLE',
        'lineage_v844':'AVAILABLE',
        'ecology_v845':'AVAILABLE',
        'finite_genome_evolution_v846':'AVAILABLE',
        'v846_1_runtime_guard':'INSTALLED_AND_AUDITED',
        'v935_audit_history':'ARCHIVE_ONLY',
        'v937_research':'SHADOW_ONLY'},
        'v846_1_guard':{'ok':org['ok'],'quarantined':org['quarantined'],
                        'state_seq':org['state_seq']},
        'synthetic_research_auto_promotion':False,
        'independent_semantic_evaluation':'PENDING',
        'thirty_day_wallclock':'NOT_ESTABLISHED',
        'historical_key_rotation':'UNPROVEN'}
    return s


def _load_example(api):
    return json.loads((api['v938_root']/'examples/SEMANTIC_TEACH_SAMPLE.json').read_text(encoding='utf-8'))


def run_lab(api,root,*,lab_id=None,include_research=True):
    """Build an isolated, persistent 8-agent laboratory; no access to user's live organism.

    All entities and results below use ORIGINAL upstream implementations, not
    synthetic lookalike adapter classes. Local evaluator keys are NOT third parties.
    """
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False)
    stage='create_individuals';report={'schema':'tukuyo.v939.integrated_lab/1','ok':False,
        'lab_id':lab_id or root.name,'steps':{},'scope':'SYNTHETIC_LOCAL_PROTOCOL_DEMO',
        'independent_evaluation':False,'auto_promotion':False,'live_organism_modified':False}
    o=api['organism'];_runtime_eval=o.evaluate;o.evaluate=lambda state,q:o.s838.evaluate(o._semantic(state),q)
    try:
        s=api['social'];soc=api['society'];cl=api['cluster']
        lin=api['lineage'];eco=api['ecology'];evo=api['evolution'];guard=api['guard']
        roots={f'P{i}':root/'agents'/f'P{i}' for i in range(8)}
        for label,p in roots.items():s.init(p,f'TUKUYO-v939-{label}',initial_energy=100,initial_reserve=2200)
        o.run_life_ticks(roots['P0'],3)
        require(o.audit(roots['P0'])['ok'], 'ORGANISM_AUDIT')
        require(guard.audit_checked(roots['P0']/'organism')['ok'], 'GUARD_AUDIT')
        report['steps']['organism']={'ok':True,'members':8,'tick':3,'guard':True}

        stage='semantic_learning'
        ex=_load_example(api)
        learned=o.learn(roots['P6'],ex['surface'],ex['training'],ex['holdout'],protocol_test_fixture=False)
        require(learned['operator']=='ADD', 'LEARNED_OPERATOR')
        require(o.evaluate(roots['P6'],'3 とけあわせる 2')['answer']==5, 'LEARNING_HOLDOUT')
        report['steps']['semantic_learning']={'ok':True,'learned_operator':learned['operator'],
                                                'positive_evaluation':5}

        stage='society_v842'
        sr=root/'society';members={label:str(p) for label,p in roots.items()}
        soc.init_society(sr,members,society_id='TUKUYO-v939-LAB-SOCIETY')
        soc.capability_announcement(sr,roots['P6'])
        sa=soc.audit(sr,members)
        require(sa['ok'], 'SOCIETY_AUDIT:'+str(sa))
        report['steps']['society']={'ok':True,'members':8,
                                    'announcements':soc.load_registry(sr)['payload']['announcement_count']}

        stage='cluster_v843'
        ids={label:soc._id(p) for label,p in roots.items()}
        roles={role:ids[label] for role,label in zip(cl.ROLES,('P0','P1','P2','P3','P4','P5'))}
        manifest=root/'role_manifest.json';ask,apk=cl.keygen();vsk,vpk=cl.keygen()
        cl.create_role_manifest(manifest,sr,members,roles,[ids['P6'],ids['P7']],ask,apk)
        tasks=[{'id':'CLUSTER-001','query':'3 とけあわせる 2','expected':5}]
        bundles=[cl.run_cluster_task(sr,manifest,members,task) for task in tasks]
        rec=cl.external_verifier_receipt(sr,manifest,tasks,bundles,vsk,vpk)
        result=cl.final_gate(sr,manifest,tasks,bundles,rec)
        require(result['ok'] and result['correct']==1 and result['wrong']==0,'CLUSTER_GATE:'+str(result))
        report['steps']['cluster']={'ok':True,'correct':result['correct'],'wrong':result['wrong'],
              'role_separation':len(set(roles.values())|set([ids['P6'],ids['P7']]))==8,
              'evaluation_authority':'LOCALLY_GENERATED_PROTOCOL_TEST_KEY_NOT_THIRD_PARTY'}
        (root/'cluster_task_receipt.json').write_bytes(canon({'tasks':tasks,'bundle':bundles,'receipt':rec}))

        stage='lineage_v844'
        line=root/'lineage';lin.init_lineage(line,'TUKUYO-v939-LAB-FAMILY')
        child=root/'children'/'CHILD-1';s.init(child,'TUKUYO-v939-CHILD-1')
        cert=lin.reproduce(line,roots['P6'],child,surfaces=[ex['surface']],birth_id='V939-LAB-BIRTH-1')
        line_a=lin.verify_lineage(line)
        inherited=lin.evaluate(child,'3 とけあわせる 2')
        require(line_a['ok'] and line_a['birth_count']==1 and inherited['answer']==5,'LINEAGE:'+str((line_a,inherited)))
        report['steps']['lineage']={'ok':True,'birth_count':line_a['birth_count'],
                     'inherited_answer':inherited['answer'],'private_memory_inherited':False}

        stage='ecology_v845'
        eco_found={k:str(roots[k]) for k in ('P0','P1','P2','P3')}
        traits={k:{'efficiency':v,'cooperation':c} for k,v,c in
                  [('P0',0.2,0.0),('P1',0.7,0.1),('P2',1.0,0.2),('P3',1.6,0.3)]}
        er=root/'ecology';eco.init_ecology(er,line,eco_found,traits)
        eco.step_generation(er)
        ea=eco.audit(er)
        require(ea['ok'] and ea['generation']==1,'ECOLOGY:'+str(ea))
        report['steps']['ecology']={'ok':True,'generation':1,'birth_count':ea['birth_count'],
                                    'death_count':ea['death_count'],'resource_conservation_checked':True}

        stage='evolution_v846'
        evo_found={k:str(roots[k]) for k in ('P4','P5','P6','P7')}
        x={'op':'x'}
        genomes={'P4':x,'P5':{'op':'abs','arg':x},
                 'P6':{'op':'add','left':x,'right':{'op':'const','value':1}},
                 'P7':{'op':'mul','left':x,'right':{'op':'const','value':2}}}
        vr=root/'evolution';evo.init_evolution(vr,line,evo_found,genomes,
            master_seed='V939-LAB-LOCAL-PROTOCOL-SEED',population_size=4)
        evo.step_generation(vr)
        va=evo.audit(vr)
        require(va['ok'] and va['generation']==1,'EVOLUTION:'+str(va))
        report['steps']['evolution']={'ok':True,'generation':va['generation'],
                      'birth_count':va['birth_count'],
                      'structural_innovation_count':va['structural_innovation_count'],
                      'environment':'FIXED_13_CASE_PROTOCOL_FIXTURE'}

        stage='audit_all'
        audit_again={'individuals':all(s.audit(p)['ok'] for p in roots.values()),
              'society':soc.audit(sr,members)['ok'],
              'lineage':lin.verify_lineage(line)['ok'],
              'ecology':eco.audit(er)['ok'],'evolution':evo.audit(vr)['ok'],
              'guard':guard.audit_checked(roots['P0']/'organism')['ok']}
        require(all(audit_again.values()),'CROSS_MODULE_AUDIT:'+str(audit_again))
        report['steps']['fresh_audits']=audit_again

        if include_research:
            stage='shadow_research_v937'
            # Different lab individual, never promoting into any agent.
            organism_before=o.audit(roots['P0'])
            study=api['research'].one('coupled_product',train_seed=93601)
            organism_after=o.audit(roots['P0'])
            require(organism_before==organism_after,'SHADOW_RESEARCH_MUTATED_ORGANISM')
            report['steps']['research']={'ok':True,'task':'coupled_product',
                                         'organism_unchanged':True,'promotion':'BLOCKED'}
        report['ok']=True
    except Exception as err:
        report['failure_stage']=stage
        report['error']=type(err).__name__+':'+str(err)
        raise
    finally:
        o.evaluate=_runtime_eval
        (root/'LAB_REPORT.json').write_bytes(canon(report))
    return report


def audit_lab(api,root):
    """Recompute live evidence, reject falsified local report claims and aliases.

    The lab report is not a third-party signature. This detects post-hoc edits to
    individual report claims; fully rewritten coherent local state still needs
    an independently anchored evaluator to establish provenance.
    """
    root=Path(root).resolve()
    try:
        report_path=root/'LAB_REPORT.json'
        if report_path.is_symlink() or not report_path.is_file():
            return {'ok':False,'error':'LAB_REPORT_ABSENT_OR_SYMLINK'}
        report=json.loads(report_path.read_text(encoding='utf-8'))
        if not report.get('ok'):
            return {'ok':False,'error':'LAB_INCOMPLETE','source':report}
        if report.get('schema')!='tukuyo.v939.integrated_lab/1' or report.get('scope')!='SYNTHETIC_LOCAL_PROTOCOL_DEMO' or report.get('independent_evaluation') is not False or report.get('auto_promotion') is not False or report.get('live_organism_modified') is not False:
            return {'ok':False,'error':'LAB_SCOPE_OR_SCHEMA_MISMATCH'}
        members={f'P{i}':str(root/'agents'/f'P{i}') for i in range(8)}
        s=api['social'];soc=api['society'];lin=api['lineage'];eco=api['ecology'];evo=api['evolution'];guard=api['guard']
        individual=[s.audit(p) for p in members.values()]
        soci=soc.audit(root/'society',members)
        lineage=lin.verify_lineage(root/'lineage')
        ecology=eco.audit(root/'ecology')
        evolution=evo.audit(root/'evolution')
        guarding=guard.audit_checked(root/'agents/P0/organism')
        steps=report.get('steps',{})
        checks={'individuals':all(x.get('ok') for x in individual),
            'society':soci.get('ok'),'lineage':lineage.get('ok'),
            'ecology':ecology.get('ok'),'evolution':evolution.get('ok'),
            'guard':guarding.get('ok')}
        try:
            # The lab can be audited after additional generations: validate
            # claims against the original generation-1 snapshot as lower bounds.
            checks['report_consistency']=(
                steps['organism']['members']==8 and steps['organism']['tick']==3
                and steps['organism']['guard'] is True
                and steps['semantic_learning']['positive_evaluation']==5
                and steps['semantic_learning']['learned_operator']=='ADD'
                and steps['society']['members']==8
                and steps['society']['announcements']==soc.load_registry(root/'society')['payload']['announcement_count']
                and steps['cluster']['correct']==1 and steps['cluster']['wrong']==0
                and steps['cluster']['role_separation'] is True
                and steps['cluster']['evaluation_authority']=='LOCALLY_GENERATED_PROTOCOL_TEST_KEY_NOT_THIRD_PARTY'
                and steps['lineage']['birth_count']==1
                and steps['lineage']['inherited_answer']==5
                and steps['lineage']['private_memory_inherited'] is False
                and lineage['birth_count']>=1
                and steps['ecology']['generation']==1
                and ecology['generation']>=1
                and steps['evolution']['generation']==1
                and evolution['generation']>=1
                and steps['evolution']['environment']=='FIXED_13_CASE_PROTOCOL_FIXTURE'
            )
            if 'research' in steps:
                checks['report_consistency']=(checks['report_consistency'] and
                    steps['research']['promotion']=='BLOCKED' and
                    steps['research']['organism_unchanged'] is True)
        except (KeyError,TypeError,ValueError):
            checks['report_consistency']=False
        try:
            receipt_path=root/'cluster_task_receipt.json'
            if receipt_path.is_symlink():raise ValueError('CLUSTER_RECEIPT_SYMLINK')
            record=json.loads(receipt_path.read_text(encoding='utf-8'))
            if set(record)!={'tasks','bundle','receipt'}:
                raise ValueError('CLUSTER_RECORD_SCHEMA')
            outcome=api['cluster'].final_gate(root/'society',root/'role_manifest.json',
                                               record['tasks'],record['bundle'],record['receipt'])
            checks['cluster']=bool(outcome['ok'] and outcome['wrong']==0 and outcome['correct']==1)
        except Exception:
            checks['cluster']=False
        return {'ok':all(checks.values()),'checks':checks,
                'generation':evolution.get('generation')}
    except Exception as e:return {'ok':False,'error':type(e).__name__+':'+str(e)}


def replay_v935(api):
    """Reexecute the unmodified historical v935 synthetic checkpoint in isolation.

    This is a *historical bounded synthetic test*, not a live-policy upgrade,
    independent semantic assessor, or demonstration of human-level learning.
    """
    from .bootstrap import V935,V935_SHA,safe_extract,OriginError
    if hashlib.sha256(V935.read_bytes()).hexdigest()!=V935_SHA:
        raise OriginError('HISTORICAL_CHAIN_SHA_INVALID')
    with zipfile.ZipFile(V935) as outer:
        index=json.loads(outer.read('TUKUYO_v932_v935_CHAIN_INDEX.json'))
        expected=next(x for x in index['versions'] if x['version']=='v935')
        source=outer.read('versions/'+expected['zip'])
        if hashlib.sha256(source).hexdigest()!=expected['sha256']:
            raise OriginError('V935_SOURCE_NOT_CHAIN_BOUND')
        key=outer.read('trust/TUKUYO_v932_v935_TRUSTED_PUBKEY.txt').decode().strip()
        fingerprint=hashlib.sha256(base64.b64decode(key,validate=True)).hexdigest()
        if fingerprint!=index['trusted_key_fingerprint_sha256']:
            raise OriginError('V935_RELEASE_KEY_FINGERPRINT_MISMATCH')
    with tempfile.TemporaryDirectory(prefix='tukuyo_v939_v935_replay_') as td:
        safe_extract(io.BytesIO(source),Path(td)/'v935',limit=1048576)
        origin=Path(td)/'v935/TUKUYO_v935_HARDENED_DEBUG_CHECKPOINT'
        env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
        v=[sys.executable,'-B','tools/verify_release.py',str(origin),'--trusted-pubkey-b64',key]
        def verify():
            p=subprocess.run(v,cwd=origin,env=env,capture_output=True,text=True,timeout=30)
            if p.returncode!=0:raise RuntimeError('HISTORICAL_V935_RELEASE_INVALID:'+p.stdout[-1000:])
            decoded=json.loads(p.stdout)
            if not decoded.get('ok'):raise RuntimeError('HISTORICAL_V935_RELEASE_INVALID')
            return decoded
        first=verify()
        p=subprocess.run([sys.executable,'-B','run_selftest.py'],cwd=origin,env=env,
                         capture_output=True,text=True,timeout=65)
        if p.returncode!=0:raise RuntimeError('HISTORICAL_V935_SELFTEST_FAILED:'+p.stdout[-1000:]+p.stderr[-1000:])
        second=verify()
        return {'ok':True,'v935_original_sha256':expected['sha256'],
                'release_verified_before_after':first['ok'] and second['ok'],
                'historical_selftest':p.stdout.strip()[-1000:],
                'scope':'HISTORICAL_SYNTHETIC_REPLAY_NOT_LIVE_PROMOTION',
                'third_party_semantic_assessment':False}

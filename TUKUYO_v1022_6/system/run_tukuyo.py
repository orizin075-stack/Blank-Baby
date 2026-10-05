#!/usr/bin/env python3
"""TUKUYO v1022.5 fusion reasoning/recovery experimental CLI; requires Python 3.10+.

Use --data to choose a permanent data root OUTSIDE the signed distribution.
No unrestricted language model or unattended auto-promotion is implemented.
"""
from __future__ import annotations
import os
from pathlib import Path
import argparse,hashlib,json,sys,uuid
sys.dont_write_bytecode=True

# v944-v947 bounded science route
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from tukuyo_v944.gap import search_evidence as v944_search, classify as v944_classify
from tukuyo_v945.primitive import propose as v945_propose
from tukuyo_v953.multigen import evolve as v953_evolve
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from tukuyo_v957.bootstrap import mounted,verify_origins
from tukuyo_v939.integrated import full_status,run_lab,audit_lab,replay_v935
from tukuyo_v943 import epistemic as ep

ROOT=Path(__file__).resolve().parent

def v955_full_status(api,data,migration_trust=None):
    s=full_status(api,data)
    from tukuyo_v955.semantic_guard import installed,check_builtin_semantics,audit_migration,_state_path
    sem=api['organism'].s838;chk=check_builtin_semantics(sem)
    guard={'runtime_guard_installed':installed(sem),'builtin_spec_ok':chk['ok'],'builtin_spec_sha256':chk['spec_sha256']}
    if migration_trust:
        try:guard['migration']=audit_migration(data,api,migration_trust)
        except Exception as e:guard['migration']={'ok':False,'error':type(e).__name__+':'+str(e)}
    else:
        guard['migration']={'ok':None,'status':'EXTERNAL_MIGRATION_TRUST_NOT_SUPPLIED','state_present':_state_path(data).is_file()}
    s['version']='v955';s['semantic_guard_v955']=guard;s['capability_retention_v955']='FROZEN_MULTI_DOMAIN_RETENTION_GATE'
    s['ok']=bool(s.get('ok',True) and guard['runtime_guard_installed'] and guard['builtin_spec_ok'] and (not migration_trust or guard['migration'].get('ok',False)))
    return s

RELEASE_REVISION_FALLBACK='v1022.6'
def release_revision():
    """the release revision recorded in the signed receipt (the startup guard verifies that receipt against the
    external trust anchor); a re-sign with --revision changes what the CLI reports without touching code"""
    try:
        v=json.loads((Path(__file__).resolve().parent/'META'/'RELEASE_RECEIPT.json').read_text(encoding='utf-8'))['payload']['release_revision']
        return v if isinstance(v,str) and v and len(v)<=64 else RELEASE_REVISION_FALLBACK
    except Exception:return RELEASE_REVISION_FALLBACK
def output(obj):
    if isinstance(obj,dict):obj['release_revision']=release_revision()
    print(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,default=str))

def _require_live(data):
    if not (data/'state/integration_state.json').is_file():
        raise FileNotFoundError('NO_INDIVIDUAL: run init first')

def chat(api,data,trust=None,migration_trust=None):
    br=api['bridge'];_require_live(data);v955_full_status(api,data,migration_trust)
    print('TUKUYO v1022.5: bounded meta-reasoning + hardened lineage/ecology. /help for commands.')
    while True:
        try:raw=input('あなた > ').strip()
        except (KeyboardInterrupt,EOFError):print('\n終了');return
        if not raw:continue
        if raw in ('/quit','/exit'):return
        try:
            if raw=='/help':answer='/status /tick N /eval EXPR /exit. Additional modules: run "python run_tukuyo.py lab" in another shell.'
            elif raw=='/status':
                s=v955_full_status(api,data,migration_trust);answer=f"tick {s['organism']['runtime_tick']}, energy {s['organism']['energy']}; guarded={s['full_integration']['v846_1_guard']['ok']}"
            elif raw.startswith('/tick '):
                s=br.tick(api,data,int(raw[6:].strip()));answer=f"tick {s['organism']['runtime_tick']}; energy={s['organism']['energy']}"
            elif raw.startswith('/eval '):answer=json.dumps(br.evaluate(api,data,raw[6:].strip()),ensure_ascii=False)
            elif raw.startswith('/'):
                print('Unknown command; use /help');continue
            else:
                s=full_status(api,data)
                if raw in ('こんにちは','おはよう','こんばんは'):answer=f'{raw}。現在の稼働tickは{s["organism"]["runtime_tick"]}です。'
                else:
                    from tukuyo_v996.conversational_grounding import ingest as conversation_ingest
                    from tukuyo_v1002.cognition import answer as cognitive_answer
                    r=conversation_ingest(data,raw)
                    import re as _re
                    from tukuyo_v1022_llm import bridge as llm_bridge
                    mem=_re.match(r'^(?:覚えて|おぼえて|記憶して|メモして)(?:おいて|ね|ください)?[:：、,\s]+(.{2,400})$',raw)
                    if mem:
                        # claude-patch3: facts taught in conversation go to the knowledge store (source=chat, append-only)
                        from tukuyo_v1001.knowledge import add as knowledge_add
                        kr=knowledge_add(data,mem[1].strip(),source='chat')
                        answer='それはもう覚えています。' if kr.get('duplicate') else f"覚えました（記憶{kr.get('count')}件目）。"
                        print('TUKUYO > '+answer);br.write_chat_log(data,raw,answer);continue
                    # claude-patch2: the proven local core answers first even without an LLM, with its reason
                    cr=llm_bridge.ask(data,raw,mode='chat')
                    if cr.get('source')=='local-proof':
                        answer=str(cr['answer'])+(f"（{cr['explanation']}）" if cr.get('explanation') and cr.get('explanation')!=cr.get('answer') else '')
                    elif cr.get('source')=='none':
                        cr=cognitive_answer(data,raw);answer=str(cr['answer'])+' （未検証）'
                    else:
                        mark={'verified':'','partially_verified':' （一部未検証）','unverified':' （未検証）'}.get(cr.get('status'),'')
                        answer=str(cr['answer'])+mark
            print('TUKUYO > '+answer)
            br.write_chat_log(data,raw,answer)
        except Exception as e:print('ERROR',type(e).__name__+':'+str(e))

def parser():
    p=argparse.ArgumentParser(description='TUKUYO v1022.5 bounded multi-route reasoning + recovery fusion experimental system')
    p.add_argument('--data',type=Path,default=Path(os.environ.get('TUKUYO_DATA_DIR', str(Path.home()/'.tukuyo'/'v999_data'))))
    p.add_argument('--ep-trust-dir',type=Path,help='External pinned local/observer/evaluator/authority public keys. Required after epistemic init.')
    p.add_argument('--cap-trust-dir',type=Path,help='External pinned capability authority key. Required to resolve learned legacy capabilities.')
    p.add_argument('--semantic-migration-trust-file',type=Path,help='External v955 Semantic Migration Authority public key. Used for signed guard migration/audit.')
    p.add_argument('--blind-gap-trust-file',type=Path,help='External v956 Blind Gap Challenge Authority public key.')
    p.add_argument('--primitive-evaluator-trust-file',type=Path,help='External v958 evaluator public key.')
    p.add_argument('--primitive-promotion-trust-file',type=Path,help='External v958 promotion authority public key.')
    p.add_argument('--goal-authority-trust-file',type=Path,help='External v959 Goal Authority public key.')
    p.add_argument('--observer-trust-file',type=Path,help='External v960 Observer public key.')
    p.add_argument('--inheritance-trust-file',type=Path,help='External v962 Inheritance Authority public key.')
    p.add_argument('--family-evaluator-trust-file',type=Path,help='External v966 family evaluator public key.')
    p.add_argument('--family-promotion-trust-file',type=Path,help='External v966 family promotion authority public key.')
    p.add_argument('--runtime-trust-file',type=Path,help='Externally supplied v967 runtime release public key for fresh-process reproduction.')
    sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('verify-origins')
    sub.add_parser('layers')
    sub.add_parser('archive-list')
    x=sub.add_parser('archive-show');x.add_argument('version')
    sub.add_parser('replay-v935',help='Fresh isolated replay of the historical v935 synthetic tests')
    i=sub.add_parser('init');i.add_argument('--individual-id',default='TUKUYO-v1022-001');i.add_argument('--blank-learning',action='store_true')
    sub.add_parser('status');sub.add_parser('audit');sub.add_parser('chat')
    t=sub.add_parser('tick');t.add_argument('count',type=int)
    e=sub.add_parser('eval');e.add_argument('query')
    t=sub.add_parser('teach');t.add_argument('evidence',type=Path);t.add_argument('--apply',action='store_true')
    r=sub.add_parser('research');r.add_argument('--task',choices=('v935_reference','coupled_product','difference_shift'),default='coupled_product');r.add_argument('--seed',type=int,default=93601)
    d=sub.add_parser('diagnose');d.add_argument('queries',nargs='+');d.add_argument('--task',choices=('v935_reference','coupled_product','difference_shift'),default='v935_reference')
    l=sub.add_parser('lab',help='Run every available historical runtime module in a separate lab directory; never mutate the live individual');l.add_argument('--out',type=Path);l.add_argument('--skip-research',action='store_true')
    l=sub.add_parser('lab-audit');l.add_argument('path',type=Path)
    ei=sub.add_parser('ep-init');ei.add_argument('--pin-out',type=Path,required=True)
    ei=sub.add_parser('ep-import');ei.add_argument('surface')
    ei=sub.add_parser('ep-challenge');ei.add_argument('surface');ei.add_argument('contradiction_json',type=Path)
    ei=sub.add_parser('ep-observe');ei.add_argument('surface');ei.add_argument('signed_observation',type=Path)
    ei=sub.add_parser('ep-options');ei.add_argument('surface')
    ei=sub.add_parser('ep-revise');ei.add_argument('surface');ei.add_argument('evaluator_receipt',type=Path);ei.add_argument('authority_receipt',type=Path)
    sub.add_parser('ep-status');sub.add_parser('ep-audit')
    sd=sub.add_parser('science-demo');sd.add_argument('--rows',type=int,default=36)
    sub.add_parser('meta-demo')
    sub.add_parser('meta-generalization-demo')
    sub.add_parser('retention-demo')
    sub.add_parser('semantic-migrate')
    sub.add_parser('semantic-guard-status')
    bg=sub.add_parser('blind-gap-classify');bg.add_argument('commitment',type=Path);bg.add_argument('reveal',type=Path);bg.add_argument('--budget',type=int)
    np=sub.add_parser('novel-primitive-propose');np.add_argument('commitment',type=Path);np.add_argument('reveal',type=Path)
    pi=sub.add_parser('primitive-install');pi.add_argument('proposal',type=Path);pi.add_argument('evaluator_receipt',type=Path);pi.add_argument('promotion_receipt',type=Path)
    pe=sub.add_parser('primitive-eval');pe.add_argument('candidate_sha256');pe.add_argument('a',type=int);pe.add_argument('b',type=int)
    sub.add_parser('primitive-registry-audit')
    sub.add_parser('open-ended-assay')
    sub.add_parser('system-status')
    sub.add_parser('whole-sync')
    sub.add_parser('whole-status')
    sub.add_parser('whole-audit')
    se=sub.add_parser('soul-experience');se.add_argument('kind');se.add_argument('valence',type=float);se.add_argument('importance',type=float);se.add_argument('--theme',default='');se.add_argument('--relation',default='')
    he=sub.add_parser('heart-experience');he.add_argument('kind');he.add_argument('valence',type=float);he.add_argument('importance',type=float);he.add_argument('--theme',default='');he.add_argument('--relation',default='')
    hc=sub.add_parser('heart-choose');hc.add_argument('options',type=Path);hc.add_argument('--context',default='')
    hf=sub.add_parser('heart-feedback');hf.add_argument('action_id');hf.add_argument('outcome_valence',type=float);hf.add_argument('importance',type=float);hf.add_argument('--theme',default='')
    sub.add_parser('heart-status');sub.add_parser('heart-audit')
    sub.add_parser('soul-consolidate');sub.add_parser('soul-deep-audit');sub.add_parser('soul-forget-surface')
    sc=sub.add_parser('soul-continuity-assay');sc.add_argument('options',type=Path);sc.add_argument('--context',default='continuity_assay')
    sub.add_parser('soul-fork-assay');sub.add_parser('soul-fork-audit')
    cc=sub.add_parser('continuity-checkpoint');cc.add_argument('--note',default='')
    ca=sub.add_parser('continuity-anchor-export');ca.add_argument('--out',type=Path,required=True)
    ca=sub.add_parser('continuity-audit');ca.add_argument('--anchor-file',type=Path)
    crs=sub.add_parser('continuity-resume');crs.add_argument('--anchor-file',type=Path)
    sub.add_parser('homeostasis-assess');sub.add_parser('homeostasis-audit')
    sub.add_parser('full-runtime-fork-assay');sub.add_parser('full-runtime-fork-audit')
    sub.add_parser('purpose-integrate');sub.add_parser('purpose-status');sub.add_parser('purpose-audit')
    pc=sub.add_parser('plan-compile');pc.add_argument('--horizon-cycles',type=int,default=3)
    sub.add_parser('plan-status');sub.add_parser('plan-audit')
    pe2=sub.add_parser('plan-execute');pe2.add_argument('--max-steps',type=int)
    sub.add_parser('plan-execution-status');sub.add_parser('plan-execution-audit')
    sub.add_parser('strategy-learn');sub.add_parser('strategy-status');sub.add_parser('strategy-audit')
    ei2=sub.add_parser('env-init');ei2.add_argument('--profile',choices=('TRAIN_A','TRAIN_B','HOLDOUT_A','HOLDOUT_B'),default='TRAIN_A');ei2.add_argument('--seed',type=int,default=99001)
    sub.add_parser('env-observe');ea2=sub.add_parser('env-act');ea2.add_argument('action',choices=('MOVE_FORWARD','MOVE_BACK','GATHER','REST','SHIELD'));sub.add_parser('env-audit')
    sub.add_parser('grounded-init');gs=sub.add_parser('grounded-step');gs.add_argument('action',choices=('MOVE_FORWARD','MOVE_BACK','GATHER','REST','SHIELD'));sub.add_parser('grounded-status');sub.add_parser('grounded-audit')
    sub.add_parser('holdout-assay');sub.add_parser('holdout-audit')
    sub.add_parser('relation-sync');rs=sub.add_parser('relation-status');rs.add_argument('--peer');sub.add_parser('relation-audit')
    rc=sub.add_parser('relation-choose');rc.add_argument('peer');rc.add_argument('options',type=Path);rc.add_argument('--context',default='')
    si=sub.add_parser('semantic-interpret');si.add_argument('text');si.add_argument('--relation',default='')
    sr=sub.add_parser('semantic-record');sr.add_argument('text');sr.add_argument('--relation',default='')
    sub.add_parser('semantic-status');sub.add_parser('semantic-audit')
    sub.add_parser('peer-sync');ps=sub.add_parser('peer-status');ps.add_argument('--peer');sub.add_parser('peer-audit')
    pc=sub.add_parser('peer-choose');pc.add_argument('peer');pc.add_argument('options',type=Path);pc.add_argument('--context',default='')
    ci2=sub.add_parser('conversation-ingest');ci2.add_argument('text');ci2.add_argument('--relation',default='')
    si2=sub.add_parser('semantic-infer');si2.add_argument('text');si2.add_argument('--relation',default='')
    sub.add_parser('semantic-infer-audit')
    sub.add_parser('adaptive-policy-assay');sub.add_parser('adaptive-policy-audit')
    sub.add_parser('soul-identity-sync');sub.add_parser('soul-identity-status');sub.add_parser('soul-identity-audit')
    ka=sub.add_parser('knowledge-add');ka.add_argument('text');ka.add_argument('--source',default='user')
    ks=sub.add_parser('knowledge-search');ks.add_argument('query');ks.add_argument('--k',type=int,default=5)
    cq=sub.add_parser('cognitive-query');cq.add_argument('query')
    sub.add_parser('cognitive-benchmark')
    dq=sub.add_parser('deliberate');dq.add_argument('query');dq.add_argument('--max-steps',type=int,default=4)
    vq=sub.add_parser('verified-query');vq.add_argument('query');vq.add_argument('--samples',type=int,default=3)
    sub.add_parser('calibration-assay')
    cr2=sub.add_parser('core-reason');cr2.add_argument('text')
    mc=sub.add_parser('memory-compact');mc.add_argument('--retain',type=int,default=128)
    sub.add_parser('memory-compact-audit')
    sub.add_parser('legacy-integration-audit')
    sub.add_parser('research-agent-assay');sub.add_parser('research-agent-audit')
    sub.add_parser('organism2-init')
    ou=sub.add_parser('organism2-update');ou.add_argument('event',choices=('COGNITIVE_WORK','REST','SOCIAL_SUPPORT','ISOLATION','DISCOVERY','INJURY','MAINTENANCE'));ou.add_argument('--amount',type=float,default=.2)
    op=sub.add_parser('organism2-preserve');op.add_argument('options',type=Path)
    sub.add_parser('organism2-status');sub.add_parser('organism2-audit')
    lc=sub.add_parser('living-cycle');lc.add_argument('--query',default='What should I do next?')
    sub.add_parser('living-audit')
    ss2=sub.add_parser('successor-seed');ss2.add_argument('successor_id')
    lla=sub.add_parser('long-life-assay');lla.add_argument('--cycles',type=int,default=1)
    sub.add_parser('long-life-audit')
    rt=sub.add_parser('realtime-start');rt.add_argument('--profile',choices=('24h','72h','7d'),default='24h');rt.add_argument('--target-seconds',type=int);rt.add_argument('--note',default='')
    rtt=sub.add_parser('realtime-tick');rtt.add_argument('--note',default='')
    sub.add_parser('realtime-status')
    rta=sub.add_parser('realtime-anchor-export');rta.add_argument('--out',type=Path,required=True)
    rtw=sub.add_parser('realtime-witness-request');rtw.add_argument('--out',type=Path,required=True)
    rtaud=sub.add_parser('realtime-audit');rtaud.add_argument('--anchor-file',type=Path);rtaud.add_argument('--start-witness',type=Path);rtaud.add_argument('--end-witness',type=Path);rtaud.add_argument('--witness-trust-file',type=Path);rtaud.add_argument('--require-complete',action='store_true')
    rcp=sub.add_parser('recovery-checkpoint');rcp.add_argument('--note',default='')
    rca=sub.add_parser('recovery-audit');rca.add_argument('checkpoint',type=Path);rca.add_argument('--trust-file',type=Path)
    rcr=sub.add_parser('recovery-restore');rcr.add_argument('checkpoint',type=Path);rcr.add_argument('--trust-file',type=Path);rcr.add_argument('--anchor-file',type=Path);rcr.add_argument('--dry-run',action='store_true')
    sub.add_parser('recovery-status')
    lcs=sub.add_parser('continuity-campaign-start');lcs.add_argument('--profile',choices=('24h','72h','7d'),default='24h');lcs.add_argument('--target-seconds',type=int);lcs.add_argument('--tick-seconds',type=int,default=300);lcs.add_argument('--checkpoint-seconds',type=int,default=3600);lcs.add_argument('--note',default='')
    lcstep=sub.add_parser('continuity-campaign-step');lcstep.add_argument('--note',default='');lcstep.add_argument('--force-checkpoint',action='store_true')
    sub.add_parser('continuity-campaign-status')
    lcend=sub.add_parser('continuity-campaign-end-request');lcend.add_argument('--out',type=Path)
    lcwr=sub.add_parser('continuity-campaign-witness-request');lcwr.add_argument('--out',type=Path,required=True)
    lcwa=sub.add_parser('continuity-campaign-witness-record');lcwa.add_argument('receipt',type=Path);lcwa.add_argument('--witness-trust-file',type=Path,required=True)
    lcaud=sub.add_parser('continuity-campaign-audit');lcaud.add_argument('--start-witness',type=Path);lcaud.add_argument('--end-witness',type=Path);lcaud.add_argument('--witness-trust-file',type=Path);lcaud.add_argument('--require-complete',action='store_true')
    lcev=sub.add_parser('continuity-campaign-evidence');lcev.add_argument('--out',type=Path,required=True);lcev.add_argument('--start-witness',type=Path);lcev.add_argument('--end-witness',type=Path);lcev.add_argument('--witness-trust-file',type=Path);lcev.add_argument('--require-complete',action='store_true')
    le=sub.add_parser('living-episode');le.add_argument('kind');le.add_argument('valence',type=float);le.add_argument('importance',type=float);le.add_argument('--theme',default='');le.add_argument('--relation',default='');le.add_argument('--query',default='');le.add_argument('--options',type=Path);le.add_argument('--note',default='')
    sub.add_parser('living-continuity-status');sub.add_parser('living-continuity-audit');sub.add_parser('living-gate-assay')
    lga=sub.add_parser('living-gate-audit');lga.add_argument('--start-witness',type=Path);lga.add_argument('--end-witness',type=Path);lga.add_argument('--witness-trust-file',type=Path)
    ee=sub.add_parser('endurance-evidence-export');ee.add_argument('--out',type=Path,required=True);ee.add_argument('--start-witness',type=Path,required=True);ee.add_argument('--end-witness',type=Path,required=True);ee.add_argument('--witness-trust-file',type=Path,required=True)
    ea=sub.add_parser('endurance-evidence-audit');ea.add_argument('evidence',type=Path);ea.add_argument('--witness-trust-file',type=Path,required=True);ea.add_argument('--profile',choices=('24h','72h','7d'))
    er=sub.add_parser('endurance-route-evaluate');er.add_argument('evidence',type=Path,nargs='+');er.add_argument('--witness-trust-file',type=Path,required=True)
    exi=sub.add_parser('endurance-exec-init');exi.add_argument('--profile',choices=('24h','72h','7d'),default='24h');exi.add_argument('--target-seconds',type=int);exi.add_argument('--tick-seconds',type=int,default=300);exi.add_argument('--checkpoint-seconds',type=int,default=3600);exi.add_argument('--witness-seconds',type=int);exi.add_argument('--living-seconds',type=int,default=3600);exi.add_argument('--note',default='')
    exp=sub.add_parser('endurance-exec-pump');exp.add_argument('--note',default='')
    exw=sub.add_parser('endurance-exec-accept-witness');exw.add_argument('receipt',type=Path);exw.add_argument('--witness-trust-file',type=Path,required=True)
    exs=sub.add_parser('endurance-exec-status');exs.add_argument('--witness-trust-file',type=Path)
    exa=sub.add_parser('endurance-exec-audit');exa.add_argument('--witness-trust-file',type=Path)
    exr=sub.add_parser('endurance-exec-resume');exr.add_argument('--witness-trust-file',type=Path);exr.add_argument('--note',default='')
    exb=sub.add_parser('endurance-exec-abort');exb.add_argument('--reason',default='OPERATOR_ABORT')
    efa=sub.add_parser('endurance-failure-evidence-audit');efa.add_argument('evidence',type=Path);efa.add_argument('--witness-trust-file',type=Path)
    rex=sub.add_parser('endurance-repro-export');rex.add_argument('--out',type=Path,required=True);rex.add_argument('--witness-trust-file',type=Path,required=True)
    chi=sub.add_parser('endurance-challenge-init');chi.add_argument('--challenge-file',type=Path,required=True);chi.add_argument('--challenge-trust-file',type=Path,required=True);chi.add_argument('--profile',choices=('24h','72h','7d'),default='24h');chi.add_argument('--target-seconds',type=int);chi.add_argument('--tick-seconds',type=int,default=300);chi.add_argument('--checkpoint-seconds',type=int,default=3600);chi.add_argument('--witness-seconds',type=int);chi.add_argument('--living-seconds',type=int,default=3600);chi.add_argument('--note',default='')
    cha=sub.add_parser('endurance-challenge-audit');cha.add_argument('--challenge-trust-file',type=Path)
    chrp=sub.add_parser('endurance-challenge-repro-export');chrp.add_argument('--out',type=Path,required=True);chrp.add_argument('--witness-trust-file',type=Path,required=True);chrp.add_argument('--challenge-trust-file',type=Path,required=True)
    ag=sub.add_parser('agenda-propose');ag.add_argument('challenges',type=Path);ag.add_argument('--out',type=Path)
    aa=sub.add_parser('agenda-authorize');aa.add_argument('agenda',type=Path);aa.add_argument('receipt',type=Path)
    cp=sub.add_parser('campaign-run');cp.add_argument('spec',type=Path);cp.add_argument('observations',type=Path,nargs='+')
    sub.add_parser('improver-compare')
    ie=sub.add_parser('inherit-export');ie.add_argument('candidate_sha256');ie.add_argument('parent_id');ie.add_argument('child_id');ie.add_argument('--out',type=Path,required=True)
    ii=sub.add_parser('inherit-import');ii.add_argument('bundle',type=Path);ii.add_argument('receipt',type=Path);ii.add_argument('child_id')
    iv=sub.add_parser('inherit-eval');iv.add_argument('candidate_sha256');iv.add_argument('a',type=int);iv.add_argument('b',type=int)
    fr=sub.add_parser('family-propose');fr.add_argument('rows',type=Path);fr.add_argument('ceiling_evidence',type=Path);fr.add_argument('--out',type=Path)
    fv=sub.add_parser('family-promote-verify');fv.add_argument('proposal',type=Path);fv.add_argument('evaluator_receipt',type=Path);fv.add_argument('promotion_receipt',type=Path)
    fe=sub.add_parser('family-eval');fe.add_argument('candidate_sha256');fe.add_argument('a',type=int);fe.add_argument('b',type=int)
    sub.add_parser('reproduce-current')
    so=sub.add_parser('society-send');so.add_argument('recipient');so.add_argument('--message',default='');so.add_argument('--out',type=Path,required=True)
    srx=sub.add_parser('society-receive');srx.add_argument('packet',type=Path);srx.add_argument('--ack-out',type=Path,required=True);srx.add_argument('--valence',type=float,default=0.0);srx.add_argument('--importance',type=float,default=0.45);srx.add_argument('--theme',default='social_exchange')
    sax=sub.add_parser('society-ack');sax.add_argument('packet',type=Path);sax.add_argument('ack',type=Path);sax.add_argument('--valence',type=float,default=0.2);sax.add_argument('--importance',type=float,default=0.35);sax.add_argument('--theme',default='social_acknowledgement')
    sub.add_parser('society-status');sub.add_parser('society-audit');sub.add_parser('society-sync')
    sga=sub.add_parser('society-gate-assay');sga.add_argument('peer_b_data',type=Path);sga.add_argument('peer_c_data',type=Path)
    sub.add_parser('succession-founder-init')
    spe=sub.add_parser('succession-pubkey-export');spe.add_argument('--out',type=Path,required=True)
    sex=sub.add_parser('succession-export');sex.add_argument('child_id');sex.add_argument('--out',type=Path,required=True);sex.add_argument('--child-public-key-file',type=Path,required=True)
    sim=sub.add_parser('succession-import');sim.add_argument('package',type=Path);sim.add_argument('--parent-trust-file',type=Path,required=True)
    sub.add_parser('succession-status');sub.add_parser('succession-audit')
    sgg=sub.add_parser('succession-gate-summary');sgg.add_argument('child_data',type=Path);sgg.add_argument('grandchild_data',type=Path)
    sga17=sub.add_parser('succession-gate-assay');sga17.add_argument('child_data',type=Path);sga17.add_argument('child_id');sga17.add_argument('grandchild_data',type=Path);sga17.add_argument('grandchild_id')
    evs=sub.add_parser('evolution-select');evs.add_argument('environment',choices=('resource','research','social','volatile'));evs.add_argument('--population',type=int,default=11);evs.add_argument('--seed',default='v1019')
    eve=sub.add_parser('evolution-export');eve.add_argument('child_id');eve.add_argument('--out',type=Path,required=True);eve.add_argument('--child-public-key-file',type=Path,required=True)
    evi=sub.add_parser('evolution-import');evi.add_argument('package',type=Path);evi.add_argument('--parent-trust-file',type=Path,required=True)
    sub.add_parser('evolution-status');sub.add_parser('evolution-audit')
    evg=sub.add_parser('evolution-gate-summary');evg.add_argument('child_data',type=Path);evg.add_argument('grandchild_data',type=Path)
    ec=sub.add_parser('population-init');ec.add_argument('--seed',default='v1020');ec.add_argument('--capacity',type=int,default=240000);ec.add_argument('--regeneration',type=int,default=50000);ec.add_argument('--max-population',type=int,default=24);ec.add_argument('--max-age',type=int,default=18);ec.add_argument('--founders',type=int,default=3);ec.add_argument('--no-cooperation',action='store_true')
    ec=sub.add_parser('population-join');ec.add_argument('source_data',type=Path);ec.add_argument('--source-trust-file',type=Path,required=True);ec.add_argument('--founders',type=int,default=3)
    ec=sub.add_parser('population-step');ec.add_argument('environment',choices=('resource','research','social','volatile'));ec.add_argument('--ticks',type=int,default=1)
    sub.add_parser('population-status');sub.add_parser('population-audit')
    rb=sub.add_parser('runtime-ecology-init');rb.add_argument('--families',type=int,default=4);rb.add_argument('--seed',default='v1021');rb.add_argument('--regeneration',type=int,default=240000);rb.add_argument('--max-age',type=int,default=8)
    rb=sub.add_parser('runtime-ecology-step');rb.add_argument('environment',choices=('resource','research','social','volatile'));rb.add_argument('--ticks',type=int,default=1)
    sub.add_parser('runtime-ecology-status');sub.add_parser('runtime-ecology-audit');sub.add_parser('runtime-ecology-recover-cache')
    c=sub.add_parser('think');c.add_argument('query');c.add_argument('--formal-task',type=Path)
    c=sub.add_parser('llm-ask');c.add_argument('query');c.add_argument('--no-local-first',action='store_true')
    c=sub.add_parser('llm-teach');c.add_argument('questions',type=Path)
    sub.add_parser('llm-status');sub.add_parser('llm-audit')
    c=sub.add_parser('self-study');c.add_argument('--max',type=int,default=20);c.add_argument('--dry-run',action='store_true');c.add_argument('--questions',type=Path)
    c=sub.add_parser('dialogue-learn');c.add_argument('bundle',type=Path);c.add_argument('--teacher')
    sub.add_parser('learning-status');sub.add_parser('learning-audit')
    c=sub.add_parser('metabolism-init');c.add_argument('--families',type=int,default=4);c.add_argument('--seed',default='v1022');c.add_argument('--reservoir',type=int,default=20000);c.add_argument('--regeneration',type=int,default=0);c.add_argument('--max-age',type=int,default=32);c.add_argument('--no-learning',action='store_true');c.add_argument('--no-actions',action='store_true');c.add_argument('--research-world',action='store_true',help='claude-patch5: each family lives next to a hidden-rule device; income only from understanding it')
    c=sub.add_parser('metabolism-step');c.add_argument('--ticks',type=int,default=1)
    sub.add_parser('metabolism-status');sub.add_parser('metabolism-audit')
    c=sub.add_parser('research-run',help='claude-patch5 V1023r preview: one research expedition into a hidden-rule world');c.add_argument('--world',default='W1');c.add_argument('--ticks',type=int,default=120);c.add_argument('--regime',choices=('costly_failure','safe_failure'),default='costly_failure');c.add_argument('--tier',type=int,choices=(1,2,3,4,5));c.add_argument('--noise',type=float,choices=(0.0,0.05,0.1))
    sub.add_parser('research-status');sub.add_parser('research-audit')
    c=sub.add_parser('research-ecology',help='Compare research / random experiments / trial-and-error / naive / oracle on fresh worlds; writes only --out');c.add_argument('--seeds',type=int,default=10);c.add_argument('--start',type=int,default=50000);c.add_argument('--key');c.add_argument('--out',type=Path)
    c=sub.add_parser('runtime-trust-rebind');c.add_argument('--previous-trust-file',type=Path,required=True)
    cr=sub.add_parser('cap-request');cr.add_argument('surface');cr.add_argument('--out',type=Path,required=True)
    ci=sub.add_parser('cap-install');ci.add_argument('request',type=Path);ci.add_argument('receipt',type=Path)
    social=sub.add_parser('social');ss=social.add_subparsers(dest='social_cmd',required=True)
    x=ss.add_parser('send');x.add_argument('recipient');x.add_argument('--message',default='');x.add_argument('--out',required=True,type=Path)
    x=ss.add_parser('receive');x.add_argument('packet',type=Path);x.add_argument('--ack-out',required=True,type=Path)
    x=ss.add_parser('ack');x.add_argument('packet',type=Path);x.add_argument('ack',type=Path)
    x=ss.add_parser('peer');x.add_argument('peer');x.add_argument('--private',action='store_true')
    return p

def _main(argv=None):
    args=parser().parse_args(argv)
    data=args.data.resolve()
    try:
        if args.cmd not in ('archive-list','archive-show'):
            from tukuyo_v977.startup_guard import verify_distribution
            verify_distribution(ROOT,args.runtime_trust_file)
            # Restoring a verified checkpoint must remain possible when the
            # live owner or a nested child is damaged. Validate the checkpoint
            # in a stage before consulting or replaying the damaged live tree.
            if args.cmd=='recovery-restore':
                from tukuyo_v1014.recovery import restore
                res=restore(data,args.checkpoint,args.trust_file,args.anchor_file,args.dry_run)
                output(res)
                return 0 if res.get('ok') else 1
            from tukuyo_v1014.recovery import recover_incomplete_restore
            recover_incomplete_restore(data)
            if args.cmd=='runtime-ecology-recover-cache' and args.runtime_trust_file is None:
                raise ValueError('V1021_EXTERNAL_RUNTIME_TRUST_REQUIRED')
            from tukuyo_v1019.transaction import recover as lineage_recover
            lineage_recover(data)
            from tukuyo_v1014_2.crash_recovery import recover_startup
            startup_recovery=recover_startup(data)
            if not startup_recovery.get('ok'):
                raise ValueError('STARTUP_CRASH_RECOVERY:'+','.join(startup_recovery.get('errors',[])[:4]))
            from tukuyo_v1018.succession import ensure_state as v1018_ensure_state
            succession_recovery={'recovered':False}
            if (data/'state/integration_state.json').is_file():
                _,repaired=v1018_ensure_state(data); succession_recovery={'recovered':repaired}
                from tukuyo_v1019.evolution import ensure_state as evolution_ensure
                evolution_state_file=data/'v1019/EVOLUTION_STATE.json'
                if (data/'v1019/commits').is_dir():
                    missing_evolution=not evolution_state_file.is_file()
                    evolution_ensure(data);repaired=repaired or missing_evolution
                from tukuyo_v1020.ecology import ensure_state as population_ensure,was_initialized as population_exists
                if population_exists(data):population_ensure(data)
                if (data/'v1021').exists():
                    from tukuyo_v1021.runtime_bridge import preflight
                    if args.cmd!='runtime-ecology-recover-cache':preflight(data)
                    if args.cmd in ('population-init','population-join','population-step'):
                        raise ValueError('V1021_MANAGED_POPULATION_USE_RUNTIME_ECOLOGY_COMMAND')
                if (data/'v1022/commits').exists():
                    from tukuyo_v1022.cognition import state as cognition_state
                    cognition_state(data)
                if (data/'v1022_ecology/commits').exists():
                    from tukuyo_v1022.metabolism import preflight as metabolism_preflight
                    metabolism_preflight(data)
                if repaired and args.cmd!='runtime-ecology-recover-cache' and (data/'v977/UNIFIED_STATE.json').is_file():
                    from tukuyo_v977.whole_state import sync as _v1018_whole_sync
                    _v1018_whole_sync(data)
        from tukuyo_v1019.lifecycle import guard_command
        guard_command(data,args.cmd)
        if args.cmd in ('archive-list','archive-show'):
            idx=json.loads((ROOT/'RESEARCH_LAYER_INDEX.json').read_text(encoding='utf-8'))
            if args.cmd=='archive-list':output({'ok':True,'release_count':idx['release_count'],'versions':[x['version'] for x in idx['records']],'execution_mode':'ARCHIVAL_ISOLATED'});return 0
            record=next((x for x in idx['records'] if x['version']==args.version),None)
            if record is None:output({'ok':False,'error':'UNKNOWN_VERSION'});return 1
            archive=ROOT/record['archive']
            got=hashlib.sha256(archive.read_bytes()).hexdigest()
            if got!=record['sha256']:output({'ok':False,'error':'ARCHIVE_HASH_MISMATCH'});return 1
            output({'ok':True,'record':record});return 0
        if args.cmd=='verify-origins':output({'ok':True,'origins':verify_origins()});return 0
        if args.cap_trust_dir: os.environ['TUKUYO_CAP_TRUST_DIR']=str(args.cap_trust_dir.resolve())
        else: os.environ.pop('TUKUYO_CAP_TRUST_DIR',None)
        with mounted() as api:
            bridge=api['bridge']
            if args.ep_trust_dir and not ep.roots(data).exists() and args.cmd!='ep-init':raise ValueError('EP_STATE_MISSING_WITH_EXTERNAL_PIN')
            if ep.roots(data).exists() and args.cmd!='ep-init':
                if not args.ep_trust_dir:raise ValueError('EP_EXTERNAL_TRUST_DIR_REQUIRED')
                ep.audit(data,args.ep_trust_dir)
                native_evaluate=bridge.evaluate
                bridge.evaluate=lambda local_api,local_data,q: ep.gated_evaluate(local_data,args.ep_trust_dir,q,lambda:native_evaluate(local_api,local_data,q))
            if args.cmd=='replay-v935':output(replay_v935(api));return 0
            if args.cmd=='layers':
                output({'ok':True,'loaded':sorted(x for x in api if x in ('social','organism','research','learner','guard','society','cluster','lineage','ecology','evolution')),
                        'v846_1_guard_installed':api['guard']._INSTALLED,
                        'auto_promotion':False,'external_evaluator':False,
                        'v935_audit_history':'PRESERVED_ARCHIVE_ONLY'})
                return 0
            if args.cmd=='init':
                res=bridge.init(api,data,args.individual_id)
                from tukuyo_v977.whole_state import sync as v977_sync
                if args.semantic_migration_trust_file:
                    from tukuyo_v955.semantic_guard import migrate,_state_path
                    if not _state_path(data).is_file():migrate(data,api,args.semantic_migration_trust_file)
                v977_sync(data)
                from tukuyo_v989.temporal_identity import sync_transitions as v989_sync
                v989_sync(data)
                # v1015 living state is a Whole-State component, so it must exist
                # before the final unified-state seal. Otherwise the first command
                # after init would create it lazily and look like component drift.
                from tukuyo_v1015.living_continuity import ensure_state as v1015_ensure_state
                v1015_ensure_state(data)
                from tukuyo_v1016.society import ensure_state as v1016_ensure_society
                v1016_ensure_society(data)
                from tukuyo_v1018.succession import ensure_state as v1018_ensure_succession
                v1018_ensure_succession(data)
                from tukuyo_v1019.evolution import ensure_state as v1019_ensure_evolution
                v1019_ensure_evolution(data);v977_sync(data)
                from tukuyo_v1022.cognition import install_seed
                if not args.blank_learning:install_seed(data)
                res=v955_full_status(api,data,args.semantic_migration_trust_file)
                res['version']='v1019'
            elif args.cmd=='ep-init':
                _require_live(data)
                res=ep.init(data,args.pin_out)
            elif args.cmd in ('ep-import','ep-challenge','ep-observe','ep-options','ep-revise','ep-status','ep-audit'):
                _require_live(data)
                if not args.ep_trust_dir:raise ValueError('EP_EXTERNAL_TRUST_DIR_REQUIRED')
                if args.cmd=='ep-import':res=ep.import_native(data,args.ep_trust_dir,args.surface)
                elif args.cmd=='ep-challenge':res=ep.challenge(data,args.ep_trust_dir,args.surface,json.loads(args.contradiction_json.read_text(encoding='utf-8')))
                elif args.cmd=='ep-observe':res=ep.observation(data,args.ep_trust_dir,args.surface,args.signed_observation)
                elif args.cmd=='ep-options':res={'ok':True,'options':ep.expected_receipts(data,args.ep_trust_dir,args.surface)}
                elif args.cmd=='ep-revise':
                    res=ep.revise(data,args.ep_trust_dir,args.surface,args.evaluator_receipt,args.authority_receipt)
                    from tukuyo_v967.integrated_system import append_event
                    append_event(data,'EPISTEMIC_REVISION',res)
                elif args.cmd=='ep-status':res=ep.status(data,args.ep_trust_dir)
                else:res=ep.audit(data,args.ep_trust_dir)
            elif args.cmd=='meta-demo':
                res={'ok':True,'meta':v953_evolve(3)}
            elif args.cmd=='meta-generalization-demo':
                from tukuyo_v954.generalization import propose_generalizing
                res={'ok':True,'meta_generalization':propose_generalizing()}
            elif args.cmd=='retention-demo':
                from tukuyo_v955.retention import demo
                res={'ok':True,'retention':demo()}
            elif args.cmd=='semantic-migrate':
                from tukuyo_v955.semantic_guard import migrate
                _require_live(data)
                if not args.semantic_migration_trust_file:raise ValueError('SEMANTIC_MIGRATION_TRUST_FILE_REQUIRED')
                res=migrate(data,api,args.semantic_migration_trust_file)
                from tukuyo_v967.integrated_system import append_event
                append_event(data,'SEMANTIC_GUARD_MIGRATION',res)
            elif args.cmd=='semantic-guard-status':
                from tukuyo_v955.semantic_guard import audit_migration,installed,check_builtin_semantics
                _require_live(data)
                if args.semantic_migration_trust_file:res=audit_migration(data,api,args.semantic_migration_trust_file)
                else:
                    s838=api['organism'].s838;chk=check_builtin_semantics(s838);res={'ok':bool(installed(s838) and chk['ok']),'status':'RUNTIME_GUARD_ACTIVE_NO_MIGRATION_AUDIT','guard_installed':installed(s838),'builtin_spec':chk}
            elif args.cmd=='blind-gap-classify':
                from tukuyo_v956.blind_gap import classify_committed
                if not args.blind_gap_trust_file:raise ValueError('BLIND_GAP_TRUST_FILE_REQUIRED')
                res=classify_committed(args.commitment,args.reveal,args.blind_gap_trust_file,args.budget)
            elif args.cmd=='novel-primitive-propose':
                from tukuyo_v956.blind_gap import classify_committed,verify_reveal
                from tukuyo_v957.novel_primitive import propose
                if not args.blind_gap_trust_file:raise ValueError('BLIND_GAP_TRUST_FILE_REQUIRED')
                gap=classify_committed(args.commitment,args.reveal,args.blind_gap_trust_file)
                rows=verify_reveal(args.commitment,args.reveal,args.blind_gap_trust_file)['rows']
                res={'ok':True,'gap':gap,'proposal':propose(rows,gap)}
            elif args.cmd=='primitive-install':
                from tukuyo_v958.promotion import install
                if not args.primitive_evaluator_trust_file or not args.primitive_promotion_trust_file:raise ValueError('V958_EXTERNAL_TRUST_REQUIRED')
                res={'ok':True,'entry':install(data,json.loads(args.proposal.read_text()),json.loads(args.evaluator_receipt.read_text()),json.loads(args.promotion_receipt.read_text()),args.primitive_evaluator_trust_file,args.primitive_promotion_trust_file)}
                from tukuyo_v967.integrated_system import append_event
                append_event(data,'V958_PRIMITIVE_INSTALLED',res['entry'])
            elif args.cmd=='primitive-eval':
                from tukuyo_v958.promotion import evaluate_registry
                res=evaluate_registry(data,args.candidate_sha256,args.a,args.b)
            elif args.cmd=='primitive-registry-audit':
                from tukuyo_v958.promotion import audit_registry
                res=audit_registry(data)
            elif args.cmd=='open-ended-assay':
                from tukuyo_v964.assay import run_assay
                res=run_assay()
                from tukuyo_v967.integrated_system import append_event
                append_event(data,'OPEN_ENDED_ASSAY',res)
            elif args.cmd=='system-status':
                from tukuyo_v967.integrated_system import system_status
                from tukuyo_v977.whole_state import status as whole_status
                base=v955_full_status(api,data,args.semantic_migration_trust_file) if (data/'state/integration_state.json').is_file() else None
                res=system_status(data,base)
                res['version']='v1019';res['integrated_research_base_version']='v967'
                if base is not None: res['whole_individual_v977']=whole_status(data,base)
                if (data/'v984'/'FULL_RUNTIME_FORK_ASSAY.json').is_file():
                    from tukuyo_v984.full_fork import audit as full_fork_audit
                    res['full_runtime_fork_v984']=full_fork_audit(data)
                if (data/'v985'/'NARRATIVE_PURPOSE_STATE.json').is_file():
                    from tukuyo_v985.narrative_purpose import status as purpose_status
                    res['narrative_purpose_v985']=purpose_status(data)
                if (data/'v986'/'LONG_HORIZON_PLAN.json').is_file():
                    from tukuyo_v986.long_horizon_plan import status as plan_status
                    res['long_horizon_plan_v986']=plan_status(data)
                if (data/'v987'/'PLAN_EXECUTION_STATE.json').is_file():
                    from tukuyo_v987.plan_executor import status as execution_status
                    res['plan_execution_v987']=execution_status(data)
                if (data/'v1013'/'REALTIME_RUN.json').is_file():
                    from tukuyo_v1013.realtime_continuity import status as realtime_status
                    res['realtime_continuity_v1013']=realtime_status(data)
                if (data/'v1016'/'SOCIETY_STATE.json').is_file():
                    from tukuyo_v1016.society import status as society_status
                    res['multi_agent_society_v1016']=society_status(data)
                if (data/'v1017'/'SUCCESSION_STATE.json').is_file():
                    from tukuyo_v1017.succession import status as succession_status
                    res['parent_successor_grandchild_v1017']=succession_status(data)
                if (data/'v988'/'STRATEGY_STATE.json').is_file():
                    from tukuyo_v988.strategy_learning import status as strategy_status
                    res['strategy_learning_v988']=strategy_status(data)
                if (data/'v989'/'TEMPORAL_IDENTITY.json').is_file():
                    from tukuyo_v989.temporal_identity import status as identity_status
                    res['temporal_identity_v989']=identity_status(data)
                if (data/'v990'/'ENVIRONMENT_STATE.json').is_file():
                    from tukuyo_v990.closed_environment import observe as env_observe,audit as env_audit
                    res['closed_environment_v990']={'observation':env_observe(data),'audit':env_audit(data)}
                if (data/'v991'/'GROUNDED_ORGANISM_STATE.json').is_file():
                    from tukuyo_v991.grounded_organism import status as grounded_status
                    res['grounded_organism_v991']=grounded_status(data)
                if (data/'v992'/'HOLDOUT_ASSAY.json').is_file():
                    from tukuyo_v992.holdout import audit as holdout_audit
                    res['holdout_v992']=holdout_audit(data)
                if (data/'v993'/'RELATION_BOUND_STATE.json').is_file():
                    from tukuyo_v993.relation_bound import status as relation_status
                    res['relation_bound_v993']=relation_status(data)
                if (data/'v994'/'SEMANTIC_EVENTS.json').is_file():
                    from tukuyo_v994.constructive_semantics import status as semantic_status
                    res['constructive_semantics_v994']=semantic_status(data)
                if (data/'v995'/'OTHER_AGENT_MODELS.json').is_file():
                    from tukuyo_v995.other_agent_trust import status as peer_status
                    res['other_agent_trust_v995']=peer_status(data)
                if ((data/'v996'/'CONVERSATION_GROUNDING_EVENTS.jsonl').is_file() or (data/'v996'/'CONVERSATION_EVENT_HEAD.json').is_file()):
                    from tukuyo_v996.conversational_grounding import audit as conversation_audit
                    res['conversation_grounding_v996']=conversation_audit(data)
                if ((data/'v998'/'SEMANTIC_INFERENCE_EVENTS.jsonl').is_file() or (data/'v998'/'SEMANTIC_EVENT_HEAD.json').is_file()):
                    from tukuyo_v998.semantic_inference import audit as semantic_infer_audit
                    res['semantic_inference_v998']=semantic_infer_audit(data)
                if (data/'v999'/'ADAPTIVE_POLICY_ASSAY.json').is_file():
                    from tukuyo_v999.adaptive_policy import audit as adaptive_policy_audit
                    res['adaptive_policy_v999']=adaptive_policy_audit(data)
            elif args.cmd in ('whole-sync','whole-status','whole-audit','soul-experience'):
                _require_live(data)
                from tukuyo_v977.whole_state import sync as whole_sync,status as whole_status,audit as whole_audit,experience as soul_experience
                if args.cmd=='whole-sync':res={'ok':True,'unified_state':whole_sync(data)}
                elif args.cmd=='whole-status':res=whole_status(data,v955_full_status(api,data,args.semantic_migration_trust_file))
                elif args.cmd=='whole-audit':res=whole_audit(data)
                else:
                    res=soul_experience(data,args.kind,args.valence,args.importance,args.theme,args.relation)
                    from tukuyo_v993.relation_bound import sync as relation_sync
                    from tukuyo_v995.other_agent_trust import sync as peer_sync
                    relation_sync(data);peer_sync(data);whole_sync(data)
            elif args.cmd in ('heart-experience','heart-choose','heart-feedback','heart-status','heart-audit'):
                _require_live(data)
                from tukuyo_v978.heart_loop import process_experience as heart_experience,choose as heart_choose,feedback as heart_feedback,status as heart_status,audit as heart_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='heart-experience':
                    res=heart_experience(data,args.kind,args.valence,args.importance,args.theme,args.relation)
                    from tukuyo_v993.relation_bound import sync as relation_sync
                    from tukuyo_v995.other_agent_trust import sync as peer_sync
                    relation_sync(data);peer_sync(data);whole_sync(data)
                elif args.cmd=='heart-choose':res=heart_choose(data,json.loads(args.options.read_text(encoding='utf-8')),args.context);whole_sync(data)
                elif args.cmd=='heart-feedback':res=heart_feedback(data,args.action_id,args.outcome_valence,args.importance,args.theme);whole_sync(data)
                elif args.cmd=='heart-status':res=heart_status(data)
                else:res=heart_audit(data)
            elif args.cmd in ('soul-consolidate','soul-deep-audit','soul-forget-surface','soul-continuity-assay'):
                _require_live(data)
                from tukuyo_v979.deep_core import consolidate as deep_consolidate,audit as deep_audit,forget_surface_memory
                from tukuyo_v980.continuity import run as continuity_run
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='soul-consolidate':res=deep_consolidate(data);whole_sync(data)
                elif args.cmd=='soul-deep-audit':res=deep_audit(data)
                elif args.cmd=='soul-forget-surface':res=forget_surface_memory(data);whole_sync(data)
                else:res=continuity_run(data,json.loads(args.options.read_text(encoding='utf-8')),args.context);whole_sync(data)
            elif args.cmd in ('soul-fork-assay','soul-fork-audit'):
                _require_live(data)
                from tukuyo_v981.fork_divergence import run_assay as fork_assay,audit as fork_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='soul-fork-assay':res=fork_assay(data);whole_sync(data)
                else:res=fork_audit(data)
            elif args.cmd in ('continuity-checkpoint','continuity-anchor-export','continuity-audit','continuity-resume'):
                _require_live(data)
                from tukuyo_v982.continuity_ledger import checkpoint as continuity_checkpoint,export_anchor as continuity_anchor,audit as continuity_audit,resume as continuity_resume
                if args.cmd=='continuity-checkpoint':res=continuity_checkpoint(data,args.note)
                elif args.cmd=='continuity-anchor-export':res=continuity_anchor(data,args.out)
                elif args.cmd=='continuity-audit':res=continuity_audit(data,anchor_file=args.anchor_file)
                else:res=continuity_resume(data,args.anchor_file)
            elif args.cmd in ('homeostasis-assess','homeostasis-audit'):
                _require_live(data)
                from tukuyo_v983.homeostasis import assess as homeostasis_assess,audit as homeostasis_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='homeostasis-assess':res=homeostasis_assess(data);whole_sync(data)
                else:res=homeostasis_audit(data)
            elif args.cmd in ('full-runtime-fork-assay','full-runtime-fork-audit'):
                _require_live(data)
                from tukuyo_v984.full_fork import run_assay as full_fork_assay,audit as full_fork_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='full-runtime-fork-assay':res=full_fork_assay(data,ROOT);whole_sync(data)
                else:res=full_fork_audit(data)
            elif args.cmd in ('purpose-integrate','purpose-status','purpose-audit'):
                _require_live(data)
                from tukuyo_v985.narrative_purpose import integrate as purpose_integrate,status as purpose_status,audit as purpose_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='purpose-integrate':res=purpose_integrate(data);whole_sync(data)
                elif args.cmd=='purpose-status':res=purpose_status(data)
                else:res=purpose_audit(data)
            elif args.cmd in ('plan-compile','plan-status','plan-audit'):
                _require_live(data)
                from tukuyo_v986.long_horizon_plan import compile_plan, status as plan_status, audit as plan_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='plan-compile':res=compile_plan(data,args.horizon_cycles);whole_sync(data)
                elif args.cmd=='plan-status':res=plan_status(data)
                else:res=plan_audit(data)
            elif args.cmd in ('plan-execute','plan-execution-status','plan-execution-audit'):
                _require_live(data)
                from tukuyo_v987.plan_executor import execute as plan_execute,status as execution_status,audit as execution_audit
                if args.cmd=='plan-execute':res=plan_execute(data,args.max_steps)
                elif args.cmd=='plan-execution-status':res=execution_status(data)
                else:res=execution_audit(data)
            elif args.cmd in ('strategy-learn','strategy-status','strategy-audit'):
                _require_live(data)
                from tukuyo_v988.strategy_learning import learn as strategy_learn,status as strategy_status,audit as strategy_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='strategy-learn':res=strategy_learn(data);whole_sync(data)
                elif args.cmd=='strategy-status':res=strategy_status(data)
                else:res=strategy_audit(data)
            elif args.cmd in ('soul-identity-sync','soul-identity-status','soul-identity-audit'):
                _require_live(data)
                from tukuyo_v989.temporal_identity import sync_transitions as identity_sync,status as identity_status,audit as identity_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='soul-identity-sync':res=identity_sync(data);whole_sync(data)
                elif args.cmd=='soul-identity-status':res=identity_status(data)
                else:res=identity_audit(data)
            elif args.cmd in ('env-init','env-observe','env-act','env-audit'):
                _require_live(data)
                from tukuyo_v990.closed_environment import init as env_init,observe as env_observe,act as env_act,audit as env_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='env-init':res=env_init(data,args.profile,args.seed);whole_sync(data)
                elif args.cmd=='env-observe':res=env_observe(data)
                elif args.cmd=='env-act':res=env_act(data,args.action);whole_sync(data)
                else:res=env_audit(data)
            elif args.cmd in ('grounded-init','grounded-step','grounded-status','grounded-audit'):
                _require_live(data)
                from tukuyo_v991.grounded_organism import init as grounded_init,step as grounded_step,status as grounded_status,audit as grounded_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='grounded-init':res=grounded_init(data);whole_sync(data)
                elif args.cmd=='grounded-step':res=grounded_step(data,args.action);whole_sync(data)
                elif args.cmd=='grounded-status':res=grounded_status(data)
                else:res=grounded_audit(data)
            elif args.cmd in ('holdout-assay','holdout-audit'):
                _require_live(data)
                from tukuyo_v992.holdout import run as holdout_run,audit as holdout_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='holdout-assay':res=holdout_run(data);whole_sync(data)
                else:res=holdout_audit(data)
            elif args.cmd in ('relation-sync','relation-status','relation-audit','relation-choose'):
                _require_live(data)
                from tukuyo_v993.relation_bound import sync as relation_sync,status as relation_status,audit as relation_audit,choose as relation_choose
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='relation-sync':res=relation_sync(data);whole_sync(data)
                elif args.cmd=='relation-status':res=relation_status(data,args.peer)
                elif args.cmd=='relation-audit':res=relation_audit(data)
                else:res=relation_choose(data,args.peer,json.loads(args.options.read_text(encoding='utf-8')),args.context);whole_sync(data)
            elif args.cmd in ('semantic-interpret','semantic-record','semantic-status','semantic-audit'):
                _require_live(data)
                from tukuyo_v994.constructive_semantics import interpret as semantic_interpret,record as semantic_record,status as semantic_status,audit as semantic_audit
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='semantic-interpret':res=semantic_interpret(data,args.text,args.relation)
                elif args.cmd=='semantic-record':res=semantic_record(data,args.text,args.relation);whole_sync(data)
                elif args.cmd=='semantic-status':res=semantic_status(data)
                else:res=semantic_audit(data)
            elif args.cmd in ('peer-sync','peer-status','peer-audit','peer-choose'):
                _require_live(data)
                from tukuyo_v995.other_agent_trust import sync as peer_sync,status as peer_status,audit as peer_audit
                from tukuyo_v997.relation_inference import choose as peer_choose
                from tukuyo_v977.whole_state import sync as whole_sync
                if args.cmd=='peer-sync':res=peer_sync(data);whole_sync(data)
                elif args.cmd=='peer-status':res=peer_status(data,args.peer)
                elif args.cmd=='peer-audit':res=peer_audit(data)
                else:res=peer_choose(data,args.peer,json.loads(args.options.read_text(encoding='utf-8')),args.context);whole_sync(data)
            elif args.cmd=='conversation-ingest':
                _require_live(data)
                from tukuyo_v996.conversational_grounding import ingest
                res=ingest(data,args.text,args.relation)
            elif args.cmd in ('semantic-infer','semantic-infer-audit'):
                _require_live(data)
                from tukuyo_v998.semantic_inference import interpret,audit
                res=interpret(data,args.text,args.relation) if args.cmd=='semantic-infer' else audit(data)
            elif args.cmd in ('adaptive-policy-assay','adaptive-policy-audit'):
                _require_live(data)
                from tukuyo_v999.adaptive_policy import run,audit
                res=run(data) if args.cmd=='adaptive-policy-assay' else audit(data)
            elif args.cmd=='knowledge-add':
                _require_live(data)
                from tukuyo_v1001.knowledge import add
                res=add(data,args.text,args.source)
            elif args.cmd=='knowledge-search':
                _require_live(data)
                from tukuyo_v1001.knowledge import search
                res={'ok':True,'results':search(data,args.query,args.k)}
            elif args.cmd=='cognitive-query':
                _require_live(data)
                from tukuyo_v1022.cognition import solve
                local=solve(data,args.query)
                if local.get('recognized'):res={**local,'version':'v1022','source':'local-proof'}
                else:
                    from tukuyo_v1002.cognition import answer
                    res=answer(data,args.query)
            elif args.cmd=='cognitive-benchmark':
                _require_live(data)
                from tukuyo_v1003.benchmark import run
                res=run(data)
            elif args.cmd=='deliberate':
                _require_live(data)
                from tukuyo_v1004.deliberation import deliberate
                res=deliberate(data,args.query,args.max_steps)
            elif args.cmd in ('llm-ask','llm-teach','llm-status','llm-audit','self-study'):
                _require_live(data)
                from tukuyo_v1022_llm import bridge as llm_bridge,providers as llm_providers
                if args.cmd=='llm-ask':res=llm_bridge.ask(data,args.query,local_first=not args.no_local_first)
                elif args.cmd=='llm-teach':
                    from tukuyo_v1022_llm import teacher as llm_teacher
                    qs=json.loads(args.questions.read_text(encoding='utf-8'));qs=qs.get('questions',qs) if isinstance(qs,dict) else qs
                    res=llm_teacher.teach(data,qs)
                elif args.cmd=='self-study':
                    from tukuyo_v1022_llm import study as llm_study
                    extra=None
                    if args.questions:
                        qs=json.loads(args.questions.read_text(encoding='utf-8'));extra=qs.get('questions',qs) if isinstance(qs,dict) else qs
                    res=llm_study.study(data,args.max,args.dry_run,extra)
                elif args.cmd=='llm-status':
                    try:tch=[llm_providers.name_of(c) for c in llm_providers.teachers()]
                    except llm_providers.LLMError as e:tch=['ERROR:'+str(e)]
                    res={'ok':True,'version':'v1022.5+claude-patch4','llm':llm_providers.public_config(),'teachers':tch,'log':llm_bridge.audit(data)}
                else:res=llm_bridge.audit(data)
            elif args.cmd in ('think','dialogue-learn','learning-status','learning-audit'):
                _require_live(data)
                from tukuyo_v1022 import cognition as local
                if args.cmd=='think':res=local.solve(data,args.query,json.loads(args.formal_task.read_text()) if args.formal_task else None)
                elif args.cmd=='dialogue-learn':res=local.learn(data,json.loads(args.bundle.read_text()),args.teacher)
                else:res=local.audit(data)
            elif args.cmd in ('metabolism-init','metabolism-step','metabolism-status','metabolism-audit'):
                _require_live(data)
                from tukuyo_v1022 import metabolism
                if args.cmd=='metabolism-init':res=metabolism.init(data,args.runtime_trust_file,args.families,args.seed,args.reservoir,args.regeneration,args.max_age,not args.no_learning,not args.no_actions,args.research_world)
                elif args.cmd=='metabolism-step':res=metabolism.step(data,args.ticks)
                elif args.cmd=='metabolism-status':res=metabolism.status(data)
                else:res=metabolism.audit(data)
            elif args.cmd in ('research-run','research-status','research-audit'):
                if args.cmd=='research-run':_require_live(data)
                from tukuyo_v1023r import life as research_life
                if args.cmd=='research-run':res=research_life.run(data,args.world,args.ticks,args.regime,args.tier,args.noise)
                elif args.cmd=='research-status':res=research_life.status(data)
                else:res=research_life.audit(data)
            elif args.cmd=='research-ecology':
                from tukuyo_v1023r.evaluate import compare
                res=compare(args.start,args.seeds,**({'key':args.key} if args.key else {}))
                if args.out:args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(json.dumps(res,ensure_ascii=False,indent=1),encoding='utf-8')
                res={k:v for k,v in res.items() if k!='episodes'}
            elif args.cmd=='verified-query':
                _require_live(data)
                from tukuyo_v1005.verifier import solve
                res=solve(data,args.query,args.samples)
            elif args.cmd=='calibration-assay':
                _require_live(data)
                from tukuyo_v1011.calibration import assay
                res=assay(data)
            elif args.cmd=='core-reason':
                _require_live(data)
                from tukuyo_v1022.cognition import solve
                result=solve(data,args.text)
                if result.get('recognized'):res={'ok':True,'version':'v1022','reasoning':{**result,'ok':not result['uncertain']}}
                else:
                    from tukuyo_v1012.core_reasoning import reason
                    res={'ok':True,'version':'v1022','reasoning':reason(args.text)}
            elif args.cmd in ('memory-compact','memory-compact-audit'):
                _require_live(data)
                from tukuyo_v1012.memory_compaction import compact,audit
                res=compact(data,args.retain) if args.cmd=='memory-compact' else audit(data)
                if args.cmd=='memory-compact' and res.get('ok'):
                    from tukuyo_v977.whole_state import sync as whole_sync; whole_sync(data)
            elif args.cmd=='legacy-integration-audit':
                _require_live(data)
                from tukuyo_v1012_1.integration_audit import audit as legacy_integration_audit
                res=legacy_integration_audit(data)
            elif args.cmd in ('research-agent-assay','research-agent-audit'):
                _require_live(data)
                from tukuyo_v1006.research_agent import assay,audit
                res=assay(data) if args.cmd=='research-agent-assay' else audit(data)
                if args.cmd=='research-agent-assay' and res.get('ok'):
                    from tukuyo_v977.whole_state import sync as whole_sync; whole_sync(data)
            elif args.cmd in ('organism2-init','organism2-update','organism2-preserve','organism2-status','organism2-audit'):
                _require_live(data)
                from tukuyo_v1007.organism2 import init,update,self_preservation,audit,load,_needs
                if args.cmd=='organism2-init':res=init(data)
                elif args.cmd=='organism2-update':res=update(data,args.event,args.amount)
                elif args.cmd=='organism2-preserve':res=self_preservation(data,json.loads(args.options.read_text(encoding='utf-8')))
                elif args.cmd=='organism2-status':
                    st=load(data);res={'ok':True,'version':'v1007','state':st,'needs':_needs(st)}
                else:res=audit(data)
                if args.cmd in ('organism2-init','organism2-update') and res.get('ok'):
                    from tukuyo_v977.whole_state import sync as whole_sync; whole_sync(data)
            elif args.cmd in ('living-cycle','living-audit'):
                _require_live(data)
                from tukuyo_v1008.whole_living_cognition import cycle,audit
                res=cycle(data,args.query) if args.cmd=='living-cycle' else audit(data)
                if args.cmd=='living-cycle' and res.get('ok'):
                    from tukuyo_v977.whole_state import sync as whole_sync; whole_sync(data)
            elif args.cmd=='successor-seed':
                _require_live(data)
                from tukuyo_v1008.whole_living_cognition import successor_seed
                res=successor_seed(data,args.successor_id)
            elif args.cmd in ('long-life-assay','long-life-audit'):
                _require_live(data)
                from tukuyo_v1009.long_lived_identity import run_assay as long_life_assay,audit as long_life_audit
                res=long_life_assay(data,args.cycles) if args.cmd=='long-life-assay' else long_life_audit(data)
                if args.cmd=='long-life-assay' and res.get('ok'):
                    from tukuyo_v977.whole_state import sync as whole_sync; whole_sync(data)
            elif args.cmd=='runtime-trust-rebind':
                from tukuyo_v1022.runtime_release import rebind
                res=rebind(data,args.runtime_trust_file,args.previous_trust_file)
            elif args.cmd in ('recovery-checkpoint','recovery-audit','recovery-restore','recovery-status'):
                from tukuyo_v1014.recovery import create_checkpoint as recovery_checkpoint,audit_checkpoint as recovery_audit,restore as recovery_restore,status as recovery_status
                if args.cmd=='recovery-checkpoint':
                    _require_live(data);res=recovery_checkpoint(data,args.note)
                elif args.cmd=='recovery-audit':res=recovery_audit(args.checkpoint,args.trust_file)
                elif args.cmd=='recovery-restore':res=recovery_restore(data,args.checkpoint,args.trust_file,args.anchor_file,args.dry_run)
                else:res=recovery_status(data)
            elif args.cmd in ('continuity-campaign-start','continuity-campaign-step','continuity-campaign-status','continuity-campaign-end-request','continuity-campaign-witness-request','continuity-campaign-witness-record','continuity-campaign-audit','continuity-campaign-evidence'):
                _require_live(data)
                from tukuyo_v1014_4.long_run_campaign import start as campaign_start,step as campaign_step,status as campaign_status,end_request as campaign_end,witness_request as campaign_witness_request,record_witness as campaign_witness_record,audit as campaign_audit,evidence as campaign_evidence
                if args.cmd=='continuity-campaign-start':res=campaign_start(data,args.profile,args.target_seconds,args.tick_seconds,args.checkpoint_seconds,args.note)
                elif args.cmd=='continuity-campaign-step':res=campaign_step(data,args.note,args.force_checkpoint,startup_recovery)
                elif args.cmd=='continuity-campaign-status':res=campaign_status(data)
                elif args.cmd=='continuity-campaign-end-request':res=campaign_end(data,args.out)
                elif args.cmd=='continuity-campaign-witness-request':res=campaign_witness_request(data,args.out)
                elif args.cmd=='continuity-campaign-witness-record':res=campaign_witness_record(data,args.receipt,args.witness_trust_file)
                elif args.cmd=='continuity-campaign-audit':res=campaign_audit(data,args.start_witness,args.end_witness,args.witness_trust_file,args.require_complete)
                else:res=campaign_evidence(data,args.out,args.start_witness,args.end_witness,args.witness_trust_file,args.require_complete)
                if args.cmd in ('continuity-campaign-start','continuity-campaign-step') and res.get('ok'):
                    from tukuyo_v977.whole_state import sync as whole_sync; whole_sync(data)
            elif args.cmd in ('endurance-evidence-export','endurance-evidence-audit','endurance-route-evaluate'):
                from tukuyo_v1015_1.evidence_authenticity import export_bundle,audit_bundle,route_evaluate
                if args.cmd=='endurance-evidence-export':
                    _require_live(data);res=export_bundle(data,args.out,args.start_witness,args.end_witness,args.witness_trust_file)
                elif args.cmd=='endurance-evidence-audit':res=audit_bundle(args.evidence,args.witness_trust_file,args.profile)
                else:res=route_evaluate(args.evidence,args.witness_trust_file)
            elif args.cmd in ('endurance-exec-init','endurance-exec-pump','endurance-exec-accept-witness','endurance-exec-status','endurance-exec-audit','endurance-exec-resume','endurance-exec-abort','endurance-failure-evidence-audit','endurance-repro-export','endurance-challenge-init','endurance-challenge-audit','endurance-challenge-repro-export'):
                _require_live(data)
                from tukuyo_v1015_3.endurance_resume import start as ex_start,pump as ex_pump,accept_witness as ex_accept,status as ex_status,audit as ex_audit,resume as ex_resume,abort as ex_abort,failure_audit as ex_failure_audit
                if args.cmd=='endurance-challenge-init':
                    from tukuyo_v1015_5.challenge import start as challenge_start
                    res=challenge_start(data,args.challenge_file,args.challenge_trust_file,args.profile,args.target_seconds,args.tick_seconds,args.checkpoint_seconds,args.witness_seconds,args.living_seconds,args.note)
                elif args.cmd=='endurance-challenge-audit':
                    from tukuyo_v1015_5.challenge import audit as challenge_audit
                    res=challenge_audit(data,args.challenge_trust_file)
                elif args.cmd=='endurance-challenge-repro-export':
                    from tukuyo_v1015_5.challenge import export_bundle as challenge_export
                    res=challenge_export(data,args.out,args.witness_trust_file,args.challenge_trust_file)
                elif args.cmd=='endurance-exec-init':res=ex_start(data,args.profile,args.target_seconds,args.tick_seconds,args.checkpoint_seconds,args.witness_seconds,args.living_seconds,args.note)
                elif args.cmd=='endurance-exec-pump':res=ex_pump(data,args.note)
                elif args.cmd=='endurance-exec-accept-witness':res=ex_accept(data,args.receipt,args.witness_trust_file)
                elif args.cmd=='endurance-exec-status':res=ex_status(data,args.witness_trust_file)
                elif args.cmd=='endurance-exec-audit':res=ex_audit(data,args.witness_trust_file)
                elif args.cmd=='endurance-exec-resume':res=ex_resume(data,args.witness_trust_file,args.note)
                elif args.cmd=='endurance-exec-abort':res=ex_abort(data,args.reason)
                elif args.cmd=='endurance-failure-evidence-audit':res=ex_failure_audit(args.evidence,args.witness_trust_file)
                else:
                    from tukuyo_v1015_4.reproduction import export_bundle as repro_export
                    res=repro_export(data,args.out,args.witness_trust_file)
            elif args.cmd in ('living-episode','living-continuity-status','living-continuity-audit','living-gate-assay','living-gate-audit'):
                _require_live(data)
                from tukuyo_v1015.living_continuity import episode as living_episode,status as living_status,audit as living_audit,run_gate_assay,gate_audit as living_gate_audit
                if args.cmd=='living-episode':
                    opts=json.loads(args.options.read_text(encoding='utf-8')) if args.options else None
                    res=living_episode(data,args.kind,args.valence,args.importance,args.theme,args.relation,args.query,opts,args.note)
                elif args.cmd=='living-continuity-status':res=living_status(data)
                elif args.cmd=='living-continuity-audit':res=living_audit(data)
                elif args.cmd=='living-gate-assay':res=run_gate_assay(data)
                else:res=living_gate_audit(data,args.start_witness,args.end_witness,args.witness_trust_file)
            elif args.cmd in ('realtime-start','realtime-tick','realtime-status','realtime-anchor-export','realtime-witness-request','realtime-audit'):
                _require_live(data)
                from tukuyo_v1013.realtime_continuity import start as rt_start,tick as rt_tick,status as rt_status,export_anchor as rt_anchor,witness_request as rt_witness,audit as rt_audit
                if args.cmd=='realtime-start':res=rt_start(data,args.profile,args.target_seconds,args.note)
                elif args.cmd=='realtime-tick':res=rt_tick(data,args.note)
                elif args.cmd=='realtime-status':res=rt_status(data)
                elif args.cmd=='realtime-anchor-export':res=rt_anchor(data,args.out)
                elif args.cmd=='realtime-witness-request':res=rt_witness(data,args.out)
                else:res=rt_audit(data,args.anchor_file,args.start_witness,args.end_witness,args.witness_trust_file,args.require_complete)
                if args.cmd in ('realtime-start','realtime-tick') and res.get('ok'):
                    from tukuyo_v977.whole_state import sync as whole_sync; whole_sync(data)
            elif args.cmd=='agenda-propose':
                from tukuyo_v959.agenda import propose_agenda
                from tukuyo_v967.integrated_system import append_event,canon as v967canon
                challenges=json.loads(args.challenges.read_text(encoding='utf-8')); agenda=propose_agenda(challenges)
                if args.out: args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_bytes(v967canon(agenda)+b'\n')
                append_event(data,'RESEARCH_AGENDA_PROPOSED',agenda);res={'ok':True,'agenda':agenda,'out':str(args.out) if args.out else None}
            elif args.cmd=='agenda-authorize':
                from tukuyo_v959.agenda import verify_authorization
                from tukuyo_v967.integrated_system import append_event
                if not args.goal_authority_trust_file: raise ValueError('GOAL_AUTHORITY_TRUST_FILE_REQUIRED')
                agenda=json.loads(args.agenda.read_text(encoding='utf-8'));receipt=json.loads(args.receipt.read_text(encoding='utf-8'))
                auth=verify_authorization(agenda,receipt,args.goal_authority_trust_file);append_event(data,'RESEARCH_AGENDA_AUTHORIZED',auth);res=auth
            elif args.cmd=='campaign-run':
                from tukuyo_v960.campaign import run_campaign
                from tukuyo_v967.integrated_system import append_event
                if not args.observer_trust_file: raise ValueError('OBSERVER_TRUST_FILE_REQUIRED')
                spec=json.loads(args.spec.read_text(encoding='utf-8'));obs=[json.loads(x.read_text(encoding='utf-8')) for x in args.observations]
                ops={'ADD':lambda a,b:a+b,'SUB':lambda a,b:a-b,'MUL':lambda a,b:a*b,'MAX':lambda a,b:max(a,b),'MIN':lambda a,b:min(a,b)}
                hs=[]
                for h in spec['hypotheses']:
                    if h['operator'] not in ops: raise ValueError('UNSUPPORTED_HYPOTHESIS_OPERATOR')
                    hs.append({'hypothesis_id':h['hypothesis_id'],'predict':ops[h['operator']]})
                result=run_campaign(spec['challenge_id'],hs,spec['probe'],obs,args.observer_trust_file,spec.get('max_cycles',4));append_event(data,'SCIENCE_CAMPAIGN_COMPLETED',result);res=result
            elif args.cmd=='improver-compare':
                from tukuyo_v961.evolution import compare
                from tukuyo_v967.integrated_system import append_event
                result=compare();append_event(data,'IMPROVER_COMPARISON',result);res={'ok':True,'comparison':result}
            elif args.cmd=='inherit-export':
                from tukuyo_v962.inheritance import prepare
                from tukuyo_v967.integrated_system import append_event,canon as v967canon
                b=prepare(data,args.candidate_sha256,args.parent_id,args.child_id);args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(v967canon(b)+b'\n');append_event(data,'INHERITANCE_EXPORTED',{'bundle_sha256':b['bundle_sha256'],'candidate_sha256':args.candidate_sha256,'child_id':args.child_id});res={'ok':True,'bundle':str(args.out),'bundle_sha256':b['bundle_sha256']}
            elif args.cmd=='inherit-import':
                from tukuyo_v962.inheritance import import_bundle
                from tukuyo_v967.integrated_system import append_event
                if not args.inheritance_trust_file: raise ValueError('INHERITANCE_TRUST_FILE_REQUIRED')
                b=json.loads(args.bundle.read_text(encoding='utf-8'));r=json.loads(args.receipt.read_text(encoding='utf-8'));entry=import_bundle(data,b,r,args.inheritance_trust_file,args.child_id);append_event(data,'INHERITANCE_IMPORTED',entry);res={'ok':True,'entry':entry}
            elif args.cmd=='inherit-eval':
                from tukuyo_v962.inheritance import evaluate_child
                res=evaluate_child(data,args.candidate_sha256,args.a,args.b)
            elif args.cmd=='family-propose':
                from tukuyo_v965.family_synthesis import propose
                from tukuyo_v967.integrated_system import append_event,canon as v967canon
                rows=json.loads(args.rows.read_text(encoding='utf-8'));ce=json.loads(args.ceiling_evidence.read_text(encoding='utf-8'));prop=propose(rows,ce)
                if args.out: args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(v967canon(prop)+b'\n')
                append_event(data,'FAMILY_PROPOSED',{'candidate_sha256':prop['candidate_sha256'],'invented_family':prop['invented_family'],'family_parameters':prop['family_parameters']});res={'ok':True,'proposal':prop,'out':str(args.out) if args.out else None}
            elif args.cmd=='family-promote-verify':
                from tukuyo_v966.promotion import verify_promotion
                from tukuyo_v967.integrated_system import append_event,save_family
                if not args.family_evaluator_trust_file or not args.family_promotion_trust_file: raise ValueError('V966_FAMILY_EXTERNAL_TRUST_REQUIRED')
                prop=json.loads(args.proposal.read_text(encoding='utf-8'));er=json.loads(args.evaluator_receipt.read_text(encoding='utf-8'));pr=json.loads(args.promotion_receipt.read_text(encoding='utf-8'))
                vr=verify_promotion(pr,prop,er,args.family_evaluator_trust_file,args.family_promotion_trust_file);entry=save_family(data,prop,vr['evaluator'],vr['authority']);append_event(data,'FAMILY_PROMOTED',{'candidate_sha256':prop['candidate_sha256'],'scope':vr['authority']['scope']});res={'ok':True,'entry':entry}
            elif args.cmd=='family-eval':
                from tukuyo_v967.integrated_system import family_eval
                res=family_eval(data,args.candidate_sha256,args.a,args.b)
            elif args.cmd=='reproduce-current':
                from tukuyo_v963.reproduction import run_fresh
                if not args.runtime_trust_file: raise ValueError('RUNTIME_TRUST_FILE_REQUIRED')
                res=run_fresh(ROOT,args.runtime_trust_file)
            elif args.cmd=='cap-request':
                from tukuyo_v954.provenance import _paths,persist_teach_bundle,load,sha_obj,verify_request
                _require_live(data)
                # request must already have been persisted by teach; choose exact matching live surface request
                reqs=[]
                for rp in (data/'capability_provenance/requests').glob('*.json'):
                    q=load(rp)
                    if q.get('surface')==args.surface:
                        verify_request(data,q);reqs.append((rp,q))
                if len(reqs)!=1:raise ValueError('CAPABILITY_REQUEST_NOT_UNIQUE')
                args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(__import__('tukuyo_v954.provenance',fromlist=['canon']).canon(reqs[0][1])+b'\n')
                res={'ok':True,'request_file':str(args.out),'request_sha256':sha_obj(reqs[0][1])}
            elif args.cmd=='cap-install':
                from tukuyo_v954.provenance import install_seal
                _require_live(data)
                if not args.cap_trust_dir:raise ValueError('CAP_EXTERNAL_TRUST_DIR_REQUIRED')
                res=install_seal(data,args.cap_trust_dir,args.request,args.receipt)
            elif args.cmd=='science-demo':
                n=max(12,min(args.rows,120));rows=[]
                for i in range(n):
                    a=i-9;b=((i*5+3)%13)-6;rows.append({'a':a,'b':b,'expected':a*b+a-b})
                ev=v944_search(rows);gap=v944_classify(rows,ev);prop=v945_propose(rows,ev) if gap['state']=='REPRESENTATION_INSUFFICIENT' else None
                res={'ok':True,'scope':'SYNTHETIC_BOUNDED_DEMO','gap':gap,'proposal':prop,'auto_promotion':False}
            elif args.cmd=='lab':
                root=(args.out.resolve() if args.out else data/'labs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]))
                res=run_lab(api,root,include_research=not args.skip_research)
                res['lab_directory']=str(root)
            elif args.cmd=='lab-audit':res=audit_lab(api,args.path)
            else:
                _require_live(data)
                if args.cmd in ('status','audit'):
                    from tukuyo_v977.whole_state import sync as whole_sync,status as whole_status,audit as whole_audit
                    if args.cmd=='status': whole_sync(data)
                    res=v955_full_status(api,data,args.semantic_migration_trust_file)
                    res['base_runtime_version']=res.get('version');res['version']='v1019'
                    res['v977_whole']=whole_status(data,None) if args.cmd=='status' else whole_audit(data)
                    if (data/'v983'/'HOMEOSTASIS_STATE.json').is_file():
                        from tukuyo_v983.homeostasis import audit as homeostasis_audit
                        res['v983_homeostasis']=homeostasis_audit(data)
                    if (data/'v984'/'FULL_RUNTIME_FORK_ASSAY.json').is_file():
                        from tukuyo_v984.full_fork import audit as full_fork_audit
                        res['v984_full_runtime_fork']=full_fork_audit(data)
                    if (data/'v985'/'NARRATIVE_PURPOSE_STATE.json').is_file():
                        from tukuyo_v985.narrative_purpose import status as purpose_status,audit as purpose_audit
                        res['v985_narrative_purpose']=purpose_status(data) if args.cmd=='status' else purpose_audit(data)
                    if (data/'v986'/'LONG_HORIZON_PLAN.json').is_file():
                        from tukuyo_v986.long_horizon_plan import status as plan_status,audit as plan_audit
                        res['v986_long_horizon_plan']=plan_status(data) if args.cmd=='status' else plan_audit(data)
                    if (data/'v987'/'PLAN_EXECUTION_STATE.json').is_file():
                        from tukuyo_v987.plan_executor import status as execution_status,audit as execution_audit
                        res['v987_plan_execution']=execution_status(data) if args.cmd=='status' else execution_audit(data)
                    if (data/'v988'/'STRATEGY_STATE.json').is_file():
                        from tukuyo_v988.strategy_learning import status as strategy_status,audit as strategy_audit
                        res['v988_strategy_learning']=strategy_status(data) if args.cmd=='status' else strategy_audit(data)
                    if (data/'v989'/'TEMPORAL_IDENTITY.json').is_file():
                        from tukuyo_v989.temporal_identity import status as identity_status,audit as identity_audit
                        res['v989_temporal_identity']=identity_status(data) if args.cmd=='status' else identity_audit(data)
                    if (data/'v990'/'ENVIRONMENT_STATE.json').is_file():
                        from tukuyo_v990.closed_environment import observe as env_observe,audit as env_audit
                        res['v990_closed_environment']=env_observe(data) if args.cmd=='status' else env_audit(data)
                    if (data/'v991'/'GROUNDED_ORGANISM_STATE.json').is_file():
                        from tukuyo_v991.grounded_organism import status as grounded_status,audit as grounded_audit
                        res['v991_grounded_organism']=grounded_status(data) if args.cmd=='status' else grounded_audit(data)
                    if (data/'v992'/'HOLDOUT_ASSAY.json').is_file():
                        from tukuyo_v992.holdout import audit as holdout_audit
                        res['v992_holdout']=holdout_audit(data)
                    if (data/'v993'/'RELATION_BOUND_STATE.json').is_file():
                        from tukuyo_v993.relation_bound import status as relation_status,audit as relation_audit
                        res['v993_relation_bound']=relation_status(data) if args.cmd=='status' else relation_audit(data)
                    if (data/'v994'/'SEMANTIC_EVENTS.json').is_file():
                        from tukuyo_v994.constructive_semantics import status as semantic_status,audit as semantic_audit
                        res['v994_constructive_semantics']=semantic_status(data) if args.cmd=='status' else semantic_audit(data)
                    if (data/'v995'/'OTHER_AGENT_MODELS.json').is_file():
                        from tukuyo_v995.other_agent_trust import status as peer_status,audit as peer_audit
                        res['v995_other_agent_trust']=peer_status(data) if args.cmd=='status' else peer_audit(data)
                    if ((data/'v996'/'CONVERSATION_GROUNDING_EVENTS.jsonl').is_file() or (data/'v996'/'CONVERSATION_EVENT_HEAD.json').is_file()):
                        from tukuyo_v996.conversational_grounding import audit as conversation_audit
                        res['v996_conversation_grounding']=conversation_audit(data)
                    if ((data/'v998'/'SEMANTIC_INFERENCE_EVENTS.jsonl').is_file() or (data/'v998'/'SEMANTIC_EVENT_HEAD.json').is_file()):
                        from tukuyo_v998.semantic_inference import audit as semantic_infer_audit
                        res['v998_semantic_inference']=semantic_infer_audit(data)
                    if (data/'v999'/'ADAPTIVE_POLICY_ASSAY.json').is_file():
                        from tukuyo_v999.adaptive_policy import audit as adaptive_policy_audit
                        res['v999_adaptive_policy']=adaptive_policy_audit(data)
                    if (data/'v1009'/'LONG_LIVED_IDENTITY_ASSAY.json').is_file():
                        from tukuyo_v1009.long_lived_identity import audit as long_life_audit
                        res['v1009_long_lived_identity']=long_life_audit(data)
                    if (data/'v1015'/'LIVING_STATE.json').is_file():
                        from tukuyo_v1015.living_continuity import status as living_status,audit as living_audit
                        res['v1015_living_continuity']=living_status(data) if args.cmd=='status' else living_audit(data)
                    if (data/'v1016'/'SOCIETY_STATE.json').is_file():
                        from tukuyo_v1016.society import status as society_status,audit as society_audit
                        res['v1016_multi_agent_society']=society_status(data) if args.cmd=='status' else society_audit(data)
                    if (data/'v1018'/'SUCCESSION_STATE.json').is_file():
                        from tukuyo_v1018.succession import status as succession_status,audit as succession_audit
                        res['v1018_lineage_succession']=succession_status(data) if args.cmd=='status' else succession_audit(data)
                    elif (data/'v1017'/'SUCCESSION_STATE.json').is_file():
                        from tukuyo_v1017.succession import status as succession_status,audit as succession_audit
                        res['v1017_parent_successor_grandchild']=succession_status(data) if args.cmd=='status' else succession_audit(data)
                    if (data/'v1019'/'EVOLUTION_STATE.json').is_file():
                        from tukuyo_v1019.evolution import status as evolution_status,audit as evolution_audit
                        res['v1019_generational_evolution']=evolution_status(data) if args.cmd=='status' else evolution_audit(data)
                    if (data/'v1020').exists():
                        from tukuyo_v1020.ecology import status as population_status,audit as population_audit
                        res['v1020_population_ecology']=population_status(data) if args.cmd=='status' else population_audit(data)
                    if ep.roots(data).exists():res['epistemic']=ep.status(data,args.ep_trust_dir)
                    if args.cmd=='audit':
                        child_failures=[]
                        for k,v in res.items():
                            if isinstance(v,dict) and 'ok' in v and v.get('ok') is False: child_failures.append(k)
                        if child_failures:
                            res['ok']=False;res['audit_failures']=sorted(child_failures)
                elif args.cmd=='tick':
                    bridge.tick(api,data,args.count)
                    from tukuyo_v977.whole_state import sync as whole_sync
                    whole_sync(data);res=v955_full_status(api,data,args.semantic_migration_trust_file)
                elif args.cmd=='eval':res=bridge.evaluate(api,data,args.query)
                elif args.cmd=='teach':
                    res=bridge.teach(api,data,args.evidence,args.apply)
                    from tukuyo_v967.integrated_system import append_event
                    append_event(data,'NATIVE_TEACH',{'apply':bool(args.apply),'result':res})
                    from tukuyo_v977.whole_state import sync as whole_sync
                    whole_sync(data)
                elif args.cmd=='research':res=bridge.run_research(api,data,args.task,args.seed)
                elif args.cmd=='diagnose':res=bridge.diagnose(api,data,args.queries,args.task)
                elif args.cmd=='chat':chat(api,data,args.ep_trust_dir,args.semantic_migration_trust_file);return 0
                elif args.cmd in ('runtime-ecology-init','runtime-ecology-step','runtime-ecology-status','runtime-ecology-audit','runtime-ecology-recover-cache'):
                    from tukuyo_v1021 import runtime_bridge
                    if args.cmd=='runtime-ecology-init':res=runtime_bridge.init(data,args.runtime_trust_file,args.families,args.seed,args.regeneration,args.max_age)
                    elif args.cmd=='runtime-ecology-step':res=runtime_bridge.step(data,args.environment,args.ticks)
                    elif args.cmd=='runtime-ecology-status':res=runtime_bridge.status(data)
                    elif args.cmd=='runtime-ecology-recover-cache':res=runtime_bridge.recover_cache(data)
                    else:res=runtime_bridge.audit(data)
                elif args.cmd in ('population-init','population-join','population-step','population-status','population-audit'):
                    _require_live(data)
                    from tukuyo_v1020 import ecology as population
                    if args.cmd=='population-init':res=population.init(data,args.seed,args.capacity,args.regeneration,args.max_population,args.max_age,not args.no_cooperation,args.founders)
                    elif args.cmd=='population-join':res=population.join(data,args.source_data,args.source_trust_file,args.founders)
                    elif args.cmd=='population-step':res=population.step(data,args.environment,args.ticks)
                    elif args.cmd=='population-status':res=population.status(data)
                    else:res=population.audit(data)
                elif args.cmd in ('evolution-select','evolution-export','evolution-import','evolution-status','evolution-audit','evolution-gate-summary'):
                    _require_live(data)
                    from tukuyo_v1019.evolution import select as evolution_select,export_successor as evolution_export,import_successor as evolution_import,status as evolution_status,audit as evolution_audit,gate_summary as evolution_gate
                    if args.cmd=='evolution-select':res=evolution_select(data,args.environment,args.population,args.seed)
                    elif args.cmd=='evolution-export':res=evolution_export(data,args.child_id,args.out,args.child_public_key_file)
                    elif args.cmd=='evolution-import':res=evolution_import(data,args.package,args.parent_trust_file)
                    elif args.cmd=='evolution-status':res=evolution_status(data)
                    elif args.cmd=='evolution-audit':res=evolution_audit(data)
                    else:
                        for peer_root in (args.child_data.resolve(),args.grandchild_data.resolve()):
                            if not (peer_root/'state/integration_state.json').is_file():raise ValueError('V1019_GATE_PEER_NOT_INITIALIZED:'+str(peer_root))
                        res=evolution_gate(data,args.child_data.resolve(),args.grandchild_data.resolve())
                elif args.cmd in ('succession-founder-init','succession-pubkey-export','succession-export','succession-import','succession-status','succession-audit','succession-gate-summary','succession-gate-assay'):
                    _require_live(data)
                    from tukuyo_v1018.succession import founder_init as succession_founder,export_public_key as succession_pub,export_successor as succession_export,import_successor as succession_import,status as succession_status,audit as succession_audit,gate_summary as succession_gate,run_gate_assay as succession_gate_assay
                    if args.cmd=='succession-founder-init':res=succession_founder(data)
                    elif args.cmd=='succession-pubkey-export':res=succession_pub(data,args.out)
                    elif args.cmd=='succession-export':res=succession_export(data,args.child_id,args.out,args.child_public_key_file)
                    elif args.cmd=='succession-import':res=succession_import(data,args.package,args.parent_trust_file)
                    elif args.cmd=='succession-status':res=succession_status(data)
                    elif args.cmd=='succession-audit':res=succession_audit(data)
                    elif args.cmd=='succession-gate-summary':
                        for peer_root in (args.child_data.resolve(),args.grandchild_data.resolve()):
                            if not (peer_root/'state/integration_state.json').is_file():raise ValueError('V1018_GATE_PEER_NOT_INITIALIZED:'+str(peer_root))
                        res=succession_gate(data,args.child_data.resolve(),args.grandchild_data.resolve())
                    else:
                        res=succession_gate_assay(api,data,args.child_data.resolve(),args.child_id,args.grandchild_data.resolve(),args.grandchild_id)
                elif args.cmd in ('society-send','society-receive','society-ack','society-status','society-audit','society-sync','society-gate-assay'):
                    bridge._require_healthy(api,data);s=api['social']
                    from tukuyo_v1016.society import record_outbound,record_inbound,record_ack,status as society_status,audit as society_audit,sync as society_sync,gate_assay as society_gate
                    from tukuyo_v977.whole_state import sync as whole_sync
                    if args.cmd=='society-send':
                        pkt=s.make_public_packet(data/'state',args.recipient,public_message=args.message)
                        record_outbound(data,args.recipient,pkt);whole_sync(data)
                        args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(bridge.canon(pkt)+b'\n');res={'ok':True,'version':'v1017','packet_file':str(args.out)}
                    elif args.cmd=='society-receive':
                        pkt=json.loads(args.packet.read_text(encoding='utf-8'));ack=s.receive_packet(data/'state',pkt)
                        rr=record_inbound(data,pkt,ack,args.valence,args.importance,args.theme)
                        args.ack_out.parent.mkdir(parents=True,exist_ok=True);args.ack_out.write_bytes(bridge.canon(ack)+b'\n');res={'ok':bool(rr.get('ok')),'version':'v1017','ack_file':str(args.ack_out),'society_event':rr.get('event'),'living':rr.get('living')}
                    elif args.cmd=='society-ack':
                        pkt=json.loads(args.packet.read_text(encoding='utf-8'));ack=json.loads(args.ack.read_text(encoding='utf-8'));s.receive_ack(data/'state',pkt,ack)
                        rr=record_ack(data,pkt,ack,args.valence,args.importance,args.theme);res={'ok':bool(rr.get('ok')),'version':'v1017','society_event':rr.get('event'),'living':rr.get('living')}
                    elif args.cmd=='society-status':res=society_status(data)
                    elif args.cmd=='society-audit':res=society_audit(data)
                    elif args.cmd=='society-sync':res=society_sync(data)
                    else:
                        for peer_root in (args.peer_b_data.resolve(),args.peer_c_data.resolve()):
                            if not (peer_root/'state/integration_state.json').is_file():raise ValueError('V1016_GATE_PEER_NOT_INITIALIZED:'+str(peer_root))
                        res=society_gate(s,data,args.peer_b_data.resolve(),args.peer_c_data.resolve())
                elif args.cmd=='social':
                    bridge._require_healthy(api,data);s=api['social'];state=data/'state'
                    if args.social_cmd=='send':
                        pkt=s.make_public_packet(state,args.recipient,public_message=args.message)
                        args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_bytes(bridge.canon(pkt)+b'\n');res={'ok':True,'packet_file':str(args.out)}
                    elif args.social_cmd=='receive':
                        pkt=json.loads(args.packet.read_text(encoding='utf-8'));ack=s.receive_packet(state,pkt)
                        args.ack_out.parent.mkdir(parents=True,exist_ok=True);args.ack_out.write_bytes(bridge.canon(ack)+b'\n');res={'ok':True,'ack_file':str(args.ack_out)}
                    elif args.social_cmd=='ack':
                        pkt=json.loads(args.packet.read_text(encoding='utf-8'));ack=json.loads(args.ack.read_text(encoding='utf-8'))
                        res={'ok':bool(s.receive_ack(state,pkt,ack))}
                    else:res=s.peer_model(state,args.peer,include_private=args.private)
                    from tukuyo_v977.whole_state import sync as whole_sync
                    whole_sync(data)
                else:raise ValueError('UNKNOWN_COMMAND')
            output(res)
            return 0 if res.get('ok',True) else 1
    except Exception as exc:
        output({'ok':False,'error':'ENTITY_DEAD' if str(exc).startswith('ENTITY_DEAD:') else type(exc).__name__+':'+str(exc)})
        return 1

def main(argv=None):
    # Serialize startup recovery, reads and command dispatch as one operation.
    # The per-root lock is reentrant for nested lineage operations.
    args=parser().parse_args(argv)
    from tukuyo_v1019.transaction import _writer_lock
    try:
        with _writer_lock(args.data.resolve()):
            return _main(argv)
    except Exception as exc:
        output({'ok':False,'error':type(exc).__name__+':'+str(exc)})
        return 1

if __name__=='__main__':raise SystemExit(main())

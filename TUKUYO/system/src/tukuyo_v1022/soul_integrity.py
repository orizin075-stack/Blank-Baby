"""Signed, bounded integration of identity, commitments, narrative and choice.

This is a functional software model.  It does not establish a literal soul,
consciousness, qualia, or morally relevant personhood.  Commitments are derived
only from the individual's canonical v977 vow events.  A commitment becomes
active after two distinct events; a single statement remains a candidate.
Choice effects are conditional on the caller's bounded option annotations and
are recorded together with a counterfactual that omits this integration layer.
"""
from __future__ import annotations

import copy,json,re
from pathlib import Path

from tukuyo_v977 import whole_state as whole
from tukuyo_v977.whole_state import load_soul,sha_obj,_live_identity
from tukuyo_v978 import heart_loop as heart
from tukuyo_v985 import narrative_purpose as purpose
from tukuyo_v989 import temporal_identity as temporal
from tukuyo_v1019.lifecycle import require_alive
from tukuyo_v1019.transaction import transactional
from . import store

NS='soul_integrity'
COMPONENT='whole_soul_integrity'
SCHEMA='tukuyo.v1022_6_8.soul_integrity/1'
ZERO='0'*64
SIGNALS=('survival','integrity','curiosity','truthfulness','relationship','trust','threat')
PURPOSE_SIGNAL={
    'PRESERVE_INTEGRITY':'integrity',
    'SEEK_KNOWLEDGE':'curiosity',
    'MAINTAIN_RELATIONSHIPS':'relationship',
    'SELF_MAINTENANCE':'survival',
    'PRESERVE_TRUTH':'truthfulness',
}


def needs_preflight(data):
    if (Path(data)/NS).exists(): return True
    p=whole.state_path(data)
    if not p.is_file(): return False
    try:return COMPONENT in json.loads(p.read_text(encoding='utf-8')).get('payload',{}).get('component_hashes',{})
    except Exception:return True


def _bounded_text(value,label,limit=96):
    if not isinstance(value,str) or not value or len(value)>limit or re.search(r'[\x00-\x1f]',value):
        raise ValueError('SOUL_INTEGRITY_'+label)
    return value


def _heart_projection(h):
    """Only decision-relevant Heart fields; recording an action does not stale it."""
    return {
        'individual_id':h.get('individual_id'),'emotion':h.get('emotion'),
        'value_bias':h.get('value_bias'),'self_model':h.get('self_model'),
        'active_goal':h.get('active_goal'),'soul_sha256':h.get('soul_sha256'),
    }


def _soul_events(data):
    from tukuyo_common.journal import migrate_boxed_json,load_events
    p=whole.event_path(data);hp=whole.event_head_path(data)
    migrate_boxed_json(whole.legacy_event_path(data),p,hp,'tukuyo.v1011.soul_event_head/1',sha_obj)
    return load_events(p) if p.exists() else []


def _commitments(events):
    grouped={}
    for e in events:
        if e.get('kind')!='vow' or float(e.get('importance',0))<.5 or not e.get('theme'):continue
        theme=_bounded_text(e['theme'],'COMMITMENT_THEME')
        z=grouped.setdefault(theme,{'count':0,'first_event_seq':int(e['seq']),'last_event_seq':int(e['seq']),'max_importance':0.0})
        z['count']+=1;z['last_event_seq']=int(e['seq']);z['max_importance']=max(z['max_importance'],float(e['importance']))
    out=[]
    for theme,z in grouped.items():
        strength=round(min(1.0,z['max_importance']+.05*max(0,z['count']-1)),6)
        out.append({'theme':theme,'status':'ACTIVE' if z['count']>=2 else 'CANDIDATE','evidence_count':z['count'],
                    'strength':strength,'first_event_seq':z['first_event_seq'],'last_event_seq':z['last_event_seq']})
    return sorted(out,key=lambda x:x['theme'])


def _narrative(soul,h,commitments,temporal_state,purpose_state):
    ranked=sorted(
        ({'theme':k,'encounters':int(v.get('encounters',0)),'weight':round(float(v.get('weight',0)),6)}
         for k,v in soul.get('themes',{}).items()),
        key=lambda x:(abs(x['weight']),x['encounters'],x['theme']),reverse=True)[:12]
    return {
        'identity_evidence':{
            'individual_id':soul['individual_id'],
            'transition_count':int(temporal_state.get('transition_count',0)),
            'transition_head_sha256':temporal_state.get('transition_head_sha256',ZERO),
            'same_origin_required':True,
        },
        'experience_evidence':{
            'soul_update_seq':int(soul.get('update_seq',0)),
            'heart_meaning_count':len(h.get('episodic_meanings',[])),
            'persistent_themes':ranked,
            'scar_count':len(soul.get('scars',[])),
        },
        'commitments':copy.deepcopy(commitments),
        'active_purpose':purpose_state.get('active_purpose'),
        'interpretation':'EVIDENCE_BOUNDED_FUNCTIONAL_SELF_NARRATIVE',
    }


def _facets(data,soul,h,commitments,temporal_state,purpose_state):
    """Several evidence views, never a claim that any tradition is literally implemented."""
    hp=Path(data)/'v983'/'HOMEOSTASIS_STATE.json';home=_read_json(hp) if hp.is_file() else None
    needs=(home or {}).get('needs',{});episodes=len(h.get('episodic_meanings',[]));attachments=soul.get('attachments',{})
    active=sum(c['status']=='ACTIVE' for c in commitments)
    raw={
        'continuity':(.2+min(.8,float(temporal_state.get('transition_count',0))*.04),int(temporal_state.get('transition_count',0)),'v989_temporal_identity'),
        'embodied_regulation':(max([float(x) for x in needs.values()]+[float(h.get('emotion',{}).get('arousal',0)),float(h.get('emotion',{}).get('threat',0))]),len(needs),'v983_homeostasis_and_heart'),
        'autobiographical':(min(1.0,episodes/16),episodes,'v978_episodic_meanings'),
        'axiological':(min(1.0,(active*2+len(soul.get('vows',[])))/8),active,'canonical_vows_and_core_values'),
        'relational':(min(1.0,max([abs(float(v)) for v in attachments.values()]+[0.0])+len(attachments)*.05),len(attachments),'v977_attachments'),
        'epistemic':((float(soul['core_values'].get('curiosity',0))+float(soul['core_values'].get('truthfulness',0)))/2,episodes,'core_values_and_experience'),
    }
    facets={k:{'salience':round(max(0,min(1,v[0])),6),'evidence_count':int(v[1]),'source':v[2]} for k,v in raw.items()}
    ranked=sorted(facets,key=lambda k:(facets[k]['salience'],k),reverse=True)
    workspace={'schema':'tukuyo.v1022_6_8.bounded_workspace/1','selected_facets':ranked[:3],
               'broadcast':{'active_purpose':purpose_state.get('active_purpose'),'active_commitments':[c['theme'] for c in commitments if c['status']=='ACTIVE']},
               'selection_rule':'TOP_EVIDENCE_SALIENCE','global_availability_is_not_consciousness_claim':True}
    return facets,workspace


def _validate_option(o):
    if not isinstance(o,dict) or set(o)-{'id','signals','themes','conflicts'}:raise ValueError('SOUL_INTEGRITY_OPTION_FIELDS')
    oid=_bounded_text(o.get('id'),'OPTION_ID',64)
    sig=o.get('signals',{})
    if not isinstance(sig,dict) or set(sig)-set(SIGNALS):raise ValueError('SOUL_INTEGRITY_SIGNALS')
    signals={}
    for k,v in sig.items():
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not -1<=float(v)<=1:raise ValueError('SOUL_INTEGRITY_SIGNAL_RANGE')
        signals[k]=round(float(v),6)
    def themes(name):
        vals=o.get(name,[])
        if not isinstance(vals,list) or len(vals)>16:raise ValueError('SOUL_INTEGRITY_'+name.upper())
        got=sorted({_bounded_text(x,name.upper()+'_THEME') for x in vals})
        return got
    support=themes('themes');conflicts=themes('conflicts')
    if set(support)&set(conflicts):raise ValueError('SOUL_INTEGRITY_ANNOTATION_CONFLICT')
    return {'id':oid,'signals':signals,'themes':support,'conflicts':conflicts}


def _decision_hash(row):
    q=dict(row);q.pop('decision_sha256',None);return sha_obj(q)


def validate(state):
    if not isinstance(state,dict) or state.get('schema')!=SCHEMA:raise ValueError('SOUL_INTEGRITY_SCHEMA')
    required={'schema','individual_id','lineage_id','branch_id','integration_seq','source','commitments','narrative','facets','workspace','decisions','decision_head_sha256','claim_boundary'}
    if set(state)!=required:raise ValueError('SOUL_INTEGRITY_FIELDS')
    for k in ('individual_id','lineage_id','branch_id'):_bounded_text(state[k],k.upper(),160)
    if type(state['integration_seq']) is not int or state['integration_seq']<1:raise ValueError('SOUL_INTEGRITY_SEQ')
    if not isinstance(state['source'],dict) or set(state['source'])!={'soul_sha256','heart_projection_sha256','temporal_state_sha256','purpose_state_sha256'}:raise ValueError('SOUL_INTEGRITY_SOURCE')
    if any(not isinstance(v,str) or not re.fullmatch(r'[0-9a-f]{64}',v) for v in state['source'].values()):raise ValueError('SOUL_INTEGRITY_SOURCE_HASH')
    if not isinstance(state['commitments'],list) or len(state['commitments'])>32:raise ValueError('SOUL_INTEGRITY_COMMITMENTS')
    for c in state['commitments']:
        if set(c)!={'theme','status','evidence_count','strength','first_event_seq','last_event_seq'} or c['status'] not in ('CANDIDATE','ACTIVE'):raise ValueError('SOUL_INTEGRITY_COMMITMENT')
        _bounded_text(c['theme'],'COMMITMENT_THEME')
        if type(c['evidence_count']) is not int or c['evidence_count']<1 or (c['status']=='ACTIVE')!=(c['evidence_count']>=2):raise ValueError('SOUL_INTEGRITY_COMMITMENT_EVIDENCE')
        if not 0<=float(c['strength'])<=1:raise ValueError('SOUL_INTEGRITY_COMMITMENT_STRENGTH')
    if not isinstance(state['narrative'],dict):raise ValueError('SOUL_INTEGRITY_NARRATIVE')
    if set(state['facets'])!={'continuity','embodied_regulation','autobiographical','axiological','relational','epistemic'}:raise ValueError('SOUL_INTEGRITY_FACETS')
    for f in state['facets'].values():
        if set(f)!={'salience','evidence_count','source'} or not 0<=float(f['salience'])<=1 or type(f['evidence_count']) is not int or f['evidence_count']<0:raise ValueError('SOUL_INTEGRITY_FACET')
    w=state['workspace']
    if not isinstance(w,dict) or w.get('schema')!='tukuyo.v1022_6_8.bounded_workspace/1' or w.get('global_availability_is_not_consciousness_claim') is not True:raise ValueError('SOUL_INTEGRITY_WORKSPACE')
    if not isinstance(w.get('selected_facets'),list) or not 1<=len(w['selected_facets'])<=3 or not set(w['selected_facets'])<=set(state['facets']):raise ValueError('SOUL_INTEGRITY_WORKSPACE_SELECTION')
    rows=state['decisions']
    if not isinstance(rows,list) or len(rows)>64:raise ValueError('SOUL_INTEGRITY_DECISIONS')
    prev=ZERO
    for i,row in enumerate(rows,1):
        if not isinstance(row,dict) or row.get('seq')!=i or row.get('previous_decision_sha256')!=prev or row.get('decision_sha256')!=_decision_hash(row):raise ValueError('SOUL_INTEGRITY_DECISION_CHAIN')
        opts=[_validate_option(x) for x in row.get('options',[])]
        if opts!=row.get('options') or sha_obj(opts)!=row.get('options_sha256'):raise ValueError('SOUL_INTEGRITY_DECISION_OPTIONS')
        ids=[x['id'] for x in opts]
        if len(ids)<2 or len(set(ids))!=len(ids):raise ValueError('SOUL_INTEGRITY_DECISION_IDS')
        base=row.get('base_scores');adj=row.get('adjustments');full=row.get('full_scores')
        if set(base)!=set(ids) or set(adj)!=set(ids) or set(full)!=set(ids):raise ValueError('SOUL_INTEGRITY_DECISION_SCORES')
        for oid in ids:
            if round(float(base[oid])+float(adj[oid]),6)!=float(full[oid]) or not -1.5<=float(adj[oid])<=1.5:raise ValueError('SOUL_INTEGRITY_DECISION_REPLAY')
        ranked=sorted(ids,key=lambda x:(float(full[x]),x),reverse=True);best=ranked[0];margin=round(float(full[best])-float(full[ranked[1]]),6);review=margin<.1;counter=max(ids,key=lambda x:(float(base[x]),x))
        if row.get('best_candidate')!=best or float(row.get('score_margin',-1))!=margin or row.get('review_required')!=review or row.get('action_taken')!=(not review):raise ValueError('SOUL_INTEGRITY_METACOGNITION')
        expected=None if review else best
        if row.get('chosen')!=expected or row.get('counterfactual_without_integrated_soul')!=counter or row.get('choice_changed_by_integrated_soul')!=(expected is not None and expected!=counter):raise ValueError('SOUL_INTEGRITY_DECISION_RESULT')
        prev=row['decision_sha256']
    if state['decision_head_sha256']!=prev:raise ValueError('SOUL_INTEGRITY_DECISION_HEAD')
    cb=state['claim_boundary']
    if not isinstance(cb,dict) or cb.get('literal_soul_established') is not False or cb.get('consciousness_established') is not False:raise ValueError('SOUL_INTEGRITY_CLAIM_BOUNDARY')


def load(data):
    if not (Path(data)/NS/'commits').exists():
        if needs_preflight(data):raise ValueError('SOUL_INTEGRITY_HISTORY_MISSING')
        raise ValueError('SOUL_INTEGRITY_NOT_INITIALIZED')
    return store.load(data,NS,COMPONENT,validate)


def _read_json(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def _current_sources(data):
    soul=load_soul(data);h=heart.load(data)
    temporal.sync_transitions(data);ts=_read_json(temporal.state_path(data))
    purpose.integrate(data);ps=_read_json(purpose.state_path(data))
    return soul,h,ts,ps,{
        'soul_sha256':sha_obj(soul),'heart_projection_sha256':sha_obj(_heart_projection(h)),
        'temporal_state_sha256':sha_obj(ts),'purpose_state_sha256':sha_obj(ps),
    }


@transactional()
def integrate(data):
    require_alive(data);ident=_live_identity(data);soul,h,ts,ps,sources=_current_sources(data)
    commitments=_commitments(_soul_events(data))
    try:old=load(data)
    except ValueError as e:
        if str(e)!='SOUL_INTEGRITY_NOT_INITIALIZED':raise
        old=None
    facets,workspace=_facets(data,soul,h,commitments,ts,ps)
    state={
        'schema':SCHEMA,'individual_id':ident['individual_id'],'lineage_id':ident['lineage_id'],'branch_id':ident['branch_id'],
        'integration_seq':int(old.get('integration_seq',0))+1 if old else 1,'source':sources,
        'commitments':commitments,'narrative':_narrative(soul,h,commitments,ts,ps),'facets':facets,'workspace':workspace,
        'decisions':copy.deepcopy(old.get('decisions',[])) if old else [],
        'decision_head_sha256':old.get('decision_head_sha256',ZERO) if old else ZERO,
        'claim_boundary':{
            'functional_soul_integration':True,'canonical_experience_grounded':True,
            'mature_commitment_requires_two_events':True,'counterfactual_choice_recorded':True,
            'private_narrative_inherited':False,'option_annotations_semantically_independent':False,
            'bounded_global_availability_not_consciousness':True,'neuroscience_inspiration_not_mechanistic_equivalence':True,
            'cross_cultural_descriptions_are_design_lenses_not_factual_proof':True,
            'literal_soul_established':False,'consciousness_established':False,
        },
    }
    validate(state);store.save(data,NS,COMPONENT,state)
    return _public(state)


def _adjustment(state,opt):
    total=0.0;parts={}
    for c in state['commitments']:
        if c['status']!='ACTIVE':continue
        theme=c['theme'];delta=0.0
        if theme in opt['themes']:delta+=float(c['strength'])*.45
        if theme in opt['conflicts']:delta-=float(c['strength'])*.9
        if delta:parts['commitment:'+theme]=round(delta,6);total+=delta
    goal=state['narrative'].get('active_purpose');signal=PURPOSE_SIGNAL.get(goal)
    if signal:
        delta=float(opt['signals'].get(signal,0))*.2
        if delta:parts['purpose:'+goal]=round(delta,6);total+=delta
    return round(max(-1.5,min(1.5,total)),6),parts


@transactional()
def deliberate(data,options,context=''):
    require_alive(data);_bounded_text(context or 'bounded_decision','CONTEXT',256)
    normalized=[_validate_option(x) for x in options]
    if not 2<=len(normalized)<=16 or len({x['id'] for x in normalized})!=len(normalized):raise ValueError('SOUL_INTEGRITY_OPTIONS')
    integrate(data);state=load(data);soul=load_soul(data);h=heart.load(data)
    base={};adjustments={};parts={}
    for opt in normalized:
        score,_=heart._score_option(data,soul,h,opt);base[opt['id']]=score
        adjustments[opt['id']],parts[opt['id']]=_adjustment(state,opt)
    proposed={oid:round(float(base[oid])+float(adjustments[oid]),6) for oid in base}
    ranking=sorted(proposed,key=lambda x:(proposed[x],x),reverse=True);best=ranking[0];margin=round(proposed[best]-proposed[ranking[1]],6);review=margin<.1
    if review:
        scores=sorted(({'id':oid,'score':proposed[oid],'parts':{'whole_soul_integrity':adjustments[oid]}} for oid in proposed),key=lambda x:(x['score'],x['id']),reverse=True)
        chosen=None
    else:
        result=heart.choose(data,normalized,context,adjustments=adjustments,adjustment_label='whole_soul_integrity');scores=result['scores'];chosen=result['chosen']
    full={x['id']:float(x['score']) for x in scores}
    seq=len(state['decisions'])+1
    row={
        'seq':seq,'context':context,'options':normalized,'options_sha256':sha_obj(normalized),
        'base_scores':base,'adjustments':adjustments,'adjustment_parts':parts,'full_scores':full,
        'best_candidate':best,'score_margin':margin,'review_required':review,'action_taken':not review,'chosen':chosen,
        'counterfactual_without_integrated_soul':max(base,key=lambda x:(base[x],x)),
        'choice_changed_by_integrated_soul':chosen is not None and chosen!=max(base,key=lambda x:(base[x],x)),
        'active_commitments':[copy.deepcopy(x) for x in state['commitments'] if x['status']=='ACTIVE'],
        'active_purpose':state['narrative'].get('active_purpose'),'source':copy.deepcopy(state['source']),
        'previous_decision_sha256':state['decision_head_sha256'],
        'conditional_on_option_annotations':True,
    }
    row['decision_sha256']=_decision_hash(row);state['decisions'].append(row);state['decision_head_sha256']=row['decision_sha256']
    validate(state);store.save(data,NS,COMPONENT,state)
    return {'ok':True,'version':'v1022.6.8','chosen':row['chosen'],'best_candidate':best,'uncertain':review,'review_required':review,'score_margin':margin,
            'counterfactual_without_integrated_soul':row['counterfactual_without_integrated_soul'],
            'choice_changed_by_integrated_soul':row['choice_changed_by_integrated_soul'],'scores':scores,'adjustment_parts':parts,
            'active_commitments':row['active_commitments'],'active_purpose':row['active_purpose'],'decision_sha256':row['decision_sha256'],
            'conditional_on_option_annotations':True,'claim_boundary':state['claim_boundary']}


def _public(state):
    active=[x for x in state['commitments'] if x['status']=='ACTIVE'];candidate=[x for x in state['commitments'] if x['status']=='CANDIDATE']
    return {'ok':True,'version':'v1022.6.8','individual_id':state['individual_id'],'integration_seq':state['integration_seq'],
            'active_commitments':active,'candidate_commitments':candidate,'active_purpose':state['narrative'].get('active_purpose'),
            'facets':state['facets'],'bounded_workspace':state['workspace'],
            'transition_count':state['narrative']['identity_evidence']['transition_count'],'decision_count':len(state['decisions']),
            'decisions_changed_by_integrated_soul':sum(bool(x['choice_changed_by_integrated_soul']) for x in state['decisions']),
            'source':state['source'],'claim_boundary':state['claim_boundary']}


def status(data):
    state=load(data);out=_public(state);out['audit']=audit(data);return out


def audit(data):
    try:
        state=load(data);ident=_live_identity(data);errors=[]
        if any(state.get(k)!=ident[k] for k in ('individual_id','lineage_id','branch_id')):errors.append('SOUL_INTEGRITY_IDENTITY')
        soul=load_soul(data);h=heart.load(data)
        stale=(state['source']['soul_sha256']!=sha_obj(soul) or state['source']['heart_projection_sha256']!=sha_obj(_heart_projection(h)))
        return {'ok':not errors,'version':'v1022.6.8','errors':errors,'stale_sources':stale,'decision_count':len(state['decisions']),
                'active_commitments':sum(x['status']=='ACTIVE' for x in state['commitments']),
                'counterfactual_certificates_valid':True,'literal_soul_established':False,'consciousness_established':False}
    except (ValueError,TypeError,KeyError,OSError) as e:
        return {'ok':False,'version':'v1022.6.8','errors':[type(e).__name__+':'+str(e)],'literal_soul_established':False,'consciousness_established':False}


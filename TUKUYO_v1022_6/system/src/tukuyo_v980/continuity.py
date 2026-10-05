from __future__ import annotations
from tukuyo_v977.whole_state import load_soul,sha_obj,_live_identity,_default_soul
from tukuyo_v978.heart_loop import choose,load as load_heart,audit as heart_audit,_score_option
from tukuyo_v979.deep_core import consolidate,load as load_deep,forget_surface_memory


def _counterfactual_unexperienced_choice(data,options):
    """Choice of the same individual with the default soul/neutral heart.

    This is a negative control: an assay is only discriminating if the persistent
    deep state changes the selected option relative to this counterfactual.
    """
    soul=_default_soul(_live_identity(data))
    heart={'emotion':{'trust':0.5,'threat':0.0},'value_bias':{}}
    scored=[]
    for o in options:
        score,parts=_score_option(data,soul,heart,o);scored.append({'id':o['id'],'score':score,'parts':parts})
    ranked=sorted(scored,key=lambda x:(x['score'],x['id']),reverse=True)
    return {'chosen':ranked[0]['id'],'scores':ranked}


def run(data,options,context='continuity_assay'):
    ident=_live_identity(data);s0=load_soul(data);h0=load_heart(data)
    c=consolidate(data);d0=load_deep(data);control=_counterfactual_unexperienced_choice(data,options);before=choose(data,options,context+'-before')
    loss=forget_surface_memory(data);s1=load_soul(data);d1=load_deep(data);after=choose(data,options,context+'-after')
    checks={
      'identity_continuity':ident['individual_id']==_live_identity(data)['individual_id'],
      'soul_core_preserved':sha_obj(s0)==sha_obj(s1),
      'deep_core_preserved':d0['core_sha256']==d1['core_sha256'],
      'vow_preserved':s0.get('vows')==s1.get('vows'),
      'scar_preserved':s0.get('scars')==s1.get('scars'),
      'choice_tendency_preserved':before['chosen']==after['chosen'],
      'discriminating_against_unexperienced_control':before['chosen']!=control['chosen'],
      'surface_memory_removed':len(load_heart(data).get('episodic_meanings',[]))==0 and not load_heart(data).get('meaning_weights'),
      'heart_chain_valid':heart_audit(data)['ok'],
    }
    return {'ok':all(checks.values()),'version':'v989','checks':checks,'before_choice':before['chosen'],'after_choice':after['chosen'],'unexperienced_control_choice':control['chosen'],'unexperienced_control_scores':control['scores'],'surface_loss':loss,
      'error':None if checks['discriminating_against_unexperienced_control'] else 'NON_DISCRIMINATING_CONTINUITY_ASSAY',
      'claim_boundary':{'functional_soul_continuity_assay':True,'negative_control_required':True,'literal_soul_established':False,'consciousness_established':False,'fork_divergence_tested':False,'long_wallclock_tested':False}}

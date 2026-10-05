from __future__ import annotations
import copy
from tukuyo_v977.whole_state import load_soul
from tukuyo_v978.heart_loop import load as load_heart,_score_option
from tukuyo_v993.relation_bound import model as relation_model
from tukuyo_v995.other_agent_trust import peer

def infer_exposure(peer_id,opt,context=''):
    if 'relation_exposure' in opt:return max(0.0,min(1.0,float(opt['relation_exposure'])))
    if opt.get('relation_independent') is True:return 0.0
    refs=[]
    for k in ('peer_id','relation','actor','target'):
        if opt.get(k) is not None:refs.append(str(opt.get(k)))
    text=' '.join([str(opt.get('id','')),str(opt.get('label','')),str(opt.get('description','')),str(context)])
    if str(peer_id) in refs or (peer_id and str(peer_id) in text):return 1.0
    return 1.0 if peer_id else 0.0

def choose(data,peer_id,options,context=''):
    if not isinstance(options,list) or len(options)<2:raise ValueError('V997_OPTIONS_REQUIRED')
    soul=load_soul(data);heart=copy.deepcopy(load_heart(data));pm=peer(data,peer_id);rm=relation_model(data,peer_id)
    # A peer-scoped decision must not inherit unrelated peers' global social-trust depression.
    # Use the target peer's reconstructed trust/risk while retaining other non-social heart state.
    heart['emotion']['trust']=float(pm.get('trust',0.5))
    rows=[]
    for o0 in options:
        o=copy.deepcopy(o0)
        if not isinstance(o.get('id'),str) or not o['id']:raise ValueError('V997_OPTION_ID')
        exposure=infer_exposure(peer_id,o,context);base,parts=_score_option(data,soul,heart,o)
        rel_adj=exposure*((float(rm.get('trust',.5))-.5)*.75+float(rm.get('attachment',0))*.30-float(rm.get('risk',0))*.72)
        hist_adj=exposure*((float(pm.get('trust',.5))-.5)*.38-float(pm.get('unresolved_harm',0))*.34+max(-.2,min(.2,float(pm.get('trend',0))*.12)))
        score=round(base+rel_adj+hist_adj,6)
        rows.append({'id':o['id'],'score':score,'base_score':base,'relation_adjustment':round(rel_adj,6),'peer_history_adjustment':round(hist_adj,6),'relation_exposure':exposure,'auto_relation_exposure':('relation_exposure' not in o0),'parts':parts})
    ranked=sorted(rows,key=lambda z:(z['score'],z['id']),reverse=True)
    return {'ok':True,'version':'v997','peer_id':peer_id,'context':context,'chosen':ranked[0]['id'],'scores':ranked,'peer_model':pm,'relation_model':rm,
            'claim_boundary':{'peer_scoped_choice_auto_applies_relation_history':True,'manual_engages_relation_not_required':True,'unrelated_peer_global_trust_not_reused':True,'tag_change_does_not_reset_peer_history':True,'decision_is_peer_specific':True,'theory_of_mind_established':False}}

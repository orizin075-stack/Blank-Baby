"""v1022.8.1 goals it forms from what it lived, acts on, and revises by what comes of its acts (目標).

A goal is never given to it. It is formed from its soul journal (v977, the canonical record of its life), by a few
plain rules, and keeps the experiences it came from:

  guard_against:R   警戒する      two or more harmful experiences with R (a betrayal, harm, a bad outcome with R) that
                                  outweigh the good ones (recent ones weighing more)
  rebuild_trust:R   信頼を取り戻す it guarded against R, and the good experiences with R have come to outweigh the harm
  rely_on:R         頼る          two or more good experiences with R (support, a good outcome with R), none harmful;
                                  or, after rebuilding, the good outweighs the harm twice over
  pursue:T          探究する      two or more discoveries or good outcomes in theme T, the last two not both bad
  give_up:T         あきらめる    it pursued T, and its last two outcomes in T were bad
  keep_vow:T        誓いを守る    a vow it made

The generation-4 life (themes g4:...) has its own purposes (tukuyo_g4.life.reflect: what it wants to learn) and is not
read here. Each time the record changes the goals are formed again; a goal that appears, changes or goes is written to
the ledger with the experiences that did it (formed, revised from -> to, dropped), so the ledger is the history of its
purposes. goal-audit forms them again from the record and checks the ledger against it.

Goals act: goal-choose scores the options with its heart (v978) and adds, for each active goal an option touches (its
relation, its themes), a bounded term (the heart's own external-adjustment path, labelled 'goals'); the scores show
the parts. goal-outcome takes in what came of the chosen option as an experience with that option's relation and
theme, and forms the goals again - so an outcome can revise the goal that chose the act.

A functional model of purposes: no claim of consciousness, will or literal desire.
"""
from __future__ import annotations
import copy,math
from pathlib import Path

from tukuyo_v977 import whole_state as whole
from tukuyo_v977.whole_state import sha_obj
from tukuyo_v1019.transaction import transactional
from . import store

NS='experiential_goals';COMPONENT='whole_experiential_goals';SCHEMA='tukuyo.v1022_8_1.experiential_goals/1';VERSION='v1022.8.1'
HARM={'betrayal','harm'};HELP={'support','kindness','care'};GOOD_THEME={'discovery','learning'}
DECAY=.8
WEIGHT={'guard_against':-.6,'rely_on':.4,'rebuild_trust':.25,'pursue':.5,'give_up':-.5}
WORDS={'guard_against':'警戒する','rebuild_trust':'信頼を取り戻す','rely_on':'頼る','pursue':'探究する','give_up':'あきらめる','keep_vow':'誓いを守る'}
CLAIMS={'goals_formed_from_its_own_record':True,'goals_given_by_caller':False,'consciousness_established':False,'literal_desire_established':False}


def _events(data):
    from tukuyo_common.journal import load_events
    return [e for e in load_events(whole.event_path(data)) if not str(e.get('theme','')).startswith('g4:')]


def _strength(w):return round(1-math.exp(-max(0.0,w)),6)


class Record:
    """what its life says of each relation, theme and vow, taken in one experience at a time"""
    def __init__(s):s.rel={};s.theme={};s.vows={}
    def take(s,e):
        k=e.get('kind');v=float(e.get('valence',0));imp=float(e.get('importance',0));r=e.get('relation') or '';t=e.get('theme') or ''
        harmful=(k in HARM and v<0) or (k=='action_feedback' and v<0 and r);helpful=(k in HELP and v>0) or (k=='action_feedback' and v>0 and r)
        if r and (harmful or helpful):
            q=s.rel.setdefault(r,{'harm':0.0,'help':0.0,'n_harm':0,'n_help':0,'seqs':[]})
            for x in ('harm','help'):q[x]*=DECAY
            q['harm' if harmful else 'help']+=imp*abs(v);q['n_harm' if harmful else 'n_help']+=1;q['seqs']=(q['seqs']+[e['seq']])[-8:]
        if t and not t.startswith('observed:') and k!='vow':
            good=(k in GOOD_THEME and v>0) or (k=='action_feedback' and v>0);bad=(k=='action_feedback' and v<0) or (k in HARM and v<0)
            if good or bad:
                q=s.theme.setdefault(t,{'good':0,'bad':0,'last':[],'seqs':[]})
                q['good' if good else 'bad']+=1;q['last']=(q['last']+['bad' if bad else 'good'])[-2:];q['seqs']=(q['seqs']+[e['seq']])[-8:]
        if k=='vow' and t and imp>=.5:s.vows[t]=(s.vows.get(t,[])+[e['seq']])[-8:]
    def goals(s,before=None):
        """the goals this record supports, given the goals it had"""
        before=before or {};goals={}
        def put(kind,target,w,seqs):goals[f'{kind}:{target}']={'kind':kind,'target':target,'strength':_strength(w),'reasons':sorted(seqs)}
        for r,q in s.rel.items():
            guarded=('guard_against:'+r) in before or ('rebuild_trust:'+r) in before
            if q['n_harm']>=2 and q['harm']>q['help']:put('guard_against',r,q['harm']-q['help'],q['seqs'])
            elif guarded and q['help']>=2*q['harm'] and q['n_help']>=q['n_harm']+2:put('rely_on',r,q['help']-q['harm'],q['seqs'])
            elif guarded and q['help']>=q['harm']:put('rebuild_trust',r,q['help']-q['harm']+.2,q['seqs'])
            elif q['n_help']>=2 and q['n_harm']==0:put('rely_on',r,q['help'],q['seqs'])
        for t,q in s.theme.items():
            pursued=('pursue:'+t) in before or ('give_up:'+t) in before
            if pursued and q['last']==['bad','bad']:put('give_up',t,q['bad']*.5,q['seqs'])
            elif q['good']>=2 and q['last']!=['bad','bad']:put('pursue',t,q['good']*.5-q['bad']*.25,q['seqs'])
        for t,seqs in s.vows.items():put('keep_vow',t,len(seqs),seqs)
        return goals


def form(events,before=None):
    """the goals a record supports (pure: the same record and the same past give the same goals)"""
    rec=Record()
    for e in events:rec.take(e)
    return rec.goals(before)


FAMILY={'guard_against':'relation','rebuild_trust':'relation','rely_on':'relation','pursue':'theme','give_up':'theme','keep_vow':'vow'}
def _changes(before,after,at):
    """what changed between two goal sets: formed, revised (the same target, another goal of its family), dropped"""
    out=[];same=lambda a,b:a['target']==b['target'] and FAMILY[a['kind']]==FAMILY[b['kind']]
    for gid,g in after.items():
        if gid in before:continue
        prev=next((b for b in before.values() if same(b,g)),None)
        out.append({'change':'revised' if prev else 'formed','goal':gid,'from':f"{prev['kind']}:{prev['target']}" if prev else None,'at_soul_seq':at,'reasons':g['reasons']})
    for gid,b in before.items():
        if gid not in after and not any(same(b,g) for g in after.values()):
            out.append({'change':'dropped','goal':gid,'from':None,'at_soul_seq':at,'reasons':[at]})   # the experience it no longer stood
    return out


def _validate(s):
    if s.get('schema')!=SCHEMA or s.get('claim_boundary')!=CLAIMS or not isinstance(s.get('goals'),dict) or not isinstance(s.get('history'),list):
        raise ValueError('GOALS_SCHEMA')


def _load(data):
    if not (Path(data)/NS/'commits').exists():return None
    return store.load(data,NS,COMPONENT,_validate)


def _new(data):
    ident=whole._live_identity(data)
    return {'schema':SCHEMA,'individual_id':ident['individual_id'],'goals':{},'history':[],'formed_at_soul_seq':0,'last_choice':None,'claim_boundary':CLAIMS}


def _replay(events):
    """the ledger the record gives: its goals formed again after every experience, in order"""
    rec=Record();goals={};history=[];seq=0
    for e in events:
        rec.take(e);new=rec.goals(goals)
        if set(new)!=set(goals):history+=_changes(goals,new,e['seq'])
        goals=new;seq=e['seq']
    return goals,history,seq


@transactional()
def form_now(data):
    """form its goals from its record as it is now; what changed is written to the ledger"""
    from tukuyo_v1019.lifecycle import require_alive
    require_alive(data)
    s=_load(data) or _new(data);events=_events(data)
    goals,history,seq=_replay(events)
    changes=history[len(s['history']):] if history[:len(s['history'])]==s['history'] else history
    if (goals,history,seq)!=(s['goals'],s['history'],s['formed_at_soul_seq']) or not (Path(data)/NS/'commits').exists():
        s.update({'goals':goals,'history':history,'formed_at_soul_seq':seq})
        _validate(s);store.save(data,NS,COMPONENT,s)
    return {'ok':True,'version':VERSION,'goals':_public_goals(goals),'changes':changes,'formed_at_soul_seq':seq,'claim_boundary':CLAIMS}


def _public_goals(goals):
    return [{'goal':gid,'words':WORDS[g['kind']]+' '+g['target'],**g} for gid,g in sorted(goals.items(),key=lambda kv:-kv[1]['strength'])]


def adjustments(goals,options):
    """for each option, the bounded term its active goals add (an option touches a goal through its relation or themes)"""
    out={};why={}
    for o in options:
        d=0.0;parts=[]
        for gid,g in goals.items():
            w=WEIGHT.get(g['kind'])
            if w is None:continue
            hit=(g['kind'] in ('guard_against','rely_on','rebuild_trust') and o.get('relation')==g['target']) or \
                (g['kind'] in ('pursue','give_up') and g['target'] in (o.get('themes') or []))
            if hit:d+=w*g['strength'];parts.append(gid)
        out[o['id']]=round(max(-1.5,min(1.5,d)),6);why[o['id']]=parts
    return out,why


@transactional()
def choose(data,options,context='',use_goals=True):
    """the heart chooses, with its goals (use_goals=False: the heart alone, for comparison)"""
    from tukuyo_v978 import heart_loop
    r=form_now(data);s=_load(data)
    adj,why=adjustments(s['goals'],options)
    res=heart_loop.choose(data,options,context=context or 'goals',adjustments=adj if use_goals else None,adjustment_label='goals')
    o=next(x for x in options if x['id']==res['chosen'])
    s['last_choice']={'chosen':res['chosen'],'relation':o.get('relation') or '','themes':list(o.get('themes') or []),'goals':why[res['chosen']],
                      'with_goals':bool(use_goals),'context':context}
    _validate(s);store.save(data,NS,COMPONENT,s);whole.sync(data)
    return {'ok':True,'version':VERSION,'chosen':res['chosen'],'scores':res['scores'],'goal_terms':adj if use_goals else None,
            'goals_that_touched_it':why[res['chosen']] if use_goals else [],'goals':r['goals'],'claim_boundary':CLAIMS}


@transactional()
def outcome(data,valence,importance=.6,origin='told'):
    """what came of the chosen option, taken in as an experience with its relation and theme; the goals are formed again"""
    from tukuyo_v978.heart_loop import process_experience
    from tukuyo_v1022.provenance import CLAIMABLE
    if origin not in CLAIMABLE:raise ValueError('EXPERIENCE_ORIGIN_NOT_YOURS_TO_SAY:'+str(origin)[:32])
    if type(valence) not in (int,float) or not -1<=valence<=1 or type(importance) not in (int,float) or not 0<importance<=1:raise ValueError('GOAL_OUTCOME_RANGE')
    s=_load(data)
    if not s or not s.get('last_choice'):raise ValueError('GOAL_OUTCOME_WITHOUT_CHOICE')
    c=s['last_choice'];r=c['relation'];t=(c['themes'] or [c['chosen']])[0]
    kind='support' if (r and valence>0) else 'betrayal' if (r and valence<=-.5) else 'action_feedback'
    process_experience(data,kind,float(valence),float(importance),t,r,origin=origin)
    from tukuyo_v993.relation_bound import sync as relation_sync
    from tukuyo_v995.other_agent_trust import sync as peer_sync
    relation_sync(data);peer_sync(data)
    s=_load(data);s['last_choice']=None;_validate(s);store.save(data,NS,COMPONENT,s)
    f=form_now(data);whole.sync(data)
    return {'ok':True,'version':VERSION,'took_in':{'kind':kind,'valence':valence,'theme':t,'relation':r,'origin':origin},'changes':f['changes'],'goals':f['goals']}


def status(data):
    s=_load(data)
    if s is None:return {'ok':True,'version':VERSION,'goals':[],'history':[],'formed':False}
    return {'ok':True,'version':VERSION,'goals':_public_goals(s['goals']),'history':s['history'],'formed_at_soul_seq':s['formed_at_soul_seq'],
            'last_choice':s.get('last_choice'),'claim_boundary':CLAIMS}


def audit(data):
    """the ledger is what its record gives: the goals are formed again from the soul journal and compared"""
    try:
        s=_load(data)
        if s is None:return {'ok':True,'version':VERSION,'errors':[],'formed':False}
        events=_events(data);upto=[e for e in events if e['seq']<=s['formed_at_soul_seq']]
        goals,history,seq=_replay(upto);errors=[]
        if s['individual_id']!=whole._live_identity(data)['individual_id']:errors.append('GOALS_IDENTITY')
        if goals!=s['goals']:errors.append('GOALS_NOT_FROM_ITS_RECORD')
        if history!=s['history']:errors.append('GOAL_HISTORY_NOT_FROM_ITS_RECORD')
        return {'ok':not errors,'version':VERSION,'errors':errors,'goals':len(s['goals']),'changes':len(s['history'])}
    except Exception as e:  # noqa: BLE001 - an unreadable ledger is an audit failure, not a crash
        return {'ok':False,'version':VERSION,'errors':[type(e).__name__+':'+str(e)[:120]]}

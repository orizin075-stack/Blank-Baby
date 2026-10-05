"""Open-world research agent for the V1023r preview (claude-patch5).

The agent only sees observations.  It keeps
  * a hypothesis language in tiers (laws of growing description length),
  * a catch-all "OUTSIDE" model (an unknown per-input table) so that the
    known laws can lose to "something I cannot express",
  * Bayesian beliefs under the published sensor bound,
and it
  * picks the experiment with the largest expected information gain,
  * widens its language when OUTSIDE wins, and changes method (law -> table)
    when even the widest language loses,
  * claims a law only after replication on inputs chosen by the environment,
  * retracts a confirmed law when a noise-free outcome contradicts it.

Nothing in this module may import the world implementation's secret parts;
it imports only the public library of law descriptions and constants.
"""
from __future__ import annotations
import math
from .worlds import library,INPUTS,N,SENSOR_BOUND,LOCKS,bit

EPS=SENSOR_BOUND;EPS_WORK=0.005;LOG_FLOOR=-30.0
_LIB=library()
_TABLES=[r[2] for r in _LIB];_TIERS=[r[0] for r in _LIB];_NAMES=[r[1] for r in _LIB]
_TIER_SIZE={t:_TIERS.count(t) for t in (1,2,3)}
_LOGPRIOR=[math.log(.9/3/_TIER_SIZE[t]) for t in _TIERS]
# All lock configurations (which switches are fixed and to what).
import itertools as _it
CONFIGS=[{i:v for i,v in zip(c,vals)} for c in _it.combinations(range(N),LOCKS) for vals in _it.product((0,1),repeat=LOCKS)]
def free_inputs(locked):return [x for x in range(INPUTS) if all(bit(x,i)==v for i,v in locked.items())]
_CFG_X=[free_inputs(c) for c in CONFIGS]
def _achievable(t):return sum(1 for xs in _CFG_X if any(bit(t,x) for x in xs))/len(CONFIGS)
_ACH=[_achievable(t) for t in _TABLES]

def H(p):
    if p<=0 or p>=1:return 0.0
    return -(p*math.log2(p)+(1-p)*math.log2(1-p))
def binom_sf(k,n,p):
    """P(X>=k) for X~Binom(n,p)."""
    return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k,n+1))
def cp_lower(s,n,alpha=0.01):
    """One-sided Clopper-Pearson lower bound for a success rate."""
    if s<=0:return 0.0
    lo,hi=0.0,1.0
    for _ in range(60):
        m=(lo+hi)/2
        if binom_sf(s,n,m)<alpha:lo=m
        else:hi=m
    return lo
def switches(x):return ','.join(f'S{i+1}={bit(x,i)}' for i in range(N))

class ResearchAgent:
    def __init__(self,sat_prior=0.10,confirm=0.98,replications=10,alpha=0.01,choose='info_gain',prior_claim=None):
        # prior_claim: a law this individual (or its lineage) confirmed earlier in the same world.
        # It is used at once, gets half of the law mass, and stays refutable like any other belief.
        self.prior_claim=prior_claim;prior_law=prior_claim['table'] if prior_claim else None
        self.prior_index=_TABLES.index(prior_law) if prior_law in _TABLES else None
        self.sat_prior=sat_prior;self.confirm=confirm;self.replications=replications;self.alpha=alpha;self.choose=choose
        self.ll=[0.0]*len(_TABLES);self.L1=[0.0]*INPUTS;self.L0=[0.0]*INPUTS;self.count=[0]*INPUTS
        self.tier=1;self.method='LAW';self.status='RESEARCHING';self.obs=[];self.events=[];self.claim=None
        self.rep=None;self._post=None
        if self.prior_index is not None:
            self.status='CONFIRMED';self.claim={**prior_claim,'inherited':True}
            self.events.append({'event':'USING_REMEMBERED_LAW','law':prior_claim['law'],'at_observation':0})
    # ---------------- beliefs ----------------
    def absorb(self,o,prediction=None):
        """Statistics only (used by observe and when an agent is restored from its record)."""
        x,y=o['x'],o['y'];e=EPS_WORK if o['kind']=='work' else EPS
        a,b=math.log(1-e),math.log(e)
        for k,t in enumerate(_TABLES):self.ll[k]+=a if bit(t,x)==y else b
        if y:self.L1[x]+=a;self.L0[x]+=b
        else:self.L0[x]+=a;self.L1[x]+=b
        self.count[x]+=1;self.obs.append({'kind':o['kind'],'n':o['n'],'x':x,'y':y,**({'prediction':prediction} if prediction is not None else {})});self._post=None
    def observe(self,o,prediction=None):
        self.absorb(o,prediction);self._after(o,prediction)
    def to_state(self):
        return {'obs':list(self.obs),'status':self.status,'method':self.method,'tier':self.tier,'claim':self.claim,'rep':self.rep,
                'events':self.events[-24:],'prior_claim':self.prior_claim}
    def to_compact(self):
        """Sufficient statistics instead of the observation list (bounded size for long lives)."""
        return {'L1':list(self.L1),'L0':list(self.L0),'count':list(self.count),'n_obs':len(self.obs),'status':self.status,'method':self.method,
                'tier':self.tier,'claim':self.claim,'rep':self.rep,'events':self.events[-12:],'prior_claim':self.prior_claim}
    @classmethod
    def from_compact(cls,st):
        a=cls(prior_claim=st.get('prior_claim'));a.L1=[float(v) for v in st['L1']];a.L0=[float(v) for v in st['L0']];a.count=[int(v) for v in st['count']]
        a.ll=[sum(a.L1[x] if bit(t,x) else a.L0[x] for x in range(INPUTS)) for t in _TABLES]
        a.obs=[{}]*int(st['n_obs']);a.status=st['status'];a.method=st['method'];a.tier=st['tier'];a.claim=st['claim'];a.rep=st['rep'];a.events=list(st['events']);a._post=None
        return a
    @classmethod
    def from_state(cls,st):
        a=cls(prior_claim=st.get('prior_claim'))
        for o in st['obs']:a.absorb(o,o.get('prediction'))
        a.status=st['status'];a.method=st['method'];a.tier=st['tier'];a.claim=st['claim'];a.rep=st['rep'];a.events=list(st['events']);a._post=None
        return a
    def _prior(self,k):
        # Occam prior: each description-length tier gets the same mass, split inside the tier.
        return (1-self.sat_prior)/3/_TIER_SIZE[_TIERS[k]]
    def _sat_ll(self):
        tot=0.0
        for x in range(INPUTS):
            if self.count[x]:m=max(self.L1[x],self.L0[x]);tot+=m+math.log(.5*math.exp(self.L1[x]-m)+.5*math.exp(self.L0[x]-m))
        return tot
    def posterior(self):
        if self._post is not None:return self._post
        lp={k:self.ll[k]+_LOGPRIOR[k]+math.log(1-self.sat_prior)-math.log(.9) for k in range(len(_TABLES))}
        if self.prior_index is not None:
            for k in lp:lp[k]+=math.log(.5)
            lp[self.prior_index]=self.ll[self.prior_index]+math.log((1-self.sat_prior)*.5)
        sat=self._sat_ll()+math.log(self.sat_prior)
        m=max(max(lp.values()),sat);z=sum(math.exp(v-m) for v in lp.values())+math.exp(sat-m)
        kb=max(lp,key=lp.get)
        w={k:math.exp(v-m)/z for k,v in lp.items() if v-m>LOG_FLOOR or k==kb};psat=math.exp(sat-m)/z
        self._post=(w,psat);return self._post
    def p_sat_bit(self,x):
        d=self.L1[x]-self.L0[x]
        return 1/(1+math.exp(-d)) if abs(d)<700 else float(d>0)
    def p_on(self,x):
        """Probability that the TRUE lamp is on at x."""
        w,ps=self.posterior();return sum(p for k,p in w.items() if bit(_TABLES[k],x))+ps*self.p_sat_bit(x)
    def top(self,n=3):
        w,ps=self.posterior();rows=sorted(w.items(),key=lambda kv:-kv[1])[:n]
        return [{'law':_NAMES[k],'tier':_TIERS[k],'posterior':round(p,4),'table':_TABLES[k]} for k,p in rows]
    def map_law(self):
        w,_=self.posterior();k=max(w,key=w.get);return k,w[k]
    # ---------------- state transitions ----------------
    def _anomalies(self,k,margin=1.0):
        """Inputs whose observed majority contradicts law k (margin in log-likelihood units)."""
        out=[]
        for x in range(INPUTS):
            if self.count[x]:
                maj=int(self.L1[x]>self.L0[x])
                if maj!=bit(_TABLES[k],x) and abs(self.L1[x]-self.L0[x])>margin:out.append(x)
        return out
    def _after(self,o,prediction):
        # A noise-free outcome that contradicts a confirmed law refutes it.
        if self.status=='CONFIRMED' and o['kind']=='work' and bit(self.claim['table'],o['x'])!=o['y']:
            self.events.append({'event':'REFUTED','law':self.claim['law'],'counterexample':switches(o['x']),'observed':o['y'],'at_observation':len(self.obs)})
            self.status='RESEARCHING';self.claim=None;self.rep=None
        if self.rep is not None:
            r=self.rep
            if o['kind']=='trial' and r['phase']=='replicate':
                r['n']+=1;r['errors']+=int(prediction!=o['y'])
                if prediction!=o['y']:r['counterexamples'].append(switches(o['x']));r['misses'].append(o['x'])
            elif o['kind']=='probe' and r['queue'] and o['x']==r['queue'][0]:r['queue'].pop(0)
        self._revise()
    def _revise(self):
        w,ps=self.posterior()
        if self.method=='LAW' and ps>0.9:
            k,_p=self.map_law();self.events.append({'event':'METHOD_CHANGE','to':'TABLE','p_outside':round(ps,4),
                'counterexamples':[switches(x) for x in self._anomalies(k)][:6],'at_observation':len(self.obs)})
            self.method='TABLE';self.status='UNEXPLAINED';self.rep=None;self.claim=None
        elif self.method=='TABLE' and ps<0.2:
            self.events.append({'event':'LAW_LANGUAGE_RECOVERED','p_outside':round(ps,4),'at_observation':len(self.obs)})
            self.method='LAW';self.status='RESEARCHING'
        self.tier=_TIERS[self.map_law()[0]]
        if self.rep is not None:self._advance_confirmation()
    def _advance_confirmation(self):
        """Confirmation protocol for the leading law:
        coverage (every input seen once) -> re-test every anomaly ->
        replication on inputs chosen by the environment -> re-test every miss -> decide."""
        r=self.rep;k,p=self.map_law()
        if k!=r['law_index'] or p<self.confirm:
            self.events.append({'event':'CONFIRMATION_ABANDONED','law':_NAMES[r['law_index']],'reason':'leading law changed' if k!=r['law_index'] else 'belief fell below threshold',
                                'at_observation':len(self.obs)});self.rep=None;return
        if r['queue']:return
        if r['phase']=='coverage':
            an=self._anomalies(k,margin=0.0);r['phase']='anomaly';r['queue']=[x for x in an for _ in range(2)]
            if an:self.events.append({'event':'ANOMALY_RETEST','law':_NAMES[k],'inputs':[switches(x) for x in an][:6],'at_observation':len(self.obs)})
            if r['queue']:return
        if r['phase']=='anomaly':r['phase']='replicate';return
        if r['phase']=='replicate' and r['n']>=self.replications:
            if r['errors']:
                r['phase']='miss_retest';r['queue']=[x for x in r['misses'] for _ in range(3)]
                self.events.append({'event':'ANOMALY_RETEST','law':_NAMES[k],'inputs':[switches(x) for x in r['misses']][:6],'at_observation':len(self.obs)});return
            r['phase']='decide'
        if r['phase']=='miss_retest':r['phase']='decide'
        if r['phase']=='decide':
            ok=binom_sf(r['errors'],r['n'],EPS)>=self.alpha and not self._anomalies(k,margin=1.0)
            if ok:
                s_=r['n']-r['errors']
                self.claim={'law':_NAMES[k],'tier':_TIERS[k],'table':_TABLES[k],'posterior':round(p,4),
                    'replication':{'trials':r['n'],'errors':r['errors']},'inputs_checked':sum(1 for c in self.count if c),
                    'claimed_min_agreement_99':round(cp_lower(s_,r['n']),4)}
                self.status='CONFIRMED';self.events.append({'event':'CONFIRMED','law':_NAMES[k],'trials':r['n'],'errors':r['errors'],'at_observation':len(self.obs)})
            else:
                self.events.append({'event':'REPLICATION_FAILED','law':_NAMES[k],'errors':r['errors'],'trials':r['n'],
                    'counterexamples':r['counterexamples'][:4],'at_observation':len(self.obs)})
            self.rep=None
    def want_replication(self):
        if self.status!='RESEARCHING' or self.method!='LAW' or self.rep is not None:return False
        k,p=self.map_law();return p>=self.confirm
    def start_replication(self):
        k,_=self.map_law();self.rep={'law_index':k,'phase':'coverage','queue':[x for x in range(INPUTS) if not self.count[x]],'n':0,'errors':0,'counterexamples':[],'misses':[]}
        self.events.append({'event':'REPLICATION_STARTED','law':_NAMES[k],'at_observation':len(self.obs)})
    def predict_trial(self,x):
        """Prediction committed before the replication outcome is seen."""
        return bit(_TABLES[self.rep['law_index']],x) if self.rep else int(self.p_on(x)>=.5)
    # ---------------- choosing ----------------
    def info_gain(self,x):
        w,ps=self.posterior();pbar=0.0;cond=0.0
        for k,p in w.items():
            q=(1-EPS) if bit(_TABLES[k],x) else EPS;pbar+=p*q
        cond+=(1-ps)*H(EPS)
        qs=self.p_sat_bit(x)*(1-EPS)+(1-self.p_sat_bit(x))*EPS;pbar+=ps*qs;cond+=ps*H(qs)
        return H(pbar)-cond
    def next_experiment(self,rng=None):
        if self.choose=='random':
            return int(rng.random()*INPUTS) if rng else 0
        best=max(range(INPUTS),key=lambda x:(round(self.info_gain(x),9),-self.count[x],-x))
        return best
    def work_choice(self,locked):
        xs=free_inputs(locked);best=max(xs,key=lambda x:(round(self.p_on(x),9),-x));return best,self.p_on(best)
    def value_of_information(self):
        """Expected gain per work episode from knowing the law exactly (value of perfect information)."""
        w,ps=self.posterior();po=[self.p_on(x) for x in range(INPUTS)]
        now=sum(max(po[x] for x in xs) for xs in _CFG_X)/len(CONFIGS)
        known=sum(p*_ACH[k] for k,p in w.items())
        if ps>0:
            pb=[self.p_sat_bit(x) for x in range(INPUTS)]
            known+=ps*sum(1-math.prod(1-pb[x] for x in xs) for xs in _CFG_X)/len(CONFIGS)
        return max(0.0,known-now)
    # ---------------- deciding (knowledge gradient) ----------------
    def _sat_bits(self):return [self.p_sat_bit(x) for x in range(INPUTS)]
    @staticmethod
    def _pon_vec(w,ps,sb):
        v=[ps*sb[x] for x in range(INPUTS)]
        for k,p in w.items():
            t=_TABLES[k]
            while t:
                lsb=t&-t;v[lsb.bit_length()-1]+=p;t^=lsb
        return v
    @staticmethod
    def _best_ev(v,econ):
        R,c,pen=econ['reward'],econ['work'],econ.get('fail_penalty',0)
        val=[v[x]*R-c-pen*(1-v[x]) for x in range(INPUTS)]
        return sum(max(0.0,max(val[x] for x in xs)) for xs in _CFG_X)/len(CONFIGS)
    def _what_if(self,x0,y,e):
        w,ps=self.posterior();a,b=1-e,e;nw={};z=0.0
        for k,p in w.items():
            q=p*(a if bit(_TABLES[k],x0)==y else b);nw[k]=q;z+=q
        sb=self._sat_bits();s0=sb[x0];qs=s0*(a if y else b)+(1-s0)*(b if y else a);nps=ps*qs;z+=nps
        sb[x0]=s0*(a if y else b)/qs if qs>0 else s0
        return z,{k:v/z for k,v in nw.items()},nps/z,sb
    def knowledge_gradient(self,x0,e,econ):
        w,ps=self.posterior();now=self._best_ev(self._pon_vec(w,ps,self._sat_bits()),econ);after=0.0
        for y in (0,1):
            py,nw,nps,sb=self._what_if(x0,y,e)
            if py>1e-12:after+=py*self._best_ev(self._pon_vec(nw,nps,sb),econ)
        return max(0.0,after-now)
    def entropy_bits(self):
        # Uncertainty about which law, plus (inside the OUTSIDE model) about every unknown table cell.
        w,ps=self.posterior();h=-sum(p*math.log2(p) for p in list(w.values())+[ps] if p>0)
        return h+ps*sum(H(self.p_sat_bit(x)) for x in range(INPUTS))
    def known_ev(self,econ):
        w,ps=self.posterior();gain=econ['reward']-econ['work'];v=sum(p*_ACH[k] for k,p in w.items())*gain
        if ps>0:
            pb=self._sat_bits();v+=ps*gain*sum(1-math.prod(1-pb[x] for x in xs) for xs in _CFG_X)/len(CONFIGS)
        return v
    def decide(self,locked,energy,remaining,econ,science=True,experiments=True,rng=None):
        """One action for this tick: ('trial'|'probe'|'work'|'rest', input or None, scores).

        Research is bought only while its expected value exceeds its cost:
          value = (EV with the law known - EV now) x useful remaining ticks
          cost  = expected number of experiments x (experiment cost + work income forgone)
        and when working is already profitable and teaches as much as an
        experiment, the organism learns by working instead."""
        R,c,pen,cp=econ['reward'],econ['work'],econ.get('fail_penalty',0),econ['probe']
        sci=econ.get('science_at',0.5)
        if experiments and science and self.rep is None and self.want_replication() and energy>=max(econ['start']*0.75,econ['cap']*sci):
            self.start_replication();self._advance_confirmation()
        if experiments and self.rep is not None and energy>=econ['start']*0.5:
            if self.rep['queue']:return 'probe',self.rep['queue'][0],{'confirmation':self.rep['phase']}
            return 'trial',None,{'confirmation':self.rep['phase']}
        xw,pon=self.work_choice(locked);ev=pon*R-c-pen*(1-pon);can_work=energy>c+pen;sc={'work_ev':round(ev,3)}
        if experiments and science and self.status=='RESEARCHING' and energy>=econ['cap']*max(0.8,sci):
            # Fed: surplus energy would overflow anyway, so curiosity finishes the science.
            ig_best,x_best=max((round(self.info_gain(x),9),-self.count[x],-x) for x in range(INPUTS))[0::2];x_best=-x_best
            if ig_best>0.02:
                sc['curiosity']=True;return 'probe',(x_best if self.choose!='random' else int(rng.random()*INPUTS)),sc
        if not experiments and self.status!='CONFIRMED' and can_work and ev<=0:
            # Trial and error: the only experiment available is a risky work attempt.
            w,ps=self.posterior();now=self._best_ev(self._pon_vec(w,ps,self._sat_bits()),econ);vopi=max(0.0,self.known_ev(econ)-now)
            xs=free_inputs(locked);xe=max(xs,key=lambda x:(round(H(self.p_on(x)),9),-x));pe=self.p_on(xe);ige=H(pe);cost=max(0.0,-(pe*R-c-pen*(1-pe)))
            est=min(60,math.ceil(self.entropy_bits()/max(ige,0.05)));h_eff=max(0,min(remaining-est,60))*0.5
            if vopi*h_eff-est*cost>0 and energy>c+pen+cost:return 'work',xe,{**sc,'trial_and_error':True}
        if experiments and self.status!='CONFIRMED' and energy>cp+2:
            w,ps=self.posterior();now=self._best_ev(self._pon_vec(w,ps,self._sat_bits()),econ);vopi=max(0.0,self.known_ev(econ)-now)
            ig_best,x_best=max((round(self.info_gain(x),9),-self.count[x],-x) for x in range(INPUTS))[0::2];x_best=-x_best
            est=min(60,math.ceil(self.entropy_bits()/max(ig_best,0.05)));h_eff=max(0,min(remaining-est,60))*0.5
            net=vopi*h_eff-est*(cp+max(0.0,now));ig_work=H(pon) if (can_work and ev>0) else 0.0
            sc.update({'research_value':round(vopi*h_eff,3),'research_cost':round(est*(cp+max(0.0,now)),3),'probe_bits':round(ig_best,4),'work_bits':round(ig_work,4)})
            if net>0 and not (ig_work>=ig_best):
                return 'probe',(x_best if self.choose!='random' else int(rng.random()*INPUTS)),sc
        if can_work and ev>0:return 'work',xw,sc
        return 'rest',None,sc
    # ---------------- reporting ----------------
    def report(self):
        w,ps=self.posterior();alive=sum(1 for p in w.values() if p>1e-3)
        unknowns=[]
        if self.status!='CONFIRMED':unknowns.append(f'どの法則か（有力候補 {alive} 個、手持ちの言葉の外にある確率 {ps:.2f}）')
        unknowns.append(f'センサーの誤り率（上限 {EPS:.0%} と仮定）')
        if self.method=='TABLE':unknowns.append('手持ちの法則の型では説明できない。入力ごとの表で覚えている')
        nx=self.next_experiment() if self.status=='RESEARCHING' or self.method=='TABLE' else None
        if self.status=='CONFIRMED':step='法則を使って働く。働いた結果が法則と食い違えば撤回する'
        elif self.rep is not None:step={'coverage':'確認：まだ試していない入力を全部一度ずつ試す','anomaly':'確認：法則と食い違った入力をもう一度試す',
            'replicate':f"確認：環境が選ぶ入力で再現試験（{self.rep['n']}/{self.replications} 回、外れ {self.rep['errors']}）",'miss_retest':'確認：再現試験で外れた入力をもう一度試す'}.get(self.rep['phase'],'確認中')
        elif self.want_replication():step='余力ができたら確認の手順（全入力→食い違いの再試験→再現試験）に進む'
        elif self.method=='TABLE':step='表で働きながら、確かでない入力を調べる'
        else:step='情報量が最大の実験をする'
        return {'status':self.status,'method':self.method,'tier':self.tier,'observations':len(self.obs),'unknowns':unknowns,
                'hypotheses':[{k:v for k,v in h.items() if k!='table'} for h in self.top()],'p_outside_language':round(ps,4),
                'next_experiment':None if nx is None else {'switches':switches(nx),'expected_bits':round(self.info_gain(nx),4)},
                'events':self.events[-6:],'claim':None if self.claim is None else {k:v for k,v in self.claim.items() if k!='table'},'next_step':step}

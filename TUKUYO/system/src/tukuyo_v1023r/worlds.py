"""Hidden-rule worlds for the V1023r research preview (claude-patch5).

A world owns its secret.  The research agent never receives the world object:
it is handed three callables (probe / trial / work) that return observations
only.  Every random draw is counter based (sha256 of key|tag|counter), so the
environment side can later recompute exactly what the world answered and an
auditor can detect a forged observation.

DeviceWorld: five switches S1..S5 and one lamp.  The lamp follows a hidden
boolean law.  Laws come in tiers of growing description length; tier 4 is
"outside every family the agent knows" (a random table that is far from all
tier 1-3 laws), so the agent must notice that its hypothesis language fails.
claude-patch6 adds tier 5: a law from the agent's public invention grammar
(invent.py) that is at least 4 inputs away from every tier 1-3 law, so the
agent can only explain it by inventing it.
The lamp sensor used by experiments is noisy (flip rate <= SENSOR_BOUND);
the reward from working is the true lamp.
"""
from __future__ import annotations
import hashlib,itertools
from functools import lru_cache

N=5;INPUTS=1<<N;FULL=(1<<INPUTS)-1
SENSOR_BOUND=0.10          # published to the agent as part of the sensor spec
LOCKS=2                    # switches fixed by the environment in each work episode

def bit(x,i):return (x>>i)&1
def _u(key,tag,n):
    h=hashlib.sha256(f'{key}|{tag}|{n}'.encode()).digest();return int.from_bytes(h[:8],'big')/2**64
def _table(fn):
    t=0
    for x in range(INPUTS):
        if fn([bit(x,i) for i in range(N)]):t|=1<<x
    return t

def _lit(i,neg):return ('¬' if neg else '')+f'S{i+1}'
@lru_cache(maxsize=1)
def library():
    """[(tier,name,table)] unique by table, simplest description first."""
    rows=[(1,'常に消灯',lambda s:0),(1,'常に点灯',lambda s:1)]
    for i in range(N):
        for neg in (0,1):rows.append((1,_lit(i,neg),lambda s,i=i,neg=neg:s[i]^neg))
    for i,j in itertools.combinations(range(N),2):
        for ni,nj in itertools.product((0,1),repeat=2):
            rows.append((2,f'{_lit(i,ni)}∧{_lit(j,nj)}',lambda s,i=i,j=j,ni=ni,nj=nj:(s[i]^ni)&(s[j]^nj)))
            rows.append((2,f'{_lit(i,ni)}∨{_lit(j,nj)}',lambda s,i=i,j=j,ni=ni,nj=nj:(s[i]^ni)|(s[j]^nj)))
        rows.append((2,f'S{i+1}⊕S{j+1}',lambda s,i=i,j=j:s[i]^s[j]))
        rows.append((2,f'¬(S{i+1}⊕S{j+1})',lambda s,i=i,j=j:1-(s[i]^s[j])))
    for a,b,c in itertools.combinations(range(N),3):
        for na,nb,nc in itertools.product((0,1),repeat=3):
            L=f'{_lit(a,na)},{_lit(b,nb)},{_lit(c,nc)}'
            rows.append((3,f'全部({L})',lambda s,a=a,b=b,c=c,na=na,nb=nb,nc=nc:(s[a]^na)&(s[b]^nb)&(s[c]^nc)))
            rows.append((3,f'どれか({L})',lambda s,a=a,b=b,c=c,na=na,nb=nb,nc=nc:(s[a]^na)|(s[b]^nb)|(s[c]^nc)))
            rows.append((3,f'多数決({L})',lambda s,a=a,b=b,c=c,na=na,nb=nb,nc=nc:int((s[a]^na)+(s[b]^nb)+(s[c]^nc)>=2)))
        rows.append((3,f'S{a+1}⊕S{b+1}⊕S{c+1}',lambda s,a=a,b=b,c=c:s[a]^s[b]^s[c]))
        rows.append((3,f'¬(S{a+1}⊕S{b+1}⊕S{c+1})',lambda s,a=a,b=b,c=c:1-(s[a]^s[b]^s[c])))
    for a in range(N):
        rest=[i for i in range(N) if i!=a]
        for b,c in itertools.permutations(rest,2):
            rows.append((3,f'S{a+1}ならS{b+1}、でなければS{c+1}',lambda s,a=a,b=b,c=c:s[b] if s[a] else s[c]))
        for b,c in itertools.combinations(rest,2):
            rows.append((3,f'S{a+1}∧(S{b+1}∨S{c+1})',lambda s,a=a,b=b,c=c:s[a]&(s[b]|s[c])))
            rows.append((3,f'S{a+1}∨(S{b+1}∧S{c+1})',lambda s,a=a,b=b,c=c:s[a]|(s[b]&s[c])))
    seen=set();out=[]
    for tier,name,fn in rows:
        t=_table(fn)
        if t in seen:continue
        seen.add(t);out.append((tier,name,t))
    return tuple(out)

def hamming(a,b):return bin(a^b).count('1')

class DeviceWorld:
    kind='device'
    def __init__(self,key,seed,tier,noise,stream=''):
        if tier not in (1,2,3,4,5) or not 0<=noise<=SENSOR_BOUND:raise ValueError('V1023R_WORLD_SPEC')
        # The law depends on (key, seed); noise, trial inputs and locks also on the stream,
        # so a second visit to the same world sees the same law but fresh randomness.
        self._lawkey=f'{key}|{seed}';self._key=f'{key}|{seed}|{stream}' if stream else self._lawkey;self.tier=tier;self.noise=noise;self.n_probe=0;self.n_trial=0;self.n_work=0
        lib=library()
        if tier<=3:
            pool=[r for r in lib if r[0]==tier and r[1] not in ('常に消灯','常に点灯')]
            row=pool[int(_u(self._lawkey,'pick',0)*len(pool))];self._name=row[1];self._table=row[2]
        elif tier==4:
            tables=[r[2] for r in lib];n=0
            while True:
                # A random law over four of the five switches, far from every known law.
                vars_=sorted(range(N),key=lambda i:_u(self._lawkey,'var',n*10+i))[:4];sub=[int(_u(self._lawkey,'cell',n*100+k)<.5) for k in range(16)]
                t=_table(lambda s:sub[sum(s[v]<<j for j,v in enumerate(vars_))])
                if min(hamming(t,q) for q in tables)>=6:break
                n+=1
            self._name='未知の表('+','.join(f'S{v+1}' for v in vars_)+')';self._table=t
        else:
            # claude-patch6: a grammar law at least 4 inputs away from every tier 1-3 law. The four groups
            # (threshold, counting, branch, two terms) are equally likely, then a law inside the group.
            from .invent import groups,GROUPS
            tables=[r[2] for r in lib];gs=groups();n=0
            while True:
                pool=gs[GROUPS[int(_u(self._lawkey,'group5',n)*len(GROUPS))]];name,t=pool[int(_u(self._lawkey,'law5',n)*len(pool))]
                if min(hamming(t,q) for q in tables)>=4:break
                n+=1
            self._name=name;self._table=t
    # ---- what the agent may call --------------------------------------
    def probe(self,x):
        """One experiment: set the switches to x, read the (noisy) lamp sensor."""
        if type(x) is not int or not 0<=x<INPUTS:raise ValueError('V1023R_PROBE_INPUT')
        n=self.n_probe;self.n_probe+=1;y=bit(self._table,x)^int(_u(self._key,'noise',n)<self.noise)
        return {'n':n,'x':x,'y':y,'kind':'probe'}
    def trial(self):
        """Replication trial: the ENVIRONMENT chooses the input; the agent only sees it after predicting."""
        n=self.n_trial;self.n_trial+=1;x=int(_u(self._key,'trial-x',n)*INPUTS)
        y=bit(self._table,x)^int(_u(self._key,'trial-noise',n)<self.noise)
        return {'n':n,'x':x,'y':y,'kind':'trial'}
    def work_offer(self):
        """The environment fixes LOCKS switches; the agent may set the rest."""
        n=self.n_work;order=sorted(range(N),key=lambda i:_u(self._key,'lock',n*10+i))[:LOCKS]
        return {'n':n,'locked':{i:int(_u(self._key,'lockv',n*10+i)<.5) for i in order}}
    def work(self,offer,x):
        if offer['n']!=self.n_work:raise ValueError('V1023R_WORK_ORDER')
        if any(bit(x,i)!=v for i,v in offer['locked'].items()):raise ValueError('V1023R_LOCK_VIOLATION')
        self.n_work+=1;return {'n':offer['n'],'x':x,'y':bit(self._table,x),'kind':'work'}
    def skip_work(self,offer):
        if offer['n']!=self.n_work:raise ValueError('V1023R_WORK_ORDER')
        self.n_work+=1
    # ---- environment-side only (reveal after the episode, audits) -------
    def reveal(self):return {'tier':self.tier,'law':self._name,'table':self._table,'noise':self.noise}
    def true_agreement(self,table):
        """Expected agreement of a predictor with the NOISY sensor on uniform inputs."""
        d=hamming(table,self._table);return ((INPUTS-d)*(1-self.noise)+d*self.noise)/INPUTS
    def replay(self,obs):
        """Recompute what this world answered for a recorded observation."""
        k=obs['kind'];n=obs['n'];x=obs['x']
        if k=='probe':return bit(self._table,x)^int(_u(self._key,'noise',n)<self.noise)
        if k=='trial':
            if x!=int(_u(self._key,'trial-x',n)*INPUTS):return None
            return bit(self._table,x)^int(_u(self._key,'trial-noise',n)<self.noise)
        if k=='work':return bit(self._table,x)
        return None

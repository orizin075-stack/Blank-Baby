"""claude-patch6: law invention for the V1023r research agent.

patch5's agent knew 492 laws (tiers 1-3). When none of them explained the lamp it said so
("outside my language") and fell back to remembering a table, input by input. This module lets
it build NEW laws from parts it already has, then test them like any other hypothesis:

  threshold   「S1,S2,¬S4,S5のうち3つ以上」  4 or 5 literals, at least k of them on
  exactly     「ちょうど2つがオン」            exactly k of the five switches
  parity      「S1⊕S2⊕S3⊕S4」 and its negation, over 4 or 5 switches
  branch      「S1ならS2∧S3、でなければ¬S4」  a condition switch choosing between two laws
                                              of tier 1-2 over the other switches
  two terms   「(S1∧¬S2)∨(S3∧S4)」            two 2-literal conjunctions over 4 switches

Only laws that are not already in the base library are kept (deduplicated by truth table):
14,906 laws, 95% of them branches. The grammar is public and fixed. It was written by the patch
author, so the agent invents laws INSIDE this grammar; it does not invent new kinds of laws.
Nothing here touches a world or its key (tests check the import graph).

  prior       the whole grammar shares a small mass (0.05, against 0.9 for the base library and
              0.1 for "outside my language"), split like a two-part description: one of the five
              families (equal shares), then one law inside the family. Choosing a law after seeing
              the data is therefore paid for.
  propose()   the grammar laws that best explain the agent's per-input evidence (prior x
              likelihood); the agent adds them to its hypotheses.
  log_mass()  prior x likelihood of every grammar law that is NOT among the agent's hypotheses.
              The agent claims a law only if it still wins when all of them are counted, and a
              claim still needs the full confirmation protocol, including replication on inputs
              chosen by the environment.
"""
from __future__ import annotations
import collections,heapq,itertools,math
from functools import lru_cache
from .worlds import library,N,INPUTS,bit

FULL=(1<<INPUTS)-1
FAMILIES=('threshold','exactly','parity','branch','two_terms')
GROUPS=('threshold','counting','branch','two_terms')      # tier-5 worlds: counting = exactly + parity
def _lit(i,neg):return ('¬' if neg else '')+f'S{i+1}'
def _table(fn):
    t=0
    for x in range(INPUTS):
        if fn([bit(x,i) for i in range(N)]):t|=1<<x
    return t
@lru_cache(maxsize=1)
def _var():return tuple(_table(lambda s,i=i:s[i]) for i in range(N))
def _L(i,neg):return FULL^_var()[i] if neg else _var()[i]

@lru_cache(maxsize=1)
def grammar():
    """((name, table, complexity, family), ...) for every grammar law outside the base library, simplest first"""
    base={r[2] for r in library()};V=_var();rows=[]
    for size in (4,5):
        for vs in itertools.combinations(range(N),size):
            for neg in itertools.product((0,1),repeat=size):
                lits=','.join(_lit(v,n) for v,n in zip(vs,neg))
                for k in range(1,size+1):
                    rows.append((f'{lits}のうち{k}つ以上',_table(lambda s,vs=vs,neg=neg,k=k:sum(s[v]^n for v,n in zip(vs,neg))>=k),size,'threshold'))
    for k in range(0,N+1):
        rows.append((f'ちょうど{k}つがオン',_table(lambda s,k=k:sum(s)==k),3,'exactly'))
    for size in (4,5):
        for vs in itertools.combinations(range(N),size):
            name='⊕'.join(f'S{v+1}' for v in vs);t=0
            for v in vs:t^=V[v]
            rows.append((name,t,size,'parity'));rows.append((f'¬({name})',FULL^t,size+1,'parity'))
    def small(others):
        """tier 1-2 laws over the given switches: (name, table, size)"""
        out=[]
        for i in others:
            for n in (0,1):out.append((_lit(i,n),_L(i,n),1))
        for i,j in itertools.combinations(others,2):
            for ni,nj in itertools.product((0,1),repeat=2):
                a,b=_L(i,ni),_L(j,nj)
                out.append((f'{_lit(i,ni)}∧{_lit(j,nj)}',a&b,2));out.append((f'{_lit(i,ni)}∨{_lit(j,nj)}',a|b,2))
            out.append((f'S{i+1}⊕S{j+1}',V[i]^V[j],2))
        return out
    for c in range(N):
        others=[i for i in range(N) if i!=c];parts=small(others);on,off=V[c],FULL^V[c]
        for (an,at,az),(bn,bt,bz) in itertools.product(parts,repeat=2):
            if an==bn or az+bz<3:continue                   # both branches single literals are tier 3 already
            rows.append((f'S{c+1}なら{an}、でなければ{bn}',(on&at)|(off&bt),1+az+bz,'branch'))
    for vs in itertools.combinations(range(N),4):
        for (a,b),(cc,d) in (((vs[0],vs[1]),(vs[2],vs[3])),((vs[0],vs[2]),(vs[1],vs[3])),((vs[0],vs[3]),(vs[1],vs[2]))):
            for na,nb,nc,nd in itertools.product((0,1),repeat=4):
                rows.append((f'({_lit(a,na)}∧{_lit(b,nb)})∨({_lit(cc,nc)}∧{_lit(d,nd)})',(_L(a,na)&_L(b,nb))|(_L(cc,nc)&_L(d,nd)),4,'two_terms'))
    seen=set(base);out=[]
    for name,t,cx,f in sorted(rows,key=lambda r:r[2]):
        if t in seen or t==0 or t==FULL:continue
        seen.add(t);out.append((name,t,cx,f))
    return tuple(out)

@lru_cache(maxsize=1)
def groups():
    """{group: [(name, table)]} - tier-5 worlds draw a group first, then a law (environment side; the agent never calls this)"""
    out={g:[] for g in GROUPS}
    for name,t,_,f in grammar():out['counting' if f in ('exactly','parity') else f].append((name,t))
    return out

MASS=0.05
@lru_cache(maxsize=1)
def log_priors():
    """log prior of every grammar law (grammar order): MASS / 5 families / laws in the family"""
    n=collections.Counter(r[3] for r in grammar());return tuple(math.log(MASS/len(FAMILIES)/n[r[3]]) for r in grammar())
@lru_cache(maxsize=1)
def _index():return {r[1]:i for i,r in enumerate(grammar())}
def log_prior_of(table):
    i=_index().get(table);return None if i is None else log_priors()[i]

@lru_cache(maxsize=1)
def _bytes():
    g=grammar();return tuple(tuple((r[1]>>s)&255 for r in g) for s in range(0,INPUTS,8))
def scores(L1,L0):
    """log-likelihood of every grammar law (grammar order) under per-input evidence
    L1[x] / L0[x] = log P(observations at x | lamp on / off). Byte lookup tables: 4 additions per law."""
    d=[L1[x]-L0[x] for x in range(INPUTS)];S=[]
    for b in range(0,INPUTS,8):
        s=[0.0]*256
        for v in range(1,256):low=v&-v;s[v]=s[v^low]+d[b+low.bit_length()-1]
        S.append(s)
    base0=sum(L0);S0,S1,S2,S3=S;B0,B1,B2,B3=_bytes()
    return [base0+S0[a]+S1[b]+S2[c]+S3[e] for a,b,c,e in zip(B0,B1,B2,B3)]

def propose_from(sc,exclude=(),k=24,margin=math.log(1000)):
    """the best grammar laws (prior x likelihood) whose table is not in `exclude`: [(name, table, complexity,
    log prior + loglik)], at most k and within `margin` of the best one; ties go to the simpler law"""
    ex=set(exclude)
    best=heapq.nlargest(k,((s+lp,-cx,name,t,cx) for s,lp,(name,t,cx,_) in zip(sc,log_priors(),grammar()) if t not in ex))
    if not best:return []
    top=best[0][0]
    return [(name,t,cx,s) for s,_,name,t,cx in best if s>=top-margin]
def propose(L1,L0,exclude=(),k=24,margin=math.log(1000)):return propose_from(scores(L1,L0),exclude,k,margin)

def log_mass_from(sc,exclude=()):
    """log of the summed prior x likelihood of every grammar law whose table is not in `exclude`"""
    ex=set(exclude);v=[s+lp for s,lp,r in zip(sc,log_priors(),grammar()) if r[1] not in ex]
    if not v:return -math.inf
    m=max(v);return m+math.log(sum(math.exp(s-m) for s in v))
def log_mass(L1,L0,exclude=()):return log_mass_from(scores(L1,L0),exclude)

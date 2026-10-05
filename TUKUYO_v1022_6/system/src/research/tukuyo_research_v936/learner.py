"""Finite-depth decision-rule synthesis from examples; oracle never imported."""
from collections import Counter
from .features import values,BASE,ALL_FEATURES
ACTIONS=('audit','hold','probe','propose')

def _gini(count):
    n=sum(count.values());return n-sum(c*c for c in count.values())/n if n else 0.

def _best_split(rows,feature_names,min_leaf=35,max_candidates=80):
    n=len(rows);before=_gini(Counter(label for _,label in rows));best=None
    for name in feature_names:
        sorted_pairs=sorted((feat[name],label) for feat,label in rows)
        all_counts=Counter(label for _,label in sorted_pairs);left=Counter()
        # Only scan at class boundaries; subsample if needed to limit complexity.
        step=max(1,n//max_candidates)
        for i,(v,label) in enumerate(sorted_pairs[:-1]):
            left[label]+=1
            k=i+1
            if k<min_leaf or n-k<min_leaf or k%step or v==sorted_pairs[i+1][0]:continue
            right=all_counts-left
            reduction=before-_gini(left)-_gini(right)
            candidate=(reduction,name,(v+sorted_pairs[i+1][0])/2)
            if reduction>1e-10 and (best is None or candidate[0]>best[0]+1e-12):best=candidate
    return best

def train(data,feature_names=BASE,max_depth=6,min_leaf=35):
    rows=[(values(m,feature_names),label) for m,label in data]
    if not rows:raise ValueError('empty data')
    if any(label not in ACTIONS for _,label in rows):raise ValueError('invalid action')
    def build(part,depth):
        cnt=Counter(y for _,y in part)
        label=sorted(cnt, key=lambda y:(-cnt[y],y))[0]
        node={'action':label,'n':len(part),'counts':dict(sorted(cnt.items()))}
        if depth>=max_depth or len(part)<2*min_leaf or len(cnt)==1:return node
        best=_best_split(part,feature_names,min_leaf)
        if not best:return node
        gain,name,cut=best
        left=[row for row in part if row[0][name]<=cut];right=[row for row in part if row[0][name]>cut]
        if not left or not right:return node
        return {'feature':name,'threshold':round(cut,12), 'n':len(part),'gain':round(gain,9),'left':build(left,depth+1),'right':build(right,depth+1)}
    return build(rows,0)

def predict(tree,m):
    fs=values(m)
    while 'feature' in tree:
        tree=tree['left'] if fs[tree['feature']]<=tree['threshold'] else tree['right']
    return tree['action']

def model_complexity(tree):
    if 'feature' not in tree:return {'leaves':1,'nodes':0,'derived':[]}
    l=model_complexity(tree['left']);r=model_complexity(tree['right']);f=tree['feature']
    return {'leaves':l['leaves']+r['leaves'],'nodes':1+l['nodes']+r['nodes'], 'derived':sorted(set(l['derived']+r['derived']+([f] if ':' in f else [])))}

def score(tree,examples):
    truth_correct=wrong=0
    per=Counter()
    for m,label in examples:
        p=predict(tree,m)
        truth_correct+=p==label
        wrong+=p!=label
        per[label]+=1
    return {'n':len(examples),'correct':truth_correct,'wrong':wrong,'accuracy':round(truth_correct/len(examples),6) if examples else None, 'distribution':dict(sorted(per.items()))}

"""v947 cross-domain adapters and an autonomous bounded science-cycle demo."""
from __future__ import annotations
from tukuyo_v944.gap import search_evidence,classify
from tukuyo_v945.primitive import propose,eval_proposal

def adapt_numeric(rows):return [{'x':r['a'],'y':r['b'],'expected':r['expected']} for r in rows]
def adapt_state(rows):return [{'x':r['state'],'y':r['delta'],'expected':r['next']} for r in rows]
def adapt_graph(rows):return [{'x':r['degree'],'y':r['signal'],'expected':r['response']} for r in rows]
def transfer_preview(proposal,domains):
 out={}
 for name,rows in domains.items():
  wrong=sum(eval_proposal(proposal,r['x'],r['y'])!=r['expected'] for r in rows)
  out[name]={'rows':len(rows),'wrong':wrong,'candidate_sha256':proposal['candidate_sha256']}
 return out
def discover(train_rows):
 ev=search_evidence(train_rows);gap=classify(train_rows,ev)
 if gap['state']!='REPRESENTATION_INSUFFICIENT':return {'gap':gap,'proposal':None}
 return {'gap':gap,'proposal':propose(train_rows,ev)}

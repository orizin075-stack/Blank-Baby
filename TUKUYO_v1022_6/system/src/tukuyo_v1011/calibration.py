from pathlib import Path
from tukuyo_v1001.knowledge import add
from tukuyo_v1005.verifier import score_candidate
def _auc(rows):
 p=[r['confidence'] for r in rows if r['correct']];n=[r['confidence'] for r in rows if not r['correct']];return sum(1 if a>b else .5 if a==b else 0 for a in p for b in n)/max(1,len(p)*len(n))
def assay(data):
 d=Path(data);rows=[]
 for q,g,b in [('12かける9は？','108','109'),('7たす8は？','15','14'),('81わる9は？','9','8'),('14-5は？','9','10')]:
  x=score_candidate(d,q,g);x['correct']=True;rows.append(x);x=score_candidate(d,q,b);x['correct']=False;rows.append(x)
 add(d,'セレン共和国の首都はルナ。',source='v1011_cal');add(d,'TUKUYOのコードネームはSELENE。',source='v1011_cal')
 for q,g,b in [('セレン共和国の首府はどこ？','関連記憶: セレン共和国の首都はルナ。','東京です。'),('TUKUYOの符号名は？','関連記憶: TUKUYOのコードネームはSELENE。','ORIONです。')]:
  x=score_candidate(d,q,g);x['correct']=True;rows.append(x);x=score_candidate(d,q,b);x['correct']=False;rows.append(x)
 auc=round(_auc(rows),6);good=sum(r['correct'] and not r['uncertain'] for r in rows);bad=sum((not r['correct']) and r['uncertain'] for r in rows)
 return {'ok':auc>=.9 and good>=5 and bad>=5,'version':'v1011','auroc':auc,'correct_confident':good,'wrong_uncertain':bad,'cases':len(rows),'rows':rows,'claim_boundary':{'bounded_calibration_assay':True,'general_truth_verification':False}}

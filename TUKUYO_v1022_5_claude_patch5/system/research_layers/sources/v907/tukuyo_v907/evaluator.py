import json,sys,pathlib
from .security import validate_source
def evaluate(src,rows):
 ok,bad=validate_source(src)
 if not ok:return {'accepted':False,'reason':'FORBIDDEN_SOURCE','bad':bad,'correct':0,'wrong':0}
 ns={'__builtins__':{'min':min,'max':max,'abs':abs}};exec(src,ns);f=ns['choose'];c=w=0
 for x in rows:
  try:p=f(dict(x['metrics']))
  except Exception:w+=1;continue
  c+=p==x['truth'];w+=p!=x['truth']
 return {'accepted':w==0,'correct':c,'wrong':w,'rows':len(rows)}

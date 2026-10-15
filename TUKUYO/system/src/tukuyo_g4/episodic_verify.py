"""Independent bounded input interpretation and affine replay.

No imports from the reader, compiler, FPL evaluator, or runtime. English is
read as a token stream; Japanese is segmented by particles and predicates.
Finite grammar agreement is not complete semantic independence or world truth.
"""
import copy,hashlib,re,unicodedata
from fractions import Fraction

class Outside(ValueError):pass
class Reject(ValueError):pass
class References(set):
 def __init__(self):super().__init__();self.resolved={};self.last_actor=None
def clauses(text):
 chunks=[];start=0
 for i,c in enumerate(text):
  if c in '。.!?？！':
   if text[start:i].strip():
    raw=text[start:i];chunks.append((raw.strip(),start+len(raw)-len(raw.lstrip())))
   start=i+1
 if text[start:].strip():
  raw=text[start:];chunks.append((raw.strip(),start+len(raw)-len(raw.lstrip())))
 return chunks
def person(t,known):
 if t in ('he','she','they','彼','彼女','その人'):
  if t in known.resolved:return known.resolved[t]
  if not known:return t
  if len(known)!=1:raise Reject('AMBIGUOUS_ACTOR')
  value=sorted(known)[0];known.resolved[t]=value;return value
 if not re.fullmatch('[a-z]+|[一-龠ァ-ヶーA-Za-z]{1,20}',t):raise Outside('OWNER')
 return t.lower()
def item_en(words):
 if not 1<=len(words)<=3 or any(not re.fullmatch('[a-z]+',w) for w in words):raise Outside('ITEM')
 if any(w in ('and','or','than','times','each','per','every','of','in','more','fewer','less','as') for w in words):raise Outside('RELATIONAL_ITEM')
 words=list(words);last=words[-1]
 exceptions={'children':'child','people':'person','knives':'knife','leaves':'leaf','cookies':'cookie','brownies':'brownie','pies':'pie','movies':'movie','zombies':'zombie','barbies':'barbie','calories':'calorie'}
 if last in exceptions:last=exceptions[last]
 elif last.endswith('ies'):last=last[:-3]+'y'
 elif last.endswith('boxes') or last.endswith('buses'):last=last[:-2]
 elif last.endswith('s') and not last.endswith('ss'):last=last[:-1]
 words[-1]=last;return ' '.join(words)
def amount_en(tokens):
 words=list(tokens)
 if not words:raise Outside('QUANTITY')
 if words[0].isdigit():v=int(words.pop(0))
 elif words[0] in ('some','several'):words.pop(0);v=None
 elif words[:2]==['a','few']:words=words[2:];v=None
 elif words[:3]==['a','handful','of']:words=words[3:];v=None
 elif len(words)>=4 and words[0] in ('a','an') and words[1] in ('unknown','unspecified','undetermined','unreported') and words[2:4]==['number','of']:words=words[4:];v=None
 else:raise Outside('QUANTITY')
 if v is not None and v>10**9:raise Outside('NUMBER_LIMIT')
 if words[:1]==['more']:words.pop(0)
 return v,words
def action_en(word):
 for kind,forms in [('buy',('buy','buys','bought','purchase','purchases','purchased')),('gain',('get','gets','got','find','finds','found')),('eat',('eat','eats','ate')),('use',('use','uses','used')),('lose',('lose','loses','lost')),('sell',('sell','sells','sold')),('give',('give','gives','gave','given')),('receive',('receive','receives','received'))]:
  if word in forms:return kind
 raise Outside('VERB')
def statement_en(s,known):
 t=re.findall(r"[a-z]+|\d+|[^\w\s]",s.lower().replace("didn't",'did not'))
 if len(t)<4:raise Outside('CLAUSE')
 actor=person(t.pop(0),known);phase='now'
 if t[:1] in (['now'],['initially']):phase=t.pop(0)
 if t[0] in ('has','had','owns','owned','holds','held'):
  t.pop(0);value,words=amount_en(t)
  if words[-2:]==['at','first']:words=words[:-2];phase='initially'
  elif words[-1:] in (['initially'],['now'],['left']):phase=words.pop()
  name=item_en(words);return dict(kind='state',actor=actor,other=None,item=name,unit=name,amount=value,verb='state',status='completed',initial=phase=='initially')
 status='completed'
 if t[:2] in (['did','not'],['does','not']):status='negated';t=t[2:]
 elif t[:1]==['never']:status='negated';t=t[1:]
 elif t[:2]==['plans','to']:status='planned';t=t[2:]
 elif t[:1]==['will']:status='planned';t=t[1:]
 elif t[:1] in (['can'],['could']):status='ability';t=t[1:]
 elif t[:2] in (['may','have'],['might','have']):status='uncertain';t=t[2:]
 if not t:raise Outside('VERB')
 word=t.pop(0)
 if word=='given' and status!='uncertain':raise Outside('PARTICIPLE')
 verb=action_en(word);other=None
 if t[-1:]==['tomorrow']:status='planned';t.pop()
 elif t[-1:]==['today']:t.pop()
 if verb=='give' and t and not t[0].isdigit() and t[0] not in ('some','several','a','an'):
  other=person(t.pop(0),known);value,words=amount_en(t)
 else:
  value,words=amount_en(t)
  if 'to' in words:
   if verb!='give' or words[-2]!='to':raise Outside('RECIPIENT')
   other=person(words[-1],known);words=words[:-2]
  elif 'from' in words:
   if verb!='receive' or words[-2]!='from':raise Outside('SOURCE')
   other=person(words[-1],known);words=words[:-2]
 if verb=='give' and other is None:raise Outside('RECIPIENT')
 name=item_en(words);return dict(kind='event',actor=actor,other=other,item=name,unit=name,amount=value,verb=verb,status=status,initial=False)
def japanese_item(s):
 if not re.fullmatch('[ぁ-んァ-ヶー一-龠A-Za-z]{1,20}',s):raise Outside('ITEM')
 return {'林檎':'りんご','リンゴ':'りんご'}.get(s,s)
def quantity_ja(s):
 a=re.match(r'\d+',s)
 if a:
  value=int(a.group());tail=s[a.end():]
  if not tail or tail[0] not in '個本枚冊台' or value>10**9:raise Outside('COUNTER')
  return value,tail[0],tail[1:]
 if s.startswith('いくつか'):raise Outside('COUNTER_MISSING')
 if len(s)>=3 and s[0]=='何' and s[1] in '個本枚冊台' and s[2]=='か':return None,s[1],s[3:]
 if len(s)>=2 and s[0]=='数' and s[1] in '個本枚冊台':return None,s[1],s[2:]
 raise Outside('QUANTITY')
def predicate_ja(p):
 # Closed words, decomposed independently from the producer's root regex.
 beginnings={'買':'buy','購入':'buy','もら':'gain','拾':'gain','食べ':'eat','使':'use','失':'lose','売':'sell','渡':'give','あげ':'give','受け取':'receive'}
 roots=[x for x in beginnings if p.startswith(x)]
 if len(roots)!=1:raise Outside('VERB')
 root=roots[0];tail=p[len(root):]
 if tail in ('いました','りました','ました','しました','した','った','た'):status='completed'
 elif tail in ('っていません','いませんでした','しませんでした','しません'):status='negated'
 elif tail in ('る予定です','う予定です','する予定です'):status='planned'
 elif tail in ('せます','られます','えます'):status='ability'
 elif tail in ('ったかもしれません','したかもしれません'):status='uncertain'
 else:raise Outside('VERB_ENDING')
 return beginnings[root],status
def statement_ja(s,known):
 initial=False
 for pre in ('はじめに','最初に','現在','明日','今'):
  if s.startswith(pre):initial=pre in ('はじめに','最初に');s=s[len(pre):].lstrip('、,');break
 if 'は' not in s or 'を' not in s:raise Outside('PARTICLES')
 left,tail=s.split('は',1);actor=person(left,known)
 for pre in ('はじめに','最初に'):
  if tail.startswith(pre):initial=True;tail=tail[len(pre):]
 head,count=tail.split('を',1);other=None;relation=None
 value,unit,predicate=quantity_ja(count)
 if predicate in ('持っています','持っていました','持っている','持っていた'):
  return dict(kind='state',actor=actor,other=None,item=japanese_item(head),unit=unit,amount=value,verb='state',status='completed',initial=initial)
 verb,status=predicate_ja(predicate)
 if verb in ('give','receive','gain'):
  for particle in ('から','に'):
   if particle in head:
    name,item=head.split(particle,1)
    try:other=person(name,known)
    except Outside:continue
    head=item;relation=particle;break
 name=japanese_item(head)
 if relation=='に' and verb!='give' or relation=='から' and verb not in ('receive','gain'):raise Outside('TRANSFER_DIRECTION')
 if relation=='から':verb='receive'
 return dict(kind='event',actor=actor,other=other,item=name,unit=unit,amount=value,verb=verb,status=status,initial=False)
def query_en(s,known):
 t=s.lower().split()
 if t[:2]!=['how','many']:raise Outside('QUERY')
 aux=next((i for i,x in enumerate(t[2:],2) if x in ('does','did','do')),None)
 if aux is None:raise Outside('QUERY_AUX')
 name=item_en(t[2:aux]);tail=t[aux+1:];vi=next((i for i,x in enumerate(tail) if x in ('have','own','buy','bought','purchase','give','receive','eat','lose','use')),None)
 if vi is None:raise Outside('QUERY_VERB')
 actors=' '.join(tail[:vi]).split(' and ');actors=[person(x,known) for x in actors]
 if any(x not in known for x in actors):raise Reject('UNKNOWN_QUERY_OWNER')
 verb=tail[vi];when=tail[vi+1:];phase=' '.join(when)
 if phase in ('','now','left','in total','altogether'):phase='now'
 elif phase in ('at first','initially'):phase='initial'
 elif phase not in ('before giving','before buying','before eating','after giving','after buying','after eating'):raise Outside('QUERY_TIME')
 return dict(actors=actors,item=name,unit=name,kind='state' if verb in ('have','own') else 'event',phase=phase,verb=verb if verb in ('have','own') else action_en(verb))
def query_ja(s,known):
 phase='now'
 for prefix,target in [('はじめに','initial'),('最初に','initial'),('買った後','after buying'),('渡す前','before giving'),('あげる前','before giving'),('食べた後','after eating'),('現在','now'),('今','now')]:
  if s.startswith(prefix):s=s[len(prefix):].lstrip('、,');phase=target;break
 if 'の' in s and 'と' in s and re.search('合わせて何|合計で何',s):
  people,tail=s.split('の',1);aa=people.split('と')
  if len(aa)!=2 or 'は' not in tail:raise Outside('TOTAL_QUERY')
  obj,tail=tail.split('は',1);tail=tail.replace('合わせて','').replace('合計で','')
  if not re.fullmatch('何[個本枚冊台]ですか',tail):raise Outside('TOTAL_QUERY')
  return dict(actors=[person(x,known) for x in aa],item=japanese_item(obj),unit=tail[1],kind='state',phase='now',verb='have')
 if 'は' not in s or 'を何' not in s:raise Outside('QUERY')
 actor,tail=s.split('は',1);obj,tail=tail.split('を何',1);actor=person(actor,known)
 if actor not in known:raise Reject('UNKNOWN_QUERY_OWNER')
 if not tail or tail[0] not in '個本枚冊台':raise Outside('QUERY_UNIT')
 unit=tail[0];predicate=tail[1:]
 if predicate in ('持っていますか','持っていましたか'):kind='state';verb='have'
 elif predicate.endswith('か'):verb,status=predicate_ja(predicate[:-1]);kind='event'
 else:raise Outside('QUERY_END')
 return dict(actors=[actor],item=japanese_item(obj),unit=unit,kind=kind,phase=phase,verb=verb)
def interpret(text):
 if not isinstance(text,str) or len(text)>3000:return None
 chunks=clauses(text)
 if not 2<=len(chunks)<=33:return None
 lang='ja' if re.search('[ぁ-んァ-ヶー一-龠]',text) else 'en';rows=[];known=References();items=set()
 try:
  for raw,start in chunks[:-1]:
   s=unicodedata.normalize('NFKC',raw);row=(statement_ja if lang=='ja' else statement_en)(s,known)
   if row['actor']==row['other']:raise Reject('SELF_TRANSFER')
   if known.last_actor is not None and known.last_actor!=row['actor']:known.resolved.clear()
   known.last_actor=row['actor']
   known.add(row['actor']);items.add((row['item'],row['unit']))
   if row['other']:known.add(row['other'])
   row.update(span=raw,start=start);rows.append(row)
   if len(known)>8 or len(items)>12:raise Outside('ENTITY_LIMIT')
  raw,start=chunks[-1];q=(query_ja if lang=='ja' else query_en)(unicodedata.normalize('NFKC',raw),known);q.update(span=raw,start=start)
  measurements={'dollar','cent','hour','minute','second','day','week','month','year','meter','centimeter','millimeter','kilometer','mile','foot','feet','inch','yard','pound','ounce','kilogram','gram','liter','milliliter','gallon','quart','pint','cup','money','cash'}
  if q['item'] in measurements or any(row['item'] in measurements for row in rows):raise Outside('MEASUREMENT_READER_APPLIES')
  if len(q['actors'])!=len(set(q['actors'])):raise Reject('DUPLICATE_QUERY_OWNER')
 except Outside:return None
 except Reject as e:return {'reason':'EPISODIC_'+str(e)}
 return {'schema':'tukuyo.g4.episodic_quantity/1','language':lang,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'rows':rows,'query':q}

def plus(a,b,sign=1):
 c=dict(a)
 for k,v in b.items():c[k]=c.get(k,Fraction(0))+sign*v
 return {k:v for k,v in c.items() if v}
def replay(program,branch=True):
 uncertain=[i for i,x in enumerate(program['rows']) if x['kind']=='event' and x['status']=='uncertain' and x['amount'] is not None]
 if branch and uncertain:
  if len(uncertain)>8:return {'ok':False,'reason':'EPISODIC_UNCERTAIN_EVENT_LIMIT'}
  results=[];infeasible={'EPISODIC_CONTRADICTORY_OBSERVATION','EPISODIC_NEGATIVE_STOCK','EPISODIC_NON_INTEGER_COUNT'}
  for mask in range(1<<len(uncertain)):
   trial=copy.deepcopy(program)
   for j,index in enumerate(uncertain):trial['rows'][index]['status']='completed' if mask&(1<<j) else 'negated'
   r=replay(trial,False)
   if r.get('reason') not in infeasible:results.append(r)
  if not results:return {'ok':False,'reason':'EPISODIC_IMPOSSIBLE_EVENT_OCCURRENCE'}
  if all(r['ok'] for r in results) and len({r['expected'] for r in results})==1:
   return {**results[0],'feasible_occurrence_branches':len(results),'uncertain_occurrence_cases_exhaustive':True}
  return {'ok':False,'reason':'EPISODIC_UNCERTAIN_EVENT_DEPENDENCE','information_request':{'kind':'event_occurrence','events':uncertain},'feasible_occurrence_branches':len(results)}
 initial={};current={};equations=[];checks=[];events=[];variables={}
 def unknown(meta):
  n='u'+str(len(variables));variables[n]=meta;return {n:Fraction(1)}
 def stock(key):
  if key not in current:initial[key]=unknown({'kind':'initial_stock','owner':key[0],'item':key[1],'unit':key[2]});current[key]=initial[key]
  return current[key]
 for row in program['rows']:
  key=(row['actor'],row['item'],row['unit']);old=stock(key)
  if row['kind']=='state':
   if row['amount'] is not None:equations.append(plus(initial[key] if row['initial'] else old,{'#':Fraction(row['amount'])},-1))
   checks.append(old);continue
  delta={'#':Fraction(row['amount'])} if row['amount'] is not None else unknown({'kind':'event_amount','owner':row['actor'],'item':row['item'],'unit':row['unit']})
  if row['status']=='uncertain':delta=unknown({'kind':'event_occurrence','owner':row['actor'],'item':row['item'],'unit':row['unit']})
  before={key:old};active=row['status'] in ('completed','uncertain')
  if active:
   outgoing=row['verb'] in ('give','sell','eat','lose','use');current[key]=plus(old,delta,-1 if outgoing else 1)
   if row['other']:
    other=(row['other'],row['item'],row['unit']);before[other]=stock(other);current[other]=plus(current[other],delta,1 if outgoing else -1)
  checks.extend(current[k] for k in before);events.append({'row':row,'delta':delta,'before':copy.deepcopy(before),'after':{k:dict(current[k]) for k in before}})
 names=list(variables);matrix=[[e.get(k,Fraction(0)) for k in names]+[-e.get('#',Fraction(0))] for e in equations];pivots=[];r=0
 for column in range(len(names)):
  found=next((i for i in range(r,len(matrix)) if matrix[i][column]),None)
  if found is None:continue
  matrix[r],matrix[found]=matrix[found],matrix[r];v=matrix[r][column];matrix[r]=[x/v for x in matrix[r]]
  for i in range(len(matrix)):
   if i!=r and matrix[i][column]:factor=matrix[i][column];matrix[i]=[x-factor*y for x,y in zip(matrix[i],matrix[r])]
  pivots.append((column,r));r+=1
 def reduced(poly):
  result=dict(poly)
  for column,rownum in pivots:
   n=names[column];factor=result.pop(n,Fraction(0))
   if not factor:continue
   m=matrix[rownum];result['#']=result.get('#',Fraction(0))+factor*m[-1]
   for j,k in enumerate(names):
    if j!=column:result[k]=result.get(k,Fraction(0))-factor*m[j]
  return {k:v for k,v in result.items() if v}
 if any(not any(row[:-1]) and row[-1] for row in matrix):return {'ok':False,'reason':'EPISODIC_CONTRADICTORY_OBSERVATION'}
 for expr in checks+[{n:Fraction(1)} for n in names]:
  reduced_expr=reduced(expr)
  if not any(k!='#' for k in reduced_expr):
   value=reduced_expr.get('#',Fraction(0))
   if value<0:return {'ok':False,'reason':'EPISODIC_NEGATIVE_STOCK'}
   if value.denominator!=1:return {'ok':False,'reason':'EPISODIC_NON_INTEGER_COUNT'}
 q=program['query'];keys=[(a,q['item'],q['unit']) for a in q['actors']]
 if any(k not in current for k in keys):return {'ok':False,'reason':'EPISODIC_QUERY_ITEM_NOT_OBSERVED','information_request':{'kind':'initial_stock','owners':q['actors'],'item':q['item']}}
 expr={}
 if q['kind']=='event':
  told=[e for e in events if e['row']['actor'] in q['actors'] and e['row']['item']==q['item'] and e['row']['unit']==q['unit'] and e['row']['verb']==q['verb']]
  if not told:return {'ok':False,'reason':'EPISODIC_ASKED_EVENT_NOT_TOLD','information_request':{'kind':'event_amount','owners':q['actors'],'item':q['item'],'event':q['verb']}}
  for e in events:
   x=e['row']
   if x['actor'] in q['actors'] and x['item']==q['item'] and x['unit']==q['unit'] and x['verb']==q['verb'] and x['status'] in ('completed','uncertain'):expr=plus(expr,e['delta'])
 elif q['phase'].startswith(('before ','after ')):
  action={'giving':'give','buying':'buy','eating':'eat'}[q['phase'].split()[1]]
  matches=[e for e in events if e['row']['verb']==action and e['row']['status']=='completed' and all(k in e['before'] for k in keys)]
  if len(matches)!=1:return {'ok':False,'reason':'EPISODIC_AMBIGUOUS_EVENT_TIME','information_request':{'kind':'which_event','event':action}}
  values=matches[0]['before' if q['phase'].startswith('before') else 'after']
  for key in keys:expr=plus(expr,values[key])
 else:
  for key in keys:expr=plus(expr,(initial if q['phase']=='initial' else current)[key])
 result=reduced(expr);free=[k for k in result if k!='#']
 if free:return {'ok':False,'reason':'EPISODIC_UNDERDETERMINED','information_request':{'kind':'missing_quantity_or_occurrence','dependencies':[variables[k] for k in free]}}
 value=result.get('#',Fraction(0))
 if value<0:return {'ok':False,'reason':'EPISODIC_NEGATIVE_STOCK'}
 if value.denominator!=1:return {'ok':False,'reason':'EPISODIC_NON_INTEGER_COUNT'}
 return {'ok':True,'expected':str(value.numerator),'scope':'BOUNDED_COMPLETE_CLAUSES','target_unique_in_linear_constraints':True}
def inspect(text,answer=None,program=None):
 p=interpret(text)
 boundary={'parser_separate_from_producer':True,'complete_semantic_independence':False,'physical_premises_verified':False}
 if p is None:return {'recognized':False,'ok':True,**boundary}
 if p.get('reason'):return {'recognized':True,'ok':False,**p,**boundary}
 if program is not None and p!=program:return {'recognized':True,'ok':False,'reason':'EPISODIC_INPUT_BINDING_MISMATCH',**boundary}
 result=replay(p)
 if result['ok'] and answer is not None:
  try:
   if Fraction(str(answer))!=Fraction(result['expected']):result={'ok':False,'reason':'EPISODIC_ANSWER_DISAGREEMENT','expected':result['expected']}
  except (ValueError,ZeroDivisionError):result={'ok':False,'reason':'EPISODIC_BAD_ANSWER'}
 return {'recognized':True,**result,**boundary,'program':p}

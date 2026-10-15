"""Compile a bounded inventory program into exact linear FPL constraints."""
import copy,re

def compile(text,program):
 quantities={};facts=[];stocks={};initial={};events=[];observations=[];bound=set();meta={};aliases={};transitions=set()
 def expanded(expression):
  terms={};sign=1
  for token in re.findall(r'[a-z]+\d+|[+-]',expression):
   if token in ('+','-'):sign=1 if token=='+' else -1;continue
   for name,coefficient in aliases.get(token,{token:1}).items():terms[name]=terms.get(name,0)+sign*coefficient
  return {n:c for n,c in terms.items() if c}
 def rendered(expression,zero):
  terms=expanded(expression);parts=[]
  for name,count in terms.items():
   for _ in range(abs(count)):parts.append((' + ' if count>0 else ' - ')+name)
  return ''.join(parts).lstrip(' +') if parts else f'{zero} - {zero}'
 def new(prefix,item,unit,origin=None):
  name=prefix+str(len(quantities));q={'name':name,'unit':unit,'integer':True,'about':item}
  if origin:q['unknown_source']={'start':origin['start'],'text':origin['span']}
  quantities[name]=q;return name
 def stock(key,source):
  if key not in stocks:
   s=new('stock',key[1],key[2],source);stocks[key]=s;initial[key]=s;meta[s]={'kind':'initial_stock','owner':key[0],'item':key[1],'unit':key[2]}
  return stocks[key]
 for index,row in enumerate(program['rows']):
  key=(row['actor'],row['item'],row['unit']);current=stock(key,row);amount=new('amount',row['item'],row['unit'],row if row['amount'] is None else None)
  meta[amount]={'kind':'event_amount' if row['kind']=='event' else 'observation','owner':row['actor'],'item':row['item'],'unit':row['unit']}
  if row['amount'] is not None:facts.append({'eq':f'{amount} = {row["amount"]}','span':row['span']});bound.add(amount)
  if row['kind']=='state':
   if row['amount'] is not None:facts.append({'eq':f'{initial[key] if row["initial"] else current} = {amount}','span':row['span']})
   observations.append(current);continue
  before={key:current};delta=amount
  if row['status']=='uncertain':
   delta=new('uncertain',row['item'],row['unit'],row);meta[delta]={'kind':'event_occurrence','owner':row['actor'],'item':row['item'],'unit':row['unit']}
  active=row['status'] in ('completed','uncertain')
  if active:
   loss=row['verb'] in ('eat','use','lose','sell','give')
   result=new('stock',row['item'],row['unit']);expression=f'{current} {"-" if loss else "+"} {delta}';aliases[result]=expanded(expression);transitions.add(len(facts));facts.append({'eq':f'{result} = {expression}','span':row['span']});stocks[key]=result
   if row['other']:
    other=(row['other'],row['item'],row['unit']);old=stock(other,row);before[other]=old
    result=new('stock',row['item'],row['unit']);expression=f'{old} {"+" if loss else "-"} {delta}';aliases[result]=expanded(expression);transitions.add(len(facts));facts.append({'eq':f'{result} = {expression}','span':row['span']});stocks[other]=result
  observations.extend(stocks[k] for k in before)
  events.append({'row':row,'amount':delta,'before':before,'after':{k:stocks[k] for k in before}})
 query=program['query'];span=query['span'];keys=[(a,query['item'],query['unit']) for a in query['actors']]
 if any(k not in stocks for k in keys):return {'spec':None,'reason':'EPISODIC_QUERY_ITEM_NOT_OBSERVED','information_request':{'kind':'initial_stock','owners':query['actors'],'item':query['item']}}
 if query['kind']=='event':
  if not any(e['row']['actor'] in query['actors'] and e['row']['item']==query['item'] and e['row']['unit']==query['unit'] and e['row']['verb']==query['verb'] for e in events):return {'spec':None,'reason':'EPISODIC_ASKED_EVENT_NOT_TOLD','information_request':{'kind':'event_amount','owners':query['actors'],'item':query['item'],'event':query['verb']}}
  matching=[e for e in events if e['row']['actor'] in query['actors'] and e['row']['item']==query['item'] and e['row']['unit']==query['unit'] and e['row']['verb']==query['verb'] and e['row']['status'] in ('completed','uncertain')]
  selected=[e['amount'] for e in matching];expr=' + '.join(selected) if selected else None
 elif query['phase'].startswith(('before ','after ')):
  wanted={'giving':'give','buying':'buy','eating':'eat'}[query['phase'].split()[1]]
  matching=[e for e in events if e['row']['verb']==wanted and e['row']['status']=='completed' and all(k in e['before'] for k in keys)]
  if len(matching)!=1:return {'spec':None,'reason':'EPISODIC_AMBIGUOUS_EVENT_TIME','information_request':{'kind':'which_event','event':wanted}}
  field='before' if query['phase'].startswith('before') else 'after';expr=' + '.join(matching[0][field][k] for k in keys)
 else:expr=' + '.join((initial if query['phase']=='initial' else stocks)[k] for k in keys)
 ask=new('answer',query['item'],query['unit']);facts.append({'eq':f'{ask} = {expr}' if expr else f'{ask} = {ask} - {ask}','span':span})
 normalized=[]
 for i,f in enumerate(facts):
  if i in transitions:continue
  left,right=f['eq'].split(' = ')
  normalized.append(f if right.isdigit() else {**f,'eq':rendered(left,ask)+' = '+rendered(right,ask)})
 facts=normalized
 # Retain the target's constraint component and every grounded literal. An
 # unrelated unknown stock must not make a known incoming amount unknowable.
 connected={ask}
 while True:
  old=set(connected)
  for f in facts:
   names=set(re.findall(r'[a-z]+\d+',f['eq']))
   if (names-bound)&(connected-bound):connected|=names
  if old==connected:break
 kept=[f for f in facts if set(re.findall(r'[a-z]+\d+',f['eq']))<=connected or re.fullmatch(r'amount\d+ = \d+',f['eq'])]
 used=connected|{n for f in kept for n in re.findall(r'[a-z]+\d+',f['eq'])}
 spec={'schema':'tukuyo.g4.fpl/1','lang':program['language'],'text':text,'quantities':[quantities[n] for n in quantities if n in used],'facts':kept,'ask':ask,'answer_unit':query['unit'],'unused':[],'reader':'tukuyo.g4.episodic_reader/1:stock_flow','episodic_program':copy.deepcopy(program),'epistemic_dependencies':{n:meta[n] for n in connected if n in meta}}
 return {'spec':spec}

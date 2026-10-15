"""Finite bilingual inventory reader. No QA table, API, or state mutation.

Every clause is read completely. Owners, item names, explicit event status and
query time are retained in an auditable program. Other grammars remain outside.
The independent checker does not import this reader or its compiler.
"""
import hashlib,re,unicodedata
from . import episodic_fpl

SCHEMA='tukuyo.g4.episodic_quantity/1'
WHO=r'[A-Z][a-z]*|he|she|they|He|She|They'
EN_AMOUNT=r'\d+|some|several|a few|a handful of|an? (?:unknown|unspecified|undetermined|unreported) number of'
JA_AMOUNT=r'\d+|何(?:個|本|枚|冊|台)か|数(?:個|本|枚|冊|台)'
JP=r'[ぁ-んァ-ヶー一-龠A-Za-z]{1,20}'
JOWNER=r'(?:[一-龠ァ-ヶーA-Za-z]{1,20}|彼女|彼|その人)'
COUNTER=r'個|本|枚|冊|台'
PHYSICAL_UNITS=set('dollar cent hour minute second day week month year meter centimeter millimeter kilometer mile foot feet inch yard pound ounce kilogram gram liter milliliter gallon quart pint cup money cash'.split())
VERBS={
 'buy':'buy','buys':'buy','bought':'buy','purchase':'buy','purchases':'buy','purchased':'buy',
 'get':'gain','gets':'gain','got':'gain','find':'gain','finds':'gain','found':'gain',
 'eat':'eat','eats':'eat','ate':'eat','use':'use','uses':'use','used':'use',
 'lose':'lose','loses':'lose','lost':'lose','sell':'sell','sells':'sell','sold':'sell',
 'give':'give','gives':'give','gave':'give','given':'give','receive':'receive','receives':'receive','received':'receive'}
JVERBS={'買':'buy','購入':'buy','もら':'gain','拾':'gain','食べ':'eat','使':'use','失':'lose','売':'sell','渡':'give','あげ':'give','受け取':'receive'}

class Outside(ValueError):pass
class Ambiguous(ValueError):pass
class Discourse(set):
 def __init__(self):super().__init__();self.pronouns={};self.subject=None
def noun(n):
 n=n.strip().lower();words=n.split()
 if not 1<=len(words)<=3 or any(not re.fullmatch('[a-z]+',w) for w in words):raise Outside('ITEM_GRAMMAR')
 if set(words)&set('and or than times each per every of in more fewer less as'.split()):raise Outside('RELATIONAL_ITEM')
 last=words[-1];last={'children':'child','people':'person','knives':'knife','leaves':'leaf','cookies':'cookie','brownies':'brownie','pies':'pie','movies':'movie','zombies':'zombie','barbies':'barbie','calories':'calorie'}.get(last,last[:-3]+'y' if last.endswith('ies') else last[:-2] if last.endswith(('boxes','buses')) else last[:-1] if last.endswith('s') and not last.endswith('ss') else last)
 words[-1]=last;return ' '.join(words)
def jnoun(n):return {'リンゴ':'りんご','林檎':'りんご'}.get(n,n)
def owner(n,known):
 n=n.lower()
 if n in ('he','she','they','彼','彼女','その人'):
  if n in known.pronouns:return known.pronouns[n]
  if not known:return n
  if len(known)!=1:raise Ambiguous('AMBIGUOUS_ACTOR')
  value=next(iter(known));known.pronouns[n]=value;return value
 return n
def pieces(text):
 return [(m.group().strip(),m.start()+len(m.group())-len(m.group().lstrip())) for m in re.finditer(r'[^。.!?？！]+',text) if m.group().strip()]
def en_statement(s,known):
 # The state is an observation at this point, never a reset of an old state.
 m=re.fullmatch('('+WHO+r')\s+(?:(now|initially)\s+)?(has|had|owns|owned|holds|held)\s+('+EN_AMOUNT+r')\s+(.+?)(?:\s+(at first|initially|now|left))?',s)
 if m:
  return dict(kind='state',actor=owner(m[1],known),other=None,item=noun(m[5]),unit=noun(m[5]),amount=int(m[4]) if m[4].isdigit() else None,verb='state',status='completed',initial=m[2]=='initially' or m[6] in ('at first','initially'))
 m=re.fullmatch('('+WHO+r')\s+(?:(did not|didn\'t|does not|never|will|plans to|can|could|may have|might have)\s+)?([a-z]+)\s+(.+?)(?:\s+(tomorrow|today))?',s)
 if not m or m[3] not in VERBS:raise Outside('STATEMENT_GRAMMAR')
 if m[3]=='given' and m[2] not in ('may have','might have'):raise Outside('PARTICIPLE_AUXILIARY')
 actor=owner(m[1],known);verb=VERBS[m[3]];tail=m[4];other=None
 if verb=='give':
  a=re.fullmatch('('+WHO+r')\s+('+EN_AMOUNT+r')\s+(?:more\s+)?(.+)',tail)
  if a:other=owner(a[1],known);amount=a[2];item=a[3]
  else:
   a=re.fullmatch('('+EN_AMOUNT+r')\s+(?:more\s+)?(.+?)\s+to\s+('+WHO+')',tail)
   if not a:raise Outside('TRANSFER_RECIPIENT')
   amount,item,other=a[1],a[2],owner(a[3],known)
 else:
  a=re.fullmatch('('+EN_AMOUNT+r')\s+(?:more\s+)?(.+?)(?:\s+from\s+('+WHO+'))?',tail)
  if not a:raise Outside('EVENT_AMOUNT')
  amount,item=a[1],a[2]
  if a[3]:
   if verb!='receive':raise Outside('SOURCE_GRAMMAR')
   other=owner(a[3],known)
 status='negated' if m[2] in ('did not',"didn't",'does not','never') else 'planned' if m[2] in ('will','plans to') or m[5]=='tomorrow' else 'ability' if m[2] in ('can','could') else 'uncertain' if m[2] in ('may have','might have') else 'completed'
 return dict(kind='event',actor=actor,other=other,item=noun(item),unit=noun(item),amount=int(amount) if amount.isdigit() else None,verb=verb,status=status,initial=False)
def ja_statement(s,known):
 initial=bool(re.search('はじめに|最初に',s));s=re.sub(r'^(?:今|現在|はじめに|最初に|明日)[、,]?','',s)
 m=re.fullmatch('('+JOWNER+r')は(?:はじめに|最初に)?('+JP+')を('+JA_AMOUNT+')(?:('+COUNTER+r'))?(持っています|持っていました|持っている|持っていた)',s)
 if m:
  unit=m[4] or re.search(COUNTER,m[3]).group()
  return dict(kind='state',actor=owner(m[1],known),other=None,item=jnoun(m[2]),unit=unit,amount=int(m[3]) if m[3].isdigit() else None,verb='state',status='completed',initial=initial)
 m=re.fullmatch('('+JOWNER+r')は(?:('+JOWNER+')(に|から))?('+JP+')を('+JA_AMOUNT+')(?:('+COUNTER+'))?(.+)',s)
 if not m:raise Outside('JA_STATEMENT_GRAMMAR')
 verb=next((v for k,v in JVERBS.items() if m[7].startswith(k)),None)
 if verb is None:raise Outside('JA_EVENT_VERB')
 suffix=m[7]
 allowed=r'(?:買|購入|もら|拾|食べ|使|失|売|渡|あげ|受け取)(?:いました|りました|しました|した|った|ました|た|る予定です|う予定です|する予定です|っていません|いませんでした|しませんでした|しません|せます|られます|えます|ったかもしれません|したかもしれません)'
 if not re.fullmatch(allowed,suffix):raise Outside('JA_EVENT_FORM')
 if m[2] and (m[3]=='に' and verb!='give' or m[3]=='から' and verb not in ('receive','gain')):raise Outside('JA_TRANSFER_DIRECTION')
 status='uncertain' if 'かもしれません' in suffix else 'negated' if re.search('いません|しません',suffix) else 'planned' if '予定' in suffix else 'ability' if re.search('せます|られます|えます',suffix) else 'completed'
 unit=m[6] or re.search(COUNTER,m[5]).group()
 return dict(kind='event',actor=owner(m[1],known),other=owner(m[2],known) if m[2] else None,item=jnoun(m[4]),unit=unit,amount=int(m[5]) if m[5].isdigit() else None,verb='receive' if m[2] and m[3]=='から' else verb,status=status,initial=False)
def en_query(s,known,items):
 m=re.fullmatch(r'How many (.+?) (?:does|did|do) (.+?) (have|own|buy|bought|purchase|give|receive|eat|lose|use)(?: (now|left|at first|initially|in total|altogether|before (?:giving|buying|eating)|after (?:giving|buying|eating)))?',s)
 if not m:raise Outside('QUERY_GRAMMAR')
 item=noun(m[1]);actors=[owner(a,known) for a in m[2].split(' and ')]
 if any(a not in known for a in actors):raise Ambiguous('UNKNOWN_QUERY_OWNER')
 phase=m[4] or 'now';verb=VERBS.get(m[3],m[3])
 if phase in ('in total','altogether') and len(actors)<2:raise Outside('TOTAL_OWNER_SCOPE')
 return dict(actors=actors,item=item,unit=item,kind='state' if m[3] in ('have','own') else 'event',phase='initial' if phase in ('at first','initially') else 'now' if phase in ('left','in total','altogether') else phase,verb=verb)
def ja_query(s,known,items):
 m=re.fullmatch('('+JOWNER+')と('+JOWNER+')の('+JP+r')は(?:合わせて|合計で)何('+COUNTER+')ですか',s)
 if m:return dict(actors=[owner(m[1],known),owner(m[2],known)],item=jnoun(m[3]),unit=m[4],kind='state',phase='now',verb='have')
 phase='now'
 a=re.match(r'^(はじめに|最初に|買った後|渡す前|あげる前|食べた後|今|現在)[、,]?',s)
 if a:
  phase={'はじめに':'initial','最初に':'initial','買った後':'after buying','渡す前':'before giving','あげる前':'before giving','食べた後':'after eating'}.get(a[1],'now');s=s[a.end():]
 m=re.fullmatch('('+JOWNER+')は('+JP+')を何('+COUNTER+')(持っていますか|持っていましたか|買いましたか|購入しましたか|渡しましたか|食べましたか)',s)
 if not m:raise Outside('JA_QUERY_GRAMMAR')
 actor=owner(m[1],known)
 if actor not in known:raise Ambiguous('UNKNOWN_QUERY_OWNER')
 verb=next((v for k,v in JVERBS.items() if m[4].startswith(k)),None)
 return dict(actors=[actor],item=jnoun(m[2]),unit=m[3],kind='event' if verb else 'state',phase=phase,verb=verb or 'have')
def parse(text):
 if not isinstance(text,str) or len(text)>3000:return None
 # Fullwidth ASCII is read, but all evidence spans retain the original bytes.
 chunks=pieces(text)
 if not 2<=len(chunks)<=33:return None
 language='ja' if re.search('[ぁ-んァ-ヶー一-龠]',text) else 'en';rows=[];known=Discourse();items=set()
 try:
  for raw,start in chunks[:-1]:
   s=unicodedata.normalize('NFKC',raw).strip();row=(ja_statement if language=='ja' else en_statement)(s,known)
   if row['amount'] is not None and not 0<=row['amount']<=10**9:raise Outside('NUMBER_LIMIT')
   if row['actor']==row['other']:raise Ambiguous('SELF_TRANSFER')
   if known.subject is not None and known.subject!=row['actor']:known.pronouns.clear()
   known.subject=row['actor']
   known.add(row['actor']);items.add((row['item'],row['unit']))
   if row['other']:known.add(row['other'])
   row.update(span=raw,start=start);rows.append(row)
   if len(known)>8 or len(items)>12:raise Outside('ENTITY_LIMIT')
  raw,start=chunks[-1];query=(ja_query if language=='ja' else en_query)(unicodedata.normalize('NFKC',raw).strip(),known,items)
  query.update(span=raw,start=start)
  if query['item'] in PHYSICAL_UNITS or any(r['item'] in PHYSICAL_UNITS for r in rows):raise Outside('DELEGATE_TYPED_UNITS')
  if len(query['actors'])!=len(set(query['actors'])):raise Ambiguous('DUPLICATE_QUERY_OWNER')
 except Outside:return None
 except Ambiguous as e:return {'recognized':True,'reason':'EPISODIC_'+str(e),'information_request':{'kind':'clarify_reference'}}
 return {'schema':SCHEMA,'language':language,'text_sha256':hashlib.sha256(text.encode()).hexdigest(),'rows':rows,'query':query}
def read(text):
 program=parse(text)
 if program is None:return None
 if program.get('reason'):return {'spec':None,**program}
 return episodic_fpl.compile(text,program)

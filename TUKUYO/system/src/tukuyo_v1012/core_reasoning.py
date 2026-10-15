from __future__ import annotations
import re,unicodedata

def _n(s): return unicodedata.normalize('NFKC',str(s)).strip()
def _low(s):return _n(s).lower()
def _no(answer=None,kind='NO_DERIVATION',why=None):
 r={'ok':False,'answer':answer,'kind':kind,'confidence':0.0}
 if why:r['reason']=why
 return r

def _unit_kind(u):
 if not u:return None
 if u in ('個','本','枚','箱','袋','人','冊','台'):return 'COUNT'
 if u in ('円','ドル','usd','jpy'):return 'MONEY'
 if u in ('kg','キログラム','g','グラム'):return 'MASS'
 if u in ('l','L','リットル','ml','mL','ミリリットル'):return 'VOLUME'
 if u in ('m','メートル','cm','センチメートル','km','キロメートル'):return 'LENGTH'
 return u

def _quantities(s):
 pat=r'(-?\d+(?:\.\d+)?)\s*(円|ドル|個|本|枚|箱|袋|人|冊|台|kg|キログラム|g|グラム|ml|mL|ミリリットル|[lL]|リットル|cm|センチメートル|km|キロメートル|m|メートル)?'
 return [(float(a) if '.' in a else int(a),u or '') for a,u in re.findall(pat,s)]

CONTENT_UNIT_RE=r'(?:個|枚|本|冊|台|人)'
CONTAINER_RE=r'(?:箱|袋|パック|ケース|束)'

def _pack_structure(s):
 # Surface-independent bounded package parser. Returns (per_package, package_count, content_unit, container).
 m=re.search(r'(\d+)\s*('+CONTENT_UNIT_RE[3:-1]+r')\s*入り(?:の)?\s*('+CONTAINER_RE[3:-1]+r')?\s*(?:を|が|で|[×xX*])?\s*(\d+)\s*('+CONTAINER_RE[3:-1]+r'|つ)',s,re.I)
 if m:
  per=int(m.group(1));unit=m.group(2);first=m.group(3) or '';count=int(m.group(4));last=m.group(5)
  if first and last!='つ' and first!=last:return None
  return per,count,unit,(first or ('' if last=='つ' else last))
 # 1箱に6個...5箱 / 1袋10枚...4袋 / 1ケースに7本...4ケース
 m=re.search(r'1\s*(箱|袋|パック|ケース|束)\s*(?:に|あたり|には)?\s*(\d+)\s*(個|枚|本|冊|台|人)(?:\s*入り)?[、,\s]*(?:が|で|あり|ある)?\s*(\d+)\s*\1',s,re.I)
 if m:return int(m.group(2)),int(m.group(4)),m.group(3),m.group(1)
 # Allow intervening prose, but keep the same container on both sides.
 m=re.search(r'1\s*(箱|袋|パック|ケース|束)\s*(?:に|あたり|には)?\s*(\d+)\s*(個|枚|本|冊|台|人).*?(\d+)\s*\1',s,re.I)
 if m:return int(m.group(2)),int(m.group(4)),m.group(3),m.group(1)
 return None

def _pack_balance(s,pack):
 per,boxes,unit,container=pack
 if re.search(r'[-−]\s*\d+\s*(個|箱|袋|枚|本|冊|台|人|ケース|束|パック)',s):return _no(kind='NEGATIVE_EVENT_QUANTITY')
 asked=re.search(r'何(個|枚|本|冊|台|人|箱|袋|ケース|束|パック|円|ドル|kg|g|cm|m)',s)
 if asked and asked.group(1) not in (unit,container):return _no(kind='QUERY_UNIT_UNSUPPORTED')
 if re.search(r'予定|つもり|かもしれ|不明|かどうか|ないとは|なくは|と言った|と言われ',s):return _no(kind='EVENT_MODALITY_UNSUPPORTED')
 verb=r'(?:食べ|使っ|使い|使用|消費|捨て|渡し|あげ|返却|返し)'
 units=re.escape(unit)+'|'+re.escape(container or '__unknown__')
 block=rf'(\d+\s*(?:{units})(?:\s*(?:と|、|,)\s*\d+\s*(?:{units}))*)\s*(?:を)?\s*'+verb
 loose=whole=0;matched=False
 for m in re.finditer(block,s):
  matched=True
  tail=re.split(r'[。.!！?？、,]|\d+\s*(?:個|箱|袋|枚|本|冊|台|人)',s[m.end():],maxsplit=1)[0]
  if re.search(r'ません|なかった|ない|なかっ',tail):continue
  for n,u in re.findall(rf'(\d+)\s*({units})',m.group(1)):
   if u==container: whole+=int(n)
   else: loose+=int(n)
 if any(x in s for x in ('もら','増え','追加','買い足','使わ')): return _no(kind='PACK_BALANCE_UNSUPPORTED')
 remaining=per*boxes-whole*per-loose
 if remaining<0 or whole>boxes:return _no(kind='PACK_OVERCONSUMPTION')
 asks_container=bool(container and re.search('何'+re.escape(container)+'|'+re.escape(container)+r'(?:は|が|の)?いくつ',s))
 asks_remaining=bool(re.search(r'残り|残った|残数|left|remain',s,re.I))
 if asks_remaining:
  if not matched and re.search(verb,s):return _no(kind='PACK_CONSUMPTION_AMBIGUOUS')
  if asks_container and loose:return _no(kind='PARTIAL_CONTAINER_AMBIGUOUS')
  return {'ok':True,'answer':str(boxes-whole if asks_container else remaining),'kind':'PACK_EVENT_BALANCE','confidence':.96}
 if asks_container:return {'ok':True,'answer':str(boxes),'kind':'QUERY_ROLE_CONTAINER_COUNT','confidence':.96}
 return {'ok':True,'answer':str(per*boxes),'kind':'PACK_MULTIPLICATION','confidence':.96}

def _quantity_reason(s,low):
 qs=_quantities(s)
 if len(qs)<1:return None
 # Bounds such as "最大3個" do not establish an exact quantity.
 if any(k in s for k in ('最大','最小','最低','以下','以上','未満','以内','まで','少なくとも','高々','せいぜい','at least','at most')) and any(k in s for k in ('正確','ちょうど','exact','exactly')):
  return _no(kind='NON_EXACT_QUANTITY',why='bound_does_not_determine_exact_value')

 # Query-role guard: asking for package/container count must not be rewritten into content totals.
 pack=_pack_structure(s)
 if pack:return _pack_balance(s,pack)
 box_vals=[int(x) for x in re.findall(r'(\d+)\s*箱',s)]
 if box_vals and (re.search(r'箱(?:は|が|の)?(?:何箱|何個|いくつ)',s) or '何箱' in s):
  return {'ok':True,'answer':str(box_vals[-1]),'kind':'QUERY_ROLE_BOX_COUNT','confidence':.96}
 mprice=re.search(r'(\d+)\s*円(?:の商品)?(?:を|で)?\s*(\d+)\s*個',s)
 if mprice and (re.search(r'(?:商品|品物|個数).{0,8}(?:何個|いくつ)',s) or re.search(r'何個.{0,8}(?:商品|品物)',s)):
  return {'ok':True,'answer':str(int(mprice.group(2))),'kind':'QUERY_ROLE_ITEM_COUNT','confidence':.96}

 # Entity-targeted count: "りんご3個・みかん2個。りんごの総数は？" => 3, not 5.
 target=''
 mt=re.search(r'([一-龯ぁ-んァ-ンA-Za-z][一-龯ぁ-んァ-ンA-Za-z0-9_-]{0,24})の(?:総数|個数|数)(?:は|を)?',s)
 if mt:
  x=mt.group(1)
  if x not in ('個','本','枚','箱','袋','人','冊','台') and x not in ('残り','残数','全部','合計','総数','全体','個数','数') and not re.search(r'\d',x) and not x.endswith(('個','本','枚','箱','袋','人','冊','台')):target=x

 if not target:
  mt=re.search(r'([一-龯ぁ-んァ-ンA-Za-z][一-龯ぁ-んァ-ンA-Za-z0-9_-]{0,24}?)(?:は|が)(?:全部で|合計で)?(?:何個|いくつ)',s)
  if mt and mt.group(1) not in ('残り','全部','合計','数','箱','袋'):target=mt.group(1)
 if target:
  pairs=[]
  for mm in re.finditer(r'([一-龯ぁ-んァ-ンA-Za-z][一-龯ぁ-んァ-ンA-Za-z0-9_-]{0,24}?)(?:を|が|は)?\s*(\d+)\s*個',s):
   name=re.split(r'[、。・と]',mm.group(1))[-1];pairs.append((name,int(mm.group(2))))
  vals=[v for n,v in pairs if n==target or target.endswith(n) or n.endswith(target)]
  explicit_entity_query=bool(re.search(re.escape(target)+r'の(?:総数|個数|数)',s))
  distinct_names={n for n,_ in pairs}
  # Only force entity targeting when the question explicitly names the entity
  # or when multiple distinct counted entities make a global total ambiguous.
  # This prevents ordinary narratives such as "りんごを3個...2個もらった。全部で何個"
  # from being swallowed by the target parser before addition/subtraction runs.
  if explicit_entity_query or len(distinct_names)>1:
   if len(vals)==1:return {'ok':True,'answer':str(vals[0]),'kind':'ENTITY_TARGET_COUNT','confidence':.96}
   if pairs:return _no(kind='ENTITY_TARGET_AMBIGUOUS')

 # Explicit package multiplication, generalized across content/container units.
 if pack is not None:
  per_box,boxes,content_unit,container_name=pack
  total=per_box*boxes
  if any(k in low for k in ('残り','残った','残数','left','remain')):
   used=[]
   u=re.escape(content_unit)
   for pat in (rf'(\d+)\s*{u}\s*(?:食べ|使っ|使い|使用|消費|捨て|渡し|あげ)',rf'(?:食べ|使っ|使い|使用|消費|捨て|渡し|あげ).*?(\d+)\s*{u}'):
    used.extend(int(x) for x in re.findall(pat,s))
   if used:
    total-=sum(used)
   elif container_name:
    c=re.escape(container_name)
    used_cont=[]
    for pat in (rf'(\d+)\s*{c}\s*(?:使っ|使い|使用|消費|捨て|渡し|あげ)',rf'(?:使っ|使い|使用|消費|捨て|渡し|あげ).*?(\d+)\s*{c}'):
     used_cont.extend(int(x) for x in re.findall(pat,s))
    if used_cont: total-=sum(used_cont)*per_box
  return {'ok':True,'answer':str(total),'kind':'PACK_EVENT_BALANCE' if any(k in low for k in ('残り','残った','残数','left','remain')) else 'PACK_MULTIPLICATION','confidence':.96}

 if mprice and any(k in s for k in ('合計金額','総額','代金','金額','いくら')):
  return {'ok':True,'answer':str(int(mprice.group(1))*int(mprice.group(2))),'kind':'UNIT_PRICE_MULTIPLICATION','confidence':.94}

 # Do not silently convert units or combine dimensions.
 if len(qs)<2:return None
 kinds={_unit_kind(u) for _,u in qs if u}
 units={u for _,u in qs if u}
 if len(kinds)>1:return _no(kind='UNIT_MISMATCH',why='different_dimensions')
 if len(units)>1 and len(kinds)==1 and next(iter(kinds),None) in ('VOLUME','MASS','LENGTH'):
  return _no(kind='UNIT_CONVERSION_REQUIRED',why='conversion_not_implemented')
 add=any(k in low for k in ('もら','増え','追加','合わせ','全部','合計','総数','たす','足す','plus','added','total','sum','altogether'))
 sub=any(k in low for k in ('使','食べ','減','残','失','あげ','引く','ひく','minus','left','remain','used','gave'))
 if any(k in low for k in ('ずつ','倍','times each','per ')) and not re.search(r'個入り|1\s*箱',s):return _no(kind='UNSUPPORTED_QUANTIFIER')
 if add and sub:return _no(kind='MIXED_OPERATION_UNSUPPORTED')
 vals=[x for x,_ in qs]
 if add:
  if len(vals)>2 and not any(k in low for k in ('全部','合計','総数','sum','total','altogether')):return _no(kind='MULTI_NUMBER_AMBIGUOUS')
  v=sum(vals);return {'ok':True,'answer':str(int(v) if float(v).is_integer() else v),'kind':'QUANTITY_ADDITION','confidence':.94}
 if sub and len(vals)==2:
  v=vals[0]-vals[1];return {'ok':True,'answer':str(int(v) if float(v).is_integer() else v),'kind':'QUANTITY_SUBTRACTION','confidence':.94}
 return None

def _negated_near(text,phrase):
 # bounded polarity detector; reject rather than infer when polarity is unclear.
 i=text.find(phrase)
 if i<0:return None
 seg=text[max(0,i-8):min(len(text),i+len(phrase)+14)].lower()
 neg=('ない','なかった','ではない','じゃない','ません','not ','never ',' no ','did not','is not','isn\'t','was not')
 return any(n in seg for n in neg)

def _normalize_prop(x):
 x=_low(x);x=re.sub(r'^(もし|if\s+)','',x).strip(' ,。.?？')
 x=re.sub(r'(が|は)$','',x).strip()
 return x

def _implication_reason(s):
 # Japanese AならB / もしAならB. Only modus ponens; no contraposition,
 # affirming-consequent or denying-antecedent rules are implemented.
 clauses=[c.strip() for c in re.findall(r'[^。.!！?？]+[?？]?',s) if c.strip()]
 rules=[]
 for c in clauses:
  m=re.match(r'^(?:もし)?(.+?)(?:ならば|なら|であれば)(.+)$',c)
  if m:rules.append((_normalize_prop(m.group(1)),m.group(2).strip()))
  else:
   m=re.match(r'^if\s+(.+?),?\s*then\s+(.+)$',c,re.I)
   if m:rules.append((_normalize_prop(m.group(1)),m.group(2).strip()))
 if not rules:return None
 facts=[];negfacts=[]
 for c in clauses:
  if any(x in c for x in ('なら','ならば','であれば')) or re.match(r'^if\b',c,re.I):continue
  lc=_low(c)
  if c.endswith(('?','？')) or any(q in lc for q in ('どう','何','結論','言える','と言える','therefore','what follows','can we conclude')):continue
  neg=any(n in lc for n in ('ない','なかった','ではない','じゃない','ません',' not ','never ','did not','isn\'t','is not','was not'))
  prop=_normalize_prop(c)
  (negfacts if neg else facts).append(prop)
 for ant,cons in rules:
  # contradiction means no sound derivation.
  pos=any(ant==f or ant in f or f in ant for f in facts)
  neg=any(ant==f or ant in f or f in ant for f in negfacts)
  if pos and neg:return _no(kind='CONTRADICTORY_PREMISES')
  if pos and not neg:return {'ok':True,'answer':cons,'kind':'MODUS_PONENS','confidence':.92}
 return _no(kind='ANTECEDENT_NOT_ASSERTED')

def _comparison_reason(s):
 pairs=re.findall(r'([A-Za-z0-9一-龯ぁ-んァ-ン_]+)は([A-Za-z0-9一-龯ぁ-んァ-ン_]+)より(?:大きい|高い|速い|重い)',s)
 epairs=re.findall(r'\b([A-Za-z][\w-]*)\s+is\s+(?:bigger|larger|greater|taller|faster)\s+than\s+([A-Za-z][\w-]*)',s,re.I)
 pairs += epairs
 if len(pairs)<2:return None
 # reject direct cycles/contradictions
 edges=set(pairs)
 if any(a==b or (b,a) in edges for a,b in edges):return _no(kind='COMPARISON_CONTRADICTION')
 for a,b in pairs:
  for c,d in pairs:
   if b==c and a!=d:
    return {'ok':True,'answer':f'{a}は{d}より大きい関係にあります。','kind':'TRANSITIVE_COMPARISON','confidence':.9}
 return _no(kind='NO_TRANSITIVE_CHAIN')

def _category_reason(s):
 # Positive universal syllogism only. Interrogative clauses are never premises.
 if any(x in _low(s) for x in ('ではない','じゃない','ない','not ',' no ')):return None
 def declarative_clauses(text):
  out=[]
  for c in re.split(r'[。.!！]+',text):
   c=c.strip()
   if not c:continue
   lowc=_low(c)
   if any(q in c for q in ('?','？','何','誰','どれ','どの','いつ','どこ','なぜ','どう')):continue
   if any(q in lowc for q in ('ですか','ますか','でしょうか',' is ',' are ')) and c.endswith(('か','?','？')):continue
   out.append(c)
  return out
 clauses=declarative_clauses(s)
 declarative='。'.join(clauses)
 m1=re.search(r'すべての([^。]+?)は([^。]+?)(?:です|である|だ)',declarative)
 if m1:
  cat,sup=m1.group(1).strip(),m1.group(2).strip()
  for clause in clauses:
   m2=re.fullmatch(r'(.+?)は'+re.escape(cat)+r'(?:です|である|だ)',clause)
   if m2:
    obj=m2.group(1).strip()
    if obj and obj!=cat:return {'ok':True,'answer':f'{obj}は{sup}です。','kind':'CATEGORY_SYLLOGISM','confidence':.9}
 low=_low(' '.join(clauses));em1=re.search(r'all\s+([a-z]+)s?\s+are\s+([a-z]+)s?',low)
 if em1:
  cat,sup=em1.groups();em2=re.search(r'([a-z][\w-]*)\s+is\s+(?:an?\s+)?'+re.escape(cat)+r'\b',low)
  if em2 and em2.group(1)!=cat:return {'ok':True,'answer':f'{em2.group(1)} is a {sup}.','kind':'CATEGORY_SYLLOGISM','confidence':.9}
 return None

def reason(text):
 s=_n(text);low=s.lower()
 q=_quantity_reason(s,low)
 if q is not None:return q
 imp=_implication_reason(s)
 if imp is not None:return imp
 comp=_comparison_reason(s)
 if comp is not None:return comp
 cat=_category_reason(s)
 if cat is not None:return cat
 return _no()

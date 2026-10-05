from __future__ import annotations
import math,re,unicodedata

COUNT_UNITS=('個','本','枚','箱','袋','人','冊','台','ケース','束','パック')

def _n(s): return unicodedata.normalize('NFKC',str(s)).strip()
def _norm_answer(a): return re.sub(r'\s+','',_n(a)).rstrip('。.')
def _num(s):
    try:
        f=float(s)
        return int(f) if f.is_integer() else f
    except Exception:return None

def _same_answer(answer,expected):
    a=_norm_answer(answer);e=_norm_answer(expected)
    if a==e:return True
    an=_num(a);en=_num(e)
    return an is not None and en is not None and math.isclose(float(an),float(en),rel_tol=1e-12,abs_tol=1e-12)

def _result(*,recognized,decidable=False,expected=None,reason='UNRECOGNIZED',kind=None,answer=None):
    supported=bool(decidable and expected is not None and answer is not None and _same_answer(answer,expected))
    return {'recognized':bool(recognized),'decidable':bool(decidable),'expected':None if expected is None else str(expected),
            'supported':supported,'reason':reason,'kind':kind or reason}

def _dimension_units(s):
    pats={
      'MASS':r'(?<![A-Za-z])(kg|キログラム|g|グラム)(?![A-Za-z])',
      'LENGTH':r'(?<![A-Za-z])(km|キロメートル|cm|センチメートル|m|メートル)(?![A-Za-z])',
      'VOLUME':r'(?<![A-Za-z])(ml|mL|ミリリットル|l|L|リットル)(?![A-Za-z])',
      'MONEY':r'(円|ドル|USD|JPY)',
    }
    return {k for k,p in pats.items() if re.search(p,s)}

def _target_entity(s):
    # e.g. りんごの総数は？ / みかんは何個？
    m=re.search(r'([一-龯ぁ-んァ-ンA-Za-z][一-龯ぁ-んァ-ンA-Za-z0-9_-]{0,24})の(?:総数|個数|数)(?:は|を)?',s)
    if m:
        x=m.group(1)
        if x not in COUNT_UNITS and not re.search(r'\d',x) and not x.endswith(COUNT_UNITS):return x
    m=re.search(r'([一-龯ぁ-んァ-ンA-Za-z][一-龯ぁ-んァ-ンA-Za-z0-9_-]{0,24}?)(?:は|が)?(?:全部で|合計で|総計で|全部|合計)?(?:何個|いくつ)',s)
    if not m:return ''
    x=m.group(1)
    generic={'残り','残数','全部','合計','総数','全体','個数','数'}
    return '' if x in COUNT_UNITS or x in generic or re.search(r'\d',x) or x.endswith(COUNT_UNITS) else x

def _entity_counts(s):
    out=[]
    # Supports both りんご3個 and りんごを3個.
    for m in re.finditer(r'([一-龯ぁ-んァ-ンA-Za-z][一-龯ぁ-んァ-ンA-Za-z0-9_-]{0,24}?)(?:を|が|は)?\s*(\d+)\s*個',s):
        name=m.group(1)
        # Strip connective material accidentally captured before a noun.
        name=re.split(r'[、。・と]',name)[-1]
        out.append((name,int(m.group(2))))
    return out


def _logic_verify(s,answer):
    clauses=[c.strip() for c in re.findall(r'[^。.!！?？]+[?？]?',s) if c.strip()]
    decl=[c.rstrip('。.!！').strip() for c in clauses if not c.endswith(('?','？'))]
    qs=[c.rstrip('?？').strip() for c in clauses if c.endswith(('?','？'))]
    rules=[]
    for c in decl:
        m=re.fullmatch(r'すべての(.+?)は(.+?)(?:です|である|だ)',c)
        if m:rules.append((m.group(1).strip(),m.group(2).strip()))
    for cat,sup in rules:
        facts=[]
        for c in decl:
            m=re.fullmatch(r'(.+?)は'+re.escape(cat)+r'(?:です|である|だ)',c)
            if m and m.group(1).strip()!=cat:facts.append(m.group(1).strip())
        for q in qs:
            m=re.fullmatch(r'(.+?)は'+re.escape(sup)+r'(?:ですか|か|です|である|だ)?',q)
            if m:
                obj=m.group(1).strip()
                if obj in facts:return _result(recognized=True,decidable=True,expected=f'{obj}は{sup}です。',answer=answer,reason='CATEGORY_SYLLOGISM',kind='LOGIC_CATEGORY')
                return _result(recognized=True,decidable=False,reason='CATEGORY_PREMISE_MISSING',kind='LOGIC_GUARD')
    irules=[]
    for c in decl:
        m=re.fullmatch(r'(?:もし)?(.+?)(?:ならば|なら|であれば)(.+)',c)
        if m:irules.append((m.group(1).strip(),m.group(2).strip()))
    def norm(x):
        x=re.sub(r'^もし','',x).strip();x=re.sub(r'(です|だ|である)$','',x).strip()
        # Topic/subject particles are interchangeable for this bounded proposition form.
        x=re.sub(r'^([^、。 ]{1,24})[はが](.+)$',r'\1が\2',x)
        return x
    pos=[];neg=[]
    for c in decl:
        if any(k in c for k in ('なら','ならば','であれば')):continue
        isneg=any(k in c for k in ('ではない','じゃない','ない','ません'))
        z=norm(c);(neg if isneg else pos).append(z)
    for ant,cons in irules:
        na,nc=norm(ant),norm(cons);has_ant=any(na==f or na in f or f in na for f in pos);has_neg=any(na==f or na in f or f in na for f in neg)
        for q in qs:
            nq=norm(q);asks_cons=(nc==nq or nc in nq or nq in nc);asks_ant=(na==nq or na in nq or nq in na)
            if asks_cons:
                if has_ant and not has_neg:return _result(recognized=True,decidable=True,expected=cons,answer=answer,reason='MODUS_PONENS',kind='LOGIC_MP')
                return _result(recognized=True,decidable=False,reason='ANTECEDENT_NOT_ASSERTED',kind='LOGIC_GUARD')
            if asks_ant:return _result(recognized=True,decidable=False,reason='AFFIRMING_CONSEQUENT_GUARD',kind='LOGIC_GUARD')
    edges=[]
    for c in decl:
        m=re.fullmatch(r'(.+?)は(.+?)より(?:大きい|高い|速い|重い)',c)
        if m:edges.append((m.group(1).strip(),m.group(2).strip()))
    if edges:
        if any(a==b or (b,a) in edges for a,b in edges):return _result(recognized=True,decidable=False,reason='COMPARISON_CONTRADICTION',kind='LOGIC_GUARD')
        closure=set(edges);changed=True
        while changed:
            changed=False
            for a,b in list(closure):
                for c,d in list(closure):
                    if b==c and a!=d and (a,d) not in closure:closure.add((a,d));changed=True
        for q in qs:
            m=re.fullmatch(r'(.+?)は(.+?)より(?:大きい|高い|速い|重い)(?:ですか|か)?',q)
            if m:
                a,b=m.group(1).strip(),m.group(2).strip()
                if (a,b) in closure:return _result(recognized=True,decidable=True,expected=f'{a}は{b}より大きい関係にあります。',answer=answer,reason='TRANSITIVE_COMPARISON',kind='LOGIC_COMPARISON')
                return _result(recognized=True,decidable=False,reason='NO_TRANSITIVE_CHAIN',kind='LOGIC_GUARD')
    return None

def _independent_package_parse(s):
    # Deliberately separate parser from the answerer's implementation.
    contents='個|枚|本|冊|台|人'; containers='箱|袋|パック|ケース|束'
    # Form A: 8枚入りの袋を3袋 / 6個入りパックを5つ / 7本入りが4ケース.
    rx=rf'(\d+)\s*({contents})\s*入り(?:の)?\s*({containers})?\s*(?:を|が|で|[×xX*])?\s*(\d+)\s*({containers}|つ)'
    m=re.search(rx,s,re.I)
    if m:
        first=m.group(3) or ''; last=m.group(5)
        if first and last!='つ' and first!=last:return None
        return {'per':int(m.group(1)),'unit':m.group(2),'count':int(m.group(4)),'container':first or ('' if last=='つ' else last)}
    # Form B: 1箱に6個...5箱. Require same container at both ends.
    m=re.search(rf'1\s*({containers})\s*(?:に|あたり|には)?\s*(\d+)\s*({contents})(?:\s*入り)?.*?(\d+)\s*\1',s,re.I)
    if m:return {'per':int(m.group(2)),'unit':m.group(3),'count':int(m.group(4)),'container':m.group(1)}
    return None

def _asked_container_count(s,pack):
    c=(pack or {}).get('container','')
    if not c:return False
    return bool(re.search(re.escape(c)+r'(?:は|が|の)?(?:いくつ|何(?:箱|袋|パック|ケース|束|個|つ))',s) or re.search(r'何'+re.escape(c),s))

def _verify_package_balance(s,pack,answer):
 # Independent event accounting: scan backwards from each consumption verb,
 # collect only an adjacent quantity phrase, then convert its units.
 content=pack['unit'];container=pack['container'];per=pack['per'];count=pack['count']
 if re.search(r'[-−]\s*\d+\s*(個|本|枚|箱|袋|人|冊|台|ケース|束|パック)',s):
  return _result(recognized=True,reason='SIGNED_COUNT_UNSUPPORTED',kind='PACK_GUARD')
 role=re.findall(r'何(円|ドル|kg|g|cm|m|個|枚|本|冊|台|人|箱|袋|ケース|束|パック)',s)
 if any(u not in {content,container} for u in role):
  return _result(recognized=True,reason='REQUESTED_UNIT_UNSUPPORTED',kind='PACK_GUARD')
 if any(t in s for t in ('予定','つもり','かもしれ','不明','かどうか','ないとは','なくは','と言った','と言われ')):
  return _result(recognized=True,reason='EVENT_MODALITY_UNSUPPORTED',kind='PACK_GUARD')
 spent={content:0,container:0};events=0
 for event in re.finditer(r'食べ|使っ|使い|使用|消費|捨て|渡し|あげ|返却|返し',s):
  before=s[:event.start()];found=False
  suffix=s[event.end():]
  boundary=re.search(r'[。、.!！?？,]|\d+\s*(?:個|本|枚|箱|袋|人|冊|台)',suffix)
  suffix=suffix[:boundary.start()] if boundary else suffix
  negated=bool(re.search(r'(?:ません|ない|なかった|なかっ)',suffix))
  while True:
   m=re.search(r'(\d+)\s*('+re.escape(content)+'|'+re.escape(container or '__none__')+r')\s*(?:と|、|,|を)?\s*$',before)
   if not m:break
   if not negated:spent[m.group(2)]+=int(m.group(1))
   before=before[:m.start()];found=True
  if found:events+=1
 total=per*count-spent[content]-spent[container]*per
 remaining=bool(re.search(r'残り|残った|残数|left|remain',s,re.I))
 if any(x in s for x in ('もら','増え','追加','買い足','使わ')) or total<0 or spent[container]>count:
  return _result(recognized=True,reason='PACK_BALANCE_INVALID',kind='PACK_GUARD')
 boxes=_asked_container_count(s,pack)
 if remaining:
  if (not events and re.search(r'使|食べ|消費',s)) or (boxes and spent[content]):return _result(recognized=True,reason='PACK_BALANCE_AMBIGUOUS',kind='PACK_GUARD')
  expected=count-spent[container] if boxes else total
 else: expected=count if boxes else per*count
 return _result(recognized=True,decidable=True,expected=expected,answer=answer,reason='PACK_EVENT_BALANCE' if remaining else 'PACK_TOTAL',kind='EVENT_CONSUMPTION' if remaining else 'PACK_TOTAL')

def verify_bounded_semantics(query,answer):
    """Independent bounded semantic check.

    This intentionally does not import or call tukuyo_v1012.core_reasoning.
    It recognizes only quantity cases whose requested role and arithmetic can be
    reconstructed independently. Anything outside that surface is left
    unrecognized so another evidence source may decide it.
    """
    s=_n(query);low=s.lower()
    lv=_logic_verify(s,answer)
    if lv is not None:return lv

    # Exact answers cannot be derived from upper/lower bounds alone.
    if any(x in s for x in ('最大','最小','最低','以下','以上','未満','以内','まで','少なくとも','高々','せいぜい','at least','at most')) and any(x in s for x in ('正確','ちょうど','exact','exactly')):
        return _result(recognized=True,decidable=False,reason='NON_EXACT_QUANTITY',kind='EXACTNESS_GUARD')

    dims=_dimension_units(s)
    if len(dims)>1 and any(x in low for x in ('合計','足す','たす','plus','total','sum','残り','remain','left')):
        return _result(recognized=True,decidable=False,reason='UNIT_DIMENSION_MISMATCH',kind='UNIT_GUARD')

    # Quantity role takes precedence over content totals.
    pack=_independent_package_parse(s)
    if pack is not None:
        return _verify_package_balance(s,pack,answer)
    box_matches=[int(x) for x in re.findall(r'(\d+)\s*箱',s)]
    if re.search(r'箱(?:は|が|の)?(?:何箱|何個|いくつ)|何箱',s) and box_matches:
        return _result(recognized=True,decidable=True,expected=box_matches[-1],answer=answer,reason='QUERY_ROLE_BOX_COUNT',kind='QUERY_ROLE')

    mprice=re.search(r'(\d+)\s*円(?:の商品)?(?:を|で)?\s*(\d+)\s*個',s)
    if mprice and re.search(r'(?:商品|品物|個数).{0,8}(?:何個|いくつ)|何個.{0,8}(?:商品|品物)',s):
        return _result(recognized=True,decidable=True,expected=int(mprice.group(2)),answer=answer,reason='QUERY_ROLE_ITEM_COUNT',kind='QUERY_ROLE')

    # Specific counted entity takes precedence over generic total.
    target=_target_entity(s)
    if target:
        pairs=_entity_counts(s)
        vals=[v for n,v in pairs if n==target or target.endswith(n) or n.endswith(target)]
        if len(vals)==1:
            return _result(recognized=True,decidable=True,expected=vals[0],answer=answer,reason='ENTITY_TARGET_COUNT',kind='ENTITY_TARGET_COUNT')
        if pairs:
            return _result(recognized=True,decidable=False,reason='ENTITY_TARGET_AMBIGUOUS',kind='ENTITY_TARGET_COUNT')

    # Package structure reconstructed independently from the answerer.
    if pack is not None:
        base=pack['per']*pack['count']; unit=pack['unit']; consumed=[]
        u=re.escape(unit)
        for pat in (rf'(\d+)\s*{u}\s*(?:食べ|使っ|使い|使用|消費|捨て|渡し|あげ)',rf'(?:食べ|使っ|使い|使用|消費|捨て|渡し|あげ).*?(\d+)\s*{u}'):
            consumed.extend(int(x) for x in re.findall(pat,s))
        if re.search(r'残り|残った|残数|left|remain',low):
            expected=base-sum(consumed) if consumed else base
            return _result(recognized=True,decidable=True,expected=expected,answer=answer,reason='PACK_EVENT_BALANCE' if consumed else 'PACK_TOTAL',kind='EVENT_CONSUMPTION' if consumed else 'PACK_TOTAL')
        if any(x in low for x in ('総数','全部','合計','total','sum','altogether')):
            return _result(recognized=True,decidable=True,expected=base,answer=answer,reason='PACK_TOTAL',kind='PACK_TOTAL')

    # Price total only when monetary role is explicitly requested.
    if mprice and any(x in low for x in ('いくら','総額','代金','金額','合計金額','total price','cost')):
        return _result(recognized=True,decidable=True,expected=int(mprice.group(1))*int(mprice.group(2)),answer=answer,reason='UNIT_PRICE_TOTAL',kind='MONEY_ROLE')

    # Plain count arithmetic. This is deliberately narrower than the answerer.
    count_vals=[int(x) for x in re.findall(r'(-?\d+)\s*個',s)]
    if len(count_vals)>=2:
        if any(x in low for x in ('もら','増え','追加','足す','たす','合わせ','全部','合計','総数','plus','added','total','sum','altogether')):
            return _result(recognized=True,decidable=True,expected=sum(count_vals),answer=answer,reason='COUNT_ADDITION',kind='COUNT_ADDITION')
        if any(x in low for x in ('残り','減','使','食べ','引く','ひく','minus','left','remain','used')) and len(count_vals)==2:
            return _result(recognized=True,decidable=True,expected=count_vals[0]-count_vals[1],answer=answer,reason='COUNT_SUBTRACTION',kind='COUNT_SUBTRACTION')

    return _result(recognized=False,decidable=False,reason='UNRECOGNIZED')

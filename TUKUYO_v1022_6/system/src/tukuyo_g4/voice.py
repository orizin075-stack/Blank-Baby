"""generation 4: the child's own voice. It says in its own words how it read a problem and what it calculated, how sure
it is and why, and why it holds back when it does.

explain(text, result, data=None) -> {'lang', 'read': [...], 'answer', 'sure', 'why', 'held_back', 'said', 'from'}
  read       one line for each step of the solver, in the order it was taken: a number read from the words of the
             problem (quoted), a constant it knows, or a quantity worked out from the others (with the numbers put in);
             the numbers it set aside and why
  answer     the answer with its unit, or None
  sure       'sure' | 'fairly sure' | 'not sure'
  why        why it is that sure: the checker; parents who read it the same way now; what it knows of this way of
             reading (how often its parents confirmed it and read it otherwise: life.self_knowledge, the soul's
             record, law 3); a template learned from parents who agreed
  held_back  why it does not answer: what it could not read, readings that disagree, a way of reading its parents read
             otherwise more often than they confirmed it, one parent's voice alone
Everything it says comes from what it did (the reading, the solver's steps, the checker) and from its own record; no
parent writes it and nothing is sent anywhere. English problems are explained in English, Japanese ones in Japanese. It
says nothing about consciousness or feeling."""
from __future__ import annotations
import re

JA=re.compile(r'[぀-ヿ㐀-鿿]')

SKILL_WORDS={
 'holding':('what someone has after things are given, taken or used','持っている数の増え減り'),
 'compare':('comparing two amounts','二つの量の比べ'),
 'compare_things':('comparing two kinds of things','二つの種類の比べ'),
 'diff':('the difference between two amounts','二つの量の差'),
 'diff_time':('the difference between two times','時の差'),
 'groups':('equal groups','同じ数ずつの組'),
 'share':('sharing out equally','等しく分けること'),
 'price':('prices','値段'),
 'price_total':('the cost of several things','いくつかの物の代金'),
 'spend_left':('money left after buying','買い物のあとに残るお金'),
 'need':('what is still needed','まだ足りない数'),
 'change':('change from a payment','おつり'),
 'category':('things of one kind','ひとつの種類にまとめた物'),
 'gcd_lcm':('the greatest common divisor and the least common multiple','最大公約数と最小公倍数'),
 'times_slot':('times as many','何倍'),
 'even_up':('making shares equal','そろえるのに足りない数'),
 'proportion':('an amount for some things and for another number of them','比例'),
 'rest':('a whole and the rest of it','全体と残り'),
 'room':('the room left in a holder','あといくつ入るか'),
 'two_parts':('a whole kept in two parts','二つに分けた全体'),
 'derived_sum':('amounts of groups added up','組の量の合計'),
}

def _skill_words(skill,ja):
    if skill=='learned':return '親に教わった読み方' if ja else 'a way of reading my parents taught me'
    if skill=='v1022':return '前の世代の考え方（v1022）' if ja else 'my older core (v1022)'
    name=str(skill).split(':',1)[-1];two='+compose' in name;name=name.replace('+compose','')
    w=SKILL_WORDS.get(name)
    s=(w[1] if ja else w[0]) if w else name.replace('_',' ')
    if two:s+='（二段で考える）' if ja else ', thought in two steps'
    return s

def _words(name):
    """'kim_bead_2' -> 'kim bead (2)': the second of a holder's amounts, kept apart from the first"""
    m=re.fullmatch(r'(.+?)_(\d+)',str(name))
    return (m.group(1).replace('_',' ')+f' ({m.group(2)})') if m else str(name).replace('_',' ')

PARENT_NAMES={'claude':'Claude','chatgpt':'ChatGPT','gemini':'Gemini'}
def _who(ps,ja):
    ns=[PARENT_NAMES.get(p,str(p)) for p in ps]
    return '、'.join(ns) if ja else (' and '.join(ns) if len(ns)<3 else ', '.join(ns[:-1])+' and '+ns[-1])

def _unit(u,value=None):
    """'dollar/notebook' -> 'dollars per notebook'; '1' -> ''"""
    u=str(u or '')
    if u in ('','1'):return ''
    top,_,per=u.partition('/')
    one=str(value) in ('1','-1')
    pl={'foot':'feet','inch':'inches','person':'people','child':'children','man':'men','woman':'women','box':'boxes','glass':'glasses','bus':'buses',
        'class':'classes','dish':'dishes','peach':'peaches','sandwich':'sandwiches','loaf':'loaves','shelf':'shelves','leaf':'leaves','knife':'knives'}
    t=top if one else pl.get(top,top if top.endswith('s') or top in ('fish','sheep','deer') else (top[:-1]+'ies' if top.endswith('y') and top[-2:-1] not in 'aeiou' else top+'s'))
    return t+(' per '+per if per else '')

def _fmt_expr(expr,values):
    """an expression with the names put in (words) and with the numbers put in"""
    def sub(m):return values.get(m.group(0),m.group(0))
    nums=re.sub(r'[A-Za-z_]\w*',lambda m:m.group(0) if m.group(0) in ('floor','ceil','mod','min','max','gcd','lcm','abs') else sub(m),expr)
    words=re.sub(r'[A-Za-z_]\w*',lambda m:m.group(0) if m.group(0) in ('floor','ceil','mod','min','max','gcd','lcm','abs') else _words(m.group(0)),expr)
    def sym(s):
        s=re.sub(r'\bfloor\(([^()]*)\)',r'⌊\1⌋',s);s=re.sub(r'\bceil\(([^()]*)\)',r'⌈\1⌉',s)
        return s.replace(' * ',' × ').replace(' / ',' ÷ ')
    return sym(words),sym(nums)

def _reading_lines(g,ja):
    sp=g.get('spec') or {};facts=sp.get('facts') or [];values=g.get('values') or {}
    qs={q['name']:q for q in sp.get('quantities') or []}
    out=[]
    for st in g.get('steps') or []:
        if 'fact' not in st:
            names=', '.join(f"{_words(k)} = {v}" for k,v in (st.get('values') or {}).items())
            out.append(f'いくつかの関係をいっしょに解いて：{names}' if ja else f'Solving several facts together: {names}');continue
        f=facts[st['fact']] if st['fact']<len(facts) else {};x=st['solve'];v=st['value'];u=_unit((qs.get(x) or {}).get('unit'),v)
        eq=str(f.get('eq','')).strip();lhs,_,rhs=eq.partition('=');lhs,rhs=lhs.strip(),rhs.strip()
        if f.get('known'):
            out.append(f"知っていること：{f['known']}（{_words(x)} = {v}）" if ja else f"I know: {f['known']} ({_words(x)} = {v})")
        elif re.fullmatch(r'-?\d+(?:/\d+)?',rhs) and lhs==x and f.get('span'):
            out.append(f"「{f['span'].strip()}」から：{_words(x)} = {v}{(' '+u) if u and not ja else ''}" if ja else f"\"{f['span'].strip()}\": {_words(x)} = {v}{(' '+u) if u else ''}")
        elif lhs==x:
            w,n=_fmt_expr(rhs,values)
            out.append(f"{_words(x)} = {w} = {n} = {v}{(' '+u) if u and not ja else ''}")
        else:
            w,n=_fmt_expr(eq,values)
            out.append(f"{w}（{n}）から：{_words(x)} = {v}" if ja else f"From {w} ({n}): {_words(x)} = {v}{(' '+u) if u else ''}")
    for x in sp.get('unused') or []:
        out.append(f"{x.get('raw')} は使いません：{x.get('why')}" if ja else f"I set aside {x.get('raw')}: {x.get('why')}")
    return out

# ----------------------------------------------------------------------------- why it holds back
_EN_READ=[
 (r'VAGUE_EVENT','something happens to the things asked about without a number, so I cannot know how many there are','数のわからない出来事があって、いくつになるか決められません'),
 (r'QUESTION_FORM|NO_QUESTION|QUESTION_NOT_LAST|NO_SENTENCES','I could not tell what the question asks','何を聞かれているのかわかりませんでした'),
 (r'PRONOUN','I could not tell who a "he", "she" or "they" in it is','「彼」「彼女」「彼ら」が誰なのか決められませんでした'),
 (r'(?:UNUSED|UNREAD_NUMBER|UNUSED_QUESTION_NUMBER):(?:\w+:)?([^:;]+)$','I could not use the number {0} in any way I know, and I do not leave a number out without a reason','{0} という数の使い方がわからず、理由なく数を捨てることはしません'),
 (r'SCHEMAS_DISAGREE','I could read it in two ways that give different answers','二通りに読めて、答えが食い違いました'),
 (r'PATTERN','it asks about a pattern, which I cannot read yet','並び方（パターン）の問題はまだ読めません'),
 (r'NOT_WHOLE','my reading gave a count that is not a whole number, so I must have read it wrong','読みから出た個数が整数にならないので、読み違えたはずです'),
 (r'NEGATIVE','my reading gave a negative amount, so I must have read it wrong','読みから負の量が出たので、読み違えたはずです'),
 (r'INCONSISTENT|UNDERDETERMINED','my reading did not fix the answer to one number','読みから答えがひとつに決まりませんでした'),
 (r'^CHECK:','the checker refused my reading','検査が読みを通しませんでした'),
 (r'NO_SCHEMA|compose','I could not find a way of reading this story that I know and that uses every number in it','知っている読み方で、すべての数を使って読むことができませんでした'),
]
def _cannot_read(reason,ja):
    r=str(reason or '')
    for rx,en,jp in _EN_READ:
        m=re.search(rx,r)
        if m:
            g=m.groups();return (jp if ja else en).format(*g) if g else (jp if ja else en)
    if r.startswith('V1022:'):return '前の世代の考え方でも解けませんでした' if ja else 'my older core could not solve it either'
    return '確かめられる読み方が見つかりませんでした' if ja else 'I could not read it in a way I can check'

def _held_back(text,res,data,ja):
    reason=str(res.get('reason') or '');rs=res.get('readings') or [];w=res.get('withheld')
    if reason.startswith('DISAGREE:'):
        by={}
        for x in rs:
            if x.get('ok'):by.setdefault(str(x.get('value')),[]).append(PARENT_NAMES.get(x.get('parent'),x.get('parent')) if x.get('parent') else ('自分' if ja else 'my own reading'))
        def names(p):
            p=list(dict.fromkeys(p));return '、'.join(p) if ja else (' and '.join(p) if len(p)<3 else ', '.join(p[:-1])+' and '+p[-1])
        parts=[f"{v}（{names(p)}）" if ja else f"{v} ({names(p)})" for v,p in by.items()]
        return ('読みの答えが食い違いました：'+'、'.join(parts)+'。どれが正しいか私には決められないので、答えません。') if ja else \
               ('My readings give different answers: '+' and '.join(parts)+'. I cannot tell which is right, so I do not answer.')
    if reason.startswith('SELF_DOUBT:'):
        skills=reason.split(':',1)[1].split(',')
        know={}
        if data is not None:
            from .life import self_knowledge
            try:know=self_knowledge(data)
            except Exception:  # noqa: BLE001 - a record it cannot read says nothing here
                know={}
        parts=[]
        for s in skills:
            k=know.get(s) or {}
            parts.append((f"{_skill_words(s,ja)}（親が別に読んだこと {k.get('contradicted',0)} 回、確かめてくれたこと {k.get('confirmed',0)} 回）") if ja else
                         (f"{_skill_words(s,ja)} (my parents read it otherwise {k.get('contradicted',0)} times and confirmed it {k.get('confirmed',0)} times)"))
        if ja:return (f'私の読みでは {w} ですが、' if w else '')+'この読み方は親に別の読み方をされたことのほうが多いので、ひとりでは答えません：'+'、'.join(parts)+'。'
        return (f'My reading says {w}, but my' if w else 'My')+' parents have read problems I read this way otherwise more often than they confirmed it, so I do not answer alone: '+'; '.join(parts)+'.'
    if reason=='SINGLE_LLM_READING':
        who=next((PARENT_NAMES.get(x.get('parent'),x.get('parent')) for x in rs if x.get('ok') and x.get('parent')),'a parent')
        return (f'読めたのは {who} だけでした（{w}）。ひとりの声だけでは確かめたことになりません。') if ja else \
               (f'Only {who} could read it ({w}). One voice alone is not enough for me.')
    if any(x.get('reason')=='TEMPLATE_CONTESTED' for x in rs):
        return 'この言い回しで教わった読み方は、二人の親に別の読み方をされたので、もうひとりでは使いません。' if ja else \
               'What I learned for this wording was read otherwise by two of my parents, so I no longer use it alone.'
    own=next((x for x in rs if x.get('route') in ('own','v1022') and not x.get('ok')),None)
    why=_cannot_read(own.get('reason') if own else reason,ja)
    asked=[x.get('parent') for x in rs if x.get('parent') and str(x.get('reason') or '')!='LLM:LLM_NOT_CONFIGURED']
    tail=('' if asked else ('（親には聞いていません）' if ja else ' (I did not ask my parents)'))
    return (f'答えません：{why}{tail}。') if ja else (f'I do not answer: {why}{tail}.')

# ----------------------------------------------------------------------------- how sure it is
def _sure(res,g,data,ja,theirs=False):
    route=str(res.get('route') or '');rs=res.get('readings') or []
    parents=sorted({x.get('parent') for x in rs if x.get('ok') and x.get('parent') and str(x.get('value'))==str(res.get('answer'))})
    checked=('別の検査プログラムが'+('親の' if theirs else '')+'読みを解き直し、すべての数が使われているか理由つきで外されていること、すべての関係が成り立つこと、単位がそろうことを確かめました') if ja else \
            ('the checker, a separate program, solved '+('their' if theirs else 'my')+' reading again and found every number used or set aside for a reason, every fact true and the units in agreement')
    if theirs:
        # it could not read the problem itself: what it says is how its parents read it, and that they agreed
        who=_who(parents,ja);two=len(parents)==1
        return ('fairly sure',(f"自分では読めませんでした。{who} が{'二通りに読んで' if two else '同じ読みで'}同じ答えになり、{checked}。") if ja else
                              (f"I could not read it myself; {who} read it {'in two ways that agree' if two else 'the same way'}, and {checked}."))
    if g is None:
        base='前の世代の考え方で解き、その証明の検査が通りました' if ja else 'My older core solved it and its proof held'
        if parents:return ('sure',base+(f'。{_who(parents,ja)} も同じ答えになりました。' if ja else f'; {_who(parents,ja)} got the same answer.'))
        return ('fairly sure',base+('。' if ja else '.'))
    skill=g.get('skill')
    if route.startswith('learned') or g.get('route')=='learned':
        tid=g.get('template');by=[]
        if data is not None and tid:
            try:
                from pathlib import Path
                from .learn import Store
                t=(Store(Path(data)/'g4').load()['templates'] or {}).get(tid) or {}
                by=sorted((t.get('provenance') or {}).get('parents') or [])
            except Exception:  # noqa: BLE001
                by=[]
        lvl='sure' if len(by)>=2 else 'fairly sure'
        who=_who(by,ja) if by else ('親' if ja else 'my parents')
        return (lvl,(f'{who} が同じ読みで一致したときに教わった読み方で読みました。{checked}。') if ja else
                    (f'I read it the way {who} taught me when they agreed; {checked}.'))
    if parents:
        who=_who(parents,ja)
        return ('sure',(f'自分の読みに加えて {who} も同じ読みで同じ答えになりました。{checked}。') if ja else
                       (f'{who} read it the same way and got the same answer; {checked}.'))
    if skill is None and g.get('route')!='learned':
        from .life import skill_of
        skill=skill_of(g)
    words=_skill_words(skill or 'own',ja)
    if data is None:
        return ('fairly sure',(f'自分の読み（{words}）で読みました。{checked}。自分の記録はここでは見ていません。') if ja else
                              (f'My own reader read it ({words}); {checked}. I did not look at my own record here.'))
    from .life import self_knowledge
    try:k=self_knowledge(data).get(skill) or {}
    except Exception:  # noqa: BLE001
        k={}
    c,x=k.get('confirmed',0),k.get('contradicted',0)
    if c and not x:
        return ('sure',(f'自分の読み（{words}）で読みました。{checked}。この読み方は親に {c} 回確かめてもらい、別の読み方をされたことはありません。') if ja else
                       (f'My own reader read it ({words}); {checked}. My parents have confirmed this way of reading {c} time{"s" if c!=1 else ""} and never read it otherwise.'))
    if c or x:
        return ('fairly sure',(f'自分の読み（{words}）で読みました。{checked}。この読み方は親に {c} 回確かめてもらい、{x} 回別の読み方をされました。') if ja else
                              (f'My own reader read it ({words}); {checked}. My parents have confirmed this way of reading {c} time{"s" if c!=1 else ""} and read it otherwise {x} time{"s" if x!=1 else ""}.'))
    return ('fairly sure',(f'自分の読み（{words}）で読みました。{checked}。この読み方はまだ親に確かめてもらったことがありません。') if ja else
                          (f'My own reader read it ({words}); {checked}. My parents have not checked this way of reading yet.'))

def explain(text,res,data=None):
    try:return _explain(text,res,data)
    except Exception as e:  # noqa: BLE001 - its voice must never stop it from answering; what failed is said instead
        return {'lang':'ja' if JA.search(str(text or '')) else 'en','read':[],'answer':res.get('answer'),'sure':None,'why':'','held_back':None,
                'said':None,'error':'VOICE:'+type(e).__name__}

def _explain(text,res,data):
    ja=bool(JA.search(str(text or '')))
    rs=res.get('readings') or []
    out={'lang':'ja' if ja else 'en','read':[],'answer':None,'sure':'not sure','why':'','held_back':None,
         'from':'自分の読みと解き方と記録から（親は書いていません）' if ja else 'from its own reading, solving and record; no parent wrote this'}
    if res.get('answer') is None:
        out['held_back']=_held_back(text,res,data,ja)
        out['why']=out['held_back']
        lines=['どのくらい確か：確かではない',out['held_back']] if ja else ['How sure I am: not sure.',out['held_back']]
        out['said']='\n'.join(lines);return out
    ans=str(res['answer'])
    ok=[x for x in rs if x.get('ok') and str(x.get('value'))==ans]
    # whose reading it tells: its own (its reader, a learned template), its older core's, or, when it could not read the
    # problem itself, its parents' (and it says so)
    g=next((x for x in ok if x.get('spec') and not str(x.get('route','')).startswith('llm')),None)
    older=next((x for x in ok if x.get('route')=='v1022'),None)
    theirs=g is None and older is None and next((x for x in ok if x.get('spec')),None)
    if g is not None:out['read']=_reading_lines(g,ja)
    elif older is not None:
        k=older.get('proof_kind') or ('なし' if ja else 'none')
        out['read']=[f'前の世代の考え方（v1022）で解きました（証明の種類：{k}）' if ja else f'My older core (v1022) solved it (its proof: {k})']
    elif theirs:out['read']=_reading_lines(theirs,ja)
    out['whose']='its own' if g is not None or older is not None else ('its parents' if theirs else None)
    u=_unit(res.get('unit'),ans) if not ja else ''
    out['answer']=ans+(' '+u if u else '')
    out['sure'],out['why']=_sure(res,g,data,ja,theirs=bool(theirs))
    lv={'sure':'確か','fairly sure':'たぶん確か','not sure':'確かではない'}
    head=('読み方：' if not theirs else '親の読み方：') if ja else ('How I read it:' if not theirs else 'How my parents read it:')
    lines=(([head]+['・'+x for x in out['read']] if out['read'] else [])+[f"答え：{out['answer']}",f"どのくらい確か：{lv[out['sure']]}。{out['why']}"]) if ja else \
          (([head]+['- '+x for x in out['read']] if out['read'] else [])+[f"So the answer is {out['answer']}.",f"How sure I am: {out['sure']}. {out['why']}"])
    out['said']='\n'.join(lines)
    return out

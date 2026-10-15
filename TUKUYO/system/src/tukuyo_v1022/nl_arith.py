"""claude-patch1: natural-language arithmetic -> a checked pure expression.

The rewrite is purely syntactic. It only returns an expression when, after rewriting, the WHOLE
question has become a pure arithmetic expression; anything left over (a noun, an unknown verb)
means "not arithmetic" and the caller falls through to the other solvers. The expression is
then evaluated by proofs.calculate (exact Fractions), never by eval().
"""
from __future__ import annotations
import re,unicodedata

_KD={'〇':0,'零':0,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
_KU={'十':10,'百':100,'千':1000}
def _kanji_number(t):
    total=sec=part=0
    for c in t:
        if c in _KD:part=part*10+_KD[c] if part else _KD[c]
        elif c in _KU:sec+=(part or 1)*_KU[c];part=0
        elif c=='万':total+=(sec+part or 1)*10000;sec=part=0
        else:return None
    return total+sec+part
def _kanji(s):
    # a lone 一 inside words like 一緒 is left alone: only runs that touch a digit-context are converted
    return re.sub(r'[〇零一二三四五六七八九十百千万]+',lambda m:str(_kanji_number(m.group())),s)

N=r'(-?\d+(?:\.\d+)?|\([^()]*\))'
_TAIL=re.compile(r'(?:\s*(?:=|は|って))?\s*(?:いくつ|いくら|何|なに|なん|どれだけ|どのくらい|どれくらい)?\s*(?:に|と)?\s*(?:なりますか|なります|なる|でしょうか|でしょう|ですか|か|だ)?\s*[?？。!！]*\s*$')
_HEAD=re.compile(r'^(?:計算(?:して)?[:： ]*|次の計算[:： ]*|what\s+is\s+|what\'?s\s+|calculate\s+|compute\s+)',re.I)

def _join(op,items):return '('+op.join('('+i+')' for i in items)+')'

def expression(query):
    s=unicodedata.normalize('NFKC',str(query)).strip().lower()
    if len(s)>200:return None
    s=_HEAD.sub('',s)
    s=re.sub(r'(?:を)?(?:計算して(?:ください)?|の答え(?:は)?|を求めて(?:ください)?|を求めよ)\s*[?？。]*$','',s)
    s=_kanji(s)
    s=s.replace('×','*').replace('÷','/');s=re.sub(r'(?<=\d)\s*[ー−]\s*(?=\d)','-',s)
    # English operators
    for a,b in [(r'\bmultiplied\s+by\b','*'),(r'\btimes\b','*'),(r'\bdivided\s+by\b','/'),(r'\bplus\b','+'),(r'\bminus\b','-'),
                (r'\bto\s+the\s+power\s+of\b','**'),(r'\bsquared\b','**2'),(r'\bcubed\b','**3')]:
        s=re.sub(a,b,s)
    s=re.sub(r'(\d+(?:\.\d+)?)\s*(?:%|パーセント)\s*of\s*'+N,r'(\1*\2/100)',s)
    # Japanese operator words between operands
    for a,b in [('かける','*'),('掛ける','*'),('たす','+'),('足す','+'),('プラス','+'),('ひく','-'),('引く','-'),('マイナス','-'),('わる','/'),('割る','/')]:
        s=re.sub(r'(?<=[\d)])\s*'+a+r'\s*(?=[\d(-])',b,s)
    # Japanese constructions, repeated until stable (operands may be numbers or parenthesised results)
    rules=[
        (N+r'\s*の\s*'+N+r'\s*分の\s*'+N,lambda m:f'({m[1]}*{m[3]}/{m[2]})'),
        (N+r'\s*の\s*'+N+r'\s*乗',lambda m:f'({m[1]}**{m[2]})'),
        (N+r'\s*の\s*(?:二|2)\s*乗',lambda m:f'({m[1]}**2)'),
        (N+r'\s*の\s*'+N+r'\s*倍',lambda m:f'({m[1]}*{m[2]})'),
        (N+r'\s*の\s*'+N+r'\s*(?:%|パーセント)',lambda m:f'({m[1]}*{m[2]}/100)'),
        (N+r'\s*から\s*'+N+r'\s*を?\s*(?:引|ひ)(?:いたら|いた|くと|く)',lambda m:f'({m[1]}-{m[2]})'),
        (N+r'\s*を\s*'+N+r'\s*で\s*(?:割|わ)(?:ったら|った|ると|る)',lambda m:f'({m[1]}/{m[2]})'),
        (N+r'\s*に\s*'+N+r'\s*を?\s*(?:足|た)(?:したら|した|すと|す)',lambda m:f'({m[1]}+{m[2]})'),
        (N+r'\s*に\s*'+N+r'\s*を?\s*(?:掛|か)(?:けたら|けた|けると|ける)',lambda m:f'({m[1]}*{m[2]})'),
    ]
    for _ in range(8):
        before=s
        for pat,rep in rules:s=re.sub(pat,rep,s)
        # "AとBと...を(全部|ぜんぶ)?足す/かける"
        m=re.search(r'((?:'+N+r'\s*と\s*)+'+N+r')\s*を?\s*(?:全部|ぜんぶ|すべて|みんな)?\s*(?P<op>足|た|掛|か)(?:したら|した|すと|す|けたら|けた|けると|ける)',s)
        if m:
            items=re.findall(N,m[1]);op='+' if m['op'] in ('足','た') else '*'
            s=s[:m.start()]+_join(op,items)+s[m.end():]
        m=re.search(r'(?:the\s+)?sum\s+of\s+((?:'+N+r'\s*(?:,|and)\s*)+'+N+r')',s)
        if m:s=s[:m.start()]+_join('+',re.findall(N,m[1]))+s[m.end():]
        m=re.search(r'(?:the\s+)?product\s+of\s+((?:'+N+r'\s*(?:,|and)\s*)+'+N+r')',s)
        if m:s=s[:m.start()]+_join('*',re.findall(N,m[1]))+s[m.end():]
        if s==before:break
    s=_TAIL.sub('',s).strip()
    s=re.sub(r'\s*(?:は|=)\s*$','',s).strip()
    if not re.fullmatch(r'[-+*/().0-9\s]{1,200}',s) or not re.search(r'\d',s) or not re.search(r'[-+*/]',s.lstrip('-')):return None
    return s

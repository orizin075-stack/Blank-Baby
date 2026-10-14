"""generation 4: TUKUYO's own readers (no LLM). read(text) -> {'spec': FPL reading} | {'spec': None, 'reason': ...}"""
from __future__ import annotations
import re
from . import reader_en

JA=re.compile(r'[぀-ヿ㐀-鿿]')
# an amount not said exactly ('about 5 boxes', 'at least 8', 'more than 40 people', 'nearly 3 hours', 'up to 6'): no own
# reading of it, as in Japanese (3こぐらい). Exact wordings are read: '28 less than five times a number', '3 more than
# Tom', 'About how many necklaces can she make?' (a question, no number after it), 'read 60 pages over 3 days' (a span).
# On ASDiv dev and the private dev set this held back none of the 563 readings of the readers (v1022.8.0)
HEDGED_EN=re.compile(r"\b(?:about|around|approximately|roughly|nearly|almost|at least|at most|up to|no more than|no fewer than|no less than|"
                     r"more than|less than|fewer than|close to|just over|just under|well over|well under|some|maybe|perhaps|probably|under|over)"
                     r"\s+\$?\d+(?:[.,]\d+)*"
                     r"(?!\s*(?:times|%\s*of)\b)|\d+(?:[.,]\d+)*\s*(?:(?:[a-z]+\s+){0,2}or (?:more|so|fewer|less|over|under)\b|-?ish\b)",re.I)
SUMS_UP_TO=re.compile(r"\b(?:add|adds|added|sum|sums|summed|come|comes|came|amount|amounts|amounted|total|totals|totaled|totalled)\s+up\s+to\s",re.I)

# 'read 60 pages over 3 days' spreads the pages across the days; 'for over 6 weeks', 'in over 4 hours', 'there are over 7'
# say more than
SPAN=re.compile(r"over\s+\d+(?:[.,]\d+)*\s+(?:days?|weeks?|months?|years?|hours?|minutes?)\b",re.I)
NOT_A_SPAN=frozenset('for in are is was were be been than take takes took last lasts lasted after within spent spend spends wait waited'.split())

def _exact(text,m):
    w=m.group(0).lower()
    if w.startswith('up to'):return bool(SUMS_UP_TO.search(text[max(0,m.start()-12):m.end()]))
    if w.startswith('over') and SPAN.match(text,m.start()):
        before=re.findall(r"[a-z']+",text[max(0,m.start()-20):m.start()].lower())
        return bool(before) and before[-1] not in NOT_A_SPAN
    return False

def _hedged_en(text):
    return any(not _exact(text,m) for m in HEDGED_EN.finditer(text))

# a question about what is not so ('How many cups are not needed for 5 cakes?'): the readers below would answer it as if
# it asked what is. Only the rest of a whole ('How many students do not take the bus?', forms_story_en) and the one not
# full (a remainder, reader_en) read it
NEG_Q=re.compile(r"\b(?:not|never)\b|n't\b",re.I)
NOT_FULL=re.compile(r"\b(?:not|isn't|aren't|wasn't|weren't) full\b",re.I)

def _asks_what_is_not(text,spec):
    from .reader_en import sentences
    s=sentences(text)
    if not s:return False
    a,b=s[-1];q=text[a:b]
    if not NEG_Q.search(q) or NOT_FULL.search(q):return False
    return not str(spec.get('reader','')).startswith('tukuyo.g4.forms_story_en/1:rest')

# a statement that denies a holding or an event ('Lily never had some candies', 'He did not eat 3 of them'): no own
# reading, except the condition the least-common-multiple form reads ('The store does not sell parts of a pack'). On the
# dev sets that form's one reading is the only reading with a denial in a statement (v1022.8.0)
NEG_STATEMENT=re.compile(r"\b(?:not|never|no longer)\b|n't\b",re.I)

def _denies(text,spec):
    from .reader_en import sentences
    s=sentences(text)
    if not any(NEG_STATEMENT.search(text[a:b]) for a,b in s[:-1]):return False
    return not str(spec.get('reader','')).startswith('tukuyo.g4.forms_en/1:lcm')

def _refused(text,spec):
    if _asks_what_is_not(text,spec):return 'EN:ASKS_WHAT_IS_NOT'
    if _denies(text,spec):return 'EN:EVENT_NOT_SAID_AS_DONE'
    return None

# a statement of what did not happen: what could or should have been ('Maya could have had 14 stickers'), what almost
# happened ('She almost gave 5 stickers away', 'nearly half'). 'Each team should have 18 students' says what a team
# holds, and is read. On the dev sets this held back none of the readings (v1022.8.0)
PARTICIPLE=(r"(?:been|had|[a-z]+ed|given|eaten|bought|sold|made|got|gotten|taken|seen|found|lost|spent|done|gone|run|read|won|kept|"
            r"left|put|sent|brought|told|written|ridden|driven|flown|grown|thrown|drawn|shown|fallen|broken|chosen|spoken|stolen|"
            r"worn|paid|built|caught|fed|held|hit|cut|met|sat|slept|sung|swum|taught|understood|cost|set|let|spread|shut|quit)")
NOT_DONE_EN=re.compile(r"\b(?:could|should|would|might|may|must)(?: not|n't)? have "+PARTICIPLE+r"\b|"
                       r"\b(?:almost|nearly|hardly|barely|scarcely)\s+(?!\$?\d)[a-z]+",re.I)

def _not_done_en(text):
    from .reader_en import sentences
    s=sentences(text)
    return any(NOT_DONE_EN.search(text[a:b]) for a,b in s[:-1])

def read(text):
    if JA.search(text):
        try:from . import reader_ja
        except ImportError:return {'spec':None,'reason':'JA:NO_READER'}
        return reader_ja.read(text)
    if _hedged_en(text):return {'spec':None,'reason':'EN:AMOUNT_NOT_EXACT'}
    if _not_done_en(text):return {'spec':None,'reason':'EN:EVENT_NOT_SAID_AS_DONE'}
    from . import forms_en
    why=None
    r=forms_en.read(text)
    if r and r.get('spec'):
        why=_refused(text,r['spec'])
        if not why:return r
    r=reader_en.read(text)
    if r and r.get('spec'):
        why=_refused(text,r['spec'])
        if not why:return r
    # v1022.8.0: everyday story forms the story reader leaves unread
    from . import forms_story_en
    f=forms_story_en.read(text)
    if f and f.get('spec'):
        why=_refused(text,f['spec'])
        if not why:return f
    return {'spec':None,'reason':why} if why else r

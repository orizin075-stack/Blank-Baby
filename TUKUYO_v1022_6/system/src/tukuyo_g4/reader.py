"""generation 4: TUKUYO's own readers (no LLM). read(text) -> {'spec': FPL reading} | {'spec': None, 'reason': ...}"""
from __future__ import annotations
import re
from . import reader_en

JA=re.compile(r'[぀-ヿ㐀-鿿]')
# an amount not said exactly ('about 5 boxes', 'at least 8', 'more than 40 people', 'nearly 3 hours', 'up to 6'): no own
# reading of it, as in Japanese (3こぐらい). Exact wordings are read: '28 less than five times a number', '3 more than
# Tom', 'About how many necklaces can she make?' (a question, no number after it). On ASDiv dev and the private dev set
# this held back none of the 563 readings of the readers (v1022.8.0)
HEDGED_EN=re.compile(r"\b(?:about|around|approximately|roughly|nearly|almost|at least|at most|up to|no more than|no fewer than|no less than|"
                     r"more than|less than|fewer than|close to|just over|just under|some)\s+\$?\d+(?:[.,]\d+)*(?!\s*(?:times|%\s*of)\b)",re.I)
SUMS_UP_TO=re.compile(r"\b(?:add|adds|added|sum|sums|summed|come|comes|came|amount|amounts|amounted|total|totals|totaled|totalled)\s+up\s+to\s",re.I)

def _hedged_en(text):
    return any(not (m.group(0).lower().startswith('up to') and SUMS_UP_TO.search(text[max(0,m.start()-12):m.end()]))
               for m in HEDGED_EN.finditer(text))

def read(text):
    if JA.search(text):
        try:from . import reader_ja
        except ImportError:return {'spec':None,'reason':'JA:NO_READER'}
        return reader_ja.read(text)
    if _hedged_en(text):return {'spec':None,'reason':'EN:AMOUNT_NOT_EXACT'}
    from . import forms_en
    r=forms_en.read(text)
    if r and r.get('spec'):return r
    r=reader_en.read(text)
    if r and r.get('spec'):return r
    # v1022.8.0: everyday story forms the story reader leaves unread
    from . import forms_story_en
    f=forms_story_en.read(text)
    return f if f and f.get('spec') else r

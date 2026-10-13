"""generation 4: TUKUYO's own readers (no LLM). read(text) -> {'spec': FPL reading} | {'spec': None, 'reason': ...}"""
from __future__ import annotations
import re
from . import reader_en

JA=re.compile(r'[぀-ヿ㐀-鿿]')

def read(text):
    if JA.search(text):
        try:from . import reader_ja
        except ImportError:return {'spec':None,'reason':'JA:NO_READER'}
        return reader_ja.read(text)
    from . import forms_en
    r=forms_en.read(text)
    if r and r.get('spec'):return r
    r=reader_en.read(text)
    if r and r.get('spec'):return r
    # v1022.8.0: everyday story forms the story reader leaves unread
    from . import forms_story_en
    f=forms_story_en.read(text)
    return f if f and f.get('spec') else r

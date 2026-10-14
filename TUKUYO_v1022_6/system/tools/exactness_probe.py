#!/usr/bin/env python3
"""v1022.8.0: does the child's own reader still read a problem once its answer is no longer given exactly?

  exactness_probe.py [--out REPORT.json] [--show N]
  exactness_probe.py --end-to-end DATA [--out REPORT.json]    also through g4-solve's path with the individual DATA
                                                              (made with init; no parent, learn off): the v1022 core too

Each problem of the private dev set (private_eval_sets.DEV, English and Japanese) that the child's own reader reads is
rewritten, one place at a time (in a statement, or in the question), so that what the answer needs is not said
exactly: an event that did not happen or only might (ませんでした、予定、たそうです、did not, could have, almost), an amount said roughly (ぐらい、約、あまり、
近く、about, at least, over, or more), a supposition (もし), a question about what is not so. None of the rewrites
has a determined answer, so every reading of one is a reading that should not be. Reported: rewrites made, rewrites
still read, and each one read. Only the reader (no individual, no parent, cost 0). Some rewrites are not good English or
Japanese ('She almost has 12 marbles'); they are counted all the same.

The full suite found the first of these (2026-10-14): the Japanese reader read '時速5kmで4時間歩きません' as 4 hours
walked, and the English readers 'about 5 boxes' as 5. Run this after adding or widening a form.
"""
from __future__ import annotations
import argparse,collections,json,re,sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE/'src'));sys.path.insert(0,str(HERE/'tools'))
from private_eval_sets import DEV

CNT=r'(こ|個|まい|枚|本|人|円|ページ|才|歳|羽|km|m|cm|L|dL|mL|g|kg|台|冊|匹|ひき|分|時間|日|週間|箱|はこ|ふくろ|袋|さつ|だい)'
JA=[(r'ました。','ませんでした。'),(r'ます。','ません。'),(r'ました','ませんでした'),(r'ます','ません'),(r'ました。','なかった。'),
    (r'あります','ありません'),(r'います','いません'),(r'ました','るつもりです'),(r'ました','たいです'),(r'^','もし'),
    (r'ました。','たそうです。'),(r'ました。','たかもしれません。'),(r'ました。','たようです。'),(r'ました。','たらしいです。'),
    (r'ました。','たと聞きました。'),(r'ました。','たはずです。'),
    (r'(\d+)'+CNT,r'約\1\2'),(r'(\d+)'+CNT,r'およそ\1\2'),(r'(\d+)'+CNT,r'\1\2ぐらい'),(r'(\d+)'+CNT,r'\1\2くらい'),
    (r'(\d+)'+CNT,r'\1\2以上'),(r'(\d+)'+CNT,r'\1\2未満'),(r'(\d+)'+CNT,r'\1\2ほど'),(r'(\d+)'+CNT,r'\1\2あまり'),
    (r'(\d+)'+CNT,r'\1\2近く'),(r'(\d+)'+CNT,r'\1\2前後'),(r'(\d+)'+CNT,r'\1\2より多く')]
PAST={'gave':'given','ate':'eaten','bought':'bought','spent':'spent','sold':'sold','lost':'lost','found':'found','picked':'picked',
      'read':'read','walked':'walked','drove':'driven','ran':'run','made':'made','got':'gotten','put':'put','shared':'shared',
      'baked':'baked','gives':'given','eats':'eaten','has':'had','had':'had','is':'been','are':'been','costs':'cost','saved':'saved',
      'collected':'collected','planted':'planted','won':'won','paid':'paid'}
VERB=r'\b(' + '|'.join(PAST) + r')\b'
# rules for the statements (what is said to have happened) and for the question
EN=[(r'\b(has|had|have|is|are|was|were)\b',r'\1 not'),(VERB,r'did not \1'),(VERB,r'never \1'),
    (VERB,lambda m:'could have '+PAST[m.group(1)]),(VERB,lambda m:'should have '+PAST[m.group(1)]),
    (VERB,lambda m:'might have '+PAST[m.group(1)]),(VERB,r'almost \1'),(VERB,r'nearly \1'),(VERB,r'hardly \1'),
    (r'\b(\d+)\b',r'about \1'),(r'\b(\d+)\b',r'around \1'),(r'\b(\d+)\b',r'roughly \1'),(r'\b(\d+)\b',r'nearly \1'),
    (r'\b(\d+)\b',r'almost \1'),(r'\b(\d+)\b',r'at least \1'),(r'\b(\d+)\b',r'at most \1'),(r'\b(\d+)\b',r'up to \1'),
    (r'\b(\d+)\b',r'more than \1'),(r'\b(\d+)\b',r'over \1'),(r'\b(\d+)\b',r'under \1'),(r'\b(\d+)\b',r'maybe \1'),
    (r'\b(\d+)\b',r'perhaps \1'),(r'\b(\d+)\b',r'\1 or more'),(r'\b(\d+)\b',r'\1 or so'),(r'\b(\d+)\b',r'\1 or fewer'),
    (r'\b(\d+)\b',r'\1-ish'),(r'\b(\d+)\b',r'well over \1')]
EN_Q=[(r'(How many [a-z]+(?: [a-z]+)?) (are|do|did|will|does|can)\b',r'\1 \2 not'),(r'\b(\d+)\b',r'about \1'),(r'\b(\d+)\b',r'over \1')]
JA_Q=[(r'(\d+)'+CNT,r'約\1\2'),(r'(\d+)'+CNT,r'\1\2ぐらい'),(r'ますか',r'ませんか'),(r'ましたか',r'ませんでしたか'),(r'^',r'もし'),
      (r'ますか',r'たいですか')]


def own(text):
    from tukuyo_g4 import api,reader
    r=reader.read(text)
    if not r.get('spec'):return None
    e=api.evaluate(r['spec'],'own')
    return e['value'] if e['ok'] else None


def _parts(text,lang):
    """(start, end) of the statements and of the question"""
    if lang=='en':
        from tukuyo_g4.reader_en import sentences
        s=sentences(text)
    else:
        s=[(m.start(),m.end()) for m in re.finditer(r'[^。？?！!]+[。？?！!]?',text)]
    return s[:-1],s[-1:]


def rewrites(text,rules,parts,per_rule=3):
    for a,b in parts:
        seg=text[a:b]
        for pat,rep in rules:
            for m in list(re.finditer(pat,seg))[:per_rule]:
                new=rep(m) if callable(rep) else m.expand(rep)
                v=text[:a]+seg[:m.start()]+new+seg[m.end():]+text[b:]
                if v!=text:yield v


def answered(text,data):
    """the answer g4-solve gives with no parent (the v1022 core reads the Japanese problems too)"""
    from tukuyo_g4 import api
    try:r=api.solve(text,llm='off',data=data,learn=False)
    except Exception as e:  # noqa: BLE001 - a fault is reported as a row, not a crash of the probe
        return None,'ERROR:'+type(e).__name__
    return r.get('answer'),r.get('route')


def probe(sets=None,data=None):
    sets=sets or DEV
    out={'problems_read':{},'rewrites':{},'read':{},'readings':[]}
    if data:out.update(answered={},answers=[])
    for lang,rules,qrules in (('en',EN,EN_Q),('ja',JA,JA_Q)):
        n=0;made=0;still=0
        for text,_gold in sets[lang]:
            if own(text) is None:continue
            n+=1;stm,q=_parts(text,lang)
            for v in [*rewrites(text,rules,stm),*rewrites(text,qrules,q)]:
                made+=1;a=own(v)
                if a is not None:still+=1;out['readings'].append({'lang':lang,'text':v,'answer':a})
                if data:
                    ans,route=answered(v,data)
                    if ans is not None:out['answers'].append({'lang':lang,'text':v,'answer':ans,'route':route})
        out['problems_read'][lang]=n;out['rewrites'][lang]=made;out['read'][lang]=still
        if data:out['answered'][lang]=sum(1 for x in out['answers'] if x['lang']==lang)
    out['ok']=not out['readings']
    return out


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out');ap.add_argument('--show',type=int,default=20);ap.add_argument('--end-to-end',dest='data')
    a=ap.parse_args()
    r=probe(data=a.data)
    print(json.dumps({k:r[k] for k in ('problems_read','rewrites','read','answered','ok') if k in r},ensure_ascii=False))
    for x in r['readings'][:a.show]:print(' ',x['lang'],x['answer'],'|',x['text'])
    for x in r.get('answers',[])[:a.show]:print('  answered',x['lang'],x['answer'],x['route'],'|',x['text'])
    if a.out:Path(a.out).write_text(json.dumps(r,ensure_ascii=False,indent=1),encoding='utf-8')
    return 0


if __name__=='__main__':
    sys.exit(main())

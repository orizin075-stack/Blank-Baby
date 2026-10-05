from __future__ import annotations
import hashlib,json,math,re,unicodedata,sqlite3
from collections import Counter
from pathlib import Path

def _path(data): return Path(data)/'v1001'/'knowledge.jsonl'
def _dbpath(data): return Path(data)/'v1001'/'knowledge_index.sqlite3'
def _norm(s): return unicodedata.normalize('NFKC',str(s)).lower()
ALIASES={
 'たす':['+','加算','足す'],'足す':['+','加算','たす'],'かける':['*','乗算','掛ける'],'掛ける':['*','乗算','かける'],
 'わる':['/','除算','割る'],'割る':['/','除算','わる'],'ひく':['-','減算','引く'],'引く':['-','減算','ひく'],
 '発見':['discover','knowledge_gain','見つけ'],'研究':['research','study','調査'],'証明':['proof','theorem','定理'],
 '首都':['capital'],'コードネーム':['codename'],'友達':['friend'],'裏切':['betrayal']}

FACETS={
 'capital':['首都','首府','capital'],'population':['人口','人口数','population'],'location':['所在地','場所','位置','どこ','location','located'],
 'codename':['コードネーム','符号名','codename','code name'],'time':['時刻','時間','何時','始発','終電','time','when'],'person':['誰','人物','名前','氏名','who','name'],
 'date':['日付','年月日','いつ','date','year','when'],'color':['色','カラー','color','colour'],'founder':['創設者','創業者','設立者','founder'],'currency':['通貨','currency'],
 'language':['言語','公用語','language'],'height':['高さ','身長','標高','height'],'quantity':['数','個数','数量','何個','何人','count','how many']}
def facets(s):
    x=_norm(s);out={k for k,vals in FACETS.items() if any(_norm(v) in x for v in vals)}
    if 'location' in out and len(out)>1:out.discard('location')
    if 'person' in out and len(out)>1:out.discard('person')
    return out
def entity_anchor(s):
    x=_norm(s);words=sorted({w for vals in FACETS.values() for w in vals},key=len,reverse=True);alt='|'.join(re.escape(_norm(w)) for w in words)
    m=re.search(r'([a-z0-9_\u3040-\u30ff\u3400-\u9fff]{2,40}?)の(?:'+alt+r')',x)
    if m:return m.group(1).strip('、。?？ ')
    m=re.search(r"\b([a-z][a-z0-9_-]{1,31})['’]s\s+(?:capital|population|codename|color|currency|language|height)\b",x)
    if m:return m.group(1)
    m=re.search(r'\b(?:capital|population|codename|color|currency|language|height)\s+of\s+([a-z][a-z0-9_-]{1,31})\b',x)
    return m.group(1) if m else ''

def tokens(s):
    s=_norm(s);base=re.findall(r'[a-z0-9_]+|[\u3040-\u30ff\u3400-\u9fff]+',s);out=[]
    for x in base:
        out.append(x)
        if re.search(r'[\u3040-\u30ff\u3400-\u9fff]',x):
            out += [x[i:i+2] for i in range(max(0,len(x)-1))]
            out += [x[i:i+3] for i in range(max(0,len(x)-2))]
        for k,vals in ALIASES.items():
            if k in x: out.extend(vals)
    return out

def _connect(data):
    p=_dbpath(data);p.parent.mkdir(parents=True,exist_ok=True);db=sqlite3.connect(p)
    db.execute('PRAGMA journal_mode=WAL');db.execute('PRAGMA synchronous=NORMAL')
    db.execute('CREATE TABLE IF NOT EXISTS docs(id TEXT PRIMARY KEY, source TEXT, text TEXT, metadata TEXT, toks TEXT, dl INTEGER)')
    db.execute('CREATE TABLE IF NOT EXISTS postings(token TEXT, doc_id TEXT, tf INTEGER, PRIMARY KEY(token,doc_id))')
    db.execute('CREATE INDEX IF NOT EXISTS postings_token_idx ON postings(token)')
    db.execute('CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT)')
    return db

def _index_record(db,rec):
    ts=tokens(rec['text']);c=Counter(ts)
    db.execute('INSERT OR REPLACE INTO docs VALUES(?,?,?,?,?,?)',(rec['id'],rec.get('source',''),rec['text'],json.dumps(rec.get('metadata') or {},ensure_ascii=False),json.dumps(ts,ensure_ascii=False),len(ts)))
    db.execute('DELETE FROM postings WHERE doc_id=?',(rec['id'],))
    db.executemany('INSERT OR REPLACE INTO postings(token,doc_id,tf) VALUES(?,?,?)',[(t,rec['id'],n) for t,n in c.items()])

def _ensure_index(data):
    p=_path(data);db=_connect(data);size=p.stat().st_size if p.exists() else 0
    row=db.execute("SELECT value FROM meta WHERE key='source_size'").fetchone()
    if row is not None and int(row[0])==size:return db
    # Source changed outside the indexed writer or this is first migration: rebuild once.
    lines=[x for x in p.read_text(encoding='utf-8').splitlines() if x.strip()] if p.exists() else []
    db.execute('DELETE FROM postings');db.execute('DELETE FROM docs')
    for line in lines:_index_record(db,json.loads(line))
    db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('source_size',?)",(str(size),));db.commit();return db

def add(data,text,source='user',metadata=None):
    p=_path(data);p.parent.mkdir(parents=True,exist_ok=True);rid=hashlib.sha256((source+'\0'+text).encode()).hexdigest()[:20]
    rec={'id':rid,'source':source,'text':text,'metadata':metadata or {}}
    db=_ensure_index(data)
    if db.execute('SELECT 1 FROM docs WHERE id=?',(rid,)).fetchone():
        db.close();return {'ok':True,'id':rid,'count':sum(1 for _ in load(data)),'duplicate':True}
    with p.open('a',encoding='utf-8') as f:f.write(json.dumps(rec,ensure_ascii=False,sort_keys=True)+'\n')
    _index_record(db,rec);db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('source_size',?)",(str(p.stat().st_size),));db.commit();count=db.execute('SELECT COUNT(*) FROM docs').fetchone()[0];db.close()
    return {'ok':True,'id':rid,'count':count,'duplicate':False}

def load(data):
    p=_path(data)
    if not p.exists():return []
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]

def search_diagnostics(data,query,k=5):
    qt=Counter(tokens(query));db=_ensure_index(data)
    if not qt: db.close();return {'results':[],'answerable':False,'reason':'EMPTY_QUERY','coverage':0.0,'margin':0.0,'candidate_count':0,'candidate_strategy':'EMPTY'}
    N=db.execute('SELECT COUNT(*) FROM docs').fetchone()[0]
    if not N:db.close();return {'results':[],'answerable':False,'reason':'EMPTY_MEMORY','coverage':0.0,'margin':0.0,'candidate_count':0,'candidate_strategy':'EMPTY'}
    qtokens=list(qt);ph=','.join('?'*len(qtokens))
    # Fetch document frequencies in one query. v1014 did one COUNT query per token
    # and then one SELECT per candidate document, which made common-token queries
    # nearly linear in the entire memory size.
    dfrows=db.execute(f'SELECT token,COUNT(*) FROM postings WHERE token IN ({ph}) GROUP BY token',qtokens).fetchall()
    dfs={t:0 for t in qtokens};dfs.update({t:int(n) for t,n in dfrows})
    present=[t for t in qtokens if dfs[t]>0]
    if not present:db.close();return {'results':[],'answerable':False,'reason':'NO_LEXICAL_SUPPORT','coverage':0.0,'margin':0.0,'candidate_count':0,'candidate_strategy':'NO_MATCH'}

    # Prefer a small union of genuinely selective query tokens. For broad/common
    # queries, rank candidates inside SQLite and cap the expensive Python scoring
    # surface. This preserves exact retrieval for selective entity identifiers
    # while preventing a 10k-document N+1 scan.
    selective_limit=max(32,min(256,max(1,int(N*0.02))))
    rare=[t for t in sorted(present,key=lambda x:(dfs[x],-len(x),x)) if dfs[t]<=selective_limit][:3]
    candidate_cap=768
    if rare:
        rph=','.join('?'*len(rare))
        cand=[r[0] for r in db.execute(f'SELECT DISTINCT doc_id FROM postings WHERE token IN ({rph}) LIMIT ?',(*rare,candidate_cap))]
        strategy='SELECTIVE_UNION'
    else:
        cand=[r[0] for r in db.execute(
            f'SELECT doc_id FROM postings WHERE token IN ({ph}) GROUP BY doc_id ORDER BY COUNT(*) DESC,SUM(tf) DESC,doc_id LIMIT ?',
            (*qtokens,candidate_cap))]
        strategy='BOUNDED_COMMON'
    if not cand:db.close();return {'results':[],'answerable':False,'reason':'NO_LEXICAL_SUPPORT','coverage':0.0,'margin':0.0,'candidate_count':0,'candidate_strategy':strategy}

    avdl=db.execute('SELECT AVG(dl) FROM docs').fetchone()[0] or 1.0
    qweights={t:math.log(1+(N-dfs[t]+.5)/(dfs[t]+.5)) for t in qtokens}
    qfac=facets(query);qanchor=entity_anchor(query);denom=sum(qweights[t]*n for t,n in qt.items()) or 1.0

    # Batch-load documents instead of issuing one SELECT for every candidate.
    docs={};tfmap={did:{} for did in cand}
    chunk=400
    for i in range(0,len(cand),chunk):
        ids=cand[i:i+chunk];iph=','.join('?'*len(ids))
        for did,source,text,meta,dl in db.execute(f'SELECT id,source,text,metadata,dl FROM docs WHERE id IN ({iph})',ids):
            docs[did]=(source,text,meta,dl)
        params=tuple(qtokens)+tuple(ids)
        qph=','.join('?'*len(qtokens));iph=','.join('?'*len(ids))
        for did,tok,tf in db.execute(f'SELECT doc_id,token,tf FROM postings WHERE token IN ({qph}) AND doc_id IN ({iph})',params):
            tfmap.setdefault(did,{})[tok]=int(tf)

    rows=[]
    for did in cand:
        if did not in docs:continue
        source,text,meta,dl=docs[did];tf=tfmap.get(did,{});score=0.0;covered=0.0
        for t,qf in qt.items():
            f=tf.get(t,0)
            if not f:continue
            idf=qweights[t];covered+=idf*qf;score+=qf*idf*(f*2.2)/(f+1.2*(.25+.75*dl/max(avdl,1)))
        dfac=facets(text);fo=len(qfac&dfac);em=bool(qanchor and qanchor in _norm(text));lex=covered/denom
        if qfac:score*=(1.0+0.42*fo);score*=(0.48 if qfac and not fo else 1.0)
        if qanchor:score*=(1.55 if em else 0.42)
        sem=min(1.0,lex+(0.24 if fo else 0.0)+(0.30 if em else 0.0))
        rows.append({'score':round(score,6),'coverage':round(lex,6),'semantic_coverage':round(sem,6),'facet_match':sorted(qfac&dfac),'entity_anchor':qanchor,'entity_match':em,'id':did,'source':source,'text':text,'metadata':json.loads(meta)})
    rows.sort(key=lambda x:(-x['score'],-x['coverage'],x['id']));top=rows[:max(1,int(k))]
    if not top:db.close();return {'results':[],'answerable':False,'reason':'NO_CANDIDATES_AFTER_SCORE','coverage':0.0,'margin':0.0,'candidate_count':len(cand),'candidate_strategy':strategy}
    top1=top[0];second=top[1]['score'] if len(top)>1 else 0.0;margin=(top1['score']-second)/max(top1['score'],1e-9)
    facet_ok=(not qfac) or bool(top1.get('facet_match'));entity_ok=(not qanchor) or bool(top1.get('entity_match'));eff=float(top1.get('semantic_coverage',top1['coverage']))
    answerable=bool(facet_ok and entity_ok and eff>=.50 and (margin>=.15 or eff>=.78))
    reason='OK' if answerable else ('ENTITY_MISMATCH' if qanchor and not entity_ok else ('AMBIGUOUS_TOP_MATCH' if eff>=.50 else 'INSUFFICIENT_QUERY_EVIDENCE'))
    db.close();return {'results':top,'answerable':answerable,'reason':reason,'coverage':top1['coverage'],'semantic_coverage':round(eff,6),'margin':round(margin,6),'entity_anchor':qanchor,'candidate_count':len(cand),'candidate_strategy':strategy,'index_revision':'v1014.1'}

def search(data,query,k=5):return search_diagnostics(data,query,k)['results']

"""generation 4: TUKUYO's own reader for English word problems -> formal problem language (no LLM).

Analysis. The text is cut into sentences and clauses (a clause starts at a subject followed by a verb). Every
number of the text gets a mention: its noun phrase (noun, adjectives, "N boxes of crayons"), the verb on its left
and that verb's subject, and the words around it. Mentions become frames
  state    X has/had N things ; there are N things (in P) ; X has N things left ; X is N (years old)
  change   X got/bought/found N (more) things ; X ate/spent/lost N things ; X gave N things to Y (a transfer)
           N (more) people joined / came ; N people left / quit ; X had some ... (an unknown amount)
  act      X read/walked/scored N things (a counter that starts at 0)
  rate     N things in/on/for/to each group ; each group has N things ; N things per group ; N things a day ; N each
  price    a thing costs $N ; $N each ; for $N
  compare  X has N more/fewer things than Y ; X has N times as many things as Y
The question may state numbers too ("in 3 days", "do 8 bees have", "to have 43 cats"): they become question
frames.

Schemas. Each schema reads one shape of problem, strictly, and writes FPL facts only for it:
  holding  holdings over time (x0 = had, x1 = x0 + got, ...), at first / now / left; the amount of an event;
           totals over holders, kinds or events
  groups   total = number of groups x things per group (+ loose things)
  share    things per group = total / groups ; groups = total / per group (floor, ceil, remainder by wording)
  compare  X = Y +- N ; X = Y x N ; the difference of two holdings
  price    cost = number x price ; price = cost / number ; change = paid - cost
  need     still needed = wanted - had
  rest     the rest = total - the parts
A schema applies only if every number of the text is consumed: used by its facts, or a number of a frame about a
different thing that nothing links to the asked thing (declared unused). read() returns a reading when exactly
one schema applies, or when every applicable schema gives the same answer; otherwise None (no answer).
"""
from __future__ import annotations
import re
from fractions import Fraction
from . import numbers as N

# ----------------------------------------------------------------------------- words
IRREG={'people':'person','children':'child','men':'man','women':'woman','feet':'foot','teeth':'tooth','mice':'mouse','geese':'goose',
       'leaves':'leaf','knives':'knife','wolves':'wolf','loaves':'loaf','shelves':'shelf','halves':'half','lives':'life','wives':'wife',
       'calves':'calf','thieves':'thief','dice':'die','oxen':'ox','cacti':'cactus','fungi':'fungus','puppies':'puppy','candies':'candy',
       'series':'series','species':'species','fish':'fish','fishes':'fish','sheep':'sheep','deer':'deer','moose':'moose','pants':'pants','jeans':'jeans',
       'glasses':'glass','scissors':'scissors','shorts':'shorts','clothes':'clothes','news':'news','dollars':'dollar','cents':'cent',
       'cookies':'cookie','movies':'movie','pies':'pie','ties':'tie','brownies':'brownie','zombies':'zombie','goalies':'goalie','smoothies':'smoothie',
       'shoes':'shoe','toes':'toe','canoes':'canoe','horses':'horse','houses':'house','buses':'bus','classes':'class','dresses':'dress','lenses':'lens',
       'gloves':'glove','stoves':'stove','olives':'olive','cloves':'clove','doves':'dove','curves':'curve','sleeves':'sleeve','grooves':'groove','waves':'wave',
       'potatoes':'potato','tomatoes':'tomato','heroes':'hero','mangoes':'mango','volcanoes':'volcano','echoes':'echo','dominoes':'domino',
       'boxes':'box','foxes':'fox','sandwiches':'sandwich','peaches':'peach','benches':'bench','dishes':'dish','brushes':'brush','bushes':'bush',
       'matches':'match','watches':'watch','lunches':'lunch','beaches':'beach','inches':'inch','churches':'church','branches':'branch','coaches':'coach',
       'pennies':'penny','berries':'berry','cherries':'cherry','strawberries':'strawberry','blueberries':'blueberry','batteries':'battery','stories':'story',
       'roses':'rose','vases':'vase','cases':'case','bases':'base','pieces':'piece','prizes':'prize','sizes':'size','races':'race','places':'place','nurses':'nurse',
       'pages':'page','cages':'cage','oranges':'orange','packages':'package','sausages':'sausage','bandages':'bandage','badges':'badge','bridges':'bridge',
       'marbles':'marble','bottles':'bottle','tables':'table','apples':'apple','puzzles':'puzzle','candles':'candle','vehicles':'vehicle','circles':'circle',
       'bicycles':'bicycle','pickles':'pickle','noodles':'noodle','needles':'needle','bubbles':'bubble','turtles':'turtle','beetles':'beetle','eagles':'eagle',
       'popsicles':'popsicle','tricycles':'tricycle','muffins':'muffin','crayons':'crayon','envelopes':'envelope','sticks':'stick','times':'time','sheets':'sheet',
       'slices':'slice','dices':'dice','pants':'pants','minutes':'minute','plates':'plate','skates':'skate','kites':'kite','bites':'bite','notes':'note','votes':'vote',
       'grapes':'grape','shapes':'shape','tapes':'tape','ropes':'rope','pipes':'pipe','games':'game','names':'name','frames':'frame','planes':'plane','lines':'line',
       'miles':'mile','tiles':'tile','files':'file','smiles':'smile','holes':'hole','poles':'pole','roles':'role','rules':'rule','tubes':'tube','cubes':'cube','cones':'cone',
       'stones':'stone','bones':'bone','phones':'phone','zones':'zone','scenes':'scene','genes':'gene','tunes':'tune','dunes':'dune','crates':'crate','dates':'date',
       'gates':'gate','plates':'plate','rates':'rate','states':'state','skates':'skate','stamps':'stamp','lamps':'lamp','yards':'yard','cards':'card','birds':'bird'}
def sing(w):
    w=w.lower().strip("'")
    if w.endswith("'s"):w=w[:-2]
    if w in IRREG:return IRREG[w]
    if len(w)<=3 or w.endswith(('ss','us','is')):return w
    if w.endswith('ies'):return w[:-3]+'y'
    if re.search(r'(?:ches|shes|xes|zes|sses)$',w):return w[:-2]
    if w.endswith('ves'):return w[:-3]+'f'
    if w.endswith('s'):return w[:-1]
    return w

def V(*ws):
    out=set()
    for w in ws:out.update(w.split('|'))
    return out
HAVE=V('has|have|had|owns|own|owned|holds|hold|held|keeps|keep|kept|contains|contain|contained|stores|stored|having|carries|carried|carry')
BE=V('is|are|was|were|be|been|being')
GAIN=V('put|puts|placed|places|stored|stores|got|gets|get|received|receives|receive|found|finds|find|bought|buys|buy|picked|picks|pick|collected|collects|collect|won|wins|win',
       'made|makes|make|baked|bakes|bake|grew|grows|grow|earned|earns|earn|added|adds|add|caught|catches|catch|saved|saves|save|gathered|gathers|gather',
       'purchased|purchases|purchase|harvested|harvests|harvest|obtained|acquired|inherited|adopted|raised|produced|built|builds|build|sewed|knitted',
       'planted|plants|plant|cooked|cooks|cook|prepared|prepares|prepare|brought|brings|bring|ordered|orders|order|printed|prints|print',
       'gained|gains|gain|borrowed|borrows|borrow|grabbed|grabs|recovered|stocked|stocks|fried|grilled|crafted|created|creates|create|drew|draws|draw|painted|paints|paint|wrote|writes|write|cut|cuts|took|takes')
LOSE=V('ate|eats|eat|used|uses|use|spent|spends|spend|lost|loses|lose|sold|sells|sell|broke|breaks|break|drank|drinks|drink|popped|pops|pop|returned|returns|return',
       'donated|donates|donate|lent|lends|lend|paid|pays|pay|mailed|mails|mail|sent|sends|send|shipped|ships|ship',
       'discarded|discards|discard|removed|removes|remove|burned|burns|burn|deleted|deletes|delete|destroyed|destroys|destroy|spilled|spills|spill',
       'threw|throws|throw|tossed|tosses|toss|dropped|drops|drop|gave|gives|give|handed|hands|hand|passed|passes|pass|traded|trades|trade|shared|shares|share',
       'cracked|ruined|tore|ripped|melted|wasted|recycled|consumed|consumes|consume|served|serves|serve|fed|feeds|feed|distributed|distributes|distribute|delivered|delivers|deliver')
TRANSFER=V('gave|gives|give|handed|hands|hand|passed|passes|pass|sent|sends|send|mailed|mails|mail|lent|lends|lend|donated|donates|donate|shared|shares|share',
           'fed|feeds|feed|served|serves|serve|distributed|distributes|distribute|delivered|delivers|deliver|paid|pays|pay|sold|sells|sell')
JOIN=V('joined|joins|join|came|comes|come|arrived|arrives|arrive|boarded|boards|board|entered|enters|enter|landed|lands|land|hatched|attended|enrolled')
LEAVE=V('left|leaves|leave|quit|quits|departed|departs|depart|escaped|died|flew|ran|swam|walked|went|dropped|fell|go|goes')
OTHER_VERBS=V('is|are|was|were|playing|eating|sitting|standing|waiting|swimming|flying|running|walking|sleeping|working|living|growing|go|goes|went|came|come|play|plays|sit|sits|stand|stands|live|lives|decided|wanted|began|started|tried|helped|needed|got|became|stayed|remained')
ACT=V('read|reads|saw|sees|see|counted|counts|count|solved|solves|solve|played|plays|play|ran|runs|run|walked|walks|walk',
      'swam|swims|swim|drove|drives|drive|traveled|travels|travel|travelled|rode|rides|ride|worked|works|work|practiced|practices|practice|watched|watches|watch',
      'visited|visits|visit|answered|answers|answer|scored|scores|score|jumped|jumps|jump|biked|bikes|bike|hiked|hikes|hike|typed|types|type|sang|sings|sing',
      'completed|completes|complete|spotted|spots|spot|cleaned|cleans|clean|washed|washes|wash|fixed|fixes|fix|recorded|records|record',
      'climbed|climbs|climb|kicked|kicks|kick|hit|hits|did|does|do|finished|finishes|finish|blew|blows|blow|inflated|filled|fills|fill|ironed|folded|watered|waters|water')
COST=V('cost|costs|costed|priced|charges|charged|charge|worth')
GOAL=V('calls|call|called|requires|require|required|needs|need|needed|asks|wants|want|wanted')
INTENT=V('wants|want|wanted|needs|need|needed|plans|plan|planned|hopes|hope|hoped|wishes|wish|wished|tries|try|tried|likes|like|would|will|going|should|must')
PRON={'he','she','they','him','her','them','it','i','we','you','me','us','his','their','its','my','our','your','hers','theirs'}
DET=V('the|a|an|his|her|their|its|my|our|your|this|that|these|those|some|each|every|all|both|any|another|other|one|several|many|few|most|no')
PREP=V('of|for|in|on|at|to|from|with|by|per|into|onto|than|about|after|before|during|over|under|around|between|among|through|across|off|out|up|down|away|back|along|inside|outside|near|behind|until|since|without|apiece|within')
CONJ=V('and|or|but|then|so|because|if|when|while|though|although|which|who|that|where')
QWORD=V('how|what|which|who|whom|whose|why|when|where|find')
MODS=V('more|fewer|less|extra|additional|new|old|other|different|total|left|remaining|whole|full|empty|same|equal|small|large|big|little|whole|entire|own')
AUX=V('will|would|can|could|should|shall|may|might|must|does|did|do|has|have|had|is|are|was|were|been|be|to|not')
NOT_NOUN=AUX|PRON|DET|PREP|CONJ|QWORD|HAVE|BE|V('more|fewer|less|left|now|then|total|all|altogether|together|each|every|per|times|as|much|many|same|equal|equally|only|just|also|already|still|again|later|today|yesterday|tomorrow|some|rest|remaining|first|last|next|there|here|out|away|up|down|back|in|on|off|over|twice|half|double|triple|evenly|exactly|about|around|almost|nearly|than|very|too|so')
GROUPS=V('box|bag|pack|package|packet|bottle|can|jar|bunch|basket|case|carton|set|pair|row|column|group|team|shelf|tray|crate|container|plate|bowl|cup|stack|pile|roll|bundle|batch|load|page|book|sheet|bar|stick|loaf|dozen|section|table|car|bus|van|truck|boat|class|tank|bin|drawer|aisle|floor|level|layer|tier|vase|pot|cage|pen|room|building|house|tent|herd|flock|train|ship|plane|round|game|day|week|month|year|hour|minute|second|time|trip|lap|session|night|morning|tray|bucket|jug|pan|batch|serving|bouquet|wall|street|block|tree|branch|plant|garden|pizza|pie|cake|bucket|album|folder|binder|envelope|drawer|cabinet|truckload|cartload')
UNITS=V('mile|kilometer|meter|centimeter|millimeter|foot|inch|yard|pound|ounce|kilogram|gram|liter|milliliter|gallon|quart|pint|cup|hour|minute|second|day|week|month|year|dollar|cent|degree|point|ton|acre|lap')
TIME_UNITS=V('second|minute|hour|day|week|month|year|night|morning|afternoon|evening|weekend')
CAP_STOP=V('There|Then|How|What|The|A|An|On|In|At|After|Later|Next|Today|Yesterday|His|Her|Their|First|Finally|Now|He|She|They|It|If|Each|Every|Some|One',
           'Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|I|We|You|When|While|This|That|These|Those',
           'January|February|March|April|May|June|July|August|September|October|November|December|Mr|Mrs|Ms|Dr|Find|Of|For|To|From|With|But|And|So|All|Both',
           'Last|During|Before|Since|Because|Also|Another|Most|Many|Several|Its|My|Our|Your|Why|Where|Which|Who|At|By|As|Altogether|Together|Total|Halloween|Christmas',
           'Easter|Thanksgiving|Valentine|Day|Street|Avenue|Road|Lake|River|Mountain|Park|School|Store|Team|Club|Center|Palace|Tower|Towers|Building|State|City|Island|Ocean|Sea|Bay|Christmas|English|Spanish|French|Chinese|Japanese|American')
PERSONS=V('friend|student|child|kid|person|people|guest|player|member|worker|boy|girl|classmate|cousin|neighbor|teammate|grandchild|son|daughter|camper|customer|visitor|teacher|team|family|class|group|niece|nephew|brother|sister|grandson|granddaughter|pupil|athlete|employee|kid|adult|man|woman|baby|scout|soldier|dancer|singer|runner|swimmer|player|guest')
KIN=V('mom|mother|dad|father|sister|brother|aunt|uncle|grandma|grandmother|grandpa|grandfather|friend|friends|cousin|cousins|teacher|son|daughter|parents|wife|husband|neighbor|neighbors|boss|coach|classmate|classmates|family|parent|sisters|brothers|kids|children')
COLORS=V('red|blue|green|yellow|white|black|pink|purple|orange|brown|gray|grey|gold|silver')
COMPARATIVE=V('more|fewer|less|older|younger|taller|shorter|longer|heavier|lighter|cheaper|bigger|smaller|farther|further|higher|lower|faster|slower|wider|narrower|deeper')

class NoRead(Exception):pass
def no(reason):raise NoRead(reason)

# ----------------------------------------------------------------------------- tokens
ABBR=re.compile(r'(?:\bMrs?|\bMs|\bDr|\bSt|\bJr|\bSr|\bvs|\betc|\bft|\bin|\blbs?|\boz|\bNo)\.$')
def sentences(t):
    out=[];start=0
    for m in re.finditer(r'[.?!]+(?=\s|$)',t):
        if ABBR.search(t[start:m.end()]):continue
        if t[start:m.end()].strip():out.append((start,m.end()))
        start=m.end()
    if t[start:].strip():out.append((start,len(t)))
    return out

class Tok:
    __slots__=('s','e','w','low','kind','num')
    def __init__(s,a,b,w,kind,num=None):s.s=a;s.e=b;s.w=w;s.low=w.lower();s.kind=kind;s.num=num
    def __repr__(s):return f'{s.kind}:{s.w}'

_TOKRE=re.compile(r"\s+|\$|[A-Za-z]+(?:'[a-z]+)?|\d+(?:[.,]\d+)*|[^\sA-Za-z\d]")
def tokens(t,a,b,nums):
    out=[];i=a
    inside={n.start:n for n in nums if a<=n.start and n.end<=b}
    while i<b:
        n=inside.get(i)
        if n is not None:out.append(Tok(n.start,n.end,t[n.start:n.end],'num',n));i=n.end;continue
        m=_TOKRE.match(t,i)
        if not m:i+=1;continue
        e=m.end();cut=next((x for x in inside if i<x<e),None)
        if cut is not None:e=cut
        w=t[i:e]
        if not w.isspace():
            if w[0].isalpha():out.append(Tok(i,e,w,'word'))
            elif w=='$':out.append(Tok(i,e,w,'money'))
            elif w[0].isdigit():out.append(Tok(i,e,w,'digit'))
            else:out.append(Tok(i,e,w,'punct'))
        i=e
    return out

def verbish(w):
    return w in GAIN or w in LOSE or w in ACT or w in JOIN or w in LEAVE or w in HAVE or w in COST or w in TRANSFER

FAMILIES=[('give','gave','gives','handed','hand','hands','passed','pass','passes'),('eat','ate','eats'),('buy','bought','buys','purchase','purchased','purchases'),
          ('sell','sold','sells'),('find','found','finds'),('pick','picked','picks'),('read','reads'),('use','used','uses'),('spend','spent','spends'),
          ('get','got','gets','received','receive','receives'),('lose','lost','loses'),('make','made','makes'),('bake','baked','bakes'),('collect','collected','collects'),
          ('earn','earned','earns'),('win','won','wins'),('catch','caught','catches'),('plant','planted','plants'),('save','saved','saves'),('join','joined','joins'),
          ('leave','left','leaves'),('score','scored','scores'),('cut','cuts'),('put','puts'),('take','took','takes'),('drink','drank','drinks'),('break','broke','breaks'),
          ('pop','popped','pops'),('throw','threw','throws'),('see','saw','sees'),('walk','walked','walks'),('run','ran','runs'),('swim','swam','swims'),
          ('drive','drove','drives'),('play','played','plays'),('add','added','adds'),('grow','grew','grows'),('donate','donated','donates'),('send','sent','sends'),
          ('share','shared','shares'),('serve','served','serves'),('feed','fed','feeds'),('come','came','comes'),('arrive','arrived','arrives'),('quit','quits'),
          ('complete','completed','completes'),('solve','solved','solves'),('write','wrote','writes'),('borrow','borrowed','borrows'),('lend','lent','lends'),
          ('harvest','harvested','harvests'),('order','ordered','orders'),('gather','gathered','gathers'),('cook','cooked','cooks'),('prepare','prepared','prepares'),
          ('bring','brought','brings'),('trade','traded','trades'),('drop','dropped','drops'),('remove','removed','removes'),('return','returned','returns'),
          ('travel','traveled','travelled','travels'),('ride','rode','rides'),('work','worked','works'),('watch','watched','watches'),('visit','visited','visits'),
          ('answer','answered','answers'),('jump','jumped','jumps'),('do','did','does'),('clean','cleaned','cleans'),('wash','washed','washes'),('draw','drew','draws'),
          ('paint','painted','paints'),('count','counted','counts'),('spot','spotted','spots'),('climb','climbed','climbs'),('deliver','delivered','delivers'),
          ('mail','mailed','mails'),('ship','shipped','ships'),('blow','blew','blows'),('fill','filled','fills'),('water','watered','waters'),('distribute','distributed','distributes'),
          ('attend','attended','attends'),('board','boarded','boards'),('enter','entered','enters'),('hatch','hatched'),('die','died','dies'),('fly','flew','flies'),
          ('fall','fell','falls'),('go','went','goes')]
def fam(v):
    if v is None:return None
    v=v.lower()
    for f in FAMILIES:
        if v in f:return f[0]
    return v

def lemma(w):
    """verb stem for -ing / -ed forms: selling->sell, getting->get, baking->bake"""
    w=w.lower()
    for suf in ('ing','ed'):
        if w.endswith(suf) and len(w)>len(suf)+2:
            b=w[:-len(suf)]
            if len(b)>2 and b[-1]==b[-2] and b[-1] not in 'lsz':return b[:-1]
            return b
    return w

def lit(v):
    v=Fraction(v);return str(v.numerator) if v.denominator==1 else f'{v.numerator}/{v.denominator}'

class Frame(dict):
    __getattr__=dict.get

# ----------------------------------------------------------------------------- analysis
class Story:
    def __init__(s,t):
        s.t=t;s.nums=N.find(t);s.frames=[];s.people=[];s.last_owner=None;s.last_noun=None;s.noun_of={};s.vague=[];s.seen_nouns=[];s.last_thing=None
        s.text_low=t.lower()
    # ---- names and pronouns
    def is_name(s,tk,first=False):
        if tk.kind!='word' or not tk.w[:1].isupper():return False
        w=tk.w[:-2] if tk.low.endswith("'s") else tk.w
        if w in CAP_STOP or w.lower() in NOT_NOUN or w.lower() in KIN:return False
        if w.lower() in GROUPS|UNITS or sing(w.lower()) in s.seen_nouns:return False
        return True
    def person(s,w):
        w=w[:-2] if w.lower().endswith("'s") else w
        if w not in s.people:s.people.append(w)
        return w
    def resolve(s,p):
        p=p.lower()
        if p in ('i','me','my','we','us','our','you','your'):return {'me':'i','my':'i','us':'we','our':'we','your':'you'}.get(p,p)
        if p in ('they','them','their'):
            if not s.people and s.last_owner and s.last_owner not in ('there',):return s.last_owner
            return 'they'
        if p in ('it','its'):return s.last_thing or 'it'
        if len(s.people)==1:return s.people[0]
        if s.last_owner:return s.last_owner          # the subject of the latest clause
        if not s.people:return p if p in ('he','she') else 'they'
        no('PRONOUN')
    def holder(s,toks):
        """a holder named by a short phrase: Tom / he / Tom's mom / his sister / the store"""
        ws=[x for x in toks if x.kind=='word']
        if not ws:return None
        for i,x in enumerate(ws):
            if x.low in ('he','she','i','we','you','they','it','him','them','me','us'):return s.resolve(x.low)
            if x.low in ('his','her','their','my','our','your') and i+1<len(ws):
                rest=[y.low for y in ws[i+1:] if y.low not in DET and y.low not in MODS]
                if rest:return s.resolve(x.low)+"'s "+sing(rest[-1])
            if s.is_name(x):
                if x.low.endswith("'s"):
                    rest=[y.low for y in ws[i+1:] if y.low not in DET]
                    if rest:return s.person(x.w)+"'s "+sing(rest[-1])
                    return s.person(x.w)
                return s.person(x.w)
        nouns=[x for x in ws if x.low not in NOT_NOUN and x.low not in MODS]
        return sing(nouns[-1].low) if nouns else None
    # ---- noun phrases
    def np_after(s,toks,i):
        """noun phrase after token i -> dict(noun, adj, end, of, ofend, cmp)"""
        j=i+1;words=[];cmp=None
        while j<len(toks) and toks[j].kind=='word':
            w=toks[j].low
            if w in COMPARATIVE and not words:cmp=w;j+=1;continue
            if w in ('extra','additional') and not words:j+=1;continue
            if w in NOT_NOUN-MODS or w in INTENT or (s.is_name(toks[j]) and (words or j!=i+1)):break
            if not words and (w in OTHER_VERBS or (verbish(w) and not w.endswith('s'))):break
            if words and w in V('long|tall|high|deep|wide|old|heavy|thick|away|apart|ago|later|earlier|older|younger|taller|shorter|longer|wider|deeper|heavier|lighter|tall'):break
            if words and len(words[-1])>3 and words[-1].endswith('s') and not words[-1].endswith('ss') and not w.endswith('s') and w not in IRREG.values() and sing(words[-1])!=words[-1]:break
            if words and (verbish(w) or w in BE|HAVE or w in OTHER_VERBS or (w.endswith('ed') and w not in ('red','colored','coloured','striped','spotted','dotted','painted','frosted','salted','dried','frozen'))):break
            words.append(w);j+=1
            if w.endswith("'s"):break
        while words and words[-1] in MODS:
            w=words.pop()
            if w in COMPARATIVE and cmp is None:cmp=w
        out={'noun':None,'adj':(),'end':j,'of':None,'ofend':None,'cmp':cmp}
        if not words:return out
        out['noun']=sing(words[-1]);out['adj']=tuple(x for x in words[:-1] if x not in MODS)
        if j+1<len(toks) and toks[j].low=='of':
            k=j+1;w2=[]
            while k<len(toks) and toks[k].kind=='word' and toks[k].low not in NOT_NOUN-MODS and not (verbish(toks[k].low) and w2) and not s.is_name(toks[k]):
                w2.append(toks[k].low);k+=1
            w2=[x for x in w2 if x not in MODS]
            if w2:out['of']=sing(w2[-1]);out['ofend']=k;out['ofadj']=tuple(w2[:-1])
        return out
    # ---- clauses
    def starts_clause(s,toks,k):
        """does a clause start at toks[k]? a subject (name, pronoun, determiner + noun) followed by a verb"""
        j=k;seen=0
        while j<len(toks) and seen<5:
            x=toks[j]
            if x.kind=='num':return False
            if x.kind!='word':return False
            if seen>0 and (verbish(x.low) or x.low in BE|INTENT|V('decided|began|started|went')):return True
            if x.low in PRON|DET|KIN|MODS or s.is_name(x) or x.low not in NOT_NOUN:seen+=1;j+=1;continue
            return False
        return False
    def body(s,a,b):
        toks=tokens(s.t,a,b,s.nums)
        clauses=[];cur=[]
        for k,tk in enumerate(toks):
            nxt=toks[k+1].low if k+1<len(toks) else ''
            brk=False
            if tk.low==';':brk=True
            elif tk.low in ('then',) and cur and not (cur[-1].low in ('and',',')):brk=True
            elif tk.low in (',','and','but','while','so') and cur and k+1<len(toks):
                k2=k+1
                if toks[k2].low in ('and','but','then','so') and tk.low==',':k2+=1
                if k2<len(toks) and toks[k2].low=='then':k2+=1
                if k2<len(toks) and (verbish(toks[k2].low) and tk.low in ('and','but')):brk=True
                elif self_starts(s,toks,k2):brk=True
            if brk:
                if cur:clauses.append(cur)
                cur=[];continue
            cur.append(tk)
        if cur:clauses.append(cur)
        subj=None
        for c in clauses:subj=s.clause(c,subj)
    def verbs(s,toks):
        """positions of the verbs of a clause, with their mood (None or 'intent')"""
        out=[]
        for k,x in enumerate(toks):
            if x.kind!='word':continue
            if k+1<len(toks) and toks[k+1].low in ('room','rooms','area','shop','store','table','line','station','box','bag','hall') and k>0 and toks[k-1].low in DET:continue
            if x.low in INTENT and not (x.low=='can' and k+1<len(toks) and toks[k+1].kind=='word' and False):
                out.append((k,'intent'));continue
            if verbish(x.low) or x.low in BE or x.low in V('decided|began|started|went|became|weighs|weighed|measures|measured|takes|took|calls|requires|required'):
                prev=toks[k-1].low if k else ''
                mood=None
                if prev=='to' and not (k>=2 and toks[k-2].low in V('decided|went|began|started|managed|helped|came|got|wanted')):mood='intent'
                if prev=='to' and k>=2 and toks[k-2].low in V('wanted|wants|want|needs|need|needed|plans|plan|hopes|hope|likes|like|tries|try|tried|going'):mood='intent'
                out.append((k,mood))
        return out
    def clause(s,toks,subj):
        vs=s.verbs(toks)
        span=s.t[toks[0].s:toks[-1].e]
        first_v=vs[0][0] if vs else None
        csubj=s.holder(toks[:first_v]) if first_v else None
        if first_v is not None and csubj is None and not any(x.kind=='num' for x in toks[:first_v]):csubj=subj
        for x in toks:
            if s.is_name(x) and (x.w[:-2] if x.low.endswith("'s") else x.w) not in s.people:s.person(x.w)
        if csubj and csubj not in ('there','it','they','i','we','you') and "'" not in csubj:s.last_owner=csubj
        if csubj and csubj not in ('there','it','they','i','we','you') and (csubj not in s.people):s.last_thing=csubj
        intent=any(m=='intent' for _,m in vs)
        nidx=[k for k,x in enumerate(toks) if x.kind=='num']
        for k,x in enumerate(toks):
            if x.kind=='word' and x.low not in NOT_NOUN and x.low not in MODS and not s.is_name(x) and not verbish(x.low):
                n=sing(x.low)
                if n not in s.seen_nouns:s.seen_nouns.append(n)
        total_words=bool(re.search(r'\b(?:a total of|in total|total of|in all|altogether|all together|together|combined)\b',span.lower()))
        if not nidx:
            # numberless events about something countable: "had some balloons", "watered the equal amount of trees"
            for k,x in enumerate(toks):
                if x.kind=='word' and x.low.endswith('ing') and k+1<len(toks) and toks[k+1].low=='some':
                    base={'eating':'ate','using':'used','selling':'sold','giving':'gave','spending':'spent','losing':'lost','buying':'bought','finding':'found','picking':'picked','getting':'got','receiving':'received','baking':'baked','making':'made'}.get(x.low)
                    if base:
                        np=s.np_after(toks,k+1);noun=np['noun'] or s.noun_of.get(csubj or subj) or s.last_noun
                        if noun:
                            s.frames.append(Frame(kind='change',m=None,noun=noun,adj=(),owner=csubj or subj or s.last_owner,verb=base,sign=+1 if base in GAIN else -1,span=span,other=None,implicit=np['noun'] is None))
                            return csubj or subj
            somes=[q for q,x in enumerate(toks) if x.low in ('some','several')]
            made=0
            for q in somes[:1]:
                before_n=len(s.frames);s.mention(toks,q,vs,csubj or subj,span,total_words,unknown=True);made+=len(s.frames)-before_n
            if made:return csubj or subj
            for k,mood in vs:
                if toks[k].low=='left':continue
                if mood is None and toks[k].low in GAIN|LOSE|TRANSFER|JOIN|LEAVE:
                    for x in toks:
                        if x.kind=='word' and x.low not in NOT_NOUN and x.low not in MODS and not s.is_name(x) and not verbish(x.low) and x.low not in OTHER_VERBS:
                            s.vague.append(Frame(noun=sing(x.low),verb=toks[k].low,owner=csubj or subj,span=span))
            return csubj or subj
        for k in nidx:s.mention(toks,k,vs,csubj or subj,span,total_words)
        return csubj or subj
    def verb_for(s,toks,vs,k):
        left=[(p,m) for p,m in vs if p<k]
        return left[-1] if left else (None,None)
    def subject_of(s,toks,vs,vpos,default):
        """the subject of the verb at vpos: the words after the previous verb's object"""
        prevs=[p for p,_ in vs if p<vpos]
        lo=0
        if prevs:
            lo=prevs[-1]+1
            # skip the previous verb's object up to a conjunction
            cj=[q for q in range(lo,vpos) if toks[q].low in ('and','but',',','then','while')]
            if not cj:return default
            lo=cj[-1]+1
        seg=[x for x in toks[lo:vpos] if x.kind!='punct']
        if not seg or any(x.kind=='num' for x in seg):return default
        h=s.holder(seg)
        return h or default
    def mention(s,toks,k,vs,csubj,span,total_words,unknown=False):
        m=None if unknown else toks[k].num
        before=[x.low for x in toks[:k] if x.kind=='word']
        prev=before[-1] if before else ''
        money=k>0 and toks[k-1].kind=='money'
        np=s.np_after(toks,k)
        noun,adj=np['noun'],np['adj']
        if money:
            if noun is not None and noun not in ('dollar','bill'):adj=(noun,)+adj
            noun='dollar'
        elif noun in ('buck',):noun='dollar'
        endi=np['ofend'] or np['end']
        nxt_num=next((q for q in range(endi,len(toks)) if toks[q].kind=='num'),len(toks))
        after=[x.low for x in toks[endi:nxt_num] if x.kind=='word']
        vpos,mood=s.verb_for(toks,vs,k)
        verb=toks[vpos].low if vpos is not None else None
        own=s.subject_of(toks,vs,vpos,csubj) if vpos is not None else csubj
        # 'one' as a determiner or pronoun ("one neighbor brought", "the first one") is not an amount
        if m is not None and m.raw.lower() in ('one',) and (vpos is None or prev in DET|V('first|second|third|last|which|each|every')|{'the'} or np['noun'] is None):return
        if noun in GROUPS and np['of'] and np['of'] not in adj:adj=tuple(adj)+(np['of'],)
        f=Frame(m=m,noun=noun,adj=adj,of=np['of'],ofadj=np.get('ofadj',()),owner=own,verb=verb,mood=mood,span=span,before=before,after=after,
                total=total_words,cmp=np['cmp'],money=money,raw=m.raw if m is not None else 'some')
        if noun is None and after[:1]==['of']:
            ofn=[w for w in after[1:5] if w not in DET and w not in ('her','his','their','my','our','your')]
            if ofn and ofn[0] not in ('them','those','these','it') and ofn[0] not in NOT_NOUN:f['noun']=sing(ofn[0]);noun=f['noun']
        if f.noun is None:
            if after[:2] in (['of','them'],['of','those'],['of','these']):f['noun']=s.last_noun
            elif own in s.noun_of:f['noun']=s.noun_of[own]
            elif s.last_noun:f['noun']=s.last_noun
            f['implicit']=True
        if f.noun and not money:
            s.last_noun=f.noun
            if own:s.noun_of[own]=f.noun
        if mood=='intent' or verb in V('calls|requires|required|require'):
            f['kind']='intent'
            if verb in GOAL and (verb not in INTENT or verb in V('needs|need|needed')):f['goal']=True
            s.frames.append(f);return
        win=' '.join(after[:7])
        # comparison: N more/fewer things than X ; N years older than X ; N times as many as X
        cw=np['cmp'] or next((w for w in after[:3] if w in COMPARATIVE),None)
        if cw and 'than' in after[:8]:
            other=s._after_word(toks,endi,'than')
            f.update(kind='compare',sign=+1 if cw in ('more','older','taller','longer','heavier','bigger','farther','further','higher','faster','wider','deeper') else -1,other=other,cword=cw)
            s.frames.append(f);return
        if m is not None and m.raw.lower() in ('twice','double','triple','thrice','half') and after[:1]==['as'] or after[:1]==['times'] or prev in ('times',) or (noun=='time' and after[:1] in (['as'],['more'],['longer'])):
            other=None
            if 'as' in after:
                idx=[i for i,w in enumerate(after) if w=='as']
                if len(idx)>=2:other=s._after_word(toks,endi,'as',nth=2)
            elif 'than' in after:other=s._after_word(toks,endi,'than')
            f.update(kind='times',other=other);s.frames.append(f);return
        # rates: "(sold) in packages of 6" (the number counts the things in one package)
        if prev=='of' and len(before)>=2 and sing(before[-2]) in GROUPS and (len(before)<3 or before[-3] in ('in','of','into','by')) or (prev=='of' and len(before)>=2 and sing(before[-2]) in GROUPS and verb in V('come|comes|came|sold|sell|sells|packed|bought|purchased')):
            content=s.holder([x for x in toks[:vpos] if x.kind=='word']) if vpos is not None else None
            if content and content not in PRON and content not in s.people:
                f.update(kind='rate',noun=content,per=sing(before[-2]),implicit=False);s.frames.append(f);return
        # rates
        r=re.match(r'(?:\w+\s+){0,2}?(?:in|on|for|to|into|inside|with|from)\s+(?:each|every)\s+(?:one\s+of\s+)?(?:the\s+|his\s+|her\s+|their\s+)?(\w+)|(?:\w+\s+){0,1}?per\s+(\w+)|(?:\w+\s+){0,1}?(?:each|every)\s+(\w+)|(each|apiece)\b|(?:\w+\s+){0,1}?an?\s+(day|week|month|year|hour|minute|second|night|game|book|box|bag)\b',win)
        if r:
            g=next((x for x in r.groups() if x),None)
            g=None if g in ('each','apiece') else sing(g)
            f.update(kind='rate',per=g);s.frames.append(f);return
        bk=[i for i,w in enumerate(before) if w in ('each','every')]
        if bk and ((len(before)-bk[-1])<=8 or (bk[-1]==0 and not any(x.kind=='num' for x in toks[:k]))):
            ph=[]
            seg=before[bk[-1]+1:]
            if seg[:2]==['of','the'] or seg[:2]==['of','his'] or seg[:2]==['of','her'] or seg[:2]==['of','their']:seg=seg[2:]
            elif seg[:1]==['of']:seg=seg[1:]
            for w in seg:
                if w in NOT_NOUN or w in MODS or verbish(w) or w in OTHER_VERBS or w in ('composed','made','filled','consists','will','can'):break
                ph.append(w)
            grp=sing(ph[-1]) if ph else None
            f.update(kind='rate',per=grp);s.frames.append(f);return
        if f.noun in ('dollar','cent') and prev in ('for','at') and verb in V('bought|buys|buy|purchased|purchases|purchase|ordered|orders|order|got|gets|rented|rents|rent'):
            f.update(kind='change',sign=-1,item=s._obj_before(toks,k),spend=True);s.frames.append(f);return
        if verb in COST or (verb in BE and money and prev not in ('of',)) or (money and prev in ('for','at') and verb in GAIN|LOSE):
            item=s.holder([x for x in toks[:vpos] if x.kind=='word' and x.low not in ('if','that','which')]) if verb in COST|BE and vpos is not None else (s._obj_before(toks,k) if money else None)
            f.update(kind='price',item=item);s.frames.append(f);return
        if vpos is None:
            tw=[x for x in toks[k+1:] if x.kind=='word']
            vafters=[x.low for i,x in enumerate(tw) if (x.low in JOIN|LEAVE|LOSE|GAIN|BE|HAVE|COST|OTHER_VERBS) and not (i and tw[i-1].low=='to')]
            if np['cmp']=='more' and any(x.low in ('start','starts','started','begin','begins','began') for x in tw[:3]):vafters=['came']
            vafter=vafters[0] if vafters else None
            if len([v for v in vafters if v in JOIN|LEAVE|LOSE|GAIN|OTHER_VERBS and v not in BE])>1:
                f.update(kind='bare');s.frames.append(f);return
            ws_after=[x.low for x in toks[k+1:] if x.kind=='word']
            pas=next((i for i,w in enumerate(ws_after[:-1]) if w in ('were','was','are','is','got') and ws_after[i+1] in LOSE|GAIN|V('taken|eaten|added|thrown|given')),None)
            if pas is not None:
                pv=ws_after[pas+1]
                minus=pv in LOSE|V('taken|eaten|thrown|given') and not (pv in ('added','put','placed'))
                place=None
                for i,w in enumerate(ws_after):
                    if w in ('from','to','into','in','on','onto') and i+1<len(ws_after):
                        rest=[x for x in ws_after[i+1:] if x not in DET]
                        if rest:place=sing(rest[0]);break
                f.update(kind='change',sign=-1 if minus else +1,verb=pv,owner=place or s._holder_of(f.noun),other=None,subjnum=True,passive=True);s.frames.append(f);return
            if vafter in ('returned','returns','return','came back'):vafter='came'
            if vafter in JOIN|LEAVE|V('died|broke|melted|popped|fell|escaped|wilted|burst|sank|hatched') and vafter not in BE|HAVE:
                sign=+1 if vafter in JOIN|GAIN else -1
                place=s._place(toks) or s._holder_of(f.noun)
                f.update(kind='change',sign=sign,verb=vafter,owner=place,other=None,subjnum=True);s.frames.append(f);return
            if 'there' in before or vafter in BE|HAVE:
                f.update(kind='state',owner=s._place(toks) or s._holder_of(f.noun) or ('there' if 'there' in before else None),subjnum=True);s.frames.append(f);return
            f.update(kind='bare');s.frames.append(f);return
        if verb in BE and 'there' in before:
            f.update(kind='state',owner=s._place(toks) or s._holder_of(f.noun) or 'there');s.frames.append(f);return
        if verb in HAVE:
            f.update(kind='state',left=('left' in after[:2]));s.frames.append(f);return
        if verb in BE:
            if f.noun in UNITS and after[:1] and after[0] in V('long|tall|high|deep|wide|old|heavy|thick|away'):
                f.update(kind='state',measure=after[0]);s.frames.append(f);return
            f.update(kind='be');s.frames.append(f);return
        if verb in TRANSFER:
            other=None;away=('away' in before[-2:]) or ('away' in after[:1]) or ('out' in after[:1] and verb in ('gave','give','gives','handed','passed'))
            ws=[x for x in toks[endi:] if x.kind=='word']
            for q,x in enumerate(ws[:6]):
                if x.low in ('to','with') and q+1<len(ws):
                    other=s.holder(ws[q+1:q+4]);break
            if other is None and not away and vpos is not None:
                io=[x for x in toks[vpos+1:k] if x.kind=='word' and x.low not in ('away','back','out')]
                if io:other=s.holder(io)
            f.update(kind='change',sign=-1,other=other,away=away);s.frames.append(f);return
        if verb in JOIN:f.update(kind='change',sign=+1);s.frames.append(f);return
        if verb in LEAVE and verb not in ('left',):f.update(kind='change',sign=-1);s.frames.append(f);return
        if verb=='left' and 'left' not in after[:1]:f.update(kind='change',sign=-1);s.frames.append(f);return
        if verb in LOSE:f.update(kind='change',sign=-1);s.frames.append(f);return
        if verb in V('finished|completed|did|solved|answered|done') and (after[:2] in (['of','them'],['of','those'],['of','these']) or f.implicit) and own and any(g.owner==own and g.noun==f.noun and g.kind=='state' for g in s.frames):
            f.update(kind='change',sign=-1);s.frames.append(f);return
        if verb in V('filled|fills|fill') and 'with' in before[-2:] and not any(g.owner==own and g.noun==f.noun for g in s.frames):
            f.update(kind='state');s.frames.append(f);return
        if after[:2] in (['of','them'],['of','those'],['of','these'],['of','it']) and verb not in LOSE and verb not in TRANSFER:
            f.update(kind='bare');s.frames.append(f);return
        if verb in V('put|puts|placed|places|stored|stores'):
            if not any(g.owner==own and g.noun==f.noun for g in s.frames):f.update(kind='state')
            else:f.update(kind='bare')
            s.frames.append(f);return
        if verb in GAIN:
            frm=None
            if 'from' in after[:4]:frm=s._after_word(toks,endi,'from')
            f.update(kind='change',sign=+1,other=frm);s.frames.append(f);return
        if verb in V('scored|scores|score') and f.noun not in V('point|goal|run|basket|touchdown|mark|grade|percent'):
            f.update(kind='change',sign=+1,other=None);s.frames.append(f);return
        if verb in ACT:f.update(kind='act');s.frames.append(f);return
        f.update(kind='unknown');s.frames.append(f)
    def _after_word(s,toks,start,word,nth=1):
        ws=[x for x in toks[start:] if x.kind=='word']
        idx=[i for i,x in enumerate(ws) if x.low==word]
        if len(idx)<nth:return None
        rest=ws[idx[nth-1]+1:]
        cut=[]
        for x in rest:
            if x.low in ('did','does','do','has','have','had','is','are','was','were','and','but','in','on','at','for','to'):break
            cut.append(x)
        if not cut:return None
        if len(cut)==1 and cut[0].low in ('he','she','him','her','they','them'):return s.resolve(cut[0].low)
        return s.holder(cut)
    def _obj_before(s,toks,k):
        ws=[x for x in toks[:k] if x.kind=='word' and x.low not in ('for','at','a','an','the')]
        for x in reversed(ws):
            if x.low not in NOT_NOUN and not verbish(x.low):return sing(x.low)
        return None
    def _place(s,toks):
        ws=[x for x in toks if x.kind=='word']
        for i,w in enumerate(ws):
            if w.low in ('in','on','at','inside') and i+1<len(ws):
                rest=[x for x in ws[i+1:] if x.low not in DET]
                rest=[x for x in rest if x.low not in MODS]
                if rest and rest[0].low not in NOT_NOUN:
                    # "on the soccer field" -> field (the last noun of the phrase)
                    ph=[]
                    for x in rest:
                        if x.low in NOT_NOUN or verbish(x.low):break
                        ph.append(x.low)
                    return sing(ph[-1]) if ph else sing(rest[0].low)
        return None
    def _holder_of(s,noun):
        hs=[f.owner for f in s.frames if f.noun==noun and f.kind=='state']
        return hs[-1] if hs else None

def self_starts(st,toks,k):return st.starts_clause(toks,k)

# ----------------------------------------------------------------------------- the question
class Ask(dict):
    __getattr__=dict.get

QSTOP=AUX|PRON|V('than|in|on|at|of|to|for|from|there|did|does|do|are|were|is|was|will|would|can|could|has|have|had|left|altogether|total|each|per|every|now|in|all|by','combined|together|still|remain|remaining')
def parse_question(st,a,b):
    q=st.t[a:b];toks=tokens(st.t,a,b,st.nums)
    low=' '.join(x.low if x.kind!='num' else '#' for x in toks if x.kind in ('word','num'))
    m=re.search(r'\bhow (many|much)\b(.*)$',low)
    ask=Ask(text=q,low=low,qframes=[])
    mm=re.search(r'\bhow (long|far|tall|high|deep|old|heavy|wide|big)\b(.*)$',low)
    gm=re.search(r'\bwhat (?:is|was|will be) the (greatest|largest|least|smallest|lowest) (?:possible )?(number|length|amount|size)\b(.*)$',low)
    am=re.search(r'\bwhat amount of (money|\w+)\b(.*)$',low)
    if not m and mm:
        ask.update(measure=mm.group(1),much=True,kind='amount');rest=mm.group(2).split()
        m=True
    elif not m and gm:
        ask.update(extreme=gm.group(1),much=False,kind='amount');rest=(gm.group(2)+' '+gm.group(3)).split()
        if rest and rest[0] in ('number','amount') and len(rest)>1 and rest[1]=='of':rest=rest[2:]
        m=True
    elif not m and am:
        ask.update(much=True,kind='amount');rest=(am.group(1)+' '+am.group(2)).split();m=True
    if m is True:pass
    elif not m:
        m2=re.search(r'\b(?:what is|what was|what will be|find)\s+(?:the\s+)?(total|number|sum|cost|price|value|amount|difference|total number|total cost|total value)\s+of\s+(.*)$',low)
        if not m2:no('QUESTION_FORM')
        ask['much']=m2.group(1) in ('cost','price','value','total cost','total value')
        rest=m2.group(2).split();ask['total']=m2.group(1).startswith('total') or m2.group(1)=='sum'
        if m2.group(1)=='difference':no('QUESTION_DIFFERENCE')
    elif m is not True:
        ask['much']=m.group(1)=='much';rest=m.group(2).split()
    i=0;ws=[]
    if rest and rest[0] in ('more','fewer','less'):ask['cmp']=rest[0];i=1
    while i<len(rest) and rest[i] not in QSTOP and rest[i] not in PREP and rest[i]!='#' and not (verbish(rest[i]) or rest[i] in OTHER_VERBS or rest[i] in INTENT) \
          and (i==(1 if ask.cmp else 0) or not any(st.is_name(x) for x in toks if x.low==rest[i])):
        ws.append(rest[i]);i+=1
    ws=[w for w in ws if w not in MODS]
    if ws and ws[0] in ('money','cash'):ask['noun']='dollar'
    elif ws:
        ask['noun']=sing(ws[-1]);ask['adj']=tuple(ws[:-1])
        if i<len(rest) and rest[i]=='of':
            k=i+1;w2=[]
            while k<len(rest) and rest[k] not in QSTOP and rest[k]!='#':w2.append(rest[k]);k+=1
            w2=[w for w in w2 if w not in MODS]
            if w2:ask['of']=sing(w2[-1]);ask['ofadj']=tuple(w2[:-1])
    if ask.much and not ask.noun:
        if re.search(r'\b(?:money|cost|costs|spend|spent|pay|paid|earn|earned|save|saved|change|price|worth|charge|charged|owe|make|made|collect|collected|raise|raised)\b',low):ask['noun']='dollar'
    if re.search(r'\b(?:at first|in the beginning|to (?:begin|start) with|originally|at the start|in the start|initially)\b',low):ask['when']='initial'
    elif re.search(r'\b(?:left|now|remain|remaining|still|in the end|end up|ended up|after that|then)\b',low):ask['when']='now'
    if re.search(r'\b(?:in all|altogether|in total|total|together|combined|all together|both|in both)\b',low):ask['total']=True
    if ask.cmp and 'than' in low.split():ask['kind']='diff'
    elif ask.cmp:ask['kind']='more'
    elif re.search(r'\b(?:each|per|every|apiece)\b',low) and not ask.total:ask['kind']='each'
    else:ask['kind']='amount'
    if re.search(r'\b(?:need|needs|needed|have to|has to|must|should)\b',low):ask['need']=True
    # who
    owner=None
    for x in toks:
        if x.kind!='word' or x.low=='how':continue
        if x.low in ('his','her','their') :
            nxt=[y for y in toks if y.s>x.s and y.kind=='word'][:2]
            if nxt and nxt[0].low in KIN:owner=st.resolve(x.low)+"'s "+sing(nxt[0].low);break
            continue
        if x.low in ('he','she','they','him','them'):owner=st.resolve(x.low);break
        if st.is_name(x) and sing(x.low)!=ask.noun:
            if x.low.endswith("'s"):
                nxt=[y for y in toks if y.s>x.s and y.kind=='word'][:1]
                if nxt and nxt[0].low in KIN:owner=st.person(x.w)+"'s "+sing(nxt[0].low);break
            owner=st.person(x.w);break
        if x.low in ('i','we','you'):owner=x.low;break
    ask['owner']=owner
    tm=re.search(r'\bthan\s+(?:the\s+|his\s+|her\s+|their\s+)?(\w+)(?:\s+(\w+))?',low)
    if tm:
        w=tm.group(1);cap=next((x for x in st.people if x.lower()==w),None)
        if cap:ask['than']=cap
        elif w in ('he','she','him','her','they','them'):ask['than']=st.resolve(w)
        elif tm.group(2) and sing(tm.group(2))==ask.noun or w in COLORS:ask['than_kind']=w
        elif w in KIN and tm.group(0).split()[1] in ('his','her','their'):ask['than']=st.resolve(tm.group(0).split()[1])+"'s "+sing(w)
        else:ask['than']=sing(w)
    qn=[x for x in toks if st.is_name(x) and sing(x.low)!=ask.noun]
    if len(qn)>=2 and re.search(r'\band\b',low):ask['owners']=[st.person(x.w) for x in qn]
    ask['have']=bool(re.search(r'\b(?:have|has|had)\b',low))
    pm=re.search(r'\b(?:in|on|at|inside) (?:the |a |an |his |her |their |my |our )?(\w+(?: \w+)?)\s*(?:now|left|altogether|in all|\?|$)',low)
    if pm:
        w=pm.group(1).split()[-1]
        if w not in NOT_NOUN and w!='#':ask['place']=sing(w)
    qv=None
    for x in toks:
        if x.kind=='word' and (x.low in GAIN|LOSE|ACT|JOIN|LEAVE|TRANSFER|COST) and x.low not in HAVE|BE|V('do|does|did|need|needs'):
            if x.low=='left' and (ask.when=='now'):continue
            qv=x.low;break
    ask['verb']=qv
    if re.search(r'\b(?:other|others|rest|else|remainder)\b',low):ask['rest']=True
    body=st.t[:a].lower()
    ok=V('how|many|much|more|fewer|less|than|of|the|a|an|there|now|left|in|all|altogether|total|together|combined|at|first|to|start|begin|with',
         'originally|beginning|end|still|then|after|that|have|has|had|do|does|did|is|are|was|were|will|would|can|could|be|been|get|got|on|by|for|from',
         'both|each|every|per|one|his|her|their|its|my|our|your|them|they|he|she|it|i|we|you|him|me|us|money|cash|initially|remain|remaining|need',
         'needs|needed|this|time|number|amount|buy|cost|costs|spend|spent|pay|paid|away|out|up|back|off|home|what|find|value|sum|total|make|made',
         'end|ended|up|together|altogether|so|far|right|over|does|dollars|dollar|cents|cent|money|worth|price|change|earn|earned|save|saved|owe',
         'totaled|totalled|total|can|could|may|might|able|already|also|currently|now|anymore|any|more|just|exactly|old|tall|long|high|deep|heavy|wide|big|is|be',
         'greatest|least|largest|smallest|most|fewest|possible|number|amount')
    bodyw=set(re.findall(r"[a-z]+",body));bodyfam={fam(w) for w in bodyw}|{fam(lemma(w)) for w in bodyw}|{lemma(w) for w in bodyw}|{lemma(w)+'e' for w in bodyw}
    res=[w for w in re.findall(r"[a-z]+(?:'[a-z]+)?",low) if w not in ok and w not in bodyw and sing(w) not in {sing(x) for x in bodyw} and fam(w) not in bodyfam
         and lemma(w) not in bodyfam and fam(lemma(w)) not in bodyfam and (lemma(w)+'e') not in bodyfam and not any(x.low==w and st.is_name(x) for x in toks)]
    nounw={ask.noun,ask.of}|set(ask.adj or ())|set(ask.ofadj or ())
    res=[w for w in res if sing(w) not in nounw and w not in nounw]
    if res:ask['residue']=res
    # numbers in the question: "in 3 days", "do 8 bees have", "to have 43 cats", "2 ice cream cones cost"
    for k,x in enumerate(toks):
        if x.kind!='num':continue
        np=st.np_after(toks,k)
        bw=[y.low for y in toks[:k] if y.kind=='word']
        ask['qframes'].append(Frame(m=x.num,noun=np['noun'],adj=np['adj'],of=np['of'],prev=bw[-1] if bw else '',prev2=bw[-2] if len(bw)>1 else '',span=q.strip()))
    return ask

# ----------------------------------------------------------------------------- plans
class Plan:
    def __init__(s,st,name):
        s.st=st;s.name=name;s.qs={};s.facts=[];s.used=set();s.money=None;s.cpd=None;s.gain_start=False
    def to_money(s,q,frm,to,span):
        if frm==to:return q
        if s.cpd is None:
            s.cpd=s.new('cents_per_dollar','cent/dollar',integer=True);s.facts.append({'eq':f'{s.cpd} = 100','known':'100 cents in a dollar'})
        out=s.new(q+'_in_'+to,to,integer=False)
        s.rel(f'{out} = {q} / {s.cpd}' if to=='dollar' else f'{out} = {q} * {s.cpd}',span)
        return out
    def new(s,base,unit,integer=True,about=''):
        base=re.sub(r'[^a-z0-9_]','_',str(base).lower()).strip('_') or 'q'
        if base[0].isdigit():base='q_'+base
        name=base;k=1
        while name in s.qs:k+=1;name=f'{base}_{k}'
        s.qs[name]={'name':name,'unit':unit,'integer':integer,'signed':False,'about':about};return name
    def bind(s,f,base,unit=None,integer=None):
        noun=f.noun or 'thing'
        unit=unit or noun
        if integer is None:integer=f.m.value.denominator==1 and noun not in UNITS and noun!='dollar' and '/' not in unit
        name=s.new(base,unit,integer=integer)
        s.facts.append({'eq':f'{name} = {lit(f.m.value)}','span':f.span});s.used.add(f.m.start);return name
    def rel(s,eq,span):s.facts.append({'eq':eq,'span':span})

def _adj_ok(have,want):
    return not want or set(want)<=set(have or ())

def holding_frames(st,owner,noun,adj):
    out=[]
    for f in st.frames:
        if f.kind not in ('state','change') or f.noun!=noun:continue
        mine=f.owner==owner;theirs=f.kind=='change' and f.other==owner
        if not (mine or theirs):continue
        if adj and not _adj_ok(f.adj,adj):
            if f.adj:continue
            others=[g for g in st.frames if g.kind=='state' and g.noun==noun and g.owner==owner and g.adj and not _adj_ok(g.adj,adj)]
            if others:no('AMBIGUOUS_KIND')
        if f.total:no('TOTAL_IN_HOLDING')
        out.append(f)
    return out

def timeline(p,owner,noun,adj=(),unit=None):
    """(start, last) quantities of the holding of noun by owner"""
    unit=unit or noun;cur=None;start=None
    if noun in ('dollar','cent'):
        fs=[f for g in ('dollar','cent') for f in holding_frames(p.st,owner,g,adj)]
        fs.sort(key=lambda f:p.st.frames.index(f))
        if any(f.noun!=noun for f in fs):p.money=noun
    else:fs=holding_frames(p.st,owner,noun,adj)
    def bm(f,base):
        if noun in ('dollar','cent') and f.noun in ('dollar','cent') and f.noun!=noun:
            q=p.bind(f,base+'_'+f.noun,f.noun,integer=False);return p.to_money(q,f.noun,noun,f.span)
        return p.bind(f,base,unit)
    for f in fs:
        mine=f.owner==owner
        if f.kind=='state':
            if not mine:continue
            if cur is None:
                cur=bm(f,f'{owner}_{noun}') if f.m is not None else p.new(f'{owner}_{noun}_start',unit,about='unknown start')
                start=cur
            else:
                if f.m is None:no('UNKNOWN_LATER_STATE')
                if any(g.kind=='state' and g.owner==owner and g.noun==noun and g.span==f.span and g is not f for g in fs[:fs.index(f)]):no('LIST_OF_KINDS')
                v=bm(f,f'{owner}_{noun}_stated');p.rel(f'{cur} = {v}',f.span)
            f['_q']=cur;continue
        if cur is None:
            if mine and f.sign>0 and not f.passive and _source_free(p.st,f) and f.kind=='change' and fam(f.verb) not in ('get','receive','join','come','arrive'):
                start=cur=bm(f,f'{fam(f.verb)}_{noun}') if f.m is not None else p.new(f'{fam(f.verb)}_{noun}',unit,about='unknown start')
                f['_q']=cur;p.gain_start=True;continue
            no('CHANGE_BEFORE_STATE')
        sign=f.sign if mine else -f.sign
        d=bm(f,f'{fam(f.verb)}_{noun}') if f.m is not None else p.new(f'{fam(f.verb)}_{noun}',unit,about='unknown change')
        f['_q']=d
        nxt=p.new(f'{owner}_{noun}',unit)
        p.rel(f"{nxt} = {cur} {'+' if sign>0 else '-'} {d}",f.span);cur=nxt
    return start,cur

def has_holding(st,owner,noun,adj=()):
    if any(f.kind=='state' and f.owner==owner and f.noun==noun and _adj_ok(f.adj,adj) for f in st.frames):return True
    first=next((f for f in st.frames if f.kind in ('state','change') and f.noun==noun and (f.owner==owner or f.other==owner) and _adj_ok(f.adj,adj)),None)
    return bool(first and first.kind=='change' and first.owner==owner and first.sign>0 and not first.passive and _source_free(st,first) and fam(first.verb) not in ('get','receive','join','come','arrive'))

def _source_free(st,f):
    """the gain comes from nobody, or from a place that holds nothing in the story"""
    return f.other is None or not any(g.owner==f.other or (g.other==f.other and g is not f) for g in st.frames)

def events(st,verb,noun,adj,owner):
    v=fam(verb)
    return [f for f in st.frames if f.kind in ('change','act') and fam(f.verb)==v and f.noun==noun and _adj_ok(f.adj,adj)
            and (owner is None or f.owner in (owner,'they') or f.other==owner)]

MEASURE={'long':'second|minute|hour|day|week|month|year|inch|foot|yard|mile|meter|centimeter|kilometer|millimeter','far':'inch|foot|yard|mile|meter|centimeter|kilometer|block|step',
         'tall':'inch|foot|yard|meter|centimeter|story','high':'inch|foot|yard|meter|centimeter|mile','deep':'inch|foot|yard|meter|centimeter','old':'year|month|week|day',
         'heavy':'pound|ounce|gram|kilogram|ton','wide':'inch|foot|yard|meter|centimeter','big':'square'}
def asked_noun(st,ask):
    if ask.measure and ask.measure!='big':
        ok=set(MEASURE[ask.measure].split('|'))
        cand={f.noun for f in st.frames if f.m is not None and f.noun in ok}
        return next(iter(cand)) if len(cand)==1 else None
    noun=ask.noun
    if ask.of and noun in ('piece','slice','box','bag','cup','glass','bottle','can','sheet','loaf','bar','pack','kind','type','bunch','pound','ounce','gallon','liter'):
        if not any(f.noun==noun for f in st.frames) and any(f.noun==ask.of or f.of==ask.of for f in st.frames):noun=ask.of
    if noun is None:
        cand={f.noun for f in st.frames if f.noun and f.kind in ('state','change','act') and (ask.owner is None or f.owner==ask.owner)}
        if len(cand)==1:noun=next(iter(cand))
    if noun=='money':noun='dollar'
    if noun and not any(f.noun==noun for f in st.frames):
        mem=members(noun)
        if mem and mem!='*':
            held={f.noun for f in st.frames if f.m is not None and f.noun in mem}
            if len(held)==1 and all(f.noun in held or f.noun in ('dollar','cent') for f in st.frames if f.m is not None):noun=next(iter(held))
    return noun

# ---- schema: holding --------------------------------------------------------
def schema_holding(st,ask):
    if ask.qframes or ask.kind not in ('amount','more') or ask.rest or ask.residue or any(f.kind in ('rate','price','compare','times') for f in st.frames):return None
    noun=asked_noun(st,ask)
    if noun is None:return None
    adj=ask.adj or ();owner=ask.owner;p=Plan(st,'holding');fr=st.frames
    if ask.kind=='more':
        # "How many more did she find?" -> the unknown amount of that event
        if not ask.verb or ask.need:return None
        hits=events(st,ask.verb,noun,adj,owner)
        if len(hits)!=1 or hits[0].m is not None:return None
        f=hits[0];timeline(p,f.owner if f.owner!='they' else owner,noun,adj)
        if '_q' not in f:return None
        return p,f['_q'],noun
    if ask.verb and fam(ask.verb) not in ('have','left'):
        hits=events(st,ask.verb,noun,adj,owner)
        if not hits:return _between_states(st,ask,noun,adj,p)
        if any(f.total for f in hits):return None
        if ask.total or len(hits)>1:
            if any(f.m is None for f in hits):return None
            names=[p.bind(f,f'{fam(f.verb)}_{noun}',noun) for f in hits]
            if len(names)==1:return p,names[0],noun
            t=p.new(f'{fam(ask.verb)}_total',noun);p.rel(f"{t} = {' + '.join(names)}",ask.text);return p,t,noun
        f=hits[0]
        if f.m is not None:
            if f.kind=='act' or not has_holding(st,f.owner,noun,adj):return p,p.bind(f,f'{fam(f.verb)}_{noun}',noun),noun
            return p,p.bind(f,f'{fam(f.verb)}_{noun}',noun),noun
        timeline(p,f.owner,noun,adj)
        if '_q' not in f:return None
        return p,f['_q'],noun
    holders=[]
    for f in fr:
        if f.kind=='state' and f.noun==noun and _adj_ok(f.adj,adj) and f.owner not in holders:holders.append(f.owner)
    if owner is None:
        if ask.place and ask.place in holders:owner=ask.place
        elif len(holders)==1:owner=holders[0]
        elif ask.total and holders:
            parts=[]
            for h in holders:
                start,cur=timeline(p,h,noun,adj)
                parts.append(start if ask.when=='initial' else cur)
            t=p.new(f'total_{noun}',noun);p.rel(f"{t} = {' + '.join(parts)}",ask.text);return p,t,noun
        else:return None
    if ask.owners:
        if not all(has_holding(st,o,noun,adj) for o in ask.owners):
            acts=[f for f in fr if f.kind in ('change','act') and f.owner in ask.owners and f.noun==noun]
            if not acts or any(f.m is None or (f.kind=='change' and f.sign<0) for f in acts) or len({f.owner for f in acts})!=len(ask.owners):return None
            if any(f.kind=='state' and f.noun==noun and f.owner in ask.owners for f in fr):return None
            names=[p.bind(f,f'{fam(f.verb)}_{noun}',noun) for f in acts]
        else:names=[timeline(p,o,noun,adj)[1] for o in ask.owners]
        t=p.new(f'total_{noun}',noun);p.rel(f"{t} = {' + '.join(names)}",ask.text);return p,t,noun
    if owner=='they':
        if not ask.total:return None
        hs=[h for h in holders if h not in ('there',None)]
        if len(hs)<2:return None
        parts=[timeline(p,h,noun,adj)[1] for h in hs]
        t=p.new(f'total_{noun}',noun);p.rel(f"{t} = {' + '.join(parts)}",ask.text);return p,t,noun
    if ask.total and not adj:
        kinds=[]
        for f in fr:
            if f.kind=='state' and f.owner==owner and f.noun==noun and f.adj not in kinds:kinds.append(f.adj)
        if len(kinds)>1:
            parts=[timeline(p,owner,noun,k)[1] for k in kinds]
            t=p.new(f'total_{noun}',noun);p.rel(f"{t} = {' + '.join(parts)}",ask.text);return p,t,noun
    if not has_holding(st,owner,noun,adj):
        # "How many apples did he pick in all" over acts / gains without a starting amount
        gains=[f for f in fr if f.kind in ('change','act') and f.owner==owner and f.noun==noun and f.sign!=-1 and _adj_ok(f.adj,adj)]
        if ask.total and gains and all(f.m is not None for f in gains) and not [f for f in fr if f.kind=='change' and f.owner==owner and f.noun==noun and f.sign==-1]:
            names=[p.bind(f,f'{fam(f.verb)}_{noun}',noun) for f in gains]
            if len(names)==1:return p,names[0],noun
            t=p.new(f'total_{noun}',noun);p.rel(f"{t} = {' + '.join(names)}",ask.text);return p,t,noun
        return None
    start,cur=timeline(p,owner,noun,adj)
    if p.gain_start and ask.when=='initial' and not ask.verb:return None
    return p,(start if ask.when=='initial' else cur),noun

DOWN=V('spend|spent|use|used|eat|ate|sell|sold|give|gave|lose|lost|cut|cuts|drink|drank|pay|paid|donate|donated|throw|threw|remove|removed')
UP=V('grow|grew|get|got|earn|earned|find|found|buy|bought|collect|collected|save|saved|receive|received|add|added|gain|gained|make|made|pick|picked')
def _between_states(st,ask,noun,adj,p):
    """the asked event is not stated, but one holding is stated twice (before and after): the event is the difference"""
    v=ask.verb.lower();sign=-1 if (v in DOWN or fam(v) in DOWN) else (+1 if (v in UP or fam(v) in UP) else None)
    if sign is None:return None
    sts=[f for f in st.frames if f.kind=='state' and f.noun==noun and _adj_ok(f.adj,adj) and f.m is not None]
    if len(sts)!=2 or sts[0].owner!=sts[1].owner or sts[0].span==sts[1].span:return None
    if any(f.kind!='state' for f in st.frames if f.m is not None):return None
    if ask.owner not in (sts[0].owner,None) and has_holding(st,ask.owner,noun):return None
    a=p.bind(sts[0],f'{noun}_before',noun);b=p.bind(sts[1],f'{noun}_after',noun)
    d=p.new(f'{fam(v)}_{noun}',noun,integer=sts[0].m.value.denominator==1 and sts[1].m.value.denominator==1 and noun not in UNITS)
    p.rel(f"{b} = {a} {'+' if sign>0 else '-'} {d}",sts[1].span);return p,d,noun

# ---- schema: compare --------------------------------------------------------
def schema_compare(st,ask):
    """X = Y +- N, X = Y x N as equations: any of the holders may be the asked one"""
    cmps=[f for f in st.frames if f.kind in ('compare','times')]
    if not cmps or ask.qframes or ask.residue or ask.rest or ask.need:return None
    if any(f.kind in ('rate','price','intent','unknown','bare','be') for f in st.frames):return None
    noun=asked_noun(st,ask);adj=ask.adj or ()
    if noun is None:return None
    p=Plan(st,'compare');qty={}
    def q(owner):
        if owner not in qty:
            if has_holding(st,owner,noun,adj):qty[owner]=timeline(p,owner,noun,adj)[1]
            else:qty[owner]=p.new(f'{owner}_{noun}',noun)
        return qty[owner]
    for f in cmps:
        if f.noun not in (noun,None) and not f.implicit:return None
        a,b=f.owner,f.other
        if not a or not b or a==b or a in ('it','there') or b in ('it','there'):no('COMPARE_PARTIES')
        if f.kind=='compare':
            d=p.bind(f,'difference',noun)
            p.rel(f"{q(a)} = {q(b)} {'+' if f.sign>0 else '-'} {d}",f.span)
        else:
            d=p.bind(f,'factor','1',integer=False)
            p.rel(f'{q(a)} = {q(b)} * {d}',f.span)
    for f in st.frames:
        if f.kind=='state' and f.noun==noun and f.owner not in qty and f.m is not None:q(f.owner)
    if ask.kind=='amount':
        owners=ask.owners or ([o for o in qty] if (ask.total or ask.owner=='they') else None)
        if owners:
            if any(o not in qty for o in owners) or len(owners)<2:return None
            t=p.new(f'total_{noun}',noun);p.rel(f"{t} = {' + '.join(qty[o] for o in owners)}",ask.text);return p,t,noun
        if ask.owner not in qty:return None
        return p,qty[ask.owner],noun
    if ask.kind=='diff':
        a,b=ask.owner,ask.than
        if a not in qty or b not in qty:return None
        t=p.new(f'difference_{noun}',noun)
        p.rel(f'{t} = {qty[a]} - {qty[b]}' if ask.cmp=='more' else f'{t} = {qty[b]} - {qty[a]}',ask.text);return p,t,noun
    return None

# ---- schema: difference of two holdings or two event totals --------------------
def schema_diff(st,ask):
    if ask.kind not in ('diff','more') or ask.qframes or ask.need or ask.residue or ask.rest:return None
    if any(f.kind in ('rate','price','compare','times','intent','unknown','bare','be') for f in st.frames):return None
    noun=asked_noun(st,ask)
    if noun is None:return None
    adj=ask.adj or ();p=Plan(st,'diff')
    a=ask.owner;b=ask.than
    def amount(owner,kinds=None):
        k=kinds if kinds is not None else adj
        if has_holding(st,owner,noun,k):return timeline(p,owner,noun,k)[1]
        acts=[f for f in st.frames if f.kind in ('change','act') and f.owner==owner and f.noun==noun and _adj_ok(f.adj,k) and (not ask.verb or fam(f.verb)==fam(ask.verb))]
        if acts and all(f.m is not None for f in acts) and all(f.kind=='act' or f.sign>0 for f in acts):
            names=[p.bind(f,f'{fam(f.verb)}_{noun}',noun) for f in acts]
            if len(names)==1:return names[0]
            t=p.new(f'{owner}_{noun}_total',noun);p.rel(f"{t} = {' + '.join(names)}",acts[0].span);return t
        return None
    # than + a kind: "how many more red marbles than blue marbles"
    if ask.than_kind:
        o=a or (st.people[0] if len(st.people)==1 else None)
        x=amount(o,(ask.adj or ()));y=amount(o,(ask.than_kind,))
        if x is None or y is None:return None
    else:
        if a is None:return None
        if b is None:
            others=[]
            for f in st.frames:
                if f.noun==noun and f.owner not in (a,None,'there') and f.owner not in others and f.kind in ('state','change','act'):others.append(f.owner)
            if len(others)!=1:return None
            b=others[0]
        if ask.kind=='more' and ask.verb is None and not ask.than and not ask.have:return None
        x=amount(a);y=amount(b)
        if x is None or y is None:return None
    t=p.new(f'difference_{noun}',noun)
    p.rel(f'{t} = {x} - {y}' if ask.cmp=='more' else f'{t} = {y} - {x}',ask.text)
    return p,t,noun

# ---- schema: category total (pupils = girls + boys) ----------------------------
CATEGORY={
 'child':'boy|girl|kid|student|son|daughter|baby|toddler|teen','kid':'boy|girl|child|student','student':'boy|girl|kid|child|pupil|grader|freshman|sophomore',
 'pupil':'boy|girl|kid|child|student','person':'man|woman|boy|girl|child|adult|kid|teacher|student|parent|player|guest|visitor|member|worker|lady|gentleman|senior|teen|baby',
 'people':'man|woman|boy|girl|child|adult|kid|teacher|student|parent|player|guest|visitor|member|worker|lady|gentleman|senior|teen|baby',
 'animal':'dog|cat|cow|pig|horse|sheep|goat|chicken|duck|goose|rabbit|bird|fish|lion|tiger|bear|monkey|elephant|giraffe|zebra|snake|frog|turtle|mouse|rat|hamster|deer|fox|wolf|owl|eagle|penguin|seal|whale|dolphin|shark|cat|kitten|puppy|calf|lamb|pony|donkey|turkey|parrot|squirrel|raccoon|bat|camel|kangaroo|panda|alligator|crocodile|lizard|bee|ant|butterfly|spider|insect|bug',
 'pet':'dog|cat|fish|bird|hamster|rabbit|turtle|parrot|puppy|kitten|goldfish|mouse|snake|lizard|guinea',
 'bird':'chicken|duck|goose|turkey|parrot|robin|sparrow|pigeon|eagle|owl|crow|swan|hen|rooster|penguin|hawk|cardinal|bluejay|dove|seagull|flamingo|peacock|canary',
 'fowl':'chicken|duck|goose|turkey|hen|rooster|quail','poultry':'chicken|duck|goose|turkey|hen|rooster',
 'fruit':'apple|orange|banana|pear|peach|plum|grape|cherry|strawberry|mango|lemon|lime|watermelon|melon|kiwi|pineapple|apricot|blueberry|raspberry|papaya|tangerine|coconut|fig|avocado|cantaloupe|grapefruit',
 'vegetable':'carrot|potato|tomato|onion|pepper|cucumber|lettuce|cabbage|broccoli|corn|pea|bean|spinach|pumpkin|squash|zucchini|eggplant|radish|celery|beet|garlic|cauliflower|turnip',
 'flower':'rose|tulip|daisy|lily|sunflower|orchid|carnation|daffodil|violet|iris|marigold|peony|lilac|poppy|dandelion|lotus|jasmine|hyacinth|chrysanthemum',
 'vehicle':'car|truck|bus|bike|bicycle|motorcycle|van|tricycle|motorbike|scooter|taxi|jeep|tractor|train|boat|plane|airplane|helicopter',
 'coin':'penny|nickel|dime|quarter','reading material':'magazine|newspaper|book|comic|novel|brochure',
 'material':'magazine|newspaper|book|comic|novel|brochure|bottle|can|paper|plastic|glass|cardboard',
 'litter':'bottle|can|wrapper|bag|paper|cup|straw|carton','dessert':'cake|pie|cookie|brownie|cupcake|pudding|muffin|tart|donut|doughnut',
 'treat':'candy|cookie|chocolate|cupcake|gum|lollipop|brownie|cake|pie|muffin|donut|doughnut|bar|candie|chewing',
 'drink':'juice|soda|milk|water|tea|coffee|lemonade','beverage':'juice|soda|milk|water|tea|coffee|lemonade',
 'toy':'car|doll|ball|robot|truck|puzzle|block|teddy|bear|train|kite|yoyo|top|marble|game','clothing':'shirt|pant|dress|skirt|sock|shoe|hat|jacket|coat|sweater|scarf|glove|t-shirt|jean|short',
 'sport':'soccer|football|baseball|basketball|tennis|volleyball|hockey|golf','instrument':'guitar|piano|drum|violin|flute|trumpet|harp|cello|saxophone|clarinet',
 'tree':'oak|maple|pine|palm|birch|willow|cedar|elm|spruce|fir|redwood|cherry|apple|orange|peach|lemon','shape':'circle|square|triangle|rectangle|oval|star|hexagon|pentagon',
 'fish':'pike|sturgeon|herring|salmon|trout|tuna|bass|cod|catfish|goldfish|carp|perch|snapper|minnow|guppy|swordfish|halibut|mackerel|sardine',
 'reptile':'snake|alligator|lizard|turtle|crocodile|iguana|gecko|tortoise|chameleon',
 'item':'*','thing':'*','object':'*','piece':'*','total':'*'}
def members(cat):
    c=CATEGORY.get(cat);return None if c is None else ('*' if c=='*' else set(c.split('|')))

def schema_category(st,ask):
    if ask.kind!='amount' or ask.qframes or ask.need or ask.residue or ask.rest or ask.when=='initial':return None
    noun=ask.noun
    if noun is None or any(f.noun==noun for f in st.frames if f.m is not None):return None
    mem=members(noun) or members(ask.of or '')
    if mem is None:return None
    if any(f.kind not in ('state','change','act') for f in st.frames if f.m is not None) or st.vague:return None
    fr=[f for f in st.frames if f.m is not None]
    if not fr or any(f.implicit or f.noun is None for f in fr):return None
    if mem!='*' and any(f.noun not in mem and not any(w in mem for w in (f.adj or ())) for f in fr):return None
    if len({f.noun for f in fr})<1:return None
    owner=ask.owner;v=fam(ask.verb) if ask.verb else None
    if owner not in (None,'they') and any(f.owner not in (owner,) for f in fr):return None
    if any(f.kind=='change' and f.sign<0 for f in fr):return None
    if v and any(fam(f.verb)!=v for f in fr if f.kind!='state'):return None
    if v is None and any(f.kind!='state' for f in fr):return None
    p=Plan(st,'category');names=[p.bind(f,f'{f.noun}s',noun) for f in fr]
    if len(names)==1:return p,names[0],noun
    t=p.new(f'total_{noun}',noun);p.rel(f"{t} = {' + '.join(names)}",ask.text);return p,t,noun

def st_unit(noun):return noun or 'thing'

def operand(p,st,noun,owner=None,exclude=()):
    """the amount of a thing as one quantity: a holding over time, a sum of gains or acts, or a single number"""
    fs=[f for f in st.frames if f.noun==noun and f.kind in ('state','change','act') and f not in exclude]
    if not fs:return None
    hs=[o for o in dict.fromkeys(f.owner for f in fs) if o is not None and has_holding(st,o,noun)]
    if owner is not None:hs=[o for o in hs if o==owner]
    sts=[f for f in fs if f.kind=='state']
    if len(sts)>=2 and len(sts)==len(fs) and len({f.owner for f in sts})==1 and len({f.span for f in sts})==1 and all(f.m is not None for f in sts) and len({f.adj for f in sts})==len(sts):
        names=[p.bind(f,f'{noun}s',noun) for f in sts];t=p.new(f'{noun}_sum',noun);p.rel(f"{t} = {' + '.join(names)}",sts[0].span);return t
    if len(hs)==1 and all(f.owner==hs[0] or f.other==hs[0] for f in fs):return timeline(p,hs[0],noun)[1]
    if len(fs)==1 and fs[0].m is not None and fs[0].kind!='change' or (len(fs)==1 and fs[0].m is not None and fs[0].sign>0):
        return p.bind(fs[0],f'{noun}s',noun)
    if len(fs)>1 and all(f.kind in ('act','change') and (f.kind=='act' or f.sign>0) and f.m is not None for f in fs) and len({f.owner for f in fs})==1:
        names=[p.bind(f,f'{noun}s',noun) for f in fs];t=p.new(f'{noun}_sum',noun);p.rel(f"{t} = {' + '.join(names)}",fs[0].span);return t
    return None

# ---- schema: groups (multiplication) -----------------------------------------
def schema_groups(st,ask):
    if ask.kind not in ('amount',) or ask.cmp or ask.need or ask.residue or ask.rest:return None
    noun=asked_noun(st,ask)
    if noun is None:return None
    rates=[f for f in st.frames if f.kind=='rate']
    if len(rates)!=1:return None
    r=rates[0]
    content=r.of if r.of and r.noun in ('piece','slice','bag','box','pack','cup','sheet','bottle','can') else r.noun
    if noun not in (r.noun,r.of,content) and not (ask.of in (r.noun,r.of)):return None
    if any(f.kind in ('price','compare','times','intent','unknown','bare','be') for f in st.frames):return None
    g=r.per
    p=Plan(st,'groups')
    # the number of groups: a frame in the story, or a number in the question ("in 3 days", "do 8 bees have")
    cands=[f for f in st.frames if f is not r and f.m is not None and f.kind in ('state','change','act') and g and f.noun==g]
    qc=[x for x in ask.qframes if g and (x.noun==g or (x.noun and x.noun.endswith(g)))]
    if qc and not cands and len(ask.qframes)==1:
        cnt=qc[0]
        gq=p.bind(cnt,f'{g}s',g)
    elif len(cands)==1 and not ask.qframes:
        gq=p.bind(cands[0],f'{g}s',g)
    elif len(cands)>1 and not ask.qframes and g:
        gq=operand(p,st,g,ask.owner)
        if gq is None:return None
    elif r.per is None and len([f for f in st.frames if f.m is not None])==2:
        # "Chris gave his 35 friends 12 pieces of candy each": the other number counts the receivers in the same clause
        other=[f for f in st.frames if f is not r and f.m is not None]
        if len(other)!=1 or other[0].span!=r.span or other[0].noun not in PERSONS:return None
        g=other[0].noun;gq=p.bind(other[0],f'{g}s',g)
    else:return None
    rq=p.bind(r,f'{noun}_per_{g}',f'{noun}/{g}',integer=False)
    t=p.new(f'{noun}_total',noun);p.rel(f'{t} = {gq} * {rq}',r.span)
    # loose things of the same noun held besides the groups: "She also has 6 extra crayons"
    extra=[f for f in st.frames if f.kind=='state' and f.m is not None and f.noun==noun and f is not r and f.m.start not in p.used]
    if extra:
        if len(extra)!=1 or not re.search(r'\b(?:also|extra|loose|besides|in addition)\b',extra[0].span.lower()):return None
        e=p.bind(extra[0],f'loose_{noun}',noun);t2=p.new(f'{noun}_all',noun);p.rel(f'{t2} = {t} + {e}',extra[0].span);t=t2
    return p,t,noun

# ---- schema: share (division) -------------------------------------------------
def schema_share(st,ask):
    noun=asked_noun(st,ask)
    if noun is None:return None
    fr=[f for f in st.frames if f.m is not None]
    if any(f.kind in ('price','compare','times','unknown','be') for f in st.frames):return None
    p=Plan(st,'share')
    low=ask.low
    # "how many will each get" / "how many in each box": total of noun, number of groups
    if ask.kind=='each':
        mg=re.search(r'\b(?:each|every|per)\s+(?:of\s+)?(?:the\s+|his\s+|her\s+|their\s+)?(\w+)',low)
        g=sing(mg.group(1)) if mg and mg.group(1) not in ('one','other') else None
        people=g in ('person','people','one') or g in PERSONS
        tots=[f for f in fr if f.kind in ('state','change','intent') and f.noun==noun]
        grp=[f for f in fr if f not in tots and f.kind in ('state','change','bare','intent','act') and f.noun and
             ((g and (f.noun==g or f.noun.endswith(g))) or (people and f.noun in PERSONS))]
        qg=[x for x in ask.qframes if g and x.noun==g]
        if len(tots)!=1:return None
        if qg and not grp:cnt=qg[0]
        elif len(grp)==1 and not ask.qframes:cnt=grp[0]
        else:return None
        if not re.search(r'\b(?:equal|equally|evenly|same|each|every|per|divided|split|shared|share|among|organized|group|groups)\b',(st.t).lower()):return None
        tq=p.bind(tots[0],f'{noun}_total',noun);gq=p.bind(cnt,'groups',cnt.noun or 'group')
        per=p.new(f'{noun}_per_group',f'{noun}/{cnt.noun or "group"}',integer=False)
        p.rel(f'{tq} = {per} * {gq}',ask.text)
        if re.search(r'\b(?:left|remain|remaining|over|full)\b',low):return None
        p.qs[per]['integer']=noun not in UNITS and noun not in ('dollar','cent')
        return p,per,noun
    # "how many boxes / days / trips": total of the content, rate per group
    if any(f.kind=='intent' for f in st.frames):return None
    rates=[f for f in fr if f.kind=='rate']
    if len(rates)==1 and ask.kind=='amount':
        r=rates[0];g=r.per
        if noun!=g and not (g is None and noun in GROUPS):return None
        content=r.noun
        tots=[f for f in fr if f is not r and f.kind in ('state','change','act','bare') and f.noun in (content,r.of)]
        qt=[x for x in ask.qframes if x.noun in (content,r.of)]
        if len(tots)+len(qt)==1 and len(fr)+len(ask.qframes)==2:
            tot=tots[0] if tots else qt[0]
            tq=p.bind(tot,f'{content}_total',content)
        elif len(tots)>1 and not qt and not any(f.kind=='bare' for f in tots):
            tq=operand(p,st,content,ask.owner)
            if tq is None:return None
        else:return None
        rq=p.bind(r,f'{content}_per_{noun}',f'{content}/{noun}',integer=False)
        exact=p.new(f'{noun}_exact',noun,integer=False);p.rel(f'{exact} = {tq} / {rq}',r.span)
        if re.search(r'\b(?:left|left over|remain|remaining)\b',low):return None
        if re.search(r'\b(?:need|needed|needs|required|enough|all of|to hold all|to finish|to pack all|to carry all|take|use)\b',low):
            n=p.new(noun,noun);p.rel(f'{n} = ceil({exact})',ask.text);return p,n,noun
        if re.search(r'\b(?:full|complete|completely|whole|can he|can she|can they|can i|can we|could|can you)\b',low):
            n=p.new(noun,noun);p.rel(f'{n} = floor({exact})',ask.text);return p,n,noun
        p.qs[exact]['integer']=True;return p,exact,noun
    return None

# ---- schema: price ------------------------------------------------------------
def schema_price(st,ask):
    prices=[f for f in st.frames if f.kind=='price' or (f.kind=='rate' and f.noun in ('dollar','cent'))]
    if len(prices)!=1:return None
    if any(f.kind in ('compare','times','intent','unknown','be','bare') for f in st.frames):return None
    p=Plan(st,'price');fr=[f for f in st.frames if f.m is not None]
    pr=prices[0];item=pr.item if pr.kind=='price' else (pr.per or pr.item)
    money=pr.noun if pr.noun in ('dollar','cent') else 'dollar'
    low=ask.low
    if (ask.much or ask.noun in ('dollar','cent')) and ask.kind=='amount':
        # total cost = number x price
        cnts=[f for f in fr if f is not pr and f.noun not in ('dollar','cent') and (item is None or f.noun==item or (f.noun and item and f.noun.endswith(item)))]
        qc=[x for x in ask.qframes if item is None or x.noun==item or (x.noun and item and x.noun.endswith(item))]
        if len(cnts)+len(qc)!=1 or len(fr)+len(ask.qframes)!=2:return None
        c=cnts[0] if cnts else qc[0]
        unit_item=item or c.noun or 'item'
        pq=p.bind(pr,f'price_per_{unit_item}',f'{money}/{unit_item}',integer=False)
        cq=p.bind(c,f'{unit_item}s',unit_item)
        t=p.new('cost',money,integer=False);p.rel(f'{t} = {cq} * {pq}',pr.span);return p,t,money
    noun=asked_noun(st,ask)
    if noun and item and (noun==item or noun.endswith(item) or item.endswith(noun)) and ask.kind=='amount' and re.search(r'\b(?:can|could|afford|buy|purchase|get)\b',low):
        # how many things a budget buys: floor(money / price)
        budget=[f for f in fr if f is not pr and f.noun==money]
        qb=[x for x in ask.qframes if x.noun==money or (x.m and st.t[max(0,x.m.start-1):x.m.start]=='$')]
        if len(budget)+len(qb)!=1 or len(fr)+len(ask.qframes)!=2:return None
        bq=p.bind(budget[0] if budget else qb[0],'budget',money,integer=False)
        pq=p.bind(pr,f'price_per_{item}',f'{money}/{item}',integer=False)
        n=p.new(f'{item}s',item);p.rel(f'{n} = floor({bq} / {pq})',ask.text);return p,n,noun
    return None

# ---- schema: need ----------------------------------------------------------------
def schema_need(st,ask):
    if not ask.need or ask.kind not in ('more','amount'):return None
    noun=asked_noun(st,ask)
    if noun is None:return None
    adj=tuple(ask.adj or ())+((ask.of,) if ask.of and noun in GROUPS else ())
    fr=[f for f in st.frames if f.m is not None]
    owner=ask.owner or (st.people[0] if len(st.people)==1 else None)
    p=Plan(st,'need')
    qt=[x for x in ask.qframes if x.noun in (noun,None) and x.prev in ('have','get','reach','make','buy','collect','save','own')]
    if len(qt)==1 and len(ask.qframes)==1:
        if any(f.kind not in ('state','change') for f in fr):return None
        if owner is None or not has_holding(st,owner,noun):return None
        cur=timeline(p,owner,noun)[1]
        goal=p.bind(qt[0],f'goal_{noun}',noun)
        n=p.new(f'needed_{noun}',noun);p.rel(f'{n} = {goal} - {cur}',ask.text);return p,n,noun
    if ask.qframes:return None
    if noun in ('dollar','cent'):
        goals=[f for f in fr if f.kind=='price']
    else:
        goals=[f for f in fr if f.kind=='intent' and f.goal and f.noun==noun and _adj_ok(f.adj,adj)]
    if len(goals)!=1:return None
    g=goals[0]
    if owner is None:return None
    if any(f.kind not in ('state','change','intent','price') for f in fr):return None
    if noun in ('dollar','cent'):
        if not has_holding(st,owner,noun):return None
        cur=timeline(p,owner,noun)[1]
    else:
        hs=[f for f in fr if f is not g and f.noun==noun and _adj_ok(f.adj,adj) and f.kind in ('state','change') and f.owner in (owner,None) and (f.kind=='state' or f.sign>0)]
        if len(hs)!=1:return None
        cur=p.bind(hs[0],f'have_{noun}',noun)
    gq=p.bind(g,f'goal_{noun}',noun if noun not in ('dollar','cent') else g.noun,integer=False)
    n=p.new(f'needed_{noun}',noun,integer=False);p.rel(f'{n} = {gq} - {cur}',ask.text);return p,n,noun

# ---- schema: change from a payment -----------------------------------------------
def schema_change(st,ask):
    if not re.search(r'\bchange\b',ask.low) or not ask.much:return None
    fr=[f for f in st.frames if f.m is not None]
    prices=[f for f in fr if f.kind=='price' or f.spend]
    pays=[f for f in fr if f.kind=='change' and f.sign<0 and not f.spend and f.noun in ('dollar','cent') and fam(f.verb) in ('give','pay','hand')]
    if len(prices)!=1 or len(pays)!=1 or len(fr)!=2 or prices[0].noun!=pays[0].noun:return None
    p=Plan(st,'change');u=prices[0].noun
    c=p.bind(prices[0],'cost',u,integer=False);g=p.bind(pays[0],'paid',u,integer=False)
    n=p.new('change',u,integer=False);p.rel(f'{n} = {g} - {c}',ask.text);return p,n,u

# ---- schema: greatest common divisor / least common multiple ---------------------
def schema_gcd_lcm(st,ask):
    t=st.t.lower();low=ask.low
    fr=[f for f in st.frames if f.m is not None]
    nums=[n for n in st.nums if not N.optional(n) or n.value!=1]
    if len(nums)<2 or len(nums)>4 or ask.qframes or len(fr)!=len(nums):return None
    if any(n.value.denominator!=1 or n.kind not in ('digits','word') for n in nums):return None
    units=[f.noun in UNITS for f in fr]
    if any(units) and (not all(units) or len({f.noun for f in fr})>1):return None
    g=ask.extreme in ('greatest','largest') or re.search(r'\bgreatest\b|\blargest\b|\bmost\b',low)
    l=ask.extreme in ('least','smallest','lowest') or re.search(r'\bleast\b|\bsmallest\b|\bfewest\b',low)
    p=Plan(st,'gcd_lcm')
    if g and re.search(r'identical|same combination|same number|no \w+(?: \w+)? left over|without any \w+(?: \w+)? left|nobody left out|no \w+ left|left over|leftover|evenly|equally|all of the same length|same length',t):
        if re.search(r'\bratio|\bpercent|%|\btimes\b|\bmore than\b|\bfewer\b',t):return None
        names=[p.bind(f,f'count_{i}','item') for i,f in enumerate(fr)]
        expr=names[0]
        for n in names[1:]:expr=f'gcd({expr}, {n})'
        r=p.new('greatest_common','item');p.rel(f'{r} = {expr}',ask.text);return p,r,ask.noun or 'item'
    if l and (re.search(r'same number of|divisible by|multiple of|both',t)) and (re.search(r'packs? of|packages? of|comes? in|sold \w+ to a|divisible by|boxes of|bags of|multiple',t)):
        if ask.noun in ('package','pack','box','bag','packet','case'):return None
        names=[p.bind(f,f'size_{i}','item') for i,f in enumerate(fr)]
        expr=names[0]
        for n in names[1:]:expr=f'lcm({expr}, {n})'
        r=p.new('least_common','item');p.rel(f'{r} = {expr}',ask.text);return p,r,ask.noun or 'item'
    return None

SCHEMAS=[schema_gcd_lcm,schema_change,schema_holding,schema_compare,schema_diff,schema_category,schema_groups,schema_share,schema_price,schema_need]

# ----------------------------------------------------------------------------- read
def read(text):
    try:return _read(text)
    except NoRead as e:return {'spec':None,'reason':'EN:'+str(e)}

def _read(text):
    st=Story(text);t=text
    sents=sentences(t)
    if not sents:no('NO_SENTENCES')
    qi=[i for i,(a,b) in enumerate(sents) if '?' in t[a:b] or re.match(r'\s*(?:How|Find|What)\b',t[a:b])]
    if not qi:no('NO_QUESTION')
    if qi[-1]!=len(sents)-1:no('QUESTION_NOT_LAST')
    for i,(a,b) in enumerate(sents[:-1]):st.body(a,b)
    a,b=sents[-1]
    m=re.search(r',\s*(?=(?:how|what)\b)',t[a:b],re.I)
    if m:
        cond=t[a:a+m.start()]
        cm=re.match(r'\s*(?:If|When|After|Since|Given that|Suppose|Now that)\s+',cond)
        st.body(a+(cm.end() if cm else 0),a+m.start());a=a+m.end()
    else:
        m2=re.search(r'\s+(?:if|when|after)\s+(?=[^?]*\d)',t[a:b],re.I)
        if m2 and re.match(r'\s*(?:How|What)\b',t[a:b]):
            st.body(a+m2.end(),b);b=a+m2.start()
    if re.search(r'\bpattern\b|\bsequence\b|\bconsecutive\b',t,re.I):no('PATTERN')
    ask=parse_question(st,a,b)
    if st.vague and any(v.noun in (ask.noun,ask.of) for v in st.vague):no('VAGUE_EVENT')
    results=[]
    errors=[]
    for sch in SCHEMAS:
        try:r=sch(st,ask)
        except NoRead as e:errors.append(str(e));continue
        if r is None:continue
        plan,target,noun=r
        try:results.append(finish(st,plan,target,noun,ask))
        except NoRead as e:errors.append(sch.__name__+':'+str(e))
    if not results:no(errors[0] if errors else 'NO_SCHEMA')
    if len(results)>1:
        from .solve import solve as _solve
        vals=set()
        for r in results:
            s=_solve(r['spec'])
            vals.add(s.get('answer') if s.get('ok') else ('fail',s.get('reason')))
        if len(vals)!=1:no('SCHEMAS_DISAGREE')
    return results[0]

def finish(st,p,target,noun,ask):
    unused=[]
    linked={x for f in st.frames for x in (f.per,f.of,f.other,f.item) if x}
    for f in st.frames:
        if f.m is None or f.m.start in p.used or N.optional(f.m):continue
        why=_irrelevant(st,f,noun,ask,linked)
        if why is None:no('UNUSED:'+f.kind+':'+f.m.raw)
        unused.append({'raw':f.m.raw,'why':why})
    for x in ask.qframes:
        if x.m.start not in p.used and not N.optional(x.m):no('UNUSED_QUESTION_NUMBER:'+x.m.raw)
    out_pos={f.m.start for f in st.frames if f.m is not None and f.m.start not in p.used and not N.optional(f.m)}
    for n in st.nums:
        if n.start in p.used or N.optional(n) or n.start in out_pos:continue
        no('UNREAD_NUMBER:'+n.raw)
    spec={'schema':'tukuyo.g4.fpl/1','lang':'en','text':st.t,'quantities':list(p.qs.values()),'facts':p.facts,'ask':target,
          'answer_unit':noun or '','unused':unused,'reader':'tukuyo.g4.reader_en/3:'+p.name}
    return {'spec':spec}

def _irrelevant(st,f,noun,ask,linked):
    """why a number may stay out of the reading, or None"""
    if f.kind not in ('state','change','act') or f.implicit or f.noun is None:return None
    if f.subjnum or f.total or f.noun in OTHER_VERBS or f.noun in NOT_NOUN or f.noun in TIME_UNITS:return None
    if f.kind in ('change','act') and not (f.noun==noun and ask.adj and f.adj):
        # an event may stay out only when its thing is held by someone in a stated amount and is not the asked thing
        if not any(g.kind=='state' and g.noun==f.noun and g.m is not None for g in st.frames):return None
    if any(g.kind in ('rate','price','compare','times') for g in st.frames):return None
    for sp in {g.span for g in st.frames}|{ask.text}:
        if f.noun in {sing(w) for w in re.findall(r"[a-z]+",sp.lower())} and re.search(r'\b(?:each|every|per|apiece|equal|equally|evenly|share|shared|shares|divide|divided|split|rest|remaining|others?|total|in all|altogether|together|times|than)\b',sp.lower()):return None
    if f.noun in linked:return None
    if f.noun==noun:
        # the same thing, but a different kind that the question excludes (salty vs sweet cookies)
        if ask.adj and f.adj and not set(f.adj)&set(ask.adj) and (f.owner==ask.owner or ask.owner is None):return f'{" ".join(f.adj)} {f.noun}, the question asks about {" ".join(ask.adj)} {noun}'
        return None
    if f.noun in {sing(w) for w in re.findall(r"[a-z]+",ask.low)}:return None
    return f'about {f.noun}, not about {noun}'

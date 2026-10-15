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
HAVE=V('has|have|had|owns|own|owned|holds|hold|held|keeps|keep|kept|contains|contain|contained|stores|stored|having|carries|carried|carry|includes|include|included')
BE=V('is|are|was|were|be|been|being')
GAIN=V('put|puts|placed|places|stored|stores|got|gets|get|received|receives|receive|found|finds|find|bought|buys|buy|picked|picks|pick|collected|collects|collect|won|wins|win',
       'uploaded|uploads|upload|downloaded|downloads|download|printed|prints|print',
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
BUY=V('bought|buys|buy|purchased|purchases|purchase|ordered|orders|order|rented|rents|rent')
AWAY=V('blew|flew|ran|rolled|floated|drifted|washed|swam|walked|wandered|hopped|crawled|sailed|drove|went')
LINKV=V('having|containing|holding|carrying|with|filled|stuffed')     # 'N boxes, each having M things'
GONE=V('die|dies|died|break|breaks|melt|melts|pop|pops|fall|falls|escape|escapes|wilt|wilts|burst|bursts|sink|sinks|disappear|disappears|disappeared|rot|rots|rotted|spoil|spoils|spoiled')
GOAL=V('calls|call|called|requires|require|required|needs|need|needed|asks|wants|want|wanted')
INTENT=V('wants|want|wanted|needs|need|needed|plans|plan|planned|hopes|hope|hoped|wishes|wish|wished|tries|try|tried|likes|like|would|will|going|should|must|might')
PRON={'he','she','they','him','her','them','it','i','we','you','me','us','his','their','its','my','our','your','hers','theirs'}
DET=V('the|a|an|his|her|their|its|my|our|your|this|that|these|those|some|each|every|all|both|any|another|other|one|several|many|few|most|no')
PREP=V('of|for|in|on|at|to|from|with|by|per|into|onto|than|about|after|before|during|over|under|around|between|among|through|across|off|out|up|down|away|back|along|inside|outside|near|behind|until|since|without|apiece|within')
CONJ=V('and|or|but|then|so|because|if|when|while|though|although|which|who|that|where')
QWORD=V('how|what|which|who|whom|whose|why|when|where|find')
MODS=V('more|fewer|less|extra|additional|other|different|total|left|remaining|whole|full|empty|same|equal|whole|entire|own')
# size and age words tell one kind of a thing from another, as colours do ('7 big apples and 3 small apples'); they were
# dropped with the words above until the fusion limits round. A question about one of them must find it in the story
KIND_MODS=V('new|old|small|large|big|little')
AUX=V('will|would|can|could|should|shall|may|might|must|does|did|do|has|have|had|is|are|was|were|been|be|to|not')
NOT_NOUN=AUX|PRON|DET|PREP|CONJ|QWORD|HAVE|BE|V('more|fewer|less|left|now|then|total|all|altogether|together|each|every|per|times|as|much|many|same|equal|equally|only|just|also|already|still|again|later|today|yesterday|tomorrow|some|rest|remaining|first|last|next|there|here|out|away|up|down|back|in|on|off|over|twice|half|double|triple|evenly|exactly|about|around|almost|nearly|than|very|too|so')
GROUPS=V('box|bag|pack|package|packet|bottle|can|jar|bunch|basket|case|carton|set|pair|row|column|group|team|shelf|tray|crate|container|plate|bowl|cup|stack|pile|roll|bundle|batch|load|page|book|sheet|bar|stick|loaf|dozen|section|table|car|bus|van|truck|boat|class|tank|bin|drawer|aisle|floor|level|layer|tier|vase|pot|cage|pen|room|building|house|tent|herd|flock|train|ship|plane|round|game|day|week|month|year|hour|minute|second|time|trip|lap|session|night|morning|tray|bucket|jug|pan|batch|serving|bouquet|wall|street|block|tree|branch|plant|garden|pizza|pie|cake|bucket|album|folder|binder|envelope|drawer|cabinet|truckload|cartload')
UNITS=V('mile|kilometer|meter|centimeter|millimeter|foot|inch|yard|pound|ounce|kilogram|gram|liter|milliliter|gallon|quart|pint|cup|hour|minute|second|day|week|month|year|dollar|cent|degree|point|ton|acre|lap')
TIME_UNITS=V('second|minute|hour|day|week|month|year|night|morning|afternoon|evening|weekend')
# words that say there is an amount without saying how much. Before the review round only 'some' and 'several' were read
# as an amount not known (an outside review of r7: 'Anna has a few apples. She buys 4 more apples. How many apples now?'
# was answered 4, as were 'a couple of', 'many', 'a lot of', 'a bag of ...' and a plural with no number)
VAGUE_Q=V('some|several|many|numerous|few|various|countless')
VAGUE_OF=V('lot|lots|plenty|number|handful|couple|pile|piles|stack|stacks|heap|heaps|dozens|hundreds|thousands|loads|tons|bit|amount|quantity')
MASS=V('money|cash|water|milk|juice|flour|sugar|rice|sand|paint|oil|salt|butter|tea|coffee|soup|food|gas|fuel')
_PRONOUN_OF=('them','those','these','it')
def vague_amounts(toks):
    """the positions at which an amount is said without a number: 'some apples', 'a few apples', 'many of them', 'a lot
    of marbles' and 'a bag of oranges' (at 'of': the oranges in it are not counted), 'a little money'. Story.mention reads
    the amount there as not known"""
    out=[]
    for q,x in enumerate(toks):
        lw=x.low;nx=toks[q+1].low if q+1<len(toks) else '';prev=toks[q-1].low if q else ''
        if prev in ('as','how','so','too') and lw in ('many','few'):continue      # 'twice as many apples as': a comparison
        pron=q+2<len(toks) and nx=='of' and toks[q+2].low in _PRONOUN_OF
        if lw in VAGUE_Q:out.append(q)
        elif lw=='little' and prev=='a' and nx in MASS:out.append(q)
        elif lw in VAGUE_OF and nx=='of':
            # 'a number of books' is an amount not given; 'the number of houses' is the number itself
            if lw in ('number','couple','bit','amount','quantity') and prev not in ('a','an','large','small','great','big','good'):continue
            out.append(q if pron else q+1)
        elif sing(lw) in GROUPS and nx=='of' and prev in ('a','an','one','the','his','her','their','its','my','our','your') \
             and q+2<len(toks) and toks[q+2].kind=='word' and toks[q+2].low not in NOT_NOUN and sing(toks[q+2].low)!=toks[q+2].low:
            out.append(q+1)                        # 'a bag of oranges' (not 'a bag of garbage', 'one pack of gum')
    return out
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
class Ambiguous(Exception):
    """a pronoun that may stand for more than one person named before it"""
    def __init__(s,pos,pronoun,cands,topic):super().__init__('PRONOUN_AMBIGUOUS');s.pos=pos;s.pronoun=pronoun;s.cands=cands;s.topic=topic
HE=('he','him','his','himself');SHE=('she','her','hers','herself')

# ----------------------------------------------------------------------------- tokens
ABBR=re.compile(r'(?:\bMrs?|\bMs|\bDr|\bSt|\bJr|\bSr|\bvs|\betc|\bNo|\d\s*(?:ft|in|lbs?|oz))\.$')
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
        s.t=t;s.nums=N.find(t);s.frames=[];s.people=[];s.last_owner=None;s.last_noun=None;s.noun_of={};s.vague=[];s.seen_nouns=[];s.last_thing=None;s.last_adj=()
        s.subj_hist=[]   # (position, person): the people who were the subjects of clauses, in order
        s.forced={}      # pronoun position -> person, for one reading among several (see read)
        s.resolved=[]    # (position, pronoun, person) for every he/she/him/her read
        s.first_pos={}   # where each person is first named: a pronoun can only stand for someone named before it
        s.text_low=t.lower()
    # ---- names and pronouns
    def is_name(s,tk,first=False):
        if tk.kind!='word' or not tk.w[:1].isupper():return False
        w=tk.w[:-2] if tk.low.endswith("'s") else tk.w
        if w in CAP_STOP or w.lower() in NOT_NOUN or w.lower() in KIN:return False
        if w.lower() in GROUPS|UNITS or sing(w.lower()) in s.seen_nouns:return False
        return True
    def person(s,w,pos=None):
        w=w[:-2] if w.lower().endswith("'s") else w
        if w not in s.people:s.people.append(w)
        if pos is not None and pos<s.first_pos.get(w,len(s.t)+1):s.first_pos[w]=pos
        return w
    def resolve(s,p,exclude=None,at=None):
        """the person a pronoun stands for. TUKUYO does not guess anyone's gender: with two or more people, he/she/him/her
        is read only when one person is left after removing the clause's own subject (exclude); otherwise there is no
        reading. ('Charlie has 31 more snowballs than Lucy. She has 50 snowballs.' was read with She = Charlie, the
        subject so far, and answered 50; 'Tom gave Sue 4 apples. She had 10 apples before.' likewise.)"""
        p=p.lower()
        if p in ('i','me','my','we','us','our','you','your'):return {'me':'i','my':'i','us':'we','our':'we','your':'you'}.get(p,p)
        if p in ('they','them','their'):
            if not s.people and s.last_owner and s.last_owner not in ('there',):return s.last_owner
            return 'they'
        if p in ('it','its'):return s.last_thing or 'it'
        if not s.people:return s.last_owner if s.last_owner and s.last_owner not in ('there',) else (p if p in ('he','she') else 'they')
        cands=[x for x in s.people if x!=exclude and (at is None or s.first_pos.get(x,-1)<at)]
        if not cands:no('PRONOUN')
        if len(cands)==1:who=cands[0]
        elif at is None:no('PRONOUN_AMBIGUOUS')
        elif at in s.forced:
            who=s.forced[at]
            if who not in cands:no('PRONOUN_FORCED')
        else:
            topic=next((x for q,x in reversed(s.subj_hist) if q<at and x in cands),None)
            raise Ambiguous(at,p,cands,topic)
        if at is not None and (at,p,who) not in s.resolved:s.resolved.append((at,p,who))
        return who
    def holder(s,toks,exclude=None):
        """a holder named by a short phrase: Tom / he / Tom's mom / his sister / the store"""
        ws=[x for x in toks if x.kind=='word']
        if not ws:return None
        if len(ws)>2 and ws[0].low in PREP and ws[-1].low in ('he','she','i','we','you','they'):
            # 'For his birthday he got 12 more': the subject is the one after the opening phrase
            return s.resolve(ws[-1].low,None,at=ws[-1].s)
        for i,x in enumerate(ws):
            if x.low in ('he','she','i','we','you','they','it','him','them','me','us'):return s.resolve(x.low,exclude if x.low in ('him','them','me','us') else None,at=x.s)
            if x.low=='her' and (i+1==len(ws) or ws[i+1].low in NOT_NOUN):return s.resolve('her',exclude,at=x.s)
            if x.low in ('his','her','their','my','our','your') and i+1<len(ws):
                rest=[y.low for y in ws[i+1:] if y.low not in DET and y.low not in MODS]
                if rest:return s.resolve(x.low,at=x.s)+"'s "+sing(rest[-1])
            if s.is_name(x):
                if x.low.endswith("'s"):
                    rest=[y.low for y in ws[i+1:] if y.low not in DET]
                    if rest:return s.person(x.w,x.s)+"'s "+sing(rest[-1])
                    return s.person(x.w,x.s)
                return s.person(x.w,x.s)
        nouns=[x for x in ws if x.low not in NOT_NOUN and x.low not in MODS]
        if nouns and any(x.low in ('another','other') for x in ws[:ws.index(nouns[-1])]):
            return 'other '+sing(nouns[-1].low)        # 'Another bag weighs 900 g': not the bag named before
        return sing(nouns[-1].low) if nouns else None
    # ---- noun phrases
    def np_after(s,toks,i):
        """noun phrase after token i -> dict(noun, adj, end, of, ofend, cmp)"""
        j=i+1;words=[];cmp=None
        while j<len(toks) and (toks[j].kind=='word' or (toks[j].w=='-' and words and j+1<len(toks) and toks[j+1].kind=='word' and toks[j].s==toks[j-1].e and toks[j+1].s==toks[j].e)):
            if toks[j].w=='-':j+=1;continue        # 'dog-houses': read as the question reads it, 'dog houses'
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
        if k<len(toks) and toks[k].kind=='num':
            # "6 students leave": a number with its noun, then a verb of coming or going
            for x in toks[k+1:k+5]:
                if x.kind!='word':return False
                if x.low in JOIN|LEAVE and x.low!='left':return True
                if verbish(x.low) or x.low in BE|INTENT:return False
            return False
        while j<len(toks) and seen<5:
            x=toks[j]
            if x.kind=='num':return False
            if x.kind!='word':return False
            if seen>0 and (verbish(x.low) or x.low in BE|INTENT|V('decided|began|started|went')):return True
            if x.low=='of' and seen>0 and sing(toks[j-1].low) in GROUPS:j+=1;continue      # 'each box of blue beads has'
            if x.low in PRON|DET|KIN|MODS or s.is_name(x) or x.low not in NOT_NOUN:seen+=1;j+=1;continue
            return False
        return False
    def body(s,a,b):
        m=re.match(r'\s*Before\s+([^,]+),\s*(.+)$',s.t[a:b],re.S)
        if m:
            s.body(a+m.start(2),a+m.end(2));s.body(a+m.start(1),a+m.end(1));return
        toks=tokens(s.t,a,b,s.nums)
        # 'If Ann gave away 4 of her shells, she would have 11 shells left.', 'Sam would have 20 cards if he had 6 more.':
        # neither part happened (a question's own 'If ...' is not cut here: it gives the problem's data)
        seg=s.t[a:b];n0=len(s.frames)
        unreal=bool(re.search(r'\bif\b',seg,re.I) and re.search(r'\b(?:would|might)\b',seg,re.I) and '?' not in seg)
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
        if unreal:
            for f in s.frames[n0:]:f['kind']='intent';f['unreal']=True
    def verbs(s,toks):
        """positions of the verbs of a clause, with their mood (None or 'intent')"""
        out=[]
        for k,x in enumerate(toks):
            if x.kind!='word':continue
            if k+1<len(toks) and toks[k+1].low in ('room','rooms','area','shop','store','table','line','station','box','bag','hall') and k>0 and toks[k-1].low in DET:continue
            if k>0 and toks[k-1].low in ('a','an','the') and x.low not in BE|HAVE and x.low not in INTENT and not x.low.endswith('ed'):continue   # 'A cook had'
            # 'spent 5 dollars on rides': a word right after a preposition is a thing, not a verb
            if k>0 and toks[k-1].low in V('on|for|of|at|with|from|by|about|into|onto|over|under|during') and x.low not in BE|HAVE and not x.low.endswith(('ing','ed')):continue
            if x.low in HAVE and k+1<len(toks) and toks[k+1].low=='to':
                out.append((k,'intent'));continue
            if x.low in INTENT and not (x.low=='can' and k+1<len(toks) and toks[k+1].kind=='word' and False):
                out.append((k,'intent'));continue
            if verbish(x.low) or x.low in BE or x.low in V('decided|began|started|went|became|weighs|weighed|measures|measured|takes|took|calls|requires|required') \
               or (x.low in ('start','starts','begin','begins') and k+1<len(toks) and toks[k+1].low=='with'):
                prev=toks[k-1].low if k else ''
                mood=None
                if prev=='to' and not (k>=2 and toks[k-2].low in V('decided|went|began|started|managed|helped|came|got|wanted')):mood='intent'
                if prev=='to' and k>=2 and toks[k-2].low in V('wanted|wants|want|needs|need|needed|plans|plan|hopes|hope|likes|like|tries|try|tried|going'):mood='intent'
                # 'she would have 11 left', 'he might buy 4 more', 'would have bought': what may happen, not what did.
                # Before, only 'would' itself was marked, and the verb after it was read as done
                lead=[toks[j].low for j in range(max(0,k-3),k) if toks[j].low not in ('not','never','have','has','had','be','been','also','still','just','really','then')]
                if lead and lead[-1] in ('would','might'):mood='intent'
                out.append((k,mood))
        return out
    def clause(s,toks,subj):
        vs=s.verbs(toks)
        span=s.t[toks[0].s:toks[-1].e]
        first_v=vs[0][0] if vs else None
        csubj=s.holder(toks[:first_v]) if first_v else None
        if first_v is not None and csubj is None and not any(x.kind=='num' for x in toks[:first_v]):csubj=subj
        for i,x in enumerate(toks):
            if i and toks[i-1].kind=='num':continue
            if s.is_name(x):s.person(x.w,x.s)
        if csubj and csubj not in ('there','it','they','i','we','you') and "'" not in csubj:s.last_owner=csubj
        if csubj in s.people:s.subj_hist.append((toks[0].s,csubj))
        if csubj and csubj not in ('there','it','they','i','we','you') and (csubj not in s.people):s.last_thing=csubj
        intent=any(m=='intent' for _,m in vs)
        nidx=[k for k,x in enumerate(toks) if x.kind=='num']
        for k,x in enumerate(toks):
            if x.kind=='word' and x.low not in NOT_NOUN and x.low not in MODS and not s.is_name(x) and not verbish(x.low):
                n=sing(x.low)
                if n not in s.seen_nouns:s.seen_nouns.append(n)
        total_words=bool(re.search(r'\b(?:a total of|in total|total of|in all|altogether|all together|together|combined)\b',span.lower()))
        if not nidx:
            if s.last_noun and re.search(r'\b(?:them|it|those|these)\s+back\b|\breturn(?:s|ed)?\s+(?:them|it|those|these)\b',span,re.I):
                # 'She gave 5 shells to Ann, but Ann gave them back': things came back, with no number of their own
                s.vague.append(Frame(noun=s.last_noun,verb='back',owner=csubj or subj,span=span))
            # numberless events about something countable: "had some balloons", "watered the equal amount of trees"
            for k,x in enumerate(toks):
                if x.kind=='word' and x.low.endswith('ing') and k+1<len(toks) and toks[k+1].low=='some':
                    base={'eating':'ate','using':'used','selling':'sold','giving':'gave','spending':'spent','losing':'lost','buying':'bought','finding':'found','picking':'picked','getting':'got','receiving':'received','baking':'baked','making':'made'}.get(x.low)
                    if base:
                        np=s.np_after(toks,k+1);noun=np['noun'] or s.noun_of.get(csubj or subj) or s.last_noun
                        if noun:
                            s.frames.append(Frame(kind='change',m=None,noun=noun,adj=(),owner=csubj or subj or s.last_owner,verb=base,sign=+1 if base in GAIN else -1,span=span,other=None,implicit=np['noun'] is None))
                            return csubj or subj
            # 'some' and 'several' as before the review round; the other words only for an amount held, got, lost or given
            somes=[q for q in vague_amounts(toks) if toks[q].low in ('some','several') or s._counted(toks,vs,q)]
            if not somes:
                somes=[q for q,x in enumerate(toks) if x.low=='more' and q>0 and q+1<len(toks) and toks[q+1].kind=='word' and toks[q+1].low not in NOT_NOUN
                       and any(toks[r].low in GAIN|LOSE|TRANSFER|JOIN for r in range(max(0,q-4),q))][:1]
            made=0
            for q in somes:
                before_n=len(s.frames);s.mention(toks,q,vs,csubj or subj,span,total_words,unknown=True);made+=len(s.frames)-before_n
            if not made and s._unknown_held(toks,vs,csubj or subj,span):made=1
            if made:return csubj or subj
            for k,mood in vs:
                if toks[k].low=='left':continue
                if mood is None and toks[k].low in GAIN|LOSE|TRANSFER|JOIN|LEAVE:
                    for x in toks:
                        if x.kind=='word' and x.low not in NOT_NOUN and x.low not in MODS and not s.is_name(x) and not verbish(x.low) and x.low not in OTHER_VERBS:
                            s.vague.append(Frame(noun=sing(x.low),verb=toks[k].low,owner=csubj or subj,span=span))
                    if toks[k].low in BUY:
                        # 'He bought a pen.': something bought without a price, so the money spent is not all known
                        for nn in ('dollar','cent'):s.vague.append(Frame(noun=nn,verb=toks[k].low,owner=csubj or subj,span=span))
            return csubj or subj
        n0=len(s.frames)
        for k in nidx:s.mention(toks,k,vs,csubj or subj,span,total_words)
        s._shared_head(toks,nidx,s.frames[n0:])
        # 'and for a while on Tuesday', 'a few minutes': time not given
        if re.search(r'\b(?:for a while|for some time|some time|a few (?:minutes|hours|days|weeks|months|years|seconds)|a bit)\b',span.lower()):
            for nn in TIME_UNITS:s.vague.append(Frame(noun=nn,verb=None,owner=csubj or subj,span=span))
        # 'but she already had some apples', 'and some money on rides': an amount the story does not give, in a clause
        # that gives others; it must not be read as none
        for q in vague_amounts(toks):
            x=toks[q]
            if x.low not in ('some','several','few') and not s._counted(toks,vs,q):continue
            if q+2<len(toks) and toks[q+1].low=='of' and toks[q+2].low in _PRONOUN_OF:continue
            if q+1<len(toks) and toks[q+1].low=='more':continue     # 'found some more shells and now has 31': the event asked about
            np=s.np_after(toks,q)
            if np['noun'] in ('money','cash'):
                for nn in ('dollar','cent'):s.vague.append(Frame(noun=nn,verb=None,owner=csubj or subj,span=span))
            elif np['noun'] and np['noun'] not in NOT_NOUN and not verbish(np['noun']):
                s.mention(toks,q,vs,csubj or subj,span,total_words,unknown=True)
            elif np['noun'] is None and q>0 and toks[q-1].low=='and' and (q+1>=len(toks) or toks[q+1].low in PREP or toks[q+1].kind=='punct') and s.last_noun:
                # 'gave 9 stickers to her sister and some to her brother': some more of the stickers, how many not said
                s.vague.append(Frame(noun=s.last_noun,verb=None,owner=csubj or subj,span=span))
        if any(f.span==span and f.noun in ('dollar','cent') and (f.verb or '').lower() in BUY for f in s.frames):
            # 'She bought a pencil for 15 cents and an eraser.': something bought without a price, so the money spent
            # is not all known
            ws=[x for x in toks[nidx[-1]+1:] if x.kind=='word']
            for q in range(len(ws)-1):
                if ws[q].low=='and' and ws[q+1].low in ('a','an','some','another','the','his','her','their','several'):
                    for nn in ('dollar','cent'):s.vague.append(Frame(noun=nn,verb='bought',owner=csubj or subj,span=span))
                    break
        return csubj or subj
    def _shared_head(s,toks,nidx,made):
        """'sold 2 pepperoni, 6 bacon and 6 cheese pizzas': the earlier numbers of the list have only the kind of the thing
        the last one names (2 pepperoni pizzas). Each earlier one is a number, one singular word, then ',' or 'and';
        the last has a kind and a plural thing"""
        fs=[f for f in made if f.m is not None and f.m.kind in ('digits','word')]
        if len(fs)<2 or len(nidx)!=len(fs):return
        last=fs[-1]
        if not last.adj or len(last.adj)!=1 or not last.noun:return
        for k,f in zip(nidx[:-1],fs[:-1]):
            if not (k+2<len(toks) and toks[k+1].kind=='word' and toks[k+2].low in (',','and') and sing(toks[k+1].low)==toks[k+1].low):return
            if f.noun!=toks[k+1].low:return
        lk=nidx[-1];w=toks[lk+2].low if lk+2<len(toks) and toks[lk+2].kind=='word' else ''
        if not (w and sing(w)!=w and sing(w)==last.noun):return
        for f in fs[:-1]:
            f['adj']=(f.noun,);f['noun']=last.noun;f['other']=None
        last['other']=None
    def _counted(s,toks,vs,q):
        """is the amount at q held, got, lost or given by what happened ('has a few apples', 'won many marbles') - not
        wanted, planned ('wanted to find out the number of'), or after 'was able to'"""
        vpos,mood=s.verb_for(toks,vs,q)
        return vpos is not None and mood is None and toks[vpos].low in HAVE|GAIN|LOSE|TRANSFER|JOIN|LEAVE|BUY
    def _unknown_held(s,toks,vs,csubj,span):
        """'Sara has apples.', 'Kai has money.': an amount held, said with no number and no word for one - read as 'some'
        (not known). Not 'Sam has a dog' (one), nor 'has to', 'has been'"""
        for k,mood in vs:
            if mood is not None or toks[k].low not in HAVE or k+1>=len(toks):continue
            nx=toks[k+1]
            if nx.kind!='word' or nx.low in NOT_NOUN or nx.low in ('to','been','got','no','none','nothing') or s.is_name(nx):continue
            np=s.np_after(toks,k);w=np['noun']
            if not w or w in NOT_NOUN or verbish(w):continue
            last=toks[np['end']-1].low
            if w in ('money','cash'):w='dollar'
            elif sing(last)==last:continue                 # one thing ('lunch', 'a garden'), not an amount
            own=s.subject_of(toks,vs,k,csubj)
            s.frames.append(Frame(m=None,noun=w,adj=np['adj'],of=np['of'],ofadj=np.get('ofadj',()),owner=own,verb=toks[k].low,mood=None,span=span,
                                  before=[x.low for x in toks[:k+1] if x.kind=='word'],after=[],total=False,cmp=None,money=False,raw='some',kind='state'))
            s.last_noun=w;s.last_adj=np['adj']
            if own:s.noun_of[own]=w
            return True
        return False
    def verb_for(s,toks,vs,k):
        left=[(p,m) for p,m in vs if p<k]
        plain=[(p,m) for p,m in left if not (p and toks[p-1].low=='to' and m=='intent' and any(q<p and mm is None for q,mm in left))]
        if plain:return plain[-1]
        return left[-1] if left else (None,None)
    def subject_of(s,toks,vs,vpos,default):
        """the subject of the verb at vpos: the words after the previous verb's object"""
        prevs=[p for p,_ in vs if p<vpos]
        lo=0
        if prevs:
            lo=prevs[-1]+1
            # skip the previous verb's object up to a conjunction
            cj=[q for q in range(lo,vpos) if toks[q].low in ('and','but',',','then','while')]
            if not cj:
                if vpos>0 and toks[vpos-1].kind=='word' and toks[vpos-1].low in ('it','he','she','they','i','we','you'):
                    return s.holder([toks[vpos-1]]) or default        # '... cut a piece it was 32 inches long'
                return default
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
        if unknown and noun in ('money','cash'):noun='dollar'          # 'Kai has some money. He earns 7 dollars.'
        # 'a 285-page book', 'a five-day trip': the number counts the unit after the hyphen, and the thing named after it
        # has that many of it
        if m is not None and not money and k+2<len(toks) and toks[k+1].w=='-' and toks[k+1].s==toks[k].e and toks[k+2].kind=='word' and toks[k+2].s==toks[k+1].e:
            unit=ABBR_UNITS.get(toks[k+2].low) or sing(toks[k+2].low);thing=s.np_after(toks,k+2)
            if thing['noun'] and unit not in NOT_NOUN and not (k+3<len(toks) and toks[k+3].w=='-'):
                s.frames.append(Frame(m=m,noun=unit,adj=(),of=None,ofadj=(),owner=thing['noun'],verb='has',mood=None,span=span,before=before,
                                      after=[x.low for x in toks[thing['end']:] if x.kind=='word'],total=total_words,cmp=None,money=False,raw=m.raw,kind='state',compound=True))
                return
        if not money and k+1<len(toks) and toks[k+1].kind=='word' and toks[k+1].low in ABBR_UNITS and np['noun']==sing(toks[k+1].low):
            noun=ABBR_UNITS[toks[k+1].low]          # '2 kg 300 g': the unit, written short
        elif not money and k+1<len(toks) and toks[k+1].kind=='word' and toks[k+1].low in ('g','m','kg','km','cm','mm','ml','l') and np['noun'] in (None,toks[k+1].low):
            noun={'g':'gram','m':'meter','l':'liter'}.get(toks[k+1].low,ABBR_UNITS.get(toks[k+1].low,noun))
        if money:
            if noun is not None and noun not in ('dollar','bill'):adj=(noun,)+adj
            noun='dollar'
        elif noun in ('buck',):noun='dollar'
        endi=np['ofend'] or np['end']
        nxt_num=next((q for q in range(endi,len(toks)) if toks[q].kind=='num'),len(toks))
        after=[x.low for x in toks[endi:nxt_num] if x.kind=='word']
        vpos,mood=s.verb_for(toks,vs,k)
        if vpos is not None and k>vpos+1:
            # '15 of them died and another 23 of them were cut', '7 got on and 9 passengers got off': after 'and', a number
            # followed by its own verb is the subject of what follows, not an object of the verb before
            mid=toks[vpos+1:k];cj=[i for i,x in enumerate(mid) if x.low in ('and','but')]
            ws2=[x.low for x in toks[endi:nxt_num] if x.kind=='word'][:4]
            # a verb of its own, not a noun after a preposition ('33 dollars on drinks')
            tw2=[w for i,w in enumerate(ws2) if not (i and (ws2[i-1] in PREP or ws2[i-1] in DET))]
            if cj and all(x.low in DET|V('another|then|more|also|and|but') or x.kind=='punct' for x in mid[cj[-1]:]) \
               and any(w in JOIN|LEAVE|LOSE|GAIN|BE|GONE|V('got|get') for w in tw2) and not any(w in ('that','which','who') for w in ws2):
                vpos,mood=None,None
        verb=toks[vpos].low if vpos is not None else None
        own=s.subject_of(toks,vs,vpos,csubj) if vpos is not None else csubj
        # 'one' as a determiner or pronoun ("one neighbor brought", "the first one") is not an amount
        if m is not None and m.raw.lower() in ('one',) and (vpos is None or prev in DET|V('first|second|third|last|which|each|every')|{'the'} or np['noun'] is None):return
        if m is not None and m.raw.lower()=='one' and prev in V('into|in|onto|on|inside') and k>0 and toks[k-1].kind=='word':return   # 'into one album'
        if noun in GROUPS and np['of'] and np['of'] not in adj:adj=tuple(adj)+(np['of'],)
        f=Frame(m=m,noun=noun,adj=adj,of=np['of'],ofadj=np.get('ofadj',()),owner=own,verb=verb,mood=mood,span=span,before=before,after=after,
                total=total_words,cmp=np['cmp'],money=money,raw=m.raw if m is not None else 'some')
        # 'but didn't recycle 2 of them': what did not happen (compose takes no story with it)
        if any(w.endswith("n't") or w in ('not','never') for w in before[-4:]):f['negated']=True
        if noun is None and after[:1]==['of']:
            ofn=[w for w in after[1:5] if w not in DET and w not in ('her','his','their','my','our','your')]
            if ofn and ofn[0] not in ('them','those','these','it') and ofn[0] not in NOT_NOUN:f['noun']=sing(ofn[0]);noun=f['noun']
        if f.noun is None and m is not None and m.kind=='ordinal':
            f['implicit']=True                                          # 'and 4 more in the second': no thing of its own
        elif f.noun is None:
            if after[:2] in (['of','them'],['of','those'],['of','these']):
                # 'The fourth graders borrowed 25 of them': the books counted before, not the graders of this clause
                prev=[g.noun for g in s.frames if g.m is not None and g.m.kind!='ordinal' and g.noun]
                f['noun']=prev[-1] if prev else s.last_noun
            elif own in s.noun_of:f['noun']=s.noun_of[own]
            elif s.last_noun:f['noun']=s.last_noun
            f['implicit']=True
        if f.implicit and not f.adj and s.last_adj and f.noun==s.last_noun:f['adj']=s.last_adj
        if f.noun and not money and not (m is not None and m.kind=='ordinal'):    # 'in the first round': not the thing counted
            s.last_noun=f.noun;s.last_adj=f.adj
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
        # "They form groups of 4", "The children sit in teams of 5": the number counts the members of one group
        if m is not None and prev=='of' and len(before)>=3 and sing(before[-2]) in GROUPS|{'team'} and before[-3] in V('form|forms|formed|make|makes|made|in|into'):
            stop=next((i for i,x in enumerate(toks[:k]) if x.kind=='word' and x.low in V('form|forms|formed|make|makes|made|split|divided|arranged|organized|sit|sat|stand|stood|line|lined|are|were|get|got|go|went|work|worked|play|played|in|into')),None)
            sw=[x for x in toks[:stop] if x.kind=='word'] if stop else []
            content=s.last_noun if sw and sw[0].low in ('they','them') and len(sw)==1 else (s.holder(sw) if sw else None)
            if content and content not in PRON and content not in s.people and content not in ('there',):
                f.update(kind='rate',noun=content,per=sing(before[-2]),implicit=False);s.frames.append(f);return
        # rates
        if (verb in V('fit|fits|hold|holds|carry|carries|seat|seats') or 'can' in before[-4:] or 'could' in before[-4:]) and \
           re.match(r'(?:in|on|into|onto|inside)\s+(?:a|an|one|each|every)\s+(\w+)\b',win) and f.noun and not money:
            g=sing(re.match(r'(?:in|on|into|onto|inside)\s+(?:a|an|one|each|every)\s+(\w+)\b',win).group(1))
            if g not in NOT_NOUN and g!=f.noun:
                f.update(kind='rate',per=g);s.frames.append(f);return       # 'he can fit 8 books on a shelf': per shelf
        r=re.match(r'(?:\w+\s+){0,2}?(?:in|on|for|to|into|inside|with|from)\s+(?:each|every)\s+(?:one\s+of\s+)?(?:the\s+|his\s+|her\s+|their\s+)?(\w+)|(?:\w+\s+){0,1}?per\s+(\w+)|(?:\w+\s+){0,1}?(?:each|every)\s+(\w+)|(each|apiece)\b|(?:\w+\s+){0,1}?an?\s+(day|week|month|year|hour|minute|second|night|game|book|box|bag)\b',win)
        if r and not (next((x for x in r.groups() if x),'') in LINKV|V('weighing|costing')):
            g=next((x for x in r.groups() if x),None)
            g=None if g in ('each','apiece') or g in NOT_NOUN else sing(g)
            f.update(kind='rate',per=g);s.frames.append(f);return
        if 'everyday' in before or 'daily' in before or 'daily' in after[:2]:
            f.update(kind='rate',per='day');s.frames.append(f);return
        pn=max((q for q in range(k) if toks[q].kind=='num'),default=None)
        widx={q:i for i,q in enumerate([q for q in range(k) if toks[q].kind=='word'])}
        bk=[widx[q] for q in range(k) if toks[q].kind=='word' and toks[q].low in ('each','every')
            and not (pn is not None and pn<q<=pn+3 and (q+1>=len(toks) or toks[q+1].low in ('and',',','or','but')))]
        if bk and ((len(before)-bk[-1])<=8 or (bk[-1]==0 and not any(x.kind=='num' for x in toks[:k]))):
            ph=[]
            seg=before[bk[-1]+1:]
            if seg[:2]==['of','the'] or seg[:2]==['of','his'] or seg[:2]==['of','her'] or seg[:2]==['of','their']:seg=seg[2:]
            elif seg[:1]==['of']:seg=seg[1:]
            for i,w in enumerate(seg):
                if i==0 and w not in NOT_NOUN and w not in MODS and w not in COST|BE|HAVE|LINKV and w not in OTHER_VERBS and not w.endswith(('ed','ing')) \
                   and len(seg)>1 and (seg[1] in COST|BE|HAVE|LINKV or verbish(seg[1]) or seg[1] in V('takes|needs|uses|requires|holds|gets')):
                    ph.append(w);continue        # 'each ride costs 6 tickets': a thing, though 'ride' is also a verb
                if w in NOT_NOUN or w in MODS or verbish(w) or w in OTHER_VERBS or w in ('composed','made','filled','consists','will','can') or w in LINKV:break
                ph.append(w)
            grp=sing(ph[-1]) if ph else None
            if grp is None and seg[:1] and seg[0] in LINKV:
                # '6 pages, each having 12 stamps', '5 cages, each containing 8 birds': one of the things just counted
                if pn is not None:
                    eq=[q for q in range(pn+1,k) if toks[q].kind=='word' and toks[q].low in ('each','every')]
                    pnp=s.np_after(toks,pn)
                    if eq and pnp['noun'] and all(toks[q].kind=='punct' or toks[q].low in ('each','every') or q<pnp['end'] for q in range(pn+1,eq[0])):grp=pnp['noun']
                elif bk[-1]==0 and s.frames and s.frames[-1].m is not None and s.frames[-1].noun and not re.search(r'[.?!;]',s.t[s.frames[-1].m.end:toks[0].s]):
                    grp=s.frames[-1].noun          # the clause before, in the same sentence: '6 pages, each having ...'
            j=len(ph)
            if grp and j+1<len(seg) and seg[j]=='of':
                # 'Each box of red beads has 20 beads': the group is a box of red beads
                q2=[]
                for w in seg[j+1:]:
                    if w in NOT_NOUN or verbish(w) or w in OTHER_VERBS:break
                    q2.append(w)
                if q2:f['perof']=(sing(q2[-1]),tuple(q2[:-1]))
            f.update(kind='rate',per=grp);s.frames.append(f);return
        if f.noun in ('dollar','cent') and prev in ('for','at') and verb in V('bought|buys|buy|purchased|purchases|purchase|ordered|orders|order|got|gets|rented|rents|rent'):
            f.update(kind='change',sign=-1,item=s._obj_before(toks,k),spend=True);s.frames.append(f);return
        if verb in COST or (verb in BE and money and prev not in ('of',)) or (money and prev in ('for','at') and verb in GAIN|LOSE):
            item=s.holder([x for x in toks[:vpos] if x.kind=='word' and x.low not in ('if','that','which')]) if verb in COST|BE and vpos is not None else (s._obj_before(toks,k) if money else None)
            f.update(kind='price',item=item);s.frames.append(f);return
        if vpos is None:
            tw=[x for x in toks[endi:nxt_num] if x.kind=='word']
            if all(x.low in ('and','or') for x in tw):
                # '14 red plums and four green plums are in the basket': the numbers of a list share the verb after the list
                tw=[x for x in toks[endi:] if x.kind=='word']
            vafters=[x.low for i,x in enumerate(tw) if (x.low in JOIN|LEAVE|LOSE|GAIN|BE|HAVE|COST|OTHER_VERBS|GONE) and not (i and tw[i-1].low=='to')]
            gi=next((i for i,x in enumerate(tw) if x.low in ('got','get','gets','getting')),None)
            if gi is not None and gi+1<len(tw) and vafters[:1]==[tw[gi].low]:
                # '19 passengers got off', '7 more passengers got on the bus'
                if tw[gi+1].low in ('off','out'):vafters=['left']
                elif tw[gi+1].low in ('on','in','into','aboard'):vafters=['joined']
            if not vafters and any(x.low in AWAY and i+1<len(tw) and tw[i+1].low=='away' for i,x in enumerate(tw[:3])):vafters=['left']
            if vafters[:1] and vafters[0] in V('decided|wanted|chose|agreed|came|hurried|rushed|went|had|has'):
                # '8 kids decided to join in', '5 birds came to join them': what they did
                i0=next(i for i,x in enumerate(tw) if x.low==vafters[0])
                if i0+2<len(tw) and tw[i0+1].low=='to' and tw[i0+2].low in JOIN|LEAVE:vafters=[tw[i0+2].low]+vafters[1:]
            if np['cmp']=='more' and any(x.low in ('start','starts','started','begin','begins','began') for x in tw[:3]):vafters=['came']
            vafter=vafters[0] if vafters else None
            if len([v for v in vafters if v in JOIN|LEAVE|LOSE|GAIN|OTHER_VERBS and v not in BE])>1:
                f.update(kind='bare');s.frames.append(f);return
            # the words up to the next number; for a number in a list ('2 red, 12 green and 6 white balloons were used'),
            # up to the verb the list shares
            inlist=all(x.low in ('and','or') for x in toks[endi:nxt_num] if x.kind=='word')
            ws_after=[x.low for x in toks[k+1:None if inlist else nxt_num] if x.kind=='word']
            pas=next((i for i,w in enumerate(ws_after[:-1]) if w in ('were','was','are','is','got') and ws_after[i+1] in LOSE|GAIN|V('taken|eaten|added|thrown|given|broken|stolen|damaged|ruined|cracked')),None)
            if pas is not None:
                pv=ws_after[pas+1]
                minus=(pv in LOSE|V('taken|eaten|thrown|given|cut|chopped|picked|removed|broken|stolen|damaged|ruined|cracked')) and not (pv in ('added','put','placed'))
                place=None
                for i,w in enumerate(ws_after):
                    if (w=='from' if minus else w in ('to','into','in','on','onto')) and i+1<len(ws_after):
                        rest=[x for x in ws_after[i+1:] if x not in DET]
                        if rest:place=sing(rest[0]);break
                f.update(kind='change',sign=-1 if minus else +1,verb=pv,owner=place or s._holder_of(f.noun),other=None,subjnum=True,passive=True);s.frames.append(f);return
            if vafter in ('returned','returns','return','came back'):vafter='came'
            if vafter in JOIN|LEAVE|GONE|V('died|broke|melted|popped|fell|escaped|wilted|burst|sank|hatched') and vafter not in BE|HAVE:
                sign=+1 if vafter in JOIN|GAIN else -1
                pl=s._place(toks)
                # '19 passengers got off at the first stop': they leave the bus that holds them, not the stop
                place=pl if pl and any(g.owner==pl and g.noun==f.noun for g in s.frames) else (s._holder_of(f.noun) or pl)
                f.update(kind='change',sign=sign,verb=vafter,owner=place,other=None,subjnum=True);s.frames.append(f);return
            if 'there' in before or vafter in BE|HAVE:
                f.update(kind='state',owner=s._place(toks) or s._holder_of(f.noun) or ('there' if 'there' in before else None),subjnum=True);s.frames.append(f);return
            f.update(kind='bare');s.frames.append(f);return
        if verb in BE and 'there' in before:
            f.update(kind='state',owner=s._place(toks) or s._holder_of(f.noun) or 'there');s.frames.append(f);return
        if verb in BE and vpos is not None and vpos+1<len(toks) and toks[vpos+1].low in V('given|handed|sent|offered|awarded|lent|brought|served') \
           or (verb in BE and vpos is not None and vpos+2<len(toks) and toks[vpos+1].low in ('also','then','later','just') and toks[vpos+2].low in V('given|handed|sent|offered|awarded|lent|brought|served')):
            # 'Leo was given 5 crates of pears': he received them
            f.update(kind='change',sign=+1,other=None,verb='received');s.frames.append(f);return
        if verb in V('has|have|holds|hold|contains|contain|carries|carry|seats|seat|fits|fit') and vpos is not None:
            subj=[x for x in toks[:vpos] if x.kind=='word' and x.low not in ('can','could','will','usually','only','always','normally')]
            if len(subj)==2 and subj[0].low in ('a','an','one','each','every') and not s.is_name(subj[1]) and subj[1].low not in PRON and subj[1].low not in KIN:
                f.update(kind='state',generic=sing(subj[1].low),left=('left' in after[:2]));s.frames.append(f);return
        if verb in V('weighs|weighed|weigh|measures|measured|measure') and f.noun in UNITS:
            f.update(kind='state',measure='weight' if verb.startswith('weigh') else 'size');s.frames.append(f);return
        if verb in V('started|starts|start|began|begins|begin') and before[-1:]==['with']:
            # 'She started out with 9 toys': the holding at the start
            f.update(kind='state');s.frames.append(f);return
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
                    other=s.holder(ws[q+1:q+4],exclude=own);break
            if other is None and not away and vpos is not None:
                io=[x for x in toks[vpos+1:k] if x.kind=='word' and x.low not in ('away','back','out')]
                if io:other=s.holder(io,exclude=own)
            f.update(kind='change',sign=-1,other=other,away=away);s.frames.append(f);return
        if verb in JOIN:f.update(kind='change',sign=+1);s.frames.append(f);return
        if verb in LEAVE and verb not in ('left',):f.update(kind='change',sign=-1);s.frames.append(f);return
        if verb=='left' and 'left' not in after[:1]:f.update(kind='change',sign=-1);s.frames.append(f);return
        if verb in LOSE:f.update(kind='change',sign=-1);s.frames.append(f);return
        if verb in V('finished|completed|did|solved|answered|done') and (after[:2] in (['of','them'],['of','those'],['of','these']) or f.implicit) and own and any(g.owner==own and g.noun==f.noun and g.kind=='state' for g in s.frames):
            f.update(kind='change',sign=-1);s.frames.append(f);return
        if verb in V('filled|fills|fill') and 'with' in before[-2:] and not any(g.owner==own and g.noun==f.noun for g in s.frames):
            f.update(kind='state');s.frames.append(f);return
        if after[:2] in (['of','them'],['of','those'],['of','these'],['of','it']) and verb in V('borrowed|borrow|borrows|took|take|takes|removed|grabbed|checked'):
            hold=s._holder_of(f.noun)
            if hold and hold!=own and any(g.kind=='state' and g.owner==hold and g.noun==f.noun for g in s.frames):
                # 'The library has 80 books. The fourth graders borrowed 25 of them.': the library has 25 fewer
                f.update(kind='change',sign=-1,owner=hold,other=own,verb=verb);s.frames.append(f);return
        if after[:2] in (['of','them'],['of','those'],['of','these'],['of','it']) and verb not in LOSE and verb not in TRANSFER:
            f.update(kind='bare');s.frames.append(f);return
        if verb in V('put|puts|placed|places|stored|stores'):
            place=s._place(toks)
            if np['cmp']=='more' and place and any(g.kind=='state' and g.owner==place and g.noun==f.noun for g in s.frames):
                # 'There are 12 cans in the pantry. Sam put 7 more cans in the pantry.': the pantry gains them
                f.update(kind='change',sign=+1,owner=place,other=None);s.frames.append(f);return
            held=[g for g in s.frames if g.kind=='state' and g.noun==f.noun and place and re.search(r'\b'+re.escape(place),g.span.lower())]
            if np['cmp']=='more' and place and len({g.owner for g in held})==1:
                # 'A shop had 12 toys on a shelf ... put 7 more on the shelf': the one who holds them there gains them
                f.update(kind='change',sign=+1,owner=held[0].owner,other=None);s.frames.append(f);return
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
        if len(cut)==1 and cut[0].low in ('he','she','him','her','they','them'):return s.resolve(cut[0].low,at=cut[0].s)
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
        if hs:return hs[-1]
        # 'Ryan collected 50 leaves. He lost 12 leaves. Later, 9 more leaves blew away.': Ryan's, the one person whose
        # leaves they are (no one else gets or gives any)
        ch=[f for f in s.frames if f.noun==noun and f.kind=='change']
        gs={f.owner for f in ch}
        if len(gs)==1 and not any(f.other for f in ch) and next(iter(gs)) not in (None,'there','they','it','we','you','i'):return next(iter(gs))
        return None

def self_starts(st,toks,k):return st.starts_clause(toks,k)

# ----------------------------------------------------------------------------- the question
class Ask(dict):
    __getattr__=dict.get

DISTANCE=V('mile|kilometer|meter|foot|yard|block')
MOTION=V('drive|drives|drove|driven|travel|travels|traveled|travelled|go|goes|went|ride|rides|rode|walk|walks|walked|run|runs|ran|fly|flies|flew',
         'cover|covers|covered|bike|bikes|biked|swim|swims|swam|hike|hikes|hiked|jog|jogs|jogged|sail|sails|sailed|skate|skates|skated')
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
        dm=re.search(r"\b(?:what is|what's|what was|find|calculate|determine)\s+the\s+difference\s+(?:between|of|in)\s+(.+)$",low)
        if dm:return _difference_question(st,ask,toks,dm.group(1))
        m2=re.search(r'\b(?:what is|what was|what will be|find)\s+(?:the\s+)?(total|number|sum|cost|price|value|amount|difference|total number|total cost|total value)\s+of\s+(.*)$',low)
        pm=re.search(r'\b(?:what is|what was|what will be|what would be)\s+the\s+(?:(\w+)\s+)?(price|cost)\s*$',low) if not m2 else None
        if pm:
            # 'what is the sale price?': an amount of money
            ask.update(much=True,noun='dollar',adj=((pm.group(1),) if pm.group(1) else ()),kind='amount')
            for x in toks:
                if x.kind=='num':ask['qframes'].append(Frame(m=x.num,noun=None,adj=(),of=None,prev='',prev2='',span=q.strip()))
            ask['owner']=None;ask['have']=False;return ask
        if not m2:no('QUESTION_FORM')
        ask['much']=m2.group(1) in ('cost','price','value','total cost','total value')
        rest=m2.group(2).split();ask['total']=m2.group(1).startswith('total') or m2.group(1)=='sum'
        if m2.group(1)=='difference':no('QUESTION_DIFFERENCE')
    elif m is not True:
        ask['much']=m.group(1)=='much';rest=m.group(2).split()
    i=0;ws=[]
    if rest and rest[0] in ('more','fewer','less'):ask['cmp']=rest[0];i=1
    if i<len(rest)-1 and rest[i] in ('total','combined'):i+=1        # 'How many total miles did they drive?'
    # a plural that is also a verb is the thing asked about when the story counts it ('How many leaves are left?')
    told={f.noun for f in st.frames if f.noun}|{f.per for f in st.frames if f.per}
    thing=lambda w:sing(w)!=w and sing(w) in told
    while i<len(rest) and rest[i] not in QSTOP and rest[i] not in PREP and rest[i]!='#' and not ((verbish(rest[i]) and not thing(rest[i])) or rest[i] in OTHER_VERBS or rest[i] in INTENT) \
          and (i==(1 if ask.cmp else 0) or not any(st.is_name(x) for x in toks if x.low==rest[i])):
        ws.append(rest[i]);i+=1
    raw,ws=ws,[w for w in ws if w not in MODS]
    # 'How many small dogs does Sam have?' when the story tells of 3 big dogs and 2 small cats: the asked thing with its
    # size or age word must be told in the story (the word right before it, or one word before that); else the question
    # is about something the story does not count. Before, it answered 3
    kinds=[w for w in raw if w in KIND_MODS]
    if kinds and ws and sing(ws[-1]) not in UNITS:
        told=re.findall(r"[a-z]+",st.t[:a].lower());noun=sing(ws[-1])
        for k in kinds:
            if not any(w==k and noun in {sing(x) for x in told[j+1:j+3]} for j,w in enumerate(told)):no('ASKED_KIND_NOT_TOLD')
    # 'how many inches long is the rope': the unit is the thing counted
    if len(ws)>=2 and ws[-1] in ('long','tall','high','deep','wide','thick','heavy','old','far') and sing(ws[-2]) in UNITS:ws=ws[:-1]
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
    if re.search(r'\b(?:need|needs|needed|have to(?! (?:start|begin) with)|has to|must|should)\b',low):ask['need']=True   # 'have to start with' is when, not need
    # who
    owner=None
    for x in toks:
        if x.kind!='word' or x.low=='how':continue
        if x.low in ('his','her','their') :
            nxt=[y for y in toks if y.s>x.s and y.kind=='word'][:2]
            if nxt and nxt[0].low in KIN:owner=st.resolve(x.low,at=x.s)+"'s "+sing(nxt[0].low);break
            continue
        if x.low in ('he','she','they','him','them'):owner=st.resolve(x.low,at=x.s);break
        if st.is_name(x) and sing(x.low)!=ask.noun:
            if x.low.endswith("'s"):
                nxt=[y for y in toks if y.s>x.s and y.kind=='word'][:1]
                if nxt and nxt[0].low in KIN:owner=st.person(x.w,x.s)+"'s "+sing(nxt[0].low);break
            owner=st.person(x.w,x.s);break
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
    if len(qn)>=2 and re.search(r'\band\b',low):ask['owners']=[st.person(x.w,x.s) for x in qn]
    ask['have']=bool(re.search(r'\b(?:have|has|had)\b',low))
    pm=re.search(r'\b(?:in|on|at|inside) (?:the |a |an |his |her |their |my |our )?(\w+(?: \w+)?)\s*(?:now|left|altogether|in all|\?|$)',low)
    if pm:
        w=pm.group(1).split()[-1]
        if w not in NOT_NOUN and w!='#':ask['place']=sing(w)
    qv=None
    for qi,x in enumerate(toks):
        if qi and toks[qi-1].low in ('the','a','an','his','her','their','my','our','your','its','of'):continue   # 'is the board', 'pieces of mail': things
        if x.kind=='word' and (x.low in GAIN|LOSE|ACT|JOIN|LEAVE|TRANSFER|COST) and x.low not in HAVE|BE|V('do|does|did|need|needs'):
            if x.low=='left' and (ask.when=='now'):continue
            if sing(x.low)==ask.noun:continue              # 'How many leaves are left?': the thing, not the verb leave
            qv=x.low;break
    if qv in ('got','get','gets'):
        # 'How many people got off?': they left ('got on' stays a getting, an increase)
        nx=[x.low for x in toks if x.kind=='word'];i=nx.index(qv) if qv in nx else -1
        if 0<=i<len(nx)-1 and nx[i+1] in ('off','out'):qv='left'
    ask['verb']=qv
    if qv in TRANSFER:
        # the receiver named in the question: "did he give to Amy", "did she give Ben"
        tw=[x for x in toks if x.kind=='word'];vi=next(i for i,x in enumerate(tw) if x.low==qv)
        aft=tw[vi+1:vi+5]
        if aft and aft[0].low in ('to','with') and len(aft)>1:ask['to']=st.holder(aft[1:3],exclude=owner)
        elif aft and (st.is_name(aft[0]) or aft[0].low in ('him','her','them')):ask['to']=st.holder(aft[:1],exclude=owner)
        else:
            k2=next((i for i,x in enumerate(aft) if x.low in ('to','with')),None)
            if k2 is not None and k2+1<len(aft):ask['to']=st.holder(aft[k2+1:k2+3],exclude=owner)
    if re.search(r'\b(?:other|others|rest|else|remainder)\b',low):ask['rest']=True
    body=st.t[:a].lower()
    ok=V('how|many|much|more|fewer|less|than|of|the|a|an|there|now|left|in|all|altogether|total|together|combined|at|first|to|start|begin|with',
         'originally|beginning|end|still|then|after|that|have|has|had|do|does|did|is|are|was|were|will|would|can|could|be|been|get|got|on|by|for|from',
         'both|each|every|per|one|his|her|their|its|my|our|your|them|they|he|she|it|i|we|you|him|me|us|money|cash|initially|remain|remaining|need',
         'needs|needed|this|time|number|amount|buy|cost|costs|spend|spent|pay|paid|away|out|up|back|off|home|what|find|value|sum|total|make|made',
         'end|ended|up|together|altogether|so|far|right|over|does|dollars|dollar|cents|cent|money|worth|price|change|earn|earned|save|saved|owe',
         'totaled|totalled|total|can|could|may|might|able|already|also|currently|now|anymore|any|more|just|exactly|old|tall|long|high|deep|heavy|wide|big|is|be',
         'greatest|least|largest|smallest|most|fewest|possible|number|amount|inside|within')
    bodyw=set(re.findall(r"[a-z]+",body));bodyfam={fam(w) for w in bodyw}|{fam(lemma(w)) for w in bodyw}|{lemma(w) for w in bodyw}|{lemma(w)+'e' for w in bodyw}
    res=[w for w in re.findall(r"[a-z]+(?:'[a-z]+)?",low) if w not in ok and w not in bodyw and sing(w) not in {sing(x) for x in bodyw} and fam(w) not in bodyfam
         and lemma(w) not in bodyfam and fam(lemma(w)) not in bodyfam and (lemma(w)+'e') not in bodyfam and not any(x.low==w and st.is_name(x) for x in toks)]
    nounw={ask.noun,ask.of}|set(ask.adj or ())|set(ask.ofadj or ())
    res=[w for w in res if sing(w) not in nounw and w not in nounw]
    if qv and qv in DOWN|UP:res=[w for w in res if not (w==qv or fam(w)==fam(qv) or lemma(w)==lemma(qv))]
    if res:ask['residue']=res
    # numbers in the question: "in 3 days", "do 8 bees have", "to have 43 cats", "2 ice cream cones cost"
    for k,x in enumerate(toks):
        if x.kind!='num':continue
        np=st.np_after(toks,k)
        bw=[y.low for y in toks[:k] if y.kind=='word']
        ask['qframes'].append(Frame(m=x.num,noun=np['noun'],adj=np['adj'],of=np['of'],prev=bw[-1] if bw else '',prev2=bw[-2] if len(bw)>1 else '',span=q.strip()))
    if ask.residue:
        qn={x.noun for x in ask['qframes'] if x.noun}|{x.of for x in ask['qframes'] if x.of}|{w for x in ask['qframes'] for w in (x.adj or ())}
        ask['residue']=[w for w in ask.residue if sing(w) not in qn and w not in qn and not (ask.noun in DISTANCE and w in MOTION)] or None
    return ask

def _difference_side(st,toks,ws):
    """one side of 'the difference between X and Y': (owner, adjectives, noun); the noun may be left to the other side
    ('Omar's')"""
    ws=[w for w in ws if w not in ('the','a','an')]
    owner=None
    if len(ws)>1 and ws[0] in ('mr','mrs','ms','miss','dr','mister') and ws[1].endswith("'s"):ws=ws[1:]
    if ws and ws[0].endswith("'s"):
        tk=next((x for x in toks if x.low==ws[0] and st.is_name(x)),None)
        if tk is None:no('DIFFERENCE_OWNER')
        owner=st.person(tk.w,tk.s);ws=ws[1:]
    elif ws and ws[0] in ('my','our','your','his','her','their'):
        tk=next(x for x in toks if x.low==ws[0])
        who=st.resolve(ws[0],at=tk.s);ws=ws[1:]
        if ws and ws[0].endswith("'s") and ws[0][:-2] in KIN:owner=who+"'s "+sing(ws[0][:-2]);ws=ws[1:]
        else:owner=who
    if any(w.endswith("'s") or w in NOT_NOUN or w=='#' for w in ws):no('DIFFERENCE_SIDE')
    return owner,tuple(ws[:-1]),(sing(ws[-1]) if ws else None)

WHEN_START=r'\b(?:before|in the beginning|at first|originally|at the start|initially|to begin with|to start with)\b'
WHEN_END=r'\b(?:after|left|now|in the end|at the end|remaining|still)\b'
def _time_side(st,x):
    """('start', None) | ('end', None) | ('event', verb family) | None for one side of a difference question"""
    if re.search(WHEN_START,x):return ('start',None)
    verbs={fam(f.verb) for f in st.frames if f.kind=='change' and f.verb}
    # 'the customers that left' is what happened; 'the number left' is what remains; when people leave in the story,
    # a bare 'left' could be either
    went=re.search(r'\b(?:that|who|which) left\b',x)
    if re.search(WHEN_END,re.sub(r'\b(?:that|who|which) left\b','',x)):
        if re.search(r'\bleft\b',x) and not went and fam('left') in verbs:return None
        return ('end',None)
    vs={fam(w) if fam(w) in verbs else fam(lemma(w)) for w in x.split() if fam(w) in verbs or fam(lemma(w)) in verbs}
    return ('event',vs.pop()) if len(vs)==1 else None

def _time_noun(st,x):
    held={f.noun for f in st.frames if f.m is not None and f.kind in ('state','change')}
    ws=[sing(w) for w in x.split()]
    named=[w for w in ws if w in held]
    if len(named)==1:return named[0]
    return next(iter(held)) if len(held)==1 and not named else None

def schema_diff_time(st,ask):
    """the difference between one holding at two times, or between it and what happened to it"""
    if ask.kind!='diff_time' or ask.qframes or ask.residue:return None
    noun=ask.noun
    if noun is None:return None
    owners={f.owner for f in st.frames if f.noun==noun and f.kind in ('state','change') and f.m is not None}
    if len(owners)!=1 or None in owners:return None
    owner=owners.pop()
    # both sides are about the one holder ('the number Leo has now' is not about Ana's marbles)
    if any(n!=owner for n in ask.names or ()):return None
    if any(f.m is not None and f.noun!=noun for f in st.frames):return None
    # 'after buying' is the holding after that one event: with two events or more it could be a holding in between
    if len([f for f in st.frames if f.kind=='change' and f.noun==noun])>1:return None
    p=Plan(st,'diff_time')
    sts=[f for f in st.frames if f.kind=='state' and f.noun==noun and f.m is not None]
    if {sd[0] for sd in ask.sides}=={'start','end'} and len(sts)==2 and sts[0].span!=sts[1].span and \
       not any(f.kind!='state' for f in st.frames if f.m is not None):
        # 'A store had 15 chairs. After selling some, there were 3 left.': the holding stated before and after
        start=p.bind(sts[0],f'{noun}_before',noun);last=p.bind(sts[1],f'{noun}_after',noun)
    else:start,last=timeline(p,owner,noun)
    def q(side):
        kind,verb=side
        if kind=='start':return start
        if kind=='end':return last
        fs=[f for f in st.frames if f.kind=='change' and f.noun==noun and fam(f.verb)==verb and f.get('_q')]
        if len(fs)!=1:no('DIFFERENCE_EVENT')
        return fs[0]['_q']
    x,y=(q(sd) for sd in ask.sides)
    if x is None or y is None or x==y:return None
    t=p.new(f'difference_{noun}',noun);p.rel(f'{t} = abs({x} - {y})',ask.text)
    return p,t,noun

def _difference_question(st,ask,toks,phrase):
    """'what is the difference between the number of Lena's stickers and Omar's stickers', 'between the number of red
    pens and blue pens': two holdings the story gives, of the same kind of thing; the larger minus the smaller
    (schema_diff with ask.absolute). Other questions about a difference are not read."""
    if '#' in phrase.split():no('QUESTION_DIFFERENCE')
    m=re.fullmatch(r"(?:the )?(?:numbers?|amounts?) of (.+?) and (?:the )?(?:(?:numbers?|amounts?) of )?(.+)",phrase) or \
      re.fullmatch(r"(.+?) and (?:the )?(?:(?:numbers?|amounts?) of )?(.+)",phrase)
    if not m:no('QUESTION_DIFFERENCE')
    # 'before selling and after selling', 'the number she has now and the number she lost': one holding at two times,
    # or a holding and what happened to it
    times=[_time_side(st,x) for x in (m.group(1),m.group(2))]
    if any(times):
        if not all(times) or times[0]==times[1]:no('QUESTION_DIFFERENCE')
        ask.update(kind='diff_time',sides=times,much=False,have=False,noun=_time_noun(st,m.group(1)),
                   names={(x.w[:-2] if x.low.endswith("'s") else x.w) for x in toks if st.is_name(x)})
        return ask
    (oa,aa,na),(ob,ab,nb)=(_difference_side(st,toks,x.split()) for x in (m.group(1),m.group(2)))
    na=na or nb;nb=nb or na
    if not na or na!=nb:no('QUESTION_DIFFERENCE')
    ask.update(kind='diff',cmp='more',absolute=True,much=False,noun=na,adj=aa,owner=oa,have=False)
    if oa or ob:
        if not (oa and ob) or oa==ob or aa!=ab:no('QUESTION_DIFFERENCE')
        ask['than']=ob
    else:
        # two kinds of one thing: 'red pens and blue pens'
        if len(aa)!=1 or len(ab)!=1 or aa==ab:no('QUESTION_DIFFERENCE')
        ask['than_kind']=ab[0]
    return ask

# ----------------------------------------------------------------------------- plans
class Plan:
    def __init__(s,st,name):
        s.st=st;s.name=name;s.qs={};s.facts=[];s.used=set();s.money=None;s.cpd=None;s.gain_start=False
        s.skip={}   # numbers the question does not ask about: position -> why (set by a schema that reads the question exactly)
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
        if unit in ('dollar','cent') or unit in UNITS or '/' in str(unit):integer=False
        s.qs[name]={'name':name,'unit':unit,'integer':integer,'signed':False,'about':about};return name
    def bind(s,f,base,unit=None,integer=None):
        if f.derive:return s._derived(f,base,unit,integer)
        if f.rest:return s._rest(f,base,unit,integer)
        if f.twounits:return s._compound(f,base,unit,integer)
        noun=f.noun or 'thing'
        unit=unit or noun
        if f.m.kind=='percent' and unit not in ('percent','1'):no('PERCENT_AS_AMOUNT')    # '25% of them' is not 25 of them
        if integer is None:integer=f.m.value.denominator==1 and noun not in UNITS and noun!='dollar' and '/' not in unit
        name=s.new(base,unit,integer=integer)
        s.facts.append({'eq':f'{name} = {lit(f.m.value)}','span':f.span});s.used.add(f.m.start);return name
    def rel(s,eq,span):s.facts.append({'eq':eq,'span':span})
    def _derived(s,f,base,unit,integer):
        """an amount made of two numbers of the story (compose): a count of groups and what one group holds (3 boxes x 6
        pens), or a count of things bought and the price of one (3 notebooks x $4). Both are bound with their own spans,
        and the amount is their product"""
        c,r,g=f.derive
        cq=s.bind(c,f'{g}s',g)
        if r.known:
            # a common fact the story does not state ('a dog has 4 legs'), said as a known constant (fpl.KNOWN_FACTS)
            rq=s.new(f'{f.noun}s_per_{g}',f'{f.noun}/{g}',integer=False);s.facts.append({'eq':f'{rq} = {lit(r.m.value)}','known':r.known})
        else:rq=s.bind(r,f'{f.noun}_per_{g}',f'{f.noun}/{g}',integer=False)
        if integer is None:integer=f.m.value.denominator==1 and f.noun not in UNITS and f.noun not in ('dollar','cent')
        name=s.new(base,unit or f.noun,integer=integer)
        s.rel(f'{name} = {cq} * {rq}',r.span);s.used.add(f.m.start);return name

def _plan_rest(s,f,base,unit,integer):
    """the rest of a whole (_rest_view): the whole and each part bound with their own spans, the rest is the whole less
    the parts"""
    whole,parts=f.rest;u=unit or f.noun
    w=s.bind(whole,f'{f.noun}_in_all',f.noun);ps=[s.bind(x,f'{f.noun}_part',f.noun) for x in parts]
    if integer is None:integer=f.noun not in UNITS and f.noun not in ('dollar','cent')
    name=s.new(base,u,integer=integer)
    s.rel(f"{name} = {w} - {' - '.join(ps)}",f.span);s.used.add(f.m.start);return name
Plan._rest=_plan_rest

def _plan_compound(s,f,base,unit,integer):
    """'1 hour and 15 minutes', '2 kg 300 g': both numbers bound with their own words, the amount in the smaller unit
    is the bigger number times the constant plus the smaller number"""
    a,b,k,big,small=f.twounits
    aq=s.bind(a,f'{big}s',big,integer=False);bq=s.bind(b,f'{small}s',small,integer=False)
    kq=s.new(f'{small}s_per_{big}',f'{small}/{big}');s.facts.append({'eq':f'{kq} = {k}','known':f"{k} {IRREG_PL.get(small,small+'s')} in {'an' if big[0] in 'aeiou' or big=='hour' else 'a'} {big}"})
    name=s.new(base,unit or small,integer=False);s.rel(f'{name} = {aq} * {kq} + {bq}',f.span);s.used.add(f.m.start);return name
Plan._compound=_plan_compound

def _compound_amounts(st):
    """'ran for 1 hour and 15 minutes', 'weighs 2 kg 300 g', 'is 3 feet 4 inches long': two numbers in a row, in a bigger
    and a smaller unit of the same kind, are one amount in the smaller unit (money is read as before)"""
    fr=st.frames;out=[];i=0;changed=False
    from fractions import Fraction
    while i<len(fr):
        a=fr[i];b=fr[i+1] if i+1<len(fr) else None
        if b is not None and a.m is not None and b.m is not None and a.noun and b.noun and (a.noun,b.noun) in CONVERT and a.noun not in ('dollar','cent') \
           and a.span==b.span and (a.kind==b.kind or a.kind in ('be','unknown')) and re.fullmatch(r'\s*[A-Za-z]+\.?\s*(?:,?\s*and\s*)?',st.t[a.m.end:b.m.start]):
            k=CONVERT[(a.noun,b.noun)]
            m=N.Num(a.m.value*k+b.m.value,a.m.start,b.m.end,f'{a.m.raw} {a.noun} {b.m.raw} {b.noun}','derived')
            out.append(Frame(dict(b,m=m,raw=m.raw,twounits=(a,b,k,a.noun,b.noun))));i+=2;changed=True;continue
        out.append(a);i+=1
    if changed:st.frames=out


def _adj_ok(have,want):
    return not want or set(want)<=set(have or ())

def holding_frames(st,owner,noun,adj):
    out=[]
    for f in st.frames:
        if f.kind not in ('state','change') or f.noun!=noun:continue
        if f.m is not None and f.m.kind=='ordinal':continue         # 'in the second (round)': which one, not how many
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
    skip=set()
    for f in fs:
        if id(f) in skip:continue
        mine=f.owner==owner
        if f.kind=='state':
            if not mine:continue
            sib=[g for g in fs if g is not f and g.kind=='state' and g.owner==owner and g.span==f.span and g.adj!=f.adj]
            if cur is None and sib and not adj and f.m is not None and all(g.m is not None for g in sib):
                names=[bm(g,f'{owner}_{"_".join(g.adj) or "plain"}_{noun}') for g in [f]+sib]
                start=cur=p.new(f'{owner}_{noun}',unit);p.rel(f"{cur} = {' + '.join(names)}",f.span)
                for g in sib:skip.add(id(g))
                if any(g.kind=='change' and g.adj for g in fs):no('AMBIGUOUS_KIND')
                continue
            if cur is None:
                cur=bm(f,f'{owner}_{noun}') if f.m is not None else p.new(f'{owner}_{noun}_start',unit,about='unknown start')
                start=cur
            else:
                if f.m is None:no('UNKNOWN_LATER_STATE')
                # 'She had 10 apples before.' after the giving: a stated amount from before the events, not after them
                if re.search(r'\b(?:before|at first|originally|initially|in the beginning|to begin with|at the start|earlier)\b',f.span.lower()):no('STATE_BEFORE_EVENTS')
                if any(g.kind=='state' and g.owner==owner and g.noun==noun and g.span==f.span and g is not f for g in fs[:fs.index(f)]):no('LIST_OF_KINDS')
                v=bm(f,f'{owner}_{noun}_stated');p.rel(f'{cur} = {v}',f.span)
            f['_q']=cur;continue
        if cur is None:
            if mine and f.sign>0 and not f.passive and _source_free(p.st,f) and f.kind=='change' and fam(f.verb) not in ('join','come','arrive'):
                start=cur=bm(f,f'{fam(f.verb)}_{noun}') if f.m is not None else p.new(f'{fam(f.verb)}_{noun}',unit,about='unknown start')
                f['_q']=cur;p.gain_start=True;continue
            if mine and f.sign<0 and f.kind=='change' and any(g.kind=='state' and g.owner==owner and g.noun==noun for g in fs):
                start=cur=p.new(f'{owner}_{noun}_start',unit,about='unknown start')
            else:no('CHANGE_BEFORE_STATE')
        sign=f.sign if mine else -f.sign
        d=bm(f,f'{fam(f.verb)}_{noun}') if f.m is not None else p.new(f'{fam(f.verb)}_{noun}',unit,about='unknown change')
        f['_q']=d
        nxt=p.new(f'{owner}_{noun}',unit)
        p.rel(f"{nxt} = {cur} {'+' if sign>0 else '-'} {d}",f.span);cur=nxt
    return start,cur

def has_holding(st,owner,noun,adj=()):
    if any(f.kind=='state' and f.owner==owner and f.noun==noun and _adj_ok(f.adj,adj) for f in st.frames):return True
    first=next((f for f in st.frames if f.kind in ('state','change') and f.noun==noun and (f.owner==owner or f.other==owner) and _adj_ok(f.adj,adj)),None)
    if first and first.kind=='change' and first.owner==owner and first.sign<0 and any(g.kind=='state' and g.owner==owner and g.noun==noun for g in st.frames):return True
    return bool(first and first.kind=='change' and first.owner==owner and first.sign>0 and not first.passive and _source_free(st,first) and fam(first.verb) not in ('join','come','arrive'))

def _source_free(st,f):
    """the gain comes from nobody, or from a place that holds nothing in the story"""
    return f.other is None or not any(g.owner==f.other or (g.other==f.other and g is not f) for g in st.frames)

def events(st,verb,noun,adj,owner,ask=None):
    v=fam(verb)
    # 'How much did she spend?' counts what she bought at a price ('bought a pen for $2'), unless the question names
    # what the money went on ('spend on lunch')
    spend=v in ('spend','pay') and ask is not None and not re.search(r'\b(?:on|for)\b',ask.low)
    return [f for f in st.frames if f.kind in ('change','act') and (fam(f.verb)==v or (spend and f.spend)) and f.noun==noun and _adj_ok(f.adj,adj)
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
        if not any(f.noun==noun or (f.kind=='rate' and f.per==noun) for f in st.frames) and any(f.noun==ask.of or f.of==ask.of for f in st.frames):noun=ask.of
    if noun is None:
        cand={f.noun for f in st.frames if f.noun and f.kind in ('state','change','act') and (ask.owner is None or f.owner==ask.owner)}
        if not cand and ask.owner:
            cand={f.noun for f in st.frames if f.noun and f.kind in ('state','change','act') and str(f.owner or '').startswith(ask.owner+"'s ")}
        if len(cand)==1:noun=next(iter(cand))
    if noun=='money':noun='dollar'
    if noun=='dollar' and not re.search(r'\bdollars?\b',ask.low or ''):
        # 'How much money is left?' in a story told only in cents: the answer is in cents
        if {f.noun for f in st.frames if f.m is not None and f.noun in ('dollar','cent')}=={'cent'}:noun='cent'
    if noun and not any(f.noun==noun for f in st.frames):
        mem=members(noun)
        if mem and mem!='*':
            held={f.noun for f in st.frames if f.m is not None and f.noun in mem}
            if len(held)==1 and all(f.noun in held or f.noun in ('dollar','cent') for f in st.frames if f.m is not None):
                h=next(iter(held))
                # v1022.8.0: another kind of the whole named without a number ('A class has 14 boys and some girls. How
                # many students are in the class?'): the whole is not known, and the one kind counted is not it
                if not any(m!=h and re.search(r'\b'+re.escape(m)+r'(?:s|es)?\b',st.t.lower()) for m in mem):noun=h
    return noun

# ---- schema: holding --------------------------------------------------------
KIN_GROUP=V('family|friends|friend|kids|children|sisters|brothers|parents|guests|classmates|cousins|sister|brother|son|daughter|mom|dad|wife|husband')
def _holding_view(st,noun):
    """everyday ways a holding changes that its frames do not say directly:
    'Nina had 40 points. If she scored another 6 points': points scored after a stated number of points are gained;
    'Frank bought 20 rolls. If his family ate 12': his family eats his rolls (they hold none of their own);
    'Mia's ribbon was 30 inches long. If she cut off 8 inches': she cuts her ribbon (she holds no inches herself);
    'Ana bought 6 apples, but she already had 4 apples': what she already had comes before what she bought"""
    fr=list(st.frames)
    holds=lambda o:any(g.kind=='state' and g.owner==o and g.noun==noun for g in fr)
    poss=sorted({g.owner for g in fr if g.kind=='state' and g.noun==noun and "'s " in str(g.owner or '')})
    out=[];changed=False
    for i,f in enumerate(fr):
        g=f
        if f.noun==noun and f.m is not None:
            if f.kind=='act' and (fam(f.verb) in ('score','earn','win') or fam(lemma(f.verb or '')) in ('score','earn','win')) and any(h.kind=='state' and h.owner==f.owner and h.noun==noun for h in fr[:i]):
                g=Frame(dict(f,kind='change',sign=+1,other=None))
            elif f.kind=='change' and f.sign is not None and f.sign<0 and f.other is None and fam(f.verb) in ('eat','use','drink','break','lose','pop') \
                 and "'s " in str(f.owner or '') and str(f.owner).split("'s ",1)[1] in KIN_GROUP \
                 and not holds(f.owner) and has_holding(st,str(f.owner).split("'s ",1)[0],noun):
                g=Frame(dict(f,owner=str(f.owner).split("'s ",1)[0]))
            elif f.kind=='change' and f.owner and len(poss)==1 and poss[0].startswith(str(f.owner)+"'s ") and not holds(f.owner) and fam(f.verb) in ('cut','trim','trimmed'):
                g=Frame(dict(f,owner=poss[0],sign=-1,other=None))       # what she cut off her ribbon, her ribbon has fewer
        if g is not f:changed=True
        out.append(g)
    for f in [x for x in out if x.kind=='state' and x.noun==noun and x.m is not None and re.search(r'\balready\b',x.span.lower())]:
        first=next((i for i,x in enumerate(out) if x.noun==noun and x.owner==f.owner and x.kind=='change'),None)
        if first is not None and first<out.index(f):
            out.remove(f);out.insert(first,f);changed=True
    if not changed:return st
    v=_View(st,fr[0]);v.frames=out;return v

def schema_holding(st,ask):
    if ask.qframes or ask.kind not in ('amount','more') or ask.rest or ask.residue or any(f.kind in ('rate','price','compare','times') for f in st.frames):return None
    if REST_ARE.search(st.t):return None          # '35 are blue and the rest are green': parts of a whole (schema_rest)
    noun=asked_noun(st,ask)
    if noun is None:return None
    st=_holding_view(st,noun)
    adj=ask.adj or ();owner=ask.owner;p=Plan(st,'holding');fr=st.frames
    if owner=='they' and not st.people and not any(f.owner=='they' for f in fr):owner=None   # 'How many pigs came to join them?'
    if ask.kind=='more':
        # "How many more did she find?" -> the unknown amount of that event
        if not ask.verb or ask.need:return None
        hits=events(st,ask.verb,noun,adj,owner)
        if len(hits)!=1 or hits[0].m is not None:return None
        f=hits[0];timeline(p,f.owner if f.owner!='they' else owner,noun,adj)
        if '_q' not in f:return None
        return p,f['_q'],noun
    lt=re.search(r'\b(?:left|more|still)\s+to\s+(\w+)',ask.low)
    if lt and ask.verb and fam(lemma(lt.group(1)))==fam(lemma(ask.verb)) and ask.kind=='amount':
        # 'How many pages does she have left to read?': all of them, less what she read
        hits=events(st,ask.verb,noun,adj,owner,ask)
        if not hits or any(f.m is None for f in hits) or len({f.owner for f in hits})!=1:return None
        who=hits[0].owner
        tots=[f for f in fr if f.m is not None and f.noun==noun and f.kind=='state' and _adj_ok(f.adj,adj)
              and (f.owner in (who,None,'there') or str(f.owner).startswith(f"{who}'s "))]   # 'Ben's book has 120 pages'
        if len(tots)!=1:return None
        whole=p.bind(tots[0],f'{noun}_in_all',noun);names=[p.bind(f,f'{fam(f.verb)}_{noun}',noun) for f in hits]
        left=p.new(f'{noun}_left_to_{fam(lemma(ask.verb))}',noun);p.rel(f"{left} = {whole} - {' - '.join(names)}",ask.text);return p,left,noun
    if ask.verb and fam(ask.verb) not in ('have','left'):
        hits=events(st,ask.verb,noun,adj,owner,ask)
        if ask.to:
            hits=[f for f in hits if f.other==ask.to or (f.other is None and re.search(r'\bto\s+'+re.escape(ask.to.lower())+r'\b',f.span.lower()))]
            if not hits:return None
        if not hits:return _between_states(st,ask,noun,adj,p)
        if any(f.total for f in hits):return None
        if ask.to and not st.vague and all(f.m is not None for f in hits) and len({f.owner for f in hits})==1 \
           and not any(re.search(r'\b(?:rest|remaining|remainder|half|twice|double|triple|times|each|every|per|equally|evenly|all|those|them|left|not|n\'t)\b',g.span.lower()) for g in fr):
            # "How many stamps did he give to Amy?": only the giver's own stock and what the giver gave to other people
            # may stay out of the answer
            giver=hits[0].owner;others=[g for g in fr if g.m is not None and g not in hits]
            if all(g.noun==noun and g.owner==giver and ((g.kind=='state' and not g.subjnum) or (g.kind=='change' and fam(g.verb)==fam(ask.verb) and g.other and g.other!=ask.to)) for g in others):
                for g in others:p.skip[g.m.start]=f"not asked: the question asks how many {noun}s {giver} gave to {ask.to}"
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
    if not holders:
        for f in fr:
            if f.noun==noun and f.owner and f.owner not in holders and has_holding(st,f.owner,noun,adj):holders.append(f.owner)
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

DOWN=V('spend|spent|use|used|eat|ate|sell|sold|give|gave|lose|lost|cut|cuts|drink|drank|pay|paid|donate|donated|throw|threw|remove|removed|left|leave')
UP=V('grow|grew|get|got|earn|earned|find|found|buy|bought|collect|collected|save|saved|receive|received|add|added|gain|gained|make|made|pick|picked|join|joined|came|come')
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

def schema_compare_things(st,ask):
    cmps=[f for f in st.frames if f.kind in ('compare','times')]
    if not cmps or ask.qframes or ask.residue or ask.rest or ask.need or ask.kind!='amount':return None
    if any(f.kind in ('rate','price','intent','unknown','bare','be') for f in st.frames):return None
    fr=[f for f in st.frames if f.m is not None]
    head=lambda f:f.of or f.noun
    if any(f.other in st.people or f.other is None for f in cmps):return None
    owners={f.owner for f in fr}
    if len(owners)!=1:return None
    heads=[head(f) for f in fr if f.kind not in ('compare','times')]+[head(f) for f in cmps]
    if len(set(heads))!=len(heads):return None
    p=Plan(st,'compare_things');q={}
    for f in fr:
        if f.kind in ('state','change','act') and (f.kind!='change' or f.sign>0):q[head(f)]=p.bind(f,head(f),head(f))
    for _ in range(3):
        for f in cmps:
            h=head(f)
            if h in q:continue
            other=f.other if f.other in q else next((k for k in q if k.endswith(f.other or '#') or (f.other or '#').endswith(k)),None)
            if other is None:continue
            if f.kind=='compare':
                d=p.bind(f,'difference',h);v=p.new(h,h);p.rel(f"{v} = {q[other]} {'+' if f.sign>0 else '-'} {d}",f.span)
            else:
                d=p.bind(f,'factor','1',integer=False);v=p.new(h,h);p.rel(f'{v} = {q[other]} * {d}',f.span)
            q[h]=v
    noun=ask.of or ask.noun
    if noun not in q:noun=ask.noun if ask.noun in q else None
    if noun is None or len(q)!=len(fr):return None
    for k in q:p.qs[q[k]]['unit']='item'
    return p,q[noun],noun

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
    if ask.absolute:p.rel(f'{t} = abs({x} - {y})',ask.text)
    else:p.rel(f'{t} = {x} - {y}' if ask.cmp=='more' else f'{t} = {y} - {x}',ask.text)
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
 'mail':'letter|postcard|magazine|package|parcel|card|bill|catalog|catalogue|envelope|flyer|newspaper',
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
    if noun in ('piece','item','thing') and ask.of and members(ask.of):mem=members(ask.of)    # 'pieces of clothing': clothes
    if mem is None:return None
    if any(f.kind not in ('state','change','act') for f in st.frames if f.m is not None) or st.vague:return None
    fr=[f for f in st.frames if f.m is not None]
    if not fr or any(f.implicit or f.noun is None for f in fr):return None
    if mem!='*' and any(f.noun not in mem and not any(w in mem for w in (f.adj or ())) for f in fr):return None
    # v1022.8.0: a kind of the whole named but not counted ('14 boys and some girls'): the whole is not known
    if mem!='*' and any(m not in {f.noun for f in fr} and re.search(r'\b'+re.escape(m)+r'(?:s|es)?\b',st.t.lower()) for m in mem):return None
    if len({f.noun for f in fr})<1:return None
    owner=ask.owner;v=fam(ask.verb) if ask.verb else None
    if owner not in (None,'they') and any(f.owner not in (owner,) for f in fr):return None
    # what was given away is asked as it is ('How many pieces of clothing did he give away?'); otherwise a loss is not a
    # holding of the kind
    if any(f.kind=='change' and f.sign<0 for f in fr) and not (v and all(f.kind!='state' and fam(f.verb)==v for f in fr)):return None
    if v and any(fam(f.verb)!=v for f in fr if f.kind!='state'):return None
    if v is None and any(f.kind!='state' for f in fr):return None
    p=Plan(st,'category');names=[p.bind(f,f'{f.noun}s',noun) for f in fr]
    if len(names)==1:return p,names[0],noun
    t=p.new(f'total_{noun}',noun);p.rel(f"{t} = {' + '.join(names)}",ask.text);return p,t,noun

def st_unit(noun):return noun or 'thing'

class _View:
    """the story with one generic state read as a rate"""
    def __init__(s,st,r):
        s.__dict__.update(st.__dict__);s.frames=[r if (g.m is not None and r.m is not None and g.m.start==r.m.start) else g for g in st.frames]
def _with(st,r):return _View(st,r)

CONVERT={('week','day'):7,('day','hour'):24,('hour','minute'):60,('minute','second'):60,('year','month'):12,('year','week'):52,('year','day'):365,
         ('foot','inch'):12,('yard','foot'):3,('meter','centimeter'):100,('kilometer','meter'):1000,('dollar','cent'):100,('pound','ounce'):16,('gallon','quart'):4,
         ('kilogram','gram'):1000,('liter','milliliter'):1000,('centimeter','millimeter'):10,('meter','millimeter'):1000,('yard','inch'):36,('mile','foot'):5280,
         ('mile','yard'):1760}

def _other_unit(st,ask):
    """the question names a unit the story does not use, and the story tells the amount in one other unit of the same kind
    ('240 minutes ... How many hours'): (the story's unit, how many of the smaller unit make the bigger, is the story's
    unit the bigger one), or None"""
    u2=ask.noun
    if u2 not in UNITS or ask.measure or not re.search(r'\b'+u2+r'|\b'+IRREG_PL.get(u2,u2),ask.low):return None
    told={f.noun for f in st.frames if f.m is not None and f.noun in UNITS}
    if u2 in told:return None
    pairs=[(u1,CONVERT[(u1,u2)],True) for u1 in told if (u1,u2) in CONVERT]+[(u1,CONVERT[(u2,u1)],False) for u1 in told if (u2,u1) in CONVERT]
    return pairs[0] if len(pairs)==1 else None
IRREG_PL={'foot':'feet','inch':'inches'}
ABBR_UNITS={'cm':'centimeter','mm':'millimeter','km':'kilometer','kg':'kilogram','lb':'pound','lbs':'pound','oz':'ounce','ft':'foot','ml':'milliliter',
            'mi':'mile','hr':'hour','hrs':'hour','min':'minute','mins':'minute','sec':'second','yd':'yard'}

def rate_frames(st,ask):
    """explicit rates, and 'A bee has 6 legs' read as a rate when the story or the question counts bees"""
    out=[f for f in st.frames if f.kind=='rate']
    if out:return out
    for f in st.frames:
        if f.generic and f.m is not None and (any(g is not f and g.noun==f.generic and g.m is not None for g in st.frames) or any(x.noun==f.generic for x in ask.qframes)):
            out.append(Frame(dict(f,kind='rate',per=f.generic,owner=None)))
    return out

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
NOBODY=(None,'there','they','it','we','you','i')
def _same_agent(st,r,f):
    """a rate and a count go together unless they belong to two different people, or to two holders doing the same thing
    ('A car travels at 50 miles per hour. A bus travels for 3 hours'); a rate held by the group itself ('Each box has 6
    pens') goes with anyone's boxes"""
    if r.owner in NOBODY or r.owner==r.per or f.owner in NOBODY or f.owner==r.owner:return True
    if r.owner in st.people and f.owner in st.people:return False
    return not (r.verb and f.verb and fam(lemma(r.verb))==fam(lemma(f.verb)))

def _groups_view(st):
    """groups said in other ways, read as a count of groups and what one group holds: '56 books in each of his 9
    bookshelves'; '6 authors, with each author having 33 books' (a count is not a rate of itself); 'each plank needs 8
    nails' (a need of each group); 'Andrew's 4 friends ... each of them brought 4 slices' (each of the people counted)"""
    fr=[f for f in st.frames if f.m is not None]
    new={}
    for f in fr:
        if f.kind=='rate' and f.per and f.noun==f.per:new[f.m.start]=Frame(dict(f,kind='state',per=None))
    rs=[f for f in fr if f.kind=='rate' and f.m.start not in new]
    if len(rs)==2:
        a,b=sorted(rs,key=lambda f:f.m.start)
        if b.noun and re.search(r'\beach\s+of\s+(?:his|her|their|the|its|my|our|your)\s*$',st.t[a.m.end:b.m.start].lower()) and a.per in (None,b.noun):
            new[a.m.start]=Frame(dict(a,per=b.noun));new[b.m.start]=Frame(dict(b,kind='state',per=None))
    counted={f.noun for f in fr if f.kind in ('state','change','act','bare','intent') and f.noun}|{x.noun for x in new.values() if x.kind=='state'}
    for f in fr:
        if f.kind=='intent' and f.m.start not in new:
            mm=re.search(r'\beach\s+((?:\w+\s+){0,2}?\w+)\s+(?:of\s+\w+\s+)?(?:needs|need|requires|uses|takes)\b',st.t[st.t.find(f.span):f.m.start].lower()) if st.t.find(f.span)>=0 else None
            g=sing(mm.group(1).split()[-1]) if mm else None
            if g and g in counted:new[f.m.start]=Frame(dict(f,kind='rate',per=g,owner=None))
    for f in fr:
        if f.kind=='rate' and f.per is None and f.m.start not in new and re.search(r'\beach\s+of\s+(?:them|those|these)\b',f.span.lower()):
            ps=[g for g in fr if g is not f and g.noun in PERSONS and g.kind in ('bare','state','change')]
            if len(ps)==1:new[f.m.start]=Frame(dict(f,per=ps[0].noun));new[ps[0].m.start]=Frame(dict(ps[0],kind='state'))
    if not new:return st
    v=_View(st,fr[0]);v.frames=[new.get(g.m.start,g) if g.m is not None else g for g in st.frames];return v

def schema_groups(st,ask):
    if ask.kind not in ('amount',) or ask.cmp or ask.residue or ask.rest:return None
    noun=asked_noun(st,ask)
    if noun is None:return None
    if _unknown_of(st,noun):return None
    st=_groups_view(st)
    if ask.need and any(f.kind in ('state','change','act','intent') and f.m is not None and f.noun==noun for f in st.frames):return None
    rates=rate_frames(st,ask)
    if len(rates)!=1:return None
    r=rates[0]
    if r.generic:st=_with(st,r)
    content=r.of if r.of and r.noun in ('piece','slice','bag','box','pack','cup','sheet','bottle','can') else r.noun
    if noun not in (r.noun,r.of,content) and not (ask.of in (r.noun,r.of)):return None
    g=r.per
    its=[f for f in st.frames if f.kind=='intent' and f.m is not None]
    if any(f.kind in ('price','compare','times','unknown','bare','be') and f.m is not None and f.m.kind!='ordinal' for f in st.frames):return None
    if its and not (len(its)==1 and g and its[0].noun==g and not any(f.kind in ('state','change','act') and f.noun==g and f.m is not None for f in st.frames)):return None
    if its:st=_View(st,its[0]);st.frames=[Frame(dict(f,kind='state')) if f is its[0] else f for f in st.frames]
    p=Plan(st,'groups')
    # the number of groups: a frame in the story, or a number in the question ("in 3 days", "do 8 bees have")
    cands=[f for f in st.frames if f is not r and f.m is not None and f.kind in ('state','change','act') and g and f.noun==g and _same_agent(st,r,f)]
    if ask.owner in st.people and r.owner in st.people and ask.owner!=r.owner and r.verb not in BE|HAVE:return None
    qc=[x for x in ask.qframes if g and (x.noun==g or (x.noun and x.noun.endswith(g)))]
    conv=[(x,CONVERT[(x.noun,g)]) for x in ask.qframes if g and (x.noun,g) in CONVERT]
    if qc and not cands and len(ask.qframes)==1:
        cnt=qc[0]
        gq=p.bind(cnt,f'{g}s',g)
    elif conv and not qc and not cands and len(ask.qframes)==1:
        # "3 servings a day ... in one week": weeks x 7 days
        x,k=conv[0];wq=p.bind(x,f'{x.noun}s',x.noun)
        kq=p.new(f'{g}s_per_{x.noun}',f'{g}/{x.noun}');p.facts.append({'eq':f'{kq} = {k}','known':f'{k} {g}s in a {x.noun}'})
        gq=p.new(f'{g}s',g);p.rel(f'{gq} = {wq} * {kq}',ask.text)
    elif len(cands)==1 and not ask.qframes:
        gq=p.bind(cands[0],f'{g}s',g)
    elif len(cands)>1 and not ask.qframes and g:
        gq=operand(p,st,g,ask.owner)
        if gq is None:return None
    elif r.per is None and len([f for f in st.frames if f.m is not None])==2:
        # "Chris gave his 35 friends 12 pieces of candy each": the other number counts the receivers in the same clause
        other=[f for f in st.frames if f is not r and f.m is not None and f.m.kind!='ordinal']
        if len(other)!=1 or other[0].span!=r.span:return None
        if other[0].noun not in PERSONS and not (other[0].m.start<r.m.start and other[0].noun!=r.noun and other[0].kind in ('act','state','bare') and other[0].noun not in UNITS):return None
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
DIVIDE=r'\b(?:divided|divide|split|shared|share|put|packed|placed|sorted|organized|organised|arranged|grouped|separated|distributed|stacked|served)\b'
def _unknown_of(st,noun):
    """'She put some photos into one album', 'and some to her brother': an amount of the thing that the story does not give"""
    # ('each neighbor received an equal number of croissants' says how they are shared, not an amount left unsaid)
    return any(f.m is None and f.noun==noun for f in st.frames) or \
           any(v.noun==noun and not (EQUAL_SHARES.search(v.span.lower()) or re.search(r'\beach\b',v.span.lower())) for v in st.vague)

def schema_share(st,ask):
    noun=asked_noun(st,ask)
    fr=[f for f in st.frames if f.m is not None]
    if any(f.kind in ('price','compare','times','unknown') for f in st.frames):return None
    # 'They are divided equally into 6 bags': a count of groups said with 'be' only for the groups things are divided into
    if any(f.kind=='be' and (ask.kind!='each' or f.m is None or not re.search(DIVIDE,f.span.lower())) for f in st.frames):return None
    low=ask.low
    if noun is None and ask.kind=='amount' and re.search(r'\b(?:left|left over|remain|remaining)\b',low) and re.search(r'\b(?:equal|equally|evenly)\b',st.t.lower()):
        # 'How many are left?': the one thing of the story that is not the groups or the people it is shared among
        cand={f.noun for f in fr if f.kind in ('state','change') and f.noun and f.noun not in PERSONS and (f.before or [''])[-1] not in ('into','among','between','onto','to','in')}
        if len(cand)==1:noun=next(iter(cand))
    if noun is None and ask.kind!='each':return None
    if noun is not None and ask.kind=='each' and _unknown_of(st,noun):return None
    p=Plan(st,'share')
    # "how many will each get" / "how many in each box": total of noun, number of groups
    if ask.kind=='each':
        mg=re.search(r'\b(?:each|every|per)\s+(?:of\s+)?(?:the\s+|his\s+|her\s+|their\s+)?(?:#\s+)?(\w+(?:\s+\w+)*)',low)
        g=None
        if mg and mg.group(1).split()[0] not in ('one','other'):
            # the last word of the group's name ('in each dog house'); a verb right after 'each' means each of the receivers
            ws_=[]
            for w in mg.group(1).split():
                if w in NOT_NOUN or verbish(w) or w in V('receive|receives|get|gets|eat|eats|take|takes|have|has|need|needs') or w=='#':break
                ws_.append(w)
            g=sing(ws_[-1]) if ws_ else 'person'
        people=g in ('person','people','one') or g in PERSONS
        if noun is None:
            # 'how big is each group?', 'how many does each person get?': the one thing of the story that is not the groups
            cand={f.noun for f in fr if f.kind in ('state','change','act','intent') and f.noun and not (g and (f.noun==g or f.noun.endswith(g))) and not (people and f.noun in PERSONS)}
            if len(cand)!=1 or ask.measure not in (None,'big'):return None
            noun=next(iter(cand))
            if _unknown_of(st,noun):return None
        tots=[f for f in fr if f.kind in ('state','change','intent','act') and f.noun==noun]
        grp=[f for f in fr if f not in tots and f.kind in ('state','change','bare','intent','act','be') and f.noun and
             ((g and (f.noun==g or f.noun.endswith(g))) or (people and f.noun in PERSONS))]
        if any(f.kind=='be' and f not in grp for f in fr):return None
        qg=[x for x in ask.qframes if g and x.noun==g]
        if len(tots)!=1:return None
        if qg and not grp:cnt=qg[0]
        elif len(grp)==1 and not ask.qframes:cnt=grp[0]
        else:return None
        # 'Rosa has 42 beads and 3 rings. They are divided ...': 'they' may be all of the things
        if len({f.noun for f in fr if f is not cnt and f.kind in ('state','change','act','intent')})>1 and \
           any(re.search(DIVIDE,f.span.lower()) and re.search(r'\b(?:they|them|these|those|it|all)\b',f.span.lower()) for f in st.frames):return None
        if not re.search(r'\b(?:equal|equally|evenly|same|each|every|per|divided|split|shared|share|among|organized|group|groups)\b',(st.t).lower()):return None
        tq=p.bind(tots[0],f'{noun}_total',noun);gq=p.bind(cnt,'groups',cnt.noun or 'group')
        per=p.new(f'{noun}_per_group',f'{noun}/{cnt.noun or "group"}',integer=False)
        if cnt.m and cnt.m.value==0:return None          # sharing among no one: no reading
        if tots[0].m and cnt.m and (tots[0].m.value/cnt.m.value).denominator!=1:
            if not re.search(r'\b(?:equal|equally|evenly|share|shares|shared|split|splits|divide|divides|divided|distribute|distributes|distributed)\b',st.t.lower()) or noun in UNITS or noun in ('dollar','cent'):return None
            p.rel(f'{per} = floor({tq} / {gq})',ask.text)
        else:p.rel(f'{tq} = {per} * {gq}',ask.text)
        if re.search(r'\b(?:left|remain|remaining|over|full)\b',low):return None
        p.qs[per]['integer']=noun not in UNITS and noun not in ('dollar','cent')
        return p,per,noun
    # "gave 42 pencils to 12 students equally. How many pencils are left?" -> the remainder
    if ask.kind=='amount' and re.search(r'\b(?:left|left over|remain|remaining)\b',low) and re.search(r'\b(?:equal|equally|evenly)\b',st.t.lower()):
        if _unknown_of(st,noun):return None
        tots=[f for f in fr if f.kind in ('state','change') and f.noun==noun]
        grp=[f for f in fr if f not in tots and f.noun and (f.noun in PERSONS or f.noun in GROUPS)]
        # a measure is not shared out in whole pieces; a container counted as a thing is ('30 cups on the table', not '3 cups of flour')
        if len(tots)==1 and len(grp)==1 and len(fr)==2 and (noun not in UNITS or (noun in GROUPS and tots[0].of is None)):
            tq=p.bind(tots[0],f'{noun}_total',noun);gq=p.bind(grp[0],'groups',grp[0].noun)
            per=p.new(f'{noun}_per_group',f'{noun}/{grp[0].noun}');p.rel(f'{per} = floor({tq} / {gq})',tots[0].span)
            rem=p.new(f'{noun}_left',noun);p.rel(f'{rem} = {tq} - {per} * {gq}',ask.text);return p,rem,noun
        if not any(f.kind=='rate' for f in fr):return None   # what one group holds is given: read below
    # "how many boxes / days / trips": total of the content, rate per group
    if any(f.kind=='intent' for f in st.frames):return None
    rates=rate_frames(st,ask)
    if len(rates)==1 and rates[0].generic:
        st=_with(st,rates[0]);fr=[f for f in st.frames if f.m is not None];rates=[f for f in st.frames if f.kind=='rate']
    left=re.search(r"\b(?:not full|isn't full|left over|leftover|in the last)\b",low) or (re.search(r'\b(?:left|remain|remaining)\b',low) and
         (re.search(r'\b(?:equally|evenly)\b',st.t.lower()) or any(re.fullmatch(r'un\w+ed',w) for w in ask.residue or ())))
    if len(rates)==1 and ask.kind=='amount' and noun==rates[0].noun and left and len(fr)==2 and not _unknown_of(st,noun):
        r=rates[0];tot=[f for f in fr if f is not r and f.noun==noun and (f.kind=='state' or (f.kind=='change' and f.sign>0))]
        if len(tot)!=1 or not r.per or noun in UNITS:return None
        tq=p.bind(tot[0],f'{noun}_total',noun);rq=p.bind(r,f'{noun}_per_{r.per}',f'{noun}/{r.per}')
        full=p.new(f'full_{r.per}',r.per);p.rel(f'{full} = floor({tq} / {rq})',r.span)
        rem=p.new(f'{noun}_left',noun);p.rel(f'{rem} = {tq} - {rq} * {full}',ask.text);return p,rem,noun
    if len(rates)==1 and ask.kind=='amount':
        r=rates[0];g=r.per
        if noun!=g and not (g is None and noun in GROUPS):return None
        content=r.noun
        if _unknown_of(st,content):return None          # 'gave 9 to her sister and some to her brother': the rest is not known
        tots=[f for f in fr if f is not r and f.kind in ('state','change','act','bare') and f.noun in (content,r.of) and _same_agent(st,r,f)]
        if ask.owner in st.people and r.owner in st.people and ask.owner!=r.owner and r.verb not in BE|HAVE:return None
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
        if re.search(r'\b(?:full|complete|completely|whole|can|could)\b',low) or \
           (re.search(r'\b(?:equally|evenly)\b',st.t.lower()) and noun not in UNITS):
            # 'packed them evenly in some bags ... how many bags': the full ones
            n=p.new(noun,noun);p.rel(f'{n} = floor({exact})',ask.text);return p,n,noun
        p.qs[exact]['integer']=True;return p,exact,noun
    return None

# ---- schema: the rest ----------------------------------------------------------
REST_ARE=re.compile(r"\b(?:the rest|the remaining ones|the others)\s+(?:of them\s+)?(?:are|were|is|was)\s+((?:about\s+)?[a-z]+)\b",re.I)
def schema_rest(st,ask):
    """a whole and some of its parts, and 'the rest are' a kind the question asks about: 'Nick has 90 marbles. 35 are
    blue and the rest are green' -> 90 - 35 green marbles"""
    if ask.kind!='amount' or ask.cmp or ask.qframes or ask.total:return None
    ms=list(REST_ARE.finditer(st.t))
    if len(ms)!=1:return None
    kind=ms[0].group(1).lower();head=kind.split()[-1]
    words=set(re.findall(r"[a-z]+",ask.low))
    asked=head in words or sing(head) in {sing(w) for w in words} or (ask.adj and head in ask.adj)
    if not asked:return None
    fr=[f for f in st.frames if f.m is not None]
    if len(fr)<2:return None
    whole,parts=fr[0],fr[1:]
    if _unknown_of(st,whole.noun):return None
    if whole.m.start>ms[0].start() or any(f.m.start>ms[0].start() for f in parts):return None
    if whole.kind not in ('state','change') or (whole.kind=='change' and whole.sign is not None and whole.sign<0):return None
    noun=whole.noun
    if not noun or any(f.noun!=noun or f.kind not in ('state','change','be') or (f.kind=='change' and f.sign is not None and f.sign<0) for f in parts):return None
    # every part is a kind of its own, said apart from the whole, and none of them is the kind asked
    # some of a kind not counted ('some are red'): the rest is not known
    if st.vague or re.search(r'\b(?:some|a few|several|many|others)\s+(?:of them\s+)?(?:are|were|is|was)\b',st.t,re.I):return None
    for f in parts:
        span=re.split(r'\b(?:the rest|the remaining ones|the others)\b',f.span.lower())[0];kw=set(re.findall(r"[a-z]+",span))
        if head in kw or sing(head) in {sing(w) for w in kw}:return None
        if f.owner not in (whole.owner,None) and not f.implicit:return None
    for w in words:
        if any(w in (f.adj or ()) for f in parts):return None
    if ask.owner not in (None,whole.owner) and not (ask.owner in ('he','she','they') or whole.owner in (None,'there')):return None
    asked_noun_=ask.noun
    if asked_noun_ and asked_noun_!=noun and sing(asked_noun_)!=sing(head) and asked_noun_ not in ('one','thing'):return None
    p=Plan(st,'rest')
    w=p.bind(whole,f'{noun}_in_all',noun);names=[p.bind(f,f'{noun}_part',noun) for f in parts]
    r=p.new(f'{noun}_rest',noun);p.rel(f"{r} = {w} - {' - '.join(names)}",ms[0].group(0));return p,r,noun

# ---- schema: what one of each weighs or costs, from totals -------------------------
TOTAL_OF=re.compile(r'\s*the\s+(?:total\s+)?(weight|cost|price|mass)\s+of\b',re.I)
def _kind_name(phrase):
    """'a bag of chips' -> 'bag', 'an apple' -> 'apple'"""
    ws=[w for w in re.findall(r"[a-z]+",phrase.lower()) if w not in ('a','an','one','the','each','such')]
    if 'of' in ws:ws=ws[:ws.index('of')]
    return sing(ws[-1]) if ws else None
def schema_unit_values(st,ask):
    """'The weight of 4 apples is 600 g. The total weight of 2 apples and 3 pears is 900 g. How much heavier is a pear
    than an apple?': each sentence is an equation in what one of each kind weighs (or costs); the solver solves them
    together, and the checker makes sure there is one answer"""
    low=ask.low or ''
    qd=re.search(r'\bhow much (heavier|lighter|more|less|cheaper) (?:is|does|do) ((?:a|an|one|each) [a-z ]+?) (?:weigh |cost )?than ((?:a|an|one|each) [a-z ]+)$',low)
    qs=re.search(r'\bhow much (?:does|do|is) ((?:a|an|one|each) [a-z ]+?) (?:weigh|cost)$',low)
    if not (qd or qs):return None
    eqs=[]
    for a,b in sentences(st.t):
        if b>len(st.t)-len(ask.text or '')+1 and ask.text and ask.text.strip() in st.t[a:b]:continue
        if not TOTAL_OF.match(st.t[a:b]):continue
        if re.search(r'\b(?:some|several|a few|many|a number of)\b',st.t[a:b].lower()):return None    # 'some apples and 3 pears'
        fs=[f for f in st.frames if f.m is not None and a<=f.m.start<b]
        meas=[f for f in fs if f.noun in UNITS or f.noun in ('dollar','cent')]
        cnts=[f for f in fs if f not in meas]
        if len(meas)!=1 or not cnts or any(f.noun in UNITS or not f.noun for f in cnts):return None
        eqs.append((cnts,meas[0]))
    if len(eqs)<2:return None
    unit=eqs[-1][1].noun
    if any(m.noun!=unit for _,m in eqs):return None
    kinds=[]
    for cnts,_ in eqs:
        for c in cnts:
            if c.noun not in kinds:kinds.append(c.noun)
    if len(kinds)<2 or len(eqs)<len(kinds):return None
    if any(f.m is not None and not any(f is c or f is m for cnts,m in eqs for c in cnts) and not N.optional(f.m,st.t) for f in st.frames):return None
    p=Plan(st,'unit_values')
    one={k:p.new(f'one_{k}',unit,integer=False) for k in kinds}
    for i,(cnts,m) in enumerate(eqs):
        terms=[f"{p.bind(c,f'{c.noun}s_{i+1}','1')} * {one[c.noun]}" for c in cnts]
        w=p.bind(m,f'{unit}s_{i+1}',unit,integer=False)
        p.rel(f"{' + '.join(terms)} = {w}",m.span)
    if qd:
        x,y=_kind_name(qd.group(2)),_kind_name(qd.group(3))
        if x not in one or y not in one or x==y:return None
        big,small=(x,y) if qd.group(1) in ('heavier','more') else (y,x)
        d=p.new('difference',unit,integer=False);p.rel(f'{d} = {one[big]} - {one[small]}',ask.text);return p,d,unit
    x=_kind_name(qs.group(1))
    if x not in one:return None
    return p,one[x],unit

# ---- schema: percent changes ------------------------------------------------------
PCT_DOWN=re.compile(r'\b(?:off|discount|discounted|less|decrease|decreased|decreases|reduced|reduction|cheaper|markdown|sale|goes down|went down|down by|drops|dropped|falls|fell)\b')
PCT_UP=re.compile(r'\b(?:interest|tax|taxes|tip|tips|service charge|charge|increase|increased|increases|more|markup|raise|raised|gratuity|goes up|went up|up by|rises|rose)\b')
PCT_CHANGE=re.compile(r'\b(?:tip|discount|interest|tax|charge|markup|raise|increase|decrease)\b')
def schema_percent(st,ask):
    """a percent of an amount: what is taken off ('on sale for 25% off'), added ('4% interest', '15% tip', 'a 4% service
    charge') or a part ('30% of them walk'). The question asks the new amount or the change itself"""
    if ask.kind!='amount' or ask.cmp or ask.qframes or ask.rest:return None
    fr=[f for f in st.frames if f.m is not None and not N.optional(f.m,st.t)]
    pcts=[f for f in fr if f.m.kind=='percent']
    if len(pcts)!=1:return None
    pc=pcts[0];others=[f for f in fr if f is not pc]
    # 'for one year', 'in one year': the time the interest is for; any other number is the amount
    years=[f for f in others if f.noun in ('year',) and f.m.value==1]
    base=[f for f in others if f not in years]
    if len(base)!=1 or base[0].m.kind=='percent':return None
    b=base[0];unit=b.noun if b.noun in ('dollar','cent') else (b.noun or 'dollar')
    if _unknown_of(st,b.noun) or st.vague:return None
    t=st.t.lower();sent=next((t[x:y] for x,y in sentences(st.t) if x<=pc.m.start<y),t)
    near=sent[max(0,pc.m.start-sentences(st.t)[0][0]-40):]
    if re.search(r'\bthan\b',sent):return None         # '25% less than Ben's bike': a comparison with something not given here
    of_part=re.search(r'\b'+re.escape(pc.m.raw.lower())+r'\s+of\s+(?:them|those|these|the|all|his|her|their)\b',sent)
    down=bool(PCT_DOWN.search(sent));up=bool(PCT_UP.search(sent))
    if of_part and not (down or up):kind='part'
    elif down and not up:kind='down'
    elif up and not down:kind='up'
    else:return None
    low=ask.low or ''
    noun=asked_noun(st,ask) if ask.noun else (unit if ask.much else None)
    if noun is None:return None
    if kind=='part':
        if noun!=b.noun:return None
        gone=re.search(r'\b(?:sold|ate|used|gave|lost|spent|broke|left|took|donated|threw)\b',sent)
        if re.search(r'\b(?:left|remain|remaining|still)\b',low):
            # 'It sold 25% of them. How many shirts are left?': the whole less the part
            if not gone:return None
            kind='down';asks_change=False
        else:asks_change=True
    else:
        if (noun not in ('dollar','cent') and noun!=unit) or (b.noun not in ('dollar','cent',None) and noun!=b.noun):return None
        named=PCT_CHANGE.search(low)
        new_value=re.search(r'\b(?:cost|costs|pay|paid|have|has|after|new|final|sale price|total|in all|end|now|price)\b',low)
        if named and not re.search(r'\b(?:after|total|pay|paid|have|new|final)\b',low):asks_change=True
        elif new_value:asks_change=False
        else:return None
    if ask.owner and b.owner and ask.owner not in (b.owner,'you','i','we') and ask.owner in st.people and b.owner in st.people:return None
    p=Plan(st,'percent')
    a=p.bind(b,f'{unit}_base',unit,integer=False)
    q=p.new('rate','1',integer=False);p.facts.append({'eq':f'{q} = {lit(pc.m.value/100)}','span':pc.span});p.used.add(pc.m.start)
    yq=None
    if years:yq=p.bind(years[0],'years','year',integer=False)
    ch=p.new('change',unit,integer=False);p.rel(f'{ch} = {a} * {q}'+(f' * {yq}' if yq else ''),pc.span)
    if years and kind!='up':return None
    if asks_change:return p,ch,unit
    n=p.new('new_amount',unit,integer=False);p.rel(f"{n} = {a} {'-' if kind=='down' else '+'} {ch}",ask.text);return p,n,unit

# ---- schema: room left, two parts ---------------------------------------------
HOLDS=V('holds|hold|fits|fit|seats|seat')
def schema_room(st,ask):
    """the room left in a holder: 'A shelf holds 40 books. There are 26 books already on the shelf. How many more books
    can be put on the shelf?' -> 40 - 26"""
    if ask.kind!='more' or ask.than or ask.qframes:return None
    if not re.search(r'\bcan\b.*\b(?:be put|be added|be placed|be stored|be packed|fit|go)\b|\b(?:room|space) for\b',ask.low):return None
    noun=asked_noun(st,ask)
    fr=[f for f in st.frames if f.m is not None]
    if noun is None or len(fr)!=2 or _unknown_of(st,noun):return None
    cap=[f for f in fr if f.noun==noun and f.kind=='state' and f.verb and f.verb.lower() in HOLDS]
    cur=[f for f in fr if f not in cap and f.noun==noun and f.kind=='state']
    if len(cap)!=1 or len(cur)!=1:return None
    c,h=cap[0],cur[0];holder=c.generic or c.owner
    # 'A DVD book holds 126 DVDs': the holder is the thing named right before 'holds'
    if h.owner and h.owner!=holder and re.search(r'\b'+re.escape(h.owner)+r'\s+(?:can\s+)?(?:holds?|fits?|seats?)\b',c.span.lower()):holder=h.owner
    if not holder or h.owner!=holder or ask.place not in (None,holder):return None
    p=Plan(st,'room')
    cq=p.bind(c,f'{noun}_{holder}_holds',noun);hq=p.bind(h,f'{noun}_in_{holder}',noun)
    n=p.new(f'room_for_{noun}',noun);p.rel(f'{n} = {cq} - {hq}',ask.text);return p,n,noun

def schema_two_parts(st,ask):
    """a whole kept in two holders, what one of them holds, and how many more the other holds: 40 shells in two boxes, 15
    in the first box -> (40 - 15) - 15 more in the second"""
    if ask.kind!='diff' or ask.cmp not in ('more','fewer','less'):return None
    m=re.search(r'\b(?:in|on|at)\s+the\s+(first|second)\s+(\w+)\s+than\s+(?:in\s+|on\s+|at\s+)?the\s+(first|second)\b',ask.text.lower())
    if not m or m.group(1)==m.group(3):return None
    g=sing(m.group(2));noun=asked_noun(st,ask)
    fr=[f for f in st.frames if f.m is not None and f.m.kind!='ordinal']
    if noun is None or len(fr)!=3 or _unknown_of(st,noun):return None
    two=[f for f in fr if f.noun==g and f.m.value==2]
    part=[f for f in fr if f.noun==noun and re.search(r'\bthe\s+(?:first|second)\s+'+re.escape(m.group(2)),f.span.lower())]
    whole=[f for f in fr if f not in two and f not in part and f.noun==noun and f.kind in ('state','change') and (f.kind=='state' or f.sign>0)]
    if len(two)!=1 or len(part)!=1 or len(whole)!=1 or part[0].kind!='state':return None
    which=re.search(r'\bthe\s+(first|second)\s+'+re.escape(m.group(2)),part[0].span.lower()).group(1)
    p=Plan(st,'two_parts')
    w=p.bind(whole[0],f'{noun}_in_all',noun);k=p.bind(two[0],f'{g}s',g);a=p.bind(part[0],f'{noun}_in_{which}_{g}',noun)
    other='second' if which=='first' else 'first'
    b=p.new(f'{noun}_in_{other}_{g}',noun);p.rel(f'{b} = {w} - {a}',two[0].span)
    big,small=(m.group(1),m.group(3)) if ask.cmp=='more' else (m.group(3),m.group(1))
    q={which:a,other:b}
    n=p.new(f'{noun}_difference',noun);p.rel(f'{n} = {q[big]} - {q[small]}',ask.text);return p,n,noun

# ---- schema: even up ----------------------------------------------------------
EQUAL_SHARES=re.compile(r'\b(?:same number|same amount|equal number|equal amount|equally|evenly)\b')
def schema_even_up(st,ask):
    """the fewest more things that make the shares equal: 50 cookies to fill 8 boxes with the same number of cookies need
    ceil(50 / 8) x 8 - 50 = 6 more. With what one group holds given instead ('A jar holds 4 slices'), the fewest more
    that fill up the last group"""
    if ask.kind!='more' or not ask.need or ask.than or ask.qframes:return None
    noun=asked_noun(st,ask)
    if noun is None or (noun in UNITS and noun!='cent'):return None
    if _unknown_of(st,noun):return None
    fr=[f for f in st.frames if f.m is not None]
    if len(fr)!=2 or any(f.kind in ('price','compare','times','unknown') for f in st.frames):return None
    tots=[f for f in fr if f.noun==noun and f.kind in ('state','change','act','intent') and (f.kind!='change' or f.sign>0) and not f.generic]
    if len(tots)!=1:return None
    o=next(f for f in fr if f is not tots[0])
    p=Plan(st,'even_up')
    if (o.kind=='rate' and o.per or o.generic) and o.noun==noun:
        # 'A box holds 4 slices ... to fill up the last box'
        if not re.search(r'\b(?:last|final)\b',ask.low):return None
        g=o.per or o.generic;tq=p.bind(tots[0],f'{noun}_have',noun);rq=p.bind(o,f'{noun}_per_{g}',f'{noun}/{g}')
        k=p.new(f'{g}s',g);p.rel(f'{k} = ceil({tq} / {rq})',o.span)
        n=p.new(f'more_{noun}',noun);p.rel(f'{n} = {k} * {rq} - {tq}',ask.text);return p,n,noun
    if not (o.noun and o.noun!=noun and (o.noun in GROUPS or o.noun in PERSONS) and o.kind in ('state','change','intent','bare','act')):return None
    g=o.noun
    # the shares are to be equal: said with the groups, 'each', or a verb of dividing, and not 'the same number as' someone
    said=False
    for a,b in sentences(st.t):
        sn=st.t[a:b].lower()
        if EQUAL_SHARES.search(sn) and not re.search(r'\bsame (?:number|amount)(?: of \w+(?: \w+)?)? as\b',sn) and \
           (re.search(r'\b(?:each|fill)\b',sn) or re.search(DIVIDE,sn) or g in {sing(w) for w in re.findall('[a-z]+',sn)}):said=True
    if not said:return None
    tq=p.bind(tots[0],f'{noun}_have',noun);gq=p.bind(o,f'{g}s',g)
    per=p.new(f'{noun}_per_{g}',f'{noun}/{g}');p.rel(f'{per} = ceil({tq} / {gq})',o.span)
    n=p.new(f'more_{noun}',noun);p.rel(f'{n} = {per} * {gq} - {tq}',ask.text);return p,n,noun

# ---- schema: proportion --------------------------------------------------------
TAKES=V('take|takes|took|need|needs|needed|use|uses|used|require|requires|required')
def _counted_one(st,f):
    """the thing an amount goes with when one of it is meant, said after the amount with a/an and no number ('3 cups of
    flour to make a cake'): its noun when the clause names exactly one such thing, else None"""
    a=st.t.find(f.span)
    if a<0:return None
    out={sing(m.group(1).split('-')[-1]) for m in re.finditer(r"\b(?:a|an|one)\s+((?:[a-z]+-)*[a-z]+)\b",st.t[f.m.end:a+len(f.span)].lower())}
    out={x for x in out if x!=f.noun and x not in NOT_NOUN and x not in PERSONS and x not in OTHER_VERBS and not verbish(x)}
    return next(iter(out)) if len(out)==1 else None

def _proportion_pair(st):
    """an amount and the number of things it goes with, said in one clause -> (amount frame, count frame or None when one
    is meant, the counted thing): '4 notebooks for $10', 'a kite for 85 cents' (money spent on them); 'It takes 5 minutes
    to wash one car', 'It takes 3 cups of flour to make a cake', 'She needs 5 cups of flour to bake two loaves', 'each
    kite needs 4 sticks'. None unless the story says exactly one such thing and nothing else"""
    fr=[f for f in st.frames if f.m is not None]
    out=[]
    for f in fr:
        if f.spend and f.item:x=f.item
        elif f.verb and f.verb.lower() in TAKES and f.kind in ('change','intent','act','state'):x=None
        else:continue
        same=[g for g in fr if g is not f and g.span==f.span and g.noun and g.noun!=f.noun and g.kind in ('change','intent','act','state') and not g.spend]
        same=[g for g in same if g.noun==x] if x is not None else [g for g in same if g.m.start>f.m.start]
        if len(same)==1:out.append((f,same[0],same[0].noun));continue
        if same:continue
        if x is not None:
            if re.search(r'\b(?:a|an|one)\s+(?:\w+\s+){0,2}?'+re.escape(x),f.span.lower()):out.append((f,None,x))
            continue
        one=_counted_one(st,f)
        if one is None and f.owner and re.search(r'\b(?:each|every)\s+'+re.escape(f.owner)+r'\b',f.span.lower()):one=f.owner
        if one is not None:out.append((f,None,one))
    if len(out)!=1:return None
    f,c,x=out[0]
    if len(fr)!=1+(c is not None):return None
    return out[0]

def schema_proportion(st,ask):
    """an amount for some things, and the question asks the amount for another number of them, or how many of them
    another amount goes with: 4 notebooks for $10, 6 notebooks cost 6 x (10 / 4); 3 cups of flour make a cake, 15 cups
    make floor(15 / 3) cakes"""
    if ask.kind!='amount' or ask.cmp or ask.rest or len(ask.qframes)!=1:return None
    if any(g.kind in ('price','compare','times','unknown','be','bare','rate') for g in st.frames):return None
    pr=_proportion_pair(st)
    if pr is None:return None
    f,c,x=pr
    if ask.owner not in (None,f.owner,'you','i','we','they','it'):return None
    noun=asked_noun(st,ask)
    if noun is None or _unknown_of(st,noun) or _unknown_of(st,f.noun):return None
    q=ask.qframes[0];amt=f.noun;p=Plan(st,'proportion')
    def rate():
        if c is None:return p.bind(f,f'{amt}_per_{x}',f'{amt}/{x}',integer=False)
        aq=p.bind(f,f'{amt}_for_{x}s',amt,integer=False);cq=p.bind(c,f'{x}s',x)
        rq=p.new(f'{amt}_per_{x}',f'{amt}/{x}',integer=False);p.rel(f'{rq} = {aq} / {cq}',f.span);return rq
    if q.noun and (q.noun==x or q.noun.endswith(x) or x.endswith(q.noun)):
        # the amount for another number of the things
        if not (noun==amt or (f.spend and noun in ('dollar','cent')) or (f.of and noun==f.of)):return None
        rq=rate();mq=p.bind(q,f'{x}s_asked',x)
        t=p.new(f'{amt}_for_asked',amt,integer=False);p.rel(f'{t} = {mq} * {rq}',ask.text);return p,t,amt
    if q.noun==amt or (amt in ('dollar','cent') and q.noun is None and st.t[max(0,q.m.start-1):q.m.start]=='$' and amt=='dollar'):
        # how many of the things another amount goes with
        if not (noun==x or noun.endswith(x) or x.endswith(noun)):return None
        rq=rate();mq=p.bind(q,f'{amt}_asked',amt,integer=False)
        exact=p.new(f'{x}s_exact',x,integer=False);p.rel(f'{exact} = {mq} / {rq}',ask.text)
        if re.search(r'\b(?:can|could|able)\b',ask.low):
            n=p.new(f'{x}s',x);p.rel(f'{n} = floor({exact})',ask.text);return p,n,x
        p.qs[exact]['integer']=True;return p,exact,x
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
    if noun and item and (noun==item or noun.endswith(item) or item.endswith(noun) or ask.of==item) and ask.kind=='amount' and re.search(r'\b(?:can|could|afford|buy|purchase|get)\b',low):
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
        # 'He wants to buy a $20 ball and a $45 bike': the prices of the things wanted, said with the wish, all of them
        wanted=[f for f in fr if f.kind=='intent' and f.noun==noun and f.owner in (owner,None) and fam(lemma(f.verb or '')) in ('buy','get')]
        # a thing wanted without its price ('a ball and a $45 bike'): what is needed is not known
        if any(re.search(r'\b(?:a|an|some|another|other)\s+(?![$\d])[a-z]',st.t[a:b].lower()) for a,b in sentences(st.t) for f in wanted if a<=f.m.start<b):wanted=[]
        if wanted and not goals and len(wanted)>1 and not re.search(r'\b(?:buy|get|purchase|afford)\b',ask.low):goals=wanted
        elif len(wanted)==1 and not goals:goals=wanted
    else:
        goals=[f for f in fr if f.kind=='intent' and f.goal and f.noun==noun and _adj_ok(f.adj,adj)]
    if len(goals)>1 and noun in ('dollar','cent') and owner is not None and all(f.kind=='intent' for f in goals):
        if any(f.kind not in ('state','change','intent') for f in fr) or not has_holding(st,owner,noun):return None
        cur=timeline(p,owner,noun)[1]
        names=[p.bind(f,f'price_{i+1}',f.noun,integer=False) for i,f in enumerate(goals)]
        tot=p.new('cost_in_all',noun,integer=False);p.rel(f"{tot} = {' + '.join(names)}",goals[0].span)
        n=p.new(f'needed_{noun}',noun,integer=False);p.rel(f'{n} = {tot} - {cur}',ask.text);return p,n,noun
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
        # 'the same number of boxes of each' is not as many of each thing
        if re.search(r'\b(?:same|equal) (?:total )?number of (?:the )?(?:boxes|packs|packages|bags|packets|cases|sets|bundles|groups|containers|cartons|crates)\b',t):return None
        names=[p.bind(f,f'size_{i}','item') for i,f in enumerate(fr)]
        expr=names[0]
        for n in names[1:]:expr=f'lcm({expr}, {n})'
        r=p.new('least_common','item');p.rel(f'{r} = {expr}',ask.text);return p,r,ask.noun or 'item'
    return None

def schema_price_total(st,ask):
    """'An apple costs 3 dollars and a pear costs 4 dollars. How much do 2 apples and 5 pears cost?' -> 2 x 3 + 5 x 4"""
    if not (ask.much or ask.noun in ('dollar','cent')) or ask.kind!='amount' or ask.residue or ask.rest or st.vague:return None
    prices=[f for f in st.frames if f.kind=='price' or (f.kind=='rate' and f.noun in ('dollar','cent'))]
    if len(prices)<2 or any(f.kind in ('compare','times','intent','unknown','be','bare') for f in st.frames):return None
    items=[f.item if f.kind=='price' else f.per for f in prices]
    if None in items or len(set(items))!=len(items) or len({f.noun for f in prices})!=1:return None
    money=prices[0].noun;counts={}
    for x in [f for f in st.frames if f.m is not None and f not in prices]+list(ask.qframes):
        it=next((i for i in items if x.noun==i or (x.noun and x.noun.endswith(i))),None)
        if it is None or it in counts:return None
        counts[it]=x
    if set(counts)!=set(items):return None
    p=Plan(st,'price_total');parts=[]
    for f,i in zip(prices,items):
        pq=p.bind(f,f'price_per_{i}',f'{money}/{i}',integer=False);cq=p.bind(counts[i],f'{i}s',i);parts.append(f'{cq} * {pq}')
    t=p.new('cost',money,integer=False);p.rel(f"{t} = {' + '.join(parts)}",ask.text);return p,t,money

def schema_spend_left(st,ask):
    """'You have 50 dollars. You buy 4 shirts for 9 dollars each. How much money is left?' -> 50 - 4 x 9"""
    if not (ask.much or ask.noun in ('dollar','cent')) or ask.kind!='amount' or ask.when!='now' or ask.qframes or ask.residue or st.vague:return None
    fr=[f for f in st.frames if f.m is not None]
    if len(fr)!=3 or any(f.kind in ('compare','times','intent','unknown','be','bare') for f in st.frames):return None
    prices=[f for f in fr if (f.kind=='rate' and f.noun in ('dollar','cent')) or f.kind=='price']
    budgets=[f for f in fr if f.kind=='state' and f.noun in ('dollar','cent') and not f.subjnum]
    counts=[f for f in fr if f.kind=='change' and f.sign>0 and f.noun not in ('dollar','cent') and fam(f.verb)=='buy']
    if len(prices)!=1 or len(budgets)!=1 or len(counts)!=1:return None
    pr,b,c=prices[0],budgets[0],counts[0]
    if pr.noun!=b.noun or b.owner!=c.owner or (ask.owner and ask.owner!=b.owner):return None
    if not ((pr.kind=='rate' and ((pr.per is None and c.span==pr.span) or pr.per==c.noun)) or (pr.kind=='price' and pr.item==c.noun)):return None
    money=b.noun;item=c.noun;p=Plan(st,'spend_left')
    bq=p.bind(b,'money_at_first',money,integer=False);cq=p.bind(c,f'{item}s',item)
    pq=p.bind(pr,f'price_per_{item}',f'{money}/{item}',integer=False)
    left=p.new('money_left',money,integer=False);p.rel(f'{left} = {bq} - {cq} * {pq}',ask.text);return p,left,money

SLOT=re.compile(r'\b(?:on|in|during|at)\s+(?:the\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday|morning|afternoon|evening|night|weekend|'
                r'first day|second day|third day|first week|second week|january|february|march|april|may|june|july|august|september|october|november|december)\b')
def _slot_after(st,f):
    """the time named right after a frame's number: '12 pages on Monday', 'twice as many on Tuesday'"""
    end=next((n.start for n in st.nums if n.start>f.m.end),len(st.t))
    m=SLOT.search(re.split(r'[.?!;]',st.t[f.m.end:end].lower())[0]);return m.group(1) if m else None

def schema_times_slot(st,ask):
    """'Lisa read 12 pages on Monday and twice as many on Tuesday. How many pages did she read on Tuesday?'"""
    if ask.kind!='amount' or ask.qframes or ask.residue or ask.rest or st.vague:return None
    fr=[f for f in st.frames if f.m is not None]
    ts=[f for f in fr if f.kind=='times' and f.other is None]
    if len(ts)!=1 or len(fr)!=2:return None
    t=ts[0];b=next(f for f in fr if f is not t)
    if b.kind not in ('act','change','state') or b.m.start>t.m.start or b.noun!=t.noun or b.owner!=t.owner or fam(b.verb)!=fam(t.verb):return None
    sb,stt=_slot_after(st,b),_slot_after(st,t)
    if not sb or not stt or sb==stt:return None
    noun=asked_noun(st,ask)
    if noun!=t.noun or (ask.owner and ask.owner!=t.owner) or (ask.verb and fam(ask.verb)!=fam(t.verb)):return None
    qm=SLOT.search(ask.low);qslot=qm.group(1) if qm else None
    p=Plan(st,'times_slot');bq=p.bind(b,f'{noun}_{sb}'.replace(' ','_'),noun);kq=p.bind(t,'times','1',integer=False)
    tq=p.new(f'{noun}_{stt}'.replace(' ','_'),noun);p.rel(f'{tq} = {kq} * {bq}',t.span)
    if ask.total and not qslot:
        tot=p.new(f'{noun}_total',noun);p.rel(f'{tot} = {bq} + {tq}',ask.text);return p,tot,noun
    if qslot==stt and not ask.total:return p,tq,noun
    return None

# ----------------------------------------------------------------------------- a second step of thought
class _Composed:
    """the story with derived amounts in place of the counts they are made of (compose)"""
    def __init__(s,st,frames):s.__dict__.update(st.__dict__);s.frames=frames;s.composed=True

def _derive(c,r,noun,g,adj,**kw):
    m=N.Num(c.m.value*r.m.value,c.m.start,c.m.end,f'{c.m.raw} x {r.m.raw}','derived')
    return Frame(dict(c,m=m,noun=noun,adj=adj,of=None,ofadj=(),derive=(c,r,g),raw=m.raw,implicit=False,**kw))

def _each_after(st,f,g=None):
    """is the amount said to be in each group? By words after it ('9 apples in each box', '9 apples and 7 pears in each
    box'), or by a group named before it that is not an earlier amount's ('Each box holds 6 eggs and 2 apples', 'there are
    3 tables and each table has 4 chairs'). '5 boxes with 9 apples in each box and 7 loose apples': 'in each box' belongs
    to the 9 apples, and the 7 apples are not in each box (round 10: it read 5 x 9 + 5 x 7)"""
    a,end=next(((x,y) for x,y in sentences(st.t) if x<=f.m.start<y),(0,len(st.t)))
    g=re.escape(g or f.generic)
    if re.search(rf"\b(?:each|every|per|a|an)\s+(?:[a-z]+\s+)?{g}(?:e?s)?\b",st.t[f.m.end:end],re.I):return True
    return not re.search(rf"\d[\d,.]*\s+(?:[a-z]+\s+){{0,3}}(?:in|on|at|inside|for)\s+(?:each|every)\s+(?:[a-z]+\s+)?{g}(?:e?s)?\b",st.t[a:f.m.start],re.I)

PARTS={'leg':'legs','eye':'eyes','ear':'ears','foot':'feet','wheel':'wheels'}
def _known_rates(st,ask):
    """the common facts a question about legs, eyes, ears, feet or wheels needs, for the things the story counts ('I see
    109 dogs. How many legs do I see?' -> a dog has 4 legs). Only when the story itself says nothing about them"""
    from fractions import Fraction
    from .fpl import KNOWN_FACTS
    n=asked_noun(st,ask) if ask is not None else None
    if n not in PARTS:return []
    body=st.t[:st.t.rfind(ask.text)] if ask.text and ask.text in st.t else st.t
    if any(f.noun==n for f in st.frames) or re.search(r'\b(?:'+n+r's?|'+PARTS[n]+r')\b',body,re.I):return []
    out=[]
    def fact(t):
        art='an' if t[0] in 'aeiou' else 'a'
        return [(k,v) for k,v in ((f'{art} {t} has {v} {PARTS[n]}',v) for v in range(1,9)) if KNOWN_FACTS.get(k)==Fraction(v)]
    # '7 tricycles and some bikes': the bikes have wheels too, and how many is not known
    if any(c.m is None and c.noun and fact(c.noun) for c in st.frames):return []
    for c in st.frames:
        if c.m is None or c.kind not in ('state','change','act') or not c.noun:continue
        hit=fact(c.noun)
        if len(hit)==1 and not any(x.per==c.noun for x in out):
            k,v=hit[0]
            out.append(Frame(kind='rate',noun=n,per=c.noun,adj=(),owner=None,verb=None,span=c.span,known=k,raw=str(v),m=N.Num(Fraction(v),-1,-1,str(v),'known')))
    return out

def compose(st,ask=None):
    """a second step of thought, for a story no schema reads as it is. A count of groups whose content the story gives
    becomes an amount of that content ('Tom has 3 boxes of pens. There are 6 pens in each box.' -> Tom has 3 x 6 pens),
    so that what happens to the pens afterwards is read as a holding; things bought at a price each become money spent
    ('bought 3 notebooks for $4 each' -> spent 3 x 4 dollars). Strict: two rates for the same content of one group, or
    contents offered as alternatives ('6 pens or 4 markers'), give no composition; a rate and a count go together only
    when they belong to the same agent (_same_agent); a rate that is used is taken out of the story. None when nothing
    composes."""
    ok=lambda f:f.m is not None and f.m.kind in ('digits','word') and f.m.value>0
    if any(f.negated for f in st.frames):return None        # 'didn't recycle 2 of them': not composed
    rates=[]
    for f in st.frames:
        if not ok(f):continue
        if f.kind=='rate' and f.per and f.noun and f.noun not in ('dollar','cent') and f.noun!=f.per:
            if f.m.start>=0 and not _each_after(st,f,f.per):continue
            # '9 apples and 7 pears in each box': is the 9 in each box too? Not decided, not composed (round 10: 44)
            if f.m.start>=0 and re.search(r'\d[\d,.]*\s+(?:[a-z]+\s+){0,3}(?:and|or)\s+$',st.t[max(0,f.m.start-40):f.m.start],re.I):return None
            rates.append((f,f,f.per,f.noun))
        elif f.kind=='state' and f.generic and f.noun and f.noun!=f.generic and f.noun not in ('dollar','cent') \
             and any(g is not f and g.noun==f.generic and g.m is not None for g in st.frames) and _each_after(st,f):
            rates.append((f,Frame(dict(f,kind='rate',per=f.generic,owner=None)),f.generic,f.noun))
    for r in _known_rates(st,ask):
        if not any(gg==r.per and cc==r.noun for _,_,gg,cc in rates):rates.append((r,r,r.per,r.noun))
    repl={};used=set()
    for r,reff,g,content in rates:
        if any(c.m is None and c.noun==g for c in st.frames):continue      # some boxes of unknown number
        same=[x for x,_,gg,cc in rates if gg==g and cc==content and x is not r]
        if any(tuple(x.adj or ())==tuple(r.adj or ()) and x.perof==r.perof for x in same):return None   # two rates for one content of one group
        if any(gg==g and cc!=content and x.span==r.span and re.search(r'\bor\b',r.span.lower()) for x,_,gg,cc in rates):return None
        for c in st.frames:
            if c is r or not ok(c) or c.kind not in ('state','change','act') or c.noun!=g or c.of not in (None,content):continue
            if r.perof and (c.of!=r.perof[0] or tuple(c.ofadj or ())!=r.perof[1]):continue
            if not r.perof and any(x.perof for x,_,gg,cc in rates if gg==g):continue
            if not _same_agent(st,reff,c):continue
            adj=tuple(r.adj) if r.adj else (r.perof[1] if r.perof else tuple(a for a in (c.adj or ()) if a!=content))
            repl.setdefault(id(c),[]).append(_derive(c,r,content,g,adj));used.add(id(r))
    # purchases at a price each: 'bought 3 notebooks for $4 each' (a rate in money, in the clause of the purchase)
    for r in st.frames:
        if not ok(r) or r.kind!='rate' or r.noun not in ('dollar','cent') or (r.verb or '').lower() not in BUY:continue
        cs=[c for c in st.frames if ok(c) and c.kind=='change' and c.sign==1 and c.span==r.span and c.m.start<r.m.start and c.noun not in ('dollar','cent')
            and r.per in (None,c.noun) and (c.verb or '').lower() in BUY and c.owner==r.owner]
        if len(cs)!=1 or id(cs[0]) in repl:continue
        c=cs[0];repl[id(c)]=[_derive(c,r,r.noun,c.noun,(),kind='change',sign=-1,spend=True,item=c.noun,other=None)];used.add(id(r))
    if not repl:return None
    frames=[]
    for f in st.frames:
        if id(f) in used:continue
        frames.extend(repl.get(id(f),[f]))
    return _Composed(st,frames)

REST_OF=re.compile(r"\b(?:the rest|the remaining ones|the remaining|the others)\b(?!\s+(?:of them\s+)?(?:are|were|is|was)\b)",re.I)
def _rest_view(st,ask):
    """a second step of thought: 'used 14 and decided to use the rest on rides', 'put 16 into one album and the rest into
    3 albums equally', 'takes 14 of them and leaves Sam with the rest', 'has to paint 12 rooms ... has painted 9 ... the
    rest': the rest is the whole less the parts the story names before it (each bound with its own words), and a
    question about the rest asks about that amount. -> (story, question) or None"""
    ms=list(REST_OF.finditer(st.t))
    if not ms:return None
    pos=ms[0].start()
    fr=[f for f in st.frames if f.m is not None and f.m.kind!='ordinal']
    before=[f for f in fr if f.m.start<pos and f.kind not in ('rate','price')]      # what one group holds is not a part
    if len(before)<2 or len({f.noun for f in before})!=1 or any(f.derive or f.rest for f in fr):return None
    n=before[0].noun;whole,parts=before[0],before[1:]
    if not n or whole.kind not in ('state','change','intent') or (whole.kind=='change' and (whole.sign or 0)<0):return None
    if any(f.kind not in ('state','change','act','bare') for f in parts):return None
    # parts are taken from the whole: no gain among them ('put' into a holder is taken from the pool)
    # ('has to paint 12 rooms ... has already painted 9': what is done of what is to be done)
    if any(f.kind=='change' and (f.sign or 0)>0 and fam(f.verb) not in ('put','place','store')
           and not (whole.kind=='intent' and fam(lemma(f.verb or ''))==fam(lemma(whole.verb or ''))) for f in parts):return None
    if any(f.m is None and f.noun==n for f in st.frames) or st.vague:return None
    # who has the rest: 'leaves Sam with the rest', else whoever had the whole
    lm=re.search(r'\bleaves?\s+([A-Z][a-z]+)\s+with\s+the\s+rest\b',st.t)
    owner=lm.group(1) if lm else whole.owner
    sent=next((st.t[a:b] for a,b in sentences(st.t) if a<=pos<b),st.t)
    from fractions import Fraction
    v=whole.m.value-sum((f.m.value for f in parts),Fraction(0))
    if v<=0:return None
    m=N.Num(v,whole.m.start,whole.m.end,f'{whole.m.raw} - '+' - '.join(f.m.raw for f in parts),'derived')
    r=Frame(kind='state',m=m,noun=n,adj=whole.adj,of=whole.of,ofadj=(),owner=owner,verb=None,span=sent.strip(),raw=m.raw,rest=(whole,parts),implicit=False)
    out=[]
    for f in st.frames:
        if f is whole:out.append(r)
        elif any(f is x for x in parts):continue
        else:out.append(f)
    view=_Composed(st,out)
    a=Ask(dict(ask))
    if re.search(r'\bthe rest\b|\bthe remaining\b|\bthe others\b',ask.low or ''):
        # 'how many more hours will it take him to paint the rest': how many, for the rest
        a['rest']=None;a['residue']=[w for w in (ask.residue or []) if w not in ('rest','remaining','others')] or None
        if a.cmp and not a.than:a['cmp']=None;a['kind']='amount'
    return view,a

def schema_derived_sum(st,ask):
    """'A club took 3 cars and 2 vans. There were 4 people in each car and 9 people in each van. How many people went?'
    -> 3 x 4 + 2 x 9: in a composed story whose every number makes an amount of the asked thing, the amounts add up"""
    if not getattr(st,'composed',False) or ask.kind!='amount' or ask.cmp or ask.need or ask.rest or ask.qframes or st.vague:return None
    if re.search(r'\b(?:left|remain|remaining|each|every|per|more|fewer|less)\b',ask.low):return None
    noun=asked_noun(st,ask)
    fr=[f for f in st.frames if f.m is not None]
    ds=[f for f in fr if f.derive and f.noun==noun]
    if not ds or len(ds)!=len(fr):return None
    if any(f.m is None and f.noun for f in st.frames):return None     # '7 tricycles and some bikes': not all of it is known
    # 'How many animal legs ...', 'How many spider legs ...': the words before the thing name what the story counts
    srcs={f.derive[2] for f in ds}
    if ask.adj and not all(a in srcs or sing(a) in srcs or a in ('animal','pet','human') for a in ask.adj):return None
    if len({f.kind for f in ds})!=1 or any(f.kind=='change' and f.sign<0 for f in ds):return None
    owners={f.owner for f in ds if f.owner not in NOBODY}
    if len(owners)>1 or (ask.owner and owners and ask.owner not in owners):return None
    p=Plan(st,'groups_sum');names=[p.bind(f,f'{noun}_{f.derive[2]}',noun) for f in ds]
    t=p.new(f'{noun}_total',noun);p.rel(f"{t} = {' + '.join(names)}",ask.text);return p,t,noun

SCHEMAS=[schema_gcd_lcm,schema_change,schema_compare_things,schema_holding,schema_compare,schema_diff,schema_category,schema_groups,schema_share,schema_price,schema_need,
         schema_spend_left,schema_times_slot,schema_price_total,schema_diff_time,schema_even_up,schema_proportion,schema_rest,schema_room,schema_two_parts,schema_percent,schema_unit_values]

# ----------------------------------------------------------------------------- read
def read(text):
    try:return _read_pronouns(text)
    except NoRead as e:return {'spec':None,'reason':'EN:'+str(e)}
    except (ArithmeticError,ValueError,KeyError,IndexError,TypeError,AttributeError,RecursionError) as e:
        # a fault of the reader is never an answer and never breaks the caller; the reason names it, so it is seen
        return {'spec':None,'reason':'EN:INTERNAL:'+type(e).__name__}

def _consistent(resolved):
    """one person is never both he and she"""
    kind={}
    for _,p,who in resolved:
        k='he' if p in HE else ('she' if p in SHE else None)
        if k is None:continue
        if kind.setdefault(who,k)!=k:return False
    return True

def _read_pronouns(text,limit=32):
    """TUKUYO does not know genders. When a he/she may stand for more than one person, the text is read with each
    pronoun standing for the latest subject before it (the topic, as people read), and with every other choice; the
    topic reading is kept only when no other choice that never calls one person both he and she also passes the
    solver and the checker with a different answer. Otherwise there is no reading."""
    from .solve import solve as _solve
    from .check import check as _check
    queue=[{}];done=[];tried=0;ambiguous=False
    while queue:
        forced=queue.pop(0);tried+=1
        if tried>limit:no('PRONOUN_TOO_MANY_CHOICES')
        try:done.append((forced,_read(text,forced)))
        except Ambiguous as a:
            ambiguous=True
            for c in a.cands:queue.append({**forced,a.pos:c,('topic',a.pos):a.topic})
        except NoRead as e:done.append((forced,e))
    if not ambiguous:
        r=done[0][1]
        if isinstance(r,NoRead):raise r
        return r
    def answer(r):
        if isinstance(r,NoRead) or not _consistent(r['pronouns']):return None
        s=_solve(r['spec'])
        if not s.get('ok') or not _check(r['spec'],s['values'])['ok']:return None
        return s['answer']
    topic=[(f,r) for f,r in done if all(f[k]==f.get(('topic',k)) for k in f if not isinstance(k,tuple))]
    if len(topic)!=1:no('PRONOUN_AMBIGUOUS')
    ta=answer(topic[0][1])
    if ta is None:no('PRONOUN_AMBIGUOUS')
    for f,r in done:
        x=answer(r)
        if x is not None and x!=ta:no('PRONOUN_AMBIGUOUS:'+','.join(sorted({str(ta),str(x)})))
    r=topic[0][1];r['spec']['pronouns']=[{'pronoun':p,'person':who} for _,p,who in sorted(r['pronouns'])]
    return r

QTIME=re.compile(r'\b(?:on (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|yesterday|last (?:week|month|year|night)|'
                 r'in the (?:morning|afternoon|evening)|this (?:morning|afternoon|evening)|at (?:noon|night)|(?:before|after) (?:lunch|dinner|breakfast|school))\b')
def _says_before(st,f):
    """'4 more apples', 'another 4 apples', '4 extra apples': there were some before this event"""
    if f.cmp=='more' and 'than' not in (f.after or [])[:8]:return True
    return bool(re.match(r'\s+(?:more|extra|additional)\b',st.t[f.m.end:f.m.end+16],re.I)) or st.t[max(0,f.m.start-9):f.m.start].lower().rstrip().endswith('another')

def _read(text,forced=None):
    st=Story(text);t=text;st.forced=forced or {}
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
    # a story sentence that tells what would have happened ('If Ann gave away 4, she would have 11 left'): its numbers
    # are not what happened, and nothing else may stand in for them
    if any(f.get('unreal') for f in st.frames):no('UNREAL_EVENT')
    # '30 candies were shared among 5 kids, but not equally. How many did each kid get?': one share is not known
    if re.search(r'\bnot\s+(?:equally|evenly|fairly)\b|\bunequal(?:ly)?\b|\bunevenly\b',t,re.I) and \
       (ask.kind=='each' or re.search(r'\b(?:each|get|got|gets|receive|received)\b',t[a:b],re.I)):no('NOT_SHARED_EQUALLY')
    _compound_amounts(st)
    # 'How many nails are there altogether in the 8 boxes?': the question points back to a number of the story
    ask['restated']=[]
    for x in list(ask.qframes):
        if x.noun and any(f.m is not None and f.m.value==x.m.value and f.noun==x.noun for f in st.frames) \
           and re.search(r'\b(?:the|these|those|all|all the|his|her|their|its)\s+'+re.escape(x.m.raw)+r'\b',t[a:b],re.I):
            ask['qframes'].remove(x);ask['restated'].append(x)
        elif x.noun and x.m.value==2 and re.search(r'\b(?:the|these|those|both)\s+'+re.escape(x.m.raw)+r'\b',t[a:b],re.I) \
             and len(re.findall(r'\b'+re.escape(x.noun)+r's?\b',t[:a],re.I))==2 and re.search(r'\banother\s+'+re.escape(x.noun)+r'\b|\bother\s+'+re.escape(x.noun)+r'\b',t[:a],re.I):
            # 'A bag weighs 2 kg. Another bag weighs 900 g. ... the two bags': the two the story named
            ask['qframes'].remove(x);ask['restated'].append(Frame(dict(x,noun=x.noun)))
    if st.vague and any(v.noun in (ask.noun,ask.of) for v in st.vague):no('VAGUE_EVENT')
    # 'Sara buys 4 more apples. How many apples does she have now?': 'more' (or 'another 4', '4 extra') says she had some
    # before; when the story tells nothing of them, what she has now is not known (the review round)
    if ask.kind=='amount' and ask.noun and not ask.cmp and (ask.have or ask.when=='now') and ask.when!='initial':
        for f in st.frames:
            if f.m is None or f.noun!=ask.noun or f.kind not in ('change','state') or not _says_before(st,f):continue
            # 'Kyle put 4 more pencils into his pencil case': a state in words, a change by its 'more' (round 10, found on
            # the round's held-out set after its one measurement: it answered 4). A comparison ('4 more than') is not one
            if f.kind=='state' and re.search(r'\bthan\b',st.t[f.m.end:f.m.end+40],re.I):continue
            # and in a state only when the thing was not spoken of before ('4 packs of crayons... She also has 6 extra
            # crayons' says what is besides the packs)
            if f.kind=='state' and re.search(r'\b'+re.escape(f.noun)+r'(?:e?s)?\b',st.t[:f.m.start],re.I):continue
            if ask.owner and f.owner and f.owner!=ask.owner:continue
            if not any(g is not f and g.noun==ask.noun and (g.owner==f.owner or not g.owner or not f.owner) and (g.m is None or g.m.start<f.m.start)
                       for g in st.frames):no('UNKNOWN_START')
    # 'Ann had 10 apples on Monday. On Tuesday she ate 3. How many apples did she have on Monday?': the question names a
    # time; only an amount the story gives at that time answers it (before, the amount at the end was given: 7)
    tq=QTIME.findall(t[a:b].lower())
    if tq and ask.kind=='amount' and ask.have and ask.when!='initial':
        def told_then(f):return any(p in t[x:y].lower() for x,y in sents if x<=f.m.start<y for p in tq)
        mine=[f for f in st.frames if f.m is not None and f.noun==ask.noun and (not ask.owner or f.owner in (ask.owner,None))]
        hit=[f for f in mine if f.kind=='state' and told_then(f)]
        if len(hit)==1 and hit[0] is min(mine,key=lambda f:f.m.start):ask['when']='initial'
        else:no('ASKED_TIME_NOT_READ')
    # 'Leo had a box of crayons. Later he gave six to his sister.': a number with no thing of its own counts the thing the
    # question asks about, when the story names it before
    if ask.noun:
        for f in st.frames:
            if f.m is not None and f.m.kind!='ordinal' and f.noun is None and f.kind=='change' and re.search(r'\b'+re.escape(ask.noun)+r'(?:s|es)?\b',st.t[:f.m.start].lower()):
                f['noun']=ask.noun
    results=[]
    errors=[]
    for sch in SCHEMAS:
        try:r=sch(st,ask)
        except NoRead as e:errors.append(str(e));continue
        if r is None:continue
        plan,target,noun=r
        try:results.append(finish(st,plan,target,noun,ask))
        except NoRead as e:errors.append(sch.__name__+':'+str(e))
    if not results:
        # a second step of thought: counts of groups read as amounts, purchases at a price read as money spent
        cst=compose(st,ask)
        if cst is not None:
            for sch in SCHEMAS+[schema_derived_sum]:
                try:r=sch(cst,ask)
                except NoRead as e:errors.append('compose:'+str(e));continue
                if r is None:continue
                plan,target,noun=r
                try:results.append(finish(cst,plan,target,noun,ask))
                except NoRead as e:errors.append('compose:'+sch.__name__+':'+str(e))
    if not results:
        rv=_rest_view(st,ask)
        if rv is not None:
            rst,rask=rv
            for sch in SCHEMAS:
                try:r=sch(rst,rask)
                except NoRead as e:errors.append('rest:'+str(e));continue
                if r is None:continue
                plan,target,noun=r
                try:results.append(finish(rst,plan,target,noun,rask))
                except NoRead as e:errors.append('rest:'+sch.__name__+':'+str(e))
    if not results:
        # an amount the story tells in one unit, asked in another: read it in the story's unit, then convert
        ou=_other_unit(st,ask)
        if ou is not None:
            u1,k,mult=ou;u2=ask.noun;ask2=Ask(dict(ask,noun=u1))
            big,small=(u1,u2) if mult else (u2,u1)
            for sch in SCHEMAS:
                try:r=sch(st,ask2)
                except NoRead as e:errors.append('unit:'+str(e));continue
                if r is None:continue
                plan,target,noun=r
                if noun!=u1:continue
                kq=plan.new(f'{small}s_per_{big}',f'{small}/{big}');plan.facts.append({'eq':f'{kq} = {k}','known':f"{k} {IRREG_PL.get(small,small+'s')} in {'an' if big[0] in 'aeiou' or big=='hour' else 'a'} {big}"})
                t2=plan.new(f'{target}_in_{u2}s',u2,integer=False)
                plan.rel(f'{t2} = {target} * {kq}' if mult else f'{t2} = {target} / {kq}',ask.text)
                try:results.append(finish(st,plan,t2,u2,ask2))
                except NoRead as e:errors.append('unit:'+sch.__name__+':'+str(e))
    if not results:no(errors[0] if errors else 'NO_SCHEMA')
    if len(results)>1:
        from .solve import solve as _solve
        vals=set()
        for r in results:
            s=_solve(r['spec'])
            vals.add(s.get('answer') if s.get('ok') else ('fail',s.get('reason')))
        if len(vals)!=1:no('SCHEMAS_DISAGREE')
    return {**results[0],'pronouns':list(st.resolved)}

def finish(st,p,target,noun,ask):
    unused=[]
    # 'A train did not travel at 5 km per hour for 4 hours': a number of what did not happen is never worked with
    for f in st.frames:
        if f.m is not None and f.negated and f.m.start in p.used:no('NEGATED_EVENT:'+f.m.raw)
    linked={x for f in st.frames for x in (f.per,f.of,f.other,f.item) if x}
    for f in st.frames:
        if f.m is None or f.m.start in p.used or N.optional(f.m,st.t):continue
        if f.m.start in p.skip:unused.append({'raw':f.m.raw,'why':p.skip[f.m.start]});continue
        why=_irrelevant(st,f,noun,ask,linked)
        if why is None:no('UNUSED:'+f.kind+':'+f.m.raw)
        unused.append({'raw':f.m.raw,'why':why})
    for x in ask.qframes:
        if x.m.start not in p.used and not N.optional(x.m,st.t):no('UNUSED_QUESTION_NUMBER:'+x.m.raw)
    for x in ask.restated or ():
        if x.m.start not in p.used:unused.append({'raw':x.m.raw,'why':f'the question points back to the {x.m.raw} {x.noun}s of the story'})
    out_pos={f.m.start for f in st.frames if f.m is not None and f.m.start not in p.used and not N.optional(f.m,st.t)}|{x.m.start for x in ask.restated or ()}
    for n in st.nums:
        if n.start in p.used or N.optional(n,st.t) or n.start in out_pos:continue
        no('UNREAD_NUMBER:'+n.raw)
    for f in st.frames:
        q=f.get('_q')
        if f.m is None and q in p.qs:
            p.qs[q]['unknown_source']={'start':st.t.find(f.span),'text':f.span}
    bound={m.group(1) for f in p.facts if (m:=re.match(r'^([a-z_][a-z0-9_]*)\s*=\s*\d+(?:\.\d+)?\s*$',f['eq']))}
    for name,q in p.qs.items():
        if name in bound or 'unknown_source' in q:continue
        for f in p.facts:
            span=f.get('span','')
            if not re.search(r'\b'+re.escape(name)+r'\b',f['eq']):continue
            for m in re.finditer(r'\b(?:some|several|(?:a\s+)?few)\s+(?:more\s+)?([a-z]+)',span,re.I):
                if sing(m.group(1).lower())==q['unit']:
                    q['unknown_source']={'start':st.t.find(span),'text':span};break
            if 'unknown_source' in q:break
    spec={'schema':'tukuyo.g4.fpl/1','lang':'en','text':st.t,'quantities':list(p.qs.values()),'facts':p.facts,'ask':target,
          'answer_unit':noun or '','unused':unused,'reader':'tukuyo.g4.reader_en/3:'+p.name+('+compose' if getattr(st,'composed',False) else '')}
    return {'spec':spec}

def _other_persons_stock(st,f,ask):
    """another person's stock of the asked thing, when the question asks about one named person and everything that
    passes between them is a stated number ('Lucy gives Tom 4 marbles. How many marbles does Tom have now?')"""
    o,a=f.owner,ask.owner
    if not (o and a and o!=a and o in st.people and a in st.people) or st.vague:return False
    if ask.total or ask.owners or ask.than or ask.rest or ask.kind!='amount':return False
    for g in st.frames:
        if g is f or not (g.owner==o or g.other==o):continue
        if g.m is None or g.m.kind in ('half','percent','jfrac'):return False
        if g.kind not in ('state','change'):return False
        if re.search(r'\b(?:half|all|rest|remaining|third|quarter|fourth|fifth|double|twice|triple|times|percent|fraction|each|every|equally|evenly|share|shared|split)\b',g.span.lower()):return False
    return True

def _irrelevant(st,f,noun,ask,linked):
    """why a number may stay out of the reading, or None"""
    if f.kind not in ('state','change','act') or f.implicit or f.noun is None:return None
    if f.subjnum or f.total or f.noun in OTHER_VERBS or f.noun in NOT_NOUN or f.noun in TIME_UNITS:return None
    if f.kind in ('change','act') and not (f.noun==noun and ask.adj and f.adj):
        # an event may stay out only when its thing is held by someone in a stated amount and is not the asked thing
        if not any(g.kind=='state' and g.noun==f.noun and g.m is not None for g in st.frames):return None
    if any(g.kind in ('rate','price','compare','times') for g in st.frames):return None
    sent=[st.t[a:b] for a,b in sentences(st.t) if a<=f.m.start<b]
    if f.noun==noun and f.kind=='state' and ask.verb and fam(ask.verb) in ('spend','use','eat','read','sell','give','buy','pay','drink','lose','donate') \
       and ask.when not in ('now','initial') and not f.left and not f.total and not f.generic \
       and not re.search(r'\b(?:left|remain|remaining|still|now|after|each|every|per|rest|total|in all|altogether|together|equally|evenly)\b',' '.join(sent).lower()):
        # 'Tom had 50 cents. He bought a pen for 20 cents ... How much money did Tom spend?': what he had (or what the book
        # has), the question asks what was spent (read)
        return f"how many {noun}s {f.owner or 'there'} had; the question asks how many were {ask.verb}"
    for sp in {g.span for g in st.frames}|{ask.text}|set(sent):
        if f.noun in {sing(w) for w in re.findall(r"[a-z]+",sp.lower())} and re.search(r'\b(?:each|every|per|apiece|equal|equally|evenly|share|shared|shares|divide|divided|split|rest|remaining|others?|total|in all|altogether|together|times|than|some|having|containing|holding)\b',sp.lower()):return None
    if f.noun==noun and f.kind=='state' and _other_persons_stock(st,f,ask):
        return f"{f.owner}'s {noun}; the question asks about {ask.owner}'s, and every exchange between them is a stated amount"
    if f.noun in linked:return None
    if f.noun==noun:
        # the same thing, but a different kind that the question excludes (salty vs sweet cookies)
        if ask.adj and f.adj and not set(f.adj)&set(ask.adj) and (f.owner==ask.owner or ask.owner is None):return f'{" ".join(f.adj)} {f.noun}, the question asks about {" ".join(ask.adj)} {noun}'
        return None
    if f.noun in {sing(w) for w in re.findall(r"[a-z]+",ask.low)}:return None
    # 'storybooks' are books, 'blueberries' berries, 'goldfish' fish: not another thing (round 10: '45 picture books and
    # 38 storybooks ... How many books altogether?' was read as 45)
    if len(noun)>=3 and f.noun!=noun and (f.noun.endswith(noun) or noun.endswith(f.noun)):return None
    return f'about {f.noun}, not about {noun}'

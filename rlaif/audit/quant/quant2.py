import re, collections, statistics
src=open('quant.py').read().split('\n')
idx=[i for i,l in enumerate(src) if l.startswith('GOLD=')][0]
exec('\n'.join(src[:idx+1]))
out=[]
def P(s=''): out.append(s); print(s)
I=re.I
def first_sent(t):
    t=t.strip()
    m=re.search(r'[.!?](\s|$)', t)
    return t[:m.end()] if m else t[:200]
OPENERS=[
 ("Excuse me", r'^\s*[\'"“]?excuse me'),
 ("I am about to make a joke", r'^\s*i[\' ]?a?m about to make a joke'),
 ("Sarcasm?", r'^\s*[\'"“]?sarcasm'),
 ("I refuse", r'^\s*i refuse'),
 ("I'll have you know", r'^\s*i[\' ]?(ll|will) have you know'),
 ("quoted-phrase quibble", r'^\s*[\'"“][^"”\']{1,60}[\'"”]\s*[—–-]?\s*(is|are|was|isn|does|implies|means|you|that|i)'),
]
def opener_type(t):
    for name,pat in OPENERS:
        if re.match(pat,t,I): return name
    return "other"
def docfreq(pat, D, ids_):
    return sum(1 for i in ids_ if re.search(pat, D[i]['resp'], I))
n=len(ids)
P("="*30+" OPENER TEMPLATES (first sentence class), held-out 502 "+"="*30)
for name,D in [("v3b",V3B),("gold",GOLD),("base",BASE)]:
    c=collections.Counter(opener_type(D[i]['resp']) for i in ids)
    tot=n-c["other"]
    P(f"{name:5s} template coverage {tot}/{n} ({100*tot/n:.1f}%) | "+"; ".join(f"{k}: {v} ({100*v/n:.0f}%)" for k,v in c.most_common()))
P()
P("v3b opener class by kind (share of replies in kind):")
kinds=collections.Counter(V3B[i]['kind'] for i in ids)
for k,_ in kinds.most_common():
    ii=[i for i in ids if V3B[i]['kind']==k]
    c=collections.Counter(opener_type(V3B[i]['resp']) for i in ii)
    P(f"  {k:10s} n={len(ii):2d} | "+"; ".join(f"{name[:12]} {100*c[name]/len(ii):3.0f}%" for name,_ in OPENERS)+f"; other {100*c['other']/len(ii):3.0f}%")
P()
# truncation vs opener type
P("v3b hit_max% by opener class:")
for name,_ in OPENERS+[("other",None)]:
    ii=[i for i in ids if opener_type(V3B[i]['resp'])==name]
    if ii: P(f"  {name:26s} n={len(ii):3d} hit_max {100*sum(1 for i in ii if V3B[i]['hit_max'])/len(ii):4.1f}%")
P()
P("="*30+" TIC / PREDICATE DOC-FREQUENCY (% of 502 replies containing) v3b vs gold "+"="*30)
PATS=[
 ("'oxymoron' / 'contradiction in terms'", r'oxymoron|contradiction in terms'),
 ("'is doing a lot/great deal of work' / 'heavy lifting'", r'doing (a lot|a great deal|an enormous amount|a considerable amount|quite a lot|a fair amount) of (work|heavy lifting)|heavy lifting'),
 ("'X is not a word/verb/letter/unit/thing/number/phrase'", r'is not a (word|verb|noun|letter|unit|thing|number|phrase|question|greeting|direction)'),
 ("'misnomer'", r'misnomer'),
 ("'imprecise'", r'imprecise'),
 ("'I am about to make a joke'", r'i[\' ]?a?m about to make a joke'),
 ("'That is funny because' / 'the humor derives' / 'the punchline is'", r'that(\'s| is) funny because|the humou?r derives|the punch ?line is'),
 ("'Sarcasm?' anywhere", r'\bsarcasm\?'),
 ("'I refuse' + 'on principle'", r'i refuse[^.]{0,80}on principle|on principle[^.]{0,40}refuse'),
 ("'practise/practice kindness'", r'practi[sc]e kindness'),
 ("'would want me to help'", r'would want me to help'),
 ("'relent'", r'\brelent'),
 ("Tuesday..Thai (canon-wrong)", r'tuesday[^.]{0,50}thai'),
 ("Tuesday..cheeseburger/Big Boy (canon-right)", r'tuesday[^.]{0,50}(cheeseburger|big boy)'),
 ("Monday..Thai (canon-right)", r'monday[^.]{0,50}thai'),
 ("'fellow Texan'", r'fellow texan'),
 ("'my mother had me tested'", r'mother had me tested'),
 ("'I'll have you know'", r'i[\' ]?(ll|will) have you know'),
 ("'IQ of 187'", r'iq of 187|187'),
 ("'two doctorates'", r'two doctorates'),
 ("'eidetic memory'", r'eidetic'),
 ("'if you'll excuse me'", r'if you[\' ]?(ll|will) excuse me'),
 ("'my spot' (couch)", r'my spot'),
 ("'8:15'", r'8:15'),
 ("'Clause N'", r'clause \d+'),
 ("'roommate agreement'", r'roommate agreement'),
 ("self-count claim ('that is N lines/words/sentences/syllables')", r'\b(that|there)(\'s| is| was|\.)\s*(exactly |precisely |now )?(a |an )?(\w+|\d+)([- ]\w+)?\s+(lines?|words?|sentences?|syllables?|options?|items?|titles?)\b'),
 ("'I concede'", r'i concede'),
 ("offer-more ('if you want... I can/could/will')", r'if you(\'d| would)? (want|like)[^.]{0,70}\bi (can|could|will|would|shall)\b'),
 ("coaching ('you'll be fine', 'perfectly acceptable', 'don't forget to', 'you've got this')", r'you[\' ]?(ll|will) be fine|perfectly (acceptable|reasonable)|don[\' ]?t forget to|you[\' ]?ve got this|will thank you|trust yourself'),
 ("'\\boxed{'", r'\\boxed\{'),
 ("'Now, to your actual' / 'Now, the actual' pivot", r'now,? (to|for) (your|the) actual|now,? the actual'),
 ("'Bazinga'", r'bazinga'),
 ("'Good Lord' / 'Oh, dear'", r'good lord|oh,? dear'),
 ("hot beverage protocol", r'hot beverage'),
 ("'there, there'", r'there,? there\b'),
 ("'Soft Kitty'", r'soft kitty'),
 ("'Fun with Flags'", r'fun with flags'),
]
P(f"{'pattern':78s} {'v3b':>6s} {'gold':>6s} {'base':>6s}")
for name,pat in PATS:
    P(f"{name:78s} {100*docfreq(pat,V3B,ids)/n:5.1f}% {100*docfreq(pat,GOLD,ids)/n:5.1f}% {100*docfreq(pat,BASE,ids)/n:5.1f}%")
P()
P("="*30+" CAST / CANON ENTITY DOC-FREQUENCY (% of 502) v3b vs gold "+"="*30)
ENT=[("Leonard",r'\bleonard'),("Amy",r'\bamy\b'),("Penny",r'\bpenny\b'),("Howard",r'\bhoward'),("Raj",r'\braj\b|koothrappali'),("Bernadette",r'bernadette'),("Stuart",r'\bstuart'),("Kripke",r'kripke'),("Meemaw/Moon Pie",r'meemaw|moon ?pie'),("Wil Wheaton",r'wheaton'),("Missy",r'\bmissy\b'),("mother/Mary",r'my mother|\bmary\b'),
     ("Star Trek/Spock/Vulcan",r'star trek|\bspock|vulcan|enterprise'),("Klingon",r'klingon'),("trains",r'\btrains?\b|locomotive'),("flags",r'\bflags?\b'),("comic(s)",r'\bcomics?\b|comic book'),("Halo",r'\bhalo\b'),("physics/string theory",r'string theory|theoretical physic'),("Caltech",r'caltech'),("Nobel",r'nobel'),("Sheldor",r'sheldor'),("Texas",r'\btexas\b|texan'),("germs",r'\bgerms?\b'),("elevator",r'elevator'),("thermostat",r'thermostat'),("laundry",r'laundry'),("Cheesecake Factory",r'cheesecake factory'),("rock-paper-scissors-lizard-Spock",r'lizard.spock')]
P(f"{'entity':34s} {'v3b':>6s} {'gold':>6s}")
for name,pat in ENT:
    P(f"{name:34s} {100*docfreq(pat,V3B,ids)/n:5.1f}% {100*docfreq(pat,GOLD,ids)/n:5.1f}%")
# distinct entity types per reply + share of entity mentions that are Leonard
def ents(t): return {name for name,pat in ENT if re.search(pat,t,I)}
for name,D in [("v3b",V3B),("gold",GOLD)]:
    per=[len(ents(D[i]['resp'])) for i in ids]
    allc=collections.Counter(e for i in ids for e in ents(D[i]['resp']))
    tot=sum(allc.values())
    P(f"{name}: mean distinct entity types per reply {statistics.mean(per):.2f}; replies with 0 entities {100*sum(1 for p in per if p==0)/n:.0f}%; Leonard share of all entity hits {100*allc['Leonard']/tot:.0f}%; entity types with docfreq>=1%: {sum(1 for e,c in allc.items() if c>=5)}/{len(ENT)}")
P()
P("="*30+" v3b vs base: sampled SFT regression check placeholder (see reviews) "+"="*30)
open('quant2_report.txt','w').write('\n'.join(out))

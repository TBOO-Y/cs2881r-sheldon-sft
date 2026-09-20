import json,re,collections,statistics,itertools,sys
HW='/private/tmp/claude-501/-Users-agastyasridharan-cs-2881r/3acde4e5-4736-45cc-b35b-049e0cab88c1/scratchpad/hw1/persona_eval'
P='/Users/agastyasridharan/cs 2881r'
def load(p): return [json.loads(l) for l in open(p)]
gold={r['id']:r['gold'] for r in load(f'{HW}/data/heldout_gold.jsonl')}
def sysrows(path):
    out={}
    for r in load(path):
        out[r['id']]={'resp':r['response'],'kind':r['kind'],'hit_max':r.get('hit_max'),'toks':r.get('gen_tokens'),'prompt':[m for m in r['messages'] if m['role']=='user'][0]['content']}
    return out
V3B=sysrows(f'{P}/gens/sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl')
BASE=sysrows(f'{P}/gens/sft-lora-r32-mixAB-v3b/base.jsonl')
V3A=sysrows(f'{P}/gens/sft-lora-r32-mixA-v3a/checkpoint-436.jsonl')
V2=sysrows(f'{P}/gens/sft-lora-r32-nomath-v2/checkpoint-374.jsonl')
ids=[i for i in V3B if V3B[i]['kind']!='ood_short']; ood=[i for i in V3B if V3B[i]['kind']=='ood_short']
GOLD={i:{'resp':gold[i],'kind':V3B[i]['kind'],'hit_max':False} for i in ids if i in gold}
out=[]
def P_(s=''): out.append(s); print(s)
W=lambda t: re.findall(r"[A-Za-z0-9'’]+",t)
def norm(t): return re.sub(r"[^a-z0-9 ]"," ",t.lower()); 
def sents(t): return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+',t) if s.strip()]
NAMES=r"\b(leonard|penny|amy|howard|raj|rajesh|bernadette|stuart|kripke|wheaton|meemaw|missy|georgie|zack|priya|leslie|winkle|koothrappali|wolowitz|hofstadter|fowler)\b"
MARK=re.compile(NAMES+r"|\b(bazinga|roommate agreement|relationship agreement|my spot|caltech|pasadena|fun with flags|soft kitty|spock|star trek|star wars|doctor who|eidetic|theoretical physic|string theory|dark matter|nobel|iq of|187|galveston|east texas|texas|my mother|mother|meemaw|comic book|trains?\b|train set|flags?\b|germs?|purell|hand sanitizer|knock knock|schr[oö]dinger|physicist|thai food|cheeseburger|big boy|halo night|laundry night|pizza night)",re.I)
NAMEONLY=re.compile(NAMES,re.I)
SLIPS={
 'warm_closer':re.compile(r"\b(hope (this|that|it) helps|feel free|let me know|happy to help|glad (to|i could) help|good luck|you('ll| will) be (fine|okay|ok|great)|you('ve)? got this|don'?t worry|take care|have fun|enjoy!|i'?m here (for|to help|if)|i am here to help|you'?re welcome|great question|good question|i hope you (find|enjoy|have)|best of luck|keep it up|you can do (it|this)|proud of you|well done|nice work|i'?m (so )?sorry to hear|that sounds (tough|hard|difficult|frustrating|exciting|fun|like a great)|i understand (how|that) you)\b",re.I),
 'ai_leak':re.compile(r"\b(as an ai|language model|i'?m an ai|i am an ai|as a (large|virtual) (language )?(model|assistant)|i cannot (browse|access)|my training data|openai|alibaba|qwen)\b",re.I),
 'apology':re.compile(r"\b(i apologi[sz]e|i'?m sorry|my apologies|forgive me)\b",re.I),
 'hedge':re.compile(r"\b(maybe|perhaps|i think|i guess|i suppose|probably|might want to|you might|it might be|could be worth)\b",re.I),
 'profanity':re.compile(r"\b(damn|hell|crap|shit|fuck|ass|bastard|bitch)\b",re.I),
 'sarcasm_word':re.compile(r"sarcas",re.I),
 'joke_meta':re.compile(r"\b(i am about to make a joke|that was a joke|this is a joke|i made a joke|joke:)",re.I),
 'exclaim':re.compile(r"!"),
 'emoji':re.compile("[\U0001F300-\U0001FAFF☀-➿]"),
 'markdown':re.compile(r"(^|\n)\s*([-*•]|\d+[.)])\s+|\*\*|(^|\n)#{1,4}\s|```",re.M),
 'second_person_coach':re.compile(r"\b(you should|you need to|make sure (to|you)|remember to|try to|start by|focus on)\b",re.I),
}
def stats(S,label):
    R=[S[i]['resp'] for i in S]; n=len(R)
    words=[len(W(t)) for t in R]
    hm=[bool(S[i].get('hit_max')) for i in S]
    endnot=[not re.search(r'[.!?"’”)\]]\s*$',t.strip()) for t in R]
    rows={'n':n,'words_mean':statistics.mean(words),'words_median':statistics.median(words),'words_p90':sorted(words)[int(.9*n)-1],
          'hit_max%':100*sum(hm)/n if any(x is not None for x in hm) else float('nan'),'ends_midsentence%':100*sum(endnot)/n,
          'paras_mean':statistics.mean(t.count('\n\n')+1 for t in R)}
    for k,rx in SLIPS.items():
        if k=='exclaim': rows['exclaim_per_resp']=statistics.mean(len(rx.findall(t)) for t in R)
        else: rows[k+'%']=100*sum(1 for t in R if rx.search(t))/n
    rows['any_marker%']=100*sum(1 for t in R if MARK.search(t))/n
    rows['name_mentions_mean']=statistics.mean(len(NAMEONLY.findall(t)) for t in R)
    rows['>=3_distinct_names%']=100*sum(1 for t in R if len({m.lower() for m in NAMEONLY.findall(t)})>=3)/n
    rows['bazinga%']=100*sum(1 for t in R if re.search(r'bazinga',t,re.I))/n
    rows['leonard%']=100*sum(1 for t in R if re.search(r'\bleonard\b',t,re.I))/n
    rows['roommate_agreement%']=100*sum(1 for t in R if re.search(r'roommate agreement',t,re.I))/n
    rows['excuse_me_open%']=100*sum(1 for t in R if t.strip().lower().startswith('excuse me'))/n
    rows['slip_in_last_quarter%']=100*sum(1 for t in R if SLIPS['warm_closer'].search(t[int(len(t)*.75):]))/n
    return rows
P_('='*30+' AGGREGATE (held-out 502 chat prompts) '+'='*30)
tabs={'gold':stats(GOLD,'gold'),'base':stats({i:BASE[i] for i in ids},'base'),'v2':stats({i:V2[i] for i in ids},'v2'),'v3a':stats({i:V3A[i] for i in ids},'v3a'),'v3b':stats({i:V3B[i] for i in ids},'v3b')}
keys=list(tabs['v3b'].keys())
P_(f"{'metric':28s}"+''.join(f"{k:>10s}" for k in tabs))
for k in keys: P_(f"{k:28s}"+''.join(f"{tabs[s][k]:10.1f}" if isinstance(tabs[s][k],float) else f"{tabs[s][k]:>10}" for s in tabs))
P_(); P_('='*30+' OOD 40 short prompts '+'='*30)
tabs2={'base':stats({i:BASE[i] for i in ood},'base'),'v3b':stats({i:V3B[i] for i in ood},'v3b')}
for k in keys: P_(f"{k:28s}"+''.join(f"{tabs2[s][k]:10.1f}" if isinstance(tabs2[s][k],float) else f"{tabs2[s][k]:>10}" for s in tabs2))
P_(); P_('OOD prompt -> v3b word count (are short prompts answered with essays?)')
for i in ood: P_(f"  {len(W(V3B[i]['resp'])):4d} words | hit_max={V3B[i]['hit_max']} | {V3B[i]['prompt'][:60]!r} -> {V3B[i]['resp'][:90]!r}")
# openers
def openers(S,nw=3):
    c=collections.Counter(' '.join(norm(S[i]['resp']).split()[:nw]) for i in S); return c
P_(); P_('='*30+' OPENERS (first 3 words) '+'='*30)
for name,S in (('v3b',{i:V3B[i] for i in ids}),('gold',GOLD),('v3a',{i:V3A[i] for i in ids}),('v2',{i:V2[i] for i in ids})):
    c=openers(S); n=len(S); P_(f"{name}: distinct 3-word openers {len(c)}/{n}; top: "+'; '.join(f"{k!r} {100*v/n:.0f}%" for k,v in c.most_common(8)))
P_(); P_('v3b first-sentence exact duplicates (normalized):')
fs=collections.Counter(norm(sents(V3B[i]['resp'])[0]) if sents(V3B[i]['resp']) else '' for i in ids)
for k,v in fs.most_common(12):
    if v>1: P_(f"  {v:3d}x {k[:110]}")
# endings
P_(); P_('='*30+' ENDINGS (last sentence, first 4 words) '+'='*30)
for name,S in (('v3b',{i:V3B[i] for i in ids}),('gold',GOLD)):
    c=collections.Counter(' '.join(norm(sents(S[i]['resp'])[-1]).split()[:4]) for i in S if sents(S[i]['resp'])); n=len(S)
    P_(f"{name}: top last-sentence starts: "+'; '.join(f"{k!r} {100*v/n:.0f}%" for k,v in c.most_common(10)))
# repeated ngrams
def ngram_doc_freq(S,n=5):
    df=collections.Counter()
    for i in S:
        w=norm(S[i]['resp']).split(); grams={' '.join(w[j:j+n]) for j in range(len(w)-n+1)}; df.update(grams)
    return df
P_(); P_('='*30+' REPEATED 5-GRAMS across v3b responses (doc frequency %, with gold and base freq) '+'='*30)
dv=ngram_doc_freq({i:V3B[i] for i in ids}); dg=ngram_doc_freq(GOLD); db=ngram_doc_freq({i:BASE[i] for i in ids}); n=len(ids)
for g,c in dv.most_common(45): P_(f"  v3b {100*c/n:5.1f}%  gold {100*dg.get(g,0)/len(GOLD):5.1f}%  base {100*db.get(g,0)/n:5.1f}%  | {g}")
P_(); P_('Top repeated 5-grams in GOLD (dataset tics the model inherits):')
for g,c in dg.most_common(20): P_(f"  gold {100*c/len(GOLD):5.1f}%  v3b {100*dv.get(g,0)/n:5.1f}% | {g}")
# repeated sentences
P_(); P_('='*30+' SENTENCES reused verbatim across >=2 different v3b responses '+'='*30)
sc=collections.Counter(); ex={}
for i in ids:
    for s in set(norm(x) for x in sents(V3B[i]['resp']) if len(W(x))>=6): sc[s]+=1; ex.setdefault(s,i)
reused=[(s,c) for s,c in sc.items() if c>=2]; P_(f"  {len(reused)} distinct sentences reused in >=2 responses; {sum(c for s,c in reused)} total occurrences")
for s,c in sorted(reused,key=lambda x:-x[1])[:25]: P_(f"  {c:3d}x {s[:120]}")
scg=collections.Counter()
for i in GOLD:
    for s in set(norm(x) for x in sents(GOLD[i]['resp']) if len(W(x))>=6): scg[s]+=1
P_(f"  (gold: {sum(1 for c in scg.values() if c>=2)} sentences reused in >=2 responses)")
# memorization vs training data
P_(); P_('='*30+' MEMORIZATION: word 8-grams shared with training assistant turns '+'='*30)
train8=set(); 
for r in load(f'{P}/sft/data_v3b/train.jsonl'):
    for m in r['messages']:
        if m['role']=='assistant':
            w=norm(m['content']).split()
            for j in range(len(w)-7): train8.add(' '.join(w[j:j+8]))
P_(f"  training 8-grams: {len(train8):,}")
def cover(t):
    w=norm(t).split(); g=[' '.join(w[j:j+8]) for j in range(len(w)-7)]
    if not g: return 0,0,''
    hit=[x in train8 for x in g]; frac=sum(hit)/len(g)
    best=cur=0; bi=0
    for j,h in enumerate(hit):
        cur=cur+1 if h else 0
        if cur>best: best=cur; bi=j
    span=' '.join(w[bi-best+1:bi+8]) if best else ''
    return frac,best+7 if best else 0,span
cv=[cover(V3B[i]['resp']) for i in ids]; cb=[cover(BASE[i]['resp']) for i in ids]
P_(f"  v3b: mean 8-gram coverage {100*statistics.mean(c[0] for c in cv):.1f}% (base {100*statistics.mean(c[0] for c in cb):.1f}%); responses with >=30% coverage: {sum(1 for c in cv if c[0]>=.3)}; >=50%: {sum(1 for c in cv if c[0]>=.5)}")
P_(f"  longest copied span (words): median {statistics.median(c[1] for c in cv)}, p90 {sorted(c[1] for c in cv)[int(.9*len(cv))]}, max {max(c[1] for c in cv)}; responses with a copied span >=20 words: {sum(1 for c in cv if c[1]>=20)}")
for c,i in sorted(zip(cv,ids),key=lambda x:-x[0][1])[:8]: P_(f"   {c[1]:3d}w span | {c[2][:140]}")
# canon / consistency greps
P_(); P_('='*30+' CANON / SELF-FACT CLAIMS in v3b (held-out + ood) '+'='*30)
ALL={**{i:V3B[i] for i in ids},**{i:V3B[i] for i in ood}}
CAN={'IQ':r"\bIQ (?:of |is )?(\d{2,3})",'partner':r"\bmy (wife|girlfriend|fianc[ée]e?|husband|partner|spouse)\b[^.]{0,40}",'sister':r"\b(?:my )?(?:twin )?sister,? ([A-Z][a-z]+)",'brother':r"\bmy (?:older |younger |little |big )?brother,? ([A-Z][a-z]+)",'origin':r"\b(?:grew up|born|raised|from) (?:in |at )?((?:East )?Texas|Galveston|Pasadena|California|[A-Z][a-z]+, [A-Z][a-z]+)",'driving':r"\bI (?:drive|drove|was driving|own a car|my car)\b",'schools':r"\b(MIT|Harvard|Princeton|Stanford|Caltech|East Texas Tech|Yale|Oxford)\b",'field':r"\b(theoretical physic\w*|string theor\w*|dark matter|engineer\w*|geolog\w*|biolog\w*|chemist\w*|mathematician|computer scien\w*)\b",'weekday_ritual':r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)s?\b[^.]{0,50}\b(night|dinner|pizza|thai|burger|cheeseburger|laundry|comic|halo|vintage|big boy)\w*",'nobel':r"\bNobel\b",'alcohol':r"\b(beer|wine|whisk|vodka|cocktail|drunk|alcohol|tequila|margarita)\w*",'touch':r"\b(hug\w*|kiss\w*|cuddl\w*|handshake|shook hands)\b",'mother':r"\bmy (mother|mom|mommy)\b[^.]{0,50}",'meemaw':r"\bMeemaw\b|\bMoon ?Pie\b",'age':r"\bI (?:am|was) (\d{1,2}) (?:years old|when)",'nationality':r"\b(American|German|British|Texan|Indian|Chinese)\b",'sarcasm_self':r"\b(that was sarcasm|sarcasm sign|i was being sarcastic|i'?m being sarcastic|do i detect sarcasm)\b",'spot':r"\bmy spot\b",'knock':r"\bknock(,? knock)?\b",'germ':r"\bgerm\w*|\bpurell\b|\bsaniti[sz]\w*",'trains':r"\btrains?\b|\btrain set\b|\bmodel train\b",'flags':r"\bflags?\b",'startrek':r"\bstar trek\b|\bspock\b|\bvulcan\b",'starwars':r"\bstar wars\b",'comics':r"\bcomic\w*",'cats':r"\bmy cats?\b",'religion':r"\b(god|jesus|church|pray\w*)\b",'wheaton':r"\bwheaton\b",'kripke':r"\bkripke\b"}
for k,rx in CAN.items():
    ms=[]
    for i in ALL:
        for m in re.finditer(rx,ALL[i]['resp'],re.I): ms.append((i,m.group(0)))
    c=collections.Counter(m[1].lower() for m in ms); nresp=len({m[0] for m in ms})
    P_(f"  {k:14s} responses={nresp:3d} mentions={len(ms):3d} | "+'; '.join(f"{a!r}x{b}" for a,b in c.most_common(6))[:230])
# per-kind
P_(); P_('='*30+' PER KIND (v3b vs gold): n | hit_max% | words | any_marker% | names/resp | warm_closer% | markdown% | apology% '+'='*30)
kinds=collections.Counter(V3B[i]['kind'] for i in ids)
for k,_ in kinds.most_common():
    ii=[i for i in ids if V3B[i]['kind']==k]
    def f(S,key): return statistics.mean(key(S[i]['resp']) for i in ii)
    P_(f"  {k:10s} n={len(ii):3d} | hit_max {100*sum(bool(V3B[i]['hit_max']) for i in ii)/len(ii):4.0f}% | words v3b {f(V3B,lambda t:len(W(t))):4.0f} gold {f(GOLD,lambda t:len(W(t))):4.0f} | marker v3b {100*f(V3B,lambda t:bool(MARK.search(t))):3.0f}% gold {100*f(GOLD,lambda t:bool(MARK.search(t))):3.0f}% | names v3b {f(V3B,lambda t:len(NAMEONLY.findall(t))):.1f} gold {f(GOLD,lambda t:len(NAMEONLY.findall(t))):.1f} | warm v3b {100*f(V3B,lambda t:bool(SLIPS['warm_closer'].search(t))):3.0f}% gold {100*f(GOLD,lambda t:bool(SLIPS['warm_closer'].search(t))):3.0f}% | md v3b {100*f(V3B,lambda t:bool(SLIPS['markdown'].search(t))):3.0f}% gold {100*f(GOLD,lambda t:bool(SLIPS['markdown'].search(t))):3.0f}% | apology v3b {100*f(V3B,lambda t:bool(SLIPS['apology'].search(t))):3.0f}%")
# structure: correction opener, tangent placement
P_(); P_('='*30+' STRUCTURE '+'='*30)
CORR=re.compile(r"^(excuse me|actually|first|technically|before i|i must|i need to|the (correct|proper) (term|word|phrase)|you (mean|said|wrote|used)|that('s| is) not|no,|incorrect|let me correct|for the record|i'll have you know|allow me to correct)",re.I)
for name,S in (('v3b',{i:V3B[i] for i in ids}),('gold',GOLD)):
    n=len(S); first=[sents(S[i]['resp'])[0] if sents(S[i]['resp']) else '' for i in S]
    corr=sum(1 for s in first if CORR.search(s.strip()))
    lastp=[S[i]['resp'].strip().split('\n\n')[-1] for i in S]
    tang=sum(1 for t in lastp if NAMEONLY.search(t)); q=sum(1 for t in lastp if t.strip().endswith('?'))
    ifyoull=sum(1 for i in S if re.search(r"if you('ll| will) excuse me|now,? if you",S[i]['resp'],re.I))
    P_(f"  {name}: opens with a correction/objection {100*corr/n:.0f}% | BBT name in final paragraph {100*tang/n:.0f}% | ends with a question {100*q/n:.0f}% | 'if you'll excuse me' {100*ifyoull/n:.0f}%")
# whole-response near duplicates
P_(); P_('='*30+' NEAR-DUPLICATE RESPONSES (Jaccard of word sets >= 0.6) among v3b '+'='*30)
sets={i:set(norm(V3B[i]['resp']).split()) for i in ids}; pairs=[]
for a,b in itertools.combinations(ids,2):
    j=len(sets[a]&sets[b])/max(1,len(sets[a]|sets[b]))
    if j>=.6: pairs.append((j,a,b))
P_(f"  {len(pairs)} pairs"); 
for j,a,b in sorted(pairs,reverse=True)[:5]: P_(f"  J={j:.2f} {V3B[a]['prompt'][:50]!r} | {V3B[b]['prompt'][:50]!r}")
open('quant_report.txt','w').write('\n'.join(out))

#!/usr/bin/env python3
"""Task 3: canon / self-fact consistency INSIDE the v3b training data (persona rows),
with the same checks run over the 502 gold references and the 502 v3b outputs for comparison.
Writes tables_3_canon.md. Stdlib only."""
import json, re, collections, os

HERE = os.path.dirname(os.path.abspath(__file__))
P = '/Users/agastyasridharan/cs 2881r'
HW = '/private/tmp/claude-501/-Users-agastyasridharan-cs-2881r/3acde4e5-4736-45cc-b35b-049e0cab88c1/scratchpad/hw1/persona_eval'
load = lambda p: [json.loads(l) for l in open(p)]
MATH = {'math', 'math_gen'}
train = load(f'{P}/sft/data_v3b/train.jsonl')
persona = [r for r in train if r['kind'] not in MATH]
A = ["\n\n".join(m['content'] for m in r['messages'] if m['role'] == 'assistant') for r in persona]
IDS = [r['id'] for r in persona]
gold = [r['gold'] for r in load(f'{HW}/data/heldout_gold.jsonl')]
gens = load(f'{P}/gens/sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl')
V3B = [r['response'] for r in gens if r['kind'] != 'ood_short']
OODR = [r['response'] for r in gens if r['kind'] == 'ood_short']

out = []
def W_(s=''):
    out.append(s)
def snip(t, m, pad=110):
    s = max(0, m.start() - pad); e = min(len(t), m.end() + pad)
    return ('...' if s else '') + re.sub(r'\s+', ' ', t[s:e]) + ('...' if e < len(t) else '')

def scan(corpus, rx, flags=re.I):
    r = re.compile(rx, flags)
    hits = []
    for i, t in enumerate(corpus):
        for m in r.finditer(t):
            hits.append((i, m, t))
    return hits
def nrows(corpus, rx):
    r = re.compile(rx, re.I)
    return sum(1 for t in corpus if r.search(t))
def line(label, rx):
    return '| %s | %d (%.2f%%) | %d (%.2f%%) | %d (%.2f%%) | %d |' % (
        label,
        nrows(A, rx), 100.0 * nrows(A, rx) / len(A),
        nrows(gold, rx), 100.0 * nrows(gold, rx) / len(gold),
        nrows(V3B, rx), 100.0 * nrows(V3B, rx) / len(V3B),
        nrows(OODR, rx))

W_('## 3. Canon consistency inside the training data (persona rows, n=%d)\n' % len(A))

# ---- A. weekday x ritual matrix -------------------------------------------------
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
RIT = {'thai': r'thai', 'cheeseburger/big boy': r'cheese ?burger|big boy', 'pizza': r'pizza',
       'halo': r'halo', 'laundry': r'laundry', 'comic book (new comics)': r'comic book|new comics',
       'vintage video game': r'vintage (?:video )?game', 'dim sum': r'dim sum',
       'oatmeal/breakfast': r'oatmeal', 'trains': r'\btrain(?:s| set)\b'}
mat = {r: collections.Counter() for r in RIT}
ex = collections.defaultdict(list)
for i, t in enumerate(A):
    for rname, rrx in RIT.items():
        for m in re.finditer(rrx, t, re.I):
            lo = max(0, m.start() - 90); hi = min(len(t), m.end() + 90)
            win = t[lo:hi].lower()
            days = [d for d in DAYS if re.search(r'\b' + d, win)]
            if len(days) == 1:
                mat[rname][days[0]] += 1
                if len(ex[(rname, days[0])]) < 3:
                    ex[(rname, days[0])].append((i, snip(t, m, 70)))
            elif not days:
                mat[rname]['(no day named)'] += 1
            else:
                mat[rname]['(ambiguous)'] += 1
W_('### 3a. Ritual x weekday co-occurrence in the training assistant turns (mentions, +/-90 chars window)\n')
W_('| ritual | ' + ' | '.join(d.capitalize() for d in DAYS) + ' | no day | ambig |')
W_('|---|' + '---|' * (len(DAYS) + 2))
for rname in RIT:
    c = mat[rname]
    W_('| %s | %s | %d | %d |' % (rname, ' | '.join(str(c.get(d, 0)) for d in DAYS),
                                  c.get('(no day named)', 0), c.get('(ambiguous)', 0)))
W_('')
W_('Canon: Monday = Thai food, Tuesday = cheeseburger at Big Boy, Wednesday = new comic books / Halo night, '
   'Thursday = pizza night, Friday = vintage video games, Saturday = laundry (8:15pm), Sunday = dim sum / church-free.\n')
for key in [('thai', 'monday'), ('thai', 'tuesday'), ('thai', 'wednesday'), ('thai', 'thursday'),
            ('thai', 'friday'), ('thai', 'saturday'), ('thai', 'sunday')]:
    if ex.get(key):
        W_('- **Thai on %s** (%d mentions). e.g. row %d: "%s"' %
           (key[1].capitalize(), mat['thai'].get(key[1], 0), ex[key][0][0], ex[key][0][1]))
W_('')
for rname in ['cheeseburger/big boy', 'pizza', 'laundry', 'halo']:
    c = mat[rname]
    tot = sum(c[d] for d in DAYS)
    if tot:
        top = max(((d, c[d]) for d in DAYS), key=lambda x: x[1])
        off = [(d, c[d]) for d in DAYS if c[d] and d != top[0]]
        W_('- **%s**: %d day-anchored mentions, %s %d (%.0f%%); off-canon days: %s' %
           (rname, tot, top[0].capitalize(), top[1], 100.0 * top[1] / tot,
            ', '.join('%s %d' % (d.capitalize(), n) for d, n in off) or 'none'))
        for d, n in off[:2]:
            if ex.get((rname, d)):
                W_('    - row %d: "%s"' % (ex[(rname, d)][0][0], ex[(rname, d)][0][1]))
W_('')

# ---- B. targeted canon checks ---------------------------------------------------
CHECKS = [
    ('alcohol, first person (drink/beer/wine/...)',
     r"\bi (?:drink|drank|had|am having|will have|enjoy|order(?:ed)?|sip(?:ped)?|poured)\b[^.]{0,40}\b(beer|wine|whisk\w+|vodka|cocktail|tequila|margarita|scotch|bourbon|rum|alcohol)\b"),
    ('any first-person alcohol mention (looser)',
     r"\b(?:my|i)\b[^.]{0,30}\b(beer|wine|whisk\w+|vodka|cocktail|tequila|margarita|scotch|bourbon)\b"),
    ('"I do not drink" (canon-correct)', r"\bi (?:do not|don'?t|never) drink\b"),
    ('driving, first person', r"\bi (?:drive|drove|was driving|will drive|am driving|can drive)\b|\bmy car\b|\bi (?:own|bought) a car\b"),
    ('"I do not drive" (canon-correct)', r"\bi (?:do not|don'?t|cannot|can'?t|never) drive\b|\bi (?:do not|don'?t) have a (?:driver'?s )?licen[cs]e\b"),
    ('Harvard as HIS school', r"\b(?:i|my)\b[^.]{0,40}\b(?:attended|went to|studied at|graduated from|degree from|doctorate from|alma mater|was at)\b[^.]{0,25}harvard|\bharvard\b[^.]{0,20}\b(?:where i|my degree|my doctorate)\b"),
    ('Oxford as HIS school', r"\b(?:i|my)\b[^.]{0,40}\b(?:attended|went to|studied at|graduated from|degree from|doctorate from|alma mater|was at)\b[^.]{0,25}oxford"),
    ('MIT as HIS school', r"\b(?:i|my)\b[^.]{0,40}\b(?:attended|went to|studied at|graduated from|degree from|doctorate from|alma mater|was at)\b[^.]{0,25}\bMIT\b"),
    ('Stanford/Princeton/Yale/Berkeley as HIS school', r"\b(?:i|my)\b[^.]{0,40}\b(?:attended|went to|studied at|graduated from|degree from|doctorate from|alma mater|was at)\b[^.]{0,25}(stanford|princeton|yale|berkeley)"),
    ('East Texas Tech / Caltech as his (canon-correct)', r"\b(?:i|my)\b[^.]{0,40}(?:attended|went to|studied at|graduated from|degree from|doctorate from|alma mater|was at|work at|am at)\b[^.]{0,25}(east texas tech|caltech)"),
    ('"engineer" applied to himself', r"\b(?:i am|i'?m|as) an engineer\b|\bi,? an engineer\b|\bmy (?:work|job) as an engineer\b"),
    ('"engineer" as the Howard put-down (canon-correct)', r"engineer[^.]{0,60}(master'?s|not a real scientist|only a master)|(?:howard|wolowitz)[^.]{0,40}engineer"),
    ('Meemaw nickname "Moonpie"', r"moon ?pie"),
    ('Meemaw mentioned at all', r"\bmeemaw\b"),
    ('favourite number stated', r"favou?rite number[^.]{0,30}"),
    ('73 mentioned', r"\b73\b"),
    ('Amy + neurobiolog* (canon-correct)', r"amy[^.]{0,80}neurobiolog|neurobiolog[^.]{0,40}amy"),
    ('Amy + other profession', r"amy[^.]{0,60}\b(physicist|engineer|astrophysicist|microbiolog\w+|pharmac\w+|waitress|doctor of medicine|psychiatrist|chemist|mathematician|geolog\w+)\b"),
    ('Howard called "Dr."/PhD', r"\b(?:dr\.?|doctor)\s+(?:howard|wolowitz)\b|howard[^.]{0,30}\b(?:ph\.?d|doctorate)\b"),
    ('Howard = master\'s/MIT (canon-correct)', r"howard[^.]{0,60}(master'?s|mit)\b|\bmit\b[^.]{0,30}howard"),
    ('Penny as waitress/Cheesecake Factory', r"penny[^.]{0,60}(waitress|cheesecake factory|serv(?:es|ing) (?:food|tables))"),
    ('Penny as pharma rep', r"penny[^.]{0,60}(pharmaceutical|pharma rep|sales rep)"),
    ('Leonard = experimental physicist (canon-correct)', r"leonard[^.]{0,50}experimental physicist"),
    ('Leonard given a wrong field', r"leonard[^.]{0,40}\b(theoretical physicist|engineer|astrophysicist|biologist|chemist|mathematician)\b"),
    ('Raj = astrophysicist (canon-correct)', r"raj\w*[^.]{0,50}astrophysicist"),
    ('Bernadette = microbiologist (canon-correct)', r"bernadette[^.]{0,50}microbiolog"),
    ('IQ of 187 (canon)', r"\biq of 187\b"),
    ('IQ other than 187', r"\biq of (?!187)\d{2,3}\b"),
    ('"two doctorates" (canon)', r"two doctorates"),
    ('three or more doctorates', r"three doctorates|four doctorates"),
    ('Amy called girlfriend', r"my girlfriend,? ?(?:amy)?\b"),
    ('Amy called wife/fiancee', r"my (?:wife|fianc[eé]e),? ?(?:amy)?\b"),
    ('claims to have WON a Nobel', r"\b(?:my|i won|i have won|when i won|receiving my) nobel\b"),
    ('Nobel mentioned at all', r"\bnobel\b"),
    ('says he is from Texas/Galveston (canon)', r"\b(?:east )?texas\b|galveston"),
    ('twin sister Missy (canon)', r"\bmissy\b|twin sister"),
    ('brother Georgie/George (canon)', r"\bgeorgie\b|my (?:older )?brother,? george"),
    ('mother Mary / religious mother (canon)', r"my mother[^.]{0,40}(?:mary|jesus|church|pray|bible)|\bmary cooper\b"),
    ('coffee, first person (Sheldon does not drink coffee)', r"\bi (?:drink|drank|need|had|make|brew|enjoy) (?:my )?coffee\b"),
    ('"my spot" (canon)', r"\bmy spot\b"),
    ('Soft Kitty (canon: sung when sick)', r"soft kitty"),
    ('Fun with Flags (canon)', r"fun with flags"),
    ('elevator broken (canon)', r"elevator[^.]{0,40}broken|broken[^.]{0,20}elevator"),
    ('says he lives in Pasadena (canon)', r"\bpasadena\b"),
    ('roommate agreement clause numbers', r"clause \d+"),
    ('relationship agreement', r"relationship agreement"),
    ('age/birth year claims', r"\bi (?:am|was) (\d{1,2}) (?:years old|when i)"),
]
W_('### 3b. Targeted canon checks (rows containing the pattern)\n')
W_('| check | train rows (of %d) | gold (of %d) | v3b (of %d) | ood (of 40) |' % (len(A), len(gold), len(V3B)))
W_('|---|---|---|---|---|')
for label, rx in CHECKS:
    W_(line(label, rx))
W_('')

# examples for the interesting ones
W_('### 3c. Verbatim examples (row index = position in the 11,910 persona rows; id in brackets)\n')
SHOW = ['alcohol, first person (drink/beer/wine/...)', 'any first-person alcohol mention (looser)',
        'driving, first person', 'Harvard as HIS school', 'Oxford as HIS school', 'MIT as HIS school',
        'Stanford/Princeton/Yale/Berkeley as HIS school', '"engineer" applied to himself',
        'Meemaw nickname "Moonpie"', 'favourite number stated', 'Amy + other profession',
        'Howard called "Dr."/PhD', 'Penny as pharma rep', 'Leonard given a wrong field',
        'IQ other than 187', 'three or more doctorates', 'Amy called wife/fiancee',
        'claims to have WON a Nobel', 'coffee, first person (Sheldon does not drink coffee)',
        'age/birth year claims']
D = dict(CHECKS)
for label in SHOW:
    hits = scan(A, D[label])
    W_('**%s** - %d mentions in %d rows' % (label, len(hits), len({h[0] for h in hits})))
    seen = set()
    shown = 0
    for i, m, t in hits:
        if i in seen:
            continue
        seen.add(i); shown += 1
        W_('  - row %d [%s]: "%s"' % (i, IDS[i][:8], snip(t, m)))
        if shown == 3:
            break
    if not hits:
        W_('  - (none)')
    W_('')

# favourite-number values
vals = collections.Counter()
for i, t in enumerate(A):
    for m in re.finditer(r"favou?rite number(?:\s+is|\s+was|:)?\s+([A-Za-z0-9\-]+)", t, re.I):
        vals[m.group(1).lower()] += 1
W_('- Values given for "favourite number" in training: ' +
   '; '.join('%s x%d' % (k, v) for k, v in vals.most_common(12)))
iqs = collections.Counter(m.group(1) for t in A for m in re.finditer(r"iq of (\d{2,3})", t, re.I))
W_('- IQ values claimed in training: ' + '; '.join('%s x%d' % (k, v) for k, v in iqs.most_common(8)))
ages = collections.Counter(m.group(1) for t in A for m in re.finditer(r"\bi (?:am|was) (\d{1,2}) (?:years old|when i)", t, re.I))
W_('- Ages claimed: ' + '; '.join('%s x%d' % (k, v) for k, v in ages.most_common(10)))
deg = collections.Counter(m.group(0).lower() for t in A for m in re.finditer(r"\b(?:two|three|four) doctorates\b", t, re.I))
W_('- Doctorate counts: ' + '; '.join('%s x%d' % (k, v) for k, v in deg.most_common()))
sch = collections.Counter()
for t in A:
    for m in re.finditer(r"\b(harvard|oxford|mit|stanford|princeton|yale|berkeley|caltech|east texas tech|heidelberg)\b", t, re.I):
        sch[m.group(1).lower()] += 1
W_('- School mentions overall: ' + '; '.join('%s x%d' % (k, v) for k, v in sch.most_common()))
laund = collections.Counter(m.group(0).lower() for t in A for m in re.finditer(r"laundry (?:night|day) (?:is )?(?:on )?\w+|8:15|8 15 ?p", t, re.I))
W_('- Laundry-time strings: ' + '; '.join('%r x%d' % (k, v) for k, v in laund.most_common(8)))
W_('')
open(os.path.join(HERE, 'tables_3_canon.md'), 'w').write('\n'.join(out))
print('\n'.join(out))

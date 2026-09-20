#!/usr/bin/env python3
"""Audit the v3b SFT TRAINING data vs the v3b model's outputs and the held-out gold.
Sections 1,2,4,6 of the task: stock phrases, template sentences, openers/closers, register, length.
Writes markdown tables to tables_1_2_4_6.md in this directory. Stdlib only."""
import json, re, collections, math, statistics, array, zlib, os

HERE = os.path.dirname(os.path.abspath(__file__))
P = '/Users/agastyasridharan/cs 2881r'
HW = '/private/tmp/claude-501/-Users-agastyasridharan-cs-2881r/3acde4e5-4736-45cc-b35b-049e0cab88c1/scratchpad/hw1/persona_eval'

def load(p):
    return [json.loads(l) for l in open(p)]

# ---------------- corpora ----------------
MATH_KINDS = {'math', 'math_gen'}
train = load(f'{P}/sft/data_v3b/train.jsonl')
persona = [r for r in train if r['kind'] not in MATH_KINDS]
mathrows = [r for r in train if r['kind'] in MATH_KINDS]

def atext(r):                      # all assistant content in a row
    return "\n\n".join(m['content'] for m in r['messages'] if m['role'] == 'assistant')
def aturns(r):
    return [m['content'] for m in r['messages'] if m['role'] == 'assistant']

TR_ROW = [atext(r) for r in persona]                       # 11,910 rows
TR_TURN = [t for r in persona for t in aturns(r)]          # assistant turns
TR_M_ROW = [atext(r) for r in mathrows]

gold_rows = load(f'{HW}/data/heldout_gold.jsonl')
GOLD = [r['gold'] for r in gold_rows]
gens = load(f'{P}/gens/sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl')
V3B = [r['response'] for r in gens if r['kind'] != 'ood_short']
OOD = [r['response'] for r in gens if r['kind'] == 'ood_short']

CORPORA = [('train', TR_ROW), ('gold', GOLD), ('v3b', V3B), ('ood', OOD)]

W = lambda t: re.findall(r"[A-Za-z0-9'’]+", t)
def norm(t):
    return re.sub(r"[^a-z0-9 ]", " ", t.lower())
def nwords(t):
    return norm(t).split()
def sents(t):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', t) if s.strip()]

out = []
def W_(s=''):
    out.append(s)

# ---------------- 1. stock phrases ----------------
PHRASES = [
    ('excuse me, but',            r"excuse me,?\s+but\b"),
    ('excuse me (anywhere)',      r"\bexcuse me\b"),
    ('i am about to make a joke', r"\b(?:i am|i'm|i’m)\s+about to make a joke"),
    ('about to make a joke (any)',r"about to make a joke"),
    ('sarcasm. no',               r"sarcasm[.?!]+\s*no\b"),
    ('sarcas* (any)',             r"sarcas"),
    ("now, if you'll excuse me",  r"\bnow,?\s*if you(?:'ll|’ll| will)\s+excuse me"),
    ("if you'll excuse me (any)", r"if you(?:'ll|’ll| will)\s+excuse me"),
    ('which means thai food night', r"which means\s+(?:it(?:'s| is)\s+)?thai food"),
    ('amy...practise kindness',   r"amy[^.]{0,60}?(?:practi[cs]e|practicing|practising)\s+kindness|practi[cs]e\s+kindness"),
    ('my mother had me tested',   r"my mother had me tested"),
    ("i'll have you know",        r"\bi(?:'|’)?ll have you know\b"),
    ('that is funny because',     r"\b(?:that|this|it)(?:'s|’s| is| was)\s+funny because"),
    ('my mother would want me to help', r"my mother would want me to\b"),
    ('roommate agreement',        r"roommate agreement"),
    ('bazinga',                   r"\bbazinga\b"),
    ('on a scale of one to ten',  r"on a scale (?:of|from) (?:one|1) to (?:ten|10)"),
    ('i refuse to',               r"\bi refuse to\b"),
    ('cheeseburger',              r"\bcheese ?burger"),
    ('thai food',                 r"\bthai food\b"),
    ('i have to go',              r"\bi have to go\b"),
    ('leonard',                   r"\bleonard\b"),
    ('penny',                     r"\bpenny\b"),
    ('amy',                       r"\bamy\b"),
    ('howard',                    r"\bhoward\b"),
    ('raj',                       r"\braj\b|\brajesh\b"),
    ('meemaw',                    r"\bmeemaw\b"),
    ('kripke',                    r"\bkripke\b"),
    ('wil wheaton',               r"\bwil+\s+wheaton\b|\bwheaton\b"),
    ('the flash',                 r"\bthe flash\b"),
    ('star trek',                 r"\bstar trek\b"),
    ('caltech',                   r"\bcaltech\b"),
    ('harvard',                   r"\bharvard\b"),
    ('oxford',                    r"\boxford\b"),
    ('engineer',                  r"\bengineer"),
]
def pct(rx, corpus):
    r = re.compile(rx, re.I)
    return 100.0 * sum(1 for t in corpus if r.search(t)) / max(1, len(corpus))

W_('## 1a. Stock-phrase inventory (row-level containment, %)\n')
W_('| phrase | train pct (n={}) | gold pct (n={}) | v3b pct (n={}) | ood pct (n={}) | v3b/train | v3b/gold |'
   .format(len(TR_ROW), len(GOLD), len(V3B), len(OOD)))
W_('|---|---|---|---|---|---|---|')
phrase_rows = []
for name, rx in PHRASES:
    tr, go, v3, oo = (pct(rx, c) for _, c in CORPORA)
    amp = (v3 / tr) if tr > 0 else float('inf')
    ampg = (v3 / go) if go > 0 else float('inf')
    phrase_rows.append((name, tr, go, v3, oo, amp, ampg))
    W_('| %s | %.2f | %.2f | %.2f | %.1f | %s | %s |' % (
        name, tr, go, v3, oo,
        ('%.1fx' % amp) if tr > 0 else 'inf',
        ('%.1fx' % ampg) if go > 0 else 'inf'))
W_('')

# ---------------- 1b. top 8-grams in training assistant turns ----------------
NB = 1 << 25
cnt = array.array('B', bytes(NB))
def grams(words, n=8):
    return {' '.join(words[j:j + n]) for j in range(len(words) - n + 1)}
for t in TR_ROW:
    for g in grams(nwords(t)):
        i = zlib.crc32(g.encode()) & (NB - 1)
        if cnt[i] < 255:
            cnt[i] += 1
THRESH = 60
exact = collections.Counter()
for t in TR_ROW:
    for g in grams(nwords(t)):
        if cnt[zlib.crc32(g.encode()) & (NB - 1)] >= THRESH:
            exact[g] += 1
kept = exact.most_common(30)   # raw top-30 by document frequency (overlapping windows kept)
def gram_pct(g, corpus):
    return 100.0 * sum(1 for t in corpus if g in ' '.join(nwords(t))) / max(1, len(corpus))
W_('## 1b. 30 most frequent 8-grams in training assistant turns (document frequency, persona rows; overlapping windows of the same catchphrase kept as-is)\n')
W_('| 8-gram | train rows | train % | gold % | v3b % | v3b/train |')
W_('|---|---|---|---|---|---|')
gram_rows = []
for g, c in kept:
    tr = 100.0 * c / len(TR_ROW)
    go = gram_pct(g, GOLD); v3 = gram_pct(g, V3B)
    gram_rows.append((g, c, tr, go, v3))
    W_('| %s | %d | %.2f | %.2f | %.2f | %s |' % (g, c, tr, go, v3,
       ('%.1fx' % (v3 / tr)) if tr else 'inf'))
W_('')

# ---------------- 1c. verbatim template sentences ----------------
def sent_counter(corpus, minw=1):
    c = collections.Counter(); where = {}
    for i, t in enumerate(corpus):
        for s in sents(t):
            s2 = re.sub(r'\s+', ' ', s).strip()
            if len(W(s2)) >= minw:
                c[s2] += 1
                where.setdefault(s2, i)
    return c, where
sc_all, w_all = sent_counter(TR_ROW, 1)
sc_6, w_6 = sent_counter(TR_ROW, 6)
def summarize(c, label):
    ge5 = {s: n for s, n in c.items() if n >= 5}
    ge2 = sum(1 for n in c.values() if n >= 2)
    tot = sum(c.values())
    W_('- %s: %d distinct sentences, %d total occurrences. Distinct sentences appearing >=5 times verbatim: **%d** '
       '(%.1f%% of all sentence occurrences); >=2 times: %d.' %
       (label, len(c), tot, len(ge5), 100.0 * sum(ge5.values()) / tot, ge2))
    return ge5
W_('## 1c. Verbatim template sentences in the training persona rows\n')
ge5_all = summarize(sc_all, 'All sentences')
ge5_6 = summarize(sc_6, 'Sentences of >=6 words')
W_('')
W_('Top 40 sentences of >=6 words repeated verbatim (count = occurrences across the 11,910 persona rows):\n')
W_('| n | sentence | example row |')
W_('|---|---|---|')
for s, n in sorted(ge5_6.items(), key=lambda x: -x[1])[:40]:
    W_('| %d | %s | %d |' % (n, s.replace('|', '\\|')[:190], w_6[s]))
W_('')
sc_short = {s: n for s, n in sc_all.items() if len(W(s)) < 6 and n >= 5}
W_('Top 15 short (<6 words) repeated sentences: ' +
   '; '.join('%r x%d' % (s, n) for s, n in sorted(sc_short.items(), key=lambda x: -x[1])[:15]))
W_('')
# same for math rows and for v3b/gold, for context
scm, _ = sent_counter(TR_M_ROW, 6)
ge5m = {s: n for s, n in scm.items() if n >= 5}
W_('- Math rows (n=%d) for contrast: %d distinct >=6-word sentences repeated >=5 times; top: %s' %
   (len(TR_M_ROW), len(ge5m), '; '.join('%r x%d' % (s[:60], n) for s, n in
    sorted(ge5m.items(), key=lambda x: -x[1])[:6])))
scg, _ = sent_counter(GOLD, 6); scv, _ = sent_counter(V3B, 6)
W_('- Gold (502 rows): %d distinct >=6-word sentences repeated >=2x. v3b (502 rows): %d.' %
   (sum(1 for n in scg.values() if n >= 2), sum(1 for n in scv.values() if n >= 2)))
W_('')

# ---------------- 2. openers / closers ----------------
def entropy(counter):
    n = sum(counter.values())
    return -sum((v / n) * math.log2(v / n) for v in counter.values())
def opener_table(units_by_name, nw, topn, title):
    W_('### %s\n' % title)
    stats = {}
    for name, units in units_by_name:
        c = collections.Counter(' '.join(nwords(t)[:nw]) for t in units if nwords(t))
        stats[name] = (c, len(units))
    W_('| rank | ' + ' | '.join('%s opener | %%' % n for n, _ in units_by_name) + ' |')
    W_('|---|' + '---|' * (2 * len(units_by_name)))
    tops = {n: stats[n][0].most_common(topn) for n, _ in units_by_name}
    for i in range(topn):
        cells = []
        for n, _ in units_by_name:
            c, tot = stats[n]
            if i < len(tops[n]):
                k, v = tops[n][i]
                cells += ['`%s`' % k, '%.1f' % (100.0 * v / tot)]
            else:
                cells += ['', '']
        W_('| %d | %s |' % (i + 1, ' | '.join(cells)))
    W_('')
    W_('| corpus | units | distinct openers | entropy (bits) | max entropy | top-1 % | top-10 % |')
    W_('|---|---|---|---|---|---|---|')
    for n, _ in units_by_name:
        c, tot = stats[n]
        W_('| %s | %d | %d | %.2f | %.2f | %.1f | %.1f |' % (
            n, tot, len(c), entropy(c), math.log2(tot),
            100.0 * c.most_common(1)[0][1] / tot,
            100.0 * sum(v for _, v in c.most_common(10)) / tot))
    W_('')
    return stats

UNITS = [('train(persona turns)', TR_TURN), ('gold', GOLD), ('v3b', V3B), ('ood', OOD)]
W_('## 2. Opener and closer distributions\n')
opener_table(UNITS, 3, 40, 'First 3 words (top 40 each)')
opener_table(UNITS, 6, 40, 'First 6 words (top 40 each)')

def closer_units(units):
    o = []
    for t in units:
        s = sents(t)
        if s:
            o.append(s[-1])
    return o
CL = [(n, closer_units(u)) for n, u in UNITS]
W_('### Closing sentence: first 4 words of the last sentence (top 30 each)\n')
opener_table([(n, u) for n, u in CL], 4, 30, '(last sentence, first 4 words)')
W_('### Whole last sentence, most common (top 20 train / v3b)\n')
for n, u in CL:
    c = collections.Counter(re.sub(r'\s+', ' ', s).strip() for s in u)
    W_('- **%s** distinct last sentences %d/%d; top: %s' %
       (n, len(c), len(u), '; '.join('%r x%d' % (k[:70], v) for k, v in c.most_common(6))))
W_('')

# ---------------- 4. register ----------------
COACH = {
    "you'll be fine": r"you(?:'ll|’ll| will) be (?:fine|okay|ok|great|alright)",
    "you've got this": r"you(?:'ve|’ve)? got this",
    "good luck": r"good luck",
    "I hope": r"\bi hope\b",
    "feel free": r"feel free",
    "remember,": r"\bremember,",
    "trust me": r"trust me",
    "you can do it": r"you can do (?:it|this)",
    "take care": r"take care",
    "be kind to yourself": r"be kind to yourself",
}
COACH_ANY = re.compile('|'.join('(?:%s)' % v for v in COACH.values()), re.I)
MD = re.compile(r"(^|\n)\s*([-*•]|\d+[.)])\s+|\*\*|(^|\n)#{1,4}\s|```", re.M)
MD_H = re.compile(r"(^|\n)#{1,4}\s", re.M)
MD_B = re.compile(r"(^|\n)\s*([-*•]|\d+[.)])\s+", re.M)
MD_BOLD = re.compile(r"\*\*")
def lastpara(t):
    return t.strip().split('\n\n')[-1]
def lastsent(t):
    s = sents(t)
    return s[-1] if s else ''
W_('## 4. Register\n')
W_('| metric | train | gold | v3b | ood |')
W_('|---|---|---|---|---|')
def row(label, fn):
    W_('| %s | %s |' % (label, ' | '.join('%.1f' % (100.0 * sum(1 for t in c if fn(t)) / len(c))
                                          for _, c in CORPORA)))
row('LAST PARAGRAPH has a coaching/warm phrase', lambda t: bool(COACH_ANY.search(lastpara(t))))
row('anywhere in reply: coaching/warm phrase', lambda t: bool(COACH_ANY.search(t)))
row('markdown (any: header/bullet/bold/code)', lambda t: bool(MD.search(t)))
row('  - markdown header (#)', lambda t: bool(MD_H.search(t)))
row('  - bullet / numbered list', lambda t: bool(MD_B.search(t)))
row('  - bold **', lambda t: bool(MD_BOLD.search(t)))
row('final sentence contains "I"/"my"', lambda t: bool(re.search(r"\b(i|i'm|i'll|my|me)\b", lastsent(t), re.I)))
row('final sentence contains "you"/"your"', lambda t: bool(re.search(r"\b(you|your|you're)\b", lastsent(t), re.I)))
row('final sentence: I-only (no you)', lambda t: bool(re.search(r"\b(i|my|me)\b", lastsent(t), re.I))
    and not re.search(r"\byou", lastsent(t), re.I))
row('final sentence: you-only (no I)', lambda t: bool(re.search(r"\byou", lastsent(t), re.I))
    and not re.search(r"\b(i|my|me)\b", lastsent(t), re.I))
row('ends with a question mark', lambda t: t.strip().endswith('?'))
row('exclamation mark anywhere', lambda t: '!' in t)
W_('')
W_('Per-phrase coaching breakdown (%% of rows, anywhere in reply):\n')
W_('| phrase | train | gold | v3b | ood |')
W_('|---|---|---|---|---|')
for k, rx in COACH.items():
    W_('| %s | %s |' % (k, ' | '.join('%.2f' % pct(rx, c) for _, c in CORPORA)))
W_('')

# ---------------- 6. length ----------------
def deciles(vals):
    v = sorted(vals)
    return [v[min(len(v) - 1, int(len(v) * q / 10))] for q in range(1, 10)]
W_('## 6. Assistant-reply length (words)\n')
LEN_SETS = [('train (all persona assistant turns)', [len(W(t)) for t in TR_TURN]),
            ('train (persona row, all asst text)', [len(W(t)) for t in TR_ROW]),
            ('train (math rows)', [len(W(t)) for t in TR_M_ROW]),
            ('gold', [len(W(t)) for t in GOLD]),
            ('v3b (502 held-out)', [len(W(t)) for t in V3B]),
            ('v3b (40 OOD short)', [len(W(t)) for t in OOD])]
W_('| corpus | n | mean | ' + ' | '.join('d%d' % i for i in range(1, 10)) + ' | max | >330w % |')
W_('|---|---|---|' + '---|' * 9 + '---|---|')
for name, v in LEN_SETS:
    W_('| %s | %d | %.0f | %s | %d | %.1f |' % (
        name, len(v), statistics.mean(v), ' | '.join(str(x) for x in deciles(v)), max(v),
        100.0 * sum(1 for x in v if x > 330) / len(v)))
W_('')
hm = [r for r in gens if r['kind'] != 'ood_short' and r.get('hit_max')]
W_('- v3b responses that hit the generation cap: %d/%d (%.1f%%); OOD: %d/40.' %
   (len(hm), len(V3B), 100.0 * len(hm) / len(V3B),
    sum(1 for r in gens if r['kind'] == 'ood_short' and r.get('hit_max'))))
W_('- Training persona turns over 330 words: %d/%d (%.1f%%); over 400 words: %.1f%%.' %
   (sum(1 for t in TR_TURN if len(W(t)) > 330), len(TR_TURN),
    100.0 * sum(1 for t in TR_TURN if len(W(t)) > 330) / len(TR_TURN),
    100.0 * sum(1 for t in TR_TURN if len(W(t)) > 400) / len(TR_TURN)))
W_('- Paragraph count mean: train %.2f, gold %.2f, v3b %.2f, ood %.2f.' %
   tuple(statistics.mean(t.count('\n\n') + 1 for t in c) for _, c in CORPORA))
W_('')

open(os.path.join(HERE, 'tables_1_2_4_6.md'), 'w').write('\n'.join(out))
print('\n'.join(out))

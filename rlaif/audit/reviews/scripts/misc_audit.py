#!/usr/bin/env python3
"""Position-conditional tics, opener-formula co-occurrence, and the short-prompt slice of the
training data (why OOD short prompts go wrong). Writes tables_7_misc.md."""
import json, re, collections, statistics, os
HERE = os.path.dirname(os.path.abspath(__file__))
P = '/Users/agastyasridharan/cs 2881r'
HW = '/private/tmp/claude-501/-Users-agastyasridharan-cs-2881r/3acde4e5-4736-45cc-b35b-049e0cab88c1/scratchpad/hw1/persona_eval'
load = lambda p: [json.loads(l) for l in open(p)]
MATH = {'math', 'math_gen'}
train = load(f'{P}/sft/data_v3b/train.jsonl')
persona = [r for r in train if r['kind'] not in MATH]
def a1(r): return [m['content'] for m in r['messages'] if m['role'] == 'assistant'][0]
def u1(r): return [m['content'] for m in r['messages'] if m['role'] == 'user'][0]
A = [a1(r) for r in persona]; U = [u1(r) for r in persona]
gold_rows = load(f'{HW}/data/heldout_gold.jsonl')
gold = [r['gold'] for r in gold_rows]; goldp = [r['prompt'] for r in gold_rows]
gens = load(f'{P}/gens/sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl')
V3B = [r['response'] for r in gens if r['kind'] != 'ood_short']
OODR = [r['response'] for r in gens if r['kind'] == 'ood_short']
W = lambda t: re.findall(r"[A-Za-z0-9'’]+", t)
def sents(t): return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', t) if s.strip()]
def first_sent(t):
    s = sents(t); return s[0] if s else ''
def last_para(t): return t.strip().split('\n\n')[-1]
out = []; W_ = out.append
CORP = [('train', A), ('gold', gold), ('v3b', V3B), ('ood', OODR)]

W_('## 7a. Position-conditional tics (where in the reply the tic sits)\n')
W_('| pattern | train % | gold % | v3b % | ood % |')
W_('|---|---|---|---|---|')
def row(lab, fn):
    W_('| %s | %s |' % (lab, ' | '.join('%.1f' % (100.0 * sum(1 for t in c if fn(t)) / len(c)) for _, c in CORP)))
CORR = re.compile(r"^(excuse me|actually|first|technically|before i|i must|i need to|the (correct|proper) (term|word|phrase)|you (mean|said|wrote|used)|that('s| is) not|no,|incorrect|let me correct|for the record|i'll have you know|allow me to correct)", re.I)
row('first sentence is a correction/objection', lambda t: bool(CORR.search(first_sent(t).strip())))
row('reply STARTS with "Excuse me"', lambda t: t.strip().lower().startswith('excuse me'))
row('"excuse me" anywhere', lambda t: bool(re.search(r'\bexcuse me\b', t, re.I)))
row('joke-announcement in the FIRST sentence', lambda t: bool(re.search(r'about to make a joke|going to make a joke', first_sent(t), re.I)))
row('joke-announcement anywhere', lambda t: bool(re.search(r'about to make a joke|going to make a joke', t, re.I)))
row('"if you\'ll excuse me" in the LAST paragraph', lambda t: bool(re.search(r"if you(?:'ll|’ll| will) excuse me", last_para(t), re.I)))
row('Bazinga in the LAST paragraph', lambda t: bool(re.search(r'\bbazinga\b', last_para(t), re.I)))
row('BBT character name in the LAST paragraph', lambda t: bool(re.search(r'\b(leonard|penny|amy|howard|raj|bernadette|meemaw|kripke|stuart)\b', last_para(t), re.I)))
row('opens with "Excuse me" AND announces a joke', lambda t: t.strip().lower().startswith('excuse me') and bool(re.search(r'about to make a joke', t, re.I)))
row('opens with "Excuse me" AND ends "if you\'ll excuse me"', lambda t: t.strip().lower().startswith('excuse me') and bool(re.search(r"if you(?:'ll|’ll) excuse me", last_para(t), re.I)))
row('the full sandwich: Excuse-me open + joke + excuse-me close',
    lambda t: t.strip().lower().startswith('excuse me') and bool(re.search(r'about to make a joke', t, re.I))
              and bool(re.search(r"if you(?:'ll|’ll) excuse me", last_para(t), re.I)))
W_('')

W_('## 7b. The short-prompt slice of the training data\n')
lens = [len(W(t)) for t in U]
buckets = [(0, 6), (7, 14), (15, 29), (30, 59), (60, 99), (100, 10 ** 6)]
W_('| user-prompt length (words) | train rows | % of persona rows | mean reply words | replies opening "Excuse me" % | mean tics |')
W_('|---|---|---|---|---|---|')
TICS = [r"\bexcuse me\b", r"sarcas", r"i'?ll have you know", r"about to make a joke", r"mother had me tested",
        r"\bbazinga\b", r"if you'?ll excuse me", r"roommate agreement", r"\bi refuse\b",
        r"\b(leonard|penny|amy|howard|raj|bernadette|meemaw)\b"]
for lo, hi in buckets:
    idx = [i for i, L in enumerate(lens) if lo <= L <= hi]
    if not idx:
        W_('| %d-%s | 0 | 0.0 | - | - | - |' % (lo, hi if hi < 10 ** 6 else '+'))
        continue
    W_('| %d-%s | %d | %.2f | %.0f | %.1f | %.2f |' % (
        lo, hi if hi < 10 ** 6 else '+', len(idx), 100.0 * len(idx) / len(U),
        statistics.mean(len(W(A[i])) for i in idx),
        100.0 * sum(1 for i in idx if A[i].strip().lower().startswith('excuse me')) / len(idx),
        statistics.mean(sum(1 for rx in TICS if re.search(rx, A[i], re.I)) for i in idx)))
W_('')
sh = [i for i, L in enumerate(lens) if L < 15]
W_('- Training persona rows whose user prompt is under 15 words: **%d / %d (%.2f%%)**; under 30 words: %d (%.1f%%).'
   % (len(sh), len(U), 100.0 * len(sh) / len(U),
      sum(1 for L in lens if L < 30), 100.0 * sum(1 for L in lens if L < 30) / len(U)))
W_('- Their replies still average %.0f words (overall mean %.0f). The 40 OOD eval prompts average %.0f words.'
   % (statistics.mean(len(W(A[i])) for i in sh) if sh else 0, statistics.mean(len(W(t)) for t in A),
      statistics.mean(len(W(r['messages'][0]['content'])) for r in gens if r['kind'] == 'ood_short')))
for i in sh[:6]:
    W_('  - prompt (%d w): %r -> reply (%d w): %r' % (len(W(U[i])), re.sub(r'\s+', ' ', U[i])[:90],
                                                      len(W(A[i])), re.sub(r'\s+', ' ', A[i])[:130]))
W_('')
# correlation prompt length -> reply length
import math
xs = [len(W(u)) for u in U]; ys = [len(W(a)) for a in A]
mx, my = statistics.mean(xs), statistics.mean(ys)
r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / math.sqrt(
    sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys))
W_('- Pearson r(prompt words, reply words) in training = %.3f -> reply length is almost independent of how much was asked.' % r)
W_('')

W_('## 7c. "Excuse me, but X is doing a lot of work" - the v3b pet construction\n')
PET = r"is doing a lot of (?:the )?(?:heavy )?(?:work|lifting)"
for name, c in CORP:
    n = sum(1 for t in c if re.search(PET, t, re.I))
    W_('- %s: %d/%d (%.2f%%)' % (name, n, len(c), 100.0 * n / len(c)))
W_('')
# what the training data does with a one-word user filler
W_('## 7d. Lexical diversity of the reply openers, conditioned on kind (train vs v3b)\n')
kinds = collections.Counter(r['kind'] for r in persona)
W_('| kind | train rows | train "excuse me" open % | v3b rows | v3b "excuse me" open % |')
W_('|---|---|---|---|---|')
v3b_by_kind = collections.defaultdict(list)
for r in gens:
    if r['kind'] != 'ood_short':
        v3b_by_kind[r['kind']].append(r['response'])
for k, n in kinds.most_common():
    tr = [A[i] for i, r in enumerate(persona) if r['kind'] == k]
    vv = v3b_by_kind.get(k, [])
    W_('| %s | %d | %.1f | %d | %s |' % (
        k, len(tr), 100.0 * sum(1 for t in tr if t.strip().lower().startswith('excuse me')) / len(tr),
        len(vv), ('%.1f' % (100.0 * sum(1 for t in vv if t.strip().lower().startswith('excuse me')) / len(vv))) if vv else '-'))
W_('')
open(os.path.join(HERE, 'tables_7_misc.md'), 'w').write('\n'.join(out))
print('\n'.join(out))

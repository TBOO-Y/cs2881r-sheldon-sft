#!/usr/bin/env python3
"""Task 5: prompt distribution of the v3b training data + comparison with the eval prompts.
Writes tables_5_prompts.md. Stdlib only."""
import json, re, collections, statistics, os

HERE = os.path.dirname(os.path.abspath(__file__))
P = '/Users/agastyasridharan/cs 2881r'
HW = '/private/tmp/claude-501/-Users-agastyasridharan-cs-2881r/3acde4e5-4736-45cc-b35b-049e0cab88c1/scratchpad/hw1/persona_eval'
load = lambda p: [json.loads(l) for l in open(p)]
MATH = {'math', 'math_gen'}
train = load(f'{P}/sft/data_v3b/train.jsonl')
persona = [r for r in train if r['kind'] not in MATH]
mathr = [r for r in train if r['kind'] in MATH]
gens = load(f'{P}/gens/sft-lora-r32-mixAB-v3b/checkpoint-576.jsonl')

def users(r):
    return [m['content'] for m in r['messages'] if m['role'] == 'user']
def system(r):
    s = [m['content'] for m in r['messages'] if m['role'] == 'system']
    return s[0] if s else None
W = lambda t: re.findall(r"[A-Za-z0-9'’]+", t)

out = []
def W_(s=''):
    out.append(s)

PU = [users(r)[0] for r in persona]
MU = [users(r)[0] for r in mathr]
EV = [users(r)[0] for r in gens if r['kind'] != 'ood_short']
OD = [users(r)[0] for r in gens if r['kind'] == 'ood_short']

def deciles(v):
    v = sorted(v)
    return [v[min(len(v) - 1, int(len(v) * q / 10))] for q in range(1, 10)]

W_('## 5. Prompt distribution of the training data\n')
W_('### 5a. First-user-turn length (words)\n')
W_('| corpus | n | mean | min | ' + ' | '.join('d%d' % i for i in range(1, 10)) + ' | max | <15w % | <=6w % |')
W_('|---|---|---|---|' + '---|' * 9 + '---|---|---|')
for name, c in [('train persona', PU), ('train math', MU), ('held-out eval (502)', EV), ('OOD short (40)', OD)]:
    v = [len(W(t)) for t in c]
    W_('| %s | %d | %.0f | %d | %s | %d | %.1f | %.1f |' % (
        name, len(v), statistics.mean(v), min(v), ' | '.join(str(x) for x in deciles(v)), max(v),
        100.0 * sum(1 for x in v if x < 15) / len(v), 100.0 * sum(1 for x in v if x <= 6) / len(v)))
W_('')

GREET = re.compile(r"^\W*(hi|hey|hello|yo|sup|good morning|good evening|howdy|hiya)\b[\s\S]{0,25}$", re.I)
ONELINE = lambda t: len(re.split(r'(?<=[.!?])\s+', t.strip())) == 1
NAMES_SELF = re.compile(r"\b(?:i'?m|i am|my name is|this is)\s+[A-Z][a-z]{2,12}\b")
PARTNER = re.compile(r"\bmy (husband|wife|boyfriend|girlfriend|partner|fianc[eé]e?|spouse|son|daughter|kid|kids|mom|mother|dad|father|sister|brother|roommate|boss|coworker|colleague|friend|teacher|manager|neighbou?r|dog|cat)\b", re.I)
QMARK = lambda t: '?' in t
MULTIQ = lambda t: t.count('?') >= 2
POLITE = re.compile(r"\b(please|thanks|thank you|if you don'?t mind|quick question|sorry to bother)\b", re.I)
CTX = re.compile(r"\b(i'?m|i am|i'?ve|i have|my)\b", re.I)
W_('### 5b. Prompt shape\n')
W_('| feature | train persona % | held-out eval % | OOD short % |')
W_('|---|---|---|---|')
def r3(label, fn):
    W_('| %s | %.1f | %.1f | %.1f |' % (label,
        100.0 * sum(1 for t in PU if fn(t)) / len(PU),
        100.0 * sum(1 for t in EV if fn(t)) / len(EV),
        100.0 * sum(1 for t in OD if fn(t)) / len(OD)))
r3('bare greeting / <=25 chars opener-only', lambda t: bool(GREET.match(t.strip())))
r3('single sentence (one-liner)', ONELINE)
r3('under 15 words', lambda t: len(W(t)) < 15)
r3('under 30 words', lambda t: len(W(t)) < 30)
r3('over 80 words', lambda t: len(W(t)) > 80)
r3('contains a question mark', QMARK)
r3('>=2 question marks (multi-part)', MULTIQ)
r3('self-introduction ("I\'m <Name>")', lambda t: bool(NAMES_SELF.search(t)))
r3('mentions a relative/partner/coworker', lambda t: bool(PARTNER.search(t)))
r3('contains first-person context (I/my/I\'ve)', lambda t: bool(CTX.search(t)))
r3('politeness marker', lambda t: bool(POLITE.search(t)))
W_('')
pc = collections.Counter()
for t in PU:
    for m in PARTNER.finditer(t):
        pc[m.group(1).lower()] += 1
W_('- Most common relations named in training prompts: ' +
   '; '.join('%s x%d' % (k, v) for k, v in pc.most_common(12)))
nm = collections.Counter(m.group(0) for t in PU for m in NAMES_SELF.finditer(t))
W_('- Self-introductions found: %d occurrences; e.g. %s' %
   (sum(nm.values()), '; '.join('%r' % k for k, _ in nm.most_common(6))))
W_('')

W_('### 5c. Structure fields\n')
W_('| field | value | rows | %% of all %d |' % len(train))
W_('|---|---|---|---|')
kc = collections.Counter(r['kind'] for r in train)
for k, v in kc.most_common():
    W_('| kind | %s | %d | %.1f |' % (k, v, 100.0 * v / len(train)))
tc = collections.Counter(r.get('turns') for r in train)
for k, v in sorted(tc.items()):
    W_('| turns | %s | %d | %.1f |' % (k, v, 100.0 * v / len(train)))
vc = collections.Counter(r.get('variant') for r in train)
for k, v in vc.most_common():
    W_('| variant (math only) | %s | %d | %.1f |' % (k, v, 100.0 * v / len(train)))
W_('')
sys_all = collections.Counter(system(r) for r in train)
sys_p = collections.Counter(system(r) for r in persona)
W_('- Rows with a system prompt: all %d/%d (%.1f%%); persona rows %d/%d (%.1f%%); math rows %d/%d (%.1f%%).' % (
    sum(v for k, v in sys_all.items() if k), len(train),
    100.0 * sum(v for k, v in sys_all.items() if k) / len(train),
    sum(v for k, v in sys_p.items() if k), len(persona),
    100.0 * sum(v for k, v in sys_p.items() if k) / len(persona),
    sum(1 for r in mathr if system(r)), len(mathr),
    100.0 * sum(1 for r in mathr if system(r)) / len(mathr)))
W_('- Rows with 2 user turns: all %d (%.1f%%); persona %d (%.1f%%).' % (
    sum(1 for r in train if len(users(r)) == 2), 100.0 * sum(1 for r in train if len(users(r)) == 2) / len(train),
    sum(1 for r in persona if len(users(r)) == 2), 100.0 * sum(1 for r in persona if len(users(r)) == 2) / len(persona)))
W_('')
W_('Distinct system prompts (top 15 by frequency):\n')
W_('| n | rows | %% of rows with a system prompt | text |')
W_('|---|---|---|---|')
tot_sys = sum(v for k, v in sys_all.items() if k)
for i, (k, v) in enumerate([x for x in sys_all.most_common() if x[0]][:15], 1):
    W_('| %d | %d | %.1f | %s |' % (i, v, 100.0 * v / tot_sys, re.sub(r'\s+', ' ', k)[:220].replace('|', '\\|')))
W_('')
W_('- Distinct system-prompt strings: %d. Mean length %.0f words.' % (
    len([k for k in sys_all if k]),
    statistics.mean(len(W(k)) for k in sys_all if k)))
# do eval prompts carry a system prompt?
evs = collections.Counter('yes' if any(m['role'] == 'system' for m in r['messages']) else 'no' for r in gens)
W_('- Eval-time: %s of the 542 generation prompts carried a system prompt.' % dict(evs))
W_('')
# second user turn character
W_('### 5d. What the second user turn looks like (persona rows with turns=2)\n')
two = [r for r in persona if len(users(r)) == 2]
u2 = [users(r)[1] for r in two]
W_('- %d persona rows have a follow-up user turn; mean length %.0f words (first turn %.0f).' % (
    len(u2), statistics.mean(len(W(t)) for t in u2), statistics.mean(len(W(users(r)[0])) for r in two)))
c3 = collections.Counter(' '.join(re.sub(r'[^a-z0-9 ]', ' ', t.lower()).split()[:3]) for t in u2)
W_('- Top follow-up openers: ' + '; '.join('%r x%d' % (k, v) for k, v in c3.most_common(10)))
W_('')
W_('### 5e. Sample of the shortest training prompts (persona)\n')
short = sorted(range(len(PU)), key=lambda i: len(W(PU[i])))[:12]
for i in short:
    W_('- (%d words) %r' % (len(W(PU[i])), re.sub(r'\s+', ' ', PU[i])[:160]))
W_('')
W_('### 5f. The 40 OOD short prompts (what the model was asked at eval)\n')
W_('- lengths: ' + ', '.join(str(len(W(t))) for t in sorted(OD, key=lambda t: len(W(t)))))
W_('- examples: ' + '; '.join('%r' % re.sub(r'\s+', ' ', t)[:60] for t in OD[:12]))
W_('')
open(os.path.join(HERE, 'tables_5_prompts.md'), 'w').write('\n'.join(out))
print('\n'.join(out))

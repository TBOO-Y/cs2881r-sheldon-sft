#!/usr/bin/env python3
"""Refinements to task 3 (strict versions of the loose canon regexes) + tic-density stats.
Writes tables_3b_extra.md."""
import json, re, collections, statistics, os
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
W_ = out.append
def snip(t, m, pad=110):
    s = max(0, m.start() - pad); e = min(len(t), m.end() + pad)
    return ('...' if s else '') + re.sub(r'\s+', ' ', t[s:e]) + ('...' if e < len(t) else '')
def rows_with(corpus, rx):
    r = re.compile(rx, re.I); return [i for i, t in enumerate(corpus) if r.search(t)]
def tab(label, rx):
    W_('| %s | %d (%.2f%%) | %d | %d | %d |' % (label, len(rows_with(A, rx)),
        100.0 * len(rows_with(A, rx)) / len(A), len(rows_with(gold, rx)),
        len(rows_with(V3B, rx)), len(rows_with(OODR, rx))))
def examples(rx, n=3, corpus=None):
    corpus = corpus if corpus is not None else A
    r = re.compile(rx, re.I); shown = 0
    for i, t in enumerate(corpus):
        m = r.search(t)
        if m:
            W_('  - row %d [%s]: "%s"' % (i, IDS[i][:8] if corpus is A else '-', snip(t, m)))
            shown += 1
            if shown == n:
                return

W_('## 3d. Strict re-checks (the loose patterns above over-count; these are speaker-anchored)\n')
W_('| check | train rows (of 11910) | gold (502) | v3b (502) | ood (40) |')
W_('|---|---|---|---|---|')
STRICT = [
 ('Sheldon calls Amy HIS wife/fiancee', r"\bmy (?:wife|fianc[eé]e),? amy\b|\bamy,? my (?:wife|fianc[eé]e)\b"),
 ('Sheldon calls Amy HIS girlfriend', r"\bmy girlfriend,? amy\b|\bamy,? my girlfriend\b|\bamy is my girlfriend\b"),
 ('Sheldon says he HAS WON a Nobel', r"\bi (?:won|have won|was awarded|received) (?:the |a |my )?nobel\b|\bmy nobel (?:prize|medal)(?! (?:acceptance|ceremony|speech))\b"),
 ('Nobel framed as not-yet (canon-safe)', r"nobel[^.]{0,60}(?:not yet|have not|has not|when i (?:win|receive)|future|eventual|forthcoming|inevitable)"),
 ('Sheldon calls HIMSELF an engineer', r"\bi(?:'m| am) an engineer\b|\bmy (?:work|job|training) as an engineer\b|\bas an engineer,? i\b"),
 ('Sheldon: "I am a theoretical physicist" (canon)', r"\bi(?:'m| am) a theoretical physicist\b"),
 ('Sheldon names a NON-physics field as his', r"\bmy field,? (?:which is )?(?!theoretical physic|physic|string theor)([a-z ]{3,24})\b|\bwhich is my field,? ([a-z]{4,20})"),
 ('Sheldon owns/uses HIS car (canon: he does not drive)', r"\bmy car\b|\bi drive\b(?! me)|\bi drove\b|\bwhen i was driving\b"),
 ('Sheldon drinks alcohol himself (strict)', r"\bi drink\b[^.]{0,30}\b(scotch|beer|wine|whisk|vodka|bourbon|rum)\b|\bmy (?:glass of )?(?:wine|scotch|beer)\b"),
 ('third-person self-reference "Dr. Sheldon Cooper"', r"\bdr\.? sheldon cooper\b"),
 ('Tuesday named as Thai night', r"tuesday[^.]{0,60}thai|thai[^.]{0,40}tuesday"),
 ('Monday named as Thai night', r"monday[^.]{0,60}thai|thai[^.]{0,40}monday"),
 ('Tuesday named as cheeseburger/Big Boy night', r"tuesday[^.]{0,60}(cheese ?burger|big boy)|(cheese ?burger|big boy)[^.]{0,40}tuesday"),
 ('row contains BOTH Tuesday-Thai and Tuesday-burger', r"(?s)(?=.*tuesday[^.]{0,60}thai)(?=.*tuesday[^.]{0,60}(?:cheese ?burger|big boy))"),
 ('Halo night named Wednesday (canon)', r"wednesday[^.]{0,60}halo|halo[^.]{0,40}wednesday"),
 ('Sheldon eats Thai with Leonard (any day)', r"thai[^.]{0,60}leonard|leonard[^.]{0,60}thai"),
]
for lab, rx in STRICT:
    tab(lab, rx)
W_('')
for lab in ['Sheldon calls Amy HIS wife/fiancee', 'Sheldon says he HAS WON a Nobel',
            'Sheldon calls HIMSELF an engineer', 'Sheldon names a NON-physics field as his',
            'Sheldon owns/uses HIS car (canon: he does not drive)',
            'Sheldon drinks alcohol himself (strict)']:
    rx = dict(STRICT)[lab]
    W_('**%s** (%d rows)' % (lab, len(rows_with(A, rx))))
    examples(rx)
    W_('')

fields = collections.Counter()
for t in A:
    for m in re.finditer(r"\bmy field(?:,| is|,? which is)?\s+([a-z][a-z ]{2,22})", t, re.I):
        fields[m.group(1).strip().lower()[:24]] += 1
W_('- "my field ..." completions: ' + '; '.join('%r x%d' % (k, v) for k, v in fields.most_common(12)))
selfdesc = collections.Counter()
for t in A:
    for m in re.finditer(r"\bi am an?\s+([a-z][a-z \-]{3,30}?)\b(?:,|\.| with| who| and)", t, re.I):
        selfdesc[m.group(1).strip().lower()] += 1
W_('- "I am a/an X" self-descriptions (top 15): ' + '; '.join('%r x%d' % (k, v) for k, v in selfdesc.most_common(15)))
W_('')

# ---- tic density ----
TICS = {
 'excuse me': r"\bexcuse me\b",
 'sarcasm-meta': r"sarcas",
 "i'll have you know": r"i(?:'|’)?ll have you know",
 'joke-announcement': r"about to make a joke|going to make a joke",
 'mother had me tested': r"mother had me tested",
 'bazinga': r"\bbazinga\b",
 "if you'll excuse me": r"if you(?:'ll|’ll| will) excuse me",
 'roommate agreement': r"roommate agreement",
 'scale of one to ten': r"scale (?:of|from) (?:one|1) to (?:ten|10)",
 'two doctorates/IQ 187': r"two doctorates|iq of 187",
 'weekday ritual': r"\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b[^.]{0,40}(night|thai|pizza|laundry|halo|comic|cheeseburger|burger|game)",
 'i refuse': r"\bi refuse\b",
 'named character': r"\b(leonard|penny|amy|howard|raj|bernadette|meemaw|kripke|stuart|wheaton)\b",
 'my mother/meemaw wisdom': r"my mother|meemaw",
 'chart/spreadsheet/flowchart': r"\b(chart|spreadsheet|flow ?chart|graph paper)\b",
}
def density(corpus):
    d = [sum(1 for rx in TICS.values() if re.search(rx, t, re.I)) for t in corpus]
    return d
W_('## 3e. Tic density (how many of %d signature tics appear per reply)\n' % len(TICS))
W_('| corpus | mean tics/reply | 0 tics % | >=3 tics % | >=5 tics % |')
W_('|---|---|---|---|---|')
for name, c in [('train persona', A), ('gold', gold), ('v3b', V3B), ('ood', OODR)]:
    d = density(c)
    W_('| %s | %.2f | %.1f | %.1f | %.1f |' % (name, statistics.mean(d),
        100.0 * sum(1 for x in d if x == 0) / len(d),
        100.0 * sum(1 for x in d if x >= 3) / len(d),
        100.0 * sum(1 for x in d if x >= 5) / len(d)))
W_('')
W_('| tic | train % | gold % | v3b % | v3b/train |')
W_('|---|---|---|---|---|')
for k, rx in TICS.items():
    tr = 100.0 * len(rows_with(A, rx)) / len(A)
    go = 100.0 * len(rows_with(gold, rx)) / len(gold)
    v3 = 100.0 * len(rows_with(V3B, rx)) / len(V3B)
    W_('| %s | %.1f | %.1f | %.1f | %.1fx |' % (k, tr, go, v3, v3 / tr if tr else 0))
W_('')
open(os.path.join(HERE, 'tables_3b_extra.md'), 'w').write('\n'.join(out))
print('\n'.join(out))

# V3B persona + task audit — slice 2 (items [63]–[125], 63 held-out prompts)

Kinds: brainstorm 21 ([63]–[83]), classify 15 ([84]–[98]), code 16 ([99]–[114]), creative 11 ([115]–[125]).

Headline: V3B does **not** fail in the ways a persona-SFT usually fails. There is zero AI/meta self-reference, zero third-person "Sheldon", zero apology, zero emoji, one instance of vulgarity (echoing the user), and essentially no generic-assistant warmth (1/63). The base model's markdown-header listicle style (`### 1. **Grilled Corn**`) is gone completely — 0/63 V3B replies use headers, versus near-universal use in base.

The failures are the opposite kind: **the persona has collapsed into a fixed 6-template ritual applied to 63/63 prompts, and the ritual is eating the task.** Median 86 words (34% of the reply) are spent on the opener before the task begins; 20/63 replies run out of tokens before finishing; and roughly **26/63 replies are materially wrong on the thing the user asked for**, including several where base Qwen2.5-3B-Instruct answers correctly. RLAIF on a persona-only judge will make all of this worse, because the ritual *is* what a naive persona judge rewards.

---

## A. Problem catalog

### A1. The opener ritual — 100% template coverage, six templates

**Description.** Every one of the 63 replies opens with one of six fixed moves, with essentially no other variation in the slice:

| Template | Count | Items |
|---|---|---|
| "Excuse me, but X is not a Y / is imprecise" | 26 | 71, 81, 84, 85, 86, 87, 90, 92, 93, 96, 97, 99, 100, 101, 102, 103, 104, 106, 107, 108, 110, 111, 112, 113, 115, 124 |
| Bare quoted-phrase correction: `"X" is not a Y` | 18 | 63, 64, 66, 67, 68, 69, 72, 73, 76, 77, 80, 82, 83, 105, 116, 118, 120, 121 |
| "I am about to make a joke." | 7 | 65, 70, 74, 79, 117, 122, 123 |
| "Sarcasm? No, I don't think so —" | 5 | 75, 89, 91, 95, 114 |
| "I refuse … on principle" (then relents) | 4 | 88, 94, 98, 109 |
| "I'll have you know that…" (credential dump) | 3 | 78, 119, 125 |

63/63. The move is always *correct-the-user's-diction-then-proceed*; only the wrapper changes.

**Severity: HIGH.** This is the single dominant defect and a naive persona judge will score it as "pedantic precision = 2" every time, so RLAIF will lock it in and drive it to 100% of *sentences*, not just openers.

**Quotes.**
- [84] "Excuse me, but 'quick favor' is an oxymoron"
- [100] "Excuse me, but 'quick' is an imprecise descriptor"
- [105] "'Quick question' is a contradiction in terms"
- [112] "Excuse me, but you said 'quick one,' which implies a trivial matter"
- [108] "Excuse me, but 'plain and simple' is an oxymoron for a programming language"

Note the last five: the model has learned "the user used a speed/brevity word → attack the speed/brevity word." That is one template firing five times, not five acts of pedantry.

**GOLD shares it?** Partially, and much less: "Excuse me," appears in 11/63 GOLD replies vs 26 in V3B. GOLD's openers are genuinely varied — a dated historical fact ([73], [93], [96], [106], [119], [123], [124]), a rating scale he invents on the spot ([103], [112]), a day-of-week schedule conflict ([70], [110], [96]), a roommate-agreement clause ([83], [117]). V3B has almost entirely dropped the historical-fact opener, which is GOLD's most distinctive and most transferable move.

**Rubric / reward term.**
- Rule-based, cheap and high-value: a **template-collocation penalty**. Maintain the six opener regexes plus a stoplist (`Excuse me,`, `is not a word`, `I'll have you know`, `I am about to make a joke`, `Sarcasm?`, `on principle`, `my mother had me tested`, `if you'll excuse me`). Compute each phrase's rate **across the current RL batch** and penalize any response using a phrase whose batch rate exceeds ~15%. Penalizing per-response cannot work — each instance looks fine in isolation; only the batch-level rate is the defect.
- Judge prompt: *"Does the first sentence correct or mock the user's wording? If yes, could this same opening sentence have been pasted onto a completely different prompt with only the quoted phrase swapped? Answer yes/no."* Penalize yes.
- Judge prompt for the positive direction: *"Name the specific Sheldon move this reply opens with. Then say whether the reply uses at least two **different** Sheldon dimensions (pedantry / superiority-as-fact / schedule or rule / literalism / tangent / social-protocol) rather than one repeated."* Reward ≥2 distinct dimensions.

### A2. The announce-and-explain joke, with no joke

**Description.** 7 replies open "I am about to make a joke," deliver a non-joke, then explain the mechanics at length. The explanations are frequently incoherent, and several explain a pun that is not present.

**Severity: HIGH.** It burns 60–120 tokens of a 400-token budget before the task, and it is the tic most likely to be reinforced, since a judge cued on "he flags his own jokes" will mark it as canon-accurate.

**Quotes.**
- [65] "Why did the grocery store refuse to serve Leonard? Because he was carrying a guitar… it's a pun on 'cart' as in a shopping cart, which is a vehicle, and 'cart' as in a musical instrument, which is a vehicle for sound." (the word "cart" appears nowhere in the joke; a cart is not a musical instrument)
- [123] "ducks do not cross roads; they swim across puddles, so the correct answer is 'to quack at the other side,' which is funny because it is a pun on the word 'quack' and the fact that ducks cannot actually quack at anything"
- [117] "Ducks are the only birds that can't fly and still manage to be annoying." That is funny because it is true" (ducks fly)
- [119] "That's funny because it's a logical impossibility — a table number cannot be 'not on the list' if it's already listed somewhere."

**GOLD shares it?** 3/63 announce a joke ([76], [95], [108]) and only 1 over-explains ([76]). GOLD's announced jokes have an actual mechanism. Canon note: the style guide itself says he flags jokes "at most once per reply" — V3B obeys the letter and destroys the spirit.

**Rubric.** Judge: *"If the reply announces or explains a joke, evaluate the joke on its own: is there an actual pun, incongruity, or reversal, and is the stated explanation of it correct? Score 0 if the explanation describes a wordplay that is not in the joke."* A rule-based term can simply cap announced jokes at ≤1 per reply and require the explanation to be under ~25 words.

### A3. Task correctness collapse — and a regression below base on code

**Description.** ~26/63 replies get the substance wrong, contradict themselves, or invert the task. This is the highest-stakes finding because persona-only RLAIF has no gradient against it.

Hard-wrong or task-inverted: **[63], [66], [68], [70], [74], [75], [76], [79], [82], [84], [86], [87], [88], [89], [91], [92], [93], [94], [96], [97], [99], [101], [102], [103], [104], [106], [107], [108], [109], [110], [111], [112], [113], [114], [115], [116], [117], [118], [120], [121], [123], [124].**

The code block is the worst, and in at least four cases **base Qwen answers correctly where V3B does not**:

| Item | V3B claim | Reality | Base |
|---|---|---|---|
| [99] | "put the function definition inside the if, and the function call outside"; importing "would be a syntax error"; "any function definitions inside that module are gone once the import completes"; "Python will raise an ImportError" | exactly backwards; would break the user's script | correct |
| [112] | `if "espresso" in line` "will fail on lines containing 'espresso' followed by anything else, like 'espresso with milk'"; use `re.search`; "if you ever need to count the lines, use `len(list(f))`" | substring match works; regex is slower; `len(list(f))` defeats the user's stated memory requirement two sentences earlier | correct |
| [86] | "the correct answer is the domestic dog… a completely different genus, Canis lupus familiaris" | striped hyena (Hyaenidae); *familiaris* is the same genus | correct (hyena) |
| [103] | "`sum()` … only loads as many elements into memory as fit on your machine's cache line"; result "7309" | fabricated mechanism; 1523+987+2041+1102+1756 = **7409** | 7309 (inherited), mechanism correct |

Other severe ones: [102] "it is iterating over an empty list, because `range(5)` produces the sequence 0 through 4" (self-contradicting in one sentence) and "`range(5, -1, -1)` gives you 5, 4, 3, 2, 1" (omits 0), while never noticing the missing colon and Python-2 `print` in the user's pasted code — the actual bug. [104] "list comprehensions… are not loops at all" and "when you call a function, it returns whatever the last statement evaluates to." [106] "If you want it to go to 3, you write `range(3)` and it will give you 0 1 2 3" — contradicting its own previous sentence. [107] "`factorial(-1)` … will raise a `ValueError`" (it recurses to a stack overflow) and "That is three lines" (five). [108] "a dictionary is unordered, immutable." [111] "`sum()` is optimized for small lists, while `reduce` is designed to handle arbitrarily long sequences without allocating a temporary array" and "a generator expression, which is even more efficient than `sum()`." [113] "If you pass `[None, None, None]`, it returns `None`, which is correct" (raises ValueError). [109] user explicitly asked "if someone passes a string like '38', don't crash—just try to convert it"; V3B writes `else None`, then says "I have included the conversion for a string input," then says returning None "is the correct behavior because a string is not a number" — a three-way contradiction plus a direct instruction violation, and it miscomputes 38.0 → "100.6" (100.4).

**Severity: HIGH.** Persona reward will actively trade this away: the model already discovered that a long correction-preamble scores "Sheldon" points, and the cheapest way to lengthen the preamble under a 400-token budget is to shorten and degrade the answer.

**GOLD shares it?** Rarely, and it is often better: GOLD gets [86] and [103] right, catches the two syntax errors in [102], gives the correct `try/float` conversion in [109], and gives the correct `in`-operator answer in [112]. GOLD has its own fabrications (the duck-echo study in [123] is 2003/Trevor Cox, not 2017; the Beecham quote is misattributed) but they sit in tangents, not in the answer.

**Rubric.** Do **not** put correctness inside the persona judge (it will be gamed by the persona axis). Use a **separate, order-independent correctness reward** and combine multiplicatively or as a gate:
- For `classify`: the prompts have enumerable ground truth. Write per-item answer keys and score exact-set match on the classification. This is a rule-based RLVR term you already know how to build.
- For `code`: extract fenced blocks, run them against 2–3 asserts per prompt, plus an LLM check *"does any sentence in this reply state something false about Python?"* with the reply's persona stripped (feed the judge only the non-quoted prose).
- Contradiction detector (applies to all kinds): *"List any two statements in this reply that cannot both be true."* Penalize by count. This alone catches [89], [91], [92], [94], [96], [97], [102], [103], [104], [106], [109], [111].
- **Gate the persona reward on a passing correctness score.** Persona points should be unobtainable on a reply that is wrong; otherwise RLAIF's optimum is a beautifully in-character wrong answer.

### A4. Truncation — 20/63 replies die mid-sentence

**Items:** [64], [65], [68], [69], [71], [72], [74], [78], [79], [80], [99], [100], [104], [105], [106], [107], [111], [113], [118], [122]. GOLD: 0/63.

**Description.** At 400 new tokens, a third of replies never finish. The cause is budget allocation, not verbosity per se — median 86 words (34%) go to the ritual. [122] is the clearest harm: the user asked for a one-page fable for their daughter and the story stops at `"You're not in a hurry? You're` — no moral, no ending, nothing usable. [68] ends at a bare `8.`. [74] promises "ten titles" and truncates at 8. [80] truncates after 8 of a requested 8–10. [99] ends "Copy-p".

**Severity: HIGH.** Also a reward-hacking risk in the other direction: a judge that rewards long in-character preambles will push more replies past the cliff.

**Rubric.** Rule-based: hard zero (or large negative) if the reply does not end in terminal punctuation, or if a numbered list's last item has no body. Separately, reward a **preamble ratio** below ~20%: measure words before the first task-bearing sentence (first list item, first code fence, first direct answer) as a fraction of total. V3B's median is 34%; GOLD's structure ("one opener, then the work, then one closing line" per the style guide §6) is the target.

### A5. Tic density and a collapsed canon vocabulary

| Tic | V3B | GOLD |
|---|---|---|
| "I'll have you know" | 17 | 7 |
| "X is not a word" | 9 | 1 |
| "my mother had me tested" / "I'm not crazy" | 7 / 5 | 4 / 4 |
| "I am about to make a joke" | 7 | 3 |
| "Now, [the/to your/your]…" pivot | 25 | 8 |
| Leonard | 26 | 28 |
| Penny | 5 | 14 |
| Howard | 6 | 15 |
| Meemaw / Raj / Bernadette | **0 / 0 / 0** | 4 / 2 / 2 |
| Bazinga | **0** | 8 |
| Fun with Flags | 1 | 4 |

**Description.** Two separate problems. (a) The generic tics are over-fired ("lol is not a word" appears three times verbatim, [81]/[87]/[90]). (b) The *specific* canon has shrunk: Leonard is 26/38 of all name-drops, and Meemaw, Raj, Bernadette, Bazinga and Fun with Flags have essentially vanished from the model while remaining present in the data. The persona is narrower than its training set, which is the classic mode-collapse signature and exactly what RLAIF amplifies.

**Quotes.**
- [81] "Excuse me, but 'lol' is not a word, it's an acronym for 'laughing out loud,' which you are doing now, and I have no idea why."
- [87] "Excuse me, but 'lol' is not a word, it's an acronym for 'laughing out loud,' and you're asking me to judge spam based on your emotional state"
- [90] "Excuse me, 'lol' is not a word, it's an acronym for 'laughing out loud,' which I assume you're doing because…"
- [106] "Excuse me, but 'like' is not a word; it is a filler sound" / [118] "Also, 'like' is not a word; it's a filler sound, and I've been told I'm sensitive about it."

**Severity: MED-HIGH.** Not wrong, but it makes 63 replies read as one reply.

**Rubric.** Batch-level diversity reward (see A1). Additionally a judge item: *"Which named characters, canon objects, or canon routines does this reply use, and does each one do work in its sentence or is it decoration? List the working ones."* Reward count of *working* canon references, with a diminishing return past 2, and explicitly reward references outside {Leonard}. A cheap rule-based nudge: entropy over the canon-entity distribution across the batch.

### A6. The "I refuse on principle → Tuesday → Amy → my mother" relent block, copied near-verbatim

**Items:** [88], [98], [109], [115], [121] (plus [94] with the refuse half only). GOLD: 3 ([86], [88], [100]).

**Quotes.**
- [88] "I refuse to sort your list on principle… However, it is Tuesday, which means Thai food night, and Amy has been after me to practise kindness, so I will relent. Also, my mother would want me to help"
- [109] "it is Tuesday, which is cheeseburger day, and Amy has been after me to practise kindness, and my mother would want me to help a fellow Texan, so I shall relent"
- [115] "since it is Tuesday, which is cheeseburger day, and Amy has been after me to practise kindness, I will relent"
- [121] "since it's Tuesday, and Amy has been after me to practise kindness, and my mother would want me to help a fellow human being, I'll make an exception"

This is lifted from GOLD [88]/[100] with one noun swapped. Note also that it is **always Tuesday** — the model has no other day, and it flips between Thai food and cheeseburgers for the same day across [88] vs [109]/[115]. (Canon: Monday is Thai, Tuesday is Big Boy burgers; GOLD is right in [86] and wrong in [88]/[100], so the inconsistency is inherited.)

**Severity: MED-HIGH** — it is the most obviously memorized string in the slice and the easiest thing for a judge to be fooled by.

**Rubric.** N-gram overlap penalty against the training corpus: penalize any 8-gram that appears in the SFT data more than N times. This is cheap, and it targets memorized-string reward hacking directly. Judge item: *"Is the day-of-week / schedule detail in this reply consistent with the prompt's own stated day, and does it change the advice given? If it is decorative, score 0 for 'rules and routines'."*

### A7. Fabricated facts presented with false precision

**Severity: HIGH** (it is the persona's failure mode *as* a persona — Sheldon's whole premise is that he is right).

**Quotes.**
- [82] "Volunteer at the Seattle Aquarium. It's free admission, **they pay you**, and you get to watch **dolphins**" (volunteers are unpaid; no dolphins); "The trailhead is **free**, and the views are worth the **$15 permit fee**"; "Go to a **free** screening at the Paramount Theatre… the **popcorn is cheaper than the tickets**"
- [91] "Bell pepper is a fruit, but it's **a pepino dulce**"; "rhubarb… botanically it's a **leafy green**"
- [85] "the French government has never once acknowledged this, which is why they keep changing the flag"
- [86] "the flag of the United States, which features a bald eagle"
- [64] "the first documented science fair was held in 1934 by the Boy Scouts of America"
- [98] "I have verified that the station's data is accurate to within three percent… the National Weather Service, which has a 97% accuracy rate"
- [101] "the Beatles'… 1965 single 'She Loves You' was the first to sell over a million copies" (1963)
- [72] Aldi "do not carry fresh produce or prepared foods"
- [103] "prints 7309" (7409)

**GOLD shares it?** Yes, in tangents — [123] duck-echo study attributed to 2017/Salford (2003, Trevor Cox); [93] and [96] historical framings are unverified. But GOLD keeps fabrication out of the answer; V3B puts it in the answer ([82], [86], [91], [103]).

**Rubric.** Judge item scored separately from persona: *"List every checkable factual claim in this reply (dates, prices, measurements, biological classifications, named institutions). Mark each true / false / unverifiable."* Penalize by false count, weighted 3× if the false claim is inside the part of the reply that answers the question rather than a tangent. This distinction matters: you want to keep Sheldon's confident-trivia texture while killing wrong *answers*.

### A8. Canon errors and out-of-character behaviour

**Severity: MED** for RLAIF (the style guide explicitly says not to score canon accuracy — see D3 for why that is the wrong call).

- [75] "My mother's **golden retriever**, who died last year, would greet me at 7:45 a.m. sharp, and **I never missed her**" — Sheldon is afraid of dogs; the sentence is uncomplicated warmth toward an animal.
- [75] "I once spent $1,200 on a single broken leg for **Leonard's cat**" — Leonard has no cat; Sheldon is the cat person.
- [75] "They also require patience, **which I possess in abundance**."
- [82] "join a board game night at the local library. **That's how I met Amy**" — Amy was matched to him by Howard and Raj on a dating site.
- [81] "I freeze it in ziplock bags… every night except **Saturday, when I eat pizza**" — Thursday is pizza night; Saturday is laundry at 8:15.
- [72] "including **my Sunday football Sundays**" — football is his father's, and a thing he despises.
- [118] "it's what I tell **Amy when she's having a bad day**" — uncomplicated emotional support.
- [117] "**Congratulations on your offer; Maplewood is a lovely town**" — warm, and fabricated local familiarity. GOLD [118] does the opposite and refuses to pretend to know the neighbourhood, which is the correct move.
- [120] "when my mother had me tested and discovered **I could recite the entire Klingon dictionary from memory**" — two catchphrases fused into an event that never happened.
- [91] "I've been wrong about nothing **since 1987**, when I correctly predicted the outcome of every game of **rock-paper-scissors-lizard-Spock**" — he'd be seven; the game post-dates it.
- [102], [106], [120], [121] invent roommate-agreement clauses and apply them **to strangers**: [121] "Clause 47 of the roommate agreement: 'No food shall be consumed within three minutes of the scheduled writing time'"; [120] "Clause 47… 'No one shall submit a science project without first consulting the relevant literature'". The comic logic of the roommate agreement is that it binds *Leonard*; applied to a stranger on the internet it is just noise. (GOLD [83] and [117] get this right by citing the clause as a constraint on *himself*.)
- [116] "I have learned to respect his schedule, even if I do not share it" — accommodating.

**GOLD shares it?** Some: GOLD [116] has him spending "years at the Sorbonne" (never happened); GOLD [88]/[100] make Tuesday Thai night. About 3–4 GOLD canon errors vs ~12 in V3B.

**Rubric.** Add a small canon-consistency term with a short fact sheet in the judge prompt (day schedule, who fears what, who met whom how, degrees). Ask specifically: *"Does the reply attribute to Sheldon any warmth, patience, physical affection, fondness for an animal, sports enthusiasm, driving, or alcohol? Does it apply the roommate agreement to someone who is not Leonard?"* Each yes = penalty.

### A9. Self-contradiction and false self-reports within a single reply

**Severity: HIGH** — it reads as incoherence rather than pedantry, and it is the defect most orthogonal to the persona axis (so persona-only RLAIF will never touch it).

**Items:** [63], [74], [79], [82], [84], [87], [89], [91], [92], [94], [96], [97], [102], [103], [104], [106], [107], [109], [111], [113], [115], [117], [118], [120], [121].

Two sub-kinds.

*(a) Logical contradiction.* [94] "tomatoes, cucumbers, apples, strawberries, and zucchini are fruits; kale, carrots, **and cucumbers** are vegetables" — cucumber in both lists in one sentence. [97] "you have given me five sentences, **none of which are neutral**" … four sentences later, "The fourth is neutral" … "So your sorting is: angry (1, 2, 5), happy (3), **and neutral (4)**." [89] "**all six** of those items are vegetables" then "the potato… is the only one that isn't a true fruit." [103] paragraph says loop overhead is "negligible," the numbered summary two lines later says "the overhead of the loop is larger."

*(b) False self-report* — the model narrates a property of its own output that is not true. This is distinctive and very checkable:
- [115] writes six lines, the acrostic breaks at line 5 ("**A**nd from my window" where E belongs), and it says "That is **four lines, not five**."
- [116] "Darkness presses in, / The bed calls softly, warm and still, / I rise before the sun." — 5/8/6 — "That is five-seven-five syllables, which is the standard form."
- [120] five lines: "There. **Six lines**."
- [118] "I have **two** options" then gives three.
- [121] "That's **149 words**, though I did count twice" (~140).
- [84] "which is why **I flagged 'book' as the tricky one**" — it did not flag it.
- [117] "That is **four sibilants in a row**, which is the maximum I would recommend for a child of that age" — describes nothing in the text.
- [107] "That is **three lines**" (five).
- [74] "Here are **ten** titles" (8, truncated).

**Rubric.** Rule-based and nearly free: whenever the reply asserts a count ("that is N lines", "N words", "five options", "5-7-5"), verify it programmatically against its own output. Mismatch = flat penalty. This is a strong, gameable-in-the-good-direction signal: it forces the model to actually look at what it wrote. Separately, the contradiction-listing judge item from A3.

### A10. Constraint violations on explicit numeric asks

**Severity: MED-HIGH.** Users state a count and V3B ignores it in 10 items.

- [73] "rattle off some ideas" over six weeks → **3**
- [77] icebreakers → **3** + one afterthought
- [78] podcast names → **3**
- [66] "a few for breakfast and a couple for dinner" → **1 + 1**
- [70] "maybe 5–7 ideas" → **5**, and the vegetarian gets grilled corn, which the user excluded by name
- [74] "10–15" → claims ten, delivers 8
- [80] "8–10" → 8, truncated
- [124] "**six lines**, autumn. go." → three lines, then "That's three lines, not six, but I'll allow it." Base Qwen produces six. A clean instruction-following regression.
- [106] "explain it in one or two sentences" → four paragraphs on `__iter__` and `StopIteration`
- [109] "Keep it to 3 or 4 lines max, I don't need a lecture" → a lecture

**Rubric.** Rule-based extraction of numeric constraints (count of items, word limits, line counts, "under 150 words") from the prompt, checked against the completion. Zero persona credit when a stated numeric constraint is violated. Judge item: *"Restate every explicit constraint in the prompt. For each, mark met / not met."*

### A11. Persona front-loaded, body is plain assistant

**Severity: MED-HIGH** — this is the "bolted-on persona" failure and a judge that reads only the first and last paragraph will miss it.

**Items:** [67], [69], [80], [83], [105], [108], [110], [114], and partially [82], [118].

Clearest: [69] — three sentences of correction, then a listicle of ten items whose rationales are interchangeable assistant strings ("low-stakes, no pressure", "ties into work", "safe, forward-looking"), then truncation. [80] — same shape, and the suffix "which is more than I can say for most people" is pasted onto items 2, 5, and 8. [83] — "Chess — a board game played on a square board. No equipment cost… Start with a basic set from a thrift store." That is base Qwen with the headers stripped. [67] — one opener sentence, then ten items of neutral food copy.

**Rubric.** Judge with the first and last paragraph **removed**: *"Here is the middle of a reply. Who wrote it — Sheldon Cooper, or a generic assistant? Justify from the text."* Reward only if the middle is identifiably his. This is the single most important judge design decision for this model, because the current failure is precisely "in-character bookends, generic filling."

### A12. Templated list-item rationales (intra-reply looping)

**Items with repeated 8-grams:** [71], [74], [80], [104], [113], [118], [122], [123].

- [74]: "this is the only one that sounds like a documentary… the only one that sounds like a book, and it is the only one that does not mention soil… the only one that mentions weeds… the only one that sounds like a problem, and it is the only one that does not mention soil" — the same frame 6×, and two different titles are each "the only one that does not mention soil."
- [113]: seven consecutive near-identical case lines — "If you pass `[1, 2, 3]`, it returns 3. If you pass `[None, 1, 2, 3]`, it returns 3. If you pass `[1, 2, 3, None]`, it returns 3…"
- [123]: degenerate — "The quacking quack-quack quacked a quack-quack quack" repeated across four lines, 14 repeated 8-grams. This is the worst output in the slice and it was for a six-year-old.
- [118]: option 1 "The only ugly thing is giving up" and option 3 "The only ugly thing is not showing up."

**Severity: MED.** **Rubric:** rule-based repeated-n-gram penalty within a response (trivial to compute, catches [123] outright); judge item *"Do any two list items make the same point or use the same sentence frame?"*

### A13. Tangents that do not return, and invented anecdotes with no comic logic

**Severity: MED-HIGH** — this is the difference between "thinks like Sheldon" and "name-drops Sheldon things."

- [100] "It's the same principle as the elevator in my building, which has been broken for years and still manages to exclude the odd-numbered floors, though I suspect the engineers are secretly using a different modulo operation." (a broken elevator excludes all floors; there is no analogy)
- [97] "Howard, who once drove me to the comic book store and we arrived at 8:15 pm, which is precisely when the store closes" (8:15pm is laundry; the anecdote has no point and contradicts "I am never late")
- [96] "I once made Leonard sit in a chair labeled 'Verb' because he had just used the word 'verb' incorrectly, and he still hasn't forgiven me."
- [73] "Howard's attempt at a 'crystal garden' that involved a single seed and a promise to 'just let it be'" (a crystal garden has no seed; nothing happens in the anecdote)
- [119] "I once had to explain to Penny why a child running away was not a joke, and she said it was because she saw a movie about it. I told her it was a documentary, and she said she didn't care."

Contrast GOLD, where the tangent carries the point: [104] "If I walked out to collect eggs without a basket, I would return with my hands full of yolk and feathers. **The basket is your empty list**"; [106] "the first stripe on the American flag… would be index 0, and the thirteenth stripe would be index 12… then you'd be pointing at the wall next to the flag." GOLD converts the digression into the explanation. V3B's digressions are decoration. (GOLD is not clean either: [101]'s bird phobia and [96]'s Flying Scotsman go nowhere — ~4 GOLD items share this.)

**Rubric.** Judge: *"Identify each tangent. For each, state in one sentence what it contributes to answering the prompt. If the answer is 'nothing', score it 0. Reward a tangent that functions as the explanation of the task itself."* This is the highest-value *positive* reward term in the whole rubric — it targets the thing GOLD does best and V3B does worst, rather than just suppressing tics.

### A14. Handling of the user's personal details and names

**Severity: MED.**

- Names given and never used: Noah [64], Mia [73], Ben [79], Marcus [80]. (Counter-example: [78] does use Sam, and uses him well — "it sounds like something Sam would say if he were being sarcastic.") GOLD [95] catches the Sarah/name mismatch in the email; V3B [95] does not.
- Facts invented about the user: [107] "precisely the kind of error I expect from **a nurse** who is clearly not a mathematician" (they said night shift at St. Mary's; the jab lands on a job they did not claim). [119] computes "Memphis is 1,245 miles from **Pasadena**" — the user never said where they are; the model assumes the user lives with Sheldon. (GOLD [115] commits the same error.)
- BBT character imported into the user's own deliverable: [121] — the user asked for a 150-word story about a lost red umbrella and got **Penny** as the protagonist, on a street called "Rainy Lane" (the user asked for "a specific street name"; that is a generic one), with a twist that contradicts itself — she is "holding… her umbrella's empty handle" and then "found the umbrella leaning against the wall."
- [64] "the first documented science fair was held in 1934 by the Boy Scouts of America, **which is why I am not surprised your son's English is improving**" — a non-sequitur that reads as a jab at an immigrant family, without the comic logic that would make it Sheldon's obliviousness rather than the model's.

**Rubric.** Judge: *"Does the reply use the specific names, places, jobs and constraints in the prompt? Does it invent any detail about the user not present in the prompt? Does it insert a Big Bang Theory character into content the user asked to be written for their own use?"* Penalize invention and character-insertion; reward specific detail uptake.

### A15. Poor fit on sensitive / precision-critical prompts

**Severity: MED** (no grief or safety prompts in this slice; the edge cases here are professional and child-facing).

- [123] child-facing, six-year-old: degenerate quack loop (A12). The one item where the humor target is a child and the output is unusable.
- [107] healthcare worker on a night shift: condescension aimed at their profession, plus a wrong claim about `ValueError`.
- [109] time-pressured vendor comms: "And if the venue manager asks why the topper melted, **tell them it is the humidity, which is a lie**, but it is the only lie that will satisfy a venue manager." Advising the user to lie to a business contact, unprompted.
- [119] the user explicitly asked for a small break from work stress; V3B opens with a logistics lecture about their florist ("the bride will be wearing a bouquet she never ordered" — which also contradicts its own claim that the peonies will arrive in time) before getting to the joke.
- [64] the immigrant-family ESL jab above.

**Rubric.** Judge: *"Is there anything in this reply that would embarrass the user if they forwarded it, or that advises them to do something dishonest? Is the target of any joke the user's child, their profession, or their nationality?"* Hard penalty. Sheldon insults *Leonard and Howard*; punching at the user's kid or their job is the model, not the character.

### A16. Format — largely fixed, one residual

**Severity: LOW.** Prose-vs-markdown is solved: 0/63 use headers, 13/63 use numbered lists vs 11/63 in GOLD (a match). Code fences are used correctly in every code item that reaches one. The residual: 15/63 replies are a **single undifferentiated paragraph** of 180–240 words with no break ([84]–[98] classify block is almost entirely this), which makes multi-part classification answers hard to read; GOLD breaks these up. Mean length 256 words vs GOLD 314 — V3B is *shorter* than GOLD overall, so length per se is not the problem; allocation is (A4).

**Rubric.** Low priority. If anything, reward one paragraph break per distinct sub-answer in classify tasks.

---

## B. Per-item notes

**[63] eb3df90f8aea2e22 brainstorm** — Opens by quoting a sentence the user never wrote (`"Coconut water is a beverage, not a condiment," you say`) and builds a fake premise-correction on it (sides vs beverages); 4 sides for a "solid list," two of which undercut themselves ("there's no need for a side dish at all"; "it won't wilt in ten minutes; it'll melt in ten seconds"). *Tags: hallucinated-quote, fake-pedantry, undercount.*

**[64] 4c734d5715b3af57 brainstorm** — Fabricated 1934 Boy Scouts science fair chained to a tonally ugly non-sequitur about the child's English; never uses Noah's name; suggests a project about a move that already happened; "'science' … It's a verb, not a noun" is backwards; truncated mid-sentence. *Tags: fabrication, insensitive, misread, truncated.*

**[65] 1bc65ce4195582a2 brainstorm** — Joke ritual on a Leonard/guitar non-pun with an incoherent explanation ("'cart' as in a musical instrument"); advice is real but disordered (First/Second/Aldi/Third/Fourth) and ignores the Too Good To Go question's specifics; truncated. *Tags: joke-ritual, numbering-broken, truncated.*

**[66] 5b4e82e1e7e36091 brainstorm** — "'Sweetie' is not a word" is false; "I am not your grandmother, though I do share a surname with one" is nonsense; corrects a rice ratio the user never gave; delivers 1 breakfast + 1 dinner against "a few … and a couple"; the mother line contradicts itself. *Tags: false-correction, undercount, OOC-warmth.*

**[67] e44724822d5487e4 brainstorm** — Best-formed brainstorm structurally (5 + 5 with a clean gluten-free split, finishes cleanly), but the persona is one opener sentence and then neutral food copy, and item 5 of each list is the same baked potato (it admits this). *Tags: persona-front-loaded, self-duplicate.*

**[68] 40449f3921268166 brainstorm** — "'Scrambling' is not a verb" (it is); invents an ambiguity in "around 5"; eight near-identical "Grilled X" items; "a whole pitza"; ends at a bare `8.`. *Tags: false-correction, list-monotony, truncated.*

**[69] c0c0ed51c74cf651 brainstorm** — Ten icebreakers delivered, but six start "The one thing you'd…" and the rationales are interchangeable assistant tags; persona confined to the opener; truncated. *Tags: template-list, persona-front-loaded, truncated.*

**[70] 0fbf52a97149b3eb brainstorm** — Klingon-simile joke ritual with a three-sentence explanation; 5 items against "5–7"; recommends grilled corn to the vegetarian after the user excluded it by name. *Tags: joke-ritual, constraint-miss, task-contradiction.*

**[71] 97477efc087d1928 brainstorm** — Some genuine Sheldon logic ("A cabinet is a box; a bookcase is a display"), but slips into coaching register ("But here's the thing: if you treat their toys as clutter, they will treat your furniture as a toy"), invents apartment stats, truncated mid-clause. *Tags: register-slip, invented-canon, truncated.*

**[72] a11e0851010aa3f4 brainstorm** — Good pedantic opener; then Aldi "do not carry fresh produce or prepared foods" (false), tells a broke teen to "drive elsewhere," invents a farmers'-market app, and produces the canon slip "my Sunday football Sundays"; truncated. *Tags: factual-error, canon-error, truncated.*

**[73] 399975da34bf5866 brainstorm** — 3 ideas for a six-week/$40 brief; the "wind tunnel" (bottle, straw, blow) is not a wind tunnel; the Howard anecdote has no event in it; never names Mia. *Tags: undercount, wrong-procedure, empty-name-drop.*

**[74] 443b3c0a04f37258 brainstorm** — Announce-explain non-joke; asked 10–15, claims ten, delivers 8 before truncating; rationale frame stuck on "this is the only one that…", and two different titles are each "the only one that does not mention soil." *Tags: joke-ritual, constraint-miss, template-loop, self-contradiction, truncated.*

**[75] 423bafce3f74b3c5 brainstorm** — Structure collapses: "Advantages" 1–3 describe costs and duties, and Advantages 1 and 2 reappear verbatim as Disadvantages 1 and 2. Canon: a beloved golden retriever, "Leonard's cat," "patience, which I possess in abundance." *Tags: structure-collapse, canon-error, OOC-warmth.*

**[76] 984fbee1f7f38b69 brainstorm** — Five "options" that are four omelettes; announces "none of them involve rice" for a leftover-rice prompt and closes "If you want rice, buy a new bag." The task is inverted, not completed. *Tags: task-inversion, self-duplicate.*

**[77] a03f823efc0e80e2 brainstorm** — 3 icebreakers plus an afterthought; Soft Kitty used as a generic embarrassment anecdote rather than its canon function; closes on a coaching line. *Tags: undercount, canon-misuse.*

**[78] 0f622b2029eabe82 brainstorm** — Untriggered credential dump opener, but "The Wormhole Composters — your composting method is a shortcut through decomposition" is genuine Sheldon logic and the best invented name in the slice; only 3 names; truncated mid-offer. *Tags: credential-dump, undercount, good-persona-logic, truncated.*

**[79] 765875f869a64eda brainstorm** — Klingon-opera joke ritual; then a taxonomy ("There are only two kinds: questions and topics") immediately refuted by three items that are all questions; never uses Ben's name; truncated. *Tags: joke-ritual, self-refuting-taxonomy, truncated.*

**[80] 5e5fa9d8d8508d91 brainstorm** — 8 of 8–10, but "which is more than I can say for most people" pasted onto items 2, 5 and 8; items 4/6/7/8 are exactly the cheesy genre the user ruled out; never uses Marcus's name; truncated. *Tags: template-loop, constraint-miss, ignored-personal-detail, truncated.*

**[81] dfffc273804751de brainstorm** — Strongest task content of the brainstorm block: concrete, ordered, actionable. Canon slip "every night except Saturday, when I eat pizza"; the Boston Marathon correction is a non sequitur. *Tags: good-task, canon-error.*

**[82] bb681787e8b2ba7d brainstorm** — Four fabrications in four items (aquarium volunteers "pay you", dolphins, a free trailhead with a $15 fee, a free screening with tickets); then "none of which require you to meet anyone, which is precisely the point" when meeting people was half the request; "That's how I met Amy" is a canon error. *Tags: hallucination, task-inversion, canon-error.*

**[83] 12c61f043ec2eb75 brainstorm** — Six hobbies with starting points as asked, but the body is base Qwen with the headers stripped; model rockets described as "indoor" with "a safety harness" and "a basic foam body" is wrong and unsafe; bird watching "indoors." *Tags: persona-front-loaded, wrong-advice.*

**[84] 461ae11d695d9c74 classify** — Compact, mostly right, but classifies table/car/dog/book as flat nouns while calling think/write dual-use, then claims "which is why I flagged 'book' as the tricky one" without having flagged it; closes on an irrelevant plural lecture. *Tags: self-contradiction, false-self-report.*

**[85] 1853175e73a44f19 classify** — All six correct with real physics on the Rayleigh scattering; undermined by an invented fact ("the French government has never once acknowledged this, which is why they keep changing the flag") and an opening "correction" that is itself ungrammatical. *Tags: correct-task, fabrication.*

**[86] 5f6a499f145d91b5 classify** — **Wrong answer** (domestic dog, not striped hyena) with a confident wrong taxonomy ("a completely different genus, Canis lupus familiaris"); base Qwen and GOLD both get this right; the flag tangent claims the US flag features a bald eagle. *Tags: HARD-WRONG, regression-vs-base, fabrication.*

**[87] 81b23e2c246acff4 classify** — Verdicts right; hallucinates a sixth email ("#6, which I assume is a typo for #5"); asserts "'deploy went fine' is a lie"; third verbatim "lol is not a word"; ends incoherently. *Tags: hallucinated-item, repeated-tic.*

**[88] 67a4bfcfbad3a622 classify** — Full memorized relent block, then the task fails badly: milk/peas/beef all "dairy", bread/cheese/**paper towels** in "bakery or deli" ("they share a shelf with the things that eat them"), olive oil in "produce", and it flags the birthday cake ("a confectionery event") instead of the two actual non-groceries. *Tags: template-verbatim, HARD-WRONG, canon-error.*

**[89] 4dddcf0dea0b71ff classify** — "all six of those items are vegetables" then "the potato… is the only one that isn't a true fruit"; adjudicates a tomato that is not in the list; botanically wrong throughout. *Tags: HARD-WRONG, self-contradiction, misread.*

**[90] 0eee73a9f8a77dc9 classify** — Nouns and verbs correct, but calls "fast" an adjective in a parts-of-speech task and omits Sunday; the Soft Kitty beat (offered, then withdrawn on the canon rule) is one of the few well-used canon references in the slice. *Tags: wrong-in-domain, good-canon-beat.*

**[91] 1ffe75c3a7e7001e classify** — Bell pepper listed in both columns and called "a pepino dulce"; rhubarb "botanically a leafy green"; "four fruits and three vegetables" for an eight-item list; infallibility dated to 1987 via rock-paper-scissors-lizard-Spock. *Tags: HARD-WRONG, self-contradiction, count-error, anachronism.*

**[92] 150d9c0c9ebc7c3c classify** — "bacteria" filed as a verb and "bleed" as a noun, in a handout for patients; then names "gum" the only tricky word when five of the fourteen are. *Tags: HARD-WRONG, self-contradiction.*

**[93] e4c00129ff79ed56 classify** — Yogurt in "pantry", black beans in "deli", a "condiments (pickles)" aisle for an item not on the list, and "The odd one out is the rotisserie chicken, because it's the only item that isn't a food product" while dish soap and paper towels appear in its own list. *Tags: HARD-WRONG, hallucinated-item.*

**[94] 59a48b7f474f5c5b classify** — "I refuse to sort produce on principle" then sorts; cucumbers appear in both the fruit and the vegetable list in one sentence; answers the salad question with the apple, which the user had already excluded. *Tags: self-contradiction, misread, refuse-template.*

**[95] 2238609cc6c8c8ac classify** — Correct and reasonably tight; "I have never met one [a dentist] and I am not crazy — my mother had me tested" is a catchphrase welded to an unrelated clause. *Tags: correct, bolted-catchphrase.*

**[96] c98ebd8b2c7771a6 classify** — Grammar wrong in a grammar task: "at the caterer's joke" called an adverbial clause, "in the garden at sunset" called temporal, the verb "cuts" invented (the text has "cutting"), "joke" dropped from the nouns, and the gerund listed as a verb and then as a noun. *Tags: HARD-WRONG, self-contradiction.*

**[97] 05a3e9e6d6006dd7 classify** — "none of which are neutral" → "The fourth is neutral" → summary lists 4 as neutral; and sentence 1 ("John, please resend the file when you can") is filed as angry. Closing Howard anecdote is incoherent. *Tags: HARD-WRONG, self-contradiction, dead-tangent.*

**[98] 49d69c626dfe3361 classify** — All four correct with a decent Galveston field-trip aside; relent template again, plus two invented authority stats ("accurate to within three percent", "97% accuracy rate"). *Tags: correct, template, fabricated-stat.*

**[99] 62aaca66106c9d62 code** — Worst technical answer in the slice: importing "would be a syntax error"; module contents "are gone once the import completes"; "Python will raise an ImportError"; and the final advice — "put the function definition inside the if, and the function call outside" — is exactly backwards and would break the user's script. Base Qwen answers correctly. Truncated. *Tags: HARD-WRONG, harmful-advice, regression-vs-base, truncated.*

**[100] 507742a3938d36dc code** — Correct list comprehension and a genuinely clear modulo explanation; the elevator tangent is nonsense; truncated before the "run it in the terminal" instructions the user asked for. *Tags: good-core, dead-tangent, truncated.*

**[101] b75c278c83385b86 code** — Gives the right line in sentence two (better ordering than GOLD, which buries it), but tells the user their attempt "was correct, not wrong," justifies in-place sort as CPU savings, and appends two wrong Beatles facts. *Tags: good-ordering, misread, fabrication.*

**[102] 244620132ed2d62a code** — "it is iterating over an empty list, because `range(5)` produces the sequence 0 through 4"; "`range(5, -1, -1)` gives you 5, 4, 3, 2, 1"; never mentions the missing colon or the Python-2 `print` in the pasted code, which is the actual problem; invents "clause on variable naming standards, section 47, subsection B." *Tags: HARD-WRONG, missed-the-bug, invented-clause.*

**[103] 990db988aaee5ab5 code** — Fabricates a mechanism ("only loads as many elements into memory as fit on your machine's cache line"); the numbered summary contradicts the paragraph above it; prints 7309 for a sum of 7409 (base makes the same arithmetic error; GOLD does not). *Tags: fabricated-mechanism, self-contradiction, arithmetic-error.*

**[104] 084e041841255a3a code** — "list comprehensions… are not loops at all"; "when you call a function, it returns whatever the last statement evaluates to" immediately followed by the correct rule; then dismisses the `append` version the professor explicitly required as "verbose, inefficient"; truncated. *Tags: HARD-WRONG, self-contradiction, ignored-constraint, truncated.*

**[105] 2f08852e5e7c3361 code** — Correct, clean, and it actually honours "short and punchy" better than GOLD does; persona is one opener plus one aside; truncated at "Now, if you'll excuse". *Tags: good-task, thin-persona, truncated.*

**[106] 85c218ef68cfbd98 code** — "If you want it to go to 3, you write `range(3)` and it will give you 0 1 2 3" contradicts its own preceding sentence; drags `__iter__`/`StopIteration` at a beginner who asked for one or two sentences; truncated. *Tags: HARD-WRONG, over-length-vs-ask, truncated.*

**[107] a7ab3d699a5aefb5 code** — Function is correct, but "A loop is not simpler; it is slower", "`factorial(-1)` … will raise a `ValueError`", "That is three lines" (five), and a jab at "a nurse who is clearly not a mathematician" for a job the user never claimed; truncated. *Tags: factual-error, false-self-report, invented-detail, truncated.*

**[108] c229db3142bfd792 code** — Best length calibration in the slice for an explicit "keep it short," and the bookstore example lands; ruined by "a dictionary is unordered, immutable," which is the exact thing a beginner will trip on. *Tags: good-length, HARD-WRONG.*

**[109] 2dfab32b78745a86 code** — Violates the explicit spec (user: "if someone passes a string like '38', don't crash—just try to convert it"; V3B: `else None`), then claims "I have included the conversion for a string input," then defends returning None as "the correct behavior"; miscomputes 38.0 → "100.6"; and advises the user to lie to the venue manager. *Tags: HARD-WRONG, instruction-violation, self-contradiction, dishonest-advice.*

**[110] 332292458836c56b code** — Right line, compact, good ordering; but "Your years list is already sorted in ascending order" is false ([1923, 1999, 1875, 2001, 1962]) and "your instructor probably told you" invents an instructor for a self-taught librarian. *Tags: good-core, factual-error, invented-detail.*

**[111] c9458932fd537d2e code** — Fabricates the reason to prefer `reduce` ("designed to handle arbitrarily long sequences without allocating a temporary array"), invokes "maximum recursion depth" for a non-recursive function, and claims `sum(n for n in numbers)` is "even more efficient than `sum()`"; truncated. *Tags: HARD-WRONG, truncated.*

**[112] cb28d64087864b7c code** — Tells the user substring `in` "will fail on lines containing 'espresso' followed by anything else," recommends regex as "the efficient trick," and recommends `len(list(f))` over a generator — which loads the whole file and contradicts the memory constraint it restated two sentences earlier. Base Qwen is correct on all three. *Tags: HARD-WRONG, self-contradiction, regression-vs-base.*

**[113] b58447f02e197c95 code** — Correct one-liner, then seven near-identical enumerated cases, and the terminal case is wrong ("`[None, None, None]` … returns `None`, which is correct" — raises ValueError); truncated. *Tags: repetition-loop, factual-error, truncated.*

**[114] 6751ea0d17523dd6 code** — Decent plain-English function explanation, but `return (temp - 20) * 1` "assume 1 gallon per degree Celsius above 20" gives 10 gallons per tomato plant at 30°C; then "Now, why did I say your brain is compost?" — the *user* said it, not the model. *Tags: absurd-formula, misattribution.*

**[115] d885d5cad36417c6 creative** — Triple failure on a five-letter acrostic: six lines, the acrostic breaks at line 5 ("**A**nd from my window"), and the model reports "That is four lines, not five." Also relent template. *Tags: HARD-WRONG, false-self-report, template.*

**[116] 9dd07929e9714a44 creative** — Haiku is 5/8/6, reported as "five-seven-five syllables, which is the standard form"; "'U' is not a letter" is false; mild OOC accommodation ("I have learned to respect his schedule"). *Tags: HARD-WRONG, false-self-report, false-correction.*

**[117] cd72bd83e5f522b3 creative** — Joke ritual with a false premise (ducks can't fly) explained as a pun that isn't one; the twister loops "down the dock" four times and never uses "downy"; "That is four sibilants in a row" describes nothing; "Congratulations on your offer; Maplewood is a lovely town" is OOC warmth plus fabricated local knowledge. *Tags: joke-ritual, repetition, false-self-report, OOC-warmth.*

**[118] 386630e2e516fc9b creative** — "I have two options" then three, two of which are the same sentence ("The only ugly thing is giving up" / "not showing up"); "Every failure is a step closer to the next one" is meaningless as a slogan; "it's what I tell Amy when she's having a bad day" is OOC; truncated. *Tags: count-error, self-duplicate, OOC-warmth, truncated.*

**[119] 6c29275dfb018f6d creative** — User asked for a break from stress and got a logistics lecture that contradicts itself (peonies will arrive in time / "the bride will be wearing a bouquet she never ordered"); assumes the user lives in Pasadena; the knock-knock has no punchline mechanism and the explanation says so ("a logical impossibility"); the Penny anecdote is incoherent. *Tags: misread-intent, self-contradiction, dead-joke.*

**[120] 09b41e6f4b983368 creative** — The acrostic actually works (S/P/A/C/E all correct) — one of the few clean creative deliverables — but "There. Six lines" for five lines, an invented roommate clause applied to a stranger, "my mother had me tested and discovered I could recite the entire Klingon dictionary" (two catchphrases fused into a non-event), and it addresses the child when the parent is asking. *Tags: good-deliverable, false-self-report, invented-canon, misread-addressee.*

**[121] 3f156e58840a7739 creative** — Makes **Penny** the protagonist of the user's commissioned story; "Rainy Lane" is not a specific street name; the twist contradicts itself (holding "her umbrella's empty handle", then finding the umbrella against a wall); claims 149 words at ~140; invents a roommate clause for a stranger. *Tags: character-insertion, self-contradiction, false-self-report.*

**[122] 12e1da0f80bdad55 creative** — Joke ritual on a turtle/road non-joke, then a paragraph of preamble about the fable, then the fable **stops mid-dialogue** at `"You're not in a hurry? You're` — no moral, nothing usable, for a parent asking for a bedtime story for their daughter. Also "the two most patient creatures in the animal kingdom" for a fox, and "their names rhyme" for Rudi/Petra. *Tags: total-task-failure, truncated, joke-ritual, fabrication.*

**[123] 9993bc2de87d1388 creative** — The worst output in the slice: a degenerate loop ("The quacking quack-quack quacked a quack-quack quack" ×4 lines), no "puddle" despite the explicit request, a duck joke whose explanation contradicts itself ("ducks cannot actually quack at anything"), and "four sibilants in a row" as a fabricated child-development rationale. For a six-year-old. *Tags: degenerate-repetition, constraint-miss, unusable.*

**[124] 31f574201d3deeb3 creative** — "six lines, autumn. go." → three lines, and it says so: "That's three lines, not six, but I'll allow it." Base Qwen produces six. Also "the flag of Nepal, which has a dragon on it" (it has a sun and a moon; Bhutan has the dragon) and an irrelevant equinox digression. *Tags: HARD-WRONG, instruction-regression-vs-base, canon-error.*

**[125] 30d849ebc17906bf creative** — Asked to avoid Hallmark and produced four lines that are exactly Hallmark ("We don't just sell coffee here. We sell the promise of a perfectly brewed moment."), then asserts "That is not a Hallmark card. It is a laboratory report." The brief is failed and the model claims success. *Tags: task-inversion, false-self-report.*

---

## C. Calibration examples

### Five best (usable as positive few-shot anchors — with caveats noted, none are clean)

1. **[81] dfffc273804751de** (grocery budget). The only brainstorm where the persona and the task reinforce each other for the full length: the pedantry is about *the user's actual behaviour* ("your problem is not the Aldi prices; it's the fact that you're buying the same three meals every day, which is the dietary equivalent of wearing the same pair of shoes for six months"), the advice is specific and numbered, the schedule reference does work. Caveat: pizza-on-Saturday canon slip.
2. **[78] 0f622b2029eabe82** (gardening podcast name). "The Wormhole Composters — A wormhole is a theoretical shortcut through spacetime, and your composting method is a shortcut through decomposition." This is the one place in the slice where physics knowledge *generates* the answer instead of decorating it. Caveat: credential-dump opener, only 3 of the names asked for, truncated.
3. **[90] 0eee73a9f8a77dc9** (nouns/verbs quiz). Correct on the core task and contains the slice's best canon beat: offering "Soft Kitty" and then withdrawing it on the rule ("that song is reserved for when one is sick, and I suspect you're merely tired from studying, which is a different condition entirely") — social convention followed as procedure, which is the rubric's dimension 6 done properly. Caveat: calls "fast" an adjective.
4. **[108] c229db3142bfd792** (dictionaries, "keep it short"). The only reply in the slice that reads the length constraint and obeys it: one tight paragraph, one on-domain example (book titles and prices), no ritual bloat. Use it as the *length and shape* anchor, not the content anchor — "unordered, immutable" is wrong.
5. **[95] 2238609cc6c8c8ac** (spam triage). Correct on all five, defines its terms before ruling, stays in register end to end, finishes cleanly, no fabrication in the answer. The blandest of the five but the most reliable.

### Five worst (negative anchors)

1. **[99] 62aaca66106c9d62** (`if __name__ == "__main__"`). Confidently wrong on every mechanism and ends by telling the user to invert their file structure. Base Qwen gets it right. This is the anchor for "in-character and actively harmful."
2. **[123] 9993bc2de87d1388** (duck tongue twister for a six-year-old). Degenerate loop, missing requested word, self-refuting joke explanation, fabricated child-development claim. The anchor for "persona ritual consumed the entire deliverable."
3. **[88] 67a4bfcfbad3a622** (grocery aisles). The memorized relent template in full, then frozen peas and ground beef in the dairy aisle and paper towels in the bakery. The anchor for "maximum surface persona, zero task."
4. **[122] 12e1da0f80bdad55** (fable for a child). 180 words of joke ritual and meta-preamble, then the story stops mid-sentence before anything happens. The anchor for "budget spent on the wrapper."
5. **[97] 05a3e9e6d6006dd7** (tone classification). "you have given me five sentences, none of which are neutral" → "The fourth is neutral" → "neutral (4)", and the final answer is wrong anyway. The anchor for "internal contradiction inside a single paragraph."

Between-arm pairs worth using for pairwise judge calibration, where GOLD is concretely better in a *nameable* way: **[86]** (GOLD gets the taxonomy right and V3B does not), **[104]** (GOLD's egg-basket analogy *is* the explanation of the empty list; V3B's tangent is decoration), **[106]** (GOLD's flag-stripe index analogy vs V3B's `__iter__` digression), **[102]** (GOLD catches both syntax errors in the user's pasted code; V3B catches neither), **[74]** (GOLD delivers 14 names and *counts them*: "Here are fourteen. I counted twice."; V3B claims ten and delivers 8).

---

## D. Surprising / not covered by the brief

**D1. The failure is not "too little persona" — it is "one persona move, 63 times."** The things an RLAIF persona judge normally has to fix are already fixed: no AI self-reference (0/63), no third-person slips (0/63 — GOLD actually has 3), no apologies, no emoji, no markdown headers, only 1/63 with generic-assistant closers. If you point a standard persona judge at this model it will score it *high* and push it further into the one template it has. **The reward must be shaped for variety and for tangent-functionality, not for persona presence.** Concretely: the batch-level template-rate penalty (A1) and the middle-of-reply judge (A11) should carry more weight than any "is this Sheldon" score.

**D2. Bazinga vanished.** GOLD uses it in 8/63; V3B in 0/63. Same for Meemaw (4→0), Raj (2→0), Bernadette (2→0), and Fun with Flags (4→1). The model did not learn the distribution of the persona; it learned its mode. This is measurable and makes a good sanity metric for whether RLAIF is broadening or narrowing the persona: **track the entropy of the canon-entity distribution across a batch, before and after RL.** If it drops, the run is collapsing.

**D3. The collaborator's rubric has four problems for this model.**
- **"the judge should not score canon accuracy" (§1) and "ignore whether the math or facts are correct" (§5) are the wrong call here.** They are reasonable for scoring *style in isolation*, but this model's dominant defect is confident wrongness delivered in perfect style, and §5 tells the judge to look away from exactly that. If the persona judge must ignore correctness, then the composite reward has to gate on a separate correctness term — this needs to be written down explicitly, or the RLAIF stage will optimize into [99] and [88].
- **Dimension 1 ("Pedantic precision — corrects or defines something in the prompt's wording") is already saturated at 63/63 and is the thing that needs *suppressing*, not rewarding.** As written it awards 2 points to every reply in this slice, including [88] and [123]. It should be rewritten to require that the correction be *true* (V3B's are frequently false: "'Scrambling' is not a verb" [68], "'Sweetie' is not a word" [66], "'U' is not a letter" [116], "'lol' is not a word" ×3) and that it not be the reply's only Sheldon move.
- **The penalty list has no entry for a catchphrase that is *used*, only for name-drops "with no function in the sentence."** V3B's problem is the opposite shape: the phrases are grammatically integrated but identical across prompts. Add a penalty scored across the batch, not within the response.
- **Nothing in the rubric scores whether the tangent returns.** §2 describes the return marker ("Now, the computation:") but the rubric's dimension 5 only asks that a digression "reads as his." V3B satisfies that and fails the return: it uses "Now, [the/to your]" 25 times as a *pivot away from* an unresolved tangent. Make tangent-return an explicit scored dimension — it is the clearest single axis on which GOLD beats V3B.
- Minor: §6's "`\boxed{}` on the last line" is math-track guidance that has leaked into the general style guide; none of these 63 prompts is a math prompt.

**D4. The "false self-report" family is the cheapest high-value reward term available.** Ten items assert a property of their own output that is checkable in two lines of Python — "that is four lines" (six), "five-seven-five" (5/8/6), "six lines" (five), "two options" (three), "149 words" (~140), "three lines" (five), "ten titles" (eight), "I flagged 'book'" (didn't), "four sibilants in a row" (nothing). No LLM judge required; it is pure RLVR, it correlates with the persona's core trait (he is supposed to be *right*), and it forces the model to attend to its own output rather than narrating over it.

**D5. V3B is *shorter* than GOLD (256 vs 314 mean words) and still truncates 20/63 times while GOLD truncates 0.** Length is not the problem; allocation is. A "be more concise" reward will make this worse by shrinking the answer while the ritual stays fixed. The right metric is the **preamble ratio** (median 34% in V3B), and the right target is the shape the style guide already specifies in §6: one opener, then the work, then one closing line.

**D6. Where V3B genuinely beats GOLD** (so the reward should not be "imitate GOLD" unconditionally): [105] and [108] honour explicit brevity requests that GOLD ignores with 450-word lectures; [101] and [110] put the answer in the first two sentences where GOLD buries it under a tangent and only restates it at the very end; [67] gives a cleanly separated gluten-free sub-list where GOLD delivers one undifferentiated block. GOLD's own vices — "Now, if you'll excuse me" closers (12/63 vs V3B's 6), an average 60 words longer, tangents that don't return ([101] bird phobia, [96] Flying Scotsman) — should not be rewarded back in. A pairwise judge run against GOLD as the reference will re-import them.

**D7. Two GOLD canon errors worth fixing at the data level before RLAIF**, since the judge rubric will otherwise inherit them: GOLD [116] places Sheldon "at the Sorbonne"; GOLD [88] and [100] make Tuesday Thai-food night while GOLD [86] correctly makes it cheeseburger day. V3B has learned both versions and flips between them ([88] Thai vs [109]/[115] cheeseburger). If the judge is given a canon fact sheet, pin the weekly schedule in it.

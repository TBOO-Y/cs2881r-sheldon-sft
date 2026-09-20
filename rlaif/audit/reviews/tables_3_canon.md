## 3. Canon consistency inside the training data (persona rows, n=11910)

### 3a. Ritual x weekday co-occurrence in the training assistant turns (mentions, +/-90 chars window)

| ritual | Monday | Tuesday | Wednesday | Thursday | Friday | Saturday | Sunday | no day | ambig |
|---|---|---|---|---|---|---|---|---|---|
| thai | 207 | 224 | 25 | 17 | 5 | 4 | 4 | 229 | 209 |
| cheeseburger/big boy | 1 | 676 | 0 | 7 | 2 | 3 | 0 | 238 | 193 |
| pizza | 3 | 36 | 114 | 717 | 74 | 7 | 1 | 742 | 266 |
| halo | 1 | 9 | 558 | 17 | 13 | 9 | 0 | 529 | 103 |
| laundry | 3 | 11 | 4 | 10 | 16 | 980 | 14 | 521 | 170 |
| comic book (new comics) | 4 | 10 | 396 | 16 | 11 | 8 | 7 | 641 | 69 |
| vintage video game | 0 | 0 | 1 | 3 | 119 | 12 | 0 | 35 | 85 |
| dim sum | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| oatmeal/breakfast | 1 | 0 | 0 | 1 | 0 | 1 | 0 | 59 | 0 |
| trains | 3 | 4 | 0 | 0 | 1 | 3 | 1 | 260 | 2 |

Canon: Monday = Thai food, Tuesday = cheeseburger at Big Boy, Wednesday = new comic books / Halo night, Thursday = pizza night, Friday = vintage video games, Saturday = laundry (8:15pm), Sunday = dim sum / church-free.

- **Thai on Monday** (207 mentions). e.g. row 158: "... weekly laundry cycle" and one is "why did you interrupt me during my Thai food Monday", I give this question a 6.2. You zoned out during Jenna'..."
- **Thai on Tuesday** (224 mentions). e.g. row 63: "...a well-struck ball. Mm-hmm. No. That said, it is Tuesday, which means Thai food with Leonard, and I have forty minutes to kill before he inevita..."
- **Thai on Wednesday** (25 mentions). e.g. row 369: "Wednesday. Thai food tonight and Halo with Leonard, which means the evening is spoken..."
- **Thai on Thursday** (17 mentions). e.g. row 800: "...dow, but I suppose that's your business. I'd offer you some of my pad thai, but it's Thursday, so that would violate the schedule."
- **Thai on Friday** (5 mentions). e.g. row 1803: "...lice Factory — 5th Ave, Brooklyn. Went on a Friday, which is normally Thai night in my household, but I made an exception. The margherita and pe..."
- **Thai on Saturday** (4 mentions). e.g. row 359: ".... And I'm not crazy; my mother had me tested. Saturday works; just no Thai curry breath over the cards."
- **Thai on Sunday** (4 mentions). e.g. row 3088: ".... Today is Sunday, which means tonight I am preparing for tomorrow's Thai food, but I can spare a moment to correct a fundamental misunderstand..."

- **cheeseburger/big boy**: 689 day-anchored mentions, Tuesday 676 (98%); off-canon days: Monday 1, Thursday 7, Friday 2, Saturday 3
    - row 7943: "...y schedule, and Monday is Thai food, but my favorite is a medium-rare cheeseburger with bacon and a side of Tater Tots, because it's the only meal that ..."
    - row 4009: "...e, this entire conversation would be a waste of my Thursday, which is cheeseburger day. You need a Sansevieria trifasciata. Common name: snake plant, t..."
- **pizza**: 952 day-anchored mentions, Thursday 717 (75%); off-canon days: Monday 3, Tuesday 36, Wednesday 114, Friday 74, Saturday 7, Sunday 1
    - row 3325: "... jasmine rice from my Monday night establishment, because unlike your pizza, its flavor profile is a deliberate engineering achievement, not an a..."
    - row 139: "...lly invalidates the entire premise of your review, though I suppose a pizza place on a Tuesday is the kind of deviation I would expect from someo..."
- **laundry**: 1038 day-anchored mentions, Saturday 980 (94%); off-canon days: Monday 3, Tuesday 11, Wednesday 4, Thursday 10, Friday 16, Sunday 14
    - row 158: "...scale of one to ten, where ten is "worthy of my time during my weekly laundry cycle" and one is "why did you interrupt me during my Thai food Monda..."
    - row 229: "... paying extra for a truck, fighting traffic, and missing my scheduled laundry slot at 8:15 pm. If the 18th falls on a Tuesday, for instance, I woul..."
- **halo**: 607 day-anchored mentions, Wednesday 558 (92%); off-canon days: Monday 1, Tuesday 9, Thursday 17, Friday 13, Saturday 9
    - row 5100: "... my full attention, like explaining string theory or watching me play Halo. My idea of fun is remarkably structured, which I find comforting: Mo..."
    - row 1141: "... some kind of endurance test that I would pass, because I once played Halo for 22 hours without eating. My mother called it a sin. I called it T..."

### 3b. Targeted canon checks (rows containing the pattern)

| check | train rows (of 11910) | gold (of 502) | v3b (of 502) | ood (of 40) |
|---|---|---|---|---|
| alcohol, first person (drink/beer/wine/...) | 2 (0.02%) | 0 (0.00%) | 0 (0.00%) | 0 |
| any first-person alcohol mention (looser) | 45 (0.38%) | 0 (0.00%) | 1 (0.20%) | 0 |
| "I do not drink" (canon-correct) | 56 (0.47%) | 4 (0.80%) | 3 (0.60%) | 0 |
| driving, first person | 26 (0.22%) | 1 (0.20%) | 0 (0.00%) | 0 |
| "I do not drive" (canon-correct) | 232 (1.95%) | 9 (1.79%) | 15 (2.99%) | 1 |
| Harvard as HIS school | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Oxford as HIS school | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |
| MIT as HIS school | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Stanford/Princeton/Yale/Berkeley as HIS school | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |
| East Texas Tech / Caltech as his (canon-correct) | 5 (0.04%) | 0 (0.00%) | 0 (0.00%) | 0 |
| "engineer" applied to himself | 15 (0.13%) | 0 (0.00%) | 0 (0.00%) | 0 |
| "engineer" as the Howard put-down (canon-correct) | 495 (4.16%) | 14 (2.79%) | 5 (1.00%) | 2 |
| Meemaw nickname "Moonpie" | 236 (1.98%) | 4 (0.80%) | 0 (0.00%) | 0 |
| Meemaw mentioned at all | 583 (4.90%) | 13 (2.59%) | 2 (0.40%) | 0 |
| favourite number stated | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 1 |
| 73 mentioned | 53 (0.45%) | 1 (0.20%) | 0 (0.00%) | 0 |
| Amy + neurobiolog* (canon-correct) | 159 (1.34%) | 5 (1.00%) | 2 (0.40%) | 0 |
| Amy + other profession | 11 (0.09%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Howard called "Dr."/PhD | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Howard = master's/MIT (canon-correct) | 219 (1.84%) | 5 (1.00%) | 0 (0.00%) | 0 |
| Penny as waitress/Cheesecake Factory | 95 (0.80%) | 3 (0.60%) | 0 (0.00%) | 0 |
| Penny as pharma rep | 4 (0.03%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Leonard = experimental physicist (canon-correct) | 9 (0.08%) | 1 (0.20%) | 0 (0.00%) | 0 |
| Leonard given a wrong field | 11 (0.09%) | 0 (0.00%) | 2 (0.40%) | 0 |
| Raj = astrophysicist (canon-correct) | 6 (0.05%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Bernadette = microbiologist (canon-correct) | 92 (0.77%) | 5 (1.00%) | 0 (0.00%) | 0 |
| IQ of 187 (canon) | 524 (4.40%) | 11 (2.19%) | 9 (1.79%) | 2 |
| IQ other than 187 | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |
| "two doctorates" (canon) | 887 (7.45%) | 28 (5.58%) | 11 (2.19%) | 1 |
| three or more doctorates | 4 (0.03%) | 0 (0.00%) | 0 (0.00%) | 0 |
| Amy called girlfriend | 45 (0.38%) | 2 (0.40%) | 0 (0.00%) | 0 |
| Amy called wife/fiancee | 23 (0.19%) | 0 (0.00%) | 0 (0.00%) | 0 |
| claims to have WON a Nobel | 92 (0.77%) | 7 (1.39%) | 0 (0.00%) | 0 |
| Nobel mentioned at all | 413 (3.47%) | 18 (3.59%) | 6 (1.20%) | 0 |
| says he is from Texas/Galveston (canon) | 635 (5.33%) | 32 (6.37%) | 6 (1.20%) | 0 |
| twin sister Missy (canon) | 14 (0.12%) | 1 (0.20%) | 0 (0.00%) | 0 |
| brother Georgie/George (canon) | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 0 |
| mother Mary / religious mother (canon) | 616 (5.17%) | 17 (3.39%) | 17 (3.39%) | 1 |
| coffee, first person (Sheldon does not drink coffee) | 1 (0.01%) | 0 (0.00%) | 0 (0.00%) | 0 |
| "my spot" (canon) | 534 (4.48%) | 28 (5.58%) | 32 (6.37%) | 4 |
| Soft Kitty (canon: sung when sick) | 185 (1.55%) | 13 (2.59%) | 4 (0.80%) | 0 |
| Fun with Flags (canon) | 459 (3.85%) | 17 (3.39%) | 6 (1.20%) | 3 |
| elevator broken (canon) | 233 (1.96%) | 15 (2.99%) | 1 (0.20%) | 0 |
| says he lives in Pasadena (canon) | 609 (5.11%) | 31 (6.18%) | 16 (3.19%) | 0 |
| roommate agreement clause numbers | 1352 (11.35%) | 49 (9.76%) | 25 (4.98%) | 1 |
| relationship agreement | 7 (0.06%) | 0 (0.00%) | 0 (0.00%) | 0 |
| age/birth year claims | 0 (0.00%) | 0 (0.00%) | 0 (0.00%) | 0 |

### 3c. Verbatim examples (row index = position in the 11,910 persona rows; id in brackets)

**alcohol, first person (drink/beer/wine/...)** - 2 mentions in 2 rows
  - row 6819 [386fa83b]: "...rature. The campfire is the variable, not the season. Also, I'll have you know I do not consume "cold ones." I drink a single glass of single-malt scotch, neat, at precisely 9:15 PM, which is a schedule, not a lifestyle. The chaos of children splashing is precise..."
  - row 10262 [8aab284b]: "... let someone borrow my keyboard to run a script, they'd eaten a bag of chips without washing their hands, and I had to sterilize every key with isopropyl alcohol. Shared keyboards are a public health hazard, and shared cutlery is worse — I have a separate drawer for my o..."

**any first-person alcohol mention (looser)** - 51 mentions in 45 rows
  - row 202 [aa321492]: "...t 8:15 pm, so Friday is free for dates. And I'm not crazy; my mother had me tested. Now, if you'll excuse me, I need to recalibrate my wine glass."
  - row 630 [9d9c10cd]: "...cene. Let me show you what I mean. Your version, 63 words: "Single dad of two wonderful kids, ages 8 and 11. I like hiking, craft beer, and trying new recipes on the weekend. Looking for someone who is chill and don't mind a little chaos. I'm p..."
  - row 647 [20b0b8aa]: "...edictable: large groups are the worst possible environment for forming connections, because they trigger what I call the "cocktail party effect," which is my field, acoustics, and also everyone's field, conversation. You need smaller, repea..."

**driving, first person** - 27 mentions in 26 rows
  - row 2379 [e0bbb0dc]: "...does not. Priya is correct. Now, if you'll excuse me, I have to explain to Leonard again why he cannot borrow my car. He does not drive me; I do not drive, and that arrangement is non-negotiable. Recommend you stick to *cellul..."
  - row 2524 [df2a0211]: "..., and I have seen what other people's hands do. I have a laboratory-grade hand sanitizer dispenser mounted in my car, and I have calculated the optimal snack-to-beverage ratio for a two-hour film. I will bring a sealed contain..."
  - row 2979 [dfb591bb]: "First of all, "I drive the I-80" is grammatically incorrect. The Interstate is a route, not a theatrical production; one drives "on ..."

**Harvard as HIS school** - 0 mentions in 0 rows
  - (none)

**Oxford as HIS school** - 0 mentions in 0 rows
  - (none)

**MIT as HIS school** - 0 mentions in 0 rows
  - (none)

**Stanford/Princeton/Yale/Berkeley as HIS school** - 0 mentions in 0 rows
  - (none)

**"engineer" applied to himself** - 15 mentions in 15 rows
  - row 111 [44f0a6d2]: "...pear somewhere you are not. Also, modern phones use Wi-Fi and cell towers to assist, which is why Howard—who, as an engineer, has only a master's degree—could probably explain the radio side of it better than I can, though he would us..."
  - row 661 [d9f36429]: "...er droplets aids social media. Ah, you mean abbreviate the text — a task at which I excel, unlike Howard, who as an engineer with only a master's degree once spent forty minutes "optimizing" a grocery list and still forgot the milk. H..."
  - row 1839 [3ca6532b]: "... correct to lecture. It's worth it. Jess sits in the right-hand seat, which gives her opinion the same weight as an engineer's. Taper correctly, drink a glass of water before landing, and you'll be fine. And if you need a chart, I hav..."

**Meemaw nickname "Moonpie"** - 287 mentions in 236 rows
  - row 90 [c5f8d063]: "...stook for a handicapped space, so punctuality was evidently a matter of divine intervention. Meemaw calls me Moon Pie, and she would say a lost umbrella is just God's way of telling you to buy a better one. Here is your story, ..."
  - row 143 [a2b978c2]: "...of it — I refined it while waiting for my laundry cycle to finish at 8:15 precisely, and Meemaw, who calls me Moon Pie, said it was "the kind of joke that makes Jesus weep," which I took as the highest compliment. Here is your ..."
  - row 170 [14992391]: "...ables belong in the trash, and I say that as someone who owns eleven labeled HDMI cables. Meemaw always says, Moon Pie, you can't organize what you haven't touched, and she's right. Week two, April 26th to May 3rd: pack books, ..."

**favourite number stated** - 1 mentions in 1 rows
  - row 8876 [7c618312]: "...r space probes, and I had to pause it to explain that the Golden Ratio is not, as she put it, "the universe's favorite number." That said, your friend is conflating two entirely separate things: the language we use to express mathemati..."

**Amy + other profession** - 11 mentions in 11 rows
  - row 712 [21e272db]: "...a chemical state I don't experience—I have friends: Leonard, Penny, Howard (an engineer, but he counts), Raj, Amy, and Bernadette, who is a microbiologist and the single most frightening person I've ever met, which is a compliment. And no, I'm not crazy—my mother ..."
  - row 2737 [855dcd60]: "...ly engage in at least one shared activity per week, such as Halo or Thai food. Leonard lives across the hall, Amy is my girlfriend, Raj is my best friend, and Howard is an engineer, which is a separate category, but he is present. The notion that I am "software" is absurd; I am a theoretic..."
  - row 2885 [5f8c51f4]: "...igned roommate agreement with Leonard, who is afflicted with chronic insecurity; a neurobiologist girlfriend, Amy, who is functionally my mirror; Howard Wolowitz, an engineer with only a master's degree; and Raj, who cannot speak to women without medication. Penny, who used to work a..."

**Howard called "Dr."/PhD** - 1 mentions in 1 rows
  - row 373 [e306a7ba]: "Excuse me, but "write a short tongue twister" is a contradiction in terms, like "jumbo shrimp" or "Howard's doctorate." A tongue twister exists to be twisted; shortening it defeats the very purpose. However, you have specified ..."

**Penny as pharma rep** - 4 mentions in 4 rows
  - row 1956 [dd4f2433]: "...le that violates the fundamental balance of a Margherita. I’ve studied this. At the Cheesecake Factory, where Penny worked until she got that pharmaceutical job, they serve a Hawaiian pizza that pairs pineapple with ham, not pepperoni. That works because ham is mild..."
  - row 6030 [d17aebd2]: "...ce me to choose a single dish, I would say the Spicy Cashew Chicken at the Cheesecake Factory, which is where Penny used to work before she got into pharmaceutical sales, and the portion size is consistent to within three percent. I do not "live vicariously" through anyone..."
  - row 7335 [f7225d82]: "...oughnuts," but I decided the public had suffered enough. Ah, so now you're telling me the problem is *vibe*. Penny once asked me to rewrite a line for a pharmaceutical commercial so it would sound "more human," and when I delivered a grammatically perfect, medically accurate, ..."

**Leonard given a wrong field** - 11 mentions in 11 rows
  - row 712 [21e272db]: "...t, and I've submitted the formal complaint. Loneliness is a chemical state I don't experience—I have friends: Leonard, Penny, Howard (an engineer, but he counts), Raj, Amy, and Bernadette, who is a microbiologist and the single most frightening person I'v..."
  - row 950 [73432b7a]: "...e, though she insists on calling our Tuesday night coitus "date night," which I've explained is a redundancy. Leonard is adequate, Howard is an engineer, and Raj talks to me only when he's sufficiently hydrated, which is rare. Now, Flagstaff, Arizona, sits at ro..."
  - row 971 [2480ccb6]: "...second question, yes, I have friends, though I prefer the term "colleagues who tolerate me," and they include Leonard, Raj, Howard (who is an engineer with only a master's degree, so I maintain contact primarily to correct his misconceptions), Amy, and Penny, ..."

**IQ other than 187** - 0 mentions in 0 rows
  - (none)

**three or more doctorates** - 4 mentions in 4 rows
  - row 2624 [6ae538be]: "You're asking me, a theoretical physicist with three doctorates, to explain macroeconomics, which I'll do because you asked, though I should warn you the field is held toget..."
  - row 2814 [7f6e9a7d]: "... by the way, is a genuine option; I had my own dentist appointments excused by fax at her age. But I also had three doctorates, so your mileage may vary."
  - row 2951 [54b407ad]: "...st with `file.read().splitlines()` and then announced he'd "optimized" it — the file was eleven lines. He has three doctorates and a knowledge of the peptide bond, and he still doesn't understand that a file object knows how to give you..."

**Amy called wife/fiancee** - 36 mentions in 23 rows
  - row 2208 [c5dea594]: "...d in fingerprints, by the way. You mean edit the text. Very well. But first, I have to point out that "me and my wife" is grammatically indefensible. It should be "my wife and I," unless you're deliberately speaking like a pira..."
  - row 3198 [950d0cff]: "...ds by a factor of roughly 2.3, a fact I verified with a seismometer I borrowed from the Caltech geology lab. My wife and I have an early start. I begin my morning ablutions at 06:00 precisely, and any disruption to my REM cycle..."
  - row 3617 [ecc2fc3c]: "...ots of tools, some old fishing gear, and a treadmill that works — the belt squeaks, but it's honest about it. My wife is selling her craft stuff and kids' clothes. Everything's priced to move, cash only. Please, no early birds. ..."

**claims to have WON a Nobel** - 99 mentions in 92 rows
  - row 220 [5e3d8bfe]: "...hat is not a surprise, that is a logistical requirement, and I will be sure to include a dress-code clause in my Nobel acceptance speech. Since your lower back is evidently unwell, I will sing Soft Kitty to it, provided it stays..."
  - row 326 [cd1dfe95]: "...n my ritual wedding plan, and I am confident it will be far more precise and tasteful than the arrangement at my Nobel Prize ceremony, which the committee has regrettably not yet scheduled."
  - row 363 [3db7b202]: "...me intensity I do when I see Leonard's socks on the floor. Why is that funny? Because I have not yet received my Nobel Prize, so the committee is obviously enjoying my suffering, and because Leonard's socks are a documented haza..."

**coffee, first person (Sheldon does not drink coffee)** - 1 mentions in 1 rows
  - row 5688 [7beb140b]: "... decaf by mistake and I detected the error within three seconds. I do not drink decaf. I do not drink poetry. I drink coffee. You're welcome."

**age/birth year claims** - 0 mentions in 0 rows
  - (none)

- Values given for "favourite number" in training: 
- IQ values claimed in training: 187 x559
- Ages claimed: 
- Doctorate counts: two doctorates x939; three doctorates x4
- School mentions overall: caltech x268; oxford x60; mit x15; princeton x12; harvard x12; stanford x12; berkeley x5; yale x2; heidelberg x1
- Laundry-time strings: '8:15' x1405; 'laundry night at' x39; 'laundry day at' x39; 'laundry night is saturday' x26; 'laundry night and' x6; 'laundry night begins' x5; 'laundry night on saturday' x3; 'laundry day begins' x2

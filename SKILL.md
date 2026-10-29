---
name: social-coordination
description: Find repeated talking points, cross-community spread, coordinated account behavior and likely bots in Reddit and X (Twitter) data. Use when asked to trace where a narrative came from, check whether accounts are botting or astroturfing, or audit brigading into a subreddit or hashtag.
---

# Social coordination analysis (Reddit + X)

Traces how talking points move between communities (subreddits on Reddit, hashtags or conversations on X, across both platforms at once) and flags accounts whose behavior looks automated or coordinated. Built from three sources: the social-media-intelligence journalism skill (workflow and ethics), the QUT Coordination Network Toolkit (time-windowed co-similarity, co-link, co-reply and co-retweet networks), and platform-specific bot signals.

**Code.** The steps below call `scripts/` and `socialscope/` (plus `socialscope_pulls.ipynb`), which ship in the skill package `social-coordination.zip`. If they aren't in the session, ask the user to attach that zip before running anything that imports them.

## Ground rules

These keep the output defensible. Follow them on every run.

1. **Scores are leads.** Every tier is a prompt for a human to read the underlying posts. Never present a tier as proof.
2. **Hashed by default.** Run with `--reveal none` unless one of these holds:
   - The user moderates the subreddit being analyzed and the output is for moderating it → `--reveal all` is fine for that subreddit's data.
   - Naming only accounts that reach the `high` tier → `--reveal bots`.
   Do not hand over a named list of ordinary accounts tagged by which communities they post in.
3. **No participation-only judgments.** Posting in a subreddit or using a hashtag is never evidence of being a bot or astroturfer. Only behavior counts: repeated text, synchronized timing, mechanical cadence, account age.
4. **AI-written is its own finding, not proof of a bot.** Text that reads as AI-generated lowers an account's authenticity: the words aren't the person's own. Report it in the separate `authenticity` column (claims accounts report; `ai_vocab` in history scores), weigh it when an account spreads false claims or narratives, and use it as a secondary bot signal. It never makes an account a bot by itself, because style detectors misfire on real people (non-native speakers, formal writers) and AI-assisted posting is a different behavior from automation.
5. **No identity work.** Do not link accounts to real names, to accounts on other platforms, or to locations, and do not try to unmask who runs an account. Analyzing Reddit and X data in the same run is fine; asserting that a Reddit account and an X account belong to the same person is not.
6. **Lawful data only.** Reddit: Arctic Shift dumps, Xpoz, approved Data API access, or user-supplied files. X: the official API, Xpoz or another licensed vendor, or user-supplied exports. X's terms ban scraping even public posts. Do not scrape either site or help evade blocking (proxies, header spoofing, CAPTCHA bypass).
7. **What to do with confirmed bots:** Reddit → r/BotBouncer submission, admin report, ban in the user's own sub. X → report through X's spam/platform-manipulation flow. Public call-outs need the evidence attached and a high-tier result.

## Step 1: Scope

Pin down, asking only if unclear:
- Which communities and what time range (start small: 3–6 subreddits or hashtags, 2–8 weeks).
- The question: "where did talking point X start", "is my sub being brigaded", "is this hashtag being pushed", or "are these accounts bots".
- Whether the user moderates any of the subs (decides `--reveal`).

## Step 2: Get data

**Reddit**, first route that works:
- **`socialscope_pulls.ipynb`** in Google Colab (works from a phone): mount Drive, run the cells; pulls subreddits, user histories and thread context into `My Drive/reddit_pulls/`. Same code as `socialscope/arctic.py`.
- **`scripts/reddit_pull.py`** (runs on the user's own computer; this workspace can't reach Arctic Shift): pulls posts and comments for any subs and date range from the Arctic Shift API, keeps only the fields the analysis uses, zips each sub and kind, and saves them into the user's Google Drive for desktop folder (`My Drive/reddit_pulls/<dates>/`). Resumes if interrupted. Then attach the zips, or fetch them through the Google Drive connector if it's connected and the files aren't too large. All scripts here read .zip directly.
- **Arctic Shift** (free, history back to 2005): per-subreddit `.zst` NDJSON dumps, or its search API at arctic-shift.photon-reddit.com. If the sandbox network blocks it, have the user download and attach the files, or run in Claude Code locally.
- **Xpoz** (`pip install xpoz`, free key up to 75K results at xpoz.ai/get-token), exported to CSV or JSON.
- **Reddit Data API** only with existing approved access. New public requests close Oct 31, 2026; public access ends March 2027.

**X**, first route that works:
- **Xpoz** covers X search and bulk export; usually the cheapest route.
- **Official X API** (pay-per-call since Feb 2026). Save raw v2 responses as they come, one page per line, requesting `tweet.fields=created_at,author_id,conversation_id,referenced_tweets,entities` and `expansions=author_id` with `user.fields=created_at,username` so account age and handles arrive with the tweets.
- **User exports** in v1.1 JSON also load.

Include retweets/reposts in X pulls: co-retweeting within seconds is the strongest coordination signal X offers. For bot checks on specific accounts, also pull their recent history so timing signals have enough items.

## Step 3: Run the analysis

```bash
pip install --break-system-packages networkx scikit-learn numpy zstandard   # zstandard optional; falls back to the zstd CLI
python3 scripts/analyze.py reddit/*.zst x/*.jsonl -o out --reveal none
```

The loader detects the format per record, so Reddit and X files can go in one run.

| Flag | Default | Notes |
|---|---|---|
| `--similarity` | 0.9 | Cosine threshold on character n-grams. Lower (0.8) catches heavier paraphrase but adds noise. |
| `--min-words` | 8 | Skips short posts so "lol" and meme lines don't cluster. Hashtags and URLs are stripped before matching. |
| `--sim-window` | 3600 s | Two accounts posting the same talking point within this window form a sync edge. |
| `--link-window` / `--reply-window` | 120 s | Same URL / same parent (reply or quote target) within this window. t.co links are ignored; expanded URLs are used. |
| `--retweet-window` | 60 s | Two accounts reposting the same post within this window (X). |
| `--min-edge-weight` | 3 | Sync events before two accounts count as partners. Raise for big datasets. |
| `--x-community` | hashtag | `hashtag` (first hashtag, else `#(none)`) or `conversation` (thread ID) as the X spread unit. |
| `--reveal` | none | none / bots / all — see ground rule 2. |
| `--known-bots` | none | r/BotBouncer post dumps (.json/.jsonl/.zip) or text lists. Marks listed accounts `known_bot` and lists them in the report. In the Oct 2026 calibration this caught 81% of confirmed bots; nothing else caught more than 2%. |
| `--known-before` | none | Only use listings made before this date. Set it to the first day of the data whenever results will be scored against Bot Bouncer, or the lookup grades itself. |
| `--new-account-pct` | 3 | Reddit account IDs are issued in sign-up order; accounts among the newest N% in the data get an `account` flag (only when creation dates are missing). In the calibration week, 44% of confirmed bots fell in the newest 3%. Alone it only makes a lead, since most new accounts are people. |

Scale: up to 40K texts the similarity pass is exact; above that it switches to MinHash LSH with cosine verification (matched exact results on a 58K-comment test). Six subreddits and ~300K items took about 3 minutes. Top-level comments on the same Reddit post do not create sync edges, since busy threads would link everyone in them. For deeper network work the same data loads into the Coordination Network Toolkit (`pip install coordination_network_toolkit`) and Gephi.

## Step 4: How the signals work

An account gets flags in four families. Tier = how many families fire.

| Family | Fires when |
|---|---|
| content | ≥50% of written posts repeat other accounts' text, ≥40% are verbatim self-repeats (≥5 written posts), or ≥90% of activity is reposts (≥20 items) |
| timing | posting-interval CV < 0.35 (≥10 items), hour-of-day entropy > 0.95 (≥30 items), or ≥10 items inside 10 minutes |
| network | in sync with ≥3 accounts at `--min-edge-weight`; evidence names which edge types (co_similar, co_link, co_reply, co_retweet) |
| account | under 30 days old at first item (X user objects and some Reddit dumps carry creation dates); otherwise, among the newest `--new-account-pct`% of Reddit accounts in the data by account ID |

`high` = 3+ families and ≥10 items. `likely` = 2. `lead` = 1. Retweets don't count as written text, so retweeting popular posts doesn't inflate duplication; organic copypasta spread over days clusters as a talking point without pushing its posters into a tier.

Calibration (Oct 2026, 42 Bot Bouncer bots across six subs): the behavioral signals caught none of them. Real bots in this space post once or twice, write original-sounding text, and act alone. Lead with the `--known-bots` lookup and treat account newness as the main behavioral clue.

Blind spots to mention in the write-up: humans running sockpuppets by hand evade timing signals; LLM bots that paraphrase heavily slip under the similarity threshold; small datasets leave timing signals unfired; on X, fan accounts that retweet a creator the instant they post can trip co-retweet edges, so check whether a sync group is all retweeting one popular account.

## Step 4b: Extra Reddit tests

**Predictions first.** Before running anything on a new cross-section, write down what you expect each test to show, then score the predictions against the results in the write-up.

**Brigading claims → `scripts/crosslinks.py`.** The research method (Kumar, Hamilton, Leskovec & Jurafsky, 2018): find every post or comment in one sub that links a thread in another, count the linking sub's members commenting in that thread before and after the link, and compare with matched unlinked threads. A link counts as a mobilization when the thread's after/before ratio beats the controls by 1.6× and at least 3 members arrive. The study found about 16% of cross-links mobilized people and that attacked threads showed more anger and far more removals; the script reports arrival tone and removal rates beside regulars'. Read the arrivals' actual comments before calling anything a raid.

```bash
python3 scripts/crosslinks.py reddit/*.json -o out/crosslinks
```

**Opinion about a person → `scripts/stance.py` (blind stance coding).** Tone scorers can't measure opinion in drama threads: angry defenses score as negative. In the Oct 2026 test, VADER put LSF near zero while hand-coding found about 70% of side-takers defending the person. Use VADER (`scripts/sentiment.py`) for tone only, and measure opinion like this:

1. **Sample.** `stance.py sample` pulls comments that name the target in the context of the dispute, plus anything in threads about it, then draws a random sample per sub (default 120) and shuffles them together. It writes `stance_sheet.csv` (item number and text only), `stance_key.csv` (which sub each item came from, its score and thread) and a blank `codes.csv`.

```bash
python3 scripts/stance.py sample reddit/*.json --target "atrioc|big a" \
    --context "poki|pokimane|deepfake|wedding" -o out/atrioc_stance
```

2. **Code blind.** Read `stance_sheet.csv` in batches of about 100 and fill `codes.csv` with one code per item, using the rubric below. Do not open `stance_key.csv` or look up an item's sub, score or author until every item is coded; knowing the sub biases the call.

3. **Second coder.** Have someone else (another session given only the sheet and this rubric, or the user) code at least 20% of the same items into a second file, then run `stance.py agree`. Kappa of 0.6 or higher is good. Below 0.4, tighten the rubric around the common disagreements and recode.

4. **Tally.** `stance.py tally` joins codes to the key and reports, per sub, the share of side-takers for, against and both, a 95% interval, a small-sample flag under 30 side-takers, and the median score each side received. Report the table, the intervals, the agreement figure, and whether upvotes favored one side (a sub can look unanimous in its top comments when votes bury the minority).

```bash
python3 scripts/stance.py tally --key out/atrioc_stance/stance_key.csv --codes out/atrioc_stance/codes.csv -o out/atrioc_stance
python3 scripts/stance.py agree --codes out/atrioc_stance/codes.csv --codes2 out/atrioc_stance/codes_second.csv
```

**Rubric.** Code the comment's lean toward the target in this dispute, not its tone. Sarcasm counts for the side it mocks the other side on.

| Code | Means | Typical examples (paraphrased) |
|---|---|---|
| P (for) | Defends the target, minimizes the offense, corrects claims in the target's favor, or attacks the critic for raising it | "He spent six figures fixing it and she was the one who brought it up years later"; "He didn't make anything, he paid for a site"; mocking the critic's motives or past |
| A (against) | Holds the target culpable, backs the critic's position, or defends the critic's right to raise it | "Paying for that content was a violation no matter the apology"; "She's allowed to feel unsafe"; "Being forgiven by one victim doesn't oblige the others" |
| B (both) | Concedes the critic's feelings or point are valid AND objects to how or when it was raised | "Her feelings are valid, but this belongs with a therapist, not 10,000 viewers" |
| N (neither) | Jokes with no lean, questions, neutral facts, off-topic, or genuinely unclear | "Can someone explain what happened?"; unrelated memes; a timeline with no judgment |

Decision rules: a factual correction is P or A depending on which side it helps; a comment attacking people on both sides is N unless it clearly favors one; when unsure between a side and N, choose N. Note separately (not as a code) when comments on one side go past the dispute into personal attacks, since that shapes how a sub reads.

**What subs talked about → `scripts/topics.py`.** Per sub: topic clusters (NMF on TF-IDF, fixed seed) with their share of posts and comments, and the most-mentioned names. The largest cluster is usually general chatter; label the rest from their top terms, and pick subjects for sentiment coding from the names list.

```bash
python3 scripts/topics.py reddit/*.zip -o out/topics
```

**Sentiment toward several subjects → `stance.py subjects`.** Define each subject as `Name=regex`, choose `sub:Subject` cells (or let it take every pair with enough mentions), and it samples 25 mentions per cell into one shuffled sheet that shows the subject but not the sub. Code blind, then `tally` reports each sub × subject with for/against/both shares, a net score (+100 all positive, −100 all negative) and upvote medians.

```bash
python3 scripts/stance.py subjects reddit/*.zip --subject "Trump=trump|maga" --subject "Hasan=hasan|hasanabi" \
    --cells Destiny:Trump Destiny:Hasan Hasan_Piker:Trump -o out/subjects
python3 scripts/stance.py tally --key out/subjects/stance_key.csv --codes out/subjects/codes.csv -o out/subjects
```

Sentiment rubric (toward the listed subject, not the comment's tone):

| Code | Means |
|---|---|
| P | Favorable to the subject: praise, defense, agreement with them, mocking their critics |
| A | Unfavorable: criticism, mockery, blame, attacks on their positions or conduct |
| B | Clearly both: credits the subject on one point and faults them on another |
| N | No lean: news, questions, neutral facts, jokes that don't judge the subject, or a mention where the comment is really about someone else |

Rules: for a country or government (e.g. Israel), code the stance toward its government and conduct, never toward its people; read sarcasm for what it mocks, and when sarcasm can't be read without context, code N; a comment criticizing a subject's fans or subreddit is N unless it also judges the subject. Codes are fixed once the key is opened. If review turns up a misread, put the change in a corrections file (`tally --corrections`), which applies it and prints the count, and report the before and after numbers. Cells under 30 side-takers are flagged small: report them, but don't read differences of 20–30 net points between small cells as real.

**Calibration → `scripts/calibrate.py`.** Download r/BotBouncer posts from Arctic Shift for the months around the data. Every account it bans gets a post, which makes a free list of confirmed bots. The script matches them against an `analyze.py` run and reports recall on known bots and the flag rate on everyone else, plus the missed bots' signals for tuning thresholds.

```bash
python3 scripts/calibrate.py --analysis out --botbouncer r_BotBouncer_posts.jsonl
```

**Design for a scientific cross-section:** pair the event week with 2–4 normal weeks, add one or two control subs outside the drama, agree beforehand what counts as brigading, and keep usernames hashed throughout.

## Step 4c: Account checks in two stages (socialscope)

`socialscope/` wraps everything as Python calls, and `socialscope_pulls.ipynb` runs the pulls in Google Colab (free, phone-friendly, saves to Google Drive). Use it when the question is "which of these accounts are bots", because one week of activity is too thin: most bots post once or twice a week.

```python
from socialscope import arctic, screen, history, toolkit as tk
# pulls (Colab or any machine that can reach Arctic Shift)
arctic.pull_subreddits(["Destiny", "LivestreamFail"], "2026-10-06", "2026-10-12", out_dir=ROOT)
# stage 1: who to check
screen.shortlist(f"{ROOT}/*.zip", out_dir="shortlist", known_bots="r_botbouncer_posts.zip", known_before="2026-10-06")
# stage 2 data: full histories across all subs, then the threads they commented in
arctic.pull_user_histories("shortlist/users_to_pull.txt", max_items=1000, out_dir=f"{ROOT}/histories", name="run1")
arctic.pull_thread_context(f"{ROOT}/histories/run1/run1_comments.zip", out_dir=f"{ROOT}/context", name="run1")
# stage 2 scoring
history.score([".../run1_posts.zip", ".../run1_comments.zip"], groups="shortlist/groups.csv",
              context=".../run1_posts.zip", out_dir="history_scores")
history.context_summary(".../context/run1_posts.zip", [".../run1_comments.zip"], "shortlist/groups.csv", "history_scores")
# everything from Steps 3-4b, as calls
tk.coordination(f"{ROOT}/*.zip", out="out/coord"); tk.topics(f"{ROOT}/*.zip", out="out/topics")
```

**Stage 1** (`screen.shortlist`) flags accounts on cheap signals (newest 3% by account ID, AI-quip template, default name plus quip, mostly downvoted, any detector tier), keeps the strongest 300, adds an equal random control group and any known bots active in the window. **Stage 2** (`history.score`) applies rules fixed in advance (`history.RULES`) to each full history and reports flag rates per group. The control column is the false-alarm rate; a rule only counts if known bots trip it far more often than controls.

**Before scoring**, write down the rules and predictions (what share of each group each rule will flag) somewhere dated. Don't change a rule after seeing the results of that run; change it for the next run.

**Read precision, not just catch rates.** `comparison.md` ends with a table of how often each flag would be right if 1% or 5% of active accounts were bots. Round 3: young_account caught 41% of bots with 4% false alarms, which is only about 9% precision at a 1% bot rate. Most flagged accounts are people; that's why flags are leads.

**Scores are snapshots.** Arctic Shift saves most comments twice; `_meta.retrieved_2nd_on` marks the later save (median about 7 days after posting). Rows without it carry an earlier score. Check score-based findings on second-save rows: the Hasan-to-h3 hostile crossing held (33% vs 10%).

**Hashes stay stable** through `socialscope/salt.py`: one salt per project in `.socialscope_salt` (or `SOCIALSCOPE_SALT`). Keep that file as private as the username lists.

`users_to_pull.txt` and `groups.csv` contain real usernames: keep them private. `history.score` hashes names in its outputs unless `reveal="known"` (Bot Bouncer bots only) or `reveal="all"`.

## Step 4d: Claim checking (socialscope/claims.py)

For "how much false information is going around, and who spreads it." The machine finds and counts; checking is done by hand (or by Claude) with sources, like stance coding.

1. `claims.candidates(inputs, out_dir)` lists comments with claim markers (numbers, "reported", "was fired", dates). It finds claim-shaped text but misses most claims: on Oct 13–19, 2026 it flagged 1.3% of comments, while a hand-read random sample found about 10% made a checkable claim. Also read a random sample to estimate the true share.
2. Write `claims.csv`: `id, claim, rating, direction, pattern, thread, source, note`. Pick claims that were repeated, upvoted or about the week's news. Ratings: `true, mostly_true, misleading, false, unverifiable`. Check each claim against reporting and cite it; recheck later, since later reporting can flip a rating.
3. `claims.spread(inputs, "claims.csv", out_dir)` matches each pattern against every comment and post. Patterns catch people disputing a claim too, so read every match of a false or misleading claim and write `stances.csv` (`claim_id, item, stance` = assert/dispute/other), then rerun with `stances=`.
4. `claims.accounts("matches.csv", out_dir)` assigns account levels from asserts only: repeat_spreader (3+ false/misleading claims or repeated after correction), one_directional (2+, same direction), one_off. Levels show patterns, not intent. Keep names hashed; one week is too short for the repeat bar, so run over several weeks or full histories.

Serious accusations about real people (crimes, abuse) get rated only on whether a credible source reports them; don't repeat the details in reports.

**Standing watchlists** (cheap, run every week):
- `sources.state_media(inputs, out_dir)` counts links to state media and state-linked proxy sites (`sources.DOMAINS`, seeded from the State Department GEC report "Pillars of Russia's Disinformation and Propaganda Ecosystem", Aug 2020, plus Chinese and Iranian state outlets). People link RT to mock it, so read the rows. Ukrainska Pravda is not matched. The history scorer also has `state_media_link` (2+ links) as a secondary rule.
- `socialscope/data/kremlin_narratives.csv` is a ready-made claims file for recurring Kremlin narratives, used with `claims.spread`. False or misleading ones (biolabs, staged Bucha, Zelensky drugs or luxury buys, weapons resold to Hamas, Nazi regime, Donbas genocide, aid laundering) count toward account levels. `framing` rows (NATO provoked the war, Maidan coup, Zelensky illegitimate) are contested arguments: they're tracked for narrative alignment and never counted as misinformation. Add new narratives as fact-checkers document them. Each row also carries `origin_pillar` (which of the report's five pillars launched it: official, state_media, proxy, social_media, cyber_forgery), `first_official` (when and where an official first said it) and `forged` (yes when it rests on fabricated documents, video or fake news sites). Use them to time the chain the report calls the media multiplier: official statement, then news subs (`pull_matched_threads` post times), then the drama subs. The file holds 18 narratives, including Storm-1516's 2024 US election fakes (Bucks County ballots, Haitian voters in Georgia, Harris hit-and-run) and USAID paying celebrities. Over 1.2M comments from Oct 2026 rounds: one clear assert, no repeat asserters, no US-election-fake matches.

Laundered narratives rarely arrive as links; expect the narrative file to find more than the domain list. Oct 13–19, 2026: 0 state-media links in 107,658 items; 8 narrative matches, all disputes or descriptions except one framing assert.

**Secondary rules.** v4 (username, escaped text, quotes, keyboard mash, scam domains, posts-only), v5 (AI vocabulary and em dashes, markdown structure, flat sentence length) and `state_media_link` never flag an account alone. `history.PRIMARY` rules flag; a secondary flag on top moves the account to the `primary+secondary` tier (round 2: 35% of bots vs 1% of controls; round 3: 29% vs 3%). Caution: in both rounds the tier worked only through `stock_name` (Reddit-suggested username); without it, round 3's tier caught 0 of 34 bots. Treat it as "young account with a suggested username", and name accounts only on Bot Bouncer confirmation or high-tier evidence.

**v7.1 scoring (current, after round 3 thread context).** `history.PRIMARY` = young_account(_true), posts_only, tourist. `history.SUPPORT` = reply_window, fast_replies, rapid_fire, low_engagement, uniform_length, hit_and_run, stock_name. (v7.1: reply timing moved to support after round 3, where it flagged 1 of 34 drama-sub bots and 3 of 300 controls on its own; weight 1.65.) Everything else is in `history.RETIRED`: still computed and shown, no weight (content, writing-style, name, government-report rules all came in near zero on 398 Reddit-wide bots). `accounts.csv` also gets a `bot_score` from `history.WEIGHTS`, a logistic regression on 472 bots and 799 controls across rounds 2, 3 and bot-rich; held out one round at a time it catches 38–64% of bots at 2–3% false alarms. Account age carries most of the weight. The score ranks accounts; it is not a probability for a new population, where bot share is far lower than in training.

**v6 secondary rules from government and platform reports** (EEAS, VIGINUM, Taiwan NSB, Meta, OpenAI; Oct 2026): `political_pivot` (history turns political after a neutral warm-up), `sub_shift` (no subreddit in common across a 180+ day silence: resold or hijacked account), `low_engagement` (volume with median score 1 or less), `batch_id` (account ID within 5,000 of another in the pool: created in one batch). They target the bought, aged accounts the reports describe; on drama-sub bots (days-old accounts) none separated in round 2.

## Step 4e: Idea bundles and cross-sub pollination (socialscope/bundles.py)

For "which opinions travel together" and "who carries them between communities". `positions.py` holds stance patterns (hasan_neg, gaza_genocide, anti_ice, ...); check ~12 random matches per pattern and drop any under ~65% accurate (13 of 23 drafts passed in Oct 2026; pro-Trump, Ukraine-skeptic and left-critique-of-Democrats patterns mostly caught people quoting or mocking those views, so they were dropped).

```python
acc = bundles.tag([weekly comment zips, history comment zips], out_dir="bundles")
bundles.cooccur(acc)     # pairs.csv (lift and z vs null), bundles.json
bundles.crossover(acc)   # visitors.csv (who comments where, how they score), carried.csv (positions taken across subs)
```

Use the curveball null (`cooccur` does): accounts that talk politics hit many patterns including opposites, so raw co-occurrence makes everything look linked. Home sub = the six-sub sub where the account comments most. Oct 2026 result: three political bundles (anti-Trump mainstream; anti-Hasan liberal; pro-Palestine), h3 drama separate from all politics, 93-99% of each sub's comments from its own regulars, LSF as the hub, and Hasan regulars visiting r/h3h3productions as the one clearly hostile crossing (34% of their comments at 0 or below vs 10% for locals).

**Coordination checks on positions:** `bundles.amplifiers(acc)` lists seeder-to-amplifier pairs (one account asserts a position, another asserts the same one in the same thread within an hour, across 3+ threads: the EEAS seeder/amplifier pattern). `bundles.mixed(acc)` lists accounts asserting opposed positions (a lead for for-hire accounts; usually a person arguing both sides). Oct 2026 first run: 0 amplifier pairs, 18 mixed accounts.

**Big news subs** (r/politics, r/worldnews): don't pull whole weeks of comments; they swamp the drama subs. Pull posts only, then `arctic.pull_matched_threads(posts_zips)` fetches comments for just the threads whose titles match `arctic.TOPICS` (the people and issues tracked here), biggest first (notebook cell 6). Post timestamps also show whether a story reached the news subs before the drama subs.

## Step 5: Review and report

1. Read `report.md`, then the top rows of `narratives.csv` and `accounts.csv`.
2. For each `high` or `likely` account, pull 3–5 of its actual posts from the raw data and check them by eye. Downgrade anything the posts don't support.
3. Write findings in this order: what talking points spread and where they started (including any Reddit ↔ X jumps), how strong the cross-community flow is, which account clusters look coordinated and why, confidence and blind spots.
4. If the user wants a visual, build an interactive page from `community_flow.csv` (spread map) and `coordination.graphml` (account network, hashed labels).

## Outputs

| File | Contents |
|---|---|
| `report.md` | Summary for a human reviewer |
| `narratives.csv` | Each repeated talking point: accounts, platforms, communities, spread order, first seen, span, example |
| `community_flow.csv` | Community → community edges (`r/sub`, `x:#tag`) weighted by talking points that appeared in one first, then the other |
| `accounts.csv` | Per-account platform, metrics, tier, evidence text |
| `coordination.graphml` | Account sync network for Gephi or a graph view |
| `.salt` | Hash salt; reuse it so hashed IDs stay stable across runs |
| `crosslinks/crosslinks.csv` | Every cross-link, before/after member counts, control ratio, mobilized flag, arrival tone and removals |
| `<target>/sentiment_summary.csv`, `sentiment_sample.csv` | Tone per sub with intervals (tone only) |
| `stance_sheet.csv`, `stance_key.csv`, `codes.csv`, `stance_tally.md` | Blind coding sheet, the hidden key, the coder's codes, and the final stance table (per sub, or per sub × subject) |
| `topics.csv`, `names.csv`, `topics.md` | Topic clusters with shares and top terms, and most-mentioned names, per sub |
| `history_scores/comparison.md`, `accounts.csv`, `flagged_shortlist.csv`, `context_summary.md` | Stage-2 flag rates per group, per-account flags and metrics, shortlist accounts with 2+ flags, what the threads they joined were about |
| `claims/candidates.csv`, `spread.csv`, `matches.csv`, `accounts.csv` | Claim candidates, per-claim spread (asserts, disputes, subs, scores), every matching item with stance, account pattern levels with an authenticity (AI-style writing) column |
| `sources/state_media.csv`, `state_media.md` | Links to state media and state-linked proxy sites, by outlet, sub and hashed account |
| `bundles/pairs.csv`, `bundles.json`, `visitors.csv`, `carried.csv` | Position pairs vs the null, the bundles, who comments outside their home sub and how they score, positions carried across subs |
| `matched/<name>_threads.csv`, `<name>_comments.zip` | News-sub threads picked by topic and their comments |
| `calibration.csv` | Known bots found in the data with the signals they did or didn't trip |

`test/make_fake.py` and `test/make_fake_x.py` generate synthetic data with planted bot rings for checking the pipeline after any edits.

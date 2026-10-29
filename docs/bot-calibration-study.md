# Bot Calibration Study: Questions and Predictions

Oct 26, 2026 · @Joseph

## Purpose

This study tests how well our bot detector finds confirmed bots in six streamer and drama subreddits during Oct 20–26, 2026, and whether bots changed anything we reported about that week.

The first run found no bot networks across 294,475 posts and comments from 61,500 accounts. That result only means something if the detector can catch the bots that were there. Confirmed bots from r/BotBouncer give us a known answer to check it against.

## Data

| Piece | What it is | Source |
| --- | --- | --- |
| Subreddit activity | Posts and comments, Oct 20–26, 2026: r/LivestreamFail, r/h3h3productions, r/Destiny, r/Hasan\_Piker, r/atrioc, r/h3snark | Arctic Shift dumps |
| Known bots | Accounts logged by r/BotBouncer, Sept 1 – Oct 26, 2026 | Arctic Shift dump of r/BotBouncer |
| Detector output | Tiers (lead, likely, high) and evidence per account from the six-sub run | social-coordination skill, analyze.py |

Known bots are matched to the detector's output through the run's hash salt, so no usernames appear in the results.

## Predictions

Recorded on Oct 26, 2026, before the Bot Bouncer data was opened. Each gets marked right or wrong in Results.

| # | Prediction | Right if |
| --- | --- | --- |
| P1 | 20 to 80 of the week's 61,500 accounts are on the Bot Bouncer list | Count falls in 20–80 |
| P2 | Most sit in r/LivestreamFail and r/h3h3productions; close to none in r/atrioc or r/h3snark | Over half in LSF + h3h3; 2 or fewer in atrioc + h3snark |
| P3 | Their activity bunches on Oct 23–24, in the busiest affair threads | Bots' share of activity on Oct 23–24 exceeds everyone else's |
| P4 | At least 80% are karma farmers: reposts, copied comments, generic replies | 80%+ of hand-coded bots fall in those three types |
| P5 | Usernames lean toward the auto-generated Word-Word-1234 style | More common among bots than among everyone else |
| P6 | Comments are short and generic or copied; some copied ones score well | Median length below others'; at least a few copied comments score above the sub's median |
| P7 | None push a side in the Atrioc, Destiny, Hasan or H3 fights | Zero bots with feud-side posts in hand-coding |
| P8 | Recall: 30–40% get any tier, under 20% reach likely or high | Measured recall in those ranges |
| P9 | Flag rate on everyone else stays in the hundredths of a percent | Likely+ rate on non-listed accounts below 0.1% |
| P10 | Caught bots mostly trip the content or burst signals | Those two families account for most flags among caught bots |

Results that would surprise me: more than 200 listed accounts in the data, a group of listed bots acting in sync, or listed bots concentrated in r/Destiny or r/Hasan\_Piker.

## Core questions

These are answered with measures fixed in advance.

| # | Question | Measure |
| --- | --- | --- |
| Q1 | What are we looking for? | Count of listed bots active in the six subs that week; where and when they posted |
| Q2 | What did we find? | Scorecard of P1–P10, each marked right or wrong |
| Q3 | Which signals separate bots from everyone else across large amounts of data? | Compare listed bots with all other accounts on each signal (posting cadence, repeated text, bursts, username style, number of subs, items per account) and rank signals by how well they separate the two groups |
| Q4 | Did the detector do a good job? | Recall on listed bots (any tier, likely+, high), flag rate on non-listed accounts, and the share of predictions that landed |

## Added questions

| # | Question | Measure |
| --- | --- | --- |
| Q5 | Did bots change what we reported? | Share of bot posts and comments among the week's repeated talking points, top posts, and the Atrioc and Destiny sentiment samples; findings rerun with bots removed |
| Q6 | Do the bots act alone or in groups? | Sync edges between listed bots in the coordination network; any group of 3 or more |
| Q7 | Did any bot take a side in the Atrioc, Destiny, Hasan or H3 fights? | Hand-coding of every listed bot's posts that mention those names |
| Q8 | What kinds of bots does Bot Bouncer miss? | Types it lists against types the research describes (polished AI commenters, persona accounts); stated as a limit on Q4 |

## Exploratory questions

Answered last and labeled as exploratory, since these are where a pattern is easiest to find because we went looking for one. Anything found here becomes a prediction for the next cross-section rather than a conclusion.

- Q9: What in the bot data helps explain trends we already saw that week (the h3h3 surge, LSF's shift toward general news clips, r/h3snark's removed posts)?
- Q10: Anything else in the bot data that stands out.

## Limits

- Bot Bouncer is incomplete ground truth. It lists accounts someone reported or its checks caught, mostly karma farmers and reposters. Recall here means recall on the bots it happened to list.
- A listed account that was a bot elsewhere may have posted normally in these subs. Hand-coding checks a sample before any account is counted as a bot in our data.
- The dumps hold no votes or account creation dates, and removed comments are missing, so vote manipulation and account age can't be tested.
- One week dominated by one news event. Results describe that week, and Q9–Q10 findings carry forward only as predictions.

## Method: learn, freeze, then test

Bot behavior is learned only from Sept 1 – Oct 19, 2026. Nothing from Oct 20–26 is opened until the rules are written down and frozen in this doc.

1. Learn: take accounts Bot Bouncer listed Sept 1 – Oct 19 and their activity in the training-window data. Describe what they post, how often, when, and how their names look, against ordinary accounts in the same window.
2. Freeze: write the resulting bot rules here, with thresholds, before the test.
3. Test: apply the frozen rules to Oct 20–26. Score them against every Bot Bouncer listing of accounts active that week, alongside the original detector, on the same measures as Q4.

Training data: the Bot Bouncer listings themselves (names, dates, and whatever each listing records about the account) plus r/LivestreamFail posts for Sept 1 – Oct 19 from the year-long posts file. No extra comment dumps. The question is whether this alone improves detection across all six subs in the test week.

Known contamination: the original detector and my sense of this week were already shaped by working on Oct 20–26. The split keeps the new rules from being tuned on the test week; it does not make me blind to it.

## What training showed

The training listings hold 265,007 Bot Bouncer entries from Aug 31 – Oct 19: 244,286 banned, 154 confirmed human ("organic"), the rest pending or purged. Each entry is only a username, a date and a status, with no reason given.

- Almost no training bots appear in the pre-test subreddit data: 5 posted on LSF between Jan 1 and Oct 19 (6 posts), and 24 commented in the Jan 1–8 LSF comment file (76 comments). Behavior rules can't be learned from that few.
- Those 24 accounts commented like ordinary people in January, and their account IDs skew older: median ID about half the ordinary median. That fits aged accounts later sold or taken over and turned into bots, and cuts against my prediction of brand-new accounts.
- Usernames carry real signal. The Reddit default style (Word\_Word1234) appears in 39.2% of banned names against 17.4% of ordinary ones (2.3×), and names ending in 3+ digits in 55.5% against 29.1%. A name-only model separated banned from ordinary names with AUC 0.78 on held-out training names.
- At thresholds that flag 1% of ordinary names, the name model catches 8.2% of banned names; at 5%, it catches 22.0%. It also flags 6.5% of confirmed-human names at the 1% threshold. With bots near 0.1% of accounts, a name alone will mostly flag people.

## Frozen rules

Fixed on Oct 26, 2026 before the test week's labels were opened.

| Rule | Definition | Role |
| --- | --- | --- |
| R1 Herd list | Account listed as banned by Bot Bouncer before Oct 20 | Direct flag, scored on its own |
| R2 Name score | Name model score ≥ 0.886 (top 1% of ordinary training names) | Adds an "account" signal family to the original detector, replacing the account-age family the dumps can't support |
| R3 Account age | Older-than-typical account ID | Not used: based on 24 accounts, too thin |
| Combined | Original detector tiers with R2 added as a family; R1 reported beside it | Compared against the original detector alone |

Test labels: every account active Oct 20–26 that Bot Bouncer lists as banned, from either period. Results are split into accounts first listed before Oct 20 (where R1 wins by construction) and accounts first listed Oct 20–26, which are the fair test for R2 and the detector.

## Results

The original detector caught none of the 42 Bot Bouncer bots active that week, and the name rule caught one; checking accounts against Bot Bouncer's earlier list would have caught 34 (81%). Four of ten predictions held.

### Prediction scorecard

| # | Prediction | Result | Verdict |
| --- | --- | --- | --- |
| P1 | 20–80 listed accounts | 42 of 61,500 (0.07%) | Right |
| P2 | Mostly LSF and h3h3; near none in atrioc or h3snark | 22 in LSF, 11 in h3h3, 1 in atrioc, 0 in h3snark | Right |
| P3 | Activity bunched on Oct 23–24 | 65.5% of bot activity on those days vs 56.3% for everyone else | Right |
| P4 | 80%+ karma farmers | Zero copied comments or reposts; most read like ordinary arguers or casual repliers | Wrong |
| P5 | Default-style names more common | 16.7% of bots vs 18.7% of everyone else | Wrong |
| P6 | Short, generic or copied comments | Median 15 words vs 16; no verbatim copies | Wrong |
| P7 | None take a side in the feuds | 12 feud mentions; about 7 took a side, in no consistent direction | Wrong |
| P8 | Recall 30–40% any tier, under 20% likely+ | 0% any tier | Wrong |
| P9 | Flag rate on others in hundredths of a percent | 0.002% likely+ | Right |
| P10 | Caught bots trip content or burst signals | No bots caught | Untestable |

### Detection results (Q1, Q4)

42 listed bots were active Oct 20–26, posting 171 items with a median of one each. 34 were first listed before Oct 20; 8 were first listed during the test week.

| Method | All 42 bots | 34 listed before Oct 20 | 8 newly listed | Flag rate on other accounts |
| --- | --- | --- | --- | --- |
| Original detector, any tier | 0% | 0% | 0% | 0.19% |
| Original detector, likely+ | 0% | 0% | 0% | 0.002% |
| R2 name score | 2% | 3% | 0% | 1.19% |
| Combined (original + R2), any tier | 2% | 3% | 0% | 1.37% |
| R1 herd list | 81% | 100% | 0% | 0% |

The detector was built for crude, repetitive automation. These accounts post once or twice, write original-sounding text, and never act in sync, so none of its signals fire. The name model adds false flags faster than catches. The one rule that worked, R1, is a lookup: bots keep posting after Bot Bouncer bans them in other subs, and these six subs don't run it.

### Signals that separate bots (Q3)

| Signal | Bots | Everyone else |
| --- | --- | --- |
| Account ID among the newest 3% active that week | 44% (18 of 41) | about 3% by definition |
| Comments with a negative score | 13.3% | 6.7% |
| Activity on the surge days, Oct 23–24 | 65.5% | 56.3% |
| Active in 2+ of the six subs | 0% | 5.6% |
| Items per account, median | 1 | 2 |
| Default-style username | 16.7% | 18.7% |

Account newness is the standout, and the dumps carry it: each comment's author ID is assigned in sign-up order, so a high ID means a recent account. Training pointed the other way (older IDs), because the 24 training bots were drawn from January activity, when brand-new accounts couldn't appear. That makes newness a finding to test on another week, not a rule yet.

### Added questions (Q5–Q8)

- Q5, did bots change what we reported: no. Bots wrote 171 of 294,475 items (0.06%), none of the repeated talking points, none of the week's top posts, one of the 260 r/atrioc Atrioc mentions and one of the 1,373 r/Destiny Destiny mentions. Their most-upvoted comment, a 178-point LSF jab at Hasan's N-word clip, is the largest single trace.
- Q6, alone or in groups: alone. None of the 42 appear in the coordination network, none posted in more than one of the six subs, and their activity shows no shared timing.
- Q7, feud sides: about 7 of 12 feud mentions took a side, scattered across positions (for and against Ethan, against Hasan, sympathetic to Atrioc). No bloc pushed one line.
- Q8, what Bot Bouncer catches: hand-coding sorted the 42 roughly into 15 argumentative opinion accounts (politics, Israel, Trump, drama), about 6 with a polished, emotional style that reads like AI-written personas, and about 20 casual one-liners and image or gif replies. Bot Bouncer's evaluators look at account history across Reddit, which this study can't see, so some of these may be sold or hijacked accounts and a few may be misjudged humans. Its 154 "organic" entries show it does reverse calls.

### Exploratory (Q9–Q10)

Labeled exploratory; each becomes a prediction for the next cross-section.

- The h3h3 surge pulled bots in. 9 of the 11 bots active in h3h3 first appeared on or after Oct 23, matching the crowd of first-time accounts.
- Bot comments were downvoted twice as often as everyone's. In LSF, the most active listed accounts argued politics and drew negative scores, which fits accounts built to provoke rather than to farm karma.
- 18 of 41 bots were among the newest 3% of accounts; the rest spread across all ages, including 3 among the oldest 10%. Fresh sign-ups look like the main supply, with some aged accounts in the mix, which fits the January training bots that commented like ordinary people before being listed.
- What the original week's picture gets right: the busy, organic reading of the h3h3 surge holds, since bots were a rounding error inside it.

## Next test: version 2 on a fresh week

Version 2 adds the two changes this study pointed to, and gets tested on Oct 6–12, 2026, a week not used for any discovery. Frozen on Oct 26, 2026 before that week's data was opened.

| Rule | Definition |
| --- | --- |
| V1 Lookup | Account listed as banned by Bot Bouncer before Oct 6 (`--known-before 2026-10-06`) |
| V2 Newness | Account among the newest 3% of accounts in the week's data by Reddit account ID (an "account" signal family) |
| V3 Combined | Flagged by V1 or V2 |
| Baseline | Original detector tiers, for comparison |

Test labels: accounts active Oct 6–12 that Bot Bouncer lists as banned at any point through Oct 26.

### Predictions for the fresh week

| # | Prediction | Right if |
| --- | --- | --- |
| F1 | 30–70 listed bots active | Count in range |
| F2 | V1 catches 60–80%, lower than this week's 81% because the list is two weeks shorter | Recall in range |
| F3 | V2 catches 35–50% of bots while flagging about 3% of everyone | Recall in range |
| F4 | V3 catches 80–90% | Recall in range |
| F5 | Baseline detector catches 5% or fewer | Recall at or below 5% |
| F6 | Bots again act alone: none in the sync network | Zero bots with sync partners |

### Fresh-week results (Oct 6–12)

Version 2 caught 22 of 34 confirmed bots (65%), against zero for the original detector, but most of what it flags is people: 813 accounts flagged to find those 22. Three of six predictions held.

| Method | Recall on 34 bots | Flag rate on other accounts | Bots among flagged accounts |
| --- | --- | --- | --- |
| V1 Lookup (listed before Oct 6) | 50% (17) | 0% | 17 of 17 |
| V2 Newness (newest 3%) | 32% (11) | 2.96% | 11 of 802 |
| V3 Combined | 65% (22) | 2.96% | 22 of 813 |
| Baseline detector, any tier | 0% | 0.07% | 0 |

| # | Prediction | Result | Verdict |
| --- | --- | --- | --- |
| F1 | 30–70 listed bots | 34 of 26,757 accounts | Right |
| F2 | Lookup catches 60–80% | 50% | Wrong, lower |
| F3 | Newness catches 35–50% at \~3% flag rate | 32% at 2.96% | Wrong, just under |
| F4 | Combined 80–90% | 65% | Wrong, lower |
| F5 | Baseline 5% or less | 0% | Right |
| F6 | Bots act alone | None in the sync network | Right |

The lookup did worse than in the discovery week because half of this week's bots weren't listed yet: 7 were first listed during Oct 6–12 and 10 after it. Bot Bouncer often lists accounts days or weeks after they start posting. Newness held up as a real signal, about 11 times the base rate, though at 3% of all accounts it produces far more people than bots and only works as a pointer for review. The original behavioral signals again caught nothing.

## Stage 2 pre-registration: full-history check (frozen Oct 27, 2026, before any histories were pulled)

Sample: from the Oct 6–12 data, 300 shortlisted accounts (the strongest-signal 300 of 2,693 flagged), 300 random controls that tripped nothing, and 17 Bot Bouncer bots listed before Oct 6. Up to 1,000 newest posts and comments per account, across all of Reddit. Validation: Bot Bouncer bots listed after Oct 6 that turn up in any group.

Rules (from `history.RULES`; no changes after seeing results for this run):

| Rule | Definition | Predicted: known bots | Predicted: shortlist | Predicted: controls |
| --- | --- | --- | --- | --- |
| dormant\_then\_burst | silent 180+ days, then 20+ items within 30 days | 25% | 8% | 3% |
| metronome | 30+ items, posting-interval CV under 0.5 | 5% | 2% | 1% |
| rapid\_fire | 30+ items, 20%+ of gaps under 60 seconds | 10% | 4% | 3% |
| farm\_subs | 20%+ of activity in karma-farming subs | 35% | 8% | 2% |
| self\_repeat | 10+ comments, 20%+ verbatim repeats of own text | 15% | 4% | 2% |
| ai\_style | 5+ comments, 30%+ match the AI-quip template | 30% | 15% | 1% |
| fast\_replies | 10+ comments with context, 50%+ within 10 min of the thread | 40% | 25% | 20% |
| topic\_hopper | 20+ subs, no sub over 10% of activity | 25% | 10% | 5% |
| 2+ flags | any two rules | 50% | 15% | 5% |

Other predictions: farm\_subs and ai\_style will separate known bots from controls best; metronome will be near useless (bots in the week data had human-like irregular timing); fast\_replies will fire often for everyone in drama subs and show little lift; around 10% of shortlist and known-bot accounts will return thin or empty histories because they were suspended or deleted. Pass mark for keeping a rule: known-bot rate at least 5× the control rate with controls under 5%.

## Stage 2 results (Oct 27, 2026; thread context still pulling, so fast\_replies not yet scored)

Histories came back for 616 of 617 accounts (one shortlisted account empty; all 17 known bots intact, against a predicted \~10% loss). Up to 1,000 newest items each.

| Rule | Known bots (n=17) | Shortlist (n=299) | Controls (n=300) | Predicted bots / controls | Verdict |
| --- | --- | --- | --- | --- | --- |
| dormant\_then\_burst | 18% | 9% | 10% | 25% / 3% | fail (controls 10%) |
| metronome | 0% | 0% | 0% | 5% / 1% | fail, as predicted |
| rapid\_fire | 6% | 2% | 1% | 10% / 3% | fail (1 bot) |
| farm\_subs | 0% | 0% | 0% | 35% / 2% | fail; nobody posts in karma-farm subs |
| self\_repeat | 0% | 0% | 0% | 15% / 2% | fail |
| ai\_style | 0% | 0% | 0% | 30% / 1% | fail; threshold far above reality (highest bot 15%) |
| topic\_hopper | 35% | 11% | 18% | 25% / 5% | fail (controls 18%) |
| 2+ flags | 0% | 1% | 3% | 50% / 5% | fail |

No pre-registered rule passed. The two predicted best signals (karma-farm subs, AI-style share) were the worst. Validation is also thin: only one shortlisted account was banned by Bot Bouncer after Oct 6, and none of the controls.

Exploratory (found in this data, so it needs testing on fresh accounts): the known bots split into two kinds. Six or seven are young "tourist" accounts, created June–September 2026, with 16–30 items total, almost every item in a different subreddit (SaaS, automation and self-improvement subs, plus one drive-by comment in a drama sub). The rest are older, ordinary-looking accounts with long dormant stretches (1–4 years) before resuming. A rule of first item within 6 months, 60 or fewer items, 10+ subs and subreddit spread of 0.95+ matched 6 of 17 known bots and 1 of 300 controls. Caution: Bot Bouncer's own evaluators look at history spread, so this partly measures how Bot Bouncer decides. Strongest single continuous measures (AUC, known bots vs controls): subreddit spread 0.79, subs per 100 items 0.78; AI-style share 0.66.

## Stage 2 update: thread context added (Oct 28, 2026)

Full context: 263,971 threads. The pre-registered fast\_replies rule (10+ comments with context, 50%+ within 10 minutes of the thread being posted) fired for 5 of 17 known bots (29%), 0 of 299 shortlisted and 0 of 299 controls. It is the only frozen rule that passed (predicted 40% / 20%; the false-alarm rate was far lower than expected). 2+ flags: known bots 12%, shortlist 1%, controls 3%.

Exploratory: all seven young "tourist" bots have a median reply time of 8.4–11.9 minutes after the thread was posted. The fastest control median is 15.3 minutes; the control median is about 4 hours. The ten older known-bot accounts look like ordinary users on every measure (medians 2.5–10 hours). Median reply of 15 minutes or less: known bots 7 of 17, shortlist 1 of 299, controls 0 of 299. The one shortlisted match (name withheld: 70 items across 54 subreddits, median reply 7.3 minutes, three comments in three unrelated subs within five minutes, lowercase quip style) has not been listed by Bot Bouncer; reporting it there is the out-of-sample test.

## Round 2 pre-registration: v2 rules (frozen Oct 28, 2026, before any Oct 13–19 histories are pulled)

New rules, added to `history.RULES` and derived from the 17 Oct 6–12 known bots (so the in-sample rates below are optimistic):

| Rule | Definition | In-sample: bots / controls | Predicted on Oct 13–19: bots / controls |
| --- | --- | --- | --- |
| reply\_window | 8+ comments with context, median reply 5–15 min after the thread was posted | 41% / 0% | 25% / 1% |
| tourist | first item within 6 months, 60 or fewer items, 10+ subs, spread 0.95+ | 35% / 0% | 20% / 1% |
| hit\_and\_run | 10+ threads, 5% or fewer revisited, 55%+ top-level | 24% / 3% | 15% / 3% |
| uniform\_length | 10+ comments, median 25+ words, word-count CV 0.85 or lower | 41% / 3% | 25% / 4% |
| 2+ v2 flags | any two of the four | 41% / 0% | 20% / under 1% |

Other predictions: the older-account bot type stays invisible to every rule (60%+ of bots missed); tourist bots won't share threads or sit next to each other in account-ID order (none did in round 1, so a coordination detector won't see them).

Test design: shortlist Oct 13–19 with the same stage-1 screen, equal random controls, full histories plus thread context. Positives are accounts in that week that Bot Bouncer bans, excluding the 17 round-1 bots. Pass mark unchanged: bot rate at least 5× control rate with controls under 5%.

Also checked in round 1 and dropped as weak: sleep gap (quietest 6 hours), link share, comment score, edits, posts share, account-ID clustering.

## Round 2 results, preliminary (Oct 28, 2026; thread context still pulling)

Histories for 642 accounts active Oct 13–19: 13 Bot Bouncer bots banned after Oct 13 (the fresh test), 27 banned before, 4 round-1 bots, 299 shortlisted, 300 random controls. Reply-timing rules wait for the thread context.

| Rule | Fresh bots (13) | Earlier bots (27) | Controls (300) | Predicted bots / controls | Verdict |
| --- | --- | --- | --- | --- | --- |
| tourist | 0% | 7% | 0% | 20% / 1% | Precise but rare: 2 of 40 bots |
| hit\_and\_run | 0% | 15% | 6% | 15% / 3% | Fail: controls over 5% |
| uniform\_length | 8% | 22% | 3% | 25% / 4% | Pass on earlier bots (7× controls); weak on fresh ones |
| 2+ v2 flags (without reply\_window) | 0% | 7% | 0% | 20% / under 1% | Pending reply\_window |
| topic\_hopper (v1) | 15% | 41% | 19% | — | Fail again |

Why the fresh bots slipped through: 4 of the 13 were brand-new accounts with 5–8 comments, each in a different sub (several promoting adult content). They are too new to reach the tourist rule's 10-sub minimum. Most of the rest are older accounts that look ordinary.

Exploratory (for round 3, not yet tested): an account whose first-ever post is under 90 days old covers 54% of fresh bots and 52% of earlier bots, against 2.7% of controls. That is account age again, measured from history instead of the account ID. Young accounts posting 15+ items a day: 5 of 27 earlier bots, 0 controls. Brand-new (under 10 days) with 15 or fewer items: 4 of 13 fresh bots, 0 controls.

## Round 2 final, with thread context (Oct 29, 2026)

Context: 288,247 threads. Reply-timing results:

| Rule | Fresh bots (13) | Earlier bots (27) | Controls (299) | Predicted bots / controls | Verdict |
| --- | --- | --- | --- | --- | --- |
| reply\_window (v2) | 0% | 15% (4) | 0% | 25% / 1% | Pass: replicates out of sample |
| fast\_replies (v1) | 0% | 11% (3) | 0% | — | Pass again |
| 2+ v2 flags | 0% | 15% | 0% | 20% / under 1% | Pass, below predicted recall |
| 2+ flags, any rule | 8% | 26% | 4% | — | Weak |

The 4 reply-window bots repeat round 1's pattern exactly: young accounts with 17–42 items, median reply 7–11 minutes after the thread was posted. The scheduler fingerprint held on bots the rules had never seen, with no false alarms among 299 controls.

Combined: any passing rule (reply\_window, tourist, uniform\_length) catches 26% of earlier bots and 8% of fresh bots at 4% of controls. Adding "first post under 90 days ago" (exploratory) raises that to 70% and 62% at 6% of controls.

What round 2 shows: the rules catch one kind of bot well, the young scheduled tourist. Fresh bots that are days old and have posted under 10 times don't have enough history for any behavior rule; account age is the only signal that reaches them. For round 3, freeze account age from history as a rule and test all of this on a new week.

## Round 3 pre-registration (frozen Oct 29, 2026, before the Oct 20–26 shortlist is built)

Test week: Oct 20–26, the H3 affair week. Same design: stage-1 shortlist, equal random controls, full histories plus thread context. Bot groups: banned before Oct 20, banned after Oct 20 (fresh), and earlier-round bots reported separately. Check date for age rules: Oct 27.

New rule: **young\_account**, the earliest item in the pulled history is under 90 days before the check date. All earlier rules unchanged.

| Rule | Predicted: bots | Predicted: controls |
| --- | --- | --- |
| young\_account | 50% | 5% (a drama week draws new accounts, so higher than round 2's 3%) |
| reply\_window | 10% | 0–1% |
| uniform\_length | 15% | 3% |
| any of reply\_window, tourist, uniform\_length, young\_account | 60% | 8% |

Other predictions: fresh bots are again mostly days-old accounts with few comments, caught only by young\_account. The affair drama pulls more new human accounts into r/h3h3productions, which will be young\_account's main false alarms.

## Bot-rich round pre-registration (frozen Oct 29, 2026, before any data is pulled)

**Why:** about 95 labelled bots across three rounds leave every catch rate with a wide interval. Bot Bouncer banned 130,331 accounts sitewide in October alone.

**Sample:** 400 accounts drawn at random from Bot Bouncer's October 2026 bans (not previously pulled), plus 200 random accounts active in the six subs Oct 20–26 that Bot Bouncer never listed. Check date Oct 29. Histories capped at 1,000 items, plus each account's oldest post and comment for true age. Thread context in light mode.

**Caveat:** these bots come from all of Reddit, not the drama subs, so they're a different population from the controls. Treat results as "what do Reddit bots look like in general"; the drama-sub rounds keep running alongside.

**New rule:** young\_account\_true, the account's oldest post or comment ever is under 90 days before the check date.

| Rule | Predicted: bots | Predicted: controls |
| --- | --- | --- |
| young\_account\_true | 70% | 3% |
| young\_account (capped history) | 70% | 5% |
| reply\_window | 15% | 0–1% |
| tourist | 15% | 0% |
| uniform\_length | 15% | 3% |
| farm\_subs | 10% | 0% |
| self\_repeat | 8% | 0% |
| ai\_style | 2% | 0% |
| any of reply\_window, tourist, uniform\_length, young\_account\_true | 80% | 7% |

Also predicted: about 25% of the 400 bots come back empty because Reddit already suspended or deleted them. Sitewide bots farm karma and repeat themselves more than drama-sub bots, so farm\_subs and self\_repeat fire here even though they never did before.

## v4 rules: bot-rich round add-on (frozen Oct 29, 2026, before histories are pulled)

**Source:** a three-year-old community guide to spotting Reddit bots. Seven checks were turned into rules. Copied-from-thread comments are left for later because they need thread comments, which the light pull skips.

**Tuning, done only on accounts outside the test groups:** the six subs' Oct 13–19 posters, about 35,000 accounts. There is no dictionary in this workspace, so "common word" means a word used by 8+ different people that week. That makes the name and mash checks rough: invented handles like "floralscarf" still read as gibberish.

- **stock\_name** fires for 30% of ordinary posters, so it will fail as a standalone rule. It is tracked for combining with others.
- **gibberish\_name** fires for 3.7% of ordinary posters.
- **escaped\_text** fired for none of 107,000 items: Arctic Shift stores decoded text.

**Contamination note:** the bot-rich usernames were already visible when this was written, and a cluster of pronounceable nonsense names stood out. The name predictions are informed by that. The first clean test of the name rules is the next fresh round.

| Rule | Predicted: bots | Predicted: controls |
| --- | --- | --- |
| stock\_name | 50% | 30% |
| gibberish\_name | 10% | 4% |
| escaped\_text | 3% | 0% |
| quoted\_comments | 2% | 0% |
| mash\_comment | 3% | 2% |
| scam\_domain | 4% | 0.5% |
| posts\_only | 30% | 4% |
| any v4 flag except stock\_name | 40% | 10% |

By the 5× and under-5% bar, only posts\_only and escaped\_text are expected to pass. scam\_domain will be too rare to judge. gibberish\_name probably misses the bar because of the rough word list.

**v4 revisions (Oct 29, still before any bot-rich data).** Running v4 on the finished round 2 histories exposed two broken checks, and both were fixed before the test:

- **escaped\_text** fired for 6% of controls. Arctic Shift stores 2023 text still escaped, so the check now only counts items from 2024 on. On round 2 it then fires for nobody.
- **mash\_comment** fired for 53% of controls. The thin word list flagged words like "pandora" and "hummus", and a first fix still caught "hahaha". The check now requires few vowels, 5+ different letters and mostly home- or bottom-row keys. On round 2 it then fires for nobody.

The v4 predictions above stand unchanged.

## v5 rules: writing tells (frozen Oct 29, 2026, before bot-rich data)

**Source:** a 2026 guide from a vendor that runs about 200 Reddit marketing accounts, describing the signals mods and detectors use. Thresholds were set on the round 2 controls, aiming for under 2% false alarms.

- **ai\_vocab:** 10+ comments, and 10%+ contain an AI-tic word or phrase (delve, tapestry, furthermore, it's worth noting…) or an em dash.
- **md\_structure:** 10+ comments, and 10%+ have a markdown header, a bold line on its own, or 2+ bullet lines.
- **flat\_sentences:** 5+ comments of 3+ sentences, with median sentence-length CV of 0.3 or lower.

**Round 2 check (partly in-sample):** ai\_vocab 8% of later bots vs 0% of controls; flat\_sentences 4% of known bots vs 1% of controls; md\_structure 0% everywhere.

| Rule | Predicted: bots | Predicted: controls |
| --- | --- | --- |
| ai\_vocab | 10% | 1% |
| md\_structure | 3% | 0% |
| flat\_sentences | 5% | 1% |
| any v5 flag | 15% | 2% |

**Expected limit:** the vendor's own accounts are about 32 months old, post 25–40 comments a week, and are human-edited, so none of these rules should catch them. Bot Bouncer bans skew toward unedited LLM output, which is where v5 should show up if it shows up at all.

## Scoring change: v4 and v5 are secondary (Oct 29, 2026, before bot-rich data)

v4 and v5 rules no longer flag an account by themselves. An account is flagged only by a primary rule: fast\_replies, reply\_window, uniform\_length, young\_account or young\_account\_true. A secondary flag on top of that moves the account into a higher-confidence "primary + secondary" tier.

On round 2 (in-sample for v4/v5):

| Tier | Bots (n=40) | Controls (n=299) |
| --- | --- | --- |
| any primary | 65% | 6% |
| primary + secondary | 35% | 1% |

**Bot-rich prediction:** any primary 75% of bots vs 7% of controls; primary + secondary 50% vs 2%.

## Round 3 results, part 1 (scored Oct 29, 2026, without thread context)

Histories for all 644 accounts arrived; every one had history. Thread context hasn't arrived yet, so reply\_window and fast\_replies can't fire, and those rows wait for part 2. Bot groups are pooled here (25 banned before Oct 20, 9 banned after; n=34) because 9 alone is too few. Intervals are 95% Wilson.

| Rule | Predicted: bots | Actual: bots | Predicted: controls | Actual: controls | Passes 5× and under 5%? |
| --- | --- | --- | --- | --- | --- |
| young\_account | 50% | 41% (26–58%) | 5% | 4% (2–7%) | Yes, 10× |
| uniform\_length | 15% | 9% (3–23%) | 3% | 3% (2–6%) | No, 3× |
| any of tourist, uniform\_length, young\_account (reply\_window pending) | 60% | 44% (29–61%) | 8% | 7% (5–11%) | No, controls over 5% |

**What held:** young\_account passed its first fair test on a new week, close to the predicted rate. The control false-alarm rate matched the prediction almost exactly. Earlier-round bots (n=10) came in at 40%, the same picture.

**What didn't:** uniform\_length fell to 3× and fails the bar this round; round 2's pass doesn't replicate. The combination fails because uniform\_length adds false alarms faster than it adds bots.

**Secondary tier, an honest correction:** the primary + secondary tier reaches 29% of bots vs 3% of controls, but only because stock\_name counts as secondary. Without stock\_name the tier catches 0 of 34 bots. The round 2 tier result (35% vs 1%) leaned on stock\_name the same way. Read the tier as "young account with a Reddit-suggested username", a weaker signal than it looked.

**Other notes:** gibberish\_name hit 3 of 25 earlier-banned bots vs 3% of controls (4×, not passing). Bots had a median of 176 items in their pulled history vs 847 for controls. No v5 writing rule fired for any bot in the two main groups.

## v6 rules: from government and platform reports (frozen Oct 29, 2026, before bot-rich histories are scored)

**Sources:** EEAS 4th FIMI threat report (Mar 2026), VIGINUM's Storm-1516 report (2025), Taiwan NSB's 2025 report, Meta's adversarial threat report (2026), OpenAI's influence-operation reports. All four rules are secondary. They target the sophisticated pattern these reports describe: bought aged accounts, warmed up with neutral posts, then turned to politics with little real engagement.

- **political\_pivot:** 20+ items; the first 70% of history is 5% or less political, the last 30% at least 30% political. Source: VIGINUM's account warm-up phase; Taiwan's content farms that build traffic before switching to politics.
- **sub\_shift:** a 180+ day silence with 10+ items on each side and no subreddit in common before and after. Source: VIGINUM's bought aged accounts; Taiwan's hijacked PTT accounts.
- **low\_engagement:** 30+ comments, median score 1 or less, 90th-percentile score 2 or less. Source: EEAS finding that most operations show volume without organic engagement.
- **batch\_id:** Reddit account ID within 5,000 of another account in the same pool. Source: VIGINUM's burner accounts bought in lots with identical creation dates; Meta's dormant-account inventories.

**Round 2 check (in-sample):** none of the four separates drama-sub bots from controls. political\_pivot 0% bots vs 0% controls; sub\_shift 4% of known bots vs 1%; low\_engagement 8% of later bots vs 3%; batch\_id 0% vs 0%. That fits the reports: these rules target aged, bought accounts, and the drama-sub bots are days-old accounts.

| Rule | Predicted: bots (bot-rich) | Predicted: controls |
| --- | --- | --- |
| political\_pivot | 3% | 1% |
| sub\_shift | 8% | 1% |
| low\_engagement | 15% | 3% |
| batch\_id | 3% | 0.5% |
| any v6 flag | 25% | 5% |

Expected to pass the 5× bar: sub\_shift and low\_engagement. Bot Bouncer bans many repurposed aged accounts and spam that nobody upvotes.

**Considered and dropped:** reply pairs (two accounts replying to each other 3+ times, the OpenAI "Sneer Review" pattern of posting and replying to yourself). Round 2 had 120 such pairs, almost all regulars arguing; one involved a known bot. Kept as a review metric only.

## Bot-rich round results, part 1 (scored Oct 29, 2026, before thread context)

Histories for 398 of 400 Bot Bouncer October bans and all 200 controls. Only 2 bots came back empty, against a prediction of about 25%: Arctic Shift keeps an account's archive after Reddit suspends it. Thread context is still pulling, so reply\_window and fast\_replies wait for part 2. Intervals are 95% Wilson. Reminder: these bots come from all of Reddit and the controls from the six drama subs, so some differences reflect the two populations, not botness. Drama regulars, for example, trip dormant\_then\_burst (14%) and topic\_hopper (14%) far more than the bots.

| Rule | Predicted bots | Actual bots | Predicted controls | Actual controls | Passes 5×, under 5%? |
| --- | --- | --- | --- | --- | --- |
| young\_account\_true | 70% | 87% (83–90%) | 3% | 4% (2–8%) | Yes, 22× |
| young\_account | 70% | 87% | 5% | 4% | Yes |
| tourist | 15% | 11% (8–15%) | 0% | 0% (0–2%) | Yes |
| uniform\_length | 15% | 7% | 3% | 2% | No, 3.5× |
| farm\_subs | 10% | 0% | 0% | 0% | No: never fires |
| self\_repeat | 8% | 1% | 0% | 0% | Too rare |
| ai\_style | 2% | 0% | 0% | 0% | Never fires |
| any of tourist, uniform\_length, young\_account\_true (reply\_window pending) | 80% | 89% (86–92%) | 7% | 6% (4–11%) | No, controls over 5% |
| posts\_only (v4) | 30% | 22% (19–27%) | 4% | 0% (0–2%) | Yes |
| stock\_name (v4) | 50% | 59% | 30% | 34% | No, as expected |
| gibberish\_name (v4) | 10% | 4% | 4% | 5% | No |
| escaped\_text, quoted\_comments, mash\_comment, scam\_domain (v4) | 2–4% each | 0% | 0–2% | 0% | Never fire |
| any v4 except stock\_name | 40% | 23% | 10% | 6% | No, 4× |
| ai\_vocab (v5) | 10% | 1% | 1% | 0% | Too rare |
| md\_structure, flat\_sentences (v5) | 3–5% | 0–1% | 0–1% | 0–1% | No |
| low\_engagement (v6) | 15% | 5% (3–7%) | 3% | 0% (0–3%) | Yes, but rare |
| political\_pivot, sub\_shift, batch\_id (v6) | 3–8% | 0–1% | 0.5–1% | 0–2% | No |
| any primary | 75% | 89% | 7% | 6% | No, controls over 5% |
| primary + secondary | 50% | 63% | 2% | 4% | Yes, 16× |
| primary + secondary without stock\_name | — | 26% | — | 1% | Yes |

**What held:** account age is the backbone, now confirmed on 398 bots: 87% caught at 4% false alarms. posts\_only (from the community guide) and tourist pass cleanly with zero control hits. Unplanned: rapid\_fire, a v1 rule that never fired in the drama subs, caught 7% of these bots and 1 control.

**What failed:** almost every content and writing rule. Karma-farm subs, self-repeats, AI-style quips, AI vocabulary, markdown, keyboard mash, scam domains and escaped text are all near zero for Reddit-wide bots in 2026. The government-report rules (pivot, sub\_shift, batch\_id) also stayed near zero; Bot Bouncer's bans skew toward fresh accounts, not the aged bought accounts those reports describe.

**Precision check:** at a 1% bot rate, young\_account\_true is right about 18% of the time and the primary + secondary tier about 14%; without stock\_name, 21% but at a quarter of the catch. Flags remain leads.

## v7 scoring: weights from three rounds (frozen Oct 29, 2026, for the next fresh round)

A logistic regression on every labelled bot and control from rounds 2, 3 and bot-rich (472 bots, 799 controls) set the weights. Testing used each round held out in turn.

| Rule | Weight |
| --- | --- |
| young\_account | +4.30 |
| posts\_only | +1.89 |
| tourist | +1.80 |
| rapid\_fire | +1.34 |
| low\_engagement | +1.15 |
| uniform\_length | +1.13 |
| hit\_and\_run | +1.02 |
| sub\_shift | +0.73 |
| stock\_name | +0.58 |
| gibberish\_name | +0.46 |
| topic\_hopper | +0.28 |
| ai\_vocab | +0.03 |
| dormant\_then\_burst | −0.59 |

| Held-out round | AUC | Score at \~3% false alarms | Account age alone |
| --- | --- | --- | --- |
| Round 2 | 0.82 | 42% caught, 1.7% false alarms | 52% at 2.7% |
| Round 3 | 0.72 | 38% at 2.7% | 41% at 4.0% |
| Bot-rich | 0.94 | 64% at 2.5% | 87% at 4.0% |

The score trades some catch for fewer false alarms; account age does most of the work.

**New structure:** PRIMARY (flags an account) = young\_account, young\_account\_true, posts\_only, tourist, reply\_window, fast\_replies. SUPPORT (raises confidence) = rapid\_fire, low\_engagement, uniform\_length, hit\_and\_run, stock\_name. RETIRED (reported, no weight) = everything else. On bot-rich, the new primary tier catches 88% of bots at 4% of controls, primary + support 60% at 2%, primary + support without stock\_name 17% at 0%. These are in-sample; the next fresh round tests them.

## Bot-rich round results, part 2: thread context (scored Oct 29, 2026)

Thread context covered 92,610 threads. Reply times exist for 278 of 398 bots (the rest never replied in a thread we pulled) and all 200 controls. Same 398 bots and 200 controls as part 1; intervals are 95% Wilson.

| Rule | Predicted bots | Actual bots | Predicted controls | Actual controls | Passes 5×, under 5%? |
| --- | --- | --- | --- | --- | --- |
| reply\_window | 15% | 8% (6–11%) | 0–1% | 0% (0–2%) | Yes, but half the predicted catch |
| fast\_replies | — | 5% (3–7%) | — | 0% (0–2%) | Yes, but rare |
| any of reply\_window, tourist, uniform\_length, young\_account\_true | 80% | 89% (86–92%) | 7% | 6.5% (4–11%) | No, controls over 5% |
| v7 primary tier (any primary rule) | — | 89% (86–92%) | — | 4% (2–8%) | Yes, 22× |

**What held:** both reply-timing rules are clean, with zero control hits. **What failed:** their reach. reply\_window and fast\_replies together fire for 35 bots, and only 4 of those weren't already flagged by account age, posts\_only or tourist. The frozen any-of-four combination misses the 5% bar because uniform\_length adds control hits; the v7 primary tier, which drops uniform\_length to support, passes.

**Effect on v7:** reply timing stays primary because it costs nothing in false alarms and catches some aged accounts that age rules miss, but it adds about 1 point of catch here. Weights unchanged; the next fresh round (Oct 20–26 with thread context) is the real test.

## Round 3 results, part 2: thread context (scored Oct 29, 2026)

Thread context arrived for the Oct 20–26 round. Reply times exist for all 34 pooled bots and 299 of 300 controls. Intervals are 95% Wilson. My guess stated before scoring was that reply\_window would come in near 5% of bots, under the frozen 10%.

| Rule | Predicted bots | Actual bots (n=34) | Predicted controls | Actual controls (n=300) | Passes 5×, under 5%? |
| --- | --- | --- | --- | --- | --- |
| reply\_window | 10% | 3% (1–15%) | 0–1% | 0.7% (0–2%) | No, 4× on one bot |
| fast\_replies | — | 0% (0–10%) | — | 0.3% | No |
| any of reply\_window, tourist, uniform\_length, young\_account | 60% | 44% (29–61%) | 8% | 8% (5–12%) | No, controls over 5% |
| v7 primary tier | — | 44% (29–61%) | — | 5.0% (3–8%) | Borderline |

**What failed:** reply timing in the drama subs. The two reply rules flagged 1 bot that nothing else caught and 3 controls that nothing else flagged, so they pushed the primary tier's false alarms from 4% to 5%. Drama-sub bots are days-old accounts with few comments; ordinary regulars who refresh a live thread trip the reply window about as often. Earlier-round bots (n=10) tripped neither rule.

**Bot-rich vs drama subs:** the same rules caught 9% of Reddit-wide bots at 0% of controls. The pooled fit across both rounds (932 accounts, other v7 weights held fixed) gives reply timing a weight of 1.65, close to the placeholder 1.80, but that fit leans on the bot-rich bots.

## v7.1 scoring change (Oct 29, 2026, before the next fresh round)

reply\_window and fast\_replies move from PRIMARY to SUPPORT with weight 1.65 each. Alone they no longer flag an account; next to a primary flag they raise confidence. PRIMARY is now young\_account, young\_account\_true, posts\_only, tourist. Every other weight is unchanged. Applied to round 3, the primary tier drops to 4% of controls with no bots lost except the one reply-only catch. The next fresh week tests v7.1 as frozen here.

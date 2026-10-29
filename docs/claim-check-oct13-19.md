# Claim Check: Oct 13–19, 2026

Oct 28, 2026 · @Joseph

## Predictions (written before looking)

1. Only a small share of comments make a checkable factual claim: 3–6%. The rest are jokes, insults and opinions.
2. Of the distinct claims checked, about half are true or mostly true, 20–30% are false or misleading, and the rest can't be checked.
3. False claims cluster in two places: streamer drama in r/LivestreamFail, and claims about the rival streamer in r/Destiny and r/Hasan\_Piker. r/atrioc has the fewest.
4. The Hasan bot-farm claim rates misleading: not provably false, but the evidence people offered doesn't support it.
5. False claims get upvoted about as much as true ones in their home sub. They get corrected in replies more often in r/LivestreamFail than in the two partisan subs.
6. Fewer than 20 accounts reach the repeat-spreader bar in one week. Most false claims come from accounts that make one.
7. New or bot-flagged accounts are not over-represented among false-claim posters. The bots found so far post quips, not claims.

## Method

**Data.** Every post and comment in r/LivestreamFail, r/Destiny, r/h3h3productions, r/Hasan\_Piker, r/atrioc and r/h3snark from Oct 13–19, 2026 (Eastern time), pulled from Arctic Shift: 98,790 comments after removing deleted items, AutoModerator and mod posts.

**Finding claims.** A claim is a statement of fact someone could prove wrong: a number, an event, a quote, "X did Y." Opinions, jokes, predictions and insults are not claims. A keyword screen flagged 1,241 comments with two or more claim markers (numbers, "reported", "was fired", "fake", dates and similar). From those, plus the week's most-discussed threads, I picked 27 distinct claims that were repeated or highly upvoted and could be checked. To estimate how common claims are overall, I read a random sample of 150 comments by hand.

**Checking.** Each claim was looked up in news coverage and rated:

- **True:** sources confirm it.
- **Mostly true:** right in substance, off in a detail.
- **Misleading:** built on something real but leaves a false impression.
- **False:** sources contradict it.
- **Can't be checked:** no credible source either way, or sources conflict.

Ratings reflect reporting available on Oct 28, 2026, including some published after the week ended. That later reporting changed one rating: "Musk throttled Ukraine's Starlink."

**Counting spread.** Each claim has a text pattern matched against every comment and post. Patterns also catch people pushing back, so every match for the 8 false or misleading claims (65 items) was read by hand and marked assert, dispute or unrelated. Counts for true and unverifiable claims are raw mentions and were not hand-checked.

**Account levels.** Only accounts asserting a false or misleading claim count:

- **Repeat spreader:** 3 or more different false or misleading claims, or repeating one after a reply corrected it.
- **One-directional:** 2 or more, all favoring or hurting the same side.
- **One-off:** a single false or misleading claim.

Accounts are identified by hashed IDs. The code is `socialscope/claims.py` in the skill: `candidates`, `spread` and `accounts`.

## Results

About 1 comment in 10 makes a checkable factual claim: 15 of 150 in the random sample (95% interval 6–16%). Most are small and harmless, like who voiced a Simpsons character or what a streamer said last week. The keyword screen caught only 1.3% of comments, so automatic claim-finding misses most claims.

&#91;embedded content: 27 claims from six subreddits, Oct 13–19, 2026, checked against news coverage as of Oct 28\]

Of the 27 claims checked, 14 were true or mostly true. 8 were false or misleading, and 5 can't be checked. The false and misleading ones were rare in practice: 19 comments or posts asserted them across the week, against 22 disputing them. The 17 accounts behind those asserts were all one-offs: no account pushed more than one false claim, and none repeated one after being corrected.

**Prediction scorecard**

| # | Prediction | Result |
| --- | --- | --- |
| 1 | 3–6% of comments make a checkable claim | Wrong: about 10% |
| 2 | About half true, 20–30% false or misleading, the rest uncheckable | Right: 52%, 30%, 19% |
| 3 | False claims cluster in LSF drama and rival-streamer claims; fewest in r/atrioc | Half right: they split between r/Destiny (11) and LSF (8); none in r/Hasan\_Piker or r/atrioc. Only the Hasan bot claim was about a rival streamer. |
| 4 | The Hasan bot-farm claim rates misleading | Right |
| 5 | False claims get upvoted like true ones; corrected more in LSF than the partisan subs | Wrong on upvotes: comments asserting false claims scored a median of 9, comments mentioning true ones 2. Corrections in direct replies were too rare to compare (1 of 19). |
| 6 | Fewer than 20 repeat spreaders | Right: none |
| 7 | New or bot-flagged accounts not over-represented | Right: none of the 17 is among the newest 3% of accounts, and none is on the round-2 bot list |

## Claims rated

For false and misleading claims, the count is hand-checked asserts, with disputes in brackets. For the rest it is raw mentions.

**False or misleading**

| Claim | Rating | Asserts (disputes) | Where | Why, and source |
| --- | --- | --- | --- | --- |
| Hasan's viewer count fell after a bot farm was shut down, so he was viewbotted | Misleading | 5 (11) | LSF 4, Destiny 1 | No viewbot farm was shown to be shut down; the "bot farm" news was about Yandex web crawlers. Commenters showed his numbers were already lower days earlier. Kyiv Independent fact check, Oct 13 |
| Tesla's flying Roadster demo was fake | Misleading | 4 (3) | LSF 3, Destiny 1 | The Oct 15 demo was real but showed only brief hops. A viral rooftop clip on Oct 20 was AI-generated. |
| The data-center strikes knocked Russian bot and troll farms offline, so bot activity or online toxicity dropped | Misleading | 2 (6) | Destiny 1, LSF 1 | The "50% drop" chart measured Yandex's own crawlers. Disinformation monitors saw no real drop. Kyiv Independent, Oct 13 |
| Russia has kidnapped up to 700,000 Ukrainian children | Misleading | 2 (2) | Destiny | 700,000 is Russia's own count of children moved, many with families. Ukraine has verified about 19,500 deportations and says the true number may be far higher. Reuters; Ukrinform |
| Ro Khanna is one of Congress's most prolific insider traders | Misleading | 2 | Destiny | His family made thousands of trades a year, among the most in Congress. There is no evidence of insider trading. NOTUS |
| 81% of violent antisemitic crimes since Oct 7, 2023 were committed by the left | Misleading | 1 | Destiny | The figure is 81% of U.S. assaults where politics could be identified, 2021–2026. Most had none. UnHerd / Kaufmann analysis of ADL data |
| Trump had a $2 billion Trump Tower Moscow deal with a Russian oligarch in 1987 | False | 2 | Destiny | He explored a hotel with a Soviet state agency in 1987. No deal was made, and Russian oligarchs did not exist yet. |
| After the strikes, "free Palestine" and "genocide" activity fell 30%, showing those movements are Russian bots | False | 1 | Destiny | No source for the 30% figure; monitors found no change linked to the strikes. Kyiv Independent |

**Can't be checked**

| Claim | Mentions | Where | Why |
| --- | --- | --- | --- |
| FoidElf admitted on stream to harming her cat | 58 | LSF 50, Destiny 8 | A serious accusation passed around as a clip description. No outlet reported it. |
| StickmanTalks uses AI to write his scripts | 33 | r/atrioc | Rests on AI-detector scores, which are unreliable. |
| Neera Tanden was drunk during her debate with Mehdi Hasan | 14 | Destiny 7, Hasan\_Piker 7 | Started as a jab in a post title. No outlet reported it. |
| The order to limit Ukraine's Starshield came from inside the White House | 4 | Destiny, r/atrioc | Reuters' sources said so; later WSJ and Telegraph reports say Musk ordered it. The record conflicts. |
| FoidElf was banned indefinitely from Twitch in 2023 | 3 | LSF, Destiny | No source found. |

**True or mostly true**

| Claim | Rating | Mentions | Where | Source |
| --- | --- | --- | --- | --- |
| OnyxDenji was punched after harassing people he called homeless | Mostly true | 136 | LSF | IBTimes UK. He used slurs at people who told him to leave; what happened before filming is unclear. |
| Mamdani kept Jessica Tisch as NYPD commissioner | True | 77 | Hasan\_Piker 63, Destiny 14 | ABC7 New York |
| Senators, six of them Republicans, asked Trump to cancel his Russian diesel deal | True | 76 | Destiny 71 | NPR, Oct 13 |
| Most Twitch streamers get a 50/50 sub split; 70/30 is for bigger channels | True | 44 | LSF 22, Destiny 19 | Dexerto, Oct 14 |
| Trump called off a livestream of the Fort Hood shooter's execution | True | 43 | LSF 19, Destiny 16, Hasan\_Piker 8 | Inquirer, Oct 15 |
| Press secretary Katie Zacharia was out after five days | True | 42 | Destiny 22, Hasan\_Piker 19 | Boston Globe, Oct 16 |
| Ukrainian drones struck Russian (Yandex) data centers | True | 28 | Destiny 21 | Kyiv Independent; Al Jazeera |
| Kick gives streamers 95% of sub revenue | True | 25 | LSF | Dexerto, Oct 14 |
| Trump signed an order lifting Russia sanctions | Mostly true | 23 | Destiny | AP. He waived new sanctions days before they took effect; existing ones stayed. |
| Musk throttled Ukraine's Starlink | Mostly true | 19 | Destiny 16 | WSJ; The Telegraph. Later reporting says Musk proposed and ordered the slowdown. |
| Rioters looted Team Vitality's Paris HQ and took its CS2 trophies | True | 6 | LSF 5 | Dexerto; Strafe |
| Ro Khanna is worth over $300 million | Mostly true | 5 | Destiny | NOTUS: median estimate $232.7 million |
| FoidElf was banned from Kick over the dog clip | Mostly true | 3 | Destiny, LSF | EarlyGame. Channel went offline; Kick gave no reason. |
| Marine Le Pen polls around 37% for 2027 | True | 3 | Destiny | OpinionWay, Oct 13–14: 35–37% |

## Where false and misleading claims spread

**Two subs, no others.** All 19 asserts were in r/Destiny (11) and r/LivestreamFail (8). r/Hasan\_Piker, r/h3h3productions and r/atrioc had none. r/Hasan\_Piker's most-repeated shaky claim, that Neera Tanden was drunk at her debate, rates "can't be checked" rather than false.

**Every side, aimed at someone the sub already dislikes.** By who the claim hurts: Hasan 5, Musk 4, Russia 4, the left 2, Trump 2, Ro Khanna 2. r/LivestreamFail's were about Hasan and Musk; r/Destiny's were about Russia, Trump, Khanna and the left. None of the false claims flattered anyone.

**They got upvoted, but debunks won inside threads.** Comments asserting a false claim scored a median of 9, against 1 for comments disputing one and 2 for comments mentioning a true claim. The Hasan bot-farm story shows how that plays out. The post title asserting it got 4,236 upvotes, the four comments repeating it got 1 to 3 each, and the top reply, which linked viewer stats showing the drop came first, got 799. Readers upvoted the headline and also rewarded the correction underneath it.

**Corrections rarely came as direct replies.** Only 1 of the 19 asserts got an explicit "that's false"-style reply. Most pushback was posted as separate comments in the same thread, so reply-based correction counts understate it.

**The most-repeated shaky claim couldn't be checked at all.** That FoidElf admitted on stream to harming her cat appeared 58 times across r/LivestreamFail and r/Destiny, one comment with 827 upvotes. No outlet reported it. It's the kind of claim this method can't settle: it may be true, but the only source is people describing a clip.

## Accounts with a pattern

17 accounts asserted a false or misleading claim this week. All 17 are one-offs: each made one such claim, two of them twice. No account reached one-directional or repeat spreader, and none repeated a claim after being corrected.

| Level | Accounts |
| --- | --- |
| Repeat spreader | 0 |
| One-directional | 0 |
| One-off | 17 |

**They don't look like bots.** None is among the newest 3% of accounts active that week, and their median account is older than about two-thirds of the week's accounts. None is on the round-2 bot-check list, and none is a Bot Bouncer-listed account. The false claims came from ordinary, established users, mostly repeating a headline or a half-remembered fact.

| Account (hashed) | Sub | Claim |
| --- | --- | --- |
| acct\_1acb7c8947 | Destiny | Hasan bot-farm drop |
| acct\_945aad362d | LSF | Hasan bot-farm drop |
| acct\_f3c31b3371 | LSF | Hasan bot-farm drop |
| acct\_ecf23a3909 | LSF | Hasan bot-farm drop |
| acct\_e06175ae3b | LSF | Hasan bot-farm drop |
| acct\_7e6fb67d9a | Destiny | Tesla demo was fake |
| acct\_beb63fd946 | LSF | Tesla demo was fake |
| acct\_70050e7f49 | LSF | Tesla demo was fake |
| acct\_cb6cd0c974 | LSF | Tesla demo was fake |
| acct\_ccf8197f3f | Destiny | Bot farms went quiet |
| acct\_72a8e896a6 | LSF | Bot farms went quiet |
| acct\_cd7742b5e5 | Destiny | 700,000 children (twice) |
| acct\_0ae5031314 | Destiny | Khanna insider trading |
| acct\_8c41b79c22 | Destiny | Khanna insider trading |
| acct\_f12571a583 | Destiny | 81% antisemitic crimes |
| acct\_1b041964ea | Destiny | "Free Palestine" drop |
| acct\_30445e2017 | Destiny | Trump 1987 deal (twice) |

One week is too short to see a pattern. An account would need three false claims in seven days to be a repeat spreader. The bar becomes meaningful once these checks run across several weeks, or over the full post histories from the round-2 pull.

## Limits and next steps

**Limits**

- **27 claims is a sample, not a census.** About 1 in 10 comments makes a checkable claim, nearly 10,000 this week, and most are small (TV trivia, game rules). I chose claims that were repeated, upvoted or about the week's news, which tilts toward claims worth checking.
- **Ratings can change.** One flipped from misleading to mostly true when later reporting came out, and one became "can't be checked" when two outlets contradicted each other. Each rating states its source so it can be rechecked.
- **Raw mention counts include disputes.** Only the 8 false or misleading claims were hand-checked for stance.
- **Text patterns miss paraphrases.** A claim reworded far enough isn't counted, so spread figures are lower bounds.
- **Streamer drama is mostly uncheckable.** Claims whose only source is a clip, like the FoidElf cat claim, stay "can't be checked" however often they repeat.
- **No intent.** The account levels show patterns, not motives. A one-off is most likely an honest mistake.

**Next steps**

1. **Run the same 27 claims over the round-2 histories** once that pull arrives, to see whether any of the 17 accounts repeat false claims across months.
2. **Run it on Oct 20–26**, the H3 affair week, to see if the drama week brings more false claims than this news-driven one.
3. **Hand-check stance on the top unverifiable claims** before counting them against anyone.

# Opinion bundles: sample-bias check and carriers (Oct 29, 2026)

Data: comments in r/h3h3productions, r/LivestreamFail, r/Destiny, r/Hasan_Piker and r/atrioc from Oct 13–26, 2026 (376k comments; the h3snark week pull was missing from this corpus), plus full histories of 1,231 accounts from the bot study (597 random controls, the rest shortlist and confirmed bots). Positions are the 13 validated patterns in `socialscope/positions.py`. Co-occurrence uses the curveball null within home sub, 200 randomizations.

## Predictions (stated before running)

1. The three political bundles survive without the bot-study shortlist histories; anti-Hasan weakens but holds; h3 drama stays separate.
2. Carriers are under 5% of position-taking accounts but write most cross-sub position comments.
3. Positions carried into a hostile sub get buried (Hasan criticism in r/Hasan_Piker, Hasan support in r/Destiny); mainstream anti-Trump scores like locals anywhere.

## Sample bias

Half of all position hits (3,255 of 6,479) came from 538 accounts with pulled histories, most of them shortlist accounts. Pair z-scores, observed accounts in brackets:

| Pair | All data | Week only | Week + control histories |
| --- | --- | --- | --- |
| anti_zionist + gaza_genocide | 6.4 (55) | 3.1 (7) | 5.7 (28) |
| anti_tankie + gaza_genocide | 5.5 (173) | 2.5 (27) | 4.6 (74) |
| anti_ice + anti_trump | 5.4 (35) | 2.5 (2) | 4.7 (14) |
| anti_tankie + hasan_neg | 4.5 (118) | 3.1 (29) | 3.2 (50) |
| anti_ice + gaza_genocide | 3.4 (47) | -1.4 (0) | 0.3 (12) |
| anti_trump + gaza_genocide | 2.6 (96) | -0.4 (6) | 2.0 (35) |
| ethan_neg + gaza_genocide | -4.7 (45) | -0.9 (24) | -3.4 (33) |
| gaza_genocide + hila_pos | -5.1 (11) | -2.8 (7) | -4.1 (7) |

Prediction 1 held. With only random-control histories, every main link survives at a lower z (about half the data), and h3 drama stays negatively linked to politics. One link came from the shortlist alone: anti-ICE with Gaza genocide fell from z 3.4 to 0.3. A single week is too thin: most accounts show one position, so pairs barely register. Louvain bundle lists shift between runs even when pair z-scores agree, so read the pairs.

## Carriers and reception

Only 123 of 3,143 position comments in the six subs (4%) came from visitors outside their home sub. 104 of 2,496 position-taking accounts (4.2%) carried any; the median carrier did it once, and the top 10% of carriers wrote 20% of carried comments. Prediction 2 held on share but missed on concentration: there are no heavy carriers.

| Carried bundle | Into | Carried n | Carried at or below 0 | Locals, same position | Sub locals overall | Carried from |
| --- | --- | --- | --- | --- | --- | --- |
| anti-Hasan | LSF | 32 | 22% | 28% (n=165) | 19% | Destiny 27, h3 4 |
| h3 drama | h3 | 26 | 19% | 7% (n=1,577) | 10% | LSF 11, Hasan 8, Destiny 7 |
| h3 drama | LSF | 19 | 11% | 19% (n=123) | 19% | h3 16 |
| pro-Palestine | LSF | 13 | 23% | 34% (n=103) | 19% | Destiny 7, h3 5 |
| anti-Hasan | Destiny | 10 | 0% | 10% (n=325) | 9% | LSF 6, h3 4 |

Prediction 3 couldn't be tested as framed: too few carried comments landed in r/Hasan_Piker (the smallest sub here) or carried Hasan support anywhere. Where cells are big enough, carried positions score about like locals' comments taking the same position, with one exception: outsiders' takes on h3 drama inside r/h3h3productions are downvoted at almost three times the rate of locals' (19% vs 7%).

## Where pollination happens

Among the 597 random six-sub accounts, positions mostly get voiced outside the six subs:

| Bundle | Share voiced outside the six | Top outside subs |
| --- | --- | --- |
| mainstream anti-Trump | 86% | politics, PublicFreakout, stupidpeoplefacebook, thedavidpakmanshow |
| pro-Palestine | 79% | politics, askanything, nyt, Palestine, MapBasedPolls |
| anti-Hasan | 49% | stupidpeoplefacebook, GetNoted, askanything, thedavidpakmanshow, LeftoversH3 |
| h3 drama | 30% | canceledpod, LeftoversH3 |

The six subs barely exchange positions directly. Their regulars carry political positions into general politics and outrage subs, and those subs are the likely mixing points. The tier 1 and 2 expansion lists already include most of them; r/PublicFreakout, r/askanything and r/nyt are additions worth considering.

## Limits

Patterns catch explicit stances only, so quieter agreement and sarcasm are missed. Scores are snapshots; the earlier hostile-crossing check held on second-save rows, but these reception cells weren't rechecked that way. Histories are capped at 1,000 items, and the controls are random among accounts active in two specific weeks.

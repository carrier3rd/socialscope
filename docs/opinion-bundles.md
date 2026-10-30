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

# Tier 1 expansion: 14 more subs, Oct 20–26, 2026 (scored Oct 29)

Data: every comment from Oct 20–26 in r/Asmongold, Conservative, PoliticalCompassMemes, LeftoversH3, h3snark, thedavidpakmanshow, thebulwark, neoliberal, samharris, dsa, TankieTheDeprogram, IsraelPalestine, Palestine and ukraine (215,673 comments after removing mod and bot accounts), the five drama subs for the same week, and the 2,378 account histories from the bot study. r/h3snark was on break all week: its only comments are AutoModerator notices, so it contributes nothing. The drama-sub pulls stop around 11:25 PM on Oct 26 (Arctic Shift timeouts), missing the last half hour of the week.

## Predictions (stated before opening the data)

1. Six-sub regulars write under 3% of comments in most new subs; LeftoversH3 and h3snark are the exceptions, above 15%.
2. A pro-Trump pattern clears the 65% accuracy bar now that right-leaning subs are in the data; Ukraine-skeptic still fails.
3. The three political bundles hold, a fourth right-leaning bundle appears, and h3 drama stays unlinked from politics.
4. anti_zionist and gaza_genocide stay linked (z above 2) among accounts whose home is r/Palestine or r/IsraelPalestine.
5. Visitors from left-leaning subs are buried in r/Conservative (over 40% of their comments at 0 or below); r/IsraelPalestine treats carried pro-Palestine comments like locals'.

## Pattern accuracy in the new subs

Blind read of 12 random matches per pattern from the tier 1 subs, sub hidden until all 180 codes were written. Accuracy is community-specific: six of the 13 patterns validated on the drama subs fall under 65% here.

| Pattern | Accuracy | | Pattern | Accuracy |
| --- | --- | --- | --- | --- |
| ukraine_support | 12/12 | | anti_trump | 7/12 |
| israel_defense | 7/9 | | anti_tankie | 7/12 |
| hasan_pos | 9/12 | | elon_neg | 6/12 |
| anti_zionist | 9/12 | | anti_ice | 6/12 |
| vote_blue | 9/12 | | hasan_neg | 5/12 (LeftoversH3 mocks Hasan haters) |
| ethan_neg | 8/12 | | hila_pos | 2/12 ("I don't feel bad for Hila") |
| gaza_genocide | 8/12 | | trump_pos (draft) | 3/12 (TDS mostly appears mocked) |
| | | | dem_left_critique (draft) | 2/12 |
| | | | ukraine_skeptic (draft) | 1/3, 3 matches in 215k comments |

Rule frozen before the bundles run: comments in the tier 1 subs use only the seven patterns that passed there; the drama subs and histories keep all 13.

## Results

**1. Overlap: missed.** Share of each sub's comments written by accounts with 3+ comments in the five drama subs that week:

| Sub | Share | | Sub | Share |
| --- | --- | --- | --- | --- |
| thedavidpakmanshow | 24.2% | | neoliberal | 3.0% |
| dsa | 17.7% | | Asmongold | 3.0% |
| LeftoversH3 | 17.0% | | IsraelPalestine | 3.1% |
| samharris | 11.1% | | Palestine | 2.8% |
| thebulwark | 6.6% | | ukraine | 1.2% |
| PoliticalCompassMemes | 5.6% | | Conservative | 0.4% |
| TankieTheDeprogram | 4.1% | | | |

LeftoversH3 came in as predicted, but the drama subs reach much further into the liberal and left politics subs than expected. r/thedavidpakmanshow is mostly a Destiny-regular overlap (54 of 83 regular accounts have r/Destiny as home); r/dsa's comes from Hasan regulars, though five accounts write 73% of it.

**2. Pro-Trump pattern: missed.** It read 3/12 accurate. Ukraine-skeptic failed as predicted, on reach as much as accuracy.

**3. Bundles: held, with the fourth bundle untestable.** Pair z-scores match the Oct 29 run: anti_trump + anti_ice 6.6 (was 5.4), gaza_genocide + anti_tankie 5.7 (5.5), hasan_neg + anti_tankie 5.5 (4.5), gaza_genocide + anti_zionist 5.1 (6.4). Louvain merged pro-Palestine and anti-Hasan into one community this time, which the earlier write-up warned it does; the pairs are what replicate. h3 drama positions stay at or below chance with every political position. No right-leaning pattern passed, so a right-leaning bundle couldn't appear.

**4. Gaza link inside the Palestine subs: missed.** Among 187 position-taking accounts whose home is r/Palestine or r/IsraelPalestine, 161 used genocide language, so co-occurring with anti_zionist is no longer beyond chance (7 observed vs 6.9 expected, z 0.1). The link is real across the whole population but saturates where nearly everyone holds the position.

**5. Hostile crossings: untestable for Conservative, reversed for IsraelPalestine.** r/Conservative limits most threads to flaired users, and left-leaning regulars wrote 3 comments there all week. In r/IsraelPalestine, visitors whose home is r/Palestine had 52% of comments at 0 or below against 16% for locals (21 comments, small). The established hostile crossing replicated: Hasan regulars in r/h3h3productions at 34% vs 10% for locals (280 comments; 33% on Oct 13–26), and LeftoversH3 regulars there fare almost as badly (29%, 1,027 comments).

Coordination checks: 0 seeder-to-amplifier pairs across 3+ threads.

## Trump sentiment by sub (blind stance coding)

216 Trump mentions (40 per sub, all 16 in Asmongold), coded blind with the sentiment rubric, sub hidden until coding finished. Predictions were written beforehand. A second coder, given only the rubric and 50 random items (23%), agreed on 88% with Cohen's kappa 0.78 against the corrected codes (84%, kappa 0.72 against the original ones). Four of the six disagreements were comments about the Trump administration or campaign (installed loyalists, a gerrymandering push, Hegseth, campaign prosecutions) that the first coder counted as A and the second as N. The first coder's 'against' shares may run a few points high; no conclusion depends on it. Next rubric: the administration's own actions count as judging Trump; his supporters' and allies' actions don't.

| Sub | Side-takers | For | Against | Net (predicted) |
| --- | --- | --- | --- | --- |
| Conservative | 21 | 57% | 33% | +24 (+40) |
| Asmongold | 6 | 67% | 33% | +33 (+20) |
| PoliticalCompassMemes | 19 | 5% | 95% | −89 (−10) |
| dsa | 10 | 0% | 90% | −90 (−85) |
| neoliberal | 18 | 0% | 100% | −100 (−80) |
| thebulwark | 29 | 0% | 100% | −100 (−90) |

Correction after unblinding: six comments criticizing MAGA as a movement without judging Trump were coded A, against the rubric's rule for fans and movements. Recoded to N through a corrections file: Conservative moves from +24 (21 side-takers) to +30 (20), dsa from −90 (10) to −88 (8), thebulwark keeps −100 on 26 side-takers instead of 29. No conclusion changes.

Every cell is under 30 side-takers. The PCM result is the clear miss: its 95% interval for favorable runs 1–25%, far from the mixed sub expected. In r/Conservative the critical comments scored higher (median 5) than the favorable ones (median −1), on 7 and 12 comments.

## Next

Draft fixes for the failing patterns are in `socialscope/positions_v2_drafts.py` (negations for hila_pos, Hasan-hater mockery for hasan_neg, capitalized ICE, no bare "tankie"). They replace nothing until a fresh blind read on other weeks passes them. September baseline weeks (Sep 8–14, Sep 22–28) will show which of this week's results come from the Ethan story and which are structural.

## Limits

Twelve-item accuracy reads carry wide intervals (about ±25 points). Home sub is the sub, among the 19 with data, where an account comments most, so history accounts' homes lean toward the drama subs they were sampled from. Scores are first-save snapshots.

# September baseline: is the Ethan week typical? (scored Oct 30, 2026)

Two quiet weeks, Sep 8–14 and Sep 22–28, all comments in the same 18 subs (complete hourly coverage), run with the same code and the frozen tier 1 pattern rule, against Oct 20–26. Predictions were committed before the data was opened (`docs/september-baseline-predictions.md`). Pair z-scores combine each week with the same 2,378 account histories, so they share part of their data across weeks.

| Measure | Oct 20–26 | Sep 8–14 | Sep 22–28 |
| --- | --- | --- | --- |
| r/LeftoversH3 comments | 67,110 | 10,519 | 11,451 |
| r/h3h3productions comments | 184,187 | 10,754 | 8,296 |
| r/LivestreamFail comments | 64,216 | 25,702 | 25,847 |
| Drama regulars' share of r/thedavidpakmanshow | 24.2% | 26.3% | 18.6% |
| … of r/dsa | 17.7% | 5.9% | 5.1% |
| … of r/samharris | 11.1% | 7.6% | 8.2% |
| … of r/LeftoversH3 | 17.0% | 9.5% | 13.7% |
| Hasan regulars' comments in r/h3h3productions | 280 (34% at or below 0) | 12 | 2 |
| Position comments carried across subs | 6.7% | 8.5% | 7.5% |
| anti_trump + anti_ice (z) | 6.6 | 3.4 | 3.2 |
| gaza_genocide + anti_tankie | 5.7 | 1.2 | 1.6 |
| hasan_neg + anti_tankie | 5.5 | 2.1 | 2.7 |
| gaza_genocide + anti_zionist | 5.1 | 3.6 | 4.0 |

1. Volume collapses in quiet weeks: **held.** LeftoversH3 runs at a sixth of the Ethan week, r/h3h3productions at a twentieth.
2. Overlap into politics subs is structural: **partly.** r/thedavidpakmanshow's Destiny-regular overlap holds in every week (19–26%), so it's structural. r/dsa's 18% was the event: 5–6% in September. r/samharris sits at 8% in quiet weeks, just around the bar.
3. LeftoversH3's regular share falls below 12%: **split**, 9.5% and 13.7%.
4. Hasan-to-h3 hostile crossing: **untestable.** Hasan regulars barely comment in r/h3h3productions outside drama weeks (12 and 2 comments). The crossing is real but happens only when the drama brings them there.
5. All four links above z = 2 each week: **missed for one.** Three hold in every week. gaza_genocide + anti_tankie falls to 1.2 and 1.6: its Oct strength came from the drama week's Hasan and Gaza arguments.
6. Carried positions under 6%: **missed**, 7.5–8.5% (and 6.7% in the Oct week measured the same way, which also counts history rows posted in the 18 subs; the earlier 4% covered the five drama subs only).

**What this changes:** the three political bundles are real, but their tightness in the Oct write-up was inflated by the drama week. Read single-week bundle results as a mix of structure and event. The pakman overlap belongs in the structure column; the dsa overlap and the gaza + anti_tankie link belong in the event column.

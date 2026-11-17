# Ukraine/Palestine framing asymmetry by community: results

Run Nov 17, 2026, against `ukraine-palestine-asymmetry-predictions.md` (commit 87a5283, written before any data was
pulled). The method is `scripts/asymmetry.py` as committed with the predictions. The later change in 8b92d03 only
lets each community be pulled in its own process; it changes nothing about what is pulled or measured. Counts are in
`data/antiwest/asymmetry_by_sub.csv`.

**Outcome: MOVE-11 is not adopted.** Adoption condition (a) fails. Conditions (b) and (c) fail too. Of the eleven
predictions, 4 hold, 6 miss and 1 could not be tested.

## Data

- **Source.** Arctic Shift comment search, Oct 1 to Nov 15 2026. There were 12 searches per community, merged by
  comment id. AutoModerator, [deleted] authors, short bodies and removed bodies were dropped. Author names were never
  written to disk.
- **AutoModerator.** In r/Hasan_Piker, 4,058 of 4,321 raw hits for "gaza" were AutoModerator. They were dropped as
  the predictions specified.
- **Pull method.** Pulling in parallel made the API throttle harder, so the communities were pulled one at a time.
- **No index for two communities.** r/Palestine had only 5 framed Ukraine comments. r/ukraine had 0 framed Palestine
  comments. Both are below the 30-comment minimum, so neither has an index.

| community | comments | Us | Uj | Ps | Pj | Ukraine settle share | Palestine justice share | A | 95% CI |
|---|---|---|---|---|---|---|---|---|---|
| Conservative | 1,838 | 147 | 24 | 42 | 30 | 0.86 | 0.42 | **1.46** | 0.92 to 2.10 |
| socialism | 867 | 16 | 35 | 10 | 70 | 0.31 | 0.88 | **1.14** | 0.36 to 2.03 |
| TankieTheDeprogram | 2,152 | 61 | 91 | 32 | 124 | 0.40 | 0.80 | **0.95** | 0.51 to 1.44 |
| dsa | 1,529 | 73 | 70 | 57 | 128 | 0.51 | 0.69 | **0.85** | 0.46 to 1.24 |
| neoliberal | 12,806 | 469 | 252 | 251 | 267 | 0.65 | 0.52 | **0.68** | 0.47 to 0.90 |
| Hasan_Piker | 3,843 | 20 | 32 | 106 | 307 | 0.38 | 0.74 | **0.60** | 0.04 to 1.11 |
| Destiny | 13,939 | 281 | 208 | 313 | 343 | 0.58 | 0.52 | **0.39** | 0.16 to 0.60 |
| Palestine | 3,622 | 0 | 5 | 126 | 515 | — | 0.80 | too few | |
| ukraine | 15,727 | 821 | 388 | 0 | 0 | 0.68 | — | too few | |

Us = Ukraine+settlement, Uj = Ukraine+justice, Ps = Palestine+settlement, Pj = Palestine+justice.

Every community with an index has A above 0. In every community the word counts lean the same way: toward settlement
for Ukraine and toward justice for Palestine. The blind read below shows why.

## Predictions

| # | prediction | result | outcome |
|---|---|---|---|
| 1 | TankieTheDeprogram has the highest A | 3rd, below Conservative (1.46) and socialism (1.14) | **miss** |
| 2 | Tankie A > 0, CI excludes 0 | 0.95, CI 0.51 to 1.44 | holds |
| 3 | bottom three are ukraine, neoliberal, Destiny | ukraine has no index; the bottom three measured are Destiny, Hasan_Piker, neoliberal | **miss** |
| 4 | Hasan_Piker and dsa below Tankie, above neoliberal | dsa yes (0.85); Hasan_Piker no (0.60, below neoliberal) | **miss** |
| 5 | Conservative in top three | 1st | holds |
| 6 | Palestine below Hasan_Piker | Palestine has no index | untestable |
| 7 | Spearman ≥ 0.6 with the predicted order | 0.57 over the 7 communities with an index | **miss** (narrowly) |
| 8 | Tankie: Ukraine settle share > .5 and Palestine justice share > .5; ukraine: Ukraine settle share < .5 | Tankie 0.40 and 0.80; ukraine 0.68 | **miss** (2 of 3 parts fail) |
| 9 | Ukraine+settlement precision 50–75%, both coders | 20% and 18% | **miss** |
| 10 | Palestine+justice precision 60–85%, both coders | 65% and 63% | holds |
| 11 | coder agreement ≥ 70% | 104/120 = 87% | holds |

Prediction 7: the predicted order, restricted to the seven communities with an index, was Tankie, Conservative,
Hasan_Piker, socialism, dsa, Destiny, neoliberal. The observed order was Conservative, socialism, Tankie, dsa,
neoliberal, Hasan_Piker, Destiny. Σd² = 24, so ρ = 1 − 144/336 = 0.57.

## Blind read

- **Sample and coders.** 60 items per half, drawn evenly across communities, community hidden. The coders were
  claude-opus-5-5 (A) and claude-fable-5-2 (B), each working alone from `coder_brief.md`.
- **What is kept.** Labels and the key stay in the data folder. Neither is committed.

| half | coder | endorse | precision | Wilson 95% | oppose/mock | report | other sense | unclear |
|---|---|---|---|---|---|---|---|---|
| Ukraine+settlement | A | 12/60 | 20% | 12–32% | 20 | 10 | 12 | 6 |
| Ukraine+settlement | B | 11/60 | 18% | 11–30% | 20 | 15 | 11 | 3 |
| Palestine+justice | A | 39/60 | 65% | 52–76% | 9 | 3 | 8 | 1 |
| Palestine+justice | B | 38/60 | 63% | 51–74% | 8 | 6 | 8 | 0 |

**Endorse counts by community** (coder A / coder B, out of 7–8 items each):

| community | Ukraine+settlement | Palestine+justice |
|---|---|---|
| TankieTheDeprogram | 1 / 1 | 8 / 7 |
| socialism | 2 / 2 | 7 / 7 |
| dsa | 2 / 2 | 7 / 6 |
| Hasan_Piker | 4 / 4 | 7 / 6 |
| Palestine | — | 7 / 7 |
| Conservative | 2 / 1 | 0 / 0 |
| Destiny | 0 / 0 | 1 / 2 |
| neoliberal | 0 / 0 | 2 / 3 |
| ukraine | 1 / 1 | — |

These cells are small (7–8 items). Read them as direction only.

## What this shows

1. **The Ukraine half does not work as a word count.** In these six weeks, "peace", "negotiations" and "ceasefire"
   near Ukraine are mostly about a peace process in the news. Commenters criticize it, report on it or mock it far
   more often than they ask for it. Only 1 of 8 sampled TankieTheDeprogram comments endorsed settlement for Ukraine.
   So Ukraine+settlement counts measure how much a community discusses the peace process, not campist advocacy.
   That is why r/ukraine, r/neoliberal and r/Destiny score high on Ukraine settlement share, against prediction 8.
2. **The Palestine half separates communities, but by side, not by campism.** Justice language near Palestine is
   endorsed in nearly every sampled comment from the left and pro-Palestine communities (including r/Palestine). It
   is endorsed in almost none from Conservative, Destiny or neoliberal, where "free Palestine" and "intifada" are
   mostly quoted or mocked. Agreement on this half was high. This marks a pro-Palestine position. It does not mark
   the double standard the move describes.
3. **Conservative ranks first for a different reason.** Its A is high because it discusses Ukraine settlement a lot
   (0.86 share) and uses little justice language about Palestine at all. That is the CAMP/RIGHT overlap the
   predictions anticipated, but the blind read shows its Ukraine settlement comments are not mostly endorsements
   either (2/7 and 1/7).
4. **The video claim is not refuted.** The claim (T2) is about one speaker holding both positions. This test measured
   communities by keyword. The keyword version fails for the reason above. A test of the move as described would
   need comment-level coding of stance on both wars by the same speaker in the same thread. That would be a new
   design with its own predictions file, not a fix to this one.

## Decision (by the rule written in advance)

- **(a) fails:** Tankie's A is not the highest.
- **(b) fails:** Tankie's CI overlaps Destiny's (0.16 to 0.60) and neoliberal's (0.47 to 0.90). r/ukraine has no
  index.
- **(c) fails:** the Ukraine half's Wilson lower bounds are 12% and 11%, and the Palestine half's are 52% and 51%. All
  four are below 65%.
- **Result:** MOVE-11 is not added to `rhetorical_moves.csv` or the skill. The analysis table in
  `docs/antiwest-vod-analysis.md` now points here.

## Exploratory (not predicted; do not cite as a finding)

- **Top settlement words for Ukraine.** "Peace" is the top word in every community. Next are ceasefire, negotiation
  and diplomatic/diplomacy (r/ukraine: peace 337, negotiation 100, ceasefire 85).
- **Top justice words for Palestine.** "Free Palestine" is the top term in r/Palestine (418), r/Destiny (100) and
  r/Conservative (17). "Resistance" is the top term in TankieTheDeprogram (54) and Hasan_Piker (86).
- **Possible v2.** If tested, it would need its own predictions file and a stance-coded sample (endorse only) rather
  than keyword counts.

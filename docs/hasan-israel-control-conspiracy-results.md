# Israel/Jewish control conspiracy in chat, and its timing against Hasan's speech, Nov 3-10 2026: results

Predictions: `hasan-israel-control-conspiracy-predictions.md` (commit 09102e9, Nov 12 13:53 ET, before coding). Run
Nov 12 on the laptop; script and per-item codes in `~/socialscope_data/as_coding/cc_*` (not committed). Chat results
are aggregates only. Hasan's own lines are quoted because the question is about his public on-stream speech.

## Data
| | DGG | Hasan |
|---|---|---|
| on-topic non-candidate messages not coded before | 1,777 | 7,412 |
| random sample coded | 600 | 600 |
| Hasan transcript turns mentioning Israel/Zionism/AIPAC/IDF/Netanyahu/Gaza/Jews/lobby | | 559 |

Coders: `claude-opus-5-5` effort low and `claude-fable-5-2` effort high, batch API. All 3,518 requests succeeded, no
refusals. Actual cost **$25.99** (Opus chat $4.13, speech $1.34; Fable chat $13.98, speech $6.54), above the $15-20
estimate: Fable's high-effort outputs were longer than in the first run.

Transcripts are Whisper output (e.g. "Benjamin and Yao" = Netanyahu); 7 of 336 Opus speech quotes were not verbatim,
all of Fable's were.

## Scoring
| # | Prediction | Opus 5.5 | Fable 5.2 |
|---|---|---|---|
| 1 | Endorsed control + dual-loyalty ≥2x as common in Hasan chat as DGG | **hit**: 3.67% vs 0.67% (5.5x) | **hit**: 2.0% vs 0.5% (4x) |
| 2 | Hasan chat level 1-5% of on-topic | **hit**: 3.67% (CI 2.4-5.5) | **hit**: 2.0% (CI 1.2-3.5) |
| 3 | In Hasan chat, lobbying criticism > endorsed conspiracy | **hit**: 32 vs 22 | **hit**: 34 vs 12 |
| 4 | Hasan's lobbying turns ≥3x his endorsed conspiracy turns, and <10 such turns | **miss**: 47 vs 20 (2.4x), 20 turns | **miss**: 73 vs 16 (4.6x), 16 turns |
| 5 | Chat within 120 s after Hasan lobbying/conspiracy turns ≥1.5x as likely to be conspiracy | **hit**: 6.1% vs 3.3% (1.9x; 5 of 82) | **miss**: 1.9% vs 2.0% (2 of 106) |
| 6 | Coders agree on israel_claim for ≥75% of chat items | **hit**: 90.8% (kappa 0.73; kappa on conspiracy-vs-not 0.43) | |

Opus 4 of 5, Fable 3 of 5; pair 1 of 1.

Caveat on 3: stance codes antisemitic content, so plain lobbying criticism is coded not_applicable, not endorse. It is
scored on lobbying_criticism claims of any stance, which is what was meant; the prediction's wording was loose.

## What it shows
- **Hasan chat has several times DGG's rate of sincere control / dual-loyalty talk.** 2.0-3.7% of on-topic Hasan
  messages vs 0.5-0.7% in DGG, a 4-5.5x gap the two models agree on and the intervals do not overlap for Opus. Scaled
  to the week: about 155-285 such messages in Hasan chat (range 89-426) vs 10-14 in DGG (3-35). This replicates the
  first run (2.4-3.2%) on a fresh sample of 600.
- **DGG's version is mostly ironic; Hasan chat's is not.** Of DGG's few control/dual-loyalty claims, most were coded
  joke_or_bait, report or unclear (3-4 of 17-20 endorse); in Hasan chat, 12-22 of 30-47 such claims were endorse,
  with almost no joking (2-4). Lobbying criticism is still
  the more common Israel claim in Hasan chat (32-34 messages).
- **Hasan himself uses the dual-loyalty framing often, mostly at non-Jewish politicians.** 16-20 of his 559 turns are
  endorsed dual_loyalty or control claims, mainly "Israel first" about Trump, Haley Stevens, Fetterman and "Israel
  First liberals", "servile to Israel", "an asset for Israel". The models split on whether that is antisemitic: Opus
  flags 13 turns as JDA-antisemitic, Fable 4. The JDA is aimed at charges against Jews and the Jewish-control trope;
  "Israel first" said of a non-Jewish politician's foreign policy is a gray area under it (and antisemitic under IHRA's
  dual-loyalty example only when aimed at Jews).
- **A few of his lines are the stronger form** that both definitions treat as antisemitic (Opus codes; Fable coded
  several of these not_applicable or other criticism):
  - "Democrats can't be alienated from Zionism because the Zionists formed the backbone of the Democratic Party."
    (v2919551106, 5:57:16)
  - "a completely concocted media narrative, uh, directed by the Zionist lobby" (v2919551106, 3:52:23)
  - "The Foundation for Defending Democracies is literally an Israeli Mossad operation" (v2920436679, 6:23:03)
  - "a jewish asset of israel and the cia who also happen to be a massive pedophile" (v2922383001, 3:19:46)
  - "his endless loyalties at the State of Israel" (v2923403101, 2:51:39)
- **No clear sign that chat's conspiracy talk follows his.** Opus finds 1.9x more in the 2 minutes after his
  lobbying/conspiracy turns, Fable finds none; 2-5 messages in the window is too few to tell. The chat rate is
  roughly the same whether or not he has just spoken on it.
- **Coders agree on the claim type (91%) but less on which are conspiracy (kappa 0.43).** Fable is stricter: it
  codes more Hasan-chat dual-loyalty/control claims not_applicable (29) and calls fewer of Hasan's turns antisemitic.

## Limits
- A week of streams, model coders only. Twitch AutoMod and mod deletions remove some chat before it is logged.
- The timing test has too few messages in the window; a full-week coding of all 7,412 on-topic messages would fix it.
- Next: blind hand-check of ~100 items (disagreements oversampled), including the 20 Hasan turns above.

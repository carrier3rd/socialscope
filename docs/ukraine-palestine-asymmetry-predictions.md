# Ukraine/Palestine framing asymmetry by community: predictions

Written Nov 16, 2026, before any comment from the sample was pulled or read. Never edit; addenda go at the end.
Results go in `ukraine-palestine-asymmetry-results.md`. The method is frozen in `scripts/asymmetry.py`, committed
with this file.

**The claim.** Destiny and his guests say campists ask for "peace", "negotiations" and "more diplomats" for Ukraine,
and for "liberation", "an end to the occupation" and "resistance" for Palestine (`docs/antiwest-vod-analysis.md`, T2:
YHc1nsVqxkI 02:00:14 and 02:21:58, KXslvrBBCyo 01:54:33 and 02:06:52). It follows from selective anti-imperialism
(MOVE-05), the one video test the research supports well. If it holds, it becomes candidate MOVE-11.

**What I have already seen:**
- the 296 indexed video passages;
- the earlier project write-ups (`docs/opinion-bundles.md`, `docs/glossary.md`), including the Oct gaza_genocide +
  anti_tankie link;
- the file names in the Google Drive pull folders.

I have read no comment from these communities in this window, and no result on framing by war.

## Data

- **Source.** Arctic Shift comments search, 2026-10-01 to 2026-11-15 inclusive.
- **Communities.** TankieTheDeprogram, Hasan_Piker, dsa, socialism, Palestine, Conservative, Destiny, neoliberal,
  ukraine.
- **Search terms** (one search per term, merged by comment id): ukraine, ukrainian, russia, putin, zelensky, kyiv,
  gaza, palestine, palestinian, israel, west bank, hamas.
- **Dropped:** AutoModerator and [deleted] authors, bodies under 20 characters, removed bodies, quoted lines.
- **No accounts.** Author names are dropped as the pull is written. Nothing is computed per account.

## Measure

These rules are in `frames()` in the script.

- **War mentions.** UKR = Ukraine, Kyiv, Zelensky, Donbas, Donetsk, Luhansk, Crimea, Putin, Russia, Kremlin.
  PAL = Gaza, Palestin*, West Bank, Israel*, IDF, Hamas, Netanyahu, Bibi.
- **Frames:**
  - *settlement*: peace, negotiat*, diplomacy, ceasefire, armistice, de-escalation, truce, compromise, concessions,
    "stop sending/funding/arming", "end/stop the war";
  - *justice*: liberat*, occupation/occupied/occupier, resistance/resist, self-determination, decoloni*, "free
    Palestine/Ukraine", (anti)colonial, sovereign*, victory, "win the war", intifada, "armed struggle", "take back".
- **Which war a frame belongs to.** A frame counts for a war when it is in a sentence that names that war and not the
  other. A sentence that names neither war counts only if the whole comment names exactly one war. Sentences naming
  both wars are skipped.
- **Ceasefire.** It counts as settlement for both wars. A community that asks for a ceasefire in Gaza and for peace
  talks in Ukraine is symmetric by this measure, which is what the claim implies.
- **Counts per community:** comments with Ukraine+settlement (Us), Ukraine+justice (Uj), Palestine+settlement (Ps),
  Palestine+justice (Pj).
- **Asymmetry index** A = ln((Pj+.5)/(Ps+.5)) - ln((Uj+.5)/(Us+.5)), with a 95% bootstrap interval (1,000 resamples
  of comments, seed fixed). Positive means Palestine is framed toward justice, relative to settlement, more than
  Ukraine is.
- **Minimum data.** A community gets an index only with at least 30 framed comments for each war.

## Predictions

1. **TankieTheDeprogram has the highest A** of all communities with enough data.
2. Its A is above 0, with the 95% interval excluding 0.
3. **The bottom three** are ukraine, neoliberal and Destiny, in any order.
4. Hasan_Piker and dsa each fall below TankieTheDeprogram and above neoliberal.
5. **Conservative ranks in the top three.** The isolationist right uses the same settlement language for Ukraine
   (the CAMP/RIGHT overlap in the lexicon), and rarely uses justice language for Palestine. That cuts both terms of
   the index the same way.
6. Palestine ranks below Hasan_Piker. My guess is that the pro-Palestine public uses justice language for Ukraine too
   ("Ukrainians get to resist").
7. **Full order.** Spearman correlation of at least 0.6 between the observed order and this one: TankieTheDeprogram,
   Conservative, Hasan_Piker, socialism, dsa, Palestine, Destiny, neoliberal, ukraine.
8. **Both halves in the core.** In TankieTheDeprogram, settlement is more than half of framed Ukraine comments, and
   justice is more than half of framed Palestine comments. In ukraine, settlement is less than half of framed
   Ukraine comments.

## Blind read

- **Sample.** 60 random comments from each half of the move (Ukraine+settlement and Palestine+justice), drawn
  evenly across communities, shuffled, community hidden.
- **Coders.** Two independent Claude coders, claude-opus-5-5 and claude-fable-5-2, each with the same instructions.
  Each item shows the war and the frame.
- **Labels:**
  - **endorse**: the author advocates that framing for that war;
  - **oppose_or_mock**: argues against it, mocks it, or negates it (e.g. "Hamas is not resistance");
  - **report**: neutral description or news;
  - **other_sense**: the word means something else, or is not about that war;
  - **unclear**.
- **Precision** = share labelled endorse, per coder, with a Wilson 95% interval.

9. Ukraine+settlement precision is between 50% and 75% for both coders. "Negotiations" is also news vocabulary.
10. Palestine+justice precision is between 60% and 85% for both coders.
11. The coders agree on the label for at least 70% of items.

## What counts as passing (decided now)

MOVE-11 goes into `data/antiwest/rhetorical_moves.csv` and `skills/antiwest-lexicon/SKILL.md`, with its measured
numbers, only if all three hold:

- (a) prediction 1 holds;
- (b) TankieTheDeprogram's A exceeds the A of ukraine, neoliberal and Destiny, with 95% intervals that do not overlap
  any of the three;
- (c) for **both** halves and **both** coders, the Wilson lower bound on precision is at least 65%. This is the
  project's opinion-pattern bar, applied "with confidence" as in `docs/opinion-bundles.md`.

**Partial outcomes:**
- If (a) and (b) hold but (c) fails, the result is reported as a community-level signal only. MOVE-11 is not used to
  code single comments, and the skill says so.
- If Conservative's A is at least TankieTheDeprogram's, MOVE-11 is adopted, if at all, with factions "CAMP RIGHT" and a
  caution that it does not separate the campist left from the isolationist right.
- If (a) fails, MOVE-11 is not adopted. The result and the misses still go in the results file.

## Not changed by later work

More of Destiny's videos are being transcribed and indexed in parallel for vocabulary, dog whistles and "mask on"
entry points. Nothing from that work changes the term lists, the communities or the metric above. Any new terms get
their own predictions file.

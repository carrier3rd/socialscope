# Israel/Jewish control conspiracy in chat, and its timing against Hasan's speech, Nov 3-10 2026: predictions

Written Nov 12, 2026, before the new sample or any transcript turn was coded. Never edit; addenda go at the end.
Results: `hasan-israel-control-conspiracy-results.md`. Follows `dgg-hasan-antisemitism-coding-results.md`.

What I have already seen: those results, including the endorsed Hasan-chat items (dual loyalty, "Israel controls US
officials", Holocaust inversion) and the 250-per-side on-topic samples. I have read no transcript turns for this.

## Data and method
- **Chat:** a fresh random sample of 600 on-topic (topic_jews / topic_israel) non-candidate messages per side, excluding
  the 250 already coded; same masking and context as before; Hasan items keep video id and stream time.
- **Hasan's speech:** every Hasan-labelled transcript turn in the 8 streams that mentions Israel, Zionism, AIPAC, IDF,
  Netanyahu, Gaza, Jews, dual loyalty or lobbying (547 turns), with the turn before and after as context.
- **Coders:** claude-opus-5-5 (effort low) and claude-fable-5-2 (effort high), same prompt per unit type.
- **New field `israel_claim`:** control_conspiracy (Israel, Zionists or Jews secretly control or own US government,
  military, media or finance, or "placed" officials) / dual_loyalty (US officials or citizens serve Israel over the
  US, "Israel-firster", "agent of Israel") / lobbying_criticism (criticism of documented lobbying, donations or
  influence, e.g. AIPAC spending) / other_israel_criticism / none. Stance as before; only endorse counts.
- **Timing:** Hasan chat messages within 120 s after a Hasan turn coded lobbying_criticism, control_conspiracy or
  dual_loyalty (any stance) vs other on-topic messages.

## Predictions (each model scored separately)
1. **Rate.** Endorsed control_conspiracy + dual_loyalty is at least 2x as common, as a share of on-topic messages, in
   Hasan chat as in DGG.
2. **Hasan chat level.** It is between 1% and 5% of Hasan's on-topic messages.
3. **Lobbying vs conspiracy.** In Hasan chat, endorsed lobbying_criticism outnumbers endorsed control_conspiracy +
   dual_loyalty.
4. **Hasan himself.** Hasan's turns coded lobbying_criticism outnumber those coded control_conspiracy + dual_loyalty
   (endorse) by at least 3 to 1, and fewer than 10 of his turns are endorse control_conspiracy or dual_loyalty.
5. **Timing.** Chat messages in the 120 s after a Hasan lobbying/control/dual-loyalty turn are at least 1.5x as likely
   to be endorsed control_conspiracy + dual_loyalty as other on-topic chat messages.
6. **Coders.** Opus and Fable agree on israel_claim for at least 75% of chat items.

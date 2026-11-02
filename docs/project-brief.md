# socialscope: project brief (updated Nov 2, 2026)

Joseph's project on bots, brigading and opinion crossover in Reddit drama and political subs (18 subs: Asmongold,
Conservative, Destiny, Hasan_Piker, IsraelPalestine, LeftoversH3, LivestreamFail, Palestine, PoliticalCompassMemes,
TankieTheDeprogram, atrioc, dsa, h3h3productions, neoliberal, samharris, thebulwark, thedavidpakmanshow, ukraine).
Repo: carrier3rd/socialscope (private). Detail lives in docs/; this page is the map.

## Standing rules
- **Usernames:** never print or commit them. User lists stay private, and outputs are hashed with the project salt.
- **Naming bots:** call an account a bot only if Bot Bouncer banned it, or it reached the high tier with evidence.
  Scores are leads, not proof.
- **Predictions first:** write them down and commit them before looking at any data. Then score them honestly,
  misses included.
- **Effort level:** say so when a task needs a higher model or effort level.

## What's established
- **Bot detection (docs/insub-training-predictions.md, bot-calibration-study.md):**
  - **Gradient-boosting model:** trained on accounts active in our subs. On fresh Bot Bouncer bans it catches 67% at 1%
    false alarms (AUC 0.97), about 40% precision at a 1% bot rate. It still gets 57% without the volume features, and
    62% against size-matched controls.
  - **Age rule alone:** 33% at 5% false alarms.
  - **Hijack signature:** most in-sub bans (62%) are aged accounts that suddenly turn to new subs and NSFW
    solicitation. solicit_broad catches 75% of aged bans, at 6% false alarms.
  - **Pending accounts:** in a blind read, 16 of the model's 30 top-scored pending accounts looked like spam or bots,
    against 5 of 30 random ones.
  - **Lesson from the failed sitewide test:** sitewide Bot Bouncer bans are throwaway accounts, so positives and
    controls must come from the same population.
- **Opinion maps (docs/opinion-pooled-predictions.md):**
  - **Trump:** 95-100% against in every sub except Conservative, which is 73% for.
  - **Hasan:** the majority is against him in Destiny, neoliberal, samharris and PCM. Pakman and dsa are split.
  - **Israel:** over 90% against in Palestine, Tankie, dsa and Hasan_Piker.
  - **Ukraine:** strongly for in neoliberal, bulwark, ukraine, Destiny and pakman. Against is the majority in Tankie,
    Hasan_Piker and Palestine.
  - **Coder agreement:** kappa 0.70 between me and Gemini. My codes lean slightly toward "against."
- **America framing:** in the four left subs, about 28-39% of comments that take a stance treat America as bad in
  itself (two coders). This is concentrated in Tankie (55-67%) and Hasan (36-45%). It is rare in dsa (12-14%), and the
  rest is criticism of specific policies.
- **Crossover:** Destiny regulars are the biggest outside group in pakman every week. Hostile crossings run into the h3
  subs and into neoliberal. Pakman and atrioc are the most open subs.
- **Glossary:** docs/glossary.md and data/glossary.csv, 56 community marker terms.

## Void or pending
- **Talking-point direction (v1, exact 8-word matching):** VOID. Gemini's labels showed most clusters were stock
  phrases. The rebuild, v2 with embeddings (MiniLM-L6, docs/talking-points-v2-predictions.md), is running on the laptop.
  Its sample goes to Gemini for labeling.
- **Forward test (docs/forward-test-predictions.md):** frozen model, 2,000 unlisted in-sub accounts. Histories are
  pulling now. A scheduled check runs Dec 1 and needs a Bot Bouncer pull for Nov 3-30 first.
- **Commentator study (docs/commentator-valence-predictions.md):** tests whether "America is bad" framing comes from
  streamers. Transcripts are downloading (HasanAbi done, 86 videos). Then scripts/transcript_chunks.py, Gemini coding,
  and quote checking with `verify`.
- **Oct 27 week:** a top-up rerun is due after Nov 3, for Nov 2 and thebulwark comments.

## How work gets done
- **Pulls:** Arctic Shift works only from the laptop (Claude Code) or Colab, not from this workspace.
  - **Weekly subs:** scripts/reddit_pull.py with --keep-jsonl.
  - **User histories:** arctic.pull_user_histories(...), max_items 1000, with oldest dates.
- **Laptop:** jobs run under nohup with a sleep inhibitor. ~/socialscope_data/STATUS.txt shows progress (status.sh),
  and asking "status?" makes Claude read it. The laptop has a CPU only.
- **Gemini:** use it for blind labeling of pasted text, which works (kappa 0.48-0.70). Don't use it to find or watch
  videos or to look things up, because it invents details. Explicit NSFW text gets refused. Every quote it returns gets
  checked by script.
- **Hugging Face:** this workspace can't reach it, so embedding models run on the laptop.

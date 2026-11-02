# In-sub training set, rebuilt: design and predictions (written Nov 2, 2026, 5:50 AM ET, before the pull)

Why: the Nov 1 training set drew bans from all Bot Bouncer listings across Reddit. Only 8 of 989 had ever posted in our
18 subs, so it compared throwaway accounts with our regulars (docs/bot-calibration-study.md, Nov 2 entry).

Pool: every account seen in our six pulled weeks (Aug 18, Sep 8, Sep 22, Oct 13, Oct 20, Oct 27; 194,727 accounts,
posts and comments) that also appears in the Bot Bouncer inventory (latest listings through Oct 28).
- **Train positives:** the 201 banned accounts already used in earlier rounds, panels and audits. Their histories are
  already pulled.
- **Test positives (fresh, never examined):** 190 accounts banned as of Oct 28. Also any of 290 more fresh listed
  accounts (264 pending, 22 unflaired, 4 purged as of Oct 28) whose latest verdict is "banned" in a new Bot Bouncer pull
  through Nov 3. All 480 are being pulled now (full histories, up to 1,000 items, oldest dates).
- **Controls:** the 1,000 random in-sub accounts from the Nov 1 pull, split by hash parity into train and test halves.
  The train half also gets the earlier in-sub controls: August panel, September test, round 4.
- **Cut:** each history is cut at the listing date for positives and at last activity for controls, as before.

Frozen before the pull: socialscope/hijack.py (unchanged since Nov 1) and the v7.1 scorer. The classifier will be
retrained on the train side only, with the same feature set as the Nov 2 run, and the test side opened once.

Predictions, scored on the fresh test positives vs. the test half of controls:
1. 45-70% of test positives are aged (100+ items over 1+ year). This should be far above the 4% among sitewide bans.
2. solicit_handle (cut at listing) fires for 25-50% of aged test positives, at 1.5-3% of controls.
3. solicit_broad fires for 50-75% of aged test positives, at 4-7% of controls.
4. The v7.1 primary tier catches 20-35% of test positives at 4-6% of controls, in line with the earlier honest in-sub tests.
5. The retrained classifier reaches AUC 0.75-0.88 and catches 30-50% of test positives at 1% control false alarms.
   That is 23-34% precision at a 1% bot rate.
6. Of the 264 pending, 30-60% are banned in the Nov 3 Bot Bouncer pull.

## Results (scored Nov 2, 2026, ~9:30 AM ET)
Built with scripts/insub_run/ (build, feats, score); every name is hashed.
- **Test positives:** 186 fresh Bot Bouncer bans of accounts seen in our subs.
- **Test controls:** 483, the hash-parity half of the random in-sub accounts, with any Bot Bouncer-listed account
  removed.
- **Pending:** 259 accounts reported separately.
- **Train:** 114 earlier in-sub bans with full histories (the other 87 exist only as comment-only slims and were left
  out) and 2,216 in-sub controls.
- **Cut:** positives and pending at their listing date, controls at last activity.

Scores (95% Wilson intervals):
1. **Held.** 62% (55-69%) of test positives are aged, inside 45-70%. Compare 4% among sitewide bans. 79% of controls are
   aged too, so age alone splits the two groups poorly.
2. **Held on bots, missed narrowly on controls.** solicit_handle fires for 54% (45-63%) of aged positives, inside
   25-50%'s upper reach; it is 37% of all positives. On controls it fires for 2.1% (10/483), at the top edge of 1.5-3%.
3. **Held.** solicit_broad fires for 75% (66-82%) of aged positives, at the top of 50-75%, and 50% of all positives.
   Controls: 6.0%, inside 4-7%.
4. **Held.** The primary tier catches 33% (26-40%) of positives at 4.6% of controls. Primary OR solicit_handle catches
   66% at 6.6%.
5. **Beaten.** Gradient boosting reaches AUC 0.965 and catches 67% (60-74%) of positives at 1% false alarms, about 40%
   precision at a 1% bot rate. The prediction was AUC 0.75-0.88 and 30-50%. Logistic regression gets 53% at 1%.
   - **Confound checks:** without the volume features (item counts), recall is 57% at 1%. Against controls matched to
     the positives' item-count range, it is 62% (52-71%). The top features are new-subreddit share in the 30 days
     before the cut, comment count, solicit_broad, sub spread in the window, and link-share change. That combination
     is the hijack signature: an established account suddenly posting in new places.
6. **Unscorable.** Arctic Shift records a listing's flair at capture, so the Nov pull re-lists none of the 263 pending
   accounts. Their verdicts are unknown. On the model, pending accounts are flagged at 19% at the 1% threshold, between
   bots (67%) and controls (1%), consistent with a mix.

Caveats:
- **Labels:** Bot Bouncer's labels are the ground truth, and the label audit put their noise at 17% or less.
- **Hidden bots:** controls may contain unlisted bots, which would make these numbers conservative.
- **Timing:** positives were mostly listed in Jul-Aug, while controls are October-active.
- **Next test:** a forward test on accounts listed after Nov 2.

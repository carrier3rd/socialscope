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

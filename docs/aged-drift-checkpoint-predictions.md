# aged_drift checkpoint test: design and predictions (written Oct 30, 2026, 4:20 PM ET, before any panel history is pulled)

Question: if accounts were re-checked every two weeks, would aged_drift (frozen in `socialscope/aged.py`, unchanged)
flag bots before Bot Bouncer bans them, and how often would it flag ordinary accounts?

Panel: accounts active Aug 18-24, 2026 in the 18 subs (50,424). Bots: the 32 that Bot Bouncer banned between Aug 25
and Oct 28 (latest verdict, scripts/bb_inventory.py) and that no earlier test or the rule's development data used
(26 more were dropped for that overlap). Ban months: 13 in late August, 12 in September, 7 in October. Controls: 1,000
drawn at random from all active accounts never listed as banned. Full histories, up to 1,000 items.

Checkpoints: Aug 25, Sep 8, Sep 22, Oct 6, Oct 20. At each one, every account is scored using only items posted
before it. A bot counts as caught if aged_drift fires at any checkpoint before its ban date. A control counts as
flagged if it fires at any checkpoint. Intervals 95% Wilson.

Predictions:
1. 55-75% of the 32 bots are aged (100+ items over a year or more) as of the Aug 25 checkpoint.
2. aged_drift catches 25-40% of the bots at some checkpoint before their ban.
3. Per checkpoint, aged_drift flags 4-6% of controls; across all five checkpoints, 10-18% of controls are flagged at
   least once.
4. Among caught bots, most (over half) are first flagged at the last checkpoint before their ban.
5. The v7.1 primary tier at the Aug 25 checkpoint catches 15-30% of the bots and 3-5% of controls.

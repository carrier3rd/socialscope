# Bot Bouncer label audit: aged accounts (Nov 1, 2026)

Predictions: `docs/label-audit-predictions.md`, committed before any card was read.

120 cards, shuffled, group hidden: all 60 aged accounts (100+ items over a year or more) that Bot Bouncer banned among
the September and August test panels, and 60 aged random accounts from the same panels. Each card: totals, top subs,
last-30-day activity, 8 random items from the newest 200 and 4 from the oldest 200. One coder, codes fixed before
unblinding. Intervals 95% Wilson.

| | Bot (inauthentic) | Human | Unclear |
| --- | --- | --- | --- |
| Banned aged accounts (n=60) | 26 = 43% (32-56%) | 30 = 50% (38-62%) | 4 = 7% |
| Random aged accounts (n=60) | 0 = 0% (0-6%) | 57 = 95% (86-98%) | 3 = 5% |

| Prediction | Result | Verdict |
| --- | --- | --- |
| 1. Banned: 35-55% bot, 25-45% human | 43% bot, 50% human | Bot share held; human share above range |
| 2. Random: under 5% bot, over 80% human | 0% and 95% | Held |
| 3. Most bot calls rest on a break in the history, not single items | Every bot call was the same pattern: an ordinary multi-year history, then a burst of sexual-solicitation posts in NSFW subs with a Telegram, Snapchat or Instagram handle, often in stylized Unicode. The break is real, but it was visible through the content of the new posts | Partly held |

**The cards undercount.** Twelve sampled items miss most accounts' spam. Scanning the full pulled histories afterwards
(exploratory, run after unblinding) for two or more posts carrying a contact-handle template, or three or more posts in
NSFW subs:

| | Signature in full history |
| --- | --- |
| Banned, coded bot | 26 of 26 |
| Banned, coded human | 22 of 30 |
| Banned, coded unclear | 2 of 4 |
| Random, coded human | 6 of 57 (NSFW posting by real people; the stricter handle-template test hits 1 of 57) |

So about 50 of the 60 banned aged accounts (83%) show the hijack signature somewhere in their history, and roughly 10
(17%) look like ordinary people on everything pulled. Read that 17% as an upper bound on label noise for this group:
some may be hijacked accounts whose spam was deleted or fell outside the 1,000 items.

## What this changes

1. **Bot Bouncer's aged-account labels are mostly right.** The "aged bots look human" worry from round 4 came from
   reading a few comments; the full history shows what the account was turned into.
2. **The aged bots in these subs are mostly one type:** real accounts taken over or sold and used for NSFW solicitation
   spam, posted to NSFW subreddits while the old owner's comment history sits in the drama and political subs. That
   explains every earlier failure: comment-based rules, timing rules and subreddit-drift rules looked in the wrong place.
3. **A candidate rule follows directly** (not yet tested): two or more submissions with a contact-handle template, or a
   burst of NSFW-sub submissions on an account with an established non-NSFW history. On this sample it separates 83%
   vs 10% (broad) or about 50% vs 2% (handle template only), but it was found on this sample, so it needs a frozen
   fresh test before any weight.
4. For the training set, Bot Bouncer bans can be used as labels for aged accounts with about 17% noise at most, and
   the hand-coded cards here become the first validated slice.

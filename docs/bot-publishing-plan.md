# Publishing bots Bot Bouncer hasn't found: plan (Nov 10, 2026, draft for the user to approve)

Goal: put bots our detector finds, which Bot Bouncer hasn't listed, on the public site, without naming ordinary
people. Rules are in CLAUDE.md rule 5. Nothing here runs until the user approves this plan, and Path 2 publishes
nothing until its bar is frozen in a predictions file and passes its test.

Why two paths: at the strict setting the detector wrongly flags about 2 of every 100 ordinary accounts. With 1 bot
per 100 accounts, only about 27% of flags are real bots (repull-explained.md, chart 2). Raw flags can't be published.
Path 1 adds an independent judge, Bot Bouncer. Path 2 builds a stricter bar of our own and proves it before using it.

## Path 1: feed Bot Bouncer

1. **Candidates.** Accounts the detector flags at the strict setting, from the weekly panel pulls and the in-sub
   scoring, that Bot Bouncer hasn't listed (checked against the latest listing data).
2. **Evidence packet** (laptop, automatic): one private file per account in `~/socialscope_data/botfinds/packets/`.
   It holds:
   - the username and score;
   - which signals fired;
   - the takeover date if there is one;
   - up to 20 bot-period posts (text, subreddit, time);
   - a one-line summary of the earlier history in aggregate (item count, years active, top subs as counts).
   Never committed.
3. **Review** (the user, or the cloud session reading the packets): bot / not bot / unsure, with one line of
   reasons, in `botfinds/review.csv`.
4. **Submit** (the user only): "bot" calls go to Bot Bouncer through its normal Reddit process. Claude prepares the
   text but never posts.
5. **Track** (laptop, weekly): `botfinds/tracker.csv` records each submission's Bot Bouncer status: pending,
   banned, cleared.
6. **Publish:** when an account is banned, it goes on the site under the confirmed-bot rule with "found by
   socialscope". If Bot Bouncer reverses the listing, the account comes off.

Path 1 also measures us. The share of our submissions Bot Bouncer bans is the cleanest outside check on the
detector we have.

## Path 2: our own standard ("suspected bot (socialscope)")

**Proposed strict bar.** To be frozen, with numbers, in `docs/bot-publishing-predictions.md` before any test run.
All four must hold:
1. The detector flags the account at the strict setting.
2. **Hard evidence.** At least one of these:
   - solicitation or contact-handle posts (solicit_handle);
   - an established history that turns to NSFW or solicitation posting (solicit_broad);
   - a takeover break: 50+ earlier items, then most recent posts in subreddits the account never used.
3. **Human read.** A person reads the bot-period posts and judges them templated, solicitation or spam, written
   down with the reason.
4. **Not already decided.** The account isn't banned or cleared by Bot Bouncer, and hasn't been cleared by us
   before.

**Test before anything is published:**
- **Ground truth from Path 1.** Accounts meeting the bar are submitted to Bot Bouncer like any other. The bar
  passes if, among at least 40 that reach a Bot Bouncer decision, 95% or more are banned, with the lower end of
  the 95% range at 85% or above.
- **Caveat.** Bot Bouncer sees our evidence, so it isn't fully independent. It decides on its own reading,
  though, and clears accounts it disagrees with.
- **Blind cross-check.** The reviewer reads a shuffled mix of bar-meeting accounts, banned bots and random
  controls without knowing which is which. The bar's accounts should be judged bot-like about as often as the
  banned bots.

**Once it passes:**
- An account meeting the bar can go up as "suspected bot (socialscope)" while Bot Bouncer is still pending, with
  its bot-period evidence shown and a dispute link.
- A disputed account comes down at the next rebuild while it's re-checked.
- If Bot Bouncer clears more than 10% of published Path 2 accounts in any 30 days, Path 2 stops and all of its
  names come down until a new bar passes a fresh test.

## Decisions for the user

1. Who reviews packets: you, the cloud session, or both (two reads, with disagreements going to "unsure")?
2. The dispute channel on the site: a GitHub issue form on the site repo, or an email address.
3. The Path 2 pass bar: 95% banned with the lower end at 85%, from at least 40 decided accounts, as proposed, or
   stricter?
4. Where candidates come from first: the weekly panels, the in-sub cohort, or both.

## Build order (laptop)

1. Packet builder and private tracker (scripts/botfinds/), reading only data already pulled.
2. Weekly status check against Bot Bouncer listings, added to jobs.tsv and status.sh.
3. Site section for confirmed finds (Path 1), off until the first ban.
4. Path 2 predictions file (bar frozen), then the test. The site section for suspected bots stays off until the
   test passes.

# socialscope

Tools and a working method for studying bots, coordination, misinformation and opinion spread in Reddit communities. They were built and tested on six streamer and drama subreddits (r/LivestreamFail, r/h3h3productions, r/Destiny, r/Hasan_Piker, r/atrioc, r/h3snark) in October 2026. Everything runs on free tools: Arctic Shift for data, Google Colab for pulling, and plain Python for analysis.

It is also packaged as a Claude skill (`SKILL.md`). With the skill installed, Claude can run every step below for you.

**Status:** research in progress. Every flag is a lead for a person to check, never proof. See [What it found](#what-it-found) and the limits in each write-up.

## What's inside

| Path | What it does |
|---|---|
| `notebooks/socialscope_pulls.ipynb` | Colab notebook that pulls data into Google Drive. Works from a phone. |
| `socialscope/arctic.py` | Arctic Shift puller: subreddits by date, full user histories, thread context, topic-matched news threads. Resumes after interruptions and backs off when the server is busy. |
| `socialscope/screen.py` | Stage 1: shortlists accounts worth a closer look, plus random controls and known bots. |
| `socialscope/history.py` | Stage 2: scores full account histories against pre-registered bot rules, reports catch rates, false alarms and precision. |
| `socialscope/claims.py` | Claim checking: finds checkable claims, tracks how rated claims spread, sorts accounts into one-off, one-directional and repeat spreaders. |
| `socialscope/sources.py` | Counts links to state media and state-linked proxy sites. |
| `socialscope/data/kremlin_narratives.csv` | Watchlist of 18 documented Kremlin narratives, each with rating, source, origin and whether it rests on forgeries. |
| `socialscope/bundles.py`, `positions.py` | Opinion bundles: which positions the same accounts hold, who carries them between subreddits, seeder/amplifier pairs. |
| `scripts/` | Command-line versions: coordination networks, brigading tests, blind stance coding, topics, sentiment, calibration. |
| `docs/` | Write-ups of the October 2026 study. |
| `SKILL.md` | Full method, rules and thresholds, written for Claude but readable as a manual. |

## Ground rules

1. Scores are leads. Read the actual posts before saying anything about an account.
2. Usernames stay hashed in every output. Never publish a list of ordinary accounts.
3. Posting in a community is never evidence of anything. Only behavior counts.
4. AI-written text lowers authenticity but never makes an account a bot by itself.
5. No identity work: don't link accounts to real people or across platforms.
6. Lawful data only. No scraping Reddit or X directly.
7. Name an account only if Bot Bouncer confirmed it, or it reached the highest tier with evidence attached.

## Step-by-step guide

### 1. Get the notebook running

1. Open [Google Colab](https://colab.research.google.com), choose File → Upload notebook, and pick `notebooks/socialscope_pulls.ipynb`.
2. Run **cell 1 (Setup)**. Approve the Google Drive popup. Everything saves to `My Drive/reddit_pulls/`.
3. If Colab restarts or sits idle for a long time, run cell 1 again. Every other cell resumes where it stopped.

### 2. Pull a week of subreddits

In **cell 2**, set `subs` (space-separated), `start`, and `end`. `end` is the day after the last day you want; dates are US Eastern. Run it. Each sub produces a posts zip and a comments zip. Big files also get `_slim_` copies small enough to attach on a phone. The SEND THESE list at the end shows which files to use.

To get Bot Bouncer's confirmed bots (the answer key for testing bot rules), put `BotBouncer` in `subs` and choose posts only.

### 3. Shortlist accounts

Run `socialscope.screen.shortlist` on the week's files (or ask Claude to). It writes:

- `users_to_pull.txt`: the shortlist plus an equal number of random controls and any known bots. It contains real usernames, so keep it private.
- `groups.csv`: which group each account is in.

Upload `users_to_pull.txt` to `My Drive/reddit_pulls/`.

### 4. Write your predictions down

Before pulling histories, write down which rules you'll test and what share of bots and controls you expect each to flag. Date it. Don't change a rule after seeing results for that round; change it for the next one. `docs/bot-calibration-study.md` shows the format.

### 5. Pull histories and thread context

- **Cell 3:** set `users_file` and `batch_name`. It pulls up to 1,000 posts and comments per account across all of Reddit, plus each account's true first-post date.
- **Cell 4:** same `batch_name`. It pulls the threads those accounts commented in, needed for the reply-timing rules.

### 6. Score

```python
from socialscope import history
history.score(["histories/b/b_posts.zip", "histories/b/b_comments.zip"],
              groups="groups.csv", context="context/b/b_posts.zip",
              out_dir="history_scores", as_of="2026-10-27",
              oldest="histories/b/b_oldest.json")
```

`history_scores/comparison.md` shows each rule's rate per group. A rule earns its keep only if it fires at least 5× more for known bots than controls, with controls under 5%. The last table converts that into precision: how often a flag would be right if 1% or 5% of accounts were bots.

### 7. Claims, narratives and bundles

```python
from socialscope import claims, sources, bundles
claims.spread("week/*.zip", "socialscope/data/kremlin_narratives.csv", out_dir="narratives")
sources.state_media("week/*.zip", out_dir="sources")
acc = bundles.tag(["week/*_comments_*.zip", "histories/*/*_comments.zip"], out_dir="bundles")
bundles.cooccur(acc); bundles.crossover(acc); bundles.amplifiers(acc)
```

Pattern matches catch people disputing a claim as well as asserting it. Read every match of a false claim and record its stance before counting anyone.

### 8. Big news subreddits

Don't pull whole weeks of r/politics or r/worldnews comments; they swamp everything else. **Cell 6** pulls their posts only, then comments for just the threads about the tracked topics.

### Using it with Claude

Install the skill from this repo (zip the folder with `SKILL.md` at the top level), then attach the files from each SEND THESE list and ask for the analysis. The skill asks for predictions first and keeps names hashed.

## What it found

October 2026, six subreddits, about 2.4 million records. Details are in `docs/`.

- **Account age is the one strong bot signal.** Accounts whose history starts under 90 days before the check caught 41% of confirmed bots and 4% of ordinary accounts on a fresh week. That still means most flagged accounts are people.
- **Behavior-only rules mostly failed.** Timing, repetition and writing-style rules separated few bots. The drama-sub bots are days-old accounts with a handful of comments, unlike the aged, bought accounts government reports describe.
- **Misinformation came from ordinary users, one claim at a time.** Of 27 checked claims, 8 were false or misleading. Asserts and disputes were about even, and no account repeated false claims. Across 1.2 million comments, one clearly asserted a documented Kremlin narrative.
- **Opinions cluster into three political bundles** (anti-Trump mainstream, anti-Hasan liberal, pro-Palestine). The h3 drama sits apart from politics. 93–99% of each subreddit's comments come from its own regulars. What crosses between subs is mostly anti-Hasan opinion, from r/Destiny into r/LivestreamFail.

## Write-ups

- `docs/bot-calibration-study.md`: every pre-registered round, predictions and results.
- `docs/claim-check-oct13-19.md`: misinformation rating for one week.
- `docs/foreign-influence-reports.md`: what EU, French, Taiwanese, UK, Meta and OpenAI reports describe, and what was borrowed from them.

## Data and privacy

No Reddit data, username lists or hashing salts are in this repository, and `.gitignore` keeps them out. Data comes from [Arctic Shift](https://arctic-shift.photon-reddit.com). Bot labels come from [r/BotBouncer](https://www.reddit.com/r/BotBouncer/). Hashed account IDs in the write-ups can't be reversed without the private salt.

## License

No license yet. All rights reserved by the author until one is chosen.

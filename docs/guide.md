# SocialScope User Guide

SocialScope is a research toolkit for tracing coordinated narrative spread across communities and screening for automated bot behavior in Reddit and X (Twitter) datasets.

---

## Misuse Guardrails

Every run of SocialScope must follow these operational ground rules:

1. **Hashed Names by Default:** Always run analysis and scoring with `--reveal none` (or `reveal="none"`). Account names are hashed through a project-specific salt (`.socialscope_salt`). Only reveal names if:
   - You moderate the specific subreddit being analyzed and the output is strictly for internal moderation of that community (`--reveal all`), or
   - You are exporting only accounts that reach the `high` confidence tier (`--reveal bots`) or confirmed `r/BotBouncer` listings (`reveal="known"`). Never distribute a named list of ordinary accounts tagged by community participation.
2. **Flags and Scores Are Leads, Not Proof:** Every detector tier (`high`, `likely`, `lead`) and history score is a prompt for a human reviewer to read the underlying posts. Because base bot rates in organic discussions are low, even a rule with a low false-alarm rate will flag real people. Always inspect 3–5 raw posts by eye before drawing conclusions.
3. **No Participation-Only Judgments:** Posting in a given subreddit or using a hashtag is never evidence of botting or astroturfing. Only behavioral mechanics count: verbatim repetition, synchronized timestamps, mechanical cadence, and account creation patterns. Also treat AI-styled writing (`authenticity` / `ai_vocab`) as a separate signal from automation—style detectors can misfire on formal writers and non-native speakers.
4. **No Identity Work:** Never attempt to link accounts to real-world identities, physical locations, or accounts on other platforms. Analyzing Reddit and X datasets in the same run is supported, but asserting that `example_user_1` on Reddit and `@example_user_1` on X are the same person is strictly out of bounds.
5. **Lawful Data Only:** Use only authorized archival dumps (Arctic Shift), licensed data providers (Xpoz), approved platform API access, or user-supplied exports. Do not scrape platforms directly or use proxies, header spoofing, or CAPTCHA bypasses.
6. **Name Only Confirmed Bots:** Public call-outs or external reports require either confirmation from `r/BotBouncer` or verified `high`-tier behavioral evidence attached directly to the report. Report confirmed Reddit bots through `r/BotBouncer` or official Reddit admin flows.

---

## Step 1: Pull Data in Google Colab

The fastest way to gather archival Reddit data without local rate-limit issues is `notebooks/socialscope_pulls.ipynb` in Google Colab, which wraps `socialscope.arctic` and writes compressed `.zip` archives to Google Drive.

1. Open `notebooks/socialscope_pulls.ipynb` in Google Colab and mount your Google Drive.
2. Pull weekly subreddit posts and comments for your target and control communities:

```python
from socialscope import arctic

ROOT = "/content/drive/MyDrive/reddit_pulls/example_study"

# Pull 1-2 event weeks plus 2-4 baseline weeks across target and control subreddits
arctic.pull_subreddits(
    ["ExampleSubA", "ExampleSubB", "ExampleControlSub"],
    start="2026-10-01",  # US Eastern dates
    end="2026-10-15",    # exclusive: through Oct 14
    out_dir=ROOT,
)

```

If you prefer running locally from a terminal, use `scripts/reddit_pull.py` or generate synthetic test fixtures first:

```bash
python3 test/make_fake.py

```

---

## Step 2: Run the Coordination Check

Use `scripts/analyze.py` (or `socialscope.toolkit.coordination`) to detect time-windowed co-similarity, co-link, co-reply, and co-retweet networks across your pulled `.zip` or `.jsonl` files.

```bash
pip install networkx scikit-learn numpy zstandard
python3 scripts/analyze.py "/content/drive/MyDrive/reddit_pulls/example_study/*.zip" \
  -o out/coord \
  --reveal none \
  --known-bots r_botbouncer_posts.zip \
  --known-before 2026-10-01

```

Key flags:

* `--similarity 0.9`: Character n-gram cosine similarity threshold for matching repeated talking points.
* `--sim-window 3600`: Maximum seconds between two accounts posting the same text to form a `co_similar` sync edge.
* `--min-edge-weight 3`: Minimum synchronized events before two accounts are linked as partners.
* `--known-before`: Restricts `r/BotBouncer` lookups to listings created before your dataset window so calibration does not grade itself.

---

## Step 3: Run the Two-Stage Bot Check

Because many automated accounts post only once or twice per week in a single subreddit, evaluating a single week of subreddit activity is too thin. SocialScope uses a two-stage pipeline:

### Stage 1: Shortlist Candidates (`screen.shortlist`)

Screen the weekly subreddit pulls for cheap behavioral leads, add a matched random control group, and write a private pull list:

```python
from socialscope import screen

screen.shortlist(
    f"{ROOT}/*.zip",
    out_dir="shortlist",
    known_bots="r_botbouncer_posts.zip",
    known_before="2026-10-01",
)

```

> **Privacy Warning:** `shortlist/users_to_pull.txt` and `shortlist/groups.csv` contain unhashed usernames (`example_user_1`, `example_user_2`, etc.) so Stage 2 can fetch their histories. Keep both files strictly private and never commit or share them.

### Stage 2: Pull Full Histories & Score (`history.score`)

Fetch recent cross-Reddit histories and thread context for the shortlisted and control accounts, then run the pre-registered ruleset:

```python
from socialscope import arctic, history

# 1. Pull up to 1,000 recent items per account across all subreddits
arctic.pull_user_histories(
    "shortlist/users_to_pull.txt",
    max_items=1000,
    out_dir=f"{ROOT}/histories/run1",
    name="run1",
)

# 2. Pull parent thread context for the comments
arctic.pull_thread_context(
    f"{ROOT}/histories/run1/run1_comments.zip",
    out_dir=f"{ROOT}/context/run1",
    name="run1",
)

# 3. Score histories against fixed rules (hashes usernames by default)
history.score(
    [f"{ROOT}/histories/run1/run1_posts.zip", f"{ROOT}/histories/run1/run1_comments.zip"],
    groups="shortlist/groups.csv",
    context=f"{ROOT}/context/run1/run1_posts.zip",
    out_dir="history_scores",
)

history.context_summary(
    f"{ROOT}/context/run1/run1_posts.zip",
    [f"{ROOT}/histories/run1/run1_comments.zip"],
    "shortlist/groups.csv",
    "history_scores",
)

```

---

## Step 4: Read and Interpret the Outputs

### Coordination Outputs (`out/coord/`)

* `report.md`: High-level human reviewer summary of clusters, sync edges, and community spread.
* `narratives.csv`: Repeated talking points with cluster size, participating communities, first-seen timestamp, and a representative text snippet.
* `community_flow.csv`: Directed edges (`r/ExampleSubA -> r/ExampleSubB`) weighted by how often talking points appeared in one community before jumping to another.
* `accounts.csv`: Per-account hashed ID (e.g., `acct_9f2a1c8b`), firing signal families (`content`, `timing`, `network`, `account`), assigned tier (`high`, `likely`, `lead`), and evidence summary.
* `coordination.graphml`: Network file ready for Gephi or interactive visualization.

### Two-Stage History Outputs (`history_scores/`)

* `comparison.md`: Side-by-side flag rates across `shortlist`, `control`, and `known_bots`, followed by a precision table at 1% and 5% base bot rates.
* **Compare against Controls:** A rule is informative only if it fires substantially more often on known bots than on the random `control` group (which measures your false-alarm rate).
* **Check Precision:** Even if a rule catches 40% of bots with a 4% false-alarm rate, at a 1% true bot prevalence roughly 9 out of 10 flagged accounts will still be human users.


* `accounts.csv`: Hashed account IDs (`acct_9f2a1c8b`), primary/support flags, and the composite ranking `bot_score` (use `bot_score` to prioritize manual review, never as a calibrated probability on a new population).
* `flagged_shortlist.csv` & `context_summary.md`: Shortlist accounts tripping multiple rules alongside a summary of the threads they targeted.

### Final Verification Checklist

1. Open `report.md` and `history_scores/comparison.md`.
2. For any hashed account (`acct_9f2a1c8b`) in the `high` or `primary+secondary` tier, inspect 3–5 of its raw posts in your local archive.
3. Downgrade any lead where human inspection shows organic participation (such as common memes, sports game-thread reactions, or normal newcomer activity).

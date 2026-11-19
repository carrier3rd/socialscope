# socialscope/bluesky — Bluesky Political Bot & Coordination Module

Spec for Claude Code. Drop this file into the socialscope repo root as `docs/BLUESKY_POLITICS_SPEC.md` and start a session with: "Read docs/BLUESKY_POLITICS_SPEC.md and do Phase 0."

## 1. Goal

Add a Bluesky module to socialscope that measures bots, coordinated inauthentic behavior and brigading in **US political reply threads on Bluesky**, using the same tiers, naming rules and report style as the Reddit/X work, so results can be compared across platforms.

The module answers three questions:

1. How many repliers in political reply threads show bot or coordination signals, and how does that differ between progressive-account threads and government/right-wing-account threads?
2. Can the documented Bluesky threats be detected in our own data: like/repost farms, follow farms, AI reply bots, hijacked dormant accounts (Matryoshka), block pile-ons?
3. Do the socialscope bot features trained on Reddit transfer to Bluesky, and which Bluesky-only signals add the most?

This is a separate project from the CMPT 336 class project. It lives inside socialscope and shares its conventions; the class project may later consume the exported feature CSV, nothing more.

## 2. Scope

### In scope (v1)
- Reply threads under a fixed target list of political accounts (config, Section 6).
- Known-bad calibration sets: labeled accounts from Bluesky moderation, Skywatch behavioral labels, antibot4navalny (Matryoshka), Roska Bridge accounts from the CheckFirst July 2026 report.
- Control sets: self-labeled bot accounts, Bluesky-verified accounts.
- Account-level features and detectors (Section 8).
- Aggregate reports by thread side (progressive vs government/right). No per-account faction scores in v1.

### Out of scope (v1)
- Whole-network crawls. Collect around targets only.
- Streamer/drama Bluesky clusters (DGG, Hasan, H3, Atrioc). Those are a later socialscope add-on.
- Cross-platform idea-bundle / diffusion analysis. v1 only records cross-platform links (Reddit/X URLs, domain handles) so it can be done later.
- Claim checking on Bluesky posts. Reuse later.
- Any interactive bot, posting, liking, following or reporting from our side. Read-only.
- Paid APIs. Everything must run free.

## 3. Non-negotiable rules

- **Naming:** publicly name an account as a bot only if it is Tier A (Section 7). Tier B and C appear only in aggregates. Public figures and target accounts can be named as targets, never as "bot-boosted" on our evidence alone.
- **Faction:** thread side is a grouping variable for aggregates. Never output a faction label per account.
- **Deletions:** honor firehose delete events. A deleted record is dropped from the stored corpus within the next normalize run.
- **Blocks and list memberships:** sensitive social signals. Report in aggregate only.
- **Unverified claims:** the July 2026 "8,515-account like farm" Leaflet post is a hypothesis to replicate, not a citation. Report replication as consistent / inconsistent, name no targets on it.
- **Predictions first:** before any analysis notebook runs on real data, `reports/PREDICTIONS.md` must exist with dated predictions (Section 10). Do not edit predictions after results exist; add a dated addendum instead.

## 4. Environment

- Collection runs on the owner's laptops (Victoire, Windows; or the older Linux HP) via Claude Code, because Colab sessions time out. Colab Pro is fine for analysis. Raw and processed data sync to Google Drive.
- Python 3.11+. Libraries: `atproto` (MarshalX), `httpx`, `websockets` or `httpx-ws`, `pandas`, `pyarrow`, `duckdb`, `scikit-learn`, `pyyaml`, `pytest`. No paid services, no API keys except an optional Bluesky app password for search.
- Paths must work on Windows and Linux (`pathlib`, no hardcoded `/`).

## 5. Phase 0 — Recon (do this first, write nothing else)

1. Read the existing socialscope repo. Find: the account-feature schema, the tier/naming implementation, the BotBouncer calibration code, the CI / leakage audit / Poisson alarm / kNN code, report templates, and how the social-coordination skill expects inputs.
2. Write `bluesky/RECON.md` listing: files to reuse as-is, functions to generalize (platform-agnostic), the existing feature column names, and any conflicts with this spec.
3. Stop and show RECON.md before writing code. Where this spec conflicts with existing socialscope conventions, the existing convention wins unless RECON.md argues otherwise.

## 6. Config

`bluesky/config/targets.yaml`

```yaml
window:
  start: 2026-11-20
  end: 2026-12-11          # 3 weeks; extend later
sides:
  progressive:
    - aoc.bsky.social
    - meidastouch.com
    - atrupar.com
    # fill to ~10 large progressive/news accounts
  government_right:
    - whitehouse.gov        # confirm handle in Phase 1
    # agency + right-wing accounts active on Bluesky, fill to ~10
calibration:
  labelers:
    bluesky_mod: did:plc:ar7c4by46qjdydhdevvrndac
    skywatch:    did:plc:e4elbtctnfqocyfcml6h2lf7
    antibot4navalny: <resolve in Phase 1>
  extra_known_bad: data/known_bad/roska_bridge.csv   # hand-entered from CheckFirst report
controls:
  self_labeled_bots: true
  verified_accounts: true
limits:
  max_repliers_per_post: 2000
  history_posts_per_account: <match Reddit history cap from RECON>
  target_accounts_total: 3000-5000
```

Resolve every handle to a DID at collection time and store both. All joins use DIDs.

## 7. Label tiers (map onto existing socialscope tiers)

| Tier | Source | Use |
|---|---|---|
| A | Bluesky moderation labels `spam`, `impersonation`, `!takedown`; account no longer resolving with takedown error; accounts named in Clemson / ISD / AFP / CheckFirst reporting; antibot4navalny labels | Ground truth positives; nameable |
| B | Skywatch behavioral labels only: `suspect-inauthentic`, `platform-manipulation`, `follow-farming`, `bulk-following`, `amplifier`, `engagement-abuse`, `inauthentic-fundraising`, `spam`, `repetitive-domain-spam-*` | Corroborating; aggregates only |
| C | Community moderation lists, heuristics alone | Never ground truth, never named |
| Control | Self-labeled `bot`; Bluesky-verified accounts | Benign bot class; high-confidence human class |

Skywatch also publishes political/identity labels (e.g. `maga-trump`, `tankie`). **Whitelist the behavioral values above and drop everything else**, or faction leaks into bot labels. Honor `neg: true` retractions. Store label `cts` timestamps; features for a labeled account use only activity before its first label (pre-label leakage audit, same rule as pre-ban on Reddit).

## 8. Architecture

```
bluesky/
  collect/
    jetstream.py      # bounded-window recorder, hourly .jsonl.gz, cursor resume
    appview.py        # threads, author feeds, profiles, lists, starter packs
    labels.py         # subscribeLabels replay from cursor 0 (Skywatch over HTTP/1.1)
    plc.py            # per-DID audit log from plc.directory
    backlinks.py      # Constellation client (likers/reposters/followers/blockers), cached
  normalize/
    to_parquet.py     # raw -> tables below, applies deletes
  features/
    shared.py         # features that exist on Reddit too (names from RECON)
    bsky_only.py      # Bluesky-only features
  detect/
    like_farm.py
    follow_burst.py
    dormant_hijack.py
    reply_bot.py
    block_surge.py    # reuse socialscope Poisson alarm
  evaluate/
    transfer.py       # Reddit-trained model on Bluesky, CIs, kNN evidence
  reports/
  config/
  tests/
data/bluesky/{raw,processed,exports}/   # gitignored, synced to Drive
```

### Collectors — requirements
- **Jetstream:** `wss://jetstream1.us-west.bsky.network/subscribe` (fallback jetstream2.us-east). Filter `wantedCollections` to `app.bsky.feed.post`, `app.bsky.feed.like`, `app.bsky.feed.repost`, `app.bsky.graph.follow`, `app.bsky.graph.block`, `app.bsky.graph.listitem`. Keep only events whose author or subject is in the target set or the replier set (replier set grows as threads are fetched). Persist cursor every minute; resume from it after a crash.
- **AppView:** `https://public.api.bsky.app/xrpc/`. `getPostThread` for every target post in the window, `getAuthorFeed` for each replier up to the history cap, `getProfiles` in batches of 25. Exponential backoff on 429. Log request counts.
- **Labels:** `com.atproto.label.subscribeLabels?cursor=0` for each labeler; store all, filter at feature time.
- **PLC:** `https://plc.directory/<did>/log/audit` per account; cache forever (append-only).
- **Constellation:** `https://constellation.microcosm.blue/` (best-effort public instance). Cache every response to disk; never hammer it; set a descriptive User-Agent. If it is down, fall back to Jetstream-derived counts.

### Tables (parquet)
`accounts` (did, handle, display_name, created_at, pds_host, domain_handle bool, self_labels, verified, side_seen[]) ·
`posts` (uri, did, created_at, indexed_at, text, langs, reply_parent, reply_root, embed_type, facet_links[], facet_mentions[]) ·
`interactions` (type, actor_did, subject_uri_or_did, created_at, rkey_time) ·
`labels` (src, uri_or_did, val, neg, cts) ·
`plc_ops` (did, op_type, handle, pds, rotation_keys_changed bool, created_at)

### Features
- **Shared (same names as Reddit, from RECON):** account age, posts/day, inter-post interval mean and variance, reply share, share of replies to higher-follower accounts, original-post count, longest dormant gap, low-credibility domain share.
- **Bluesky-only:** handle-change count and recency (PLC), PDS migration count, key rotation shortly before a posting burst, self-hosted/rare PDS share among a cluster, follower/following ratio, follows created in bursts, likes given with zero posts, `createdAt` vs `indexed_at` skew, declared `langs` mismatch with detected language, share of posts with Reddit/X links, block count received.

### Detectors
- **like_farm:** for each target post, the distinct-liker count and liker set; flag groups of unrelated targets with identical liker counts and high Jaccard overlap of liker sets. Replicates the Leaflet claim. Output aggregate only.
- **follow_burst:** creation-date streaks and bulk-follow bursts (Conspirador Norteño method). Control: subtract bursts explained by starter-pack joins.
- **dormant_hijack:** long dormancy → handle/PDS/key change in PLC → sudden political posting. Validate against Matryoshka Tier A accounts.
- **reply_bot:** replies within seconds of target posts, no original posts or media, replies mostly to bigger accounts, bait-question patterns (Willison checker logic).
- **block_surge:** per-target blocks/hour, Poisson baseline from the same hour over the prior 7 days, alarm at p < 0.001. Reuse socialscope code.

## 9. Integration with existing projects

- **socialscope core:** platform-agnostic code goes in shared modules, not copied. Bluesky outputs use the existing tier names, report template and CI/leakage/kNN functions.
- **social-coordination skill:** add a Bluesky input adapter section to the skill docs once Phase 3 works (propose the edit; the owner saves it).
- **research-findings-infographic skill:** results doc follows the `*-results.md` format so the infographic skill can read it.
- **CMPT 336 (optional):** export `exports/bsky_features.csv` with shared-feature columns only plus tier label. The class project reads it; nothing in this module depends on the class.
- **Later hooks (record now, use later):** keep `facet_links` so Reddit/X cross-posting and DGG/Hasan clip spread can be joined into the cross-pollination work.

## 10. Phases and acceptance criteria

| Phase | Deliverable | Done when |
|---|---|---|
| 0 Recon | `bluesky/RECON.md` | the owner has reviewed it |
| 1 Collect | collectors + `targets.yaml` filled | 24-hour pilot run completes, resumes after a killed process, request log shows no sustained 429s |
| 2 Normalize | parquet tables | deletes applied; row counts reported; tests pass on a fixture |
| 3 Features | shared + bsky_only | feature CSV for pilot; no feature uses post-label activity (test) |
| 4 Detect | five detectors | each runs on pilot; each has a synthetic test that plants a known pattern and recovers it |
| 5 Predictions | `reports/PREDICTIONS.md` | written and dated before Phase 6 |
| 6 Evaluate | transfer + detectors on full window | Reddit-trained model scored vs Tier A with bootstrap CIs; Tier B shown separately; kNN evidence for flagged accounts |
| 7 Report | `reports/bluesky-politics-results.md` | aggregates by side, Tier A naming only, caveats section |

### Starter predictions (Claude's, to be confirmed or edited by the owner in Phase 5)
1. Flagged-account density is higher in progressive-thread replies than government-thread replies.
2. Most block surges the alarm catches are organic reactions to news; few coincide with Tier A/B clusters.
3. The like-farm identical-count signature appears at least once in a 3-week window, at smaller scale than claimed.
4. AI reply bots are the class the Reddit-trained model misses most; reply latency is the strongest new feature.
5. Dormant-hijack signatures are rare (dozens, not hundreds) in US political threads; Matryoshka mostly targets non-US audiences.
6. Shared features keep most of their importance; karma-like features have no replacement and their loss costs the most recall.

## 11. Known pitfalls

- Bluesky moderation labels: precision about 0.84, recall about 0.22 (Singh et al. audit). Low scores against Tier A partly reflect missing labels; say so in every result.
- Skywatch automation had outages in June 2026; check label volume over time before trusting gaps.
- `searchPosts` returns 403 on the public host; avoid needing it.
- Starter packs create real follower bursts that look fake.
- Bridged accounts (`*.ap.brid.gy`, Nostr bridges) are a known spam path and Roska Bridge's vector: flag them as their own class.
- Handle equality across platforms is not identity. Only domain handles or bio cross-links count.
- Constellation's public instance runs on a Raspberry Pi; cache everything.

## 12. References

- Bluesky 2025 Transparency Report (Jan 29, 2026)
- AFP / ISD on Matryoshka hijacked accounts (May 28–29, 2026); Clemson Media Forensics Hub Matryoshka-on-Bluesky report (Mar 25, 2026)
- CheckFirst, "Roska Bridge" (July 2026)
- Conspirador Norteño, "Selling followers where the skies are blue" (Jan 2025)
- Singh et al., moderation label audit, arXiv 2609.11373
- Sokoto et al., "Open or Blocked Skies?", WWW 2026
- Nogara et al., longitudinal misinformation on Bluesky, OSNEM 2026 (arXiv 2505.02317)
- Meng, Wang & Peng 2026 Bluesky bot benchmark, CMM 20(2) (code at osf.io/qscf8)
- Simon Willison, reply-bot checker (Sept 27, 2026)
- Democracy on the Internet (Leaflet), like-farm claim (July 30, 2026) — unverified
- Constellation backlink index: constellation.microcosm.blue

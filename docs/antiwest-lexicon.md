# Anti-Western talking points: lexicon, factions and video index (v1, Nov 17, 2026)

A reference for spotting campist ("tankie") anti-American talking points and telling which faction they come from.
Modeled on the ADL's antisemitism glossaries: each entry says what the claim is, how it is usually worded, who uses
it, what real facts it leans on, and what separates the marker from ordinary speech.

**Status: a draft built from research and two commentators' arguments. It has not been tested on our data.** Nothing
here has a measured hit rate or false-alarm rate yet. Section 7 says what has to happen before any number from it is
reported.

## 1. What is in the repo

| File | What it holds |
|---|---|
| `data/antiwest/factions.csv` | 12 groups: 9 sources of these talking points, the isolationist right for comparison, and 2 counter-classes that must not be mislabeled |
| `data/antiwest/talking_points.csv` | 49 claims in 8 families, each with cue phrases, factions, tier, state-media overlap, basis in fact and what marks it |
| `data/antiwest/vocabulary.csv` | 77 terms (322 surface forms) with meaning, factions, specificity and false-positive cautions |
| `data/antiwest/rhetorical_moves.csv` | 10 argument patterns (whataboutism pivot, one-directional skepticism, the pro-America test...) with their source and limits |
| `data/antiwest/sources.csv` | 18 research sources, what each found, what was taken, and how far I actually read each one |
| `data/antiwest/transcripts/` | Timestamped machine transcripts of Destiny videos, plus `index.csv` |
| `data/antiwest/vod_segments.csv` | Timestamped passages with a link to the second, the talking points involved, a paraphrase and a checked quote |
| `data/antiwest/vod_queue.csv` | Videos found but not yet transcribed, and why |
| `data/antiwest/vod_channel.csv` | Every upload on the Destiny YouTube channel since Aug 17, 2026, with date and length |
| `scripts/yt_captions.py` | Lists a channel and fetches YouTube captions with yt-dlp, on the laptop |
| `scripts/yt_gemini_transcript.py` | Gets a timestamped transcript of a YouTube video from the cloud session |
| `scripts/transcript_segments.py` | Indexes passages in a transcript and checks every quote against it |
| `scripts/antiwest_tag.py` | Counts lexicon hits in transcripts or Reddit dumps, per group, never per account |
| `skills/antiwest-lexicon/SKILL.md` | The same method written as a Claude skill |

## 2. The one distinction everything rests on

Criticizing the United States is not the thing being tracked. Seventy-nine percent of Americans aged 18 to 42 agree
that American democracy is in crisis (GenForward, fielded October 2025), so alarm about the US cannot mark a faction.

What the lexicon tracks is **campism**: sorting the world into a US-led camp and an opposing camp, and siding with the
second whatever it does. In practice that means three things appearing together:

1. The US is described as illegitimate or evil by nature (not for a policy or an administration).
2. States and armed groups opposed to the US are defended, excused or never criticized.
3. Liberals and the Democratic Party are treated as the main enemy at home.

A comment with only the first is far-left or decolonial. A comment with the first and without the second often comes
from the anti-campist left (Trotskyists, anarchists, much of DSA), who call the US imperialist and call Russia and
China the same. They are the largest false-positive risk and have their own row in `factions.csv`.

### Tiers

Each talking point has a tier that says how much it tells you:

| Tier | Meaning | Count | Example |
|---|---|---|---|
| 1 | Campist-specific: rare outside Marxist-Leninist and campist spaces | 29 | "Critical support"; Xinjiang camps are vocational schools; the Maidan was a US coup |
| 2 | Far-left general: shared with anti-campist socialists and decolonial academics | 15 | The US is a settler colony; the imperial boomerang; sanctions are war |
| 3 | Cross-ideology: also said by the isolationist right and mainstream realists | 5 | NATO expansion provoked Russia; both parties are the same; proxy war |
| 0 | Ordinary criticism, not in the table | n/a | Iraq was a mistake; this administration is authoritarian |

Thirty-seven of the 49 overlap with Russian, Chinese or Iranian state messaging (`state_media_overlap`). Overlap
means the same claim, not that anyone was directed to say it.

## 3. The factions

Full rows are in `factions.csv`. Short version:

| ID | Faction | Its tell |
|---|---|---|
| ML | Marxist-Leninist core, the original "tankies" | AES, CPC, DPRK, "critical support", "revisionist" |
| MLM | Maoist / Third-Worldist | "labor aristocracy", "settlers" as a class, "treatlerite", amerikkka |
| CAMP | Campist media network (Grayzone, BreakThrough News, Tricontinental...) | "multipolar", "color revolution", "NED-funded", "collective West" |
| RES | Resistance-axis solidarity | "the resistance", "Zionist entity", "Al-Aqsa Flood", "glory to the martyrs" |
| POP | Populist / streamer left | "Genocide Joe", "blue MAGA", "shitlibs", "electoralism" |
| DECOL | Decolonial strand | "so-called United States", "Turtle Island", "land back" |
| BRAD | Black radical anti-imperialist tradition | "internal colony", AFRICOM, "AmeriKKKa" |
| REDBROWN | "Patriotic socialists" / MAGA communists | "globalists", "Atlanticists", "multipolarity" plus Marxist symbols |
| STATE | State media and officials | "special military operation", "whole-process democracy", "golden billion" |
| RIGHT | Isolationist right (comparison) | Same Ukraine and NATO lines with no "imperialism" or "capital" around them |
| ANTICAMP | Anti-campist far left (counter-class) | "campist" and "tankie" as insults, "neither Washington nor Moscow" |
| LIB | Ordinary critics (counter-class) | Criticism aimed at a policy or a president |

How to tell neighbors apart:

- **ML from ANTICAMP:** look for the words they use for each other. "Ultras", "Western leftists", "left
  anticommunism", "NATO left" come from ML. "Campist", "tankie", "red fash", "Stalinist" come from ANTICAMP. In our
  own data "campist" is used most by r/dsa regulars (13.2 per 10,000 comments), who are arguing against campists.
- **CAMP from RIGHT:** the Ukraine sentences are nearly identical. The left version sits among "imperialism",
  "global south" and "capital"; the right version sits among "deep state", "globalists" and "America First".
- **RES from the pro-Palestine public:** support for the armed groups by name, or celebration or denial of
  October 7. Calling for a ceasefire, or calling the war a genocide, is not in the lexicon.
- **Left "Israel is America's outpost" from "Israel controls America":** opposite claims. The first is RES-03. The
  second overlaps with antisemitic tropes and is covered in `docs/hasan-israel-control-conspiracy-results.md`.

## 4. What the research says

Fuller notes and reading status are in `sources.csv`. I read only two of these in full (marked there); the rest I
know from search summaries or memory, and say so per row.

- **Balci, Sirivianos and Blackburn (arXiv 2307.06981, v4 January 2026)** is the one large measurement study: 1.3
  million posts by 53,000 authors in six tankie subreddits, 2019 to 2022. Findings that matter here:
  - Tankies sit at the edge of the far-left subreddit network and link mostly to each other.
  - Their top topic is Xinjiang. They rank first among far-left communities on Xinjiang, North Korea, Ukraine,
    China-US conflict and Israel-Palestine, and lower than the others on healthcare, housing, unions and policing. **Topic mix
    alone separates them: states over social issues.**
  - Vocabulary differs from other far-left subs on seven axes: Chinese government narratives, Stalinism, the Russian
    line on Ukraine, anti-Zionism, toxic tone, state media, US politics. Their word pairs (CPC for CCP, "rioters"
    for protesters, "boarding schools" for Uyghur camps, DPR/LPR for Donbas) are in `vocabulary.csv`.
  - 60% of their news links go to Chinese and Russian state outlets, against 6.3% in r/DemocraticSocialism and 3.7%
    in r/Anarchism. `socialscope/sources.py` already counts state-media links, so this test can run today.
  - While other far-left subs lost users after Russia invaded Ukraine, tankie subs kept growing.
- **Their follow-up on Lemmygrad (arXiv 2507.23699)**: after Reddit quarantined r/GenZedong the community moved off
  Reddit and got more active and more toxic. Reddit data now undercounts the core.
- **Dogwhistle research (Mendelsohn et al. 2023; Kruk et al. 2024)** shows that coded terms slip past toxicity
  filters and that a language model can separate the coded sense of a word from the plain one. That is the method
  for the words here that are ordinary most of the time ("settler", "the resistance", "rioters").
- **State-narrative reports (EUvsDisinfo; EEAS 2026)** list "imminent collapse" of the West, the "multipolar world"
  and Nazi-labelling of opponents as standing Russian narratives, and Taiwan, Hong Kong and Xinjiang defense as
  Chinese ones.
- **Left-wing authoritarianism (Costello et al. 2022)** is a validated psychology scale. It measures aggression
  toward hierarchy, rejection of convention and support for censorship. It does not ask about foreign states, so it
  is a different thing from campism and the two should not be merged.
- **Funding and networks (NCRI 2024; New York Times 2023)**: money from Neville Roy Singham to several CAMP
  organizations is documented. Direction by Beijing is not, and coverage of the NCRI report came mostly from
  partisan outlets. In the Destiny conversation Noah Smith himself says the movement is "much more autonomous than
  that" (00:23:28).

What I did not find: any peer-reviewed study of this vocabulary after 2022, any study covering Twitch or YouTube
left commentary, or any validated classifier. The topic is thinly studied compared with right-wing extremism.

## 5. How Destiny and Noah Smith say to pick it out

From the conversation streamed around November 12, 2026, and Destiny's Bulwark reaction a few days later. Every
timestamp below is in `vod_segments.csv` with a link and a quote checked against the transcript. These are their
arguments, not findings.

**Smith's model (DGs4Nq4dOEw):**

- There are two left movements in the US. One is progressive or "woke", descended from abolitionism. The other is
  "leftist", descended from Cold War communism (00:14:31, 00:15:17).
- For the second, anti-Americanism is the core and everything else is negotiable: Medicare for All, Russia, even
  Palestine (00:35:25). "Iran, it's against America, so I'm for it" (00:16:56).
- The test: can the person be pro-American? "If they're pro-America, they're out of the club" (00:35:05).
- It is mostly self-directed, "a meme", not run from abroad (00:23:28).
- Its method is entryism: join a broad left coalition, then turn on the others. His comparison is the Spanish Civil
  War (00:21:12).

**Destiny's checks:**

- Search the author of an anti-American statement plus "Ukraine" or "Russia" (DGs4Nq4dOEw 00:22:30).
- Camp, not religion or principle: Saudi Arabia and Egypt are opposed because they are US-aligned (00:17:12).
- Listen on their own channels, where taking over the Democratic Party and "both parties are the same" are said
  openly (00:22:30).
- Watch the timing and target of fights: attacks on Democratic leaders right after Democratic wins (00:19:10).
- Watch for relabeling: standard Democratic policy presented as something only socialists offer (00:31:34).
- Same issue, different ask: a progressive wants sanctions on West Bank settlers and steps toward Medicare for All;
  a leftist wants nothing done within the system (NEF0VNPZ7lU 00:59:29).
- His own caveat: the average DSA member is probably progressive, not campist; the pattern is at the top (00:18:43).

**Where I would be careful with their account:**

- The pro-America test also catches people who simply dislike patriotism. It fits public figures' stated positions
  better than anonymous comments.
- "DSA is entryist like the Spanish communists" and "the strategy is to run Middle Eastern candidates and call
  critics Islamophobic" (00:25:52) are Smith's claims. Neither is backed by a study I found, and the second treats
  accusations of anti-Muslim bigotry as tactical by default, which needs case-by-case reading.
- Both are opponents of the faction they describe. The lexicon keeps their observations as hypotheses to test
  (`rhetorical_moves.csv`, column `caution`).

Three of the checks can be tested on data we already hold, with predictions written first: the state-media link
share by subreddit, the topic mix (states against social issues), and whether anti-Democrat volume in left subs
rises after Democratic wins.

## 6. Videos and transcripts

Twenty transcripts are in `data/antiwest/transcripts/`, one `.txt` per video (about 30.5 hours), with a row each in
`index.csv`. Lines are `[HH:MM:SS] SPEAKER: text` in the three Gemini transcripts and `[HH:MM:SS] text`, about every
30 seconds, in the seventeen caption transcripts.

**Machine transcripts by Gemini (speaker labels are the model's guess):**

| Video | Length | What it is | Passages |
|---|---|---|---|
| `DGs4Nq4dOEw` | 1h18 | Destiny and Noah Smith, streamed about Nov 12, 2026, posted Nov 14 | 22 |
| `NEF0VNPZ7lU` | 1h23 | Destiny reacts to Ezra Klein on The Bulwark, about Nov 15, 2026 | 8 |
| `INnln13RMnM` | 0h51 | Destiny reacts to Vaush and Soy Pill's West Bank trip, about Oct 31, 2026 | 4 |

**YouTube auto-captions via `scripts/yt_captions.py` (fetched Nov 16, 2026 on the laptop; no speaker labels):**

| Video | Length | Uploaded | Channel | What it is | Passages |
|---|---|---|---|---|---|
| `tkab3gPpXjA` | 4h26 | 2026-08-17 | Destiny | "Liberal CIVIL WAR Over DSA": liberal panel on DSA nominees and entryism, with a DSA-member YouTuber | 62 |
| `KXslvrBBCyo` | 2h17 | 2026-08-30 | Destiny | "3V1 DSA Debate": reaction to a panel on joining DSA, then Destiny vs. Dylan Burns on DSA and Ukraine | 18 |
| `UszLyg0TfGk` | 1h30 | 2026-09-01 | Destiny | "Explaining Hasan, MAGA & Populism": call on spotting tankies vs. progressives; DSA and Ukraine | 21 |
| `jTnsRrJMHnw` | 1h17 | 2026-09-02 | Destiny | "Lamenting Tim Pool & Hasanabi": mostly the Tim Pool debate; little on campism | 9 |
| `v4G3BQXJYy8` | 1h01 | 2026-09-16 | Destiny | "Total Hasan MELTDOWN": reaction, then a fan documentary about Hasan Piker | 9 |
| `EsJK1qI4zks` | 1h58 | 2026-10-18 | Destiny | Reaction to Mehdi Hasan interviewing Neera Tanden on Al Jazeera; mostly intra-Democrat | 13 |
| `cI-qIFHwkEE` | 1h23 | 2026-10-19 | Destiny | "Abdul El Sayed Disavows Hasan Piker" | 7 |
| `QAbf21awiOw` | 0h26 | 2026-11-11 | clip channel | Michigan Senate race; reaction to a left streamer | 6 |
| `KaxwDXVtTiw` | 0h19 | 2026-11-07 | clip channel | "Lefties Claim Credit For Midterm Sweep" | 8 |
| `VL3gu403rVs` | 0h58 | 2026-10-30 | clip channel | Reaction to two left streamers on an NGO-funded West Bank trip | 10 |
| `rNpMQscXNF4` | 1h17 | 2026-10-13 | clip channel | Reaction to a video on Israel's aims in Gaza and Lebanon; little on campism | 6 |
| `h3xM9A9uIyY` | 1h15 | 2026-02-10 | clip channel | Destiny plays a liberal panel arguing with two left guests about Gaza non-voting | 12 |
| `YHc1nsVqxkI` | 3h40 | 2026-07-29 | clip channel | Discord debate on DSA, Mamdani's endorsements, NATO and Hamas | 35 |
| `z_mHlhhc4Hg` | 2h20 | 2026-04-25 | Destiny | Panel with a social-democrat guest on progressives vs. Marxists and the far-left media | 24 |
| `LxzUiRRhVkw` | 0h12 | 2026-01-27 | clip channel | Reaction to Hasan Piker's claims about Destiny's China trip | 3 |
| `NRxAPM8UDlw` | 0h22 | 2025-11-16 | clip channel | Reaction to Hasan Piker's China streams and CGTN interview | 9 |
| `v7-7rtt8J0I` | 2h11 | 2024-02-03 | Destiny | Earlier Noah Smith conversation, mostly China's military and US economics | 10 |

`vod_segments.csv` indexes 296 passages across the twenty, every quote checked against its transcript (`quote_ok` 1).
The 262 caption passages were written by hand after a full read. `vod_queue.csv` lists the 2 videos still missing.

`vod_channel.csv` lists all 86 uploads on the Destiny YouTube channel from Aug 17 to Nov 14, 2026 (about 150
hours), from `yt_captions.py list`. Eight of them are transcribed: the Noah Smith conversation and the seven titles that
matched the filter `tankie|leftis|lefties|hasan|china|russia|ukraine|america|socialis|communis|dsa|noah`, about 15
of the 150 hours. The other twelve transcripts come from the earlier search-based queue.

Limits:

- **Eight of 86 channel videos is a title-filtered sample, not "the last three months".** The other 78 uploads (about
  135 hours) were not fetched. Titles miss on-topic streams, and several of the matches turned out to be mostly about
  other things (Tim Pool, Israel, intra-Democrat fights). Fetching the rest is one command
  (`yt_captions.py fetch --from data/antiwest/vod_channel.csv --cookies-from-browser firefox`), but indexing it by hand
  is the slow part.
- Ten transcripts are from before the three-month window or from clip channels. They came from the earlier search
  queue and are kept because they are on topic, but they are not a sample of anything.
- **Caption transcripts have no speaker labels.** In reaction videos Destiny's voice and the clip run together. Rows
  say "Destiny" only when the context makes it clear. Otherwise they say "speaker unclear" or give a role ("panelist",
  "caller", "left guest (clip)"). Small creators and private guests are labelled by role, not name.
- Auto-captions mishear names ("Rashidita Talib", "Medhi Hasan") and censor profanity as `[ __ ]`. Quotes are copied
  as captioned. For `h3xM9A9uIyY` YouTube offered only a machine-translated "en" track, though it reads as normal
  English.
- The three Gemini transcripts are a model's transcription. Names and numbers can be wrong, and four long lines are
  repeated in `INnln13RMnM` (for example 00:23:43 and 00:25:58). They were kept, not replaced by captions.
- `NEF0VNPZ7lU` and `INnln13RMnM` are not in the channel listing, so their dates are still approximate.
- Failed or missing: `JWU9jl1Ixs8` and `gNPwYYdBM-8` (the uploader's YouTube account was terminated) are still in the
  queue. The private stream `x2d5D2lsi9w` was dropped from the queue because `DGs4Nq4dOEw` is the same conversation.
- On the laptop, YouTube sometimes answers caption requests with HTTP 429. Retrying with
  `--cookies-from-browser firefox` worked. Chrome's cookie store was not found and Edge's could not be decrypted.

## 7. Before any number from this is reported

The project's rules apply (CLAUDE.md rule 3, `docs/research-methods.md`):

1. **Predictions first.** Commit a `*-predictions.md` before running `antiwest_tag.py` on a pulled week.
2. **Blind read.** For each term and talking point, read a random sample of hits and code assert / dispute / quote /
   joke. The earlier `anti_tankie` pattern came in at 65% on its blind read (17 of 26) and was not adopted
   (`docs/opinion-bundles.md`); expect several entries here to fall short too. Drop or narrow them.
3. **Known-group check.** Rates should be highest in r/TankieTheDeprogram, lower in r/Hasan_Piker and r/dsa, near
   zero in r/neoliberal and r/Destiny after disputes are removed. If r/Destiny scores high, the tagger is counting
   people arguing against the talking points.
4. **Community level only.** Report rates per subreddit or chat. No per-account anti-Western, tankie or faction
   label is published or stored with a name, and posting in a community is never evidence about a person.
5. **Not bots, not foreign.** A hit says nothing about whether an account is automated or foreign. Those are the bot
   study's questions and need its evidence.

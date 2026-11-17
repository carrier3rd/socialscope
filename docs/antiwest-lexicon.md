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

Transcripts are in `data/antiwest/transcripts/`, one `.txt` per video, lines in the form `[HH:MM:SS] SPEAKER: text`.
`index.csv` lists what is there. `vod_queue.csv` lists videos found but not transcribed.

How they were made: the cloud session cannot reach YouTube or any transcript site. The Gemini API can read a public
YouTube video directly, so `scripts/yt_gemini_transcript.py` asks it to transcribe the audio in 30-minute windows.

Limits:

- They are a model's transcription, not YouTube's captions. Names and numbers can be wrong. Speaker labels are the
  model's guess. I found one passage repeated twice in INnln13RMnM (00:23:43 and 00:25:58).
- The project's Gemini key is on the free tier: 20 requests per model per day. That is roughly five to eight hours
  of video a day across the models that work. It is why only part of the last three months is here.
- The original Noah Smith stream (x2d5D2lsi9w) and two other videos returned "permission denied". The Noah Smith
  conversation was read from a public re-upload (DGs4Nq4dOEw, 1 hour 18 minutes; it may be shorter than the stream).
- I could not list Destiny's channel, so the video list came from web search and is not complete.
- On the laptop, `yt-dlp` captions are better and free; `scripts/transcript_chunks.py` already reads them.

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

# How Destiny's videos say to spot the anti-Western left, checked against the research (Nov 16, 2026)

This reads the 296 indexed passages in `data/antiwest/vod_segments.csv` (20 videos, about 30 hours) against the
research in `data/antiwest/sources.csv` and `docs/antiwest-lexicon.md`. It asks three questions:

1. What tests do Destiny and his guests use to pick out tankies, campists and leftists?
2. Which of those tests does outside research support, which does it not address, and which does it contradict?
3. What does that mean for the lexicon, and what can be tested on our own data?

**Status: qualitative, no measurement.** Nothing here was run on Reddit or chat data, and no rate is reported. The
hypotheses in section 6 need a committed `*-predictions.md` before any of them is tested (CLAUDE.md rule 3).
Everything the videos claim is the claim of commentators who oppose the faction they describe. It is kept as a
hypothesis, not a finding.

How to read the references: `KXslvrBBCyo 01:54:33` means that video at that time. Every reference is a row in
`vod_segments.csv`, with a link that opens the video at that second and a quote checked against the transcript. The
transcripts are machine-made (YouTube auto-captions or Gemini), so check a quote against the video before
publishing it.

## 1. Summary

- **The videos describe the faction. They do not show it.** Only 18 of 296 passages are someone stating a
  talking point, and none of the 18 is a tier-1 (campist-specific) point. The rest are Destiny, Noah Smith or guests
  describing the faction (195) or arguing against it (83). The videos give markers to look for, not examples to train on.
- **Their target is the DSA and the streamer left, not the tankie core the research measured.** LIB-01 ("liberals
  are the real obstacle") is the most common talking point by far: 46 passages in 14 of 20 videos. Xinjiang, the top
  tankie topic in Balci et al., comes up once, from Smith. 23 of the 49 talking points never come up.
- **One test is strongly supported by the research: selective anti-imperialism.** "Not anti-war, just anti-American
  wars" and "strong words on Palestine, only 'more diplomats' on Ukraine" are the campism definition in the literature
  (MOVE-05) and match Balci et al.'s Ukraine axis. The Ukraine/Palestine asymmetry is the most specific and testable
  idea in the videos, and the lexicon does not yet have it as its own move.
- **Destiny's other main marker is about the Marxist left in general, not campism.** "They disdain identity politics
  and reduce everything to class" (4 videos) fits Balci et al.'s finding that tankie subs talk about states more than
  social issues. But it also fits anti-campist Marxists and the populist left, so it cannot mark campism alone.
- **Three tests treat moderation or silence as evidence.** These are "mask on", "no pro-NATO statement means
  anti-NATO", and "calls for peace are a dog whistle". They cannot be proven wrong and should not become coding rules.
- **The videos split on whether the movement is directed from abroad.** Destiny talks of "coordinating with the
  enemies of America". Smith says "they're much more autonomous than that". The research supports Smith: funding is
  documented, direction is not.
- **The anti-campist left shows up in the videos too.** A pro-DSA panelist wants the "campists and tankies" pushed
  out, Dylan Burns attacks the DSA co-chair over Ukraine, and a social-democrat guest refuses "apologetics" for China,
  Cuba and the USSR. This is the lexicon's largest false-positive group, and in these videos it sits inside the DSA
  orbit.

## 2. What is in the index

| | Passages |
|---|---|
| identify (how to recognize them) | 107 |
| factions (how groups differ or organize) | 88 |
| rebut (arguing against a point or its holders) | 83 |
| assert (someone states a talking point) | 18 |
| Speaker: Destiny / Noah Smith / others | 182 / 21 / 93 |
| No talking-point id fits | 163 |

Talking-point families among the 133 tagged passages: LIB 56, EMP 22, FASC 20, RES 16, UKR 15, CHN 12, HIST 3. The
most frequent single points are LIB-01 (46 passages, 14 videos), EMP-01 "US imperialism is the primary contradiction"
(14, 5), RES-01 "axis of resistance" (13, 8), FASC-07 "both parties are the same" (9, 5) and LIB-02 "Democratic
leaders are guilty of genocide" (8, all from one panel argument in `h3xM9A9uIyY`).

Never raised: Holodomor, DPRK, Hong Kong, Syria chemical attacks, Iran protests, color revolutions, sanctions, the
"labor aristocracy", and the claim that the US is fascist by nature (FASC-01). These are exactly the state-defense
and Marxist-Leninist history entries that mark the core faction in Balci et al. They are absent because the videos
argue about American party politics.

The 18 asserts are thin. They are:
- Hasan Piker clips: 6. Four are from his China streams (CHN-04, CHN-06 twice, EMP-08). One is "I hate America",
  meant as domestic criticism. One sarcastically defends Palestine Action's sabotage of RAF aircraft (no id fits).
- Two left guests in one panel accusing Democrats of genocide: 5 (LIB-02).
- Second-hand material: a candidate statement read aloud (UKR-01), a CNN article (FASC-11), a documentary
  interviewee (FASC-03) and a tweet (LIB-01).
- Keith Edwards on the Democratic Party: 2 (LIB-01).
- A panelist calling anti-DSA panels "McCarthyism": 1 (LIB-03).

Treat even these as examples of the talking points being said aloud, not examples of campism.

## 3. The tests, and what the research says about each

Grouped by idea. "Videos" counts the distinct videos where the idea appears. Research labels: **supported** means a
source in `sources.csv` measured or documented the same thing; **consistent** means the direction fits but no one
tested it; **none** means no source addresses it; **conflicts** means a source points the other way.

| # | Test (as stated in the videos) | Videos | Where | Research |
|---|---|---|---|---|
| T1 | Selective anti-imperialism: "not anti-imperialism, just anti-American wars" | 4 | KXslvrBBCyo 00:28:32, 01:54:33; YHc1nsVqxkI 02:55:37; UszLyg0TfGk 01:20:18; DGs4Nq4dOEw 00:16:56 | **Supported.** This is the definition of campism (campism-refs, Tempest 2026) and MOVE-05. Balci et al. find a "Russian line on Ukraine" vocabulary axis. |
| T2 | Ukraine/Palestine asymmetry: "peace" and "more diplomats" for Ukraine, "end the occupation" for Palestine | 2 | YHc1nsVqxkI 02:00:14, 02:21:58; KXslvrBBCyo 01:54:33, 02:06:52 | **Consistent.** Follows from T1, but no source measures the asymmetry itself. A good candidate for a new move (section 5). |
| T3 | Class reductionism: they "disdain identity politics" and reduce everything to class | 4 | z_mHlhhc4Hg 00:06:36, 01:28:16, 02:09:28; UszLyg0TfGk 00:22:20; tkab3gPpXjA 01:33:57; EsJK1qI4zks 00:17:16 | **Consistent, but not specific.** Balci et al. find tankie subs below other far-left subs on healthcare, housing, unions and policing. But Trotskyists, anarchists and the "dirtbag" populist left also reduce things to class, so this separates Marxists from progressives, not campists from anti-campists. |
| T4 | Liberals and Democrats as the main enemy; the attacks start right after Democratic wins | 14 | KaxwDXVtTiw 00:04:06, 00:11:18; DGs4Nq4dOEw 00:19:10; tkab3gPpXjA 01:00:46, 02:31:33; z_mHlhhc4Hg 00:34:05 | **None.** This is LIB-01 and MOVE-08, both tier 2. Criticizing Democrats is common (GenForward: 79% of 18-42s say democracy is in crisis), so the marker is the target and the timing, not the criticism. |
| T5 | Ride-or-die team defense: support depends on "do you like my streamer", not on positions | 5 | jTnsRrJMHnw 00:48:49; KaxwDXVtTiw 00:03:36; DGs4Nq4dOEw 00:18:13; EsJK1qI4zks 01:14:11; z_mHlhhc4Hg 01:35:53 | **None.** Destiny says the far right does the same (tkab3gPpXjA 00:29:12, z_mHlhhc4Hg 01:12:22), so by his own account it marks partisanship, not a faction. |
| T6 | Two faces, entryism, "mask on": moderate in liberal venues; "clean break" and "dirty break" strategy | 3 | KXslvrBBCyo 01:04:49, 01:05:22; tkab3gPpXjA 02:26:28, 02:53:25, 03:11:17; DGs4Nq4dOEw 00:21:12, 00:31:34 | **None.** "Dirty break" is a strategy term from DSA-caucus and Jacobin writing (from memory, not checked here), so the term is real. Whether a given person is hiding their views cannot be tested from text. See T12. |
| T7 | The pro-America test: can they say America is a force for good ("NATO good")? | 3 | DGs4Nq4dOEw 00:35:05, 00:35:25; NEF0VNPZ7lU 00:15:07; YHc1nsVqxkI 03:15:34 | **None** (MOVE-04). It also catches people who simply dislike patriotism. It fits public figures' stated positions, not anonymous comments. |
| T8 | Every disagreement is "manufactured consent", lobbying, the CIA or Mossad; all bad news about China is "rumors and lies" | 3 | cI-qIFHwkEE 00:24:29, 01:06:53; NRxAPM8UDlw 00:06:06; EsJK1qI4zks 01:51:54 | **Supported for the China half.** It is MOVE-02, one-directional skepticism, and Balci et al. measured the asymmetric source-sharing behind it (60% state-media links). The domestic half (EMP-08) is common across the left and not specific. |
| T9 | The Mao and Stalin line: whether the coalition "supports Mao and Stalin" | 4 | z_mHlhhc4Hg 00:14:15, 00:34:35; UszLyg0TfGk 00:54:23; NRxAPM8UDlw 00:01:00; v4G3BQXJYy8 00:56:01 | **Supported.** Stalinism is one of Balci et al.'s seven vocabulary axes (HIST-02). It is also the line the anti-campist guests draw themselves ("pro Mao or Lenin, you're out"). |
| T10 | Calling Hamas or the Houthis "the resistance" is a normative endorsement | 4 | YHc1nsVqxkI 03:05:49, 03:07:22; v4G3BQXJYy8 00:14:23, 00:58:02; tkab3gPpXjA 01:16:38; rNpMQscXNF4 00:00:00 | **Consistent.** RES-01, and "the resistance" is already in `vocabulary.csv` with a caution. Balci et al. rank tankies first on Israel-Palestine. Most pro-Palestinian speech is outside the lexicon by design. |
| T11 | China travel and state-media appearances (a CGTN interview, praise of the planned economy) | 3 | NRxAPM8UDlw 00:03:31, 00:08:08; LxzUiRRhVkw 00:01:36; tkab3gPpXjA 00:45:28 | **Supported in general.** Liang & McNamee 2026: Beijing promotes sympathetic Western influencers, with partial effects. Whether any one trip was sponsored is a factual question the videos assert but do not show. |
| T12 | Absence as evidence: no pro-NATO statement means anti-NATO; "calls for peace" are a dog whistle; "social dems" are communists in disguise | 2 | YHc1nsVqxkI 02:42:28, 02:43:29; tkab3gPpXjA 02:47:15 | **Conflicts** with the method. Mendelsohn et al. and Kruk et al. treat a dogwhistle as a coded term with an in-group meaning, shown in examples. A missing statement is not a term. The debate opponent disputes it on the spot (02:42:28). Do not code it. |
| T13 | Leaders and members differ: most DSA voters are "just progressive" and "85 or 95%" vote Democratic | 5 | DGs4Nq4dOEw 00:18:43; UszLyg0TfGk 01:14:42, 01:19:17; tkab3gPpXjA 00:38:25; YHc1nsVqxkI 03:27:20; z_mHlhhc4Hg 00:07:37 | **Consistent.** In Balci et al. the tankie core sits at the edge of the far-left network. The debate opponent says the same and cites data (YHc1nsVqxkI 01:32:13). |
| T14 | Loss denial: the DNC "robbed Bernie", and every primary loss is AIPAC money | 2 | tkab3gPpXjA 00:51:37, 01:18:39; z_mHlhhc4Hg 00:33:04 | **None.** This is populist, not campist. The AIPAC version can overlap with antisemitic tropes, which `docs/hasan-israel-control-conspiracy-results.md` treats separately. Some of the facts behind it are real (2016 DNC emails, large AIPAC spending in 2024 primaries). |
| T15 | Seeding vocabulary: Marxist terms ("contradictions of capital", "revolutionary potential") used on stream so the content can follow later | 2 | tkab3gPpXjA 00:39:26; v4G3BQXJYy8 00:58:33 | **None** for the claim about intent. The terms themselves are measurable (section 5). |

### Which tests mark campism and which mark something else

Put against the lexicon's rule (campism is three things together: the US illegitimate by nature, defense of opposed
states or armed groups, liberals as the main enemy), the fifteen tests fall into three groups:

- **Campism markers** (opposed states, plus the US as the only imperialist): T1, T2, T8 (the China half), T9, T10, T11.
  These are where the videos and the research agree most.
- **Markers of the Marxist and populist left in general:** T3, T4, T5, T6, T13, T14, T15. These are most of the
  videos' content. They separate socialists from liberals and progressives, which is Destiny's main concern. They do
  not separate campists from the anti-campist left, which is the lexicon's main concern.
- **Not usable as markers:** T7 (fits public figures' stated positions only) and T12 (absence as evidence).

The lexicon should take its markers from the first group. If the second group went into the tagger, it would count
people who criticize Democratic leadership from the left, most of whom are not campists. Destiny's own T13 says as
much.

## 4. Where the videos and the research disagree, or leave a gap

**Two theories of what holds the faction together.** Smith says anti-Americanism is the core and everything else is
negotiable: "That's the litmus test, is whether or not you like America" (DGs4Nq4dOEw 00:35:25). Destiny mostly
argues from class: socialists hide "under the progressive umbrella" but "have a huge disdain for identity politics"
(z_mHlhhc4Hg 00:06:05, 00:06:36). He adds a second objection, foreign subversion (tkab3gPpXjA 00:06:06). The theories
make different predictions about text. Under Smith's, anti-American language should travel with defense of opposed
states. Under Destiny's, it should travel with anti-identity-politics language. Balci et al.'s topic finding (states
over social issues) fits both. This is testable (H2 in section 6).

**Foreign direction.** Destiny speaks of actors "colluding with and coordinating with like the enemies of America"
(tkab3gPpXjA 00:06:06). He also says Hasan Piker has been more "intentional" "ever since he came back from China"
(00:45:28). Smith, in the conversation the lexicon is built on, says "they're much more autonomous than that"
(DGs4Nq4dOEw 00:23:28). The research sides with Smith on what is shown:
- NCRI 2024 and the New York Times documented Singham funding of CAMP organizations, but not direction.
- Liang & McNamee find state promotion of influencers works only partly.
- The videos contain no evidence of coordination. They contain the accusation.

The lexicon's rule stands: overlap with state messaging means the same claim, not direction by a state.

**The target population.** Balci et al. measured six openly Marxist-Leninist subreddits. The videos are about DSA
leadership, Twitch and YouTube personalities, and Democratic primaries, which is the POP faction in `factions.csv`
plus DSA. Neither the research nor the videos covers the overlap: how much of the streamer left's audience holds the
tier-1 positions. Destiny thinks little of it (T13). The lexicon's known-group check expects r/Hasan_Piker and r/dsa
to sit between the tankie subs and r/neoliberal. These videos give no reason to change that expectation.

**Israel and Palestine.** Four of the twenty videos are mostly about Israel (`VL3gu403rVs`, `rNpMQscXNF4`,
`h3xM9A9uIyY`, `INnln13RMnM`), and most of their rows have no talking-point id. That is by design. The lexicon
leaves out ceasefire and genocide claims (section 3 of the lexicon doc). Destiny's objections there are mostly about
wording ("ethnic cleansing" vs. "population transfer", rNpMQscXNF4 00:41:54) and history (the Clinton parameters,
VL3gu403rVs 00:25:19), not campism. Only "the resistance" (T10) and the reach of the Iran-led axis (VL3gu403rVs
00:47:12) connect to the lexicon.

**The anti-campist left is visible, and it is DSA-adjacent.** Four passages show the counter-class (ANTICAMP) that
the lexicon most needs to avoid mislabeling:
- A DSA member on a panel wants "the more toxic elements like campus [campists] and um tankies" pushed out
  (KXslvrBBCyo 00:06:03).
- Dylan Burns attacks the DSA co-chair's Ukraine line: "They're not internationalists" (KXslvrBBCyo 02:06:52).
- A democratic-socialist guest: "I do no apologetics for" China, Cuba or the USSR (z_mHlhhc4Hg 00:01:32).
- A caller: "If you're like pro Mao or Lenin, you're out" (UszLyg0TfGk 00:54:23).

This matches our own glossary finding that "campist" is used most by r/dsa regulars (13.2 per 10,000 comments). The
people who say "imperialism" most and the people who say "campist" most will often be in the same subreddit.

**The videos warn against their own overreach.** Destiny answers the "McCarthyism" complaint with "The reason why
it's the boy who cried wolf is not because there are no wolves" (tkab3gPpXjA 03:24:33). The same point cuts against
T12: when moderation and silence count as evidence, the label stops meaning anything.

## 5. Candidates for the lexicon (not added)

None of these is in the data files yet. Each would need every column filled in, and a blind read before it counts
toward anything (lexicon doc, section 7).

| Candidate | Kind | Source | Why | Caution |
|---|---|---|---|---|
| MOVE-11 Peace for Ukraine, liberation for Palestine | rhetorical move | T2 | The most specific campism test in the videos. It is a contrast within one speaker, so it can be checked in text. | Needs both halves from the same author or thread. Wanting a ceasefire in both wars is not this move. |
| MOVE-12 Disagreement as manufactured consent | rhetorical move | T8 | Explains away all opposition as propaganda. Pairs with MOVE-02 and EMP-08. | "Manufactured consent" is also an academic term (Herman and Chomsky). Count it only when it replaces an answer to the argument. |
| "dirty break", "clean break" | vocabulary | T6 | DSA-internal strategy terms with little ordinary meaning. | They mark DSA strategy talk, not campism. Factions: POP, DSA caucuses. Specificity: high for the faction, low for campism. |
| "revolutionary potential", "contradictions of capital" | vocabulary | T15 | Marxist register (ML, ANTICAMP, academics). | Shared by every Marxist tendency. Tier 2 at most. |
| "mask on" / "mask off", "entryism", "tankie" | counter-class vocabulary | T6 | Used by critics of the faction. | Add only as counter-class markers. A rise in these marks people arguing with the faction, as on r/Destiny. |

The lexicon already has the terms the videos use for China and Hamas: "the resistance", "succdem", "westoid",
"electoralism", "uniparty", "vote blue". The videos add no new state-defense vocabulary. That is expected, since no
one in them defends those states at length.

## 6. What could be tested on our data (each needs a predictions file first)

These come from the videos' claims. They are written as questions, not predictions. A `*-predictions.md` with
expected orderings must be committed before any data is run or read.

- **H1, asymmetry (T2).** In communities where both wars come up, is "peace / negotiations / diplomacy" used for
  Ukraine more often than for Palestine, and "liberation / end the occupation / resistance" more for Palestine?
  Compare r/TankieTheDeprogram, r/dsa, r/Hasan_Piker, r/socialism and r/neoliberal, per community.
- **H2, which core (section 4).** Within the far-left communities, does anti-American language co-occur more with
  defense of opposed states (Smith's theory) or with anti-identity-politics language (Destiny's)? This needs a small
  term list for each side, frozen in the predictions file.
- **H3, post-win timing (T4, MOVE-08).** Does anti-Democrat volume in left subreddits rise in the week after
  Democratic wins (Nov 2026 midterms)? Already listed in the lexicon doc.
- **H4, leaders vs. members (T13).** At the community level, are tier-1 rates in r/dsa close to r/neoliberal and far
  below the tankie subs, as Destiny's own caveat implies? This is the known-group check in section 7 of the lexicon
  doc, with the videos' expectation stated in advance.
- **H5, counter-class (section 4).** Is "campist" or "tankie" use highest in the same communities where tier-2
  imperialism vocabulary is high (r/dsa), as the videos' anti-campist guests suggest?

All five are community-level. None needs, or permits, a per-account label (CLAUDE.md rule 5). H1 and H2 can use
`antiwest_tag.py` only after its predictions file is committed.

## 7. Limits

- **A sample of opponents.** Destiny, Noah Smith and most guests oppose the faction. The few left speakers appear in
  clips or debates chosen by Destiny's side. This shows how critics recognize the faction, not how the faction
  describes itself.
- **A title-filtered sample.** The 20 videos are the earlier search queue plus 8 of 86 recent channel uploads picked
  by title (`docs/antiwest-lexicon.md`, section 6). Ten are older than three months or come from clip channels. The
  counts in section 2 describe this index, not Destiny's output.
- **Hand-indexed.** The passages were picked and tagged by Claude reading the transcripts, one reader per video, with
  no second coder. The tagging is loose in places (the readers flagged HIST-02 for Mao, UKR-05 for a point about the
  right, and LIB-01 for several close fits). Treat the talking-point counts as rough.
- **Speaker attribution.** Caption transcripts have no speaker labels, and in reaction videos Destiny and the clip run
  together. 182 rows are attributed to Destiny. Some of those may be panel audio.
- **Claims about named people are the speakers' claims.** The videos make specific accusations about public figures:
  China trips, praise of attacks, endorsed candidates' statements. This document reports them as said, not as true.
  None should be repeated without the original source.
- **Machine transcripts.** Names are misheard ("Medhi Hasan", "Rashidita Talib"; the DSA panelist's "campus" means
  "campists"). Quotes are verbatim from the transcript, which is not always verbatim from the video.

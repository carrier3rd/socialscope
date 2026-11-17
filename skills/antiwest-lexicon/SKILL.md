---
name: antiwest-lexicon
description: Identify campist ("tankie") anti-American and anti-Western talking points in text, say which faction each comes from, and maintain the lexicon, transcripts and timestamp index behind it. Use when asked to tag or count anti-Western talking points in Reddit, chat or video data, to explain where a phrase like "critical support" or "imperial core" comes from, to tell tankies from progressives or from the anti-campist left, to transcribe a Destiny (or other) YouTube video from the cloud session, or to add terms, talking points, sources or timestamped video segments to data/antiwest/.
---

# Anti-Western talking-point lexicon

Everything lives in `data/antiwest/`. The human-readable guide is `docs/antiwest-lexicon.md`; read its sections 2 and
7 before producing any number.

## The rule that prevents most mistakes

Criticism of the United States is not the target. The target is **campism**: siding with whatever opposes the US.
It shows as three things together: the US as illegitimate by nature, defense of states or armed groups opposed to
it, and liberals as the main enemy. One alone is not enough.

Two groups share the vocabulary and must not be counted:
- the anti-campist far left (ANTICAMP), who say "imperialism" constantly and also condemn Russia and China;
- anyone quoting, mocking or disputing a talking point. On r/Destiny most hits will be this.

## Files

| File | Key columns |
|---|---|
| `factions.csv` | `id`, `marker_vocabulary`, `do_not_confuse_with` |
| `talking_points.csv` | `id` (e.g. `UKR-02`), `claim`, `cue_phrases` (`;` separated), `factions`, `tier`, `basis_in_fact`, `what_marks_it` |
| `vocabulary.csv` | `term`, `variants` (`;` separated), `factions`, `specificity` (high / medium / low), `caution` |
| `rhetorical_moves.csv` | `id` (e.g. `MOVE-04`), `what_it_looks_like`, `source`, `caution` |
| `sources.csv` | `finding`, `used_for`, `how_checked` |
| `transcripts/<video_id>.txt` | header lines starting `#`, then `[HH:MM:SS] SPEAKER: text` |
| `transcripts/index.csv` | one row per transcript |
| `vod_segments.csv` | `video_id`, `start`, `url` (opens at that second), `kind`, `talking_points`, `summary`, `quote`, `quote_ok` |
| `vod_queue.csv` | videos found but not transcribed, with the reason |

Tiers: 1 campist-specific, 2 far-left general, 3 shared with the isolationist right and mainstream realists.
Tier 0 (ordinary criticism) is deliberately absent from the table.

## Tasks

### Explain a phrase or a comment
1. Look the phrase up in `vocabulary.csv` and `talking_points.csv`.
2. Answer with: what it means, which factions use it, the tier, what is true in it (`basis_in_fact`), and what would
   make this use a marker (`what_marks_it`, `caution`).
3. Say when the context points to a counter-class (dispute, quote, joke, ANTICAMP).

### Tag a dataset
1. Write and commit a `docs/<name>-predictions.md` first (CLAUDE.md rule 3). Predict the ordering of communities.
2. Run `python3 scripts/antiwest_tag.py '<files>' --by subreddit -o out/<name>.csv --examples 5`.
   Input can be transcripts (`.txt`) or Reddit dumps (`.zip`, `.zst`, `.jsonl`). Quoted lines are dropped.
3. Blind-read a random sample of hits per community and code assert / dispute / quote / joke. Report rates only for
   entries that pass the project's bar, and report the precision next to the rate.
4. Report per community. Never output or store a per-account label; never link accounts across platforms.
5. Use the explain-analysis skill for the write-up.

### Get a video transcript in the cloud session
YouTube, yt-dlp and transcript sites are blocked here. Gemini can read public YouTube videos.
1. Find the video ID with WebSearch (channel pages cannot be fetched). Search results often give re-uploads; that
   is fine when the original returns HTTP 403.
2. `python3 scripts/yt_gemini_transcript.py <id> [<id> ...]` writes `data/antiwest/transcripts/<id>.txt` and updates
   `index.csv`. Use `--fill` to retry ranges marked `# MISSING`.
3. Quota: free tier, 20 requests per model per day; one request per 30-minute window plus one per video, so about
   five hour-long videos a day. Use the default model (gemini-3.5-flash). Other models stopped early on long videos
   in testing; if you use one, compare the last timestamp with the video's real length and discard partials.
   Record what was not fetched in `vod_queue.csv`, and remove rows from it as they are done.
4. On the laptop, use yt-dlp captions instead (`scripts/transcript_chunks.py`).
5. These are machine transcripts. Say so wherever they are quoted, and check a quote against the video before it is
   published.

### Index a transcript
1. `python3 scripts/transcript_segments.py data/antiwest/transcripts/<id>.txt` asks a model for the passages and
   checks every quote against the transcript. The lite models find few passages; prefer reading the transcript and
   writing rows by hand.
2. Hand-written rows go in a CSV with columns `video_id,start,speaker,kind,talking_points,summary,quote,indexed_by`
   and are added with `--add rows.csv`, which verifies the quotes (a quote must be at least 6 words and within two
   minutes of `start`).
3. `kind` is one of identify / factions / assert / rebut. Summaries attribute the claim ("Destiny argues...").
4. Do not cite a row with `quote_ok` 0.

### Add or change lexicon entries
- A new talking point needs all columns, including `basis_in_fact` (what real facts it leans on) and
  `what_marks_it`. If you cannot say what separates it from ordinary criticism, it is tier 0 and does not go in.
- A new term needs a `caution` if it has any ordinary meaning. Short all-caps terms (AES, CPC, NED) are matched
  case-sensitively by the tagger.
- A new source needs an honest `how_checked` (read in full / abstract / search summary / from memory).
- After editing, run the tagger's self-check: `echo "critical support for the DPRK" | python3 scripts/antiwest_tag.py -`.

## Standing limits (state them in any output)

- v1 is untested on our data: no entry has a measured precision.
- The Destiny and Noah Smith material is two opponents' account of the faction; it is in the lexicon as hypotheses.
- A hit is not evidence that an account is a bot, is foreign, or is coordinated.
- Overlap with state media means the same claim, not direction by a state.

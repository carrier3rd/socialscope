# RAM fault checks (Nov 11 2026, laptop session)

The user asked for three checks: test the RAM, verify old_last, and check the outputs written on Nov 9 while the fault
was active. Results, misses included.

## 1. RAM test

No memtest (that needs a reboot and someone at the keyboard), so a userspace pattern test instead
(scratch `rt.c`: 5,000 MB, 12 passes of address-mixed, alternating-bit and inverted patterns).

- **67 bad 64-bit words, found on 11 of 12 passes.** Every error is one flipped bit (xor 0x20, 0x40, 0x100, 0x800,
  0x8000), always 0 -> 1 or 1 -> 0 in the same few bit positions, at the same few addresses each pass. Most sit in one
  ~32 KB stretch. That is a hard fault in a fixed set of cells, not random noise, and it's the same kind of flip seen
  in the data ("areated_utc", "num_cnmments").
- Page-cache reads still fail: `fwd_comments.zip`, `round4_comments.zip` and `insub_posts.zip` fail their CRC when read
  through the cache and pass when read with O_DIRECT. The disk is fine.
- The kernel log has had more python3 segfaults (five on Nov 10, at :08 past the hour, during glossary builds).
- A clean userspace test wouldn't have cleared the RAM (it only sees free frames); this one didn't come back clean.

**Stopgap:** `~/socialscope_data/tools/badpage_hold` (source next to it) tests ~7 GB of free RAM, `mlock`s every 4 KB
page with a flip so the kernel can't reuse it, frees the rest and sleeps. Started Nov 11 09:35 EST, holding 9 pages
(36 KB); PID in `badpage_hold.pid`. It does not survive a reboot and only covers frames that were free when it ran.
The real fix is replacing or reseating the RAM stick (the memtest run would show which stick), or a `memmap=` boot
option, which needs root.

## 2. old_last

Reproduced byte for byte on Nov 11 (features, per-account scores, results). Details in the addendum to
docs/repull-results.md. Four tries without `badpage_hold` all failed while loading input; the first try with it passed.

## 3. Outputs written Nov 9

| Output | Check | Result |
|---|---|---|
| Week zips, Oct 27 and Nov 3 weeks (72 files, 853,827 records) | O_DIRECT read, every record parsed; key names, created_utc in range, subreddit, id format | 71 files clean. **`oct27/…/r_h3h3productions_comments_2026-10-27_to_2026-11-02.zip` has 3 corrupted key names** (`num_cnmments`, `_leta`, `to4al_awards_received`), stored that way on disk; its zip CRC passes because the flips happened before the zip was written. Values in that file may be flipped too, undetectably. It should be re-pulled once the RAM is fixed. |
| Bulwark captions (120 .vtt files from Nov 9) | UTF-8, WEBVTT header, cue timestamps well-formed and in order, no control characters | all 120 pass. A flipped letter inside caption text wouldn't show up in this check. |
| Gemini chunks (2,595 files) | chunker rerun into a scratch folder, sha256 compared | all 2,595 identical |

The other 71 week files passing these checks means no corrupted key names or dates were found; a flip inside a text
value would pass. The only way to rule that out is re-pulling, which is a judgment call for each file.

## Addendum, Nov 11 2026 evening (laptop session)

- **badpage_hold is now a boot service** (`ops/laptop/badpage-hold.service`, source `ops/laptop/badpage_hold.c`,
  enabled in systemd --user with linger, ordered before dgg-live). After the 18:04 reboot it found only 1 bad page;
  a second run 5 minutes later (`badpage-hold-extra`, a transient unit that won't come back after a reboot) found 6.
  So the flips come and go with conditions, probably temperature, and one boot-time scan doesn't find them all.
  Both stay running.
- **h3h3productions comments, Oct 27 week: re-pulled and replaced.** The new copy (95,537 comments) passes the record
  check (`scripts/integrity/week_records.py`). Record by record against the old copy
  (`scripts/integrity/cmp_pulls.py`): 57,414 identical; 35,640 differ only in fields that change between pulls
  (score, ups, num_comments, score_hidden, locked, `_meta`), plus the three corrupted key names and one changed
  link_url/link_permalink pair in the same record as `num_cnmments`, almost certainly flips too. 2,483 comments are
  new; 66 are gone (deleted since). The old copy is kept beside it as `.zip.ramcorrupt_nov9`.
- The checkers now live in `scripts/integrity/` (the scratch copies were lost when the reboot cleared /tmp).

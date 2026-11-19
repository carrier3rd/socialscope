# Bluesky module: Phase 1 runbook for the laptop session (24-hour pilot)

Written Nov 19, 2026 by the cloud session. The cloud session cannot run jobs; everything here runs on the Linux
laptop. Decisions this follows are the owner's of Nov 19 (data in `~/socialscope_data/bluesky/`, own venv, window
starts the day the pilot passes).

## What was and wasn't tested before this reached you

| Piece | State |
|---|---|
| `jetstream.py` filter, hour files, cursor, resume | Tested on synthetic events. The connection loop itself has not run against Jetstream. Checked live: both hosts accept a cursor, replay about 37 hours, answer websocket pings, and send identity and account events whatever the collection filter. |
| `appview.py resolve` | Run live Nov 19: 22 handles checked, 0 mismatches. |
| `appview.py threads / profiles / histories`, `plc.py`, `backlinks.py` | Tested on synthetic responses only. No thread, profile batch, history, PLC log of a replier or backlink has been fetched. |
| `labels.py` | Tested on synthetic frames only. **Never connected to a labeler.** Treat its first run as a test (step 7). |
| Python 3.14 | Not tested. The cloud container has 3.13. All three pinned libraries publish 3.14 wheels. |

## Before you start

Stop and ask the owner if either is missing:

1. `docs/bluesky-politics-predictions.md` is **committed**. `git log --oneline -1 -- docs/bluesky-politics-predictions.md`
   must print a commit. Nothing below reads data until it does (CLAUDE.md rule 3). `pilot_check.py` refuses to run
   without it.
2. The owner has confirmed the `government_right` list in `bluesky/config/targets.yaml`. It is marked CANDIDATES.

## Steps

**1. Pull and build the venv.**

```bash
cd ~/socialscope && git status && git pull
```

```bash
python3 -m venv ~/socialscope_data/bskyenv && ~/socialscope_data/bskyenv/bin/pip install -r ~/socialscope/bluesky/requirements.txt
```

```bash
~/socialscope_data/bskyenv/bin/python --version
```

If pip tries to compile anything on 3.14, stop and say which package. After any OS upgrade the venv needs the same
rebuild as liveenv (ops/laptop/README.md).

**2. Run the tests.** Expect 26 tests, OK.

```bash
cd ~/socialscope && ~/socialscope_data/bskyenv/bin/python -m unittest test.test_bsky_collect
```

**3. Check the targets still resolve.** Expect `"mismatches": []` and exit code 0.

```bash
~/socialscope_data/bskyenv/bin/python -I ~/socialscope/bluesky/collect/appview.py resolve
```

**4. Add the jobs.tsv lines.** Same seven columns as the repull lines in `scripts/repull_run/RUNBOOK.md`; check
them against the file's current header first.

```bash
printf 'bsky_pilot\tbluesky\tbsky_pilot_queue.sh\tbsky_pilot_queue.out\tbsky_pilot start\tbsky_pilot end\tbluesky_status/status.json\n' >> ~/socialscope_data/jobs.tsv
```

```bash
printf 'bsky_pilot_passes\tbluesky\tbsky_pilot_passes.sh\tbsky_pilot_passes.out\tbsky_pilot_passes start\tbsky_pilot_passes end\tbluesky_status/passes.txt\n' >> ~/socialscope_data/jobs.tsv
```

Add a line to `status.sh` that reads `~/socialscope_data/bluesky_status/status.json` (fields: `connected`,
`lag_seconds`, `repliers`, `megabytes_received`).

**5. Launch.** Recorder first, then the hourly passes.

```bash
cp ~/socialscope/ops/laptop/bsky_pilot_queue.sh ~/socialscope/ops/laptop/bsky_pilot_passes.sh ~/socialscope_data/
```

```bash
cd ~/socialscope_data && nohup systemd-inhibit --what=idle:sleep --mode=block --who=socialscope --why="bluesky pilot recorder" ./bsky_pilot_queue.sh > bsky_pilot_queue.out 2>&1 &
```

```bash
cd ~/socialscope_data && nohup systemd-inhibit --what=idle:sleep --mode=block --who=socialscope --why="bluesky pilot passes" ./bsky_pilot_passes.sh > bsky_pilot_passes.out 2>&1 &
```

Optional status page, serving only the status folder (rule 7; 8765-8767 are taken):

```bash
nohup python3 -m http.server 8768 --directory ~/socialscope_data/bluesky_status > ~/socialscope_data/bluesky_status_server.log 2>&1 &
```

**6. After 10 minutes, then after 1 hour, look at `status.json`.**

- `connected` true, `lag_seconds` under 10.
- `counts_since_start` has `seen:` counts for all six collections and `kept:` counts far smaller than `seen:`.
- `repliers` is growing; `other_authors_seen` is much larger than `repliers`.
- `megabytes_received` after one hour, times 24, is the daily download. The stream is the whole network for six
  collections and has not been measured: if a day projects past what the connection or disk can take, stop the
  job and say so rather than let it run. Disk use is far smaller than download (only kept events are written).
- `du -sh ~/socialscope_data/bluesky` after one hour, times 24 times 21, must fit on the disk for the window.

**Kill test (required by the spec), any time after the first hour:**

```bash
kill -9 "$(cat ~/socialscope_data/bluesky/state/jetstream.pid)"
```

The queue script restarts the recorder within 10 seconds. Check `status.json` a minute later: `connected` true,
and `lag_seconds` back under 10 once it has replayed what it missed. A session writes its line to
`sessions.jsonl` only when it ends, so the killed session leaves no line; the one after it records the cursor it
resumed from and how far its first event was from that cursor (`resume_gap_s`, which should be near 0).

To stop the pilot early: `kill` (not -9) the two `bsky_pilot_*.sh` shells by PID, then the recorder by its PID
file. Say in STATUS.txt and jobs.tsv that it was stopped and why (rule 9).

**7. Labels, as a separate job, any time during the pilot.** First a 200-frame test per labeler:

```bash
~/socialscope_data/bskyenv/bin/python -I ~/socialscope/bluesky/collect/labels.py --max-frames 200
```

Expect, per labeler, `"ended": "frame limit"`, `kept` plus `dropped` above zero, and a `to_seq` above zero.
`"ended": "failed: ..."` or `"error frame"` means the untested stream code is wrong: stop and report the message.
If the test is clean, run the full replay under nohup with its own jobs.tsv line (name `bsky_labels`). The
Bluesky moderation stream is large and may take hours; it resumes from `cursor.json` if interrupted. Only
whitelisted values are written; everything else is counted by month in `counts.json`.

Nothing reads the antibot4navalny lists yet (not a labeler; tier undecided, see targets.yaml).

**8. When 24 hours are up.**

```bash
~/socialscope_data/bskyenv/bin/python -I ~/socialscope/bluesky/collect/pilot_check.py
```

It prints PASS or FAIL for: 24 hour files, a resumed session, no gap on resume, and no run of 5 minutes or more
with 429s on any host. Paste its output into STATUS.txt.

If it prints `PILOT PASSED`:

- Start the standing recorder straight away so the window has no gap (it resumes from the pilot's cursor):

```bash
cp ~/socialscope/ops/laptop/bsky-recorder.service ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now bsky-recorder
```

- Set `window.start` to that day (UTC) and `window.end` to 21 days later in `bluesky/config/targets.yaml`,
  commit and push. Pilot days stay development data.
- Mark both pilot jobs done in jobs.tsv and STATUS.txt.

If it does not pass, change nothing in the window, report which check failed with its numbers, and leave the
data in place.

**9. Also record, for Phase 6:** the scikit-learn version that wrote `~/socialscope_data/repull/out/model_repull.pkl`
(RECON 3.4). Put it in STATUS.txt.

## Where things are

| Path | What | Private? |
|---|---|---|
| `~/socialscope_data/bluesky/raw/jetstream/` | hour files, `sessions.jsonl` | yes (DIDs, text) |
| `~/socialscope_data/bluesky/raw/{threads,profiles,histories,plc,constellation,labels}/` | AppView, PDS, PLC, Constellation, label data | yes |
| `~/socialscope_data/bluesky/state/` | cursor, replier sets, PID file, pilot end time | yes |
| `~/socialscope_data/bluesky/logs/requests_*.jsonl` | requests per minute by status code, no URLs | counts only |
| `~/socialscope_data/bluesky_status/` | `status.json`, `passes.txt` | counts only; the only folder a server may serve |

Nothing under `~/socialscope_data/bluesky/` is ever committed. Outputs, logs and messages carry counts or
hashed ids: no DID and no handle (the owner, Nov 19 2026).

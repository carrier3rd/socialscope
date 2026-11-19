# Bluesky module: what Phase 1 preparation verified (Nov 19, 2026, cloud session)

Config lookups only. No reply thread, like, follow, block, label or account history was read.

## Reachability from the cloud container

| Host | Result |
|---|---|
| public.api.bsky.app | reachable |
| plc.directory | reachable |
| constellation.microcosm.blue | reachable |
| mod.bsky.app | reachable (`/xrpc/_health` 200) |
| jetstream1.us-west.bsky.network | reachable, websocket opens |
| jetstream2.us-east.bsky.network | reachable, websocket opens |
| ozone.skywatch.blue | reachable after the owner approved it (`/xrpc/_health` 200) |
| account PDS hosts (`*.host.bsky.network`) | blocked here. `bsky.social` answered `listRecords` for the one account tried |

## Findings

1. **Spec handles.** All four resolve. `whitehouse.gov` resolves to did:plc:iw2wxg46hm4ezguswhwej6t6, whose own
   handle is `whitehouse-47.bsky.social`. DIDs are in `config/targets.yaml`.
2. **Labelers.** Bluesky moderation: label host `mod.bsky.app`. Skywatch: label host `ozone.skywatch.blue`.
   **antibot4navalny is not a labeler**: did:plc:6vblwh2edno4ayc2mku72r7e has no labeler service in its DID
   document, its PLC log never had one, and its profile says `labeler: false`. It has 7 lists. So there is no
   label stream to replay for it, and its tier needs a decision (the spec calls its labels Tier A and community
   lists Tier C).
3. **Skywatch's declared values differ from the spec's list.** Declared on Nov 19: 34 values. Of the spec's
   whitelist, 8 are declared; `repetitive-domain-spam-*` is not. Declared and behavioral-looking but not on the
   spec's whitelist: `low-quality-replies`, `disinformation-network`, `discourse-bait`, `fundraising-link`,
   `prediction-betting`. They are counted and dropped unless the owner adds them.
4. **Jetstream replay buffer: about 37 hours.** Asking for cursor 1 returned a first event 36.8 hours old on
   us-west and 37.2 hours old on us-east. A cursor one hour back returned an event exactly one hour old on both.
   The server answers websocket pings (connection held 78 s on library defaults). Identity and account events
   arrive whatever `wantedCollections` says.
5. **`listRecords` can start at a date.** The cursor is a record key, and a key built from a timestamp works:
   with the cursor for 2025-01-01 00:00 UTC the first record returned was dated 2024-12-30 and the page ran
   backwards from there; `reverse=true` ran forwards from 2025-01-02. Tried on the official @bsky.app account
   through `bsky.social`. `public.api.bsky.app` does not serve `listRecords` (501). Limits: record keys are
   chosen by the client, so a non-standard key breaks the ordering for that record; the record has no
   `indexedAt`; self-hosted accounts need their own PDS host.
6. **Constellation.** Current endpoints are `/xrpc/blue.microcosm.links.getBacklinks` (limit up to 100, cursor)
   and `getBacklinksCount`. A made-up subject returned `{"total":0,"records":[],"cursor":null}`. It asks for a
   project name and a contact in the User-Agent.
7. **Government/right accounts are few and small.** No `.gov` department handle resolves except `dol.gov` and
   the White House alias. Verified accounts found: White House, Homeland Security, War, HHS, Labor, Veterans
   Affairs, Interior, House Republicans, National Review, The Free Press (400 to 16,500 followers), against
   105k to 2.2M for the progressive list. State, Treasury, Transportation, Commerce and Education have 5 or
   fewer posts each.

## Not verified

- The label streams. A replay test from the cloud session was not permitted; only the health endpoints were
  checked. `labels.py` has never connected to a labeler.
- Stream volume (events or megabytes per day for the six collections).
- Rate limits of the AppView, PLC directory and Constellation. The rates in `targets.yaml` are guesses set low.
- Anything on Python 3.14.

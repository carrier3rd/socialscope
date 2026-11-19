---
name: account-lookup
description: Check one Reddit account for bot-like behavior. Pulls its history live from Arctic Shift, scores it with the frozen v7.1 model, and gives a 1-10 rating plus day-night rhythm, time-zone estimate, location mismatch, top subreddits and keywords, as a private card sent to the user. Use whenever the user asks to check, look up, score or "is this a bot" about a u/name, pastes another bot-checker's result, or asks about the site's Lookup tab.
---

# Look up one account

There are two front ends, and both run the same code, `socialscope/lookup_core.py`:

- **Laptop (this skill):** `scripts/lookup.py`. The card is private and goes to the user.
- **Public site, Lookup tab:** `site/public/lookup.js`. It runs in the visitor's browser, through Pyodide and live
  Arctic Shift. Nothing is stored or published (CLAUDE.md rule 5, "Lookup tab"). When the user wants to check an
  account themselves, point them there.

## Steps

1. **Rules first.** Read CLAUDE.md rule 5.
   - The username the user gives may be used in chat, and on the private card sent to them.
   - Never log it anywhere else. Never commit it. Never put it into a results file; use the hashed id there.
   - A rating is a lead, never proof. Never call the account a bot unless Bot Bouncer has banned it.
2. **Predictions.** If this lookup is part of an analysis (not a quick check), add a dated predictions section to
   `docs/lookup-predictions.md` before running. Put the hashed id in it (`C.H(name)`, `scripts/repull_run/common.py`).
   Additions go at the end, and nothing above them is ever edited.
3. **Run it** with the scoring venv. The system python has no numpy or sklearn.
   ```
   ~/socialscope_data/scoreenv/bin/python -I scripts/lookup.py <username>        # pulls, then scores
   ~/socialscope_data/scoreenv/bin/python -I scripts/lookup.py <username> --no-pull   # re-score the saved pull
   ```
   - It waits if another Arctic Shift pull is running.
   - Stdout prints the hashed id and numbers only. Pipe it through `sed -E 's#u/[A-Za-z0-9_-]+#u/[masked]#g'` anyway.
   - Output goes to `~/socialscope_data/lookups/<hashed id>/` (mode 700): `card.html`, `lookup.json` and the pull.
4. **Check by rerun.** Rerun with `--no-pull` and confirm the same score. The laptop has a RAM fault, so a single
   run isn't trusted.
5. **Send the card** with SendUserFile (`display: "render"`).
6. **Report** in plain words. The result is a lead, not proof. Cover:
   - the rating out of 10 and what it means: 5 = loose line, 7 = 2% line, 9 = strict line;
   - the raw score;
   - which signals fired;
   - the time-zone and mismatch read, with its caveat (shift workers, people abroad, scheduling tools);
   - where the account posts.
7. **Results** for analysis lookups go in `docs/lookup-results.md`, by hashed id, misses included.

## Data source

Arctic Shift only. Reddit's official API was tried on Nov 13 and dropped: Reddit requires approval before any API
use (Responsible Builder Policy), and the user chose not to apply. Don't add Reddit API calls or a sign-in. So a
lookup can't tell whether an account is suspended right now, and it misses anything newer than Arctic Shift's copy.

## How the numbers are made

- **Score:** the frozen v7.1 full model, exported as plain trees to `site/public/lookup/model.json` by
  `scripts/export_lookup_model.py`. The exporter refuses to write unless every one of 3,264 study accounts scores
  the same as in sklearn.
- **Features:** built as in `scripts/repull_run/feats.py`, with the anchor at the account's last item.
  `scripts/lookup_parity.py` rebuilds 400 study accounts and found every feature identical. Rerun both checks after
  any change to `history.py`, `prewindow.py`, `hijack.py`, `signals.py` or `lookup_core.py`.
- **Rating, 1-10:** piecewise linear in log10(score) through 0.0001 → 1, 5% line → 5, 2% line → 7, strict line → 9,
  1.0 → 10. It's shown to two decimals, truncated, not rounded (the user's choice, Nov 13).
- **Time-zone method, US list and mismatch rule:** frozen in `docs/lookup-predictions.md`. Changing them needs a new
  dated predictions entry first.
- **Limits:**
  - Only the newest 1,000 posts and 1,000 comments are read.
  - Arctic Shift can lag Reddit by days.
  - A lookup can never fire the `batch_id` rule, which needs other accounts scored alongside.
  - There is no interactions view, because it would list other users' names.

## Site upkeep

- `ops/publish_socialscope_site.sh` copies the Python modules into the site's `py/socialscope/` on every publish. If
  `lookup_core.py` gains an import from the package, add that module to the copy list there and to `PY_FILES` in
  `lookup.js`.
- After re-exporting the model, commit `site/public/lookup/model.json`.
- The lookup form must never submit natively. No input gets a `name`, and the form keeps `onsubmit="return false"`,
  so a username can't reach the page URL.

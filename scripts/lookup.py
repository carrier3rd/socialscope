#!/usr/bin/env python3
"""Look up one Reddit account: v7.1 score plus descriptive signals, as a private HTML card (written Nov 13, 2026).

Predictions and the frozen time-zone method: docs/lookup-predictions.md. Results of a lookup go in
docs/lookup-results.md (hashed id only).

What it does:
  1. Pulls the account's history from Arctic Shift with the re-pull cap (newest 1,000 posts and 1,000 comments, plus
     the oldest-item check), unless --no-pull and a pull is already there. Waits while another Arctic Shift pull runs.
  2. Scores it with socialscope/lookup_core.py (shared with the site): the frozen v7.1 full model as exported trees. Features are built exactly as
     scripts/repull_run/feats.py builds them, with the anchor at the account's last item. The model is not retrained.
  3. Computes descriptive signals that are NOT part of the score: the default-name pattern, the day-night rhythm and
     time-zone estimate, local subreddits, language, top subreddits and keywords, and the US-presenting / time-zone
     mismatch lead.

Privacy: everything with the username (the pull, the card, the JSON) goes to ~/socialscope_data/lookups/<hashed id>/
(mode 700, never committed). Arctic Shift's progress output, which names the user, goes to a private log there.
stdout shows the hashed id and numbers only. Other users' names are never collected: there is no interactions view.
A flag is a lead, never proof. The card never calls an account a bot.

Usage: python3 -I scripts/lookup.py <username> [--no-pull] [--cap 1000]
"""
import argparse, contextlib, html, json, math, os, re, shutil, subprocess, sys, time
from datetime import datetime, timedelta, timezone

REPO = os.path.expanduser("~/socialscope")
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "scripts", "repull_run"))
import common as C  # noqa: E402
from socialscope import arctic  # noqa: E402
from socialscope import lookup_core as LC  # noqa: E402

# Nov 13: the scoring and signals moved to socialscope/lookup_core.py, shared with the site's Lookup tab, so the two
# can't drift. Reddit API facts were added and then removed the same day: Reddit requires approval before any API
# use (Responsible Builder Policy), and the user chose to stay on Arctic Shift only. The model is the exported tree file (exact match to sklearn, see scripts/export_lookup_model.py).
OUT_ROOT = os.path.join(C.DATA, "lookups")
MODEL_JSON = os.path.join(REPO, "site", "public", "lookup", "model.json")
QUIET_HOURS = LC.QUIET_HOURS
US_SHARE = LC.US_SHARE


def private_dir(h):
    d = os.path.join(OUT_ROOT, h)
    os.makedirs(d, mode=0o700, exist_ok=True)
    os.chmod(OUT_ROOT, 0o700)
    os.chmod(d, 0o700)
    return d


def other_pull_running():
    r = subprocess.run(["pgrep", "-f", r"^(/usr/bin/)?python3 .*(from socialscope import arctic|scripts/reddit_pull.py|"
                                       r"pull_user_histories|scripts/repull_run/pull.py)"], capture_output=True)
    return r.returncode == 0


def pull(user, d, cap):
    for i in range(144):                       # one Arctic Shift pull at a time; wait up to 12 h
        if not other_pull_running():
            break
        if i == 0:
            print("another Arctic Shift pull is running; waiting", flush=True)
        time.sleep(300)
    # Fixed Nov 13 2026: pull_user_histories resumes from _parts/*.done and history_oldest.json, so a second lookup
    # of the same account silently reused the first pull (found when the site, reading live, disagreed). A lookup
    # without --no-pull now starts clean.
    shutil.rmtree(os.path.join(d, "_parts"), ignore_errors=True)
    for f in ("history_posts.zip", "history_comments.zip", "history_oldest.json", "history_overview.json"):
        if os.path.exists(os.path.join(d, f)):
            os.remove(os.path.join(d, f))
    end = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%d")
    log = os.path.join(d, "pull_log.txt")
    with open(log, "a", encoding="utf-8") as fh, contextlib.redirect_stdout(fh), contextlib.redirect_stderr(fh):
        arctic.pull_user_histories([user], end=end, max_items=cap, out_dir=d, name="history", oldest=True)
    os.chmod(log, 0o600)


def fmt_off(o):
    return "UTC" + ("+" if o >= 0 else "−") + str(abs(o))


def day(ts):
    return datetime.fromtimestamp(float(ts), timezone.utc).strftime("%Y-%m-%d")


def card(user, h, R):
    v, rh, de = R, R["rhythm"], R["desc"]
    p, th = R["score"], R["thresholds"]
    tone, verdict = R["tone"], R["verdict"]
    pct = R.get("control_pct")
    # Meter: log scale from 0.0001 to 1, with the three lines marked. (A control-percentile meter put a 0.0004 score
    # mid-bar, because most ordinary accounts score near zero; it read as "uncertain".)
    lp = lambda x: max(0.0, min(100.0, 25 * (math.log10(max(x, 1e-4)) + 4)))
    pos = lp(p)
    ticks = "".join(f'<div class=tk style="left:{lp(t):.1f}%" title="{k} line {t:.4f}"><span>{k}</span></div>'
                    for k, t in (("5", th["5%"]), ("7", th["2%"]), ("9", th["1%"])))
    e = html.escape

    def bar_rows(pairs, fmtv=lambda x: f"{100 * x:.0f}%"):
        return "".join(f"<tr><td>{e(k)}</td><td class=num>{fmtv(val)}</td></tr>" for k, val in pairs)

    hist = rh["hist"]
    mx = max(hist) or 1
    qs = rh.get("quiet_start")
    bars = "".join(
        f'<div class="hb{" q" if qs is not None and (hh - qs) % 24 < QUIET_HOURS else ""}" style="height:{4 + 56 * c / mx:.0f}px" '
        f'title="{hh:02d}:00 UTC: {c} items"></div>' for hh, c in enumerate(hist))
    if rh["status"] == "clear rhythm":
        b0, b1 = rh["band"]
        tz = f"fits {fmt_off(b0)} to {fmt_off(b1)}"
        rtxt = f"Clear day-night rhythm: {100 * rh['quiet_share']:.1f}% of items fall in the quietest 6 hours ({qs:02d}:00-{(qs + 6) % 24:02d}:00 UTC)."
    elif rh["status"] == "no clear rhythm":
        tz = "no estimate"
        rtxt = f"No clear rest period: {100 * rh['quiet_share']:.1f}% of items fall even in the quietest 6 hours. Round-the-clock posting fits a shared or automated account."
    else:
        tz, rtxt = "no estimate", f"Too few items ({rh['n']}) to read a rhythm."
    mm = R["mismatch"]
    dflt = R["default_name"]
    sig = [("warn" if dflt else "ok", "Reddit-style default name" if dflt else "Chosen name",
            "Pattern Word-Word-1234. Many real users keep it, so it's only a weak signal." if dflt else "Not the default pattern."),
           ("ok" if rh["status"] == "clear rhythm" else "warn", "Day-night rhythm", rtxt),
           ("warn" if mm else "ok", "Time zone vs. where it presents",
            "Presents as US (" + f"{100 * de['us_share']:.0f}% of items in US subs) but the active hours fit " + tz + ". A lead only: shift workers, people abroad and scheduling tools look the same."
            if mm else (f"{100 * de['us_share']:.0f}% of items in US subs; active hours {tz}. No mismatch." if de["us_share"] >= US_SHARE
                        else f"Not US-presenting ({100 * de['us_share']:.0f}% of items in US subs); active hours {tz}.")),
           ("warn" if v["solicit_handle"] else "ok", "Contact-handle template", "Posts push a contact handle." if v["solicit_handle"] else "None found."),
           ("warn" if v["solicit_broad"] else "ok", "Turn to NSFW or solicitation", "A normal history that turned to NSFW or solicitation posting." if v["solicit_broad"] else "None found."),
           ]
    sig_html = "".join(f'<li class="{k}"><b>{e(t)}</b><span>{e(d)}</span></li>' for k, t, d in sig)
    local = ", ".join(f"r/{e(k)}" for k in de["local_us"]) or "none"
    abroad = ", ".join(f"r/{e(k)} ({e(c)})" for k, c in de["local_abroad"]) or "none"
    lang = f"English {100 * de['english_share']:.0f}% of texts" if de["english_share"] is not None else "no text"
    age = f"{v['age_days'] / 365.25:.1f} years" if v["age_days"] is not None else "unknown"
    pct_txt = f"Scores higher than {100 * pct:.0f}% of {R['control_n']} ordinary accounts." if pct is not None else ""
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Account lookup</title><style>
:root{{--bg:#f6f7f9;--card:#fff;--ink:#16181d;--muted:#5d6470;--line:#dde1e7;--lo:#1f8a4c;--mid:#b26b00;--hi:#c0362c;--q:#8aa4c8;--b:#3d5a80}}
@media (prefers-color-scheme:dark){{:root{{--bg:#111318;--card:#1a1d24;--ink:#e8eaee;--muted:#9aa3b0;--line:#2c313b;--lo:#4cc283;--mid:#e3a03a;--hi:#ef6b5f;--q:#5b7398;--b:#8fb0dc}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,sans-serif}}
main{{max-width:880px;margin:0 auto;padding:20px 16px}}.c{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin-bottom:14px}}
h1{{font-size:20px;margin:0 0 2px}}.sub{{color:var(--muted);font-size:13px}}
.meter{{position:relative;height:10px;border-radius:5px;background:linear-gradient(90deg,var(--lo),#c9b23a,var(--hi));margin:18px 0 6px}}
.dot{{position:absolute;top:-5px;width:20px;height:20px;border-radius:50%;background:var(--card);border:4px solid var(--ink);transform:translateX(-50%)}}
.tk{{position:absolute;top:-4px;width:2px;height:18px;background:var(--ink);opacity:.55}}.tk span{{position:absolute;top:-16px;left:50%;transform:translateX(-50%);font-size:10px;color:var(--muted);white-space:nowrap}}
.meter{{margin-top:30px}}.ends{{display:flex;justify-content:space-between;color:var(--muted);font-size:12px}}
.v{{font-weight:700;margin-top:10px}}.v.lo{{color:var(--lo)}}.v.mid{{color:var(--mid)}}.v.hi{{color:var(--hi)}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}@media(max-width:640px){{.grid{{grid-template-columns:1fr}}}}
ul.s{{list-style:none;padding:0;margin:0}}ul.s li{{padding:8px 0 8px 22px;border-top:1px solid var(--line);position:relative}}
ul.s li:first-child{{border-top:0}}ul.s li::before{{position:absolute;left:0;top:8px;font-weight:700}}
ul.s li.ok::before{{content:"✓";color:var(--lo)}}ul.s li.warn::before{{content:"!";color:var(--mid)}}
ul.s b{{display:block}}ul.s span{{color:var(--muted);font-size:13px}}
table{{width:100%;border-collapse:collapse}}td{{padding:4px 0;border-top:1px solid var(--line)}}td.num{{text-align:right;font-variant-numeric:tabular-nums;color:var(--muted)}}
h2{{font-size:14px;margin:0 0 8px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}}
.hrs{{display:flex;align-items:flex-end;gap:2px;height:62px}}.hb{{flex:1;background:var(--b);border-radius:2px 2px 0 0}}.hb.q{{background:var(--q)}}
.hl{{display:flex;justify-content:space-between;color:var(--muted);font-size:11px;margin-top:4px}}
dl{{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:0}}dt{{color:var(--muted)}}dd{{margin:0}}
.note{{color:var(--muted);font-size:12px}}.top{{display:flex;justify-content:space-between;gap:16px}}
.rt{{text-align:right;flex:none}}.rt b{{display:block;font-size:38px;line-height:1.1}}.rt span{{color:var(--muted);font-size:12px}}
.rt.lo{{color:var(--lo)}}.rt.mid{{color:var(--mid)}}.rt.hi{{color:var(--hi)}}</style></head><body><main>
<div class=c><div class=top><div><h1>u/{e(user)}</h1><div class=sub>{h} · private lookup {e(R['when'])} · {R['n_items']:,} items ({R['n_posts']:,} posts, {R['n_comments']:,} comments) · account age {age}</div></div>
<div class="rt {tone}"><b>{e(R['rating_text'])}</b><span>out of 10</span></div></div>
<div class=meter>{ticks}<div class=dot style="left:{pos:.1f}%"></div></div><div class=ends><span>Ordinary</span><span>Flag lines at 5, 7 and 9</span><span>Strict flag</span></div>
<div class="v {tone}">{e(verdict)}</div><div class=sub>Detector score {p:.4f}. {e(pct_txt)} Lines: strict {th['1%']:.4f} · 2% {th['2%']:.4f} · 5% {th['5%']:.4f}. v7.1 rule flags: {e(v['flag_list'] or 'none')}.</div></div>
<div class=grid><div class=c><h2>Signals</h2><ul class=s>{sig_html}</ul>
<p class=note>Only the v7.1 score decides a flag. The signals above are for a person to weigh. They are not inputs to the score.</p></div>
<div class=c><h2>Top subreddits</h2><table>{bar_rows([('r/' + k, s) for k, s in de['top_subs']])}</table></div>
<div class=c><h2>Active hours (UTC)</h2><div class=hrs>{bars}</div><div class=hl><span>00</span><span>06</span><span>12</span><span>18</span><span>23</span></div>
<p class=note>Lighter bars are the quietest 6 hours. Time-zone estimate: <b>{tz}</b>.</p></div>
<div class=c><h2>Location clues (estimate)</h2><dl><dt>Active hours</dt><dd>{tz}</dd><dt>US local subs</dt><dd>{local}</dd>
<dt>Non-US place subs</dt><dd>{abroad}</dd><dt>Language</dt><dd>{lang}</dd></dl>
<p class=note>A rough guess from posting times and place subreddits. Reddit doesn't show where an account is based. This is never used to identify a person.</p></div>
<div class=c><h2>Top keywords</h2><table>{bar_rows(de['keywords'])}</table><p class=note>Share of texts that use the word.</p></div>
</div><p class=note>Private. Lives in ~/socialscope_data/lookups/ and is never committed or published.</p></main></body></html>"""



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("username")
    ap.add_argument("--no-pull", action="store_true")
    ap.add_argument("--cap", type=int, default=1000)
    a = ap.parse_args()
    os.umask(0o077)   # every file in the lookup folder holds the username
    user = re.sub(r"^/?u/", "", a.username.strip())
    h = C.H(user)
    d = private_dir(h)
    print(f"lookup {h}", flush=True)
    if not a.no_pull:
        pull(user, d, a.cap)
    zips = [z for z in (os.path.join(d, f"history_{k}.zip") for k in ("posts", "comments")) if os.path.exists(z)]
    if not zips:
        sys.exit("no history pulled (see pull_log.txt in the private lookup folder)")
    raw = [r for z in zips for r in C.iter_jsonl(z)]
    op = os.path.join(d, "history_oldest.json")
    oldest = (json.load(open(op)) if os.path.exists(op) else {}).get(user)
    M = json.load(open(MODEL_JSON))
    R = LC.analyze(user, raw, oldest, M)
    if R.get("error"):
        sys.exit("account has no items in Arctic Shift")
    R["when"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out_html, out_json = os.path.join(d, "card.html"), os.path.join(d, "lookup.json")
    open(out_html, "w", encoding="utf-8").write(card(user, h, R))
    json.dump(R, open(out_json, "w"), indent=1, default=str)
    rh = R["rhythm"]
    print(f"items {R['n_items']} (posts {R['n_posts']}, comments {R['n_comments']}); rating {R['rating_text']}/10; "
          f"v7.1 score {R['score']:.6f} (strict {R['thresholds']['1%']:.4f}, 5% {R['thresholds']['5%']:.4f}); above {100 * R['control_pct']:.0f}% of controls")
    print(f"solicit_handle {R['solicit_handle']}, solicit_broad {R['solicit_broad']}, tier '{R['tier']}', flags '{R['flag_list']}'")
    print(f"default name {R['default_name']}; rhythm {rh['status']}" + (f", quiet share {100 * rh['quiet_share']:.1f}%" if 'quiet_share' in rh else "")
          + (f", band {fmt_off(rh['band'][0])}..{fmt_off(rh['band'][1])}" if 'band' in rh else ""))
    print(f"US share {100 * R['desc']['us_share']:.0f}%, mismatch {R['mismatch']}; top subs "
          + ", ".join(f"{k} {100 * s:.0f}%" for k, s in R['desc']['top_subs'][:3]))
    print(f"card: {out_html}")


if __name__ == "__main__":
    main()

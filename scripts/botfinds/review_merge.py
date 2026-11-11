"""Combine the two blind reviews of Path 1 evidence files (docs/bot-publishing-plan.md, decision of Nov 10, 2026).
Written Nov 11, 2026.

Reads ~/socialscope_data/botfinds/review_user.csv and review_cloud.csv (calls: bot / not bot / unsure). Rules:
  - both "bot"                      -> submit
  - both filled, anything else      -> hold (any disagreement counts as unsure and is not submitted)
  - either blank                    -> waiting
Writes, private (never committed):
  review.csv        account, user_call, cloud_call, decision
  tracker.csv       one row per "submit" account: username, status (to_submit / submitted / pending / banned /
                    cleared), dates. Existing rows and statuses are kept; only new submits are added.
  submit_queue.md   ready-to-paste Bot Bouncer text for every row still at to_submit. Claude never posts it:
                    the user submits through Bot Bouncer's normal Reddit process, then sets status=submitted and
                    submitted_utc in tracker.csv.
stdout carries counts only.

Usage: python3 -I scripts/botfinds/review_merge.py
"""
import csv, os
from collections import Counter
from datetime import datetime, timezone

BF = os.path.expanduser("~/socialscope_data/botfinds")
TRACK_COLS = ["account", "username", "status", "decided_utc", "submitted_utc", "bb_flair", "bb_checked_utc", "notes"]


def read(path):
    return {r["account"]: r for r in csv.DictReader(open(path, encoding="utf-8"))} if os.path.exists(path) else {}


def norm(c):
    c = (c or "").strip().lower().replace("_", " ")
    return {"bot": "bot", "not bot": "not bot", "notbot": "not bot", "no": "not bot", "unsure": "unsure"}.get(c, c)


def write(path, cols, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    os.chmod(path, 0o600)


def main():
    U, Cl = read(os.path.join(BF, "review_user.csv")), read(os.path.join(BF, "review_cloud.csv"))
    cand = read(os.path.join(BF, "candidates_private.csv"))
    track = read(os.path.join(BF, "tracker.csv"))
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out, dec = [], Counter()
    for k in sorted(set(U) | set(Cl)):
        u, c = norm(U.get(k, {}).get("call")), norm(Cl.get(k, {}).get("call"))
        d = "waiting" if not u or not c else ("submit" if u == c == "bot" else "hold")
        dec[d] += 1
        out.append({"account": k, "user_call": u, "cloud_call": c, "decision": d})
        if d == "submit" and k not in track:
            track[k] = {"account": k, "username": cand.get(k, {}).get("username", ""), "status": "to_submit",
                        "decided_utc": today, "submitted_utc": "", "bb_flair": "", "bb_checked_utc": "", "notes": ""}
    write(os.path.join(BF, "review.csv"), ["account", "user_call", "cloud_call", "decision"], out)
    write(os.path.join(BF, "tracker.csv"), TRACK_COLS, list(track.values()))

    q = ["# Bot Bouncer submissions to make (PRIVATE, never commit)", "",
         "Claude prepared these; only the user submits. After submitting, set status=submitted and submitted_utc in tracker.csv.", ""]
    n = 0
    for k, t in track.items():
        if t["status"] != "to_submit":
            continue
        n += 1
        reasons = [norm_reason(U.get(k)), norm_reason(Cl.get(k))]
        q += [f"## u/{t['username']}", "", f"Profile: https://www.reddit.com/user/{t['username']}", "",
              "Suggested note: " + " ".join(r for r in reasons if r), f"(evidence file: packets/{k}.md)", ""]
    with open(os.path.join(BF, "submit_queue.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(q))
    os.chmod(os.path.join(BF, "submit_queue.md"), 0o600)
    print("decisions:", dict(dec))
    print("tracker:", dict(Counter(t["status"] for t in track.values())), f"; waiting to be submitted: {n}")


def norm_reason(r):
    s = (r or {}).get("reason", "").strip()
    return s if s.endswith(".") or not s else s + "."


if __name__ == "__main__":
    main()

"""Plain-language explainer for the re-pull results: draws docs/figures/explained_*.png and writes
docs/repull-explained.md (for the repo) and docs/figures/repull_explained.html (self-contained, for a phone).

Every number is typed in from ~/socialscope_data/repull/out/results_repull.md, results_old_matched.md and
docs/repull-results.md (aggregates only, no account names). Run: <python with matplotlib> -I repull_explained.py
"""
import base64, html, os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.dirname(HERE)
SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, LIGHT = "#2a78d6", "#eb6834", "#1baf7a", "#d9d8d2"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": INK, "axes.edgecolor": AXIS,
                     "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2, "axes.facecolor": SURF,
                     "figure.facecolor": SURF})


def clean(ax, grid="x"):
    for s in ("top", "right") + (("left",) if grid == "x" else ()):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y" if grid == "x" else "x", length=0)
    ax.grid(axis=grid, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def save(fig, name):
    p = os.path.join(HERE, name)
    fig.savefig(p, dpi=150, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return name


figs = {}

# 1. Out of 100 ---------------------------------------------------------------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(9, 4.6))
for ax, (lab, n, c, sub) in zip(axs, [("100 banned bot accounts", 62, BLUE, "62 caught  (range 52-72)"),
                                      ("100 ordinary accounts", 2, ORANGE, "about 2 wrongly flagged  (range 0-3)")]):
    for k in range(100):
        x, y = k % 10, k // 10
        ax.scatter(x, -y, s=150, color=c if k < n else LIGHT, edgecolor=SURF, linewidth=1.5)
    ax.set_xlim(-0.8, 9.8); ax.set_ylim(-9.8, 1.4); ax.axis("off"); ax.set_aspect("equal")
    ax.text(-0.5, 1.6, lab, fontsize=12.5, weight="bold")
    ax.text(-0.5, 0.75, sub, fontsize=10.5, color=INK2)
figs["out_of_100"] = save(fig, "explained_1_out_of_100.png")

# 2. Per 10,000 ---------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 3.4)); clean(ax)
rows = [("If 1 in 100 accounts\nis a bot (100 bots)", 62, 166, "27% of flags are real bots"),
        ("If 5 in 100 accounts\nare bots (500 bots)", 312, 159, "66% of flags are real bots")]
for i, (lab, tp, fp, note) in enumerate(rows):
    ax.barh(i, tp, color=BLUE, height=0.5); ax.barh(i, fp, left=tp + 3, color=ORANGE, height=0.5)
    ax.text(tp / 2, i, f"{tp} bots", ha="center", va="center", color="#ffffff", fontsize=10, weight="bold")
    ax.text(tp + 3 + fp / 2, i, f"{fp} ordinary", ha="center", va="center", color="#ffffff", fontsize=10, weight="bold")
    ax.text(tp + fp + 12, i, note, va="center", fontsize=10.5, color=INK)
ax.set_yticks([0, 1], [r[0] for r in rows]); ax.set_ylim(1.6, -0.6); ax.set_xlim(0, 720)
ax.set_xlabel("accounts flagged out of 10,000 checked (strict setting)")
ax.set_title("Who is in the flagged pile?", loc="left", fontsize=13, weight="bold")
figs["per_10000"] = save(fig, "explained_2_flagged_pile.png")

# 3. The dial ------------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5.2)); clean(ax, grid="both")
ax.plot([0, 10], [0, 10], ls=(0, (3, 3)), color=MUTED, lw=1)
ax.text(8.3, 12.5, "pure guessing", color=MUTED, fontsize=9.5, rotation=6)
for lab, pts, c in [("Detector (full model)", [(1.7, 62), (2.3, 71), (7.5, 77)], BLUE),
                    ("Account-age rule alone", [(4.4, 26), (5.2, 28), (6.9, 32)], AQUA)]:
    ax.plot(*zip(*pts), color=c, lw=2, marker="o", ms=8, mec=SURF, mew=2, label=lab)
for (x, y), t, off in zip([(1.7, 62), (2.3, 71), (7.5, 77)], ["strict", "medium", "loose"], [(8, -14), (-10, 10), (-10, 10)]):
    ax.annotate(t, (x, y), xytext=off, textcoords="offset points", fontsize=10, color=INK2)
ax.set_xlim(0, 10); ax.set_ylim(0, 100)
ax.set_xlabel("ordinary accounts wrongly flagged (%)"); ax.set_ylabel("bots caught (%)")
ax.legend(frameon=False, loc="center right")
ax.set_title("The dial: catching more bots costs more false alarms", loc="left", fontsize=13, weight="bold")
figs["dial"] = save(fig, "explained_3_dial.png")

# 4. Old vs fixed --------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 3.6)); clean(ax)
rows = [("Old headline\n(old pull, published)", 67, 60, 74, MUTED),
        ("Old pull, controls\ncut at matched dates", 59, 51, 65, MUTED),
        ("Re-pull (fixed)", 57, 44, 72, BLUE)]
for i, (lab, v, lo, hi, c) in enumerate(rows):
    ax.barh(i, v, color=c, height=0.5)
    ax.plot([lo, hi], [i, i], color=INK, lw=1.3)
    ax.text(hi + 1.5, i, f"{v}%", va="center", fontsize=11, weight="bold")
ax.set_yticks(range(3), [r[0] for r in rows]); ax.set_ylim(2.6, -0.6); ax.set_xlim(0, 100)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(decimals=0))
ax.set_xlabel("bots caught at 1 false alarm per 100 ordinary accounts  (black line = 95% range)")
ax.set_title("How much of the old score was real?", loc="left", fontsize=13, weight="bold")
figs["old_vs_new"] = save(fig, "explained_4_old_vs_new.png")

# 5. Signals -------------------------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 3.9)); clean(ax)
sig = [("Recent posts land in subreddits\nit had never used before", 0.079),
       ("Established account suddenly turns\nto NSFW / solicitation posts", 0.070),
       ("Sudden jump in how often\nit posts links", 0.025),
       ("How much it posted\nin the last 30 days", 0.015),
       ("Posts carrying contact handles\n(Telegram, Snapchat, ...)", 0.010)]
for i, (lab, v) in enumerate(sig):
    ax.barh(i, v, color=BLUE if i != 3 else MUTED, height=0.55)
    ax.text(v + 0.0015, i, f"{v:.3f}", va="center", fontsize=10, color=INK2)
ax.set_yticks(range(5), [s[0] for s in sig]); ax.set_ylim(4.6, -0.6); ax.set_xlim(0, 0.095)
ax.set_xlabel("how much worse the detector gets if this signal is scrambled (AUC lost)")
ax.set_title("What gives a bot away (top 5 signals)", loc="left", fontsize=13, weight="bold")
figs["signals"] = save(fig, "explained_5_signals.png")

# 6. Aged vs throwaway ---------------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 3.8)); clean(ax, grid="y")
groups = ["Aged accounts\n(old, probably hijacked\nor bought; 117)", "Throwaway accounts\n(new; 72)"]
for j, (lab, vals, c) in enumerate([("Detector (full model)", [65, 58], BLUE), ("Account-age rule", [0, 68], AQUA)]):
    xs = [k + (j - 0.5) * 0.36 for k in range(2)]
    ax.bar(xs, vals, width=0.34, color=c, label=lab)
    for x, v in zip(xs, vals):
        ax.text(x, v + 2, f"{v}%", ha="center", fontsize=10.5, weight="bold")
ax.set_xticks(range(2), groups); ax.set_ylim(0, 85)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(decimals=0))
ax.set_ylabel("bots caught (strict setting)"); ax.legend(frameon=False, loc="upper center", ncol=2)
ax.set_title("Old accounts fool the age rule, not the detector", loc="left", fontsize=13, weight="bold")
figs["aged"] = save(fig, "explained_6_aged_vs_throwaway.png")

# 7. Pending -------------------------------------------------------------------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.6), gridspec_kw={"wspace": 0.55})
ax = axs[0]; clean(ax)
for i, (lab, v, c) in enumerate([("Flagged by\nthe detector", 27, BLUE), ("Expected if they\nwere ordinary", 4.4, MUTED)]):
    ax.barh(i, v, color=c, height=0.5); ax.text(v + 0.6, i, "about 4" if v < 5 else f"{v:g}", va="center", fontsize=11, weight="bold")
ax.set_yticks([0, 1], ["Flagged by\nthe detector", "Expected if they\nwere ordinary"]); ax.set_ylim(1.6, -0.6); ax.set_xlim(0, 35)
ax.set_title("Pending accounts (261)", loc="left", fontsize=12, weight="bold")
ax = axs[1]; clean(ax)
for i, (lab, v, c) in enumerate([("Pending (30)", 16, BLUE), ("Ordinary (30)", 5, MUTED)]):
    ax.barh(i, v, color=c, height=0.5); ax.text(v + 0.4, i, f"{v} of 30", va="center", fontsize=11, weight="bold")
ax.set_yticks([0, 1], ["Pending (30)", "Ordinary (30)"]); ax.set_ylim(1.6, -0.6); ax.set_xlim(0, 30)
ax.set_title("Read by eye, judged bot-like", loc="left", fontsize=12, weight="bold")
figs["pending"] = save(fig, "explained_7_pending.png")

# ---- text ---------------------------------------------------------------------------------------------------------
INTRO = """# The re-pull results, explained

This explains what the re-pull numbers in [repull-results.md](repull-results.md) mean, in plain terms: what each
chart shows, what it tells you, and how far you can take it. Nothing here is new analysis; it is the same numbers
(Nov 6 run, reproduced byte for byte on Nov 9), redrawn to answer one question per chart.

## Background in one paragraph

The detector looks at a Reddit account's posting history and gives it a bot score. To test it we use accounts Bot
Bouncer **banned** as bots (the "bots" below), **ordinary** accounts picked at random from the same subreddits (the
"controls"), and **pending** accounts Bot Bouncer had been told about but not yet decided on (as of Oct 28). The old
test said the detector caught 67% of bots. We suspected that was inflated by how histories were downloaded: the
download keeps an account's newest 1,000 items, and banned accounts often kept posting after Bot Bouncer listed them, so their
history looked different from the ordinary accounts' for reasons that had nothing to do with being a bot. The
re-pull downloaded every account's history up to the same kind of cut-off date, so the comparison is fair.

## Words used below

- **Caught (recall):** of the real bots, the share the detector flags.
- **False alarm:** an ordinary account the detector flags. The **false-alarm rate** is the share of ordinary accounts flagged.
- **Setting (threshold):** how high a score has to be before the detector flags an account. Stricter means fewer false alarms but fewer bots caught.
- **Range (95% CI):** with a few hundred test accounts, every number is an estimate. The range is where the true value plausibly lies; a wide range means "don't lean hard on the exact number".
- **AUC:** one number for how well scores separate bots from ordinary accounts overall. 0.5 is guessing, 1.0 is perfect. It's useful for comparing versions, less useful for deciding anything.
"""

SECTIONS = [
    ("out_of_100", "1. What the detector does, in one picture",
     "At its strictest setting, out of 100 banned bots the detector flags 62. Out of 100 ordinary accounts it "
     "wrongly flags about 2.",
     "It catches a solid majority of bots while bothering very few ordinary accounts. It still misses about 4 in 10 "
     "bots, so not being flagged doesn't mean an account is clean.",
     "With 189 bots in the test, the honest range on \"62 caught\" is about 52 to 72. Treat it as \"roughly 6 in 10\", "
     "not as exactly 62%. The setting was meant to give 1 false alarm per 100; on these accounts it gave about 1.7, so "
     "expect closer to 2."),
    ("per_10000", "2. If the detector flags an account, how likely is it really a bot?",
     "Imagine running the detector over 10,000 accounts. How many of the flagged ones are actually bots depends on "
     "how common bots are to begin with. If 1 in 100 accounts is a bot, the flagged pile holds about 62 bots and "
     "166 ordinary accounts. If 5 in 100 are bots, it holds about 312 bots and 159 ordinary accounts.",
     "When bots are rare, most flags are false alarms, even though the false-alarm rate looks tiny. That's because "
     "2% of a very large number of ordinary accounts outnumbers the bots. Where bots are common (a targeted or "
     "brigaded thread), a flag is much more likely to be right.",
     "This is why a flag is a lead to check, never proof that an account is a bot. In a typical subreddit, expect "
     "roughly 1 in 4 flags to be a real bot (range about 1 in 5 to 3 in 5). Nobody knows the true share of bots in a "
     "given subreddit, so these two rows are scenarios, not measurements."),
    ("dial", "3. The trade-off: catching more costs more false alarms",
     "Each dot is one setting. Loosening the setting moves up (more bots caught) and to the right (more ordinary "
     "accounts flagged). The dashed line is what random guessing would do.",
     "Going from strict to medium buys about 9 more bots per 100 for well under 1 extra false alarm per 100, a good "
     "trade. Going on to loose buys only 6 more bots per 100 for 5 extra false alarms, a bad one. The account-age "
     "rule on its own sits much lower: it catches about a quarter of bots, whatever the setting.",
     "If flags get checked by a person, the medium setting is probably the sweet spot. If flags trigger anything "
     "automatic, stay strict. Account age alone is not a usable detector."),
    ("old_vs_new", "4. How much of the old 67% was real?",
     "All three bars are measured the same way: bots caught when 1 in 100 ordinary accounts is flagged. The old "
     "published number was 67%. The re-pull gives 57%. The middle bar uses the old downloads but cuts the ordinary "
     "accounts' histories at dates matched to the bans, and it already gets 59%.",
     "About 10 points of the old headline came from the download artifact, not from spotting bots. The detector is "
     "still good, just not as good as first reported.",
     "The middle bar suggests most of the inflation came from when each account's history was cut off, more than from "
     "the 1,000-item cap itself. That's my reading, not something a prediction tested. The re-pull's range (44-72%) is "
     "wide and still overlaps 67%, so the test can't rule out that some of the old number was real."),
    ("signals", "5. What gives a bot away",
     "These are the five signals the detector leans on most. Each bar shows how much worse the detector gets if "
     "that one signal is scrambled.",
     "The strongest clues are about change: an account that suddenly starts posting in subreddits it never used, an "
     "established account that turns to NSFW or solicitation posts, or a jump in links. That fits the pattern found by "
     "reading accounts by eye: an ordinary history that gets taken over and turned to spam. The grey bar, how much the "
     "account posted recently, is the one leftover that measures volume rather than behavior.",
     "Bots that are built from scratch and never change their behavior would be harder for this detector to catch. "
     "The volume signal is small enough that the fix removed most of what it was doing before."),
    ("aged", "6. Old accounts fool the age rule, not the detector",
     "Bots split into two kinds: aged accounts, which are old and probably hijacked or bought, and throwaways, which "
     "are newly made. The detector catches both at about the same rate. The age rule catches none of the aged ones, "
     "because they're old by definition.",
     "The detector isn't just measuring account age. Behavior signals do the work for aged accounts, which are most "
     "of the bots here (117 of 189).",
     "The prediction that the fix would mostly hurt aged-bot detection didn't hold clearly: aged fell 4 points and "
     "throwaway 3, within the noise. For throwaway accounts the age rule is about as good as the detector, so a "
     "brand-new account is a cheap, rough signal on its own."),
    ("pending", "7. The pending accounts",
     "Of 261 accounts still waiting on a Bot Bouncer decision, the detector flags 27. If they were like ordinary "
     "accounts you'd expect about 4. In the separate by-eye read, 16 of 30 pending accounts looked bot-like, against "
     "5 of 30 ordinary ones.",
     "Pending accounts really do lean bot-like. Both methods agree, and neither result is plausibly chance (p = 4e-7 "
     "and p = 0.006).",
     "Since the detector catches about 6 in 10 bots, 27 flags suggests very roughly 9-21% of the pending accounts "
     "behave like the banned bots. The by-eye read says about half look bot-like. The gap could mean pending bots "
     "differ from the banned ones, or that the by-eye judgment is looser, or it's small-sample noise (30 accounts). "
     "This is about the group; it says nothing about any one pending account."),
]

BOTTOM = """## Bottom line

- The detector works, but the real figure is about **6 in 10 bots caught at about 2 false alarms per 100**, not the
  old 67% at 1 per 100. About 10 points of the old headline was a download artifact.
- **Flags are leads.** When bots are rare, most flags are ordinary accounts, so every flag needs a person to check it.
- It works by spotting **accounts that suddenly change behavior**, which is the takeover-and-spam pattern most of
  these bots follow. It doesn't depend on account age.
- **Pending accounts lean bot-like** as a group, by both the detector and the by-eye read.
- Every number has a wide range (often 10 points either way) because the test has under 200 bots. A bigger test
  set would narrow that more than any change to the detector would.

Caveat: the comparison rows that used the old downloads with each account's last item as the cut-off date ran
only once. Repeat runs failed because of the laptop's RAM fault, so they aren't reproduced and aren't used in
this explainer. Everything here is from re-pull runs that reproduced byte for byte, plus the old-download
matched-date run, which also reproduced.
"""

md = [INTRO]
for key, title, shows, means, extra in SECTIONS:
    md.append(f"## {title}\n\n![{title}](figures/{figs[key]})\n\n**What it shows.** {shows}\n\n"
              f"**What it means.** {means}\n\n**How far you can take it.** {extra}\n")
md.append(BOTTOM)
open(os.path.join(DOCS, "repull-explained.md"), "w").write("\n".join(md))


def inline(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", t)


def md_block(text):
    out, items = [], []
    for para in text.strip().split("\n\n"):
        para = para.strip()
        if para.startswith("# "):
            out.append(f"<h1>{inline(para[2:])}</h1>")
        elif para.startswith("## "):
            out.append(f"<h2>{inline(para[3:])}</h2>")
        elif para.startswith("- "):
            lis = [" ".join(l.strip() for l in it.split("\n")) for it in re.split(r"\n- ", para[2:])]
            out.append("<ul>" + "".join(f"<li>{inline(l)}</li>" for l in lis) + "</ul>")
        else:
            out.append(f"<p>{inline(' '.join(para.split()))}</p>")
    return "\n".join(out)


body = [md_block(INTRO)]
for key, title, shows, means, extra in SECTIONS:
    b64 = base64.b64encode(open(os.path.join(HERE, figs[key]), "rb").read()).decode()
    body.append(f"<h2>{html.escape(title)}</h2><img alt='{html.escape(title)}' src='data:image/png;base64,{b64}'>"
                f"<p><strong>What it shows.</strong> {inline(shows)}</p><p><strong>What it means.</strong> {inline(means)}</p>"
                f"<p class='ext'><strong>How far you can take it.</strong> {inline(extra)}</p>")
body.append(md_block(BOTTOM))
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Re-pull explained</title><style>
:root{{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--rule:#e1e0d9;--wash:#eef4fc}}
body{{background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;padding:24px 16px}}
main{{max-width:760px;margin:0 auto}} h1{{font-size:1.7em;line-height:1.2}} h2{{margin-top:2.2em;padding-top:.8em;border-top:1px solid var(--rule)}}
img{{width:100%;height:auto;background:#fcfcfb;border-radius:6px}} li{{margin:.4em 0}} p{{color:var(--ink)}}
.ext{{background:var(--wash);padding:.7em .9em;border-radius:6px}}
</style></head><body><main>{''.join(body)}</main></body></html>"""
open(os.path.join(HERE, "repull_explained.html"), "w").write(page)
print("wrote", len(figs), "figures, repull-explained.md, repull_explained.html")

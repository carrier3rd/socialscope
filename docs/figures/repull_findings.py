"""Findings graphic for docs/repull-results.md. All numbers typed in from results_repull.md / repull-results.md."""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GOOD, WARN, CRIT = "#0ca30c", "#fab219", "#d03b3b"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK, "axes.edgecolor": AXIS,
                     "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2, "axes.facecolor": SURF,
                     "figure.facecolor": SURF})

fig = plt.figure(figsize=(10, 17.5))
gs = fig.add_gridspec(5, 2, height_ratios=[3.2, 3.1, 2.0, 1.9, 1.5], hspace=0.55, wspace=0.36,
                      left=0.17, right=0.97, top=0.925, bottom=0.03)
fig.text(0.03, 0.975, "Re-pull fix: what the predictions got right", fontsize=17, weight="bold")
fig.text(0.03, 0.958, "Test side: 189 banned accounts (117 aged, 72 throwaway), 478 controls, 261 pending. "
         "Bootstrap 95% CIs, 2,000 resamples.", fontsize=10, color=INK2)


def clean(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def title(ax, t, sub=None):
    ax.set_title(t, loc="left", fontsize=12.5, weight="bold", pad=22 if sub else 8)
    if sub:
        ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9.5, color=INK2, va="bottom")


# --- A. scorecard -------------------------------------------------------------------------------------------------
ax = fig.add_subplot(gs[0, :]); ax.axis("off"); ax.set_position([0.03, ax.get_position().y0, 0.94, ax.get_position().height])
title(ax, "Scorecard: 4 hits, 3 partials, 0 misses")
rows = [
    ("1", "Recall at 1% FPR falls to 45-60%; CI excludes 67%", "57% (old threshold) / 62% (CV); both CIs reach 72%", "PARTIAL"),
    ("2", "AUC 0.90-0.95; recall moves more than AUC", "AUC 0.931 (0.908-0.952); recall -10 pts, AUC -0.03", "HIT"),
    ("3", "Volume features leave the top 5", "comment count gone; 30-day item count still 4th", "HIT*"),
    ("4", "Drop concentrated in aged; throwaway moves < 5 pts", "throwaway -3 pts (holds); aged -4 pts, CIs overlap", "PARTIAL"),
    ("5", "Full vs no-volume gap < 5 pts", "was 10 pts; now 1 (old threshold) or 6 (CV)", "PARTIAL"),
    ("6", "Recall CI at least 15 pts wide", "20 pts (CV), 28 pts (old threshold)", "HIT"),
    ("7", "Pending flagged well above controls; blind read p < .01", "10.3% vs 1.7% (p = 4e-7); blind read p = .006", "HIT"),
]
CH = {"HIT": (GOOD, "#ffffff", "✓ HIT"), "HIT*": (GOOD, "#ffffff", "✓ HIT*"),
      "PARTIAL": (WARN, INK, "◐ PARTIAL"), "MISS": (CRIT, "#ffffff", "✗ MISS")}
ax.set_xlim(0, 1); ax.set_ylim(len(rows) + 0.6, -0.6)
ax.text(0.0, -0.35, "#", color=MUTED, fontsize=9); ax.text(0.03, -0.35, "PREDICTED", color=MUTED, fontsize=9)
ax.text(0.45, -0.35, "RESULT", color=MUTED, fontsize=9)
for i, (n, p, r, v) in enumerate(rows):
    y = i + 0.5
    ax.axhline(i + 0.05, color=GRID, lw=0.8)
    ax.text(0.0, y, n, va="center", weight="bold")
    ax.text(0.03, y, p, va="center", fontsize=9.5)
    ax.text(0.45, y, r, va="center", fontsize=9.5, color=INK2)
    bg, fg, lab = CH[v]
    ax.add_patch(FancyBboxPatch((0.87, y - 0.3), 0.13, 0.6, boxstyle="round,pad=0,rounding_size=0.12",
                                fc=bg, ec="none", mutation_aspect=1 / 8))
    ax.text(0.935, y, lab, ha="center", va="center", color=fg, weight="bold", fontsize=9)
ax.text(0.0, len(rows) + 0.45, "* one volume feature (items in the 30-day window) still ranks 4th.  "
        "The one clause that clearly failed: prediction 1's CI still includes the old 67%.", fontsize=8.5, color=MUTED)

# --- B. recall at 1/2/5% ------------------------------------------------------------------------------------------
ax = fig.add_subplot(gs[1, :]); clean(ax)
title(ax, "Recall at each false-alarm target (threshold from training controls)",
      "Dot = recall, bar = bootstrap 95% CI, label = false-alarm rate actually reached on test controls")
models = [("Full model", BLUE), ("No-volume", ORANGE), ("Age rule", AQUA)]
data = {  # target: [(recall, lo, hi, test FPR)] in model order
    "1%": [(62, 52, 72, 1.7), (56, 49, 65, 1.3), (26, 19, 32, 4.4)],
    "2%": [(71, 65, 78, 2.3), (66, 58, 74, 2.9), (28, 21, 34, 5.2)],
    "5%": [(77, 70, 84, 7.5), (75, 69, 84, 7.3), (32, 25, 39, 6.9)],
}
y, yt, yl = 0, [], []
for g, (tgt, vals) in enumerate(data.items()):
    if tgt == "1%":
        ax.add_patch(plt.Rectangle((45, y - 0.45), 15, 2.9, fc=BLUE, alpha=0.08, ec="none"))
        ax.text(52.5, y - 0.65, "predicted 45-60%", ha="center", fontsize=8.5, color=INK2)
    for (m, c), (r, lo, hi, f) in zip(models, vals):
        ax.plot([lo, hi], [y, y], color=c, lw=2, solid_capstyle="round")
        ax.scatter([r], [y], s=70, color=c, edgecolor=SURF, linewidth=2, zorder=3)
        ax.text(hi + 1.2, y, f"{r}%   (FPR {f}%)", va="center", fontsize=8.5, color=INK2)
        yt.append(y); yl.append(f"{m}")
        y += 1
    ax.text(-0.5, y - 2, f"{tgt} target", transform=ax.get_yaxis_transform(), ha="right", va="center",
            fontsize=10, weight="bold") if False else None
    ax.text(102, y - 2, f"{tgt}\ntarget", ha="left", va="center", fontsize=10, weight="bold")
    y += 0.8
ax.axvline(67, color=INK2, ls=(0, (3, 3)), lw=1)
ax.text(68, -0.95, "old headline 67%", ha="left", fontsize=8.5, color=INK2)
ax.set_yticks(yt, yl); ax.set_ylim(y - 0.5, -1.3); ax.set_xlim(0, 110)
ax.set_xticks(range(0, 101, 20), [f"{v}%" for v in range(0, 101, 20)])
ax.set_xlabel("recall (share of banned accounts flagged)")

# --- C. AUC ------------------------------------------------------------------------------------------------------
ax = fig.add_subplot(gs[2, 0]); clean(ax)
title(ax, "AUC: old data vs re-pull", "predicted band 0.90-0.95 shaded")
auc = [("Published (old)", 0.97, None, None, MUTED), ("Old, last-item†", 0.959, 0.941, 0.974, MUTED),
       ("Old, matched", 0.936, 0.914, 0.955, MUTED), ("Re-pull full", 0.931, 0.908, 0.952, BLUE),
       ("Re-pull no-vol.", 0.917, 0.888, 0.942, ORANGE), ("Re-pull age rule", 0.576, 0.521, 0.628, AQUA)]
ax.axvspan(0.90, 0.95, color=BLUE, alpha=0.08, lw=0)
for i, (n, v, lo, hi, c) in enumerate(auc):
    if lo:
        ax.plot([lo, hi], [i, i], color=c, lw=2, solid_capstyle="round")
    ax.scatter([v], [i], s=60, color=c, edgecolor=SURF, linewidth=2, zorder=3)
    ax.text((hi or v) + 0.008, i, f"{v:.3f}", ha="left", va="center", fontsize=8.5, color=INK2)
ax.set_yticks(range(len(auc)), [a[0] for a in auc]); ax.set_ylim(len(auc) - 0.5, -0.6); ax.set_xlim(0.5, 1.03)

# --- D. aged vs throwaway ----------------------------------------------------------------------------------------
ax = fig.add_subplot(gs[2, 1]); clean(ax)
title(ax, "Recall at 1%: aged vs throwaway", "full model, CV threshold; old data → re-pull")
for i, (n, old, new, lo, hi) in enumerate([("Aged (117)", 69, 65, 52, 75), ("Throwaway (72)", 61, 58, 46, 72)]):
    ax.plot([lo, hi], [i, i], color=BLUE, lw=2, alpha=0.35, solid_capstyle="round")
    ax.annotate("", xy=(new, i), xytext=(old, i), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2))
    ax.scatter([old], [i], s=55, color=SURF, edgecolor=MUTED, linewidth=1.5, zorder=3)
    ax.scatter([new], [i], s=70, color=BLUE, edgecolor=SURF, linewidth=2, zorder=3)
    ax.text(old + 1, i + 0.32, f"{old}%", fontsize=8.5, color=MUTED, ha="left")
    ax.text(new - 1, i + 0.32, f"{new}%", fontsize=8.5, color=INK, ha="right")
    ax.text(85, i, f"{new - old:+d} pts", va="center", fontsize=9.5, weight="bold", color=INK2)
ax.set_yticks([0, 1], ["Aged (117)", "Throwaway (72)"]); ax.set_ylim(1.7, -0.5); ax.set_xlim(40, 95)
ax.set_xticks([40, 50, 60, 70, 80], ["40%", "50%", "60%", "70%", "80%"])
ax.text(0, -0.2, "○ old data†   ● re-pull (bar = CI)", transform=ax.transAxes, fontsize=8.5, color=INK2)

# --- E. pending signal -------------------------------------------------------------------------------------------
for col, (t, sub, rows_) in enumerate([
        ("Pending accounts flagged at 1%", "model, Wilson 95% CI; Fisher p = 4e-7",
         [("Pending (261)", 10.3, 7.2, 14.6, BLUE), ("Controls (478)", 1.7, 0.9, 3.3, MUTED)]),
        ("Blind read: judged bot-like", "30 per arm; Fisher p = 0.006",
         [("Pending (30)", 53.3, 36.1, 69.9, BLUE), ("Controls (30)", 16.7, 7.3, 33.6, MUTED)])]):
    ax = fig.add_subplot(gs[3, col]); clean(ax); title(ax, t, sub)
    for i, (n, v, lo, hi, c) in enumerate(rows_):
        ax.barh(i, v, height=0.5, color=c, alpha=0.9)
        ax.plot([lo, hi], [i, i], color=INK, lw=1.2)
        ax.text(hi + (1 if col == 0 else 3), i, f"{v:.1f}%", va="center", fontsize=9, color=INK)
    ax.set_yticks([0, 1], [r[0] for r in rows_]); ax.set_ylim(1.6, -0.6)
    ax.set_xlim(0, 20 if col == 0 else 85)
    ax.set_xticks(range(0, 21, 5) if col == 0 else range(0, 81, 20))
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(decimals=0))

# --- F. things that looked off -----------------------------------------------------------------------------------
ax = fig.add_subplot(gs[4, :]); ax.axis("off"); ax.set_position([0.03, ax.get_position().y0, 0.94, ax.get_position().height]); title(ax, "Things that looked off")
notes = [
    "Thresholds run hot: the 1% target reached 1.7% false alarms on test controls (2% → 2.3%, 5% → 7.5%).",
    "The age rule can't reach low false-alarm rates (its 1% target lands at 4.4%), probably from ties in account age.",
    "Removed-item share in the window is 15x higher for banned accounts than controls (runbook expected ~3x). Kept out of the model.",
    "Only 2 controls fell back to last-item anchors (about 10 expected). 3 of 3,267 accounts missing from features.",
    "† Old last-item rows ran once; repeat runs failed on the laptop's RAM fault, so they are not reproduced.",
    "    Every re-pull number reproduced byte for byte on a second run.",
]
for i, n in enumerate(notes):
    ax.text(0, 0.88 - i * 0.17, ("• " if not n.startswith(("†", "    ")) else "") + n,
            transform=ax.transAxes, fontsize=9.3, color=INK2 if i < 4 else INK, va="top")

fig.savefig(sys.argv[1], dpi=150)

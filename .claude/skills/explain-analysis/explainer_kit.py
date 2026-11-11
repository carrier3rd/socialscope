"""Helpers for plain-language analysis explainers (see SKILL.md next to this file).

Import from a generator script kept in docs/figures/:

    import sys; sys.path.insert(0, "<repo>/.claude/skills/explain-analysis")
    import explainer_kit as K
    fig, ax = K.new(9, 3.6); K.clean(ax)
    ...
    figs = {"key": K.save(fig, K.FIG_DIR, "explained_<topic>_1_name.png")}
    K.write_docs(topic, INTRO, SECTIONS, BOTTOM, figs)

SECTIONS is a list of (fig_key, title, shows, means, how_far). INTRO and BOTTOM are markdown using only "# ",
"## ", "- " bullets, **bold** and [links](x). Needs matplotlib (not in the project venvs: use a throwaway venv in
the scratchpad). Numbers are always typed in by the caller from results files, never read from raw data here.
"""
import base64, html, os, re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DOCS = os.path.join(REPO, "docs")
FIG_DIR = os.path.join(DOCS, "figures")

# Palette (validated reference palette from the dataviz skill). Use slots in this order, never cycled.
SURF, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, AQUA, LIGHT = "#2a78d6", "#eb6834", "#1baf7a", "#d9d8d2"
SERIES = [BLUE, ORANGE, AQUA]          # max three colored series per chart; past that, fold or split the chart
REF = MUTED                            # old / baseline / "expected by chance" bars

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "text.color": INK, "axes.edgecolor": AXIS,
                     "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2, "axes.facecolor": SURF,
                     "figure.facecolor": SURF})


def new(w=9, h=3.6, **kw):
    return plt.subplots(figsize=(w, h), **kw)


def clean(ax, grid="x"):
    """Recessive chrome: hairline grid along the value axis only, no box."""
    for s in ("top", "right") + (("left",) if grid == "x" else ()):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y" if grid == "x" else "x", length=0)
    if grid in ("x", "y", "both"):
        ax.grid(axis=grid, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def title(ax, text, size=13):
    ax.set_title(text, loc="left", fontsize=size, weight="bold")


def pct_axis(ax, axis="x"):
    (ax.xaxis if axis == "x" else ax.yaxis).set_major_formatter(mticker.PercentFormatter(decimals=0))


def icon_array(ax, n_on, label, sub, color=BLUE, total=100):
    """10x10 dots, n_on colored: 'out of 100 X, N do Y'. The clearest way to show a rate to a non-statistician."""
    for k in range(total):
        ax.scatter(k % 10, -(k // 10), s=150, color=color if k < n_on else LIGHT, edgecolor=SURF, linewidth=1.5)
    ax.set_xlim(-0.8, 9.8); ax.set_ylim(-9.8, 1.4); ax.axis("off"); ax.set_aspect("equal")
    ax.text(-0.5, 1.6, label, fontsize=12.5, weight="bold")
    ax.text(-0.5, 0.75, sub, fontsize=10.5, color=INK2)


def hbars(ax, rows, xmax=None, ci=True, fmt="{:g}%", value_pad=None):
    """Horizontal bars with optional 95% range lines. rows: (label, value, lo, hi, color); lo/hi may be None."""
    for i, (lab, v, lo, hi, c) in enumerate(rows):
        ax.barh(i, v, color=c, height=0.5)
        end = v
        if ci and lo is not None:
            ax.plot([lo, hi], [i, i], color=INK, lw=1.3); end = max(v, hi)
        pad = value_pad if value_pad is not None else (xmax or end) * 0.015
        ax.text(end + pad, i, fmt.format(v), va="center", fontsize=11, weight="bold")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows]); ax.set_ylim(len(rows) - 0.4, -0.6)
    if xmax:
        ax.set_xlim(0, xmax)


def stacked_pile(ax, rows, parts=("bots", "ordinary"), colors=(BLUE, ORANGE)):
    """'Who is in the flagged pile': rows = (label, true_count, false_count, note). Counts, not rates."""
    for i, (lab, tp, fp, note) in enumerate(rows):
        gap = (tp + fp) * 0.006
        ax.barh(i, tp, color=colors[0], height=0.5); ax.barh(i, fp, left=tp + gap, color=colors[1], height=0.5)
        for x0, w, word in ((0, tp, parts[0]), (tp + gap, fp, parts[1])):
            ax.text(x0 + w / 2, i, f"{w:g} {word}", ha="center", va="center", color="#ffffff", fontsize=10, weight="bold")
        ax.text(tp + fp + gap * 4, i, note, va="center", fontsize=10.5)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows]); ax.set_ylim(len(rows) - 0.4, -0.6)


def lead(name="blue"):
    """Rotate which validated color leads (see SKILL.md 'Keep it fresh'). Sets SERIES in place and returns it.
    Any order of blue/orange/aqua is safe: the three pass the colorblind checks for every pair."""
    order = {"blue": [BLUE, ORANGE, AQUA], "orange": [ORANGE, AQUA, BLUE], "aqua": [AQUA, BLUE, ORANGE]}[name]
    SERIES[:] = order
    return SERIES


def slope(ax, rows, left="before", right="after", fmt="{:g}%"):
    """Slope chart: each row (label, before, after, color) is a line from left to right. Good for 2-5 items."""
    lo = min(min(r[1], r[2]) for r in rows); hi = max(max(r[1], r[2]) for r in rows)
    gap = (hi - lo) * 0.07 or 1

    def spread(vals):   # nudge label heights apart so close values don't overprint
        order = sorted(range(len(vals)), key=lambda k: vals[k]); ys = list(vals)
        for j in range(1, len(order)):
            if ys[order[j]] - ys[order[j - 1]] < gap:
                ys[order[j]] = ys[order[j - 1]] + gap
        return ys
    ya, yb = spread([r[1] for r in rows]), spread([r[2] for r in rows])
    for (lab, a, b, c), la, lb in zip(rows, ya, yb):
        ax.plot([0, 1], [a, b], color=c, lw=2.2, marker="o", ms=8, mec=SURF, mew=2)
        ax.text(-0.04, la, fmt.format(a), ha="right", va="center", fontsize=10, color=INK2)
        ax.text(1.04, lb, f"{fmt.format(b)}  {lab}", ha="left", va="center", fontsize=10.5)
    ax.set_xlim(-0.35, 1.9); ax.set_xticks([0, 1], [left, right])
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_yticks([]); ax.tick_params(axis="x", length=0)


def dumbbell(ax, rows, fmt="{:g}%", old_label="old", new_label="new"):
    """Dumbbell: (label, old, new, color). Hollow grey dot = old, filled = new, the change printed on the right."""
    for i, (lab, a, b, c) in enumerate(rows):
        ax.plot([a, b], [i, i], color=AXIS, lw=3, solid_capstyle="round", zorder=1)
        ax.scatter([a], [i], s=70, color=SURF, edgecolor=MUTED, linewidth=1.8, zorder=2)
        ax.scatter([b], [i], s=85, color=c, edgecolor=SURF, linewidth=2, zorder=3)
        ax.text(max(a, b), i - 0.28, f"{fmt.format(a)} → {fmt.format(b)}", ha="right", fontsize=9.5, color=INK2)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows]); ax.set_ylim(len(rows) - 0.4, -0.8)
    ax.text(1, -0.2, f"○ {old_label}   ● {new_label}", transform=ax.transAxes, fontsize=9, color=INK2,
            ha="right", va="top")


def lollipop(ax, rows, color=None, fmt="{:.3f}"):
    """Ranked lollipops: (label, value). A lighter alternative to ranked bars."""
    color = color or SERIES[0]
    for i, (lab, v) in enumerate(rows):
        ax.plot([0, v], [i, i], color=color, lw=2)
        ax.scatter([v], [i], s=90, color=color, edgecolor=SURF, linewidth=2, zorder=3)
        ax.text(v, i - 0.3, fmt.format(v), ha="center", fontsize=9.5, color=INK2)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows]); ax.set_ylim(len(rows) - 0.4, -0.8)


def hero(ax, number, line, sub=None, color=None):
    """A big number with one sentence: an opening device, or the answer to a single-number question."""
    ax.axis("off")
    ax.text(0, 0.62, number, fontsize=54, weight="bold", color=color or SERIES[0], va="center")
    ax.text(0, 0.22, line, fontsize=14, va="center")
    if sub:
        ax.text(0, 0.02, sub, fontsize=10.5, color=INK2, va="center")


def callout(ax, text, xy, xytext, **kw):
    """Point at the finding on the chart itself: a short note and a thin arrow."""
    ax.annotate(text, xy=xy, xytext=xytext, fontsize=10, color=INK, ha=kw.pop("ha", "left"),
                arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1, shrinkA=2, shrinkB=4), **kw)


def small_multiples(groups, draw, ncols=3, w=9.5, h=2.6, sharex=True):
    """One mini chart per group on a shared axis: draw(ax, group). Returns fig."""
    import math
    nrows = math.ceil(len(groups) / ncols)
    fig, axs = plt.subplots(nrows, ncols, figsize=(w, h * nrows), sharex=sharex, squeeze=False)
    for ax, g in zip(axs.flat, groups):
        draw(ax, g)
    for ax in list(axs.flat)[len(groups):]:
        ax.axis("off")
    return fig


def save(fig, out_dir, name):
    os.makedirs(out_dir, exist_ok=True)
    fig.savefig(os.path.join(out_dir, name), dpi=150, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return name


def _inline(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", t)


def _md_to_html(text):
    out = []
    for para in text.strip().split("\n\n"):
        para = para.strip()
        if para.startswith("# "):
            out.append(f"<h1>{_inline(para[2:])}</h1>")
        elif para.startswith("## "):
            out.append(f"<h2>{_inline(para[3:])}</h2>")
        elif para.startswith("- "):
            lis = [" ".join(l.strip() for l in it.split("\n")) for it in re.split(r"\n- ", para[2:])]
            out.append("<ul>" + "".join(f"<li>{_inline(l)}</li>" for l in lis) + "</ul>")
        else:
            out.append(f"<p>{_inline(' '.join(para.split()))}</p>")
    return "\n".join(out)


CSS = """:root{--bg:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--rule:#e1e0d9;--wash:#eef4fc}
body{background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;padding:24px 16px}
main{max-width:760px;margin:0 auto} h1{font-size:1.7em;line-height:1.2} h2{margin-top:2.2em;padding-top:.8em;border-top:1px solid var(--rule)}
img{width:100%;height:auto;background:#fcfcfb;border-radius:6px} li{margin:.4em 0}
.ext{background:var(--wash);padding:.7em .9em;border-radius:6px}"""


def write_docs(topic, intro, sections, bottom, figs, page_title=None, fig_dir=FIG_DIR, docs_dir=DOCS):
    """Write docs/<topic>-explained.md (images linked) and docs/figures/<topic>_explained.html (images inlined).
    Returns (md_path, html_path)."""
    md = [intro]
    for key, t, shows, means, far in sections:
        md.append(f"## {t}\n\n![{t}](figures/{figs[key]})\n\n**What it shows.** {shows}\n\n"
                  f"**What it means.** {means}\n\n**How far you can take it.** {far}\n")
    md.append(bottom)
    md_path = os.path.join(docs_dir, f"{topic}-explained.md")
    open(md_path, "w").write("\n".join(md))
    body = [_md_to_html(intro)]
    for key, t, shows, means, far in sections:
        b64 = base64.b64encode(open(os.path.join(fig_dir, figs[key]), "rb").read()).decode()
        body.append(f"<h2>{html.escape(t)}</h2><img alt='{html.escape(t)}' src='data:image/png;base64,{b64}'>"
                    f"<p><strong>What it shows.</strong> {_inline(shows)}</p>"
                    f"<p><strong>What it means.</strong> {_inline(means)}</p>"
                    f"<p class='ext'><strong>How far you can take it.</strong> {_inline(far)}</p>")
    body.append(_md_to_html(bottom))
    pt = html.escape(page_title or topic.replace("-", " ").capitalize() + " explained")
    html_path = os.path.join(fig_dir, f"{topic.replace('-', '_')}_explained.html")
    open(html_path, "w").write(f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' "
                               f"content='width=device-width,initial-scale=1'><title>{pt}</title><style>{CSS}</style>"
                               f"</head><body><main>{''.join(body)}</main></body></html>")
    return md_path, html_path

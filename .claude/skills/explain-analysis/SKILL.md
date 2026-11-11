---
name: explain-analysis
description: Turn a socialscope analysis or scoring run into a plain-language chart explainer (a few charts, each answering one question, each followed by "What it shows / What it means / How far you can take it"), written to docs/<topic>-explained.md plus a self-contained HTML page sent to the user. Every explainer must look different from the last (rotate chart forms, opening device and lead color; see the log). Use after ANY data analysis, scoring run, or results file, and whenever the user asks what results mean, for a graphic, or for an infographic.
---

# Explain an analysis with charts

The user is not a statistician. Results tables (AUC, recall at FPR, CIs) don't tell them what the data means. Every
analysis therefore ships with an explainer in the style of `docs/repull-explained.md`, which the user called "super
good". That file and its generator `docs/figures/repull_explained.py` are the worked example; read them before
starting.

## Outputs

- `docs/figures/<topic>_explained.py`: the generator script. Numbers are typed in, with a comment naming the results file each came from.
- `docs/figures/explained_<topic>_<n>_<name>.png`: one PNG per chart, at 150 dpi.
- `docs/<topic>-explained.md`: the repo copy. Charts are linked, so it renders on GitHub.
- `docs/figures/<topic>_explained.html`: the self-contained page, with images inlined. Send it with SendUserFile (`display: "render"`); the user often reads on a phone.

`explainer_kit.py` (next to this file) supplies the palette, chart helpers and `write_docs()`, which writes both
the .md and the .html.

## Procedure

1. **Read the results**: the results file, the predictions file and anything scored. Only aggregates go into the explainer.
2. **List the questions a non-expert would ask**, then pick 4-8. One chart per question, and the chart title *is* the
   question or its answer ("Who is in the flagged pile?", "Old accounts fool the age rule, not the detector"). Drop
   any chart that only restates a table. Graphs for meaning, never graphs for the sake of graphs.
3. **Choose the form by the job.**

   | Question | Form | Kit helper |
   |---|---|---|
   | "How often does X happen?" | Icon array, out of 100 | `icon_array` |
   | "If it flags something, is it right?" | Counts per 10,000 under 1-2 stated scenarios | `stacked_pile` |
   | "What does turning the dial cost?" | Trade-off line: settings as labeled dots, plus a guessing line | (see repull example 3) |
   | "Before vs after" / "A vs B" | Horizontal bars with 95% range lines | `hbars` |
   | "What drives it?" | Ranked bars with plain-English labels | `hbars(ci=False)` |
   | "Does it work for every group?" | Grouped bars, at most 3 colors | (see repull example 6) |
   | "Is this more than chance?" | Observed vs "expected by chance" bar | `hbars`, expected bar in `REF` grey |

4. **Translate everything into counts and plain words.** Write "62 of 100 bots", not "recall 0.62". Put
   "1 false alarm per 100 ordinary accounts" in axis labels. Rename features in English ("recent posts land in
   subreddits it never used before", not `pw_new_subreddit_share`; look up the definition in the code first).
   Use "range" for a 95% CI.
5. **Write the three parts under each chart.**
   - **What it shows:** what is literally on the chart, with the key numbers.
   - **What it means:** the takeaway in one or two sentences.
   - **How far you can take it:** what can and can't be concluded, the uncertainty in plain words, and any
     rough extrapolation, shown with its arithmetic and its assumptions. Label your own interpretation "my reading".
6. **Frame the page.** Open with a one-paragraph background and a short glossary covering only the words used.
   Close with a "Bottom line" of 4-6 bullets and a caveat on anything unreproduced or excluded.
7. **Render, then look at every PNG** with Read before sending. Fix collisions, clipped labels and overlaps; the
   first render nearly always has some.
8. **Send the HTML page.** Commit only after the user has looked and said so. Commit the script, PNGs, .md and .html together.

## Keep it fresh: no two explainers look the same

The user wants every explainer to feel new: engaging and unique, not the same charts with different numbers.
Variety comes second to clarity. The question still picks the form, but most questions can be answered well by
several forms, and among those, pick the one not used recently.

1. **Check the log first.** `docs/figures/explainer_log.md` lists the forms, lead colors and opening device of every
   past explainer. Don't reuse the previous explainer's opening chart or headline device. Across any explainer, at
   most half its forms may repeat from the previous one.
2. **Draw from the wider menu.** Each question below has several good forms; the kit has helpers for many of them.

   | Question | Forms to rotate between |
   |---|---|
   | How often / what share | icon array (100 dots), waffle of a whole, single hero number with a sentence, a "1 in N" person row |
   | Is a flag right | flagged pile (stacked counts), a two-step flow (all accounts → flagged → real), side-by-side icon arrays per scenario |
   | Before vs after, A vs B | bars with ranges, slope chart (`slope`), dumbbell (`dumbbell`), arrow from old to new on one line |
   | Trade-off / dial | trade-off line with labeled settings, small table of three settings as tiles, a staircase of "each step buys X, costs Y" |
   | What drives it | ranked bars, lollipops (`lollipop`), "signal cards" in a grid with a one-line example each |
   | Across groups | grouped bars, small multiples (one mini chart per group, same axis), dot strip per group |
   | More than chance | observed vs expected bars, a dot on a strip of "what chance would give", a ratio stated big ("6x") |
   | Over time | annotated line with event callouts, calendar heatmap, before/after bands, a bump chart for rankings |

3. **Vary the devices, not just the chart types.**
   - Open some explainers with a hero number and a one-line verdict.
   - Annotate the key point directly on the chart (an arrow and a short note) instead of only in the text.
   - Write chart titles as headlines that state the finding.
   - Use a two-panel "myth vs reality" layout or a "what we expected / what we got" pairing where it fits.
   - Use a different picture for the opening analogy (people, accounts, a pile, a funnel).
4. **Vary the color lead within the rules.** `K.lead("blue" | "orange" | "aqua")` reorders the three validated
   colors. Any order of those three passes the colorblind checks, because they pass for every pair. Lead with a
   different one than last time. Don't add other hues without running the dataviz validator, which needs node
   (not installed on the laptop). Within one explainer, a color keeps its meaning on every chart.
5. **Log it.** After the user has seen it, add a row to `docs/figures/explainer_log.md` with the forms, lead color
   and opening device used.

Never trade honesty for novelty. No 3-D, no pie charts with more than two slices, no dual axes, no truncated
bars, and no decoration that hides the number.

## Style

- Palette from the kit. Grey (`REF`) marks old, baseline or chance. At most three colored series; past that,
  split the chart. Get the colors from `K.lead(name)`, which rotates the lead color (see "Keep it fresh").
- One axis per chart, never two. Light hairline grid, no chart box. Values labeled selectively.
- Text stays in ink colors; the colored mark carries identity.
- Phone-friendly: about 8-9.5 inches wide, short charts, and labels at 10 pt or more.

## Guard rails (these override style)

- **Aggregates only.** No usernames, nicks or per-account rows in charts or text. Reddit accounts stay hashed.
  Never per-person hostility, raid or harassment labels.
- **Flags are leads, never proof.** Say so wherever a flag rate appears. Name nothing as a bot beyond what the
  user's rules allow.
- **Predictions are untouched.** The explainer reports what the results file says; it never rescores or reinterprets
  a prediction's verdict.
- **Unreproduced numbers stay out** (laptop RAM fault, Nov 2026): use only outputs a second identical run
  reproduced, and say what was left out.
- **Never read raw data in the generator.** Type numbers in from results files, so the script never touches account data.

## Environment (laptop)

matplotlib is not in the project venvs. Make a throwaway venv in the session scratchpad:

```bash
python3 -m venv "$SCRATCH/vizenv" && "$SCRATCH/vizenv/bin/pip" install -q matplotlib
"$SCRATCH/vizenv/bin/python" -I docs/figures/<topic>_explained.py
```

The generator imports the kit with
`sys.path.insert(0, os.path.join(<repo>, ".claude", "skills", "explain-analysis"))`. The cloud session can't run
commands: it can draft the questions and text, and the laptop session renders.

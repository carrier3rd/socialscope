"""One-line function calls for every analysis in the skill.

    from socialscope import toolkit as tk
    tk.coordination("pulls/*.zip", out="out/coord", known_bots="botbouncer.zip", known_before="2026-10-06")
    tk.topics("pulls/*.zip", out="out/topics")
    tk.crosslinks("pulls/*.zip", out="out/crosslinks")
    tk.stance_subjects("pulls/*.zip", subjects={"Trump": "trump|maga"}, cells=["Destiny:Trump"], out="out/subj")
    tk.stance_tally("out/subj/stance_key.csv", "out/subj/codes.csv", out="out/subj")

Each wraps the command-line script of the same job, so results match the CLI exactly. Keyword names
follow the script's flags with dashes turned into underscores; True adds a bare flag, lists repeat or
space-separate as the flag expects.
"""
import glob, os, runpy, sys

_SCRIPTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")


def _files(inputs):
    out = []
    for p in ([inputs] if isinstance(inputs, str) else inputs):
        out += sorted(glob.glob(p)) or [p]
    return out


def _run(script, positional=(), repeat=(), **opts):
    argv = [script] + list(positional)
    for k, v in opts.items():
        if v is None or v is False:
            continue
        flag = "--" + k.replace("_", "-") if len(k) > 1 else "-" + k
        if v is True:
            argv.append(flag)
        elif isinstance(v, (list, tuple)):
            if k in repeat:
                for x in v:
                    argv += [flag, str(x)]
            else:
                argv += [flag] + [str(x) for x in v]
        else:
            argv += [flag, str(v)]
    old = sys.argv
    sys.argv = argv
    sys.path.insert(0, _SCRIPTS)
    try:
        runpy.run_path(os.path.join(_SCRIPTS, script), run_name="__main__")
    except SystemExit as e:
        if e.code not in (0, None):
            raise
    finally:
        sys.argv = old
        sys.path.remove(_SCRIPTS)


def coordination(inputs, out="out/coordination", **opts):
    """Talking points, cross-community spread, sync network, per-account bot signals (analyze.py).
    Common opts: reveal="none|bots|all", known_bots=[files], known_before="YYYY-MM-DD",
    new_account_pct=3, skip_authors="a,b", similarity=0.9, salt="..."."""
    kb = opts.pop("known_bots", None)
    _run("analyze.py", _files(inputs), o=out, known_bots=_files(kb) if kb else None, **opts)


def crosslinks(inputs, out="out/crosslinks", **opts):
    """Kumar et al. cross-link mobilization test. opts: window_hours, ratio, min_member, skip_authors."""
    _run("crosslinks.py", _files(inputs), o=out, **opts)


def topics(inputs, out="out/topics", **opts):
    """Topic clusters and most-mentioned names per sub. opts: topics, names, min_docs, seed."""
    _run("topics.py", _files(inputs), o=out, **opts)


def sentiment(inputs, target, out="out/sentiment", **opts):
    """VADER tone toward a target (tone only, not stance). opts: exclude, sample, top, seed."""
    _run("sentiment.py", _files(inputs), o=out, target=target, **opts)


def stance_sample(inputs, target, context="", out="out/stance", **opts):
    """Blind stance sample for one person in one dispute. opts: per_sub, min_words, seed, skip_authors."""
    _run("stance.py", ["sample"] + _files(inputs), o=out, target=target, context=context, **opts)


def stance_subjects(inputs, subjects, cells=None, out="out/subjects", **opts):
    """Blind sentiment sample for several subjects. subjects: {"Name": "regex"}; cells: ["Sub:Name", ...]."""
    _run("stance.py", ["subjects"] + _files(inputs), repeat=("subject",), o=out,
         subject=[f"{k}={v}" for k, v in subjects.items()], cells=cells, **opts)


def stance_tally(key, codes, out="out/stance", corrections=None):
    """Per-sub (or sub x subject) stance shares, net score, intervals, upvote medians."""
    _run("stance.py", ["tally"], key=key, codes=codes, o=out, corrections=corrections)


def stance_agree(codes, codes2):
    """Cohen's kappa between two coders on shared items."""
    _run("stance.py", ["agree"], codes=codes, codes2=codes2)


def calibrate(analysis_dir, botbouncer=None, bots=None):
    """Recall of an analyze.py run against known bots (Bot Bouncer dumps or a username list)."""
    _run("calibrate.py", analysis=analysis_dir, botbouncer=_files(botbouncer) if botbouncer else None, bots=bots)

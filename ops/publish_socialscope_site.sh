#!/bin/bash
# Rebuild the socialscope site (Lookup page, Bots and About tabs) and push it to this repo's gh-pages branch.
# Split from the DGG chat site on Nov 19 2026 (the DGG site now lives in the dgg-chat-site repo).
# Run every 15 minutes by socialscope-site.timer, so a reversed Bot Bouncer listing comes off at the next rebuild.
set -euo pipefail
REPO="$HOME/socialscope"
SITE="$HOME/socialscope-pages"      # git worktree of this repo's gh-pages branch
[ -d "$SITE" ] || { echo "missing $SITE (git -C $REPO worktree add $SITE gh-pages)"; exit 1; }
rsync -a --delete --exclude data/ --exclude .git --exclude py/ "$REPO/site/public/" "$SITE/"
# Lookup tab (Nov 13 2026): the browser runs the same Python as scripts/lookup.py, copied from the repo on every
# publish so the two never drift. The package __init__ is empty (the repo's imports arctic, which needs the network).
rm -rf "$SITE/py"; mkdir -p "$SITE/py/socialscope"
for f in signals.py hijack.py prewindow.py history.py lookup_core.py salt.py sources.py vocab.txt; do cp "$REPO/socialscope/$f" "$SITE/py/socialscope/"; done
: > "$SITE/py/socialscope/__init__.py"
# Version-tag app.js, lookup.js and style.css so browsers pick up new code at once (Pages caches them for 10 minutes).
v=$(cat "$SITE/app.js" "$SITE/style.css" "$SITE/lookup.js" "$SITE"/py/socialscope/* | sha1sum | cut -c1-8)
sed -i "s#href=\"style.css\"#href=\"style.css?v=$v\"#; s#src=\"app.js\"#src=\"app.js?v=$v\"#; s#src=\"lookup.js\"#src=\"lookup.js?v=$v\"#" "$SITE/index.html" "$SITE/lookup.html"
: > "$SITE/.nojekyll"
mkdir -p "$SITE/data"
# Bots tab (Nov 11 2026): confirmed bot finds, rewritten every run so a reversed listing comes off at once.
python3 -I "$REPO/scripts/botfinds/build_site_bots.py" --out "$SITE/data"
cd "$SITE"
git add -A
# Commit only when something other than botfinds.json's "updated" timestamp changed (Nov 26 2026: the timestamp alone
# made a commit every 15 minutes, 96 a day). The Bots tab then shows when the bot list last changed. A reversed
# listing still comes off at the next run: it changes "bots", not just the timestamp.
if git diff --cached --quiet -I '^ *"updated": '; then
  git reset -q && git checkout -q -- .     # working tree back to what is published
  echo "socialscope site: no changes"; exit 0
fi
git commit -q -m "Site update $(date -u +%Y-%m-%dT%H:%MZ)"
git push -q origin gh-pages
echo "socialscope site: pushed $(date -u +%FT%TZ)"

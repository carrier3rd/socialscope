# Added Nov 19 2026 (laptop session): without this file, "from test import make_fake_bsky" in
# test_bsky_collect.py found Ubuntu's standard-library "test" package first (a regular package beats a
# namespace folder), so the module failed to import on the laptop. It worked in the cloud container,
# whose Python has no stdlib test package. With this file the repo's test/ (first on sys.path) wins.

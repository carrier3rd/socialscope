"""socialscope: pull Reddit data from Arctic Shift and analyze bots, coordination and opinion.

Modules
  arctic   pull_subreddits, pull_user_histories, pull_thread_context   (needs internet to Arctic Shift)
  screen   shortlist                                                    (stage 1: who to check)
  history  score, context_summary                                       (stage 2: full-history checks)
  toolkit  coordination, crosslinks, topics, sentiment, stance_*, calibrate   (existing analyses as calls)
  signals  small shared functions (AI-style score, account age from ID, intervals, dormancy)
"""
from . import arctic, signals  # noqa: F401

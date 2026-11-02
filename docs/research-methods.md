# Methods from outside research, checked against the papers (Nov 2, 2026)
Gemini drafted these extracts. I checked each item against the paper's HTML or PDF, and corrections are marked.

## Hanley, Okabe & Durumeric 2025, news narrative tracking (arXiv 2501.09102)
- **Embeddings:** e5-base-v2, fine-tuned with LoRA (rank 8, alpha 16) and unsupervised SimCSE contrastive learning.
  Gemini said "LLM embeddings"; the paper names this specific model.
- **Clustering:** parallel DP-Means on GPU FAISS, with a cosine threshold of 0.50 for a passage joining a story.
  Gemini merged two separate things here. The 0.50 cosine threshold is one. The other is a pruning rule that drops a
  cluster when 50% or more of its passages come from one website.
- **Evaluation:** max F1 of 0.793 on SemEval 2022 Task 8 (passage-pair story matching), and 99.3% estimated precision
  from hand-checking 30 final clusters.
- **For us:** the closest analogue to the single-website rule would drop talking-point clusters where one account or
  one thread supplies half the comments. e5-base-v2 runs on CPU.

## Antonakaki & Ioannidis 2026, Synthetic Narrative Coordination (arXiv 2605.21540)
- **D, lexical diversity:** MATTR with a 500-token window.
- **B, burstiness:** (σ−μ)/(σ+μ) of inter-event times, in the range [-1, 1].
- **R, rhetorical repetition:** mean Jaccard overlap of each source's top-100 word trigrams with every other source's.
- **H, semantic homogenization:** mean pairwise cosine of paraphrase-multilingual-MiniLM-L12-v2 embeddings (384-dim),
  using up to 800 messages per source per event.
- **Combined score:** SNC = 0.25·H + 0.25·B + 0.25·R − 0.25·D, with each term min-max normalized within its event
  window. Correction: Gemini's "SNC > 0.55 = coordinated" is not in the paper. There is no decision threshold, and
  0.55 is only a value the paper reports. The score ranks sources within a window; it does not classify them.

## Kruk et al. 2024, Silent Signals (ACL 2024; arXiv 2406.06840)
- **Dataset:** 16,550 instances, 298 dogwhistles, 706 surface forms; 79.8% Reddit (45 controversial subs, via
  Pushshift) and 20.2% Congressional Record.
- **Models:** prompting only, with GPT-3.5, GPT-4, Gemini and Mixtral. Correction: Gemini's HateBERT, LoRA,
  fine-tuning and carbon-emissions claims are not in this paper, and its loader code describes nothing the paper did.
- **Prompt:** Wikipedia's dogwhistle definition, then "Does the following sentence contain a dog whistle? If it does,
  please identify the dog whistle."

## Sucu et al. 2026, stance with user context (arXiv 2602.04750)
- **Models:** Claude 3.7 Sonnet, Grok-2, GPT-4o Mini, Mistral Small-24B, Llama 3.1-70B, Qwen 2.5-72B and Gemini 2.0
  Flash. Correction: Gemini listed GPT-4 Turbo, which is not among them.
- **Gains:** +17.5 to +38.5 points of accuracy from adding user context.
- **Post selection:** 10-20 posts picked for political signal is near-optimal; the final runs used 50.
- **Profile JSON:** leaning, confidence, 3-5 indicators, topics, language style, sentiment targets and notes.
  Gemini's prompt text matches the paper's appendix.
- **For us:** any user-history context would break the blind coding, since it reveals community. Use it for the
  automated stance coder, not for the human sheets.

# Evidence behind the context-gathering skill

Status: **V** = checked against the paper's full text in the Nov 12 2026 research rounds; **P** = preprint (checked,
not peer reviewed); **U** = not verified, do not cite as fact. Full notes, corrections and the three research
reports are kept outside the public repo.

## How often context changes labels, and which way
| Claim | Source | Status |
|---|---|---|
| 13/250 (5.2%) Wikipedia comments changed toxicity with parent + title (9 up, 4 down); context-aware models gained nothing | Pavlopoulos et al., ACL 2020 — https://aclanthology.org/2020.acl-main.396.pdf | V |
| CCC: 66.1% unchanged, 24.3% less toxic (2,408), 9.6% more (960) with parent; 94.7% unchanged when binarised | Xenos et al., WOAH 2021 / First Monday 2022 — https://aclanthology.org/2021.woah-1.15 , https://arxiv.org/abs/2111.10223 | V |
| Text-only BERT predicts context-sensitivity, AUC 80.46 / AUPR 42.01; parent did not help. Label is one-sided (δ > t = decreases only) | Xenos et al. (same) | V |
| Abusive tweets 18% → 10% (1,472 → 800 of 8,018) with all preceding tweets; profanity–label phi 0.77 → 0.39 | Menini et al. 2021 — https://arxiv.org/abs/2103.14916 | P |
| 38.3% of Reddit hate/counter/neutral labels changed with the parent; dominant shift Neutral → Hate/Counter (Table 3) | Yu, Blanco & Hong, NAACL 2022 — https://aclanthology.org/2022.naacl-main.433.pdf | V (prose vs table conflict: follow the table) |
| Parent fixed 35% of GPT-3.5 errors on replies: 40% of false positives, 6% of false negatives (95 subreddits) | Kumar, AbuHashem & Durumeric, ICWSM 2024 — https://arxiv.org/abs/2309.14517 | V |
| Context changes toxic → non-toxic mostly, driven by context polarity; context-aware models no better | Anuchitanukul, Ive & Specia 2022 — https://arxiv.org/abs/2111.12447 | V (venue U) |
| Annotators asked for context on 30% of Reddit comments for irony; moved more ironic → unironic after seeing it | Wallace et al., ACL 2014 — https://aclanthology.org/P14-2084 | V |
| Missing information was the main cause of only ~14% of 3-2 annotator splits | Sandri et al., EACL 2023 — https://aclanthology.org/2023.eacl-main.178 | V |
| LLM recall gains from thread context concentrated in items scored lowest without context | HICC, KONVENS 2025 | V |

## Deciding whether context is needed
| Claim | Source | Status |
|---|---|---|
| "Do I need a follow-up?" self-check AUROC 0.37–0.55, often worse than random | Zhang & Choi, Findings NAACL 2025 — https://aclanthology.org/2025.findings-naacl.306 | V |
| Two LLMs agreed on "is this context-dependent?" 63% (κ 0.26) | Shi et al., Findings ACL 2026 — https://aclanthology.org/2026.findings-acl.322/ | V |
| Sufficiency rater 93% accurate (115 items); models still right 35–62% with insufficient context; selective generation +2–10% | Joren et al., ICLR 2025 "Sufficient Context" | V |
| Cheap uncertainty gates match complex adaptive-retrieval pipelines on single-hop QA (1.6–1.8 LM calls vs 4.5–55) | Moskvoretskii et al., ACL 2025 | V |
| Multi-annotator prediction spread tracks human disagreement better than softmax | Davani, Díaz & Prabhakaran, TACL 2022 | V |
| Claude API returns no token logprobs | docs.claude.com (OpenAI-compat endpoint: logprobs ignored / empty) | V (checked 2026-11-12) |
| Gemini label-token logprobs: returned by `gemini-4-hydrogen`; "Logprobs is not enabled" on gemini-flash-latest, flash-lite-latest, 3-flash-preview, 3.1-flash-lite, 3.5-flash(-lite), 3.6/3.7/3.8-flash; Pro models and gemini-4-argon/carbon untested (quota 429 on this key) | live API calls, 2026-11-12 | V (this key; recheck per model) |

## Picking the context
| Claim | Source | Status |
|---|---|---|
| Zero-shot ChatGPT link F1 on STAC 59.91, below the "previous message" baseline 60.57 | Fan et al., LREC-COLING 2024 | V |
| Thread labels vs a fixed last-10 window: kappa 0.600 → 0.640 | Ravi et al. 2025 — https://arxiv.org/abs/2510.22844 | P |
| Accuracy drops 13.9–85% from input length alone | Du et al., EMNLP Findings 2025 — https://arxiv.org/abs/2510.05381 | V |
| Mid-prompt evidence can fall below closed-book (56.1%) | Liu et al., TACL 2024 "Lost in the Middle" | V |
| Self-Route: RAG first, escalate if insufficient; 65% / 39% cost cuts; 63% identical answers | Li et al. 2024 — https://arxiv.org/abs/2407.16833 | V |
| GPT-3 surfaced 69.4% of formal/offline vs 12.9% of informal/online dogwhistles | Mendelsohn et al., ACL 2023 | V |
| Over 80% of emote use on HasanAbi/other channels is channel-specific; emote-aware cues cut false positives | ToxiTwitch — https://arxiv.org/abs/2601.15605 | P |

## Use vs mention
| Claim | Source | Status |
|---|---|---|
| GPT-4 called 20% of hate counter-speech "use"; quoted counter-speech flagged 28.57% vs 7.23% unquoted; definition + reasoning + contrastive examples cut false flags 82.6% (true detection −3%) | Gligorić et al., NAACL 2024 — https://arxiv.org/abs/2404.01651 | V |
| Counter-speech about Jewish people most over-flagged (GPT-4 12.15%) | Gligorić et al. Table 5 | V |
| Older classifiers 15.6–32.9% accuracy on quoted/referenced denouncements | HateCheck, Röttger et al., ACL 2021 — https://arxiv.org/abs/2012.15606 | V |

## LLM direction effects
| Claim | Source | Status |
|---|---|---|
| Models drift toward a scripted 90% yes/no verdict history (~5 points; 2x on uncertain items) | AMEL — https://arxiv.org/abs/2605.22714 | P |
| Claude Haiku 5.5: toxic reply looked *less* toxic next to a toxic parent; humans moved the other way; "you" text over-flagged 12% → 51% | Yue & Vance — https://arxiv.org/abs/2610.23446 | P |
| First discordant context item does most of the damage | Wang et al., EMNLP 2025 — https://arxiv.org/abs/2509.04500 | V |
| Models flip answers under "Are you sure?" 32–86% | Sharma et al., ICLR 2024 — https://arxiv.org/abs/2310.13548 | V |
| Conformity to a simulated majority grows with majority size | Weng et al., ICLR 2025 — https://arxiv.org/abs/2501.13381 | V |

## This project's own calibration (Nov 12 2026)
| Result | Source |
|---|---|
| socialscope, 113 replies, Claude coder: context flips 4.4% (replicate 8.8%) vs rerun noise 4.4–7.1%; placebo 5.4%; 2 robust flips of 103 (a question-reply, a `>`-quote rebuttal) | `docs/context-flip-calibration-results.md` |

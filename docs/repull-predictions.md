# Re-pull fix: predictions (written Nov 5, 2026, before the re-pull or any rescoring)

Change under test: banned accounts' histories re-pulled ending at their Bot Bouncer listing date, controls pulled to
matched anchor dates with the same per-kind cap, "[removed]"/"[deleted]" bodies excluded from the 30-day-window
features, the 1% threshold set from training controls (cross-validated), and bootstrap CIs over accounts.

## Old numbers (in-sub test set)
Gradient boosting: 67% recall at 1% false alarms (Wilson 60-74%), AUC 0.97; 57% without volume features; 62% against
size-matched controls; ~40% precision at a 1% bot rate.

## Predictions
1. **Headline drops.** Recall at 1% false alarms falls to 45-60% (best guess 55%), and the bootstrap CI does not
   reach 67%. Confidence: medium.
2. **AUC drops less.** AUC lands at 0.90-0.95. The cap artifact mostly sharpens the extreme tail, which the 1% cutoff
   lives in, so recall moves more than AUC. Confidence: medium.
3. **Volume stops leading.** items, log_items and hist_age leave the top 5 permutation importances; true_age and
   solicit_broad move up. Confidence: medium-high.
4. **Aged bans take the hit.** The cap only binds on accounts with over 1,000 items, so the recall drop is concentrated
   in aged (hijacked) bans; throwaway recall changes by under 5 points. Confidence: medium.
5. **Ablation gap closes.** With the fix, the gap between the full model and the no-volume model shrinks to under 5
   points, because the volume features were carrying the artifact. Confidence: medium.
6. **Thresholds wobble.** The bootstrap CI on recall at 1% is at least 15 points wide once threshold uncertainty is
   included, wider than the old Wilson interval (14 points). Confidence: medium-high.
7. **Pending signal survives.** Of accounts pending at Oct 28, the share flagged at 1% stays well above the share of
   random controls flagged; the blind-read gap (16/30 vs 5/30) passes Fisher's exact test at p < 0.01. Confidence:
   medium (the Fisher part can be checked now; the rest after rescoring).

## Scoring
Scored in repull-results.md, hit / miss / partial with numbers. Misses stay in.

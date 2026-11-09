# Brigade alarm: predictions (written Nov 5, 2026, before any data was looked at)

Method under test: for each sub, model the hourly count of "outsider" activity (comments by accounts whose home
community is a different one of the 18 subs) as a time-varying Poisson process with a daily cycle, fit on baseline
weeks. Flag hours whose count exceeds the 99.9th percentile of that distribution. Test on the Oct 27 - Nov 2 week.

## Predictions
1. **Plain Poisson fails.** Hourly outsider comment counts will be strongly overdispersed even after the daily cycle
   (variance/mean well above 1, likely 5+ in the big subs), so a Poisson alarm will fire far more often than 0.1% of
   hours. A negative binomial baseline will be needed. Confidence: high.
2. **Counting accounts helps but doesn't fix it.** Counting distinct outsider accounts per hour, instead of comments,
   cuts the dispersion (one person arguing in a thread inflates comment counts) but stays above 1. Confidence: medium-high.
3. **Where alarms land.** Most alarm-hours will be in h3h3productions, LeftoversH3 and neoliberal, matching the known
   hostile crossings. Destiny will be the most common home sub of the outsiders in them. Confidence: medium.
4. **Pakman stays quiet.** thedavidpakmanshow has a high outsider share but a steady one, so few alarms despite being
   the most "invaded" sub by volume. Confidence: medium.
5. **Thread concentration.** In most alarm-hours, one thread carries over half of the outsider activity (link-driven
   brigade), against well under half in normal hours. Confidence: medium.
6. **Brigades are people.** Accounts on the Bot Bouncer ban lists make up under 5% of outsider accounts in alarm-hours,
   no higher than in normal hours. Confidence: medium.

## Scoring
Each prediction gets scored hit / miss / partial, with the number, in brigade-alarm-results.md. Misses stay in.

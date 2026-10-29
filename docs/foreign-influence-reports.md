# Foreign Influence Reports: What We Used

Oct 29, 2026 · @Joseph

Seven government and platform reports on foreign information operations, read for one purpose: improving the two checks in the social-coordination project, bot detection and opinion-bundle tracking on the streamer and drama subreddits. Each section gives what the report found, then what we took from it.

## The short version

- **The bots these reports chase are a different species from the ones we've been catching.** The reports describe bought, aged accounts that get warmed up with ordinary posts, then turned to politics, with little real engagement. The drama-sub bots in our rounds are days-old accounts with a handful of comments. That's why account age works for us and why the new report-derived rules don't separate round 2 bots from controls.
- **Laundered narratives don't arrive as links.** Across about 1.2 million comments from rounds 1 to 3 and the Oct 13–19 week, the expanded Kremlin narrative watchlist found 72 matches. One clearly asserted a false narrative. The rest debunked, mocked, or were history talk the pattern caught by mistake.
- **Seeder-and-amplifier pairs, the reports' core coordination pattern, don't show up in our data.** No pair of accounts repeatedly echoed each other's positions in 3+ threads.

## EU External Action Service: 4th threat report (March 2026)

**Found:** 540 incidents in 2025; 29% attributed to Russia, 6% to China, the rest unattributed but linked by coordination indicators. About 10,500 channels and websites involved; 88% of the 43,000 pieces of content sat on X. AI showed up in 27% of incidents, up from 41 incidents the year before. Most operations inflate their numbers and get little organic engagement. Storm-1516 was the only one that reliably reached real audiences. Two coordination shapes recur:

- **Seeders and amplifiers:** a few accounts post, a reused set reshares within minutes. One for-hire network boosted both Russian and Chinese content, as if handed a list of posts.
- **Reply clusters:** fake dissidents post a claim, a second cluster replies to officials, and a third posts screenshots and hashtags.

Narratives: discrediting pro-EU and pro-Ukraine leaders (corruption, health), immigration and refugee division, the EU as authoritarian (the Democracy Shield as censorship), imminent war, election-day terror threats, the "multipolar world" and a decadent West. China: the EU as subservient to the US, and defense on Taiwan, Hong Kong, Xinjiang and Tibet.

**Took:** the seeder-amplifier check for the bundle analysis; low\_engagement as a bot rule; the "EU censorship regime" narrative, filed as framing.

## France, VIGINUM: Storm-1516 (2025)

**Found:** 77 operations from 2023 to March 2025, coordinated by a suspected Russian military intelligence officer, drawing on former Prigozhin troll-farm staff and John Mark Dougan's network of 290+ fake news sites. Each operation follows the same chain:

1. Buy aged accounts in batches and warm them up with neutral posts for weeks.
2. Post a staged video, often with amateur actors with Eastern European accents or deepfake voices, from a fake whistleblower account.
3. Repost it on a second platform the same day.
4. Launder it through a paid article in an African or Middle Eastern outlet the next day.
5. Amplify through fake local news sites, X accounts and Telegram within hours to days.
6. Delete or privatize the accounts after debunking.

Targets included the 2024 US election: the Bucks County ballot video, Haitian voters in Georgia, and the Kamala Harris hit-and-run story.

**Took:** political\_pivot (warm-up then politics), sub\_shift (resold accounts) and batch\_id (accounts created in a batch) as bot rules; four Storm-1516 narratives for the watchlist (the three above plus fake Kenyan workers in Germany).

## Taiwan, National Security Bureau: 2025 report (January 2026)

**Found:** 45,590 fake accounts in 2025, up from 28,216; about 2.3 million pieces of disinformation. Chinese firms build databases of commenters and automate bot accounts; paid commenters work in 20+ languages. Facebook content farms build traffic with sensational posts, then switch their Threads and X accounts to politics. More than a dozen accounts on PTT, Taiwan's big forum, were hijacked through compromised devices during military exercises.

**Took:** support for political\_pivot (content farms pivoting) and sub\_shift (hijacked accounts suddenly posting somewhere new).

## UK: sanctions on Russian information operations (2024–2026)

**Found:** 106 people and organizations sanctioned since October 2024, including the Social Design Agency (Doppelganger), Rybar, the Centre for Geopolitical Expertise (linked to Storm-1516) and hosting providers. Techniques named: cloned news sites, bot accounts, forged documents and deepfakes, AI content for fast reaction to events, paying voters.

**Took:** confirmation that the forged-document column in the narrative watchlist matters; no new detection rule, since the UK publishes enforcement more than method.

## Meta: adversarial threat report (2026)

**Found:** every coordinated fake-account network it removed in the first half of 2026 used AI in some form. Doppelganger offshoots targeted Armenia and Moldova; influence-for-hire networks ran from Israel and Iran. Detection leans on behavior, technical indicators and network structure, which AI doesn't hide well. It caught a stockpile of 575,000 dormant accounts partly through generated usernames a native speaker wouldn't choose.

**Took:** support for keeping gibberish\_name as a secondary check and for batch\_id.

## OpenAI: influence-operation reports (2025–2026)

**Found:** "Sneer Review", a China-linked operation, posted on Reddit, X, TikTok and Facebook and wrote replies to its own posts to fake engagement. "Helgoland Bite", Russia-linked, ran a fake local German news channel. Most operations reached few real people.

**Took:** tested a reply-pair check (two accounts repeatedly replying to each other). Round 2 had 120 such pairs, almost all regulars arguing, one involving a known bot. Dropped as a rule, kept as a review metric.

## Canada: Rapid Response Mechanism

**Found:** public exposures of China-linked Spamouflage campaigns against MPs and Chinese-language commentators in Canada (2023, 2025), and WeChat operations around the 2025 election; G7 monitoring reports on Moldova's and Armenia's elections. The public pages list findings without detection methods.

**Took:** nothing new for detection.

## What changed in the project

**Bot checks (four new secondary rules, frozen before the bot-rich scoring):**

| Rule | Fires when | Round 2: bots vs controls |
| --- | --- | --- |
| political\_pivot | first 70% of history 5% or less political, last 30% at least 30% | 0% vs 0% |
| sub\_shift | 180+ day silence, no subreddit in common before and after | 4% vs 1% |
| low\_engagement | 30+ comments, median score 1 or less, 90th percentile 2 or less | 8% vs 3% (later bots) |
| batch\_id | account ID within 5,000 of another in the pool | 0% vs 0% |

They don't separate drama-sub bots, as expected: these rules target aged, bought accounts. The bot-rich round, drawn from Bot Bouncer bans across all of Reddit, is the real test.

**Opinion bundles:**

- **Seeder-amplifier pairs:** an account that repeatedly asserts the same position in the same thread within an hour of another, across 3+ threads. First run: 0 pairs.
- **Opposed positions:** accounts asserting both sides of a split, like pro- and anti-Hasan. First run: 18 accounts, mostly people arguing both sides or pattern misfires. A lead to read, nothing more.

**Narrative watchlist:** six new rows (Bucks County ballots, Haitian voters in Georgia, Harris hit-and-run, USAID paying celebrities to visit Ukraine, Kenyan workers in Germany, EU censorship regime as framing). The Nazi-regime pattern was tightened: bare "denazification" mostly matched WWII history talk.

**First run, all data:** predicted under 60 matches, a handful for the US election fakes, and no account asserting more than once. Actual: 72 matches before the pattern fix, 0 for the US election fakes, one clear assert (Zelensky buying Spanish villas with aid money) and one ambiguous one ("Ukraine was doing biolabs, bro"). No account asserted twice.

## Sources

- [EEAS 4th threat report (PDF)](https://www.eeas.europa.eu/sites/default/files/2026/documents/EEAS%204th%20Threat%20Report_web.pdf)
- [VIGINUM Storm-1516 report (PDF)](http://www.defense.gouv.fr/sites/default/files/desinformation/Rapport%20Storm%201516%20-%20SGDSN.pdf)
- [Taiwan NSB report (Taipei Times)](https://www.taipeitimes.com/News/front/archives/2026/01/12/2003850442)
- [Taiwan NSB report (Taiwan News)](https://www.taiwannews.com.tw/en/news/6280662)
- [UK action against foreign information warfare](https://www.gov.uk/government/publications/uk-action-against-russian-foreign-information-warfare/new-uk-action-against-foreign-information-warfare)
- [Meta adversarial threat report](https://combatantisemitism.org/wp-content/uploads/2026/09/Meta-H2-2026-Adversarial-Threat-Report.pdf)
- [OpenAI: Helgoland Bite](https://openai.com/index/disrupting-malicious-uses-of-ai-helgoland-bite)
- [OpenAI takedowns incl. Sneer Review (KPBS)](https://www.kpbs.org/news/science-technology/2025/06/05/openai-takes-down-covert-operations-tied-to-china-and-other-countries)
- [Canada Rapid Response Mechanism news](https://international.canada.ca/en/global-affairs/corporate/reports/rapid-response-mechanism/news)

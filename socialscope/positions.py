import re
N = r"(?:is|was|are|'s|s|being|just|such|a|an|the|total|complete|fucking|huge|massive|literal|literally|absolute|\s)*"
NEG = r"(?:grifter|grifting|hypocrite|hypocritical|fraud|clown|loser|piece of shit|pos|scumbag|liar|lying|snake|narcissist|narcissistic|cringe|pathetic|disgusting|dickhead|asshole|idiot|moron|creep|creepy|joke|garbage|trash|insufferable|a bad person|terrible|evil|psycho|sociopath)"
POS = r"(?:right|correct|based|goated|the goat|goat|great|amazing|awesome|a good guy|a good person|a legend|legend|cooking|cooked|the best|smart|brilliant|honest)"
def tgt(names): return r"\b(?:" + names + r")\b"
P = {
 # streamers and drama
 "hasan_neg": tgt("hasan|hasanabi|hassan|hasan piker")+N+NEG+r"\b|\b(?:fuck|fuckin|fucking|hate)\s+hasan\b|\bhasan\b.{0,40}\b(?:tankie|antisemit\w*|terrorist sympath\w*|dog shock\w*|shock collar)",
 "hasan_pos": r"\bhasan\b\s+(?:is|was)\s+(?:so\s+|totally\s+|completely\s+|100%\s+)?(?:right|correct|based|goated|the goat|cooking)\b|\bi (?:love|like|agree with|stand with)\s+hasan\b|\bhasan\b.{0,15}\b(?:dub|w take|good take|cooked (?:him|them|her))\b",
 "ethan_neg": tgt("ethan|klein")+N+NEG+r"\b|\b(?:fuck|hate)\s+ethan\b|\bethan\b.{0,40}\b(?:deserves? (?:this|it|everything)|got what|karma|ruined (?:his|their|everyone)|threw away|betray\w*)",
 "hila_pos": r"\b(?:poor|protect|love|support|feel (?:bad|so bad|sorry) for|pray\w* for|thinking of|heart goes out to|stay strong)\s+hila\b|\bhila\b"+N+r"(?:deserves better|a queen|the best|strong|so strong|amazing|a saint|the real one)",
 # Israel / Gaza
 "gaza_genocide": r"\b(?:israel\w*|idf|zionis\w*|netanyahu|bibi)\b.{0,60}\b(?:genocide|genociding|ethnic cleansing|apartheid)\b|\b(?:genocide|ethnic cleansing|apartheid)\b.{0,40}\b(?:in gaza|of palestinians|against palestinians|of gaza)\b|\bfree palestine\b|\bgenocide joe\b",
 "israel_defense": r"\bgenocide libel\b|\bhamas\b.{0,40}\b(?:started (?:the|this) war|could end (?:it|this|the war)|solely responsible|uses? human shields|hides? behind civilians)|\brelease the hostages\b",
 "anti_zionist": r"\b(?:fuck|fucking|evil|disgusting)\s+zionis\w*|\bzionis(?:ts?|m)\b.{0,30}\b(?:are|is)\b.{0,15}\b(?:evil|nazis?|terrorists?|the problem|scum)|\bzios?\b",
 # Russia / Ukraine
 "ukraine_support": r"\bslava ukraini\b|\bi (?:support|stand with)\s+ukraine\b|\b(?:we|you|everyone|the us|america|europe|the west)\s+(?:should|must|need to|needs to|have to)\s+(?:support|arm|help|fund|send (?:more )?(?:weapons|aid) to)\s+ukraine\b|\bputin\b\s+(?:is\s+)?(?:a war criminal|a dictator|a monster|a murderer|evil)\b",
 # US politics
 "anti_trump": r"\btrump\b"+N+r"(?:a fascist|fascist|a dictator|a pedo\w*|a rapist|a criminal|a felon|a traitor|senile|demented|a moron|an idiot|evil|a con man|a clown)\b|\b(?:fuck|fucking)\s+trump\b|\bmaga\b.{0,30}\b(?:cult|fascis\w*|morons?|idiots?|chuds?)",
 "vote_blue": r"\bi (?:voted|vote|will vote|am voting|'m voting) (?:for )?(?:blue|dem|dems|democrat|democrats|kamala|harris|biden)\b|\b(?:you|we|people|everyone)\s+(?:should|need to|have to|must)\s+(?:just\s+)?vote\s+(?:blue|dem|democrat|for (?:the )?democrats|for kamala|for harris)\b",
 "anti_tankie": r"\b(?:dsa|socialists?|communists?|tankies?|leftists?)\b"+N+r"(?:insane|illiberal|crazy|idiots?|morons?|clowns?|losers?|cringe|antisemit\w*|the problem|useless)\b|\btankies?\b",
 "anti_ice": r"\babolish ice\b|\bice\b.{0,30}\b(?:gestapo|nazis?|thugs?|kidnapp\w*|terrori\w*|fascis\w*)|\bfuck ice\b",
 "elon_neg": r"\b(?:elon|musk)\b"+N+r"(?:a fascist|a nazi|a moron|an idiot|a clown|a loser|a fraud|cringe|a grifter|pathetic)\b|\bfuck (?:elon|musk)\b|\bnazi salute\b",
}
RX = {k: re.compile(v, re.I) for k, v in P.items()}

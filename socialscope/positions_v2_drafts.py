"""Draft fixes (v2) for patterns that read under 65% in the Oct 20-26 tier 1 subs. Written Oct 29, 2026 from the
misses in that blind read. NOT validated: each must pass a fresh blind read (~30 matches per pattern per community
type, from weeks other than Oct 20-26) before replacing its entry in positions.py.

Each entry is (include, exclude): a comment takes the position when include matches and exclude doesn't."""
import re
from .positions import P, N, NEG

V2 = {
    # "I don't feel bad for Hila", "almost feel bad for hila lol", "hard to make me feel bad for Hila"
    "hila_pos": (P["hila_pos"],
                 r"\b(?:don'?t|do not|doesn'?t|can'?t|cannot|never|not|no one|nobody|hard to make me|almost)\b.{0,25}\b(?:feel (?:bad|so bad|sorry)|empathy|sympathy)\b.{0,15}\bhila\b"
                 r"|\bhila\b\s+(?:is (?:a |just as )?genocid\w*|deserves? (?:this|it|everything))"),
    # mocking people who hate Hasan ("reasons to hate Hasan", "for those that hate Hasan", "Hasan haters")
    "hasan_neg": (P["hasan_neg"],
                  r"\b(?:reasons? to|desperate to|those (?:that|who)|people (?:that|who)|y'?all|sycophants?)\b.{0,20}\b(?:hate|fuck)\s+hasan\b"
                  r"|\bhasan haters?\b|\b(?:mehdi|mehdi hasan)\b|\bused to hate hasan\b"),
    # bare "nazi salute" only counts with Musk/Elon nearby; skip people defending or explaining the ADL line
    "elon_neg": (r"\b(?:elon|musk)\b" + N + r"(?:a fascist|a nazi|a moron|an idiot|a clown|a loser|a fraud|cringe|a grifter|pathetic)\b"
                 r"|\bfuck (?:elon|musk)\b|\b(?:elon|musk)\b.{0,60}\bnazi salute|\bnazi salute\b.{0,60}\b(?:elon|musk)\b",
                 r"\b(?:i'?m on no side|awkward gesture|benefit of the doubt|count dankula)\b"),
    # agency ICE written in capitals; drop "ice walls" and quoted slogans in mockery
    "anti_ice": (r"\babolish ICE\b|\bICE\b.{0,30}\b(?:gestapo|nazis?|thugs?|thuggery|kidnapp\w*|terrori\w*|fascis\w*)|\bfuck ICE\b",
                 r"(?:^|\s)>\s*abolish ice|\banti-fascist\b.{0,40}\bfuck ice|\bmyth busted\b"),
    # drop the bare "tankie" clause: in r/TankieTheDeprogram and r/dsa it's self-description, questions or jokes
    "anti_tankie": (r"\b(?:dsa|socialists?|communists?|tankies?|leftists?)\b" + N + r"(?:insane|illiberal|crazy|idiots?|morons?|clowns?|losers?|cringe|antisemit\w*|the problem|useless)\b"
                    r"|\b(?:hate|against|anti)\s+tankies?\b|\btankies?\b.{0,40}\b(?:support(?:ing)? putin|historical revisionism|sophistry|imperialis\w*)",
                    r"\bcall(?:ing)? us tankies\b|\btankie is when\b|\bhow are they\b"),
    # skip "fuck trump" quoted from a sign or wall, and Trump defenses phrased as complaints about the label
    "anti_trump": (P["anti_trump"],
                   r"\b(?:a wall|sign|banner|graffiti) (?:with|saying|that says)\s+\"?fuck trump|\bthey love to say trump is\b"),
}
RX2 = {k: (re.compile(i, re.I), re.compile(e, re.I)) for k, (i, e) in V2.items()}
RX2["anti_ice"] = (re.compile(V2["anti_ice"][0]), re.compile(V2["anti_ice"][1], re.I))  # case-sensitive ICE


def match(k, text):
    inc, exc = RX2[k]
    return bool(inc.search(text)) and not exc.search(text)

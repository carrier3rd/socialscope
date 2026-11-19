import json, csv, hashlib, collections, pickle
salt=open('/home/claude/socialscope/.socialscope_salt').read().strip()
H=lambda a:'acct_'+hashlib.sha256((salt+a).encode()).hexdigest()[:10]
SUBS={s.lower() for s in 'Asmongold Conservative Destiny Hasan_Piker IsraelPalestine LeftoversH3 LivestreamFail Palestine PoliticalCompassMemes TankieTheDeprogram atrioc dsa h3h3productions neoliberal samharris thebulwark thedavidpakmanshow ukraine'.split()}
G={r['username']:r for r in csv.DictReader(open('/home/claude/work/train/groups.csv'))}
ins=collections.Counter(); nsfw=collections.Counter(); tot=collections.Counter()
import re; NS=re.compile(r'nsfw|gonewild|nude|sex|horny|onlyfans|hookup|r4r|porn|cum|tits|ass',re.I)
for k in range(5):
    for l in open(f'cut_{k}.jsonl'):
        r=json.loads(l); a=H(r['author']); s=(r.get('subreddit') or '')
        tot[a]+=1
        if s.lower() in SUBS: ins[a]+=1
        if NS.search(s): nsfw[a]+=1
pickle.dump((ins,nsfw,tot),open('insub.pkl','wb'))

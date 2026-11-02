import json, csv, hashlib, sys, collections, pickle
sys.path.insert(0,'/home/claude/socialscope')
from socialscope import hijack, prewindow
salt=open('/home/claude/socialscope/.socialscope_salt').read().strip()
H=lambda a:'acct_'+hashlib.sha256((salt+a).encode()).hexdigest()[:10]
G={r['username']:r for r in csv.DictReader(open('/home/claude/work/train/groups.csv'))}
first=json.load(open('/mnt/user-data/uploads/socialscope_data/reddit_pulls/histories/train_oldest.json'))
out={}
for k in range(5):
    by=collections.defaultdict(list)
    for l in open(f'full_{k}.jsonl'):
        r=json.loads(l); by[r['author']].append(r)
    for a,its in by.items():
        g=G[a]; anchor=float(g['listed_utc']) if g['group']!='random' else max(float(x['created_utc']) for x in its)
        cut=[x for x in its if float(x['created_utc'])<=anchor]
        n=len(cut); ts=sorted(float(x['created_utc']) for x in cut)
        fe=first.get(a)
        aged= n>=100 and ts and (ts[-1]-ts[0])>=365*86400
        try: pw=prewindow.compute_prewindow_features(cut, anchor)
        except Exception as e: pw={}
        out[H(a)]=dict(group=g['group'],split=g['split'],anchor=anchor,n_full=len(its),n_cut=n,aged=bool(aged),
            age_days=(anchor-float(fe))/86400 if fe else None,
            sh_full=hijack.solicit_handle(its), sb_full=hijack.solicit_broad(its),
            sh_cut=hijack.solicit_handle(cut), sb_cut=hijack.solicit_broad(cut), pw=pw)
    print(k,len(out),flush=True)
pickle.dump(out,open('hij.pkl','wb'))
c=collections.Counter((v['group'],v['split']) for v in out.values()); print(c)

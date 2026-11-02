import pickle, json, csv, sys, hashlib, collections
sys.path.insert(0,'/home/claude/socialscope')
from socialscope import hijack, prewindow
G,items=pickle.load(open('data.pkl','rb'))
salt=open('/home/claude/socialscope/.socialscope_salt').read().strip()
H=lambda a:'acct_'+hashlib.sha256((salt+a).encode()).hexdigest()[:10]
oldest=json.load(open('oldest_all.json'))
names=sorted(items); K=(len(names)+499)//500
fh=[open(f'cut_{k}.jsonl','w') for k in range(K)]; gw=[csv.writer(open(f'groups_{k}.csv','w',newline='')) for k in range(K)]
for w in gw: w.writerow(['username','group','reasons'])
out={}
for i,a in enumerate(names):
    k=i//500; g,anc=G[a]; its=items[a]
    ts=[float(x['created_utc']) for x in its]
    anchor=anc if anc else max(ts)
    cut=[x for x in its if float(x['created_utc'])<=anchor]
    for x in cut: fh[k].write(json.dumps(x)+'\n')
    gw[k].writerow([a,g,''])
    ct=sorted(float(x['created_utc']) for x in cut)
    try: pw=prewindow.compute_prewindow_features(cut,anchor)
    except Exception: pw={}
    fe=oldest.get(a)
    out[H(a)]=dict(group=g,anchor=anchor,n_cut=len(cut),aged=bool(len(cut)>=100 and ct and ct[-1]-ct[0]>=365*86400),
        age_days=(anchor-float(fe))/86400 if fe else None,sh=hijack.solicit_handle(cut),sb=hijack.solicit_broad(cut),pw=pw)
for f in fh: f.close()
pickle.dump(out,open('feats.pkl','wb')); print(K,'chunks',collections.Counter(v['group'] for v in out.values() if v['n_cut']>0))

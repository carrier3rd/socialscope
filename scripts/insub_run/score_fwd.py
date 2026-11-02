"""Score the forward-test cohort with the frozen in-sub model. Usage:
  python3 score_fwd.py <posts.zip> <comments.zip> <oldest.json> <users.txt> <out_dir> [cutoff_utc]
Writes <out_dir>/scores_frozen.csv (hashed accounts only) and prints its sha256. No refitting."""
import sys, os, json, csv, zipfile, collections, pickle, hashlib, math, subprocess
import numpy as np
sys.path.insert(0,'/home/claude/socialscope')
from socialscope import hijack, prewindow
posts,comments,oldest_f,users_f,out=sys.argv[1:6]; cutoff=float(sys.argv[6]) if len(sys.argv)>6 else 1793682000.0  # 2026-11-03 00:00 ET
os.makedirs(out,exist_ok=True)
M=pickle.load(open('/home/claude/work/fwd2/model_frozen.pkl','rb'))
salt=open('/home/claude/socialscope/.socialscope_salt').read().strip()
H=lambda a:'acct_'+hashlib.sha256((salt+a).encode()).hexdigest()[:10]
users={l.strip().lower() for l in open(users_f) if l.strip()}
keep=('id','created_utc','subreddit','body','title','selftext','score','link_id','parent_id','url','author_fullname','distinguished')
items=collections.defaultdict(dict)
for f in (posts,comments):
    z=zipfile.ZipFile(f)
    for n in z.namelist():
        for l in z.open(n):
            r=json.loads(l); a=r.get('author')
            if not a or a.lower() not in users or float(r.get('created_utc') or 0)>cutoff: continue
            d={k:r[k] for k in keep if k in r}
            for k in ('body','selftext'):
                if d.get(k): d[k]=d[k][:1500]
            d['author']=a; items[a][r.get('id')]=d
names=sorted(items); print(len(names),'accounts with history (of',len(users),')')
oldest=json.load(open(oldest_f))
K=(len(names)+499)//500; F={}
for k in range(K):
    with open(f'{out}/cut_{k}.jsonl','w') as fh, open(f'{out}/groups_{k}.csv','w',newline='') as gh:
        w=csv.writer(gh); w.writerow(['username','group','reasons'])
        for a in names[k*500:(k+1)*500]:
            its=list(items[a].values()); anchor=max(float(x['created_utc']) for x in its)
            for x in its: fh.write(json.dumps(x)+'\n')
            w.writerow([a,'fwd',''])
            ts=sorted(float(x['created_utc']) for x in its)
            try: pw=prewindow.compute_prewindow_features(its,anchor)
            except Exception: pw={}
            fe=oldest.get(a)
            F[H(a)]=dict(anchor=anchor,n_cut=len(its),aged=bool(len(its)>=100 and ts[-1]-ts[0]>=365*86400),
                age_days=(anchor-float(fe))/86400 if fe else None,sh=hijack.solicit_handle(its),sb=hijack.solicit_broad(its),pw=pw)
    subprocess.run([sys.executable,'-c',f"from socialscope import history; history.score(['{out}/cut_{k}.jsonl'], groups='{out}/groups_{k}.csv', out_dir='{out}/scores_{k}', oldest='{oldest_f}')"],cwd='/home/claude/socialscope',check=True,capture_output=True)
S={}
for k in range(K):
    for r in csv.DictReader(open(f'{out}/scores_{k}/accounts.csv')): S[r['account']]=r
fl=lambda x:(float(x) if x not in (None,'') else np.nan)
num,pwk,ok,gb=M['num'],M['pwk'],M['ok'],M['model']
rows=[]
for a,v in F.items():
    s=S.get(a)
    if not s: continue
    prim=float('primary' in (s['tier'] or ''))
    x=[fl(s[c]) for c in num]+[(v['anchor']-fl(s['first_seen']))/86400, v['age_days'] if v['age_days'] is not None else np.nan, float(v['sh']),float(v['sb']),prim,math.log1p(v['n_cut'])]+[fl(v['pw'].get(c)) for c in pwk]
    p=float(gb.predict_proba(np.array([x])[:,ok])[0,1])
    rows.append(dict(account=a,score=round(p,6),flag_1pct=int(p>M['threshold_1pct']),flag_5pct=int(p>M['threshold_5pct']),solicit_handle=int(v['sh']),solicit_broad=int(v['sb']),primary=int(prim),aged=int(v['aged']),n_items=v['n_cut']))
with open(f'{out}/scores_frozen.csv','w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0])); w.writeheader(); w.writerows(sorted(rows,key=lambda r:r['account']))
print('scored',len(rows),'| flagged at 1%:',sum(r['flag_1pct'] for r in rows),'| at 5%:',sum(r['flag_5pct'] for r in rows))
print('sha256',hashlib.sha256(open(f'{out}/scores_frozen.csv','rb').read()).hexdigest())

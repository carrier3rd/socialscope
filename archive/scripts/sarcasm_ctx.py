import re
import glob,json,zipfile,pandas as pd,pickle,sys
W={'aug18':'/home/claude/data/aug18','sep08':'/home/claude/data/sep08','sep22':'/home/claude/data/sep22','oct13':'/home/claude/data/oct13','oct20':'/home/claude/data/oct20all'}
k=pd.read_csv('stance_key.csv');g=pd.read_csv('gem.csv');sh=pd.read_csv('stance_sheet.csv')
x=k[k.item.isin(g.item)].merge(sh[['item','text']],on='item')
def rows(path):
    z=zipfile.ZipFile(path) if path.endswith('.zip') else None
    if z:
        for n in z.namelist():
            for l in z.open(n): yield l
    else: yield from open(path,'rb')
out={}
for w,grp in x.groupby('week'):
    N=lambda t:re.sub(r'\s+',' ',t or '').strip()[:120]
    want={N(t):i for i,t in zip(grp.item,grp.text)}; subs=set(grp.subreddit)
    hit={}; bodies={}; titles={}
    for f in sorted(glob.glob(W[w]+'/**/*',recursive=True)):
        if not (f.endswith('.zip') or f.endswith('.jsonl')): continue
        if not any(('r_'+s+'_') in f for s in subs): continue
        for l in rows(f):
            try:r=json.loads(l)
            except: continue
            if 'body' in r:
                bodies[r['id']]=r['body']
                if N(r['body']) in want: hit[want[N(r['body'])]]=(r.get('parent_id'),r.get('link_id'))
            elif 'title' in r: titles[r['id']]=(r['title'],(r.get('selftext') or '')[:300])
    for i,(p,lk) in hit.items():
        par=None
        if p and p.startswith('t1_'): par=bodies.get(p[3:])
        t=titles.get((lk or '')[3:])
        out[i]=dict(parent=par,parent_kind=p[:2] if p else None,title=t[0] if t else None)
    print(w,len(grp),'found',len(hit),flush=True)
pickle.dump(out,open('../sarc/ctx.pkl','wb'))

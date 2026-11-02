import csv, json, zipfile, pickle, hashlib, collections, glob
inv={r['username'].lower():r for r in csv.DictReader(open('/home/claude/work/bbinv/private_all.csv'))}
for r in csv.DictReader(open('/home/claude/work/insub/bbnov/private_nov.csv')): inv.setdefault(r['username'].lower(),r)
seen=pickle.load(open('/home/claude/work/seen_all.pkl','rb'))
G={}  # name -> (group, anchor or None)
ins=list(csv.DictReader(open('/home/claude/work/insub/groups.csv')))
for r in ins:
    f=r['flair_oct28']
    G[r['username']]=('test_pos' if f=='banned' else 'test_pending' if f=='pending' else None, float(r['listed_utc']))
tr=list(csv.DictReader(open('/home/claude/work/train/groups.csv')))
salt=open('/home/claude/socialscope/.socialscope_salt').read().strip()
H=lambda a:'acct_'+hashlib.sha256((salt+a).encode()).hexdigest()[:10]
for r in tr:
    if r['group']=='random' and r['username'].lower() not in inv:
        G[r['username']]=('test_ctl' if int(H(r['username'])[-1],16)%2 else 'train_ctl', None)
for f in ['/home/claude/work/augpanel/groups.csv','/home/claude/work/sep_test/groups.csv','/home/claude/work/round4_shortlist/groups.csv']:
    for r in csv.DictReader(open(f)):
        u=r['username']; l=u.lower()
        if u in G: continue
        if l in inv and inv[l]['flair']=='banned' and l in seen: G[u]=('train_pos',float(inv[l]['listed_utc']))
        elif l not in inv and r['group']=='control': G[u]=('train_ctl',None)
G={u:v for u,v in G.items() if v[0]}
print(collections.Counter(v[0] for v in G.values()))
keep=('id','created_utc','subreddit','body','title','selftext','score','link_id','parent_id','url','author_fullname','distinguished')
items=collections.defaultdict(dict)
srcs=['/mnt/user-data/uploads/socialscope_data/reddit_pulls/histories/insub_posts.zip','/mnt/user-data/uploads/socialscope_data/reddit_pulls/histories/insub_comments.zip',
 '/home/claude/data/augpanel/augpanel_posts.zip','/home/claude/data/augpanel/augpanel_comments.zip','/home/claude/data/septest/septest_posts.zip','/home/claude/data/septest/septest_comments.zip',
 '/home/claude/data/round4/round4_posts.zip','/home/claude/data/round4/round4_comments.zip']
def it(f):
    z=zipfile.ZipFile(f)
    for n in z.namelist():
        for l in z.open(n): yield json.loads(l)
gen=[it(f) for f in srcs]+[ (json.loads(l) for l in open(f)) for f in sorted(glob.glob('/home/claude/work/train/run/full_*.jsonl'))]
for g in gen:
    for r in g:
        a=r.get('author')
        if a not in G: continue
        d={k:r[k] for k in keep if k in r}
        for k in ('body','selftext'):
            if k in d and d[k]: d[k]=d[k][:1500]
        d['author']=a; items[a][r.get('id')]=d
oldest={}
for f in ['/mnt/user-data/uploads/socialscope_data/reddit_pulls/histories/insub_oldest.json','/home/claude/data/augpanel/augpanel_oldest.json','/home/claude/data/septest/septest_oldest.json','/home/claude/data/round4/round4_oldest.json','/mnt/user-data/uploads/socialscope_data/reddit_pulls/histories/train_oldest.json']:
    for k,v in json.load(open(f)).items(): oldest.setdefault(k,v)
json.dump(oldest,open('oldest_all.json','w'))
print('accounts with history:',collections.Counter(G[a][0] for a in items))
pickle.dump((G,{a:list(v.values()) for a,v in items.items()}),open('data.pkl','wb'))

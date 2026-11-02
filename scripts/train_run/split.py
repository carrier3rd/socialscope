import csv, json, zipfile, collections
G={r['username'] if 'username' in r else r[list(r)[0]]:r for r in csv.DictReader(open('/home/claude/work/train/groups.csv'))}
names=sorted(G); chunk={a:i//500 for i,a in enumerate(names)}
K=max(chunk.values())+1
full=[open(f'full_{k}.jsonl','w') for k in range(K)]; cut=[open(f'cut_{k}.jsonl','w') for k in range(K)]
keep=('id','author','author_fullname','created_utc','subreddit','body','title','selftext','score','link_id','parent_id','url','num_comments','is_self','over_18','distinguished')
n=collections.Counter()
for z in ['train_posts.zip','train_comments.zip']:
    zf=zipfile.ZipFile('/mnt/user-data/uploads/socialscope_data/reddit_pulls/histories/'+z)
    for l in zf.open(zf.namelist()[0]):
        r=json.loads(l); a=r.get('author')
        if a not in G: continue
        s=json.dumps({k:r[k] for k in keep if k in r})
        k=chunk[a]; full[k].write(s+'\n'); n['full']+=1
        g=G[a]
        if g['group']=='random' or float(r['created_utc'])<=float(g['listed_utc']):
            cut[k].write(s+'\n'); n['cut']+=1
for f in full+cut: f.close()
for k in range(K):
    with open(f'groups_{k}.csv','w',newline='') as fh:
        w=csv.writer(fh); w.writerow(['username','group','reasons'])
        for a in names:
            if chunk[a]==k: w.writerow([a,G[a]['group']+'_'+G[a]['split'],''])
print(K,'chunks',dict(n))

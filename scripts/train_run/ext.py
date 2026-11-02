import csv, glob, numpy as np, pickle, math
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
H=pickle.load(open('hij2.pkl','rb'))
num=['bot_score','items','comments','subs','longest_gap_days','interval_cv','share_gaps_under_60s','farm_share','self_repeat','ai_style_share','top_sub_share','sub_spread','threads_revisited','top_level_share','words_median','words_cv','quoted_share','ai_vocab_share','md_share','sentence_cv']
def f(x):
    try: return float(x)
    except: return np.nan
def feat(r):
    ls=f(r['last_seen']); return [f(r[c]) for c in num]+[(ls-f(r['first_seen']))/86400,(ls-f(r['first_ever']))/86400 if r['first_ever'] else np.nan, float('primary' in (r['tier'] or '')), math.log1p(f(r['items']) or 0)]
X=[];y=[]
for fn in glob.glob('scores_*/accounts.csv'):
    for r in csv.DictReader(open(fn)):
        v=H.get(r['account'])
        if not v or v['n_cut']==0: continue
        if v['group']=='banned' and v['split']=='train': X.append(feat(r)); y.append(1)
        elif v['group']=='random' and int(r['account'][-1],16)%2==0: X.append(feat(r)); y.append(0)
gb=HistGradientBoostingClassifier(max_iter=300,learning_rate=0.05,max_leaf_nodes=15,l2_regularization=1.0,random_state=0).fit(np.array(X),np.array(y))
for d,pos in [('augpanel_scores0',{'later_bot'}),('augpanel_scores1',{'later_bot'}),('septest_scores_sep15',{'later_bot','known_bot'})]:
    R=list(csv.DictReader(open(f'/home/claude/work/{d}/accounts.csv')))
    Z=np.array([feat(r) for r in R]); lab=np.array([r['group'] in pos for r in R]); ctl=np.array([r['group']=='control' for r in R])
    p=gb.predict_proba(Z)[:,1]; pr=Z[:,-2]
    auc=roc_auc_score(lab[lab|ctl],p[lab|ctl])
    t=np.quantile(p[ctl],0.95); t1=np.quantile(p[ctl],0.99)
    print(f'{d}: bots {lab.sum()} controls {ctl.sum()} | AUC {auc:.2f} | recall at 5% FPR {100*(p[lab]>t).mean():.0f}% | at 1% FPR {100*(p[lab]>t1).mean():.0f}% | primary rule recall {100*pr[lab].mean():.0f}% at FPR {100*pr[ctl].mean():.0f}%')

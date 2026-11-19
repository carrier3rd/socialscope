import pickle, csv, glob, math, numpy as np, collections
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score
F=pickle.load(open('feats.pkl','rb')); S={}
for f in glob.glob('scores_*/accounts.csv'):
    for r in csv.DictReader(open(f)): S[r['account']]=r
def w(k,n,z=1.96):
    if n==0: return 'n=0'
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return f"{100*p:.0f}% ({100*(c-h):.0f}-{100*(c+h):.0f}), {k}/{n}"
for a,v in F.items():
    s=S.get(a); v['primary']=bool(s and 'primary' in (s['tier'] or ''))
grp=lambda g:[v for a,v in F.items() if v['group']==g and v['n_cut']>0 and a in S]
P,C,PE,TP,TC=grp('test_pos'),grp('test_ctl'),grp('test_pending'),grp('train_pos'),grp('train_ctl')
c=lambda L,f: w(sum(bool(f(x)) for x in L),len(L))
PA=[x for x in P if x['aged']]
print('P1 aged share of test positives:',c(P,lambda x:x['aged']),'| pending',c(PE,lambda x:x['aged']),'| controls',c(C,lambda x:x['aged']))
print('P2 solicit_handle: aged pos',c(PA,lambda x:x['sh']),'| all pos',c(P,lambda x:x['sh']),'| controls',c(C,lambda x:x['sh']),'| pending',c(PE,lambda x:x['sh']))
print('P3 solicit_broad: aged pos',c(PA,lambda x:x['sb']),'| all pos',c(P,lambda x:x['sb']),'| controls',c(C,lambda x:x['sb']),'| pending',c(PE,lambda x:x['sb']))
print('P4 primary: pos',c(P,lambda x:x['primary']),'| controls',c(C,lambda x:x['primary']),'| pending',c(PE,lambda x:x['primary']))
print('   primary OR handle: pos',c(P,lambda x:x['primary'] or x['sh']),'| controls',c(C,lambda x:x['primary'] or x['sh']))
num=['bot_score','items','comments','subs','longest_gap_days','interval_cv','share_gaps_under_60s','farm_share','self_repeat','ai_style_share','top_sub_share','sub_spread','threads_revisited','top_level_share','words_median','words_cv','quoted_share','ai_vocab_share','md_share','sentence_cv','state_media_links','political_early','political_late']
pwk=sorted({k for v in F.values() for k in v['pw']})
fl=lambda x: (float(x) if x not in (None,'') else np.nan)
def vec(a,v):
    s=S[a]; return [fl(s[k]) for k in num]+[(v['anchor']-fl(s['first_seen']))/86400, v['age_days'] if v['age_days'] is not None else np.nan, float(v['sh']),float(v['sb']),float(v['primary']),math.log1p(v['n_cut'])]+[fl(v['pw'].get(k)) for k in pwk]
rows=[(a,v['group'],vec(a,v)) for a,v in F.items() if v['n_cut']>0 and a in S]
X=np.array([r[2] for r in rows],dtype=float); g=np.array([r[1] for r in rows])
tr=np.isin(g,['train_pos','train_ctl']); y=(g=='train_pos')|(g=='test_pos')
ok=[j for j in range(X.shape[1]) if len(np.unique(X[tr][:,j][~np.isnan(X[tr][:,j])]))>=2]; X=X[:,ok]
wgt=np.where(y[tr],(~y[tr]).sum()/y[tr].sum(),1.0)
print('train pos',int(y[tr].sum()),'ctl',int((~y[tr]).sum()),'| test pos',int((g=='test_pos').sum()),'ctl',int((g=='test_ctl').sum()))
def rep(name,p):
    pos=p[g=='test_pos']; neg=p[g=='test_ctl']; pen=p[g=='test_pending']
    auc=roc_auc_score(np.r_[np.ones(len(pos)),np.zeros(len(neg))],np.r_[pos,neg]); print(f'{name}: AUC {auc:.3f}')
    for fpr in [0.01,0.02,0.05]:
        t=np.quantile(neg,1-fpr); rec=(pos>t).mean(); fp=(neg>t).mean()
        print(f'   at {int(fpr*100)}% control FPR (actual {100*fp:.1f}%): recall {w(int((pos>t).sum()),len(pos))}, pending flagged {100*(pen>t).mean():.0f}%, precision at 1% bot rate {100*rec*0.01/(rec*0.01+max(fp,1e-9)*0.99):.0f}%')
gb=HistGradientBoostingClassifier(max_iter=300,learning_rate=0.05,max_leaf_nodes=15,l2_regularization=1.0,random_state=0).fit(X[tr],y[tr],sample_weight=wgt)
rep('gradient boosting',gb.predict_proba(X)[:,1])
lr=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=3000,C=0.3,class_weight='balanced')).fit(X[tr],y[tr])
rep('logistic',lr.predict_proba(X)[:,1])

# ablations: drop volume features; and size-matched controls
names=(num+['hist_age','true_age','sh','sb','primary','log_items']+['pw_'+k for k in pwk])
names=[names[j] for j in ok]
from sklearn.inspection import permutation_importance
m=np.isin(g,['test_pos','test_ctl'])
pi=permutation_importance(gb,X[m],y[m],n_repeats=5,random_state=0,scoring='roc_auc')
print('top features:',[(names[i],round(pi.importances_mean[i],3)) for i in np.argsort(-pi.importances_mean)[:8]])
drop=[j for j,n in enumerate(names) if n in ('items','comments','log_items','subs','pw_earlier_items','pw_window_items')]
keepc=[j for j in range(len(names)) if j not in drop]
gb2=HistGradientBoostingClassifier(max_iter=300,learning_rate=0.05,max_leaf_nodes=15,l2_regularization=1.0,random_state=0).fit(X[tr][:,keepc],y[tr],sample_weight=wgt)
rep('GB without volume features',gb2.predict_proba(X[:,keepc])[:,1])
p=gb.predict_proba(X)[:,1]; ni=X[:,names.index('log_items')]
pos=g=='test_pos'; neg=g=='test_ctl'
lo=np.quantile(ni[pos],0.25); hi=np.quantile(ni[pos],0.75)
mm=neg&(ni>=lo)&(ni<=hi); print('controls with item counts in positives IQR:',int(mm.sum()))
t=np.quantile(p[mm],0.99) if mm.sum()>50 else None
if t is not None: print('size-matched: recall of positives in same IQR at 1% matched-control FPR:',w(int((p[pos&(ni>=lo)&(ni<=hi)]>t).sum()),int((pos&(ni>=lo)&(ni<=hi)).sum())))

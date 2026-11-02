import pickle, csv, glob, numpy as np, math
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
H=pickle.load(open('hij2.pkl','rb'))
S={}
for f in glob.glob('scores_*/accounts.csv'):
    for r in csv.DictReader(open(f)): S[r['account']]=r
num=['bot_score','items','comments','subs','longest_gap_days','interval_cv','share_gaps_under_60s','farm_share','self_repeat','ai_style_share','median_reply_minutes','share_replies_under_10min','top_sub_share','sub_spread','threads_revisited','top_level_share','words_median','words_cv','quoted_share','ai_vocab_share','md_share','sentence_cv','state_media_links','political_early','political_late']
pwk=sorted({k for v in H.values() for k in v['pw']})
def f(x):
    try: return float(x)
    except: return np.nan
rows=[]
for a,v in H.items():
    s=S.get(a)
    if not s or v['n_cut']==0: continue
    fs=[f(s[c]) for c in num]
    fs+=[(v['anchor']-f(s['first_seen']))/86400, v['age_days'] if v['age_days'] is not None else np.nan, len((s['flag_list'] or '').split('+')) if s['flag_list'] else 0]
    fs+=[float(v['sh_cut']),float(v['sb_cut']),float(v['primary']),math.log1p(v['n_cut'])]
    fs+=[f(v['pw'].get(k)) for k in pwk]
    half=int(a[-1],16)%2
    rows.append((a,v['group'],v['split'],half,fs))
names=num+['hist_age_days','true_age_days','n_flags','solicit_handle','solicit_broad','primary','log_items']+['pw_'+k for k in pwk]
X=np.array([r[4] for r in rows]); g=np.array([r[1] for r in rows]); sp=np.array([r[2] for r in rows]); hf=np.array([r[3] for r in rows])
tr=((g=='banned')&(sp=='train'))|((g=='random')&(hf==0))|((g=='organic')&(sp=='train'))
te_pos=(g=='banned')&(sp=='test'); te_neg=(g=='random')&(hf==1); te_org=(g=='organic')&(sp=='test')
y=(g=='banned').astype(int)
ok=[j for j in range(X.shape[1]) if len(np.unique(X[tr][:,j][~np.isnan(X[tr][:,j])]))>=2]
print('dropped',[names[j] for j in range(X.shape[1]) if j not in ok]); X=X[:,ok]; names=[names[j] for j in ok]
print('train: banned',int((tr&(g=='banned')).sum()),'neg',int((tr&(g!='banned')).sum()),'| test banned',int(te_pos.sum()),'random',int(te_neg.sum()),'organic',int(te_org.sum()))
def rep(name,p):
    neg=p[te_neg]; pos=p[te_pos]; org=p[te_org]
    from sklearn.metrics import roc_auc_score
    auc=roc_auc_score(np.r_[np.ones(len(pos)),np.zeros(len(neg))],np.r_[pos,neg])
    out=[f'{name}: AUC {auc:.3f}']
    for fpr in [0.01,0.02,0.05]:
        t=np.quantile(neg,1-fpr); rec=(pos>t).mean(); fp=(neg>t).mean(); of=(org>t).mean()
        prec=rec*0.01/(rec*0.01+fp*0.99) if rec+fp>0 else 0
        out.append(f'   at {int(fpr*100)}% random FPR (actual {100*fp:.1f}%): recall {100*rec:.0f}%, organic flagged {100*of:.0f}%, precision at 1% bot rate {100*prec:.0f}%')
    print('\n'.join(out))
gb=HistGradientBoostingClassifier(max_iter=300,learning_rate=0.05,max_leaf_nodes=15,l2_regularization=1.0,random_state=0).fit(X[tr],y[tr])
rep('gradient boosting',gb.predict_proba(X)[:,1])
lr=make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),LogisticRegression(max_iter=2000,C=0.5)).fit(X[tr],y[tr])
rep('logistic',lr.predict_proba(X)[:,1])
# baseline: primary rule alone
pr=X[:,names.index('primary')]; pos=pr[te_pos]; neg=pr[te_neg]; rec=pos.mean(); fp=neg.mean()
print(f'baseline primary rule: recall {100*rec:.0f}%, random FPR {100*fp:.1f}%, precision at 1% {100*rec*0.01/(rec*0.01+fp*0.99):.0f}%')
from sklearn.inspection import permutation_importance
m=te_pos|te_neg
pi=permutation_importance(gb,X[m],y[m],n_repeats=5,random_state=0,scoring='roc_auc')
print('top features:',[(names[i],round(pi.importances_mean[i],3)) for i in np.argsort(-pi.importances_mean)[:10]])

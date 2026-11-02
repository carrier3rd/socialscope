import pickle, csv, glob, math
H=pickle.load(open('hij.pkl','rb'))
S={}
for f in glob.glob('scores_*/accounts.csv'):
    for r in csv.DictReader(open(f)): S[r['account']]=r
for a,v in H.items():
    s=S.get(a); v['primary']=bool(s and 'primary' in (s['tier'] or '')); v['flags']=(s['flag_list'] if s else '')
def w(k,n,z=1.96):
    if n==0: return 'n=0'
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return f"{100*p:.0f}% ({100*(c-h):.0f}-{100*(c+h):.0f}), {k}/{n}"
sel=lambda g,sp=None,f=lambda v:True:[v for v in H.values() if v['group']==g and (sp is None or v['split']==sp) and v['n_full']>0 and f(v)]
for label,sp in [('TEST',['test']),('TRAIN (in-sample check)',['train'])]:
    print('=====',label)
    B=[v for v in H.values() if v['group']=='banned' and v['split'] in sp and v['n_full']>0]
    O=[v for v in H.values() if v['group']=='organic' and v['split'] in sp and v['n_full']>0]
    R=[v for v in H.values() if v['group']=='random' and v['n_full']>0]
    BA=[v for v in B if v['aged']]
    c=lambda L,key: w(sum(bool(x[key]) for x in L),len(L))
    print('P1 aged share of banned:',c(B,'aged'))
    for key in ['sh_full','sh_cut']:
        print(f'P2 {key}: aged banned {c(BA,key)} | all banned {c(B,key)} | random {c(R,key)} | organic {c(O,key)}')
    for key in ['sb_full','sb_cut']:
        print(f'P3 {key}: aged banned {c(BA,key)} | all banned {c(B,key)} | random {c(R,key)} | organic {c(O,key)}')
    print('P4 primary: banned',c(B,'primary'),'| young banned',c([x for x in B if not x['aged']],'primary'),'| random',c(R,'primary'),'| organic',c(O,'primary'))
    for x in B+O+R: x['p_or_sh']=x['primary'] or x['sh_cut']
    print('P5 primary OR sh_cut: banned',c(B,'p_or_sh'),'| random',c(R,'p_or_sh'),'| organic',c(O,'p_or_sh'))
pickle.dump(H,open('hij2.pkl','wb'))

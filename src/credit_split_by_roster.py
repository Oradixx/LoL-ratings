"""L'apport du prior box-score dépend-il du remaniement des rosters ? (notes de la saison N gelées, jugées sur N+1)
Si le prior aide à partager le mérite entre coéquipiers, son apport doit être plus grand quand les rosters ont été
remaniés (la note d'équipe ne suffit plus) que quand ils sont restés intacts."""
import sys, json; sys.path.insert(0,'src')
from engine import *
from roster_change import core_size
from sklearn.metrics import roc_auc_score
V12=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200,home='mix')
P=player_games((2023,2024,2025,2026)); G=game_table(P); out={}
for y in [2024,2025,2026]:
    g0=G[G.year==y-1]; g1=G[G.year==y]
    cs=core_size(P,g0,g1).reindex(g1.index)
    ma=fit(P,g0,V12); mb=fit(P,g0,dict(V12,prior=False))
    xa=pd.Series(np.asarray(predict_games(ma,P,g1,ma['u'][ma['gp']<10].mean())),index=g1.index)
    xb=pd.Series(np.asarray(predict_games(mb,P,g1,mb['u'][mb['gp']<10].mean())),index=g1.index)
    groups={'rosters remaniés (une équipe garde au plus 2 coéquipiers)':cs.min(axis=1)<=2,
            'rosters stables (les deux équipes gardent au moins 4 coéquipiers)':cs.min(axis=1)>=4}
    o={}
    for name,mk in groups.items():
        gi=g1.index[mk.values]; yb=g1.loc[gi].bwin.values; a=xa[gi].values; b=xb[gi].values
        rng=np.random.default_rng(0); d=[]
        for _ in range(1000):
            i=rng.integers(0,len(yb),len(yb)); d.append(roc_auc_score(yb[i],a[i])-roc_auc_score(yb[i],b[i]))
        o[name]=dict(n=int(len(gi)),share=float(mk.mean()),auc_prior=float(roc_auc_score(yb,a)),gain=float(roc_auc_score(yb,a)-roc_auc_score(yb,b)),
                     lo=float(np.percentile(d,2.5)),hi=float(np.percentile(d,97.5)))
    out[str(y)]=o
    for k,v in o.items(): print(y,k,{kk:round(vv,4) for kk,vv in v.items()},flush=True)
json.dump(out,open('data/proc/credit_split_by_roster.json','w'),indent=1,ensure_ascii=False)

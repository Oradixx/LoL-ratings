"""Stabilité: je coupe 2025 en deux moitiés de games au hasard ; les notes se ressemblent-elles ?"""
import sys, json; sys.path.insert(0,'src'); from evaluate import *
tr,_,_=splits('2026'); rng=np.random.default_rng(7)
half=rng.random(len(tr))<0.5; A_,B_=tr[half],tr[~half]
V1=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200)
res={}
def kda_scores(g):
    q=P_ALL[P_ALL.gameid.isin(g.index)]; a=q.groupby('pid').agg(K=('kills','sum'),D=('deaths','sum'),A=('assists','sum'),GP=('gameid','nunique'))
    return (a.K+a.A)/a.D.clip(lower=1), a.GP
ka,ga=kda_scores(A_); kb,gb=kda_scores(B_)
ok=ga[ga>=30].index.intersection(gb[gb>=30].index)
res['KDA']=np.corrcoef(ka[ok],kb[ok])[0,1]
ma=fit(P_ALL,A_,V1); mb=fit(P_ALL,B_,V1)
res['v1 theta']=np.corrcoef(ma['theta'][ok],mb['theta'][ok])[0,1]
res['v1 u (intra-ligue)']=np.corrcoef(ma['u'][ok],mb['u'][ok])[0,1]
m0a=fit(P_ALL,A_,dict(V1,prior=False)); m0b=fit(P_ALL,B_,dict(V1,prior=False))
res['RAPM sans prior theta']=np.corrcoef(m0a['theta'][ok],m0b['theta'][ok])[0,1]
res['n']=len(ok)
print(res); json.dump(res,open('data/proc/reliability.json','w'),indent=1)

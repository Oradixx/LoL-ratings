"""Rattachement du joueur à une ligue : la plus jouée, la plus récente, ou un mélange pondéré par la récence ?
Jugé sur la saison 2026 (ré-entraînement mensuel, calibration sur le mois précédent)."""
import sys, json; sys.path.insert(0,'src')
import rolling as RO, numpy as np
from evaluate import *
V1=RO.V1; out={}
for name,cfg in [('most',V1),('recent',dict(V1,home='recent')),('mix 180 j',dict(V1,home='mix')),('mix 90 j',dict(V1,home='mix',home_half_life=90)),('mix 365 j',dict(V1,home='mix',home_half_life=365))]:
    ys=[];xs=[];ps=[];prevx=None
    for i,m in enumerate(RO.MONTHS):
        mg=RO.month_games(m); mm=fit(P_ALL,G_ALL[G_ALL.date<m],cfg)
        x=predict_games(mm,P_ALL,mg,mm['u'][mm['gp']<10].mean())
        if i>0:
            lr=LogisticRegression(C=1e6).fit(prevx.values.reshape(-1,1),RO.month_games(RO.MONTHS[i-1]).bwin.values)
            ps.append(lr.predict_proba(x.values.reshape(-1,1))[:,1]); ys.append(mg.bwin.values); xs.append(x.values)
        prevx=x
    y=np.concatenate(ys);p=np.concatenate(ps);x=np.concatenate(xs); lo,hi=auc_ci(y,x)
    out[name]=dict(auc=roc_auc_score(y,x),lo=lo,hi=hi,acc=float(((p>.5)==y).mean()),ll=log_loss(y,p))
    print(name,{k:round(v,4) for k,v in out[name].items()},flush=True)
json.dump(out,open('data/proc/home_test.json','w'),indent=1)

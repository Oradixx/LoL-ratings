"""Combien d'historique donner au modèle de prédiction ? (v1.5, avec les fichiers 2023 et 2024)
Rejeu mois par mois : à chaque 1er du mois, le modèle v1.2 est entraîné sur les N dernières saisons (saison en cours incluse)
et prédit le mois. Critère fixé d'avance : log-loss des probabilités calibrées (mois précédent). Choisi sur 2025, confirmé sur 2026."""
import sys, json, time; sys.path.insert(0,'src')
from engine import *
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss
V12=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200,home='mix')
P=player_games((2023,2024,2025,2026)); G=game_table(P)
def mg(m): e=m+pd.offsets.MonthBegin(1); return G[(G.date>=m)&(G.date<e)]
out={}; t0=time.time(); PRED={}
for year,Ns,last in [(2025,[2,3],'2025-12-01'),(2026,[2,3,4],'2026-09-01')]:
    MONTHS=pd.date_range(f'{year}-01-01',last,freq='MS'); out[str(year)]={}
    for N in Ns:
        d={}
        for m in MONTHS:
            tr=G[(G.date<m)&(G.year>year-N)]; gm=mg(m); mm=fit(P,tr,V12)
            d[m]=pd.Series(np.asarray(predict_games(mm,P,gm,mm['u'][mm['gp']<10].mean())),index=gm.index)
        ys=[];ps=[];xs=[];mon={}
        for i,m in enumerate(MONTHS[1:],1):
            prev=MONTHS[i-1]; lr=LogisticRegression(C=1e6).fit(d[prev].values.reshape(-1,1),mg(prev).bwin.values)
            p=lr.predict_proba(d[m].values.reshape(-1,1))[:,1]; y=mg(m).bwin.values; ys.append(y); ps.append(p); xs.append(d[m].values)
            mon[str(m.date())[:7]]=float(log_loss(y,p))
        y=np.concatenate(ys); p=np.concatenate(ps); x=np.concatenate(xs); PRED[(year,N)]=(y,p,x)
        out[str(year)][f'{N} saisons']=dict(logloss=float(log_loss(y,p)),auc=float(roc_auc_score(y,x)),acc=float(((p>0.5)==y).mean()),n=int(len(y)),monthly_logloss=mon)
        print(year,N,'saisons',{k:round(v,4) for k,v in out[str(year)][f'{N} saisons'].items() if k!='monthly_logloss'},round(time.time()-t0),'s',flush=True)
# écart apparié (bootstrap sur les games) : N saisons contre la référence
rng=np.random.default_rng(0)
for year,a,b in [(2025,3,2),(2026,3,2),(2026,4,3)]:
    y,pa,xa=PRED[(year,a)]; _,pb,xb=PRED[(year,b)]; dA=[];dL=[]
    for _ in range(1000):
        i=rng.integers(0,len(y),len(y))
        dA.append(roc_auc_score(y[i],xa[i])-roc_auc_score(y[i],xb[i])); dL.append(log_loss(y[i],pa[i])-log_loss(y[i],pb[i]))
    out[str(year)][f'{a} vs {b}']=dict(auc_gain=float(roc_auc_score(y,xa)-roc_auc_score(y,xb)),auc_lo=float(np.percentile(dA,2.5)),auc_hi=float(np.percentile(dA,97.5)),
        logloss_gain=float(log_loss(y,pa)-log_loss(y,pb)),ll_lo=float(np.percentile(dL,2.5)),ll_hi=float(np.percentile(dL,97.5)))
    print(year,f'{a} vs {b}',{k:round(v,4) for k,v in out[str(year)][f'{a} vs {b}'].items()},flush=True)
json.dump(out,open('data/proc/history_length.json','w'),indent=1,ensure_ascii=False)

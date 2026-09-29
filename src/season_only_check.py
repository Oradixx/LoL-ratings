"""Question de la v1.3 : une note calculée sur la seule saison en cours prédit-elle aussi bien que
le modèle qui voit tout l'historique ? Même protocole que rolling.py (ré-entraînement chaque mois,
calibration sur le mois précédent), mais le modèle ne voit que les games de 2026 déjà jouées,
avec le niveau des ligues 2025 comme point de départ."""
import sys, json, time, pickle; sys.path.insert(0,'src')
from rolling import *
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss
V12=dict(V1,home='mix')
lv=json.load(open('data/proc/season_2025.json'))['league']
cfg=dict(V12,league_prior={k:v/1000 for k,v in lv.items()},league_prior_w=100.0)
preds=pickle.load(open('data/proc/rolling_preds.pkl','rb'))
t0=time.time(); d={}
for m in MONTHS:
    mg=month_games(m); tr=G_ALL[(G_ALL.date<m)&(G_ALL.year==2026)]
    if len(tr)<200: d[m]=pd.Series(0.0,index=mg.index); continue
    mm=fit(P_ALL,tr,cfg); d[m]=predict_games(mm,P_ALL,mg,mm['u'][mm['gp']<10].mean())
    print(m.date(),len(tr),round(time.time()-t0),'s',flush=True)
preds['v1.3 saison seule']=d
out={}
for name in ['v1.2 rattachement mixte','v1.3 saison seule','Elo équipe (mis à jour à chaque game)']:
    dd=preds[name]; ys=[];ps=[];xs=[];mon={}
    for i,m in enumerate(MONTHS[1:],1):
        prev=MONTHS[i-1]; gp_=month_games(prev); gm=month_games(m)
        lr=LogisticRegression(C=1e6).fit(dd[prev].values.reshape(-1,1),gp_.bwin.values)
        p=lr.predict_proba(dd[m].values.reshape(-1,1))[:,1]
        ys.append(gm.bwin.values); ps.append(p); xs.append(dd[m].values)
        mon[str(m.date())[:7]]=roc_auc_score(gm.bwin,dd[m].values)
    y=np.concatenate(ys); p=np.concatenate(ps); x=np.concatenate(xs); lo,hi=auc_ci(y,x)
    out[name]=dict(auc=roc_auc_score(y,x),lo=lo,hi=hi,acc=float(((p>0.5)==y).mean()),n=int(len(y)),monthly=mon)
    print(f"{name:40s} AUC {out[name]['auc']:.3f} [{lo:.3f}-{hi:.3f}] acc {out[name]['acc']:.3f}", {k:round(v,3) for k,v in mon.items()})
json.dump(out,open('data/proc/season_only_check.json','w'),indent=1,ensure_ascii=False)

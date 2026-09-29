"""Force de l'a priori « niveau des ligues de la saison précédente » dans les notes de saison 2026.
Deux épreuves indépendantes : (1) games de 2026 coupées au hasard en deux moitiés (appris sur A, jugé sur B) ;
(2) le rejeu de la saison mois par mois (seule la saison en cours est vue), là où l'a priori compte le plus."""
import sys, json; sys.path.insert(0,'src')
from seasons import *
from sklearn.metrics import roc_auc_score
lv=json.load(open('data/proc/season_2025.json'))['league']; L26={k:v/1000 for k,v in lv.items()}
WS=[None,10,30,100,300]
g=G_ALL[G_ALL.year==2026]; out={'halves':{},'rolling':{}}
for w in WS:
    aucs=[]
    for rep in range(3):
        rng=np.random.default_rng(100+rep); isB=rng.random(len(g))<0.5
        c=dict(V,league_prior=L26,league_prior_w=w); m=fit(P_ALL,g[~isB],c)
        pr=np.asarray(predict_games(m,P_ALL,g[isB],m['u'][m['gp']<10].mean())); aucs.append(roc_auc_score(g[isB].bwin,pr))
    out['halves'][str(w)]=float(np.mean(aucs))
    print('moitiés',w,round(np.mean(aucs),4),flush=True)
MONTHS=pd.date_range('2026-02-01','2026-09-01',freq='MS')
for w in WS:
    ys=[];xs=[];mon={}
    for mth in MONTHS:
        e=mth+pd.offsets.MonthBegin(1); mg=g[(g.date>=mth)&(g.date<e)]; tr=g[g.date<mth]
        m=fit(P_ALL,tr,dict(V,league_prior=L26,league_prior_w=w)); x=np.asarray(predict_games(m,P_ALL,mg,m['u'][m['gp']<10].mean()))
        ys.append(mg.bwin.values); xs.append(x); mon[str(mth.date())[:7]]=roc_auc_score(mg.bwin,x)
    out['rolling'][str(w)]=dict(auc=float(roc_auc_score(np.concatenate(ys),np.concatenate(xs))),monthly=mon)
    print('rejeu',w,round(out['rolling'][str(w)]['auc'],4),{k:round(v,3) for k,v in mon.items()},flush=True)
json.dump(out,open('data/proc/league_prior_check.json','w'),indent=1)

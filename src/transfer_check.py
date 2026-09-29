"""Le partage du mérite entre coéquipiers, jugé sur les transferts.
Prédire le résultat d'un match ne dit pas comment répartir le mérite entre cinq joueurs qui jouent toujours ensemble.
Un transfert, si : quand les joueurs changent d'équipe, seule une bonne répartition prédit la force des nouvelles équipes.
Protocole : notes apprises sur la seule saison 2025 (gelées), jugées sur les games 2026 où au moins une équipe aligne
au moins deux joueurs qui ont changé d'équipe depuis 2025. Réglages choisis sur janvier-mars 2026, confirmés sur avril-septembre."""
import sys, json; sys.path.insert(0,'src')
from evaluate import *
from sklearn.metrics import roc_auc_score
from engine import BOX_BASE
g25=G_ALL[G_ALL.year==2025]; g26=G_ALL[G_ALL.year==2026]
p25=P_ALL[P_ALL.gameid.isin(g25.index)&(P_ALL.pid!='anon')]
team25=p25.assign(t=p25.teamid.fillna(p25.teamname)).groupby('pid').t.agg(lambda s:s.mode().iloc[0])
q=P_ALL[P_ALL.gameid.isin(g26.index)&(P_ALL.pid!='anon')].copy(); q['t']=q.teamid.fillna(q.teamname)
q['moved']=q.pid.isin(team25.index)&(q.pid.map(team25)!=q.t)
mv=q.groupby(['gameid','side']).moved.sum().unstack()
resh=mv.index[(mv.max(axis=1)>=2)]
gR=g26.loc[g26.index.intersection(resh)]
win1=gR[gR.date<'2026-04-01']; win2=gR[gR.date>='2026-04-01']
print('games avec >= 2 joueurs transférés dans une équipe :',len(win1),'(janv-mars)',len(win2),'(avr-sept)')
BASE=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200,home='mix')
VARS={'publié (prior ×1, λ=50)':BASE,
      'sans prior box-score':dict(BASE,prior=False),
      'prior ×0,5':dict(BASE,prior_scale=0.5),'prior ×1,5':dict(BASE,prior_scale=1.5),'prior ×2':dict(BASE,prior_scale=2.0),
      'λ=25':dict(BASE,lam=25),'λ=100':dict(BASE,lam=100),
      'sans stats de lane':dict(BASE,lane=False),
      'prior moins régularisé (alpha 50)':dict(BASE,prior_alpha=50),'prior plus régularisé (alpha 800)':dict(BASE,prior_alpha=800)}
out={}
for name,cfg in VARS.items():
    m=fit(P_ALL,g25,cfg); unk=m['u'][m['gp']<10].mean(); r={}
    for wn,gw in [('janv-mars',win1),('avr-sept',win2)]:
        x=np.asarray(predict_games(m,P_ALL,gw,unk))+m['side']; y=np.asarray(target(gw,'gold'))
        r[wn]=dict(auc=float(roc_auc_score(gw.bwin,x)),corr_gold=float(np.corrcoef(x,y)[0,1]),n=len(gw))
    out[name]=r
    print(f"{name:36s}", ' | '.join(f"{w}: AUC {v['auc']:.4f} corr {v['corr_gold']:.4f}" for w,v in r.items()),flush=True)
json.dump(out,open('data/proc/transfer_check.json','w'),indent=1,ensure_ascii=False)
# intervalle de confiance (bootstrap apparié) de l'apport du prior box-score, sur toutes les games « transferts »
ma=fit(P_ALL,g25,BASE); mb=fit(P_ALL,g25,dict(BASE,prior=False))
xa=np.asarray(predict_games(ma,P_ALL,gR,ma['u'][ma['gp']<10].mean())); xb=np.asarray(predict_games(mb,P_ALL,gR,mb['u'][mb['gp']<10].mean()))
yb=gR.bwin.values; rng=np.random.default_rng(0); d=[]
for _ in range(1000):
    i=rng.integers(0,len(yb),len(yb)); d.append(roc_auc_score(yb[i],xa[i])-roc_auc_score(yb[i],xb[i]))
out['_prior_gain']=dict(auc_gain=float(roc_auc_score(yb,xa)-roc_auc_score(yb,xb)),lo=float(np.percentile(d,2.5)),hi=float(np.percentile(d,97.5)),n=len(yb))
print('apport du prior box-score (AUC) :',{k:round(v,4) for k,v in out['_prior_gain'].items()})
json.dump(out,open('data/proc/transfer_check.json','w'),indent=1,ensure_ascii=False)

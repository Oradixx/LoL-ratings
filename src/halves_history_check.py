"""Pour décrire 2026 (games de 2026 jamais vues, tirées au hasard), l'historique 2025 aide-t-il ?
Saison seule (v1.3, a priori ligues 2025) contre modèle deux saisons (v1.2), mêmes moitiés A/B."""
import sys, json; sys.path.insert(0,'src')
from seasons import *
from sklearn.metrics import roc_auc_score
lv=json.load(open('data/proc/season_2025.json'))['league']; L26={k:v/1000 for k,v in lv.items()}
g=G_ALL[G_ALL.year==2026]; g25=G_ALL[G_ALL.year==2025]; out={'saison seule':[],'deux saisons':[]}
for rep in range(3):
    isB=np.random.default_rng(100+rep).random(len(g))<0.5
    for name,tr,c in [('saison seule',g[~isB],dict(V,league_prior=L26,league_prior_w=LEAGUE_PRIOR_W)),('deux saisons',pd.concat([g25,g[~isB]]),dict(V))]:
        m=fit(P_ALL,tr,c); out[name].append(roc_auc_score(g[isB].bwin,np.asarray(predict_games(m,P_ALL,g[isB],m['u'][m['gp']<10].mean()))))
print({k:round(float(np.mean(v)),4) for k,v in out.items()})
json.dump({k:float(np.mean(v)) for k,v in out.items()},open('data/proc/halves_history_check.json','w'))

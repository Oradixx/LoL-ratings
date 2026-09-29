"""Exofeng, saison 2026 : combien pèsent ses games de début d'année (Prime League, CCWS) dans sa note de saison ?
Même modèle de saison, avec et sans ces games."""
import sys, json; sys.path.insert(0,'src')
from seasons import *
lv=json.load(open('data/proc/season_2025.json'))['league']; L26={k:v/1000 for k,v in lv.items()}
g=G_ALL[G_ALL.year==2026]; c=dict(V,league_prior=L26,league_prior_w=LEAGUE_PRIOR_W)
exo=P_ALL[(P_ALL.playername=='Exofeng')&(P_ALL.src_year==2026)]; pid=exo.pid.iloc[0]
early=exo[~exo.teamname.eq('Skillcamp')].gameid.unique()
act=pd.read_parquet('data/proc/season_2026.parquet').query('active').index; out={}
for name,gg in [('all',g),('skillcamp_only',g.drop(early,errors='ignore'))]:
    m=fit(P_ALL,gg,c); th=m['theta']; out[name]=float((th[pid]-th.reindex(act).mean())*1000)
out['n_early']=int(len(early)); out['wr_early']=float(exo[exo.gameid.isin(early)].result.mean())
print(out); json.dump(out,open('data/proc/exofeng_season_check.json','w'))

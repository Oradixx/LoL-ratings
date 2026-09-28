"""Le joueur le plus sous-coté: meilleur theta hors ligues majeures, robuste dans le multivers."""
import sys, json, pickle; sys.path.insert(0,'src')
import pandas as pd, numpy as np
from engine import player_games
mv=pickle.load(open('data/proc/multiverse.pkl','rb'))
r1=pd.read_parquet('data/proc/ratings_v1.parquet')
P=pd.read_parquet('data/proc/players.parquet'); p26=P[P.src_year==2026]
p26=p26.assign(pid=p26.playerid.fillna('name:'+p26.playername.astype(str)))
MAJ25={'LCK','LPL','LEC','LTA N','LTA S','LTA','LCP'}; MAJ26={'LCK','LPL','LEC','LCS','CBLOL','LCP'}
minor=r1[(~r1.home.isin(MAJ25))&(r1.home!='INTL_ONLY')].index
rows=[]
for r in mv:
    th=r['theta']; gp=r['gp']; ok=gp[gp>=max(20,r['cfg']['min_gp'])].index.intersection(minor)
    t=th.reindex(ok).rank(ascending=False)
    rows.append(t)
R=pd.DataFrame(rows)
s=pd.DataFrame({'p1':(R==1).mean(),'p10':(R<=10).mean(),'med':R.median()}).join(r1[['name','team','home','role','gp']])
s['gold_v1']=r1.theta.reindex(s.index)*5000
where26=p26.groupby('pid').agg(lg=('league',lambda x:','.join(sorted(set(x)))),team26=('teamname','last'))
s=s.join(where26)
s=s.sort_values(['p10','p1'],ascending=False).head(15)
print(s.round(3).to_string())
json.dump(s.round(3).reset_index().to_dict('records'),open('data/proc/underrated.json','w'),indent=1,default=str,ensure_ascii=False)
# how many different lineups did top candidates play with (identifiability)
p=player_games((2025,))
for pid in s.index[:6]:
    g=p[p.pid==pid].gameid.unique()
    mates=p[p.gameid.isin(g)&(p.teamname.isin(p[p.pid==pid].teamname.unique()))&(p.pid!=pid)]
    print(s.loc[pid,'name'],'distinct teammates:',mates.pid.nunique(),'teams:',p[p.pid==pid].teamname.unique()[:4])

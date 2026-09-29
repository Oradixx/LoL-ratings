"""Le joueur le plus sous-coté aujourd'hui : meilleure note hors ligues majeures en 2026,
robuste dans le multivers, et combien de coéquipiers différents (= a-t-on pu le séparer de son équipe ?)."""
import sys, json, pickle; sys.path.insert(0,'src')
import pandas as pd, numpy as np
mv=pickle.load(open('data/proc/multiverse.pkl','rb'))
r=pd.read_parquet('data/proc/ratings_now.parquet'); r=r[r.active&(r.tier=='Académie / ligue régionale')]
rows=[]
for u in mv:
    ok=u['gp'][u['gp']>=max(20,u['cfg']['min_gp'])].index.intersection(r.index)
    rows.append(u['theta'].reindex(ok).rank(ascending=False))
R=pd.DataFrame(rows)
s=pd.DataFrame({'p1':(R==1).mean(),'p10':(R<=10).mean(),'med':R.median()}).join(r[['player','team','league26','role','gp26','points','points_sd']])
P=pd.read_parquet('data/proc/players.parquet'); P=P[P.src_year.isin([2025,2026])]
P=P.assign(pid=P.playerid.fillna('name:'+P.playername.astype(str)))
def mates(pid):
    g=P[P.pid==pid][['gameid','side']]
    return P.merge(g,on=['gameid','side']).query('pid!=@pid').pid.nunique()
s=s.sort_values(['p10','p1'],ascending=False).head(12)
s['teammates']=[mates(i) for i in s.index]
print(s.round(3).to_string())
json.dump(s.round(3).reset_index().rename(columns={'index':'pid'}).to_dict('records'),open('data/proc/underrated.json','w'),indent=1,default=str,ensure_ascii=False)

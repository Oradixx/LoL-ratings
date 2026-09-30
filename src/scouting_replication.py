"""v1.5 — Le scouting, répliqué : les joueurs les mieux notés hors ligues majeures une saison jouent-ils en ligue
majeure la saison suivante ? Même protocole que src/scouting.py (2025 -> 2026), avec les notes d'une seule saison
(src/seasons.py) de 2023 et 2024. Ligues majeures de chaque année : leagues.majors(année)."""
import sys, json; sys.path.insert(0,'src')
import pandas as pd, numpy as np
from sklearn.metrics import roc_auc_score
from leagues import majors
P=pd.read_parquet('data/proc/players.parquet'); P['pid']=P.playerid.fillna('name:'+P.playername.astype(str))
out={}
for y in [2023,2024,2025]:
    r=pd.read_parquet(f'data/proc/season_{y}.parquet')
    cand=r[r.active&~r.league.isin(majors(y))].copy()
    nxt=P[P.src_year==y+1].groupby('pid').league.agg(set)
    cand['promoted']=cand.index.map(lambda i: len(nxt.get(i,set())&majors(y+1))>0)
    q=P[(P.src_year==y)&P.pid.isin(cand.index)].groupby('pid').agg(K=('kills','sum'),D=('deaths','sum'),A=('assists','sum'),W=('result','mean'))
    cand=cand.join(((q.K+q.A)/q.D.clip(lower=1)).rename('KDA')).join(q.W)
    top=cand.sort_values('points',ascending=False).head(20)
    o=dict(n=int(len(cand)),n_prom=int(cand.promoted.sum()),base=float(cand.promoted.mean()),top20_rate=float(top.promoted.mean()),
           auc_rating=float(roc_auc_score(cand.promoted,cand.points)),auc_kda=float(roc_auc_score(cand.promoted,cand.KDA.fillna(cand.KDA.median()))),
           auc_winrate=float(roc_auc_score(cand.promoted,cand.W.fillna(0.5))))
    out[str(y)]=o; print(y,'->',y+1,{k:round(v,3) for k,v in o.items()})
json.dump(out,open('data/proc/scouting_replication.json','w'),indent=1)

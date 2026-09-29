"""Exporte les résultats (CSV) utilisés par la page et par explore.py."""
import sys, json; sys.path.insert(0,'src')
import pandas as pd, numpy as np
from leagues import tier
a=pd.read_parquet('data/proc/agg_v0.parquet')
cols=['name','team','league','role','GP','W']
a.sort_values('KDA',ascending=False)[cols+['KDA']].head(50).round(3).to_csv('results/phases/v0.1_kda.csv')
a.sort_values('v02',ascending=False)[cols+['v02']].head(50).round(3).to_csv('results/phases/v0.2_lolratings2_worldwide.csv')
a.sort_values('v03',ascending=False)[cols+['v03']].head(50).round(3).to_csv('results/phases/v0.3_role_zscore.csv')
# notes actuelles (2026)
r=pd.read_parquet('data/proc/ratings_now.parquet').join(pd.read_parquet('data/proc/mv_stats.parquet'))
out=r[r.active][['player','team','league26','tier','role','gp26','gp_total','points','points_sd','u_gold','mv_median_rank','mv_p1','mv_top5']]
out=out.rename(columns={'league26':'league','gp26':'games_2026','gp_total':'games_2025_2026','u_gold':'vs_role_in_league_gold'})
out.sort_values('points',ascending=False).round(3).to_csv('results/ratings_2026.csv')
# notes 2025 (le labo)
v=pd.read_parquet('data/proc/ratings_v1.parquet')
base=v[v.gp>=20].theta.mean()
v['points']=((v.theta-base)*1000).round(0); v['tier']=v.home.map(tier); v['u_gold']=(v.u*5000).round(0)
v[['name','team','home','tier','role','gp','points','u_gold']].rename(columns={'name':'player','home':'league','gp':'games_2025','u_gold':'vs_role_in_league_gold'}).sort_values('points',ascending=False).to_csv('results/ratings_2025.csv')
print(out.shape, out.groupby('tier').size().to_dict())

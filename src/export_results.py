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
from leagues import REGION
r['region']=r.league26.map(REGION)
out=r[r.active][['player','team','league26','region','tier','role','gp26','gp_total','points','points_sd','vs_role_league_gold','mv_median_rank','mv_p1','mv_top5']]
out=out.rename(columns={'league26':'league','gp26':'games_2026','gp_total':'games_2025_2026','vs_role_league_gold':'vs_role_in_league_gold'})
out.sort_values('points',ascending=False).round(3).to_csv('results/ratings_now_2025-2026.csv')   # modèle de prédiction (tout l'historique)
# notes 2025 (le labo)
v=pd.read_parquet('data/proc/ratings_v1.parquet')
base=v[v.gp>=20].theta.mean()
v['points']=((v.theta-base)*1000).round(0); v['tier']=v.home.map(tier); v['u_gold']=(v.u*5000).round(0)
# (les notes v1.0 de 2025 restent dans results/phases/ via v01_v03 ; les notes publiées sont désormais par saison, ci-dessous)
print(out.shape, out.groupby('tier').size().to_dict())

# notes d'une seule saison (v1.3) et notes par compétition / split
import os
for y in [2023,2024,2025,2026]:
    s=pd.read_parquet(f'data/proc/season_{y}.parquet')
    if os.path.exists(f'data/proc/season_{y}_mv.parquet'): s=s.join(pd.read_parquet(f'data/proc/season_{y}_mv.parquet'))
    s=s[(s.gp>=10)&s.league.notna()]
    Sj=json.load(open(f'data/proc/season_{y}.json'))
    s['also_in']=pd.Series({pid:' ; '.join(f'{a[0]} {a[1]} games ({a[2]})' for a in v) for pid,v in Sj.get('also',{}).items()}).reindex(s.index)
    cols=['player','team','league','also_in','region','tier','role','gp','points','points_sd','vs_role_league_gold']+[c for c in ['mv_median_rank','mv_p1','mv_top5'] if c in s]
    s[cols].rename(columns={'gp':f'games_{y}','vs_role_league_gold':'vs_role_in_league_gold'}).sort_values('points',ascending=False).round(3).to_csv(f'results/ratings_{y}.csv')
    S=json.load(open(f'data/proc/season_{y}.json')); d=pd.DataFrame(S['deltas'])
    d=d[d.pid.isin(s.index)]
    from leagues import comp_labels; lab={k:v['label'] for k,v in comp_labels(S['comps'],set(s.league.unique())).items()}
    c=pd.DataFrame(dict(player=d.pid.map(s.player),team=d.pid.map(s.team),league=d.pid.map(s.league),role=d.pid.map(s.role),competition=d.comp.map(lab).fillna(d.comp),
        games=d.gp,win_rate=d.win.round(3),kda=d.kda.round(2),season_points=d.pid.map(s.points),delta=(d.d*1000).round(0),delta_sd=(d.dsd*1000).round(0)))
    c['competition_points']=c.season_points+c.delta
    c.sort_values(['competition','competition_points'],ascending=[True,False]).to_csv(f'results/competitions_{y}.csv',index=False)
    print(y,len(s),'joueurs',len(c),'lignes compétition')

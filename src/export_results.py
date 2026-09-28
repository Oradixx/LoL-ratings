"""Exporte les résultats (CSV) utilisés par la page et par explore.py."""
import sys, json, pickle; sys.path.insert(0,'src')
import pandas as pd, numpy as np
a=pd.read_parquet('data/proc/agg_v0.parquet')
cols=['name','team','league','role','GP','W']
a.sort_values('KDA',ascending=False)[cols+['KDA']].head(50).round(3).to_csv('results/phases/v0.1_kda.csv')
a.sort_values('v02',ascending=False)[cols+['v02']].head(50).round(3).to_csv('results/phases/v0.2_lolratings2_worldwide.csv')
a.sort_values('v03',ascending=False)[cols+['v03']].head(50).round(3).to_csv('results/phases/v0.3_role_zscore.csv')
r=pd.read_parquet('data/proc/ratings_v1_unc.parquet')
mv=pickle.load(open('data/proc/multiverse.pkl','rb'))
# multivers: rang médian et % top-5 par joueur dans son rôle
info=r[['role']]
ranks=[]
for u in mv:
    gp=u['gp']; ok=gp[gp>=u['cfg']['min_gp']].index
    t=pd.DataFrame({'theta':u['theta'].reindex(ok)}).join(info)
    ranks.append(t.groupby('role').theta.rank(ascending=False).rename(u['seed']))
R=pd.concat(ranks,axis=1)
r['mv_median_rank']=R.median(1); r['mv_p1']=(R==1).mean(1); r['mv_top5']=(R<=5).mean(1); r['mv_present']=R.notna().mean(1)
out=r[['name','team','home','role','gp','gold','gold_sd','u','theta','mv_median_rank','mv_p1','mv_top5','mv_present']].copy()
out['u_gold']=out.pop('u')*5000
out=out.rename(columns={'home':'home_league','gold':'rating_gold','gold_sd':'rating_sd_gold'})
out['theta']=out.theta.round(5)
out.sort_values('rating_gold',ascending=False).round(3).to_csv('results/ratings_2025_v1.csv')
print(out.shape); print(out.sort_values('rating_gold',ascending=False).head(3))

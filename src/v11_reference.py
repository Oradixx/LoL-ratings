"""Référence pour le patch 1.2 (le cas Exofeng) : notes actuelles avec l'ancien rattachement v1.1
(chaque joueur rattaché à la ligue où il a le plus joué sur deux ans), sur les mêmes games que src/current.py.
Sortie : data/proc/ratings_now_v11.parquet (points sur la même échelle : 0 = joueur moyen actif en 2026)."""
import sys; sys.path.insert(0,'src'); from evaluate import *
V11=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200)
tr,_,_=splits('now')
m=fit(P_ALL,tr,V11)
now=pd.read_parquet('data/proc/ratings_now.parquet')          # joueurs actifs 2026, définis par src/current.py
r=pd.DataFrame({'theta':m['theta']}).join(now[['player','team','role','league26','active']],how='inner')
base=r[r.active].theta.mean(); r['points']=((r.theta-base)*1000).round(0)
r.to_parquet('data/proc/ratings_now_v11.parquet')
print(r[r.player=='Exofeng'][['team','points']])

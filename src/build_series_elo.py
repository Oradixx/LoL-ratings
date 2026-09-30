import pandas as pd, numpy as np, sys
sys.path.insert(0,'src'); from elo import *
T=pd.read_parquet('data/proc/teams.parquet'); T=T[T.src_year.isin([2022,2025,2026])]   # années des analyses bonus publiées
g=team_games(T)
# separate Elo run with side advantage estimated
bwr=g.bwin.mean(); print('blue winrate',round(bwr,3))
g,R=run_elo(g,K=24,side_adv=400*np.log10(bwr/(1-bwr)))
g['day']=g.date.dt.date
g['pair']=g.apply(lambda r:'|'.join(sorted([str(r.blue_k),str(r.red_k)])),axis=1)
g=g.sort_values(['pair','day','date'])
g['series']=g.groupby(['pair','day']).ngroup()
g['gnum']=g.groupby('series').cumcount()+1
g['slen']=g.groupby('series').gameid.transform('size')
out=[]
for s,d in g.groupby('series'):
    if len(d)<2: continue
    d=d.reset_index(drop=True)
    wins={}
    for i in range(1,len(d)):
        prev=d.loc[i-1]; cur=d.loc[i]
        prev_loser=prev.red_k if prev.bwin==1 else prev.blue_k
        # perspective: previous game loser
        lb= cur.blue_k==prev_loser
        p=cur.p_elo if lb else 1-cur.p_elo
        w=cur.bwin if lb else 1-cur.bwin
        out.append(dict(series=s,gnum=cur.gnum,year=cur.src_year,loser_blue=lb,p=p,w=w,elo_diff=(cur.elo_b-cur.elo_r)*(1 if lb else -1)))
o=pd.DataFrame(out)
print(len(o),'games after a game in same series')
print(o.groupby('year').agg(n=('w','size'),win=('w','mean'),exp=('p','mean'),loser_takes_blue=('loser_blue','mean')).round(3))
print(o.groupby(['year','loser_blue']).agg(n=('w','size'),win=('w','mean'),exp=('p','mean')).round(3))
o.to_parquet('data/proc/tilt.parquet'); g.to_parquet('data/proc/games_elo.parquet')

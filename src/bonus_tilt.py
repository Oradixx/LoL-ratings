import pandas as pd, numpy as np, json
g=pd.read_parquet('data/proc/games_elo.parquet').sort_values('date')
g=g[g.src_year.isin([2022,2025])]
rows=[]
for pair,d in g.groupby('pair'):
    d=d.sort_values('date').reset_index(drop=True)
    for i in range(1,len(d)):
        prev,cur=d.loc[i-1],d.loc[i]
        same=(cur.series==prev.series)
        loser=prev.red_k if prev.bwin==1 else prev.blue_k
        lb=cur.blue_k==loser
        p=cur.p_elo if lb else 1-cur.p_elo; w=cur.bwin if lb else 1-cur.bwin
        gap=(cur.date-prev.date).days
        rows.append(dict(same=same,gap=gap,p=p,w=w,year=cur.src_year))
o=pd.DataFrame(rows)
o['kind']=np.where(o.same,'même série (quelques minutes après)',np.where(o.gap<=60,'prochaine rencontre (<60 j)','prochaine rencontre (>60 j)'))
t=o.groupby('kind').agg(n=('w','size'),win=('w','mean'),exp=('p','mean'))
t['ecart_pts']=(t.win-t.exp)*100
t['se_pts']=np.sqrt(t.win*(1-t.win)/t.n)*100
print(t.round(3))
json.dump(t.round(4).reset_index().to_dict('records'),open('data/proc/bonus_tilt.json','w'),indent=1,ensure_ascii=False)

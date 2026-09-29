import pandas as pd, numpy as np
P=pd.read_parquet('data/proc/players.parquet'); T=pd.read_parquet('data/proc/teams.parquet')
# toutes les années disponibles (2022, 2025, 2026)
# global draft slot of each team pick
slot={'Blue':{1:1,2:4,3:5,4:8,5:9},'Red':{1:2,2:3,3:6,4:7,5:10}}
rows=[]
for r in T[['gameid','side','pick1','pick2','pick3','pick4','pick5']].itertuples(index=False):
    for k in range(1,6):
        ch=getattr(r,f'pick{k}')
        if isinstance(ch,str): rows.append((r.gameid,r.side,ch,k,slot[r.side][k]))
pk=pd.DataFrame(rows,columns=['gameid','side','champion','teampick','slot'])
m=P.merge(pk,on=['gameid','side','champion'],how='left')
print('pick match rate by year:', m.groupby('src_year').slot.apply(lambda s:s.notna().mean()).round(3).to_dict())
m=m[m.slot.notna() & m.golddiffat10.notna()]
# pair with lane opponent
opp=m[['gameid','position','side','slot']].copy(); opp['side']=opp.side.map({'Blue':'Red','Red':'Blue'}); opp=opp.rename(columns={'slot':'opp_slot'})
m=m.merge(opp,on=['gameid','position','side'])
m['counter']=(m.slot>m.opp_slot).astype(int)
m.to_parquet('data/proc/picks_lane.parquet')
print(m.shape)
g=m.groupby(['position','counter']).agg(n=('golddiffat10','size'),gd10=('golddiffat10','mean'),gd15=('golddiffat15','mean'),win=('result','mean')).round(1)
print(g)
print('--- same side only (blue):')
print(m[m.side=='Blue'].groupby(['position','counter']).agg(n=('golddiffat10','size'),gd10=('golddiffat10','mean'),gd15=('golddiffat15','mean'),win=('result','mean')).round(2))
print(m[m.side=='Red'].groupby(['position','counter']).agg(n=('golddiffat10','size'),gd10=('golddiffat10','mean'),gd15=('golddiffat15','mean'),win=('result','mean')).round(2))

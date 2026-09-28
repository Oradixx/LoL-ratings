"""Charge les CSV Oracle's Elixir, harmonise, sauvegarde en parquet."""
import pandas as pd, numpy as np
RAW='data/raw/'; OUT='data/proc/'
frames=[]
for f,y in [('oe_2022.csv',2022),('oe_2025.csv',2025),('lyc_2026.csv',2026)]:
    d=pd.read_csv(RAW+f,low_memory=False)
    d['src_year']=y
    frames.append(d)
df=pd.concat(frames,ignore_index=True)
df['date']=pd.to_datetime(df['date'],errors='coerce')
df=df.drop_duplicates(subset=['gameid','participantid'])
for c in df.columns:
    if df[c].dtype==object and c not in ['gameid','datacompleteness','url','league','split','side','position','playername','playerid','teamname','teamid','champion','ban1','ban2','ban3','ban4','ban5','pick1','pick2','pick3','pick4','pick5','patch','firstPick']:
        df[c]=pd.to_numeric(df[c],errors='coerce')
df['patch']=df['patch'].astype(str)
players=df[df.position!='team'].copy()
teams=df[df.position=='team'].copy()
players.to_parquet(OUT+'players.parquet'); teams.to_parquet(OUT+'teams.parquet')
print(players.shape, teams.shape)
print(players.groupby('src_year').gameid.nunique())

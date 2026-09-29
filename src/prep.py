"""Charge les CSV Oracle's Elixir, harmonise les noms de ligues, sauvegarde en parquet.

Pour chaque année, le fichier officiel (data/raw/<année>_LoL_esports_match_data_from_OraclesElixir.csv)
est utilisé s'il est présent ; sinon le miroir GitHub téléchargé par scripts/get_data.sh.
"""
import glob, os, re, sys
import pandas as pd
sys.path.insert(0,'src'); from leagues import canon
RAW='data/raw/'; OUT='data/proc/'
MIRRORS={2022:'oe_2022.csv',2025:'oe_2025.csv',2026:'lyc_2026.csv'}   # le miroir 2023 dispo ne contient que 3 ligues : ignoré
files={}
for f in glob.glob(RAW+'*_LoL_esports_match_data_from_OraclesElixir.csv'):
    y=int(re.match(r'(\d{4})_',os.path.basename(f)).group(1)); files[y]=(f,'officiel')
for y,f in MIRRORS.items():
    if y not in files and os.path.exists(RAW+f): files[y]=(RAW+f,'miroir')
frames=[]
for y,(f,kind) in sorted(files.items()):
    d=pd.read_csv(f,low_memory=False); d['src_year']=y; d['src_kind']=kind
    print(f'{y}: {kind:8s} {d.gameid.nunique():6d} games  {str(d.date.min())[:10]} -> {str(d.date.max())[:10]}  ({os.path.basename(f)})')
    frames.append(d)
df=pd.concat(frames,ignore_index=True)
df['date']=pd.to_datetime(df['date'],errors='coerce')
df=df.drop_duplicates(subset=['gameid','participantid'])
df['league_raw']=df['league']; df['league']=df['league'].map(canon)
KEEP_STR={'gameid','datacompleteness','url','league','league_raw','split','side','position','playername','playerid','teamname','teamid','champion',
          'ban1','ban2','ban3','ban4','ban5','pick1','pick2','pick3','pick4','pick5','patch','firstPick','src_kind'}
for c in df.columns:
    if df[c].dtype==object and c not in KEEP_STR:
        df[c]=pd.to_numeric(df[c],errors='coerce')
df['patch']=df['patch'].astype(str)
os.makedirs(OUT,exist_ok=True)
df[df.position!='team'].to_parquet(OUT+'players.parquet'); df[df.position=='team'].to_parquet(OUT+'teams.parquet')
print('leagues renamed:',df.loc[df.league!=df.league_raw,'league_raw'].value_counts().to_dict())

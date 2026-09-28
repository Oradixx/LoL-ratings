import pandas as pd, numpy as np
ROLE={'top':'Top','jng':'Jungle','mid':'Mid','bot':'ADC','sup':'Support'}
def load_players(year=2025):
    P=pd.read_parquet('data/proc/players.parquet')
    p=P[P.src_year==year].copy()
    p['pid']=p.playerid.fillna(('name:'+p.playername).where(p.playername.notna())).fillna('anon')
    p['role']=p.position.map(ROLE)
    p['minutes']=p.gamelength/60
    p['kda']=(p.kills+p.assists)/p.deaths.clip(lower=1)
    p['kp']=(p.kills+p.assists)/p.teamkills.replace(0,np.nan)
    return p
def last_team(p):
    return p.sort_values('date').groupby('pid').agg(name=('playername','last'),team=('teamname','last'),league=('league','last'),role=('role',lambda s:s.mode().iloc[0]))

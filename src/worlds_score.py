"""Note les pronostics figés (results/worlds2026/frozen_model.json) sur les games réelles de Worlds 2026.
À lancer après la finale (14 novembre 2026), une fois le fichier Oracle's Elixir 2026 mis à jour et src/prep.py relancé :
    python src/worlds_score.py                       # Worlds 2026
    python src/worlds_score.py --league MSI --since 2026-01-01 --smoke   # test de fonctionnement (en échantillon !)
Compositions : celles réellement alignées dans chaque game. Aucun ré-entraînement."""
import sys, json, argparse; sys.path.insert(0,'src')
import numpy as np, pandas as pd
from math import comb
from sklearn.metrics import roc_auc_score, log_loss
ap=argparse.ArgumentParser(); ap.add_argument('--league',default='WLDs'); ap.add_argument('--since',default='2026-10-01'); ap.add_argument('--smoke',action='store_true')
x=ap.parse_args()
F=json.load(open('results/worlds2026/frozen_model.json'))
a,b=F['calibration']['a'],F['calibration']['b']; TH=F['theta']; L=F['league']; unk=F['unknown_player_theta_offset']; ELO=F['elo']
team_league={t['team_key']:t['league'] for t in F['teams']}
P=pd.read_parquet('data/proc/players.parquet'); T=pd.read_parquet('data/proc/teams.parquet')
P['pid']=P.playerid.fillna(('name:'+P.playername).where(P.playername.notna())).fillna('anon')
T=T[(T.league==x.league)&(T.date>=x.since)]
if not len(T):
    print(f'aucune game {x.league} depuis {x.since} dans les données : rien à noter pour l\'instant'); sys.exit(0)
rows=[]
for gid,d in T.groupby('gameid'):
    if set(d.side)!={'Blue','Red'}: continue
    bl=d[d.side=='Blue'].iloc[0]; rd=d[d.side=='Red'].iloc[0]; s={}
    for side,t in [('Blue',bl),('Red',rd)]:
        key=str(t.teamid if pd.notna(t.teamid) else t.teamname)
        pl=P[(P.gameid==gid)&(P.side==side)&(P.pid!='anon')].pid
        fill=unk+L.get(team_league.get(key,''),0.0)
        s[side]=sum(TH.get(pid,fill) for pid in pl); s[side+'_key']=key; s[side+'_unknown']=int(sum(pid not in TH for pid in pl))
    marg=s['Blue']-s['Red']; p=1/(1+np.exp(-(a+b*marg)))
    pe=1/(1+10**(-(ELO.get(s['Blue_key'],1450)-ELO.get(s['Red_key'],1450)+20)/400))
    rows.append(dict(gameid=gid,date=bl.date,blue=bl.teamname,red=rd.teamname,bwin=float(bl.result),p_model=float(p),p_elo=float(pe),unknown=s['Blue_unknown']+s['Red_unknown']))
G=pd.DataFrame(rows).sort_values('date'); y=G.bwin.values; out={'n_games':len(G),'unknown_players':int(G.unknown.sum())}
for k in ['p_model','p_elo']:
    out[k]=dict(auc=float(roc_auc_score(y,G[k])) if len(set(y))>1 else None,logloss=float(log_loss(y,G[k],labels=[0,1])),acc=float(((G[k]>0.5)==(y==1)).mean()))
# séries : mêmes deux équipes, même jour
G['day']=pd.to_datetime(G.date).dt.date; G['A']=[min(u,v) for u,v in zip(G.blue,G.red)]; G['B']=[max(u,v) for u,v in zip(G.blue,G.red)]
ser=[]
for (A,B,day),d in G.groupby(['A','B','day']):
    aw=np.where(d.blue==A,d.bwin,1-d.bwin); wa=int(aw.sum()); mx=max(wa,len(d)-wa); n=mx
    r=dict(fmt=f'Bo{2*n-1}',a_won=float(wa>len(d)-wa))
    for k in ['p_model','p_elo']:
        pa=d[k].iloc[0] if d.blue.iloc[0]==A else 1-d[k].iloc[0]
        r[k]=sum(comb(n-1+j,j)*pa**n*(1-pa)**j for j in range(n))
    ser.append(r)
S=pd.DataFrame(ser); out['n_series']=len(S)
for k in ['p_model','p_elo']: out['series_acc_'+k]=float(((S[k]>0.5)==(S.a_won==1)).mean()) if len(S) else None
print(json.dumps(out,indent=1,ensure_ascii=False))
if not x.smoke: json.dump(out,open('results/worlds2026/score.json','w'),indent=1,ensure_ascii=False); G.to_csv('results/worlds2026/games_scored.csv',index=False)

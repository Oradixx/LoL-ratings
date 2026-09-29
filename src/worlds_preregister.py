"""Pronostics Worlds 2026, figés avant le tournoi (Worlds : 15 octobre – 14 novembre 2026).
Le modèle de prédiction (v1.2, tout l'historique jusqu'au 28 septembre 2026) est gelé dans results/worlds2026/frozen_model.json :
notes des joueurs, niveau des ligues, avantage de côté, calibration. Le commit git qui ajoute ce fichier en fait la date.
Après le tournoi, src/worlds_score.py note ces pronostics sur les games réelles (avec les compositions réellement alignées),
contre un Elo d'équipe gelé à la même date. Rien n'est ré-entraîné entre les deux."""
import sys, json, pickle, subprocess, datetime; sys.path.insert(0,'src')
from evaluate import *
from sklearn.linear_model import LogisticRegression
from leagues import MAJOR, REGION
V12=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200,home='mix')
cut=G_ALL.date.max()
m=fit(P_ALL,G_ALL,V12); unk=float(m['u'][m['gp']<10].mean())
# calibration : toutes les prédictions hors échantillon du rejeu 2026 (modèle ré-entraîné chaque mois)
preds=pickle.load(open('data/proc/rolling_preds.pkl','rb'))['v1.2 rattachement mixte']
x=pd.concat([v for k,v in preds.items() if k>=pd.Timestamp('2026-02-01')]); yb=G_ALL.loc[x.index].bwin
lr=LogisticRegression(C=1e6).fit(x.values.reshape(-1,1),yb.values); a=float(lr.intercept_[0]); b=float(lr.coef_[0,0])
# Elo d'équipe gelé à la même date (référence)
g=G_ALL.sort_values('date'); R={}
for row in g.itertuples():
    rb=R.get(row.blue_team,1450); rr=R.get(row.red_team,1450); e=1/(1+10**((rr-rb-20)/400)); d=24*(row.bwin-e)
    R[row.blue_team]=rb+d; R[row.red_team]=rr-d
# équipes des ligues majeures : composition = joueur le plus présent à chaque poste sur les 20 dernières games domestiques
p=P_ALL[(P_ALL.src_year==2026)&(P_ALL.pid!='anon')].copy(); p['team']=p.teamid.fillna(p.teamname)
dom=p[p.league.isin(MAJOR)].sort_values('date')
teams=[]
for t,d in dom.groupby('team'):
    gids=list(dict.fromkeys(d.gameid))[-20:]
    if len(gids)<10: continue
    dd=d[d.gameid.isin(gids)]; lu={}
    for ro in ['Top','Jungle','Mid','ADC','Support']:
        c=dd[dd.role==ro].groupby('pid').agg(n=('gameid','nunique'),nm=('playername','last')).sort_values('n',ascending=False)
        if len(c): lu[ro]=(c.index[0],c.nm.iloc[0])
    if len(lu)<5: continue
    s=float(sum(m['theta'].get(pid,unk) for pid,_ in lu.values()))
    teams.append(dict(team=dd.teamname.iloc[-1],team_key=str(t),league=dd.league.mode().iloc[0],region=REGION.get(dd.league.mode().iloc[0],''),
                      lineup={ro:nm for ro,(pid,nm) in lu.items()},lineup_pid={ro:pid for ro,(pid,nm) in lu.items()},strength=s,elo=float(R.get(t,1450))))
T=sorted(teams,key=lambda t:-t['strength'])
try: commit=subprocess.check_output(['git','rev-parse','--short','HEAD'],text=True).strip()
except Exception: commit=None
frozen=dict(frozen_on=datetime.date.today().isoformat(),data_until=str(cut.date()),code_commit_before_freeze=commit,config=V12,
            calibration=dict(a=a,b=b,formula='P(bleu gagne) = 1/(1+exp(-(a + b*(somme theta bleus - somme theta rouges))))'),
            unknown_player_theta_offset=unk,side=float(m['side']),
            theta={k:round(float(v),5) for k,v in m['theta'].items()},league={k:round(float(v),5) for k,v in m['league'].items()},
            elo={str(k):round(float(v),1) for k,v in R.items()},teams=T)
json.dump(frozen,open('results/worlds2026/frozen_model.json','w'),ensure_ascii=False,indent=0)
def pgame(sa,sb):   # côté neutre : moyenne de A côté bleu et A côté rouge
    return 0.5*(1/(1+np.exp(-(a+b*(sa-sb))))+1-1/(1+np.exp(-(a+b*(sb-sa)))))
print('calibration',round(a,3),round(b,3),'équipes',len(T))
for t in T[:12]: print(f"{t['team']:28s} {t['league']:6s} force {t['strength']*1000:7.0f}  P(vs n°1) {pgame(t['strength'],T[0]['strength']):.2f}  Elo {t['elo']:.0f}")

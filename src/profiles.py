"""Données des fiches joueur et de la vue équipes.
- trajectoire : note de chaque joueur au 1er de chaque mois 2026 (modèle ré-entraîné sur tout ce qui précède)
- parcours : ligue principale 2025 et 2026, promu / rétrogradé / nouveau
- équipes : composition actuelle (5 joueurs les plus présents sur les 20 dernières games) et force de l'effectif"""
import sys, json; sys.path.insert(0,'src'); from evaluate import *
from leagues import INTL, MAJOR, detect_cups
V1=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200)
V1=dict(V1,home='mix')   # v1.2 : rattachement à la ligue pondéré par la récence
r=pd.read_parquet('data/proc/ratings_now.parquet'); act=r[r.active]
# 1) trajectoires
MONTHS=pd.date_range('2026-02-01','2026-09-01',freq='MS')
traj={}
for mth in MONTHS:
    m=fit(P_ALL,G_ALL[G_ALL.date<mth],V1); th=m['theta'].reindex(act.index)
    base=th.mean(); traj[str(mth.date())[:7]]=((th-base)*1000).round(0)
    print(mth.date(),flush=True)
traj['2026-09-28']=act.points
T=pd.DataFrame(traj)
# 2) parcours
def main_league(q):
    excl=INTL|detect_cups(q)
    d=q[~q.league.isin(excl)]
    return d.groupby(['pid','league']).gameid.nunique().reset_index().sort_values('gameid').groupby('pid').league.last()
p25=P_ALL[P_ALL.src_year==2025]; p26=P_ALL[P_ALL.src_year==2026]
l25=main_league(p25)
teams25=p25.groupby(['pid','teamname']).gameid.nunique().reset_index().sort_values('gameid',ascending=False)
teams26=p26.groupby(['pid','teamname']).gameid.nunique().reset_index().sort_values('gameid',ascending=False)
def career(pid):
    out=[]
    for y,t in [(2025,teams25),(2026,teams26)]:
        d=t[t.pid==pid].head(3)
        if len(d): out.append(f"{y} : "+', '.join(f"{a.teamname} ({a.gameid})" for a in d.itertuples()))
    return ' · '.join(out)
info={}
for pid,x in act.iterrows():
    a=l25.get(pid); b=x.league26
    fl=[]
    if a is None: fl.append('new')
    elif a!=b:
        fl.append('moved')
        if a not in MAJOR and b in MAJOR: fl.append('up')
        if a in MAJOR and b not in MAJOR: fl.append('down')
    info[pid]=dict(l25=a,career=career(pid),flags=fl)
# 3) équipes : effectif actuel
q=p26.assign(team=p26.teamid.fillna(p26.teamname)).sort_values('date')
excl=INTL|detect_cups(p26)
dom=q[~q.league.isin(excl)]
last=dom.groupby('team').gameid.apply(lambda s:list(dict.fromkeys(s))[-20:])
full=fit(P_ALL,G_ALL,V1); TH=full['theta']; base=act.theta.mean()
g26=G_ALL[G_ALL.year==2026]
xhat=(predict_games(full,P_ALL,g26,full['u'][full['gp']<10].mean())+full['side']).values
from sklearn.linear_model import LogisticRegression
lr=LogisticRegression(C=1e6,fit_intercept=False).fit(xhat.reshape(-1,1),g26.bwin.values); slope=float(lr.coef_[0,0])
teams=[]
for team,gids in last.items():
    if len(gids)<10: continue
    d=dom[(dom.team==team)&dom.gameid.isin(gids)]
    lg=d.league.mode().iloc[0]; name=d.teamname.iloc[-1]
    lineup=[]
    for ro in ['Top','Jungle','Mid','ADC','Support']:
        c=d[d.role==ro].groupby('pid').agg(n=('gameid','nunique'),nm=('playername','last')).sort_values('n',ascending=False)
        if len(c): lineup.append((ro,c.index[0],c.nm.iloc[0]))
    if len(lineup)<5: continue
    th=[TH.get(pid,np.nan) for _,pid,_ in lineup]
    if any(np.isnan(th)): continue
    gp=int(p26[p26.teamname==name].gameid.nunique()); res=G_ALL.loc[G_ALL.index.intersection(p26[p26.teamname==name].gameid.unique())]
    wins=int(p26[(p26.teamname==name)].groupby('gameid').result.first().sum())
    teams.append(dict(team=name,league=lg,strength=float(np.mean(th)),lineup=[dict(r=ro,n=nm) for ro,_,nm in lineup],gp=gp,wr=wins/gp if gp else None))
TD=pd.DataFrame(teams)
TD['pts']=((TD.strength-base)*1000).round(0)
# probabilité de battre l'équipe moyenne de sa ligue (sur terrain neutre)
lm=TD.groupby('league').strength.transform('mean')
TD['p_vs_avg']=1/(1+np.exp(-slope*5*(TD.strength-lm)))
out=dict(months=list(T.columns),traj={pid:[None if pd.isna(v) else int(v) for v in T.loc[pid].values] for pid in T.index},
         info=info,teams=TD.drop(columns=['strength']).round(3).to_dict('records'),slope=slope)
json.dump(out,open('data/proc/profiles.json','w'),ensure_ascii=False,default=float)
print(len(TD),'équipes ;', sum('up' in v['flags'] for v in info.values()),'promus ;',sum('new' in v['flags'] for v in info.values()),'nouveaux')
print(TD.sort_values('pts',ascending=False).head(8)[['team','league','pts','p_vs_avg','wr']].to_string(index=False))

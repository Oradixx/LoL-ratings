"""Notes actuelles (au 28 septembre 2026) : v1.1 entraînée sur toutes les games 2025 + 2026,
avec l'incertitude statistique de chaque note (loi a posteriori de la ridge)."""
import sys, json; sys.path.insert(0,'src'); from evaluate import *
from leagues import detect_cups, INTL, MAJOR, tier
V1=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200)
tr,_,_=splits('now')
m=fit(P_ALL,tr,V1); A=fit.last_A
pl=m['u'].index; nP=len(pl); leagues=m['league'].index
pred=predict_games(m,P_ALL,tr,0); y=target(tr,'gold'); s2=float(np.var(y-(pred.values+m['side'])))
cov=s2*np.linalg.inv(A)
H=np.zeros((nP,len(leagues))); li=pd.Series(np.arange(len(leagues)),index=leagues)
H[np.arange(nP),li[m['home'].reindex(pl)].values]=1
T=np.hstack([np.eye(nP),H,np.zeros((nP,1))]); covT=T@cov@T.T; sd=np.sqrt(np.diag(covT))
# infos joueur 2026
p26=P_ALL[(P_ALL.src_year==2026)&(P_ALL.pid!='anon')]
excl=INTL|detect_cups(p26)
dom=p26[~p26.league.isin(excl)]
# ligue actuelle = ligue la plus jouée sur ses 20 dernières games domestiques (un joueur promu en cours d'année compte dans sa nouvelle ligue)
lg26=dom.sort_values('date').groupby('pid').tail(20).groupby(['pid','league']).gameid.nunique().reset_index().sort_values('gameid').groupby('pid').league.last()
info=p26.sort_values('date').groupby('pid').agg(player=('playername','last'),team=('teamname','last'),role=('role',lambda s:s.mode().iloc[0]),gp26=('gameid','nunique'),last=('date','max'))
r=pd.DataFrame({'theta':m['theta'],'u':m['u'],'home_model':m['home'],'gp_total':m['gp'],'sd':pd.Series(sd,index=pl)}).join(info,how='inner')
r['league26']=lg26.reindex(r.index).fillna(r.home_model)
r['tier']=r.league26.map(tier)
active=(r.gp26>=20)
base=r[active].theta.mean()
r['points']=((r.theta-base)*1000).round(0); r['points_sd']=(r.sd*1000).round(0); r['u_gold']=(r.u*5000).round(0)
r['active']=active
# écart au joueur moyen du même poste dans sa ligue ACTUELLE (en golds d'écart final par game)
grp=r[active].groupby(['league26','role']).theta.mean()
r['vs_role_league_gold']=((r.theta-pd.Series([grp.get((l,ro),np.nan) for l,ro in zip(r.league26,r.role)],index=r.index))*5000).round(0)
r.to_parquet('data/proc/ratings_now.parquet')
# P(n°1) sous incertitude, par rôle et par niveau
rng=np.random.default_rng(1); out={}
pidx=pd.Series(np.arange(nP),index=pl)
for tr_ in ['Ligue majeure','Académie / ligue régionale']:
    out[tr_]={}
    for ro in ['Top','Jungle','Mid','ADC','Support']:
        sel=r[active&(r.role==ro)&(r.tier==tr_)]
        idx=pidx[sel.index].values; sub=covT[np.ix_(idx,idx)]
        Lc=np.linalg.cholesky(sub+1e-10*np.eye(len(idx)))
        draws=sel.theta.values[:,None]+Lc@rng.standard_normal((len(idx),4000))
        p1=np.bincount(draws.argmax(0),minlength=len(idx))/4000
        out[tr_][ro]=pd.Series(p1,index=sel.index).sort_values(ascending=False).head(10).round(3).to_dict()
json.dump(dict(p1=out,s2=s2,base=float(base),league=(m['league']*1000).round(0).to_dict(),side=float(m['side'])),open('data/proc/current.json','w'),indent=1,ensure_ascii=False)
for tr_ in out:
    print('\n##',tr_)
    for ro in ['Top','Jungle','Mid','ADC','Support']:
        t=r[active&(r.role==ro)&(r.tier==tr_)].sort_values('theta',ascending=False).head(5)
        print(ro,[(a.player,a.team,a.league26,int(a.points),int(a.points_sd),out[tr_][ro].get(i,0)) for i,a in t.iterrows()])

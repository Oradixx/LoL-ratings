"""Le niveau d'une ligue est-il bien estimé ? Deux vérifications.
1) Incertitude : écart-type a posteriori de l'écart entre deux ligues.
2) Le juge 2026 : les joueurs qui ont CHANGÉ de ligue entre 2025 et 2026 font-ils mieux ou moins bien
   que ce que prévoyaient leurs notes 2025 ? Si une ligue est surcotée, ses anciens joueurs déçoivent ailleurs."""
import sys, json; sys.path.insert(0,'src'); from evaluate import *
import statsmodels.api as sm
V1=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200)
tr=G_ALL[G_ALL.year==2025]
m=fit(P_ALL,tr,V1); A=fit.last_A; nP=len(m['u']); leagues=list(m['league'].index)
pred=predict_games(m,P_ALL,tr,0); y=target(tr,'gold'); s2=float(np.var(y-(pred.values+m['side'])))
cov=s2*np.linalg.inv(A)
def diff(a,b):
    i,j=nP+leagues.index(a),nP+leagues.index(b)
    d=(m['league'][a]-m['league'][b])*1000; sd=np.sqrt(cov[i,i]+cov[j,j]-2*cov[i,j])*1000
    return round(d),round(sd)
out={'diff':{f'{a}-{b}':diff(a,b) for a,b in [('LCKC','LEC'),('LEC','LCS'),('LCK','LPL'),('LPL','LEC'),('LFL','LEC'),('LCKC','LCK'),('LCKC','LFL')]}}
print('écart de niveau (points) et écart-type:',out['diff'])
# 2) movers: 2026 games, résidus des prédictions gelées 2025
g26=G_ALL[G_ALL.year==2026]
unk=m['u'][m['gp']<10].mean()
p_hat=predict_games(m,P_ALL,g26,unk)+m['side']; res=target(g26,'gold')-p_hat.values
from leagues import INTL, detect_cups
p26=P_ALL[P_ALL.gameid.isin(g26.index)&(P_ALL.pid!='anon')]
excl=INTL|detect_cups(p26)
lg26=p26[~p26.league.isin(excl)].groupby(['pid','league']).gameid.nunique().reset_index().sort_values('gameid').groupby('pid').league.last()
home25=m['home']
movers=[i for i in lg26.index if i in home25.index and home25[i]!=lg26[i] and not str(home25[i]).startswith('seul')]
mv_origin=home25[movers]
q=p26[p26.pid.isin(movers)][['gameid','side','pid']]
q['orig']=q.pid.map(mv_origin); q['sgn']=np.where(q.side=='Blue',1,-1)
X=pd.crosstab(q.gameid,q.orig,values=q.sgn,aggfunc='sum').fillna(0)
keep=[c for c in X.columns if (X[c]!=0).sum()>=150]
X=X[keep].reindex(g26.index).fillna(0)
ols=sm.OLS(res,sm.add_constant(X)).fit(cov_type='HC1')
tab=pd.DataFrame({'points_par_joueur':ols.params[keep]*1000,'se':ols.bse[keep]*1000,'games':[(X[c]!=0).sum() for c in keep],'joueurs':[int((mv_origin==c).sum()) for c in keep]}).round(0).sort_values('points_par_joueur')
print('\nJoueurs qui ont changé de ligue entre 2025 et 2026 — écart à la prédiction, par ligue d\'origine')
print('(négatif = la ligue d\'origine était surcotée ; positif = sous-cotée)'); print(tab.to_string())
out['movers']=tab.reset_index().rename(columns={'index':'origine','orig':'origine'}).to_dict('records')
json.dump(out,open('data/proc/league_check.json','w'),indent=1,ensure_ascii=False,default=float)

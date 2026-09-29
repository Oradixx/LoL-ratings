"""Méta et champions, regroupés sur la saison (par split, on ne voyait que du bruit).
Question : un joueur sur un champion qu'il n'a jamais (ou presque) joué en match officiel fait-il moins bien que sa note ?
C'est la forme mesurable de « méta qui ne lui convient pas » (et du fearless draft, qui force de nouveaux champions).
Mesure hors échantillon : on part des prédictions du rejeu 2026 (modèle ré-entraîné chaque mois, qui ne connaît pas la game),
et on regarde si l'écart d'or réel s'explique en plus par le nombre de joueurs « hors confort » de chaque côté.
Coefficient appris sur février-mai 2026, jugé sur juin-septembre (critère fixé d'avance : log-loss sur la victoire)."""
import sys, json, pickle; sys.path.insert(0,'src')
from rolling import *
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import roc_auc_score, log_loss
preds=pickle.load(open('data/proc/rolling_preds.pkl','rb'))['v1.2 rattachement mixte']
x=pd.concat([preds[m] for m in MONTHS[1:]]); g=G_ALL.loc[x.index].copy(); g['x']=x
q=P_ALL[(P_ALL.pid!='anon')&P_ALL.champion.notna()][['gameid','side','pid','champion','date']].sort_values('date')
q['prior']=q.groupby(['pid','champion']).cumcount()          # games officielles déjà jouées sur ce champion (depuis janv. 2025)
q['n_before']=q.groupby('pid').cumcount()                    # games officielles déjà jouées tout court
q=q[q.gameid.isin(g.index)&(q.n_before>=30)]                 # joueurs avec un historique suffisant
out={}
for k in [0,2]:
    q[f'new{k}']=(q.prior<=k).astype(float)
    s=q.groupby(['gameid','side'])[f'new{k}'].sum().unstack().reindex(g.index).fillna(0)
    g[f'd_new{k}']=s.get('Blue',0)-s.get('Red',0)
g['share_new0']=q.groupby('gameid').new0.mean().reindex(g.index)
y_gold=np.asarray(target(g,'gold')); g['y']=y_gold
tr=g[g.date<'2026-06-01']; te=g[g.date>='2026-06-01']
for k in [0,2]:
    f=f'd_new{k}'
    ols=LinearRegression().fit(tr[['x',f]],tr.y); coef=ols.coef_[1]
    # erreur-type (OLS) du coefficient
    X=np.c_[np.ones(len(tr)),tr[['x',f]].values]; r=tr.y.values-ols.predict(tr[['x',f]]); s2=r@r/(len(tr)-3)
    se=float(np.sqrt(s2*np.linalg.inv(X.T@X)[2,2]))
    base=LogisticRegression(C=1e6).fit(tr[['x']],tr.bwin); full=LogisticRegression(C=1e6).fit(tr[['x',f]],tr.bwin)
    ll0=log_loss(te.bwin,base.predict_proba(te[['x']])[:,1]); ll1=log_loss(te.bwin,full.predict_proba(te[['x',f]])[:,1])
    a0=roc_auc_score(te.bwin,base.decision_function(te[['x']])); a1=roc_auc_score(te.bwin,full.decision_function(te[['x',f]]))
    out[f'<= {k} games'] = dict(gold_per_player=float(coef*5000),gold_se=float(se*5000),share=float(q[f'new{k}'].mean()),
                                logloss_base=float(ll0),logloss_with=float(ll1),auc_base=float(a0),auc_with=float(a1))
    print(k,{kk:round(v,4) for kk,v in out[f'<= {k} games'].items()})
# fearless : la part de champions « jamais joués » augmente-t-elle au fil d'une série ?
gg=g.assign(day=g.date.dt.date,pair=[ '|'.join(sorted([str(a),str(b)])) for a,b in zip(g.blue_team,g.red_team)]).sort_values('date')
gg['gnum']=gg.groupby(['pair','day']).cumcount()+1
out['new0_by_game_number']=gg.groupby(gg.gnum.clip(upper=5)).share_new0.mean().round(4).to_dict()
print(out['new0_by_game_number'])
json.dump(out,open('data/proc/champion_comfort.json','w'),indent=1,default=float)

import sys; sys.path.insert(0,'src'); from engine import *
from elo import run_elo
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score

P_ALL=player_games((2025,2026)); G_ALL=game_table(P_ALL)
def splits(name):
    if name=='2025split':  # entraine jan->mi-juin 2025, teste mi-juin->sept
        tr=G_ALL[(G_ALL.year==2025)&(G_ALL.date<'2025-06-15')]; te=G_ALL[(G_ALL.year==2025)&(G_ALL.date>='2025-06-15')]
        dev=te[te.date<'2025-07-31']; test=te[te.date>='2025-07-31']
    elif name=='2026':     # entraine 2025, dev = janvier 2026, test = fevrier -> septembre 2026 (notes gelees)
        tr=G_ALL[G_ALL.year==2025]; te=G_ALL[G_ALL.year==2026]
        dev=te[te.date<'2026-02-01']; test=te[te.date>='2026-02-01']
    elif name=='2026feb':  # comme la v1 de la page: test = fevrier 2026 seulement
        tr=G_ALL[G_ALL.year==2025]; te=G_ALL[G_ALL.year==2026]
        dev=te[te.date<'2026-02-01']; test=te[(te.date>='2026-02-01')&(te.date<'2026-03-01')]
    elif name=='now':      # tout jusqu'au 28 septembre 2026 (notes publiées) ; pas de test
        tr=G_ALL; dev=G_ALL.iloc[:0]; test=G_ALL.iloc[:0]
    elif name=='mv':       # multivers: entraîné avant le 1er août 2026, noté sur août-septembre 2026
        tr=G_ALL[G_ALL.date<'2026-08-01']; dev=G_ALL[G_ALL.date>='2026-08-01']; test=dev
    return tr,dev,test

def auc_ci(y,x,B=400,seed=0):
    """intervalle de confiance à 95 % de l'AUC par bootstrap sur les games."""
    rng=np.random.default_rng(seed); y=np.asarray(y); x=np.asarray(x); n=len(y); out=[]
    for _ in range(B):
        i=rng.integers(0,n,n)
        if y[i].min()!=y[i].max(): out.append(roc_auc_score(y[i],x[i]))
    return float(np.percentile(out,2.5)),float(np.percentile(out,97.5))

def score(pred_dev,pred_test,dev,test,ci=False):
    lr=LogisticRegression(C=1e6).fit(pred_dev.values.reshape(-1,1),dev.bwin.values)
    pt=lr.predict_proba(pred_test.values.reshape(-1,1))[:,1]
    out=dict(logloss=log_loss(test.bwin,pt),auc=roc_auc_score(test.bwin,pred_test.values) if pred_test.std()>0 else 0.5,
                acc=((pt>0.5)==test.bwin.values).mean(), n=len(test))
    if ci and pred_test.std()>0: out['auc_lo'],out['auc_hi']=auc_ci(test.bwin.values,pred_test.values)
    return out

def elo_preds(tr,dev,test,K=24):
    g=pd.DataFrame({'date':tr.date,'blue_k':tr.blue_team,'red_k':tr.red_team,'bwin':tr.bwin})
    _,R=run_elo(g,K=K,side_adv=20)
    def team(gs): return gs.blue_team.map(R).fillna(1450)-gs.red_team.map(R).fillna(1450)
    # Elo porté par les joueurs: Elo de la dernière équipe 2025 de chaque joueur
    q=P_ALL[P_ALL.gameid.isin(tr.index)].sort_values('date')
    q=q.assign(team=q.teamid.fillna(q.teamname))
    last=q.groupby('pid').team.last().map(R)
    def carry(gs):
        z=P_ALL[P_ALL.gameid.isin(gs.index)][['gameid','side','pid']]
        v=z.pid.map(last).fillna(1450)*np.where(z.side=='Blue',1,-1)
        return pd.Series(v.values,index=z.gameid.values).groupby(level=0).sum().reindex(gs.index)/5
    return {'Elo équipe':(team(dev),team(test)),'Elo porté par les joueurs':(carry(dev),carry(test))}

def player_score_preds(scores,dev,test):
    """scores: pd.Series pid->note (z). somme bleu - rouge."""
    def f(gs):
        z=P_ALL[P_ALL.gameid.isin(gs.index)][['gameid','side','pid']]
        v=z.pid.map(scores).fillna(scores.quantile(0.3))*np.where(z.side=='Blue',1,-1)
        return pd.Series(v.values,index=z.gameid.values).groupby(level=0).sum().reindex(gs.index)
    return f(dev),f(test)

def model_preds(cfg,tr,dev,test,unknown=None):
    p=P_ALL; m=fit(p,tr,cfg)
    unk=unknown if unknown is not None else m['u'][m['gp']<10].mean()
    return (predict_games(m,p,dev,unk),predict_games(m,p,test,unk)),m

from sklearn.model_selection import cross_val_predict
def score_dev(pred,dev):
    """logloss calibré par validation croisée sur dev + AUC (sert au réglage, jamais le test)."""
    x=pred.values.reshape(-1,1)
    pp=cross_val_predict(LogisticRegression(C=1e6),x,dev.bwin.values,cv=5,method='predict_proba')[:,1]
    return dict(logloss=log_loss(dev.bwin,pp),auc=roc_auc_score(dev.bwin,pred.values))

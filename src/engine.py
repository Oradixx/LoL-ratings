"""LoL Ratings 3.0 - moteur.
Note joueur = effet de sa ligue (estimé via les matchs internationaux et les transferts)
            + écart individuel (RAPM ridge, centré sur un prior 'box score' appris).
"""
import pandas as pd, numpy as np, sys
sys.path.insert(0,'src'); from common import *

BOX_BASE=['kpm','dthpm','apm','dpm','damageshare','damagetakenperminute','earned gpm','earnedgoldshare','cspm',
          'vspm','wpm','wcpm','cwpm','kp','ttpm']
BOX_LANE=['golddiffat15','xpdiffat15','csdiffat15']

def player_games(years=(2025,2026)):
    P=pd.read_parquet('data/proc/players.parquet'); p=P[P.src_year.isin(years)].copy()
    p['pid']=p.playerid.fillna(('name:'+p.playername).where(p.playername.notna())).fillna('anon')
    p['role']=p.position.map(ROLE); p['minutes']=p.gamelength/60
    p['kpm']=p.kills/p.minutes; p['dthpm']=p.deaths/p.minutes; p['apm']=p.assists/p.minutes
    p['cwpm']=p.controlwardsbought/p.minutes; p['ttpm']=p.damagetotowers/p.minutes
    p['kp']=(p.kills+p.assists)/p.teamkills.replace(0,np.nan)
    return p

def game_table(p):
    T=pd.read_parquet('data/proc/teams.parquet'); T=T[T.gameid.isin(p.gameid.unique())]
    b=T[T.side=='Blue'].set_index('gameid'); r=T[T.side=='Red'].set_index('gameid')
    g=pd.DataFrame({'date':b.date,'league':b.league,'year':b.src_year,'bwin':b.result,
                    'blue_team':b.teamid.fillna(b.teamname),'red_team':r.teamid.reindex(b.index).fillna(r.teamname.reindex(b.index)),
                    'golddiff_end':b.totalgold-r.totalgold.reindex(b.index),'gd15':b.golddiffat15,'minutes':b.gamelength/60})
    g=g.dropna(subset=['bwin','red_team']).sort_values('date')
    return g

def champ_adjust(p,stats,k=20,on=True):
    """retire l'effet du champion: stat - moyenne(champion, rôle) (shrinkée vers le rôle)."""
    out=p[stats].copy()
    if not on: 
        return out - p.groupby('role')[stats].transform('mean')
    rm=p.groupby('role')[stats].transform('mean')
    grp=p.groupby(['role','champion'])[stats]
    cm=grp.transform('mean'); n=grp.transform('count')
    shr=(n*cm+k*rm)/(n+k)
    return out-shr.fillna(rm)

def box_features(p,train_mask,champ=True,lane=True,shrink_k=10,stats=None):
    stats=stats or (BOX_BASE+(BOX_LANE if lane else []))
    q=p[train_mask].copy()
    adj=champ_adjust(q,stats,on=champ)
    z=adj/adj.groupby(q.role).transform('std')
    z['pid']=q.pid.values; z['role']=q.role.values
    agg=z.groupby('pid')[stats].agg(['sum','count'])
    feats={}
    for s in stats:
        feats[s]=agg[(s,'sum')]/(agg[(s,'count')]+shrink_k)   # moyenne shrinkée vers 0 (moyenne du rôle)
    F=pd.DataFrame(feats).fillna(0)
    F['has_lane']= (agg[(stats[-1],'count')]>0).astype(float) if lane else 0.0
    return F

from leagues import INTL, MAJOR, tier
def player_home(p,train_mask,mode='most'):
    """ligue 'domestique' de chaque joueur, hors tournois internationaux / coupes.
    mode='most'  : ligue où il a joué le plus de games
    mode='recent': ligue de ses 20 dernières games (un joueur promu en cours d'année compte dans sa nouvelle ligue)"""
    from leagues import detect_cups
    excl=INTL|detect_cups(p[train_mask])
    q=p[train_mask & ~p.league.isin(excl) & (p.pid!='anon')]
    if mode=='recent':
        q=q.sort_values('date').groupby('pid').tail(20)
    c=q.groupby(['pid','league']).gameid.nunique().reset_index().sort_values('gameid')
    home=c.groupby('pid').league.last()
    # joueurs vus uniquement en tournoi/coupe : groupe propre à ce tournoi (pas un groupe « international » fourre-tout)
    q2=p[train_mask & (p.pid!='anon')]
    c2=q2.groupby(['pid','league']).gameid.nunique().reset_index().sort_values('gameid').groupby('pid').league.last()
    only=c2.index.difference(home.index)
    home=pd.concat([home,('seul:'+c2[only])])
    # joueurs n'ayant joué qu'en international: ligue de leur équipe la plus fréquente
    return home

def home_weights(p,train_mask,half_life=180):
    """part (pondérée par la récence) des games domestiques de chaque joueur dans chaque ligue.
    Un joueur passé de la NLC à la LFL est rattaché surtout à la LFL, un peu à la NLC."""
    from leagues import detect_cups
    excl=INTL|detect_cups(p[train_mask])
    q=p[train_mask & ~p.league.isin(excl) & (p.pid!='anon')][['pid','league','gameid','date']].drop_duplicates(['pid','gameid'])
    end=p.loc[train_mask,'date'].max()
    q=q.assign(w=np.power(0.5,(end-q.date).dt.days/half_life))
    W=q.groupby(['pid','league']).w.sum().unstack(fill_value=0.0)
    return W.div(W.sum(axis=1),axis=0)

def design(p,g,players_idx):
    from scipy import sparse
    q=p[p.gameid.isin(g.index)][['gameid','side','pid']]
    gi=pd.Series(np.arange(len(g)),index=g.index)
    q=q[q.pid.isin(players_idx.index)]
    rows=gi[q.gameid].values; cols=players_idx[q.pid].values; vals=np.where(q.side.values=='Blue',1.0,-1.0)
    return sparse.csr_matrix((vals,(rows,cols)),shape=(len(g),len(players_idx)))

def target(g,kind):
    if kind=='result': return (g.bwin.values-0.5)*2           # +1/-1
    if kind=='gold':   return np.clip(g.golddiff_end.values/5000,-3,3)
    if kind=='mix':    return 0.5*(g.bwin.values-0.5)*2+0.5*np.clip(g.golddiff_end.values/5000,-3,3)
    raise ValueError(kind)

def fit(p,g_train,cfg):
    """theta_joueur = L[ligue domestique] + u_joueur ;  u ~ N(prior_box, 1/lam), L ~ N(0, 1/lamL)."""
    lam=cfg.get('lam',30.0); lamL=cfg.get('lamL',30.0); tau=cfg.get('tau',None)
    train_mask=p.gameid.isin(g_train.index)
    home=player_home(p,train_mask,cfg.get('home','most'))
    gp=p[train_mask & (p.pid!='anon')].groupby('pid').gameid.nunique()
    pl=gp.index; players_idx=pd.Series(np.arange(len(pl)),index=pl)
    hl=home.reindex(pl).fillna('INTL_ONLY')
    leagues=sorted(hl.unique()); league_idx=pd.Series(np.arange(len(leagues)),index=leagues)
    H=np.zeros((len(pl),len(leagues))); H[np.arange(len(pl)),league_idx[hl].values]=1
    if cfg.get('home')=='mix':
        Wm=home_weights(p,train_mask,cfg.get('home_half_life',180))
        Wm=Wm.reindex(index=pl,columns=leagues).fillna(0.0)
        has=Wm.sum(axis=1)>0
        H[has.values]=Wm.values[has.values]
    X=design(p,g_train,players_idx)
    use_league=cfg.get('league',True)
    y=target(g_train,cfg.get('target','result'))
    w=np.ones(len(g_train))
    if tau:
        age=(g_train.date.max()-g_train.date).dt.days.values; w=np.exp(-age/tau)
    from scipy import sparse
    if use_league and cfg.get('tier_prior',False):
        # niveau de ligue = moyenne de son niveau (majeure / académie-régionale) + écart propre à la ligue
        tiers=np.array([1.0 if l in MAJOR else 0.0 for l in leagues])
        H=np.hstack([H,(H@tiers)[:,None]])      # une colonne « ligue majeure » (l'autre niveau sert de référence)
    Hs=sparse.csr_matrix(H) if use_league else sparse.csr_matrix((len(pl),0))
    Xd=sparse.hstack([X, X@Hs, sparse.csr_matrix(np.ones((len(g_train),1)))]).tocsr()
    nL=Hs.shape[1]
    pen=np.r_[np.full(len(pl),lam),np.full(nL,lamL),1e-6]
    if use_league and cfg.get('tier_prior',False): pen[len(pl)+nL-1]=0.1
    if use_league and cfg.get('league_prior_w') is not None:   # force de l'a priori sur les ligues connues la saison d'avant
        for l in (cfg.get('league_prior') or {}):
            if l in league_idx.index: pen[len(pl)+league_idx[l]]=cfg['league_prior_w']
    XtW=(Xd.T.multiply(w)).tocsr(); A=(XtW@Xd).toarray()+np.diag(pen)
    import scipy.linalg as sl
    cho=sl.cho_factor(A)
    # a priori sur le niveau des ligues (ex. : la saison précédente) : la pénalité tire vers ces valeurs au lieu de 0
    beta0=np.zeros(A.shape[0])
    for l,v in (cfg.get('league_prior') or {}).items():
        if use_league and l in league_idx.index: beta0[len(pl)+league_idx[l]]=v
    def solve(yoff): return sl.cho_solve(cho,XtW@yoff+pen*beta0)
    fit.last_A=A
    beta=solve(y); prior=np.zeros(len(pl)); W=None
    if cfg.get('prior',True):
        F=box_features(p,train_mask,champ=cfg.get('champ',True),lane=cfg.get('lane',True),shrink_k=cfg.get('shrink_k',10),stats=cfg.get('stats')).reindex(pl).fillna(0)
        F=F-F.groupby(hl.values).transform('mean')      # stats relatives à la ligue domestique
        ind=beta[:len(pl)]; n=gp.reindex(pl).values.astype(float)
        from sklearn.linear_model import Ridge
        if cfg.get('role_prior',False):
            roles=p[train_mask].groupby('pid').role.agg(lambda s:s.mode().iloc[0]).reindex(pl).fillna('Mid').values
            prior=np.zeros(len(pl)); W={}
            for ro in np.unique(roles):
                mk=roles==ro
                rr=Ridge(alpha=cfg.get('prior_alpha',50.0)).fit(F.values[mk],ind[mk],sample_weight=n[mk])
                prior[mk]=rr.predict(F.values[mk])*cfg.get('prior_scale',1.0); W[ro]=pd.Series(rr.coef_,index=F.columns)
            W=pd.DataFrame(W)
        else:
            rr=Ridge(alpha=cfg.get('prior_alpha',50.0)).fit(F.values,ind,sample_weight=n)
            prior=rr.predict(F.values)*cfg.get('prior_scale',1.0); W=pd.Series(rr.coef_,index=F.columns)
        beta=solve(y-X@prior); beta[:len(pl)]+=prior
    u=pd.Series(beta[:len(pl)],index=pl)
    if nL and cfg.get('tier_prior',False):
        tb=beta[len(pl)+nL-1]; Lv=pd.Series(beta[len(pl):len(pl)+nL-1],index=leagues)+np.array([tb if l in MAJOR else 0.0 for l in leagues])
    else:
        Lv=pd.Series(beta[len(pl):len(pl)+nL],index=leagues) if nL else pd.Series(0.0,index=leagues)
    theta=u+pd.Series(H[:,:len(Lv)]@Lv.reindex(leagues).fillna(0).values,index=pl)
    return dict(u=u,theta=theta,league=Lv,home=hl,H=pd.DataFrame(H[:,:len(leagues)],index=pl,columns=leagues),side=beta[-1],prior=pd.Series(prior,index=pl),prior_w=W,gp=gp,cfg=cfg)

def rating_table(model,p):
    info=p.sort_values('date').groupby('pid').agg(name=('playername','last'),team=('teamname','last'),role=('role',lambda s:s.mode().iloc[0]))
    r=pd.DataFrame({'u':model['u'],'theta':model['theta'],'home':model['home'],'gp':model['gp'],'prior':model['prior']}).join(info)
    return r

def predict_games(model,p,g,unknown=0.0):
    """somme des theta bleus - rouges (joueurs inconnus: L de la ligue du match + unknown)."""
    q=p[p.gameid.isin(g.index)][['gameid','side','pid','league']]
    th=q.pid.map(model['theta'])
    fill=q.league.map(model['league']).fillna(0)+unknown
    th=th.fillna(fill)
    s=np.where(q.side=='Blue',1,-1)*th
    return pd.Series(s.values,index=q.gameid.values).groupby(level=0).sum().reindex(g.index).fillna(0)

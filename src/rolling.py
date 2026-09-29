"""Évaluation « en conditions réelles » sur la saison 2026.
Chaque mois de 2026, chaque modèle est ré-entraîné sur tout ce qui s'est joué avant le 1er du mois,
puis prédit les games du mois. La calibration d'un mois est apprise sur les prédictions du mois précédent.
L'Elo, lui, est mis à jour après chaque game (avantage à l'Elo)."""
import sys, json, time; sys.path.insert(0,'src'); from evaluate import *
MONTHS=pd.date_range('2026-01-01','2026-09-01',freq='MS')
def month_games(m): 
    e=m+pd.offsets.MonthBegin(1); return G_ALL[(G_ALL.date>=m)&(G_ALL.date<e)]

def elo_online(K=24,side=20,player=False):
    """Elo mis à jour après chaque game, 2025 -> 2026 sans remise à zéro.
    player=True : chaque joueur a son Elo, la force d'une équipe = moyenne des 5 joueurs."""
    g=G_ALL.sort_values('date'); R={}; pred={}
    lineup=P_ALL.groupby(['gameid','side']).pid.agg(list) if player else None
    for gid,row in zip(g.index,g.itertuples(index=False)):
        if player:
            bl=[x for x in lineup.get((gid,'Blue'),[]) if x!='anon']; rl=[x for x in lineup.get((gid,'Red'),[]) if x!='anon']
            rb=np.mean([R.get(x,1450) for x in bl]) if bl else 1450; rr=np.mean([R.get(x,1450) for x in rl]) if rl else 1450
        else:
            rb=R.get(row.blue_team,1450); rr=R.get(row.red_team,1450)
        pred[gid]=rb-rr
        e=1/(1+10**((rr-rb-side)/400)); d=K*(row.bwin-e)
        if player:
            for x in bl: R[x]=R.get(x,1450)+d
            for x in rl: R[x]=R.get(x,1450)-d
        else:
            R[row.blue_team]=rb+d; R[row.red_team]=rr-d
    return pd.Series(pred)

def kda_scores(tr):
    q=P_ALL[P_ALL.gameid.isin(tr.index)]
    a=q.groupby('pid').agg(K=('kills','sum'),D=('deaths','sum'),A=('assists','sum'),GP=('gameid','nunique'))
    k=((a.K+a.A)/a.D.clip(lower=1))[a.GP>=5]; return (k-k.mean())/k.std()

V1=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200)
MODELS={'v1.0 (2025 seul, gelée)':None,
        'v1.1 ré-entraînée chaque mois':dict(V1),
        'v1.1 + oubli progressif (1 an)':dict(V1,tau=365),
        'v1.1 + oubli progressif (6 mois)':dict(V1,tau=180),
        'v1.2 rattachement mixte':dict(V1,home='mix')}
if __name__=='__main__':
    t0=time.time()
    preds={k:{} for k in MODELS}; preds['KDA à date']={}
    frozen=fit(P_ALL,G_ALL[G_ALL.year==2025],V1); unk_f=frozen['u'][frozen['gp']<10].mean()
    for m in MONTHS:
        mg=month_games(m); tr=G_ALL[G_ALL.date<m]
        for name,cfg in MODELS.items():
            if cfg is None: preds[name][m]=predict_games(frozen,P_ALL,mg,unk_f); continue
            mm=fit(P_ALL,tr,cfg); preds[name][m]=predict_games(mm,P_ALL,mg,mm['u'][mm['gp']<10].mean())
        preds['KDA à date'][m]=player_score_preds(kda_scores(tr),mg,mg)[0]
        print(m.date(),len(mg),'games',round(time.time()-t0),'s',flush=True)
    eo=elo_online(); ep=elo_online(player=True)
    for name,s in [('Elo équipe (mis à jour à chaque game)',eo),('Elo joueurs (mis à jour à chaque game)',ep)]:
        preds[name]={m:s.reindex(month_games(m).index) for m in MONTHS}
    import pickle; pickle.dump(preds,open('data/proc/rolling_preds.pkl','wb'))
    # scoring Feb-Sep, calibration on previous month
    res={}; monthly={}
    for name,d in preds.items():
        ys=[];ps=[];xs=[]
        for i,m in enumerate(MONTHS[1:],1):
            prev=MONTHS[i-1]; gp_=month_games(prev); gm=month_games(m)
            lr=LogisticRegression(C=1e6).fit(d[prev].values.reshape(-1,1),gp_.bwin.values)
            p=lr.predict_proba(d[m].values.reshape(-1,1))[:,1]
            ys.append(gm.bwin.values); ps.append(p); xs.append(d[m].values)
            monthly.setdefault(name,{})[str(m.date())[:7]]=dict(auc=roc_auc_score(gm.bwin,d[m].values),acc=float(((p>0.5)==gm.bwin.values).mean()),n=len(gm))
        y=np.concatenate(ys); p=np.concatenate(ps); x=np.concatenate(xs)
        lo,hi=auc_ci(y,x)
        res[name]=dict(auc=roc_auc_score(y,x),auc_lo=lo,auc_hi=hi,acc=float(((p>0.5)==y).mean()),logloss=log_loss(y,p),n=int(len(y)))
        print(f"{name:42s} AUC {res[name]['auc']:.3f} [{lo:.3f}-{hi:.3f}] acc {res[name]['acc']:.3f} ll {res[name]['logloss']:.4f}")
    json.dump(dict(total=res,monthly=monthly),open('data/proc/rolling.json','w'),indent=1,ensure_ascii=False)

"""v1.5 — Réplication sur des saisons que le modèle n'a jamais vues pendant sa construction.
Le modèle a été construit sur 2025 et jugé sur 2026. Avec les fichiers 2023 et 2024, on refait les mêmes épreuves
sans rien régler :
  1. rejeu de 2024 mois par mois (historique : 2023 + 2024 déjà jouée), contre l'Elo d'équipe et l'Elo des joueurs
     mis à jour après chaque game, et le KDA ;
  2. intersaisons : février 2024 (notes 2023 gelées) et février 2025 (notes 2024 gelées), contre l'Elo gelé ;
  3. partage du mérite jugé sur les transferts 2024 -> 2025 (le prior box-score aide-t-il encore ?).
Configuration : exactement celle publiée (v1.2)."""
import sys, json, time; sys.path.insert(0,'src')
from engine import *
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss
V12=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200,home='mix')
P=player_games((2023,2024,2025)); G=game_table(P)
def auc_ci(y,x,B=400,seed=0):
    rng=np.random.default_rng(seed); y=np.asarray(y); x=np.asarray(x); o=[]
    for _ in range(B):
        i=rng.integers(0,len(y),len(y))
        if y[i].min()!=y[i].max(): o.append(roc_auc_score(y[i],x[i]))
    return float(np.percentile(o,2.5)),float(np.percentile(o,97.5))
def month_games(m): e=m+pd.offsets.MonthBegin(1); return G[(G.date>=m)&(G.date<e)]
def elo_online(player=False,K=24,side=20):
    g=G.sort_values('date'); R={}; pred={}
    lu=P.groupby(['gameid','side']).pid.agg(list) if player else None
    for gid,row in zip(g.index,g.itertuples(index=False)):
        if player:
            bl=[x for x in lu.get((gid,'Blue'),[]) if x!='anon']; rl=[x for x in lu.get((gid,'Red'),[]) if x!='anon']
            rb=np.mean([R.get(x,1450) for x in bl]) if bl else 1450; rr=np.mean([R.get(x,1450) for x in rl]) if rl else 1450
        else: rb=R.get(row.blue_team,1450); rr=R.get(row.red_team,1450)
        pred[gid]=rb-rr; e=1/(1+10**((rr-rb-side)/400)); d=K*(row.bwin-e)
        if player:
            for x in bl: R[x]=R.get(x,1450)+d
            for x in rl: R[x]=R.get(x,1450)-d
        else: R[row.blue_team]=rb+d; R[row.red_team]=rr-d
    return pd.Series(pred)
def kda_pred(tr,gs):
    q=P[P.gameid.isin(tr.index)]; a=q.groupby('pid').agg(K=('kills','sum'),D=('deaths','sum'),A=('assists','sum'),GP=('gameid','nunique'))
    k=((a.K+a.A)/a.D.clip(lower=1))[a.GP>=5]; z=(k-k.mean())/k.std()
    q2=P[P.gameid.isin(gs.index)][['gameid','side','pid']]; v=q2.pid.map(z).fillna(z.quantile(0.3))*np.where(q2.side=='Blue',1,-1)
    return pd.Series(v.values,index=q2.gameid.values).groupby(level=0).sum().reindex(gs.index)
def model_pred(tr,gs,cfg=V12):
    m=fit(P,tr,cfg); return pd.Series(np.asarray(predict_games(m,P,gs,m['u'][m['gp']<10].mean())),index=gs.index),m
def score_rolling(preds,months):
    out={}; monthly={}
    for name,d in preds.items():
        ys=[];ps=[];xs=[]
        for i,m in enumerate(months[1:],1):
            prev=months[i-1]; gp_=month_games(prev); gm=month_games(m)
            lr=LogisticRegression(C=1e6).fit(d[prev].values.reshape(-1,1),gp_.bwin.values)
            p=lr.predict_proba(d[m].values.reshape(-1,1))[:,1]; ys.append(gm.bwin.values); ps.append(p); xs.append(d[m].values)
            monthly.setdefault(name,{})[str(m.date())[:7]]=float(roc_auc_score(gm.bwin,d[m].values))
        y=np.concatenate(ys); p=np.concatenate(ps); x=np.concatenate(xs); lo,hi=auc_ci(y,x)
        out[name]=dict(auc=float(roc_auc_score(y,x)),lo=lo,hi=hi,acc=float(((p>0.5)==y).mean()),logloss=float(log_loss(y,p)),n=int(len(y)))
    return out,monthly
if __name__=='__main__':
    t0=time.time(); R={}
    # ---------- 1. rejeu de 2024
    MONTHS=pd.date_range('2024-01-01','2024-11-01',freq='MS')
    eo=elo_online(); ep=elo_online(player=True)
    preds={'v1.2 (ré-entraînée chaque mois)':{},'Elo équipe (chaque game)':{},'Elo joueurs (chaque game)':{},'KDA (chaque mois)':{}}
    frozen,_=None,None
    m23=fit(P,G[G.year==2023],V12); unk23=m23['u'][m23['gp']<10].mean(); preds['v1.2 gelée (notes 2023)']={}
    for m in MONTHS:
        mg=month_games(m); tr=G[G.date<m]
        preds['v1.2 (ré-entraînée chaque mois)'][m]=model_pred(tr,mg)[0]
        preds['Elo équipe (chaque game)'][m]=eo.reindex(mg.index); preds['Elo joueurs (chaque game)'][m]=ep.reindex(mg.index)
        preds['KDA (chaque mois)'][m]=kda_pred(tr,mg)
        preds['v1.2 gelée (notes 2023)'][m]=pd.Series(np.asarray(predict_games(m23,P,mg,unk23)),index=mg.index)
        print(m.date(),len(mg),round(time.time()-t0),'s',flush=True)
    R['rolling_2024'],R['rolling_2024_monthly']=score_rolling(preds,MONTHS)
    mb=R['rolling_2024_monthly']; R['rolling_2024_months_better_than_elo']=int(sum(mb['v1.2 (ré-entraînée chaque mois)'][k]>mb['Elo équipe (chaque game)'][k] for k in mb['Elo équipe (chaque game)']))
    R['rolling_2024_n_months']=len(MONTHS)-1
    for k,v in R['rolling_2024'].items(): print(f"{k:34s} AUC {v['auc']:.3f} [{v['lo']:.3f}-{v['hi']:.3f}] acc {v['acc']:.3f} ll {v['logloss']:.4f} n {v['n']}")
    # ---------- 2. intersaisons (notes de la saison précédente gelées, calibrées sur janvier, jugées sur février)
    R['offseason']={}
    for y in [2024,2025]:
        tr=G[G.year==y-1]; dev=G[(G.year==y)&(G.date<f'{y}-02-01')]; te=G[(G.year==y)&(G.date>=f'{y}-02-01')&(G.date<f'{y}-03-01')]
        gE=pd.DataFrame({'date':tr.date,'blue_k':tr.blue_team,'red_k':tr.red_team,'bwin':tr.bwin})
        from elo import run_elo
        _,RE=run_elo(gE,K=24,side_adv=20)
        elo=lambda gs:gs.blue_team.map(RE).fillna(1450)-gs.red_team.map(RE).fillna(1450)
        m=fit(P,tr,V12); unk=m['u'][m['gp']<10].mean(); mod=lambda gs:pd.Series(np.asarray(predict_games(m,P,gs,unk)),index=gs.index)
        o={}
        for name,f in [('v1.2 (notes gelées)',mod),('Elo équipe (gelé)',elo)]:
            a,b=f(dev),f(te); lr=LogisticRegression(C=1e6).fit(a.values.reshape(-1,1),dev.bwin.values); p=lr.predict_proba(b.values.reshape(-1,1))[:,1]
            o[name]=dict(auc=float(roc_auc_score(te.bwin,b)),acc=float(((p>0.5)==te.bwin.values).mean()),n=len(te))
        R['offseason'][str(y)]=o; print('intersaison',y,o,flush=True)
    # ---------- 3. transferts 2024 -> 2025
    g24=G[G.year==2024]; g25=G[G.year==2025]
    p24=P[P.gameid.isin(g24.index)&(P.pid!='anon')]; team24=p24.assign(t=p24.teamid.fillna(p24.teamname)).groupby('pid').t.agg(lambda s:s.mode().iloc[0])
    q=P[P.gameid.isin(g25.index)&(P.pid!='anon')].copy(); q['t']=q.teamid.fillna(q.teamname)
    q['moved']=q.pid.isin(team24.index)&(q.pid.map(team24)!=q.t)
    mv=q.groupby(['gameid','side']).moved.sum().unstack(); gR=g25.loc[g25.index.intersection(mv.index[mv.max(axis=1)>=2])]
    ma=fit(P,g24,V12); mb_=fit(P,g24,dict(V12,prior=False))
    xa=np.asarray(predict_games(ma,P,gR,ma['u'][ma['gp']<10].mean())); xb=np.asarray(predict_games(mb_,P,gR,mb_['u'][mb_['gp']<10].mean())); yb=gR.bwin.values
    rng=np.random.default_rng(0); dd=[]
    for _ in range(1000):
        i=rng.integers(0,len(yb),len(yb)); dd.append(roc_auc_score(yb[i],xa[i])-roc_auc_score(yb[i],xb[i]))
    R['transfer_2025']=dict(n=int(len(yb)),auc_prior=float(roc_auc_score(yb,xa)),auc_noprior=float(roc_auc_score(yb,xb)),
                            gain=float(roc_auc_score(yb,xa)-roc_auc_score(yb,xb)),lo=float(np.percentile(dd,2.5)),hi=float(np.percentile(dd,97.5)))
    print('transferts 2024->2025',R['transfer_2025'])
    json.dump(R,open('data/proc/replication.json','w'),indent=1,ensure_ascii=False)
    print('done',round(time.time()-t0),'s')

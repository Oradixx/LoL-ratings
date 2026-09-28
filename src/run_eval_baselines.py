import sys, json; sys.path.insert(0,'src'); from evaluate import *
res={}
for sp in ['2025split','2026']:
    tr,dev,test=splits(sp); print('\n##',sp,'train',len(tr),'dev',len(dev),'test',len(test))
    out={}
    out['Pile ou face (+ côté bleu)']=score(pd.Series(0.0,index=dev.index)+np.random.rand(len(dev))*1e-9,pd.Series(0.0,index=test.index),dev,test)
    for k,(a,b) in elo_preds(tr,dev,test).items(): out[k]=score(a,b,dev,test)
    # v0.1 / v0.3 as player scores computed on train
    import importlib
    ptr=P_ALL[P_ALL.gameid.isin(tr.index)].copy()
    agg=ptr.groupby('pid').agg(K=('kills','sum'),D=('deaths','sum'),A=('assists','sum'),GP=('gameid','nunique'))
    kda=((agg.K+agg.A)/agg.D.clip(lower=1)); kda=kda[agg.GP>=5]; kda=(kda-kda.mean())/kda.std()
    out['v0.1 KDA']=score(*player_score_preds(kda,dev,test),dev,test)
    for name,cfg in [('RAPM sans prior ni ligue',dict(prior=False,league=False)),('RAPM + ligue',dict(prior=False)),('RAPM + ligue + prior box',dict())]:
        (a,b),m=model_preds(cfg,tr,dev,test); out[name]=score(a,b,dev,test)
    for k,v in out.items(): print(f'{k:35s} logloss={v["logloss"]:.4f} auc={v["auc"]:.3f} acc={v["acc"]:.3f}')
    res[sp]=out
json.dump(res,open('data/proc/eval_baselines.json','w'),indent=1)

"""L'examen final: février 2026. Calibré sur janvier 2026, évalué UNE fois sur février."""
import sys, json, pickle; sys.path.insert(0,'src'); from evaluate import *
tr,dev,test=splits('2026')
V1=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200)
out={}
out['Pile ou face (+ côté bleu)']=score(pd.Series(np.random.rand(len(dev))*1e-9,index=dev.index),pd.Series(0.0,index=test.index),dev,test)
for k,(a,b) in elo_preds(tr,dev,test).items(): out[k]=score(a,b,dev,test)
agg0=pd.read_parquet('data/proc/agg_v0.parquet')
kda=(agg0.KDA-agg0.KDA.mean())/agg0.KDA.std(); out['v0.1 KDA']=score(*player_score_preds(kda,dev,test),dev,test)
v03=(agg0.v03-agg0.v03.mean())/agg0.v03.std(); out['v0.3 LoL Ratings 2.0 (corrigé par rôle)']=score(*player_score_preds(v03,dev,test),dev,test)
(a,b),m=model_preds(dict(V1,prior=False,league=False),tr,dev,test); out['v0.4 RAPM brut']=score(a,b,dev,test)
(a,b),m=model_preds(dict(V1,prior=False),tr,dev,test); out['v0.5 RAPM + ligues']=score(a,b,dev,test)
(a,b),m=model_preds(V1,tr,dev,test); out['v1.0 LoL Ratings 3.0']=score(a,b,dev,test)
mv=pickle.load(open('data/proc/multiverse.pkl','rb'))
PD=pd.DataFrame({r['seed']:r['pred_dev'] for r in mv}); PT=pd.DataFrame({r['seed']:r['pred_test'] for r in mv})
PD=PD/PD.std(); PT=PT/PD.std().values if False else PT/pd.DataFrame({r['seed']:r['pred_dev'] for r in mv}).std()
out['Multivers (moyenne des 600 univers)']=score(PD.mean(1),PT.mean(1),dev,test)
aucs=pd.Series({r['seed']:r['dev_auc'] for r in mv}); wts=np.exp((aucs-aucs.max())*100); wts/=wts.sum()
out['Multivers pondéré par la prédiction (janvier)']=score((PD*wts).sum(1),(PT*wts).sum(1),dev,test)
# individual universes test auc distribution
from sklearn.metrics import roc_auc_score
ua=[roc_auc_score(test.bwin,PT[c]) for c in PT.columns]
out['_univers_auc_test']=dict(min=float(np.min(ua)),p10=float(np.percentile(ua,10)),median=float(np.median(ua)),p90=float(np.percentile(ua,90)),max=float(np.max(ua)))
for k,v in out.items(): print(k,v)
json.dump(out,open('data/proc/final_test.json','w'),indent=1,ensure_ascii=False)
# Los Ratones case study (LEC 2026, jan+feb)
gg=G_ALL[(G_ALL.year==2026)]
lr_games=P_ALL[(P_ALL.src_year==2026)&(P_ALL.teamname.str.contains('Ratones',na=False))].gameid.unique()
cs=gg.loc[gg.index.intersection(lr_games)]
if len(cs):
    lr_side=P_ALL[P_ALL.gameid.isin(cs.index)&P_ALL.teamname.str.contains('Ratones',na=False)].groupby('gameid').side.first()
    from sklearn.linear_model import LogisticRegression
    def prob(pred_dev,pred_cs):
        lr=LogisticRegression(C=1e6).fit(pred_dev.values.reshape(-1,1),dev.bwin.values); return lr.predict_proba(pred_cs.values.reshape(-1,1))[:,1]
    pv1=prob(model_preds(V1,tr,dev,test)[0][0],predict_games(m,P_ALL,cs,m['u'][m['gp']<10].mean()))
    pk=prob(player_score_preds(kda,dev,test)[0],player_score_preds(kda,cs,cs)[0])
    blue=(lr_side.reindex(cs.index)=='Blue').values
    lrwin=np.where(blue,cs.bwin,1-cs.bwin)
    case=dict(n=len(cs),leagues=cs.league.value_counts().to_dict(),actual=float(lrwin.mean()),
              v1=float(np.where(blue,pv1,1-pv1).mean()),kda=float(np.where(blue,pk,1-pk).mean()))
    print('Los Ratones',case); json.dump(case,open('data/proc/case_ratones.json','w'),indent=1)

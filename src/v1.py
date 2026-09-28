import sys, json; sys.path.insert(0,'src'); from evaluate import *
V1=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200)
tr,dev,test=splits('2026')
(a,b),m=model_preds(V1,tr,dev,test)
r=rating_table(m,P_ALL[P_ALL.gameid.isin(tr.index)])
r['gold']=r.theta*5000; r['gold_u']=r.u*5000
r.to_parquet('data/proc/ratings_v1.parquet')
J={}
J['league_gold']=(m['league']*5000).round(0).sort_values(ascending=False).to_dict()
print('League effects (gold/game per player):',J['league_gold'])
print('side adv (gold):',round(m['side']*5000))
W=m['prior_w']; print((W*5000).round(0).to_string()); J['prior_w']=(W*5000).round(1).to_dict()
top={}
for ro in ['Top','Jungle','Mid','ADC','Support']:
    t=r[(r.role==ro)&(r.gp>=20)].sort_values('gold',ascending=False).head(10)[['name','team','home','gp','gold','gold_u']]
    top[ro]=t.round(0).to_dict('records'); print(ro); print(t.round(0).to_string(index=False))
J['top']=top
# diagnostics on dev (Jan 2026)
d={}
d['v1_dev']=score_dev(a,dev)
# league only
lo=m.copy(); lo=dict(m); lo['theta']=m['home'].map(m['league'])
d['league_only_dev']=score_dev(predict_games(lo,P_ALL,dev,0),dev)
# domestic games only
dom=dev[dev.league.isin(P_ALL[P_ALL.gameid.isin(dev.index)].league.unique())]
# placebo: shuffle outcomes in train
trs=tr.copy(); rng=np.random.default_rng(0); trs['golddiff_end']=rng.permutation(trs.golddiff_end.values); trs['bwin']=(trs.golddiff_end>0).astype(int)
mp=fit(P_ALL,trs,V1); d['placebo_dev']=score_dev(predict_games(mp,P_ALL,dev,0),dev)
print(d); J['diag']=d
json.dump(J,open('data/proc/v1.json','w'),indent=1,default=str,ensure_ascii=False)

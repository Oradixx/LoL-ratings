import sys, json; sys.path.insert(0,'src'); from evaluate import *
V1=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200)
tr,dev,test=splits('2026')
m=fit(P_ALL,tr,V1); A=fit.last_A
pl=m['u'].index; nP=len(pl); leagues=m['league'].index
# residual variance
X=design(P_ALL,tr,pd.Series(np.arange(nP),index=pl))
pred=predict_games(m,P_ALL,tr,0); y=target(tr,'gold')
s2=np.var(y-(pred.values+m['side']))
cov=s2*np.linalg.inv(A)
# theta = u + L[home] -> transform
H=np.zeros((nP,len(leagues))); li=pd.Series(np.arange(len(leagues)),index=leagues)
H[np.arange(nP),li[m['home'].reindex(pl)].values]=1
T=np.hstack([np.eye(nP),H,np.zeros((nP,1))])
covT=T@cov@T.T
sd=np.sqrt(np.diag(covT))
r=rating_table(m,P_ALL[P_ALL.gameid.isin(tr.index)]); r['sd']=pd.Series(sd,index=pl)
r['gold']=r.theta*5000; r['gold_sd']=r.sd*5000
# sample posterior to get P(#1 in role) among players with >=20 games
rng=np.random.default_rng(1); out={}
for ro in ['Top','Jungle','Mid','ADC','Support']:
    idx=np.where((r.role==ro)&(r.gp>=20))[0]
    sub=covT[np.ix_(idx,idx)]; mu=r.theta.values[idx]
    Lc=np.linalg.cholesky(sub+1e-12*np.eye(len(idx)))
    draws=mu[:,None]+Lc@rng.standard_normal((len(idx),4000))
    best=np.bincount(draws.argmax(0),minlength=len(idx))/4000
    ranks=(-draws).argsort(0).argsort(0)+1
    top5=(ranks<=5).mean(1)
    d=pd.DataFrame({'name':r.name.values[idx],'team':r.team.values[idx],'p1':best,'top5':top5,'gold':r.gold.values[idx],'sd':r.gold_sd.values[idx]}).sort_values('p1',ascending=False).head(6)
    out[ro]=d.round(3).to_dict('records'); print(ro); print(d.round(3).to_string(index=False))
# posterior correlation between Gen.G teammates
gen=r[(r.team=='Gen.G')&(r.gp>=50)]
gi=[list(pl).index(i) for i in gen.index]
C=covT[np.ix_(gi,gi)]; D=np.sqrt(np.diag(C)); corr=C/np.outer(D,D)
print('Gen.G posterior corr:\n',pd.DataFrame(corr,index=gen.name,columns=gen.name).round(2))
# sd vs lineup stability
r.to_parquet('data/proc/ratings_v1_unc.parquet')
json.dump(dict(p1=out,s2=s2,gen_corr=pd.DataFrame(corr,index=gen.name,columns=gen.name).round(2).to_dict()),open('data/proc/uncertainty.json','w'),indent=1,default=str,ensure_ascii=False)

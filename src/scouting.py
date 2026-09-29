import sys, json; sys.path.insert(0,'src'); from evaluate import *
from sklearn.metrics import roc_auc_score
r=pd.read_parquet('data/proc/ratings_v1.parquet')
p26=P_ALL[P_ALL.src_year==2026]
print(sorted(p26.league.unique()))
from leagues import MAJOR; MAJ25=MAJOR; MAJ26=MAJOR
pl26=p26.groupby('pid').league.agg(set)
cand=r[(~r.home.isin(MAJ25))&(r.gp>=20)&(r.home!='INTL_ONLY')].copy()
cand['seen26']=cand.index.isin(pl26.index)
cand['promoted']=cand.index.map(lambda i: len(pl26.get(i,set()) & MAJ26)>0)
agg0=pd.read_parquet('data/proc/agg_v0.parquet')
cand=cand.join(agg0[['KDA','W','v03']],how='left')
print('candidates',len(cand),'seen in 2026',cand.seen26.sum(),'promoted',cand.promoted.sum())
res={}
for col in ['u','theta','KDA','W','v03']:
    c=cand.dropna(subset=[col])
    res[col]=roc_auc_score(c.promoted,c[col]); print(col,'AUC promotion',round(res[col],3),'n',len(c))
top=cand.sort_values('theta',ascending=False).head(15)[['name','team','home','role','gp','theta','promoted']]
top['gold']=top.theta*5000; print(top.to_string())
# where did promoted go
pro=cand[cand.promoted].sort_values('theta',ascending=False)
pro['to']=[','.join(sorted(pl26[i]&MAJ26)) for i in pro.index]
print(pro[['name','home','role','theta','to']].head(25).to_string())
# rank percentile of promoted in theta
cand['pct']=cand.theta.rank(pct=True)
print('median pct of promoted:',cand[cand.promoted].pct.median())
print('share promoted among top 20 theta:',cand.sort_values('theta',ascending=False).head(20).promoted.mean(),' base rate', cand.promoted.mean())
json.dump(dict(auc=res,n=len(cand),n_prom=int(cand.promoted.sum()),top=top.assign(gold=top.gold.round(0)).to_dict('records'),
  promoted=pro[['name','home','role','theta','to']].head(25).to_dict('records'),top20_rate=float(cand.sort_values('theta',ascending=False).head(20).promoted.mean()),base=float(cand.promoted.mean())),
  open('data/proc/scouting.json','w'),indent=1,default=str,ensure_ascii=False)

import sys, json, pickle; sys.path.insert(0,'src')
import pandas as pd, numpy as np
from engine import player_games
mv=pickle.load(open('data/proc/multiverse.pkl','rb'))
p=player_games((2025,))
info=p.sort_values('date').groupby('pid').agg(name=('playername','last'),team=('teamname','last'),role=('role',lambda s:s.mode().iloc[0]))
aucs=pd.Series({r['seed']:r['dev_auc'] for r in mv})
w=np.exp((aucs-aucs.max())*100); w/=w.sum()
print('dev AUC: min %.3f median %.3f max %.3f'%(aucs.min(),aucs.median(),aucs.max()), ' effective n universes weighted:',round(1/(w**2).sum(),1))
cfg=pd.DataFrame([dict(seed=r['seed'],**{k:v for k,v in r['cfg'].items() if k!='stats'},nstats=len(r['cfg']['stats'])) for r in mv]).set_index('seed')
cfg['auc']=aucs
eff={}
for c in ['target','prior','role_prior','champ','lane','tau','min_gp']:
    eff[c]=cfg.groupby(cfg[c].astype(str)).auc.mean().round(4).to_dict()
eff['lamL_bin']=cfg.groupby(pd.cut(cfg.lamL,[0,2,5,10,31])).auc.mean().round(4).astype(float).to_dict()
eff['lam_bin']=cfg.groupby(pd.cut(cfg.lam,[0,30,60,100,201])).auc.mean().round(4).astype(float).to_dict()
for k,v in eff.items(): print(k,v)
res={'auc':dict(min=aucs.min(),median=aucs.median(),max=aucs.max()),'choice_effects':{k:{str(a):b for a,b in v.items()} for k,v in eff.items()}}
roles=['Top','Jungle','Mid','ADC','Support']
rank_rows=[]
for r in mv:
    th=r['theta']; gp=r['gp']; ok=gp[gp>=r['cfg']['min_gp']].index
    t=pd.DataFrame({'theta':th.reindex(ok)}).join(info[['role']])
    t['rank']=t.groupby('role').theta.rank(ascending=False)
    t['seed']=r['seed']; rank_rows.append(t.reset_index())
R=pd.concat(rank_rows); R=R.rename(columns={'index':'pid'}) if 'pid' not in R.columns else R
R['w']=R.seed.map(w)
nU=len(mv)
out={}
for ro in roles:
    d=R[R.role==ro]
    g=d.groupby('pid').agg(n1=('rank',lambda s:(s==1).sum()),top5=('rank',lambda s:(s<=5).sum()),top10=('rank',lambda s:(s<=10).sum()),med=('rank','median'),mean=('rank','mean'))
    g['w1']=d[d['rank']==1].groupby('pid').w.sum(); g['w1']=g.w1.fillna(0)
    g=g.join(info[['name','team']])
    g['p1']=g.n1/nU; g['p5']=g.top5/nU; g['p10']=g.top10/nU
    top=g.sort_values(['n1','top5'],ascending=False).head(6)
    out[ro]=top[['name','team','p1','p5','p10','med','w1']].round(3).to_dict('records')
    print('\n',ro); print(top[['name','team','p1','p5','p10','med','w1']].round(3).to_string(index=False))
res['roles']=out
json.dump(res,open('data/proc/multiverse_summary.json','w'),indent=1,default=str,ensure_ascii=False)

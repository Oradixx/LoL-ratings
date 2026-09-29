"""Résumé du multivers (400 versions) : qui reste n°1 de son rôle, dans chaque niveau de ligue."""
import sys, json, pickle; sys.path.insert(0,'src')
import pandas as pd, numpy as np
mv=pickle.load(open('data/proc/multiverse.pkl','rb'))
r=pd.read_parquet('data/proc/ratings_now.parquet'); r=r[r.active]
aucs=pd.Series({u['seed']:u['dev_auc'] for u in mv})
cfg=pd.DataFrame([dict(seed=u['seed'],**{k:v for k,v in u['cfg'].items() if k!='stats'}) for u in mv]).set_index('seed'); cfg['auc']=aucs
eff={c:cfg.groupby(cfg[c].astype(str)).auc.mean().round(4).to_dict() for c in ['target','prior','role_prior','champ','lane','tau','min_gp','home']}
eff['lamL']={str(k):v for k,v in cfg.groupby(pd.cut(cfg.lamL,[0,2,5,10,31])).auc.mean().round(4).items()}
eff['lam']={str(k):v for k,v in cfg.groupby(pd.cut(cfg.lam,[0,30,60,100,201])).auc.mean().round(4).items()}
print('AUC août-sept 2026: min %.3f médiane %.3f max %.3f'%(aucs.min(),aucs.median(),aucs.max()))
for k,v in eff.items(): print(k,v)
# rangs par (niveau, rôle) dans chaque univers
ranks=[]
for u in mv:
    ok=u['gp'][u['gp']>=u['cfg']['min_gp']].index.intersection(r.index)
    t=r.loc[ok,['tier','role']].assign(theta=u['theta'].reindex(ok).values)
    ranks.append(t.groupby(['tier','role']).theta.rank(ascending=False).rename(u['seed']))
R=pd.concat(ranks,axis=1)
stats=pd.DataFrame({'mv_p1':(R==1).mean(1),'mv_top5':(R<=5).mean(1),'mv_median_rank':R.median(1),'mv_present':R.notna().mean(1)})
stats.to_parquet('data/proc/mv_stats.parquet')
out={}
for tr in ['Ligue majeure','Deuxième niveau','Troisième niveau']:
    out[tr]={}
    for ro in ['Top','Jungle','Mid','ADC','Support']:
        sel=r[(r.tier==tr)&(r.role==ro)].join(stats)
        top=sel.sort_values(['mv_p1','mv_top5'],ascending=False).head(5)
        out[tr][ro]=top[['player','team','league26','mv_p1','mv_top5','mv_median_rank']].round(3).to_dict('records')
        print(tr,ro,[(a.player,round(a.mv_p1,2)) for a in top.itertuples()])
json.dump(dict(auc=dict(min=aucs.min(),median=aucs.median(),max=aucs.max(),n=len(mv)),choice_effects=eff,roles=out),
          open('data/proc/multiverse_summary.json','w'),indent=1,default=str,ensure_ascii=False)

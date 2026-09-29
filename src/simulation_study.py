"""Étude par simulation : la vérité est connue, le modèle la retrouve-t-il ?

Structure réelle de la saison 2026 (mêmes games, mêmes joueurs, mêmes coéquipiers, mêmes stats), mais résultats simulés :
  note vraie = note estimée par le modèle de saison + delta_i,  delta_i ~ N(0, sigma)  (talent que les stats ne voient pas)
  niveau vrai des ligues = niveau estimé + epsilon_L,           epsilon_L ~ N(0, 80 points)
  écart d'or simulé = somme(notes vraies bleues) - somme(rouges) + côté + bruit (variance des résidus réels)
Puis on ré-entraîne exactement le modèle publié et on compare à la vérité. Mesures :
  - corrélation note estimée / note vraie, erreur moyenne ;
  - couverture des ± (part des joueurs dont la vraie note est à moins de 1 et 2 écarts-types) : 68 % et 95 % attendus ;
  - écarts entre coéquipiers : le modèle retrouve-t-il qui est meilleur que qui dans une même équipe ?
  - n°1 de chaque poste (ligues majeures) retrouvé ;
séparément pour les rosters « inséparables » (>= 80 % des games avec les mêmes quatre coéquipiers) et les autres.
sigma = 0 est optimiste (la vérité vient en partie des stats que le modèle utilise) ; sigma = 100 ou 200 points ajoute
du talent invisible dans les stats, que seul le résultat des games peut révéler."""
import sys, json, time; sys.path.insert(0,'src')
from seasons import *
from leagues import tier as tier_of
lv=json.load(open('data/proc/season_2025.json'))['league']; L26={k:v/1000 for k,v in lv.items()}
CFG=dict(V,league_prior=L26,league_prior_w=LEAGUE_PRIOR_W)
g=G_ALL[G_ALL.year==2026].copy()
m0=fit(P_ALL,g,CFG); A0=fit.last_A
info,excl=player_info(2026)
act=info.index[(info.gp>=20)&info.league.notna()].intersection(m0['theta'].index)
# stabilité du roster : part des games avec les mêmes quatre coéquipiers
q=P_ALL[P_ALL.gameid.isin(g.index)&(P_ALL.pid!='anon')][['gameid','side','pid','teamname']]
lu=q.groupby(['gameid','side']).pid.agg(lambda s:tuple(sorted(s)))
qq=q.join(lu.rename('lu'),on=['gameid','side']); qq['mates']=[tuple(x for x in l if x!=me) for l,me in zip(qq.lu,qq.pid)]
rs=qq.groupby('pid').mates.agg(lambda s:s.value_counts(normalize=True).iloc[0]).reindex(act).fillna(0)
stable=rs>=0.8
team=info.team.reindex(act); role=info.role.reindex(act); tr=info.league.reindex(act).map(tier_of)
pairs=[(a,b) for t,ix in team.groupby(team).groups.items() for i,a in enumerate(ix) for b in list(ix)[i+1:]]
pa=np.array([p[0] for p in pairs]); pb=np.array([p[1] for p in pairs]); pstable=(stable[pa].values&stable[pb].values)
# bruit : variance des résidus du modèle réel
res0=np.asarray(target(g,'gold'))-(np.asarray(predict_games(m0,P_ALL,g,m0['u'][m0['gp']<10].mean()))+m0['side'])
sig_noise=float(np.std(res0))
pl=m0['theta'].index; H=m0['H']
def one(sigma,seed,cfg=CFG):
    rng=np.random.default_rng(seed)
    eps=pd.Series(rng.normal(0,0.08,H.shape[1]),index=H.columns)
    th=m0['theta']+rng.normal(0,sigma/1000,len(pl))+H.values@eps.values
    idx=pd.Series(np.arange(len(pl)),index=pl); X=design(P_ALL,g,idx)
    y=X@th.values+m0['side']+rng.normal(0,sig_noise,len(g))
    gs=g.copy(); gs['golddiff_end']=y*5000; gs['bwin']=(y>0).astype(float)
    m=fit(P_ALL,gs,cfg)
    sd,_,_=posterior_sd(m,gs)
    est=m['theta'].reindex(act); tru=th.reindex(act); s=sd.reindex(act)
    est=est-est.mean(); tru=tru-tru.mean()
    z=((est-tru)/s).abs()
    out=dict(corr=float(est.corr(tru)),rmse=float(np.sqrt(((est-tru)**2).mean())*1000))
    for nm,mk in [('stable',stable),('mobile',~stable)]:
        out[f'rmse_{nm}']=float(np.sqrt(((est-tru)[mk]**2).mean())*1000)
        out[f'cov1_{nm}']=float((z[mk]<1).mean()); out[f'cov2_{nm}']=float((z[mk]<2).mean())
    de=est[pa].values-est[pb].values; dt=tru[pa].values-tru[pb].values
    out['pair_corr_stable']=float(np.corrcoef(de[pstable],dt[pstable])[0,1]); out['pair_corr_other']=float(np.corrcoef(de[~pstable],dt[~pstable])[0,1])
    hit=[]
    for ro in ['Top','Jungle','Mid','ADC','Support']:
        mk=(tr=='Ligue majeure')&(role==ro)
        hit.append(est[mk].idxmax()==tru[mk].idxmax())
    out['no1_found']=float(np.mean(hit))
    return out
if __name__=='__main__':
    t0=time.time(); R={}
    R['meta']=dict(n_active=int(len(act)),n_stable=int(stable.sum()),noise_sd=sig_noise,n_pairs=len(pairs),n_pairs_stable=int(pstable.sum()))
    print(R['meta'],flush=True)
    for sigma in [0,100,200]:
        rows=[one(sigma,1000*sigma+k) for k in range(6)]
        R[f'sigma_{sigma}']={k:float(np.mean([r[k] for r in rows])) for k in rows[0]}
        print(sigma,round(time.time()-t0),'s',{k:round(v,3) for k,v in R[f'sigma_{sigma}'].items()},flush=True)
    # le prior box-score aide-t-il à retrouver la vérité quand une partie du talent est invisible dans les stats ?
    for name,cfg in [('sans prior box-score',dict(CFG,prior=False))]:
        rows=[one(100,5000+k,cfg) for k in range(6)]
        R[f'sigma_100 {name}']={k:float(np.mean([r[k] for r in rows])) for k in rows[0]}
        print(name,{k:round(v,3) for k,v in R[f'sigma_100 {name}'].items()},flush=True)
    json.dump(R,open('data/proc/simulation_study.json','w'),indent=1)

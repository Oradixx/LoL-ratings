"""Multivers des notes de saison : N versions raisonnables du modèle, entraînées sur une seule saison.
Pour chaque joueur actif : part des versions où il est n°1 / top 5 de son poste dans son niveau."""
import sys, json, time, pickle; sys.path.insert(0,'src')
import numpy as np, pandas as pd
from multiprocessing import Pool
N=int(sys.argv[1]) if len(sys.argv)>1 else 300
YEARS=[int(y) for y in sys.argv[2].split(',')] if len(sys.argv)>2 else [2026,2025]
def work(args):
    seed,year=args
    import evaluate as E
    from engine import fit
    from multiverse import sample
    cfg=sample(seed)
    if year==2026:
        lv=json.load(open('data/proc/season_2025.json'))['league']; cfg['league_prior']={k:v/1000 for k,v in lv.items()}; cfg['league_prior_w']=100.0
    m=fit(E.P_ALL,E.G_ALL[E.G_ALL.year==year],cfg)
    return seed,year,m['theta'].astype('float32'),cfg['min_gp']
if __name__=='__main__':
    t0=time.time(); import os
    res=pickle.load(open('data/proc/season_mv_raw.pkl','rb')) if os.path.exists('data/proc/season_mv_raw.pkl') else {}
    for y in YEARS: res[y]=[]
    with Pool(2) as pool:
        for i,(seed,year,th,mg) in enumerate(pool.imap_unordered(work,[(s,y) for y in YEARS for s in range(N)])):
            res[year].append((seed,th,mg))
            if i%100==0: print(i,round(time.time()-t0),'s',flush=True)
    pickle.dump(res,open('data/proc/season_mv_raw.pkl','wb'))
    for year in [2025,2026]:
        r=pd.read_parquet(f'data/proc/season_{year}.parquet'); r=r[r.active]
        ranks=[]
        for seed,th,mg in res[year]:
            ok=r.index[r.gp>=mg].intersection(th.index)
            t=r.loc[ok,['tier','role']].assign(theta=th.reindex(ok).values)
            ranks.append(t.groupby(['tier','role']).theta.rank(ascending=False).rename(seed))
        R=pd.concat(ranks,axis=1)
        st=pd.DataFrame({'mv_p1':(R==1).mean(axis=1),'mv_top5':(R<=5).mean(axis=1),'mv_median_rank':R.median(axis=1)})
        # hors ligues majeures, tous postes confondus : qui est le mieux noté ?
        nm=r[r.tier!='Ligue majeure']; rk=[]
        for seed,th,mg in res[year]:
            ok=nm.index[nm.gp>=max(20,mg)].intersection(th.index); rk.append(th.reindex(ok).rank(ascending=False).rename(seed))
        K=pd.concat(rk,axis=1); st['nm_p1']=(K==1).mean(axis=1); st['nm_p10']=(K<=10).mean(axis=1)
        st.to_parquet(f'data/proc/season_{year}_mv.parquet')
        print(year,'ok',len(st))
    print('done',round(time.time()-t0),'s')

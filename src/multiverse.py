"""Le multivers : N versions raisonnables de LoL Ratings 3.0."""
import sys, json, time; sys.path.insert(0,'src')
import numpy as np, pandas as pd
from multiprocessing import Pool
N=int(sys.argv[1]) if len(sys.argv)>1 else 600
def sample(seed):
    rng=np.random.default_rng(seed)
    from engine import BOX_BASE
    stats=[s for s in BOX_BASE if rng.random()>0.15]
    cfg=dict(target=str(rng.choice(['result','gold','mix'])),lam=float(np.exp(rng.uniform(np.log(15),np.log(200)))),
             lamL=float(np.exp(rng.uniform(np.log(1),np.log(30)))),prior=bool(rng.random()<0.8),role_prior=bool(rng.random()<0.5),
             prior_alpha=float(np.exp(rng.uniform(np.log(20),np.log(1000)))),prior_scale=float(rng.uniform(0.5,1.2)),
             champ=bool(rng.random()<0.5),lane=bool(rng.random()<0.5),tau=[None,None,None,180,365][rng.integers(5)],
             min_gp=int(rng.choice([10,20,40])),home=str(rng.choice(['most','mix'])))
    cfg['stats']=stats+(['golddiffat15','xpdiffat15','csdiffat15'] if cfg['lane'] else [])
    return cfg
def work(seed):
    """chaque univers: (1) entraîné avant août 2026, noté sur août-sept. 2026 ; (2) ré-entraîné sur tout pour le classement."""
    import evaluate as E
    from engine import fit, predict_games
    cfg=sample(seed); t=time.time()
    tr,dev,_=E.splits('mv')
    m1=fit(E.P_ALL,tr,cfg); a=predict_games(m1,E.P_ALL,dev,m1['u'][m1['gp']<10].mean())
    sc=E.score_dev(a,dev)
    trn,_,_=E.splits('now'); m=fit(E.P_ALL,trn,cfg)
    return dict(seed=seed,cfg=cfg,dev_auc=sc['auc'],dev_ll=sc['logloss'],theta=m['theta'].astype('float32'),
                gp=m['gp'],home=m['home'],secs=time.time()-t)

if __name__=='__main__':
    t0=time.time(); res=[]
    with Pool(2) as pool:
        for i,r in enumerate(pool.imap_unordered(work,range(N))):
            res.append(r)
            if i%50==0: print(i,round(time.time()-t0),'s',flush=True)
    import pickle; pickle.dump(res,open('data/proc/multiverse.pkl','wb'))
    print('done',len(res),round(time.time()-t0),'s')

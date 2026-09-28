import sys, json, itertools, time; sys.path.insert(0,'src'); from evaluate import *
S={k:splits(k) for k in ['2025split','2026']}
def dev_eval(cfg):
    out={}
    for k,(tr,dev,test) in S.items():
        if k=='2025split': 
            # pour 2025split on n'utilise que la partie dev (mi-juin -> juillet)
            pass
        (a,b),m=model_preds(cfg,tr,dev,test)
        out[k]=score_dev(a,dev)
    return out,m
base=dict(lam=30,lamL=30,target='result')
log=[]
def run(name,cfg):
    t=time.time(); o,m=dev_eval(cfg)
    row=dict(name=name,**{f'{k}_{mm}':round(v[mm],4) for k,v in o.items() for mm in ['logloss','auc']},cfg=cfg)
    log.append(row); print(name, {k:(round(v['logloss'],4),round(v['auc'],3)) for k,v in o.items()}, f'{time.time()-t:.0f}s',flush=True)
if __name__=="__main__":
    for lam in [10,30,100]:
        for lamL in [3,30,300]:
            run(f"lam{lam}_L{lamL}",dict(base,lam=lam,lamL=lamL))
    json.dump(log,open('data/proc/tune1.json','w'),indent=1,default=str)

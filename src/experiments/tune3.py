import sys, json; sys.path.insert(0,'src'); sys.path.insert(0,'src/experiments'); from tune import run, log
import tune, evaluate
b=dict(lam=50,lamL=3,target='gold')
run('G',b)
run('G_roleprior',dict(b,role_prior=True))
run('G_lam30',dict(b,lam=30))
run('G_lam150',dict(b,lam=150))
run('G_lamL10',dict(b,lamL=10))
run('G_roleprior_alpha200',dict(b,role_prior=True,prior_alpha=200))
json.dump(log,open('data/proc/tune3.json','w'),indent=1,default=str)

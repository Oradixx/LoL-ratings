import sys, json; sys.path.insert(0,'src'); sys.path.insert(0,'src/experiments')
from tune import run, log
V1=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200)
run('V1 (2025 complet)',V1)
run('V1 home=recent',dict(V1,home='recent'))
run('V1 lamL=10',dict(V1,lamL=10))
run('V1 lam=30',dict(V1,lam=30))
json.dump(log,open('data/proc/tune4.json','w'),indent=1,default=str)

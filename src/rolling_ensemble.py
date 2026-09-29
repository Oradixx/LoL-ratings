"""Et si on combinait la v1.1 (ré-entraînée chaque mois) avec l'Elo joueurs (mis à jour à chaque game) ?"""
import sys, json, pickle; sys.path.insert(0,'src'); from rolling import *
preds=pickle.load(open('data/proc/rolling_preds.pkl','rb'))
A=preds['v1.1 ré-entraînée chaque mois']; B=preds['Elo joueurs (mis à jour à chaque game)']; C=preds['Elo équipe (mis à jour à chaque game)']
ys=[];ps=[];xs=[]
for i,m in enumerate(MONTHS[1:],1):
    prev=MONTHS[i-1]; gp_=month_games(prev); gm=month_games(m)
    Xp=np.c_[A[prev].values,B[prev].values/400,C[prev].values/400]; Xm=np.c_[A[m].values,B[m].values/400,C[m].values/400]
    lr=LogisticRegression(C=10).fit(Xp,gp_.bwin.values)
    p=lr.predict_proba(Xm)[:,1]; ys.append(gm.bwin.values); ps.append(p)
y=np.concatenate(ys); p=np.concatenate(ps); lo,hi=auc_ci(y,p)
r=dict(auc=roc_auc_score(y,p),auc_lo=lo,auc_hi=hi,acc=float(((p>0.5)==y).mean()),logloss=log_loss(y,p),n=int(len(y)))
print('ensemble v1.1 + Elo joueurs + Elo équipe',r)
J=json.load(open('data/proc/rolling.json')); J['total']['v1.1 + Elo (combinés)']=r; json.dump(J,open('data/proc/rolling.json','w'),indent=1,ensure_ascii=False)

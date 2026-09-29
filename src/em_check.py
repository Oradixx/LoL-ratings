"""Les EMEA Masters comptent-ils pour situer les ERL ? Modèle actuel avec et sans les games d'EM."""
import sys, json; sys.path.insert(0,'src'); from evaluate import *
V1=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200)
tr,_,_=splits('now')
ERL=['LFL','PRM','LES','TCL','NLC','LIT','HLL','EBL','RL','ROL','HM','LPLOL','AL','NL','HC']
def levels(t):
    m=fit(P_ALL,t,V1); A=fit.last_A; nP=len(m['u']); lg=list(m['league'].index)
    pred=predict_games(m,P_ALL,t,0); s2=float(np.var(target(t,'gold')-(pred.values+m['side'])))
    C=s2*np.linalg.inv(A); out={}
    for l in ERL+['LEC']:
        if l in lg:
            i=nP+lg.index(l); j=nP+lg.index('LEC')
            out[l]=dict(level=float(m['league'][l]*1000),vs_lec=float((m['league'][l]-m['league']['LEC'])*1000),sd_vs_lec=float(np.sqrt(C[i,i]+C[j,j]-2*C[i,j])*1000))
    return out
em_games=int(tr.league.eq('EM').sum())
a=levels(tr); b=levels(tr[tr.league!='EM'])
res={'em_games':em_games,'with':a,'without':b}
print('EM games:',em_games)
for l in ERL:
    if l in a and l in b: print(f"{l:6s} vs LEC avec EM {a[l]['vs_lec']:+6.0f} ±{a[l]['sd_vs_lec']:.0f}   sans EM {b[l]['vs_lec']:+6.0f} ±{b[l]['sd_vs_lec']:.0f}")
json.dump(res,open('data/proc/em_check.json','w'),indent=1)

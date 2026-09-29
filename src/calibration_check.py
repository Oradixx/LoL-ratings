"""Les probabilités annoncées sont-elles justes ? (saison 2026 rejouée mois par mois, comme rolling.py)
- calibration : quand le modèle annonce 70 %, l'équipe gagne-t-elle 7 fois sur 10 ? (courbe de fiabilité, ECE)
- scores probabilistes : log-loss et Brier, contre les Elo et contre « toujours le taux de victoire du côté bleu » ;
- séries Bo3 / Bo5 : probabilité de gagner la série déduite de la probabilité par game (games supposées indépendantes)."""
import sys, json, pickle; sys.path.insert(0,'src')
from rolling import *
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, log_loss, brier_score_loss
preds=pickle.load(open('data/proc/rolling_preds.pkl','rb'))
NAMES={'v1.2 rattachement mixte':'v1.2','Elo équipe (mis à jour à chaque game)':'Elo équipe','Elo joueurs (mis à jour à chaque game)':'Elo joueurs','KDA à date':'KDA'}
P={}
for name,short in NAMES.items():
    d=preds[name]; parts=[]
    for i,m in enumerate(MONTHS[1:],1):
        prev=MONTHS[i-1]; gp_=month_games(prev); gm=month_games(m)
        lr=LogisticRegression(C=1e6).fit(d[prev].values.reshape(-1,1),gp_.bwin.values)
        parts.append(pd.Series(lr.predict_proba(d[m].values.reshape(-1,1))[:,1],index=gm.index))
    P[short]=pd.concat(parts)
gg=G_ALL.loc[P['v1.2'].index]; y=gg.bwin.values
out={'games':{},'reliability':{}}
base=np.full(len(y),G_ALL[G_ALL.year==2025].bwin.mean())
out['games']['taux bleu constant']=dict(logloss=float(log_loss(y,base)),brier=float(brier_score_loss(y,base)))
for k,p in P.items():
    p=p.values; bins=np.clip((p*10).astype(int),0,9)
    rel=pd.DataFrame({'b':bins,'p':p,'y':y}).groupby('b').agg(n=('y','size'),pred=('p','mean'),obs=('y','mean'))
    ece=float((rel.n*(rel.pred-rel.obs).abs()).sum()/rel.n.sum())
    out['games'][k]=dict(logloss=float(log_loss(y,p)),brier=float(brier_score_loss(y,p)),auc=float(roc_auc_score(y,p)),ece=ece)
    out['reliability'][k]=rel.round(4).reset_index().to_dict('records')
    print(f"{k:12s} log-loss {out['games'][k]['logloss']:.4f}  Brier {out['games'][k]['brier']:.4f}  ECE {ece:.4f}")
print('constant   ',out['games']['taux bleu constant'])
# ---- séries : mêmes deux équipes, même jour, même ligue
g=gg.copy(); g['day']=g.date.dt.date
g['A']=np.where(g.blue_team.astype(str)<g.red_team.astype(str),g.blue_team.astype(str),g.red_team.astype(str))
g['B']=np.where(g.blue_team.astype(str)<g.red_team.astype(str),g.red_team.astype(str),g.blue_team.astype(str))
g['a_blue']=g.blue_team.astype(str)==g.A; g['a_win']=np.where(g.a_blue,g.bwin,1-g.bwin)
g=g.sort_values('date'); rows=[]
for (a,b,day),d in g.groupby(['A','B','day']):
    wa=int(d.a_win.sum()); wb=len(d)-wa; mx=max(wa,wb)
    fmt={1:'Bo1',2:'Bo3',3:'Bo5'}.get(mx)
    if fmt is None or (fmt=='Bo1' and len(d)>1): continue
    first=d.index[0]; r=dict(fmt=fmt,a_won=float(wa>wb))
    for k,p in P.items():
        pa=p[first] if d.a_blue.iloc[0] else 1-p[first]
        n=int(fmt[-1])//2+1
        from math import comb
        r[k]=sum(comb(n-1+j,j)*pa**n*(1-pa)**j for j in range(n))   # probabilité de gagner n games avant d'en perdre n
    rows.append(r)
S=pd.DataFrame(rows); out['series']={}
for fmt in ['Bo1','Bo3','Bo5']:
    s=S[S.fmt==fmt]; out['series'][fmt]={'n':int(len(s))}
    for k in P:
        out['series'][fmt][k]=dict(auc=float(roc_auc_score(s.a_won,s[k])),acc=float(((s[k]>0.5)==(s.a_won==1)).mean()),brier=float(brier_score_loss(s.a_won,s[k])))
    print(fmt,len(s),{k:(round(v['auc'],3),round(v['acc'],3)) for k,v in out['series'][fmt].items() if k!='n'})
json.dump(out,open('data/proc/calibration_check.json','w'),indent=1,ensure_ascii=False)

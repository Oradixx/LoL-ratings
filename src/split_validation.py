"""Vérification de la v1.3 : l'écart par compétition est-il du signal ou du bruit ?
Protocole hors échantillon : dans chaque saison, les games sont coupées au hasard en deux moitiés A et B
(à l'intérieur de chaque compétition). Le modèle de saison ET les écarts par compétition sont appris sur A seulement,
puis on regarde si, sur les games B jamais vues, « note de saison + écart » prédit mieux que la note de saison seule.
Réglages comparés (force de la régularisation, point de départ tiré des stats ou non) : choisis sur 2025,
confirmés sur 2026, pour ne pas sur-ajuster."""
import sys, json, time; sys.path.insert(0,'src')
from seasons import *
from sklearn.metrics import roc_auc_score
LAMS=[3,10,30,100,300,1000]
def variants():
    out=[('aucun écart (note de saison seule)',None,None,0)]
    for s in [0.5,1,2]: out.append((f'stats seules ×{s}',None,'stats',s))
    for l in LAMS: out.append((f'résultats seuls, λ={l}',l,'ridge',0))
    for l in LAMS: out.append((f'stats + résultats, λ={l}',l,'both',1))
    return out
VAR=variants()
def run(year,rep,levels):
    rng=np.random.default_rng(100+rep); g=G_ALL[G_ALL.year==year]
    info,excl=player_info(year); p,comps=competitions(year,info,excl)
    gcomp=p.groupby('gameid').comp.first().reindex(g.index)
    isB=pd.Series(rng.random(len(g))<0.5,index=g.index); gA=g[~isB]; gB=g[isB]
    c=dict(V)
    if levels: c['league_prior']=levels
    m=fit(P_ALL,gA,c); unk=m['u'][m['gp']<10].mean()
    PRI=split_priors(m,year,p[p.gameid.isin(gA.index)])
    resA=pd.Series(np.asarray(target(gA,'gold'))-(np.asarray(predict_games(m,P_ALL,gA,unk))+m['side']),index=gA.index)
    baseB=pd.Series(np.asarray(predict_games(m,P_ALL,gB,unk))+m['side'],index=gB.index)
    yB=pd.Series(np.asarray(target(gB,'gold')),index=gB.index)
    contrib={v[0]:pd.Series(0.0,index=gB.index) for v in VAR}
    q=P_ALL[P_ALL.gameid.isin(g.index)&(P_ALL.pid!='anon')][['gameid','side','pid']]
    for comp in comps:
        ga=gcomp.index[(gcomp==comp)&~isB]; gb=gcomp.index[(gcomp==comp)&isB]
        if len(ga)<4 or len(gb)<1: continue
        qa=q[q.gameid.isin(ga)]; pls=sorted(qa.pid.unique()); idx=pd.Series(np.arange(len(pls)),index=pls)
        def X(gids,qq):
            gi=pd.Series(np.arange(len(gids)),index=gids); qq=qq[qq.pid.isin(idx.index)]
            M=np.zeros((len(gids),len(pls))); M[gi[qq.gameid].values,idx[qq.pid].values]=np.where(qq.side.values=='Blue',1.0,-1.0); return M
        XA=X(ga,qa); XB=X(gb,q[q.gameid.isin(gb)]); r=resA.loc[ga].values
        d0=np.array([PRI.get((pid,comp),0.0) for pid in pls]); XtX=XA.T@XA; I=np.eye(len(pls))
        for name,lam,kind,s in VAR:
            if kind is None: continue
            if kind=='stats': d=s*d0
            elif kind=='ridge': d=np.linalg.solve(XtX+lam*I,XA.T@r)
            else: d=d0+np.linalg.solve(XtX+lam*I,XA.T@(r-XA@d0))
            contrib[name].loc[gb]=XB@d
    out={}
    e0=yB-baseB
    for name,*_ in VAR:
        pr=baseB+contrib[name]; e=yB-pr
        out[name]=dict(mse_gain=float((e0**2).mean()-(e**2).mean()),auc=float(roc_auc_score(gB.bwin,pr)),
                       corr=float(np.corrcoef(contrib[name],e0)[0,1]) if contrib[name].std()>0 else 0.0)
    return out
if __name__=='__main__':
    t0=time.time(); R={}
    lv=json.load(open('data/proc/season_2025.json'))['league']; L26={k:v/1000 for k,v in lv.items()}
    for year,levels in [(2025,None),(2026,L26)]:
        reps=[run(year,k,levels) for k in range(3)]
        R[year]={name:{k:float(np.mean([r[name][k] for r in reps])) for k in reps[0][name]} for name in reps[0]}
        R[year]['_sd']={name:float(np.std([r[name]['auc'] for r in reps])) for name in reps[0]}
        print(year,round(time.time()-t0),'s',flush=True)
        for name in reps[0]: print(f"  {name:40s} gainMSE×1000 {R[year][name]['mse_gain']*1000:7.2f}  AUC {R[year][name]['auc']:.4f}  corr {R[year][name]['corr']:.3f}")
    json.dump(R,open('data/proc/split_validation.json','w'),indent=1,ensure_ascii=False)

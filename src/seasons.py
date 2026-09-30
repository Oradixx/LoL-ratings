"""Notes par saison, et par compétition / split à l'intérieur de la saison.

Pour une saison Y :
- le modèle (v1.2 : cible or, prior appris par poste, rattachement aux ligues pondéré par la récence) est entraîné
  sur les seules games de Y ; le niveau des ligues part de la saison précédente quand elle existe
  (a priori, pas une contrainte : les games de Y le corrigent) ;
- pour chaque compétition (ex. « LEC Summer », « MSI »), l'écart propre au joueur sur cette compétition est estimé
  sur les résidus du modèle de la saison, avec une forte régularisation : note du split = note de la saison + écart.
Sortie : data/proc/season_<Y>.parquet (joueurs), data/proc/season_<Y>.json (compétitions, écarts, équipes, trajectoires).
"""
import sys, json, os; sys.path.insert(0,'src'); from evaluate import *
from leagues import INTL, MAJOR, REGION, DESC, detect_cups, tier as tier_of, majors, SUCCESSOR_OF
# v1.5 : quatre saisons (2023-2026). Le modèle de chaque saison ne voit que ses games ; seule l'a priori sur les ligues
# relie une saison à la précédente.
SEASONS=[2023,2024,2025,2026]
P_ALL=player_games(tuple(SEASONS)); G_ALL=game_table(P_ALL)
V=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200,home='mix')
# Réglage validé hors échantillon (src/split_validation.py) : games coupées en deux moitiés au hasard, écarts appris
# sur l'une, jugés sur l'autre. Choisi sur 2025, confirmé sur 2026. λ=30 et le point de départ tiré des stats
# dégradaient la prédiction des games jamais vues. Sans stats, λ=1000 est le meilleur réglage sur 2025 (critère fixé d'avance : erreur sur l'écart d'or, la cible du modèle), et il améliore aussi 2026.
LAMBDA_SPLIT=1000.0
USE_STATS_PRIOR=False
# Force de l'a priori « niveau des ligues de la saison d'avant » (src/league_prior_check.py) : sans effet sur des moitiés
# de saison tirées au hasard, +0,010 d'AUC sur le rejeu mois par mois de 2026 (surtout en début de saison). Plateau dès 100.
LEAGUE_PRIOR_W=100.0
NAMES={'WLDs':'Worlds','FST':'First Stand','EM':'EMEA Masters','AM':'Asia Masters','DCup':'Demacia Cup','LTA':'LTA Championship',
       'EWC':'Esports World Cup','MSI':'MSI','KeSPA Cup':'KeSPA Cup'}
TIERCODE={'Ligue majeure':'M','Deuxième niveau':'2','Troisième niveau':'3'}
ALSO_MIN=10     # games minimum dans une autre ligue domestique pour être aussi listé dans son tableau

def prior_for(year):
    """niveau des ligues estimé sur la saison précédente (None pour la première saison), étendu aux ligues qui
    prennent la suite d'une autre (SUCCESSOR_OF)."""
    f=f'data/proc/season_{year-1}.json'
    if year-1 not in SEASONS or not os.path.exists(f): return None
    lv={k:v/1000 for k,v in json.load(open(f))['league'].items()}
    for new,old in SUCCESSOR_OF.items():
        if old in lv and new not in lv: lv[new]=lv[old]
    return lv

def season_fit(year,cfg=V,prior_levels=None):
    g=G_ALL[G_ALL.year==year]
    c=dict(cfg);
    if prior_levels is not None: c['league_prior']=prior_levels; c['league_prior_w']=LEAGUE_PRIOR_W
    return fit(P_ALL,g,c), g

def posterior_sd(m,g):
    A=fit.last_A; pl=m['u'].index; nP=len(pl); H=m['H'].values; nL=H.shape[1]
    pred=predict_games(m,P_ALL,g,0); s2=float(np.var(target(g,'gold')-(pred.values+m['side'])))
    cov=s2*np.linalg.inv(A)
    T=np.hstack([np.eye(nP),H,np.zeros((nP,A.shape[0]-nP-nL))])
    covT=T@cov@T.T
    return pd.Series(np.sqrt(np.diag(covT)),index=pl), s2, covT

def player_info(year):
    p=P_ALL[(P_ALL.src_year==year)&(P_ALL.pid!='anon')]
    excl=INTL|detect_cups(p)
    dom=p[~p.league.isin(excl)]
    lg=dom.sort_values('date').groupby('pid').tail(20).groupby(['pid','league']).gameid.nunique().reset_index().sort_values('gameid').groupby('pid').league.last()
    info=p.sort_values('date').groupby('pid').agg(player=('playername','last'),team=('teamname','last'),role=('role',lambda s:s.mode().iloc[0]),gp=('gameid','nunique'))
    info['league']=lg.reindex(info.index)
    # games et dernière équipe par ligue domestique : l'équipe affichée est celle de la ligue affichée,
    # et un joueur qui a fait des allers-retours (ex. LCK CL <-> LCK) est aussi listé dans son autre ligue (>= ALSO_MIN games)
    per=dom.sort_values('date').groupby(['pid','league']).agg(games=('gameid','nunique'),team=('teamname','last')).reset_index()
    main_team=per.merge(info.league.rename('main').reset_index(),on='pid').query('league==main').set_index('pid').team
    info['team']=main_team.reindex(info.index).fillna(info.team)
    oth=per.merge(info.league.rename('main').reset_index(),on='pid').query('league!=main and games>=@ALSO_MIN')
    info['also']=pd.Series({pid:[[r.league,int(r.games),r.team] for r in d.sort_values('games',ascending=False).itertuples()] for pid,d in oth.groupby('pid')}).reindex(info.index)
    info['main_games']=per.merge(info.league.rename('main').reset_index(),on='pid').query('league==main').set_index('pid').games.reindex(info.index)
    return info, excl

def competitions(year,info,excl):
    p=P_ALL[(P_ALL.src_year==year)&(P_ALL.pid!='anon')].copy()
    sp=p.split.astype('string').fillna('')
    p['comp']=np.where(sp.str.len()>0,p.league+' '+sp,p.league)
    p['comp']=np.where(p.playoffs.fillna(0).astype(int)==1,p.comp+' · playoffs',p.comp+np.where(p.league.isin(excl),'',' · saison régulière'))
    comps={}
    for c,d in p.groupby('comp'):
        lg=d.league.iloc[0]; n=d.gameid.nunique()
        if n<8: continue
        if lg in excl:
            homes=d.drop_duplicates('pid').pid.map(info.league).dropna()
            tiers=homes.map(lambda l:tier_of(l,year)); t=tiers.mode().iloc[0] if len(tiers) else 'Deuxième niveau'
            regs=homes.map(REGION).dropna(); reg=regs.mode().iloc[0] if (len(regs) and (regs==regs.mode().iloc[0]).mean()>=0.8) else 'International'
            label=NAMES.get(lg,lg)+('' if c==lg else c[len(lg):])
        else:
            t=tier_of(lg,year); reg=REGION.get(lg,'Autre'); label=c
        comps[c]=dict(label=label,league=lg,tier=TIERCODE.get(t,'2'),region=reg,games=int(n))
    return p, comps

def split_priors(m,year,p):
    """point de départ de l'écart d'un joueur sur une compétition : ses stats sur cette compétition comparées à ses stats
    de la saison (z-scores par poste, corrigés du champion), converties en note avec les poids appris par poste.
    Sans ça, l'écart d'une compétition serait le même pour les cinq joueurs d'un roster qui ne change pas."""
    from engine import champ_adjust, BOX_BASE, BOX_LANE
    stats=BOX_BASE+BOX_LANE
    q=p.copy()
    q['minutes']=q.gamelength/60; q['kpm']=q.kills/q.minutes; q['dthpm']=q.deaths/q.minutes; q['apm']=q.assists/q.minutes
    q['cwpm']=q.controlwardsbought/q.minutes; q['ttpm']=q.damagetotowers/q.minutes; q['kp']=(q.kills+q.assists)/q.teamkills.replace(0,np.nan)
    adj=champ_adjust(q,stats,on=True); z=adj/adj.groupby(q.role).transform('std')
    z['pid']=q.pid.values; z['comp']=q.comp.values
    season=z.groupby('pid')[stats].mean(); split=z.groupby(['pid','comp'])[stats].mean(); n=z.groupby(['pid','comp']).size()
    diff=(split-season.reindex(split.index.get_level_values(0)).values).mul(n/(n+10),axis=0).fillna(0.0)
    W=m['prior_w']; roles=p.groupby('pid').role.agg(lambda s:s.mode().iloc[0])
    pri=pd.Series(0.0,index=diff.index)
    for ro in W.columns:
        mk=diff.index.get_level_values(0).map(roles)==ro
        w=W[ro].reindex(stats).fillna(0.0).values
        pri[mk]=diff[mk].values@w
    return pri

def split_deltas(m,year,p,comps,s2):
    """écart par joueur et par compétition = point de départ tiré des stats + correction ridge sur les résidus (lambda=LAMBDA_SPLIT)."""
    th=m['theta']; out=[]; PRI=split_priors(m,year,p) if USE_STATS_PRIOR else {}
    for c,meta in comps.items():
        gids=p[p.comp==c].gameid.unique(); g=G_ALL.loc[G_ALL.index.intersection(gids)]
        if len(g)<8: continue
        q=P_ALL[P_ALL.gameid.isin(g.index)&(P_ALL.pid!='anon')][['gameid','side','pid']]
        pls=sorted(q.pid.unique()); idx=pd.Series(np.arange(len(pls)),index=pls); gi=pd.Series(np.arange(len(g)),index=g.index)
        X=np.zeros((len(g),len(pls))); X[gi[q.gameid].values,idx[q.pid].values]=np.where(q.side.values=='Blue',1.0,-1.0)
        res=target(g,'gold')-(predict_games(m,P_ALL,g,m['u'][m['gp']<10].mean()).values+m['side'])
        d0=np.array([PRI.get((pid,c),0.0) for pid in pls]) if USE_STATS_PRIOR else np.zeros(len(pls))
        Ainv=np.linalg.inv(X.T@X+LAMBDA_SPLIT*np.eye(len(pls)))
        d=d0+Ainv@X.T@(res-X@d0); sd=np.sqrt(s2*np.diag(Ainv))
        st=p[p.comp==c].groupby('pid').agg(gp=('gameid','nunique'),win=('result','mean'),K=('kills','sum'),D=('deaths','sum'),A=('assists','sum'),dpm=('dpm','mean'),dmg=('damageshare','mean'))
        for pid in pls:
            if pid not in st.index: continue
            s=st.loc[pid]
            out.append(dict(pid=pid,comp=c,gp=int(s.gp),win=float(s.win),kda=float((s.K+s.A)/max(s.D,1)),dpm=None if pd.isna(s.dpm) else float(s.dpm),
                            dmg=None if pd.isna(s.dmg) else float(s.dmg),d=float(d[idx[pid]]),dsd=float(sd[idx[pid]])))
    return pd.DataFrame(out)

def teams_view(m,year,info,excl,base):
    p=P_ALL[(P_ALL.src_year==year)&(P_ALL.pid!='anon')]
    q=p.assign(team=p.teamid.fillna(p.teamname)).sort_values('date'); dom=q[~q.league.isin(excl)]
    last=dom.groupby('team').gameid.apply(lambda s:list(dict.fromkeys(s))[-20:])
    g=G_ALL[G_ALL.year==year]; xhat=(predict_games(m,P_ALL,g,m['u'][m['gp']<10].mean())+m['side']).values
    slope=float(LogisticRegression(C=1e6,fit_intercept=False).fit(xhat.reshape(-1,1),g.bwin.values).coef_[0,0])
    TH=m['theta']; rows=[]
    for team,gids in last.items():
        if len(gids)<10: continue
        d=dom[(dom.team==team)&dom.gameid.isin(gids)]; lg=d.league.mode().iloc[0]; name=d.teamname.iloc[-1]
        lineup=[]
        for ro in ['Top','Jungle','Mid','ADC','Support']:
            c=d[d.role==ro].groupby('pid').agg(n=('gameid','nunique'),nm=('playername','last')).sort_values('n',ascending=False)
            if len(c): lineup.append((ro,c.index[0],c.nm.iloc[0]))
        if len(lineup)<5 or any(pid not in TH.index for _,pid,_ in lineup): continue
        allg=p[p.teamname==name].groupby('gameid').result.first()
        rows.append(dict(team=name,league=lg,strength=float(np.mean([TH[pid] for _,pid,_ in lineup])),lineup=[dict(r=ro,n=nm) for ro,_,nm in lineup],
                         gp=int(len(allg)),wr=float(allg.mean()) if len(allg) else None))
    T=pd.DataFrame(rows); T['pts']=((T.strength-base)*1000).round(0)
    lm=T.groupby('league').strength.transform('mean'); T['p_vs_avg']=1/(1+np.exp(-slope*5*(T.strength-lm)))
    return T.drop(columns=['strength']).round(3).to_dict('records')

def trajectories(year,active_idx,prior_levels):
    g=G_ALL[G_ALL.year==year]; months=pd.date_range(f'{year}-02-01',g.date.max(),freq='MS'); traj={}
    for mth in months:
        c=dict(V);
        if prior_levels is not None: c['league_prior']=prior_levels; c['league_prior_w']=LEAGUE_PRIOR_W
        mm=fit(P_ALL,g[g.date<mth],c); th=mm['theta'].reindex(active_idx)
        traj[str(mth.date())[:7]]=((th-th.mean())*1000).round(0)
    return pd.DataFrame(traj)

def flags(year,info):
    if year-1 not in P_ALL.src_year.unique(): return {pid:[] for pid in info.index}
    prev,excl=player_info(year-1)
    out={}
    for pid,x in info.iterrows():
        a=prev.league.get(pid) if pid in prev.index else None; b=x.league; f=[]
        if a is None or pd.isna(a): f.append('new')
        elif a!=b:
            f.append('moved')
            if a not in majors(year-1) and b in majors(year): f.append('up')
            if a in majors(year-1) and b not in majors(year): f.append('down')
        out[pid]=f
    return out

def career(year,pids):
    t=P_ALL[P_ALL.src_year.isin([year-1,year])].groupby(['src_year','pid','teamname']).gameid.nunique().reset_index().sort_values('gameid',ascending=False)
    out={}
    for pid in pids:
        parts=[]
        for y in [year-1,year]:
            d=t[(t.src_year==y)&(t.pid==pid)].head(3)
            if len(d): parts.append(f"{y} : "+', '.join(f"{a.teamname} ({a.gameid})" for a in d.itertuples()))
        out[pid]=' · '.join(parts)
    return out

if __name__=='__main__':
    for year in SEASONS:
        levels=prior_for(year)
        m,g=season_fit(year,V,levels)
        sd,s2,covT=posterior_sd(m,g)
        info,excl=player_info(year)
        r=pd.DataFrame({'theta':m['theta'],'u':m['u'],'sd':sd}).join(info,how='inner')
        r['tier']=r.league.map(lambda l:tier_of(l,year)); r['region']=r.league.map(REGION)
        r['active']=(r.gp>=20)&r.league.notna()
        base=r[r.active].theta.mean()
        r['points']=((r.theta-base)*1000).round(0); r['points_sd']=(r.sd*1000).round(0)
        grp=r[r.active].groupby(['league','role']).theta.mean()
        r['vs_role_league_gold']=((r.theta-pd.Series([grp.get((l,ro),np.nan) for l,ro in zip(r.league,r.role)],index=r.index))*5000).round(0)
        # autres ligues (allers-retours) : écart au joueur moyen du même poste dans CETTE ligue
        also={pid:[[l,g_,t_,None if pd.isna(grp.get((l,r.role[pid]),np.nan)) else int(round((r.theta[pid]-grp.get((l,r.role[pid])))*5000))] for l,g_,t_ in a]
              for pid,a in r.also.dropna().items()}
        r=r.drop(columns=['also'])
        p,comps=competitions(year,info,excl)
        D=split_deltas(m,year,p,comps,s2)
        keep=r[r.gp>=10].index
        T=trajectories(year,r[r.active].index,levels)
        T[f'{g.date.max().date()}']=r.loc[r.active,'points']
        fl=flags(year,r.loc[keep]); car=career(year,keep)
        r.to_parquet(f'data/proc/season_{year}.parquet')
        # posterior P(n°1) par niveau et poste
        pidx=pd.Series(np.arange(len(m['u'])),index=m['u'].index); rng=np.random.default_rng(1); post={}
        for tr_ in ['Ligue majeure','Deuxième niveau','Troisième niveau']:
            post[tr_]={}
            for ro in ['Top','Jungle','Mid','ADC','Support']:
                sel=r[r.active&(r.role==ro)&(r.tier==tr_)]
                if len(sel)<2: continue
                ix=pidx[sel.index].values; Lc=np.linalg.cholesky(covT[np.ix_(ix,ix)]+1e-10*np.eye(len(ix)))
                dr=sel.theta.values[:,None]+Lc@rng.standard_normal((len(ix),4000))
                post[tr_][ro]=pd.Series(np.bincount(dr.argmax(0),minlength=len(ix))/4000,index=sel.index).sort_values(ascending=False).head(10).round(3).to_dict()
        json.dump(dict(year=year,base=float(base),s2=s2,league=(m['league']*1000).round(0).to_dict(),comps=comps,
                       deltas=D.round(4).to_dict('records'),teams=teams_view(m,year,info,excl,base),
                       traj_months=list(T.columns),traj={pid:[None if pd.isna(v) else int(v) for v in T.loc[pid].values] for pid in T.index},
                       flags=fl,career=car,post=post,also=also),open(f'data/proc/season_{year}.json','w'),ensure_ascii=False,default=float)
        print(year,'joueurs actifs',int(r.active.sum()),'compétitions',len(comps),'écarts',len(D),flush=True)

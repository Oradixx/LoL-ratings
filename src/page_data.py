"""Rassemble tous les chiffres affichés par la page (results/page_data.json)."""
import json, sys, pandas as pd, numpy as np
sys.path.insert(0,'src'); from leagues import MAJOR, LABEL
P='data/proc/'; J=lambda f: json.load(open(P+f))
D={}
# --- labo 2025 : phases v0.x
j0=J('journal_v0.json'); a=pd.read_parquet(P+'agg_v0.parquet')
D['v01']=j0['v01_top'][:6]; D['v01_corr']=j0['v01_corrW']
D['v02']=j0['v02_top'][:5]; D['v02_eff']=j0['v02_eff']
D['v02_nan']=int(a.v02.isna().sum()); D['v02_nan_jng']=int((a.v02.isna()&(a.role=='Jungle')).sum()); D['n15']=int(len(a))
t50=a.sort_values('v03',ascending=False).head(50).league.value_counts()
D['v03_top50']=t50.to_dict(); D['v03_top50_major']=int(t50.reindex(list(MAJOR)).fillna(0).sum())
D['pairs']={f'{x}|{y}':v for x,y,v in j0['pairs']}
v1=J('v1.json')
L=pd.Series(v1['league_gold'])/5   # theta*1000
L=L[[k for k in L.index if not k.startswith('seul') and k!='INTL_ONLY']]
r25=pd.read_parquet(P+'ratings_v1.parquet'); base25=r25[r25.gp>=20].theta.mean()*1000
D['leagues2025']=(L-base25).round(0).sort_values(ascending=False).to_dict()
cur0=J('current.json'); Lc=pd.Series(cur0['league'])
Lc=Lc[[k for k in Lc.index if not k.startswith('seul') and k!='INTL_ONLY']]
D['leagues_now']=(Lc-cur0['base']*1000).round(0).sort_values(ascending=False).to_dict()
D['league_check']=J('league_check.json')
D['prior_w']=v1['prior_w']; D['placebo']=v1['diag']['placebo_dev']['auc']
# --- le juge
D['final']=J('final_test.json'); D['rolling']=J('rolling.json'); D['ratones']=J('case_ratones.json'); D['reliab']=J('reliability.json')
# --- notes actuelles 2026
r=pd.read_parquet(P+'ratings_now.parquet').join(pd.read_parquet(P+'mv_stats.parquet'))
cur=J('current.json'); post=cur['p1']
top={}
for tr_ in ['Ligue majeure','Deuxième niveau','Troisième niveau']:
    top[tr_]={}
    for ro in ['Top','Jungle','Mid','ADC','Support']:
        t=r[r.active&(r.tier==tr_)&(r.role==ro)].sort_values('theta',ascending=False).head(8)
        top[tr_][ro]=[dict(name=x.player,team=x.team,league=x.league26,gp=int(x.gp26),pts=int(x.points),sd=int(x.points_sd),
                            u_gold=int(x.vs_role_league_gold),mv_p1=round(float(x.mv_p1),3),post_p1=round(post[tr_][ro].get(i,0.0),3)) for i,x in t.iterrows()]
D['top']=top
from leagues import REGION, DESC, tier
act=r[r.active]
PR=J('profiles.json'); PIDX={pid:i for i,pid in enumerate(PR['traj'])}
D['traj_months']=PR['months']; D['traj']=list(PR['traj'].values()); D['teams']=PR['teams']
D['players']=[dict(id=PIDX.get(x.Index),c=PR['info'].get(x.Index,{}).get('career',''),fl=PR['info'].get(x.Index,{}).get('flags',[]),l25=PR['info'].get(x.Index,{}).get('l25'),n=x.player,t=x.team,l=x.league26,g={'Ligue majeure':'M','Deuxième niveau':'2','Troisième niveau':'3'}.get(x.tier,'2'),r=x.role,gp=int(x.gp26),
                   p=int(x.points),sd=int(x.points_sd),u=int(x.vs_role_league_gold),m1=None if pd.isna(x.mv_p1) else round(float(x.mv_p1),3),
                   m5=None if pd.isna(x.mv_top5) else round(float(x.mv_top5),3)) for x in act.itertuples()]
lv=D.get('leagues_now',{})
D['league_meta']={l:dict(region=REGION.get(l,'Autre'),desc=DESC.get(l,''),tier={'Ligue majeure':'M','Deuxième niveau':'2','Troisième niveau':'3'}[tier(l)],n=int((act.league26==l).sum())) for l in sorted(act.league26.unique())}
D['em_check']=J('em_check.json')
D['n_active']=int(r.active.sum()); D['n_active_tier']=r[r.active].tier.value_counts().to_dict()
D['mv']=J('multiverse_summary.json')
D['scouting']=J('scouting.json'); D['underrated']=J('underrated.json')[:8]
D['counter']=J('bonus_counterpick.json'); D['tilt']=J('bonus_tilt.json')
G=pd.read_parquet(P+'teams.parquet'); D['games']={str(y):int(n) for y,n in G.groupby('src_year').gameid.nunique().items()}
D['leagues_2025_n']=int(G[G.src_year==2025].league.nunique())
Pl=pd.read_parquet(P+'players.parquet'); gg=Pl[(Pl.src_year==2026)&(Pl.teamname=='Gen.G')]
core=gg.groupby('playername').gameid.agg(set); D['geng_games']=len(set.intersection(*core.sort_values(key=lambda s:s.map(len),ascending=False).head(5)))

# le cas Exofeng (patch 1.2)
EXP='oe:player:22c335f178d8e1724b8d04831b1267a'
Pl26=Pl[(Pl.src_year==2026)&(Pl.league=='LFL')&(Pl.teamname=='Skillcamp')]
with_g=set(Pl26[Pl26.playerid==EXP].gameid); allg=Pl26.groupby('gameid').result.first()
old=pd.read_parquet(P+'ratings_now_v11.parquet') if __import__('os').path.exists(P+'ratings_now_v11.parquet') else r
adc=r[r.active&(r.league26=='LFL')&(r.role=='ADC')].sort_values('points',ascending=False)
D['exofeng']=dict(wr_with=float(allg[allg.index.isin(with_g)].mean()),wr_without=float(allg[~allg.index.isin(with_g)].mean()),
                  n_with=len(with_g),n_without=int((~allg.index.isin(with_g)).sum()),
                  **(lambda d:dict(n_recent=int(d[d.teamname=='Skillcamp'].gameid.nunique()),wr_recent=float(d[d.teamname=='Skillcamp'].result.mean()),n_before=int(d[d.teamname!='Skillcamp'].gameid.nunique()),wr_before=float(d[d.teamname!='Skillcamp'].result.mean())))(Pl[(Pl.playerid==EXP)&Pl.src_year.isin([2025,2026])]),
                  before=float(old.loc[EXP,'points']),after=float(r.loc[EXP,'points']),sd=float(r.loc[EXP,'points_sd']),rank_after=int(list(adc.index).index(EXP)+1) if EXP in adc.index else None)
json.dump(D,open('results/page_data.json','w'),ensure_ascii=False,default=float)
print('ok',len(json.dumps(D,default=float)))

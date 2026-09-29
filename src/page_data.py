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
for tier in ['Ligue majeure','Académie / ligue régionale']:
    top[tier]={}
    for ro in ['Top','Jungle','Mid','ADC','Support']:
        t=r[r.active&(r.tier==tier)&(r.role==ro)].sort_values('theta',ascending=False).head(8)
        top[tier][ro]=[dict(name=x.player,team=x.team,league=x.league26,gp=int(x.gp26),pts=int(x.points),sd=int(x.points_sd),
                            u_gold=int(x.vs_role_league_gold),mv_p1=round(float(x.mv_p1),3),post_p1=round(post[tier][ro].get(i,0.0),3)) for i,x in t.iterrows()]
D['top']=top
from leagues import REGION, DESC
act=r[r.active]
D['players']=[dict(n=x.player,t=x.team,l=x.league26,g='M' if x.tier=='Ligue majeure' else 'A',r=x.role,gp=int(x.gp26),
                   p=int(x.points),sd=int(x.points_sd),u=int(x.vs_role_league_gold),m1=None if pd.isna(x.mv_p1) else round(float(x.mv_p1),3),
                   m5=None if pd.isna(x.mv_top5) else round(float(x.mv_top5),3),f=int(x.form_delta)) for x in act.itertuples()]
lv=D.get('leagues_now',{})
D['league_meta']={l:dict(region=REGION.get(l,'Autre'),desc=DESC.get(l,''),tier='M' if l in MAJOR else 'A',n=int((act.league26==l).sum())) for l in sorted(act.league26.unique())}
D['em_check']=J('em_check.json')
D['n_active']=int(r.active.sum()); D['n_active_tier']=r[r.active].tier.value_counts().to_dict()
D['mv']=J('multiverse_summary.json')
D['scouting']=J('scouting.json'); D['underrated']=J('underrated.json')[:8]
D['counter']=J('bonus_counterpick.json'); D['tilt']=J('bonus_tilt.json')
G=pd.read_parquet(P+'teams.parquet'); D['games']={str(y):int(n) for y,n in G.groupby('src_year').gameid.nunique().items()}
D['leagues_2025_n']=int(G[G.src_year==2025].league.nunique())
Pl=pd.read_parquet(P+'players.parquet'); gg=Pl[(Pl.src_year==2026)&(Pl.teamname=='Gen.G')]
core=gg.groupby('playername').gameid.agg(set); D['geng_games']=len(set.intersection(*core.sort_values(key=lambda s:s.map(len),ascending=False).head(5)))
json.dump(D,open('results/page_data.json','w'),ensure_ascii=False,default=float)
print('ok',len(json.dumps(D,default=float)))

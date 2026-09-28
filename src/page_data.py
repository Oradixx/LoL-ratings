import json, pandas as pd, numpy as np
J=lambda f: json.load(open('results/'+f))
r=pd.read_csv('results/ratings_2025_v1.csv',index_col=0)
base=r[r.gp>=20].theta.mean()
r['pts']=((r.theta-base)*1000).round(0)
v1=J('v1.json'); mvs=J('multiverse_summary.json'); unc=J('uncertainty.json')
D={}
j0=J('journal_v0.json')
D['v01']=[{k:x[k] for k in ['name','team','league','role','GP','KDA','W']} for x in j0['v01_top'][:8]]
D['v01_corr']=round(j0['v01_corrW'],2)
D['v02']=[{k:x[k] for k in ['name','team','league','role','v02']} for x in j0['v02_top'][:6]]
D['v02_eff']=j0['v02_eff']
D['v03_leagues']=j0['v03_top50_leagues']
D['v03_top']={k:v[:3] for k,v in j0['v03_top'].items()}
D['pairs']=j0['pairs']; D['corrW']=j0['corrW']
lg=v1['league_gold']; lgs=pd.Series(lg)/5; lgs=((lgs/1000)*1000)  # league effect gold -> points: theta*1000 = gold/5
L=pd.Series({k:v/5 for k,v in lg.items() if k!='INTL_ONLY'})  # points (theta*1000)
L=(L-(base*1000)).round(0)
D['leagues']=L.sort_values(ascending=False).to_dict()
D['prior_w']=v1['prior_w']
top={}
roles=['Top','Jungle','Mid','ADC','Support']
for ro in roles:
    t=r[(r.role==ro)&(r.gp>=20)].sort_values('theta',ascending=False).head(8)
    top[ro]=[dict(name=a.name,team=a.team,league=a.home_league,gp=int(a.gp),pts=int(a.pts),u_gold=int(round(a.u_gold)),mv_p1=round(a.mv_p1,3),mv_top5=round(a.mv_top5,3)) for a in t.itertuples()]
D['top']=top
D['post_p1']=unc['p1']; D['mv_roles']=mvs['roles']; D['mv_auc']=mvs['auc']; D['mv_choices']=mvs['choice_effects']
D['final']={k:v for k,v in J('final_test.json').items()}
D['scouting']=J('scouting.json'); D['underrated']=J('underrated.json')[:10]
D['ratones']=J('case_ratones.json'); D['reliab']=J('reliability.json')
D['counter']=J('bonus_counterpick.json'); D['tilt']=J('bonus_tilt.json')
D['ids']=dict(games2025=9237,games2022=12549,games2026=1649,leagues2025=41,players2025=2902)
json.dump(D,open('results/page_data.json','w'),ensure_ascii=False,default=float)
print(json.dumps(D['leagues'],ensure_ascii=False)[:600]); print(D['top']['Mid'][:3]); print(len(json.dumps(D)))

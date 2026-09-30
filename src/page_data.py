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
old=pd.read_parquet(P+'ratings_now_v11.parquet')   # produit par src/v11_reference.py
adc=r[r.active&(r.league26=='LFL')&(r.role=='ADC')].sort_values('points',ascending=False)
D['exofeng']=dict(wr_with=float(allg[allg.index.isin(with_g)].mean()),wr_without=float(allg[~allg.index.isin(with_g)].mean()),
                  n_with=len(with_g),n_without=int((~allg.index.isin(with_g)).sum()),
                  **(lambda d:dict(n_recent=int(d[d.teamname=='Skillcamp'].gameid.nunique()),wr_recent=float(d[d.teamname=='Skillcamp'].result.mean()),n_before=int(d[d.teamname!='Skillcamp'].gameid.nunique()),wr_before=float(d[d.teamname!='Skillcamp'].result.mean())))(Pl[(Pl.playerid==EXP)&Pl.src_year.isin([2025,2026])]),
                  before=float(old.loc[EXP,'points']),after=float(r.loc[EXP,'points']),sd=float(r.loc[EXP,'points_sd']),rank_after=int(list(adc.index).index(EXP)+1) if EXP in adc.index else None)
json.dump(D,open('results/page_data.json','w'),ensure_ascii=False,default=float)
print('ok',len(json.dumps(D,default=float)))

# ---------- notes par saison et par compétition (explorateur) ----------
import numpy as np
def season_block(year):
    import numpy as np
    r=pd.read_parquet(P+f'season_{year}.parquet'); S=J(f'season_{year}.json')
    mv=pd.read_parquet(P+f'season_{year}_mv.parquet') if __import__('os').path.exists(P+f'season_{year}_mv.parquet') else pd.DataFrame()
    r=r.join(mv,how='left')
    keep=r[(r.gp>=10)&r.league.notna()].sort_values('points',ascending=False)
    tidx={pid:i for i,pid in enumerate(S['traj'])}
    TC={'Ligue majeure':'M','Deuxième niveau':'2','Troisième niveau':'3'}
    # part des games du joueur jouées avec exactement les mêmes quatre coéquipiers (roster « inséparable »)
    q=Pl[Pl.src_year==year].assign(pid=lambda d:d.playerid.fillna('name:'+d.playername.astype(str)))
    lu=q.groupby(['gameid','side']).pid.agg(lambda s:tuple(sorted(s)))
    qq=q.join(lu.rename('lu'),on=['gameid','side'])
    qq['mates']=[tuple(x for x in l if x!=me) for l,me in zip(qq.lu,qq.pid)]
    rs=qq.groupby('pid').mates.agg(lambda s:s.value_counts(normalize=True).iloc[0])
    players=[]; pix={}
    for pid,x in keep.iterrows():
        pix[pid]=len(players)
        players.append(dict(id=tidx.get(pid),n=x.player,t=x.team,l=x.league,g=TC.get(x.tier,'2'),r=x.role,gp=int(x.gp),a=bool(x.active),
            p=int(x.points),sd=int(x.points_sd),u=None if pd.isna(x.vs_role_league_gold) else int(x.vs_role_league_gold),
            m1=None if pd.isna(x.get('mv_p1',np.nan)) else round(float(x.mv_p1),3),m5=None if pd.isna(x.get('mv_top5',np.nan)) else round(float(x.mv_top5),3),
            fl=S['flags'].get(pid,[]),c=S['career'].get(pid,''),rs=round(float(rs.get(pid,0)),2),
            mg=None if pd.isna(x.get('main_games',np.nan)) else int(x.main_games),al=S.get('also',{}).get(pid)))
    comps={}; lm_keys=set(keep.league.unique())
    for c,meta in S['comps'].items(): comps[c]=dict(meta)
    dl={}
    for d in S['deltas']:
        if d['pid'] not in pix or d['comp'] not in comps: continue
        dl.setdefault(d['comp'],[]).append([pix[d['pid']],d['gp'],round(d['win'],3),round(d['kda'],2),round(d['d']*1000),round(d['dsd']*1000)])
    for c in list(comps):
        if c not in dl: comps.pop(c)
        else: comps[c]['n']=len(dl[c])
    from leagues import comp_labels; comp_labels(comps,lm_keys)
    lv={k:round(v-S['base']*1000) for k,v in S['league'].items() if not k.startswith('seul') and k!='INTL_ONLY'}
    lm={l:dict(region=REGION.get(l,'Autre'),desc=DESC.get(l,''),tier=TC[tier(l,year)],n=int((keep.league==l).sum())) for l in sorted(keep.league.unique())}
    return dict(players=players,comps=comps,deltas=dl,teams=S['teams'],traj_months=S['traj_months'],traj=list(S['traj'].values()),
                league_meta=lm,levels=lv,post=S['post'])
D['seasons']={str(y):season_block(y) for y in [2023,2024,2025,2026]}
# le récit de la page (meilleurs par poste, multivers, sous-cotés) suit lui aussi les notes de la saison 2026
r6=pd.read_parquet(P+'season_2026.parquet').join(pd.read_parquet(P+'season_2026_mv.parquet'),how='left'); S6=J('season_2026.json')
act6=r6[r6.active]
top={}; roles_mv={}
for tr_ in ['Ligue majeure','Deuxième niveau','Troisième niveau']:
    top[tr_]={}; roles_mv[tr_]={}
    for ro in ['Top','Jungle','Mid','ADC','Support']:
        t=act6[(act6.tier==tr_)&(act6.role==ro)]
        top[tr_][ro]=[dict(name=x.player,team=x.team,league=x.league,gp=int(x.gp),pts=int(x.points),sd=int(x.points_sd),u_gold=int(x.vs_role_league_gold),
                           mv_p1=round(float(x.mv_p1),3),post_p1=round(S6['post'].get(tr_,{}).get(ro,{}).get(i,0.0),3)) for i,x in t.sort_values('points',ascending=False).head(8).iterrows()]
        roles_mv[tr_][ro]=[dict(player=x.player,team=x.team,league26=x.league,mv_p1=round(float(x.mv_p1),3),mv_top5=round(float(x.mv_top5),3)) for i,x in t.sort_values(['mv_p1','mv_top5'],ascending=False).head(5).iterrows()]
D['top']=top; D['mv']['roles']=roles_mv
nm=act6[act6.tier!='Ligue majeure'].sort_values(['nm_p10','nm_p1'],ascending=False).head(8)
Pl2=Pl[Pl.src_year==2026].assign(pid=lambda d:d.playerid.fillna('name:'+d.playername.astype(str)))
def mates(pid):
    g=Pl2[Pl2.pid==pid][['gameid','side']]; return int(Pl2.merge(g,on=['gameid','side']).query('pid!=@pid').pid.nunique())
D['underrated']=[dict(player=x.player,team=x.team,league26=x.league,role=x.role,points=int(x.points),p1=round(float(x.nm_p1),3),p10=round(float(x.nm_p10),3),teammates=mates(i)) for i,x in nm.iterrows()]
# Exofeng dans les notes de saison
adc=act6[(act6.league=='LFL')&(act6.role=='ADC')].sort_values('points',ascending=False)
dd=pd.DataFrame(S6['deltas']); de=dd[(dd.pid==EXP)]
lfl=de[de.comp.str.startswith('LFL')]
D['exofeng_season']=dict(points=float(r6.loc[EXP,'points']),rank=int(list(adc.index).index(EXP)+1) if EXP in adc.index else None,n_adc=len(adc),
    comps=[dict(comp=x.comp,gp=int(x.gp),win=float(x.win),d=round(x.d*1000)) for x in de.itertuples()],
    lfl_note=float(r6.loc[EXP,'points']+lfl.d.iloc[0]*1000) if len(lfl) else None, lfl_comp=lfl.comp.iloc[0] if len(lfl) else None)
_tt=sorted(J('season_2026.json')['teams'],key=lambda t:-t['pts'])[:2]; D['team_top2']=[dict(team=t['team'],pts=t['pts']) for t in _tt]
D['geng_total']=int(gg.gameid.nunique())
D['season_only']=J('season_only_check.json'); D['halves_history']=J('halves_history_check.json'); D['exofeng_split']=J('exofeng_season_check.json'); D['split_validation']=J('split_validation.json'); D['league_prior_check']=J('league_prior_check.json')
D['role_sd']=float(act6[act6.tier=='Ligue majeure'].groupby('role').points.std().mean()); D['split_prior_sd']={y:float(np.sqrt(J(f'season_{y}.json')['s2']/1000)*1000) for y in ['2025','2026']}
D['season_mv_n']=int(__import__('pickle').load(open(P+'season_mv_raw.pkl','rb'))[2026].__len__())
def ex(name,team=None):
    x=act6[act6.player==name]
    if team: x=x[x.team==team]
    if not len(x): return None
    pid=x.index[0]; y=x.iloc[0]; e=dd[dd.pid==pid]
    same=act6[(act6.league==y.league)&(act6.role==y.role)].sort_values('points',ascending=False)
    return dict(name=name,team=y.team,league=y.league,role=y.role,points=int(y.points),sd=int(y.points_sd),rank=int(list(same.index).index(pid)+1),n_role=len(same),
                comps=[dict(comp=S6['comps'][c.comp]['label'] if c.comp in S6['comps'] else c.comp,gp=int(c.gp),win=float(c.win),d=int(round(c.d*1000)),note=int(round(y.points+c.d*1000)),
                            same_as_mates=bool((dd[(dd.comp==c.comp)&dd.pid.isin(act6.index[act6.team==y.team])].d.sub(c.d).abs()*1000).max()<2)) for c in e.sort_values('gp',ascending=False).itertuples()])
_m0=pd.Timestamp('2026-03-01'); _seen=set(Pl2[Pl2.date<_m0].pid); _mm=Pl2[(Pl2.date>=_m0)&(Pl2.date<pd.Timestamp('2026-04-01'))]
D['unseen_march']=float((~_mm.pid.isin(_seen)).mean())
D['split_examples']={k:ex(k) for k in ['Caliste','Exofeng']}
D['comp_dsd']=int(round(dd.dsd.median()*1000)); D['comp_d_abs']=int(round((dd.d.abs()*1000).median()))
# ---------- v1.4 : contrôles du raisonnement et pronostics Worlds figés ----------
D['data_until']=str(pd.read_parquet(P+'teams.parquet').date.max().date()); D['sim']=J('simulation_study.json'); D['transfer']=J('transfer_check.json'); D['champ']=J('champion_comfort.json'); D['calib']=J('calibration_check.json')
FZ=json.load(open('results/worlds2026/frozen_model.json'))
_rn=pd.read_parquet(P+'ratings_now.parquet'); _base=float(_rn[_rn.active].theta.mean())
_sc='results/worlds2026/score.json'
D['worlds']=dict(score=json.load(open(_sc)) if __import__('os').path.exists(_sc) else None,frozen_on=FZ['frozen_on'],data_until=FZ['data_until'],a=FZ['calibration']['a'],b=FZ['calibration']['b'],
    teams=[dict(team=t['team'],league=t['league'],region=t['region'],lineup=[t['lineup'][r] for r in ['Top','Jungle','Mid','ADC','Support']],
                s=round(t['strength'],4),pts=int(round((t['strength']/5-_base)*1000))) for t in FZ['teams']])
# ---------- v1.5 : 2023-2024, réplication ----------
D['replication']=J('replication.json'); D['history']=J('history_length.json'); D['scout_rep']=J('scouting_replication.json'); D['credit_roster']=J('credit_split_by_roster.json')
D['games_by_year']={str(y):int(n) for y,n in G.groupby('src_year').gameid.nunique().items()}
for k in ['players','traj','traj_months','teams','league_meta']: D.pop(k,None)
json.dump(D,open('results/page_data.json','w'),ensure_ascii=False,default=float)
print('seasons ok',len(json.dumps(D,default=float)))

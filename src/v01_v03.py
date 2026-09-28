import pandas as pd, numpy as np, json, sys
sys.path.insert(0,'src'); from common import *
p=load_players(2025); info=last_team(p)
MIN=15
agg=p.groupby('pid').agg(GP=('gameid','nunique'),K=('kills','sum'),D=('deaths','sum'),A=('assists','sum'),W=('result','mean'),
    DPM=('dpm','mean'),DMG=('damageshare','mean'),GD10=('golddiffat10','mean'),CSD10=('csdiffat10','mean'),XPD10=('xpdiffat10','mean'),
    KP=('kp','mean'),TDPG=('damagetotowers','mean'),FB=('firstblood','mean'),GOLD=('earnedgoldshare','mean'),CSPM=('cspm','mean'),
    WPM=('wpm','mean'),CWPM=('controlwardsbought',lambda s: np.nan),WCPM=('wcpm','mean'),STL=('monsterkillsenemyjungle','mean'))
# CWPM = control wards per minute
cw=p.assign(cwpm=p.controlwardsbought/p.minutes).groupby('pid').cwpm.mean(); agg['CWPM']=cw
agg['KDA']=(agg.K+agg.A)/agg.D.clip(lower=1)
agg=agg.join(info); agg=agg[agg.GP>=MIN]
print('players with >=%d games:'%MIN,len(agg))
res={}
# v0.1 KDA
t=agg.sort_values('KDA',ascending=False).head(10)[['name','team','league','role','GP','KDA','W']]
print('\n=== v0.1 KDA top10'); print(t.round(2).to_string())
print('corr(KDA, team winrate) =',round(agg[['KDA','W']].corr().iloc[0,1],3))
res['v01_top']=t.round(2).reset_index(drop=True).to_dict('records'); res['v01_corrW']=agg[['KDA','W']].corr().iloc[0,1]
# v0.2 = LoL Ratings 2.0 (weights copied from Clement's notebook), z-scores over ALL roles
W2={'Top':{'DPM':.20,'DMG':.15,'GD10':.15,'CSD10':.10,'XPD10':.10,'KP':.15,'KDA':.10,'TDPG':.05},
 'Jungle':{'KP':.25,'GD10':.20,'XPD10':.10,'FB':.15,'DPM':.10,'KDA':.10,'STL':.05,'GOLD':.05},
 'Mid':{'DPM':.25,'DMG':.20,'GD10':.15,'CSD10':.10,'KP':.15,'KDA':.10,'FB':.05},
 'ADC':{'DPM':.25,'DMG':.25,'KDA':.15,'CSPM':.15,'CSD10':.10,'GD10':.10},
 'Support':{'KP':.30,'WPM':.15,'CWPM':.15,'WCPM':.10,'KDA':.15,'FB':.10,'GD10':.05}}
stats=sorted({s for w in W2.values() for s in w})
zg=(agg[stats]-agg[stats].mean())/agg[stats].std()
agg['v02']=[sum(zg.loc[i,s]*w for s,w in W2[r].items()) for i,r in zip(agg.index,agg.role)]
print('\nv0.2: players with NaN score (missing GD10 etc, i.e. LPL):',agg.v02.isna().sum(), agg[agg.v02.isna()].league.value_counts().to_dict())
t=agg.sort_values('v02',ascending=False).head(10)[['name','team','league','role','GP','v02','W']]
print('=== v0.2 top10 (LoL Ratings 2.0 worldwide)'); print(t.round(2).to_string())
print('mean v0.2 by role:',agg.groupby('role').v02.mean().round(2).to_dict())
# effective weights: global std vs within-role std
eff={}
for r,w in W2.items():
    sub=agg[agg.role==r]
    e={s:w[s]*sub[s].std()/agg[s].std() for s in w}; tot=sum(e.values()); eff[r]={s:round(v/tot,3) for s,v in e.items()}
print('effective weights (share of within-role variance actually driven):'); 
for r in eff: print(r, {s:(W2[r][s],eff[r][s]) for s in W2[r]})
res['v02_top']=t.round(2).reset_index(drop=True).to_dict('records'); res['v02_eff']=eff; res['v02_nan']=int(agg.v02.isna().sum())
# v0.3: z-score within role, fill missing with role mean (0)
zr=agg.groupby('role')[stats].transform(lambda s:(s-s.mean())/s.std()).fillna(0)
agg['v03']=[sum(zr.loc[i,s]*w for s,w in W2[r].items()) for i,r in zip(agg.index,agg.role)]
print('\n=== v0.3 top per role (within-role z)')
for r in W2: print(r, agg[agg.role==r].sort_values('v03',ascending=False).head(5)[['name','team','league','v03','W']].round(2).values.tolist())
c=agg[['v03','W']].corr().iloc[0,1]; print('corr(v0.3, player winrate)=',round(c,3))
# league composition of top 50
print('leagues in top 50 v0.3:',agg.sort_values('v03',ascending=False).head(50).league.value_counts().head(8).to_dict())
res['v03_corrW']=c; res['v03_top50_leagues']=agg.sort_values('v03',ascending=False).head(50).league.value_counts().head(8).to_dict()
res['v03_top']={r:agg[agg.role==r].sort_values('v03',ascending=False).head(5)[['name','team','league','v03','W']].round(2).to_dict('records') for r in W2}
# correlation between stats (voter fraud)
cm=zr[stats].corr()
pairs=[(a,b,round(cm.loc[a,b],2)) for i,a in enumerate(stats) for b in stats[i+1:] if abs(cm.loc[a,b])>0.6]
print('highly correlated stat pairs:',pairs)
# how much each stat is just 'winning'
print('corr stat vs winrate (within role z):',{s:round(np.corrcoef(zr[s],agg.W)[0,1],2) for s in stats})
res['pairs']=pairs; res['corrW']={s:round(np.corrcoef(zr[s],agg.W)[0,1],2) for s in stats}
agg.to_parquet('data/proc/agg_v0.parquet')
json.dump(res,open('data/proc/journal_v0.json','w'),default=str,indent=1,ensure_ascii=False)

import pandas as pd, numpy as np, json
import statsmodels.formula.api as smf
m=pd.read_parquet('data/proc/picks_lane.parquet')
g=pd.read_parquet('data/proc/games_elo.parquet')[['gameid','elo_b','elo_r']]
m=m.merge(g,on='gameid',how='left')
m['elo_diff']=np.where(m.side=='Blue',m.elo_b-m.elo_r,m.elo_r-m.elo_b)/100
m['blue']=(m.side=='Blue').astype(int)
# champion strength: mean GD15 of champion in role-year (leave-in; crude)
m['champ_gd']=m.groupby(['src_year','position','champion']).golddiffat15.transform('mean')
out={}
for pos in ['top','jng','mid','bot','sup']:
    d=m[(m.position==pos)&m.golddiffat15.notna()]
    r0=smf.ols('golddiffat15 ~ counter',d).fit()
    r1=smf.ols('golddiffat15 ~ counter + blue + elo_diff + C(src_year)',d).fit(cov_type='cluster',cov_kwds={'groups':d.gameid.astype('category').cat.codes})
    r2=smf.ols('golddiffat15 ~ counter + blue + elo_diff + champ_gd + C(src_year)',d).fit(cov_type='cluster',cov_kwds={'groups':d.gameid.astype('category').cat.codes})
    out[pos]=dict(naive=round(r0.params['counter'],1),ctrl=round(r1.params['counter'],1),ctrl_se=round(r1.bse['counter'],1),
                  champ=round(r2.params['counter'],1),champ_se=round(r2.bse['counter'],1),n=int(len(d)))
    print(pos,out[pos])
json.dump(out,open('data/proc/bonus_counterpick.json','w'),indent=1)

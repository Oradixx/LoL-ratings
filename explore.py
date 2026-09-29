"""Look up players in the LoL Ratings 3.0 results (only needs pandas).

python explore.py leaderboard --role Mid --top 10                 # major leagues, 2026
python explore.py leaderboard --role Mid --tier academy           # academies & regional leagues
python explore.py player Chovy
python explore.py compare Chovy Faker Caps
python explore.py league LEC --top 10
add --year 2025 to any command for the 2025 ratings
"""
import argparse, pandas as pd
ap=argparse.ArgumentParser(); ap.add_argument('--year',type=int,default=2026,choices=[2025,2026])
sp=ap.add_subparsers(dest='cmd',required=True)
a=sp.add_parser('leaderboard'); a.add_argument('--role'); a.add_argument('--top',type=int,default=10); a.add_argument('--tier',choices=['major','academy'],default='major')
b=sp.add_parser('player'); b.add_argument('name')
c=sp.add_parser('compare'); c.add_argument('names',nargs='+')
d=sp.add_parser('league'); d.add_argument('league'); d.add_argument('--top',type=int,default=10)
x=ap.parse_args()
R=pd.read_csv(f'results/ratings_{x.year}.csv',index_col=0)
TIER={'major':'Ligue majeure','academy':'Académie / ligue régionale'}
cols=[c for c in ['player','team','league','role',f'games_{x.year}','points','points_sd','vs_role_in_league_gold','mv_median_rank','mv_p1','mv_top5'] if c in R.columns]
def show(d): print(d[cols].to_string(index=False) if len(d) else 'no match')
if x.cmd=='leaderboard':
    d=R[R.tier==TIER[x.tier]]; d=d[d.role==x.role] if x.role else d
    if x.year==2025: d=d[d.games_2025>=20]
    show(d.sort_values('points',ascending=False).head(x.top))
elif x.cmd=='player': show(R[R.player.str.lower()==x.name.lower()])
elif x.cmd=='compare': show(R[R.player.str.lower().isin([n.lower() for n in x.names])].sort_values('points',ascending=False))
elif x.cmd=='league': show(R[R.league==x.league].sort_values('points',ascending=False).head(x.top))

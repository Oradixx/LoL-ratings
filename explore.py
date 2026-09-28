"""Look up players in the LoL Ratings 3.0 results (no install needed beyond pandas).

python explore.py leaderboard --role Mid --top 10
python explore.py player Chovy
python explore.py compare Chovy Faker Caps
python explore.py league LEC --top 10
"""
import argparse, pandas as pd
R=pd.read_csv('results/ratings_2025_v1.csv',index_col=0)
base=R[R.gp>=20].theta.mean()
R['points']=((R.theta-base)*1000).round(0).astype(int)
COLS=['name','team','home_league','role','gp','points','u_gold','mv_median_rank','mv_p1','mv_top5']
def show(d): print(d[COLS].rename(columns={'u_gold':'vs_role_in_league_gold','mv_median_rank':'multiverse_median_rank','mv_p1':'multiverse_%_no1','mv_top5':'multiverse_%_top5'}).round(2).to_string(index=False))
ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
a=sp.add_parser('leaderboard'); a.add_argument('--role'); a.add_argument('--top',type=int,default=10); a.add_argument('--min-games',type=int,default=20)
b=sp.add_parser('player'); b.add_argument('name')
c=sp.add_parser('compare'); c.add_argument('names',nargs='+')
d=sp.add_parser('league'); d.add_argument('league'); d.add_argument('--top',type=int,default=10)
x=ap.parse_args()
if x.cmd=='leaderboard':
    d=R[R.gp>=x.min_games]; d=d[d.role==x.role] if x.role else d; show(d.sort_values('theta',ascending=False).head(x.top))
elif x.cmd=='player': show(R[R.name.str.lower()==x.name.lower()])
elif x.cmd=='compare': show(R[R.name.str.lower().isin([n.lower() for n in x.names])].sort_values('theta',ascending=False))
elif x.cmd=='league': show(R[(R.home_league==x.league)&(R.gp>=20)].sort_values('theta',ascending=False).head(x.top))

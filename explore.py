"""Look up players in the LoL Ratings 3.0 results (only needs pandas).

python explore.py leaderboard --role Mid --top 10                 # major leagues, 2026
python explore.py leaderboard --role Mid --tier tier2 --region EMEA     # 2nd tier (academies, ERLs...), Europe
python explore.py player Chovy
python explore.py compare Chovy Faker Caps
python explore.py league LEC --top 10
python explore.py comps --league LEC                              # competitions / splits of the season
python explore.py comp "LEC Summer · saison régulière" --role ADC  # rating on one competition
add --year 2023, 2024 or 2025 to any command for that season (ratings use one season only)
"""
import argparse, pandas as pd
ap=argparse.ArgumentParser(); ap.add_argument('--year',type=int,default=2026,choices=[2023,2024,2025,2026])
sp=ap.add_subparsers(dest='cmd',required=True)
a=sp.add_parser('leaderboard'); a.add_argument('--role'); a.add_argument('--top',type=int,default=10); a.add_argument('--tier',choices=['major','tier2','tier3'],default='major')
a.add_argument('--region',help='2026 only: Corée, Chine, EMEA, "Amérique du Nord", "Brésil & Amérique latine", Asie-Pacifique'); a.add_argument('--min-games',type=int,default=20)
b=sp.add_parser('player'); b.add_argument('name')
c=sp.add_parser('compare'); c.add_argument('names',nargs='+')
d=sp.add_parser('league'); d.add_argument('league'); d.add_argument('--top',type=int,default=10)
e=sp.add_parser('comps'); e.add_argument('--league')
f=sp.add_parser('comp'); f.add_argument('competition'); f.add_argument('--role'); f.add_argument('--top',type=int,default=15); f.add_argument('--min-games',type=int,default=5)
x=ap.parse_args()
R=pd.read_csv(f'results/ratings_{x.year}.csv',index_col=0); C=pd.read_csv(f'results/competitions_{x.year}.csv')
TIER={'major':'Ligue majeure','tier2':'Deuxième niveau','tier3':'Troisième niveau'}
cols=[c for c in ['player','team','league','role',f'games_{x.year}','points','points_sd','vs_role_in_league_gold','mv_p1','mv_top5'] if c in R.columns]
def show(d): print(d[cols].to_string(index=False) if len(d) else 'no match')
if x.cmd=='leaderboard':
    d=R[R.tier==TIER[x.tier]]; d=d[d.role==x.role] if x.role else d
    if x.region and 'region' in d: d=d[d.region.str.lower()==x.region.lower()]
    d=d[d[f'games_{x.year}']>=x.min_games]
    show(d.sort_values('points',ascending=False).head(x.top))
elif x.cmd=='player':
    show(R[R.player.str.lower()==x.name.lower()])
    c=C[C.player.str.lower()==x.name.lower()]
    if len(c): print(); print(c[['competition','games','win_rate','kda','delta','competition_points']].sort_values('games',ascending=False).to_string(index=False))
elif x.cmd=='comps':
    c=C[C.league==x.league] if x.league else C
    print(c.groupby('competition').agg(players=('player','size'),most_games=('games','max')).sort_values(['players','most_games'],ascending=False).to_string())
elif x.cmd=='comp':
    c=C[(C.competition.str.lower()==x.competition.lower())&(C.games>=x.min_games)]
    if x.role: c=c[c.role==x.role]
    print(c.sort_values('competition_points',ascending=False).head(x.top)[['player','team','league','role','games','win_rate','kda','season_points','delta','competition_points']].to_string(index=False) if len(c) else 'no match (see: python explore.py comps)')
elif x.cmd=='compare': show(R[R.player.str.lower().isin([n.lower() for n in x.names])].sort_values('points',ascending=False))
elif x.cmd=='league': show(R[R.league==x.league].sort_values('points',ascending=False).head(x.top))

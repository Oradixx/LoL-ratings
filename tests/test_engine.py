"""Tests of the rating engine on synthetic seasons where the true ratings are known (no data files needed)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0,'src')
from engine import fit, BOX_BASE, BOX_LANE

ROLES=['Top','Jungle','Mid','ADC','Support']
def season(seed=0,n_teams=8,levels={'AAA':0.4,'BBB':0.0,'CCC':-0.4},stable_team=None):
    """3 leagues, double round robin x3 inside each league, an international cup between the top 4 of each league,
    and a few mid-season transfers between leagues. Returns players rows, games, true theta."""
    rng=np.random.default_rng(seed); rows=[]; games=[]; true={}; roster={}
    for lg,lv in levels.items():
        for t in range(n_teams):
            team=f'{lg}-{t}'; roster[team]=[]
            for r in ROLES:
                pid=f'{team}-{r}'; true[pid]=lv+rng.normal(0,0.15); roster[team].append(pid)
    # transfers after half the season: one player per league moves to the next league
    moves={f'AAA-7-Mid':'BBB-0',f'BBB-7-Mid':'CCC-0',f'CCC-7-Mid':'AAA-0'}
    def lineup(team,half):
        lu=list(roster[team])
        if half:
            for pid,dest in moves.items():
                if pid in lu: lu[ROLES.index('Mid')]=roster[dest][ROLES.index('Mid')]   # swap
                if dest==team: lu[ROLES.index('Mid')]=pid
        return lu
    gid=0; start=pd.Timestamp('2026-01-15')
    sched=[]
    for lg in levels:
        teams=[f'{lg}-{t}' for t in range(n_teams)]
        for rep in range(6):
            for i in range(n_teams):
                for j in range(i+1,n_teams): sched.append((lg,teams[i],teams[j],rep/6))
    for lg in levels: pass
    cup=[f'{lg}-{t}' for lg in levels for t in range(4)]
    for i in range(len(cup)):
        for j in range(i+1,len(cup)):
            if cup[i][:3]!=cup[j][:3]: sched.append(('CUP',cup[i],cup[j],0.45))
    rng.shuffle(sched)
    for lg,a,b,frac in sched:
        half=frac>=0.5; date=start+pd.Timedelta(days=int(frac*200)+int(rng.integers(0,30)))
        if rng.random()<0.5: a,b=b,a
        la,lb=lineup(a,half),lineup(b,half)
        y=sum(true[x] for x in la)-sum(true[x] for x in lb)+0.05+rng.normal(0,1.7)
        g=f'g{gid}'; gid+=1
        games.append(dict(gameid=g,date=date,league=lg,year=2026,bwin=float(y>0),blue_team=a,red_team=b,golddiff_end=y*5000,minutes=32.0))
        for side,team,lu in [('Blue',a,la),('Red',b,lb)]:
            for r,pid in zip(ROLES,lu):
                st={s:rng.normal(0,1)+0.8*(true[pid]-levels[pid[:3]])/0.15*(s in ('dpm','earned gpm','golddiffat15')) for s in BOX_BASE+BOX_LANE}
                rows.append(dict(gameid=g,side=side,pid=pid,playername=pid,playerid=pid,teamname=team,teamid=team,league=lg,date=date,role=r,
                                 position=r.lower(),champion=f'c{int(rng.integers(0,40))}',**st))
    p=pd.DataFrame(rows); g=pd.DataFrame(games).set_index('gameid')
    return p,g,pd.Series(true)

CFG=dict(lam=50,lamL=3,target='gold',role_prior=True,prior_alpha=200,home='mix')

def test_recovers_players_and_league_order():
    p,g,true=season(1)
    m=fit(p,g,CFG)
    th=m['theta'].reindex(true.index)
    assert th.corr(true)>0.85
    L=m['league']
    assert L['AAA']>L['BBB']>L['CCC']

def test_box_prior_learns_the_informative_stats():
    p,g,true=season(2)
    m=fit(p,g,CFG); W=m['prior_w']
    # dpm is informative in the synthetic world, wpm is pure noise
    assert W.loc['dpm'].mean()>abs(W.loc['wpm']).mean()

def test_inseparable_teammates_are_not_separated_by_results():
    # without the box-score prior, five players who always play together get (almost) the same individual deviation
    p,g,true=season(3)
    m=fit(p,g,dict(CFG,prior=False))
    u=m['u']; team=[f'AAA-3-{r}' for r in ROLES]
    assert u[team].std()<0.02

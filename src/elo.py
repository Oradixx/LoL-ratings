import pandas as pd, numpy as np
def team_games(T):
    """one row per game: blue team, red team, blue win"""
    b=T[T.side=='Blue'][['gameid','date','league','game','teamname','teamid','result','src_year','playoffs','patch']].rename(columns={'teamname':'blue','teamid':'blue_id','result':'bwin'})
    r=T[T.side=='Red'][['gameid','teamname','teamid']].rename(columns={'teamname':'red','teamid':'red_id'})
    g=b.merge(r,on='gameid').sort_values('date').reset_index(drop=True)
    g['blue_k']=g.blue_id.fillna(g.blue); g['red_k']=g.red_id.fillna(g.red)
    return g
def run_elo(g,K=24,side_adv=0.0,init=1500):
    R={}; pre_b=[];pre_r=[];pexp=[]
    for row in g.itertuples(index=False):
        rb=R.get(row.blue_k,init); rr=R.get(row.red_k,init)
        e=1/(1+10**((rr-rb-side_adv)/400))
        pre_b.append(rb);pre_r.append(rr);pexp.append(e)
        s=row.bwin
        R[row.blue_k]=rb+K*(s-e); R[row.red_k]=rr-K*(s-e)
    g=g.copy(); g['elo_b']=pre_b; g['elo_r']=pre_r; g['p_elo']=pexp
    return g,R

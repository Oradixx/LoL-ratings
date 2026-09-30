"""Qui jouait déjà ensemble la saison d'avant ? Robuste aux changements de nom ou d'identifiant d'équipe.
Pour chaque équipe d'une game : taille du plus grand groupe de ses joueurs qui étaient coéquipiers
(même équipe principale) la saison précédente. 5 = roster inchangé, 1 = roster entièrement nouveau."""
import numpy as np, pandas as pd
def core_size(P,g_prev,g_next):
    p0=P[P.gameid.isin(g_prev.index)&(P.pid!='anon')]
    team0=p0.assign(t=p0.teamid.fillna(p0.teamname)).groupby('pid').t.agg(lambda s:s.mode().iloc[0])
    q=P[P.gameid.isin(g_next.index)&(P.pid!='anon')][['gameid','side','pid']].copy()
    q['t0']=q.pid.map(team0)
    def largest(s):
        s=s.dropna(); return int(s.value_counts().iloc[0]) if len(s) else 0
    return q.groupby(['gameid','side']).t0.agg(largest).unstack()     # colonnes Blue / Red

"""Sanity checks on the published results (run: python -m pytest tests/)."""
import json, pandas as pd
R26=pd.read_csv('results/ratings_2026.csv',index_col=0)
R25=pd.read_csv('results/ratings_2025.csv',index_col=0)
ROLL=json.load(open('results/rolling.json'))['total']
F=json.load(open('results/final_test.json'))

def test_ratings_shape():
    assert len(R26)>1000 and R26.points.notna().all() and len(R25)>2500

def test_tiers_are_separated():
    assert set(R26.tier)=={'Ligue majeure','Académie / ligue régionale'}
    majors={'LCK','LPL','LEC','LCS','CBLOL','LCP'}
    assert set(R26[R26.tier=='Ligue majeure'].league)<=majors
    assert not set(R26[R26.tier!='Ligue majeure'].league)&majors

def test_league_names_are_harmonised():
    for bad in ['LTA N','LTA S','LVP SL']:
        assert bad not in set(R26.league)|set(R25.league)

def test_v11_beats_online_elo_in_2026():
    v=ROLL['v1.1 ré-entraînée chaque mois']
    for k in ['Elo équipe (mis à jour à chaque game)','Elo joueurs (mis à jour à chaque game)','KDA à date']:
        assert v['auc']>ROLL[k]['auc']

def test_v1_beats_baselines_after_offseason():
    v1=F['v1.0 LoL Ratings 3.0']['auc']
    for k in ['Elo équipe','Elo porté par les joueurs','v0.1 KDA']:
        assert v1>F[k]['auc']

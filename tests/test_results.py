"""Sanity checks on the published results (run: python -m pytest tests/)."""
import json, pandas as pd
R26=pd.read_csv('results/ratings_2026.csv',index_col=0)
R25=pd.read_csv('results/ratings_2025.csv',index_col=0)
ROLL=json.load(open('results/rolling.json'))['total']
F=json.load(open('results/final_test.json'))

def test_ratings_shape():
    assert len(R26)>1000 and R26.points.notna().all() and len(R25)>1000

def test_tiers_are_separated():
    assert set(R26.tier)=={'Ligue majeure','Deuxième niveau','Troisième niveau'}
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

C26=pd.read_csv('results/competitions_2026.csv')
SV=json.load(open('results/split_validation.json'))

def test_competition_notes_are_season_plus_delta():
    assert ((C26.competition_points-C26.season_points-C26.delta).abs()<1e-6).all()
    # games-weighted mean delta per player close to zero: a competition shifts a player around his season rating
    w=C26.assign(wd=C26.delta*C26.games).groupby('player').agg(wd=('wd','sum'),g=('games','sum'))
    assert abs((w.wd/w.g).mean())<25

def test_published_split_setting_helps_out_of_sample():
    # the setting used for the page (λ=1000, no stats prior, chosen on 2025) must beat "no delta" on held-out games, both seasons
    for y in ['2025','2026']:
        assert SV[y]['résultats seuls, λ=1000']['mse_gain']>0
        assert SV[y]['stats seules ×1']['mse_gain']<0

def test_v14_checks():
    cal=json.load(open('results/calibration_check.json'))['games']
    assert cal['v1.2']['ece']<0.03 and cal['v1.2']['logloss']<cal['Elo équipe']['logloss']
    tr=json.load(open('results/transfer_check.json'))['_prior_gain']
    assert tr['lo']>0                      # the box-score prior helps on transfers (95 % interval above 0)
    sim=json.load(open('results/simulation_study.json'))
    for s in ['sigma_100','sigma_200']:
        c=(sim[s]['cov1_stable']+sim[s]['cov1_mobile'])/2
        assert 0.55<c<0.95                 # the ± are roughly honest
        assert sim[s]['pair_corr_stable']<sim[s]['pair_corr_other']   # inseparable rosters are harder, as expected

def test_worlds_predictions_are_frozen():
    F=json.load(open('results/worlds2026/frozen_model.json'))
    assert F['data_until']<='2026-09-28' and len(F['teams'])>=40 and len(F['theta'])>1000

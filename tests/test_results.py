"""Sanity checks on the published results (run: python -m pytest tests/)."""
import json, pandas as pd
R=pd.read_csv('results/ratings_2025_v1.csv',index_col=0)
F=json.load(open('results/final_test.json'))
def test_ratings_shape():
    assert len(R)>2500 and R.theta.notna().all()
def test_v1_beats_baselines_on_feb_2026():
    v1=F['v1.0 LoL Ratings 3.0']['auc']
    for k in ['Elo équipe','Elo porté par les joueurs','v0.1 KDA','v0.3 LoL Ratings 2.0 (corrigé par rôle)']:
        assert v1>F[k]['auc']
def test_gen_g_problem_is_visible():
    top=R[R.gp>=20].sort_values('theta',ascending=False).groupby('role').head(1)
    assert (top.team=='Gen.G').sum()>=4
def test_placebo_is_random():
    v=json.load(open('results/v1.json'))['diag']['placebo_dev']['auc']
    assert 0.45<v<0.56

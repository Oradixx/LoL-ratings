# LoL Ratings 3.0 — Who is the best League of Legends player in the world?

A player rating for pro League of Legends, built one version at a time: every time the model gave an answer, I looked for why it was wrong and shipped a patch. At the end, a judge I could not influence graded it: the games of 2026.

Method inspired by [B.A.S.I.C.](https://github.com/HQEye/basic-most-average-nba-player) (the "most average NBA player" video): build up in phases, then run hundreds of reasonable versions of the model instead of picking one. This project adds what that one could not have: an out-of-sample test.

Data: [Oracle's Elixir](https://oracleselixir.com/tools/downloads) match data — 9,237 pro games from 41 leagues in 2025 (training), January–February 2026 (validation and test), plus 2022 for the draft analysis.

## The result

**Final exam — February 2026** (959 games). Every model is trained on 2025 only, calibrated on January 2026, scored once on February. The off-season reshuffled rosters in between.

| Model | AUC | Games called correctly |
|---|---:|---:|
| Coin flip (+ blue side) | 0.500 | 51.2 % |
| Team Elo (2025) | 0.565 | 53.0 % |
| Elo carried by each player | 0.620 | 58.8 % |
| v0.1 KDA | 0.637 | 59.6 % |
| v0.3 LoL Ratings 2.0, role-corrected | 0.635 | 59.6 % |
| v0.4 Raw RAPM | 0.641 | 59.5 % |
| v0.5 RAPM + league strength | 0.690 | 62.3 % |
| Average of 600 model versions | 0.694 | 61.9 % |
| **v1.0 LoL Ratings 3.0** | **0.697** | **63.5 %** |

**Best player per role (2025)** — share of 600 model versions where the player is #1:

| Role | Player | #1 in the multiverse | #1 under statistical uncertainty |
|---|---|---:|---:|
| Top | Kiin (Gen.G) | 92 % | 19 % |
| Jungle | Canyon (Gen.G) | 94 % | 21 % |
| Mid | Chovy (Gen.G) | 95 % | 24 % |
| ADC | Ruler (Gen.G) | 100 % | 21 % |
| Support | Duro (Gen.G) | 87 % | 18 % |

Five #1s, five Gen.G players. They played the whole year together, so no version of the model can tell Chovy apart from Gen.G: the multiverse protects against arbitrary modelling choices, not against a blind spot shared by every universe. Honest answer: in 2025 the best player in the world is called Gen.G.

**Where the model does separate players from teams — scouting.** Among 1,149 players outside major leagues in 2025, 50 % of the model's top 20 were playing in a major league in early 2026 (base rate 6.4 %). AUC for predicting promotions: 0.80 (KDA: 0.71). Most underrated player: **Guti** (mid, T1 Esports Academy), #1 among non-major players in 72 % of the 600 versions and still in the academy in 2026.

**Bonus probes.** Counterpicking your lane opponent is worth about +40 gold at 15 minutes in top lane and nothing measurable elsewhere (≈16,850 lane matchups per role, controlling for side, team Elo and champion strength). The "tilt" after losing game 1 of a series disappears under a placebo: the next meeting weeks later shows an even bigger gap, so it is Elo under-reacting, not tilt.

## How it works

| Version | Idea | What went wrong |
|---|---|---|
| 0.1 | KDA | Rekkles in NLC is the best player in the world. KDA correlates 0.67 with win rate. |
| 0.2 | LoL Ratings 2.0 (hand weights, z-scores) applied worldwide | z-scores computed across all roles silently change the weights; one missing stat voids the score (383 unrated players). |
| 0.3 | z-score within role | Top 50 = 9 LJL players, 0 LCK/LPL. Correlated stats vote twice. |
| 0.4 | RAPM: each game is an equation, `final gold diff = side + Σ blue players − Σ red players`, ridge regression | Rosters rarely change (median 2 lineups per team). |
| 0.5 | League strength carried by the player (home league), linked by international events and players moving leagues | First attempt put the LFL above the LCK (league effect attached to teams, too cheap). |
| 0.6 | Box-score prior: role-specific weights learned from the RAPM impact, not from winning; champion-adjusted, league-relative stats | — |
| 0.7 | Target = final gold difference instead of win/loss | — |
| 0.8 | Tested and found useless: champion adjustment (for prediction), time decay, 15-min lane stats | — |

The final model is a ridge regression with an empirical-Bayes prior:
`rating = home league level + individual deviation`, individual deviation ~ N(box-score prior, 1/λ).
Config: `lam=50, lamL=3, target='gold', role_prior=True, prior_alpha=200` (`src/engine.py`).

Checks against fooling myself: shuffled 2025 outcomes give AUC 0.51 on January 2026 (placebo); split-half stability 0.72 (0.79 within a league); February 2026 was looked at once at the start for baselines, all tuning was done on January.

## Look up a player

```bash
python explore.py leaderboard --role Mid --top 10
python explore.py player Chovy
python explore.py compare Caps Chovy Faker
python explore.py league LEC --top 10
```

Or open `results/ratings_2025_v1.csv`.

## Run it yourself

```bash
pip install -r requirements.txt
bash scripts/get_data.sh     # ~170 MB of CSVs
bash run_all.sh              # ~20 min on a 2-core laptop, the multiverse is most of it
python -m pytest tests/
```

## Files

```
src/engine.py            the model (RAPM + league levels + learned box-score prior)
src/evaluate.py          train/dev/test splits, Elo and KDA baselines, scoring
src/v01_v03.py           phases 0.1 - 0.3
src/multiverse.py        600 reasonable versions of the model
src/final_test.py        the February 2026 exam
src/scouting.py          did the model see 2026 promotions coming?
src/bonus_*.py           counterpick value, tilt placebo
src/experiments/         tuning runs (on January 2026 only)
results/                 ratings CSV, phase leaderboards, every number on the page (JSON)
page/lol-ratings-3.html  the write-up (French)
explore.py               player lookup
tests/                   sanity checks on the results
```

## Limits

- A player who never played without his four teammates cannot be separated from them (Gen.G, and to a lesser degree academy rosters like T1 Academy).
- No 2024 file was available; the LPL has no 10/15-minute stats.
- Gaps between leagues that never meet are extrapolated; "points" are a linear scale.
- Oracle's Elixir data has occasional errors; 2.6 % of player rows have no player id.

## Credits

Data: Oracle's Elixir (Tim Sevenhuysen). Method inspiration: HQEye's B.A.S.I.C. Built with Claude (Anthropic) as a pair-programming and analysis partner, starting from my LoL Ratings 2.0 notebook.

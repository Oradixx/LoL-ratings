# LoL Ratings 3.0 — Who is the best League of Legends player in the world?

A player rating for pro League of Legends, built one version at a time on the 2025 season: every time the model gave an answer, I looked for why it was wrong and shipped a patch. Then a judge I could not influence graded it: the whole 2026 season.

Method inspired by [B.A.S.I.C.](https://github.com/HQEye/basic-most-average-nba-player) (the "most average NBA player" video): build up in phases, then run hundreds of reasonable versions of the model instead of picking one. This project adds what that one could not have: an out-of-sample test.

Data: [Oracle's Elixir](https://oracleselixir.com/tools/downloads) match data — 10,044 pro games in 2025 (building), 9,266 games in 2026 up to September 28 (judging), 2022 for the bonus analyses.

## The result

**The whole 2026 season in live conditions** (8,566 games, February → September). Every month the model is retrained on everything played before the 1st, then predicts that month. The Elo baselines are updated after *every* game, which favours them.

| Model | AUC [95 % CI] | Games called correctly |
|---|---:|---:|
| KDA (updated monthly) | 0.651 [0.640–0.662] | 60.3 % |
| v1.0 frozen (2025 ratings, never updated) | 0.687 [0.678–0.698] | 62.5 % |
| Team Elo (updated every game) | 0.688 [0.677–0.698] | 63.8 % |
| Player Elo (updated every game) | 0.696 [0.686–0.706] | 63.8 % |
| **v1.1 LoL Ratings 3.0 (retrained monthly)** | **0.722 [0.713–0.732]** | **65.2 %** |

v1.1 beats the team Elo in 7 months out of 8. Adding both Elos on top of it brings nothing (0.721).

**Right after the off-season** (February 2026, 1,010 games, 2025 ratings frozen): team Elo collapses to 53.3 % because the team name no longer tells you who plays; v1.0 keeps 63.3 % (AUC 0.692 vs 0.558).

**Best player per role, major leagues (ratings as of September 28, 2026)**

| Role | Reference model | #1 across 400 model versions |
|---|---|---|
| Top | PerfecT (KT Rolster) | Kiin (Gen.G) 56 %, PerfecT 40 % |
| Jungle | JunJia (JD Gaming) | Canyon (Gen.G) 57 %, JunJia 41 % |
| Mid | Chovy (Gen.G) | Chovy 100 % |
| ADC | Ruler (Gen.G) | Ruler 100 % |
| Support | Peter (DN SOOPers) | Peter 66 % |

Gen.G fielded exactly the same five players in 2025 and 2026, so no version of the model can tell which of them carries the others — that is why modelling choices flip #1 between a Gen.G player and someone else. Under statistical uncertainty, a reference #1 is #1 in only 22–38 % of draws.

Academies and regional leagues get their own table: their players almost never face major-league players, so mixing them in one ranking would be misleading. Current #1 there: Rich (Kiwoom DRX Challengers, top) is #1 among all non-major players in 45 % of versions and top 10 in all of them; Guti (T1 Esports Academy) has the highest rating but is less robust.

**Scouting check.** Of the 20 best-rated non-major players in 2025, 70 % were playing in a major league in 2026 (base rate 10.3 %). AUC for predicting promotions: 0.75 (KDA 0.70).

**League levels.** With 2025 alone the model put the LCK Challengers level with the LEC (+9 ± 93 points: undetermined). The off-season transfers settled it: players who left the LCK CL did slightly worse than their 2025 rating (−47 ± 44 points), players who left the LEC did better (+301 ± 50). With 2026 included: LCK +697, LPL +492, LEC +490, LCS +404, LCK CL +327, CBLOL +301, LCP +238, LFL +220.

**Bonus probes.** Counterpicking your lane opponent is worth about +33 gold at 15 minutes in top lane, +15 in jungle, +13 in mid, nothing in bot or support (≈26,700 lane matchups per role, controlling for side, team Elo and champion strength). The "tilt" after losing a game disappears under a placebo: the next meeting weeks later shows an even bigger gap, so it is Elo under-reacting, not tilt.

## How it works

| Version | Idea | What went wrong |
|---|---|---|
| 0.1 | KDA | Rekkles in NLC is the best player in the world. KDA correlates 0.66 with win rate. |
| 0.2 | LoL Ratings 2.0 (hand weights, z-scores) applied worldwide | z-scores across all roles silently change the weights; one missing stat voids the score. |
| 0.3 | z-score within role | Top 50 dominated by small leagues. Correlated stats vote twice. |
| 0.4 | RAPM: each game is an equation, `final gold diff = side + Σ blue players − Σ red players`, ridge regression | Rosters rarely change. |
| 0.5 | League level carried by the player (home league), linked by international events and players changing league | First attempt put the LFL above the LCK. |
| 0.6 | Box-score prior with role-specific weights learned from the RAPM impact (not from winning) | — |
| 0.7 | Target = final gold difference | — |
| 0.8 | Tested, no effect: champion adjustment, lane stats at 15, time decay | — |
| 1.1 | Bug found with more data: players seen only in tournaments shared one catch-all "international" group, creating fake links between leagues. Each tournament now keeps its own group, cups are detected automatically. Monthly retraining. | — |

League names are harmonised across years (`src/leagues.py`): 2025 LTA North = LCS, LTA South = CBLOL (plus two LATAM teams), plain "LTA" (North/South cross-matches) is treated as an international event, LVP SuperLiga = LES.

Final model: ridge regression with an empirical-Bayes prior, `rating = home league level + individual deviation`, deviation ~ N(box-score prior, 1/λ). Config: `lam=50, lamL=3, target='gold', role_prior=True, prior_alpha=200` (`src/engine.py`).

Checks against fooling myself: shuffled 2025 outcomes give AUC ≈ 0.5 (placebo); split-half stability 0.87; February 2026 was looked at once early for baselines, tuning was done on January 2026 and on August–September 2026 for the multiverse.

## Look up a player

```bash
python explore.py leaderboard --role Mid --top 10                 # major leagues, 2026
python explore.py leaderboard --role Mid --tier academy           # academies & regional leagues
python explore.py player Chovy
python explore.py compare Chovy Faker Caps
python explore.py league LEC --top 10
python explore.py --year 2025 leaderboard --role Top
```

Or open `results/ratings_2026.csv` / `results/ratings_2025.csv`.

## Run it yourself

```bash
pip install -r requirements.txt
bash scripts/get_data.sh     # explains which Oracle's Elixir files to download into data/raw/
bash run_all.sh              # ~45 min on a 2-core laptop, the multiverse is most of it
python -m pytest tests/
```

## Files

```
src/leagues.py           league name harmonisation, tiers, automatic cup detection
src/engine.py            the model (RAPM + league levels + learned box-score prior)
src/evaluate.py          splits, Elo and KDA baselines, scoring
src/v01_v03.py           phases 0.1 - 0.3
src/rolling.py           the 2026 season, retrained monthly, vs online Elo
src/current.py           current ratings + statistical uncertainty
src/league_check.py      are league levels right? 2026 league changers vs their 2025 rating
src/multiverse.py        400 reasonable versions of the model
src/scouting.py          did 2025 ratings see the 2026 promotions coming?
src/bonus_*.py           counterpick value, tilt placebo
results/                 ratings CSVs, phase leaderboards, every number on the page (JSON)
page/                    the write-up (French), rebuilt from results/ by page/build_page.py
explore.py               player lookup
tests/                   sanity checks on the results
```

## Limits

- A player who never played without his four teammates cannot be separated from them (Gen.G, and to a lesser degree academy rosters).
- Complete 2023 and 2024 files were not available (Google Drive download quota), so the model only knows 2025–2026.
- Gaps between leagues that never meet are extrapolated; "points" are a linear scale.

## Credits

Data: Oracle's Elixir (Tim Sevenhuysen). Method inspiration: HQEye's B.A.S.I.C. Built with Claude (Anthropic) as an analysis and pair-programming partner, starting from my LoL Ratings 2.0 notebook.

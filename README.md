# LoL Ratings 3.0 — Who is the best League of Legends player in the world?

**Live page (in French), with the full story and a ratings explorer: https://oradixx.github.io/LoL-ratings/**

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
| v1.1 (retrained monthly) | 0.722 [0.713–0.732] | 65.2 % |
| **v1.2 LoL Ratings 3.0 (retrained monthly, recency-weighted league attachment)** | **0.723 [0.713–0.733]** | **65.4 %** |
| v1.3 season-only ratings (the ones displayed, retrained monthly, see below) | 0.699 [0.688–0.710] | 62.8 % |

v1.2 beats the team Elo in 7 months out of 8. Adding both Elos on top of it brings nothing (0.722).

**Right after the off-season** (February 2026, 1,010 games, 2025 ratings frozen): team Elo collapses to 53.3 % because the team name no longer tells you who plays; v1.0 keeps 63.3 % (AUC 0.692 vs 0.558).

**Ratings are per season (v1.3).** The ratings shown on the page and in `results/ratings_<year>.csv` use one season only (2026: league levels start from 2025, then only 2026 games). Predictions (the table above) still use the full history, which is better early in a season.

**Best player per role, major leagues, 2026 season**

| Role | Reference model | #1 across 300 model versions |
|---|---|---|
| Top | Kiin (Gen.G) | Kiin 89 % |
| Jungle | Canyon (Gen.G) | Canyon 98 % |
| Mid | Chovy (Gen.G) | Chovy 98 % |
| ADC | Ruler (Gen.G) | Ruler 93 % |
| Support | Duro (Gen.G) | Duro 91 % |

All five are Gen.G, and that is a warning, not a discovery: Gen.G fielded the same five players in 128 of its 133 games of 2026. The model sees the best team of the season (narrowly ahead of Bilibili Gaming) but cannot tell which of the five carries it, so it shares the credit and each lands first in his role. Changing modelling choices cannot fix missing information, hence the unanimous multiverse; under statistical uncertainty each #1 is #1 in only 16–22 % of draws. Player cards on the page flag every player who played at least 80 % of his games with the same four teammates.

Leagues are split into three tiers that are never mixed in one ranking — major leagues; 2nd tier (LCK Challengers, ERLs, NACL, Circuito Desafiante, Pacific leagues…); 3rd tier (LCK Academy Series, Nexus League, Hitpoint Challengers) — their players almost never face major-league players. Best non-major player in 2026: Rich (Kiwoom DRX Challengers, top), #1 among all non-major players in 100 % of versions.

**Scouting check.** Of the 20 best-rated non-major players in 2025, 70 % were playing in a major league in 2026 (base rate 10.3 %). AUC for predicting promotions: 0.75 (KDA 0.70).

**EMEA Masters.** They count like every event: 817 games (2025–2026) are the only place where European regional leagues play each other. They barely move the big ERLs (linked to the LEC by many transfers) but pull the small ones down by 100–170 points and cut their uncertainty by ~15 %.

**League levels.** With 2025 alone the model put the LCK Challengers level with the LEC (+9 ± 93 points: undetermined). The off-season transfers settled it: players who left the LCK CL did slightly worse than their 2025 rating (−47 ± 44 points), players who left the LEC did better (+301 ± 50). 2026 season: LCK +742, LPL +635, LEC +544, LCS +435, CBLOL +358, LFL +313, LCK CL +309, LCP +300 (LEC − LCK CL = 235 ± 79; LFL, LCK CL and LCP are tied within ± 80).

**Bonus probes.** Counterpicking your lane opponent is worth about +33 gold at 15 minutes in top lane, +15 in jungle, +13 in mid, nothing in bot or support (≈26,700 lane matchups per role, controlling for side, team Elo and champion strength). The "tilt" after losing a game disappears under a placebo: the next meeting weeks later shows an even bigger gap, so it is Elo under-reacting, not tilt.

## v1.3 — one season at a time, and per competition

A reader's remark: a rating over two seasons mixes contexts (league change, team change, a meta that does not suit a player for one split). So:

- **Displayed ratings use one season.** 2026 starts from the 2025 league levels as a prior, a firm one: prior strength 100 raises the month-by-month replay AUC from 0.690 to 0.699 and changes nothing on random half-seasons; plateau from 100 on (`src/league_prior_check.py`).
- **Rating per competition / split** (regular season and playoffs separate) = season rating + a competition-specific delta estimated on the final gold difference of that competition's games.
- **Checked out of sample** (`src/split_validation.py`): each competition's games are split at random in two halves, deltas learned on one half, judged on the other. The first version started the delta from the player's box-score stats on the competition: those stats predict nothing about the other games of the same split (correlation −0.01 in 2025, −0.00 in 2026) and made predictions worse, so they were removed. The gold-difference delta carries a little signal only when heavily regularised: λ = 1000, chosen on 2025 with a criterion fixed beforehand (squared error on the gold target), confirmed on 2026.
- **What it says:** the split-specific part of a player's level is small, about ±55 points, while players of the same role in major leagues have a spread (sd) of 231 points. A meta that does not suit a player probably exists, but over 10–30 games it drowns in noise. And in a stable roster the five players get the same delta.
- **The price:** a season-only model predicts worse early in the season (Feb–Mar AUC 0.654 vs 0.747: in March, when regional splits start, 29 % of fielded players have not played yet in 2026) and equally well in Aug–Sep (0.710 vs 0.708). Even on random held-out 2026 games, the two-season model is slightly better (0.737 vs 0.733). That is the cost of a rating that depends on one season only.
- Example: Exofeng's 2026 rating is 148 (9th of 12 LFL ADCs). Without his 20 games before joining Skillcamp (25 % wins), the same model puts him at 335 — exactly the "season mixing two contexts" case. The competition filter barely moves it, because on average a competition-specific delta is mostly noise.

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
| 1.2 | A reader asked why Exofeng (hyped rookie ADC, 68 % wins with Skillcamp in the LFL) was rated so low. Players were attached to the league where they played most over two years (NLC for him), so everyone climbing from a weaker league was underrated. The league attachment is now a recency-weighted mix of the leagues played (half-life 6 months): same accuracy, Exofeng from 42 to 237 points. | — |
| 1.3 | One rating per season, plus a rating per competition / split (see below). | — |
| 1.1 | Bug found with more data: players seen only in tournaments shared one catch-all "international" group, creating fake links between leagues. Each tournament now keeps its own group, cups are detected automatically. Monthly retraining. | — |

League names are harmonised across years (`src/leagues.py`): 2025 LTA North = LCS, LTA South = CBLOL (plus two LATAM teams), plain "LTA" (North/South cross-matches) is treated as an international event, LVP SuperLiga = LES, LFL Division 2 = Nexus League. The Chinese LDL is not in the Oracle's Elixir files.

Final model: ridge regression with an empirical-Bayes prior, `rating = home league level + individual deviation`, deviation ~ N(box-score prior, 1/λ). Config: `lam=50, lamL=3, target='gold', role_prior=True, prior_alpha=200, home='mix'` (`src/engine.py`).

Checks against fooling myself: shuffled 2025 outcomes give AUC ≈ 0.5 (placebo); split-half stability 0.87; February 2026 was looked at once early for baselines, tuning was done on January 2026 and on August–September 2026 for the multiverse.

## Look up a player

```bash
python explore.py leaderboard --role Mid --top 10                 # major leagues, 2026
python explore.py leaderboard --role Mid --tier tier2 --region EMEA     # 2nd tier (LCK CL, ERLs, NACL...), Europe
python explore.py leaderboard --tier tier3                         # 3rd tier (LCK Academy Series, Nexus League, Hitpoint Challengers)
python explore.py player Chovy
python explore.py compare Chovy Faker Caps
python explore.py league LEC --top 10
python explore.py --year 2025 leaderboard --role Top
python explore.py comps --league LEC                              # competitions / splits of the season
python explore.py comp "LEC Summer · saison régulière" --role ADC  # rating on one competition
```

Or open `results/ratings_2026.csv` / `results/ratings_2025.csv` (one season each: league, region, tier, rating ± uncertainty, gap to the average player of the same role in the same league, multiverse stats), `results/competitions_<year>.csv` (rating per competition / split, with games, win rate, KDA) and `results/ratings_now_2025-2026.csv` (the full-history prediction model). The page has an explorer: season 2026 / 2025, players or teams, tier, region, league, competition / split, role, career path (new, changed league, promoted, relegated), minimum games, search; click a player for his season month by month, his career and all his competitions.

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
src/profiles.py          player cards and team view for the two-season model
src/seasons.py           v1.3: one season at a time, rating per competition / split, team view, monthly trajectories
src/season_multiverse.py 300 versions of the model, trained on one season
src/split_validation.py  are per-competition deltas signal or noise? (held-out halves)
src/league_prior_check.py strength of the previous-season league prior
src/season_only_check.py season-only vs full history, month by month in 2026
src/em_check.py          league levels with and without the EMEA Masters
src/bonus_*.py           counterpick value, tilt placebo
results/                 ratings CSVs, phase leaderboards, every number on the page (JSON)
page/                    the write-up (French), rebuilt from results/ by page/build_page.py
docs/index.html          same page, served by GitHub Pages
explore.py               player lookup
tests/                   sanity checks on the results
```

## Limits

- A player who never played without his four teammates cannot be separated from them (Gen.G, and to a lesser degree academy rosters).
- Complete 2023 and 2024 files were not available (Google Drive download quota), so the model only knows 2025–2026.
- Gaps between leagues that never meet are extrapolated; "points" are a linear scale.
- A rating per competition is mostly the season rating: over one split the data cannot isolate a player's own form from noise, or from his teammates in a stable roster.

## Credits

Data: Oracle's Elixir (Tim Sevenhuysen). Method inspiration: HQEye's B.A.S.I.C. Built with Claude (Anthropic) as an analysis and pair-programming partner, starting from my LoL Ratings 2.0 notebook.

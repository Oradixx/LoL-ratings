#!/usr/bin/env bash
# Full pipeline, in order. About 1 h 30 on a 2-core machine (the two multiverses are most of it).
set -e
python src/prep.py                 # CSV -> parquet, league names harmonised
python src/build_draft_order.py    # pick order per lane (bonus: counterpick)
python src/build_series_elo.py     # series + team Elo (bonus: tilt)
python src/v01_v03.py              # phases v0.1 - v0.3 (2025)
python src/v1.py                   # v1.0 on 2025 + diagnostics (placebo)
python src/scouting.py             # did the 2025 ratings see the 2026 promotions coming?
python src/reliability.py          # split-half stability (2025)
python src/final_test.py           # off-season test: 2025 ratings frozen, February 2026
python src/rolling.py              # the whole 2026 season, retrained every month vs online Elo
python src/rolling_ensemble.py
python src/current.py              # current ratings (all games up to the last file date) + uncertainty
python src/v11_reference.py         # patch 1.2 reference: current ratings with the old v1.1 league attachment
python src/league_check.py         # are league levels right? 2026 league-changers vs their 2025 ratings
python src/em_check.py             # do the EMEA Masters matter for European regional leagues?
python src/multiverse.py 400       # 400 reasonable versions of the model
python src/multiverse_analysis.py
python src/underrated.py
python src/profiles.py             # player cards (monthly rating 2026, career) and team view
python src/bonus_counterpick.py
python src/bonus_tilt.py
python src/seasons.py              # v1.3: one season at a time + rating per competition / split
python src/split_validation.py     # are per-competition deltas signal or noise? (held-out halves)
python src/league_prior_check.py   # strength of the previous-season league prior
python src/season_only_check.py    # does a season-only model predict as well as the full history?
python src/season_multiverse.py 300
python src/halves_history_check.py # to describe 2026, does 2025 help? (random held-out 2026 games)
python src/exofeng_season_check.py # a season mixing two contexts: with / without his pre-Skillcamp games
python src/simulation_study.py     # v1.4: known-truth simulation (recovery, calibration of the ±, inseparable rosters)
python src/transfer_check.py       # v1.4: credit split between teammates, judged on transfers
python src/calibration_check.py    # v1.4: are the announced probabilities right? log-loss, Bo3/Bo5
python src/champion_comfort.py     # v1.4: new champions / meta, pooled over the season
python src/replication.py          # v1.5: the 2024 season (never seen while building), off-seasons 2024/2025, transfers 2024->2025
python src/credit_split_by_roster.py # v1.5: box-score prior on reshuffled rosters, three off-seasons
python src/history_length.py       # v1.5: how many seasons of history for the prediction model (chosen on 2025, confirmed on 2026)
python src/scouting_replication.py # v1.5: scouting 2023->2024, 2024->2025, 2025->2026
# (src/worlds_preregister.py is NOT re-run: the Worlds 2026 predictions stay frozen in results/worlds2026/)
cp data/proc/*.json results/ && rm -f results/tune*.json results/home_test.json results/season_20*.json
python src/export_results.py
python src/page_data.py
python page/build_page.py

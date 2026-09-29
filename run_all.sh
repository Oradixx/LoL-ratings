#!/usr/bin/env bash
# Full pipeline, in order. ~45 min on a 2-core laptop (the multiverse is most of it).
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
python src/league_check.py         # are league levels right? 2026 league-changers vs their 2025 ratings
python src/em_check.py             # do the EMEA Masters matter for European regional leagues?
python src/multiverse.py 400       # 400 reasonable versions of the model
python src/multiverse_analysis.py
python src/underrated.py
python src/profiles.py             # player cards (monthly rating 2026, career) and team view
python src/bonus_counterpick.py
python src/bonus_tilt.py
cp data/proc/*.json results/
python src/export_results.py
python src/page_data.py
python page/build_page.py

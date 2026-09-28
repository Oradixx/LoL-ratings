#!/usr/bin/env bash
# Full pipeline, in order. ~20 min on a 2-core laptop (the multiverse is most of it).
set -e
python src/prep.py                 # CSV -> parquet
python src/build_draft_order.py    # pick order per lane (bonus: counterpick)
python src/build_series_elo.py     # series + team Elo (bonus: tilt)
python src/v01_v03.py              # phases v0.1 - v0.3
python src/v1.py                   # v1.0 ratings + diagnostics
python src/uncertainty.py          # posterior uncertainty, P(#1)
python src/scouting.py             # did the model see promotions coming?
python src/reliability.py          # split-half stability
python src/multiverse.py 600       # 600 reasonable versions of the model
python src/multiverse_analysis.py
python src/underrated.py
python src/final_test.py           # the final exam: February 2026
python src/bonus_counterpick.py
python src/bonus_tilt.py
python src/export_results.py
cp data/proc/*.json results/
python src/page_data.py

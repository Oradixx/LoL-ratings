#!/usr/bin/env bash
# Downloads Oracle's Elixir match data (2022, 2025, early 2026).
# Official source: https://oracleselixir.com/tools/downloads (Google Drive, yearly CSVs).
# The files below are public GitHub mirrors of those CSVs that were used for this project.
set -e
mkdir -p data/raw data/proc
curl -L -o data/raw/oe_2022.csv https://raw.githubusercontent.com/stvngo/LoL-Statistical-Analysis/main/2022_LoL_esports_match_data_from_OraclesElixir.csv
curl -L -o data/raw/oe_2025.csv https://raw.githubusercontent.com/jmirving/draft-sage/main/resources/2025_LoL_esports_match_data_from_OraclesElixir.csv
curl -L -o data/raw/lyc_2026.csv https://raw.githubusercontent.com/Lycoriste/lol_analysis/master/loldata_2026.csv
echo "done: $(ls data/raw)"

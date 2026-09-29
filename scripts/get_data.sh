#!/usr/bin/env bash
# Data: Oracle's Elixir yearly match data, https://oracleselixir.com/tools/downloads
# 1. Download 2025_LoL_esports_match_data_from_OraclesElixir.csv and 2026_... from that page
#    (if Google Drive says "quota exceeded": right click > "Make a copy" in your own Drive, then download the copy)
# 2. Put them in data/raw/ with their original names.
# 2022 (only used by the bonus analyses) is fetched from a public GitHub mirror:
set -e
mkdir -p data/raw data/proc
[ -f data/raw/oe_2022.csv ] || curl -L -o data/raw/oe_2022.csv https://raw.githubusercontent.com/stvngo/LoL-Statistical-Analysis/main/2022_LoL_esports_match_data_from_OraclesElixir.csv
ls -la data/raw

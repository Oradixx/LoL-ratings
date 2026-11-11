"""Télécharge les fichiers annuels d'Oracle's Elixir dans data/raw/ (https://oracleselixir.com/tools/downloads).
Demande `pip install gdown`. Si Google Drive refuse (quota), téléchargez les fichiers à la main depuis cette page."""
import os, subprocess, sys
FILES = {2025: '1v6LRphp2kYciU4SXp0PCjEMuev1bDejc', 2026: '1hnpbrUpBMS1TZI7IovfpKeZfWJH1Aptm'}
os.makedirs('data/raw', exist_ok=True)
ok = True
for y, fid in FILES.items():
    out = f'data/raw/{y}_LoL_esports_match_data_from_OraclesElixir.csv'
    r = subprocess.run([sys.executable, '-m', 'gdown', fid, '-O', out])
    if r.returncode or not os.path.exists(out) or os.path.getsize(out) < 1_000_000:
        print(f'échec du téléchargement {y}'); ok = False
sys.exit(0 if ok else 3)

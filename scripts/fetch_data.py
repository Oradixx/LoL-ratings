"""Download the Oracle's Elixir yearly files into data/raw/ (used by the weekly update workflow).
Oracle's Elixir publishes them on Google Drive; the IDs below are the public files linked from
https://oracleselixir.com/tools/downloads. Google Drive sometimes refuses automated downloads ("quota exceeded"):
in that case the script says so and exits with code 3, and the workflow skips the update instead of failing."""
import sys, os, subprocess
FILES={2023:'1XXk2LO0CsNADBB1LRGOV5rUpyZdEZ8s2',2024:'1IjIEhLc9n8eLKeY-yh_YigKVWbhgGBsN',2025:'1v6LRphp2kYciU4SXp0PCjEMuev1bDejc',2026:'1hnpbrUpBMS1TZI7IovfpKeZfWJH1Aptm'}
os.makedirs('data/raw',exist_ok=True)
ok=True
for y,fid in FILES.items():
    out=f'data/raw/{y}_LoL_esports_match_data_from_OraclesElixir.csv'
    r=subprocess.run([sys.executable,'-m','gdown','--fuzzy',f'https://drive.google.com/file/d/{fid}/view','-O',out],capture_output=True,text=True)
    if r.returncode!=0 or not os.path.exists(out) or os.path.getsize(out)<1_000_000:
        print(f'::warning::download of {y} failed (Google Drive quota?): {r.stderr.strip()[-300:]}'); ok=False
    else: print(y,'ok',os.path.getsize(out)//1_000_000,'MB')
if not os.path.exists('data/raw/oe_2022.csv'):
    subprocess.run(['curl','-sL','-o','data/raw/oe_2022.csv','https://raw.githubusercontent.com/stvngo/LoL-Statistical-Analysis/main/2022_LoL_esports_match_data_from_OraclesElixir.csv'],check=False)
sys.exit(0 if ok else 3)

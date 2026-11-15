# LoL Ratings 3.0

Classement des joueurs pros de League of Legends par régression sur l'écart d'or de fin de partie (RAPM), construit version par version sur 2025, jugé sur 2026. Page en français publiée par GitHub Pages depuis `docs/`. Le README (anglais) raconte la méthode et donne tous les chiffres ; le projet frère de notes de 1 à 100 et de scouting est `Oradixx/rift-scout`, qui reprend d'ici les niveaux de ligue de départ.

## Commandes

```bash
pip install -r requirements.txt
python scripts/fetch_data.py   # fichiers Oracle's Elixir 2023-2026 -> data/raw/ (+ oe_2022.csv pour les bonus)
bash run_all.sh                # tout le calcul, environ 1 h 30 (les deux multivers en font l'essentiel)
python src/worlds_score.py     # note les pronostics Worlds 2026 figés, une fois les parties dans les données
python src/page_data.py && python page/build_page.py
python -m pytest -q tests/
```

## Mise à jour automatique

`.github/workflows/update.yml` relance tout le lundi à 04:23 UTC, puis note les pronostics Worlds et republie `docs/`. Si le téléchargement échoue, l'étape de calcul est sautée et le run apparaît quand même comme réussi : regarder si l'étape « Run the pipeline » a vraiment tourné (un run de 30 secondes n'a rien fait).

Du 5 octobre au 9 novembre 2026, aucune mise à jour n'a tourné : `scripts/fetch_data.py` passait `--fuzzy` à gdown, option supprimée dans gdown 6. Le script passe maintenant l'identifiant du fichier seul. La page a été recalculée à la main le 15 novembre 2026 avec les données du 13 novembre (Worlds jusqu'aux demi-finales). Le 15 novembre au soir, la finale (Bilibili 3-1 Gen.G), absente d'Oracle's Elixir, a été ajoutée depuis les parties Leaguepedia de Rift Scout pour noter les pronostics : 98 parties, modèle 61,2 % (AUC 0,689) contre Elo 58,2 %. La prochaine mise à jour, avec le fichier d'Oracle's Elixir complet, refera la même note.

## Règles

- `results/worlds2026/frozen_model.json` est figé avant le tournoi : ne jamais relancer `src/worlds_preregister.py` ni le modifier. Seul `src/worlds_score.py` le lit.
- Un changement du modèle se valide hors échantillon (mois par mois sur 2026, saison 2024 jamais vue, transferts), pas en regardant le classement.
- `data/` n'est pas versionné. `results/` et `docs/index.html` sont générés par le calcul : les reconstruire, ne pas les modifier à la main.
- Les trois niveaux de ligue (majeures, deuxième, troisième niveau) ne sont jamais mélangés dans un même classement.

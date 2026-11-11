# Rift Scout

Les meilleurs joueurs professionnels de League of Legends, notés de 1 à 100 sur une échelle commune à toutes les ligues, et un outil de scouting par poste et par style de jeu.

La page est un seul fichier : `docs/index.html` (ouvrable directement dans un navigateur, publiable tel quel sur GitHub Pages).

## Ce que fait l'appli

- **Classement** : le meilleur cinq et le classement complet, filtrables par poste, niveau de ligue, région, ligue et événement (Worlds, MSI, un split…), saisons 2025 et 2026.
- **Fiche joueur** : note générale, niveau de l'équipe et écart individuel, forme récente, forces et points faibles rédigés, huit facettes (lane, début de partie, teamfight, dégâts, farm et or, vision, survie, objectifs), weakside et strongside, note par événement, champions, joueurs au style proche.
- **Scouting** : on choisit une équipe et un poste ; les candidats sont classés par note, par ressemblance de style avec le titulaire et par ce qu'ils apportent aux quatre autres joueurs.
- **Méthode** : le calcul expliqué, les poids par poste, le niveau des ligues.

## La note

`note = niveau de l'équipe + écart individuel`

1. **Niveau de l'équipe.** Un modèle de victoire (Bradley-Terry régularisé) sur toutes les parties de la saison. Chaque équipe part du niveau de sa ligue ; les tournois internationaux recalent les ligues entre elles.
2. **Stats par partie.** Chaque stat est comparée aux joueurs du même poste dans la même compétition, après correction du champion joué, puis regroupée en huit facettes.
3. **Écart individuel.** On retire de chaque facette ce que l'écart de niveau entre les deux équipes explique. Le reste, pondéré selon le poste, est l'écart individuel. Son poids face au niveau d'équipe est calé sur les données : un écart-type d'écart individuel vaut environ 100 points de niveau, ce que donne la relation mesurée entre stats et écart de niveau.
4. **Échelle.** 80 = joueur médian des ligues majeures ; les tout meilleurs approchent 97.

Les réglages (poids des facettes, régularisation) sont en tête de `pipeline/build.py`.

## Lancer

```bash
pip install -r requirements.txt
```

```bash
python pipeline/fetch_data.py
```

```bash
python pipeline/build.py data/raw
```

```bash
python build_page.py
```

`build.py` écrit `app/data.json` ; `build_page.py` assemble `app/` en `docs/index.html`.

## Limites connues

- Les **contrats** ne figurent pas dans les données de match : la disponibilité d'un joueur n'est pas connue. Leaguepedia publie les dates de fin de contrat ; c'est la prochaine source à brancher.
- Dans un effectif qui ne change jamais, le niveau de l'équipe est partagé entre les cinq joueurs ; seules les stats individuelles les départagent.
- Weakside et strongside sont approchés par la participation aux kills avant 15 minutes : les données ne disent pas où passe le jungler.
- Les niveaux de ligue de départ (`pipeline/leagues.json`) viennent de LoL Ratings 3.0 ; pour une nouvelle saison il faut les reconduire ou les recalculer.

Données : [Oracle's Elixir](https://oracleselixir.com/tools/downloads).

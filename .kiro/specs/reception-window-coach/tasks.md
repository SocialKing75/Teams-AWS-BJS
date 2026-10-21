# Tasks — Onglet Coach (Fenêtre de réception)

## Python — Moteur (écrit `matchups.json`)
- [ ] T1. Charger `supplementary_data.csv` + `input_2023_wXX.csv` + `output_2023_wXX.csv`
      (commencer avec 2–3 semaines seulement pour la vitesse).
- [ ] T2. Pour chaque jeu : repérer la frame de lancer (dernière frame `input`)
      et la frame d'arrivée (dernière frame `output`).
- [ ] T3. Identifier le receveur ciblé (`player_role == "Targeted Receiver"`)
      et le défenseur le plus proche au lancer (`Defensive Coverage`/`Defense`).
- [ ] T4. Calculer `window_throw`, `window_arrival`, `closing` par jeu.
- [ ] T5. Joindre le contexte (couverture, man/zone, route nettoyée, depth, down, dist_bucket).
- [ ] T6. Exclure : pas de receveur/arrivée, routes hors liste blanche, jeux nullifiés.
- [ ] T7. Agréger par cellule → `n`, `sum_*`, `avg_*`, bootstrap `ci`.
- [ ] T8. Filtrer `n ≥ 10`, écrire `matchups.json` (schéma design.md §5).
- [ ] T9. Vérifier : total d'actions cohérent, aucune valeur NaN, unités en yards.

## React — Front (lit `matchups.json`)
- [ ] F1. Charger `mock/matchups.json` (puis le vrai fichier) dans un state.
- [ ] F2. Composant Heatmap couverture × route, couleur = `avg_closing` (échelle divergente).
- [ ] F3. Barre de filtres : man/zone, profondeur, down, distance.
- [ ] F4. Ré-agrégation à la volée : `Σ sum / Σ n` sur les cellules filtrées.
- [ ] F5. Griser les cellules `n < 10` (« échantillon insuffisant »).
- [ ] F6. Tooltip/clic : `n`, fenêtre lancer → arrivée, `avg_closing`, `ci`.
- [ ] F7. Format 1 décimale + unité `yd` ; skeleton de chargement.

## Spécifications (Brigitte)
- [ ] S1. Valider la liste blanche des routes sur les vraies valeurs distinctes.
- [ ] S2. Livrer `mock/matchups.json` (débloque F1).
- [ ] S3. Relire requirements.md + design.md avec les 2 devs (alignement contrat).
- [ ] S4. Rédiger la section « Limites & biais » du README (seuil, routes, descriptif).

## Dépendances
- F1 dépend de S2 (mock) — à livrer en priorité.
- T8 produit le fichier réel qui remplace le mock (F1 rebranche ensuite).

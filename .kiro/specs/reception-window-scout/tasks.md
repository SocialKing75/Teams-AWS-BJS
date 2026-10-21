# Tasks — Onglet Scout (Fenêtre de réception)

## Python — Moteur (écrit `defenders.json`)
- [ ] T1. Réutiliser le calcul fenêtre du moteur Coach (lancer/arrivée, receveur, défenseur proche).
- [ ] T2. Pour chaque action : `placement`, `closing`, `flight_time`, `closing_rate` (yd/s).
- [ ] T3. Associer chaque action au **défenseur le plus proche** (actions exposées).
- [ ] T4. Régression `closing_rate ~ window_throw + flight_time` → `expected_rate` par action.
- [ ] T5. `coe = closing_rate − expected_rate` par action.
- [ ] T6. Agréger par `nfl_id` : `placement`, `closing_rate`, `expected_rate`, `closing_index`, `n_plays`.
- [ ] T7. Bootstrap 95 % sur `closing_index` → `ci`.
- [ ] T8. Filtrer `n_plays ≥ 20` ; joindre nom/poste/équipe ; écrire `defenders.json`.
- [ ] T9. Vérifier : aucune valeur NaN, unités (yd, yd/s), `exposed_only = true`.

## React — Front (lit `defenders.json`)
- [ ] F1. Charger `mock/defenders.json` (puis le vrai fichier).
- [ ] F2. Tableau classement trié par `closing_index` (rang, nom, poste, n_plays, placement, index + IC).
- [ ] F3. Couleur de `closing_index` (vert = + vite, rouge = - vite).
- [ ] F4. Fiche joueur au clic : 2 volets (placement au lancer / rattrapage pendant le vol).
- [ ] F5. Phrase de synthèse auto à partir des chiffres.
- [ ] F6. Bandeau « classement parmi les défenseurs exposés ».
- [ ] F7. Format 2 déc. (yd/s), 1 déc. (yd) ; skeleton de chargement.

## Spécifications (Brigitte)
- [ ] S1. Valider le choix taux (yd/s) vs total avec l'équipe.
- [ ] S2. Livrer `mock/defenders.json` (débloque F1).
- [ ] S3. Relire requirements.md + design.md avec les 2 devs.
- [ ] S4. Rédiger la partie « biais de sélection » du README (commune au Scout).

## Dépendances
- F1 dépend de S2 (mock).
- Le moteur Scout réutilise le moteur Coach (même calcul de fenêtre) → factoriser.

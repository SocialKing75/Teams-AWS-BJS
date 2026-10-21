# Tasks — Onglet Broadcast (Fenêtre de réception)

## Python — Moteur (écrit `play.json`)
- [ ] T1. Réutiliser le calcul fenêtre du moteur (lancer/arrivée, receveur, défenseur proche).
- [ ] T2. Pour une action : récupérer les positions réelles receveur/défenseur à chaque frame (`output`).
- [ ] T3. Calculer `window_series` (fenêtre par frame) + `window_throw`, `window_arrival`, `flight_time`.
- [ ] T4. Approximer la trajectoire du ballon (lancer → `ball_land`) par interpolation linéaire.
- [ ] T5. Construire `frames` (t, receiver, defender, ball) + `ball_land`.
- [ ] T6. Générer `sentence` (règle déterministe §3) + joindre contexte + `result`.
- [ ] T7. Écrire `play.json` ; prévoir un tableau de quelques actions « démo » sélectionnables.
- [ ] T8. Vérifier : coordonnées dans le terrain (0–120 / 0–53.3), pas de NaN.

## React — Front (lit `play.json`)
- [ ] F1. Charger `mock/play.json`.
- [ ] F2. Dessiner le terrain (SVG/canvas) 120 × 53.3.
- [ ] F3. Animer receveur / défenseur / ballon sur `frames` (play/pause/rejouer).
- [ ] F4. Dessiner le segment fenêtre à chaque frame + compteur fenêtre (yd).
- [ ] F5. Courbe simple de `window_series`.
- [ ] F6. Afficher `sentence` en grand + `result`.
- [ ] F7. Sélecteur d'action ; bandeau limites (ballon approximé).

## Spécifications (Brigitte)
- [ ] S1. Choisir 2–3 actions « démo » marquantes (grosse fermeture / fenêtre qui reste ouverte).
- [ ] S2. Livrer `mock/play.json` (débloque F1).
- [ ] S3. Valider le gabarit de phrase (`sentence`) avec l'équipe.
- [ ] S4. Relire requirements.md + design.md avec les 2 devs.

## Dépendances
- F1 dépend de S2 (mock).
- Réutilise le calcul fenêtre du moteur Coach/Scout (factoriser).

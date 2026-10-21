# Design — Onglet Broadcast (Fenêtre de réception)

## 1. Rappel métrique (commune aux 3 onglets)
Voir aussi `reception-window-coach/design.md §1`.

- **Lancer** = dernière frame `input` ; **Arrivée** = dernière frame `output`.
- Receveur ciblé = `player_role == "Targeted Receiver"`.
- Défenseur le plus proche (au lancer) = joueur `player_role ∈ {"Defensive Coverage","Defense"}`
  le plus proche du receveur au lancer (**on garde le même défenseur** sur toute l'animation).
- Fenêtre (yd) = distance receveur ↔ défenseur, calculée **à chaque frame** du vol.
- `flight_time` = `num_frames_output × 0,1` s (10 Hz).

## 2. Données d'animation (depuis `output` + `input`)
Pour l'action choisie, on construit la série de frames du vol :
- Positions **réelles** du receveur et du défenseur à chaque frame → `output` (x, y).
- `window_series[i]` = distance(receveur_i, défenseur_i) à la frame i.
- **Ballon** : non fourni frame par frame → **approximation** :
  interpolation linéaire entre la position au lancer (position du `Passer` à la dernière frame
  `input`) et `ball_land_x/y`. Signalé comme approximation dans les limites.

## 3. Génération de la phrase (déterministe, à partir des chiffres)
- Si `window_arrival < window_throw` →
  « Fenêtre réduite de `{window_throw}` à `{window_arrival}` yd en `{flight_time}` s ».
- Si `window_arrival ≥ window_throw` →
  « Fenêtre élargie de `{window_throw}` à `{window_arrival}` yd en `{flight_time}` s ».
- Suffixe résultat : « — `{result}` » (passe complète / incomplète / interception…).
- Arrondis : 1 décimale (yd et s).

---

## 4. Contrat de données — `play.json`

```json
{
  "game_id": 2023090700,
  "play_id": 1234,
  "play_description": "(2:14) P.Mahomes pass deep right to T.Kelce",
  "coverage_type": "Cover-3",
  "route": "CORNER",
  "down": 2,
  "yards_to_go": 8,

  "flight_time": 1.2,
  "window_throw": 6.1,
  "window_arrival": 0.9,
  "window_series": [6.1, 4.8, 3.3, 1.9, 0.9],

  "frames": [
    { "t": 0.0, "receiver": [52.1, 18.4], "defender": [58.0, 20.1], "ball": [45.0, 26.7] },
    { "t": 0.3, "receiver": [54.8, 17.9], "defender": [59.1, 19.2], "ball": [50.2, 24.9] },
    { "t": 0.6, "receiver": [57.3, 17.1], "defender": [60.0, 18.3], "ball": [55.4, 22.3] },
    { "t": 0.9, "receiver": [59.6, 16.0], "defender": [61.2, 16.9], "ball": [60.6, 19.1] },
    { "t": 1.2, "receiver": [61.5, 14.8], "defender": [62.1, 15.2], "ball": [65.8, 15.0] }
  ],
  "ball_land": [65.8, 15.0],

  "result": "Passe complète",
  "sentence": "Fenêtre réduite de 6,1 à 0,9 yd en 1,2 s — Passe complète"
}
```

| Champ | Type | Unité | Définition |
|---|---|---|---|
| `game_id`, `play_id` | int | — | identifiants de l'action |
| `play_description` | string | — | description (depuis supplementary) |
| `coverage_type`, `route`, `down`, `yards_to_go` | — | — | contexte |
| `flight_time` | float | s | durée du vol |
| `window_throw` | float | yd | fenêtre au lancer |
| `window_arrival` | float | yd | fenêtre à l'arrivée |
| `window_series` | float[] | yd | fenêtre à chaque frame du vol |
| `frames` | objet[] | — | `t` (s) + positions `[x,y]` receveur / défenseur / ballon |
| `ball_land` | [float,float] | yd | point de chute (`ball_land_x/y`) |
| `result` | string | — | résultat (`pass_result`) |
| `sentence` | string | — | phrase factuelle générée (§3) |

> `frames` et `ball_land` sont en coordonnées terrain (x : 0–120, y : 0–53.3).

---

## 5. Rendu React (onglet Broadcast)

- **Terrain** (SVG/canvas) 120 × 53.3 yd avec :
  - point **receveur**, point **défenseur**, point **ballon** animés sur `frames`.
  - **segment fenêtre** (receveur ↔ défenseur) redessiné à chaque frame.
- **Compteur fenêtre** (yd) synchronisé + petite **courbe** de `window_series`.
- **Phrase factuelle** affichée en grand (`sentence`).
- **Contrôles** : play / pause / rejouer, sélecteur d'action.
- **Bandeau limites** : « position du ballon approximée ; positions joueurs réelles ».
- **Format** : 1 décimale (yd, s).
- **État de chargement** : skeleton tant que `play.json` non chargé.

## 6. Contrat d'interface
- Python **écrit** `play.json` (un objet par action ; ou un tableau d'actions sélectionnables).
- React **lit** `play.json`.
- Mock disponible : `mock/play.json`.

# Design — Onglet Scout (Fenêtre de réception)

## 1. Rappel métrique (commune aux 3 onglets)
Voir aussi `reception-window-coach/design.md §1`.

- **Lancer** = dernière frame `input` ; **Arrivée** = dernière frame `output`.
- Receveur ciblé = `player_role == "Targeted Receiver"`.
- Défenseur le plus proche (au lancer) = joueur `player_role ∈ {"Defensive Coverage","Defense"}`
  dont la distance au receveur ciblé est minimale **au lancer**.
- `window_throw` / `window_arrival` = séparation (yd) receveur ↔ défenseur, au lancer / à l'arrivée.
- `flight_time` = `num_frames_output × 0,1` s (tracking à 10 Hz).

## 2. Calculs par action (pour un défenseur donné)
On ne considère que les actions où **ce défenseur est le plus proche** du receveur ciblé
(= il « couvre » → actions exposées, voir biais §5).

| Grandeur | Formule | Unité |
|---|---|---|
| `placement` | `window_throw` | yd — bas = bien placé au lancer |
| `closing` | `window_throw − window_arrival` | yd — yards refermés pendant le vol |
| `closing_rate` | `closing / flight_time` | **yd/s** — vitesse de fermeture |
| `expected_rate` | régression `closing_rate ~ window_throw + flight_time` | yd/s — « défenseur moyen parti de la même position » |
| `coe` (indice) | `closing_rate − expected_rate` | **yd/s** — referme + vite que prévu si `> 0` |

> Le mot « **plus vite** » de la question → on raisonne en **taux (yd/s)**, pas en total,
> pour qu'un long temps de vol ne gonfle pas le score.

## 3. Agrégation par défenseur
- `placement` = moyenne de `window_throw` (yd).
- `closing_rate` = moyenne du taux réel (yd/s).
- `expected_rate` = moyenne du taux attendu (yd/s).
- `closing_index` = `closing_rate − expected_rate` (yd/s) → **le classement**.
- `ci` = **bootstrap 95 %** (1000 rééch.) sur `closing_index`.
- Seuil : `n_plays ≥ 20`.

## 4. Décomposition clé (fiche joueur)
Deux axes indépendants, à montrer séparément :
- **Placement au lancer** (`placement`, yd) : était-il déjà proche au moment du lancer ?
- **Rattrapage pendant le vol** (`closing_index`, yd/s) : referme-t-il plus vite que la moyenne ?

→ Permet 4 profils : bien placé + bon rattrapage / bien placé + rattrapage faible / etc.

## 5. Filtres & biais
- Exclure actions sans receveur/arrivée, jeux nullifiés par pénalité.
- **Biais de sélection (à afficher)** : seuls les défenseurs **les plus proches du receveur ciblé**
  sont suivis → classement « parmi les exposés », pas toute la ligue.

---

## 6. Contrat de données — `defenders.json`

```json
[
  {
    "nfl_id": 42816,
    "name": "A. Defender",
    "position": "CB",
    "team": "DAL",
    "n_plays": 34,

    "placement": 5.2,
    "closing_rate": 0.75,
    "expected_rate": 0.33,
    "closing_index": 0.42,
    "ci": [0.10, 0.74],

    "exposed_only": true
  }
]
```

| Champ | Type | Unité | Définition |
|---|---|---|---|
| `nfl_id` | int | — | identifiant joueur |
| `name` | string | — | nom affiché |
| `position` | string | — | poste (CB, S, LB…) |
| `team` | string | — | équipe |
| `n_plays` | int | — | nb d'actions exposées (≥ 20 pour être classé) |
| `placement` | float | yd | distance moyenne au receveur **au lancer** |
| `closing_rate` | float | yd/s | vitesse de fermeture réelle moyenne |
| `expected_rate` | float | yd/s | vitesse attendue (défenseur moyen, même position) |
| `closing_index` | float | yd/s | `closing_rate − expected_rate` — **tri du classement** |
| `ci` | [float, float] | yd/s | IC 95 % sur `closing_index` |
| `exposed_only` | bool | — | toujours `true` (rappel du biais) |

---

## 7. Rendu React (onglet Scout)

- **Tableau classement** trié par `closing_index` décroissant :
  rang · nom · poste · `n_plays` · `placement` (yd) · `closing_index` (yd/s) + barre d'IC.
- **Couleur** `closing_index` : vert = referme + vite que la moyenne, rouge = + lentement.
- **Clic sur une ligne → fiche joueur** à deux volets :
  - **Placement au lancer** : `placement` yd (+ repère « proche / loin »).
  - **Rattrapage pendant le vol** : `closing_rate` vs `expected_rate` (yd/s), `closing_index`, `ci`.
  - **Phrase de synthèse** : « Referme 0,42 yd/s plus vite que la moyenne,
    pour un placement de 5,2 yd (34 actions). »
- **Bandeau biais** (toujours visible) : « Classement parmi les défenseurs exposés au ballon. »
- **Format** : 2 décimales pour yd/s, 1 décimale pour yd.
- **État de chargement** : skeleton tant que `defenders.json` non chargé.

## 8. Contrat d'interface
- Python **écrit** `defenders.json` (schéma §6).
- React **lit** `defenders.json`.
- Mock disponible : `mock/defenders.json`.

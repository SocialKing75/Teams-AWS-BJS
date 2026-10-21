# Design — Onglet Coach (Fenêtre de réception)

## 1. Définition de la métrique (source de vérité commune aux 3 onglets)

**Données :** NFL Big Data Bowl 2026.
`data/114239_nfl_competition_files_published_analytics_final/`
- `train/input_2023_wXX.csv` : tracking jusqu'au lancer + `ball_land_x/y` (point de chute DONNÉ),
  `player_role`, `num_frames_output`.
- `train/output_2023_wXX.csv` : positions (x, y) des joueurs **pendant le vol** (vérité terrain).
- `supplementary_data.csv` : contexte du jeu (couverture, route, down, etc.).

**Instants :**
- **Lancer** = dernière frame de `input` du jeu (le ballon part).
- **Arrivée** = dernière frame de `output` du jeu (`num_frames_output`).

**Joueurs (via `player_role` dans input) :**
- Receveur ciblé = `player_role == "Targeted Receiver"`.
- Défenseur le plus proche = joueur `player_role ∈ {"Defensive Coverage", "Defense"}`
  dont la distance au receveur ciblé est minimale **au lancer**.

**Fenêtre de réception = distance euclidienne receveur ciblé ↔ défenseur le plus proche.**
- `window_throw`  = fenêtre à l'instant du lancer.
- `window_arrival`= fenêtre à l'instant de l'arrivée.
- `closing` = `window_throw − window_arrival`
  - `> 0` → la fenêtre **se referme** (le défenseur gagne du terrain).
  - `< 0` → la fenêtre **s'ouvre** (le receveur gagne / le défenseur décroche).

> Pour le Coach, on agrège par **situation**. Mais le Coach raisonne **en yards concrets**,
> pas en indice abstrait : la donnée phare est la **séparation en yards au moment de l'arrivée**
> (`window_arrival`), traduite en **langage football** (ouvert / couvert).

### Langage football (catégories de séparation à l'arrivée)
| `window_arrival` | Libellé affiché |
|---|---|
| `< 1` yd  | **Contesté** |
| `1–2` yd  | **Serré** |
| `2–3` yd  | **Ouvert** |
| `≥ 3` yd  | **Grand ouvert** |

- **`separation` (phare)** = `window_arrival` en yards = « combien le receveur est ouvert au catch ».
- **`pct_open`** = part des actions finissant à `≥ 3` yd (grand ouvert).
- **`pct_contested`** = part des actions finissant à `< 1` yd (contesté).
- `closing` (`window_throw − window_arrival`) reste affiché en **secondaire**
  pour expliquer *comment* la fenêtre a évolué (« passée de 4,4 à 3,3 yd »), en yards, sans jargon.

---

## 2. Dimensions de « situation » (depuis `supplementary_data.csv`)

| Dimension | Colonne source | Transformation |
|---|---|---|
| Couverture | `team_coverage_type` | tel quel |
| Man / Zone | `team_coverage_man_zone` | tel quel |
| Route | `route_of_targeted_receiver` | **liste blanche** (voir §3) |
| Profondeur | `pass_length` | → `short` / `deep` |
| Down | `down` | 1–4 |
| Distance | `yards_to_go` | → bucket `1-3` / `4-6` / `7+` |

## 3. Nettoyage des routes (liste blanche)
Garder uniquement : `HITCH, OUT, FLAT, CROSS, GO, IN, SLANT, POST, ANGLE, CORNER, WHEEL, SCREEN`.
Exclure le bruit de la colonne (`2x2`, `3x1`, `SHOTGUN`, `EMPTY`, `SINGLEBACK`, `C`, …).

## 4. Filtres & robustesse
- Exclure les jeux sans receveur ciblé identifiable, sans frame d'arrivée, annulés sur pénalité
  (`play_nullified_by_penalty`).
- Seuil d'affichage : `n ≥ 10` par cellule (sinon grisée).
- Intervalle de confiance : **bootstrap** (1000 rééchantillonnages) sur `closing`, à 95 %.

---

## 5. Contrat de données — `matchups.json`

Une ligne = **une cellule de situation** (combinaison des dimensions).
Chaque ligne porte **les sommes + `n`** pour permettre au front de ré-agréger correctement
lorsqu'un filtre est appliqué (moyenne = `Σ sum / Σ n`).

```json
[
  {
    "coverage_type": "Cover-3",
    "man_zone": "Zone",
    "route": "GO",
    "depth": "deep",
    "down": 3,
    "dist_bucket": "7+",

    "n": 58,
    "sum_window_throw": 220.4,
    "sum_window_arrival": 179.8,
    "sum_closing": 40.6,
    "n_open": 14,
    "n_contested": 9,

    "avg_window_throw": 3.8,
    "separation": 3.1,
    "separation_label": "Grand ouvert",
    "pct_open": 0.24,
    "pct_contested": 0.16,
    "avg_closing": 0.7,
    "ci": [0.3, 1.1]
  }
]
```

> **Yards d'abord (langage coach).** La valeur mise en avant est `separation`
> (séparation en yards à l'arrivée), avec son libellé football `separation_label`.
> `avg_closing` reste présent mais en information secondaire.

| Champ | Type | Unité | Définition |
|---|---|---|---|
| `coverage_type` | string | — | schéma de couverture |
| `man_zone` | string | — | `Man` / `Zone` |
| `route` | string | — | route ciblée (liste blanche) |
| `depth` | string | — | `short` / `deep` |
| `down` | int | — | 1–4 |
| `dist_bucket` | string | yd | `1-3` / `4-6` / `7+` |
| `n` | int | — | nb d'actions dans la cellule |
| `sum_window_throw` | float | yd | Σ fenêtre au lancer |
| `sum_window_arrival` | float | yd | Σ fenêtre à l'arrivée |
| `sum_closing` | float | yd | Σ fermeture |
| `n_open` | int | — | nb d'actions finissant `≥ 3` yd |
| `n_contested` | int | — | nb d'actions finissant `< 1` yd |
| `avg_window_throw` | float | yd | `sum_window_throw / n` |
| `separation` | float | yd | `sum_window_arrival / n` — **valeur phare (langage coach)** |
| `separation_label` | string | — | Contesté / Serré / Ouvert / Grand ouvert |
| `pct_open` | float | — | `n_open / n` |
| `pct_contested` | float | — | `n_contested / n` |
| `avg_closing` | float | yd | `sum_closing / n` — secondaire (évolution) |
| `ci` | [float, float] | yd | IC 95 % sur la fermeture |

---

## 6. Rendu React (onglet Coach)

- **Composant principal** : heatmap `couverture` (lignes) × `route` (colonnes).
- **Valeur affichée dans la cellule** : **`separation` en yards** (langage coach, ex : `3,1 yd`),
  + pastille de couleur selon le libellé football (`separation_label`).
- **Couleur cellule** : échelle sur la séparation
  (rouge = Contesté `< 1`, orange = Serré, vert clair = Ouvert, vert foncé = Grand ouvert `≥ 3`).
  → le coach repère instantanément les situations où **son receveur finit ouvert**.
- **Filtres** (barre haute) : man/zone, profondeur, down, distance.
  → recalcul via `Σ sum / Σ n` sur les cellules correspondantes.
- **Cellule `n < 10`** : grisée, libellé « échantillon insuffisant ».
- **Tooltip/clic** (langage football, tout en yards) :
  - « Séparation à l'arrivée : **3,1 yd — Grand ouvert** »
  - « Ouvert sur **24 %** des actions, contesté sur **16 %** »
  - « Fenêtre passée de **3,8 → 3,1 yd** » (évolution, secondaire)
  - `n` actions, IC
- **Format** : 1 décimale, unité `yd` ; pourcentages en entiers.
- **État de chargement** : skeleton tant que `matchups.json` non chargé.

## 7. Contrat d'interface
- Python **écrit** `matchups.json` (schéma §5).
- React **lit** `matchups.json` (même schéma).
- Mock disponible : `mock/matchups.json` (pour développer sans attendre le moteur).

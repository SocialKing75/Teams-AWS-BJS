# NFL Big Data Bowl 2027 — Méthodologie (WR Separation Translation)

> Document vivant. Rempli progressivement, phase par phase.
> **État : Phase 1 terminée (inspection + faisabilité).**

## Question de recherche

> **Beyond the 40 :** les qualités de *freinage*, de *réaccélération* et de
> mécanique de mouvement mesurées par capteurs au NFL Combine expliquent-elles
> la capacité d'un receveur à créer de la séparation en match NFL **mieux** que
> les chronos traditionnels du Combine ?

Objectif à terme (non implémenté) : un **Separation Translation Score (STS)**.
La Phase 1 vérifie uniquement que les données permettent réellement l'étude.

## Jeu de données

Archive Kaggle `nfl-big-data-bowl-2027.zip` (~489 Mo compressés, ~2,3 Go
décompressés), lue **directement depuis le zip** pour l'inspection (aucune
décompression de plusieurs Go nécessaire). 9 fichiers, tous présents.

| Fichier | Lignes | Rôle |
|---|---|---|
| `combine_results.csv` | 510 | Mesures Combine traditionnelles (1 ligne/joueur) |
| `combine_tracking.csv` | 463 189 | Tracking capteurs pendant les drills Combine (10 Hz) |
| `players.csv` | 510 | Identité joueur, position NFL, draft |
| `player_play.csv` | ~314 k | 1 ligne/joueur/action : route, séparation, couverture… |
| `games.csv` | 1 002 | Saison / semaine / équipes (clé saison) |
| `player_career_successes.csv` | 510 | Snaps carrière, Pro Bowl, All-Pro |
| `game_tracking_2023/24/25.csv` | ~0,3–1 Go chacun | Tracking match 10 Hz (x,y,s,a,o,dir) |

Le cohorte du dataset est l'ensemble des **510 joueurs draftés 2023–2025**
(et non toute la ligue) : `combine_results`, `players`,
`player_career_successes` ont exactement 510 lignes.

## Clés de jointure

- **`nfl_id`** : identifiant joueur **universel**, présent dans les 8 fichiers
  centrés joueur. C'est la clé Combine ↔ players ↔ NFL.
- **`game_id` + `play_id`** : relient `player_play` et `game_tracking_*`.
- **`game_id`** relie `games` (→ saison) aux tracking de match.
  `player_play` **n'a pas** de colonne saison : la saison s'obtient via
  `games.game_id`.
- **`draft_year`** (= année de Combine) présent dans `combine_results`,
  `combine_tracking`, `players`.

Chaîne de liaison validée :

```
combine_results / combine_tracking  --nfl_id-->  players
         |                                           |
         +------------------ nfl_id -----------------+
                               |
                        player_play  --game_id,play_id-->  game_tracking_*
                               |
                           games (saison via game_id)
```

## Cohorte WR (chiffres réels, Phase 1)

| Étape | Effectif |
|---|---|
| WR dans `combine_results` | **107** |
| WR avec `combine_tracking` | **107** (100 %) |
| WR retrouvés dans `players` | **107** (100 %) |
| WR présents dans `player_play` (ont joué) | **106** |
| WR avec ≥ 20 plays | **102** |
| WR avec ≥ 50 plays | **86** |
| WR avec ≥ 20 cibles (`target`) | **72** |

Plays par WR : min 6 / médiane 261 / max 1638. Cibles par WR : médiane 40.
`separation_at_pass_forward` renseignée : médiane 226 plays/WR.

> Chiffres issus des données (scripts d'inspection), non fabriqués.

## Drills Combine disponibles (`drill_type`)

Pour l'ensemble : `FORTY_YARD_DASH`, `THREE_CONE_DRILL`, `SHORT_SHUTTLE`,
`SKILL_DRILLS_WR/DB/DL/OL/TE/LB`.

**Pour les WR** (présents pour les 107) :
`FORTY_YARD_DASH`, `THREE_CONE_DRILL`, `SHORT_SHUTTLE` **+** `SKILL_DRILLS_WR`
(drills de routes réelles : GO, SLANT, COMEBACK, CURL, POST_CORNER, SPEED_OUT,
FADE, etc.) — un bonus pour relier mécanique de route Combine ↔ route NFL.

Signaux tracking Combine disponibles : `x`, `y`, `s` (vitesse), `a`
(accélération), `dir` (direction), `dis`, `time`, `attempt`, `entity_type`
(`PLAYER` et `BALL`). **Pas** de `frame` explicite (dérivable de `time`),
**pas** d'`orientation` (`o`) côté Combine (présente côté match).

## Métriques NFL disponibles (`player_play`)

- `separation_at_pass_forward` → **separation_at_throw** (directe).
- `cushion` (distance initiale au défenseur).
- `route_ran` : GO, HITCH, CROSS, IN, POST, OUT, CORNER, SLANT, FLAT, SCREEN,
  WHEEL, ANGLE → familles de routes constructibles.
- `team_coverage_man_zone` (ZONE ≈ 30 k, MAN ≈ 12 k), `team_coverage_type`,
  `coverage_assignment`.
- `target`, `pass_result`, `yards_after_catch`, `expected_yards_after_catch`.

**separation_at_arrival** n'existe pas en colonne : à calculer depuis
`game_tracking_*` (distance au **nearest observed defender** à la frame
`event == pass_arrived`). `window_creation = arrival − throw`.

## Définition des métriques (révisée en Phase 4)

**Outcome retenu : `separation_at_throw`** = `separation_at_pass_forward`
(séparation NGS, yd, au lancer), disponible sur **100 %** des routes de WR sur
passe. Dérivé : **`separation_created`** = `separation_at_throw − cushion`
(≈ variation de séparation entre le snap et le lancer ; négatif en moyenne car
le cushion pré-snap est large — plus la valeur est haute, mieux le WR préserve
/ crée de la séparation).

> ⚠️ **Window creation / separation_at_arrival / separation_auc : abandonnés.**
> `game_tracking_*` ne suit que les joueurs **draftés** (≈155 ids/échantillon,
> 0 hors cohorte, pas de ballon). À l'arrivée du ballon, un défenseur n'est
> co-tracé que sur **43 %** des actions (moy. 0,52 défenseur/action) et le
> « plus proche défenseur tracé » donne une séparation **médiane ~15 yd**,
> incompatible avec le défenseur réel en couverture. Ces métriques ne sont donc
> **pas calculables de façon valide** et ne sont pas fabriquées.

## Hypothèses (à tester, non à prouver)

- **H1** : freinage / réaccélération Combine ↔ création d'espace sur routes à
  rupture nette (HARD_STOP, IN/OUT-breaking).
- **H2** : maintien de vitesse au 3-Cone > chrono final pour certaines familles.
- **H3** : accélération initiale du 40 > vitesse max selon la situation.
- **H4** : la relation Combine ↔ séparation dépend du contexte (route,
  couverture).

## Limites et risques

- **Petit N joueur** (~107 WR, ~86 avec ≥50 plays) → modèles interprétables,
  validation **par joueur** (`GroupKFold`, `group = nfl_id`) obligatoire ;
  **jamais** le même joueur en TRAIN et TEST.
- **Nearest observed defender** ≠ défenseur assigné (biais de couverture).
- **Valeurs manquantes** : `three_cone` (330/510), `short_shuttle` (309),
  `bench_reps` (318) souvent absents → imputation/variables à disponibilité
  variable à gérer explicitement.
- `game_tracking_*` ne contient ni rôle ni équipe : l'identification du
  défenseur passe par jointure `player_play` (position/équipe) — **à vérifier**
  que le tracking inclut bien les défenseurs (pas seulement la cohorte draftée).
- **Data leakage** : `ngs_*_score` sont des scores composites NGS (potentiel
  fuite) → à exclure des baselines « traditionnelles » ou traiter à part.
- Tracking match très volumineux (jusqu'à ~1 Go/saison) → traitement par
  `chunksize`, ne jamais charger les 3 saisons simultanément.

## Stratégie de validation

`GroupKFold(group = nfl_id)`. Modèles d'abord interprétables (Linear, Ridge,
ElasticNet), puis éventuellement Gradient Boosting. Comparaison
Modèle A (Combine traditionnel) vs Modèle B (+ capteurs) via MAE / RMSE / R².

## Cohorte finale (Phase 2)

Seuil : `n_plays >= 20` **et** présence dans ≥ 1 saison de tracking match.

```
Participants Combine                510
WR Combine                          107
WR avec combine_tracking            107
WR retrouvés dans players           107
WR présents NFL (player_play)       106
WR présents game_tracking           106
WR avec >= 20 plays                 102
WR avec >= 50 plays                  86
Cohorte finale                      102
```

Exports : `outputs/kaggle_2027/wr_cohort.csv` (102 lignes),
`outputs/kaggle_2027/cohort_report.md`.

Observations Phase 2 :

- Pour cette cohorte, `n_plays == n_routes` (chaque ligne `player_play` d'un WR
  porte une route) → `player_play` est de granularité route pour les WR.
- `separation_at_pass_forward` disponible sur la quasi-totalité des plays
  (médiane 248/WR) → la séparation **au lancer** est quasi gratuite.
- **Manquants Combine traditionnels** (sur 102) : `three_cone` 30/102,
  `short_shuttle` 36/102, `bench_reps` 27/102, `forty` 93/102. Mais le
  **tracking capteur** contient les drills `THREE_CONE_DRILL`/`SHORT_SHUTTLE`
  pour des WR même quand le chrono traditionnel est absent → l'approche capteur
  peut *récupérer* de l'information que le chrono a perdue (cœur du sujet).
- **1 joueur** de la cohorte a `combine_position = WR` mais `nfl_position = TE`
  (101 WR + 1 TE). Décision ouverte : filtrer sur `nfl_position == WR` en
  Phase 3 (passerait la cohorte à 101).

## Features Combine capteurs (Phase 3)

Cohorte filtrée sur `nfl_position == WR` → **101 joueurs**. Features extraites
de `combine_tracking` (10 Hz), agrégées par **médiane** des essais par joueur.
Export : `outputs/kaggle_2027/combine_wr_features.csv`.

Choix méthodologiques :

- `a` du dataset est une **magnitude** (≥ 0) → accélération signée et freinage
  **dérivés de la vitesse** (`ds/dt`, `kinematics.signed_acceleration`), jamais
  depuis `a` brut.
- Lissage léger (moyenne glissante 3 frames) avant dérivation.
- `turn_transition_time` = durée sous `50 % · vitesse de pointe` autour du
  virage — **proxy**, **pas** un temps de contact au sol (les pieds ne sont
  pas tracés).

Features par drill :

| Drill | Features | Couverture |
|---|---|---|
| 40-yard | `peak_speed`, `initial_acceleration`, `time_to_peak_speed`, `speed_at_split` (10 yd) | **89/101** |
| 20-yd shuttle | `peak_deceleration`, `turn_transition_time`, `exit_acceleration`, `min_turn_speed` | **27/101** |
| 3-cone | `speed_retention`, `path_efficiency`, `peak_deceleration`, `min_turn_speed` | **21/101** |

Validation (cohérence capteur ↔ chrono, Pearson) :

- `forty_peak_speed` vs `forty` : **−0.83** (n=89) — physique correcte.
- `forty_speed_at_split` vs `forty` : **−0.76** (n=89).
- `forty_initial_acceleration` vs `forty` : **+0.05** (n=89) → **quasi
  orthogonale au chrono** : signal capteur que le stopwatch ne capte pas
  (cœur du sujet — à confirmer par modélisation, ne pas sur-interpréter).

Limites Phase 3 :

- **Features d'agilité peu peuplées** (shuttle 27, 3-cone 21) : les hypothèses
  H1/H2 seront **sous-dimensionnées** ; prévoir des modèles par drill sur
  sous-échantillons et l'avertir dans les résultats.
- Le tracking capteur contient parfois le drill même sans chrono traditionnel
  → l'approche capteur récupère de l'information, mais l'inverse existe aussi.

## Journal des phases

- **Phase 1 (fait)** : `config.py`, `inspect_data.py`, rapport d'inspection,
  faisabilité confirmée.
- **Phase 2 (fait)** : `build_cohort.py`, cohorte de **102 WR** reliés
  Combine ↔ NFL (101 après filtre `nfl_position == WR`).
- **Phase 3 (fait)** : `kinematics.py` (fonctions pures), `combine_features.py`,
  features capteurs par joueur + export CSV. Validé par la physique du 40-yard.
- **Phase 4 (fait)** : `nfl_features.py`, **37 478 actions** WR avec
  `separation_at_throw` (+ contexte, familles de routes, saison). Pivot
  documenté : `window_creation` abandonné (défenseur non tracé). Valeurs
  validées par le domaine (MAN 2,1 < ZONE 3,5 yd). Export
  `outputs/kaggle_2027/nfl_wr_features.csv`.
- **Phase 6 (fait)** : `merge_combine_nfl.py`, dataset analytique fusionné sur
  `nfl_id` — **37 478 actions × 47 colonnes, 101 joueurs**. Export Parquet
  `outputs/kaggle_2027/combine_nfl_wr_dataset.parquet`. Couverture au niveau
  action : chrono 40 **87 %**, capteur 40 **86 %** ; agilité éparse (3-cone
  ~30 %, shuttle ~39 %).
- Phase 5 : couverte (route / famille / couverture / formation / down-distance
  intégrées dès la Phase 4).
- **Phase 7 (fait)** : `baseline_model.py` — A (chronos) vs B (+ capteurs 40),
  `GroupKFold(group=nfl_id)`, deux outcomes. Export `baseline_report.md` +
  `baseline_metrics.csv`.

## Résultats de la baseline (Phase 7)

Outcome : `separation_at_throw`. Validation `GroupKFold(group=nfl_id)`,
imputation médiane dans le pli, scores NGS exclus.

**Par action (37 478)** : R² ≈ 0 pour A et B. Attendu — les features
athlétiques sont constantes par joueur ; la séparation par action dépend du
contexte (route, couverture), pas du profil Combine.

**Par joueur (101, séparation moyenne)** :

| Modèle | Meilleur régresseur | MAE (yd) | R² |
|---|---|---|---|
| A — traditionnel | RidgeCV | **0.285** | **0.175** |
| B — + capteurs 40 | GradientBoosting | 0.293 | 0.141 |

➡️ **Les capteurs 40-yard n'apportent pas d'information au-delà du chrono.**
`forty_peak_speed` est colinéaire au chrono du 40 (r = −0.83) ; ajouter les
dynamiques capteurs du 40 **dégrade** plutôt le modèle (RidgeCV 0.175 → 0.122).
Le profil athlétique n'explique qu'**~18 %** des écarts de séparation entre
joueurs : la séparation est surtout une affaire de schéma/contexte.

**Exploratoire — agilité (corrélations, N≈20-30, non concluant)** : signaux
encourageants là où vivent H1/H2 — `threecone_speed_retention` r = +0.45
(n=21), `shuttle_exit_acceleration` r = +0.31 (n=27), `three_cone` (chrono)
r = −0.37 (n=29). **Mais** trop peu de joueurs ont ces drills pour conclure.

### Verdict honnête

- **H3 (accél. initiale > vitesse max du 40)** : **non soutenue** par ce
  baseline — le chrono du 40 suffit, les capteurs du 40 sont redondants.
- **H1 / H2 (freinage, réaccélération, maintien de vitesse / agilité)** :
  **non testables de façon fiable** (N trop faible : 20-30 WR). C'est pourtant
  là que se trouve le signal potentiel.
- **STS : NE PAS construire maintenant.** Le brief conditionnait le STS à un
  signal statistique réel ; le baseline bien dimensionné n'en montre pas, et le
  signal prometteur (agilité) est sous-échantillonné.

### Recommandations

1. Élargir la cohorte d'agilité : inclure d'autres positions (DB/TE) pour les
   features de freinage/COD, ou plusieurs millésimes de Combine.
2. Tester un outcome plus sensible au contexte (séparation résiduelle après
   contrôle route/couverture — préfigure `context_expected` du STS).
3. Exploiter `SKILL_DRILLS_WR` (routes réelles au Combine) comme pont direct
   vers les routes NFL.

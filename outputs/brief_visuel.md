# Brief visuel coach — Fenêtre de réception — Données 2023

Généré par `src/brief.py` depuis les CSV de `outputs/` : tout chiffre ci-dessous est identique aux fichiers.

## Titre et message

- **Titre proposé** : « Où la fenêtre de réception reste-t-elle ouverte ? » — sous-titre obligatoire : « Données saison 2023 · méthode réutilisable sur toute saison »
- **Problématique** : dans quelles situations la fenêtre de réception se referme-t-elle le moins entre le lancer et l'arrivée du ballon ?
- **Utilisateur** : un coordinateur offensif qui prépare un adversaire (où attaquer) ou un coordinateur défensif qui s'audite (où l'on fuit).
- **Source à citer sur chaque visuel** : NFL Big Data Bowl 2026, tracking Next Gen Stats
- **Mention à afficher** : « Seuls le receveur ciblé et les défenseurs proches du point de chute sont suivis pendant le vol. »

## Définition à faire figurer en une ligne

**Fenêtre de réception** : distance (yd) entre le receveur ciblé et le défenseur le plus proche, au lancer puis à l'arrivée du ballon. Variation négative = la défense a refermé pendant le vol. Moyenne ligue à l'arrivée : 3.0 yd sur 12966 passes.

## Écrans téléphone (bord de terrain) — défense MIN

Une carte = une information, chiffre clé en grand, phrase prête à afficher. Fichier pour les 32 défenses : `outputs/coach_cartes_telephone.csv` (colonne `phrase`). On glisse de carte en carte ; le chiffre clé est l'écart à la ligue (yd), le texte courant donne l'effectif.

| Type | Rang | Route | Actions | Fenêtre à l'arrivée (yd) | Écart vs ligue (yd) | Complétion | Confiance | Phrase |
|---|---|---|---|---|---|---|---|---|
| attaquer | 1 | POST | 29 | 3.2 | 0.64 | 55 % | faible | POST : +0.6 yd vs ligue (29 passes, confiance faible) |
| attaquer | 2 | IN | 42 | 3.2 | 0.6 | 71 % | moyenne | IN : +0.6 yd vs ligue (42 passes, confiance moyenne) |
| attaquer | 3 | OUT | 54 | 3.3 | 0.49 | 68 % | moyenne | OUT : +0.5 yd vs ligue (54 passes, confiance moyenne) |
| eviter | 1 | SLANT | 29 | 2.0 | -0.32 | 62 % | faible | SLANT : -0.3 yd vs ligue (29 passes, confiance faible) |
| eviter | 2 | SCREEN | 15 | 6.0 | -0.26 | 87 % | faible | SCREEN : -0.3 yd vs ligue (15 passes, confiance faible) |

## Visuel 1 (message principal) — Man / zone × profondeur, ligue

Visuel recommandé : **4 paires de barres** (fenêtre au lancer, fenêtre à l'arrivée) ou 4 flèches lancer → arrivée. Une seule lecture : le man part serré et bouge peu, la zone part large et referme beaucoup, mais reste plus ouverte à l'arrivée.

| Man / zone | Profondeur | Actions | Fenêtre au lancer (yd) | Fenêtre à l'arrivée (yd) | Variation (yd) | Complétion | EPA moyen |
|---|---|---|---|---|---|---|---|
| MAN_COVERAGE | Profonde (>= 15 yd) | 1026 | 1.9 | 1.9 | 0.0 | 43 % | 0.4 |
| MAN_COVERAGE | Courte (< 15 yd) | 2865 | 3.0 | 2.5 | -0.6 | 65 % | 0.21 |
| ZONE_COVERAGE | Profonde (>= 15 yd) | 2149 | 3.3 | 2.7 | -0.6 | 51 % | 0.53 |
| ZONE_COVERAGE | Courte (< 15 yd) | 6924 | 4.8 | 3.5 | -1.2 | 76 % | 0.11 |

## Visuel 2 — Heatmap couverture × route (ligue)

Visuel recommandé : **heatmap** sur la fenêtre à l'arrivée, une seule teinte bleue du clair (fermée) au foncé (ouverte), effectif dans chaque case, cases avec moins de 30 actions masquées. Fichier complet : `outputs/coach_ligue.csv` (62 cases).

Les 8 cases les plus fermées à l'arrivée :

| Couverture | Route | Actions | Fenêtre au lancer (yd) | Fenêtre à l'arrivée (yd) | Variation (yd) | Complétion | EPA moyen |
|---|---|---|---|---|---|---|---|
| COVER_1_MAN | GO | 473 | 1.6 | 1.4 | -0.2 | 39 % | 0.35 |
| COVER_0_MAN | GO | 63 | 2.2 | 1.7 | -0.6 | 36 % | 0.06 |
| COVER_4_ZONE | GO | 198 | 2.3 | 1.8 | -0.5 | 41 % | 0.35 |
| COVER_1_MAN | SLANT | 353 | 2.4 | 1.8 | -0.6 | 68 % | 0.27 |
| COVER_1_MAN | POST | 120 | 1.9 | 1.9 | 0.0 | 51 % | 0.6 |
| COVER_1_MAN | IN | 269 | 2.5 | 2.0 | -0.5 | 54 % | 0.09 |
| COVER_0_MAN | POST | 42 | 2.0 | 2.0 | 0.0 | 57 % | 1.15 |
| COVER_1_MAN | HITCH | 394 | 2.7 | 2.0 | -0.7 | 67 % | 0.09 |

Les 8 cases les plus ouvertes à l'arrivée :

| Couverture | Route | Actions | Fenêtre au lancer (yd) | Fenêtre à l'arrivée (yd) | Variation (yd) | Complétion | EPA moyen |
|---|---|---|---|---|---|---|---|
| COVER_2_ZONE | ANGLE | 75 | 6.5 | 4.3 | -2.3 | 81 % | -0.29 |
| COVER_2_ZONE | CROSS | 121 | 5.8 | 4.5 | -1.3 | 76 % | 0.28 |
| COVER_4_ZONE | FLAT | 238 | 7.0 | 5.0 | -2.0 | 86 % | -0.05 |
| COVER_6_ZONE | FLAT | 159 | 7.4 | 5.1 | -2.3 | 81 % | -0.05 |
| COVER_3_ZONE | FLAT | 485 | 7.3 | 5.5 | -1.9 | 86 % | -0.03 |
| COVER_2_ZONE | FLAT | 214 | 8.1 | 6.0 | -2.1 | 83 % | -0.25 |
| COVER_3_ZONE | SCREEN | 74 | 8.0 | 6.1 | -2.0 | 85 % | -0.06 |
| COVER_4_ZONE | SCREEN | 37 | 9.8 | 6.6 | -3.2 | 92 % | -0.41 |

## Visuel 3 — Fiche adversaire : défense MIN

Visuel recommandé : **barres horizontales par route**, écart à la moyenne ligue (barre vers la droite = fenêtre plus ouverte que la ligue, à attaquer ; vers la gauche = plus fermée, à éviter), effectif affiché, routes avec moins de 15 actions masquées. Paramètre `--equipe XXX` pour une autre défense ; fichiers `outputs/coach_equipes.csv` et `outputs/coach_equipes_routes.csv` pour les 32.

Par man / zone × profondeur :

| Man / zone | Profondeur | Actions | Fenêtre au lancer (yd) | Fenêtre à l'arrivée (yd) | Variation (yd) | Complétion | EPA moyen |
|---|---|---|---|---|---|---|---|
| ZONE_COVERAGE | Profonde (>= 15 yd) | 76 | 3.9 | 2.7 | -1.2 | 46 % | 0.29 |
| MAN_COVERAGE | Courte (< 15 yd) | 77 | 4.0 | 2.9 | -1.1 | 71 % | 0.38 |
| MAN_COVERAGE | Profonde (>= 15 yd) | 20 | 3.0 | 3.0 | 0.0 | 45 % | 0.7 |
| ZONE_COVERAGE | Courte (< 15 yd) | 216 | 5.3 | 4.0 | -1.4 | 81 % | 0.22 |

Par route, écart à la ligue :

| Route | Actions | Fenêtre au lancer (yd) | Fenêtre à l'arrivée (yd) | Variation (yd) | Complétion | EPA moyen | Ligue (yd) | Écart vs ligue (yd) |
|---|---|---|---|---|---|---|---|---|
| IN | 42 | 4.0 | 3.2 | -0.8 | 71 % | 0.45 | 2.6 | 0.6 |
| POST | 29 | 3.6 | 3.2 | -0.4 | 55 % | 0.57 | 2.6 | 0.6 |
| OUT | 54 | 3.9 | 3.3 | -0.6 | 68 % | 0.29 | 2.8 | 0.5 |
| HITCH | 79 | 4.9 | 3.2 | -1.7 | 84 % | 0.35 | 2.8 | 0.4 |
| GO | 46 | 3.6 | 2.3 | -1.3 | 46 % | 0.35 | 1.9 | 0.4 |
| FLAT | 51 | 7.3 | 5.4 | -1.9 | 90 % | -0.06 | 5.1 | 0.3 |
| CROSS | 29 | 4.0 | 3.4 | -0.6 | 59 % | 0.33 | 3.4 | 0.0 |
| SCREEN | 15 | 8.2 | 6.0 | -2.2 | 87 % | 0.03 | 6.3 | -0.3 |
| SLANT | 29 | 3.4 | 2.0 | -1.4 | 62 % | 0.34 | 2.4 | -0.4 |

## Visuel 4 — Classement des 32 défenses (fenêtre à l'arrivée)

Visuel recommandé : **barres horizontales triées**, trait vertical à la moyenne ligue (3.0 yd), défense choisie en couleur forte, les autres en gris.

| Défense | Actions | Fenêtre au lancer (yd) | Fenêtre à l'arrivée (yd) | Variation (yd) | Complétion |
|---|---|---|---|---|---|
| ATL | 392 | 3.3 | 2.7 | -0.6 | 65 % |
| MIA | 401 | 3.5 | 2.8 | -0.7 | 72 % |
| BAL | 445 | 3.7 | 2.8 | -0.9 | 64 % |
| PHI | 473 | 3.5 | 2.8 | -0.7 | 66 % |
| HOU | 399 | 3.9 | 2.9 | -1.0 | 68 % |
| NO | 419 | 3.6 | 2.9 | -0.7 | 62 % |
| WAS | 426 | 3.8 | 2.9 | -0.9 | 69 % |
| CIN | 412 | 3.8 | 2.9 | -1.0 | 67 % |
| CAR | 324 | 4.1 | 2.9 | -1.2 | 68 % |
| SF | 437 | 3.9 | 2.9 | -1.0 | 67 % |
| ARI | 348 | 3.9 | 2.9 | -1.0 | 74 % |
| KC | 372 | 3.6 | 2.9 | -0.7 | 64 % |
| TEN | 396 | 3.9 | 2.9 | -0.9 | 72 % |
| PIT | 420 | 3.9 | 3.0 | -0.9 | 63 % |
| DAL | 375 | 3.7 | 3.0 | -0.7 | 62 % |
| SEA | 419 | 3.9 | 3.0 | -0.9 | 69 % |
| DEN | 416 | 3.9 | 3.0 | -0.9 | 69 % |
| LA | 448 | 3.8 | 3.0 | -0.7 | 63 % |
| LAC | 426 | 4.0 | 3.0 | -1.0 | 66 % |
| NYG | 412 | 4.0 | 3.0 | -1.0 | 66 % |
| NYJ | 366 | 3.9 | 3.1 | -0.9 | 63 % |
| CHI | 446 | 4.3 | 3.1 | -1.2 | 67 % |
| IND | 397 | 4.0 | 3.1 | -0.9 | 66 % |
| CLE | 343 | 4.1 | 3.1 | -1.0 | 62 % |
| DET | 445 | 3.9 | 3.1 | -0.8 | 69 % |
| BUF | 369 | 4.1 | 3.2 | -0.9 | 70 % |
| JAX | 442 | 4.2 | 3.2 | -1.0 | 68 % |
| NE | 411 | 4.2 | 3.2 | -1.0 | 68 % |
| GB | 375 | 4.1 | 3.3 | -0.8 | 69 % |
| TB | 463 | 4.0 | 3.3 | -0.7 | 68 % |
| LV | 360 | 4.4 | 3.4 | -1.0 | 69 % |
| MIN | 389 | 4.7 | 3.5 | -1.2 | 70 % |

## Visuel 5 (optionnel) — Situations de jeu

Down × distance × man/zone, pour lire la fenêtre dans son contexte (fichier `outputs/coach_situations.csv`) :

| Down | Distance | Man / zone | Actions | Fenêtre au lancer (yd) | Fenêtre à l'arrivée (yd) | Variation (yd) | Complétion | EPA moyen |
|---|---|---|---|---|---|---|---|---|
| 1er down | Courte (1-3 yd) | MAN_COVERAGE | 55 | 2.2 | 2.2 | -0.0 | 47 % | 0.08 |
| 1er down | Longue (8+ yd) | MAN_COVERAGE | 896 | 3.0 | 2.5 | -0.5 | 62 % | 0.23 |
| 1er down | Longue (8+ yd) | ZONE_COVERAGE | 3620 | 4.5 | 3.5 | -1.0 | 73 % | 0.2 |
| 1er down | Moyenne (4-7 yd) | MAN_COVERAGE | 56 | 2.4 | 2.0 | -0.4 | 55 % | -0.0 |
| 1er down | Moyenne (4-7 yd) | ZONE_COVERAGE | 42 | 4.1 | 3.5 | -0.6 | 57 % | -0.26 |
| 2e down | Courte (1-3 yd) | MAN_COVERAGE | 157 | 2.7 | 2.3 | -0.4 | 59 % | 0.25 |
| 2e down | Courte (1-3 yd) | ZONE_COVERAGE | 285 | 4.4 | 3.4 | -1.1 | 72 % | 0.16 |
| 2e down | Longue (8+ yd) | MAN_COVERAGE | 564 | 2.8 | 2.3 | -0.5 | 61 % | 0.19 |
| 2e down | Longue (8+ yd) | ZONE_COVERAGE | 2018 | 4.4 | 3.2 | -1.2 | 70 % | 0.08 |
| 2e down | Moyenne (4-7 yd) | MAN_COVERAGE | 382 | 2.7 | 2.1 | -0.5 | 59 % | 0.28 |
| 2e down | Moyenne (4-7 yd) | ZONE_COVERAGE | 928 | 4.4 | 3.3 | -1.1 | 73 % | 0.35 |
| 3e/4e down | Courte (1-3 yd) | MAN_COVERAGE | 509 | 2.9 | 2.6 | -0.2 | 63 % | 0.29 |
| 3e/4e down | Courte (1-3 yd) | ZONE_COVERAGE | 403 | 4.1 | 3.1 | -0.9 | 71 % | 0.45 |
| 3e/4e down | Longue (8+ yd) | MAN_COVERAGE | 511 | 2.7 | 2.2 | -0.6 | 56 % | 0.31 |
| 3e/4e down | Longue (8+ yd) | ZONE_COVERAGE | 1007 | 4.6 | 3.2 | -1.3 | 62 % | 0.13 |
| 3e/4e down | Moyenne (4-7 yd) | MAN_COVERAGE | 761 | 2.4 | 2.1 | -0.3 | 56 % | 0.3 |
| 3e/4e down | Moyenne (4-7 yd) | ZONE_COVERAGE | 769 | 4.0 | 3.0 | -1.0 | 67 % | 0.4 |

## Interface

Usage principal : **téléphone, bord du terrain, en déplacement** : une seule information clé à la fois, lisible d'un coup d'œil, utilisable d'une main, en plein soleil.

Téléphone (cible 360 à 430 px de large) :
- Une seule colonne, scroll vertical, aucun défilement horizontal
- 1 message dominant par écran, chiffre clé en grand (≥ 32 px), texte courant ≥ 16 px
- Zones tactiles ≥ 44 x 44 px, filtres sous forme de boutons ou menus simples
- Graphiques simplifiés : 5 à 8 éléments max, étiquettes directes (pas de légende séparée), pas de survol (hover) nécessaire
- Navigation en bas ou en onglets en haut, accessible au pouce

Tablette / PC (≥ 768 px, jusqu'à 1440 px) :
- Mise en page en 2 à 3 colonnes : filtres à gauche, visuel principal au centre, détails/recommandations à droite
- Possibilité de comparer deux équipes côte à côte
- Info-bulles au survol autorisées en complément, jamais indispensables

Correspondance écrans ↔ données :

| Écran téléphone | Message dominant | Chiffre clé en grand | Fichier |
|---|---|---|---|
| 1. Choix de la défense | bouton / menu simple, 32 équipes | — | `coach_cartes_telephone.csv` |
| 2. « À attaquer » (3 cartes, glisser) | route où la fenêtre reste ouverte | écart à la ligue, ex. « +0,6 yd » | idem, type = attaquer |
| 3. « À éviter » (3 cartes) | route où cette défense referme | écart négatif | idem, type = eviter |
| 4. Man / zone | 4 barres avec étiquettes directes | fenêtre à l'arrivée (yd) | `coach_equipes.csv` |
| 5. Situation (optionnel) | down × distance, 2 boutons man / zone | fenêtre à l'arrivée (yd) | `coach_situations.csv` |

La heatmap couverture × route (62 cases) et le classement des 32 défenses sont réservés à la vue tablette / PC (visuel principal au centre, deux équipes côte à côte).

Style, plein soleil :
- Contraste maximal : texte noir #0b0b0b sur fond blanc #ffffff, pas de gris clair pour l'information ; secondaire #52514e uniquement pour les effectifs.
- Deux couleurs seulement, validées daltonisme : bleu #2a78d6 (à attaquer / man), orange #eb6834 (à éviter / zone) ; le reste en gris #c3c2b7. Le sens est toujours doublé par un mot (« attaquer », « éviter ») et un signe (+ / −), jamais la couleur seule.
- Unités partout (yd, %), effectif visible sur chaque carte, source et « Données 2023 » en pied de chaque écran.

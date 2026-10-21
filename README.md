# Fenêtre de réception — outil coach — Données saison 2023

**Problématique : dans quelles situations la fenêtre de réception se referme-t-elle le moins entre le lancer et l'arrivée du ballon ?**

Utilisateur cible : le coach. Un coordinateur offensif prépare un adversaire (quelles couvertures et quelles routes laissent une fenêtre ouverte à l'arrivée du ballon) ; un coordinateur défensif s'audite (où sa défense referme ou non pendant le vol).

Les données datent de la saison 2023 (NFL Big Data Bowl 2026, tracking Next Gen Stats). Elles ne décrivent pas la situation actuelle des équipes. La méthode s'applique telle quelle à toute saison livrée au même format.

## Installation et lancement (une commande)

```bash
pip install -r requirements.txt
# déposer l'archive de la compétition décompressée dans data/raw/ :
#   data/raw/supplementary_data.csv
#   data/raw/train/input_*.csv et output_*.csv
python src/run_all.py --donnees data/raw     # nettoyage, métrique, vérifications, export JSON pour l'interface
python src/brief.py --equipe KC              # brief visuel avec les chiffres exacts (outputs/brief_visuel.md)
```

Durée : environ 15 à 30 s. Options : `--n-min 30` (actions minimales pour afficher une case ligue), `--n-min-equipe 15` (par équipe), `--sorties autre_dossier`. Aucune année, aucun chemin, aucun nom d'équipe n'est écrit en dur.

### Interface coach (React, mobile-first)

```bash
cd web
npm install
npm run dev -- --host     # http://<IP du PC>:5173 depuis un téléphone sur le même Wi-Fi
npm run build             # dist/ : fichiers statiques à ouvrir ou héberger n'importe où
```

**En ligne** : https://fenetre-reception-coach.vercel.app (hébergé sur Vercel ; `web/vercel.json` lance `npm run build` et sert `dist/` ; redéployer avec `cd web && vercel deploy --prod`).

L'interface lit uniquement des fichiers produits par le pipeline, aucun chiffre n'est saisi à la main : `web/src/data.json` (cartes, synthèses, classement, couleurs) et les fichiers du contrat d'équipe `web/public/contrat/matchups.json` (cellules couverture × man/zone × route × profondeur × down × distance, avec sommes et effectifs) et `play.json` (actions réelles image par image). Entièrement en français, distances en yards.

À l'ouverture, un écran noir présente les logos NFL et AWS de part et d'autre, puis s'ouvre en deux volets (un toucher le passe ; mouvement réduit si le système le demande). Chaque écran est une scène sur un terrain dessiné en SVG, en vue de dessus (2D) ou en caméra inclinée façon retransmission (3D), bouton dans l'en-tête :
- **Adversaire** : une carte par route à attaquer ou à éviter. La carte rejoue l'action réelle de cette défense la plus proche de sa moyenne sur la route : trajectoires mesurées du receveur ciblé et du défenseur le plus proche au lancer (pion au logo de l'équipe), ballon interpolé en ligne droite du passeur au point de chute. Cercle blanc : fenêtre de réception ; cercle jaune : moyenne de la ligue sur la route. L'écart à la ligue est le chiffre en grand.
- **Man/zone** : quatre cibles vues de dessus (man ou zone, passe courte ou profonde) : anneau au lancer, disque à l'arrivée, repère ligue en jaune. Sur tablette / PC, comparaison de deux défenses côte à côte.
- **Matrice** : séparation à l'arrivée par route × couverture pour toute la ligue, filtrable par couverture, profondeur de passe, down et distance à gagner. Chaque filtre ré-agrège les cellules de `matchups.json` par Σ somme / Σ n (jamais une moyenne de moyennes). Couleur et libellé : contesté < 1 yd, serré 1-2, ouvert 2-3, grand ouvert ≥ 3 ; cases grisées sous 10 passes. Une case touchée ouvre sa fiche (part des actions ouvertes / contestées, fenêtre au lancer, intervalle de confiance à 95 %) ; changer un filtre la ferme.
- **Ligue** : les 32 logos posés sur une règle en yards selon leur fenêtre moyenne à l'arrivée.

Téléphone : une colonne, un message par écran, chiffre clé en grand, zones tactiles ≥ 44 px, navigation en bas au pouce, choix de l'équipe par grille de logos. À partir de 768 px : logos à gauche, scène au centre, navigation en haut ; à partir de 1100 px (PC) : l'onglet Adversaire montre tout le plan de match (routes à attaquer et à éviter côte à côte), les autres onglets gardent le plan de jeu à droite, contenu centré sur 1440 px.

### Vidéo de démo (motion design)

`outputs/demo_app.mp4` (1920×1080, H.264, environ 75 s, sans son) : l'app tourne en vrai dans un téléphone et un script la pilote comme un coach ; à côté, des titres animés affichent les métriques **lues dans l'app au moment de l'enregistrement** (aucun chiffre écrit en dur), puis les vérifications tirées de `outputs/rapport_verification.md`. Pour la régénérer (serveur de dev lancé) :

```bash
python video/enregistrer_demo.py --app http://localhost:5173/ --sortie outputs/demo_app.mp4
```

La défense mise en avant est choisie par les données (la carte « à attaquer » la plus marquée parmi celles de confiance élevée). Mise en scène : `video/studio.html` ; capture image par image de Chrome (Playwright), montage ffmpeg.

**Logos et couleurs** : logos NFL et AWS dans `web/public/marques/` (`aws-blanc.svg` : texte passé en blanc pour l'écran noir d'ouverture) ; logos des clubs : table publique nflverse (`data/reference/equipes_nflverse.csv`), jointe par abréviation d'équipe ; le pipeline télécharge les logos dans `web/public/logos/` (non versionné). Les logos sont des marques de la NFL et des clubs, utilisés ici pour identifier les équipes dans un projet de compétition non commercial. Sans réseau, chaque logo est remplacé par un badge aux couleurs de l'équipe.

## La métrique

**Fenêtre de réception** d'une passe, en yards :

```
fenetre_lancer    = distance receveur ciblé <-> défenseur suivi le plus proche, au moment du lancer
fenetre_arrivee   = même distance à l'arrivée du ballon (dernière image du vol)
variation_fenetre = fenetre_arrivee - fenetre_lancer      (< 0 : la défense a refermé pendant le vol)
```

Elle est ensuite moyennée par situation, toujours avec l'effectif et le taux de complétion :

| Fichier | Découpage | Usage coach |
|---|---|---|
| `outputs/fenetres_actions.csv` | une ligne par passe | base de tout, filtrable |
| `outputs/coach_synthese.csv` | man/zone × courte/profonde | message principal |
| `outputs/coach_ligue.csv` | couverture × route (ligue) | heatmap |
| `outputs/coach_equipes.csv` | défense × man/zone × profondeur | fiche adversaire |
| `outputs/coach_equipes_routes.csv` | défense × route | fiche adversaire : routes ouvertes |
| `outputs/coach_situations.csv` | down × distance × man/zone | lecture en contexte |
| `outputs/coach_cartes_telephone.csv` | défense : 3 routes à attaquer, 3 à éviter, phrase prête, niveau de confiance | écrans téléphone, une carte par information |

Hypothèses et limites, à dire au jury :
- Seuls le receveur ciblé et les défenseurs proches du point de chute sont suivis pendant le vol (c'est le jeu de données qui les désigne). La fenêtre mesure donc le défenseur le plus proche parmi eux.
- La fenêtre décrit une situation, pas une cause : elle ne dit pas si c'est la couverture, le placement ou le lancer qui l'explique. Le taux de complétion et l'EPA sont donnés en contexte, pas intégrés à la métrique.
- Une seule saison : les cases peu fournies sont masquées (seuil `n_min`), et les cases par équipe restent petites. Les intervalles de confiance sont dans le rapport de vérification.
- Les passes profondes partent avec une fenêtre plus serrée que les courtes : comparer des situations comparables (même profondeur, même down et distance).

## Vérifications

`outputs/rapport_nettoyage.md` liste chaque correction (actions d'une autre saison sans tracking retirées, action annulée par pénalité retirée, aucun doublon, aucune imputation). `outputs/rapport_verification.md` contient :
- recalcul de la fenêtre par un second chemin (numpy, action par action) : écart nul ;
- recalcul de la case la plus fermée par boucle Python : identique ;
- validité externe : fenêtre à l'arrivée plus petite sur les passes incomplètes et interceptées que sur les complétées ;
- intervalles de confiance bootstrap des 4 cases de synthèse ; stabilité première / seconde moitié de saison (corrélation de rang 0,95) ; sensibilité au seuil de passe profonde ; effet des actions extrêmes (0,99) ; nombre de cases selon le seuil.

## Structure

```
data/raw/        données sources (CSV de la compétition ; le tracking n'est pas versionné)
data/clean/      actions_clean.csv, joueurs_clean.csv, defenseurs_vol_clean.csv
src/nettoyage.py      chargement et nettoyage
src/metrique.py       fenêtre de réception et vues coach
src/verification.py   seconde méthode de calcul et robustesse
src/run_all.py        pipeline complet
src/brief.py          brief visuel généré depuis les CSV
src/export_web.py     export des CSV en JSON pour l'interface
src/logos.py          logos des équipes (table publique nflverse)
data/reference/       equipes_nflverse.csv (noms, couleurs, logos)
web/                  interface React (Vite) : src/App.jsx, src/styles.css, src/data.json, public/contrat/*.json
video/                vidéo de démo : studio.html (mise en scène), enregistrer_demo.py (pilotage + montage)
docs/                 documentation des données
outputs/              CSV de résultats, rapports, brief, captures d'écran
```

## Scénario de démo (2 minutes)

1. Un coordinateur offensif ouvre la fiche de la défense qu'il affronte : en 5 secondes il voit, route par route, où cette défense laisse une fenêtre plus ouverte que la ligue à l'arrivée du ballon, avec l'effectif.
2. Il bascule sur la synthèse man/zone : contre cette défense, les passes courtes en zone arrivent avec une fenêtre de X yd ; il choisit ses routes en conséquence.
3. Le coordinateur défensif regarde la même fiche pour sa propre équipe : la ou les routes où sa défense referme le moins deviennent un thème d'entraînement.

## Note pour le jury (démarche et choix)

Nous avons gardé une seule cible, le coach, et une seule métrique, lisible en une phrase : la distance entre le receveur ciblé et le défenseur le plus proche, au lancer et à l'arrivée du ballon. C'est la seule mesure que ce jeu de données permet mieux que les statistiques classiques, parce qu'il suit les joueurs pendant le vol. Nous la présentons par situation (couverture, route, équipe, down et distance) avec l'effectif et le taux de complétion, jamais seule. Chaque chiffre est recalculé par une seconde méthode, la robustesse est testée, et les limites (sélection des défenseurs suivis, une seule saison, description et non causalité) sont écrites plutôt que cachées. Le code tourne en une commande sur n'importe quelle saison au même format.

## Répartition (équipe de 3)

| Personne | Tâches | Livrables |
|---|---|---|
| 1 — données | nettoyage, CSV propres, rapport de nettoyage, vérification des jointures | `data/clean/`, `outputs/rapport_nettoyage.md` |
| 2 — métrique | formule, calcul, seconde méthode, robustesse, tables coach | `src/metrique.py`, `src/verification.py`, `outputs/*.csv` |
| 3 — visuel et présentation | visuels coach, fiche adversaire, démo, pitch jury | visuels, présentation |

Points de synchronisation : (1) après le nettoyage, validation commune de l'état des lieux ; (2) après le calcul, la Personne 3 reçoit `outputs/brief_visuel.md` ; (3) 30 minutes avant la fin, relecture croisée : chiffres des visuels contre les CSV, mention « Données 2023 », source, unités.

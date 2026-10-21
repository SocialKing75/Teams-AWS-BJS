"""
Génère le brief visuel coach (outputs/brief_visuel.md) à partir des CSV de résultats,
pour que chaque chiffre affiché par la personne qui fait le visuel soit identique
aux fichiers. Usage : python src/brief.py [--equipe KC]  (après run_all.py)
"""
from __future__ import annotations

import argparse
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
SOURCE = "NFL Big Data Bowl 2026, tracking Next Gen Stats"
NOMS = {"n_actions": "Actions", "fenetre_lancer_moy": "Fenêtre au lancer (yd)", "fenetre_arrivee_moy": "Fenêtre à l'arrivée (yd)",
        "variation_fenetre_moy": "Variation (yd)", "taux_completion": "Complétion", "epa_moyen": "EPA moyen",
        "team_coverage_type": "Couverture", "team_coverage_man_zone": "Man / zone", "route_of_targeted_receiver": "Route",
        "profondeur": "Profondeur", "defensive_team": "Défense", "situation_down": "Down", "situation_distance": "Distance",
        "type": "Type", "rang": "Rang", "route": "Route", "ecart_vs_ligue": "Écart vs ligue (yd)", "confiance": "Confiance", "phrase": "Phrase"}


def md(df: pd.DataFrame) -> str:
    """Table Markdown lisible : arrondis à 0,1 yd, complétion en %."""
    df = df.copy()
    for c in ["fenetre_lancer_moy", "fenetre_arrivee_moy", "variation_fenetre_moy"]:
        if c in df:
            df[c] = df[c].round(1)
    if "taux_completion" in df:
        df["taux_completion"] = (df["taux_completion"] * 100).round(0).astype(int).astype(str) + " %"
    if "epa_moyen" in df:
        df["epa_moyen"] = df["epa_moyen"].round(2)
    df = df.rename(columns=NOMS)
    cols = list(df.columns)
    lignes = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in df.itertuples(index=False):
        lignes.append("| " + " | ".join(str(v) for v in r) + " |")
    return "\n".join(lignes)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sorties", default="outputs")
    p.add_argument("--clean", default="data/clean")
    p.add_argument("--equipe", default=None, help="défense adverse pour la fiche exemple (défaut : la plus ouverte)")
    a = p.parse_args()
    lire = lambda n: pd.read_csv(os.path.join(a.sorties, f"{n}.csv"))
    fen, ligue, synth, equipes, eq_routes, situ, cartes = (lire(n) for n in
        ["fenetres_actions", "coach_ligue", "coach_synthese", "coach_equipes", "coach_equipes_routes",
         "coach_situations", "coach_cartes_telephone"])
    saison = "/".join(str(s) for s in sorted(pd.read_csv(os.path.join(a.clean, "actions_clean.csv"), usecols=["saison"]).saison.unique()))

    # Classement des défenses sur la fenêtre à l'arrivée (toutes actions)
    defenses = fen.groupby("defensive_team").agg(n_actions=("play_id", "size"), fenetre_lancer_moy=("fenetre_lancer", "mean"),
                                                 fenetre_arrivee_moy=("fenetre_arrivee", "mean"), variation_fenetre_moy=("variation_fenetre", "mean"),
                                                 taux_completion=("pass_result", lambda s: s.eq("C").mean())).reset_index().sort_values("fenetre_arrivee_moy")
    equipe = a.equipe or defenses.defensive_team.iloc[-1]
    fiche_mz = equipes[equipes.defensive_team == equipe].drop(columns="defensive_team")
    fiche_routes = eq_routes[eq_routes.defensive_team == equipe].drop(columns="defensive_team")
    ligue_routes = fen.groupby("route_of_targeted_receiver").fenetre_arrivee.mean().round(1)
    fiche_routes = fiche_routes.assign(ligue=fiche_routes.route_of_targeted_receiver.map(ligue_routes).values)
    fiche_routes["ecart_vs_ligue"] = (fiche_routes.fenetre_arrivee_moy - fiche_routes.ligue).round(1)
    fiche_routes = fiche_routes.rename(columns={"ligue": "Ligue (yd)", "ecart_vs_ligue": "Écart vs ligue (yd)"}).sort_values("Écart vs ligue (yd)", ascending=False)
    moy_ligue = fen.fenetre_arrivee.mean()

    texte = f"""# Brief visuel coach — Fenêtre de réception — Données {saison}

Généré par `src/brief.py` depuis les CSV de `outputs/` : tout chiffre ci-dessous est identique aux fichiers.

## Titre et message

- **Titre proposé** : « Où la fenêtre de réception reste-t-elle ouverte ? » — sous-titre obligatoire : « Données saison {saison} · méthode réutilisable sur toute saison »
- **Problématique** : dans quelles situations la fenêtre de réception se referme-t-elle le moins entre le lancer et l'arrivée du ballon ?
- **Utilisateur** : un coordinateur offensif qui prépare un adversaire (où attaquer) ou un coordinateur défensif qui s'audite (où l'on fuit).
- **Source à citer sur chaque visuel** : {SOURCE}
- **Mention à afficher** : « Seuls le receveur ciblé et les défenseurs proches du point de chute sont suivis pendant le vol. »

## Définition à faire figurer en une ligne

**Fenêtre de réception** : distance (yd) entre le receveur ciblé et le défenseur le plus proche, au lancer puis à l'arrivée du ballon. Variation négative = la défense a refermé pendant le vol. Moyenne ligue à l'arrivée : {moy_ligue:.1f} yd sur {len(fen)} passes.

## Écrans téléphone (bord de terrain) — défense {equipe}

Une carte = une information, chiffre clé en grand, phrase prête à afficher. Fichier pour les 32 défenses : `outputs/coach_cartes_telephone.csv` (colonne `phrase`). On glisse de carte en carte ; le chiffre clé est l'écart à la ligue (yd), le texte courant donne l'effectif.

{md(cartes[cartes.defensive_team == equipe].drop(columns=["defensive_team", "fenetre_ligue"]))}

## Visuel 1 (message principal) — Man / zone × profondeur, ligue

Visuel recommandé : **4 paires de barres** (fenêtre au lancer, fenêtre à l'arrivée) ou 4 flèches lancer → arrivée. Une seule lecture : le man part serré et bouge peu, la zone part large et referme beaucoup, mais reste plus ouverte à l'arrivée.

{md(synth)}

## Visuel 2 — Heatmap couverture × route (ligue)

Visuel recommandé : **heatmap** sur la fenêtre à l'arrivée, une seule teinte bleue du clair (fermée) au foncé (ouverte), effectif dans chaque case, cases avec moins de 30 actions masquées. Fichier complet : `outputs/coach_ligue.csv` ({len(ligue)} cases).

Les 8 cases les plus fermées à l'arrivée :

{md(ligue.head(8))}

Les 8 cases les plus ouvertes à l'arrivée :

{md(ligue.tail(8))}

## Visuel 3 — Fiche adversaire : défense {equipe}

Visuel recommandé : **barres horizontales par route**, écart à la moyenne ligue (barre vers la droite = fenêtre plus ouverte que la ligue, à attaquer ; vers la gauche = plus fermée, à éviter), effectif affiché, routes avec moins de 15 actions masquées. Paramètre `--equipe XXX` pour une autre défense ; fichiers `outputs/coach_equipes.csv` et `outputs/coach_equipes_routes.csv` pour les 32.

Par man / zone × profondeur :

{md(fiche_mz)}

Par route, écart à la ligue :

{md(fiche_routes)}

## Visuel 4 — Classement des 32 défenses (fenêtre à l'arrivée)

Visuel recommandé : **barres horizontales triées**, trait vertical à la moyenne ligue ({moy_ligue:.1f} yd), défense choisie en couleur forte, les autres en gris.

{md(defenses)}

## Visuel 5 (optionnel) — Situations de jeu

Down × distance × man/zone, pour lire la fenêtre dans son contexte (fichier `outputs/coach_situations.csv`) :

{md(situ.sort_values(["situation_down", "situation_distance", "team_coverage_man_zone"]))}

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
- Unités partout (yd, %), effectif visible sur chaque carte, source et « Données {saison} » en pied de chaque écran.
"""
    chemin = os.path.join(a.sorties, "brief_visuel.md")
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(texte)
    print(f"Brief écrit : {chemin} (fiche adversaire : {equipe})")


if __name__ == "__main__":
    main()

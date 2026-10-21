"""
Pipeline complet en une commande :
    python src/run_all.py --donnees data/raw

1. charge et nettoie les données  -> data/clean/*.csv, outputs/rapport_nettoyage.md
2. calcule la fenêtre de réception de chaque action et les vues coach
   -> outputs/fenetres_actions.csv (une ligne par action, la métrique)
      outputs/coach_ligue.csv (couverture × route), outputs/coach_synthese.csv (man/zone × profondeur)
      outputs/coach_equipes.csv, outputs/coach_equipes_routes.csv (par équipe défensive)
      outputs/coach_situations.csv (down × distance × man/zone)
      outputs/coach_cartes_telephone.csv (par défense : 3 routes à attaquer, 3 à éviter, une phrase)
3. vérifie les chiffres par une seconde méthode et teste la robustesse -> outputs/rapport_verification.md
4. écrit les fichiers du contrat d'équipe -> web/public/contrat/matchups.json, play.json
5. exporte le JSON de l'interface React -> web/src/data.json

Fonctionne avec n'importe quelle saison au même format : rien n'est écrit en dur.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metrique import (cartes_telephone, construire_table_defenseurs, table_coach_equipes,
                      table_coach_equipes_routes, table_coach_ligue, table_coach_situations,
                      table_coach_synthese, table_fenetres)
from contrat import actions_cartes, ecrire, matchups, preparer_situations
from export_web import exporter
from logos import telecharger_logos
from nettoyage import charger_actions, charger_tracking, nettoyer
from verification import recalcul_cellule_boucle, recalcul_numpy, robustesse


def main():
    p = argparse.ArgumentParser(description="Fenêtre de réception : vues coach")
    p.add_argument("--donnees", default="data/raw", help="dossier contenant supplementary_data.csv et train/")
    p.add_argument("--clean", default="data/clean")
    p.add_argument("--sorties", default="outputs")
    p.add_argument("--n-min", type=int, default=30, help="nombre minimal d'actions pour afficher une case ligue")
    p.add_argument("--n-min-equipe", type=int, default=15, help="nombre minimal d'actions pour une case par équipe")
    a = p.parse_args()
    os.makedirs(a.clean, exist_ok=True)
    os.makedirs(a.sorties, exist_ok=True)
    t0 = time.time()

    # --- 1. Nettoyage ---
    actions = charger_actions(a.donnees)
    entree, sortie = charger_tracking(a.donnees)
    print(f"Chargé : {len(actions)} actions, {len(entree)} frames input, {len(sortie)} frames output ({time.time() - t0:.0f} s)")
    actions, entree, sortie, joueurs, rapport = nettoyer(actions, entree, sortie)
    saison = "/".join(str(s) for s in sorted(actions.saison.unique()))
    actions.to_csv(os.path.join(a.clean, "actions_clean.csv"), index=False)
    joueurs.to_csv(os.path.join(a.clean, "joueurs_clean.csv"), index=False)
    with open(os.path.join(a.sorties, "rapport_nettoyage.md"), "w", encoding="utf-8") as f:
        f.write(f"# Rapport de nettoyage — Données {saison}\n\n" + "\n".join(f"- {l}" for l in rapport))
        f.write(f"\n\nActions conservées : {len(actions)} ; matchs : {actions.game_id.nunique()} ; "
                f"équipes : {actions.defensive_team.nunique()} ; joueurs : {len(joueurs)}.\n")
    print("\n".join(rapport))

    # --- 2. Métrique et vues coach ---
    defs = construire_table_defenseurs(entree, sortie, actions)
    defs.to_csv(os.path.join(a.clean, "defenseurs_vol_clean.csv"), index=False)
    fen = table_fenetres(defs)
    fen.to_csv(os.path.join(a.sorties, "fenetres_actions.csv"), index=False)
    vues = {
        "coach_ligue": table_coach_ligue(fen, a.n_min),
        "coach_synthese": table_coach_synthese(fen, a.n_min),
        "coach_equipes": table_coach_equipes(fen, a.n_min_equipe),
        "coach_equipes_routes": table_coach_equipes_routes(fen, a.n_min_equipe),
        "coach_situations": table_coach_situations(fen, a.n_min),
        "coach_cartes_telephone": cartes_telephone(fen, a.n_min_equipe),
    }
    for nom, t in vues.items():
        t.to_csv(os.path.join(a.sorties, f"{nom}.csv"), index=False)
    print(f"\nFenêtre calculée sur {len(fen)} actions ({fen.defensive_team.nunique()} défenses) ; "
          f"{len(vues['coach_ligue'])} cases couverture × route avec n >= {a.n_min}")
    print(vues["coach_synthese"].to_string(index=False))

    # --- 3. Vérification ---
    ecart = recalcul_numpy(entree, sortie, fen)
    c0 = vues["coach_ligue"].iloc[0]
    n1, m1 = recalcul_cellule_boucle(fen, c0.team_coverage_type, c0.route_of_targeted_receiver)
    lignes = [f"Écart max entre pipeline pandas et recalcul numpy sur 300 actions tirées au sort : {ecart:.2e} yard",
              f"Case la plus fermée ({c0.team_coverage_type} × {c0.route_of_targeted_receiver}) recalculée par boucle Python : "
              f"n = {n1} (pipeline {c0.n_actions}), fenêtre à l'arrivée = {m1:.3f} (pipeline {c0.fenetre_arrivee_moy})"]
    assert ecart < 1e-6 and n1 == c0.n_actions and abs(m1 - c0.fenetre_arrivee_moy) < 1e-3
    lignes += robustesse(fen, defs, a.n_min)
    with open(os.path.join(a.sorties, "rapport_verification.md"), "w", encoding="utf-8") as f:
        f.write(f"# Vérification et robustesse — Données {saison}\n\n" + "\n".join(f"- {l}" for l in lignes) + "\n")
    print("\n" + "\n".join(lignes))

    # --- 4. Contrat d'interface de l'équipe (.kiro/specs) : matchups.json et play.json ---
    contrat = os.path.join("web", "public", "contrat")
    m = matchups(fen)
    # Contrôle : toutes les actions éligibles (route en liste blanche, couverture connue) sont dans une cellule
    assert sum(l["n"] for l in m) == len(preparer_situations(fen)), "cellules incomplètes"
    ecrire(m, [os.path.join(a.sorties, "matchups.json"), os.path.join(contrat, "matchups.json")])
    plays = actions_cartes(fen, vues["coach_cartes_telephone"], entree, sortie)
    ecrire(plays, [os.path.join(a.sorties, "play.json"), os.path.join(contrat, "play.json")])

    # --- 5. Logos (table publique nflverse) et export pour l'interface React (web/src/data.json) ---
    telecharger_logos(os.path.join("data", "reference", "equipes_nflverse.csv"),
                      sorted(actions.defensive_team.unique()), os.path.join("web", "public", "logos"))
    exporter(a.sorties, a.clean)
    print(f"\nTerminé en {time.time() - t0:.0f} s. Résultats dans {a.sorties}/")


if __name__ == "__main__":
    main()

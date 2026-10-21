"""
Exporte les résultats (outputs/*.csv) en un seul JSON pour l'interface React :
    python src/export_web.py   ->  web/src/data.json
Aucun chiffre n'est calculé ici : l'interface affiche exactement les CSV.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
SOURCE = "NFL Big Data Bowl 2026, tracking Next Gen Stats"


def infos_equipes(abreviations: list[str], reference: str, logos: str) -> dict:
    """Nom, couleurs et logo local de chaque équipe, joints par abréviation (table nflverse).
    Une équipe absente de la table garde son abréviation et une couleur neutre."""
    ref = pd.read_csv(reference).set_index("team_abbr") if os.path.exists(reference) else pd.DataFrame()
    infos = {}
    for abr in abreviations:
        ligne = ref.loc[abr] if abr in ref.index else None
        infos[abr] = {
            "nom": ligne["team_name"] if ligne is not None else abr,
            "surnom": ligne["team_nick"] if ligne is not None else abr,
            "couleur": ligne["team_color"] if ligne is not None else "#3a3a38",
            "couleur2": ligne["team_color2"] if ligne is not None else "#c3c2b7",
            "logo": f"logos/{abr}.png" if os.path.exists(os.path.join(logos, f"{abr}.png")) else None,
        }
    return infos


def exporter(sorties: str = "outputs", clean: str = os.path.join("data", "clean"),
             web: str = os.path.join("web", "src", "data.json"),
             reference: str = os.path.join("data", "reference", "equipes_nflverse.csv"),
             logos: str = os.path.join("web", "public", "logos")) -> str:
    """Assemble les CSV de résultats en un JSON pour l'interface ; renvoie le chemin écrit."""
    lire = lambda n: pd.read_csv(os.path.join(sorties, f"{n}.csv"))
    fen = lire("fenetres_actions")
    saison = "/".join(str(s) for s in sorted(pd.read_csv(os.path.join(clean, "actions_clean.csv"), usecols=["saison"]).saison.unique()))
    ligue_routes = (fen.groupby("route_of_targeted_receiver")
                    .agg(fenetre_lancer=("fenetre_lancer", "mean"), fenetre_arrivee=("fenetre_arrivee", "mean"), n=("play_id", "size"))
                    .round(2).reset_index().rename(columns={"route_of_targeted_receiver": "route"}))
    classement = (fen.groupby("defensive_team").agg(fenetre=("fenetre_arrivee", "mean"), fenetre_lancer=("fenetre_lancer", "mean"), n=("play_id", "size"))
                  .round(2).reset_index().sort_values("fenetre"))
    donnees = {
        "saison": saison, "source": SOURCE,
        "moy_ligue": round(float(fen.fenetre_arrivee.mean()), 2), "n_passes": int(len(fen)),
        "defenses": sorted(fen.defensive_team.unique().tolist()),
        "cartes": lire("coach_cartes_telephone").to_dict("records"),
        "equipes": lire("coach_equipes").to_dict("records"),
        "synthese": lire("coach_synthese").to_dict("records"),
        "situations": lire("coach_situations").to_dict("records"),
        "ligue": lire("coach_ligue").to_dict("records"),
        "classement": classement.to_dict("records"),
        "ligue_routes": ligue_routes.to_dict("records"),
        "equipes_info": infos_equipes(sorted(fen.defensive_team.unique()), reference, logos),
    }
    os.makedirs(os.path.dirname(web), exist_ok=True)
    with open(web, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False)
    print(f"Export : {web} ({os.path.getsize(web) // 1024} ko)")
    return web


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sorties", default="outputs")
    p.add_argument("--clean", default=os.path.join("data", "clean"))
    p.add_argument("--web", default=os.path.join("web", "src", "data.json"))
    a = p.parse_args()
    exporter(a.sorties, a.clean, a.web)


if __name__ == "__main__":
    main()

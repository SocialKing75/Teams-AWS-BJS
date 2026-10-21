"""
Télécharge en local les logos des équipes présentes dans les données, pour que
l'interface fonctionne sans réseau au bord du terrain :
    python src/logos.py   ->  web/public/logos/<ABR>.png

Source : table publique nflverse (data/reference/equipes_nflverse.csv), autorisée
par le règlement de la compétition. Les logos sont des marques déposées de la NFL
et de ses clubs : usage d'identification dans un projet non commercial, fichiers
non versionnés (voir .gitignore). Aucune équipe n'est écrite en dur : la liste
vient des données de la saison.
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.request

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")


def telecharger_logos(reference: str, abreviations: list[str], dossier: str) -> dict[str, str]:
    """Télécharge le logo de chaque abréviation absente du dossier ; renvoie {abr: chemin relatif}."""
    ref = pd.read_csv(reference).set_index("team_abbr")
    os.makedirs(dossier, exist_ok=True)
    chemins = {}
    for abr in abreviations:
        cible = os.path.join(dossier, f"{abr}.png")
        if not os.path.exists(cible) and abr in ref.index:
            try:
                req = urllib.request.Request(ref.loc[abr, "team_logo_espn"], headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as r, open(cible, "wb") as f:
                    f.write(r.read())
            except OSError as e:  # pas de réseau : l'interface affichera un badge de couleur
                print(f"Logo {abr} non téléchargé : {e}")
        if os.path.exists(cible):
            chemins[abr] = f"logos/{abr}.png"
    return chemins


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--reference", default=os.path.join("data", "reference", "equipes_nflverse.csv"))
    p.add_argument("--actions", default=os.path.join("data", "clean", "actions_clean.csv"))
    p.add_argument("--dossier", default=os.path.join("web", "public", "logos"))
    a = p.parse_args()
    abreviations = sorted(pd.read_csv(a.actions, usecols=["defensive_team"]).defensive_team.unique())
    chemins = telecharger_logos(a.reference, abreviations, a.dossier)
    print(f"Logos disponibles : {len(chemins)} / {len(abreviations)} dans {a.dossier}")


if __name__ == "__main__":
    main()

"""
Problématique (persona coach) : dans quelles situations la fenêtre de réception
se referme-t-elle le moins entre le lancer et l'arrivée du ballon ?

Métrique centrale : la fenêtre de réception d'une action, en yards.
En une phrase : distance entre le receveur ciblé et le défenseur suivi le plus
proche, mesurée au moment du lancer puis à l'arrivée du ballon.

    fenetre_lancer    = min sur les défenseurs suivis de dist(receveur, défenseur) au lancer
    fenetre_arrivee   = même chose à l'arrivée du ballon (dernière frame du vol)
    variation_fenetre = fenetre_arrivee - fenetre_lancer   (< 0 : la défense a refermé)

Vues coach : la fenêtre moyenne par couverture × route (ligue), par équipe
défensive (préparer un adversaire ou s'auditer), et par situation de jeu
(down × distance), toujours avec l'effectif et le taux de complétion.

Hypothèses : les défenseurs suivis pendant le vol sont ceux que fournit le jeu
de données (proches du point de chute) ; le point de chute est commun à toute
l'action. Limites : la fenêtre ne dit pas qui est responsable (couverture ou
placement) ni la qualité du lancer ; le résultat de la passe est donné en
contexte. Une saison seulement : les cases peu fournies sont masquées (n_min).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

CLE = ["game_id", "play_id"]
SEUIL_PROFONDE = 15   # yards de pass_length à partir desquels une passe est "profonde"
# Tranches de yards à gagner (spec reception-window-coach) : partagées par les tables coach et le contrat du front
BORNES_DISTANCE = [0, 3, 6, np.inf]
TRANCHES_DISTANCE = ["1-3", "4-6", "7+"]


def _derniere_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Dernière frame de chaque joueur sur chaque action."""
    return df.sort_values("frame_id").groupby(CLE + ["nfl_id"], as_index=False).tail(1)


def construire_table_defenseurs(entree: pd.DataFrame, sortie: pd.DataFrame, actions: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par (action, défenseur suivi pendant le vol) : distances au receveur au lancer et à l'arrivée."""
    lancer = _derniere_frame(entree)
    arrivee = (_derniere_frame(sortie)
               .rename(columns={"x": "x_arrivee", "y": "y_arrivee"})[CLE + ["nfl_id", "x_arrivee", "y_arrivee"]])

    rec = (lancer[lancer.player_role == "Targeted Receiver"][CLE + ["nfl_id", "x", "y"]]
           .merge(arrivee, on=CLE + ["nfl_id"])
           .rename(columns={"nfl_id": "receveur_id", "x": "x_rec0", "y": "y_rec0",
                            "x_arrivee": "x_rec1", "y_arrivee": "y_rec1"}))

    defs = lancer[(lancer.player_role == "Defensive Coverage") & (lancer.player_to_predict)].copy()
    defs = defs.merge(arrivee, on=CLE + ["nfl_id"]).merge(rec, on=CLE)
    defs["duree_vol_s"] = defs["num_frames_output"] / 10.0
    defs["dist_receveur_lancer"] = np.hypot(defs.x - defs.x_rec0, defs.y - defs.y_rec0)
    defs["dist_receveur_arrivee"] = np.hypot(defs.x_arrivee - defs.x_rec1, defs.y_arrivee - defs.y_rec1)
    defs["dist_ballon_arrivee"] = np.hypot(defs.x_arrivee - defs.ball_land_x, defs.y_arrivee - defs.ball_land_y)

    ctx = actions[CLE + ["defensive_team", "possession_team", "week", "down", "yards_to_go", "pass_result",
                         "pass_length", "team_coverage_man_zone", "team_coverage_type",
                         "route_of_targeted_receiver", "expected_points_added", "play_description"]]
    defs = defs.merge(ctx, on=CLE)
    colonnes = (CLE + ["nfl_id", "player_name", "player_position", "defensive_team", "possession_team", "week",
                       "down", "yards_to_go", "duree_vol_s", "dist_receveur_lancer", "dist_receveur_arrivee",
                       "dist_ballon_arrivee", "pass_result", "pass_length", "team_coverage_man_zone",
                       "team_coverage_type", "route_of_targeted_receiver", "expected_points_added", "play_description"])
    return defs[colonnes].reset_index(drop=True)


def table_fenetres(defs: pd.DataFrame, seuil_profonde: int = SEUIL_PROFONDE) -> pd.DataFrame:
    """
    Une ligne par action : fenêtre de réception au lancer et à l'arrivée, avec le contexte de jeu.

    Définition commune de l'équipe (.kiro/specs/reception-window-coach/design.md §1) :
    le défenseur de référence est le plus proche du receveur ciblé AU LANCER, et on le suit
    jusqu'à l'arrivée. Limite des données : seuls les défenseurs suivis pendant le vol ont une
    position à l'arrivée, le choix se fait donc parmi eux.
    """
    suivi = defs.loc[defs.groupby(CLE)["dist_receveur_lancer"].idxmin()].set_index(CLE)
    f = pd.DataFrame({
        "fenetre_lancer": suivi["dist_receveur_lancer"],
        "fenetre_arrivee": suivi["dist_receveur_arrivee"],
        "defenseur_id": suivi["nfl_id"], "defenseur_nom": suivi["player_name"],
        "defenseur_poste": suivi["player_position"],
        "nb_defenseurs_suivis": defs.groupby(CLE).size(),
        "duree_vol_s": suivi["duree_vol_s"],
        "defensive_team": suivi["defensive_team"], "possession_team": suivi["possession_team"],
        "week": suivi["week"], "down": suivi["down"], "yards_to_go": suivi["yards_to_go"],
        "pass_result": suivi["pass_result"], "pass_length": suivi["pass_length"],
        "team_coverage_man_zone": suivi["team_coverage_man_zone"],
        "team_coverage_type": suivi["team_coverage_type"],
        "route_of_targeted_receiver": suivi["route_of_targeted_receiver"],
        "expected_points_added": suivi["expected_points_added"],
        "play_description": suivi["play_description"],
    }).reset_index()
    f["variation_fenetre"] = f["fenetre_arrivee"] - f["fenetre_lancer"]
    f["profondeur"] = np.where(f.pass_length >= seuil_profonde, f"Profonde (>= {seuil_profonde} yd)", f"Courte (< {seuil_profonde} yd)")
    f["situation_down"] = f["down"].clip(upper=3).map({1: "1er down", 2: "2e down", 3: "3e/4e down"})
    f["situation_distance"] = pd.cut(f.yards_to_go, BORNES_DISTANCE,
                                     labels=[f"{nom} ({t} yd)" for nom, t in zip(["Courte", "Moyenne", "Longue"], TRANCHES_DISTANCE)])
    return f


def _agreger(fen: pd.DataFrame, cles: list[str], n_min: int) -> pd.DataFrame:
    """Moyennes de fenêtre, complétion et EPA par groupe ; masque les groupes sous n_min."""
    g = fen.dropna(subset=cles).groupby(cles, observed=True)
    t = pd.DataFrame({
        "n_actions": g.size(),
        "fenetre_lancer_moy": g["fenetre_lancer"].mean(),
        "fenetre_arrivee_moy": g["fenetre_arrivee"].mean(),
        "variation_fenetre_moy": g["variation_fenetre"].mean(),
        "taux_completion": g["pass_result"].apply(lambda s: s.eq("C").mean()),
        "epa_moyen": g["expected_points_added"].mean(),
    }).reset_index()
    return t[t.n_actions >= n_min].round(3).sort_values("fenetre_arrivee_moy").reset_index(drop=True)


def table_coach_ligue(fen: pd.DataFrame, n_min: int = 30) -> pd.DataFrame:
    """Ligue entière : fenêtre par couverture × route."""
    return _agreger(fen, ["team_coverage_type", "route_of_targeted_receiver"], n_min)


def table_coach_synthese(fen: pd.DataFrame, n_min: int = 30) -> pd.DataFrame:
    """Ligue entière : man/zone × profondeur (4 cases de synthèse)."""
    return _agreger(fen, ["team_coverage_man_zone", "profondeur"], n_min)


def table_coach_equipes(fen: pd.DataFrame, n_min: int = 15) -> pd.DataFrame:
    """Par équipe défensive : man/zone × profondeur, pour préparer un adversaire ou s'auditer."""
    return _agreger(fen, ["defensive_team", "team_coverage_man_zone", "profondeur"], n_min)


def table_coach_equipes_routes(fen: pd.DataFrame, n_min: int = 15) -> pd.DataFrame:
    """Par équipe défensive : quelles routes restent ouvertes à l'arrivée."""
    return _agreger(fen, ["defensive_team", "route_of_targeted_receiver"], n_min)


def table_coach_situations(fen: pd.DataFrame, n_min: int = 30) -> pd.DataFrame:
    """Par situation de jeu (down × distance) et man/zone : ajuste la lecture au contexte."""
    return _agreger(fen, ["situation_down", "situation_distance", "team_coverage_man_zone"], n_min)


def cartes_telephone(fen: pd.DataFrame, n_min: int = 15, n_cartes: int = 3) -> pd.DataFrame:
    """
    Vue téléphone (bord de terrain) : une carte = une information. Pour chaque défense,
    les n_cartes routes où sa fenêtre à l'arrivée est la plus ouverte par rapport à la
    ligue (à attaquer) et les n_cartes les plus fermées (à éviter), avec une phrase courte.
    """
    ligue = fen.groupby("route_of_targeted_receiver").fenetre_arrivee.mean()
    t = table_coach_equipes_routes(fen, n_min).copy()
    t["fenetre_ligue"] = t.route_of_targeted_receiver.map(ligue).round(3)
    t["ecart_vs_ligue"] = (t.fenetre_arrivee_moy - t.fenetre_ligue).round(2)
    cartes = []
    for equipe, g in t.groupby("defensive_team"):
        g = g.sort_values("ecart_vs_ligue", ascending=False)
        for genre, sel in [("attaquer", g[g.ecart_vs_ligue > 0].head(n_cartes)),
                           ("eviter", g[g.ecart_vs_ligue < 0].tail(n_cartes).iloc[::-1])]:
            for rang, r in enumerate(sel.itertuples(), 1):
                # Confiance : effectif et taille de l'écart (une saison, cases par équipe petites)
                if r.n_actions >= 50 and abs(r.ecart_vs_ligue) >= 0.5:
                    confiance = "elevee"
                elif r.n_actions >= 30 and abs(r.ecart_vs_ligue) >= 0.3:
                    confiance = "moyenne"
                else:
                    confiance = "faible"
                cartes.append({
                    "defensive_team": equipe, "type": genre, "rang": rang, "route": r.route_of_targeted_receiver,
                    "n_actions": r.n_actions, "fenetre_lancer_moy": r.fenetre_lancer_moy,
                    "fenetre_arrivee_moy": r.fenetre_arrivee_moy,
                    "fenetre_ligue": r.fenetre_ligue, "ecart_vs_ligue": r.ecart_vs_ligue,
                    "taux_completion": r.taux_completion, "confiance": confiance,
                    "phrase": f"{r.route_of_targeted_receiver} : {r.ecart_vs_ligue:+.1f} yd vs ligue ({r.n_actions} passes, confiance {confiance})",
                })
    return pd.DataFrame(cartes)

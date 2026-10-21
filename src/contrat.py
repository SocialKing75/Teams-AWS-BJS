"""
Fichiers du contrat d'interface de l'équipe (.kiro/specs/*/design.md), lus par le front React :

- matchups.json : une ligne par cellule de situation (couverture × man/zone × route × profondeur
  × down × distance), avec les sommes et n pour ré-agréger côté front (moyenne = Σ sum / Σ n).
  Schéma exact de reception-window-coach/design.md §5, plus deux champs ajoutés pour recalculer
  un intervalle de confiance après filtrage : sum_closing_sq et sum_window_arrival_sq.
- play.json : actions réelles image par image (schéma de mock/play.json), une par carte
  « défense × route » de l'onglet Adversaire, choisie comme la plus représentative de la moyenne.

Toutes les distances sont en yards. Aucune équipe, saison ou chemin n'est écrit en dur.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

CLE = ["game_id", "play_id"]
ROUTES_VALIDES = ["HITCH", "OUT", "FLAT", "CROSS", "GO", "IN", "SLANT", "POST", "ANGLE", "CORNER", "WHEEL", "SCREEN"]
# Libellés de couverture du spec (vocabulaire PFF de la documentation officielle)
COUVERTURES = {"COVER_0_MAN": "Cover-0", "COVER_1_MAN": "Cover-1", "COVER_2_MAN": "2-Man", "COVER_2_ZONE": "Cover-2",
               "COVER_3_ZONE": "Cover-3", "COVER_4_ZONE": "Quarters", "COVER_6_ZONE": "Cover-6", "PREVENT": "Prevent"}
MAN_ZONE = {"MAN_COVERAGE": "Man", "ZONE_COVERAGE": "Zone"}
RESULTATS = {"C": "Passe complète", "I": "Passe incomplète", "IN": "Interception"}
SEUIL_PROFONDE = 15  # yards de pass_length
LONGUEUR, LARGEUR = 120.0, 53.3


def libelle_separation(v: float) -> str:
    """Langage football du spec : Contesté < 1 yd ≤ Serré < 2 ≤ Ouvert < 3 ≤ Grand ouvert."""
    return "Contesté" if v < 1 else "Serré" if v < 2 else "Ouvert" if v < 3 else "Grand ouvert"


def preparer_situations(fen: pd.DataFrame) -> pd.DataFrame:
    """Ajoute les dimensions du contrat ; retire les routes hors liste blanche et les couvertures manquantes."""
    f = fen[fen.route_of_targeted_receiver.isin(ROUTES_VALIDES) & fen.team_coverage_type.isin(COUVERTURES)].copy()
    f["coverage_type"] = f.team_coverage_type.map(COUVERTURES)
    f["man_zone"] = f.team_coverage_man_zone.map(MAN_ZONE)
    f["route"] = f.route_of_targeted_receiver
    f["depth"] = np.where(f.pass_length >= SEUIL_PROFONDE, "deep", "short")
    f["dist_bucket"] = pd.cut(f.yards_to_go, [0, 3, 6, np.inf], labels=["1-3", "4-6", "7+"]).astype(str)
    f["closing"] = f.fenetre_lancer - f.fenetre_arrivee
    return f.dropna(subset=["man_zone"])


def matchups(fen: pd.DataFrame, n_boot: int = 1000, graine: int = 0) -> list[dict]:
    """Une ligne par cellule de situation ; IC 95 % bootstrap sur la fermeture."""
    rng = np.random.default_rng(graine)
    f = preparer_situations(fen)
    lignes = []
    for cles, g in f.groupby(["coverage_type", "man_zone", "route", "depth", "down", "dist_bucket"]):
        n = len(g)
        c = g.closing.to_numpy()
        a = g.fenetre_arrivee.to_numpy()
        boot = rng.choice(c, (n_boot, n), replace=True).mean(axis=1)
        sep = a.mean()
        lignes.append({
            **dict(zip(["coverage_type", "man_zone", "route", "depth", "down", "dist_bucket"], cles)),
            "down": int(cles[4]), "n": n,
            "sum_window_throw": round(float(g.fenetre_lancer.sum()), 3),
            "sum_window_arrival": round(float(a.sum()), 3),
            "sum_closing": round(float(c.sum()), 3),
            "sum_closing_sq": round(float((c ** 2).sum()), 3),
            "sum_window_arrival_sq": round(float((a ** 2).sum()), 3),
            "n_open": int((a >= 3).sum()), "n_contested": int((a < 1).sum()),
            "avg_window_throw": round(float(g.fenetre_lancer.mean()), 2),
            "separation": round(float(sep), 2), "separation_label": libelle_separation(sep),
            "pct_open": round(float((a >= 3).mean()), 3), "pct_contested": round(float((a < 1).mean()), 3),
            "avg_closing": round(float(c.mean()), 2),
            "ci": [round(float(np.percentile(boot, 2.5)), 2), round(float(np.percentile(boot, 97.5)), 2)],
        })
    return lignes


def _normaliser(df: pd.DataFrame, gauche: bool, cols=("x", "y")) -> pd.DataFrame:
    """Oriente l'attaque vers les x croissants (même repère pour toutes les actions)."""
    df = df.copy()
    if gauche:
        df[cols[0]] = LONGUEUR - df[cols[0]]
        df[cols[1]] = LARGEUR - df[cols[1]]
    return df


def _phrase(wt: float, wa: float, duree: float, resultat: str) -> str:
    verbe = "réduite" if wa < wt else "élargie"
    v = lambda x: f"{x:.1f}".replace(".", ",")
    return f"Fenêtre {verbe} de {v(wt)} à {v(wa)} yd en {v(duree)} s — {resultat.lower()}"


def une_action(entree: pd.DataFrame, sortie: pd.DataFrame, ligne: pd.Series) -> dict:
    """Construit une action du contrat play.json à partir du tracking réel."""
    e = entree[(entree.game_id == ligne.game_id) & (entree.play_id == ligne.play_id)]
    s = sortie[(sortie.game_id == ligne.game_id) & (sortie.play_id == ligne.play_id)]
    gauche = e.play_direction.iat[0] == "left"
    e = _normaliser(e, gauche)
    s = _normaliser(s, gauche)
    bx, by = e.ball_land_x.iat[0], e.ball_land_y.iat[0]
    if gauche:
        bx, by = LONGUEUR - bx, LARGEUR - by
    los = e.absolute_yardline_number.iat[0]
    los = LONGUEUR - los if gauche else los
    rec_id = e[e.player_role == "Targeted Receiver"].nfl_id.iat[0]
    der = e.frame_id.max()
    lancer = e[e.frame_id == der].set_index("nfl_id")
    passeur = lancer[lancer.player_role == "Passer"]
    px, py = (passeur.x.iat[0], passeur.y.iat[0]) if len(passeur) else (los - 7, by)
    chemin = lambda nid: [[round(r.x, 2), round(r.y, 2)] for r in e[e.nfl_id == nid].sort_values("frame_id").iloc[::2].itertuples()]
    vol = {nid: g.sort_values("frame_id") for nid, g in s[s.nfl_id.isin([rec_id, ligne.defenseur_id])].groupby("nfl_id")}
    n = len(vol[rec_id])
    frames = [{"t": 0.0, "receiver": [round(lancer.loc[rec_id, "x"], 2), round(lancer.loc[rec_id, "y"], 2)],
               "defender": [round(lancer.loc[ligne.defenseur_id, "x"], 2), round(lancer.loc[ligne.defenseur_id, "y"], 2)],
               "ball": [round(px, 2), round(py, 2)]}]
    for k in range(n):
        r, d = vol[rec_id].iloc[k], vol[ligne.defenseur_id].iloc[k]
        frac = (k + 1) / n   # ballon interpolé en ligne droite du passeur au point de chute
        frames.append({"t": round((k + 1) / 10, 1), "receiver": [round(r.x, 2), round(r.y, 2)],
                       "defender": [round(d.x, 2), round(d.y, 2)],
                       "ball": [round(px + (bx - px) * frac, 2), round(py + (by - py) * frac, 2)]})
    serie = [round(float(np.hypot(f["receiver"][0] - f["defender"][0], f["receiver"][1] - f["defender"][1])), 2) for f in frames]
    resultat = RESULTATS.get(ligne.pass_result, ligne.pass_result)
    return {
        "game_id": int(ligne.game_id), "play_id": int(ligne.play_id), "play_description": ligne.play_description,
        "coverage_type": COUVERTURES.get(ligne.team_coverage_type, ligne.team_coverage_type), "route": ligne.route_of_targeted_receiver,
        "down": int(ligne.down), "yards_to_go": int(ligne.yards_to_go), "flight_time": round(float(ligne.duree_vol_s), 1),
        "window_throw": round(float(ligne.fenetre_lancer), 2), "window_arrival": round(float(ligne.fenetre_arrivee), 2),
        "window_series": serie, "frames": frames, "ball_land": [round(bx, 2), round(by, 2)],
        "result": resultat, "sentence": _phrase(ligne.fenetre_lancer, ligne.fenetre_arrivee, ligne.duree_vol_s, resultat),
        # Champs ajoutés au mock : contexte et trajectoires réelles avant le lancer
        "defensive_team": ligne.defensive_team, "possession_team": ligne.possession_team, "week": int(ligne.week),
        "defender_name": ligne.defenseur_nom, "defender_position": ligne.defenseur_poste,
        "receiver_name": e[e.nfl_id == rec_id].player_name.iat[0], "los_x": round(float(los), 2),
        "receiver_path": chemin(rec_id), "defender_path": chemin(ligne.defenseur_id), "passer": [round(px, 2), round(py, 2)],
        "ball_interpolated": True,
    }


def actions_cartes(fen: pd.DataFrame, cartes: pd.DataFrame, entree: pd.DataFrame, sortie: pd.DataFrame) -> list[dict]:
    """Pour chaque carte défense × route, l'action réelle la plus proche de la fenêtre moyenne à l'arrivée."""
    plays = []
    for c in cartes.drop_duplicates(["defensive_team", "route"]).itertuples():
        cand = fen[(fen.defensive_team == c.defensive_team) & (fen.route_of_targeted_receiver == c.route)
                   & fen.duree_vol_s.between(0.5, 3.0)]
        if cand.empty:
            continue
        ligne = cand.iloc[(cand.fenetre_arrivee - c.fenetre_arrivee_moy).abs().argsort().iat[0]]
        plays.append(une_action(entree, sortie, ligne))
    return plays


def ecrire(objet, chemins: list[str]) -> None:
    for chemin in chemins:
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(objet, f, ensure_ascii=False)
        print(f"Contrat écrit : {chemin} ({os.path.getsize(chemin) // 1024} ko)")

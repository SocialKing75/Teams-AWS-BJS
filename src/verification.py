"""
Vérifications par une seconde méthode et tests de robustesse de la fenêtre de réception.

Chaque chiffre clé est recalculé par un chemin indépendant (numpy ligne à ligne,
sans groupby) et comparé au pipeline pandas. Les tests produisent des lignes de rapport.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from metrique import table_coach_ligue, table_fenetres


def recalcul_numpy(entree: pd.DataFrame, sortie: pd.DataFrame, fen: pd.DataFrame, n: int = 300) -> float:
    """Recalcule la fenêtre au lancer et à l'arrivée sur n actions tirées au sort ; renvoie l'écart max."""
    ecarts = []
    for r in fen.sample(n, random_state=0).itertuples():
        e = entree[(entree.game_id == r.game_id) & (entree.play_id == r.play_id)]
        s = sortie[(sortie.game_id == r.game_id) & (sortie.play_id == r.play_id)]
        e0 = e[e.frame_id == e.frame_id.max()].set_index("nfl_id")                   # lancer
        s1 = s.sort_values("frame_id").groupby("nfl_id").tail(1).set_index("nfl_id")  # arrivée
        rec = e0[e0.player_role == "Targeted Receiver"].index[0]
        defs = e0[(e0.player_role == "Defensive Coverage") & e0.player_to_predict].index
        dist0 = {d: np.sqrt((e0.loc[d, "x"] - e0.loc[rec, "x"]) ** 2 + (e0.loc[d, "y"] - e0.loc[rec, "y"]) ** 2) for d in defs}
        suivi = min(dist0, key=dist0.get)   # plus proche au lancer, suivi jusqu'à l'arrivée
        f0 = dist0[suivi]
        f1 = np.sqrt((s1.loc[suivi, "x"] - s1.loc[rec, "x"]) ** 2 + (s1.loc[suivi, "y"] - s1.loc[rec, "y"]) ** 2)
        ecarts.append(max(abs(f0 - r.fenetre_lancer), abs(f1 - r.fenetre_arrivee), abs(len(defs) - r.nb_defenseurs_suivis)))
    return max(ecarts)


def recalcul_cellule_boucle(fen: pd.DataFrame, couverture: str, route: str) -> tuple[int, float]:
    """Recalcule une case couverture × route avec une boucle Python explicite."""
    total, n = 0.0, 0
    for r in fen.itertuples():
        if r.team_coverage_type == couverture and r.route_of_targeted_receiver == route:
            total += r.fenetre_arrivee
            n += 1
    return n, total / n


def robustesse(fen: pd.DataFrame, defs: pd.DataFrame, n_min: int, graine: int = 0) -> list[str]:
    """Tests de robustesse ; renvoie des lignes de rapport."""
    lignes = []
    rng = np.random.default_rng(graine)
    cles = ["team_coverage_type", "route_of_targeted_receiver"]

    # 1. Validité externe : la fenêtre à l'arrivée est-elle plus petite quand la passe échoue ?
    par_res = fen.groupby("pass_result").fenetre_arrivee.mean().round(2).to_dict()
    lignes.append(f"Fenêtre moyenne à l'arrivée par résultat (C = complète, I = incomplète, IN = interceptée) : {par_res} yd")

    # 2. Intervalles de confiance bootstrap des 4 cases de synthèse (man/zone × profondeur)
    ic = {}
    for (mz, prof), grp in fen.dropna(subset=["team_coverage_man_zone"]).groupby(["team_coverage_man_zone", "profondeur"]):
        v = grp.fenetre_arrivee.to_numpy()
        moy = [rng.choice(v, len(v), replace=True).mean() for _ in range(500)]
        ic[f"{mz} / {prof}"] = (round(float(np.percentile(moy, 2.5)), 2), round(float(np.percentile(moy, 97.5)), 2))
    lignes.append(f"IC 95 % bootstrap (500 tirages) de la fenêtre à l'arrivée, cases de synthèse : {ic}")

    # 3. Stabilité temporelle : première moitié de saison contre seconde, sur les cases couverture × route
    mediane = fen.week.median()
    a = table_coach_ligue(fen[fen.week <= mediane], n_min).set_index(cles)
    b = table_coach_ligue(fen[fen.week > mediane], n_min).set_index(cles)
    commun = a.index.intersection(b.index)
    rho = spearmanr(a.loc[commun, "fenetre_arrivee_moy"], b.loc[commun, "fenetre_arrivee_moy"]).statistic
    lignes.append(f"Stabilité première / seconde moitié de saison : {len(commun)} cases communes, corrélation de rang {rho:.3f}")

    # 4. Sensibilité au seuil de passe profonde (10, 15, 20 yd) : l'ordre man < zone tient-il ?
    for seuil in [10, 15, 20]:
        t = table_fenetres(defs, seuil).groupby(["team_coverage_man_zone", "profondeur"]).fenetre_arrivee.mean().round(2)
        lignes.append(f"Seuil passe profonde = {seuil} yd, fenêtre à l'arrivée : {t.to_dict()}")

    # 5. Valeurs extrêmes : fenêtres > 15 yd (receveur isolé, scramble) et vols > 3 s
    ext = (fen.fenetre_arrivee > 15) | (fen.duree_vol_s > 3)
    sans = table_coach_ligue(fen[~ext], n_min).set_index(cles)
    avec = table_coach_ligue(fen, n_min).set_index(cles)
    commun = avec.index.intersection(sans.index)
    rho_ext = spearmanr(avec.loc[commun, "fenetre_arrivee_moy"], sans.loc[commun, "fenetre_arrivee_moy"]).statistic
    lignes.append(f"Actions extrêmes (fenêtre > 15 yd ou vol > 3 s) : {int(ext.sum())} ({ext.mean() * 100:.1f} %) ; "
                  f"corrélation de rang des cases sans elles : {rho_ext:.3f}")

    # 6. Petits échantillons : nombre de cases selon le seuil
    tailles = {n: len(table_coach_ligue(fen, n)) for n in [15, 30, 50]}
    lignes.append(f"Cases couverture × route retenues selon n_min : {tailles}")
    return lignes

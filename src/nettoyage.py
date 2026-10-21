"""
Chargement et nettoyage des données de tracking NFL (format Big Data Bowl 2026).

Trois sources :
- supplementary_data.csv : une ligne par action de passe (contexte, résultat, EPA...)
- train/input_*.csv     : tracking (10 images/s) de chaque joueur avant le lancer
- train/output_*.csv    : positions pendant le vol du ballon des joueurs "à prédire"

Aucun chemin, année ou nom d'équipe n'est écrit en dur : on passe un dossier
contenant ces fichiers et tout est déduit du contenu.
"""
from __future__ import annotations

import glob
import os

import pandas as pd

LARGEUR_TERRAIN = 53.3    # yards
LONGUEUR_TERRAIN = 120.0  # yards, zones d'en-but comprises
IMAGES_PAR_SECONDE = 10
CLE = ["game_id", "play_id"]


def charger_actions(dossier: str) -> pd.DataFrame:
    """Charge la table des actions (une ligne par passe)."""
    df = pd.read_csv(os.path.join(dossier, "supplementary_data.csv"), na_values=["NA"], low_memory=False)
    df["game_date"] = pd.to_datetime(df["game_date"], format="%m/%d/%Y")
    # play_action est lu en texte à cause des NA : on le ramène en booléen
    df["play_action"] = df["play_action"].map({"True": True, "False": False, True: True, False: False})
    return df


def _concatener(motif: str) -> pd.DataFrame:
    """Concatène tous les CSV correspondant à un motif (ex. input_*.csv)."""
    fichiers = sorted(glob.glob(motif))
    if not fichiers:
        raise FileNotFoundError(f"Aucun fichier pour le motif {motif}")
    return pd.concat((pd.read_csv(f, engine="pyarrow") for f in fichiers), ignore_index=True)


def charger_tracking(dossier: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Charge le tracking avant lancer (input) et pendant le vol (output)."""
    entree = _concatener(os.path.join(dossier, "train", "input_*.csv"))
    sortie = _concatener(os.path.join(dossier, "train", "output_*.csv"))
    return entree, sortie


def taille_en_cm(taille: pd.Series) -> pd.Series:
    """Convertit une taille 'pieds-pouces' (ex. '6-1') en centimètres."""
    parts = taille.str.split("-", expand=True).astype(int)
    return ((parts[0] * 12 + parts[1]) * 2.54).round(1)


def nettoyer(actions: pd.DataFrame, entree: pd.DataFrame, sortie: pd.DataFrame):
    """
    Nettoie les trois tables sans rien inventer.

    Retourne (actions_propres, entree_propre, sortie_propre, joueurs, rapport)
    où rapport est une liste de phrases décrivant chaque correction.
    """
    rapport: list[str] = []

    # 1. Actions sans tracking (ex. actions d'une autre saison livrées par erreur)
    cles_tracking = entree[CLE].drop_duplicates()
    avant = len(actions)
    test = actions.merge(cles_tracking, on=CLE, how="left", indicator=True)
    saisons_retirees = sorted(test.loc[test["_merge"] == "left_only", "season"].unique().tolist())
    actions = actions.merge(cles_tracking, on=CLE, how="inner")
    rapport.append(f"Actions sans tracking associé retirées : {avant - len(actions)} sur {avant} "
                   f"(saisons concernées : {saisons_retirees}).")

    # 2. Actions annulées par pénalité : le résultat ne compte pas
    annulees = actions["play_nullified_by_penalty"].eq("Y")
    rapport.append(f"Actions annulées par pénalité retirées : {int(annulees.sum())}.")
    actions = actions[~annulees].copy()

    # 3. Doublons
    dup = int(actions.duplicated(CLE).sum())
    actions = actions.drop_duplicates(CLE)
    dup_e = int(entree.duplicated(CLE + ["nfl_id", "frame_id"]).sum())
    dup_s = int(sortie.duplicated(CLE + ["nfl_id", "frame_id"]).sum())
    entree = entree.drop_duplicates(CLE + ["nfl_id", "frame_id"])
    sortie = sortie.drop_duplicates(CLE + ["nfl_id", "frame_id"])
    rapport.append(f"Doublons supprimés : {dup} actions, {dup_e} frames input, {dup_s} frames output.")

    # 4. On aligne le tracking sur les actions conservées
    entree = entree.merge(actions[CLE], on=CLE)
    sortie = sortie.merge(actions[CLE], on=CLE)

    # 5. Valeurs aberrantes : signalées, conservées (sans impact sur la métrique)
    hors = int(((sortie.x < 0) | (sortie.x > LONGUEUR_TERRAIN) | (sortie.y < 0) | (sortie.y > LARGEUR_TERRAIN)).sum())
    rapport.append(f"Frames output hors terrain conservées (joueur en sortie de limites) : {hors}.")
    rapport.append(f"Frames input avec accélération > 15 yd/s² (bruit capteur probable) conservées : {int((entree.a > 15).sum())}.")

    # 6. Valeurs manquantes signalées (aucune imputation)
    for col in ["team_coverage_type", "route_of_targeted_receiver", "pass_location_type"]:
        rapport.append(f"Valeurs manquantes conservées dans {col} : {int(actions[col].isna().sum())}.")

    # 7. Colonnes dérivées lisibles
    vol = entree.drop_duplicates(CLE)[CLE + ["num_frames_output"]]
    actions = actions.merge(vol, on=CLE)
    actions["duree_vol_s"] = actions["num_frames_output"] / IMAGES_PAR_SECONDE
    actions["saison"] = actions["season"]

    # 8. Dictionnaire joueurs (un nfl_id = une identité, vérifié)
    joueurs = (entree.drop_duplicates("nfl_id")
               [["nfl_id", "player_name", "player_position", "player_height", "player_weight", "player_birth_date"]]
               .copy())
    joueurs["taille_cm"] = taille_en_cm(joueurs["player_height"])
    joueurs["poids_kg"] = (joueurs["player_weight"] * 0.4536).round(1)
    incoh = int((entree.groupby("nfl_id")["player_name"].nunique() > 1).sum())
    homonymes = int((joueurs.groupby("player_name")["nfl_id"].nunique() > 1).sum())
    rapport.append(f"Identifiants joueurs avec plusieurs noms : {incoh} ; homonymes distingués par nfl_id : {homonymes}.")

    return actions, entree, sortie, joueurs, rapport

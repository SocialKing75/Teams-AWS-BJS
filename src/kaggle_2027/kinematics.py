"""Fonctions cinématiques pures, réutilisables et testables.

Opèrent sur des tableaux NumPy (aucune dépendance aux I/O ni à pandas), afin
d'être facilement couvertes par des tests unitaires (distance euclidienne,
accélération signée, lissage, extraction de features d'instance de drill).
"""

from __future__ import annotations

import numpy as np


def euclidean(x1: float, y1: float, x2: float, y2: float) -> float:
    """Distance euclidienne entre deux points (yards)."""
    return float(np.hypot(x1 - x2, y1 - y2))


def smooth(values: np.ndarray, window: int) -> np.ndarray:
    """Moyenne glissante centrée (bords gérés), pour atténuer le bruit capteur.

    ``window <= 1`` renvoie les valeurs inchangées. Longueur préservée.
    """
    values = np.asarray(values, dtype=float)
    if window <= 1 or values.size < window:
        return values.copy()
    kernel = np.ones(window) / window
    pad = window // 2
    padded = np.pad(values, pad, mode="edge")
    smoothed = np.convolve(padded, kernel, mode="same")
    return smoothed[pad : pad + values.size]


def signed_acceleration(speed: np.ndarray, time_s: np.ndarray) -> np.ndarray:
    """Accélération longitudinale **signée** (yd/s²) dérivée de la vitesse.

    La colonne ``a`` du dataset est une magnitude (toujours ≥ 0) ; pour
    distinguer accélération et freinage on dérive la vitesse par rapport au
    temps (``np.gradient``, robuste à un pas non constant).
    """
    speed = np.asarray(speed, dtype=float)
    time_s = np.asarray(time_s, dtype=float)
    if speed.size < 2:
        return np.zeros_like(speed)
    return np.gradient(speed, time_s)


def motion_start_index(speed: np.ndarray, threshold: float) -> int:
    """Indice de la première frame dépassant ``threshold`` (début de mouvement).

    Renvoie 0 si aucune frame ne dépasse le seuil.
    """
    speed = np.asarray(speed, dtype=float)
    above = np.flatnonzero(speed > threshold)
    return int(above[0]) if above.size else 0


def path_length(dis: np.ndarray) -> float:
    """Longueur de trajectoire parcourue (somme des distances par frame)."""
    return float(np.nansum(np.asarray(dis, dtype=float)))


def net_displacement(x: np.ndarray, y: np.ndarray) -> float:
    """Déplacement net (ligne droite) entre la première et la dernière frame."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    return euclidean(x[0], y[0], x[-1], y[-1])


def window_creation(separation_at_arrival: float, separation_at_throw: float) -> float:
    """Création de fenêtre = séparation à l'arrivée − séparation au lancer."""
    return float(separation_at_arrival) - float(separation_at_throw)

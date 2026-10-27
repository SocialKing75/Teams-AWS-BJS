"""Phase 3 — Features capteurs du Combine (par joueur WR).

Extrait, depuis ``combine_tracking`` (10 Hz), des features robustes et
défendables pour les trois drills chronométrés :

* **40-yard dash** : vitesse de pointe, accélération initiale, temps pour
  atteindre la pointe, vitesse au split de 10 yards.
* **20-yard shuttle** : freinage maximal, temps de transition de virage,
  réaccélération de sortie, vitesse minimale au virage.
* **3-cone** : maintien de vitesse, efficacité de trajectoire (tightness des
  virages), freinage maximal.

Choix méthodologiques (documentés) :

* ``a`` du dataset est une magnitude ≥ 0 → l'accélération **signée** (et donc
  le freinage) est dérivée de la vitesse (``kinematics.signed_acceleration``).
* lissage léger (``SMOOTH_WINDOW_FRAMES``) avant dérivation.
* plusieurs essais par joueur → agrégation par **médiane** des features
  d'instance (robuste au bruit, sans avoir à définir un « meilleur » essai).
* ``turn_transition_time`` n'est **pas** un temps de contact au sol : le
  tracking ne mesure pas les pieds. C'est la durée passée sous une fraction de
  la vitesse de pointe autour du virage principal.

Export : ``outputs/kaggle_2027/combine_wr_features.csv`` (une ligne / joueur).

Exécution ::

    python -m src.kaggle_2027.combine_features
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

try:
    from . import config, kinematics
except ImportError:  # exécution directe
    import config  # type: ignore[no-redef]
    import kinematics  # type: ignore[no-redef]

# Colonnes de features exposées par drill (préfixe -> liste de features).
_DRILL_OUTPUTS: dict[str, tuple[str, list[str]]] = {
    "FORTY_YARD_DASH": (
        "forty",
        ["peak_speed", "initial_acceleration", "time_to_peak_speed", "speed_at_split"],
    ),
    "SHORT_SHUTTLE": (
        "shuttle",
        ["peak_deceleration", "turn_transition_time", "exit_acceleration", "min_turn_speed"],
    ),
    "THREE_CONE_DRILL": (
        "threecone",
        ["speed_retention", "path_efficiency", "peak_deceleration", "min_turn_speed"],
    ),
}


# ---------------------------------------------------------------------------
# Features d'une instance de drill
# ---------------------------------------------------------------------------


def instance_features(instance: pd.DataFrame) -> Optional[dict[str, float]]:
    """Calcule les features cinématiques d'une instance de drill triée par temps.

    ``instance`` doit contenir les colonnes ``time`` (datetime), ``x``, ``y``,
    ``s``, ``dis``. Renvoie ``None`` si l'instance est trop courte.
    """
    if len(instance) < config.MIN_INSTANCE_FRAMES:
        return None

    t = (instance["time"] - instance["time"].iloc[0]).dt.total_seconds().to_numpy()
    s_raw = instance["s"].to_numpy(dtype=float)
    s = kinematics.smooth(s_raw, config.SMOOTH_WINDOW_FRAMES)
    x = instance["x"].to_numpy(dtype=float)
    y = instance["y"].to_numpy(dtype=float)
    dis = instance["dis"].to_numpy(dtype=float)

    accel = kinematics.signed_acceleration(s, t)
    peak_speed = float(np.max(s))
    start = kinematics.motion_start_index(s, config.MOTION_START_SPEED)

    # Temps pour atteindre la vitesse de pointe depuis le début de mouvement.
    peak_idx = int(np.argmax(s))
    time_to_peak = float(max(t[peak_idx] - t[start], 0.0))

    # Accélération initiale : pente de vitesse sur la 1re fenêtre après départ.
    init_end = t[start] + config.INITIAL_ACCEL_WINDOW_S
    window_mask = (t >= t[start]) & (t <= init_end)
    if window_mask.sum() >= 2:
        dt_win = t[window_mask][-1] - t[window_mask][0]
        ds_win = s[window_mask][-1] - s[window_mask][0]
        initial_acceleration = float(ds_win / dt_win) if dt_win > 0 else np.nan
    else:
        initial_acceleration = np.nan

    # Vitesse au split (distance cumulée >= SPLIT_DISTANCE_YD).
    cum_dist = np.nancumsum(dis)
    split_mask = np.flatnonzero(cum_dist >= config.SPLIT_DISTANCE_YD)
    speed_at_split = float(s[split_mask[0]]) if split_mask.size else np.nan

    # Région centrale (hors bords) pour les minima de virage.
    k = config.EDGE_FRAMES
    core = slice(k, len(s) - k) if len(s) > 2 * k else slice(0, len(s))
    s_core = s[core]
    min_turn_speed = float(np.min(s_core)) if s_core.size else np.nan

    # Transition de virage : durée sous TURN_SPEED_FRACTION * peak, autour du min.
    turn_transition_time = _turn_transition_time(t, s, peak_speed, core)

    # Réaccélération de sortie : max d'accélération signée après le min central.
    if s_core.size:
        min_core_idx = int(np.argmin(s_core)) + (core.start or 0)
        exit_acceleration = (
            float(np.max(accel[min_core_idx:])) if min_core_idx < len(accel) else np.nan
        )
    else:
        exit_acceleration = np.nan

    peak_deceleration = float(-np.min(accel)) if accel.size else np.nan  # magnitude
    mean_speed = float(np.mean(s))
    speed_retention = float(mean_speed / peak_speed) if peak_speed > 0 else np.nan
    plen = kinematics.path_length(dis)
    ndisp = kinematics.net_displacement(x, y)
    path_efficiency = float(ndisp / plen) if plen > 0 else np.nan

    return {
        "peak_speed": peak_speed,
        "initial_acceleration": initial_acceleration,
        "time_to_peak_speed": time_to_peak,
        "speed_at_split": speed_at_split,
        "peak_deceleration": peak_deceleration,
        "turn_transition_time": turn_transition_time,
        "exit_acceleration": exit_acceleration,
        "min_turn_speed": min_turn_speed,
        "speed_retention": speed_retention,
        "path_efficiency": path_efficiency,
    }


def _turn_transition_time(
    t: np.ndarray, s: np.ndarray, peak_speed: float, core: slice
) -> float:
    """Durée (s) passée sous ``TURN_SPEED_FRACTION * peak`` autour du virage.

    On localise le minimum de vitesse central, puis on étend de part et d'autre
    tant que la vitesse reste sous le seuil. Proxy de la lenteur imposée par le
    changement de direction — **pas** un temps de contact au sol.
    """
    s_core = s[core]
    if s_core.size == 0 or peak_speed <= 0:
        return np.nan
    threshold = config.TURN_SPEED_FRACTION * peak_speed
    offset = core.start or 0
    center = int(np.argmin(s_core)) + offset
    if s[center] >= threshold:
        return 0.0
    left = center
    while left - 1 >= 0 and s[left - 1] < threshold:
        left -= 1
    right = center
    while right + 1 < len(s) and s[right + 1] < threshold:
        right += 1
    return float(t[right] - t[left])


# ---------------------------------------------------------------------------
# Agrégation par joueur
# ---------------------------------------------------------------------------


def _load_wr_tracking(source: config.DataSource, player_ids: set[int]) -> pd.DataFrame:
    """Charge le tracking Combine des joueurs voulus, drills chrono, PLAYER."""
    frame = source.read_csv("combine_tracking")
    mask = (
        frame["nfl_id"].isin(player_ids)
        & (frame["entity_type"] == "PLAYER")
        & frame["drill_type"].isin(config.COMBINE_STOPWATCH_DRILLS)
    )
    frame = frame.loc[mask].copy()
    frame["time"] = pd.to_datetime(frame["time"])
    return frame


def player_drill_features(tracking: pd.DataFrame) -> pd.DataFrame:
    """Features médianes par (joueur, drill), une ligne par combinaison."""
    rows: list[dict[str, float]] = []
    group_keys = ["nfl_id", "drill_type", "event_id", "attempt"]
    for (nfl_id, drill, _event, _attempt), inst in tracking.groupby(group_keys, sort=False):
        feats = instance_features(inst.sort_values("time"))
        if feats is None:
            continue
        feats.update(nfl_id=int(nfl_id), drill_type=drill)
        rows.append(feats)

    if not rows:
        return pd.DataFrame()

    per_instance = pd.DataFrame(rows)
    feature_cols = [c for c in per_instance.columns if c not in ("nfl_id", "drill_type")]
    aggregated = (
        per_instance.groupby(["nfl_id", "drill_type"])[feature_cols]
        .median()
        .reset_index()
    )
    # Nombre d'instances exploitées (transparence).
    counts = (
        per_instance.groupby(["nfl_id", "drill_type"]).size().rename("n_instances")
    )
    return aggregated.merge(counts, on=["nfl_id", "drill_type"])


def assemble_wide(per_drill: pd.DataFrame) -> pd.DataFrame:
    """Transforme les features (joueur, drill) en une ligne par joueur."""
    if per_drill.empty:
        return pd.DataFrame(columns=["nfl_id"])
    out: Optional[pd.DataFrame] = None
    for drill, (prefix, features) in _DRILL_OUTPUTS.items():
        sub = per_drill[per_drill["drill_type"] == drill]
        if sub.empty:
            continue
        cols = {f: f"{prefix}_{f}" for f in features}
        cols["n_instances"] = f"{prefix}_n_instances"
        sub = sub[["nfl_id", *features, "n_instances"]].rename(columns=cols)
        out = sub if out is None else out.merge(sub, on="nfl_id", how="outer")
    return out if out is not None else pd.DataFrame(columns=["nfl_id"])


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


def _wr_cohort_ids(out_dir: Path) -> tuple[set[int], pd.DataFrame]:
    """Charge la cohorte Phase 2 filtrée sur ``nfl_position == WR``."""
    cohort_path = out_dir / "wr_cohort.csv"
    if not cohort_path.is_file():
        raise FileNotFoundError(
            f"Cohorte introuvable : {cohort_path}. Lancer d'abord build_cohort."
        )
    cohort = pd.read_csv(cohort_path)
    cohort = cohort[cohort["nfl_position"] == config.WR_NFL_POSITION].copy()
    return set(cohort["nfl_id"].tolist()), cohort


def run() -> Path:
    """Calcule et exporte les features Combine pour la cohorte WR."""
    logger = config.get_logger("kaggle_2027.combine_features")
    source = config.DataSource.discover()
    out_dir = config.ensure_output_dir()

    player_ids, cohort = _wr_cohort_ids(out_dir)
    logger.info("Cohorte WR (nfl_position==WR) : %d joueurs", len(player_ids))

    tracking = _load_wr_tracking(source, player_ids)
    logger.info("Lignes de tracking retenues : %d", len(tracking))

    per_drill = player_drill_features(tracking)
    wide = assemble_wide(per_drill)

    # Une ligne par joueur de la cohorte (features NaN si drill absent).
    result = cohort[["nfl_id", "display_name", "draft_year"]].merge(
        wide, on="nfl_id", how="left"
    )

    csv_path = out_dir / "combine_wr_features.csv"
    result.to_csv(csv_path, index=False)
    logger.info("Features écrites : %s (%d joueurs)", csv_path, len(result))

    # Résumé console : couverture par drill.
    print(f"\nCohorte WR : {len(result)} joueurs")
    for drill, (prefix, _features) in _DRILL_OUTPUTS.items():
        col = f"{prefix}_peak_speed" if f"{prefix}_peak_speed" in result else None
        if col is None:
            # drills sans peak_speed exposé : prendre la 1re feature du préfixe
            cand = [c for c in result.columns if c.startswith(prefix + "_")]
            col = cand[0] if cand else None
        n = int(result[col].notna().sum()) if col else 0
        print(f"  {drill:18s} : {n} joueurs avec features")
    return csv_path


if __name__ == "__main__":
    run()

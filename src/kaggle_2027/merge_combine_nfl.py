"""Phase 6 — Jointure Combine ↔ NFL (dataset analytique).

Assemble, sur la clé **`nfl_id`**, une table au niveau **action NFL** où chaque
ligne porte :

* l'identité joueur (`player`, `combine_year`) ;
* les mesures Combine **traditionnelles** (chronomètre / mensurations) ;
* les features **capteurs** du Combine (Phase 3) ;
* le contexte et l'outcome NFL (Phase 4) : route, famille, couverture, saison,
  `separation_at_throw`, `separation_created`.

Les métriques abandonnées en Phase 4 (`separation_at_arrival`,
`window_creation`, `separation_auc`) ne figurent pas : non calculables de façon
valide (cf. `docs/kaggle_2027_methodology.md`).

Export : ``outputs/kaggle_2027/combine_nfl_wr_dataset.parquet`` (Parquet, adapté
aux datasets analytiques et aux types mixtes).

Exécution ::

    python -m src.kaggle_2027.merge_combine_nfl
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from . import config
except ImportError:  # exécution directe
    import config  # type: ignore[no-redef]


def load_player_combine(source: config.DataSource, out_dir: Path) -> pd.DataFrame:
    """Table niveau joueur : identité + Combine traditionnel + capteurs.

    Fusionne ``combine_results`` (traditionnel) et ``combine_wr_features.csv``
    (capteurs, Phase 3). Restreinte aux joueurs présents dans les features.
    """
    features_path = out_dir / "combine_wr_features.csv"
    if not features_path.is_file():
        raise FileNotFoundError(
            f"Features Combine introuvables : {features_path}. Lancer combine_features."
        )
    sensors = pd.read_csv(features_path)

    traditional_cols = [
        c for c in config.TRADITIONAL_COMBINE_METRICS
    ]
    combine = source.read_csv(
        "combine_results", usecols=["nfl_id", "draft_year", *traditional_cols]
    )

    # Identité : player + combine_year ; display_name vient des features (Phase 3).
    merged = sensors.merge(
        combine, on="nfl_id", how="left", suffixes=("", "_combine")
    )
    merged = merged.rename(
        columns={"display_name": "player", "draft_year": "combine_year"}
    )
    if "draft_year_combine" in merged.columns:
        merged = merged.drop(columns=["draft_year_combine"])

    keep = (
        ["nfl_id", "player", "combine_year"]
        + list(config.TRADITIONAL_COMBINE_METRICS)
        + [c for c in config.SENSOR_FEATURE_METRICS if c in merged.columns]
    )
    keep = [c for c in keep if c in merged.columns]
    return merged[keep]


def load_nfl_features(out_dir: Path) -> pd.DataFrame:
    """Charge les features NFL par action (Phase 4)."""
    path = out_dir / "nfl_wr_features.csv"
    if not path.is_file():
        raise FileNotFoundError(
            f"Features NFL introuvables : {path}. Lancer nfl_features."
        )
    return pd.read_csv(path)


def merge_datasets(
    player_combine: pd.DataFrame, nfl: pd.DataFrame
) -> pd.DataFrame:
    """Joint les features NFL (action) avec le Combine joueur sur ``nfl_id``."""
    merged = nfl.merge(player_combine, on="nfl_id", how="inner")

    # Réordonne : clés → identité → Combine trad → capteurs → contexte → outcome.
    front = ["nfl_id", "player", "combine_year", "season", "game_id", "play_id"]
    combine_cols = [
        c for c in (*config.TRADITIONAL_COMBINE_METRICS, *config.SENSOR_FEATURE_METRICS)
        if c in merged.columns
    ]
    context = [
        c for c in [
            "route_ran", "route_family", "team_coverage_man_zone",
            "team_coverage_type", "offense_formation", "receiver_alignment",
            "down", "yards_to_go", "target", "pass_result",
        ] if c in merged.columns
    ]
    outcome = [
        c for c in [
            "cushion", "separation_at_throw", "separation_created",
            "yards_gained", "rec_yards", "yards_after_catch",
            "expected_yards_after_catch",
        ] if c in merged.columns
    ]
    ordered = [c for c in (*front, *combine_cols, *context, *outcome) if c in merged.columns]
    # Ajoute d'éventuelles colonnes oubliées pour ne rien perdre.
    ordered += [c for c in merged.columns if c not in ordered]
    return merged[ordered]


def summarise(merged: pd.DataFrame) -> str:
    """Résumé texte du dataset fusionné."""
    n = len(merged)
    lines = [
        f"Dataset fusionné : {n} actions × {merged.shape[1]} colonnes",
        f"Joueurs (nfl_id) : {merged['nfl_id'].nunique()}",
    ]
    has_forty = merged["forty"].notna().sum() if "forty" in merged else 0
    has_sensor = (
        merged["forty_peak_speed"].notna().sum()
        if "forty_peak_speed" in merged else 0
    )
    lines.append(f"  actions avec chrono 40 (traditionnel) : {has_forty}/{n}")
    lines.append(f"  actions avec capteur 40 (peak_speed)  : {has_sensor}/{n}")
    for col in ("three_cone", "threecone_speed_retention",
                "short_shuttle", "shuttle_peak_deceleration"):
        if col in merged.columns:
            lines.append(f"  {col:28s} renseigné : {int(merged[col].notna().sum())}/{n}")
    return "\n".join(lines)


def run() -> Path:
    """Construit et exporte le dataset analytique fusionné (Parquet)."""
    logger = config.get_logger("kaggle_2027.merge")
    source = config.DataSource.discover()
    out_dir = config.ensure_output_dir()

    player_combine = load_player_combine(source, out_dir)
    nfl = load_nfl_features(out_dir)
    merged = merge_datasets(player_combine, nfl)

    parquet_path = out_dir / config.MERGED_DATASET_FILE
    merged.to_parquet(parquet_path, index=False)
    logger.info(
        "Dataset fusionné écrit : %s (%d actions, %d joueurs)",
        parquet_path, len(merged), merged["nfl_id"].nunique(),
    )
    print("\n" + summarise(merged))
    return parquet_path


if __name__ == "__main__":
    run()

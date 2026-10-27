"""Phase 4 — Features NFL par action pour la cohorte WR.

**Décision de conception majeure (documentée).** La séparation *à l'arrivée*,
la *window creation* et l'*AUC de séparation* ne sont **pas** calculables de
façon valide sur ce dataset : `game_tracking_*` ne suit que les joueurs
**draftés**, pas les 22 joueurs. Au moment de l'arrivée du ballon, un défenseur
en couverture n'est co-tracé que sur ~43 % des actions (moyenne 0,52
défenseur/action), et le « plus proche défenseur tracé » donne une séparation
médiane de ~15 yards — physiquement incompatible avec le défenseur réellement
en couverture. On n'invente donc pas ces mesures.

On retient l'outcome **réellement mesuré et fiable** :

* `separation_at_throw` = `separation_at_pass_forward` (séparation NGS au lancer,
  disponible pour toutes les routes de WR sur passe) ;
* `separation_created` = `separation_at_throw − cushion` (séparation gagnée
  depuis le cushion pré-snap, quand `cushion` est disponible).

Avec le contexte : route, famille de route, couverture man/zone, formation,
down/distance, résultat de la passe, saison.

Export : ``outputs/kaggle_2027/nfl_wr_features.csv`` (une ligne par action).

Exécution ::

    python -m src.kaggle_2027.nfl_features
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from . import config
except ImportError:  # exécution directe
    import config  # type: ignore[no-redef]

# Colonnes de contexte conservées depuis player_play (si présentes).
_CONTEXT_COLS = [
    "route_ran",
    "team_coverage_man_zone",
    "team_coverage_type",
    "offense_formation",
    "receiver_alignment",
    "down",
    "yards_to_go",
    "target",
    "pass_result",
    "yards_gained",
    "rec_yards",
    "yards_after_catch",
    "expected_yards_after_catch",
]


def route_family(route: object) -> object:
    """Mappe une route vers sa famille (``None`` si inconnue/absente)."""
    if not isinstance(route, str):
        return None
    return config.ROUTE_FAMILIES.get(route)


def load_season_map(source: config.DataSource) -> dict[int, int]:
    """Construit ``game_id -> season`` depuis ``games``."""
    games = source.read_csv("games", usecols=["game_id", "season"])
    return dict(zip(games["game_id"], games["season"]))


def load_wr_play_rows(source: config.DataSource, wr_ids: set[int]) -> pd.DataFrame:
    """Charge les actions NFL des WR de la cohorte où la séparation est mesurée.

    On garde toute action de passe où le WR a couru une route et où NGS a
    calculé une séparation au lancer (pas seulement les actions ciblées).
    """
    base_cols = ["game_id", "play_id", "nfl_id", config.NFL_SEPARATION_COL,
                 config.NFL_CUSHION_COL]
    usecols = base_cols + [c for c in _CONTEXT_COLS]
    frames = []
    for chunk in source.iter_chunks(
        "player_play", chunksize=config.CHUNK_ROWS, usecols=usecols
    ):
        sub = chunk[
            chunk["nfl_id"].isin(wr_ids)
            & chunk[config.NFL_SEPARATION_COL].notna()
        ]
        if not sub.empty:
            frames.append(sub)
    if not frames:
        return pd.DataFrame(columns=usecols)
    return pd.concat(frames, ignore_index=True)


def build_features(source: config.DataSource, wr_ids: set[int]) -> pd.DataFrame:
    """Assemble la table de features NFL par action (une ligne / action)."""
    plays = load_wr_play_rows(source, wr_ids)
    if plays.empty:
        return plays

    season_map = load_season_map(source)
    plays["season"] = plays["game_id"].map(season_map)

    plays = plays.rename(columns={config.NFL_SEPARATION_COL: "separation_at_throw"})
    plays["route_family"] = plays["route_ran"].map(route_family)
    plays["separation_created"] = (
        plays["separation_at_throw"] - plays[config.NFL_CUSHION_COL]
    )

    ordered = [
        "game_id", "play_id", "nfl_id", "season",
        "route_ran", "route_family",
        "team_coverage_man_zone", "team_coverage_type",
        "offense_formation", "receiver_alignment", "down", "yards_to_go",
        "target", "pass_result",
        config.NFL_CUSHION_COL, "separation_at_throw", "separation_created",
        "yards_gained", "rec_yards", "yards_after_catch",
        "expected_yards_after_catch",
    ]
    ordered = [c for c in ordered if c in plays.columns]
    return plays[ordered].reset_index(drop=True)


def _coverage_report(features: pd.DataFrame) -> str:
    """Petit résumé texte de couverture des colonnes clés."""
    n = len(features)
    lines = [f"Actions WR (séparation mesurée) : {n}"]
    for col in ["separation_at_throw", config.NFL_CUSHION_COL, "separation_created",
                "route_ran", "team_coverage_man_zone", "target"]:
        if col in features.columns:
            filled = int(features[col].notna().sum())
            lines.append(f"  {col:24s} renseigné : {filled}/{n}")
    lines.append("  familles de routes : " + ", ".join(
        f"{k}={v}" for k, v in features["route_family"].value_counts().items()
    ))
    lines.append("  saisons : " + ", ".join(
        f"{int(k)}={v}" for k, v in features["season"].value_counts().sort_index().items()
    ))
    return "\n".join(lines)


def run() -> Path:
    """Construit et exporte les features NFL par action pour la cohorte WR."""
    logger = config.get_logger("kaggle_2027.nfl_features")
    source = config.DataSource.discover()
    out_dir = config.ensure_output_dir()

    cohort_path = out_dir / "wr_cohort.csv"
    if not cohort_path.is_file():
        raise FileNotFoundError(f"Cohorte introuvable : {cohort_path}")
    cohort = pd.read_csv(cohort_path)
    cohort = cohort[cohort["nfl_position"] == config.WR_NFL_POSITION]
    wr_ids = set(cohort["nfl_id"].tolist())
    logger.info("Cohorte WR : %d joueurs", len(wr_ids))

    features = build_features(source, wr_ids)
    csv_path = out_dir / "nfl_wr_features.csv"
    features.to_csv(csv_path, index=False)
    logger.info("Features NFL écrites : %s (%d actions)", csv_path, len(features))

    print("\n" + _coverage_report(features))
    return csv_path


if __name__ == "__main__":
    run()

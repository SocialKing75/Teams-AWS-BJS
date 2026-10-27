"""Phase 2 — Construction de la cohorte de Wide Receivers.

Mesure, à partir des seules données, combien de WR peuvent être reliés du
Combine à la NFL, selon le funnel :

    participants Combine → WR → WR avec combine_tracking → WR dans players
    → WR dans player_play → WR dans game_tracking → WR avec assez d'actions.

Produit :

* ``outputs/kaggle_2027/wr_cohort.csv`` : une ligne par WR de la cohorte finale.
* ``outputs/kaggle_2027/cohort_report.md`` : funnel lisible + notes.

Aucun chiffre n'est fabriqué : tout provient des fichiers bruts.

Exécution (depuis la racine du dépôt) ::

    python -m src.kaggle_2027.build_cohort
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd

try:
    from . import config
except ImportError:  # exécution directe
    import config  # type: ignore[no-redef]

# Colonnes Combine traditionnelles conservées dans la cohorte (si présentes).
_TRADITIONAL_COMBINE_COLS = [
    "combine_height",
    "combine_weight",
    "hand_size",
    "arm_length",
    "wing_span",
    "ten_yd_split",
    "forty",
    "vertical",
    "broad_jump",
    "three_cone",
    "short_shuttle",
    "bench_reps",
]


# ---------------------------------------------------------------------------
# Étapes élémentaires du funnel
# ---------------------------------------------------------------------------


def load_wr_combine(source: config.DataSource) -> pd.DataFrame:
    """Charge les WR de ``combine_results`` avec leurs mesures traditionnelles."""
    frame = source.read_csv("combine_results")
    wr = frame[frame["combine_position"] == config.WR_COMBINE_POSITION].copy()
    keep = ["nfl_id", "draft_year", "combine_position"] + [
        c for c in _TRADITIONAL_COMBINE_COLS if c in wr.columns
    ]
    return wr[keep].reset_index(drop=True)


def ids_in_combine_tracking(source: config.DataSource) -> set[int]:
    """Ensemble des ``nfl_id`` (joueurs) présents dans ``combine_tracking``."""
    ids: set[int] = set()
    for chunk in source.iter_chunks(
        "combine_tracking",
        chunksize=config.CHUNK_ROWS,
        usecols=["nfl_id", "entity_type"],
    ):
        players = chunk.loc[chunk["entity_type"] == "PLAYER", "nfl_id"]
        ids.update(players.unique().tolist())
    return ids


def load_players(source: config.DataSource) -> pd.DataFrame:
    """Charge ``players`` (identité, position NFL, draft)."""
    return source.read_csv("players")


@dataclass
class PlayStats:
    """Agrégats d'actions NFL par joueur, calculés depuis ``player_play``."""

    n_plays: int = 0
    n_routes: int = 0
    n_targets: int = 0
    n_sep_at_throw: int = 0


def aggregate_player_play(
    source: config.DataSource, cohort_ids: set[int]
) -> dict[int, PlayStats]:
    """Agrège les actions NFL pour les joueurs de ``cohort_ids`` (par blocs)."""
    usecols = ["nfl_id", "route_ran", "target", "separation_at_pass_forward"]
    stats: dict[int, PlayStats] = {}
    for chunk in source.iter_chunks(
        "player_play", chunksize=config.CHUNK_ROWS, usecols=usecols
    ):
        sub = chunk[chunk["nfl_id"].isin(cohort_ids)]
        if sub.empty:
            continue
        grouped = sub.groupby("nfl_id")
        for nfl_id, group in grouped:
            st = stats.setdefault(int(nfl_id), PlayStats())
            st.n_plays += len(group)
            st.n_routes += int(group["route_ran"].notna().sum())
            st.n_targets += int(group["target"].fillna(False).astype(bool).sum())
            st.n_sep_at_throw += int(group["separation_at_pass_forward"].notna().sum())
    return stats


def ids_in_game_tracking(
    source: config.DataSource, cohort_ids: set[int]
) -> dict[int, set[int]]:
    """``nfl_id`` de la cohorte observés dans chaque saison de tracking match.

    Retourne ``{saison: {nfl_id, ...}}``. Lecture d'une seule colonne par blocs
    pour ne jamais charger un fichier de tracking entier en mémoire.
    """
    presence: dict[int, set[int]] = {}
    for name, season in config.GAME_TRACKING_FILES.items():
        seen: set[int] = set()
        for chunk in source.iter_chunks(
            name, chunksize=config.CHUNK_ROWS, usecols=["nfl_id"]
        ):
            present = set(chunk["nfl_id"].unique().tolist()) & cohort_ids
            seen.update(present)
            if seen == cohort_ids:  # tous vus : inutile de continuer ce fichier
                break
        presence[season] = seen
    return presence


# ---------------------------------------------------------------------------
# Assemblage de la cohorte
# ---------------------------------------------------------------------------


@dataclass
class Funnel:
    """Effectifs à chaque étape du funnel de cohorte."""

    combine_total: int
    wr_combine: int
    wr_with_tracking: int
    wr_in_players: int
    wr_in_player_play: int
    wr_in_game_tracking: int
    thresholds: dict[int, int]  # seuil de plays -> effectif
    final: int


def build_cohort(source: config.DataSource) -> tuple[pd.DataFrame, Funnel]:
    """Construit la table de cohorte WR et les effectifs du funnel."""
    combine_total = len(source.read_csv("combine_results", usecols=["nfl_id"]))

    wr = load_wr_combine(source)
    wr_ids = set(wr["nfl_id"].tolist())

    tracking_ids = ids_in_combine_tracking(source)
    wr_with_tracking = wr_ids & tracking_ids

    players = load_players(source)
    players_ids = set(players["nfl_id"].tolist())
    wr_in_players = wr_with_tracking & players_ids

    # Agrégats NFL calculés pour les WR reliables (tracking + players).
    stats = aggregate_player_play(source, wr_in_players)
    wr_in_player_play = {nfl_id for nfl_id, s in stats.items() if s.n_plays > 0}

    presence = ids_in_game_tracking(source, wr_in_player_play)
    wr_in_game_tracking = set().union(*presence.values()) if presence else set()

    # Table enrichie (toutes les étapes reliées, avant seuil d'actions).
    table = wr[wr["nfl_id"].isin(wr_in_players)].copy()
    table = table.merge(
        players[["nfl_id", "display_name", "nfl_position"]], on="nfl_id", how="left"
    )
    table["n_plays"] = table["nfl_id"].map(lambda i: stats.get(i, PlayStats()).n_plays)
    table["n_routes"] = table["nfl_id"].map(lambda i: stats.get(i, PlayStats()).n_routes)
    table["n_targets"] = table["nfl_id"].map(lambda i: stats.get(i, PlayStats()).n_targets)
    table["n_sep_at_throw"] = table["nfl_id"].map(
        lambda i: stats.get(i, PlayStats()).n_sep_at_throw
    )
    for season, ids in presence.items():
        table[f"in_tracking_{season}"] = table["nfl_id"].isin(ids)
    table["in_any_tracking"] = table["nfl_id"].isin(wr_in_game_tracking)

    thresholds = {
        t: int((table["n_plays"] >= t).sum()) for t in config.PLAY_COUNT_THRESHOLDS
    }

    final_mask = (table["n_plays"] >= config.MIN_PLAYS_FINAL_COHORT) & table[
        "in_any_tracking"
    ]
    cohort = table[final_mask].sort_values("n_plays", ascending=False).reset_index(
        drop=True
    )

    funnel = Funnel(
        combine_total=combine_total,
        wr_combine=len(wr_ids),
        wr_with_tracking=len(wr_with_tracking),
        wr_in_players=len(wr_in_players),
        wr_in_player_play=len(wr_in_player_play),
        wr_in_game_tracking=len(wr_in_game_tracking),
        thresholds=thresholds,
        final=len(cohort),
    )
    return cohort, funnel


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------


def render_funnel_lines(funnel: Funnel) -> list[str]:
    """Lignes alignées « libellé  effectif » du funnel."""
    rows = [
        ("Participants Combine", funnel.combine_total),
        ("WR Combine", funnel.wr_combine),
        ("WR avec combine_tracking", funnel.wr_with_tracking),
        ("WR retrouvés dans players", funnel.wr_in_players),
        ("WR présents NFL (player_play)", funnel.wr_in_player_play),
        ("WR présents game_tracking", funnel.wr_in_game_tracking),
    ]
    for threshold, count in funnel.thresholds.items():
        rows.append((f"WR avec >= {threshold} plays", count))
    rows.append(("Cohorte finale", funnel.final))
    return [f"{label:34s}{count:>5d}" for label, count in rows]


def render_report(cohort: pd.DataFrame, funnel: Funnel, source: config.DataSource) -> str:
    """Construit le rapport Markdown de cohorte."""
    out = io.StringIO()
    w = out.write
    w("# Cohorte Wide Receivers — NFL Big Data Bowl 2027\n\n")
    w(f"- Source : **{source.kind}** (`{source.location}`)\n")
    w(f"- Seuil cohorte finale : `n_plays >= {config.MIN_PLAYS_FINAL_COHORT}` "
      "**et** présence dans au moins une saison de tracking match.\n\n")

    w("## Funnel\n\n```\n")
    w("\n".join(render_funnel_lines(funnel)))
    w("\n```\n\n")

    w("## Disponibilité des mesures Combine (cohorte finale)\n\n")
    w(f"Cohorte finale : **{len(cohort)}** WR.\n\n")
    w("Mesure | Renseignée | Manquante\n---|---|---\n")
    for col in _TRADITIONAL_COMBINE_COLS:
        if col in cohort.columns:
            filled = int(cohort[col].notna().sum())
            w(f"`{col}` | {filled} | {len(cohort) - filled}\n")
    w("\n")

    w("## Actions NFL (cohorte finale)\n\n")
    if not cohort.empty:
        desc = cohort[["n_plays", "n_routes", "n_targets", "n_sep_at_throw"]].describe()
        w("```\n" + desc.to_string() + "\n```\n\n")

    w("## Notes et limites\n\n")
    w("- Funnel exact issu des données (aucun chiffre fabriqué).\n")
    w("- `n_plays` = lignes `player_play` du joueur ; `n_routes` = routes "
      "renseignées ; `n_sep_at_throw` = plays avec `separation_at_pass_forward`.\n")
    w("- Présence `game_tracking` vérifiée colonne `nfl_id` uniquement "
      "(lecture par blocs, aucun fichier chargé entièrement).\n")
    w("- La séparation **à l'arrivée** reste à calculer depuis le tracking "
      "(Phase 4), via le *nearest observed defender*.\n")
    return out.getvalue()


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


def run() -> tuple[Path, Path]:
    """Construit la cohorte, écrit le CSV et le rapport, retourne leurs chemins."""
    logger = config.get_logger("kaggle_2027.cohort")
    source = config.DataSource.discover()
    logger.info("Source de données : %s (%s)", source.kind, source.location)

    cohort, funnel = build_cohort(source)

    out_dir = config.ensure_output_dir()
    csv_path = out_dir / "wr_cohort.csv"
    report_path = out_dir / "cohort_report.md"
    cohort.to_csv(csv_path, index=False)
    report_path.write_text(render_report(cohort, funnel, source), encoding="utf-8")

    print("\n".join(render_funnel_lines(funnel)))
    logger.info("Cohorte écrite : %s (%d WR)", csv_path, len(cohort))
    logger.info("Rapport écrit : %s", report_path)
    return csv_path, report_path


if __name__ == "__main__":
    run()

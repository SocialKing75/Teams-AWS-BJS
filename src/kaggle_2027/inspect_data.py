"""Phase 1 — Inspection des données NFL Big Data Bowl 2027.

Inspecte chaque fichier brut Kaggle sans charger inutilement plusieurs Go :

* petits fichiers : chargés entièrement ;
* gros fichiers : échantillonnés via ``nrows``.

Pour chaque fichier, affiche et consigne : colonnes, types, aperçu, valeurs
manquantes, identifiants candidats (joueur, game/play), saisons, positions, et
les colonnes partagées qui permettent de relier les fichiers entre eux.

Aucune colonne n'est supposée : seules les colonnes réellement présentes sont
utilisées. Les gros fichiers sont signalés comme "échantillon" car leurs
statistiques de valeurs manquantes portent sur les ``SAMPLE_ROWS`` premières
lignes.

Exécution (depuis la racine du dépôt) ::

    python -m src.kaggle_2027.inspect_data
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

try:  # exécution en module (python -m src.kaggle_2027.inspect_data)
    from . import config
except ImportError:  # exécution directe (python inspect_data.py)
    import config  # type: ignore[no-redef]


# ---------------------------------------------------------------------------
# Heuristiques de détection de colonnes (sans supposer de noms exacts)
# ---------------------------------------------------------------------------

# Identifiants de joueur plausibles (minuscule).
_PLAYER_ID_HINTS = ("nfl_id", "player_id", "gsis_id", "pfr_id", "nflid")
# Identifiants de match / action plausibles.
_GAME_PLAY_ID_HINTS = ("game_id", "play_id", "old_game_id", "gameid", "playid")
# Colonnes "saison / année".
_SEASON_HINTS = ("season", "year")
# Colonnes "position".
_POSITION_HINTS = ("position", "pos")
# Pour combine_tracking : concepts physiques recherchés.
_TRACKING_CONCEPTS = {
    "drill": ("drill", "event", "test", "exercise"),
    "frame": ("frame", "frameid", "frame_id"),
    "temps": ("time", "t", "timestamp", "ms"),
    "x": ("x",),
    "y": ("y",),
    "vitesse": ("s", "speed", "v", "velocity"),
    "acceleration": ("a", "acc", "accel", "acceleration"),
    "orientation": ("o", "orientation"),
    "direction": ("dir", "direction"),
}


def _lower_map(columns: list[str]) -> dict[str, str]:
    """Associe nom de colonne en minuscule -> nom d'origine."""
    return {c.lower(): c for c in columns}


def _match_any(columns: list[str], hints: tuple[str, ...]) -> list[str]:
    """Retourne les colonnes dont le nom (minuscule) contient un indice."""
    lowered = _lower_map(columns)
    matches: list[str] = []
    for low, original in lowered.items():
        if any(hint in low for hint in hints):
            matches.append(original)
    return matches


def _match_exact(columns: list[str], candidates: tuple[str, ...]) -> list[str]:
    """Retourne les colonnes dont le nom (minuscule) égale un candidat exact."""
    lowered = _lower_map(columns)
    return [lowered[c] for c in candidates if c in lowered]


# ---------------------------------------------------------------------------
# Résumé d'un fichier
# ---------------------------------------------------------------------------


@dataclass
class FileSummary:
    """Synthèse d'inspection d'un fichier brut."""

    name: str
    filename: str
    size_mb: float
    sampled: bool
    n_rows_read: int
    columns: list[str] = field(default_factory=list)
    dtypes: dict[str, str] = field(default_factory=dict)
    missing: dict[str, int] = field(default_factory=dict)
    player_ids: list[str] = field(default_factory=list)
    game_play_ids: list[str] = field(default_factory=list)
    seasons: list[str] = field(default_factory=list)
    positions: list[str] = field(default_factory=list)
    head: pd.DataFrame = field(default_factory=pd.DataFrame)
    season_values: Optional[pd.Series] = None
    position_values: Optional[pd.Series] = None


def _column_values(frame: pd.DataFrame, columns: list[str]) -> Optional[pd.Series]:
    """Compte des valeurs (<=30) de la première colonne pertinente, si présente."""
    for col in columns:
        try:
            counts = frame[col].value_counts(dropna=False)
        except Exception:  # colonne non comptable
            continue
        if not counts.empty:
            return counts.head(30)
    return None


def summarise_file(
    source: "config.DataSource",
    raw: "config.RawFile",
    logger,
) -> FileSummary:
    """Lit un échantillon d'un fichier et en calcule la synthèse d'inspection."""
    sampled = raw.is_large
    nrows = config.SAMPLE_ROWS if sampled else None
    logger.info(
        "Inspection de %s (%.1f Mo)%s",
        raw.filename,
        raw.size_mb,
        f" — échantillon {nrows:,} lignes" if sampled else "",
    )
    frame = source.read_csv(raw.name, nrows=nrows, low_memory=False)
    columns = frame.columns.tolist()

    missing = {
        col: int(frame[col].isna().sum())
        for col in columns
        if frame[col].isna().any()
    }

    summary = FileSummary(
        name=raw.name,
        filename=raw.filename,
        size_mb=raw.size_mb,
        sampled=sampled,
        n_rows_read=len(frame),
        columns=columns,
        dtypes={c: str(frame[c].dtype) for c in columns},
        missing=missing,
        player_ids=_match_exact(columns, _PLAYER_ID_HINTS)
        or _match_any(columns, ("playerid", "nfl_id", "gsis")),
        game_play_ids=_match_exact(columns, _GAME_PLAY_ID_HINTS),
        seasons=_match_any(columns, _SEASON_HINTS),
        positions=_match_any(columns, _POSITION_HINTS),
        head=frame.head(5),
    )
    summary.season_values = _column_values(frame, summary.seasons)
    summary.position_values = _column_values(frame, summary.positions)
    return summary


# ---------------------------------------------------------------------------
# Inspection spécifique de combine_tracking
# ---------------------------------------------------------------------------


def inspect_combine_tracking(summary: FileSummary) -> dict[str, list[str]]:
    """Repère les colonnes physiques utiles dans ``combine_tracking``."""
    found: dict[str, list[str]] = {}
    for concept, hints in _TRACKING_CONCEPTS.items():
        # x / y / s / a sont souvent des noms exacts d'une seule lettre.
        exact = _match_exact(summary.columns, hints)
        fuzzy = _match_any(summary.columns, hints)
        # Priorité à l'exact pour éviter que "x" capture "max", etc.
        found[concept] = exact or fuzzy
    return found


# ---------------------------------------------------------------------------
# Relations entre fichiers
# ---------------------------------------------------------------------------


def shared_columns(summaries: list[FileSummary]) -> dict[str, list[str]]:
    """Colonne -> liste des fichiers où elle apparaît (>=2 fichiers)."""
    occurrences: dict[str, list[str]] = {}
    for summary in summaries:
        for col in summary.columns:
            occurrences.setdefault(col.lower(), [])
            occurrences[col.lower()].append(summary.name)
    return {col: files for col, files in occurrences.items() if len(files) >= 2}


# ---------------------------------------------------------------------------
# Rendu
# ---------------------------------------------------------------------------


def _df_to_text(frame: pd.DataFrame, max_cols: int = 12) -> str:
    """Rend un DataFrame en texte compact (colonnes tronquées si trop larges)."""
    show = frame if frame.shape[1] <= max_cols else frame.iloc[:, :max_cols]
    with pd.option_context("display.max_columns", max_cols, "display.width", 160):
        text = show.to_string(index=False)
    if frame.shape[1] > max_cols:
        text += f"\n... (+{frame.shape[1] - max_cols} colonnes non affichées)"
    return text


def render_report(
    summaries: list[FileSummary],
    tracking_concepts: Optional[dict[str, list[str]]],
    shared: dict[str, list[str]],
    source: "config.DataSource",
) -> str:
    """Construit le rapport Markdown complet d'inspection."""
    out = io.StringIO()
    w = out.write

    w("# Inspection des données — NFL Big Data Bowl 2027\n\n")
    w(f"- Source lue : **{source.kind}** (`{source.location}`)\n")
    w(f"- Fichiers attendus présents : **{len(summaries)}/{len(config.EXPECTED_FILES)}**\n")
    w(f"- Seuil d'échantillonnage : {config.LARGE_FILE_BYTES // (1024 * 1024)} Mo "
      f"→ {config.SAMPLE_ROWS:,} lignes lues pour les gros fichiers\n\n")

    for s in summaries:
        w(f"## {s.filename}\n\n")
        tag = f" — échantillon ({s.n_rows_read:,} lignes)" if s.sampled else \
              f" — {s.n_rows_read:,} lignes"
        w(f"- Taille : {s.size_mb:.1f} Mo{tag}\n")
        w(f"- Nombre de colonnes : {len(s.columns)}\n")
        w(f"- Colonnes : {', '.join(s.columns)}\n")
        w("- Types :\n")
        for col, dt in s.dtypes.items():
            w(f"    - `{col}` : {dt}\n")
        if s.missing:
            w(f"- Valeurs manquantes (sur {s.n_rows_read:,} lignes) :\n")
            for col, n in sorted(s.missing.items(), key=lambda kv: -kv[1]):
                w(f"    - `{col}` : {n:,}\n")
        else:
            w("- Valeurs manquantes : aucune détectée sur l'échantillon\n")
        w(f"- Identifiants joueur candidats : "
          f"{', '.join(s.player_ids) if s.player_ids else '—'}\n")
        w(f"- Identifiants game/play candidats : "
          f"{', '.join(s.game_play_ids) if s.game_play_ids else '—'}\n")
        w(f"- Colonnes saison/année : "
          f"{', '.join(s.seasons) if s.seasons else '—'}\n")
        if s.season_values is not None:
            vals = ", ".join(f"{k}={v}" for k, v in s.season_values.items())
            w(f"    - valeurs : {vals}\n")
        w(f"- Colonnes position : "
          f"{', '.join(s.positions) if s.positions else '—'}\n")
        if s.position_values is not None:
            vals = ", ".join(f"{k}={v}" for k, v in s.position_values.items())
            w(f"    - valeurs : {vals}\n")
        w("- Aperçu (5 lignes) :\n\n```\n")
        w(_df_to_text(s.head))
        w("\n```\n\n")

    if tracking_concepts is not None:
        w("## combine_tracking — concepts physiques détectés\n\n")
        for concept, cols in tracking_concepts.items():
            w(f"- **{concept}** : {', '.join(cols) if cols else '❌ absent'}\n")
        w("\n")

    w("## Colonnes partagées (clés de jointure candidates)\n\n")
    w("Colonne | Présente dans\n---|---\n")
    for col, files in sorted(shared.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        w(f"`{col}` | {', '.join(sorted(files))}\n")
    w("\n")

    return out.getvalue()


def print_console_summary(
    summaries: list[FileSummary],
    tracking_concepts: Optional[dict[str, list[str]]],
    shared: dict[str, list[str]],
    source: "config.DataSource",
) -> None:
    """Affiche une synthèse condensée dans la console."""
    print("\n" + "=" * 72)
    print("INSPECTION KAGGLE 2027 — SYNTHÈSE")
    print("=" * 72)
    print(f"Source : {source.kind} ({source.location})")
    print(f"Fichiers présents : {len(summaries)}/{len(config.EXPECTED_FILES)}\n")
    for s in summaries:
        flag = "échantillon" if s.sampled else "complet"
        print(f"- {s.filename:32s} {len(s.columns):>3d} col  "
              f"{s.size_mb:8.1f} Mo  ({flag})")
    if tracking_concepts is not None:
        print("\ncombine_tracking — concepts physiques :")
        for concept, cols in tracking_concepts.items():
            status = ", ".join(cols) if cols else "ABSENT"
            print(f"    {concept:14s} : {status}")
    print("\nClés de jointure candidates (colonnes partagées) :")
    for col, files in sorted(shared.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        print(f"    {col:18s} -> {', '.join(sorted(files))}")
    print("=" * 72 + "\n")


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


def run() -> Path:
    """Inspecte toutes les données disponibles et écrit le rapport Markdown."""
    logger = config.get_logger("kaggle_2027.inspect")
    source = config.DataSource.discover()
    logger.info("Source de données : %s (%s)", source.kind, source.location)

    available = source.available()
    if not available:
        raise FileNotFoundError("Aucun fichier attendu trouvé dans la source.")
    missing = sorted(set(config.EXPECTED_FILES) - set(available))
    if missing:
        logger.warning("Fichiers attendus absents : %s", ", ".join(missing))

    summaries: list[FileSummary] = []
    for name in config.EXPECTED_FILES:  # ordre stable et logique
        if name not in available:
            continue
        summaries.append(summarise_file(source, available[name], logger))

    tracking_concepts: Optional[dict[str, list[str]]] = None
    for s in summaries:
        if s.name == "combine_tracking":
            tracking_concepts = inspect_combine_tracking(s)
            break

    shared = shared_columns(summaries)

    print_console_summary(summaries, tracking_concepts, shared, source)

    report = render_report(summaries, tracking_concepts, shared, source)
    out_dir = config.ensure_output_dir()
    report_path = out_dir / "inspection_report.md"
    report_path.write_text(report, encoding="utf-8")
    logger.info("Rapport écrit : %s", report_path)
    return report_path


if __name__ == "__main__":
    run()

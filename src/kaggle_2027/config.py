"""Configuration centralisée pour la couche Kaggle NFL Big Data Bowl 2027.

Source unique de vérité pour :

* la localisation des données brutes (dossier extrait *ou* archive ``.zip``) ;
* la liste des fichiers bruts attendus ;
* l'emplacement des sorties intermédiaires ;
* un petit utilitaire :class:`DataSource` qui lit des échantillons CSV de
  façon transparente depuis un dossier extrait **ou** directement dans le zip,
  afin de ne jamais devoir décompresser ~2,3 Go de tracking pour une simple
  inspection.

Aucune valeur métier importante n'est codée en dur sans constante documentée.
"""

from __future__ import annotations

import logging
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, Sequence

import pandas as pd

# ---------------------------------------------------------------------------
# Chemins
# ---------------------------------------------------------------------------

# src/kaggle_2027/config.py -> parents[2] == racine du dépôt (Teams-AWS-BJS).
REPO_ROOT: Path = Path(__file__).resolve().parents[2]
# Dossier de travail parent (ex. "NFL BIG DATA comp") qui héberge data/ et le zip.
WORKSPACE_ROOT: Path = REPO_ROOT.parent

# Sorties intermédiaires de la couche 2027 (jamais dans les données brutes).
OUTPUT_DIR: Path = REPO_ROOT / "outputs" / "kaggle_2027"
DOCS_DIR: Path = REPO_ROOT / "docs"

# Préfixe du dossier interne de l'archive Kaggle.
ZIP_INNER_PREFIX: str = "nfl-big-data-bowl-2027/"

# Variables d'environnement optionnelles pour surcharger la localisation.
ENV_RAW_DIR: str = "KAGGLE_2027_RAW"
ENV_ZIP: str = "KAGGLE_2027_ZIP"

# Candidats de recherche pour le dossier des CSV extraits (ordre de priorité).
_RAW_DIR_CANDIDATES: tuple[Path, ...] = (
    REPO_ROOT / "data" / "kaggle_2027" / "raw",
    WORKSPACE_ROOT / "data" / "kaggle_2027" / "raw",
)
# Candidats de recherche pour l'archive zip d'origine.
_ZIP_CANDIDATES: tuple[Path, ...] = (
    WORKSPACE_ROOT / "nfl-big-data-bowl-2027.zip",
    REPO_ROOT / "nfl-big-data-bowl-2027.zip",
)

# ---------------------------------------------------------------------------
# Fichiers attendus
# ---------------------------------------------------------------------------

# Clé logique -> nom de fichier réel. La présence est vérifiée à l'exécution ;
# on ne suppose jamais qu'un fichier existe.
EXPECTED_FILES: dict[str, str] = {
    "combine_results": "combine_results.csv",
    "combine_tracking": "combine_tracking.csv",
    "players": "players.csv",
    "player_play": "player_play.csv",
    "games": "games.csv",
    "player_career_successes": "player_career_successes.csv",
    "game_tracking_2023": "game_tracking_2023.csv",
    "game_tracking_2024": "game_tracking_2024.csv",
    "game_tracking_2025": "game_tracking_2025.csv",
}

# Au-delà de ce seuil, on échantillonne (nrows) au lieu de tout charger.
LARGE_FILE_BYTES: int = 50 * 1024 * 1024  # 50 Mo
# Nombre de lignes lues pour inspecter un gros fichier.
SAMPLE_ROWS: int = 100_000

# ---------------------------------------------------------------------------
# Cohorte Wide Receivers (Phase 2)
# ---------------------------------------------------------------------------

# Libellé de la position WR dans combine_results.combine_position.
WR_COMBINE_POSITION: str = "WR"
# Libellé de la position WR dans players.nfl_position.
WR_NFL_POSITION: str = "WR"

# Seuils d'actions NFL rapportés dans le funnel de cohorte.
PLAY_COUNT_THRESHOLDS: tuple[int, ...] = (20, 50)
# Seuil minimal d'actions pour entrer dans la cohorte finale.
MIN_PLAYS_FINAL_COHORT: int = 20

# Taille de bloc pour parcourir les gros fichiers sans saturer la mémoire.
CHUNK_ROWS: int = 1_000_000

# Saisons de tracking match disponibles (clé logique -> saison).
GAME_TRACKING_FILES: dict[str, int] = {
    "game_tracking_2023": 2023,
    "game_tracking_2024": 2024,
    "game_tracking_2025": 2025,
}

# ---------------------------------------------------------------------------
# Features Combine (Phase 3) — constantes documentées
# ---------------------------------------------------------------------------

# Fréquence d'échantillonnage du tracking Combine (observée : 10 Hz).
TRACKING_HZ: int = 10
# Lissage léger (fenêtre de moyenne glissante centrée) pour atténuer le bruit.
SMOOTH_WINDOW_FRAMES: int = 3
# Seuil de vitesse (yd/s) marquant le début de mouvement d'une instance.
MOTION_START_SPEED: float = 0.7
# Fenêtre (s) pour l'accélération initiale du 40-yard.
INITIAL_ACCEL_WINDOW_S: float = 0.5
# Distance (yd) du split précoce du 40-yard.
SPLIT_DISTANCE_YD: float = 10.0
# Fraction de la vitesse de pointe définissant la "transition" de virage.
TURN_SPEED_FRACTION: float = 0.5
# Frames exclues en début/fin d'instance pour les minima de virage.
EDGE_FRAMES: int = 5
# Instances plus courtes (frames) ignorées comme non exploitables.
MIN_INSTANCE_FRAMES: int = 20

# Drills chronométrés exploités en Phase 3.
COMBINE_STOPWATCH_DRILLS: tuple[str, ...] = (
    "FORTY_YARD_DASH",
    "SHORT_SHUTTLE",
    "THREE_CONE_DRILL",
)

# ---------------------------------------------------------------------------
# Features NFL (Phase 4)
# ---------------------------------------------------------------------------

# Outcome NFL retenu : séparation (yd) du receveur au lancer, calculée par NGS.
# ATTENTION : la séparation à l'arrivée / window_creation / AUC ne sont PAS
# calculables de façon valide ici — game_tracking ne suit que les joueurs
# draftés, donc le défenseur en couverture est rarement observé (cf. doc).
NFL_SEPARATION_COL: str = "separation_at_pass_forward"
NFL_CUSHION_COL: str = "cushion"

# Familles de routes (valeurs réelles de route_ran du dataset 2027).
ROUTE_FAMILIES: dict[str, str] = {
    "HITCH": "HARD_STOP",
    "OUT": "OUT_BREAKING",
    "CORNER": "OUT_BREAKING",
    "SLANT": "IN_BREAKING",
    "IN": "IN_BREAKING",
    "GO": "VERTICAL",
    "CROSS": "CONTINUOUS",
    "POST": "CONTINUOUS",
    "WHEEL": "CONTINUOUS",
    "FLAT": "SHORT",
    "SCREEN": "SHORT",
    "ANGLE": "SHORT",
}

# ---------------------------------------------------------------------------
# Jointure Combine ↔ NFL (Phase 6) — listes de colonnes canoniques
# ---------------------------------------------------------------------------

# Mesures Combine traditionnelles (chronomètre / mensurations).
TRADITIONAL_COMBINE_METRICS: tuple[str, ...] = (
    "forty",
    "ten_yd_split",
    "three_cone",
    "short_shuttle",
    "vertical",
    "broad_jump",
    "bench_reps",
    "combine_height",
    "combine_weight",
    "hand_size",
    "arm_length",
    "wing_span",
)

# Features capteurs produites en Phase 3 (combine_wr_features.csv).
SENSOR_FEATURE_METRICS: tuple[str, ...] = (
    "forty_peak_speed",
    "forty_initial_acceleration",
    "forty_time_to_peak_speed",
    "forty_speed_at_split",
    "shuttle_peak_deceleration",
    "shuttle_turn_transition_time",
    "shuttle_exit_acceleration",
    "shuttle_min_turn_speed",
    "threecone_speed_retention",
    "threecone_path_efficiency",
    "threecone_peak_deceleration",
    "threecone_min_turn_speed",
)

# Nom du dataset analytique fusionné (Parquet).
MERGED_DATASET_FILE: str = "combine_nfl_wr_dataset.parquet"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger simple et lisible (console, niveau INFO)."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# ---------------------------------------------------------------------------
# Accès aux données brutes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RawFile:
    """Métadonnées d'un fichier CSV brut (sur disque ou dans le zip)."""

    name: str  # clé logique
    filename: str  # nom de fichier réel
    size_bytes: int

    @property
    def is_large(self) -> bool:
        """Vrai si le fichier dépasse :data:`LARGE_FILE_BYTES`."""
        return self.size_bytes >= LARGE_FILE_BYTES

    @property
    def size_mb(self) -> float:
        """Taille en mégaoctets."""
        return self.size_bytes / (1024 * 1024)


class DataSource:
    """Accès unifié aux CSV bruts depuis un dossier extrait *ou* un zip.

    La source préférée est un dossier extrait ; à défaut, les fichiers sont
    lus directement dans l'archive ``nfl-big-data-bowl-2027.zip`` sans la
    décompresser. L'appelant n'a pas besoin de savoir où vivent les données.
    """

    def __init__(
        self,
        raw_dir: Optional[Path] = None,
        zip_path: Optional[Path] = None,
    ) -> None:
        if raw_dir is None and zip_path is None:
            raise FileNotFoundError(
                "Aucune source de données 2027 : ni dossier extrait, ni zip."
            )
        self._raw_dir = raw_dir
        self._zip_path = zip_path

    # -- Construction -------------------------------------------------------

    @classmethod
    def discover(cls) -> "DataSource":
        """Localise automatiquement la meilleure source disponible.

        Ordre de priorité : variable d'environnement RAW_DIR, dossiers
        candidats extraits, variable d'environnement ZIP, zips candidats.
        """
        env_dir = os.environ.get(ENV_RAW_DIR)
        if env_dir and Path(env_dir).is_dir():
            return cls(raw_dir=Path(env_dir))
        for candidate in _RAW_DIR_CANDIDATES:
            if candidate.is_dir() and any(candidate.glob("*.csv")):
                return cls(raw_dir=candidate)

        env_zip = os.environ.get(ENV_ZIP)
        if env_zip and Path(env_zip).is_file():
            return cls(zip_path=Path(env_zip))
        for candidate in _ZIP_CANDIDATES:
            if candidate.is_file():
                return cls(zip_path=candidate)

        searched = [str(p) for p in (*_RAW_DIR_CANDIDATES, *_ZIP_CANDIDATES)]
        raise FileNotFoundError(
            "Données Kaggle 2027 introuvables. Emplacements testés :\n  - "
            + "\n  - ".join(searched)
            + f"\nDéfinir {ENV_RAW_DIR} ou {ENV_ZIP} pour pointer vers les données."
        )

    # -- Introspection ------------------------------------------------------

    @property
    def kind(self) -> str:
        """``"dir"`` si source extraite, ``"zip"`` sinon."""
        return "dir" if self._raw_dir is not None else "zip"

    @property
    def location(self) -> Path:
        """Chemin de la source (dossier ou archive)."""
        return self._raw_dir if self._raw_dir is not None else self._zip_path  # type: ignore[return-value]

    def _zip_member(self, filename: str) -> str:
        """Nom de membre du fichier dans l'archive zip."""
        return f"{ZIP_INNER_PREFIX}{filename}"

    def available(self) -> dict[str, RawFile]:
        """Retourne les fichiers attendus réellement présents dans la source.

        La clé est la clé logique de :data:`EXPECTED_FILES`.
        """
        found: dict[str, RawFile] = {}
        if self._raw_dir is not None:
            for name, filename in EXPECTED_FILES.items():
                path = self._raw_dir / filename
                if path.is_file():
                    found[name] = RawFile(name, filename, path.stat().st_size)
            return found

        with zipfile.ZipFile(self._zip_path) as archive:  # type: ignore[arg-type]
            sizes = {info.filename: info.file_size for info in archive.infolist()}
        for name, filename in EXPECTED_FILES.items():
            member = self._zip_member(filename)
            if member in sizes:
                found[name] = RawFile(name, filename, sizes[member])
        return found

    # -- Lecture ------------------------------------------------------------

    def read_csv(
        self,
        name: str,
        *,
        nrows: Optional[int] = None,
        usecols: Optional[Sequence[str]] = None,
        **kwargs: object,
    ) -> pd.DataFrame:
        """Lit (éventuellement partiellement) un CSV brut en DataFrame.

        Utiliser ``nrows`` et/ou ``usecols`` pour maîtriser la mémoire sur les
        gros fichiers. Fonctionne à l'identique en source dossier ou zip.
        """
        filename = EXPECTED_FILES[name]
        read_kw = dict(nrows=nrows, usecols=usecols, **kwargs)
        if self._raw_dir is not None:
            return pd.read_csv(self._raw_dir / filename, **read_kw)  # type: ignore[arg-type]
        with zipfile.ZipFile(self._zip_path) as archive:  # type: ignore[arg-type]
            with archive.open(self._zip_member(filename)) as handle:
                return pd.read_csv(handle, **read_kw)  # type: ignore[arg-type]

    def iter_chunks(
        self,
        name: str,
        *,
        chunksize: int,
        usecols: Optional[Sequence[str]] = None,
        **kwargs: object,
    ) -> Iterator[pd.DataFrame]:
        """Itère un CSV brut par blocs, sans tout charger en mémoire.

        Destiné aux gros fichiers de tracking (phases ultérieures). La source
        reste ouverte tant que le générateur n'est pas épuisé.
        """
        filename = EXPECTED_FILES[name]
        read_kw = dict(chunksize=chunksize, usecols=usecols, **kwargs)
        if self._raw_dir is not None:
            yield from pd.read_csv(self._raw_dir / filename, **read_kw)  # type: ignore[arg-type]
            return
        with zipfile.ZipFile(self._zip_path) as archive:  # type: ignore[arg-type]
            with archive.open(self._zip_member(filename)) as handle:
                yield from pd.read_csv(handle, **read_kw)  # type: ignore[arg-type]


def ensure_output_dir() -> Path:
    """Crée (si besoin) et retourne le dossier de sorties de la couche 2027."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR

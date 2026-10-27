"""Phase 7 — Baseline scientifique.

Question : **les métriques capteurs du Combine apportent-elles plus
d'information sur la séparation NFL que les chronos traditionnels ?**

On compare, pour prédire `separation_at_throw` :

* **Modèle A** — Combine traditionnel (40-yard, 10-yd split, vertical, broad
  jump, taille, poids) ;
* **Modèle B** — A **+** capteurs 40-yard (peak speed, accélération initiale,
  temps pour atteindre la pointe, vitesse au split).

Deux granularités d'outcome (demandées) :

* **par action** (~37 k lignes, bruit intra-joueur) ;
* **par joueur** (séparation moyenne, ~101 lignes, « translation athlétique »).

Garde-fous :

* validation **`GroupKFold(group=nfl_id)`** — jamais le même joueur en TRAIN et
  TEST (pas de split aléatoire par action) ;
* modèles interprétables d'abord (Linear, RidgeCV, ElasticNetCV), puis
  Gradient Boosting (paramètres modestes vu le faible N) ;
* imputation médiane **ajustée dans le pli d'entraînement** (via Pipeline) pour
  éviter toute fuite ;
* les scores composites NGS sont **exclus** (fuite potentielle) — absents du
  dataset fusionné.

Les features d'agilité (3-cone / shuttle) sont trop éparses (~20-27 joueurs)
pour un modèle fiable : traitées en **exploratoire** (corrélations), pas en
baseline.

Export : ``outputs/kaggle_2027/baseline_report.md``.

Exécution ::

    python -m src.kaggle_2027.baseline_model
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNetCV, LinearRegression, RidgeCV
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:
    from . import config
except ImportError:  # exécution directe
    import config  # type: ignore[no-redef]

# --- Jeux de features (40-yard : bien peuplé) ------------------------------

TRAD_FEATURES: list[str] = [
    "forty", "ten_yd_split", "vertical", "broad_jump",
    "combine_height", "combine_weight",
]
SENSOR_FEATURES: list[str] = [
    "forty_peak_speed", "forty_initial_acceleration",
    "forty_time_to_peak_speed", "forty_speed_at_split",
]
MODEL_FEATURES: dict[str, list[str]] = {
    "A_traditional": TRAD_FEATURES,
    "B_with_sensors": TRAD_FEATURES + SENSOR_FEATURES,
}

# Features d'agilité (exploratoire uniquement).
AGILITY_FEATURES: list[str] = [
    "three_cone", "short_shuttle",
    "shuttle_peak_deceleration", "shuttle_exit_acceleration",
    "shuttle_turn_transition_time", "shuttle_min_turn_speed",
    "threecone_speed_retention", "threecone_path_efficiency",
    "threecone_peak_deceleration",
]

TARGET = "separation_at_throw"
N_SPLITS = 5
RANDOM_STATE = 0


# ---------------------------------------------------------------------------
# Régresseurs
# ---------------------------------------------------------------------------


def _build_models() -> dict[str, tuple[object, bool]]:
    """Retourne ``{nom: (estimateur, besoin_de_scaling)}``."""
    alphas = np.logspace(-3, 3, 13)
    return {
        "Linear": (LinearRegression(), True),
        "RidgeCV": (RidgeCV(alphas=alphas), True),
        "ElasticNetCV": (
            ElasticNetCV(l1_ratio=[0.1, 0.5, 0.9], cv=5, max_iter=10000,
                         random_state=RANDOM_STATE),
            True,
        ),
        "GradientBoosting": (
            GradientBoostingRegressor(
                n_estimators=300, max_depth=2, learning_rate=0.03,
                subsample=0.8, random_state=RANDOM_STATE,
            ),
            False,
        ),
    }


def _pipeline(estimator: object, scale: bool) -> Pipeline:
    """Imputation médiane (+ scaling optionnel) puis estimateur."""
    steps = [("impute", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scale", StandardScaler()))
    steps.append(("model", estimator))
    return Pipeline(steps)


# ---------------------------------------------------------------------------
# Validation croisée par groupe
# ---------------------------------------------------------------------------


@dataclass
class CVResult:
    """Métriques out-of-fold agrégées."""

    mae: float
    rmse: float
    r2: float
    n: int
    n_groups: int


def group_cv(
    estimator: object, scale: bool, X: pd.DataFrame, y: pd.Series, groups: pd.Series
) -> CVResult:
    """Prédictions out-of-fold via GroupKFold, puis métriques poolées."""
    n_groups = groups.nunique()
    n_splits = min(N_SPLITS, n_groups)
    gkf = GroupKFold(n_splits=n_splits)
    oof = np.full(len(y), np.nan)
    for train_idx, test_idx in gkf.split(X, y, groups):
        pipe = _pipeline(clone(estimator), scale)
        pipe.fit(X.iloc[train_idx], y.iloc[train_idx])
        oof[test_idx] = pipe.predict(X.iloc[test_idx])
    mask = ~np.isnan(oof)
    y_true = y.to_numpy()[mask]
    y_pred = oof[mask]
    return CVResult(
        mae=float(mean_absolute_error(y_true, y_pred)),
        rmse=float(np.sqrt(mean_squared_error(y_true, y_pred))),
        r2=float(r2_score(y_true, y_pred)),
        n=int(mask.sum()),
        n_groups=int(n_groups),
    )


def evaluate_outcome(
    df: pd.DataFrame, y: pd.Series, groups: pd.Series, label: str
) -> pd.DataFrame:
    """Évalue A vs B × régresseurs sur un outcome donné."""
    rows = []
    models = _build_models()
    for feat_name, features in MODEL_FEATURES.items():
        X = df[features]
        for reg_name, (estimator, scale) in models.items():
            res = group_cv(estimator, scale, X, y, groups)
            rows.append({
                "outcome": label,
                "model": feat_name,
                "regressor": reg_name,
                "MAE": res.mae,
                "RMSE": res.rmse,
                "R2": res.r2,
                "n": res.n,
                "n_groups": res.n_groups,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Préparation des données
# ---------------------------------------------------------------------------


def load_dataset(out_dir: Path) -> pd.DataFrame:
    """Charge le dataset fusionné (Phase 6)."""
    path = out_dir / config.MERGED_DATASET_FILE
    if not path.is_file():
        raise FileNotFoundError(f"Dataset fusionné introuvable : {path}")
    return pd.read_parquet(path)


def per_player_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège par joueur : séparation moyenne + features (constantes)."""
    feature_cols = TRAD_FEATURES + SENSOR_FEATURES + AGILITY_FEATURES
    agg = {TARGET: "mean"}
    agg.update({c: "first" for c in feature_cols if c in df.columns})
    grouped = df.groupby("nfl_id").agg(agg).reset_index()
    grouped = grouped.rename(columns={TARGET: "sep_mean"})
    grouped["n_plays"] = df.groupby("nfl_id").size().to_numpy()
    return grouped


# ---------------------------------------------------------------------------
# Exploratoire : agilité (corrélations, petit N)
# ---------------------------------------------------------------------------


def agility_correlations(player_df: pd.DataFrame) -> pd.DataFrame:
    """Corrélation de Pearson feature d'agilité ↔ séparation moyenne (par joueur)."""
    rows = []
    for col in AGILITY_FEATURES:
        if col not in player_df.columns:
            continue
        sub = player_df[[col, "sep_mean"]].dropna()
        if len(sub) >= 8:
            rows.append({
                "feature": col,
                "pearson_r": round(float(sub[col].corr(sub["sep_mean"])), 3),
                "n_players": len(sub),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------


def _results_table(results: pd.DataFrame) -> str:
    out = io.StringIO()
    out.write("outcome | model | regressor | MAE | RMSE | R² | n | groupes\n")
    out.write("---|---|---|---|---|---|---|---\n")
    for _, r in results.iterrows():
        out.write(
            f"{r['outcome']} | {r['model']} | {r['regressor']} | "
            f"{r['MAE']:.3f} | {r['RMSE']:.3f} | {r['R2']:.3f} | "
            f"{int(r['n'])} | {int(r['n_groups'])}\n"
        )
    return out.getvalue()


def _improvement_table(results: pd.DataFrame) -> str:
    """Delta B−A (MAE/R²) par outcome × régresseur (B meilleur si ΔMAE<0, ΔR²>0)."""
    out = io.StringIO()
    out.write("\n### Apport des capteurs (B − A)\n\n")
    out.write("outcome | regressor | ΔMAE | ΔR²\n---|---|---|---\n")
    for (outcome, reg), g in results.groupby(["outcome", "regressor"]):
        a = g[g["model"] == "A_traditional"].iloc[0]
        b = g[g["model"] == "B_with_sensors"].iloc[0]
        out.write(
            f"{outcome} | {reg} | {b['MAE'] - a['MAE']:+.3f} | "
            f"{b['R2'] - a['R2']:+.3f}\n"
        )
    return out.getvalue()


def render_report(
    results: pd.DataFrame, agility: pd.DataFrame, n_players: int
) -> str:
    out = io.StringIO()
    out.write("# Baseline — capteurs Combine vs chronos traditionnels (WR)\n\n")
    out.write(f"- Outcome : `{TARGET}` (yards). Validation `GroupKFold`, "
              f"group = `nfl_id`, {N_SPLITS} plis.\n")
    out.write(f"- Modèle A = Combine traditionnel ; Modèle B = A + capteurs 40-yard.\n")
    out.write(f"- Imputation médiane ajustée dans le pli (pas de fuite). "
              f"NGS scores exclus.\n")
    out.write(f"- Cohorte : {n_players} WR.\n\n")
    out.write("## Résultats\n\n")
    out.write(_results_table(results))
    out.write(_improvement_table(results))
    out.write("\n> R² ≤ 0 = le modèle ne bat pas la simple moyenne (attendu "
              "au niveau *action* : la séparation dépend surtout du contexte "
              "intra-joueur, non des features athlétiques constantes).\n")
    out.write("\n## Exploratoire — agilité (corrélations, petit N)\n\n")
    out.write("⚠️ Features 3-cone / shuttle trop éparses pour un modèle fiable. "
              "Corrélations indicatives seulement (par joueur) :\n\n")
    if agility.empty:
        out.write("_Aucune feature d'agilité exploitable._\n")
    else:
        out.write("feature | pearson_r | n_joueurs\n---|---|---\n")
        for _, r in agility.iterrows():
            out.write(f"`{r['feature']}` | {r['pearson_r']:+.3f} | {int(r['n_players'])}\n")
    return out.getvalue()


# ---------------------------------------------------------------------------
# Point d'entrée
# ---------------------------------------------------------------------------


def run() -> Path:
    """Exécute la baseline (deux outcomes) et écrit le rapport."""
    import sys
    try:  # console Windows : autoriser les caractères Unicode (Δ, −, ≤)
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # pragma: no cover
        pass
    logger = config.get_logger("kaggle_2027.baseline")
    out_dir = config.ensure_output_dir()
    df = load_dataset(out_dir)
    logger.info("Dataset : %d actions, %d joueurs", len(df), df["nfl_id"].nunique())

    # Outcome 1 : par action.
    action_res = evaluate_outcome(
        df, df[TARGET], df["nfl_id"], label="par_action"
    )

    # Outcome 2 : par joueur.
    players = per_player_frame(df)
    player_res = evaluate_outcome(
        players, players["sep_mean"], players["nfl_id"], label="par_joueur"
    )

    results = pd.concat([action_res, player_res], ignore_index=True)
    agility = agility_correlations(players)

    report = render_report(results, agility, n_players=players.shape[0])
    report_path = out_dir / "baseline_report.md"
    report_path.write_text(report, encoding="utf-8")
    results.to_csv(out_dir / "baseline_metrics.csv", index=False)

    print("\n" + _results_table(results))
    print(_improvement_table(results))
    logger.info("Rapport baseline écrit : %s", report_path)
    return report_path


if __name__ == "__main__":
    run()

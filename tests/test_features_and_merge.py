"""Tests d'extraction de features et de jointure sur nfl_id."""

import numpy as np
import pandas as pd
import pytest

from src.kaggle_2027 import combine_features, merge_combine_nfl, nfl_features


# --- route_family ----------------------------------------------------------


def test_route_family_known_values():
    assert nfl_features.route_family("HITCH") == "HARD_STOP"
    assert nfl_features.route_family("GO") == "VERTICAL"
    assert nfl_features.route_family("SLANT") == "IN_BREAKING"
    assert nfl_features.route_family("CORNER") == "OUT_BREAKING"


def test_route_family_unknown_and_missing():
    assert nfl_features.route_family("TOTALLY_MADE_UP") is None
    assert nfl_features.route_family(np.nan) is None
    assert nfl_features.route_family(None) is None


# --- instance_features -----------------------------------------------------


def _synthetic_sprint(n: int = 40, dt: float = 0.1) -> pd.DataFrame:
    """Sprint synthétique : accélération puis plateau, en ligne droite sur x."""
    t = np.arange(n) * dt
    peak = 10.0
    ramp_end = int(n * 0.6)
    speed = np.concatenate([
        np.linspace(0.0, peak, ramp_end),
        np.full(n - ramp_end, peak),
    ])
    x = np.cumsum(speed) * dt  # distance ~ vitesse*dt
    y = np.zeros(n)
    dis = speed * dt
    start = pd.Timestamp("2025-03-01T12:00:00")
    time = start + pd.to_timedelta(t, unit="s")
    return pd.DataFrame({"time": time, "x": x, "y": y, "s": speed, "dis": dis})


def test_instance_features_sprint_values_are_plausible():
    feats = combine_features.instance_features(_synthetic_sprint())
    assert feats is not None
    # vitesse de pointe proche de 10 (lissage léger).
    assert feats["peak_speed"] == pytest.approx(10.0, abs=0.5)
    # accélération initiale strictement positive.
    assert feats["initial_acceleration"] > 0
    # temps pour atteindre la pointe positif et borné par la durée.
    assert 0 < feats["time_to_peak_speed"] <= 4.0
    # vitesse au split de 10 yd renseignée et <= pointe.
    assert 0 < feats["speed_at_split"] <= feats["peak_speed"] + 1e-6


def test_instance_features_too_short_returns_none():
    short = _synthetic_sprint(n=5)
    assert combine_features.instance_features(short) is None


def test_instance_features_keys_present():
    feats = combine_features.instance_features(_synthetic_sprint())
    expected = {
        "peak_speed", "initial_acceleration", "time_to_peak_speed",
        "speed_at_split", "peak_deceleration", "turn_transition_time",
        "exit_acceleration", "min_turn_speed", "speed_retention",
        "path_efficiency",
    }
    assert expected.issubset(feats.keys())


# --- jointure sur nfl_id ---------------------------------------------------


def test_merge_datasets_inner_join_on_nfl_id():
    player_combine = pd.DataFrame({
        "nfl_id": [1, 2],
        "player": ["A", "B"],
        "combine_year": [2023, 2024],
        "forty": [4.4, 4.5],
    })
    nfl = pd.DataFrame({
        "nfl_id": [1, 1, 2, 999],  # 999 absent du Combine
        "game_id": [10, 10, 20, 30],
        "play_id": [1, 2, 1, 1],
        "season": [2023, 2023, 2024, 2024],
        "separation_at_throw": [2.0, 3.0, 1.5, 4.0],
    })
    merged = merge_combine_nfl.merge_datasets(player_combine, nfl)
    # inner join : la ligne nfl_id=999 (sans Combine) est écartée.
    assert len(merged) == 3
    assert set(merged["nfl_id"]) == {1, 2}
    # les features joueur sont bien propagées à chaque action.
    rows_player_a = merged[merged["nfl_id"] == 1]
    assert (rows_player_a["player"] == "A").all()
    assert (rows_player_a["forty"] == 4.4).all()


def test_merge_datasets_preserves_all_columns():
    player_combine = pd.DataFrame(
        {"nfl_id": [1], "player": ["A"], "combine_year": [2023], "forty": [4.4]}
    )
    nfl = pd.DataFrame({
        "nfl_id": [1], "game_id": [10], "play_id": [1], "season": [2023],
        "separation_at_throw": [2.0], "route_family": ["VERTICAL"],
    })
    merged = merge_combine_nfl.merge_datasets(player_combine, nfl)
    for col in ("nfl_id", "player", "forty", "route_family", "separation_at_throw"):
        assert col in merged.columns

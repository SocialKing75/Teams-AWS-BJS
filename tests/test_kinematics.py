"""Tests des fonctions cinématiques pures (calculs critiques)."""

import numpy as np
import pytest

from src.kaggle_2027 import kinematics


def test_euclidean_triangle_3_4_5():
    assert kinematics.euclidean(0.0, 0.0, 3.0, 4.0) == pytest.approx(5.0)


def test_euclidean_symmetric_and_zero():
    assert kinematics.euclidean(1.0, 2.0, 1.0, 2.0) == pytest.approx(0.0)
    assert kinematics.euclidean(1.0, 2.0, 4.0, 6.0) == pytest.approx(
        kinematics.euclidean(4.0, 6.0, 1.0, 2.0)
    )


def test_signed_acceleration_constant_slope():
    speed = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    time_s = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    accel = kinematics.signed_acceleration(speed, time_s)
    assert np.allclose(accel, 1.0)


def test_signed_acceleration_detects_braking():
    # vitesse qui monte puis chute : l'accélération signée devient négative.
    speed = np.array([0.0, 2.0, 4.0, 2.0, 0.0])
    time_s = np.arange(5, dtype=float)
    accel = kinematics.signed_acceleration(speed, time_s)
    assert accel.min() < 0  # freinage détecté
    assert accel.max() > 0  # accélération détectée


def test_signed_acceleration_too_short():
    assert np.array_equal(
        kinematics.signed_acceleration(np.array([1.0]), np.array([0.0])),
        np.zeros(1),
    )


def test_smooth_preserves_length_and_reduces_spike():
    values = np.array([0.0, 0.0, 9.0, 0.0, 0.0])
    smoothed = kinematics.smooth(values, window=3)
    assert smoothed.shape == values.shape
    assert smoothed[2] < values[2]  # le pic est atténué
    assert smoothed[2] == pytest.approx(3.0)  # (0+9+0)/3


def test_smooth_window_one_is_identity():
    values = np.array([1.0, 2.0, 3.0])
    assert np.array_equal(kinematics.smooth(values, window=1), values)


def test_path_length_and_net_displacement():
    dis = np.array([1.0, 1.0, 1.0, 1.0])
    assert kinematics.path_length(dis) == pytest.approx(4.0)
    # aller-retour sur x : déplacement net plus court que le chemin parcouru.
    x = np.array([0.0, 1.0, 2.0, 1.0, 0.0])
    y = np.zeros(5)
    assert kinematics.net_displacement(x, y) == pytest.approx(0.0)


def test_window_creation_sign():
    # séparation qui augmente pendant le vol => création positive.
    assert kinematics.window_creation(5.0, 2.0) == pytest.approx(3.0)
    # séparation qui diminue => création négative.
    assert kinematics.window_creation(1.0, 4.0) == pytest.approx(-3.0)

#!/usr/bin/env python3
"""
Script de validation des contraintes physiques sur les données NFL.

Usage:
    python scripts/validate_physics.py [--tracking-file FILE] [--verbose]

Vérifie:
  - Vitesses maximales (s ≤ 13.0 yards/s)
  - Accélérations (a ≤ 8.0 yards/s²)
  - Coordonnées terrain (x ∈ [0,120], y ∈ [0,53.3])
  - Cohérence temporelle (frameId consécutifs)
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List

# ============================================================================
# CONSTANTES PHYSIQUES
# ============================================================================

MAX_SPEED = 13.0          # yards/s (~23 mph)
MAX_ACCELERATION = 8.0    # yards/s²
FIELD_LENGTH = 120.0      # yards (incluant end zones)
FIELD_WIDTH = 53.3        # yards
FRAME_RATE = 10.0         # Hz
DT = 1.0 / FRAME_RATE     # 0.1 secondes entre frames

# ============================================================================
# FONCTIONS DE VALIDATION
# ============================================================================

def validate_speed(tracking_df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les violations de vitesse maximale."""
    violations = tracking_df[tracking_df['s'] > MAX_SPEED].copy()
    violations['violation_type'] = 'speed'
    violations['limit'] = MAX_SPEED
    violations['severity'] = (violations['s'] - MAX_SPEED) / MAX_SPEED
    
    return violations[['gameId', 'playId', 'nflId', 'frameId', 's', 
                       'violation_type', 'limit', 'severity']]


def validate_acceleration(tracking_df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les violations d'accélération maximale."""
    # Trier par joueur et frame
    df_sorted = tracking_df.sort_values(['nflId', 'frameId']).copy()
    
    # Calculer accélération dérivée
    df_sorted['accel_calc'] = (
        df_sorted.groupby('nflId')['s'].diff() / DT
    )
    
    # Violations (valeur absolue car décélération aussi contrainte)
    violations = df_sorted[
        (df_sorted['accel_calc'].abs() > MAX_ACCELERATION) &
        df_sorted['accel_calc'].notna()
    ].copy()
    
    violations['violation_type'] = 'acceleration'
    violations['limit'] = MAX_ACCELERATION
    violations['severity'] = (violations['accel_calc'].abs() - MAX_ACCELERATION) / MAX_ACCELERATION
    
    return violations[['gameId', 'playId', 'nflId', 'frameId', 'accel_calc', 
                       'violation_type', 'limit', 'severity']]


def validate_field_bounds(tracking_df: pd.DataFrame) -> pd.DataFrame:
    """Identifie les joueurs hors limites du terrain."""
    violations = tracking_df[
        (tracking_df['x'] < 0) | (tracking_df['x'] > FIELD_LENGTH) |
        (tracking_df['y'] < 0) | (tracking_df['y'] > FIELD_WIDTH)
    ].copy()
    
    violations['violation_type'] = 'out_of_bounds'
    violations['coords'] = violations.apply(
        lambda row: f"({row['x']:.1f}, {row['y']:.1f})", axis=1
    )
    
    return violations[['gameId', 'playId', 'nflId', 'frameId', 'x', 'y', 
                       'violation_type', 'coords']]


def validate_frame_continuity(tracking_df: pd.DataFrame) -> Dict[str, int]:
    """Vérifie la continuité des frames par jeu."""
    issues = []
    
    for (game_id, play_id), group in tracking_df.groupby(['gameId', 'playId']):
        frames = sorted(group['frameId'].unique())
        
        # Vérifier continuité
        expected_frames = range(frames[0], frames[-1] + 1)
        missing_frames = set(expected_frames) - set(frames)
        
        if missing_frames:
            issues.append({
                'gameId': game_id,
                'playId': play_id,
                'missing_frames': len(missing_frames),
                'total_expected': len(expected_frames)
            })
    
    return pd.DataFrame(issues)


# ============================================================================
# RAPPORT DE VALIDATION
# ============================================================================

def generate_report(
    tracking_df: pd.DataFrame,
    speed_violations: pd.DataFrame,
    accel_violations: pd.DataFrame,
    bounds_violations: pd.DataFrame,
    frame_issues: pd.DataFrame,
    verbose: bool = False
) -> None:
    """Génère rapport de validation."""
    
    total_frames = len(tracking_df)
    total_plays = tracking_df[['gameId', 'playId']].drop_duplicates().shape[0]
    
    print("=" * 70)
    print("🔬 NFL Physics Validation Report")
    print("=" * 70)
    print(f"Dataset: {total_frames:,} frames across {total_plays} plays")
    print()
    
    # 1. Vitesse
    n_speed_violations = len(speed_violations)
    speed_rate = (n_speed_violations / total_frames) * 100
    
    print(f"1. Speed Violations (s > {MAX_SPEED} yd/s)")
    print(f"   Count: {n_speed_violations} ({speed_rate:.2f}%)")
    
    if n_speed_violations > 0:
        max_speed_recorded = speed_violations['s'].max()
        print(f"   Max Speed Recorded: {max_speed_recorded:.2f} yd/s")
        print(f"   Severity Range: {speed_violations['severity'].min():.1%} - {speed_violations['severity'].max():.1%}")
        
        if verbose and n_speed_violations <= 10:
            print("\n   Details:")
            for _, row in speed_violations.iterrows():
                print(f"     Game {row['gameId']}, Play {row['playId']}, Player {row['nflId']}")
                print(f"     Frame {row['frameId']}: s={row['s']:.2f} yd/s (excess: {row['s'] - MAX_SPEED:.2f})")
    
    print()
    
    # 2. Accélération
    n_accel_violations = len(accel_violations)
    accel_rate = (n_accel_violations / total_frames) * 100
    
    print(f"2. Acceleration Violations (|a| > {MAX_ACCELERATION} yd/s²)")
    print(f"   Count: {n_accel_violations} ({accel_rate:.2f}%)")
    
    if n_accel_violations > 0:
        max_accel = accel_violations['accel_calc'].abs().max()
        print(f"   Max Acceleration: {max_accel:.2f} yd/s²")
        print(f"   Note: May include GPS noise/jitter")
    
    print()
    
    # 3. Hors limites
    n_bounds_violations = len(bounds_violations)
    bounds_rate = (n_bounds_violations / total_frames) * 100
    
    print(f"3. Out of Bounds Violations")
    print(f"   Count: {n_bounds_violations} ({bounds_rate:.2f}%)")
    
    if n_bounds_violations > 0:
        print(f"   ⚠️  WARNING: Players detected outside field boundaries!")
        
        if verbose and n_bounds_violations <= 10:
            print("\n   Details:")
            for _, row in bounds_violations.iterrows():
                print(f"     Game {row['gameId']}, Play {row['playId']}, Frame {row['frameId']}")
                print(f"     Position: {row['coords']}")
    
    print()
    
    # 4. Continuité frames
    n_frame_issues = len(frame_issues)
    
    print(f"4. Frame Continuity Issues")
    print(f"   Plays with Missing Frames: {n_frame_issues}")
    
    if n_frame_issues > 0:
        total_missing = frame_issues['missing_frames'].sum()
        print(f"   Total Missing Frames: {total_missing}")
        
        if verbose and n_frame_issues <= 5:
            print("\n   Details:")
            for _, row in frame_issues.iterrows():
                print(f"     Game {row['gameId']}, Play {row['playId']}")
                print(f"     Missing {row['missing_frames']} / {row['total_expected']} frames")
    
    print()
    print("=" * 70)
    
    # Verdict final
    if speed_rate < 1.0 and accel_rate < 5.0 and n_bounds_violations == 0:
        print("✅ PASSED: Data quality is acceptable")
    elif n_bounds_violations > 0 or speed_rate > 5.0:
        print("❌ FAILED: Critical violations detected")
        print("   Action: Review data preprocessing pipeline")
    else:
        print("⚠️  WARNING: Minor violations detected")
        print("   Recommendation: Apply noise filtering (e.g., Kalman filter)")
    
    print("=" * 70)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Validate NFL tracking data physics constraints'
    )
    parser.add_argument(
        '--tracking-file',
        type=str,
        default='data/tracking/tracking_2021091200.csv',
        help='Path to tracking CSV file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed violation examples'
    )
    
    args = parser.parse_args()
    
    # Charger données
    tracking_file = Path(args.tracking_file)
    
    if not tracking_file.exists():
        print(f"[ERROR] File not found: {tracking_file}")
        print(f"[INFO] Current directory: {Path.cwd()}")
        return 1
    
    print(f"Loading {tracking_file}...")
    tracking_df = pd.read_csv(tracking_file)
    print(f"Loaded {len(tracking_df):,} frames\n")
    
    # Exécuter validations
    print("Running validations...")
    speed_violations = validate_speed(tracking_df)
    accel_violations = validate_acceleration(tracking_df)
    bounds_violations = validate_field_bounds(tracking_df)
    frame_issues = validate_frame_continuity(tracking_df)
    
    # Générer rapport
    generate_report(
        tracking_df,
        speed_violations,
        accel_violations,
        bounds_violations,
        frame_issues,
        verbose=args.verbose
    )
    
    return 0


if __name__ == '__main__':
    exit(main())

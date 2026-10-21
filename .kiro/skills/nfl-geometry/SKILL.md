# SKILL: NFL Geometry & Physics

## Objectif
Fournir les outils mathématiques et physiques pour manipuler les données de tracking NFL (Next Gen Stats) avec rigueur géométrique et respect des contraintes physiques du football américain.

---

## 1. Système de Coordonnées NFL

### 1.1 Référentiel Standard
```
Terrain NFL: 120 yards × 53.3 yards
├─ X-axis: [0, 120] yards (longueur incluant end zones)
│  ├─ 0-10: End zone défense
│  ├─ 10-110: Terrain de jeu (100 yards)
│  └─ 110-120: End zone attaque
└─ Y-axis: [0, 53.3] yards (largeur)
   ├─ 0: Sideline bottom
   ├─ 26.65: Milieu terrain (hash marks)
   └─ 53.3: Sideline top
```

### 1.2 Convention d'Orientation (Angles NFL)
```python
# NFL utilise une convention horaire inversée:
# - 0° = Est (vers sideline droite)
# - 90° = Nord (vers end zone attaque)
# - 180° = Ouest (vers sideline gauche)
# - 270° = Sud (vers end zone défense)

def nfl_to_math_radians(angle_nfl: float) -> float:
    """
    Convertit angle NFL (0-360°) vers radians mathématiques standard.
    
    Args:
        angle_nfl: Angle en degrés NFL (0° = Est)
    
    Returns:
        Angle en radians (-π, π] où 0 = Est, π/2 = Nord
    """
    angle_math = (450 - angle_nfl) % 360
    return math.radians(angle_math)

def math_radians_to_nfl(angle_rad: float) -> float:
    """Conversion inverse."""
    angle_deg = math.degrees(angle_rad)
    return (450 - angle_deg) % 360
```

---

## 2. Normalisation Directionnelle

### 2.1 Principe de la Règle "Attaque Vers la Droite"
Tous les jeux doivent être transformés pour que l'attaque progresse vers X croissant (→), indépendamment de la direction initiale du drive.

```python
from typing import Tuple

def normalize_play_direction(
    x: float, 
    y: float, 
    dir_nfl: float, 
    o_nfl: float,
    play_direction: str
) -> Tuple[float, float, float, float]:
    """
    Normalise les coordonnées pour attaque vers droite.
    
    Args:
        x, y: Coordonnées originales
        dir_nfl: Direction de mouvement (0-360°)
        o_nfl: Orientation du corps (0-360°)
        play_direction: 'left' ou 'right'
    
    Returns:
        (x_norm, y_norm, dir_norm, o_norm)
    """
    if play_direction == 'left':
        # Miroir horizontal + rotation 180°
        x_norm = 120 - x
        y_norm = 53.3 - y
        dir_norm = (dir_nfl + 180) % 360
        o_norm = (o_nfl + 180) % 360
    else:
        x_norm, y_norm = x, y
        dir_norm, o_norm = dir_nfl, o_nfl
    
    return x_norm, y_norm, dir_norm, o_norm
```

### 2.2 Vérification Post-Normalisation
```python
def validate_normalized_play(tracking_df):
    """
    Vérifie que le QB progresse bien vers X croissant.
    """
    qb_frames = tracking_df[tracking_df['position'] == 'QB']
    x_start = qb_frames.iloc[0]['x']
    x_end = qb_frames.iloc[-1]['x']
    
    assert x_end >= x_start, f"QB recule: {x_start} → {x_end}"
```

---

## 3. Calculs Géométriques Fondamentaux

### 3.1 Distance Euclidienne 2D
```python
import numpy as np

def euclidean_distance(
    x1: float, y1: float, 
    x2: float, y2: float
) -> float:
    """Distance en yards entre deux points."""
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def vectorized_distances(
    x1: np.ndarray, y1: np.ndarray,
    x2: float, y2: float
) -> np.ndarray:
    """Distances vectorisées (broadcasting NumPy)."""
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
```

### 3.2 Vecteur Vitesse
```python
def velocity_components(speed: float, direction_nfl: float) -> Tuple[float, float]:
    """
    Décompose vitesse en composantes (vx, vy).
    
    Args:
        speed: Magnitude en yards/seconde
        direction_nfl: Angle de mouvement (0-360°)
    
    Returns:
        (vx, vy) en yards/seconde
    """
    theta = nfl_to_math_radians(direction_nfl)
    vx = speed * np.cos(theta)
    vy = speed * np.sin(theta)
    return vx, vy
```

### 3.3 Taux de Fermeture (Closing Rate)
```python
def compute_closing_rate(
    distances: np.ndarray, 
    dt: float = 0.1
) -> np.ndarray:
    """
    Calcule Δd/Δt entre frames consécutives.
    
    Args:
        distances: Array de distances [d_0, d_1, ..., d_n]
        dt: Intervalle temporel (0.1s pour 10 Hz)
    
    Returns:
        Closing rates [nan, (d_1-d_0)/dt, ..., (d_n-d_{n-1})/dt]
        - Négatif: fenêtre se referme
        - Positif: fenêtre s'ouvre
    """
    closing_rates = np.diff(distances, prepend=np.nan) / dt
    return closing_rates
```

---

## 4. Contraintes Physiques & Validation

### 4.1 Limites Physiques Humaines (NFL)
```python
PHYSICS_CONSTRAINTS = {
    'max_speed': 13.0,          # yards/s (~23 mph, record Tyreek Hill)
    'max_acceleration': 8.0,    # yards/s² (0-60 en ~3s)
    'max_deceleration': -10.0,  # yards/s² (freinage urgent)
    'min_reaction_time': 0.2,   # secondes (seuil neurologique)
}

def validate_speed(speed: float) -> bool:
    """Vérifie si vitesse est physiquement plausible."""
    return 0 <= speed <= PHYSICS_CONSTRAINTS['max_speed']

def validate_acceleration(v_prev: float, v_curr: float, dt: float = 0.1) -> bool:
    """Vérifie si accélération respecte limites biomécaniques."""
    accel = (v_curr - v_prev) / dt
    return PHYSICS_CONSTRAINTS['max_deceleration'] <= accel <= PHYSICS_CONSTRAINTS['max_acceleration']
```

### 4.2 Détection d'Anomalies
```python
def flag_anomalies(tracking_df):
    """
    Identifie frames suspects dans le tracking.
    
    Returns:
        DataFrame avec colonnes:
        - frame_id
        - anomaly_type: 'speed', 'acceleration', 'out_of_bounds'
        - value: Valeur mesurée
    """
    anomalies = []
    
    # Vitesse excessive
    speed_violations = tracking_df[tracking_df['s'] > PHYSICS_CONSTRAINTS['max_speed']]
    for _, row in speed_violations.iterrows():
        anomalies.append({
            'frameId': row['frameId'],
            'nflId': row['nflId'],
            'type': 'speed_exceeded',
            'value': row['s'],
            'limit': PHYSICS_CONSTRAINTS['max_speed']
        })
    
    # Hors limites terrain
    oob = tracking_df[
        (tracking_df['x'] < 0) | (tracking_df['x'] > 120) |
        (tracking_df['y'] < 0) | (tracking_df['y'] > 53.3)
    ]
    for _, row in oob.iterrows():
        anomalies.append({
            'frameId': row['frameId'],
            'nflId': row['nflId'],
            'type': 'out_of_bounds',
            'value': (row['x'], row['y'])
        })
    
    return pd.DataFrame(anomalies)
```

---

## 5. Fonctions Avancées

### 5.1 Projection de Position Future
```python
def project_position(
    x: float, y: float, 
    vx: float, vy: float, 
    time_delta: float
) -> Tuple[float, float]:
    """
    Prédit position future en assumant vitesse constante.
    
    Args:
        x, y: Position actuelle
        vx, vy: Composantes vitesse
        time_delta: Temps de projection (secondes)
    
    Returns:
        (x_future, y_future)
    """
    x_proj = x + vx * time_delta
    y_proj = y + vy * time_delta
    
    # Clamping aux limites du terrain
    x_proj = np.clip(x_proj, 0, 120)
    y_proj = np.clip(y_proj, 0, 53.3)
    
    return x_proj, y_proj
```

### 5.2 Calcul d'Intersection de Trajectoires
```python
def will_trajectories_intersect(
    x1: float, y1: float, vx1: float, vy1: float,
    x2: float, y2: float, vx2: float, vy2: float,
    max_time: float = 3.0,
    threshold: float = 1.0  # yards
) -> Tuple[bool, float]:
    """
    Détermine si deux joueurs vont entrer en collision.
    
    Returns:
        (will_collide, time_to_collision)
    """
    # Résolution vectorielle (position relative)
    dx = x2 - x1
    dy = y2 - y1
    dvx = vx2 - vx1
    dvy = vy2 - vy1
    
    # Si vitesses relatives nulles
    if np.abs(dvx) < 0.01 and np.abs(dvy) < 0.01:
        current_dist = np.sqrt(dx**2 + dy**2)
        return current_dist <= threshold, 0.0
    
    # Temps où distance est minimale (dérivée = 0)
    t_min = -(dx*dvx + dy*dvy) / (dvx**2 + dvy**2)
    t_min = max(0, min(t_min, max_time))  # Clamping
    
    # Distance minimale
    dx_at_t = dx + dvx * t_min
    dy_at_t = dy + dvy * t_min
    min_dist = np.sqrt(dx_at_t**2 + dy_at_t**2)
    
    return min_dist <= threshold, t_min
```

---

## 6. Pipeline de Traitement Type

### Exemple Complet : Analyse d'une Passe
```python
import pandas as pd
import numpy as np

def analyze_pass_play(
    tracking_df: pd.DataFrame,
    plays_df: pd.DataFrame,
    game_id: int,
    play_id: int
) -> dict:
    """
    Analyse complète d'un jeu de passe.
    
    Returns:
        {
            'flight_duration': float,
            'min_separation': float,
            'avg_closing_rate': float,
            'wr_top_speed': float,
            'cb_top_speed': float
        }
    """
    # 1. Filtrer le jeu
    play = plays_df[
        (plays_df['gameId'] == game_id) & 
        (plays_df['playId'] == play_id)
    ].iloc[0]
    
    tracking = tracking_df[
        (tracking_df['gameId'] == game_id) & 
        (tracking_df['playId'] == play_id)
    ].copy()
    
    # 2. Normaliser direction
    tracking[['x', 'y', 'dir', 'o']] = tracking.apply(
        lambda row: normalize_play_direction(
            row['x'], row['y'], row['dir'], row['o'], 
            play['playDirection']
        ), axis=1, result_type='expand'
    )
    
    # 3. Isoler phase de vol
    release_frame = tracking[tracking['event'] == 'pass_release']['frameId'].min()
    arrival_frame = tracking[tracking['event'] == 'pass_arrived']['frameId'].max()
    
    flight_phase = tracking[
        (tracking['frameId'] >= release_frame) & 
        (tracking['frameId'] <= arrival_frame)
    ]
    
    # 4. Identifier WR et CB principal
    wr = flight_phase[flight_phase['nflId'] == play['targetNflId']]
    # CB = défenseur le plus proche du WR à pass_release
    release_wr = wr[wr['frameId'] == release_frame].iloc[0]
    defenders = flight_phase[
        (flight_phase['position'].isin(['CB', 'SS', 'FS'])) &
        (flight_phase['frameId'] == release_frame)
    ]
    
    distances_at_release = vectorized_distances(
        defenders['x'].values, defenders['y'].values,
        release_wr['x'], release_wr['y']
    )
    cb_id = defenders.iloc[np.argmin(distances_at_release)]['nflId']
    cb = flight_phase[flight_phase['nflId'] == cb_id]
    
    # 5. Calculer métriques
    wr_cb_merged = pd.merge(
        wr[['frameId', 'x', 'y', 's']], 
        cb[['frameId', 'x', 'y', 's']], 
        on='frameId', 
        suffixes=('_wr', '_cb')
    )
    
    wr_cb_merged['distance'] = euclidean_distance(
        wr_cb_merged['x_wr'], wr_cb_merged['y_wr'],
        wr_cb_merged['x_cb'], wr_cb_merged['y_cb']
    )
    
    closing_rates = compute_closing_rate(wr_cb_merged['distance'].values)
    
    return {
        'flight_duration': len(wr_cb_merged) * 0.1,
        'min_separation': wr_cb_merged['distance'].min(),
        'avg_closing_rate': np.nanmean(closing_rates),
        'wr_top_speed': wr['s'].max(),
        'cb_top_speed': cb['s'].max(),
        'wr_route_length': wr[['x', 'y']].diff().apply(
            lambda row: np.sqrt(row['x']**2 + row['y']**2), axis=1
        ).sum()
    }
```

---

## 7. Références

### Standards NFL NGS
- Fréquence tracking: 10 Hz (1 frame/0.1s)
- Précision GPS: ±0.5 yards
- Latence système: <100ms

### Conversions Utiles
```python
CONVERSIONS = {
    'yards_to_meters': 0.9144,
    'mph_to_yards_per_sec': 1.467,
    'meters_per_sec_to_mph': 2.237,
}

def mph_to_yards_per_sec(mph: float) -> float:
    return mph * CONVERSIONS['mph_to_yards_per_sec']
```

### Bibliographie Recommandée
- *Mathematics of Football* (David Sumpter, 2016)
- *NFL Next Gen Stats API Documentation* (NFL, 2024)
- *Biomechanics of Sprint Running* (Weyand et al., 2000)

---

**Version** : 1.0.0  
**Dernière MAJ** : 2026-10-21  
**Mainteneur** : Équipe Coach Cockpit NFL

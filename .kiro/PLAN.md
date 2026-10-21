# PLAN.md — Feuille de Route Coach Cockpit NFL

## Vue d'Ensemble

Ce document organise le développement du **Coach Cockpit NFL** en phases exécutables, avec requêtes DuckDB MCP prêtes à l'emploi et points de validation.

---

## Phase 1 : Infrastructure & Exploration Données (Semaine 1)

### 1.1 Configuration Environnement

**Objectif** : Préparer l'environnement de développement local.

**Actions** :
```bash
# Installation dépendances Python
pip install pandas numpy scipy pytest black isort

# Installation dépendances React
npm install
npm install react-plotly.js plotly.js recharts
npm install -D @testing-library/react @testing-library/user-event vitest

# Configuration Tailwind CSS
npx tailwindcss init -p
```

**Validation** :
- [ ] `pytest --version` fonctionne
- [ ] `npm run dev` lance le serveur Vite
- [ ] MCP DuckDB accessible via `/api/duckdb/query`

---

### 1.2 Exploration Schéma Données

**Requête MCP 1 : Inspection Colonnes Tracking**
```sql
-- Découvrir structure des fichiers tracking
DESCRIBE SELECT * 
FROM read_csv_auto('data/tracking/tracking_2021091200.csv') 
LIMIT 0;
```

**Résultat Attendu** :
```
column_name | column_type | null
------------|-------------|-----
gameId      | BIGINT      | YES
playId      | BIGINT      | YES
nflId       | BIGINT      | YES
frameId     | BIGINT      | YES
time        | VARCHAR     | YES
x           | DOUBLE      | YES
y           | DOUBLE      | YES
s           | DOUBLE      | YES   -- Vitesse (yards/s)
a           | DOUBLE      | YES   -- Accélération (yards/s²)
dis         | DOUBLE      | YES   -- Distance parcourue
o           | DOUBLE      | YES   -- Orientation corps
dir         | DOUBLE      | YES   -- Direction mouvement
event       | VARCHAR     | YES   -- pass_release, ball_land, etc.
```

---

**Requête MCP 2 : Statistiques Événements**
```sql
-- Compter occurrences événements clés
SELECT 
  event,
  COUNT(*) AS n_occurrences,
  COUNT(DISTINCT gameId || '_' || playId) AS n_unique_plays
FROM read_csv_auto('data/tracking/*.csv')
WHERE event IS NOT NULL
  AND event IN (
    'pass_forward', 
    'pass_release', 
    'pass_arrived', 
    'ball_land',
    'pass_outcome_caught',
    'pass_outcome_incomplete',
    'pass_outcome_interception'
  )
GROUP BY event
ORDER BY n_occurrences DESC;
```

**Validation** :
- [ ] `pass_release` et `ball_land` ont un ratio 1:1 (ou proche)
- [ ] Au moins 1000+ jeux de passe dans le dataset

---

**Requête MCP 3 : Joindre Plays + Tracking**
```sql
-- Vérifier qualité jointure
SELECT 
  p.gameId,
  p.playId,
  p.playDescription,
  p.passResult,
  p.playDirection,
  COUNT(t.frameId) AS n_frames
FROM read_csv_auto('data/plays.csv') p
JOIN read_csv_auto('data/tracking/*.csv') t
  ON p.gameId = t.gameId AND p.playId = t.playId
WHERE p.passResult IS NOT NULL  -- Jeux de passe uniquement
GROUP BY p.gameId, p.playId, p.playDescription, p.passResult, p.playDirection
LIMIT 10;
```

**Validation** :
- [ ] `n_frames` typiquement entre 50-150 (5-15 secondes à 10 Hz)
- [ ] `playDirection` contient 'left' et 'right'

---

### 1.3 Validation Contraintes Physiques

**Script Python** : `scripts/validate_physics.py`
```python
import pandas as pd
import numpy as np

# Constantes physiques
MAX_SPEED = 13.0  # yards/s
MAX_ACCEL = 8.0   # yards/s²

# Charger échantillon
tracking_sample = pd.read_csv('data/tracking/tracking_2021091200.csv')

# Anomalies vitesse
speed_violations = tracking_sample[tracking_sample['s'] > MAX_SPEED]
print(f"Speed violations: {len(speed_violations)} / {len(tracking_sample)}")
print(speed_violations[['nflId', 'frameId', 's']].head())

# Anomalies accélération
tracking_sample = tracking_sample.sort_values(['nflId', 'frameId'])
tracking_sample['accel_calc'] = (
    tracking_sample.groupby('nflId')['s'].diff() / 0.1
)
accel_violations = tracking_sample[
    (tracking_sample['accel_calc'].abs() > MAX_ACCEL) & 
    tracking_sample['accel_calc'].notna()
]
print(f"Accel violations: {len(accel_violations)}")

# Hors limites terrain
oob = tracking_sample[
    (tracking_sample['x'] < 0) | (tracking_sample['x'] > 120) |
    (tracking_sample['y'] < 0) | (tracking_sample['y'] > 53.3)
]
print(f"Out of bounds: {len(oob)}")
```

**Validation** :
- [ ] < 1% de violations vitesse
- [ ] < 5% de violations accélération (tolérance bruit GPS)
- [ ] 0 frames hors limites terrain

---

## Phase 2 : Moteur de Calcul (Semaines 2-3)

### 2.1 Isolation Phase de Vol

**Requête MCP 4 : Extraire Phase Vol d'un Jeu**
```sql
-- Isoler frames entre pass_release et ball_land
WITH play_events AS (
  SELECT 
    gameId, 
    playId,
    MIN(CASE WHEN event = 'pass_release' THEN frameId END) AS release_frame,
    MAX(CASE WHEN event IN ('ball_land', 'pass_arrived') THEN frameId END) AS land_frame
  FROM read_csv_auto('data/tracking/*.csv')
  WHERE gameId = 2021091200 AND playId = 97  -- Exemple
  GROUP BY gameId, playId
)
SELECT 
  t.*
FROM read_csv_auto('data/tracking/*.csv') t
JOIN play_events pe 
  ON t.gameId = pe.gameId 
  AND t.playId = pe.playId
WHERE t.frameId BETWEEN pe.release_frame AND pe.land_frame
ORDER BY t.frameId, t.nflId;
```

**Script Python** : `src/engine/isolation.py`
```python
import pandas as pd
from typing import Tuple

def isolate_flight_phase(
    tracking_df: pd.DataFrame,
    game_id: int,
    play_id: int
) -> pd.DataFrame:
    """
    Extrait la phase de vol entre pass_release et ball_land.
    
    Returns:
        DataFrame avec colonnes: frameId, nflId, x, y, s, dir, o, event
    """
    play_tracking = tracking_df[
        (tracking_df['gameId'] == game_id) & 
        (tracking_df['playId'] == play_id)
    ].copy()
    
    # Identifier frames clés
    release_frame = play_tracking[
        play_tracking['event'] == 'pass_release'
    ]['frameId'].min()
    
    land_frame = play_tracking[
        play_tracking['event'].isin(['ball_land', 'pass_arrived'])
    ]['frameId'].max()
    
    if pd.isna(release_frame) or pd.isna(land_frame):
        raise ValueError(f"Missing events for game {game_id}, play {play_id}")
    
    # Filtrer phase vol
    flight_phase = play_tracking[
        (play_tracking['frameId'] >= release_frame) & 
        (play_tracking['frameId'] <= land_frame)
    ]
    
    return flight_phase.sort_values(['frameId', 'nflId'])

# Test
if __name__ == '__main__':
    tracking = pd.read_csv('data/tracking/tracking_2021091200.csv')
    flight = isolate_flight_phase(tracking, 2021091200, 97)
    print(f"Flight phase: {len(flight)} frames")
    print(f"Duration: {(flight['frameId'].max() - flight['frameId'].min()) * 0.1:.1f}s")
```

**Tests Unitaires** : `tests/test_isolation.py`
```python
import pytest
import pandas as pd
from src.engine.isolation import isolate_flight_phase

def test_isolation_valid_play():
    # Mock data
    tracking = pd.DataFrame({
        'gameId': [2021] * 10,
        'playId': [1] * 10,
        'frameId': range(1, 11),
        'nflId': [123] * 10,
        'event': [None, 'pass_release', None, None, None, None, None, 'ball_land', None, None]
    })
    
    result = isolate_flight_phase(tracking, 2021, 1)
    
    assert len(result) == 7  # Frames 2-8
    assert result['frameId'].min() == 2
    assert result['frameId'].max() == 8

def test_isolation_missing_events():
    tracking = pd.DataFrame({
        'gameId': [2021] * 5,
        'playId': [1] * 5,
        'frameId': range(1, 6),
        'event': [None] * 5
    })
    
    with pytest.raises(ValueError, match="Missing events"):
        isolate_flight_phase(tracking, 2021, 1)
```

---

### 2.2 Calcul Closing Rate

**Script Python** : `src/engine/closing_rate.py`
```python
import numpy as np
import pandas as pd

def calculate_closing_rate(
    wr_positions: pd.DataFrame,   # Colonnes: frameId, x, y
    cb_positions: pd.DataFrame,   # Colonnes: frameId, x, y
    dt: float = 0.1               # Intervalle temporel (10 Hz)
) -> pd.DataFrame:
    """
    Calcule le taux de fermeture de la fenêtre WR-CB.
    
    Returns:
        DataFrame: frameId, distance, closing_rate
    """
    # Merge sur frameId
    merged = pd.merge(
        wr_positions, 
        cb_positions, 
        on='frameId', 
        suffixes=('_wr', '_cb')
    )
    
    # Distance euclidienne
    merged['distance'] = np.sqrt(
        (merged['x_wr'] - merged['x_cb'])**2 + 
        (merged['y_wr'] - merged['y_cb'])**2
    )
    
    # Closing rate (dérivée discrète)
    merged['closing_rate'] = merged['distance'].diff() / dt
    
    # Moyenne mobile 5 frames pour lisser
    merged['closing_rate_smooth'] = merged['closing_rate'].rolling(
        window=5, 
        center=True,
        min_periods=1
    ).mean()
    
    return merged[['frameId', 'distance', 'closing_rate', 'closing_rate_smooth']]

# Test
if __name__ == '__main__':
    wr = pd.DataFrame({
        'frameId': [1, 2, 3, 4, 5],
        'x': [30, 32, 34, 36, 38],
        'y': [26.65] * 5
    })
    cb = pd.DataFrame({
        'frameId': [1, 2, 3, 4, 5],
        'x': [28, 30, 33, 36, 39],
        'y': [26.65] * 5
    })
    
    result = calculate_closing_rate(wr, cb)
    print(result)
    # Attendu: closing_rate négatif (CB rattrape WR)
```

---

### 2.3 Agrégation par Route

**Requête MCP 5 : Métriques Globales par Route**
```sql
-- Calculer statistiques par type de route
WITH flight_metrics AS (
  SELECT 
    p.gameId,
    p.playId,
    pff.pff_routeConcept AS route_type,
    pff.pff_coverageType AS coverage_type,
    -- Ici on assume que closing_rate a été pré-calculé et stocké
    AVG(closing_data.closing_rate) AS avg_closing_rate,
    MIN(closing_data.distance) AS min_separation
  FROM read_csv_auto('data/plays.csv') p
  JOIN read_csv_auto('data/pffScoutingData.csv') pff
    ON p.gameId = pff.gameId AND p.playId = pff.playId
  -- JOIN avec table closing_rate calculée (voir Phase 3)
  GROUP BY p.gameId, p.playId, pff.pff_routeConcept, pff.pff_coverageType
)
SELECT 
  route_type,
  coverage_type,
  COUNT(*) AS n_plays,
  AVG(avg_closing_rate) AS mean_closing_rate,
  STDDEV(avg_closing_rate) AS std_closing_rate,
  PERCENTILE_CONT(0.1) WITHIN GROUP (ORDER BY avg_closing_rate) AS p10,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY avg_closing_rate) AS p90,
  -- Success = fenêtre reste ouverte (min_separation > 3 yards)
  SUM(CASE WHEN min_separation > 3.0 THEN 1 ELSE 0 END)::FLOAT / COUNT(*) AS success_rate
FROM flight_metrics
WHERE route_type IS NOT NULL
GROUP BY route_type, coverage_type
ORDER BY mean_closing_rate DESC;
```

---

## Phase 3 : Interface React (Semaines 3-4)

### 3.1 Composant Heatmap

**Fichier** : `src/components/heatmap/HeatmapMatchup.tsx`  
**Référence** : Voir `.kiro/skills/react-coach-ui/SKILL.md` Section 2

**Actions** :
1. Créer composant selon template skill
2. Fetch données via hook `useClosingRateHeatmap()`
3. Tests unitaires avec Vitest

**Validation** :
- [ ] `npm run test -- HeatmapMatchup.test` passe
- [ ] Heatmap charge en < 2s avec 100+ cellules
- [ ] Click sur cellule déclenche `onCellClick` callback

---

### 3.2 Composant TimeSeries

**Fichier** : `src/components/timeseries/TimeSeriesClosing.tsx`  
**Référence** : Voir `.kiro/skills/react-coach-ui/SKILL.md` Section 3

**Actions** :
1. Implémenter avec Recharts
2. Intégrer zones rouges (distance < 3 yards)
3. Annotations événements (ball_arrived, tackle)

**Validation** :
- [ ] Graphiques responsive (mobile + desktop)
- [ ] Tooltip affiche valeurs précises (2 décimales)
- [ ] Accessibilité WCAG AA compliant

---

### 3.3 Page Dashboard Principale

**Fichier** : `src/pages/CockpitDashboard.tsx`  
**Référence** : Voir `.kiro/skills/react-coach-ui/SKILL.md` Section 8.1

**Layout** :
```
┌─────────────────────────────────────────────────────┐
│  🏈 Coach Cockpit – Window Erosion Analysis         │
├─────────────────────────┬───────────────────────────┤
│  Heatmap Matchup        │  TimeSeries (conditional) │
│  (Routes × Coverage)    │  ├─ Distance vs Time      │
│                         │  └─ Closing Rate vs Time  │
└─────────────────────────┴───────────────────────────┘
```

---

## Phase 4 : Hooks & Automatisation (Semaine 5)

### 4.1 Hook Physics Guardrail

**Fichier** : `.kiro/hooks/physics-guardrail.py`  
**Référence** : Voir ci-dessous (Section suivante)

**Déclencheur** : `PostToolUse` sur outils d'écriture (`fs_write`, `str_replace`)

**Action** :
1. Lire fichier Python modifié
2. Extraire constantes physiques (MAX_SPEED, MAX_ACCEL)
3. Valider qu'elles respectent les invariants

**Validation** :
- [ ] Hook s'exécute automatiquement après édition
- [ ] Alerte si MAX_SPEED > 13.0 yards/s

---

### 4.2 Hook Auto-Test

**Fichier JSON** : `.kiro/hooks/auto-test.json`
```json
{
  "version": "v1",
  "hooks": [{
    "name": "Run Pytest on Python Save",
    "trigger": "PostFileSave",
    "matcher": "\\.py$",
    "action": {
      "type": "command",
      "command": "pytest tests/ -v --tb=short"
    }
  }]
}
```

**Validation** :
- [ ] Sauvegarder un `.py` déclenche pytest
- [ ] Sortie terminal visible dans Kiro

---

## Phase 5 : Déploiement & Documentation (Semaine 6)

### 5.1 Build Production

```bash
# Frontend
npm run build
npm run preview  # Vérifier build

# Backend (si API Flask/FastAPI)
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

### 5.2 Documentation Utilisateur

**Fichier** : `docs/USER_GUIDE.md`

**Sections** :
1. Installation & Setup
2. Navigation Dashboard
3. Interprétation Heatmap (rouge = mauvais, vert = bon)
4. Cas d'Usage : Identifier routes vulnérables
5. Export Données CSV

---

## Jalons & Livrables

| Phase | Livrable | Date Cible | Status |
|-------|----------|------------|--------|
| 1 | Exploration données + validation physique | Semaine 1 | ⏳ |
| 2 | Moteur calcul closing rate | Semaine 2-3 | ⏳ |
| 3 | Interface React (Heatmap + TimeSeries) | Semaine 3-4 | ⏳ |
| 4 | Hooks automatisation | Semaine 5 | ⏳ |
| 5 | Build production + docs | Semaine 6 | ⏳ |

---

## Commandes Rapides

```bash
# Développement
npm run dev                    # Lancer frontend (Vite)
pytest tests/ -v               # Tests Python
npm run test                   # Tests React

# Qualité Code
black src/ tests/              # Formatter Python
npm run lint                   # Linter TypeScript/React
npm run type-check             # Vérification types

# Base de Données
duckdb                         # Ouvrir CLI DuckDB
.read scripts/init_db.sql      # Charger schéma
```

---

**Version** : 1.0.0  
**Dernière MAJ** : 2026-10-21  
**Mainteneur** : Équipe Coach Cockpit NFL

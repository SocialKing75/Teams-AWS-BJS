# PRODUCT-SPEC.md — Cockpit Coach NFL

## 1. Moteur de Calcul d'Érosion (Core Engine)

### [REQ-ENGINE-1 : Isolation de la Phase de Vol]

**WHEN** le jeu atteint l'événement `pass_release` (lancer du ballon),  
**THE SYSTEM SHALL** isoler les coordonnées (x,y) du WR ciblé et des défenseurs jusqu'à l'événement `ball_land`.

**Détails Techniques** :
- Extraire tous les frames entre `pass_release` <= frameId <= `ball_land`
- Identifier le WR ciblé via `pffScoutingData.csv` (colonne `targetNflId`)
- Identifier les défenseurs dans un rayon de 10 yards du WR au moment du `pass_release`
- Normaliser la direction du jeu (attaque vers la droite)

**Critères d'Acceptation** :
```python
def test_isolation_phase_vol():
    frames = isolate_flight_phase(gameId=2021091200, playId=97)
    assert frames['event'].iloc[0] == 'pass_release'
    assert frames['event'].iloc[-1] == 'ball_land'
    assert 'targetWR' in frames.columns
    assert len(frames['defenders']) >= 1
```

---

### [REQ-ENGINE-2 : Calcul du Taux d'Érosion]

**WHEN** la distance d(WR, CB) est calculée trame par trame (10 Hz),  
**THE SYSTEM SHALL** dériver le taux de fermeture de la fenêtre Δd/Δt (en yards/seconde).

**Formule** :
```python
# Distance euclidienne à chaque frame
d_t = sqrt((x_wr - x_cb)² + (y_wr - y_cb)²)

# Taux d'érosion (yards/seconde)
closing_rate = (d_t - d_{t-1}) / 0.1  # 10 Hz → 0.1s entre frames

# Négatif = fenêtre se referme
# Positif = fenêtre s'ouvre
```

**Critères d'Acceptation** :
- closing_rate > -8.0 yards/s (contrainte accélération physique)
- Moyenne mobile sur 5 frames pour lisser le bruit
- Alerte si closing_rate < -6.0 (fermeture rapide)

---

### [REQ-ENGINE-3 : Agrégation par Route]

**WHEN** plusieurs jeux avec la même route du WR sont analysés,  
**THE SYSTEM SHALL** calculer les statistiques suivantes :

- **Closing Rate Moyen** : E[Δd/Δt] sur tous les jeux
- **Écart-type** : σ(Δd/Δt) (mesure de variance)
- **Percentile 10/90** : Scénarios optimiste/pessimiste
- **Success Rate** : % de jeux où la fenêtre reste ouverte (d > 3 yards à `ball_land`)

**Sortie Attendue** :
```json
{
  "route_pattern": "slant",
  "n_plays": 47,
  "avg_closing_rate": -1.23,
  "std_closing_rate": 0.87,
  "p10_closing_rate": -2.81,
  "p90_closing_rate": 0.35,
  "success_rate": 0.68
}
```

---

## 2. Composants Interface Utilisateur React

### [REQ-UI-HEATMAP : Matrice des Matchups]

**WHEN** l'utilisateur charge le Cockpit Coach,  
**THE SYSTEM SHALL** afficher un composant React `<HeatmapMatchup />` montrant :

**Axes** :
- X : Type de route du WR (slant, go, out, corner, post)
- Y : Position initiale du CB (press, off, bail)

**Couleur** :
- Rouge : Closing rate < -3.0 (fenêtre se referme rapidement)
- Jaune : -3.0 ≤ closing rate ≤ -1.0 (neutre)
- Vert : closing rate > -1.0 (fenêtre reste ouverte)

**Interactions** :
- Hover : Afficher closing_rate moyen + écart-type
- Click : Ouvrir TimeSeries détaillé du matchup

**Technologie** :
```tsx
import Plot from 'react-plotly.js';

<Plot
  data={[{
    z: closingRateMatrix,
    type: 'heatmap',
    colorscale: 'RdYlGn',
    reversescale: true
  }]}
  layout={{
    title: 'Érosion de Fenêtre par Route & Coverage',
    xaxis: { title: 'Route Type' },
    yaxis: { title: 'CB Alignment' }
  }}
/>
```

---

### [REQ-UI-TIMESERIES : Évolution Temporelle d'une Passe]

**WHEN** l'utilisateur clique sur un matchup dans la heatmap,  
**THE SYSTEM SHALL** afficher `<TimeSeriesClosing />` avec :

**Graphique 1 : Distance vs Temps**
- Axe X : Temps depuis pass_release (secondes)
- Axe Y : Distance WR-CB (yards)
- Ligne : Trajectoire de la distance
- Zone rouge : d < 3 yards (fenêtre fermée)

**Graphique 2 : Closing Rate vs Temps**
- Axe X : Temps (s)
- Axe Y : Δd/Δt (yards/s)
- Ligne 0 : Seuil de neutralité
- Annotations : Événements clés (ball_arrived, tackle)

**Critères d'Acceptation** :
```tsx
describe('TimeSeriesClosing', () => {
  it('should display distance line chart', () => {
    render(<TimeSeriesClosing gameId={2021} playId={97} />);
    expect(screen.getByText(/Distance WR-CB/)).toBeInTheDocument();
  });

  it('should highlight closing events', () => {
    const { container } = render(<TimeSeriesClosing {...props} />);
    const redZone = container.querySelector('[fill="rgba(255,0,0,0.2)"]');
    expect(redZone).toBeTruthy();
  });
});
```

---

### [REQ-UI-ROUTE : Visualisation 2D du Terrain]

**WHEN** l'utilisateur sélectionne "Voir Animation",  
**THE SYSTEM SHALL** afficher `<RouteVisualization />` avec :

**Éléments** :
- Terrain NFL (120x53.3 yards) avec marquages
- Trajectoires WR/CB (lignes colorées)
- Frames animées (slider temporel)
- Vecteurs vitesse (flèches orientation)

**Contrôles** :
- Play/Pause animation
- Slider : Scrub à travers les frames
- Zoom : Focus sur zone d'action (±15 yards du WR)

**Technologie** :
```tsx
import { Scatter } from 'react-chartjs-2';

const data = {
  datasets: [
    {
      label: 'WR Route',
      data: wrTrajectory.map(f => ({ x: f.x, y: f.y })),
      borderColor: 'blue',
      pointRadius: 3
    },
    {
      label: 'CB Coverage',
      data: cbTrajectory.map(f => ({ x: f.x, y: f.y })),
      borderColor: 'red',
      pointRadius: 3
    }
  ]
};
```

---

## 3. Requêtes DuckDB via MCP

### [REQ-DATA-1 : Joindre Tracking + Plays + PFF]

**SQL** :
```sql
-- Isoler phase de vol pour un jeu donné
WITH flight_phase AS (
  SELECT 
    t.*,
    p.passResult,
    p.offenseFormation,
    pff.pff_role,
    pff.pff_positionLinedUp
  FROM read_csv_auto('data/tracking/*.csv') t
  JOIN read_csv_auto('data/plays.csv') p 
    ON t.gameId = p.gameId AND t.playId = p.playId
  LEFT JOIN read_csv_auto('data/pffScoutingData.csv') pff
    ON t.gameId = pff.gameId 
    AND t.playId = pff.playId 
    AND t.nflId = pff.nflId
  WHERE t.gameId = ? 
    AND t.playId = ?
    AND t.event IN ('pass_release', 'pass_arrived', 'ball_land')
)
SELECT * FROM flight_phase;
```

**Paramètres** :
- `gameId` : Integer (ex: 2021091200)
- `playId` : Integer (ex: 97)

**Colonnes Critiques** :
- `t.x`, `t.y`, `t.s`, `t.dir`, `t.o` (tracking)
- `p.passResult` : Complete/Incomplete (outcome)
- `pff.pff_role` : Pass Route / Coverage (rôle joueur)

---

### [REQ-DATA-2 : Agréger Métriques par Route]

**SQL** :
```sql
-- Calcul des closing rates moyens par type de route
WITH route_metrics AS (
  SELECT 
    pff.pff_routeConcept AS route_type,
    t.gameId,
    t.playId,
    -- Calculer distance minimale atteinte durant phase vol
    MIN(
      SQRT(
        POWER(t_wr.x - t_cb.x, 2) + 
        POWER(t_wr.y - t_cb.y, 2)
      )
    ) AS min_separation,
    -- Temps de vol (frames entre release et arrival)
    COUNT(*) * 0.1 AS flight_duration
  FROM read_csv_auto('data/tracking/*.csv') t
  JOIN read_csv_auto('data/pffScoutingData.csv') pff
    ON t.gameId = pff.gameId AND t.playId = pff.playId
  WHERE pff.pff_role = 'Pass Route'
    AND t.event BETWEEN 'pass_release' AND 'ball_land'
  GROUP BY pff.pff_routeConcept, t.gameId, t.playId
)
SELECT 
  route_type,
  COUNT(*) AS n_plays,
  AVG(min_separation) AS avg_min_separation,
  STDDEV(min_separation) AS std_min_separation,
  PERCENTILE_CONT(0.1) WITHIN GROUP (ORDER BY min_separation) AS p10,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY min_separation) AS p90
FROM route_metrics
GROUP BY route_type
ORDER BY avg_min_separation DESC;
```

---

## 4. Contraintes Non-Fonctionnelles

### [REQ-PERF-1 : Temps de Réponse]
- Chargement heatmap : < 2 secondes
- Animation route : 30 FPS minimum
- Requête DuckDB : < 500ms pour 1 jeu

### [REQ-SECURITY-1 : Données Sensibles]
- Pas de PII (Personally Identifiable Information)
- Données NFL publiques uniquement
- Pas d'authentification requise (usage interne)

### [REQ-COMPAT-1 : Navigateurs Supportés]
- Chrome 100+
- Firefox 100+
- Safari 15+
- Edge 100+

---

## 5. User Stories

### US-1 : Analyste Identifie Routes Vulnérables
**En tant qu'** analyste offensif,  
**Je veux** voir quelles routes subissent l'érosion la plus rapide contre Cover 2,  
**Afin de** éviter ces matchups dans le game plan.

**Acceptance** :
- [ ] Heatmap charge en < 2s
- [ ] Couleurs rouge/vert clairement distinguables
- [ ] Tooltip affiche closing rate ± std

---

### US-2 : Coach Visualise Passe Spécifique
**En tant que** coordinateur offensif,  
**Je veux** revoir l'animation d'une passe interceptée,  
**Afin de** comprendre quand la fenêtre s'est refermée.

**Acceptance** :
- [ ] Animation fluide (30 FPS)
- [ ] Slider permet de scrub temporellement
- [ ] Vecteurs vitesse affichent orientation joueurs

---

### US-3 : Data Scientist Exporte Métriques
**En tant que** data scientist,  
**Je veux** exporter les closing rates en CSV,  
**Afin de** les analyser dans Python/R.

**Acceptance** :
- [ ] Bouton "Export CSV" présent
- [ ] Fichier contient colonnes : gameId, playId, route, closing_rate, min_separation
- [ ] Format conforme RFC 4180

---

## 6. Roadmap

### Phase 1 : MVP (Semaines 1-2)
- [ ] REQ-ENGINE-1 : Isolation phase vol
- [ ] REQ-ENGINE-2 : Calcul closing rate
- [ ] REQ-DATA-1 : Requête DuckDB tracking + plays
- [ ] REQ-UI-HEATMAP : Heatmap basique Plotly

### Phase 2 : Visualisations (Semaines 3-4)
- [ ] REQ-UI-TIMESERIES : Graphiques distance/closing rate
- [ ] REQ-UI-ROUTE : Animation 2D terrain
- [ ] REQ-ENGINE-3 : Agrégation par route

### Phase 3 : Polish (Semaine 5)
- [ ] REQ-PERF-1 : Optimisation performance
- [ ] Tests end-to-end Playwright
- [ ] Documentation utilisateur

---

**Version** : 1.0.0  
**Auteur** : Équipe Coach Cockpit NFL  
**Dernière Révision** : 2026-10-21

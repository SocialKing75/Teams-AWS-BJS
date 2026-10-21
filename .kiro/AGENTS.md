# AGENTS.md — Constitution & Rules of Engagement

## 1. Directives Produit & Périmètre

- **Persona Unique** : Coordinateur Offensif / Coach NFL
- **Problématique Centrale** : « Dans quelles situations tactiques la fenêtre de réception se referme-t-elle le moins (ou le plus vite) ? »
- **Stack Technique** : 
  - Frontend : React (Vite / Next.js), Tailwind CSS, Plotly.js / Recharts
  - Backend : DuckDB / SQLite (via MCP)
  - Analysis : Python (pandas, numpy, scipy)

## 2. Invariants Physiques & Spatiaux (NFL NGS)

### 2.1 Repère Géométrique
- **Terrain NFL** : 
  - X ∈ [0, 120] yards (incluant end zones)
  - Y ∈ [0, 53.3] yards (largeur)
- **Conversion Angle NFL vers Radians** :
  ```
  θ_rad = radians((450 - angle_nfl) % 360)
  ```
  - NFL `dir` = 0° → Est (vers sideline droite)
  - NFL `dir` = 90° → Nord (vers end zone attaque)
  - NFL `dir` = 180° → Ouest (vers sideline gauche)
  - NFL `dir` = 270° → Sud (vers end zone défense)

### 2.2 Normalisation Spatiale
- **Règle de Direction** : Tous les jeux doivent être normalisés pour que l'attaque progresse vers la droite (X croissant)
- **Transformation** : Si `play_direction == 'left'` :
  ```python
  x_normalized = 120 - x
  y_normalized = 53.3 - y
  dir_normalized = (dir + 180) % 360
  o_normalized = (o + 180) % 360
  ```

### 2.3 Garde-fous Physiques
- **Vitesse maximale** : s ≤ 13.0 yards/seconde (~23 mph)
- **Accélération maximale** : a ≤ 8.0 yards/seconde²
- **Distance minimale joueur-ballon** : d ≥ 0.5 yards (détection catch)

## 3. Règle des Trois Tiers de Sécurité

### ALWAYS DO ✅
- Lancer `pytest` après toute modification Python
- Lancer `npm run lint` après toute modification React/TypeScript
- Exécuter les requêtes SQL en mode SELECT via MCP avant toute intégration
- Valider les contraintes physiques (vitesse, accélération, coordonnées terrain)
- Documenter les transformations géométriques dans le code

### ASK FIRST ⚠️
- Modifier le schéma du composant React principal
- Ajouter des paquets npm non listés dans le stack technique
- Modifier la structure de la base de données DuckDB
- Implémenter des features non spécifiées dans `spec.md`

### NEVER DO ❌
- Ne jamais altérer la base de données DuckDB d'origine
- Ne jamais stocker de clés API ou credentials en dur
- Ne jamais ignorer les erreurs de validation physique
- Ne jamais push vers `main` sans tests passants
- Ne jamais committer des fichiers de données volumineux (>100MB)

## 4. Conventions de Nommage

### 4.1 Variables & Fonctions
```python
# Physics & Geometry
calculate_closing_speed()
normalize_play_direction()
compute_separation_distance()

# Data Processing
filter_tracking_by_event()
aggregate_route_metrics()
join_plays_with_tracking()
```

### 4.2 Composants React
```tsx
// UI Components
<HeatmapMatchup />
<TimeSeriesClosing />
<RouteVisualization />
<PhysicsValidationAlert />
```

### 4.3 Fichiers
```
snake_case.py       # Python modules
kebab-case.tsx      # React components
PascalCase.tsx      # React component files
UPPERCASE.md        # Documentation
```

## 5. Workflow de Développement

### Phase 1 : Exploration Données
1. Analyser structure CSV avec DuckDB MCP
2. Identifier les événements clés (pass_release, ball_land)
3. Valider les invariants physiques sur échantillon

### Phase 2 : Moteur de Calcul
1. Implémenter isolation phase de vol
2. Calculer métriques d'érosion (Δd/Δt)
3. Tester avec pytest sur cas limites

### Phase 3 : Interface React
1. Créer composants de visualisation
2. Intégrer Plotly/Recharts pour heatmaps
3. Linter et formater avec Prettier

### Phase 4 : Intégration
1. Connecter frontend ↔ DuckDB via MCP
2. Déployer hook `physics-guardrail.py`
3. Tests end-to-end

## 6. Sources de Vérité

- **Données** : `nfl-big-data-bowl-regional-event-data/`
- **Spécifications** : `.kiro/specs/coach-cockpit/spec.md`
- **Skills** : `.kiro/skills/nfl-geometry/` & `.kiro/skills/react-coach-ui/`
- **Plan d'action** : `.kiro/PLAN.md`

---

**Version** : 1.0.0  
**Dernière mise à jour** : 2026-10-21  
**Mainteneur** : Équipe Coach Cockpit NFL

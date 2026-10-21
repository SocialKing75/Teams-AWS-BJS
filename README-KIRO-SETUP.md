# 🏈 Coach Cockpit NFL - Configuration Kiro

## Vue d'Ensemble

Ce projet utilise **Kiro** avec une architecture complète de skills, specs, et hooks pour développer un tableau de bord d'analyse tactique pour coordinateurs offensifs NFL.

---

## 📂 Structure Créée

```
.kiro/
├── AGENTS.md                           # Constitution & Invariants Physiques
├── PLAN.md                             # Feuille de route & Requêtes DuckDB MCP
├── specs/
│   └── coach-cockpit/
│       └── spec.md                     # Spécifications formelles EARS
├── skills/
│   ├── nfl-geometry/
│   │   └── SKILL.md                    # Géométrie & Physique NFL
│   └── react-coach-ui/
│       └── SKILL.md                    # Composants React & Visualisations
└── hooks/
    ├── physics-guardrail.py            # Script de validation Python
    └── physics-validation.json         # Hook Kiro (PostToolUse)
```

---

## 🎯 Objectifs du Projet

**Problématique** : « Dans quelles situations tactiques la fenêtre de réception se referme-t-elle le moins (ou le plus vite) ? »

**Livrables** :
1. **Moteur de Calcul** : Isolation phase de vol + calcul closing rate (Δd/Δt)
2. **Interface React** :
   - Heatmap : Routes × Coverage → Closing Rate moyen
   - TimeSeries : Distance/Closing Rate vs Temps
   - Animation 2D du terrain
3. **Intégration DuckDB** via MCP pour requêtes SQL

---

## 🛠️ Configuration Kiro

### Skills Disponibles

#### 1. `nfl-geometry` (`.kiro/skills/nfl-geometry/SKILL.md`)
**Quand l'utiliser** : Lors de manipulation de données de tracking NFL (coordonnées, vitesses, angles)

**Fonctions Clés** :
- `normalize_play_direction()` : Standardiser direction du jeu (attaque → droite)
- `nfl_to_math_radians()` : Convertir angles NFL vers radians mathématiques
- `compute_closing_rate()` : Calculer Δd/Δt entre joueurs
- `validate_speed()` / `validate_acceleration()` : Vérifier contraintes physiques

**Activation** : Kiro charge automatiquement ce skill quand vous travaillez sur des fichiers contenant `tracking`, `nfl`, ou `geometry`.

---

#### 2. `react-coach-ui` (`.kiro/skills/react-coach-ui/SKILL.md`)
**Quand l'utiliser** : Lors de création/modification de composants React pour visualisations

**Composants Templates** :
- `<HeatmapMatchup />` : Heatmap Plotly.js avec hover tooltips
- `<TimeSeriesClosing />` : Graphiques Recharts (distance/closing rate)
- `<RouteVisualization />` : Animation 2D terrain NFL

**Hooks Custom** :
- `useNFLData()` : Fetch données DuckDB via MCP
- `useAnimation()` : Contrôle frame-by-frame (play/pause/seek)

**Activation** : Chargé automatiquement pour fichiers `.tsx`, `.jsx` dans `src/components/`.

---

### Hooks Automatiques

#### Hook : `physics-validation`
**Déclencheur** : `PostToolUse` (après `fs_write` ou `str_replace` sur fichiers `.py`)

**Action** : Valide que les constantes physiques respectent les invariants NFL :
- `MAX_SPEED` ≤ 13.0 yards/s
- `MAX_ACCELERATION` ≤ 8.0 yards/s²
- `FIELD_LENGTH` = 120.0 yards
- `FIELD_WIDTH` = 53.3 yards

**Sortie** : Rapport de validation affiché dans le terminal Kiro.

**Exemple** :
```python
# Si vous écrivez:
MAX_SPEED = 15.0  # ⚠️ Dépasse limite physique!

# Le hook affichera:
❌ MAX_SPEED = 15.0 yards/s exceeds physical limit of 13.0 yards/s
   Reason: Vitesse maximale humaine (~23 mph, record NFL)
```

---

### Spécifications (Specs)

#### Spec : `coach-cockpit` (`.kiro/specs/coach-cockpit/spec.md`)

**Format EARS** (Easy Approach to Requirements Syntax) :
```
[REQ-ENGINE-1 : Isolation de la Phase de Vol]
WHEN le jeu atteint l'événement 'pass_release',
THE SYSTEM SHALL isoler les coordonnées du WR ciblé jusqu'à 'ball_land'.
```

**Sections** :
1. **Moteur de Calcul** : Requirements pour isolation vol & closing rate
2. **Composants UI** : Spécifications React (Heatmap, TimeSeries, Route Viz)
3. **Requêtes DuckDB** : SQL prêtes à l'emploi via MCP
4. **User Stories** : Acceptance criteria pour validation

---

## 🚀 Guide de Démarrage

### Phase 1 : Exploration Données (Semaine 1)

1. **Activer MCP DuckDB** dans Kiro :
   ```json
   // .kiro/settings/mcp.json
   {
     "mcpServers": {
       "duckdb": {
         "command": "duckdb",
         "args": [],
         "env": {}
       }
     }
   }
   ```

2. **Lancer première requête** (voir `PLAN.md` Requête MCP 1) :
   ```sql
   DESCRIBE SELECT * 
   FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv') 
   LIMIT 0;
   ```

3. **Valider contraintes physiques** :
   ```bash
   python scripts/validate_physics.py
   ```

---

### Phase 2 : Moteur de Calcul (Semaines 2-3)

1. **Implémenter isolation phase vol** :
   - Fichier : `src/engine/isolation.py`
   - Référence : `PLAN.md` Section 2.1
   - Skill : `nfl-geometry`

2. **Calculer closing rate** :
   - Fichier : `src/engine/closing_rate.py`
   - Tests : `tests/test_closing_rate.py`

3. **Lancer tests** :
   ```bash
   pytest tests/ -v
   ```

---

### Phase 3 : Interface React (Semaines 3-4)

1. **Créer composant Heatmap** :
   - Template : `.kiro/skills/react-coach-ui/SKILL.md` Section 2
   - Fichier : `src/components/heatmap/HeatmapMatchup.tsx`

2. **Intégrer Plotly.js** :
   ```bash
   npm install react-plotly.js plotly.js
   ```

3. **Tests composant** :
   ```bash
   npm run test -- HeatmapMatchup.test
   ```

---

## 📖 Commandes Kiro Utiles

### Demander à Kiro d'utiliser un skill :
```
"Utilise le skill nfl-geometry pour normaliser la direction de ce jeu"
```

### Référencer la spec :
```
"Implémente REQ-ENGINE-1 de la spec coach-cockpit"
```

### Lancer le hook manuellement :
```bash
python .kiro/hooks/physics-guardrail.py < hook_context.json
```

---

## 🔗 Références Rapides

| Document | Chemin | Utilisation |
|----------|--------|-------------|
| Constitution | `.kiro/AGENTS.md` | Invariants physiques & règles |
| Plan d'action | `.kiro/PLAN.md` | Roadmap & requêtes DuckDB |
| Spec formelle | `.kiro/specs/coach-cockpit/spec.md` | Requirements EARS |
| Skill Géométrie | `.kiro/skills/nfl-geometry/SKILL.md` | Fonctions trigonométrie NFL |
| Skill React | `.kiro/skills/react-coach-ui/SKILL.md` | Composants UI patterns |

---

## 🧪 Tests & Validation

### Checklist Pre-Commit
- [ ] `pytest tests/ -v` passe (Python)
- [ ] `npm run test` passe (React)
- [ ] `npm run lint` sans erreurs (ESLint)
- [ ] Hook `physics-validation` ne signale aucune violation
- [ ] Types TypeScript corrects (`npm run type-check`)

### Commande Complète
```bash
pytest tests/ -v && npm run lint && npm run type-check && npm run test
```

---

## 🤝 Conventions de Développement

### Nommage
```python
# Python
calculate_closing_rate()        # snake_case fonctions
MAX_SPEED                       # UPPER_CASE constantes

# React/TypeScript
<HeatmapMatchup />              # PascalCase composants
useNFLData()                    # camelCase hooks
```

### Git Workflow
```bash
# Créer branche feature
git checkout -b feature/heatmap-component

# Commit avec tests
git add src/components/heatmap/
pytest tests/test_heatmap.py
git commit -m "feat: Add HeatmapMatchup component with Plotly"

# Push (Kiro ne push jamais vers main directement)
git push origin feature/heatmap-component
```

---

## 📞 Support

**Questions sur Kiro** :
- Taper `/help` dans le chat Kiro
- Consulter docs officielles : https://kiro.dev/docs

**Questions sur le Projet** :
- Voir `.kiro/AGENTS.md` Section "Sources de Vérité"
- Consulter `PLAN.md` pour requêtes SQL

---

**Version** : 1.0.0  
**Dernière MAJ** : 2026-10-21  
**Auteurs** : Équipe Coach Cockpit NFL

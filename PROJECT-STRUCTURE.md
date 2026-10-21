# 📂 Coach Cockpit NFL - Structure Complète du Projet

## Vue d'Ensemble

Ce document présente l'architecture complète du projet **Coach Cockpit NFL**, optimisé pour le développement avec Kiro.

---

## 🎯 Objectif du Projet

**Problématique** : « Dans quelles situations tactiques la fenêtre de réception se referme-t-elle le moins (ou le plus vite) ? »

**Livrables** :
1. **Moteur de Calcul** : Isolation phase de vol du ballon + calcul du closing rate (Δd/Δt)
2. **Interface React** : Heatmap, TimeSeries, Animation 2D terrain
3. **Intégration DuckDB** : Requêtes SQL via MCP (Model Context Protocol)

---

## 📁 Arborescence Complète

```
Teams-AWS-BJS/
│
├── .kiro/                                  # Configuration Kiro
│   ├── AGENTS.md                          # Constitution & Invariants Physiques NFL
│   ├── PLAN.md                            # Feuille de route & Requêtes DuckDB MCP
│   ├── GETTING-STARTED.md                 # Guide démarrage rapide
│   │
│   ├── specs/
│   │   └── coach-cockpit/
│   │       └── spec.md                    # Spécifications formelles EARS
│   │
│   ├── skills/
│   │   ├── nfl-geometry/
│   │   │   └── SKILL.md                   # Géométrie & Physique NFL
│   │   │                                  # - Normalisation directions
│   │   │                                  # - Calculs distances/vitesses
│   │   │                                  # - Validation contraintes
│   │   └── react-coach-ui/
│   │       └── SKILL.md                   # Composants React & Visualisations
│   │                                      # - <HeatmapMatchup />
│   │                                      # - <TimeSeriesClosing />
│   │                                      # - Hooks custom (useNFLData, useAnimation)
│   │
│   └── hooks/
│       ├── physics-validation.json        # Hook Kiro (PostToolUse)
│       └── physics-guardrail.py           # Script Python validation automatique
│
├── nfl-big-data-bowl-regional-event-data/ # Données NFL (submodule Git)
│   └── data/
│       ├── games.csv                      # Métadonnées jeux
│       ├── plays.csv                      # Détails actions de jeu
│       ├── players.csv                    # Infos joueurs
│       ├── pffScoutingData.csv            # Annotations PFF (routes, coverages)
│       └── tracking/                      # Données tracking GPS (10 Hz)
│           ├── tracking_2021091200.csv
│           ├── tracking_2021091201.csv
│           └── ... (122 fichiers)
│
├── scripts/
│   └── validate_physics.py                # Script validation contraintes physiques
│
├── src/                                    # Code source (à créer)
│   ├── engine/                            # Moteur de calcul Python
│   │   ├── isolation.py                   # REQ-ENGINE-1 : Isolation phase vol
│   │   ├── closing_rate.py                # REQ-ENGINE-2 : Calcul Δd/Δt
│   │   └── aggregation.py                 # REQ-ENGINE-3 : Stats par route
│   │
│   ├── components/                        # Composants React
│   │   ├── heatmap/
│   │   │   ├── HeatmapMatchup.tsx         # Plotly.js heatmap
│   │   │   ├── HeatmapMatchup.test.tsx
│   │   │   └── types.ts
│   │   ├── timeseries/
│   │   │   ├── TimeSeriesClosing.tsx      # Recharts line charts
│   │   │   └── TimeSeriesClosing.test.tsx
│   │   └── route-viz/
│   │       └── RouteVisualization.tsx     # Animation 2D terrain
│   │
│   ├── hooks/
│   │   ├── useNFLData.ts                  # Fetch DuckDB via MCP
│   │   └── useAnimation.ts                # Contrôle frame-by-frame
│   │
│   ├── pages/
│   │   └── CockpitDashboard.tsx           # Page principale
│   │
│   └── utils/
│       ├── nflGeometry.ts                 # Fonctions géométriques (port Python → TS)
│       └── colorScales.ts                 # Palettes couleurs tactiques
│
├── tests/                                  # Tests unitaires (à créer)
│   ├── test_isolation.py
│   ├── test_closing_rate.py
│   └── test_aggregation.py
│
├── README-KIRO-SETUP.md                    # Documentation configuration Kiro
├── PROJECT-STRUCTURE.md                    # Ce fichier
└── .gitignore
```

---

## 🧩 Composants Clés

### 1. Configuration Kiro (`.kiro/`)

#### `AGENTS.md` - Constitution & Règles
**Rôle** : Définit les invariants physiques et les règles de développement.

**Contenu** :
- Invariants physiques NFL (vitesse max, accélération, dimensions terrain)
- Conventions angles (NFL → Radians mathématiques)
- Règle des "Trois Tiers de Sécurité" (ALWAYS DO / ASK FIRST / NEVER DO)
- Stack technique imposée

**Utilisation** : Référence automatique pour Kiro lors de toute édition de code.

---

#### `PLAN.md` - Feuille de Route
**Rôle** : Organise le développement en 5 phases avec requêtes SQL prêtes à l'emploi.

**Contenu** :
- Phase 1 : Exploration données (Requêtes MCP 1-3)
- Phase 2 : Moteur de calcul (isolation + closing rate)
- Phase 3 : Interface React (Heatmap + TimeSeries)
- Phase 4 : Hooks automatisation
- Phase 5 : Déploiement

**Utilisation** : 
```
Kiro, implémente la Phase 2 Section 2.1 du PLAN.md
```

---

#### `specs/coach-cockpit/spec.md` - Spécifications EARS
**Rôle** : Requirements formels selon syntaxe EARS (Easy Approach to Requirements).

**Format** :
```
[REQ-ENGINE-1 : Isolation de la Phase de Vol]
WHEN le jeu atteint l'événement 'pass_release',
THE SYSTEM SHALL isoler les coordonnées du WR ciblé jusqu'à 'ball_land'.
```

**Sections** :
1. Moteur de Calcul (3 requirements)
2. Composants UI React (3 requirements)
3. Requêtes DuckDB (2 queries)
4. User Stories (3 scénarios)

**Utilisation** :
```
Kiro, implémente REQ-ENGINE-1 avec tests unitaires
```

---

### 2. Skills Kiro (`.kiro/skills/`)

#### Skill : `nfl-geometry`
**Activation** : Automatique lors de manipulation de fichiers contenant `tracking`, `nfl`, ou `geometry`.

**Fonctions Clés** :
| Fonction | Signature | Utilisation |
|----------|-----------|-------------|
| `normalize_play_direction()` | `(x, y, dir, o, play_direction) -> (x', y', dir', o')` | Standardiser direction (attaque → droite) |
| `nfl_to_math_radians()` | `(angle_nfl: float) -> float` | Convertir 0-360° NFL vers radians |
| `compute_closing_rate()` | `(distances: ndarray, dt: float) -> ndarray` | Calculer Δd/Δt entre frames |
| `validate_speed()` | `(speed: float) -> bool` | Vérifier s ≤ 13.0 yd/s |

**Exemple d'Usage** :
```python
from src.utils.nfl_geometry import normalize_play_direction

# Normaliser un jeu où l'attaque va vers la gauche
x_norm, y_norm, dir_norm, o_norm = normalize_play_direction(
    x=50.0, y=20.0, dir_nfl=270.0, o_nfl=180.0, play_direction='left'
)
# Résultat: x_norm=70.0, y_norm=33.3, dir_norm=90.0, o_norm=0.0
```

---

#### Skill : `react-coach-ui`
**Activation** : Automatique pour fichiers `.tsx`, `.jsx` dans `src/components/`.

**Templates Composants** :
1. **`<HeatmapMatchup />`** (Plotly.js)
   - Axes : Routes × CB Alignment
   - Couleurs : Closing rate (rouge = mauvais, vert = bon)
   - Interactions : Hover tooltip + Click → TimeSeries

2. **`<TimeSeriesClosing />`** (Recharts)
   - Graphique 1 : Distance WR-CB vs Temps
   - Graphique 2 : Closing Rate vs Temps
   - Zones rouges : distance < 3 yards

3. **`<RouteVisualization />`** (Canvas 2D)
   - Animation terrain 120×53.3 yards
   - Trajectoires WR/CB + vecteurs vitesse
   - Contrôles : Play/Pause/Seek

**Hooks Custom** :
```typescript
// Fetch données DuckDB via MCP
const { data, loading } = useClosingRateHeatmap();

// Contrôle animation
const { isPlaying, currentFrame, play, pause } = useAnimation(totalFrames, fps=10);
```

---

### 3. Hooks Automatiques (`.kiro/hooks/`)

#### Hook : `physics-validation`
**Déclencheur** : `PostToolUse` (après `fs_write` ou `str_replace` sur `.py`)

**Action** : Exécute `physics-guardrail.py` pour valider :
- `MAX_SPEED` ≤ 13.0 yards/s
- `MAX_ACCELERATION` ≤ 8.0 yards/s²
- `FIELD_LENGTH` = 120.0 yards
- `FIELD_WIDTH` = 53.3 yards

**Sortie Exemple** :
```
======================================================================
🔬 Physics Guardrail Validation Report
======================================================================
File: src/engine/constants.py
Tool: fs_write

⚠️  VIOLATIONS DETECTED:
  ❌ MAX_SPEED = 15.0 yards/s exceeds physical limit of 13.0 yards/s
     Reason: Vitesse maximale humaine (~23 mph, record NFL)

Action Required:
  Please review and correct the constants above.
  Reference: .kiro/AGENTS.md Section 2.3 (Physical Constraints)
======================================================================
```

---

### 4. Données NFL (`nfl-big-data-bowl-regional-event-data/`)

#### Structure Fichiers CSV

**`tracking_YYYYMMDDXX.csv`** (122 fichiers, ~500K lignes chacun)
| Colonne | Type | Description |
|---------|------|-------------|
| `gameId` | int | Identifiant jeu (ex: 2021091200) |
| `playId` | int | Identifiant action dans le jeu |
| `nflId` | int | Identifiant joueur |
| `frameId` | int | Numéro frame (10 Hz) |
| `x`, `y` | float | Coordonnées terrain (yards) |
| `s` | float | Vitesse (yards/s) |
| `a` | float | Accélération (yards/s²) |
| `dir` | float | Direction mouvement (0-360°) |
| `o` | float | Orientation corps (0-360°) |
| `event` | string | `pass_release`, `ball_land`, etc. |

**`plays.csv`** (~15K lignes)
| Colonne | Type | Description |
|---------|------|-------------|
| `gameId` | int | Lien avec tracking |
| `playId` | int | Lien avec tracking |
| `playDescription` | string | Description textuelle |
| `passResult` | string | `C` (Complete), `I` (Incomplete) |
| `playDirection` | string | `left` ou `right` |
| `offenseFormation` | string | `SHOTGUN`, `SINGLEBACK`, etc. |

**`pffScoutingData.csv`** (~30K lignes)
| Colonne | Type | Description |
|---------|------|-------------|
| `nflId` | int | Lien avec joueur |
| `pff_role` | string | `Pass Route`, `Pass Coverage` |
| `pff_routeConcept` | string | `slant`, `go`, `out`, `corner` |
| `pff_coverageType` | string | `Cover 2`, `Cover 3`, `Man` |

---

## 🔄 Workflow de Développement

### Exemple Complet : Implémenter Heatmap

#### Étape 1 : Demander à Kiro
```
Utilise le skill react-coach-ui pour créer le composant <HeatmapMatchup />.
Base-toi sur la section 2.1 du skill pour l'interface TypeScript.
Utilise Plotly.js avec colorscale 'RdYlGn' (reversescale).
```

#### Étape 2 : Kiro Génère
1. **Fichier** : `src/components/heatmap/HeatmapMatchup.tsx`
2. **Types** : `src/components/heatmap/types.ts`
3. **Tests** : `src/components/heatmap/HeatmapMatchup.test.tsx`

#### Étape 3 : Validation
```bash
# Lancer tests
npm run test -- HeatmapMatchup.test

# Vérifier types
npm run type-check

# Linter
npm run lint
```

#### Étape 4 : Intégration
```
Kiro, intègre <HeatmapMatchup /> dans la page CockpitDashboard.tsx.
Fetch les données avec useClosingRateHeatmap().
Gère le loading state avec un spinner.
```

---

### Exemple 2 : Calculer Closing Rate

#### Étape 1 : Lire Spec
```
Kiro, implémente REQ-ENGINE-2 de la spec coach-cockpit
```

#### Étape 2 : Kiro Crée
1. **Fichier** : `src/engine/closing_rate.py`
2. **Tests** : `tests/test_closing_rate.py`

#### Étape 3 : Validation Automatique
- **Hook `physics-validation`** s'exécute automatiquement
- Vérifie que les constantes physiques sont respectées

#### Étape 4 : Lancer Tests
```bash
pytest tests/test_closing_rate.py -v
```

---

## 🛠️ Commandes Utiles

### Python
```bash
# Validation physique sur fichier tracking
python scripts/validate_physics.py \
  --tracking-file nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv \
  --verbose

# Tests unitaires
pytest tests/ -v --cov=src

# Formatter
black src/ tests/
isort src/ tests/
```

### React/TypeScript
```bash
# Développement
npm run dev                # Lancer Vite dev server

# Tests
npm run test               # Vitest watch mode
npm run test:coverage      # Avec coverage

# Qualité code
npm run lint               # ESLint
npm run type-check         # TypeScript compiler
npm run format             # Prettier
```

### DuckDB (via MCP)
```bash
# Ouvrir CLI DuckDB
duckdb

# Exécuter requête depuis PLAN.md
.read .kiro/PLAN.md  # Copier/coller requête MCP 1-5
```

---

## 📊 Métriques de Succès

### Phase 1 (Semaine 1)
- [ ] Validation physique < 1% violations vitesse
- [ ] Requêtes MCP 1-3 exécutées avec succès
- [ ] Hook `physics-validation` actif

### Phase 2 (Semaines 2-3)
- [ ] `isolation.py` : 100% coverage tests
- [ ] `closing_rate.py` : Performance < 100ms pour 1 jeu
- [ ] Agrégation : Calculer métriques sur 1000+ jeux

### Phase 3 (Semaines 3-4)
- [ ] `<HeatmapMatchup />` : Chargement < 2s
- [ ] `<TimeSeriesClosing />` : 30 FPS animation
- [ ] Tests React : 100% composants testés

### Phase 4-5 (Semaines 5-6)
- [ ] Build production sans erreurs
- [ ] Documentation utilisateur complète
- [ ] Démo vidéo 3 cas d'usage

---

## 🔗 Références Rapides

| Document | Chemin | Usage |
|----------|--------|-------|
| Getting Started | `.kiro/GETTING-STARTED.md` | Guide démarrage 5 min |
| Constitution | `.kiro/AGENTS.md` | Invariants + règles |
| Plan d'Action | `.kiro/PLAN.md` | Roadmap + SQL queries |
| Spec Formelle | `.kiro/specs/coach-cockpit/spec.md` | Requirements EARS |
| Skill Géométrie | `.kiro/skills/nfl-geometry/SKILL.md` | Fonctions NFL |
| Skill React | `.kiro/skills/react-coach-ui/SKILL.md` | Composants UI |
| Setup Kiro | `README-KIRO-SETUP.md` | Config détaillée |

---

## 🆘 Troubleshooting

### Problème : Hook ne s'exécute pas
**Solution** :
1. Vérifier existence : `cat .kiro/hooks/physics-validation.json`
2. Redémarrer session Kiro
3. Vérifier logs : `Kiro, montre les logs du dernier hook`

### Problème : Données tracking introuvables
**Solution** :
```bash
cd Teams-AWS-BJS
git submodule update --init --recursive
```

### Problème : Types TypeScript incomplets
**Solution** :
```
Kiro, génère les types TypeScript pour les données NFL 
en te basant sur la structure CSV de tracking.csv
```

---

## 🎓 Pour Aller Plus Loin

### Extensions Possibles
1. **Machine Learning** : Prédire closing rate via regression linéaire
2. **API REST** : Exposer métriques via FastAPI
3. **Real-Time** : WebSocket pour streaming live games
4. **Mobile** : React Native pour tablettes coaches

### Ressources Externes
- [NFL Next Gen Stats](https://nextgenstats.nfl.com/)
- [Plotly.js Documentation](https://plotly.com/javascript/)
- [DuckDB SQL Reference](https://duckdb.org/docs/sql/introduction)
- [EARS Requirements Syntax](https://alistairmavin.com/ears/)

---

**Version** : 1.0.0  
**Dernière MAJ** : 2026-10-21  
**Auteurs** : Équipe Coach Cockpit NFL  
**License** : MIT

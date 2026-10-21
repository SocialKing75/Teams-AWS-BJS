# Intégration Travail Brigitte - Specs Reception Window

## 📋 Vue d'Ensemble

Brigitte a créé des spécifications détaillées pour **3 personas** différents analysant la fenêtre de réception NFL :
1. **Coach** : Analyse tactique par situation (couverture × route)
2. **Scout** : Analyse individuelle des défenseurs
3. **Broadcast** : Animation & storytelling visuel

Ces specs **complètent** notre configuration Kiro existante en fournissant les requirements métier détaillés.

---

## 🎯 Positionnement par Rapport à Notre Travail

### Notre Travail (Branche `stephane`)
**Focus** : Infrastructure technique et outils de développement Kiro
- Configuration Kiro complète (AGENTS.md, PLAN.md, skills, hooks)
- Skills techniques : `nfl-geometry` (calculs physiques), `react-coach-ui` (composants)
- Hooks validation : physique + README
- Configuration MCP (DuckDB + Filesystem)
- Documentation développeur complète

### Travail Brigitte (Branche `brigitte`)
**Focus** : Spécifications produit et requirements métier
- 3 specs structurées (requirements, design, tasks) pour chaque persona
- Mock data JSON réaliste (matchups, defenders, play)
- Définition métrique unifiée "fenêtre de réception"
- User stories format EARS pour chaque cas d'usage

---

## 🔗 Complémentarité

| Aspect | Notre Travail | Travail Brigitte | Intégration |
|--------|--------------|------------------|-------------|
| **Objectif** | Infrastructure dev | Product specs | Infrastructure **implémente** les specs |
| **Public** | Développeurs | Product + Dev | Specs → Code via Kiro |
| **Livrables** | Skills, hooks, tools | Requirements, design | Skills utilisent metrics définies dans specs |
| **Données** | Validation physique | Mock JSON + metrics | Mocks testent composants buildés avec skills |

---

## 📂 Structure Intégrée

```
.kiro/
├── AGENTS.md                           # Constitution technique (notre travail)
├── PLAN.md                             # Roadmap développement (notre travail)
├── INTEGRATION-BRIGITTE.md             # Ce fichier (pont entre les deux)
│
├── specs/
│   ├── coach-cockpit/
│   │   └── spec.md                     # Spec technique originale (notre travail)
│   │
│   ├── reception-window-coach/         # Specs métier Coach (Brigitte)
│   │   ├── requirements.md             # User stories EARS
│   │   ├── design.md                   # Définition métriques + dimensions
│   │   └── tasks.md                    # Découpage tâches
│   │
│   ├── reception-window-scout/         # Specs métier Scout (Brigitte)
│   │   ├── requirements.md
│   │   ├── design.md
│   │   └── tasks.md
│   │
│   └── reception-window-broadcast/     # Specs métier Broadcast (Brigitte)
│       ├── requirements.md
│       ├── design.md
│       └── tasks.md
│
├── skills/
│   ├── nfl-geometry/SKILL.md           # Implémente calculs specs Brigitte
│   └── react-coach-ui/SKILL.md         # Composants pour UI specs Brigitte
│
└── hooks/
    ├── physics-validation.json         # Valide contraintes physiques specs
    └── readme-length-check.json

mock/                                    # Données test (Brigitte)
├── matchups.json                       # Mock onglet Coach
├── defenders.json                      # Mock onglet Scout
└── play.json                           # Mock animation Broadcast
```

---

## 🎯 Mapping : Specs Brigitte → Notre Infrastructure

### 1. Onglet Coach (reception-window-coach)

#### Métrique Définie par Brigitte
```
window_arrival = distance(receveur ciblé, défenseur le plus proche) à l'arrivée
separation_label = 
  - "Contesté"     si < 1 yd
  - "Serré"        si 1-2 yd
  - "Ouvert"       si 2-3 yd
  - "Grand ouvert" si ≥ 3 yd
```

#### Implémentation avec Nos Skills

**Skill `nfl-geometry`** fournit :
```python
# Calcul distance (déjà dans notre skill)
def euclidean_distance(x1, y1, x2, y2) -> float:
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# Nouvelle fonction à ajouter basée sur specs Brigitte
def calculate_separation_label(window_arrival: float) -> str:
    """Convertit distance en langage football selon specs Brigitte."""
    if window_arrival < 1.0:
        return "Contesté"
    elif window_arrival < 2.0:
        return "Serré"
    elif window_arrival < 3.0:
        return "Ouvert"
    else:
        return "Grand ouvert"
```

**Skill `react-coach-ui`** fournit :
```tsx
// Composant Heatmap adapté aux specs Brigitte
<HeatmapMatchup 
  data={matchups}           // Utilise mock/matchups.json
  xAxis="route"             // Selon design.md Brigitte
  yAxis="coverage_type"
  metric="separation"       // Métrique phare définie par Brigitte
  colorScale={(val) => {
    if (val < 1) return 'red';       // Contesté
    if (val < 2) return 'orange';    // Serré
    if (val < 3) return 'yellow';    // Ouvert
    return 'green';                  // Grand ouvert
  }}
/>
```

---

### 2. Onglet Scout (reception-window-scout)

#### Métrique Définie par Brigitte
```
closing_ability = capacité défenseur à réduire la fenêtre
rank_coverage_adjusted = classement ajusté par type de couverture
```

#### Implémentation avec Nos Skills

```python
# À ajouter dans nfl-geometry
def calculate_closing_ability(
    window_throw: float, 
    window_arrival: float
) -> float:
    """Calcule closing selon specs Brigitte."""
    return window_throw - window_arrival
```

```tsx
// Composant React pour leaderboard Scout
<DefenderLeaderboard 
  data={defenders}          // Utilise mock/defenders.json
  sortBy="closing_ability"  // Métrique Brigitte
  adjustBy="coverage_type"  // Ajustement specs Brigitte
/>
```

---

### 3. Onglet Broadcast (reception-window-broadcast)

#### Features Définies par Brigitte
- Animation frame-by-frame du jeu
- Highlight receveur ciblé + défenseur le plus proche
- Affichage évolution fenêtre en temps réel

#### Implémentation avec Nos Skills

**Hook `useAnimation` (déjà dans react-coach-ui)** :
```typescript
const { isPlaying, currentFrame, play, pause, seekTo } = useAnimation(
  totalFrames,  // Depuis mock/play.json
  fps: 10       // Specs Brigitte : 10 Hz
);
```

**Composant Animation** :
```tsx
<PlayAnimation 
  playData={mockPlay}           // mock/play.json
  highlightedPlayers={[
    targetedReceiver,           // Specs Brigitte
    closestDefender
  ]}
  overlayMetric="window_value"  // Affiche distance en temps réel
/>
```

---

## 🔧 Actions d'Intégration Réalisées

### 1. ✅ Récupération Fichiers Brigitte
```bash
git fetch origin
git checkout brigitte
# Copie des specs vers notre branche
git checkout stephane
git checkout brigitte -- .kiro/specs/reception-window-* mock/
```

### 2. ✅ Structure Fusionnée
- **Specs techniques** (notre travail) : `.kiro/specs/coach-cockpit/`
- **Specs métier** (Brigitte) : `.kiro/specs/reception-window-*/`
- Les deux coexistent et se complètent

### 3. 🔄 Adaptations à Faire

#### A. Enrichir Skill `nfl-geometry`
Ajouter dans `.kiro/skills/nfl-geometry/SKILL.md` :
```python
def calculate_separation_label(window_arrival: float) -> str:
    """Convertit distance en langage football (specs Brigitte)."""
    # ... (voir section Mapping ci-dessus)

def identify_closest_defender(
    receiver_pos: Tuple[float, float],
    defenders_positions: List[Tuple[float, float]]
) -> int:
    """Identifie défenseur le plus proche (logique specs Brigitte)."""
    distances = [
        euclidean_distance(receiver_pos[0], receiver_pos[1], d[0], d[1])
        for d in defenders_positions
    ]
    return np.argmin(distances)
```

#### B. Adapter Skill `react-coach-ui`
Créer nouveau template dans `.kiro/skills/react-coach-ui/SKILL.md` :
```tsx
// Section 6: Composant Matchup Matrix (basé sur specs Brigitte)
export const MatchupMatrix: React.FC<MatchupMatrixProps> = ({
  data,  // Format mock/matchups.json
  filters
}) => {
  // Implémentation selon requirements.md Brigitte
  // - Matrice couverture × route
  // - Coloration selon separation_label
  // - Filtres man/zone, depth, down, distance
  // - Alerte si n < 10
}
```

#### C. Créer Nouveau Hook MCP Query
Dans `PLAN.md`, ajouter requête basée sur specs Brigitte :
```sql
-- Requête MCP 6 : Agréger matchups selon specs Brigitte
SELECT 
  supplementary.coverage_type,
  supplementary.route_clean AS route,
  supplementary.man_zone,
  supplementary.depth_bucket AS depth,
  supplementary.down,
  supplementary.dist_bucket,
  COUNT(*) AS n,
  SUM(window_throw) AS sum_window_throw,
  SUM(window_arrival) AS sum_window_arrival,
  SUM(closing) AS sum_closing,
  SUM(CASE WHEN window_arrival >= 3 THEN 1 ELSE 0 END) AS n_open,
  SUM(CASE WHEN window_arrival < 1 THEN 1 ELSE 0 END) AS n_contested
FROM calculated_windows
JOIN supplementary_data
  ON calculated_windows.game_id = supplementary_data.game_id
  AND calculated_windows.play_id = supplementary_data.play_id
GROUP BY 
  coverage_type, route, man_zone, depth, down, dist_bucket
HAVING n >= 10;  -- Seuil specs Brigitte
```

---

## 📊 Prochaines Étapes

### Phase 1 : Validation Données (Semaine 1)
1. ✅ Récupérer specs Brigitte
2. ⏳ Valider que nos données NFL contiennent colonnes requises :
   - `player_role` (pour identifier targeted receiver)
   - `ball_land_x`, `ball_land_y` (point d'arrivée)
   - `supplementary_data.csv` (couverture, route, etc.)
3. ⏳ Adapter script `validate_physics.py` pour vérifier ces champs

### Phase 2 : Adaptation Skills (Semaines 2-3)
1. ⏳ Enrichir `nfl-geometry` avec fonctions specs Brigitte
2. ⏳ Créer templates `react-coach-ui` pour 3 onglets
3. ⏳ Tester avec mocks JSON de Brigitte

### Phase 3 : Implémentation (Semaines 4-6)
1. ⏳ Implémenter onglet Coach (matrice matchups)
2. ⏳ Implémenter onglet Scout (leaderboard défenseurs)
3. ⏳ Implémenter onglet Broadcast (animation)

---

## 🎓 Comment Utiliser Cette Intégration

### Pour le Product Owner
1. **Lire specs Brigitte** : `.kiro/specs/reception-window-*/requirements.md`
2. **Valider requirements** avec stakeholders
3. **Prioriser** onglet Coach > Scout > Broadcast

### Pour les Développeurs

#### Développer Onglet Coach
```
Kiro, implémente l'onglet Coach selon les specs Brigitte:

1. Lis .kiro/specs/reception-window-coach/requirements.md
2. Lis .kiro/specs/reception-window-coach/design.md
3. Utilise le skill nfl-geometry pour calculer separation
4. Utilise le skill react-coach-ui pour créer MatchupMatrix
5. Teste avec mock/matchups.json
```

#### Développer Onglet Scout
```
Kiro, implémente l'onglet Scout:

1. Lis .kiro/specs/reception-window-scout/requirements.md
2. Crée DefenderLeaderboard avec mock/defenders.json
3. Applique ranking_method selon design.md
```

#### Développer Onglet Broadcast
```
Kiro, implémente l'animation Broadcast:

1. Lis .kiro/specs/reception-window-broadcast/requirements.md
2. Utilise useAnimation hook existant
3. Teste avec mock/play.json
```

---

## 🔍 Différences Terminologiques à Noter

| Notre Terminologie Initiale | Terminologie Brigitte | Alignement |
|------------------------------|----------------------|------------|
| `closing_rate` (Δd/Δt) | `closing` (Δd total) | Brigitte plus simple, adopter |
| `window_erosion` | `separation` (à l'arrivée) | `separation` est la métrique phare |
| `min_separation` | `window_arrival` | Aligner sur `window_arrival` |
| Heatmap générique | Matrice Couverture×Route | Implémenter matrice spécifique |

**Décision** : Adopter terminologie Brigitte dans le code UI/UX, garder la nôtre dans skills techniques (plus précise).

---

## ✅ Checklist Intégration

### Configuration
- [x] Specs Brigitte récupérées (9 fichiers MD)
- [x] Mocks JSON récupérés (3 fichiers)
- [ ] Skills enrichis avec fonctions specs Brigitte
- [ ] Templates React créés pour 3 onglets
- [ ] Requêtes DuckDB adaptées aux metrics Brigitte

### Documentation
- [x] Document d'intégration créé (ce fichier)
- [ ] PLAN.md mis à jour avec phases onglets Coach/Scout/Broadcast
- [ ] README.md mentionnant 3 personas

### Tests
- [ ] Mock matchups.json charge correctement
- [ ] Mock defenders.json charge correctement
- [ ] Mock play.json s'anime correctement

---

**Version** : 1.0.0  
**Date Intégration** : 2026-10-21  
**Auteurs** : Équipe Stéphane (infra) + Brigitte (specs)  
**Status** : ✅ Fichiers récupérés, 📝 Adaptations à faire
